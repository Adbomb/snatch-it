-- Профили игроков через ProfileStore (с блокировкой сессии): загрузка, Reconcile, запись, сохранение.
-- Схема профиля — Config/ProfileTemplate (DESIGN.md §2). Повторы и pcall делает сам ProfileStore. При каждой загрузке
-- записи предметов проверяет Shared/Inventory.Normalize (миграция v2 → v3, D46): ничего не удаляется, экспонаты на
-- несуществующих или занятых постаментах уходят в инвентарь.
-- Кража (D46, DESIGN §6): передача записи между профилями (TransferItem), сохранение с ожиданием (SaveAndWait) и журнал
-- передач в DataStore «Transfers» (в Studio без доступа к API и у тестовых профилей — в памяти); при загрузке вора
-- незавершённые передачи решает Util/TransferJournal.
-- D55: schema 3 → 4 (Ловибумы и обучение, Shared/TutorialRules.Migrate) — после разбора журнала и проверки записей;
-- покупка и трата Ловибумов — атомарно (монеты и запас в одном кадре, без yield).
-- Зависит от Vendor/ProfileStore, ProfileTemplate, GameConfig, Config/Items, Shared/Inventory, Shared/CatchRules,
-- Shared/TutorialRules, Util/TransferJournal, Util/Log.

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local CatchRules = require(ReplicatedStorage.Shared.CatchRules)
local Inventory = require(ReplicatedStorage.Shared.Inventory)
local TutorialRules = require(ReplicatedStorage.Shared.TutorialRules)
local ProfileTemplate = require(ReplicatedStorage.Shared.Config.ProfileTemplate)
local ProfileStore = require(ServerScriptService.Server.Vendor.ProfileStore)
local Log = require(ServerScriptService.Server.Util.Log)
local TransferJournal = require(ServerScriptService.Server.Util.TransferJournal)

local store = ProfileStore.New(GameConfig.Data.StoreName, ProfileTemplate)
local profiles: { [Player]: any } = {}
local saveState: { [Player]: { last: number, pending: boolean } } = {}
-- тестовые профили (ProfileStore.Mock): журнал краж — в памяти; отметка остаётся и после выхода (D53: сохранённые
-- данные ушедшего тестового игрока читаются из того же хранилища в памяти)
local mockUsers: { [number]: boolean } = {}
local waiting: { [Player]: { string } } = {} -- передачи с решением «ждать» при загрузке (D53: проверяет TheftService)

-- Журнал передач (DESIGN §6): DataStore «Transfers», ключ to_<вор> → список записей. Пока ProfileStore работает с
-- DataStore (DataStoreState = "Access"), журнал — только там (с повторами при сбоях); без доступа к API (Studio) и у
-- тестовых профилей — в памяти сервера, как и сами профили в этом режиме.
local journalStore: DataStore? = nil
local journalMemory: { [string]: { any } } = {}
local JOURNAL_TRIES = 4

local function journalMode(user: number): string
	if mockUsers[user] then
		return "Memory"
	end
	local waited = 0
	while ProfileStore.DataStoreState == "NotReady" and waited < 15 do
		task.wait(0.25)
		waited += 0.25
	end
	if ProfileStore.DataStoreState ~= "Access" then
		return "Memory"
	end
	if not journalStore then
		journalStore = DataStoreService:GetDataStore(GameConfig.Data.TransferStoreName)
	end
	return "DataStore"
end

local function withRetries<T>(label: string, fn: () -> T): (boolean, T?)
	local delay = 0.5
	for attempt = 1, JOURNAL_TRIES do
		local ok, result = pcall(fn)
		if ok then
			return true, result
		end
		Log.Warn("DataService", ("%s, попытка %d: %s"):format(label, attempt, tostring(result)))
		if attempt < JOURNAL_TRIES then
			task.wait(delay)
			delay *= 2
		end
	end
	return false, nil
end

local DataService = {}

-- Постаментов в музее уровня level (действующие правила, GameConfig.Museum.SlotsByLevel).
function DataService.SlotCountFor(level: number?): number
	local slots = GameConfig.Museum.SlotsByLevel
	return slots[level or 1] or slots[1]
end

local function getActiveProfile(player: Player): any
	local profile = profiles[player]
	if profile and profile:IsActive() then
		return profile
	end
	return nil
end

local finishLoad: (Player, any) -> boolean

-- Загружает профиль (ждёт). true — профиль готов; false — игрока кикнули или он уже вышел.
-- mock — профиль в памяти (ProfileStore.Mock), в DataStore не пишется: только для серверных тестов.
function DataService.LoadAsync(player: Player, mock: boolean?): boolean
	mockUsers[player.UserId] = if mock then true else nil
	local source = if mock then store.Mock else store
	local profile = source:StartSessionAsync(GameConfig.Data.KeyPrefix .. player.UserId, {
		Cancel = function()
			return player.Parent ~= Players
		end,
	})
	if profile == nil then
		if player.Parent == Players then
			player:Kick(
				"Не удалось загрузить сохранение. Попробуйте зайти ещё раз."
			)
		end
		return false
	end
	return finishLoad(player, profile)
end

-- Загрузка после начала сессии. Конец сессии (её перехватил другой сервер) ловится сразу — в том числе пока ждём
-- журнал передач (DataStore); профиль, который уже не активен, игроку не отдаётся (D52: иначе игрок остался бы без
-- сохранения, а GetData — nil посреди входа).
finishLoad = function(player: Player, profile: any): boolean
	local ended = false
	profile.OnSessionEnd:Connect(function()
		ended = true
		if profiles[player] == profile then
			profiles[player] = nil
			saveState[player] = nil
		end
		if player.Parent == Players then
			player:Kick("Сохранение открыто на другом сервере. Перезайдите.")
		end
	end)
	if ended or not profile:IsActive() then
		-- сессию перехватили ещё до загрузки: обработчик выше уже не сработает — кикнуть здесь
		if player.Parent == Players then
			player:Kick("Сохранение открыто на другом сервере. Перезайдите.")
		end
		return false
	end

	profile:AddUserId(player.UserId)
	profile:Reconcile()
	-- Миграция: schema 1 → 2 — новые поля (strength, dumbbellLevel) уже добавил Reconcile.
	if profile.Data.schema == 1 then
		profile.Data.schema = 2
	end
	if type(profile.Data.items) ~= "table" then
		profile.Data.items = {} -- нечитаемое поле предметов (Inventory.Normalize сделал бы то же)
	end
	-- Незавершённые передачи украденного (DESIGN §6): до проверки записей; подтверждение — после загрузки.
	local confirmLater, waitLater = DataService.ResolveTransfers(player, profile.Data)
	-- schema 2 → 3 (D46) и проверка записей при каждой загрузке.
	local report = Inventory.Normalize(
		profile.Data,
		DataService.SlotCountFor(profile.Data.museumLevel),
		Items,
		GameConfig.Museum.RotateStep
	)
	if #report.moved > 0 or #report.unknown > 0 then
		Log.Warn(
			"DataService",
			("%s: в инвентарь с постаментов %d, неизвестных предметов %d"):format(
				player.Name,
				#report.moved,
				#report.unknown
			)
		)
	end
	-- schema 3 → 4 (D55): обучение — по своим предметам (pending не считается), Ловибумы — пусто; затем проверка
	-- Ловибумов и записи обучения при каждой загрузке.
	if TutorialRules.Migrate(profile.Data, ProfileTemplate.schema) then
		Log.Debug(
			"DataService",
			("%s: миграция v3 → v4, обучение — %s"):format(player.Name, profile.Data.tutorial.step)
		)
	end
	profile.Data.lovibums = CatchRules.Normalize(profile.Data.lovibums)
	TutorialRules.Normalize(profile.Data)
	if profile.Data.schema ~= ProfileTemplate.schema then
		Log.Warn(
			"DataService",
			("%s: schema %s, ожидалась %d"):format(
				player.Name,
				tostring(profile.Data.schema),
				ProfileTemplate.schema
			)
		)
	end

	if player.Parent ~= Players then
		profile:EndSession()
		return false
	end
	if ended or not profile:IsActive() then
		-- сессию перехватили, пока шла загрузка (ждали журнал): без профиля играть нельзя
		Log.Warn(
			"DataService",
			player.Name .. ": сессия профиля закончилась во время загрузки"
		)
		if player.Parent == Players then
			player:Kick("Сохранение открыто на другом сервере. Перезайдите.")
		end
		return false
	end
	profiles[player] = profile
	waiting[player] = if waitLater and #waitLater > 0 then waitLater else nil
	if confirmLater and #confirmLater > 0 then
		task.spawn(DataService.ConfirmResolved, player, confirmLater)
	end
	Log.Debug(
		"DataService",
		("Профиль %s загружен, экспонатов: %d"):format(
			player.Name,
			DataService.CountItems(player)
		)
	)
	return true
end

-- Игрок вышел: сохранить и снять блокировку сессии.
function DataService.Release(player: Player)
	local profile = profiles[player]
	profiles[player] = nil
	saveState[player] = nil
	waiting[player] = nil
	if profile then
		profile:EndSession()
	end
end

-- Данные профиля только для чтения; менять их можно лишь функциями ниже.
function DataService.GetData(player: Player): any
	local profile = getActiveProfile(player)
	return if profile then profile.Data else nil
end

function DataService.CountItems(player: Player): number
	local data = DataService.GetData(player)
	local count = 0
	if data then
		for _ in data.items do
			count += 1
		end
	end
	return count
end

function DataService.HasItem(player: Player, uid: string): boolean
	local data = DataService.GetData(player)
	return data ~= nil and data.items[uid] ~= nil
end

function DataService.IsSlotFree(player: Player, slot: number): boolean
	local data = DataService.GetData(player)
	if not data then
		return false
	end
	for _, record in data.items do
		if type(record) == "table" and record.place == "slot" and record.slot == slot then
			return false
		end
	end
	return true
end

-- Запись экспоната. Один экземпляр — одно место: uid и витрина не должны быть заняты.
function DataService.AddItem(player: Player, uid: string, record: { [string]: any }): boolean
	local data = DataService.GetData(player)
	if not data then
		Log.Warn(
			"DataService",
			player.Name .. ": профиль не загружен, запись отклонена"
		)
		return false
	end
	if data.items[uid] ~= nil then
		Log.Warn("DataService", ("%s: uid %s уже есть в профиле"):format(player.Name, uid))
		return false
	end
	if record.place == "slot" and not DataService.IsSlotFree(player, record.slot) then
		Log.Warn(
			"DataService",
			("%s: витрина %s уже занята в профиле"):format(player.Name, tostring(record.slot))
		)
		return false
	end
	data.items[uid] = record
	return true
end

-- Перенос записи между витриной и хранилищем. Поворот (rot) сохраняется.
-- Откат — тот же вызов со старыми place/slot в том же кадре.
function DataService.SetItemPlace(player: Player, uid: string, place: string, slot: number?): boolean
	local data = DataService.GetData(player)
	local record = data and data.items[uid]
	if not record then
		Log.Warn("DataService", ("%s: uid %s нет в профиле"):format(player.Name, uid))
		return false
	end
	if place == "slot" then
		if type(slot) ~= "number" or not DataService.IsSlotFree(player, slot) then
			Log.Warn(
				"DataService",
				("%s: витрина %s занята или не указана"):format(player.Name, tostring(slot))
			)
			return false
		end
	elseif place ~= "storage" then
		return false
	end
	record.place = place
	record.slot = if place == "slot" then slot else nil
	return true
end

-- Обмен витринами двух экспонатов одного игрока. Откат — тот же вызов ещё раз.
function DataService.SwapItemSlots(player: Player, uidA: string, uidB: string): boolean
	local data = DataService.GetData(player)
	local a = data and data.items[uidA]
	local b = data and data.items[uidB]
	if not a or not b or a.place ~= "slot" or b.place ~= "slot" or uidA == uidB then
		Log.Warn("DataService", ("%s: обмен %s ↔ %s невозможен"):format(player.Name, uidA, uidB))
		return false
	end
	a.slot, b.slot = b.slot, a.slot
	return true
end

-- Замена экспоната (D46): newUid из инвентаря встаёт на постамент oldUid, oldUid уходит в инвентарь.
-- Откат — тот же вызов с переставленными uid в том же кадре.
function DataService.ReplaceInSlot(player: Player, oldUid: string, newUid: string): boolean
	local data = DataService.GetData(player)
	local old = data and data.items[oldUid]
	local new = data and data.items[newUid]
	if not old or not new or old.place ~= "slot" or new.place ~= "storage" or oldUid == newUid then
		Log.Warn("DataService", ("%s: замена %s → %s невозможна"):format(player.Name, oldUid, newUid))
		return false
	end
	new.place, new.slot = "slot", old.slot
	old.place, old.slot = "storage", nil
	return true
end

function DataService.SetItemRotation(player: Player, uid: string, rot: number): boolean
	local data = DataService.GetData(player)
	local record = data and data.items[uid]
	if not record then
		return false
	end
	record.rot = rot
	return true
end

-- Только для отката AddItem в том же кадре (без yield между ними), если переход в ItemRegistry отказал.
function DataService.RemoveItem(player: Player, uid: string)
	local data = DataService.GetData(player)
	if data then
		data.items[uid] = nil
	end
end

-- ── Кража (D46, DESIGN §6) ─────────────────────────────────────────────────────────────────────────────────

-- Журнал вора: изменить (fn получает список и возвращает новый). Ждёт DataStore. true — записано.
function DataService.JournalUpdate(thief: number, fn: ({ any }) -> { any }): boolean
	local key = TransferJournal.Key(thief)
	if journalMode(thief) == "Memory" then
		journalMemory[key] = fn(table.clone(journalMemory[key] or {}))
		return true
	end
	local ok = withRetries("журнал " .. key .. " не записан", function()
		(journalStore :: DataStore):UpdateAsync(key, function(old)
			return fn(if type(old) == "table" then old else {})
		end)
		return true
	end)
	return ok
end

-- Журнал вора. nil — прочитать не удалось.
function DataService.JournalRead(thief: number): { any }?
	local key = TransferJournal.Key(thief)
	if journalMode(thief) == "Memory" then
		return table.clone(journalMemory[key] or {})
	end
	local ok, result = withRetries("журнал " .. key .. " не прочитан", function()
		return (journalStore :: DataStore):GetAsync(key)
	end)
	if not ok then
		return nil
	end
	return if type(result) == "table" then result else {}
end

-- Удалить из журнала вора записи с этими id.
function DataService.JournalRemove(thief: number, ids: { string }): boolean
	if #ids == 0 then
		return true
	end
	local drop = {}
	for _, id in ids do
		drop[id] = true
	end
	return DataService.JournalUpdate(thief, function(list)
		local keep = {}
		for _, entry in list do
			if type(entry) ~= "table" or not drop[entry.id] then
				table.insert(keep, entry)
			end
		end
		return keep
	end)
end

-- Сохранённые (не живые) данные игрока userId и есть ли у профиля живая сессия. nil — прочитать не удалось или
-- ProfileStore закрывается (ничего не известно).
function DataService.ReadSaved(userId: number): (any?, boolean)
	local source = if mockUsers[userId] then store.Mock else store
	local ok, result = pcall(function()
		return source:GetAsync(GameConfig.Data.KeyPrefix .. userId)
	end)
	if not ok or result == nil then
		return nil, false
	end
	return result.Data or {}, result.Session ~= nil
end

-- Сохранена ли у жертвы метка передачи id (TransferJournal.Resolve): true / false / nil — неизвестно.
local function victimOut(from: number, id: string, age: number): boolean?
	local data, active = DataService.ReadSaved(from)
	if data == nil then
		return nil
	end
	local marks = data.transfersOut
	if type(marks) == "table" and marks[id] ~= nil then
		return true
	end
	if active and age < TransferJournal.SessionGrace then
		return nil -- живая сессия могла ещё не сохранить удаление
	end
	return false
end

-- При загрузке вора: незавершённые передачи по журналу и меткам (TransferJournal). Меняет data до проверки записей.
-- Возвращает действия, которые надо подтвердить сохранением (ConfirmResolved), или nil, и id передач с решением
-- «ждать» (D53: их во время сессии перепроверяет TheftService.WatchTransfers).
function DataService.ResolveTransfers(player: Player, data: any): ({ any }?, { string }?)
	local entries = DataService.JournalRead(player.UserId)
	if entries == nil then
		Log.Warn(
			"DataService",
			player.Name
				.. ": журнал передач не прочитан — передачи решатся при следующем входе"
		)
		return nil
	end
	local now = os.time()
	local actions = TransferJournal.Resolve(entries, data, now, victimOut)
	local waits = {}
	for _, action in actions do
		if action.kind == "wait" then
			table.insert(waits, action.id)
		end
	end
	local done, confirm = TransferJournal.Apply(actions, data, now)
	TransferJournal.Prune(data, entries, now)
	if #done > 0 then
		DataService.JournalRemove(player.UserId, done)
	end
	if #confirm > 0 or #done > 0 or #waits > 0 then
		Log.Warn(
			"DataService",
			("%s: передач по журналу — решено %d, ждут сохранения %d, ждут жертву %d"):format(
				player.Name,
				#done,
				#confirm,
				#waits
			)
		)
	end
	return confirm, waits
end

-- Передачи, которые при загрузке ждали жертву (id); забирает список (D53, TheftService.WatchTransfers).
function DataService.TakeWaitingTransfers(player: Player): { string }?
	local ids = waiting[player]
	waiting[player] = nil
	return ids
end

-- Повторная проверка передач ids во время сессии вора (D53). Решение — только однозначное: метка жертвы сохранена
-- (выдать или оставить) или у жертвы нет живой сессии и метки нет (кража не состоялась — убрать у вора). Живая
-- сессия без метки — ждать дальше: решение по сроку (TransferJournal.SessionGrace) принимается только при входе, как
-- раньше. Применяет решения к профилю в памяти в одном кадре после всех чтений. Возвращает применённые действия,
-- оставшиеся id и действия для ConfirmResolved; nil — профиль не загружен или журнал не прочитан.
function DataService.ResolveWaiting(player: Player, ids: { string }): ({ any }?, { string }, { any })
	local want: { [string]: boolean } = {}
	for _, id in ids do
		want[id] = true
	end
	local entries = DataService.JournalRead(player.UserId)
	local data = DataService.GetData(player)
	if entries == nil or data == nil then
		return nil, ids, {}
	end
	-- жертвы нужных передач: из журнала и из записей вора с pending (без журнала — from в записи)
	local sources: { [string]: number } = {}
	local chosen = {}
	for _, entry in entries do
		if type(entry) == "table" and type(entry.id) == "string" and want[entry.id] then
			table.insert(chosen, entry)
			sources[entry.id] = tonumber(entry.from) or 0
		end
	end
	for _, record in data.items do
		if type(record) == "table" and type(record.pending) == "string" and want[record.pending] then
			sources[record.pending] = sources[record.pending] or tonumber(record.from) or 0
		end
	end
	-- чтения сохранений жертв (ждут DataStore) — до решений
	local outcome: { [string]: boolean? } = {}
	for id, from in sources do
		local saved, active = DataService.ReadSaved(from)
		if saved ~= nil then
			local marks = saved.transfersOut
			if type(marks) == "table" and marks[id] ~= nil then
				outcome[id] = true
			elseif not active then
				outcome[id] = false
			end
		end
	end
	data = DataService.GetData(player)
	if data == nil then
		return nil, ids, {}
	end
	-- решения и применение — в одном кадре, без yield
	local now = os.time()
	local actions = {}
	for _, action in
		TransferJournal.Resolve(chosen, data, now, function(_from: number, id: string): boolean?
			return outcome[id]
		end)
	do
		if want[action.id] then
			table.insert(actions, action)
		end
	end
	local left, seen = {}, {}
	for _, action in actions do
		seen[action.id] = true
		if action.kind == "wait" then
			table.insert(left, action.id)
		end
	end
	local _, confirm = TransferJournal.Apply(actions, data, now)
	-- «уже закрыта» (done) — тоже через ConfirmResolved: запись журнала удаляется только после сохранения (D53, ревью)
	for _, action in actions do
		if action.kind == "done" and action.journal then
			table.insert(confirm, action)
		end
	end
	local applied = {}
	for _, action in actions do
		if action.kind ~= "wait" then
			table.insert(applied, action)
		end
	end
	for _, id in ids do
		if not seen[id] then
			-- ни записи журнала, ни pending: передачу уже закрыли (другим путём) — больше не ждать
			Log.Debug("DataService", ("%s: передача %s уже закрыта"):format(player.Name, id))
		end
	end
	return applied, left, confirm
end

-- После загрузки: дождаться сохранения, в котором есть решения журнала, и только тогда удалить записи журнала.
function DataService.ConfirmResolved(player: Player, actions: { any })
	local ok = DataService.SaveAndWait(player, 30, function(saved)
		for _, action in actions do
			if not TransferJournal.Confirmed(action, saved) then
				return false
			end
		end
		return true
	end)
	if ok then
		local ids = {}
		for _, action in actions do
			if action.journal then
				table.insert(ids, action.id)
			end
		end
		DataService.JournalRemove(player.UserId, ids)
	end
end

-- Передача владения (шаг 2 журнала): у жертвы запись удаляется и ставится метка transfersOut[id], вору добавляется
-- запись с pending = id и метка transfersIn[id]. Один кадр, без yield. false — записи нет у жертвы, uid уже у вора или
-- профиль не загружен.
function DataService.TransferItem(
	victim: Player,
	thief: Player,
	uid: string,
	record: { [string]: any },
	transferId: string
): boolean
	local from = DataService.GetData(victim)
	local to = DataService.GetData(thief)
	if not from or not to or from.items[uid] == nil or to.items[uid] ~= nil then
		Log.Warn(
			"DataService",
			("передача %s: %s → %s невозможна"):format(uid, victim.Name, thief.Name)
		)
		return false
	end
	local now = os.time()
	local copy = table.clone(record)
	copy.pending = transferId
	from.transfersOut = if type(from.transfersOut) == "table" then from.transfersOut else {}
	to.transfersIn = if type(to.transfersIn) == "table" then to.transfersIn else {}
	from.items[uid] = nil
	from.transfersOut[transferId] = { uid = uid, at = now }
	to.items[uid] = copy
	to.transfersIn[transferId] = { uid = uid, at = now }
	return true
end

-- Откат TransferItem в том же кадре (реестр отказал).
function DataService.UndoTransfer(
	victim: Player,
	thief: Player,
	uid: string,
	original: { [string]: any },
	transferId: string
)
	local from = DataService.GetData(victim)
	local to = DataService.GetData(thief)
	if to then
		to.items[uid] = nil
		if type(to.transfersIn) == "table" then
			to.transfersIn[transferId] = nil
		end
	end
	if from then
		from.items[uid] = original
		if type(from.transfersOut) == "table" then
			from.transfersOut[transferId] = nil
		end
	end
end

-- Передача подтверждена: у записи вора снимается pending.
function DataService.ClearPending(player: Player, uid: string, transferId: string)
	local data = DataService.GetData(player)
	local record = data and data.items[uid]
	if record and record.pending == transferId then
		record.pending = nil
	end
end

local function stateOf(player: Player): { last: number, pending: boolean }
	local state = saveState[player]
	if not state then
		state = { last = -math.huge, pending = false }
		saveState[player] = state
	end
	return state
end

-- Запросить запись профиля, если с прошлой нашей прошло MinSaveInterval (лимит DataStore — запись ключа раз в 6 с,
-- D52). true — запрошено.
local function saveIfAllowed(player: Player, profile: any): boolean
	if profiles[player] ~= profile or not profile:IsActive() then
		return false -- игрок вышел: закрытый профиль не пишем и состояние не заводим заново
	end
	local state = stateOf(player)
	if os.clock() - state.last < GameConfig.Data.MinSaveInterval then
		return false
	end
	state.last = os.clock()
	profile:Save()
	return true
end

-- Сохранить профиль и дождаться записи, в которой выполнено check(сохранённые данные), не дольше timeout секунд.
-- Сохранение, начатое раньше (снимок до изменений), не засчитывается: проверяется содержимое. true — записано.
-- Запросы записи — не чаще MinSaveInterval (D52), включая внеочередные сохранения (RequestSave).
function DataService.SaveAndWait(player: Player, timeout: number, check: ((any) -> boolean)?): boolean
	local profile = getActiveProfile(player)
	if not profile then
		return false
	end
	local saved = false
	local connection = profile.OnAfterSave:Connect(function(lastSaved)
		if check == nil or (type(lastSaved) == "table" and check(lastSaved)) then
			saved = true
		end
	end)
	local started = os.clock()
	saveIfAllowed(player, profile)
	while not saved and os.clock() - started < timeout and profile:IsActive() do
		task.wait(0.1)
		if not saved then
			saveIfAllowed(player, profile)
		end
	end
	connection:Disconnect()
	return saved
end

-- Списать монеты (покупки защиты и взлома, D37). false — не хватает или профиль не загружен.
function DataService.Spend(player: Player, amount: number): boolean
	local data = DataService.GetData(player)
	if not data or amount ~= amount or amount < 0 or data.coins < amount then
		return false
	end
	data.coins -= amount
	return true
end

-- ── Ловибумы (D55) ─────────────────────────────────────────────────────────────────────────────────────────

-- Запас Ловибумов (lovibums = { L<уровень> → { вид → n } }), проверенный; nil — профиль не загружен.
function DataService.Lovibums(player: Player): { [string]: { [string]: number } }?
	local data = DataService.GetData(player)
	if not data then
		return nil
	end
	data.lovibums = CatchRules.Normalize(data.lovibums)
	return data.lovibums
end

-- Покупка: монеты и запас — в одном кадре (без yield). price — цена штуки (CatchRules.Price; проверки — в ShopService,
-- здесь последняя защита данных: итог считается тут). false — не хватает монет, переполнение запаса, нет цены или
-- профиль не загружен.
function DataService.BuyLovibums(player: Player, level: number, kind: string, count: number, price: number): boolean
	local data = DataService.GetData(player)
	local lovibums = DataService.Lovibums(player)
	if not data or not lovibums or not CatchRules.IsLevel(level) or not CatchRules.IsKind(kind) then
		return false
	end
	if not CatchRules.IsWhole(count) or count < 1 or count > CatchRules.Config.MaxBuy then
		return false
	end
	if type(price) ~= "number" or price ~= price or price <= 0 then
		return false
	end
	local total = price * count
	if not CatchRules.IsWhole(total) or data.coins < total then
		return false
	end
	local have = CatchRules.Stock(lovibums, level, kind)
	if have + count > CatchRules.Config.MaxStock then
		return false
	end
	local key = CatchRules.LevelKey(level)
	data.coins -= total
	lovibums[key] = lovibums[key] or {}
	lovibums[key][kind] = have + count
	return true
end

-- Списать один Ловибум (бросок, D55: до результата). false — нет такого.
function DataService.SpendLovibum(player: Player, level: number, kind: string): boolean
	local lovibums = DataService.Lovibums(player)
	if not lovibums or not CatchRules.IsLevel(level) or not CatchRules.IsKind(kind) then
		return false
	end
	local have = CatchRules.Stock(lovibums, level, kind)
	if have < 1 then
		return false
	end
	local key = CatchRules.LevelKey(level)
	lovibums[key][kind] = if have > 1 then have - 1 else nil
	if next(lovibums[key]) == nil then
		lovibums[key] = nil
	end
	return true
end

-- ── Обучение (D55) ─────────────────────────────────────────────────────────────────────────────────────────

-- Запись обучения (проверенная); nil — профиль не загружен. Менять — через SetTutorial.
function DataService.Tutorial(player: Player): TutorialRules.State?
	local data = DataService.GetData(player)
	return if data then TutorialRules.Normalize(data) else nil
end

-- Изменить запись обучения (TutorialRules.Apply: шаг — только вперёд, itemId и uid — один раз, placed — только при
-- записи предмета). Без yield. false — отказ.
function DataService.SetTutorial(player: Player, fields: { [string]: any }): boolean
	local data = DataService.GetData(player)
	if not data then
		return false
	end
	return TutorialRules.Apply(TutorialRules.Normalize(data), data.items, fields)
end

-- Защита музея в профиле (D37): { owned = { вид → n }, hacks = { L<уровень> → n } }.
function DataService.Defense(player: Player): any
	local data = DataService.GetData(player)
	if not data then
		return nil
	end
	if type(data.defense) ~= "table" then
		data.defense = { owned = {}, hacks = {} }
	end
	data.defense.owned = if type(data.defense.owned) == "table" then data.defense.owned else {}
	data.defense.hacks = if type(data.defense.hacks) == "table" then data.defense.hacks else {}
	return data.defense
end

-- Числовое поле статистики (номер события кражи и т. п.).
function DataService.SetStat(player: Player, statName: string, value: number)
	local data = DataService.GetData(player)
	if data then
		data.stats[statName] = value
	end
end

function DataService.GetStat(player: Player, statName: string): number?
	local data = DataService.GetData(player)
	local value = data and data.stats[statName]
	return if type(value) == "number" then value else nil
end

-- Сила от качания (D30): прибавка, потолок GameConfig.Gym.MaxStrength. Возвращает новую силу или nil.
function DataService.AddStrength(player: Player, amount: number): number?
	local data = DataService.GetData(player)
	if not data or amount ~= amount or amount <= 0 then
		return nil
	end
	data.strength = math.min(data.strength + amount, GameConfig.Gym.MaxStrength)
	return data.strength
end

-- Улучшение гантели за монеты: списывает price и поднимает уровень на 1. false — не хватает монет
-- или уровень уже последний (проверки — в GymService, здесь последняя защита данных).
function DataService.UpgradeDumbbell(player: Player, price: number, maxLevel: number): boolean
	local data = DataService.GetData(player)
	if not data or data.dumbbellLevel >= maxLevel or data.coins < price then
		return false
	end
	data.coins -= price
	data.dumbbellLevel += 1
	return true
end

-- Монеты (только DevTools в Studio, пока нет экономики шага 7).
function DataService.AddCoins(player: Player, amount: number): number?
	local data = DataService.GetData(player)
	if not data or amount ~= amount then
		return nil
	end
	data.coins = math.max(data.coins + amount, 0)
	return data.coins
end

function DataService.IncrementStat(player: Player, statName: string)
	local data = DataService.GetData(player)
	if data then
		data.stats[statName] = (data.stats[statName] or 0) + 1
	end
end

-- Внеочередное сохранение, не чаще раза в SaveCooldown секунд (лишние запросы склеиваются).
function DataService.RequestSave(player: Player)
	if not getActiveProfile(player) then
		return
	end
	local state = stateOf(player)
	if state.pending then
		return
	end
	local cooldown = math.max(GameConfig.Data.SaveCooldown, GameConfig.Data.MinSaveInterval)
	local delay = state.last + cooldown - os.clock()
	state.pending = true
	task.delay(math.max(delay, 0), function()
		state.pending = false
		local profile = getActiveProfile(player)
		if profile and not saveIfAllowed(player, profile) then
			DataService.RequestSave(player) -- только что записывали (подтверждение кражи): позже, не чаще MinSaveInterval
		end
	end)
end

-- Для серверных тестов (Server/Tests): загрузка после начала сессии (моделирование перехвата сессии) и профиль игрока
-- (подсчёт запросов записи).
DataService.Handlers = {
	FinishLoad = function(player: Player, profile: any): boolean
		return finishLoad(player, profile)
	end,
	Profile = function(player: Player): any
		return profiles[player]
	end,
}

return DataService

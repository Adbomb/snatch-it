-- Профили игроков через ProfileStore (с блокировкой сессии): загрузка, Reconcile, запись, сохранение.
-- Схема профиля — Config/ProfileTemplate (DESIGN.md §2). Повторы и pcall делает сам ProfileStore. При каждой загрузке
-- записи предметов проверяет Shared/Inventory.Normalize (миграция v2 → v3, D46): ничего не удаляется, экспонаты на
-- несуществующих или занятых постаментах уходят в инвентарь.
-- Кража (D46, DESIGN §6): передача записи между профилями (TransferItem), сохранение с ожиданием (SaveAndWait) и журнал
-- передач в DataStore «Transfers» (в Studio без доступа к API и у тестовых профилей — в памяти); при загрузке вора
-- незавершённые передачи решает Util/TransferJournal.
-- Зависит от Vendor/ProfileStore, ProfileTemplate, GameConfig, Config/Items, Shared/Inventory, Util/TransferJournal,
-- Util/Log.

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local Inventory = require(ReplicatedStorage.Shared.Inventory)
local ProfileTemplate = require(ReplicatedStorage.Shared.Config.ProfileTemplate)
local ProfileStore = require(ServerScriptService.Server.Vendor.ProfileStore)
local Log = require(ServerScriptService.Server.Util.Log)
local TransferJournal = require(ServerScriptService.Server.Util.TransferJournal)

local store = ProfileStore.New(GameConfig.Data.StoreName, ProfileTemplate)
local profiles: { [Player]: any } = {}
local saveState: { [Player]: { last: number, pending: boolean } } = {}
local mockUsers: { [number]: boolean } = {} -- тестовые профили (ProfileStore.Mock): журнал краж — в памяти

-- Журнал передач (DESIGN §6): DataStore «Transfers», ключ to_<вор> → список записей. Если DataStore недоступен
-- (Studio без доступа к API), журнал живёт в памяти сервера — как и профили ProfileStore в этом режиме.
local journalStore: DataStore? = nil
local journalMemory: { [string]: { any } } = {}
local journalChecked = false

local function journal(): DataStore?
	if not journalChecked then
		journalChecked = true
		local ok, result = pcall(function()
			local ds = DataStoreService:GetDataStore(GameConfig.Data.TransferStoreName)
			ds:GetAsync("probe")
			return ds
		end)
		if ok then
			journalStore = result
		else
			Log.Warn("DataService", "журнал передач — в памяти (DataStore недоступен): " .. tostring(result))
		end
	end
	return journalStore
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

	profile:AddUserId(player.UserId)
	profile:Reconcile()
	-- Миграция: schema 1 → 2 — новые поля (strength, dumbbellLevel) уже добавил Reconcile.
	if profile.Data.schema == 1 then
		profile.Data.schema = 2
	end
	-- Незавершённые передачи украденного (DESIGN §6): до проверки записей.
	DataService.ResolveTransfers(player, profile.Data)
	-- schema 2 → 3 (D46) и проверка записей при каждой загрузке.
	local report = Inventory.Normalize(profile.Data, DataService.SlotCountFor(profile.Data.museumLevel), Items)
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

	profile.OnSessionEnd:Connect(function()
		profiles[player] = nil
		saveState[player] = nil
		if player.Parent == Players then
			player:Kick("Сохранение открыто на другом сервере. Перезайдите.")
		end
	end)

	if player.Parent ~= Players then
		profile:EndSession()
		return false
	end
	profiles[player] = profile
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
	mockUsers[player.UserId] = nil
	local profile = profiles[player]
	profiles[player] = nil
	saveState[player] = nil
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
		if record.place == "slot" and record.slot == slot then
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
	local ds = if mockUsers[thief] then nil else journal()
	if not ds then
		journalMemory[key] = fn(table.clone(journalMemory[key] or {}))
		return true
	end
	local ok, err = pcall(function()
		(ds :: DataStore):UpdateAsync(key, function(old)
			return fn(if type(old) == "table" then old else {})
		end)
	end)
	if not ok then
		Log.Warn("DataService", ("журнал %s не записан: %s"):format(key, tostring(err)))
	end
	return ok
end

function DataService.JournalRead(thief: number): { any }?
	local key = TransferJournal.Key(thief)
	local ds = if mockUsers[thief] then nil else journal()
	if not ds then
		return table.clone(journalMemory[key] or {})
	end
	local ok, result = pcall(function()
		return (ds :: DataStore):GetAsync(key)
	end)
	if not ok then
		Log.Warn("DataService", ("журнал %s не прочитан: %s"):format(key, tostring(result)))
		return nil
	end
	return if type(result) == "table" then result else {}
end

-- Сохранённые (не живые) записи предметов игрока userId: для решения по журналу. nil — прочитать не удалось.
function DataService.ReadSavedItems(userId: number): { [string]: any }?
	local source = if mockUsers[userId] then store.Mock else store
	local ok, result = pcall(function()
		return source:GetAsync(GameConfig.Data.KeyPrefix .. userId)
	end)
	if not ok then
		return nil
	end
	if result == nil then
		return {}
	end
	return result.Data and result.Data.items or {}
end

-- При загрузке вора: незавершённые передачи по журналу (TransferJournal.Resolve). Меняет data до проверки записей.
function DataService.ResolveTransfers(player: Player, data: any)
	local hasPending = false
	for _, record in data.items or {} do
		if type(record) == "table" and record.pending ~= nil then
			hasPending = true
		end
	end
	local entries = DataService.JournalRead(player.UserId)
	if not entries or (#entries == 0 and not hasPending) then
		return
	end
	local actions = TransferJournal.Resolve(entries, data.items, os.time(), function(from, uid)
		local items = DataService.ReadSavedItems(from)
		if items == nil then
			return nil
		end
		return items[uid] ~= nil
	end)
	local cleared = TransferJournal.Apply(actions, data.items)
	if #cleared > 0 then
		local done = {}
		for _, id in cleared do
			done[id] = true
		end
		DataService.JournalUpdate(player.UserId, function(list)
			local keep = {}
			for _, entry in list do
				if not done[entry.id] then
					table.insert(keep, entry)
				end
			end
			return keep
		end)
		Log.Warn("DataService", ("%s: передач по журналу решено %d"):format(player.Name, #cleared))
	end
end

-- Передача владения (шаг 2 журнала): у жертвы запись удаляется, вору добавляется с pending = transferId. Один кадр,
-- без yield. false — записи нет у жертвы, uid уже у вора или профиль не загружен.
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
		Log.Warn("DataService", ("передача %s: %s → %s невозможна"):format(uid, victim.Name, thief.Name))
		return false
	end
	local copy = table.clone(record)
	copy.pending = transferId
	from.items[uid] = nil
	to.items[uid] = copy
	return true
end

-- Откат TransferItem в том же кадре (реестр отказал).
function DataService.UndoTransfer(victim: Player, thief: Player, uid: string, original: { [string]: any })
	local from = DataService.GetData(victim)
	local to = DataService.GetData(thief)
	if to then
		to.items[uid] = nil
	end
	if from then
		from.items[uid] = original
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

-- Сохранить профиль и дождаться записи (OnAfterSave) не дольше timeout секунд. true — записано.
function DataService.SaveAndWait(player: Player, timeout: number): boolean
	local profile = getActiveProfile(player)
	if not profile then
		return false
	end
	local saved = false
	local connection = profile.OnAfterSave:Connect(function()
		saved = true
	end)
	profile:Save()
	local started = os.clock()
	while not saved and os.clock() - started < timeout and profile:IsActive() do
		task.wait(0.1)
	end
	connection:Disconnect()
	return saved
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
	local state = saveState[player]
	if not state then
		state = { last = -math.huge, pending = false }
		saveState[player] = state
	end
	if state.pending then
		return
	end
	local delay = state.last + GameConfig.Data.SaveCooldown - os.clock()
	state.pending = true
	task.delay(math.max(delay, 0), function()
		state.pending = false
		local profile = getActiveProfile(player)
		if profile then
			state.last = os.clock()
			profile:Save()
		end
	end)
end

return DataService

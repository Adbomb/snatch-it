--!strict
-- Чистые правила музея-небоскрёба (этап B, docs/TOWER_PLAN.md v3 §1). Этаж — это запись экземпляра items[uid] с
-- полем builtAt (время постройки); place у этажа всегда "storage" — Shared/Inventory.Normalize сбрасывает
-- незнакомые place, а builtAt не трогает. Порядок этажей — data.tower.order (uid снизу вверх), FloorIndex — позиция
-- в нём (не хранится), ключ уникальности — id (ItemID) внутри башни одного владельца; идентичность этажа — uid.
-- Инварианты (Check): в order только записи с builtAt без pending, без повторов uid и id, все — с доходом; каждая
-- запись с builtAt (кроме pending) есть в order; у этажа place = "storage" и нет slot. Повтор — запись без builtAt,
-- чей id уже есть в order (вычисляется, не хранится).
-- Без Instance: вызывают DataService, TowerService, InventoryService и Lune (scripts/lune/check_tower.luau).
-- Описания предметов (Config/Items) передаёт вызывающий. Ни от чего не зависит.

local TowerRules = {}

TowerRules.Version = 1 -- data.tower.v
TowerRules.MigrationVersion = 1 -- data.migration.tower.v

export type Report = {
	changed: boolean,
	dropped: { string }, -- uid убраны из order (нет записи, pending, повтор, без дохода)
	appended: { string }, -- этажи вне order дописаны наверх
	demoted: { string }, -- у записи снят builtAt (второй этаж того же id или предмет без дохода)
}

local function newReport(): Report
	return { changed = false, dropped = {}, appended = {}, demoted = {} }
end

-- Даёт ли предмет этаж: известен, с доходом, не прежний (legacy).
function TowerRules.Buildable(def: any): boolean
	return type(def) == "table" and type(def.income) == "number" and def.income > 0 and def.legacy ~= true
end

-- Запись — построенный этаж (или этаж, который ещё передаётся: pending + builtAt).
function TowerRules.IsBuilt(record: any): boolean
	return type(record) == "table" and type(record.builtAt) == "number"
end

-- Есть ли в профиле данные башни: порядок этажей или хотя бы одна запись с builtAt. У обычных профилей — нет.
function TowerRules.HasTower(data: any): boolean
	if type(data) ~= "table" then
		return false
	end
	if data.tower ~= nil then
		return true
	end
	for _, record in if type(data.items) == "table" then data.items else {} do
		if TowerRules.IsBuilt(record) then
			return true
		end
	end
	return false
end

-- Порядок этажей (список uid снизу вверх) или пустой список. Только чтение.
function TowerRules.Order(data: any): { string }
	local tower = type(data) == "table" and data.tower
	return if type(tower) == "table" and type(tower.order) == "table" then tower.order else {}
end

-- Номер этажа uid (1 — нижний над холлом) или nil.
function TowerRules.IndexOf(data: any, uid: string): number?
	for index, value in TowerRules.Order(data) do
		if value == uid then
			return index
		end
	end
	return nil
end

-- Этаж вида itemId в башне: uid и номер, или nil.
function TowerRules.FloorOf(data: any, itemId: string): (string?, number?)
	local items = type(data) == "table" and data.items or {}
	for index, uid in TowerRules.Order(data) do
		local record = items[uid]
		if type(record) == "table" and record.id == itemId then
			return uid, index
		end
	end
	return nil, nil
end

-- Повтор: сохранённая запись без builtAt и без pending, этаж её вида уже стоит в башне.
function TowerRules.IsDuplicate(data: any, uid: string): boolean
	local record = type(data) == "table" and type(data.items) == "table" and data.items[uid]
	if type(record) ~= "table" or TowerRules.IsBuilt(record) or record.pending ~= nil or record.place ~= "storage" then
		return false
	end
	return (TowerRules.FloorOf(data, record.id)) ~= nil
end

-- Высота пола этажа index над полом холла (0 — холл): холл высотой Lobby.Height, дальше по FloorHeight.
function TowerRules.BaseY(index: number, cfg: any): number
	if index <= 0 then
		return 0
	end
	return cfg.Lobby.Height + (index - 1) * cfg.FloorHeight
end

-- Можно ли построить этаж из записи uid. true или false и причина для игрока.
function TowerRules.CanBuild(data: any, uid: any, defs: { [string]: any }): (boolean, string?)
	if type(data) ~= "table" or type(data.items) ~= "table" then
		return false, "Сохранение ещё загружается"
	end
	if type(uid) ~= "string" then
		return false, "Нет такого предмета"
	end
	local record = data.items[uid]
	if type(record) ~= "table" then
		return false, "Нет такого предмета"
	end
	if record.pending ~= nil then
		return false, "Предмет ещё передаётся"
	end
	if TowerRules.IsBuilt(record) then
		return false, "Этот предмет уже стоит этажом"
	end
	if record.place ~= "storage" then
		return false, "Сначала уберите предмет в инвентарь"
	end
	local def = defs[record.id]
	if type(def) ~= "table" then
		return false, "Неизвестный предмет"
	end
	if not TowerRules.Buildable(def) then
		return false, "У этого предмета пока нет этажа"
	end
	if TowerRules.FloorOf(data, record.id) ~= nil then
		return false, ("Этаж «%s» уже есть в башне"):format(tostring(def.displayName or record.id))
	end
	return true, nil
end

local function ensureTower(data: any): any
	if type(data.tower) ~= "table" then
		data.tower = { v = TowerRules.Version, order = {} }
	end
	if type(data.tower.order) ~= "table" then
		data.tower.order = {}
	end
	return data.tower
end

-- Постройка: builtAt и uid наверх. Проверка — CanBuild до вызова (здесь не повторяется).
function TowerRules.AddFloor(data: any, uid: string, now: number)
	local tower = ensureTower(data)
	data.items[uid].builtAt = now
	table.insert(tower.order, uid)
end

-- Снять этаж (DEV RemoveFloor): uid из order, builtAt снимается — запись остаётся предметом в инвентаре. Возвращает
-- прежний номер или nil (этажа не было).
function TowerRules.RemoveFloor(data: any, uid: string): number?
	local index = TowerRules.IndexOf(data, uid)
	if not index then
		return nil
	end
	table.remove(data.tower.order, index)
	local record = data.items[uid]
	if type(record) == "table" then
		record.builtAt = nil
	end
	return index
end

-- Перестановка этажа uid на номер to (1…N, сдвиг остальных). Возвращает прежний номер или nil.
function TowerRules.MoveFloor(data: any, uid: string, to: number): number?
	local index = TowerRules.IndexOf(data, uid)
	local order = TowerRules.Order(data)
	if not index or to < 1 or to > #order or to ~= math.floor(to) then
		return nil
	end
	table.remove(order, index)
	table.insert(order, to, uid)
	return index
end

local function sameList(a: { string }, b: { string }): boolean
	if #a ~= #b then
		return false
	end
	for i, v in a do
		if b[i] ~= v then
			return false
		end
	end
	return true
end

-- Проверка и починка при каждой загрузке (после Inventory.Normalize). У профиля без башни ничего не создаётся.
-- Повторный запуск ничего не меняет. Ничего не удаляется: лишние этажи становятся предметами в инвентаре.
function TowerRules.Normalize(data: any, defs: { [string]: any }): Report
	local report = newReport()
	if type(data) ~= "table" or type(data.items) ~= "table" or not TowerRules.HasTower(data) then
		return report
	end
	if type(data.tower) ~= "table" or type(data.tower.order) ~= "table" or data.tower.v ~= TowerRules.Version then
		local old = if type(data.tower) == "table" and type(data.tower.order) == "table" then data.tower.order else {}
		data.tower = { v = TowerRules.Version, order = old }
		report.changed = true
	end
	local items = data.items
	local order: { string } = {}
	local seenUid: { [string]: boolean } = {}
	local seenId: { [string]: boolean } = {}
	for _, uid in data.tower.order do
		local record = if type(uid) == "string" then items[uid] else nil
		local keep = type(uid) == "string"
			and not seenUid[uid]
			and type(record) == "table"
			and record.pending == nil
			and TowerRules.IsBuilt(record)
			and TowerRules.Buildable(defs[record.id])
			and not seenId[record.id]
		if keep then
			table.insert(order, uid)
			seenUid[uid] = true
			seenId[record.id] = true
		else
			table.insert(report.dropped, tostring(uid))
			-- запись осталась (повтор вида, без дохода): снять признак этажа; pending не трогается — решит журнал
			if type(uid) == "string" and not seenUid[uid] and TowerRules.IsBuilt(record) and record.pending == nil then
				record.builtAt = nil
				table.insert(report.demoted, uid)
			end
		end
	end
	-- Этажи вне порядка (например, выданные журналом после сбоя): наверх по времени постройки.
	local loose: { string } = {}
	for uid, record in items do
		if type(uid) == "string" and TowerRules.IsBuilt(record) and record.pending == nil and not seenUid[uid] then
			table.insert(loose, uid)
		end
	end
	table.sort(loose, function(a, b)
		local ta, tb = items[a].builtAt, items[b].builtAt
		return if ta == tb then a < b else ta < tb
	end)
	for _, uid in loose do
		local record = items[uid]
		if TowerRules.Buildable(defs[record.id]) and not seenId[record.id] then
			table.insert(order, uid)
			seenUid[uid] = true
			seenId[record.id] = true
			table.insert(report.appended, uid)
		else
			record.builtAt = nil
			table.insert(report.demoted, uid)
		end
	end
	-- У этажа место — только инвентарь (постаментов в башне нет).
	for _, uid in order do
		local record = items[uid]
		if record.place ~= "storage" or record.slot ~= nil then
			record.place = "storage"
			record.slot = nil
			report.changed = true
		end
	end
	if not sameList(order, data.tower.order) then
		data.tower.order = order
		report.changed = true
	end
	if #report.demoted > 0 or #report.appended > 0 then
		report.changed = true
	end
	return report
end

-- Миграция v5 → v6 (только режим башни, тестовые копии профилей): выставленные экспонаты — по номеру постамента,
-- первый экземпляр каждого вида с доходом становится этажом; все выставленные уходят в инвентарь (постаментов в башне
-- нет), повторы и предметы без дохода — обычные записи. Ничего не удаляется. Повторный запуск ничего не меняет
-- (отметка data.migration.tower). true — миграция выполнена сейчас.
function TowerRules.Migrate(data: any, defs: { [string]: any }, now: number): boolean
	if type(data) ~= "table" or type(data.items) ~= "table" then
		return false
	end
	if type(data.migration) == "table" and type(data.migration.tower) == "table" then
		return false
	end
	local tower = ensureTower(data)
	local shown: { string } = {}
	for uid, record in data.items do
		if type(uid) == "string" and type(record) == "table" and record.place == "slot" then
			table.insert(shown, uid)
		end
	end
	table.sort(shown, function(a, b)
		local sa, sb = data.items[a].slot, data.items[b].slot
		sa = if type(sa) == "number" then sa else math.huge
		sb = if type(sb) == "number" then sb else math.huge
		return if sa == sb then a < b else sa < sb
	end)
	local floors = 0
	for _, uid in shown do
		local record = data.items[uid]
		record.place = "storage"
		record.slot = nil
		if
			record.pending == nil
			and not TowerRules.IsBuilt(record)
			and TowerRules.Buildable(defs[record.id])
			and TowerRules.FloorOf(data, record.id) == nil
		then
			record.builtAt = now
			table.insert(tower.order, uid)
			floors += 1
		end
	end
	data.migration = if type(data.migration) == "table" then data.migration else {}
	data.migration.tower = { v = TowerRules.MigrationVersion, at = now, floors = floors }
	return true
end

-- Проверка инвариантов (тесты: серверные и Lune). true или false и список нарушений.
function TowerRules.Check(data: any, defs: { [string]: any }): (boolean, { string })
	local problems: { string } = {}
	local items = type(data) == "table" and type(data.items) == "table" and data.items or {}
	local order = TowerRules.Order(data)
	local seenUid: { [string]: boolean } = {}
	local seenId: { [string]: boolean } = {}
	for index, uid in order do
		local record = items[uid]
		if type(record) ~= "table" then
			table.insert(problems, ("этаж %d: нет записи %s"):format(index, tostring(uid)))
			continue
		end
		if seenUid[uid] then
			table.insert(problems, ("uid %s в башне дважды"):format(uid))
		end
		if seenId[record.id] then
			table.insert(problems, ("два этажа вида %s"):format(tostring(record.id)))
		end
		seenUid[uid] = true
		seenId[record.id] = true
		if not TowerRules.IsBuilt(record) then
			table.insert(problems, ("этаж %d (%s) без builtAt"):format(index, uid))
		end
		if record.pending ~= nil then
			table.insert(problems, ("этаж %d (%s) ещё передаётся"):format(index, uid))
		end
		if record.place ~= "storage" or record.slot ~= nil then
			table.insert(problems, ("этаж %d (%s) на постаменте"):format(index, uid))
		end
		if not TowerRules.Buildable(defs[record.id]) then
			table.insert(problems, ("этаж %d (%s) — предмет без дохода"):format(index, uid))
		end
	end
	for uid, record in items do
		if TowerRules.IsBuilt(record) and record.pending == nil and not seenUid[uid] then
			table.insert(problems, ("builtAt у %s, но в башне его нет"):format(tostring(uid)))
		end
	end
	return #problems == 0, problems
end

return TowerRules

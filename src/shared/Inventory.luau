--!strict
-- Единый инвентарь игрока (D46): все его коллекционные предметы — записи профиля items[uid], один экземпляр — одна
-- запись. place = "slot" (Displayed, на постаменте slot) или "storage" (Stored, в инвентаре). Здесь — чистые функции
-- без Instance: миграция и проверка профиля (схема 3), подсчёты и доход. Их вызывают DataService (при каждой
-- загрузке), сервисы музея и интерфейс; проверяет scripts/lune/check_inventory.luau.
-- Ни от чего не зависит: описания предметов (Config/Items) передаются аргументом.

local Inventory = {}

Inventory.Schema = 3
Inventory.RotateStep = 45

export type Record = {
	id: string,
	mods: { string }?,
	place: string, -- "slot" | "storage"
	slot: number?,
	rot: number?,
	acquiredAt: number?,
	source: string?, -- "map" | "boss" | "raid"
	boss: number?, -- уровень босса-источника (локация происхождения)
	from: number?, -- UserId прежнего владельца (украденное, D46)
}

export type Report = {
	moved: { string }, -- uid, снятые с несуществующего или занятого постамента в инвентарь
	fixed: { string }, -- uid, у которых исправлены поля (место, поворот, mods)
	unknown: { string }, -- uid предметов, которых нет в Config/Items (остаются в профиле)
	total: number,
	displayed: number,
	changed: boolean,
}

-- Кто остаётся на постаменте, если на одном месте несколько записей: раньше полученный, затем меньший uid.
local function older(a: { uid: string, record: any }, b: { uid: string, record: any }): boolean
	local ta = if type(a.record.acquiredAt) == "number" then a.record.acquiredAt else 0
	local tb = if type(b.record.acquiredAt) == "number" then b.record.acquiredAt else 0
	if ta ~= tb then
		return ta < tb
	end
	return a.uid < b.uid
end

local function isWhole(n: any): boolean
	return type(n) == "number" and n == n and n == math.floor(n)
end

-- Миграция v2 → v3 и проверка при каждой загрузке (повторный вызов ничего не меняет). Ничего не удаляет:
-- экспонат на несуществующем постаменте (больше slotCount), на занятом или с неверным местом уходит в инвентарь;
-- неизвестный предмет (нет в itemDefs) остаётся в профиле, но с постамента уходит в инвентарь. Меняет data на месте.
function Inventory.Normalize(data: any, slotCount: number, itemDefs: { [string]: any }): Report
	local report: Report = { moved = {}, fixed = {}, unknown = {}, total = 0, displayed = 0, changed = false }
	if type(data.items) ~= "table" then
		data.items = {}
		report.changed = true
	end
	local bySlot: { [number]: { { uid: string, record: any } } } = {}
	local uids = {}
	for uid in data.items do
		table.insert(uids, uid)
	end
	table.sort(uids, function(a, b)
		return tostring(a) < tostring(b)
	end)
	for _, uid in uids do
		local record = data.items[uid]
		report.total += 1
		if type(record) ~= "table" then
			table.insert(report.unknown, tostring(uid)) -- нечитаемая запись: не трогаем
			continue
		end
		local wasFixed = false
		if type(record.id) ~= "string" or itemDefs[record.id] == nil then
			table.insert(report.unknown, uid)
			if record.place ~= "storage" or record.slot ~= nil then
				record.place = "storage"
				record.slot = nil
				table.insert(report.moved, uid)
				report.changed = true
			end
			continue
		end
		if record.place ~= "slot" and record.place ~= "storage" then
			record.place = "storage"
			wasFixed = true
		end
		if record.place == "slot" then
			local slot = record.slot
			if not isWhole(slot) or slot < 1 or slot > slotCount then
				record.place = "storage"
				record.slot = nil
				table.insert(report.moved, uid)
				report.changed = true
			else
				bySlot[slot] = bySlot[slot] or {}
				table.insert(bySlot[slot], { uid = uid, record = record })
			end
		elseif record.slot ~= nil then
			record.slot = nil
			wasFixed = true
		end
		local rot = record.rot
		local validRot = type(rot) == "number"
			and rot == rot
			and rot % Inventory.RotateStep == 0
			and rot >= 0
			and rot < 360
		if not validRot then
			record.rot = 0
			wasFixed = true
		end
		if type(record.mods) ~= "table" then
			record.mods = {}
			wasFixed = true
		end
		if record.boss == nil and type(itemDefs[record.id].boss) == "number" then
			record.boss = itemDefs[record.id].boss -- локация происхождения для фильтра инвентаря
			wasFixed = true
		end
		if wasFixed then
			table.insert(report.fixed, uid)
			report.changed = true
		end
	end
	for _, list in bySlot do
		table.sort(list, older)
		for i, item in list do
			if i == 1 then
				report.displayed += 1
			else
				item.record.place = "storage"
				item.record.slot = nil
				table.insert(report.moved, item.uid)
				report.changed = true
			end
		end
	end
	if data.schema ~= Inventory.Schema then
		data.schema = Inventory.Schema
		report.changed = true
	end
	return report
end

-- Всего предметов, выставлено и доход в секунду (только Displayed — D37, D46).
function Inventory.Summary(items: { [string]: any }, itemDefs: { [string]: any }): (number, number, number)
	local total, displayed, income = 0, 0, 0
	for _, record in items do
		total += 1
		if type(record) == "table" and record.place == "slot" then
			displayed += 1
			local def = itemDefs[record.id]
			if def and type(def.income) == "number" then
				income += def.income
			end
		end
	end
	return total, displayed, income
end

-- Сколько записей стоит на постаменте slot (в целом профиле должно быть 0 или 1).
function Inventory.CountOnSlot(items: { [string]: any }, slot: number): number
	local n = 0
	for _, record in items do
		if type(record) == "table" and record.place == "slot" and record.slot == slot then
			n += 1
		end
	end
	return n
end

return Inventory

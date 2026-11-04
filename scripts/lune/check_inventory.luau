--!nocheck
-- Проверка единого инвентаря без Roblox Studio (D46): миграция профиля v2 → v3 на копиях данных (Shared/Inventory),
-- подсчёты и доход, правило «когда можно менять экспонаты» и фазы кражи (Shared/GameTime). Реальные сохранения не
-- трогаются: все профили — таблицы в памяти. Запуск из корня репозитория: lune run scripts/lune/check_inventory.luau.
-- Ошибка — код возврата 1.

local process = require("@lune/process")

local Env = require("./env")

local GameConfig = Env.Require("ReplicatedStorage.Shared.Config.GameConfig")
local GameTime = Env.Require("ReplicatedStorage.Shared.GameTime")
local Inventory = Env.Require("ReplicatedStorage.Shared.Inventory")
local Items = Env.Require("ReplicatedStorage.Shared.Config.Items")

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

local function deepCopy(value)
	if type(value) ~= "table" then
		return value
	end
	local out = {}
	for k, v in value do
		out[k] = deepCopy(v)
	end
	return out
end

local function deepEqual(a, b): boolean
	if type(a) ~= type(b) then
		return false
	end
	if type(a) ~= "table" then
		return a == b
	end
	for k, v in a do
		if not deepEqual(v, b[k]) then
			return false
		end
	end
	for k in b do
		if a[k] == nil then
			return false
		end
	end
	return true
end

-- Предметы босса 1 с доходом (настоящие id из каталога), по имени — чтобы тест был воспроизводимым.
local ids = {}
for id, def in Items do
	if type(def) == "table" and def.boss == 1 and not def.legacy and (def.income or 0) > 0 then
		table.insert(ids, id)
	end
end
table.sort(ids)
assert(#ids >= 4, "нужно хотя бы 4 предмета босса 1")
local A, B, C, D = ids[1], ids[2], ids[3], ids[4]
local SLOTS = GameConfig.Museum.SlotsByLevel[1]

local function v2Profile(items)
	return { schema = 2, coins = 1234, museumLevel = 1, strength = 10, dumbbellLevel = 1, items = items, stats = {} }
end
local function rec(id, place, slot, extra)
	local r = { id = id, mods = {}, place = place, slot = slot, rot = 0, acquiredAt = 100, source = "boss", boss = 1 }
	for k, v in extra or {} do
		r[k] = v
	end
	return r
end
local function uidsOf(items)
	local out = {}
	for uid in items do
		table.insert(out, uid)
	end
	table.sort(out)
	return table.concat(out, ",")
end

print("Миграция профиля v2 → v3 (копии данных):")
do
	-- Обычный профиль: 3 на постаментах, 2 в инвентаре, повторы одного предмета — разные экземпляры.
	local original = v2Profile({
		u1 = rec(A, "slot", 1),
		u2 = rec(B, "slot", 2),
		u3 = rec(A, "slot", 3),
		u4 = rec(A, "storage"),
		u5 = rec(C, "storage"),
	})
	local data = deepCopy(original)
	local report = Inventory.Normalize(data, SLOTS, Items)
	check(data.schema == 3, "схема 2 → 3")
	check(
		#report.moved == 0 and #report.unknown == 0,
		"обычный профиль: ни один экспонат не сдвинут"
	)
	check(
		uidsOf(data.items) == uidsOf(original.items),
		"все uid на месте, новых нет (повторы A не объединены)"
	)
	local same = true
	for uid, r in original.items do
		local n = data.items[uid]
		same = same and n.id == r.id and n.place == r.place and n.slot == r.slot
	end
	check(same, "предметы, места и постаменты не изменились")
	local _, displayed, income = Inventory.Summary(data.items, Items)
	check(
		displayed == 3 and income == Items[A].income * 2 + Items[B].income,
		("доход прежний: %s = 2 × %s + %s"):format(tostring(income), A, B)
	)
	check(data.coins == 1234 and data.strength == 10, "монеты и сила не тронуты")

	local again = deepCopy(data)
	local second = Inventory.Normalize(again, SLOTS, Items)
	check(
		not second.changed and deepEqual(again, data),
		"повторная миграция ничего не меняет и не создаёт экземпляров"
	)
end

do
	-- Два экспоната на одном постаменте: остаётся раньше полученный, второй — в инвентарь (не теряется).
	local data = v2Profile({
		late = rec(A, "slot", 2, { acquiredAt = 500 }),
		early = rec(B, "slot", 2, { acquiredAt = 50 }),
	})
	local report = Inventory.Normalize(data, SLOTS, Items)
	check(
		data.items.early.place == "slot" and data.items.early.slot == 2 and data.items.late.place == "storage",
		"двойной постамент: старший экземпляр на месте, младший — в инвентарь"
	)
	check(#report.moved == 1 and report.moved[1] == "late", "в отчёте один перенос")
	check(Inventory.CountOnSlot(data.items, 2) == 1, "на постаменте 2 одна запись")
end

do
	-- Постамент вне музея, дробный, отрицательный; неверное место; кривой поворот.
	local data = v2Profile({
		far = rec(A, "slot", SLOTS + 1),
		frac = rec(B, "slot", 1.5),
		neg = rec(C, "slot", -1),
		odd = rec(D, "museum", 3),
		rot = rec(A, "slot", 4, { rot = 33 }),
		nomods = rec(B, "storage", nil, { mods = "x" }),
	})
	local report = Inventory.Normalize(data, SLOTS, Items)
	check(
		data.items.far.place == "storage" and data.items.frac.place == "storage" and data.items.neg.place == "storage",
		"постамент вне музея, дробный и отрицательный — в инвентарь"
	)
	check(
		data.items.odd.place == "storage" and data.items.odd.slot == nil,
		"неизвестное место → инвентарь"
	)
	check(
		data.items.rot.rot == 0 and data.items.rot.place == "slot",
		"кривой поворот → 0, экспонат на месте"
	)
	check(type(data.items.nomods.mods) == "table", "mods восстановлены")
	check(report.total == 6, "все 6 записей на месте")
end

do
	-- Неизвестный предмет и нечитаемая запись: остаются в профиле; неизвестный — с постамента в инвентарь.
	local data = v2Profile({ ghost = rec("NoSuchItem", "slot", 1), broken = "???", ok = rec(A, "slot", 2) })
	local report = Inventory.Normalize(data, SLOTS, Items)
	check(
		data.items.ghost ~= nil and data.items.ghost.place == "storage",
		"неизвестный предмет остался, ушёл в инвентарь"
	)
	check(data.items.broken == "???", "нечитаемая запись не тронута")
	check(
		#report.unknown == 2 and data.items.ok.slot == 2,
		"в отчёте 2 неизвестных, обычный экспонат на месте"
	)
	local again = deepCopy(data)
	check(
		not Inventory.Normalize(again, SLOTS, Items).changed,
		"повтор после исправлений ничего не меняет"
	)
end

do
	-- Пустой профиль, профиль без items, чужой профиль не меняется.
	local empty = v2Profile({})
	Inventory.Normalize(empty, SLOTS, Items)
	check(
		empty.schema == 3 and next(empty.items) == nil,
		"пустой профиль: схема 3, предметов нет"
	)
	local noItems = { schema = 2 }
	Inventory.Normalize(noItems, SLOTS, Items)
	check(type(noItems.items) == "table", "профиль без items: таблица создана")
	local mine = v2Profile({ a = rec(A, "slot", 1), b = rec(A, "slot", 1) })
	local other = v2Profile({ c = rec(B, "slot", 1) })
	local otherBefore = deepCopy(other)
	Inventory.Normalize(mine, SLOTS, Items)
	check(
		deepEqual(other, otherBefore),
		"миграция одного профиля не трогает другой"
	)
end

do
	-- Большой инвентарь: 1000 экземпляров, 6 на постаментах — все сохраняются.
	local items = {}
	for i = 1, 1000 do
		items["big" .. i] =
			rec(ids[(i % #ids) + 1], if i <= SLOTS then "slot" else "storage", if i <= SLOTS then i else nil)
	end
	local data = v2Profile(items)
	local report = Inventory.Normalize(data, SLOTS, Items)
	local total, displayed = Inventory.Summary(data.items, Items)
	check(
		total == 1000 and displayed == SLOTS and #report.moved == 0,
		"1000 экземпляров: все на месте, выставлено " .. SLOTS
	)
end

print("Когда можно менять экспонаты и красть (D46):")
do
	local cfg = GameConfig.Time
	local length = GameTime.CycleLength()
	local base = cfg.Epoch + length * 1000 -- какой-то круг далеко от начала
	local doomStart = base + (cfg.DoomEvery - 1) * (cfg.DayLength + cfg.NightLength) + cfg.DayLength
	local prepStart = doomStart - cfg.PreparationLength
	local doomEnd = doomStart + cfg.DoomNightLength
	local cases = {
		{ base + cfg.DeliveryGrace + 1, nil, nil, "день 1 после окна доставки" },
		{ base + 150, nil, nil, "день" },
		{ base + cfg.DayLength + 5, nil, nil, "обычная ночь" },
		{ prepStart - 0.01, nil, nil, "за миг до подготовки" },
		{ prepStart, "lock", nil, "начало подготовки" },
		{ doomStart - 0.01, "lock", nil, "конец подготовки" },
		{ doomStart, "lock", "Open", "начало Судной ночи" },
		{ doomEnd - 0.01, "lock", "Open", "конец Судной ночи" },
		{ doomEnd, "lock", "Delivery", "начало 10 с доставки" },
		{ doomEnd + cfg.DeliveryGrace - 0.01, "lock", "Delivery", "конец 10 с доставки" },
		{ doomEnd + cfg.DeliveryGrace, nil, nil, "после доставки" },
	}
	for _, case in cases do
		local t, lock, theft, name = case[1], case[2], case[3], case[4]
		local gotLock = GameTime.ExhibitLock(t)
		local gotTheft = GameTime.TheftPhase(t)
		check(
			(gotLock ~= nil) == (lock ~= nil) and gotTheft == theft,
			("%s: менять %s, кража %s"):format(
				name,
				if gotLock then "нельзя" else "можно",
				tostring(gotTheft)
			)
		)
	end
	check(
		cfg.DeliveryGrace == 10 and cfg.PreparationLength == 120 and cfg.DoomNightLength == 90,
		"числа D37: 120 / 90 / 10"
	)
end

print(("Проверок: %d, не прошло: %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end
print("Все проверки инвентаря прошли")

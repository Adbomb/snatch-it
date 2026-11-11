--!nocheck
-- Проверка защиты музея и взлома без Roblox Studio (D37, D46, Shared/DefenseRules): цены по уровню (доля цены взлома),
-- капкан без цены не продаётся, когда покупать и ставить, лимит min(уровень, 5) и по одному виду, места на полу зала
-- (постаменты, вход, сундук, стены, расстояние между устройствами) — на настоящих координатах постаментов и сундука
-- (Util/PartBuilder), фиксированные места, годность взлома, возврат установленного до ночи (Settle).
-- Запуск из корня репозитория: lune run scripts/lune/check_defense.luau.

local process = require("@lune/process")

local Env = require("./env")

local Vector3 = Env.roblox.Vector3
local GameConfig = Env.Require("ReplicatedStorage.Shared.Config.GameConfig")
local MuseumLayout = Env.Require("ReplicatedStorage.Shared.Config.MuseumLayout")
local DefenseRules = Env.Require("ReplicatedStorage.Shared.DefenseRules")

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

local cfg = GameConfig.Defense

print("Цены (D37; уровни 7–10 — D56):")
do
	local hackOk = true
	for level, price in { 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 3e10, 8e10 } do
		hackOk = hackOk and DefenseRules.HackPrice(cfg, level) == price
	end
	check(hackOk, "взлом: 1K … 100M (D37), уровни 7–10 — 1B / 10B / 30B / 80B (D56)")
	check(DefenseRules.Price(cfg, "Trap", 1) == 100, "ловушка ур. 1 — 10 % от 1K")
	check(DefenseRules.Price(cfg, "Laser", 2) == 1500, "лазер ур. 2 — 15 % от 10K")
	check(DefenseRules.Price(cfg, "Door", 3) == 20000, "дверь ур. 3 — 20 % от 100K")
	check(DefenseRules.Price(cfg, "Robot", 10) == 2.4e10, "робот ур. 10 — 30 % от 80B")
	check(
		DefenseRules.Price(cfg, "Snare", 1) == nil,
		"капкан без утверждённой цены не продаётся"
	)
	check(
		DefenseRules.CanBuyDefense(cfg, "Snare", "Preparation", 1e15, 1) ~= nil,
		"капкан купить нельзя"
	)
end

print("Когда покупать и ставить:")
do
	check(
		DefenseRules.CanBuyDefense(cfg, "Trap", "Preparation", 100, 1) == nil,
		"ловушка в подготовку — можно"
	)
	check(DefenseRules.CanBuyDefense(cfg, "Trap", "Day", 1e9, 1) ~= nil, "ловушка днём — нельзя")
	check(
		DefenseRules.CanBuyDefense(cfg, "Trap", "DoomNight", 1e9, 1) ~= nil,
		"ловушка в Судную ночь — нельзя"
	)
	check(DefenseRules.CanBuyDefense(cfg, "Trap", "Preparation", 99, 1) ~= nil, "не хватает монет")
	check(
		DefenseRules.CanBuyDefense(cfg, "Bomb", "Preparation", 1e9, 1) ~= nil,
		"неизвестное устройство"
	)
	check(DefenseRules.CanBuyHack(cfg, 3, "Day", 1e5) == nil, "взлом днём — можно")
	check(
		DefenseRules.CanBuyHack(cfg, 3, "Preparation", 1e9) ~= nil,
		"взлом в подготовку — нельзя (заранее, днём)"
	)
	check(
		DefenseRules.CanBuyHack(cfg, 11, "Day", 1e15) ~= nil and DefenseRules.CanBuyHack(cfg, 1.5, "Day", 1e15) ~= nil,
		"уровни только 1…10"
	)
	check(
		DefenseRules.CanInstall(cfg, "Trap", "Preparation", 1, {}, 1) == nil,
		"поставить в подготовку"
	)
	check(
		DefenseRules.CanInstall(cfg, "Trap", "DoomNight", 1, {}, 1) ~= nil,
		"в Судную ночь не ставят"
	)
	check(
		DefenseRules.CanInstall(cfg, "Trap", "Preparation", 1, {}, 0) ~= nil,
		"не купил — не поставить"
	)
	check(
		DefenseRules.CanInstall(cfg, "Trap", "Preparation", 5, { Trap = true }, 2) ~= nil,
		"второй ловушки нет"
	)
end

print("Сколько устройств (min(уровень, 5)):")
do
	for level = 1, 10 do
		check(
			DefenseRules.MaxDevices(cfg, level) == math.min(level, 5),
			("уровень %d — %d"):format(level, math.min(level, 5))
		)
	end
	check(
		DefenseRules.CanInstall(cfg, "Laser", "Preparation", 1, { Trap = true }, 1) ~= nil,
		"музей ур. 1: второе устройство нельзя"
	)
	local five = { Trap = true, Laser = true, Door = true, Robot = true }
	check(DefenseRules.CanInstall(cfg, "Snare", "Preparation", 7, five, 1) == nil, "ур. 7: пятое — можно")
	five.Snare = true
	check(
		DefenseRules.CanInstall(cfg, "Trap", "Preparation", 10, five, 1) ~= nil,
		"шестого нет даже на ур. 10"
	)
end

print(
	"Где ставить (оси участка, постаменты и сундук — Config/MuseumLayout, D48-C):"
)
do
	local showcases = {}
	for _, place in MuseumLayout.Places do
		if place.slot <= GameConfig.Museum.SlotsByLevel[1] then
			table.insert(showcases, place.center)
		end
	end
	local chest = MuseumLayout.Chest.Center
	local function spot(x, z, others, galleries)
		return DefenseRules.CheckFreeSpot(cfg, Vector3.new(x, 0, z), showcases, chest, others or {}, galleries)
	end
	check(spot(7, 5) == nil, "боковой проход у павильона — можно")
	check(spot(0, 15) == nil, "за павильоном — можно")
	check(spot(0, 0) ~= nil and spot(0, 7) ~= nil, "на дорожке и в павильоне — нельзя")
	check(spot(5, -1) ~= nil, "у открытой двери сейфа — нельзя")
	check(spot(-14, 18) ~= nil, "угол у ниши — нельзя (постамент или урна)")
	check(spot(13, -8, nil, true) ~= nil and spot(22, 0, nil, true) ~= nil, "у арки и в галерее — нельзя")
	check(spot(13.4, -2) ~= nil and spot(-13.4, 10.2) ~= nil, "на постаменте — нельзя")
	check(spot(0, -9) ~= nil, "во входном коридоре — нельзя")
	check(spot(-12, -9) ~= nil, "у сундука — нельзя")
	check(
		spot(17, 5) ~= nil and spot(0, 25) ~= nil and spot(0, -14) ~= nil,
		"за стенами и снаружи — нельзя"
	)
	check(
		spot(7, 5, { Vector3.new(9, 0, 5) }) ~= nil,
		"вплотную к другому устройству — нельзя"
	)
	check(spot(0 / 0, 5) ~= nil, "NaN — нельзя")
	check(
		spot(-7, 5) == nil and spot(3, 16) == nil,
		"свободные места есть и в проходах, и за павильоном"
	)
end

print("Фиксированные места, взлом, списание:")
do
	check(DefenseRules.FixedSpots(cfg, "Door")[1] == "Entrance", "дверь — на входе")
	local lasers = DefenseRules.FixedSpots(cfg, "Laser")
	check(#lasers == 2, "лазер — 2 размеченных места прохода")
	check(DefenseRules.FixedSpots(cfg, "Trap") == nil, "ловушка — свободно")
	local laser = cfg.Lasers.Gallery
	check(DefenseRules.InLaser(cfg, laser, Vector3.new(0, 0, laser.z + 0.3)), "вор в луче")
	check(not DefenseRules.InLaser(cfg, laser, Vector3.new(0, 0, laser.z + 2)), "мимо луча")
	-- путь за такт (0.2 с): бегущий вор перешагивает луч шириной 1.2 между проверками — ловится по отрезку пути
	local before, after = Vector3.new(0, 0, laser.z - 1.5), Vector3.new(0, 0, laser.z + 1.5)
	check(
		not DefenseRules.InLaser(cfg, laser, before)
			and not DefenseRules.InLaser(cfg, laser, after)
			and DefenseRules.CrossedLaser(cfg, laser, before, after),
		"пробежал луч между тактами — лазер сработал"
	)
	check(
		not DefenseRules.CrossedLaser(cfg, laser, nil, after)
			and DefenseRules.CrossedLaser(cfg, laser, nil, Vector3.new(0, 0, laser.z)),
		"первый такт (нет прошлой точки) — только точка"
	)
	local side = laser.x1 + 2
	check(
		not DefenseRules.CrossedLaser(
			cfg,
			laser,
			Vector3.new(side, 0, laser.z - 1.5),
			Vector3.new(side, 0, laser.z + 1.5)
		),
		"прошёл сбоку от луча — не сработал"
	)
	check(
		DefenseRules.CrossedLaser(
			cfg,
			laser,
			Vector3.new(laser.x1 + 1, 0, laser.z - 1.5),
			Vector3.new(laser.x1 - 1, 0, laser.z + 1.5)
		),
		"наискосок через край луча — сработал"
	)
	check(
		not DefenseRules.CrossedLaser(cfg, laser, Vector3.new(-3, 0, laser.z + 1), Vector3.new(3, 0, laser.z + 1)),
		"вдоль луча рядом с ним — не сработал"
	)
	local center = Vector3.new(7, 0, -2)
	check(
		math.abs(DefenseRules.PathDistance(center, Vector3.new(7, 0, -5), Vector3.new(7, 0, 1)) - 0) < 1e-6,
		"пробежал через ловушку между тактами — расстояние 0"
	)
	check(
		math.abs(DefenseRules.PathDistance(center, nil, Vector3.new(10, 0, 2)) - 5) < 1e-6,
		"без прошлой точки — расстояние до точки"
	)
	check(
		math.abs(DefenseRules.PathDistance(center, Vector3.new(7, 0, -9), Vector3.new(7, 0, -6)) - 4) < 1e-6,
		"путь не дошёл до ловушки — до ближнего конца"
	)
	-- D52: зона срабатывания с высотой (радиус 2, высота 4; Y — корень над полом, стоя ≈ 3)
	local zone = function(from: Vector3?, to: Vector3): boolean
		return DefenseRules.ZoneHit(center, 2, 4, from, to)
	end
	check(zone(Vector3.new(7, 3, -6), Vector3.new(7, 3, 2)), "пробежал по полу через ловушку — касание")
	check(zone(nil, Vector3.new(7, 3, -1)) and not zone(nil, Vector3.new(7, 7, -1)), "точка: внутри низко — да, высоко — нет")
	check(
		not zone(Vector3.new(7, 3, -6), Vector3.new(7, 9, -2)) and not zone(Vector3.new(7, 9, -2), Vector3.new(7, 3, 2)),
		"прыжок: проверка в воздухе над ловушкой — перелёт, не касание (ни на подъёме, ни на спуске)"
	)
	check(
		not zone(Vector3.new(7, 3, -9), Vector3.new(7, 9, -5)) and zone(Vector3.new(7, 9, -5), Vector3.new(7, 3, -1)),
		"приземлился прямо в ловушку — касание"
	)
	check(not zone(Vector3.new(10, 3, -6), Vector3.new(10, 3, 2)), "прошёл в 3 ст. сбоку — не касание")
	check(zone(Vector3.new(7, 3, -2), Vector3.new(7, 3, -2)), "стоит в ловушке — касание")
	check(not zone(Vector3.new(7, 6, -12), Vector3.new(7, 6, 12)), "телепорт высоко над ловушкой — не касание")
	-- лазер: прыжок над лучом (на отрезке пересечения выше y + LaserHeight) — не касание
	local top = laser.y + cfg.LaserHeight
	check(
		DefenseRules.CrossedLaser(cfg, laser, Vector3.new(0, 3, laser.z - 1.5), Vector3.new(0, 3, laser.z + 1.5), 99),
		"лазер: пробежал понизу — касание"
	)
	check(
		not DefenseRules.CrossedLaser(
			cfg,
			laser,
			Vector3.new(0, top + 2, laser.z - 1.5),
			Vector3.new(0, top + 2, laser.z + 1.5),
			top
		),
		"лазер: перелетел выше луча — не касание"
	)
	check(
		not DefenseRules.CrossedLaser(cfg, laser, nil, Vector3.new(0, top + 1, laser.z), top),
		"лазер: стоит над лучом выше — не касание"
	)
	check(
		DefenseRules.HackFits(3, 3) and DefenseRules.HackFits(5, 2) and not DefenseRules.HackFits(2, 3),
		"взлом: уровень устройства ≥ уровня музея"
	)
	-- Списание при установке: вышел или упал сервер до ночи — вернётся; ночь началась — отработало.
	local nightStart = function(cycle)
		return cycle * 100 + 90
	end
	-- D56: запас — по уровням покупки; устройство возвращается в запас своего уровня
	local before = {
		owned = { Robot = { L2 = 1 } },
		installed = { Trap = { cycle = 3, level = 2 }, Laser = { cycle = 3, level = 1 } },
	}
	check(
		DefenseRules.Settle(before, 3 * 100 + 50, nightStart, 2) == 2
			and before.owned.Trap.L2 == 1
			and before.owned.Laser.L1 == 1
			and before.owned.Robot.L2 == 1,
		"до Судной ночи — устройства вернулись в запас своего уровня покупки"
	)
	local during = { owned = {}, installed = { Trap = { cycle = 3, level = 2 } } }
	check(
		DefenseRules.Settle(during, 3 * 100 + 95, nightStart, 2) == 0 and during.owned.Trap == nil,
		"вышел посреди ночи и вернулся — запас не вернулся"
	)
	check(
		next(during.installed) == nil and next(before.installed) == nil,
		"отметки об установке очищены"
	)
	check(cfg.Snare.Seconds == 10 and cfg.HackSeconds == 5, "капкан 10 с, взлом 5 с — D37")
end

print("Защита привязана к уровню музея (D56):")
do
	local owned = {}
	DefenseRules.Add(owned, "Trap", 1, 2)
	DefenseRules.Add(owned, "Trap", 3)
	DefenseRules.Add(owned, "Robot", 3, 1)
	check(
		owned.Trap.L1 == 2 and owned.Trap.L3 == 1 and owned.Robot.L3 == 1,
		"покупка записывается за уровнем музея"
	)
	check(
		DefenseRules.Stock(owned, "Trap", 1) == 2
			and DefenseRules.Stock(owned, "Trap", 3) == 1
			and DefenseRules.Stock(owned, "Trap", 2) == 0
			and DefenseRules.Stock(owned, "Door", 1) == 0,
		"запас считается отдельно по каждому уровню"
	)
	check(
		DefenseRules.OtherStock(owned, "Trap", 3) == 2 and DefenseRules.OtherStock(owned, "Robot", 3) == 0,
		"устройства других уровней считаются отдельно"
	)
	-- установка: только устройством своего уровня
	check(
		DefenseRules.CanInstall(
			cfg,
			"Trap",
			"Preparation",
			3,
			{},
			DefenseRules.Stock(owned, "Trap", 3),
			DefenseRules.OtherStock(owned, "Trap", 3)
		) == nil,
		"устройство уровня 3 на музей уровня 3 — можно"
	)
	local refusal = DefenseRules.CanInstall(
		cfg,
		"Trap",
		"Preparation",
		2,
		{},
		DefenseRules.Stock(owned, "Trap", 2),
		DefenseRules.OtherStock(owned, "Trap", 2)
	)
	check(
		refusal ~= nil and string.find(refusal, "другого уровня", 1, true) ~= nil,
		"на музей уровня 2 устройства уровней 1 и 3 не ставятся (причина — другой уровень)"
	)
	check(
		DefenseRules.CanInstall(cfg, "Door", "Preparation", 2, {}, 0, 0) == "Сначала купите это устройство",
		"нет устройства никакого уровня — «сначала купите»"
	)
	check(
		DefenseRules.Take(owned, "Trap", 1) and owned.Trap.L1 == 1 and owned.Trap.L3 == 1,
		"списание — только из запаса своего уровня"
	)
	check(
		not DefenseRules.Take(owned, "Trap", 2) and owned.Trap.L1 == 1 and owned.Trap.L3 == 1,
		"списать устройство другого уровня нельзя"
	)
	check(DefenseRules.Take(owned, "Trap", 1) and owned.Trap.L1 == nil, "последнее списано — ключ уровня убран")
	local stale = DefenseRules.Stale({ Trap = { L1 = 2, L5 = 1, L4 = 3 }, Door = { L4 = 1 }, Laser = {} }, 4)
	check(
		#stale.Trap == 2
			and stale.Trap[1].level == 1
			and stale.Trap[1].count == 2
			and stale.Trap[2].level == 5
			and stale.Door == nil
			and stale.Laser == nil,
		"список прежних уровней: без своего уровня, по возрастанию"
	)
	local at = DefenseRules.StockAt({ Trap = { L1 = 2, L4 = 3 }, Door = { L4 = 1 }, Robot = { L2 = 1 } }, 4)
	check(at.Trap == 3 and at.Door == 1 and at.Robot == nil, "запас музея этого уровня: вид → количество")

	-- миграция прежнего формата: сохранённый уровень музея игрока (не обязательно 1), ничего не теряется
	for _, level in { 1, 3, 7, 10 } do
		local old = {
			owned = { Trap = 2, Robot = 1, Snare = 0, Laser = 3.9, Door = -1 },
			hacks = { L2 = 1 },
			installed = { Door = 12 },
		}
		local key = "L" .. level
		local moved = DefenseRules.Normalize(old, level)
		check(
			moved == 7
				and old.owned.Trap[key] == 2
				and old.owned.Robot[key] == 1
				and old.owned.Laser[key] == 3
				and next(old.owned.Snare) == nil
				and next(old.owned.Door) == nil
				and old.hacks.L2 == 1
				and old.installed.Door.cycle == 12
				and old.installed.Door.level == level,
			("прежний формат → музей уровня %d: количества сохранены, взлом не тронут"):format(level)
		)
		local again = DefenseRules.Normalize(old, if level < 10 then level + 1 else 1)
		check(
			again == 0 and old.owned.Trap[key] == 2 and old.installed.Door.level == level,
			("повторная проверка (уровень музея уже другой) ничего не переносит: уровень %d"):format(level)
		)
	end
	local mixed = { owned = { Trap = { L2 = 1, L11 = 5, junk = 2, L3 = 0 }, Bomb = 4, Robot = "x" } }
	DefenseRules.Normalize(mixed, 5)
	check(
		mixed.owned.Trap.L2 == 1
			and mixed.owned.Trap.L11 == nil
			and mixed.owned.Trap.junk == nil
			and mixed.owned.Trap.L3 == nil
			and mixed.owned.Bomb.L5 == 4
			and next(mixed.owned.Robot) == nil
			and type(mixed.hacks) == "table"
			and type(mixed.installed) == "table",
		"мусор убран, неизвестный вид с количеством сохранён, недостающие поля созданы"
	)
	local empty = {}
	check(
		DefenseRules.Normalize(empty, nil) == 0 and next(empty.owned) == nil and next(empty.installed) == nil,
		"пустая запись и уровень не числом — без ошибок"
	)
	-- прежняя запись об установке без уровня: при возврате — сохранённый уровень музея
	local nightStart = function(cycle)
		return cycle * 100 + 90
	end
	local legacy = { owned = { Trap = 1 }, installed = { Trap = 3, Laser = 3 } }
	check(
		DefenseRules.Settle(legacy, 3 * 100 + 50, nightStart, 6) == 2
			and legacy.owned.Trap.L6 == 2
			and legacy.owned.Laser.L6 == 1,
		"прежний формат установленного: вернулось на сохранённый уровень музея 6"
	)
	check(
		DefenseRules.LevelKey(4) == "L4" and DefenseRules.KeyLevel("L10") == 10 and DefenseRules.KeyLevel("L0") == nil,
		"ключи уровней L1…L10"
	)
end

print(("Проверок: %d, не прошло: %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end
print("Все проверки защиты прошли")

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

print("Цены (D37):")
do
	check(DefenseRules.HackPrice(cfg, 1) == 1e3 and DefenseRules.HackPrice(cfg, 10) == 1e12, "взлом: 1K … 1T")
	check(DefenseRules.Price(cfg, "Trap", 1) == 100, "ловушка ур. 1 — 10 % от 1K")
	check(DefenseRules.Price(cfg, "Laser", 2) == 1500, "лазер ур. 2 — 15 % от 10K")
	check(DefenseRules.Price(cfg, "Door", 3) == 20000, "дверь ур. 3 — 20 % от 100K")
	check(DefenseRules.Price(cfg, "Robot", 10) == 3e11, "робот ур. 10 — 30 % от 1T")
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
	local before = { owned = { Trap = 0, Robot = 1 }, installed = { Trap = 3, Laser = 3 } }
	check(
		DefenseRules.Settle(before, 3 * 100 + 50, nightStart) == 2
			and before.owned.Trap == 1
			and before.owned.Laser == 1,
		"до Судной ночи — устройства вернулись в запас"
	)
	local during = { owned = { Trap = 0 }, installed = { Trap = 3 } }
	check(
		DefenseRules.Settle(during, 3 * 100 + 95, nightStart) == 0 and during.owned.Trap == 0,
		"вышел посреди ночи и вернулся — запас не вернулся"
	)
	check(
		next(during.installed) == nil and next(before.installed) == nil,
		"отметки об установке очищены"
	)
	check(cfg.Snare.Seconds == 10 and cfg.HackSeconds == 5, "капкан 10 с, взлом 5 с — D37")
end

print(("Проверок: %d, не прошло: %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end
print("Все проверки защиты прошли")

-- Раскладка карты (D36, утверждённый рисунок заказчика; D22) только данными. Безопасная зона — поле травы между
-- земляными обрывами: у дальней стены (+Z) пять музеев в ряд входом к полю, у каждого спереди слева (по +X —
-- левая рука игрока, смотрящего на музеи) поле качалки с огромной гантелью и табличкой «Улучшение»; у переднего
-- края — лавки «Аура» и «Продажа» по бокам от коридора уровней. Коридор уходит в -Z: 10 зон подряд, игрок
-- проходит зону N, чтобы попасть в N+1. Ни от чего не зависит, кроме GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

local MapLayout = {}

-- Обрыв (D75, решение владельца 2026-11-28): безопасная зона кончается обрывом, трасса зон лежит ниже на Drop.
-- С края обрыва игрок бросает Ловибум; вниз ведут спуски в полосах бега (Ramp).
MapLayout.Drop = 10

-- Высоты верхних граней поверхностей: разные, чтобы плоскости не мерцали (у Baseplate шаблона верх на 0).
MapLayout.Heights = {
	Ground = 0.1, -- трава безопасной зоны
	Water = -1.2, -- уровень воды вокруг острова
	Track = 0.1 - MapLayout.Drop, -- земля коридора зон (под плитами полов)
	Path = 0.3 - MapLayout.Drop, -- полы зон
	Floor = 1.4, -- пол музеев (PartBuilder.FloorTop): на ступень выше травы
}

-- Безопасная зона: от входа в коридор (z = 0) до дальней стены; коридор уровней — полоса ±CorridorHalf.
MapLayout.SafeZone = { halfX = 183, back = 131 }
MapLayout.CorridorHalf = 92

-- Обрывы (D36): земля 30 с травой поверху; у безопасной зоны сзади и по бокам — уступом: нижняя терраса
-- Low высотой и Terrace вглубь, за ней верхний обрыв. Outer — ширина плато за обрывом.
MapLayout.Cliff = {
	height = 30,
	grass = 3,
	low = 12,
	lowGrass = 2,
	terrace = 14,
	outer = 60,
	lip = 1, -- трава нависает над гранью обрыва
}

-- Участки: центр музея (44 × 44, вход в -Z) — PlotCFrame. Участок 1 — по +X (левая рука игрока).
local PLOT_XS = { 150, 75, 0, -75, -150 }
local PLOT_Z = 100
assert(
	#PLOT_XS == GameConfig.World.PlotCount,
	"MapLayout: число участков не совпадает с GameConfig.World.PlotCount"
)

function MapLayout.PlotCFrame(index: number): CFrame
	return CFrame.new(PLOT_XS[index], 0, PLOT_Z)
end

-- Поле качалки и табличка «Улучшение» — в координатах участка (x — от центра музея, z < -22 — перед фасадом).
MapLayout.PlotYard = {
	field = Vector2.new(20, -32),
	sign = Vector2.new(7, -30),
}

-- Лавки у переднего края по бокам от входа в коридор, лицом к полю (D41: павильоны World/Models/Shops).
MapLayout.Shops = {
	{ title = "Аура", position = Vector3.new(MapLayout.CorridorHalf + 4, 0, 24) },
	{ title = "Продажа", position = Vector3.new(-MapLayout.CorridorHalf - 4, 0, 24) },
}
MapLayout.ShopScale = 1.45 -- павильоны World/Models/Shops крупнее в 1.45 раза: видны от точки появления (D41)

-- Точка появления посередине поля, лицом к музеям.
MapLayout.Spawn = { position = Vector3.new(0, MapLayout.Heights.Ground, 40), size = Vector3.new(8, 0.4, 8) }

-- Полоса броска вдаль (D75): вдоль края обрыва у входа в коридор, между спусками; площадки нет. Игрок на полосе
-- (|x| ≤ halfX, z от края обрыва до z1) видит шкалу и бросает; сервер проверяет то же место (InThrowEdge).
-- z0…z1 — сама светлая полоса на траве (за красной линией Safe Zone).
MapLayout.ThrowEdge = { halfX = 46, z0 = 1.3, z1 = 10.3 }

function MapLayout.InThrowEdge(position: Vector3): boolean
	local edge = MapLayout.ThrowEdge
	-- запас 6 по z: сервер видит бегущего игрока позади его настоящего места (задержка сети)
	return math.abs(position.X) <= edge.halfX + 3 and position.Z >= -1.5 and position.Z <= edge.z1 + 6
end

-- Середина полосы броска: куда ставят игрока тесты и где появляется награда, если игрока уже нет.
MapLayout.ThrowSpot = Vector3.new(0, MapLayout.Heights.Ground, (MapLayout.ThrowEdge.z0 + MapLayout.ThrowEdge.z1) / 2)

-- Спуски с безопасной зоны на трассу (обрыв D75): в полосах бега D66 по обе стороны, клином вглубь зоны 1.
-- |x| от x0 до x1 (уже полосы: рядом, на x 46…48, — место обучения D55), длина — по z от края обрыва.
MapLayout.Ramp = { x0 = 52, x1 = 66, length = 30 }

-- Коридор зон. Вход в зону 1 — край обрыва (z = 0). Все зоны одной длины ZoneSize (решение владельца 2026-11-28,
-- по его записи референса: зоны одинаковые, их просто много). ZoneLength — на случай зон разной длины; обрыв вдоль
-- коридора — одна деталь, предел Roblox 2 048 стадов.
MapLayout.ZoneSize = 95
MapLayout.ZoneGrowth = 1

function MapLayout.ZoneLength(index: number): number
	return math.round(MapLayout.ZoneSize * MapLayout.ZoneGrowth ^ (index - 1))
end
MapLayout.ZoneHalfWidth = MapLayout.CorridorHalf
-- Рамок, ворот и стен между зонами нет (D41): зоны различают пол с узором, полоса-граница и голограмма названия.
MapLayout.HologramSize = Vector2.new(40, 7) -- надпись уровня, стадов (D49: только название)
-- Масштаб надписи по зоне (id из GameConfig.Zones), остальные — 1. «ПУСТЫНЯ» на 35 % меньше (решение владельца
-- 2026-11-13): крупная надпись перекрывала площадку Сфинкса на подходе.
MapLayout.HologramScale = { Desert = 0.65 } :: { [string]: number }
-- Центр надписи над полом: низ на 16.5 — выше головы и выше боссов (пёс 9.8, торговец 14.9), не мешает обзору.
MapLayout.HologramHeight = 20
MapLayout.HologramInset = 10 -- от входа в зону вглубь
MapLayout.PylonX = 86 -- светящиеся столбики на границах зон, у обрывов
-- Сквозные полосы (D66): во всех 10 зонах по обе стороны от площадки босса — прямой свободный бег от входа до выхода
-- зоны. В полосах |x| Lane[1]..Lane[2] нет ни одной твёрдой детали на высоте LaneHeight[1]..LaneHeight[2] над полом
-- зоны (ступени и поддоны ниже — пробегаются, крыши и мосты выше — не мешают). Проверка — scripts/lune/check_world.
MapLayout.Lane = { 48, 66 }
MapLayout.LaneHeight = { 1.1, 7 }
MapLayout.SafeLabel = Vector2.new(54, 6) -- надпись «БЕЗОПАСНАЯ ЗОНА» на траве у входа в коридор
-- Ночной барьер (D41): сплошная стена во всю ширину коридора на входе в опасную зону, только ночью.
MapLayout.Barrier = { height = 28, thickness = 1 }
local ZONES_START = 0
local ZONE_COUNT = #GameConfig.Zones
local STARTS: { number } = {} -- мировая z входа в зону; [ZONE_COUNT + 1] — конец трассы
do
	local z = ZONES_START
	for index = 1, ZONE_COUNT do
		STARTS[index] = z
		z -= MapLayout.ZoneLength(index)
	end
	STARTS[ZONE_COUNT + 1] = z
end
MapLayout.ZonesEnd = STARTS[ZONE_COUNT + 1]

-- Опасная зона (D37): коридор уровней — от входа в зону 1 (z = 0) вглубь, в ширину коридора.
function MapLayout.InDangerZone(position: Vector3): boolean
	return position.Z < ZONES_START and math.abs(position.X) <= MapLayout.CorridorHalf + 2
end

-- Мировая z входа в зону index (сторона безопасной зоны).
function MapLayout.ZoneStartZ(index: number): number
	return STARTS[index]
end

-- CFrame зоны: центр пола, -Z смотрит на вход (к безопасной зоне), +Z — на выход в следующую зону.
function MapLayout.ZoneCFrame(index: number): CFrame
	local center = Vector3.new(0, MapLayout.Heights.Path, STARTS[index] - MapLayout.ZoneLength(index) / 2)
	return CFrame.lookAt(center, center + Vector3.new(0, 0, 1))
end

-- Точка перед входом в зону (снаружи, по центру проёма) — куда возвращать игрока.
function MapLayout.ZoneEntrance(index: number): Vector3
	return Vector3.new(0, MapLayout.Heights.Path, MapLayout.ZoneStartZ(index) + 4)
end

-- Куда ночью уводить всех из зон (D21): поле перед входом в коридор.
MapLayout.NightReturn = Vector3.new(0, MapLayout.Heights.Ground, 12)

-- Босс и его 4 предмета (D37) в локальных координатах зоны (x поперёк коридора, z от центра; вход на
-- z = -Size/2). Босс — в центре зоны (круг радиусом 16 свободен от оформления во всех зонах), постаменты
-- раскиданы вокруг него не в ряд; мимо проходят по бокам коридора.
MapLayout.BossSpot = Vector2.new(0, -5)
MapLayout.ArtSlots = {
	Vector2.new(-12, -13),
	Vector2.new(11, -11),
	Vector2.new(-9, 7),
	Vector2.new(13, 5),
}
MapLayout.PedestalHeight = 2.5

-- Площадка босса (D43): у зоны с записью предметы стоят прямо на площадке вокруг босса, без постаментов, каждый со
-- своим поворотом (turn, градусы вокруг вертикали; 0 — как на постаменте). Места те же, что у постаментов (ArtSlots),
-- top — высота площадки над полом зоны под предметами, radius — край площадки от места босса (декор — за ним).
-- Площадку строит декор зоны (World/Models/FleaMarket, SubwayStation). Зоны без записи — постаменты D37.
MapLayout.Arenas = {
	[2] = {
		top = 0.3,
		radius = 24,
		turns = { 28, -40, 115, -150 },
	},
	-- «Королевский люк» (D54): предметы на бархатных подушках, верх подушки — top (World/Models/SubwayStation).
	[3] = {
		top = 0.6,
		radius = 24,
		turns = { -25, 40, 145, -125 },
	},
	-- «Ложе Сфинкса» (D59): Сфинкс лежит на ковре 16 × 34 (лапы к входу), поэтому места существ — свои, дальше общих
	-- ArtSlots (slots, в координатах зоны): на краю площадки r 31, не под боссом и не на ковре; верх плиты — top.
	[4] = {
		floor = 0.34, -- верх поля площадки: на нём стоит и ходит Сфинкс (место босса — BossService.HomeOf)
		top = 0.58,
		radius = 31,
		turns = { -35, 30, 150, -140 },
		slots = { Vector2.new(-22, -18), Vector2.new(23, -16), Vector2.new(-22, 12), Vector2.new(21, 13) },
	},
	-- «Замёрзшее озеро» (D64, World/Models/GlacierHall): Йети (рост 24.7) стоит в центре на верху мозаики (floor), во сне
	-- глыба — рядом справа; места существ — на краю площадки r 32, не под Йети и не у глыбы; верх плиты — top.
	[5] = {
		floor = 0.7,
		top = 1.08,
		radius = 32,
		turns = { -35, 30, 150, -140 },
		slots = { Vector2.new(-22, -18), Vector2.new(23, -16), Vector2.new(-22, 12), Vector2.new(21, 13) },
	},
}

-- Временные тестовые площадки закрытых боссов (этап C босса 10, 2026-11-15): только в Studio с DevMode — там, где
-- закрытый босс вообще строится (BossService.ClosedAllowed); в опубликованной игре их нет. Площадка — ровный пол сбоку
-- от карты (x — центр, за коридором ±CorridorHalf), в полосе z своей зоны: D49 держит бойца в зоне по z. Зона, её
-- декор и пути не меняются. Удалить площадку — убрать запись (и World/Models/TestArena).
MapLayout.TestArenas = {
	[10] = { x = 330, size = Vector2.new(150, 92) },
} :: { [number]: { x: number, size: Vector2 } }

-- Место обучения (D55) в зоне 1 «Свалка»: у входа слева, вне круга настоящего пса и мест его предметов, на свободной
-- от декора площадке (проверено по кирпичам Junkyard). creature — учебное существо, dog — личный учебный пёс.
MapLayout.Tutorial = { zone = 1, creature = Vector2.new(-46, -36), dog = Vector2.new(-48, -16) }

-- CFrame низа учебного существа (лицом ко входу) и места личного пса (лицом к существу).
function MapLayout.TutorialPoints(): (CFrame, CFrame)
	local cfg = MapLayout.Tutorial
	local frame = MapLayout.ZoneCFrame(cfg.zone)
	local creature = frame * CFrame.new(cfg.creature.X, 0, cfg.creature.Y)
	local dogAt = (frame * CFrame.new(cfg.dog.X, 0, cfg.dog.Y)).Position
	return creature, CFrame.lookAt(dogAt, Vector3.new(creature.Position.X, dogAt.Y, creature.Position.Z))
end

-- Границы острова (трава и плато за обрывами) — для земли и воды вокруг.
local cliff = MapLayout.Cliff
local OUTER_X = MapLayout.SafeZone.halfX + cliff.terrace + cliff.outer
MapLayout.Island = {
	minX = -OUTER_X,
	maxX = OUTER_X,
	minZ = MapLayout.ZonesEnd - cliff.outer,
	maxZ = MapLayout.SafeZone.back + cliff.terrace + cliff.outer,
}

-- Точки предметов у боссов: верх постаментов (D37), лицом ко входу в зону; у зоны с площадкой (Arenas) — на
-- площадке, со своим поворотом (у площадки со своими местами slots — на них).
export type ArtSlotPoint = { name: string, cframe: CFrame, zone: number, slot: number }

function MapLayout.ArtSlotPoints(): { ArtSlotPoint }
	local points: { ArtSlotPoint } = {}
	for zone = 1, ZONE_COUNT do
		local frame = MapLayout.ZoneCFrame(zone)
		local arena = MapLayout.Arenas[zone]
		for slot, spot in (arena and arena.slots) or MapLayout.ArtSlots do
			local top = if arena
				then frame * CFrame.new(spot.X, arena.top, spot.Y) * CFrame.Angles(0, math.rad(arena.turns[slot]), 0)
				else frame * CFrame.new(spot.X, MapLayout.PedestalHeight, spot.Y)
			local name = ("Boss%d_Slot%d"):format(zone, slot)
			table.insert(points, { name = name, cframe = top, zone = zone, slot = slot })
		end
	end
	return points
end

return MapLayout

-- Раскладка карты (D35, D22) только данными. База — прямоугольник: 5 музеев в линию фасадом к зонам (-Z),
-- перед каждым — двор с полем качалки, огромной гантелью и табличкой «Улучшение» (D34); перед дворами —
-- площадь с фонтаном и точкой появления; на краю площади — ворота, за ними короткий двор и 10 зон одним
-- прямым коридором: игрок проходит зону N, чтобы попасть в N+1. Вокруг острова стена, холмы, песок и вода.
-- Ни от чего не зависит, кроме GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

local MapLayout = {}

-- Высоты верхних граней поверхностей: разные, чтобы плоскости не мерцали (у Baseplate шаблона верх на 0).
MapLayout.Heights = {
	Ground = 0.1,
	Sand = -0.2, -- песчаный берег
	Water = -1.2, -- уровень воды
	Path = 0.3, -- двор перед зонами, полы зон
	Plaza = 0.4, -- площадь и дворы участков
	Floor = 1.4, -- пол музеев (PartBuilder.FloorTop): на ступень выше площади
}

-- Ворота в зоны на краю площади; за ними двор до первой зоны.
MapLayout.Gate = { z = -130, width = 60 }
MapLayout.Yard = 12 -- длина двора между воротами и входом в зону 1

-- Участки (D35): музей 44 × 44 (центр — PlotCFrame), перед фасадом двор глубиной YardDepth, между музеями
-- проходы. Координаты двора — в системе участка: x вправо, вход в -Z, фасад на z = -22.
local PLOT_HALF = GameConfig.World.PlotSize.X / 2
MapLayout.PlotStep = 58 -- между центрами музеев (проход 14)
MapLayout.YardDepth = 26
MapLayout.PlazaDepth = 50
local PLAZA_FRONT = MapLayout.Gate.z + MapLayout.PlazaDepth -- граница площади и дворов
local PLOT_Z = PLAZA_FRONT + MapLayout.YardDepth + PLOT_HALF

function MapLayout.PlotCFrame(index: number): CFrame
	local x = (index - (GameConfig.World.PlotCount + 1) / 2) * MapLayout.PlotStep
	return CFrame.new(x, 0, PLOT_Z) -- без поворота: вход (-Z участка) смотрит к зонам
end

local yardMidZ = -PLOT_HALF - MapLayout.YardDepth / 2
MapLayout.PlotYard = {
	center = Vector2.new(0, yardMidZ), -- середина двора
	size = Vector2.new(PLOT_HALF * 2, MapLayout.YardDepth),
	path = 12, -- ширина дорожки ко входу
	field = Vector2.new(PLOT_HALF - 7.5, yardMidZ - 1), -- центр поля качалки (справа от дорожки)
	sign = Vector2.new(-PLOT_HALF + 8, yardMidZ + 6), -- табличка «Улучшение» (слева от дорожки)
}

-- Площадь от ворот до дворов; точка появления смотрит на музеи, фонтан — между ней и воротами.
local BASE_X = MapLayout.PlotStep * (GameConfig.World.PlotCount - 1) / 2 + PLOT_HALF + 20
MapLayout.Plaza = { minX = -BASE_X, maxX = BASE_X, minZ = MapLayout.Gate.z, maxZ = PLAZA_FRONT }
MapLayout.Spawn = {
	position = Vector3.new(0, MapLayout.Heights.Plaza, PLAZA_FRONT - 15),
	size = Vector3.new(8, 0.6, 8),
}
MapLayout.Fountain = Vector3.new(0, MapLayout.Heights.Plaza, MapLayout.Gate.z + 17)
MapLayout.CheckSize = 6 -- сторона клетки мостовой площади

-- Коридор зон: ширина, длина зоны, проём ворот между зонами.
MapLayout.ZoneSize = 60
MapLayout.ZoneHalfWidth = 30
MapLayout.ZoneDoor = 16 -- ширина проёма ворот зоны
MapLayout.ZoneWallHeight = 8
local ZONES_START = MapLayout.Gate.z - MapLayout.Yard
local ZONE_COUNT = #GameConfig.Zones

-- Мировая z входа в зону index (сторона площади).
function MapLayout.ZoneStartZ(index: number): number
	return ZONES_START - (index - 1) * MapLayout.ZoneSize
end

-- CFrame зоны: центр пола, -Z смотрит на вход (к площади), +Z — на выход в следующую зону.
function MapLayout.ZoneCFrame(index: number): CFrame
	local center = Vector3.new(0, MapLayout.Heights.Path, MapLayout.ZoneStartZ(index) - MapLayout.ZoneSize / 2)
	return CFrame.lookAt(center, center + Vector3.new(0, 0, 1))
end

-- Точка перед входом в зону (снаружи, по центру проёма) — куда возвращать игрока.
function MapLayout.ZoneEntrance(index: number): Vector3
	return Vector3.new(0, MapLayout.Heights.Path, MapLayout.ZoneStartZ(index) + 4)
end

-- Куда ночью уводить всех из зон (D21): площадь перед воротами.
MapLayout.NightReturn = Vector3.new(0, MapLayout.Heights.Plaza, MapLayout.Gate.z + 6)

-- Постаменты в локальных координатах зоны (x поперёк коридора, z от входа вглубь, вход на z = -Size/2).
MapLayout.Pedestals = {
	Vector2.new(-18, 2),
	Vector2.new(18, 2),
	Vector2.new(0, 10),
	Vector2.new(-12, 20),
	Vector2.new(12, 20),
}
MapLayout.PedestalHeight = 2.5
MapLayout.GuardSpot = Vector2.new(0, -14) -- место босса (шаг 5)

-- Контур острова по часовой стрелке (вид сверху): база с музеями и площадью и узкий коридор зон.
-- Стена-граница идёт по контуру, холмы, песок и вода — снаружи.
local ISLAND_X = BASE_X + 2
local ISLAND_TOP = PLOT_Z + PLOT_HALF + 24 -- за музеями место под деревья
local zonesEnd = ZONES_START - ZONE_COUNT * MapLayout.ZoneSize
MapLayout.Outline = {
	Vector2.new(-ISLAND_X, ISLAND_TOP),
	Vector2.new(ISLAND_X, ISLAND_TOP),
	Vector2.new(ISLAND_X, MapLayout.Gate.z),
	Vector2.new(MapLayout.ZoneHalfWidth, MapLayout.Gate.z),
	Vector2.new(MapLayout.ZoneHalfWidth, zonesEnd),
	Vector2.new(-MapLayout.ZoneHalfWidth, zonesEnd),
	Vector2.new(-MapLayout.ZoneHalfWidth, MapLayout.Gate.z),
	Vector2.new(-ISLAND_X, MapLayout.Gate.z),
}

-- Прямоугольники острова (для земли и пятен травы): база и коридор.
export type Rect = { minX: number, maxX: number, minZ: number, maxZ: number }
MapLayout.IslandRects = {
	{ minX = -ISLAND_X, maxX = ISLAND_X, minZ = MapLayout.Gate.z, maxZ = ISLAND_TOP },
	{ minX = -MapLayout.ZoneHalfWidth, maxX = MapLayout.ZoneHalfWidth, minZ = zonesEnd, maxZ = MapLayout.Gate.z },
} :: { Rect }
MapLayout.GrassMargin = 110 -- трава за стеной (под холмами)
MapLayout.SandMargin = 150 -- песок до воды

-- Точки появления предметов: верх постаментов в зонах (D15).
export type SpawnPoint = { name: string, position: Vector3, zone: number }

function MapLayout.SpawnPoints(): { SpawnPoint }
	local points: { SpawnPoint } = {}
	for zone = 1, ZONE_COUNT do
		local frame = MapLayout.ZoneCFrame(zone)
		for i, spot in MapLayout.Pedestals do
			local top = frame * CFrame.new(spot.X, MapLayout.PedestalHeight, spot.Y)
			table.insert(points, { name = ("Zone%d_%d"):format(zone, i), position = top.Position, zone = zone })
		end
	end
	return points
end

return MapLayout

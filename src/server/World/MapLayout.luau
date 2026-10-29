-- Раскладка карты (D12, D22) только данными. Аллея идёт вдоль оси Z: начало (точка появления, качалка) на +Z,
-- ворота в зоны на -Z. Музеи — по 4 с каждой стороны, входом на аллею. За воротами короткий двор и 10 зон
-- одним прямым коридором: игрок проходит зону N, чтобы попасть в N+1. Остров — аллея и коридор, вокруг
-- стена, холмы, песок и вода. Ни от чего не зависит, кроме GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

local MapLayout = {}

-- Высоты верхних граней поверхностей: разные, чтобы плоскости не мерцали (у Baseplate шаблона верх на 0).
MapLayout.Heights = {
	Ground = 0.1,
	Sand = -0.2, -- песчаный берег
	Water = -1.2, -- уровень воды
	Path = 0.3, -- двор перед зонами, полы зон
	Alley = 0.4, -- аллея, качалка
	Floor = 1.4, -- пол музеев (PartBuilder.FloorTop): на ступень выше аллеи
}

MapLayout.Alley = {
	halfWidth = 20,
	startZ = 130, -- начало аллеи (точка появления)
	endZ = -130, -- ворота в зоны
	curbWidth = 1.5,
	checkSize = 6, -- сторона клетки мостовой
}

MapLayout.Spawn = { position = Vector3.new(0, MapLayout.Heights.Alley, 122), size = Vector3.new(8, 0.6, 8) }
MapLayout.Fountain = Vector3.new(0, MapLayout.Heights.Alley, 104)

-- Музеи: М1–М4 слева (x < 0) от начала к воротам, М5–М8 справа. Вход (сторона -Z участка) — на аллею.
local PLOT_X = 44
local PLOT_ZS = { 62, 12, -38, -88 }
local plotSpecs = {}
for _, z in PLOT_ZS do
	table.insert(plotSpecs, { Vector3.new(-PLOT_X, 0, z), Vector3.new(1, 0, 0) })
end
for _, z in PLOT_ZS do
	table.insert(plotSpecs, { Vector3.new(PLOT_X, 0, z), Vector3.new(-1, 0, 0) })
end
assert(#plotSpecs == GameConfig.World.PlotCount, "MapLayout: число участков не совпадает с GameConfig.World.PlotCount")

function MapLayout.PlotCFrame(index: number): CFrame
	local spec = plotSpecs[index]
	return CFrame.lookAt(spec[1], spec[1] + spec[2])
end

-- Качалка (D31) в начале аллеи слева: поле, в середине огромная гантель, вывеска смотрит на аллею (+X).
MapLayout.Gym = {
	center = Vector3.new(-44, MapLayout.Heights.Alley, 110),
	size = Vector2.new(44, 36), -- по X и по Z
	field = Vector2.new(28, 24), -- поле, где качаются
}

-- Сквер напротив качалки.
MapLayout.Garden = { center = Vector3.new(44, MapLayout.Heights.Ground, 110), size = Vector2.new(44, 36) }

-- Ворота в конце аллеи; за ними двор до первой зоны.
MapLayout.Gate = { z = MapLayout.Alley.endZ, width = MapLayout.Alley.halfWidth * 2 }
MapLayout.Yard = 12 -- длина двора между воротами аллеи и входом в зону 1

-- Коридор зон: ширина, длина зоны, проём ворот между зонами.
MapLayout.ZoneSize = 60
MapLayout.ZoneHalfWidth = 30
MapLayout.ZoneDoor = 16 -- ширина проёма ворот зоны
MapLayout.ZoneWallHeight = 8
local ZONES_START = MapLayout.Gate.z - MapLayout.Yard
local ZONE_COUNT = #GameConfig.Zones

-- Мировая z входа в зону index (сторона аллеи).
function MapLayout.ZoneStartZ(index: number): number
	return ZONES_START - (index - 1) * MapLayout.ZoneSize
end

-- CFrame зоны: центр пола, -Z смотрит на вход (к аллее), +Z — на выход в следующую зону.
function MapLayout.ZoneCFrame(index: number): CFrame
	local center = Vector3.new(0, MapLayout.Heights.Path, MapLayout.ZoneStartZ(index) - MapLayout.ZoneSize / 2)
	return CFrame.lookAt(center, center + Vector3.new(0, 0, 1))
end

-- Точка перед входом в зону (снаружи, по центру проёма) — куда возвращать игрока.
function MapLayout.ZoneEntrance(index: number): Vector3
	return Vector3.new(0, MapLayout.Heights.Path, MapLayout.ZoneStartZ(index) + 4)
end

-- Куда ночью уводить всех из зон (D21): аллея перед воротами.
MapLayout.NightReturn = Vector3.new(0, MapLayout.Heights.Alley, MapLayout.Gate.z + 10)

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

-- Контур острова по часовой стрелке (вид сверху): аллея с музеями и узкий коридор зон.
-- Стена-граница идёт по контуру, холмы, песок и вода — снаружи.
local ISLAND_X = 92
local ISLAND_TOP = 150
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

-- Прямоугольники острова (для земли и пятен травы): аллея и коридор.
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

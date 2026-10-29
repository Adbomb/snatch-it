-- Раскладка карты «аллея» (D12) и зон добычи (D15) только данными. Аллея идёт вдоль оси Z:
-- начало (точка появления, спортзал) на +Z, ворота в зоны на -Z. Музеи — по 4 с каждой стороны,
-- входом на аллею. За воротами дорожка, вдоль неё 4 зоны: чем сложнее, тем дальше от ворот.
-- Ни от чего не зависит, кроме GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

local MapLayout = {}

-- Высоты верхних граней поверхностей: разные, чтобы плоскости не мерцали (у Baseplate шаблона верх на 0).
MapLayout.Heights = {
	Ground = 0.1,
	Path = 0.3, -- дорожка к зонам, полы зон
	Alley = 0.4, -- аллея, спортзал
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

-- Спортзал в начале аллеи слева, стойки смотрят на аллею (+X).
MapLayout.Gym = {
	center = Vector3.new(-44, MapLayout.Heights.Alley, 110),
	size = Vector2.new(44, 36), -- по X и по Z
	rackSpacing = 8,
}

-- Сквер напротив спортзала.
MapLayout.Garden = { center = Vector3.new(44, MapLayout.Heights.Ground, 110), size = Vector2.new(44, 36) }

-- Ворота в конце аллеи и дорожка к зонам.
MapLayout.Gate = { z = MapLayout.Alley.endZ, width = MapLayout.Alley.halfWidth * 2 }
MapLayout.Path = { halfWidth = 8, fromZ = MapLayout.Alley.endZ, toZ = -345 }

-- Зоны: центр, сторона дорожки (знак x), размер. Порядок = GameConfig.Zones (Свалка ближе всех).
MapLayout.ZoneSize = 60
local ZONE_X = 44
local zoneSpecs = {
	{ x = -ZONE_X, z = -170 },
	{ x = ZONE_X, z = -215 },
	{ x = -ZONE_X, z = -260 },
	{ x = ZONE_X, z = -305 },
}
assert(#zoneSpecs == #GameConfig.Zones, "MapLayout: число зон не совпадает с GameConfig.Zones")

-- CFrame зоны: центр пола, -Z смотрит на дорожку (там ворота зоны).
function MapLayout.ZoneCFrame(index: number): CFrame
	local spec = zoneSpecs[index]
	local center = Vector3.new(spec.x, MapLayout.Heights.Path, spec.z)
	return CFrame.lookAt(center, center + Vector3.new(-math.sign(spec.x), 0, 0))
end

-- Постаменты в локальных координатах зоны (x вдоль ворот, z от ворот вглубь, ворота на z = -Size/2).
MapLayout.Pedestals = {
	Vector2.new(-18, 2),
	Vector2.new(18, 2),
	Vector2.new(0, 10),
	Vector2.new(-12, 20),
	Vector2.new(12, 20),
}
MapLayout.PedestalHeight = 2.5
MapLayout.GuardSpot = Vector2.new(0, -12) -- место стража (шаг 3)

-- Граница карты: стены по прямоугольнику.
MapLayout.Bounds = { minX = -92, maxX = 92, minZ = -360, maxZ = 150 }

-- Точки появления предметов: верх постаментов в зонах (D15).
export type SpawnPoint = { name: string, position: Vector3, zone: number }

function MapLayout.SpawnPoints(): { SpawnPoint }
	local points: { SpawnPoint } = {}
	for zone in zoneSpecs do
		local frame = MapLayout.ZoneCFrame(zone)
		for i, spot in MapLayout.Pedestals do
			local top = frame * CFrame.new(spot.X, MapLayout.PedestalHeight, spot.Y)
			table.insert(points, { name = ("Zone%d_%d"):format(zone, i), position = top.Position, zone = zone })
		end
	end
	return points
end

return MapLayout

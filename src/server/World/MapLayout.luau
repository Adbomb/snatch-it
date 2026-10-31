-- Раскладка карты (D36, утверждённый рисунок заказчика; D22) только данными. Безопасная зона — поле травы между
-- земляными обрывами: у дальней стены (+Z) пять музеев в ряд входом к полю, у каждого спереди слева (по +X —
-- левая рука игрока, смотрящего на музеи) поле качалки с огромной гантелью и табличкой «Улучшение»; у переднего
-- края — лавки «Аура» и «Продажа» по бокам от коридора уровней. Коридор уходит в -Z: 10 зон подряд, игрок
-- проходит зону N, чтобы попасть в N+1. Ни от чего не зависит, кроме GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

local MapLayout = {}

-- Высоты верхних граней поверхностей: разные, чтобы плоскости не мерцали (у Baseplate шаблона верх на 0).
MapLayout.Heights = {
	Ground = 0.1, -- трава
	Water = -1.2, -- уровень воды вокруг острова
	Path = 0.3, -- полы зон
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
assert(#PLOT_XS == GameConfig.World.PlotCount, "MapLayout: число участков не совпадает с GameConfig.World.PlotCount")

function MapLayout.PlotCFrame(index: number): CFrame
	return CFrame.new(PLOT_XS[index], 0, PLOT_Z)
end

-- Поле качалки и табличка «Улучшение» — в координатах участка (x — от центра музея, z < -22 — перед фасадом).
MapLayout.PlotYard = {
	field = Vector2.new(20, -32),
	sign = Vector2.new(7, -30),
}

-- Лавки у переднего края, прилавком к полю; awning — пара цветов навеса из Palette.Awnings.
MapLayout.Shops = {
	{ title = "Аура", position = Vector3.new(MapLayout.CorridorHalf, 0, 12), awning = 2 },
	{ title = "Продажа", position = Vector3.new(-MapLayout.CorridorHalf, 0, 12), awning = 3 },
}
MapLayout.ShopScale = 2.6 -- ларёк Plaza.Stall в 2.6 раза больше

-- Точка появления посередине поля, лицом к музеям.
MapLayout.Spawn = { position = Vector3.new(0, MapLayout.Heights.Ground, 40), size = Vector3.new(8, 0.4, 8) }

-- Коридор зон: длина зоны, проём ворот между зонами. Вход в зону 1 — граница безопасной зоны (z = 0).
MapLayout.ZoneSize = 95
MapLayout.ZoneHalfWidth = MapLayout.CorridorHalf
MapLayout.ZoneDoor = 16 -- ширина проёма ворот зоны
MapLayout.ZoneWallHeight = 8
local ZONES_START = 0
local ZONE_COUNT = #GameConfig.Zones
MapLayout.ZonesEnd = ZONES_START - ZONE_COUNT * MapLayout.ZoneSize

-- Опасная зона (D37): коридор уровней — от входа в зону 1 (z = 0) вглубь, в ширину коридора.
function MapLayout.InDangerZone(position: Vector3): boolean
	return position.Z < ZONES_START and math.abs(position.X) <= MapLayout.CorridorHalf + 2
end

-- Мировая z входа в зону index (сторона безопасной зоны).
function MapLayout.ZoneStartZ(index: number): number
	return ZONES_START - (index - 1) * MapLayout.ZoneSize
end

-- CFrame зоны: центр пола, -Z смотрит на вход (к безопасной зоне), +Z — на выход в следующую зону.
function MapLayout.ZoneCFrame(index: number): CFrame
	local center = Vector3.new(0, MapLayout.Heights.Path, MapLayout.ZoneStartZ(index) - MapLayout.ZoneSize / 2)
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

-- Границы острова (трава и плато за обрывами) — для земли и воды вокруг.
local cliff = MapLayout.Cliff
local OUTER_X = MapLayout.SafeZone.halfX + cliff.terrace + cliff.outer
MapLayout.Island = {
	minX = -OUTER_X,
	maxX = OUTER_X,
	minZ = MapLayout.ZonesEnd - cliff.outer,
	maxZ = MapLayout.SafeZone.back + cliff.terrace + cliff.outer,
}

-- Точки предметов у боссов: верх постаментов (D37), лицом ко входу в зону.
export type ArtSlotPoint = { name: string, cframe: CFrame, zone: number, slot: number }

function MapLayout.ArtSlotPoints(): { ArtSlotPoint }
	local points: { ArtSlotPoint } = {}
	for zone = 1, ZONE_COUNT do
		local frame = MapLayout.ZoneCFrame(zone)
		for slot, spot in MapLayout.ArtSlots do
			local top = frame * CFrame.new(spot.X, MapLayout.PedestalHeight, spot.Y)
			local name = ("Boss%d_Slot%d"):format(zone, slot)
			table.insert(points, { name = name, cframe = top, zone = zone, slot = slot })
		end
	end
	return points
end

return MapLayout

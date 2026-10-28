-- Раскладка карты «город» (D12) только данными: участки, дорога, площадь, улицы, кварталы, парк, граница,
-- точки появления. Север — сторона -Z. Карта 400×400, центр в (0, 0, 0).
-- Кварталы задаются в локальных координатах (u — от центра по X, v — от центра по Z) и зеркалятся
-- по четвертям. Ни от чего не зависит, кроме GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

local MapLayout = {}

MapLayout.Half = 200 -- граница карты: стены на ±Half

-- Высоты верхних граней поверхностей. Разные, чтобы плоскости не мерцали друг на друге
-- (у Baseplate шаблона верх на 0).
MapLayout.Heights = {
	Ground = 0.1,
	Quarter = 0.2,
	Road = 0.3,
	Plaza = 0.4,
	Floor = 0.4, -- пол музеев (PartBuilder.FloorTop)
}

-- Кольцевая дорога: квадрат, осевая линия на ±RoadCenter.
MapLayout.Road = { center = 136, width = 24, curbHeight = 0.5, curbWidth = 1 }
MapLayout.CityHalf = MapLayout.Road.center - MapLayout.Road.width / 2 -- внутренний край дороги (124)

MapLayout.PlazaSize = 60
MapLayout.StreetWidth = 16 -- 4 улицы от площади к дороге по осям

-- 8 участков: по 2 на сторону, вход (сторона -Z участка) смотрит в город. Порядок — М1…М8 по часовой с севера.
local PLOT_DISTANCE = 172
local PLOT_OFFSET = 60
local plotSpecs = {
	{ Vector3.new(-PLOT_OFFSET, 0, -PLOT_DISTANCE), Vector3.new(0, 0, 1) }, -- М1 север
	{ Vector3.new(PLOT_OFFSET, 0, -PLOT_DISTANCE), Vector3.new(0, 0, 1) }, -- М2 север
	{ Vector3.new(PLOT_DISTANCE, 0, -PLOT_OFFSET), Vector3.new(-1, 0, 0) }, -- М3 восток
	{ Vector3.new(PLOT_DISTANCE, 0, PLOT_OFFSET), Vector3.new(-1, 0, 0) }, -- М4 восток
	{ Vector3.new(PLOT_OFFSET, 0, PLOT_DISTANCE), Vector3.new(0, 0, -1) }, -- М5 юг
	{ Vector3.new(-PLOT_OFFSET, 0, PLOT_DISTANCE), Vector3.new(0, 0, -1) }, -- М6 юг
	{ Vector3.new(-PLOT_DISTANCE, 0, PLOT_OFFSET), Vector3.new(1, 0, 0) }, -- М7 запад
	{ Vector3.new(-PLOT_DISTANCE, 0, -PLOT_OFFSET), Vector3.new(1, 0, 0) }, -- М8 запад
}
assert(#plotSpecs == GameConfig.World.PlotCount, "MapLayout: число участков не совпадает с GameConfig.World.PlotCount")

-- CFrame участка: позиция центра, -Z смотрит в город.
function MapLayout.PlotCFrame(index: number): CFrame
	local spec = plotSpecs[index]
	return CFrame.lookAt(spec[1], spec[1] + spec[2])
end

-- Точка на осевой дороги напротив входа участка.
local function roadInFront(index: number): Vector3
	local spec = plotSpecs[index]
	local toRoad = PLOT_DISTANCE - MapLayout.Road.center
	return spec[1] + spec[2] * toRoad
end

-- Четверти города: знаки (sx, sz) переводят локальные (u, v) в мир: x = sx·u, z = sz·v.
export type House = {
	u: number,
	v: number,
	w: number, -- ширина (вдоль фасада)
	d: number, -- глубина
	h: number, -- высота стен
	facing: string, -- "street" (дверь к улице вдоль u) или "side" (дверь к улице вдоль v)
	access: string, -- "ladder" | "crates" | "fire"
	wall: number, -- индекс в Palette.HouseWalls
	roof: number, -- индекс в Palette.HouseRoofs
}

export type Quarter = {
	name: string,
	sx: number,
	sz: number,
	houses: { House },
	bridge: { number }?, -- индексы двух домов одной высоты, соединённых доской по крышам
}

-- Шаблон квартала: H1 и H2 разделены переулком 10 стадов с тупиком, H3 — высокий, за переулком 10 стадов.
local function quarter(name: string, sx: number, sz: number, heights: { number }, walls: { number }): Quarter
	return {
		name = name,
		sx = sx,
		sz = sz,
		houses = {
			{ u = 50, v = 50, w = 24, d = 20, h = heights[1], facing = "side", access = "ladder", wall = walls[1], roof = walls[2] },
			{ u = 84, v = 50, w = 24, d = 20, h = heights[1], facing = "side", access = "crates", wall = walls[2], roof = walls[3] },
			{ u = 50, v = 82, w = 24, d = 24, h = heights[2], facing = "street", access = "fire", wall = walls[3], roof = walls[1] },
		},
		bridge = { 1, 2 },
	}
end

MapLayout.Quarters = {
	quarter("А", -1, -1, { 16, 22 }, { 1, 3, 2 }),
	quarter("В", -1, 1, { 12, 20 }, { 4, 2, 1 }),
	quarter("Г", 1, 1, { 18, 24 }, { 2, 4, 3 }),
}

-- Тупик: стена поперёк переулка между H1 и H2, открыт к улице (меньшие v).
MapLayout.DeadEnd = { u = 67, v = 60.5, width = 10, height = 8, spawnV = 56 }

-- Парк-лес в северо-восточной четверти (sx = 1, sz = -1).
MapLayout.Park = {
	sx = 1,
	sz = -1,
	pond = { u = 44, v = 78, radius = 12 },
	hill = { u = 92, v = 92, tiers = { 34, 26, 18 }, tierHeight = 4 },
	treeCount = 30,
	bushCount = 18,
	treeSeed = 7,
	forestDepth = { u = 108, v = 36 }, -- Far-точка в глубине леса
	paths = {
		{ from = Vector2.new(30, 30), to = Vector2.new(44, 62), width = 6 },
		{ from = Vector2.new(56, 78), to = Vector2.new(78, 90), width = 6 },
	},
}

-- Мир из локальных (u, v) четверти.
function MapLayout.ToWorld(sx: number, sz: number, u: number, v: number, y: number): Vector3
	return Vector3.new(sx * u, y, sz * v)
end

-- Верх крыши дома (крыша — плита ROOF_THICKNESS над стенами).
MapLayout.RoofThickness = 1.2
function MapLayout.RoofTop(house: House): number
	return MapLayout.Heights.Quarter + house.h + MapLayout.RoofThickness
end

-- 16 точек появления (D11/D12): Near — на дороге у входов, Center — площадь и улица,
-- Far — крыши, тупики, глубина леса, беседка на холме.
export type SpawnPoint = { name: string, position: Vector3, tier: string }

function MapLayout.SpawnPoints(): { SpawnPoint }
	local points: { SpawnPoint } = {}
	local function add(name: string, position: Vector3, tier: string)
		table.insert(points, { name = name, position = position, tier = tier })
	end
	local h = MapLayout.Heights

	for _, index in { 1, 3, 5, 7 } do
		local p = roadInFront(index)
		add("Near_M" .. index, Vector3.new(p.X, h.Road, p.Z), "Near")
	end

	add("Center_PlazaE", Vector3.new(16, h.Plaza, 0), "Center")
	add("Center_PlazaW", Vector3.new(-16, h.Plaza, 0), "Center")
	add("Center_PlazaN", Vector3.new(0, h.Plaza, -16), "Center")
	add("Center_PlazaS", Vector3.new(0, h.Plaza, 16), "Center")
	add("Center_StreetS", Vector3.new(0, h.Road, 80), "Center")

	for _, q in MapLayout.Quarters do
		local tall = q.houses[3]
		add("Far_Roof" .. q.name, MapLayout.ToWorld(q.sx, q.sz, tall.u, tall.v, MapLayout.RoofTop(tall)), "Far")
	end
	local dead = MapLayout.DeadEnd
	for _, index in { 1, 3 } do
		local q = MapLayout.Quarters[index]
		add("Far_DeadEnd" .. q.name, MapLayout.ToWorld(q.sx, q.sz, dead.u, dead.spawnV, h.Quarter), "Far")
	end
	local park = MapLayout.Park
	add(
		"Far_Forest",
		MapLayout.ToWorld(park.sx, park.sz, park.forestDepth.u, park.forestDepth.v, h.Ground),
		"Far"
	)
	add(
		"Far_Gazebo",
		MapLayout.ToWorld(park.sx, park.sz, park.hill.u, park.hill.v, MapLayout.GazeboFloor()),
		"Far"
	)
	return points
end

-- Верх пола беседки на вершине холма.
MapLayout.GazeboFloorHeight = 1
function MapLayout.GazeboFloor(): number
	local hill = MapLayout.Park.hill
	return MapLayout.Heights.Ground + #hill.tiers * hill.tierHeight + MapLayout.GazeboFloorHeight
end

return MapLayout

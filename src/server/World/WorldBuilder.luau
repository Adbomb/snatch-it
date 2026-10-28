-- Строит карту «город» (D12) по MapLayout: землю, кольцевую дорогу, улицы, площадь, три квартала,
-- парк-лес, стены и холмы по краю. Только геометрия, без логики; участки-музеи строит PlotService.
-- Зависит от MapLayout, ModelBuilder, Palette, World/Models/*.

local ServerScriptService = game:GetService("ServerScriptService")

local World = ServerScriptService.Server.World
local MapLayout = require(World.MapLayout)
local ModelBuilder = require(World.ModelBuilder)
local Palette = require(World.Palette)
local House = require(World.Models.House)
local Park = require(World.Models.Park)
local Plaza = require(World.Models.Plaza)
local Props = require(World.Models.Props)
local Tree = require(World.Models.Tree)

local B = ModelBuilder.Brick
local H = MapLayout.Heights
local SLAB = 0.4 -- толщина плит покрытия

local WorldBuilder = {}

local function folder(name: string, parent: Instance): Folder
	local f = Instance.new("Folder")
	f.Name = name
	f.Parent = parent
	return f
end

-- Плита покрытия с верхом на высоте top.
local function slab(name: string, size: Vector2, center: Vector3, top: number, color: Color3, parent: Instance)
	local brick = B(Vector3.new(size.X, SLAB, size.Y), Vector3.new(center.X, top - SLAB / 2, center.Z), color)
	ModelBuilder.Build(name, { brick }).Parent = parent
end

local function place(key: string, build: () -> { ModelBuilder.Brick }, at: CFrame, parent: Instance, opts: ModelBuilder.Options?)
	local model = ModelBuilder.FromTemplate(key, function()
		return ModelBuilder.Build(key, build(), opts)
	end)
	ModelBuilder.Place(model, at, parent)
end

local function buildGround(parent: Instance)
	-- Одна большая плита травы закрывает Baseplate и уходит к горизонту.
	local size = 2048
	ModelBuilder.Build("Ground", {
		B(Vector3.new(size, 2, size), Vector3.new(0, H.Ground - 1, 0), Palette.Grass),
	}).Parent = parent
end

local function buildRoad(parent: Instance)
	local road = MapLayout.Road
	local f = folder("Road", parent)
	local outer = road.center + road.width / 2
	local inner = road.center - road.width / 2
	local street = MapLayout.StreetWidth / 2
	local bricks: { ModelBuilder.Brick } = {}
	local curbTop = H.Road + road.curbHeight

	for _, sign in { -1, 1 } do
		-- Север/юг на всю длину, запад/восток между ними.
		table.insert(bricks, B(Vector3.new(outer * 2, SLAB, road.width), Vector3.new(0, H.Road - SLAB / 2, sign * road.center), Palette.Asphalt))
		table.insert(bricks, B(Vector3.new(road.width, SLAB, inner * 2), Vector3.new(sign * road.center, H.Road - SLAB / 2, 0), Palette.Asphalt))
		-- Внешние бордюры.
		table.insert(
			bricks,
			B(Vector3.new(outer * 2, curbTop, road.curbWidth), Vector3.new(0, curbTop / 2, sign * (outer - road.curbWidth / 2)), Palette.Curb)
		)
		table.insert(
			bricks,
			B(Vector3.new(road.curbWidth, curbTop, outer * 2), Vector3.new(sign * (outer - road.curbWidth / 2), curbTop / 2, 0), Palette.Curb)
		)
		-- Внутренние бордюры с разрывом под улицу.
		local pieceLength = inner - street
		local pieceCenter = (inner + street) / 2
		for _, half in { -1, 1 } do
			table.insert(
				bricks,
				B(
					Vector3.new(pieceLength, curbTop, road.curbWidth),
					Vector3.new(half * pieceCenter, curbTop / 2, sign * (inner + road.curbWidth / 2)),
					Palette.Curb
				)
			)
			table.insert(
				bricks,
				B(
					Vector3.new(road.curbWidth, curbTop, pieceLength),
					Vector3.new(sign * (inner + road.curbWidth / 2), curbTop / 2, half * pieceCenter),
					Palette.Curb
				)
			)
		end
	end
	ModelBuilder.Build("RoadSurface", bricks).Parent = f

	-- Белая прерывистая разметка по осевой, без перекрёстков.
	local dashes: { ModelBuilder.Brick } = {}
	local dashLength, step, skip = 4, 10, 14
	local markTop = H.Road + 0.05
	local t = -road.center + step / 2
	while t < road.center do
		if math.abs(t) > skip then
			for _, sign in { -1, 1 } do
				table.insert(dashes, B(Vector3.new(dashLength, 0.1, 0.6), Vector3.new(t, markTop, sign * road.center), Palette.Marking, { collide = false, shadow = false }))
				table.insert(dashes, B(Vector3.new(0.6, 0.1, dashLength), Vector3.new(sign * road.center, markTop, t), Palette.Marking, { collide = false, shadow = false }))
			end
		end
		t += step
	end
	ModelBuilder.Build("Markings", dashes).Parent = f
end

local function buildStreets(parent: Instance)
	local f = folder("Streets", parent)
	local half = MapLayout.PlazaSize / 2
	local length = MapLayout.CityHalf - half
	local mid = (MapLayout.CityHalf + half) / 2
	local w = MapLayout.StreetWidth
	for _, dir in { Vector3.new(0, 0, -1), Vector3.new(0, 0, 1), Vector3.new(-1, 0, 0), Vector3.new(1, 0, 0) } do
		local size = if dir.X == 0 then Vector2.new(w, length) else Vector2.new(length, w)
		slab("Street", size, dir * mid, H.Road, Palette.Street, f)
	end
end

local function buildPlaza(parent: Instance)
	local f = folder("Plaza", parent)
	local size = MapLayout.PlazaSize
	slab("PlazaFloor", Vector2.new(size, size), Vector3.zero, H.Plaza, Palette.Plaza, f)
	-- Узор: рамка из акцентной плитки.
	local ring: { ModelBuilder.Brick } = {}
	local inset, band = 6, 2
	local r = size / 2 - inset
	for _, sign in { -1, 1 } do
		table.insert(ring, B(Vector3.new(r * 2, 0.1, band), Vector3.new(0, H.Plaza + 0.05, sign * r), Palette.PlazaAccent, { collide = false, shadow = false }))
		table.insert(ring, B(Vector3.new(band, 0.1, r * 2), Vector3.new(sign * r, H.Plaza + 0.05, 0), Palette.PlazaAccent, { collide = false, shadow = false }))
	end
	ModelBuilder.Build("PlazaPattern", ring).Parent = f

	local floor = H.Plaza
	place("Fountain", Plaza.Fountain, CFrame.new(0, floor, 0), f)
	for i, corner in { Vector3.new(-1, 0, -1), Vector3.new(1, 0, -1), Vector3.new(1, 0, 1), Vector3.new(-1, 0, 1) } do
		local stripes = Palette.Awnings[i]
		local position = corner * 22 + Vector3.new(0, floor, 0)
		place("Stall_" .. i, function()
			return Plaza.Stall(stripes[1], stripes[2])
		end, CFrame.lookAt(position, Vector3.new(0, floor, 0)), f)
		-- Лавочка между фонтаном и ларьком, смотрит на фонтан.
		local benchPosition = corner * 12 + Vector3.new(0, floor, 0)
		place("Bench", Props.Bench, CFrame.lookAt(benchPosition, Vector3.new(0, floor, 0)), f)
	end
	-- Фонари по краям площади у въездов улиц.
	for _, spot in { Vector2.new(28, 10), Vector2.new(28, -10), Vector2.new(-28, 10), Vector2.new(-28, -10) } do
		place("Lamp", Props.Lamp, CFrame.new(spot.X, floor, spot.Y), f)
		place("Lamp", Props.Lamp, CFrame.new(spot.Y, floor, spot.X), f)
	end
end

local function houseCFrame(q: MapLayout.Quarter, house: MapLayout.House): CFrame
	local position = MapLayout.ToWorld(q.sx, q.sz, house.u, house.v, H.Quarter)
	-- Дверь (сторона -Z модели) смотрит к ближней улице.
	local facing = if house.facing == "side" then Vector3.new(0, 0, -q.sz) else Vector3.new(-q.sx, 0, 0)
	return CFrame.lookAt(position, position + facing)
end

local function buildQuarter(q: MapLayout.Quarter, parent: Instance)
	local f = folder("Quarter_" .. q.name, parent)
	local near = MapLayout.StreetWidth / 2
	local far = MapLayout.CityHalf
	local center = (near + far) / 2
	slab("Pavement", Vector2.new(far - near, far - near), MapLayout.ToWorld(q.sx, q.sz, center, center, 0), H.Quarter, Palette.Pavement, f)

	for index, house in q.houses do
		local params = {
			w = house.w,
			d = house.d,
			h = house.h,
			wall = Palette.HouseWalls[house.wall],
			roof = Palette.HouseRoofs[house.roof],
			access = house.access,
			roofThickness = MapLayout.RoofThickness,
		}
		ModelBuilder.Place(ModelBuilder.Build("House_" .. index, House(params)), houseCFrame(q, house), f)
	end

	-- Доска-мостик между крышами двух домов одной высоты.
	if q.bridge then
		local a, b = q.houses[q.bridge[1]], q.houses[q.bridge[2]]
		local gapStart = a.u + a.w / 2
		local gapEnd = b.u - b.w / 2
		local length = gapEnd - gapStart + 2
		local position = MapLayout.ToWorld(q.sx, q.sz, (gapStart + gapEnd) / 2, a.v, MapLayout.RoofTop(a) + 0.3)
		ModelBuilder.Build("RoofPlank", {
			B(Vector3.new(length, 0.6, 3), position, Palette.Wood),
		}).Parent = f
	end

	-- Тупик: кирпичная стена поперёк переулка.
	local dead = MapLayout.DeadEnd
	local wallBricks: { ModelBuilder.Brick } = {}
	local rows = 4
	for row = 1, rows do
		local y = H.Quarter + (row - 0.5) * dead.height / rows
		local color = if row % 2 == 0 then Palette.HouseWalls[1] else Palette.HouseWalls[1]:Lerp(Palette.Black, 0.2)
		table.insert(wallBricks, B(Vector3.new(dead.width, dead.height / rows, 1), MapLayout.ToWorld(q.sx, q.sz, dead.u, dead.v, y), color))
	end
	ModelBuilder.Build("DeadEndWall", wallBricks).Parent = f

	-- Двор: ящики и кусты.
	for i, spot in { Vector2.new(80, 80), Vector2.new(85, 80), Vector2.new(80, 85) } do
		place("Crate", Props.Crate, CFrame.new(MapLayout.ToWorld(q.sx, q.sz, spot.X, spot.Y, H.Quarter)) * CFrame.Angles(0, i * 0.3, 0), f)
	end
	for i, spot in { Vector2.new(30, 100), Vector2.new(104, 30), Vector2.new(104, 104) } do
		place("Bush_" .. i, function()
			return Props.Bush(i)
		end, CFrame.new(MapLayout.ToWorld(q.sx, q.sz, spot.X, spot.Y, H.Quarter)), f)
	end
end

-- Расстояние от точки до отрезка (для дорожек парка).
local function distanceToSegment(p: Vector2, a: Vector2, b: Vector2): number
	local ab = b - a
	local t = math.clamp((p - a):Dot(ab) / ab:Dot(ab), 0, 1)
	return (p - (a + ab * t)).Magnitude
end

local function buildPark(parent: Instance)
	local park = MapLayout.Park
	local f = folder("Park", parent)
	local function world(u: number, v: number, y: number): Vector3
		return MapLayout.ToWorld(park.sx, park.sz, u, v, y)
	end

	-- Дорожки.
	for i, path in park.paths do
		local a, b = path.from, path.to
		local mid = (a + b) / 2
		local length = (b - a).Magnitude
		local from, to = world(a.X, a.Y, 0), world(b.X, b.Y, 0)
		local cframe = CFrame.lookAt(world(mid.X, mid.Y, H.Quarter - SLAB / 2), world(mid.X, mid.Y, H.Quarter - SLAB / 2) + (to - from))
		ModelBuilder.Build("Path_" .. i, {
			B(Vector3.new(path.width, SLAB, length + path.width), cframe, Palette.PlazaAccent),
		}).Parent = f
	end

	-- Пруд: каменный край и вода, мостик поперёк.
	local pond = park.pond
	local upright = CFrame.Angles(0, 0, math.rad(90)) -- ось цилиндра вертикально
	ModelBuilder.Build("Pond", {
		B(Vector3.new(0.5, (pond.radius + 1.5) * 2, (pond.radius + 1.5) * 2), CFrame.new(world(pond.u, pond.v, H.Ground + 0.1)) * upright, Palette.Stone, {
			shape = "Cylinder",
			shadow = false,
		}),
		B(Vector3.new(0.5, pond.radius * 2, pond.radius * 2), CFrame.new(world(pond.u, pond.v, H.Ground + 0.15)) * upright, Palette.Water, {
			shape = "Cylinder",
			material = Enum.Material.Glass,
			transparency = 0.2,
			shadow = false,
		}),
	}).Parent = f
	local bridgeLength = pond.radius * 2 + 2
	local bridgeAt = CFrame.lookAt(world(pond.u, pond.v, H.Ground), world(pond.u + 1, pond.v, H.Ground))
	ModelBuilder.Place(ModelBuilder.Build("PondBridge", Park.Bridge(bridgeLength)), bridgeAt, f)

	-- Холм ступенями (каждая ступень берётся прыжком) и беседка на вершине.
	local hill = park.hill
	local hillBricks: { ModelBuilder.Brick } = {}
	for tier, size in hill.tiers do
		local top = H.Ground + tier * hill.tierHeight
		local color = if tier % 2 == 0 then Palette.Hill else Palette.GrassDark
		table.insert(hillBricks, B(Vector3.new(size, hill.tierHeight, size), world(hill.u, hill.v, top - hill.tierHeight / 2), color))
	end
	ModelBuilder.Build("Hill", hillBricks).Parent = f
	local hillTop = H.Ground + #hill.tiers * hill.tierHeight
	local gazeboAt = CFrame.lookAt(world(hill.u, hill.v, hillTop), world(hill.u - 1, hill.v - 1, hillTop))
	ModelBuilder.Place(ModelBuilder.Build("Gazebo", Park.Gazebo(MapLayout.GazeboFloorHeight, Palette.HouseWalls[1])), gazeboAt, f)

	-- Деревья и кусты в свободных местах (детерминированно: одинаково при каждом запуске).
	local random = Random.new(park.treeSeed)
	local taken: { { pos: Vector2, radius: number } } = {}
	local function free(p: Vector2, radius: number): boolean
		if p.X < 36 and p.Y < 36 then
			return false -- угол у площади
		end
		if (p - Vector2.new(pond.u, pond.v)).Magnitude < pond.radius + radius + 3 then
			return false
		end
		local hillHalf = hill.tiers[1] / 2 + radius + 2
		if math.abs(p.X - hill.u) < hillHalf and math.abs(p.Y - hill.v) < hillHalf then
			return false
		end
		for _, path in park.paths do
			if distanceToSegment(p, path.from, path.to) < path.width / 2 + radius + 1 then
				return false
			end
		end
		if (p - Vector2.new(park.forestDepth.u, park.forestDepth.v)).Magnitude < radius + 4 then
			return false
		end
		for _, other in taken do
			if (p - other.pos).Magnitude < radius + other.radius then
				return false
			end
		end
		return true
	end
	local function scatter(count: number, radius: number, spawnOne: (Vector2, number) -> ())
		local placed, attempts = 0, 0
		local edge = MapLayout.CityHalf - 4
		while placed < count and attempts < count * 60 do
			attempts += 1
			local p = Vector2.new(random:NextNumber(12, edge), random:NextNumber(12, edge))
			if free(p, radius) then
				placed += 1
				table.insert(taken, { pos = p, radius = radius })
				spawnOne(p, placed)
			end
		end
	end
	local sizes = { "S", "M", "M", "L", "L" }
	scatter(park.treeCount, 5, function(p, i)
		local size = sizes[random:NextInteger(1, #sizes)]
		local color = random:NextInteger(1, #Palette.Leaves)
		place(("Tree_%s_%d"):format(size, color), function()
			return Tree(size, color)
		end, CFrame.new(world(p.X, p.Y, H.Ground)) * CFrame.Angles(0, random:NextNumber(0, math.pi), 0), f)
	end)
	scatter(park.bushCount, 2.5, function(p, i)
		local variant = i % 3 + 1
		place("Bush_" .. variant, function()
			return Props.Bush(variant)
		end, CFrame.new(world(p.X, p.Y, H.Ground)), f)
	end)
end

local function buildBorder(parent: Instance)
	local f = folder("Border", parent)
	local half = MapLayout.Half
	local thickness, bandHeight = 4, 6
	local bricks: { ModelBuilder.Brick } = {}
	for band, color in Palette.BorderWall do
		local y = H.Ground + (band - 0.5) * bandHeight
		for _, sign in { -1, 1 } do
			table.insert(bricks, B(Vector3.new(half * 2 + thickness * 2, bandHeight, thickness), Vector3.new(0, y, sign * (half + thickness / 2)), color))
			table.insert(bricks, B(Vector3.new(thickness, bandHeight, half * 2), Vector3.new(sign * (half + thickness / 2), y, 0), color))
		end
	end
	ModelBuilder.Build("BorderWall", bricks).Parent = f

	-- Холмы за стеной, чтобы не было видно края мира.
	local hills: { ModelBuilder.Brick } = {}
	local random = Random.new(3)
	for side = 0, 3 do
		local rotation = CFrame.Angles(0, side * math.pi / 2, 0)
		for t = -180, 180, 72 do
			local height = random:NextNumber(16, 30)
			local width = random:NextNumber(60, 90)
			local base = rotation * CFrame.new(t, H.Ground + height / 2, -(half + 30))
			table.insert(hills, B(Vector3.new(width, height, 44), base, Palette.GrassDark, { shadow = false }))
			table.insert(
				hills,
				B(Vector3.new(width * 0.6, height * 0.5, 28), base * CFrame.new(0, height * 0.75, 4), Palette.Hill, { shadow = false })
			)
		end
	end
	ModelBuilder.Build("BorderHills", hills).Parent = f
end

function WorldBuilder.Build(parent: Instance)
	local city = folder("City", parent)
	buildGround(city)
	buildRoad(city)
	buildStreets(city)
	buildPlaza(city)
	for _, q in MapLayout.Quarters do
		buildQuarter(q, city)
	end
	buildPark(city)
	buildBorder(city)
end

return WorldBuilder

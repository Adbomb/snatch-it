-- Строит карту (D36, D22) по MapLayout: остров травы, земляные обрывы с травой поверху вокруг безопасной зоны
-- (сзади и по бокам — уступом с травяной террасой) и коридора уровней, деревья на террасах и плато, лавки
-- «Аура» и «Продажа», точку появления и 10 зон коридором — пол, стена с воротами и вывеской, постаменты, декор.
-- Воду вокруг острова строит BuildWater (Terrain; только в Play). Участки-музеи с полем качалки строит PlotService.
-- Совпадающих граней у разных деталей нет (D36): трава обрывов, свесы и «натёки» лежат встык или с выступом.
-- Зависит от MapLayout, ModelBuilder, Palette, Signs, Studs, World/Models/*, GameConfig, NumberFormat.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local NumberFormat = require(ReplicatedStorage.Shared.NumberFormat)
local World = ServerScriptService.Server.World
local MapLayout = require(World.MapLayout)
local ModelBuilder = require(World.ModelBuilder)
local Palette = require(World.Palette)
local Signs = require(World.Signs)
local Studs = require(World.Studs)
local Gate = require(World.Models.Gate)
local Plaza = require(World.Models.Plaza)
local Props = require(World.Models.Props)
local Tree = require(World.Models.Tree)
local ZoneDecor = require(World.Models.ZoneDecor)
local ZoneWall = require(World.Models.ZoneWall)

local B = ModelBuilder.Brick
local H = MapLayout.Heights
local SLAB = 0.4 -- толщина плит покрытия
local GROUND = 2 -- толщина плиты травы
local BICEPS = "💪"
local DEEP = "LegoSquaresDeep" -- рельеф обрывов
local DRIP_SEED = 7

local WorldBuilder = {}

local function folder(name: string, parent: Instance): Folder
	local f = Instance.new("Folder")
	f.Name = name
	f.Parent = parent
	return f
end

-- Плита покрытия с верхом на высоте top.
local function slab(name: string, size: Vector2, center: Vector3, top: number, color: Color3, parent: Instance): Model
	local model = ModelBuilder.Build(name, {
		B(Vector3.new(size.X, SLAB, size.Y), Vector3.new(center.X, top - SLAB / 2, center.Z), color),
	})
	model.Parent = parent
	return model
end

local function place(key: string, build: () -> { ModelBuilder.Brick }, at: CFrame, parent: Instance): Model
	local model = ModelBuilder.FromTemplate(key, function()
		return ModelBuilder.Build(key, build())
	end)
	return ModelBuilder.Place(model, at, parent)
end

-- Брусок по границам (x0 < x1, z0 < z1).
local function box(
	x0: number,
	x1: number,
	y0: number,
	y1: number,
	z0: number,
	z1: number,
	color: Color3,
	extra: { [string]: any }?
)
	local size = Vector3.new(x1 - x0, y1 - y0, z1 - z0)
	return B(size, Vector3.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), color, extra)
end

local function buildGround(parent: Instance)
	local island = MapLayout.Island
	ModelBuilder.Build("Ground", {
		-- Шире обрывов на 2: боковые грани земли и обрывов не совпадают (D36).
		box(
			island.minX - 2,
			island.maxX + 2,
			H.Ground - GROUND,
			H.Ground,
			island.minZ - 2,
			island.maxZ + 2,
			Palette.Field
		),
	}).Parent = parent
end

-- «Натёки» травы на грани обрыва: бруски разной длины свисают с травы. Грань — along ("x" или "z") от a до b
-- на fixed, inward — куда смотрит грань (±1 по другой оси), top — верх земли, maxLen — длиннейший натёк.
-- Натёк выступает из грани на 1.4 (дальше свеса травы на 1), верх уходит в траву.
local function drips(
	bricks: { ModelBuilder.Brick },
	random: Random,
	along: string,
	a: number,
	b: number,
	fixed: number,
	inward: number,
	top: number,
	maxLen: number
)
	local t = a + 2 -- от края грани отступ: натёк не совпадает гранью со свесом соседней грани
	while t < b - 2 do
		local w = math.min(random:NextInteger(3, 7), b - 2 - t)
		local len = random:NextInteger(1, maxLen)
		local c = fixed + inward * 0.4
		local center = t + w / 2
		local y = top - len / 2 + 0.5
		if along == "x" then
			table.insert(bricks, B(Vector3.new(w, len + 1, 2), Vector3.new(center, y, c), Palette.CliffGrass))
		else
			table.insert(bricks, B(Vector3.new(2, len + 1, w), Vector3.new(c, y, center), Palette.CliffGrass))
		end
		t += w + random:NextInteger(1, 4)
	end
end

-- Обрывы вокруг безопасной зоны и коридора. Земляные блоки не перекрываются; трава поверху — по их следу,
-- свесы травы (lip) — отдельными полосами вдоль открытых граней, обрезанными так, чтобы не накладываться.
local function buildCliffs(parent: Instance)
	local f = folder("Cliffs", parent)
	local c = MapLayout.Cliff
	local SX, SZ, CX = MapLayout.SafeZone.halfX, MapLayout.SafeZone.back, MapLayout.CorridorHalf
	local D, HI, LO, L = c.terrace, c.height, c.low, c.lip
	local ZE = MapLayout.ZonesEnd
	local OX = SX + D + c.outer
	local deep = { variant = DEEP }
	local dirt, grass = Palette.CliffDirt, Palette.CliffGrass
	local bricks: { ModelBuilder.Brick } = {}
	local function block(x0, x1, z0, z1, top, grassH)
		table.insert(bricks, box(x0, x1, 0, top, z0, z1, dirt, deep))
		table.insert(bricks, box(x0, x1, top, top + grassH, z0, z1, grass))
	end
	-- Нижние террасы: сзади и по бокам безопасной зоны.
	block(-SX, SX, SZ, SZ + D, LO, c.lowGrass)
	-- Верхний обрыв сзади.
	block(-(SX + D), SX + D, SZ + D, SZ + D + c.outer, HI, c.grass)
	-- Конец коридора.
	block(-CX, CX, ZE - c.outer, ZE, HI, c.grass)
	for _, s in { -1, 1 } do
		local function X(a: number, b: number): (number, number)
			return math.min(s * a, s * b), math.max(s * a, s * b)
		end
		local x0, x1 = X(SX, SX + D)
		block(x0, x1, 0, SZ + D, LO, c.lowGrass)
		x0, x1 = X(SX + D, OX)
		block(x0, x1, 0, SZ + D + c.outer, HI, c.grass)
		-- Передний обрыв: от коридора до края острова, вдоль всего коридора.
		x0, x1 = X(CX, OX)
		block(x0, x1, ZE - c.outer, 0, HI, c.grass)

		-- Свесы травы: боковая терраса, боковой верхний обрыв, передний обрыв со стороны поля, стенка коридора.
		x0, x1 = X(SX - L, SX)
		table.insert(bricks, box(x0, x1, LO, LO + c.lowGrass, 0, SZ - L, grass))
		x0, x1 = X(SX + D - L, SX + D)
		table.insert(bricks, box(x0, x1, HI, HI + c.grass, L, SZ + D - L, grass))
		x0, x1 = X(CX, SX + D)
		table.insert(bricks, box(x0, x1, HI, HI + c.grass, 0, L, grass))
		x0, x1 = X(CX - L, CX)
		table.insert(bricks, box(x0, x1, HI, HI + c.grass, ZE + L, 0, grass))
	end
	table.insert(bricks, box(-SX, SX, LO, LO + c.lowGrass, SZ - L, SZ, grass))
	table.insert(bricks, box(-(SX + D), SX + D, HI, HI + c.grass, SZ + D - L, SZ + D, grass))
	table.insert(bricks, box(-(CX - L), CX - L, HI, HI + c.grass, ZE, ZE + L, grass))

	-- Натёки травы на открытых гранях.
	local random = Random.new(DRIP_SEED)
	drips(bricks, random, "x", -SX, SX, SZ, -1, LO, 4)
	drips(bricks, random, "x", -(SX + D), SX + D, SZ + D, -1, HI, 6)
	drips(bricks, random, "x", -CX, CX, ZE, 1, HI, 8)
	for _, s in { -1, 1 } do
		drips(bricks, random, "z", 0, SZ, s * SX, -s, LO, 4)
		drips(bricks, random, "z", 0, SZ + D, s * (SX + D), -s, HI, 6)
		local a, b = math.min(s * CX, s * (SX + D)), math.max(s * CX, s * (SX + D))
		drips(bricks, random, "x", a, b, 0, 1, HI, 8)
		drips(bricks, random, "z", ZE, 0, s * CX, -s, HI, 8)
	end
	ModelBuilder.Build("Cliffs", bricks).Parent = f

	-- Деревья: на задней террасе — в просветах между музеями и по углам, на боковых террасах, на плато у края.
	local trees: { { pos: Vector3, size: string } } = {}
	local terrace = LO + c.lowGrass
	for _, x in { -165, -112, -37, 37, 112, 165 } do
		table.insert(trees, { pos = Vector3.new(x, terrace, SZ + D / 2), size = "M" })
	end
	for _, s in { -1, 1 } do
		for _, z in { 25, 70, 112 } do
			table.insert(trees, { pos = Vector3.new(s * (SX + D / 2), terrace, z), size = "M" })
		end
		for _, z in { 10, 60, 120, 160 } do
			table.insert(trees, { pos = Vector3.new(s * (SX + D + 9), HI + c.grass, z), size = "L" })
		end
	end
	for _, x in { -150, -75, 0, 75, 150 } do
		table.insert(trees, { pos = Vector3.new(x + 20, HI + c.grass, SZ + D + 10), size = "L" })
	end
	for i, tree in trees do
		local color = i % #Palette.Leaves + 1
		place(("Tree_%s_%d"):format(tree.size, color), function()
			return Tree(tree.size, color)
		end, CFrame.new(tree.pos) * CFrame.Angles(0, i, 0), f)
	end
end

-- Лавки «Аура» и «Продажа»: ларёк в ShopScale раз больше, прилавком к полю (+Z), табло над навесом.
-- Табло в координатах ларька до увеличения.
local SHOP_BOARD = { size = Vector3.new(9, 2, 0.3), at = Vector3.new(0, 9.6, 2.7) }

local function buildShops(parent: Instance)
	local f = folder("Shops", parent)
	local k = MapLayout.ShopScale
	for _, shop in MapLayout.Shops do
		local stripes = Palette.Awnings[shop.awning]
		local stall = ModelBuilder.Build(shop.title, Plaza.Stall(Palette.Muted(stripes[1]), stripes[2]))
		stall:ScaleTo(k)
		local base = shop.position + Vector3.new(0, H.Ground, 0)
		local at = CFrame.lookAt(base, base + Vector3.new(0, 0, 1))
		ModelBuilder.Place(stall, at, f)
		local board = Instance.new("Part")
		board.Name = "SignBoard"
		board.Anchored = true
		board.Size = SHOP_BOARD.size * k
		board.CFrame = at * CFrame.new(SHOP_BOARD.at * k)
		board.Color = Palette.SignBoard
		board.Material = Enum.Material.SmoothPlastic -- табличка с текстом: без пупырышков
		Studs.Apply(board)
		board.Parent = stall
		Signs.Write(board, Enum.NormalId.Front, { { text = string.upper(shop.title), scale = 0.7 } })
	end
end

local function buildSpawn(parent: Instance)
	-- Точка появления игроков лицом к музеям. Своя SpawnLocation; чужие выключает Main (только в Play).
	local spawn = Instance.new("SpawnLocation")
	spawn.Name = "FieldSpawn"
	spawn.Anchored = true
	spawn.Neutral = true
	spawn.Duration = 0
	spawn.Size = MapLayout.Spawn.size
	local center = MapLayout.Spawn.position + Vector3.new(0, MapLayout.Spawn.size.Y / 2, 0)
	spawn.CFrame = CFrame.lookAt(center, center + Vector3.new(0, 0, 1))
	spawn.Color = Palette.FieldFloor
	spawn.Material = Enum.Material.Plastic
	Studs.Apply(spawn)
	local decal = spawn:FindFirstChildOfClass("Decal")
	if decal then
		decal:Destroy()
	end
	spawn.Parent = folder("Spawn", parent)
end

local function buildZone(index: number, parent: Instance)
	local zone = GameConfig.Zones[index]
	local frame = MapLayout.ZoneCFrame(index)
	local size = MapLayout.ZoneSize
	local f = folder(("Zone%d_%s"):format(index, zone.id), parent)
	f:SetAttribute("Zone", index)
	local ground = CFrame.new(frame.Position.X, H.Ground, frame.Position.Z) * frame.Rotation
	local accent = Color3.fromHex(zone.accent)

	slab("Floor", Vector2.new(MapLayout.ZoneHalfWidth * 2, size), frame.Position, H.Path, Color3.fromHex(zone.floor), f)

	-- Стена поперёк коридора на входе и ворота с вывеской: номер, название, босс и его сила.
	local entrance = ground * CFrame.new(0, 0, -size / 2)
	-- Стена начинается внутри стоек ворот: торцы стены и стоек не совпадают (D36).
	local wall = ZoneWall(MapLayout.ZoneHalfWidth, MapLayout.ZoneDoor + Gate.Post, MapLayout.ZoneWallHeight, accent)
	ModelBuilder.Place(ModelBuilder.Build("ZoneWall", wall), entrance, f)
	local gate = ModelBuilder.Place(ModelBuilder.Build("ZoneGate", Gate.Zone(MapLayout.ZoneDoor, accent)), entrance, f)
	local board = gate:FindFirstChild("SignBoard")
	if board and board:IsA("BasePart") then
		Signs.Write(board, Enum.NormalId.Front, {
			{ text = ("%d. %s"):format(index, zone.name), scale = 0.46 },
			{ text = ("%s %s %s"):format(zone.boss, BICEPS, NumberFormat.Short(GameConfig.Progression.Bosses[index])), scale = 0.3 },
		}, accent)
	end

	-- Постаменты под 4 предмета босса (D37).
	for i, spot in MapLayout.ArtSlots do
		place("Pedestal_" .. zone.id, function()
			return ZoneDecor.Pedestal(accent)
		end, frame * CFrame.new(spot.X, 0, spot.Y), f).Name = "Pedestal_" .. i
	end

	-- Декор по теме зоны.
	local decor: { ModelBuilder.Brick } = {}
	if zone.id == "Junk" then
		decor = ZoneDecor.Junk()
	elseif zone.id == "Flea" then
		decor = ZoneDecor.Flea(MapLayout.ArtSlots)
		for i, spot in { Vector2.new(-20, 26), Vector2.new(20, 26) } do
			local stripes = Palette.Awnings[i + 1]
			place("Stall_Flea_" .. i, function()
				return Plaza.Stall(stripes[1], stripes[2])
			end, frame * CFrame.new(spot.X, 0, spot.Y), f) -- прилавок (сторона -Z) смотрит ко входу
		end
	elseif zone.id == "Warehouse" then
		decor = ZoneDecor.Warehouse()
		for i, spot in { Vector3.new(-24, 0, -16), Vector3.new(24, 0, -16), Vector3.new(24, 4, -16), Vector3.new(-24, 0, -11) } do
			place("Crate", Props.Crate, frame * CFrame.new(spot) * CFrame.Angles(0, i * 0.2, 0), f)
		end
	elseif zone.id == "Bank" then
		decor = ZoneDecor.Bank(size)
	elseif zone.id == "Jungle" then
		decor = ZoneDecor.Jungle()
		for i, spot in { Vector2.new(-24, -14), Vector2.new(24, -4), Vector2.new(-24, 26), Vector2.new(24, 20) } do
			place("Tree_L_2", function()
				return Tree("L", 2)
			end, frame * CFrame.new(spot.X, 0, spot.Y) * CFrame.Angles(0, i, 0), f)
		end
	elseif ZoneDecor[zone.id] then
		decor = ZoneDecor[zone.id]()
	end
	ModelBuilder.Place(ModelBuilder.Build("Decor", decor), frame, f)
end


function WorldBuilder.Build(parent: Instance)
	local map = folder("Map", parent)
	buildGround(map)
	buildCliffs(map)
	buildShops(map)
	buildSpawn(map)
	local zones = folder("Zones", map)
	for index in GameConfig.Zones do
		buildZone(index, zones)
	end
end

-- Вода до горизонта и песчаное дно (Terrain). Только в Play: в режиме редактирования Terrain
-- сохранился бы в месте.
local WATER_SIZE = 3000
local WATER_DEPTH = 10

function WorldBuilder.BuildWater()
	local terrain = workspace.Terrain
	terrain.WaterColor = Palette.Water
	terrain.WaterTransparency = 0.4
	terrain.WaterWaveSize = 0.1
	local island = MapLayout.Island
	local center = Vector3.new(0, H.Water - WATER_DEPTH / 2, (island.minZ + island.maxZ) / 2)
	terrain:FillBlock(CFrame.new(center), Vector3.new(WATER_SIZE, WATER_DEPTH, WATER_SIZE), Enum.Material.Water)
	terrain:FillBlock(
		CFrame.new(center - Vector3.new(0, WATER_DEPTH / 2 + 2, 0)),
		Vector3.new(WATER_SIZE, 4, WATER_SIZE),
		Enum.Material.Sand
	)
end

return WorldBuilder

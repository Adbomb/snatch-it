-- Строит карту «аллея» (D12) и зоны добычи (D15) по MapLayout: траву, аллею с фонарями и лавочками,
-- точку появления с фонтаном, спортзал, сквер, ворота, дорожку, 4 зоны с забором, вывеской, постаментами
-- и декором, стену и холмы по краю. Только геометрия; участки-музеи строит PlotService.
-- Зависит от MapLayout, ModelBuilder, Palette, Signs, World/Models/*, GameConfig, UITokens.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local UITokens = require(ReplicatedStorage.Shared.Config.UITokens)
local World = ServerScriptService.Server.World
local MapLayout = require(World.MapLayout)
local ModelBuilder = require(World.ModelBuilder)
local Palette = require(World.Palette)
local Signs = require(World.Signs)
local Studs = require(World.Studs)
local Border = require(World.Models.Border)
local Fence = require(World.Models.Fence)
local Gate = require(World.Models.Gate)
local Gym = require(World.Models.Gym)
local Plaza = require(World.Models.Plaza)
local Props = require(World.Models.Props)
local Tree = require(World.Models.Tree)
local ZoneDecor = require(World.Models.ZoneDecor)

local B = ModelBuilder.Brick
local H = MapLayout.Heights
local SLAB = 0.4 -- толщина плит покрытия
local BICEPS = "💪"

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

local GRASS_PATCHES = 70
local PATCH_SIZE = Vector2.new(18, 40) -- мин. и макс. сторона пятна
local PATCH_MARGIN = 140 -- пятна и за стеной, до холмов

local function buildGround(parent: Instance)
	-- Одна большая плита травы закрывает Baseplate и уходит к горизонту.
	local size = 2048
	ModelBuilder.Build("Ground", {
		B(Vector3.new(size, 2, size), Vector3.new(0, H.Ground - 1, 0), Palette.Grass),
	}).Parent = parent
	-- Крупные пятна травы другого оттенка (детерминированно), чуть выше земли.
	local bounds = MapLayout.Bounds
	local random = Random.new(5)
	local patches: { ModelBuilder.Brick } = {}
	for _ = 1, GRASS_PATCHES do
		local w = random:NextNumber(PATCH_SIZE.X, PATCH_SIZE.Y)
		local d = random:NextNumber(PATCH_SIZE.X, PATCH_SIZE.Y)
		local x = random:NextNumber(bounds.minX - PATCH_MARGIN, bounds.maxX + PATCH_MARGIN)
		local z = random:NextNumber(bounds.minZ - PATCH_MARGIN, bounds.maxZ + PATCH_MARGIN)
		table.insert(
			patches,
			B(Vector3.new(w, 0.1, d), Vector3.new(x, H.Ground + 0.04, z), Palette.GrassPatch, { collide = false, shadow = false })
		)
	end
	ModelBuilder.Build("GrassPatches", patches).Parent = parent
end

local function buildAlley(parent: Instance)
	local alley = MapLayout.Alley
	local f = folder("Alley", parent)
	local length = alley.startZ - alley.endZ
	local midZ = (alley.startZ + alley.endZ) / 2
	slab("AlleyFloor", Vector2.new(alley.halfWidth * 2, length), Vector3.new(0, 0, midZ), H.Alley, Palette.Alley, f)

	-- Бордюры и мостовая в клетку.
	local bricks: { ModelBuilder.Brick } = {}
	local curbTop = H.Alley + 0.5
	for _, sign in { -1, 1 } do
		local x = sign * (alley.halfWidth - alley.curbWidth / 2)
		table.insert(bricks, B(Vector3.new(alley.curbWidth, curbTop, length), Vector3.new(x, curbTop / 2, midZ), Palette.Curb))
	end
	local inner = alley.halfWidth - alley.curbWidth
	local columns = math.floor(inner * 2 / alley.checkSize)
	local width = inner * 2 / columns
	local rows = math.floor(length / alley.checkSize)
	local depth = length / rows
	for column = 0, columns - 1 do
		for row = 0, rows - 1 do
			if (column + row) % 2 == 0 then
				local x = -inner + (column + 0.5) * width
				local z = alley.startZ - (row + 0.5) * depth
				table.insert(
					bricks,
					B(Vector3.new(width, 0.1, depth), Vector3.new(x, H.Alley + 0.05, z), Palette.AlleyCheck, { collide = false, shadow = false })
				)
			end
		end
	end
	ModelBuilder.Build("AlleyDetails", bricks).Parent = f

	-- Фонари и лавочки в промежутках между музеями, кусты в самих промежутках.
	local gaps = { 87, 37, -13, -63, -115 }
	for _, z in gaps do
		for _, sign in { -1, 1 } do
			place("Lamp", Props.Lamp, CFrame.new(sign * (alley.halfWidth - 3), H.Alley, z), f)
		end
	end
	for i = 2, 4 do
		local z = gaps[i]
		for _, sign in { -1, 1 } do
			local at = Vector3.new(sign * (alley.halfWidth - 6), H.Alley, z + 4)
			place("Bench", Props.Bench, CFrame.lookAt(at, at + Vector3.new(-sign, 0, 0)), f)
			place("Bush_" .. i, function()
				return Props.Bush(i)
			end, CFrame.new(sign * 44, H.Ground, z), f)
		end
	end
	-- Деревья за музеями.
	for i, z in { 80, 40, 0, -40, -80, -120 } do
		for _, sign in { -1, 1 } do
			local size = if i % 2 == 0 then "L" else "M"
			local color = (i + (sign + 1) / 2) % #Palette.Leaves + 1
			place(("Tree_%s_%d"):format(size, color), function()
				return Tree(size, color)
			end, CFrame.new(sign * 80, H.Ground, z) * CFrame.Angles(0, i, 0), f)
		end
	end
end

local function buildStart(parent: Instance)
	local f = folder("Start", parent)
	place("Fountain", Plaza.Fountain, CFrame.new(MapLayout.Fountain), f)

	-- Точка появления игроков. Своя SpawnLocation; чужие выключает Main (только в Play).
	local spawn = Instance.new("SpawnLocation")
	spawn.Name = "AlleySpawn"
	spawn.Anchored = true
	spawn.Neutral = true
	spawn.Duration = 0
	spawn.Size = MapLayout.Spawn.size
	spawn.CFrame = CFrame.lookAt(
		MapLayout.Spawn.position + Vector3.new(0, MapLayout.Spawn.size.Y / 2, 0),
		MapLayout.Spawn.position + Vector3.new(0, MapLayout.Spawn.size.Y / 2, -1)
	)
	spawn.Color = UITokens.Gradients.Go.top
	spawn.Material = Enum.Material.Plastic
	Studs.Apply(spawn)
	spawn.Parent = f

	-- Сквер напротив спортзала.
	local garden = MapLayout.Garden
	for i, offset in { Vector2.new(-10, -10), Vector2.new(10, 8), Vector2.new(-6, 12) } do
		local color = i % #Palette.Leaves + 1
		place(("Tree_M_%d"):format(color), function()
			return Tree("M", color)
		end, CFrame.new(garden.center + Vector3.new(offset.X, 0, offset.Y)), f)
	end
	for _, offset in { Vector2.new(8, -10), Vector2.new(14, -4) } do
		place("Bush_1", function()
			return Props.Bush(1)
		end, CFrame.new(garden.center + Vector3.new(offset.X, 0, offset.Y)), f)
	end
	local benchAt = garden.center + Vector3.new(-16, 0, 0)
	place("Bench", Props.Bench, CFrame.lookAt(benchAt, benchAt + Vector3.new(-1, 0, 0)), f)
end

local function buildGym(parent: Instance)
	local gym = MapLayout.Gym
	local f = folder("Gym", parent)
	local hall = ModelBuilder.Place(ModelBuilder.Build("GymHall", Gym.Hall(gym.size)), CFrame.new(gym.center), f)
	local hallSign = hall:FindFirstChild("SignBoard")
	if hallSign and hallSign:IsA("BasePart") then
		Signs.Write(hallSign, Enum.NormalId.Right, { { text = "СПОРТЗАЛ " .. BICEPS, scale = 0.8 } })
	end
	-- Стойки в ряд вдоль аллеи, лицом к ней (+X).
	local dumbbells = GameConfig.Gym.Dumbbells
	for i, dumbbell in dumbbells do
		local z = gym.center.Z + (i - (#dumbbells + 1) / 2) * gym.rackSpacing
		local at = Vector3.new(gym.center.X + gym.size.X / 2 - 8, gym.center.Y, z)
		local rack = ModelBuilder.Place(ModelBuilder.Build("Rack_" .. dumbbell.id, Gym.Rack(dumbbell.id)), CFrame.lookAt(at, at + Vector3.new(1, 0, 0)), f)
		rack:SetAttribute("Dumbbell", dumbbell.id)
		local board = rack:FindFirstChild("SignBoard")
		if board and board:IsA("BasePart") then
			local price = if dumbbell.price == 0 then "Бесплатно" else "Скоро"
			Signs.Write(board, Enum.NormalId.Front, {
				{ text = dumbbell.name, scale = 0.36 },
				{ text = ("+%d %s"):format(dumbbell.power, BICEPS), scale = 0.32 },
				{ text = price, scale = 0.26 },
			})
		end
	end
end

local function buildGateAndPath(parent: Instance)
	local f = folder("Gate", parent)
	local gate = MapLayout.Gate
	local at = Vector3.new(0, H.Alley, gate.z)
	local arch = ModelBuilder.Place(ModelBuilder.Build("AlleyGate", Gate.Alley(gate.width)), CFrame.lookAt(at, at + Vector3.new(0, 0, 1)), f)
	local board = arch:FindFirstChild("SignBoard")
	if board and board:IsA("BasePart") then
		Signs.Write(board, Enum.NormalId.Front, { { text = "ЗОНЫ ДОБЫЧИ", scale = 0.7 } })
	end
	local path = MapLayout.Path
	slab(
		"Path",
		Vector2.new(path.halfWidth * 2, path.fromZ - path.toZ),
		Vector3.new(0, 0, (path.fromZ + path.toZ) / 2),
		H.Path,
		Palette.Street,
		f
	)
end

local ZONE_FLOORS = {
	Junk = Color3.fromHex("A1887F"),
	Flea = Color3.fromHex("F3D9A4"),
	Warehouse = Color3.fromHex("90A4AE"),
	Bank = Color3.fromHex("ECEFF1"),
}

local function buildZone(index: number, parent: Instance)
	local zone = GameConfig.Zones[index]
	local frame = MapLayout.ZoneCFrame(index)
	local size = MapLayout.ZoneSize
	local f = folder(("Zone%d_%s"):format(index, zone.id), parent)
	f:SetAttribute("Zone", index)
	local ground = CFrame.new(frame.Position.X, H.Ground, frame.Position.Z) * frame.Rotation
	local signColor = UITokens.RarityColor(zone.rarity)

	slab("Floor", Vector2.new(size, size), frame.Position, H.Path, ZONE_FLOORS[zone.id] or Palette.Pavement, f)
	ModelBuilder.Place(ModelBuilder.Build("Fence", Fence(size, 12, Palette.White, signColor)), ground, f)

	-- Ворота с вывеской: название и сила стража.
	local gate = ModelBuilder.Place(ModelBuilder.Build("ZoneGate", Gate.Zone(12, signColor)), ground * CFrame.new(0, 0, -size / 2), f)
	local board = gate:FindFirstChild("SignBoard")
	if board and board:IsA("BasePart") then
		Signs.Write(board, Enum.NormalId.Front, {
			{ text = zone.name, scale = 0.55 },
			{ text = ("Сила стража: %s %s"):format(tostring(zone.guard.strength), BICEPS), scale = 0.38 },
		})
	end

	-- Постаменты под предметы.
	for i, spot in MapLayout.Pedestals do
		place("Pedestal_" .. zone.id, function()
			return ZoneDecor.Pedestal(signColor)
		end, frame * CFrame.new(spot.X, 0, spot.Y), f).Name = "Pedestal_" .. i
	end

	-- Декор по теме зоны.
	local decor: { ModelBuilder.Brick } = {}
	if zone.id == "Junk" then
		decor = ZoneDecor.Junk()
	elseif zone.id == "Flea" then
		decor = ZoneDecor.Flea(MapLayout.Pedestals)
		for i, spot in { Vector2.new(-20, 26), Vector2.new(20, 26) } do
			local stripes = Palette.Awnings[i + 1]
			place("Stall_Flea_" .. i, function()
				return Plaza.Stall(stripes[1], stripes[2])
			end, frame * CFrame.new(spot.X, 0, spot.Y), f) -- прилавок (сторона -Z) смотрит к воротам
		end
	elseif zone.id == "Warehouse" then
		decor = ZoneDecor.Warehouse()
		for i, spot in { Vector3.new(-24, 0, -16), Vector3.new(24, 0, -16), Vector3.new(24, 4, -16), Vector3.new(-24, 0, -11) } do
			place("Crate", Props.Crate, frame * CFrame.new(spot) * CFrame.Angles(0, i * 0.2, 0), f)
		end
	elseif zone.id == "Bank" then
		decor = ZoneDecor.Bank(size)
	end
	ModelBuilder.Place(ModelBuilder.Build("Decor", decor), frame, f)
end

function WorldBuilder.Build(parent: Instance)
	local map = folder("Map", parent)
	buildGround(map)
	buildAlley(map)
	buildStart(map)
	buildGym(map)
	buildGateAndPath(map)
	local zones = folder("Zones", map)
	for index in GameConfig.Zones do
		buildZone(index, zones)
	end
	local border = folder("Border", map)
	ModelBuilder.Build("BorderWall", Border.Wall(MapLayout.Bounds, H.Ground)).Parent = border
	local hills, tops = Border.Hills(MapLayout.Bounds, H.Ground)
	ModelBuilder.Build("BorderHills", hills).Parent = border
	for i, top in tops do
		local size = if i % 3 == 0 then "L" else "M"
		local color = i % #Palette.Leaves + 1
		place(("Tree_%s_%d"):format(size, color), function()
			return Tree(size, color)
		end, top * CFrame.Angles(0, i, 0), border)
	end
end

return WorldBuilder

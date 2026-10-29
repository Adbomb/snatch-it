-- Строит участки-музеи: здание из Blender по уровню (World/MeshBuilder, D33) с невидимыми стенами, части
-- с механикой витрин (окружение витрин и сундука — кирпичи World/Models/Museum) и двор перед входом (D34,
-- D35): дорожка, поле качалки, табличка «Улучшение» и место огромной гантели (её ставит GymService).
-- Карту строит World/WorldBuilder. Только геометрия, без логики.
-- Зависит от GameConfig, World/MapLayout, World/MeshBuilder, World/ModelBuilder, World/Models/Museum,
-- World/Models/Gym, World/Signs.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local MapLayout = require(ServerScriptService.Server.World.MapLayout)
local MeshBuilder = require(ServerScriptService.Server.World.MeshBuilder)
local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Gym = require(ServerScriptService.Server.World.Models.Gym)
local Museum = require(ServerScriptService.Server.World.Models.Museum)
local Signs = require(ServerScriptService.Server.World.Signs)

local PartBuilder = {}

-- Верх пола участков (выше травы и дорог, см. MapLayout.Heights).
PartBuilder.FloorTop = MapLayout.Heights.Floor

local PATH_COLOR = Color3.fromHex("B0B6BF") -- дорожка ко входу
local SIGN_COLOR = Color3.fromHex("1E2A4A") -- табло таблички «Улучшение» (тёмно-синее, как на референсе)
local YARD_DARKEN = 0.6 -- двор — тёмный оттенок цвета участка

export type PlotParts = {
	model: Model,
	showcases: { [number]: BasePart },
	exhibits: Folder,
	signLabel: TextLabel,
	chest: BasePart,
	floorOrigin: CFrame, -- центр участка на уровне пола, вход в -Z
	accent: Color3,
	fieldCFrame: CFrame, -- центр поля качалки на уровне двора
	dumbbellCFrame: CFrame, -- где висит огромная гантель (рукоять вдоль Z участка)
	signBoard: BasePart, -- табло таблички «Улучшение» (лицо — сторона -Z, к площади)
}

-- Размеры зала, общие для всех моделей музея: фасад и вывеска одинаковые, лампы — под самым низким потолком.
local function hallSize(): (number, number, number, number)
	local facadeZ, signY, lamp, ceiling = 0, 0, math.huge, math.huge
	for i = 1, GameConfig.Models.MuseumModelCount do
		local hall = MeshBuilder.Get("Museum" .. i)
		if hall then
			facadeZ, signY = hall.facadeZ :: number, hall.signY :: number
			lamp = math.min(lamp, hall.lampHeight :: number)
			ceiling = math.min(ceiling, hall.wallHeight :: number)
		end
	end
	return facadeZ, signY, lamp, ceiling
end

type PartProps = {
	name: string,
	size: Vector3,
	cframe: CFrame,
	color: Color3,
	parent: Instance,
	material: Enum.Material?,
	transparency: number?,
	canCollide: boolean?,
}

function PartBuilder.MakePart(props: PartProps): Part
	local part = Instance.new("Part")
	part.Name = props.name
	part.Anchored = true
	part.Size = props.size
	part.CFrame = props.cframe
	part.Color = props.color
	part.Material = props.material or Enum.Material.Plastic
	part.Transparency = props.transparency or 0
	part.CanCollide = if props.canCollide == nil then true else props.canCollide
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Parent = props.parent
	return part
end

function PartBuilder.CreateWorldFolder(): Folder
	local world = Instance.new("Folder")
	world.Name = "World"
	world.Parent = workspace
	return world
end

-- Участок index стоит по MapLayout и смотрит входом (сторона -Z) на аллею. Здание — World/Models/Museum;
-- здесь части с механикой: Floor, витрины Showcase_i (папка Showcases), Chest, табличка, лампы, Exhibits.
function PartBuilder.BuildPlot(index: number, origin: CFrame, slotCount: number, parent: Instance): PlotParts
	local cfg = GameConfig.World
	local top = PartBuilder.FloorTop
	local accent = Museum.Accents[(index - 1) % #Museum.Accents + 1]
	local floorOrigin = origin * CFrame.new(0, top, 0)

	local model = Instance.new("Model")
	model.Name = "Plot_" .. index
	model:SetAttribute("PlotIndex", index)
	model:SetAttribute("OwnerUserId", 0)

	-- Пол: толстая плита от земли до уровня пола музея.
	local floorThickness = top + 0.2
	local floor = PartBuilder.MakePart({
		name = "Floor",
		size = Vector3.new(cfg.PlotSize.X, floorThickness, cfg.PlotSize.Z),
		cframe = origin * CFrame.new(0, top - floorThickness / 2, 0),
		color = accent:Lerp(Color3.new(0, 0, 0), 0.55),
		parent = model,
	})
	model.PrimaryPart = floor

	local facadeZ, signY, lampHeight, ceiling = hallSize()
	PartBuilder.SetBuilding(model, floorOrigin, accent, 1)

	-- Вывеска «МУЗЕЙ <имя>» над входом.
	local board = PartBuilder.MakePart({
		name = "Sign",
		size = Vector3.new(18, 3.2, 0.4),
		cframe = floorOrigin * CFrame.new(0, signY, facadeZ - 0.75),
		color = accent:Lerp(Color3.new(0, 0, 0), 0.25),
		material = Enum.Material.SmoothPlastic, -- табличка с текстом: без пупырышков
		parent = model,
	})
	local signLabel = Signs.Write(board, Enum.NormalId.Front, { { text = "", scale = 0.8 } })[1]

	-- Витрины: два ряда по три, номер на передней грани; вокруг — колпак, канаты, лампа сверху.
	local showcaseFolder = Instance.new("Folder")
	showcaseFolder.Name = "Showcases"
	showcaseFolder.Parent = model
	local decorFolder = Instance.new("Folder")
	decorFolder.Name = "ShowcaseDecor"
	decorFolder.Parent = model
	local lampFolder = Instance.new("Folder")
	lampFolder.Name = "Lamps"
	lampFolder.Parent = model
	local showcaseSize = GameConfig.Museum.ShowcaseSize
	local step = GameConfig.Museum.ShowcaseStep
	local showcases = {}
	for slot = 1, slotCount do
		local column = (slot - 1) % 3
		local row = (slot - 1) // 3
		local base = floorOrigin * CFrame.new((column - 1) * step.X, 0, -2 + row * step.Y)
		local showcase = PartBuilder.MakePart({
			name = "Showcase_" .. slot,
			size = showcaseSize,
			cframe = base * CFrame.new(0, showcaseSize.Y / 2, 0),
			color = Color3.fromHex("3C4A5C"),
			parent = showcaseFolder,
		})
		showcase:SetAttribute("Slot", slot)
		showcase:SetAttribute("Occupied", false)
		Signs.Write(showcase, Enum.NormalId.Front, { { text = tostring(slot), scale = 0.7 } })
		showcases[slot] = showcase

		ModelBuilder.Place(ModelBuilder.Build("Decor_" .. slot, Museum.ShowcaseDecor(showcaseSize, accent)), base, decorFolder)
		local lamp =
			ModelBuilder.Place(ModelBuilder.Build("Lamp_" .. slot, Museum.Lamp(lampHeight, ceiling)), base, lampFolder)
		local bulb = lamp:FindFirstChild("Bulb")
		if bulb then
			-- Прожектор презентации: выключен, включает PresentationController у зрителей.
			local spot = Instance.new("SpotLight")
			spot.Name = "PresentationLight"
			spot.Face = Enum.NormalId.Bottom
			spot.Enabled = false
			spot.Parent = bulb
			-- Мягкий свет зала: по одной лампе в центре каждого ряда.
			if column == 1 then
				local glow = Instance.new("PointLight")
				glow.Range = 22
				glow.Brightness = 1
				glow.Color = Color3.fromHex("FFE8B0")
				glow.Shadows = false
				glow.Parent = bulb
			end
		end
	end

	-- Сундук-хранилище у входа, слева от прохода: корпус (Chest) + крышка, полосы, замок.
	local chestSize = GameConfig.Museum.ChestSize
	local chestCFrame = floorOrigin * CFrame.new(-12, chestSize.Y / 2, facadeZ + 4)
	local chest = PartBuilder.MakePart({
		name = "Chest",
		size = chestSize,
		cframe = chestCFrame,
		color = Color3.fromHex("8A5A2B"),
		parent = model,
	})
	ModelBuilder.Place(ModelBuilder.Build("ChestDecor", Museum.ChestDecor(chestSize)), chestCFrame, model)

	-- Двор перед музеем (D34, D35): плита, дорожка ко входу, поле качалки, табличка «Улучшение».
	local yard = MapLayout.PlotYard
	local yardOrigin = origin * CFrame.new(0, MapLayout.Heights.Plaza, 0)
	PartBuilder.MakePart({
		name = "Yard",
		size = Vector3.new(yard.size.X, 0.4, yard.size.Y),
		cframe = yardOrigin * CFrame.new(yard.center.X, -0.2, yard.center.Y),
		color = accent:Lerp(Color3.new(0, 0, 0), YARD_DARKEN),
		parent = model,
	})
	PartBuilder.MakePart({
		name = "YardPath",
		size = Vector3.new(yard.path, 0.1, yard.size.Y),
		cframe = yardOrigin * CFrame.new(0, 0.05, yard.center.Y),
		color = PATH_COLOR,
		canCollide = false,
		parent = model,
	})
	local fieldCFrame = yardOrigin * CFrame.new(yard.field.X, 0, yard.field.Y)
	local fieldBricks = Gym.Field(GameConfig.Gym.FieldSize, accent)
	local field = ModelBuilder.Place(ModelBuilder.Build("GymField", fieldBricks), fieldCFrame, model)
	field:SetAttribute("GymField", true)
	local signCFrame = yardOrigin * CFrame.new(yard.sign.X, 0, yard.sign.Y)
	ModelBuilder.Place(ModelBuilder.Build("SignPost", Gym.SignPost()), signCFrame, model)
	local signBoard = PartBuilder.MakePart({
		name = "UpgradeBoard",
		size = Gym.SignBoard,
		cframe = signCFrame * CFrame.new(0, Gym.SignHeight, 0),
		color = SIGN_COLOR,
		material = Enum.Material.SmoothPlastic, -- табличка с текстом: без пупырышков
		parent = model,
	})

	local exhibits = Instance.new("Folder")
	exhibits.Name = "Exhibits"
	exhibits.Parent = model

	model.Parent = parent
	return {
		model = model,
		showcases = showcases,
		exhibits = exhibits,
		signLabel = signLabel,
		chest = chest,
		floorOrigin = floorOrigin,
		accent = accent,
		fieldCFrame = fieldCFrame,
		dumbbellCFrame = fieldCFrame * CFrame.new(0, Gym.DumbbellHeight, 0) * CFrame.Angles(0, math.rad(90), 0),
		signBoard = signBoard,
	}
end

-- Здание музея уровня level (1–10): модель ceil(level / 2), на чётных уровнях с декором, и невидимые простые
-- стены зала вместо столкновений мешей. Прежнее здание участка заменяется.
function PartBuilder.SetBuilding(model: Model, floorOrigin: CFrame, accent: Color3, level: number)
	for _, name in { "Building", "Walls" } do
		local old = model:FindFirstChild(name)
		if old then
			old:Destroy()
		end
	end
	local count = GameConfig.Models.MuseumModelCount
	local hallName = "Museum" .. math.clamp(math.ceil(level / 2), 1, count)
	MeshBuilder.Build(hallName, floorOrigin, model, { accent = accent, decor = level % 2 == 0, name = "Building" })
	local hall = MeshBuilder.Get(hallName)
	if not hall then
		return
	end
	local walls = Instance.new("Folder")
	walls.Name = "Walls"
	walls.Parent = model
	local half, t, h = hall.halfWidth :: number, hall.wallThickness :: number, hall.wallHeight :: number
	local front, back, door = hall.facadeZ :: number, hall.back :: number, hall.doorWidth :: number
	local function wall(name: string, size: Vector3, center: Vector3)
		local part = PartBuilder.MakePart({
			name = name,
			size = size,
			cframe = floorOrigin * CFrame.new(center),
			color = accent,
			transparency = 1,
			parent = walls,
		})
		part.CanQuery = false
		part.CanTouch = false
	end
	for _, sx in { -1, 1 } do
		wall("Side", Vector3.new(t, h, back - front), Vector3.new(sx * (half - t / 2), h / 2, (front + back) / 2))
		local side = half - door / 2
		wall("Facade", Vector3.new(side, h, t), Vector3.new(sx * (door / 2 + side / 2), h / 2, front + t / 2))
	end
	wall("Back", Vector3.new(half * 2, h, t), Vector3.new(0, h / 2, back - t / 2))
end

return PartBuilder

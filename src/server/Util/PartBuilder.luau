-- Строит участки-музеи: здание музея по уровню (World/Models/MuseumHall, D36), части с механикой витрин (окружение
-- витрин и сундука — кирпичи World/Models/Museum), поле качалки и табличку «Улучшение» перед музеем (D34, D36) и
-- место огромной гантели (её ставит GymService). Карту строит World/WorldBuilder. Только геометрия, без логики.
-- Зависит от GameConfig, World/MapLayout, World/ModelBuilder, World/Palette, World/Models/Museum,
-- World/Models/MuseumHall, World/Models/Gym, World/Signs.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Textures = require(ReplicatedStorage.Shared.Config.Textures)
local MapLayout = require(ServerScriptService.Server.World.MapLayout)
local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Gym = require(ServerScriptService.Server.World.Models.Gym)
local Museum = require(ServerScriptService.Server.World.Models.Museum)
local MuseumHall = require(ServerScriptService.Server.World.Models.MuseumHall)
local Palette = require(ServerScriptService.Server.World.Palette)
local Signs = require(ServerScriptService.Server.World.Signs)

local PartBuilder = {}

-- Верх пола участков (выше травы и дорог, см. MapLayout.Heights).
PartBuilder.FloorTop = MapLayout.Heights.Floor


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
	signBoard: BasePart, -- табло таблички «Улучшение» (лицо — сторона -Z, к полю)
}

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

-- Участок index стоит по MapLayout и смотрит входом (сторона -Z) на поле. Здание — World/Models/MuseumHall;
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

	-- Пол: толстая плита от земли до уровня пола музея (светлый, спокойный рельеф — как у здания).
	local floorThickness = top + 0.2
	local floor = PartBuilder.MakePart({
		name = "Floor",
		size = Vector3.new(cfg.PlotSize.X, floorThickness, cfg.PlotSize.Z),
		cframe = origin * CFrame.new(0, top - floorThickness / 2, 0),
		color = Palette.MuseumFloor,
		parent = model,
	})
	floor.MaterialVariant = Textures.SquaresSoft.name
	model.PrimaryPart = floor

	local facadeZ, signY = MuseumHall.FacadeZ, MuseumHall.SignY
	local lampHeight, ceiling = MuseumHall.LampHeight, MuseumHall.Ceiling
	PartBuilder.SetBuilding(model, floorOrigin, accent, 1)

	-- Вывеска «МУЗЕЙ <имя>» над входом.
	local board = PartBuilder.MakePart({
		name = "Sign",
		size = Vector3.new(18, 3.2, 0.4),
		cframe = floorOrigin * CFrame.new(0, signY, facadeZ - 0.75),
		color = Palette.Muted(accent),
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
	-- Вплотную к фасаду (зазор 0.1), замком в зал: подсказки витрины 1 не перехватывают E у сундука.
	local chestCFrame = floorOrigin
		* CFrame.new(-12, chestSize.Y / 2, facadeZ + 1.4 + chestSize.Z / 2 + 0.1)
		* CFrame.Angles(0, math.pi, 0)
	local chest = PartBuilder.MakePart({
		name = "Chest",
		size = chestSize,
		cframe = chestCFrame,
		color = Color3.fromHex("8A5A2B"),
		parent = model,
	})
	ModelBuilder.Place(ModelBuilder.Build("ChestDecor", Museum.ChestDecor(chestSize)), chestCFrame, model)

	-- Поле качалки и табличка «Улучшение» перед музеем, спереди слева (D34, D36).
	local yard = MapLayout.PlotYard
	local yardOrigin = origin * CFrame.new(0, MapLayout.Heights.Ground, 0)
	local fieldCFrame = yardOrigin * CFrame.new(yard.field.X, 0, yard.field.Y)
	local fieldBricks = Gym.Field(GameConfig.Gym.FieldSize, Palette.Muted(accent))
	local field = ModelBuilder.Place(ModelBuilder.Build("GymField", fieldBricks), fieldCFrame, model)
	field:SetAttribute("GymField", true)
	local signCFrame = yardOrigin * CFrame.new(yard.sign.X, 0, yard.sign.Y)
	ModelBuilder.Place(ModelBuilder.Build("SignPost", Gym.SignPost()), signCFrame, model)
	local signBoard = PartBuilder.MakePart({
		name = "UpgradeBoard",
		size = Gym.SignBoard,
		cframe = signCFrame * CFrame.new(0, Gym.SignHeight, 0),
		color = Palette.SignBoard,
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

-- Здание музея уровня level (1–10, D36): стартовый зал, с уровнем — боковые залы, портик на 6 колонн, купол,
-- позолота; на чётных уровнях — оформление. Прежнее здание участка заменяется.
function PartBuilder.SetBuilding(model: Model, floorOrigin: CFrame, accent: Color3, level: number)
	local old = model:FindFirstChild("Building")
	if old then
		old:Destroy()
	end
	ModelBuilder.Place(ModelBuilder.Build("Building", MuseumHall.Build(level, accent)), floorOrigin, model)
end

return PartBuilder

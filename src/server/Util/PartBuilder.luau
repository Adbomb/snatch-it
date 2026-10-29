-- Строит участки-музеи: здание из кирпичей (World/Models/Museum) и части с механикой витрин.
-- Карту строит World/WorldBuilder. Только геометрия, без логики.
-- Зависит от GameConfig, World/MapLayout, World/ModelBuilder, World/Models/Museum, World/Signs.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local MapLayout = require(ServerScriptService.Server.World.MapLayout)
local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Museum = require(ServerScriptService.Server.World.Models.Museum)
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

	ModelBuilder.Place(ModelBuilder.Build("Building", Museum.Building(accent)), floorOrigin, model)

	-- Вывеска «МУЗЕЙ <имя>» над входом.
	local board = PartBuilder.MakePart({
		name = "Sign",
		size = Vector3.new(18, 3.2, 0.4),
		cframe = floorOrigin * CFrame.new(0, Museum.SignY, Museum.FacadeZ - 0.75),
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
	local lampHeight = Museum.WallHeight - 2.5
	local showcases = {}
	for slot = 1, slotCount do
		local column = (slot - 1) % 3
		local row = (slot - 1) // 3
		local base = floorOrigin * CFrame.new((column - 1) * 12, 0, -2 + row * 14)
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
		local lamp = ModelBuilder.Place(ModelBuilder.Build("Lamp_" .. slot, Museum.Lamp(lampHeight)), base, lampFolder)
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
	local chestCFrame = floorOrigin * CFrame.new(-15, chestSize.Y / 2, Museum.FacadeZ + 4)
	local chest = PartBuilder.MakePart({
		name = "Chest",
		size = chestSize,
		cframe = chestCFrame,
		color = Color3.fromHex("8A5A2B"),
		parent = model,
	})
	ModelBuilder.Place(ModelBuilder.Build("ChestDecor", Museum.ChestDecor(chestSize)), chestCFrame, model)

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
	}
end

return PartBuilder

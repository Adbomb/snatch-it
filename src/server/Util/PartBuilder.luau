-- Строит участки-музеи с витринами из простых Part. Город строит World/WorldBuilder.
-- Только геометрия, без логики. Зависит от GameConfig, World/MapLayout.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local MapLayout = require(ServerScriptService.Server.World.MapLayout)

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
	part.Material = props.material or Enum.Material.SmoothPlastic
	part.Transparency = props.transparency or 0
	part.CanCollide = if props.canCollide == nil then true else props.canCollide
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Parent = props.parent
	return part
end

local function addSurfaceText(part: BasePart, text: string): TextLabel
	local gui = Instance.new("SurfaceGui")
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 40
	gui.Parent = part

	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextScaled = true
	label.Font = Enum.Font.GothamBold
	label.Text = text
	label.Parent = gui
	return label
end

function PartBuilder.CreateWorldFolder(): Folder
	local world = Instance.new("Folder")
	world.Name = "World"
	world.Parent = workspace
	return world
end

-- Участок index стоит по MapLayout и смотрит входом (сторона -Z) в город.
function PartBuilder.BuildPlot(index: number, origin: CFrame, slotCount: number, parent: Instance): PlotParts
	local cfg = GameConfig.World
	local half = cfg.PlotSize.X / 2
	local top = PartBuilder.FloorTop

	local model = Instance.new("Model")
	model.Name = "Plot_" .. index
	model:SetAttribute("PlotIndex", index)
	model:SetAttribute("OwnerUserId", 0)

	local floor = PartBuilder.MakePart({
		name = "Floor",
		size = cfg.PlotSize,
		cframe = origin * CFrame.new(0, top - cfg.PlotSize.Y / 2, 0),
		color = Color3.fromRGB(160, 120, 90),
		material = Enum.Material.WoodPlanks,
		parent = model,
	})
	model.PrimaryPart = floor

	local wallColor = Color3.fromRGB(235, 225, 205)
	local h = cfg.WallHeight
	local walls = {
		{
			name = "WallLeft",
			size = Vector3.new(1, h, cfg.PlotSize.Z),
			offset = CFrame.new(-half + 0.5, top + h / 2, 0),
		},
		{
			name = "WallRight",
			size = Vector3.new(1, h, cfg.PlotSize.Z),
			offset = CFrame.new(half - 0.5, top + h / 2, 0),
		},
		{
			name = "WallBack",
			size = Vector3.new(cfg.PlotSize.X, h, 1),
			offset = CFrame.new(0, top + h / 2, half - 0.5),
		},
	}
	for _, wall in walls do
		PartBuilder.MakePart({
			name = wall.name,
			size = wall.size,
			cframe = origin * wall.offset,
			color = wallColor,
			parent = model,
		})
	end

	-- Табличка у входа: две стойки и доска с текстом, повёрнутая лицом к площади.
	local signZ = -half + 1
	for _, x in { -6.5, 6.5 } do
		PartBuilder.MakePart({
			name = "SignPost",
			size = Vector3.new(0.6, 9, 0.6),
			cframe = origin * CFrame.new(x, top + 4.5, signZ),
			color = Color3.fromRGB(90, 60, 40),
			parent = model,
		})
	end
	local board = PartBuilder.MakePart({
		name = "Sign",
		size = Vector3.new(14, 3, 0.4),
		cframe = origin * CFrame.new(0, top + 7.5, signZ),
		color = Color3.fromRGB(40, 40, 60),
		parent = model,
	})
	local signLabel = addSurfaceText(board, "")

	-- Витрины: два ряда по три, номер написан на передней грани.
	local showcaseFolder = Instance.new("Folder")
	showcaseFolder.Name = "Showcases"
	showcaseFolder.Parent = model
	local showcaseSize = GameConfig.Museum.ShowcaseSize
	local showcases = {}
	for slot = 1, slotCount do
		local column = (slot - 1) % 3
		local row = (slot - 1) // 3
		local showcase = PartBuilder.MakePart({
			name = "Showcase_" .. slot,
			size = showcaseSize,
			cframe = origin * CFrame.new((column - 1) * 12, top + showcaseSize.Y / 2, -2 + row * 14),
			color = Color3.fromRGB(70, 90, 120),
			material = Enum.Material.Marble,
			parent = showcaseFolder,
		})
		showcase:SetAttribute("Slot", slot)
		showcase:SetAttribute("Occupied", false)
		addSurfaceText(showcase, tostring(slot))
		showcases[slot] = showcase
	end

	-- Сундук-хранилище у входа, слева от прохода.
	local chestSize = GameConfig.Museum.ChestSize
	local chest = PartBuilder.MakePart({
		name = "Chest",
		size = chestSize,
		cframe = origin * CFrame.new(-half + 5, top + chestSize.Y / 2, -half + 5),
		color = Color3.fromRGB(150, 95, 45),
		material = Enum.Material.Wood,
		parent = model,
	})
	addSurfaceText(chest, "Хранилище")

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

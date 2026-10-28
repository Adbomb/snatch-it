-- Строит мир из простых Part: центральную площадь и участки-музеи с витринами.
-- Только геометрия, без логики. Зависит от GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

local PartBuilder = {}

-- Верх пола площади и участков (Baseplate из шаблона Studio имеет верх на Y = 0).
PartBuilder.FloorTop = 0.1

export type PlotParts = {
	model: Model,
	showcases: { [number]: BasePart },
	exhibits: Folder,
	signLabel: TextLabel,
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

function PartBuilder.BuildPlaza(parent: Instance): Part
	local size = GameConfig.World.PlazaSize
	return PartBuilder.MakePart({
		name = "Plaza",
		size = size,
		cframe = CFrame.new(0, PartBuilder.FloorTop - size.Y / 2, 0),
		color = Color3.fromRGB(200, 195, 185),
		material = Enum.Material.Concrete,
		parent = parent,
	})
end

-- Платформы-«крыши» на окраинах со ступеньками со стороны площади.
-- Возвращает CFrame верхней грани каждой крыши (центр) — туда ставятся точки Far.
function PartBuilder.BuildRoofs(parent: Instance): { CFrame }
	local cfg = GameConfig.World
	local folder = Instance.new("Folder")
	folder.Name = "Roofs"
	folder.Parent = parent
	local tops = {}
	for index, roof in cfg.Roofs do
		local angle = math.rad(roof.angle)
		local position = Vector3.new(math.cos(angle) * roof.radius, 0, math.sin(angle) * roof.radius)
		local origin = CFrame.lookAt(position, Vector3.zero) -- -Z смотрит на площадь
		local size = roof.size
		local top = PartBuilder.FloorTop + size.Y
		PartBuilder.MakePart({
			name = "Roof_" .. index,
			size = size,
			cframe = origin * CFrame.new(0, top - size.Y / 2, 0),
			color = Color3.fromRGB(150, 75, 60),
			material = Enum.Material.Brick,
			parent = folder,
		})
		-- Ступеньки: каждая выше предыдущей не больше чем на StepHeight, самая высокая — у крыши.
		local steps = math.ceil(size.Y / cfg.StepHeight) - 1
		for step = 1, steps do
			local height = size.Y * step / (steps + 1)
			local z = -size.Z / 2 - (steps - step + 0.5) * cfg.StepSize.Y
			PartBuilder.MakePart({
				name = ("Roof_%d_Step_%d"):format(index, step),
				size = Vector3.new(cfg.StepSize.X, height, cfg.StepSize.Y),
				cframe = origin * CFrame.new(0, PartBuilder.FloorTop + height / 2, z),
				color = Color3.fromRGB(120, 110, 100),
				material = Enum.Material.Concrete,
				parent = folder,
			})
		end
		table.insert(tops, origin * CFrame.new(0, top, 0))
	end
	return tops
end

-- Участок index из count стоит на круге и смотрит входом (сторона -Z) в центр площади.
function PartBuilder.BuildPlot(index: number, count: number, slotCount: number, parent: Instance): PlotParts
	local cfg = GameConfig.World
	local angle = (index - 1) / count * math.pi * 2
	local position = Vector3.new(math.cos(angle) * cfg.PlotRadius, 0, math.sin(angle) * cfg.PlotRadius)
	local origin = CFrame.lookAt(position, Vector3.zero)
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

	local exhibits = Instance.new("Folder")
	exhibits.Name = "Exhibits"
	exhibits.Parent = model

	model.Parent = parent
	return {
		model = model,
		showcases = showcases,
		exhibits = exhibits,
		signLabel = signLabel,
	}
end

return PartBuilder

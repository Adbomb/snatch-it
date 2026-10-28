-- Сборка моделей из кирпичей (D13): модуль модели возвращает список кирпичей, ModelBuilder делает из него Model.
-- Всё Anchored и по умолчанию Plastic (пупырышки даёт MaterialVariant «LegoStuds»). Шаблон собирается один раз и дальше клонируется;
-- в Play шаблоны лежат в ServerStorage.Templates, в предпросмотре — вне DataModel.
-- Зависит от World/Studs.

local ServerScriptService = game:GetService("ServerScriptService")

local Studs = require(ServerScriptService.Server.World.Studs)

export type Brick = {
	size: Vector3,
	cframe: CFrame, -- относительно начала модели
	color: Color3,
	material: Enum.Material?, -- по умолчанию Plastic; другое — только вода, стекло, неон и таблички с текстом
	shape: string?, -- Block | Ball | Cylinder | Wedge | CornerWedge | Truss
	collide: boolean?, -- по умолчанию из опций модели
	shadow: boolean?, -- по умолчанию из опций модели
	transparency: number?,
	name: string?,
	light: { range: number, brightness: number, color: Color3 }?, -- PointLight внутри кирпича
}

-- collide/shadow — значения по умолчанию для всех кирпичей модели. Мелкий декор: оба false.
export type Options = { collide: boolean?, shadow: boolean? }

local ModelBuilder = {}

local templates: { [string]: Model } = {}
local templateFolder: Folder? = nil

-- Кирпич в одну строку: размер, позиция (или CFrame), цвет, остальное — по желанию.
function ModelBuilder.Brick(size: Vector3, at: Vector3 | CFrame, color: Color3, extra: { [string]: any }?): Brick
	local brick: { [string]: any } = {
		size = size,
		cframe = if typeof(at) == "CFrame" then at else CFrame.new(at :: Vector3),
		color = color,
	}
	if extra then
		for key, value in extra do
			brick[key] = value
		end
	end
	return brick :: Brick
end

local function makePart(brick: Brick, opts: Options): BasePart
	local part: BasePart
	if brick.shape == "Truss" then
		local truss = Instance.new("TrussPart")
		truss.Style = Enum.Style.NoSupports
		part = truss
	else
		local p = Instance.new("Part")
		if brick.shape and brick.shape ~= "Block" then
			p.Shape = (Enum.PartType :: any)[brick.shape]
		end
		part = p
	end
	part.Name = brick.name or "Brick"
	part.Anchored = true
	part.Size = brick.size
	part.CFrame = brick.cframe
	part.Color = brick.color
	part.Material = brick.material or Enum.Material.Plastic
	part.Transparency = brick.transparency or 0
	local collide = if brick.collide ~= nil then brick.collide else opts.collide
	local shadow = if brick.shadow ~= nil then brick.shadow else opts.shadow
	part.CanCollide = collide ~= false
	part.CanTouch = false
	part.CastShadow = shadow ~= false
	if not part.CanCollide then
		part.CanQuery = false
	end
	Studs.Apply(part)
	if brick.light then
		local light = Instance.new("PointLight")
		light.Range = brick.light.range
		light.Brightness = brick.light.brightness
		light.Color = brick.light.color
		light.Shadows = false
		light.Parent = part
	end
	return part
end

-- Собирает Model из кирпичей; точка опоры (WorldPivot) — начало координат модели.
function ModelBuilder.Build(name: string, bricks: { Brick }, opts: Options?): Model
	local model = Instance.new("Model")
	model.Name = name
	local options = opts or {}
	for _, brick in bricks do
		makePart(brick, options).Parent = model
	end
	model.WorldPivot = CFrame.new()
	return model
end

-- Куда класть шаблоны: ServerStorage в Play, nil (вне DataModel) в предпросмотре.
function ModelBuilder.SetTemplateParent(parent: Instance?)
	if parent then
		local folder = Instance.new("Folder")
		folder.Name = "Templates"
		folder.Parent = parent
		templateFolder = folder
	else
		templateFolder = nil
	end
	table.clear(templates)
end

-- Копия шаблона key; при первом вызове шаблон собирается функцией build.
function ModelBuilder.FromTemplate(key: string, build: () -> Model): Model
	local template = templates[key]
	if not template then
		template = build()
		template.Name = key
		template.Parent = templateFolder
		templates[key] = template
	end
	return template:Clone()
end

-- Поставить модель в мир: поворот и сдвиг относительно начала координат модели.
function ModelBuilder.Place(model: Model, at: CFrame, parent: Instance): Model
	model:PivotTo(at)
	model.Parent = parent
	return model
end

-- Сколько частей внутри root (для бюджета карты).
function ModelBuilder.CountParts(root: Instance): number
	local count = 0
	for _, descendant in root:GetDescendants() do
		if descendant:IsA("BasePart") then
			count += 1
		end
	end
	return count
end

return ModelBuilder

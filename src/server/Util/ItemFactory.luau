-- Создаёт видимый предмет с подписью над ним (BillboardGui, цвет редкости из UI_KIT.md).
-- Корень предмета — всегда один Part: с ним работают реестр, перенос, витрины и сохранение.
-- Если для предмета есть меш (Config/ItemModels), корень — невидимый хитбокс, а модель из Blender
-- («Visual», MeshPart) приварена к нему внутри. Иначе корень — сам цветной Part нужной формы.
-- Только внешний вид, без логики и состояний. Зависит от AssetService, Config/Items, Config/ItemModels, Config/UITokens.

local AssetService = game:GetService("AssetService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local ItemModels = require(ReplicatedStorage.Shared.Config.ItemModels)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local UITokens = require(ReplicatedStorage.Shared.Config.UITokens)

local LABEL_SIZE = UDim2.fromOffset(200, 36)
local LABEL_GAP = 1.2 -- стадов между верхом предмета и подписью
local LABEL_MAX_DISTANCE = 60
local VISUAL_NAME = "Visual"

local templates: { [string]: MeshPart } = {}

local ItemFactory = {}

-- Загружает меши всех предметов из ItemModels один раз при старте (ждёт сеть), чтобы Create
-- дальше работал без задержек. Ошибка загрузки — предмет останется простым Part.
function ItemFactory.Preload()
	for itemId, model in ItemModels do
		local ok, result = pcall(function()
			return AssetService:CreateMeshPartAsync(Content.fromUri(model.mesh))
		end)
		if ok and result then
			local mesh = result :: MeshPart
			mesh.Name = VISUAL_NAME
			mesh.TextureID = model.texture
			mesh.Material = model.material
			mesh.Size = model.meshSize * model.scale
			mesh.Anchored = false
			mesh.Massless = true
			mesh.CanCollide = false
			mesh.CanQuery = false
			mesh.CanTouch = false
			templates[itemId] = mesh
		else
			warn(("[ItemFactory] Меш %s не загрузился: %s"):format(itemId, tostring(result)))
		end
	end
end

local function addLabel(part: BasePart, def: Items.ItemDef)
	local billboard = Instance.new("BillboardGui")
	billboard.Name = "Label"
	billboard.Size = LABEL_SIZE
	billboard.StudsOffset = Vector3.new(0, part.Size.Y / 2 + LABEL_GAP, 0)
	billboard.MaxDistance = LABEL_MAX_DISTANCE
	billboard.Parent = part

	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.TextColor3 = UITokens.RarityColor(def.rarity)
	label.TextScaled = true
	label.FontFace = UITokens.BodyFont()
	label.Text = def.displayName
	label.Parent = billboard

	local stroke = Instance.new("UIStroke")
	stroke.Color = UITokens.Colors.Ink
	stroke.Thickness = UITokens.Stroke.Text
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
	stroke.Parent = label

	if def.rarity == "Secret" then
		-- У Secret цвет — градиент: текст белый, цвет даёт UIGradient.
		label.TextColor3 = UITokens.Colors.TextOnColor
		local gradient = Instance.new("UIGradient")
		gradient.Color = UITokens.ToColorSequence(UITokens.Rarity.Secret)
		gradient.Parent = label
	end
end

function ItemFactory.Create(itemId: string): Part
	local def = Items[itemId]
	assert(def, "Нет предмета в Config/Items: " .. tostring(itemId))
	local template = templates[itemId]

	local part = Instance.new("Part")
	part.Name = itemId
	part.Anchored = true
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part:SetAttribute("ItemId", itemId)
	if template then
		-- Невидимый хитбокс по размеру модели, модель приварена к нему.
		part.Size = template.Size
		part.Transparency = 1
		part.CastShadow = false
		local visual = template:Clone()
		visual.CFrame = part.CFrame
		visual.Parent = part
		-- Weld (не WeldConstraint): жёстко держит модель в центре корня, даже когда закреплённый
		-- корень переставляют через CFrame (WeldConstraint в этом случае модель не тянул).
		local weld = Instance.new("Weld")
		weld.Part0 = part
		weld.Part1 = visual
		weld.C0 = CFrame.identity
		weld.C1 = CFrame.identity
		weld.Parent = visual
	else
		part.Shape = (Enum.PartType :: any)[def.shape] or Enum.PartType.Block
		part.Size = def.size
		part.Color = def.color
		part.Material = def.material or Enum.Material.Plastic
	end
	addLabel(part, def)
	return part
end

-- Прозрачность видимой части предмета (мигание D10): у модели — меш, у простого Part — сам Part.
function ItemFactory.SetVisualTransparency(part: BasePart, transparency: number)
	local visual = part:FindFirstChild(VISUAL_NAME)
	if visual and visual:IsA("BasePart") then
		visual.Transparency = transparency
	else
		part.Transparency = transparency
	end
end

return ItemFactory

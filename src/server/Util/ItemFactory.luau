-- Создаёт видимый предмет с подписью над ним (BillboardGui, D45): название цветом редкости и строка «Редкость ·
-- +доход/сек», ширина — по длине названия (UITokens.ItemLabel); раскладку на экране делает клиент
-- (ItemLabelController).
-- Корень предмета — всегда один Part: с ним работают реестр, перенос, витрины и сохранение.
-- Если для предмета загружен меш (Config/ItemModels), корень — невидимый хитбокс по габаритам модели, а модель из
-- Blender («Visual», MeshPart с SurfaceAppearance D39) приварена к нему внутри. Иначе корень — сам цветной Part
-- нужной формы (заготовка до импорта). Карты SurfaceAppearance игровой скрипт задать не может (права плагина) —
-- копируется шаблон из Server/Looks (его создаёт Rojo, scripts/make_looks.py). Только внешний вид, без логики.
-- Зависит от AssetService, Config/Items, Config/ItemModels, Config/Rarities, Config/UITokens, Shared/NumberFormat,
-- Server/Looks.

local AssetService = game:GetService("AssetService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local ItemModels = require(ReplicatedStorage.Shared.Config.ItemModels)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local NumberFormat = require(ReplicatedStorage.Shared.NumberFormat)
local Rarities = require(ReplicatedStorage.Shared.Config.Rarities)
local UITokens = require(ReplicatedStorage.Shared.Config.UITokens)
local Looks = ServerScriptService.Server.Looks

local VISUAL_NAME = "Visual"

local templates: { [string]: MeshPart } = {}

local ItemFactory = {}

-- Меш предмета с картами D39 по описанию из ItemModels (ждёт сеть). nil — меша нет или он не загрузился.
local function loadModel(itemId: string): MeshPart?
	local model = ItemModels.Models[itemId]
	if not model or not model.mesh then
		return nil
	end
	local ok, result = pcall(function()
		return AssetService:CreateMeshPartAsync(Content.fromUri(model.mesh :: string))
	end)
	if not ok or not result then
		warn(("[ItemFactory] Меш %s не загрузился: %s"):format(itemId, tostring(result)))
		return nil
	end
	local mesh = result :: MeshPart
	mesh.Name = VISUAL_NAME
	mesh.Size = model.size
	mesh.Material = Enum.Material.SmoothPlastic -- цвет, кольца и тени — в SurfaceAppearance
	mesh.Anchored = false
	mesh.Massless = true
	mesh.CanCollide = false
	mesh.CanQuery = false
	mesh.CanTouch = false
	local look = Looks:FindFirstChild(itemId)
	if look then
		look:Clone().Parent = mesh
	else
		warn(("[ItemFactory] Нет шаблона карт Looks/%s (scripts/make_looks.py)"):format(itemId))
	end
	mesh:SetAttribute("Turn", model.turn or 0)
	return mesh
end

-- Загружает меши всех предметов один раз при старте (параллельно, ждёт сеть), чтобы Create дальше работал без
-- задержек. Ошибка загрузки — предмет останется заготовкой.
function ItemFactory.Preload()
	local pending = 0
	for itemId in ItemModels.Models do
		pending += 1
		task.spawn(function()
			templates[itemId] = loadModel(itemId)
			pending -= 1
		end)
	end
	while pending > 0 do
		task.wait()
	end
end

-- Есть ли у предмета загруженная модель (для тестов и проверок).
function ItemFactory.HasModel(itemId: string): boolean
	return templates[itemId] ~= nil
end

-- Строка подписи: размер текста в пределах limits (мин., макс.), белая обводка цвета Ink.
local function labelText(name: string, size: UDim2, position: UDim2, limits: Vector2, parent: Instance): TextLabel
	local label = Instance.new("TextLabel")
	label.Name = name
	label.Size = size
	label.Position = position
	label.BackgroundTransparency = 1
	label.TextScaled = true
	label.FontFace = UITokens.BodyFont()
	label.Parent = parent
	local constraint = Instance.new("UITextSizeConstraint")
	constraint.MinTextSize = limits.X
	constraint.MaxTextSize = limits.Y
	constraint.Parent = label
	local stroke = Instance.new("UIStroke")
	stroke.Color = UITokens.Colors.Ink
	stroke.Thickness = UITokens.Stroke.Text
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
	stroke.Parent = label
	return label
end

-- Подпись над предметом: название (Name) и «Редкость · +доход/сек» (Info). Атрибуты BaseWidth, BaseHeight и BaseLift —
-- исходные размер и подъём: от них клиент считает масштаб под экран и подъём над соседними подписями.
local function addLabel(part: BasePart, def: Items.ItemDef)
	local cfg = UITokens.ItemLabel
	local width = math.clamp((utf8.len(def.displayName) or 0) * cfg.CharWidth + cfg.Padding, cfg.MinWidth, cfg.MaxWidth)
	local lift = part.Size.Y / 2 + cfg.Gap
	local billboard = Instance.new("BillboardGui")
	billboard.Name = "Label"
	billboard.Size = UDim2.fromOffset(width, cfg.Height)
	billboard.StudsOffset = Vector3.new(0, lift, 0)
	billboard.MaxDistance = cfg.MaxDistance
	billboard:SetAttribute("BaseWidth", width)
	billboard:SetAttribute("BaseHeight", cfg.Height)
	billboard:SetAttribute("BaseLift", lift)
	billboard.Parent = part

	local color = UITokens.RarityColor(def.rarity)
	local name = labelText("Name", UDim2.fromScale(1, cfg.NameShare), UDim2.new(), cfg.NameTextSize, billboard)
	name.TextColor3 = color
	name.Text = def.displayName
	if def.rarity == "Secret" then
		-- У Secret цвет — градиент: текст белый, цвет даёт UIGradient.
		name.TextColor3 = UITokens.Colors.TextOnColor
		local gradient = Instance.new("UIGradient")
		gradient.Color = UITokens.ToColorSequence(UITokens.Rarity.Secret)
		gradient.Parent = name
	end

	local share = cfg.NameShare
	local infoSize, infoPosition = UDim2.fromScale(1, 1 - share), UDim2.fromScale(0, share)
	local info = labelText("Info", infoSize, infoPosition, cfg.InfoTextSize, billboard)
	info.TextColor3 = UITokens.Colors.TextOnColor
	info.RichText = true
	local rarity = ('<font color="#%s">%s</font>'):format(color:ToHex(), Rarities.Names[def.rarity] or def.rarity)
	local income = def.income or 0
	info.Text = if income > 0
		then ('%s · <font color="#%s">+%s/сек</font>'):format(rarity, cfg.Income:ToHex(), NumberFormat.Short(income))
		else rarity
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
		local turn = CFrame.Angles(0, math.rad(template:GetAttribute("Turn") or 0), 0)
		visual.CFrame = part.CFrame * turn
		visual.Parent = part
		-- Weld (не WeldConstraint): жёстко держит модель в центре корня, даже когда закреплённый
		-- корень переставляют через CFrame (WeldConstraint в этом случае модель не тянул).
		local weld = Instance.new("Weld")
		weld.Part0 = part
		weld.Part1 = visual
		weld.C0 = turn
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

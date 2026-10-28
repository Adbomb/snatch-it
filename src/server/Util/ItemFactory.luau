-- Создаёт видимый предмет: Part нужной формы, цвета и размера с подписью над ним (BillboardGui).
-- Цвет подписи — цвет редкости из UI_KIT.md. Только внешний вид, без логики и состояний.
-- Зависит от Config/Items, Config/UITokens.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Items = require(ReplicatedStorage.Shared.Config.Items)
local UITokens = require(ReplicatedStorage.Shared.Config.UITokens)

local LABEL_SIZE = UDim2.fromOffset(200, 36)
local LABEL_GAP = 1.2 -- стадов между верхом предмета и подписью
local LABEL_MAX_DISTANCE = 60

local ItemFactory = {}

function ItemFactory.Create(itemId: string): Part
	local def = Items[itemId]
	assert(def, "Нет предмета в Config/Items: " .. tostring(itemId))

	local part = Instance.new("Part")
	part.Name = itemId
	part.Shape = (Enum.PartType :: any)[def.shape] or Enum.PartType.Block
	part.Size = def.size
	part.Color = def.color
	part.Material = def.material or Enum.Material.Plastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Anchored = true
	part:SetAttribute("ItemId", itemId)

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

	return part
end

return ItemFactory

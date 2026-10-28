-- Создаёт видимый предмет: цветной Part нужного размера с подписью над ним (BillboardGui).
-- Только внешний вид, без логики и состояний. Зависит от Config/Items.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Items = require(ReplicatedStorage.Shared.Config.Items)

local ItemFactory = {}

function ItemFactory.Create(itemId: string): Part
	local def = Items[itemId]
	assert(def, "Нет предмета в Config/Items: " .. tostring(itemId))

	local part = Instance.new("Part")
	part.Name = itemId
	part.Size = def.size
	part.Color = def.color
	part.Material = Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Anchored = true
	part:SetAttribute("ItemId", itemId)

	local billboard = Instance.new("BillboardGui")
	billboard.Size = UDim2.fromOffset(200, 36)
	billboard.StudsOffset = Vector3.new(0, def.size.Y / 2 + 1.2, 0)
	billboard.MaxDistance = 60
	billboard.Parent = part

	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextStrokeTransparency = 0
	label.TextScaled = true
	label.Font = Enum.Font.GothamBold
	label.Text = def.displayName
	label.Parent = billboard

	return part
end

return ItemFactory

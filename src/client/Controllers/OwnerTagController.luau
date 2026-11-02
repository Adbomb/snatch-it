-- Владелец музея (D41): над входом в каждый занятый музей — круглое фото игрока (аватар-голова) в белом кольце и его
-- ник, вместо прежней вывески «МУЗЕЙ <имя>». Подпись в мире (BillboardGui в стадах — с расстоянием уменьшается, как
-- предмет мира), у точки OwnerTag пола участка; у свободного музея подписи нет. Данные — атрибуты участка
-- OwnerUserId и OwnerName (PlotService). Фото — rbxthumb (без запросов к серверу). Зависит от Config/UITokens.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))

local player = Players.LocalPlayer
local CFG = UITokens.OwnerTag
local FONT = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
local PHOTO = 0.55 -- доля ширины подписи под фото
local RING = 0.06 -- толщина кольца, доля ширины фото

local OwnerTagController = {}

local function circle(parent: Instance, name: string, size: UDim2, color: Color3): Frame
	local frame = Instance.new("Frame")
	frame.Name = name
	frame.BackgroundColor3 = color
	frame.BorderSizePixel = 0
	frame.AnchorPoint = Vector2.new(0.5, 0.5)
	frame.Position = UDim2.fromScale(0.5, 0.5)
	frame.Size = size
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0.5, 0)
	corner.Parent = frame
	frame.Parent = parent
	return frame
end

-- Подпись участка plot у точки anchor: строится один раз, содержимое — по атрибутам.
local function build(plot: Model, anchor: Attachment)
	local gui = Instance.new("BillboardGui")
	gui.Name = "OwnerTag_" .. plot.Name
	gui.Adornee = anchor
	gui.Size = UDim2.fromScale(CFG.Size.X, CFG.Size.Y)
	gui.LightInfluence = 0
	gui.MaxDistance = CFG.MaxDistance
	gui.ResetOnSpawn = false

	-- Фото: тёмный ободок → белое кольцо → круглая картинка (кольца — круги разного размера, они масштабируются вместе с
	-- подписью, в отличие от UIStroke в пикселях).
	local holder = Instance.new("Frame")
	holder.Name = "Photo"
	holder.BackgroundTransparency = 1
	holder.AnchorPoint = Vector2.new(0.5, 0)
	holder.Position = UDim2.fromScale(0.5, 0)
	holder.Size = UDim2.fromScale(PHOTO, PHOTO * CFG.Size.X / CFG.Size.Y)
	holder.Parent = gui
	local outer = circle(holder, "Outline", UDim2.fromScale(1, 1), CFG.RingDark)
	local ring = circle(outer, "Ring", UDim2.fromScale(1 - RING, 1 - RING), CFG.Ring)
	local photo = circle(ring, "Back", UDim2.fromScale(1 - RING * 2, 1 - RING * 2), Color3.fromHex("CFE3F5"))
	local image = Instance.new("ImageLabel")
	image.Name = "Image"
	image.BackgroundTransparency = 1
	image.Size = UDim2.fromScale(1, 1)
	image.ScaleType = Enum.ScaleType.Crop
	image.Parent = photo
	local imageCorner = Instance.new("UICorner")
	imageCorner.CornerRadius = UDim.new(0.5, 0)
	imageCorner.Parent = image

	local name = Instance.new("TextLabel")
	name.Name = "Nick" -- не «Name»: так называется свойство, gui.Name вернул бы строку
	name.BackgroundTransparency = 1
	name.AnchorPoint = Vector2.new(0.5, 1)
	name.Position = UDim2.fromScale(0.5, 1)
	name.Size = UDim2.fromScale(1, 1 - PHOTO * CFG.Size.X / CFG.Size.Y - 0.03)
	name.FontFace = FONT
	name.TextScaled = true
	name.TextColor3 = Color3.new(1, 1, 1)
	name.Parent = gui
	local stroke = Instance.new("UIStroke")
	stroke.Color = CFG.RingDark
	stroke.Thickness = 2.5
	stroke.Parent = name

	local function refresh()
		local userId = plot:GetAttribute("OwnerUserId")
		local owned = type(userId) == "number" and userId ~= 0
		gui.Enabled = owned
		if owned then
			image.Image = ("rbxthumb://type=AvatarHeadShot&id=%d&w=150&h=150"):format(math.abs(userId))
			name.Text = tostring(plot:GetAttribute("OwnerName") or "")
		end
	end
	plot:GetAttributeChangedSignal("OwnerUserId"):Connect(refresh)
	plot:GetAttributeChangedSignal("OwnerName"):Connect(refresh)
	refresh()
	gui.Parent = player:WaitForChild("PlayerGui")
end

local function track(plot: Instance)
	if not plot:IsA("Model") then
		return
	end
	local floor = plot:WaitForChild("Floor", 30)
	local anchor = floor and floor:WaitForChild("OwnerTag", 30)
	if anchor and anchor:IsA("Attachment") then
		build(plot, anchor)
	end
end

function OwnerTagController.Init()
	task.spawn(function()
		local plots = workspace:WaitForChild("World"):WaitForChild("Plots")
		plots.ChildAdded:Connect(function(plot)
			task.spawn(track, plot)
		end)
		for _, plot in plots:GetChildren() do
			task.spawn(track, plot)
		end
	end)
end

return OwnerTagController

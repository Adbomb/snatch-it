-- Окно хранилища (UI_KIT.md): карточки предметов, по нажатию «Выставить» отправляет серверу (uid, витрина).
-- Список приходит с сервера (StorageChanged); клиент ничего не решает сам.
-- Зависит от Remotes, Items, GameConfig, UIKit, UITokens.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local Items = require(Shared:WaitForChild("Config"):WaitForChild("Items"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UIKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UIKit"))

type StoredItem = { uid: string, itemId: string }

local StorageController = {}

local gui: ScreenGui
local stored: { StoredItem } = {}
local window: Frame?
local targetSlot: number?

local function close()
	if window then
		window:Destroy()
	end
	window = nil
	targetSlot = nil
end

local function buildCard(item: StoredItem, parent: Instance, order: number)
	local def = Items[item.itemId]
	if not def then
		return
	end
	local _, body = UIKit.Panel({ card = true, parent = parent, layoutOrder = order })
	local layout = Instance.new("UIListLayout")
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.Padding = UDim.new(0, UITokens.Spacing.Small)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = body

	UIKit.Text({
		text = def.displayName,
		onLight = true,
		textSize = UITokens.TextSize.Body,
		parent = body,
		size = UDim2.fromScale(1, 0.34),
		layoutOrder = 1,
	})
	UIKit.RarityTag(def.rarity, { parent = body, size = UDim2.fromScale(0.9, 0.2), layoutOrder = 2 })
	local button = UIKit.Button({
		kind = "Go",
		text = "Выставить",
		parent = body,
		size = UDim2.fromScale(1, 0.3),
		layoutOrder = 3,
	})
	button:OnClick(function()
		local slot = targetSlot
		if slot then
			Remotes.Get(Remotes.Names.DisplayFromStorage):FireServer(item.uid, slot)
		end
		close()
	end)
end

local function build(slot: number)
	close()
	targetSlot = slot
	local cfg = UITokens.Layout.StorageWindow
	local title = ("Хранилище (%d/%d) → витрина %d"):format(#stored, GameConfig.Museum.StorageCapacity, slot)
	local panel, body = UIKit.Panel({
		title = title,
		headerHeight = cfg.headerHeight,
		parent = gui,
		size = cfg.size,
		anchorPoint = Vector2.new(0.5, 0.5),
		position = UDim2.fromScale(0.5, 0.5),
	})
	UIKit.Constrain(panel, { minSize = cfg.minSize, maxSize = cfg.maxSize })
	window = panel

	local footerHeight = UITokens.Layout.MinTouchButton.Y + UITokens.Button.Shadow
	local list = Instance.new("ScrollingFrame")
	list.Name = "List"
	list.BackgroundTransparency = 1
	list.BorderSizePixel = 0
	list.Size = UDim2.new(1, 0, 1, -(footerHeight + UITokens.Spacing.Medium))
	list.AutomaticCanvasSize = Enum.AutomaticSize.Y
	list.CanvasSize = UDim2.new()
	list.ScrollBarImageColor3 = UITokens.Colors.Ink
	list.Parent = body
	local grid = Instance.new("UIGridLayout")
	grid.CellSize = UDim2.fromOffset(cfg.cardSize.X, cfg.cardSize.Y)
	grid.CellPadding = UDim2.fromOffset(UITokens.Spacing.Medium, UITokens.Spacing.Medium + UITokens.Button.Shadow)
	grid.HorizontalAlignment = Enum.HorizontalAlignment.Center
	grid.SortOrder = Enum.SortOrder.LayoutOrder
	grid.Parent = list
	UIKit.Padding(list, UITokens.Spacing.Small)

	if #stored == 0 then
		UIKit.Text({ text = "Хранилище пусто", onLight = true, parent = list })
	end
	for order, item in stored do
		buildCard(item, list, order)
	end

	local closeButton = UIKit.Button({
		kind = "Stop",
		text = "Закрыть",
		parent = body,
		anchorPoint = Vector2.new(0.5, 1),
		position = UDim2.new(0.5, 0, 1, -UITokens.Button.Shadow),
		size = UDim2.new(0.4, 0, 0, UITokens.Layout.MinTouchButton.Y),
	})
	UIKit.Constrain(closeButton.Instance, { minSize = UITokens.Layout.MinTouchButton })
	closeButton:OnClick(close)
end

-- Открыть окно выбора для своей пустой витрины slot.
function StorageController.Open(slot: number)
	build(slot)
end

function StorageController.Init()
	gui = UIKit.ScreenGui("Storage", 5)
	Remotes.Get(Remotes.Names.StorageChanged).OnClientEvent:Connect(function(list: { StoredItem })
		stored = list
		if window and targetSlot then
			build(targetSlot)
		end
	end)
end

return StorageController

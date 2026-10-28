-- Показывает короткие сообщения сервера уведомлениями-Toast в колонке справа (UI_KIT.md).
-- Новое сообщение выезжает справа, через lifetime секунд уезжает обратно. Зависит от Remotes, UIKit, UITokens.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UIKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UIKit"))

local SLIDE_INFO = TweenInfo.new(UITokens.Motion.Slide, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local HIDDEN = UDim2.fromScale(1.2, 0) -- за правым краем колонки

local NotifyController = {}

local column: Frame
local order = 0

local function hide(slot: Frame, toast: Frame)
	if not slot.Parent then
		return
	end
	local tween = TweenService:Create(toast, SLIDE_INFO, { Position = HIDDEN })
	tween.Completed:Once(function()
		slot:Destroy()
	end)
	tween:Play()
end

-- Показать сообщение. kind: Info (по умолчанию), Stop (отказ), Go (успех).
function NotifyController.Show(text: string, kind: UIKit.ButtonKind?)
	local cfg = UITokens.Layout.Toasts
	order += 1

	local slot = Instance.new("Frame")
	slot.Name = "ToastSlot"
	slot.BackgroundTransparency = 1
	slot.Size = UDim2.new(1, 0, 0, cfg.itemHeight)
	slot.LayoutOrder = order
	slot.Parent = column

	local toast = UIKit.Toast({ text = text, kind = kind, parent = slot, position = HIDDEN })
	TweenService:Create(toast, SLIDE_INFO, { Position = UDim2.fromScale(0, 0) }):Play()
	task.delay(cfg.lifetime, hide, slot, toast)

	local slots = {}
	for _, child in column:GetChildren() do
		if child:IsA("Frame") then
			table.insert(slots, child)
		end
	end
	table.sort(slots, function(a, b)
		return a.LayoutOrder < b.LayoutOrder
	end)
	for i = 1, #slots - cfg.maxCount do
		slots[i]:Destroy()
	end
end

function NotifyController.Init()
	local cfg = UITokens.Layout.Toasts
	local gui = UIKit.ScreenGui("Toasts", 10)
	column = Instance.new("Frame")
	column.Name = "Column"
	column.BackgroundTransparency = 1
	column.AnchorPoint = Vector2.new(1, 0)
	column.Position = cfg.position
	column.Size = cfg.size
	column.Parent = gui
	UIKit.Constrain(column, {
		minSize = Vector2.new(cfg.minWidth, 0),
		maxSize = Vector2.new(cfg.maxWidth, math.huge),
	})
	local layout = Instance.new("UIListLayout")
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Padding = UDim.new(0, UITokens.Spacing.Medium)
	layout.Parent = column

	Remotes.Get(Remotes.Names.Notify).OnClientEvent:Connect(function(text: string, kind: string?)
		NotifyController.Show(text, kind :: any)
	end)
end

return NotifyController

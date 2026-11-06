-- Показывает короткие сообщения сервера уведомлениями-Toast в колонке справа (UI_KIT.md): левее колонки меню HUD v2
-- и ниже таймера (D49: не перекрывают «Инвентарь», «Защиту» и таймер). Сообщений не больше, чем помещается в высоту
-- колонки (на телефоне — 2), а на узком телефоне, где колонка по ширине заходит на «Бросить», — только до верха этой
-- кнопки. Новое сообщение выезжает справа, через lifetime секунд уезжает обратно.
-- Зависит от Remotes, UIKit, UITokens, UI/HudLayout, CarryHud (кнопка «Бросить» — CarryController).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UIKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UIKit"))
local HudLayout = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudLayout"))

local SLIDE_INFO = TweenInfo.new(UITokens.Motion.Slide, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local HIDDEN = UDim2.fromScale(1.2, 0) -- за правым краем колонки

local NotifyController = {}

local column: Frame
local order = 0

-- Сколько уведомлений помещается: по высоте колонки; если колонка по ширине заходит на «Бросить» (узкий телефон) —
-- только до верха кнопки (и пока её не видно: она появится с добычей в руках).
local function capacity(): number
	local cfg = UITokens.Layout.Toasts
	local pad = UITokens.Spacing.Medium
	local top = column.AbsolutePosition.Y
	local bottom = top + column.AbsoluteSize.Y
	local playerGui = Players.LocalPlayer:FindFirstChildOfClass("PlayerGui")
	local carry = playerGui and playerGui:FindFirstChild("CarryHud")
	local drop = carry and carry:FindFirstChild("Button")
	if drop and drop:IsA("GuiObject") and column.AbsolutePosition.X < drop.AbsolutePosition.X + drop.AbsoluteSize.X then
		bottom = math.min(bottom, drop.AbsolutePosition.Y - pad)
	end
	return math.max(1, math.floor((bottom - top + pad) / (cfg.itemHeight + pad)))
end

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
	for i = 1, #slots - math.min(cfg.maxCount, capacity()) do
		slots[i]:Destroy()
	end
end

-- Правый край колонки — левее колонки меню, верх — под таймером (при текущем масштабе экрана).
local function placeColumn()
	local cfg = UITokens.Layout.Toasts
	column.Position = UDim2.new(1, -HudLayout.LeftOfMenu(cfg.menuGap), 0, HudLayout.BelowTimer(cfg.timerGap))
end

function NotifyController.Init()
	local cfg = UITokens.Layout.Toasts
	local gui = UIKit.ScreenGui("Toasts", 10)
	column = Instance.new("Frame")
	column.Name = "Column"
	column.BackgroundTransparency = 1
	column.AnchorPoint = Vector2.new(1, 0)
	column.Size = cfg.size
	column.Parent = gui
	HudLayout.Track(placeColumn)
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

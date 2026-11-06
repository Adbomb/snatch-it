-- Показывает короткие сообщения сервера уведомлениями-Toast в колонке справа (UI_KIT.md): левее колонки меню HUD v2
-- и ниже таймера (D49: не перекрывают «Инвентарь», «Защиту» и таймер). Сообщений не больше, чем помещается в высоту
-- колонки (на телефоне — 2), а на узком телефоне, где колонка по ширине заходит на «Бросить», — только до верха этой
-- кнопки. На узком телефоне, где колонка заходит под плашку входа в зону, на время показа плашки уведомления
-- спрятаны; при открытом окне меню — справа от окна поверх всего, а где места нет (телефон) — ждут закрытия окна
-- (D50). Новое сообщение выезжает справа, через lifetime секунд уезжает обратно.
-- Зависит от Remotes, UIKit, UITokens, UI/HudLayout, CarryHud (кнопка «Бросить» — CarryController), LevelBanner
-- (плашка зоны — ZoneController).

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

local banner: GuiObject? = nil -- плашка входа в зону (ZoneController)

-- Открытое окно меню Stud-UI (видна рамка «Fenetre»: при закрытии StudMotion прячет только её) или nil.
local function openWindow(): GuiObject?
	local playerGui = Players.LocalPlayer:FindFirstChildOfClass("PlayerGui")
	for _, gui in if playerGui then playerGui:GetChildren() else {} do
		local frame = gui:IsA("ScreenGui") and gui.Enabled and gui:FindFirstChild("Fenetre")
		if frame and frame:IsA("GuiObject") and frame.Visible then
			return frame
		end
	end
	return nil
end

-- Правый край колонки — левее колонки меню, верх — под таймером (при текущем масштабе экрана). Пока видна плашка
-- входа в зону (≈2 с), а колонка по ширине заходит под неё (узкий телефон, D50), уведомления спрятаны и потом
-- возвращаются: ниже плашки места нет — там «Бросить», «Ты несёшь…» и прыжок. Пока открыто окно меню (колонка меню
-- спрятана) — в полосе справа от окна, а если она уже minWidth (телефон) — спрятаны до закрытия окна (D50).
local function placeColumn()
	local cfg = UITokens.Layout.Toasts
	local viewport = workspace.CurrentCamera.ViewportSize
	local window = openWindow()
	if window then
		local free = viewport.X - window.AbsolutePosition.X - window.AbsoluteSize.X - 2 * cfg.menuGap
		column.Size = UDim2.new(0, math.min(free, cfg.maxWidth), cfg.size.Y.Scale, 0)
		column.Position = UDim2.new(1, -cfg.menuGap, 0, HudLayout.BelowTimer(cfg.timerGap))
		column.Visible = free >= cfg.minWidth
		return
	end
	local right = HudLayout.LeftOfMenu(cfg.menuGap)
	local width = math.clamp(cfg.size.X.Scale * viewport.X, cfg.minWidth, cfg.maxWidth)
	column.Size = cfg.size
	column.Position = UDim2.new(1, -right, 0, HudLayout.BelowTimer(cfg.timerGap))
	column.Visible = not (
		banner ~= nil
		and banner.Visible
		and viewport.X - right - width < viewport.X / 2 + HudLayout.BannerHalfWidth()
	)
end

function NotifyController.Init()
	local cfg = UITokens.Layout.Toasts
	-- поверх окон меню (12–13): окна оставляют уведомления видимыми, под окном они читались наполовину (D50)
	local gui = UIKit.ScreenGui("Toasts", UITokens.Layout.Toasts.displayOrder)
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
	task.spawn(function()
		local zoneGui = Players.LocalPlayer:WaitForChild("PlayerGui"):WaitForChild("LevelBanner", 30)
		local found = zoneGui and zoneGui:WaitForChild("LevelBanner", 10)
		if found and found:IsA("GuiObject") then
			banner = found
			found:GetPropertyChangedSignal("Visible"):Connect(placeColumn)
		end
	end)
	-- окна меню открываются и закрываются в своих контроллерах: проверять несколько раз в секунду (дёшево)
	task.spawn(function()
		while true do
			task.wait(cfg.windowCheck)
			placeColumn()
		end
	end)
end

return NotifyController

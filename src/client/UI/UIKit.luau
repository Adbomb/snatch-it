-- Фабрики интерфейса по UI_KIT.md: Button, Panel, Pill, RarityTag, Toast и подписи.
-- Все цвета, скругления, обводки и шрифты берутся из Config/UITokens; контроллеры чисел не задают.
-- Зависит от UITokens, Rarities, TweenService.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Rarities = require(Shared:WaitForChild("Config"):WaitForChild("Rarities"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))

local Colors = UITokens.Colors

export type ButtonKind = "Go" | "Info" | "Stop" | "Coin" | "Disabled"

export type Placement = {
	parent: Instance?,
	size: UDim2?,
	position: UDim2?,
	anchorPoint: Vector2?,
	layoutOrder: number?,
}

export type ButtonHandle = {
	Instance: Frame,
	SetText: (self: ButtonHandle, text: string) -> (),
	SetKind: (self: ButtonHandle, kind: ButtonKind) -> (),
	OnClick: (self: ButtonHandle, callback: () -> ()) -> (),
}

local UIKit = {}

local function place(object: GuiObject, props: Placement)
	object.Size = props.size or object.Size
	object.Position = props.position or object.Position
	object.AnchorPoint = props.anchorPoint or object.AnchorPoint
	object.LayoutOrder = props.layoutOrder or 0
	object.Parent = props.parent
end

local function blank(name: string): Frame
	local frame = Instance.new("Frame")
	frame.Name = name
	frame.BackgroundTransparency = 1
	frame.BorderSizePixel = 0
	frame.Size = UDim2.fromScale(1, 1)
	return frame
end

local function filled(name: string, color: Color3): Frame
	local frame = blank(name)
	frame.BackgroundTransparency = 0
	frame.BackgroundColor3 = color
	return frame
end

function UIKit.Corner(parent: Instance, radius: UDim)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = radius
	corner.Parent = parent
end

function UIKit.Border(parent: Instance)
	local stroke = Instance.new("UIStroke")
	stroke.Color = Colors.Ink
	stroke.Thickness = UITokens.Stroke.Border
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	stroke.Parent = parent
end

function UIKit.Gradient(parent: Instance, g: UITokens.Gradient)
	local gradient = Instance.new("UIGradient")
	gradient.Color = UITokens.ToColorSequence(g)
	gradient.Rotation = 90 -- сверху вниз
	gradient.Parent = parent
end

function UIKit.Padding(parent: Instance, pixels: number)
	local padding = Instance.new("UIPadding")
	local p = UDim.new(0, pixels)
	padding.PaddingTop, padding.PaddingBottom, padding.PaddingLeft, padding.PaddingRight = p, p, p, p
	padding.Parent = parent
end

-- Ограничения размера: пропорции и мин/макс в пикселях (UI_KIT.md: Scale + UIAspectRatioConstraint).
function UIKit.Constrain(object: GuiObject, opts: { aspect: number?, minSize: Vector2?, maxSize: Vector2? })
	if opts.aspect then
		local ratio = Instance.new("UIAspectRatioConstraint")
		ratio.AspectRatio = opts.aspect
		ratio.Parent = object
	end
	if opts.minSize or opts.maxSize then
		local limits = Instance.new("UISizeConstraint")
		limits.MinSize = opts.minSize or Vector2.zero
		limits.MaxSize = opts.maxSize or Vector2.new(math.huge, math.huge)
		limits.Parent = object
	end
end

-- Подпись. onLight = тёмный текст без обводки (на светлой панели), иначе белый с обводкой Ink.
function UIKit.Text(
	props: Placement & {
		text: string,
		textSize: number?,
		weight: Enum.FontWeight?,
		onLight: boolean?,
		color: Color3?,
		alignX: Enum.TextXAlignment?,
	}
): TextLabel
	local label = Instance.new("TextLabel")
	label.Name = "Text"
	label.BackgroundTransparency = 1
	label.Size = UDim2.fromScale(1, 1)
	label.FontFace = UITokens.BodyFont(props.weight)
	label.Text = props.text
	label.TextScaled = true
	label.TextWrapped = true
	label.TextXAlignment = props.alignX or Enum.TextXAlignment.Center
	label.TextColor3 = props.color or (if props.onLight then Colors.Ink else Colors.TextOnColor)
	local sizeLimit = Instance.new("UITextSizeConstraint")
	sizeLimit.MaxTextSize = props.textSize or UITokens.TextSize.Body
	sizeLimit.Parent = label
	if not props.onLight then
		local stroke = Instance.new("UIStroke")
		stroke.Color = Colors.Ink
		stroke.Thickness = UITokens.Stroke.Text
		stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
		stroke.Parent = label
	end
	place(label, props)
	return label
end

-- Кнопка: градиент, нижняя тёмная полоса, жёсткая тень; при нажатии опускается, тень исчезает.
function UIKit.Button(props: Placement & { kind: ButtonKind, text: string, textSize: number? }): ButtonHandle
	local tokens = UITokens.Button
	local holder = blank("Button")

	local shadow = filled("Shadow", Colors.Ink)
	shadow.Position = UDim2.fromOffset(0, tokens.Shadow)
	UIKit.Corner(shadow, UITokens.Corner.Button)
	shadow.Parent = holder

	local content = blank("Content")
	content.Parent = holder

	local base = filled("Base", Colors.Ink)
	UIKit.Corner(base, UITokens.Corner.Button)
	UIKit.Border(base)
	base.Parent = content

	local face = filled("Face", Colors.TextOnColor)
	face.Size = UDim2.new(1, 0, 1, -tokens.DarkBar)
	UIKit.Corner(face, UITokens.Corner.Button)
	face.Parent = base
	local faceGradient = Instance.new("UIGradient")
	faceGradient.Rotation = 90
	faceGradient.Parent = face

	local label = UIKit.Text({
		text = props.text,
		textSize = props.textSize or UITokens.TextSize.Body,
		parent = face,
	})
	UIKit.Padding(label, UITokens.Spacing.Small)

	local hit = Instance.new("TextButton")
	hit.Name = "Hit"
	hit.BackgroundTransparency = 1
	hit.Size = UDim2.fromScale(1, 1)
	hit.Text = ""
	hit.AutoButtonColor = false
	hit.ZIndex = 10
	hit.Parent = holder

	local handle = { Instance = holder } :: any
	local kind: ButtonKind = props.kind
	local callbacks: { () -> () } = {}

	function handle:SetKind(newKind: ButtonKind)
		kind = newKind
		local g = UITokens.Gradients[newKind]
		faceGradient.Color = UITokens.ToColorSequence(g)
		base.BackgroundColor3 = g.bottom:Lerp(Colors.Ink, tokens.DarkBarShade)
	end
	function handle:SetText(text: string)
		label.Text = text
	end
	function handle:OnClick(callback: () -> ())
		table.insert(callbacks, callback)
	end
	handle:SetKind(kind)

	local pressInfo = TweenInfo.new(tokens.PressTime)
	local function setPressed(pressed: boolean)
		shadow.Visible = not pressed
		TweenService:Create(content, pressInfo, {
			Position = UDim2.fromOffset(0, if pressed then tokens.PressOffset else 0),
		}):Play()
	end
	hit.MouseButton1Down:Connect(function()
		if kind ~= "Disabled" then
			setPressed(true)
		end
	end)
	hit.MouseButton1Up:Connect(function()
		setPressed(false)
	end)
	hit.MouseLeave:Connect(function()
		setPressed(false)
	end)
	hit.Activated:Connect(function()
		if kind == "Disabled" then
			return
		end
		for _, callback in callbacks do
			task.spawn(callback)
		end
	end)

	place(holder, props)
	return handle :: ButtonHandle
end

-- Окно или карточка: светлый фон, обводка, тень; с title — синяя шапка.
-- Возвращает (окно, область содержимого).
function UIKit.Panel(
	props: Placement & { title: string?, headerHeight: number?, card: boolean? }
): (Frame, Frame)
	local radius = if props.card then UITokens.Corner.Card else UITokens.Corner.Window
	local holder = blank(if props.card then "Card" else "Panel")

	local shadow = filled("Shadow", Colors.Ink)
	shadow.Position = UDim2.fromOffset(0, UITokens.Button.Shadow)
	UIKit.Corner(shadow, radius)
	shadow.Parent = holder

	local main = filled("Main", Colors.Panel)
	UIKit.Corner(main, radius)
	UIKit.Border(main)
	main.Parent = holder

	local body = blank("Body")
	body.Parent = main

	if props.title then
		local headerHeight = props.headerHeight or UITokens.Layout.StorageWindow.headerHeight
		local header = filled("Header", Colors.Header)
		header.Size = UDim2.new(1, 0, 0, headerHeight)
		UIKit.Corner(header, radius)
		header.Parent = main
		-- Квадратная полоса закрывает нижние скругления шапки.
		local filler = filled("Filler", Colors.Header)
		filler.Size = UDim2.new(1, 0, 0.5, 0)
		filler.Position = UDim2.fromScale(0, 0.5)
		filler.Parent = header
		local title = UIKit.Text({
			text = props.title,
			textSize = UITokens.TextSize.Title,
			parent = header,
		})
		title.ZIndex = 2
		UIKit.Padding(title, UITokens.Spacing.Small)

		body.Position = UDim2.fromOffset(0, headerHeight)
		body.Size = UDim2.new(1, 0, 1, -headerHeight)
	end
	UIKit.Padding(body, UITokens.Spacing.Medium)

	place(holder, props)
	return holder, body
end

-- Плашка-«таблетка»: полностью скруглённая, тёмная (InkSoft) или с градиентом.
function UIKit.Pill(props: Placement & { text: string, gradient: UITokens.Gradient?, textSize: number? }): Frame
	local pill = filled("Pill", Colors.InkSoft)
	UIKit.Corner(pill, UITokens.Corner.Pill)
	UIKit.Border(pill)
	if props.gradient then
		pill.BackgroundColor3 = Colors.TextOnColor
		UIKit.Gradient(pill, props.gradient)
	end
	local label = UIKit.Text({
		text = props.text,
		textSize = props.textSize or UITokens.TextSize.Body,
		parent = pill,
	})
	local padding = Instance.new("UIPadding")
	padding.PaddingLeft = UDim.new(0, UITokens.Spacing.Large)
	padding.PaddingRight = UDim.new(0, UITokens.Spacing.Large)
	padding.PaddingTop = UDim.new(0, UITokens.Spacing.Small)
	padding.PaddingBottom = UDim.new(0, UITokens.Spacing.Small)
	padding.Parent = label
	place(pill, props)
	return pill
end

-- Плашка редкости: цвет редкости из UI_KIT.md и её название.
function UIKit.RarityTag(rarity: string, props: Placement & { textSize: number? }): Frame
	local tag = UIKit.Pill({
		text = Rarities.Names[rarity] or rarity,
		gradient = UITokens.Rarity[rarity] or UITokens.Rarity.Common,
		textSize = props.textSize or UITokens.TextSize.Small,
		parent = props.parent,
		size = props.size,
		position = props.position,
		anchorPoint = props.anchorPoint,
		layoutOrder = props.layoutOrder,
	})
	tag.Name = "RarityTag"
	return tag
end

-- Уведомление: карточка с цветной полосой слева (Info — обычное, Stop — отказ, Go — успех).
function UIKit.Toast(props: Placement & { text: string, kind: ButtonKind? }): Frame
	local toast = filled("Toast", Colors.Panel)
	UIKit.Corner(toast, UITokens.Corner.Card)
	UIKit.Border(toast)

	local accent = filled("Accent", Colors.TextOnColor)
	accent.Size = UDim2.new(0, UITokens.Spacing.Medium, 1, 0)
	UIKit.Corner(accent, UITokens.Corner.Card)
	UIKit.Gradient(accent, UITokens.Gradients[props.kind or "Info"])
	accent.Parent = toast

	local label = UIKit.Text({
		text = props.text,
		onLight = true,
		alignX = Enum.TextXAlignment.Left,
		textSize = UITokens.TextSize.Body,
		weight = UITokens.Fonts.ExtraBold,
		parent = toast,
	})
	local padding = Instance.new("UIPadding")
	padding.PaddingLeft = UDim.new(0, UITokens.Spacing.Medium * 2)
	padding.PaddingRight = UDim.new(0, UITokens.Spacing.Medium)
	padding.PaddingTop = UDim.new(0, UITokens.Spacing.Small)
	padding.PaddingBottom = UDim.new(0, UITokens.Spacing.Small)
	padding.Parent = label

	place(toast, props)
	return toast
end

-- Экранный слой для контроллера: не сбрасывается при смерти, учитывает безопасные зоны Roblox.
function UIKit.ScreenGui(name: string, displayOrder: number?): ScreenGui
	local gui = Instance.new("ScreenGui")
	gui.Name = name
	gui.ResetOnSpawn = false
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets
	gui.DisplayOrder = displayOrder or 0
	gui.Parent = game:GetService("Players").LocalPlayer:WaitForChild("PlayerGui")
	return gui
end

return UIKit

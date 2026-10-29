--!strict
-- Check-UI (D20): токены и фабрики интерфейса по стандарту заказчика (Skill check-ui-clean-roblox).
-- Копия scripts/CheckUI.lua из навыка, путь в игре: ReplicatedStorage.Shared.CheckUI.CheckUI.
-- Только клиентский интерфейс: покупки, награды и проверки — на сервере.

local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")

local CheckUI = {}

local function rgb(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local function seq(a: Color3, b: Color3): ColorSequence
	return ColorSequence.new(a, b)
end

-- Typography -------------------------------------------------------------------------------
CheckUI.Font = Enum.Font.GothamBlack
-- Text stroke thickness grows with font size, clamped to the spec range 2.0..3.5 px.
function CheckUI.StrokeFor(textSize: number): number
	return math.clamp(textSize / 11, 2, 3.5)
end

-- Assets (IDs from the specification; existence checked 2026-10-29, see references/asset-check.md).
-- Do NOT add IDs that were not provided or verified.
CheckUI.Assets = {
	Checkerboard = "rbxassetid://385956923",
	Sunburst = "rbxassetid://130563114903838",
	CashIcon = "rbxassetid://88694661500877",
	PlayerIcon = "rbxassetid://77589096360120",
	RobuxIcon = "rbxassetid://132185731364109",
	HoverSound = "rbxassetid://6895079853",
	ClickSound = "rbxassetid://6895079853",
}

-- Universal colors -------------------------------------------------------------------------
CheckUI.Colors = {
	Window = rgb(59, 88, 102),
	WindowStroke = rgb(24, 30, 34),
	Card = rgb(26, 44, 52),
	CardHighlight = rgb(75, 125, 145),
	Requirements = rgb(20, 34, 42),
	RequirementsBorder = rgb(85, 140, 160),
	CloseBase = rgb(115, 0, 16),
	CloseSep = rgb(70, 0, 10),
	CloseHighlight = rgb(255, 210, 235),
	CloseFace = seq(rgb(255, 125, 175), rgb(255, 20, 40)),
	ButtonOutline = rgb(12, 20, 26), -- #0C141A
	TextStroke = rgb(17, 23, 26), -- #11171A
	Black = rgb(0, 0, 0),
	White = rgb(255, 255, 255),
	ProgressTrough = rgb(20, 30, 36),
	ProgressTroughStroke = rgb(12, 18, 22),
	ProgressFill = seq(rgb(255, 200, 0), rgb(255, 106, 0)),
	ProgressBevel = rgb(153, 60, 0),
}

export type HeaderTheme = { gradient: ColorSequence, top: Color3, damier: Color3, divDark: Color3, titleDark: boolean? }

-- 5 canonical header themes (Settings has a light header: title keeps white text + black stroke).
CheckUI.Headers = {
	Shop = { gradient = seq(rgb(255, 20, 150), rgb(225, 0, 25)), top = rgb(255, 200, 225), damier = rgb(150, 0, 20), divDark = rgb(125, 0, 18) },
	Codes = { gradient = seq(rgb(0, 205, 255), rgb(0, 130, 245)), top = rgb(180, 240, 255), damier = rgb(0, 75, 150), divDark = rgb(0, 50, 110) },
	Settings = { gradient = seq(rgb(255, 255, 255), rgb(215, 222, 232)), top = rgb(255, 255, 255), damier = rgb(110, 120, 135), divDark = rgb(90, 100, 112) },
	Rebirth = { gradient = seq(rgb(160, 0, 255), rgb(96, 0, 200)), top = rgb(224, 160, 255), damier = rgb(96, 0, 144), divDark = rgb(80, 0, 120) },
	DailyRewards = { gradient = seq(rgb(152, 255, 0), rgb(80, 208, 0)), top = rgb(224, 255, 176), damier = rgb(53, 128, 0), divDark = rgb(37, 96, 0) },
} :: { [string]: HeaderTheme }

export type ButtonState = { gradient: ColorSequence, bevel: Color3, highlight: Color3, damier: Color3 }

-- Button State Triad + specialized states.
CheckUI.States = {
	Claim = { gradient = seq(rgb(180, 255, 25), rgb(105, 225, 0)), bevel = rgb(15, 120, 15), highlight = rgb(235, 255, 130), damier = rgb(40, 160, 20) },
	Claimed = { gradient = seq(rgb(216, 222, 228), rgb(148, 160, 176)), bevel = rgb(72, 82, 96), highlight = rgb(255, 255, 255), damier = rgb(96, 104, 112) },
	Locked = { gradient = seq(rgb(255, 32, 80), rgb(208, 0, 32)), bevel = rgb(112, 0, 16), highlight = rgb(255, 176, 200), damier = rgb(144, 0, 24) },
	Skip = { gradient = seq(rgb(255, 208, 0), rgb(255, 140, 0)), bevel = rgb(153, 76, 0), highlight = rgb(255, 240, 160), damier = rgb(176, 96, 0) },
	MusicOn = { gradient = seq(rgb(255, 20, 128), rgb(212, 0, 85)), bevel = rgb(120, 10, 45), highlight = rgb(255, 176, 208), damier = rgb(160, 0, 64) },
	-- Default iconless action gradient from §3.4 (#FFE808 -> #FF6800).
	Action = { gradient = seq(rgb(255, 232, 8), rgb(255, 104, 0)), bevel = rgb(153, 76, 0), highlight = rgb(255, 240, 160), damier = rgb(0, 0, 0) },
} :: { [string]: ButtonState }

-- Card backgrounds.
CheckUI.Cards = {
	Cyan = seq(rgb(0, 210, 255), rgb(0, 120, 255)),
	Purple = seq(rgb(176, 32, 255), rgb(112, 0, 224)),
	Lime = seq(rgb(180, 255, 25), rgb(105, 225, 0)),
	Magenta = seq(rgb(208, 0, 224), rgb(128, 0, 160)),
	Amber = seq(rgb(255, 170, 0), rgb(224, 96, 0)),
	Rainbow = ColorSequence.new({
		ColorSequenceKeypoint.new(0.00, rgb(255, 30, 80)),
		ColorSequenceKeypoint.new(0.18, rgb(255, 140, 0)),
		ColorSequenceKeypoint.new(0.35, rgb(255, 230, 0)),
		ColorSequenceKeypoint.new(0.52, rgb(40, 230, 50)),
		ColorSequenceKeypoint.new(0.70, rgb(0, 210, 255)),
		ColorSequenceKeypoint.new(0.85, rgb(90, 60, 255)),
		ColorSequenceKeypoint.new(1.00, rgb(220, 0, 230)),
	}),
}
CheckUI.RainbowRotation = 45

-- Layout constants.
CheckUI.HeaderHeight = 60
CheckUI.WindowCorner = 4
CheckUI.WindowStroke = 3.5
CheckUI.SunburstSpeed = 20 -- degrees per second
CheckUI.DamierFade = NumberSequence.new({ -- full-height window damier (§1.6)
	NumberSequenceKeypoint.new(0, 1),
	NumberSequenceKeypoint.new(0.33, 0.82),
	NumberSequenceKeypoint.new(0.66, 0.35),
	NumberSequenceKeypoint.new(1, 0.10),
})
CheckUI.ButtonDamierFade = NumberSequence.new(0.91, 0.62) -- iconless buttons (§3.4)

-- Low-level helpers ------------------------------------------------------------------------
local function stroke(parent: Instance, color: Color3, thickness: number, mode: Enum.ApplyStrokeMode?, transparency: number?): UIStroke
	local s = Instance.new("UIStroke")
	s.Color = color
	s.Thickness = thickness
	s.ApplyStrokeMode = mode or Enum.ApplyStrokeMode.Contextual
	s.Transparency = transparency or 0
	s.Parent = parent
	return s
end

local function gradient(parent: Instance, color: ColorSequence, rotation: number?): UIGradient
	local g = Instance.new("UIGradient")
	g.Color = color
	g.Rotation = rotation or 90
	g.Parent = parent
	return g
end

local function corner(parent: Instance, px: number)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, px)
	c.Parent = parent
end

local function frame(name: string, parent: Instance?, z: number?): Frame
	local f = Instance.new("Frame")
	f.Name = name
	f.BorderSizePixel = 0
	f.BackgroundTransparency = 1
	f.Size = UDim2.fromScale(1, 1)
	f.ZIndex = z or 1
	f.Parent = parent
	return f
end

CheckUI.Stroke = stroke
CheckUI.Gradient = gradient

-- Text: GothamBlack, white, black outline proportional to size. TextScaled + max size keeps
-- long (e.g. Cyrillic) labels from clipping.
export type TextProps = {
	Text: string,
	Parent: Instance?,
	TextSize: number?,
	Size: UDim2?,
	Position: UDim2?,
	AnchorPoint: Vector2?,
	Color: Color3?,
	ZIndex: number?,
	XAlignment: Enum.TextXAlignment?,
}

function CheckUI.Text(props: TextProps): TextLabel
	local size = props.TextSize or 24
	local label = Instance.new("TextLabel")
	label.Name = "Label"
	label.BackgroundTransparency = 1
	label.Font = CheckUI.Font
	label.Text = props.Text
	label.TextColor3 = props.Color or CheckUI.Colors.White
	label.TextScaled = true
	label.TextWrapped = true
	label.TextXAlignment = props.XAlignment or Enum.TextXAlignment.Center
	label.Size = props.Size or UDim2.fromScale(1, 1)
	label.Position = props.Position or UDim2.fromScale(0.5, 0.5)
	label.AnchorPoint = props.AnchorPoint or Vector2.new(0.5, 0.5)
	label.ZIndex = props.ZIndex or 1
	local limit = Instance.new("UITextSizeConstraint")
	limit.MaxTextSize = size
	limit.Parent = label
	stroke(label, CheckUI.Colors.Black, CheckUI.StrokeFor(size))
	label.Parent = props.Parent
	return label
end

-- Tiled checkerboard overlay with a vertical transparency fade.
function CheckUI.Checkerboard(parent: Instance, color: Color3, fade: NumberSequence, tile: number?, z: number?): ImageLabel
	local img = Instance.new("ImageLabel")
	img.Name = "Checkerboard"
	img.BackgroundTransparency = 1
	img.Size = UDim2.fromScale(1, 1)
	img.Image = CheckUI.Assets.Checkerboard
	img.ScaleType = Enum.ScaleType.Tile
	img.TileSize = UDim2.fromOffset(tile or 19, tile or 19)
	img.ImageColor3 = color
	img.ZIndex = z or 1
	local g = Instance.new("UIGradient")
	g.Name = "DamierGradient"
	g.Rotation = 90
	g.Transparency = fade
	g.Parent = img
	img.Parent = parent
	return img
end

-- Icon: always ScaleType.Fit (never stretched).
function CheckUI.Icon(image: string, parent: Instance?, size: UDim2?, z: number?): ImageLabel
	local img = Instance.new("ImageLabel")
	img.Name = "Icon"
	img.BackgroundTransparency = 1
	img.Image = image
	img.ScaleType = Enum.ScaleType.Fit
	img.Size = size or UDim2.fromScale(1, 1)
	img.AnchorPoint = Vector2.new(0.5, 0.5)
	img.Position = UDim2.fromScale(0.5, 0.5)
	img.ZIndex = z or 1
	img.Parent = parent
	return img
end

-- Interaction ------------------------------------------------------------------------------
local soundCache: { [string]: Sound } = {}
local function playSound(id: string)
	local sound = soundCache[id]
	if not sound then
		sound = Instance.new("Sound")
		sound.SoundId = id
		sound.Volume = 0.5
		soundCache[id] = sound
	end
	SoundService:PlayLocalSound(sound)
end

-- Center-anchored scale micro-interactions (§5). Hover is desktop-only; press works for touch.
-- Returns a function that disconnects everything.
function CheckUI.BindButton(btn: GuiButton, onActivated: (() -> ())?, hover: number?, click: number?): () -> ()
	assert(btn.AnchorPoint == Vector2.new(0.5, 0.5), ("[Check-UI] %s must have AnchorPoint (0.5, 0.5)"):format(btn.Name))
	local scale = btn:FindFirstChild("ButtonScale") :: UIScale?
	if not scale then
		local s = Instance.new("UIScale")
		s.Name = "ButtonScale"
		s.Parent = btn
		scale = s
	end
	local target = scale :: UIScale
	local hoverFactor, clickFactor = hover or 1.05, click or 0.94
	local hovering = false
	local current: Tween? = nil
	local function to(value: number, info: TweenInfo)
		if current then
			current:Cancel()
		end
		current = TweenService:Create(target, info, { Scale = value })
		current:Play()
	end
	local quick = TweenInfo.new(0.08, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	local press = TweenInfo.new(0.05, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	local release = TweenInfo.new(0.12, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
	local connections = {
		btn.MouseEnter:Connect(function()
			hovering = true
			playSound(CheckUI.Assets.HoverSound)
			to(hoverFactor, quick)
		end),
		btn.MouseLeave:Connect(function()
			hovering = false
			to(1, quick)
		end),
		btn.MouseButton1Down:Connect(function()
			playSound(CheckUI.Assets.ClickSound)
			to(clickFactor, press)
		end),
		btn.MouseButton1Up:Connect(function()
			to(if hovering then hoverFactor else 1, release)
		end),
		btn.Activated:Connect(function()
			if onActivated then
				onActivated()
			end
		end),
		-- Restore scale when the button is hidden or deactivated mid-press.
		btn:GetPropertyChangedSignal("Visible"):Connect(function()
			hovering = false
			if current then
				current:Cancel()
			end
			target.Scale = 1
		end),
	}
	return function()
		for _, c in connections do
			c:Disconnect()
		end
	end
end

-- Components -------------------------------------------------------------------------------

-- §3.1 Signature 3D beveled square close button.
function CheckUI.CloseButton(parent: Instance, onClose: (() -> ())?): ImageButton
	local btn = Instance.new("ImageButton")
	btn.Name = "CloseButton"
	btn.Size = UDim2.fromOffset(38, 38)
	btn.Position = UDim2.new(1, -34, 0.5, -2)
	btn.AnchorPoint = Vector2.new(0.5, 0.5)
	btn.BackgroundColor3 = CheckUI.Colors.CloseBase
	btn.BorderSizePixel = 0
	btn.AutoButtonColor = false
	btn.ZIndex = 25
	stroke(btn, CheckUI.Colors.Black, 2.8, Enum.ApplyStrokeMode.Border)

	local face = frame("Face", btn, 26)
	face.BackgroundTransparency = 0
	face.BackgroundColor3 = CheckUI.Colors.White
	face.Size = UDim2.new(1, 0, 1, -4)
	gradient(face, CheckUI.Colors.CloseFace)

	local inner = frame("InnerBorder", face, 27)
	inner.Size = UDim2.new(1, -2, 1, -2)
	inner.AnchorPoint = Vector2.new(0.5, 0.5)
	inner.Position = UDim2.fromScale(0.5, 0.5)
	stroke(inner, CheckUI.Colors.CloseHighlight, 1.2, Enum.ApplyStrokeMode.Border)

	local sep = frame("SepLine", btn, 27)
	sep.BackgroundTransparency = 0
	sep.BackgroundColor3 = CheckUI.Colors.CloseSep
	sep.Size = UDim2.new(1, 0, 0, 1)
	sep.Position = UDim2.new(0, 0, 1, -4)

	local x = Instance.new("TextLabel")
	x.Name = "X"
	x.Text = "X"
	x.Font = CheckUI.Font
	x.TextSize = 29
	x.TextColor3 = CheckUI.Colors.White
	x.BackgroundTransparency = 1
	x.Size = UDim2.fromScale(1, 1)
	x.AnchorPoint = Vector2.new(0.5, 0.5)
	x.Position = UDim2.fromScale(0.5, 0.5)
	x.ZIndex = 28
	stroke(x, CheckUI.Colors.Black, 3)
	x.Parent = face

	local s = Instance.new("UIScale")
	s.Name = "ButtonScale"
	s.Parent = btn
	btn.Parent = parent
	CheckUI.BindButton(btn, onClose)
	return btn
end

-- §3.2 Header action button (rounded 4px, bevel, inner highlight). state defaults to Skip.
function CheckUI.HeaderButton(parent: Instance, text: string, stateName: string?, offsetRight: number?, onActivated: (() -> ())?): ImageButton
	local state = CheckUI.States[stateName or "Skip"]
	local btn = Instance.new("ImageButton")
	btn.Name = text .. "Button"
	btn.Size = UDim2.fromOffset(84, 36)
	btn.Position = UDim2.new(1, offsetRight or -86, 0.5, -2)
	btn.AnchorPoint = Vector2.new(0.5, 0.5)
	btn.BackgroundColor3 = CheckUI.Colors.White
	btn.BorderSizePixel = 0
	btn.AutoButtonColor = false
	btn.ClipsDescendants = true
	btn.ZIndex = 25
	corner(btn, 4)
	stroke(btn, CheckUI.Colors.Black, 2.8, Enum.ApplyStrokeMode.Border)
	gradient(btn, state.gradient)

	local bevel = frame("Bevel", btn, 26)
	bevel.BackgroundTransparency = 0
	bevel.BackgroundColor3 = state.bevel
	bevel.Size = UDim2.new(1, 0, 0, 3)
	bevel.Position = UDim2.new(0, 0, 1, -3)

	local inner = frame("InnerHighlight", btn, 27)
	inner.Size = UDim2.new(1, -4, 1, -4)
	inner.AnchorPoint = Vector2.new(0.5, 0.5)
	inner.Position = UDim2.fromScale(0.5, 0.5)
	stroke(inner, state.highlight, 1.2, Enum.ApplyStrokeMode.Border)

	CheckUI.Text({ Text = text, Parent = btn, TextSize = 24, ZIndex = 28 })
	local s = Instance.new("UIScale")
	s.Name = "ButtonScale"
	s.Parent = btn
	btn.Parent = parent
	CheckUI.BindButton(btn, onActivated)
	return btn
end

-- §3.4 Canonical iconless button: square corners, 3px outline, gradient, checkerboard,
-- triple inner highlight, GothamBlack label with 1px optical lift.
export type ButtonProps = {
	Text: string,
	Parent: Instance?,
	Name: string?,
	State: string?, -- key of CheckUI.States, default "Action"
	Size: UDim2?,
	Position: UDim2?,
	TextSize: number?,
	ZIndex: number?,
	OnActivated: (() -> ())?,
}

function CheckUI.Button(props: ButtonProps): ImageButton
	local state = CheckUI.States[props.State or "Action"]
	local z = props.ZIndex or 25
	local btn = Instance.new("ImageButton")
	btn.Name = props.Name or "StandardButton"
	btn.Size = props.Size or UDim2.fromOffset(176, 55)
	btn.Position = props.Position or UDim2.fromScale(0.5, 0.5)
	btn.AnchorPoint = Vector2.new(0.5, 0.5)
	btn.BackgroundColor3 = CheckUI.Colors.White
	btn.BorderSizePixel = 0
	btn.AutoButtonColor = false
	btn.ClipsDescendants = true
	btn.ZIndex = z
	stroke(btn, CheckUI.Colors.ButtonOutline, 3, Enum.ApplyStrokeMode.Border).Name = "OuterStroke"
	gradient(btn, state.gradient).Name = "ButtonGradient"
	CheckUI.Checkerboard(btn, CheckUI.Colors.Black, CheckUI.ButtonDamierFade, 19, z + 1)
	for i, spec in { { 2, 0.25 }, { 4, 0.45 }, { 6, 0.8 } } do
		local f = frame("InnerHighlight" .. i, btn, z + 2)
		f.Size = UDim2.new(1, -spec[1], 1, -spec[1])
		f.AnchorPoint = Vector2.new(0.5, 0.5)
		f.Position = UDim2.fromScale(0.5, 0.5)
		stroke(f, CheckUI.Colors.White, 1, Enum.ApplyStrokeMode.Border, spec[2])
	end
	local label = CheckUI.Text({
		Text = props.Text,
		Parent = btn,
		TextSize = props.TextSize or 36,
		Size = UDim2.new(1, -12, 1, -8),
		Position = UDim2.new(0.5, 0, 0.5, -1),
		ZIndex = z + 3,
	})
	local textStroke = label:FindFirstChildOfClass("UIStroke") :: UIStroke
	textStroke.Name = "TextStroke"
	textStroke.Color = CheckUI.Colors.TextStroke
	textStroke.Thickness = 3
	local s = Instance.new("UIScale")
	s.Name = "ButtonScale"
	s.Parent = btn
	btn.Parent = props.Parent
	CheckUI.BindButton(btn, props.OnActivated, 1.06, 0.94)
	return btn
end

-- Switch a canonical button between states (Claim / Claimed / Locked ...).
function CheckUI.SetButtonState(btn: ImageButton, stateName: string)
	local state = CheckUI.States[stateName]
	local g = btn:FindFirstChild("ButtonGradient") :: UIGradient?
	if state and g then
		g.Color = state.gradient
	end
end

-- §3.3 Progress bar. Returns trough and a setter.
function CheckUI.ProgressBar(parent: Instance, size: UDim2, position: UDim2, progress: number, text: string?): (Frame, (number, string?) -> ())
	local trough = frame("ProgressTrough", parent, 24)
	trough.BackgroundTransparency = 0
	trough.BackgroundColor3 = CheckUI.Colors.ProgressTrough
	trough.Size = size
	trough.Position = position
	trough.AnchorPoint = Vector2.new(0.5, 0)
	trough.ClipsDescendants = true
	stroke(trough, CheckUI.Colors.ProgressTroughStroke, 2, Enum.ApplyStrokeMode.Border)

	local fill = frame("ProgressFill", trough, 25)
	fill.BackgroundTransparency = 0
	fill.BackgroundColor3 = CheckUI.Colors.White
	gradient(fill, CheckUI.Colors.ProgressFill)
	local bevel = frame("Bevel", fill, 26)
	bevel.BackgroundTransparency = 0
	bevel.BackgroundColor3 = CheckUI.Colors.ProgressBevel
	bevel.Size = UDim2.new(1, 0, 0, 2)
	bevel.Position = UDim2.new(0, 0, 1, -2)
	local label = CheckUI.Text({ Text = "", Parent = trough, TextSize = 22, ZIndex = 27 })

	local function set(value: number, newText: string?)
		local pct = math.clamp(value, 0, 1)
		fill.Size = UDim2.fromScale(pct, 1)
		label.Text = newText or ("%d%%"):format(math.floor(pct * 100))
	end
	set(progress, text)
	return trough, set
end

-- Recessed inset card (optionally with a themed gradient background).
function CheckUI.Card(parent: Instance?, size: UDim2?, background: ColorSequence?, z: number?): Frame
	local card = frame("Card", parent, z or 2)
	card.BackgroundTransparency = 0
	card.BackgroundColor3 = if background then CheckUI.Colors.White else CheckUI.Colors.Card
	card.Size = size or UDim2.fromOffset(160, 190)
	corner(card, 4)
	stroke(card, CheckUI.Colors.WindowStroke, 2.5, Enum.ApplyStrokeMode.Border)
	if background then
		local g = gradient(card, background, if background == CheckUI.Cards.Rainbow then CheckUI.RainbowRotation else 90)
		g.Name = "CardGradient"
	end
	local inner = frame("InnerHighlight", card, (z or 2) + 1)
	inner.Size = UDim2.new(1, -4, 1, -4)
	inner.AnchorPoint = Vector2.new(0.5, 0.5)
	inner.Position = UDim2.fromScale(0.5, 0.5)
	stroke(inner, CheckUI.Colors.CardHighlight, 1.2, Enum.ApplyStrokeMode.Border, 0.4)
	return card
end

-- Sunburst behind a card/icon. Rotates only while `visibleWhen` is visible; cleans up on destroy.
function CheckUI.Sunburst(parent: Instance, visibleWhen: GuiObject, size: UDim2?, z: number?): ImageLabel
	local img = CheckUI.Icon(CheckUI.Assets.Sunburst, parent, size or UDim2.fromScale(1.4, 1.4), z or 1)
	img.Name = "Sunburst"
	local connection: RBXScriptConnection? = nil
	local function update()
		local shouldRun = visibleWhen.Visible and img.Parent ~= nil
		if shouldRun and not connection then
			connection = RunService.RenderStepped:Connect(function(dt)
				img.Rotation = (img.Rotation + CheckUI.SunburstSpeed * dt) % 360
			end)
		elseif not shouldRun and connection then
			connection:Disconnect()
			connection = nil
		end
	end
	visibleWhen:GetPropertyChangedSignal("Visible"):Connect(update)
	img.Destroying:Connect(function()
		if connection then
			connection:Disconnect()
		end
	end)
	update()
	return img
end

-- Modal window: solid slate canvas, 60px themed header with top highlight, damier fade,
-- 2-tier divider, close button, scrolling body. WindowScale is driven by Responsive.lua.
export type WindowProps = {
	Title: string,
	Theme: string, -- key of CheckUI.Headers
	Parent: Instance?,
	Size: UDim2?, -- base design size in pixels (before WindowScale)
	OnClose: (() -> ())?,
}

function CheckUI.Window(props: WindowProps): (Frame, ScrollingFrame, ImageButton)
	local theme = CheckUI.Headers[props.Theme]
	assert(theme, "[Check-UI] Unknown header theme: " .. tostring(props.Theme))
	local window = frame(props.Title:gsub("%s", "") .. "Window", nil, 20)
	window.BackgroundTransparency = 0
	window.BackgroundColor3 = CheckUI.Colors.Window
	window.Size = props.Size or UDim2.fromOffset(640, 440)
	window.AnchorPoint = Vector2.new(0.5, 0.5)
	window.Position = UDim2.fromScale(0.5, 0.5)
	window.ClipsDescendants = false
	corner(window, CheckUI.WindowCorner)
	stroke(window, CheckUI.Colors.WindowStroke, CheckUI.WindowStroke, Enum.ApplyStrokeMode.Border)
	local windowScale = Instance.new("UIScale")
	windowScale.Name = "WindowScale"
	windowScale.Parent = window

	local header = frame("Header", window, 21)
	header.BackgroundTransparency = 0
	header.BackgroundColor3 = CheckUI.Colors.White
	header.Size = UDim2.new(1, 0, 0, CheckUI.HeaderHeight)
	header.ClipsDescendants = true
	corner(header, CheckUI.WindowCorner)
	gradient(header, theme.gradient)
	CheckUI.Checkerboard(header, theme.damier, CheckUI.DamierFade, 19, 22)
	local top = frame("TopHighlight", header, 23)
	top.BackgroundTransparency = 0
	top.BackgroundColor3 = theme.top
	top.Size = UDim2.new(1, 0, 0, 2)
	CheckUI.Text({
		Text = props.Title,
		Parent = header,
		TextSize = 34,
		Size = UDim2.new(1, -120, 1, -12),
		Position = UDim2.new(0, 16, 0.5, -1),
		AnchorPoint = Vector2.new(0, 0.5),
		XAlignment = Enum.TextXAlignment.Left,
		ZIndex = 24,
	})

	-- 2-tier divider: thematic dark 3px + black 3px.
	local divDark = frame("DividerDark", window, 23)
	divDark.BackgroundTransparency = 0
	divDark.BackgroundColor3 = theme.divDark
	divDark.Size = UDim2.new(1, 0, 0, 3)
	divDark.Position = UDim2.fromOffset(0, CheckUI.HeaderHeight)
	local divBlack = frame("DividerBlack", window, 23)
	divBlack.BackgroundTransparency = 0
	divBlack.BackgroundColor3 = CheckUI.Colors.Black
	divBlack.Size = UDim2.new(1, 0, 0, 3)
	divBlack.Position = UDim2.fromOffset(0, CheckUI.HeaderHeight + 3)

	local close = CheckUI.CloseButton(header, props.OnClose)

	local bodyTop = CheckUI.HeaderHeight + 6
	local body = Instance.new("ScrollingFrame")
	body.Name = "Body"
	body.BackgroundTransparency = 1
	body.BorderSizePixel = 0
	body.Position = UDim2.fromOffset(0, bodyTop)
	body.Size = UDim2.new(1, 0, 1, -bodyTop)
	body.AutomaticCanvasSize = Enum.AutomaticSize.Y
	body.CanvasSize = UDim2.new()
	body.ScrollBarThickness = 6
	body.ScrollBarImageColor3 = CheckUI.Colors.WindowStroke
	body.ZIndex = 21
	local padding = Instance.new("UIPadding")
	padding.PaddingTop, padding.PaddingBottom = UDim.new(0, 12), UDim.new(0, 12)
	padding.PaddingLeft, padding.PaddingRight = UDim.new(0, 12), UDim.new(0, 12)
	padding.Parent = body
	body.Parent = window

	window.Parent = props.Parent
	return window, body, close
end

return CheckUI

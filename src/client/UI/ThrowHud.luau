-- Интерфейс броска вдаль (D75) — строго по записи референса владельца (2026-11-28), размеры сняты с кадра 960 × 540
-- и пересчитываются по высоте экрана (UITokens.Throw, единица — пиксель кадра 540): шкала по центру экрана (капсула
-- зелёный верх → красный низ, пять делений, белый бегунок, число справа, «Нажмите, чтобы бросить!» под ней; после
-- нажатия — «+N Мощность» и «Идеально!»), чёрные поля кино, затемнение и вспышка; в полёте — светлая плашка «1.35X /
-- Удача» и тёмная полоса с названием зоны; на раскрытии — «1 из N» сверху, имя по буквам снизу; на карточке — «Удача!»
-- с лучами за числом, редкость этажа, имя, доход и метка «Новинка!». Шрифт — LuckiestGuy (кириллица — запасным
-- шрифтом Roblox, как в референсе). Нажатие в любом месте экрана — бросок. Ничего сверх записи здесь нет.
-- Только показ: что показывать, решает Controllers/ThrowController; появления считаются по времени в Update.
-- Зависит от StudUI (лучи), Config/UITokens.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))

local T = UITokens.Throw
local FONT = UI.Fonts.Heavy -- шрифт игры (Stud-UI); вид и слова — свои, от референса — только места и размеры
local WHITE = Color3.new(1, 1, 1)
local BLACK = Color3.new(0, 0, 0)

local ThrowHud = {}

ThrowHud.RaysImage = UI.Assets.Sunburst -- лучи (картинка Stud-UI): и за числом, и за существом в мире

local gui: ScreenGui
local overlay: Frame
local barTop: Frame
local barBottom: Frame
local tap: TextButton
local aim: Frame
local tube: Frame
local marker: Frame
local value: TextLabel
local caption: TextLabel
local power: TextLabel
local perfect: TextLabel
local flight: Frame
local luck: TextLabel
local zoneLabel: TextLabel
local reveal: Frame
local oneIn: TextLabel
local lucky: TextLabel
local rays: ImageLabel
local nameLabel: TextLabel
local card: Frame
local cardLines: { TextLabel } = {}
local tag: Frame
local tagLabel: TextLabel
local onTap: (() -> ())? = nil

local unit = 1 -- пикселей экрана в одном пикселе кадра 540
local strokes: { { stroke: UIStroke, px: number } } = {}
local layouts: { () -> () } = {}

type Pop = { scale: UIScale, from: number, started: number, dur: number }
local pops: { [UIScale]: Pop } = {}
local flash = { alpha = 0, decay = 0, color = T.Flash }
local fade = 0
local fadeColor = T.Dip
local clock = 0

local function new(class: string, props: { [string]: any }, parent: Instance?): any
	local object = Instance.new(class)
	for key, v in props do
		(object :: any)[key] = v
	end
	object.Parent = parent
	return object
end

local function px(n: number): number
	return math.round(n * unit)
end

-- Текст с чёрной обводкой; размер и место ставит layout (в пикселях кадра 540).
local function text(parent: Instance, name: string, size: number, color: Color3?): TextLabel
	local label = new("TextLabel", {
		Name = name,
		BackgroundTransparency = 1,
		FontFace = FONT,
		Text = "",
		TextColor3 = color or WHITE,
		AutomaticSize = Enum.AutomaticSize.XY,
		AnchorPoint = Vector2.new(0.5, 0.5),
		ZIndex = 10,
	}, parent)
	local stroke = new("UIStroke", { Color = BLACK, LineJoinMode = Enum.LineJoinMode.Round }, label)
	table.insert(strokes, { stroke = stroke, px = math.max(1.6, size * 0.085) })
	table.insert(layouts, function()
		label.TextSize = px(size)
	end)
	return label
end

local function scaleOf(object: GuiObject): UIScale
	return object:FindFirstChildOfClass("UIScale") or new("UIScale", {}, object)
end

local function pop(object: GuiObject, from: number?, dur: number?)
	local scale = scaleOf(object)
	pops[scale] = { scale = scale, from = from or 1.5, started = clock, dur = dur or 0.3 }
	scale.Scale = from or 1.5
end

local function backOut(t: number): number
	local x = math.clamp(t, 0, 1) - 1
	return 1 + x * x * (2.7 * x + 1.7)
end

local function relayout()
	local camera = workspace.CurrentCamera
	local height = if camera then camera.ViewportSize.Y else 540
	unit = math.max(0.4, height / 540)
	for _, fn in layouts do
		fn()
	end
	for _, s in strokes do
		s.stroke.Thickness = math.max(1, s.px * unit)
	end
end

function ThrowHud.Init(parent: Instance)
	gui = UI.ScreenGui("ThrowHud", T.Order, { Parent = parent, Menu = false })
	gui.Enabled = false

	tap = new("TextButton", {
		Name = "Tap",
		Text = "",
		BackgroundTransparency = 1,
		Size = UDim2.fromScale(1, 1),
		ZIndex = 1,
		Visible = false,
	}, gui)
	tap.Activated:Connect(function()
		if onTap then
			onTap()
		end
	end)

	-- шкала: по центру экрана
	local S = T.Scale
	aim = new("Frame", { Name = "Aim", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Visible = false }, gui)
	tube = new("Frame", {
		Name = "Tube",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(S.At.X, S.At.Y),
		BackgroundColor3 = WHITE,
		ZIndex = 4,
	}, aim)
	local corner = new("UICorner", {}, tube)
	local tubeStroke = new("UIStroke", { Color = BLACK }, tube)
	table.insert(strokes, { stroke = tubeStroke, px = S.Stroke })
	new("UIGradient", {
		Rotation = 90,
		Color = ColorSequence.new({
			ColorSequenceKeypoint.new(0, S.Top),
			ColorSequenceKeypoint.new(0.38, S.High),
			ColorSequenceKeypoint.new(0.7, S.Mid),
			ColorSequenceKeypoint.new(1, S.Low),
		}),
	}, tube)
	for i = 1, S.Ticks do
		new("Frame", {
			Name = "Tick",
			BackgroundColor3 = BLACK,
			BackgroundTransparency = 0.25,
			BorderSizePixel = 0,
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(0.5, i / (S.Ticks + 1)),
			Size = UDim2.new(1, 0, 0, 2),
			ZIndex = 5,
		}, tube)
	end
	marker = new("Frame", {
		Name = "Marker",
		BackgroundColor3 = S.MarkerFill,
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 1),
		ZIndex = 8,
	}, tube)
	local markerCorner = new("UICorner", {}, marker)
	local markerStroke = new("UIStroke", { Color = S.MarkerEdge }, marker)
	table.insert(strokes, { stroke = markerStroke, px = 2 })
	value = text(marker, "Value", S.Value)
	value.AnchorPoint = Vector2.new(0, 0.5)
	caption = text(aim, "Caption", S.Caption)
	caption.Text = "Нажми, чтобы бросить!"
	power = text(aim, "Power", S.Power)
	power.AnchorPoint = Vector2.new(0, 0.5)
	power.Visible = false
	perfect = text(aim, "Perfect", S.Perfect)
	perfect.Visible = false
	table.insert(layouts, function()
		tube.Size = UDim2.fromOffset(px(S.Size.X), px(S.Size.Y))
		corner.CornerRadius = UDim.new(0, px(S.Size.X / 2))
		marker.Size = UDim2.fromOffset(px(S.Marker.X), px(S.Marker.Y))
		markerCorner.CornerRadius = UDim.new(0, px(S.Marker.Y / 2))
		value.Position = UDim2.new(1, px(S.ValueGap), 0.5, 0)
		caption.Position = UDim2.new(S.At.X, 0, S.At.Y, px(S.Size.Y / 2 + S.CaptionGap))
		perfect.Position = caption.Position
		power.Position = UDim2.new(S.At.X, px(S.PowerShift), S.At.Y, 0)
	end)

	-- полёт: светлая плашка «1.35X / Удача» и тёмная полоса с названием зоны
	local F = T.Flight
	flight = new(
		"Frame",
		{ Name = "Flight", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Visible = false },
		gui
	)
	local plate = new("Frame", {
		Name = "Plate",
		AnchorPoint = Vector2.new(0.5, 0),
		BackgroundColor3 = WHITE,
		BackgroundTransparency = F.PlateAlpha,
		ZIndex = 20,
	}, flight)
	local plateCorner = new("UICorner", {}, plate)
	luck = text(plate, "Luck", F.Luck)
	local luckWord = text(plate, "Word", F.Word)
	luckWord.Text = "Удача"
	local band = new("Frame", {
		Name = "Band",
		AnchorPoint = Vector2.new(0.5, 0),
		BackgroundColor3 = F.Band,
		BorderSizePixel = 0,
		ZIndex = 20,
	}, flight)
	new("UIGradient", {
		Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(0.25, F.BandAlpha),
			NumberSequenceKeypoint.new(0.75, F.BandAlpha),
			NumberSequenceKeypoint.new(1, 1),
		}),
	}, band)
	zoneLabel = text(band, "Zone", F.Zone)
	table.insert(layouts, function()
		plate.Size = UDim2.fromOffset(px(F.Plate.X), px(F.Plate.Y))
		plate.Position = UDim2.new(0.5, 0, 0, px(F.PlateTop))
		plateCorner.CornerRadius = UDim.new(0, px(F.Plate.Y * 0.45))
		luck.Position = UDim2.new(0.5, 0, 0, px(F.LuckAt))
		luckWord.Position = UDim2.new(0.5, 0, 0, px(F.WordAt))
		band.Size = UDim2.new(F.BandWidth, 0, 0, px(F.BandHeight))
		band.Position = UDim2.new(0.5, 0, 0, px(F.BandTop))
		zoneLabel.Position = UDim2.fromScale(0.5, 0.5)
	end)

	-- раскрытие: «1 из N» сверху (с «Удача!» и лучами на карточке), имя по буквам снизу
	local R = T.Reveal
	reveal = new(
		"Frame",
		{ Name = "Reveal", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Visible = false },
		gui
	)
	rays = UI.Image(reveal, UI.Assets.Sunburst, { Name = "Rays", ZIndex = 8, Color = R.Rays })
	rays.Visible = false
	oneIn = text(reveal, "OneIn", R.OneIn)
	lucky = text(reveal, "Lucky", R.Lucky)
	lucky.Text = "Удача!"
	lucky.Visible = false
	nameLabel = text(reveal, "Name", R.Name)
	table.insert(layouts, function()
		oneIn.Position = UDim2.new(0.5, 0, 0, px(R.OneInAt))
		lucky.Position = UDim2.new(0.5, 0, 0, px(R.LuckyAt))
		rays.Position = UDim2.new(0.5, 0, 0, px(R.OneInAt))
		rays.Size = UDim2.fromOffset(px(R.RaysSize), px(R.RaysSize))
		nameLabel.Position = UDim2.new(0.5, 0, 0, px(R.NameAt))
	end)

	-- карточка: редкость этажа, имя, доход; справа — метка
	local K = T.Card
	card =
		new("Frame", { Name = "Card", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Visible = false }, gui)
	for i, spec in { { K.Rarity, K.RarityAt }, { K.Name, K.NameAt }, { K.Income, K.IncomeAt } } do
		local line = text(card, "Line" .. i, spec[1])
		cardLines[i] = line
		table.insert(layouts, function()
			line.Position = UDim2.new(0.5, 0, 0, px(spec[2]))
		end)
	end
	tag = new("Frame", {
		Name = "Tag",
		AnchorPoint = Vector2.new(0.5, 0.5),
		BackgroundColor3 = K.TagFill,
		Rotation = K.TagTurn,
		ZIndex = 12,
	}, card)
	local tagCorner = new("UICorner", {}, tag)
	local tagStroke = new("UIStroke", { Color = K.TagEdge }, tag)
	table.insert(strokes, { stroke = tagStroke, px = 3 })
	tagLabel = text(tag, "Text", K.TagText)
	tagLabel.ZIndex = 13
	table.insert(layouts, function()
		tag.Size = UDim2.fromOffset(px(K.Tag.X), px(K.Tag.Y))
		tag.Position = UDim2.new(0.5, px(K.TagShift), 0, px(K.TagAt))
		tagCorner.CornerRadius = UDim.new(0, px(8))
		tagLabel.Position = UDim2.fromScale(0.5, 0.5)
	end)

	-- чёрные поля кино и затемнение/вспышка — поверх всего
	barTop = new("Frame", {
		Name = "BarTop",
		BackgroundColor3 = BLACK,
		BorderSizePixel = 0,
		Size = UDim2.fromScale(1, 0),
		ZIndex = 40,
	}, gui)
	barBottom = new("Frame", {
		Name = "BarBottom",
		BackgroundColor3 = BLACK,
		BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Size = UDim2.fromScale(1, 0),
		ZIndex = 40,
	}, gui)
	overlay = new("Frame", {
		Name = "Overlay",
		BackgroundColor3 = T.Dip,
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = UDim2.fromScale(1, 1),
		ZIndex = 50,
	}, gui)

	relayout()
	local camera = workspace.CurrentCamera
	if camera then
		camera:GetPropertyChangedSignal("ViewportSize"):Connect(relayout)
	end
end

function ThrowHud.Gui(): ScreenGui
	return gui
end

function ThrowHud.SetEnabled(on: boolean)
	gui.Enabled = on
	if on then
		relayout()
		return
	end
	tap.Visible = false
	aim.Visible = false
	flight.Visible = false
	reveal.Visible = false
	card.Visible = false
	onTap = nil
	ThrowHud.Bars(0)
	ThrowHud.Vignette(0)
	fade = 0
	flash.alpha = 0
	overlay.BackgroundTransparency = 1
end

-- Затемнение (режиссёр ставит каждый кадр): alpha 0…1.
function ThrowHud.Fade(alpha: number, color: Color3?)
	fade = math.clamp(alpha, 0, 1)
	fadeColor = color or T.Dip
end

-- Вспышка: сама гаснет за seconds.
function ThrowHud.Flash(alpha: number, seconds: number, color: Color3?)
	flash.alpha = alpha
	flash.decay = alpha / math.max(0.01, seconds)
	flash.color = color or T.Flash
end

-- Чёрные поля кино: 0…1.
function ThrowHud.Bars(amount: number)
	local h = T.Bars * math.clamp(amount, 0, 1)
	barTop.Size = UDim2.fromScale(1, h)
	barBottom.Size = UDim2.fromScale(1, h)
end

-- Шкала появилась: нажатие в любом месте экрана — handler.
function ThrowHud.ShowAim()
	onTap = nil
	power.Visible = false
	perfect.Visible = false
	caption.Visible = true
	aim.Visible = true
	tap.Visible = false -- нажатия ловит Controllers/ThrowController (джойстик телефона остаётся свободным)
end

-- Бегунок: position 0 (низ) … 1 (верх), число рядом.
function ThrowHud.SetMarker(position: number, label: string)
	marker.Position = UDim2.fromScale(0.5, 1 - math.clamp(position, 0, 1))
	value.Text = label
end

-- Нажал: «+N Мощность» у шкалы; «Идеально!» под ней — только при идеальном попадании.
function ThrowHud.AimResult(label: string, isPerfect: boolean)
	tap.Visible = false
	caption.Visible = false
	power.Text = label
	power.Visible = true
	pop(power, 1.6, 0.3)
	perfect.Text = "Идеально!"
	perfect.Visible = isPerfect
	if isPerfect then
		pop(perfect, 1.6, 0.34)
	end
end

function ThrowHud.HideAim()
	aim.Visible = false
	tap.Visible = false
	onTap = nil
end

function ThrowHud.Flight(on: boolean)
	flight.Visible = on
end

-- Счётчик удачи и зона; bump — зона сменилась (название всплывает).
function ThrowHud.SetFlight(luckValue: number, zone: string, color: Color3, bump: boolean)
	luck.Text = ("×%.2f"):format(luckValue)
	zoneLabel.Text = zone
	zoneLabel.TextColor3 = color
	if bump then
		pop(zoneLabel, 1.5, 0.32)
	end
end

function ThrowHud.Reveal(on: boolean)
	reveal.Visible = on
	if on then
		lucky.Visible = false
		rays.Visible = false
	end
end

-- Раскрытие: «1 из N» и имя с пропусками; bump — число выросло (лёгкий толчок). Число видно только от Reveal.From;
-- чем реже — тем крупнее и ярче.
function ThrowHud.SetReveal(n: number, name: string, bump: boolean)
	local R = T.Reveal
	nameLabel.Text = name
	if n < R.From then
		oneIn.Visible = false
		lucky.Visible = false
		rays.Visible = false
		return
	end
	local rare = math.clamp(math.log10(n / R.From) / 3, 0, 1)
	oneIn.Visible = true
	oneIn.Text = ("1 из %d"):format(n)
	oneIn.TextSize = px(R.OneIn * (1 + R.Grow * rare))
	oneIn.TextColor3 = WHITE:Lerp(R.Hot, rare)
	if bump then
		pop(oneIn, 1.18, 0.16)
	end
end

-- «Удача!» над числом (редкий результат).
function ThrowHud.Lucky()
	if oneIn.Visible then
		lucky.Visible = true
		pop(lucky, 1.8, 0.34)
	end
end

-- Затемнение краёв экрана (полное шоу): 0…1.
local vignette: { Frame } = {}
function ThrowHud.Vignette(amount: number)
	if #vignette == 0 then
		-- четыре полосы с градиентом от края: без картинок
		for _, side in
			{ { 0, 0, 1, 0.3, 90 }, { 0, 0.7, 1, 0.3, 270 }, { 0, 0, 0.22, 1, 0 }, { 0.78, 0, 0.22, 1, 180 } }
		do
			local frame = new("Frame", {
				Name = "Vignette",
				BackgroundColor3 = BLACK,
				BorderSizePixel = 0,
				Position = UDim2.fromScale(side[1], side[2]),
				Size = UDim2.fromScale(side[3], side[4]),
				ZIndex = 2,
			}, gui)
			new("UIGradient", { Rotation = side[5] }, frame)
			table.insert(vignette, frame)
		end
	end
	local k = math.clamp(amount, 0, 1)
	for _, frame in vignette do
		frame.Visible = k > 0.01
		local gradient = frame:FindFirstChildOfClass("UIGradient") :: UIGradient
		gradient.Transparency = NumberSequence.new(1 - T.Vignette * k, 1)
	end
end

-- Карточка: лучи за числом, три строки (редкость этажа, имя, доход) и метка; имя по буквам убирается. nil — убрать.
function ThrowHud.Card(lines: { { text: string, color: Color3? } }?, tagText: string?)
	if not lines then
		card.Visible = false
		rays.Visible = false
		return
	end
	nameLabel.Text = ""
	rays.Visible = oneIn.Visible -- лучи — только за числом от 1 из 100
	if oneIn.Visible then
		pop(rays, 0.3, 0.4)
		pop(oneIn, 1.5, 0.34)
	end
	for i, label in cardLines do
		local line = lines[i]
		label.Text = if line then line.text else ""
		label.TextColor3 = (line and line.color) or WHITE
	end
	tag.Visible = tagText ~= nil and tagText ~= ""
	tagLabel.Text = tagText or ""
	card.Visible = true
	pop(tag, 0.2, 0.38)
end

-- ── панель выбора вида Ловибума у края (свой экранный слой: видна, пока шкалы нет) ──────────────────────────────
local kindsGui: ScreenGui
local kindsRow: Frame
local kindPills: { [string]: { frame: Frame, label: TextLabel } } = {}
local onKind: ((string) -> ())? = nil

function ThrowHud.InitKinds(parent: Instance, kinds: { string })
	local K = T.Kinds
	kindsGui = UI.ScreenGui("ThrowKinds", T.Order - 1, { Parent = parent, Menu = false })
	kindsGui.Enabled = false
	kindsRow = new("Frame", { Name = "Row", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5) }, kindsGui)
	local list = new("UIListLayout", {
		FillDirection = Enum.FillDirection.Horizontal,
		HorizontalAlignment = Enum.HorizontalAlignment.Center,
		VerticalAlignment = Enum.VerticalAlignment.Center,
		SortOrder = Enum.SortOrder.LayoutOrder,
	}, kindsRow)
	for i, kind in kinds do
		local pill = new("TextButton", {
			Name = kind,
			Text = "",
			AutoButtonColor = false,
			BackgroundColor3 = K.Fill,
			BackgroundTransparency = K.Alpha,
			LayoutOrder = i,
		}, kindsRow)
		local corner = new("UICorner", {}, pill)
		local stroke = new("UIStroke", { Color = BLACK, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, pill)
		table.insert(strokes, { stroke = stroke, px = 2 })
		local label = text(pill, "Text", K.Text)
		kindPills[kind] = { frame = pill, label = label }
		pill.Activated:Connect(function()
			if onKind then
				onKind(kind)
			end
		end)
		table.insert(layouts, function()
			pill.Size = UDim2.fromOffset(px(K.Size.X), px(K.Size.Y))
			corner.CornerRadius = UDim.new(0, px(K.Size.Y / 2))
			label.Position = UDim2.fromScale(0.5, 0.5)
		end)
	end
	table.insert(layouts, function()
		list.Padding = UDim.new(0, px(K.Gap))
		kindsRow.Size = UDim2.fromOffset(px((K.Size.X + K.Gap) * #kinds), px(K.Size.Y))
		kindsRow.Position = UDim2.new(0.5, 0, 1, -px(K.Bottom))
	end)
	relayout()
end

-- Панель видов: строки { kind, text, count, selected }; nil — убрать. handler — выбор вида.
function ThrowHud.SetKinds(
	rows: { { kind: string, text: string, count: number, selected: boolean } }?,
	handler: ((string) -> ())?
)
	if not rows then
		if kindsGui.Enabled then
			kindsGui.Enabled = false
		end
		return
	end
	onKind = handler
	for _, row in rows do
		local pill = kindPills[row.kind]
		if pill then
			pill.label.Text = row.text
			pill.label.TextColor3 = if row.count > 0 then WHITE else T.Kinds.Empty
			pill.frame.BackgroundColor3 = if row.selected then T.Kinds.On else T.Kinds.Fill
			pill.frame.BackgroundTransparency = if row.selected then 0.05 else T.Kinds.Alpha
		end
	end
	if not kindsGui.Enabled then
		relayout()
		kindsGui.Enabled = true
	end
end

-- Каждый кадр: появления, лучи, вспышка, затемнение.
function ThrowHud.Update(dt: number)
	clock += dt
	for scale, p in pops do
		local t = (clock - p.started) / p.dur
		if t >= 1 then
			scale.Scale = 1
			pops[scale] = nil
		else
			scale.Scale = p.from + (1 - p.from) * backOut(t)
		end
	end
	if rays.Visible then
		rays.Rotation = (clock * 40) % 360
	end
	if flash.alpha > 0 then
		flash.alpha = math.max(0, flash.alpha - flash.decay * dt)
	end
	if flash.alpha > fade then
		overlay.BackgroundColor3 = flash.color
		overlay.BackgroundTransparency = 1 - flash.alpha
	else
		overlay.BackgroundColor3 = fadeColor
		overlay.BackgroundTransparency = 1 - fade
	end
end

return ThrowHud

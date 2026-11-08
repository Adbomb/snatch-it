-- Мини-игра поимки «Ловибум» на клиенте ловящего (D55, Stud-UI; поимка от первого лица). Сервер прислал CatchState —
-- режим поимки: камера подлетает к существу (камеру считает сервер — Shared/CatchThrow.Frame: существо крупно в
-- центре, фон — настоящая локация), свой персонаж спрятан, управление выключено (на телефоне — и экранные кнопки).
-- Вокруг существа два кольца: белое — наибольшее, цветное сжимается и начинается снова (Shared/CatchRules.CircleRadius —
-- тот же размер, что у сервера; цвет — базовая сложность захвата выбранным видом: зелёный — легко … красный — трудно;
-- на шанс размер кольца не влияет). Внизу по центру лежит 3D-Ловибум выбранного вида: его берут мышью или пальцем, он
-- идёт за указателем; бросок — смахнуть вверх: направление — куда, скорость в конце жеста — сила (короткий, медленный,
-- вбок — не бросок, Ловибум возвращается). Серверу уходит только жест (CatchThrow.Gesture) и время отпускания — точку
-- прилёта и попадание считает сервер; клиент сразу показывает полёт к той же точке (LovibumFxController.LocalThrow),
-- исход приходит с сервера. Справа внизу — выбор вида (Бум, Турбо, Мега уровня этого босса и запас; в обучении — один
-- учебный), слева вверху — «Уйти», вверху — компактная плашка (имя; редкость, шанс, броски), слева от Ловибума —
-- короткая подсказка. Фон спокойнее: дальний план размыт (DepthOfField), края экрана притемнены; локация та же. CatchState =
-- nil — конец: камера, персонаж, HUD, подписи, свет и управление вернулись.
-- Зависит от Shared/StudUI, Shared/CatchRules, Shared/CatchThrow, Shared/CreatureMotion, Remotes, Config/GameConfig,
-- Config/Items, Config/Rarities, Config/UITokens, World/LovibumModel, Controllers/LovibumFxController.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local GuiService = game:GetService("GuiService")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local CatchRules = require(Shared:WaitForChild("CatchRules"))
local CatchThrow = require(Shared:WaitForChild("CatchThrow"))
local CreatureMotion = require(Shared:WaitForChild("CreatureMotion"))
local GameConfig = require(Config:WaitForChild("GameConfig"))
local Items = require(Config:WaitForChild("Items"))
local Rarities = require(Config:WaitForChild("Rarities"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Config:WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local LovibumModel = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("LovibumModel"))
local LovibumFx = require(script.Parent:WaitForChild("LovibumFxController"))

local T = UITokens.Catch
local Catch = GameConfig.Catch
local G = Catch.Game
local TH = Catch.Throw
local player = Players.LocalPlayer

local CatchController = {}

type Sample = { p: Vector2, t: number }
type Choice = { button: GuiButton, count: TextLabel }

local state: any = nil -- CatchState от сервера
local lovibums: any = {} -- запас (LovibumsChanged)
local kind = "Boom"
local hud: ScreenGui -- кнопки и подписи (в безопасной зоне экрана)
local screen: Frame -- всё, что в hud (в Studio можно сузить до экрана телефона: DevCatchScreen)
-- масштаб кнопок и подписей; touchMin — на касании не меньше (кнопка под палец, текст читается на телефоне)
local scales: { { scale: UIScale, touchMin: number? } } = {}
local aimGui: ScreenGui -- кольца и Ловибум (весь экран: координаты = координаты камеры)
type Ring = { holder: Frame, line: Frame, stroke: UIStroke, edge: UIStroke }
local outer: Ring
local inner: Ring
local vignette: Frame
local calm: { Instance } = {} -- эффекты света на время поимки (у этого клиента)
local hintPill: Frame
local hintText: TextLabel
local ball: Frame
local ballScale: UIScale
local ballView: ViewportFrame? = nil
local ballCamera: Camera? = nil
local ballKind: string? = nil
local title: TextLabel
local titleGradient: UIGradient?
local info: TextLabel
local kindButton: GuiButton
local kindPreviews: { [string]: ViewportFrame } = {}
local kindLabel: TextLabel
local choices: Frame
local choiceCards: { [string]: Choice } = {}
local cameraWas: { type: Enum.CameraType, fov: number }? = nil
local tween: { from: CFrame, start: number }? = nil
local controls: any = nil
local drag: { input: InputObject?, start: Vector2, samples: { Sample } }? = nil
local sentAt = -math.huge
local pendingUntil = -math.huge -- после броска Ловибума внизу нет, пока сервер не ответил
local note: { text: string, till: number }? = nil
local hiddenGuis: { ScreenGui } = {} -- HUD игры, спрятанный на время поимки
local hiddenLabels: { BillboardGui } = {} -- подписи предметов в мире
local shownAt = 0
local wasShown = false

local function now(): number
	return workspace:GetServerTimeNow()
end

local function smooth(x: number): number
	x = math.clamp(x, 0, 1)
	return x * x * (3 - 2 * x)
end

-- Положение ввода (координаты GUI под полосой Roblox) → координаты экрана камеры.
local function screenOf(input: InputObject): Vector2
	return Vector2.new(input.Position.X, input.Position.Y) + GuiService:GetGuiInset()
end

local function viewSize(): Vector2
	local camera = workspace.CurrentCamera
	return if camera then camera.ViewportSize else Vector2.new(1280, 720)
end

local function isTouch(): boolean
	return (GameConfig.DevMode and player:GetAttribute("DevTouch") == true)
		or (UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled)
end

-- Где лежит Ловибум (координаты экрана камеры) и его радиус в пикселях (на касании крупнее — под палец).
local function restPoint(): Vector2
	local v = viewSize()
	return Vector2.new(v.X / 2, v.Y * (0.5 + TH.BallY))
end

local function ballRadius(): number
	return math.max(viewSize().Y * (if isTouch() then T.BallTouch else T.Ball), T.BallMin) / 2
end

local function getControls(): any
	if controls == nil then
		local ok, result = pcall(function()
			local module = player:WaitForChild("PlayerScripts"):FindFirstChild("PlayerModule")
			return module and (require(module) :: any):GetControls()
		end)
		controls = if ok and result then result else false
	end
	return controls or nil
end

local function stock(k: string): number
	return if state then CatchRules.Stock(lovibums, state.boss, k) else 0
end

local function creaturePart(): BasePart?
	local part = state and state.part
	return if typeof(part) == "Instance" and part:IsA("BasePart") and part.Parent then part else nil
end

local function scaleOf(): number
	local def = state and Items[state.itemId]
	return if def then CreatureMotion.ScaleOf(def.size) else 1
end

local function chanceOf(k: string): number
	return if state.tutorial then 1 else CatchRules.Chance(state.rarity, k)
end

-- Можно бросать сейчас: мини-игра идёт, сервер разрешил, прошлый бросок обработан, Ловибум есть.
local function canThrow(): boolean
	return state ~= nil
		and state.state == "Aim"
		and now() >= (state.readyAt or 0)
		and now() >= pendingUntil
		and (state.tutorial or stock(kind) > 0)
end

local function say(text: string)
	note = { text = text, till = os.clock() + T.NoteTime }
	CatchController.Render()
end

-- ── Интерфейс ────────────────────────────────────────────────────────────────────────────────────────────────

-- 3D-превью Ловибума вида k во ViewportFrame; angle — откуда смотрит камера.
local function preview(parent: GuiObject, k: string, z: number, angle: Vector3, fit: number?): (ViewportFrame, Camera)
	local view = Instance.new("ViewportFrame")
	view.Name = "Apercu"
	view.BackgroundTransparency = 1
	view.Size = UDim2.fromScale(1, 1)
	view.Ambient = Color3.fromRGB(170, 170, 180)
	view.LightDirection = Vector3.new(-0.5, -1, -0.7)
	view.ZIndex = z
	view.Parent = parent
	local model = LovibumModel.Build(k)
	LovibumModel.Place(model, CFrame.new(), 0, 1, true)
	model.Parent = view
	local size, center = LovibumModel.Bounds(k)
	local camera = Instance.new("Camera")
	camera.FieldOfView = 30
	local dist = size.Magnitude / 2 / math.sin(math.rad(15)) * (fit or 1.05)
	camera.CFrame = CFrame.lookAt(center + angle.Unit * dist, center)
	camera.Parent = view
	view.CurrentCamera = camera
	return view, camera
end

-- Ловибум внизу экрана — вид kind (перестраивается при смене вида).
local function setBallKind(k: string)
	if ballKind == k then
		return
	end
	ballKind = k
	if ballView then
		ballView:Destroy()
	end
	local view, camera = preview(ball, k, 3, Vector3.new(0, 0.5, 1), T.BallFit)
	ballView, ballCamera = view, camera
end

-- Кольцо прицела: цветная линия поверх тёмного контура (видна на любом фоне); у цветного — лёгкая заливка (куда
-- бросать). Контур и линия — соседние рамки (ребёнок рисуется поверх родителя, поэтому не вложены).
local function ring(name: string, color: Color3, thickness: number, fill: boolean): Ring
	local holder = Instance.new("Frame")
	holder.Name = name
	holder.BackgroundTransparency = 1
	holder.AnchorPoint = Vector2.new(0.5, 0.5)
	holder.Size = UDim2.fromOffset(100, 100)
	holder.ZIndex = 2
	holder.Parent = aimGui
	local back = Instance.new("Frame")
	back.Name = "Contour"
	back.BackgroundTransparency = 1
	back.AnchorPoint = Vector2.new(0.5, 0.5)
	back.Position = UDim2.fromScale(0.5, 0.5)
	back.Size = UDim2.new(1, -2 * T.RingEdge, 1, -2 * T.RingEdge)
	back.ZIndex = 2
	back.Parent = holder
	UI.Corner(back, 9999)
	local edge = Instance.new("UIStroke")
	edge.Thickness = thickness + 2 * T.RingEdge
	edge.Color = T.RingDark
	edge.Parent = back
	local line = Instance.new("Frame")
	line.Name = "Trait"
	line.BackgroundColor3 = color
	line.BackgroundTransparency = if fill then T.RingFill else 1
	line.AnchorPoint = Vector2.new(0.5, 0.5)
	line.Position = UDim2.fromScale(0.5, 0.5)
	line.Size = UDim2.fromScale(1, 1)
	line.ZIndex = 3
	line.Parent = holder
	UI.Corner(line, 9999)
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = thickness
	stroke.Color = color
	stroke.Parent = line
	return { holder = holder, line = line, stroke = stroke, edge = edge }
end

-- Притемнённые края экрана (фон спокойнее, середина — как есть).
local function buildVignette()
	vignette = Instance.new("Frame")
	vignette.Name = "Vignette"
	vignette.BackgroundTransparency = 1
	vignette.Size = UDim2.fromScale(1, 1)
	vignette.ZIndex = 1
	vignette.Parent = aimGui
	local sides = {
		{ UDim2.fromScale(T.Vignette.Side, 1), UDim2.fromScale(0, 0), 0 },
		{ UDim2.fromScale(T.Vignette.Side, 1), UDim2.fromScale(1 - T.Vignette.Side, 0), 180 },
		{ UDim2.fromScale(1, T.Vignette.Top), UDim2.fromScale(0, 0), 90 },
		{ UDim2.fromScale(1, T.Vignette.Top), UDim2.fromScale(0, 1 - T.Vignette.Top), 270 },
	}
	for i, side in sides do
		local f = Instance.new("Frame")
		f.Name = "Bord" .. i
		f.BackgroundColor3 = Color3.new(0, 0, 0)
		f.BorderSizePixel = 0
		f.Size = side[1]
		f.Position = side[2]
		f.ZIndex = 1
		f.Parent = vignette
		local g = Instance.new("UIGradient")
		g.Rotation = side[3]
		g.Transparency = NumberSequence.new(T.Vignette.Edge, 1)
		g.Parent = f
	end
end

-- Свет на время поимки: дальний план размыт, существо и кольца в фокусе (только у этого клиента).
local function calmBackground(on: boolean)
	for _, x in calm do
		x:Destroy()
	end
	table.clear(calm)
	vignette.Visible = on
	if not on or typeof(state.camera) ~= "CFrame" or typeof(state.stage) ~= "Vector3" then
		return
	end
	local dof = Instance.new("DepthOfFieldEffect")
	dof.Name = "CaptureFocus"
	dof.FocusDistance = (state.camera.Position - state.stage).Magnitude
	dof.InFocusRadius = T.Focus.Radius
	dof.FarIntensity = T.Focus.Far
	dof.NearIntensity = 0
	dof.Parent = game:GetService("Lighting")
	table.insert(calm, dof)
end

-- Карточка вида в списке выбора (над кнопкой вида): превью и запас.
local function choiceCard(k: string, y: number)
	local size = T.KindButton
	local b = UI.Button(choices, {
		Name = "Lovibum_" .. k,
		Style = "Chunky",
		Theme = "gray",
		Size = size,
		Position = UDim2.fromOffset(size.X / 2, y),
		ZIndex = 5,
	})
	local holder = Instance.new("Frame")
	holder.Name = "Cadre"
	holder.BackgroundTransparency = 1
	holder.Size = UDim2.new(1, -8, 1, -30)
	holder.Position = UDim2.fromOffset(4, 2)
	holder.ZIndex = 8
	holder.Parent = b
	preview(holder, k, 8, Vector3.new(0.35, 0.4, 1))
	local count = UI.Text(b, "", {
		Name = "Stock",
		Size = UDim2.new(1, -8, 0, 24),
		Position = UDim2.new(0.5, 0, 1, -18),
		TextSize = 20,
		ZIndex = 9,
	})
	Motion.BindButton(b, 1.05, nil, function()
		if not state or stock(k) < 1 then
			Motion.Shake(b)
			return
		end
		kind = k
		choices.Visible = false
		CatchController.Render()
	end)
	choiceCards[k] = { button = b, count = count }
end

local function scaled(
	parent: Instance,
	name: string,
	size: Vector2,
	anchor: Vector2,
	position: UDim2,
	touchMin: number?
): Frame
	local f = Instance.new("Frame")
	f.Name = name
	f.BackgroundTransparency = 1
	f.Size = UDim2.fromOffset(size.X, size.Y)
	f.AnchorPoint = anchor
	f.Position = position
	f.Parent = parent
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = f
	table.insert(scales, { scale = scale, touchMin = touchMin })
	return f
end

-- Studio (DevMode): атрибут игрока DevCatchScreen = Vector3(ширина, высота, вырез) — интерфейс поимки как на экране
-- телефона: сужен до прямоугольника его пропорций во всю высоту окна, масштаб кнопок — как у StudMotion на таком
-- экране (× высота окна / высота телефона). Угол обзора камеры по вертикали тот же, поэтому снимок, обрезанный по этому
-- прямоугольнику, совпадает с экраном телефона (моделирование, не устройство). nil — обычный экран.
local function devScreen(): Vector3?
	local v = GameConfig.DevMode and player:GetAttribute("DevCatchScreen")
	return if typeof(v) == "Vector3" then v else nil
end

-- Масштаб кнопок и подписей (как StudMotion: по экрану; на касании «Уйти» не ниже MinTouch) и область экрана.
local function applyScreen()
	local dev = devScreen()
	local base, k = Motion.ScreenScale(), 1
	if dev then
		local view = viewSize()
		k = view.Y / dev.Y
		local width = (dev.X - 2 * dev.Z) * k
		screen.Size = UDim2.new(0, width, 1, 0)
		screen.Position = UDim2.new(0.5, -width / 2, 0, 0)
		base = math.clamp(math.min(dev.X / Motion.REFERENCE.X, dev.Y / Motion.REFERENCE.Y), 0.52, 1.18)
	else
		screen.Size = UDim2.fromScale(1, 1)
		screen.Position = UDim2.new()
	end
	local touch = isTouch()
	for _, entry in scales do
		local value = base
		if touch and entry.touchMin then
			value = math.max(value, entry.touchMin)
		end
		entry.scale.Scale = value * k
	end
end

local function build()
	-- кольца и Ловибум — на весь экран (без вставок): координаты совпадают с камерой
	aimGui = UI.ScreenGui("CaptureVisee", 13, { Menu = false, ScreenInsets = Enum.ScreenInsets.None })
	aimGui.Enabled = false
	aimGui.Parent = player:WaitForChild("PlayerGui")
	buildVignette()
	outer = ring("Anneau", T.OuterRing, T.OuterThickness, false)
	inner = ring("Cible", T.Difficulty[1].color, T.RingThickness, true)
	ball = Instance.new("Frame")
	ball.Name = "Lovibum"
	ball.BackgroundTransparency = 1
	ball.AnchorPoint = Vector2.new(0.5, 0.5)
	ball.Visible = false
	ball.ZIndex = 3
	ball.Parent = aimGui
	ballScale = Instance.new("UIScale")
	ballScale.Parent = ball
	-- короткая подсказка — отдельно, над Ловибумом (надписи касание не перехватывают)
	hintPill = UI.Pill(aimGui, "", {
		Name = "Aide",
		Height = T.HintHeight,
		TextSize = T.HintText,
		ZIndex = 6,
		AnchorPoint = Vector2.new(1, 0.5),
	})
	hintPill.Visible = false
	hintText = hintPill:FindFirstChild("Texte", true) :: TextLabel
	local hintScale = Instance.new("UIScale")
	hintScale.Parent = hintPill
	table.insert(scales, { scale = hintScale, touchMin = T.TouchText })

	hud = UI.ScreenGui("Capture", 14, { Menu = false, ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets })
	hud.Enabled = false
	hud.Parent = player:WaitForChild("PlayerGui")
	-- вверху по центру: компактная плашка — имя; редкость, шанс, броски (на тёмной подложке: читается над любым фоном)
	screen = Instance.new("Frame")
	screen.Name = "Ecran"
	screen.BackgroundTransparency = 1
	screen.Size = UDim2.fromScale(1, 1)
	screen.Parent = hud
	-- плашка — у самого верха по центру (aimGui без вставок: середина полосы Roblox свободна), чтобы прыжок-уклонение
	-- существа не уходил под неё
	local top = scaled(aimGui, "Haut", T.Panel, Vector2.new(0.5, 0), UDim2.new(0.5, 0, 0, T.PanelTop), T.TouchText)
	top.ZIndex = 5 -- над кольцами и Ловибумом (у прыгнувшего существа кольцо доходит до верха)
	UI.InsetBox(top, { Name = "Fond", Size = UDim2.fromScale(1, 1), Transparency = T.PanelTransparency, ZIndex = 4 })
	title = UI.Text(top, "", {
		Name = "Nom",
		Size = UDim2.new(1, -2 * T.PanelPad, 0, T.TitleText + 4),
		Position = UDim2.new(0.5, 0, 0, T.PanelPad + (T.TitleText + 4) / 2),
		TextSize = T.TitleText, -- размер — масштабом (UIScale), без автоподбора: на любом экране пропорционально
		Gradient = UITokens.ToColorSequence(UITokens.Rarity.Common),
		ZIndex = 6,
	})
	titleGradient = title:FindFirstChildOfClass("UIGradient")
	info = UI.Text(top, "", {
		Name = "Infos",
		Font = "Bold",
		Size = UDim2.new(1, -2 * T.PanelPad, 0, T.InfoText + 4),
		Position = UDim2.new(0.5, 0, 1, -T.PanelPad - (T.InfoText + 4) / 2),
		TextSize = T.InfoText,
		Rich = true,
		ZIndex = 6,
	})
	-- «Уйти» — слева вверху
	local left =
		scaled(screen, "Gauche", T.Leave, Vector2.zero, UDim2.fromOffset(T.Margin, T.Margin), T.MinTouch / T.Leave.Y)
	local leave = UI.Button(left, {
		Name = "Partir",
		Theme = "gray",
		Size = T.Leave,
		Position = UDim2.fromOffset(T.Leave.X / 2, T.Leave.Y / 2),
		Text = "Уйти",
		TextSize = 24,
		ZIndex = 5,
	})
	Motion.BindButton(leave, 1.05, nil, function()
		Remotes.Get(Remotes.Names.CatchAction):FireServer("Leave")
	end)
	-- справа внизу: кнопка вида (превью выбранного и запас), над ней — список видов
	local size = T.KindButton
	local stackH = 3 * size.Y + 3 * T.KindGap
	local corner = scaled(
		screen,
		"Coin",
		Vector2.new(size.X, size.Y + stackH),
		Vector2.new(1, 1),
		UDim2.new(1, -T.Margin, 1, -T.Margin)
	)
	kindButton = UI.Button(corner, {
		Name = "Type",
		Style = "Chunky",
		Theme = "green",
		Size = size,
		Position = UDim2.fromOffset(size.X / 2, stackH + size.Y / 2),
		ZIndex = 5,
	})
	local holder = Instance.new("Frame")
	holder.Name = "Cadre"
	holder.BackgroundTransparency = 1
	holder.Size = UDim2.new(1, -8, 1, -30)
	holder.Position = UDim2.fromOffset(4, 2)
	holder.ZIndex = 8
	holder.Parent = kindButton
	for _, k in Catch.Kinds do
		local view = preview(holder, k, 8, Vector3.new(0.35, 0.4, 1))
		view.Visible = false
		kindPreviews[k] = view
	end
	kindLabel = UI.Text(kindButton, "", {
		Name = "Stock",
		Size = UDim2.new(1, -8, 0, 24),
		Position = UDim2.new(0.5, 0, 1, -18),
		TextSize = 20,
		ZIndex = 9,
	})
	Motion.BindButton(kindButton, 1.05, nil, function()
		if state and not state.tutorial then
			choices.Visible = not choices.Visible
			CatchController.Render()
		end
	end)
	choices = Instance.new("Frame")
	choices.Name = "Choix"
	choices.BackgroundTransparency = 1
	choices.Size = UDim2.fromOffset(size.X, stackH)
	choices.Visible = false
	choices.Parent = corner
	for i, k in Catch.Kinds do
		choiceCard(k, (i - 1) * (size.Y + T.KindGap) + size.Y / 2)
	end
end

local function difficultyColor(chance: number): Color3
	for _, d in T.Difficulty do
		if chance >= d.at then
			return d.color
		end
	end
	return T.Difficulty[#T.Difficulty].color
end

function CatchController.Render()
	if not state then
		return
	end
	local def = Items[state.itemId]
	title.Text = if def then def.displayName else "Существо"
	-- длинное имя (до ~30 букв) — чуть мельче, чтобы влезло в плашку
	title.TextSize = if (utf8.len(title.Text) or 0) > T.LongName then T.TitleLong else T.TitleText
	if titleGradient then
		titleGradient.Color = UITokens.ToColorSequence(UITokens.Rarity[state.rarity] or UITokens.Rarity.Common)
	end
	local chance = chanceOf(kind)
	local throws = if state.max and state.max > 0
		then ("броски %d из %d"):format(math.max(state.max - state.throws, 0), state.max)
		else "учебная поимка"
	info.Text = ('%s   ·   шанс <font color="%s">%d %%</font>   ·   %s'):format(
		Rarities.Names[state.rarity] or "",
		UI.Colors.HighlightHex,
		math.floor(chance * 100 + 0.5),
		throws
	)
	-- подсказка над Ловибумом: коротко; после неудачного жеста — что исправить
	local text = if note and os.clock() < note.till
		then note.text
		elseif canThrow() then if isTouch()
			then "Смахните Ловибум вверх"
			else "Потяните Ловибум вверх и отпустите"
		elseif
			state.state == "Aim"
			and not state.tutorial
			and stock(kind) < 1
		then "Вид кончился — выберите справа"
		else ""
	hintText.Text = text
	hintPill.Visible = text ~= ""
	for k, view in kindPreviews do
		view.Visible = k == kind
	end
	kindLabel.Text = if state.tutorial then "учебный" else ("%s ×%d"):format(Catch.Names[kind], stock(kind))
	-- кончился выбранный вид — кнопка красная, но открывается (выбрать другой)
	UI.Recolor(kindButton, if state.tutorial or stock(kind) > 0 then "green" else "close")
	for k, card in choiceCards do
		local n = stock(k)
		card.count.Text = ("%s ×%d"):format(Catch.Names[k], n)
		UI.Recolor(card.button, if k == kind then "green" elseif n > 0 then "gray" else "close")
		UI.SetDisabled(card.button, n < 1)
	end
	if state.tutorial then
		choices.Visible = false
	end
	local color = difficultyColor(chance)
	inner.stroke.Color = color
	inner.line.BackgroundColor3 = color
	setBallKind(if state.tutorial then "Boom" else kind)
end

-- ── Бросок жестом ────────────────────────────────────────────────────────────────────────────────────────────

-- Жест из точек указателя: скорость и направление — за последние Window секунд движения (палец, замерший на миг перед
-- отпусканием — не дольше Grace, — не обнуляет скорость; дольше — медленный жест, не бросок), длина — от начала.
local function gestureOf(d: { start: Vector2, samples: { Sample } }, finish: Vector2, t: number): CatchThrow.Gesture
	local h = viewSize().Y
	local samples = d.samples
	local tEnd = t
	for i = #samples, 1, -1 do
		if (samples[i].p - finish).Magnitude > 2 then
			break
		end
		tEnd = samples[i].t -- указатель уже стоял здесь
	end
	if t - tEnd > TH.Grace then
		tEnd = t
	end
	local ref = samples[1]
	for i = #samples, 1, -1 do
		ref = samples[i]
		if tEnd - ref.t >= TH.Window then
			break
		end
	end
	local dt = tEnd - ref.t
	local v = if dt > 1 / 240 then (finish - ref.p) / dt else Vector2.zero
	local dir = if v.Magnitude > 1e-3 then v.Unit else Vector2.zero
	return { dx = dir.X, dy = dir.Y, speed = v.Magnitude / h, length = (finish - d.start).Magnitude / h }
end

local function release(finish: Vector2)
	local d = drag
	drag = nil
	if not d or not state then
		return
	end
	local raw = gestureOf(d, finish, os.clock())
	local g, why = CatchThrow.Parse(raw)
	if GameConfig.DevMode then
		print(
			("[CatchController] жест: dx %.2f, dy %.2f, скорость %.2f, длина %.2f, точек %d → %s"):format(
				raw.dx,
				raw.dy,
				raw.speed,
				raw.length,
				#d.samples,
				if g then "бросок" else tostring(why)
			)
		)
	end
	if not g then
		-- не бросок: Ловибум возвращается на место, ничего не тратится
		say(
			if why == "short"
				then "Жест короткий — смахните дальше"
				elseif why == "slow" then "Смахните быстрее"
				else "Смахните вверх, к существу"
		)
		return
	end
	local t = now()
	if not canThrow() or t - sentAt < 0.3 then
		return
	end
	sentAt = t
	pendingUntil = t + T.Pending
	local lovibum = if state.tutorial then "Boom" else kind
	Remotes.Get(Remotes.Names.CatchAction):FireServer("Throw", lovibum, g, t)
	-- полёт сразу, к той же точке, что посчитает сервер (исход — от сервера)
	local camera = workspace.CurrentCamera
	if camera and typeof(state.camera) == "CFrame" and typeof(state.stage) == "Vector3" then
		local ray = camera:ViewportPointToRay(finish.X, finish.Y)
		local size = LovibumModel.Bounds(lovibum)
		local across = 2 * math.tan(math.rad(camera.FieldOfView / 2)) * T.BallDepth -- стадов на высоту экрана
		LovibumFx.LocalThrow({
			lovibum = lovibum,
			from = ray.Origin + ray.Direction * T.BallDepth,
			fromScale = 2 * ballRadius() / viewSize().Y * across / math.max(size.X, size.Y, size.Z),
			aim = CatchThrow.Aim(state.camera, state.stage, g),
			release = t,
			arrival = t + G.FlightTime,
			part = state.part,
		})
	end
	ball.Visible = false
	wasShown = false
	CatchController.Render()
end

-- ── Вход и выход ─────────────────────────────────────────────────────────────────────────────────────────────

-- На время поимки экран — только поимка: HUD игры и подписи предметов в мире спрятаны (вернутся после).
local KEEP = {
	Capture = true,
	CaptureVisee = true,
	Toasts = true, -- уведомления сервера
	Tutoriel = true, -- прячется сам
	Chat = true,
	BubbleChat = true,
	ProximityPrompts = true,
	Freecam = true,
}

-- HUD, включившийся во время поимки (например, закрылось окно, открытое до неё), — тоже спрятать.
local function keepHudHidden()
	for _, g in player.PlayerGui:GetChildren() do
		if g:IsA("ScreenGui") and g.Enabled and not KEEP[g.Name] then
			g.Enabled = false
			if not table.find(hiddenGuis, g) then
				table.insert(hiddenGuis, g)
			end
		end
	end
end

local function hideWorldUi(hidden: boolean)
	if hidden then
		keepHudHidden()
		for _, d in workspace:GetDescendants() do
			if d:IsA("BillboardGui") and d.Enabled and d.Parent and d.Parent:GetAttribute("ItemId") ~= nil then
				d.Enabled = false
				table.insert(hiddenLabels, d)
			end
		end
		return
	end
	for _, g in hiddenGuis do
		if g.Parent then
			g.Enabled = true
		end
	end
	for _, d in hiddenLabels do
		local root = d.Parent
		if root and root:GetAttribute("CatchMode") ~= "Hidden" then
			d.Enabled = true
		end
	end
	table.clear(hiddenGuis)
	table.clear(hiddenLabels)
end

-- Свой персонаж на время поимки не виден (взгляд от первого лица).
local function hideCharacter(hidden: boolean)
	local character = player.Character
	if not character then
		return
	end
	for _, d in character:GetDescendants() do
		if d:IsA("BasePart") or d:IsA("Decal") then
			(d :: any).LocalTransparencyModifier = if hidden then 1 else 0
		end
	end
end

local function enter()
	local camera = workspace.CurrentCamera
	if not cameraWas and camera then
		cameraWas = { type = camera.CameraType, fov = camera.FieldOfView }
		camera.CameraType = Enum.CameraType.Scriptable
		tween = { from = camera.CFrame, start = os.clock() }
	end
	local c = getControls()
	if c then
		c:Disable()
	end
	UserInputService.ModalEnabled = true -- на телефоне — без джойстика и прыжка (жест не крутит камеру)
	hideCharacter(true)
	hideWorldUi(true)
	calmBackground(true)
	if state.tutorial then
		kind = "Boom" -- учебный Ловибум
	elseif stock(kind) < 1 then
		kind = "Boom"
		for _, k in Catch.Kinds do
			if stock(k) > 0 and stock(kind) < 1 then
				kind = k
			end
		end
	end
	choices.Visible = false
	sentAt, pendingUntil, wasShown = -math.huge, -math.huge, false
	hud.Enabled = true
	aimGui.Enabled = true
end

local function exit()
	drag = nil
	hud.Enabled = false
	aimGui.Enabled = false
	local camera = workspace.CurrentCamera
	if cameraWas and camera then
		camera.CameraType = Enum.CameraType.Custom
		camera.FieldOfView = cameraWas.fov
	end
	cameraWas, tween = nil, nil
	local c = getControls()
	if c then
		c:Enable()
	end
	UserInputService.ModalEnabled = false
	hideCharacter(false)
	hideWorldUi(false)
	calmBackground(false)
end

local function step(dt: number)
	if not state then
		return
	end
	local camera = workspace.CurrentCamera
	if not camera then
		return
	end
	-- камера: подлёт к камере поимки (её посчитал сервер), дальше — неподвижна
	local want = state.camera
	if typeof(want) == "CFrame" then
		camera.CameraType = Enum.CameraType.Scriptable
		camera.FieldOfView = G.Camera.FOV
		if tween then
			local f = smooth((os.clock() - tween.start) / G.Camera.Tween)
			camera.CFrame = tween.from:Lerp(want, f)
			if f >= 1 then
				tween = nil
			end
		else
			camera.CFrame = want
		end
	end
	applyScreen()
	-- координаты камеры → координаты внутри aimGui (его AbsolutePosition отсчитан от низа полосы Roblox)
	local origin = aimGui.AbsolutePosition + GuiService:GetGuiInset()
	local ready = canThrow()
	-- кольца вокруг существа: белое — наибольшее, цветное — сейчас (размер — как у сервера)
	local part = creaturePart()
	if part then
		local center = part.Position
		local factor = state.circle or 1
		local p0, on = camera:WorldToViewportPoint(center)
		local right = camera.CFrame.RightVector
		local function px(r: number): number
			local p1 = camera:WorldToViewportPoint(center + right * r)
			return (Vector2.new(p1.X, p1.Y) - Vector2.new(p0.X, p0.Y)).Magnitude
		end
		local big = px(G.Circle.Max * scaleOf() * factor)
		local now_ = px(CatchRules.CircleRadius(now(), state.since, scaleOf(), factor))
		local pos = UDim2.fromOffset(p0.X - origin.X, p0.Y - origin.Y)
		outer.holder.Visible, inner.holder.Visible = on, on
		outer.holder.Position, inner.holder.Position = pos, pos
		outer.holder.Size = UDim2.fromOffset(big * 2, big * 2)
		inner.holder.Size = UDim2.fromOffset(now_ * 2, now_ * 2)
		-- пока Ловибум в деле — кольца бледные (бросать нельзя)
		outer.stroke.Transparency = if ready then T.OuterTransparency else T.WaitTransparency
		outer.edge.Transparency = if ready then T.RingDarkTransparency else T.WaitTransparency
		inner.stroke.Transparency = if ready then 0 else T.WaitTransparency
		inner.edge.Transparency = if ready then T.RingDarkTransparency else T.WaitTransparency
		inner.line.BackgroundTransparency = if ready then T.RingFill else 1
	else
		outer.holder.Visible, inner.holder.Visible = false, false
	end
	-- Ловибум внизу: идёт за указателем, иначе лежит и чуть покачивается; появляется, когда можно бросать
	local r = ballRadius()
	ball.Size = UDim2.fromOffset(r * 2, r * 2)
	if drag then
		local last = drag.samples[#drag.samples].p
		ball.Position = UDim2.fromOffset(last.X - origin.X, last.Y - origin.Y)
		ball.Visible = true
	else
		if ready and not wasShown then
			shownAt = os.clock()
		end
		wasShown = ready
		ball.Visible = ready
		local rest = restPoint()
		local bob = math.sin(os.clock() * T.BobSpeed) * r * T.Bob
		ball.Position = UDim2.fromOffset(rest.X - origin.X, rest.Y - origin.Y + bob)
	end
	ballScale.Scale = 0.6 + 0.4 * smooth((os.clock() - shownAt) / 0.25)
	local rest = restPoint()
	-- подсказка — слева от Ловибума, в одну строку с ним (не пересекает кольцо и путь броска)
	hintPill.AnchorPoint = Vector2.new(1, 0.5)
	hintPill.Position = UDim2.fromOffset(rest.X - r - T.HintGap - origin.X, rest.Y - origin.Y)
	if rest.X - r - T.HintGap - hintPill.AbsoluteSize.X < T.Margin then
		-- узкий экран: слева не помещается — над Ловибумом
		hintPill.AnchorPoint = Vector2.new(0.5, 1)
		hintPill.Position = UDim2.fromOffset(rest.X - origin.X, rest.Y - r - T.HintGap - origin.Y)
	end
	if ballCamera and ballKind then
		local size, center = LovibumModel.Bounds(ballKind)
		local a = os.clock() * T.BallSpin
		local dir = Vector3.new(math.sin(a), 0.5, math.cos(a)).Unit
		local dist = size.Magnitude / 2 / math.sin(math.rad(15)) * T.BallFit
		ballCamera.CFrame = CFrame.lookAt(center + dir * dist, center)
	end
	if math.floor(os.clock() * 4) ~= math.floor((os.clock() - dt) * 4) then
		keepHudHidden()
		CatchController.Render()
	end
end

function CatchController.Init()
	build()
	Remotes.Get(Remotes.Names.CatchState).OnClientEvent:Connect(function(payload)
		local was = state
		state = if type(payload) == "table" then payload else nil
		pendingUntil = -math.huge -- сервер ответил: Ловибум внизу — по его readyAt
		if state and not was then
			enter()
		elseif not state and was then
			exit()
		end
		if state then
			CatchController.Render()
		end
	end)
	Remotes.Get(Remotes.Names.LovibumsChanged).OnClientEvent:Connect(function(payload)
		if type(payload) == "table" and type(payload.lovibums) == "table" then
			lovibums = payload.lovibums
			if state then
				CatchController.Render()
			end
		end
	end)
	UserInputService.InputBegan:Connect(function(input, processed)
		if not state or processed or drag then
			return
		end
		local t = input.UserInputType
		if t ~= Enum.UserInputType.MouseButton1 and t ~= Enum.UserInputType.Touch then
			return
		end
		local p = screenOf(input)
		-- Ловибум берут рукой: жест начинается на нём (с запасом вокруг)
		local grab = ballRadius() * (if isTouch() then T.GrabTouch else T.Grab)
		if not canThrow() or (p - restPoint()).Magnitude > grab then
			return
		end
		choices.Visible = false
		drag = {
			input = if t == Enum.UserInputType.Touch then input else nil,
			start = p,
			samples = { { p = p, t = os.clock() } },
		}
	end)
	UserInputService.InputChanged:Connect(function(input)
		local d = drag
		if
			d
			and d.input == nil
			and input.UserInputType == Enum.UserInputType.MouseMovement
			and not UserInputService:IsMouseButtonPressed(Enum.UserInputType.MouseButton1)
		then
			drag = nil -- кнопку отпустили вне окна: жест отменён
			return
		end
		if d and (input == d.input or (d.input == nil and input.UserInputType == Enum.UserInputType.MouseMovement)) then
			local t = os.clock()
			table.insert(d.samples, { p = screenOf(input), t = t })
			while #d.samples > 2 and t - d.samples[1].t > 0.5 do
				table.remove(d.samples, 1)
			end
		end
	end)
	UserInputService.InputEnded:Connect(function(input)
		local d = drag
		if not d then
			return
		end
		if input == d.input or (d.input == nil and input.UserInputType == Enum.UserInputType.MouseButton1) then
			if input.UserInputState == Enum.UserInputState.Cancel then
				drag = nil -- касание отменено системой — не бросок
				return
			end
			release(screenOf(input))
		end
	end)
	UserInputService.WindowFocusReleased:Connect(function()
		drag = nil -- окно потеряло фокус посреди жеста — не бросок
	end)
	RunService.RenderStepped:Connect(step)
end

return CatchController

-- Мини-игра поимки «Ловибум» на клиенте ловящего (D55, Stud-UI). Сервер прислал CatchState — режим поимки: камера
-- плавно к существу (фон — настоящая локация), управление персонажем выключено (на телефоне — и экранные кнопки),
-- вокруг существа — сжимающийся круг (тот же, что считает сервер: Shared/CatchRules.CircleRadius; зелёный — можно
-- бросать, серый — летит прошлый бросок), внизу — выбор вида (Бум, Турбо, Мега уровня этого босса и запас каждого;
-- в обучении — один учебный), счётчик бросков, шанс захвата выбранным видом, «Уйти». Бросок — жест мышью или пальцем:
-- зажать внизу и провести вверх к существу; направление — куда полетит, длина — сила (короче — недолёт, длиннее —
-- перелёт). Точка прилёта (на вертикальной плоскости через существо) и время отпускания уходят серверу — исход решает
-- он. CatchState = nil — конец: камера и управление вернулись. Эффекты броска для всех — LovibumFxController.
-- Зависит от Shared/StudUI, Shared/CatchRules, Shared/CreatureMotion, Remotes, Config/GameConfig, Config/UITokens,
-- World/LovibumModel.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local GuiService = game:GetService("GuiService")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local CatchRules = require(Shared:WaitForChild("CatchRules"))
local CreatureMotion = require(Shared:WaitForChild("CreatureMotion"))
local GameConfig = require(Config:WaitForChild("GameConfig"))
local Items = require(Config:WaitForChild("Items"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Config:WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local LovibumModel = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("LovibumModel"))

local T = UITokens.Catch
local Catch = GameConfig.Catch
local G = Catch.Game
local player = Players.LocalPlayer

local CatchController = {}

local state: any = nil -- CatchState от сервера
local lovibums: any = {} -- запас (LovibumsChanged)
local kind = "Boom"
local gui: ScreenGui
local circle: Frame
local circleStroke: UIStroke
local bottom: Frame
local kindButtons: { [string]: { button: GuiButton, count: TextLabel } } = {}
local info: TextLabel
local hint: TextLabel
local leaveButton: GuiButton
local cameraWas: { type: Enum.CameraType, cf: CFrame }? = nil
local controls: any = nil
local drag: { input: InputObject?, start: Vector2, now: Vector2 }? = nil
local sentAt = -math.huge

local function now(): number
	return workspace:GetServerTimeNow()
end

-- Положение ввода (без полосы Roblox сверху) → координаты экрана камеры (ViewportPointToRay).
local function viewportOf(input: InputObject): Vector2
	return Vector2.new(input.Position.X, input.Position.Y) + GuiService:GetGuiInset()
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

-- ── Интерфейс ────────────────────────────────────────────────────────────────────────────────────────────────

local function kindCard(k: string, x: number)
	local size = T.KindButton
	local b = UI.Button(bottom, {
		Name = "Lovibum_" .. k,
		Style = "Chunky",
		Theme = "gray",
		Size = size,
		Position = UDim2.fromOffset(x, size.Y / 2),
		ZIndex = 5,
	})
	local view = Instance.new("ViewportFrame")
	view.Name = "Apercu"
	view.BackgroundTransparency = 1
	view.Size = UDim2.new(1, -8, 1, -30)
	view.Position = UDim2.fromOffset(4, 2)
	view.Ambient = Color3.fromRGB(170, 170, 180)
	view.LightDirection = Vector3.new(-0.5, -1, -0.7)
	view.ZIndex = 8
	view.Parent = b
	local model = LovibumModel.Build(k)
	LovibumModel.Place(model, CFrame.new(), 0, 1, true)
	model.Parent = view
	local lsize, center = LovibumModel.Bounds(k)
	local camera = Instance.new("Camera")
	camera.FieldOfView = 30
	local dist = lsize.Magnitude / 2 / math.sin(math.rad(15)) * 1.05
	camera.CFrame = CFrame.lookAt(center + Vector3.new(0.35, 0.4, 1).Unit * dist, center)
	camera.Parent = view
	view.CurrentCamera = camera
	local count = UI.Text(b, "", {
		Name = "Stock",
		Size = UDim2.new(1, -8, 0, 24),
		Position = UDim2.new(0.5, 0, 1, -18),
		TextSize = 20,
		ZIndex = 9,
	})
	Motion.BindButton(b, 1.05, nil, function()
		if state and not state.tutorial and stock(k) < 1 then
			Motion.Shake(b)
			return
		end
		kind = k
		CatchController.Render()
	end)
	kindButtons[k] = { button = b, count = count }
end

local function build()
	gui = UI.ScreenGui("Capture", 14, { Menu = false })
	gui.Enabled = false
	gui.Parent = player:WaitForChild("PlayerGui")
	circle = Instance.new("Frame")
	circle.Name = "Cercle"
	circle.BackgroundTransparency = 1
	circle.AnchorPoint = Vector2.new(0.5, 0.5)
	circle.Size = UDim2.fromOffset(100, 100)
	circle.Parent = gui
	UI.Corner(circle, 9999)
	circleStroke = Instance.new("UIStroke")
	circleStroke.Thickness = T.CircleThickness
	circleStroke.Transparency = T.CircleTransparency
	circleStroke.Color = T.CircleReady
	circleStroke.Parent = circle
	-- низ: выбор вида и подписи (одна WindowScale)
	bottom = Instance.new("Frame")
	bottom.Name = "Bas"
	bottom.BackgroundTransparency = 1
	local width = 3 * T.KindButton.X + 2 * T.KindGap
	bottom.Size = UDim2.fromOffset(width, T.KindButton.Y + 70)
	bottom.AnchorPoint = Vector2.new(0.5, 1)
	bottom.Position = UDim2.new(0.5, 0, 1, -T.BottomMargin)
	bottom.Parent = gui
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = bottom
	Motion.BindResponsive(scale)
	for i, k in Catch.Kinds do
		kindCard(k, T.KindButton.X / 2 + (i - 1) * (T.KindButton.X + T.KindGap))
	end
	info = UI.Text(bottom, "", {
		Name = "Infos",
		Font = "Bold",
		Size = UDim2.fromOffset(width + 200, 28),
		Position = UDim2.fromOffset(width / 2, T.KindButton.Y + 20),
		TextSize = T.InfoText,
		Rich = true,
		ZIndex = 5,
	})
	hint = UI.Text(bottom, "", {
		Name = "Aide",
		Font = "Bold",
		Size = UDim2.fromOffset(width + 260, 28),
		Position = UDim2.fromOffset(width / 2, T.KindButton.Y + 52),
		TextSize = T.HintText,
		Color = UI.Colors.Secondary,
		ZIndex = 5,
	})
	-- «Уйти» — справа вверху, ниже кнопок Roblox
	local top = Instance.new("Frame")
	top.Name = "Haut"
	top.BackgroundTransparency = 1
	top.Size = UDim2.fromOffset(T.Leave.X, T.Leave.Y)
	top.AnchorPoint = Vector2.new(1, 0)
	top.Position = UDim2.new(1, -16, 0, 16)
	top.Parent = gui
	local topScale = Instance.new("UIScale")
	topScale.Name = "WindowScale"
	topScale.Parent = top
	Motion.BindResponsive(topScale)
	leaveButton = UI.Button(top, {
		Name = "Partir",
		Theme = "gray",
		Size = T.Leave,
		Position = UDim2.fromOffset(T.Leave.X / 2, T.Leave.Y / 2),
		Text = "Уйти",
		TextSize = 24,
		ZIndex = 5,
	})
	Motion.BindButton(leaveButton, 1.05, nil, function()
		Remotes.Get(Remotes.Names.CatchAction):FireServer("Leave")
	end)
end

function CatchController.Render()
	if not state then
		return
	end
	local ready = now() >= (state.readyAt or 0) and state.state == "Aim"
	for _, k in Catch.Kinds do
		local entry = kindButtons[k]
		local visible = not state.tutorial or k == "Boom"
		entry.button.Visible = visible
		local n = stock(k)
		entry.count.Text = if state.tutorial then "учебный" else ("%s ×%d"):format(Catch.Names[k], n)
		UI.Recolor(entry.button, if k == kind then "green" elseif state.tutorial or n > 0 then "gray" else "close")
		UI.SetDisabled(entry.button, not state.tutorial and n < 1)
	end
	local chance = if state.tutorial then 1 else CatchRules.Chance(state.rarity, kind)
	local throws = if state.max and state.max > 0
		then ("Бросок %d из %d"):format(math.min(state.throws + 1, state.max), state.max)
		else "Учебная поимка"
	info.Text = ('%s   ·   шанс захвата: <font color="%s">%d %%</font>'):format(
		throws,
		UI.Colors.HighlightHex,
		math.floor(chance * 100 + 0.5)
	)
	local touch = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
	hint.Text = if not ready
		then "Ловибум летит…"
		elseif
			touch
		then "Проведите пальцем вверх к существу — отпустите, когда оно в круге"
		else "Зажмите мышь внизу и потяните вверх к существу — отпустите, когда оно в круге"
end

-- ── Бросок жестом ────────────────────────────────────────────────────────────────────────────────────────────

-- Точка прилёта по жесту: направление — к существу, длина — сила (недолёт ниже, перелёт выше); на вертикальной
-- плоскости через центр существа, перпендикулярной взгляду камеры.
local function aimFrom(start: Vector2, finish: Vector2): Vector3?
	local camera = workspace.CurrentCamera
	local part = creaturePart()
	if not camera or not part then
		return nil
	end
	local view = camera.ViewportSize
	local swipe = finish - start
	if -swipe.Y < view.Y * T.MinSwipe then
		return nil -- не вверх или слишком коротко
	end
	local center = part.Position
	local screen = camera:WorldToViewportPoint(center)
	-- продолжение жеста до высоты существа на экране
	local k = (start.Y - screen.Y) / -swipe.Y
	local x = start.X + swipe.X * k
	local power = swipe.Magnitude / view.Y
	local y = screen.Y + (T.Power - power) * view.Y * T.PowerSpread
	local ray = camera:ViewportPointToRay(x, y)
	local normal = Vector3.new(camera.CFrame.LookVector.X, 0, camera.CFrame.LookVector.Z)
	if normal.Magnitude < 1e-3 then
		return nil
	end
	normal = normal.Unit
	local denom = ray.Direction:Dot(normal)
	if math.abs(denom) < 1e-4 then
		return nil
	end
	local t = (center - ray.Origin):Dot(normal) / denom
	local aim = ray.Origin + ray.Direction * t
	local home = part:GetAttribute("Home")
	local anchor = if typeof(home) == "CFrame" then home.Position else center
	local offset = aim - anchor
	if offset.Magnitude > G.AimRange - 0.5 then
		aim = anchor + offset.Unit * (G.AimRange - 0.5)
	end
	return aim
end

local function release(finish: Vector2)
	local d = drag
	drag = nil
	if not d or not state or state.state ~= "Aim" then
		return
	end
	local t = now()
	if t < (state.readyAt or 0) or t - sentAt < 0.3 then
		return
	end
	if not state.tutorial and stock(kind) < 1 then
		return
	end
	local aim = aimFrom(d.start, finish)
	if not aim then
		return
	end
	sentAt = t
	Remotes.Get(Remotes.Names.CatchAction):FireServer("Throw", kind, aim, t)
end

-- ── Вход и выход ─────────────────────────────────────────────────────────────────────────────────────────────

local function enter()
	local camera = workspace.CurrentCamera
	if not cameraWas and camera then
		cameraWas = { type = camera.CameraType, cf = camera.CFrame }
		camera.CameraType = Enum.CameraType.Scriptable
	end
	local c = getControls()
	if c then
		c:Disable()
	end
	UserInputService.ModalEnabled = true -- на телефоне — без джойстика и прыжка (жест не крутит камеру)
	if state.tutorial or stock(kind) < 1 then
		kind = "Boom"
		for _, k in Catch.Kinds do
			if stock(k) > 0 and stock(kind) < 1 then
				kind = k
			end
		end
	end
	gui.Enabled = true
end

local function exit()
	drag = nil
	gui.Enabled = false
	local camera = workspace.CurrentCamera
	if cameraWas and camera then
		camera.CameraType = Enum.CameraType.Custom
	end
	cameraWas = nil
	local c = getControls()
	if c then
		c:Enable()
	end
	UserInputService.ModalEnabled = false
end

local function step(dt: number)
	if not state then
		return
	end
	local camera = workspace.CurrentCamera
	local part = creaturePart()
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not camera or not part then
		return
	end
	-- камера: за игроком и чуть выше, смотрит на существо; догоняет его плавно
	local center = part.Position
	local from = if root then root.Position else center + Vector3.new(0, 0, 8)
	local flat = Vector3.new(from.X - center.X, 0, from.Z - center.Z)
	flat = if flat.Magnitude > 0.1 then flat.Unit else Vector3.new(0, 0, 1)
	local wantPos = center + flat * G.Camera.Distance + Vector3.new(0, G.Camera.Height, 0)
	local want = CFrame.lookAt(wantPos, center + Vector3.new(0, 0.3, 0))
	camera.CFrame = camera.CFrame:Lerp(want, math.clamp(dt * T.CameraLerp, 0, 1))
	-- круг: радиус сервера (в стадах) → пиксели у центра существа
	local t = now()
	local radius = CatchRules.CircleRadius(t, state.since, scaleOf(), state.circle or 1)
	local p0, on = camera:WorldToViewportPoint(center)
	local p1 = camera:WorldToViewportPoint(center + camera.CFrame.RightVector * radius)
	local origin = gui.AbsolutePosition -- ScreenGui без полосы Roblox (IgnoreGuiInset): сдвиг — только безопасная зона
	local px = (Vector2.new(p1.X, p1.Y) - Vector2.new(p0.X, p0.Y)).Magnitude
	circle.Visible = on
	circle.Position = UDim2.fromOffset(p0.X - origin.X, p0.Y - origin.Y)
	circle.Size = UDim2.fromOffset(px * 2, px * 2)
	local ready = t >= (state.readyAt or 0) and state.state == "Aim"
	circleStroke.Color = if ready then T.CircleReady else T.CircleWait
	if math.floor(t * 4) ~= math.floor((t - dt) * 4) then
		CatchController.Render()
	end
end

function CatchController.Init()
	build()
	Remotes.Get(Remotes.Names.CatchState).OnClientEvent:Connect(function(payload)
		local was = state
		state = if type(payload) == "table" then payload else nil
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
		if not state or processed then
			return
		end
		local t = input.UserInputType
		if t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.Touch then
			local p = viewportOf(input)
			drag = { input = if t == Enum.UserInputType.Touch then input else nil, start = p, now = p }
		end
	end)
	UserInputService.InputChanged:Connect(function(input)
		if
			drag
			and (input == drag.input or (drag.input == nil and input.UserInputType == Enum.UserInputType.MouseMovement))
		then
			drag.now = viewportOf(input)
		end
	end)
	UserInputService.InputEnded:Connect(function(input)
		if not drag then
			return
		end
		if input == drag.input or (drag.input == nil and input.UserInputType == Enum.UserInputType.MouseButton1) then
			release(viewportOf(input))
		end
	end)
	RunService.RenderStepped:Connect(step)
end

return CatchController

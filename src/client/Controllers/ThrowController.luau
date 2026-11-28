-- Бросок вдаль у бросающего (D75) — по записи референса владельца (2026-11-28), порядок сцен тот же: игрок выходит
-- на полосу у края обрыва → короткое затемнение, камера близко за плечом, интерфейс скрыт, шкала (бегунок ведётся по
-- времени сервера) → нажатие в любом месте экрана → «+N Мощность», «Идеально!», чёрные поля, замах и бросок (камера
-- облетает спереди и возвращается за спину) → полёт Ловибума над трассой (камера-погоня, сверху «1.35X / Удача» и
-- название зоны) → удар → затемнение → низкая дальняя камера медленно наезжает на Ловибум, сверху «1 из N», слева
-- выходит монстр, имя открывается по буквам → «Удача!», вспышка, лучи, столб света, карточка (редкость этажа, имя,
-- доход, «Новинка!») → монстра втягивает в Ловибум (решение владельца: монстр попадает в Ловибум), тот
-- захлопывается → белая вспышка, игрок снова у края с капсулой в руках.
-- Результат решает сервер (ThrowAction → ThrowState / ThrowResult); здесь только показ. Всё движение считается каждый
-- кадр по времени (кривые и пружины), склеек, кроме затемнений, нет. Бросается Ловибум старшего уровня, до зоны
-- которого игрок добивает (выбора на экране броска нет — как в записи).
-- Зависит от ThrowHud, ThrowPath, ThrowPose, LovibumModel, Util/Spring, Shared/ThrowRules, CatchRules, GameTime,
-- Config (GameConfig, Items, FloorRarity, UITokens, Catch, LovibumRigs), Remotes.

local Debris = game:GetService("Debris")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local Items = require(Config:WaitForChild("Items"))
local FloorRarity = require(Config:WaitForChild("FloorRarity"))
local UITokens = require(Config:WaitForChild("UITokens"))
local Catch = require(Config:WaitForChild("Catch"))
local LovibumRigs = require(Config:WaitForChild("LovibumRigs"))
local CatchRules = require(Shared:WaitForChild("CatchRules"))
local GameTime = require(Shared:WaitForChild("GameTime"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local ThrowRules = require(Shared:WaitForChild("ThrowRules"))

local Client = script.Parent.Parent
local LovibumModel = require(Client:WaitForChild("World"):WaitForChild("LovibumModel"))
local ThrowPath = require(Client:WaitForChild("World"):WaitForChild("ThrowPath"))
local ThrowPose = require(Client:WaitForChild("World"):WaitForChild("ThrowPose"))
local Spring = require(Client:WaitForChild("Util"):WaitForChild("Spring"))
local ThrowHud = require(Client:WaitForChild("UI"):WaitForChild("ThrowHud"))
local ZoneController = require(script.Parent:WaitForChild("ZoneController"))

local Throw = GameConfig.Throw
local Show = Throw.Show
local player = Players.LocalPlayer

local ThrowController = {}

-- Числа камеры и сцен (стады, градусы). Вид интерфейса — UITokens.Throw, времена — Throw.Show.
local C = {
	AimEye = Vector3.new(1.3, 2.2, 4.6), -- близко за правым плечом (от корня персонажа; трасса — в −Z)
	AimLook = Vector3.new(1.3, -5, -40), -- вниз, в каньон трассы
	AimFov = 70,
	FrontAngle = 152, -- градусов вокруг персонажа: 0 — за спиной, 180 — спереди
	BackAngle = 8,
	FrontFov = 52,
	ReleaseFov = 84,
	ChaseEye = Vector3.new(0, 4.6, 12), -- от Ловибума: над и позади
	ChaseLook = Vector3.new(0, -1, -18),
	ChaseFov = 80,
	SideEye = Vector3.new(0.5, 3.4, 9), -- после удара: камера оседает за Ловибумом
	SideLook = Vector3.new(0, 0.6, -2),
	-- раскрытие: камера смотрит назад, к обрыву (+Z); слева на экране — +X
	FarEye = Vector3.new(1.5, 0.7, -26),
	NearEye = Vector3.new(1.2, 0.8, -7.5),
	NearLook = Vector3.new(1.0, 1.2, 0),
	MidEye = Vector3.new(2.6, 1.7, -14),
	MidLook = Vector3.new(2.4, 1.6, 0),
	SuckEye = Vector3.new(1.8, 1.5, -9),
	SuckLook = Vector3.new(1.0, 1.4, 0),
	RevealFov = 55,
	SuckFov = 47,
	CardEye = Vector3.new(-1.2, 2.7, -15), -- полное шоу, карточка: существо крупно — чуть больше трети высоты экрана
	CardLook = Vector3.new(-0.8, 2.6, 0), -- от места существа
	CardFov = 50,
	ShortEye = Vector3.new(2, 2.6, 10.5), -- обычный результат: со стороны полёта, Ловибум и существо в кадре
	ShortLook = Vector3.new(2, 1.8, 0), -- от Ловибума
	ShortFov = 58,
	MonsterFrom = Vector3.new(7, 0, -16), -- откуда выходит монстр (от Ловибума): из-за левого края кадра
	Hidden = Vector3.new(0, -300, 0), -- где монстр ждёт выхода (не виден)
	MonsterGap = 1.6, -- зазор между монстром и Ловибумом
	Hops = 6,
	SlideLength = 3,
	Bank = 2, -- крен камеры в полёте, градусов
}

type Stack = { level: number, kind: string, count: number }

local lovibums: any = {}
local armed = true -- шкала появится при выходе на полосу (после отказа или показа — только с нового захода)
local retries = 0 -- повторные просьбы шкалы за один заход на полосу
local state = "Idle" -- Idle | Starting | Aim | Pressed | Show
local stateAt = 0
local clock = 0
local session: any = nil -- ThrowState от сервера
local result: any = nil -- ThrowResult

local controls: any = nil
local hidden: { [LayerCollector]: boolean } = {}
local cameraWas: { fov: number }? = nil
local eye = Spring.new(Vector3.zero, 14)
local look = Spring.new(Vector3.zero, 16)
local fov = Spring.new(70, 10)
local shake = Spring.new(Vector3.zero, 22)
local roll = 0

local pose: any = nil
local origin = Vector3.zero -- корень персонажа на полосе
local ball: Model? = nil -- Ловибум показа
local ballKind = "Boom"
local monster: Model? = nil
local monsterInfo: any = nil
local fxFolder: Folder? = nil
local fx: { (number) -> boolean } = {} -- эффекты: шаг(dt) → false, когда закончился
local scene: any = nil -- текущая сцена показа: { name, t, ... }
local lastZone = 0
local selectedKind: string = Catch.Kinds[1] -- вид с панели у края; по умолчанию Бум: дорогие виды сами не тратятся
local walkWas: number? = nil -- скорость персонажа до шкалы (на шкале он стоит)
local released = false -- игрок отпустил движение после выхода на полосу: новое движение — отмена шкалы
local movedFor = 0
local kindsAt = 0

-- ── кривые ──────────────────────────────────────────────────────────────────────────────────────────────────────────
local function smooth(t: number): number
	local x = math.clamp(t, 0, 1)
	return x * x * (3 - 2 * x)
end
local function easeIn(t: number): number
	local x = math.clamp(t, 0, 1)
	return x * x * x
end
local function easeOut(t: number): number
	local x = 1 - math.clamp(t, 0, 1)
	return 1 - x * x * x
end
local function backOut(t: number): number
	local x = math.clamp(t, 0, 1) - 1
	return 1 + x * x * (2.7 * x + 1.7)
end
local function mix(a: number, b: number, t: number): number
	return a + (b - a) * t
end

-- ── какой Ловибум бросать ───────────────────────────────────────────────────────────────────────────────────────────
-- Ловибум вида kind: старший уровень, до зоны которого игрок добивает (ThrowRules.SuggestLevel); нет такого —
-- младший из запаса этого вида. Вид выбирает игрок на панели у края (по умолчанию Бум) — сам дорогой не тратится.
local function pickFor(kind: string): Stack?
	local reach = ThrowRules.SuggestLevel(player:GetAttribute("Strength") or 0)
	local best: Stack? = nil
	local lowest: Stack? = nil
	for level = 1, #GameConfig.Zones do
		local n = CatchRules.Stock(lovibums, level, kind)
		if n > 0 then
			local stack = { level = level, kind = kind, count = n }
			lowest = lowest or stack
			if level <= reach then
				best = stack
			end
		end
	end
	return best or lowest
end

-- Редкий результат — полное шоу; обычный — коротко (Throw.Show.FullFloors, FullCreatures, босс).
local function isFull(r: any): boolean
	-- в Studio атрибут игрока ThrowFullShow включает полное шоу для любого результата (проверка сцен)
	if RunService:IsStudio() and player:GetAttribute("ThrowFullShow") == true then
		return true
	end
	return r.boss ~= nil or Show.FullFloors[r.floor] == true or Show.FullCreatures[r.rarity] == true
end

-- ── персонаж, управление, интерфейс ─────────────────────────────────────────────────────────────────────────────────
local function rootOf(): (BasePart?, Humanoid?)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if root and root:IsA("BasePart") and humanoid and humanoid.Health > 0 then
		return root, humanoid
	end
	return nil, nil
end

local function getControls(): any
	if controls == nil then
		local ok, found = pcall(function()
			local module = player:WaitForChild("PlayerScripts"):FindFirstChild("PlayerModule")
			return module and (require(module) :: any):GetControls()
		end)
		controls = if ok and found then found else false
	end
	return controls or nil
end

local function hideInterface(hide: boolean, keepTouch: boolean?)
	local gui = player:FindFirstChildOfClass("PlayerGui")
	if not gui then
		return
	end
	if hide then
		for _, layer in gui:GetChildren() do
			local touch = keepTouch and layer.Name == "TouchGui" -- на шкале джойстик нужен: движение — отмена
			if layer:IsA("LayerCollector") and layer ~= ThrowHud.Gui() and layer.Enabled and not touch then
				hidden[layer] = true
				layer.Enabled = false
			end
		end
	else
		for layer in hidden do
			if layer.Parent then
				layer.Enabled = true
			end
		end
		table.clear(hidden)
	end
end

-- Капсула награды в руках (сервер выдаёт её сразу) не видна до конца показа.
local function hideCarried(hide: boolean)
	local folder = workspace:FindFirstChild("ThrowItems", true)
	local root = rootOf()
	if not folder then
		return
	end
	for _, d in folder:GetDescendants() do
		if d:IsA("BasePart") then
			local near = root ~= nil and (d.Position - root.Position).Magnitude < 14
			d.LocalTransparencyModifier = if hide and near then 1 else 0
		end
	end
end

-- ── эффекты ─────────────────────────────────────────────────────────────────────────────────────────────────────────
local SPARKLES = "rbxasset://textures/particles/sparkles_main.dds" -- встроенные текстуры Roblox
local SMOKE = "rbxasset://textures/particles/smoke_main.dds"

local function effects(): Folder
	if not fxFolder or not fxFolder.Parent then
		local folder = Instance.new("Folder")
		folder.Name = "ThrowFx"
		folder.Parent = workspace
		fxFolder = folder
	end
	return fxFolder :: Folder
end

local function ghost(part: BasePart)
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
end

-- Расходящийся круг по полу.
local function ring(at: Vector3, color: Color3, from: number, to: number, seconds: number)
	local disc = Instance.new("Part")
	disc.Name = "Ring"
	disc.Shape = Enum.PartType.Cylinder
	disc.Material = Enum.Material.SmoothPlastic
	disc.Color = color
	ghost(disc)
	disc.Parent = effects()
	local t = 0
	table.insert(fx, function(dt: number): boolean
		t += dt
		local k = easeOut(t / seconds)
		local d = mix(from, to, k) * 2
		disc.Size = Vector3.new(0.12, d, d)
		disc.CFrame = CFrame.new(at + Vector3.new(0, 0.12, 0)) * CFrame.Angles(0, 0, math.rad(90))
		disc.Transparency = mix(0.45, 1, k)
		if t >= seconds then
			disc:Destroy()
			return false
		end
		return true
	end)
end

-- Разовый выброс частиц.
local function burst(at: Vector3, color: Color3, count: number, texture: string, speed: number, size: number)
	local anchor = Instance.new("Part")
	anchor.Name = "Burst"
	anchor.Transparency = 1
	anchor.Size = Vector3.new(0.4, 0.4, 0.4)
	anchor.CFrame = CFrame.new(at)
	ghost(anchor)
	anchor.Parent = effects()
	local emitter = Instance.new("ParticleEmitter")
	emitter.Texture = texture
	emitter.Color = ColorSequence.new(color, Color3.new(1, 1, 1))
	emitter.LightEmission = if texture == SMOKE then 0.1 else 0.9
	emitter.Size =
		NumberSequence.new({ NumberSequenceKeypoint.new(0, size), NumberSequenceKeypoint.new(1, size * 0.2) })
	emitter.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) })
	emitter.Lifetime = NumberRange.new(0.5, 1.1)
	emitter.Speed = NumberRange.new(speed * 0.5, speed)
	emitter.SpreadAngle = Vector2.new(180, 180)
	emitter.Drag = 3
	emitter.Rate = 0
	emitter.Parent = anchor
	emitter:Emit(count)
	Debris:AddItem(anchor, 1.6)
end

-- Столб света над точкой (карточка): луч между двумя точками, сам гаснет.
local function pillar(at: Vector3, width: number, seconds: number)
	local base = Instance.new("Part")
	base.Name = "Pillar"
	base.Transparency = 1
	base.Size = Vector3.new(0.4, 0.4, 0.4)
	base.CFrame = CFrame.new(at)
	ghost(base)
	base.Parent = effects()
	local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
	a1.Position = Vector3.new(0, 60, 0)
	a0.Parent, a1.Parent = base, base
	-- мягкий край: три луча один в другом — широкий едва виден, узкий ярче
	local beams: { { beam: Beam, alpha: number } } = {}
	for _, spec in { { 1.6, 0.93 }, { 1.0, 0.86 }, { 0.5, 0.8 } } do
		local beam = Instance.new("Beam")
		beam.Attachment0, beam.Attachment1 = a0, a1
		beam.Width0, beam.Width1 = width * spec[1], width * spec[1]
		beam.FaceCamera = true
		beam.LightEmission = 1
		beam.Color = ColorSequence.new(Color3.new(1, 1, 1))
		beam.Parent = base
		table.insert(beams, { beam = beam, alpha = spec[2] })
	end
	local t = 0
	table.insert(fx, function(dt: number): boolean
		t += dt
		local k = math.clamp(t / seconds, 0, 1)
		for _, b in beams do
			b.beam.Transparency = NumberSequence.new(mix(b.alpha, 1, easeIn(k)))
		end
		if k >= 1 then
			base:Destroy()
			return false
		end
		return true
	end)
end

-- Полное шоу: сцена темнеет и насыщается (ColorCorrection у этого клиента) и края экрана затемняются. k: 0…1.
local mood: ColorCorrectionEffect? = nil
local function setMood(k: number)
	local amount = math.clamp(k, 0, 1)
	if amount <= 0 then
		if mood then
			mood:Destroy()
			mood = nil
		end
		ThrowHud.Vignette(0)
		return
	end
	local effect = mood
	if not effect then
		effect = Instance.new("ColorCorrectionEffect")
		effect.Name = "ThrowMood"
		effect.Parent = Lighting
		mood = effect
	end
	effect.Brightness = -0.1 * amount
	effect.Contrast = 0.18 * amount
	effect.Saturation = 0.4 * amount
	ThrowHud.Vignette(amount)
end

-- Вращающиеся лучи за существом (полное шоу): плоская картинка в мире позади него, цвет — редкости.
local function rays(at: Vector3, away: Vector3, color: Color3, size: number)
	local anchor = Instance.new("Part")
	anchor.Name = "Rays"
	anchor.Transparency = 1
	anchor.Size = Vector3.new(0.4, 0.4, 0.4)
	anchor.CFrame = CFrame.new(at + away)
	ghost(anchor)
	anchor.Parent = effects()
	local board = Instance.new("BillboardGui")
	board.Size = UDim2.fromScale(size, size)
	board.LightInfluence = 0
	board.Parent = anchor
	local image = Instance.new("ImageLabel")
	image.BackgroundTransparency = 1
	image.Size = UDim2.fromScale(1, 1)
	image.Image = ThrowHud.RaysImage
	image.ImageColor3 = color
	image.ImageTransparency = 1
	image.Parent = board
	local t = 0
	table.insert(fx, function(dt: number): boolean
		t += dt
		if not image.Parent then
			return false
		end
		image.Rotation = (t * 50) % 360
		image.ImageTransparency = mix(1, 0.15, smooth(t / 0.4))
		return true
	end)
end

local function clearFx()
	table.clear(fx)
	if fxFolder then
		fxFolder:Destroy()
		fxFolder = nil
	end
end

local function glowOf(kind: string): Color3
	local rig = LovibumRigs.Types[kind]
	return Color3.fromHex(if rig then rig.Glow else "FFFFFF")
end

-- ── Ловибум и монстр ────────────────────────────────────────────────────────────────────────────────────────────────
local function makeBall(kind: string)
	if ball then
		ball:Destroy()
	end
	ballKind = kind
	local model = LovibumModel.Build(kind)
	model.Parent = effects()
	ball = model
end

local function placeBall(cf: CFrame, open: number, scale: number)
	if ball then
		LovibumModel.Place(ball, cf, open, scale)
	end
end

-- Ловибум в полёте: центр в точке at, кувырок turn вокруг центра.
local function tumbleBall(at: Vector3, turn: CFrame, scale: number)
	if ball then
		local rig = LovibumRigs.Types[ballKind]
		local half = (if rig then rig.Size.Y else 1.3) * scale / 2
		LovibumModel.Place(ball, CFrame.new(at) * turn * CFrame.new(0, -half, 0), 0, scale)
	end
end

-- Монстр показа: копия предмета из ItemPreviews (как в инвентаре), без столкновений.
local function makeMonster(itemId: string): any
	local previews = ReplicatedStorage:FindFirstChild("ItemPreviews")
	local source = previews and previews:FindFirstChild(itemId)
	if not (source and source:IsA("Model")) then
		return nil
	end
	local model = source:Clone()
	model.Name = "Monster"
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") then
			ghost(d)
		elseif d:IsA("LayerCollector") or d:IsA("ProximityPrompt") or d:IsA("BaseScript") then
			d:Destroy()
		end
	end
	local _, size = model:GetBoundingBox()
	-- рост — Show.MonsterHeight, но плоское и длинное существо не шире Show.MonsterWidth (иначе закрывает кадр)
	local width = math.max(size.X, size.Z)
	local fit = math.min(Show.MonsterHeight / math.max(0.5, size.Y), Show.MonsterWidth / math.max(0.5, width))
	local base = math.clamp(fit, 0.3, 9)
	model.Parent = effects()
	monster = model
	return { base = base, width = width }
end

-- Поставить монстра: низ в точке at, лицом по dir, масштаб k (от размера показа).
local function placeMonster(at: Vector3, dir: Vector3, k: number, tilt: CFrame?)
	local model, info = monster, monsterInfo
	if not model or not info then
		return
	end
	local scale = math.max(0.02, info.base * k)
	if math.abs(model:GetScale() - scale) > 1e-3 then
		model:ScaleTo(scale)
	end
	local boxCf, size = model:GetBoundingBox()
	local offset = model:GetPivot():ToObjectSpace(boxCf)
	local centre = at + Vector3.new(0, size.Y / 2, 0)
	local flat = Vector3.new(dir.X, 0, dir.Z)
	local facing = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(-1, 0, 0)
	local want = CFrame.lookAt(centre, centre + facing) * (tilt or CFrame.identity)
	model:PivotTo(want * offset:Inverse())
end

-- ── камера ──────────────────────────────────────────────────────────────────────────────────────────────────────────
local function takeCamera()
	local camera = workspace.CurrentCamera
	if not cameraWas then
		cameraWas = { fov = camera.FieldOfView }
		eye:Set(camera.CFrame.Position)
		look:Set(camera.CFrame.Position + camera.CFrame.LookVector * 30)
		fov:Set(camera.FieldOfView)
	end
end

local function releaseCamera()
	local camera = workspace.CurrentCamera
	if cameraWas then
		camera.CameraType = Enum.CameraType.Custom
		camera.FieldOfView = cameraWas.fov
		cameraWas = nil
	end
end

-- Цель камеры этого кадра: пружины догоняют её, встряска и крен — поверх.
local function aimCamera(dt: number, eyeTo: Vector3, lookTo: Vector3, fovTo: number, snap: boolean?)
	local camera = workspace.CurrentCamera
	if not cameraWas then
		return
	end
	if snap then
		eye:Set(eyeTo)
		look:Set(lookTo)
		fov:Set(fovTo)
	else
		eye:Step(eyeTo, dt)
		look:Step(lookTo, dt)
		fov:Step(fovTo, dt)
	end
	local jolt = shake:Step(Vector3.zero, dt)
	camera.CameraType = Enum.CameraType.Scriptable
	local from = eye.value + jolt
	camera.CFrame = CFrame.lookAt(from, look.value + jolt * 0.4) * CFrame.Angles(0, 0, math.rad(roll))
	camera.Focus = CFrame.new(look.value)
	camera.FieldOfView = fov.value
end

-- Точка на окружности вокруг персонажа: angle 0 — за спиной (+Z), 90 — справа (+X), 180 — спереди.
local function orbit(angle: number, radius: number, height: number): Vector3
	local a = math.rad(angle)
	return origin + Vector3.new(math.sin(a) * radius, height, math.cos(a) * radius)
end

-- ── конец показа ────────────────────────────────────────────────────────────────────────────────────────────────────
local function restore()
	scene = nil
	session = nil
	result = nil
	state = "Idle"
	stateAt = clock
	if pose then
		pose:Stop()
		pose = nil
	end
	if ball then
		ball:Destroy()
		ball = nil
	end
	if monster then
		monster:Destroy()
		monster = nil
	end
	monsterInfo = nil
	clearFx()
	setMood(0)
	roll = 0
	eye.speed, look.speed = 14, 16
	hideCarried(false)
	releaseCamera()
	local _, humanoid = rootOf()
	if humanoid then
		humanoid.AutoRotate = true
		if walkWas then
			humanoid.WalkSpeed = walkWas
		end
	end
	walkWas = nil
	ZoneController.Probe(nil) -- свет — снова по месту игрока
	local c = getControls()
	if c then
		c:Enable()
	end
	UserInputService.ModalEnabled = false
	ThrowHud.SetEnabled(false)
	hideInterface(false)
end

-- ── шкала ───────────────────────────────────────────────────────────────────────────────────────────────────────────
local function requestStart()
	local stack = pickFor(selectedKind)
	if not stack then
		return -- выбранного вида нет: другой вид сам не тратится — игрок выбирает его на панели
	end
	state = "Starting"
	stateAt = clock
	armed = false
	Remotes.Get(Remotes.Names.ThrowAction):FireServer("Start", stack.level, stack.kind)
end

local function beginAim(payload: any)
	local root, humanoid = rootOf()
	if not root or not humanoid then
		Remotes.Get(Remotes.Names.ThrowAction):FireServer("Cancel")
		state = "Idle"
		return
	end
	session = payload
	result = nil
	state = "Aim"
	stateAt = clock
	origin = root.Position
	-- персонаж стоит лицом к трассе; управление не отключается: отпустил и снова повёл — уход со шкалы
	walkWas = walkWas or humanoid.WalkSpeed
	humanoid.WalkSpeed = 0
	humanoid.AutoRotate = false
	root.CFrame = CFrame.new(root.Position)
	released = false
	movedFor = 0
	if not pose and player.Character then
		pose = ThrowPose.Start(player.Character)
	end
	makeBall(payload.kind)
	ThrowHud.SetKinds(nil)
	hideInterface(true, true)
	ThrowHud.SetEnabled(true)
	ThrowHud.ShowAim()
	scene = { name = "Aim", t = 0, dipped = false }
end

function ThrowController.Press()
	if state ~= "Aim" or not session then
		return
	end
	local now = workspace:GetServerTimeNow()
	Remotes.Get(Remotes.Names.ThrowAction):FireServer("Press", now)
	local position = ThrowRules.ScalePosition(now - session.at, session.period, session.phase)
	local quality = ThrowRules.Quality(position)
	local bonus = math.floor(Throw.Accuracy.Max * 100 * quality + 0.5)
	ThrowHud.SetMarker(position, ("+%d %%"):format(bonus))
	ThrowHud.AimResult(("+%d %% к дальности"):format(bonus), quality >= 1)
	state = "Pressed"
	stateAt = clock
	-- на время показа управление и джойстик убраны
	local c = getControls()
	if c then
		c:Disable()
	end
	UserInputService.ModalEnabled = true
	hideInterface(true)
	if not cameraWas then -- нажал раньше, чем кончилось затемнение
		takeCamera()
		eye:Set(origin + C.AimEye)
		look:Set(origin + C.AimLook)
		fov:Set(C.AimFov)
	end
	ThrowHud.Fade(0)
	scene = { name = "Windup", t = 0, released = false }
end

-- Уход со шкалы без броска (игрок повёл персонажа): Ловибум цел; новая шкала — с нового захода на полосу.
function ThrowController.Cancel()
	if state == "Aim" then
		Remotes.Get(Remotes.Names.ThrowAction):FireServer("Cancel")
		restore()
	end
end

-- ── сцены ───────────────────────────────────────────────────────────────────────────────────────────────────────────
local function handCFrame(): CFrame
	local hand = pose and pose:Hand()
	return hand or CFrame.new(origin + Vector3.new(0.9, 0.6, -0.4))
end

-- Шкала у края: затемнение, камера за плечом, стойка, бегунок по времени сервера.
local function stepAim(dt: number, s: any)
	s.t += dt
	local dip = Show.Dip
	if not s.dipped then
		ThrowHud.Fade(smooth(s.t / dip))
		if s.t >= dip then
			s.dipped = true
			takeCamera()
			aimCamera(dt, origin + C.AimEye, origin + C.AimLook, C.AimFov, true)
		end
		return
	end
	ThrowHud.Fade(1 - smooth((s.t - dip) / (dip * 1.4)))
	aimCamera(dt, origin + C.AimEye, origin + C.AimLook, C.AimFov)
	if pose then
		pose:Aim(smooth((s.t - dip) / 0.35))
	end
	placeBall(handCFrame(), 0, 1)
	if session and state == "Aim" then
		local position =
			ThrowRules.ScalePosition(workspace:GetServerTimeNow() - session.at, session.period, session.phase)
		local bonus = math.floor(Throw.Accuracy.Max * 100 * ThrowRules.Quality(position) + 0.5)
		ThrowHud.SetMarker(position, ("+%d %%"):format(bonus))
	end
end

-- Итог: вспышка, «1 из N» с лучами, карточка (редкость этажа, имя, доход, метка). stop — где стоит монстр (полное
-- шоу): над ним столб света. short — без втягивания: карточка держится Show.Quick и показ кончается.
local function beginCard(rest: Vector3, stop: Vector3?, short: boolean, lucky: boolean)
	local r = result
	local def = Items[r.itemId]
	local rarity = UITokens.RarityColor(r.rarity)
	ThrowHud.Flight(false)
	ThrowHud.Reveal(true)
	ThrowHud.SetReveal(r.oneIn, "", true)
	if not lucky and r.oneIn >= Show.LuckyFrom then
		ThrowHud.Lucky()
	end
	ThrowHud.Flash(0.75, 0.45, Color3.fromRGB(255, 244, 214))
	if stop and not short then -- полное шоу: столб света, искры и вращающиеся лучи за существом
		pillar(stop, if monsterInfo then monsterInfo.width * monsterInfo.base * 0.8 else 3, Show.Card + Show.Suck)
		burst(stop + Vector3.new(0, 2, 0), Color3.new(1, 1, 1), 26, SPARKLES, 18, 1.1)
		rays(stop + Vector3.new(0, 2.8, 0), Vector3.new(0, 0, 3), rarity, 24)
	end
	local K = UITokens.Throw.Card
	ThrowHud.Card({
		{ text = FloorRarity.Names[r.floor] or "", color = rarity },
		{ text = if def then def.displayName else "???", color = K.NameColor },
		{ text = ("+%s/с"):format(tostring(r.income)), color = K.IncomeColor },
	}, if r.sold then "Продано" elseif r.duplicate then "Уже есть" else "Новое!")
	scene = { name = "Card", t = 0, rest = rest, stop = stop, short = short }
end

local function startFlight(from: Vector3)
	local r = result
	local to = ThrowPath.Landing(r.zone, r.depth, origin.X) or (origin + Vector3.new(0, -10, -60))
	local rig = LovibumRigs.Types[ballKind]
	local half = (if rig then rig.Size.Y else 1.3) * Show.LovibumScale / 2
	scene = {
		name = "Flight",
		t = 0,
		from = from,
		to = to + Vector3.new(0, half, 0),
		floor = to,
		rest = to + Vector3.new(0, 0, -C.SlideLength),
		duration = ThrowPath.Duration(from, to),
		trail = nil,
	}
	lastZone = 0
	-- белый след: невидимая деталь с двумя точками, ведётся за Ловибумом
	local carrier = Instance.new("Part")
	carrier.Name = "Trail"
	carrier.Transparency = 1
	carrier.Size = Vector3.new(0.5, 0.5, 0.5)
	ghost(carrier)
	carrier.Parent = effects()
	local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
	a0.Position, a1.Position = Vector3.new(0, 0.6, 0), Vector3.new(0, -0.6, 0)
	a0.Parent, a1.Parent = carrier, carrier
	local trail = Instance.new("Trail")
	trail.Attachment0, trail.Attachment1 = a0, a1
	trail.Lifetime = 0.45
	trail.LightEmission = 1
	trail.Color = ColorSequence.new(Color3.new(1, 1, 1))
	trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 1) })
	trail.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.15) })
	trail.Parent = carrier
	scene.trail = carrier
	ThrowHud.Flight(true)
end

-- Замах и бросок: поля кино, облёт спереди, хлёст, возврат за спину; на Release Ловибум уходит в полёт.
local function stepWindup(dt: number, s: any)
	-- без ответа сервера замах дожидается в верхней точке
	if not (result or s.t / Show.Windup < 0.6) then
		dt = 0
	end
	s.t += dt
	local u = math.clamp(s.t / Show.Windup, 0, 1)
	ThrowHud.Bars(smooth(s.t / 0.2))
	if pose then
		pose:Windup(u)
	end
	local angle, radius, height, fovTo
	local target: Vector3
	local chest = origin + Vector3.new(0, 1.3, 0)
	if u < 0.26 then
		local k = smooth(u / 0.26)
		angle, radius, height = mix(16, C.FrontAngle, k), mix(4.8, 5.6, k), mix(2.2, 1.5, k)
		target = (origin + C.AimLook):Lerp(chest, smooth(u / 0.1))
		fovTo = mix(C.AimFov, C.FrontFov, k)
	elseif u < 0.62 then
		local k = (u - 0.26) / 0.36
		angle, radius, height = mix(C.FrontAngle, C.FrontAngle + 10, k), mix(5.6, 4.8, k), 1.5
		target = chest
		fovTo = mix(C.FrontFov, C.FrontFov - 4, k)
	else
		local k = smooth((u - 0.62) / 0.24)
		angle, radius, height = mix(C.FrontAngle + 10, C.BackAngle, k), mix(4.8, 6, k), mix(1.5, 2.3, k)
		target = chest:Lerp(origin + Vector3.new(0, -3, -60), k * k) -- персонаж в кадре до самого броска
		fovTo = mix(C.FrontFov - 4, C.ReleaseFov, k)
	end
	aimCamera(dt, orbit(angle, radius, height), target, fovTo)
	if not s.released then
		placeBall(handCFrame(), 0, 1 + 0.25 * easeIn(u / ThrowPose.Release))
		if u >= ThrowPose.Release and result then
			s.released = true
			ThrowHud.HideAim()
			local from = handCFrame().Position
			local windup = s
			startFlight(from)
			scene.windup = windup -- доводка позы идёт под полётом
		end
	end
end

-- Полёт: погоня на пружинах, удача, смена зон.
local function stepFlight(dt: number, s: any)
	s.t += dt
	if s.windup then -- доводка позы и уход полей
		local w = s.windup
		w.t += dt
		if pose then
			pose:Windup(math.clamp(w.t / Show.Windup, 0, 1))
		end
		ThrowHud.Bars(1 - smooth(s.t / 0.35))
	end
	local u = math.clamp(s.t / s.duration, 0, 1)
	local at, p = ThrowPath.At(s.from, s.to, u)
	local grow = mix(1.25, Show.LovibumScale, smooth(s.t / 0.3))
	tumbleBall(at, CFrame.Angles(s.t * 8.5, s.t * 2.1, 0), grow)
	if s.trail then
		s.trail.CFrame = CFrame.new(at)
	end
	-- камера: чем ближе к концу — тем ниже и ближе
	local late = smooth((u - 0.8) / 0.2)
	local back = C.ChaseEye:Lerp(C.SideEye, late)
	eye.speed = mix(6, 13, smooth(s.t / 0.6))
	roll = math.sin(s.t * 1.4) * C.Bank * (1 - late)
	aimCamera(dt, at + back, at + C.ChaseLook:Lerp(C.SideLook, late), C.ChaseFov)
	local index = ThrowPath.ZoneAt(at.Z) or 1
	local zone = GameConfig.Zones[index]
	local changed = index ~= lastZone
	lastZone = index
	if changed then
		ZoneController.Probe(index) -- свет зоны — за Ловибумом
	end
	ThrowHud.SetFlight(1 + (result.luck - 1) * p, zone.name, Color3.fromHex(zone.accent), changed)
	if u >= 1 then
		-- удар: белый круг по полу и пыль
		ring(s.floor, Color3.new(1, 1, 1), 1, 7, 0.5)
		burst(s.floor, Color3.fromRGB(235, 225, 205), 10, SMOKE, 9, 2.2)
		shake:Kick(Vector3.new(0, -8, 0))
		roll = 0
		scene = { name = "Slide", t = 0, to = s.to, floor = s.floor, rest = s.rest, trail = s.trail, spin = s.t * 8.5 }
	end
end

-- После удара Ловибум докатывается и замирает; затем затемнение и сцена раскрытия.
local function stepSlide(dt: number, s: any)
	s.t += dt
	local k = easeOut(s.t / Show.Slide)
	local ground = s.floor:Lerp(s.rest, k)
	local hop = math.abs(math.sin(k * math.pi * 2)) * 0.7 * (1 - k)
	local turn = CFrame.Angles(s.spin + k * 4, 0, 0):Lerp(CFrame.Angles(0, math.pi, 0), smooth(k * 1.3))
	if k < 0.75 then
		tumbleBall(ground + Vector3.new(0, s.to.Y - s.floor.Y + hop, 0), turn, Show.LovibumScale)
	else
		placeBall(CFrame.new(ground) * CFrame.Angles(0, math.pi, 0), 0, Show.LovibumScale)
	end
	if s.trail then
		s.trail.CFrame = CFrame.new(ground + Vector3.new(0, 1, 0))
	end
	eye.speed, look.speed = 5, 8
	aimCamera(dt, ground + C.SideEye, ground + C.SideLook, C.ChaseFov - 14)
	if not isFull(result) then -- обычный результат: коротко — вспышка, существо рядом с Ловибумом, доход
		if s.t >= Show.Slide then
			if s.trail then
				s.trail:Destroy()
			end
			monsterInfo = makeMonster(result.itemId)
			local halfWidth = if monsterInfo then monsterInfo.width * monsterInfo.base / 2 else 2
			beginCard(s.rest, s.rest + Vector3.new(C.MonsterGap + halfWidth, 0, 0.4), true, false)
		end
		return
	end
	local out = (s.t - Show.Slide - 0.25) / Show.Dip
	ThrowHud.Fade(smooth(out))
	if out >= 1 then
		ThrowHud.Flight(false)
		if s.trail then
			s.trail:Destroy()
		end
		local def = Items[result.itemId]
		monsterInfo = makeMonster(result.itemId)
		local name = if def then def.displayName else "???"
		local letters: { string } = {}
		for _, code in utf8.codes(name) do
			table.insert(letters, utf8.char(code))
		end
		local order: { number } = {}
		for i, ch in letters do
			if ch ~= " " then
				table.insert(order, i)
			end
		end
		local rng = Random.new(#name * 7 + result.oneIn)
		for i = #order, 2, -1 do
			local j = rng:NextInteger(1, i)
			order[i], order[j] = order[j], order[i]
		end
		local rest = s.rest
		local halfWidth = if monsterInfo then monsterInfo.width * monsterInfo.base / 2 else 2
		scene = {
			name = "Approach",
			t = 0,
			rest = rest,
			stop = rest + Vector3.new(C.MonsterGap + halfWidth, 0, 0.4),
			letters = letters,
			order = order,
			shown = 0,
			lucky = false,
		}
		eye.speed, look.speed = 4, 6
		aimCamera(dt, rest + C.FarEye, rest + Vector3.new(0, 1, 0), C.RevealFov, true)
		ThrowHud.Reveal(true)
		ThrowHud.SetReveal(1, "", false)
		placeMonster(rest + C.Hidden, Vector3.new(-1, 0, 0), 1)
	end
end

-- Имя с пропусками: открыто share букв (в случайном порядке); пока share < 0 — ничего.
local function masked(s: any, share: number): string
	if share < 0 then
		return ""
	end
	local open: { [number]: boolean } = {}
	for i = 1, math.floor(#s.order * math.clamp(share, 0, 1) + 0.001) do
		open[s.order[i]] = true
	end
	local out = table.create(#s.letters)
	for i, ch in s.letters do
		out[i] = if ch == " " or open[i] then ch else "_"
	end
	return table.concat(out)
end

-- Раскрытие, как в записи: низкая дальняя камера медленно наезжает на Ловибум (сверху «1 из 1»), слева выходит
-- монстр, камера отходит на средний план, растёт «1 из N», имя открывается по буквам; в конце — «Удача!» и круг.
local function stepApproach(dt: number, s: any)
	s.t += dt
	ThrowHud.Fade(1 - smooth(s.t / (Show.Dip * 1.6)))
	local k = math.clamp(s.t / Show.Approach, 0, 1)
	setMood(smooth(k / 0.25))
	local rest = s.rest
	placeBall(CFrame.new(rest) * CFrame.Angles(0, math.pi, 0), 0, Show.LovibumScale)
	-- монстр: выходит на 0.42…0.66, дальше стоит и слегка покачивается
	if not monsterInfo and k < 0.42 then -- модель монстра могла ещё не прийти с сервера
		monsterInfo = makeMonster(result.itemId)
		if monsterInfo then
			s.stop = rest + Vector3.new(C.MonsterGap + monsterInfo.width * monsterInfo.base / 2, 0, 0.4)
		end
	end
	local walk = smooth((k - 0.42) / 0.24)
	local from = rest + C.MonsterFrom
	local at = from:Lerp(s.stop, walk)
	local hop = math.abs(math.sin(walk * math.pi * C.Hops)) * 0.8 * (1 - walk * 0.5)
	local idle = if walk >= 1 then math.sin(s.t * 3) * 0.06 else 0
	if k < 0.42 then
		placeMonster(rest + C.Hidden, Vector3.new(-1, 0, 0), 1)
	else
		placeMonster(
			at + Vector3.new(0, hop + math.max(0, idle), 0),
			if walk < 1 then s.stop - from else rest - s.stop,
			1
		)
	end
	-- камера: наезд (до 0.62), затем средний план
	if k < 0.62 then
		local push = smooth(k / 0.62)
		aimCamera(
			dt,
			rest + C.FarEye:Lerp(C.NearEye, push),
			rest + Vector3.new(0, 1, 0):Lerp(C.NearLook, push),
			C.RevealFov
		)
	else
		aimCamera(dt, rest + C.MidEye, rest + C.MidLook, C.RevealFov)
	end
	-- «1 из N»: до выхода монстра почти стоит, потом растёт до выпавшего; имя — по буквам с 0.62
	local grow = if k < 0.42
		then 0.1 * (k / 0.42)
		elseif k < 0.62 then mix(0.1, 0.3, (k - 0.42) / 0.2)
		else mix(0.3, 1, smooth((k - 0.62) / 0.36))
	local n = math.max(1, math.floor(result.oneIn ^ grow + 0.5))
	local share = if k < 0.56 then -1 else (k - 0.64) / 0.32
	ThrowHud.SetReveal(n, masked(s, share), n > s.shown)
	s.shown = n
	if not s.lucky and k > 0.9 and result.oneIn >= Show.LuckyFrom then
		s.lucky = true
		ThrowHud.Lucky()
		ring(s.stop, Color3.new(1, 1, 1), 1, 14, 0.6)
	end
	if k >= 1 then
		ThrowHud.SetReveal(result.oneIn, masked(s, 1), true)
		beginCard(rest, s.stop, false, s.lucky)
	end
end

-- Карточка: монстр стоит в столбе света.
local function stepCard(dt: number, s: any)
	s.t += dt
	local rest = s.rest
	placeBall(CFrame.new(rest) * CFrame.Angles(0, math.pi, 0), 0, Show.LovibumScale)
	if s.stop then
		if not monsterInfo then -- модель могла ещё не прийти с сервера
			monsterInfo = makeMonster(result.itemId)
		end
		local near = s.short and not s.far -- обычный результат: существо выскакивает рядом и смотрит в камеру
		local grow = if near then math.max(0.05, backOut(s.t / 0.35)) else 1
		local face = if near then rest + C.ShortEye - s.stop else rest - s.stop
		placeMonster(s.stop + Vector3.new(0, math.max(0, math.sin(s.t * 3) * 0.06), 0), face, grow)
		if s.short and not s.far then
			aimCamera(dt, rest + C.ShortEye, rest + C.ShortLook, C.ShortFov)
		else
			aimCamera(dt, s.stop + C.CardEye, s.stop + C.CardLook, C.CardFov)
		end
	else
		aimCamera(dt, rest + C.SideEye, rest + C.SideLook, C.ChaseFov - 14)
	end
	if s.short then -- обычный результат или пропуск: без втягивания
		if s.t >= Show.Quick then
			scene = { name = "Fade", t = 0 }
		end
		return
	end
	if s.t >= Show.Card then
		-- вихрь: искры летят к Ловибуму со сферы вокруг него
		local shell = Instance.new("Part")
		shell.Name = "Vortex"
		shell.Shape = Enum.PartType.Ball
		shell.Transparency = 1
		shell.Size = Vector3.new(14, 14, 14)
		shell.CFrame = CFrame.new(rest + Vector3.new(0, 2, 0))
		ghost(shell)
		shell.Parent = effects()
		local sparks = Instance.new("ParticleEmitter")
		sparks.Texture = SPARKLES
		sparks.Shape = Enum.ParticleEmitterShape.Sphere
		sparks.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
		sparks.ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward
		sparks.Color = ColorSequence.new(glowOf(ballKind), Color3.new(1, 1, 1))
		sparks.LightEmission = 1
		sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.15) })
		sparks.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(0.2, 0),
			NumberSequenceKeypoint.new(1, 0.2),
		})
		sparks.Lifetime = NumberRange.new(0.4, 0.5)
		sparks.Speed = NumberRange.new(14, 16)
		sparks.Rate = 90
		sparks.Parent = shell
		if ball then
			LovibumModel.SetLight(ball, 16, 2.4)
		end
		scene = { name = "Suck", t = 0, rest = rest, from = s.stop, shell = shell, sparks = sparks }
	end
end

-- Монстр попадает в Ловибум: тот раскрывается, монстра отрывает от земли, крутит и затягивает внутрь.
local function stepSuck(dt: number, s: any)
	s.t += dt
	local k = math.clamp(s.t / Show.Suck, 0, 1)
	local rest = s.rest
	local rig = LovibumRigs.Types[ballKind]
	local core = rest + Vector3.new(0, (if rig then rig.Size.Y else 1.3) * Show.LovibumScale * 0.6, 0)
	local wobble = CFrame.Angles(0, math.pi, math.rad(5) * math.sin(s.t * 40) * k)
	placeBall(CFrame.new(rest) * wobble, backOut(s.t / 0.25), Show.LovibumScale * (1 + 0.1 * k))
	local pull = easeIn(k)
	local at = s.from:Lerp(core, pull) + Vector3.new(0, math.sin(k * math.pi) * 2.2, 0)
	placeMonster(at, rest - s.from, mix(1, 0.04, pull), CFrame.Angles(0, pull * math.pi * 9, math.rad(25) * k))
	if ball then
		LovibumModel.SetLight(ball, mix(16, 30, k), mix(2.4, 6, k))
	end
	shake:Kick(Vector3.new(math.sin(s.t * 71), math.cos(s.t * 53), 0) * 6 * k * dt * 60)
	aimCamera(
		dt,
		rest + C.MidEye:Lerp(C.SuckEye, smooth(k)),
		rest + C.MidLook:Lerp(C.SuckLook, smooth(k)),
		mix(C.RevealFov, C.SuckFov, smooth(k))
	)
	if k >= 1 then
		if monster then
			monster:Destroy()
			monster = nil
		end
		s.sparks.Enabled = false
		Debris:AddItem(s.shell, 1)
		ThrowHud.Flash(0.85, 0.3)
		ring(rest, glowOf(ballKind), 1, 12, 0.55)
		burst(core, glowOf(ballKind), 26, SPARKLES, 26, 1.2)
		shake:Kick(Vector3.new(0, 14, 0))
		scene = { name = "Shake", t = 0, rest = rest }
	end
end

-- Захлопнулся и дрожит; затем белая вспышка — и обратно к краю.
local function stepShake(dt: number, s: any)
	s.t += dt
	local k = math.clamp(s.t / Show.Shake, 0, 1)
	local rest = s.rest
	local hop = math.abs(math.sin(k * math.pi * 2)) * 1.1 * (1 - k)
	local tilt = math.rad(18) * math.sin(k * math.pi * 6) * (1 - k)
	placeBall(
		CFrame.new(rest + Vector3.new(0, hop, 0)) * CFrame.Angles(0, math.pi, tilt),
		math.max(0, 1 - s.t / 0.1),
		Show.LovibumScale * (1.1 - 0.1 * k)
	)
	aimCamera(dt, rest + C.SuckEye, rest + C.SuckLook, C.SuckFov)
	if s.t >= Show.Shake then
		scene = { name = "Fade", t = 0 }
	end
end

-- Белая вспышка — и обратно к краю: камера, управление и интерфейс возвращаются.
local function stepFade(dt: number, s: any)
	s.t += dt
	local out = s.t / 0.25
	ThrowHud.Fade(smooth(out), UITokens.Throw.Flash)
	if out >= 1 then
		ThrowHud.Card(nil)
		restore()
		ThrowHud.SetEnabled(true) -- белая вспышка гаснет уже на обычной камере
		scene = { name = "Out", t = 0 }
	end
end

-- Касание во время показа — пропуск: из полёта и раскрытия сразу к итогу, с итога — к концу.
function ThrowController.Skip()
	local s = scene
	if not s or not result then
		return
	end
	if s.name == "Flight" or s.name == "Slide" or s.name == "Approach" then
		if s.trail then
			s.trail:Destroy()
		end
		roll = 0
		ThrowHud.Bars(0)
		ThrowHud.Fade(0)
		local rest = s.rest
		local stop: Vector3? = nil
		if isFull(result) then
			monsterInfo = monsterInfo or makeMonster(result.itemId)
			local halfWidth = if monsterInfo then monsterInfo.width * monsterInfo.base / 2 else 2
			stop = s.stop or (rest + Vector3.new(C.MonsterGap + halfWidth, 0, 0.4))
			aimCamera(0, rest + C.MidEye, rest + C.MidLook, C.RevealFov, true)
		else
			aimCamera(0, rest + C.SideEye, rest + C.SideLook, C.ChaseFov - 14, true)
		end
		ZoneController.Probe(result.zone)
		local full = isFull(result)
		beginCard(rest, stop, true, s.lucky == true)
		scene.far = full -- камера остаётся со стороны раскрытия
		if full then
			setMood(1)
		end
	elseif s.name == "Card" or s.name == "Suck" or s.name == "Shake" then
		scene = { name = "Fade", t = 0 }
	end
end

local function stepOut(dt: number, s: any)
	s.t += dt
	ThrowHud.Fade(1 - smooth(s.t / 0.35), UITokens.Throw.Flash)
	if s.t >= 0.35 then
		ThrowHud.SetEnabled(false)
		scene = nil
	end
end

local STEPS: { [string]: (number, any) -> () } = {
	Aim = stepAim,
	Windup = stepWindup,
	Flight = stepFlight,
	Slide = stepSlide,
	Approach = stepApproach,
	Card = stepCard,
	Suck = stepSuck,
	Shake = stepShake,
	Fade = stepFade,
	Out = stepOut,
}

-- ── каждый кадр ─────────────────────────────────────────────────────────────────────────────────────────────────────
local function step(dt: number)
	clock += dt
	for i = #fx, 1, -1 do
		if not fx[i](dt) then
			table.remove(fx, i)
		end
	end
	if scene then
		STEPS[scene.name](dt, scene)
		ThrowHud.Update(dt)
		if result and (state == "Pressed" or state == "Show") then
			hideCarried(true)
		end
	end
	local root, humanoid = rootOf()
	-- панель выбора вида: пока игрок подходит к краю (и шкалы нет)
	if clock - kindsAt > 0.25 then
		kindsAt = clock
		if state == "Idle" and scene == nil and root and ThrowPath.NearEdge(root.Position, 22) then
			local rows = {}
			for _, kind in Catch.Kinds do
				local stack = pickFor(kind)
				local count = if stack then stack.count else 0
				table.insert(rows, {
					kind = kind,
					text = ("%s ×%d"):format(Catch.Names[kind] or kind, count),
					count = count,
					selected = kind == selectedKind,
				})
			end
			ThrowHud.SetKinds(rows, function(kind: string)
				selectedKind = kind -- запоминается до конца сеанса
				kindsAt = 0
			end)
		else
			ThrowHud.SetKinds(nil)
		end
	end
	if state == "Idle" then
		local on = root ~= nil and ThrowPath.OnEdge(root.Position)
		if not on then
			armed = true
			retries = 0
		elseif
			armed
			and scene == nil
			and clock - stateAt > 0.6
			and player:GetAttribute("CarryingItemId") == nil
			and not GameTime.IsNight(ReplicatedStorage:GetAttribute("Phase"))
		then
			requestStart()
		end
	elseif state == "Starting" then
		if clock - stateAt > 1.2 then -- ответа нет: одна повторная просьба (сервер мог видеть игрока ещё не у края)
			state = "Idle"
			stateAt = clock
			if retries < 1 then
				retries += 1
				armed = true
			end
		end
	elseif state == "Aim" then
		if not root or not humanoid then
			ThrowController.Cancel()
		else
			-- отпустил движение и повёл снова (клавиши или джойстик) — уход со шкалы
			local moving = humanoid.MoveDirection.Magnitude > 0.3
			if not moving then
				released = true
				movedFor = 0
			elseif released then
				movedFor += dt
				if movedFor > 0.12 then
					ThrowController.Cancel()
				end
			end
		end
	elseif state == "Pressed" then
		if result then
			state = "Show"
		elseif clock - stateAt > 3 then -- ответа нет (ночь, заняты руки): показ отменяется
			restore()
		end
	end
end

function ThrowController.Init()
	local gui = player:WaitForChild("PlayerGui")
	ThrowHud.Init(gui)
	ThrowHud.InitKinds(gui, Catch.Kinds)
	Remotes.Get(Remotes.Names.LovibumsChanged).OnClientEvent:Connect(function(payload)
		if type(payload) == "table" and type(payload.lovibums) == "table" then
			lovibums = payload.lovibums
		end
	end)
	Remotes.Get(Remotes.Names.ThrowState).OnClientEvent:Connect(function(payload)
		if type(payload) == "table" then
			if state == "Starting" then
				beginAim(payload)
			end
		elseif state == "Aim" then
			restore() -- шкала закрыта сервером (время вышло)
		end
	end)
	Remotes.Get(Remotes.Names.ThrowResult).OnClientEvent:Connect(function(payload)
		if type(payload) == "table" and (state == "Pressed" or state == "Aim") then
			result = payload
		end
	end)
	player.CharacterAdded:Connect(function()
		if state ~= "Idle" or scene then
			restore()
		end
	end)
	-- нажатие в любом месте экрана (мышь, касание), Enter, E или кнопка A: на шкале — бросок, во время показа
	-- — пропуск. Касания джойстика и кнопок игра забирает сама (processed) — они не бросают.
	UserInputService.InputBegan:Connect(function(input, processed)
		if processed then
			return
		end
		local kind, key = input.UserInputType, input.KeyCode
		local go = kind == Enum.UserInputType.MouseButton1
			or kind == Enum.UserInputType.Touch
			or key == Enum.KeyCode.Return
			or key == Enum.KeyCode.E
			or key == Enum.KeyCode.ButtonA
		if not go then
			return
		end
		if state == "Aim" then
			ThrowController.Press()
		elseif state == "Show" then
			ThrowController.Skip()
		end
	end)
	RunService:BindToRenderStep("ThrowShow", Enum.RenderPriority.Camera.Value + 5, step)
end

return ThrowController

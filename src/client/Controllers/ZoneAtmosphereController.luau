-- Свет по зонам (Config/ZoneAtmosphere): при входе игрока в зону с профилем плавно переводит Lighting, Atmosphere и
-- ColorCorrection к профилю, при выходе — к исходным настройкам места (запомнены при запуске). Только у этого клиента.
-- У зоны с Aurora — мягкое северное сияние: бледные полупрозрачные ленты высоко за ледником, медленно колышутся,
-- появляются и гаснут вместе со светом (лучи Beam без текстуры на невидимых опорах, только у клиента).
-- Зона под игроком — ZoneController.Changed, координаты зоны — по её полу (ZoneController.Bounds).
-- Зависит от Config/ZoneAtmosphere, Controllers/ZoneController.

local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local ZoneAtmosphere =
	require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("ZoneAtmosphere"))
local ZoneController = require(script.Parent:WaitForChild("ZoneController"))

local ZoneAtmosphereController = {}

local LIGHT_KEYS = { "Ambient", "OutdoorAmbient", "ExposureCompensation" }
local ATMOSPHERE_KEYS = { "Color", "Decay", "Density", "Haze", "Glare" }
local CC_KEYS = { "TintColor", "Brightness", "Contrast", "Saturation" }

local base: ZoneAtmosphere.Profile = {}
local atmosphere: Atmosphere? = nil
local correction: ColorCorrectionEffect? = nil
local tweens: { Tween } = {}

local aurora: Model? = nil
local auroraZone: number? = nil
local auroraShown = 0 -- 0…1: насколько сияние проявлено
local auroraTarget = 0

local function remember()
	atmosphere = Lighting:FindFirstChildOfClass("Atmosphere")
	correction = Lighting:FindFirstChildOfClass("ColorCorrectionEffect")
	for _, key in LIGHT_KEYS do
		(base :: any)[key] = (Lighting :: any)[key]
	end
	if atmosphere then
		local a = {}
		for _, key in ATMOSPHERE_KEYS do
			a[key] = (atmosphere :: any)[key]
		end
		base.Atmosphere = a
	end
	if correction then
		local c = {}
		for _, key in CC_KEYS do
			c[key] = (correction :: any)[key]
		end
		base.ColorCorrection = c
	end
end

local function tween(target: Instance, goal: { [string]: any })
	if next(goal) == nil then
		return
	end
	local t = TweenService:Create(target, TweenInfo.new(ZoneAtmosphere.Fade, Enum.EasingStyle.Sine), goal)
	table.insert(tweens, t)
	t:Play()
end

-- Свет к профилю: заданные ключи — из профиля, остальные — исходные.
local function apply(profile: ZoneAtmosphere.Profile?)
	for _, t in tweens do
		t:Cancel()
	end
	table.clear(tweens)
	local p = profile or {}
	local goal = {}
	for _, key in LIGHT_KEYS do
		goal[key] = (p :: any)[key] or (base :: any)[key]
	end
	tween(Lighting, goal)
	if atmosphere and base.Atmosphere then
		local a, g = p.Atmosphere or {}, {}
		for _, key in ATMOSPHERE_KEYS do
			g[key] = (a :: any)[key] or (base.Atmosphere :: any)[key]
		end
		tween(atmosphere, g)
	end
	if correction and base.ColorCorrection then
		local c, g = p.ColorCorrection or {}, {}
		for _, key in CC_KEYS do
			g[key] = (c :: any)[key] or (base.ColorCorrection :: any)[key]
		end
		tween(correction, g)
	end
end

-- Прозрачность вдоль ленты: концы невидимы, середина — mid (с поправкой на проявленность shown).
local function fade(mid: number, shown: number): NumberSequence
	local m = 1 - (1 - mid) * shown
	return NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.22, m + (1 - m) * 0.35),
		NumberSequenceKeypoint.new(0.5, m),
		NumberSequenceKeypoint.new(0.78, m + (1 - m) * 0.35),
		NumberSequenceKeypoint.new(1, 1),
	})
end

local function beam(
	a0: Attachment,
	a1: Attachment,
	width: number,
	color: Color3,
	color2: Color3,
	parent: Instance
): Beam
	local b = Instance.new("Beam")
	b.Attachment0, b.Attachment1 = a0, a1
	b.Width0, b.Width1 = width, width * 0.8
	b.Color = ColorSequence.new(color, color2)
	b.Transparency = NumberSequence.new(1)
	b.LightEmission = 1
	b.LightInfluence = 0
	b.FaceCamera = true
	b.Segments = 30
	b.Parent = parent
	return b
end

-- Ленты сияния над зоной index: координаты зоны → мир по полу зоны (вход — у большего z мира, зоны идут к −z).
-- Каждая лента — опорная деталь (невидимая) с двумя точками крепления и двумя лучами: ядро и ореол.
local function buildAurora(index: number)
	if aurora and auroraZone == index then
		return
	end
	if aurora then
		aurora:Destroy()
		aurora = nil
	end
	local min, max = ZoneController.Bounds(index)
	if not min or not max then
		return
	end
	local cfg = ZoneAtmosphere.Aurora
	local center = Vector3.new((min.X + max.X) / 2, min.Y, (min.Z + max.Z) / 2)
	local model = Instance.new("Model")
	model.Name = "Aurora"
	for r, ribbon in cfg.Ribbons do
		local anchor = Instance.new("Part")
		anchor.Name = "Ribbon" .. r
		anchor.Anchored = true
		anchor.CanCollide = false
		anchor.CanQuery = false
		anchor.CanTouch = false
		anchor.CastShadow = false
		anchor.Transparency = 1
		anchor.Size = Vector3.new(1, 1, 1)
		anchor.CFrame = CFrame.new(center.X - ribbon.x, center.Y + ribbon.y, center.Z - ribbon.z)
		local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
		a0.Position = Vector3.new(ribbon.length / 2, -ribbon.rise / 2, 0)
		a1.Position = Vector3.new(-ribbon.length / 2, ribbon.rise / 2, 0)
		-- изгиб — вдоль осей точек крепления (обе наклонены вверх: у начала лента уходит вверх, у конца приходит
		-- снизу — S-волна)
		a0.Axis, a0.SecondaryAxis = Vector3.new(-1, 0.6, 0).Unit, Vector3.new(0, 0, 1)
		a1.Axis, a1.SecondaryAxis = Vector3.new(-1, 0.6, 0).Unit, Vector3.new(0, 0, 1)
		a0.Parent, a1.Parent = anchor, anchor
		local color2 = ribbon.color2 or ribbon.color
		local core = beam(a0, a1, ribbon.width, ribbon.color, color2, anchor)
		core.Name = "Core"
		local halo = beam(a0, a1, ribbon.width * cfg.HaloWidth, ribbon.color, color2, anchor)
		halo.Name = "Halo"
		anchor:SetAttribute("Phase", r * 1.7)
		anchor.Parent = model
	end
	model.Parent = workspace
	aurora, auroraZone = model, index
end

local function animateAurora(dt: number)
	if not aurora then
		return
	end
	local cfg = ZoneAtmosphere.Aurora
	auroraShown += math.clamp(auroraTarget - auroraShown, -dt / ZoneAtmosphere.Fade, dt / ZoneAtmosphere.Fade)
	local t = os.clock()
	for _, anchor in aurora:GetChildren() do
		local phase = anchor:GetAttribute("Phase") or 0
		local wave = math.sin(t / cfg.Period * 2 * math.pi + phase)
		local shimmer = 0.04 * math.sin(t * 0.7 + phase * 2)
		for _, b in anchor:GetChildren() do
			if b:IsA("Beam") then
				b.CurveSize0 = cfg.Curve + wave * cfg.Sway
				b.CurveSize1 = cfg.Curve - wave * cfg.Sway
				local mid = if b.Name == "Halo" then cfg.Halo else cfg.Core
				b.Transparency = fade(math.clamp(mid - shimmer, 0, 1), auroraShown)
			end
		end
	end
	if auroraShown <= 0 and auroraTarget <= 0 then
		aurora:Destroy()
		aurora, auroraZone = nil, nil
	end
end

local function onZone(index: number?)
	local profile = if index then ZoneAtmosphere.Profiles[index] else nil
	apply(profile)
	if profile and profile.Aurora and index then
		buildAurora(index)
		auroraTarget = 1
	else
		auroraTarget = 0
	end
end

function ZoneAtmosphereController.Init()
	remember()
	ZoneController.Changed:Connect(onZone)
	RunService.Heartbeat:Connect(animateAurora)
end

return ZoneAtmosphereController

-- Свет по зонам (Config/ZoneAtmosphere): при входе игрока в зону с профилем плавно переводит Lighting, Atmosphere и
-- ColorCorrection к профилю, при выходе — к исходным настройкам места (запомнены при запуске). Только у этого клиента.
-- У зоны с Aurora — мягкое северное сияние: бледные полупрозрачные ленты высоко за ледником, медленно колышутся,
-- появляются и гаснут вместе со светом (детали без столкновений, только у клиента).
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

-- Ленты сияния над зоной index: координаты зоны → мир по полу зоны (вход — у большего z мира, зоны идут к −z).
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
		local step = ribbon.length / cfg.Segments
		for k = 0, cfg.Segments - 1 do
			local lx = ribbon.x - ribbon.length / 2 + (k + 0.5) * step
			local wave = math.sin(k * 0.9 + r) * 2.2
			local part = Instance.new("Part")
			part.Name = ("Ribbon%d_%d"):format(r, k)
			part.Anchored = true
			part.CanCollide = false
			part.CanQuery = false
			part.CanTouch = false
			part.CastShadow = false
			part.Material = Enum.Material.Neon
			part.Color = ribbon.color
			part.Transparency = 1
			part.Size = Vector3.new(step + 0.6, ribbon.height * (0.8 + 0.4 * math.abs(math.sin(k + r))), 0.3)
			local world =
				Vector3.new(center.X - lx, center.Y + ribbon.y + wave + ribbon.height / 2, center.Z - ribbon.z)
			part.CFrame = CFrame.new(world) * CFrame.Angles(0, 0, math.rad(ribbon.tilt + wave * 2))
			part:SetAttribute("BaseY", world.Y)
			part:SetAttribute("Phase", k * 0.7 + r * 1.3)
			part.Parent = model
		end
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
	for _, part in aurora:GetChildren() do
		if part:IsA("BasePart") then
			local phase = part:GetAttribute("Phase") or 0
			local y = (part:GetAttribute("BaseY") or part.Position.Y)
				+ math.sin(t / cfg.Period * 2 * math.pi + phase) * cfg.Sway
			local pos = part.Position
			part.CFrame = CFrame.new(pos.X, y, pos.Z) * part.CFrame.Rotation
			local shimmer = 0.06 * math.sin(t * 0.8 + phase * 2)
			part.Transparency = 1 - (1 - cfg.Transparency - shimmer) * auroraShown
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

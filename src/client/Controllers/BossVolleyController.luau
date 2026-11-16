-- Эффекты магического залпа Короля-дракона (босс 10) у каждого клиента: магический круг с рунами, три полосы
-- предупреждения на земле (до фиксации следят за бойцом, после — точное направление с сервера), три снаряда по той же
-- формуле, что у сервера (Shared/BossVolley), короткая вспышка выстрела и всплеск там, где снаряд погас. Всё исчезает
-- по отмене (бой кончился, VolleyCancelAt), по новому залпу и само после последнего снаряда. Урон и попадания решает
-- только сервер (BattleService) — здесь вид. Атрибуты модели босса — BossService.Volley…; время — сервера.
-- Бюджет на залп: ≤ 25 частей, 3 Trail, без источников света и частиц. Цвета дракона: бирюза, золото, фиолет.
-- Зависит от Config/Battle, Shared/BossVolley.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Battle = require(Shared:WaitForChild("Config"):WaitForChild("Battle"))
local BossVolley = require(Shared:WaitForChild("BossVolley"))

local TAG = "Boss"
local TURQUOISE = Color3.fromHex("2FE6D8")
local GOLD = Color3.fromHex("F5B21C")
local PURPLE = Color3.fromHex("8E44FF")
local CIRCLE_RADIUS = 3.2 -- стада: магический круг (как в ролике)
local RUNES = 8
local FADE = 0.3 -- с: круг раскрывается и гаснет
local AFTER = 0.6 -- с: сколько живёт всплеск после конца снаряда
local SIDE_KEY = { [-1] = "L", [0] = "C", [1] = "R" }

type Shot = { ball: BasePart, lane: BasePart, ended: boolean, burst: BasePart? }
type Fx = {
	model: Model,
	seq: number,
	folder: Folder,
	disc: BasePart,
	runes: { BasePart },
	flash: BasePart,
	shots: { [number]: Shot },
	doneAt: number?,
}

local active: { [Model]: Fx } = {}
local finished: { [Model]: number } = {} -- номер последнего показанного залпа: заново не строить
local BossVolleyController = {}

local function part(
	folder: Folder,
	name: string,
	shape: Enum.PartType,
	size: Vector3,
	color: Color3,
	alpha: number
): Part
	local p = Instance.new("Part")
	p.Name = name
	p.Shape = shape
	p.Size = size
	p.Color = color
	p.Material = Enum.Material.Neon
	p.Transparency = alpha
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Parent = folder
	return p
end

local function build(model: Model, seq: number, cfg: any): Fx
	local folder = Instance.new("Folder")
	folder.Name = "VolleyFx"
	local disc = part(
		folder,
		"Circle",
		Enum.PartType.Cylinder,
		Vector3.new(0.15, CIRCLE_RADIUS * 2, CIRCLE_RADIUS * 2),
		PURPLE,
		1
	)
	local runes = {}
	for i = 1, RUNES do
		runes[i] = part(folder, "Rune", Enum.PartType.Block, Vector3.new(0.25, 0.6, 0.35), GOLD, 1)
	end
	local flash = part(folder, "Flash", Enum.PartType.Ball, Vector3.one * 0.5, TURQUOISE, 1)
	local shots = {}
	for _, side in BossVolley.Sides do
		local lane = part(folder, "Lane", Enum.PartType.Block, Vector3.new(cfg.Radius * 2, 0.12, 1), GOLD, 1)
		local ball = part(folder, "Bolt", Enum.PartType.Ball, Vector3.one * cfg.Radius * 2, TURQUOISE, 1)
		local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
		a0.Position, a1.Position = Vector3.new(0, cfg.Radius * 0.6, 0), Vector3.new(0, -cfg.Radius * 0.6, 0)
		a0.Parent, a1.Parent = ball, ball
		local trail = Instance.new("Trail")
		trail.Attachment0, trail.Attachment1 = a0, a1
		trail.Lifetime = 0.25
		trail.Color = ColorSequence.new(TURQUOISE, PURPLE)
		trail.Transparency = NumberSequence.new(0.2, 1)
		trail.LightEmission = 0.6
		trail.FaceCamera = true
		trail.Enabled = false
		trail.Parent = ball
		shots[side] = { ball = ball, lane = lane, ended = false, burst = nil }
	end
	folder.Parent = workspace
	return { model = model, seq = seq, folder = folder, disc = disc, runes = runes, flash = flash, shots = shots }
end

local function clear(model: Model)
	local fx = active[model]
	if fx then
		finished[model] = fx.seq
		fx.folder:Destroy()
		active[model] = nil
	end
end

-- Ступни бойца-цели (TargetUserId) — для полос до фиксации.
local function targetFeet(model: Model): Vector3?
	local userId = model:GetAttribute("TargetUserId")
	local player = if type(userId) == "number" then Players:GetPlayerByUserId(userId) else nil
	local character = player and player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not root then
		return nil
	end
	local hip = if humanoid then humanoid.HipHeight else 2
	return root.Position - Vector3.new(0, root.Size.Y / 2 + hip, 0)
end

local function placeLane(lane: BasePart, from: Vector3, to: Vector3, width: number)
	local d = Vector3.new(to.X - from.X, 0, to.Z - from.Z)
	local len = math.max(d.Magnitude, 0.1)
	lane.Size = Vector3.new(width, 0.12, len)
	lane.CFrame = CFrame.lookAt((from + to) / 2 + Vector3.new(0, 0.08, 0), to + Vector3.new(0, 0.08, 0))
end

local function update(fx: Fx, cfg: any, now: number)
	local model = fx.model
	local startAt = model:GetAttribute("VolleyAt")
	local origin = model:GetAttribute("VolleyOrigin")
	local root = model.PrimaryPart
	if type(startAt) ~= "number" or typeof(origin) ~= "Vector3" or not root then
		clear(model)
		return
	end
	local t = now - startAt
	local groundY = root.Position.Y
	local lockAt = model:GetAttribute("VolleyLockAt")
	local center = model:GetAttribute("VolleyDir")
	local dirs
	if typeof(center) == "Vector3" and type(lockAt) == "number" and now >= lockAt then
		dirs = BossVolley.FromCenter(center, cfg)
	else
		local feet = targetFeet(model)
		dirs = if feet then BossVolley.Directions(origin, feet, cfg) else nil
	end
	-- круг: раскрывается перед слежением, гаснет после выстрела; руны вращаются
	local open = math.clamp((t - (cfg.TrackFrom - FADE)) / FADE, 0, 1)
	local gone = math.clamp((t - cfg.Fire) / (FADE * 2), 0, 1)
	local alpha = 1 - open * (1 - gone)
	local facing = if dirs then dirs[0] else root.CFrame.ZVector
	local frame = CFrame.lookAt(origin, origin + facing) * CFrame.Angles(0, math.rad(90), 0) -- ось цилиндра (X) — вдоль полёта
	fx.disc.CFrame = frame
	fx.disc.Transparency = 0.45 + 0.55 * alpha
	local spin = math.rad(140) * t
	for i, rune in fx.runes do
		local a = spin + (i - 1) * 2 * math.pi / RUNES
		rune.CFrame = frame
			* CFrame.new(0, math.cos(a) * CIRCLE_RADIUS * 0.85, math.sin(a) * CIRCLE_RADIUS * 0.85)
			* CFrame.Angles(a, 0, 0)
		rune.Transparency = 0.1 + 0.9 * alpha
	end
	-- вспышка выстрела
	local ft = t - cfg.Fire
	if ft >= 0 and ft < 0.25 then
		fx.flash.Size = Vector3.one * (1 + ft * 24)
		fx.flash.CFrame = CFrame.new(origin)
		fx.flash.Transparency = 0.2 + 0.8 * ft / 0.25
	else
		fx.flash.Transparency = 1
	end
	-- полосы и снаряды
	local fireAt = startAt + cfg.Fire
	local pending = 0
	for side, shot in fx.shots do
		local dir = dirs and dirs[side]
		if not dir then
			shot.lane.Transparency = 1
			continue
		end
		local limit = BossVolley.Limit(origin, dir, cfg, groundY, nil)
		local endAt = model:GetAttribute("VolleyEnd" .. SIDE_KEY[side])
		local endAge = if type(endAt) == "number" then endAt - fireAt else limit / cfg.Speed
		local age = now - fireAt
		-- полоса: с начала слежения до конца снаряда; золотая — следит, бирюзовая и пульсирует — зафиксирована
		if t >= cfg.TrackFrom and age < endAge then
			local from, to = BossVolley.Lane(origin, dir, cfg, groundY, limit)
			placeLane(shot.lane, from, to, cfg.Radius * 2)
			local locked = type(lockAt) == "number" and now >= lockAt
			shot.lane.Color = if locked then TURQUOISE else GOLD
			shot.lane.Transparency = if locked then 0.45 + 0.2 * math.sin(now * 14) else 0.7
		else
			shot.lane.Transparency = 1
		end
		if age < 0 then
			pending += 1
			continue
		end
		if age < endAge then
			pending += 1
			shot.ball.CFrame = CFrame.new(BossVolley.Position(origin, dir, cfg, age, limit))
			shot.ball.Transparency = 0.05
			local trail = shot.ball:FindFirstChildOfClass("Trail")
			if trail then
				trail.Enabled = true
			end
		else
			if not shot.ended then
				shot.ended = true
				shot.ball.Transparency = 1
				local trail = shot.ball:FindFirstChildOfClass("Trail")
				if trail then
					trail.Enabled = false
				end
				local at = BossVolley.Position(origin, dir, cfg, endAge, limit)
				local burst = part(fx.folder, "Burst", Enum.PartType.Cylinder, Vector3.new(0.2, 1, 1), GOLD, 0.2)
				burst.CFrame = CFrame.new(at) * CFrame.Angles(0, 0, math.rad(90))
				shot.burst = burst
			end
			local bt = age - endAge
			if shot.burst then
				if bt < AFTER then
					local k = bt / AFTER
					shot.burst.Size = Vector3.new(0.2, 2 + 6 * k, 2 + 6 * k)
					shot.burst.Transparency = 0.2 + 0.8 * k
					pending += 1
				else
					shot.burst:Destroy()
					shot.burst = nil
				end
			end
		end
	end
	-- все снаряды погасли — или залп давно кончился (страховка)
	if (t > cfg.Fire and pending == 0) or t > cfg.Duration + 4 then
		clear(model)
	end
end

local function step()
	local now = workspace:GetServerTimeNow()
	for _, model in CollectionService:GetTagged(TAG) do
		if not model:IsA("Model") then
			continue
		end
		local zone = model:GetAttribute("Zone")
		local cfg = Battle.Bosses[zone] and Battle.Bosses[zone].Volley
		if not cfg then
			continue
		end
		local seq = model:GetAttribute("VolleySeq")
		local fx = active[model]
		local cancelAt = model:GetAttribute("VolleyCancelAt")
		if type(seq) ~= "number" then
			continue
		end
		if fx and fx.seq ~= seq then
			clear(model)
			fx = nil
		end
		local startAt = model:GetAttribute("VolleyAt")
		local canceled = type(cancelAt) == "number" and type(startAt) == "number" and cancelAt >= startAt
		if canceled then
			clear(model) -- бой кончился: предупреждения и снаряды исчезают сразу
			continue
		end
		if not fx then
			if finished[model] == seq then
				continue
			end
			if type(startAt) == "number" and now - startAt < cfg.Duration + 1 then
				fx = build(model, seq, cfg)
				active[model] = fx
			else
				continue
			end
		end
		update(fx :: Fx, cfg, now)
	end
	for model in active do
		if not model.Parent then
			clear(model)
		end
	end
	for model in finished do
		if not model.Parent then
			finished[model] = nil
		end
	end
end

function BossVolleyController.Init()
	RunService.RenderStepped:Connect(step)
end

return BossVolleyController

-- Эффекты поимки «Ловибум» у всех игроков рядом (D55, CatchEffect): Ловибум в руке ловящего (у самого ловящего —
-- нет: он смотрит от первого лица, Ловибум у него внизу экрана); бросок — полёт по дуге кристаллом вперёд с вращением
-- и коротким следом из квадратных искр; промах — летит дальше и падает; попадание — вспышка, Ловибум подскакивает над
-- существом, когти раскрываются, существо светом втягивается в кристалл, когти смыкаются, Ловибум падает и качается:
-- поимка — после третьего покачивания щелчок и звёзды, закрытый Ловибум лежит на месте, пока идёт бой (существо
-- спрятано, CatchMode = Hidden); побег — после 1–3 покачиваний существо выскакивает, Ловибум рассыпается квадратами.
-- Свой бросок начинается сразу после жеста (LocalThrow — от Ловибума внизу экрана к точке, которую посчитает и сервер),
-- исход подставляется из CatchEffect. Время — общее время сервера (release, arrival): у всех одинаково, опоздавший
-- видит середину. Свет — один PointLight и только на время полёта и захвата (слабые телефоны). Звуки —
-- GameConfig.Sounds.Lovibum (пока пусто). Модели — World/LovibumModel (Part-версия).
-- Зависит от Remotes, Config/GameConfig, Config/Items, Config/LovibumRigs.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local Items = require(Config:WaitForChild("Items"))
local LovibumRigs = require(Config:WaitForChild("LovibumRigs"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local LovibumModel = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("LovibumModel"))

local G = GameConfig.Catch.Game
local SOUNDS = GameConfig.Sounds.Lovibum
local HAND_SCALE = 0.75
local HOVER = 1.3 -- над макушкой существа
local LIGHT_RANGE = 9
local WOBBLE_START, WOBBLE_EVERY, WOBBLE_LEN = 1.15, 0.55, 0.42 -- покачивания на земле: начало, шаг, длительность
local CAUGHT_COLOR = Color3.fromHex("FFE15A") -- звёзды поимки
local WAIT = 2 -- свой бросок без ответа сервера: столько секунд висит у цели, потом гаснет

local LovibumFxController = {}

-- update(время сервера) → true, пока эффект жив; resolve — исход своего броска с сервера
type Fx = { update: (number) -> boolean, cleanup: () -> (), resolve: (any) -> (), alive: boolean }

local folder: Folder
local effects: { Fx } = {}
local hands: { [number]: { model: Model, hidden: number } } = {} -- UserId → Ловибум в руке
local pending: { [number]: { fx: Fx, at: number } } = {} -- свои броски до ответа сервера (по времени отпускания)

local function now(): number
	return workspace:GetServerTimeNow()
end

local function smooth(x: number): number
	x = math.clamp(x, 0, 1)
	return x * x * (3 - 2 * x)
end

local function play(name: string, at: Vector3)
	local id = SOUNDS[name]
	if type(id) ~= "string" or id == "" then
		return -- звуков пока нет (решение владельца): место для подключения
	end
	local holder = Instance.new("Part")
	holder.Anchored, holder.CanCollide, holder.CanQuery, holder.CanTouch = true, false, false, false
	holder.Transparency = 1
	holder.Size = Vector3.one
	holder.Position = at
	holder.Parent = folder
	local sound = Instance.new("Sound")
	sound.SoundId = id
	sound.Parent = holder
	sound:Play()
	task.delay(4, function()
		holder:Destroy()
	end)
end

local function glowColor(kind: string): Color3
	local rig = LovibumRigs.Types[kind]
	return Color3.fromHex(rig and rig.Glow or "8AFFF2")
end

-- Светящийся брусок от a до b (сеть, луч).
local function bar(a: Vector3, b: Vector3, w: number, color: Color3): Part
	local p = Instance.new("Part")
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
	p.Material = Enum.Material.Neon
	p.Color = color
	local d = b - a
	p.Size = Vector3.new(w, w, math.max(d.Magnitude, 0.01))
	p.CFrame = CFrame.lookAt((a + b) / 2, b)
	p.Parent = folder
	return p
end

local function handOf(userId: number): BasePart?
	local who = Players:GetPlayerByUserId(userId)
	local character = who and who.Character
	if not character then
		return nil
	end
	return (character:FindFirstChild("RightHand") or character:FindFirstChild("Right Arm")) :: BasePart?
end

local function handCFrame(userId: number): CFrame?
	local hand = handOf(userId)
	if not hand then
		return nil
	end
	return hand.CFrame * CFrame.new(0, -hand.Size.Y / 2 - 0.15, -0.25)
end

-- Ловибум в руке ловящего (до конца поимки); вид — последний брошенный. У себя — нет (первое лицо).
local function setHand(userId: number, kind: string?)
	local entry = hands[userId]
	if entry then
		entry.model:Destroy()
		hands[userId] = nil
	end
	if kind and userId ~= Players.LocalPlayer.UserId then
		local model = LovibumModel.Build(kind)
		model.Parent = folder
		hands[userId] = { model = model, hidden = 0 }
	end
end

type Spark = { part: Part, from: Vector3, v: Vector3, born: number, life: number }

-- Квадратная искра: из at со скоростью v, гаснет за life секунд (падает).
local function spark(list: { Spark }, at: Vector3, v: Vector3, color: Color3, size: number, t: number, life: number)
	local p = Instance.new("Part")
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
	p.Material = Enum.Material.Neon
	p.Color = color
	p.Size = Vector3.one * size
	p.CFrame = CFrame.new(at)
	p.Parent = folder
	table.insert(list, { part = p, from = at, v = v, born = t, life = life })
end

-- Вспышка: count искр во все стороны (lift — сколько вверх).
local function burst(list: { Spark }, at: Vector3, count: number, speed: number, color: Color3, size: number, t: number)
	for i = 1, count do
		local a = i / count * 2 * math.pi
		local e = (i % 3) * 0.35 + 0.15
		local v = Vector3.new(math.cos(a) * math.cos(e), math.sin(e) + 0.6, math.sin(a) * math.cos(e)) * speed
		spark(list, at, v, color, size, t, 0.55)
	end
end

local function moveSparks(list: { Spark }, t: number)
	for i = #list, 1, -1 do
		local s = list[i]
		local age = t - s.born
		local a = age / s.life
		if a >= 1 then
			s.part:Destroy()
			table.remove(list, i)
		else
			s.part.CFrame = CFrame.new(s.from + s.v * age - Vector3.new(0, 6 * age * age, 0))
				* CFrame.Angles(age * 5, age * 3, 0)
			s.part.Transparency = 0.15 + 0.85 * math.max(a, 0)
		end
	end
end

-- Существо у этого клиента: втянуто в Ловибум — не видно, вырвалось — снова видно (пойманное прячет CreatureController).
local function setCreatureHidden(part: any, hidden: boolean)
	if typeof(part) ~= "Instance" or not part.Parent then
		return
	end
	if not hidden and part:GetAttribute("CatchMode") == "Hidden" then
		return
	end
	for _, d in part:GetDescendants() do
		if d:IsA("BasePart") then
			d.LocalTransparencyModifier = if hidden then 1 else 0
		end
	end
end

-- Полёт и поимка одного броска. Полёт — по дуге кристаллом вперёд с коротким следом; промах — летит дальше и падает;
-- попадание — Ловибум подскакивает над существом, когти раскрываются, существо светом втягивается в кристалл, когти
-- смыкаются, Ловибум падает на землю и качается: поимка — после третьего покачивания щелчок и звёзды из квадратов,
-- закрытый Ловибум лежит, пока идёт бой; побег — после 1–3 покачиваний (у всех одинаково, по времени броска) когти
-- раскрываются, существо выскакивает, Ловибум рассыпается. Исход может прийти позже начала (свой бросок).
local function throwFx(payload: any): Fx?
	local kind = payload.lovibum
	local release, arrival = payload.release, payload.arrival
	if
		type(kind) ~= "string"
		or not LovibumRigs.Types[kind]
		or type(release) ~= "number"
		or type(arrival) ~= "number"
		or typeof(payload.aim) ~= "Vector3"
	then
		return nil
	end
	local part = payload.part
	local def = typeof(part) == "Instance" and Items[part:GetAttribute("ItemId")]
	local size = if def then def.size else Vector3.new(2, 2, 2)
	local outcome: string? = payload.outcome
	local aim: Vector3 = payload.aim
	local center: Vector3 = if typeof(payload.center) == "Vector3" then payload.center else aim
	local from: Vector3
	local fromScale = HAND_SCALE
	if typeof(payload.from) == "Vector3" then
		from = payload.from
		fromScale = if type(payload.fromScale) == "number" then math.clamp(payload.fromScale, 0.05, 2) else HAND_SCALE
	else
		local cf = handCFrame(payload.user)
		local camera = workspace.CurrentCamera
		if payload.user == Players.LocalPlayer.UserId and camera then
			from = camera.CFrame.Position + camera.CFrame.LookVector * 2 - camera.CFrame.UpVector * 1.2 -- от первого лица
		else
			from = if cf then cf.Position else center + Vector3.new(0, 2, 8)
		end
	end
	local color = glowColor(kind)
	local model = LovibumModel.Build(kind)
	model.Parent = folder
	LovibumModel.SetLight(model, LIGHT_RANGE, 1.2)
	local hand = hands[payload.user]
	if hand then
		hand.hidden = arrival + G.CaptureTime -- рука пустая, пока Ловибум в деле
	end
	play("Throw", from)
	local sparks: { Spark } = {}
	local lastDot = 0
	local arc = math.clamp((aim - from).Magnitude * 0.18, 0.5, 2.2)
	local yaw = math.atan2(from.X - aim.X, from.Z - aim.Z) -- Ловибум на земле — к бросившему
	local breaks = 1 + math.floor(release * 1000) % 3 -- побег: после стольких покачиваний
	local ghost: Part? = nil
	local beam: Part? = nil
	local hidden = false
	local stage = 0 -- пройденные отметки: 1 — вспышка, 2 — втягивание, 3 — щелчок / побег
	local wobbled = 0
	local capEnd = arrival + G.CaptureTime

	local function hover(): Vector3
		return center + Vector3.new(0, size.Y / 2 + HOVER, 0)
	end
	local function ground(): Vector3
		return center - Vector3.new(0, size.Y / 2, 0)
	end

	local function cleanup()
		model:Destroy()
		for _, s in sparks do
			s.part:Destroy()
		end
		if ghost then
			ghost:Destroy()
		end
		if beam then
			beam:Destroy()
		end
		if hidden then
			setCreatureHidden(part, false) -- поймано и спрятано сервером (Hidden) — не трогает
		end
	end

	local function update(t: number): boolean
		moveSparks(sparks, t)
		local k = t - arrival
		if k < 0 then
			-- полёт по дуге, кристаллом вперёд, с вращением; ближе — крупнее не нужно: перспектива сама
			local f = math.clamp((t - release) / (arrival - release), 0, 1)
			local function at(x: number): Vector3
				return from:Lerp(aim, x) + Vector3.new(0, arc * 4 * x * (1 - x), 0)
			end
			local pos = at(f)
			local dir = at(math.min(f + 0.05, 1)) - pos
			dir = if dir.Magnitude > 1e-3 then dir.Unit else (aim - from).Unit
			local cf = CFrame.lookAt(pos, pos + dir) * CFrame.Angles(-math.pi / 2, 0, 0) * CFrame.Angles(0, t * 14, 0)
			LovibumModel.Place(model, cf * CFrame.new(0, -0.6, 0), 0, fromScale + (1 - fromScale) * f)
			if t - lastDot > 0.045 and f < 1 then
				lastDot = t
				spark(sparks, pos, Vector3.zero, color, 0.16, t, 0.35)
			end
			return true
		end
		if outcome == nil then
			-- свой бросок, сервер ещё не ответил: Ловибум висит у цели (не показываем промах, которого не было)
			local f = math.clamp((k - WAIT) / 0.4, 0, 1)
			LovibumModel.Place(model, CFrame.new(aim + Vector3.new(0, 0.1 * math.sin(t * 6), 0)), 0, 1)
			LovibumModel.SetTransparency(model, f)
			return f < 1
		end
		if outcome ~= "Caught" and outcome ~= "Escape" then
			-- промах: летит дальше и падает, гаснет
			local f = math.clamp(k / 0.6, 0, 1)
			if f >= 1 then
				return #sparks > 0
			end
			local dir = Vector3.new(aim.X - from.X, 0, aim.Z - from.Z)
			dir = if dir.Magnitude > 1e-3 then dir.Unit else Vector3.zAxis
			local pos = aim + dir * 3 * f - Vector3.new(0, 4 * f * f, 0)
			LovibumModel.Place(model, CFrame.new(pos) * CFrame.Angles(f * 3, t * 10, 0), 0, 1)
			LovibumModel.SetTransparency(model, f)
			LovibumModel.SetLight(model, 0)
			return true
		end
		-- попадание: вспышка, подскок над существом, когти раскрываются
		if stage < 1 then
			stage = 1
			burst(sparks, aim, 10, 5, color, 0.22, t)
			play("Open", hover())
		end
		local open = smooth(k / 0.2) * (1 - smooth((k - 0.6) / 0.15))
		local pos: Vector3
		local tilt = 0
		if k < 0.75 then
			pos = aim:Lerp(hover(), smooth(k / 0.25))
		else
			-- падает на землю с маленьким отскоком
			local d = math.clamp((k - 0.75) / 0.3, 0, 1)
			local bounce = if d >= 1
				then 0.25 * math.max(0, math.sin(math.pi * math.clamp((k - 1.05) / 0.2, 0, 1)))
				else 0
			pos = hover():Lerp(ground(), d * d) + Vector3.new(0, bounce, 0)
		end
		-- существо светом втягивается в кристалл
		if k >= 0.2 and k < 0.65 then
			if not ghost then
				local g = Instance.new("Part")
				g.Anchored, g.CanCollide, g.CanQuery, g.CanTouch, g.CastShadow = true, false, false, false, false
				g.Material = Enum.Material.Neon
				g.Color = color
				g.Parent = folder
				ghost = g
				beam = bar(center, hover(), 0.15, color)
				play("Absorb", center)
			end
			local f = smooth((k - 0.2) / 0.45)
			local g = ghost :: Part
			g.Size = size * (1 - f) + Vector3.one * 0.2
			g.CFrame = CFrame.new(center:Lerp(hover(), f * f))
			g.Transparency = 0.35 + 0.6 * f
			if k >= 0.3 and not hidden then
				hidden = true
				setCreatureHidden(part, true)
			end
		elseif ghost then
			ghost:Destroy()
			ghost = nil
			if beam then
				beam:Destroy()
				beam = nil
			end
		end
		-- покачивания на земле
		local last = if outcome == "Caught" then 3 else breaks
		local w = k - WOBBLE_START
		local index = math.floor(w / WOBBLE_EVERY)
		if w >= 0 and index < last then
			local x = (w - index * WOBBLE_EVERY) / WOBBLE_LEN
			if x < 1 then
				tilt = 0.42 * math.sin(2 * math.pi * x) * (1 - x * 0.5)
				if wobbled <= index then
					wobbled = index + 1
					play("Wobble", ground())
				end
			end
		end
		local done = w >= last * WOBBLE_EVERY
		if outcome == "Escape" and done then
			-- побег: когти раскрываются, существо выскакивает, Ловибум рассыпается и гаснет
			if stage < 3 then
				stage = 3
				hidden = false
				setCreatureHidden(part, false)
				burst(sparks, ground() + Vector3.new(0, 0.5, 0), 14, 6, color, 0.3, t)
				play("Escape", center)
			end
			local f = math.clamp((w - last * WOBBLE_EVERY) / 0.5, 0, 1)
			LovibumModel.SetLight(model, 0)
			LovibumModel.SetTransparency(model, f)
			LovibumModel.Place(model, CFrame.new(ground()) * CFrame.Angles(0, yaw, 0), 1, 1)
			return f < 1 or #sparks > 0
		end
		if outcome == "Caught" and done then
			-- щелчок: звёзды из квадратов, закрытый Ловибум лежит на месте, пока идёт бой (существо в нём)
			if stage < 3 then
				stage = 3
				LovibumModel.SetLight(model, 0)
				burst(sparks, ground() + Vector3.new(0, 0.8, 0), 12, 4, CAUGHT_COLOR, 0.26, t)
				play("Caught", center)
			end
			LovibumModel.Place(model, CFrame.new(ground()) * CFrame.Angles(0, yaw, 0), 0, 1)
			local stillHidden = typeof(part) == "Instance"
				and part.Parent ~= nil
				and part:GetAttribute("CatchMode") == "Hidden"
			return stillHidden or t < capEnd + 1.5 or #sparks > 0
		end
		LovibumModel.Place(
			model,
			CFrame.new(pos) * CFrame.Angles(0, if k < 0.75 then t * 1.5 else yaw, 0) * CFrame.Angles(0, 0, tilt),
			open,
			1
		)
		return true
	end

	local function resolve(p: any)
		if type(p.outcome) == "string" then
			outcome = p.outcome
		end
		if typeof(p.aim) == "Vector3" then
			aim = p.aim
		end
		if typeof(p.center) == "Vector3" then
			center = p.center
		end
	end

	local fx: Fx = { update = update, cleanup = cleanup, resolve = resolve, alive = true }
	table.insert(effects, fx)
	return fx
end

-- Свой бросок — сразу после жеста (не ждать сервер): полёт к той же точке, что посчитает сервер; исход — с CatchEffect.
function LovibumFxController.LocalThrow(payload: any)
	payload.user = Players.LocalPlayer.UserId
	local fx = throwFx(payload)
	if fx then
		pending[payload.release] = { fx = fx, at = now() }
	end
end

local function onEffect(payload: any)
	if type(payload) ~= "table" or type(payload.user) ~= "number" then
		return
	end
	if payload.kind == "Start" then
		setHand(payload.user, "Boom")
	elseif payload.kind == "Throw" then
		if hands[payload.user] and hands[payload.user].model:GetAttribute("LovibumKind") ~= payload.lovibum then
			setHand(payload.user, payload.lovibum)
		end
		local mine = if type(payload.release) == "number" then pending[payload.release] else nil
		if mine and payload.user == Players.LocalPlayer.UserId then
			pending[payload.release] = nil
		end
		if mine and mine.fx.alive and payload.user == Players.LocalPlayer.UserId then
			mine.fx.resolve(payload)
		else
			throwFx(payload) -- чужой бросок или свой, чей эффект уже погас (ответ сервера опоздал)
		end
	elseif payload.kind == "End" then
		setHand(payload.user, nil)
	end
end

local function step()
	local t = now()
	for release, entry in pending do
		if t - entry.at > 5 then
			pending[release] = nil -- сервер не ответил
		end
	end
	for i = #effects, 1, -1 do
		local fx = effects[i]
		local ok, alive = pcall(fx.update, t)
		if not ok or not alive then
			fx.alive = false
			fx.cleanup()
			table.remove(effects, i)
		end
	end
	for userId, entry in hands do
		local cf = handCFrame(userId)
		local visible = cf ~= nil and t >= entry.hidden
		if visible then
			LovibumModel.Place(entry.model, (cf :: CFrame) * CFrame.new(0, -0.45, 0), 0, HAND_SCALE)
		end
		LovibumModel.SetTransparency(entry.model, if visible then 0 else 1)
		local who = Players:GetPlayerByUserId(userId)
		if not who or who:GetAttribute("Catching") == nil then
			setHand(userId, nil)
		end
	end
end

function LovibumFxController.Init()
	folder = Instance.new("Folder")
	folder.Name = "LovibumFx"
	folder.Parent = workspace
	Remotes.Get(Remotes.Names.CatchEffect).OnClientEvent:Connect(onEffect)
	RunService.RenderStepped:Connect(step)
end

return LovibumFxController

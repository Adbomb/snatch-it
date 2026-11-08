-- Эффекты поимки «Ловибум» у всех игроков рядом (D55, CatchEffect): Ловибум в руке ловящего; бросок — полёт по дуге
-- кристаллом вперёд с вращением и коротким следом из квадратных искр; промах — летит дальше и падает; попадание —
-- зависает над существом, когти раскрываются, кристалл плетёт сеть-купол из квадратных ячеек, сеть стягивается в куб
-- света, луч уходит в кристалл, когти смыкаются; поимка — закрытый Ловибум лежит на месте, пока идёт бой (существо
-- спрятано, CatchMode = Hidden); побег — сеть рассыпается квадратами. Время — общее время сервера (release, arrival
-- из события): у всех одинаково, опоздавший видит середину. Свечение умеренное (существо видно сквозь сеть); свет —
-- один PointLight и только на время полёта и сети (слабые телефоны). Звуки — GameConfig.Sounds.Lovibum (пока пусто).
-- Модели — World/LovibumModel (Part-версия). Зависит от Remotes, Config/GameConfig, Config/Items, Config/LovibumRigs.

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

local LovibumFxController = {}

type Fx = { update: (number) -> boolean, cleanup: () -> () } -- update(время сервера) → true, пока эффект жив

local folder: Folder
local effects: { Fx } = {}
local hands: { [number]: { model: Model, hidden: number } } = {} -- UserId → Ловибум в руке

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

-- Ловибум в руке ловящего (до конца поимки); вид — последний брошенный.
local function setHand(userId: number, kind: string?)
	local entry = hands[userId]
	if entry then
		entry.model:Destroy()
		hands[userId] = nil
	end
	if kind then
		local model = LovibumModel.Build(kind)
		model.Parent = folder
		hands[userId] = { model = model, hidden = 0 }
	end
end

-- Сеть-купол над существом: квадратные кольца и линии по граням (как в концепте v5).
local function buildNet(center: Vector3, half: number, height: number, color: Color3): { Part }
	local parts = {}
	local rings, lines = 4, 3
	local base = center - Vector3.new(0, height / 2, 0)
	local hs, zs = {}, {}
	for i = 0, rings do
		hs[i] = 0.25 * half + (half - 0.25 * half) * math.cos(math.pi / 2 * i / rings) ^ 0.6
		zs[i] = height * (i / rings) ^ 1.1
	end
	for i = 0, rings do
		local h, z = hs[i], zs[i]
		local c = {
			base + Vector3.new(-h, z, -h),
			base + Vector3.new(h, z, -h),
			base + Vector3.new(h, z, h),
			base + Vector3.new(-h, z, h),
		}
		for k = 1, 4 do
			table.insert(parts, bar(c[k], c[k % 4 + 1], 0.06, color))
		end
	end
	for side = 0, 3 do
		for j = 0, lines do
			local s = -1 + 2 * j / lines
			local function at(i: number): Vector3
				local h = hs[i]
				local p = ({
					Vector2.new(s * h, -h),
					Vector2.new(h, s * h),
					Vector2.new(-s * h, h),
					Vector2.new(-h, -s * h),
				})[side + 1]
				return base + Vector3.new(p.X, zs[i], p.Y)
			end
			for i = 0, rings - 1 do
				table.insert(parts, bar(at(i), at(i + 1), 0.05, color))
			end
		end
	end
	for _, p in parts do
		p.Transparency = 1
	end
	return parts
end

-- Полёт и поимка одного броска.
local function throwFx(payload: any)
	local kind = payload.lovibum
	local release, arrival = payload.release, payload.arrival
	if type(kind) ~= "string" or type(release) ~= "number" or type(arrival) ~= "number" then
		return
	end
	local part = payload.part
	local def = typeof(part) == "Instance" and Items[part:GetAttribute("ItemId")]
	local size = if def then def.size else Vector3.new(2, 2, 2)
	local center: Vector3 = if typeof(payload.center) == "Vector3" then payload.center else payload.aim
	local outcome = payload.outcome
	local target = if outcome == "Miss" then payload.aim else center
	local startCF = handCFrame(payload.user) or CFrame.new(center + Vector3.new(0, 2, 8))
	local from = startCF.Position
	local color = glowColor(kind)
	local model = LovibumModel.Build(kind)
	model.Parent = folder
	LovibumModel.SetLight(model, LIGHT_RANGE, 1.2)
	local hand = hands[payload.user]
	if hand then
		hand.hidden = arrival + G.CaptureTime -- рука пустая, пока Ловибум в деле
	end
	play("Throw", from)
	local trail: { { part: Part, born: number } } = {}
	local lastDot = 0
	local half = math.max(size.X, size.Z) / 2 + 0.5
	local hover = center + Vector3.new(0, size.Y / 2 + HOVER, 0)
	local net: { Part }? = nil
	local cube: Part? = nil
	local beam: Part? = nil
	local shards: { { part: Part, v: Vector3 } }? = nil
	local opened, netAt, caughtShown = false, false, false
	local capEnd = arrival + G.CaptureTime

	local function cleanup()
		model:Destroy()
		for _, d in trail do
			d.part:Destroy()
		end
		for _, list in { net or {} } do
			for _, p in list do
				p:Destroy()
			end
		end
		if cube then
			cube:Destroy()
		end
		if beam then
			beam:Destroy()
		end
		for _, s in shards or {} do
			s.part:Destroy()
		end
	end

	local function update(t: number): boolean
		-- след: квадратные искры цвета ядра, короткий
		for i = #trail, 1, -1 do
			local d = trail[i]
			local age = (t - d.born) / 0.35
			if age >= 1 then
				d.part:Destroy()
				table.remove(trail, i)
			else
				d.part.Transparency = 0.2 + 0.8 * age
				d.part.Size = Vector3.one * 0.18 * (1 - age)
			end
		end
		if t < arrival then
			-- полёт по дуге, кристаллом вперёд, с вращением
			local f = math.clamp((t - release) / (arrival - release), 0, 1)
			local pos = from:Lerp(target, f) + Vector3.new(0, 2.2 * 4 * f * (1 - f), 0)
			local ahead = from:Lerp(target, math.min(f + 0.05, 1))
				+ Vector3.new(0, 2.2 * 4 * (f + 0.05) * (0.95 - f), 0)
			local dir = (ahead - pos)
			dir = if dir.Magnitude > 1e-3 then dir.Unit else (target - from).Unit
			local cf = CFrame.lookAt(pos, pos + dir) * CFrame.Angles(-math.pi / 2, 0, 0) * CFrame.Angles(0, t * 14, 0)
			LovibumModel.Place(model, cf * CFrame.new(0, -0.6, 0), 0, 1)
			if t - lastDot > 0.045 then
				lastDot = t
				local dot = Instance.new("Part")
				dot.Anchored, dot.CanCollide, dot.CanQuery, dot.CanTouch, dot.CastShadow =
					true, false, false, false, false
				dot.Material = Enum.Material.Neon
				dot.Color = color
				dot.Size = Vector3.one * 0.18
				dot.CFrame = CFrame.new(pos) * CFrame.Angles(0.6, t * 3, 0.4)
				dot.Parent = folder
				table.insert(trail, { part = dot, born = t })
			end
			return true
		end
		if outcome == "Miss" then
			-- промах: летит дальше и падает, гаснет
			local f = (t - arrival) / 0.6
			if f >= 1 then
				return #trail > 0
			end
			local dir = (target - from)
			dir = Vector3.new(dir.X, 0, dir.Z)
			dir = if dir.Magnitude > 1e-3 then dir.Unit else Vector3.zAxis
			local pos = target + dir * 3 * f - Vector3.new(0, 4 * f * f, 0)
			LovibumModel.Place(model, CFrame.new(pos) * CFrame.Angles(f * 3, t * 10, 0), 0, 1)
			LovibumModel.SetTransparency(model, f)
			LovibumModel.SetLight(model, 0)
			return true
		end
		-- попадание: зависает над существом
		local k = t - arrival
		local open = smooth(k / 0.25) * (1 - smooth((k - 1.6) / 0.3))
		if not opened then
			opened = true
			play("Open", hover)
		end
		LovibumModel.Place(model, CFrame.new(hover) * CFrame.Angles(0, t * 1.5, 0), open, 1)
		if k >= 0.2 and not net then
			net = buildNet(center, half, size.Y + 0.5, color)
		end
		if net then
			-- сеть опускается сверху и проявляется; затем гаснет — её место занимает куб света
			local fadeIn = smooth((k - 0.2) / 0.4)
			local fadeOut = smooth((k - 0.85) / 0.3)
			if outcome == "Escape" and k >= 1.25 then
				fadeOut = 1
			end
			for _, p in net do
				p.Transparency = 1 - 0.75 * fadeIn * (1 - fadeOut)
			end
			if not netAt and fadeIn > 0.5 then
				netAt = true
				play("Net", center)
			end
		end
		if k >= 0.85 and not cube then
			cube = Instance.new("Part")
			local c = cube :: Part
			c.Anchored, c.CanCollide, c.CanQuery, c.CanTouch, c.CastShadow = true, false, false, false, false
			c.Material = Enum.Material.Neon
			c.Color = color
			c.Parent = folder
			beam = bar(center, hover, 0.15, color)
		end
		if cube then
			local f = smooth((k - 0.85) / 0.6)
			local escape = outcome == "Escape" and k >= 1.25
			local s = (1 - f) * math.max(size.X, size.Y, size.Z) * 0.9 + 0.3
			cube.Size = Vector3.one * s
			cube.CFrame = CFrame.new(center:Lerp(hover, f * f))
			cube.Transparency = if escape then 1 else 0.55 + 0.35 * f
			if beam then
				beam.Transparency = if escape or k > 1.7 then 1 else 0.35
			end
			if escape and not shards then
				-- побег: сеть рассыпается квадратами
				shards = {}
				play("Escape", center)
				for i = 1, 14 do
					local p = Instance.new("Part")
					p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
					p.Material = Enum.Material.Neon
					p.Color = color
					p.Size = Vector3.new(0.35, 0.35, 0.06)
					local a = i / 14 * 2 * math.pi
					local off = Vector3.new(math.cos(a) * half, (i % 4) * 0.4 - 0.4, math.sin(a) * half)
					p.CFrame = CFrame.new(center + off)
					p.Parent = folder;
					(shards :: any)[i] = { part = p, v = off.Unit * 6 + Vector3.new(0, 4, 0) }
				end
			end
		end
		if shards then
			local f = math.clamp((k - 1.25) / 0.7, 0, 1)
			for _, s in shards do
				s.part.CFrame = s.part.CFrame + s.v * (1 / 60) - Vector3.new(0, 9.8 * f / 60, 0)
				s.part.Transparency = f
			end
		end
		if outcome == "Caught" then
			if t >= capEnd then
				-- закрытый Ловибум лежит на месте поимки, пока идёт бой (существо в нём)
				LovibumModel.SetLight(model, 0)
				if not caughtShown then
					caughtShown = true
					play("Caught", center)
				end
				local ground = center - Vector3.new(0, size.Y / 2, 0)
				local drop = smooth((t - capEnd) / 0.35)
				LovibumModel.Place(model, CFrame.new(hover:Lerp(ground, drop)) * CFrame.Angles(0, t * 0.6, 0), 0, 1)
				local hidden = typeof(part) == "Instance"
					and part.Parent ~= nil
					and part:GetAttribute("CatchMode") == "Hidden"
				return hidden or t < capEnd + 1.5
			end
			return true
		end
		-- побег: Ловибум падает и гаснет
		if k >= 1.6 then
			local f = (k - 1.6) / 0.6
			LovibumModel.SetLight(model, 0)
			LovibumModel.SetTransparency(model, math.clamp(f, 0, 1))
			return f < 1 or (shards ~= nil and k < 2.2)
		end
		return true
	end

	table.insert(effects, { update = update, cleanup = cleanup })
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
		throwFx(payload)
	elseif payload.kind == "End" then
		setHand(payload.user, nil)
	end
end

local function step()
	local t = now()
	for i = #effects, 1, -1 do
		local fx = effects[i]
		local ok, alive = pcall(fx.update, t)
		if not ok or not alive then
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
		if not Players:GetPlayerByUserId(userId) then
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

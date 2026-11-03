-- Процедурные анимации босса (D18, D40, D42): по состоянию босса и времени с его начала — Transform каждого сустава
-- (Motor6D) между ключевыми позами скелета (Config/Boss<N>…Rig, имена поз у всех боссов одни). Считается на каждом
-- клиенте одинаково (состояние и время приходят атрибутами модели), поэтому все игроки видят одно и то же, а по сети
-- идут только атрибуты.
-- Состояния (как в BossService): Sleep, Wake, StandUp, ToCombat, Combat, Victory, Defeat, Return, FallAsleep.
-- Удары и попадания — короткие наложения поверх Combat (номера AttackSeq / HitSeq и время их начала).
-- Длительности — Config/Battle.Timeline. Ни от чего не зависит, кроме Config/Battle.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Battle = require(ReplicatedStorage.Shared.Config.Battle)

export type Rig = {
	Order: { string },
	Parts: { [string]: any },
	Poses: { [string]: { [string]: { number } } },
}

export type Input = {
	state: string,
	t: number, -- секунд с начала состояния
	moving: boolean, -- босс идёт (бег за игроком, возвращение)
	attackKind: string?, -- "bite" | "swipe"
	attackT: number?, -- секунд с начала последнего выпада (nil — давно)
	hitT: number?, -- секунд с последнего попадания по боссу
	clock: number, -- общее время для циклов (дыхание, шаги)
}

local ATTACK_TIME = 0.5 -- выпад: 0.2 замах и удар, остальное — возврат
local HIT_TIME = 0.35
local WALK_PERIOD = 0.55
local BREATH_PERIOD = 3.2

local BossAnim = {}

local cache: { [Rig]: { [string]: { [string]: CFrame } } } = {}

-- Поза name как набор CFrame суставов.
function BossAnim.Pose(rig: Rig, name: string): { [string]: CFrame }
	local byRig = cache[rig]
	if not byRig then
		byRig = {}
		cache[rig] = byRig
	end
	local pose = byRig[name]
	if not pose then
		pose = {}
		local data = rig.Poses[name]
		assert(data, "Нет позы " .. name)
		for part, n in data do
			pose[part] = CFrame.new(n[1], n[2], n[3], n[4], n[5], n[6], n[7], n[8], n[9], n[10], n[11], n[12])
		end
		byRig[name] = pose
	end
	return pose
end

local function smooth(x: number): number
	x = math.clamp(x, 0, 1)
	return x * x * (3 - 2 * x)
end

local function blend(rig: Rig, a: { [string]: CFrame }, b: { [string]: CFrame }, alpha: number): { [string]: CFrame }
	local out = {}
	for _, part in rig.Order do
		out[part] = a[part]:Lerp(b[part], alpha)
	end
	return out
end

-- Переход from → to за duration секунд (t — с начала), со сглаживанием.
local function ramp(rig: Rig, from: string, to: string, t: number, duration: number): { [string]: CFrame }
	return blend(rig, BossAnim.Pose(rig, from), BossAnim.Pose(rig, to), smooth(t / duration))
end

-- Цикл между двумя позами с периодом period.
local function cycle(rig: Rig, a: string, b: string, clock: number, period: number): { [string]: CFrame }
	local phase = 0.5 - 0.5 * math.cos(clock / period * 2 * math.pi)
	return blend(rig, BossAnim.Pose(rig, a), BossAnim.Pose(rig, b), phase)
end

-- Сон: лежит, дышит (корпус поднимается и опускается), изредка дёргает ухом (если у скелета есть уши).
local function sleeping(rig: Rig, clock: number): { [string]: CFrame }
	local pose = table.clone(BossAnim.Pose(rig, "sleep"))
	local breath = math.sin(clock / BREATH_PERIOD * 2 * math.pi)
	pose.Torso = pose.Torso * CFrame.new(0, 0.06 * breath, 0)
	pose.Head = pose.Head * CFrame.Angles(math.rad(1.5 * breath), 0, 0)
	local twitch = clock % 5.3
	if twitch < 0.25 and pose.EarL then
		pose.EarL = pose.EarL * CFrame.Angles(0, 0, math.rad(12 * math.sin(twitch / 0.25 * math.pi)))
	end
	return pose
end

-- Наложение выпада или попадания поверх позы.
local function overlay(rig: Rig, base: { [string]: CFrame }, input: Input): { [string]: CFrame }
	local pose = base
	local at = input.attackT
	if at and at < ATTACK_TIME then
		local target = BossAnim.Pose(rig, if input.attackKind == "swipe" then "swipe" else "bite")
		local w = if at < 0.2 then smooth(at / 0.2) else 1 - smooth((at - 0.2) / (ATTACK_TIME - 0.2))
		pose = blend(rig, pose, target, w)
	end
	local ht = input.hitT
	if ht and ht < HIT_TIME then
		local w = if ht < 0.08 then smooth(ht / 0.08) else 1 - smooth((ht - 0.08) / (HIT_TIME - 0.08))
		pose = blend(rig, pose, BossAnim.Pose(rig, "hit"), w * 0.85)
	end
	return pose
end

-- Transform каждого сустава для состояния.
function BossAnim.Sample(rig: Rig, input: Input): { [string]: CFrame }
	local tl = Battle.Timeline
	local state, t, clock = input.state, input.t, input.clock
	local pose
	if state == "Sleep" then
		pose = sleeping(rig, clock)
	elseif state == "Wake" then
		pose = ramp(rig, "sleep", "alert", t, tl.Wake)
	elseif state == "StandUp" then
		pose = ramp(rig, "alert", "stand", t, tl.StandUp)
	elseif state == "ToCombat" then
		pose = ramp(rig, "stand", "combat", t, tl.ToCombat)
	elseif state == "Combat" then
		if input.moving then
			pose = blend(rig, cycle(rig, "walkA", "walkB", clock, WALK_PERIOD), BossAnim.Pose(rig, "combat"), 0.35)
		else
			pose = cycle(rig, "combat", "combat2", clock, 0.9)
		end
		pose = overlay(rig, pose, input)
	elseif state == "Victory" then
		if t < 0.25 then
			pose = ramp(rig, "combat", "bark", t, 0.25)
		elseif t < tl.Victory - 0.4 then
			pose = cycle(rig, "bark", "bark2", t - 0.25, 0.4)
		else
			pose = ramp(rig, "bark", "stand", t - (tl.Victory - 0.4), 0.4)
		end
	elseif state == "Defeat" then
		if t < 0.15 then
			pose = ramp(rig, "combat", "hit", t, 0.15)
		elseif t < 0.75 then
			pose = ramp(rig, "hit", "dizzy", t - 0.15, 0.6)
		elseif t < tl.Defeat - 0.6 then
			pose = table.clone(BossAnim.Pose(rig, "dizzy"))
			pose.Head = pose.Head * CFrame.Angles(0, 0, math.rad(8 * math.sin((t - 0.75) * 7)))
		else
			pose = ramp(rig, "dizzy", "stand", t - (tl.Defeat - 0.6), 0.6)
		end
	elseif state == "Return" then
		pose = if input.moving then cycle(rig, "walkA", "walkB", clock, WALK_PERIOD) else BossAnim.Pose(rig, "stand")
	elseif state == "FallAsleep" then
		if t < tl.FallAsleep * 0.55 then
			pose = ramp(rig, "stand", "alert", t, tl.FallAsleep * 0.55)
		else
			pose = ramp(rig, "alert", "sleep", t - tl.FallAsleep * 0.55, tl.FallAsleep * 0.45)
		end
	else
		pose = BossAnim.Pose(rig, "stand")
	end
	return pose
end

return BossAnim

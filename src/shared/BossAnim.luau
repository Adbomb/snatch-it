-- Процедурные анимации босса (D18, D40, D42): по состоянию босса и времени с его начала — Transform каждого сустава
-- (Motor6D) между ключевыми позами скелета (Config/Boss<N>…Rig, имена поз у всех боссов одни). Считается на каждом
-- клиенте одинаково (состояние и время приходят атрибутами модели), поэтому все игроки видят одно и то же, а по сети
-- идут только атрибуты.
-- Состояния (как в BossService): Sleep, Wake, StandUp, ToCombat, Combat, Victory, Defeat, Return, FallAsleep.
-- Удары и попадания — короткие наложения поверх Combat (номера AttackSeq / HitSeq и время их начала).
-- Шаг (Combat и Return) включается и гаснет за один шаг цикла от смены Moving (атрибут MovingAt); каждый переход
-- начинается с живой позы того, что играло (сон с дыханием, бой с выпадом, шаг домой, головокружение, танец), —
-- на стыках состояний и при остановке позы не прыгают, длительности прежние.
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
	movingT: number?, -- секунд с тех пор, как начал или перестал идти (nil — давно)
	fromState: string?, -- прошлое состояние (разбудили, пока засыпал или только уснул)
	fromT: number?, -- сколько оно длилось к началу нынешнего, секунд
	attackKind: string?, -- "bite" | "swipe"
	attackT: number?, -- секунд с начала последнего выпада (nil — давно)
	hitT: number?, -- секунд с последнего попадания по боссу
	clock: number, -- общее время для циклов (дыхание, шаги)
}

local ATTACK_TIME = 0.5 -- выпад: 0.2 замах и удар, остальное — возврат
local HIT_TIME = 0.35
local WALK_PERIOD = 0.55
local WALK_BLEND = WALK_PERIOD / 2 -- шаг включается и гаснет за один шаг (полцикла), темп ходьбы тот же
local BREATH_PERIOD = 3.2
local BREATH_IN = BREATH_PERIOD / 2 -- уснул — дыхание набирает силу за полвдоха

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

local IDENTITY = CFrame.new()

-- Переход между ключевыми позами a → b по прежнему пути (как ramp), с живыми отклонениями: liveA — поза того, что
-- играло (её отличие от a гаснет), liveB — того, что будет (отличие от b набирает силу). Отклонения малы (дыхание,
-- шаг, покачивание, выпад, танец), поэтому путь поворота не перескакивает — у пса задние ноги в позах сна и ходьбы
-- повёрнуты почти на 180°, и прямое смешение живой позы шага с позой сна выбирало то одну, то другую сторону.
local function bridge(
	rig: Rig,
	a: string,
	liveA: { [string]: CFrame }?,
	b: string,
	liveB: { [string]: CFrame }?,
	alpha: number
): { [string]: CFrame }
	local from, to = BossAnim.Pose(rig, a), BossAnim.Pose(rig, b)
	local out = {}
	for _, part in rig.Order do
		local cf = from[part]:Lerp(to[part], alpha)
		if liveA then
			cf = cf * IDENTITY:Lerp(from[part]:Inverse() * liveA[part], 1 - alpha)
		end
		if liveB then
			cf = cf * IDENTITY:Lerp(to[part]:Inverse() * liveB[part], alpha)
		end
		out[part] = cf
	end
	return out
end

-- Цикл между двумя позами с периодом period.
local function cycle(rig: Rig, a: string, b: string, clock: number, period: number): { [string]: CFrame }
	local phase = 0.5 - 0.5 * math.cos(clock / period * 2 * math.pi)
	return blend(rig, BossAnim.Pose(rig, a), BossAnim.Pose(rig, b), phase)
end

-- Сон: лежит, дышит (корпус поднимается и опускается), изредка дёргает ухом (если у скелета есть уши). depth — доля
-- дыхания: только что уснул — от нуля (засыпание кончается позой сна без дыхания), потом полное.
local function sleeping(rig: Rig, clock: number, depth: number): { [string]: CFrame }
	local pose = table.clone(BossAnim.Pose(rig, "sleep"))
	local breath = depth * math.sin(clock / BREATH_PERIOD * 2 * math.pi)
	pose.Torso = pose.Torso * CFrame.new(0, 0.06 * breath, 0)
	pose.Head = pose.Head * CFrame.Angles(math.rad(1.5 * breath), 0, 0)
	local twitch = clock % 5.3
	if twitch < 0.25 and pose.EarL then
		pose.EarL = pose.EarL * CFrame.Angles(0, 0, math.rad(12 * depth * math.sin(twitch / 0.25 * math.pi)))
	end
	return pose
end

-- Доля шага в позе: 1 — идёт, 0 — стоит; после смены Moving — плавно за WALK_BLEND.
local function walkWeight(input: Input): number
	local t = input.movingT
	if t == nil then
		return if input.moving then 1 else 0
	end
	local w = smooth(t / WALK_BLEND)
	return if input.moving then w else 1 - w
end

-- Поза возвращения домой: шаг поверх стойки (на стыке с поражением и победой — из стойки, которой они кончаются).
local function returning(rig: Rig, input: Input): { [string]: CFrame }
	local w = walkWeight(input)
	if w <= 0 then
		return BossAnim.Pose(rig, "stand")
	end
	local walk = cycle(rig, "walkA", "walkB", input.clock, WALK_PERIOD)
	if w >= 1 then
		return walk
	end
	return blend(rig, BossAnim.Pose(rig, "stand"), walk, w)
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

-- Бой: боевая стойка с покачиванием, на бегу — шаг поверх стойки (плавно при смене Moving), сверху выпады и попадания.
-- Не зависит от времени состояния — им же начинаются победа и поражение (с той позы, где застал конец боя).
local function fighting(rig: Rig, input: Input): { [string]: CFrame }
	local w = walkWeight(input)
	local idle = if w < 1 then cycle(rig, "combat", "combat2", input.clock, 0.9) else nil
	local run = if w > 0
		then blend(rig, cycle(rig, "walkA", "walkB", input.clock, WALK_PERIOD), BossAnim.Pose(rig, "combat"), 0.35)
		else nil
	local pose
	if idle and run then
		pose = blend(rig, idle, run, w)
	else
		pose = (run or idle) :: { [string]: CFrame }
	end
	return overlay(rig, pose, input)
end

-- Головокружение после поражения: поза dizzy, голова качается (с нуля в начале).
local function dizzy(rig: Rig, t: number): { [string]: CFrame }
	local pose = table.clone(BossAnim.Pose(rig, "dizzy"))
	pose.Head = pose.Head * CFrame.Angles(0, 0, math.rad(8 * math.sin((math.max(t, 0.75) - 0.75) * 7)))
	return pose
end

-- Transform каждого сустава для состояния. Каждый переход начинается с той позы, что играла (живой: с дыханием,
-- покачиванием, шагом, выпадом), и приходит в ту, что будет, — на стыках позы совпадают, длительности те же.
function BossAnim.Sample(rig: Rig, input: Input): { [string]: CFrame }
	local tl = Battle.Timeline
	local state, t, clock = input.state, input.t, input.clock
	local pose
	if state == "Sleep" then
		pose = sleeping(rig, clock, smooth(t / BREATH_IN))
	elseif state == "Wake" then
		local s = smooth(t / tl.Wake)
		local from, lasted = input.fromState, input.fromT
		if from == "FallAsleep" and lasted and lasted < tl.FallAsleep then
			-- разбудили, пока засыпал: засыпание (поза на пути «стойка → проснулся → сон») гаснет, «проснулся» набирает
			-- силу; засыпание идёт дальше по своему времени — клиент, к которому пробуждение пришло на кадр-два позже,
			-- продолжает с той позы, что показывал
			local caught = BossAnim.Sample(rig, {
				state = "FallAsleep",
				t = math.min(lasted + t, tl.FallAsleep),
				clock = clock,
				moving = false,
				movingT = input.movingT,
			})
			local alert = BossAnim.Pose(rig, "alert")
			pose = {}
			for _, part in rig.Order do
				pose[part] = caught[part]:Lerp(alert[part], s)
			end
		else
			-- со сна: дыхание той силы, что было (только уснул — ещё не в полную)
			local depth = if from == "Sleep" and lasted
				then smooth(lasted / BREATH_IN)
				elseif from == "FallAsleep" then 0
				else 1
			pose = bridge(rig, "sleep", sleeping(rig, clock, depth), "alert", nil, s)
		end
	elseif state == "StandUp" then
		pose = ramp(rig, "alert", "stand", t, tl.StandUp)
	elseif state == "ToCombat" then
		pose = bridge(rig, "stand", nil, "combat", fighting(rig, input), smooth(t / tl.ToCombat))
	elseif state == "Combat" then
		pose = fighting(rig, input)
	elseif state == "Victory" then
		if t < 0.25 then
			pose = bridge(rig, "combat", fighting(rig, input), "bark", nil, smooth(t / 0.25))
		elseif t < tl.Victory - 0.4 then
			pose = cycle(rig, "bark", "bark2", t - 0.25, 0.4)
		else
			local dance = cycle(rig, "bark", "bark2", t - 0.25, 0.4)
			pose = bridge(rig, "bark", dance, "stand", nil, smooth((t - (tl.Victory - 0.4)) / 0.4))
		end
	elseif state == "Defeat" then
		if t < 0.15 then
			-- последний удар игрока и есть это падение: его наложение (началось вместе с поражением) не повторять
			local last = input
			if input.hitT and input.hitT <= t + 0.05 then
				last = table.clone(input)
				last.hitT = nil
			end
			pose = bridge(rig, "combat", fighting(rig, last), "hit", nil, smooth(t / 0.15))
		elseif t < 0.75 then
			pose = ramp(rig, "hit", "dizzy", t - 0.15, 0.6)
		elseif t < tl.Defeat - 0.6 then
			pose = dizzy(rig, t)
		else
			pose = bridge(rig, "dizzy", dizzy(rig, t), "stand", nil, smooth((t - (tl.Defeat - 0.6)) / 0.6))
		end
	elseif state == "Return" then
		pose = returning(rig, input)
	elseif state == "FallAsleep" then
		if t < tl.FallAsleep * 0.55 then
			-- от позы, в которой пришёл (шаг ещё гаснет, если только что остановился), к позе «проснулся»
			pose = bridge(rig, "stand", returning(rig, input), "alert", nil, smooth(t / (tl.FallAsleep * 0.55)))
		else
			pose = ramp(rig, "alert", "sleep", t - tl.FallAsleep * 0.55, tl.FallAsleep * 0.45)
		end
	else
		pose = BossAnim.Pose(rig, "stand")
	end
	return pose
end

return BossAnim

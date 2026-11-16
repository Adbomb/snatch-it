-- Проигрыватель клипов боссов (D18): у скелета с клипами (rig.Clips — босс 4 «Сфинкс-лежебока») BossAnim.Sample отдаёт
-- позу отсюда — кадры анимаций из Blender (Config/Boss4SphinxClips), а не две позы на состояние, как у боссов 1–3.
-- Всё считается из атрибутов модели и серверного времени, поэтому все клиенты видят одну и ту же фазу, а повторно
-- пришедшее то же состояние ничего не перезапускает.
--   Sleep — цикл сна; Wake, StandUp, ToCombat — один клип пробуждения по Battle.Timeline (1.0 + 0.9 + 0.5 с);
--   Combat — цикл стойки, шаг при беге, выпады и реакция на удар; Victory, Defeat, FallAsleep — свои клипы;
--   Return — шаг домой поверх стойки. Смена состояния: прошлое движение продолжается и гаснет за BLEND.
-- Выпад: клиент начинает замах заранее по плану атаки (атрибуты PlanKind/PlanAt/PlanSeq/PlanCancelAt, пишет сервер),
-- выпад, начатый по плану, идёт от времени плана (AttackPlanAt); без плана — сокращённый замах догоняет попадание.
-- Урон считает только сервер (BattleService, через HitDelay после выпада) — клип только показывает.
-- Свои таблицы скелета (босс 10 «Король-дракон»): rig.AttackClips — вид выпада → клип (иначе общая таблица Сфинкса),
-- rig.HeadParts — что вздрагивает при ударе поверх выпада, rig.Turn — шаг на месте, пока модель поворачивается
-- (input.turnDir, turnT, turnWeight считает BossAnimController); у скелета без них всё как раньше.
-- Зависит от Config/Battle.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Battle = require(ReplicatedStorage.Shared.Config.Battle)

export type Clip = {
	name: string,
	duration: number,
	loop: boolean,
	fps: number,
	count: number,
	events: { [string]: number },
	frames: { { [string]: CFrame } },
	lead: number, -- от начала клипа до начала выпада в игре (AttackAt), секунд; у не-выпадов 0
	eyes: { number }?, -- канал глаз (rig.Eyes): время, значение, … — 0 закрыты, 1 открыты; нет — открыты весь клип
}

type Pose = { [string]: CFrame }

local LEAD_EVENT = "начало выпада в игре (AttackAt)"
-- Вид выпада на сервере (BattleService) → клип: каждый третий — «Хвост-кистень», остальные — «Тяжёлая лапа».
local ATTACK_CLIP = { bite = "heavy_paw", swipe = "tail_strike" }
local BLEND = 0.25 -- стык состояний: прошлое движение гаснет, новое набирает силу, секунд
local ATTACK_IN = 0.12 -- выпад входит из стойки или шага
local ATTACK_OUT = 0.15 -- и выходит обратно (клипы кончаются позой combat, стойка качается рядом)
local CATCH_UP = 0.15 -- выпад без плана: замах короче на столько и догоняет время попадания
local PLAN_MATCH = 0.2 -- выпад позже плана больше чем на столько — считается начатым без плана
local CANCEL_FADE = 0.3 -- отменённый замах гаснет за столько
local IDLE_FADE = 0.45 -- раскачка стойки гаснет перед выпадом и набирается после него: между выпадами — поза combat
local HIT_IN, HIT_OUT = 0.06, 0.12
local HIT_ON_TOP = 0.8 -- сила реакции на удар поверх выпада или шага (только голова, морда, уши, платок)
local HEAD_PARTS = { "Head", "Jaw", "EyelidL", "EyelidR", "BrowL", "BrowR", "EarL", "EarR", "NemesL", "NemesR" }

-- Клип выпада вида kind у скелета rig (nil — такого выпада у скелета нет).
local function attackClipName(rig: any, kind: string?): string?
	if not kind then
		return nil
	end
	local map = rig.AttackClips or ATTACK_CLIP
	return map[kind]
end

local BossClips = {}

local decoded: { [any]: { [string]: Clip } } = {}
local poses: { [any]: { [string]: Pose } } = {}
local IDENTITY = CFrame.new()

local function smooth(x: number): number
	x = math.clamp(x, 0, 1)
	return x * x * (3 - 2 * x)
end

-- Клип name скелета rig (данные разбираются в CFrame один раз).
function BossClips.Get(rig: any, name: string): Clip
	local byRig = decoded[rig]
	if not byRig then
		byRig = {}
		decoded[rig] = byRig
	end
	local clip = byRig[name]
	if clip then
		return clip
	end
	local data = rig.Clips.Load(name)
	assert(data and data.data, "Нет клипа " .. name)
	local moved = {}
	for _, part in data.moved do
		moved[part] = true
	end
	local d = data.data
	local frames = table.create(data.frames)
	local k = 1
	for f = 1, data.frames do
		local frame = {}
		for _, part in rig.Order do
			local qx, qy, qz, qw = d[k], d[k + 1], d[k + 2], d[k + 3]
			k += 4
			local n = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw)
			local x, y, z = 0, 0, 0
			if moved[part] then
				x, y, z = d[k], d[k + 1], d[k + 2]
				k += 3
			end
			frame[part] = CFrame.new(x, y, z, qx / n, qy / n, qz / n, qw / n)
		end
		frames[f] = frame
	end
	assert(k == #d + 1, "Клип " .. name .. ": данные не совпадают со скелетом")
	data.data = nil -- числа разобраны в CFrame: держать их ещё и массивом — вдвое больше памяти
	clip = {
		name = name,
		duration = data.duration,
		loop = data.loop,
		fps = data.fps,
		count = data.frames,
		events = data.events,
		frames = frames,
		lead = data.events[LEAD_EVENT] or 0,
		eyes = data.eyes,
	}
	byRig[name] = clip
	return clip
end

-- Ключевая поза скелета (формат Config/Boss<N>…Rig: {x, y, z, r00…r22}).
local function keyPose(rig: any, name: string): Pose
	local byRig = poses[rig]
	if not byRig then
		byRig = {}
		poses[rig] = byRig
	end
	local pose = byRig[name]
	if not pose then
		pose = {}
		for part, n in rig.Poses[name] do
			pose[part] = CFrame.new(n[1], n[2], n[3], n[4], n[5], n[6], n[7], n[8], n[9], n[10], n[11], n[12])
		end
		byRig[name] = pose
	end
	return pose
end

-- Поза клипа в момент t (циклы — по кругу, остальные — от первого до последнего кадра), между кадрами — Lerp.
function BossClips.At(rig: any, clip: Clip, t: number): Pose
	local n = clip.count
	local a, b, alpha
	if clip.loop then
		local f = (t % clip.duration) * clip.fps
		local i = math.floor(f)
		alpha = f - i
		a, b = clip.frames[i % n + 1], clip.frames[(i + 1) % n + 1]
	else
		local f = math.clamp(t, 0, clip.duration) * clip.fps
		local i = math.min(math.floor(f), n - 1)
		alpha = if i >= n - 1 then 0 else f - i
		a, b = clip.frames[i + 1], clip.frames[math.min(i + 2, n)]
	end
	local out = {}
	for _, part in rig.Order do
		out[part] = a[part]:Lerp(b[part], alpha)
	end
	return out
end

local function play(rig: any, name: string, t: number): Pose
	return BossClips.At(rig, BossClips.Get(rig, name), t)
end

local function blend(rig: any, a: Pose, b: Pose, alpha: number): Pose
	if alpha <= 0 then
		return a
	elseif alpha >= 1 then
		return b
	end
	local out = {}
	for _, part in rig.Order do
		out[part] = a[part]:Lerp(b[part], alpha)
	end
	return out
end

-- Доля шага: 1 — идёт, 0 — стоит; после смены Moving — плавно за полцикла шага.
local function walkWeight(rig: any, input: any): number
	local t = input.movingT
	if t == nil then
		return if input.moving then 1 else 0
	end
	local w = smooth(t / (BossClips.Get(rig, "walk").duration / 2))
	return if input.moving then w else 1 - w
end

-- Последний начатый выпад: клип и время в нём (по плану — от времени плана; без плана — сокращённый замах догоняет
-- попадание) и сила входа; nil — выпадов не было.
local function lastAttack(rig: any, input: any): (Clip?, number, number)
	local kind, at = input.attackKind, input.attackT
	-- время сервера у клиента оценивается с погрешностью: выпад «из будущего» на доли секунды — уже начался
	if not kind or not at or at < -PLAN_MATCH then
		return nil, 0, 0
	end
	at = math.max(at, 0)
	local clip =
		BossClips.Get(rig, attackClipName(rig, kind) or (if rig.AttackClips then "claw_swipe" else "heavy_paw"))
	local lead = clip.lead
	local planT = input.attackPlanT
	if planT and planT - at <= PLAN_MATCH and planT - at >= -lead then
		local tau = lead + planT
		return clip, tau, smooth(tau / ATTACK_IN)
	end
	local hitDelay = Battle.HitDelay
	local tau = if at < hitDelay then lead - CATCH_UP + at * (1 + CATCH_UP / hitDelay) else lead + at
	-- rig.CatchUpIn (дракон, этап C.2): выпад без плана входит в силу до самого попадания, а не за ATTACK_IN —
	-- лапа не «выстреливает» из стойки в середину замаха; к попаданию поза та же (вес 1)
	return clip, tau, smooth(at / (rig.CatchUpIn or ATTACK_IN))
end

-- Следующий выпад по плану: клип, время в нём (минус — замах ещё впереди), сила и насколько он близко (1 — идёт
-- или вот-вот, 0 — далеко или отменён и погас); nil — плана нет.
local function nextAttack(rig: any, input: any): (Clip?, number, number, number)
	local pk, pt = input.planKind, input.planT
	if not pk or not pt or not attackClipName(rig, pk) then
		return nil, 0, 0, 0
	end
	if input.planSeq ~= nil and input.planSeq ~= (input.attackSeq or 0) + 1 then
		return nil, 0, 0, 0 -- этот план уже сыгран
	end
	local clip = BossClips.Get(rig, attackClipName(rig, pk) :: string)
	local tau = clip.lead + pt
	-- отменён (игрок ушёл из дальности, бой кончился) или выпад так и не пришёл: замах замирает и гаснет
	local cancelT = input.planCancelT
	if not cancelT and tau > clip.lead + PLAN_MATCH then
		cancelT = tau - (clip.lead + PLAN_MATCH)
	end
	if cancelT and cancelT >= 0 then
		local frozen = tau - cancelT
		if frozen < 0 then
			return nil, 0, 0, 0 -- отменили до начала замаха
		end
		local fade = 1 - smooth(cancelT / CANCEL_FADE)
		return clip, frozen, smooth(frozen / ATTACK_IN) * fade, fade
	end
	if tau < 0 then
		return clip, tau, 0, 1 - smooth(-tau / IDLE_FADE)
	end
	return clip, tau, smooth(tau / ATTACK_IN), 1
end

-- Выпад, который сейчас виден: клип, время в нём и сила (0 — нет выпада).
function BossClips.Attack(rig: any, input: any): (Clip?, number, number)
	local clip, tau, weight = nextAttack(rig, input)
	if clip and tau >= 0 and weight > 0 then
		return clip, tau, weight
	end
	clip, tau, weight = lastAttack(rig, input)
	if clip and tau < clip.duration then
		return clip, tau, weight * smooth((clip.duration - tau) / ATTACK_OUT)
	end
	return nil, 0, 0
end

-- Насколько далеко выпады (1 — давно не было и не скоро будет, 0 — идёт или рядом): сила раскачки стойки. Клипы
-- выпадов начинаются и кончаются позой combat — между ними стойка не раскачивается, хвост и голова не дёргаются.
function BossClips.Calm(rig: any, input: any): number
	local near = 0
	local clip, tau = lastAttack(rig, input)
	if clip then
		near = if tau < clip.duration then 1 else 1 - smooth((tau - clip.duration) / IDLE_FADE)
	end
	local _, _, _, soon = nextAttack(rig, input)
	return 1 - math.max(near, soon)
end

-- Поверх позы base — отклонение layer от ref у частей parts с силой w.
local function additive(base: Pose, ref: Pose, layer: Pose, w: number, parts: { string }): Pose
	local out = table.clone(base)
	for _, part in parts do
		out[part] = base[part] * IDENTITY:Lerp(ref[part]:Inverse() * layer[part], w)
	end
	return out
end

-- Бой: цикл стойки от начала боя, при беге — шаг, сверху выпады и реакция на удар.
local function fighting(rig: any, input: any): Pose
	local clip, tau, weight = BossClips.Attack(rig, input)
	local w = walkWeight(rig, input)
	local pose
	if clip and weight >= 1 and w <= 0 then
		pose = BossClips.At(rig, clip, tau) -- выпад в полную силу: стойка под ним не видна
	else
		local calm = BossClips.Calm(rig, input)
		local combat = keyPose(rig, "combat")
		if calm <= 0 then
			pose = combat
		elseif calm >= 1 then
			pose = play(rig, "combat_idle", input.t)
		else
			pose = additive(combat, combat, play(rig, "combat_idle", input.t), calm, rig.Order)
		end
		if w > 0 then
			pose = blend(rig, pose, play(rig, "walk", input.clock), w)
		end
		-- поворот модели на месте (rig.Turn): шаги лап по пройденному углу — лапы не скользят
		local tw = input.turnWeight or 0
		if rig.Turn and tw > 0 and input.turnDir then
			local turn = BossClips.Get(rig, if input.turnDir > 0 then rig.Turn.Left else rig.Turn.Right)
			pose = blend(rig, pose, BossClips.At(rig, turn, input.turnT or 0), tw)
		end
		if clip and weight > 0 then
			pose = blend(rig, pose, BossClips.At(rig, clip, tau), weight)
		end
	end
	local ht = input.hitT
	local hit = BossClips.Get(rig, "hit")
	if ht and ht >= 0 and ht < hit.duration then
		local hw = smooth(ht / HIT_IN) * smooth((hit.duration - ht) / HIT_OUT)
		local reaction = BossClips.At(rig, hit, ht)
		local k = math.max(weight, w) -- сила выпада или шага: 0 — стойка, 1 — в полную силу
		if rig.Fade and k > 0 and k < 1 then
			-- дракон (этап C.2): выпад начался посреди реакции — тело выходит из неё по силе выпада, а не за кадр
			local headOnly = additive(pose, hit.frames[1], reaction, hw * HIT_ON_TOP, rig.HeadParts or HEAD_PARTS)
			pose = blend(rig, blend(rig, pose, reaction, hw), headOnly, k)
		elseif k > 0 then
			-- выпад или шаг не ломаются: вздрагивают только голова, морда, уши и платок
			pose = additive(pose, hit.frames[1], reaction, hw * HIT_ON_TOP, rig.HeadParts or HEAD_PARTS)
		else
			pose = blend(rig, pose, reaction, hw)
		end
	end
	return pose
end

-- Домой: шаг поверх стойки (победа и поражение кончаются позой stand).
local function returning(rig: any, input: any): Pose
	local w = walkWeight(rig, input)
	local stand = keyPose(rig, "stand")
	if w <= 0 then
		return stand
	end
	return blend(rig, stand, play(rig, "walk", input.clock), w)
end

-- Поза состояния без стыка с прошлым.
local function current(rig: any, input: any): Pose
	local tl = Battle.Timeline
	local state, t = input.state, input.t
	if state == "Sleep" then
		return play(rig, "sleep_idle", t)
	elseif state == "Wake" then
		return play(rig, "wake", t)
	elseif state == "StandUp" then
		return play(rig, "wake", tl.Wake + t)
	elseif state == "ToCombat" then
		return play(rig, "wake", tl.Wake + tl.StandUp + t)
	elseif state == "Combat" then
		return fighting(rig, input)
	elseif state == "Victory" then
		return play(rig, "victory", t)
	elseif state == "Defeat" then
		return play(rig, "defeat", t)
	elseif state == "Return" then
		return returning(rig, input)
	elseif state == "FallAsleep" then
		return play(rig, "fall_asleep", t)
	end
	return keyPose(rig, "stand")
end

-- Transform каждого сустава (формат BossAnim.Sample). Первые BLEND секунд нового состояния прошлое продолжается и
-- гаснет: выпад, начатый перед концом боя, доигрывает в победу или поражение без скачка; разбудили, пока засыпал, —
-- засыпание переходит в пробуждение дольше (за Timeline.Wake).
function BossClips.Sample(rig: any, input: any): Pose
	local pose = current(rig, input)
	local from, t = input.fromState, input.t
	if not from or from == input.state then
		return pose
	end
	local span = BLEND
	if from == "FallAsleep" and input.state == "Wake" then
		span = Battle.Timeline.Wake
	end
	if t >= span then
		return pose
	end
	local prev = table.clone(input)
	prev.state = from
	prev.t = (input.fromT or 0) + t
	prev.fromState = nil
	return blend(rig, current(rig, prev), pose, smooth(t / span))
end

-- Канал глаз клипа в момент t (как поза: циклы — по кругу, остальные — от первого до последнего кадра).
local function eyesAt(clip: Clip, t: number): number
	local keys = clip.eyes
	if not keys then
		return 1
	end
	t = if clip.loop then t % clip.duration else math.clamp(t, 0, clip.duration)
	if t <= keys[1] then
		return keys[2]
	end
	for i = 3, #keys, 2 do
		if t <= keys[i] then
			local t0, t1 = keys[i - 2], keys[i]
			local k = if t1 > t0 then (t - t0) / (t1 - t0) else 1
			return keys[i - 1] + (keys[i + 1] - keys[i - 1]) * k
		end
	end
	return keys[#keys]
end

local function eyesNow(rig: any, input: any): number
	local tl = Battle.Timeline
	local state, t = input.state, input.t
	local function at(name: string, time: number): number
		return eyesAt(BossClips.Get(rig, name), time)
	end
	if state == "Sleep" then
		return at("sleep_idle", t)
	elseif state == "Wake" then
		return at("wake", t)
	elseif state == "StandUp" then
		return at("wake", tl.Wake + t)
	elseif state == "ToCombat" then
		return at("wake", tl.Wake + tl.StandUp + t)
	elseif state == "Combat" then
		-- как fighting(): моргание стойки гаснет рядом с выпадом (раскачка Calm), во время выпада — его клип
		local clip, tau, weight = BossClips.Attack(rig, input)
		local v = 1 + (at("combat_idle", t) - 1) * BossClips.Calm(rig, input)
		if clip and weight > 0 then
			v += (eyesAt(clip, tau) - v) * weight
		end
		local ht = input.hitT
		local hit = BossClips.Get(rig, "hit")
		if ht and ht >= 0 and ht < hit.duration then
			v = math.min(v, eyesAt(hit, ht)) -- прищур от удара — и поверх выпада
		end
		return v
	elseif state == "Victory" then
		return at("victory", t)
	elseif state == "Defeat" then
		return at("defeat", t)
	elseif state == "FallAsleep" then
		return at("fall_asleep", t)
	end
	return 1
end

-- Глаза (rig.Eyes): 0 — закрыты, 1 — открыты; стык состояний — как у позы (BossClips.Sample).
function BossClips.Eyes(rig: any, input: any): number
	local v = eyesNow(rig, input)
	local from, t = input.fromState, input.t
	if not from or from == input.state then
		return v
	end
	local span = BLEND
	if from == "FallAsleep" and input.state == "Wake" then
		span = Battle.Timeline.Wake
	end
	if t >= span then
		return v
	end
	local prev = table.clone(input)
	prev.state = from
	prev.t = (input.fromT or 0) + t
	prev.fromState = nil
	local p = eyesNow(rig, prev)
	return p + (v - p) * smooth(t / span)
end

BossClips.AttackClip = ATTACK_CLIP
BossClips.LeadEvent = LEAD_EVENT

return BossClips

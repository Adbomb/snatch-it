--!nocheck
-- Переходы анимаций Короля-дракона (этап C.2) без Studio: настоящие Shared/BossAnim, Shared/BossClips,
-- Shared/PoseFade, Config/Boss10DragonRig, Config/Battle. Сценарии — как их пишет сервер (BattleService.step):
--   1) выпад без плана: игрок вошёл в дальность, когда перезарядка уже прошла, — сервер бьёт сразу (AttackPlanAt нет);
--   2) замах лапы → залп в том же шаге сервера: keepPlan отменяет план, Plan("volley") сразу стирает PlanCancelAt;
--   3) замах отменён без залпа (игрок отошёл) — гаснет за CANCEL_FADE (для сравнения);
--   4) быстрые переходы подряд: выпад за выпадом, удар по дракону, залп, поражение посреди залпа;
--   5) плановый выпад не задерживается: поза в момент попадания — та же, что без сглаживания.
-- Мерило — наибольший поворот сустава за кадр (30 и 15 к/с) и левого плеча отдельно; кадр как у клиента:
-- BossAnim.Sample → PoseFade (ключ источника — BossAnimController). Время попадания (HitDelay) не меняется.
-- Ничего не пишет. Запуск из корня репозитория: lune run scripts/lune/check_boss10_transitions.luau

local process = require("@lune/process")

local Env = require("./env")

local BossAnim = Env.Require("ReplicatedStorage.Shared.BossAnim")
local PoseFade = Env.Require("ReplicatedStorage.Shared.PoseFade")
local Battle = Env.Require("ReplicatedStorage.Shared.Config.Battle")
local rig = Env.Require("ReplicatedStorage.Shared.Config.Boss10DragonRig")

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

local SKIP = { Scepter = true, ScepterShards = true } -- скипетр симметричен, крутится сам
local function angle(a, b): number
	local _, ang = (a:Inverse() * b):ToAxisAngle()
	local d = math.deg(math.abs(ang)) % 360
	return if d > 180 then 360 - d else d
end

-- Прогон: events(t) → поля входа поверх базовых; возвращает наибольший поворот за кадр (все / левое плечо) и позы.
local function run(events: (number) -> any, from: number, to: number, fps: number, useFade: boolean)
	local fade = PoseFade.new(rig)
	local prev
	local worst, worstPart, worstT, arm = 0, "", 0, 0
	local poses = {}
	local count = math.floor((to - from) * fps + 0.5)
	for i = 0, count do
		local t = from + i / fps
		local input = events(t)
		input.clock = t
		local pose = BossAnim.Sample(rig, input)
		if useFade then
			pose = fade:Apply(PoseFade.Key(input), pose, t)
		end
		if prev then
			for _, part in rig.Order do
				if not SKIP[part] then
					local d = angle(prev[part], pose[part])
					if d > worst then
						worst, worstPart, worstT = d, part, t
					end
					if part == "UpperArmL" then
						arm = math.max(arm, d)
					end
				end
			end
		end
		poses[i] = pose
		prev = pose
	end
	return worst, worstPart, worstT, arm, poses
end

local HIT = Battle.HitDelay

-- 1) выпад без плана в момент 5.0
local function unplanned(t)
	local input = { state = "Combat", t = t, moving = false, attackSeq = 0 }
	if t >= 5 then
		input.attackKind, input.attackT, input.attackSeq = "claw", t - 5, 1
	end
	return input
end

-- 2) план лапы (выпад в 6.0, замах с 5.45), в 5.7 — отмена и план залпа в том же шаге (PlanCancelAt стёрт)
local function planSwitch(t)
	local input = { state = "Combat", t = t, moving = false, attackSeq = 0 }
	if t >= 4.6 and t < 5.7 then
		input.planKind, input.planSeq, input.planT = "claw", 1, t - 6
	elseif t >= 5.7 then
		input.planKind, input.planSeq, input.planT = "volley", 1, t - 6.2 -- залп через Announce 0.5
	end
	if t >= 6.2 then
		input.attackKind, input.attackT, input.attackSeq, input.attackPlanT = "volley", t - 6.2, 1, t - 6.2
	end
	return input
end

-- 2б) как в игре (Play): план залпа, через шаг сервера его же PlanCancelAt (keepPlan: боец вне ближней дальности),
-- залп по своему таймеру через Announce (0.5 с)
local function planSwitchCancel(t)
	local input = planSwitch(t)
	if t >= 5.83 and t < 6.2 then
		input.planCancelT = t - 5.83
	end
	return input
end

-- 3) тот же замах, но отмена видна (игрок отошёл, залпа нет)
local function planCancel(t)
	local input = { state = "Combat", t = t, moving = false, attackSeq = 0 }
	if t >= 4.6 then
		input.planKind, input.planSeq, input.planT = "claw", 1, t - 6
		if t >= 5.7 then
			input.planCancelT = t - 5.7
		end
	end
	return input
end

-- 4) подряд: укус по плану, лапа без плана сразу за ним, удары по дракону, залп по плану, поражение посреди залпа
local function rapid(t)
	local input = { state = "Combat", t = t, moving = false, attackSeq = 0 }
	local hits = { 4.2, 4.9, 5.6, 6.3 }
	for _, h in hits do
		if t >= h then
			input.hitT = t - h
		end
	end
	if t >= 3.4 and t < 4 then
		input.planKind, input.planSeq, input.planT = "bite", 1, t - 4
	end
	if t >= 4 then
		input.attackKind, input.attackT, input.attackSeq, input.attackPlanT = "bite", t - 4, 1, t - 4
	end
	if t >= 4.6 then -- лапа без плана через 0.6 с (вошёл в дальность после отмены)
		input.attackKind, input.attackT, input.attackSeq, input.attackPlanT = "claw", t - 4.6, 2, nil
	end
	if t >= 5.2 and t < 6.5 then
		input.planKind, input.planSeq, input.planT = "volley", 3, t - 6.5
	end
	if t >= 6.5 then
		input.attackKind, input.attackT, input.attackSeq, input.attackPlanT = "volley", t - 6.5, 3, t - 6.5
	end
	if t >= 7.6 then
		input.state, input.t, input.fromState, input.fromT = "Defeat", t - 7.6, "Combat", 7.6
	end
	return input
end

-- 5) плановый выпад: замах по плану, выпад в 6.0
local function planned(t)
	local input = { state = "Combat", t = t, moving = false, attackSeq = 0 }
	if t >= 4.6 and t < 6 then
		input.planKind, input.planSeq, input.planT = "claw", 1, t - 6
	end
	if t >= 6 then
		input.attackKind, input.attackT, input.attackSeq, input.attackPlanT = "claw", t - 6, 1, t - 6
	end
	return input
end

-- наибольший поворот за 1/30 с у самих клипов выпада (для сравнения)
local clipMax = 0
do
	local w = run(function(t)
		return {
			state = "Combat",
			t = 9,
			moving = false,
			attackSeq = 1,
			attackKind = "claw",
			attackT = t,
			attackPlanT = t,
		}
	end, 0, 0.8, 30, false)
	clipMax = w
end
print(
	("Клип «Удар лапой» по плану: наибольший поворот сустава за 1/30 с — %.1f°"):format(
		clipMax
	)
)

local LIMIT30, LIMIT15 = 24, 40 -- °/кадр: не больше, чем быстрые места самих клипов (лапа ≈ 17–22° за 1/30 с)

for _, case in
	{
		{ "1. выпад без плана", unplanned, 4.5, 6.5 },
		{ "2. замах лапы → залп в том же шаге", planSwitch, 4.5, 7.5 },
		{ "2б. то же и отмена плана залпа через шаг", planSwitchCancel, 4.5, 7.5 },
		{ "3. замах отменён, залпа нет", planCancel, 4.5, 6.5 },
		{ "4. быстрые переходы подряд", rapid, 3, 9.5 },
	}
do
	local name, fn, a, b = case[1], case[2], case[3], case[4]
	print(name)
	local w0, p0, t0, arm0 = run(fn, a, b, 30, false)
	local w1, p1, t1, arm1 = run(fn, a, b, 30, true)
	local w2, _, _, arm2 = run(fn, a, b, 15, true)
	print(
		("     без сглаживания: %.1f° за 1/30 с (%s, %.2f с), левое плечо %.1f°"):format(
			w0,
			p0,
			t0,
			arm0
		)
	)
	print(
		("     со сглаживанием: %.1f° (%s, %.2f с), левое плечо %.1f°; при 15 к/с — %.1f°, плечо %.1f°"):format(
			w1,
			p1,
			t1,
			arm1,
			w2,
			arm2
		)
	)
	check(w1 <= LIMIT30, ("%s: поворот за 1/30 с ≤ %d° (%.1f°)"):format(name, LIMIT30, w1))
	check(w2 <= LIMIT15, ("%s: поворот за 1/15 с ≤ %d° (%.1f°)"):format(name, LIMIT15, w2))
end

print("5. Плановый выпад и попадание")
do
	local _, _, _, _, raw = run(planned, 4.5, 7, 30, false)
	local _, _, _, _, faded = run(planned, 4.5, 7, 30, true)
	local key = math.floor((6 + HIT - 4.5) * 30 + 0.5)
	local a, b = raw[key], faded[key]
	local d = 0
	if a and b then
		for _, part in rig.Order do
			if not SKIP[part] then
				d = math.max(d, angle(a[part], b[part]))
			end
		end
	end
	check(
		a ~= nil and d < 0.5,
		("плановый выпад: поза в момент попадания (+%.2f с) та же (расхождение %.2f°)"):format(
			HIT,
			d
		)
	)
	-- выпад без плана: к попаданию поза — клип в момент попадания (вес 1)
	local _, _, _, _, u = run(unplanned, 4.5, 6, 30, true)
	local _, _, _, _, ref = run(function(t)
		return {
			state = "Combat",
			t = t,
			moving = false,
			attackSeq = 1,
			attackKind = "claw",
			attackT = t - 5,
			attackPlanT = t - 5,
		}
	end, 4.5, 6, 30, false)
	local k2 = math.floor((5 + HIT - 4.5) * 30 + 0.5)
	local d2 = 0
	for _, part in rig.Order do
		if not SKIP[part] and u[k2] and ref[k2] then
			d2 = math.max(d2, angle(u[k2][part], ref[k2][part]))
		end
	end
	check(
		d2 < 6,
		("выпад без плана: в момент попадания поза — удар лапы (расхождение %.1f°)"):format(
			d2
		)
	)
end

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
process.exit(if failed > 0 then 1 else 0)

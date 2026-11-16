--!nocheck
-- Проверка проигрывателя клипов на босс 10 «Король-дракон» без Studio (этап B): настоящие Shared/BossAnim,
-- Shared/BossClips, Config/Boss10DragonRig, Config/Battle.
--   1) выпады дракона → его клипы (rig.AttackClips), у Сфинкса — прежняя таблица (bite → «Тяжёлая лапа»,
--      swipe → «Хвост-кистень»): общий модуль обратно совместим;
--   2) все состояния подряд как в бою: сон → пробуждение → стойка с выпадами всех видов, ударами по дракону, поворотом
--      на месте (шаги лап по пройденному углу) и залпом → победа → домой → засыпание; и поражение посреди выпада —
--      без скачков суставов (наибольший поворот за кадр — не больше, чем в самих клипах);
--   3) шаг на месте: сила набирается и гаснет, пока модель поворачивается, кадры шага идут по углу;
--   4) цена кадра.
-- Ничего не пишет. Запуск из корня репозитория: lune run scripts/lune/check_boss10_player.luau

local process = require("@lune/process")

local Env = require("./env")

local BossAnim = Env.Require("ReplicatedStorage.Shared.BossAnim")
local BossClips = Env.Require("ReplicatedStorage.Shared.BossClips")
local Battle = Env.Require("ReplicatedStorage.Shared.Config.Battle")
local rig = Env.Require("ReplicatedStorage.Shared.Config.Boss10DragonRig")
local sphinx = Env.Require("ReplicatedStorage.Shared.Config.Boss4SphinxRig")
local tl = Battle.Timeline

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

local SYMMETRY = { Scepter = 90, ScepterShards = 120 }
local function angle(part, a, b): number
	local _, ang = (a:Inverse() * b):ToAxisAngle()
	local d = math.deg(math.abs(ang)) % 360
	d = if d > 180 then 360 - d else d
	local sym = SYMMETRY[part]
	if sym then
		local m = d % sym
		d = math.min(m, sym - m)
	end
	return d
end

-- ── 1. Выпады → клипы ──────────────────────────────────────────────────────────────────────────────────────
print("1. Выпады → клипы")
local function attackClip(r, kind)
	local clip = BossClips.Attack(r, { attackKind = kind, attackT = 0.3, clock = 0, state = "Combat", t = 5 })
	return clip and clip.name
end
for kind, want in { claw = "claw_swipe", bite = "bite", tail = "tail_strike", wings = "wing_buffet", volley = "magic_volley" } do
	check(attackClip(rig, kind) == want, ("дракон: %s → %s"):format(kind, tostring(attackClip(rig, kind))))
end
check(attackClip(sphinx, "bite") == "heavy_paw", "Сфинкс: bite → heavy_paw (как раньше)")
check(attackClip(sphinx, "swipe") == "tail_strike", "Сфинкс: swipe → tail_strike (как раньше)")
check(sphinx.AttackClips == nil and sphinx.Turn == nil, "у Сфинкса нет своих таблиц — путь прежний")

-- ── 2. Бой целиком ─────────────────────────────────────────────────────────────────────────────────────────
print("2. Все состояния подряд")
-- расписание сервера: состояния (время начала), выпады, удары по дракону, поворот модели
local states = {
	{ "Sleep", 0 },
	{ "Wake", 2 },
	{ "StandUp", 2 + tl.Wake },
	{ "ToCombat", 2 + tl.Wake + tl.StandUp },
	{ "Combat", 2 + tl.Wake + tl.StandUp + tl.ToCombat },
}
local combatAt = states[5][2]
local attacks = {
	{ "claw", combatAt + 0.6 },
	{ "bite", combatAt + 2.0 },
	{ "tail", combatAt + 3.4 },
	{ "wings", combatAt + 4.8 },
	{ "volley", combatAt + 6.4 },
	{ "claw", combatAt + 9.6 },
}
local hits = { combatAt + 0.9, combatAt + 1.8, combatAt + 2.7, combatAt + 9.0 }
local turnFrom, turnTo = combatAt + 1.0, combatAt + 3.0 -- модель поворачивается на 50°/с
local endAt = combatAt + 10.4
table.insert(states, { "Victory", endAt })
table.insert(states, { "Return", endAt + tl.Victory })
table.insert(states, { "FallAsleep", endAt + tl.Victory + 1.5 })
table.insert(states, { "Sleep", endAt + tl.Victory + 1.5 + tl.FallAsleep })
local stopAt = endAt + tl.Victory + 1.5 + tl.FallAsleep + 2

local turnCfg = rig.Turn
local turnClip = BossClips.Get(rig, turnCfg.Left)
local acc, weight = 0, 0
local function sampleAt(now: number, dt: number)
	local si = 1
	for i, s in states do
		if now >= s[2] then
			si = i
		end
	end
	local state, at = states[si][1], states[si][2]
	local from = if si > 1 then states[si - 1] else nil
	local kind, attackAt, seq = nil, nil, 0
	for i, a in attacks do
		if now >= a[2] and state == "Combat" then
			kind, attackAt, seq = a[1], a[2], i
		end
	end
	-- план атаки, как у сервера: следующий выпад объявлен за интервал до него (залп — без плана)
	local planKind, planAt, planSeq, attackPlanAt = nil, nil, nil, nil
	for i, a in attacks do
		-- выпад объявлен за интервал атаки, залп — за Volley.Announce (как у BattleService)
		local lead = if a[1] == "volley" then Battle.Bosses[10].Volley.Announce else Battle.Bosses[10].AttackInterval
		if state == "Combat" and now >= a[2] - lead and now < a[2] then
			planKind, planAt, planSeq = a[1], a[2], i
		end
		if attackAt == a[2] then
			attackPlanAt = a[2]
		end
	end
	local hitAt = nil
	for _, h in hits do
		if now >= h then
			hitAt = h
		end
	end
	local turning = state == "Combat" and now >= turnFrom and now < turnTo
	if turning then
		acc += turnCfg.Rate * dt
	end
	weight = math.clamp(weight + (if turning then dt / 0.25 else -dt / 0.25), 0, 1)
	-- домой: идёт с начала Return 1.2 с и останавливается (MovingAt — момент смены, как у BossService)
	local walkFrom, walkTo = endAt + tl.Victory, endAt + tl.Victory + 1.2
	local moving = state == "Return" and now < walkTo
	return BossAnim.Sample(rig, {
		state = state,
		t = now - at,
		moving = moving,
		movingT = if state == "Return" then (if moving then now - walkFrom else now - walkTo) else nil,
		fromState = if from then from[1] else nil,
		fromT = if from then at - from[2] else nil,
		attackKind = kind,
		attackT = if attackAt then now - attackAt else nil,
		hitT = if hitAt then now - hitAt else nil,
		clock = now,
		attackSeq = seq,
		attackPlanT = if attackPlanAt then now - attackPlanAt else nil,
		planKind = planKind,
		planSeq = planSeq,
		planT = if planAt then now - planAt else nil,
		turnDir = 1,
		turnT = (acc % turnCfg.Degrees) / turnCfg.Degrees * turnClip.duration,
		turnWeight = weight * weight * (3 - 2 * weight),
	})
end

local prev = nil
local worst, worstAt, worstPart = 0, 0, ""
local frames, ok = 0, true
local started = os.clock()
local dt = 1 / 30
local t = 0
while t <= stopAt do
	local pose = sampleAt(t, dt)
	frames += 1
	for _, part in rig.Order do
		local cf = pose[part]
		if not cf or cf.Position.X ~= cf.Position.X then
			ok = false
		end
	end
	if prev then
		for _, part in rig.Order do
			if part ~= "ScepterShards" and part ~= "Scepter" then
				local d = angle(part, prev[part], pose[part])
				if d > worst then
					worst, worstAt, worstPart = d, t, part
				end
			end
		end
	end
	prev = pose
	t += dt
end
local cost = (os.clock() - started) / frames * 1000
check(ok, ("%d кадров боя: у каждого из %d суставов есть поза, без NaN"):format(frames, #rig.Order))
check(worst < 36, ("наибольший поворот сустава за кадр %.1f° (%s, %.2f с) — не больше быстрейшего в клипах (35°)"):format(worst, worstPart, worstAt))

-- поражение посреди выпада: победа игрока — Defeat с прошлого «выпад лапой»
local p0 = BossAnim.Sample(rig, { state = "Combat", t = 5, clock = 5, attackKind = "claw", attackT = 0.5, attackSeq = 1, moving = false })
local p1 = BossAnim.Sample(rig, { state = "Defeat", t = 1 / 30, clock = 5 + 1 / 30, fromState = "Combat", fromT = 5, attackKind = "claw", attackT = 0.5 + 1 / 30, moving = false })
local jump = 0
for _, part in rig.Order do
	if part ~= "ScepterShards" and part ~= "Scepter" then
		jump = math.max(jump, angle(part, p0[part], p1[part]))
	end
end
check(jump < 15, ("бой кончился посреди выпада: первый кадр поражения без скачка (%.1f°)"):format(jump))

-- ── 3. Шаг на месте ────────────────────────────────────────────────────────────────────────────────────────
print("3. Шаг на месте")
local still = BossAnim.Sample(rig, { state = "Combat", t = 2, clock = 2, moving = false, turnDir = 1, turnT = 0, turnWeight = 0 })
local stepping = BossAnim.Sample(rig, { state = "Combat", t = 2, clock = 2, moving = false, turnDir = 1, turnT = 0.4, turnWeight = 1 })
local legMoved = 0
for _, part in { "ForearmL", "ForearmR", "ShinL", "ShinR", "MetaL", "MetaR" } do
	legMoved = math.max(legMoved, angle(part, still[part], stepping[part]))
end
check(legMoved > 5, ("при повороте лапы переступают (%.1f°), без поворота — стоят"):format(legMoved))
check(turnClip.duration == 1.8 and turnCfg.Degrees == 90, "цикл шага — 90° поворота за 1.8 с (50°/с)")

-- ── 4. Цена кадра ──────────────────────────────────────────────────────────────────────────────────────────
print("4. Цена кадра")
print(("     BossAnim.Sample на драконе (52 сустава): %.3f мс на кадр в Lune"):format(cost))
check(cost < 2, "кадр дешевле 2 мс")

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end

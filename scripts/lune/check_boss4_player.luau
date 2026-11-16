--!nocheck
-- Проверка проигрывателя клипов босса 4 «Сфинкс-лежебока» без Studio (интеграция 2026-11-12): настоящие модули игры
-- Shared/BossAnim, Shared/BossClips, Config/Boss4SphinxRig, Config/Boss4SphinxClips, Config/Battle.
--   1) скелет и десять клипов: части, позы, кадры совпадают с экспортом Blender (anim.json), стыки клипов с позами;
--   2) все состояния подряд (сон → пробуждение → бой с выпадами, ударами и бегом → победа или поражение → домой →
--      засыпание, разбудили во время засыпания, бой кончился посреди выпада): нет скачков больше быстрейшего движения
--      самих клипов;
--   3) план атаки на модели серверного цикла (шаг 0.1 с с задержкой кадра, интервал 1.4 с): видимый контакт и урон,
--      каждый третий — «Хвост-кистень», отмена плана, выпад без плана, первый замах при задержке сети;
--   4) боссы 1–3 идут прежним путём (у их скелетов нет клипов) — подробно их проверяет check_boss_anim.luau;
--   5) цена кадра и память клипов.
-- Ничего не пишет. Запуск из корня репозитория: lune run scripts/lune/check_boss4_player.luau

local fs = require("@lune/fs")
local process = require("@lune/process")
local serde = require("@lune/serde")

local Env = require("./env")
local CFrame = Env.roblox.CFrame

local BossAnim = Env.Require("ReplicatedStorage.Shared.BossAnim")
local BossClips = Env.Require("ReplicatedStorage.Shared.BossClips")
local Battle = Env.Require("ReplicatedStorage.Shared.Config.Battle")
local rig = Env.Require("ReplicatedStorage.Shared.Config.Boss4SphinxRig")
local others = {
	Env.Require("ReplicatedStorage.Shared.Config.Boss1DogRig"),
	Env.Require("ReplicatedStorage.Shared.Config.Boss2TraderRig"),
	Env.Require("ReplicatedStorage.Shared.Config.Boss3RatKingRig"),
}
local anim = serde.decode("json", fs.readFile("assets/models/Boss4_Sphinx.anim.json"))
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

local function angle(a: CFrame, b: CFrame): number
	local _, ang = (a:Inverse() * b):ToAxisAngle()
	return math.deg(math.abs(ang))
end

local function gap(a, b): (number, number)
	local deg, pos = 0, 0
	for _, part in rig.Order do
		deg = math.max(deg, angle(a[part], b[part]))
		pos = math.max(pos, (a[part].Position - b[part].Position).Magnitude)
	end
	return deg, pos
end

-- ── 1. Скелет и клипы ────────────────────────────────────────────
print("1. Скелет и клипы")
check(#rig.Order == 27, ("частей %d"):format(#rig.Order))
local poseCount = 0
for _ in rig.Poses do
	poseCount += 1
end
check(poseCount == 13, ("поз %d"):format(poseCount))
check(#rig.Clips.Names == 10, ("клипов %d"):format(#rig.Clips.Names))
for _, other in others do
	check(
		other.Clips == nil,
		"у скелета боссов 1–3 клипов нет — BossAnim идёт прежним путём"
	)
end
local before = collectgarbage("count")
local worstDeg, worstPos = 0, 0
for _, name in rig.Clips.Names do
	local clip = BossClips.Get(rig, name)
	local src = anim.clips[name]
	local step = math.floor(30 / clip.fps + 0.5)
	local ok = true
	for i, frame in clip.frames do
		local row = src.frames[(i - 1) * step + 1]
		for j, part in rig.Order do
			local v = row[j]
			local ref = CFrame.new(v[1], v[2], v[3], v[4], v[5], v[6], v[7])
			local d, p = angle(frame[part], ref), (frame[part].Position - ref.Position).Magnitude
			worstDeg, worstPos = math.max(worstDeg, d), math.max(worstPos, p)
			ok = ok and d < 0.05 and p < 0.002
		end
	end
	check(
		ok,
		("%s: %d кадров (%d/с), %.2f с, совпадает с экспортом"):format(
			name,
			clip.count,
			clip.fps,
			clip.duration
		)
	)
end
print(
	("     наибольшее расхождение с экспортом: %.4f° и %.5f ст."):format(
		worstDeg,
		worstPos
	)
)
local memory = collectgarbage("count") - before
local function pose(name)
	local out = {}
	for part, n in rig.Poses[name] do
		out[part] = CFrame.new(n[1], n[2], n[3], n[4], n[5], n[6], n[7], n[8], n[9], n[10], n[11], n[12])
	end
	return out
end
local function first(name)
	return BossClips.Get(rig, name).frames[1]
end
local function last(name)
	local clip = BossClips.Get(rig, name)
	return clip.frames[clip.count]
end
for _, spec in
	{
		{ "wake", "начало", first, "sleep" },
		{ "wake", "конец", last, "combat" },
		{ "heavy_paw", "начало", first, "combat" },
		{ "heavy_paw", "конец", last, "combat" },
		{ "tail_strike", "начало", first, "combat" },
		{ "tail_strike", "конец", last, "combat" },
		{ "hit", "начало", first, "combat" },
		{ "victory", "конец", last, "stand" },
		{ "defeat", "конец", last, "stand" },
		{ "fall_asleep", "начало", first, "stand" },
		{ "fall_asleep", "конец", last, "sleep" },
		{ "sleep_idle", "начало", first, "sleep" },
		{ "combat_idle", "начало", first, "combat" },
	}
do
	local d, p = gap(spec[3](spec[1]), pose(spec[4]))
	check(d < 0.5 and p < 0.01, ("%s, %s — поза %s (%.2f°, %.3f ст.)"):format(spec[1], spec[2], spec[4], d, p))
end
local heavy, tail = BossClips.Get(rig, "heavy_paw"), BossClips.Get(rig, "tail_strike")
check(
	math.abs(heavy.events["контакт: удар лапы"] - heavy.lead - Battle.HitDelay) < 1e-6,
	"«Тяжёлая лапа»: контакт через HitDelay после начала выпада"
)
check(
	math.abs(tail.events["контакт: удар лапы"] - tail.lead - Battle.HitDelay) < 1e-6,
	"«Хвост-кистень»: контакт левой лапой через HitDelay после начала выпада"
)
check(
	math.abs(tail.duration - 1.4) < 1e-6 and math.abs(tail.events["контакт: удар лапы"] - 0.75) < 1e-6,
	"«Хвост-кистень»: 1.4 с, контакт на 0.75 с"
)
check(
	BossClips.Get(rig, "wake").duration == tl.Wake + tl.StandUp + tl.ToCombat,
	"пробуждение = Wake + StandUp + ToCombat"
)
check(
	BossClips.Get(rig, "victory").duration == tl.Victory and BossClips.Get(rig, "defeat").duration == tl.Defeat,
	"победа и поражение — длительности Timeline"
)
check(
	BossClips.Get(rig, "fall_asleep").duration == tl.FallAsleep,
	"засыпание — длительность Timeline"
)
for _, name in { "sleep_idle", "combat_idle", "walk" } do
	local clip = BossClips.Get(rig, name)
	local d, p = gap(clip.frames[clip.count], clip.frames[1])
	local d2, p2 = 0, 0 -- наибольший шаг между соседними кадрами внутри цикла
	for i = 2, clip.count do
		local a, b = gap(clip.frames[i - 1], clip.frames[i])
		d2, p2 = math.max(d2, a), math.max(p2, b)
	end
	check(
		d <= d2 + 0.05 and p <= p2 + 0.002,
		("цикл %s замыкается: стык %.2f°/%.3f ст., наибольший шаг внутри %.2f°/%.3f ст."):format(
			name,
			d,
			p,
			d2,
			p2
		)
	)
end

-- ── 2. Все состояния подряд: скачки ─────────────────────────────
print("2. Состояния подряд (60 кадров в секунду)")
local DT = 1 / 60
-- Мировые точки по цепочке суставов (как BossService: сустав = родитель · сдвиг(pivot − pivot родителя) · Transform).
local MARKS = { "FPawL", "FPawR", "BPawL", "BPawR", "Head", "Tassel", "Torso" }
local function world(p)
	local joints = {}
	for _, part in rig.Order do
		local info = rig.Parts[part]
		if info.parent then
			joints[part] = joints[info.parent] * CFrame.new(info.pivot - rig.Parts[info.parent].pivot) * p[part]
		else
			joints[part] = CFrame.new(info.pivot) * p[part]
		end
	end
	local out = {}
	for _, part in MARKS do
		out[part] = (joints[part] * CFrame.new(rig.Parts[part].center)).Position
	end
	return out
end
local function stepOf(a, b): (number, string)
	local worst, who = 0, ""
	for _, part in MARKS do
		local d = (a[part] - b[part]).Magnitude
		if d > worst then
			worst, who = d, part
		end
	end
	return worst, who
end
-- быстрейшее движение самих клипов (за 1/60 с) — с ним сравниваются стыки
local native = 0
for _, name in rig.Clips.Names do
	local clip = BossClips.Get(rig, name)
	local prev = nil
	for t = 0, clip.duration, DT do
		local w = world(BossClips.At(rig, clip, t))
		if prev then
			native = math.max(native, (stepOf(prev, w)))
		end
		prev = w
	end
end
print(("     быстрейшее движение клипов: %.3f ст. за кадр"):format(native))

-- Сценарий: атрибуты модели во времени — как пишет сервер. Время — секунды от начала.
type Event = { at: number, set: { [string]: any } }
local function run(title: string, events: { Event }, untilT: number): (number, string, number)
	table.sort(events, function(a, b)
		return a.at < b.at
	end)
	local attrs = { State = "Sleep", StateAt = -10, Moving = false, MovingAt = -10, AttackSeq = 0 }
	local k = 1
	local prev, worst, who, when = nil, 0, "", 0
	local now = 0
	while now <= untilT do
		while events[k] and events[k].at <= now + 1e-9 do
			for key, v in events[k].set do
				if key == "State" then
					attrs.FromState, attrs.FromAt = attrs.State, attrs.StateAt
					attrs.StateAt = events[k].at
				end
				if v == "nil" then
					attrs[key] = nil
				else
					attrs[key] = v
				end
			end
			k += 1
		end
		local function since(key)
			return if attrs[key] then now - attrs[key] else nil
		end
		local p = BossAnim.Sample(rig, {
			state = attrs.State,
			t = now - attrs.StateAt,
			moving = attrs.Moving,
			movingT = since("MovingAt"),
			fromState = attrs.FromState,
			fromT = if attrs.FromAt then attrs.StateAt - attrs.FromAt else nil,
			attackKind = attrs.AttackKind,
			attackT = since("AttackAt"),
			hitT = since("HitAt"),
			clock = 1.7e9 + now,
			attackSeq = attrs.AttackSeq,
			attackPlanT = since("AttackPlanAt"),
			planKind = attrs.PlanKind,
			planSeq = attrs.PlanSeq,
			planT = since("PlanAt"),
			planCancelT = since("PlanCancelAt"),
		})
		local w = world(p)
		if prev then
			local d, part = stepOf(prev, w)
			if d > worst then
				worst, who, when = d, part, now
			end
			if process.env.DEBUG_STEPS and d > native * 0.8 then
				local c, tau, wt = BossClips.Attack(rig, {
					attackKind = attrs.AttackKind,
					attackT = since("AttackAt"),
					attackSeq = attrs.AttackSeq,
					attackPlanT = since("AttackPlanAt"),
					planKind = attrs.PlanKind,
					planSeq = attrs.PlanSeq,
					planT = since("PlanAt"),
					planCancelT = since("PlanCancelAt"),
				})
				print(
					("       шаг %.2f %s на %.3f: %s %s τ %.3f w %.2f"):format(
						d,
						part,
						now,
						attrs.State,
						c and c.name or "-",
						tau,
						wt
					)
				)
			end
		end
		prev = w
		now += DT
	end
	check(
		worst <= native * 1.05,
		("%s: наибольший шаг %.3f ст. за кадр (%s на %.2f с)"):format(title, worst, who, when)
	)
	return worst, who, when
end

-- серверный бой: выпады с планом (как BattleService.plan), удары игрока, бег
local function fight(startAt: number, attacks: number, opts): ({ Event }, number)
	local ev = {}
	local t = startAt
	local function add(at, set)
		table.insert(ev, { at = at, set = set })
	end
	add(t, { State = "Wake" })
	add(t + tl.Wake, { State = "StandUp" })
	add(t + tl.Wake + tl.StandUp, { State = "ToCombat" })
	local combat = t + tl.Wake + tl.StandUp + tl.ToCombat
	local seq = 0
	local plannedAt = combat + 0.6 + Battle.AttackPlan.ExpectedDelay
	add(combat - tl.ToCombat, { PlanKind = "bite", PlanAt = plannedAt, PlanSeq = 1, PlanCancelAt = "nil" })
	add(combat, { State = "Combat" })
	local nextAt = combat + 0.6
	local delays = opts.delays
	for n = 1, attacks do
		local fireAt = nextAt + delays[(n - 1) % #delays + 1]
		seq += 1
		local kind = if n % 3 == 0 then "swipe" else "bite"
		local nextKind = if (n + 1) % 3 == 0 then "swipe" else "bite"
		local nextPlan = fireAt + 1.4 + Battle.AttackPlan.ExpectedDelay
		add(fireAt, {
			AttackKind = kind,
			AttackAt = fireAt,
			AttackSeq = seq,
			AttackPlanAt = plannedAt,
			PlanKind = nextKind,
			PlanAt = nextPlan,
			PlanSeq = seq + 1,
			PlanCancelAt = "nil",
		})
		plannedAt = nextPlan
		nextAt = fireAt + 1.4
	end
	for h = combat + 0.3, nextAt - 0.2, 0.9 do
		table.insert(ev, { at = h, set = { HitAt = h } })
	end
	return ev, nextAt
end

local DELAYS = { 0.017, 0.067, 0.1, 0.033, 0.083, 0.05, 0.117, 0.0 }
local ev, endAt = fight(1, 9, { delays = DELAYS })
local stopAt = endAt - 0.6 -- конец боя посреди выпада
table.insert(ev, { at = stopAt, set = { State = "Victory", PlanCancelAt = stopAt } })
table.insert(
	ev,
	{ at = stopAt + tl.Victory, set = { State = "Return", Moving = true, MovingAt = stopAt + tl.Victory } }
)
table.insert(ev, { at = stopAt + tl.Victory + 3, set = { Moving = false, MovingAt = stopAt + tl.Victory + 3 } })
table.insert(ev, { at = stopAt + tl.Victory + 3.4, set = { State = "FallAsleep" } })
table.insert(ev, { at = stopAt + tl.Victory + 3.4 + tl.FallAsleep, set = { State = "Sleep" } })
run(
	"сон → бой (9 выпадов, удары, конец посреди выпада) → победа → домой → сон",
	ev,
	stopAt + tl.Victory + 8
)

ev, endAt = fight(1, 4, { delays = DELAYS })
stopAt = endAt - 1.0
table.insert(ev, { at = stopAt, set = { State = "Defeat", PlanCancelAt = stopAt } })
table.insert(ev, { at = stopAt + tl.Defeat, set = { State = "Return", Moving = true, MovingAt = stopAt + tl.Defeat } })
table.insert(ev, { at = stopAt + tl.Defeat + 2, set = { Moving = false, MovingAt = stopAt + tl.Defeat + 2 } })
table.insert(ev, { at = stopAt + tl.Defeat + 2.3, set = { State = "FallAsleep" } })
table.insert(ev, { at = stopAt + tl.Defeat + 2.3 + 0.7, set = { State = "Wake" } }) -- разбудили, пока засыпал
run(
	"бой → поражение посреди замаха → домой → разбудили во время засыпания",
	ev,
	stopAt + tl.Defeat + 6
)

-- бег в бою: игрок отходит, план отменён, босс догоняет и бьёт без плана
ev = {}
for _, e in (fight(1, 1, { delays = { 0.05 } })) do
	table.insert(ev, e)
end
local combatAt = 1 + tl.Wake + tl.StandUp + tl.ToCombat
local cancelAt = combatAt + 0.6 + 0.05 + 0.9 -- через 0.9 с после первого выпада игрок ушёл
table.insert(ev, { at = cancelAt, set = { PlanCancelAt = cancelAt, Moving = true, MovingAt = cancelAt } })
table.insert(ev, { at = cancelAt + 1.5, set = { Moving = false, MovingAt = cancelAt + 1.5 } })
table.insert(
	ev,
	{
		at = cancelAt + 1.55,
		set = { AttackKind = "bite", AttackAt = cancelAt + 1.55, AttackSeq = 2, AttackPlanAt = "nil" },
	}
)
run("бой: план отменён, бег, выпад без плана", ev, cancelAt + 3.5)

-- ── 3. План атаки: контакт и урон ───────────────────────────────
print("3. План атаки")
local seed = 4
local function rand(): number -- своя последовательность (в Lune нет Random)
	seed = (seed * 48271) % 2147483647
	return seed / 2147483647
end
local offsets, worstOff, sum = 0, 0, 0
local kinds = {}
local tick = 0
local nextBoss = 0.6
local planAt = nextBoss + Battle.AttackPlan.ExpectedDelay
for n = 1, 2000 do
	while tick < nextBoss do
		tick += Battle.TickSeconds + rand() / 60 -- task.wait(0.1) просыпается на кадре
	end
	local fireAt = tick
	local kind = if n % 3 == 0 then "swipe" else "bite"
	kinds[kind] = (kinds[kind] or 0) + 1
	-- клиент в момент урона (выпад + HitDelay): на каком времени клипа он
	local damageAt = fireAt + Battle.HitDelay
	local clip, tau = BossClips.Attack(rig, {
		attackKind = kind,
		attackT = damageAt - fireAt,
		attackSeq = n,
		attackPlanT = damageAt - planAt,
		planKind = if (n + 1) % 3 == 0 then "swipe" else "bite",
		planSeq = n + 1,
		planT = damageAt - (fireAt + 1.4 + Battle.AttackPlan.ExpectedDelay),
	})
	local contact = clip.events["контакт: удар лапы"]
	local off = tau - contact -- плюс — видимый контакт раньше урона
	worstOff = math.max(worstOff, math.abs(off))
	sum += off
	offsets += 1
	nextBoss = fireAt + 1.4
	planAt = nextBoss + Battle.AttackPlan.ExpectedDelay
end
check(
	kinds.swipe == 666 and kinds.bite == 1334,
	("каждый третий — «Хвост-кистень»: %d из %d"):format(kinds.swipe, offsets)
)
check(
	math.abs(sum / offsets) < 0.02 and worstOff < 0.09,
	("видимый контакт и урон сервера: в среднем %+.3f с, наибольшее расхождение %.3f с"):format(
		sum / offsets,
		worstOff
	)
)
-- выпад без плана: контакт ровно в момент урона
local clip, tau = BossClips.Attack(rig, { attackKind = "swipe", attackT = Battle.HitDelay, attackSeq = 3 })
check(
	clip.name == "tail_strike" and math.abs(tau - clip.events["контакт: удар лапы"]) < 1e-6,
	"выпад без плана: контакт ровно в момент урона"
)
-- замах по плану начинается за lead до выпада
clip, tau = BossClips.Attack(rig, { planKind = "swipe", planSeq = 3, attackSeq = 2, planT = -tail.lead + 0.01 })
check(
	clip and clip.name == "tail_strike" and math.abs(tau - 0.01) < 1e-6,
	"замах «Хвоста-кистеня» начинается за 0.5 с до выпада"
)
clip = BossClips.Attack(rig, { planKind = "bite", planSeq = 3, attackSeq = 2, planT = -0.6 })
check(clip == nil, "раньше этого замаха нет")
-- отмена до начала замаха — ничего; после — замах замирает и гаснет
clip = BossClips.Attack(rig, { planKind = "bite", planSeq = 2, attackSeq = 1, planT = -0.4, planCancelT = 0.1 })
check(clip == nil, "план отменён до начала замаха — замаха нет")
local c1, t1, w1 =
	BossClips.Attack(rig, { planKind = "bite", planSeq = 2, attackSeq = 1, planT = 0, planCancelT = 0.1 })
local c2, t2, w2 =
	BossClips.Attack(rig, { planKind = "bite", planSeq = 2, attackSeq = 1, planT = 0.05, planCancelT = 0.15 })
local c3, _, w3 =
	BossClips.Attack(rig, { planKind = "bite", planSeq = 2, attackSeq = 1, planT = 0.2, planCancelT = 0.3 })
check(
	c1 and c2 and math.abs(t1 - t2) < 1e-6 and w1 > w2 and w2 > 0 and c3 == nil and w3 == 0,
	("отменённый замах замирает (%.2f с клипа) и гаснет за 0.3 с"):format(t1)
)
-- первый выпад: план объявлен в начале ToCombat — запас на задержку сети
local slack = tl.ToCombat + 0.6 + Battle.AttackPlan.ExpectedDelay - math.max(heavy.lead, tail.lead)
check(
	slack > 0.6,
	("первый замах не обрезается при задержке сети до %.2f с (было 0.15 с)"):format(
		slack
	)
)

-- ── 5. Цена кадра и память ──────────────────────────────────────
print("5. Цена кадра и память")
local input = {
	state = "Combat",
	t = 10,
	moving = false,
	clock = 1.7e9,
	attackKind = "swipe",
	attackT = 0.2,
	attackSeq = 3,
	attackPlanT = 0.25,
	hitT = 0.1,
	planKind = "bite",
	planSeq = 4,
	planT = -1.0,
}
local N = 3000
local t0 = os.clock()
for _ = 1, N do
	BossAnim.Sample(rig, input)
end
local us4 = (os.clock() - t0) / N * 1e6
local king = others[3]
t0 = os.clock()
for _ = 1, N do
	BossAnim.Sample(
		king,
		{ state = "Combat", t = 10, moving = false, clock = 1.7e9, attackKind = "bite", attackT = 0.2, hitT = 0.1 }
	)
end
local us3 = (os.clock() - t0) / N * 1e6
check(
	us4 < 200,
	("кадр Сфинкса в бою (выпад + реакция на удар): %.0f мкс; Крысиный король: %.0f мкс (Lune, ПК)"):format(
		us4,
		us3
	)
)
local frames = 0
for _, name in rig.Clips.Names do
	frames += BossClips.Get(rig, name).count
end
print(
	("     в памяти %d кадров × 27 суставов = %d CFrame, ≈ %.0f КБ кучи Lune"):format(
		frames,
		frames * 27,
		memory
	)
)

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end

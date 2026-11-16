--!nocheck
-- Проверка клипов босса 4 «Сфинкс-лежебока» без Roblox Studio и без изменения кода игры: читает экспорт Blender
-- (assets/models/Boss4_Sphinx.rig.json и .anim.json), настоящие Shared/BossAnim и Config/Battle из src/ и проверяет:
--   1) формат клипов и стыки с позами движка (те же 13 имён, те же 27 частей);
--   2) что нынешний BossAnim (две позы на состояние) работает на скелете Сфинкса как есть;
--   3) образец проигрывателя клипов (только здесь, не в игре): плавность, цена кадра рядом с BossAnim.Sample;
--   4) размер данных клипов в разных упаковках и память после разбора;
--   5) расписание атак с заранее объявленным временем (схема «план атаки») на модели серверного цикла боя:
--      шаг 0.1 с, интервал 1.4 с, попадание через HitDelay — те же числа, что в BattleService.
-- Ничего не пишет. Запуск из корня репозитория: lune run scripts/lune/check_boss4_clips.luau.

local fs = require("@lune/fs")
local process = require("@lune/process")
local serde = require("@lune/serde")

local Env = require("./env")
local CFrame = Env.roblox.CFrame

local BossAnim = Env.Require("ReplicatedStorage.Shared.BossAnim")
local Battle = Env.Require("ReplicatedStorage.Shared.Config.Battle")
local Boss3 = Env.Require("ReplicatedStorage.Shared.Config.Boss3RatKingRig")

local rigData = serde.decode("json", fs.readFile("assets/models/Boss4_Sphinx.rig.json"))
local anim = serde.decode("json", fs.readFile("assets/models/Boss4_Sphinx.anim.json"))
local rig = { Order = rigData.order, Parts = rigData.parts, Poses = rigData.poses }
local FPS = anim.fps
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

local function diff(a: CFrame, b: CFrame): number
	local ca, cb = { a:GetComponents() }, { b:GetComponents() }
	local worst = 0
	for i = 1, 12 do
		worst = math.max(worst, math.abs(ca[i] - cb[i]))
	end
	return worst
end

local function jump(a, b): number
	local worst = 0
	for _, part in rig.Order do
		worst = math.max(worst, diff(a[part], b[part]))
	end
	return worst
end

-- ── 1. Формат и стыки ───────────────────────────────────────────────────────────────────────────────────────
print("1. Формат клипов и стыки с позами движка")
local sameOrder = #anim.order == #rig.Order
for i, name in rig.Order do
	sameOrder = sameOrder and anim.order[i] == name
end
check(sameOrder and #rig.Order == 27, ("порядок и число частей как в скелете (%d)"):format(#rig.Order))
local poseCount = 0
for _ in rig.Poses do
	poseCount += 1
end
local allPoses = true
for _, name in { "sleep", "alert", "stand", "combat", "combat2", "walkA", "walkB", "bite", "swipe", "hit", "bark", "bark2", "dizzy" } do
	allPoses = allPoses and rig.Poses[name] ~= nil
end
check(allPoses and poseCount == 13, "13 игровых поз на месте")

-- Клипы как массивы CFrame (так их держал бы проигрыватель в памяти).
type Clip = { name: string, duration: number, loop: boolean, frames: { { CFrame } }, events: { [string]: number } }
local clips: { [string]: Clip } = {}
local clipNames = {}
local before = gcinfo()
local frameTotal = 0
for name, data in anim.clips do
	local frames = table.create(#data.frames)
	for i, row in data.frames do
		local list = table.create(#row)
		for j, v in row do
			list[j] = CFrame.new(v[1], v[2], v[3], v[4], v[5], v[6], v[7])
		end
		frames[i] = list
	end
	frameTotal += #frames
	clips[name] = { name = name, duration = data.duration, loop = data.loop, frames = frames, events = data.events }
	table.insert(clipNames, name)
end
table.sort(clipNames)
local heapCFrames = gcinfo() - before

for _, name in clipNames do
	local clip = clips[name]
	local expect = if clip.loop then math.floor(clip.duration * FPS + 0.5) else math.floor(clip.duration * FPS + 0.5) + 1
	check(#clip.frames == expect, ("%s: кадров %d на %.3f с (%s)"):format(name, #clip.frames, clip.duration, if clip.loop then "цикл" else "с обоими концами"))
end

local function asPose(list: { CFrame }): { [string]: CFrame }
	local pose = {}
	for j, part in rig.Order do
		pose[part] = list[j]
	end
	return pose
end

local ENDS = {
	wake = { "sleep", "combat" }, heavy_paw = { "combat", "combat" }, tail_strike = { "combat", "combat" },
	hit = { "combat", "combat" }, victory = { "combat", "stand" }, defeat = { "combat", "stand" },
	fall_asleep = { "stand", "sleep" },
}
local worstEnd = 0
for name, ends in ENDS do
	local clip = clips[name]
	worstEnd = math.max(worstEnd, jump(asPose(clip.frames[1]), BossAnim.Pose(rig, ends[1])))
	worstEnd = math.max(worstEnd, jump(asPose(clip.frames[#clip.frames]), BossAnim.Pose(rig, ends[2])))
end
check(worstEnd < 2e-3, ("концы семи клипов совпадают с позами BossAnim.Pose (наибольшая разница %.5f)"):format(worstEnd))
for _, pair in { { "sleep_idle", "sleep" }, { "combat_idle", "combat" } } do
	local gap = jump(asPose(clips[pair[1]].frames[1]), BossAnim.Pose(rig, pair[2]))
	check(gap < 6e-3, ("%s начинается с позы %s (%.5f)"):format(pair[1], pair[2], gap))
end

-- ── 2. Нынешний движок на скелете Сфинкса ───────────────────────────────────────────────────────────────────
print("2. Нынешний BossAnim (позы) на скелете Сфинкса, без клипов")
local okOld, err = pcall(function()
	local scans = {
		{ "Sleep", 6 }, { "Wake", tl.Wake }, { "StandUp", tl.StandUp }, { "ToCombat", tl.ToCombat }, { "Combat", 3 },
		{ "Victory", tl.Victory }, { "Defeat", tl.Defeat }, { "Return", 2 }, { "FallAsleep", tl.FallAsleep },
	}
	for _, scan in scans do
		for i = 0, math.ceil(scan[2] * 60) do
			local t = i / 60
			local pose = BossAnim.Sample(rig, {
				state = scan[1], t = t, clock = 10 + t, moving = scan[1] == "Return", movingT = t,
				attackKind = if i % 2 == 0 then "bite" else "swipe", attackT = t % 1.4, hitT = t % 0.9,
			})
			for _, part in rig.Order do
				local x = pose[part].Position.X
				assert(x == x, "NaN в позе " .. scan[1])
			end
		end
	end
end)
check(okOld, "все девять состояний считаются без ошибок" .. (if okOld then "" else ": " .. tostring(err)))

-- ── 3. Образец проигрывателя клипов ─────────────────────────────────────────────────────────────────────────
print("3. Образец проигрывателя клипов (два соседних кадра и Lerp)")
local function sampleClip(clip: Clip, t: number, out: { [string]: CFrame })
	local frames = clip.frames
	local n = #frames
	local f = t * FPS
	local a, b
	if clip.loop then
		f %= n
		local i = math.floor(f)
		a, b, f = frames[i + 1], frames[(i + 1) % n + 1], f - i
	else
		f = math.clamp(f, 0, n - 1)
		local i = math.min(math.floor(f), n - 2)
		a, b, f = frames[i + 1], frames[i + 2], f - i
	end
	for j, part in rig.Order do
		out[part] = a[j]:Lerp(b[j], f)
	end
	return out
end

for _, name in clipNames do
	local clip = clips[name]
	local worst30, worst60, spikes = 0, 0, 0
	local prev, steps = nil, {}
	local last = if clip.loop then clip.duration * 2 else clip.duration
	for i = 0, math.floor(last * 60 + 0.5) do
		local pose = sampleClip(clip, i / 60, {})
		if prev then
			table.insert(steps, jump(prev, pose))
		end
		prev = pose
	end
	for i, s in steps do
		worst60 = math.max(worst60, s)
		if i > 1 and i < #steps and s > 0.05 and s > 3 * math.max(steps[i - 1], steps[i + 1]) then
			spikes += 1
		end
	end
	for i = 1, #clip.frames - 1 do
		worst30 = math.max(worst30, jump(asPose(clip.frames[i]), asPose(clip.frames[i + 1])))
	end
	check(spikes == 0 and worst60 <= worst30 * 0.75 + 1e-3, ("%s: при 60 кадрах в секунду шаг %.3f (в данных при 30 — %.3f), одиночных скачков %d"):format(name, worst60, worst30, spikes))
end

-- Цена кадра: образец проигрывателя и нынешний BossAnim.Sample на одном и том же скелете (числа Lune, не телефона —
-- важно отношение).
local function bench(label: string, count: number, fn: (number) -> ())
	local started = os.clock()
	for i = 1, count do
		fn(i)
	end
	local each = (os.clock() - started) / count * 1e6
	print(("  %-58s %7.1f мкс на кадр"):format(label, each))
	return each
end
local N = 20000
local reuse = {}
local tClip = bench("клип «Тяжёлая лапа», 27 суставов (образец)", N, function(i)
	sampleClip(clips.heavy_paw, (i % 39) / 30 + 0.013, reuse)
end)
local tLoop = bench("клип «Сон», 27 суставов (образец)", N, function(i)
	sampleClip(clips.sleep_idle, i * 0.017, reuse)
end)
local tOldFight = bench("BossAnim.Sample: бой с выпадом и попаданием, Сфинкс 27", N, function(i)
	BossAnim.Sample(rig, { state = "Combat", t = 5, clock = i * 0.017, moving = false, attackKind = "bite", attackT = 0.1, hitT = 0.1 })
end)
local tOldRun = bench("BossAnim.Sample: бой на бегу, Сфинкс 27", N, function(i)
	BossAnim.Sample(rig, { state = "Combat", t = 5, clock = i * 0.017, moving = true, movingT = 0.1, attackKind = "bite", attackT = 0.1 })
end)
local tOldSleep = bench("BossAnim.Sample: сон, Сфинкс 27", N, function(i)
	BossAnim.Sample(rig, { state = "Sleep", t = 30, clock = i * 0.017 })
end)
bench("BossAnim.Sample: бой с выпадом, Крысиный король 21", N, function(i)
	BossAnim.Sample(Boss3, { state = "Combat", t = 5, clock = i * 0.017, moving = false, attackKind = "bite", attackT = 0.1, hitT = 0.1 })
end)
check(tClip <= tOldFight * 1.2, ("кадр клипа не дороже кадра нынешнего боя (%.1f против %.1f мкс)"):format(tClip, tOldFight))
check(tLoop <= math.max(tOldSleep, tOldRun) * 1.5, ("кадр цикла сна сопоставим с нынешним (%.1f против %.1f мкс)"):format(tLoop, tOldSleep))

-- ── 4. Размер данных ────────────────────────────────────────────────────────────────────────────────────────
print("4. Размер данных клипов")
local function num(v: number): string
	local s = string.format("%.4f", v)
	s = string.gsub(s, "0+$", "")
	s = string.gsub(s, "%.$", "")
	if s == "-0" or s == "" then
		s = "0"
	end
	return s
end
-- какие суставы вообще сдвигаются (остальным хватит поворота)
local moves = {}
for j in rig.Order do
	moves[j] = false
end
for _, data in anim.clips do
	for _, row in data.frames do
		for j, v in row do
			if math.abs(v[1]) > 1e-3 or math.abs(v[2]) > 1e-3 or math.abs(v[3]) > 1e-3 then
				moves[j] = true
			end
		end
	end
end
local moving = 0
for _, flag in moves do
	if flag then
		moving += 1
	end
end
local SLOW = { sleep_idle = true, combat_idle = true }
local dense, lean, leanSlow, packed, packedSlow = 0, 0, 0, 0, 0
local perClip = {}
for _, name in clipNames do
	local data = anim.clips[name]
	local d, l = 0, 0
	for _, row in data.frames do
		for j, v in row do
			d += #num(v[1]) + #num(v[2]) + #num(v[3]) + #num(v[4]) + #num(v[5]) + #num(v[6]) + #num(v[7]) + 9
			-- поворот тремя числами (w ≥ 0 восстанавливается), сдвиг — только у тех, кто сдвигается
			local sign = if v[7] < 0 then -1 else 1
			l += #num(v[4] * sign) + #num(v[5] * sign) + #num(v[6] * sign) + 3
			if moves[j] then
				l += #num(v[1]) + #num(v[2]) + #num(v[3]) + 3
			end
		end
	end
	local frames = #data.frames
	local bytes = frames * (27 * 6 + moving * 6) -- по 2 байта на число
	dense += d
	lean += l
	packed += bytes
	local k = if SLOW[name] then 0.5 else 1
	leanSlow += l * k
	packedSlow += bytes * k
	perClip[name] = { d, l, bytes }
end
print(("  суставов со сдвигом: %d из 27; кадров всего %d"):format(moving, frameTotal))
print(("  %-14s %10s %10s %10s"):format("клип", "плотно", "экономно", "байты"))
for _, name in clipNames do
	local p = perClip[name]
	print(("  %-14s %9.0fк %9.0fк %9.1fк"):format(name, p[1] / 1000, p[2] / 1000, p[3] / 1000))
end
print(("  всего: плотно %.0f тыс. знаков; экономно %.0f тыс.; экономно и медленные циклы на 15 к/с %.0f тыс."):format(dense / 1000, lean / 1000, leanSlow / 1000))
print(("  двоичная упаковка по 2 байта: %.0f КБ (%.0f тыс. знаков текстом base64); с циклами на 15 к/с %.0f КБ (%.0f тыс.)"):format(
	packed / 1024, packed * 4 / 3 / 1000, packedSlow / 1024, packedSlow * 4 / 3 / 1000))
print(("  память после разбора в CFrame (Lune): %d КБ на %d кадров × 27"):format(heapCFrames, frameTotal))
-- точность двоичной упаковки: поворот ±1 → шаг 1/32767, сдвиг ±8 стадов → шаг 8/32767
local worstQ = 0
for _, data in anim.clips do
	for _, row in data.frames do
		for _, v in row do
			local sign = if v[7] < 0 then -1 else 1
			local q = {}
			for k = 4, 6 do
				q[k] = math.floor(v[k] * sign * 32767 + 0.5) / 32767
			end
			local w = math.sqrt(math.max(0, 1 - q[4] ^ 2 - q[5] ^ 2 - q[6] ^ 2))
			local p = {}
			for k = 1, 3 do
				p[k] = math.floor(v[k] / 8 * 32767 + 0.5) / 32767 * 8
			end
			local exact = CFrame.new(v[1], v[2], v[3], v[4], v[5], v[6], v[7])
			local got = CFrame.new(p[1], p[2], p[3], q[4], q[5], q[6], w)
			worstQ = math.max(worstQ, diff(exact, got))
		end
	end
end
check(worstQ < 2e-3, ("двоичная упаковка по 2 байта: наибольшая ошибка числа CFrame %.5f"):format(worstQ))

-- ── 5. Расписание атак с «планом» ───────────────────────────────────────────────────────────────────────────
print("5. Расписание атак: сервер объявляет время следующей атаки заранее (модель цикла BattleService)")
local LEAD = { bite = 0.45, swipe = 0.5 } -- от начала клипа до начала выпада в игре
local LENGTH = { bite = clips.heavy_paw.duration, swipe = clips.tail_strike.duration }
check(math.abs(clips.heavy_paw.events["контакт: удар лапы"] - (LEAD.bite + Battle.HitDelay)) < 1e-6
	and math.abs(clips.tail_strike.events["контакт: удар лапы"] - (LEAD.swipe + Battle.HitDelay)) < 1e-6,
	"контакт в обоих клипах — ровно через HitDelay после начала выпада")
local seed = 12345
local function rnd(): number
	seed = (seed * 48271) % 2147483647
	return seed / 2147483647
end
local interval = Battle.Bosses[1].AttackInterval
local late, lateMax, gapMin, hitLate, hitLateMax, attacks = 0, 0, math.huge, 0, 0, 0
for _ = 1, 400 do -- 400 боёв по 12 атак
	local now = rnd()
	local function frame()
		now += 1 / 60 + (rnd() - 0.5) * 0.004 + (if rnd() < 0.02 then 0.03 else 0) -- кадры сервера, изредка долгий
	end
	local function wait(seconds: number)
		local untilTime = now + seconds
		repeat
			frame()
		until now >= untilTime
	end
	local nextBoss = now + 0.6 -- бой начался: первый выпад через 0.6 с
	local plan = nextBoss
	local count = 0
	local prevEnd = -math.huge
	while count < 12 do
		if now >= nextBoss then
			count += 1
			attacks += 1
			local kind = if count % 3 == 0 then "swipe" else "bite"
			local attackAt = now
			-- клиент: клип идёт по плану (plan), контакт на plan + HitDelay; сервер: урон через HitDelay после attackAt
			local clipStart = plan - LEAD[kind]
			gapMin = math.min(gapMin, clipStart - prevEnd)
			prevEnd = clipStart + LENGTH[kind]
			local jitter = attackAt - plan
			late += jitter
			lateMax = math.max(lateMax, jitter)
			local damageAt = attackAt
			local untilTime = attackAt + Battle.HitDelay
			local t = attackAt
			repeat
				t += 1 / 60
			until t >= untilTime
			damageAt = t
			local behind = damageAt - (plan + Battle.HitDelay)
			hitLate += behind
			hitLateMax = math.max(hitLateMax, behind)
			nextBoss = now + interval
			plan = nextBoss
		end
		wait(Battle.TickSeconds)
	end
end
print(("  атак в модели: %d; выпад позже плана в среднем на %.3f с, наибольшее %.3f с"):format(attacks, late / attacks, lateMax))
print(("  урон на сервере позже видимого контакта в среднем на %.3f с, наибольшее %.3f с (плюс задержка сети до игрока)"):format(hitLate / attacks, hitLateMax))
print(("  наименьший промежуток между концом клипа атаки и началом следующего замаха: %.3f с"):format(gapMin))
check(gapMin >= 0, "клипы соседних атак не накладываются при интервале 1.4 с")
check(lateMax < 0.2, "выпад отстаёт от плана меньше чем на 0.2 с")
for _, latency in { 0.05, 0.15, 0.3, 0.6 } do
	local firstCut = math.max(0, latency - (0.6 - LEAD.bite))
	local nextCut = math.max(0, latency - (interval - LEAD.swipe))
	print(("  задержка сети %.2f с: первый замах боя обрезан на %.2f с из %.2f, остальные — на %.2f с"):format(latency, firstCut, LEAD.bite, nextCut))
end

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end

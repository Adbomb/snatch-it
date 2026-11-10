--!nocheck
-- Проверка стыков процедурных анимаций боссов без Roblox Studio (Shared/BossAnim, скелеты боссов 1–3): поза не
-- прыгает, когда босс после поражения или победы идёт домой, начинает и перестаёт идти (в бою и по дороге домой) и
-- засыпает, только что остановившись. Сравнивает Transform суставов в последний момент одного состояния и в первый
-- момент следующего (те же часы), и шаг за 1/60 с, пока шаг включается, — с шагом обычной ходьбы.
-- Запуск из корня репозитория: lune run scripts/lune/check_boss_anim.luau.

local process = require("@lune/process")

local Env = require("./env")

local BossAnim = Env.Require("ReplicatedStorage.Shared.BossAnim")
local Battle = Env.Require("ReplicatedStorage.Shared.Config.Battle")
local RIGS = {
	{ "пёс (босс 1)", Env.Require("ReplicatedStorage.Shared.Config.Boss1DogRig") },
	{ "торговец (босс 2)", Env.Require("ReplicatedStorage.Shared.Config.Boss2TraderRig") },
	{ "Крысиный король (босс 3)", Env.Require("ReplicatedStorage.Shared.Config.Boss3RatKingRig") },
}
local tl = Battle.Timeline
local EXACT = 1e-4 -- стык без скачка: Transform совпадают (числа CFrame)
local CLOCKS = { 0.13, 1.71, 3.38, 5.05 } -- разные фазы шага и боевой стойки

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

-- Наибольшая разница чисел CFrame суставов двух поз (сдвиг в стадах и элементы поворота).
local function jump(rig, a, b): number
	local worst = 0
	for _, part in rig.Order do
		local ca, cb = { a[part]:GetComponents() }, { b[part]:GetComponents() }
		for i = 1, 12 do
			worst = math.max(worst, math.abs(ca[i] - cb[i]))
		end
	end
	return worst
end

local function sample(rig, input)
	input.t = input.t or 0
	input.moving = input.moving == true
	return BossAnim.Sample(rig, input)
end

for _, entry in RIGS do
	local name, rig = entry[1], entry[2]
	print(name .. ":")
	local worst = { defeat = 0, victory = 0, stop = 0, start = 0, asleep = 0, walking = 0, combatOn = 0, combatOff = 0 }
	for _, clock in CLOCKS do
		-- поражение и победа кончаются стойкой — возвращение начинается с неё, шаг включается после
		local stand = sample(rig, { state = "Return", clock = clock })
		local walkIn = sample(rig, { state = "Return", clock = clock, moving = true, movingT = 0 })
		worst.defeat =
			math.max(worst.defeat, jump(rig, sample(rig, { state = "Defeat", t = tl.Defeat, clock = clock }), walkIn))
		worst.victory = math.max(
			worst.victory,
			jump(rig, sample(rig, { state = "Victory", t = tl.Victory, clock = clock }), walkIn)
		)
		worst.start = math.max(worst.start, jump(rig, stand, walkIn))
		-- остановился по дороге домой: шаг гаснет плавно
		local walking = sample(rig, { state = "Return", clock = clock, moving = true, movingT = 10 })
		local stopped = sample(rig, { state = "Return", clock = clock, moving = false, movingT = 0 })
		worst.stop = math.max(worst.stop, jump(rig, walking, stopped))
		-- засыпание с той позы, в которой пришёл (и если ещё идёт, и если только что встал)
		for _, input in
			{ { moving = false, movingT = 0.1 }, { moving = true, movingT = 10 }, { moving = false, movingT = 10 } }
		do
			local before =
				sample(rig, { state = "Return", clock = clock, moving = input.moving, movingT = input.movingT })
			local after = sample(
				rig,
				{ state = "FallAsleep", t = 0, clock = clock, moving = input.moving, movingT = input.movingT }
			)
			worst.asleep = math.max(worst.asleep, jump(rig, before, after))
		end
		-- бой: побежал и остановился
		local idle = sample(rig, { state = "Combat", t = 5, clock = clock, moving = false, movingT = 10 })
		local run = sample(rig, { state = "Combat", t = 5, clock = clock, moving = true, movingT = 10 })
		worst.combatOn = math.max(
			worst.combatOn,
			jump(rig, idle, sample(rig, { state = "Combat", t = 5, clock = clock, moving = true, movingT = 0 }))
		)
		worst.combatOff = math.max(
			worst.combatOff,
			jump(rig, run, sample(rig, { state = "Combat", t = 5, clock = clock, moving = false, movingT = 0 }))
		)
	end
	-- остальные стыки цикла: сон ↔ пробуждение, к бою → бой, бой (с выпадом и попаданием) → победа / поражение,
	-- танец победы → стойка, головокружение → стойка, засыпание → сон
	local other = {}
	local function seam(label, a, b)
		other[label] = math.max(other[label] or 0, jump(rig, a, b))
	end
	for _, clock in CLOCKS do
		seam(
			"сон → пробуждение",
			sample(rig, { state = "Sleep", t = 30, clock = clock }),
			sample(rig, { state = "Wake", t = 0, clock = clock })
		)
		seam(
			"засыпание → сон",
			sample(rig, { state = "FallAsleep", t = tl.FallAsleep, clock = clock }),
			sample(rig, { state = "Sleep", t = 0, clock = clock })
		)
		for _, moving in { false, true } do
			local fight =
				{ clock = clock, moving = moving, movingT = 10, attackKind = "swipe", attackT = 0.2, hitT = 0.1 }
			local function with(state, t)
				local input = table.clone(fight)
				input.state, input.t = state, t
				return sample(rig, input)
			end
			seam("к бою → бой", with("ToCombat", tl.ToCombat), with("Combat", 0))
			seam("бой → победа", with("Combat", 5), with("Victory", 0))
			seam("бой → поражение", with("Combat", 5), with("Defeat", 0))
		end
		local v = tl.Victory - 0.4
		seam(
			"танец → стойка",
			sample(rig, { state = "Victory", t = v - 1e-6, clock = clock }),
			sample(rig, { state = "Victory", t = v, clock = clock })
		)
		local d = tl.Defeat - 0.6
		seam(
			"головокружение → стойка",
			sample(rig, { state = "Defeat", t = d - 1e-6, clock = clock }),
			sample(rig, { state = "Defeat", t = d, clock = clock })
		)
	end
	for _, label in
		{
			"сон → пробуждение",
			"засыпание → сон",
			"к бою → бой",
			"бой → победа",
			"бой → поражение",
			"танец → стойка",
			"головокружение → стойка",
		}
	do
		check(other[label] < EXACT, ("%s без скачка (%.5f)"):format(label, other[label]))
	end
	-- разбудили, пока засыпал или только уснул: пробуждение начинается с позы, где застали
	local caught = 0
	for _, clock in CLOCKS do
		for _, lasted in { 0.05, 0.3, 0.6, 0.88, 1.2, 1.55 } do
			local before =
				sample(rig, { state = "FallAsleep", t = lasted, clock = clock, moving = false, movingT = 0.1 + lasted })
			local after = sample(rig, {
				state = "Wake",
				t = 0,
				clock = clock,
				moving = false,
				movingT = 0.1 + lasted,
				fromState = "FallAsleep",
				fromT = lasted,
			})
			caught = math.max(caught, jump(rig, before, after))
			local slept = sample(rig, { state = "Sleep", t = lasted, clock = clock })
			local woke = sample(rig, { state = "Wake", t = 0, clock = clock, fromState = "Sleep", fromT = lasted })
			caught = math.max(caught, jump(rig, slept, woke))
		end
	end
	check(
		caught < EXACT,
		("разбудили, пока засыпал или только уснул — без скачка (%.5f)"):format(
			caught
		)
	)
	check(
		worst.defeat < EXACT,
		("поражение → возвращение без скачка (%.5f)"):format(worst.defeat)
	)
	check(
		worst.victory < EXACT,
		("победа → возвращение без скачка (%.5f)"):format(worst.victory)
	)
	check(
		worst.start < EXACT,
		("начал идти домой — шаг включается с нуля (%.5f)"):format(worst.start)
	)
	check(
		worst.stop < EXACT,
		("остановился дома — шаг гаснет с полного (%.5f)"):format(worst.stop)
	)
	check(
		worst.asleep < EXACT,
		("засыпание начинается с позы возвращения (%.5f)"):format(worst.asleep)
	)
	check(
		worst.combatOn < EXACT and worst.combatOff < EXACT,
		("в бою побежал / остановился без скачка (%.5f / %.5f)"):format(
			worst.combatOn,
			worst.combatOff
		)
	)
	-- шаг за 1/60 с, пока шаг включается и гаснет, не больше, чем в обычной ходьбе (не рывок)
	local step, walkStep = 0, 0
	local prevIn, prevOut, prevWalk
	for i = 0, 60 do
		local t = i / 60
		local clock = 2 + t
		local walkIn = sample(rig, { state = "Return", clock = clock, moving = true, movingT = t })
		local walkOut = sample(rig, { state = "Return", clock = clock, moving = false, movingT = t })
		local walk = sample(rig, { state = "Return", clock = clock, moving = true, movingT = 10 })
		if prevIn then
			step = math.max(step, jump(rig, prevIn, walkIn), jump(rig, prevOut, walkOut))
			walkStep = math.max(walkStep, jump(rig, prevWalk, walk))
		end
		prevIn, prevOut, prevWalk = walkIn, walkOut, walk
	end
	check(
		step <= walkStep * 1.5 + 1e-3,
		("шаг включается и гаснет плавно: за кадр %.4f, в ходьбе %.4f"):format(
			step,
			walkStep
		)
	)
	-- внутри переходов по кадрам (1/60 с) нет одиночных скачков: кадр не больше трёх соседних (быстрая поза — да,
	-- перескок поворота на другую сторону — нет)
	local scans = {
		{
			"пробуждение",
			tl.Wake,
			function(t, c)
				return { state = "Wake", t = t, clock = c }
			end,
		},
		{
			"пробуждение во время засыпания",
			tl.Wake,
			function(t, c)
				return { state = "Wake", t = t, clock = c, fromState = "FallAsleep", fromT = 0.4, movingT = 0.5 + t }
			end,
		},
		{
			"пробуждение в конце засыпания",
			tl.Wake,
			function(t, c)
				return { state = "Wake", t = t, clock = c, fromState = "FallAsleep", fromT = 1.3, movingT = 1.4 + t }
			end,
		},
		{
			"к бою",
			tl.ToCombat,
			function(t, c)
				return { state = "ToCombat", t = t, clock = c, moving = true, movingT = t }
			end,
		},
		{
			"победа",
			tl.Victory,
			function(t, c)
				return { state = "Victory", t = t, clock = c, attackKind = "bite", attackT = 0.15 + t }
			end,
		},
		{
			"поражение",
			tl.Defeat,
			function(t, c)
				return { state = "Defeat", t = t, clock = c, hitT = t, moving = false, movingT = t }
			end,
		},
		{
			"засыпание",
			tl.FallAsleep,
			function(t, c)
				return { state = "FallAsleep", t = t, clock = c, moving = false, movingT = 0.02 + t }
			end,
		},
		{
			"засыпание на ходу",
			tl.FallAsleep,
			function(t, c)
				return { state = "FallAsleep", t = t, clock = c, moving = true, movingT = 10 }
			end,
		},
		{
			"бой, побежал",
			0.6,
			function(t, c)
				return { state = "Combat", t = 5, clock = c, moving = true, movingT = t }
			end,
		},
		{
			"бой, остановился",
			0.6,
			function(t, c)
				return { state = "Combat", t = 5, clock = c, moving = false, movingT = t }
			end,
		},
	}
	for _, scan in scans do
		local label, duration, make = scan[1], scan[2], scan[3]
		local spikes, biggest = 0, 0
		for _, clock in CLOCKS do
			local steps, prev = {}, nil
			for i = 0, math.ceil(duration * 60) + 2 do
				local pose = sample(rig, make(i / 60, clock + i / 60))
				if prev then
					table.insert(steps, jump(rig, prev, pose))
				end
				prev = pose
			end
			for i = 2, #steps - 1 do
				local s = steps[i]
				biggest = math.max(biggest, s)
				if s > 0.05 and s > 3 * math.max(steps[i - 1], steps[i + 1]) then
					spikes += 1
				end
			end
		end
		check(
			spikes == 0,
			("%s: одиночных скачков по кадрам %d (наибольший шаг за кадр %.3f)"):format(
				label,
				spikes,
				biggest
			)
		)
	end
end

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end

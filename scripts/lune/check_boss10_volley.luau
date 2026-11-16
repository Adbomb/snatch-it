--!nocheck
-- Проверка магического залпа Короля-дракона (босс 10) без Studio: настоящий модуль игры Shared/BossVolley и числа
-- Battle.Bosses[10].Volley; цикл повторяет BattleService (фиксация, выстрел, шаг 1/60 с, отрезок против капсулы,
-- допуск Grace, одно попадание за залп, земля, дальность, препятствие). Цель — движущаяся по заданному пути.
--   1) сценарии на 20 стадах: стоит — попадание; вовремя влево и вправо — промах; поздно — касание без попадания или
--      попадание (по допуску); колонна на пути — центральный гаснет о неё;
--   2) минимальная дистанция 16 стадов: можно ли увернуться после фиксации — самое позднее начало ухода;
--   3) снаряды не доворачивают: направления после фиксации не зависят от движения цели;
--   4) один залп — не больше одного урона, даже если цель стоит на пути двух снарядов.
-- Сеть и задержку это не проверяет (нужен Studio с двумя клиентами). Ничего не пишет.
-- Запуск из корня репозитория: lune run scripts/lune/check_boss10_volley.luau

local process = require("@lune/process")

local Env = require("./env")
local Vector3 = Env.roblox.Vector3

local BossVolley = Env.Require("ReplicatedStorage.Shared.BossVolley")
local Battle = Env.Require("ReplicatedStorage.Shared.Config.Battle")
local rig = Env.Require("ReplicatedStorage.Shared.Config.Boss10DragonRig")
local cfg = Battle.Bosses[10].Volley

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

local ORIGIN = rig.VolleyOrigin -- дракон в (0, 0, 0) лицом к +Z, земля y = 0
local SPEED_PLAYER = 14 -- ст/с: Progression.Speed.min
local REACTION = 0.35 -- с после фиксации: реакция с запасом на сеть

-- Залп против цели path(t) (t — секунды от начала клипа, ступни). obstacle(dir) → расстояние до препятствия или nil.
local function volley(path, obstacle)
	local dirs, shots = nil, nil
	local hits, damage, best = {}, 0, -math.huge
	local step = cfg.Step
	local t, lastAge, prevFeet = 0, 0, nil
	while t <= cfg.Duration + 1 do
		local feet = path(t)
		if not dirs and t >= cfg.Lock then
			dirs = BossVolley.Directions(ORIGIN, feet, cfg)
		end
		if dirs and not shots and t >= cfg.Fire then
			shots = {}
			for _, side in BossVolley.Sides do
				local limit = BossVolley.Limit(ORIGIN, dirs[side], cfg, 0, obstacle and obstacle(dirs[side]))
				shots[side] = { limit = limit, alive = true }
			end
			lastAge, prevFeet = 0, feet
		end
		if shots then
			local age1 = t - cfg.Fire
			for side, shot in shots do
				if shot.alive then
					local a = BossVolley.Position(ORIGIN, dirs[side], cfg, lastAge, shot.limit)
					local b = BossVolley.Position(ORIGIN, dirs[side], cfg, age1, shot.limit)
					local overlap = BossVolley.Overlap(a, b, prevFeet, feet, cfg)
					best = math.max(best, overlap)
					if #hits < cfg.MaxHits and BossVolley.Hits(overlap, cfg) then
						shot.alive = false
						table.insert(hits, { side = side, t = t, overlap = overlap })
						damage += 1
					elseif age1 * cfg.Speed >= shot.limit then
						shot.alive = false
					end
				end
			end
			lastAge, prevFeet = age1, feet
		end
		t += step
	end
	return hits, damage, best, dirs
end

local function standing(p)
	return function()
		return p
	end
end
local function dodge(p, dir, start, distance)
	return function(t)
		if t <= start then
			return p
		end
		return p + dir * math.min((t - start) * SPEED_PLAYER, distance)
	end
end
local LEFT, RIGHT = Vector3.new(-1, 0, 0), Vector3.new(1, 0, 0) -- для бойца лицом к дракону (смотрит в −Z)
local function feetAt(d: number): Vector3
	return Vector3.new(ORIGIN.X, 0, ORIGIN.Z + d)
end
local function arrival(d: number): number
	local p = feetAt(d)
	return cfg.Fire + (BossVolley.Aim(p, cfg) - ORIGIN).Magnitude / cfg.Speed
end

-- ── 1. Сценарии на 20 стадах ───────────────────────────────────────────────────────────────────────────────
print("1. Сценарии (цель в 20 ст. от центра круга, бежит 14 ст/с)")
local D = 20
local p0 = feetAt(D)
local pocket = D * math.tan(math.rad(cfg.Spread)) / 2
local hits, dmg, best = volley(standing(p0))
check(dmg == 1 and hits[1].side == 0, ("стоит — центральный попадает (вошёл на %.2f ст.), урон 1"):format(best))
hits, dmg, best = volley(dodge(p0, LEFT, cfg.Lock + REACTION, pocket))
check(dmg == 0, ("влево через %.2f с после фиксации на %.1f ст. — промах (наибольший заход %.2f ст.)"):format(REACTION, pocket, best))
hits, dmg, best = volley(dodge(p0, RIGHT, cfg.Lock + REACTION, pocket))
check(dmg == 0, ("вправо так же — промах (наибольший заход %.2f ст.)"):format(best))
hits, dmg, best = volley(dodge(p0, LEFT, arrival(D) - 0.12, pocket))
print(("     поздно (за 0.12 с до прилёта): урон %d, наибольший заход %.2f ст. при допуске %.1f"):format(dmg, best, cfg.Grace))
check(best > 0, "поздний уход — снаряд задевает (попадание засчитывается, если заход ≥ допуска)")
hits, dmg, best = volley(standing(p0), function(dir)
	-- колонна r 1.6 на 12 ст. от круга по центральной полосе: снаряд гаснет у её края (как Spherecast на сервере)
	local c = Vector3.new(ORIGIN.X, 0, ORIGIN.Z + 12)
	local flat = Vector3.new(dir.X, 0, dir.Z)
	local along = (c - Vector3.new(ORIGIN.X, 0, ORIGIN.Z)):Dot(flat.Unit)
	local off = ((c - Vector3.new(ORIGIN.X, 0, ORIGIN.Z)) - flat.Unit * along).Magnitude
	if off > 1.6 + cfg.Radius then
		return nil
	end
	return (along - math.sqrt(math.max((1.6 + cfg.Radius) ^ 2 - off * off, 0))) / flat.Magnitude
end)
check(dmg == 0, "цель за колонной — центральный гаснет о колонну, урона нет")

-- ── 2. Минимальная дистанция ───────────────────────────────────────────────────────────────────────────────
print(("2. Минимальная дистанция %d ст.: успевает ли увернуться"):format(cfg.MinDistance))
for _, d in { cfg.MinDistance + 0.01, 20, 30 } do
	local p = feetAt(d)
	local need = d * math.tan(math.rad(cfg.Spread)) / 2
	-- самое позднее начало ухода (после фиксации), при котором урона нет — для каждой стороны
	local latest = {}
	for _, side in { { "влево", LEFT }, { "вправо", RIGHT } } do
		local lo, hi = 0, arrival(d) - cfg.Lock
		if select(2, volley(dodge(p, side[2], cfg.Lock + lo, need))) > 0 then
			latest[side[1]] = -1
		else
			for _ = 1, 20 do
				local mid = (lo + hi) / 2
				if select(2, volley(dodge(p, side[2], cfg.Lock + mid, need))) > 0 then
					hi = mid
				else
					lo = mid
				end
			end
			latest[side[1]] = lo
		end
	end
	local window = arrival(d) - cfg.Lock
	print(("     %.0f ст.: от фиксации до прилёта %.2f с, уход на %.2f ст.; начать не позже чем через %.2f с (влево) и %.2f с (вправо)"):format(d, window, need, latest["влево"], latest["вправо"]))
	check(
		latest["влево"] >= 0.45 and latest["вправо"] >= 0.45,
		("%.0f ст.: после фиксации есть ≥ 0.45 с на реакцию (человек ~0.25 с + сеть ~0.2 с)"):format(d)
	)
end

-- ── 3. Без доворота ────────────────────────────────────────────────────────────────────────────────────────
print("3. После фиксации снаряды не доворачивают")
local _, _, _, dirsStand = volley(standing(p0))
local _, _, _, dirsRun = volley(dodge(p0, LEFT, cfg.Lock + 0.05, 10)) -- сервер фиксирует на первом шаге после Lock (≤ 1/60 с)
local same = true
for _, side in BossVolley.Sides do
	same = same and (dirsStand[side] - dirsRun[side]).Magnitude < 1e-6
end
check(same, "направления фиксируются на 1.45 с и дальше не зависят от движения цели")

-- ── 4. Один урон за залп ───────────────────────────────────────────────────────────────────────────────────
print("4. Не больше одного урона за залп")
-- цель бежит поперёк всех трёх полос во время полёта: каждая полоса её задевает, урон — один
local cross = function(t)
	local start = cfg.Fire + 0.25
	local x = if t < start then -12 else -12 + (t - start) * 40
	return Vector3.new(ORIGIN.X + x, 0, ORIGIN.Z + 12)
end
hits, dmg = volley(cross)
check(dmg <= cfg.MaxHits, ("цель на пути нескольких снарядов: урон %d (не больше %d)"):format(dmg, cfg.MaxHits))

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end

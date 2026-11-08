--!nocheck
-- Проверка поимки «Ловибум» без Roblox Studio (D55): таблица шансов (100 000 бросков на клетку, ±0.5 %), покупка
-- (уровень, вид, количество, монеты, запас, NaN, дроби, переполнение), запас в профиле (Normalize), автомат мини-игры
-- (броски, промах, побег, поимка, конец, учебная), личная пауза только у этого игрока и босса, круг и попадание,
-- движение существ (Shared/CreatureMotion: одно зерно и время — одна поза, не дальше радиуса, на постаменте — без
-- сдвига, уклонение с замахом, одинаковый хэш), бросок (Shared/CatchThrow: камера поимки, жест → точка, не броски,
-- обратная задача, уклонение уводит из кольца). Запуск из корня репозитория: lune run scripts/lune/check_catch.luau.

local process = require("@lune/process")

local Env = require("./env")

local Catch = Env.Require("ReplicatedStorage.Shared.Config.Catch")
local CatchRules = Env.Require("ReplicatedStorage.Shared.CatchRules")
local CreatureMotion = Env.Require("ReplicatedStorage.Shared.CreatureMotion")
local GameConfig = Env.Require("ReplicatedStorage.Shared.Config.GameConfig")
local Vector3 = Env.roblox.Vector3

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	if not ok then
		print("  ОШИБКА " .. message)
		failed += 1
	else
		passed += 1
	end
end
local function section(name: string)
	print("· " .. name)
end

check(GameConfig.Catch == Catch, "GameConfig.Catch — Config/Catch")

-- ── Шансы ─────────────────────────────────────────────────────────────────────────────────────────────────
section("шансы после попадания (утверждённая таблица D55)")
local TABLE = {
	Common = { Boom = 0.6, Turbo = 0.9, Mega = 1 },
	Rare = { Boom = 0.35, Turbo = 0.525, Mega = 0.7 },
	Epic = { Boom = 0.3, Turbo = 0.45, Mega = 0.6 },
	Legendary = { Boom = 0.14, Turbo = 0.21, Mega = 0.28 },
	Secret = { Boom = 0.06, Turbo = 0.09, Mega = 0.12 },
}
local rng = Env.Random.new(55)
for rarity, byKind in TABLE do
	for kind, want in byKind do
		local chance = CatchRules.Chance(rarity, kind)
		check(math.abs(chance - want) < 1e-9, ("%s / %s: %.4f, ждали %.4f"):format(rarity, kind, chance, want))
		local session = CatchRules.NewSession(1, 1, 1, "u", rarity, 0, false)
		local caught, n = 0, 100000
		for _ = 1, n do
			if CatchRules.Outcome(session, true, chance, rng:NextNumber()) == "Caught" then
				caught += 1
			end
		end
		check(math.abs(caught / n - want) <= 0.005, ("%s / %s: %d из %d"):format(rarity, kind, caught, n))
	end
end
check(
	CatchRules.Chance("Mythic", "Boom") == 0 and CatchRules.Chance("Common", "Ultra") == 0,
	"неизвестное — шанс 0"
)
check(
	CatchRules.Outcome(CatchRules.NewSession(1, 1, 1, "u", "Common", 0), false, 1, 0) == "Miss",
	"промах без шанса"
)

-- ── Покупка ───────────────────────────────────────────────────────────────────────────────────────────────
section("покупка")
local prices = CatchRules.Prices(true)
check(Catch.Prices == nil, "цены не утверждены — Prices пусто")
check(CatchRules.Prices(false) == nil, "без тестового режима не продаётся")
check(prices ~= nil and prices[1].Boom == 500 and prices[10].Mega == 150000000, "тестовые цены")
local function buy(level, kind, count, coins, lov)
	return CatchRules.CheckBuy(prices, level, kind, count, coins or 1e12, lov or {})
end
check(buy(1, "Boom", 1) == 500, "1 Бум ур. 1 = 500")
check(buy(3, "Mega", 10) == 300000, "10 Мега ур. 3")
for _, bad in { 0, 11, 1.5, -1, 0 / 0, math.huge, "1", nil } do
	check(buy(bad, "Boom", 1) == nil, "уровень " .. tostring(bad))
end
for _, bad in { "Ultra", "", 1, nil } do
	check(buy(1, bad, 1) == nil, "вид " .. tostring(bad))
end
for _, bad in { 0, -1, 2.5, 100, 0 / 0, math.huge, "5", nil } do
	check(buy(1, "Boom", bad) == nil, "количество " .. tostring(bad))
end
check(buy(1, "Boom", 99) == 49500, "99 за раз можно")
local total, reason = buy(10, "Mega", 99, 1e9)
check(total == nil and reason == "Не хватает монет", "мало монет")
check(buy(1, "Boom", 5, 0 / 0) == nil, "монеты NaN")
check(buy(1, "Boom", 2, 1e12, { L1 = { Boom = 9998 } }) == nil, "запас сверх 9999")
check(buy(1, "Boom", 1, 1e12, { L1 = { Boom = 9998 } }) == 500, "до 9999 можно")
check(CatchRules.CheckBuy(nil, 1, "Boom", 1, 1e12, {}) == nil, "без цен не продаётся")

section("запас в профиле")
local lov = CatchRules.Normalize({
	L1 = { Boom = 3, Turbo = 0, Mega = -2, Ultra = 5 },
	L2 = { Boom = 2.5 },
	L11 = { Boom = 1 },
	X = 5,
	L3 = { Mega = 1e9 },
})
check(lov.L1.Boom == 3 and lov.L1.Turbo == nil and lov.L1.Mega == nil and lov.L1.Ultra == nil, "L1 почищен")
check(lov.L2 == nil and lov.L11 == nil and lov.X == nil, "мусор убран")
check(lov.L3.Mega == Catch.MaxStock, "сверх запаса — потолок")
check(
	type(CatchRules.Normalize(nil)) == "table" and type(CatchRules.Normalize(5)) == "table",
	"не таблица — пусто"
)
check(CatchRules.Stock(lov, 1, "Boom") == 3 and CatchRules.Stock(lov, 2, "Boom") == 0, "Stock")
check(CatchRules.StockOfLevel({ L4 = { Boom = 1, Mega = 2 } }, 4) == 3, "StockOfLevel")

-- ── Мини-игра ─────────────────────────────────────────────────────────────────────────────────────────────
section("автомат мини-игры")
local g = Catch.Game
local T0 = 1700000000
local s = CatchRules.NewSession(7, 2, 3, "uid", "Rare", T0, false)
check(CatchRules.CheckThrow(s, T0 + 1, "Boom", 5, T0 + 1) == nil, "первый бросок")
check(CatchRules.CheckThrow(s, T0 + 1, "Boom", 0, T0 + 1) ~= nil, "нет Ловибумов — нельзя")
check(CatchRules.CheckThrow(s, T0 + 1, "Ultra", 5, T0 + 1) ~= nil, "чужой вид")
check(
	CatchRules.CheckThrow(s, T0 + 1, "Boom", 5, T0 + 1 + g.ClockSlack + 0.1) ~= nil,
	"время из будущего"
)
check(CatchRules.CheckThrow(s, T0 + 1, "Boom", 5, 0 / 0) ~= nil, "время NaN")
check(CatchRules.CheckThrow(s, T0 + 1, "Boom", 5, "x") ~= nil, "время строкой")
CatchRules.AfterThrow(s, "Miss", T0 + 1)
check(s.state == "Aim" and s.throws == 1, "промах — дальше")
check(
	CatchRules.CheckThrow(s, T0 + 1.5, "Boom", 5, T0 + 1.5) == "Подождите",
	"броски чаще паузы"
)
CatchRules.AfterThrow(s, "Escape", T0 + 4)
check(s.state == "Aim" and s.throws == 2, "побег — дальше")
CatchRules.AfterThrow(s, "Escape", T0 + 7)
check(s.state == "Over" and s.endReason == "Throws", "три неудачи — конец")
check(CatchRules.CheckThrow(s, T0 + 20, "Boom", 5, T0 + 20) ~= nil, "четвёртого броска нет")
local s2 = CatchRules.NewSession(7, 2, 3, "uid", "Rare", T0, false)
CatchRules.AfterThrow(s2, "Caught", T0 + 2)
check(s2.state == "Caught", "поимка")
local s3 = CatchRules.NewSession(7, 2, 3, "uid", "Rare", T0, false)
check(CatchRules.ShouldEnd(s3, T0 + g.Idle + 1, 5) == "Idle", "бездействие")
check(CatchRules.ShouldEnd(s3, T0 + 5, 0) == "Empty", "кончились Ловибумы уровня")
check(CatchRules.ShouldEnd(s3, T0 + 5, 3) == nil, "идёт")
s3.lastActive = T0 + g.Watchdog
check(CatchRules.ShouldEnd(s3, T0 + g.Watchdog + 1, 3) == "Watchdog", "сторож")
local tut = CatchRules.NewSession(7, 1, 0, "tut", "Common", T0, true)
for i = 1, 6 do
	check(
		CatchRules.CheckThrow(tut, T0 + i * 3, nil, 0, T0 + i * 3) == nil,
		"учебный бросок " .. i .. " бесплатный"
	)
	CatchRules.AfterThrow(tut, "Miss", T0 + i * 3)
end
check(tut.state == "Aim", "учебная: промахи без лимита")
check(
	CatchRules.Outcome(tut, true, 0, 0.999) == "Caught",
	"учебная: первое попадание — захват"
)
check(CatchRules.ShouldEnd(tut, T0 + 20, 0) == nil, "учебная: без Ловибумов не кончается")

section("личная пауза у босса")
local pauses = {}
CatchRules.SetPause(pauses, 7, 2, T0)
check(
	math.abs(CatchRules.PauseLeft(pauses, 7, 2, T0 + 1) - (g.FailPause - 1)) < 1e-9,
	"пауза у этого босса"
)
check(CatchRules.PauseLeft(pauses, 7, 3, T0 + 1) == 0, "другой босс — сразу")
check(CatchRules.PauseLeft(pauses, 8, 2, T0 + 1) == 0, "другой игрок — сразу")
check(CatchRules.PauseLeft(pauses, 7, 2, T0 + g.FailPause + 0.01) == 0, "после 10 с — можно")
check(g.FailPause == 10 and g.MaxThrows == 3, "пауза 10 с и 3 броска (утверждено)")

section("круг и попадание")
local c = g.Circle
check(math.abs(CatchRules.CircleRadius(T0, T0, 1) - c.Max) < 1e-9, "начало — большой круг")
check(math.abs(CatchRules.CircleRadius(T0 + c.Period * 0.999, T0, 1) - c.Min) < 0.01, "конец — малый")
check(CatchRules.CircleRadius(T0 + c.Period + 0.001, T0, 1) > c.Max - 0.01, "и снова")
check(CatchRules.CircleRadius(T0, T0, 2) == 2 * c.Max, "масштаб существа")
check(
	CatchRules.IsHit(Vector3.new(1, 0, 0), Vector3.zero, 1)
		and not CatchRules.IsHit(Vector3.new(1.01, 0, 0), Vector3.zero, 1),
	"попадание по радиусу"
)

-- ── Движение существ ──────────────────────────────────────────────────────────────────────────────────────
section("движение существ")
check(
	CreatureMotion.SeedOf("abc") == CreatureMotion.SeedOf("abc")
		and CreatureMotion.SeedOf("abc") ~= CreatureMotion.SeedOf("abd"),
	"зерно из uid"
)
check(
	CreatureMotion.SeedOf("2F6D0A54-0C3B-4B2A-9C8E-1A2B3C4D5E6F") == 2657439381,
	"FNV-1a (как у эталона Python) не изменился (иначе разойдутся клиенты)"
)
check(CreatureMotion.Hash(12345, 678) == CreatureMotion.Hash(12345, 678), "хэш стабилен")
local hashes = {}
for k = 1, 2000 do
	local h = CreatureMotion.Hash(987654321, k)
	check(h >= 0 and h < 1, "хэш в [0, 1)")
	table.insert(hashes, h)
end
local mean = 0
for _, h in hashes do
	mean += h / #hashes
end
check(math.abs(mean - 0.5) < 0.03, ("хэш равномерный (среднее %.3f)"):format(mean))

local maxDist, maxCatch, maxCalm = 0, 0, 0
for i = 1, 40 do
	local seed = CreatureMotion.SeedOf("creature-" .. i)
	for _, zone in { 1, 2, 3 } do
		local p =
			{ seed = seed, radius = CreatureMotion.WanderRadius(zone), scale = 1 + (i % 3) * 0.4, mode = "Wander" }
		local prev
		for step = 0, 600 do
			local t = T0 + step * 0.05 + i
			local pose = CreatureMotion.Pose(p, t)
			local again = CreatureMotion.Pose(p, t)
			check(pose.offset == again.offset and pose.yaw == again.yaw, "одно время — одна поза")
			local flat = Vector3.new(pose.offset.X, 0, pose.offset.Z).Magnitude
			maxDist = math.max(maxDist, flat / p.radius)
			check(
				flat <= p.radius + 1e-6,
				("зона %d: %.3f за радиусом %.2f"):format(zone, flat, p.radius)
			)
			check(
				pose.offset.Y >= -1e-9 and pose.offset.Y <= Catch.Creature.HopHeight * p.scale + 1e-6,
				"прыжок в пределах"
			)
			if prev then
				check((pose.offset - prev).Magnitude < 0.6 * p.scale + p.radius * 0.2, "без телепортов")
			end
			prev = pose.offset
		end
		local cp = table.clone(p)
		cp.mode, cp.since, cp.face = "Catch", T0, 0.7
		for step = 0, 400 do
			local pose = CreatureMotion.Pose(cp, T0 + step * 0.05)
			local flat = Vector3.new(pose.offset.X, 0, pose.offset.Z).Magnitude
			maxCatch = math.max(maxCatch, flat)
			check(
				flat <= p.radius + (Catch.Creature.Sway + Catch.Creature.DodgeSide) * cp.scale + 1e-6,
				"мини-игра: недалеко"
			)
		end
		local mp = { seed = seed, radius = 0, scale = 1, mode = "Calm" }
		for step = 0, 200 do
			local pose = CreatureMotion.Pose(mp, T0 + step * 0.1)
			maxCalm = math.max(maxCalm, pose.offset.Magnitude)
		end
	end
end
check(maxCalm == 0, "на постаменте музея — без сдвига")
check(maxDist > 0.5, "существа действительно ходят")
check(maxCatch > 0.5, "в мини-игре уклоняются")

-- уклонение начинается с замаха: за DodgeWindup до рывка существо уже приседает (squash < 1) — видно заранее
local seen, warned = 0, 0
for i = 1, 60 do
	local p =
		{ seed = CreatureMotion.SeedOf("dodge-" .. i), radius = 2.4, scale = 1, mode = "Catch", since = T0, face = 0 }
	local wasDodging = false
	for step = 0, 600 do
		local t = T0 + step * 0.02
		local pose = CreatureMotion.Pose(p, t)
		local dodging = math.abs(pose.dodge) >= 0.99
		if dodging and not wasDodging then
			seen += 1
			-- бросок, который прилетел бы во время рывка (отпущен позже, чем за полёт до него), игрок делает, уже видя
			-- присед: замах заметен раньше, чем за полёт + 0.1 с до рывка
			local before = CreatureMotion.Pose(p, t - g.FlightTime - 0.1)
			if before.squash < 0.9 and math.abs(before.dodge) > 0.25 then
				warned += 1
			end
		end
		wasDodging = dodging
	end
end
check(
	seen > 20 and warned == seen,
	("присед виден до броска, который попал бы в рывок (%d из %d)"):format(
		warned,
		seen
	)
)
check(Catch.Creature.DodgeWindup >= g.FlightTime + 0.3, "замах дольше полёта")
local first = { seed = 5, radius = 2.4, scale = 1, mode = "Catch", since = T0, face = 0 }
local calmStart = true
for step = 0, math.floor(Catch.Creature.DodgeEvery / 0.05) - 1 do
	calmStart = calmStart and math.abs(CreatureMotion.Pose(first, T0 + step * 0.05).dodge) < 1e-9
end
check(calmStart, "первый цикл мини-игры без уклонения")

local fp = { seed = 9, radius = 0.45, scale = 1, mode = "Flee", since = T0, face = 0, drop = 2.5 }
local far = CreatureMotion.Pose(fp, T0 + g.FleeTime * 0.4)
check(
	far.offset.Magnitude > g.FleeDistance * 0.9 and math.abs(far.offset.Y + 2.5) < 1e-6,
	"побег: спрыгнул и отбежал"
)
local after = T0 + g.FleeTime + g.Blend + 0.01
local home = CreatureMotion.Pose(fp, after)
local wander = CreatureMotion.Pose({ seed = 9, radius = 0.45, scale = 1, mode = "Wander" }, after)
check(home.offset == wander.offset, "после побега — снова блуждает")

-- без скачков на сменах режима: блуждание → мини-игра → побег → блуждание
for i = 1, 30 do
	local base = { seed = CreatureMotion.SeedOf("modes-" .. i), radius = 2.4, scale = 1.2, drop = 0 }
	local catchAt, fleeAt = T0 + 7.3 + i * 0.37, T0 + 19.1 + i * 0.37
	local function at(t)
		local q = table.clone(base)
		if t < catchAt then
			q.mode = "Wander"
		elseif t < fleeAt then
			q.mode, q.since, q.face = "Catch", catchAt, 0.4
		else
			q.mode, q.since, q.anchor, q.face = "Flee", fleeAt, catchAt, 0.4
		end
		return CreatureMotion.Pose(q, t)
	end
	local worst = 0
	for _, edge in { catchAt, fleeAt, fleeAt + g.FleeTime, fleeAt + g.FleeTime + g.Blend } do
		worst = math.max(worst, (at(edge - 1 / 60).offset - at(edge + 1 / 60).offset).Magnitude)
	end
	check(worst < 0.35, ("смена режима без телепорта (%.2f ст.)"):format(worst))
end

section("тайминг бросков")
local ts = CatchRules.NewSession(1, 1, 1, "u", "Common", T0, false)
check(
	CatchRules.CheckThrow(ts, T0 + 1, "Boom", 3, T0 + 1 + g.ClockAhead + 0.01) ~= nil,
	"время из будущего — нет"
)
check(
	CatchRules.CheckThrow(ts, T0 + 1, "Boom", 3, T0 + 1 - g.ClockSlack - 0.01) ~= nil,
	"слишком старое — нет"
)
CatchRules.AfterThrow(ts, "Escape", T0 + 1)
local ready = T0 + 1 + g.FlightTime + g.CaptureTime + g.EscapeRest
check(
	CatchRules.CheckThrow(ts, ready - 0.05, "Boom", 3, ready - 0.05) == "Подождите",
	"до конца сети — нельзя"
)
check(CatchRules.CheckThrow(ts, ready + 0.01, "Boom", 3, ready + 0.01) == nil, "после сети — можно")
check(
	CatchRules.ShouldEnd(ts, ready - 0.1, 0) == nil and CatchRules.ShouldEnd(ts, ready + 0.01, 0) == "Empty",
	"«кончились» — после показа побега"
)
CatchRules.AfterThrow(ts, "Miss", ready + 0.01)
local again = ready + 0.01 + g.FlightTime + g.MissRest
check(
	CatchRules.CheckThrow(ts, ready + 0.5, "Boom", 3, ready + 0.5) == "Подождите",
	"после промаха — короткая пауза"
)
check(CatchRules.CheckThrow(ts, again + 0.01, "Boom", 3, again + 0.01) == nil, "потом можно")

-- ── Бросок: жест → точка (сервер считает сам) ─────────────────────────────────────────────────────────────
section("бросок: камера поимки, жест, точка прилёта, уклонение")
local CatchThrow = Env.Require("ReplicatedStorage.Shared.CatchThrow")
local CFrame = Env.roblox.CFrame
local TH, CAM, GM = Catch.Throw, Catch.Game.Camera, Catch.Game
local home = CFrame.new(10, 2, -30) * CFrame.Angles(0, 0.7, 0)
local params = {
	seed = CreatureMotion.SeedOf("бросок"),
	radius = 0.45,
	scale = 1,
	mode = "Catch",
	since = 100,
	face = 0.4,
}
local height = 2
local cam, stage = CatchThrow.Frame(home, params, height)
check(
	(cam.LookVector - (stage - cam.Position).Unit).Magnitude < 1e-4,
	"камера смотрит в центр места"
)
local toward = home:VectorToWorldSpace(CFrame.Angles(0, 0.4, 0).LookVector)
local flatCam = Vector3.new(cam.Position.X - stage.X, 0, cam.Position.Z - stage.Z)
check(
	flatCam.Unit:Dot(Vector3.new(toward.X, 0, toward.Z).Unit) > 0.999,
	"камера — со стороны ловящего"
)
check(
	flatCam.Magnitude >= CAM.Min - 1e-6 and flatCam.Magnitude <= CAM.Max + 1e-6,
	"расстояние камеры в пределах"
)
check(cam.Position.Y > stage.Y, "камера чуть выше существа")
local cam2, stage2 = CatchThrow.Frame(home, params, height)
check(
	(cam2.Position - cam.Position).Magnitude < 1e-9 and stage2 == stage,
	"одни данные — одна камера"
)
local base = CreatureMotion.CatchBase(params)
local start = CreatureMotion.Pose(params, params.since)
check(
	math.abs(base.X - start.offset.X) < 1e-9 and math.abs(base.Z - start.offset.Z) < 1e-9,
	"место — где стояло"
)

local function aimOf(g)
	local parsed = CatchThrow.Parse(g)
	return parsed and CatchThrow.Aim(cam, stage, parsed)
end
local plane = Vector3.new(cam.LookVector.X, 0, cam.LookVector.Z).Unit
local straight = aimOf({ dx = 0, dy = -1, speed = TH.Ideal, length = 0.3 })
check(
	straight ~= nil and (straight - stage).Magnitude < 1e-3,
	"прямо вверх с идеальной скоростью — в центр"
)
local right = aimOf({ dx = 0.3, dy = -1, speed = TH.Ideal, length = 0.3 })
local left = aimOf({ dx = -0.3, dy = -1, speed = TH.Ideal, length = 0.3 })
check(
	(right - stage):Dot(cam.RightVector) > 0.2 and (left - stage):Dot(cam.RightVector) < -0.2,
	"вбок — в ту сторону"
)
local slow = aimOf({ dx = 0, dy = -1, speed = TH.Ideal / 2, length = 0.3 })
local fast = aimOf({ dx = 0, dy = -1, speed = TH.Ideal * 2, length = 0.3 })
check(
	slow.Y < stage.Y - 0.3 and fast.Y > stage.Y + 0.3,
	"медленнее — недолёт ниже, быстрее — перелёт выше"
)
local long = aimOf({ dx = 0, dy = -1, speed = TH.Ideal, length = 1.5 })
check(
	(long - straight).Magnitude < 1e-9,
	"длина жеста силу не меняет — только скорость"
)
for _, a in { straight, right, left, slow, fast } do
	check(math.abs((a - stage):Dot(plane)) < 1e-3, "точка — на плоскости через место")
end
local huge = CatchThrow.Parse({ dx = 0, dy = -1, speed = 1e6, length = 0.3 })
check(huge ~= nil and huge.speed == TH.MaxSpeed, "быстрее MaxSpeed — как MaxSpeed")
local far = CatchThrow.Aim(cam, stage, huge)
check(
	(far - stage).Magnitude < CAM.Max * 1.2,
	"даже предельный жест — недалеко от места"
)
local NOT_THROWS = {
	{ { dx = 0, dy = -1, speed = 3, length = TH.MinSwipe * 0.5 }, "short", "короткий" },
	{ { dx = 0, dy = -1, speed = TH.MinSpeed * 0.5, length = 0.3 }, "slow", "медленный" },
	{ { dx = 1, dy = -0.2, speed = 3, length = 0.3 }, "side", "вбок" },
	{ { dx = 0, dy = 1, speed = 3, length = 0.3 }, "side", "вниз" },
	{ { dx = 0 / 0, dy = -1, speed = 3, length = 0.3 }, "bad", "NaN" },
	{ { dx = 0, dy = -1, speed = math.huge, length = 0.3 }, "bad", "бесконечная скорость" },
	{ { dx = 0, dy = -1, speed = 3, length = 50 }, "bad", "длина 50 экранов" },
	{ { dx = 0, dy = 0, speed = 3, length = 0.3 }, "bad", "без направления" },
	{ { dx = "0", dy = -1, speed = 3, length = 0.3 }, "bad", "строка" },
	{ "жест", "bad", "не таблица" },
	{ Vector3.new(1, 2, 3), "bad", "старый формат — точка прицела" },
}
for _, case in NOT_THROWS do
	local g, why = CatchThrow.Parse(case[1])
	check(g == nil and why == case[2], ("не бросок: %s (%s)"):format(case[3], tostring(why)))
end
for _, target in
	{
		stage,
		stage + cam.RightVector * 0.8,
		stage + Vector3.new(0, 0.6, 0),
		stage - cam.RightVector * 0.5 - Vector3.new(0, 0.4, 0),
	}
do
	local g = CatchThrow.GestureFor(cam, target)
	check(g ~= nil and (CatchThrow.Aim(cam, stage, g) - target).Magnitude < 1e-3, "GestureFor → та же точка")
end
local origin = CatchThrow.Origin(cam, 2)
local rel = cam:PointToObjectSpace(origin)
check(
	rel.Z < 0 and rel.Y < 0 and math.abs(rel.X) < 1e-4,
	"Ловибум — внизу по центру перед камерой"
)
-- попадание — по положению существа в момент прилёта: в рывке уклонения бросок в место — мимо
local missDodge, hitCalm = false, false
for i = 0, 600 do
	local t = params.since + 0.5 + i * 0.05
	local arrival = t + GM.FlightTime
	local pose = CreatureMotion.Pose(params, arrival)
	local center = CreatureMotion.Center(home, pose, height)
	local hit = CatchRules.IsHit(straight, center, CatchRules.CircleRadius(arrival, params.since, params.scale))
	if math.abs(pose.dodge) >= 0.99 and not hit then
		missDodge = true
	end
	if math.abs(pose.dodge) < 0.05 and hit then
		hitCalm = true
	end
end
check(missDodge, "в рывке уклонения бросок в место — мимо")
check(hitCalm, "без уклонения бросок в место — в кольце")

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
process.exit(if failed == 0 then 0 else 1)

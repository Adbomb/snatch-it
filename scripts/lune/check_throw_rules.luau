--!nocheck
-- Проверка правил «броска вдаль» (D75) без Roblox Studio: отметки зон (сила босса N гарантирует зону N), потолок по
-- уровню Ловибума, глубина и удача, шкала точности на времени сервера (задержка с потолком, подделка момента), шансы
-- редкости существа и этажа (без удачи — D37 и D74, с удачей — сдвиг вверх), «1 из N», доход с калибровкой зоны, доход
-- босса, продажа, запрет одинаковых этажей и фильтр авто-продажи, защита от мусора на входе.
-- Запуск из корня репозитория: lune run scripts/lune/check_throw_rules.luau.

local process = require("@lune/process")

local Env = require("./env")

local FloorRarity = Env.Require("ReplicatedStorage.Shared.Config.FloorRarity")
local Progression = Env.Require("ReplicatedStorage.Shared.Config.Progression")
local Rarities = Env.Require("ReplicatedStorage.Shared.Config.Rarities")
local Throw = Env.Require("ReplicatedStorage.Shared.Config.Throw")
local FloorRules = Env.Require("ReplicatedStorage.Shared.FloorRules")
local ThrowRules = Env.Require("ReplicatedStorage.Shared.ThrowRules")

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	if not ok then
		print("  ОШИБКА " .. message)
		failed += 1
	else
		passed += 1
	end
end
local function near(a: number, b: number, eps: number): boolean
	return math.abs(a - b) <= eps
end
local NAN = 0 / 0

print("· трасса")
local marks = { 0, 34, 58, 197, 413, 758, 1316, 2698, 5351, 8651 } -- docs/D75_PLAN.md
for zone = 1, 10 do
	check(
		near(ThrowRules.Mark(zone), marks[zone], 1),
		("отметка зоны %d: %.1f"):format(zone, ThrowRules.Mark(zone))
	)
	check(ThrowRules.Mark(zone + 1) > ThrowRules.Mark(zone), ("отметки растут: зона %d"):format(zone))
end
check(
	ThrowRules.Mark(11) == Throw.EndMark and Throw.EndMark > ThrowRules.Mark(10),
	"конец трассы дальше зоны 10"
)
check(ThrowRules.Zones == 10, "зон 10")
for zone = 2, 10 do
	local s = Progression.Bosses[zone]
	local z = ThrowRules.Landing(ThrowRules.Distance(s, 0, "Boom", 10))
	check(
		z == zone,
		("сила босса %d гарантирует зону %d при худшем нажатии (вышла %d)"):format(
			zone,
			zone,
			z
		)
	)
	local below = ThrowRules.Landing(ThrowRules.Distance(s * 0.3, 1, "Mega", 10))
	check(
		below == zone - 1,
		("сила в 0.3 порога зоны %d: и лучший бросок не долетает (%d)"):format(
			zone,
			below
		)
	)
end
check(ThrowRules.Landing(ThrowRules.Distance(0, 0, "Boom", 10)) == 1, "новичок — зона 1")
-- лучший бросок: +18 % × Мега = ×1.32 дальности
check(
	near(ThrowRules.Distance(1e6, 1, "Mega", 10) / ThrowRules.Distance(1e6, 0, "Boom", 10), 1.18 * 1.12, 1e-9),
	"×1.32"
)
check(
	near(ThrowRules.Distance(1e6, 1, "Turbo", 10) / ThrowRules.Distance(1e6, 1, "Boom", 10), 1.06, 1e-9),
	"Турбо +6 %"
)

print("· потолок по уровню Ловибума")
for level = 1, 10 do
	local d = ThrowRules.Distance(1e15, 1, "Mega", level)
	local zone, depth = ThrowRules.Landing(d, level)
	check(
		d == ThrowRules.Mark(level + 1),
		("уровень %d не летит дальше конца своей зоны"):format(level)
	)
	check(
		zone == level and depth == 1,
		("уровень %d: упёрся в конец своей зоны — зона %d, глубина 1"):format(
			level,
			level
		)
	)
end
check(
	ThrowRules.Landing(ThrowRules.Mark(5), 9) == 5,
	"уровень выше зоны приземления зону не меняет"
)
check(
	ThrowRules.Landing(ThrowRules.Mark(5), NAN) == 5,
	"мусор вместо уровня в Landing — без потолка"
)
check(
	ThrowRules.Distance(1e15, 1, "Mega", 10) == Throw.EndMark,
	"самый дальний бросок — конец трассы"
)
check(
	ThrowRules.Distance(1e6, 0.5, "Boom", 99) == ThrowRules.Distance(1e6, 0.5, "Boom", 10),
	"уровень выше 10 — как 10"
)
check(
	ThrowRules.Distance(1e6, 0.5, "Boom", NAN) <= ThrowRules.Mark(2),
	"мусор вместо уровня — уровень 1"
)
check(
	ThrowRules.Distance(NAN, 0.5, "Boom", 10) == ThrowRules.Distance(0, 0.5, "Boom", 10),
	"мусор вместо силы — 0"
)
check(
	ThrowRules.Distance(1e6, 5, "Нет", 10) == ThrowRules.Distance(1e6, 1, "Boom", 10),
	"точность > 1 и чужой вид"
)

print("· глубина, удача и подсказка магазина")
do
	local a, b = ThrowRules.Mark(5), ThrowRules.Mark(6)
	local z0, f0 = ThrowRules.Landing(a)
	local z1, f1 = ThrowRules.Landing((a + b) / 2)
	local z2, f2 = ThrowRules.Landing(b - 1e-6)
	check(z0 == 5 and f0 == 0, "начало зоны — глубина 0")
	check(z1 == 5 and near(f1, 0.5, 1e-9), "середина зоны — глубина 0.5")
	check(z2 == 5 and f2 > 0.999, "у конца зоны — глубина почти 1")
	local zn, fn = ThrowRules.Landing(NAN)
	check(zn == 1 and fn == 0, "мусор вместо дальности — начало трассы")
	local ze, fe = ThrowRules.Landing(1e9)
	check(ze == 10 and fe == 1, "дальше конца трассы — конец зоны 10")
end
check(
	ThrowRules.Luck(0) == 1 and ThrowRules.Luck(1) == 2 and near(ThrowRules.Luck(0.5), 1.5, 1e-9),
	"удача: ×1 … ×2"
)
check(
	ThrowRules.Luck(NAN) == 1 and ThrowRules.Luck(7) == 2 and ThrowRules.Luck(-3) == 1,
	"мусор и глубина вне 0…1"
)
check(
	ThrowRules.SuggestLevel(0) == 1 and ThrowRules.SuggestLevel(139) == 1,
	"подсказка: до порога — уровень 1"
)
check(
	ThrowRules.SuggestLevel(140) == 2 and ThrowRules.SuggestLevel(5.6e11) == 10,
	"подсказка: с порога — зона"
)

print("· шкала точности")
local P = Throw.Scale.Period
check(
	ThrowRules.ScalePosition(0, P) == 0 and near(ThrowRules.ScalePosition(P / 2, P), 1, 1e-9),
	"маркер: 0 → 1 за полпериода"
)
check(
	near(ThrowRules.ScalePosition(P / 4, P), 0.5, 1e-9) and near(ThrowRules.ScalePosition(P * 0.75, P), 0.5, 1e-9),
	"середина — дважды за период"
)
check(near(ThrowRules.ScalePosition(P * 7.25, P), 0.5, 1e-9), "маркер ходит по кругу")
check(near(ThrowRules.ScalePosition(0, P, 0.25), 0.5, 1e-9), "своё начало у каждого броска")
check(
	ThrowRules.ScalePosition(NAN, P) == 0 and ThrowRules.ScalePosition(1, 0) == 0,
	"мусор вместо времени и периода"
)
check(
	ThrowRules.Quality(1) == 1 and ThrowRules.Quality(1 - Throw.Scale.Perfect) == 1,
	"зона «идеально» — у верха шкалы"
)
check(ThrowRules.Quality(0) == 0 and ThrowRules.Quality(-1) == 0, "низ шкалы — 0")
check(ThrowRules.Quality(0.8) > ThrowRules.Quality(0.2) and ThrowRules.Quality(2) == 1, "выше — лучше")
check(
	ThrowRules.Quality(0.3) > ThrowRules.Quality(0.2) and ThrowRules.Quality(NAN) == 0,
	"к верху — лучше; мусор — 0"
)
check(
	ThrowRules.AccuracyMult(0) == 1 and near(ThrowRules.AccuracyMult(1), 1.18, 1e-9),
	"точность: ×1 … ×1.18"
)
check(
	near(ThrowRules.AccuracyMult(99), 1.18, 1e-9) and ThrowRules.AccuracyMult(NAN) == 1,
	"подделка качества — не больше идеала"
)
-- момент нажатия: задержка с потолком, будущее и мусор — «сейчас»
local now = 1000
check(
	ThrowRules.PressTime(now, now - 0.1) == now - 0.1,
	"нажатие 100 мс назад — принято как есть"
)
check(
	ThrowRules.PressTime(now, now - 5) == now - Throw.Scale.LagCap,
	"нажатие «5 с назад» — не раньше потолка задержки"
)
check(ThrowRules.PressTime(now, now + 3) == now, "нажатие «из будущего» — сейчас")
check(
	ThrowRules.PressTime(now, NAN) == now and ThrowRules.PressTime(now, "x") == now,
	"мусор вместо момента — сейчас"
)
do -- любой заявленный момент даёт точность не выше идеальной
	local best = 0
	for i = -200, 200 do
		local t = ThrowRules.PressTime(now, now + i / 50)
		best = math.max(best, ThrowRules.AccuracyMult(ThrowRules.Quality(ThrowRules.ScalePosition(t - 990, P, 0.3))))
	end
	check(
		best <= 1.18 + 1e-9,
		"подделка момента — не больше обычного идеального попадания"
	)
end

print("· шансы редкости существа и этажа")
local tiers = Progression.BossLoot.Tiers
for zone = 1, 10 do
	local tier
	for _, tr in tiers do
		if zone >= tr.from and zone <= tr.to then
			tier = tr.chances
		end
	end
	local w = ThrowRules.CreatureWeights(zone, 1)
	local sum, same = 0, true
	for i, rarity in Rarities.Order do
		sum += w[i]
		same = same and near(w[i] * 100, tier[rarity], 1e-6)
	end
	check(near(sum, 1, 1e-9) and same, ("зона %d без удачи — шансы D37"):format(zone))
	local lucky = ThrowRules.CreatureWeights(zone, 2, "Mega")
	check(lucky[1] < w[1], ("зона %d: с удачей и Мегой Common реже"):format(zone))
	for i, rarity in Rarities.Order do
		check(
			(tier[rarity] == 0) == (lucky[i] == 0),
			("зона %d: удача и охота не открывают редкость %s"):format(zone, rarity)
		)
	end
end
for _, rarity in Rarities.Order do
	local a, b = ThrowRules.FloorWeights(rarity, 1), FloorRules.Weights(rarity)
	local same, sum = true, 0
	for i in FloorRarity.Order do
		same = same and near(a[i], b[i], 1e-12)
		sum += a[i]
	end
	check(same and near(sum, 1, 1e-9), ("этаж без удачи = D74 (%s)"):format(rarity))
	local lucky = ThrowRules.FloorWeights(rarity, 2)
	check(
		lucky[6] > a[6] * 2 and lucky[1] < a[1],
		("удача ×2 поднимает Алмазный (%s)"):format(rarity)
	)
end
check(
	near(ThrowRules.FloorWeights("Common", 2)[6] * 100, 0.43, 0.01),
	"Алмазный при удаче ×2 — 0.43 % (report_d75)"
)
check(
	ThrowRules.CreatureWeights(5, 0.2)[1] == ThrowRules.CreatureWeights(5, 1)[1],
	"удача меньше 1 не бывает"
)
check(
	ThrowRules.CreatureWeights(5, NAN)[1] == ThrowRules.CreatureWeights(5, 1)[1],
	"мусор вместо удачи — ×1"
)

print("· охота: Бум — фарм, Турбо и Мега поднимают верхние редкости")
do
	local c1, f1 = ThrowRules.Hunt("Boom")
	local c2, f2 = ThrowRules.Hunt("Turbo")
	local c3, f3 = ThrowRules.Hunt("Mega")
	local c0, f0 = ThrowRules.Hunt("Нет")
	check(c1 == 1 and f1 == 1, "Бум без охоты")
	check(c0 == 1 and f0 == 1, "чужой вид — как Бум")
	check(
		c3 > c2 and c2 > 1 and f3 > f2 and f2 > 1,
		"Мега сильнее Турбо, Турбо сильнее Бума"
	)
	local boom, mega = ThrowRules.CreatureWeights(5, 1.5, "Boom"), ThrowRules.CreatureWeights(5, 1.5, "Mega")
	check(near(mega[4] / boom[4], c3 / (1 + boom[4] * (c3 - 1)), 1e-9), "Legendary у Меги: вес × охота")
	check(
		mega[1] < boom[1] and near(mega[2] / mega[1], boom[2] / boom[1], 1e-9),
		"нижние редкости между собой — как были"
	)
	local plain = ThrowRules.CreatureWeights(2, 1.5)
	check(
		near(ThrowRules.CreatureWeights(2, 1.5, "Mega")[1], plain[1], 1e-12),
		"в зоне без Legendary охота существ не меняет"
	)
	local fb, fm = ThrowRules.FloorWeights("Common", 1, "Boom"), ThrowRules.FloorWeights("Common", 1, "Mega")
	check(
		fm[6] > fb[6] * 3 and fm[5] > fb[5] * 3,
		"Мифический и Алмазный у Меги — больше чем втрое чаще"
	)
	check(
		near(fm[2] / fm[1], fb[2] / fb[1], 1e-9),
		"нижние редкости этажа между собой — как были"
	)
	-- роли за монету (Турбо = 2 Бума, Мега = 3): доход чуть хуже, редкий этаж — лучше (зона 5, середина зоны)
	local base = { 1115, 3615, 14784, 44352, 0 } -- Progression.CreatureIncome.ByBoss[5]
	local function value(kind: string): (number, number)
		local income, diamond = 0, 0
		local cw = ThrowRules.CreatureWeights(5, 1.5, kind)
		for i, rarity in Rarities.Order do
			local fw = ThrowRules.FloorWeights(rarity, 1.5, kind)
			local mult = 0
			for k, key in FloorRarity.Order do
				mult += fw[k] * FloorRarity.Mult[key]
			end
			income += cw[i] * base[i] / FloorRules.ExpectedMult(rarity) * mult
			diamond += cw[i] * fw[6]
		end
		return income, diamond
	end
	local ib, db = value("Boom")
	local it, dt = value("Turbo")
	local im, dm = value("Mega")
	check(
		it / 2 < ib and im / 3 < it / 2,
		"доход за монету: Бум лучше Турбо, Турбо лучше Меги"
	)
	check(
		im / 3 > ib * 0.6,
		"Мега по доходу за монету не хуже 0.6 от Бума (без учёта дальности)"
	)
	check(
		dt / 2 > db * 1.15 and dm / 3 > db * 1.15,
		"Алмазный за монету: и Турбо, и Мега лучше Бума (без учёта дальности)"
	)
end

print("· броски по случайным числам")
check(ThrowRules.RollCreature(1, 1, nil, 0) == "Common", "зона 1: с нуля — Common")
check(
	ThrowRules.RollCreature(1, 1, nil, 0.6999) == "Common" and ThrowRules.RollCreature(1, 1, nil, 0.7) == "Rare",
	"зона 1: Common до 70 %"
)
check(ThrowRules.RollCreature(1, 1, nil, 0.96) == "Epic", "зона 1: Epic")
check(
	ThrowRules.RollCreature(1, 1, "Mega", 0.999999) == "Epic",
	"зона 1: Легендарных нет даже на краю и с Мегой"
)
check(
	ThrowRules.RollCreature(1, 2, nil, 1) == "Epic" and ThrowRules.RollCreature(1, 1, nil, NAN) == "Common",
	"roll = 1 и мусор"
)
check(ThrowRules.RollCreature(9, 1, nil, 0.999) == "Secret", "зона 9: Secret на краю")
check(ThrowRules.RollFloor("Common", 1, nil, 0.9995) == "Diamond", "этаж: Алмазный на краю")
check(ThrowRules.RollFloor("Common", 1, nil, 0) == "Wood", "этаж: с нуля — Деревянный")
check(
	ThrowRules.RollFloor("Common", 1, nil, 0.9985) == "Mythic",
	"этаж: Мифический перед Алмазным"
)
check(ThrowRules.RollFloor("Common", 2, nil, 0.9985) == "Diamond", "удача двигает границу")
check(ThrowRules.RollFloor("Common", 1, "Mega", 0.9975) == "Diamond", "охота двигает границу")
do
	local counts, n = {}, 200000
	math.randomseed(12345)
	local rnd = math.random
	for _ = 1, n do
		local r = ThrowRules.RollCreature(5, 1.5, "Turbo", rnd())
		counts[r] = (counts[r] or 0) + 1
	end
	local w = ThrowRules.CreatureWeights(5, 1.5, "Turbo")
	local ok = true
	for i, rarity in Rarities.Order do
		ok = ok and near((counts[rarity] or 0) / n, w[i], 0.004)
	end
	check(ok, "200 000 бросков сходятся с шансами")
	local bosses = 0
	for _ = 1, n do
		if ThrowRules.IsBoss(rnd()) then
			bosses += 1
		end
	end
	check(bosses > 40 and bosses < 130, ("босс 1 из 2 500: %d на 200 000"):format(bosses))
end
check(ThrowRules.IsBoss(0) and not ThrowRules.IsBoss(Throw.BossChance), "босс: граница шанса")
check(not ThrowRules.IsBoss(NAN) and not ThrowRules.IsBoss(-1), "босс: мусор")

print("· «1 из N»")
check(near(ThrowRules.Chance(5, 1, nil, "Legendary"), 0.05, 1e-9), "Legendary в зоне 5 — 5 %")
check(
	near(ThrowRules.Chance(5, 1, "Boom", "Common", "Diamond"), 0.52 * 0.001, 1e-9),
	"Common на Алмазном — 0.052 %"
)
check(ThrowRules.OneIn(ThrowRules.Chance(5, 1, nil, "Common", "Diamond")) == 1923, "1 из 1 923")
check(
	ThrowRules.Chance(1, 1, "Mega", "Secret") == 0 and ThrowRules.OneIn(0) == math.huge,
	"закрытая редкость — шанса нет"
)
check(
	ThrowRules.Chance(5, 1, nil, "Нет") == 0 and ThrowRules.Chance(5, 1, nil, "Common", "Нет") == 0,
	"чужие ключи"
)
check(
	ThrowRules.OneIn(1) == 1 and ThrowRules.OneIn(Throw.BossChance) == 2500 and ThrowRules.OneIn(NAN) == math.huge,
	"OneIn"
)
do
	local sum = 0
	for _, rarity in Rarities.Order do
		for _, floor in FloorRarity.Order do
			sum += ThrowRules.Chance(8, 1.7, "Mega", rarity, floor)
		end
	end
	check(near(sum, 1, 1e-9), "шансы всех сочетаний в сумме 100 %")
end

print("· доход, босс, продажа")
check(#Throw.IncomeK == 10, "калибровка дохода — на 10 зон")
for zone = 1, 10 do
	local k = Throw.IncomeK[zone]
	check(k > 0 and k <= 1.2, ("IncomeK зоны %d в пределах"):format(zone))
	check(
		near(ThrowRules.Income(1000, "Rare", "Gold", zone), FloorRules.Income(1000, "Rare", "Gold") * k, 1e-9),
		("доход = D74 × калибровка зоны %d"):format(zone)
	)
	if zone > 1 then
		-- следующая зона выгоднее прошлой: каталог растёт в Growth раз за зону
		local growth = Progression.CreatureIncome.Growth
		check(k * growth > Throw.IncomeK[zone - 1], ("зона %d выгоднее зоны %d"):format(zone, zone - 1))
		check(
			ThrowRules.BossIncome(zone) > ThrowRules.BossIncome(zone - 1),
			("босс зоны %d доходнее прошлого"):format(zone)
		)
	end
end
check(
	ThrowRules.Income(1000, "Rare", "Gold", 99) == FloorRules.Income(1000, "Rare", "Gold"),
	"чужая зона — без калибровки"
)
check(near(ThrowRules.LegendaryBase(4), 13860, 1e-6), "Легендарное зоны 4 — из D56")
check(
	ThrowRules.LegendaryBase(1) > 0 and ThrowRules.LegendaryBase(3) > ThrowRules.LegendaryBase(2),
	"зоны 1–3: 3 × Эпическое"
)
check(
	near(ThrowRules.BossIncome(4), 13860 / FloorRules.ExpectedMult("Legendary") * 8 * Throw.IncomeK[4], 1e-6),
	"босс = Легендарное на Золотом этаже своей зоны"
)
check(
	ThrowRules.SellPrice(100) == 100 * Throw.SellSeconds and ThrowRules.SellPrice(0) == 1,
	"продажа: секунды дохода, не меньше 1"
)
check(ThrowRules.SellPrice(NAN) == 1 and ThrowRules.SellPrice(-5) == 1, "продажа: мусор")

print("· одинаковые этажи и авто-продажа")
check(
	ThrowRules.SameFloor("PizzaRat", "Gold", "PizzaRat", "Gold"),
	"то же существо и та же редкость — одинаковые"
)
check(
	not ThrowRules.SameFloor("PizzaRat", "Gold", "PizzaRat", "Wood"),
	"та же крыса на другом этаже — можно"
)
check(not ThrowRules.SameFloor("PizzaRat", "Gold", "YetiCub", "Gold"), "другое существо — можно")
check(ThrowRules.SameFloor("PizzaRat", nil, "PizzaRat", "Wood"), "пустая редкость = Деревянный")
local tower = { { itemId = "PizzaRat", floor = "Gold" }, { itemId = "YetiCub", floor = nil } }
check(
	ThrowRules.HasFloor(tower, "PizzaRat", "Gold") and ThrowRules.HasFloor(tower, "YetiCub", "Wood"),
	"повтор найден"
)
check(
	not ThrowRules.HasFloor(tower, "PizzaRat", "Diamond") and not ThrowRules.HasFloor({}, "PizzaRat", "Gold"),
	"не повтор"
)
do -- одного существа — до 6 этажей, по одному на редкость
	local list, placed = {}, 0
	for _ = 1, 3 do
		for _, floor in FloorRarity.Order do
			if not ThrowRules.HasFloor(list, "PizzaRat", floor) then
				table.insert(list, { itemId = "PizzaRat", floor = floor })
				placed += 1
			end
		end
	end
	check(placed == 6, "одного существа — не больше 6 этажей")
end
local filter = { creature = "Rare", floor = "Stone", duplicates = true }
check(
	ThrowRules.AutoSell(filter, "Common", "Wood", false) and ThrowRules.AutoSell(filter, "Rare", "Stone", false),
	"фильтр: не выше порога — продать"
)
check(
	not ThrowRules.AutoSell(filter, "Epic", "Wood", false),
	"фильтр: существо выше порога — оставить"
)
check(
	not ThrowRules.AutoSell(filter, "Common", "Marble", false),
	"фильтр: этаж выше порога — оставить"
)
check(
	ThrowRules.AutoSell(filter, "Secret", "Diamond", true),
	"повтор «Уже есть» продаётся, если включено"
)
check(
	not ThrowRules.AutoSell({ duplicates = false }, "Secret", "Diamond", true),
	"повтор не продаётся, если выключено"
)
check(
	not ThrowRules.AutoSell(nil, "Common", "Wood", true) and not ThrowRules.AutoSell({}, "Common", "Wood", false),
	"без фильтра — ничего"
)
check(
	not ThrowRules.AutoSell({ creature = "Нет", floor = "Wood" }, "Common", "Wood", false),
	"чужой ключ в фильтре — ничего"
)
check(
	ThrowRules.AutoSell({ creature = "Common", floor = "Wood" }, "Common", nil, false),
	"пустая редкость этажа = Деревянный"
)

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
process.exit(if failed == 0 then 0 else 1)

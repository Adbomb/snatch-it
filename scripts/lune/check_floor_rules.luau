--!nocheck
-- Проверка правил редкости этажа без Roblox Studio (D74): шансы в сумме 100 %, веса со сдвигом от редкости существа
-- (числа из пересчёта экономики report_d74), бросок по границам и на 200 000 случайных числах, нормировка дохода
-- (матожидание дохода с поимки = доход существа), множитель удержания по силе, защита от мусора на входе.
-- Запуск из корня репозитория: lune run scripts/lune/check_floor_rules.luau.

local process = require("@lune/process")

local Env = require("./env")

local FloorRarity = Env.Require("ReplicatedStorage.Shared.Config.FloorRarity")
local FloorRules = Env.Require("ReplicatedStorage.Shared.FloorRules")

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

print("· таблицы")
local sum = 0
for _, key in FloorRarity.Order do
	sum += FloorRarity.Chance[key]
	check(
		FloorRarity.Mult[key] ~= nil and FloorRarity.Names[key] ~= nil,
		"у ступени " .. key .. " есть множитель и имя"
	)
end
check(near(sum, 100, 1e-9), "шансы в сумме 100 %")
check(
	#FloorRarity.Order == 6 and FloorRarity.Order[1] == FloorRarity.Default,
	"6 ступеней, первая — по умолчанию"
)

print("· веса и средний множитель")
local expected = { Common = 2.060, Rare = 2.391, Epic = 2.779, Legendary = 3.384, Secret = 4.467 }
for rarity, value in expected do
	local w = FloorRules.Weights(rarity)
	local total = 0
	for _, x in w do
		total += x
	end
	check(near(total, 1, 1e-9), "веса " .. rarity .. " в сумме 1")
	check(
		near(FloorRules.ExpectedMult(rarity), value, 0.001),
		"средний множитель " .. rarity .. " = " .. value
	)
end
check(near(FloorRules.Weights("Common")[1], 0.6, 1e-9), "Common без сдвига: Деревянный 60 %")
check(near(FloorRules.Chance("Legendary", "Cosmic"), 0.0055, 0.0001), "Legendary: Космический 0.55 %")
check(near(FloorRules.Chance("Secret", "Cosmic"), 0.0110, 0.0001), "Secret: Космический 1.10 %")
check(
	near(FloorRules.ExpectedMult(nil), 2.060, 0.001),
	"неизвестная редкость существа — без сдвига"
)

print("· бросок")
check(FloorRules.Roll("Common", 0) == "Wood", "roll 0 — Деревянный")
check(
	FloorRules.Roll("Common", 0.5999) == "Wood" and FloorRules.Roll("Common", 0.6001) == "Stone",
	"граница 60 %"
)
check(
	FloorRules.Roll("Common", 0.9989) == "Mythic" and FloorRules.Roll("Common", 0.9991) == "Cosmic",
	"граница 99.9 %"
)
check(FloorRules.Roll("Common", 0.999999) == "Cosmic", "roll у 1 — Космический")
check(FloorRules.Roll("Common", 0 / 0) == "Wood", "NaN — ступень по умолчанию")
check(FloorRules.Roll("Common", "x") == "Wood", "не число — ступень по умолчанию")
local counts, n = {}, 200000
math.randomseed(12345)
for _ = 1, n do
	local key = FloorRules.Roll("Epic", math.random())
	counts[key] = (counts[key] or 0) + 1
end
for i, key in FloorRarity.Order do
	local want = FloorRules.Weights("Epic")[i]
	check(
		near((counts[key] or 0) / n, want, 0.004),
		("частота %s у Epic около %.2f %%"):format(key, want * 100)
	)
end

print("· доход")
for rarity in expected do
	local mean = 0
	for i, key in FloorRarity.Order do
		mean += FloorRules.Weights(rarity)[i] * FloorRules.Income(1000, rarity, key)
	end
	check(
		near(mean, 1000, 1e-6),
		"матожидание дохода с поимки у " .. rarity .. " = доход существа"
	)
end
check(near(FloorRules.Income(206, "Common", "Wood"), 100, 0.01), "Деревянный этаж Common: 206 → 100")
check(
	near(FloorRules.Income(206, "Common", "Cosmic"), 6000, 0.5),
	"Космический этаж Common: 206 → 6000"
)
check(
	FloorRules.Income(100, "Common", nil) == FloorRules.Income(100, "Common", "Wood"),
	"пустая редкость = Деревянный"
)
check(
	FloorRules.Income(100, "Common", "Golden") == FloorRules.Income(100, "Common", "Wood"),
	"чужой ключ = Деревянный"
)
check(
	FloorRules.Normalize(42) == "Wood" and FloorRules.IsRarity("Gold") and not FloorRules.IsRarity("gold"),
	"ключи"
)

print("· удержание по силе")
check(
	FloorRules.HoldFactor(0, 0) == 1 and FloorRules.HoldFactor(5, 0) == 1,
	"босс с нулевой силой — обычный шанс"
)
check(FloorRules.HoldFactor(140, 140) == 1, "сила = силе босса — 1")
check(near(FloorRules.HoldFactor(70, 140), 0.5, 1e-9), "половина силы — 0.5")
check(FloorRules.HoldFactor(1, 1000000) == 0.05, "очень слабый — не ниже 0.05")
check(near(FloorRules.HoldFactor(210, 140), 1.125, 1e-9), "в 1.5 раза сильнее — +12.5 %")
check(
	FloorRules.HoldFactor(280, 140) == 1.25 and FloorRules.HoldFactor(1e12, 140) == 1.25,
	"от 2 раз — +25 %, не больше"
)
check(
	FloorRules.HoldFactor(0 / 0, 140) == 0.05 and FloorRules.HoldFactor(-5, 140) == 0.05,
	"мусор вместо силы — минимум"
)
check(FloorRules.HoldFactor(100, 0 / 0) == 1, "мусор вместо силы босса — обычный шанс")

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
process.exit(if failed == 0 then 0 else 1)

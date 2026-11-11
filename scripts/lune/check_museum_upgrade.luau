--!nocheck
-- Проверка улучшения музея без Roblox Studio (D56; Shared/MuseumRules, Shared/GameTime.UpgradeLock): уровни 1…10,
-- места max(6, 2 × уровень) ≤ 20, цены уровней 2…10, коды отказа (последний уровень, запрет по фазе, монеты), «только
-- следующий уровень», запрет покупки в подготовку, Судную ночь и 10 с после неё — на всём круге с шагом 0.5 с.
-- Сам обработчик покупки (сервер, профиль, мир) проверяют серверные тесты в Studio («D56 музей»).
-- Запуск из корня репозитория: lune run scripts/lune/check_museum_upgrade.luau. Ошибка — код возврата 1.

local process = require("@lune/process")

local Env = require("./env")

local GameConfig = Env.Require("ReplicatedStorage.Shared.Config.GameConfig")
local GameTime = Env.Require("ReplicatedStorage.Shared.GameTime")
local MuseumRules = Env.Require("ReplicatedStorage.Shared.MuseumRules")

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

local Codes = MuseumRules.Codes
local prices = GameConfig.Progression.Museum.Prices
local NAN = 0 / 0

print("Уровни и места:")
do
	check(MuseumRules.MaxLevel(GameConfig) == 10, "уровней 10")
	local levelsOk = true
	for level = 1, 10 do
		levelsOk = levelsOk and MuseumRules.IsLevel(GameConfig, level)
	end
	check(levelsOk, "уровни 1…10 — уровни")
	local badOk = true
	for _, bad in { 0, 11, -1, 2.5, NAN, math.huge, "3", true, {} } do
		badOk = badOk and not MuseumRules.IsLevel(GameConfig, bad)
	end
	check(
		badOk and not MuseumRules.IsLevel(GameConfig, nil),
		"0, 11, дробное, NaN, строка, nil — не уровни"
	)
	check(
		MuseumRules.Level(GameConfig, nil) == 1
			and MuseumRules.Level(GameConfig, "7") == 1
			and MuseumRules.Level(GameConfig, NAN) == 1
			and MuseumRules.Level(GameConfig, 0) == 1
			and MuseumRules.Level(GameConfig, 3.9) == 3
			and MuseumRules.Level(GameConfig, 99) == 10,
		"испорченный уровень из профиля приводится к 1…10"
	)
	local want = { 6, 6, 6, 8, 10, 12, 14, 16, 18, 20 }
	local slotsOk = true
	for level, slots in want do
		slotsOk = slotsOk
			and MuseumRules.Slots(GameConfig, level) == slots
			and slots == math.min(20, math.max(6, 2 * level))
	end
	check(slotsOk, "мест 6, 6, 6, 8, 10, 12, 14, 16, 18, 20 — max(6, 2 × уровень), не больше 20")
	check(GameConfig.Museum.MaxSlots == 20, "всего постаментов на участке — 20")
end

print("Цены:")
do
	local approved = { 10e3, 100e3, 610e3, 94e6, 680e6, 3.7e9, 46e9, 630e9, 3.2e12 }
	local priceOk, total = #prices == 9, 0
	for level = 1, 9 do
		priceOk = priceOk
			and MuseumRules.Price(GameConfig, level) == approved[level]
			and prices[level] == approved[level]
		total += approved[level]
	end
	check(
		priceOk,
		"цена уровня N + 1 — утверждённая: 10K, 100K, 610K, 94M, 680M, 3.7B, 46B, 630B, 3.2T"
	)
	check(total == 3880474720000, ("все уровни 2…10 стоят вместе %d"):format(total))
	check(MuseumRules.Price(GameConfig, 10) == nil, "после уровня 10 цены нет")
	check(
		MuseumRules.Price(GameConfig, 0) == nil
			and MuseumRules.Price(GameConfig, 11) == nil
			and MuseumRules.Price(GameConfig, 1.5) == nil
			and MuseumRules.Price(GameConfig, "1") == nil
			and MuseumRules.Price(GameConfig, nil) == nil,
		"у «не уровня» цены нет"
	)
end

print("Можно ли купить:")
do
	local allOk = true
	for level = 1, 9 do
		local price = prices[level]
		allOk = allOk
			and MuseumRules.Check(GameConfig, level, price, nil) == nil
			and MuseumRules.Check(GameConfig, level, price + 1e15, nil) == nil
			and MuseumRules.Check(GameConfig, level, price - 1, nil) == Codes.Coins
			and MuseumRules.Check(GameConfig, level, 0, nil) == Codes.Coins
			and MuseumRules.Check(GameConfig, level, price, "запрет") == Codes.Locked
			and MuseumRules.Check(GameConfig, level, 0, "запрет") == Codes.Locked
	end
	check(
		allOk,
		"уровни 1…9: ровно цена — можно, на 1 меньше — «Coins», запрет по фазе — «Locked»"
	)
	check(
		MuseumRules.Check(GameConfig, 10, 1e18, nil) == Codes.Max
			and MuseumRules.Check(GameConfig, 10, 0, "запрет") == Codes.Max,
		"уровень 10: «Max» при любых монетах и фазе"
	)
	check(
		MuseumRules.Check(GameConfig, 1, NAN, nil) == Codes.Coins
			and MuseumRules.Check(GameConfig, 1, "999999", nil) == Codes.Coins
			and MuseumRules.Check(GameConfig, 1, nil, nil) == Codes.Coins,
		"монеты не числом — «Coins»"
	)
	check(
		MuseumRules.Check(GameConfig, 0, 1e18, nil) == Codes.Stale
			and MuseumRules.Check(GameConfig, 2.5, 1e18, nil) == Codes.Stale
			and MuseumRules.Check(GameConfig, nil, 1e18, nil) == Codes.Stale,
		"уровень в профиле не уровень — «Stale», покупки нет"
	)
	local nextOk = true
	for level = 1, 9 do
		nextOk = nextOk and MuseumRules.IsNext(GameConfig, level, level + 1)
		for requested = 1, 10 do
			if requested ~= level + 1 then
				nextOk = nextOk and not MuseumRules.IsNext(GameConfig, level, requested)
			end
		end
	end
	check(
		nextOk,
		"годится только запрос ровно следующего уровня (не текущего, не через уровень, не ниже)"
	)
	local forged = true
	for _, bad in { 2.5, "2", NAN, math.huge, -1, 0, 11, true, {} } do
		forged = forged and not MuseumRules.IsNext(GameConfig, 1, bad)
	end
	check(
		forged and not MuseumRules.IsNext(GameConfig, 1, nil) and not MuseumRules.IsNext(GameConfig, 10, 11),
		"поддельные запросы (дробь, строка, NaN, nil, 11) не годятся"
	)
end

print("Запрет по фазам (круг с шагом 0.5 с):")
do
	local time = GameConfig.Time
	local length = GameTime.CycleLength()
	local base = time.Epoch + 1000 * length
	local prepStart = base + length - time.DoomNightLength - time.PreparationLength
	local doomStart = base + length - time.DoomNightLength
	local doomEnd = base + length
	local unlock = doomEnd + time.DeliveryGrace
	local wrong, lockedSteps, openSteps, wrongUnlock = 0, 0, 0, 0
	local phases = {}
	local t = base
	while t < base + length + 30 do
		local reason, unlockAt = GameTime.UpgradeLock(t)
		-- в начале круга ещё идут 10 с после прошлой Судной ночи
		local expected = (t >= prepStart and t < unlock) or (t < base + time.DeliveryGrace)
		if (reason ~= nil) ~= expected then
			wrong += 1
		end
		if reason then
			lockedSteps += 1
			phases[GameTime.At(t).phase] = true
			local wantUnlock = if t < base + time.DeliveryGrace then base + time.DeliveryGrace else unlock
			if unlockAt ~= wantUnlock then
				wrongUnlock += 1
			end
		else
			openSteps += 1
			if unlockAt ~= nil then
				wrongUnlock += 1
			end
		end
		t += 0.5
	end
	check(
		wrong == 0,
		("запрет ровно в подготовку, Судную ночь и 10 с после неё (расхождений %d)"):format(
			wrong
		)
	)
	check(wrongUnlock == 0, "время окончания запрета — конец Судной ночи + 10 с")
	check(
		phases.Preparation and phases.DoomNight and phases.Day and not phases.Night,
		"запрет бывает в подготовку, в Судную ночь и днём (10 с после); в обычную ночь — нет"
	)
	check(
		time.PreparationLength + time.DoomNightLength + time.DeliveryGrace == 220,
		"запрет длится 120 + 90 + 10 = 220 с из 3360 с круга"
	)
	local eps = 1e-3
	check(
		GameTime.UpgradeLock(prepStart - eps) == nil and GameTime.UpgradeLock(prepStart) ~= nil,
		"граница: за миг до подготовки — можно, с её начала — нельзя"
	)
	check(
		GameTime.UpgradeLock(doomStart - eps) ~= nil
			and GameTime.UpgradeLock(doomStart) ~= nil
			and GameTime.UpgradeLock(doomEnd - eps) ~= nil
			and GameTime.UpgradeLock(doomEnd) ~= nil,
		"граница: подготовка → Судная ночь → 10 с после — запрет без разрывов"
	)
	check(
		GameTime.UpgradeLock(unlock - eps) ~= nil and GameTime.UpgradeLock(unlock) == nil,
		"граница: на 10-й секунде после Судной ночи запрет кончается"
	)
	local nights = true
	for day = 1, time.DoomEvery - 1 do
		local nightStart = base + (day - 1) * (time.DayLength + time.NightLength) + time.DayLength
		nights = nights and GameTime.At(nightStart + 1).phase == "Night" and GameTime.UpgradeLock(nightStart + 1) == nil
	end
	check(nights, "в девять обычных ночей покупать можно")
	local a = GameTime.UpgradeLock(prepStart + 1)
	local b = GameTime.UpgradeLock(doomStart + 1)
	local c = GameTime.UpgradeLock(doomEnd + 1)
	check(
		type(a) == "string" and type(b) == "string" and type(c) == "string" and a ~= b and b ~= c,
		"у каждой причины запрета свой текст для игрока"
	)
	print(("    шагов с запретом %d, без запрета %d"):format(lockedSteps, openSteps))
end

print(("Проверок: %d, не прошло: %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end
print("Все проверки улучшения музея прошли")

-- Правила редкости этажа (D74), чистые функции для сервера, клиента и проверок: веса ступеней со сдвигом от редкости
-- существа, бросок по готовому случайному числу (число даёт сервер), средний множитель, доход этажа (нормирован:
-- матожидание дохода с поимки — как у существа по D56) и множитель удержания по силе. Проверка —
-- scripts/lune/check_floor_rules.luau. Зависит от Config/FloorRarity.

local FloorRarity = require(script.Parent.Config.FloorRarity)

local FloorRules = {}

function FloorRules.IsRarity(key: any): boolean
	return type(key) == "string" and FloorRarity.Mult[key] ~= nil
end

-- Ключ редкости записи предмета: пустое или чужое значение — ступень по умолчанию (Деревянный).
function FloorRules.Normalize(key: any): string
	return if FloorRules.IsRarity(key) then key else FloorRarity.Default
end

-- Веса ступеней (в порядке FloorRarity.Order, в сумме 1) для существа редкости creatureRarity.
function FloorRules.Weights(creatureRarity: string?): { number }
	local shift = FloorRarity.Shift[creatureRarity or ""] or 1
	local weights, total = {}, 0
	for i, key in FloorRarity.Order do
		local w = FloorRarity.Chance[key] * shift ^ (i - 1)
		weights[i] = w
		total += w
	end
	for i, w in weights do
		weights[i] = w / total
	end
	return weights
end

-- Бросок: roll — случайное число 0 ≤ roll < 1 (сервер). Возвращает ключ редкости этажа.
function FloorRules.Roll(creatureRarity: string?, roll: number): string
	local order = FloorRarity.Order
	if type(roll) ~= "number" or roll ~= roll then
		return FloorRarity.Default
	end
	local acc = 0
	for i, w in FloorRules.Weights(creatureRarity) do
		acc += w
		if roll < acc then
			return order[i]
		end
	end
	return order[#order]
end

-- Шанс ступени для существа этой редкости, доля 0…1 (показ «1 из N» в прокрутке).
function FloorRules.Chance(creatureRarity: string?, floorRarity: string): number
	local weights = FloorRules.Weights(creatureRarity)
	for i, key in FloorRarity.Order do
		if key == floorRarity then
			return weights[i]
		end
	end
	return 0
end

-- Средний множитель дохода этажа для существа этой редкости — делитель нормировки.
function FloorRules.ExpectedMult(creatureRarity: string?): number
	local sum = 0
	for i, w in FloorRules.Weights(creatureRarity) do
		sum += w * FloorRarity.Mult[FloorRarity.Order[i]]
	end
	return sum
end

-- Доход этажа в секунду: доход существа ÷ средний множитель × множитель редкости этажа.
function FloorRules.Income(baseIncome: number, creatureRarity: string?, floorRarity: any): number
	local mult = FloorRarity.Mult[FloorRules.Normalize(floorRarity)]
	return baseIncome / FloorRules.ExpectedMult(creatureRarity) * mult
end

-- Множитель шанса удержания существа в Ловибуме по силе игрока против силы босса. У босса с нулевой силой — 1.
function FloorRules.HoldFactor(strength: number, bossStrength: number): number
	local cfg = FloorRarity.Hold
	if type(strength) ~= "number" or strength ~= strength or strength < 0 then
		return cfg.Min
	end
	if type(bossStrength) ~= "number" or bossStrength ~= bossStrength or bossStrength <= 0 then
		return 1
	end
	local ratio = strength / bossStrength
	if ratio < 1 then
		return math.max(cfg.Min, ratio)
	end
	local t = math.clamp((ratio - 1) / (cfg.BonusAt - 1), 0, 1)
	return 1 + cfg.Bonus * t
end

return FloorRules

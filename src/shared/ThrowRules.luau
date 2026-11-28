-- Правила «броска вдаль» (D75), чистые функции для сервера, клиента и проверок. Случайные числа и время даёт
-- вызывающий (сервер): здесь только расчёт.
--   трасса    — Metres (дальность по силе), Mark (отметка зоны), Landing (зона и глубина приземления);
--   шкала     — ScalePosition (где маркер в момент t), Quality (качество нажатия 0…1), PressTime (момент нажатия с
--               учётом задержки и защитой от подделки), AccuracyMult;
--   бросок    — Distance (сила × точность × вид, не дальше зоны уровня Ловибума), Luck (удача по глубине), Hunt
--               (охота вида: Бум — фарм, Турбо и Мега поднимают верхние редкости), SuggestLevel (подсказка магазина);
--   розыгрыш  — CreatureWeights / RollCreature (редкость существа, D37 + удача), FloorWeights / RollFloor (редкость этажа,
--               D74 + удача), IsBoss, Chance и OneIn («1 из N» для экрана выпадения и окна шансов);
--   награда   — Income (доход этажа с калибровкой зоны), BossIncome, SellPrice;
--   башня     — SameFloor / HasFloor (двух одинаковых этажей — то же существо и та же редкость этажа — быть не может),
--               AutoSell (фильтр авто-продажи).
-- Проверка — scripts/lune/check_throw_rules.luau.
-- Зависит от Config/Throw, Config/Progression, Config/FloorRarity, Config/Rarities, Config/Items, Shared/FloorRules.

local Config = script.Parent.Config
local FloorRarity = require(Config.FloorRarity)
local Items = require(Config.Items)
local Progression = require(Config.Progression)
local Rarities = require(Config.Rarities)
local Throw = require(Config.Throw)
local FloorRules = require(script.Parent.FloorRules)

local ThrowRules = {}

ThrowRules.Zones = #Progression.Bosses

local function number(x: any): boolean
	return type(x) == "number" and x == x and x ~= math.huge and x ~= -math.huge
end

-- ---------- трасса ----------

-- Дальность броска без бонусов, м, по силе игрока.
function ThrowRules.Metres(strength: number): number
	local s = if number(strength) then math.max(0, strength) else 0
	return Throw.Metre.K * (1 + s) ^ Throw.Metre.Power
end

-- Отметка начала зоны zone на трассе, м: зона 1 — с нуля, дальше — дальность при силе босса зоны; после последней
-- зоны — конец трассы.
function ThrowRules.Mark(zone: number): number
	if zone <= 1 then
		return 0
	end
	if zone > ThrowRules.Zones then
		return Throw.EndMark
	end
	return ThrowRules.Metres(Progression.Bosses[zone])
end

-- Зона приземления и глубина в ней (0 — у начала зоны, 1 — у конца) по дальности, м.
function ThrowRules.Landing(distance: number): (number, number)
	local d = if number(distance) then math.clamp(distance, 0, Throw.EndMark) else 0
	local zone = 1
	for n = ThrowRules.Zones, 2, -1 do
		if d >= ThrowRules.Mark(n) then
			zone = n
			break
		end
	end
	local from, to = ThrowRules.Mark(zone), ThrowRules.Mark(zone + 1)
	return zone, math.clamp((d - from) / (to - from), 0, 1)
end

-- ---------- шкала точности ----------

-- Положение маркера на шкале 0…1 через elapsed секунд после начала: ходит туда-обратно за period секунд, начиная с
-- доли phase (0…1) своего пути.
function ThrowRules.ScalePosition(elapsed: number, period: number, phase: number?): number
	if not number(elapsed) or not number(period) or period <= 0 then
		return 0
	end
	local turn = (math.max(0, elapsed) / period + (if number(phase) then phase :: number else 0)) % 1
	return if turn < 0.5 then turn * 2 else 2 - turn * 2
end

-- Качество нажатия 0…1 по положению маркера: 1 — в зоне «идеально» у середины шкалы, к краям — линейно до 0.
function ThrowRules.Quality(position: number): number
	if not number(position) then
		return 0
	end
	local off = math.abs(math.clamp(position, 0, 1) - 0.5)
	local perfect = Throw.Scale.Perfect
	if off <= perfect + 1e-9 then -- граница зоны входит в неё (погрешность дробных чисел)
		return 1
	end
	return math.clamp(1 - (off - perfect) / (0.5 - perfect), 0, 1)
end

-- Момент нажатия, который принимает сервер: заявленный клиентом claimed (время сервера в его оценке), но не раньше
-- «сейчас − LagCap» и не позже «сейчас». Мусор вместо числа — «сейчас».
function ThrowRules.PressTime(serverNow: number, claimed: any): number
	if not number(claimed) then
		return serverNow
	end
	return math.clamp(claimed, serverNow - Throw.Scale.LagCap, serverNow)
end

-- Множитель дальности за точность: качество 0…1 → 1 … 1 + Max.
function ThrowRules.AccuracyMult(quality: number): number
	local q = if number(quality) then math.clamp(quality, 0, 1) else 0
	return 1 + Throw.Accuracy.Max * q
end

-- ---------- бросок ----------

local function kindOf(kind: any): string
	return if type(kind) == "string" and Throw.KindRange[kind] then kind else "Boom"
end

-- Дальность броска, м: сила × точность × вид; Ловибум уровня level не летит дальше конца зоны level.
function ThrowRules.Distance(strength: number, quality: number, kind: string, level: number): number
	local lv = if number(level) then math.clamp(math.floor(level), 1, ThrowRules.Zones) else 1
	local d = ThrowRules.Metres(strength) * ThrowRules.AccuracyMult(quality) * Throw.KindRange[kindOf(kind)]
	return math.min(d, ThrowRules.Mark(lv + 1))
end

-- Удача броска по глубине в зоне приземления: ×1 у начала зоны … ×(1 + Depth) у конца.
function ThrowRules.Luck(depth: number): number
	local f = if number(depth) then math.clamp(depth, 0, 1) else 0
	return 1 + Throw.Luck.Depth * f
end

-- Охота вида Ловибума: множители весов верхних редкостей существ и этажей (Бум — 1 и 1).
function ThrowRules.Hunt(kind: any): (number, number)
	local hunt = Throw.KindHunt[kindOf(kind)]
	return hunt.creature, hunt.floor
end

-- Уровень Ловибума, который стоит купить: самая дальняя зона, до которой игрок добивает при любом нажатии.
function ThrowRules.SuggestLevel(strength: number): number
	return (ThrowRules.Landing(ThrowRules.Metres(strength)))
end

-- ---------- розыгрыш ----------

local function step(luck: number?): number
	local l = if number(luck) then math.max(1, luck :: number) else 1
	return l ^ Throw.Luck.Power
end

local function tierOf(zone: number): { [string]: number }
	for _, tier in Progression.BossLoot.Tiers do
		if zone >= tier.from and zone <= tier.to then
			return tier.chances
		end
	end
	return Progression.BossLoot.Tiers[1].chances
end

-- Шансы редкости существа в зоне (в порядке Rarities.Order, в сумме 1): D37, вес каждой следующей ступени × удача^Power,
-- веса верхних редкостей × охота вида kind (без kind — Бум).
function ThrowRules.CreatureWeights(zone: number, luck: number?, kind: string?): { number }
	local chances, s = tierOf(zone), step(luck)
	local hunt = ThrowRules.Hunt(kind)
	local weights, total = {}, 0
	for i, rarity in Rarities.Order do
		local w = (chances[rarity] or 0) * s ^ (i - 1) * (if Throw.HuntCreatures[rarity] then hunt else 1)
		weights[i] = w
		total += w
	end
	for i, w in weights do
		weights[i] = w / total
	end
	return weights
end

-- Шансы редкости этажа (в порядке FloorRarity.Order, в сумме 1): D74 со сдвигом от редкости существа и от удачи,
-- веса верхних редкостей × охота вида kind (без kind — Бум).
function ThrowRules.FloorWeights(creatureRarity: string?, luck: number?, kind: string?): { number }
	local shift = (FloorRarity.Shift[creatureRarity or ""] or 1) * step(luck)
	local _, hunt = ThrowRules.Hunt(kind)
	local weights, total = {}, 0
	for i, key in FloorRarity.Order do
		local w = FloorRarity.Chance[key] * shift ^ (i - 1) * (if Throw.HuntFloors[key] then hunt else 1)
		weights[i] = w
		total += w
	end
	for i, w in weights do
		weights[i] = w / total
	end
	return weights
end

local function pick(weights: { number }, order: { string }, roll: number): string
	if not number(roll) then
		return order[1]
	end
	local acc = 0
	for i, w in weights do
		acc += w
		if roll < acc then
			return order[i]
		end
	end
	for i = #order, 1, -1 do -- roll ≥ 1 или накопленная погрешность: самая редкая из возможных
		if weights[i] > 0 then
			return order[i]
		end
	end
	return order[1]
end

-- Редкость существа: roll — случайное число 0 ≤ roll < 1 (сервер).
function ThrowRules.RollCreature(zone: number, luck: number?, kind: string?, roll: number): string
	return pick(ThrowRules.CreatureWeights(zone, luck, kind), Rarities.Order, roll)
end

-- Редкость этажа: roll — случайное число 0 ≤ roll < 1 (сервер).
function ThrowRules.RollFloor(creatureRarity: string?, luck: number?, kind: string?, roll: number): string
	return pick(ThrowRules.FloorWeights(creatureRarity, luck, kind), FloorRarity.Order, roll)
end

-- Выпал ли босс зоны: roll — своё случайное число 0 ≤ roll < 1 (сервер).
function ThrowRules.IsBoss(roll: number): boolean
	return number(roll) and roll >= 0 and roll < Throw.BossChance
end

-- Шанс сочетания «существо редкости creatureRarity на этаже floorRarity» в зоне при удаче и виде Ловибума, доля
-- 0…1. Без floorRarity — шанс редкости существа.
function ThrowRules.Chance(
	zone: number,
	luck: number?,
	kind: string?,
	creatureRarity: string,
	floorRarity: string?
): number
	local i = table.find(Rarities.Order, creatureRarity)
	if not i then
		return 0
	end
	local p = ThrowRules.CreatureWeights(zone, luck, kind)[i]
	if floorRarity == nil then
		return p
	end
	local k = table.find(FloorRarity.Order, floorRarity)
	return if k then p * ThrowRules.FloorWeights(creatureRarity, luck, kind)[k] else 0
end

-- «1 из N» по шансу (доля 0…1): целое N ≥ 1; нулевой шанс — math.huge.
function ThrowRules.OneIn(chance: number): number
	if not number(chance) or chance <= 0 then
		return math.huge
	end
	return math.max(1, math.floor(1 / chance + 0.5))
end

-- ---------- награда ----------

local function incomeK(zone: number): number
	return Throw.IncomeK[zone] or 1
end

-- Доход этажа в секунду (дробный): доход существа ÷ средний множитель этажа × множитель редкости этажа (D74) ×
-- калибровка зоны существа (D75).
function ThrowRules.Income(baseIncome: number, creatureRarity: string?, floorRarity: any, zone: number): number
	return FloorRules.Income(baseIncome, creatureRarity, floorRarity) * incomeK(zone)
end

local legendary: { [number]: number } = {}

-- Средний доход Легендарного существа зоны по каталогу: Progression.CreatureIncome (зоны 4–10) или коллекция зоны в
-- Config/Items; в зонах без Легендарных — LegendaryOfEpic × средний Эпический.
function ThrowRules.LegendaryBase(zone: number): number
	if legendary[zone] then
		return legendary[zone]
	end
	local income = Progression.CreatureIncome
	local row = income.ByBoss[zone] or {}
	local value = row.Legendary
	if not value then
		local sums: { [string]: { number } } = { Legendary = { 0, 0 }, Epic = { 0, 0 } }
		for _, def in Items do
			local s = sums[def.rarity]
			if s and def.boss == zone and not def.legacy and def.income > 0 then
				s[1] += def.income
				s[2] += 1
			end
		end
		if sums.Legendary[2] > 0 then
			value = sums.Legendary[1] / sums.Legendary[2]
		else
			local epic = row.Epic or (if sums.Epic[2] > 0 then sums.Epic[1] / sums.Epic[2] else 0)
			value = epic * income.LegendaryOfEpic
		end
	end
	legendary[zone] = value
	return value
end

-- Доход босса зоны на крыше башни, в секунду (дробный): как у Легендарного существа на Золотом этаже своей зоны.
function ThrowRules.BossIncome(zone: number): number
	return ThrowRules.Income(ThrowRules.LegendaryBase(zone), Throw.Boss.Rarity, Throw.Boss.Floor, zone)
end

-- Цена продажи капсулы, монет: доход этажа за SellSeconds секунд, не меньше 1.
function ThrowRules.SellPrice(incomePerSecond: number): number
	local income = if number(incomePerSecond) then math.max(0, incomePerSecond) else 0
	return math.max(1, math.floor(income * Throw.SellSeconds + 0.5))
end

-- ---------- башня ----------

-- Одинаковые ли этажи: то же существо и та же редкость этажа (пустая редкость = Деревянный).
function ThrowRules.SameFloor(itemA: string, floorA: any, itemB: string, floorB: any): boolean
	return itemA == itemB and FloorRules.Normalize(floorA) == FloorRules.Normalize(floorB)
end

-- Есть ли уже такой этаж среди floors — списка { itemId = …, floor = … }.
function ThrowRules.HasFloor(floors: { { itemId: string, floor: any } }, itemId: string, floor: any): boolean
	for _, f in floors do
		if ThrowRules.SameFloor(f.itemId, f.floor, itemId, floor) then
			return true
		end
	end
	return false
end

export type SellFilter = { creature: string?, floor: string?, duplicates: boolean? }

-- Авто-продажа по фильтру игрока: продаётся повтор (duplicate), если включено duplicates, и награда, у которой и
-- редкость существа не выше filter.creature, и редкость этажа не выше filter.floor (оба поля заданы). Босс не
-- продаётся никогда (вызывающий его сюда не передаёт).
function ThrowRules.AutoSell(filter: SellFilter?, creatureRarity: string, floorRarity: any, duplicate: boolean): boolean
	if type(filter) ~= "table" then
		return false
	end
	if duplicate and filter.duplicates == true then
		return true
	end
	local creatureMax = table.find(Rarities.Order, filter.creature :: any)
	local floorMax = table.find(FloorRarity.Order, filter.floor :: any)
	if not creatureMax or not floorMax then
		return false
	end
	local c = table.find(Rarities.Order, creatureRarity) or 1
	local f = table.find(FloorRarity.Order, FloorRules.Normalize(floorRarity)) or 1
	return c <= creatureMax and f <= floorMax
end

return ThrowRules

--!strict
-- Правила поимки «Ловибум» и магазина Ловибумов (D55): шанс захвата, цена и проверка покупки, запас в профиле, круг
-- прицеливания и попадание, автомат мини-игры (броски, поимка, конец), личная пауза у босса. Чистые функции без
-- Instance: их вызывают ShopService, CatchService, TutorialService, клиент (подсказки, круг) и
-- scripts/lune/check_catch.luau. Числа — Config/Catch.
-- Зависит от Config/Catch.

local Catch = require(script.Parent.Config.Catch)

local CatchRules = {}

CatchRules.Config = Catch

local MAX_SAFE = 9e15 -- больше — дробная часть и целые числа теряют точность

-- Целое число без NaN и бесконечностей.
function CatchRules.IsWhole(n: any): boolean
	return type(n) == "number" and n == n and n == math.floor(n) and math.abs(n) <= MAX_SAFE
end

function CatchRules.IsKind(kind: any): boolean
	return type(kind) == "string" and Catch.Bonus[kind] ~= nil
end

function CatchRules.IsLevel(level: any): boolean
	return CatchRules.IsWhole(level) and level >= 1 and level <= Catch.Levels
end

-- Ключ уровня в профиле: lovibums.L<уровень>.
function CatchRules.LevelKey(level: number): string
	return "L" .. level
end

-- Шанс захвата после попадания: база редкости × бонус вида, не больше 1. 0 — неизвестные редкость или вид.
function CatchRules.Chance(rarity: string, kind: string): number
	local base = Catch.BaseChance[rarity]
	local bonus = Catch.Bonus[kind]
	if not base or not bonus then
		return 0
	end
	return math.min(1, base * bonus)
end

-- ── Магазин ──────────────────────────────────────────────────────────────────────────────────────────────────

-- Действующие цены (уровень → вид → монеты): утверждённые (Config/Catch.Prices); в тестовом режиме (Studio + DevMode)
-- к ним — предварительные (PreliminaryPrices) уровней без утверждённой цены. Уровня нет — не продаётся.
function CatchRules.Prices(testMode: boolean): { [number]: { [string]: number } }
	local out = {}
	for level = 1, Catch.Levels do
		local final = if Catch.Prices then Catch.Prices[level] else nil
		local preliminary = if testMode and Catch.PreliminaryPrices then Catch.PreliminaryPrices[level] else nil
		out[level] = final or preliminary
	end
	return out
end

-- Цена уровня ещё не утверждена владельцем (продаётся только в Studio + DevMode с пометкой).
function CatchRules.IsPreliminary(level: number): boolean
	return not (Catch.Prices and Catch.Prices[level])
end

-- Цена одного Ловибума вида kind уровня level или nil.
function CatchRules.Price(prices: { [number]: { [string]: number } }?, level: number, kind: string): number?
	local byKind = prices and prices[level]
	local price = byKind and byKind[kind]
	if type(price) ~= "number" or price ~= price or price <= 0 or price > MAX_SAFE then
		return nil
	end
	return price
end

-- Запас вида kind уровня level в профиле (lovibums = { L<уровень> = { вид → n } }); испорченное считается нулём.
function CatchRules.Stock(lovibums: any, level: number, kind: string): number
	local byKind = type(lovibums) == "table" and lovibums[CatchRules.LevelKey(level)]
	local n = type(byKind) == "table" and byKind[kind]
	return if CatchRules.IsWhole(n) and n > 0 then n else 0
end

-- Всего Ловибумов уровня level (любых видов).
function CatchRules.StockOfLevel(lovibums: any, level: number): number
	local total = 0
	for _, kind in Catch.Kinds do
		total += CatchRules.Stock(lovibums, level, kind)
	end
	return total
end

-- Проверка покупки (все аргументы — от клиента, им не верим). Возвращает итог в монетах или nil и причину отказа.
function CatchRules.CheckBuy(
	prices: { [number]: { [string]: number } }?,
	level: any,
	kind: any,
	count: any,
	coins: number,
	lovibums: any
): (number?, string?)
	if not CatchRules.IsLevel(level) then
		return nil, "Нет такого уровня"
	end
	if not CatchRules.IsKind(kind) then
		return nil, "Нет такого Ловибума"
	end
	if not CatchRules.IsWhole(count) or count < 1 or count > Catch.MaxBuy then
		return nil, ("Можно купить от 1 до %d за раз"):format(Catch.MaxBuy)
	end
	local price = CatchRules.Price(prices, level, kind)
	if not price then
		return nil, "Ловибумы пока не продаются"
	end
	local total = price * count
	if total > MAX_SAFE then
		return nil, "Слишком дорого"
	end
	if CatchRules.Stock(lovibums, level, kind) + count > Catch.MaxStock then
		return nil, ("Больше %d штук одного вида не поместится"):format(Catch.MaxStock)
	end
	if type(coins) ~= "number" or coins ~= coins or coins < total then
		return nil, "Не хватает монет"
	end
	return total, nil
end

-- Запас Ловибумов из профиля в порядке: только L1…L10 и известные виды, целые 1…MaxStock (остальное — убрать).
-- Меняет таблицу на месте и возвращает её; не таблица — новая пустая.
function CatchRules.Normalize(lovibums: any): { [string]: { [string]: number } }
	local out = if type(lovibums) == "table" then lovibums else {}
	for key, byKind in out do
		local level = type(key) == "string" and tonumber(string.match(key, "^L(%d+)$"))
		if not level or not CatchRules.IsLevel(level) or type(byKind) ~= "table" then
			out[key] = nil
			continue
		end
		for kind, n in byKind do
			if not CatchRules.IsKind(kind) or not CatchRules.IsWhole(n) or n <= 0 then
				byKind[kind] = nil
			elseif n > Catch.MaxStock then
				byKind[kind] = Catch.MaxStock
			end
		end
		if next(byKind) == nil then
			out[key] = nil
		end
	end
	return out
end

-- ── Круг прицеливания и попадание ────────────────────────────────────────────────────────────────────────────

-- Радиус круга в момент t мини-игры, начатой в since (сжимается от Max к Min за Period, потом снова), × масштаб
-- существа (CreatureMotion.ScaleOf) × множитель (обучение — крупнее).
function CatchRules.CircleRadius(t: number, since: number, scale: number, factor: number?): number
	local c = Catch.Game.Circle
	local phase = ((t - since) % c.Period) / c.Period
	return (c.Max - (c.Max - c.Min) * phase) * scale * (factor or 1)
end

-- Попадание: точка прилёта aim внутри круга radius вокруг центра существа center.
function CatchRules.IsHit(aim: Vector3, center: Vector3, radius: number): boolean
	return (aim - center).Magnitude <= radius
end

-- ── Мини-игра ────────────────────────────────────────────────────────────────────────────────────────────────

export type Session = {
	user: number,
	boss: number,
	slot: number,
	uid: string,
	rarity: string,
	since: number, -- начало (общее время сервера)
	throws: number,
	lastThrow: number, -- время отпускания последнего броска
	readyAt: number, -- раньше этого (время отпускания) следующий бросок нельзя: полёт и сеть / побег видны всем
	lastActive: number,
	state: string, -- "Aim" | "Caught" | "Over"
	tutorial: boolean, -- учебная: броски бесплатные, первое попадание — захват, без лимита бросков
	endReason: string?,
}

function CatchRules.NewSession(
	user: number,
	boss: number,
	slot: number,
	uid: string,
	rarity: string,
	now: number,
	tutorial: boolean?
): Session
	return {
		user = user,
		boss = boss,
		slot = slot,
		uid = uid,
		rarity = rarity,
		since = now,
		throws = 0,
		lastThrow = -math.huge,
		readyAt = -math.huge,
		lastActive = now,
		state = "Aim",
		tutorial = tutorial == true,
		endReason = nil,
	}
end

-- Можно ли бросить: причина отказа или nil. releaseTime — когда игрок отпустил (от клиента: не позже времени сервера
-- больше ClockAhead и не раньше ClockSlack; пауза между бросками — по временам отпускания), stock — запас этого вида
-- этого уровня (у учебной не нужен).
function CatchRules.CheckThrow(session: Session, now: number, kind: any, stock: number, releaseTime: any): string?
	local g = Catch.Game
	if session.state ~= "Aim" then
		return "Поимка уже закончилась"
	end
	if not session.tutorial and session.throws >= g.MaxThrows then
		return "Броски кончились"
	end
	if type(releaseTime) ~= "number" or releaseTime ~= releaseTime then
		return "Бросок не засчитан"
	end
	if releaseTime > now + g.ClockAhead or releaseTime < now - g.ClockSlack then
		return "Бросок не засчитан"
	end
	if releaseTime < session.readyAt or now < session.readyAt then
		return "Подождите"
	end
	if not session.tutorial then
		if not CatchRules.IsKind(kind) then
			return "Нет такого Ловибума"
		end
		if stock < 1 then
			return "Ловибумы этого вида кончились"
		end
	end
	return nil
end

-- Исход броска: промах (без проверки захвата), побег (не повезло с шансом) или поимка. roll — случайное 0…1.
function CatchRules.Outcome(session: Session, hit: boolean, chance: number, roll: number): string
	if not hit then
		return "Miss"
	end
	if session.tutorial or roll < chance then
		return "Caught"
	end
	return "Escape"
end

-- После броска (Ловибум уже списан): счётчик, время, состояние. Поимка — "Caught"; последний бросок без поимки —
-- "Over" (существо убегает, пауза). releaseTime — время отпускания (проверенное CheckThrow): следующий бросок — после
-- прилёта и отдыха (промах) или после сети и побега.
function CatchRules.AfterThrow(session: Session, outcome: string, releaseTime: number)
	local g = Catch.Game
	session.throws += 1
	session.lastThrow = releaseTime
	session.lastActive = releaseTime
	session.readyAt = releaseTime
		+ g.FlightTime
		+ (if outcome == "Miss" then g.MissRest else g.CaptureTime + g.EscapeRest)
	if outcome == "Caught" then
		session.state = "Caught"
	elseif not session.tutorial and session.throws >= Catch.Game.MaxThrows then
		session.state = "Over"
		session.endReason = "Throws"
	end
end

-- Пора ли закончить мини-игру без поимки: причина ("Idle" — бездействие, "Watchdog" — слишком долго, "Empty" — нет
-- Ловибумов этого уровня и бросок не летит) или nil. stockOfLevel — запас уровня босса.
function CatchRules.ShouldEnd(session: Session, now: number, stockOfLevel: number): string?
	if session.state ~= "Aim" then
		return nil
	end
	local g = Catch.Game
	if now - session.since > g.Watchdog then
		return "Watchdog"
	end
	if now - session.lastActive > g.Idle then
		return "Idle"
	end
	if not session.tutorial and stockOfLevel < 1 and now >= session.readyAt then
		return "Empty" -- последний бросок уже долетел и сеть (побег) показана
	end
	return nil
end

-- ── Личная пауза у босса ─────────────────────────────────────────────────────────────────────────────────────

export type Pauses = { [number]: { [number]: number } } -- [UserId][босс] = до какого времени

-- Пауза после любого конца мини-игры без поимки (три неудачи, кончились Ловибумы, выход, прерывание): только у этого
-- игрока и этого босса.
function CatchRules.SetPause(pauses: Pauses, user: number, boss: number, now: number)
	pauses[user] = pauses[user] or {}
	pauses[user][boss] = now + Catch.Game.FailPause
end

-- Сколько секунд паузы осталось (0 — можно).
function CatchRules.PauseLeft(pauses: Pauses, user: number, boss: number, now: number): number
	local byBoss = pauses[user]
	local untilTime = byBoss and byBoss[boss]
	if not untilTime then
		return 0
	end
	local left = untilTime - now
	if left <= 0 then
		byBoss[boss] = nil
		return 0
	end
	return left
end

return CatchRules

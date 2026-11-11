--!strict
-- Правила улучшения музея (D56) без Instance: уровни 1…10, сколько мест открыто, цена следующего уровня, можно ли его
-- купить. Покупается только следующий уровень; в подготовку, Судную ночь и 10 с после неё — нельзя (причину запрета
-- даёт Shared/GameTime.UpgradeLock, сюда она приходит готовой). Читают сервер (MuseumUpgradeService, DataService —
-- проверка) и клиент (окно «Улучшение музея» — состояние кнопки); проверяет scripts/lune/check_museum_upgrade.luau.
-- Зависит только от переданного конфига (GameConfig: Museum.SlotsByLevel, Progression.Museum.Prices).

local MuseumRules = {}

-- Почему уровень не купить (состояние кнопки и ответ сервера).
MuseumRules.Codes = {
	Max = "Max", -- уровень уже последний
	Locked = "Locked", -- подготовка, Судная ночь или 10 с после неё
	Coins = "Coins", -- не хватает монет
	Stale = "Stale", -- запрос не про следующий уровень (повторное нажатие, устаревшее окно, подделка)
	Tutorial = "Tutorial", -- идёт обучение новичка
	Busy = "Busy", -- профиль или участок не готовы
}

MuseumRules.Texts = {
	Max = "Музей уже максимального уровня",
	Coins = "Не хватает монет",
	Stale = "Уровень музея уже изменился",
	Tutorial = "Улучшение музея откроется после обучения",
	Busy = "Музей ещё загружается",
}

-- Последний уровень музея.
function MuseumRules.MaxLevel(config: any): number
	return #config.Museum.SlotsByLevel
end

-- Уровень музея — целое от 1 до последнего.
function MuseumRules.IsLevel(config: any, value: any): boolean
	return type(value) == "number"
		and value == value
		and value == math.floor(value)
		and value >= 1
		and value <= MuseumRules.MaxLevel(config)
end

-- Уровень из профиля в порядке: не число — 1, дробное — вниз, за пределами — ближайший допустимый.
function MuseumRules.Level(config: any, value: any): number
	if type(value) ~= "number" or value ~= value then
		return 1
	end
	return math.clamp(math.floor(value), 1, MuseumRules.MaxLevel(config))
end

-- Сколько мест открыто на уровне level: max(6, 2 × уровень), не больше 20 (GameConfig.Museum.SlotsByLevel).
function MuseumRules.Slots(config: any, level: number): number
	local slots = config.Museum.SlotsByLevel
	return slots[MuseumRules.Level(config, level)]
end

-- Цена перехода с уровня level на следующий. nil — следующего уровня нет (или level — не уровень).
function MuseumRules.Price(config: any, level: any): number?
	if not MuseumRules.IsLevel(config, level) or level >= MuseumRules.MaxLevel(config) then
		return nil
	end
	local price = config.Progression.Museum.Prices[level]
	if type(price) ~= "number" or price ~= price or price <= 0 then
		return nil
	end
	return price
end

-- Можно ли купить следующий уровень: level — уровень сейчас, coins — монеты, lock — причина запрета по фазе (или nil).
-- nil — можно; иначе код из MuseumRules.Codes. Порядок: последний уровень → запрет по фазе → монеты.
function MuseumRules.Check(config: any, level: any, coins: any, lock: string?): string?
	if not MuseumRules.IsLevel(config, level) then
		return MuseumRules.Codes.Stale
	end
	local price = MuseumRules.Price(config, level)
	if not price then
		return MuseumRules.Codes.Max
	end
	if lock then
		return MuseumRules.Codes.Locked
	end
	if type(coins) ~= "number" or coins ~= coins or coins < price then
		return MuseumRules.Codes.Coins
	end
	return nil
end

-- Запрос клиента «хочу уровень requested» годится, только если это ровно следующий уровень после level: второй
-- запрос того же уровня (двойное нажатие, два запроса в одном кадре) после покупки уже не про следующий.
function MuseumRules.IsNext(config: any, level: any, requested: any): boolean
	return MuseumRules.IsLevel(config, level) and MuseumRules.IsLevel(config, requested) and requested == level + 1
end

return MuseumRules

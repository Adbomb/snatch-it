--!strict
-- Правила защиты музея и взлома (D37, D46) без Instance: цены, когда покупать и ставить, сколько устройств, где
-- можно ставить, годится ли устройство взлома. Читают сервер (DefenseService — проверка) и клиент (окно «Защита» —
-- образец зелёный или красный); проверяет scripts/lune/check_defense.luau. Координаты — в осях участка.
-- Зависит только от переданного конфига (GameConfig.Defense).

local DefenseRules = {}

DefenseRules.Types = { "Trap", "Laser", "Door", "Robot", "Snare" }

DefenseRules.Names = {
	Trap = "Ловушка",
	Laser = "Лазер",
	Door = "Усиленная дверь",
	Robot = "Робот-охранник",
	Snare = "Капкан",
}

-- Как ставится (D46): свободно на полу или на фиксированное место.
DefenseRules.Placement = { Trap = "Free", Robot = "Free", Snare = "Free", Door = "Fixed", Laser = "Fixed" }

function DefenseRules.IsType(value: any): boolean
	return type(value) == "string" and DefenseRules.Names[value] ~= nil
end

local function levelOf(level: any): number
	return if type(level) == "number" then math.clamp(math.floor(level), 1, 10) else 1
end

-- Цена устройства взлома для музея уровня level (D37).
function DefenseRules.HackPrice(cfg: any, level: number): number
	return cfg.HackPrices[levelOf(level)]
end

-- Цена устройства защиты для музея уровня level: доля цены взлома того же уровня. nil — не продаётся (цена не
-- утверждена: капкан).
function DefenseRules.Price(cfg: any, kind: string, level: number): number?
	local share = cfg.Share[kind]
	if not share then
		return nil
	end
	return DefenseRules.HackPrice(cfg, level) * share
end

-- Устройств в музее уровня level: min(уровень, MaxDevices) (D37).
function DefenseRules.MaxDevices(cfg: any, level: number): number
	return math.min(levelOf(level), cfg.MaxDevices)
end

-- Можно ли купить устройство защиты. nil — можно.
function DefenseRules.CanBuyDefense(cfg: any, kind: string, phase: string, coins: number, level: number): string?
	if not DefenseRules.IsType(kind) then
		return "Нет такого устройства"
	end
	local price = DefenseRules.Price(cfg, kind, level)
	if not price then
		return "Цена ещё не утверждена"
	end
	if phase ~= "Preparation" then
		return "Защиту покупают и ставят только в подготовку к Судной ночи"
	end
	if coins < price then
		return "Не хватает монет"
	end
	return nil
end

-- Можно ли купить устройство взлома для музея уровня level. nil — можно. Покупают заранее, днём (D37).
function DefenseRules.CanBuyHack(cfg: any, level: any, phase: string, coins: number): string?
	if type(level) ~= "number" or level ~= math.floor(level) or level < 1 or level > #cfg.HackPrices then
		return "Нет такого уровня"
	end
	if phase ~= "Day" then
		return "Устройство взлома покупают заранее, днём"
	end
	if coins < DefenseRules.HackPrice(cfg, level) then
		return "Не хватает монет"
	end
	return nil
end

-- Можно ли поставить устройство kind. installed — уже стоящие в музее (вид → true), owned — сколько куплено.
function DefenseRules.CanInstall(
	cfg: any,
	kind: string,
	phase: string,
	level: number,
	installed: { [string]: any },
	owned: number
): string?
	if not DefenseRules.IsType(kind) then
		return "Нет такого устройства"
	end
	if phase ~= "Preparation" then
		return "Ставить защиту можно только в подготовку к Судной ночи"
	end
	if installed[kind] then
		return "Такое устройство уже стоит — каждого вида только одно"
	end
	local count = 0
	for _ in installed do
		count += 1
	end
	if count >= DefenseRules.MaxDevices(cfg, level) then
		return ("Больше устройств не поставить: %d из %d"):format(
			count,
			DefenseRules.MaxDevices(cfg, level)
		)
	end
	if owned < 1 then
		return "Сначала купите это устройство"
	end
	return nil
end

-- Свободное место на полу зала для ловушки, робота или капкана. showcases и others — точки (оси участка).
-- nil — можно.
function DefenseRules.CheckFreeSpot(
	cfg: any,
	at: Vector3,
	showcases: { Vector3 },
	chest: Vector3,
	others: { Vector3 }
): string?
	local hall = cfg.Hall
	if at.X ~= at.X or at.Z ~= at.Z then
		return "Неверное место"
	end
	if at.X < hall.MinX or at.X > hall.MaxX or at.Z < hall.MinZ or at.Z > hall.MaxZ then
		return "Только на полу своего музея"
	end
	for _, showcase in showcases do
		if math.abs(at.X - showcase.X) < hall.ShowcaseClear and math.abs(at.Z - showcase.Z) < hall.ShowcaseClear then
			return "Нельзя загораживать постаменты"
		end
	end
	if math.abs(at.X) < hall.PassageHalfWidth and at.Z < hall.PassageZ then
		return "Нельзя загораживать вход"
	end
	if math.abs(at.X - chest.X) < hall.ChestClear and math.abs(at.Z - chest.Z) < hall.ChestClear then
		return "Нельзя загораживать сундук"
	end
	for _, other in others do
		if Vector3.new(at.X - other.X, 0, at.Z - other.Z).Magnitude < hall.DeviceGap then
			return "Слишком близко к другому устройству"
		end
	end
	return nil
end

-- Фиксированные места: дверь — «Entrance», лазер — имена из cfg.Lasers. nil — у вида нет фиксированных мест.
function DefenseRules.FixedSpots(cfg: any, kind: string): { string }?
	if kind == "Door" then
		return { "Entrance" }
	elseif kind == "Laser" then
		local names = {}
		for name in cfg.Lasers do
			table.insert(names, name)
		end
		table.sort(names)
		return names
	end
	return nil
end

-- Годится ли устройство взлома уровня deviceLevel для двери музея уровня museumLevel.
function DefenseRules.HackFits(deviceLevel: number, museumLevel: number): boolean
	return deviceLevel >= museumLevel
end

-- Вор в луче лазера: в полосе шириной Width поперёк прохода, под высотой луча.
function DefenseRules.InLaser(cfg: any, laser: any, at: Vector3): boolean
	return math.abs(at.Z - laser.z) <= cfg.Laser.Width / 2 and at.X >= laser.x0 and at.X <= laser.x1
end

-- Установленное устройство списано при установке и привязано к Судной ночи круга cycle (data.defense.installed).
-- При загрузке и выходе: эта ночь ещё не началась (игрок вышел или сервер упал до неё) — вернуть в запас; началась —
-- устройство отработало (выход посреди ночи и вход обратно запас не возвращают). nightStart(cycle) — начало Судной
-- ночи круга.
function DefenseRules.Settle(defense: any, now: number, nightStart: (number) -> number): number
	local returned = 0
	defense.owned = defense.owned or {}
	for kind, cycle in defense.installed or {} do
		if type(cycle) == "number" and now < nightStart(cycle) then
			defense.owned[kind] = (defense.owned[kind] or 0) + 1
			returned += 1
		end
	end
	defense.installed = {}
	return returned
end

return DefenseRules

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

local function inRect(at: Vector3, r: { number }, strict: boolean): boolean
	if strict then
		return at.X > r[1] and at.X < r[2] and at.Z > r[3] and at.Z < r[4]
	end
	return at.X >= r[1] and at.X <= r[2] and at.Z >= r[3] and at.Z <= r[4]
end

-- Свободное место на полу зала для ловушки, робота или капкана (D46, зоны D48-C): только в разрешённых прямоугольниках
-- (боковые проходы, за павильоном) и не в запрещённых; galleries — у музея есть галереи (запрет подходов к аркам).
-- showcases и others — точки (оси участка). nil — можно.
function DefenseRules.CheckFreeSpot(
	cfg: any,
	at: Vector3,
	showcases: { Vector3 },
	chest: Vector3,
	others: { Vector3 },
	galleries: boolean?
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
	local forbidden = hall.Forbidden or {}
	for _, r in forbidden do
		if inRect(at, r, true) then
			return "Нельзя загораживать вход, дорожку и павильон хранилища"
		end
	end
	if galleries then
		for _, r in hall.GalleryForbidden or {} do
			if inRect(at, r, true) then
				return "Нельзя загораживать арки галерей"
			end
		end
	end
	local allowed = false
	for _, r in hall.Allowed or {} do
		allowed = allowed or inRect(at, r, false)
	end
	if hall.Allowed and not allowed then
		return "Ставьте в боковые проходы вдоль павильона или за ним"
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

-- Путь вора за такт проверки (from → to, оси участка) прошёл через луч. Такт сервера длиннее, чем бегущий вор
-- пересекает полосу луча, поэтому проверяется весь отрезок, а не только точка to. from = nil — только точка to
-- (первый такт, перенос).
function DefenseRules.CrossedLaser(cfg: any, laser: any, from: Vector3?, to: Vector3, top: number?): boolean
	local limit = top or math.huge -- top: выше этого (над полом) луч не задевает — перепрыгнул (D52)
	if DefenseRules.InLaser(cfg, laser, to) and to.Y < limit then
		return true
	end
	if not from then
		return false
	end
	local half = cfg.Laser.Width / 2
	local dz = to.Z - from.Z
	local t0, t1 = 0, 1
	if math.abs(dz) < 1e-6 then
		if math.abs(from.Z - laser.z) > half then
			return false
		end
	else
		local a = (laser.z - half - from.Z) / dz
		local b = (laser.z + half - from.Z) / dz
		t0, t1 = math.max(0, math.min(a, b)), math.min(1, math.max(a, b))
		if t0 > t1 then
			return false
		end
	end
	local xa = from.X + (to.X - from.X) * t0
	local xb = from.X + (to.X - from.X) * t1
	local ya = from.Y + (to.Y - from.Y) * t0
	local yb = from.Y + (to.Y - from.Y) * t1
	return math.max(xa, xb) >= laser.x0 and math.min(xa, xb) <= laser.x1 and math.min(ya, yb) < limit
end

-- Путь вора за такт (from → to, оси участка; Y — высота над полом зала) прошёл через зону срабатывания устройства:
-- круг radius вокруг center по полу при высоте меньше height (D52). Высота между проверками — по прямой: прыжок над
-- ловушкой, пойманный в воздухе хоть одной проверкой над зоной, — не касание; бег или телепорт по полу через неё —
-- касание (прямая не выше настоящей дуги прыжка, поэтому перелёт засчитывается только явный). from = nil — точка to.
function DefenseRules.ZoneHit(center: Vector3, radius: number, height: number, from: Vector3?, to: Vector3): boolean
	local cx, cz = center.X, center.Z
	if not from then
		return math.abs(to.Y) < height and (to.X - cx) ^ 2 + (to.Z - cz) ^ 2 <= radius * radius
	end
	local dx, dz = to.X - from.X, to.Z - from.Z
	local fx, fz = from.X - cx, from.Z - cz
	local a = dx * dx + dz * dz
	local c = fx * fx + fz * fz - radius * radius
	local t0, t1 = 0, 1
	if a < 1e-9 then
		if c > 0 then
			return false
		end
	else
		-- доля пути t, на которой расстояние по полу до центра не больше radius: a t² + b t + c ≤ 0
		local b = 2 * (fx * dx + fz * dz)
		local disc = b * b - 4 * a * c
		if disc < 0 then
			return false
		end
		local root = math.sqrt(disc)
		t0, t1 = math.max(0, (-b - root) / (2 * a)), math.min(1, (-b + root) / (2 * a))
		if t0 > t1 then
			return false
		end
	end
	local y0 = from.Y + (to.Y - from.Y) * t0
	local y1 = from.Y + (to.Y - from.Y) * t1
	return y0 * y1 <= 0 or math.min(math.abs(y0), math.abs(y1)) < height
end

-- Ближайшее расстояние по полу от устройства center до пути вора за такт (from → to); from = nil — до точки to.
-- Ловушка и капкан ловят того, кто пробежал через них между проверками.
function DefenseRules.PathDistance(center: Vector3, from: Vector3?, to: Vector3): number
	local cx, cz = center.X, center.Z
	if not from then
		return math.sqrt((to.X - cx) ^ 2 + (to.Z - cz) ^ 2)
	end
	local ax, az = from.X, from.Z
	local dx, dz = to.X - ax, to.Z - az
	local len2 = dx * dx + dz * dz
	local t = if len2 > 1e-9 then math.clamp(((cx - ax) * dx + (cz - az) * dz) / len2, 0, 1) else 0
	return math.sqrt((ax + dx * t - cx) ^ 2 + (az + dz * t - cz) ^ 2)
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

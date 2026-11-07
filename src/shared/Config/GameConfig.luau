-- Общие настройки игры: числа баланса, размеры мира, лимиты запросов.
-- Читается и сервером, и клиентом. Зависит от Config/Progression (числа D29–D31), Config/MuseumLayout (D48-C).

local MuseumLayout = require(script.Parent.MuseumLayout) -- раскладка музея D48-C (места, зоны защиты, лазеры)

local GameConfig = {}

-- Режим разработчика: подробные логи в Output. Перед релизом выключить.
GameConfig.DevMode = true

GameConfig.Data = {
	StoreName = "PlayerData",
	KeyPrefix = "Player_",
	SaveCooldown = 10, -- секунд между внеочередными сохранениями после изменения профиля
	TransferStoreName = "Transfers", -- журнал передачи украденного (DESIGN §6, D46)
}

-- Кража в Судную ночь (D37, D46). Лимиты (1 кража на вора, 1 потеря на музей за событие) и 10 с доставки — D37.
GameConfig.Theft = {
	HoldSeconds = 3, -- удержание «Украсть» (E на ПК, экранная кнопка на телефоне), D46
	HoldTolerance = 0.25, -- запас на сеть при проверке удержания на сервере
	Distance = 7, -- радиус «Украсть» у постамента (стадов; дальше — удержание прерывается)
	SaveTimeout = 20, -- сколько ждать записи профиля при передаче владения
	CheckSeconds = 0.5, -- как часто сервер проверяет, не вышло ли время кражи и доставки
	LiftGrace = 1, -- снятие дольше HoldSeconds + HoldTolerance + LiftGrace (удержание «залипло») — провал
	ConfirmSeconds = 60, -- сколько пытаться подтвердить сохранение жертвы после передачи
}

-- Защита музея и взлом (D37, D46). Утверждено: устройств min(уровень музея, MaxDevices), каждого вида по одному;
-- покупка и установка — только в подготовку, установленное исчезает после Судной ночи, купленное остаётся; цена
-- устройства — доля цены взлома того же уровня; взлом — одноразовое устройство, купленное днём, 5 с, уроном не
-- прерывается, дверь открыта до конца ночи; капкан — 10 с. Расстановка D46 в музее D48-C (зоны утверждены с фазой 1):
-- ловушка, робот и капкан — в боковых проходах вдоль павильона и за ним (Hall.Allowed), не на дорожке, у павильона,
-- открытой двери сейфа, во входной группе, у постаментов, у арок и в галереях (Hall.Forbidden, GalleryForbidden);
-- дверь — на входе, лазер — «Вход» и «Галерея» поперёк дорожки. «В музее» (для двери и устройств) — главный зал и, с
-- уровня Galleries.Level, галереи. Координаты — в осях участка (центр, пол зала, вход −Z; Config/MuseumLayout).
-- ПРЕДВАРИТЕЛЬНО (D37 не утвердил): эффекты ловушки, HP и урон робота, урон лазера; цена капкана не утверждена —
-- капкан не продаётся.
GameConfig.Defense = {
	MaxDevices = 5,
	HackPrices = { 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 1e11, 1e12 }, -- взлом музея уровня 1…10 (D37)
	Share = { Trap = 0.10, Laser = 0.15, Door = 0.20, Robot = 0.30 }, -- доля цены взлома (D37); Snare — нет цены
	HackSeconds = 5,
	Hall = {
		MinX = -MuseumLayout.Hall.InnerX, -- внутренний пол главного зала (до стен)
		MaxX = MuseumLayout.Hall.InnerX,
		MinZ = MuseumLayout.Hall.InnerZ0,
		MaxZ = MuseumLayout.Hall.InnerZ1,
		Allowed = MuseumLayout.Defense.Allowed, -- куда можно (x0, x1, z0, z1)
		Forbidden = MuseumLayout.Defense.Forbidden, -- куда нельзя
		GalleryForbidden = MuseumLayout.Defense.GalleryForbidden, -- ещё нельзя, когда есть галереи
		ShowcaseClear = 4.6, -- от центра постамента (5 × 5) до устройства по каждой оси
		ChestClear = 3.6, -- от центра сундука
		DeviceGap = 4, -- между устройствами
	},
	-- Галереи (с уровня Level) — тоже «в музее»: от стены зала до наружной стены галереи (|x|), по z — внутри.
	Galleries = {
		Level = MuseumLayout.Gallery.Level,
		MinX = MuseumLayout.Hall.InnerX,
		MaxX = MuseumLayout.Gallery.InnerX,
		MinZ = MuseumLayout.Gallery.InnerZ0,
		MaxZ = MuseumLayout.Gallery.InnerZ1,
	},
	Door = { Size = Vector3.new(12, 10, 0.6), At = Vector3.new(0, 5, -12.0) }, -- проём входа (Hall: DoorHalf 6, DoorHeight 10)
	Lasers = { -- лучи поперёк дорожки на высоте y (MuseumLayout.Lasers)
		Entrance = {
			z = MuseumLayout.Lasers.Entrance.z,
			x0 = -MuseumLayout.Lasers.Entrance.length / 2,
			x1 = MuseumLayout.Lasers.Entrance.length / 2,
			y = MuseumLayout.Lasers.Entrance.y,
		},
		Gallery = {
			z = MuseumLayout.Lasers.Gallery.z,
			x0 = -MuseumLayout.Lasers.Gallery.length / 2,
			x1 = MuseumLayout.Lasers.Gallery.length / 2,
			y = MuseumLayout.Lasers.Gallery.y,
		},
	},
	Trap = {
		Radius = 2,
		Damage = 0.2, -- ПРЕДВАРИТЕЛЬНО: доля максимального HP вора
		Effect = "Slow", -- ПРЕДВАРИТЕЛЬНО: "Slow" | "Stun" | "Damage" (D37: варианты в конфиге)
		Slow = 0.5, -- множитель скорости
		SlowSeconds = 3,
		StunSeconds = 2,
		Cooldown = 4, -- секунд до повторного срабатывания на того же вора
	},
	Laser = { Width = 1.2, Damage = 0.1, Cooldown = 2 }, -- ПРЕДВАРИТЕЛЬНО: урон — доля HP
	Robot = { HP = 300, Damage = 12, Interval = 1.2, Radius = 10 }, -- ПРЕДВАРИТЕЛЬНО (D37: не утверждено)
	Snare = { Radius = 1.6, Seconds = 10 }, -- 10 с — D37
	Tick = 0.2, -- как часто сервер проверяет воров у устройств
	TrackStep = 10, -- путь вора за такт длиннее (стадов) — это перенос, а не бег: устройства смотрят только точку
	HackDistance = 13, -- от середины двери до взломщика (стадов)
	DoorEject = Vector3.new(0, 3, -5), -- куда выставить чужого из зала: от двери наружу (оси участка)
	NoticeCooldown = 3, -- секунд между одинаковыми подсказками вору
	HallMargin = 1.2, -- «в зале»: пол зала + запас к стенам (у галерей — тоже)
	HallHeight = Vector2.new(-2, 14), -- «в зале»: высота от пола зала
	TrapHeight = 4, -- ловушка срабатывает, если вор не выше этого над полом
	LaserHeight = 3, -- лазер — если вор не выше луча на столько
	RobotAim = 2.3, -- высота корпуса робота (цель для ударов)
	PushDepth = 2, -- отброс от устройства — к выходу: источник на столько глубже в зал
}

-- PvP в Судную ночь (D37, D46): ручные удары (ЛКМ на ПК, кнопка «Удар» на телефоне), урон и HP — формула игрока из
-- боя с боссом (Config/Battle.Player, частота — AttackInterval, от силы не зависит). Нокаут — D37.
GameConfig.Pvp = {
	KnockSeconds = 15, -- лежит со звёздами, неуязвим, не двигается и не бьёт (D37)
	Range = 7, -- ПРЕДВАРИТЕЛЬНО: кого достаёт удар (стадов, центр — центр)
	FrontDot = -0.2, -- ПРЕДВАРИТЕЛЬНО: цель не за спиной (косинус угла между взглядом и целью)
	SpawnSafeRadius = 24, -- ПРЕДВАРИТЕЛЬНО: Safe Zone у места появления — урона нет (D37; границы не утверждены)
	EffectRadius = 90, -- кому показывать удар и нокаут (стадов)
	SwingTolerance = 0.1, -- запас перезарядки на сети (клиент шлёт не чаще AttackInterval)
}

-- Раскладка карты — в ServerScriptService.Server.World.MapLayout (D35: 5 музеев в линию, впереди уровни).
GameConfig.World = {
	PlotCount = 5, -- D35: до 5 игроков на сервере (Max Players места = 5)
	PlotSize = Vector3.new(44, 1, 44),
	MaxParts = 12000, -- бюджет частей всей карты
}

-- Музей D48-C (утверждено владельцем 2026-11-06): до MaxSlots мест, на уровне L открыто
-- max(SlotsMin, SlotsPerLevel × L) — 6, 6, 6, 8, 10 … 20; раскладка мест — Config/MuseumLayout.
local MUSEUM_SLOTS = { Min = 6, PerLevel = 2, Max = 20, Levels = 10 }
local slotsByLevel = {}
for level = 1, MUSEUM_SLOTS.Levels do
	slotsByLevel[level] = math.min(MUSEUM_SLOTS.Max, math.max(MUSEUM_SLOTS.Min, MUSEUM_SLOTS.PerLevel * level))
end

GameConfig.Museum = {
	SlotsByLevel = slotsByLevel,
	MaxSlots = MUSEUM_SLOTS.Max,
	ShowcaseSize = Vector3.new(5, 3, 5),
	DisplayDistance = 6.5, -- радиус подсказок у постамента: соседний в нише — 7.0 от прохода (не перехватит)
	ChestSize = Vector3.new(4, 3, 3),
	ChestDistance = 10, -- радиус подсказки «В инвентарь» на сундуке
	RotateStep = 45, -- градусов за одно «Повернуть»
	MoveSelectTimeout = 15, -- секунд, через которые выбор «Переставить» отменяется
	-- Графика здания (World/MuseumVisual): "Parts" — временная Part-версия; "Mesh" — модули Blender пачки Pack3_d48
	-- по MeshId из World/MeshModels. У модуля без MeshId — Part-версия, стены и столкновения одинаковы.
	Visual = "Parts",
	-- Хранилище только владельцу (D48-C, Services/VaultService): проверка объёма, куда выставлять чужого (от портала
	-- павильона наружу и над полом), высота барьера в портале, подсказки терминала и центра безопасности.
	Vault = {
		CheckSeconds = 0.25,
		ExitDistance = 3,
		ExitHeight = 3,
		BarrierHeight = 7.2,
		PromptDistance = 7,
		OpensPerSecond = 2,
		NoticeCooldown = 3,
	},
}

-- Модели из Blender (World/MeshBuilder): гантели (D34) и, после импорта, модули музея D48 (World/MuseumVisual).
GameConfig.Models = {
	GlassTransparency = 0.35, -- стекло и кристаллы (то же число в scripts/blender/lego.py для превью)
	AccentDarken = 0.45, -- тёмный оттенок цвета участка (роль AccentDark: крыша, купол)
	DefaultAccent = "2F6FD6", -- цвет участка, если не задан
}

-- Качалка (D31, D34, D36): поле и огромная гантель перед каждым музеем. Сила в секунду и цены уровней —
-- Progression.Dumbbell, сила музея — Progression.MuseumPower.
GameConfig.Gym = {
	TickSeconds = 1, -- как часто владелец в поле получает силу (такт — по общему серверному времени, D51)
	StateCheck = 0.2, -- секунд между проверками «в поле, руки пустые» (гантель в руке появляется и пропадает, D51)
	-- гантель в руке (D51, World/HandDumbbell): модель уровня, уменьшенная до длины Length по грифу; место в осях кисти
	-- R15 (RightHand) и руки R6 (Right Arm): гриф поворотом на 90° — вперёд по кисти (молотковый хват)
	HandDumbbell = {
		Length = 1.7,
		R15Hold = CFrame.new(0, -0.3, 0) * CFrame.Angles(0, math.rad(90), 0),
		R6Hold = CFrame.new(0, -1.1, 0) * CFrame.Angles(0, math.rad(90), 0),
	},
	FieldSize = Vector2.new(12, 12), -- поле качалки перед музеем: по X и Z (D36)
	FieldHeight = 8, -- до какой высоты над полем игрок считается «в поле»
	SignDistance = 12, -- радиус подсказки и кнопки «Улучшить» у таблички
	GuestHintCooldown = 5, -- секунд между подсказками «Это гантель игрока X»
	MaxStrength = 9e15, -- потолок силы (числа ≤ 9e15)
	UpgradesPerSecond = 2, -- лимит запросов «Улучшить» от игрока
}

-- Игровое время (D37): одно на всех серверах — фазу считает Shared/GameTime от общего времени.
GameConfig.Time = {
	DayLength = 300, -- секунд дня
	NightLength = 30, -- обычная ночь
	DoomNightLength = 90, -- Судная ночь (каждая DoomEvery-я)
	PreparationLength = 120, -- подготовка к Судной ночи: последние секунды DoomEvery-го дня (день не удлиняется)
	DoomEvery = 10,
	DeliveryGrace = 10, -- секунд после Судной ночи, чтобы донести уже украденное (D37); новые кражи нельзя
	Epoch = 0, -- Unix-время начала отсчёта кругов (общее для всех серверов)
	TickSeconds = 0.25, -- как часто сервер проверяет смену фазы
	NightCheckSeconds = 0.5, -- как часто ночью сервер выводит игроков из коридора уровней
	SafeSpread = 6, -- разброс точки переноса в Safe Zone вокруг места появления, стадов
}

GameConfig.Carry = {
	-- Скорость — от силы (D24, Progression.Speed); груз умножает её (D24).
	WeightSpeed = { Light = 1, Medium = 0.9, Heavy = 0.8 },
	PickupDistance = 10, -- радиус подсказки «Поднять»
	DropForward = 4, -- на сколько стадов перед собой кладётся брошенный предмет
}

GameConfig.Spawn = {
	-- D10: брошенный предмет, который никто не трогает, исчезает; последние секунды мигает.
	LooseDespawnTime = 60,
	LooseBlinkTime = 10,
	BlinkInterval = 0.25,
	BlinkTransparency = 0.8,
}

-- D22: 10 зон добычи одним коридором без рамок (D41), порядок — от Safe Zone вглубь. boss — имя босса-стража
-- (сила — Progression.Bosses[номер зоны]), floor — цвет пола, accent — цвет голограммы и полосы-границы зоны.
-- mood — смайлик плашки входа в уровень (от доброго к страшному, D41). pattern — узор пола (Config/ZonePatterns):
-- kind, color, tile (стадов на плитку узора), alpha (непрозрачность узора, 0…1).
-- Предметы у боссов — Progression.BossLoot (D37), коллекции — Config/Items.
local function pattern(kind: string, color: string, tile: number, alpha: number)
	return { kind = kind, color = color, tile = tile, alpha = alpha }
end
GameConfig.Zones = {
	{ id = "Junk", name = "Свалка", boss = "Сторожевой пёс", floor = "8C7A60", accent = "8D6E63", mood = "😊",
		pattern = pattern("gravel", "4A3A2A", 11, 0.65) },
	-- Барахолка (D43, D44): пол зоны виден между павильонами, мощение и площадку босса кладёт декор
	-- (World/Models/FleaMarket), узора нет.
	{ id = "Flea", name = "Барахолка", boss = "Торговец-громила", floor = "565D6D", accent = "2CB5A8", mood = "🙂" },
	{ id = "Warehouse", name = "Склад", boss = "Робот-охранник", floor = "90A4AE", accent = "3D8EE0", mood = "😐",
		pattern = pattern("grid", "455A64", 12, 0.55) },
	{ id = "Desert", name = "Пустыня", boss = "Сфинкс", floor = "F2C46D", accent = "E08A1E", mood = "😬",
		pattern = pattern("waves", "D99A3A", 28, 0.38) },
	{ id = "Glacier", name = "Ледник", boss = "Полярный медведь", floor = "DDF3FF", accent = "4FC3F7", mood = "😨",
		pattern = pattern("diamonds", "8FD3F5", 20, 0.45) },
	{ id = "Jungle", name = "Джунгли", boss = "Горилла", floor = "2E8B3A", accent = "1B7A2B", mood = "😠",
		pattern = pattern("tiles", "1E6B2A", 16, 0.45) },
	{ id = "Bank", name = "Банк", boss = "Бронированный охранник", floor = "ECEFF1", accent = "F5A215", mood = "😡",
		pattern = pattern("grid", "D9A21E", 10, 0.7) },
	{ id = "Volcano", name = "Вулкан", boss = "Лавовый голем", floor = "4E342E", accent = "FF5722", mood = "👹",
		pattern = pattern("waves", "FF6A1E", 22, 0.55) },
	{ id = "Spaceport", name = "Космопорт", boss = "Пришелец-генерал", floor = "3B3561", accent = "6A45F5", mood = "😈",
		pattern = pattern("grid", "9B7BFF", 12, 0.75) },
	{ id = "Castle", name = "Замок", boss = "Король-дракон", floor = "9E9E9E", accent = "C62828", mood = "☠️",
		pattern = pattern("tiles", "6E6E6E", 8, 0.4) },
}

-- Боссы (D37, D40, D42): 4 предмета у каждого. Забрать предмет — победой в автобое (BattleService, Config/Battle); у
-- боссов, у которых боя ещё нет (3–10), без боя — только в тестовом режиме Studio (DevMode), в опубликованной игре —
-- нельзя.
GameConfig.Bosses = {
	FreeTakeInStudio = true,
	TakeDistance = 10, -- радиус подсказки «Забрать» у предмета
	TakeHold = 0.5, -- секунды удержания
}

-- D31: качалка — одно поле с огромной гантелью; уровни и сила гантели — Progression.Dumbbell (шаг 4).

-- Презентация экспоната после размещения (UI_KIT.md). 0 — только уведомление.
GameConfig.Presentation = {
	Duration = { Common = 0, Rare = 0, Epic = 1.5, Legendary = 3, Secret = 4 }, -- секунды
	ViewerRadius = 60, -- другие игроки в этом радиусе видят прожектор и название
	LightHeight = 10, -- прожектор над верхом витрины, стадов
	LightRange = 18,
	LightAngle = 40,
	LightBrightness = 6,
	LiftHeight = 1.5, -- подъём экспоната у владельца, стадов
	SpinTurns = 1, -- оборотов за презентацию
	TitleHeight = 3, -- название над верхом экспоната, стадов
	TitleSize = UDim2.fromOffset(320, 110),
	TitleMaxDistance = 120,
}

-- Звуки. Пустая строка — звук не играет. Asset id выбирает дизайнер, сюда вписывает его.
GameConfig.Sounds = {
	Presentation = { Rare = "", Legendary = "", Secret = "" }, -- презентация экспоната по редкости
	Place = "", -- любое выставление (и Common)
}

-- Запас к дистанции на сервере: позиция игрока на сервере слегка отстаёт от клиента.
GameConfig.DistanceTolerance = 4

-- Подсказка с удержанием («Украсть», «Взломать»): Roblox на сервере шлёт конец удержания раньше Triggered, поэтому
-- отпускание считается отменой, только если за ReleaseGrace секунд не пришёл Triggered (Util/Prompts.BindHold).
GameConfig.HoldRelease = {
	ReleaseGrace = 0.3,
}

-- Не чаще N запросов в секунду на игрока.
GameConfig.RateLimits = {
	Pickup = 4,
	Display = 4,
	Drop = 4,
	Storage = 4,
	Move = 4,
	Rotate = 6,
	Steal = 4,
	PvpAttack = 4, -- запросов удара в секунду (сама частота ударов — Battle.Player.AttackInterval)
}

-- Долгая прогрессия (D29–D31): боссы, гантель, музей, сила музея, доход, редкость, каталог, скорость.
-- Отдельный файл, чтобы его читал симулятор scripts/sim/progression.py.
GameConfig.Progression = require(script.Parent.Progression)

return GameConfig

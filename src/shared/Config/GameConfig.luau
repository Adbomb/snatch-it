-- Общие настройки игры: числа баланса, размеры мира, лимиты запросов.
-- Читается и сервером, и клиентом. Зависит от Config/Progression (числа D29–D31).

local GameConfig = {}

-- Режим разработчика: подробные логи в Output. Перед релизом выключить.
GameConfig.DevMode = true

GameConfig.Data = {
	StoreName = "PlayerData",
	KeyPrefix = "Player_",
	SaveCooldown = 10, -- секунд между внеочередными сохранениями после изменения профиля
}

-- Раскладка карты — в ServerScriptService.Server.World.MapLayout (D35: 5 музеев в линию, впереди уровни).
GameConfig.World = {
	PlotCount = 5, -- D35: до 5 игроков на сервере (Max Players места = 5)
	PlotSize = Vector3.new(44, 1, 44),
	MaxParts = 12000, -- бюджет частей всей карты
}

GameConfig.Museum = {
	SlotsByLevel = { [1] = 6 }, -- DESIGN.md §2: museumLevel 1 → 6 витрин
	ShowcaseSize = Vector3.new(5, 3, 5),
	ShowcaseStep = Vector2.new(10, 14), -- шаг сетки витрин по X и Z (влезает в самый узкий зал)
	DisplayDistance = 6.5, -- радиус подсказок на витринах: у канатов ≈ 5; от сундука до витрины 1 — 8.5 (не перехватит)
	StorageCapacity = 10, -- мест в хранилище
	ChestSize = Vector3.new(4, 3, 3),
	ChestDistance = 10, -- радиус подсказки «В хранилище» на сундуке
	RotateStep = 45, -- градусов за одно «Повернуть»
	MoveSelectTimeout = 15, -- секунд, через которые выбор «Переставить» отменяется
}

-- Модели из Blender (World/MeshBuilder): гантели (D34). Музеи строятся кодом (World/Models/MuseumHall, D36).
GameConfig.Models = {
	GlassTransparency = 0.35, -- стекло и кристаллы (то же число в scripts/blender/lego.py для превью)
	AccentDarken = 0.45, -- тёмный оттенок цвета участка (роль AccentDark: крыша, купол)
	DefaultAccent = "2F6FD6", -- цвет участка, если не задан
}

-- Качалка (D31, D34, D36): поле и огромная гантель перед каждым музеем. Сила в секунду и цены уровней —
-- Progression.Dumbbell, сила музея — Progression.MuseumPower.
GameConfig.Gym = {
	TickSeconds = 1, -- как часто владелец в поле получает силу
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
	RespawnDelay = 30, -- секунд от освобождения точки до нового предмета
	-- D10: брошенный предмет, который никто не трогает, исчезает; последние секунды мигает.
	LooseDespawnTime = 60,
	LooseBlinkTime = 10,
	BlinkInterval = 0.25,
	BlinkTransparency = 0.8,
}

-- D22: 10 зон добычи одним коридором, порядок — от ворот аллеи вглубь. boss — имя босса-стража
-- (сила — Progression.Bosses[номер зоны]), floor — цвет пола, accent — цвет ворот и вывески.
-- Шансы редкости — Progression.RarityFirst → RarityLast по номеру зоны, Secret — с SecretFromZone.
GameConfig.Zones = {
	{ id = "Junk", name = "Свалка", boss = "Сторожевой пёс", floor = "A1887F", accent = "8D6E63" },
	{ id = "Flea", name = "Барахолка", boss = "Торговец-громила", floor = "F3D9A4", accent = "43C22E" },
	{ id = "Warehouse", name = "Склад", boss = "Робот-охранник", floor = "90A4AE", accent = "3D8EE0" },
	{ id = "Desert", name = "Пустыня", boss = "Сфинкс", floor = "F2C46D", accent = "E08A1E" },
	{ id = "Glacier", name = "Ледник", boss = "Полярный медведь", floor = "DDF3FF", accent = "4FC3F7" },
	{ id = "Jungle", name = "Джунгли", boss = "Горилла", floor = "2E8B3A", accent = "1B7A2B" },
	{ id = "Bank", name = "Банк", boss = "Бронированный охранник", floor = "ECEFF1", accent = "F5A215" },
	{ id = "Volcano", name = "Вулкан", boss = "Лавовый голем", floor = "4E342E", accent = "FF5722" },
	{ id = "Spaceport", name = "Космопорт", boss = "Пришелец-генерал", floor = "3B3561", accent = "6A45F5" },
	{ id = "Castle", name = "Замок", boss = "Король-дракон", floor = "9E9E9E", accent = "C62828" },
}

-- Сколько лежащих или несомых предметов редкости может быть на всём сервере одновременно.
GameConfig.MaxOnMap = { Legendary = 3, Secret = 1 }

-- D31: качалка — одно поле с огромной гантелью; уровни и сила гантели — Progression.Dumbbell (шаг 4).

-- Презентация экспоната после размещения (UI_KIT.md). 0 — только уведомление.
GameConfig.Presentation = {
	Duration = { Common = 0, Uncommon = 0, Rare = 1.5, Legendary = 3, Secret = 4 }, -- секунды
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

-- Не чаще N запросов в секунду на игрока.
GameConfig.RateLimits = {
	Pickup = 4,
	Display = 4,
	Drop = 4,
	Storage = 4,
	Move = 4,
	Rotate = 6,
}

-- Долгая прогрессия (D29–D31): боссы, гантель, музей, сила музея, доход, редкость, каталог, скорость.
-- Отдельный файл, чтобы его читал симулятор scripts/sim/progression.py.
GameConfig.Progression = require(script.Parent.Progression)

return GameConfig

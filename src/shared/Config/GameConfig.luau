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

-- Раскладка карты — в ServerScriptService.Server.World.MapLayout (D12).
GameConfig.World = {
	PlotCount = 8,
	PlotSize = Vector3.new(44, 1, 44),
	MaxParts = 12000, -- бюджет частей всей карты
}

GameConfig.Museum = {
	SlotsByLevel = { [1] = 6 }, -- DESIGN.md §2: museumLevel 1 → 6 витрин
	ShowcaseSize = Vector3.new(5, 3, 5),
	ShowcaseStep = Vector2.new(10, 14), -- шаг сетки витрин по X и Z (влезает в самый узкий зал)
	DisplayDistance = 10, -- радиус подсказок на витринах
	StorageCapacity = 10, -- мест в хранилище
	ChestSize = Vector3.new(4, 3, 3),
	ChestDistance = 10, -- радиус подсказки «В хранилище» на сундуке
	RotateStep = 45, -- градусов за одно «Повернуть»
	MoveSelectTimeout = 15, -- секунд, через которые выбор «Переставить» отменяется
}

-- Модели из Blender (World/MeshBuilder, D33): музей уровня L — модель ceil(L / 2), на чётных уровнях с декором.
GameConfig.Models = {
	MuseumModelCount = 5, -- Museum1 … Museum5
	GlassTransparency = 0.35, -- стекло и кристаллы (то же число в scripts/blender/lego.py для превью)
	AccentDarken = 0.45, -- тёмный оттенок цвета участка (роль AccentDark: крыша, купол)
	DefaultAccent = "2F6FD6", -- цвет участка, если не задан (гантель в качалке)
}

GameConfig.Carry = {
	NormalWalkSpeed = 16, -- DESIGN.md §4
	SpeedByWeight = { Light = 14, Medium = 12, Heavy = 10 }, -- DESIGN.md §4
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

-- Общие настройки игры: числа баланса, размеры мира, лимиты запросов.
-- Читается и сервером, и клиентом. Ни от чего не зависит.

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
	WallHeight = 8,
	MaxParts = 12000, -- бюджет частей всей карты
}

GameConfig.Museum = {
	SlotsByLevel = { [1] = 6 }, -- DESIGN.md §2: museumLevel 1 → 6 витрин
	ShowcaseSize = Vector3.new(5, 3, 5),
	DisplayDistance = 10, -- радиус подсказок на витринах
	StorageCapacity = 10, -- мест в хранилище
	ChestSize = Vector3.new(4, 3, 3),
	ChestDistance = 10, -- радиус подсказки «В хранилище» на сундуке
	RotateStep = 45, -- градусов за одно «Повернуть»
	MoveSelectTimeout = 15, -- секунд, через которые выбор «Переставить» отменяется
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
	MaxLegendaryOnMap = 1, -- лежащих или в руках на всём сервере
}

-- D15: зоны добычи. Порядок — от ворот аллеи вглубь (Свалка ближе всех, Банк дальше всех).
-- rarity — главная редкость зоны (цвет вывески), weights — веса редкостей предметов,
-- guard — страж и его сила (бой — D16). Secret не появляется нигде.
GameConfig.Zones = {
	{
		id = "Junk",
		name = "Свалка",
		rarity = "Common",
		weights = { Common = 100 },
		guard = { name = "Сторожевой пёс", strength = 0 },
	},
	{
		id = "Flea",
		name = "Барахолка",
		rarity = "Uncommon",
		weights = { Common = 40, Uncommon = 60 },
		guard = { name = "Торговец-громила", strength = 100 },
	},
	{
		id = "Warehouse",
		name = "Склад",
		rarity = "Rare",
		weights = { Uncommon = 40, Rare = 60 },
		guard = { name = "Робот-охранник", strength = 1500 },
	},
	{
		id = "Bank",
		name = "Банк",
		rarity = "Legendary",
		weights = { Rare = 70, Legendary = 30 },
		guard = { name = "Бронированный охранник", strength = 25000 },
	},
}

-- D17: гантели спортзала. price в монетах (этап 3); пока монет нет, платные закрыты табличкой «Скоро».
GameConfig.Gym = {
	Dumbbells = {
		{ id = "Wood", name = "Деревянная", power = 1, price = 0 },
		{ id = "Iron", name = "Железная", power = 5, price = 500 },
		{ id = "Gold", name = "Золотая", power = 25, price = 5000 },
		{ id = "Diamond", name = "Алмазная", power = 100, price = 50000 },
	},
}

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

return GameConfig

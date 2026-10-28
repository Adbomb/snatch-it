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

GameConfig.World = {
	PlazaSize = Vector3.new(60, 1, 60),
	PlotCount = 8,
	PlotRadius = 90, -- расстояние от центра площади до центра участка
	PlotSize = Vector3.new(44, 1, 44),
	WallHeight = 8,
	-- Платформы-«крыши» на окраинах для точек Far: угол (градусы), расстояние от центра, размер.
	Roofs = {
		{ angle = 67.5, radius = 130, size = Vector3.new(14, 5, 14) },
		{ angle = 157.5, radius = 130, size = Vector3.new(16, 9, 16) },
		{ angle = 247.5, radius = 130, size = Vector3.new(18, 12, 18) },
	},
	StepHeight = 4.5, -- максимальный подъём между ступеньками (прыжок берёт ~7 стадов)
	StepSize = Vector2.new(6, 4), -- ширина и глубина ступеньки
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
	-- D11: веса редкостей по типу точки. Secret на этапе 2 не появляется.
	TierWeights = {
		Near = { Common = 100, Uncommon = 0, Rare = 0, Legendary = 0 },
		Center = { Common = 70, Uncommon = 25, Rare = 5, Legendary = 0 },
		Far = { Common = 20, Uncommon = 45, Rare = 30, Legendary = 5 },
	},
	DefaultTier = "Center", -- точка без атрибута Tier
	MaxLegendaryOnMap = 1, -- лежащих или в руках на всём сервере
	-- Раскладка 12 точек, если в мире нет ни одной с тегом ItemSpawn.
	CenterCount = 4,
	CenterRadius = 18, -- на площади
	NearCount = 4,
	NearRadius = 64, -- между площадью и входами в музеи
	FarGroundAngle = 337.5, -- четвёртая точка Far: на земле за музеями
	FarGroundRadius = 140,
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

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
}

GameConfig.Museum = {
	SlotsByLevel = { [1] = 6 }, -- DESIGN.md §2: museumLevel 1 → 6 витрин
	ShowcaseSize = Vector3.new(5, 3, 5),
	DisplayDistance = 10, -- радиус подсказки «Выставить»
}

GameConfig.Carry = {
	NormalWalkSpeed = 16, -- DESIGN.md §4
	SpeedByWeight = { Light = 14, Medium = 12, Heavy = 10 }, -- DESIGN.md §4
	PickupDistance = 10, -- радиус подсказки «Поднять»
	DropForward = 4, -- на сколько стадов перед собой кладётся брошенный предмет
}

GameConfig.Spawn = {
	RespawnDelay = 30, -- секунд от освобождения точки до нового предмета
	DefaultPointCount = 6, -- сколько точек создать, если в мире нет ни одной с тегом ItemSpawn
	DefaultPointRadius = 18, -- радиус круга точек на площади
}

-- Запас к дистанции на сервере: позиция игрока на сервере слегка отстаёт от клиента.
GameConfig.DistanceTolerance = 4

-- Не чаще N запросов в секунду на игрока.
GameConfig.RateLimits = {
	Pickup = 4,
	Display = 4,
	Drop = 4,
}

return GameConfig

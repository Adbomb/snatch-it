-- Справочник предметов: id → название, редкость, вес и внешний вид заглушки (DESIGN.md §4).
-- Заглушки различаются формой Part, цветом и размером. Читается сервером и клиентом. Ни от чего не зависит.

export type ItemDef = {
	id: string,
	displayName: string,
	rarity: string, -- Common | Uncommon | Rare | Legendary | Secret (см. Config/Rarities)
	weight: string, -- Light | Medium | Heavy
	shape: string, -- Enum.PartType: Block | Ball | Cylinder | Wedge (у Ball размер берётся по X)
	color: Color3,
	size: Vector3,
	material: Enum.Material?, -- по умолчанию Plastic (LEGO-пупырышки); Neon — для свечения
}

local Items: { [string]: ItemDef } = {
	OldBoot = {
		id = "OldBoot",
		displayName = "Старый ботинок",
		rarity = "Common",
		weight = "Light",
		shape = "Wedge",
		color = Color3.fromRGB(110, 78, 50),
		size = Vector3.new(1.6, 1.2, 2.6),
	},
	Mug = {
		id = "Mug",
		displayName = "Кружка",
		rarity = "Common",
		weight = "Light",
		shape = "Cylinder",
		color = Color3.fromRGB(235, 235, 245),
		size = Vector3.new(1.6, 1.4, 1.4),
	},
	AlarmClock = {
		id = "AlarmClock",
		displayName = "Будильник",
		rarity = "Common",
		weight = "Light",
		shape = "Ball",
		color = Color3.fromRGB(220, 60, 60),
		size = Vector3.new(1.8, 1.8, 1.8),
	},
	RubberDuck = {
		id = "RubberDuck",
		displayName = "Резиновая уточка",
		rarity = "Common",
		weight = "Light",
		shape = "Ball",
		color = Color3.fromRGB(255, 220, 40),
		size = Vector3.new(1.4, 1.4, 1.4),
	},
	DancingCactus = {
		id = "DancingCactus",
		displayName = "Танцующий кактус",
		rarity = "Uncommon",
		weight = "Medium",
		shape = "Block",
		color = Color3.fromRGB(60, 160, 70),
		size = Vector3.new(1.2, 3.2, 1.2),
	},
	FluffySlipper = {
		id = "FluffySlipper",
		displayName = "Пушистая тапка",
		rarity = "Uncommon",
		weight = "Light",
		shape = "Wedge",
		color = Color3.fromRGB(255, 150, 200),
		size = Vector3.new(1.4, 0.9, 2.4),
	},
	NeonTV = {
		id = "NeonTV",
		displayName = "Неоновый телевизор",
		rarity = "Rare",
		weight = "Heavy",
		shape = "Block",
		color = Color3.fromRGB(255, 0, 200),
		size = Vector3.new(4, 3, 1.5),
		material = Enum.Material.Neon,
	},
	JetFridge = {
		id = "JetFridge",
		displayName = "Реактивный холодильник",
		rarity = "Rare",
		weight = "Heavy",
		shape = "Block",
		color = Color3.fromRGB(150, 210, 255),
		size = Vector3.new(2.4, 4.2, 2.2),
	},
	TalkingSafe = {
		id = "TalkingSafe",
		displayName = "Говорящий сейф",
		rarity = "Rare",
		weight = "Heavy",
		shape = "Block",
		color = Color3.fromRGB(70, 75, 85),
		size = Vector3.new(2.6, 2.6, 2.6),
	},
	StarMeteorite = {
		id = "StarMeteorite",
		displayName = "Звёздный метеорит",
		rarity = "Legendary",
		weight = "Heavy",
		shape = "Ball",
		color = Color3.fromRGB(255, 190, 40),
		size = Vector3.new(3, 3, 3),
		material = Enum.Material.Neon,
	},
}

return Items

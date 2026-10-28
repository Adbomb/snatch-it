-- Справочник предметов: id → название, редкость, вес, цвет, размер (DESIGN.md §4).
-- Читается сервером и клиентом. Ни от чего не зависит. Этап 1: 4 тестовых предмета.

export type ItemDef = {
	id: string,
	displayName: string,
	rarity: string, -- Common | Uncommon | Rare | Legendary (пока ни на что не влияет)
	weight: string, -- Light | Medium | Heavy
	color: Color3,
	size: Vector3,
}

local Items: { [string]: ItemDef } = {
	OldBoot = {
		id = "OldBoot",
		displayName = "Старый ботинок",
		rarity = "Common",
		weight = "Light",
		color = Color3.fromRGB(110, 78, 50),
		size = Vector3.new(1.6, 1.2, 2.6),
	},
	Mug = {
		id = "Mug",
		displayName = "Кружка",
		rarity = "Common",
		weight = "Light",
		color = Color3.fromRGB(235, 235, 245),
		size = Vector3.new(1.4, 1.6, 1.4),
	},
	AlarmClock = {
		id = "AlarmClock",
		displayName = "Будильник",
		rarity = "Common",
		weight = "Light",
		color = Color3.fromRGB(220, 60, 60),
		size = Vector3.new(1.8, 1.8, 1),
	},
	NeonTV = {
		id = "NeonTV",
		displayName = "Неоновый телевизор",
		rarity = "Rare",
		weight = "Heavy",
		color = Color3.fromRGB(255, 0, 200),
		size = Vector3.new(4, 3, 1.5),
	},
}

return Items

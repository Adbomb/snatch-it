-- Меши предметов из Blender (V3): модели собираются из LEGO-кирпичей скриптами scripts/blender/*.py,
-- экспортируются в assets/models/*.fbx и импортируются в Studio (File → Import 3D). Здесь — ID, которые
-- выдал импорт, размер меша в файле и масштаб в игре. Предмета нет в списке — он остаётся простым Part.
-- Ни от чего не зависит.

export type ItemModel = {
	mesh: string, -- rbxassetid меша
	texture: string, -- rbxassetid текстуры-палитры (assets/textures/item_palette.png)
	meshSize: Vector3, -- размер меша после импорта, стадов
	scale: number, -- во сколько раз уменьшить в игре
	material: Enum.Material, -- SmoothPlastic: пупырышки у модели свои, из геометрии
}

return {
	RubberDuck = {
		mesh = "rbxassetid://91115944871956",
		texture = "rbxassetid://103158563600468",
		meshSize = Vector3.new(5.98, 6.18, 7.98),
		scale = 0.3,
		material = Enum.Material.SmoothPlastic,
	},
} :: { [string]: ItemModel }

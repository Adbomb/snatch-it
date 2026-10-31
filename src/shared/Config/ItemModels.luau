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

-- Пилотная уточка (хлам) удалена вместе с хламом (D37); модели произведений — этап 7.
return {} :: { [string]: ItemModel }

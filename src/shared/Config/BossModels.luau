-- Модели боссов из Blender (D40): у каждой части свой меш (импорт FBX в Studio даёт MeshId), карты SurfaceAppearance
-- общие на группу частей (голова и тело, assets/textures/art/IDS.md). turn — поворот меша частей вокруг вертикали
-- после импорта, чтобы он совпал со скелетом. Нет меша у части — часть показывается заготовкой (блок цвета из
-- скелета) до импорта. Скелет и позы — Config/Boss<N>…Rig. Ни от чего не зависит.

export type BossModel = {
	name: string,
	maps: { [string]: { color: string, normal: string } },
	meshes: { [string]: string },
	turn: number,
}

local ROUGHNESS = "rbxassetid://120633114716941"

-- MeshId частей пса из импорта Boss1_Dog.fbx: заполняется после импорта в Studio.
local DOG_MESHES: { [string]: number } = {}

local function ids(list: { [string]: number }): { [string]: string }
	local out = {}
	for part, id in list do
		out[part] = "rbxassetid://" .. id
	end
	return out
end

return table.freeze({
	Roughness = ROUGHNESS,
	[1] = {
		name = "Сторожевой пёс",
		maps = {
			Head = { color = "rbxassetid://114075578064919", normal = "rbxassetid://72281207474806" },
			Body = { color = "rbxassetid://94835517459826", normal = "rbxassetid://94675390063511" },
		},
		meshes = ids(DOG_MESHES),
		turn = 0,
	} :: BossModel,
})

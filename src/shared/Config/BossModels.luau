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

-- MeshId частей пса из импорта Boss1_Dog.fbx (владелец, 2026-11-02; assets/models/Boss1_meshids.json).
-- Импорт повернул меши на 180° вокруг вертикали — turn = 180.
local DOG_MESHES: { [string]: number } = {
	BLowerL = 137250136190249,
	BLowerR = 124331422196767,
	BUpperL = 104633290669632,
	BUpperR = 125922436330102,
	EarL = 106455314556039,
	EarR = 139039230448770,
	EyelidL = 90682315510664,
	EyelidR = 102060066850738,
	FLowerL = 119589483306303,
	FLowerR = 103144601510934,
	FUpperL = 89740211608879,
	FUpperR = 76645415165349,
	Head = 132977355807397,
	Jaw = 85791501528323,
	Tail = 106766032217885,
	Torso = 103252526545154,
}

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
		turn = 180,
	} :: BossModel,
})

-- Модели боссов из Blender (D40): у каждой части свой меш (импорт FBX в Studio даёт MeshId), карты SurfaceAppearance
-- общие на группу частей (голова и тело, assets/textures/art/IDS.md). turn — поворот меша частей вокруг вертикали
-- после импорта, чтобы он совпал со скелетом. Нет меша у части — часть показывается заготовкой (блок цвета из
-- скелета) до импорта. Скелет и позы — Config/Boss<N>…Rig (1 — пёс, 2 — торговец, 3 — Крысиный король). Ни от чего
-- не зависит.

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

-- MeshId частей торговца — после импорта Boss2_Trader.fbx (scripts/bind_meshes.py). Пока пусто — части-заготовки
-- цвета из скелета (Config/Boss2TraderRig).
local TRADER_MESHES: { [string]: number } = {}

-- Крысиный король (D54): FBX и карты лежат локально (assets/models/Boss3_RatKing.fbx), импорт и загрузка пока запрещены
-- владельцем — части-заготовки цвета из скелета (Config/Boss3RatKingRig).
local RATKING_MESHES: { [string]: number } = {}

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
	-- Карты торговца загружены до бана аккаунта (2026-11-02, assets/textures/art/IDS.md).
	[2] = {
		name = "Торговец-громила",
		maps = {
			Head = { color = "rbxassetid://111835541987471", normal = "rbxassetid://95234991557771" },
			Body = { color = "rbxassetid://88982407819751", normal = "rbxassetid://111891368383392" },
			Limbs = { color = "rbxassetid://126025887496516", normal = "rbxassetid://71574604601669" },
		},
		meshes = ids(TRADER_MESHES),
		turn = 180,
	} :: BossModel,
	-- D55: бой Крысиного короля подключён на материалах D54; карт в Roblox нет (не загружались).
	[3] = {
		name = "Крысиный король",
		maps = {},
		meshes = ids(RATKING_MESHES),
		turn = 180,
	} :: BossModel,
})

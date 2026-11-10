-- Модели произведений искусства (D39, D40): меш из Blender (импорт FBX в Studio даёт MeshId) и карты
-- SurfaceAppearance (загружены, assets/textures/art/IDS.md). size — габариты модели в игре (оси Roblox), turn — поворот
-- меша вокруг вертикали после импорта, чтобы лицо смотрело вперёд (−Z, LookVector). Нет mesh — меш ещё не загружен,
-- предмет показывается заготовкой из Config/Items. Исходники: scripts/blender/art_wonders.py, assets/models/art/.
-- Ни от чего не зависит.

export type ItemModel = {
	mesh: string?, -- rbxassetid меша; nil — FBX ещё не импортирован
	color: string, -- ColorMap
	normal: string, -- NormalMap
	size: Vector3,
	turn: number?, -- градусов вокруг Y
}

-- Шероховатость у всех предметов D39 общая (константа 0.5).
local ROUGHNESS = "rbxassetid://120633114716941"

local V = Vector3.new

local function model(color: number, normal: number, size: Vector3): ItemModel
	return {
		mesh = nil,
		color = "rbxassetid://" .. color,
		normal = "rbxassetid://" .. normal,
		size = size,
		turn = 0,
	}
end

local ItemModels: { [string]: ItemModel } = {
	Moai = model(105253304964317, 120032926441846, V(2, 3.05, 1.59)),
	EgyptianCat = model(94947747747723, 95772578879363, V(1.24, 2.45, 1.55)),
	AnubisStatue = model(137440016885164, 121294058519368, V(1.24, 2.628, 1.92)),
	TerracottaWarrior = model(114796888736421, 122260531476182, V(1.2, 2.8, 1.15)),
	MiniStonehenge = model(80149207675845, 73650756357876, V(3.1, 1.68, 3.1)),
	TriceratopsSkull = model(133225519991661, 127260356018558, V(2.611, 2.669, 3.309)),
	EgyptianSarcophagus = model(128131075096087, 77861039156361, V(1.24, 2.62, 1.09)),
	GladiatorHelmet = model(88385745895259, 73391772408638, V(1.84, 2.66, 1.84)),
	Sunflowers = model(131105502255082, 92755479414938, V(3.2, 4.56, 1.285)),
	GreatWave = model(80731527570741, 126741554085708, V(4.04, 3.98, 1.285)),
	PearlEarring = model(136037848067182, 114861412054144, V(3.1, 4.64, 1.285)),
	TheScream = model(80503607696065, 117083610159219, V(3.1, 4.64, 1.285)),
	GreatSphinx = model(134797811982324, 84154981701716, V(1.9, 1.7, 3.16)),
	NefertitiBust = model(95805399568175, 84332980255120, V(1.24, 2.112, 1.04)),
	GizaPyramids = model(133525199780651, 133504341060199, V(3.2, 1.24, 2.64)),
	Colosseum = model(76009389052440, 90605462607478, V(3.56, 1.515, 2.88)),
	StarryNight = model(73838980548932, 101463536355680, V(3.7, 3.98, 1.285)),
	StatueOfLiberty = model(112148975514927, 93478835262330, V(1.9, 4.326, 1.94)),
	TRexSkeleton = model(99458752211442, 134574151071110, V(3.866, 2.04, 1.28)),
	TutMask = model(85785727862394, 132482211480983, V(2.1, 2.82, 1.59)),
}

-- MeshId из импорта Art_Boss1_MuseumOfWonders.fbx (владелец, 2026-11-02; assets/models/Boss1_meshids.json).
-- Лицо модели смотрит вдоль LookVector корня (−Z, как принято в Roblox): импорт повернул меши на 180°, и лицо
-- как раз в −Z меша — turn = 0. У босса LookVector слота смотрит к входу зоны, у витрины — к входу в музей.
local MESHES: { [string]: number } = {
	AnubisStatue = 72471382385582,
	Colosseum = 130691704356145,
	EgyptianCat = 77547660556391,
	EgyptianSarcophagus = 72167735231107,
	GizaPyramids = 121300305001766,
	GladiatorHelmet = 116895933236713,
	GreatSphinx = 94641147537472,
	GreatWave = 101238889976695,
	MiniStonehenge = 99952358954292,
	Moai = 103135057319657,
	NefertitiBust = 114408460945483,
	PearlEarring = 140488510279558,
	StarryNight = 108672604205460,
	StatueOfLiberty = 89914358189856,
	Sunflowers = 128458988572967,
	TRexSkeleton = 118278022347551,
	TerracottaWarrior = 77073529408916,
	TheScream = 94029497308524,
	TriceratopsSkull = 81000202521326,
	TutMask = 76920497781136,
}

for itemId, meshId in MESHES do
	ItemModels[itemId].mesh = "rbxassetid://" .. meshId
end

-- Существа босса 3 (D54, D55): у каждой части свой меш — MeshId из импорта assets/models/art/<id>.fbx (объекты
-- Art_<id>_<Часть>; вписывает scripts/bind_meshes.py, ключ «<id>_<Часть>»), карты — одна пара на предмет (запись
-- <id> = model(…) выше, шаблон Looks/<id>). Пока пусто — существа показываются Part-версией (Config/CreatureRigs,
-- рабочий резерв: тег git d55-creatures-parts-v1); у части без меша — её блоки. Импорт поворачивает меши на 180°
-- вокруг вертикали от скелета (как у пса) — CREATURE_TURN. ForceCreatureParts = true — всегда Part-версия.
local CREATURE_MESHES: { [string]: number } = {}
local CREATURE_TURN = 180

local creatures: { [string]: { [string]: string } } = {}
for key, meshId in CREATURE_MESHES do
	local itemId, part = string.match(key, "^(%w+)_(%w+)$")
	if itemId and part then
		creatures[itemId] = creatures[itemId] or {}
		creatures[itemId][part] = "rbxassetid://" .. meshId
	end
end

return table.freeze({
	Models = ItemModels,
	Roughness = ROUGHNESS,
	Creatures = creatures, -- [предмет][часть] = rbxassetid меша
	CreatureTurn = CREATURE_TURN,
	ForceCreatureParts = false,
})

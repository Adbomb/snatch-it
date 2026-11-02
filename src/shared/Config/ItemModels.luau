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

-- MeshId из импорта (Art_Boss1_MuseumOfWonders.fbx): заполняется после импорта в Studio.
local MESHES: { [string]: number } = {}

for itemId, meshId in MESHES do
	ItemModels[itemId].mesh = "rbxassetid://" .. meshId
end

return table.freeze({
	Models = ItemModels,
	Roughness = ROUGHNESS,
})

-- СГЕНЕРИРОВАНО scripts/d48_to_luau.py из scripts/blender/d48c_layout.py и
-- assets/concepts/d48/c2/mesh_placement.json — руками не править.
-- Раскладка музея D48-C (утверждена владельцем 2026-11-06): главный зал с 8 нишами, две галереи по 6 мест (с
-- уровня Gallery.Level), павильон и лестница в хранилище, сундук, лазеры, зоны защиты, модули Blender по уровням.
-- Оси участка: начало — центр участка на уровне пола зала, вход в −Z, x+ — левая рука входящего. Ни от чего не
-- зависит.

export type Place = { slot: number, zone: string, center: Vector3, face: Vector3, unlock: number }
export type Module = { model: string, position: Vector3, yaw: number, from: number, to: number }

local MuseumLayout = {}

-- Главный зал: полуширина, фасад и задняя грань, толщина стен, потолок, проём входа (полуширина, высота), трава
-- и плита пола (от пола зала), передний край портика.
MuseumLayout.Hall = {
	HalfWidth = 18,
	Front = -12.7,
	Back = 20.7,
	Wall = 1.4,
	InnerX = 16.6,
	InnerZ0 = -11.3,
	InnerZ1 = 19.3,
	Ceiling = 16,
	DoorHalf = 6,
	DoorHeight = 10,
	Ground = -1.3,
	Slab = 1.4,
	Portico = -23,
}

-- Павильон над лестницей (портал спереди, z0) и лестница: верх у TopZ, ступени 1 × 1 вниз к +z, проём в полу.
MuseumLayout.Pavilion = {
	HalfX = 4.4,
	Z0 = 2.4,
	Z1 = 11.6,
	Height = 9,
}
MuseumLayout.Stair = {
	TopZ = 3,
	HalfWidth = 2.6,
	Steps = 12,
	WellX = 2.8,
	WellZ1 = 11,
}
-- Хранилище под главным залом: пол и низ потолка (от пола зала), по плану — контур зала.
MuseumLayout.Vault = {
	Floor = -13,
	Ceiling = -1.8,
}

-- Галереи (места 9–20) с уровня Level: от стены зала (In) до наружной стены (Out), фасад Z0, арка из входного
-- зала, клумба снаружи (x0, x1, высота).
MuseumLayout.Gallery = {
	In = 18,
	Out = 29,
	Z0 = -19,
	Z1 = 20.7,
	Height = 10.4,
	InnerX = 27.6,
	InnerZ0 = -17.6,
	InnerZ1 = 19.3,
	Eave = 29.4,
	Planter = { 29, 31.4, 1.6 },
	Arch = { Z0 = -10.8, Z1 = -6, Height = 8 },
	Level = 5,
	Z = { -8.45, -2.35, -14.55, 3.75, 9.85, 15.95 },
	Inset = 2.9,
}

-- Ниши главного зала (по 4 у боковой стены) и пилястры между ними.
MuseumLayout.Niche = {
	Z = { -2, 4.1, 10.2, 16.3 },
	Pilasters = { -5.05, 1.05, 7.15, 13.25 },
	Inset = 3.2,
}

-- Постамент: верх Top × Top на высоте Height (GameConfig.Museum.ShowcaseSize), основание Base.
MuseumLayout.Showcase = { Top = 5, Base = 5.4, Height = 3 }

-- Места 1–20: центр постамента на полу, куда смотрит его лицо (в проход), уровень открытия max(6, 2 × уровень).
MuseumLayout.Places = {
	{ slot = 1, zone = "Hall", center = Vector3.new(13.4, 0, -2), face = Vector3.new(-1, 0, 0), unlock = 1 },
	{ slot = 2, zone = "Hall", center = Vector3.new(-13.4, 0, -2), face = Vector3.new(1, 0, 0), unlock = 1 },
	{ slot = 3, zone = "Hall", center = Vector3.new(13.4, 0, 4.1), face = Vector3.new(-1, 0, 0), unlock = 1 },
	{ slot = 4, zone = "Hall", center = Vector3.new(-13.4, 0, 4.1), face = Vector3.new(1, 0, 0), unlock = 1 },
	{ slot = 5, zone = "Hall", center = Vector3.new(13.4, 0, 10.2), face = Vector3.new(-1, 0, 0), unlock = 1 },
	{ slot = 6, zone = "Hall", center = Vector3.new(-13.4, 0, 10.2), face = Vector3.new(1, 0, 0), unlock = 1 },
	{ slot = 7, zone = "Hall", center = Vector3.new(13.4, 0, 16.3), face = Vector3.new(-1, 0, 0), unlock = 4 },
	{ slot = 8, zone = "Hall", center = Vector3.new(-13.4, 0, 16.3), face = Vector3.new(1, 0, 0), unlock = 4 },
	{ slot = 9, zone = "Gallery", center = Vector3.new(24.7, 0, -8.45), face = Vector3.new(-1, 0, 0), unlock = 5 },
	{ slot = 10, zone = "Gallery", center = Vector3.new(-24.7, 0, -8.45), face = Vector3.new(1, 0, 0), unlock = 5 },
	{ slot = 11, zone = "Gallery", center = Vector3.new(24.7, 0, -2.35), face = Vector3.new(-1, 0, 0), unlock = 6 },
	{ slot = 12, zone = "Gallery", center = Vector3.new(-24.7, 0, -2.35), face = Vector3.new(1, 0, 0), unlock = 6 },
	{ slot = 13, zone = "Gallery", center = Vector3.new(24.7, 0, -14.55), face = Vector3.new(-1, 0, 0), unlock = 7 },
	{ slot = 14, zone = "Gallery", center = Vector3.new(-24.7, 0, -14.55), face = Vector3.new(1, 0, 0), unlock = 7 },
	{ slot = 15, zone = "Gallery", center = Vector3.new(24.7, 0, 3.75), face = Vector3.new(-1, 0, 0), unlock = 8 },
	{ slot = 16, zone = "Gallery", center = Vector3.new(-24.7, 0, 3.75), face = Vector3.new(1, 0, 0), unlock = 8 },
	{ slot = 17, zone = "Gallery", center = Vector3.new(24.7, 0, 9.85), face = Vector3.new(-1, 0, 0), unlock = 9 },
	{ slot = 18, zone = "Gallery", center = Vector3.new(-24.7, 0, 9.85), face = Vector3.new(1, 0, 0), unlock = 9 },
	{ slot = 19, zone = "Gallery", center = Vector3.new(24.7, 0, 15.95), face = Vector3.new(-1, 0, 0), unlock = 10 },
	{ slot = 20, zone = "Gallery", center = Vector3.new(-24.7, 0, 15.95), face = Vector3.new(1, 0, 0), unlock = 10 },
} :: { Place }

-- Сундук (центр на полу, замок смотрит в Face) и стенд музея у входа.
MuseumLayout.Chest = { Center = Vector3.new(-9, 0, -9.7), Face = Vector3.new(0, 0, 1) }
MuseumLayout.Stand = { Center = Vector3.new(9, 0, -9.6) }

-- Лазеры поперёк прохода: z, длина луча, высота.
MuseumLayout.Lasers = {
	Entrance = { z = -8.6, length = 12, y = 2.4 },
	Gallery = { z = -6.4, length = 9.2, y = 2.4 },
}

-- Зоны защиты на полу (x0, x1, z0, z1): ловушка, робот и капкан — только в Allowed и не в Forbidden;
-- GalleryForbidden добавляется с уровня Gallery.Level (подходы к аркам и сами галереи).
MuseumLayout.Defense = {
	Allowed = {
		{ -10.2, -5, -4.5, 18.8 },
		{ 5, 10.2, -4.5, 18.8 },
		{ -4.6, 4.6, 12.2, 18.8 },
	},
	Forbidden = {
		{ -3.6, 3.6, -11.3, 2.4 },
		{ -4.8, 4.8, 2, 12 },
		{ 4.4, 5.6, -5, 2.6 },
		{ -7.5, 7.5, -11.3, -5 },
		{ 8.8, 18, -6.6, 2.6 },
		{ -18, -8.8, -6.6, 2.6 },
		{ 8.8, 18, -0.5, 8.7 },
		{ -18, -8.8, -0.5, 8.7 },
		{ 8.8, 18, 5.6, 14.8 },
		{ -18, -8.8, 5.6, 14.8 },
		{ 8.8, 18, 11.7, 20.9 },
		{ -18, -8.8, 11.7, 20.9 },
	},
	GalleryForbidden = {
		{ -16.6, -10.6, -11.3, -5 },
		{ -27.6, -18, -17.6, 19.3 },
		{ 10.6, 16.6, -11.3, -5 },
		{ 18, 27.6, -17.6, 19.3 },
	},
}

-- Модули Blender (пачка Pack3_d48) по уровням музея: модель, место, поворот (градусы вокруг y), уровни from…to.
MuseumLayout.Modules = {
	{ model = "D48_Hall", position = Vector3.new(0, 0, 0), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Roof", position = Vector3.new(0, 0, 0), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Pavilion", position = Vector3.new(0, 0, 0), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Stair", position = Vector3.new(0, 0, 0), yaw = 0, from = 1, to = 10 },
	{ model = "D48_VaultShell", position = Vector3.new(0, 0, 0), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Safe", position = Vector3.new(0, -8, 19.3), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Terminal", position = Vector3.new(0, -13, 3), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Security", position = Vector3.new(0, -13, 0), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Archive", position = Vector3.new(-16.35, -13, -6), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Archive", position = Vector3.new(-16.35, -13, 9), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Lockers", position = Vector3.new(-11.9, -13, -11.3), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Lockers", position = Vector3.new(4, -13, -11.3), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Chest", position = Vector3.new(-9, 0, -9.7), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Stand", position = Vector3.new(9, 0, -9.6), yaw = 0, from = 1, to = 10 },
	{ model = "D48_GateLeaf", position = Vector3.new(-2.58, 0, 2.7), yaw = 0, from = 1, to = 10 },
	{ model = "D48_GateLeaf", position = Vector3.new(2.58, 0, 2.7), yaw = 180, from = 1, to = 10 },
	{ model = "D48_Scanner", position = Vector3.new(-3.45, 2.6, 2.25), yaw = 0, from = 1, to = 10 },
	{ model = "D48_SideClosed_L", position = Vector3.new(0, 0, 0), yaw = 0, from = 1, to = 4 },
	{ model = "D48_SideClosed_R", position = Vector3.new(0, 0, 0), yaw = 0, from = 1, to = 4 },
	{ model = "D48_Plinth", position = Vector3.new(13.4, 0, -2), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(-13.4, 0, -2), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(13.4, 0, 4.1), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(-13.4, 0, 4.1), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(13.4, 0, 10.2), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(-13.4, 0, 10.2), yaw = 0, from = 1, to = 10 },
	{ model = "D48_Urn", position = Vector3.new(13.4, 0, 16.3), yaw = 0, from = 1, to = 3 },
	{ model = "D48_Urn", position = Vector3.new(-13.4, 0, 16.3), yaw = 0, from = 1, to = 3 },
	{ model = "D48_Plinth", position = Vector3.new(13.4, 0, 16.3), yaw = 0, from = 4, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(-13.4, 0, 16.3), yaw = 0, from = 4, to = 10 },
	{ model = "D48_SideArch_L", position = Vector3.new(0, 0, 0), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Gallery_L", position = Vector3.new(0, 0, 0), yaw = 0, from = 5, to = 10 },
	{ model = "D48_GalleryRoof_L", position = Vector3.new(0, 0, 0), yaw = 0, from = 5, to = 10 },
	{ model = "D48_SideArch_R", position = Vector3.new(0, 0, 0), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Gallery_R", position = Vector3.new(0, 0, 0), yaw = 0, from = 5, to = 10 },
	{ model = "D48_GalleryRoof_R", position = Vector3.new(0, 0, 0), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(24.7, 0, -8.45), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(-24.7, 0, -8.45), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(24.7, 0, -2.35), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(-24.7, 0, -2.35), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(24.7, 0, -14.55), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(-24.7, 0, -14.55), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(24.7, 0, 3.75), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(-24.7, 0, 3.75), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(24.7, 0, 9.85), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(-24.7, 0, 9.85), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(24.7, 0, 15.95), yaw = 0, from = 5, to = 10 },
	{ model = "D48_Plinth", position = Vector3.new(-24.7, 0, 15.95), yaw = 0, from = 5, to = 10 },
} :: { Module }

return MuseumLayout

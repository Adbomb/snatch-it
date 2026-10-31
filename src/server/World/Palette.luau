-- Цвета мира в стиле LEGO (D13, D36): спокойный зелёный, светлая архитектура, тёплый коричневый в меру.
-- Ни от чего не зависит.

local function rgb(hex: string): Color3
	return Color3.fromHex(hex)
end

local Palette = {
	Water = rgb("3DB4FF"),
	Stone = rgb("A7ADB8"),
	Wood = rgb("8A5A2B"),
	WoodDark = rgb("5E3A1A"),
	Trunk = rgb("7A4A22"),
	Leaves = { rgb("5FAE45"), rgb("4F9C3C"), rgb("74BD58") },
	Bush = rgb("37B23A"),
	Metal = rgb("6B7280"),
	Lamp = rgb("FFE08A"),
	White = rgb("FFFFFF"),
	Black = rgb("1B1530"),
	Glass = rgb("BFE6FF"),
	-- Яркие цвета для мелких деталей (табло, стены зон).
	HouseWalls = { rgb("E53935"), rgb("FDD835"), rgb("1E88E5"), rgb("FB8C00") },
	-- Полосатые навесы ларьков: пары цветов.
	Awnings = {
		{ rgb("2EBD4E"), rgb("FFFFFF") },
		{ rgb("E53935"), rgb("FFFFFF") },
		{ rgb("1E88E5"), rgb("FFFFFF") },
		{ rgb("FFB300"), rgb("FFFFFF") },
	},
	-- Карта D36 (цвета сняты с референса заказчика и приглушены).
	Field = rgb("7FC75A"), -- трава безопасной зоны и коридора уровней
	CliffDirt = rgb("D4B07E"), -- земля обрывов: светлая бежево-коричневая
	CliffGrass = rgb("6CB84C"), -- трава поверх обрывов: чуть темнее поля, край читается
	MuseumWall = rgb("F3EFE6"),
	MuseumTrim = rgb("E0D9CA"), -- цоколь, карнизы, ступени, потолок
	MuseumColumn = rgb("FAF7F0"),
	MuseumFloor = rgb("E6DFD0"),
	MuseumGlass = rgb("A9D8F0"),
	MuseumGold = rgb("D9B45A"), -- позолота старших уровней
	FieldFloor = rgb("ECE6D8"), -- пол поля качалки
	SignBoard = rgb("1E2A4A"), -- табло с текстом
	AccentShade = rgb("6B5B53"), -- к нему приглушается цвет участка (Palette.Muted)
	RoofShade = rgb("A39689"), -- к нему сильнее приглушается цвет участка на крышах (Palette.Roof)
	-- Цвета мешей из Blender под палитру карты (hex меша → цвет в игре): деревянная гантель светлее и теплее.
	MeshColors = {
		A0682F = rgb("C49A68"),
		["6B4423"] = rgb("9C7048"),
		C8945A = rgb("E3C89C"),
		C9A86A = rgb("EADBB4"),
	},
}

-- Цвет участка в приглушённом виде: акценты музея (крыша, фриз, эмблема) и плитки поля качалки.
function Palette.Muted(accent: Color3): Color3
	return accent:Lerp(Palette.AccentShade, 0.3)
end

-- Крыша: большая площадь, поэтому цвет участка только оттенком.
function Palette.Roof(accent: Color3): Color3
	return accent:Lerp(Palette.RoofShade, 0.55)
end

return Palette

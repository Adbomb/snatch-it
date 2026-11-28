-- Темы зон трассы броска (D75, решение владельца 2026-11-28): у каждой зоны свои стены каньона, трава уступов, цвет
-- пола и то, что стоит у стен; середина трассы пустая. Начало — зелень, как на снимках референса; дальше зоны
-- заметно разные: Пустыня — песок и кактусы, Ледник — лёд и снег, Джунгли — густая листва, Банк — тёмный мрамор и
-- золото; у зон 8–10 пока только цвет (свет зон — Config/ZoneAtmosphere у клиента). Только данные и кирпичи декора;
-- строит World/WorldBuilder.buildTrack. Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick
local hex = Color3.fromHex

local TrackThemes = {}

export type Theme = {
	floor: Color3, -- две клетки пола
	light: Color3,
	wall: Color3, -- стены каньона и клетка на них
	tile: Color3,
	grass: Color3, -- верх уступов, свесы и натёки
	kind: string, -- что стоит у стен: trees | jungle | cacti | ice | bank | none
	leaf: Color3?, -- листва деревьев
	leaf2: Color3?,
}

local function theme(floor, light, wall, tile, grass, kind, leaf, leaf2): Theme
	return {
		floor = hex(floor),
		light = hex(light),
		wall = hex(wall),
		tile = hex(tile),
		grass = hex(grass),
		kind = kind,
		leaf = if leaf then hex(leaf) else nil,
		leaf2 = if leaf2 then hex(leaf2) else nil,
	}
end

local THEMES: { [string]: Theme } = {
	Junk = theme("6FD44A", "82E05C", "A86C42", "6E4022", "4EC326", "trees", "4FCB1E", "63D62C"), -- зелень, как на снимках
	Flea = theme("4FB8A8", "63C8B8", "9A5A3C", "6A3A22", "8ACB3A", "trees", "F0A23A", "F7C24A"), -- осенняя листва
	Subway = theme("8C8F9A", "A0A3AE", "6F7480", "50545E", "7E8894", "trees", "2E8F7A", "3BA58C"), -- камень, тёмная зелень
	Desert = theme("E3BC6A", "EECB80", "D9A860", "B98444", "E8C883", "cacti"),
	Glacier = theme("BFE6F5", "DDF3FB", "9CCFE8", "74B4D6", "F4FAFF", "ice"),
	Jungle = theme("3FA33A", "4DB446", "5E5A34", "3F3D22", "2F8F2A", "jungle", "2FA02A", "45B838"),
	Bank = theme("2B2E3A", "3A3E4C", "30333F", "1E2029", "3A3D47", "bank"),
	Volcano = theme("5A3430", "6A4038", "4A2A26", "2E1816", "5A3430", "none"),
	Spaceport = theme("56628A", "6672A0", "3A4460", "262E44", "56628A", "none"),
	Castle = theme("7A7690", "8C88A2", "5A5670", "3E3A52", "7A7690", "none"),
}

-- Тема зоны по её id (GameConfig.Zones); неизвестная — зелень.
function TrackThemes.Of(zoneId: string): Theme
	return THEMES[zoneId] or THEMES.Junk
end

-- Дерево с широкой кроной из кубов (как на снимках референса): толстый ствол из блоков, наверху два-три больших
-- куба листвы со сдвигом. size: "S" — у стен каньона, "L" — на уступах. Начало координат — центр низа ствола.
function TrackThemes.Tree(size: string, leaf: Color3, leaf2: Color3): { ModelBuilder.Brick }
	if size == "L" then
		return {
			B(Vector3.new(3.6, 3, 3.6), Vector3.new(0, 1.5, 0), Palette.Trunk),
			B(Vector3.new(2.8, 9, 2.8), Vector3.new(0, 7.5, 0), Palette.WoodDark),
			B(Vector3.new(10, 9, 10), Vector3.new(0.6, 16.5, 0.4), leaf),
			B(Vector3.new(7, 6, 7), Vector3.new(-5.2, 12.6, 1.8), leaf2),
			B(Vector3.new(6, 5, 6), Vector3.new(5, 12.2, -2.2), leaf2),
			B(Vector3.new(5, 4, 5), Vector3.new(-0.8, 22.6, -0.6), leaf),
		}
	end
	return {
		B(Vector3.new(2.6, 2.4, 2.6), Vector3.new(0, 1.2, 0), Palette.Trunk),
		B(Vector3.new(2, 5.6, 2), Vector3.new(0, 5.2, 0), Palette.WoodDark),
		B(Vector3.new(7, 6, 7), Vector3.new(0.4, 10.8, 0.3), leaf),
		B(Vector3.new(5, 4, 5), Vector3.new(-3.4, 8.2, 1.2), leaf2),
		B(Vector3.new(4, 3.4, 4), Vector3.new(3, 7.8, -1.6), leaf2),
	}
end

local CACTUS, CACTUS2 = hex("3FA34D"), hex("4DB85C")
local ROCK = hex("C99A52")
local ICE, ICE2, SNOW = hex("BFE9FB"), hex("9AD6F2"), hex("F4FAFF")
local MARBLE, MARBLE2, GOLD = hex("30333F"), hex("454957"), hex("F0BC3C")

-- Кактус: ствол и две руки разной высоты.
function TrackThemes.Cactus(): { ModelBuilder.Brick }
	return {
		B(Vector3.new(2, 8, 2), Vector3.new(0, 4, 0), CACTUS),
		B(Vector3.new(2.6, 1.4, 1.4), Vector3.new(-2.3, 4.2, 0), CACTUS2),
		B(Vector3.new(1.4, 3.2, 1.4), Vector3.new(-2.9, 6.5, 0), CACTUS2),
		B(Vector3.new(2.4, 1.4, 1.4), Vector3.new(2.2, 5.6, 0), CACTUS2),
		B(Vector3.new(1.4, 2.4, 1.4), Vector3.new(2.7, 7.5, 0), CACTUS2),
		B(Vector3.new(4, 1.6, 3), Vector3.new(0.5, 0.8, 3.4), ROCK),
	}
end

-- Ледяные глыбы со снежным сугробом.
function TrackThemes.Ice(): { ModelBuilder.Brick }
	return {
		B(Vector3.new(3, 7, 3), Vector3.new(0, 3.5, 0), ICE),
		B(Vector3.new(2, 4.4, 2), Vector3.new(0.4, 9.2, 0.3), ICE2),
		B(Vector3.new(2.2, 4.6, 2.2), Vector3.new(-2.8, 2.3, 1.2), ICE2),
		B(Vector3.new(7, 1.6, 5), Vector3.new(1, 0.8, -3.6), SNOW),
		B(Vector3.new(4.4, 1.4, 3.2), Vector3.new(1.6, 2.3, -3.8), SNOW),
	}
end

-- Колонна тёмного мрамора с золотом и стопка слитков.
function TrackThemes.Vault(): { ModelBuilder.Brick }
	return {
		B(Vector3.new(3.8, 1, 3.8), Vector3.new(0, 0.5, 0), MARBLE2),
		B(Vector3.new(2.6, 9, 2.6), Vector3.new(0, 5.5, 0), MARBLE),
		B(Vector3.new(3.2, 0.6, 3.2), Vector3.new(0, 3.2, 0), GOLD),
		B(Vector3.new(3.4, 0.9, 3.4), Vector3.new(0, 10.45, 0), GOLD),
		B(Vector3.new(4.4, 1, 1.8), Vector3.new(0.5, 0.5, 4), GOLD),
		B(Vector3.new(4.4, 1, 1.8), Vector3.new(0.5, 0.5, 6), GOLD),
		B(Vector3.new(4.4, 1, 1.8), Vector3.new(0.5, 1.5, 5), GOLD),
	}
end

return TrackThemes

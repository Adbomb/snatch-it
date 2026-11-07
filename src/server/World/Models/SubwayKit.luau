-- Набор «Подземки» (D54): цвета станции и мелкие вещи, из которых собраны большие части (World/Models/SubwayParts)
-- и сам уровень (World/Models/SubwayStation). Палитра: синий кафель с кремовыми полосами, светлый бетон перрона,
-- жёлтая линия безопасности, красные вагоны, фиолетовый ковёр короля с золотом, тёплые лампы — ярко, не мрачно.
-- Общие помощники (брусок, диск, неон, табличка с надписью, монеты, мешки, сундук) — из набора «Барахолки»
-- (World/Models/FleaKit): у двух уровней одни правила деталей и один список надписей. Вещь — функция кирпичей в
-- своих координатах: начало — центр низа, лицо — сторона −Z. Совпадающих граней нет (D36). Без Random.
-- Зависит от ModelBuilder, Palette, World/Models/FleaKit, World/Models/Props.

local ServerScriptService = game:GetService("ServerScriptService")

local World = ServerScriptService.Server.World
local FleaKit = require(World.Models.FleaKit)
local Palette = require(World.Palette)
local Props = require(World.Models.Props)

type Brick = FleaKit.Brick

local B, V = FleaKit.B, FleaKit.V
local Box, Disc, Neon = FleaKit.Box, FleaKit.Disc, FleaKit.Neon
local DECOR, ROUND, BALL = FleaKit.DECOR, FleaKit.ROUND, FleaKit.BALL

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

local SubwayKit = {}

-- Общее с «Барахолкой».
SubwayKit.B, SubwayKit.V = B, V
SubwayKit.Box, SubwayKit.Disc, SubwayKit.Round, SubwayKit.Neon = Box, Disc, FleaKit.Round, Neon
SubwayKit.Board, SubwayKit.Label, SubwayKit.Put, SubwayKit.Gem = FleaKit.Board, FleaKit.Label, FleaKit.Put, FleaKit.Gem
SubwayKit.Sack, SubwayKit.GoldChest = FleaKit.Sack, FleaKit.GoldChest
SubwayKit.Suitcases, SubwayKit.CoinSacks = FleaKit.Suitcases, FleaKit.CoinSacks
SubwayKit.Reset, SubwayKit.Signs, SubwayKit.With = FleaKit.Reset, FleaKit.Signs, FleaKit.With
SubwayKit.DECOR, SubwayKit.ROUND, SubwayKit.BALL = DECOR, ROUND, BALL
SubwayKit.UPRIGHT, SubwayKit.ALONG_Z, SubwayKit.TURN = FleaKit.UPRIGHT, FleaKit.ALONG_Z, FleaKit.TURN
SubwayKit.ALONG_X = CFrame.new() -- цилиндр Roblox и так лежит осью вдоль X
-- Мягкие квадратные пупырышки (D36: шахматка едва заметна) — на больших поверхностях станции (плиты перронов, кафель
-- стен, навес): одинаковый рельеф на огромных плоскостях рябил (уточнение D54 по просьбе владельца).
SubwayKit.SOFT = "LegoSquaresSoft"
SubwayKit.FLOOR = FleaKit.With(DECOR, { variant = SubwayKit.SOFT })

SubwayKit.C = {
	tile = hex("2F6DB5"), -- кафель стен
	tileDark = hex("1F4E8A"),
	tileLight = hex("5B92D6"),
	tunnel = hex("18365E"), -- глубина тоннеля: тёмно-синяя, не чёрная
	tunnelDeep = hex("0F2442"),
	-- Светлые тона приглушены (просьба владельца после рендеров): в дневном свете Roblox (Brightness 3, Bloom) кремовый,
	-- светлый бетон и золото засвечивались почти до белого (как D9C8A5 у «Барахолки», D45).
	cream = hex("DCCB9E"), -- кремовые полосы кафеля, свод (было EFE3C2)
	creamDark = hex("C4B289"),
	concrete = hex("A39D91"), -- перрон (было B9B2A6)
	concreteMid = hex("968F83"), -- вторая тональность плит перрона
	concreteDark = hex("88827A"),
	concreteSide = hex("9A9488"), -- боковые платформы
	granite = hex("6F6A63"), -- кайма перрона у жёлтой линии
	seam = hex("6A645B"),
	yellow = hex("E8B41C"), -- линия безопасности
	gravel = hex("6E6258"),
	gravelDark = hex("5A4F47"),
	sleeper = hex("6B4A32"),
	rail = hex("A7AFBA"),
	railDark = hex("6E7682"),
	red = hex("D8352A"), -- вагоны
	redDark = hex("A82820"),
	wagonCream = hex("E2D2AE"),
	roof = hex("AEB5C0"),
	window = hex("F3C060"), -- окна светятся тёплым
	interior = hex("3A2E3A"),
	purple = hex("6B3FB8"), -- ковёр короля
	purpleDark = hex("4E2A8C"),
	purpleLight = hex("9B6BE0"),
	velvet = hex("C2263A"), -- подушки-подстилки предметов
	gold = hex("E0A824"), -- золото глубже: не слепит (было F2C230)
	goldDark = hex("B5821E"),
	goldLight = hex("EEC040"), -- было FFE27A
	lamp = hex("FFA63A"), -- тёплые лампы
	lampLight = hex("FFCC70"), -- шары-лампы теплее, без белого ореола (было FFE2A0)
	green = hex("3DDC84"),
	signal = hex("FF4D4D"),
	iron = hex("5A6170"), -- крышка люка, металл
	ironDark = hex("3E4450"),
	metal = hex("8C95A3"),
	graphite = hex("3A3F4B"),
	pipeRed = hex("C0392B"),
	pipeTeal = hex("2CB5A8"),
	ratFur = hex("8790B0"), -- крысята-статисты: шерсть как у короля
	ratPink = hex("F49AB0"),
	foil = hex("D9DEE6"), -- корона из фольги
	paper = hex("E2DACA"),
	spot = hex("FFF1C9"), -- свет прожекторов
	wood = Palette.Wood,
	woodDark = Palette.WoodDark,
	white = Palette.White,
}
local C = SubwayKit.C

-- Монета, лежащая на полу (толщина задаёт высоту верха: у соседних монет разная), золото «Подземки».
function SubwayKit.Coin(x: number, z: number, thickness: number, size: number?): Brick
	local d = size or 0.9
	return B(V(thickness, d, d), CFrame.new(x, thickness / 2, z) * FleaKit.UPRIGHT, C.gold, ROUND)
end

-- Колесо с осью вдоль X (вагоны, дрезина, вагонетки): центр at, диаметр d, толщина t.
function SubwayKit.Wheel(at: Vector3, d: number, t: number): Brick
	return B(V(t, d, d), CFrame.new(at), C.ironDark, ROUND)
end

-- Крысёнок-статист (декор, ≈ 3.2 стада): серый, с розовыми ушами и хвостом, корона из фольги. Лицо — −Z.
function SubwayKit.RatMinion(): { Brick }
	local out = {
		Box(-0.7, 0.7, 0, 1.6, -0.55, 0.65, C.ratFur, DECOR), -- тело
		Box(-0.5, 0.5, 0.25, 1.3, -0.62, -0.5, C.wagonCream, DECOR), -- брюшко
		Box(-0.65, 0.65, 1.55, 2.6, -0.7, 0.5, C.ratFur, DECOR), -- голова
		Box(-0.36, 0.36, 1.62, 2.18, -1.25, -0.65, C.wagonCream, DECOR), -- мордочка
		Box(-0.16, 0.16, 1.98, 2.28, -1.4, -1.2, C.ratPink, DECOR), -- нос
		Box(-1, 1, 2.7, 2.85, -0.35, 0.35, C.foil, DECOR), -- обруч короны
	}
	for _, s in { -1, 1 } do
		table.insert(out, Box(s * 0.42 - 0.1, s * 0.42 + 0.1, 2.15, 2.42, -0.76, -0.68, C.graphite, DECOR)) -- глаз
		local ear = CFrame.new(s * 0.62, 2.85, -0.05) * CFrame.Angles(0, 0, s * 0.35) * FleaKit.ALONG_Z
		table.insert(out, B(V(0.2, 1.1, 1.1), ear, C.ratPink, ROUND)) -- круглое ухо лицом вперёд
		table.insert(out, Box(s * 0.75 - 0.15, s * 0.75 + 0.15, 2.84, 3.35, -0.12, 0.12, C.gold, DECOR)) -- зубец
	end
	table.insert(out, Box(-0.15, 0.15, 2.84, 3.45, -0.12, 0.12, C.gold, DECOR))
	table.insert(
		out,
		B(
			V(1.6, 0.26, 0.26),
			CFrame.new(0, 0.35, 1.25) * CFrame.Angles(0, math.rad(80), math.rad(25)),
			C.ratPink,
			DECOR
		)
	)
	return out
end

-- Ящик: Props.Crate (как на «Свалке») — деревянный короб с рейками.
SubwayKit.Crate = Props.Crate

-- Скамейка вдоль X длиной len: сиденье, спинка, ножки. Лицо — −Z.
function SubwayKit.Bench(len: number): { Brick }
	local out = {
		Box(-len / 2, len / 2, 1.4, 1.8, -0.9, 0.9, C.wood),
		Box(-len / 2, len / 2, 1.8, 3.3, 0.7, 1.05, C.wood, DECOR),
	}
	for _, x in { -len / 2 + 0.6, len / 2 - 0.6 } do
		table.insert(out, Box(x - 0.25, x + 0.25, 0, 1.45, -0.7, 0.8, C.graphite))
	end
	return out
end

-- Мелкий мусор на полу: газеты, банки, бутылка, коробка — лежат, а не «натыканы».
function SubwayKit.Litter(): { Brick }
	return {
		B(V(1.6, 0.06, 1.1), CFrame.new(0, 0.03, 0) * CFrame.Angles(0, 0.4, 0), C.paper, DECOR),
		B(V(1.4, 0.05, 1), CFrame.new(0.8, 0.075, 0.5) * CFrame.Angles(0, -0.3, 0), C.creamDark, DECOR),
		B(V(0.9, 0.5, 0.5), CFrame.new(-1.4, 0.25, 0.6) * CFrame.Angles(0, 0.9, 0), C.pipeRed, ROUND),
		B(V(0.9, 0.5, 0.5), CFrame.new(1.8, 0.25, -0.9) * CFrame.Angles(0, -0.5, 0), C.pipeTeal, ROUND),
		B(V(1.3, 0.45, 0.45), CFrame.new(-0.6, 0.225, -1.3) * CFrame.Angles(0, 0.2, 0), C.green, ROUND),
		B(V(1.1, 0.7, 0.9), CFrame.new(2.4, 0.35, 1) * CFrame.Angles(0, 0.6, 0), C.creamDark, DECOR),
	}
end

-- Шар-лампа на кронштейне (без света, Neon): кронштейн вдоль −Z длиной arm, шар диаметра d.
function SubwayKit.GlobeLamp(arm: number, d: number): { Brick }
	return {
		Box(-0.2, 0.2, -0.2, 0.2, -arm, 0, C.graphite, DECOR),
		Box(-0.35, 0.35, -0.55, -0.15, -arm - 0.35, -arm + 0.35, C.goldDark, DECOR),
		B(
			V(d, d, d),
			V(0, -0.55 - d / 2, -arm),
			C.lampLight,
			{ shape = "Ball", material = Enum.Material.Neon, collide = false, shadow = false }
		),
	}
end

return SubwayKit

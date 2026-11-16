-- «Храм спящего Сфинкса» (D60, по утверждённому изображению владельца assets/concepts/boss4/zone4_temple/
-- reference.png): храм за ареной Сфинкса и набор оформления зоны 4 «Пустыня» — кубический стиль для слабых телефонов.
-- Храм — колоннада лицом к входу (−z): ступенчатый подиум, шесть квадратных столпов с золотыми базами и капителями,
-- архитрав с золотым поясом, тёмная глубина портика с дверью в золотой раме, второй ярус с золотым шестиугольником
-- и синим камнем по центру и розовыми камнями в золотых ромбах по бокам, фиолетовые знамёна с золотой мордой кошки,
-- лианы и кусты на кровле; по бокам — крылья-террасы, с которых в пруды падают водопады. Набор: стела со
-- светящимся анхом и ступенчатым золотым верхом, жаровня с огнём, пирамида, пальма, руины (колоннада, арка, обломок
-- стены), сосуд, ящик, куст, скала, уступ у стены, водопад со стены обрыва, мощёный путь с золотым меандром.
-- Огонь, анхи и блики камней — неон без источников света, частиц нет. Координаты — зоны (как у
-- World/Models/DesertOasis): x поперёк (стены обрыва на ±92), z вдоль (вход −47.5, выход +47.5), y = 0 — пол.
-- Совпадающих граней нет: накладки выступают ≥ 0.1, слои — встык (D36).
-- Зависит от World/Models/FleaKit.

local ServerScriptService = game:GetService("ServerScriptService")

local FleaKit = require(ServerScriptService.Server.World.Models.FleaKit)

type Brick = FleaKit.Brick

local B, V = FleaKit.B, FleaKit.V
local Box, Disc, Round = FleaKit.Box, FleaKit.Disc, FleaKit.Round
local DECOR = FleaKit.DECOR
local SOLID = { collide = true } -- цилиндры по умолчанию без столкновений и теней (FleaKit.ROUND)

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

-- Палитра по изображению владельца: тёплый песчаник, лилово-коричневое мощение, яркое золото, синие плитки,
-- фиолетовые знамёна и сосуды. Светлота средняя: солнце Roblox и Bloom светлят светлые жёлтые до белого.
local C = {
	stoneL = hex("D9AE76"), -- светлый песчаник: стены, верх яруса
	stone = hex("C79A62"),
	stoneD = hex("A97A4C"),
	stoneDD = hex("8A603A"), -- глубина портика
	pave = hex("B08A78"), -- мощение площадки
	paveD = hex("94705F"),
	gold = hex("F0B52A"),
	goldD = hex("C99018"),
	blue = hex("3A8EDB"), -- плитки мозаики, камень на храме
	blueL = hex("6CC2F2"),
	purple = hex("8A3FAF"),
	purpleD = hex("5E2A7D"),
	pink = hex("E2449C"),
	panel = hex("5C3B22"), -- плита стелы под анхом
	glow = hex("FFC93C"), -- неон анха
	dark = hex("3A2418"), -- дверной проём
	flameD = hex("D9531B"), -- огонь: низ, середина, верх
	flame = hex("EE7A1E"),
	flameL = hex("FFB632"),
	turq = hex("2FB9B0"),
	water = hex("35C6D6"),
	waterL = hex("8EE6EC"),
	waterD = hex("1E8C86"),
	foam = hex("E6F8FA"),
	trunk = hex("A0663A"),
	trunkD = hex("7A4A28"),
	leaf = hex("6DB83E"),
	leafD = hex("3F8F2E"),
	leafL = hex("94CF52"),
	wood = hex("8A5A34"),
	woodD = hex("64401F"),
	rock = hex("C3955A"),
	rockD = hex("A57842"),
	rockL = hex("D2A86A"),
	dune = hex("DEB061"),
	duneD = hex("CC9B4E"),
	board = hex("F4E4C4"),
}

local GLASS_WATER = { material = Enum.Material.Glass, transparency = 0.2, collide = false, shadow = false }
local GLASS_LIGHT = { material = Enum.Material.Glass, transparency = 0.1, collide = false, shadow = false }
local GLOW = { material = Enum.Material.Neon, collide = false, shadow = false }

local DesertTemple = {}
DesertTemple.C = C

-- Кирпичи вещи в своих координатах (начало — центр низа) → в зону: точка (x, z), поворот yaw градусов.
local function put(out: { Brick }, bricks: { Brick }, x: number, z: number, yaw: number?)
	FleaKit.Put(out, bricks, CFrame.new(x, 0, z) * CFrame.Angles(0, math.rad(yaw or 0), 0))
end

-- Неоновый язык пламени w × h с центром at.
local function flame(w: number, h: number, at: CFrame, color: Color3): Brick
	return FleaKit.Neon(V(w, h, w), at * CFrame.Angles(0, math.rad(45), 0), color)
end

-- Ромб (квадрат, повёрнутый на 45° в плоскости фасада) со стороной a и толщиной t, центр at, лицо −z.
local function diamond(a: number, t: number, at: CFrame, color: Color3): Brick
	return B(V(a, a, t), at * CFrame.Angles(0, 0, math.rad(45)), color, DECOR)
end

-- Шестиугольник «вершиной вверх» с радиусом описанной окружности r и толщиной t (три повёрнутых прямоугольника).
local function hexagon(out: { Brick }, r: number, t: number, at: CFrame, color: Color3)
	-- три полосы на разной глубине (по 0.06): лицевые грани не в одной плоскости (D36: иначе пупырышки мерцают)
	for i, deg in { 0, 60, 120 } do
		local depth = CFrame.new(0, 0, -(i - 1) * 0.06)
		table.insert(
			out,
			B(V(r * math.sqrt(3), r, t), at * depth * CFrame.Angles(0, 0, math.rad(90 + deg)), color, DECOR)
		)
	end
end

-- Лиана: зелёная полоса шириной w от y1 вниз на длину h у плоскости z (лицо −z).
local function vine(out: { Brick }, x: number, y1: number, h: number, z: number, w: number, color: Color3?)
	table.insert(out, Box(x - w / 2, x + w / 2, y1 - h, y1, z - 0.2, z, color or C.leafD, DECOR))
end

-- Жаровня на постаменте высотой h (низ на base): стойка, золотой пояс, чаша с ободом и неоновый огонь — три
-- яруса от тёмно-оранжевого к жёлтому (неон высветляет цвет: светлый оранжевый в Studio выглядит жёлтым кубом).
function DesertTemple.Brazier(out: { Brick }, x: number, z: number, h: number, base: number?)
	local y0 = base or 0
	local top = y0 + h
	put(out, {
		Box(-0.8, 0.8, y0, top, -0.8, 0.8, C.stone),
		Box(-0.9, 0.9, top - 0.6, top - 0.25, -0.9, 0.9, C.gold, DECOR),
		Disc(1.6, top, top + 0.35, 0, 0, C.goldD),
		Disc(2.4, top + 0.35, top + 0.85, 0, 0, C.gold),
		flame(1.3, 0.95, CFrame.new(0, top + 1.25, 0), C.flameD),
		flame(0.95, 0.9, CFrame.new(0.08, top + 1.95, -0.05), C.flame),
		flame(0.55, 0.8, CFrame.new(-0.05, top + 2.6, 0.05), C.flameL),
	}, x, z)
end

-- Стела (как на изображении): каменный цоколь высотой stand, золотой пояс, тело с тёмной плитой и светящимся анхом
-- (лицо −z), ступенчатый золотой верх.
function DesertTemple.Stele(out: { Brick }, x: number, z: number, stand: number, yaw: number?)
	local y = stand
	put(out, {
		Box(-2.8, 2.8, 0, y, -2.8, 2.8, C.stone),
		Box(-2.9, 2.9, y - 0.5, y - 0.2, -2.9, 2.9, C.stoneD, DECOR),
		Box(-2.3, 2.3, y, y + 0.6, -2.3, 2.3, C.gold),
		Box(-2, 2, y + 0.6, y + 8.4, -2, 2, C.stoneL),
		Box(-1.3, 1.3, y + 1.2, y + 7.8, -2.15, -2, C.panel, DECOR),
		-- анх: петля, просвет, перекладина, стойка; под ним — знак-основание
		Round(1.5, 0.12, CFrame.new(0, y + 6.35, -2.21), C.glow, GLOW),
		Round(0.65, 0.12, CFrame.new(0, y + 6.4, -2.27), C.panel),
		Box(-0.8, 0.8, y + 5.25, y + 5.6, -2.27, -2.15, C.glow, GLOW),
		Box(-0.18, 0.18, y + 3.3, y + 5.25, -2.27, -2.15, C.glow, GLOW),
		Box(-0.9, 0.9, y + 2.2, y + 2.45, -2.27, -2.15, C.glow, GLOW),
		-- ступенчатый золотой верх
		Box(-2.3, 2.3, y + 8.4, y + 9.1, -2.3, 2.3, C.gold),
		Box(-1.8, 1.8, y + 9.1, y + 9.8, -1.8, 1.8, C.goldD),
		Box(-1.3, 1.3, y + 9.8, y + 10.5, -1.3, 1.3, C.gold),
		Box(-0.6, 0.6, y + 10.5, y + 11.1, -0.6, 0.6, C.gold),
	}, x, z, yaw)
end

-- Знамя храма: штанга с фиолетовыми концами, полотнище с заострённым низом в золотой кайме и золотая морда кошки
-- (лицо −z), от y1 вниз до y0.
local function banner(out: { Brick }, x: number, y1: number, y0: number, z: number)
	local w = 3.6
	table.insert(out, Box(x - w / 2 - 0.5, x + w / 2 + 0.5, y1, y1 + 0.4, z - 0.2, z + 0.4, C.gold, DECOR))
	for _, s in { -1, 1 } do
		local ex = x + s * (w / 2 + 0.5)
		table.insert(out, Box(ex - 0.25, ex + 0.25, y1 - 0.05, y1 + 0.45, z - 0.25, z + 0.45, C.purpleD, DECOR))
	end
	table.insert(out, Box(x - w / 2, x + w / 2, y0 + 1.6, y1, z, z + 0.25, C.purple, DECOR))
	table.insert(out, Box(x - w / 2 + 0.6, x + w / 2 - 0.6, y0 + 0.7, y0 + 1.6, z, z + 0.25, C.purple, DECOR))
	table.insert(out, Box(x - 0.6, x + 0.6, y0, y0 + 0.7, z, z + 0.25, C.purple, DECOR))
	for _, s in { -1, 1 } do
		local ex = x + s * (w / 2 - 0.1)
		table.insert(out, Box(ex - 0.2, ex + 0.2, y0 + 1.5, y1, z - 0.1, z + 0.3, C.gold, DECOR))
	end
	-- морда кошки: голова, уши, глаза, нос
	local hy = y0 + (y1 - y0) * 0.55
	table.insert(out, Box(x - 0.85, x + 0.85, hy - 0.7, hy + 0.6, z - 0.15, z, C.gold, DECOR))
	for _, s in { -1, 1 } do
		table.insert(
			out,
			Box(
				math.min(x + s * 0.3, x + s * 0.8),
				math.max(x + s * 0.3, x + s * 0.8),
				hy + 0.6,
				hy + 1.1,
				z - 0.15,
				z,
				C.gold,
				DECOR
			)
		)
		table.insert(
			out,
			Box(
				math.min(x + s * 0.2, x + s * 0.55),
				math.max(x + s * 0.2, x + s * 0.55),
				hy - 0.05,
				hy + 0.25,
				z - 0.25,
				z - 0.15,
				C.purpleD,
				DECOR
			)
		)
	end
	table.insert(out, Box(x - 0.15, x + 0.15, hy - 0.45, hy - 0.2, z - 0.25, z - 0.15, C.purpleD, DECOR))
end

-- Квадратный столп портика: золотая база, ствол с тёмной плиткой знаков, золотая капитель и абака до top.
local function pillar(out: { Brick }, x: number, z: number, base: number, top: number)
	table.insert(out, Box(x - 1.8, x + 1.8, base, base + 0.8, z - 1.8, z + 1.8, C.goldD))
	table.insert(out, Box(x - 1.4, x + 1.4, base + 0.8, top - 1.8, z - 1.4, z + 1.4, C.stoneL))
	table.insert(out, Box(x - 0.6, x + 0.6, base + 3, base + 5.4, z - 1.5, z - 1.4, C.stoneD, DECOR))
	table.insert(out, Box(x - 1.9, x + 1.9, top - 1.8, top - 0.6, z - 1.9, z + 1.9, C.gold))
	table.insert(out, Box(x - 2.1, x + 2.1, top - 0.6, top, z - 2.1, z + 2.1, C.goldD))
end

-- Куст: три зелёных блока разных оттенков со своим поворотом, низ на y, масштаб s.
function DesertTemple.Bush(out: { Brick }, x: number, y: number, z: number, s: number)
	table.insert(
		out,
		B(V(2.2 * s, 1.4 * s, 2 * s), CFrame.new(x, y + 0.7 * s, z) * CFrame.Angles(0, 0.4, 0), C.leafD, DECOR)
	)
	table.insert(
		out,
		B(
			V(1.6 * s, 1.2 * s, 1.5 * s),
			CFrame.new(x + 0.5 * s, y + 1.5 * s, z - 0.3 * s) * CFrame.Angles(0, -0.3, 0),
			C.leaf,
			DECOR
		)
	)
	table.insert(
		out,
		B(
			V(1.2 * s, 0.9 * s, 1.1 * s),
			CFrame.new(x - 0.7 * s, y + 1.1 * s, z + 0.5 * s) * CFrame.Angles(0, 0.9, 0),
			C.leafL,
			DECOR
		)
	)
end

-- Храм за ареной: фасад от z 34.5 до 47.4 (у выхода зоны), центр шириной 52 и высотой до 39 (крупный фон за
-- Сфинксом), крылья до |x| 41 с водопадами в пруды перед ними; боковые пути к следующей зоне (|x| ≥ 48) свободны.
function DesertTemple.Temple(out: { Brick })
	-- подиум из трёх ступеней и золотая кромка верхней (выступает на 0.1)
	table.insert(out, Box(-30, 30, 0, 0.8, 34.5, 47.4, C.stoneD))
	table.insert(out, Box(-29, 29, 0.8, 1.6, 35.7, 47.4, C.stone))
	table.insert(out, Box(-28, 28, 1.6, 2.4, 36.9, 47.4, C.stoneL))
	table.insert(out, Box(-28.1, 28.1, 2.2, 2.5, 36.8, 37.2, C.gold, DECOR))
	-- колоннада: шесть столпов, глубина портика с дверью в золотой раме
	local top = 21 -- низ архитрава
	for _, x in { -22.5, -13.5, -4.5, 4.5, 13.5, 22.5 } do
		pillar(out, x, 39.2, 2.4, top)
	end
	-- задняя стена портика с глубокой нишей двери (2.6) в золотой раме: настоящая тень, а не тёмная плитка
	table.insert(out, Box(-26, -4.8, 2.4, top, 43.5, 47, C.stoneDD))
	table.insert(out, Box(4.8, 26, 2.4, top, 43.5, 47, C.stoneDD))
	table.insert(out, Box(-4.8, 4.8, 15.1, top, 43.5, 47, C.stoneDD))
	table.insert(out, Box(-4.8, 4.8, 2.4, 15.1, 46.1, 47, C.stoneDD))
	table.insert(out, Box(-4, 4, 2.4, 14, 45.9, 46.1, C.dark, DECOR))
	table.insert(out, Box(-4.8, -4, 2.4, 14.8, 43.2, 46.1, C.gold))
	table.insert(out, Box(4, 4.8, 2.4, 14.8, 43.2, 46.1, C.gold))
	table.insert(out, Box(-5.2, 5.2, 14, 15.1, 43.1, 46.1, C.gold))
	-- архитрав с золотым поясом
	table.insert(out, Box(-26, 26, top, top + 2.4, 37, 43.5, C.stone))
	table.insert(out, Box(-26.3, 26.3, top + 2.4, top + 3, 36.8, 43.7, C.gold))
	local up = top + 3 -- низ второго яруса
	-- выступающий карниз над архитравом (тень на фасад) с бирюзовой кромкой; боковые рамы-анты портика
	table.insert(out, Box(-27, 27, up, up + 0.9, 35.8, 39.5, C.stoneD))
	table.insert(out, Box(-27, 27, up + 0.2, up + 0.55, 35.6, 35.8, C.turq, DECOR))
	for _, s in { -1, 1 } do
		local x0, x1 = math.min(s * 26, s * 28), math.max(s * 26, s * 28)
		table.insert(out, Box(x0, x1, 2.4, up + 1.6, 36.2, 47, C.stone))
		x0, x1 = math.min(s * 25.8, s * 28.2), math.max(s * 25.8, s * 28.2)
		table.insert(out, Box(x0, x1, up + 1.6, up + 2.2, 36, 47.2, C.gold))
		x0, x1 = math.min(s * 25.9, s * 28.1), math.max(s * 25.9, s * 28.1)
		table.insert(out, Box(x0, x1, 9, 9.6, 36.1, 47.1, C.turq, DECOR))
	end
	-- второй ярус (отступает), карниз и центральный выступ под шестиугольником
	table.insert(out, Box(-24, 24, up, up + 7, 39.5, 47, C.stoneL))
	table.insert(out, Box(-24.3, 24.3, up + 7, up + 7.7, 39.2, 47.2, C.gold))
	for _, x in { -18, -6.5, 6.5, 18 } do
		table.insert(out, Box(x - 1, x + 1, up, up + 7, 39.2, 39.5, C.stone, DECOR)) -- лопатки второго яруса
	end
	local crestTop = up + 14
	table.insert(out, Box(-6.5, 6.5, up + 7.7, crestTop, 39.5, 45, C.stoneL))
	table.insert(out, Box(-6.8, 6.8, crestTop, crestTop + 0.6, 39.2, 45.3, C.gold))
	-- золотой шестиугольник с синим камнем
	local crest = CFrame.new(0, up + 10.2, 38.9)
	hexagon(out, 5.4, 0.6, crest, C.gold)
	hexagon(out, 4.4, 0.6, crest * CFrame.new(0, 0, -0.3), C.goldD)
	table.insert(out, diamond(4.2, 0.6, crest * CFrame.new(0, 0, -0.6), C.blue))
	table.insert(out, diamond(2.4, 0.5, crest * CFrame.new(0, 0.35, -0.9), C.blueL))
	table.insert(out, FleaKit.Neon(V(0.6, 0.6, 0.2), crest * CFrame.new(-0.6, 1.1, -1.2), C.foam))
	-- розовые камни в золотых ромбах по сторонам
	for _, s in { -1, 1 } do
		local at = CFrame.new(s * 12.2, up + 3.5, 39.0)
		table.insert(out, diamond(3.4, 0.4, at, C.gold))
		table.insert(out, diamond(2.2, 0.4, at * CFrame.new(0, 0, -0.3), C.pink))
		table.insert(out, FleaKit.Neon(V(0.45, 0.45, 0.15), at * CFrame.new(-0.35, 0.45, -0.55), C.foam))
	end
	-- надпись над дверью (на архитраве)
	table.insert(
		out,
		FleaKit.Board(V(14, 1.6, 0.2), V(0, top + 1.2, 36.9), C.board, FleaKit.Label("ЛОГОВО СФИНКСА"))
	)
	-- фиолетовые знамёна между столпами
	for _, s in { -1, 1 } do
		banner(out, s * 9, top - 0.4, 8.5, 37.6)
	end
	-- лианы с архитрава и второго яруса, кусты на кровле
	for _, v in
		{
			{ -24.6, 4, 0.8 },
			{ -19.2, 2.6, 0.6 },
			{ -15.4, 5.4, 0.7 },
			{ 8.2, 2.4, 0.6 },
			{ 16.5, 4.4, 0.8 },
			{ 20.4, 2.8, 0.6 },
			{ 25, 5, 0.7 },
		}
	do
		vine(out, v[1], top + 2.4, v[2], 36.8, v[3])
	end
	for _, v in { { -21.5, 3.6, 0.7 }, { -9.5, 2.6, 0.6 }, { 9.8, 4, 0.7 }, { 21.6, 2.8, 0.6 } } do
		vine(out, v[1], up + 7, v[2], 39.27, v[3], C.leaf) -- зад лианы не в плоскости розовых ромбов (39.2)
	end
	DesertTemple.Bush(out, -15, up + 7.7, 43.5, 1.6)
	DesertTemple.Bush(out, 16, up + 7.7, 44, 1.4)
	DesertTemple.Bush(out, -3.8, crestTop + 0.6, 43, 1.1)
	-- крылья-террасы с водопадами в пруды
	for _, s in { -1, 1 } do
		local function X(a: number, b: number): (number, number)
			return math.min(s * a, s * b), math.max(s * a, s * b)
		end
		local x0, x1 = X(28, 41)
		table.insert(out, Box(x0, x1, 0, 10, 37.4, 47.2, C.stone))
		x0, x1 = X(28.5, 40.5)
		table.insert(out, Box(x0, x1, 9.6, 10.3, 37.1, 47.4, C.gold))
		x0, x1 = X(30, 40)
		table.insert(out, Box(x0, x1, 10.3, 15, 39.5, 46.8, C.stoneL))
		x0, x1 = X(29.6, 40.4)
		table.insert(out, Box(x0, x1, 15, 15.6, 39.2, 47.1, C.goldD))
		-- выступающий пилон на конце крыла (глубина фасада) с золотой шапкой
		x0, x1 = X(39.3, 41.3)
		table.insert(out, Box(x0, x1, 0, 13, 35.9, 47, C.stoneL))
		x0, x1 = X(39.2, 41.45)
		table.insert(out, Box(x0, x1, 13, 13.6, 35.8, 47.3, C.gold))
		-- проём-арка на втором ярусе крыла
		x0, x1 = X(33.5, 36.5)
		table.insert(out, Box(x0, x1, 10.3, 13.8, 39.3, 39.5, C.stoneDD, DECOR))
		-- вода: струя по фасаду крыла, пена сверху и у подножия, пруд
		x0, x1 = X(32.5, 38.5)
		table.insert(out, Box(x0, x1, 0.5, 9.5, 37, 37.3, C.water, GLASS_WATER))
		for _, f in { 33.6, 36.8 } do
			x0, x1 = X(f - 0.3, f + 0.3)
			table.insert(out, Box(x0, x1, 0.8, 9.3, 36.8, 37, C.waterL, GLASS_LIGHT))
		end
		x0, x1 = X(32.2, 38.8)
		table.insert(out, Box(x0, x1, 9, 9.6, 36.6, 37.4, C.foam, GLASS_LIGHT))
		x0, x1 = X(31.8, 39.2)
		table.insert(out, Box(x0, x1, 0.42, 1.2, 35.6, 37, C.foam, GLASS_LIGHT))
		local px, pz = s * 35.5, 31.6
		table.insert(out, Disc(11, -0.04, 0.3, px, pz, C.stoneD, SOLID))
		table.insert(out, Disc(9.4, -0.03, 0.34, px, pz, C.waterD))
		table.insert(
			out,
			Disc(9.8, 0.36, 0.46, px, pz, C.water, { material = Enum.Material.Glass, transparency = 0.35 })
		)
		table.insert(out, Disc(1.4, 0.46, 0.56, px - s * 2.2, pz - 1.4, C.leaf))
		-- лианы и кусты на крыле
		for _, v in { { 29.4, 3 }, { 40.2, 4 } } do
			vine(out, s * v[1], 9.6, v[2], 37.4, 0.7)
		end
		DesertTemple.Bush(out, s * 37.5, 15.6, 43, 1.2)
		DesertTemple.Bush(out, s * 31.5, 15.6, 44.5, 0.9)
	end
end

-- Пирамида: steps ступеней квадратных плит (светлые и тёмные по очереди) и золотая верхушка.
function DesertTemple.Pyramid(out: { Brick }, x: number, z: number, base: number, steps: number, step: number)
	for i = 0, steps - 1 do
		local side = base * (1 - i / steps)
		local color = if i % 2 == 0 then C.stoneL else C.stone
		table.insert(out, B(V(side, step, side), V(x, (i + 0.5) * step, z), color))
	end
	local cap = base / steps * 0.7
	table.insert(out, B(V(cap, step * 0.6, cap), V(x, steps * step + step * 0.3, z), C.gold))
end

-- Пальма: ствол из колен двух оттенков (как на изображении), шесть листьев и орехи; lean — вынос верхушки.
function DesertTemple.Palm(out: { Brick }, x: number, z: number, height: number, lean: number, yaw: number?)
	local bricks = {}
	local top = Vector3.new(lean, height, 0)
	local n = 4
	for k = 0, n - 1 do
		local f0, f1 = k / n, (k + 1) / n
		local p0 = Vector3.new(lean * f0 * f0, height * f0, 0)
		local p1 = Vector3.new(lean * f1 * f1, height * f1, 0)
		local d = p1 - p0
		table.insert(
			bricks,
			B(
				V(1.1 - 0.06 * k, d.Magnitude + 0.1, 1.1 - 0.06 * k),
				CFrame.lookAt((p0 + p1) / 2, p1) * CFrame.Angles(math.rad(90), 0, 0),
				if k % 2 == 0 then C.trunk else C.trunkD,
				DECOR
			)
		)
	end
	for k = 0, 5 do
		local tilt = if k % 2 == 0 then -16 else -30
		-- нечётные листья повёрнуты ещё на 4°: противоположные листья не в одной плоскости у кроны (D36)
		local leafYaw = k * 60 + 20 + (k % 2) * 4
		local frame = CFrame.new(top) * CFrame.Angles(0, math.rad(leafYaw), 0) * CFrame.Angles(math.rad(tilt), 0, 0)
		table.insert(
			bricks,
			B(V(1.5, 0.25, 5.2), frame * CFrame.new(0, 0, 2.4), if k % 2 == 0 then C.leafL else C.leaf, DECOR)
		)
	end
	table.insert(bricks, B(V(1.2, 0.9, 1.2), CFrame.new(top) * CFrame.new(0, -0.55, 0), C.trunkD, DECOR))
	put(out, bricks, x, z, yaw)
end

-- Песчаная скала: три грубых блока разной светлоты, повёрнутых вразнобой.
function DesertTemple.Rock(out: { Brick }, x: number, z: number, w: number, h: number, d: number, yaw: number)
	local a = math.rad(yaw)
	table.insert(out, B(V(w, h * 0.55, d), CFrame.new(x, h * 0.275, z) * CFrame.Angles(0, a, 0), C.rockD))
	table.insert(
		out,
		B(
			V(w * 0.75, h * 0.38, d * 0.78),
			CFrame.new(x + w * 0.07, h * 0.72, z - d * 0.05) * CFrame.Angles(0, a + 0.35, 0),
			C.rock
		)
	)
	table.insert(
		out,
		B(
			V(w * 0.42, h * 0.26, d * 0.48),
			CFrame.new(x - w * 0.1, h * 0.98, z + d * 0.08) * CFrame.Angles(0.06, a - 0.25, 0.08),
			C.rockL
		)
	)
end

-- Скала у стены обрыва (сторона s): высокий уступ длиной len вдоль z с центром z и высотой h.
function DesertTemple.CliffRock(out: { Brick }, s: number, z: number, len: number, h: number)
	local function X(a: number, b: number): (number, number)
		return math.min(s * a, s * b), math.max(s * a, s * b)
	end
	local x0, x1 = X(85.5, 92)
	table.insert(out, Box(x0, x1, 0, h * 0.62, z - len / 2, z + len / 2, C.rockD))
	table.insert(
		out,
		B(
			V(5, h * 0.3, len * 0.78),
			CFrame.new(s * 88.6, h * 0.77 - 0.3, z + len * 0.06) * CFrame.Angles(0, 0.12 * s, 0.05 * s),
			C.rock
		)
	)
	table.insert(
		out,
		B(
			V(3.6, h * 0.16, len * 0.5),
			CFrame.new(s * 89.4, h - 0.5, z - len * 0.1) * CFrame.Angles(0, -0.15 * s, 0.07 * s),
			C.rockL
		)
	)
end

-- Сосуд масштаба s: тулово, широкий пояс, плечо, горло и венчик.
function DesertTemple.Vase(out: { Brick }, x: number, z: number, s: number, body: Color3, rim: Color3)
	table.insert(out, Disc(1.8 * s, 0, 1.6 * s, x, z, body, SOLID))
	table.insert(out, Disc(1.95 * s, 0.55 * s, 1.05 * s, x, z, rim))
	table.insert(out, Disc(1.4 * s, 1.6 * s, 2 * s, x, z, body))
	table.insert(out, Disc(0.9 * s, 2 * s, 2.5 * s, x, z, body))
	table.insert(out, Disc(1.25 * s, 2.5 * s, 2.75 * s, x, z, rim))
end

-- Деревянный ящик со стороной a и тёмным поясом, поворот yaw; низ на y.
function DesertTemple.Crate(out: { Brick }, x: number, y: number, z: number, a: number, yaw: number)
	local at = CFrame.new(x, y, z) * CFrame.Angles(0, math.rad(yaw), 0)
	table.insert(out, B(V(a, a, a), at * CFrame.new(0, a / 2, 0), C.wood))
	table.insert(out, B(V(a + 0.2, a * 0.22, a + 0.2), at * CFrame.new(0, a / 2, 0), C.woodD, DECOR))
end

-- Дюна: три пологих яруса.
function DesertTemple.Dune(out: { Brick }, x: number, z: number, w: number, d: number)
	for k, f in { 1, 0.7, 0.42 } do
		table.insert(
			out,
			B(V(w * f, 1.1, d * f), V(x, 0.55 + (k - 1) * 1.08, z + (k - 1) * 0.6), if k == 2 then C.duneD else C.dune)
		)
	end
end

-- Руины: kind "colonnade" — обломки колонн и упавший ствол, "arch" — уцелевшая арка из квадратных столбов,
-- "wall" — обломок стены с рельефом. Лианы — по камню.
function DesertTemple.Ruin(out: { Brick }, x: number, z: number, kind: string, yaw: number)
	local bricks: { Brick } = {}
	if kind == "colonnade" then
		for i, c in { { -3, 3 }, { 0, 1 }, { 3, 2 } } do
			local cx, drums = c[1], c[2]
			for k = 0, drums - 1 do
				table.insert(bricks, Disc(2.6 - 0.12 * k, k * 1.7, (k + 1) * 1.7, cx, 0, C.stone, SOLID))
			end
			table.insert(bricks, Disc(3.1, 0, 0.5, cx, 0, C.stoneD, SOLID))
			if i == 2 then
				table.insert(bricks, Disc(2.75, 1.0, 1.35, cx, 0, C.gold))
			end
		end
		table.insert(
			bricks,
			B(V(6, 2.3, 2.3), CFrame.new(0.5, 1.15, 3.2) * CFrame.Angles(0, math.rad(12), 0), C.stone, SOLID)
		)
		table.insert(bricks, B(V(1.6, 1.2, 1.4), CFrame.new(-4.2, 0.6, 2.6) * CFrame.Angles(0, 0.5, 0), C.stoneD))
	elseif kind == "arch" then
		for _, s in { -1, 1 } do
			table.insert(bricks, Box(s * 2.6 - 1.1, s * 2.6 + 1.1, 0, 7.4, -1.1, 1.1, C.stone))
			table.insert(bricks, Box(s * 1.2 - 0.3, s * 1.2 + 0.3, 6.4, 7.4, -0.9, 0.9, C.stoneL)) -- пята арки
		end
		table.insert(bricks, Box(-3.9, 3.9, 7.4, 8.8, -1.2, 1.2, C.stoneL))
		table.insert(bricks, Box(-4.1, 4.1, 8.8, 9.3, -1.3, 1.3, C.gold))
		table.insert(bricks, Box(-3.4, -2.8, 4.2, 7.4, -1.3, -1.1, C.leafD, DECOR))
		table.insert(bricks, Box(1.2, 1.8, 6.8, 7.4, -1.4, -1.2, C.leaf, DECOR))
		table.insert(bricks, B(V(2.2, 1.4, 1.8), CFrame.new(5.6, 0.7, 1.5) * CFrame.Angles(0, 0.4, 0), C.stoneD))
	else
		table.insert(bricks, Box(-3, 3, 0, 4.2, -0.6, 0.6, C.stoneD))
		-- обломок тоньше стены (1.0 против 1.2): лицевые грани не совпадают
		table.insert(bricks, B(V(2.6, 1.5, 1), CFrame.new(1.4, 4.8, 0) * CFrame.Angles(0, 0, math.rad(-9)), C.stoneD))
		for i, color in { C.blue, C.gold, C.blue, C.gold } do
			local gx = -3 + i * 1.2
			table.insert(bricks, Box(gx - 0.4, gx + 0.4, 1.6, 2.6, -0.75, -0.6, color, DECOR))
		end
		table.insert(bricks, Box(-2.6, -2.1, 1.4, 4.2, -0.8, -0.6, C.leafD, DECOR))
		table.insert(bricks, B(V(1.8, 1.1, 1.5), CFrame.new(-2.2, 0.55, -2) * CFrame.Angles(0, 0.7, 0), C.stoneD))
	end
	put(out, bricks, x, z, yaw)
end

-- Водопад со стены обрыва (сторона s: стена на s · 92) шириной w вдоль z с центром zc и пруд под ним: струя из
-- стекла, светлые потоки, пена сверху и у подножия; пруд — каменная кромка, глубина и стеклянная гладь.
function DesertTemple.Waterfall(out: { Brick }, s: number, zc: number, w: number)
	local function X(a: number, b: number): (number, number)
		return math.min(s * a, s * b), math.max(s * a, s * b)
	end
	local x0, x1 = X(91.2, 91.8)
	table.insert(out, Box(x0, x1, 0.5, 29.4, zc - w / 2, zc + w / 2, C.water, GLASS_WATER))
	for _, f in { { -0.22, 0.6, 28.4 }, { 0.26, 0.5, 26 } } do
		local z = zc + f[1] * w
		x0, x1 = X(91, 91.2)
		table.insert(out, Box(x0, x1, 29.4 - f[3], 29.2, z - f[2] / 2, z + f[2] / 2, C.waterL, GLASS_LIGHT))
	end
	x0, x1 = X(90.6, 92)
	table.insert(out, Box(x0, x1, 28.8, 29.6, zc - w / 2 - 0.3, zc + w / 2 + 0.3, C.foam, GLASS_LIGHT))
	x0, x1 = X(88.6, 91.6)
	table.insert(out, Box(x0, x1, 0.42, 1.3, zc - w / 2 - 0.7, zc + w / 2 + 0.7, C.foam, GLASS_LIGHT))
	local px = s * 85
	table.insert(out, Disc(18, -0.04, 0.3, px, zc, C.stoneD, SOLID))
	table.insert(out, Disc(16, -0.03, 0.34, px, zc, C.waterD))
	table.insert(out, Disc(16.4, 0.36, 0.46, px, zc, C.water, { material = Enum.Material.Glass, transparency = 0.35 }))
	for _, p in { { -3.4, 3 }, { 1.6, -4.2 } } do
		table.insert(out, Disc(1.5, 0.46, 0.56, px - s * p[1], zc + p[2], C.leaf))
	end
	for i, r in { { -6.2, -7.4 }, { -7.4, 6.3 } } do
		local rx, rz = px + s * r[1], zc + r[2]
		table.insert(out, B(V(0.4, 1.6 + 0.4 * i, 0.4), V(rx, 0.8 + 0.2 * i, rz), C.leafD, DECOR))
		table.insert(out, B(V(0.35, 1.2, 0.35), V(rx + 0.5, 0.6, rz + 0.3), C.leaf, DECOR))
	end
end

-- Мощёный путь вдоль z (от z0 до z1) между |x| a и b по стороне s: плиты, золотая кайма и золотой меандр с синей
-- плиткой у центров centers (всё не выше 0.2 — по нему ходят, путь не загораживает).
function DesertTemple.Path(out: { Brick }, s: number, a: number, b: number, z0: number, z1: number, centers: { number })
	local function X(p: number, q: number): (number, number)
		return math.min(s * p, s * q), math.max(s * p, s * q)
	end
	local x0, x1 = X(a, b)
	table.insert(out, Box(x0, x1, 0, 0.12, z0, z1, C.paveD))
	for _, e in { { a - 0.4, a }, { b, b + 0.4 } } do
		x0, x1 = X(e[1], e[2])
		table.insert(out, Box(x0, x1, 0, 0.2, z0, z1, C.gold))
	end
	for _, c in centers do
		-- меандр: квадратная спираль из пяти золотых полос и синяя плитка у угла
		for _, r in
			{
				{ a + 2, b - 2, c - 2, c - 1.6 },
				{ b - 2.4, b - 2, c - 1.6, c + 2 },
				{ a + 3.6, b - 2.4, c + 1.6, c + 2 },
				{ a + 3.6, a + 4, c - 0.4, c + 1.6 },
				{ a + 4, a + 6, c - 0.4, c },
			}
		do
			x0, x1 = X(r[1], r[2])
			table.insert(out, Box(x0, x1, 0.12, 0.2, r[3], r[4], C.gold, DECOR))
		end
		x0, x1 = X(a + 0.6, a + 1.8)
		table.insert(out, Box(x0, x1, 0.12, 0.18, c - 2, c - 0.8, C.blue, DECOR))
	end
end

-- Мощёная дорога x0..x1 × z0..z1 (верх 0.08) с золотой каймой по длинным сторонам: alongZ — дорога вдоль z.
function DesertTemple.Road(out: { Brick }, x0: number, x1: number, z0: number, z1: number, alongZ: boolean)
	table.insert(out, Box(x0, x1, 0, 0.08, z0, z1, C.paveD))
	if alongZ then
		table.insert(out, Box(x0 - 0.4, x0, 0, 0.16, z0, z1, C.gold, DECOR))
		table.insert(out, Box(x1, x1 + 0.4, 0, 0.16, z0, z1, C.gold, DECOR))
	else
		table.insert(out, Box(x0, x1, 0, 0.16, z0 - 0.4, z0, C.gold, DECOR))
		table.insert(out, Box(x0, x1, 0, 0.16, z1, z1 + 0.4, C.gold, DECOR))
	end
end

-- Песчаный блок: один грубый камень, повёрнутый на yaw.
function DesertTemple.Pebble(out: { Brick }, x: number, z: number, w: number, h: number, yaw: number)
	table.insert(
		out,
		B(V(w, h, w * 0.8), CFrame.new(x, h / 2 - 0.1, z) * CFrame.Angles(0.05, math.rad(yaw), 0.04), C.rock)
	)
end

return DesertTemple

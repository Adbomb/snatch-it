-- Уровень 5 «Ледник» — «Замёрзшая галерея коллекционера» (D64, концепт-лист assets/concepts/bosses_5_10/boss5_v2/
-- 2_arena.png, утверждён владельцем; площадка r 32 и глыба во сне справа от Йети — решение 2026-11-24): площадка босса
-- и оформление зоны в кубическом стиле для слабых телефонов. В центре — «замёрзшее озеро»: ледяная площадка (r 32) с
-- синей кромкой, кольцами и снежинкой-мозаикой; четыре места существ — плиты с синим ободом (MapLayout.Arenas[5].slots,
-- верх плиты — Arenas[5].top). По краю — музейные столбики с красным канатом (ниже 2), проходы у входа и к выходу. За
-- ареной (к выходу) — ледник одной стеной (не дворец и не башни): гранёные глыбы, острые пики со смещёнными вершинами,
-- снежный карниз с сосульками, в центре круглая дверь хранилища (золотое кольцо, снежинка-штурвал, голубое свечение);
-- на ледяном уступе перед стеной — четыре объёмные витрины с экспонатами (не рамки на стене). По бокам — ещё шесть
-- витрин на пьедесталах, гряды ледника у стен обрыва, трещины с голубым светом, ели и сугробы с кристаллами; в небе за
-- ледником — северное сияние (неон). Экспонаты — только предметы: кубок, самоцвет, будильник, корона, ключ, кристалл.
-- Пути (D62): от входа к площадке и от неё к выходу по бокам ледника (GlacierHall.Paths) — без твёрдых деталей выше
-- порога; в круге, куда босс заходит в бою (scripts/lune/check_world.luau), нет ничего выше 2. Света мало (дверь и две
-- витрины), частиц нет; поперёк коридора ничего (D41). Координаты зоны: x — поперёк (±92), z — вдоль (вход −47.5,
-- выход +47.5), y = 0 — пол. Надписи возвращаются списком (их пишет WorldBuilder).
-- Зависит от MapLayout, World/Models/FleaKit.

local ServerScriptService = game:GetService("ServerScriptService")

local World = ServerScriptService.Server.World
local MapLayout = require(World.MapLayout)
local FleaKit = require(World.Models.FleaKit)

type Brick = FleaKit.Brick
export type Sign = FleaKit.Sign

local B, V = FleaKit.B, FleaKit.V
local Box, Disc, Round = FleaKit.Box, FleaKit.Disc, FleaKit.Round
local DECOR, BALL = FleaKit.DECOR, FleaKit.BALL
local SOLID = { collide = true } -- площадка, плиты, пьедесталы: по ним ходят (диски по умолчанию без столкновений)
local GLASS = { material = Enum.Material.Glass, transparency = 0.55, shadow = false, collide = true } -- колпак витрины
local NEON = { material = Enum.Material.Neon, collide = false, shadow = false }
local SKY = { material = Enum.Material.Neon, collide = false, shadow = false, transparency = 0.25 }
local SOFT = { variant = "LegoSquaresSoft" } -- большие плоскости ледника: мягкие пупырышки

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

-- Цвета концепт-листа (scripts/blender/boss5/arena.py, PAL).
local C = {
	path = hex("BFDCF0"),
	tile = hex("8FCDF0"),
	edge = hex("4FC3F7"),
	plat = hex("B7ECFF"),
	platEdge = hex("3F98D6"),
	slot = hex("7FCBF0"),
	mosaic = hex("5FB6E8"),
	mosaicL = hex("E2FAFF"),
	glacier = hex("A6E4FA"),
	glacierD = hex("62BDE6"),
	glacierE = hex("E6FBFF"),
	snowS = hex("DCE8F7"),
	cave = hex("1F3A6E"),
	gold = hex("F5B21C"),
	goldD = hex("C27E0E"),
	rope = hex("D8344A"),
	stone = hex("4E5F8C"),
	stoneD = hex("35426A"),
	pine = hex("2F7A5A"),
	pineD = hex("23604A"),
	trunk = hex("8F5A31"),
	crev = hex("203A66"),
	neonIce = hex("6FF2FF"),
	neonAur = hex("3DFFB0"),
	neonAurP = hex("B57CFF"),
	neonGem = hex("FF4FA3"),
	red = hex("E8384F"),
	white = hex("FFFFFF"),
	dark = hex("161824"),
	iceCase = hex("9FE6FF"),
}

-- Площадка (диаметры и верх дисков снизу вверх; каждый следующий выше на 0.06 — грани не совпадают, D36). Верх
-- центрального диска — Arenas[5].floor: на нём стоит Йети.
local DISCS = {
	{ 65.6, -0.06, 0.40, C.platEdge },
	{ 64, -0.055, 0.46, C.plat },
	{ 53.6, -0.05, 0.52, C.mosaic },
	{ 52, -0.045, 0.58, C.plat },
	{ 28.6, -0.04, 0.64, C.mosaicL },
	{ 27.4, -0.035, 0.70, C.plat },
}
local STANCHION_R = 34.4 -- столбики за краем площадки (r 32 + 1 — проверка «на площадке нет декора»)
local ENTRY_DEG, EXIT_DEG = 180, 53.5 -- проходы в канате: к входу и к двум дорожкам выхода (градусы от +z к +x)

local GlacierHall = {}

-- Видимые пути (D62): отрезки {x0, z0, x1, z1, ширина}. Центральный — от входа к площадке, два — от входа зоны по
-- бокам (продолжение путей «Пустыни»), два — от проходов в канате к выходу в обход ледника. Без твёрдых деталей выше
-- порога (scripts/lune/check_world.luau).
GlacierHall.Paths = {
	{ 0, -47.3, 0, -36.6, 10 },
	{ -52, -47.3, -7, -41, 10 },
	{ 52, -47.3, 7, -41, 10 },
	{ -27, 15, -44, 47.3, 10 },
	{ 27, 15, 44, 47.3, 10 },
}

-- Пик: треугольник в плоскости «поперёк» (along = "x": виден спереди, вершина над x = apex) или «вдоль» (along = "z":
-- виден сбоку, вершина над z = apex) из двух клиньев спиной к спине; left/right — полуширины, depth — толщина,
-- c — центр по другой оси.
local function peak(
	out: { Brick },
	along: string,
	apex: number,
	left: number,
	right: number,
	c: number,
	depth: number,
	base: number,
	h: number,
	color: Color3,
	extra: { [string]: any }?
)
	local y = base + h / 2
	if along == "x" then
		-- клин поднимается к +z; поворот на ±90° — к +x (левая половина) и к −x (правая)
		table.insert(
			out,
			B(V(depth, h, left), CFrame.new(apex - left / 2, y, c) * CFrame.Angles(0, math.rad(90), 0), color, extra)
		)
		table.insert(
			out,
			B(V(depth, h, right), CFrame.new(apex + right / 2, y, c) * CFrame.Angles(0, math.rad(-90), 0), color, extra)
		)
	else
		table.insert(out, B(V(depth, h, left), CFrame.new(c, y, apex - left / 2), color, extra))
		table.insert(out, B(V(depth, h, right), CFrame.new(c, y, apex + right / 2) * FleaKit.TURN, color, extra))
	end
end

local WEDGE_DECOR = { shape = "Wedge", collide = false }

-- Экспонат витрины: начало — центр низа (x, y, z), размер s, лицо к −z. Только предметы, без людей и картин.
local function exhibit(out: { Brick }, kind: string, x: number, y: number, z: number, s: number)
	if kind == "trophy" then
		FleaKit.Put(out, FleaKit.Trophy(C.gold, 1.6 * s, true), CFrame.new(x, y, z))
	elseif kind == "gem" then
		table.insert(out, Disc(1.3 * s, y, y + 0.25 * s, x, z, C.goldD))
		local a = 1.4 * s -- куб на вершине: высота a·√3
		table.insert(out, B(V(a, a, a), CFrame.new(x, y + 0.2 * s + a * 0.87, z) * FleaKit.DIAMOND, C.neonGem, NEON))
	elseif kind == "clock" then -- будильник: красный корпус, белый циферблат, стрелки, звонки, ножки
		local cy, t = y + 1.5 * s, 0.9 * s
		table.insert(out, Round(2.6 * s, t, CFrame.new(x, cy, z), C.red))
		table.insert(out, Round(2.0 * s, t + 0.2, CFrame.new(x, cy, z), C.white))
		local face = z - t / 2 - 0.1
		-- стрелки утоплены в циферблат на разную глубину (задние грани не совпадают)
		table.insert(out, B(V(0.16 * s, 0.8 * s, 0.17), V(x, cy + 0.35 * s, face - 0.035), C.dark, DECOR))
		table.insert(out, B(V(0.6 * s, 0.16 * s, 0.34), V(x + 0.25 * s, cy, face - 0.07), C.dark, DECOR))
		for _, sx in { -1, 1 } do
			table.insert(out, B(V(0.9, 0.9, 0.9) * s, V(x + sx * 0.8 * s, cy + 1.35 * s, z), C.gold, BALL))
			table.insert(out, B(V(0.3, 0.45, 0.3) * s, V(x + sx * 0.7 * s, y + 0.22 * s, z), C.gold, DECOR))
		end
	elseif kind == "crown" then -- обод, пять зубцов, самоцветы спереди
		table.insert(out, Disc(2.4 * s, y, y + 0.9 * s, x, z, C.gold))
		for i = 0, 4 do
			local a = math.rad(i * 72 + 36)
			local frame = CFrame.new(x + math.sin(a) * 0.95 * s, y + 1.3 * s, z + math.cos(a) * 0.95 * s)
				* CFrame.Angles(0, a + math.rad(45), 0)
			table.insert(out, B(V(0.45 * s, 1.0 * s, 0.45 * s), frame, C.gold, DECOR))
		end
		for _, dx in { -0.45, 0.45 } do
			table.insert(out, B(V(0.3, 0.3, 0.3) * s, V(x + dx * s, y + 0.45 * s, z - 1.12 * s), C.neonGem, NEON))
		end
	elseif kind == "key" then -- ключ стоит бородкой вниз: кольцо с отверстием, стержень, два зубца
		local t = 0.4 * s
		table.insert(out, Round(1.8 * s, t + 0.24, CFrame.new(x, y + 2.4 * s, z), C.gold))
		table.insert(out, Round(0.8 * s, t + 0.48, CFrame.new(x, y + 2.4 * s, z), C.iceCase))
		table.insert(
			out,
			Box(x - 0.22 * s, x + 0.22 * s, y + 0.2 * s, y + 1.8 * s, z - t / 2, z + t / 2, C.gold, DECOR)
		)
		local tz = t / 2 - 0.12
		table.insert(out, Box(x + 0.1 * s, x + 0.8 * s, y + 0.3 * s, y + 0.6 * s, z - tz, z + tz, C.goldD, DECOR))
		table.insert(out, Box(x + 0.1 * s, x + 0.6 * s, y + 0.85 * s, y + 1.1 * s, z - tz, z + tz, C.goldD, DECOR))
	elseif kind == "crystal" then -- три голубых кристалла разной высоты
		for i, k in { { -0.55, 2.2, 30 }, { 0, 3.2, 45 }, { 0.6, 1.8, 60 } } do
			local h = k[2] * s
			local frame = CFrame.new(x + k[1] * s, y + h / 2, z + (i - 2) * 0.15 * s)
				* CFrame.Angles(0, math.rad(k[3]), 0)
			table.insert(out, B(V(0.8 * s, h, 0.8 * s), frame, C.neonIce, NEON))
		end
	end
end

-- Витрина: пьедестал (низ y0, верх top, диаметр d) с золотым ободом, стеклянный колпак до высоты glassTop, ледяная
-- крышка, экспонат внутри. light — свет экспоната (радиус).
local function vitrine(
	out: { Brick },
	kind: string,
	x: number,
	z: number,
	y0: number,
	top: number,
	d: number,
	glassTop: number,
	s: number
)
	table.insert(out, Disc(d, y0, top, x, z, C.stone, SOLID))
	table.insert(out, Disc(d + 0.3, top - 0.2, top + 0.15, x, z, C.gold, SOLID))
	local rim = top + 0.15
	table.insert(out, Disc(d * 0.85, rim, glassTop, x, z, C.iceCase, GLASS))
	table.insert(out, Disc(d * 0.9, glassTop, glassTop + 0.4, x, z, C.glacierE, SOLID))
	table.insert(out, Disc(d * 0.45, glassTop + 0.4, glassTop + 0.8, x, z, C.glacierE))
	exhibit(out, kind, x, rim, z, s)
end

-- Ель: ствол и три ступенчатых яруса (через один повёрнуты на 45°) со снегом, макушка-снежок.
local function pine(out: { Brick }, x: number, z: number, scale: number, yaw: number)
	local s = scale
	table.insert(out, Box(x - 0.6 * s, x + 0.6 * s, 0, 3 * s, z - 0.6 * s, z + 0.6 * s, C.trunk))
	for i, tier in { { 6.4, 2.2, 2.4 }, { 4.8, 4.4, 2.2 }, { 3.2, 6.4, 2.0 } } do
		local w, y0, h = tier[1] * s, tier[2] * s, tier[3] * s
		local turn = CFrame.Angles(0, math.rad(yaw + (i % 2) * 45), 0)
		table.insert(out, B(V(w, h, w), CFrame.new(x, y0 + h / 2, z) * turn, if i == 2 then C.pineD else C.pine, DECOR))
		table.insert(
			out,
			B(V(w * 0.72, 0.4 * s, w * 0.72), CFrame.new(x, y0 + h + 0.1 * s, z) * turn, C.glacierE, DECOR)
		)
	end
	table.insert(
		out,
		B(V(1.3, 1.2, 1.3) * s, CFrame.new(x, 8.9 * s, z) * CFrame.Angles(0, math.rad(yaw), 0), C.glacierE, DECOR)
	)
end

-- Сугроб с кристаллом.
local function drift(out: { Brick }, x: number, z: number, yaw: number)
	local turn = CFrame.Angles(0, math.rad(yaw), 0)
	table.insert(out, B(V(8, 1.0, 6), CFrame.new(x, 0.45, z) * turn, C.snowS))
	table.insert(out, B(V(5, 1.8, 3.6), CFrame.new(x, 0.85, z) * turn * CFrame.new(-0.8, 0, 0.4), C.glacierE))
	local crystal = CFrame.new(x, 0, z)
		* turn
		* CFrame.new(1.6, 2.2, -0.6)
		* CFrame.Angles(0, math.rad(45), math.rad(12))
	table.insert(out, B(V(1, 3, 1), crystal, C.neonIce, NEON))
end

-- Трещина во льду от (x0, z0) до (x1, z1): тёмная щель, голубой свет, ледяные края.
local function crevasse(out: { Brick }, x0: number, z0: number, x1: number, z1: number)
	local dx, dz = x1 - x0, z1 - z0
	local len = math.sqrt(dx * dx + dz * dz)
	local at = CFrame.new((x0 + x1) / 2, 0, (z0 + z1) / 2) * CFrame.Angles(0, math.atan2(-dz, dx), 0)
	table.insert(out, B(V(len, 0.14, 2.8), at * CFrame.new(0, 0.05, 0), C.crev, DECOR))
	table.insert(out, B(V(len - 2, 0.12, 0.7), at * CFrame.new(0, 0.1, 0), C.neonIce, NEON))
	for _, t in { -0.3, 0.1, 0.4 } do
		for _, side in { -1, 1 } do
			table.insert(out, B(V(4.4, 0.55, 1.0), at * CFrame.new(t * len, 0.25, side * 1.9), C.glacierE, DECOR))
		end
	end
end

-- Путь: плита вдоль отрезка (без столкновений) и ледяные ромбы по оси.
local function path(out: { Brick }, p: { number }, top: number, edges: boolean)
	local x0, z0, x1, z1, w = p[1], p[2], p[3], p[4], p[5]
	local dx, dz = x1 - x0, z1 - z0
	local len = math.sqrt(dx * dx + dz * dz)
	local at = CFrame.new((x0 + x1) / 2, 0, (z0 + z1) / 2) * CFrame.Angles(0, math.atan2(dx, dz), 0)
	table.insert(out, B(V(w, top + 0.04, len), at * CFrame.new(0, (top - 0.04) / 2, 0), C.path, DECOR))
	if edges then
		for _, side in { -1, 1 } do
			-- кромка выступает за край плиты на 0.1 и над ней на 0.06 (ниже кромки площадки 0.40)
			local strip = at * CFrame.new(side * (w / 2 - 0.3), (top + 0.02) / 2, 0)
			table.insert(out, B(V(0.8, top + 0.1, len - 0.4), strip, C.edge, DECOR))
		end
	end
	local count = math.max(1, math.floor(len / 9))
	for k = 1, count do
		local u = -len / 2 + (k - 0.5) * len / count
		local tileAt = at * CFrame.new(0, (top + 0.04) / 2, u) * CFrame.Angles(0, math.rad(45), 0)
		table.insert(out, B(V(2, top + 0.08, 2), tileAt, C.tile, DECOR))
	end
end

-- Ледник за ареной: гранёные глыбы (x от, до, перед, верх, цвет), пики, карниз, сосульки, уступ, дверь хранилища.
local WALL = {
	{ -32, -22, 41.0, 11.5, C.glacierD },
	{ -22, -12, 40.0, 15.2, C.glacier },
	{ -12, -4, 39.6, 15.6, C.glacier },
	{ -4, 4, 39.3, 16.0, C.glacier },
	{ 4, 12, 39.6, 15.4, C.glacier },
	{ 12, 22, 40.2, 15.0, C.glacier },
	{ 22, 32, 41.2, 12.0, C.glacierD },
}
local WALL_BACK = 47
-- Пики: вершина x, полуширины слева и справа, низ, высота, перед и зад (у каждого свой перед — грани не совпадают).
local PEAKS = {
	{ -24, 6, 5, 11.2, 9, 42.0, 46.6 },
	{ -15, 7, 6, 14.8, 12, 41.4, 46.4 },
	{ -5, 6, 7, 15.2, 17, 41.0, 46.8 },
	{ 7, 6, 6, 15.1, 13, 41.2, 46.2 },
	{ 17, 6, 6, 14.6, 10, 41.6, 46.5 },
	{ 26, 5, 5, 11.6, 8, 42.2, 46.9 },
}
local DOOR = Vector3.new(0, 8, 0) -- центр двери (z — по слоям ниже); верх свечения 15.5 — под карнизом

local function glacierWall(out: { Brick })
	for i, seg in WALL do
		local x0, x1, front, top, color = seg[1], seg[2], seg[3], seg[4], seg[5]
		table.insert(out, Box(x0, x1, 0, top, front, WALL_BACK, color, SOFT))
		-- снежный карниз чуть шире глыбы (выступает на 0.1–0.3) и сосульки под ним
		-- карниз — козырёк глубиной 3.5 (зад не совпадает с гранями пиков и соседних карнизов)
		table.insert(out, Box(x0 - 0.1, x1 + 0.1, top - 0.4, top + 0.5, front - 0.25, front + 3.25, C.glacierE))
		for k, u in { 0.3, 0.72 } do
			local x = x0 + (x1 - x0) * u
			local h = 1.2 + ((i + k) % 3) * 0.5
			table.insert(
				out,
				Box(x - 0.45, x + 0.45, top - 0.4 - h, top - 0.3, front - 0.2, front + 0.6, C.glacierE, DECOR)
			)
			table.insert(
				out,
				Box(x - 0.2, x + 0.2, top - 0.6 - h - 0.9, top - 0.5 - h, front - 0.1, front + 0.5, C.glacierE, DECOR)
			)
		end
	end
	for i, p in PEAKS do
		local apex, left, right, base, h, z0, z1 = p[1], p[2], p[3], p[4], p[5], p[6], p[7]
		local color = if i == 3 then C.glacierD else C.glacier
		peak(out, "x", apex, left, right, (z0 + z1) / 2, z1 - z0, base, h, color, { shape = "Wedge" })
		-- снег на вершине: верхние 30 % чуть шире и выше пика (скаты не совпадают)
		local ch = h * 0.3 + 0.25
		peak(
			out,
			"x",
			apex,
			left * 0.3 + 0.2,
			right * 0.3 + 0.2,
			(z0 + z1) / 2,
			z1 - z0 + 0.3,
			base + h * 0.7 - 0.1,
			ch,
			C.glacierE,
			WEDGE_DECOR
		)
	end
	-- ледяной уступ перед стеной и три ступени к двери
	table.insert(out, Box(-30, 30, 0, 1.6, 33, 41.2, C.glacierE))
	for i = 0, 2 do
		table.insert(out, Box(-6.5 + i * 0.8, 6.5 - i * 0.8, 0, 0.55 + i * 0.5, 31.2 + i * 0.6, 33.2, C.glacierE))
	end
	-- круглая дверь хранилища: голубое свечение, золотое кольцо, тёмная середина, снежинка-штурвал, ступица, заклёпки
	local function layer(d: number, front: number, back: number, color: Color3, extra: { [string]: any }?)
		table.insert(out, Round(d, back - front, CFrame.new(DOOR.X, DOOR.Y, (front + back) / 2), color, extra))
	end
	layer(15, 39.05, 39.8, C.neonIce, { material = Enum.Material.Neon })
	layer(13.2, 38.85, 39.5, C.gold)
	layer(10.4, 38.7, 39.4, C.cave)
	for i, deg in { 0, 60, 120 } do
		local front = 38.45 - (i - 1) * 0.1
		local turn = CFrame.new(DOOR.X, DOOR.Y, (front + 38.9) / 2) * CFrame.Angles(0, 0, math.rad(deg))
		table.insert(out, B(V(0.9, 9.6, 38.9 - front), turn, C.gold, DECOR))
		for _, end_ in { -1, 1 } do
			for _, side in { -1, 1 } do
				local arm = turn
					* CFrame.new(0, end_ * 3.4, 0)
					* CFrame.Angles(0, 0, math.rad(side * 45))
					* CFrame.new(0, end_ * 0.6, 0)
				table.insert(
					out,
					B(V(0.6, 1.4, 0.3), CFrame.new(arm.Position.X, arm.Position.Y, 38.75) * arm.Rotation, C.gold, DECOR)
				)
			end
		end
	end
	layer(3, 38.1, 38.8, C.goldD)
	table.insert(out, FleaKit.Neon(V(0.6, 1.5, 1.5), CFrame.new(DOOR.X, DOOR.Y, 38.2) * FleaKit.ALONG_Z, C.neonIce, 22))
	out[#out].shape = "Cylinder"
	for k = 0, 7 do
		local a = math.rad(k * 45 + 22.5)
		table.insert(
			out,
			Box(
				DOOR.X + math.sin(a) * 5.9 - 0.3,
				DOOR.X + math.sin(a) * 5.9 + 0.3,
				DOOR.Y + math.cos(a) * 5.9 - 0.3,
				DOOR.Y + math.cos(a) * 5.9 + 0.3,
				38.7,
				39.0,
				C.goldD,
				DECOR
			)
		)
	end
	-- витрины на уступе
	for _, v in { { "trophy", -25 }, { "gem", -16 }, { "clock", 16 }, { "crown", 25 } } do
		vitrine(out, v[1], v[2], 37, 1.5, 3.2, 4, 7.6, 1)
	end
end

function GlacierHall.Zone(): ({ Brick }, { Sign })
	FleaKit.Reset()
	local out: { Brick } = {}
	local arena = MapLayout.Arenas[5]
	local spot = MapLayout.BossSpot
	local cx, cz = spot.X, spot.Y
	local function polar(deg: number, r: number): (number, number)
		local a = math.rad(deg)
		return cx + math.sin(a) * r, cz + math.cos(a) * r
	end

	-- «Замёрзшее озеро»: кромка, поле, кольца мозаики (каждый следующий диск выше), снежинка — лучи и «ёлочки»
	for _, d in DISCS do
		table.insert(out, Disc(d[1], d[2], d[3], cx, cz, d[4], SOLID))
	end
	for k = 0, 5 do
		local deg = k * 60 + 30
		local x, z = polar(deg, 17)
		table.insert(
			out,
			B(V(1.1, 0.58, 16), CFrame.new(x, 0.59, z) * CFrame.Angles(0, math.rad(deg), 0), C.mosaicL, DECOR)
		)
		for _, ring in { { 12, 5 }, { 19.5, 4 } } do
			local px, pz = polar(deg, ring[1])
			for _, side in { -1, 1 } do
				local a = math.rad(deg + side * 45)
				local mx, mz = px + math.sin(a) * ring[2] / 2, pz + math.cos(a) * ring[2] / 2
				table.insert(
					out,
					B(V(0.8, 0.5, ring[2]), CFrame.new(mx, 0.55, mz) * CFrame.Angles(0, a, 0), C.mosaicL, DECOR)
				)
			end
		end
	end
	-- места четырёх существ: плита с синим ободом (верх — Arenas[5].top)
	for _, s in arena.slots do
		table.insert(out, Disc(5.9, 0.3, arena.top - 0.08, s.X, s.Y, C.platEdge, SOLID))
		table.insert(out, Disc(5.2, 0.31, arena.top, s.X, s.Y, C.slot, SOLID))
	end

	-- музейные столбики с красным канатом по краю (проходы — к входу и к дорожкам выхода)
	local posts = {}
	for k = 0, 23 do
		local deg = k * 15 + 7.5
		local open = false
		for _, gap in { ENTRY_DEG, EXIT_DEG, 360 - EXIT_DEG } do
			if math.abs((deg - gap + 180) % 360 - 180) < 10 then
				open = true
			end
		end
		if not open then
			local x, z = polar(deg, STANCHION_R)
			posts[k] = Vector3.new(x, 1.5, z)
			table.insert(out, Disc(1.1, -0.05, 0.38, x, z, C.goldD)) -- выше путей (0.26–0.34) — грани не совпадают
			table.insert(out, Disc(0.44, 0.2, 1.6, x, z, C.gold))
			table.insert(out, Disc(0.66, 1.55, 1.8, x, z, C.gold))
		end
	end
	for k = 0, 23 do
		local a, b = posts[k], posts[(k + 1) % 24]
		if a and b then
			local mid = (a + b) / 2 - Vector3.new(0, 0.35, 0)
			for _, seg in { { a, mid }, { mid, b } } do
				local p0, p1 = seg[1], seg[2]
				local len = (p1 - p0).Magnitude
				table.insert(out, B(V(0.22, 0.22, len), CFrame.lookAt((p0 + p1) / 2, p1), C.rope, DECOR))
			end
		end
	end

	-- пути: центральный с кромками, боковые — с ледяными ромбами
	for i, p in GlacierHall.Paths do
		path(out, p, if i == 1 then 0.28 elseif i <= 3 then 0.26 else 0.27, i == 1)
	end

	glacierWall(out)

	-- витрины по бокам (на пьедесталах с цоколем); у кристалла и самоцвета — свет
	for _, v in
		{
			{ "trophy", -46, -24 },
			{ "key", 46, -24 },
			{ "crystal", -54, 2 },
			{ "gem", 54, 2 },
			{ "clock", -62, 28 },
			{ "crown", 62, 28 },
		}
	do
		table.insert(out, Disc(6.8, -0.05, 0.9, v[2], v[3], C.stoneD, SOLID))
		vitrine(out, v[1], v[2], v[3], 0.85, 2.6, 6, 8.6, 1.35)
		if v[1] == "crystal" or v[1] == "gem" then
			out[#out].light = { range = 14, brightness = 1, color = if v[1] == "gem" then C.neonGem else C.neonIce }
		end
	end

	-- гряды ледника у стен обрыва: твёрдое основание (до 13 — с него не допрыгнуть до кромки) и пик без столкновений
	for _, s in { -1, 1 } do
		local z = -47
		local k = 0
		while z < 46 do
			k += 1
			local len = 7 + (k * 37 % 5)
			local z1 = math.min(z + len, 47)
			local inner = 80 + (k * 53 % 7)
			local top = 8 + (k * 29 % 6)
			local color = if k % 3 == 0 then C.glacierD else C.glacier
			local x0, x1 = math.min(s * inner, s * 93), math.max(s * inner, s * 93)
			table.insert(out, Box(x0, x1, 0, top, z, z1, color, SOFT))
			local apex = (z + z1) / 2 + ((k % 3) - 1) * 1.2
			local h = 4 + (k * 17 % 5)
			peak(
				out,
				"z",
				apex,
				apex - z + 0.1,
				z1 - apex + 0.1,
				s * (inner + 93) / 2,
				93 - inner - 1.5,
				top - 0.2,
				h,
				if k % 2 == 0 then C.glacierE else C.glacier,
				WEDGE_DECOR
			)
			z = z1
		end
	end

	-- трещины, ели, сугробы — в боковых полосах, вне путей и круга боя
	crevasse(out, -74, -40, -58, -12)
	crevasse(out, 62, -36, 76, -8)
	crevasse(out, -70, 6, -52, 28)
	crevasse(out, 56, 18, 72, 38)
	for _, t in
		{
			{ -66, -30, 1, 0 },
			{ 68, -22, 1.1, 20 },
			{ -54, -38, 0.9, 10 },
			{ 72, 6, 1, 30 },
			{ -74, 18, 1.15, 15 },
			{ 76, -42, 0.95, 5 },
			{ -58, 40, 1, 25 },
			{ 60, 42, 1.05, 12 },
			{ -76, -6, 0.9, 35 },
		}
	do
		pine(out, t[1], t[2], t[3], t[4])
	end
	for _, d in
		{ { -66, -14, 15 }, { 66, -6, -20 }, { -54, 30, 30 }, { 48, -36, 10 }, { -70, 34, -10 }, { 74, 26, 25 } }
	do
		drift(out, d[1], d[2], d[3])
	end

	-- указатели к следующему уровню у дорожек выхода
	for _, s in { -1, 1 } do
		local x, z = s * 47.5, 36
		table.insert(out, Box(x - 0.2, x + 0.2, 0, 3.7, z - 0.2, z + 0.2, C.trunk))
		table.insert(
			out,
			FleaKit.Board(V(4.6, 1.3, 0.3), V(x, 3.3, z - 0.35), C.platEdge, FleaKit.Label("В ДЖУНГЛИ"))
		)
	end

	-- северное сияние за ледником: две ленты неоновых полос разной высоты (без столкновений, вне игры)
	for i = 0, 25 do
		local x = -78 + i * 6.24
		local y0 = 38 + 5 * math.sin(i * 0.45)
		local h = 7 + 6 * math.abs(math.sin(i * 0.9))
		table.insert(out, B(V(6, h, 0.4), V(x, y0 + h / 2, 46.6), C.neonAur, SKY))
	end
	for i = 0, 17 do
		local x = -60 + i * 7.06
		local y0 = 48 + 4 * math.sin(i * 0.5 + 1.7)
		local h = 4 + 4 * math.abs(math.sin(i * 0.8 + 1.7))
		table.insert(out, B(V(6.8, h, 0.4), V(x, y0 + h / 2, 46.0), C.neonAurP, SKY))
	end
	return out, FleaKit.Signs()
end

return GlacierHall

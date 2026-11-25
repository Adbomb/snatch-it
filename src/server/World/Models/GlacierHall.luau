-- Уровень 5 «Ледник» — «Замёрзшая галерея коллекционера» (D64, D65; концепт-лист boss5_v2/2_arena.png, площадка r 32
-- и глыба во сне справа от Йети — решение владельца 2026-11-24). Переделка 2026-11-24 по замечаниям владельца: «сделай
-- намного красивее ледяной биом», «убери сверху ледяную радугу», «чтобы игрок мог спокойно бегать между уровнями».
-- Свободный бег: три прямых прохода через всю зону — центральный (|x| ≤ 7: вход → площадка → перевал в леднике → выход)
-- и две боковые полосы |x| 48–66 (продолжение полос «Пустыни», DesertOasis.Lane) — без твёрдых деталей; на площадке
-- нет каната и столбиков, весь декор между проходами — без столкновений. Твёрдое — только площадка (ступени ≤ 0.7),
-- ледник за ареной, витрины и ели у стен.
-- Оформление: в центре «замёрзшее озеро» (r 32) — синяя кромка, кольца, снежинка-трещины, четыре плиты существ
-- (MapLayout.Arenas[5]), светящееся ледяное кольцо по краю (ниже 0.4); за ареной — природный ледник (замечание
-- 2026-11-25 «не замок»): ступенчатый массив с трещинами, пики разной высоты из-за него, бледный дальний хребет,
-- уступы с витринами; проходы — перевалы между пиками. У стен
-- обрыва — ледяные скалы до кромки (нижний ярус твёрдый ≤ 12, верх — без столкновений), ели группами, кристаллы,
-- замёрзшие пруды, сугробы; на снегу — голубые наледи. Экспонаты витрин — только предметы. Света мало (витрины,
-- пруды, плиты существ), частиц нет; поперёк коридора ничего (D41). Координаты зоны: x — поперёк (±92), z — вдоль
-- (вход −47.5, выход +47.5), y = 0 — пол. Надписи возвращаются списком (их пишет WorldBuilder).
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
local SOFT = { variant = "LegoSquaresSoft" } -- большие плоскости ледника: мягкие пупырышки
local SOFT_DECOR = { variant = "LegoSquaresSoft", collide = false, shadow = false }
local WEDGE_DECOR = { shape = "Wedge", collide = false }

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

local C = {
	path = hex("CFE6F6"),
	tile = hex("8FCDF0"),
	edge = hex("8CCBEB"), -- кромка дорожек: спокойный голубой (не «неоновая» полоса)
	-- «замёрзшее глубокое озеро» (замечание 2026-11-25 «белое на белом»): насыщенный синий, к краю темнее
	lakeRim = hex("0F3B74"),
	lake = hex("1E5EA6"),
	lakeRing = hex("16488A"),
	lakeMid = hex("286CB6"),
	lakeRing2 = hex("1A5296"),
	lakeCore = hex("2F79C2"),
	crack = hex("1F4E96"), -- тонкие трещины-снежинка: чуть темнее льда, без неона (спокойный лёд)
	glow = hex("5FDCFF"), -- подсветка плит существ и кольцо по краю (неон)
	slot = hex("13274B"), -- плита существа: тёмный круг
	platEdge = hex("3F98D6"),
	-- ледник: стена за Йети — тёмно-синяя, со щелями-тенями; боковые скалы — средний синий
	wall1 = hex("2A68AE"),
	wall2 = hex("22599C"),
	wall3 = hex("1B4B88"),
	wallShadow = hex("0F2C58"),
	farA = hex("C8D6EE"), -- дальний хребет: бледный, чуть сиреневый (воздушная перспектива)
	farB = hex("B6C4E4"),
	crevDeep = hex("14295A"), -- глубина расселины между глыбами массива
	farSnow = hex("EEF3FA"),
	glacier = hex("6FAEE0"),
	glacierM = hex("4E92D0"),
	glacierD = hex("3577BB"),
	glacierDeep = hex("1F5596"),
	glacierE = hex("EAFBFF"),
	snow = hex("F6FAFF"),
	snowS = hex("DCE8F7"),
	ice = hex("BDEBFF"),
	cave = hex("1F3A6E"),
	gold = hex("F5B21C"),
	goldD = hex("C27E0E"),
	stone = hex("4E5F8C"),
	stoneD = hex("35426A"),
	pine = hex("2F7A5A"),
	pineL = hex("3D9468"),
	pineD = hex("23604A"),
	trunk = hex("8F5A31"),
	crev = hex("203A66"),
	neonIce = hex("6FF2FF"),
	neonGem = hex("FF4FA3"),
	red = hex("E8384F"),
	white = hex("FFFFFF"),
	dark = hex("161824"),
	iceCase = hex("9FE6FF"),
}

-- Площадка (диаметры и верх дисков снизу вверх; каждый следующий выше на 0.06 — грани не совпадают, D36). Верх
-- центрального диска — Arenas[5].floor: на нём стоит Йети.
local DISCS = {
	{ 65.6, -0.06, 0.40, C.lakeRim },
	{ 64, -0.055, 0.46, C.lake },
	{ 53.6, -0.05, 0.52, C.lakeRing },
	{ 52, -0.045, 0.58, C.lakeMid },
	{ 28.6, -0.04, 0.64, C.lakeRing2 },
	{ 27.4, -0.035, 0.70, C.lakeCore },
}

local GlacierHall = {}

-- Свободные проходы (D62, замечание владельца 2026-11-24): отрезки {x0, z0, x1, z1, ширина}. Центральный — от входа к
-- площадке и от площадки через ворота ледника к выходу; две боковые полосы — через всю зону (|x| 48–66, как полосы
-- «Пустыни»). В полосе каждого отрезка нет твёрдых деталей выше порога 1.1 и ниже 7 (scripts/lune/check_world.luau).
GlacierHall.Paths = {
	{ 0, -47.3, 0, -37.4, 14 },
	{ 0, 26.6, 0, 47.3, 14 },
	{ -57, -47.3, -57, 47.3, 18 },
	{ 57, -47.3, 57, 47.3, 18 },
}
GlacierHall.Lane = { 48, 66 } -- боковые полосы свободного бега (|x|)

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

-- Пик со снежной шапкой (верхние 30 % чуть шире и выше — скаты не совпадают).
local function snowPeak(
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
	solid: boolean
)
	peak(out, along, apex, left, right, c, depth, base, h, color, if solid then { shape = "Wedge" } else WEDGE_DECOR)
	peak(
		out,
		along,
		apex,
		left * 0.32 + 0.2,
		right * 0.32 + 0.2,
		c,
		depth + 0.3,
		base + h * 0.68 - 0.1,
		h * 0.32 + 0.25,
		C.glacierE,
		WEDGE_DECOR
	)
end

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
-- крышка, экспонат внутри.
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

-- Ель: ствол и четыре ступенчатых яруса (через один повёрнуты на 45°, светлый и тёмный) со снегом, макушка-снежок.
local function pine(out: { Brick }, x: number, z: number, scale: number, yaw: number)
	local s = scale
	table.insert(out, Box(x - 0.6 * s, x + 0.6 * s, 0, 3 * s, z - 0.6 * s, z + 0.6 * s, C.trunk))
	for i, tier in { { 7.2, 2.0, 2.4 }, { 5.8, 4.1, 2.3 }, { 4.4, 6.1, 2.2 }, { 2.9, 8.0, 2.0 } } do
		local w, y0, h = tier[1] * s, tier[2] * s, tier[3] * s
		local turn = CFrame.Angles(0, math.rad(yaw + (i % 2) * 45), 0)
		local color = if i % 2 == 0 then C.pineD else (if i == 3 then C.pineL else C.pine)
		table.insert(out, B(V(w, h, w), CFrame.new(x, y0 + h / 2, z) * turn, color, DECOR))
		table.insert(out, B(V(w * 0.74, 0.42 * s, w * 0.74), CFrame.new(x, y0 + h + 0.12 * s, z) * turn, C.snow, DECOR))
	end
	table.insert(
		out,
		B(V(1.2, 1.2, 1.2) * s, CFrame.new(x, 10.7 * s, z) * CFrame.Angles(0, math.rad(yaw), 0), C.snow, DECOR)
	)
end

-- Сугроб: два мягких бугра (без столкновений, по ним проходят).
local function drift(out: { Brick }, x: number, z: number, yaw: number, s: number)
	local turn = CFrame.Angles(0, math.rad(yaw), 0)
	table.insert(out, B(V(8, 0.9, 5.5) * s, CFrame.new(x, 0.42 * s, z) * turn, C.snowS, SOFT_DECOR))
	table.insert(
		out,
		B(V(4.6, 1.6, 3.4) * s, CFrame.new(x, 0.78 * s, z) * turn * CFrame.new(-0.9 * s, 0, 0.3 * s), C.snow, DECOR)
	)
end

-- Кристаллы: связка ледяных шипов (наклонены в разные стороны), один светится. Без столкновений.
local function crystals(out: { Brick }, x: number, z: number, s: number, yaw: number)
	local base = CFrame.new(x, 0, z) * CFrame.Angles(0, math.rad(yaw), 0)
	for i, k in
		{
			{ 0, 0, 5.0, 0, 1.3, C.glacierD },
			{ 1.3, 0.4, 3.4, 18, 1.0, C.ice },
			{ -1.2, 0.5, 3.0, -20, 0.9, C.glacier },
			{ 0.3, -1.1, 2.4, 12, 0.8, C.neonIce },
		}
	do
		local h, w = k[3] * s, k[5] * s
		local at = base
			* CFrame.new(k[1] * s, 0, k[2] * s)
			* CFrame.Angles(math.rad(k[4] * 0.5), math.rad(i * 37), math.rad(k[4]))
			* CFrame.new(0, h / 2, 0)
		table.insert(out, B(V(w, h, w), at, k[6], if i == 4 then NEON else DECOR))
		-- остриё: куб на вершине, наполовину в кристалле (грани под углом — не совпадают с гранями тела)
		table.insert(
			out,
			B(
				V(w * 0.74, w * 0.74, w * 0.74),
				at * CFrame.new(0, h / 2, 0) * FleaKit.DIAMOND,
				k[6],
				if i == 4 then NEON else DECOR
			)
		)
	end
end

-- Замёрзший пруд: каменный бортик, гладкий лёд, светлые блики, лунка со светом снизу.
local function pond(out: { Brick }, x: number, z: number, w: number, d: number)
	table.insert(
		out,
		Box(x - w / 2 - 1.4, x + w / 2 + 1.4, -0.05, 0.28, z - d / 2 - 1.4, z + d / 2 + 1.4, C.snow, SOFT_DECOR)
	)
	table.insert(
		out,
		Box(x - w / 2 - 0.6, x + w / 2 + 0.6, -0.04, 0.34, z - d / 2 - 0.6, z + d / 2 + 0.6, C.stone, DECOR)
	)
	table.insert(out, Box(x - w / 2, x + w / 2, -0.03, 0.4, z - d / 2, z + d / 2, C.glacierD, DECOR))
	for i, k in { { -0.22, -0.1, 0.4, 0.07 }, { 0.15, 0.2, 0.3, 0.05 } } do
		local at = CFrame.new(x + k[1] * w, 0.41, z + k[2] * d) * CFrame.Angles(0, math.rad(35 + i * 20), 0)
		table.insert(out, B(V(w * k[3], 0.06, 0.5), at, C.white, DECOR))
	end
	table.insert(out, Disc(2.4, -0.03, 0.44, x + w * 0.25, z - d * 0.2, C.glacierDeep))
	table.insert(
		out,
		FleaKit.Neon(V(0.2, 1.6, 1.6), CFrame.new(x + w * 0.25, 0.45, z - d * 0.2) * FleaKit.UPRIGHT, C.neonIce, 12)
	)
	out[#out].shape = "Cylinder"
end

-- Наледь на снегу: плоское голубое пятно из двух повёрнутых плит (ниже 0.2 — по ней бегут).
local function icePatch(out: { Brick }, x: number, z: number, w: number, d: number, yaw: number)
	local turn = CFrame.Angles(0, math.rad(yaw), 0)
	table.insert(out, B(V(w, 0.1, d), CFrame.new(x, 0.03, z) * turn, C.glacierM, DECOR))
	table.insert(
		out,
		B(
			V(w * 0.6, 0.1, d * 1.3),
			CFrame.new(x, 0.05, z) * turn * CFrame.Angles(0, math.rad(40), 0),
			C.glacierE,
			DECOR
		)
	)
end

-- Путь: светлая плита вдоль отрезка (без столкновений) с голубой кромкой и ледяными ромбами по оси.
local function path(out: { Brick }, p: { number }, top: number, w: number)
	local x0, z0, x1, z1 = p[1], p[2], p[3], p[4]
	local dx, dz = x1 - x0, z1 - z0
	local len = math.sqrt(dx * dx + dz * dz)
	local at = CFrame.new((x0 + x1) / 2, 0, (z0 + z1) / 2) * CFrame.Angles(0, math.atan2(dx, dz), 0)
	table.insert(out, B(V(w, top + 0.04, len), at * CFrame.new(0, (top - 0.04) / 2, 0), C.path, DECOR))
	for _, side in { -1, 1 } do
		local strip = at * CFrame.new(side * (w / 2 - 0.3), (top + 0.02) / 2, 0)
		table.insert(out, B(V(0.8, top + 0.1, len - 0.4), strip, C.edge, DECOR))
	end
	local count = math.max(1, math.floor(len / 9))
	for k = 1, count do
		local u = -len / 2 + (k - 0.5) * len / count
		local tileAt = at * CFrame.new(0, (top + 0.04) / 2, u) * CFrame.Angles(0, math.rad(45), 0)
		table.insert(out, B(V(2, top + 0.08, 2), tileAt, C.tile, DECOR))
	end
end

-- Ледяные скалы у стен обрыва (|x| 84–92.6): закрывают землю обрыва до кромки. Нижний ярус твёрдый (≤ 12 — с него
-- не допрыгнуть до кромки), выше — ступенчатые глыбы без столкновений, снежная шапка поверх кромки, над каждой
-- скалой — пик своей высоты (неровный верх, без сосулек и ровного карниза).
local function iceCliffs(out: { Brick })
	for _, s in { -1, 1 } do
		local z, k = -47.5, 0
		while z < 47.5 do
			k += 1
			local len = 8 + (k * 37 % 5)
			local z1 = math.min(z + len, 47.5)
			local function X(a: number, b: number): (number, number)
				return math.min(s * a, s * b), math.max(s * a, s * b)
			end
			local inner = 84 + (k * 53 % 4) - (if k % 3 == 1 then 2 else 0) -- через две — выступ скалы
			local low = 9 + (k * 29 % 4)
			local mid = 20 + (k * 17 % 6)
			local cMain = if k % 3 == 0 then C.glacierM else C.glacier
			local x0, x1 = X(inner, 92.6)
			table.insert(out, Box(x0, x1, 0, low, z, z1, cMain, SOFT))
			-- ледяной скат у подножия (поднимается к стене), сугроб перед ним, тёмная трещина на стыке скал
			local h = low * (0.55 + (k % 2) * 0.2)
			table.insert(
				out,
				B(
					V(z1 - z - 0.8, h, 2.4),
					CFrame.new(s * (inner - 1.15), h / 2, (z + z1) / 2) * CFrame.Angles(0, math.rad(s * 90), 0),
					if k % 2 == 0 then C.ice else C.glacierE,
					{ shape = "Wedge", variant = "LegoSquaresSoft" }
				)
			)
			table.insert(
				out,
				B(
					V(2.8, 0.8 + (k % 3) * 0.25, (z1 - z) * 0.62),
					CFrame.new(s * (inner - 3.2), 0.38, (z + z1) / 2 + ((k % 3) - 1) * 0.8),
					C.snow,
					SOFT_DECOR
				)
			)
			x0, x1 = X(inner - 0.18, inner + 1.2)
			table.insert(out, Box(x0, x1, 1.2, low - 1.15, z - 0.28, z + 0.28, C.glacierDeep, DECOR))
			-- средний и верхний ярус: наклонены верхом к стене и повёрнуты (у соседних скал — разные углы), низ
			-- заходит в ярус ниже
			local lean = -s * (4 + (k % 3) * 2)
			local turn = s * ((k % 3) - 1) * 4
			local function tier(a: number, b: number, y0: number, y1: number, inset: number, color: Color3)
				local at = CFrame.new(s * (a + b) / 2, (y0 + y1) / 2, (z + z1) / 2)
					* CFrame.Angles(0, math.rad(turn), math.rad(lean))
				table.insert(out, B(V(b - a, y1 - y0, z1 - z - inset * 2), at, color, SOFT_DECOR))
			end
			tier(inner + 1.6, 92.8, low - 0.7, mid, 0.15, if k % 2 == 0 then C.glacierD else C.glacierM)
			tier(inner + 3.4, 93.0, mid - 0.7, 31.6, 0.3, if k % 2 == 0 then C.glacier else C.glacierD)
			-- снежная шапка на кромке (выше травы обрыва 32.7)
			-- соседние шапки заходят друг на друга на 0.1: края и низ через одну сдвинуты (грани не совпадают)
			local odd = k % 2
			x0, x1 = X(inner + 2.6 + odd * 0.15, 94.5 + odd * 0.2)
			table.insert(out, Box(x0, x1, 31.5 - odd * 0.1, 33.5 + odd * 0.4, z - 0.05, z1 + 0.05, C.snow, DECOR))
			-- пик над каждой скалой (вдоль стены): высота и смещение вершины разные
			do
				local apex = (z + z1) / 2 + ((k % 3) - 1) * 1.5
				snowPeak(
					out,
					"z",
					apex,
					apex - z - 0.6,
					z1 - apex - 0.6,
					s * (inner + 95) / 2,
					95 - inner - 4.2,
					33.3,
					4 + (k * 11 % 7),
					C.glacierE,
					false
				)
			end
			z = z1
		end
	end
end

-- Ледник за ареной (замечание 2026-11-25 «не замок — природный ледник»; четвёртый заход по двум кругам разбора
-- кадров): общий ступенчатый массив — наклонные ярусы-скаты к арене (передний — бледный лёд, второй — синие глыбы с
-- настоящими расселинами: щель между глыбами и тёмная глубина за ней), из-за массива поднимаются пики разной формы
-- (иглы, наклонённые, с плечом; снег — на освещённом склоне, на теневом только кончик; силуэт «V»: за Йети низко,
-- высокие пики по краям), позади отдельно — бледный дальний хребет (воздушная перспектива). Над полосами — перевалы
-- между двумя пиками с отвесным склоном к полосе. Перед массивом — россыпь обломков льда. Ни стоячих брусков, ни
-- карнизов, ни сосулек, ни мостов. Проходы — центральный (|x| ≤ 7) и полосы |x| 48–66 — свободны.

-- Ярус массива (скат к арене): |x| центра, ширина, высота, z центра, глубина, поворот, крен (градусы; справа
-- зеркально), цвет, снег на верхнем крае (смещение по x или nil). Между глыбами второго яруса — щели 1–1.6.
local TIER1 = {
	[-1] = {
		{ 15, 13, 5.5, 38.8, 6, -4, 2, C.glacier },
		{ 28, 14, 4.5, 39.2, 6, 5, -3, C.glacierM },
		{ 40.5, 12, 6, 38.9, 6, -6, 3, C.glacier },
	},
	[1] = {
		{ 14.5, 12, 4.5, 39.0, 6, 6, -2, C.glacierM },
		{ 27, 15, 6, 38.7, 6.4, -5, 3, C.glacier },
		{ 40, 13, 5, 39.3, 6, 4, -2, C.glacierM },
	},
}
local TIER2 = {
	[-1] = {
		{ 13.6, 10.8, 9, 42.2, 6, 5, -3, C.wall2, -1.5 },
		{ 26.3, 12.2, 14, 42.6, 6.5, -4, 4, C.wall1, nil },
		{ 39.55, 11.9, 12, 42.0, 6.5, 6, -3, C.wall2, 2 },
	},
	[1] = {
		{ 13.4, 10.8, 8, 42.4, 6, -5, 3, C.wall1, 1 },
		{ 26.0, 12.4, 13, 42.0, 6.5, 4, -4, C.wall2, -2 },
		{ 39.65, 11.7, 15, 42.8, 6.2, -6, 3, C.wall1, nil },
	},
}
-- Пик: |x| вершины, z, полуширина к центру, наружу, высота, толщина, поворот, крен, оттенок (1…3), доля снега на
-- освещённом склоне, плечо {сдвиг наружу, полуширины к центру и наружу, доля высоты} или nil. Задние углы — не
-- дальше z 45.9 (дальний хребет начинается с 45.95).
local PEAKS = {
	[-1] = {
		{ 12, 43.6, 3.5, 6.5, 14, 4, 2, 3, 2, 0.35 },
		{ 21.5, 43.4, 6, 3.5, 24, 4, -2, -5, 1, 0.45, { 4.5, 3, 4, 0.55 } },
		{ 31, 43.5, 3.5, 7.5, 31, 4, 1.5, 4, 3, 0.3 },
		{ 40.5, 43.3, 7, 4, 21, 4, -1.5, -3, 2, 0.5, { -5, 3, 3, 0.5 } },
	},
	[1] = {
		{ 13.5, 43.5, 4, 6, 13, 4, -2, -4, 1, 0.4 },
		{ 23.5, 43.2, 3.5, 8, 26, 4, 2, 5, 3, 0.3, { 5, 3, 4.5, 0.5 } },
		{ 34, 43.6, 7.5, 4, 33, 4, -1.5, -3, 2, 0.42 },
		{ 42, 43.4, 5, 4, 20, 4, 2, 4, 1, 0.35 },
	},
}
-- Дальний хребет (без столкновений, бледный, отдельно позади пиков): |x| вершины, z, полуширины, высота.
local BACK = {
	[-1] = { { 18, 46.8, 10, 12, 38 }, { 37, 46.6, 9, 9.5, 34 } },
	[1] = { { 20, 46.75, 12, 10, 40 }, { 38, 46.55, 8, 9, 35 } },
}
-- Обломки льда перед массивом (без столкновений, мимо витрин): |x|, z.
local RUBBLE = {
	{ 9.5, 36.6 },
	{ 10.8, 36.2 },
	{ 13.5, 37.0 },
	{ 17, 36.5 },
	{ 21, 36.2 },
	{ 24.5, 36.9 },
	{ 27, 36.4 },
	{ 35.8, 36.8 },
	{ 44.5, 36.6 },
}
local SHADES = {
	[1] = { C.wall1, C.wall2 },
	[2] = { C.wall2, C.wall3 },
	[3] = { C.wall1, C.wall3 },
}
local MASS = { shape = "Wedge", variant = "LegoSquaresSoft" }
local MASS_DECOR = { shape = "Wedge", variant = "LegoSquaresSoft", collide = false, shadow = false }

-- Треугольник из двух клиньев спиной к спине в кадре at (низ, вершина над началом): left/right — полуширины,
-- depth — толщина.
local function ridge(
	out: { Brick },
	at: CFrame,
	left: number,
	right: number,
	h: number,
	depth: number,
	cl: Color3,
	cr: Color3,
	extra: { [string]: any }
)
	table.insert(
		out,
		B(V(depth, h, left), at * CFrame.new(-left / 2, h / 2, 0) * CFrame.Angles(0, math.rad(90), 0), cl, extra)
	)
	table.insert(
		out,
		B(V(depth, h, right), at * CFrame.new(right / 2, h / 2, 0) * CFrame.Angles(0, math.rad(-90), 0), cr, extra)
	)
end

-- Снег на склоне треугольника (side −1 — левый, 1 — правый): клин с вершиной на 0.3 выше вершины горы, низ — на доле
-- f от верха; шире склона на ≥ 0.06 и толще на 0.2, задняя грань на 0.05 от оси вершины (грани не совпадают).
local function snowSide(
	out: { Brick },
	at: CFrame,
	side: number,
	half: number,
	h: number,
	depth: number,
	f: number,
	c: Color3
)
	local w, sh = half * f + 0.3, h * f + 0.4
	local frame = at
		* CFrame.new(side * (w / 2 + 0.05), h * (1 - f) - 0.1 + sh / 2, 0)
		* CFrame.Angles(0, math.rad(-side * 90), 0)
	table.insert(out, B(V(depth + 0.2, sh, w), frame, c, WEDGE_DECOR))
end

-- Пик (summit) с вершиной над (x, 0, z): поворот yaw и крен roll (низ уходит в землю), склоны разного оттенка; снег — доля f
-- на левом (освещённом) склоне и короткий кончик на правом; плечо — пик пониже сбоку, на 0.3 позади.
local function summit(
	out: { Brick },
	x: number,
	z: number,
	left: number,
	right: number,
	h: number,
	depth: number,
	yaw: number,
	roll: number,
	cl: Color3,
	cr: Color3,
	extra: { [string]: any },
	f: number
): CFrame
	local sink = math.abs(math.sin(math.rad(roll))) * math.max(left, right)
	local at = CFrame.new(x, -sink, z) * CFrame.Angles(0, math.rad(yaw), math.rad(roll))
	ridge(out, at, left, right, h, depth, cl, cr, extra)
	snowSide(out, at, -1, left, h, depth, f, C.snow)
	snowSide(out, at, 1, right, h, depth, f * 0.4, C.snowS)
	return at
end

-- Скат (клин) с низом на полу: поворот yaw, крен roll — верхний край наклонён, низ уходит в пол.
local function slope(w: number, h: number, x: number, z: number, yaw: number, roll: number): CFrame
	local sink = math.abs(math.sin(math.rad(roll))) * w / 2
	return CFrame.new(x, h / 2 - sink, z) * CFrame.Angles(0, math.rad(yaw), math.rad(roll))
end

-- Снег на верхнем крае клина: клин того же уклона на 0.2 выше ската, задняя грань на 0.15 впереди.
local function snowTop(out: { Brick }, at: CFrame, w: number, h: number, d: number, u: number, k: number, c: Color3)
	local top = h / 2 - 0.15 * h / d + 0.2
	table.insert(
		out,
		B(V(w, h * k, d * k), at * CFrame.new(u, top - h * k / 2, d / 2 - 0.15 - d * k / 2), c, WEDGE_DECOR)
	)
end

-- Сторона: полуширины «к центру / наружу» → «влево / вправо» (координата x зоны).
local function sides(s: number, inner: number, outer: number): (number, number)
	if s > 0 then
		return inner, outer
	end
	return outer, inner
end

local function glacier(out: { Brick })
	for _, s in { -1, 1 } do
		-- передний ярус: бледный лёд
		for _, t in TIER1[s] do
			local at = slope(t[2], t[3], s * t[1], t[4], s * t[6], s * t[7])
			table.insert(out, B(V(t[2], t[3], t[5]), at, t[8], MASS))
		end
		-- второй ярус: синие глыбы со снегом на верхнем крае; в щели между соседними — тёмная глубина (клин того же
		-- уклона, на 0.8 позади и на 1.5 ниже)
		local tiers = TIER2[s]
		for i, t in tiers do
			local w, h, d = t[2], t[3], t[5]
			local at = slope(w, h, s * t[1], t[4], s * t[6], s * t[7])
			table.insert(out, B(V(w, h, d), at, t[8], MASS))
			if t[9] then
				snowTop(out, at, w * 0.55, h, d, s * t[9], 0.3, C.snow)
			end
			local nxt = tiers[i + 1]
			if nxt then
				local gx = ((t[1] + w / 2) + (nxt[1] - nxt[2] / 2)) / 2
				local gh = math.min(h, nxt[3]) - 1.5
				local gat = slope(3.2, gh, s * gx, (t[4] + nxt[4]) / 2 + 0.8, s * (t[6] + nxt[6]) / 2, 0)
				table.insert(out, B(V(3.2, gh, 5), gat, C.crevDeep, MASS))
			end
		end
		-- пики из-за массива (с плечом у некоторых)
		for _, p in PEAKS[s] do
			local l, r = sides(s, p[3], p[4])
			local sh = SHADES[p[9]]
			local at = summit(out, s * p[1], p[2], l, r, p[5], p[6], s * p[7], s * p[8], sh[1], sh[2], MASS, p[10])
			local sp = p[11]
			if sp then
				local sl, sr = sides(s, sp[2], sp[3])
				local shoulder = at * CFrame.new(s * sp[1], -0.3, 0.3)
				ridge(out, shoulder, sl, sr, p[5] * sp[4], p[6] * 0.9, sh[1], sh[2], MASS)
				snowSide(out, shoulder, -1, sl, p[5] * sp[4], p[6] * 0.9, 0.3, C.snow)
			end
		end
		-- дальний хребет: бледный, без поворота, отдельно позади пиков
		for _, b in BACK[s] do
			local l, r = sides(s, b[3], b[4])
			summit(out, s * b[1], b[2], l, r, b[5], 1.2, 0, 0, C.farA, C.farB, MASS_DECOR, 0.3)
		end
		-- перевал над полосой: по сторонам — пики с отвесным склоном к полосе (основание до |x| 47.4 и от 66.6)
		local li, lo = sides(s, 6, 1.9)
		summit(out, s * 45.5, 42.5, li, lo, 26, 9, s * 2, 0, C.wall2, C.wall3, MASS, 0.3)
		local oi, oo = sides(s, 1.9, 7)
		summit(out, s * 68.5, 42.4, oi, oo, 30, 9, -s * 2, 0, C.wall1, C.wall3, MASS, 0.34)
		-- у стены обрыва: ярусы (твёрдые ≤ 24) и пики (без столкновений)
		local o1 = slope(18, 10, s * 81, 40.5, -s * 3, s * 2)
		table.insert(out, B(V(18, 10, 7), o1, C.glacierM, MASS))
		local o2 = slope(17, 20, s * 81.5, 43.6, s * 4, -s * 3)
		table.insert(out, B(V(17, 20, 6), o2, C.wall2, MASS))
		snowTop(out, o2, 9, 20, 6, s * 2, 0.28, C.snow)
		summit(out, s * 77, 44.6, 5, 6, 34, 4.4, s * 3, -s * 3, C.wall1, C.wall3, MASS_DECOR, 0.45)
		summit(out, s * 85.5, 44.6, 6, 6, 30, 4.6, -s * 4, s * 4, C.wall2, C.wall3, MASS_DECOR, 0.35)
		-- обломки льда перед массивом: разного размера, наклонены, наполовину в снегу
		for i, r in RUBBLE do
			local w, hh, d = 1.4 + (i * 7 % 5) * 0.35, 0.9 + (i * 3 % 4) * 0.3, 1.2 + (i * 5 % 4) * 0.3
			local at = CFrame.new(s * r[1], hh / 2 - 0.25, r[2])
				* CFrame.Angles(math.rad((i * 13 % 25) - 12), math.rad(s * i * 37), math.rad(s * ((i * 17 % 29) - 14)))
			table.insert(
				out,
				B(V(w, hh, d), at, if i % 3 == 0 then C.glacierM elseif i % 2 == 0 then C.ice else C.glacierE, DECOR)
			)
		end
		-- уступ перед массивом — две неровные плиты (верх 1.2 и 1.15), на нём витрины
		for j, sl in { { 22, 9.5, 1.2, 3 }, { 36.5, 9, 1.15, -4 } } do
			local at = CFrame.new(s * sl[1], sl[3] / 2, 34.4) * CFrame.Angles(0, math.rad(s * sl[4]), 0)
			table.insert(out, B(V(sl[2] * 2, sl[3], 5.6 - j * 0.4), at, C.glacierD, SOFT))
		end
		for j, v in { { "trophy", 31.5 }, { "clock", 40.5 } } do
			local kind = if s > 0 then v[1] else (if j == 1 then "gem" else "crown")
			vitrine(out, kind, s * v[2], 33.4, 1.1, 2.7, 4, 7.4, 1)
			if kind == "gem" then
				out[#out].light = { range = 12, brightness = 0.9, color = C.neonGem }
			end
		end
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

	-- «Замёрзшее озеро»: кромка, поле, кольца мозаики (каждый следующий диск выше), снежинка — тонкие трещины во льду (лучи и «ёлочки», без неона)
	for _, d in DISCS do
		table.insert(out, Disc(d[1], d[2], d[3], cx, cz, d[4], SOLID))
	end
	-- шесть ломаных лучей из четырёх отрезков (изломы 9–14°, через один в другую сторону); верх отрезков через один
	-- 0.83 / 0.77, «ёлочки» у первого и третьего излома — 0.8 / 0.68 (диски 0.70 / 0.58 ниже, грани не совпадают)
	for k = 0, 5 do
		local deg = k * 60 + 30
		local sign = if k % 2 == 0 then 1 else -1
		local px, pz = polar(deg, 8.5)
		for i, seg in { { 4.6, 0 }, { 4.2, 14 }, { 4.0, -11 }, { 3.4, 9 } } do
			local a = math.rad(deg + sign * seg[2])
			local len = seg[1]
			local top = if i % 2 == 1 then 0.83 else 0.77
			local mx, mz = px + math.sin(a) * len / 2, pz + math.cos(a) * len / 2
			table.insert(
				out,
				B(V(0.1, 0.3, len + 0.2), CFrame.new(mx, top - 0.15, mz) * CFrame.Angles(0, a, 0), C.crack, DECOR)
			)
			px, pz = px + math.sin(a) * len, pz + math.cos(a) * len
			if i == 1 or i == 3 then
				local bl, btop = if i == 1 then 3.6 else 3.0, if i == 1 then 0.8 else 0.68
				for _, side in { -1, 1 } do
					local br = a + math.rad(side * (40 + i * 4))
					local at = CFrame.new(px + math.sin(br) * bl / 2, btop - 0.15, pz + math.cos(br) * bl / 2)
					table.insert(out, B(V(0.08, 0.3, bl), at * CFrame.Angles(0, br, 0), C.crack, DECOR))
				end
			end
		end
	end
	-- места четырёх существ (замечание 2026-11-25 «добыча видна от входа»): тёмный круг с золотым ободом на
	-- светящемся кольце (подсветка снизу), верх — Arenas[5].top
	for _, s in arena.slots do
		table.insert(out, Disc(6.9, 0.3, 0.6, s.X, s.Y, C.glow, NEON)) -- выше пола 0.46 на 0.14
		out[#out].light = { range = 9, brightness = 0.7, color = C.glow }
		table.insert(out, Disc(6.1, 0.31, arena.top - 0.07, s.X, s.Y, C.gold, SOLID))
		table.insert(out, Disc(5.3, 0.32, arena.top, s.X, s.Y, C.slot, SOLID))
	end
	-- светящееся ледяное кольцо по краю площадки (низкое, по нему пробегают): 24 неоновых отрезка
	for k = 0, 23 do
		local deg = k * 15
		local x, z = polar(deg + 7.5, 33.7)
		local at = CFrame.new(x, 0.2, z) * CFrame.Angles(0, math.rad(deg + 7.5 + 90), 0)
		table.insert(out, B(V(8.6, 0.34, 0.7), at, C.glow, NEON))
	end

	-- проходы: центральный и две боковые полосы (светлые, с голубой кромкой и ромбами)
	for i, p in GlacierHall.Paths do
		path(out, p, if i <= 2 then 0.28 else 0.26, if i <= 2 then 12 else 12)
	end

	glacier(out)
	iceCliffs(out)

	-- у стен (|x| ≥ 70): ели группами, витрины, пруды, кристаллы, сугробы — вне полос бега
	for _, t in
		{
			{ -74, -40, 1.1, 0 },
			{ -77.5, -32, 0.85, 20 },
			{ 76, -38, 1.0, 10 },
			{ 77.5, -28, 0.8, 35 },
			{ -76, 10, 1.15, 15 },
			{ -77.5, 20, 0.85, 40 },
			{ 75, 16, 1.1, 25 },
			{ 77.5, 26, 0.9, 5 },
			{ -72, 40, 0.95, 30 },
			{ 74, 42, 1.0, 12 },
		}
	do
		pine(out, t[1], t[2], t[3], t[4])
	end
	for _, v in { { "key", -74, -12 }, { "crystal", 74, -10 } } do
		table.insert(out, Disc(6.8, -0.05, 0.9, v[2], v[3], C.stoneD, SOLID))
		vitrine(out, v[1], v[2], v[3], 0.85, 2.6, 6, 8.6, 1.35)
		if v[1] == "crystal" then
			out[#out].light = { range = 14, brightness = 1, color = C.neonIce }
		end
	end
	pond(out, -74, 28, 9, 7)
	pond(out, 74, 2, 8, 9)
	for _, c in
		{
			{ -70, -24, 1.2, 10 },
			{ 71, -22, 1.0, 40 },
			{ -80, 2, 0.9, 70 },
			{ 81, 36, 1.1, 20 },
			{ -82, 36, 1.0, 55 },
			{ 82, -44, 0.9, 15 },
		}
	do
		crystals(out, c[1], c[2], c[3], c[4])
	end
	for _, d in { { -70, -44, 15, 1 }, { 70, 32, -20, 0.9 }, { -70, 4, -10, 0.8 } } do
		drift(out, d[1], d[2], d[3], d[4])
	end
	-- между проходами (без столкновений): наледи на снегу, низкие кристаллы и сугробы
	for _, p in
		{
			{ -30, -43, 9, 5, 20 },
			{ 31, -43, 8, 6, -15 },
			{ -40, 10, 7, 9, 30 },
			{ 40, 4, 8, 7, -25 },
			{ -76, -2, 6, 5, 10 },
			{ 78, -30, 6, 4, 40 },
		}
	do
		icePatch(out, p[1], p[2], p[3], p[4], p[5])
	end
	for _, c in { { -40, -42, 0.55, 20 }, { 40, -44, 0.5, 60 }, { -44, 22, 0.5, 35 }, { 44, 24, 0.45, 80 } } do
		crystals(out, c[1], c[2], c[3], c[4])
	end
	drift(out, -26, -40, 10, 0.6)
	drift(out, 24, -42, -15, 0.55)

	-- трещины с голубым светом (плоские) у стен
	for _, cr in { { -82, -42, -70, -30 }, { 70, 10, 82, 22 } } do
		local x0, z0, x1, z1 = cr[1], cr[2], cr[3], cr[4]
		local dx, dz = x1 - x0, z1 - z0
		local len = math.sqrt(dx * dx + dz * dz)
		local at = CFrame.new((x0 + x1) / 2, 0, (z0 + z1) / 2) * CFrame.Angles(0, math.atan2(-dz, dx), 0)
		table.insert(out, B(V(len, 0.14, 2.4), at * CFrame.new(0, 0.05, 0), C.crev, DECOR))
		table.insert(out, B(V(len - 2, 0.12, 0.6), at * CFrame.new(0, 0.1, 0), C.neonIce, NEON))
	end

	-- указатели к следующему уровню: у боковых полос и у центрального перевала
	for _, s in { -1, 1 } do
		local x, z = s * 45.5, 33
		table.insert(out, Box(x - 0.2, x + 0.2, 0, 3.7, z - 0.2, z + 0.2, C.trunk))
		table.insert(
			out,
			FleaKit.Board(V(4.6, 1.3, 0.3), V(x, 3.3, z - 0.35), C.platEdge, FleaKit.Label("В ДЖУНГЛИ"))
		)
	end
	-- у центрального перевала — столбик слева от прохода (|x| ≤ 7 свободен, круг боя не задет)
	table.insert(out, Box(-10.8, -10.4, 0, 4.6, 36.2, 36.6, C.trunk))
	table.insert(
		out,
		FleaKit.Board(V(5.6, 1.4, 0.3), V(-10.6, 4.1, 36.05), C.platEdge, FleaKit.Label("В ДЖУНГЛИ"))
	)
	return out, FleaKit.Signs()
end

return GlacierHall

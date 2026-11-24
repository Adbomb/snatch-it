-- Уровень 5 «Ледник» — «Замёрзшая галерея коллекционера» (D64, D65; концепт-лист boss5_v2/2_arena.png, площадка r 32
-- и глыба во сне справа от Йети — решение владельца 2026-11-24). Переделка 2026-11-24 по замечаниям владельца: «сделай
-- намного красивее ледяной биом», «убери сверху ледяную радугу», «чтобы игрок мог спокойно бегать между уровнями».
-- Свободный бег: три прямых прохода через всю зону — центральный (|x| ≤ 7: вход → площадка → ворота в леднике → выход)
-- и две боковые полосы |x| 48–66 (продолжение полос «Пустыни», DesertOasis.Lane) — без твёрдых деталей; на площадке
-- нет каната и столбиков, весь декор между проходами — без столкновений. Твёрдое — только площадка (ступени ≤ 0.7),
-- ледник за ареной, витрины и ели у стен.
-- Оформление: в центре «замёрзшее озеро» (r 32) — синяя кромка, кольца, снежинка-мозаика, четыре плиты существ
-- (MapLayout.Arenas[5]), светящееся ледяное кольцо по краю (ниже 0.4); за ареной — ледник из двух массивов с воротами
-- между ними (ледяной мост, золотая рама, снежинка-герб, сосульки), пики со снегом, уступы с витринами; у стен обрыва —
-- ледяные скалы до кромки (закрывают землю обрыва, нижний ярус твёрдый ≤ 12, верх — без столкновений), ели группами,
-- кристаллы, замёрзшие пруды, сугробы; на снегу — голубые наледи. Экспонаты витрин — только предметы (кубок, самоцвет,
-- будильник, корона, ключ, кристалл). Света мало (герб ворот, два пруда, две витрины), частиц нет; поперёк коридора
-- ничего (D41). Координаты зоны: x — поперёк (±92), z — вдоль (вход −47.5, выход +47.5), y = 0 — пол. Надписи
-- возвращаются списком (их пишет WorldBuilder).
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
	edge = hex("4FC3F7"),
	plat = hex("B7ECFF"),
	platEdge = hex("3F98D6"),
	slot = hex("7FCBF0"),
	mosaic = hex("5FB6E8"),
	mosaicL = hex("E2FAFF"),
	glacier = hex("A6E4FA"),
	glacierM = hex("86D3F3"),
	glacierD = hex("5BB4E2"),
	glacierDeep = hex("3C8FCB"),
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
	{ 65.6, -0.06, 0.40, C.platEdge },
	{ 64, -0.055, 0.46, C.plat },
	{ 53.6, -0.05, 0.52, C.mosaic },
	{ 52, -0.045, 0.58, C.plat },
	{ 28.6, -0.04, 0.64, C.mosaicL },
	{ 27.4, -0.035, 0.70, C.plat },
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
GlacierHall.Gate = { 9.2, 12.4 } -- ворота ледника: полуширина проёма и высота до моста

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
-- не допрыгнуть до кромки), выше — ступенчатые глыбы без столкновений, снежная шапка поверх кромки, сосульки.
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
			x0, x1 = X(inner + 1.6, 92.8)
			table.insert(
				out,
				Box(
					x0,
					x1,
					low - 0.1,
					mid,
					z + 0.15,
					z1 - 0.15,
					if k % 2 == 0 then C.glacierD else C.glacierM,
					SOFT_DECOR
				)
			)
			x0, x1 = X(inner + 3.4, 93.0)
			table.insert(
				out,
				Box(
					x0,
					x1,
					mid - 0.1,
					31.6,
					z + 0.3,
					z1 - 0.3,
					if k % 2 == 0 then C.glacier else C.glacierD,
					SOFT_DECOR
				)
			)
			-- снежная шапка на кромке (выше травы обрыва 32.7) и снег на уступах
			-- соседние шапки заходят друг на друга на 0.1: края и низ через одну сдвинуты (грани не совпадают)
			local odd = k % 2
			x0, x1 = X(inner + 2.6 + odd * 0.15, 94.5 + odd * 0.2)
			table.insert(out, Box(x0, x1, 31.5 - odd * 0.1, 33.5 + odd * 0.4, z - 0.05, z1 + 0.05, C.snow, DECOR))
			x0, x1 = X(inner - 0.25, inner + 1.9)
			table.insert(out, Box(x0, x1, low - 0.3, low + 0.35, z + 0.4, z1 - 0.4, C.snow, DECOR))
			-- пик над скалой (вдоль стены), через один
			if k % 2 == 1 then
				local apex = (z + z1) / 2 + ((k % 3) - 1)
				snowPeak(
					out,
					"z",
					apex,
					apex - z - 0.6,
					z1 - apex - 0.6,
					s * (inner + 95) / 2,
					95 - inner - 4.2,
					33.3,
					4 + (k * 11 % 4),
					C.glacierE,
					false
				)
			end
			-- сосульки под уступом
			for _, u in { 0.25, 0.6 } do
				local zz = z + (z1 - z) * u
				x0, x1 = X(inner - 0.1, inner + 0.6)
				table.insert(
					out,
					Box(x0, x1, low - 2.1 - (k % 2) * 0.6, low - 0.25, zz - 0.3, zz + 0.3, C.glacierE, DECOR)
				)
			end
			z = z1
		end
	end
end

-- Ледник за ареной: два массива (|x| 10–46) с воротами между ними — ледяной мост, золотая рама, снежинка-герб.
-- Массив: ступенчатые глыбы (x от, до, перед, верх, цвет), пики, карниз, сосульки, уступ с витринами.
local MASSIF = {
	{ 10.5, 18, 37.4, 18.5, C.glacier },
	{ 18, 27, 37.8, 21.5, C.glacierM },
	{ 27, 36, 38.0, 17.5, C.glacier },
	{ 36, 46, 39.2, 12.5, C.glacierD },
}
local PEAKS =
	{ -- вершина |x|, полуширины к центру и наружу, низ, высота, перед, зад
		{ 13.5, 3, 4.5, 18.3, 10, 38.0, 46.4 },
		{ 24.5, 6, 2.5, 21.3, 13, 38.6, 46.8 },
		{ 29.5, 2.2, 6.3, 17.3, 7, 39.4, 46.2 },
		{ 42.5, 6.3, 3.3, 12.3, 8, 40.6, 46.6 },
		-- второй ряд — ниже и светлее, за первым (ледник не «замок с башнями»: вершины смещены, ряды разной высоты)
		{ 17.4, 1.4, 2.8, 18.25, 6, 43.6, 46.95 },
		{ 21, 2.4, 3.5, 21.25, 8.5, 43.9, 46.9 },
		{ 34, 3, 2, 17.25, 5, 44.1, 46.85 },
	}
local GATE_Z0, GATE_Z1 = 37.8, 46.8 -- глубина моста над воротами (перед — вне круга боя r 41)

local function glacier(out: { Brick })
	for _, s in { -1, 1 } do
		local function X(a: number, b: number): (number, number)
			return math.min(s * a, s * b), math.max(s * a, s * b)
		end
		for i, seg in MASSIF do
			local x0, x1 = X(seg[1], seg[2])
			local front, top = seg[3], seg[4]
			table.insert(out, Box(x0, x1, 0, top, front, 47, seg[5], SOFT))
			-- снежный карниз-козырёк (низ глыбы закрыт скатом)
			table.insert(
				out,
				Box(x0 - 0.1, x1 + 0.1, top - 0.4, top + 0.55, front - 0.3, front + 3.2 + i * 0.1, C.snow)
			)
			for k, u in { 0.28, 0.7 } do
				local x = s * (seg[1] + (seg[2] - seg[1]) * u)
				local h = 1.4 + ((i + k) % 3) * 0.6
				table.insert(
					out,
					Box(x - 0.45, x + 0.45, top - 0.4 - h, top - 0.3, front - 0.25, front + 0.55, C.glacierE, DECOR)
				)
				table.insert(
					out,
					Box(x - 0.2, x + 0.2, top - 1.4 - h, top - 0.5 - h, front - 0.15, front + 0.45, C.glacierE, DECOR)
				)
			end
		end
		for i, p in PEAKS do
			local apex = s * p[1]
			local towardC, out_ = p[2], p[3]
			local left, right = if s > 0 then towardC else out_, if s > 0 then out_ else towardC
			snowPeak(
				out,
				"x",
				apex,
				left,
				right,
				(p[6] + p[7]) / 2,
				p[7] - p[6],
				p[4],
				p[5],
				if i == 2 then C.glacierD else C.glacier,
				true
			)
		end
		-- уступ перед массивом (ступень 1.2) с двумя витринами
		local x0, x1 = X(12, 44)
		table.insert(out, Box(x0, x1, 0, 1.2, 31.0, 37.4, C.glacierE, SOFT))
		-- ледяные скаты перед глыбами (низ — на уступе, вне круга боя): ледник «стекает» на уступ
		for i, seg in MASSIF do
			local h = seg[4] * 0.5
			local w = seg[2] - seg[1] - 0.9 -- уже глыбы: боковины не совпадают
			table.insert(
				out,
				B(
					V(w, h, 2.6),
					CFrame.new(s * (seg[1] + seg[2]) / 2, 1.15 + h / 2, seg[3] - 1.25),
					if i % 2 == 0 then C.ice else C.glacierE,
					{ shape = "Wedge", variant = "LegoSquaresSoft" }
				)
			)
		end
		for j, v in { { "trophy", 31.5 }, { "clock", 40.5 } } do
			local kind = if s > 0 then v[1] else (if j == 1 then "gem" else "crown")
			vitrine(out, kind, s * v[2], 33.1, 1.1, 2.7, 4, 7.4, 1)
			if kind == "gem" then
				out[#out].light = { range = 12, brightness = 0.9, color = C.neonGem }
			end
		end
	end
	-- ворота: мост между массивами над проходом (низ GlacierHall.Gate[2]), золотая рама, снежинка-герб, сосульки
	local hw, gh = GlacierHall.Gate[1], GlacierHall.Gate[2]
	table.insert(out, Box(-10.6, 10.6, gh, 20.0, GATE_Z0, GATE_Z1, C.glacierM, SOFT))
	table.insert(out, Box(-10.8, 10.8, 19.9, 20.8, GATE_Z0 - 0.3, GATE_Z1 + 0.1, C.snow))
	-- рама: стойки по краям проёма и перекладина (выступают из массивов на 0.4, грани не совпадают)
	for _, s in { -1, 1 } do -- стойки заходят в массив на 0.2
		local a, b = s * hw, s * (hw + 1.5)
		table.insert(out, Box(math.min(a, b), math.max(a, b), 0, gh + 0.2, 37.7, 39.2, C.gold))
		a, b = s * (hw - 0.3), s * (hw + 1.2)
		table.insert(out, Box(math.min(a, b), math.max(a, b), 0, 1.0, 37.55, 39.4, C.goldD))
	end
	table.insert(out, Box(-hw - 1.6, hw + 1.6, gh - 0.3, gh + 1.1, 37.6, 39.1, C.gold))
	-- снежинка-герб на мосту: круг, шесть лучей, самоцвет со светом
	local ec = Vector3.new(0, 16.6, 37.8)
	table.insert(out, Round(5.6, 0.5, CFrame.new(ec), C.glacierDeep))
	table.insert(out, Round(6.2, 0.4, CFrame.new(ec + Vector3.new(0, 0, 0.2)), C.gold))
	for i, deg in { 0, 60, 120 } do
		local front = ec.Z - 0.35 - i * 0.06
		table.insert(
			out,
			B(V(0.55, 4.8, 0.3), CFrame.new(ec.X, ec.Y, front) * CFrame.Angles(0, 0, math.rad(deg)), C.neonIce, NEON)
		)
	end
	table.insert(
		out,
		FleaKit.Neon(V(1.1, 1.1, 1.1), CFrame.new(ec.X, ec.Y, ec.Z - 0.7) * FleaKit.DIAMOND, C.neonIce, 18)
	)
	-- сосульки под мостом (выше головы: низ ≥ 9.6)
	for i = 0, 6 do
		local x = -6.6 + i * 2.2
		local h = 1.4 + (i % 3) * 0.7
		table.insert(out, Box(x - 0.4, x + 0.4, gh - h, gh + 0.05, 38.3, 39.0, C.glacierE, DECOR))
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
	-- светящееся ледяное кольцо по краю площадки (низкое, по нему пробегают): 24 отрезка, через один светятся
	for k = 0, 23 do
		local deg = k * 15
		local x, z = polar(deg + 7.5, 33.7)
		local at = CFrame.new(x, 0.2, z) * CFrame.Angles(0, math.rad(deg + 7.5 + 90), 0)
		table.insert(
			out,
			B(V(8.6, 0.34, 0.9), at, if k % 2 == 0 then C.neonIce else C.glacierE, if k % 2 == 0 then NEON else DECOR)
		)
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

	-- указатели к следующему уровню: у боковых полос и на мосту ворот
	for _, s in { -1, 1 } do
		local x, z = s * 45.5, 33
		table.insert(out, Box(x - 0.2, x + 0.2, 0, 3.7, z - 0.2, z + 0.2, C.trunk))
		table.insert(
			out,
			FleaKit.Board(V(4.6, 1.3, 0.3), V(x, 3.3, z - 0.35), C.platEdge, FleaKit.Label("В ДЖУНГЛИ"))
		)
	end
	table.insert(
		out,
		FleaKit.Board(
			V(7, 1.1, 0.3),
			V(0, GlacierHall.Gate[2] + 0.4, 37.58),
			C.platEdge,
			FleaKit.Label("В ДЖУНГЛИ")
		)
	)
	return out, FleaKit.Signs()
end

return GlacierHall

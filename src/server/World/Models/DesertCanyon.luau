-- Ландшафт зоны 4 «Храм спящего Сфинкса» (D60, полировка 2026-11-14): песчаные скалы и барханы вдоль стен обрыва
-- вместо голых стен-коробок, спокойный песок и оазис. Стены коридора (WorldBuilder.buildCliffs) не меняются — их
-- закрывают уступы скал: нижний ярус твёрдый и не выше 21 (с пола и с клина-склона на него не запрыгнуть: прыжок
-- ≈ 6.4, ступень ≥ 8; с любой твёрдой площадки до верха обрыва 32.7 — больше прыжка, за карту не выйти), верхние
-- ярусы и шпили — без столкновений: ломают прямую линию стены и выходят над её кромкой. К уступам ведут песчаные
-- склоны-клинья (плавный переход песок → скала). Песок зоны — сплошной слой мягкого варианта пупырышков
-- (LegoSquaresSoft: без шахматки основного LegoSquares, решение владельца «песок спокойнее»), скалы — основной
-- LegoSquares тёплого песчаника (крупная LegoSquaresDeep стены рядом с ней сливалась). Оазис — два бассейна с
-- каменной кромкой и ступенями, водопад из расщелины скал, пальмы, цветы, камыш и кувшинки. Координаты — зоны
-- (как у World/Models/DesertOasis): x поперёк (стены обрыва на ±92), z вдоль (вход −47.5, выход +47.5), y = 0 —
-- пол; s — сторона (−1 / +1), u = |x|.
-- Зависит от World/Models/FleaKit, World/Models/DesertTemple.

local ServerScriptService = game:GetService("ServerScriptService")

local World = ServerScriptService.Server.World
local FleaKit = require(World.Models.FleaKit)
local DesertTemple = require(World.Models.DesertTemple)

type Brick = FleaKit.Brick

local B, V = FleaKit.B, FleaKit.V
local Box, Disc = FleaKit.Box, FleaKit.Disc

local C = DesertTemple.C
local function hex(code: string): Color3
	return Color3.fromHex(code)
end

-- Песок: основной слой и оттенки склонов и барханов (средняя светлота — без пересвета).
local SAND = {
	base = hex("D8AE66"),
	light = hex("E2BC78"),
	mid = hex("D1A45C"),
	deep = hex("C6984F"),
}
-- Скалы: тёплый оранжевый песчаник снизу вверх — отличается от бежевой земли стены (Palette.CliffDirt D4B07E) и
-- цветом, и мелкой фактурой основного LegoSquares (у стены — крупная LegoSquaresDeep).
local ROCK = { hex("BF7A43"), hex("CE8C50"), hex("DB9F60"), hex("E6B676") }

local SOFT = { variant = "LegoSquaresSoft", shadow = false }
local AIR = { collide = false } -- верхние ярусы: видны, но на них не встать
local DECOR = FleaKit.DECOR
local SOLID = { collide = true }
local WATER = { material = Enum.Material.Glass, transparency = 0.3, collide = false, shadow = false }
local FOAM = { material = Enum.Material.Glass, transparency = 0.1, collide = false, shadow = false }

local DesertCanyon = {}

-- Наибольший верх твёрдого уступа у стен (проверяет scripts/lune/check_world.luau).
DesertCanyon.SolidTop = 21

local function X(s: number, a: number, b: number): (number, number)
	return math.min(s * a, s * b), math.max(s * a, s * b)
end

-- Клин-склон вдоль стены стороны s: z0..z1, по u от u0 (низ) до u1 (верх h) — высокая сторона клина к стене.
local function ramp(out: { Brick }, s: number, z0: number, z1: number, u0: number, u1: number, h: number, color: Color3)
	local at = CFrame.new(s * (u0 + u1) / 2, h / 2, (z0 + z1) / 2) * CFrame.Angles(0, math.rad(s * 90), 0)
	table.insert(out, B(V(z1 - z0, h, u1 - u0), at, color, { shape = "Wedge", variant = "LegoSquaresSoft" }))
end

-- Сплошной слой спокойного песка на весь пол зоны (на 0.04 выше пола; мощение, площадка и дорожки — выше).
function DesertCanyon.Sand(out: { Brick })
	table.insert(out, Box(-91.95, 91.95, -0.06, 0.04, -47.45, 47.45, SAND.base, SOFT))
end

-- Бархан посреди песка: гребень из двух клиньев (длина len вдоль yaw, высота h, ширина склонов w).
function DesertCanyon.Dune(out: { Brick }, x: number, z: number, len: number, h: number, w: number, yaw: number)
	local at = CFrame.new(x, h / 2, z) * CFrame.Angles(0, math.rad(yaw), 0)
	local opts = { shape = "Wedge", variant = "LegoSquaresSoft" }
	table.insert(out, B(V(len, h, w), at * CFrame.new(0, 0, -w / 2), SAND.light, opts))
	table.insert(
		out,
		B(V(len, h, w * 0.8), at * CFrame.new(0, 0, w * 0.4) * CFrame.Angles(0, math.pi, 0), SAND.mid, opts)
	)
end

export type Cliff = {
	z0: number,
	z1: number,
	base: { number }, -- { u, h } — твёрдый нижний ярус
	mid: { number }, -- { u, h } — средний (без столкновений)
	top: { number }, -- { u, h } — верхний (без столкновений)
	yaw: number?, -- поворот верхних ярусов, градусы
	spire: { number }?, -- { z, h } — шпиль над кромкой обрыва
	shade: number?, -- 0/1 — какой оттенок склона
}

-- Скальный уступ у стены стороны s: склон, твёрдый нижний ярус из двух уступов с валунами, два верхних яруса без
-- столкновений и шпиль.
function DesertCanyon.Cliff(out: { Brick }, s: number, c: Cliff)
	local z0, z1 = c.z0, c.z1
	local zc, len = (z0 + z1) / 2, z1 - z0
	local bu, bh = c.base[1], c.base[2]
	assert(bh <= DesertCanyon.SolidTop, "DesertCanyon: твёрдый уступ выше SolidTop")
	-- склон к уступу (верх 2: с него на уступ не запрыгнуть)
	ramp(out, s, z0, z1, bu - 5.5, bu, 2, if c.shade == 1 then SAND.mid else SAND.light)
	-- нижний ярус: два уступа разной высоты и глубины (не ровная стена)
	local split = z0 + len * 0.55
	local x0, x1 = X(s, bu, 92)
	table.insert(out, Box(x0, x1, 0, bh, z0, split, ROCK[1]))
	x0, x1 = X(s, bu + 1.6, 91.9) -- задняя грань — не в одной плоскости с соседним уступом
	table.insert(out, Box(x0, x1, 0, bh - 2.5, split, z1, ROCK[2]))
	-- светлая полоса по фасаду первого уступа: слоистый песчаник
	x0, x1 = X(s, bu - 0.15, bu + 0.5)
	table.insert(out, Box(x0, x1, bh * 0.45, bh * 0.62, z0 + 0.3, split - 0.3, ROCK[3], AIR))
	-- валун у подножия (низкий: не ступенька) и валун на кромке уступа
	table.insert(
		out,
		B(
			V(2.6, 1.8, 2.2),
			CFrame.new(s * (bu - 1.6), 0.8, z0 + len * 0.3) * CFrame.Angles(0.05, math.rad(25 + zc), 0.04),
			ROCK[2]
		)
	)
	table.insert(
		out,
		B(
			V(3, 1.6, 2.6),
			CFrame.new(s * (bu + 1.4), bh + 0.6, z0 + len * 0.25) * CFrame.Angles(0.04, math.rad(30 + zc), 0.03),
			ROCK[4],
			AIR
		)
	)
	-- средний ярус стоит на нижнем уступе второго (низ на bh − 2.5), верхний — на среднем
	local yaw = math.rad(c.yaw or 0)
	local mu, mh = c.mid[1], c.mid[2]
	local depth = 92 - mu + 0.6
	table.insert(
		out,
		B(
			V(depth, mh - bh + 2.5, len * 0.94),
			CFrame.new(s * (mu + depth / 2 - 0.3), (bh - 2.5 + mh) / 2, zc) * CFrame.Angles(0, yaw, 0),
			ROCK[3],
			AIR
		)
	)
	local tu, th = c.top[1], c.top[2]
	depth = 92 - tu + 0.6
	table.insert(
		out,
		B(
			V(depth, th - mh, len * 0.78),
			CFrame.new(s * (tu + depth / 2 - 0.3), (mh + th) / 2, zc + len * 0.06) * CFrame.Angles(0, -yaw * 1.5, 0),
			ROCK[4],
			AIR
		)
	)
	if c.spire then
		local sz, sh = c.spire[1], c.spire[2]
		table.insert(
			out,
			B(
				V(3.6, sh - th + 1, 3.4),
				CFrame.new(s * 89.6, (th + sh - 1) / 2, sz) * CFrame.Angles(0, math.rad(20), math.rad(s * 3)),
				ROCK[3],
				AIR
			)
		)
		table.insert(
			out,
			B(V(2.4, 1.6, 2.2), CFrame.new(s * 89.5, sh + 0.6, sz) * CFrame.Angles(0, math.rad(50), 0), ROCK[4], AIR)
		)
	end
end

-- Шов между соседними скалами a и b (b.z0 = a.z1): тёмная утопленная скала у стены, чтобы в щели между верхними
-- ярусами (они короче нижнего и повёрнуты) не была видна ровная стена. Без столкновений, повёрнут — без общих граней.
function DesertCanyon.Seam(out: { Brick }, s: number, a: Cliff, b: Cliff)
	local y0 = math.min(a.base[2], b.base[2]) - 2.5
	local y1 = math.min(a.top[2], b.top[2]) - 1.2
	table.insert(
		out,
		B(
			V(1.8, y1 - y0, 7.4),
			CFrame.new(s * 91.1, (y0 + y1) / 2, a.z1) * CFrame.Angles(0, math.rad(s * 4), 0),
			ROCK[1],
			AIR
		)
	)
end

-- Цветущий куст: куст и два цветка цветов a и b.
function DesertCanyon.Flowers(out: { Brick }, x: number, z: number, a: Color3, b: Color3)
	DesertTemple.Bush(out, x, 0, z, 0.55)
	table.insert(out, B(V(0.5, 0.5, 0.5), CFrame.new(x + 0.4, 1.35, z - 0.3) * CFrame.Angles(0, 0.7, 0), a, DECOR))
	table.insert(out, B(V(0.45, 0.45, 0.45), CFrame.new(x - 0.5, 1.05, z + 0.4) * CFrame.Angles(0, 0.3, 0), b, DECOR))
end

-- Оазис у стены стороны s: большой бассейн (центр u, z, диаметр d) и малый (центр u2, z2, диаметр d2) — каменные
-- ступени вокруг, кромка из камней, вода; водопад из расщелины между двумя скалами на стене (z от wz0 до wz1).
export type Oasis = {
	main: { number }, -- { u, z, d }
	lobe: { number }, -- { u, z, d }
	falls: { number }, -- { z0, z1 } — расщелина водопада
	towers: { { number } }, -- { z0, z1, u, h } — скалы по сторонам водопада (твёрдые, h ≤ SolidTop)
}

function DesertCanyon.Oasis(out: { Brick }, s: number, o: Oasis)
	local pools = { o.main, o.lobe }
	local inside = function(px: number, pz: number, pool: { number }, extra: number): boolean
		return math.sqrt((px - pool[1]) ^ 2 + (pz - pool[2]) ^ 2) < pool[3] / 2 + extra
	end
	-- бассейны заходят друг в друга: у малого все слои выше на 0.05 — торцы дисков не в одной плоскости (D36)
	for i, p in pools do
		local px, pz, d = s * p[1], p[2], p[3]
		local lift = (i - 1) * 0.05
		table.insert(out, Disc(d + 2.4, -0.05, 0.35 + lift, px, pz, C.stoneD, SOLID)) -- нижняя ступень вокруг
		table.insert(out, Disc(d + 1.6, -0.045, 0.7 + lift, px, pz, C.stoneL, SOLID)) -- кромка
		table.insert(out, Disc(d, -0.04, 0.78 + lift, px, pz, C.waterD))
		table.insert(out, Disc(d + 0.2, 0.8 + lift, 0.95 + lift, px, pz, C.water, WATER))
	end
	-- камни по кромке: на стыке бассейнов (внутри другого бассейна) камней нет, у прохода к пути — ступени
	for i, p in pools do
		local other = pools[3 - i]
		local r = p[3] / 2 + 0.55
		local n = if i == 1 then 16 else 9
		for k = 0, n - 1 do
			local a = math.rad(k * 360 / n + 8)
			local u, z = p[1] + math.sin(a) * r, p[2] + math.cos(a) * r
			local towardPath = i == 1 and math.abs(z - p[2]) < 3.5 and u < p[1]
			if not inside(u, z, other, 0.2) and not towardPath then
				local frame = CFrame.new(s * u, 0.95 + (i - 1) * 0.05, z)
					* CFrame.Angles(0, math.atan2(s * math.sin(a), math.cos(a)), 0)
				table.insert(out, B(V(2.3, 0.5, 1.25), frame, if k % 2 == 0 then C.stoneL else ROCK[3]))
			end
		end
	end
	-- ступени к воде со стороны пути
	local m = o.main
	local x0, x1 = X(s, m[1] - m[3] / 2 - 1.5, m[1] - m[3] / 2 - 0.2)
	table.insert(out, Box(x0, x1, 0, 0.55, m[2] - 2.6, m[2] + 2.6, C.stoneL))
	-- скалы по сторонам водопада и камень за струёй
	for _, t in o.towers do
		local tz0, tz1, tu, th = t[1], t[2], t[3], t[4]
		assert(th <= DesertCanyon.SolidTop, "DesertCanyon: скала оазиса выше SolidTop")
		x0, x1 = X(s, tu, 92)
		table.insert(out, Box(x0, x1, 0, th, tz0, tz1, ROCK[2]))
		local tc = (tz0 + tz1) / 2
		table.insert(
			out,
			B(
				V(92 - tu - 0.8, 7, (tz1 - tz0) * 0.8),
				CFrame.new(s * (tu + (92 - tu) / 2 + 0.4), th + 3.5, tc) * CFrame.Angles(0, math.rad(4), 0),
				ROCK[4],
				AIR
			)
		)
		DesertTemple.Bush(out, s * (tu + 1.6), th, tc - 1.5, 1)
	end
	local fz0, fz1 = o.falls[1], o.falls[2]
	local fh = 16.5
	x0, x1 = X(s, 89, 92)
	table.insert(out, Box(x0, x1, 0, fh, fz0, fz1, ROCK[1]))
	-- водопад: струя, светлые потоки, пена на уступе и у воды
	x0, x1 = X(s, 88.5, 88.9)
	table.insert(out, Box(x0, x1, 1.05, fh - 0.2, fz0 + 1, fz1 - 1, C.water, WATER))
	for _, f in { 0.32, 0.68 } do
		local z = fz0 + (fz1 - fz0) * f
		x0, x1 = X(s, 88.3, 88.5)
		table.insert(out, Box(x0, x1, 1.2, fh - 0.5, z - 0.3, z + 0.3, C.waterL, FOAM))
	end
	x0, x1 = X(s, 88.2, 89.4)
	table.insert(out, Box(x0, x1, fh - 0.5, fh + 0.3, fz0 + 0.7, fz1 - 0.7, C.foam, FOAM))
	x0, x1 = X(s, 86.4, 88.8)
	table.insert(out, Box(x0, x1, 0.97, 1.6, fz0 + 0.6, fz1 - 0.6, C.foam, FOAM))
	-- лианы по скалам у водопада и папоротники у его подножия
	for _, v in
		{
			{ o.towers[1][2] - 1.2, 9 },
			{ o.towers[1][2] - 3.5, 5.5 },
			{ o.towers[2][1] + 1.4, 8 },
			{ o.towers[2][1] + 4, 6 },
		}
	do
		local tower = if v[1] < fz0 then o.towers[1] else o.towers[2]
		local vu = tower[3] - 0.2
		x0, x1 = X(s, vu, vu + 0.3)
		table.insert(out, Box(x0, x1, tower[4] - v[2], tower[4] - 0.2, v[1] - 0.4, v[1] + 0.4, C.leafD, DECOR))
	end
	DesertTemple.Bush(out, s * 87.2, 0.95, fz0 - 0.8, 0.7)
	DesertTemple.Bush(out, s * 87.4, 0.95, fz1 + 0.9, 0.6)
	-- кувшинки, цветок на кувшинке, камыш
	for _, p in { { 2.5, -3 }, { -3.5, 2 }, { 1, 4.5 } } do
		table.insert(out, Disc(1.5, 0.95, 1.03, s * (m[1] + p[1]), m[2] + p[2], C.leaf))
	end
	table.insert(out, B(V(0.45, 0.4, 0.45), CFrame.new(s * (m[1] + 2.5), 1.2, m[2] - 3), C.pink, DECOR))
	for i, r in { { 4, 9.6 }, { -6, 8.6 }, { -1.5, -10.4 } } do
		local rx, rz = s * (m[1] + r[1]), m[2] + r[2]
		table.insert(out, B(V(0.35, 1.8 + 0.3 * i, 0.35), V(rx, 0.9 + 0.15 * i, rz), C.leafD, DECOR))
		table.insert(out, B(V(0.3, 1.3, 0.3), V(rx + 0.45, 0.65, rz + 0.3), C.leaf, DECOR))
	end
end

return DesertCanyon

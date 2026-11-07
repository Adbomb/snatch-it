-- Большие части «Подземки» (D54): вагоны, тронный вагон короля, дрезина, вагонетки, упоры и светофоры путей,
-- колонны с лампами и рёбра свода, эскалатор, касса, турникеты, вывески и прожекторы на босса. Каждая — функция
-- кирпичей в своих координатах: начало — центр низа, лицо — сторона −Z (у вагонов и дрезины длина вдоль X; у
-- дрезины и вагонеток — вдоль Z, колёса на рельсах x = ±GAUGE/2). Рельсы — верх на RAIL_TOP над полом.
-- Совпадающих граней нет (D36): накладки выступают за грань, торцы встык, у соседних сегментов — разная толщина.
-- Зависит от World/Models/SubwayKit.

local ServerScriptService = game:GetService("ServerScriptService")

local World = ServerScriptService.Server.World
local SubwayKit = require(World.Models.SubwayKit)

type Brick = SubwayKit.Brick

local B, V, C = SubwayKit.B, SubwayKit.V, SubwayKit.C
local Box, Disc, Neon, Board, Label, Put, Gem =
	SubwayKit.Box, SubwayKit.Disc, SubwayKit.Neon, SubwayKit.Board, SubwayKit.Label, SubwayKit.Put, SubwayKit.Gem
local DECOR, ROUND = SubwayKit.DECOR, SubwayKit.ROUND
local Wheel = SubwayKit.Wheel

local SubwayParts = {}

SubwayParts.RAIL_TOP = 0.62 -- верх рельса над полом
SubwayParts.GAUGE = 5 -- между рельсами
local RAIL_TOP, GAUGE = SubwayParts.RAIL_TOP, SubwayParts.GAUGE

local W = 8.4 -- ширина вагона
local BODY = { y0 = 2.1, y1 = 10.1 } -- кузов вагона над полом

-- Колёсные тележки вагона длины len: по две оси на тележку, колёса на рельсах z = ±GAUGE/2.
local function bogies(out: { Brick }, len: number)
	local d = 1.6
	for _, bx in { -len / 2 + 4, len / 2 - 4 } do
		table.insert(out, Box(bx - 2.2, bx + 2.2, 1.0, BODY.y0, -2.2, 2.2, C.graphite))
		for _, ax in { -1.2, 1.2 } do
			for _, z in { -GAUGE / 2, GAUGE / 2 } do
				table.insert(out, Wheel(V(bx + ax, RAIL_TOP + d / 2, z), d, 0.5))
			end
		end
	end
	table.insert(
		out,
		Box(-len / 2 + 6.5, len / 2 - 6.5, 1.75, BODY.y0 + 0.05, -W / 2 + 0.5, W / 2 - 0.5, C.ironDark, DECOR)
	)
end

-- Окна вдоль борта side (−1 — лицо −Z, 1 — +Z) на отрезках между дверями; ширина окна 2.6, просвет 0.8.
local function windows(out: { Brick }, len: number, side: number, doors: { number })
	local edges = { -len / 2 + 1.2 }
	for _, x in doors do
		table.insert(edges, x - 1.6)
		table.insert(edges, x + 1.6)
	end
	table.insert(edges, len / 2 - 1.2)
	local z0, z1 =
		math.min(side * (W / 2 - 0.02), side * (W / 2 + 0.08)), math.max(side * (W / 2 - 0.02), side * (W / 2 + 0.08))
	for i = 1, #edges - 1, 2 do
		local a, b = edges[i], edges[i + 1]
		local n = math.floor((b - a + 0.8) / 3.4)
		if n > 0 then
			local span = n * 2.6 + (n - 1) * 0.8
			for k = 0, n - 1 do
				local x = (a + b) / 2 - span / 2 + k * 3.4
				table.insert(out, Box(x, x + 2.6, 5.2, 8.0, z0, z1, C.window, DECOR))
			end
		end
	end
end

-- Фары и задние огни на торцах, торцевые окна и сцепки.
local function ends(out: { Brick }, len: number)
	for _, s in { -1, 1 } do
		local x0, x1 = math.min(s * len / 2, s * (len / 2 + 0.08)), math.max(s * len / 2, s * (len / 2 + 0.08))
		local light = if s < 0 then C.lampLight else C.signal
		for _, z in { -2.6, 2.6 } do
			table.insert(out, Neon(V(x1 - x0, 0.7, 1.1), V((x0 + x1) / 2, 3.0, z), light))
		end
		table.insert(out, Box(x0, x1, 5.2, 8.0, -1.4, 1.4, C.window, DECOR))
		local c0, c1 = math.min(s * len / 2, s * (len / 2 + 0.7)), math.max(s * len / 2, s * (len / 2 + 0.7))
		table.insert(out, Box(c0, c1, 2.3, 2.9, -0.45, 0.45, C.graphite, DECOR))
	end
end

-- Крыша с коньком и двумя вентиляторами.
local function roof(out: { Brick }, len: number)
	table.insert(out, Box(-len / 2 - 0.1, len / 2 + 0.1, BODY.y1, BODY.y1 + 0.5, -W / 2 - 0.1, W / 2 + 0.1, C.roof))
	table.insert(
		out,
		Box(-len / 2 + 0.6, len / 2 - 0.6, BODY.y1 + 0.5, BODY.y1 + 1.1, -W / 2 + 0.9, W / 2 - 0.9, C.metal)
	)
	for _, x in { -len / 4, len / 4 } do
		table.insert(out, Box(x - 1, x + 1, BODY.y1 + 1.1, BODY.y1 + 1.6, -0.8, 0.8, C.railDark, DECOR))
	end
end

-- Вагон метро длины len вдоль X, лицо −Z: красный кузов, кремовая полоса, светящиеся окна, двери (у open —
-- открыта передняя дверь, внутри блестит золото), крыша, тележки на рельсах.
function SubwayParts.Wagon(len: number, open: boolean?): { Brick }
	local out = {}
	bogies(out, len)
	table.insert(out, Box(-len / 2, len / 2, BODY.y0, BODY.y1, -W / 2, W / 2, C.red))
	table.insert(out, Box(-len / 2 - 0.06, len / 2 + 0.06, 3.6, 4.3, -W / 2 - 0.06, W / 2 + 0.06, C.wagonCream, DECOR))
	local doors = { -len / 4, len / 4 }
	for _, side in { -1, 1 } do
		windows(out, len, side, doors)
		for i, x in doors do
			local z0, z1 = math.min(side * W / 2, side * (W / 2 + 0.1)), math.max(side * W / 2, side * (W / 2 + 0.1))
			if open and side < 0 and i == 1 then
				-- Открытая дверь: тёмный проём, в нём золото; створка отъехала вбок.
				table.insert(out, Box(x - 1.2, x + 1.2, 2.4, 9.0, -W / 2 - 0.09, -W / 2 + 0.02, C.interior, DECOR))
				table.insert(out, Box(x - 1.0, x + 1.0, 2.45, 3.6, -W / 2 - 0.13, -W / 2 + 0.02, C.gold, DECOR))
				table.insert(out, Gem(0.6, V(x - 0.3, 3.9, -W / 2 - 0.35), C.purpleLight))
				table.insert(out, Box(x + 1.25, x + 3.65, 2.4, 9.0, -W / 2 - 0.25, -W / 2 - 0.14, C.roof, DECOR))
			else
				table.insert(out, Box(x - 1.2, x + 1.2, 2.4, 9.0, z0, z1, C.roof, DECOR))
				local w0, w1 =
					math.min(side * W / 2, side * (W / 2 + 0.16)), math.max(side * W / 2, side * (W / 2 + 0.16))
				table.insert(out, Box(x - 0.7, x + 0.7, 5.4, 7.8, w0, w1, C.window, DECOR))
			end
		end
	end
	ends(out, len)
	roof(out, len)
	return out
end

-- Тронный вагон короля (длина 28 вдоль X, лицо −Z — к боссу): широкие двери посередине открыты, внутри фиолетовый
-- бархат, тёплый свет и гора золота, монеты высыпаются на пол; на крыше огромная жестяная корона и вывеска
-- «КОРОЛЬ ПОДЗЕМКИ». Сам вагон — фон для босса, на его площадку он не заходит.
function SubwayParts.ThroneWagon(): { Brick }
	local len, gap = 28, 3.2
	local out = {}
	bogies(out, len)
	local y0, y1 = BODY.y0, BODY.y1
	table.insert(out, Box(-len / 2, len / 2, y0, y1, 0, W / 2, C.red)) -- задняя половина кузова
	for _, s in { -1, 1 } do
		local x0, x1 = math.min(s * gap, s * len / 2), math.max(s * gap, s * len / 2)
		table.insert(out, Box(x0, x1, y0, y1, -W / 2, 0.02, C.red))
		local a0, a1 = math.min(s * (gap + 0.1), s * (len / 2 + 0.08)), math.max(s * (gap + 0.1), s * (len / 2 + 0.08))
		table.insert(out, Box(a0, a1, 3.6, 4.3, -W / 2 - 0.06, 0.1, C.wagonCream, DECOR)) -- полоса спереди
		-- Створки дверей отъехали в стороны.
		local d0, d1 = math.min(s * (gap - 0.06), s * (gap + 2.6)), math.max(s * (gap - 0.06), s * (gap + 2.6))
		table.insert(out, Box(d0, d1, 2.4, 9.2, -W / 2 - 0.2, -W / 2 - 0.05, C.roof, DECOR))
		local e0, e1 = math.min(s * (gap + 0.6), s * (gap + 2.0)), math.max(s * (gap + 0.6), s * (gap + 2.0))
		table.insert(out, Box(e0, e1, 5.4, 7.8, -W / 2 - 0.26, -W / 2 - 0.1, C.window, DECOR))
		for _, x in { 8, 11.6 } do -- окна на передней стене
			local w0, w1 = math.min(s * (x - 1.3), s * (x + 1.3)), math.max(s * (x - 1.3), s * (x + 1.3))
			table.insert(out, Box(w0, w1, 5.2, 8.0, -W / 2 - 0.08, -W / 2 + 0.02, C.window, DECOR))
		end
	end
	table.insert(out, Box(-len / 2 - 0.06, len / 2 + 0.06, 3.6, 4.3, 0.04, W / 2 + 0.06, C.wagonCream, DECOR))
	windows(out, len, 1, { -len / 4, len / 4 })
	table.insert(out, Box(-gap, gap, 9.2, y1, -W / 2, 0.02, C.red)) -- над проёмом
	-- Внутри: бархатная стена, пол, гора золота, самоцветы, тёплая лампа.
	table.insert(out, Box(-gap, gap, y0, 9.2, -0.05, 0.02, C.purple, DECOR))
	table.insert(out, Box(-gap, gap, y0, y0 + 0.3, -W / 2 + 0.05, 0, C.interior, DECOR))
	table.insert(out, Box(-3.0, 3.0, y0 + 0.3, 3.6, -3.8, -0.1, C.gold, DECOR))
	table.insert(out, Box(-2.2, 2.2, 3.6, 4.6, -3.1, -0.1, C.goldLight, DECOR))
	table.insert(out, Box(-1.2, 1.2, 4.6, 5.4, -2.4, -0.1, C.gold, DECOR))
	table.insert(out, Gem(0.9, V(-1.6, 4.0, -3.0), C.purpleLight))
	table.insert(out, Gem(0.8, V(1.8, 4.0, -2.8), C.signal))
	table.insert(out, Gem(0.7, V(0.3, 5.7, -1.9), C.green))
	table.insert(out, Neon(V(1.2, 0.6, 1.2), V(0, 8.7, -1.8), C.lampLight, 18))
	-- Монеты высыпаются на пол перед дверями.
	table.insert(out, Box(-2.8, 2.8, 0, 1.0, -W / 2 - 2.4, -W / 2 + 0.1, C.gold, DECOR))
	table.insert(out, Box(-2.2, 2.2, 1.0, 2.0, -W / 2 - 1.2, -W / 2 + 0.1, C.goldLight, DECOR))
	for i, p in { V(-1.8, 0, -W / 2 - 3.2), V(1.6, 0, -W / 2 - 3.0), V(0.2, 0, -W / 2 - 3.9), V(2.9, 0, -W / 2 - 1.4) } do
		table.insert(out, SubwayKit.Coin(p.X, p.Z, 0.2 + i * 0.05))
	end
	ends(out, len)
	roof(out, len)
	-- Жестяная корона на крыше: обруч, бархатная шапка, зубцы с самоцветами.
	local base = BODY.y1 + 1.1
	table.insert(out, Box(-2.9, 2.9, base + 0.05, base + 1.8, -2.9, 2.9, C.purple, DECOR))
	for _, s in { -1, 1 } do
		table.insert(out, Box(-3.6, 3.6, base, base + 2.2, s * 3.1 - 0.5, s * 3.1 + 0.5, C.gold, DECOR))
		table.insert(out, Box(s * 3.1 - 0.5, s * 3.1 + 0.5, base, base + 2.2, -2.6, 2.6, C.gold, DECOR))
	end
	local tips = { C.signal, C.purpleLight, C.green, C.lampLight }
	for i, p in
		{
			V(-3.1, 0, -3.1),
			V(0, 0, -3.1),
			V(3.1, 0, -3.1),
			V(3.1, 0, 0),
			V(3.1, 0, 3.1),
			V(0, 0, 3.1),
			V(-3.1, 0, 3.1),
			V(-3.1, 0, 0),
		}
	do
		local h = if p.X == 0 or p.Z == 0 then 2.4 else 1.5
		table.insert(
			out,
			Box(p.X - 0.45, p.X + 0.45, base + 2.2, base + 2.2 + h, p.Z - 0.45, p.Z + 0.45, C.goldLight, DECOR)
		)
		table.insert(out, Gem(1.0, V(p.X, base + 2.2 + h + 0.55, p.Z), tips[(i - 1) % #tips + 1]))
	end
	-- Вывеска на краю крыши перед короной.
	table.insert(out, Box(-9.4, 9.4, BODY.y1 + 0.5, BODY.y1 + 3.3, -W / 2 + 0.05, -W / 2 + 0.55, C.goldDark, DECOR))
	table.insert(
		out,
		Board(
			V(18.4, 2.4, 0.3),
			V(0, BODY.y1 + 1.9, -W / 2 - 0.05),
			C.purpleDark,
			Label("КОРОЛЬ ПОДЗЕМКИ")
		)
	)
	return out
end

-- Короткий отрезок пути вдоль X от x0 до x1: шпалы и рельсы z = ±GAUGE/2 (под тронный вагон).
function SubwayParts.TrackX(x0: number, x1: number): { Brick }
	local out = {}
	local n = math.floor((x1 - x0) / 2.6)
	for k = 0, n do
		local x = x0 + 0.6 + k * (x1 - x0 - 1.2) / n
		table.insert(out, Box(x - 0.6, x + 0.6, 0, 0.32, -4, 4, C.sleeper, DECOR))
	end
	for _, z in { -GAUGE / 2, GAUGE / 2 } do
		table.insert(out, Box(x0, x1, 0.32, RAIL_TOP, z - 0.25, z + 0.25, C.rail, DECOR))
	end
	return out
end

-- Ручная дрезина (вдоль Z): настил на четырёх колёсах, стойка и качалка-рычаг с ручками.
function SubwayParts.Handcar(): { Brick }
	local out = {
		Box(-2.9, 2.9, 1.85, 2.35, -2.2, 2.2, C.wood),
		Box(-3.0, 3.0, 1.6, 1.9, -1.9, 1.9, C.graphite, DECOR),
		Box(-0.6, 0.6, 2.35, 4.6, -0.4, 0.4, C.metal),
		Box(-0.7, 0.7, 4.6, 5.0, -0.5, 0.5, C.red, DECOR),
	}
	for _, x in { -GAUGE / 2, GAUGE / 2 } do
		for _, z in { -1.4, 1.4 } do
			table.insert(out, Wheel(V(x, RAIL_TOP + 0.6, z), 1.2, 0.4))
		end
	end
	local beam = CFrame.new(0, 5.15, 0) * CFrame.Angles(math.rad(14), 0, 0)
	table.insert(out, B(V(0.4, 0.4, 5.6), beam, C.red, DECOR))
	for _, z in { -2.8, 2.8 } do
		table.insert(out, B(V(2.6, 0.3, 0.3), beam * CFrame.new(0, 0, z), C.graphite, DECOR))
	end
	return out
end

-- Вагонетка с золотом (вдоль Z): кузов, обвязка, горка золота, самоцветы, колёса на рельсах.
function SubwayParts.MineCart(gem: Color3): { Brick }
	local out = {
		Box(-2.4, 2.4, 1.5, 3.5, -1.9, 1.9, C.iron),
		Box(-2.55, 2.55, 3.3, 3.75, -2.05, 2.05, C.ironDark, DECOR),
		Box(-2.1, 2.1, 3.75, 4.35, -1.6, 1.6, C.gold, DECOR),
		Box(-1.3, 1.3, 4.35, 4.95, -0.9, 0.9, C.goldLight, DECOR),
		Gem(0.7, V(0.9, 4.75, -0.5), gem),
		Gem(0.6, V(-0.8, 4.65, 0.6), C.green),
	}
	for _, x in { -GAUGE / 2, GAUGE / 2 } do
		for _, z in { -1.2, 1.2 } do
			table.insert(out, Wheel(V(x, RAIL_TOP + 0.55, z), 1.1, 0.4))
		end
	end
	return out
end

-- Тупиковый упор (вдоль Z, лицом к −Z): стойки, брус в красно-белую полоску, буфера, красный фонарь.
function SubwayParts.BufferStop(): { Brick }
	local out = {
		Box(-3.2, 3.2, 2.2, 3.4, -0.4, 0.4, C.red),
		Neon(V(0.9, 0.6, 0.6), V(0, 3.7, 0), C.signal),
	}
	for _, x in { -2.5, 2.5 } do
		table.insert(out, Box(x - 0.35, x + 0.35, RAIL_TOP, 3.3, -0.3, 0.3, C.graphite))
		table.insert(out, B(V(0.8, 0.8, 0.8), CFrame.new(x, 2.8, -0.85) * SubwayKit.ALONG_Z, C.ironDark, ROUND))
		table.insert(
			out,
			B(V(0.4, 0.5, 3), CFrame.new(x, 1.7, 1.2) * CFrame.Angles(math.rad(-38), 0, 0), C.graphite, DECOR)
		)
	end
	for _, x in { -3.25, 0 } do -- белые полосы; первая выступает за торец бруса
		table.insert(out, Box(x, x + 1.6, 2.15, 3.45, -0.46, -0.38, C.paper, DECOR))
	end
	return out
end

-- Путевой светофор: столб, головка с двумя огнями (верхний горит цветом lit), козырьки.
function SubwayParts.Signal(lit: Color3): { Brick }
	return {
		Box(-0.6, 0.6, 0, 0.5, -0.6, 0.6, C.graphite),
		Box(-0.25, 0.25, 0.5, 6.4, -0.25, 0.25, C.metal),
		Box(-0.7, 0.7, 5.6, 8.6, -0.45, 0.45, C.graphite),
		Neon(V(0.8, 0.8, 0.2), V(0, 7.8, -0.5), lit),
		B(V(0.8, 0.8, 0.2), V(0, 6.5, -0.5), lit:Lerp(C.graphite, 0.75), DECOR),
		Box(-0.55, 0.55, 8.2, 8.35, -0.9, -0.45, C.graphite, DECOR),
	}
end

-- Колонна станции: основание, кафельный ствол с кремовыми поясами, капитель, шар-лампа к −Z (без света).
function SubwayParts.Column(): { Brick }
	local out = {
		Box(-1.5, 1.5, 0, 1.0, -1.5, 1.5, C.tileDark),
		Box(-1.1, 1.1, 1.0, 14.2, -1.1, 1.1, C.tile),
		Box(-1.6, 1.6, 14.2, 15.2, -1.6, 1.6, C.cream),
	}
	for _, y in { 4, 10 } do
		table.insert(out, Box(-1.2, 1.2, y, y + 0.7, -1.2, 1.2, C.cream, DECOR))
	end
	Put(out, SubwayKit.GlobeLamp(1.6, 1.3), CFrame.new(0, 13.0, -1.1))
	return out
end

-- Ребро свода над боковой платформой (в плоскости X–Y): от капители колонны (0, y0) дугой вверх к стене (span,
-- y0 + rise). Пять сегментов по четверти эллипса; соседние разной толщины по Z — их боковые грани не совпадают.
function SubwayParts.Rib(span: number, y0: number, rise: number): { Brick }
	local out = {}
	local n = 5
	local function point(k: number): Vector3
		local phi = math.rad(90 * k / n)
		return V(span - span * math.cos(phi), y0 + rise * math.sin(phi), 0)
	end
	for k = 0, n - 1 do
		local a, b = point(k), point(k + 1)
		local d = b - a
		local at = CFrame.new((a + b) / 2) * CFrame.Angles(0, 0, math.atan2(d.Y, d.X))
		local t = if k % 2 == 0 then 1.4 else 1.55
		table.insert(out, B(V(d.Magnitude + 0.8, 1.2, t), at, C.cream, DECOR))
	end
	return out
end

-- Эскалатор: поднимается вдоль +X от 0 до run на высоту rise, ширина вдоль Z ±half. Ступени на наклонной ферме,
-- балюстрады с чёрным поручнем и тёплой подсветкой, площадки внизу и вверху (верхняя длиной landing).
function SubwayParts.Escalator(run: number, rise: number, half: number, landing: number): { Brick }
	local out = {}
	local len = math.sqrt(run * run + rise * rise)
	local angle = math.atan2(rise, run)
	local incline = CFrame.new(run / 2, rise / 2, 0) * CFrame.Angles(0, 0, angle)
	table.insert(out, B(V(len + 1.5, 1.6, half * 2 + 0.6), incline * CFrame.new(0, -1.2, 0), C.metal))
	local steps = 12
	for i = 0, steps - 1 do
		local x0, x1 = i * run / steps, (i + 1) * run / steps
		local top = (i + 1) * rise / steps
		local w = if i % 2 == 0 then half else half - 0.05 -- у соседних ступеней боковые грани не совпадают
		table.insert(out, Box(x0, x1 + 0.05, top - 1.4, top, -w, w, if i % 2 == 0 then C.railDark else C.metal, DECOR))
	end
	for _, s in { -1, 1 } do
		local side = CFrame.new(0, 0, s * (half + 0.35))
		table.insert(out, B(V(len + 0.6, 2.4, 0.4), side * incline * CFrame.new(0, 0.6, 0), C.tileLight, DECOR))
		table.insert(out, B(V(len + 1.0, 0.4, 0.6), side * incline * CFrame.new(0, 1.95, 0), C.graphite, DECOR))
		table.insert(out, Neon(V(len, 0.25, 0.2), side * incline * CFrame.new(0, -0.45, -s * 0.25), C.lamp))
	end
	table.insert(out, Box(-2.5, 0.1, 0, 0.25, -half - 0.6, half + 0.6, C.railDark, DECOR))
	-- Верхняя площадка доходит ровно до проёма в стене (длина площадки — landing) и уже его.
	table.insert(out, Box(run + 0.05, run + landing, rise - 0.6, rise, -half - 0.5, half + 0.5, C.metal))
	return out
end

-- Касса «БИЛЕТЫ»: кремовый киоск с кафельной крышей, окошко, прилавок, вывеска, тёплая лампа. Лицо — −Z.
function SubwayParts.TicketBooth(): { Brick }
	return {
		Box(-3.4, 3.4, 0, 0.5, -2.8, 2.8, C.tileDark),
		Box(-3, 3, 0.5, 7.5, -2.5, 2.5, C.cream),
		Box(-3.5, 3.5, 7.5, 8.3, -3, 3, C.tile),
		Box(-3.2, 3.2, 8.3, 8.8, -2.7, 2.7, C.tileDark, DECOR),
		Box(-1.8, 1.8, 3.2, 5.8, -2.6, -2.45, C.tileLight, DECOR),
		Box(-2.2, 2.2, 3.0, 3.3, -3.3, -2.45, C.wood, DECOR),
		Board(V(5.6, 1.4, 0.3), V(0, 6.7, -2.65), C.tileDark, Label("БИЛЕТЫ")),
		Neon(V(0.8, 0.5, 0.8), V(0, 7.25, -3.1), C.lampLight, 14),
	}
end

-- Ряд из count турникетов вдоль X с шагом 3: тумба, крышка с зелёной стрелкой, трёхлучевая вертушка к −Z.
function SubwayParts.Turnstiles(count: number): { Brick }
	local out = {}
	for i = 0, count - 1 do
		local x = (i - (count - 1) / 2) * 3
		table.insert(out, Box(x - 0.6, x + 0.6, 0, 3.0, -1.2, 1.2, C.metal))
		table.insert(out, Box(x - 0.7, x + 0.7, 3.0, 3.3, -1.3, 1.3, C.graphite, DECOR))
		table.insert(out, Neon(V(0.6, 0.12, 0.8), V(x, 3.36, -0.4), C.green))
		for k = 0, 2 do
			local arm = CFrame.new(x + 0.6, 2.4, -0.6) * CFrame.Angles(0, 0, math.rad(k * 120)) * CFrame.new(0.75, 0, 0)
			table.insert(out, B(V(1.5, 0.18, 0.18), arm, C.railDark, DECOR))
		end
	end
	return out
end

-- Табло станции: тёмная рама, кремовый кант, синяя табличка с надписью text. Лицо — −Z, центр на высоте 0.
function SubwayParts.StationBoard(text: string, width: number): { Brick }
	return {
		Box(-width / 2 - 0.6, width / 2 + 0.6, -2.3, 2.3, 0, 0.5, C.tileDark),
		Box(-width / 2 - 0.25, width / 2 + 0.25, -1.95, 1.95, -0.1, 0.1, C.cream, DECOR),
		Board(V(width, 3.3, 0.3), V(0, 0, -0.2), C.tile, Label(text)),
	}
end

-- Плакат на стене: бумажная рамка и цветной лист с надписью text. Лицо — −Z.
function SubwayParts.Poster(text: string, color: Color3, width: number): { Brick }
	return {
		Box(-width / 2 - 0.4, width / 2 + 0.4, -1.7, 1.7, 0, 0.2, C.paper),
		Board(V(width, 2.8, 0.25), V(0, 0, -0.08), color, Label(text)),
	}
end

-- Станционный фонарь-прожектор на босса: тумба, столб, кремовые пояса, головка со SpotLight на target (вектор от
-- основания фонаря), шар сверху. Высота головки 13.5 — свет ложится на корпус, не только на макушку (D45).
function SubwayParts.SpotPost(target: Vector3): { Brick }
	local out = {
		Box(-1.4, 1.4, 0, 0.8, -1.4, 1.4, C.tileDark),
		Disc(1.0, 0.8, 14.6, 0, 0, C.graphite, { collide = true }),
		Box(-0.9, 0.9, 14.6, 15.2, -0.9, 0.9, C.goldDark),
		B(
			V(1.4, 1.4, 1.4),
			V(0, 15.9, 0),
			C.lampLight,
			{ shape = "Ball", material = Enum.Material.Neon, collide = false, shadow = false }
		),
	}
	for _, y in { 5, 10 } do
		table.insert(out, Disc(1.5, y, y + 0.5, 0, 0, C.cream))
	end
	local from = V(0, 13.5, 0)
	local head = CFrame.lookAt(from + (target - from).Unit * 1.4, target)
	table.insert(
		out,
		B(
			V(1.8, 1.4, 2),
			head,
			C.graphite,
			{ collide = false, shadow = false, light = { range = 46, brightness = 1, color = C.spot, angle = 60 } }
		)
	)
	table.insert(out, Neon(V(1.4, 1.0, 0.2), head * CFrame.new(0, 0, -1.05), C.lampLight))
	return out
end

return SubwayParts

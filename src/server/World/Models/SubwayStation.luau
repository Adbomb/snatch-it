-- Уровень 3 «Подземка» (D54): заброшенная станция метро без потолка — свет игры общий, небо остаётся, подземку
-- читают кафель, пути, вагоны, тоннели и лампы; ярко, не мрачно. По центру перрон из светлых плит с жёлтыми линиями
-- безопасности и фиолетовой ковровой дорожкой от входа к боссу; по бокам пути (щебень, шпалы, рельсы, тупиковые
-- упоры); дальше боковые платформы с колоннами-лампами, рёбрами свода, кассой, турникетами, эскалатором в обрыв,
-- ящиками и крысятами; у обрывов — кафельные стены с тоннелями, табло, плакатами и трубами. В центре — площадка
-- босса «Королевский люк» (кафельное кольцо с огоньками, золотой обод, ковёр, крышка люка с короной под боссом;
-- 4 предмета на бархатных подушках, MapLayout.Arenas[3]); за боссом — тронный вагон короля с горой золота. Слева
-- (для входящего игрока) на пути — вагон с открытой дверью, касса и турникеты; справа — дрезина, вагонетки с
-- золотом и эскалатор. Поперёк коридора ничего нет (D41); в круге,
-- куда босс заходит в бою (r 34, scripts/lune/check_world.luau), — только пол не выше 2 стадов. Света мало
-- (2 прожектора, вагон, 2 тоннеля, касса), частиц нет. Координаты зоны: x — поперёк (±92, стены у обрывов с 86),
-- z — вдоль (вход −47.5, выход +47.5), y = 0 — пол. Надписи вывесок возвращаются списком (их пишет WorldBuilder).
-- Зависит от MapLayout, World/Models/SubwayKit, World/Models/SubwayParts.

local ServerScriptService = game:GetService("ServerScriptService")

local World = ServerScriptService.Server.World
local MapLayout = require(World.MapLayout)
local SubwayKit = require(World.Models.SubwayKit)
local SubwayParts = require(World.Models.SubwayParts)

type Brick = SubwayKit.Brick
export type Sign = { name: string, faces: { Enum.NormalId }, text: string }

local B, V, C = SubwayKit.B, SubwayKit.V, SubwayKit.C
local Box, Disc, Neon, Put = SubwayKit.Box, SubwayKit.Disc, SubwayKit.Neon, SubwayKit.Put
local DECOR = SubwayKit.DECOR

local HALF = MapLayout.ZoneSize / 2 -- вход −HALF, выход +HALF
local PLATFORM = 30 -- перрон |x| < 30
local TRACK = 39 -- ось пути
local SIDE = 47 -- боковые платформы с |x| = 47
local WALL = 86 -- лицо стены станции (обрыв — с 92)
local WALL_TOP = 24
local COLUMN = 50.5 -- колонны боковых платформ
local BAYS = { -38, -19, 0, 19, 38 } -- колонны, рёбра свода, пилястры стен
local RUNNER = 4.5 -- полуширина ковровой дорожки
local ROW = HALF * 2 / 16 -- ряд плит перрона вдоль z
local SEAM = 0.5
local L, R = 1, -1 -- лево и право входящего игрока (лицом к выходу): лево — +x зоны
local TUNNELS = { [L] = 28.5, [R] = -28.5 } -- z тоннеля в левой и правой стене
local TUNNEL = { half = 7, top = 12 }
local ESCALATOR = { z = 9.5, half = 3.5, run = 24, rise = 16, landing = 4.4 } -- справа

-- Высоты верха слоёв пола (D36): шаг 0.05 — грани ближе 0.05 друг к другу мерцают (World/FaceCheck).
local TOP = {
	ballast = 0.08, -- щебень путей
	grout = 0.05, -- подложка плит (швы)
	slab = 0.1, -- плиты перрона и боковых платформ
	inlay = 0.15, -- ковровая дорожка, жёлтые линии, бордюры
	edge = 0.2, -- золотая кромка дорожки, кафельное кольцо площадки
	rim = 0.25, -- золотой обод площадки, ромбы дорожки
	carpet = 0.3, -- ковёр площадки, огоньки кольца
	dash = 0.35, -- пунктир на ковре, крышка люка
	sleeper = 0.32, -- шпалы (верх рельса — SubwayParts.RAIL_TOP)
}

local SubwayStation = {}

local function X(s: number, a: number, b: number): (number, number)
	return math.min(s * a, s * b), math.max(s * a, s * b)
end

-- Пол станции: перрон с плитами и дорожкой, площадка босса, пути, боковые платформы.
function SubwayStation.Ground(): { Brick }
	local out = {}
	local arena = MapLayout.Arenas[3]
	local center = MapLayout.BossSpot
	local outer = arena.radius + 3 -- кафельное кольцо

	-- Плита целиком под площадкой или дорожкой не нужна.
	local function hidden(x0: number, x1: number, z0: number, z1: number): boolean
		local corners = { Vector2.new(x0, z0), Vector2.new(x1, z0), Vector2.new(x0, z1), Vector2.new(x1, z1) }
		local inArena = true
		for _, corner in corners do
			inArena = inArena and (corner - center).Magnitude < outer
		end
		local onRunner = x0 >= -RUNNER and x1 <= RUNNER and z1 <= center.Y - outer + 1
		return inArena or onRunner
	end

	-- Перрон: ряды плит со сдвигом на полплиты по подложке (швы), редкие плиты темнее.
	table.insert(out, Box(-PLATFORM, PLATFORM, 0, TOP.grout, -HALF + 0.1, HALF - 0.1, C.seam, DECOR))
	for row = 0, 15 do
		local z0 = -HALF + row * ROW
		local edges = { -PLATFORM }
		local x = -PLATFORM + (if row % 2 == 0 then 10 else 5)
		while x < PLATFORM - 0.01 do
			table.insert(edges, x)
			x += 10
		end
		table.insert(edges, PLATFORM)
		for column = 1, #edges - 1 do
			local x0, x1 = edges[column], edges[column + 1]
			if not hidden(x0, x1, z0, z0 + ROW) then
				local color = if (row * 5 + column * 3) % 7 == 0 then C.concreteDark else C.concrete
				local half = SEAM / 2
				table.insert(out, Box(x0 + half, x1 - half, 0, TOP.slab, z0 + half, z0 + ROW - half, color, DECOR))
			end
		end
	end

	-- Жёлтые линии безопасности и бордюры у края перрона и боковых платформ.
	for _, s in { -1, 1 } do
		local a, b = X(s, PLATFORM - 1.6, PLATFORM - 0.4)
		table.insert(out, Box(a, b, 0, TOP.inlay, -HALF + 0.3, HALF - 0.3, C.yellow, DECOR))
		a, b = X(s, PLATFORM - 0.3, PLATFORM + 0.5)
		table.insert(out, Box(a, b, 0, TOP.inlay, -HALF + 0.2, HALF - 0.2, C.concreteDark, DECOR))
		-- Путь: щебень, шпалы, рельсы.
		a, b = X(s, PLATFORM + 0.5, SIDE)
		table.insert(out, Box(a, b, 0, TOP.ballast, -HALF, HALF, C.gravel, DECOR))
		for k = 0, 37 do
			local z = -HALF + 1.25 + k * 2.5
			local x0, x1 = X(s, TRACK - 5.5, TRACK + 5.5)
			table.insert(out, Box(x0, x1, 0, TOP.sleeper, z - 0.6, z + 0.6, C.sleeper, DECOR))
		end
		for _, r in { TRACK - SubwayParts.GAUGE / 2, TRACK + SubwayParts.GAUGE / 2 } do
			local x0, x1 = X(s, r - 0.25, r + 0.25)
			table.insert(out, Box(x0, x1, TOP.sleeper, SubwayParts.RAIL_TOP, -HALF + 0.4, HALF - 0.4, C.rail, DECOR))
		end
		-- Боковая платформа: бордюр, жёлтая линия, плиты по подложке до стены.
		a, b = X(s, SIDE, WALL)
		table.insert(out, Box(a, b, 0, TOP.grout, -HALF + 0.15, HALF - 0.15, C.seam, DECOR))
		for row = 0, 7 do
			local z0 = -HALF + row * HALF / 4
			for _, span in { { SIDE + 0.8, 66.5 }, { 66.5, WALL } } do
				local x0, x1 = X(s, span[1] + SEAM / 2, span[2] - SEAM / 2)
				local color = if (row + span[1]) % 3 < 1 then C.concreteDark else C.concreteSide
				table.insert(out, Box(x0, x1, 0, TOP.slab, z0 + SEAM / 2, z0 + HALF / 4 - SEAM / 2, color, DECOR))
			end
		end
		a, b = X(s, SIDE, SIDE + 0.8)
		table.insert(out, Box(a, b, 0, TOP.inlay, -HALF + 0.25, HALF - 0.25, C.concreteDark, DECOR))
		a, b = X(s, SIDE + 0.9, SIDE + 2.1)
		table.insert(out, Box(a, b, 0, TOP.inlay, -HALF + 0.35, HALF - 0.35, C.yellow, DECOR))
	end

	-- Ковровая дорожка короля от входа к площадке: фиолетовая, золотая кромка, золотые ромбы.
	table.insert(out, Box(-RUNNER, RUNNER, 0, TOP.inlay, -HALF + 0.2, center.Y - outer + 1, C.purple, DECOR))
	for _, s in { -1, 1 } do
		local a, b = X(s, RUNNER, RUNNER + 0.6)
		-- От входа — за полосой границы зоны (WorldBuilder: ширина 1, верх на той же высоте 0.2).
		table.insert(out, Box(a, b, 0, TOP.edge, -HALF + 0.7, center.Y - outer - 0.5, C.gold, DECOR))
	end
	for k = 0, 2 do
		local at = CFrame.new(0, TOP.rim / 2, -HALF + 4 + k * 5) * CFrame.Angles(0, math.rad(45), 0)
		table.insert(out, B(V(2.6, TOP.rim, 2.6), at, if k % 2 == 0 then C.gold else C.purpleLight, DECOR))
	end

	-- Площадка «Королевский люк»: кафельное кольцо с огоньками, золотой обод, ковёр, пунктир, крышка люка с короной.
	local function disc(diameter: number, top: number, color: Color3): Brick
		return Disc(diameter, 0, top, center.X, center.Y, color)
	end
	local function around(angle: number, radius: number, top: number): CFrame
		return CFrame.new(center.X, top / 2, center.Y) * CFrame.Angles(0, angle, 0) * CFrame.new(0, 0, radius)
	end
	table.insert(out, disc(outer * 2, TOP.edge, C.tileDark))
	for k = 0, 15 do
		table.insert(
			out,
			Neon(V(0.9, TOP.carpet, 0.9), around(math.rad(11.25 + k * 22.5), outer - 0.9, TOP.carpet), C.yellow)
		)
	end
	table.insert(out, disc((arena.radius + 1.3) * 2, TOP.rim, C.gold))
	table.insert(out, disc(arena.radius * 2, TOP.carpet, C.purple))
	for k = 0, 23 do
		table.insert(
			out,
			B(V(2.6, TOP.dash, 0.45), around(math.rad(7.5 + k * 15), arena.radius - 3, TOP.dash), C.goldLight, DECOR)
		)
	end
	table.insert(out, disc(10.8, TOP.dash, C.iron))
	table.insert(out, disc(9.2, 0.4, C.ironDark))
	table.insert(out, disc(7.4, 0.45, C.iron))
	-- Корона на крышке люка: зубцы смотрят от входа (так её читает входящий).
	local function emblem(x0: number, x1: number, z0: number, z1: number, color: Color3)
		table.insert(out, Box(center.X + x0, center.X + x1, 0, 0.5, center.Y + z0, center.Y + z1, color, DECOR))
	end
	emblem(-1.5, 1.5, -1.0, -0.4, C.gold)
	emblem(-1.3, -0.7, -0.4, 0.8, C.gold)
	emblem(-0.3, 0.3, -0.4, 1.2, C.goldLight)
	emblem(0.7, 1.3, -0.4, 0.8, C.gold)
	for _, x in { -0.9, 0, 0.9 } do
		table.insert(out, Neon(V(0.36, 0.55, 0.3), V(center.X + x, 0.275, center.Y - 0.7), C.signal))
	end

	-- 4 бархатные подушки под предметы босса с золотой каймой и кистями, рядом монеты (предмет стоит на подушке:
	-- верх подушки — Arenas[3].top).
	for i, spot in MapLayout.ArtSlots do
		local at = CFrame.new(spot.X, 0, spot.Y) * CFrame.Angles(0, math.rad(arena.turns[i]), 0)
		table.insert(out, B(V(4.1, 0.52, 4.1), at * CFrame.new(0, 0.26, 0), C.goldDark, DECOR))
		table.insert(out, B(V(3.7, arena.top, 3.7), at * CFrame.new(0, arena.top / 2, 0), C.velvet, DECOR))
		for _, corner in { V(-2.2, 0, -2.2), V(2.2, 0, -2.2), V(2.2, 0, 2.2), V(-2.2, 0, 2.2) } do
			table.insert(out, B(V(0.5, 0.55, 0.5), at * CFrame.new(corner.X, 0.275, corner.Z), C.gold, DECOR))
		end
		for k, offset in { V(-2.9, 0, 1.1), V(2.7, 0, -1.6), V(1.4, 0, 2.9) } do
			local p = at * CFrame.new(offset)
			table.insert(out, SubwayKit.Coin(p.Position.X, p.Position.Z, 0.34 + k * 0.05))
		end
	end
	return out
end

-- Стена станции с той стороны s (лицо x = s·WALL, до обрыва): кафель, тёмный цоколь, кремовая полоса, карниз и
-- верхний пояс, пилястры у рёбер свода; проёмы — тоннель и решётка эскалатора.
local function wall(out: { Brick }, s: number, openings: { { number } })
	local function slab(z0: number, z1: number, y0: number, y1: number, color: Color3)
		local x0, x1 = X(s, WALL, 92)
		table.insert(out, Box(x0, x1, y0, y1, z0, z1, color))
	end
	-- Тело стены: между проёмами — во всю высоту, над и под проёмом — куски.
	table.sort(openings, function(a, b)
		return a[1] < b[1]
	end)
	local z = -HALF
	for _, o in openings do
		slab(z, o[1], 0, WALL_TOP, C.tile)
		if o[3] > 0 then
			slab(o[1], o[2], 0, o[3], C.tile)
		end
		slab(o[1], o[2], o[4], WALL_TOP, C.tile)
		z = o[2]
	end
	slab(z, HALF, 0, WALL_TOP, C.tile)
	-- Полосы вдоль стены, с пропусками в проёмах, которые они пересекли бы.
	local function band(y0: number, y1: number, color: Color3, depth: number)
		local x0, x1 = X(s, WALL - depth, WALL)
		local from = -HALF
		for _, o in openings do
			if y1 > o[3] and y0 < o[4] then
				table.insert(out, Box(x0, x1, y0, y1, from, o[1], color, DECOR))
				from = o[2]
			end
		end
		table.insert(out, Box(x0, x1, y0, y1, from, HALF, color, DECOR))
	end
	band(0, 2.2, C.tileDark, 0.15)
	band(7.8, 8.9, C.cream, 0.12)
	band(20.8, 22.2, C.cream, 0.3)
	band(22.2, WALL_TOP, C.tileDark, 0.1)
	for _, bz in BAYS do
		local x0, x1 = X(s, WALL - 0.5, WALL)
		table.insert(out, Box(x0, x1, 0, 20.8, bz - 1.2, bz + 1.2, C.tileLight, DECOR))
	end
end

-- Тоннель в стене стороны s с центром z: скруглённый верх, кремовый портал с золотым замковым камнем, тёмно-синяя
-- глубина, лампы цепочкой вглубь, рельсы из тоннеля и тупиковый упор, тёплый свет.
local function tunnel(out: { Brick }, s: number, z: number)
	local h, top = TUNNEL.half, TUNNEL.top
	local function xr(a: number, b: number): (number, number)
		return X(s, a, b)
	end
	local x0, x1 = xr(WALL, 91.4)
	table.insert(out, Box(x0, x1, 0, 0.05, z - h, z + h, C.tunnelDeep, DECOR)) -- пол
	x0, x1 = xr(91.4, 92)
	table.insert(out, Box(x0, x1, 0, top, z - h, z + h, C.tunnelDeep, DECOR)) -- дальняя стена
	for _, side in { -1, 1 } do
		local a, b = math.min(z + side * (h - 0.3), z + side * h), math.max(z + side * (h - 0.3), z + side * h)
		x0, x1 = xr(WALL + 0.05, 91.4)
		table.insert(out, Box(x0, x1, 0, top, a, b, C.tunnel, DECOR))
		-- Скругление верха: две ступени в углах проёма.
		a, b = math.min(z + side * (h - 1.4), z + side * h), math.max(z + side * (h - 1.4), z + side * h)
		x0, x1 = xr(WALL - 0.05, 91.4)
		table.insert(out, Box(x0, x1, top - 1.6, top, a, b, C.tile, DECOR))
		a, b =
			math.min(z + side * (h - 2.8), z + side * (h - 1.4)), math.max(z + side * (h - 2.8), z + side * (h - 1.4))
		table.insert(out, Box(x0, x1, top - 0.7, top, a, b, C.tile, DECOR))
		-- Портал: кремовые косяки (заходят в проём на 0.1 — закрывают торцы полос стены).
		a, b =
			math.min(z + side * (h - 0.1), z + side * (h + 1.2)), math.max(z + side * (h - 0.1), z + side * (h + 1.2))
		x0, x1 = xr(WALL - 0.4, WALL)
		table.insert(out, Box(x0, x1, 0, top + 0.6, a, b, C.cream, DECOR))
	end
	x0, x1 = xr(WALL - 0.6, WALL)
	table.insert(out, Box(x0, x1, top, top + 1.4, z - h - 1.4, z + h + 1.4, C.cream, DECOR)) -- перемычка
	x0, x1 = xr(WALL - 0.8, WALL)
	table.insert(out, Box(x0, x1, top + 0.1, top + 1.7, z - 0.8, z + 0.8, C.gold, DECOR)) -- замковый камень
	-- Лампы цепочкой вглубь (всё меньше) и тёплый свет.
	for k, depth in { 87.4, 89.0, 90.6 } do
		local size = 1.1 - k * 0.2
		local a, b = xr(depth - size / 2, depth + size / 2)
		table.insert(out, Neon(V(b - a, size * 0.6, size), V((a + b) / 2, top - 0.8 - k * 0.1, z), C.lampLight))
	end
	table.insert(out, Neon(V(0.6, 0.6, 0.6), V(s * 90, top - 3, z), C.lamp, 16))
	-- Рельсы из тоннеля на платформу и упор на краю.
	for _, r in { -2.5, 2.5 } do
		local a, b = xr(68, 91.4)
		table.insert(out, Box(a, b, 0.24, 0.5, z + r - 0.25, z + r + 0.25, C.rail, DECOR))
	end
	for k = 0, 8 do
		local cx = 70 + k * 2.6
		local a, b = xr(cx - 0.55, cx + 0.55)
		table.insert(out, Box(a, b, 0.05, 0.24, z - 3.6, z + 3.6, C.sleeper, DECOR))
	end
	Put(out, SubwayParts.BufferStop(), CFrame.new(s * 67, 0, z) * CFrame.Angles(0, -s * math.pi / 2, 0))
end

-- Весь декор «Подземки» в координатах зоны и надписи вывесок.
function SubwayStation.Zone(): ({ Brick }, { Sign })
	SubwayKit.Reset()
	local out = SubwayStation.Ground()
	-- Стороны — для входящего игрока (лицом к выходу): слева +x зоны, справа −x. Вещь у стороны смотрит лицом −Z к
	-- середине коридора.
	local function left(z: number, x: number, turn: number?): CFrame
		return CFrame.new(L * x, 0, z) * CFrame.Angles(0, math.pi / 2 + (turn or 0), 0)
	end
	local function right(z: number, x: number, turn: number?): CFrame
		return CFrame.new(R * x, 0, z) * CFrame.Angles(0, -math.pi / 2 + (turn or 0), 0)
	end
	local function facing(x: number, z: number, target: Vector2, y: number?): CFrame
		return CFrame.lookAt(V(x, y or 0, z), V(target.X, y or 0, target.Y))
	end
	local boss = MapLayout.BossSpot

	-- Стены с тоннелями; справа — решётка наверху эскалатора.
	local e = ESCALATOR
	wall(out, L, { { TUNNELS[L] - TUNNEL.half, TUNNELS[L] + TUNNEL.half, 0, TUNNEL.top } })
	wall(out, R, {
		{ TUNNELS[R] - TUNNEL.half, TUNNELS[R] + TUNNEL.half, 0, TUNNEL.top },
		{ e.z - e.half - 0.6, e.z + e.half + 0.6, e.rise, e.rise + 4.6 },
	})
	tunnel(out, L, TUNNELS[L])
	tunnel(out, R, TUNNELS[R])

	-- Колонны с лампами, рёбра свода с подвесными лампами над боковыми платформами (поперёк коридора ничего нет).
	local span = WALL - COLUMN
	for _, s in { L, R } do
		for _, z in BAYS do
			Put(out, SubwayParts.Column(), if s == L then left(z, COLUMN) else right(z, COLUMN))
			local turn = if s < 0 then CFrame.Angles(0, math.pi, 0) else CFrame.new()
			Put(out, SubwayParts.Rib(span, 15.2, 8), CFrame.new(s * COLUMN, 0, z) * turn)
			-- Лампа на цепи с середины ребра (там его низ на высоте около 21.5).
			local x = s * (COLUMN + span / 2)
			table.insert(out, Box(x - 0.1, x + 0.1, 18.6, 21.6, z - 0.1, z + 0.1, C.graphite, DECOR))
			table.insert(out, Box(x - 0.55, x + 0.55, 18.2, 18.7, z - 0.55, z + 0.55, C.goldDark, DECOR))
			local glow = SubwayKit.With(SubwayKit.BALL, { material = Enum.Material.Neon })
			table.insert(out, B(V(1.5, 1.5, 1.5), V(x, 17.5, z), C.lampLight, glow))
		end
		-- Трубы вдоль стены и хомуты у пилястр.
		for _, pipe in { { 18.6, 0.9, C.pipeRed }, { 19.8, 0.7, C.pipeTeal } } do
			local at = CFrame.new(s * (WALL - 0.75), pipe[1], 0) * CFrame.Angles(0, math.pi / 2, 0)
			table.insert(out, B(V(HALF * 2 - 0.4, pipe[2], pipe[2]), at, pipe[3], SubwayKit.ROUND))
		end
		for _, z in BAYS do
			local x0, x1 = X(s, WALL - 1.4, WALL - 0.5)
			table.insert(out, Box(x0, x1, 17.9, 20.4, z - 0.25, z + 0.25, C.graphite, DECOR))
		end
	end

	-- Табло «ПОДЗЕМКА», плакаты (выше крыши кассы — их видно из коридора). Отодвинуты от стены: грани не совпадают
	-- с кафелем (D36).
	Put(out, SubwayParts.StationBoard("ПОДЗЕМКА", 13), left(-9.5, WALL) * CFrame.new(0, 12.4, -0.3))
	Put(out, SubwayParts.StationBoard("ПОДЗЕМКА", 13), right(28.5, WALL) * CFrame.new(0, 12.4, -0.3))
	Put(
		out,
		SubwayParts.Poster("РАЗЫСКИВАЕТСЯ", C.signal, 8.4),
		left(-28.5, WALL) * CFrame.new(0, 13.4, -0.25)
	)
	Put(
		out,
		SubwayParts.Poster("НЕ КОРМИТЬ КРЫС", C.purple, 9.4),
		right(-9.5, WALL) * CFrame.new(0, 13.4, -0.25)
	)

	-- Эскалатор вверх в обрыв (справа), наверху решётка «ВЫХОД ЗАКРЫТ».
	local foot = WALL - e.landing - e.run
	local stairs = CFrame.new(R * foot, 0, e.z) * CFrame.Angles(0, if R < 0 then math.pi else 0, 0)
	Put(out, SubwayParts.Escalator(e.run, e.rise, e.half, e.landing), stairs)
	for k = 0, 7 do
		local zz = e.z - e.half - 0.2 + k * (e.half * 2 + 0.4) / 7
		local x0, x1 = X(R, WALL + 0.1, WALL + 0.35)
		table.insert(out, Box(x0, x1, e.rise, e.rise + 4.6, zz - 0.12, zz + 0.12, C.metal, DECOR))
	end
	local g0, g1 = X(R, WALL + 2.5, 92)
	table.insert(out, Box(g0, g1, e.rise, e.rise + 4.6, e.z - e.half - 0.6, e.z + e.half + 0.6, C.tunnelDeep, DECOR))
	local face = if R < 0 then Enum.NormalId.Right else Enum.NormalId.Left -- табличка смотрит в коридор
	local exitSign = SubwayKit.Label("ВЫХОД ЗАКРЫТ", { face })
	table.insert(out, SubwayKit.Board(V(0.3, 1.3, 8.6), V(R * (WALL - 0.4), 22.75, e.z), C.signal, exitSign))

	-- Вагон на левом пути: открытая дверь с золотом, на крыше ящики и крысёнок.
	local inward = CFrame.Angles(0, L * math.pi / 2, 0) -- лицом −Z к середине коридора с левой стороны
	Put(out, SubwayParts.Wagon(28, true), left(22, TRACK))
	Put(out, SubwayKit.Crate(), CFrame.new(L * TRACK, 11.2, 28) * CFrame.Angles(0, 0.3, 0))
	Put(out, SubwayKit.Crate(), CFrame.new(L * (TRACK - 0.4), 11.2, 31.5) * CFrame.Angles(0, -0.2, 0))
	SubwayKit.Sack(out, CFrame.new(L * (TRACK + 0.6), 11.2, 17) * CFrame.Angles(0, 0.5, 0), 0.9)
	Put(out, SubwayKit.RatMinion(), CFrame.new(L * (TRACK - 1), 11.2, 13.5) * inward)
	-- Правый путь: дрезина и две вагонетки с золотом.
	Put(out, SubwayParts.Handcar(), CFrame.new(R * TRACK, 0, -33))
	Put(out, SubwayParts.MineCart(C.purpleLight), CFrame.new(R * TRACK, 0, -21))
	Put(out, SubwayParts.MineCart(C.signal), CFrame.new(R * TRACK, 0, -12.5))
	-- Тупиковые упоры на концах путей и путевые светофоры у входа.
	for _, s in { L, R } do
		Put(out, SubwayParts.BufferStop(), CFrame.new(s * TRACK, 0, -HALF + 1.6) * SubwayKit.TURN)
		Put(out, SubwayParts.BufferStop(), CFrame.new(s * TRACK, 0, HALF - 1.6))
		local lit = if s == L then C.signal else C.green
		Put(out, SubwayParts.Signal(lit), CFrame.new(s * (SIDE + 3), 0, -HALF + 4))
	end

	-- Левая платформа: касса, турникеты, скамейка, ящики с добычей, крысята.
	Put(out, SubwayParts.TicketBooth(), left(-33, 66))
	Put(out, SubwayParts.Turnstiles(4), left(-15, 70))
	Put(out, SubwayKit.Bench(6), left(4.5, 58))
	Put(out, SubwayKit.Litter(), CFrame.new(L * 57, 0, -22) * CFrame.Angles(0, 0.6, 0))
	Put(out, SubwayKit.Crate(), CFrame.new(L * 62, 0, 35) * CFrame.Angles(0, 0.2, 0))
	Put(out, SubwayKit.Crate(), CFrame.new(L * 62.4, 4.0, 35.3) * CFrame.Angles(0, -0.25, 0))
	Put(out, SubwayKit.Crate(), CFrame.new(L * 57.8, 0, 38.5) * CFrame.Angles(0, 0.55, 0))
	Put(out, SubwayKit.GoldChest(), left(30, 58, -0.2))
	Put(out, SubwayKit.RatMinion(), CFrame.new(L * 62.4, 8.0, 35.3) * inward * CFrame.Angles(0, -0.3, 0))
	Put(out, SubwayKit.RatMinion(), left(TUNNELS[L], 80, -0.4)) -- выглядывает из тоннеля между рельсами
	-- Правая платформа: скамейки, ящики, чемоданы, мусор, крысёнок у эскалатора.
	Put(out, SubwayKit.Bench(6), right(31, 58))
	Put(out, SubwayKit.Bench(6), right(39, 58))
	Put(out, SubwayKit.Crate(), CFrame.new(R * 61, 0, -40) * CFrame.Angles(0, 0.3, 0))
	Put(out, SubwayKit.Crate(), CFrame.new(R * 65.5, 0, -41.5) * CFrame.Angles(0, -0.15, 0))
	Put(out, SubwayKit.CoinSacks(), right(-36, 61, -0.3))
	Put(out, SubwayKit.Suitcases(), right(-12.5, 66, 0.25))
	Put(out, SubwayKit.Litter(), CFrame.new(R * 57, 0, 22) * CFrame.Angles(0, 0.4, 0))
	Put(out, SubwayKit.RatMinion(), CFrame.new(R * 61, 4.0, -40) * CFrame.Angles(0, -L * math.pi / 2 + 0.3, 0))
	Put(out, SubwayKit.RatMinion(), right(e.z - e.half - 2.2, foot - 1.5, 0.3))

	-- Вход на перрон: скамейки лицом к площадке и урны по углам; немного мусора на перроне за кругом площадки.
	for _, s in { L, R } do
		Put(out, SubwayKit.Bench(6), CFrame.new(s * 19, 0, -43) * SubwayKit.TURN)
		table.insert(out, Disc(1.7, 0, 2.3, s * 25.5, -44, C.tileDark, { collide = true }))
		table.insert(out, Disc(1.95, 2.3, 2.6, s * 25.5, -44, C.metal))
	end
	Put(out, SubwayKit.Litter(), CFrame.new(L * 22, 0, -30) * CFrame.Angles(0, 1.1, 0))
	Put(out, SubwayKit.Litter(), CFrame.new(R * 22, 0, 16) * CFrame.Angles(0, -0.7, 0))

	-- За боссом: тронный вагон на коротком пути, перед ним золото, сундук, мешки, чемоданы и крысёнок; фонари-прожекторы
	-- светят на короля (в середину корпуса).
	local throne = 41
	Put(out, SubwayParts.TrackX(-16, 16), CFrame.new(0, 0, throne))
	Put(out, SubwayParts.ThroneWagon(), CFrame.new(0, 0, throne))
	table.insert(out, Box(-2.4, 2.4, 0, 0.7, 30.6, 33, C.gold, DECOR))
	table.insert(out, Box(-1.4, 1.4, 0.7, 1.3, 31, 32.6, C.goldLight, DECOR))
	Put(out, SubwayKit.GoldChest(), facing(-8.5, 33, boss))
	Put(out, SubwayKit.CoinSacks(), facing(8.8, 33.5, boss))
	Put(out, SubwayKit.Suitcases(), facing(-13.2, 34.5, boss) * CFrame.Angles(0, 0.4, 0))
	Put(out, SubwayKit.RatMinion(), facing(4.5, 31.6, boss))
	local target = V(boss.X, 7, boss.Y)
	for _, x in { -24, 24 } do
		local at = V(x, 0, 27)
		Put(out, SubwayParts.SpotPost(target - at), CFrame.new(at))
	end
	return out, SubwayKit.Signs()
end

return SubwayStation

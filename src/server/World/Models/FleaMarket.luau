-- Уровень 2 «Барахолка» (D43, редизайн D44, полировка D45, сквозные полосы D66): безумный рынок сокровищ. Проход
-- мощён крупными плитами тёплого камня со сдвигом рядов (без шахматки), от входа к боссу ведёт бирюзовая дорожка с
-- золотой кромкой и ромбами, по бокам — графитовые променады с золотыми вставками и неоновыми точками, бордюры с
-- золотым кантом. В центре — площадка босса в виде огромной монеты: графитовое кольцо с огоньками, золотой обод с
-- насечкой, бирюзовое поле (на нём 4 предмета, MapLayout.Arenas), пунктирное золотое кольцо и ромб-самоцвет под
-- боссом. За боссом — гора сокровищ с огромным сундуком (фон: торговец — хозяин рынка), по бокам от неё гигантские
-- карманные часы и стопка монет, перед ними башни-прожекторы на босса, между ними дорожки к выходу.
-- Шесть разных павильонов (World/Models/FleaStalls) стоят у стен обрыва, слева и справа разные и в разном порядке;
-- перед каждым на променаде — своя площадка. Между павильонами и проходом — сквозные полосы |x| 48–66
-- (MapLayout.Lane): в них нет твёрдого на высоте 1.1–7, по ним идёт бирюзовая дорожка 52–62 с золотыми кромками и
-- ромбами; выше 7 над полосой нависают только свесы крыш и верхний контейнер «Скупки». Между бордюром и
-- полосой (|x| ≈ 45) — вывески павильонов, которые от стен с камеры игрока далеко: щиты на двух столбах у каждого
-- павильона, мачты с подвесной «ДЁШЕВО!» и ценником «−50%», ящик «?»; там же фонарь у входа. В просветах у стен —
-- мачта с монетой, сундуки, мешки, штабель контейнеров; у входа — тележки с зонтами; вдоль бордюров — фонари, столбы с вывесками
-- редкостей и гирлянды флажков. Проход (|x| < 41) свободен для бега; в круге, куда босс заходит в бою (r 34,
-- scripts/lune/check_world.luau), — только пол не выше 2 стадов, высокое — дальше; у стен обрыва (|x| > 76)
-- твёрдое не выше 24. Арок и ворот нет (D41). Света мало (по одному на павильон, сундук, 2 прожектора), частиц нет —
-- для телефонов. Координаты зоны: x — поперёк коридора (±92, обрывы за краем), z — вдоль (вход −47.5, выход
-- +47.5), y = 0 — пол. Надписи вывесок возвращаются списком (их пишет WorldBuilder через World/Signs).
-- Зависит от MapLayout, World/Models/FleaKit, World/Models/FleaStalls.

local ServerScriptService = game:GetService("ServerScriptService")

local World = ServerScriptService.Server.World
local MapLayout = require(World.MapLayout)
local FleaKit = require(World.Models.FleaKit)
local FleaStalls = require(World.Models.FleaStalls)
local SlotGlow = require(World.SlotGlow)

type Brick = FleaKit.Brick
export type Sign = FleaKit.Sign

local B, V, C = FleaKit.B, FleaKit.V, FleaKit.C
local Box, Disc, Neon, Put = FleaKit.Box, FleaKit.Disc, FleaKit.Neon, FleaKit.Put
local DECOR = FleaKit.DECOR

local HALF = MapLayout.ZoneSize / 2 -- вход −HALF, выход +HALF
local PAVING = 30 -- мощение |x| < 30
local CURB = 41.5 -- бордюр (середина), между ним и мощением — променад
local STREET = 45 -- вывески павильонов у дорожки (|x|): между бордюром (до 42) и сквозной полосой (от 48)
local RUNNER = 7 -- полуширина дорожки от входа к площадке
local SLAB = V(12, 0, HALF * 2 / 16) -- плита мощения: 12 поперёк, 16 рядов вдоль
local SEAM = 0.5
local HOARD = Vector2.new(0, 36.4) -- гора сокровищ за боссом (крышка сундука — у конца зоны)
-- Путь к следующему уровню (|x|): полуширина перехода от кольца, дорожки по бокам горы сокровищ — от inner до outer
-- (гора — до 15.5, часы и стопка монет — от 21.9).
local EXIT = { spine = 2.4, inner = 16.5, outer = 20.5 }

local FleaMarket = {}

FleaMarket.Exit = EXIT -- проверяет scripts/lune/check_world.luau: на дорожках к выходу нет твёрдого

-- Высоты верха слоёв пола (D36): шаг 0.05 — грани ближе 0.05 друг к другу мерцают (World/FaceCheck).
local TOP = {
	grout = 0.05, -- подложка мощения (швы)
	slab = 0.1, -- плиты мощения и променады
	inlay = 0.15, -- дорожка, золотые квадратики мощения, вставки променадов
	porch = 0.2, -- площадки у павильонов, кромка дорожки; графитовое кольцо площадки босса
	pattern = 0.25, -- узор площадок, ромбы дорожки; золотой обод площадки босса
	dot = 0.3, -- неоновые точки; поле площадки босса — Arenas.top
	dash = 0.35, -- пунктир на поле площадки, внешний ромб под боссом
	teeth = 0.4, -- насечка обода
}

-- Пол барахолки поверх пола зоны: мощение со швами, променады с вставками и точками, бордюры, дорожка от входа и
-- площадка босса — монета (графитовое кольцо с огоньками, золотой обод с насечкой, поле с пунктиром, ромб-самоцвет
-- под боссом). Высоты слоёв — TOP.
function FleaMarket.Ground(): { Brick }
	local out = {}
	local arena = MapLayout.Arenas[2]
	local center = MapLayout.BossSpot
	local outer = arena.radius + 3 -- графитовое кольцо

	-- Плита целиком под другой плоскостью (площадка, дорожка, гора) не нужна.
	local function hidden(x0: number, x1: number, z0: number, z1: number): boolean
		local corners = { Vector2.new(x0, z0), Vector2.new(x1, z0), Vector2.new(x0, z1), Vector2.new(x1, z1) }
		local inArena = true
		for _, corner in corners do
			inArena = inArena and (corner - center).Magnitude < outer
		end
		local onRunner = x0 >= -RUNNER and x1 <= RUNNER and z1 <= center.Y - outer + 1
		return inArena or onRunner
	end

	-- Мощение: ряды плит со сдвигом на полплиты по тёплой подложке (швы), редкие плиты темнее; в стыках рядов —
	-- золотые квадратики.
	-- Концы слоёв у границ зоны не совпадают (подложка, дорожка и её кромка начинаются с разным отступом).
	table.insert(out, Box(-PAVING, PAVING, 0, TOP.grout, -HALF + 0.1, HALF - 0.1, C.grout, DECOR))
	for row = 0, 15 do
		local z0 = -HALF + row * SLAB.Z
		local edges = { -PAVING }
		local x = -PAVING + (if row % 2 == 0 then SLAB.X else SLAB.X / 2)
		while x < PAVING - 0.01 do
			table.insert(edges, x)
			x += SLAB.X
		end
		table.insert(edges, PAVING)
		for column = 1, #edges - 1 do
			local x0, x1 = edges[column], edges[column + 1]
			if not hidden(x0, x1, z0, z0 + SLAB.Z) then
				local dark = (row * 7 + column * 3) % 5 == 0
				local color = if dark then C.stoneDark else C.stone
				local half = SEAM / 2
				table.insert(out, Box(x0 + half, x1 - half, 0, TOP.slab, z0 + half, z0 + SLAB.Z - half, color, DECOR))
			end
			local near = hidden(x0 - 1, x0 + 1, z0 - 1, z0 + 1)
			if row % 2 == 1 and column > 1 and math.abs(x0) > RUNNER + 1 and not near then
				table.insert(out, Box(x0 - 0.45, x0 + 0.45, 0, TOP.inlay, z0 - 0.45, z0 + 0.45, C.gold, DECOR))
			end
		end
	end

	-- Променады вдоль павильонов: графит, поперечные золотые вставки, неоновые точки у края мощения; бордюры с
	-- золотым кантом.
	for _, s in { -1, 1 } do
		local function X(a: number, b: number): (number, number)
			return math.min(s * a, s * b), math.max(s * a, s * b)
		end
		local x0, x1 = X(PAVING, CURB - 0.5)
		table.insert(out, Box(x0, x1, 0, TOP.slab, -HALF, HALF, C.graphite, DECOR))
		for k = 0, 9 do
			local z = -HALF + 4.75 + k * 9.5
			local a, b = X(PAVING + 0.4, CURB - 0.9)
			table.insert(out, Box(a, b, 0, TOP.inlay, z - 0.2, z + 0.2, C.goldDark, DECOR))
			if k < 9 then
				local color = if s < 0 then C.orangeLight else C.tealLight
				table.insert(out, Neon(V(0.6, TOP.dot, 0.6), V(s * (PAVING + 0.6), TOP.dot / 2, z + 4.75), color))
			end
		end
		x0, x1 = X(CURB - 0.5, CURB + 0.5)
		table.insert(out, Box(x0, x1, 0, 0.45, -HALF + 0.5, HALF - 0.5, C.graphiteDark))
		x0, x1 = X(CURB - 0.55, CURB + 0.55)
		table.insert(out, Box(x0, x1, 0.4, 0.55, -HALF + 0.4, HALF - 0.4, C.gold, DECOR))
	end

	-- Дорожка от входа к площадке: бирюза, золотая кромка (до графитового кольца), ромбы и неоновые точки.
	local ring = center.Y - outer
	table.insert(out, Box(-RUNNER, RUNNER, 0, TOP.inlay, -HALF + 0.2, ring + 1, C.tealDeep, DECOR))
	for _, s in { -1, 1 } do
		-- кромка начинается за полосой границы зон (её полуширина 0.5, верх тот же): верх не в одной плоскости
		table.insert(out, Box(s * RUNNER - 0.4, s * RUNNER + 0.4, 0, TOP.porch, -HALF + 0.6, ring - 0.2, C.gold, DECOR))
		for k = 0, 2 do
			local at = V(s * (RUNNER - 1.1), TOP.dot / 2, -HALF + 3.5 + k * 5.5)
			table.insert(out, Neon(V(0.5, TOP.dot, 0.5), at, C.goldLight))
		end
	end
	for k = 0, 2 do
		local at = CFrame.new(0, TOP.pattern / 2, -HALF + 4 + k * 5.5) * CFrame.Angles(0, math.rad(45), 0)
		table.insert(out, B(V(3.2, TOP.pattern, 3.2), at, if k % 2 == 0 then C.gold else C.orange, DECOR))
	end

	-- Площадка торговца (D72: один основной цвет и одна кайма): бирюзовое кольцо, золотой обод, бирюзовое поле.
	local function disc(diameter: number, top: number, color: Color3): Brick
		return Disc(diameter, 0, top, center.X, center.Y, color)
	end
	table.insert(out, disc(outer * 2, TOP.porch, C.tealDeep))
	table.insert(out, disc((arena.radius + 1.4) * 2, TOP.pattern, C.gold))
	table.insert(out, disc(arena.radius * 2, arena.top, C.tealMid))
	-- Места предметов (D71): светящееся кольцо цвета редкости предмета (красит BossLootService) в латунном ободе;
	-- без света снизу — у «Барахолки» бюджет света 10 уже занят.
	for slot, spot in MapLayout.ArtSlots do
		local at = CFrame.new(spot.X, arena.top, spot.Y)
		for _, brick in SlotGlow.Ring(2, slot, at, 3.0, 3.5, C.tealMid, { light = false }) do
			table.insert(out, brick)
		end
		for _, brick in SlotGlow.Rim(at, 3.5, 3.85, C.goldDark, 0.16) do
			table.insert(out, brick)
		end
	end
	-- Путь к следующему уровню (запрос владельца 2026-11-14: от каждого босса к следующему — видимый путь): от
	-- графитового кольца за боссом — перемычка перед горой сокровищ, от неё две дорожки по бокам горы (между горой и
	-- часами / стопкой монет) до выхода. Бирюза на высоте площадок (porch), золотая кромка (pattern), ромбы (dot) —
	-- как дорожка от входа; стыки — встык, верх кромок не накладывается (D36).
	local back = center.Y + outer -- задний край графитового кольца
	local cross = { z0 = back + 2, z1 = back + 6 } -- перемычка
	local function edge(x0: number, x1: number, z0: number, z1: number)
		table.insert(out, Box(x0, x1, 0, TOP.pattern, z0, z1, C.gold, DECOR))
	end
	table.insert(out, Box(-EXIT.spine, EXIT.spine, 0, TOP.porch, back + 0.1, cross.z0, C.tealDeep, DECOR))
	table.insert(out, Box(-EXIT.inner, EXIT.inner, 0, TOP.porch, cross.z0, cross.z1, C.tealDeep, DECOR))
	edge(-EXIT.inner + 0.4, EXIT.inner - 0.4, cross.z1, cross.z1 + 0.4) -- за перемычкой (у горы)
	for _, s in { -1, 1 } do
		local function X(a: number, b: number): (number, number)
			return math.min(s * a, s * b), math.max(s * a, s * b)
		end
		local x0, x1 = X(EXIT.inner, EXIT.outer)
		table.insert(out, Box(x0, x1, 0, TOP.porch, cross.z0, HALF - 0.6, C.tealDeep, DECOR))
		x0, x1 = X(EXIT.outer, EXIT.outer + 0.4)
		edge(x0, x1, cross.z0 - 0.4, HALF - 0.6) -- внешняя кромка дорожки
		x0, x1 = X(EXIT.inner - 0.4, EXIT.inner)
		edge(x0, x1, cross.z1, HALF - 0.6) -- внутренняя (у горы)
		x0, x1 = X(EXIT.spine, EXIT.outer)
		edge(x0, x1, cross.z0 - 0.4, cross.z0) -- перед перемычкой
		x0, x1 = X(EXIT.spine, EXIT.spine + 0.4)
		edge(x0, x1, back + 0.3, cross.z0 - 0.4) -- у перехода от кольца
		-- указатель к следующему уровню у начала дорожки — снаружи от неё (табличка лицом к площадке)
		local sx = s * (EXIT.outer + 2.7)
		table.insert(out, Box(sx - 0.2, sx + 0.2, 0, 3.7, cross.z0 - 0.2, cross.z0 + 0.2, C.graphiteDark))
		table.insert(
			out,
			FleaKit.Board(V(4.2, 1.2, 0.3), V(sx, 3.3, cross.z0 - 0.35), C.orange, FleaKit.Label("К ПОДЗЕМКЕ"))
		)
		-- ромбы по дорожке — к выходу
		for k, z in { cross.z1 + 5, cross.z1 + 11, cross.z1 + 17 } do
			local at = CFrame.new(s * (EXIT.inner + EXIT.outer) / 2, TOP.dot / 2, z) * CFrame.Angles(0, math.rad(45), 0)
			table.insert(out, B(V(2, TOP.dot, 2), at, if k % 2 == 1 then C.gold else C.orange, DECOR))
		end
	end
	-- Сквозные полосы (D66, MapLayout.Lane |x| 48–66) — дорожки к следующей зоне вдоль павильонов: бирюза 52–62 на
	-- высоте вставок, золотые кромки (начинаются дальше от границ зоны, чем бирюза), шесть ромбов на сторону.
	for _, s in { -1, 1 } do
		local function X(a: number, b: number): (number, number)
			return math.min(s * a, s * b), math.max(s * a, s * b)
		end
		local x0, x1 = X(52, 62)
		table.insert(out, Box(x0, x1, 0, TOP.inlay, -HALF + 0.2, HALF - 0.2, C.tealDeep, DECOR))
		for _, e in { { 51.6, 52 }, { 62, 62.4 } } do
			x0, x1 = X(e[1], e[2])
			table.insert(out, Box(x0, x1, 0, TOP.porch, -HALF + 0.6, HALF - 0.6, C.gold, DECOR))
		end
		for k, z in { -40, -25, -10, 5, 20, 35 } do
			local at = CFrame.new(s * 57, TOP.pattern / 2, z) * CFrame.Angles(0, math.rad(45), 0)
			table.insert(out, B(V(3.2, TOP.pattern, 3.2), at, if k % 2 == 1 then C.gold else C.orange, DECOR))
		end
	end
	return out
end

-- Весь декор барахолки в координатах зоны и надписи вывесок.
function FleaMarket.Zone(): ({ Brick }, { Sign })
	FleaKit.Reset()
	local out = FleaMarket.Ground()
	-- Лицом к середине коридора: слева (x < 0) лицо −Z смотрит в +X, справа — в −X. Слева +X вещи — к выходу,
	-- справа — ко входу.
	local function left(z: number, x: number, turn: number?): CFrame
		return CFrame.new(-x, 0, z) * CFrame.Angles(0, -math.pi / 2 + (turn or 0), 0)
	end
	local function right(z: number, x: number, turn: number?): CFrame
		return CFrame.new(x, 0, z) * CFrame.Angles(0, math.pi / 2 + (turn or 0), 0)
	end

	-- Павильоны у стен обрыва, за сквозными полосами (передний край — |x| 63.7–66.4, у каждого свой: задом к стене):
	-- слева пагода, ломбард, шатёр; справа контейнеры, купол, призы (просветы в разных местах).
	Put(out, FleaStalls.Vault(), left(7, 65.8))
	Put(out, FleaStalls.Containers(), right(-31, 64.5))
	Put(out, FleaStalls.Rotunda(), right(-6, 66.4))

	-- Площадки перед павильонами на променаде: у каждого свой узор (полосы, кант, клетка, «осторожно»).
	local function porch(side: number, z: number, width: number, base: Color3, accent: Color3, kind: string)
		local x0, x1 = math.min(side * 33, side * 40.9), math.max(side * 33, side * 40.9)
		local z0, z1 = z - width / 2, z + width / 2
		table.insert(out, Box(x0, x1, 0, TOP.porch, z0, z1, base, DECOR))
		if kind == "stripes" then
			local count = math.floor(width / 4)
			for i = 0, count - 1, 2 do
				local a = z0 + i * width / count
				table.insert(
					out,
					Box(x0 + 0.4, x1 - 0.6, 0, TOP.pattern, a + 0.3, a + width / count - 0.3, accent, DECOR)
				)
			end
		elseif kind == "frame" then
			table.insert(out, Box(x0 + 0.5, x1 - 0.5, 0, TOP.pattern, z0 + 0.5, z0 + 1.1, accent, DECOR))
			table.insert(out, Box(x0 + 0.5, x1 - 0.5, 0, TOP.pattern, z1 - 1.1, z1 - 0.5, accent, DECOR))
			local mid = (x0 + x1) / 2
			local rhomb = CFrame.new(mid, TOP.pattern / 2, z) * CFrame.Angles(0, math.rad(45), 0)
			table.insert(out, B(V(4.2, TOP.pattern, 4.2), rhomb, accent, DECOR))
		else -- клетка
			for i = 0, math.floor(width / 3.4) - 1 do
				local a = z0 + 0.6 + i * 3.4
				local offset = if i % 2 == 0 then 0.6 else 4.1
				table.insert(out, Box(x0 + offset, x0 + offset + 2.8, 0, TOP.pattern, a, a + 2.8, accent, DECOR))
			end
		end
	end
	porch(-1, 7, 20, C.graphiteDark, C.gold, "check")
	porch(1, -31, 22, C.graphiteDark, C.gold, "stripes")
	porch(1, -6, 20, C.purpleDark, C.goldLight, "frame")

	-- Крупные вывески трёх павильонов у дорожки (между бордюром и полосой, в полосе фасада своего павильона).
	Put(out, FleaStalls.StreetSign("ЛОМБАРД", 12, 2.4, C.graphiteDark, 10.6), left(2, STREET))
	Put(out, FleaStalls.StreetSign("СКУПКА", 12, 3, C.graphiteDark, 13, C.orange), right(-32, STREET))
	Put(out, FleaStalls.StreetSign("РЕДКОСТИ", 12, 2.4, C.orange, 11.4), right(-6, STREET))

	-- За боссом — гора золотых монет вдвое меньше прежней горы сокровищ и одним цветом (D72): четыре яруса-диска
	-- (каждый следующий меньше и выше), сверху закрытый сундук. Без столкновений, без света.
	for i, tier in { { 16, 1.0 }, { 12, 2.2 }, { 8, 3.4 }, { 4.4, 4.4 } } do
		table.insert(out, Disc(tier[1], 0, tier[2], HOARD.X, HOARD.Y, if i % 2 == 1 then C.gold else C.goldDark))
	end
	local chest = CFrame.new(HOARD.X, 4.4, HOARD.Y) * CFrame.Angles(0, math.rad(12), 0)
	table.insert(out, B(V(3.6, 2, 2.4), chest * CFrame.new(0, 1, 0), C.goldDark, DECOR))
	table.insert(out, B(V(3.8, 0.7, 2.6), chest * CFrame.new(0, 2.25, 0), C.gold, DECOR))

	-- Задник (D72): ровная графитовая стена одного цвета у конца зоны — закрывает шум следующей зоны; открыты только
	-- проходы — дорожки к выходу (|x| 16.5–20.5) и сквозные полосы (|x| 48–66).
	for _, seg in { { -15.6, 15.6 }, { 21.4, 47.4 }, { 66.6, 91.6 }, { -47.4, -21.4 }, { -91.6, -66.6 } } do
		table.insert(out, Box(seg[1], seg[2], 0, 14, HALF - 1.2, HALF - 0.3, C.graphiteDark))
	end
	return out, FleaKit.Signs()
end

return FleaMarket

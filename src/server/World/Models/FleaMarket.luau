-- Уровень 2 «Барахолка» (D43, редизайн D44): безумный рынок сокровищ. Проход мощён крупными плитами тёплого камня
-- со сдвигом рядов (без шахматки), от входа к боссу ведёт бирюзовая дорожка с золотой кромкой и ромбами, вдоль
-- павильонов — графитовые променады с золотыми вставками и неоновыми точками, бордюры с золотым кантом. В центре —
-- площадка босса в виде огромной монеты: графитовое кольцо с огоньками, золотой обод с насечкой, бирюзовое поле
-- (на нём 4 предмета, MapLayout.Arenas), пунктирное золотое кольцо и ромб-самоцвет под боссом. За боссом — гора
-- сокровищ с огромным сундуком (фон: торговец — хозяин рынка), по бокам от неё гигантские карманные часы и стопка
-- монет, перед ними башни-прожекторы на босса. По краям — шесть разных павильонов (World/Models/FleaStalls), слева и
-- справа разные и в разном порядке, перед каждым своя площадка; в просветах — мачты с ценником и монетой, рекламные
-- щиты на обрывах, сундуки и мешки; за павильонами — штабеля контейнеров; у входа — тележки с зонтами; фонари,
-- столбы с вывесками редкостей и гирлянды флажков вдоль променадов. Проход (|x| < 41) свободен для бега; в круге,
-- куда босс заходит в бою (r 34, scripts/lune/check_world.luau), — только пол не выше 2 стадов, высокое — дальше.
-- Арок и ворот нет (D41). Света мало (по одному на павильон, сундук, 2 прожектора), частиц нет — для телефонов. Координаты зоны: x — поперёк коридора
-- (±92, обрывы за краем), z — вдоль (вход −47.5, выход +47.5), y = 0 — пол. Надписи вывесок возвращаются списком
-- (их пишет WorldBuilder через World/Signs).
-- Зависит от MapLayout, World/Models/FleaKit, World/Models/FleaStalls.

local ServerScriptService = game:GetService("ServerScriptService")

local World = ServerScriptService.Server.World
local MapLayout = require(World.MapLayout)
local FleaKit = require(World.Models.FleaKit)
local FleaStalls = require(World.Models.FleaStalls)

type Brick = FleaKit.Brick
export type Sign = FleaKit.Sign

local B, V, C = FleaKit.B, FleaKit.V, FleaKit.C
local Box, Disc, Neon, Put = FleaKit.Box, FleaKit.Disc, FleaKit.Neon, FleaKit.Put
local DECOR = FleaKit.DECOR

local HALF = MapLayout.ZoneSize / 2 -- вход −HALF, выход +HALF
local PAVING = 30 -- мощение |x| < 30
local CURB = 41.5 -- бордюр (середина), между ним и мощением — променад
local FRONT = 43 -- передний край павильонов (|x|)
local RUNNER = 7 -- полуширина дорожки от входа к площадке
local WALL = 91.4 -- щиты на обрыве (|x|), обрыв — с 92
local SLAB = V(12, 0, HALF * 2 / 16) -- плита мощения: 12 поперёк, 16 рядов вдоль
local SEAM = 0.5
local HOARD = Vector2.new(0, 36.4) -- гора сокровищ за боссом (крышка сундука — у конца зоны)
local HOARD_RADIUS = 6.5 -- холм нижнего яруса (их три в ряд)

local FleaMarket = {}

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
		local inArena, inHoard = true, true
		for _, corner in corners do
			inArena = inArena and (corner - center).Magnitude < outer
			local hill = Vector2.new(math.clamp(corner.X, HOARD.X - 9, HOARD.X + 9), HOARD.Y)
			inHoard = inHoard and (corner - hill).Magnitude < HOARD_RADIUS
		end
		local onRunner = x0 >= -RUNNER and x1 <= RUNNER and z1 <= center.Y - outer + 1
		return inArena or inHoard or onRunner
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
		table.insert(out, Box(s * RUNNER - 0.4, s * RUNNER + 0.4, 0, TOP.porch, -HALF + 0.3, ring - 0.2, C.gold, DECOR))
		for k = 0, 2 do
			local at = V(s * (RUNNER - 1.1), TOP.dot / 2, -HALF + 3.5 + k * 5.5)
			table.insert(out, Neon(V(0.5, TOP.dot, 0.5), at, C.goldLight))
		end
	end
	for k = 0, 2 do
		local at = CFrame.new(0, TOP.pattern / 2, -HALF + 4 + k * 5.5) * CFrame.Angles(0, math.rad(45), 0)
		table.insert(out, B(V(3.2, TOP.pattern, 3.2), at, if k % 2 == 0 then C.gold else C.orange, DECOR))
	end

	-- Площадка-монета: кольцо, обод, поле (на нём предметы).
	local function disc(diameter: number, top: number, color: Color3): Brick
		return Disc(diameter, 0, top, center.X, center.Y, color)
	end
	table.insert(out, disc(outer * 2, TOP.porch, C.graphiteDark))
	table.insert(out, disc((arena.radius + 1.4) * 2, TOP.pattern, C.goldDark))
	table.insert(out, disc(arena.radius * 2, arena.top, C.tealMid))
	-- Насечка обода: золотые зубцы по кругу.
	local function around(angle: number, radius: number, top: number): CFrame
		return CFrame.new(center.X, top / 2, center.Y) * CFrame.Angles(0, angle, 0) * CFrame.new(0, 0, radius)
	end
	for k = 0, 31 do
		local at = around(math.rad(k * 360 / 32), arena.radius + 0.7, TOP.teeth)
		table.insert(out, B(V(1.6, TOP.teeth, 1.1), at, if k % 2 == 0 then C.gold else C.goldLight, DECOR))
	end
	-- Огоньки по графитовому кольцу.
	for k = 0, 7 do
		table.insert(
			out,
			Neon(V(0.9, TOP.dot, 0.9), around(math.rad(22.5 + k * 45), outer - 0.8, TOP.dot), C.purpleLight)
		)
	end
	-- Пунктир между предметами и ободом.
	for k = 0, 23 do
		local at = around(math.rad(7.5 + k * 15), arena.radius - 2, TOP.dash)
		table.insert(out, B(V(3.4, TOP.dash, 0.5), at, C.goldLight, DECOR))
	end
	-- Ромб-самоцвет под боссом: золотой, фиолетовый, светлый, золотой центр.
	local rhomb = CFrame.new(center.X, 0, center.Y) * CFrame.Angles(0, math.rad(45), 0)
	for i, layer in { { 11.6, C.gold }, { 10.2, C.purple }, { 5.6, C.purpleLight } } do
		local top = TOP.dash + (i - 1) * 0.05
		table.insert(out, B(V(layer[1], top, layer[1]), rhomb * CFrame.new(0, top / 2, 0), layer[2], DECOR))
	end
	table.insert(out, Disc(2.6, 0, TOP.dash + 0.15, center.X, center.Y, C.goldLight))
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
	local function facing(x: number, z: number, target: Vector2): CFrame
		return CFrame.lookAt(V(x, 0, z), V(target.X, 0, target.Y))
	end

	-- Павильоны: слева пагода, ломбард, шатёр; справа контейнеры, купол, призы (просветы в разных местах).
	Put(out, FleaStalls.Pagoda(), left(-30, FRONT))
	Put(out, FleaStalls.Vault(), left(7, FRONT))
	Put(out, FleaStalls.Tent(), left(32, FRONT))
	Put(out, FleaStalls.Containers(), right(-31, FRONT))
	Put(out, FleaStalls.Rotunda(), right(-6, FRONT))
	Put(out, FleaStalls.PrizeMachine(), right(32, FRONT))

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
					Box(x0 + 0.4, x1 - 0.4, 0, TOP.pattern, a + 0.3, a + width / count - 0.3, accent, DECOR)
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
	porch(-1, -30, 22, C.tealDeep, C.gold, "frame")
	porch(-1, 7, 20, C.graphiteDark, C.gold, "check")
	porch(-1, 32, 20, C.orangeDark, C.cream, "stripes")
	porch(1, -31, 22, C.graphiteDark, C.gold, "stripes")
	porch(1, -6, 20, C.purpleDark, C.goldLight, "frame")
	porch(1, 32, 20, C.purpleDark, C.teal, "check")

	-- Просвет слева (между пагодой и ломбардом): мачта с ценником, сундук, мешки; щит на обрыве.
	Put(out, FleaStalls.SymbolMast("−50%"), left(-11, 50))
	Put(out, FleaKit.GoldChest(), left(-13.4, 46, 0.35))
	Put(out, FleaKit.CoinSacks(), left(-8.6, 47, -0.3))
	Put(out, FleaStalls.Billboard("БАРАХОЛКА", C.orange), left(-11, WALL))
	-- Просвет справа (между куполом и призами): мачта с монетой, ящики, сундук; щит на обрыве.
	Put(out, FleaStalls.SymbolMast(), right(13, 51))
	Put(out, FleaKit.NeonCrates(), right(16.4, 47, 0.3))
	Put(out, FleaKit.GoldChest(), right(9.6, 46, -0.4))
	Put(out, FleaStalls.Billboard("ЗОЛОТО И ТРОФЕИ", C.purple), right(13, WALL))
	-- За павильонами — штабеля контейнеров (склад рынка у обрывов).
	Put(out, FleaStalls.ContainerStack({ C.teal, C.orange }, 0.3), left(-34, 80))
	Put(out, FleaStalls.ContainerStack({ C.purple, C.teal, C.orange }, -0.25), left(30, 78))
	Put(out, FleaStalls.ContainerStack({ C.orange, C.purple }, -0.35), right(-28, 77))
	Put(out, FleaStalls.ContainerStack({ C.teal, C.orange, C.purple }, 0.2), right(34, 78))

	-- Входная площадь: тележки с зонтами по бокам от дорожки, лицом к ней.
	Put(out, FleaStalls.UmbrellaCart(C.orange, C.cream), facing(-20, -41, Vector2.new(0, -41)))
	Put(out, FleaStalls.UmbrellaCart(C.purple, C.goldLight), facing(22, -40, Vector2.new(0, -40)))

	-- Фонари у бордюров (слева тёплые, справа холодные), столбы с вывесками редкостей справа и гирлянды флажков
	-- между ними вдоль променадов (поперёк коридора ничего нет).
	local westLamps = { -45.5, -16, 20, 45 }
	for _, z in westLamps do
		Put(out, FleaKit.Lamp(C.orangeLight), left(z, CURB - 1.8))
	end
	for _, z in { -45.5, 45 } do
		Put(out, FleaKit.Lamp(C.tealLight), right(z, CURB - 1.8))
	end
	local poles = { -18, 6.5, 20 }
	for i, rarity in { "Common", "Rare", "Epic" } do
		Put(out, FleaKit.RarityPole(rarity), right(poles[i], CURB - 1.8))
	end
	local function bunting(side: number, z0: number, z1: number, colors: { Color3 })
		local at = CFrame.new(side * (CURB - 1.8), 0, z0) * CFrame.Angles(0, -math.pi / 2, 0)
		Put(out, FleaStalls.Bunting(z1 - z0, 10.1, 1.6, 2.4, colors), at)
	end
	local warm = { C.orange, C.goldLight, C.teal }
	bunting(-1, -16, 20, warm) -- у пагоды гирлянды нет: там подвесная вывеска
	bunting(-1, 20, 45, warm)
	local cold = { C.purpleLight, C.teal, C.goldLight }
	local east = { -45.5, poles[1], poles[2], poles[3], 45 }
	for i = 1, #east - 1 do
		bunting(1, east[i], east[i + 1], cold)
	end

	-- За боссом: гора сокровищ, по бокам гигантские часы и стопка монет, перед ними башни-прожекторы на босса.
	Put(out, FleaStalls.TreasureHoard(), CFrame.new(HOARD.X, 0, HOARD.Y))
	local boss = MapLayout.BossSpot
	Put(out, FleaStalls.PocketWatch(), facing(-25, 38, boss))
	Put(out, FleaStalls.CoinStack(), facing(25, 37, boss))
	local target = V(boss.X, 7, boss.Y)
	for _, tower in { { -28, 22, C.orange }, { 28, 22, C.purple } } do
		local at = V(tower[1], 0, tower[2])
		Put(out, FleaStalls.LightTower(target - at, tower[3]), CFrame.new(at))
	end
	return out, FleaKit.Signs()
end

return FleaMarket

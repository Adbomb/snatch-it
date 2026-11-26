-- Уровень 1 «Свалка» (D41, D68, D72 «Спокойные уровни»): круглая площадка пса «свалочная монета»
-- (MapLayout.Arenas[1], предметы прямо на ней) — кольцо из покрышек, ржаво-оранжевый обод, рифлёное железо с
-- жёлто-чёрной разметкой, люк-«миска» с косточкой; пол — грязь: пятна двух тонов, лужи, колеи с протектором, масло,
-- дорога из бетонных плит обходит площадку (пол D72 не меняет); вокруг — несколько крупных ориентиров: кран с машиной
-- у стены, стопка из трёх машин, гора покрышек, будка пса, пара жёлтых бочек; края — земляные откосы одного цвета до
-- кромки обрыва. Круг боя пса (r 34 от (0, −5)) — ниже 2; боковые полосы |x| 48–66 (D66) без твёрдого на высоте
-- 1.1–7; места обучения D55 (у x −46…−48) не застраиваются. Координаты зоны: x — поперёк коридора (±92), z — вдоль
-- (вход −47.5, выход +47.5), y = 0 — пол; +x — слева от входящего игрока. Надписи — списком
-- (FleaKit.Label), их пишет WorldBuilder. Зависит от MapLayout, ModelBuilder, Palette, JunkKit, FleaKit, SlotGlow.

local ServerScriptService = game:GetService("ServerScriptService")

local World = ServerScriptService.Server.World
local MapLayout = require(World.MapLayout)
local SlotGlow = require(World.SlotGlow)
local ModelBuilder = require(World.ModelBuilder)
local Palette = require(World.Palette)
local JunkKit = require(World.Models.JunkKit)
local FleaKit = require(World.Models.FleaKit)

type Brick = ModelBuilder.Brick
export type Sign = FleaKit.Sign

local B = JunkKit.B
local DECOR, ROUND, BALL, UPRIGHT = JunkKit.DECOR, JunkKit.ROUND, JunkKit.BALL, JunkKit.UPRIGHT
local C, hex, put = JunkKit.C, JunkKit.hex, JunkKit.put
local LANE = MapLayout.Lane -- боковые полосы свободного бега (|x|): твёрдого на высоте 1.1–7 нет
local LANE_AXIS = (LANE[1] + LANE[2]) / 2 -- ось полосы: дорожка из плит

local Junkyard = {}

-- Площадка пса (D68): диски снизу вверх (диаметр, верх; каждый следующий выше на ≥ 0.05 — грани не совпадают),
-- верх поля — Arenas[1].top, на нём стоят предметы.
local ARENA = MapLayout.Arenas[1]
local SPOT = MapLayout.BossSpot
local DISCS = {
	{ ARENA.radius * 2 + 6, 0.2, hex("2B2B33") }, -- кольцо из покрышек
	{ ARENA.radius * 2 + 2.8, 0.25, C.rustOrange }, -- ржаво-оранжевый обод
	{ ARENA.radius * 2, ARENA.top, hex("6F6A66") }, -- поле: тёмное рифлёное железо (пёс и предметы читаются)
}

function Junkyard.Arena(): { Brick }
	local out = {}
	local cx, cz = SPOT.X, SPOT.Y
	for _, d in DISCS do
		table.insert(
			out,
			B(Vector3.new(d[2] + 0.05, d[1], d[1]), CFrame.new(cx, (d[2] - 0.05) / 2, cz) * UPRIGHT, d[3], {
				shape = "Cylinder",
			})
		)
	end
	local r0 = ARENA.radius
	-- протектор на кольце покрышек: 32 тёмные плашки поперёк кольца (верх 0.25 — над кольцом 0.2)
	for k = 0, 31 do
		local a = math.rad(k * 360 / 32)
		local at = CFrame.new(cx + math.sin(a) * (r0 + 2.25), 0.125, cz + math.cos(a) * (r0 + 2.25))
			* CFrame.Angles(0, a, 0)
		table.insert(out, B(Vector3.new(1.6, 0.25, 0.7), at, hex("1C1C22"), DECOR))
	end
	-- заклёпки на ободе: 24 шарика
	for k = 0, 23 do
		local a = math.rad(k * 15 + 7.5)
		local p = Vector3.new(cx + math.sin(a) * (r0 + 0.7), 0.25, cz + math.cos(a) * (r0 + 0.7))
		table.insert(out, B(Vector3.new(0.4, 0.4, 0.4), p, hex("8A4A22"), BALL))
	end
	-- жёлто-чёрная разметка по краю поля: 36 плашек через одну (верх 0.35)
	for k = 0, 35 do
		local a = math.rad(k * 10 + 5)
		local at = CFrame.new(cx + math.sin(a) * (r0 - 1.6), 0.325, cz + math.cos(a) * (r0 - 1.6))
			* CFrame.Angles(0, a, 0)
		table.insert(out, B(Vector3.new(3.4, 0.05, 1.2), at, if k % 2 == 0 then C.yellow else hex("23232A"), DECOR))
	end
	-- жёлтые ромбики по кругу r 15 (верх 0.36) — в цвет разметки; у мест предметов их нет (кольца D71)
	for k = 0, 15 do
		local a = math.rad(k * 22.5)
		local p = Vector2.new(cx + math.sin(a) * 15, cz + math.cos(a) * 15)
		local underSlot = false -- под кольцом места предмета (D71) ромбика нет
		for _, spot in MapLayout.ArtSlots do
			underSlot = underSlot or (p - spot).Magnitude < 4.5
		end
		if underSlot then
			continue
		end
		local at = CFrame.new(p.X, 0.33, p.Y) * CFrame.Angles(0, a + 0.785, 0)
		table.insert(out, B(Vector3.new(1.1, 0.06, 1.1), at, C.yellow, DECOR))
	end
	-- люк-«миска» под псом: тёмное кольцо, красная миска, косточка-эмблема
	local bowl = {
		{ 12.4, 0.36, hex("3A3F4A") },
		{ 10.6, 0.41, C.bowl },
		{ 8.0, 0.46, hex("B32D26") },
	}
	for _, d in bowl do
		table.insert(out, B(Vector3.new(0.12, d[1], d[1]), CFrame.new(cx, d[2] - 0.06, cz) * UPRIGHT, d[3], ROUND))
	end
	-- места предметов (D71): светящееся кольцо цвета редкости предмета (красит BossLootService) в ржавом ободе; пустое
	-- место — тёмное железо. Без света снизу: неон и так ярче пёстрого пола.
	for slot, spot in MapLayout.ArtSlots do
		local at = CFrame.new(spot.X, ARENA.top, spot.Y)
		for _, brick in SlotGlow.Ring(1, slot, at, 3.0, 3.5, hex("4A4542"), { light = false, height = 0.14 }) do
			table.insert(out, brick)
		end
		for _, brick in SlotGlow.Rim(at, 3.5, 3.85, C.rust, 0.16) do
			table.insert(out, brick)
		end
	end
	local bone = CFrame.new(cx, 0.48, cz) * CFrame.Angles(0, math.rad(30), 0)
	table.insert(out, B(Vector3.new(4.2, 0.1, 0.9), bone, C.bone, DECOR))
	for _, s in { -1, 1 } do
		for _, z in { -0.45, 0.45 } do
			local dy = if z > 0 then 0.04 else 0.01 -- соседние шарики косточки — разной высоты (торцы не совпадают)
			table.insert(
				out,
				B(Vector3.new(0.12, 1.2, 1.2), bone * CFrame.new(s * 2.1, dy, z) * UPRIGHT, C.bone, ROUND)
			)
		end
	end
	return out
end

-- Пол свалки поверх пола зоны: дорога из плит (обходит площадку), дорожки полос, пятна грязи двух тонов, лужи,
-- колеи с протектором, масляные пятна, железные листы, поддоны, мелкий мусор и трава. Плоские слои — с разной
-- высотой верха (≥ 0.05): нет совпадающих граней.
local GROUND = {
	slab = { hex("A8A29A"), hex("9C968D"), hex("B4AEA5") },
	dirt = { hex("6E5A44"), hex("5D4B39"), hex("7C6750") },
	track = hex("4F4235"),
	oil = hex("2B2620"),
}

-- Колеи от машин (ломаные): по ним рисуется след шин (пол, D72 его не меняет).
local TRACKS = {
	{ Vector2.new(-44, -30), Vector2.new(-34, -36), Vector2.new(-22, -40), Vector2.new(-10, -46) },
	{ Vector2.new(44, 12), Vector2.new(34, 16), Vector2.new(24, 22), Vector2.new(12, 26), Vector2.new(8, 32) },
	{ Vector2.new(-44, 4), Vector2.new(-36, 20), Vector2.new(-30, 30), Vector2.new(-28, 44) },
}

function Junkyard.Ground(): { Brick }
	local out = {}
	local random = Random.new(41)
	-- Дорога: две колонны бетонных плит 5×7 с зазорами; каждая чуть повёрнута, часть треснула, кое-где плиты нет;
	-- под площадкой и её кольцом плит нет.
	for row = 0, 11 do
		local z = -41.8 + row * 7.6
		for col, x in { -2.7, 2.7 } do
			local n = row * 2 + col
			local near = (Vector2.new(x, z) - SPOT).Magnitude < ARENA.radius + 7.5
			if n % 7 ~= 3 and not near then
				local tone = GROUND.slab[n % 3 + 1]
				local top = 0.2 + ((row + col) % 3) * 0.06
				local turn = (if n % 2 == 0 then 1 else -1) * random:NextNumber(0.008, 0.025)
				local base = CFrame.new(x + random:NextNumber(-0.08, 0.08), 0, z) * CFrame.Angles(0, turn, 0)
				if n % 5 == 2 then
					table.insert(out, B(Vector3.new(5, top, 3.35), base * CFrame.new(0, top / 2, -1.82), tone, DECOR))
					local half = base * CFrame.new(0.1, (top - 0.08) / 2, 1.85) * CFrame.Angles(0, 0.05, 0)
					table.insert(out, B(Vector3.new(4.9, top - 0.08, 3.3), half, tone:Lerp(Palette.Black, 0.06), DECOR))
				else
					table.insert(out, B(Vector3.new(5, top, 7), base * CFrame.new(0, top / 2, 0), tone, DECOR))
				end
			end
		end
	end
	-- Дорожка по оси каждой боковой полосы (x ±LANE_AXIS): колонна плит 5×7, одной плиты нет.
	for _, s in { -1, 1 } do
		for row = 0, 11 do
			if row % 7 ~= 5 then
				local z = -41.8 + row * 7.6
				local top = 0.23 + (row % 3) * 0.06
				local turn = (if row % 2 == 0 then 1 else -1) * 0.015
				local at = CFrame.new(s * LANE_AXIS, top / 2, z) * CFrame.Angles(0, turn, 0)
				table.insert(out, B(Vector3.new(5, top, 7), at, GROUND.slab[row % 3 + 1], DECOR))
			end
		end
	end
	-- Пятно грязи неровной формы: count кругов разного размера, сдвинутых в разные стороны, ближе к центру выше.
	local function blob(x: number, z: number, radius: number, turn: number, count: number, color: Color3)
		for i = 1, count do
			local angle = turn + i * 2.4
			local dist = radius * 0.55 * (1 - (i - 1) / count)
			local r = radius * (0.5 + 0.3 * ((i * 0.37) % 1))
			local h = 0.02 * i -- верх 0.02 / 0.04: ниже луж (0.06), колей (0.07) и мусора — грани не совпадают
			local at = CFrame.new(x + math.cos(angle) * dist, h / 2, z + math.sin(angle) * dist) * UPRIGHT
			table.insert(out, B(Vector3.new(h, r * 2, r * 2), at, color:Lerp(Palette.Black, (i % 3) * 0.04), ROUND))
		end
	end
	-- Пятна грязи по всему полю (не в полосах и не на площадке): тёмные и светлые, разного размера.
	for i, spot in
		{
			{ -20, -30, 7 },
			{ 26, -32, 6 },
			{ -30, 18, 8 },
			{ 30, 10, 6.5 },
			{ -14, 30, 5.5 },
			{ 14, 34, 6 },
			{ -38, -10, 5 },
			{ 38, -14, 5.5 },
			{ -26, -44, 4.5 },
			{ 28, -44, 4.5 },
			{ 40, 40, 5 },
			{ -40, 26, 4.5 },
		}
	do
		blob(spot[1], spot[2], spot[3], i * 1.1, 2, GROUND.dirt[i % 3 + 1])
	end
	-- Колеи от машин: две полосы по ломаной с ёлочкой протектора (отрезки внахлёст, верх через один выше).
	local function track(points: { Vector2 })
		local k = 0
		for i = 1, #points - 1 do
			local a, b = points[i], points[i + 1]
			local along = (b - a).Unit
			local side = Vector2.new(-along.Y, along.X) * 0.95
			local steps = math.ceil((b - a).Magnitude / 3)
			for s = 0, steps - 1 do
				k += 1
				local mid = a + (b - a) * ((s + 0.5) / steps)
				local h = if k % 2 == 0 then 0.07 else 0.13
				local turn = math.atan2(-along.Y, along.X)
				for _, sign in { -1, 1 } do
					local p = mid + side * sign
					local at = CFrame.new(p.X, h / 2, p.Y) * CFrame.Angles(0, turn, 0)
					table.insert(out, B(Vector3.new((b - a).Magnitude / steps + 0.3, h, 0.7), at, GROUND.track, DECOR))
					-- протектор: светлая косая плашка поверх каждого второго отрезка
					if k % 2 == 1 then
						local chev = at * CFrame.new(0, h / 2 + 0.02, 0) * CFrame.Angles(0, sign * 0.6, 0)
						table.insert(out, B(Vector3.new(0.9, 0.04, 0.22), chev, GROUND.dirt[3], DECOR))
					end
				end
			end
		end
	end
	for _, points in TRACKS do
		track(points)
	end
	-- Масляные пятна: по два круга разной толщины.
	for _, spot in { { -31, 30.5, 1.7 }, { 36.5, 33.5, 1.3 }, { 37.5, -1.8, 1.1 }, { 44, -11, 1.5 }, { 24, -42, 1.2 } } do
		local r = spot[3]
		table.insert(
			out,
			B(Vector3.new(0.26, r * 2, r * 2), CFrame.new(spot[1], 0.13, spot[2]) * UPRIGHT, GROUND.oil, ROUND)
		)
		local small = CFrame.new(spot[1] + r * 0.8, 0.15, spot[2] + r * 0.5) * UPRIGHT
		table.insert(out, B(Vector3.new(0.3, r * 1.1, r * 1.1), small, GROUND.oil:Lerp(Palette.White, 0.06), ROUND))
	end
	return out
end

-- Края зоны (D72 «Спокойные уровни»): простые земляные откосы одного приглушённого цвета до кромки обрыва вместо гор
-- вещей. Отрезками вдоль z (8–11, у соседних разный поворот — край неровный): нижний откос твёрдый (от |x| ≈ 72 до
-- 88.8, высота 13–19, ≤ 24 у стены — по нему можно подняться, за кромку не выпрыгнуть) и верхний круче, без
-- столкновений (верх 34.4 у |x| 91.3 — клетчатая стена обрыва не видна). Место крана (+x, z 18–26) — откос отступает к
-- стене; у столбиков границы (x ±86, z > 45.9) — только верхний откос у самой стены. Полосы |x| 48–66 свободны.
local EARTH = hex("6F5C49") -- откосы: земля, один приглушённый цвет
local EARTH_SOLID = { shape = "Wedge", variant = "LegoSquaresDeep" }
local EARTH_DECOR = { shape = "Wedge", variant = "LegoSquaresDeep", collide = false, shadow = false }

-- Откос-клин: скат к полю (поворот s · 90° плюс сдвиг jitter), передний нижний край на |x| = front, задний верхний —
-- на |x| = back, низ base, верх top; вдоль z — zl с центром zc.
local function slope(
	out: { Brick },
	s: number,
	front: number,
	back: number,
	base: number,
	top: number,
	zc: number,
	zl: number,
	jitter: number,
	extra: { [string]: any }
)
	local at = CFrame.new(s * (front + back) / 2, (base + top) / 2, zc) * CFrame.Angles(0, math.rad(s * 90 + jitter), 0)
	table.insert(out, B(Vector3.new(zl, top - base, back - front), at, EARTH, extra))
end

function Junkyard.WallJunk(): { Brick }
	local out = {}
	for _, s in { -1, 1 } do
		local z, k = -46.9, 0 -- от начала зоны с запасом: повёрнутые откосы не выходят за её край
		while z < 45.9 do
			k += 1
			local len = 8 + (k * 37 % 4)
			local z1 = math.min(z + len, 45.9)
			local zc, zl = (z + z1) / 2, z1 - z
			local crane = s > 0 and zc > 14 and zc < 30
			local front = (if crane then 78 else 72) + (k * 53 % 3)
			local jitter = ((k * 7) % 5 - 2) * 1.7 + 0.8 -- у соседних отрезков разный, ни один не ровно 90°
			local h1 = 13 + (k * 5 % 7)
			slope(out, s, front, 88.8, -0.3, h1, zc, zl, jitter, EARTH_SOLID)
			local upFront = front + (88.8 - front) * 0.45
			slope(out, s, upFront, 91.3, h1 * 0.45 - 0.6, 34.4 + (k % 2) * 0.5, zc, zl - 0.2, -jitter, EARTH_DECOR)
			z = z1
		end
		slope(out, s, 88.4, 91.3, -0.3, 34.6, 46.6, 1.4, 2.1, EARTH_DECOR)
	end
	return out
end

-- Весь декор свалки в координатах зоны и надписи.
function Junkyard.Zone(): ({ Brick }, { Sign })
	FleaKit.Reset()
	local out = Junkyard.Ground()
	for _, brick in Junkyard.Arena() do
		table.insert(out, brick)
	end
	for _, brick in Junkyard.WallJunk() do
		table.insert(out, brick)
	end
	local function at(x: number, z: number, turn: number?): CFrame
		return CFrame.new(x, 0, z) * CFrame.Angles(0, turn or 0, 0)
	end
	-- Ориентиры (D72: вокруг площадки всего несколько крупных узнаваемых объектов): кран с висящей машиной у стены,
	-- стопка из трёх сплющенных машин, гора покрышек, будка пса и пара жёлтых бочек — всё вне круга боя пса.
	put(out, JunkKit.Crane(30), at(70, 22))
	put(out, JunkKit.CarStack(), at(-38, 24, 0.4))
	put(out, JunkKit.TireMountain(), at(36, 20, 0.3))
	put(out, JunkKit.Kennel(), at(-40, -2, -math.pi / 2))
	put(out, JunkKit.Barrel(C.yellow, hex("23232A")), at(40, 1))
	put(out, JunkKit.Barrel(C.yellow, hex("23232A")), at(42.4, 3.2))
	-- Лужи — часть пола (D72 пол не меняет).
	put(out, JunkKit.Puddle(3.4), at(-26, 14, 0.4))
	put(out, JunkKit.Puddle(2.8), at(26, -26, -0.3))
	put(out, JunkKit.Puddle(3.6), at(42, 26, 0.9))
	put(out, JunkKit.Puddle(2.4), at(-20, -32, 1.3))
	put(out, JunkKit.Puddle(3), at(16, 40, 0.2))
	-- Указатель к следующему уровню у выхода, слева от прохода.
	table.insert(out, B(Vector3.new(0.4, 4.4, 0.4), Vector3.new(-10.5, 2.2, 40.2), Palette.WoodDark))
	table.insert(
		out,
		FleaKit.Board(
			Vector3.new(6, 1.4, 0.3),
			Vector3.new(-10.5, 3.9, 39.85),
			C.rustOrange,
			FleaKit.Label("К БАРАХОЛКЕ")
		)
	)
	return out, FleaKit.Signs()
end

return Junkyard

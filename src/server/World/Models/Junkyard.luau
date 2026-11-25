-- Уровень 1 «Свалка» (D41, D68 — первая зона новичка): круглая площадка пса «свалочная монета» (MapLayout.Arenas[1],
-- предметы прямо на ней, без постаментов) — кольцо из покрышек, ржаво-оранжевый обод, рифлёное железо с жёлто-чёрной
-- разметкой, люк-«миска» с косточкой под псом; пол — грязь: пятна двух тонов, лужи, колеи с протектором, масляные
-- пятна, мелкий низкий мусор (≤ 0.6, проход не перекрывает), дорога из бетонных плит обходит площадку; вдоль стен —
-- горы хлама до кромки обрыва вместо гладких клетчатых стен (низ — контейнеры и сплющенные машины, твёрдый ≤ 24;
-- выше — без столкновений, наклонены); яркие акценты — ржаво-оранжевый, жёлтые бочки, красные машины, бирюзовая будка;
-- кран с машиной и сторожка — у стен. Круг боя пса (r 34 от (0, −5)) — ниже 2; боковые полосы |x| 48–66 (D66) без
-- твёрдого на высоте 1.1–7; места обучения D55 (у x −46…−48) не застраиваются. Координаты зоны: x — поперёк коридора
-- (±92), z — вдоль (вход −47.5, выход +47.5), y = 0 — пол; +x — слева от входящего игрока. Надписи — списком
-- (FleaKit.Label), их пишет WorldBuilder. Зависит от MapLayout, ModelBuilder, Palette, Props, JunkKit, FleaKit.

local ServerScriptService = game:GetService("ServerScriptService")

local World = ServerScriptService.Server.World
local MapLayout = require(World.MapLayout)
local SlotGlow = require(World.SlotGlow)
local ModelBuilder = require(World.ModelBuilder)
local Palette = require(World.Palette)
local Props = require(World.Models.Props)
local JunkKit = require(World.Models.JunkKit)
local FleaKit = require(World.Models.FleaKit)

type Brick = ModelBuilder.Brick
export type Sign = FleaKit.Sign

local B = JunkKit.B
local DECOR, ROUND, BALL, UPRIGHT = JunkKit.DECOR, JunkKit.ROUND, JunkKit.BALL, JunkKit.UPRIGHT
local C, SCRAP, hex, put = JunkKit.C, JunkKit.SCRAP, JunkKit.hex, JunkKit.put
local LANE = MapLayout.Lane -- боковые полосы свободного бега (|x|): твёрдого на высоте 1.1–7 нет
local LANE_AXIS = (LANE[1] + LANE[2]) / 2 -- ось полосы: дорожка из плит
local WALL = MapLayout.ZoneHalfWidth -- грань обрыва (|x| = 92): декор до неё не доходит

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

-- Места, где мусора нет: площадка, крупные вещи, лужи, фонари, места обучения (x, z, радиус).
local KEEP_OUT = {
	{ SPOT.X, SPOT.Y, ARENA.radius + 4 },
	{ -46, -36, 5 },
	{ -48, -16, 5 },
	{ -40, -2, 5 }, -- будка
	{ 40, 2, 4 }, -- бочки
	{ 30, 26, 2.5 }, -- шины
	{ -34, 34, 5 }, -- красная машина
	{ 33, 36, 5 }, -- вторая красная машина
	{ 40, -38, 4 }, -- диван
	{ -42, 40, 4.5 }, -- кучка техники
	{ -38, 12, 4.5 },
	{ 22, -36, 3.5 },
	{ -32, 6, 3.5 }, -- железный лист
	{ 42, 26, 4.5 }, -- лужи
	{ -26, 14, 4.5 },
	{ 26, -26, 4 },
	{ -20, -32, 3.5 },
	{ 16, 40, 4 },
	{ -22, -40, 4 },
	{ -17, -42, 1.2 },
	{ 17, -42, 1.2 },
	{ -22, 26, 1.2 },
	{ 22, 30, 1.2 },
	{ 40, -27, 2 },
	{ -10.5, 40, 2 }, -- указатель
}

-- Колеи от машин (ломаные): по ним рисуется след шин, мусор их обходит.
local TRACKS = {
	{ Vector2.new(-44, -30), Vector2.new(-34, -36), Vector2.new(-22, -40), Vector2.new(-10, -46) },
	{ Vector2.new(44, 12), Vector2.new(34, 16), Vector2.new(24, 22), Vector2.new(12, 26), Vector2.new(8, 32) },
	{ Vector2.new(-44, 4), Vector2.new(-36, 20), Vector2.new(-30, 30), Vector2.new(-28, 44) },
}

local function nearTrack(p: Vector2): boolean
	for _, points in TRACKS do
		for i = 1, #points - 1 do
			local a, b = points[i], points[i + 1]
			local t = math.clamp((p - a):Dot(b - a) / (b - a):Dot(b - a), 0, 1)
			if (p - (a + (b - a) * t)).Magnitude < 3 then
				return true
			end
		end
	end
	return false
end

local function isFree(p: Vector2): boolean
	local x = math.abs(p.X)
	-- вне прохода по центру, полос свободного бега (с запасом 1) и гор у стен (|x| > 66)
	if x < 7 or x > LANE[1] - 1 or math.abs(p.Y) > 45 or nearTrack(p) then
		return false
	end
	for _, spot in KEEP_OUT do
		if (p - Vector2.new(spot[1], spot[2])).Magnitude < spot[3] then
			return false
		end
	end
	return true
end

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
	-- Ржавые железные листы с заклёпками (низкие, без столкновений).
	for i, spot in { { -14, -20, 0.35 }, { 16, 22, -0.5 }, { -32, 6, 1.1 } } do
		local at = CFrame.new(spot[1], 0, spot[2]) * CFrame.Angles(0, spot[3], 0)
		local h = 0.14 + i * 0.05
		table.insert(out, B(Vector3.new(4.4, h, 3.2), at * CFrame.new(0, h / 2, 0), SCRAP.sheet[i], DECOR))
		for _, corner in { { -1.9, -1.3 }, { 1.9, -1.3 }, { -1.9, 1.3 }, { 1.9, 1.3 } } do
			table.insert(
				out,
				B(Vector3.new(0.3, 0.3, 0.3), at * CFrame.new(corner[1], h, corner[2]), Palette.Metal, BALL)
			)
		end
	end
	-- Мелкий мусор по полю (≤ 0.6): 50 штук, крупнее прежних.
	local placed, tries = 0, 0
	while placed < 50 and tries < 3000 do
		tries += 1
		local p = Vector2.new(random:NextNumber(-47, 47), random:NextNumber(-45, 45))
		if isFree(p) then
			placed += 1
			local at = CFrame.new(p.X, 0, p.Y) * CFrame.Angles(0, random:NextNumber(0.1, 3.0), 0)
			put(out, JunkKit.Scrap(random:NextInteger(1, 9), random:NextInteger(1, 4)), at)
		end
	end
	-- Поддоны (на втором — ещё один поддон сверху).
	for i, spot in { { -30, -20 }, { 40, -27 }, { 24, 40 } } do
		local at = CFrame.new(spot[1], 0, spot[2]) * CFrame.Angles(0, spot[1] * 0.07, 0)
		put(out, JunkKit.Pallet(), at)
		if i == 2 then
			put(out, JunkKit.Pallet(), at * CFrame.new(0.15, 0.52, -0.1) * CFrame.Angles(0, 0.2, 0))
		end
	end
	-- Сорная трава: у подножия гор хлама (перед ними, |x| 67–68) и по краям дороги.
	local count = 0
	local function weeds(x: number, z: number)
		count += 1
		put(out, JunkKit.Weeds(count), CFrame.new(x, 0, z) * CFrame.Angles(0, count * 0.9, 0))
	end
	for i = 1, 10 do
		weeds((if i % 2 == 0 then 1 else -1) * 66.6, -42 + i * 8.4)
	end
	for _, spot in { { -6.4, -40 }, { 6.6, -36 }, { 6.5, 26 }, { -6.6, 32 }, { 6.3, 42 }, { -6.5, 24 } } do
		weeds(spot[1], spot[2])
	end
	return out
end

-- Горы хлама вдоль стен (|x| 67–92), отрезками вдоль z: низ — контейнер или стопка сплющенных машин (твёрдый, ≤ 24),
-- выше — наклонённые ярусы хлама без столкновений до кромки обрыва (≥ 33.4, закрывают траву 32.7), сверху — шины,
-- бочки, лист железа. У соседних отрезков разные наклоны и цвета. Место крана (+x, z 18–26) и сторожки (−x,
-- z −40…−32) — гора отступает к стене; у столбиков границы (z > 45.9) гор нет.
local HEAP_COLORS = { C.rustOrange, C.red, C.blue, C.yellow, C.teal, C.green, C.rust, C.steel }
-- Ярусы гор — приглушённые цвета старого железа (ржавчина, сталь, выцветшие краски); яркие — только низ и акценты.
local JUNK_TONES = {
	hex("A0522D"),
	hex("7A4A2E"),
	hex("7D8790"),
	hex("525A64"),
	hex("A8443A"),
	hex("3E5F8A"),
	hex("3A7F78"),
	hex("B88A2E"),
}

function Junkyard.WallJunk(): { Brick }
	local out = {}
	for _, s in { -1, 1 } do
		local z, k = -47.4, 0
		while z < 45.9 do
			k += 1
			local len = 8 + (k * 37 % 4)
			local z1 = math.min(z + len, 45.9)
			local zc, zl = (z + z1) / 2, z1 - z
			local blocked = (s > 0 and zc > 14 and zc < 30) or (s < 0 and zc > -44 and zc < -28)
			local inner = (if blocked then 78 else 67.2) + (k * 53 % 3) -- передний край горы (|x|)
			local function color(n: number): Color3
				return HEAP_COLORS[(k * 3 + n) % #HEAP_COLORS + 1]
			end
			-- низ: контейнер вдоль стены или стопка из двух сплющенных машин (твёрдые, верх ≤ 9.5)
			if k % 2 == 0 then
				local at = CFrame.new(s * (inner + 2.4), 0, zc)
					* CFrame.Angles(0, math.rad(90 + s * ((k % 3) * 2 + 3.5)), 0)
				put(out, JunkKit.Container(color(0), math.min(zl - 0.6, 9.6), true), at)
				put(
					out,
					JunkKit.Container(color(1), math.min(zl - 1.4, 8.2), false),
					at * CFrame.new(0.3, 4.65, 0.2) * CFrame.Angles(0, 0.06, 0.04)
				)
			else
				for j = 0, 1 do
					local at = CFrame.new(s * (inner + 2.2 + j * 0.4), j * 1.95, zc + (j - 0.5) * 0.6)
						* CFrame.Angles(0, math.rad(90 + (j * 2 - 1) * 5), math.rad((j * 2 - 1) * 3))
					local car = JunkKit.CrushedCar(color(j))
					if j == 0 then
						car[1].collide = true -- корпус нижней машины — твёрдый
					end
					put(out, car, at)
				end
			end
			-- ярусы хлама к стене: от земли (низ уходит в пол — при наклоне край не висит), наклонены верхом к стене,
			-- у соседних отрезков — разные углы и цвета
			local lean = -s * (5 + (k % 3) * 3)
			local turn = s * ((k % 3) - 1) * 5
			local tiers = {
				{ inner + 4.6, -2, 10 + (k * 11 % 4) },
				{ inner + 9, 8, 20 + (k * 7 % 4) },
				{ inner + 13.6, 17, 34.2 },
			}
			for t, tier in tiers do
				-- ярус — два куска «сплющенных машин» вдоль z: свои наклон, поворот, высота и приглушённый цвет; на
				-- лицевой грани нижних кусков — полоса окон и колесо (читается как машина в стопке)
				for piece = 1, 2 do
					local h = tier[3] - tier[2] - (if piece == 2 then 1.6 else 0)
					local depth = zl / 2 - 0.25 - t * 0.1
					local pl = lean + s * (if piece == 1 then 2 else -2) - s * t * 1.5
					local pt = turn + (piece * 2 - 3) * 3 + t
					-- задний край: с учётом наклона и поворота кусок не доходит до грани обрыва (≤ |x| 91.7)
					local b = WALL
						- 0.3
						- h / 2 * math.abs(math.sin(math.rad(pl)))
						- depth / 2 * math.abs(math.sin(math.rad(pt)))
					local a = math.min(tier[1] + (piece - 1) * 0.8, b - 4)
					local w = b - a
					local at = CFrame.new(s * (a + b) / 2, tier[2] + h / 2, zc + (piece - 1.5) * (zl / 2))
						* CFrame.Angles(0, math.rad(pt), math.rad(pl))
					table.insert(
						out,
						B(Vector3.new(w, h, depth), at, JUNK_TONES[(k * 5 + t * 3 + piece) % #JUNK_TONES + 1], DECOR)
					)
					if t <= 2 then
						local face = -s * (w / 2 + 0.06)
						table.insert(
							out,
							B(
								Vector3.new(0.14, 0.9, depth * 0.7),
								at * CFrame.new(face, h / 2 - 1.5, 0),
								C.screen:Lerp(C.dark, 0.35),
								DECOR
							)
						)
					end
					if t == 1 then
						local wheel = at * CFrame.new(-s * (w / 2 + 0.25), h / 2 - 4, depth * 0.25 * (piece * 2 - 3))
						table.insert(out, B(Vector3.new(0.5, 1.7, 1.7), wheel, C.tire, ROUND))
					end
				end
			end
			-- сверху: шина, бочка или лист железа (без столкновений)
			local topAt = CFrame.new(s * (inner + 6.5), 10.4 + (k * 11 % 4), zc + ((k % 3) - 1) * 1.5)
			if k % 3 == 0 then
				local tires = JunkKit.Tires(2)
				for _, brick in tires do
					brick.collide = false
				end
				put(out, tires, topAt * CFrame.Angles(0.2, 0, 0.15))
			elseif k % 3 == 1 then
				local barrel = JunkKit.Barrel(C.yellow, hex("23232A"))
				barrel[1].collide = false
				put(out, barrel, topAt * CFrame.Angles(0, 0, s * 0.5))
			else
				table.insert(
					out,
					B(Vector3.new(4.6, 0.18, 3.4), topAt * CFrame.Angles(0.25, 0.3, s * 0.3), SCRAP.sheet[2], DECOR)
				)
			end
			z = z1
		end
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
	-- Ориентиры у стен: кран с висящей машиной (стрела над полосой), сторожка у входа.
	put(out, JunkKit.Crane(30), at(70, 22))
	put(out, JunkKit.Booth(), at(-74, -36, math.rad(30)))
	-- Красные машины — яркие пятна по бокам поля (вне круга боя пса).
	put(out, JunkKit.Car(C.red), at(-34, 34, 0.35))
	put(out, JunkKit.Car(hex("E04434")), at(33, 36, -0.6))
	-- Будка пса — у края поля, лазом к площадке.
	put(out, JunkKit.Kennel(), at(-40, -2, -math.pi / 2))
	-- Жёлтые бочки с чёрной полосой — группами; шины, конусы.
	for _, spot in
		{
			Vector3.new(40, 0, 1),
			Vector3.new(42.4, 0, 3.2),
			Vector3.new(39.4, 0, 4),
			Vector3.new(-38, 0, 12),
			Vector3.new(-40.4, 0, 13.6),
			Vector3.new(22, 0, -36),
		}
	do
		put(out, JunkKit.Barrel(C.yellow, hex("23232A")), CFrame.new(spot))
	end
	put(out, JunkKit.Tires(3), at(30, 26))
	put(out, JunkKit.Tires(4), at(-22, -40))
	for _, spot in { Vector2.new(-30, -18), Vector2.new(-37, -30), Vector2.new(20, -40), Vector2.new(25, -34) } do
		put(out, JunkKit.Cone(), at(spot.X, spot.Y))
	end
	-- Диван и кучка техники по краям поля.
	put(out, JunkKit.Sofa(hex("C0504D")), at(40, -38, 0.5))
	put(out, JunkKit.Washer(), at(-42, 40, -0.3))
	put(out, JunkKit.TV(), at(-38.6, 41.2, 0.4))
	put(out, JunkKit.Fridge(), at(-45.6, 38, 0.9))
	-- Лужи.
	put(out, JunkKit.Puddle(3.4), at(-26, 14, 0.4))
	put(out, JunkKit.Puddle(2.8), at(26, -26, -0.3))
	put(out, JunkKit.Puddle(3.6), at(42, 26, 0.9))
	put(out, JunkKit.Puddle(2.4), at(-20, -32, 1.3))
	put(out, JunkKit.Puddle(3), at(16, 40, 0.2))
	-- Фонари вдоль прохода.
	for _, spot in { Vector2.new(-17, -42), Vector2.new(17, -42), Vector2.new(-22, 26), Vector2.new(22, 30) } do
		put(out, Props.Lamp(), at(spot.X, spot.Y))
	end
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

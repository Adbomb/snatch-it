-- Уровень 4 «Пустыня» — «Храм спящего Сфинкса» (D59, оформление — D60 по утверждённому изображению владельца
-- assets/concepts/boss4/zone4_temple/reference.png): площадка босса и оформление зоны в кубическом стиле для слабых
-- телефонов. В центре — арена «Ложе Сфинкса»: мощёная площадка (r 31) с сине-золотой мозаичной лентой по краю,
-- солнечными лучами и ложем под спящим боссом (сине-золотая рамка, перед лапами — золотое солнце); четыре места
-- существ — плиты с золотым ободом (MapLayout.Arenas[4].slots, верх плиты — Arenas[4].top). Вокруг — каменный борт из
-- пяти ярусов (r 32–41.5, выше всего 1.35) с проходами к храму и по бокам; к входу — парадная лестница с бортами и
-- мозаикой на площадке. Жаровни с огнём — у лестницы, на борту, у проходов и у храма; четыре стелы со светящимся
-- анхом — по углам. За ареной (к выходу) — храм с водопадами (World/Models/DesertTemple), по бокам — пирамиды,
-- водопады со стен обрыва с прудами-оазисами, пальмы, руины с аркой, фиолетовые сосуды, ящики, скалы, дюны и кусты.
-- Полосы |x| 48–66 вдоль всей зоны — мощёные пути с меандром (ничего твёрдого выше пола и ниже 7); к арене ведут
-- дороги от путей и к лестнице храма. Высоты площадки, места Сфинкса и существ — как в D59: в круге, куда босс
-- заходит в бою (r 34, scripts/lune/check_world.luau), нет ничего выше 2. Света нет (огонь, анхи — неон), частиц
-- нет; поперёк коридора ничего (D41). Координаты зоны: x — поперёк (±92, стены обрыва на ±92), z — вдоль (вход
-- −47.5, выход +47.5), y = 0 — пол. Надпись возвращается списком (её пишет WorldBuilder).
-- Зависит от MapLayout, World/Models/FleaKit, World/Models/DesertTemple.

local ServerScriptService = game:GetService("ServerScriptService")

local World = ServerScriptService.Server.World
local MapLayout = require(World.MapLayout)
local FleaKit = require(World.Models.FleaKit)
local DesertTemple = require(World.Models.DesertTemple)
local DesertCanyon = require(World.Models.DesertCanyon)

type Brick = FleaKit.Brick
export type Sign = FleaKit.Sign

local B, V = FleaKit.B, FleaKit.V
local Box, Disc = FleaKit.Box, FleaKit.Disc
local DECOR = FleaKit.DECOR
local SOLID = { collide = true } -- площадка, солнце и плиты — по ним ходят игроки и Сфинкс (диски по умолчанию без столкновений)

local C = DesertTemple.C

-- Борт арены: ярусы (внутренний и внешний радиус, верх, цвет) — вверх до 1.35 и снова вниз, как стена подиума.
local TIERS = {
	{ 32, 34, 0.45, C.stoneD },
	{ 34, 36, 0.9, C.stone },
	{ 36, 38.5, 1.35, C.stoneL },
	{ 38.5, 40, 0.9, C.stone },
	{ 40, 41.5, 0.45, C.stoneD },
}
local SEGMENTS = 32 -- по кругу; у четырёх направлений (0°, 90°, 180°, 270°) по два пропущено: проходы и лестница
-- Ступени парадной лестницы (к входу; z от и до, верх): вверх до площадки и вниз к арене.
local STAIRS = {
	{ -46.6, -45, 0.55 },
	{ -45, -43.5, 1 },
	{ -43.5, -41, 1.45 },
	{ -41, -38.9, 1 },
	{ -38.9, -37, 0.55 },
}
local STAIR_HALF = 6.6

local DesertOasis = {}
-- Свободный путь вдоль зоны по обе стороны (|x| от и до) и обход храма за крыльями к следующей зоне (|x| от и до,
-- z от и до): проверяет scripts/lune/check_world.luau.
DesertOasis.Lane = { 48, 66 }
DesertOasis.Bypass = { 41.5, 48, 24, 47.5 }

-- Сегмент с центром под углом deg (от +z к +x) — у прохода (два сегмента у каждого направления 0/90/180/270).
local function atOpening(deg: number): boolean
	local m = deg % 90
	return m < 9 or m > 81
end

function DesertOasis.Zone(): ({ Brick }, { Sign })
	FleaKit.Reset()
	local out: { Brick } = {}
	DesertCanyon.Sand(out) -- спокойный песок на весь пол зоны
	local arena = MapLayout.Arenas[4]
	local spot = MapLayout.BossSpot
	local cx, cz = spot.X, spot.Y
	local function polar(deg: number, r: number): (number, number)
		local a = math.rad(deg)
		return cx + math.sin(a) * r, cz + math.cos(a) * r
	end

	-- «Ложе Сфинкса»: золотая кромка, синяя мозаичная лента, золотая рамка и мощёное поле (каждый следующий диск
	-- выше — грани не совпадают; поле — на высоте Arenas[4].floor, как в D59)
	table.insert(out, Disc(62, -0.06, 0.1, cx, cz, C.gold, SOLID))
	table.insert(out, Disc(61.2, -0.055, 0.16, cx, cz, C.blue, SOLID))
	table.insert(out, Disc(57.2, -0.05, 0.22, cx, cz, C.gold, SOLID))
	table.insert(out, Disc(56, -0.04, 0.34, cx, cz, C.pave, SOLID))
	-- золотые швы мозаики поперёк синей ленты
	for k = 0, 35 do
		local a = math.rad(k * 10 + 5)
		local frame = CFrame.new(cx + math.sin(a) * 29.6, 0.21, cz + math.cos(a) * 29.6) * CFrame.Angles(0, a, 0)
		table.insert(out, B(V(0.4, 0.1, 2), frame, C.gold, DECOR))
	end
	-- солнечные лучи по полю (между ложем и местами существ)
	for k = 0, 11 do
		local a = math.rad(k * 30 + 15)
		-- верх 0.40: на 0.06 выше поля и на 0.06 ниже рамки ложа (0.46) — там, где луч заходит под рамку (D36)
		local frame = CFrame.new(cx + math.sin(a) * 20.5, 0.35, cz + math.cos(a) * 20.5) * CFrame.Angles(0, a, 0)
		table.insert(out, B(V(0.7, 0.1, 5), frame, if k % 2 == 0 then C.gold else C.blue, DECOR))
	end
	-- ложе спящего Сфинкса (лапы к входу, −z): двойная рамка — синяя внутри, золотая снаружи — прямо на поле.
	-- Под самим Сфинксом — поле площадки: его место стоит на верху поля (Arenas[4].floor), не проваливается.
	-- Рамка низкая (0.12 над полем) — лапы в бою её не задевают; полосы встык, грани не совпадают.
	table.insert(out, Box(cx - 8, cx - 7.2, 0.26, 0.46, cz - 18.8, cz + 12.8, C.blue))
	table.insert(out, Box(cx + 7.2, cx + 8, 0.26, 0.46, cz - 18.8, cz + 12.8, C.blue))
	table.insert(out, Box(cx - 8, cx + 8, 0.26, 0.46, cz - 19.6, cz - 18.8, C.blueL))
	table.insert(out, Box(cx - 8, cx + 8, 0.26, 0.46, cz + 12.8, cz + 13.6, C.blueL))
	table.insert(out, Box(cx - 8.8, cx - 8, 0.26, 0.46, cz - 19.6, cz + 13.6, C.gold))
	table.insert(out, Box(cx + 8, cx + 8.8, 0.26, 0.46, cz - 19.6, cz + 13.6, C.gold))
	table.insert(out, Box(cx - 8.8, cx + 8.8, 0.26, 0.46, cz - 20.4, cz - 19.6, C.goldD))
	table.insert(out, Box(cx - 8.8, cx + 8.8, 0.26, 0.46, cz + 13.6, cz + 14.4, C.goldD))
	-- золотое солнце перед лапами: диск и восемь лучей
	local sun = Vector3.new(cx, 0, cz - 25.5)
	table.insert(out, Disc(5, 0.26, 0.46, sun.X, sun.Z, C.gold, SOLID))
	table.insert(out, Disc(2.4, 0.3, 0.58, sun.X, sun.Z, C.goldD, SOLID))
	for k = 0, 7 do
		local a = math.rad(k * 45)
		local frame = CFrame.new(sun.X + math.sin(a) * 3.6, 0.215, sun.Z + math.cos(a) * 3.6) * CFrame.Angles(0, a, 0)
		table.insert(out, B(V(0.8, 0.49, 2), frame, C.gold, DECOR)) -- до пола: крайние лучи не висят над кромкой
	end
	-- места четырёх существ: плита с золотым ободом (верх — Arenas[4].top)
	for _, s in arena.slots do
		table.insert(out, Disc(6.2, -0.03, arena.top - 0.12, s.X, s.Y, C.gold, SOLID))
		table.insert(out, Disc(5.2, -0.02, arena.top, s.X, s.Y, C.stoneL, SOLID))
	end

	-- борт из пяти ярусов: сегменты по внутренней хорде — у внешнего края тонкий шов, совпадающих граней нет
	local step = 360 / SEGMENTS
	for _, tier in TIERS do
		local r0, r1, top, color = tier[1], tier[2], tier[3], tier[4]
		local width = 2 * r0 * math.sin(math.rad(step / 2))
		for k = 0, SEGMENTS - 1 do
			local deg = (k + 0.5) * step
			if not atOpening(deg) then
				local x, z = polar(deg, (r0 + r1) / 2)
				local frame = CFrame.new(x, top / 2, z) * CFrame.Angles(0, math.rad(deg), 0)
				table.insert(out, B(V(width, top, r1 - r0), frame, color))
			end
		end
	end
	-- парадная лестница к входу: ступени с золотыми кромками, борта с золотым покрытием, мозаика на площадке
	for i, st in STAIRS do
		local z0, z1, top = st[1], st[2], st[3]
		table.insert(out, Box(-STAIR_HALF, STAIR_HALF, 0, top, z0, z1, C.stoneL))
		-- кромка на лицевой грани: у ступеней к входу — на −z, у ступеней к арене — на +z
		local h = STAIR_HALF - 0.1
		if i <= 3 then
			table.insert(out, Box(-h, h, top - 0.2, top + 0.1, z0 - 0.1, z0 + 0.3, C.gold))
		else
			table.insert(out, Box(-h, h, top - 0.2, top + 0.1, z1 - 0.3, z1 + 0.1, C.gold))
		end
	end
	for _, s in { -1, 1 } do
		local x0, x1 = math.min(s * STAIR_HALF, s * 8.4), math.max(s * STAIR_HALF, s * 8.4)
		table.insert(out, Box(x0, x1, 0, 1.75, -46.6, -37.4, C.stone))
		x0, x1 = math.min(s * 6.5, s * 8.5), math.max(s * 6.5, s * 8.5)
		table.insert(out, Box(x0, x1, 1.75, 1.95, -46.7, -37.3, C.gold))
	end
	table.insert(out, Box(-5, 5, 1.45, 1.53, -42.9, -41.6, C.blue, DECOR))
	table.insert(out, Box(-5.2, 5.2, 1.45, 1.57, -43.1, -42.9, C.gold, DECOR))
	table.insert(out, Box(-5.2, 5.2, 1.45, 1.57, -41.6, -41.4, C.gold, DECOR))
	for _, s in { -1, 1 } do
		local x0, x1 = math.min(s * 1.8, s * 3.2), math.max(s * 1.8, s * 3.2)
		table.insert(out, Box(x0, x1, 1.53, 1.6, -42.5, -42, C.gold, DECOR))
	end

	-- жаровни: на бортах лестницы и у её подножия, у боковых проходов, у лестницы храма, на борту арены
	for _, s in { -1, 1 } do
		DesertTemple.Brazier(out, s * 7.5, -45.8, 1.3, 1.95)
		DesertTemple.Brazier(out, s * 11.5, -45.8, 2.6)
		DesertTemple.Brazier(out, s * 44, 3.5, 2.6)
		DesertTemple.Brazier(out, s * 44, -13.5, 2.6)
		DesertTemple.Brazier(out, s * 9, 32.2, 2.2)
	end
	for _, deg in { 40, 140, 220, 320 } do
		local x, z = polar(deg, 37.25)
		DesertTemple.Brazier(out, x, z, 2.6)
	end
	-- зелень: кусты у подножия лестницы и на внешнем ярусе борта, лианы по бортам лестницы
	for _, s in { -1, 1 } do
		DesertTemple.Bush(out, s * 9.8, 0, -47, 0.55)
		for _, z in { -44.2, -40.6 } do
			local x0, x1 = math.min(s * 8.4, s * 8.6), math.max(s * 8.4, s * 8.6)
			table.insert(out, Box(x0, x1, 0.3, 1.75, z - 0.35, z + 0.35, C.leafD, DECOR))
		end
	end
	for _, deg in { 46, 134, 226, 314 } do
		local x, z = polar(deg, 39.25)
		DesertTemple.Bush(out, x, 0.9, z, 0.6)
	end
	-- стелы со светящимся анхом по углам арены
	for _, s in { -1, 1 } do
		DesertTemple.Stele(out, s * 26, -42.5, 2.5)
		DesertTemple.Stele(out, s * 26, 31.5, 2.5)
	end

	-- храм за ареной (к выходу) с водопадами в пруды
	DesertTemple.Temple(out)

	-- дороги: от арены к лестнице храма, от боковых проходов к путям; пути вдоль зоны — мощёные, с меандром
	DesertTemple.Road(out, -4.5, 4.5, 26.4, 34.4, true)
	DesertTemple.Road(out, 31.2, 51.6, -9.5, -0.5, false)
	DesertTemple.Road(out, -51.6, -31.2, -9.5, -0.5, false)
	for _, s in { -1, 1 } do
		DesertTemple.Path(out, s, 52, 62, -46.9, 46.9, { -38, -23, -8, 7, 22, 37 })
	end

	-- стены обрыва — за песчаными скалами: уступы со склонами, слои песчаника, шпили над кромкой (DesertCanyon)
	local cliffs: { [number]: { DesertCanyon.Cliff } } = {
		[-1] = {
			{ z0 = -45, z1 = -36, base = { 81, 12 }, mid = { 84.5, 20 }, top = { 88, 29 }, yaw = 3 },
			{
				z0 = -36,
				z1 = -24,
				base = { 83.5, 10.5 },
				mid = { 86.5, 18.5 },
				top = { 89, 28 },
				yaw = -3.5,
				spire = { -31, 34 },
				shade = 1,
			},
			{ z0 = 12, z1 = 26, base = { 82, 14 }, mid = { 85.5, 21.5 }, top = { 88.5, 29.5 }, yaw = 3.5 },
			{
				z0 = 26,
				z1 = 45,
				base = { 89.5, 20 },
				mid = { 90.2, 27 },
				top = { 91, 31 },
				spire = { 38, 37 },
				shade = 1,
			},
		},
		[1] = {
			{
				z0 = -45,
				z1 = -33,
				base = { 82.5, 11 },
				mid = { 86, 19 },
				top = { 88.5, 28.5 },
				yaw = -3,
				spire = { -39, 35 },
				shade = 1,
			},
			{ z0 = -33, z1 = -18, base = { 79.5, 13 }, mid = { 84, 21 }, top = { 88, 29.5 }, yaw = 3.5 },
			{ z0 = -18, z1 = -3, base = { 83, 10 }, mid = { 86.5, 17.5 }, top = { 89, 28 }, yaw = -3.5, shade = 1 },
			{
				z0 = -3,
				z1 = 12,
				base = { 80.5, 12 },
				mid = { 84.5, 20 },
				top = { 88, 29.5 },
				yaw = 3,
				spire = { 4, 36 },
			},
			{ z0 = 12, z1 = 26, base = { 83.5, 10.5 }, mid = { 87, 19 }, top = { 89.5, 28.5 }, yaw = -3.5, shade = 1 },
			{ z0 = 26, z1 = 45, base = { 89.5, 20 }, mid = { 90.2, 27 }, top = { 91, 31 }, spire = { 38, 37 } },
		},
	}
	for s, list in cliffs do
		for i, c in list do
			DesertCanyon.Cliff(out, s, c)
			local nextCliff = list[i + 1]
			if nextCliff and nextCliff.z0 == c.z1 then
				DesertCanyon.Seam(out, s, c, nextCliff)
			end
		end
	end
	-- оазис у левой стены: два бассейна, каменная кромка и ступени, водопад из расщелины, пальмы, цветы, камыш
	DesertCanyon.Oasis(out, -1, {
		main = { 79, -6, 22 },
		lobe = { 73.5, 6.5, 12 },
		falls = { -8.5, -2.5 },
		towers = { { -24, -8.5, 86.5, 19 }, { -2.5, 12, 87, 21 } },
	})
	DesertTemple.Palm(out, -70.5, -18, 10, 2, 40)
	DesertTemple.Palm(out, -84, -20, 12.5, 2.4, 110)
	DesertTemple.Palm(out, -69.5, 13.5, 11, 2.2, 150)
	DesertTemple.Palm(out, -79, 15, 9, 1.8, 250)
	DesertTemple.Palm(out, -85.5, 3, 11.5, 2.2, 290)
	DesertCanyon.Flowers(out, -69, -15.5, C.pink, C.flameL)
	DesertCanyon.Flowers(out, -74, -19.5, C.flameL, C.foam)
	DesertCanyon.Flowers(out, -68, 12.5, C.pink, C.foam)
	DesertCanyon.Flowers(out, -78.5, 13.5, C.purple, C.flameL)
	DesertTemple.Vase(out, -70.2, -21.2, 0.9, C.purple, C.gold)
	-- пирамиды у выхода (фон храма), пальмы и кусты на уступах, барханы
	DesertTemple.Pyramid(out, -79.5, 36.5, 21, 9, 2.2)
	DesertTemple.Pyramid(out, 79.5, 36.5, 21, 9, 2.2)
	DesertTemple.Palm(out, 75, -10, 11, 2, 200)
	DesertTemple.Palm(out, 76.5, 18.5, 12, 2.2, 160)
	DesertTemple.Palm(out, -77, -40.5, 10.5, 2, 30)
	for _, b in { { 81.5, 13, -25.5, 1.1 }, { 82.5, 12, 4.5, 1 }, { -83, 12, -40.5, 1 }, { -84, 14, 19, 1.1 } } do
		DesertTemple.Bush(out, b[1], b[2], b[3], b[4])
	end
	DesertCanyon.Dune(out, -71.5, -42, 8, 1.6, 4, 70)
	DesertCanyon.Dune(out, 72, -40, 7, 1.4, 3.5, 100)

	-- между ареной и путями: руины с аркой, пальмы, сосуды и ящики, кусты, песчаные блоки
	DesertTemple.Ruin(out, -42, -36, "colonnade", 20)
	DesertTemple.Ruin(out, 40.5, -36, "arch", -15)
	DesertTemple.Ruin(out, -37, 22.5, "arch", 10)
	DesertTemple.Ruin(out, 38.5, 22, "wall", -20)
	DesertTemple.Palm(out, -46, 30, 12, 2.4, 330)
	DesertTemple.Palm(out, 46.5, 31, 11, 2, 200)
	DesertTemple.Palm(out, -44.5, -45, 10.5, 2.2, 60)
	DesertTemple.Palm(out, 45, -44.5, 11.5, 2, 130)
	DesertTemple.Vase(out, -34, -45.2, 1.1, C.purple, C.gold)
	DesertTemple.Vase(out, -31.4, -46.2, 0.85, C.purple, C.gold)
	DesertTemple.Vase(out, 34, -45.5, 0.95, C.purple, C.gold)
	DesertTemple.Crate(out, -37.5, 0, -44.5, 2.2, 15)
	DesertTemple.Crate(out, -37.3, 2.2, -44.6, 1.6, 40)
	DesertTemple.Crate(out, 37, 0, -45, 2, -10)
	for _, s in { -1, 1 } do
		DesertTemple.Vase(out, s * 20.5, 33.4, 0.9, C.purple, C.gold)
		DesertTemple.Vase(out, s * 18.6, 33.9, 0.65, C.purple, C.gold)
		DesertTemple.Bush(out, s * 30.5, 0, -41, 0.8)
		DesertTemple.Bush(out, s * 22, 0, 30.5, 0.7)
	end
	DesertTemple.Bush(out, -33.5, 0, 25, 0.8)
	DesertTemple.Bush(out, 45, 0, 25, 0.7)
	for _, p in
		{
			{ 44, -22, 1.8, 0.9, 20 },
			{ -45, 9, 2.2, 1.1, -30 },
			{ 41, 12, 1.4, 0.7, 50 },
			{ -39, -23, 1.6, 0.8, 10 },
		}
	do
		DesertTemple.Pebble(out, p[1], p[2], p[3], p[4], p[5])
	end
	return out, FleaKit.Signs()
end

return DesertOasis

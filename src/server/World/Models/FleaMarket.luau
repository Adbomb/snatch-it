-- Уровень 2 «Барахолка» (D43): яркий, немного безумный рынок редких трофеев. Цвета по старшинству: графит — металл
-- и основа, бирюза — крупные поверхности, оранжевый — навесы, вывески, бордюры, золото — сокровища, фиолетовый —
-- редкости и неон. Пол — плитка 8×8 шахматкой двух тонов со швами (между плитками виден графитовый пол зоны) и
-- оранжевые бордюры вдоль торговых рядов (FleaMarket.Ground). В центре — торговая площадка босса: круг с золотым
-- ободом и огоньками, звезда, медальон под боссом; предметы стоят прямо на ней (MapLayout.Arenas). Вокруг площадки —
-- сундуки с золотом, мешки с монетами и два прожектора на босса. По бокам коридора — торговые ряды: у края стена из
-- цветных панелей на металлических стойках с рекламой и крупными вывесками, перед ней прилавки с навесами, стеллажи
-- с трофеями, витрины, автоматы с капсулами, стопки чемоданов, большие весы, ящики с неоном, мешки и сундуки; у
-- бордюров — столбы с подвесными вывесками редкостей. Проход вдоль коридора (|x| < 46) и круг площадки свободны,
-- арок и ворот нет (D41). Света мало (2 прожектора и 4 точечных), частиц нет — для телефонов. Без Random: декор
-- одинаков при каждой сборке. Координаты зоны: x — поперёк коридора (±92), z — вдоль (вход −47.5, выход +47.5),
-- y = 0 — пол. Вещь — функция кирпичей в своих координатах (лицо — сторона −Z), ставится через put. Совпадающих
-- граней нет: накладки выступают за грань или лежат встык, плоские слои — с разной высотой верха (D36).
-- Надписи вывесок FleaMarket.Zone возвращает списком (их пишет WorldBuilder через World/Signs).
-- Зависит от ModelBuilder, Palette, MapLayout, Config/Rarities, Config/UITokens.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Rarities = require(ReplicatedStorage.Shared.Config.Rarities)
local UITokens = require(ReplicatedStorage.Shared.Config.UITokens)
local World = ServerScriptService.Server.World
local MapLayout = require(World.MapLayout)
local ModelBuilder = require(World.ModelBuilder)
local Palette = require(World.Palette)

type Brick = ModelBuilder.Brick

-- Надпись на табличке name (деталь модели декора): текст на гранях faces.
export type Sign = { name: string, faces: { Enum.NormalId }, text: string }

local B = ModelBuilder.Brick
local V = Vector3.new
local DECOR = { collide = false, shadow = false }
local ROUND = { shape = "Cylinder", collide = false, shadow = false }
local BALL = { shape = "Ball", collide = false, shadow = false }
local GLASS = { material = Enum.Material.Glass, transparency = 0.55, collide = false, shadow = false }
local UPRIGHT = CFrame.Angles(0, 0, math.rad(90)) -- ось цилиндра вертикально
local ALONG_Z = CFrame.Angles(0, math.rad(90), 0) -- ось цилиндра вдоль Z
local DIAMOND = CFrame.Angles(math.rad(45), 0, math.rad(45)) -- куб на вершине: самоцвет

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

local C = {
	tileA = hex("EADFC6"), -- плитка: светлый камень
	tileB = hex("A9DED6"), -- плитка: светлая бирюза
	graphite = hex("3A3F4B"),
	graphiteDark = hex("2A2E38"),
	metal = hex("8C95A3"),
	silver = hex("C9D1DB"),
	teal = hex("2CB5A8"),
	tealDark = hex("1E7F77"),
	tealLight = hex("8FDDD3"),
	orange = hex("F08A24"),
	orangeLight = hex("FFB25E"),
	gold = hex("F2C230"),
	goldDark = hex("C9952A"),
	goldLight = hex("FFE27A"),
	purple = hex("7B3FD1"),
	purpleLight = hex("B07CF2"),
	cream = hex("F6EEDB"),
	red = hex("E5484D"),
	blue = hex("3D8EE0"),
	burlap = hex("C9A26B"),
	burlapDark = hex("9C7A48"),
	spot = hex("FFF1C9"), -- свет прожекторов
	wood = Palette.Wood,
	woodDark = Palette.WoodDark,
	glass = Palette.Glass,
	white = Palette.White,
}

local signs: { Sign } = {} -- надписи текущей сборки (FleaMarket.Zone)

-- Имя таблички с надписью text (уникальное в модели декора).
local function label(text: string, faces: { Enum.NormalId }?): string
	local name = ("Sign_%d"):format(#signs + 1)
	table.insert(signs, { name = name, faces = faces or { Enum.NormalId.Front }, text = text })
	return name
end

-- Кирпичи вещи, сдвинутые и повёрнутые на at.
local function put(out: { Brick }, bricks: { Brick }, at: CFrame)
	for _, brick in bricks do
		brick.cframe = at * brick.cframe
		table.insert(out, brick)
	end
end

-- Неон (без света или с точечным светом радиуса range).
local function neon(size: Vector3, at: Vector3 | CFrame, color: Color3, range: number?): Brick
	return B(size, at, color, {
		material = Enum.Material.Neon,
		collide = false,
		shadow = false,
		light = if range then { range = range, brightness = 1.2, color = color } else nil,
	})
end

-- Табличка под надпись: гладкая (SmoothPlastic), пупырышки не мешают тексту.
local function board(size: Vector3, at: Vector3 | CFrame, color: Color3, name: string): Brick
	return B(size, at, color, { material = Enum.Material.SmoothPlastic, name = name })
end

-- Самоцвет: куб на вершине с центром в at.
local function gem(size: number, at: Vector3, color: Color3): Brick
	return B(V(size, size, size), CFrame.new(at) * DIAMOND, color, DECOR)
end

-- Кубок высотой 1.8 × scale: подставка, ножка, чаша, крышка-шарик. Начало — центр низа.
local function trophy(color: Color3, scale: number): { Brick }
	local s = scale
	return {
		B(V(0.9, 0.3, 0.9) * s, V(0, 0.15, 0) * s, C.graphite, DECOR),
		B(V(0.5, 0.3, 0.3) * s, CFrame.new(0, 0.55 * s, 0) * UPRIGHT, color, ROUND),
		B(V(0.7, 0.9, 0.9) * s, CFrame.new(0, 1.15 * s, 0) * UPRIGHT, color, ROUND),
		B(V(0.5, 0.5, 0.5) * s, V(0, 1.55 * s, 0), color:Lerp(C.white, 0.35), BALL),
	}
end

-- Монета, лежащая на полу (толщина задаёт высоту верха: у соседних монет разная).
local function coin(x: number, z: number, thickness: number): Brick
	return B(V(thickness, 0.9, 0.9), CFrame.new(x, thickness / 2, z) * UPRIGHT, C.gold, ROUND)
end

local FleaMarket = {}

-- Прилавок с полосатым навесом: стойка, столешница, товар (кубок, самоцвет, коробка), задняя стенка с вывеской text.
function FleaMarket.Counter(stripeA: Color3, stripeB: Color3, text: string): { Brick }
	local out = {
		B(V(9.6, 3, 2.4), V(0, 1.5, -1.2), C.teal),
		B(V(10, 0.4, 2.8), V(0, 3.2, -1.2), C.cream, DECOR),
		B(V(9.8, 0.6, 0.16), V(0, 2.2, -2.48), C.orange, DECOR),
		B(V(10, 6.5, 0.5), V(0, 3.25, 2.25), C.tealDark),
		board(V(7, 1.6, 0.3), V(0, 5.4, 1.85), stripeA, label(text)),
		B(V(1.4, 0.9, 1.1), V(3, 3.85, -1), C.orangeLight, DECOR),
		gem(0.8, V(0, 4.05, -1.4), C.purpleLight),
	}
	for _, x in { -5, 5 } do
		table.insert(out, B(V(0.5, 7.6, 0.5), V(x, 3.8, -2.9), C.graphite, DECOR))
	end
	-- Навес с наклоном вперёд: от стоек (y 7.6) к верху задней стенки (y 6.5).
	local tilt = CFrame.new(0, 7.05, -0.35) * CFrame.Angles(math.rad(11), 0, 0)
	for i = 1, 5 do
		local color = if i % 2 == 0 then stripeB else stripeA
		table.insert(out, B(V(2.2, 0.3, 6.8), tilt * CFrame.new(-6.6 + i * 2.2, 0, 0), color, DECOR))
	end
	put(out, trophy(C.gold, 1.2), CFrame.new(-3, 3.4, -1.2))
	return out
end

-- Металлический стеллаж с трофеями: четыре полки, фиолетовая задняя стенка, неоновая кромка; кубки, самоцветы,
-- глобус, корона, слитки и столбик монет.
function FleaMarket.TrophyShelf(): { Brick }
	local out = {
		B(V(7.2, 7.8, 0.2), V(0, 4.1, 1.1), C.purple),
		B(V(8.4, 0.3, 2.6), V(0, 8.15, 0), C.graphiteDark),
		neon(V(8, 0.15, 0.1), V(0, 8.15, -1.35), C.purpleLight),
	}
	for _, x in { -3.8, 3.8 } do
		table.insert(out, B(V(0.4, 8, 2.4), V(x, 4, 0), C.graphite))
	end
	for _, y in { 0.4, 2.4, 4.4, 6.4 } do
		table.insert(out, B(V(7.2, 0.2, 2.2), V(0, y, -0.1), C.metal, DECOR))
	end
	-- Нижняя полка (верх 0.5): слитки и столбик монет.
	table.insert(out, B(V(1.6, 0.5, 0.8), V(-2.2, 0.75, -0.2), C.gold, DECOR))
	table.insert(
		out,
		B(V(1.4, 0.45, 0.7), CFrame.new(-2.1, 1.225, -0.25) * CFrame.Angles(0, 0.2, 0), C.goldLight, DECOR)
	)
	table.insert(out, B(V(1, 0.8, 0.8), CFrame.new(1.8, 1, -0.3) * UPRIGHT, C.gold, ROUND))
	-- Вторая (верх 2.5): два кубка и самоцвет.
	put(out, trophy(C.gold, 0.9), CFrame.new(-2.3, 2.5, -0.2))
	put(out, trophy(C.silver, 0.85), CFrame.new(2.3, 2.5, -0.2))
	table.insert(out, gem(0.8, V(0, 3.2, -0.2), C.teal))
	-- Третья (верх 4.5): глобус на подставке, корона, самоцвет.
	table.insert(out, B(V(0.2, 0.9, 0.9), CFrame.new(-2.2, 4.6, -0.2) * UPRIGHT, C.gold, ROUND))
	table.insert(out, B(V(1.3, 1.3, 1.3), V(-2.2, 5.35, -0.2), C.blue, BALL))
	table.insert(out, B(V(0.7, 1.2, 1.2), CFrame.new(0.4, 4.85, -0.2) * UPRIGHT, C.gold, ROUND))
	table.insert(out, B(V(0.4, 0.4, 0.4), V(0.4, 5.3, -0.2), C.red, BALL))
	table.insert(out, gem(0.7, V(2.4, 5.1, -0.2), C.purpleLight))
	-- Верхняя (верх 6.5): кубок и два самоцвета.
	put(out, trophy(C.gold, 0.8), CFrame.new(0, 6.5, -0.2))
	table.insert(out, gem(0.6, V(-2.4, 7, -0.2), C.red))
	table.insert(out, gem(0.6, V(2.4, 7, -0.2), C.tealLight))
	return out
end

-- Открытый сундук с золотом: окованный ящик, откинутая назад крышка, горка золота, шары-самородки, самоцвет.
function FleaMarket.GoldChest(): { Brick }
	return {
		B(V(3.6, 1.8, 2.4), V(0, 0.9, 0), C.wood),
		B(V(0.3, 1.9, 2.5), V(-1.2, 0.95, 0), C.goldDark, DECOR),
		B(V(0.3, 1.9, 2.5), V(1.2, 0.95, 0), C.goldDark, DECOR),
		B(V(0.6, 0.6, 0.2), V(0, 1.2, -1.3), C.goldLight, DECOR),
		B(
			V(3.6, 0.4, 2.4),
			CFrame.new(0, 1.8, 1.2) * CFrame.Angles(math.rad(105), 0, 0) * CFrame.new(0, 0.2, -1.2),
			C.woodDark,
			DECOR
		),
		B(V(3.3, 0.5, 2.1), V(0, 1.95, 0), C.gold, DECOR),
		B(V(1, 1, 1), V(-0.9, 2.3, -0.2), C.goldLight, BALL),
		B(V(0.8, 0.8, 0.8), V(0.7, 2.25, 0.4), C.gold, BALL),
		gem(0.7, V(0.2, 2.6, -0.4), C.purpleLight),
	}
end

-- Автомат с капсулами: тумба цвета color, монетоприёмник с ручкой, стеклянный купол с капсулами.
function FleaMarket.CapsuleMachine(color: Color3): { Brick }
	local out = {
		B(V(2.4, 3, 2.4), V(0, 1.5, 0), color),
		B(V(1.4, 1.2, 0.2), V(0, 2.1, -1.3), C.graphite, DECOR),
		neon(V(0.6, 0.15, 0.1), V(0, 2.45, -1.45), C.goldLight),
		B(V(0.3, 0.9, 0.9), CFrame.new(0, 1.9, -1.55) * ALONG_Z, C.metal, ROUND),
		B(V(1, 0.6, 0.2), V(0, 0.7, -1.3), C.graphiteDark, DECOR),
		B(V(0.3, 2.7, 2.7), CFrame.new(0, 3.15, 0) * UPRIGHT, C.graphite, ROUND),
		B(V(2.6, 2.6, 2.6), V(0, 4.5, 0), C.glass, {
			shape = "Ball",
			material = Enum.Material.Glass,
			transparency = 0.5,
			collide = false,
			shadow = false,
		}),
		B(V(0.4, 1.2, 1.2), CFrame.new(0, 5.85, 0) * UPRIGHT, color, ROUND),
	}
	local capsules = {
		{ V(-0.5, 3.9, -0.3), C.red },
		{ V(0.5, 3.9, 0.2), C.gold },
		{ V(0, 3.95, 0.6), C.teal },
		{ V(-0.3, 4.5, 0.3), C.purpleLight },
		{ V(0.4, 4.4, -0.4), C.orange },
	}
	for _, capsule in capsules do
		table.insert(out, B(V(0.7, 0.7, 0.7), capsule[1], capsule[2], BALL))
	end
	return out
end

-- Стопка из четырёх чемоданов: каждый чуть повёрнут, с ремнём и ручкой спереди.
function FleaMarket.Suitcases(): { Brick }
	local out = {}
	local stack = {
		{ size = V(4.2, 1.4, 2.8), color = C.wood, turn = 0 },
		{ size = V(3.8, 1.2, 2.6), color = C.teal, turn = 0.14 },
		{ size = V(3.3, 1.3, 2.3), color = C.orange, turn = -0.1 },
		{ size = V(2.7, 1.1, 2), color = C.purple, turn = 0.32 },
	}
	local y = 0
	for i, case in stack do
		local at = CFrame.new((i % 2) * 0.2 - 0.1, y + case.size.Y / 2, 0) * CFrame.Angles(0, case.turn, 0)
		table.insert(out, B(case.size, at, case.color, DECOR))
		local strap = V(0.35, case.size.Y + 0.1, case.size.Z + 0.2) -- выступает на 0.1 (D36)
		table.insert(out, B(strap, at * CFrame.new(-case.size.X / 4, 0, 0), C.woodDark, DECOR))
		table.insert(out, B(V(1.2, 0.3, 0.25), at * CFrame.new(0.3, 0, -case.size.Z / 2 - 0.125), C.graphite, DECOR))
		y += case.size.Y
	end
	return out
end

-- Большие весы (ориентир ряда): тумба, золотая колонна, коромысло с наклоном — чаша с монетами и слитком
-- перевешивает чашу с самоцветом.
function FleaMarket.BigScales(): { Brick }
	local pivot = V(0, 10, 0)
	local beam = CFrame.new(pivot) * CFrame.Angles(0, 0, math.rad(6))
	local out = {
		B(V(5, 1, 3.4), V(0, 0.5, 0), C.graphite),
		B(V(4, 0.6, 2.6), V(0, 1.3, 0), C.goldDark),
		B(V(8.2, 1, 1), CFrame.new(0, 5.7, 0) * UPRIGHT, C.gold, ROUND),
		B(V(1.6, 1.6, 1.6), pivot, C.goldLight, BALL),
		B(V(11, 0.5, 0.6), beam, C.goldDark, DECOR),
	}
	for _, side in { -1, 1 } do
		local tip = (beam * CFrame.new(side * 5.2, 0, 0)).Position
		local pan = V(tip.X, tip.Y - 4.3, 0)
		for _, dx in { -1.4, 1.4 } do
			local foot = pan + V(dx, 0.15, 0)
			local mid = (tip + foot) / 2
			table.insert(out, B(V(0.15, 0.15, (tip - foot).Magnitude), CFrame.lookAt(mid, foot), C.metal, DECOR))
		end
		table.insert(out, B(V(0.3, 3.4, 3.4), CFrame.new(pan) * UPRIGHT, C.gold, ROUND))
		local top = pan.Y + 0.15
		if side < 0 then
			table.insert(out, B(V(0.6, 1, 1), CFrame.new(pan.X - 0.6, top + 0.3, 0.3) * UPRIGHT, C.gold, ROUND))
			table.insert(out, B(V(0.9, 1, 1), CFrame.new(pan.X + 0.5, top + 0.45, -0.4) * UPRIGHT, C.goldLight, ROUND))
			table.insert(
				out,
				B(V(1.2, 0.45, 0.6), CFrame.new(pan.X, top + 0.225, 0.95) * CFrame.Angles(0, 0.3, 0), C.gold, DECOR)
			)
		else
			table.insert(out, gem(1.2, V(pan.X, top + 1, 0), C.purpleLight))
		end
	end
	return out
end

-- Ящики с неоном: большой ящик со светящейся крышкой (с точечным светом, если lit), на нём ящик поменьше, рядом
-- третий.
function FleaMarket.NeonCrates(lit: boolean): { Brick }
	local out = {
		B(V(3, 2.4, 3), V(0, 1.2, 0), C.wood),
		B(V(3.1, 0.4, 3.1), V(0, 0.6, 0), C.woodDark, DECOR),
		B(V(3.1, 0.4, 3.1), V(0, 1.8, 0), C.woodDark, DECOR),
		neon(V(2.4, 0.3, 2.4), V(0, 2.5, 0), C.purpleLight, if lit then 14 else nil),
	}
	local upper = CFrame.new(0.2, 3.65, 0.1) * CFrame.Angles(0, 0.26, 0)
	table.insert(out, B(V(2.4, 2, 2.4), upper, C.wood))
	table.insert(out, B(V(2.5, 0.35, 2.5), upper * CFrame.new(0, -0.3, 0), C.woodDark, DECOR))
	table.insert(out, neon(V(1.9, 0.25, 1.9), upper * CFrame.new(0, 1.1, 0), C.tealLight))
	local side = CFrame.new(3.7, 1, -0.6) * CFrame.Angles(0, -0.2, 0)
	table.insert(out, B(V(2.6, 2, 2.6), side, C.wood))
	table.insert(out, B(V(2.7, 0.35, 2.7), side * CFrame.new(0, 0.3, 0), C.woodDark, DECOR))
	table.insert(out, neon(V(2, 0.25, 2), side * CFrame.new(0, 1.1, 0), C.orange))
	return out
end

-- Витрина: стеклянный шкаф в золотых стойках на графитовой тумбе, подсветка внутри (точечный свет), полка,
-- редкости (кубок, самоцветы, золотое яйцо), вывеска text сверху.
function FleaMarket.Showcase(text: string): { Brick }
	local out = {
		B(V(6, 1.4, 2.4), V(0, 0.7, 0), C.graphite),
		B(V(5.6, 3.6, 2), V(0, 3.2, 0), C.glass, GLASS),
		B(V(6.2, 0.5, 2.6), V(0, 5.25, 0), C.graphite),
		B(V(5.4, 0.15, 1.8), V(0, 3, 0), C.metal, DECOR),
		neon(V(5.2, 0.12, 0.3), V(0, 4.94, 0), C.cream, 10),
		board(V(5, 1.1, 0.3), V(0, 6.05, -0.2), C.orange, label(text)),
		gem(0.8, V(0, 2.15, 0), C.teal),
		B(V(1, 1, 1), V(1.8, 1.9, 0), C.goldLight, BALL),
		gem(0.6, V(-1.2, 3.6, 0), C.purpleLight),
		gem(0.6, V(1.2, 3.6, 0), C.red),
	}
	for _, x in { -2.85, 2.85 } do
		for _, z in { -1.05, 1.05 } do
			table.insert(out, B(V(0.3, 3.8, 0.3), V(x, 3.3, z), C.gold, DECOR))
		end
	end
	put(out, trophy(C.gold, 0.8), CFrame.new(-1.8, 1.4, 0))
	return out
end

-- Мешок с монетами размера scale: низ, круглое тело, горловина с золотой завязкой, монета-знак спереди.
local function sack(out: { Brick }, at: CFrame, scale: number)
	local s = scale
	put(out, {
		B(V(2, 1.6, 2) * s, V(0, 0.8 * s, 0), C.burlap, DECOR),
		B(V(2.3, 2.3, 2.3) * s, V(0, 1.5 * s, 0), C.burlap, BALL),
		B(V(0.6, 0.9, 0.9) * s, CFrame.new(0, 2.75 * s, 0) * UPRIGHT, C.burlapDark, ROUND),
		B(V(0.2, 1.05, 1.05) * s, CFrame.new(0, 2.6 * s, 0) * UPRIGHT, C.goldDark, ROUND),
		B(V(0.2, 0.9, 0.9) * s, CFrame.new(0, 1.3 * s, -1.15 * s) * ALONG_Z, C.gold, ROUND),
	}, at)
end

-- Три мешка с монетами и рассыпанные монеты перед ними.
function FleaMarket.CoinSacks(): { Brick }
	local out = {}
	sack(out, CFrame.new(0, 0, 0), 1)
	sack(out, CFrame.new(2.3, 0, 0.6) * CFrame.Angles(0, -0.5, 0), 0.8)
	sack(out, CFrame.new(-2, 0, 0.9) * CFrame.Angles(0, 0.6, 0), 0.9)
	table.insert(out, coin(-1, -2, 0.15))
	table.insert(out, coin(-0.3, -1.7, 0.2))
	table.insert(out, coin(0.4, -2.4, 0.25))
	table.insert(out, coin(1.2, -1.9, 0.3))
	table.insert(out, coin(0.6, -1.5, 0.35))
	return out
end

-- Столб с подвесной вывеской редкости rarity: на кронштейне над проходом табличка цвета редкости (Stud-UI,
-- UITokens) с названием редкости с обеих сторон и самоцветами по старшинству (1 — обычный, 3 — эпический).
function FleaMarket.RarityPole(rarity: string): { Brick }
	local color = UITokens.RarityColor(rarity)
	local out = {
		B(V(1.6, 0.4, 1.6), V(0, 0.2, 0), C.graphite),
		B(V(0.6, 11, 0.6), V(0, 5.9, 0), C.metal),
		B(V(0.5, 0.5, 5.2), V(0, 11.35, -2.15), C.graphite, DECOR), -- выступает за столб сзади (D36)
		board(
			V(0.3, 3, 3.6),
			V(0, 8.2, -2.6),
			color,
			label(Rarities.Names[rarity], { Enum.NormalId.Left, Enum.NormalId.Right })
		),
		B(V(0.2, 3.3, 3.9), V(0, 8.2, -2.6), C.goldDark, DECOR),
	}
	for _, z in { -1.2, -4 } do
		table.insert(out, B(V(0.12, 1.4, 0.12), V(0, 10.4, z), C.metal, DECOR))
	end
	local rank = Rarities.Rank(rarity)
	for k = 1, rank do
		table.insert(out, gem(0.7, V(0, 10.3, -2.6 + (k - (rank + 1) / 2)), color))
	end
	return out
end

local CURB = 46.5 -- бордюры вдоль прохода (|x|), плитка — до 44.5
local FRONT = 56 -- передний торговый ряд (|x| начала вещи)
local BACK = 80 -- задний ряд у стены
local WALL_X = 89 -- торговая стена у края коридора
local WALL_BAYS = 7
local BAY = 12 -- ширина пролёта стены

-- Торговая стена ряда вдоль X: металлические стойки, цветные панели, цоколь, балка с неоновой полосой; на панелях
-- реклама — плакаты posters (по порядку), большая монета или самоцвет; на балке — две вывески billboards.
function FleaMarket.TradeWall(posters: { string }, billboards: { { text: string, color: Color3 } }): { Brick }
	local out = {}
	local half = WALL_BAYS * BAY / 2
	local panels = { C.teal, C.orange, C.purple }
	local ads = { "poster", "coin", "poster", "gem", "poster", "coin", "gem" }
	local posterIndex = 0
	for i = 0, WALL_BAYS do
		table.insert(out, B(V(1.2, 14.6, 1.2), V(-half + i * BAY, 7.3, 0), C.graphite))
	end
	for i = 1, WALL_BAYS do
		local x = -half + (i - 0.5) * BAY
		table.insert(out, B(V(BAY - 1.2, 12.6, 0.8), V(x, 7.3, 0), panels[(i - 1) % #panels + 1]))
		local ad = ads[i]
		if ad == "poster" then
			posterIndex += 1
			table.insert(out, B(V(8.4, 4, 0.2), V(x, 8.6, -0.5), C.goldDark, DECOR))
			table.insert(out, board(V(8, 3.6, 0.3), V(x, 8.6, -0.55), C.cream, label(posters[posterIndex])))
		elseif ad == "coin" then
			table.insert(out, B(V(0.3, 6, 6), CFrame.new(x, 8, -0.55) * ALONG_Z, C.gold, ROUND))
			table.insert(out, B(V(0.2, 4.6, 4.6), CFrame.new(x, 8, -0.75) * ALONG_Z, C.goldLight, ROUND))
		else
			local turn = CFrame.Angles(0, 0, math.rad(45))
			table.insert(out, B(V(4.2, 4.2, 0.4), CFrame.new(x, 8.4, -0.6) * turn, C.purpleLight, DECOR))
			table.insert(out, B(V(2.6, 2.6, 0.3), CFrame.new(x, 8.4, -0.9) * turn, C.gold, DECOR))
		end
	end
	table.insert(out, B(V(WALL_BAYS * BAY, 1, 1), V(0, 0.5, 0), C.graphiteDark))
	table.insert(out, B(V(WALL_BAYS * BAY + 1.6, 1.4, 1.4), V(0, 14.3, 0), C.graphiteDark))
	table.insert(out, neon(V(WALL_BAYS * BAY, 0.3, 0.2), V(0, 13.9, -0.8), C.orange))
	for i, sign in billboards do
		local x = (if i == 1 then -1 else 1) * 21
		table.insert(out, B(V(16.6, 5, 0.4), V(x, 17.2, 0.4), C.gold, DECOR))
		table.insert(out, board(V(16, 4.4, 0.6), V(x, 17.2, 0), sign.color, label(sign.text)))
	end
	return out
end

-- Прожектор на столбе: голова смотрит на точку target (свет — конус из её грани −Z).
local function spotTower(out: { Brick }, x: number, z: number, target: Vector3)
	table.insert(out, B(V(2.6, 0.6, 2.6), V(x, 0.3, z), C.graphite))
	table.insert(out, B(V(13.4, 0.8, 0.8), CFrame.new(x, 7.3, z) * UPRIGHT, C.metal, ROUND))
	local head = CFrame.lookAt(V(x, 14.6, z), target)
	table.insert(
		out,
		B(V(1.8, 1.6, 2.4), head, C.graphiteDark, {
			collide = false,
			shadow = false,
			light = { range = 40, brightness = 3, color = C.spot, angle = 45 },
		})
	)
	table.insert(out, neon(V(1.4, 1.2, 0.2), head * CFrame.new(0, 0, -1.25), C.goldLight))
end

-- Пол барахолки поверх пола зоны: плитка шахматкой (верх 0.05) — у площадки её нет, бордюры рядов (верх 0.4);
-- торговая площадка босса: обод (верх 0.1), круг (верх Arenas.top = 0.15, на нём предметы), звезда из двух квадратов
-- (0.2 и 0.25), медальон под боссом (0.3) и восемь огоньков по ободу.
function FleaMarket.Ground(): { Brick }
	local out = {}
	local arena = MapLayout.Arenas[2]
	local center = MapLayout.BossSpot
	local rim = arena.radius + 1
	for i = 0, 9 do
		for j = 0, 9 do
			local x, z = -40.5 + i * 9, -40.5 + j * 9
			-- Плитка целиком под площадкой не видна — её нет; плитку на краю закрывает обод.
			local far = 0
			for _, corner in { V(-4, 0, -4), V(4, 0, -4), V(-4, 0, 4), V(4, 0, 4) } do
				far = math.max(far, (Vector2.new(x + corner.X, z + corner.Z) - center).Magnitude)
			end
			if far >= rim then
				table.insert(
					out,
					B(V(8, 0.05, 8), V(x, 0.025, z), if (i + j) % 2 == 0 then C.tileA else C.tileB, DECOR)
				)
			end
		end
	end
	for _, x in { -CURB, CURB } do
		table.insert(out, B(V(1, 0.4, 91), V(x, 0.2, 0), C.orange, DECOR))
	end
	local function disc(diameter: number, top: number, color: Color3): Brick
		return B(V(top, diameter, diameter), CFrame.new(center.X, top / 2, center.Y) * UPRIGHT, color, ROUND)
	end
	table.insert(out, disc(rim * 2, arena.top - 0.05, C.gold))
	table.insert(out, disc(arena.radius * 2, arena.top, C.teal))
	table.insert(out, B(V(16, arena.top + 0.05, 16), V(center.X, (arena.top + 0.05) / 2, center.Y), C.orange, DECOR))
	local star = CFrame.new(center.X, (arena.top + 0.1) / 2, center.Y) * CFrame.Angles(0, math.rad(45), 0)
	table.insert(out, B(V(16, arena.top + 0.1, 16), star, C.gold, DECOR))
	table.insert(out, disc(9, arena.top + 0.15, C.purple))
	for k = 0, 7 do
		local angle = math.rad(22.5 + k * 45)
		local at = CFrame.new(center.X + math.sin(angle) * (rim - 0.5), 0.1, center.Y + math.cos(angle) * (rim - 0.5))
		table.insert(out, neon(V(0.8, 0.2, 0.8), at * CFrame.Angles(0, angle, 0), C.purpleLight))
	end
	return out
end

-- Весь декор барахолки в координатах зоны и надписи вывесок.
function FleaMarket.Zone(): ({ Brick }, { Sign })
	signs = {}
	local out = FleaMarket.Ground()
	-- Лицом к середине коридора: слева (x < 0) лицо −Z смотрит в +X, справа — в −X.
	local function left(z: number, x: number, turn: number?): CFrame
		return CFrame.new(-x, 0, z) * CFrame.Angles(0, -math.pi / 2 + (turn or 0), 0)
	end
	local function right(z: number, x: number, turn: number?): CFrame
		return CFrame.new(x, 0, z) * CFrame.Angles(0, math.pi / 2 + (turn or 0), 0)
	end
	local function facing(x: number, z: number, target: Vector2): CFrame
		return CFrame.lookAt(V(x, 0, z), V(target.X, 0, target.Y))
	end

	-- Торговые стены у краёв коридора.
	put(
		out,
		FleaMarket.TradeWall({ "ТОРГ УМЕСТЕН", "НАХОДКА ДНЯ", "СКУПКА ТРОФЕЕВ" }, {
			{ text = "БАРАХОЛКА", color = C.orange },
			{ text = "РЕДКОСТИ", color = C.teal },
		}),
		left(0, WALL_X)
	)
	put(
		out,
		FleaMarket.TradeWall({ "ВСЁ БЕЗУМНО", "ОБМЕН НЕ ПРОСИ", "ЗОЛОТО ДЁШЕВО" }, {
			{ text = "ТРОФЕИ", color = C.purple },
			{ text = "ЗОЛОТО", color = C.orange },
		}),
		right(0, WALL_X)
	)

	-- Ряды вдоль прохода: передний — у бордюра (FRONT), задний — у стены (BACK…), между ними — торговая улочка.
	-- Левый ряд.
	put(out, FleaMarket.Counter(C.orange, C.white, "ТРОФЕИ"), left(-36, FRONT))
	for i, color in { C.teal, C.orange, C.purple } do
		put(out, FleaMarket.CapsuleMachine(color), left(-22 + (i - 2) * 3, FRONT))
	end
	put(out, FleaMarket.BigScales(), left(-8, FRONT))
	put(out, FleaMarket.Showcase("РЕДКОСТИ"), left(6, FRONT))
	put(out, FleaMarket.Counter(C.purple, C.white, "ЗОЛОТО"), left(20, FRONT))
	put(out, FleaMarket.CoinSacks(), left(34, FRONT, -0.3))
	put(out, FleaMarket.TrophyShelf(), left(-30, BACK + 4))
	put(out, FleaMarket.NeonCrates(true), left(-16, BACK))
	put(out, FleaMarket.Suitcases(), left(-2, BACK + 2, 0.2))
	put(out, FleaMarket.TrophyShelf(), left(12, BACK + 4))
	put(out, FleaMarket.GoldChest(), left(26, BACK, 0.3))
	put(out, FleaMarket.NeonCrates(false), left(37, BACK))

	-- Правый ряд.
	put(out, FleaMarket.Showcase("ВИТРИНА"), right(-36, FRONT))
	put(out, FleaMarket.Counter(C.teal, C.white, "НАХОДКИ"), right(-22, FRONT))
	for i, color in { C.purple, C.teal, C.orange } do
		put(out, FleaMarket.CapsuleMachine(color), right(-8 + (i - 2) * 3, FRONT))
	end
	put(out, FleaMarket.Counter(C.orange, C.white, "КАПСУЛЫ"), right(6, FRONT))
	put(out, FleaMarket.BigScales(), right(20, FRONT))
	put(out, FleaMarket.GoldChest(), right(32, FRONT, 0.25))
	put(out, FleaMarket.CoinSacks(), right(37, FRONT + 1, -0.2))
	put(out, FleaMarket.NeonCrates(true), right(-30, BACK))
	put(out, FleaMarket.TrophyShelf(), right(-16, BACK + 4))
	put(out, FleaMarket.Suitcases(), right(-2, BACK + 2, -0.25))
	put(out, FleaMarket.NeonCrates(false), right(12, BACK))
	put(out, FleaMarket.TrophyShelf(), right(26, BACK + 4))
	put(out, FleaMarket.Suitcases(), right(38, BACK + 2, 0.15))

	-- Столбы с подвесными вывесками редкостей у бордюров: обычный, редкий, эпический — от входа вглубь.
	for i, rarity in { "Common", "Rare", "Epic" } do
		local z = -30 + (i - 1) * 24
		put(out, FleaMarket.RarityPole(rarity), left(z, CURB + 2.5))
		put(out, FleaMarket.RarityPole(rarity), right(z, CURB + 2.5))
	end

	-- Вокруг площадки: сундуки и мешки лицом к боссу, прожекторы на него.
	local boss = MapLayout.BossSpot
	put(out, FleaMarket.GoldChest(), facing(-17, 18, boss))
	put(out, FleaMarket.GoldChest(), facing(17, 18, boss))
	put(out, FleaMarket.GoldChest(), facing(-26, -22, boss))
	put(out, FleaMarket.CoinSacks(), facing(26, -24, boss))
	put(out, FleaMarket.CoinSacks(), facing(-27, -6, boss))
	put(out, FleaMarket.CoinSacks(), facing(27, -4, boss))
	local target = V(boss.X, 7, boss.Y)
	spotTower(out, -24, 12, target)
	spotTower(out, 24, 12, target)
	return out, signs
end

return FleaMarket

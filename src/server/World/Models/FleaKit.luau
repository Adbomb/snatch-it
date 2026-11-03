-- Набор «Барахолки» (D43, D44): цвета рынка, общие детали и мелкий товар — то, из чего собраны павильоны и большие
-- вещи (World/Models/FleaStalls) и сам уровень (World/Models/FleaMarket). Цвета по старшинству: графит — металл и
-- основа, бирюза — крупные поверхности, оранжевый — навесы и вывески, золото — сокровища, фиолетовый — редкости и
-- неон. Вещь — функция кирпичей в своих координатах: начало — центр низа, лицо — сторона −Z; ставится через Put.
-- Совпадающих граней нет (D36): накладки выступают за грань, плоские слои — с разной высотой верха. Надписи табличек
-- копятся списком (Label), их пишет WorldBuilder через World/Signs. Без Random: декор одинаков при каждой сборке.
-- Зависит от ModelBuilder, Palette, Config/Rarities, Config/UITokens.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Rarities = require(ReplicatedStorage.Shared.Config.Rarities)
local UITokens = require(ReplicatedStorage.Shared.Config.UITokens)
local World = ServerScriptService.Server.World
local ModelBuilder = require(World.ModelBuilder)
local Palette = require(World.Palette)

export type Brick = ModelBuilder.Brick

-- Надпись на табличке name (деталь модели декора): текст на гранях faces.
export type Sign = { name: string, faces: { Enum.NormalId }, text: string }

local B = ModelBuilder.Brick
local V = Vector3.new

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

local FleaKit = {}

FleaKit.B = B
FleaKit.V = V
FleaKit.DECOR = { collide = false, shadow = false }
FleaKit.ROUND = { shape = "Cylinder", collide = false, shadow = false }
FleaKit.BALL = { shape = "Ball", collide = false, shadow = false }
FleaKit.WEDGE = { shape = "Wedge" }
FleaKit.GLASS = { material = Enum.Material.Glass, transparency = 0.6, collide = false, shadow = false }
FleaKit.UPRIGHT = CFrame.Angles(0, 0, math.rad(90)) -- ось цилиндра вертикально
FleaKit.ALONG_Z = CFrame.Angles(0, math.rad(90), 0) -- ось цилиндра вдоль Z: круг смотрит в −Z
FleaKit.DIAMOND = CFrame.Angles(math.rad(45), 0, math.rad(45)) -- куб на вершине: самоцвет
FleaKit.TURN = CFrame.Angles(0, math.pi, 0) -- разворот на 180° вокруг вертикали

FleaKit.C = {
	stone = hex("D9C8A5"), -- мощение прохода: тёплый светлый камень
	stoneDark = hex("BFA67F"),
	grout = hex("8F7A5E"), -- швы мощения: тёплые, мягче графита
	graphite = hex("3A3F4B"),
	graphiteDark = hex("2A2E38"),
	graphiteLight = hex("555C6B"),
	metal = hex("8C95A3"),
	silver = hex("C9D1DB"),
	teal = hex("2CB5A8"),
	tealDark = hex("1E7F77"),
	tealDeep = hex("16514D"),
	tealLight = hex("8FDDD3"),
	tealMid = hex("23998F"), -- поле площадки босса: темнее бирюзы, предметы на нём читаются
	orange = hex("F08A24"),
	orangeDark = hex("C4661A"),
	orangeLight = hex("FFB25E"),
	gold = hex("F2C230"),
	goldDark = hex("C9952A"),
	goldLight = hex("FFE27A"),
	purple = hex("7B3FD1"),
	purpleDark = hex("4E2A8C"),
	purpleLight = hex("B07CF2"),
	cream = hex("F6EEDB"),
	red = hex("E5484D"),
	blue = hex("3D8EE0"),
	burlap = hex("C9A26B"),
	burlapDark = hex("9C7A48"),
	spot = hex("FFF1C9"), -- свет прожекторов и ламп
	wood = Palette.Wood,
	woodDark = Palette.WoodDark,
	glass = Palette.Glass,
	white = Palette.White,
}
local C = FleaKit.C
local DECOR, ROUND, BALL, WEDGE = FleaKit.DECOR, FleaKit.ROUND, FleaKit.BALL, FleaKit.WEDGE
local UPRIGHT, ALONG_Z, DIAMOND = FleaKit.UPRIGHT, FleaKit.ALONG_Z, FleaKit.DIAMOND

-- Опции кирпича: base, дополненные extra.
local function with(base: { [string]: any }, extra: { [string]: any }?): { [string]: any }
	local merged = table.clone(base)
	if extra then
		for key, value in extra do
			merged[key] = value
		end
	end
	return merged
end
FleaKit.With = with

local signs: { Sign } = {} -- надписи текущей сборки

-- Начать сборку уровня: список надписей пуст.
function FleaKit.Reset()
	signs = {}
end

-- Надписи, накопленные с последнего Reset.
function FleaKit.Signs(): { Sign }
	return signs
end

-- Имя таблички с надписью text (уникальное в модели декора).
function FleaKit.Label(text: string, faces: { Enum.NormalId }?): string
	local name = ("Sign_%d"):format(#signs + 1)
	table.insert(signs, { name = name, faces = faces or { Enum.NormalId.Front }, text = text })
	return name
end

-- Кирпичи вещи, сдвинутые и повёрнутые на at.
function FleaKit.Put(out: { Brick }, bricks: { Brick }, at: CFrame)
	for _, brick in bricks do
		brick.cframe = at * brick.cframe
		table.insert(out, brick)
	end
end

-- Брусок по границам: x0..x1, y0..y1, z0..z1.
function FleaKit.Box(
	x0: number,
	x1: number,
	y0: number,
	y1: number,
	z0: number,
	z1: number,
	color: Color3,
	extra: { [string]: any }?
): Brick
	return B(V(x1 - x0, y1 - y0, z1 - z0), V((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), color, extra)
end

-- Диск (цилиндр с вертикальной осью) диаметра d от y0 до y1 с центром (x, z).
function FleaKit.Disc(
	d: number,
	y0: number,
	y1: number,
	x: number,
	z: number,
	color: Color3,
	extra: { [string]: any }?
): Brick
	return B(V(y1 - y0, d, d), CFrame.new(x, (y0 + y1) / 2, z) * UPRIGHT, color, with(ROUND, extra))
end

-- Круг лицом к −Z (цилиндр с осью вдоль Z) диаметра d толщиной t с центром at.
function FleaKit.Round(d: number, t: number, at: CFrame, color: Color3, extra: { [string]: any }?): Brick
	return B(V(t, d, d), at * ALONG_Z, color, with(ROUND, extra))
end

-- Неон (без света или с точечным светом радиуса range).
function FleaKit.Neon(size: Vector3, at: Vector3 | CFrame, color: Color3, range: number?): Brick
	return B(size, at, color, {
		material = Enum.Material.Neon,
		collide = false,
		shadow = false,
		light = if range then { range = range, brightness = 1.2, color = color } else nil,
	})
end

-- Табличка под надпись: гладкая (SmoothPlastic), пупырышки не мешают тексту.
function FleaKit.Board(size: Vector3, at: Vector3 | CFrame, color: Color3, name: string): Brick
	return B(size, at, color, { material = Enum.Material.SmoothPlastic, name = name, shadow = false })
end

-- Самоцвет: куб на вершине с центром в at.
function FleaKit.Gem(size: number, at: Vector3, color: Color3): Brick
	return B(V(size, size, size), CFrame.new(at) * DIAMOND, color, DECOR)
end

-- Двускатная крыша, конёк вдоль X: от x0 до x1, скаты к −Z (до z0) и к +Z (до z1), низ y, высота h. Полосы шириной
-- около stripe — по очереди цветов colors (без stripe — один цвет на скат). Высокая сторона клина — его +Z.
function FleaKit.Gable(
	out: { Brick },
	x0: number,
	x1: number,
	z0: number,
	z1: number,
	y: number,
	h: number,
	colors: { Color3 },
	stripe: number?
)
	local depth = (z1 - z0) / 2
	local count = if stripe then math.max(1, math.round((x1 - x0) / stripe)) else 1
	local w = (x1 - x0) / count
	for i = 1, count do
		local x = x0 + (i - 0.5) * w
		local color = colors[(i - 1) % #colors + 1]
		table.insert(out, B(V(w, h, depth), CFrame.new(x, y + h / 2, z0 + depth / 2), color, WEDGE))
		table.insert(out, B(V(w, h, depth), CFrame.new(x, y + h / 2, z1 - depth / 2) * FleaKit.TURN, color, WEDGE))
	end
end

-- Кубок высотой 1.8 × scale: подставка, ножка, чаша, ручки, крышка-шарик. Начало — центр низа.
function FleaKit.Trophy(color: Color3, scale: number, handles: boolean?): { Brick }
	local s = scale
	local out = {
		B(V(0.9, 0.3, 0.9) * s, V(0, 0.15, 0) * s, C.graphite, DECOR),
		B(V(0.5, 0.3, 0.3) * s, CFrame.new(0, 0.55 * s, 0) * UPRIGHT, color, ROUND),
		B(V(0.7, 0.9, 0.9) * s, CFrame.new(0, 1.15 * s, 0) * UPRIGHT, color, ROUND),
		B(V(0.5, 0.5, 0.5) * s, V(0, 1.55 * s, 0), color:Lerp(C.white, 0.35), BALL),
	}
	if handles then
		for _, x in { -0.55, 0.55 } do
			table.insert(out, B(V(0.25, 0.55, 0.2) * s, V(x, 1.2, 0) * s, color:Lerp(C.goldDark, 0.4), DECOR))
		end
	end
	return out
end

-- Монета, лежащая на полу (толщина задаёт высоту верха: у соседних монет разная).
function FleaKit.Coin(x: number, z: number, thickness: number, size: number?): Brick
	local d = size or 0.9
	return B(V(thickness, d, d), CFrame.new(x, thickness / 2, z) * UPRIGHT, C.gold, ROUND)
end

-- Мешок с монетами размера scale: низ, круглое тело, горловина с золотой завязкой, монета-знак спереди.
function FleaKit.Sack(out: { Brick }, at: CFrame, scale: number)
	local s = scale
	FleaKit.Put(out, {
		B(V(2, 1.6, 2) * s, V(0, 0.8 * s, 0), C.burlap, DECOR),
		B(V(2.3, 2.3, 2.3) * s, V(0, 1.5 * s, 0), C.burlap, BALL),
		B(V(0.6, 0.9, 0.9) * s, CFrame.new(0, 2.75 * s, 0) * UPRIGHT, C.burlapDark, ROUND),
		B(V(0.2, 1.05, 1.05) * s, CFrame.new(0, 2.6 * s, 0) * UPRIGHT, C.goldDark, ROUND),
		B(V(0.2, 0.9, 0.9) * s, CFrame.new(0, 1.3 * s, -1.15 * s) * ALONG_Z, C.gold, ROUND),
	}, at)
end

-- Три мешка с монетами и рассыпанные монеты перед ними.
function FleaKit.CoinSacks(): { Brick }
	local out = {}
	FleaKit.Sack(out, CFrame.new(0, 0, 0), 1)
	FleaKit.Sack(out, CFrame.new(2.3, 0, 0.6) * CFrame.Angles(0, -0.5, 0), 0.8)
	FleaKit.Sack(out, CFrame.new(-2, 0, 0.9) * CFrame.Angles(0, 0.6, 0), 0.9)
	table.insert(out, FleaKit.Coin(-1, -2, 0.15))
	table.insert(out, FleaKit.Coin(-0.3, -1.7, 0.2))
	table.insert(out, FleaKit.Coin(0.4, -2.4, 0.25))
	table.insert(out, FleaKit.Coin(1.2, -1.9, 0.3))
	return out
end

-- Открытый сундук с золотом: окованный ящик, откинутая назад крышка, горка золота, самородки, самоцвет.
function FleaKit.GoldChest(): { Brick }
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
		FleaKit.Gem(0.7, V(0.2, 2.6, -0.4), C.purpleLight),
	}
end

-- Автомат с капсулами: тумба цвета color, монетоприёмник с ручкой, стеклянный купол с капсулами.
function FleaKit.CapsuleMachine(color: Color3): { Brick }
	local out = {
		B(V(2.4, 3, 2.4), V(0, 1.5, 0), color),
		B(V(1.4, 1.2, 0.2), V(0, 2.1, -1.3), C.graphite, DECOR),
		FleaKit.Neon(V(0.6, 0.15, 0.1), V(0, 2.45, -1.45), C.goldLight),
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
function FleaKit.Suitcases(): { Brick }
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

-- Ящики с неоном: большой ящик со светящейся крышкой, на нём ящик поменьше, рядом третий.
function FleaKit.NeonCrates(): { Brick }
	local out = {
		B(V(3, 2.4, 3), V(0, 1.2, 0), C.wood),
		B(V(3.1, 0.4, 3.1), V(0, 0.6, 0), C.woodDark, DECOR),
		B(V(3.1, 0.4, 3.1), V(0, 1.8, 0), C.woodDark, DECOR),
		FleaKit.Neon(V(2.4, 0.3, 2.4), V(0, 2.5, 0), C.purpleLight),
	}
	local upper = CFrame.new(0.2, 3.65, 0.1) * CFrame.Angles(0, 0.26, 0)
	table.insert(out, B(V(2.4, 2, 2.4), upper, C.wood))
	table.insert(out, B(V(2.5, 0.35, 2.5), upper * CFrame.new(0, -0.3, 0), C.woodDark, DECOR))
	table.insert(out, FleaKit.Neon(V(1.9, 0.25, 1.9), upper * CFrame.new(0, 1.1, 0), C.tealLight))
	local side = CFrame.new(3.7, 1, -0.6) * CFrame.Angles(0, -0.2, 0)
	table.insert(out, B(V(2.6, 2, 2.6), side, C.wood))
	table.insert(out, B(V(2.7, 0.35, 2.7), side * CFrame.new(0, 0.3, 0), C.woodDark, DECOR))
	table.insert(out, FleaKit.Neon(V(2, 0.25, 2), side * CFrame.new(0, 1.1, 0), C.orange))
	return out
end

-- Подарочные коробки-сюрпризы: стопка из коробок с лентами крест-накрест и бантом.
function FleaKit.GiftBoxes(): { Brick }
	local out = {}
	local boxes = {
		{ size = V(3, 2.4, 3), at = CFrame.new(0, 1.2, 0), color = C.purple, ribbon = C.gold },
		{
			size = V(2.2, 1.8, 2.2),
			at = CFrame.new(0.2, 3.3, 0.1) * CFrame.Angles(0, 0.4, 0),
			color = C.teal,
			ribbon = C.orangeLight,
		},
		{
			size = V(2, 2, 2),
			at = CFrame.new(3, 1, -0.4) * CFrame.Angles(0, -0.3, 0),
			color = C.orange,
			ribbon = C.cream,
		},
		{
			size = V(1.4, 1.2, 1.4),
			at = CFrame.new(0.1, 4.8, 0.2) * CFrame.Angles(0, -0.2, 0),
			color = C.red,
			ribbon = C.goldLight,
		},
	}
	for _, box in boxes do
		local s = box.size
		table.insert(out, B(s, box.at, box.color, DECOR))
		table.insert(out, B(V(s.X * 0.22, s.Y + 0.1, s.Z + 0.1), box.at, box.ribbon, DECOR))
		table.insert(out, B(V(s.X + 0.1, s.Y + 0.08, s.Z * 0.22), box.at, box.ribbon, DECOR))
		table.insert(
			out,
			B(V(s.X * 0.4, s.X * 0.4, s.X * 0.4), box.at * CFrame.new(0, s.Y / 2 + s.X * 0.12, 0), box.ribbon, BALL)
		)
	end
	return out
end

-- Пирамида золотых слитков: 3 + 2 + 1 в ряд, чуть повёрнута.
function FleaKit.GoldBars(): { Brick }
	local out = {}
	local bar = V(1.6, 0.6, 0.9)
	for row = 0, 2 do
		for i = 0, 2 - row do
			local x = (i - (2 - row) / 2) * 1.7
			local color = if (row + i) % 2 == 0 then C.gold else C.goldLight
			table.insert(out, B(bar, V(x, 0.3 + row * 0.6, row * 0.05), color, DECOR))
		end
	end
	return out
end

-- Уличный фонарь: тумба, столб, золотой пояс, кронштейн к −Z и светящийся фонарь цвета color (без света).
function FleaKit.Lamp(color: Color3): { Brick }
	return {
		B(V(1.6, 0.6, 1.6), V(0, 0.3, 0), C.graphite),
		B(V(0.6, 9.4, 0.6), V(0, 5.3, 0), C.graphiteDark),
		B(V(0.8, 0.6, 0.8), V(0, 6.5, 0), C.gold, DECOR),
		B(V(0.35, 0.35, 2.6), V(0, 9.6, -1.2), C.graphiteDark, DECOR),
		B(V(0.5, 0.9, 1.3), CFrame.new(0, 9.5, -2.35) * UPRIGHT, C.gold, ROUND),
		FleaKit.Neon(V(1.5, 1.5, 1.5), V(0, 8.5, -2.35), color),
		B(V(0.3, 0.7, 0.7), CFrame.new(0, 7.65, -2.35) * UPRIGHT, C.goldDark, ROUND),
		B(V(0.9, 0.9, 0.9), V(0, 10.3, 0), C.gold, BALL),
	}
end

-- Столб с подвесной вывеской редкости rarity: на кронштейне табличка цвета редкости (Stud-UI, UITokens) с названием
-- редкости с обеих сторон и самоцветами по старшинству (1 — обычный, 3 — эпический).
function FleaKit.RarityPole(rarity: string): { Brick }
	local color = UITokens.RarityColor(rarity)
	local out = {
		B(V(1.6, 0.4, 1.6), V(0, 0.2, 0), C.graphite),
		B(V(0.6, 11, 0.6), V(0, 5.9, 0), C.metal),
		B(V(0.5, 0.5, 5.2), V(0, 11.35, -2.15), C.graphite, DECOR), -- выступает за столб сзади (D36)
		FleaKit.Board(
			V(0.3, 3, 3.6),
			V(0, 8.2, -2.6),
			color,
			FleaKit.Label(Rarities.Names[rarity], { Enum.NormalId.Left, Enum.NormalId.Right })
		),
		B(V(0.2, 3.3, 3.9), V(0, 8.2, -2.6), C.goldDark, DECOR),
	}
	for _, z in { -1.2, -4 } do
		table.insert(out, B(V(0.12, 1.4, 0.12), V(0, 10.4, z), C.metal, DECOR))
	end
	local rank = Rarities.Rank(rarity)
	for k = 1, rank do
		table.insert(out, FleaKit.Gem(0.7, V(0, 10.3, -2.6 + (k - (rank + 1) / 2)), color))
	end
	return out
end

return FleaKit

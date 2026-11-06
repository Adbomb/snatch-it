-- Устройства защиты музея кодом (D37, D46) — временная Part-версия в стиле D48-C (пачка Pack4_d48_defense, рендеры
-- assets/concepts/d48/c2/devices): тёмно-синий, белый, золото; детали Glow — подсветка состояния (цвет States,
-- ставит DefenseService: дежурит — бирюзовый, сработал — красный, сломан — серый). Ловушка, капкан, робот-охранник,
-- усиленная дверь, лазер. Начало координат — центр устройства на уровне пола зала (у лазера — середина луча на полу,
-- луч вдоль X). Всё Plastic, кроме неона (подсветка, луч, глаз робота). Совпадающих граней нет: накладки выступают ≥ 0.1
-- или детали встык. Без загрузок в Roblox. Зависит от ModelBuilder.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)

local B = ModelBuilder.Brick
local V = Vector3.new
local hex = Color3.fromHex
local UPRIGHT = CFrame.Angles(0, 0, math.rad(90)) -- ось цилиндра вертикально
local ALONG_Z = CFrame.Angles(0, math.rad(90), 0)

local C = {
	navy = hex("26345E"),
	navyDark = hex("1A2440"),
	white = hex("F4F7FB"),
	gold = hex("E9B43C"),
	steel = hex("5E7186"),
	red = hex("FF3B3B"),
}

local NEON = { material = Enum.Material.Neon, name = "Glow", shadow = false }

local Defense = {}

-- Цвета подсветки по состояниям (как в defense_rigs.json фазы 2).
Defense.States = {
	idle = hex("39E1FF"),
	detect = hex("FFB020"),
	active = hex("FF3B3B"),
	attack = hex("FF3B3B"),
	hit = hex("F4F7FB"),
	broken = hex("3A3D46"),
	hack = hex("FF7A1A"),
	open = hex("4CE07A"),
}

local function disc(radius: number, height: number, y: number, color: Color3, extra: { [string]: any }?)
	local props: { [string]: any } = { shape = "Cylinder" }
	for k, v in extra or {} do
		props[k] = v
	end
	return B(V(height, radius * 2, radius * 2), CFrame.new(0, y, 0) * UPRIGHT, color, props)
end

-- Ловушка: плита с золотой рамкой, подсвеченная середина, золотые шипы.
function Defense.Trap(): { ModelBuilder.Brick }
	local bricks = {
		B(V(2.6, 0.2, 2.6), V(0, 0.1, 0), C.navy),
		B(V(2.2, 0.12, 2.2), V(0, 0.26, 0), C.gold),
		B(V(1.6, 0.06, 1.6), V(0, 0.35, 0), C.red, NEON),
	}
	for _, at in { V(-0.75, 0, -0.75), V(0.75, 0, -0.75), V(-0.75, 0, 0.75), V(0.75, 0, 0.75) } do
		table.insert(bricks, B(V(0.3, 0.5, 0.3), at + V(0, 0.57, 0), C.white))
	end
	return bricks
end

-- Капкан: круглое основание, две стальные челюсти, подсвеченное кольцо.
function Defense.Snare(): { ModelBuilder.Brick }
	return {
		disc(1.0, 0.2, 0.1, C.navy),
		disc(0.75, 0.06, 0.23, C.red, NEON),
		B(V(1.7, 0.45, 0.24), V(0, 0.425, -0.72), C.steel),
		B(V(1.7, 0.45, 0.24), V(0, 0.425, 0.72), C.steel),
		disc(0.25, 0.3, 0.4, C.gold),
	}
end

-- Робот-охранник: стоит на месте, лицо −Z (визор «Eye» — неон, над ним шкала HP).
function Defense.Robot(): { ModelBuilder.Brick }
	return {
		B(V(1.8, 0.8, 1.4), V(0, 0.4, 0), C.navy),
		B(V(2.4, 2.4, 1.8), V(0, 2.0, 0), C.white),
		B(V(1.4, 0.4, 0.1), V(0, 2.4, -0.95), C.red, NEON),
		B(V(0.5, 1.8, 0.6), V(-1.45, 2.0, 0), C.navy),
		B(V(0.5, 1.8, 0.6), V(1.45, 2.0, 0), C.navy),
		B(V(1.8, 1.3, 1.5), V(0, 3.85, 0), C.white),
		B(
			V(1.4, 0.35, 0.12),
			V(0, 3.95, -0.81),
			C.red,
			{ material = Enum.Material.Neon, name = "Eye", shadow = false }
		),
		B(V(0.2, 0.7, 0.2), V(0, 4.85, 0), C.gold),
		B(V(0.4, 0.4, 0.4), V(0, 5.4, 0), C.red, NEON),
	}
end

-- Усиленная дверь в проёме входа (12 × 10): полотно с зазором 0.1 от откосов, золотые полосы, штурвал замка и лампа
-- выступают вперёд.
function Defense.Door(size: Vector3): { ModelBuilder.Brick }
	local w, h, d = size.X - 0.2, size.Y - 0.1, size.Z
	return {
		B(V(w, h, d), V(0, h / 2, 0), C.navy, { name = "Panel" }),
		B(V(w, 0.5, d + 0.2), V(0, 1.2, 0), C.gold),
		B(V(w, 0.5, d + 0.2), V(0, h - 1.2, 0), C.gold),
		B(V(d + 0.4, 2.4, 2.4), CFrame.new(0, h / 2, 0) * ALONG_Z, C.gold, { shape = "Cylinder" }),
		B(V(d + 0.6, 0.9, 0.9), CFrame.new(0, h / 2, 0) * ALONG_Z, C.steel, { shape = "Cylinder" }),
		B(V(0.8, 0.5, d + 0.3), V(0, h - 0.4, 0), C.red, NEON),
	}
end

-- Лазер поперёк прохода: две стойки с золотыми колпаками и подсвеченными излучателями, луч на высоте y длиной length.
function Defense.Laser(length: number, y: number): { ModelBuilder.Brick }
	local half = length / 2
	local bricks = {}
	for _, x in { -half, half } do
		table.insert(bricks, B(V(0.7, y + 0.6, 0.7), V(x, (y + 0.6) / 2, 0), C.navy))
		table.insert(bricks, B(V(0.9, 0.3, 0.9), V(x, y + 0.75, 0), C.gold))
		table.insert(bricks, B(V(0.8, 0.3, 0.8), V(x, y, 0), C.red, NEON))
	end
	table.insert(
		bricks,
		B(
			V(length - 0.8, 0.16, 0.16),
			V(0, y, 0),
			C.red,
			{ material = Enum.Material.Neon, name = "Beam", shadow = false }
		)
	)
	return bricks
end

return Defense

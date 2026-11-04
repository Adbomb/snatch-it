-- Устройства защиты музея кодом (D37, D46): ловушка, капкан, робот-охранник, усиленная дверь, лазер. Начало
-- координат — центр устройства на уровне пола зала (у лазера — середина луча на полу, луч вдоль X). Всё Plastic,
-- луч и глаз робота — Neon. Совпадающих граней нет: накладки выступают ≥ 0.1 или детали встык. Без загрузок в Roblox.
-- Зависит от ModelBuilder.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)

local B = ModelBuilder.Brick
local V = Vector3.new
local hex = Color3.fromHex

local C = {
	steel = hex("4A5361"),
	steelDark = hex("2E343E"),
	hazard = hex("FFC93C"),
	red = hex("E8323C"),
	teal = hex("2CB5A8"),
	tealDark = hex("1C7C74"),
	black = hex("1E1E24"),
	white = hex("E8ECF2"),
}

local Defense = {}

-- Ловушка: плита с шипами и красной кнопкой.
function Defense.Trap(): { ModelBuilder.Brick }
	local bricks = {
		B(V(2.4, 0.2, 2.4), V(0, 0.1, 0), C.steelDark),
		B(V(0.9, 0.25, 0.9), V(0, 0.325, 0), C.red),
	}
	for _, at in { V(-0.8, 0, -0.8), V(0.8, 0, -0.8), V(-0.8, 0, 0.8), V(0.8, 0, 0.8) } do
		table.insert(bricks, B(V(0.32, 0.55, 0.32), at + V(0, 0.475, 0), C.hazard))
	end
	return bricks
end

-- Капкан: основание, две челюсти, пружина.
function Defense.Snare(): { ModelBuilder.Brick }
	return {
		B(V(1.9, 0.18, 1.9), V(0, 0.09, 0), C.steelDark),
		B(V(1.7, 0.45, 0.24), V(0, 0.405, -0.72), C.steel),
		B(V(1.7, 0.45, 0.24), V(0, 0.405, 0.72), C.steel),
		B(V(0.5, 0.3, 0.5), V(0, 0.33, 0), C.hazard),
	}
end

-- Робот-охранник: стоит на месте, лицо −Z (глаз — Neon).
function Defense.Robot(): { ModelBuilder.Brick }
	return {
		B(V(1.6, 1.2, 1.2), V(0, 0.6, 0), C.steelDark),
		B(V(2.4, 2.2, 1.8), V(0, 2.3, 0), C.teal),
		B(V(0.5, 1.6, 0.6), V(-1.45, 2.3, 0), C.tealDark),
		B(V(0.5, 1.6, 0.6), V(1.45, 2.3, 0), C.tealDark),
		B(V(1.6, 1.2, 1.4), V(0, 4.0, 0), C.white),
		B(V(1.0, 0.3, 0.12), V(0, 4.1, -0.76), C.red, { material = Enum.Material.Neon, name = "Eye" }),
		B(V(0.2, 0.8, 0.2), V(0, 5.0, 0), C.steel),
		B(V(0.4, 0.4, 0.4), V(0, 5.6, 0), C.red),
	}
end

-- Усиленная дверь в проёме входа (12 × 10): полотно с зазором 0.1 от откосов, полосы и замок выступают на 0.1.
function Defense.Door(size: Vector3): { ModelBuilder.Brick }
	local w, h, d = size.X - 0.2, size.Y - 0.1, size.Z
	return {
		B(V(w, h, d), V(0, h / 2, 0), C.steelDark, { name = "Panel" }),
		B(V(w, 0.5, d + 0.2), V(0, 1.2, 0), C.hazard),
		B(V(w, 0.5, d + 0.2), V(0, h - 1.2, 0), C.hazard),
		B(V(1.4, 1.4, d + 0.4), V(0, h / 2, 0), C.steel),
		B(V(0.5, 0.5, d + 0.6), V(0, h / 2, 0), C.red),
	}
end

-- Лазер поперёк прохода: два излучателя и луч на высоте y длиной length (вдоль X).
function Defense.Laser(length: number, y: number): { ModelBuilder.Brick }
	local half = length / 2
	return {
		B(V(0.6, y + 0.8, 0.6), V(-half, (y + 0.8) / 2, 0), C.steelDark),
		B(V(0.6, y + 0.8, 0.6), V(half, (y + 0.8) / 2, 0), C.steelDark),
		B(V(length - 0.6, 0.16, 0.16), V(0, y, 0), C.red, { material = Enum.Material.Neon, name = "Beam" }),
	}
end

return Defense

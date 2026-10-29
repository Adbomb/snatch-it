-- Декор зон добычи и постамент под предмет. Всё в локальных координатах зоны: начало — центр пола,
-- вход на стороне -Z (z = -30), выход в следующую зону на +Z (z = 30), x — поперёк коридора. Декор не заходит
-- на постаменты, проход по центру (|x| < 8) и место босса. Простые кирпичи; в шаге 3 их заменят модели
-- из Blender (D28). Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick
local DECOR = { collide = false, shadow = false }
local UPRIGHT = CFrame.Angles(0, 0, math.rad(90)) -- ось цилиндра вертикально

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

local ZoneDecor = {}

-- Постамент высотой 2.5: основание, колонна, площадка цвета акцента. Начало — центр основания.
function ZoneDecor.Pedestal(accent: Color3): { ModelBuilder.Brick }
	return {
		B(Vector3.new(4.4, 1, 4.4), Vector3.new(0, 0.5, 0), Palette.Stone),
		B(Vector3.new(3, 1, 3), Vector3.new(0, 1.5, 0), Palette.White),
		B(Vector3.new(3.8, 0.5, 3.8), Vector3.new(0, 2.25, 0), accent),
	}
end

-- Свалка: горы хлама в углах, шины, бочки.
function ZoneDecor.Junk(): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local random = Random.new(11)
	local junk = { hex("8D6E63"), hex("9E9E9E"), hex("C0CA33"), hex("E57373"), hex("64B5F6"), hex("FFB74D"), hex("795548") }
	for _, corner in { Vector2.new(-22, -20), Vector2.new(22, -20), Vector2.new(-24, 25), Vector2.new(24, 25) } do
		local y = 0
		for layer = 1, 4 do
			local spread = 6 - layer
			for _ = 1, 3 do
				local size = Vector3.new(random:NextNumber(2, 4.5), random:NextNumber(1, 2.4), random:NextNumber(2, 4.5))
				local at = CFrame.new(
					corner.X + random:NextNumber(-spread, spread),
					y + size.Y / 2,
					corner.Y + random:NextNumber(-spread, spread)
				) * CFrame.Angles(0, random:NextNumber(0, math.pi), 0)
				table.insert(bricks, B(size, at, junk[random:NextInteger(1, #junk)]))
			end
			y += 1.6
		end
	end
	for i, spot in { Vector2.new(-14, -24), Vector2.new(-11, -23), Vector2.new(14, 26) } do
		-- Шины лежат плашмя.
		table.insert(bricks, B(Vector3.new(1.4, 4, 4), CFrame.new(spot.X, 0.7 + (i - 1) % 2 * 1.4, spot.Y) * UPRIGHT, Palette.Black, {
			shape = "Cylinder",
		}))
	end
	for _, spot in { Vector2.new(26, -4), Vector2.new(26, 0), Vector2.new(-26, 8) } do
		table.insert(bricks, B(Vector3.new(4, 2.6, 2.6), CFrame.new(spot.X, 2, spot.Y) * UPRIGHT, hex("B23B2B"), { shape = "Cylinder" }))
	end
	return bricks
end

-- Барахолка: цветные коврики под постаментами (ларьки и ящики ставит WorldBuilder).
function ZoneDecor.Flea(pedestals: { Vector2 }): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local rugs = { hex("E53935"), hex("8E24AA"), hex("1E88E5"), hex("FB8C00"), hex("43A047") }
	for i, spot in pedestals do
		table.insert(bricks, B(Vector3.new(8, 0.1, 8), Vector3.new(spot.X, 0.05, spot.Y), rugs[(i - 1) % #rugs + 1], DECOR))
		table.insert(bricks, B(Vector3.new(6.4, 0.12, 6.4), Vector3.new(spot.X, 0.06, spot.Y), Palette.White, DECOR))
	end
	-- Столы с мелочью вдоль боковых заборов.
	for _, x in { -26, 26 } do
		table.insert(bricks, B(Vector3.new(4, 2.6, 12), Vector3.new(x, 1.3, 8), Palette.Wood))
		for i = 1, 4 do
			table.insert(bricks, B(Vector3.new(1.4, 1, 1.4), Vector3.new(x, 3.1, 8 - 6 + i * 2.4), rugs[i], DECOR))
		end
	end
	return bricks
end

-- Склад: жёлтая разметка и стеллажи с коробками (ящики ставит WorldBuilder).
function ZoneDecor.Warehouse(): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local yellow = hex("FFC400")
	for _, x in { -7, 7 } do
		table.insert(bricks, B(Vector3.new(1, 0.1, 50), Vector3.new(x, 0.05, 0), yellow, DECOR))
	end
	local boxColors = { hex("A1887F"), hex("8D6E63"), hex("BCAAA4") }
	for _, rackX in { -20, 20 } do
		local z, length, height = 27, 16, 10
		for _, dx in { -length / 2, length / 2 } do
			for _, dz in { -1.6, 1.6 } do
				table.insert(bricks, B(Vector3.new(0.6, height, 0.6), Vector3.new(rackX + dx, height / 2, z + dz), hex("1565C0")))
			end
		end
		for shelf = 1, 3 do
			local y = shelf * 3.2
			table.insert(bricks, B(Vector3.new(length + 0.6, 0.4, 3.8), Vector3.new(rackX, y, z), hex("FF7043")))
			for box = 1, 3 do
				local size = Vector3.new(3.4, 2.2, 2.8)
				table.insert(
					bricks,
					B(size, Vector3.new(rackX - length / 3 + (box - 1) * length / 3, y + 0.2 + size.Y / 2, z), boxColors[(shelf + box) % 3 + 1], DECOR)
				)
			end
		end
	end
	return bricks
end

-- Банк: «мраморный» пол в шахматку (светлые плитки), колонны, сейфы у задней стены, золотая окантовка.
function ZoneDecor.Bank(size: number): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local tile = 6
	local count = math.floor(size / tile)
	local marbleA, marbleB = hex("F5F5F5"), hex("B0BEC5")
	for ix = 0, count - 1 do
		for iz = 0, count - 1 do
			if (ix + iz) % 2 == 0 then
				local x = -size / 2 + (ix + 0.5) * tile
				local z = -size / 2 + (iz + 0.5) * tile
				table.insert(bricks, B(Vector3.new(tile, 0.1, tile), Vector3.new(x, 0.05, z), marbleB, {
					collide = false,
					shadow = false,
				}))
			end
		end
	end
	table.insert(bricks, B(Vector3.new(size, 0.08, size), Vector3.new(0, 0.04, 0), marbleA, {
		collide = false,
		shadow = false,
	}))
	local gold = hex("FFB800")
	for _, x in { -24, 24 } do
		for _, z in { -6, 14 } do
			table.insert(bricks, B(Vector3.new(3, 1, 3), Vector3.new(x, 0.5, z), gold))
			table.insert(bricks, B(Vector3.new(2.2, 10, 2.2), Vector3.new(x, 6, z), Palette.White))
			table.insert(bricks, B(Vector3.new(3, 1, 3), Vector3.new(x, 11.5, z), gold))
		end
	end
	for _, x in { -21, -14, 14, 21 } do
		local z = 27
		table.insert(bricks, B(Vector3.new(5, 6, 3.6), Vector3.new(x, 3, z), hex("546E7A")))
		table.insert(bricks, B(Vector3.new(0.4, 2.2, 2.2), CFrame.new(x, 3.6, z - 2) * CFrame.Angles(0, math.rad(90), 0), gold, {
			shape = "Cylinder",
			collide = false,
		}))
		table.insert(bricks, B(Vector3.new(0.6, 0.6, 1.2), Vector3.new(x + 1.6, 2.4, z - 2.2), Palette.Metal, DECOR))
	end
	return bricks
end

-- Ступенчатая пирамида из квадратных плит: base — сторона нижней, steps — число ступеней.
local function stepped(bricks: { ModelBuilder.Brick }, at: Vector2, base: number, steps: number, step: number, color: Color3)
	for i = 0, steps - 1 do
		local side = base * (1 - i / steps)
		table.insert(bricks, B(Vector3.new(side, step, side), Vector3.new(at.X, (i + 0.5) * step, at.Y), color))
	end
end

-- Пустыня: две пирамиды и кактусы.
function ZoneDecor.Desert(): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	stepped(bricks, Vector2.new(-21, -19), 12, 5, 2, hex("E0B060"))
	stepped(bricks, Vector2.new(22, 24), 10, 4, 2, hex("D9A24E"))
	local cactus = hex("2E9E40")
	for i, spot in { Vector2.new(24, -22), Vector2.new(-26, 10), Vector2.new(26, 8), Vector2.new(-23, 26) } do
		local h = 5 + i % 2 * 2
		local side = if i % 2 == 0 then 1 else -1
		table.insert(bricks, B(Vector3.new(1.6, h, 1.6), Vector3.new(spot.X, h / 2, spot.Y), cactus))
		table.insert(bricks, B(Vector3.new(1.6, 1.2, 1.2), Vector3.new(spot.X + side * 1.4, h * 0.5, spot.Y), cactus))
		table.insert(bricks, B(Vector3.new(1.2, 2.4, 1.2), Vector3.new(spot.X + side * 1.8, h * 0.5 + 1.8, spot.Y), cactus))
	end
	return bricks
end

-- Ледник: сугробы, прозрачные ледяные пики и глыбы.
function ZoneDecor.Glacier(): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local ice = { material = Enum.Material.Glass, transparency = 0.25 }
	local iceColor, snow = hex("9BE0FF"), Palette.White
	for _, spot in { Vector2.new(-23, -21), Vector2.new(23, -21), Vector2.new(-24, 25), Vector2.new(24, 25) } do
		table.insert(bricks, B(Vector3.new(7, 1.2, 7), Vector3.new(spot.X, 0.6, spot.Y), snow))
		for i, h in { 9, 6, 4 } do
			local dx, dz = (i - 2) * 2, (i % 2) * 2 - 1
			table.insert(bricks, B(Vector3.new(1.8, h, 1.8), Vector3.new(spot.X + dx, h / 2 + 1.2, spot.Y + dz), iceColor, ice))
		end
	end
	for _, spot in { Vector2.new(-26, 6), Vector2.new(26, 10) } do
		table.insert(bricks, B(Vector3.new(4, 3, 6), Vector3.new(spot.X, 1.5, spot.Y), iceColor, ice))
		table.insert(bricks, B(Vector3.new(5, 0.8, 8), Vector3.new(spot.X, 0.4, spot.Y), snow))
	end
	return bricks
end

-- Джунгли: камни с мхом и папоротники (деревья ставит WorldBuilder).
function ZoneDecor.Jungle(): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local rock, moss, leaf = hex("6D7B6A"), hex("3E7D2E"), hex("43A047")
	for _, spot in { Vector2.new(-26, 4), Vector2.new(26, 12), Vector2.new(-22, -24) } do
		table.insert(bricks, B(Vector3.new(5, 3, 5), Vector3.new(spot.X, 1.5, spot.Y), rock))
		table.insert(bricks, B(Vector3.new(5.2, 0.4, 5.2), Vector3.new(spot.X, 3.2, spot.Y), moss, DECOR))
	end
	for i, spot in { Vector2.new(24, -22), Vector2.new(-25, 16), Vector2.new(25, 26), Vector2.new(-14, 27) } do
		table.insert(bricks, B(Vector3.new(0.5, 3, 0.5), Vector3.new(spot.X, 1.5, spot.Y), hex("2E7D32"), DECOR))
		for j = 0, 2 do
			local frame = CFrame.new(spot.X, 3, spot.Y) * CFrame.Angles(0, math.rad(j * 120 + i * 20), math.rad(-20))
			table.insert(bricks, B(Vector3.new(1.2, 0.2, 3.6), frame * CFrame.new(0, 0, 1.6), leaf, DECOR))
		end
	end
	return bricks
end

-- Вулкан: тёмные камни, лавовые озёра (неон) и маленький конус с жерлом в углу.
function ZoneDecor.Volcano(): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local basalt, lava = hex("3E2723"), hex("FF6D00")
	local glow = { material = Enum.Material.Neon, collide = false, shadow = false }
	stepped(bricks, Vector2.new(22, 24), 12, 5, 2.4, basalt)
	table.insert(bricks, B(Vector3.new(2.6, 0.4, 2.6), Vector3.new(22, 12.2, 24), lava, glow))
	for _, spot in { Vector2.new(-24, -20), Vector2.new(24, -18), Vector2.new(-24, 24) } do
		table.insert(bricks, B(Vector3.new(8, 0.2, 6), Vector3.new(spot.X, 0.1, spot.Y), lava, glow))
		table.insert(bricks, B(Vector3.new(3, 2.4, 3), CFrame.new(spot.X + 4, 1.2, spot.Y + 3) * CFrame.Angles(0, 0.5, 0), basalt))
	end
	return bricks
end

-- Космопорт: посадочная площадка с ракетой, антенна и светящиеся ящики.
function ZoneDecor.Spaceport(): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local pad, white, red = hex("546E7A"), Palette.White, hex("E53935")
	local at = Vector2.new(-22, 22)
	table.insert(bricks, B(Vector3.new(0.4, 12, 12), CFrame.new(at.X, 0.2, at.Y) * UPRIGHT, pad, { shape = "Cylinder" }))
	-- Ракета снизу вверх: корпус, кольцо, нос, кончик (диаметр, высота).
	local y = 0.4
	for i, piece in { { 3.6, 10 }, { 3, 2 }, { 2, 2 }, { 1, 1.4 } } do
		local color = if i % 2 == 0 then red else white
		table.insert(bricks, B(Vector3.new(piece[2], piece[1], piece[1]), CFrame.new(at.X, y + piece[2] / 2, at.Y) * UPRIGHT, color, {
			shape = "Cylinder",
		}))
		y += piece[2]
	end
	for j = 0, 2 do
		local frame = CFrame.new(at.X, 2.4, at.Y) * CFrame.Angles(0, math.rad(j * 120), 0)
		table.insert(bricks, B(Vector3.new(0.4, 3, 2.4), frame * CFrame.new(0, 0, 2.6), red))
	end
	local dish = Vector2.new(24, -20)
	table.insert(bricks, B(Vector3.new(1, 6, 1), Vector3.new(dish.X, 3, dish.Y), Palette.Metal))
	table.insert(bricks, B(Vector3.new(0.4, 6, 6), CFrame.new(dish.X, 6.5, dish.Y) * CFrame.Angles(0, 0, math.rad(60)), white, {
		shape = "Cylinder",
	}))
	for _, spot in { Vector2.new(-26, -6), Vector2.new(26, 8) } do
		table.insert(bricks, B(Vector3.new(3, 3, 3), Vector3.new(spot.X, 1.5, spot.Y), hex("90A4AE")))
		table.insert(bricks, B(Vector3.new(3.2, 0.3, 3.2), Vector3.new(spot.X, 3.15, spot.Y), hex("00E5FF"), {
			material = Enum.Material.Neon,
			collide = false,
		}))
	end
	return bricks
end

-- Замок: башни с зубцами по углам, знамёна и красная дорожка по центру.
function ZoneDecor.Castle(): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local stone, dark, banner = hex("BDBDBD"), hex("757575"), hex("C62828")
	for _, spot in { Vector2.new(-25, -25), Vector2.new(25, -25), Vector2.new(-25, 25), Vector2.new(25, 25) } do
		for i = 0, 4 do
			table.insert(bricks, B(Vector3.new(7, 2.4, 7), Vector3.new(spot.X, i * 2.4 + 1.2, spot.Y), if i % 2 == 0 then stone else dark))
		end
		for _, d in { Vector2.new(-2.5, -2.5), Vector2.new(2.5, -2.5), Vector2.new(-2.5, 2.5), Vector2.new(2.5, 2.5) } do
			table.insert(bricks, B(Vector3.new(1.6, 1.6, 1.6), Vector3.new(spot.X + d.X, 12.8, spot.Y + d.Y), stone))
		end
		table.insert(bricks, B(Vector3.new(0.2, 4, 2.4), Vector3.new(spot.X - math.sign(spot.X) * 3.6, 8, spot.Y), banner, DECOR))
	end
	table.insert(bricks, B(Vector3.new(6, 0.1, 56), Vector3.new(0, 0.05, 0), banner, DECOR))
	return bricks
end

return ZoneDecor

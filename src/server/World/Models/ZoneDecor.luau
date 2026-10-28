-- Декор зон добычи и постамент под предмет. Всё в локальных координатах зоны: начало — центр пола,
-- ворота на стороне -Z (z = -30), x — вдоль ворот. Декор не заходит на постаменты, проход от ворот
-- и место стража. Зависит от ModelBuilder, Palette.

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
	for i, spot in { Vector2.new(-8, -24), Vector2.new(-5, -23), Vector2.new(9, 26) } do
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
	for _, x in { -14, 0, 14 } do
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

return ZoneDecor

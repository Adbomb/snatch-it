-- Модели площади: фонтан с водой и ларёк с полосатым навесом.
-- Начало координат — центр основания, у ларька прилавок на стороне -Z. Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick
local DECOR = { collide = false, shadow = false }
local WATER = { material = Enum.Material.Glass, transparency = 0.3, collide = false, shadow = false }

local Plaza = {}

function Plaza.Fountain(): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local size, rim, height = 18, 1.5, 2
	-- Бортик бассейна из четырёх брусков в два цвета.
	for i, offset in { Vector3.new(0, 0, -1), Vector3.new(0, 0, 1), Vector3.new(-1, 0, 0), Vector3.new(1, 0, 0) } do
		local alongX = offset.X == 0
		local dims = if alongX then Vector3.new(size, height, rim) else Vector3.new(rim, height, size - 2 * rim)
		local color = if i % 2 == 0 then Palette.Stone else Palette.White
		table.insert(bricks, B(dims, offset * (size / 2 - rim / 2) + Vector3.new(0, height / 2, 0), color))
	end
	table.insert(bricks, B(Vector3.new(size - 2 * rim, 1.2, size - 2 * rim), Vector3.new(0, 0.9, 0), Palette.Water, WATER))
	-- Колонна, чаша, верхняя чаша и струя.
	table.insert(bricks, B(Vector3.new(3, 4, 3), Vector3.new(0, 2, 0), Palette.Stone))
	table.insert(bricks, B(Vector3.new(8, 1, 8), Vector3.new(0, 4.5, 0), Palette.White))
	table.insert(bricks, B(Vector3.new(6.6, 0.4, 6.6), Vector3.new(0, 5.1, 0), Palette.Water, WATER))
	table.insert(bricks, B(Vector3.new(1.6, 2.4, 1.6), Vector3.new(0, 6.2, 0), Palette.Stone))
	table.insert(bricks, B(Vector3.new(3.4, 0.6, 3.4), Vector3.new(0, 7.6, 0), Palette.White))
	table.insert(bricks, B(Vector3.new(0.8, 3.2, 0.8), Vector3.new(0, 9.5, 0), Palette.Water, {
		material = Enum.Material.Neon,
		transparency = 0.25,
		collide = false,
		shadow = false,
	}))
	return bricks
end

function Plaza.Stall(stripeA: Color3, stripeB: Color3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local w, d = 9, 6
	-- Прилавок, задняя стенка, стойки.
	table.insert(bricks, B(Vector3.new(w, 3, 1.6), Vector3.new(0, 1.5, -d / 2 + 0.8), Palette.Wood))
	table.insert(bricks, B(Vector3.new(w, 0.4, 2), Vector3.new(0, 3.2, -d / 2 + 0.8), Palette.WoodDark, DECOR))
	table.insert(bricks, B(Vector3.new(w, 6, 0.6), Vector3.new(0, 3, d / 2 - 0.3), Palette.Wood))
	for _, x in { -w / 2 + 0.3, w / 2 - 0.3 } do
		table.insert(bricks, B(Vector3.new(0.6, 7, 0.6), Vector3.new(x, 3.5, -d / 2 + 0.3), Palette.WoodDark, DECOR))
	end
	-- Полосатый навес с наклоном вперёд.
	local stripes = 6
	local stripeWidth = (w + 1) / stripes
	local tilt = CFrame.new(0, 7.4, 0) * CFrame.Angles(math.rad(-12), 0, 0)
	for i = 1, stripes do
		local x = -(w + 1) / 2 + (i - 0.5) * stripeWidth
		local color = if i % 2 == 0 then stripeB else stripeA
		table.insert(bricks, B(Vector3.new(stripeWidth, 0.4, d + 1.5), tilt * CFrame.new(x, 0, -0.5), color, DECOR))
	end
	-- Товар на прилавке.
	for i, color in { stripeA, Palette.Lamp, Palette.HouseWalls[1] } do
		table.insert(
			bricks,
			B(Vector3.new(1.2, 1, 1.2), Vector3.new(-2.5 + (i - 1) * 2.5, 3.9, -d / 2 + 0.8), color, DECOR)
		)
	end
	return bricks
end

return Plaza

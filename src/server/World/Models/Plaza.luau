-- Ларёк с полосатым навесом (лавки поля, барахолка).
-- Начало координат — центр основания, у ларька прилавок на стороне -Z. Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick
local DECOR = { collide = false, shadow = false }

local Plaza = {}

function Plaza.Stall(stripeA: Color3, stripeB: Color3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local w, d = 9, 6
	-- Прилавок, задняя стенка, стойки.
	-- Прилавок на 0.1 уже с каждой стороны: стойки выступают, грани не совпадают (D36).
	table.insert(bricks, B(Vector3.new(w - 0.2, 3, 1.6), Vector3.new(0, 1.5, -d / 2 + 0.8), Palette.Wood))
	table.insert(bricks, B(Vector3.new(w - 0.2, 0.4, 2), Vector3.new(0, 3.2, -d / 2 + 0.8), Palette.WoodDark, DECOR))
	table.insert(bricks, B(Vector3.new(w, 6, 0.6), Vector3.new(0, 3, d / 2 - 0.3), Palette.Wood))
	for _, x in { -w / 2 + 0.3, w / 2 - 0.3 } do
		table.insert(bricks, B(Vector3.new(0.6, 7, 0.6), Vector3.new(x, 3.5, -d / 2 + 0.2), Palette.WoodDark, DECOR))
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

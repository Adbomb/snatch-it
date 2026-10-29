-- Стена поперёк коридора зон с проёмом посередине: кладка из кирпичей цвета акцента зоны и белых.
-- Начало координат — центр проёма на земле, стена вдоль X. Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick

local THICKNESS = 2
local BRICK_LENGTH = 6
local BRICK_HEIGHT = 2

-- halfWidth — от проёма до боковой стены, door — ширина проёма, height — высота.
return function(halfWidth: number, door: number, height: number, accent: Color3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local rows = math.ceil(height / BRICK_HEIGHT)
	for _, side in { -1, 1 } do
		local from, to = door / 2, halfWidth
		for row = 0, rows - 1 do
			-- Кладка со сдвигом через ряд.
			local t = from - (if row % 2 == 0 then 0 else BRICK_LENGTH / 2)
			local index = 0
			while t < to do
				local a, b = math.max(t, from), math.min(t + BRICK_LENGTH, to)
				if b - a > 0.05 then
					local color = if (index + row) % 2 == 0 then accent else Palette.White
					table.insert(
						bricks,
						B(Vector3.new(b - a, BRICK_HEIGHT, THICKNESS), Vector3.new(side * (a + b) / 2, (row + 0.5) * BRICK_HEIGHT, 0), color)
					)
				end
				index += 1
				t += BRICK_LENGTH
			end
		end
	end
	return bricks
end

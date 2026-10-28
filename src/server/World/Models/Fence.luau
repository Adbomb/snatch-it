-- Забор зоны по квадрату со стороной size и проёмом gap посередине лицевой стороны (-Z).
-- Начало координат — центр квадрата на земле. Зависит от ModelBuilder.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)

local B = ModelBuilder.Brick

local POST_STEP = 6
local HEIGHT = 5

-- Пролёт от a до b (в плоскости XZ): столбики через POST_STEP и две перекладины.
local function run(bricks: { ModelBuilder.Brick }, a: Vector3, b: Vector3, post: Color3, rail: Color3)
	local length = (b - a).Magnitude
	if length < 0.5 then
		return
	end
	local dir = (b - a).Unit
	local frame = CFrame.lookAt((a + b) / 2, (a + b) / 2 + dir)
	for _, y in { HEIGHT * 0.4, HEIGHT * 0.8 } do
		table.insert(bricks, B(Vector3.new(0.5, 0.6, length), frame * CFrame.new(0, y, 0), rail, { shadow = false }))
	end
	local count = math.max(1, math.floor(length / POST_STEP))
	for i = 0, count do
		local p = a + dir * (length * i / count)
		table.insert(bricks, B(Vector3.new(0.9, HEIGHT, 0.9), p + Vector3.new(0, HEIGHT / 2, 0), post, { shadow = false }))
	end
end

return function(size: number, gap: number, post: Color3, rail: Color3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local h = size / 2
	local c = {
		Vector3.new(-h, 0, -h),
		Vector3.new(h, 0, -h),
		Vector3.new(h, 0, h),
		Vector3.new(-h, 0, h),
	}
	-- Лицевая сторона с проёмом, затем три глухие.
	run(bricks, c[1], Vector3.new(-gap / 2, 0, -h), post, rail)
	run(bricks, Vector3.new(gap / 2, 0, -h), c[2], post, rail)
	run(bricks, c[2], c[3], post, rail)
	run(bricks, c[3], c[4], post, rail)
	run(bricks, c[4], c[1], post, rail)
	return bricks
end

-- Кубическое дерево трёх размеров: ствол из коричневых брусков, крона из зелёных кубов.
-- Начало координат — центр основания ствола. Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick

-- trunk: толщина и высота ствола; crowns: {ширина, высота} слоёв кроны снизу вверх; side — боковые кубы.
local SIZES = {
	S = { trunk = Vector2.new(1.6, 4), crowns = { { 6, 4 }, { 4, 3 } }, side = 0 },
	M = { trunk = Vector2.new(2, 6), crowns = { { 9, 4 }, { 7, 4 }, { 4, 3 } }, side = 0 },
	L = { trunk = Vector2.new(2.6, 8), crowns = { { 12, 5 }, { 9, 5 }, { 6, 4 } }, side = 2 },
}

return function(size: string, colorIndex: number): { ModelBuilder.Brick }
	local spec = SIZES[size] or SIZES.M
	local leaves = Palette.Leaves[(colorIndex - 1) % #Palette.Leaves + 1]
	local bricks: { ModelBuilder.Brick } = {}
	local t = spec.trunk
	-- Ствол из двух брусков разного оттенка.
	table.insert(bricks, B(Vector3.new(t.X, t.Y / 2, t.X), Vector3.new(0, t.Y / 4, 0), Palette.Trunk))
	table.insert(bricks, B(Vector3.new(t.X * 0.85, t.Y / 2, t.X * 0.85), Vector3.new(0, t.Y * 3 / 4, 0), Palette.WoodDark))
	local y = t.Y
	for index, crown in spec.crowns do
		local color = if index % 2 == 0 then leaves:Lerp(Palette.White, 0.12) else leaves
		table.insert(bricks, B(Vector3.new(crown[1], crown[2], crown[1]), Vector3.new(0, y + crown[2] / 2, 0), color))
		y += crown[2]
	end
	-- У большого дерева — кубы-«ветки» по бокам нижнего слоя.
	local base = spec.crowns[1]
	for i = 1, spec.side do
		local sign = if i == 1 then 1 else -1
		table.insert(
			bricks,
			B(Vector3.new(4, 3, 4), Vector3.new(sign * (base[1] / 2 + 1), t.Y + 1.5, -sign * 2), leaves, { collide = false })
		)
	end
	return bricks
end

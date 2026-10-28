-- Ворота: большая арка в конце аллеи и ворота зоны с вывеской. Вывеска — кирпич "SignBoard",
-- надпись на неё ставит WorldBuilder (грань Front = сторона -Z модели). Начало координат — центр
-- проёма на земле, лицевая сторона — -Z. Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick

local Gate = {}

-- Башня из кирпичей двух цветов вперемешку.
local function tower(bricks: { ModelBuilder.Brick }, x: number, size: number, height: number, a: Color3, b: Color3)
	local layer = 2
	local y = 0
	local i = 0
	while y < height do
		i += 1
		local h = math.min(layer, height - y)
		table.insert(bricks, B(Vector3.new(size, h, size), Vector3.new(x, y + h / 2, 0), if i % 2 == 0 then a else b))
		y += h
	end
	-- Зубцы наверху.
	for _, dx in { -size / 3, size / 3 } do
		table.insert(bricks, B(Vector3.new(size / 4, 1.5, size), Vector3.new(x + dx, height + 0.75, 0), a))
	end
end

-- Арка в конце аллеи: ширина проёма width.
function Gate.Alley(width: number): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local towerSize, height = 6, 18
	local half = width / 2 + towerSize / 2
	tower(bricks, -half, towerSize, height, Palette.HouseWalls[1], Palette.White)
	tower(bricks, half, towerSize, height, Palette.HouseWalls[1], Palette.White)
	table.insert(bricks, B(Vector3.new(width + towerSize * 2, 2, towerSize), Vector3.new(0, height - 3, 0), Palette.HouseWalls[3]))
	table.insert(
		bricks,
		B(Vector3.new(width * 0.7, 6, 1), Vector3.new(0, height - 7, -towerSize / 2 - 0.5), Palette.HouseWalls[2], {
			name = "SignBoard",
			material = Enum.Material.SmoothPlastic, -- табличка с текстом: без пупырышков
		})
	)
	return bricks
end

-- Ворота зоны: два столба, перекладина, вывеска цветом главной редкости зоны.
function Gate.Zone(width: number, signColor: Color3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local post, height = 2.4, 12
	for _, x in { -width / 2 - post / 2, width / 2 + post / 2 } do
		table.insert(bricks, B(Vector3.new(post, height, post), Vector3.new(x, height / 2, 0), Palette.WoodDark))
		table.insert(bricks, B(Vector3.new(post + 0.6, 1, post + 0.6), Vector3.new(x, height + 0.5, 0), signColor:Lerp(Palette.Black, 0.3)))
	end
	table.insert(bricks, B(Vector3.new(width + post * 2, 1.2, 1.2), Vector3.new(0, height - 0.6, 0), Palette.WoodDark))
	table.insert(
		bricks,
		B(Vector3.new(width + post * 2 + 4, 5, 0.8), Vector3.new(0, height + 3, 0), signColor, {
			name = "SignBoard",
			material = Enum.Material.SmoothPlastic,
		})
	)
	-- Обводка вывески тёмной рамкой (как UIStroke в UI_KIT).
	table.insert(
		bricks,
		B(Vector3.new(width + post * 2 + 4.6, 5.6, 0.6), Vector3.new(0, height + 3, 0.3), Palette.Black, { collide = false, shadow = false })
	)
	return bricks
end

return Gate

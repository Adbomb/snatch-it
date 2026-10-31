-- Ворота зоны (уровня) с вывеской. Вывеска — кирпич "SignBoard", надпись на неё ставит WorldBuilder
-- (грань Front = сторона -Z модели). Начало координат — центр проёма на земле, лицевая сторона — -Z.
-- Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick

local Gate = {}

-- Толщина стоек ворот зоны: стена зоны начинается внутри стойки (торцы не совпадают, D36).
Gate.Post = 2.4

function Gate.Zone(width: number, signColor: Color3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local post, height = Gate.Post, 12
	for _, x in { -width / 2 - post / 2, width / 2 + post / 2 } do
		table.insert(bricks, B(Vector3.new(post, height, post), Vector3.new(x, height / 2, 0), Palette.WoodDark))
		table.insert(bricks, B(Vector3.new(post + 0.6, 1, post + 0.6), Vector3.new(x, height + 0.5, 0), signColor:Lerp(Palette.Black, 0.3)))
	end
	-- Перекладина кончается внутри стоек: торцы не совпадают с гранями стоек (D36).
	local beam = Vector3.new(width + post * 2 - 0.2, 1.2, 1.2)
	table.insert(bricks, B(beam, Vector3.new(0, height - 0.6, 0), Palette.WoodDark))
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

-- Граница карты: трёхцветная стена из кирпичей по прямоугольнику и холмы за ней, чтобы не было видно края мира.
-- Координаты мировые (начало модели — 0, 0, 0). Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick

local THICKNESS = 4
local BAND_HEIGHT = 6
local HILL_DISTANCE = 30 -- от стены наружу до центра холма
local HILL_STEP = 70

export type Bounds = { minX: number, maxX: number, minZ: number, maxZ: number }

local Border = {}

function Border.Wall(bounds: Bounds, groundTop: number): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local width = bounds.maxX - bounds.minX
	local depth = bounds.maxZ - bounds.minZ
	local cx = (bounds.minX + bounds.maxX) / 2
	local cz = (bounds.minZ + bounds.maxZ) / 2
	for band, color in Palette.BorderWall do
		local y = groundTop + (band - 0.5) * BAND_HEIGHT
		for _, z in { bounds.minZ - THICKNESS / 2, bounds.maxZ + THICKNESS / 2 } do
			table.insert(bricks, B(Vector3.new(width + THICKNESS * 2, BAND_HEIGHT, THICKNESS), Vector3.new(cx, y, z), color))
		end
		for _, x in { bounds.minX - THICKNESS / 2, bounds.maxX + THICKNESS / 2 } do
			table.insert(bricks, B(Vector3.new(THICKNESS, BAND_HEIGHT, depth), Vector3.new(x, y, cz), color))
		end
	end
	return bricks
end

-- Холмы вдоль всех четырёх сторон (детерминированно).
function Border.Hills(bounds: Bounds, groundTop: number): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local random = Random.new(3)
	local function hill(center: Vector3, alongX: boolean)
		local height = random:NextNumber(16, 32)
		local length = random:NextNumber(60, 90)
		local size = if alongX then Vector3.new(length, height, 44) else Vector3.new(44, height, length)
		local top = if alongX then Vector3.new(length * 0.6, height * 0.5, 28) else Vector3.new(28, height * 0.5, length * 0.6)
		table.insert(bricks, B(size, center + Vector3.new(0, groundTop + height / 2, 0), Palette.GrassDark, { shadow = false }))
		table.insert(bricks, B(top, center + Vector3.new(0, groundTop + height * 1.25, 0), Palette.Hill, { shadow = false }))
	end
	for x = bounds.minX - 20, bounds.maxX + 20, HILL_STEP do
		hill(Vector3.new(x, 0, bounds.minZ - HILL_DISTANCE), true)
		hill(Vector3.new(x, 0, bounds.maxZ + HILL_DISTANCE), true)
	end
	for z = bounds.minZ - 20, bounds.maxZ + 20, HILL_STEP do
		hill(Vector3.new(bounds.minX - HILL_DISTANCE, 0, z), false)
		hill(Vector3.new(bounds.maxX + HILL_DISTANCE, 0, z), false)
	end
	return bricks
end

return Border

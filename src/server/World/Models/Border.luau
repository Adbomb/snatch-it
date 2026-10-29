-- Граница карты: стена из кирпичей в шахматку по прямоугольнику и ступенчатые холмы из кирпичей за ней
-- (с местами под деревья), чтобы не было видно края мира. Ни одна деталь не длиннее MAX_PIECE стадов.
-- Координаты мировые (начало модели — 0, 0, 0). Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick

local MAX_PIECE = 40
local THICKNESS = 4
local BRICK_LENGTH = 8
local BRICK_HEIGHT = 4
local ROWS = 3 -- высота стены = ROWS × BRICK_HEIGHT
-- Холмы: ряды за стеной (расстояние от стены до центра, высота ступени, шаг вдоль стены).
local HILL_ROWS = {
	{ distance = 26, step = 5, spacing = 44, seed = 3 },
	{ distance = 62, step = 8, spacing = 52, seed = 9 },
}
-- Ступени холма снизу вверх: размер вдоль стены и поперёк (≤ MAX_PIECE).
local HILL_TIERS = { Vector2.new(40, 28), Vector2.new(30, 20), Vector2.new(20, 12) }

export type Bounds = { minX: number, maxX: number, minZ: number, maxZ: number }

local Border = {}

-- Ряд кирпичей вдоль отрезка a→b (по оси X или Z), со сдвигом через ряд, как кладка.
local function wallRun(bricks: { ModelBuilder.Brick }, a: Vector3, b: Vector3, groundTop: number)
	local length = (b - a).Magnitude
	local dir = (b - a).Unit
	local alongX = math.abs(dir.X) > 0.5
	for row = 0, ROWS - 1 do
		local offset = if row % 2 == 0 then 0 else BRICK_LENGTH / 2
		local t = -offset
		local index = 0
		while t < length do
			local from = math.max(t, 0)
			local to = math.min(t + BRICK_LENGTH, length)
			if to - from > 0.05 then
				local center = a + dir * ((from + to) / 2)
				local size = if alongX
					then Vector3.new(to - from, BRICK_HEIGHT, THICKNESS)
					else Vector3.new(THICKNESS, BRICK_HEIGHT, to - from)
				local color = Palette.BorderChecker[(index + row) % 2 + 1]
				table.insert(bricks, B(size, Vector3.new(center.X, groundTop + (row + 0.5) * BRICK_HEIGHT, center.Z), color))
			end
			index += 1
			t += BRICK_LENGTH
		end
	end
end

function Border.Wall(bounds: Bounds, groundTop: number): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local h = THICKNESS / 2
	local x0, x1 = bounds.minX - h, bounds.maxX + h
	local z0, z1 = bounds.minZ - h, bounds.maxZ + h
	wallRun(bricks, Vector3.new(x0 - h, 0, z0), Vector3.new(x1 + h, 0, z0), groundTop)
	wallRun(bricks, Vector3.new(x0 - h, 0, z1), Vector3.new(x1 + h, 0, z1), groundTop)
	wallRun(bricks, Vector3.new(x0, 0, z0 + h), Vector3.new(x0, 0, z1 - h), groundTop)
	wallRun(bricks, Vector3.new(x1, 0, z0 + h), Vector3.new(x1, 0, z1 - h), groundTop)
	return bricks
end

-- Ступенчатые холмы в два ряда вдоль всех сторон. Возвращает кирпичи и CFrame вершин (под деревья).
function Border.Hills(bounds: Bounds, groundTop: number): ({ ModelBuilder.Brick }, { CFrame })
	local bricks: { ModelBuilder.Brick } = {}
	local tops: { CFrame } = {}
	local colors = { Palette.GrassDark, Palette.Hill, Palette.Grass }
	for _, row in HILL_ROWS do
		local random = Random.new(row.seed)
		local function hill(center: Vector3, alongX: boolean)
			local y = groundTop
			local jitter = random:NextNumber(0.8, 1)
			for tier, size in HILL_TIERS do
				local w, d = math.min(size.X * jitter, MAX_PIECE), math.min(size.Y * jitter, MAX_PIECE)
				local dims = if alongX then Vector3.new(w, row.step, d) else Vector3.new(d, row.step, w)
				table.insert(bricks, B(dims, center + Vector3.new(0, y + row.step / 2, 0), colors[tier], { shadow = false }))
				y += row.step
			end
			table.insert(tops, CFrame.new(center + Vector3.new(0, y, 0)))
		end
		for x = bounds.minX - 10, bounds.maxX + 10, row.spacing do
			hill(Vector3.new(x, 0, bounds.minZ - row.distance), true)
			hill(Vector3.new(x, 0, bounds.maxZ + row.distance), true)
		end
		for z = bounds.minZ - 10, bounds.maxZ + 10, row.spacing do
			hill(Vector3.new(bounds.minX - row.distance, 0, z), false)
			hill(Vector3.new(bounds.maxX + row.distance, 0, z), false)
		end
	end
	return bricks, tops
end

return Border

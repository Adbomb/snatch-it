-- Граница карты: стена из кирпичей в шахматку по контуру острова и ступенчатые холмы из кирпичей за ней
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
local CONCAVE_GAP = 24 -- отступ холмов от вогнутого угла: полхолма (20) + толщина стены (4)

local Border = {}

-- Контур — точки по часовой стрелке (вид сверху, x вправо, z вверх), стороны только вдоль осей.
-- Наружная нормаль стороны с направлением d — (-d.z, d.x).
local function outward(d: Vector2): Vector2
	return Vector2.new(-d.Y, d.X)
end

-- Выпуклая вершина (поворот направо при обходе по часовой) — стены продлеваются, вогнутая — нет.
local function convex(d1: Vector2, d2: Vector2): boolean
	return d1.X * d2.Y - d1.Y * d2.X < 0
end

local function edges(outline: { Vector2 }): { { a: Vector2, b: Vector2, d: Vector2, n: Vector2, convexA: boolean, convexB: boolean } }
	local list = {}
	local count = #outline
	for i = 1, count do
		local prev, a, b, next = outline[(i - 2) % count + 1], outline[i], outline[i % count + 1], outline[(i + 1) % count + 1]
		local d = (b - a).Unit
		table.insert(list, {
			a = a,
			b = b,
			d = d,
			n = outward(d),
			convexA = convex((a - prev).Unit, d),
			convexB = convex(d, (next - b).Unit),
		})
	end
	return list
end

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

function Border.Wall(outline: { Vector2 }, groundTop: number): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local h = THICKNESS / 2
	for _, e in edges(outline) do
		-- Осевая линия стены — снаружи контура на h; на выпуклых углах стена заходит за угол на 2h.
		local from = e.a + e.n * h - e.d * (if e.convexA then 2 * h else 0)
		local to = e.b + e.n * h + e.d * (if e.convexB then 2 * h else 0)
		wallRun(bricks, Vector3.new(from.X, 0, from.Y), Vector3.new(to.X, 0, to.Y), groundTop)
	end
	return bricks
end

-- Ступенчатые холмы в два ряда снаружи каждой стороны. Возвращает кирпичи и CFrame вершин (под деревья).
function Border.Hills(outline: { Vector2 }, groundTop: number): ({ ModelBuilder.Brick }, { CFrame })
	local bricks: { ModelBuilder.Brick } = {}
	local tops: { CFrame } = {}
	local colors = { Palette.GrassDark, Palette.Hill, Palette.Grass }
	for _, row in HILL_ROWS do
		local random = Random.new(row.seed)
		for _, e in edges(outline) do
			local alongX = math.abs(e.d.X) > 0.5
			local length = (e.b - e.a).Magnitude
			-- У вогнутого угла холмы не доходят до угла: иначе залезут на остров с другой стороны.
			local first = if e.convexA then -10 else CONCAVE_GAP
			local last = if e.convexB then length + 10 else length - CONCAVE_GAP
			for t = first, last, row.spacing do
				local at = e.a + e.d * t + e.n * row.distance
				local y = groundTop
				local jitter = random:NextNumber(0.8, 1)
				for tier, size in HILL_TIERS do
					local w, d = math.min(size.X * jitter, MAX_PIECE), math.min(size.Y * jitter, MAX_PIECE)
					local dims = if alongX then Vector3.new(w, row.step, d) else Vector3.new(d, row.step, w)
					table.insert(bricks, B(dims, Vector3.new(at.X, y + row.step / 2, at.Y), colors[tier], { shadow = false }))
					y += row.step
				end
				table.insert(tops, CFrame.new(at.X, y, at.Y))
			end
		end
	end
	return bricks, tops
end

return Border

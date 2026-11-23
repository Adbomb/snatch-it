--!strict
-- Набор для тем этажей (этап C): размеры этажа, кирпич темы (Plastic с LegoSquaresItem — контурные квадраты
-- предметов и боссов D39, без шахматки музеев), стены с проёмами и поясами цвета, стекло в толще стены, двери лифта в
-- нише задней стены, кость-цепочка (изогнутая сужающаяся деталь из отрезков).
-- Стена — минимум прямоугольников: строки по высоте (границы поясов и проёмов), в строке — сплошные отрезки между
-- проёмами; одинаковые строки подряд сливаются. Проёмы — объединение прямоугольников (ступенчатые окна). Все стены —
-- occlude (стоят ровно на месте стен каркаса: у клиента в них упирается камера). Площадка лифта (cfg.Landing) пуста:
-- двери лифта утоплены в толщу задней стены.
-- Координаты — оси этажа (Placeholder): центр башни на уровне пола, вход в −Z, площадка лифта сзади.
--   стороны стен: "Front" (−Z), "Back" (+Z) — u вдоль X; "Left" (−X), "Right" (+X) — u вдоль Z; v — высота от пола.
-- Зависит от Floors/FloorBuilder.

local FloorBuilder = require(script.Parent.FloorBuilder)

local Brick = FloorBuilder.Brick

local Kit = {}

Kit.Tile = "LegoSquaresItem" -- MaterialVariant предметов и боссов (Config/Textures.SquaresItem, D39)
Kit.Door = { Half = 3.5, Height = 10.5, Recess = 0.2, Leaf = 0.3 } -- двери лифта в задней стене

export type Rect = { number } -- { u0, u1, v0, v1 }
export type Band = { v0: number, v1: number, color: Color3 }

-- Полуразмеры, толщина стен и высота стен этажа (до низа плиты следующего).
function Kit.Dims(cfg: any): (number, number, number, number)
	return cfg.Half.X, cfg.Half.Y, cfg.Wall, cfg.FloorHeight - cfg.Slab
end

-- Кирпич темы: у Plastic — контурные квадраты предметов (Kit.Tile), если свой вариант не задан.
function Kit.B(size: Vector3, at: Vector3 | CFrame, color: Color3, extra: { [string]: any }?): FloorBuilder.Brick
	local brick = Brick(size, at, color, extra)
	if
		(brick.material == nil or brick.material == Enum.Material.Plastic)
		and brick.variant == nil
		and not brick.text
	then
		brick.variant = Kit.Tile
	end
	return brick
end

-- Длина стены side по u (передняя и задняя — во всю ширину, боковые — между ними).
function Kit.Length(cfg: any, side: string): number
	local hx, hz, t = Kit.Dims(cfg)
	return if side == "Front" or side == "Back" then hx * 2 else hz * 2 - t * 2
end

-- Брусок в толще стены side: u0…u1, v0…v1, глубина d0…d1 от внутренней грани (0) к наружной (t).
function Kit.Slice(
	side: string,
	cfg: any,
	u0: number,
	u1: number,
	v0: number,
	v1: number,
	d0: number,
	d1: number,
	color: Color3,
	extra: { [string]: any }?
): FloorBuilder.Brick
	local hx, hz = Kit.Dims(cfg)
	local du, dv, dd = u1 - u0, v1 - v0, d1 - d0
	local u, v = (u0 + u1) / 2, (v0 + v1) / 2
	local size: Vector3
	local at: Vector3
	if side == "Front" then
		size, at = Vector3.new(du, dv, dd), Vector3.new(u, v, -hz + (cfg.Wall - (d0 + d1) / 2))
	elseif side == "Back" then
		size, at = Vector3.new(du, dv, dd), Vector3.new(u, v, hz - (cfg.Wall - (d0 + d1) / 2))
	elseif side == "Left" then
		size, at = Vector3.new(dd, dv, du), Vector3.new(-hx + (cfg.Wall - (d0 + d1) / 2), v, u)
	else
		size, at = Vector3.new(dd, dv, du), Vector3.new(hx - (cfg.Wall - (d0 + d1) / 2), v, u)
	end
	return Kit.B(size, at, color, extra)
end

local function colorAt(bands: { Band }?, color: Color3, v: number): Color3
	if bands then
		for _, band in bands do
			if v >= band.v0 and v < band.v1 then
				return band.color
			end
		end
	end
	return color
end

-- Стена side во всю толщину с проёмами openings и поясами bands (иначе — цвет color). Добавляет кирпичи в bricks.
function Kit.Wall(
	bricks: { FloorBuilder.Brick },
	cfg: any,
	side: string,
	openings: { Rect },
	color: Color3,
	bands: { Band }?
)
	local _, _, t, h = Kit.Dims(cfg)
	local half = Kit.Length(cfg, side) / 2
	local marks = { 0, h }
	for _, band in bands or {} do
		table.insert(marks, band.v0)
		table.insert(marks, band.v1)
	end
	for _, o in openings do
		table.insert(marks, math.clamp(o[3], 0, h))
		table.insert(marks, math.clamp(o[4], 0, h))
	end
	table.sort(marks)
	type Row = { v0: number, v1: number, solid: { { number } }, color: Color3, key: string }
	local rows: { Row } = {}
	for i = 1, #marks - 1 do
		local v0, v1 = marks[i], marks[i + 1]
		if v1 - v0 < 1e-6 then
			continue
		end
		local mid = (v0 + v1) / 2
		local cuts = {}
		for _, o in openings do
			if o[3] < mid and o[4] > mid then
				table.insert(cuts, { math.max(o[1], -half), math.min(o[2], half) })
			end
		end
		table.sort(cuts, function(a, b)
			return a[1] < b[1]
		end)
		local solid: { { number } } = {}
		local u = -half
		for _, c in cuts do
			if c[1] > u + 1e-6 then
				table.insert(solid, { u, c[1] })
			end
			u = math.max(u, c[2])
		end
		if u < half - 1e-6 then
			table.insert(solid, { u, half })
		end
		local col = colorAt(bands, color, mid)
		local parts = { col:ToHex() }
		for _, s in solid do
			table.insert(parts, ("%.3f:%.3f"):format(s[1], s[2]))
		end
		local key = table.concat(parts, "|")
		local last = rows[#rows]
		if last and last.key == key and math.abs(last.v1 - v0) < 1e-6 then
			last.v1 = v1
		else
			table.insert(rows, { v0 = v0, v1 = v1, solid = solid, color = col, key = key })
		end
	end
	for _, row in rows do
		for _, s in row.solid do
			table.insert(bricks, Kit.Slice(side, cfg, s[1], s[2], row.v0, row.v1, 0, t, row.color, { occlude = true }))
		end
	end
end

-- Стекло в толще стены (0.2 посередине): rect может заходить в сплошную стену — там оно скрыто внутри неё.
function Kit.Glass(
	bricks: { FloorBuilder.Brick },
	cfg: any,
	side: string,
	rect: Rect,
	color: Color3,
	transparency: number?
)
	local t = cfg.Wall
	table.insert(
		bricks,
		Kit.Slice(side, cfg, rect[1], rect[2], rect[3], rect[4], t / 2 - 0.1, t / 2 + 0.1, color, {
			material = Enum.Material.Glass,
			transparency = transparency or 0.35,
			name = "Glass",
		})
	)
end

-- Проём дверей лифта в задней стене (для Kit.Wall).
function Kit.DoorOpening(): Rect
	local d = Kit.Door
	return { -d.Half, d.Half, 0, d.Height }
end

-- Двери лифта в нише проёма Kit.DoorOpening: две створки (шов 0.1) утоплены на Recess от зала, за ними — заглушка до
-- наружной грани стены по поясам стены (снаружи — продолжение фасада). accent — полоса поперёк створок (или nil).
function Kit.LiftDoor(
	bricks: { FloorBuilder.Brick },
	cfg: any,
	leaf: Color3,
	wall: Color3,
	bands: { Band }?,
	accent: { color: Color3, v0: number, v1: number }?
)
	local d = Kit.Door
	local t = cfg.Wall
	local back = d.Recess + d.Leaf
	for _, sx in { -1, 1 } do
		local u0, u1 = if sx < 0 then -d.Half else 0.05, if sx < 0 then -0.05 else d.Half
		table.insert(bricks, Kit.Slice("Back", cfg, u0, u1, 0, d.Height, d.Recess, back, leaf, { occlude = true }))
		if accent then
			-- полоса выступает из створки на 0.1 (в нише, в зал не выходит)
			table.insert(
				bricks,
				Kit.Slice("Back", cfg, u0, u1, accent.v0, accent.v1, d.Recess - 0.1, d.Recess, accent.color, {
					occlude = true,
				})
			)
		end
	end
	-- заглушка: по поясам стены
	local marks = { 0, d.Height }
	for _, band in bands or {} do
		if band.v0 > 0 and band.v0 < d.Height then
			table.insert(marks, band.v0)
		end
	end
	table.sort(marks)
	for i = 1, #marks - 1 do
		local v0, v1 = marks[i], marks[i + 1]
		if v1 - v0 > 1e-6 then
			table.insert(
				bricks,
				Kit.Slice(
					"Back",
					cfg,
					-d.Half,
					d.Half,
					v0,
					v1,
					back,
					t,
					colorAt(bands, wall, (v0 + v1) / 2),
					{ occlude = true }
				)
			)
		end
	end
	-- шов между створками — тёмная щель в глубине ниши
	table.insert(
		bricks,
		Kit.Slice("Back", cfg, -0.05, 0.05, 0, d.Height, back - 0.1, back, Color3.fromHex("1C1C22"), { occlude = true })
	)
end

-- Пояс вокруг этажа снаружи (выступ out, высота v0…v1): передний и задний — во всю ширину с выступом по углам,
-- боковые — между ними (встык). 4 кирпича.
function Kit.Belt(
	bricks: { FloorBuilder.Brick },
	cfg: any,
	v0: number,
	v1: number,
	out: number,
	color: Color3,
	extra: { [string]: any }?
)
	local hx, hz = Kit.Dims(cfg)
	local dv, v = v1 - v0, (v0 + v1) / 2
	table.insert(bricks, Kit.B(Vector3.new(hx * 2 + out * 2, dv, out), Vector3.new(0, v, -hz - out / 2), color, extra))
	table.insert(bricks, Kit.B(Vector3.new(hx * 2 + out * 2, dv, out), Vector3.new(0, v, hz + out / 2), color, extra))
	table.insert(bricks, Kit.B(Vector3.new(out, dv, hz * 2), Vector3.new(-hx - out / 2, v, 0), color, extra))
	table.insert(bricks, Kit.B(Vector3.new(out, dv, hz * 2), Vector3.new(hx + out / 2, v, 0), color, extra))
end

-- Кромка плиты пола снаружи (как у временного этажа: чуть шире каркаса), цвет темы.
function Kit.SlabEdge(bricks: { FloorBuilder.Brick }, cfg: any, color: Color3)
	local hx, hz = Kit.Dims(cfg)
	local slab = cfg.Slab
	table.insert(bricks, Kit.B(Vector3.new(hx * 2 + 0.4, slab, hz * 2 + 0.4), Vector3.new(0, -slab / 2, 0), color))
end

-- Потолок: тонкая плита под плитой следующего этажа (зазор 0.1 до стен и плиты).
function Kit.Ceiling(bricks: { FloorBuilder.Brick }, cfg: any, color: Color3, extra: { [string]: any }?)
	local hx, hz, t, h = Kit.Dims(cfg)
	table.insert(
		bricks,
		Kit.B(Vector3.new((hx - t) * 2 - 0.2, 0.2, (hz - t) * 2 - 0.2), Vector3.new(0, h - 0.2, 0), color, extra)
	)
end

-- Пол-накладка во весь зал (0…0.1 над плитой).
function Kit.Floor(bricks: { FloorBuilder.Brick }, cfg: any, color: Color3)
	local hx, hz, t = Kit.Dims(cfg)
	table.insert(bricks, Kit.B(Vector3.new((hx - t) * 2, 0.1, (hz - t) * 2), Vector3.new(0, 0.05, 0), color))
end

-- Каркас сервера: плита и 4 стены (имена — как у временного этажа), дальше тема добавляет свои опоры.
function Kit.Shell(cfg: any): { FloorBuilder.Brick }
	local hx, hz, t, h = Kit.Dims(cfg)
	local slab = cfg.Slab
	local any = Color3.new(0, 0, 0)
	return {
		Brick(Vector3.new(hx * 2, slab, hz * 2), Vector3.new(0, -slab / 2, 0), any, { name = "Slab" }),
		Brick(Vector3.new(hx * 2, h, t), Vector3.new(0, h / 2, -hz + t / 2), any, { name = "WallFront" }),
		Brick(Vector3.new(hx * 2, h, t), Vector3.new(0, h / 2, hz - t / 2), any, { name = "WallBack" }),
		Brick(Vector3.new(t, h, hz * 2 - t * 2), Vector3.new(-hx + t / 2, h / 2, 0), any, { name = "WallLeft" }),
		Brick(Vector3.new(t, h, hz * 2 - t * 2), Vector3.new(hx - t / 2, h / 2, 0), any, { name = "WallRight" }),
	}
end

-- Брусок, повёрнутый вокруг оси Z (в плоскости стены): луч, наклонный лист. angle — градусы.
function Kit.Turned(
	size: Vector3,
	at: Vector3,
	angle: number,
	color: Color3,
	axis: string?,
	extra: { [string]: any }?
): FloorBuilder.Brick
	local a = math.rad(angle)
	local rot = if axis == "X"
		then CFrame.Angles(a, 0, 0)
		elseif axis == "Y" then CFrame.Angles(0, a, 0)
		else CFrame.Angles(0, 0, a)
	return Kit.B(size, CFrame.new(at) * rot, color, extra)
end

-- Изогнутая сужающаяся кость (ребро, арка) в плоскости XY на глубине z: отрезки между точками points (x, y), у каждого
-- своя толщина (поперёк, в плоскости) и глубина (по Z) — от широкого к узкому. Отрезки чуть продлены (ext), чтобы
-- стыки закрывались соседями. Возвращает число отрезков.
function Kit.Bone(
	bricks: { FloorBuilder.Brick },
	points: { Vector2 },
	z: number,
	thick: { number },
	depth: { number },
	color: Color3,
	ext: number?
): number
	local e = ext or 0.3
	local n = 0
	for i = 1, #points - 1 do
		local a, b = points[i], points[i + 1]
		local d = b - a
		local len = d.Magnitude
		local angle = math.atan2(d.Y, d.X) - math.pi / 2
		local mid = (a + b) / 2
		local cf = CFrame.new(mid.X, mid.Y, z) * CFrame.Angles(0, 0, angle)
		table.insert(
			bricks,
			Kit.B(Vector3.new(thick[i] or thick[#thick], len + e * 2, depth[i] or depth[#depth]), cf, color)
		)
		n += 1
	end
	return n
end

return Kit

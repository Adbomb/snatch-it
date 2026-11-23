--!strict
-- Временный технический этаж «Этаж в разработке» (этап B): для предметов без своей темы (этап C — свои модули с той же
-- таблицей функций). Не финальный вид: светлые стены с окнами, жёлто-графитовая полоса стройки, табличка с названием.
-- Координаты — оси этажа: начало в центре башни на уровне пола этажа, вход в −Z, площадка лифта сзади (cfg.Landing).
--   shell(cfg)              — серверный каркас: только столкновения (невидимый), ≈ 6 деталей
--   decor(cfg, ctx, tier)   — убранство клиента: "interior" (LOD 0, добавляется к фасаду), "facade" (LOD 1),
--                             "silhouette" (LOD 2); ctx = { itemName, accent, stress }
-- Совпадающих граней нет (Lune check_tower, World/FaceCheck): накладки выступают, остальное — встык.
-- Зависит от Floors/FloorBuilder.

local FloorBuilder = require(script.Parent.FloorBuilder)

local Brick = FloorBuilder.Brick

local Placeholder = {}

Placeholder.Name = "Placeholder"
Placeholder.Temporary = true -- временный каркас, не художественный эталон

local WALL = Color3.fromHex("F3EFE6")
local TRIM = Color3.fromHex("E0D9CA")
local FLOOR = Color3.fromHex("C9BFAE")
local DARK = Color3.fromHex("3B3F47")
local WORK = Color3.fromHex("F2C230") -- жёлтый стройки
local GLASS = Color3.fromHex("9FD3EA")
local CEILING = Color3.fromHex("FAF8F3")

local function dims(cfg: any)
	local hx, hz = cfg.Half.X, cfg.Half.Y
	local t = cfg.Wall
	local h = cfg.FloorHeight - cfg.Slab -- высота стен этажа: до низа плиты следующего
	return hx, hz, t, h
end

-- Серверный каркас: плита пола, 4 стены, тумба экспоната (все — столкновения, без вида).
function Placeholder.shell(cfg: any): { FloorBuilder.Brick }
	local hx, hz, t, h = dims(cfg)
	local slab = cfg.Slab
	local plinth = cfg.Exhibit.Plinth
	local c = cfg.Exhibit.Center
	local any = DARK
	return {
		Brick(Vector3.new(hx * 2, slab, hz * 2), Vector3.new(0, -slab / 2, 0), any, { name = "Slab" }),
		Brick(Vector3.new(hx * 2, h, t), Vector3.new(0, h / 2, -hz + t / 2), any, { name = "WallFront" }),
		Brick(Vector3.new(hx * 2, h, t), Vector3.new(0, h / 2, hz - t / 2), any, { name = "WallBack" }),
		Brick(Vector3.new(t, h, hz * 2 - t * 2), Vector3.new(-hx + t / 2, h / 2, 0), any, { name = "WallLeft" }),
		Brick(Vector3.new(t, h, hz * 2 - t * 2), Vector3.new(hx - t / 2, h / 2, 0), any, { name = "WallRight" }),
		Brick(plinth, Vector3.new(c.X, plinth.Y / 2, c.Z), any, { name = "Plinth" }),
	}
end

-- Стена с тремя окнами вдоль оси (length — длина стены, центр center, нормаль наружу outward): нижний и верхний
-- пояс, 4 простенка, одно стекло за простенками (внутри толщины стены, не в плоскости их граней).
local function windowWall(bricks: { FloorBuilder.Brick }, cfg: any, center: Vector3, length: number, alongX: boolean)
	local _, _, t, h = dims(cfg)
	local sill, head = 5, 15
	local windows, width = 3, 6
	local pier = (length - windows * width) / (windows + 1)
	local function box(sx: number, sy: number, sz: number, x: number, y: number, color: Color3, extra: any?)
		local size = if alongX then Vector3.new(sx, sy, sz) else Vector3.new(sz, sy, sx)
		local offset = if alongX then Vector3.new(x, y, 0) else Vector3.new(0, y, x)
		table.insert(bricks, Brick(size, center + offset, color, extra))
	end
	local solid = { occlude = true } -- в плоскости стены каркаса: камера упирается в неё у клиента
	box(length, sill, t, 0, sill / 2, WALL, solid)
	box(length, h - head, t, 0, (head + h) / 2, WALL, solid)
	for i = 0, windows do
		local x = -length / 2 + pier / 2 + i * (pier + width)
		box(pier, head - sill, t, x, (sill + head) / 2, WALL, solid)
	end
	box(length - 0.2, head - sill, 0.2, 0, (sill + head) / 2, GLASS, {
		material = Enum.Material.Glass,
		transparency = 0.35,
		name = "Glass",
	})
end

Placeholder.WindowWall = windowWall -- та же стена у холла (Floors.Lobby)

local function facade(cfg: any, ctx: any): { FloorBuilder.Brick }
	local hx, hz, t, h = dims(cfg)
	local slab = cfg.Slab
	local bricks: { FloorBuilder.Brick } = {}
	-- плита пола видна снаружи кромкой: чуть шире каркаса
	table.insert(bricks, Brick(Vector3.new(hx * 2 + 0.4, slab, hz * 2 + 0.4), Vector3.new(0, -slab / 2, 0), TRIM))
	windowWall(bricks, cfg, Vector3.new(0, 0, -hz + t / 2), hx * 2, true)
	windowWall(bricks, cfg, Vector3.new(0, 0, hz - t / 2), hx * 2, true)
	windowWall(bricks, cfg, Vector3.new(-hx + t / 2, 0, 0), hz * 2 - t * 2, false)
	windowWall(bricks, cfg, Vector3.new(hx - t / 2, 0, 0), hz * 2 - t * 2, false)
	-- полоса стройки по верхнему поясу (выступает на 0.15): спереди и сзади — во всю ширину, по бокам — между ними
	local y = h - 2
	local accent = if ctx and ctx.accent then ctx.accent else WORK
	table.insert(bricks, Brick(Vector3.new(hx * 2 + 0.3, 0.8, 0.15), Vector3.new(0, y, -hz - 0.075), accent))
	table.insert(bricks, Brick(Vector3.new(hx * 2 + 0.3, 0.8, 0.15), Vector3.new(0, y, hz + 0.075), accent))
	table.insert(bricks, Brick(Vector3.new(0.15, 0.8, hz * 2), Vector3.new(-hx - 0.075, y, 0), accent))
	table.insert(bricks, Brick(Vector3.new(0.15, 0.8, hz * 2), Vector3.new(hx + 0.075, y, 0), accent))
	return bricks
end

local function interior(cfg: any, ctx: any): { FloorBuilder.Brick }
	local hx, hz, t, h = dims(cfg)
	local ix, iz = hx - t, hz - t -- внутренний контур
	local plinth = cfg.Exhibit.Plinth
	local c = cfg.Exhibit.Center
	local land = cfg.Landing
	local bricks: { FloorBuilder.Brick } = {}
	-- потолок: тонкая плита под плитой следующего этажа (зазор 0.1, без совпадения граней)
	table.insert(bricks, Brick(Vector3.new(ix * 2 - 0.2, 0.2, iz * 2 - 0.2), Vector3.new(0, h - 0.2, 0), CEILING))
	table.insert(
		bricks,
		Brick(Vector3.new(2, 0.3, 2), Vector3.new(0, h - 0.45, c.Z), CEILING, {
			light = { range = 34, brightness = 1.1, color = Color3.fromHex("FFF1D6") },
			material = Enum.Material.Neon,
			name = "Lamp",
		})
	)
	-- пол: рамка из полос (накладка 0.1 над плитой) и дорожка от лифта к экспонату
	-- (задней полосы нет: там площадка лифта — накладки не должны совпадать гранями)
	local inset = 1.5
	table.insert(bricks, Brick(Vector3.new(ix * 2 - inset * 2, 0.1, 1), Vector3.new(0, 0.05, -iz + inset), FLOOR))
	table.insert(bricks, Brick(Vector3.new(1, 0.1, iz * 2 - inset * 2 - 2), Vector3.new(-ix + inset, 0.05, 0), FLOOR))
	table.insert(bricks, Brick(Vector3.new(1, 0.1, iz * 2 - inset * 2 - 2), Vector3.new(ix - inset, 0.05, 0), FLOOR))
	local pathFrom, pathTo = c.Z + plinth.Z / 2 + 1, land.Center.Z - land.Half.Y
	table.insert(
		bricks,
		Brick(Vector3.new(3, 0.1, pathTo - pathFrom), Vector3.new(0, 0.05, (pathFrom + pathTo) / 2), TRIM)
	)
	-- тумба экспоната: тёмное тело и выступающая крышка, верх крышки — верх тумбы каркаса (на нём стоит экспонат)
	local cap = 0.3
	table.insert(
		bricks,
		Brick(Vector3.new(plinth.X, plinth.Y - cap, plinth.Z), Vector3.new(c.X, (plinth.Y - cap) / 2, c.Z), DARK)
	)
	table.insert(
		bricks,
		Brick(Vector3.new(plinth.X + 0.4, cap, plinth.Z + 0.4), Vector3.new(c.X, plinth.Y - cap / 2, c.Z), WORK)
	)
	-- площадка лифта: плита-накладка, рамка проёма и табличка
	local lc, lh = land.Center, land.Half
	table.insert(bricks, Brick(Vector3.new(lh.X * 2, 0.1, lh.Y * 2), Vector3.new(lc.X, 0.05, lc.Z), DARK))
	local frameZ = hz - t - 0.3
	table.insert(bricks, Brick(Vector3.new(0.6, 10, 0.6), Vector3.new(lc.X - lh.X - 0.3, 5, frameZ), WORK))
	table.insert(bricks, Brick(Vector3.new(0.6, 10, 0.6), Vector3.new(lc.X + lh.X + 0.3, 5, frameZ), WORK))
	table.insert(bricks, Brick(Vector3.new(lh.X * 2 + 1.2, 0.8, 0.6), Vector3.new(lc.X, 10.4, frameZ), WORK))
	-- табличка вплотную к задней стене (встык), надпись на грани −Z — в зал
	table.insert(
		bricks,
		Brick(Vector3.new(5, 1.4, 0.2), Vector3.new(lc.X, 12, hz - t - 0.1), DARK, {
			text = { text = "ЛИФТ", color = WORK },
			name = "LiftSign",
		})
	)
	-- табличка «Этаж в разработке» на левой стене (лицом в зал)
	table.insert(
		bricks,
		Brick(Vector3.new(12, 3, 0.2), CFrame.new(-ix + 0.2, 9, c.Z) * CFrame.Angles(0, -math.pi / 2, 0), DARK, {
			text = {
				text = "ЭТАЖ В РАЗРАБОТКЕ · " .. tostring(ctx and ctx.itemName or ""),
				color = WORK,
			},
		})
	)
	-- колонны по углам (зазор 0.1 до стен) и две скамьи
	for _, sx in { -1, 1 } do
		for _, sz in { -1, 1 } do
			table.insert(
				bricks,
				Brick(
					Vector3.new(1.4, h - 0.4, 1.4),
					Vector3.new(sx * (ix - 0.8), (h - 0.4) / 2, sz * (iz - 0.8)),
					TRIM
				)
			)
		end
		table.insert(bricks, Brick(Vector3.new(1.6, 1, 6), Vector3.new(sx * (ix - 4), 0.5, c.Z), DARK))
	end
	-- нагрузка для замеров (TowerStress): мелкие панели на стенах — LOD 0 близко к бюджету будущих тем
	if ctx and ctx.stress then
		local n = cfg.StressParts or 0
		local perRow = 30
		for i = 0, n - 1 do
			local row, col = i // perRow, i % perRow
			local side = if row % 2 == 0 then -1 else 1
			local x = -ix + 2 + col * ((ix * 2 - 4) / perRow)
			local y = 1.5 + (row // 2) * 1.2
			table.insert(bricks, Brick(Vector3.new(0.9, 0.9, 0.1), Vector3.new(x, y, side * (iz - 0.15)), TRIM))
		end
	end
	return bricks
end

local function silhouette(cfg: any, ctx: any): { FloorBuilder.Brick }
	local hx, hz = cfg.Half.X, cfg.Half.Y
	local slab = cfg.Slab
	local height = cfg.FloorHeight
	local accent = if ctx and ctx.accent then ctx.accent else WORK
	return {
		Brick(Vector3.new(hx * 2, height, hz * 2), Vector3.new(0, height / 2 - slab, 0), WALL),
		Brick(Vector3.new(hx * 2 - 4, 8, 0.2), Vector3.new(0, 10, -hz - 0.1), DARK),
		Brick(Vector3.new(hx * 2 + 0.3, 0.8, hz * 2 + 0.3), Vector3.new(0, height - slab - 2, 0), accent),
	}
end

function Placeholder.decor(cfg: any, ctx: any, tier: string): { FloorBuilder.Brick }
	if tier == "interior" then
		return interior(cfg, ctx)
	elseif tier == "facade" then
		return facade(cfg, ctx)
	elseif tier == "silhouette" then
		return silhouette(cfg, ctx)
	end
	return {}
end

return Placeholder

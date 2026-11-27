-- Этаж башни в формате «витрина» (D74, вариант B, решение владельца 2026-11-27): единый каркас (плита с кантом по
-- редкости, четыре угловые колонны с базой и капителью), фасад и бока — большое стекло, за ним тематическая
-- комната-диорама; потолок комнаты отделан (с земли виден он). Пока одна тема — салун Кактуса-боксёра — и две
-- редкости: Деревянный (1) и Космический (6: каркас шире, радужный, светится; по бокам — руки-кактусы с перчатками).
-- Координаты — в осях этажа: начало — центр низа плиты, перед (стекло фасада) — −Z, высота — FloorHeight × множитель.
-- Архитектура — LegoSquaresBold, предметы — кольца D39 (LegoRingsD39Boss), стекло — Glass; неона нет.
-- Только кирпичи: жильца ставит World/ShowcasePreview. Зависит от ModelBuilder, GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)

type Brick = ModelBuilder.Brick

local ShowcaseFloor = {}

local HX, HZ = GameConfig.Tower.Half.X, GameConfig.Tower.Half.Y
-- Высота этажа по редкости (D74): FloorHeight × 1 / 1.35 / 1.6 / 1.9 / 2.3 / 3.
ShowcaseFloor.HeightFactor = { 1, 1.35, 1.6, 1.9, 2.3, 3 }
ShowcaseFloor.Slab = 1.6 -- толщина плиты этажа
local SLAB = ShowcaseFloor.Slab

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

local C = {
	woodLight = hex("E2BE86"),
	woodMid = hex("C9A06A"),
	woodCore = hex("8A5A2B"),
	graphite = hex("3E3F45"),
	wall = hex("9A6A3E"),
	wall2 = hex("835632"),
	dark = hex("5A3A20"),
	board1 = hex("A8743F"),
	board2 = hex("96653A"),
	ceiling = hex("EAD7B0"),
	beam = hex("6B4524"),
	red = hex("C0392B"),
	redDark = hex("962D22"),
	cream = hex("F2E6D0"),
	green = hex("3FA14B"),
	green2 = hex("2E8A3E"),
	brass = hex("C9A24A"),
	iron = hex("3A3A3F"),
	lamp = hex("FFD98A"),
	glass = hex("CFEFFF"),
	gold = hex("E9B43A"),
	pot = hex("B5653A"),
}
local RAINBOW = { hex("E53935"), hex("FB8C00"), hex("FDD835"), hex("43A047"), hex("1E88E5"), hex("8E24AA") }
local BOTTLES = { hex("43A047"), hex("FB8C00"), hex("E53935"), hex("1E88E5"), hex("FDD835") }

local ARCH = { variant = "LegoSquaresBold" } -- архитектура
local PROP = { variant = "LegoRingsD39Boss" } -- предметы
local TRIM = { variant = "LegoRingsD39Boss", collide = false }
local UPRIGHT = CFrame.Angles(0, 0, math.rad(90)) -- ось цилиндра вертикально
local ALONG_Z = CFrame.Angles(0, math.rad(90), 0) -- ось цилиндра вдоль Z

local function with(base: { [string]: any }, more: { [string]: any }): { [string]: any }
	local t = table.clone(base)
	for k, v in more do
		t[k] = v
	end
	return t
end

-- Брусок по центру (x, y, z) размером (sx, sy, sz).
local function box(
	out: { Brick },
	sx: number,
	sy: number,
	sz: number,
	x: number,
	y: number,
	z: number,
	color: Color3,
	extra: any?
)
	table.insert(out, ModelBuilder.Brick(Vector3.new(sx, sy, sz), Vector3.new(x, y, z), color, extra or ARCH))
end

-- Вертикальный цилиндр радиуса r и высоты h с низом на y.
local function cyl(out: { Brick }, r: number, h: number, x: number, y: number, z: number, color: Color3, extra: any?)
	local e = with(extra or PROP, { shape = "Cylinder" })
	table.insert(out, ModelBuilder.Brick(Vector3.new(h, r * 2, r * 2), CFrame.new(x, y + h / 2, z) * UPRIGHT, color, e))
end

function ShowcaseFloor.Height(tier: number): number
	return math.floor(GameConfig.Tower.FloorHeight * ShowcaseFloor.HeightFactor[tier] + 0.5)
end

-- Цвет каркаса по редкости: k — номер сегмента (дерево — два тона досок, радужный — по кругу).
local function frameColor(tier: number, k: number): Color3
	if tier == 6 then
		return RAINBOW[k % 6 + 1]
	end
	return if k % 2 == 0 then C.woodLight else C.woodMid
end

-- Плита этажа с кантом по редкости на высоте y: сердцевина по следу, кант — доски-сегменты снаружи (через одну выше и
-- дальше на 0.1 — без совпадающих граней).
local function slab(out: { Brick }, tier: number, y: number)
	local wide = if tier == 6 then 2.0 else 0
	local e = 0.5 + wide
	box(out, HX * 2, SLAB, HZ * 2, 0, y + SLAB / 2, 0, if tier == 6 then C.graphite else C.woodCore)
	local seg = 3
	local function row(a0: number, a1: number, alongX: boolean, fixed: number, sign: number)
		local n = math.max(1, math.floor((a1 - a0) / seg + 0.5))
		for k = 0, n - 1 do
			local s0, s1 = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
			local bump = if k % 2 == 0 then 0.1 else 0
			local depth, h = e + bump, SLAB + bump
			local c = fixed + sign * depth / 2
			if alongX then
				box(out, s1 - s0, h, depth, (s0 + s1) / 2, y + h / 2, c, frameColor(tier, k))
			else
				box(out, depth, h, s1 - s0, c, y + h / 2, (s0 + s1) / 2, frameColor(tier, k + 1))
			end
		end
	end
	row(-HX - e, HX + e, true, -HZ, -1)
	row(-HX - e, HX + e, true, HZ, 1)
	row(-HZ, HZ, false, -HX, -1)
	row(-HZ, HZ, false, HX, 1)
end

-- Угловая колонна от плиты до верха этажа: плинт, база, ствол с накладками, шейка, капитель, абака.
local function column(out: { Brick }, tier: number, sx: number, sz: number, y0: number, y1: number)
	local w = if tier == 6 then 4.6 else 3.0
	local outFace = if tier == 6 then 2.0 else 0
	local cx, cz = sx * (HX + outFace - w / 2), sz * (HZ + outFace - w / 2)
	local idx = (if sx > 0 then 1 else 0) + (if sz > 0 then 2 else 0)
	box(out, w + 0.6, 1.2, w + 0.6, cx, y0 + 0.6, cz, frameColor(tier, idx + 1))
	box(out, w + 0.3, 0.4, w + 0.3, cx, y0 + 1.4, cz, frameColor(tier, idx))
	local s0, s1 = y0 + 1.6, y1 - 1.7
	if tier == 6 then -- радужный ствол: сегменты по 6, через один уже на 0.2; у части — мягкий свет
		local n = math.max(1, math.floor((s1 - s0) / 6 + 0.5))
		for k = 0, n - 1 do
			local a, b = s0 + (s1 - s0) * k / n, s0 + (s1 - s0) * (k + 1) / n
			local ww = if k % 2 == 0 then w else w - 0.2
			local extra = if k % 3 == 1
				then with(ARCH, { light = { range = 14, brightness = 0.45, color = frameColor(tier, k + idx) } })
				else ARCH
			box(out, ww, b - a, ww, cx, (a + b) / 2, cz, frameColor(tier, k + idx), extra)
		end
	else
		box(out, w, s1 - s0, w, cx, (s0 + s1) / 2, cz, frameColor(tier, 0))
		-- накладки на двух наружных гранях ствола
		box(out, w - 1.2, s1 - s0 - 1.2, 0.15, cx, (s0 + s1) / 2, cz + sz * (w / 2 + 0.075), frameColor(tier, 1), TRIM)
		box(out, 0.15, s1 - s0 - 1.2, w - 1.2, cx + sx * (w / 2 + 0.075), (s0 + s1) / 2, cz, frameColor(tier, 1), TRIM)
	end
	box(out, w + 0.3, 0.4, w + 0.3, cx, y1 - 1.5, cz, frameColor(tier, idx + 1))
	box(out, w + 0.8, 0.7, w + 0.8, cx, y1 - 0.95, cz, frameColor(tier, idx))
	box(out, w + 1.3, 0.6, w + 1.3, cx, y1 - 0.3, cz, frameColor(tier, idx + 1))
end

-- Стекло фасада и боков: низкий цоколь, стёкла, импосты и ригели в цвет каркаса, верхняя балка.
local function glazing(out: { Brick }, tier: number, y0: number, y1: number)
	local GLASS = { material = Enum.Material.Glass, transparency = 0.72, shadow = false }
	local sill, head = 1.0, 1.4 -- не вровень с плинтом и шейкой колонн
	local g0, g1 = y0 + sill, y1 - 0.4 - head
	local tone = if tier == 6 then C.graphite else C.dark
	local function run(alongX: boolean, half: number, fixed: number, mullions: { number })
		local function put(sa: number, sy: number, sd: number, a: number, y: number, color: Color3, extra: any?)
			if alongX then
				box(out, sa, sy, sd, a, y, fixed, color, extra)
			else
				box(out, sd, sy, sa, fixed, y, a, color, extra)
			end
		end
		put(half * 2, sill, 0.7, 0, y0 + sill / 2, tone)
		put(half * 2, head, 0.8, 0, y1 - 0.4 - head / 2, tone)
		put(half * 2, g1 - g0, 0.2, 0, (g0 + g1) / 2, C.glass, GLASS)
		for _, a in mullions do
			put(0.5, g1 - g0, 0.5, a, (g0 + g1) / 2, if tier == 6 then C.graphite else frameColor(tier, 0), TRIM)
		end
		local n = math.floor((g1 - g0) / 20) -- ригели у высоких этажей
		for k = 1, n do
			put(
				half * 2,
				0.5,
				0.3,
				0,
				g0 + (g1 - g0) * k / (n + 1),
				if tier == 6 then C.graphite else frameColor(tier, k),
				TRIM
			)
		end
	end
	local inset = if tier == 6 then 2.6 else 3.0 -- до внутренней грани колонны
	run(true, HX - inset, -HZ + 0.5, { -5, 5 })
	run(false, HZ - inset, -HX + 0.5, { 0 })
	run(false, HZ - inset, HX - 0.5, { 0 })
end

-- Оболочка комнаты салуна: пол из досок, задняя стена с панелями, потолок с балками.
local function shell(out: { Brick }, tier: number, y0: number, y1: number)
	local n = 12
	local w = (HX * 2 - 1) / n
	for k = 0, n - 1 do -- доски пола: через одну выше на 0.06; крайние короче — не заходят под плинты колонн
		local h = if k % 2 == 0 then 0.3 else 0.36
		local len = if k == 0 or k == n - 1 then 27.2 else HZ * 2 - 1
		box(out, w, h, len, -HX + 0.5 + w * (k + 0.5), y0 + h / 2, 0, if k % 2 == 0 then C.board1 else C.board2)
	end
	local wy0, wy1 = y0 + 0.3, y1 - 0.4
	local inset = if tier == 6 then 2.6 else 3.0 -- стена — между внутренними гранями колонн
	box(out, (HX - inset) * 2, wy1 - wy0, 0.8, 0, (wy0 + wy1) / 2, HZ - 0.4, C.wall)
	box(out, HX * 2 - 7, 5, 0.3, 0, wy0 + 2.5, HZ - 0.95, C.wall2) -- панель низа
	box(out, HX * 2 - 6.6, 0.4, 0.5, 0, wy0 + 5.2, HZ - 1.05, C.dark, TRIM) -- рейка
	for k = 0, 7 do -- вертикальные доски стены
		if k % 2 == 0 then
			local x = -HX + 4.5 + k * (HX * 2 - 9) / 7
			box(out, 2.2, wy1 - wy0 - 6.2, 0.14, x, (wy0 + 5.4 + wy1) / 2, HZ - 0.87, C.wall2, TRIM)
		end
	end
	box(out, HX * 2 - 1, 0.36, HZ * 2 - 1, 0, y1 - 0.22, 0, C.ceiling) -- потолок (верх на 0.04 ниже абак колонн)
	for _, z in { -9, 0, 9 } do
		box(out, HX * 2 - 1.4, 0.9, 1.2, 0, y1 - 0.75, z, C.beam, TRIM) -- верх утоплен в потолок на 0.1
	end
	for _, x in { -8, 8 } do
		box(out, 1.0, 0.65, HZ * 2 - 1.4, x, y1 - 0.675, 0, C.dark, TRIM)
	end
end

local function barrel(out: { Brick }, x: number, y: number, z: number, r: number, h: number)
	cyl(out, r, h, x, y, z, C.wall)
	cyl(out, r + 0.08, 0.3, x, y + h * 0.2, z, C.iron, TRIM)
	cyl(out, r + 0.08, 0.3, x, y + h * 0.72, z, C.iron, TRIM)
	cyl(out, r - 0.25, 0.1, x, y + h, z, C.wall2, TRIM)
end

local function stool(out: { Brick }, x: number, y: number, z: number)
	cyl(out, 0.2, 1.5, x, y, z, C.dark, TRIM)
	cyl(out, 0.85, 0.4, x, y + 1.5, z, C.red, TRIM)
end

local function tableSet(out: { Brick }, x: number, y: number, z: number)
	cyl(out, 1.0, 0.2, x, y, z, C.dark, TRIM)
	cyl(out, 0.3, 2.2, x, y + 0.2, z, C.dark, TRIM)
	cyl(out, 2.2, 0.35, x, y + 2.4, z, C.wall2)
	cyl(out, 0.35, 0.7, x + 0.7, y + 2.75, z - 0.4, C.cream, TRIM) -- кружка
	cyl(out, 0.3, 0.9, x - 0.6, y + 2.75, z + 0.5, BOTTLES[1], TRIM)
	stool(out, x - 3.2, y, z + 0.6)
	stool(out, x + 3.0, y, z - 1.0)
end

-- Люстра-колесо: обод, спицы, ступица, четыре фонаря со светом, подвес до потолка.
local function chandelier(out: { Brick }, x: number, y: number, z: number, r: number, ceilingY: number)
	cyl(out, r, 0.35, x, y, z, C.dark)
	cyl(out, r - 0.6, 0.1, x, y + 0.35, z, C.wall2, TRIM)
	cyl(out, 0.5, 0.9, x, y - 0.3, z, C.iron, TRIM)
	box(out, 0.2, ceilingY - y - 0.35, 0.2, x, (y + 0.35 + ceilingY) / 2, z, C.iron, TRIM)
	for k = 0, 3 do
		local a = math.rad(45 + k * 90)
		local lx, lz = x + math.cos(a) * (r - 0.5), z + math.sin(a) * (r - 0.5)
		box(out, 0.8, 1.0, 0.8, lx, y - 0.5, lz, C.lamp, {
			collide = false,
			shadow = false,
			material = Enum.Material.SmoothPlastic,
			light = { range = 18, brightness = 0.3, color = C.lamp },
		})
		box(out, 1.0, 0.2, 1.0, lx, y - 1.1, lz, C.iron, TRIM)
	end
end

local function cactusPot(out: { Brick }, x: number, y: number, z: number, h: number)
	cyl(out, 1.1, 1.2, x, y, z, C.pot)
	box(out, 1.1, h, 1.1, x, y + 1.2 + h / 2, z, C.green, PROP)
	box(out, 1.6, 0.8, 0.8, x + 1.0, y + 1.2 + h * 0.5, z, C.green2, TRIM)
	box(out, 0.8, 1.6, 0.6, x + 1.5, y + 1.2 + h * 0.5 + 0.8, z, C.green2, TRIM)
end

-- Перчатка-эмблема на стене z (плоская, лицом в −Z): кулак, большой палец, манжета.
local function gloveSign(out: { Brick }, x: number, y: number, z: number, s: number)
	box(out, 4.2 * s, 3.6 * s, 0.9, x, y, z, C.red, PROP)
	box(out, 3.4 * s, 0.9 * s, 0.7, x, y + 2.2 * s, z + 0.05, C.red, TRIM)
	box(out, 1.2 * s, 1.9 * s, 0.7, x - 2.6 * s, y - 0.3 * s, z + 0.05, C.redDark, TRIM)
	box(out, 3.2 * s, 1.1 * s, 0.8, x, y - 2.35 * s, z + 0.02, C.cream, TRIM)
end

-- Ринг-подиум жильца: помост, настил, столбы, два ряда канатов. Возвращает высоту верха настила.
local function ring(out: { Brick }, x: number, y: number, z: number, sx: number, sz: number): number
	box(out, sx, 0.8, sz, x, y + 0.4, z, C.red, PROP)
	box(out, sx - 0.6, 0.2, sz - 0.6, x, y + 0.9, z, C.cream, PROP)
	local px, pz = sx / 2 - 0.5, sz / 2 - 0.5
	for _, a in { -1, 1 } do
		for _, b in { -1, 1 } do
			box(out, 0.6, 3.4, 0.6, x + a * px, y + 1.0 + 1.7, z + b * pz, C.dark, TRIM)
			cyl(out, 0.45, 0.3, x + a * px, y + 4.4, z + b * pz, C.brass, TRIM)
		end
		for _, ry in { 2.2, 3.5 } do
			box(out, 0.16, 0.16, pz * 2 - 0.6, x + a * px, y + ry, z, C.cream, TRIM)
			box(out, px * 2 - 0.6, 0.16, 0.16, x, y + ry + 0.05, z + a * pz, C.cream, TRIM)
		end
	end
	return y + 1.0
end

-- Диорама салуна; богатство — по редкости. Возвращает точку жильца (низ) и его масштаб показа.
local function saloon(out: { Brick }, tier: number, y0: number, y1: number): (Vector3, number)
	local f = y0 + 0.36 -- верх досок пола
	local back = HZ - 0.8
	-- стойка с подножкой и табуретами, полки с бутылками
	box(out, 12, 3.6, 2.4, -8, f + 1.8, back - 3.4, C.dark, PROP)
	box(out, 12.8, 0.4, 3.0, -8, f + 3.8, back - 3.4, C.woodLight, PROP)
	table.insert(
		out,
		ModelBuilder.Brick(
			Vector3.new(12, 0.3, 0.3),
			Vector3.new(-8, f + 0.8, back - 4.9),
			C.brass,
			with(TRIM, { shape = "Cylinder" })
		)
	)
	for _, x in { -12, -8, -4 } do
		stool(out, x, f, back - 6.4)
	end
	box(out, 12, 6.4, 0.3, -8, f + 8.6, back - 0.35, C.wall2, PROP)
	for row = 0, 1 do
		local sy = f + 6.4 + row * 2.6
		box(out, 12.4, 0.3, 1.1, -8, sy, back - 0.95, C.dark, TRIM)
		for k = 0, 5 do
			cyl(out, 0.32, 1.3, -12.5 + k * 1.8, sy + 0.15, back - 0.95, BOTTLES[(k + row) % 5 + 1], TRIM)
		end
	end
	-- бочки, столы, кактусы в горшках, перчатка-эмблема, настенные фонари
	barrel(out, 12.5, f, back - 2.4, 1.5, 3.2)
	barrel(out, 9.2, f, back - 2.2, 1.3, 2.8)
	barrel(out, 14.0, f, back - 5.6, 1.2, 2.6)
	tableSet(out, -10.5, f, -1.5)
	tableSet(out, 11, f, 2.5)
	cactusPot(out, -14.2, f, -13.2, 3.4)
	cactusPot(out, 14.0, f, -13.4, 2.6)
	gloveSign(out, 7.5, f + 9.4, back - 0.5, 1.0)
	for _, x in { -1.5, 12.8 } do
		box(out, 0.9, 1.3, 0.9, x, f + 9.6, back - 0.9, C.lamp, {
			collide = false,
			shadow = false,
			material = Enum.Material.SmoothPlastic,
			light = { range = 14, brightness = 0.25, color = C.lamp },
		})
		box(out, 1.2, 0.25, 1.2, x, f + 10.4, back - 0.9, C.iron, TRIM)
	end
	chandelier(out, 0, y1 - 4.4, 5, 3.2, y1 - 0.4)
	if tier < 6 then
		local top = ring(out, 0, f, -7.5, 10, 8)
		return Vector3.new(0, top, -7.5), 4.0
	end
	-- Космический: большой ринг, две галереи с перилами, гигантские перчатки, флаги, золотой пояс чемпиона, люстры
	local top = ring(out, 0, f, -5.5, 16, 13)
	for i, gy in { y0 + 21, y0 + 39 } do
		local depth = if i == 1 then 8 else 6
		box(out, HX * 2 - 7, 0.7, depth, 0, gy, back - 0.4 - depth / 2, C.wall2)
		box(out, HX * 2 - 7, 0.3, 0.3, 0, gy + 2.3, back - 0.4 - depth + 0.2, C.dark, TRIM)
		for k = 0, 8 do
			box(out, 0.35, 2.0, 0.35, -HX + 4 + k * (HX * 2 - 8) / 8, gy + 1.3, back - 0.4 - depth + 0.2, C.dark, TRIM)
		end
		barrel(out, -11 + i * 2, gy + 0.35, back - 3.2, 1.3, 2.8)
		barrel(out, 12 - i * 2, gy + 0.35, back - 3.0, 1.4, 3.0)
		tableSet(out, 2 - i * 3, gy + 0.35, back - 3.6)
	end
	for k = 0, 7 do -- флаги под потолком
		local x = -14 + k * 4
		box(out, 2.6, 3.4, 0.25, x, y1 - 3.4, back - 0.6, if k % 2 == 0 then C.red else C.cream, TRIM)
	end
	for _, sx in { -1, 1 } do -- гигантские перчатки на цепях
		box(out, 0.3, 9, 0.3, sx * 9, y1 - 5.0, 3, C.iron, TRIM)
		box(out, 6, 6.6, 5, sx * 9, y1 - 12.8, 3, C.red, PROP)
		box(out, 2.0, 3.2, 2.4, sx * 9 - sx * 3.6, y1 - 13.4, 2.2, C.redDark, TRIM)
		box(out, 4.6, 1.8, 4.0, sx * 9, y1 - 17.0, 3, C.cream, PROP)
	end
	-- пояс чемпиона на задней стене: золотой медальон (ось цилиндра — в стену) на красной ленте
	table.insert(
		out,
		ModelBuilder.Brick(
			Vector3.new(0.6, 6.8, 6.8),
			CFrame.new(0, y0 + 30, back - 0.75) * ALONG_Z,
			C.gold,
			with(PROP, { shape = "Cylinder" })
		)
	)
	box(out, 16, 2.4, 0.4, 0, y0 + 30, back - 0.62, C.red, TRIM)
	chandelier(out, -8, y0 + 17.5, -3, 3.0, y0 + 20.65)
	chandelier(out, 8, y0 + 35.5, -3, 3.0, y0 + 38.65)
	chandelier(out, 0, y1 - 22, -9, 4.0, y1 - 0.4)
	cactusPot(out, -13.5, f, 4, 6.5)
	cactusPot(out, 13.5, f, -1, 5.0)
	return Vector3.new(0, top, -5.5), 8.4
end

-- Руки-кактусы с перчатками по бокам Космического этажа: растут из передних колонн, вынос ≤ 6 от следа башни.
local function wings(out: { Brick }, y0: number, h: number)
	local z = -(HZ + 2.0 - 2.3) -- ось передних колонн
	for _, sx in { -1, 1 } do
		local face = sx * (HX + 2.0) -- наружная грань колонны
		local ay = y0 + h * 0.42
		box(out, 2.4, 2.8, 2.8, face + sx * 1.2, ay, z, C.green, PROP)
		box(out, 2.6, h * 0.2, 2.6, face + sx * 2.6, ay + h * 0.1 + 1.4, z, C.green, PROP)
		box(out, 3.4, 1.4, 3.4, face + sx * 2.3, ay + h * 0.2 + 2.1, z, C.cream, PROP)
		box(out, 4.0, 5.0, 4.4, face + sx * 2.0, ay + h * 0.2 + 5.3, z, C.red, PROP)
		box(out, 1.6, 2.4, 1.8, face + sx * 2.0, ay + h * 0.2 + 4.6, z - 3.1, C.redDark, TRIM)
	end
end

export type Built = { bricks: { Brick }, height: number, resident: Vector3, scale: number }

-- Этаж-витрина салуна редкости tier (1 или 6).
function ShowcaseFloor.Saloon(tier: number): Built
	local out: { Brick } = {}
	local h = ShowcaseFloor.Height(tier)
	slab(out, tier, 0)
	for _, sx in { -1, 1 } do
		for _, sz in { -1, 1 } do
			column(out, tier, sx, sz, SLAB, h)
		end
	end
	shell(out, tier, SLAB, h)
	glazing(out, tier, SLAB + 0.3, h)
	local at, scale = saloon(out, tier, SLAB, h)
	if tier == 6 then
		wings(out, 0, h)
	end
	return { bricks = out, height = h, resident = at, scale = scale }
end

-- Плита-кровля над верхним этажом (до колпака башни): та же плита с кантом редкости.
function ShowcaseFloor.Roof(tier: number): { Brick }
	local out: { Brick } = {}
	slab(out, tier, 0)
	return out
end

return ShowcaseFloor

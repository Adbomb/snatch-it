-- Тема этажа-витрины «Салун Кактуса-боксёра» (D74, вариант B): комната за стеклом — доски пола, задняя стена с
-- панелями, потолок с балками — и диорама, которая растёт с редкостью этажа (тема на всех редкостях одна):
--   1 стойка с полками, бочки, столы, ринг-подиум жильца;   2 + пианино и штабель бочек, кованые фонари;
--   3 + галерея с лестницей (два уровня);                   4 + атриум: галерея буквой П, большая люстра, пояс чемпиона;
--   5 + второй ярус, гигантские перчатки, большой кактус;   6 + героический объект — золотая перчатка чемпиона.
-- Жилец стоит у самого стекла на ринге без передних канатов — его ничто не перекрывает. Свет: общий тёплый и
-- прожектор на жильца (у Алмазного третий — на трофей). Наружные выросты (Grow): у Мифического кактус оплетает
-- переднюю колонну, у Алмазного из-за колонн выходят изогнутые руки-кактусы с золотыми перчатками.
-- Только кирпичи. Зависит от ShowcaseKit.

local ServerScriptService = game:GetService("ServerScriptService")

local Kit = require(ServerScriptService.Server.World.Models.ShowcaseKit)

local HX, HZ, BACK, W = Kit.HX, Kit.HZ, Kit.BACK, Kit.W
local box, cyl, cylZ, cylX, ball, rod, limb, lamp =
	Kit.box, Kit.cyl, Kit.cylZ, Kit.cylX, Kit.ball, Kit.rod, Kit.limb, Kit.lamp
local hex = Kit.hex
local PROP, TRIM = Kit.PROP, Kit.TRIM

local Saloon = {}

Saloon.Item = "CactusBoxer"
Saloon.Scale = { 4.0, 4.6, 5.2, 5.8, 6.4, 7.0 } -- масштаб показа жильца по редкости
-- Цвет светлого проёма дальней версии: тёплый, ярче с редкостью.
Saloon.Glow = { hex("D9A25E"), hex("E0AC66"), hex("E8B670"), hex("F0C27C"), hex("F5CC8A"), hex("FFD99A") }
-- (Dado — цвет цоколя стены для дальней версии — задан ниже, после палитры.)
local SIZE = Vector3.new(2.48, 2.384, 1.975) -- размер жильца в натуральную величину (Config/Items)

local C = {
	wall = hex("9A6A3E"),
	wall2 = hex("835632"),
	dark = hex("5A3A20"),
	board1 = hex("A8743F"),
	board2 = hex("96653A"),
	ceiling = hex("EAD7B0"),
	beam = hex("6B4524"),
	woodLight = hex("E2BE86"),
	red = hex("C0392B"),
	redDark = hex("962D22"),
	cream = hex("F2E6D0"),
	green = hex("3FA14B"),
	green2 = hex("2E8A3E"),
	brass = Kit.BRASS,
	iron = hex("3A3A3F"),
	lamp = hex("FFD98A"),
	gold = Kit.GOLD,
	gold2 = Kit.GOLD2,
	pot = hex("B5653A"),
	pink = hex("F27BA5"),
	warm = hex("FFD9A0"),
}
Saloon.Dado = C.wall2
local PAL: Kit.Palette =
	{ deck = C.wall2, trim = C.dark, step1 = C.board1, step2 = C.board2, metal = C.iron, lamp = C.lamp }
local BOTTLES = { hex("43A047"), hex("FB8C00"), hex("E53935"), hex("1E88E5"), hex("FDD835") }

-- Оболочка комнаты: пол из досок, задняя стена с панелями, потолок с балками. o — вынос каркаса за след.
local function shell(out, y0: number, y1: number, o: number, tier: number)
	local lift = ({ 0, 0, 0.1, 0.2, 0.3, 0.4 })[tier] -- на высших редкостях зал светлее
	local wall, wall2 = C.wall:Lerp(C.cream, lift), C.wall2:Lerp(C.cream, lift)
	local x1, z0 = HX - 1.4 + o, -(HZ - 1.4 + o)
	local n = 12
	local w = x1 * 2 / n
	for k = 0, n - 1 do -- доски пола: через одну выше на 0.06
		local h = if k % 2 == 0 then 0.3 else 0.36
		box(
			out,
			w,
			h,
			BACK - z0,
			-x1 + w * (k + 0.5),
			y0 + h / 2,
			(z0 + BACK) / 2,
			if k % 2 == 0 then C.board1 else C.board2
		)
	end
	local half = HX + o - 3.0
	local wy0, wy1 = y0, y1 - 0.4
	box(out, half * 2, wy1 - wy0, 0.3, 0, (wy0 + wy1) / 2, BACK + 0.15, wall)
	box(out, half * 2 - 1, 5, 0.15, 0, wy0 + 2.8, BACK - 0.075, wall2) -- панель низа
	box(out, half * 2 - 0.6, 0.4, 0.3, 0, wy0 + 5.5, BACK - 0.15, C.dark, TRIM) -- рейка
	for _, x in { -12, -4, 4, 12 } do -- вертикальные доски стены
		box(out, 2.2, wy1 - wy0 - 6.2, 0.12, x, (wy0 + 5.8 + wy1 - 0.4) / 2, BACK - 0.06, wall2, TRIM)
	end
	box(out, (HX + o) * 2 - 1.4, 0.36, (HZ + o) * 2 - 1.4, 0, y1 - 0.22, 0, C.ceiling) -- потолок: с земли виден он
	for _, z in { -9, 0, 9 } do
		box(out, (HX + o) * 2 - 1.8, 0.9, 1.2, 0, y1 - 0.75, z, C.beam, TRIM)
	end
	for _, x in { -8, 8 } do
		box(out, 1.0, 0.65, (HZ + o) * 2 - 1.8, x, y1 - 0.675, 0, C.dark, TRIM)
	end
end

local function barrel(out, x: number, y: number, z: number, r: number, h: number)
	cyl(out, r, h, x, y, z, C.wall)
	cyl(out, r + 0.08, 0.3, x, y + h * 0.2, z, C.iron, TRIM)
	cyl(out, r + 0.08, 0.3, x, y + h * 0.72, z, C.iron, TRIM)
	cyl(out, r - 0.25, 0.1, x, y + h, z, C.wall2, TRIM)
end

-- Лежащая бочка (ось вдоль Z) — для штабеля.
local function barrelLying(out, x: number, y: number, z: number, r: number, len: number)
	cylZ(out, r, len, x, y + r, z, C.wall)
	cylZ(out, r + 0.08, 0.3, x, y + r, z - len * 0.28, C.iron, TRIM)
	cylZ(out, r + 0.08, 0.3, x, y + r, z + len * 0.28, C.iron, TRIM)
end

local function stool(out, x: number, y: number, z: number)
	cyl(out, 0.2, 1.5, x, y, z, C.dark, TRIM)
	cyl(out, 0.85, 0.4, x, y + 1.5, z, C.red, TRIM)
end

local function tableSet(out, x: number, y: number, z: number)
	cyl(out, 1.0, 0.2, x, y, z, C.dark, TRIM)
	cyl(out, 0.3, 2.2, x, y + 0.2, z, C.dark, TRIM)
	cyl(out, 2.2, 0.35, x, y + 2.4, z, C.wall2)
	cyl(out, 0.35, 0.7, x + 0.7, y + 2.75, z - 0.4, C.cream, TRIM) -- кружка
	cyl(out, 0.3, 0.9, x - 0.6, y + 2.75, z + 0.5, BOTTLES[1], TRIM)
	stool(out, x - 3.2, y, z + 0.6)
	stool(out, x + 3.0, y, z - 1.0)
end

-- Люстра-колесо: обод, ступица, n плафонов, подвес до потолка (свет — общий источник этажа).
local function chandelier(out, x: number, y: number, z: number, r: number, ceilingY: number, n: number, rim: Color3)
	cyl(out, r, 0.35, x, y, z, rim)
	cyl(out, r - 0.6, 0.1, x, y + 0.35, z, C.wall2, TRIM)
	cyl(out, 0.5, 0.9, x, y - 0.3, z, C.iron, TRIM)
	box(out, 0.2, ceilingY - y - 0.35, 0.2, x, (y + 0.35 + ceilingY) / 2, z, C.iron, TRIM)
	for k = 0, n - 1 do
		local a = math.rad(45 + k * 360 / n)
		local lx, lz = x + math.cos(a) * (r - 0.5), z + math.sin(a) * (r - 0.5)
		lamp(out, 0.8, 1.0, 0.8, lx, y - 0.5, lz, C.lamp)
		box(out, 1.0, 0.2, 1.0, lx, y - 1.1, lz, C.iron, TRIM)
	end
end

local function cactusPot(out, x: number, y: number, z: number, h: number, side: number)
	cyl(out, 1.1, 1.2, x, y, z, C.pot)
	box(out, 1.1, h, 1.1, x, y + 1.2 + h / 2, z, C.green, PROP)
	box(out, 1.6, 0.8, 0.8, x + side * 1.0, y + 1.2 + h * 0.5, z, C.green2, TRIM)
	box(out, 0.8, 1.6, 0.6, x + side * 1.5, y + 1.2 + h * 0.5 + 0.8, z, C.green2, TRIM)
end

-- Перчатка-эмблема на стене z (плоская, лицом в −Z): кулак, большой палец, манжета.
local function gloveSign(out, x: number, y: number, z: number, s: number)
	box(out, 4.2 * s, 3.6 * s, 0.9, x, y, z, C.red, PROP)
	box(out, 3.4 * s, 0.9 * s, 0.7, x, y + 2.2 * s, z + 0.05, C.red, TRIM)
	box(out, 1.2 * s, 1.9 * s, 0.7, x - 2.6 * s, y - 0.3 * s, z + 0.05, C.redDark, TRIM)
	box(out, 3.2 * s, 1.1 * s, 0.8, x, y - 2.35 * s, z + 0.02, C.cream, TRIM)
end

-- Объёмная перчатка размера s с центром кулака (x, y, z): кулак, костяшки, большой палец, манжета.
local function glove3(out, x: number, y: number, z: number, s: number, color: Color3, dark: Color3, cuff: Color3)
	box(out, 6 * s, 5.2 * s, 5 * s, x, y, z, color, PROP)
	box(out, 5 * s, 1.3 * s, 4.2 * s, x, y + 3.2 * s, z, color, TRIM)
	box(out, 1.9 * s, 3.2 * s, 2.4 * s, x - 3.9 * s, y - 0.4 * s, z - 0.7 * s, dark, TRIM)
	box(out, 4.6 * s, 1.9 * s, 4.0 * s, x, y - 3.5 * s, z, cuff, PROP)
end

-- Пианино у задней стены (клавиши — к залу).
local function piano(out, x: number, y: number, z: number)
	box(out, 5.2, 4.4, 1.6, x, y + 2.2, z, C.dark, PROP)
	box(out, 5.5, 0.3, 1.9, x, y + 4.55, z - 0.05, C.wall2, TRIM)
	box(out, 5.2, 0.4, 1.1, x, y + 2.2, z - 1.35, C.dark, PROP)
	box(out, 4.8, 0.12, 0.8, x, y + 2.46, z - 1.4, C.cream, TRIM)
	box(out, 4.4, 0.26, 0.4, x, y + 2.53, z - 1.1, C.iron, TRIM)
	box(out, 1.7, 1.2, 0.1, x, y + 3.5, z - 0.85, C.cream, TRIM)
	for _, s in { -1, 1 } do
		box(out, 0.4, 2.0, 0.4, x + s * 2.3, y + 1.0, z - 1.6, C.dark, TRIM)
	end
	stool(out, x, y, z - 3.2)
end

-- Ринг-подиум жильца у стекла: помост и настил, задние столбы, канаты сзади и по бокам (перед открыт).
-- Возвращает точку жильца, половину ширины ринга и его задний край.
local function ring(out, tier: number, f: number, post: Color3): (Vector3, number, number)
	local s = Saloon.Scale[tier]
	local sx, sz = s * SIZE.X + 3.2, s * SIZE.Z + 2.4
	local z0 = -(HZ - 1.8)
	local zc = z0 + sz / 2
	local ph = 0.7 + 0.1 * tier
	box(out, sx, ph, sz, 0, f + ph / 2, zc, C.red, PROP)
	box(out, sx - 0.6, 0.2, sz - 0.6, 0, f + ph + 0.1, zc, C.cream, PROP)
	local px, pz = sx / 2 - 0.5, sz / 2 - 0.5
	local postH = 2.6 + 0.5 * tier
	local base = f + ph
	for _, a in { -1, 1 } do
		box(out, 0.7, postH, 0.7, a * px, base + postH / 2, zc + pz, post, TRIM)
		cyl(out, 0.5, 0.3, a * px, base + postH, zc + pz, C.brass, TRIM)
		cyl(out, 0.5, 0.35, a * px, base, zc - pz, C.brass, TRIM)
		for _, t in { 0.45, 0.85 } do
			local from = Vector3.new(a * px, base + postH * t, zc + pz)
			rod(out, 0.09, from, Vector3.new(a * px, base + 0.3, zc - pz), C.cream, TRIM)
		end
	end
	for _, t in { 0.45, 0.85 } do
		box(out, px * 2 - 0.7, 0.16, 0.16, 0, base + postH * t, zc + pz, C.cream, TRIM)
	end
	return Vector3.new(0, base + 0.2, zc), sx / 2, zc + sz / 2
end

-- Вымпелы на шнуре вдоль стены или кромки галереи.
local function flags(out, x0: number, x1: number, n: number, y: number, z: number)
	box(out, x1 - x0, 0.12, 0.12, (x0 + x1) / 2, y + 1.5, z, C.cream, TRIM)
	for k = 0, n - 1 do
		local x = x0 + (x1 - x0) * (k + 0.5) / n
		box(out, 2.0, 2.8, 0.2, x, y, z, if k % 2 == 0 then C.red else C.cream, TRIM)
	end
end

-- Пояс чемпиона на стене: золотой медальон на красной ленте.
local function belt(out, x: number, y: number, r: number)
	box(out, r * 5, r * 0.8, 0.3, x, y, BACK - 0.3, C.red, TRIM)
	cylZ(out, r, 0.5, x, y, BACK - 0.45, C.gold)
	cylZ(out, r * 0.62, 0.3, x, y, BACK - 0.75, C.gold2, TRIM)
	for _, s in { -1, 1 } do
		box(out, r * 0.7, r * 0.7, 0.2, x + s * r * 1.75, y, BACK - 0.5, C.gold, TRIM)
	end
end

-- Место жильца у стекла: точка (низ существа), размеры подиума sx × sz и его высота. f — верх пола.
function Saloon.Spot(tier: number, f: number): (Vector3, number, number, number)
	local s = Saloon.Scale[tier]
	local sx, sz = s * SIZE.X + 3.2, s * SIZE.Z + 2.4
	local ph = 0.7 + 0.1 * tier
	return Vector3.new(0, f + ph + 0.2, -(HZ - 1.8) + sz / 2), sx, sz, ph
end

-- Пояс чемпиона на стойке (лицом к стеклу): тумба, столб, золотой медальон на красной ленте. s — размер.
local function beltStand(out, x: number, y: number, z: number, s: number)
	box(out, 3.6 * s, 1.2 * s, 3.0 * s, x, y + 0.6 * s, z, C.dark, PROP)
	box(out, 0.7 * s, 5.2 * s, 0.7 * s, x, y + 3.8 * s, z + 0.4 * s, C.dark, TRIM)
	box(out, 5.0 * s, 1.5 * s, 0.3 * s, x, y + 6.2 * s, z, C.red, TRIM)
	cylZ(out, 2.1 * s, 0.5 * s, x, y + 6.2 * s, z - 0.2 * s, C.gold)
	cylZ(out, 1.3 * s, 0.3 * s, x, y + 6.2 * s, z - 0.5 * s, C.gold2, TRIM)
end

-- Точка жильца — низ существа на ринге. o — вынос каркаса за след (у Алмазного 1 стад).
function Saloon.Build(out, tier: number, y0: number, y1: number): Vector3
	local o = if tier == 6 then 1.0 else 0
	local f = y0 + 0.36 -- верх досок пола
	local top = y1 - 0.4 -- низ потолка
	shell(out, y0, y1, o, tier)
	local at, rx, rz = ring(out, tier, f, if tier >= 4 then C.gold2 else C.dark)
	local headY = at.Y + Saloon.Scale[tier] * SIZE.Y -- макушка жильца

	-- стойка с подножкой и табуретами, полки с бутылками (слева у задней стены)
	box(out, 12, 3.6, 2.4, -8, f + 1.8, BACK - 3.4, C.dark, PROP)
	box(out, 12.8, 0.4, 3.0, -8, f + 3.8, BACK - 3.4, C.woodLight, PROP)
	cylX(out, 0.15, 12, -8, f + 0.8, BACK - 4.9, C.brass, TRIM)
	for _, x in { -12, -8, -4 } do
		stool(out, x, f, BACK - 6.4)
	end
	box(out, 12, 6.4, 0.3, -8, f + 8.6, BACK - 0.3, C.wall2, PROP)
	for row = 0, 1 do
		local sy = f + 6.4 + row * 2.6
		box(out, 12.4, 0.3, 1.1, -8, sy, BACK - 0.95, C.dark, TRIM)
		for k = 0, 5 do
			cyl(out, 0.32, 1.3, -12.5 + k * 1.8, sy + 0.15, BACK - 0.95, BOTTLES[(k + row) % 5 + 1], TRIM)
		end
	end
	-- бочки справа у задней стены, кактусы в горшках у передних углов, настенные фонари
	barrel(out, 12.6, f, BACK - 2.4, 1.5, 3.2)
	barrel(out, 14.1, f, BACK - 5.6, 1.2, 2.6)
	if tier < 5 then
		cactusPot(out, -14.4, f, -12.2, 2.4 + tier * 0.4, 1)
	end
	cactusPot(out, 14.4, f, -12.1, 2.0 + tier * 0.3, -1)
	for _, x in { -1.2, 13.4 } do
		lamp(out, 0.9, 1.3, 0.9, x, f + 9.6, BACK - 0.75, C.lamp)
		box(out, 1.2, 0.25, 1.2, x, f + 10.4, BACK - 0.75, C.iron, TRIM)
	end

	local g1, g2 -- высоты галерей: невысоко, чтобы второй уровень был виден с ракурса игрока
	local side = rx + 3.3 -- место «на виду» рядом с жильцом (между рингом и боковым стеклом)
	if tier <= 2 then
		barrel(out, 9.4, f, BACK - 2.2, 1.3, 2.8)
		tableSet(out, -11.5, f, rz + 5.2)
		tableSet(out, 10.5, f, rz + 6.6)
		gloveSign(out, 8.4, f + 9.6, BACK - 0.5, 1.0)
		chandelier(out, 0, top - 4.0, rz + 6, 3.2, top, 4, C.dark)
	end
	if tier >= 2 then -- пианино, штабель бочек, кованые фонари
		piano(out, if tier == 2 then 3.4 else 4.2, f, BACK - 1.0)
		barrelLying(out, 9.3, f, BACK - 2.6, 1.3, 3.0)
		if tier >= 3 then
			barrelLying(out, 6.6 + 5.3, f + 2.25, BACK - 2.6, 1.3, 3.0)
		end
		local drop = math.min(5 + tier, top - headY - 3.2)
		Kit.lantern(out, PAL, -(rx + 2.6), top, at.Z, drop)
		Kit.lantern(out, PAL, rx + 2.6, top, at.Z, drop)
	end
	if tier >= 3 then -- галерея и лестница: диорама в два уровня
		local zF = math.max(rz + 3.4, BACK - 7.5)
		g1 = f + 11.5 + tier
		Kit.gallery(out, PAL, f, g1, zF, HX - 3.6 + o, true)
		Kit.stairs(out, PAL, f, g1, -1.5, 11.5, zF - 1.7)
		tableSet(out, -8, g1, BACK - 3.6)
		barrel(out, 10.5, g1, BACK - 2.6, 1.4, 3.0)
		barrel(out, 7.6, g1, BACK - 2.4, 1.2, 2.6)
		cactusPot(out, -13, g1, BACK - 2.4, 3.2, 1)
		gloveSign(out, 1.5, g1 + 7.4, BACK - 0.5, 1.15)
		if tier <= 4 then
			flags(out, -(HX - 4.2), HX - 4.2, 9, top - 2.2, BACK - 0.35)
		end
		if tier == 3 then
			chandelier(out, 0, headY + 6.4, rz + 3.2, 3.4, top, 4, C.dark)
		end
	end
	if tier >= 4 then -- атриум в два света: крылья галереи вдоль стёкол, большая люстра, пояс чемпиона
		local zF = math.max(rz + 3.4, BACK - 7.5)
		for _, s in { -1, 1 } do
			Kit.wing(out, PAL, g1, s, HX - 5.6 + o, HX - 1.6 + o, at.Z + 4, zF)
		end
		belt(out, -7.5, g1 + 7.6, 2.3)
		if tier == 4 then
			local cy = headY + 7
			chandelier(out, 0, cy, rz + 3.6, 5.2, top, 8, C.gold2)
			chandelier(out, 0, cy - 2.4, rz + 3.6, 2.6, cy, 4, C.gold2)
			beltStand(out, side, f, at.Z + 1, 1.0) -- на виду рядом с жильцом
		end
	end
	if tier >= 5 then -- второй ярус, гигантские перчатки на цепях, большой кактус в переднем углу, знамёна
		g2 = g1 + 12
		local zF2 = BACK - 6.5
		Kit.gallery(out, PAL, f, g2, zF2, HX - 3.6 + o, false)
		barrel(out, -10.5, g2, BACK - 2.6, 1.4, 3.0)
		barrel(out, -7.6, g2, BACK - 2.4, 1.2, 2.6)
		for _, s in { -1, 1 } do
			local gx, gy, gz = s * (HX - 6.5 + o), headY + 6, math.min(rz - 1.5, -1.4)
			box(out, 0.3, top - gy - 3.4, 0.3, gx, (top + gy + 3.4) / 2, gz, C.iron, TRIM)
			glove3(out, gx, gy, gz, 0.82, C.red, C.redDark, C.cream)
		end
		for i, x in { -9.5, 0, 9.5 } do -- знамёна на верхней стене: зал не пустой до потолка
			local len = top - g2 - 7
			box(out, 5, len, 0.2, x, top - 1 - len / 2, BACK - 0.1, if i == 2 then C.cream else C.red, TRIM)
			cylZ(out, 1.5, 0.3, x, top - 1 - len * 0.35, BACK - 0.3, C.gold, TRIM)
		end
		-- большой кактус за передней левой колонной: ствол и руки
		local kx, kz = -(HX - 3.0 + o), -(HZ - 5.4 + o)
		local kh = (g1 - f) * 0.86
		cyl(out, 1.6, 1.6, kx, f, kz, C.pot)
		box(out, 1.9, kh, 1.9, kx, f + 1.6 + kh / 2, kz, C.green, PROP)
		box(out, 1.3, 1.3, 2.6, kx, f + 1.6 + kh * 0.45, kz + 2.2, C.green2, TRIM)
		box(out, 1.2, kh * 0.3, 1.2, kx, f + 1.6 + kh * 0.45 + kh * 0.15, kz + 3.0, C.green2, TRIM)
		ball(out, 0.8, kx, f + 1.6 + kh + 0.5, kz, C.pink, TRIM)
		if tier == 5 then
			local cy = headY + 7.5
			chandelier(out, 0, cy, rz + 3.2, 5.0, top, 8, C.iron)
			chandelier(out, 0, cy - 2.4, rz + 3.2, 2.5, cy, 4, C.iron)
			-- на виду рядом с жильцом: большая красная перчатка на тумбе
			box(out, 4.2, 2.6, 4.2, side, f + 1.3, at.Z + 1, C.dark, PROP)
			glove3(out, side, f + 6.3, at.Z + 1, 0.6, C.red, C.redDark, C.cream)
		end
	end
	if tier == 6 then -- героические объекты рядом с жильцом: золотая перчатка чемпиона и пояс, алмазные друзы
		local hz = at.Z + 1
		box(out, 4.8, 4.2, 4.8, -side, f + 2.1, hz, C.dark, PROP)
		box(out, 5.4, 0.4, 5.4, -side, f + 4.4, hz, C.gold, PROP)
		cyl(out, 1.6, 1.5, -side, f + 4.6, hz, C.gold2) -- манжета
		ball(out, 2.7, -side, f + 8.3, hz, C.gold, PROP) -- кулак
		ball(out, 1.15, -side + 2.5, f + 7.5, hz - 0.9, C.gold2, TRIM) -- большой палец
		cylX(out, 0.9, 4.0, -side, f + 10.2, hz - 0.4, C.gold, TRIM) -- костяшки
		Kit.druse(out, -side + 1.2, f, hz - 3.4, 1.3, Kit.DIAMOND)
		beltStand(out, side, f, hz, 1.35)
		Kit.druse(out, side - 1.0, f, hz - 3.2, 1.2, Kit.DIAMOND)
		local cy = headY + 8
		chandelier(out, 0, cy, rz + 1.6, 5.6, top, 8, C.gold2)
		chandelier(out, 0, cy - 2.6, rz + 1.6, 2.8, cy, 4, C.gold2)
		Kit.light(out, Vector3.new(-side, f + 19, hz - 6), 28, 1.7, C.warm, 60, Vector3.new(0, -1, 0.35))
	end

	Kit.lights(out, tier, y0, y1, at, headY, C.warm)
	return at
end

-- Наружные выросты темы: 5 — кактус оплетает переднюю левую колонну; 6 — изогнутые руки с золотыми перчатками.
function Saloon.Grow(out, tier: number, h: number, _frame, _crystal)
	if tier == 5 then
		-- кактус-лоза ступенями: стволы вверх по наружным граням колонны, короткие переходы через наружный угол
		local cx, cz = -(HX - W / 2), -(HZ - W / 2)
		local r, reach = 0.95, W / 2 + 0.9
		local front = Vector3.new(cx + 0.9, 0, cz - reach)
		local corner = Vector3.new(cx - reach + 0.25, 0, cz - reach + 0.25)
		local side = Vector3.new(cx - reach, 0, cz + 0.9)
		local up = function(p: Vector3, y: number): Vector3
			return Vector3.new(p.X, y, p.Z)
		end
		local points = {}
		local y, run, jog = 3.2, 6.2, 1.5
		local onFront = true
		while y + run < h - 3.5 do
			local a, b = if onFront then front else side, if onFront then side else front
			table.insert(points, up(a, y))
			table.insert(points, up(a, y + run))
			table.insert(points, up(corner, y + run + jog))
			y += run + jog * 2
			onFront = not onFront
			if y + run >= h - 3.5 then
				table.insert(points, up(b, y))
				table.insert(points, up(b, math.min(y + run * 0.6, h - 4)))
			end
		end
		limb(out, r, points, C.green2, TRIM)
		for i = 1, #points - 1 do -- шипы на стволах
			local a, b = points[i], points[i + 1]
			if math.abs(a.X - b.X) < 0.01 and b.Y - a.Y > 3 then
				local out2 = if math.abs(a.Z - front.Z) < 0.01 then Vector3.new(0, 0, -1) else Vector3.new(-1, 0, 0)
				for _, t in { 0.3, 0.7 } do
					local p = a:Lerp(b, t) + out2 * (r + 0.1)
					box(out, 0.3, 0.3, 0.3, p.X, p.Y, p.Z, C.cream, TRIM)
				end
			end
		end
		local last = points[#points]
		ball(out, 1.0, last.X, last.Y + 1.0, last.Z, C.pink, TRIM)
		ball(out, 0.5, last.X, last.Y + 1.9, last.Z, C.gold, TRIM)
		-- рука с перчаткой из середины лозы
		local mid = points[math.floor(#points / 2)]
		local hand = mid + Vector3.new(0.6, 2.4, 0.6)
		rod(out, 0.6, mid, hand, C.green2, TRIM)
		ball(out, 1.0, hand.X, hand.Y + 0.9, hand.Z, C.red, TRIM)
		ball(out, 0.5, hand.X + 0.7, hand.Y + 0.8, hand.Z - 0.5, C.redDark, TRIM)
		-- росток у правой колонны
		local px, pz = HX - W / 2 + 0.6, -(HZ - W / 2) - reach
		limb(out, 0.6, {
			Vector3.new(px, 3.2, pz),
			Vector3.new(px, 7.4, pz),
			Vector3.new(px - 1.2, 8.6, pz),
			Vector3.new(px - 1.2, 11, pz),
		}, C.green2, TRIM)
		ball(out, 0.75, px - 1.2, 11.8, pz, C.pink, TRIM)
	elseif tier == 6 then
		local face = HX + 1.0 -- наружная грань колонны Алмазного
		local z = -(HZ + 1.0) + 2.6
		for i, s in { -1, 1 } do
			local ay = h * (if i == 1 then 0.36 else 0.5)
			local pts = {
				Vector3.new(s * (face - 0.6), ay, z),
				Vector3.new(s * (face + 1.4), ay + 0.3, z),
				Vector3.new(s * (face + 2.3), ay + 2.8, z),
				Vector3.new(s * (face + 2.2), ay + 12.0, z),
			}
			limb(out, 1.35, pts, C.green2, PROP)
			local gx, gy = s * (face + 2.2), ay + 16.0
			cyl(out, 1.8, 1.5, gx, ay + 12.0, z, C.cream, TRIM)
			ball(out, 2.8, gx, gy, z, C.gold, PROP)
			ball(out, 1.3, gx - s * 1.8, gy - 0.6, z - 2.0, C.gold2, TRIM)
			-- малый отросток с цветком
			local b0 = Vector3.new(s * (face - 0.6), ay - h * 0.14, z + 0.4)
			local b1 = Vector3.new(s * (face + 1.6), ay - h * 0.14 + 0.6, z + 0.4)
			local b2 = Vector3.new(s * (face + 2.0), ay - h * 0.14 + 3.2, z + 0.4)
			limb(out, 0.7, { b0, b1, b2 }, C.green2, TRIM)
			ball(out, 0.9, b2.X, b2.Y + 0.9, b2.Z, C.gold, TRIM)
		end
	end
end

-- Дальняя версия: подиум жильца и выросты редкости (сам жилец — настоящая модель).
function Saloon.Far(out, tier: number, f: number, h: number, _frame)
	local FAR = { variant = "LegoSquaresFar", collide = false }
	local at, sx, sz, ph = Saloon.Spot(tier, f)
	box(out, sx, ph, sz, 0, f + ph / 2, at.Z, C.red, FAR)
	box(out, sx - 0.8, 0.2, sz - 0.8, 0, f + ph + 0.2 / 2, at.Z, C.cream, FAR)
	if tier == 5 then
		local cx, cz = -(HX - W / 2), -(HZ - W / 2)
		box(out, 1.2, h * 0.7, 0.7, cx + 0.6, h * 0.45, cz - W / 2 - 0.4, C.green, FAR)
		box(out, 0.7, h * 0.5, 1.2, cx - W / 2 - 0.4, h * 0.6, cz + 0.6, C.green, FAR)
	elseif tier == 6 then
		for i, sgn in { -1, 1 } do
			local ay = h * (if i == 1 then 0.36 else 0.5)
			local face = HX + 1.0
			box(out, 3.6, 2.0, 2.0, sgn * (face + 1.5), ay + 0.5, -(HZ + 1.0) + 2.6, C.green2, FAR)
			box(out, 2.2, 10.5, 1.7, sgn * (face + 2.3), ay + 6.6, -(HZ + 1.0) + 2.6, C.green2, FAR)
			box(out, 4.8, 4.8, 4.8, sgn * (face + 2.2), ay + 15.8, -(HZ + 1.0) + 2.6, C.gold, FAR)
		end
	end
end

return Saloon

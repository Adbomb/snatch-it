-- Этаж башни в формате «витрина» (D74, вариант B): единый каркас на общих осях (плита с кантом, четыре угловые
-- колонны, цельное стекло фасада и боков — рама только по краям) и комната-диорама темы за стеклом. Редкость этажа —
-- материал каркаса и высота; тема комнаты одна на все редкости (салун остаётся салуном):
--   1 Деревянный — тёплое дерево, простые капители;            2 Каменный — серый камень, руст, кованые фонари;
--   3 Мраморный — белый мрамор, каннелюры, бронза;              4 Золотой — слоновая кость и золото;
--   5 Мифический — тёмный камень, аметист, светлые прожилки;    6 Космический — ночное небо и золото, радужный кант.
-- След у всех один; у Космического каркас выходит за след на 1 стад. Выше верхней плиты ничего нет; купол — только у
-- колпака башни (Cap). Источников света на этаже — 2 (у Космического 3). Дальняя версия (Far) — каркас, светлый проём
-- и кант, до 40 деталей. Координаты — в осях этажа: начало — центр низа плиты, перед — −Z.
-- Только кирпичи: жильца ставит World/ShowcasePreview. Зависит от ShowcaseKit, ShowcaseSaloon, ShowcaseOcean,
-- ModelBuilder, GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Kit = require(ServerScriptService.Server.World.Models.ShowcaseKit)
local ShowcaseOcean = require(ServerScriptService.Server.World.Models.ShowcaseOcean)
local ShowcaseSaloon = require(ServerScriptService.Server.World.Models.ShowcaseSaloon)

type Brick = ModelBuilder.Brick

local ShowcaseFloor = {}

local HX, HZ, SLAB, W = Kit.HX, Kit.HZ, Kit.SLAB, Kit.W
local box, tilt, cylZ, cylX, hex, with = Kit.box, Kit.tilt, Kit.cylZ, Kit.cylX, Kit.hex, Kit.with
local DECO = Kit.DECO

-- Высота этажа по редкости (D74): FloorHeight × 1 / 1.35 / 1.6 / 1.9 / 2.3 / 3.
ShowcaseFloor.HeightFactor = { 1, 1.35, 1.6, 1.9, 2.3, 3 }
ShowcaseFloor.Slab = SLAB
ShowcaseFloor.Keys = { "Wood", "Stone", "Marble", "Gold", "Mythic", "Cosmic" } -- порядок Config/FloorRarity.Order
ShowcaseFloor.Budget = { 250, 300, 350, 400, 450, 500 } -- деталей на этаж (телефон)
ShowcaseFloor.FarBudget = 40
ShowcaseFloor.Themes = { Saloon = ShowcaseSaloon, Ocean = ShowcaseOcean }

function ShowcaseFloor.Height(tier: number): number
	return math.floor(GameConfig.Tower.FloorHeight * ShowcaseFloor.HeightFactor[tier] + 0.5)
end

-- Палитра каркаса: два основных цвета и один акцент на редкость (core — сердцевина плиты, почти не видна).
local F = {
	{ main = hex("E2BE86"), second = hex("C9A06A"), accent = hex("5A3A20"), core = hex("8A5A2B"), out = 0 },
	{ main = hex("9EA2AA"), second = hex("7C8089"), accent = hex("2B2C30"), core = hex("5F636B"), out = 0 },
	{ main = hex("F5F2EC"), second = hex("DDDAD3"), accent = hex("B07A3C"), core = hex("C9C6BF"), out = 0 },
	{ main = hex("F3E9D2"), second = hex("E9B43A"), accent = hex("B98A1E"), core = hex("D9CDB2"), out = 0 },
	{ main = hex("2F2B3A"), second = hex("423B52"), accent = hex("9B5DE5"), core = hex("221F2B"), out = 0 },
	{ main = hex("0F1634"), second = hex("1B2552"), accent = hex("E9B43A"), core = hex("0B1026"), out = 1.0 },
}
local VEIN_MARBLE = hex("A9A7A3")
local VEIN_MYTHIC = hex("CDB0FF")
local STAR_PALE = hex("FFF1C4")
local LAMP = hex("FFD98A")
local GLASS_COLOR = hex("D6F0FF")
local GLOW = { material = Enum.Material.SmoothPlastic, collide = false, shadow = false } -- светлые прожилки и контур
local GEM = { material = Enum.Material.Glass, transparency = 0.12, collide = false } -- аметист

ShowcaseFloor.Frame = F

local function colW(tier: number): number
	return if tier == 6 then W + 0.6 else W
end

-- Ступенчатый кристалл: тело и более узкое остриё вдоль dir (резкие ступени D39), от точки base.
local function crystal(out: { Brick }, base: Vector3, dir: Vector3, len: number, r: number, color: Color3, extra: any?)
	local d = dir.Unit
	local up = if math.abs(d.Y) > 0.95 then Vector3.xAxis else Vector3.yAxis
	local cf = CFrame.lookAt(base, base + d, up) * CFrame.Angles(math.rad(-90), 0, 0) -- ось Y бруска вдоль dir
	local spin = CFrame.Angles(0, math.rad(45), 0)
	local e = extra or GEM
	tilt(out, r * 2, len * 0.72, r * 2, cf * CFrame.new(0, len * 0.36, 0) * spin, color, e)
	tilt(out, r * 1.3, len * 0.36, r * 1.3, cf * CFrame.new(0, len * 0.82, 0) * spin, color, e)
end

-- Радужный цвет по доле круга (тонкий кант Космического).
local function rainbow(t: number): Color3
	return Color3.fromHSV(t % 1, 0.62, 1)
end

-- Плита этажа на высоте y: сердцевина по следу и пояс-кант по кромке (материал — по названию редкости).
local function slab(out: { Brick }, tier: number, y: number)
	local f = F[tier]
	local ix, iz = HX + f.out / 2, HZ + f.out / 2 -- край сердцевины (у Космического шире — не под порогом стекла)
	local e = 0.6 + f.out / 2
	box(out, ix * 2, SLAB, iz * 2, 0, y + SLAB / 2, 0, f.core)
	-- ряд пояса вдоль стороны side (1 — перед, 2 — зад, 3 — лево, 4 — право): n сегментов, цвет и вынос — от номера
	local function row(
		side: number,
		n: number,
		paint: (k: number) -> (Color3, number),
		h: number,
		yc: number,
		extra: any?
	)
		local alongX = side <= 2
		local sign = if side % 2 == 1 then -1 else 1
		local a0 = if alongX then -ix - e else -iz
		local a1 = -a0
		for k = 0, n - 1 do
			local s0, s1 = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
			local color, depth = paint(k + side)
			if alongX then -- крайние сегменты длиннее на свой вынос: торцы накладок не совпадают с торцом пояса
				s0 -= if k == 0 then depth - e else 0
				s1 += if k == n - 1 then depth - e else 0
				box(out, s1 - s0, h, depth, (s0 + s1) / 2, yc, sign * (iz + depth / 2), color, extra)
			else
				box(out, depth, h, s1 - s0, sign * (ix + depth / 2), yc, (s0 + s1) / 2, color, extra)
			end
		end
	end
	local function belt(
		nX: number,
		nZ: number,
		paint: (k: number) -> (Color3, number),
		h: number,
		yc: number,
		extra: any?
	)
		row(1, nX, paint, h, yc, extra)
		row(2, nX, paint, h, yc, extra)
		row(3, nZ, paint, h, yc, extra)
		row(4, nZ, paint, h, yc, extra)
	end
	local function plain(color: Color3, depth: number): (k: number) -> (Color3, number)
		return function()
			return color, depth
		end
	end
	local mid = y + SLAB / 2
	if tier == 1 then -- доски двух тонов
		belt(8, 7, function(k)
			return if k % 2 == 0 then f.main else f.second, e + (if k % 2 == 0 then 0.1 else 0)
		end, SLAB, mid)
	elseif tier == 2 then -- каменные блоки
		belt(6, 5, function(k)
			return if k % 2 == 0 then f.main else f.second, e + (if k % 2 == 0 then 0.15 else 0)
		end, SLAB, mid)
	elseif tier == 3 then -- белый мрамор с прожилками, бронзовая кромка снизу
		belt(1, 1, plain(f.main, e), SLAB, mid)
		belt(1, 1, plain(f.accent, e + 0.12), 0.22, y + 0.21, DECO)
		for i = 0, 5 do -- прожилки на переднем и заднем поясе
			local x = -15 + i * 6 + Kit.rand(i) * 2
			local a = math.rad(if i % 2 == 0 then 24 else -31)
			for _, s in { -1, 1 } do
				local cf = CFrame.new(x * s, mid + 0.15, s * (iz + e + 0.01)) * CFrame.Angles(0, 0, a)
				tilt(out, 2.6, 0.13, 0.06, cf, VEIN_MARBLE, DECO)
			end
		end
		for i = 0, 3 do
			local z = -12 + i * 8 + Kit.rand(i + 9) * 2
			local a = math.rad(if i % 2 == 0 then -27 else 22)
			for _, s in { -1, 1 } do
				local cf = CFrame.new(s * (ix + e + 0.01), mid + 0.15, z * s) * CFrame.Angles(a, 0, 0)
				tilt(out, 0.06, 0.13, 2.6, cf, VEIN_MARBLE, DECO)
			end
		end
	elseif tier == 4 then -- золотой карниз: пояс и два валика
		belt(1, 1, plain(f.second, e), SLAB, mid)
		belt(1, 1, plain(f.accent, e + 0.28), 0.36, y + SLAB - 0.3, DECO)
		belt(1, 1, plain(f.accent, e + 0.14), 0.26, y + 0.25, DECO)
	elseif tier == 5 then -- тёмный камень, тонкий аметистовый кант
		belt(1, 1, plain(f.second, e), SLAB, mid)
		belt(1, 1, plain(f.accent, e + 0.14), 0.34, mid, DECO)
	else -- ночное небо: золотые кромки, тонкий радужный кант
		belt(1, 1, plain(f.second, e), SLAB, mid)
		belt(1, 1, plain(f.accent, e + 0.12), 0.2, y + SLAB - 0.2, DECO)
		belt(1, 1, plain(f.accent, e + 0.12), 0.2, y + 0.2, DECO)
		row(1, 8, function(k)
			return rainbow(k / 8), e + 0.22
		end, 0.3, mid, GLOW)
		row(2, 8, function(k)
			return rainbow(1 - k / 8), e + 0.22
		end, 0.3, mid, GLOW)
		row(3, 7, function(k)
			return rainbow(k / 7 + 0.5), e + 0.22
		end, 0.3, mid, GLOW)
		row(4, 7, function(k)
			return rainbow(0.5 - k / 7), e + 0.22
		end, 0.3, mid, GLOW)
	end
end

-- Угловая колонна от плиты до верха этажа. sx, sz — знаки угла; оси колонн у всех редкостей общие.
local function column(out: { Brick }, tier: number, sx: number, sz: number, y0: number, y1: number)
	local f = F[tier]
	local w = colW(tier)
	local cx, cz = sx * (HX + f.out - w / 2), sz * (HZ + f.out - w / 2)
	local seed = (if sx > 0 then 1 else 0) + (if sz > 0 then 2 else 0)
	-- ярус: квадрат стороны side высотой h с низом на y
	local function level(side: number, h: number, y: number, color: Color3, extra: any?)
		box(out, side, h, side, cx, y + h / 2, cz, color, extra)
	end
	-- накладка на обеих наружных гранях ствола стороны side: ширина along, высота tall, вынос proud, сдвиг a
	local function plate(side: number, along: number, tall: number, proud: number, a: number, yc: number, color: Color3)
		box(out, along, tall, proud, cx + a, yc, cz + sz * (side / 2 + proud / 2), color, DECO)
		box(out, proud, tall, along, cx + sx * (side / 2 + proud / 2), yc, cz + a, color, DECO)
	end
	-- четыре «листа» по углам капители
	local function leaves(side: number, size: number, h: number, y: number, color: Color3)
		for _, a in { -1, 1 } do
			for _, b in { -1, 1 } do
				box(out, size, h, size, cx + a * side / 2, y + h / 2, cz + b * side / 2, color, DECO)
			end
		end
	end
	if tier == 1 then
		level(w + 0.6, 1.2, y0, f.second)
		level(w + 0.3, 0.4, y0 + 1.2, f.main)
		local s0, s1 = y0 + 1.6, y1 - 1.7
		level(w, s1 - s0, s0, f.main)
		plate(w, w - 1.2, s1 - s0 - 1.2, 0.15, 0, (s0 + s1) / 2, f.second)
		level(w + 0.3, 0.4, y1 - 1.7, f.second)
		level(w + 0.8, 0.7, y1 - 1.3, f.main)
		level(w + 1.3, 0.6, y1 - 0.6, f.second)
	elseif tier == 2 then
		level(w + 0.9, 1.4, y0, f.second)
		local y = y0 + 1.4
		for k = 1, 4 do -- руст: блоки через один шире
			level(if k % 2 == 1 then w + 0.5 else w + 0.1, 1.8, y, if k % 2 == 1 then f.main else f.second)
			y += 1.8
		end
		level(w - 0.3, y1 - 2.0 - y, y, f.main)
		level(w, 0.45, y1 - 2.0, f.second)
		level(w + 0.7, 0.85, y1 - 1.55, f.main)
		level(w + 1.3, 0.7, y1 - 0.7, f.second)
		if sz < 0 then -- кованый фонарь на кронштейне у передних колонн
			local face = cz - (w - 0.3) / 2
			local ly = y0 + (y1 - y0) * 0.56
			box(out, 0.25, 0.25, 1.6, cx, ly, face - 0.8, f.accent, DECO)
			box(out, 0.25, 0.9, 0.25, cx, ly - 0.575, face - 0.3, f.accent, DECO)
			box(out, 0.12, 0.5, 0.12, cx, ly - 0.375, face - 1.3, f.accent, DECO)
			box(out, 1.0, 0.22, 1.0, cx, ly - 0.735, face - 1.3, f.accent, DECO)
			Kit.lamp(out, 0.72, 1.1, 0.72, cx, ly - 1.395, face - 1.3, LAMP)
			box(out, 0.9, 0.2, 0.9, cx, ly - 2.045, face - 1.3, f.accent, DECO)
		end
	elseif tier == 3 then
		level(w + 0.8, 1.0, y0, f.main)
		level(w + 0.5, 0.35, y0 + 1.0, f.accent)
		level(w + 0.2, 0.45, y0 + 1.35, f.second)
		local s0, s1 = y0 + 1.8, y1 - 2.2
		local sw = w - 0.5
		level(sw, s1 - s0, s0, f.second)
		for _, a in { -0.95, 0, 0.95 } do -- каннелюры
			plate(sw, 0.5, s1 - s0 - 0.5, 0.14, a, (s0 + s1) / 2, f.main)
		end
		level(w - 0.2, 0.3, y1 - 2.2, f.accent)
		level(w + 0.4, 0.9, y1 - 1.9, f.main)
		local half = (w + 0.4) / 2
		for _, a in { -1, 1 } do -- волюты
			cylZ(out, 0.5, 0.3, cx + a * (half - 0.35), y1 - 1.8, cz + sz * (half + 0.1), f.second, DECO)
			cylX(out, 0.5, 0.3, cx + sx * (half + 0.1), y1 - 1.8, cz + a * (half - 0.35), f.second, DECO)
		end
		level(w + 0.9, 0.18, y1 - 1.0, f.accent)
		level(w + 1.3, 0.82, y1 - 0.82, f.main)
		-- прожилки на плинте
		local pf = (w + 0.8) / 2 + 0.01
		local a1 = CFrame.new(cx + 0.3, y0 + 0.5, cz + sz * pf) * CFrame.Angles(0, 0, math.rad(21))
		tilt(out, 1.7, 0.12, 0.06, a1, VEIN_MARBLE, DECO)
		local a2 = CFrame.new(cx + sx * pf, y0 + 0.5, cz - 0.3) * CFrame.Angles(math.rad(-24), 0, 0)
		tilt(out, 0.06, 0.12, 1.7, a2, VEIN_MARBLE, DECO)
	elseif tier == 4 then
		level(w + 0.8, 1.2, y0, f.main)
		level(w + 1.0, 0.3, y0 + 1.2, f.second)
		level(w + 0.5, 0.4, y0 + 1.5, f.accent)
		local s0, s1 = y0 + 1.9, y1 - 2.6
		local sw = w - 0.3
		level(sw, s1 - s0, s0, f.main)
		plate(sw, 0.8, s1 - s0 - 1.6, 0.12, 0, (s0 + s1) / 2, f.second)
		level(w, 0.35, y1 - 2.6, f.accent)
		level(w + 0.5, 1.1, y1 - 2.25, f.second)
		leaves(w + 0.5, 1.0, 0.9, y1 - 2.0, f.accent)
		level(w + 1.2, 0.55, y1 - 1.15, f.main)
		level(w + 1.5, 0.6, y1 - 0.6, f.second)
	elseif tier == 5 then
		level(w + 1.0, 1.6, y0, f.main)
		level(w + 0.5, 0.5, y0 + 1.6, f.second)
		local s0, s1 = y0 + 2.1, y1 - 2.4
		local sw = w - 0.1
		level(sw, s1 - s0, s0, f.main)
		level(w + 0.3, 0.7, y0 + (y1 - y0) * 0.5, f.second)
		-- светлые прожилки зигзагом по наружным граням
		local n = math.max(4, math.floor((s1 - s0) / 5))
		local step = (s1 - s0 - 2) / n
		local lean = math.atan(1.1 / step)
		local len = math.sqrt(step * step + 1.21) + 0.1
		local fz, fx = cz + sz * (sw / 2 + 0.03), cx + sx * (sw / 2 + 0.03)
		for k = 0, n - 1 do
			local yc = s0 + 1 + step * (k + 0.5)
			local a = if (k + seed) % 2 == 0 then lean else -lean
			tilt(out, 0.2, len, 0.06, CFrame.new(cx, yc, fz) * CFrame.Angles(0, 0, a), VEIN_MYTHIC, GLOW)
			tilt(out, 0.06, len, 0.2, CFrame.new(fx, yc, cz) * CFrame.Angles(a, 0, 0), VEIN_MYTHIC, GLOW)
		end
		level(w + 0.3, 0.4, y1 - 2.4, f.second)
		level(w + 0.9, 1.2, y1 - 2.0, f.main)
		level(w + 1.4, 0.8, y1 - 0.8, f.second)
		-- друзы аметиста: у подножия и под капителью
		local corner = Vector3.new(cx + sx * (w / 2 + 0.2), y0 + 1.5, cz + sz * (w / 2 + 0.2))
		crystal(out, corner, Vector3.new(sx * 0.3, 1, sz * 0.3), 3.6, 0.5, f.accent)
		if sz < 0 then
			local c2 = corner + Vector3.new(-sx * 1.3, 0, 0.2 * sz)
			crystal(out, c2, Vector3.new(-sx * 0.15, 1, sz * 0.45), 2.6, 0.4, f.accent)
			local c3 = corner + Vector3.new(0.2 * sx, 0, -sz * 1.3)
			crystal(out, c3, Vector3.new(sx * 0.45, 1, -sz * 0.15), 2.3, 0.38, f.accent)
		end
		local under = Vector3.new(cx + sx * (w / 2 + 0.3), y1 - 2.2, cz + sz * (w / 2 + 0.3))
		crystal(out, under, Vector3.new(sx * 0.35, -1, sz * 0.35), 2.4, 0.36, f.accent)
	else
		-- пьедестал: плинт, золотая ступень, тумба со звездой, золотой карниз
		level(w + 0.8, 2.2, y0, f.main)
		level(w + 1.0, 0.35, y0 + 2.2, f.accent)
		level(w + 0.3, 1.5, y0 + 2.55, f.second)
		level(w + 0.7, 0.35, y0 + 4.05, f.accent)
		local s0, s1 = y0 + 4.4, y1 - 4.6
		local sw = w - 0.3
		level(sw, s1 - s0, s0, f.main)
		for _, t in { 0.34, 0.67 } do -- тонкие золотые пояски
			level(sw + 0.3, 0.3, s0 + (s1 - s0) * t, f.accent, DECO)
		end
		-- мягкий светлый контур: тонкие рейки по наружному ребру и краям наружных граней
		local edge = sw / 2 + 0.02
		local ym, yl = (s0 + s1) / 2, s1 - s0 - 0.4
		box(out, 0.2, yl, 0.2, cx + sx * edge, ym, cz + sz * edge, STAR_PALE, GLOW)
		box(out, 0.14, yl, 0.14, cx - sx * (edge - 0.3), ym, cz + sz * edge, STAR_PALE, GLOW)
		box(out, 0.14, yl, 0.14, cx + sx * edge, ym, cz - sz * (edge - 0.3), STAR_PALE, GLOW)
		-- золотые звёзды-ромбы на наружных гранях ствола и по одной крупной на тумбе
		local turnZ, turnX = CFrame.Angles(0, 0, math.rad(45)), CFrame.Angles(math.rad(45), 0, 0)
		for k = 1, 9 do
			local r1, r2, r3 = Kit.rand(seed * 31 + k), Kit.rand(seed * 17 + k * 3), Kit.rand(seed * 7 + k * 5)
			local yc = s0 + 1.4 + (s1 - s0 - 2.8) * (k - 0.5 + (r1 - 0.5) * 0.7) / 9
			local a = (r2 - 0.5) * (sw - 1.8)
			local size = 0.45 + r3 * 0.65
			local color = if k % 3 == 0 then STAR_PALE else f.accent
			if k % 2 == 0 then
				tilt(out, size, size, 0.1, CFrame.new(cx + a, yc, cz + sz * (sw / 2 + 0.03)) * turnZ, color, DECO)
			else
				tilt(out, 0.1, size, size, CFrame.new(cx + sx * (sw / 2 + 0.03), yc, cz + a) * turnX, color, DECO)
			end
		end
		local die = (w + 0.3) / 2 + 0.03
		tilt(out, 0.95, 0.95, 0.1, CFrame.new(cx, y0 + 3.3, cz + sz * die) * turnZ, f.accent, DECO)
		tilt(out, 0.1, 0.95, 0.95, CFrame.new(cx + sx * die, y0 + 3.3, cz) * turnX, f.accent, DECO)
		-- капитель: золотая шейка, колокол с листьями, ступенчатая золотая корона
		level(w, 0.5, y1 - 4.6, f.accent)
		level(w + 0.5, 2.0, y1 - 4.1, f.second)
		leaves(w + 0.5, 1.3, 1.7, y1 - 3.8, f.accent)
		level(w + 1.2, 0.6, y1 - 2.1, f.main)
		level(w + 1.6, 0.5, y1 - 1.5, f.accent)
		level(w + 1.3, 0.4, y1 - 1.0, f.main)
		level(w + 1.8, 0.6, y1 - 0.6, f.accent)
	end
end

-- Цвет рамы стекла: тёмное дерево, камень, бронза, золото, тёмный камень, золото.
local function frameTone(tier: number): Color3
	local f = F[tier]
	return if tier == 2 or tier == 5 then f.second else f.accent
end

-- Цельное стекло фасада и боков: низкий порог и верхняя балка — рама только по краям (жильца ничто не перекрывает).
-- Задняя стена снаружи — в материале каркаса, с лопатками.
local function glazing(out: { Brick }, tier: number, y0: number, y1: number)
	local f = F[tier]
	local w = colW(tier)
	local sill, head = 0.7, 1.0
	local g0, g1 = y0 + sill, y1 - 0.4 - head
	local tone = frameTone(tier)
	local function run(alongX: boolean, half: number, fixed: number)
		local function put(sa: number, sy: number, sd: number, a: number, y: number, color: Color3, extra: any?)
			if alongX then
				box(out, sa, sy, sd, a, y, fixed, color, extra)
			else
				box(out, sd, sy, sa, fixed, y, a, color, extra)
			end
		end
		put(half * 2, sill, 0.8, 0, y0 + sill / 2, tone)
		put(half * 2, head, 0.8, 0, y1 - 0.4 - head / 2, tone)
		put(half * 2, g1 - g0, 0.2, 0, (g0 + g1) / 2, GLASS_COLOR, Kit.GLASS)
		if tier == 4 or tier == 6 then -- золотая рама: тонкие стойки вплотную к колоннам
			for _, s in { -1, 1 } do
				put(0.45, g1 - g0, 0.5, s * (half - 0.62), (g0 + g1) / 2, f.accent, DECO)
			end
		end
	end
	run(true, HX + f.out - w + 0.4, -(HZ + f.out) + 1.0)
	run(false, HZ + f.out - w + 0.4, -(HX + f.out) + 1.0)
	run(false, HZ + f.out - w + 0.4, HX + f.out - 1.0)
	local zb = HZ + f.out - 0.45
	local half = HX + f.out - w + 0.4
	box(out, half * 2, y1 - y0 - 0.45, 0.5, 0, (y0 + y1 - 0.45) / 2, zb, f.second)
	for _, x in { -8, 0, 8 } do
		box(out, 2.4, y1 - y0 - 1.4, 0.25, x, (y0 + y1 - 0.45) / 2, zb + 0.375, f.main, DECO)
	end
end

export type Built = { bricks: { Brick }, height: number, resident: Vector3, scale: number, item: string }

-- Этаж-витрина темы theme ("Saloon" | "Ocean") редкости tier (1…6).
function ShowcaseFloor.Build(theme: string, tier: number): Built
	local out: { Brick } = {}
	local t = ShowcaseFloor.Themes[theme]
	local h = ShowcaseFloor.Height(tier)
	slab(out, tier, 0)
	for _, sx in { -1, 1 } do
		for _, sz in { -1, 1 } do
			column(out, tier, sx, sz, SLAB, h)
		end
	end
	glazing(out, tier, SLAB, h)
	local at = t.Build(out, tier, SLAB, h)
	t.Grow(out, tier, h, F[tier], crystal)
	return { bricks = out, height = h, resident = at, scale = t.Scale[tier], item = t.Item }
end

-- Дальняя версия (от 150 стадов): каркас, кант и светлый проём — тёплая стена сразу за жильцом (жилец остаётся
-- настоящей моделью); без стекла, мебели и источников света.
function ShowcaseFloor.Far(theme: string, tier: number): Built
	local out: { Brick } = {}
	local t = ShowcaseFloor.Themes[theme]
	local f = F[tier]
	local h = ShowcaseFloor.Height(tier)
	local w = colW(tier)
	local ix, iz = HX + f.out / 2, HZ + f.out / 2
	local e = 0.6 + f.out / 2
	local FAR = { variant = "LegoSquaresFar", collide = false }
	local band = if tier <= 3 then f.main else f.second
	box(out, ix * 2, SLAB, iz * 2, 0, SLAB / 2, 0, f.core, FAR)
	for _, s in { -1, 1 } do
		box(out, (ix + e) * 2, SLAB, e, 0, SLAB / 2, s * (iz + e / 2), band, FAR)
		box(out, e, SLAB, iz * 2, s * (ix + e / 2), SLAB / 2, 0, band, FAR)
	end
	if tier == 5 then
		box(out, (ix + e) * 2 + 0.3, 0.4, (iz + e) * 2 + 0.3, 0, SLAB / 2, 0, f.accent, FAR)
	elseif tier == 6 then
		local full = (ix + e + 0.2) * 2
		for k = 0, 5 do
			box(
				out,
				full / 6,
				0.4,
				(iz + e) * 2 + 0.4,
				-full / 2 + full * (k + 0.5) / 6,
				SLAB / 2,
				0,
				rainbow(k / 6),
				FAR
			)
		end
	end
	for _, sx in { -1, 1 } do
		for _, sz in { -1, 1 } do
			local cx, cz = sx * (HX + f.out - w / 2), sz * (HZ + f.out - w / 2)
			local cap = if tier == 6 then f.accent else f.second
			box(out, w + 0.8, 1.4, w + 0.8, cx, SLAB + 0.7, cz, if tier == 1 then f.second else f.main, FAR)
			box(out, w - 0.1, h - SLAB - 3.4, w - 0.1, cx, (SLAB + 1.4 + h - 2.0) / 2, cz, f.main, FAR)
			box(out, w + 1.2, 2.0, w + 1.2, cx, h - 1.0, cz, cap, FAR)
			if tier == 5 and sz < 0 then -- друза аметиста у передних колонн
				local base = Vector3.new(cx + sx * (w / 2 + 0.3), SLAB + 1.2, cz + sz * (w / 2 + 0.3))
				crystal(out, base, Vector3.new(sx * 0.3, 1, sz * 0.3), 4.0, 0.6, f.accent, FAR)
			end
		end
	end
	-- светлый проём: пол и потолок комнаты, тёплая светлая стена сразу за жильцом, порог по краям, задняя стена
	local zf, xs = -(HZ + f.out) + 1.0, HX + f.out - 1.0
	local zb = HZ + f.out - 0.7
	local zc = (zf + zb) / 2
	local floorY = SLAB + 0.36
	local at, _, sz = t.Spot(tier, floorY)
	local zg = at.Z + sz / 2 + 0.6 -- светлая стена — сразу за подиумом жильца
	local tone = frameTone(tier)
	local glow = with(GLOW, { name = "Glow" })
	box(out, xs * 2, h - floorY - 1.35, zb - zg, 0, (floorY + h - 1.35) / 2, (zg + zb) / 2, t.Glow[tier], glow)
	box(out, xs * 2 + 0.6, 1.35, zb - zf + 0.6, 0, h - 0.725, zc - 0.05, tone, FAR)
	box(out, xs * 2 + 0.6, 0.36, zb - zf + 0.3, 0, SLAB + 0.18, zc - 0.15, t.Glow[tier]:Lerp(tone, 0.45), FAR)
	box(out, xs * 2 - 1, 0.7, 0.8, 0, SLAB + 0.35, zf, tone, FAR)
	for _, s in { -1, 1 } do
		box(out, 0.8, 0.7, zg - zf, s * xs, SLAB + 0.35, (zf + zg) / 2 + 0.2, tone, FAR)
	end
	box(out, xs * 2 - 0.5, h - SLAB - 0.1, 0.5, 0, (SLAB + h - 0.1) / 2, zb + 0.25, f.second, FAR)
	box(out, xs * 2 - 0.4, 5.2, 0.3, 0, floorY + 2.6, zg - 0.15, t.Dado, FAR) -- цоколь стены: читается как комната
	t.Far(out, tier, floorY, h, F[tier])
	return { bricks = out, height = h, resident = at, scale = t.Scale[tier], item = t.Item }
end

-- Плита-кровля над верхним этажом (под колпак башни): плита с кантом редкости верхнего этажа.
function ShowcaseFloor.Roof(tier: number): { Brick }
	local out: { Brick } = {}
	slab(out, tier, 0)
	return out
end

-- Поворот углового клина: его вершина — над углом (+X, −Z); разворот ставит её на ось кристалла (проверено в Studio).
local WEDGE_TURN = CFrame.Angles(0, math.rad(180), 0)

-- Колпак башни C «Ловибум-кристалл»: сад на кровле, золотое кольцо, четыре когтя держат кристалл (знак игры).
-- Начало — центр верха плиты-кровли. Купола и шпили есть только здесь.
function ShowcaseFloor.Cap(): { Brick }
	local out: { Brick } = {}
	local green, green2 = hex("4E9A3A"), hex("3C8230")
	local gold, gold2 = hex("E9B43A"), hex("B98A1E")
	box(out, HX * 2 - 2, 1.2, HZ * 2 - 2, 0, 0.6, 0, green, Kit.PROP)
	for k = 0, 9 do -- живая изгородь
		local a = math.pi * 2 * k / 10
		Kit.ball(out, 2.1, math.cos(a) * 13.6, 2.2, math.sin(a) * 12.6, if k % 2 == 0 then green2 else green, Kit.TRIM)
	end
	Kit.cyl(out, 10, 2.4, 0, 1.2, 0, gold)
	Kit.cyl(out, 8.8, 0.5, 0, 3.6, 0, gold2, Kit.TRIM)
	-- кристалл-бипирамида из восьми угловых клиньев
	local crystalColor = hex("38D6E0")
	local r, yMid, yLow, yTop = 7.6, 19.5, 5.2, 36
	local GEMC = { material = Enum.Material.Glass, transparency = 0.18, shape = "CornerWedge", collide = false }
	for q = 0, 3 do
		local rot = CFrame.Angles(0, math.rad(90 * q), 0)
		local up = CFrame.new(0, (yMid + yTop) / 2, 0) * rot * CFrame.new(r / 2, 0, -r / 2) * WEDGE_TURN
		table.insert(out, ModelBuilder.Brick(Vector3.new(r, yTop - yMid, r), up, crystalColor, GEMC))
		local down = CFrame.new(0, (yMid + yLow) / 2, 0)
			* CFrame.Angles(math.rad(180), 0, 0)
			* rot
			* CFrame.new(r / 2, 0, -r / 2)
			* WEDGE_TURN
		table.insert(out, ModelBuilder.Brick(Vector3.new(r, yMid - yLow, r), down, crystalColor, GEMC))
	end
	for k = 0, 3 do -- когти
		local a = math.rad(45 + 90 * k)
		local dir = Vector3.new(math.cos(a), 0, math.sin(a))
		local foot, tip = dir * 9.2 + Vector3.new(0, 3.4, 0), dir * 6.9 + Vector3.new(0, 22, 0)
		local cf = CFrame.lookAt((foot + tip) / 2, tip) * CFrame.Angles(math.rad(-90), 0, 0)
		tilt(out, 2.0, (tip - foot).Magnitude, 2.0, cf, gold, Kit.PROP)
		tilt(out, 2.6, 1.5, 2.6, cf * CFrame.new(0, -(tip - foot).Magnitude / 2 + 1.2, 0), gold2, Kit.TRIM)
		local hook = CFrame.lookAt(tip, tip - dir * 3 + Vector3.new(0, 2.4, 0)) * CFrame.Angles(math.rad(-90), 0, 0)
		tilt(out, 1.5, 3.6, 1.5, hook * CFrame.new(0, 1.3, 0), gold2, Kit.TRIM)
	end
	return out
end

return ShowcaseFloor

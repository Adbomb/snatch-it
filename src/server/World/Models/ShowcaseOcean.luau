-- Тема этажа-витрины «Океанариум Верблюда-аквариума» (D74, вариант B): комната за стеклом — песочный пол, бирюзовая
-- стена с плиточным поясом, светлый потолок с балками — и диорама, которая растёт с редкостью (тема одна на все):
--   1 настенный аквариум с рыбами, сундук, кораллы, спасательный круг, лампа-медуза, песчаный островок жильца;
--   2 + аквариум-колонна с пузырями и якорь, фонари;      3 + галерея-мостик с лестницей и иллюминаторами;
--   4 + атриум: крылья галереи, большая медуза-люстра, большой иллюминатор с рыбой;
--   5 + второй ярус, лампы-медузы на цепях, гигантская ламинария;   6 + героический объект — золотая раковина с
--   жемчужиной. Жилец стоит у самого стекла на низком островке — его ничто не перекрывает. Свет: общий тёплый и
-- прожектор на жильца (у Космического третий — на жемчужину). Наружные выросты (Grow): у Мифического коралл оплетает
-- переднюю колонну, у Космического из-за колонн выходят изогнутые коралловые ветви с шарами-аквариумами.
-- Только кирпичи. Зависит от ShowcaseKit.

local ServerScriptService = game:GetService("ServerScriptService")

local Kit = require(ServerScriptService.Server.World.Models.ShowcaseKit)

local HX, HZ, BACK, W = Kit.HX, Kit.HZ, Kit.BACK, Kit.W
local box, cyl, cylZ, cylX, ball, rod, limb, tilt =
	Kit.box, Kit.cyl, Kit.cylZ, Kit.cylX, Kit.ball, Kit.rod, Kit.limb, Kit.tilt
local hex = Kit.hex
local PROP, TRIM = Kit.PROP, Kit.TRIM

local Ocean = {}

Ocean.Item = "AquariumCamel"
Ocean.Scale = { 4.0, 4.9, 5.6, 6.3, 7.2, 8.4 } -- масштаб показа жильца по редкости
-- Цвет светлого проёма дальней версии: тёплая бирюза, ярче с редкостью.
Ocean.Glow = { hex("7FC4BE"), hex("8CCDC6"), hex("9AD6CE"), hex("A9DFD6"), hex("B8E7DE"), hex("CBF1E8") }
-- (Dado — цвет цоколя стены для дальней версии — задан ниже, после палитры.)
local SIZE = Vector3.new(2.868, 2.876, 1.228) -- размер жильца в натуральную величину (Config/Items)

local C = {
	wall = hex("1F7F92"),
	wall2 = hex("176273"),
	tile = hex("8FD3D9"),
	sand1 = hex("E8D2A2"),
	sand2 = hex("DCC08C"),
	ceiling = hex("DDF3EE"),
	beam = hex("2A9DAE"),
	deck = hex("2B8FA3"),
	white = hex("F4F6F2"),
	water = hex("49BDE6"),
	coral = hex("F2788C"),
	coral2 = hex("F59A4C"),
	kelp = hex("2FA36B"),
	kelp2 = hex("238556"),
	rock = hex("8C8F96"),
	wood = hex("8A5A2B"),
	wood2 = hex("6B4524"),
	gold = hex("E9B43A"),
	gold2 = hex("B98A1E"),
	brass = hex("C9A24A"),
	iron = hex("3A3F48"),
	red = hex("D9483B"),
	lamp = hex("FFE3A0"),
	jelly = hex("FFC6DC"),
	jelly2 = hex("F29BC0"),
	pearl = hex("FFF4F8"),
	warm = hex("FFE2B0"),
}
local FISH = { hex("F5A623"), hex("FDD835"), hex("E5533D"), hex("7C5CE0"), hex("F27BA5") }
Ocean.Dado = C.wall2
local PAL: Kit.Palette =
	{ deck = C.deck, trim = C.white, step1 = C.sand1, step2 = C.sand2, metal = C.brass, lamp = C.lamp }
local WATER = { material = Enum.Material.Glass, transparency = 0.45, collide = false, shadow = false }
local BOWL = { material = Enum.Material.Glass, transparency = 0.5, collide = false, shadow = false }

-- Оболочка комнаты: песочный пол, бирюзовая стена с плиточным поясом, светлый потолок с балками.
local function shell(out, y0: number, y1: number, o: number)
	local x1, z0 = HX - 1.4 + o, -(HZ - 1.4 + o)
	local n = 12
	local w = x1 * 2 / n
	for k = 0, n - 1 do -- полосы пола: через одну выше на 0.06
		local h = if k % 2 == 0 then 0.3 else 0.36
		local color = if k % 2 == 0 then C.sand1 else C.sand2
		box(out, w, h, BACK - z0, -x1 + w * (k + 0.5), y0 + h / 2, (z0 + BACK) / 2, color)
	end
	local half = HX + o - 3.0
	local wy0, wy1 = y0, y1 - 0.4
	box(out, half * 2, wy1 - wy0, 0.3, 0, (wy0 + wy1) / 2, BACK + 0.15, C.wall)
	box(out, half * 2 - 1, 4.4, 0.15, 0, wy0 + 2.5, BACK - 0.075, C.wall2) -- цоколь
	box(out, half * 2 - 0.6, 0.9, 0.3, 0, wy0 + 5.15, BACK - 0.15, C.tile, TRIM) -- плиточный пояс
	box(out, half * 2 - 1.8, 0.5, 0.25, 0, wy1 - 1.6, BACK - 0.125, C.tile, TRIM) -- пояс под потолком
	box(out, (HX + o) * 2 - 1.4, 0.36, (HZ + o) * 2 - 1.4, 0, y1 - 0.22, 0, C.ceiling) -- потолок: с земли виден он
	for _, z in { -9, 0, 9 } do
		box(out, (HX + o) * 2 - 1.8, 0.9, 1.2, 0, y1 - 0.75, z, C.beam, TRIM)
	end
	for _, x in { -8, 8 } do
		box(out, 1.0, 0.65, (HZ + o) * 2 - 1.8, x, y1 - 0.675, 0, C.white, TRIM)
	end
end

-- Рыбка: тело и хвост; dir — куда плывёт (1 — вправо), s — размер.
local function fish(out, x: number, y: number, z: number, s: number, dir: number, color: Color3)
	box(out, 1.5 * s, 0.9 * s, 0.35 * s, x, y, z, color, TRIM)
	box(out, 0.5 * s, 0.8 * s, 0.2 * s, x - dir * 1.0 * s, y, z, C.white, TRIM)
	box(out, 0.2 * s, 0.2 * s, 0.52 * s, x + dir * 0.45 * s, y + 0.15 * s, z, C.iron, TRIM)
end

-- Ветка коралла веером (плоская, резкие ступени): ствол, две ветви, по веточке на каждой. yaw — поворот веера.
-- Толщина у всех частей разная: ветви сходятся в развилке, одинаковые грани там мерцали бы.
local function coralFan(out, x: number, y: number, z: number, s: number, color: Color3, yaw: number)
	local base = CFrame.new(x, y, z) * CFrame.Angles(0, math.rad(yaw), 0)
	tilt(out, 0.55 * s, 1.5 * s, 0.62 * s, base * CFrame.new(0, 0.75 * s, 0), color, TRIM)
	for _, sgn in { -1, 1 } do
		local fork = base * CFrame.new(0, 1.4 * s, 0) * CFrame.Angles(0, 0, math.rad(-32 * sgn))
		tilt(out, 0.45 * s, 1.5 * s, (0.46 + sgn * 0.05) * s, fork * CFrame.new(0, 0.75 * s, 0), color, TRIM)
		local twig = fork * CFrame.new(0, 1.4 * s, 0) * CFrame.Angles(0, 0, math.rad(42 * sgn))
		tilt(out, 0.36 * s, 1.0 * s, (0.3 + sgn * 0.04) * s, twig * CFrame.new(0, 0.5 * s, 0), color, TRIM)
	end
end

-- Куст кораллов: камень-основание и два веера разного цвета.
local function coralBush(out, x: number, y: number, z: number, s: number, seed: number)
	cyl(out, 1.2 * s, 0.6 * s, x, y, z, C.rock)
	coralFan(out, x - 0.2 * s, y + 0.5 * s, z, 1.15 * s, C.coral, seed * 40)
	coralFan(out, x + 0.35 * s, y + 0.5 * s, z + 0.3 * s, 0.8 * s, C.coral2, seed * 40 + 75)
end

-- Сундук с сокровищами: короб, круглая крышка, золотые полосы, монеты.
local function chest(out, x: number, y: number, z: number)
	box(out, 3.6, 1.8, 2.2, x, y + 0.9, z, C.wood, PROP)
	cylX(out, 1.1, 3.5, x, y + 1.8, z, C.wood2)
	for _, s in { -1, 1 } do
		box(out, 0.35, 1.9, 2.3, x + s * 1.1, y + 1.05, z, C.gold, TRIM)
		cylX(out, 1.16, 0.29, x + s * 1.1, y + 1.8, z, C.gold, TRIM)
	end
	box(out, 0.6, 0.7, 0.2, x, y + 1.5, z - 1.15, C.gold2, TRIM)
	cyl(out, 0.5, 0.15, x - 2.6, y, z - 0.9, C.gold, TRIM)
	cyl(out, 0.5, 0.15, x - 2.3, y + 0.15, z - 0.7, C.gold, TRIM)
	cyl(out, 0.5, 0.15, x + 2.5, y, z - 1.3, C.gold, TRIM)
end

-- Спасательный круг на стене (лицом в −Z).
local function lifeRing(out, x: number, y: number, r: number)
	cylZ(out, r, 0.45, x, y, BACK - 0.225, C.white)
	cylZ(out, r * 0.52, 0.5, x, y, BACK - 0.25, C.wall, TRIM)
	for k = 0, 3 do
		local a = math.rad(45 + k * 90)
		local cf = CFrame.new(x + math.cos(a) * r * 0.76, y + math.sin(a) * r * 0.76, BACK - 0.25)
			* CFrame.Angles(0, 0, a)
		tilt(out, r * 0.5, r * 0.5, 0.52, cf, C.red, TRIM)
	end
end

-- Иллюминатор на стене: латунная рама и вода; с рыбкой — если fishColor задан.
local function porthole(out, x: number, y: number, r: number, rim: Color3, fishColor: Color3?)
	cylZ(out, r, 0.4, x, y, BACK - 0.2, rim)
	cylZ(out, r * 0.78, 0.5, x, y, BACK - 0.25, C.water, TRIM)
	if fishColor then
		fish(out, x, y, BACK - 0.6, r * 0.42, 1, fishColor)
	end
end

-- Лампа-медуза: купол, кайма, щупальца, подвес до потолка (свет — общий источник этажа).
local function jelly(out, x: number, y: number, z: number, r: number, ceilingY: number, tint: Color3)
	Kit.ball(out, r, x, y, z, tint, Kit.LAMP)
	cyl(out, r * 1.04, r * 0.3, x, y - r * 0.35, z, C.jelly2, TRIM)
	box(out, 0.16, ceilingY - y - r * 0.8, 0.16, x, (ceilingY + y + r * 0.8) / 2, z, C.brass, TRIM)
	for k = 0, 4 do
		local a = math.rad(k * 72)
		local len = r * (1.2 + (k % 2) * 0.5)
		local tx, tz = x + math.cos(a) * r * 0.6, z + math.sin(a) * r * 0.6
		box(out, r * 0.16, len, r * 0.16, tx, y - r * 0.5 - len / 2, tz, C.jelly2, TRIM)
	end
end

-- Настенный аквариум: рама, песок, вода, рыбы, водоросли и коралл. Центр по X — x, низ — y, ширина w, высота h.
local function wallTank(out, x: number, y: number, w: number, h: number, fishes: number)
	local z = BACK - 1.0
	box(out, w + 0.8, 0.8, 2.2, x, y + 0.4, z - 0.1, C.wall2, PROP)
	box(out, w + 0.8, 0.6, 2.2, x, y + h + 1.1, z - 0.1, C.wall2, PROP)
	for _, s in { -1, 1 } do
		box(out, 0.5, h, 2.0, x + s * (w / 2 + 0.15), y + 0.8 + h / 2, z, C.wall2, TRIM)
	end
	box(out, w - 0.2, 0.5, 1.6, x, y + 1.05, z, C.sand1, TRIM)
	box(out, w - 0.2, h - 0.5, 1.6, x, y + 1.3 + (h - 0.5) / 2, z, C.water, WATER)
	for k = 0, fishes - 1 do
		local fx = x - w / 2 + w * (k + 0.5) / fishes
		local fy = y + 2.2 + ((k * 7) % 5) / 5 * (h - 2.6)
		fish(out, fx, fy, z - 0.2, 0.8 + (k % 3) * 0.2, if k % 2 == 0 then 1 else -1, FISH[k % 5 + 1])
	end
	box(out, 0.3, h * 0.6, 0.3, x - w * 0.38, y + 1.3 + h * 0.3, z + 0.3, C.kelp, TRIM)
	box(out, 0.3, h * 0.42, 0.3, x - w * 0.3, y + 1.3 + h * 0.21, z + 0.1, C.kelp2, TRIM)
	coralFan(out, x + w * 0.36, y + 1.3, z + 0.2, h * 0.16, C.coral, 0)
	box(out, w - 0.2, h, 0.2, x, y + 0.8 + h / 2, z + 0.9, C.tile, TRIM) -- светлая задняя стенка: рыбы читаются
end

-- Аквариум-колонна: латунное основание и крышка, вода, пузыри, рыбка.
local function tubeTank(out, x: number, y: number, z: number, r: number, h: number)
	cyl(out, r + 0.3, 0.9, x, y, z, C.brass)
	cyl(out, r, h, x, y + 0.9, z, C.water, WATER)
	cyl(out, r + 0.3, 0.6, x, y + 0.9 + h, z, C.brass)
	for k = 0, 3 do
		local a = math.rad(k * 100)
		ball(
			out,
			0.22 + (k % 2) * 0.12,
			x + math.cos(a) * r * 0.4,
			y + 2 + h * k / 4.4,
			z + math.sin(a) * r * 0.4,
			C.white,
			TRIM
		)
	end
	fish(out, x, y + 0.9 + h * 0.62, z, 0.8, 1, FISH[3])
end

-- Якорь, прислонённый к задней стене.
local function anchor(out, x: number, y: number)
	local z = BACK - 0.7
	local lean = CFrame.Angles(0, 0, math.rad(-8))
	tilt(out, 0.5, 6.4, 0.5, CFrame.new(x, y + 3.4, z) * lean, C.iron, PROP)
	tilt(out, 3.0, 0.45, 0.34, CFrame.new(x + 0.75, y + 5.9, z) * lean, C.iron, TRIM)
	tilt(out, 2.4, 0.5, 0.4, CFrame.new(x - 1.4, y + 0.9, z) * CFrame.Angles(0, 0, math.rad(-38)), C.iron, TRIM)
	tilt(out, 2.4, 0.5, 0.42, CFrame.new(x + 0.6, y + 0.6, z) * CFrame.Angles(0, 0, math.rad(24)), C.iron, TRIM)
	cylZ(out, 0.6, 0.3, x + 0.95, y + 7.0, z, C.brass, TRIM)
end

-- Островок жильца у стекла: песок в два слоя, камни и раковины по краям (спереди — только низкие).
-- Возвращает точку жильца, половину ширины островка и его задний край.
local function island(out, tier: number, f: number): (Vector3, number, number)
	local s = Ocean.Scale[tier]
	local sx, sz = s * SIZE.X + 3.4, s * SIZE.Z + 3.4
	local z0 = -(HZ - 1.8)
	local zc = z0 + sz / 2
	local ph = 0.7 + 0.1 * tier
	box(out, sx, ph, sz, 0, f + ph / 2, zc, C.sand2, PROP)
	box(out, sx - 1.0, 0.25, sz - 1.0, 0, f + ph + 0.125, zc, C.sand1, PROP)
	local bx, bz = sx / 2 - 0.3, zc + sz / 2 - 0.3
	ball(out, 1.0 + tier * 0.12, -bx, f + ph + 0.2, bz, C.rock, TRIM)
	ball(out, 0.7 + tier * 0.1, bx - 0.4, f + ph, bz + 0.1, C.rock, TRIM)
	coralFan(out, bx - 0.3, f + ph, bz - 1.2, 0.7 + tier * 0.12, C.coral2, 0)
	cyl(out, 0.55, 0.2, -bx + 0.6, f + ph, zc - sz / 2 + 0.7, C.coral, TRIM) -- морская звезда
	ball(out, 0.35, bx - 0.6, f + ph + 0.1, zc - sz / 2 + 0.6, C.pearl, TRIM) -- раковина
	return Vector3.new(0, f + ph + 0.25, zc), sx / 2, zc + sz / 2
end

-- Место жильца у стекла: точка (низ существа), размеры подиума sx × sz и его высота. f — верх пола.
function Ocean.Spot(tier: number, f: number): (Vector3, number, number, number)
	local s = Ocean.Scale[tier]
	local sx, sz = s * SIZE.X + 3.4, s * SIZE.Z + 3.4
	local ph = 0.7 + 0.1 * tier
	return Vector3.new(0, f + ph + 0.25, -(HZ - 1.8) + sz / 2), sx, sz, ph
end

-- Точка жильца — низ существа на островке.
function Ocean.Build(out, tier: number, y0: number, y1: number): Vector3
	local o = if tier == 6 then 1.0 else 0
	local f = y0 + 0.36 -- верх пола
	local top = y1 - 0.4 -- низ потолка
	shell(out, y0, y1, o)
	local at, rx, rz = island(out, tier, f)
	local headY = at.Y + Ocean.Scale[tier] * SIZE.Y
	local rim = if tier >= 4 then C.gold else C.brass

	-- настенный аквариум слева, сундук и кораллы справа, спасательный круг, лампы-иллюминаторы
	wallTank(out, -7.5, f, 13, 6.6, if tier == 1 then 3 else 4)
	chest(out, 11.2, f, BACK - 2.2)
	coralBush(out, 7.4, f, BACK - 1.9, 0.9, 1)
	if tier < 5 then
		coralBush(out, -14.2, f, -12.0, 0.8 + tier * 0.06, 2)
	end
	if tier < 6 then
		coralBush(out, 14.2, f, -11.9, 0.75 + tier * 0.05, 3)
	end
	for _, x in { 0.8, 13.6 } do
		cylZ(out, 1.0, 0.3, x, f + 9.6, BACK - 0.15, rim)
		cylZ(out, 0.72, 0.4, x, f + 9.6, BACK - 0.2, C.lamp, Kit.LAMP)
	end

	local g1, g2 -- высоты галерей
	if tier <= 2 then
		lifeRing(out, 7.2, f + 9.4, 1.9)
		box(out, 5.0, 0.4, 1.6, -11.5, f + 1.5, rz + 5.0, C.white, PROP) -- скамья
		for _, s in { -1, 1 } do
			box(out, 0.4, 1.3, 1.4, -11.5 + s * 2.0, f + 0.65, rz + 5.0, C.deck, TRIM)
		end
		jelly(out, 7.5, top - 4.6, rz + 5, 2.0, top, C.jelly)
	end
	if tier >= 2 then -- аквариум-колонна с пузырями, якорь у стены, фонари
		tubeTank(out, if tier == 2 then 3.2 else 3.6, f, BACK - 2.8, 1.9, 8.5)
		anchor(out, 14.2, f)
		local drop = math.min(5 + tier, top - headY - 3.2)
		Kit.lantern(out, PAL, -(rx + 2.6), top, at.Z, drop)
		Kit.lantern(out, PAL, rx + 2.6, top, at.Z, drop)
	end
	if tier >= 3 then -- галерея-мостик и лестница: диорама в два уровня
		local zF = math.max(rz + 3.4, BACK - 7.5)
		g1 = f + ({ 0, 0, 15.5, 17.5, 19.5, 24 })[tier]
		Kit.gallery(out, PAL, f, g1, zF, HX - 3.6 + o, true)
		Kit.stairs(out, PAL, f, g1, -1.5, 11.5, zF - 1.7)
		for i, x in { -10, -4, 2 } do
			porthole(out, x, g1 + 5.2, 2.0, rim, FISH[i])
		end
		lifeRing(out, 9.6, g1 + 5.4, 2.0)
		coralBush(out, -12.6, g1, BACK - 2.4, 1.0, 5)
		chest(out, 9.4, g1, BACK - 2.4)
		if tier == 3 then
			jelly(out, 0, top - 5.0, rz + 3.2, 2.3, top, C.jelly)
		end
	end
	if tier >= 4 then -- атриум в два света: крылья галереи, большая медуза-люстра, большой иллюминатор
		local zF = math.max(rz + 3.4, BACK - 7.5)
		for _, s in { -1, 1 } do
			Kit.wing(out, PAL, g1, s, HX - 5.6 + o, HX - 1.6 + o, at.Z - 2, zF)
		end
		if tier == 4 then
			local cy = math.max(headY + 5.5, top - 8)
			jelly(out, 0, cy, rz + 3.6, 3.6, top, C.jelly)
			jelly(out, -5.4, cy + 1.5, rz + 5.2, 1.5, top, C.lamp)
			jelly(out, 5.4, cy + 2.2, rz + 5.2, 1.5, top, C.lamp)
			porthole(out, 2.5, g1 + 12.5, 3.4, rim, FISH[1])
		end
	end
	if tier >= 5 then -- второй ярус, лампы-медузы на цепях, гигантская ламинария в переднем углу
		g2 = f + (if tier == 5 then 31.5 else 41)
		local zF2 = BACK - 6.5
		Kit.gallery(out, PAL, f, g2, zF2, HX - 3.6 + o, false)
		tubeTank(out, -9.5, g2, BACK - 2.8, 1.7, 6.0)
		porthole(out, -3.5, g2 + 5.0, 2.0, rim, FISH[4])
		for _, s in { -1, 1 } do
			local jx, jy, jz = s * (HX - 6.5 + o), math.max(headY + 7, g1 + 9), rz - 1.5
			jelly(out, jx, jy, jz, 2.6, top, if s < 0 then C.jelly else C.lamp)
		end
		local kx, kz = -(HX - 3.0 + o), -(HZ - 5.4 + o)
		local kh = (g1 - f) * 0.92
		cyl(out, 1.5, 0.8, kx, f, kz, C.rock)
		limb(out, 0.6, {
			Vector3.new(kx, f + 0.8, kz),
			Vector3.new(kx + 0.7, f + kh * 0.3, kz + 0.5),
			Vector3.new(kx - 0.5, f + kh * 0.62, kz + 1.0),
			Vector3.new(kx + 0.4, f + kh, kz + 0.4),
		}, C.kelp, TRIM)
		limb(out, 0.45, {
			Vector3.new(kx + 0.6, f + 0.8, kz + 0.8),
			Vector3.new(kx - 0.4, f + kh * 0.28, kz + 1.9),
			Vector3.new(kx + 0.6, f + kh * 0.55, kz + 2.4),
		}, C.kelp2, TRIM)
		if tier == 5 then
			jelly(out, 0, math.max(headY + 6, g2 - 3), rz + 3.2, 3.4, top, C.jelly)
		end
	end
	if tier == 6 then -- героический объект: золотая раковина с жемчужиной, аквариум-колонна, большой иллюминатор
		local gz = BACK - 3.3
		local py = g2 + 6.6
		box(out, 11.6, 1.0, 5.6, 0, g2 + 0.5, gz, C.wall2, PROP)
		cylX(out, 3.1, 11.0, 0, g2 + 2.6, gz, C.gold) -- нижняя створка
		box(out, 11.4, 0.5, 5.9, 0, g2 + 3.85, gz, C.gold2, TRIM)
		ball(out, 3.6, 0, py + 0.9, gz - 0.2, C.pearl, Kit.LAMP) -- жемчужина
		local lid = CFrame.new(0, py + 6.4, gz + 2.5) * CFrame.Angles(math.rad(-66), 0, 0)
		tilt(out, 12.0, 0.7, 10.4, lid, C.gold, PROP) -- верхняя створка
		for k = -2, 2 do -- рёбра створки веером
			local rib = lid * CFrame.new(k * 2.3, -0.5, 0.6) * CFrame.Angles(0, math.rad(-k * 7), 0)
			tilt(out, 0.9, 0.4, 9.4, rib, C.gold2, TRIM)
		end
		tubeTank(out, 11.2, g2, BACK - 2.8, 1.6, 9.0)
		porthole(out, 8.6, g1 + 11.6, 3.4, rim, FISH[1])
		Kit.light(out, Vector3.new(0, py + 8, BACK - 13), 32, 1.7, C.warm, 70, Vector3.new(0, -0.3, 1))
	end

	Kit.lights(out, tier, y0, y1, at, headY, C.warm)
	return at
end

-- Шар-аквариум на конце ветви: вода, золотой ободок, рыбка.
local function bowl(out, x: number, y: number, z: number, r: number, s: number)
	ball(out, r, x, y, z, C.water, BOWL)
	cyl(out, r * 0.62, 0.5, x, y + r * 0.82, z, C.gold, TRIM)
	box(out, 1.3, 0.75, 0.35, x, y - 0.2, z, FISH[1], TRIM)
	box(out, 0.45, 0.7, 0.2, x - s * 0.85, y - 0.2, z, C.white, TRIM)
end

-- Наружные выросты темы: 5 — коралл оплетает переднюю левую колонну; 6 — изогнутые ветви с шарами-аквариумами.
function Ocean.Grow(out, tier: number, h: number, _frame, _crystal)
	if tier == 5 then
		-- коралл ступенями вверх по наружным граням колонны, с вилками-веточками
		local cx, cz = -(HX - W / 2), -(HZ - W / 2)
		local r, reach = 0.9, W / 2 + 0.85
		local front = Vector3.new(cx + 0.9, 0, cz - reach)
		local corner = Vector3.new(cx - reach + 0.25, 0, cz - reach + 0.25)
		local side = Vector3.new(cx - reach, 0, cz + 0.9)
		local up = function(p: Vector3, y: number): Vector3
			return Vector3.new(p.X, y, p.Z)
		end
		local points = {}
		local y, run, jog = 3.2, 5.4, 1.6
		local onFront = true
		while y + run < h - 3.5 do
			local a = if onFront then front else side
			table.insert(points, up(a, y))
			table.insert(points, up(a, y + run))
			table.insert(points, up(corner, y + run + jog))
			y += run + jog * 2
			onFront = not onFront
		end
		limb(out, r, points, C.coral2, TRIM)
		for i = 1, #points - 1 do -- вилки-веточки на стволах
			local a, b = points[i], points[i + 1]
			if math.abs(a.X - b.X) < 0.01 and b.Y - a.Y > 3 then
				local isFront = math.abs(a.Z - front.Z) < 0.01
				local p = a:Lerp(b, 0.55)
				if isFront then
					coralFan(out, p.X, p.Y, p.Z - r * 0.6, 0.9, C.coral, 0)
				else
					coralFan(out, p.X - r * 0.6, p.Y, p.Z, 0.9, C.coral, 90)
				end
			end
		end
		-- веер у правой колонны
		coralFan(out, HX - W / 2 + 0.4, 3.2, -(HZ - W / 2) - reach, 2.2, C.coral2, 0)
	elseif tier == 6 then
		local face = HX + 1.0
		local z = -(HZ + 1.0) + 2.6
		for i, s in { -1, 1 } do
			local ay = h * (if i == 1 then 0.36 else 0.5)
			local pts = {
				Vector3.new(s * (face - 0.6), ay, z),
				Vector3.new(s * (face + 1.4), ay + 0.3, z),
				Vector3.new(s * (face + 2.3), ay + 2.8, z),
				Vector3.new(s * (face + 2.2), ay + 9.0, z),
			}
			limb(out, 1.25, pts, C.coral2, PROP)
			local bx, by = s * (face + 2.2), ay + 13.2
			for _, a in { -1, 1 } do -- вилка держит шар-аквариум
				local from = Vector3.new(bx, ay + 9.0, z)
				rod(out, 0.6, from, Vector3.new(bx + a * 2.5, by - 1.2, z), C.coral2, TRIM)
			end
			cyl(out, 1.5, 0.6, bx, by - 3.2, z, C.gold, TRIM)
			bowl(out, bx, by, z, 2.8, s)
			-- малая ветвь-веер
			coralFan(out, s * (face + 0.9), ay - h * 0.14, z + 0.4, 1.7, C.coral, 0)
		end
	end
end

-- Дальняя версия: подиум жильца и выросты редкости (сам жилец — настоящая модель).
function Ocean.Far(out, tier: number, f: number, h: number, _frame)
	local FAR = { variant = "LegoSquaresFar", collide = false }
	local at, sx, sz, ph = Ocean.Spot(tier, f)
	box(out, sx, ph, sz, 0, f + ph / 2, at.Z, C.sand2, FAR)
	box(out, sx - 0.8, 0.25, sz - 0.8, 0, f + ph + 0.25 / 2, at.Z, C.sand1, FAR)
	if tier == 5 then
		local cx, cz = -(HX - W / 2), -(HZ - W / 2)
		box(out, 1.2, h * 0.7, 0.7, cx + 0.6, h * 0.45, cz - W / 2 - 0.4, C.coral2, FAR)
		box(out, 0.7, h * 0.5, 1.2, cx - W / 2 - 0.4, h * 0.6, cz + 0.6, C.coral2, FAR)
	elseif tier == 6 then
		for i, sgn in { -1, 1 } do
			local ay = h * (if i == 1 then 0.36 else 0.5)
			local face = HX + 1.0
			local z = -(HZ + 1.0) + 2.6
			box(out, 3.4, 2.0, 2.0, sgn * (face + 1.4), ay + 0.5, z, C.coral2, FAR)
			box(out, 2.2, 8.0, 1.7, sgn * (face + 2.3), ay + 5.2, z, C.coral2, FAR)
			box(out, 4.6, 4.8, 4.6, sgn * (face + 2.2), ay + 13.0, z, C.water, FAR)
		end
	end
end

return Ocean

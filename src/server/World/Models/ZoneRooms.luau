-- Комната этажа по зоне босса существа (D74, генератор этажей): набор на зону — цвета оболочки и четыре предмета
-- (small — мелкий в трёх видах, big — крупный, decor — настенный, lamp — светильник); раскладку и рост с редкостью делает общий код — так же, как
-- в утверждённых витринах: 1 база; 2 + крупный предмет и фонари; 3 + галерея с лестницей; 4 + атриум и показной
-- предмет рядом с жильцом; 5 + второй ярус и знамёна в цветах монстра; 6 + героический объект. Подиум жильца, знамёна
-- и показные предметы — в палитре и с собственными частями существа (заявки MonsterParts): комната — его дом.
-- Сейчас наборы: 3 Подземка, 4 Пустыня, 5 Ледник (существа этих зон есть в игре); остальным зонам — набор по
-- умолчанию (нейтральный зал), пока не появятся их существа. Только кирпичи и заявки. Зависит от ShowcaseKit.

local ServerScriptService = game:GetService("ServerScriptService")

local Kit = require(ServerScriptService.Server.World.Models.ShowcaseKit)

local HX, HZ, BACK = Kit.HX, Kit.HZ, Kit.BACK
local box, cyl, cylZ, ball, tilt, lamp = Kit.box, Kit.cyl, Kit.cylZ, Kit.ball, Kit.tilt, Kit.lamp
local hex = Kit.hex
local PROP, TRIM = Kit.PROP, Kit.TRIM

local ZoneRooms = {}

type Zone = { [string]: any }

local LAMP = hex("FFE3A0")
local IRON = hex("3A3F48")

-- ── Пустыня (зона 4) ───────────────────────────────────────────────────────────────────────────────────────────
local desert: Zone = {
	floor1 = hex("E6CFA0"),
	floor2 = hex("D9BE8A"),
	wall = hex("D29A5E"),
	dado = hex("B67A44"),
	belt = hex("F0D9A8"),
	ceiling = hex("F3E6C8"),
	beam = hex("8A5A2B"),
	beam2 = hex("6B4524"),
	deck = hex("B67A44"),
	trim = hex("6B4524"),
	warm = hex("FFD9A0"),
	glow = hex("E0AC66"),
}
function desert.small(out, x: number, y: number, z: number, s: number, k: number)
	if k == 1 then -- кактус в горшке
		cyl(out, 1.1 * s, 1.2 * s, x, y, z, hex("B5653A"))
		box(out, 1.1 * s, 3.0 * s, 1.1 * s, x, y + 2.7 * s, z, hex("3FA14B"), PROP)
		box(out, 1.6 * s, 0.8 * s, 0.8 * s, x + 1.0 * s, y + 2.6 * s, z, hex("2E8A3E"), TRIM)
		box(out, 0.8 * s, 1.5 * s, 0.6 * s, x + 1.5 * s, y + 3.4 * s, z, hex("2E8A3E"), TRIM)
	elseif k == 2 then -- бочка
		cyl(out, 1.4 * s, 3.0 * s, x, y, z, hex("9A6A3E"))
		cyl(out, 1.48 * s, 0.3 * s, x, y + 0.6 * s, z, IRON, TRIM)
		cyl(out, 1.48 * s, 0.3 * s, x, y + 2.1 * s, z, IRON, TRIM)
	else -- кувшины
		cyl(out, 1.0 * s, 1.6 * s, x, y, z, hex("C9793F"))
		cyl(out, 0.6 * s, 0.7 * s, x, y + 1.6 * s, z, hex("B5653A"), TRIM)
		cyl(out, 0.7 * s, 1.1 * s, x + 1.7 * s, y, z + 0.4 * s, hex("E0A35E"))
	end
end
function desert.big(out, x: number, y: number, z: number, s: number) -- пальма
	for i = 0, 3 do
		cyl(
			out,
			(0.75 - i * 0.07) * s,
			2.3 * s,
			x + i * 0.18 * s,
			y + i * 2.3 * s,
			z,
			if i % 2 == 0 then hex("8A5A2B") else hex("9C6A35")
		)
	end
	local top = Vector3.new(x + 0.6 * s, y + 9.3 * s, z)
	for i = 0, 4 do
		local a = math.rad(i * 72 + 20)
		local cf = CFrame.new(top)
			* CFrame.Angles(0, a, 0)
			* CFrame.Angles(0, 0, math.rad(-24))
			* CFrame.new(2.2 * s, 0, 0)
		tilt(
			out,
			4.4 * s,
			0.35 * s,
			(1.3 - i * 0.04) * s,
			cf,
			if i % 2 == 0 then hex("3FA14B") else hex("2E8A3E"),
			TRIM
		)
	end
	ball(out, 0.6 * s, top.X, top.Y - 0.2 * s, top.Z, hex("7A4A22"), TRIM)
end
function desert.decor(out, x: number, y: number, s: number, k: number)
	if k % 2 == 1 then -- тканый ковёр
		box(out, 5.0 * s, 3.6 * s, 0.3, x, y, BACK - 0.15, hex("B5372B"), PROP)
		box(out, 5.2 * s, 0.6 * s, 0.4, x, y + 0.9 * s, BACK - 0.2, hex("F2E6D0"), TRIM)
		box(out, 5.2 * s, 0.6 * s, 0.4, x, y - 0.9 * s, BACK - 0.2, hex("E9B43A"), TRIM)
	else -- солнце
		cylZ(out, 1.7 * s, 0.4, x, y, BACK - 0.2, hex("F2C230"))
		for i = 0, 7 do
			local a = math.rad(i * 45)
			local cf = CFrame.new(x + math.cos(a) * 2.7 * s, y + math.sin(a) * 2.7 * s, BACK - 0.15)
				* CFrame.Angles(0, 0, a)
			tilt(out, 1.2 * s, 0.45 * s, 0.25, cf, hex("E9972B"), TRIM)
		end
	end
end
function desert.lamp(out, x: number, y: number, z: number, r: number, ceilingY: number)
	cyl(out, r, 0.35, x, y, z, hex("6B4524"))
	box(out, 0.2, ceilingY - y - 0.35, 0.2, x, (y + 0.35 + ceilingY) / 2, z, IRON, TRIM)
	for k = 0, 3 do
		local a = math.rad(45 + k * 90)
		lamp(out, 0.8, 1.0, 0.8, x + math.cos(a) * (r - 0.5), y - 0.5, z + math.sin(a) * (r - 0.5), LAMP)
	end
end

-- ── Ледник (зона 5) ────────────────────────────────────────────────────────────────────────────────────────────
local glacier: Zone = {
	floor1 = hex("EAF4FB"),
	floor2 = hex("D5E7F4"),
	wall = hex("86BCDD"),
	dado = hex("5E97BF"),
	belt = hex("F4FAFF"),
	ceiling = hex("EEF7FD"),
	beam = hex("5E97BF"),
	beam2 = hex("FFFFFF"),
	deck = hex("6FA6CC"),
	trim = hex("F4FAFF"),
	warm = hex("FFE9C4"),
	glow = hex("9FD0EE"),
}
local ICE = { material = Enum.Material.Glass, transparency = 0.35, collide = false }
function glacier.small(out, x: number, y: number, z: number, s: number, k: number)
	if k == 1 then -- ледяные глыбы
		box(out, 2.6 * s, 1.6 * s, 2.2 * s, x, y + 0.8 * s, z, hex("BFE3F7"), PROP)
		box(out, 1.6 * s, 1.3 * s, 1.5 * s, x + 0.3 * s, y + 2.25 * s, z - 0.1 * s, hex("DDF1FB"), PROP)
		box(out, 1.2 * s, 1.0 * s, 1.2 * s, x - 2.1 * s, y + 0.5 * s, z - 0.6 * s, hex("A8D8F2"), ICE)
	elseif k == 2 then -- ящик под снегом
		box(out, 2.4 * s, 2.0 * s, 2.2 * s, x, y + 1.0 * s, z, hex("9A6A3E"), PROP)
		box(out, 2.6 * s, 0.5 * s, 2.4 * s, x, y + 2.25 * s, z, hex("FFFFFF"), TRIM)
		box(out, 2.1 * s, 0.3 * s, 0.25 * s, x, y + 1.0 * s, z - 1.12 * s, hex("6B4524"), TRIM)
	else -- сосульки-кристаллы
		Kit.crystal(out, Vector3.new(x, y, z), Vector3.new(0.1, 1, 0), 3.4 * s, 0.5 * s, hex("A8D8F2"))
		Kit.crystal(
			out,
			Vector3.new(x + 1.0 * s, y, z - 0.3 * s),
			Vector3.new(0.4, 1, -0.1),
			2.2 * s,
			0.4 * s,
			hex("CFEAF8")
		)
		Kit.crystal(
			out,
			Vector3.new(x - 0.9 * s, y, z - 0.4 * s),
			Vector3.new(-0.35, 1, -0.2),
			1.9 * s,
			0.36 * s,
			hex("A8D8F2")
		)
	end
end
function glacier.big(out, x: number, y: number, z: number, s: number) -- ледяная арка-иглу
	local c1, c2 = hex("E3F2FB"), hex("C5E2F4")
	for _, sgn in { -1, 1 } do
		box(out, 1.8 * s, 2.4 * s, 2.6 * s, x + sgn * 2.6 * s, y + 1.2 * s, z, c1, PROP)
		box(out, 1.7 * s, 2.0 * s, 2.5 * s, x + sgn * 2.3 * s, y + 3.4 * s, z, c2, PROP)
		box(out, 1.6 * s, 1.5 * s, 2.4 * s, x + sgn * 1.5 * s, y + 5.1 * s, z, c1, PROP)
	end
	box(out, 2.2 * s, 1.3 * s, 2.3 * s, x, y + 6.1 * s, z, c2, PROP)
	box(out, 3.4 * s, 4.2 * s, 0.4 * s, x, y + 2.1 * s, z + 1.0 * s, hex("3E6F96"), TRIM) -- тёмный проём
end
function glacier.decor(out, x: number, y: number, s: number, k: number)
	if k % 2 == 1 then -- снежинка
		for i = 0, 2 do
			tilt(
				out,
				4.4 * s,
				0.5 * s,
				0.25 + i * 0.04,
				CFrame.new(x, y, BACK - 0.15) * CFrame.Angles(0, 0, math.rad(i * 60)),
				hex("FFFFFF"),
				TRIM
			)
		end
		cylZ(out, 0.8 * s, 0.5, x, y, BACK - 0.25, hex("BFE3F7"), TRIM)
	else -- ряд сосулек
		box(out, 6.0 * s, 0.6 * s, 0.6, x, y + 1.6 * s, BACK - 0.3, hex("FFFFFF"), TRIM)
		for i = 0, 3 do
			local len = (2.2 - (i % 2) * 0.8) * s
			Kit.crystal(
				out,
				Vector3.new(x - 2.2 * s + i * 1.5 * s, y + 1.3 * s, BACK - 0.5),
				Vector3.new(0, -1, 0),
				len,
				0.3 * s,
				hex("CFEAF8")
			)
		end
	end
end
function glacier.lamp(out, x: number, y: number, z: number, r: number, ceilingY: number)
	box(out, 0.2, ceilingY - y - r * 0.4, 0.2, x, (y + r * 0.4 + ceilingY) / 2, z, IRON, TRIM)
	ball(out, r * 0.55, x, y, z, hex("FFF3D6"), Kit.LAMP)
	for k = 0, 3 do
		local a = math.rad(k * 90)
		Kit.crystal(
			out,
			Vector3.new(x + math.cos(a) * r * 0.4, y, z + math.sin(a) * r * 0.4),
			Vector3.new(math.cos(a), -0.5, math.sin(a)),
			r * 0.9,
			r * 0.14,
			hex("CFEAF8")
		)
	end
end

-- ── Подземка (зона 3) ──────────────────────────────────────────────────────────────────────────────────────────
local subway: Zone = {
	floor1 = hex("9AA0A8"),
	floor2 = hex("8A9098"),
	wall = hex("F1EFE6"),
	dado = hex("2F7D5B"),
	belt = hex("2F7D5B"),
	ceiling = hex("D5D8DD"),
	beam = hex("6D737C"),
	beam2 = hex("4A4F57"),
	deck = hex("6D737C"),
	trim = hex("F2C230"),
	warm = hex("FFE7B8"),
	glow = hex("E6DFC4"),
}
function subway.small(out, x: number, y: number, z: number, s: number, k: number)
	if k == 1 then -- скамья
		box(out, 4.6 * s, 0.4 * s, 1.5 * s, x, y + 1.5 * s, z, hex("8A5A2B"), PROP)
		box(out, 4.6 * s, 1.6 * s, 0.35 * s, x, y + 2.5 * s, z + 0.6 * s, hex("8A5A2B"), TRIM)
		for _, sgn in { -1, 1 } do
			box(out, 0.4 * s, 1.3 * s, 1.3 * s, x + sgn * 1.9 * s, y + 0.65 * s, z, IRON, TRIM)
		end
	elseif k == 2 then -- урна
		cyl(out, 0.9 * s, 2.2 * s, x, y, z, hex("4A4F57"))
		cyl(out, 1.0 * s, 0.3 * s, x, y + 2.2 * s, z, hex("F2C230"), TRIM)
	else -- чемоданы
		box(out, 2.4 * s, 1.6 * s, 1.2 * s, x, y + 0.8 * s, z, hex("B5372B"), PROP)
		box(out, 2.0 * s, 1.2 * s, 1.0 * s, x + 0.2 * s, y + 2.2 * s, z, hex("3E6FB0"), PROP)
		box(out, 0.8 * s, 0.25 * s, 0.25 * s, x + 0.2 * s, y + 2.95 * s, z, IRON, TRIM)
	end
end
function subway.big(out, x: number, y: number, z: number, s: number) -- турникеты
	for i = -1, 1 do
		box(out, 0.9 * s, 3.2 * s, 2.6 * s, x + i * 2.6 * s, y + 1.6 * s, z, hex("AEB4BD"), PROP)
		box(out, 1.15 * s, 0.5 * s, 2.8 * s, x + i * 2.6 * s, y + 3.3 * s, z, hex("F2C230"), TRIM)
	end
	for _, sgn in { -1, 1 } do
		box(out, 1.7 * s, 0.25 * s, 0.25 * s, x + sgn * 1.3 * s, y + 2.2 * s, z - 0.6 * s, hex("D8483B"), TRIM)
	end
end
function subway.decor(out, x: number, y: number, s: number, k: number)
	if k % 2 == 1 then -- часы
		cylZ(out, 1.7 * s, 0.4, x, y, BACK - 0.2, IRON)
		cylZ(out, 1.4 * s, 0.5, x, y, BACK - 0.25, hex("FFFFFF"), TRIM)
		tilt(out, 0.22 * s, 1.1 * s, 0.56, CFrame.new(x, y + 0.45 * s, BACK - 0.28), IRON, TRIM)
		tilt(out, 0.8 * s, 0.4 * s, 0.58, CFrame.new(x + 0.35 * s, y + 0.05 * s, BACK - 0.29), IRON, TRIM)
	else -- плиточная арка
		box(out, 5.0 * s, 4.0 * s, 0.3, x, y, BACK - 0.15, hex("2F7D5B"), PROP)
		box(out, 4.2 * s, 3.2 * s, 0.4, x, y - 0.2 * s, BACK - 0.2, hex("DDE9E2"), TRIM)
	end
end
function subway.lamp(out, x: number, y: number, z: number, r: number, ceilingY: number)
	for _, sgn in { -1, 1 } do
		box(out, 0.2, ceilingY - y, 0.2, x + sgn * r * 0.8, (y + ceilingY) / 2, z, IRON, TRIM)
	end
	box(out, r * 2.2, 0.3, 1.0, x, y - 0.15, z, hex("4A4F57"), TRIM)
	lamp(out, r * 2.0, 0.4, 0.7, x, y - 0.5, z, hex("FFF6DC"))
end

-- ── Зал по умолчанию (зоны без набора) ─────────────────────────────────────────────────────────────────────────
local hall: Zone = table.clone(subway)
hall.wall, hall.dado, hall.belt = hex("C9CDD3"), hex("8E949D"), hex("E6E8EC")

ZoneRooms.Zones = { [3] = subway, [4] = desert, [5] = glacier } :: { [number]: Zone }

local function zoneOf(dna): Zone
	return ZoneRooms.Zones[dna.zone] or hall
end

function ZoneRooms.Glow(dna, tier: number): Color3
	return zoneOf(dna).glow:Lerp(Color3.new(1, 1, 1), (tier - 1) * 0.04)
end

function ZoneRooms.Dado(dna): Color3
	return zoneOf(dna).dado
end

-- Масштаб показа жильца: высота растёт с редкостью, ширина ограничена — рядом остаётся место показным предметам.
function ZoneRooms.Scale(dna, tier: number): number
	local tall = ({ 9.5, 11, 12.4, 13.8, 15.3, 16.7 })[tier]
	local wide = ({ 12, 13, 14.5, 16, 17.5, 19 })[tier]
	return math.min(tall / dna.size.Y, wide / dna.size.X, (wide + 2) / dna.size.Z)
end

-- Место жильца у стекла: точка (низ существа), размеры подиума sx × sz и его высота. f — верх пола.
function ZoneRooms.Spot(dna, tier: number, f: number): (Vector3, number, number, number)
	local s = ZoneRooms.Scale(dna, tier)
	local sx, sz = s * dna.size.X + 3.2, s * dna.size.Z + 3.0
	local ph = 0.7 + 0.1 * tier
	return Vector3.new(0, f + ph + 0.25, -(HZ - 1.8) + sz / 2), sx, sz, ph
end

-- Подиум жильца в палитре существа: основание, настил, акцентная кромка спереди (низкая — жильца не перекрывает).
local function podium(out, dna, tier: number, f: number): (Vector3, number, number)
	local at, sx, sz, ph = ZoneRooms.Spot(dna, tier, f)
	local body, second, accent = dna.palette[1], dna.palette[2], dna.palette[3]
	box(out, sx, ph, sz, 0, f + ph / 2, at.Z, second, PROP)
	box(out, sx - 0.8, 0.25, sz - 0.8, 0, f + ph + 0.125, at.Z, body:Lerp(Color3.new(1, 1, 1), 0.55), PROP)
	box(out, sx + 0.2, 0.3, 0.3, 0, f + ph - 0.27, at.Z - sz / 2 - 0.05, accent, TRIM)
	return at, sx / 2, at.Z + sz / 2
end

function ZoneRooms.FarPodium(out, dna, tier: number, f: number, extra: any)
	local at, sx, sz, ph = ZoneRooms.Spot(dna, tier, f)
	box(out, sx, ph, sz, 0, f + ph / 2, at.Z, dna.palette[2], extra)
	box(out, sx - 0.8, 0.25, sz - 0.8, 0, f + ph + 0.125, at.Z, dna.palette[1]:Lerp(Color3.new(1, 1, 1), 0.55), extra)
end

-- Место подвеса по Z в стороне от потолочных балок (z = −9, 0, 9): цепь не совпадает гранью с балкой.
local function clearOfBeams(z: number): number
	for _, b in { -9, 0, 9 } do
		if math.abs(z - b) < 1.1 then
			return b + 1.2
		end
	end
	return z
end

-- Оболочка комнаты: пол в две полосы, задняя стена с цоколем и поясами, потолок с балками.
local function shell(out, zone: Zone, tier: number, y0: number, y1: number)
	local lift = ({ 0, 0, 0.08, 0.16, 0.24, 0.32 })[tier] -- на высших редкостях зал светлее
	local wall, dado = zone.wall:Lerp(Color3.new(1, 1, 1), lift), zone.dado:Lerp(zone.wall, lift)
	local x1, z0 = HX - 1.4, -(HZ - 1.4)
	local n = 12
	local w = x1 * 2 / n
	for k = 0, n - 1 do
		local h = if k % 2 == 0 then 0.3 else 0.36
		box(
			out,
			w,
			h,
			BACK - z0,
			-x1 + w * (k + 0.5),
			y0 + h / 2,
			(z0 + BACK) / 2,
			if k % 2 == 0 then zone.floor1 else zone.floor2
		)
	end
	local half = HX - 3.0
	local wy1 = y1 - 0.4
	box(out, half * 2, wy1 - y0, 0.3, 0, (y0 + wy1) / 2, BACK + 0.15, wall)
	box(out, half * 2 - 1, 4.6, 0.15, 0, y0 + 2.6, BACK - 0.075, dado)
	box(out, half * 2 - 0.6, 0.6, 0.3, 0, y0 + 5.2, BACK - 0.15, zone.belt, TRIM)
	box(out, half * 2 - 1.8, 0.5, 0.25, 0, wy1 - 1.6, BACK - 0.125, zone.belt, TRIM)
	box(out, HX * 2 - 1.4, 0.36, HZ * 2 - 1.4, 0, y1 - 0.22, 0, zone.ceiling)
	for _, z in { -9, 0, 9 } do
		box(out, HX * 2 - 1.8, 0.9, 1.2, 0, y1 - 0.75, z, zone.beam, TRIM)
	end
	for _, x in { -8, 8 } do
		box(out, 1.0, 0.65, HZ * 2 - 1.8, x, y1 - 0.675, 0, zone.beam2, TRIM)
	end
end

-- Комната этажа существа dna редкости tier. requests — сюда добавляются заявки на собственные части существа.
-- Возвращает точку жильца.
function ZoneRooms.Build(
	out,
	dna,
	tier: number,
	y0: number,
	y1: number,
	requests: { any },
	featureSize: Vector3?
): Vector3
	local zone = zoneOf(dna)
	local f = y0 + 0.36
	local top = y1 - 0.4
	shell(out, zone, tier, y0, y1)
	local at, rx, rz = podium(out, dna, tier, f)
	local headY = at.Y + ZoneRooms.Scale(dna, tier) * dna.size.Y
	local pal: Kit.Palette =
		{ deck = zone.deck, trim = zone.trim, step1 = zone.floor1, step2 = zone.floor2, metal = IRON, lamp = LAMP }
	local side = rx + 3.3
	local accent, body = dna.palette[3], dna.palette[1]

	-- база: предметы у задней стены, по одному в передних углах, два настенных, светильник
	zone.small(out, -11.5, f, BACK - 2.6, 1.0, 1)
	zone.small(out, 12.4, f, BACK - 2.4, 1.0, 2)
	zone.small(out, -5.5, f, BACK - 2.2, 0.9, 3)
	if tier < 5 then
		zone.small(out, -14.3, f, -12.2, 0.7, 1)
	end
	if tier < 4 then
		zone.small(out, 14.3, f, -12.0, 0.65, 3)
	end
	if tier <= 2 then
		zone.decor(out, -8, f + 10.4, 1.0, 1)
		zone.decor(out, 8, f + 10.6, 0.9, 2)
		zone.lamp(out, -8, top - 4.0, clearOfBeams(rz + 6), 3.0, top) -- сбоку: не сливается с головой жильца
	end
	if tier >= 2 then -- крупный предмет зоны и фонари
		zone.big(out, 4.6, f, BACK - 3.0, 1.0)
		local drop = math.min(5 + tier, top - headY - 3.2)
		Kit.lantern(out, pal, -(rx + 2.6), top, clearOfBeams(at.Z), drop)
		Kit.lantern(out, pal, rx + 2.6, top, clearOfBeams(at.Z), drop)
	end
	local g1, g2
	if tier >= 3 then -- галерея и лестница
		local zF = math.max(rz + 3.4, BACK - 7.5)
		g1 = f + 11.5 + tier
		Kit.gallery(out, pal, f, g1, zF, HX - 3.6, true)
		Kit.stairs(out, pal, f, g1, -1.5, 11.5, zF - 1.7)
		zone.small(out, -11.5, g1, BACK - 2.6, 0.9, 2)
		zone.small(out, 10.5, g1, BACK - 2.5, 0.9, 1)
		zone.decor(out, -5.5, g1 + 6.2, 1.0, 1)
		zone.decor(out, 5.5, g1 + 6.4, 1.0, 2)
		if tier == 3 then
			zone.lamp(out, -8, headY + 6.6, clearOfBeams(rz + 3.2), 3.2, top)
		end
	end
	if tier >= 4 then -- атриум: крылья галереи, большой светильник; показной предмет — золотая черта существа
		local zF = math.max(rz + 3.4, BACK - 7.5)
		for _, s in { -1, 1 } do
			Kit.wing(out, pal, g1, s, HX - 5.6, HX - 1.6, at.Z + 4, zF)
		end
		if tier <= 5 then
			zone.lamp(out, 0, headY + 7.5, clearOfBeams(rz + 3.4), 4.6, top)
		end
		if featureSize and dna.feature then
			local k = (if tier == 6 then 7.5 elseif tier == 5 then 5.5 else 4.6)
				/ math.max(featureSize.X, featureSize.Y, featureSize.Z)
			local ped = if tier == 6 then 4.2 else 2.6
			box(out, 4.4, ped, 4.4, -side, f + ped / 2, at.Z + 1, zone.dado, PROP)
			box(out, 5.0, 0.4, 5.0, -side, f + ped + 0.2, at.Z + 1, Kit.GOLD, PROP)
			table.insert(requests, {
				part = dna.feature,
				at = CFrame.new(-side, f + ped + 0.4 + featureSize.Y * k / 2, at.Z + 1),
				scale = k,
				gold = true,
			})
		end
	end
	if tier >= 5 then -- второй ярус, знамёна в цветах монстра, крупный предмет зоны рядом с жильцом
		g2 = g1 + 12
		Kit.gallery(out, pal, f, g2, BACK - 6.5, HX - 3.6, false)
		zone.small(out, -10, g2, BACK - 2.6, 0.9, 3)
		for i, x in { -9.5, 0, 9.5 } do
			local len = top - g2 - 7
			box(out, 5, len, 0.2, x, top - 1.6 - len / 2, BACK - 0.1, if i == 2 then accent else body, TRIM)
			cylZ(out, 1.5, 0.3, x, top - 1.6 - len * 0.35, BACK - 0.3, if i == 2 then body else accent, TRIM)
		end
		zone.big(out, side + 0.2, f, at.Z + 1.5, if tier == 6 then 1.0 else 0.8)
	end
	if tier == 6 then -- алмазные друзы у героического объекта и свет на него
		Kit.druse(out, -side + 1.6, f, at.Z - 2.6, 1.3, Kit.DIAMOND)
		Kit.druse(out, side - 1.4, f, at.Z - 2.4, 1.1, Kit.DIAMOND)
		Kit.light(out, Vector3.new(-side, f + 19, at.Z - 5), 28, 1.7, zone.warm, 60, Vector3.new(0, -1, 0.35))
	end

	Kit.lights(out, tier, y0, y1, at, headY, zone.warm)
	return at
end

return ZoneRooms

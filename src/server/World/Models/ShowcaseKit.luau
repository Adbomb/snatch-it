-- Набор деталей для этажей-витрин (D74, вариант B): короткие функции «брусок / цилиндр / шар / стержень» поверх
-- ModelBuilder и общие материалы. Архитектура — LegoSquaresBold, предметы — кольца D39 (LegoRingsD39Boss), стекло и
-- вода — Glass; неона нет. Координаты — в осях этажа: начало — центр низа плиты, перед (стекло фасада) — −Z.
-- Зависит от ModelBuilder, GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)

type Brick = ModelBuilder.Brick

local Kit = {}

Kit.HX, Kit.HZ = GameConfig.Tower.Half.X, GameConfig.Tower.Half.Y
Kit.SLAB = 1.6 -- толщина плиты этажа
Kit.W = 3.4 -- сторона угловой колонны (у всех редкостей колонны на одних осях)
Kit.BACK = Kit.HZ - 1.0 -- внутренняя грань задней стены

Kit.ARCH = { variant = "LegoSquaresBold" } -- архитектура
Kit.DECO = { variant = "LegoSquaresBold", collide = false } -- накладки архитектуры
Kit.PROP = { variant = "LegoRingsD39Boss" } -- предметы
Kit.TRIM = { variant = "LegoRingsD39Boss", collide = false } -- мелкие детали предметов
Kit.GLASS = { material = Enum.Material.Glass, transparency = 0.8, shadow = false }
Kit.LAMP = { material = Enum.Material.SmoothPlastic, collide = false, shadow = false } -- плафон

local UPRIGHT = CFrame.Angles(0, 0, math.rad(90)) -- ось цилиндра вертикально
local ALONG_Z = CFrame.Angles(0, math.rad(90), 0) -- ось цилиндра вдоль Z

function Kit.hex(code: string): Color3
	return Color3.fromHex(code)
end

-- Металл (решение владельца 2026-11-27, исключение из «всё Plastic»): золото, латунь и бронза — встроенный материал
-- Roblox Foil, без загрузок. Цвет, заведённый через Kit.metal, красится фольгой во всех функциях набора.
local metals: { [string]: boolean } = {}
function Kit.metal(code: string): Color3
	local color = Color3.fromHex(code)
	metals[color:ToHex()] = true
	return color
end
Kit.GOLD, Kit.GOLD2 = Kit.metal("F0BC3C"), Kit.metal("C4922A")
Kit.BRASS, Kit.BRONZE = Kit.metal("D0A84E"), Kit.metal("C08444")
Kit.DIAMOND = Color3.fromHex("8FD8FF") -- кристаллы Алмазного
Kit.GEM = { material = Enum.Material.Glass, transparency = 0.28, collide = false } -- гранёный прозрачный кристалл

local function finish(color: Color3, extra: { [string]: any }): { [string]: any }
	if extra.material == nil and metals[color:ToHex()] then
		return { material = Enum.Material.Foil, collide = extra.collide, shadow = extra.shadow, name = extra.name }
	end
	return extra
end

function Kit.with(base: { [string]: any }, more: { [string]: any }): { [string]: any }
	local t = table.clone(base)
	for k, v in more do
		t[k] = v
	end
	return t
end

-- Брусок по центру (x, y, z) размером (sx, sy, sz).
function Kit.box(
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
	table.insert(
		out,
		ModelBuilder.Brick(Vector3.new(sx, sy, sz), Vector3.new(x, y, z), color, finish(color, extra or Kit.ARCH))
	)
end

-- Повёрнутый брусок: cf — положение и поворот центра.
function Kit.tilt(out: { Brick }, sx: number, sy: number, sz: number, cf: CFrame, color: Color3, extra: any?)
	table.insert(out, ModelBuilder.Brick(Vector3.new(sx, sy, sz), cf, color, finish(color, extra or Kit.TRIM)))
end

-- Вертикальный цилиндр радиуса r и высоты h с низом на y.
function Kit.cyl(out: { Brick }, r: number, h: number, x: number, y: number, z: number, color: Color3, extra: any?)
	local e = Kit.with(finish(color, extra or Kit.PROP), { shape = "Cylinder" })
	table.insert(out, ModelBuilder.Brick(Vector3.new(h, r * 2, r * 2), CFrame.new(x, y + h / 2, z) * UPRIGHT, color, e))
end

-- Цилиндр с осью вдоль Z: центр (x, y, z), длина len.
function Kit.cylZ(out: { Brick }, r: number, len: number, x: number, y: number, z: number, color: Color3, extra: any?)
	local e = Kit.with(finish(color, extra or Kit.PROP), { shape = "Cylinder" })
	table.insert(out, ModelBuilder.Brick(Vector3.new(len, r * 2, r * 2), CFrame.new(x, y, z) * ALONG_Z, color, e))
end

-- Цилиндр с осью вдоль X: центр (x, y, z), длина len.
function Kit.cylX(out: { Brick }, r: number, len: number, x: number, y: number, z: number, color: Color3, extra: any?)
	local e = Kit.with(finish(color, extra or Kit.PROP), { shape = "Cylinder" })
	table.insert(out, ModelBuilder.Brick(Vector3.new(len, r * 2, r * 2), CFrame.new(x, y, z), color, e))
end

function Kit.ball(out: { Brick }, r: number, x: number, y: number, z: number, color: Color3, extra: any?)
	local e = Kit.with(finish(color, extra or Kit.PROP), { shape = "Ball" })
	table.insert(out, ModelBuilder.Brick(Vector3.new(r * 2, r * 2, r * 2), Vector3.new(x, y, z), color, e))
end

-- Стержень-цилиндр радиуса r от точки a до точки b.
function Kit.rod(out: { Brick }, r: number, a: Vector3, b: Vector3, color: Color3, extra: any?)
	local e = Kit.with(finish(color, extra or Kit.PROP), { shape = "Cylinder" })
	local cf = CFrame.lookAt((a + b) / 2, b) * ALONG_Z
	table.insert(out, ModelBuilder.Brick(Vector3.new((b - a).Magnitude, r * 2, r * 2), cf, color, e))
end

-- Изогнутая «рука»: стержни по точкам с шарами в сгибах (органика без мешей).
function Kit.limb(out: { Brick }, r: number, points: { Vector3 }, color: Color3, extra: any?)
	for i = 1, #points - 1 do
		Kit.rod(out, r, points[i], points[i + 1], color, extra)
		if i > 1 then
			Kit.ball(out, r, points[i].X, points[i].Y, points[i].Z, color, extra)
		end
	end
end

-- Ступенчатый гранёный кристалл: тело и более узкое остриё вдоль dir (резкие ступени D39), от точки base.
function Kit.crystal(out: { Brick }, base: Vector3, dir: Vector3, len: number, r: number, color: Color3, extra: any?)
	local d = dir.Unit
	local up = if math.abs(d.Y) > 0.95 then Vector3.xAxis else Vector3.yAxis
	local cf = CFrame.lookAt(base, base + d, up) * CFrame.Angles(math.rad(-90), 0, 0) -- ось Y бруска вдоль dir
	local spin = CFrame.Angles(0, math.rad(45), 0)
	local e = extra or Kit.GEM
	Kit.tilt(out, r * 2, len * 0.72, r * 2, cf * CFrame.new(0, len * 0.36, 0) * spin, color, e)
	Kit.tilt(out, r * 1.3, len * 0.36, r * 1.3, cf * CFrame.new(0, len * 0.82, 0) * spin, color, e)
end

-- Друза из трёх кристаллов на полу у точки (x, y, z): высокий и два пониже; s — размер.
function Kit.druse(out: { Brick }, x: number, y: number, z: number, s: number, color: Color3)
	Kit.crystal(out, Vector3.new(x, y, z), Vector3.new(0.1, 1, -0.1), 3.6 * s, 0.55 * s, color)
	Kit.crystal(out, Vector3.new(x + 0.9 * s, y, z - 0.3 * s), Vector3.new(0.45, 1, -0.2), 2.4 * s, 0.42 * s, color)
	Kit.crystal(out, Vector3.new(x - 0.8 * s, y, z - 0.5 * s), Vector3.new(-0.4, 1, -0.3), 2.0 * s, 0.38 * s, color)
end

-- Плафон без источника света (свет этажа — два общих источника, бюджет телефона).
function Kit.lamp(out: { Brick }, sx: number, sy: number, sz: number, x: number, y: number, z: number, color: Color3)
	table.insert(out, ModelBuilder.Brick(Vector3.new(sx, sy, sz), Vector3.new(x, y, z), color, Kit.LAMP))
end

-- Невидимая точка с источником света (PointLight; с angle — SpotLight, светит вдоль look).
function Kit.light(
	out: { Brick },
	at: Vector3,
	range: number,
	brightness: number,
	color: Color3,
	angle: number?,
	look: Vector3?
)
	local cf = if look then CFrame.lookAt(at, at + look) else CFrame.new(at)
	table.insert(
		out,
		ModelBuilder.Brick(Vector3.new(0.4, 0.4, 0.4), cf, color, {
			transparency = 1,
			collide = false,
			shadow = false,
			name = "Light",
			light = { range = range, brightness = brightness, color = color, angle = angle },
		})
	)
end

-- Псевдослучайное число 0…1 по целому зерну (одинаковое при каждой сборке).
function Kit.rand(seed: number): number
	local x = math.sin(seed * 12.9898 + 78.233) * 43758.5453
	return x - math.floor(x)
end

-- ── Общие конструкции комнат (цвета — палитра темы: deck, trim, step1, step2, metal, lamp) ──────────────────────────

export type Palette = { deck: Color3, trim: Color3, step1: Color3, step2: Color3, metal: Color3, lamp: Color3 }

-- Галерея у задней стены на высоте g (верх настила): настил, кромка, перила, опоры от пола f.
function Kit.gallery(out: { Brick }, p: Palette, f: number, g: number, zFront: number, half: number, posts: boolean)
	Kit.box(out, half * 2, 0.6, Kit.BACK - zFront, 0, g - 0.3, (zFront + Kit.BACK) / 2, p.deck)
	Kit.box(out, half * 2 + 0.2, 0.9, 0.3, 0, g - 0.25, zFront - 0.15, p.trim, Kit.TRIM)
	Kit.box(out, half * 2, 0.3, 0.3, 0, g + 2.6, zFront + 0.15, p.trim, Kit.TRIM)
	local n = 9
	for k = 0, n - 1 do
		local x = -half + 0.4 + k * (half * 2 - 0.8) / (n - 1)
		Kit.box(out, 0.3, 2.45, 0.3, x, g + 1.225, zFront + 0.15, p.trim, Kit.TRIM)
	end
	if posts then
		for _, s in { -1, 1 } do
			Kit.box(out, 0.8, g - 0.6 - f, 0.8, s * half * 0.62, (f + g - 0.6) / 2, zFront + 0.6, p.trim, Kit.TRIM)
		end
	end
end

-- Боковое крыло галереи вдоль стекла (атриум): настил и перила с внутренней стороны.
function Kit.wing(
	out: { Brick },
	p: Palette,
	g: number,
	side: number,
	xIn: number,
	xOut: number,
	z0: number,
	z1: number
)
	Kit.box(out, xOut - xIn, 0.5, z1 - z0, side * (xIn + xOut) / 2, g - 0.3, (z0 + z1) / 2, p.deck)
	Kit.box(out, 0.3, 0.3, z1 - z0, side * (xIn + 0.15), g + 2.6, (z0 + z1) / 2, p.trim, Kit.TRIM)
	for k = 0, 4 do
		local z = z0 + 0.3 + k * (z1 - z0 - 0.6) / 4
		Kit.box(out, 0.3, 2.5, 0.3, side * (xIn + 0.15), g + 1.2, z, p.trim, Kit.TRIM)
	end
end

-- Лестница вдоль переднего края галереи: от пола f у xLow до настила g у xHigh.
function Kit.stairs(out: { Brick }, p: Palette, f: number, g: number, xLow: number, xHigh: number, z: number)
	local n = math.max(6, math.floor((g - f) / 1.7 + 0.5))
	local dir = if xHigh > xLow then 1 else -1
	local run = math.abs(xHigh - xLow) / n
	for k = 1, n do
		local y = f + (g - f) * k / n
		local color = if k % 2 == 0 then p.step1 else p.step2
		Kit.box(out, run + 0.3, 0.35, 2.8, xLow + dir * run * (k - 0.5), y - 0.175, z, color, Kit.PROP)
	end
	local a, b = Vector3.new(xLow, f + 0.2, z - 1.5), Vector3.new(xHigh, g - 0.4, z - 1.5)
	local cf = CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.rad(90), 0)
	Kit.tilt(out, (b - a).Magnitude, 0.9, 0.3, cf * CFrame.new(0, -0.5, 0), p.trim, Kit.TRIM) -- тетива
	Kit.rod(out, 0.14, a + Vector3.new(0, 2.8, 0), b + Vector3.new(0, 3.0, 0), p.trim, Kit.TRIM) -- поручень
end

-- Фонарь на цепи от потолка (плафон без своего света).
function Kit.lantern(out: { Brick }, p: Palette, x: number, ceilingY: number, z: number, drop: number)
	Kit.box(out, 0.14, drop, 0.14, x, ceilingY - drop / 2, z, p.metal, Kit.TRIM)
	Kit.box(out, 1.3, 0.25, 1.3, x, ceilingY - drop - 0.125, z, p.metal, Kit.TRIM)
	Kit.lamp(out, 0.95, 1.4, 0.95, x, ceilingY - drop - 0.95, z, p.lamp)
	Kit.box(out, 1.15, 0.22, 1.15, x, ceilingY - drop - 1.76, z, p.metal, Kit.TRIM)
end

-- Свет этажа (2 источника): общий тёплый в глубине комнаты и прожектор сверху на жильца; ярче с редкостью.
function Kit.lights(out: { Brick }, tier: number, y0: number, y1: number, at: Vector3, headY: number, warm: Color3)
	local bright = ({ 1.0, 1.05, 1.15, 1.3, 1.45, 1.6 })[tier]
	local span = y1 - y0
	local top = y1 - 0.4
	local main = Vector3.new(0, math.min(top - 3, y0 + span * 0.6), 3)
	Kit.light(out, main, math.clamp(span * 0.7 + 18, 28, 60), bright, warm)
	local keyY = math.min(top - 1.0, headY + 12)
	local key = Vector3.new(0, keyY, at.Z - 3.5)
	Kit.light(out, key, math.clamp(keyY - y0 + 8, 16, 60), bright * 1.4, warm, 75, Vector3.new(0, -1, 0.28))
end

return Kit

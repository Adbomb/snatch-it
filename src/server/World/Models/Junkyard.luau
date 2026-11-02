-- Уровень 1 «Свалка» (D41): декор из узнаваемого хлама — ржавые машины, холодильники, стиральные машины, старые
-- телевизоры, диван, шины, бочки, кран с магнитом (держит машину — ориентир издалека), будка сторожевого пса с миской и
-- косточкой, сторожка, лужи, фонари. Всё по краям: проход по центру (|x| < 10), круг босса (r 16 от (0, −5)) и
-- постаменты свободны. Координаты зоны: x — поперёк коридора (±92), z — вдоль (вход −47.5, выход +47.5), y = 0 —
-- пол. Каждая вещь — функция кирпичей в своих координатах (лицо — сторона −Z), ставится через put. Совпадающих
-- граней нет: накладки выступают за грань, стопки — с разными размерами. Зависит от ModelBuilder, Palette, Props.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)
local Props = require(ServerScriptService.Server.World.Models.Props)

type Brick = ModelBuilder.Brick

local B = ModelBuilder.Brick
local DECOR = { collide = false, shadow = false }
local UPRIGHT = CFrame.Angles(0, 0, math.rad(90)) -- ось цилиндра вертикально
local ALONG_Z = CFrame.Angles(0, math.rad(90), 0) -- ось цилиндра вдоль Z

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

local C = {
	tire = hex("2B2B33"),
	rim = hex("9AA3AE"),
	rust = hex("B5653A"),
	white = hex("EEF0F3"),
	appliance = hex("DCE3EA"),
	dark = hex("3A3F4A"),
	screen = hex("7FB8D8"),
	crane = hex("F2B632"),
	concrete = hex("A9A39A"),
	kennel = hex("C68A4E"),
	roof = hex("D84A3A"),
	bone = hex("F6F0E1"),
	bowl = hex("E53935"),
	food = hex("8A5A2B"),
	booth = hex("E3DCCB"),
	puddle = hex("2E3B4A"), -- тёмная вода с масляным отливом
	cone = hex("FF7A1A"),
}

-- Кирпичи вещи, сдвинутые и повёрнутые на at.
local function put(out: { Brick }, bricks: { Brick }, at: CFrame)
	for _, brick in bricks do
		brick.cframe = at * brick.cframe
		table.insert(out, brick)
	end
end

local Junkyard = {}

-- Старая машина вдоль X (передом в +X), колёса касаются пола.
function Junkyard.Car(color: Color3): { Brick }
	local cabin = color:Lerp(Palette.White, 0.15)
	local bricks = {
		B(Vector3.new(8, 1.6, 3.8), Vector3.new(0, 1.6, 0), color),
		B(Vector3.new(4.2, 1.5, 3.4), Vector3.new(-0.4, 3.15, 0), cabin),
		B(Vector3.new(0.2, 1.1, 3.0), Vector3.new(1.75, 3.2, 0), Palette.Glass, DECOR),
		B(Vector3.new(0.2, 1.1, 3.0), Vector3.new(-2.55, 3.2, 0), Palette.Glass, DECOR),
		B(Vector3.new(0.6, 0.5, 4.0), Vector3.new(4.1, 1.0, 0), Palette.Metal, DECOR),
		B(Vector3.new(0.6, 0.5, 4.0), Vector3.new(-4.1, 1.0, 0), Palette.Metal, DECOR),
		B(Vector3.new(1.6, 0.9, 0.1), Vector3.new(-2.2, 1.7, 1.92), C.rust, DECOR), -- ржавое пятно
		B(Vector3.new(1.1, 0.7, 0.1), Vector3.new(2.3, 1.9, -1.92), C.rust, DECOR),
	}
	for _, z in { -1.75, 1.75 } do
		table.insert(bricks, B(Vector3.new(3.6, 1.0, 0.2), Vector3.new(-0.4, 3.2, z), Palette.Glass, DECOR))
	end
	for _, z in { -1.2, 1.2 } do
		table.insert(bricks, B(Vector3.new(0.15, 0.45, 0.7), Vector3.new(4.03, 1.95, z), Palette.Lamp, DECOR))
	end
	for _, x in { -2.6, 2.6 } do
		for _, z in { -1.95, 1.95 } do
			local at = CFrame.new(x, 0.95, z) * ALONG_Z
			table.insert(bricks, B(Vector3.new(0.8, 1.9, 1.9), at, C.tire, { shape = "Cylinder" }))
			table.insert(bricks, B(Vector3.new(0.86, 0.9, 0.9), at, C.rim, { shape = "Cylinder", collide = false }))
		end
	end
	return bricks
end

function Junkyard.Fridge(): { Brick }
	return {
		B(Vector3.new(2.2, 4.6, 2.0), Vector3.new(0, 2.3, 0), C.white),
		B(Vector3.new(2.06, 0.1, 0.12), Vector3.new(0, 3.1, -1.02), C.dark, DECOR),
		B(Vector3.new(0.16, 1.2, 0.16), Vector3.new(0.75, 3.8, -1.06), Palette.Metal, DECOR),
		B(Vector3.new(0.16, 1.0, 0.16), Vector3.new(0.75, 2.3, -1.06), Palette.Metal, DECOR),
	}
end

function Junkyard.Washer(): { Brick }
	return {
		B(Vector3.new(2.4, 2.6, 2.2), Vector3.new(0, 1.3, 0), C.appliance),
		B(Vector3.new(0.12, 1.5, 1.5), CFrame.new(0, 1.15, -1.1) * ALONG_Z, C.dark, { shape = "Cylinder", collide = false }),
		B(Vector3.new(0.14, 1.1, 1.1), CFrame.new(0, 1.15, -1.1) * ALONG_Z, C.screen, { shape = "Cylinder", collide = false }),
		B(Vector3.new(2.0, 0.36, 0.12), Vector3.new(0, 2.33, -1.12), C.dark, DECOR),
	}
end

function Junkyard.TV(): { Brick }
	return {
		B(Vector3.new(2.6, 2.2, 2.2), Vector3.new(0, 1.1, 0), hex("6B4E3A")),
		B(Vector3.new(1.9, 1.5, 0.12), Vector3.new(-0.15, 1.15, -1.11), C.screen, DECOR),
		B(Vector3.new(0.3, 0.3, 0.12), Vector3.new(1.0, 0.6, -1.12), C.dark, DECOR),
		B(Vector3.new(0.12, 1.5, 0.12), CFrame.new(-0.35, 2.85, 0) * CFrame.Angles(0, 0, 0.45), Palette.Metal, DECOR),
		B(Vector3.new(0.12, 1.5, 0.12), CFrame.new(0.35, 2.85, 0) * CFrame.Angles(0, 0, -0.45), Palette.Metal, DECOR),
	}
end

-- Стопка шин (count штук), у каждой — серый диск сверху; шины чуть сдвинуты — стопка «живая».
function Junkyard.Tires(count: number): { Brick }
	local bricks = {}
	for i = 1, count do
		local shift = Vector3.new(((i * 37) % 5 - 2) * 0.12, 0, ((i * 53) % 5 - 2) * 0.12)
		local at = CFrame.new(Vector3.new(0, 0.5 + (i - 1), 0) + shift) * UPRIGHT
		table.insert(bricks, B(Vector3.new(1.0, 3.2, 3.2), at, C.tire, { shape = "Cylinder" }))
		table.insert(bricks, B(Vector3.new(1.04, 1.5, 1.5), at, C.rim, { shape = "Cylinder", collide = false }))
	end
	return bricks
end

-- Бочка с двумя полосами.
function Junkyard.Barrel(color: Color3): { Brick }
	local bricks = { B(Vector3.new(3, 2, 2), CFrame.new(0, 1.5, 0) * UPRIGHT, color, { shape = "Cylinder" }) }
	for _, y in { 0.8, 2.2 } do
		table.insert(bricks, B(Vector3.new(0.3, 2.08, 2.08), CFrame.new(0, y, 0) * UPRIGHT, C.crane, DECOR))
	end
	table.insert(bricks, B(Vector3.new(0.06, 0.5, 0.5), CFrame.new(0.45, 3.03, 0.3) * UPRIGHT, C.dark, DECOR))
	return bricks
end

-- Конус-ограждение.
function Junkyard.Cone(): { Brick }
	return {
		B(Vector3.new(1.4, 0.2, 1.4), Vector3.new(0, 0.1, 0), C.cone, DECOR),
		B(Vector3.new(0.8, 1.2, 0.8), Vector3.new(0, 0.8, 0), C.cone, DECOR),
		B(Vector3.new(0.86, 0.3, 0.86), Vector3.new(0, 0.9, 0), Palette.White, DECOR),
		B(Vector3.new(0.4, 0.5, 0.4), Vector3.new(0, 1.6, 0), C.cone, DECOR),
	}
end

-- Будка сторожевого пса: дверь на −Z, ступенчатая красная крыша, миска с кормом и косточка у входа.
function Junkyard.Kennel(): { Brick }
	local bricks = {
		B(Vector3.new(6.4, 0.4, 6.2), Vector3.new(0, 0.2, 0.4), Palette.WoodDark),
		B(Vector3.new(5, 3.6, 4.2), Vector3.new(0, 2.2, 0.9), C.kennel),
		B(Vector3.new(2.2, 2.6, 0.14), Vector3.new(0, 1.7, -1.22), C.dark, DECOR), -- лаз
		B(Vector3.new(5.8, 0.6, 5.0), Vector3.new(0, 4.3, 0.9), C.roof),
		B(Vector3.new(4.2, 0.6, 5.2), Vector3.new(0, 4.9, 0.9), C.roof:Lerp(Palette.Black, 0.1)),
		B(Vector3.new(2.4, 0.6, 5.4), Vector3.new(0, 5.5, 0.9), C.roof),
		B(Vector3.new(2.6, 0.5, 0.14), Vector3.new(0, 3.55, -1.22), Palette.White, DECOR), -- табличка-косточка
		-- миска и корм
		B(Vector3.new(0.5, 1.7, 1.7), CFrame.new(2.0, 0.65, -1.9) * UPRIGHT, C.bowl, { shape = "Cylinder", collide = false }),
		B(Vector3.new(0.52, 1.3, 1.3), CFrame.new(2.0, 0.67, -1.9) * UPRIGHT, C.food, { shape = "Cylinder", collide = false }),
		-- косточка
		B(Vector3.new(1.4, 0.3, 0.3), CFrame.new(-1.8, 0.55, -2.2) * CFrame.Angles(0, 0.5, 0), C.bone, DECOR),
	}
	for _, s in { -1, 1 } do
		for _, z in { -0.18, 0.18 } do
			local at = CFrame.new(-1.8, 0.55, -2.2) * CFrame.Angles(0, 0.5, 0) * CFrame.new(s * 0.75, 0, z)
			table.insert(bricks, B(Vector3.new(0.42, 0.42, 0.42), at, C.bone, { shape = "Ball", collide = false }))
		end
	end
	return bricks
end

-- Сторожка: домик с окном, дверью, плоской крышей с козырьком и фонарём над дверью.
function Junkyard.Booth(): { Brick }
	return {
		B(Vector3.new(7, 0.5, 7), Vector3.new(0, 0.25, 0), C.concrete),
		B(Vector3.new(6, 5.5, 6), Vector3.new(0, 3.25, 0), C.booth),
		B(Vector3.new(3.2, 1.8, 0.16), Vector3.new(-1.2, 3.8, -3.02), Palette.Glass, DECOR),
		B(Vector3.new(1.6, 3.4, 0.16), Vector3.new(1.7, 2.2, -3.02), hex("4F7CBF"), DECOR),
		B(Vector3.new(7.4, 0.6, 7.6), Vector3.new(0, 6.3, -0.2), hex("4F7CBF")),
		B(Vector3.new(0.8, 0.8, 0.5), Vector3.new(1.7, 4.6, -3.2), Palette.Lamp, {
			material = Enum.Material.Neon,
			collide = false,
			shadow = false,
			light = { range = 14, brightness = 1, color = Palette.Lamp },
		}),
	}
end

-- Башенный кран с магнитом; стрела над отметкой x = −reach (влево), на магните висит машина.
function Junkyard.Crane(reach: number): { Brick }
	local height = 24
	local bricks = {
		B(Vector3.new(7, 2, 7), Vector3.new(0, 1, 0), C.concrete),
		B(Vector3.new(2, height, 2), Vector3.new(0, 2 + height / 2, 0), C.crane, { shape = "Truss" }),
		B(Vector3.new(4.4, 3.4, 4), Vector3.new(0, 2 + height + 1.7, 0), C.crane),
		B(Vector3.new(0.16, 1.8, 3.2), Vector3.new(-2.28, 2 + height + 2, 0), Palette.Glass, DECOR),
		-- стрела (ферма) и противовес
		B(Vector3.new(2, reach + 4, 2), CFrame.new(-reach / 2 + 1, 2 + height + 4.4, 0) * CFrame.Angles(0, 0, math.rad(90)), C.crane, {
			shape = "Truss",
		}),
		B(Vector3.new(2, 8, 2), CFrame.new(7, 2 + height + 4.4, 0) * CFrame.Angles(0, 0, math.rad(90)), C.crane, { shape = "Truss" }),
		B(Vector3.new(3, 3, 3.2), Vector3.new(7.6, 2 + height + 2.6, 0), C.concrete),
		-- трос и магнит
		B(Vector3.new(0.2, 8, 0.2), Vector3.new(-reach, 2 + height - 0.6, 0), C.dark, DECOR),
		B(Vector3.new(1.2, 4.4, 4.4), CFrame.new(-reach, 2 + height - 5.2, 0) * UPRIGHT, C.dark, { shape = "Cylinder" }),
		B(Vector3.new(0.4, 3.6, 3.6), CFrame.new(-reach, 2 + height - 4.5, 0) * UPRIGHT, C.roof, {
			shape = "Cylinder",
			collide = false,
		}),
	}
	-- Машина висит под магнитом, чуть наклонена.
	local carTop = 3.9
	local hang = CFrame.new(-reach, 2 + height - 5.8 - carTop - 0.05, 0) * CFrame.Angles(0, 0.4, math.rad(6))
	put(bricks, Junkyard.Car(hex("3E7CC9")), hang)
	return bricks
end

-- Гора хлама: техника и шины в два яруса, разные вещи без общих граней.
function Junkyard.Heap(variant: number): { Brick }
	local bricks = {}
	local base = {
		{ Junkyard.Fridge, CFrame.new(-3.2, 0, 1.2) * CFrame.Angles(0, 0.3, 0) },
		{ Junkyard.Washer, CFrame.new(0.4, 0, -1.6) * CFrame.Angles(0, -0.2, 0) },
		{ Junkyard.TV, CFrame.new(3.6, 0, 1.4) * CFrame.Angles(0, 0.6, 0) },
		{ function() return Junkyard.Tires(2) end, CFrame.new(0.2, 0, 3.8) },
		{ Props.Crate, CFrame.new(-0.6, 0, 6.8) * CFrame.Angles(0, 0.25, 0) },
	}
	local top = { -- на опорах: стиральная машина на холодильнике, телевизор на стиральной, шина на ящике
		{ Junkyard.Washer, CFrame.new(-3.2, 4.6, 1.2) * CFrame.Angles(0, 1.0, 0) },
		{ Junkyard.TV, CFrame.new(0.5, 2.6, -1.5) * CFrame.Angles(0, -0.5, 0) },
		{ function() return Junkyard.Tires(1) end, CFrame.new(-0.6, 4.0, 6.8) },
	}
	local turn = if variant == 2 then CFrame.Angles(0, math.pi, 0) else CFrame.identity -- зеркально: другая гора
	for _, entry in base do
		put(bricks, entry[1](), turn * entry[2])
	end
	if variant == 2 then
		put(bricks, Junkyard.Barrel(hex("2F6BD8")), turn * CFrame.new(-6.4, 0, -1.6))
	end
	for _, entry in top do
		put(bricks, entry[1](), turn * entry[2])
	end
	return bricks
end

-- Старый диван: сиденье, спинка, подлокотники, заплатка, выпавшая пружина.
function Junkyard.Sofa(color: Color3): { Brick }
	return {
		B(Vector3.new(6, 1.4, 2.6), Vector3.new(0, 0.9, 0), color),
		B(Vector3.new(6, 2.2, 0.8), Vector3.new(0, 2.2, 1.1), color:Lerp(Palette.Black, 0.1)),
		B(Vector3.new(0.8, 1.2, 2.6), Vector3.new(-3.3, 2.2, 0.0), color:Lerp(Palette.Black, 0.15)),
		B(Vector3.new(0.8, 1.2, 2.6), Vector3.new(3.3, 2.2, 0.0), color:Lerp(Palette.Black, 0.15)),
		B(Vector3.new(4.4, 0.4, 1.8), Vector3.new(-0.2, 1.75, -0.3), color:Lerp(Palette.White, 0.12)),
		B(Vector3.new(1.2, 0.8, 0.12), Vector3.new(1.6, 2.4, 0.64), hex("E8C54A"), DECOR), -- заплатка
		B(Vector3.new(0.12, 0.9, 0.12), CFrame.new(-1.6, 2.3, -0.4) * CFrame.Angles(0.3, 0, 0.2), Palette.Metal, DECOR),
		B(Vector3.new(0.5, 0.2, 0.5), Vector3.new(-2.6, 0.1, -0.9), C.dark, DECOR),
		B(Vector3.new(0.5, 0.2, 0.5), Vector3.new(2.6, 0.1, -0.9), C.dark, DECOR),
	}
end

-- Лужа (вода — материал Glass, D36).
function Junkyard.Puddle(size: Vector2): { Brick }
	return {
		B(Vector3.new(size.X, 0.06, size.Y), Vector3.new(0, 0.03, 0), C.puddle, {
			material = Enum.Material.Glass,
			transparency = 0.45,
			collide = false,
			shadow = false,
		}),
		B(Vector3.new(size.X * 0.6, 0.08, size.Y * 0.55), Vector3.new(size.X * 0.25, 0.04, size.Y * 0.35), C.puddle, {
			material = Enum.Material.Glass,
			transparency = 0.45,
			collide = false,
			shadow = false,
		}),
	}
end

-- Весь декор свалки в координатах зоны.
function Junkyard.Zone(): { Brick }
	local out = {}
	local function at(x: number, z: number, turn: number?): CFrame
		return CFrame.new(x, 0, z) * CFrame.Angles(0, turn or 0, 0)
	end
	-- Ориентиры по краям: кран с висящей машиной справа в глубине, горы хлама.
	put(out, Junkyard.Crane(26), at(66, 22))
	put(out, Junkyard.Heap(1), at(-56, 24, 0.3))
	put(out, Junkyard.Heap(2), at(58, -20, -0.4))
	put(out, Junkyard.Heap(1), at(-68, -16, 1.4))
	-- Машины.
	put(out, Junkyard.Car(hex("D84A3A")), at(-34, -24, 0.35))
	put(out, Junkyard.Car(hex("4CAF7A")), at(34, 30, -0.6))
	-- Будка пса — рядом с его местом, лазом к нему; сторожка у входа.
	put(out, Junkyard.Kennel(), at(-25, -3, -math.pi / 2))
	put(out, Junkyard.Booth(), at(-74, -36, math.rad(30)))
	-- Шины, бочки, конусы.
	put(out, Junkyard.Tires(4), at(-22, -36))
	put(out, Junkyard.Tires(3), at(-18.6, -38.4))
	put(out, Junkyard.Tires(2), at(27, 14))
	put(out, Junkyard.Tires(5), at(78, -40))
	for i, spot in { Vector3.new(30, 0, -4), Vector3.new(32.4, 0, -1.6), Vector3.new(29.6, 0, 0.6), Vector3.new(44, 0, 38) } do
		local colors = { hex("C8442E"), hex("2F6BD8"), hex("C8442E"), hex("43A047") }
		put(out, Junkyard.Barrel(colors[i]), CFrame.new(spot))
	end
	for _, spot in { Vector2.new(-30, -18), Vector2.new(-37, -30), Vector2.new(20, -40), Vector2.new(22, -36) } do
		put(out, Junkyard.Cone(), at(spot.X, spot.Y))
	end
	-- Диван и ещё одна кучка техники по краям.
	put(out, Junkyard.Sofa(hex("C0504D")), at(46, -38, 0.5))
	put(out, Junkyard.Washer(), at(-46, 40, -0.3))
	put(out, Junkyard.TV(), at(-42.6, 41.2, 0.4))
	put(out, Junkyard.Fridge(), at(-49.6, 38, 0.9))
	-- Лужи.
	put(out, Junkyard.Puddle(Vector2.new(8, 5)), at(-40, 8, 0.4))
	put(out, Junkyard.Puddle(Vector2.new(6, 4)), at(18, -28, -0.3))
	put(out, Junkyard.Puddle(Vector2.new(9, 5)), at(50, 6, 0.9))
	-- Фонари вдоль прохода.
	for _, spot in { Vector2.new(-17, -42), Vector2.new(17, -42), Vector2.new(-22, 26), Vector2.new(22, 30) } do
		put(out, Props.Lamp(), at(spot.X, spot.Y))
	end
	return out
end

return Junkyard

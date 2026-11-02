-- Уровень 1 «Свалка» (D41): декор из узнаваемого хлама — ржавые машины, холодильники, стиральные машины, старые
-- телевизоры, диван, шины, бочки, кран с магнитом (держит машину — ориентир издалека), будка сторожевого пса с миской и
-- косточкой, сторожка, лужи, фонари; пол — земля с дорогой из бетонных плит, буграми под кучами, мусором и травой
-- (Junkyard.Ground). Всё по краям: проход по центру (|x| < 10), круг босса (r 16 от (0, −5)) и постаменты свободны. Координаты зоны: x — поперёк коридора (±92), z — вдоль (вход −47.5, выход +47.5), y = 0 —
-- пол. Каждая вещь — функция кирпичей в своих координатах (лицо — сторона −Z), ставится через put. Совпадающих
-- граней нет: накладки выступают за грань, стопки — с разными размерами. Зависит от ModelBuilder, Palette, Props.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)
local Props = require(ServerScriptService.Server.World.Models.Props)

type Brick = ModelBuilder.Brick

local B = ModelBuilder.Brick
local DECOR = { collide = false, shadow = false }
local ROUND = { shape = "Cylinder", collide = false, shadow = false }
local BALL = { shape = "Ball", collide = false, shadow = false }
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
	puddle = hex("54809A"), -- вода (круглые лужи с грязным краем)
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

-- Лужа (вода — материал Glass, D36): грязный край из двух кругов, вода из трёх (форма неровная), блик сбоку.
function Junkyard.Puddle(radius: number): { Brick }
	local mud = hex("5E4B38")
	local function water(transparency: number)
		return { shape = "Cylinder", material = Enum.Material.Glass, transparency = transparency, collide = false, shadow = false }
	end
	local bricks = {}
	for i, spot in { { 0.15, 0.1, 1.15 }, { -0.35, -0.3, 0.85 } } do
		local h = 0.03 + i * 0.03
		local d = radius * 2 * spot[3]
		table.insert(bricks, B(Vector3.new(h, d, d), CFrame.new(spot[1] * radius, h / 2, spot[2] * radius) * UPRIGHT, mud, ROUND))
	end
	for i, spot in { { 0, 0, 1 }, { 0.5, 0.3, 0.68 }, { -0.45, -0.25, 0.6 } } do
		local h = 0.1 + i * 0.03
		local d = radius * 2 * spot[3]
		local at = CFrame.new(spot[1] * radius, h / 2, spot[2] * radius) * UPRIGHT
		table.insert(bricks, B(Vector3.new(h, d, d), at, C.puddle, water(0.15)))
	end
	local glint = CFrame.new(-0.3 * radius, 0.11, 0.35 * radius) * UPRIGHT
	table.insert(bricks, B(Vector3.new(0.22, radius * 0.5, radius * 0.5), glint, Palette.White, water(0.45)))
	return bricks
end

-- Деревянный поддон: три бруска и доски поверх.
function Junkyard.Pallet(): { Brick }
	local wood = hex("B88A55")
	local bricks = {}
	for _, z in { -0.95, 0, 0.95 } do
		table.insert(bricks, B(Vector3.new(2.4, 0.36, 0.4), Vector3.new(0, 0.18, z), wood:Lerp(Palette.Black, 0.15)))
	end
	for i, x in { -0.88, -0.3, 0.3, 0.88 } do
		table.insert(bricks, B(Vector3.new(0.5, 0.16, 2.5 - (i % 2) * 0.1), Vector3.new(x, 0.44, 0), wood, DECOR))
	end
	return bricks
end

-- Пучок сорной травы: четыре травинки разной высоты, наклонены в разные стороны.
function Junkyard.Weeds(variant: number): { Brick }
	local green = Palette.Leaves[(variant - 1) % #Palette.Leaves + 1]
	local bricks = {}
	for i, blade in { { 0, 0, 1.5, 0.15 }, { 0.4, 0.2, 1.1, -0.35 }, { -0.35, 0.25, 0.9, 0.4 }, { 0.1, -0.4, 0.75, -0.2 } } do
		local at = CFrame.new(blade[1], 0, blade[2]) * CFrame.Angles(0, i * 1.3, blade[4]) * CFrame.new(0, blade[3] / 2, 0)
		local tone = if i % 2 == 0 then green:Lerp(Palette.White, 0.12) else green
		table.insert(bricks, B(Vector3.new(0.34, blade[3], 0.34), at, tone, DECOR))
	end
	return bricks
end

-- Мелкий мусор на земле: доска, лист железа, труба, банка, кирпичи, лежащая шина, колпак, гайки.
local SCRAP = {
	plank = { hex("A0784A"), hex("8A6238"), hex("B88A55") },
	sheet = { hex("8C949E"), hex("9C5A35"), hex("7D8790") },
	can = { hex("D84A3A"), hex("2F6BD8"), hex("43A047"), hex("F2B632") },
	brick = hex("B5533C"),
}

function Junkyard.Scrap(kind: number, tone: number): { Brick }
	local function pick(list: { Color3 }): Color3
		return list[(tone - 1) % #list + 1]
	end
	if kind == 1 then
		return { B(Vector3.new(2.8, 0.2, 0.55), Vector3.new(0, 0.1, 0), pick(SCRAP.plank), DECOR) }
	elseif kind == 2 then
		local wood = pick(SCRAP.plank)
		return {
			B(Vector3.new(2.6, 0.2, 0.5), Vector3.new(0, 0.1, 0), wood, DECOR),
			B(Vector3.new(2.2, 0.2, 0.5), CFrame.new(0.2, 0.3, 0.1) * CFrame.Angles(0, 0.9, 0), wood:Lerp(Palette.Black, 0.12), DECOR),
		}
	elseif kind == 3 then
		return { B(Vector3.new(2.2, 0.12, 1.5), Vector3.new(0, 0.06, 0), pick(SCRAP.sheet), DECOR) }
	elseif kind == 4 then
		return { B(Vector3.new(3.2, 0.5, 0.5), Vector3.new(0, 0.25, 0), pick(SCRAP.sheet), ROUND) }
	elseif kind == 5 then
		local tin = pick(SCRAP.can)
		return {
			B(Vector3.new(0.8, 0.45, 0.45), Vector3.new(0, 0.22, 0), tin, ROUND),
			B(Vector3.new(0.7, 0.45, 0.45), CFrame.new(0.5, 0.35, 0.6) * UPRIGHT, tin:Lerp(Palette.White, 0.1), ROUND),
		}
	elseif kind == 6 then
		return {
			B(Vector3.new(0.9, 0.45, 0.45), Vector3.new(0, 0.22, 0), SCRAP.brick, DECOR),
			B(Vector3.new(0.9, 0.45, 0.45), CFrame.new(0.3, 0.22, 0.7) * CFrame.Angles(0, 0.7, 0), SCRAP.brick:Lerp(Palette.Black, 0.1), DECOR),
			B(Vector3.new(0.9, 0.45, 0.45), CFrame.new(0.1, 0.62, 0.3) * CFrame.Angles(0, 0.3, 0), SCRAP.brick:Lerp(Palette.White, 0.08), DECOR),
		}
	elseif kind == 7 then
		return {
			B(Vector3.new(0.8, 2.8, 2.8), CFrame.new(0, 0.4, 0) * UPRIGHT, C.tire, ROUND),
			B(Vector3.new(0.84, 1.3, 1.3), CFrame.new(0, 0.4, 0) * UPRIGHT, C.rim, ROUND),
		}
	elseif kind == 8 then
		return { B(Vector3.new(0.14, 1.2, 1.2), CFrame.new(0, 0.07, 0) * UPRIGHT, C.rim, ROUND) }
	end
	return {
		B(Vector3.new(0.42, 0.42, 0.42), Vector3.new(0, 0.21, 0), C.dark, BALL),
		B(Vector3.new(0.36, 0.36, 0.36), Vector3.new(0.7, 0.18, 0.4), C.rim, BALL),
	}
end

-- Пол свалки поверх пола зоны (D41): дорога из старых бетонных плит (часть треснула, части нет), холмы земли под
-- кучами хлама (вещи стоят в грунте, а не на плитке), тёмные пятна под машинами, масляные пятна, железные листы у
-- крана, поддоны, разбросанный мелкий мусор и сорная трава. Плоские слои — с разной высотой верха (≥ 0.05), у
-- повёрнутых деталей тоже: нет совпадающих граней.
local GROUND = {
	slab = { hex("A8A29A"), hex("9C968D"), hex("B4AEA5") },
	dirt = { hex("725E48"), hex("685540") }, -- бугры, пятна под вещами
	track = hex("6A5944"),
	oil = hex("2B2620"),
}

-- Места, где мусора нет: круг босса, постаменты, крупные вещи, лужи, фонари (x, z, радиус).
local KEEP_OUT = {
	{ 0, -5, 16 },
	{ -12, -13, 4.5 },
	{ 11, -11, 4.5 },
	{ -9, 7, 4.5 },
	{ 13, 5, 4.5 },
	{ 66, 22, 5 },
	{ -56, 24, 4 },
	{ 58, -20, 4 },
	{ -68, -16, 4 },
	{ -34, -24, 4.5 },
	{ 34, 30, 4.5 },
	{ -25, -3, 5 },
	{ -74, -36, 6 },
	{ -22, -36, 2 },
	{ -18.6, -38.4, 2 },
	{ 27, 14, 2 },
	{ 78, -40, 2 },
	{ 31, -2, 3.5 },
	{ 44, 38, 1.5 },
	{ 46, -38, 4 },
	{ -46, 40, 4.5 },
	{ -40, 8, 4.5 },
	{ 18, -28, 3.5 },
	{ 50, 6, 4.5 },
	{ -17, -42, 1.2 },
	{ 17, -42, 1.2 },
	{ -22, 26, 1.2 },
	{ 22, 30, 1.2 },
	{ -64, 36, 2 },
	{ 50, -28, 2 },
	{ 72, 30, 2 },
}

-- Холмы земли (x, z, радиус, поворот): под горами хлама, под краном, под кучкой техники.
local MOUNDS = {
	{ -56, 24, 10, 0.3 },
	{ 58, -20, 10, -0.4 },
	{ -68, -16, 9, 1.4 },
	{ 66, 22, 7, 0.2 },
	{ -46, 40, 6, 0.5 },
}

-- Высота земли в точке (верх холма, примерно): мусор ложится на склон, а не прячется внутри.
local function groundHeight(p: Vector2): number
	local top = 0
	for _, m in MOUNDS do
		local d = (p - Vector2.new(m[1], m[2])).Magnitude / m[3]
		local h = if d < 0.5 then 0.35 elseif d < 0.9 then 0.2 else 0
		top = math.max(top, h)
	end
	return top
end

local function isFree(p: Vector2): boolean
	if math.abs(p.X) < 7 or math.abs(p.X) > 88 or math.abs(p.Y) > 45 then
		return false
	end
	for _, spot in KEEP_OUT do
		if (p - Vector2.new(spot[1], spot[2])).Magnitude < spot[3] then
			return false
		end
	end
	return true
end

function Junkyard.Ground(): { Brick }
	local out = {}
	local random = Random.new(41)
	-- Дорога: две колонны бетонных плит 5×7 с зазорами; каждая чуть повёрнута, часть треснула, кое-где плиты нет.
	for row = 0, 11 do
		local z = -41.8 + row * 7.6
		for col, x in { -2.7, 2.7 } do
			local n = row * 2 + col
			if n % 7 ~= 3 then
				local tone = GROUND.slab[n % 3 + 1]
				local top = 0.2 + ((row + col) % 3) * 0.06
				local turn = (if n % 2 == 0 then 1 else -1) * random:NextNumber(0.008, 0.025)
				local base = CFrame.new(x + random:NextNumber(-0.08, 0.08), 0, z) * CFrame.Angles(0, turn, 0)
				if n % 5 == 2 then
					table.insert(out, B(Vector3.new(5, top, 3.35), base * CFrame.new(0, top / 2, -1.82), tone, DECOR))
					local half = base * CFrame.new(0.1, (top - 0.08) / 2, 1.85) * CFrame.Angles(0, 0.05, 0)
					table.insert(out, B(Vector3.new(4.9, top - 0.08, 3.3), half, tone:Lerp(Palette.Black, 0.06), DECOR))
				else
					table.insert(out, B(Vector3.new(5, top, 7), base * CFrame.new(0, top / 2, 0), tone, DECOR))
				end
			end
		end
	end
	-- Пятно земли неровной формы: count кругов разного размера, сдвинутых в разные стороны; ближе к центру — выше
	-- (верх top, top + 0.06, …) — пологий бугор, а не ступенчатый «торт».
	local function blob(x: number, z: number, radius: number, turn: number, count: number, top: number, color: Color3)
		for i = 1, count do
			local angle = turn + i * 2.4
			local dist = radius * 0.55 * (1 - (i - 1) / count)
			local r = radius * (0.5 + 0.3 * ((i * 0.37) % 1))
			local h = top + (i - 1) * 0.06
			local at = CFrame.new(x + math.cos(angle) * dist, h / 2, z + math.sin(angle) * dist) * UPRIGHT
			table.insert(out, B(Vector3.new(h, r * 2, r * 2), at, color:Lerp(Palette.Black, (i % 3) * 0.04), ROUND))
		end
	end
	-- Бугры земли под горами хлама, под краном, под кучкой техники.
	for _, m in MOUNDS do
		blob(m[1], m[2], m[3], m[4], 6, 0.11, GROUND.dirt[1])
	end
	-- Тёмная земля под машинами, бочками, диваном, шинами.
	for i, spot in { { -34, -24, 5.5 }, { 34, 30, 5.5 }, { 31, -2, 4.2 }, { 46, -38, 4.6 }, { -21, -37, 4.2 }, { 78, -40, 3.2 } } do
		blob(spot[1], spot[2], spot[3], i * 0.9, 3, 0.09, GROUND.dirt[2])
	end
	-- Колеи от машин: две полосы по ломаной (отрезки внахлёст, верх через один выше — без совпадающих граней).
	local function track(points: { Vector2 })
		local k = 0
		for i = 1, #points - 1 do
			local a, b = points[i], points[i + 1]
			local along = (b - a).Unit
			local side = Vector2.new(-along.Y, along.X) * 0.95
			local steps = math.ceil((b - a).Magnitude / 3)
			for s = 0, steps - 1 do
				k += 1
				local mid = a + (b - a) * ((s + 0.5) / steps)
				local h = if k % 2 == 0 then 0.07 else 0.13
				local turn = math.atan2(-along.Y, along.X)
				for _, sign in { -1, 1 } do
					local p = mid + side * sign
					local at = CFrame.new(p.X, h / 2, p.Y) * CFrame.Angles(0, turn, 0)
					table.insert(out, B(Vector3.new((b - a).Magnitude / steps + 0.3, h, 0.7), at, GROUND.track, DECOR))
				end
			end
		end
	end
	track({ Vector2.new(-66, -29), Vector2.new(-52, -34), Vector2.new(-40, -38.5), Vector2.new(-28, -44.5), Vector2.new(-10, -46) })
	track({ Vector2.new(58, 12), Vector2.new(44, 14.5), Vector2.new(30, 18.5), Vector2.new(16, 18), Vector2.new(8, 16) })
	-- Масляные пятна: по два круга разной толщины.
	for _, spot in { { -31, -21.5, 1.7 }, { 36.5, 27.5, 1.3 }, { 33.5, 1.8, 1.1 }, { 46, -11, 1.5 }, { 24, -42, 1.2 } } do
		local r = spot[3]
		table.insert(out, B(Vector3.new(0.26, r * 2, r * 2), CFrame.new(spot[1], 0.13, spot[2]) * UPRIGHT, GROUND.oil, ROUND))
		local small = CFrame.new(spot[1] + r * 0.8, 0.15, spot[2] + r * 0.5) * UPRIGHT
		table.insert(out, B(Vector3.new(0.3, r * 1.1, r * 1.1), small, GROUND.oil:Lerp(Palette.White, 0.06), ROUND))
	end
	-- Железные листы с заклёпками у крана.
	for i, spot in { { 58, 30, 0.35 }, { 74, 14, -0.5 }, { 60, 13, 1.1 } } do
		local at = CFrame.new(spot[1], 0, spot[2]) * CFrame.Angles(0, spot[3], 0)
		local h = 0.14 + i * 0.05
		table.insert(out, B(Vector3.new(4.4, h, 3.2), at * CFrame.new(0, h / 2, 0), SCRAP.sheet[i], DECOR))
		for _, corner in { { -1.9, -1.3 }, { 1.9, -1.3 }, { -1.9, 1.3 }, { 1.9, 1.3 } } do
			table.insert(out, B(Vector3.new(0.3, 0.3, 0.3), at * CFrame.new(corner[1], h, corner[2]), Palette.Metal, BALL))
		end
	end
	-- Мусор: две трети — у холмов (на склонах и вокруг), остальное — по всей свалке.
	local placed, tries = 0, 0
	while placed < 150 and tries < 3000 do
		tries += 1
		local p
		if placed % 3 ~= 2 then
			local m = MOUNDS[random:NextInteger(1, #MOUNDS)]
			local a = random:NextNumber(0, math.pi * 2)
			p = Vector2.new(m[1], m[2]) + Vector2.new(math.cos(a), math.sin(a)) * random:NextNumber(m[3] * 0.25, m[3] + 5)
		else
			p = Vector2.new(random:NextNumber(-88, 88), random:NextNumber(-45, 45))
		end
		if isFree(p) then
			placed += 1
			local y = groundHeight(p)
			local tilt = random:NextNumber(-0.07, 0.07) * (if y > 0 then 3 else 1) -- на бугре вещи лежат криво
			local at = CFrame.new(p.X, y, p.Y) * CFrame.Angles(tilt, random:NextNumber(0.1, 3.0), tilt * 0.5)
			put(out, Junkyard.Scrap(random:NextInteger(1, 9), random:NextInteger(1, 4)), at)
		end
	end
	-- Поддоны (на втором — ещё один поддон сверху).
	for i, spot in { { -64, 36 }, { 50, -28 }, { 72, 30 } } do
		local at = CFrame.new(spot[1], 0, spot[2]) * CFrame.Angles(0, spot[1] * 0.07, 0)
		put(out, Junkyard.Pallet(), at)
		if i == 2 then
			put(out, Junkyard.Pallet(), at * CFrame.new(0.15, 0.52, -0.1) * CFrame.Angles(0, 0.2, 0))
		end
	end
	-- Сорная трава: у обрывов, у подножия холмов и по краям дороги.
	local count = 0
	local function weeds(x: number, z: number)
		count += 1
		put(out, Junkyard.Weeds(count), CFrame.new(x, 0, z) * CFrame.Angles(0, count * 0.9, 0))
	end
	for i = 1, 12 do
		weeds((if i % 2 == 0 then 1 else -1) * random:NextNumber(84, 88), -44 + i * 7.2)
	end
	for _, m in MOUNDS do
		for j = 1, 2 do
			local a = m[4] + j * 2.6
			weeds(m[1] + math.cos(a) * m[3] * 0.9, m[2] + math.sin(a) * m[3] * 0.9)
		end
	end
	for _, spot in { { -6.4, -32 }, { 6.6, -26 }, { 6.5, 22 }, { -6.6, 30 }, { 6.3, 40 }, { -6.5, 16 } } do
		weeds(spot[1], spot[2])
	end
	return out
end

-- Весь декор свалки в координатах зоны.
function Junkyard.Zone(): { Brick }
	local out = Junkyard.Ground()
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
	put(out, Junkyard.Puddle(3.4), at(-40, 8, 0.4))
	put(out, Junkyard.Puddle(2.6), at(18, -28, -0.3))
	put(out, Junkyard.Puddle(3.6), at(50, 6, 0.9))
	-- Фонари вдоль прохода.
	for _, spot in { Vector2.new(-17, -42), Vector2.new(17, -42), Vector2.new(-22, 26), Vector2.new(22, 30) } do
		put(out, Props.Lamp(), at(spot.X, spot.Y))
	end
	return out
end

return Junkyard

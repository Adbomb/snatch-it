-- Вещи «Свалки» (D41, D68): каждая — функция кирпичей в своих координатах (лицо — сторона −Z, низ на y = 0), ставится
-- через put. Ржавые машины, техника, шины, бочки (в том числе жёлтые с чёрной полосой), конусы, будка пса, сторожка,
-- кран с машиной на магните, диван, лужи, поддоны, сорная трава, мелкий мусор (низкий, ≤ 0.6 — проход не перекрывает),
-- а для гор хлама у стен — морские контейнеры и сплющенные машины. Совпадающих граней нет: накладки выступают за
-- грань, стопки — с разными размерами. Зависит от ModelBuilder, Palette, Props.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)
local Props = require(ServerScriptService.Server.World.Models.Props)

type Brick = ModelBuilder.Brick

local B = ModelBuilder.Brick

local JunkKit = {}

JunkKit.B = B
JunkKit.DECOR = { collide = false, shadow = false }
JunkKit.ROUND = { shape = "Cylinder", collide = false, shadow = false }
JunkKit.BALL = { shape = "Ball", collide = false, shadow = false }
JunkKit.UPRIGHT = CFrame.Angles(0, 0, math.rad(90)) -- ось цилиндра вертикально
JunkKit.ALONG_Z = CFrame.Angles(0, math.rad(90), 0) -- ось цилиндра вдоль Z

local DECOR, ROUND, BALL = JunkKit.DECOR, JunkKit.ROUND, JunkKit.BALL
local UPRIGHT, ALONG_Z = JunkKit.UPRIGHT, JunkKit.ALONG_Z

function JunkKit.hex(code: string): Color3
	return Color3.fromHex(code)
end
local hex = JunkKit.hex

-- Палитра свалки: бурое разбавлено яркими акцентами (D68) — ржаво-оранжевый, жёлтый, красный, синий, бирюзовый.
JunkKit.C = {
	tire = hex("2B2B33"),
	rim = hex("9AA3AE"),
	rust = hex("B5653A"),
	rustOrange = hex("D9722E"),
	white = hex("EEF0F3"),
	appliance = hex("DCE3EA"),
	dark = hex("3A3F4A"),
	screen = hex("7FB8D8"),
	crane = hex("F2B632"),
	yellow = hex("F5C431"),
	red = hex("D8392B"),
	blue = hex("2F6BD8"),
	teal = hex("2BA39A"),
	green = hex("4CAF7A"),
	steel = hex("8C949E"),
	concrete = hex("A9A39A"),
	kennel = hex("2BA39A"), -- будка пса — бирюзовая, яркий акцент у площадки
	roof = hex("D84A3A"),
	bone = hex("F6F0E1"),
	bowl = hex("E53935"),
	food = hex("8A5A2B"),
	booth = hex("E3DCCB"),
	puddle = hex("54809A"), -- вода (круглые лужи с грязным краем)
	cone = hex("FF7A1A"),
}
local C = JunkKit.C

-- Кирпичи вещи, сдвинутые и повёрнутые на at.
function JunkKit.put(out: { Brick }, bricks: { Brick }, at: CFrame)
	for _, brick in bricks do
		brick.cframe = at * brick.cframe
		table.insert(out, brick)
	end
end
local put = JunkKit.put

-- Старая машина вдоль X (передом в +X), колёса касаются пола.
function JunkKit.Car(color: Color3): { Brick }
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

function JunkKit.Fridge(): { Brick }
	return {
		B(Vector3.new(2.2, 4.6, 2.0), Vector3.new(0, 2.3, 0), C.white),
		B(Vector3.new(2.06, 0.1, 0.12), Vector3.new(0, 3.1, -1.02), C.dark, DECOR),
		B(Vector3.new(0.16, 1.2, 0.16), Vector3.new(0.75, 3.8, -1.06), Palette.Metal, DECOR),
		B(Vector3.new(0.16, 1.0, 0.16), Vector3.new(0.75, 2.3, -1.06), Palette.Metal, DECOR),
	}
end

function JunkKit.Washer(): { Brick }
	return {
		B(Vector3.new(2.4, 2.6, 2.2), Vector3.new(0, 1.3, 0), C.appliance),
		B(
			Vector3.new(0.12, 1.5, 1.5),
			CFrame.new(0, 1.15, -1.1) * ALONG_Z,
			C.dark,
			{ shape = "Cylinder", collide = false }
		),
		-- стекло выступает за кольцо на 0.06 с каждой стороны (было 0.01 — торцы мерцали, D36)
		B(
			Vector3.new(0.24, 1.1, 1.1),
			CFrame.new(0, 1.15, -1.1) * ALONG_Z,
			C.screen,
			{ shape = "Cylinder", collide = false }
		),
		B(Vector3.new(2.0, 0.36, 0.12), Vector3.new(0, 2.33, -1.12), C.dark, DECOR),
	}
end

function JunkKit.TV(): { Brick }
	return {
		B(Vector3.new(2.6, 2.2, 2.2), Vector3.new(0, 1.1, 0), hex("6B4E3A")),
		B(Vector3.new(1.9, 1.5, 0.12), Vector3.new(-0.15, 1.15, -1.11), C.screen, DECOR),
		B(Vector3.new(0.3, 0.3, 0.12), Vector3.new(1.0, 0.6, -1.12), C.dark, DECOR),
		B(Vector3.new(0.12, 1.5, 0.12), CFrame.new(-0.35, 2.85, 0) * CFrame.Angles(0, 0, 0.45), Palette.Metal, DECOR),
		B(Vector3.new(0.12, 1.5, 0.12), CFrame.new(0.35, 2.85, 0) * CFrame.Angles(0, 0, -0.45), Palette.Metal, DECOR),
	}
end

-- Стопка шин (count штук), у каждой — серый диск сверху; шины чуть сдвинуты — стопка «живая».
function JunkKit.Tires(count: number): { Brick }
	local bricks = {}
	for i = 1, count do
		local shift = Vector3.new(((i * 37) % 5 - 2) * 0.12, 0, ((i * 53) % 5 - 2) * 0.12)
		local at = CFrame.new(Vector3.new(0, 0.5 + (i - 1), 0) + shift) * UPRIGHT
		table.insert(bricks, B(Vector3.new(1.0, 3.2, 3.2), at, C.tire, { shape = "Cylinder" }))
		table.insert(bricks, B(Vector3.new(1.04, 1.5, 1.5), at, C.rim, { shape = "Cylinder", collide = false }))
	end
	return bricks
end

-- Бочка с двумя полосами (band — цвет полос; по умолчанию жёлтые, у жёлтой бочки — чёрные).
function JunkKit.Barrel(color: Color3, band: Color3?): { Brick }
	local bricks = { B(Vector3.new(3, 2, 2), CFrame.new(0, 1.5, 0) * UPRIGHT, color, { shape = "Cylinder" }) }
	for _, y in { 0.8, 2.2 } do
		table.insert(bricks, B(Vector3.new(0.3, 2.08, 2.08), CFrame.new(0, y, 0) * UPRIGHT, band or C.crane, DECOR))
	end
	table.insert(bricks, B(Vector3.new(0.06, 0.5, 0.5), CFrame.new(0.45, 3.03, 0.3) * UPRIGHT, C.dark, DECOR))
	return bricks
end

-- Конус-ограждение.
function JunkKit.Cone(): { Brick }
	return {
		B(Vector3.new(1.4, 0.2, 1.4), Vector3.new(0, 0.1, 0), C.cone, DECOR),
		B(Vector3.new(0.8, 1.2, 0.8), Vector3.new(0, 0.8, 0), C.cone, DECOR),
		B(Vector3.new(0.86, 0.3, 0.86), Vector3.new(0, 0.9, 0), Palette.White, DECOR),
		B(Vector3.new(0.4, 0.5, 0.4), Vector3.new(0, 1.6, 0), C.cone, DECOR),
	}
end

-- Будка сторожевого пса: дверь на −Z, ступенчатая красная крыша, миска с кормом и косточка у входа.
function JunkKit.Kennel(): { Brick }
	local bricks = {
		B(Vector3.new(6.4, 0.4, 6.2), Vector3.new(0, 0.2, 0.4), Palette.WoodDark),
		B(Vector3.new(5, 3.6, 4.2), Vector3.new(0, 2.2, 0.9), C.kennel),
		B(Vector3.new(2.2, 2.6, 0.14), Vector3.new(0, 1.7, -1.22), C.dark, DECOR), -- лаз
		B(Vector3.new(5.8, 0.6, 5.0), Vector3.new(0, 4.3, 0.9), C.roof),
		B(Vector3.new(4.2, 0.6, 5.2), Vector3.new(0, 4.9, 0.9), C.roof:Lerp(Palette.Black, 0.1)),
		B(Vector3.new(2.4, 0.6, 5.4), Vector3.new(0, 5.5, 0.9), C.roof),
		B(Vector3.new(2.6, 0.5, 0.14), Vector3.new(0, 3.55, -1.22), Palette.White, DECOR), -- табличка-косточка
		B(
			Vector3.new(0.5, 1.7, 1.7),
			CFrame.new(2.0, 0.65, -1.9) * UPRIGHT,
			C.bowl,
			{ shape = "Cylinder", collide = false }
		),
		B(
			Vector3.new(0.52, 1.3, 1.3),
			CFrame.new(2.0, 0.67, -1.9) * UPRIGHT,
			C.food,
			{ shape = "Cylinder", collide = false }
		),
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
function JunkKit.Booth(): { Brick }
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
function JunkKit.Crane(reach: number): { Brick }
	local height = 24
	local bricks = {
		B(Vector3.new(7, 2, 7), Vector3.new(0, 1, 0), C.concrete),
		B(Vector3.new(2, height, 2), Vector3.new(0, 2 + height / 2, 0), C.crane, { shape = "Truss" }),
		B(Vector3.new(4.4, 3.4, 4), Vector3.new(0, 2 + height + 1.7, 0), C.crane),
		B(Vector3.new(0.16, 1.8, 3.2), Vector3.new(-2.28, 2 + height + 2, 0), Palette.Glass, DECOR),
		B(
			Vector3.new(2, reach + 4, 2),
			CFrame.new(-reach / 2 + 1, 2 + height + 4.4, 0) * CFrame.Angles(0, 0, math.rad(90)),
			C.crane,
			{ shape = "Truss" }
		),
		B(
			Vector3.new(2, 8, 2),
			CFrame.new(7, 2 + height + 4.4, 0) * CFrame.Angles(0, 0, math.rad(90)),
			C.crane,
			{ shape = "Truss", collide = false }
		),
		B(Vector3.new(3, 3, 3.2), Vector3.new(7.6, 2 + height + 2.6, 0), C.concrete, { collide = false }),
		B(Vector3.new(0.2, 8, 0.2), Vector3.new(-reach, 2 + height - 0.6, 0), C.dark, DECOR),
		B(
			Vector3.new(1.2, 4.4, 4.4),
			CFrame.new(-reach, 2 + height - 5.2, 0) * UPRIGHT,
			C.dark,
			{ shape = "Cylinder" }
		),
		B(Vector3.new(0.4, 3.6, 3.6), CFrame.new(-reach, 2 + height - 4.5, 0) * UPRIGHT, C.roof, {
			shape = "Cylinder",
			collide = false,
		}),
	}
	-- Машина висит под магнитом, чуть наклонена.
	local carTop = 3.9
	local hang = CFrame.new(-reach, 2 + height - 5.8 - carTop - 0.05, 0) * CFrame.Angles(0, 0.4, math.rad(6))
	put(bricks, JunkKit.Car(hex("3E7CC9")), hang)
	return bricks
end

-- Старый диван: сиденье, спинка, подлокотники, заплатка, выпавшая пружина.
function JunkKit.Sofa(color: Color3): { Brick }
	return {
		B(Vector3.new(6, 1.4, 2.6), Vector3.new(0, 0.9, 0), color),
		B(Vector3.new(5.8, 2.2, 0.8), Vector3.new(0, 2.2, 1.1), color:Lerp(Palette.Black, 0.1)),
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
function JunkKit.Puddle(radius: number): { Brick }
	local mud = hex("5E4B38")
	local function water(transparency: number)
		return {
			shape = "Cylinder",
			material = Enum.Material.Glass,
			transparency = transparency,
			collide = false,
			shadow = false,
		}
	end
	local bricks = {}
	for i, spot in { { 0.15, 0.1, 1.15 }, { -0.35, -0.3, 0.85 } } do
		local h = 0.03 + i * 0.03
		local d = radius * 2 * spot[3]
		table.insert(
			bricks,
			B(Vector3.new(h, d, d), CFrame.new(spot[1] * radius, h / 2, spot[2] * radius) * UPRIGHT, mud, ROUND)
		)
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
function JunkKit.Pallet(): { Brick }
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
function JunkKit.Weeds(variant: number): { Brick }
	local green = Palette.Leaves[(variant - 1) % #Palette.Leaves + 1]
	local bricks = {}
	for i, blade in
		{ { 0, 0, 1.5, 0.15 }, { 0.4, 0.2, 1.1, -0.35 }, { -0.35, 0.25, 0.9, 0.4 }, { 0.1, -0.4, 0.75, -0.2 } }
	do
		local at = CFrame.new(blade[1], 0, blade[2])
			* CFrame.Angles(0, i * 1.3, blade[4])
			* CFrame.new(0, blade[3] / 2, 0)
		local tone = if i % 2 == 0 then green:Lerp(Palette.White, 0.12) else green
		table.insert(bricks, B(Vector3.new(0.34, blade[3], 0.34), at, tone, DECOR))
	end
	return bricks
end

-- Мелкий мусор на земле (D68: не выше 0.6 — проход не перекрывает): доски, лист железа, труба, банки, кирпичи,
-- лежащая шина, колпак, гайки. Цвета — с яркими (красная и жёлтая банки, ржавый лист).
JunkKit.SCRAP = {
	plank = { hex("A0784A"), hex("8A6238"), hex("B88A55") },
	sheet = { hex("8C949E"), hex("C0612E"), hex("7D8790") },
	can = { hex("D84A3A"), hex("2F6BD8"), hex("43A047"), hex("F2B632") },
	brick = hex("B5533C"),
}
local SCRAP = JunkKit.SCRAP

function JunkKit.Scrap(kind: number, tone: number): { Brick }
	local function pick(list: { Color3 }): Color3
		return list[(tone - 1) % #list + 1]
	end
	if kind == 1 then
		return { B(Vector3.new(2.8, 0.2, 0.55), Vector3.new(0, 0.1, 0), pick(SCRAP.plank), DECOR) }
	elseif kind == 2 then
		local wood = pick(SCRAP.plank)
		return {
			B(Vector3.new(2.6, 0.2, 0.5), Vector3.new(0, 0.1, 0), wood, DECOR),
			B(
				Vector3.new(2.2, 0.2, 0.5),
				CFrame.new(0.2, 0.3, 0.1) * CFrame.Angles(0, 0.9, 0),
				wood:Lerp(Palette.Black, 0.12),
				DECOR
			),
		}
	elseif kind == 3 then
		return { B(Vector3.new(2.2, 0.12, 1.5), Vector3.new(0, 0.06, 0), pick(SCRAP.sheet), DECOR) }
	elseif kind == 4 then
		return { B(Vector3.new(3.2, 0.5, 0.5), Vector3.new(0, 0.25, 0), pick(SCRAP.sheet), ROUND) }
	elseif kind == 5 then
		local tin = pick(SCRAP.can)
		return {
			B(Vector3.new(0.8, 0.45, 0.45), Vector3.new(0, 0.22, 0), tin, ROUND),
			B(
				Vector3.new(0.7, 0.42, 0.42),
				CFrame.new(0.5, 0.21, 0.6) * CFrame.Angles(0, 1.1, 0),
				tin:Lerp(Palette.White, 0.1),
				ROUND
			),
		}
	elseif kind == 6 then
		return {
			B(Vector3.new(0.9, 0.45, 0.45), Vector3.new(0, 0.22, 0), SCRAP.brick, DECOR),
			B(
				Vector3.new(0.9, 0.45, 0.45),
				CFrame.new(0.3, 0.22, 0.7) * CFrame.Angles(0, 0.7, 0),
				SCRAP.brick:Lerp(Palette.Black, 0.1),
				DECOR
			),
		}
	elseif kind == 7 then
		return {
			B(Vector3.new(0.5, 2.6, 2.6), CFrame.new(0, 0.25, 0) * UPRIGHT, C.tire, ROUND),
			B(Vector3.new(0.54, 1.2, 1.2), CFrame.new(0, 0.25, 0) * UPRIGHT, C.rim, ROUND),
		}
	elseif kind == 8 then
		return { B(Vector3.new(0.14, 1.2, 1.2), CFrame.new(0, 0.07, 0) * UPRIGHT, C.rim, ROUND) }
	end
	return {
		B(Vector3.new(0.42, 0.42, 0.42), Vector3.new(0, 0.21, 0), C.dark, BALL),
		B(Vector3.new(0.36, 0.36, 0.36), Vector3.new(0.7, 0.18, 0.4), C.rim, BALL),
	}
end

-- Морской контейнер вдоль X: корпус, рёбра на боках (выступают на 0.12), створки на торце +X. collide — твёрдый
-- корпус (низ горы у стены) или без столкновений (верх горы).
function JunkKit.Container(color: Color3, length: number, collide: boolean): { Brick }
	local opts = if collide then nil else DECOR
	local bricks = { B(Vector3.new(length, 4.6, 4.4), Vector3.new(0, 2.3, 0), color, opts) }
	local rib = color:Lerp(Palette.Black, 0.18)
	local count = math.floor(length / 1.6)
	for i = 1, count do
		local x = -length / 2 + (i - 0.5) * length / count
		table.insert(bricks, B(Vector3.new(0.4, 4.2, 4.64), Vector3.new(x, 2.3, 0), rib, DECOR))
	end
	table.insert(bricks, B(Vector3.new(0.14, 4.3, 4.1), Vector3.new(length / 2 + 0.1, 2.3, 0), rib, DECOR))
	return bricks
end

-- Сплющенная машина (для стопок в горах хлама): плоский корпус, вмятая крыша, ржавое пятно, колесо сбоку.
function JunkKit.CrushedCar(color: Color3): { Brick }
	return {
		B(Vector3.new(7.6, 1.3, 3.7), Vector3.new(0, 0.65, 0), color, DECOR),
		B(
			Vector3.new(3.8, 0.55, 3.3),
			CFrame.new(-0.3, 1.5, 0) * CFrame.Angles(0, 0, 0.06),
			color:Lerp(Palette.White, 0.12),
			DECOR
		),
		B(Vector3.new(1.8, 0.8, 0.12), Vector3.new(1.8, 0.7, -1.9), C.rust, DECOR),
		B(Vector3.new(0.7, 1.5, 1.5), CFrame.new(2.6, 0.6, 1.92) * ALONG_Z, C.tire, ROUND),
	}
end

JunkKit.Crate = Props.Crate

return JunkKit

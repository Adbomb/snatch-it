-- Здание музея кодом (D36). Уровни 1–2 — утверждённый стартовый зал: небольшой светлый классический зал с портиком
-- на 4 колонны, двускатной крышей, фронтоном и эмблемой. Улучшения достраивают его в том же стиле:
-- 3–4 — боковые залы (проходы из главного зала), 5–6 — портик на 6 колонн и парапеты, 7–8 — купол,
-- 9–10 — позолота; на чётных уровнях — оформление (кадки, фонари, знамёна, статуи, вазы).
-- Цвет участка — только акцентом: фриз, эмблема, полосы, знамёна (Palette.Muted), крыша — лишь оттенком (Palette.Roof).
-- Все детали Plastic с вариантом LegoSquaresSoft (квадратный рельеф, спокойная шахматка), окна — Glass.
-- Совпадающих граней у разных деталей нет (D36): накладки выступают ≥ 0.1, стыки — только встык.
-- Начало координат — центр участка на уровне пола зала (верх подиума), вход — сторона -Z, трава на y = Ground.
-- Витрины, сундук, табличку и лампы строит Util/PartBuilder на постоянных местах внутри главного зала.
-- Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

type Brick = ModelBuilder.Brick

local MuseumHall = {}

-- Размеры главного зала (одинаковые на всех уровнях — на них опираются витрины, сундук, табличка, лампы).
MuseumHall.FacadeZ = -12.7 -- наружная грань фасада
MuseumHall.SignY = 11.5 -- центр таблички «МУЗЕЙ <имя>» над входом
MuseumHall.Ceiling = 14.4 -- низ потолка главного зала
MuseumHall.LampHeight = 11.9 -- низ подвесных ламп над витринами
MuseumHall.Ground = -1.3 -- верх травы относительно пола зала

local SOFT = "LegoSquaresSoft"
local H, HW, FZ, BZ, T = MuseumHall.Ceiling, 18, MuseumHall.FacadeZ, 20.7, 1.4
local DOOR, DOORH = 6, 10 -- полуширина и высота входа
local PZ = -23 -- передний край портика
local G = MuseumHall.Ground
-- Боковые залы (уровень 3+): от главной стены до WX, по глубине WZ0…WZ1, высота WH; проход из главного зала.
local WX, WZ0, WZ1, WH = 29, -6, 18, 10.4
local PASS0, PASS1, PASSH = 1, 9, 8

function MuseumHall.Build(level: number, accent: Color3): { Brick }
	local tier = math.clamp(math.ceil(level / 2), 1, 5)
	local decorated = level % 2 == 0
	local muted = Palette.Muted(accent)
	local gold = tier >= 5
	local bricks: { Brick } = {}

	-- Брусок по границам (координаты зала), рельеф LegoSquaresSoft.
	local function box(name: string, x0, x1, y0, y1, z0, z1, color: Color3, extra: { [string]: any }?)
		local props: { [string]: any } = { name = name, variant = SOFT }
		if extra then
			for k, v in extra do
				props[k] = v
			end
		end
		if props.variant == false then
			props.variant = nil -- стекло, неон, листва: без варианта
		end
		local size = Vector3.new(x1 - x0, y1 - y0, z1 - z0)
		local center = Vector3.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
		table.insert(bricks, ModelBuilder.Brick(size, center, color, props))
	end
	local function glass(x0, x1, y0, y1, z0, z1)
		box("Window", x0, x1, y0, y1, z0, z1, Palette.MuseumGlass, {
			variant = false,
			material = Enum.Material.Glass,
			transparency = 0.25,
		})
	end
	-- Окно на стене: рама (0.1 наружу) и стекло (0.15 наружу). axis — "x" (стена x = at) или "z" (стена z = at).
	local function window(axis: string, at: number, out: number, a0: number, a1: number, y0: number, y1: number)
		local inner = at - out * 0.05
		local f0, f1 = math.min(inner, at + out * 0.1), math.max(inner, at + out * 0.1)
		local g0, g1 = math.min(inner, at + out * 0.15), math.max(inner, at + out * 0.15)
		if axis == "x" then
			box("WindowFrame", f0, f1, y0 - 0.4, y1 + 0.4, a0 - 0.4, a1 + 0.4, Palette.MuseumTrim)
			glass(g0, g1, y0, y1, a0, a1)
		else
			box("WindowFrame", a0 - 0.4, a1 + 0.4, y0 - 0.4, y1 + 0.4, f0, f1, Palette.MuseumTrim)
			glass(a0, a1, y0, y1, g0, g1)
		end
	end

	local wings = tier >= 2

	-- ── Главный зал: стены (с проходами в боковые залы с уровня 3) ─────────────────────────────────
	for _, s in { -1, 1 } do
		local x0, x1 = if s > 0 then HW - T else -HW, if s > 0 then HW else -HW + T
		if wings then
			box("SideWall", x0, x1, 0, H, FZ, PASS0, Palette.MuseumWall)
			box("SideWall", x0, x1, 0, H, PASS1, BZ, Palette.MuseumWall)
			box("PassLintel", x0, x1, PASSH, H, PASS0, PASS1, Palette.MuseumWall)
		else
			box("SideWall", x0, x1, 0, H, FZ, BZ, Palette.MuseumWall)
			for _, z in { -1, 11 } do
				window("x", s * HW, s, z - 2, z + 2, 4, 10)
			end
		end
	end
	box("BackWall", -HW + T, HW - T, 0, H, BZ - T, BZ, Palette.MuseumWall)
	box("FrontWall", -HW + T, -DOOR, 0, H, FZ, FZ + T, Palette.MuseumWall)
	box("FrontWall", DOOR, HW - T, 0, H, FZ, FZ + T, Palette.MuseumWall)
	box("Lintel", -DOOR, DOOR, DOORH, H, FZ, FZ + T, Palette.MuseumWall)

	-- Цоколь (0.3 наружу) и карниз (0.4 наружу): бруски встык, без перекрытий; цоколь не перекрывает проходы.
	for _, band in { { 0, 1.2, 0.3, "Base" }, { H - 1, H, 0.4, "Cornice" } } do
		local y0, y1, out, name = band[1], band[2], band[3], band[4]
		local trim = if gold and name == "Cornice" then Palette.MuseumGold else Palette.MuseumTrim
		for _, s in { -1, 1 } do
			local x0, x1 = if s > 0 then HW - 0.1 else -HW - out, if s > 0 then HW + out else -HW + 0.1
			if wings and name == "Base" then
				-- Цоколь чуть отступает от проёма: торцы не совпадают с торцами стены (D36).
				box(name, x0, x1, y0, y1, FZ - out, PASS0 - 0.1, trim)
				box(name, x0, x1, y0, y1, PASS1 + 0.1, BZ + out, trim)
			else
				box(name, x0, x1, y0, y1, FZ - out, BZ + out, trim)
			end
		end
		box(name, -HW + 0.1, HW - 0.1, y0, y1, BZ - 0.1, BZ + out, trim)
		if name == "Base" then
			box(name, -HW + 0.1, -DOOR - 0.1, y0, y1, FZ - out, FZ + 0.1, trim)
			box(name, DOOR + 0.1, HW - 0.1, y0, y1, FZ - out, FZ + 0.1, trim)
		else
			box(name, -HW + 0.1, HW - 0.1, y0, y1, FZ - out, FZ + 0.1, trim)
		end
	end

	-- Потолок над залом и портиком; фриз по переднему краю (цвет участка, на 9–10 — золото).
	box("Ceiling", -HW - 0.4, HW + 0.4, H, H + 0.6, PZ, BZ + 0.4, Palette.MuseumTrim)
	box("Frieze", -HW - 0.5, HW + 0.5, H + 0.1, H + 0.5, PZ - 0.2, PZ + 0.2, if gold then Palette.MuseumGold else muted)

	-- Портик: 4 колонны, с уровня 5 — 6.
	local columns = if tier >= 3 then { -15.5, -10, -4.5, 4.5, 10, 15.5 } else { -15, -9, 9, 15 }
	local capColor = if gold then Palette.MuseumGold else Palette.MuseumTrim
	for _, x in columns do
		box("ColumnBase", x - 1.2, x + 1.2, 0, 0.6, -20.7, -18.3, capColor)
		box("Column", x - 0.9, x + 0.9, 0.6, H - 0.8, -20.4, -18.6, Palette.MuseumColumn)
		box("ColumnCap", x - 1.3, x + 1.3, H - 0.8, H, -20.8, -18.2, capColor)
	end

	-- Двускатная крыша (конёк вдоль глубины) и фронтон с эмблемой. Высокая сторона клина — на +Z детали;
	-- поворот на ∓90° по Y направляет её к коньку (x = 0).
	local RH, RHW = 7, HW + 1.4
	local RZ0, RZ1 = PZ - 0.5, BZ + 0.9
	for _, s in { -1, 1 } do
		local turn = CFrame.Angles(0, -s * math.rad(90), 0)
		table.insert(bricks, ModelBuilder.Brick(
			Vector3.new(RZ1 - RZ0, RH, RHW),
			CFrame.new(s * RHW / 2, H + 0.6 + RH / 2, (RZ0 + RZ1) / 2) * turn,
			Palette.Roof(accent),
			{ name = "Roof", shape = "Wedge", variant = SOFT }
		))
		-- Фронтон чуть меньше крыши (виден край кровли) и выходит вперёд, задняя часть — внутри крыши.
		local w = RHW - 1.6
		local h = RH * w / RHW
		table.insert(bricks, ModelBuilder.Brick(
			Vector3.new(0.8, h, w),
			CFrame.new(s * w / 2, H + 0.6 + h / 2, RZ0 - 0.1) * turn,
			Palette.MuseumWall,
			{ name = "Pediment", shape = "Wedge", variant = SOFT }
		))
	end
	table.insert(bricks, ModelBuilder.Brick(
		Vector3.new(0.4, 3.2, 3.2),
		CFrame.new(0, H + 0.6 + 2.4, RZ0 - 0.6) * CFrame.Angles(0, math.rad(90), 0),
		if gold then Palette.MuseumGold else muted,
		{ name = "Emblem", shape = "Cylinder", variant = SOFT }
	))

	-- Ступени от травы к порталу; с уровня 5 — во всю ширину портика.
	local stepHalf = if tier >= 3 then HW else 10
	box("Step", -stepHalf, stepHalf, G, G / 2, -25, -22, Palette.MuseumTrim)
	box("Step", -stepHalf, stepHalf, G / 2, 0, -23.5, -22, Palette.MuseumTrim)

	-- ── Боковые залы (уровень 3+) ─────────────────────────────────────────────────────────────────
	if wings then
		for _, s in { -1, 1 } do
			local function X(a: number, b: number): (number, number)
				return math.min(s * a, s * b), math.max(s * a, s * b)
			end
			local ax, bx
			-- Пол за краем подиума участка (до x = 22 пол — подиум): верх вровень с полом зала, с отступом под цоколь.
			ax, bx = X(22, WX + 0.5)
			box("WingFloor", ax, bx, G - 0.3, 0, WZ0 - 0.5, WZ1 + 0.5, Palette.MuseumTrim)
			-- Стены: наружная, передняя и задняя (встык с главной стеной).
			ax, bx = X(WX - T, WX)
			box("WingWall", ax, bx, 0, WH, WZ0, WZ1, Palette.MuseumWall)
			ax, bx = X(HW, WX - T)
			box("WingWall", ax, bx, 0, WH, WZ0, WZ0 + T, Palette.MuseumWall)
			box("WingWall", ax, bx, 0, WH, WZ1 - T, WZ1, Palette.MuseumWall)
			-- Цоколь: наружный и передний/задний (от главного цоколя, без перекрытия).
			ax, bx = X(WX - 0.1, WX + 0.3)
			box("WingBase", ax, bx, 0, 1.2, WZ0 - 0.3, WZ1 + 0.3, Palette.MuseumTrim)
			ax, bx = X(HW + 0.3, WX - 0.1)
			box("WingBase", ax, bx, 0, 1.2, WZ0 - 0.3, WZ0 + 0.1, Palette.MuseumTrim)
			box("WingBase", ax, bx, 0, 1.2, WZ1 - 0.1, WZ1 + 0.3, Palette.MuseumTrim)
			-- Плоская крыша с напуском — она же карниз; полоса цвета участка под ней на фасаде.
			ax, bx = X(HW, WX + 0.4)
			box("WingRoof", ax, bx, WH, WH + 0.6, WZ0 - 0.4, WZ1 + 0.4, Palette.MuseumTrim)
			ax, bx = X(HW + 0.3, WX + 0.05)
			box("WingStripe", ax, bx, WH - 1.4, WH - 0.8, WZ0 - 0.2, WZ0 + 0.05, muted)
			-- Окна: два на наружной стене, одно на фасаде.
			for _, z in { 0, 12 } do
				window("x", s * WX, s, z - 2, z + 2, 3.2, 8)
			end
			local wa, wb = X((HW + WX) / 2 - 2, (HW + WX) / 2 + 2)
			window("z", WZ0, -1, wa, wb, 3.2, 8)
			-- Свет в зале.
			ax, bx = X((HW + WX) / 2 - 1, (HW + WX) / 2 + 1)
			box("WingLamp", ax, bx, WH - 0.5, WH, 5, 7, Palette.Lamp, {
				variant = false,
				material = Enum.Material.Neon,
				collide = false,
				shadow = false,
				light = { range = 16, brightness = 0.8, color = Palette.Lamp },
			})
			-- Парапет на крыше (уровень 5+), чуть утоплен от края крыши.
			if tier >= 3 then
				ax, bx = X(HW, WX + 0.3)
				box("Parapet", ax, bx, WH + 0.6, WH + 1.4, WZ0 - 0.3, WZ0 + 0.3, Palette.MuseumTrim)
			end
		end
	end

	-- ── Купол (уровень 7+): барабан, карниз-кольцо, купол и фонарь цвета участка ─────────────────────
	if tier >= 4 then
		local up = CFrame.Angles(0, 0, math.rad(90)) -- ось цилиндра — вертикально
		local cz = (FZ + BZ) / 2
		local function cylinder(name: string, radius: number, y0: number, y1: number, color: Color3)
			table.insert(bricks, ModelBuilder.Brick(
				Vector3.new(y1 - y0, radius * 2, radius * 2),
				CFrame.new(0, (y0 + y1) / 2, cz) * up,
				color,
				{ name = name, shape = "Cylinder", variant = SOFT }
			))
		end
		cylinder("Drum", 5.5, 18, 23.5, Palette.MuseumWall)
		cylinder("DrumRing", 6, 23.2, 23.9, if gold then Palette.MuseumGold else Palette.MuseumTrim)
		table.insert(bricks, ModelBuilder.Brick(
			Vector3.new(11, 11, 11),
			CFrame.new(0, 23.5, cz),
			if gold then Palette.MuseumGold else Palette.MuseumTrim,
			{ name = "Dome", shape = "Ball", variant = SOFT }
		))
		cylinder("Lantern", 1.2, 28.6, 31, Palette.MuseumColumn)
		table.insert(bricks, ModelBuilder.Brick(Vector3.new(2, 2, 2), CFrame.new(0, 31.6, cz), muted, {
			name = "LanternTop",
			shape = "Ball",
			variant = SOFT,
		}))
	end

	-- ── Оформление чётных уровней ─────────────────────────────────────────────────────────────────
	if decorated then
		-- Кадки с кустами по бокам портика (до уровня 6), дальше — статуи (на 10-м — золотые). Стоят на подиуме
		-- участка между крайней колонной и краем: не мешают гантели во дворе.
		for _, s in { -1, 1 } do
			local x, z = s * 19.5, -18
			if tier <= 3 then
				box("Planter", x - 1.5, x + 1.5, 0, 1.4, z - 1.5, z + 1.5, Palette.MuseumTrim)
				box("Shrub", x - 1.2, x + 1.2, 1.4, 3.2, z - 1.2, z + 1.2, Palette.Leaves[1], { variant = false })
			else
				local statue = if gold then Palette.MuseumGold else Palette.MuseumColumn
				box("Plinth", x - 1.3, x + 1.3, 0, 2, z - 1.3, z + 1.3, Palette.MuseumTrim)
				box("Statue", x - 0.6, x + 0.6, 2, 5, z - 0.4, z + 0.4, statue)
				box("Statue", x - 0.5, x + 0.5, 5, 6, z - 0.5, z + 0.5, statue)
				box("Statue", x - s * 1.1, x - s * 0.6, 3.5, 6.5, z - 0.3, z + 0.3, statue)
			end
		end
		-- Фонари у боковых залов (уровень 4+).
		if wings then
			for _, s in { -1, 1 } do
				local x = s * (WX + 1.5)
				local pz = WZ0 - 2
				box("LampPost", x - 0.25, x + 0.25, G, G + 5, pz - 0.25, pz + 0.25, Palette.Black, { variant = false })
				box("LampBulb", x - 0.5, x + 0.5, G + 5, G + 6, pz - 0.5, pz + 0.5, Palette.Lamp, {
					variant = false,
					material = Enum.Material.Neon,
					collide = false,
					shadow = false,
					light = { range = 12, brightness = 0.7, color = Palette.Lamp },
				})
			end
		end
		-- Знамёна цвета участка перед колоннами (уровень 6+).
		if tier >= 3 then
			for _, x in { -15.5, -4.5, 4.5, 15.5 } do
				box("Banner", x - 1, x + 1, 6, H - 1.2, -21.2, -21, muted, { collide = false })
			end
		end
		-- Вазы на углах крыши портика (уровень 10).
		if gold then
			for _, s in { -1, 1 } do
				local x = s * 17.5
				box("Vase", x - 0.6, x + 0.6, H + 0.6, H + 1.4, PZ + 0.4, PZ + 1.6, Palette.MuseumGold)
				box("Vase", x - 0.9, x + 0.9, H + 1.4, H + 2.8, PZ + 0.1, PZ + 1.9, Palette.MuseumGold)
			end
		end
	end
	return bricks
end

return MuseumHall

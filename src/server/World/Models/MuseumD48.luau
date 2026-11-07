-- Музей D48-C — временная Part-версия (ТЗ владельца 2026-11-06: до загрузки мешей, ≤ 400 деталей на музей).
-- Модули с теми же именами и началом координат, что модули Blender пачки Pack3_d48 (scripts/blender/d48_final.py):
-- World/MuseumVisual ставит их по MuseumLayout.Modules и для каждого модуля решает, чем его показать — этими
-- кирпичами или мешами. Кирпич с collide = true — «оболочка»: пол, стены, ступени, тумбы. Она есть всегда, а при
-- мешах становится невидимой — столкновения не зависят от того, какая графика показана. collide = false — детали
-- вида (без столкновений и запросов). Упрощено против Blender: без фасок, круги — Cylinder, мелочь опущена.
-- Совпадающих граней у разных деталей нет (D36): накладки выступают, детали встык (проверка —
-- scripts/lune/check_museum_layout.luau). Всё Plastic с вариантом LegoSquaresSoft, кроме стекла и неона.
-- Зависит от ModelBuilder, Config/MuseumLayout.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local MuseumLayout = require(ReplicatedStorage.Shared.Config.MuseumLayout)
local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)

type Brick = ModelBuilder.Brick

local L = MuseumLayout
local HW, FZ, BZ = L.Hall.HalfWidth, L.Hall.Front, L.Hall.Back
local IX, IZ0, IZ1 = L.Hall.InnerX, L.Hall.InnerZ0, L.Hall.InnerZ1
local CEIL, DOOR, DOORH = L.Hall.Ceiling, L.Hall.DoorHalf, L.Hall.DoorHeight
local G, SLAB, PZ = L.Hall.Ground, L.Hall.Slab, L.Hall.Portico
local TOP = CEIL + 1.4 -- верх стен зала
local PV_X, PV_Z0, PV_Z1, PV_H = L.Pavilion.HalfX, L.Pavilion.Z0, L.Pavilion.Z1, L.Pavilion.Height
local ST0, STW, WX, WZ1 = L.Stair.TopZ, L.Stair.HalfWidth, L.Stair.WellX, L.Stair.WellZ1
local VF, VCEIL = L.Vault.Floor, L.Vault.Ceiling
local GAL = L.Gallery
local SOFT = "LegoSquaresSoft"
local UPRIGHT = CFrame.Angles(0, 0, math.rad(90)) -- ось цилиндра вертикально
local ALONG_Z = CFrame.Angles(0, math.rad(90), 0) -- ось цилиндра вдоль z

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

-- Цвета — те же коды, что у ролей мешей (Pack3_d48.layout.json).
local C = {
	wall = hex("F4EFE4"),
	pil = hex("FBF8F1"),
	gold = hex("E9B43C"),
	navy = hex("26345E"),
	navyDark = hex("1A2440"),
	floor = hex("EFE6D3"),
	runner = hex("B8283A"),
	ceiling = hex("D3E3F2"),
	backdrop = hex("2E4377"),
	steel = hex("3A5A8C"),
	steelLight = hex("A7B6C8"),
	steelDark = hex("5E7186"),
	roof = hex("D9705A"),
	step = hex("93A7C7"),
	disk = hex("AEBCD0"),
	vWall = hex("1F3A63"),
	vPanel = hex("2C5283"),
	vFloor = hex("17223D"),
	vCeil = hex("131D33"),
	locker = hex("8EA2BD"),
	plant = hex("4FB45A"),
	plantDark = hex("3C8F47"),
	stone = hex("D8D2C4"),
	chest = hex("3E7BE0"),
	chestLight = hex("5A93F0"),
	red = hex("F0473C"),
	cyan = hex("2FB5CF"), -- D50: мягче прежнего 39E1FF (неон у сундука, павильона, хранилища)
	warm = hex("FFD88A"),
	screen = hex("1D6FE0"),
	sky = hex("EAF7FF"),
	glass = hex("BDEBFF"),
}
local MuseumD48 = {}

MuseumD48.Colors = C

-- Модули хранилища: оболочка — на сервере, детали вида видит только владелец (клиент, World/MuseumVisual).
MuseumD48.VaultModules = {
	D48_VaultShell = true,
	D48_Safe = true,
	D48_Terminal = true,
	D48_Security = true,
	D48_Archive = true,
	D48_Lockers = true,
}

type Opts = {
	shell: boolean?, -- оболочка: столкновения (по умолчанию — деталь вида)
	material: Enum.Material?,
	transparency: number?,
	name: string?,
	shadow: boolean?,
	invisible: boolean?, -- оболочка без вида: только столкновение (стеллажи хранилища)
}

-- Брусок по границам (x0 < x1 и т. д.) в осях модуля.
local function box(list: { Brick }, x0, x1, y0, y1, z0, z1, color: Color3, opts: Opts?)
	local o = opts or {} :: Opts
	local a0, a1 = math.min(x0, x1), math.max(x0, x1)
	local b0, b1 = math.min(y0, y1), math.max(y0, y1)
	local c0, c1 = math.min(z0, z1), math.max(z0, z1)
	local material = o.material
	local extra: { [string]: any } = {
		name = o.name or (if o.shell then "Shell" else "Detail"),
		collide = o.shell == true,
		shell = o.shell == true,
		shadow = o.shadow,
		material = material,
		transparency = if o.invisible then 1 else o.transparency,
		variant = if material == nil or material == Enum.Material.Plastic then SOFT else nil,
	}
	table.insert(
		list,
		ModelBuilder.Brick(
			Vector3.new(a1 - a0, b1 - b0, c1 - c0),
			Vector3.new((a0 + a1) / 2, (b0 + b1) / 2, (c0 + c1) / 2),
			color,
			extra
		)
	)
end

local function glow(list: { Brick }, x0, x1, y0, y1, z0, z1, color: Color3)
	box(list, x0, x1, y0, y1, z0, z1, color, { material = Enum.Material.Neon, shadow = false, name = "Glow" })
end

-- Цилиндр: ось "y" (вертикально), "x" или "z"; радиус, длина по оси.
local function cylinder(
	list: { Brick },
	center: Vector3,
	radius: number,
	length: number,
	axis: string,
	color: Color3,
	opts: Opts?
)
	local o = opts or {} :: Opts
	local turn = if axis == "y" then UPRIGHT elseif axis == "z" then ALONG_Z else CFrame.identity
	local material = o.material
	table.insert(
		list,
		ModelBuilder.Brick(Vector3.new(length, radius * 2, radius * 2), CFrame.new(center) * turn, color, {
			name = o.name or (if o.shell then "Shell" else "Detail"),
			shape = "Cylinder",
			collide = o.shell == true,
			shell = o.shell == true,
			shadow = o.shadow,
			material = material,
			variant = if material == nil then SOFT else nil,
		})
	)
end

-- Полоса a…b от боковой стены зала внутрь (sx = −1 / +1) → x0, x1.
local function sideX(sx: number, a: number, b: number): (number, number)
	local x0, x1 = sx * (IX - a), sx * (IX - b)
	return math.min(x0, x1), math.max(x0, x1)
end

local function gx(sx: number, a: number, b: number): (number, number)
	return math.min(sx * a, sx * b), math.max(sx * a, sx * b)
end

local SHELL: Opts = { shell = true }

-- ── Зал: пол с проёмом лестницы, фасад, задняя стена, портик, дорожка ─────────────────────────────────────────
local function hall(): { Brick }
	local b: { Brick } = {}
	-- пол (оболочка): вокруг проёма лестницы |x| < WX, z ST0…WZ1
	for _, r in { { -HW, HW, FZ, ST0 }, { -HW, -WX, ST0, BZ }, { WX, HW, ST0, BZ }, { -WX, WX, WZ1, BZ } } do
		box(b, r[1], r[2], -SLAB, 0, r[3], r[4], C.floor, { shell = true, name = "Floor" })
	end
	-- фасад с проёмом входа и задняя стена (боковые стены — модули Side)
	box(b, -IX, -DOOR, 0, TOP, FZ, IZ0, C.wall, SHELL)
	box(b, DOOR, IX, 0, TOP, FZ, IZ0, C.wall, SHELL)
	box(b, -DOOR, DOOR, DOORH, TOP, FZ, IZ0, C.wall, SHELL)
	box(b, -IX, IX, 0, TOP, IZ1, BZ, C.wall, SHELL)
	-- плинтус и золотой пояс изнутри (боковые — в модулях Side; встык у x ±(IX − 0.2))
	for _, band in { { 0, 1, C.navy }, { 12.4, 12.7, C.gold } } do
		box(b, -IX + 0.2, -DOOR - 1.2, band[1], band[2], IZ0, IZ0 + 0.2, band[3]) -- до сундука не доходит
		box(b, DOOR + 1.2, IX - 0.2, band[1], band[2], IZ0, IZ0 + 0.2, band[3])
		box(b, -IX + 0.2, IX - 0.2, band[1], band[2], IZ1 - 0.2, IZ1, band[3])
	end
	-- задняя стена: эмблема и два знамени
	cylinder(b, Vector3.new(0, 12.3, IZ1 - 0.25), 2.1, 0.5, "z", C.gold)
	cylinder(b, Vector3.new(0, 12.3, IZ1 - 0.55), 1.5, 0.2, "z", C.navy)
	for _, sx in { -1, 1 } do
		box(b, sx * 8 - 1.6, sx * 8 + 1.6, 6.0, 12.8, IZ1 - 0.15, IZ1, C.backdrop)
		box(b, sx * 8 - 1.9, sx * 8 + 1.9, 12.8, 13.1, IZ1 - 0.3, IZ1, C.gold)
	end
	-- дорожка с золотыми кромками и медальон
	box(b, -3.2, 3.2, 0, 0.08, IZ0 + 0.05, PV_Z0 - 0.35, C.runner, { shadow = false })
	for _, sx in { -1, 1 } do
		box(b, sx * 3.2, sx * 3.5, 0, 0.12, IZ0, PV_Z0 - 0.3, C.gold, { shadow = false }) -- встык с дорожкой
	end
	cylinder(b, Vector3.new(0, 0.07, -1.4), 3.3, 0.14, "y", C.gold, { shadow = false })
	cylinder(b, Vector3.new(0, 0.09, -1.4), 2.7, 0.18, "y", C.navy, { shadow = false })
	cylinder(b, Vector3.new(0, 0.11, -1.4), 1.0, 0.22, "y", C.gold, { shadow = false })
	-- портик: две ступени и пол, 4 колонны, антаблемент, ступенчатый фронтон с медальоном
	local rise = -G / 3
	box(b, -16, 16, G, G + rise, PZ, PZ + 0.7, C.floor, SHELL)
	box(b, -16, 16, G, G + 2 * rise, PZ + 0.7, PZ + 1.4, C.floor, SHELL)
	box(b, -16, 16, G, 0, PZ + 1.4, FZ, C.floor, SHELL)
	box(b, -HW - 1, HW + 1, G, -0.02, BZ, BZ + 1, C.wall, SHELL) -- бортик подиума сзади
	for _, cx in { -14, -8, 8, 14 } do
		cylinder(b, Vector3.new(cx, 6.5, -19.4), 0.95, 13.0, "y", C.wall, SHELL)
		box(b, cx - 1.25, cx + 1.25, 13.0, 13.6, -20.65, -18.15, C.gold)
		box(b, cx - 1.45, cx + 1.45, 13.6, 14.0, -20.85, -17.95, C.pil)
	end
	box(b, -16.5, 16.5, 14.0, 16.0, -22.6, FZ, C.pil, SHELL)
	box(b, -16.6, 16.6, 14.5, 15.3, -22.75, -22.5, C.gold)
	for k, step in { { 16.5, 16.0 }, { 13.5, 17.2 }, { 10.5, 18.4 }, { 7.5, 19.6 }, { 4.5, 20.8 } } do
		box(b, -step[1], step[1], step[2], step[2] + 1.2, -22.6 + 0.2 * (k - 1), -21.0, C.pil)
	end
	cylinder(b, Vector3.new(0, 18.3, -22.85), 2.0, 0.5, "z", C.gold)
	cylinder(b, Vector3.new(0, 18.3, -23.2), 1.4, 0.3, "z", C.warm, { material = Enum.Material.Neon, shadow = false })
	-- золотая рама входа (выступает в проём на 0.1) и фонари у входа
	box(b, -DOOR - 1, -DOOR + 0.1, 0, DOORH + 1, FZ - 0.5, FZ + 0.3, C.gold)
	box(b, DOOR - 0.1, DOOR + 1, 0, DOORH + 1, FZ - 0.5, FZ + 0.3, C.gold)
	box(b, -DOOR + 0.1, DOOR - 0.1, DOORH - 0.1, DOORH + 1, FZ - 0.5, FZ + 0.3, C.gold)
	for _, sx in { -1, 1 } do
		glow(b, sx * 9.2 - 0.5, sx * 9.2 + 0.5, 4.0, 7.0, FZ - 0.8, FZ - 0.2, C.warm)
	end
	return b
end

-- ── Крыша: потолок с кессоном и световым фонарём, ступенчатая кровля ─────────────────────────────────────────
local function roof(): { Brick }
	local b: { Brick } = {}
	box(b, -HW, HW, TOP, TOP + 1, FZ, BZ, C.ceiling, SHELL)
	box(b, -IX, IX, CEIL + 0.4, TOP, IZ0, IZ1, C.ceiling, SHELL)
	glow(b, -5, 5, CEIL + 0.3, CEIL + 0.4, -10.5, 10.0, C.sky)
	for k, w in { 19.5, 16.0, 12.5, 9.0, 5.5, 2.0 } do
		local y = TOP + 1 + (k - 1) * 1.1
		box(b, -w, w, y, y + 1.1, FZ - 0.4, BZ + 0.6, C.roof)
	end
	box(b, -4.5, 4.5, TOP + 1 + 6 * 1.1, TOP + 1 + 6 * 1.1 + 1.4, -9.5, 9.0, C.glass, {
		material = Enum.Material.Glass,
		transparency = 0.35,
	})
	return b
end

-- ── Боковая стена зала (sx −1 / +1): глухая (уровни 1–4) или с аркой в галерею; пилястры, 4 ниши ───────────────
local function side(sx: number, arch: boolean): { Brick }
	local b: { Brick } = {}
	local x0, x1 = math.min(sx * IX, sx * HW), math.max(sx * IX, sx * HW)
	local A = GAL.Arch
	if arch then
		box(b, x0, x1, 0, TOP, FZ, A.Z0, C.wall, SHELL)
		box(b, x0, x1, 0, TOP, A.Z1, BZ, C.wall, SHELL)
		box(b, x0, x1, A.Height, TOP, A.Z0, A.Z1, C.wall, SHELL)
		-- золотая рама арки (стойки до верха проёма, перекладина над ними) и вывеска
		local ax0, ax1 = sideX(sx, 0, 0.25)
		box(b, ax0, ax1, 0, A.Height, A.Z0 - 0.5, A.Z0, C.gold)
		box(b, ax0, ax1, 0, A.Height, A.Z1, A.Z1 + 0.5, C.gold)
		box(b, ax0, ax1, A.Height, A.Height + 0.5, A.Z0 - 0.5, A.Z1 + 0.5, C.gold)
		local sx0, sx1 = sideX(sx, 0.25, 0.4)
		box(b, sx0, sx1, A.Height + 1.1, A.Height + 2.1, A.Z0, A.Z1, C.navyDark, { name = "ArchSign" })
	else
		box(b, x0, x1, 0, TOP, FZ, BZ, C.wall, SHELL)
		local r0, r1 = gx(sx, HW, HW + 1)
		box(b, r0, r1, G, -0.02, FZ, BZ, C.wall, SHELL) -- бортик подиума
	end
	local px0, px1 = sideX(sx, 0, 0.2)
	box(b, px0, px1, 0, 1, if arch then A.Z1 + 0.5 else IZ0, IZ1, C.navy) -- плинтус (у арки — от её рамы)
	box(b, px0, px1, 12.4, 12.7, IZ0, IZ1, C.gold) -- пояс
	local gl0, gl1 = sideX(sx, 0.2, 0.45)
	glow(b, gl0, gl1, 12.7, 12.9, IZ0 + 0.2, IZ1 - 0.2, C.warm)
	local cx0, cx1 = sideX(sx, 0, 0.5)
	box(b, cx0, cx1, 15.2, 16.0, IZ0, IZ1, C.pil) -- карниз
	for _, z in L.Niche.Pilasters do -- пилястры: ствол и капитель
		local s0, s1 = sideX(sx, 0, 1.3)
		box(b, s0, s1, 0, 11.6, z - 0.4, z + 0.4, C.pil)
		local c0, c1 = sideX(sx, 0, 1.55)
		box(b, c0, c1, 11.6, 12.4, z - 0.55, z + 0.55, C.gold)
	end
	for i, _ in L.Niche.Z do -- ниши: тёмный фон между пилястрами
		local z0 = L.Niche.Pilasters[i] + 0.45
		local z1 = if i < #L.Niche.Pilasters then L.Niche.Pilasters[i + 1] - 0.45 else IZ1 - 0.05
		local b0, b1 = sideX(sx, 0, 0.3)
		box(b, b0, b1, 1.0, 9.2, z0, z1, C.backdrop)
	end
	return b
end

-- ── Галерея (sx −1 / +1, с уровня Gallery.Level): оболочка, фасад, 6 ниш, клумба ───────────────────────────────
local function gallery(sx: number): { Brick }
	local b: { Brick } = {}
	local top = GAL.Height + 1
	local x0, x1 = gx(sx, GAL.In, GAL.Out)
	box(b, x0, x1, G, 0, GAL.Z0, GAL.Z1, C.floor, { shell = true, name = "Floor" })
	x0, x1 = gx(sx, GAL.InnerX, GAL.Out)
	box(b, x0, x1, 0, top, GAL.Z0, GAL.Z1, C.wall, SHELL) -- наружная стена
	x0, x1 = gx(sx, GAL.In, GAL.InnerX)
	box(b, x0, x1, 0, top, GAL.Z0, GAL.InnerZ0, C.wall, SHELL) -- фасад
	box(b, x0, x1, 0, top, GAL.InnerZ1, GAL.Z1, C.wall, SHELL) -- задняя
	x0, x1 = gx(sx, IX, GAL.In)
	box(b, x0, x1, 0, top, GAL.Z0, FZ, C.wall, SHELL) -- вдоль портика
	-- внутри: плинтус, пояс, тёмная дорожка
	x0, x1 = gx(sx, GAL.InnerX - 0.2, GAL.InnerX)
	box(b, x0, x1, 0, 1, GAL.InnerZ0, GAL.InnerZ1, C.navy)
	box(b, x0, x1, 9.6, 9.9, GAL.InnerZ0, GAL.InnerZ1, C.gold)
	x0, x1 = gx(sx, GAL.Walk - 1.45, GAL.Walk + 1.45) -- дорожка по середине прохода (D50)
	box(b, x0, x1, 0, 0.08, GAL.InnerZ0 + 0.6, GAL.InnerZ1 - 0.6, C.navy, { shadow = false })
	-- ниши у наружной стены: тёмный фон
	for _, z in GAL.Z do
		x0, x1 = gx(sx, GAL.InnerX - 0.3, GAL.InnerX)
		box(b, x0, x1, 1.0, 8.6, z - 2.75, z + 2.75, C.backdrop)
	end
	-- фасад к портику: фриз, две пилястры, глухая арка, аттик
	x0, x1 = gx(sx, GAL.In, GAL.Eave)
	box(b, x0, x1, GAL.Height - 0.2, GAL.Height + 0.6, GAL.Z0 - 0.3, GAL.Z0, C.gold)
	for _, px in { GAL.In + 0.8, GAL.Out - 0.8 } do
		x0, x1 = gx(sx, px - 0.7, px + 0.7)
		box(b, x0, x1, 0, GAL.Height - 0.2, GAL.Z0 - 0.4, GAL.Z0, C.pil)
	end
	local mid = (GAL.In + GAL.Out) / 2
	x0, x1 = gx(sx, mid - 2.6, mid + 2.6)
	box(b, x0, x1, 0, 7.8, GAL.Z0 - 0.35, GAL.Z0, C.gold)
	x0, x1 = gx(sx, mid - 2.1, mid + 2.1)
	box(b, x0, x1, 0.4, 7.3, GAL.Z0 - 0.45, GAL.Z0 - 0.3, C.backdrop)
	cylinder(b, Vector3.new(sx * mid, 5.4, GAL.Z0 - 0.5), 1.0, 0.12, "z", C.gold)
	-- снаружи вдоль наружной стены: 3 пилястры
	for _, z in { (GAL.Z[1] + GAL.Z[2]) / 2, (GAL.Z[4] + GAL.Z[5]) / 2, (GAL.Z[3] + GAL.Z[1]) / 2 } do
		x0, x1 = gx(sx, GAL.Out, GAL.Out + 0.35)
		box(b, x0, x1, G + 0.88, top - 0.4, z - 0.45, z + 0.45, C.pil)
	end
	-- клумба: каменный бортик (оболочка — у крайних участков закрывает щель до обрыва), земля, кусты; узкий бортик
	-- (D50: галерея шире, до кромки обрыва 0.6 ст.) — без земли и кустов
	local p0, p1, ph = GAL.Planter[1], GAL.Planter[2], GAL.Planter[3]
	x0, x1 = gx(sx, p0, p1)
	box(b, x0, x1, G, G + ph * 0.55, GAL.Z0, GAL.Z1, C.stone, SHELL)
	if p1 - p0 < GAL.PlanterBush then
		return b
	end
	x0, x1 = gx(sx, p0 + 0.25, p1 - 0.25)
	box(b, x0, x1, G + ph * 0.55, G + ph * 0.62, GAL.Z0 + 0.25, GAL.Z1 - 0.25, C.plantDark, { shadow = false })
	local y0 = G + ph * 0.62
	local k = 0
	local z = GAL.Z0 + 3.0
	while z < GAL.Z1 - 2 do
		x0, x1 = gx(sx, p0 + 0.3, p1 - 0.3)
		box(b, x0, x1, y0, y0 + 1.5, z - 1.4, z + 1.4, if k % 2 == 0 then C.plant else C.plantDark)
		z += 8.0
		k += 1
	end
	return b
end

local function galleryRoof(sx: number): { Brick }
	local b: { Brick } = {}
	local top = GAL.Height + 1
	local x0, x1 = gx(sx, GAL.In, GAL.Eave - 0.2)
	box(b, x0, x1, top, top + 0.8, GAL.Z0 - 0.4, GAL.Z1 + 0.4, C.pil, SHELL)
	x0, x1 = gx(sx, GAL.Walk - 1.5, GAL.Walk + 1.5)
	glow(b, x0, x1, top - 0.1, top, GAL.InnerZ0 + 1, GAL.InnerZ1 - 1, C.sky)
	x0, x1 = gx(sx, GAL.In + 0.4, GAL.Eave - 0.4)
	box(b, x0, x1, top + 0.8, top + 1.7, GAL.Z0 - 0.3, GAL.Z0 + 1.2, C.pil) -- аттик над фасадом
	return b
end

-- ── Постамент (кроме тумбы — её роль играет Showcase_n) и урна ─────────────────────────────────────────────────
local function plinth(): { Brick }
	local b: { Brick } = {}
	local hb = L.Showcase.Base / 2
	box(b, -hb, hb, 0, 0.5, -hb, hb, C.navy)
	return b
end

local function urn(): { Brick }
	local b: { Brick } = {}
	box(b, -1.6, 1.6, 0, 1.2, -1.6, 1.6, C.navy, SHELL)
	cylinder(b, Vector3.new(0, 1.45, 0), 0.6, 0.5, "y", C.gold)
	table.insert(
		b,
		ModelBuilder.Brick(Vector3.new(2.6, 2.5, 2.6), Vector3.new(0, 2.9, 0), C.gold, {
			name = "Detail",
			shape = "Ball",
			collide = false,
			variant = SOFT,
		})
	)
	cylinder(b, Vector3.new(0, 4.3, 0), 0.55, 0.8, "y", C.gold)
	return b
end

-- ── Павильон хранилища: портал с решёткой, стены, крыша, круглая сейфовая дверь (открыта) ───────────────────────
local function pavilion(): { Brick }
	local b: { Brick } = {}
	box(b, -PV_X, -STW, 0, PV_H, PV_Z0, PV_Z0 + 0.6, C.steel, SHELL)
	box(b, STW, PV_X, 0, PV_H, PV_Z0, PV_Z0 + 0.6, C.steel, SHELL)
	box(b, -STW, STW, 7.2, PV_H, PV_Z0, PV_Z0 + 0.6, C.steel, SHELL)
	box(b, -PV_X, -PV_X + 0.6, 0, PV_H, PV_Z0 + 0.6, PV_Z1 - 0.6, C.steel, SHELL)
	box(b, PV_X - 0.6, PV_X, 0, PV_H, PV_Z0 + 0.6, PV_Z1 - 0.6, C.steel, SHELL)
	box(b, -PV_X, PV_X, 0, PV_H, PV_Z1 - 0.6, PV_Z1, C.steel, SHELL)
	box(b, -PV_X - 0.4, PV_X + 0.4, PV_H, PV_H + 0.6, PV_Z0 - 0.4, PV_Z1 + 0.4, C.pil, SHELL)
	box(b, -PV_X - 0.6, PV_X + 0.6, PV_H + 0.6, PV_H + 0.9, PV_Z0 - 0.6, PV_Z1 + 0.6, C.gold)
	box(b, -3.4, 3.4, PV_H + 0.9, PV_H + 1.7, PV_Z0 + 0.6, PV_Z1 - 0.6, C.navy)
	-- золотая рама портала (стойки и перекладина встык), бирюзовые полосы, табло
	box(b, -STW - 0.3, -STW + 0.05, 0, 7.1, PV_Z0 - 0.15, PV_Z0 + 0.1, C.gold)
	box(b, STW - 0.05, STW + 0.3, 0, 7.1, PV_Z0 - 0.15, PV_Z0 + 0.1, C.gold)
	box(b, -STW - 0.3, STW + 0.3, 7.1, 7.5, PV_Z0 - 0.15, PV_Z0 + 0.1, C.gold) -- ниже перемычки на 0.1
	for _, sx in { -1, 1 } do
		glow(b, sx * 3.3 - 0.1, sx * 3.3 + 0.1, 0.5, 6.8, PV_Z0 - 0.1, PV_Z0, C.cyan)
	end
	box(b, -3.3, 3.3, 7.75, 8.75, PV_Z0 - 0.15, PV_Z0, C.navyDark, { name = "VaultSign" })
	-- круглая дверь сейфа, распахнута на 90° (как в утверждённом v2): диск — оболочка, кольцо и штурвал — вид
	local dr = 3.5
	local dcx, dcz, dcy = PV_X + 0.45, PV_Z0 - dr - 0.1, 0.35 + dr
	cylinder(b, Vector3.new(dcx - 0.1, dcy, dcz), dr - 0.2, 0.6, "x", C.disk, SHELL)
	cylinder(b, Vector3.new(dcx + 0.3, dcy, dcz), dr + 0.3, 0.3, "x", C.gold)
	cylinder(b, Vector3.new(dcx - 0.55, dcy, dcz), 1.3, 0.3, "x", C.gold)
	cylinder(b, Vector3.new(dcx - 0.8, dcy, dcz), 0.5, 0.3, "x", C.steelDark)
	return b
end

-- Створка решётки: начало — нижний внутренний угол у середины проёма, створка — к +x; вторая повёрнута на 180°.
local function gateLeaf(): { Brick }
	local b: { Brick } = {}
	local w, h = STW - 0.05, 7.1
	box(b, 0, 0.25, 0, h, -0.1, 0.1, C.steelDark, { name = "Gate" })
	box(b, w - 0.25, w, 0, h, -0.1, 0.1, C.steelDark, { name = "Gate" })
	box(b, 0.25, w - 0.25, 0, 0.3, -0.1, 0.1, C.steelDark, { name = "Gate" })
	box(b, 0.25, w - 0.25, h - 0.3, h, -0.1, 0.1, C.steelDark, { name = "Gate" })
	for k = 1, 3 do
		local x = 0.25 + k * (w - 0.5) / 4
		cylinder(b, Vector3.new(x, h / 2, 0), 0.07, h - 0.6, "y", C.gold, { name = "Gate" })
	end
	return b
end

local function scanner(): { Brick }
	local b: { Brick } = {}
	box(b, -0.5, 0.5, 0, 1.4, -0.12, 0.12, C.navyDark)
	box(
		b,
		-0.35,
		0.35,
		0.5,
		1.2,
		-0.16,
		-0.12,
		C.cyan,
		{ material = Enum.Material.Neon, shadow = false, name = "Screen" }
	)
	return b
end

-- ── Лестница: 12 ступеней-столбов до пола хранилища, стеклянные перила (оболочка) и золотые поручни ─────────────
local function stair(): { Brick }
	local b: { Brick } = {}
	for k = 1, L.Stair.Steps do
		box(b, -STW, STW, VF, -k, ST0 + k - 1, ST0 + k, C.step, { shell = true, name = "Step" })
	end
	-- перила спускаются вместе со ступенями (к +z; D50: были наклонены обратно и выходили над полом зала за
	-- проёмом). Ось — на RAIL выше линии середин ступеней, от START за решёткой (z ≥ ST0) до середины нижней ступени.
	local RAIL, START = 1.2, 0.6
	local tilt = CFrame.Angles(math.rad(45), 0, 0)
	local z0, z1 = ST0 + START, ST0 + L.Stair.Steps - 0.5
	local length = (z1 - z0) * math.sqrt(2)
	local midZ = (z0 + z1) / 2
	local midY = -(midZ - ST0 + 0.5) + RAIL
	for _, sx in { -1, 1 } do
		-- стекло 2.62…2.74 (ступени до 2.6), поручень 2.58…2.78 — внутри проёма пола (2.8), граней встык нет
		local x = sx * (STW + 0.08)
		table.insert(
			b,
			ModelBuilder.Brick(Vector3.new(0.12, 2.1, length), CFrame.new(x, midY, midZ) * tilt, C.glass, {
				name = "Rail",
				collide = true,
				shell = true,
				material = Enum.Material.Glass,
				transparency = 0.35,
			})
		)
		table.insert(
			b,
			ModelBuilder.Brick(Vector3.new(0.2, 0.25, length), CFrame.new(x, midY + 1.15, midZ) * tilt, C.gold, {
				name = "Detail",
				collide = false,
				variant = SOFT,
			})
		)
	end
	return b
end

-- ── Сундук (корпус — сама деталь Chest, здесь крышка и окантовка) и стенд у входа ─────────────────────────────
local function chest(): { Brick }
	local b: { Brick } = {}
	box(b, -2.1, 2.1, 1.9, 2.5, -1.6, 1.6, C.chestLight)
	cylinder(b, Vector3.new(0, 2.5, 0), 1.25, 3.7, "x", C.chest)
	for _, x in { -1.2, 1.2 } do
		box(b, x - 0.18, x + 0.18, 0, 2.6, -1.75, 1.75, C.gold)
	end
	box(b, -0.45, 0.45, 1.2, 2.2, 1.5, 1.8, C.gold)
	glow(b, -1.0, 1.0, 2.3, 2.4, 1.6, 1.68, C.cyan)
	return b
end

local function stand(): { Brick }
	local b: { Brick } = {}
	box(b, -0.9, 0.9, 0, 0.6, -0.7, 0.7, C.navy, SHELL)
	cylinder(b, Vector3.new(0, 1.8, 0), 0.3, 2.4, "y", C.gold)
	local tilt = CFrame.Angles(math.rad(20), 0, 0) -- экран смотрит ко входу (−z) и чуть вверх
	table.insert(
		b,
		ModelBuilder.Brick(Vector3.new(3.2, 2.0, 0.25), CFrame.new(0, 3.8, 0) * tilt, C.navyDark, {
			name = "StandBoard",
			collide = false,
			material = Enum.Material.SmoothPlastic, -- табличка с текстом
		})
	)
	return b
end

-- ── Хранилище: оболочка (пол, стены, потолок вокруг проёма) и обстановка ───────────────────────────────────────
local function vaultShell(): { Brick }
	local b: { Brick } = {}
	box(b, -HW, HW, VF - 1.4, VF, FZ, BZ, C.vFloor, { shell = true, name = "Floor" })
	box(b, -HW, -IX, VF, -SLAB, FZ, BZ, C.vWall, SHELL)
	box(b, IX, HW, VF, -SLAB, FZ, BZ, C.vWall, SHELL)
	box(b, -IX, IX, VF, -SLAB, FZ, IZ0, C.vWall, SHELL)
	box(b, -IX, IX, VF, -SLAB, IZ1, BZ, C.vWall, SHELL)
	for _, r in { { -IX, IX, IZ0, ST0 }, { -IX, -WX, ST0, IZ1 }, { WX, IX, ST0, IZ1 }, { -WX, WX, WZ1, IZ1 } } do
		box(b, r[1], r[2], VCEIL, -SLAB, r[3], r[4], C.vCeil, SHELL)
	end
	-- вид (только владельцу): золотой цоколь, бирюзовые линии света, эмблема
	box(b, -IX, -IX + 0.25, VF, VF + 0.5, IZ0 + 0.25, IZ1, C.gold)
	box(b, IX - 0.25, IX, VF, VF + 0.5, IZ0 + 0.25, IZ1, C.gold)
	box(b, -IX, IX, VF, VF + 0.5, IZ0, IZ0 + 0.25, C.gold)
	for _, x in { -10.0, 10.0 } do
		glow(b, x - 0.15, x + 0.15, VCEIL - 0.12, VCEIL, IZ0 + 0.5, IZ1 - 0.5, C.cyan)
	end
	cylinder(b, Vector3.new(0, VF + 7.8, IZ0 + 0.3), 1.8, 0.3, "z", C.gold)
	cylinder(b, Vector3.new(0, VF + 7.8, IZ0 + 0.5), 1.3, 0.2, "z", C.navy)
	return b
end

local function safe(): { Brick } -- начало — центр двери на задней стене (z = 0 — грань стены), дверь — к −z
	local b: { Brick } = {}
	box(b, -5.2, 5.2, -5.0, 5.2, -0.4, 0, C.navyDark)
	cylinder(b, Vector3.new(0, 0, -0.6), 3.95, 0.4, "z", C.gold)
	cylinder(b, Vector3.new(0, 0, -1.1), 3.6, 0.6, "z", C.disk)
	cylinder(b, Vector3.new(0, 0, -1.55), 1.3, 0.3, "z", C.gold)
	for _, sx in { -1, 1 } do
		glow(b, sx * 5.6 - 0.2, sx * 5.6 + 0.2, -5.0, 4.6, -0.3, 0, C.warm)
	end
	return b
end

local function terminal(): { Brick } -- начало — у торца лестницы на полу хранилища, экран смотрит в −z
	local b: { Brick } = {}
	box(b, -2.2, 2.2, 0, 2.5, -2.4, -1.0, C.navy, SHELL)
	box(b, -2.45, 2.45, 3.6, 9.6, -0.3, 0, C.navyDark)
	glow(b, -2.15, 2.15, 3.9, 9.3, -0.36, -0.3, C.screen)
	return b
end

local function security(): { Brick } -- начало — центр хранилища на полу; стол и экраны у правой стены
	local b: { Brick } = {}
	box(b, 13.4, 15.6, 0, 2.35, -7.8, -0.2, C.navyDark, SHELL)
	box(b, 12.8, 15.7, 2.35, 2.75, -8.0, 0.0, C.navy)
	for _, mz in { -6.2, -4.0, -1.8 } do
		box(b, 13.6, 13.9, 3.2, 5.2, mz - 1.0, mz + 1.0, C.navyDark)
		glow(b, 13.5, 13.6, 3.35, 5.05, mz - 0.85, mz + 0.85, C.screen)
	end
	box(b, IX - 0.3, IX, 5.4, 10.2, -9.0, 1.0, C.navyDark)
	glow(b, IX - 0.36, IX - 0.3, 5.7, 9.9, -8.7, 0.7, C.screen)
	return b
end

local function archive(): { Brick } -- начало — у стены на полу, полки смотрят в +x
	local b: { Brick } = {}
	box(b, 0, 2.35, 0, 8.6, -3.4, 3.4, C.steelDark, { shell = true, invisible = true, name = "Shell" })
	box(b, 0, 0.3, 0, 8.6, -3.1, 3.1, C.steelDark)
	for _, zz in { -3.4, 3.1 } do
		box(b, 0, 2.35, 0, 8.6, zz, zz + 0.3, C.gold)
	end
	for lvl = 0, 2 do
		local y = 0.6 + lvl * 2.75
		box(b, 0.3, 2.35, y - 0.2, y, -3.1, 3.1, C.steelLight)
	end
	return b
end

local function lockers(): { Brick } -- начало — левый нижний угол у стены, дверцы смотрят в +z
	local b: { Brick } = {}
	box(b, 0, 7.9, 0, 6.5, 0, 0.35, C.gold, SHELL)
	for row = 0, 1 do
		local y = 0.35 + row * 3.05
		box(b, 0.2, 7.7, y, y + 2.85, 0.35, 0.6, if row == 0 then C.locker else C.vPanel)
	end
	return b
end

local BUILDERS: { [string]: () -> { Brick } } = {
	D48_Hall = hall,
	D48_Roof = roof,
	D48_SideClosed_L = function()
		return side(-1, false)
	end,
	D48_SideClosed_R = function()
		return side(1, false)
	end,
	D48_SideArch_L = function()
		return side(-1, true)
	end,
	D48_SideArch_R = function()
		return side(1, true)
	end,
	D48_Gallery_L = function()
		return gallery(-1)
	end,
	D48_Gallery_R = function()
		return gallery(1)
	end,
	D48_GalleryRoof_L = function()
		return galleryRoof(-1)
	end,
	D48_GalleryRoof_R = function()
		return galleryRoof(1)
	end,
	D48_Plinth = plinth,
	D48_Urn = urn,
	D48_Pavilion = pavilion,
	D48_GateLeaf = gateLeaf,
	D48_Scanner = scanner,
	D48_Stair = stair,
	D48_Chest = chest,
	D48_Stand = stand,
	D48_VaultShell = vaultShell,
	D48_Safe = safe,
	D48_Terminal = terminal,
	D48_Security = security,
	D48_Archive = archive,
	D48_Lockers = lockers,
}

-- Кирпичи модуля name в его осях (как у модуля Blender). nil — такого модуля нет.
function MuseumD48.Module(name: string): { Brick }?
	local build = BUILDERS[name]
	return if build then build() else nil
end

function MuseumD48.Has(name: string): boolean
	return BUILDERS[name] ~= nil
end

return MuseumD48

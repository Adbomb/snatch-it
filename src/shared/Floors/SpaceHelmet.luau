--!strict
-- Этаж «Гигантский космический шлем»: исследовательский корабль из мешей по эталону GoldenThrone v6 и TRexSkeleton v1
-- (утверждены владельцем 2026-11-21): крупные блоки, крупные квадраты по одному на стад (LegoSquaresFar / Quiet).
-- Замысел (просьба владельца 2026-11-21: «космическая станция или исследовательский корабль, не белая комната с
-- неоновыми полосками; шлем сразу привлекает внимание; глубокие сине-серые тона, яркие чистые акценты»): снаружи —
-- корпус панелями, белые угловые колонны с оранжевыми поясами, спереди огромный золотой визор в белой раме с
-- фонарями шлема, по бокам солнечные батареи, двигательные гондолы и радар, сзади три сопла. Внутри — отсек со
-- скошенными углами, шпангоутами, иллюминаторами, пультами и шлюзом у лифта; шлем — на восьмигранном подиуме со
-- светящимися кольцами между пилонами-излучателями, над ним парящее кольцо с прожектором, за ним — окно в космос.
-- Геометрия — scripts/blender/floor_space.py → assets/models/floors/SpaceHelmetFloor.fbx; меши и их центры —
-- Floors/FloorMeshes (scripts/floor_bind_meshes.py). Цвета, тени и яркость сторон — в цветах вершин; Color детали —
-- общий множитель яркости. Огни, экраны и окна в космос (*_Glass) — без затенения, светятся сами.
--   shell — каркас сервера (плита, стены, подиум, пилоны, пульты, стойки, стойки шпангоутов), exhibit — шлем на
--   подиуме визором к лифту (масштаб показа 2.8), decor — убранство клиента: interior / facade / silhouette;
--   soloLights — пока камера на этом этаже, лампы остальных этажей погашены (TowerController).
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/Kit, Floors/FloorMeshes.

local FloorMeshes = require(script.Parent.FloorMeshes)
local Kit = require(script.Parent.Kit)

local B = Kit.B

local Theme = {}

Theme.Name = "SpaceHelmet"
Theme.soloLights = true

local MESHES = FloorMeshes.SpaceHelmet.parts
local FAR = "LegoSquaresFar" -- обшивка, рамы, колонны: крупные квадраты по одному на стад (Config/Textures.SquaresFar)
local QUIET = "LegoSquaresQuiet" -- палуба: квадраты едва заметны (Config/Textures.SquaresQuiet)
local PROPS = "LegoRingsD39Boss" -- вещи этажа — кольца D39 в масштабе боссов (Config/Textures.RingsD39Boss)

-- множитель яркости деталей (цвета — в вершинах меша), подобран в Studio в фазе «День»
local TONE_IN = Color3.fromHex("FFFFFF")
local TONE_OUT = Color3.fromHex("E2E2E2")
local TONE_GLOW_IN = Color3.fromHex("C8C8C8") -- огни зала приглушены: без пересвета, шлем — самое светлое
local POCHE = Color3.fromHex("222C42") -- стены каркаса в убранстве (скрыты между обшивками, упор камеры)
local COOL = Color3.fromHex("DCE6FF")
local WHITE = Color3.fromHex("F4F8FF")
local CYAN = Color3.fromHex("56D6FF")

local LOOK: { [string]: { material: Enum.Material, variant: string? } } = {
	SH_F_Rings = { material = Enum.Material.Plastic, variant = FAR },
	SH_F_Quiet = { material = Enum.Material.Plastic, variant = QUIET },
	SH_F_Smooth = { material = Enum.Material.SmoothPlastic },
	SH_F_Props = { material = Enum.Material.Plastic, variant = PROPS },
	SH_F_Glass = { material = Enum.Material.SmoothPlastic }, -- огни, линзы, свечение сопел
	SH_I_Rings = { material = Enum.Material.Plastic, variant = FAR },
	SH_I_Quiet = { material = Enum.Material.Plastic, variant = QUIET },
	SH_I_Smooth = { material = Enum.Material.SmoothPlastic },
	SH_I_Props = { material = Enum.Material.Plastic, variant = PROPS },
	SH_I_Glass = { material = Enum.Material.SmoothPlastic }, -- окно в космос, экраны, кольца света
	SH_S_All = { material = Enum.Material.SmoothPlastic },
}

-- зал (как в scripts/blender/floor_space.py)
local DAIS = { x = 0, z = -4, low = 0.8, top = 2.15 } -- подиум: центр, верх нижней ступени, верх излучателя
local PYLONS = { 0, 180, 240, 300 } -- пилоны: углы вокруг подиума (к лифту, +z, пилонов нет)
local CONSOLES = { 3, -7.5 } -- пульты у боковых стен (z)
local FRAMES = { 8.5, -1.5 } -- силовые шпангоуты (z)

local function meshes(tier: string): { any }
	local list: { any } = {}
	local names = {}
	for name, info in MESHES do
		if info.tier == tier then
			table.insert(names, name)
		end
	end
	table.sort(names)
	for _, name in names do
		local info, look = MESHES[name], LOOK[name]
		table.insert(list, {
			mesh = name,
			name = name,
			size = info.size,
			cframe = CFrame.new(info.center),
			color = if name == "SH_I_Glass" then TONE_GLOW_IN elseif tier == "interior" then TONE_IN else TONE_OUT,
			material = look.material,
			variant = look.variant,
		})
	end
	return list
end

-- Брусок каркаса по границам x0…x1, y0…y1, z0…z1.
local function block(x0: number, x1: number, y0: number, y1: number, z0: number, z1: number, name: string): any
	return B(
		Vector3.new(math.abs(x1 - x0), y1 - y0, math.abs(z1 - z0)),
		Vector3.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
		Color3.new(0, 0, 0),
		{ name = name }
	)
end

function Theme.shell(cfg: any): { any }
	local shell = Kit.Shell(cfg)
	local d = DAIS
	table.insert(shell, block(d.x - 5.4, d.x + 5.4, 0, d.low, d.z - 5.4, d.z + 5.4, "Dais1"))
	table.insert(shell, block(d.x - 4, d.x + 4, d.low, d.top, d.z - 4, d.z + 4, "Dais2"))
	for i, deg in PYLONS do
		local a = math.rad(deg)
		local x, z = d.x + 5.9 * math.cos(a), d.z + 5.9 * math.sin(a)
		table.insert(shell, block(x - 0.6, x + 0.6, 0.5, 4.8, z - 0.6, z + 0.6, "Pylon" .. i))
	end
	local wall = cfg.Half.X - cfg.Wall
	for _, s in { -1, 1 } do
		local side = if s < 0 then "L" else "R"
		for i, z in CONSOLES do
			table.insert(shell, block(s * 14.48, s * wall, 0, 2.4, z - 2, z + 2, "Console" .. i .. side))
		end
		table.insert(shell, block(s * 14.68, s * wall, 0, 9, -13, -10, "Rack" .. side))
		for i, z in FRAMES do
			table.insert(shell, block(s * 14.95, s * 16.25, 0, 12.6, z - 0.7, z + 0.7, "Frame" .. i .. side))
		end
	end
	return shell
end

function Theme.exhibit(_cfg: any): { at: Vector3, yaw: number, scale: number }
	return { at = Vector3.new(DAIS.x, DAIS.top, DAIS.z), yaw = 180, scale = 2.8 }
end

-- Невидимый держатель света (свет этажа — часть интерьера).
local function lamp(list: { any }, at: Vector3, light: any)
	table.insert(
		list,
		B(Vector3.new(0.2, 0.2, 0.2), at, Color3.new(1, 1, 1), {
			material = Enum.Material.SmoothPlastic,
			transparency = 1,
			light = light,
			name = "Light",
		})
	)
end

local function interior(_cfg: any): { any }
	local list = meshes("interior")
	-- Свет и тени отсека запечены в цвета вершин; лампа зала — холодная, под потолком между шлюзом и подиумом;
	-- прожектор — в парящем кольце над шлемом, мягкий свет спереди (шлем светлее всего в отсеке), слабый голубой
	-- отсвет колец подиума.
	lamp(list, Vector3.new(0, 15.0, 5.0), { range = 40, brightness = 0.65, color = COOL })
	lamp(list, Vector3.new(DAIS.x, 13.2, DAIS.z), { range = 16, brightness = 2.4, color = WHITE, spot = 50 })
	-- мягкий белый свет спереди: визор и лицевая сторона шлема — со стороны лифта (без него шлем в тени, Studio)
	lamp(list, Vector3.new(DAIS.x, 7.5, DAIS.z + 6.5), { range = 9, brightness = 1.0, color = WHITE })
	lamp(list, Vector3.new(DAIS.x, 2.6, DAIS.z + 4.5), { range = 6, brightness = 0.3, color = CYAN })
	return list
end

local function facade(cfg: any): { any }
	local list = meshes("facade")
	-- стены каркаса: скрыты между обшивками зала и фасада, у клиента в них упирается камера
	for _, side in { "Front", "Left", "Right" } do
		Kit.Wall(list, cfg, side, {}, POCHE)
	end
	-- в задней стене — ниша дверей лифта: створки (меш интерьера) утоплены, за ними заглушка
	local door = Kit.DoorOpening()
	Kit.Wall(list, cfg, "Back", { door }, POCHE)
	table.insert(
		list,
		Kit.Slice("Back", cfg, door[1], door[2], door[3], door[4], 0.6, cfg.Wall, POCHE, { occlude = true })
	)
	return list
end

function Theme.decor(cfg: any, _ctx: any, tier: string): { any }
	if tier == "interior" then
		return interior(cfg)
	elseif tier == "facade" then
		return facade(cfg)
	elseif tier == "silhouette" then
		return meshes("silhouette")
	end
	return {}
end

return Theme

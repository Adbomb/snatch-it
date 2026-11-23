--!strict
-- Этаж «Скелет тираннозавра»: доисторическая экспозиция из мешей по эталону GoldenThrone v6 (утверждён владельцем
-- 2026-11-21): крупные блоки по сетке в стад, крупные квадраты по одному на стад (LegoSquaresFar / LegoSquaresQuiet).
-- Замысел (просьба владельца 2026-11-21: «впечатляющий доисторический мир, этаж — достопримечательность; скелет —
-- главный экспонат; фасад узнаётся издалека»): снаружи — обрыв из слоёв породы с уступами и поясом папоротников,
-- спереди из скалы выступает огромный череп тираннозавра в профиле (открытая пасть, глаз-янтарь), по бокам —
-- позвоночник по верху и рёбра по обрыву, сзади — хвост; в слоях — янтарь и аммониты. Внутри — зал-раскоп: стены
-- слоями, крепь шахты у лифта, две арки гигантских рёбер, лампы; скелет на скальном постаменте в профиль к лифту,
-- за ним — диорама с вулканом на закате (тёмный вулкан — фон для светлых костей); настил, следы, сетка раскопа.
-- Геометрия — scripts/blender/floor_trex.py → assets/models/floors/TRexSkeletonFloor.fbx; меши и их центры —
-- Floors/FloorMeshes (scripts/floor_bind_meshes.py). Цвета, тени и яркость сторон — в цветах вершин; Color детали —
-- общий множитель яркости. Небо, лава, янтарь и лампы (*_Glass) — без затенения, светятся сами.
--   shell — каркас сервера (плита, стены, постамент, уступы, опоры арок, ящики), exhibit — скелет на постаменте в
--   профиль к лифту (масштаб показа 3.4), decor — убранство клиента: interior / facade / silhouette; soloLights — пока
--   камера на этом этаже, лампы остальных этажей погашены (TowerController).
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/Kit, Floors/FloorMeshes.

local FloorMeshes = require(script.Parent.FloorMeshes)
local Kit = require(script.Parent.Kit)

local B = Kit.B

local Theme = {}

Theme.Name = "TRexSkeleton"
Theme.soloLights = true

local MESHES = FloorMeshes.TRexSkeleton.parts
local FAR = "LegoSquaresFar" -- порода и кость: крупные квадраты по одному на стад, мягкие (Config/Textures.SquaresFar)
local QUIET = "LegoSquaresQuiet" -- песок, земля, трава: квадраты едва заметны (Config/Textures.SquaresQuiet)
local PROPS = "LegoRingsD39Boss" -- вещи этажа — кольца D39 в масштабе боссов (Config/Textures.RingsD39Boss)

-- множитель яркости деталей (цвета — в вершинах меша), подобран в Studio в фазе «День»
local TONE_IN = Color3.fromHex("FFFFFF")
local TONE_OUT = Color3.fromHex("E2E2E2")
local TONE_SKY = Color3.fromHex("B4B4B4") -- небо и лава диорамы приглушены: светлее всего в зале — скелет (Studio)
local POCHE = Color3.fromHex("3A3430") -- стены каркаса в убранстве (скрыты между обшивками, упор камеры)
local WARM = Color3.fromHex("F4F4FF") -- лампа зала: нейтральная — кости не желтеют (тёплый тон даёт постобработка карты)
local LAVA = Color3.fromHex("FF9A50")
local SPOTLIGHT = Color3.fromHex("E8F0FF") -- прожектор чуть холоднее белого: уравновешивает тёплую постобработку карты -- прожектор над скелетом — почти белый: кости светлее тёплого зала

local LOOK: { [string]: { material: Enum.Material, variant: string? } } = {
	TR_F_Rings = { material = Enum.Material.Plastic, variant = FAR },
	TR_F_Quiet = { material = Enum.Material.Plastic, variant = QUIET },
	TR_F_Smooth = { material = Enum.Material.SmoothPlastic },
	TR_F_Props = { material = Enum.Material.Plastic, variant = PROPS },
	TR_F_Glass = { material = Enum.Material.SmoothPlastic }, -- янтарь, лампы: цвет в вершинах, без затенения
	TR_I_Rings = { material = Enum.Material.Plastic, variant = FAR },
	TR_I_Quiet = { material = Enum.Material.Plastic, variant = QUIET },
	TR_I_Smooth = { material = Enum.Material.SmoothPlastic },
	TR_I_Props = { material = Enum.Material.Plastic, variant = PROPS },
	TR_I_Glass = { material = Enum.Material.SmoothPlastic }, -- небо и лава диорамы, янтарь, лампы
	TR_S_All = { material = Enum.Material.SmoothPlastic },
}

-- зал (как в scripts/blender/floor_trex.py)
local PLINTH = { { 9, -11, -1, 1.2 }, { 7.5, -10, -2, 2.2 } } -- постамент: полуширина, z0, z1, верх
local TERRACE = { x = 12.5, z0 = -14, z1 = 8, top = 2 } -- уступы у боковых стен
local ARCH_FEET = { { z = 9, y0 = 0 }, { z = 0, y0 = 1 } } -- опоры арок рёбер (у второй низ утоплен в уступ)
local CRATE = { x = 9, z = 13.2, w = 1.1, d = 0.9, height = 1.6 } -- ящики с находками у лифта
local SKELETON = Vector3.new(0, 2.2, -6) -- центр верха постамента

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
			color = if name == "TR_I_Glass" then TONE_SKY elseif tier == "interior" then TONE_IN else TONE_OUT,
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
	local base = 0
	for i, p in PLINTH do
		table.insert(shell, block(-p[1], p[1], base, p[4], p[2], p[3], "Plinth" .. i))
		base = p[4]
	end
	local wall = cfg.Half.X - cfg.Wall
	for _, s in { -1, 1 } do
		local side = if s < 0 then "L" else "R"
		local t = TERRACE
		table.insert(shell, block(s * t.x, s * wall, 0, t.top, t.z0, t.z1, "Terrace" .. side))
		for i, f in ARCH_FEET do
			table.insert(shell, block(s * 13.4, s * 15.4, f.y0, 6, f.z - 0.8, f.z + 0.8, "ArchFoot" .. i .. side))
		end
		local c = CRATE
		table.insert(shell, block(s * c.x - c.w, s * c.x + c.w, 0, c.height, c.z - c.d, c.z + c.d, "Crate" .. side))
	end
	return shell
end

function Theme.exhibit(_cfg: any): { at: Vector3, yaw: number, scale: number }
	return { at = SKELETON, yaw = 180, scale = 3.4 }
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
	-- Свет и тени зала запечены в цвета вершин; лампа зала — под сводом между лифтом и постаментом, прожектор над
	-- скелетом (он — самое светлое в зале), тёплый отсвет вулкана из диорамы ложится на кости сзади.
	lamp(list, Vector3.new(0, 15.0, 4.0), { range = 40, brightness = 0.6, color = WARM })
	lamp(list, Vector3.new(0, 14.5, -5.0), { range = 18, brightness = 2.6, color = SPOTLIGHT, spot = 55 })
	lamp(list, Vector3.new(0, 7.0, -13.5), { range = 6, brightness = 0.3, color = LAVA })
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

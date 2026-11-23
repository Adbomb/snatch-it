--!strict
-- Этаж «Золотой трон» (эталон этажей): королевский тронный зал из мешей в принятом владельцем стиле (крупные
-- вдавленные квадраты по одному на стад, LegoSquaresBold / LegoSquaresFar / LegoSquaresQuiet, 2026-11-20). Замысел
-- (просьба владельца 2026-11-20: «этаж — не только кресло, кресло красивое и выделяется на фоне роскошного
-- королевского этажа»): трон — единственная целиком золотая вещь, вокруг — синий бархат, светлый мрамор и тонкое
-- золото. Снаружи — дворец: мрамор, золотые пояса и пилястры, синий фриз, витражи, балкон с короной, знамёна.
-- Внутри — колоннада со знамёнами, витражи, кессонный потолок, люстра, красная дорожка к мраморному помосту; за
-- троном — балдахин: тёмная бархатная ниша с золотым ореолом, занавеси и полог с короной; над троном — прожектор.
-- Геометрия — scripts/blender/floor_golden_throne.py → assets/models/floors/GoldenThroneFloor.fbx; меши и их
-- центры — Floors/FloorMeshes (scripts/floor_bind_meshes.py). Цвета, тени и своя яркость у каждой стороны блока
-- запечены в цвета вершин (лампы игры без теней); Color детали — общий множитель яркости. Витражи и огоньки
-- (*_Glass) — без затенения, светятся сами.
--   shell — каркас сервера (плита, стены, помост, колонны, стены ниши, канделябры, сундуки),
--   exhibit — трон на верхней ступени помоста лицом к лифту (масштаб показа 2.8), decor — убранство клиента:
--   interior / facade / silhouette; soloLights — пока камера на этом этаже, лампы остальных этажей башни погашены
--   (TowerController): они без теней и светят сквозь перекрытия.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/Kit, Floors/FloorMeshes.

local FloorMeshes = require(script.Parent.FloorMeshes)
local Kit = require(script.Parent.Kit)

local B = Kit.B

local Theme = {}

Theme.soloLights = true

local MESHES = FloorMeshes.GoldenThrone.parts
local FAR = "LegoSquaresFar" -- мрамор и золото: крупные квадраты по одному на стад, мягкие (Config/Textures.SquaresFar)
local QUIET = "LegoSquaresQuiet" -- ткань (бархат, ковёр, потолок): квадраты едва заметны (Config/Textures.SquaresQuiet)
local PROPS = "LegoRingsD39Boss" -- вещи этажа — кольца D39 в масштабе боссов (Config/Textures.RingsD39Boss)

-- множитель яркости деталей (цвета — в вершинах меша), подобран в Studio в фазе «День»
local TONE_IN = Color3.fromHex("FFFFFF") -- зал: яркость задаёт запечённое затенение, множитель не нужен
local TONE_OUT = Color3.fromHex("D8D8D8") -- фасад и силуэт: на солнце без множителя золото упирается в предел яркости
local POCHE = Color3.fromHex("C9921A") -- стены каркаса в убранстве (скрыты между обшивками, упор камеры)
local WARM = Color3.fromHex("FFF1D6")
local LAMP = 0.55 -- яркость лампы зала: зал чуть темнее трона
local SPOT = 1.2 -- прожектор над троном: трон — самое светлое место зала

local LOOK: { [string]: { material: Enum.Material, variant: string? } } = {
	GT_F_Rings = { material = Enum.Material.Plastic, variant = FAR },
	GT_F_Quiet = { material = Enum.Material.Plastic, variant = QUIET },
	GT_F_Smooth = { material = Enum.Material.SmoothPlastic },
	GT_F_Props = { material = Enum.Material.Plastic, variant = PROPS },
	GT_F_Glass = { material = Enum.Material.SmoothPlastic }, -- витражи: цвет в вершинах, без затенения
	-- мрамор и золото зала — на мягком варианте: на белом мраморе чередование оттенков Bold пестрит (проверено в Studio)
	GT_I_Rings = { material = Enum.Material.Plastic, variant = FAR },
	GT_I_Quiet = { material = Enum.Material.Plastic, variant = QUIET },
	GT_I_Smooth = { material = Enum.Material.SmoothPlastic },
	GT_I_Props = { material = Enum.Material.Plastic, variant = PROPS },
	GT_I_Glass = { material = Enum.Material.SmoothPlastic }, -- витражи и огоньки свечей
	GT_S_All = { material = Enum.Material.SmoothPlastic },
}

-- зал (как в scripts/blender/floor_golden_throne.py)
local TIERS = { { 10, -15, 4 }, { 8, -15, 3 }, { 6, -15, 2 } } -- ступени помоста: полуширина, z0, z1
local BACK = -9 -- задняя стена зала; в ней ниша балдахина
local NICHE = { half = 7, back = -15 } -- ниша балдахина: полуширина, задняя стенка
local COLUMN = { x = 12, half = 1, z = { 11, 5, -1 } } -- колонны: ось, полуширина ствола, места
local CANDLE = { x = 8.6, z = 1, y = 1, height = 6.5 } -- канделябры на первой ступени
local CHEST = { x = 14.8, z = 13.8, w = 1.6, d = 1.1, height = 2.6 } -- сундуки у лифта
local THRONE = Vector3.new(0, 3, -4.3) -- центр верхней ступени под троном

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
			color = if tier == "interior" then TONE_IN else TONE_OUT,
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
	local _, _, _, h = Kit.Dims(cfg)
	for i, t in TIERS do
		table.insert(shell, block(-t[1], t[1], i - 1, i, t[2], t[3], "Dais" .. i))
	end
	local wall = cfg.Half.X - cfg.Wall
	local front = -(cfg.Half.Y - cfg.Wall)
	for _, s in { -1, 1 } do
		local side = if s < 0 then "L" else "R"
		local c = COLUMN
		for i, z in c.z do
			table.insert(
				shell,
				block(s * (c.x - c.half), s * (c.x + c.half), 0, h, z - c.half, z + c.half, "Column" .. i .. side)
			)
		end
		table.insert(shell, block(s * NICHE.half, s * wall, 0, h, front, BACK, "Niche" .. side))
		local k = CANDLE
		table.insert(
			shell,
			block(s * k.x - 0.8, s * k.x + 0.8, k.y, k.y + k.height, k.z - 0.8, k.z + 0.8, "Candle" .. side)
		)
		local b = CHEST
		table.insert(shell, block(s * b.x - b.w, s * b.x + b.w, 0, b.height, b.z - b.d, b.z + b.d, "Chest" .. side))
	end
	table.insert(shell, block(-NICHE.half, NICHE.half, 0, h, front, NICHE.back, "NicheBack"))
	return shell
end

function Theme.exhibit(_cfg: any): { at: Vector3, yaw: number, scale: number }
	return { at = THRONE, yaw = 180, scale = 2.8 }
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
	-- Свет и тени зала запечены в цвета вершин; лампа одна — под потолком между лифтом и троном: от любой точки зала до
	-- неё меньше 20 стадов (на низкой графике дальние лампы не рисуются, BUGS.md), свет идёт сверху и спереди на трон.
	-- Прожектор из-под полога светит вниз на трон: он светлее зала и выделяется на тёмном балдахине.
	lamp(list, Vector3.new(0, 15.6, 4.0), { range = 40, brightness = LAMP, color = WARM })
	lamp(list, Vector3.new(0, 14.4, -1.5), { range = 16, brightness = SPOT, color = WARM, spot = 50 })
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

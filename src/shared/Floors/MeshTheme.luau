--!strict
-- Тема этажа из мешей по описанию — общий технический конвейер новых этажей (по эталонам GoldenThrone v6,
-- TRexSkeleton v1, SpaceHelmet v1, утверждены владельцем 2026-11-21). Художественный замысел — в скрипте Blender
-- scripts/blender/floor_<тема>.py (геометрия, цвета, тени в цветах вершин) и в описании темы (каркас, экспонат, свет);
-- здесь — только сборка: меши уровней из Floors/FloorMeshes с материалами по имени детали, стены каркаса и ниша дверей
-- лифта в убранстве фасада, лампы зала.
--   Детали: <prefix>_F_* — фасад, <prefix>_I_* — зал, <prefix>_S_All — силуэт; *_Rings — Plastic + LegoSquaresFar,
--   *_Quiet — Plastic + LegoSquaresQuiet, *_Props — Plastic + LegoRingsD39Boss (объекты в стиле предметов и боссов),
--   остальные — SmoothPlastic (Glass светится сам: затенения в нём нет).
--   Пока меши темы не привязаны (нет записи в FloorMeshes), этаж строится из каркаса и стен — без ошибки.
-- Зависит от Floors/Kit, Floors/FloorMeshes.

local FloorMeshes = require(script.Parent.FloorMeshes)
local Kit = require(script.Parent.Kit)

local B = Kit.B

local MeshTheme = {}

export type Light = { range: number, brightness: number, color: Color3, spot: number? }
export type Def = {
	name: string, -- ItemID предмета и имя записи в FloorMeshes
	poche: Color3, -- стены каркаса в убранстве (скрыты между обшивками, упор камеры)
	tones: { interior: Color3?, facade: Color3?, glowIn: Color3?, glowOut: Color3? }?, -- множители яркости деталей
	shell: ((cfg: any, box: (number, number, number, number, number, number, string) -> any) -> { any })?, -- опоры
	exhibit: { at: Vector3, yaw: number, scale: number }, -- место показа (верх опоры каркаса)
	lamps: { { at: Vector3, light: Light } }, -- свет зала
}

local FAR = "LegoSquaresFar"
local QUIET = "LegoSquaresQuiet"
local PROPS = "LegoRingsD39Boss" -- объекты этажа — квадраты-контуры D39 в масштабе боссов
local WHITE = Color3.fromHex("FFFFFF")
local OUTSIDE = Color3.fromHex("E2E2E2") -- фасад на солнце: без множителя светлые цвета упираются в предел яркости

local function look(name: string): (Enum.Material, string?)
	if string.find(name, "_Rings$") then
		return Enum.Material.Plastic, FAR
	elseif string.find(name, "_Quiet$") then
		return Enum.Material.Plastic, QUIET
	elseif string.find(name, "_Props$") then
		return Enum.Material.Plastic, PROPS
	end
	return Enum.Material.SmoothPlastic, nil
end

-- Брусок по границам x0…x1, y0…y1, z0…z1 (порядок границ любой).
local function box(x0: number, x1: number, y0: number, y1: number, z0: number, z1: number, name: string): any
	return B(
		Vector3.new(math.abs(x1 - x0), math.abs(y1 - y0), math.abs(z1 - z0)),
		Vector3.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
		Color3.new(0, 0, 0),
		{ name = name }
	)
end

function MeshTheme.new(def: Def): any
	local Theme = {}
	Theme.Name = def.name
	Theme.soloLights = true
	local tones = def.tones or {}

	local function tone(name: string, tier: string): Color3
		if string.find(name, "_I_Glass$") then
			return tones.glowIn or WHITE
		elseif string.find(name, "_F_Glass$") then
			return tones.glowOut or tones.facade or OUTSIDE
		elseif tier == "interior" then
			return tones.interior or WHITE
		end
		return tones.facade or OUTSIDE
	end

	local function meshes(tier: string): { any }
		local entry = FloorMeshes[def.name]
		local list: { any } = {}
		if not entry then
			return list
		end
		local names = {}
		for name, info in entry.parts do
			if info.tier == tier then
				table.insert(names, name)
			end
		end
		table.sort(names)
		for _, name in names do
			local info = entry.parts[name]
			local material, variant = look(name)
			table.insert(list, {
				mesh = name,
				name = name,
				size = info.size,
				cframe = CFrame.new(info.center),
				color = tone(name, tier),
				material = material,
				variant = variant,
			})
		end
		return list
	end

	function Theme.shell(cfg: any): { any }
		local shell = Kit.Shell(cfg)
		if def.shell then
			for _, b in def.shell(cfg, box) do
				table.insert(shell, b)
			end
		end
		return shell
	end

	function Theme.exhibit(_cfg: any): { at: Vector3, yaw: number, scale: number }
		return def.exhibit
	end

	local function interior(): { any }
		local list = meshes("interior")
		for _, l in def.lamps do
			table.insert(
				list,
				B(Vector3.new(0.2, 0.2, 0.2), l.at, WHITE, {
					material = Enum.Material.SmoothPlastic,
					transparency = 1,
					light = l.light,
					name = "Light",
				})
			)
		end
		return list
	end

	local function facade(cfg: any): { any }
		local list = meshes("facade")
		for _, side in { "Front", "Left", "Right" } do
			Kit.Wall(list, cfg, side, {}, def.poche)
		end
		local door = Kit.DoorOpening()
		Kit.Wall(list, cfg, "Back", { door }, def.poche)
		table.insert(
			list,
			Kit.Slice("Back", cfg, door[1], door[2], door[3], door[4], 0.6, cfg.Wall, def.poche, { occlude = true })
		)
		return list
	end

	function Theme.decor(cfg: any, _ctx: any, tier: string): { any }
		if tier == "interior" then
			return interior()
		elseif tier == "facade" then
			return facade(cfg)
		elseif tier == "silhouette" then
			return meshes("silhouette")
		end
		return {}
	end

	return Theme
end

return MeshTheme

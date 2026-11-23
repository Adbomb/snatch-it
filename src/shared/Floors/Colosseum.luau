--!strict
-- Этаж «Колизей» (первая партия новых этажей, 2026-11-21): этаж — сам амфитеатр. Снаружи — римская аркада в три
-- яруса из травертина с полуколоннами, антаблементами и аттиком с мачтами навеса; правый передний угол обрушен, за
-- руиной виден внутренний ярус. Внутри — арена: трибуны ярусами с трёх сторон, песок, мраморный постамент с моделью
-- Колизея, полосатый веларий с окулусом (сквозь него — небо и свет), триумфальная арка у лифта, жаровни, колесница.
-- Геометрия — scripts/blender/floor_colosseum.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: трибуны (по три яруса у боковых и передней стен), постамент, пилоны триумфальной арки.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

local SIDE = { { 15, 3 }, { 13, 2 }, { 11, 1 } } -- ярусы у боковых стен: внутренний край x, высота
local FRONT = { { -14, 3 }, { -12, 2 }, { -10, 1 } } -- ярусы у передней стены: внутренний край z, высота
local SEAT_Z = 6 -- трибуны боковых стен — до z = 6 (дальше — проход к лифту)
local ARENA = Vector3.new(0, 0, -2) -- центр арены и постамента
local TOP = 1.64 -- верх постамента

return MeshTheme.new({
	name = "Colosseum",
	poche = Color3.fromHex("5A4A3A"),
	tones = { glowIn = Color3.fromHex("E0E0E0") },
	shell = function(cfg: any, box: any): { any }
		local wall = cfg.Half.X - cfg.Wall
		local front = -(cfg.Half.Y - cfg.Wall)
		local list = {}
		for _, s in { -1, 1 } do
			local side = if s < 0 then "L" else "R"
			local outer = wall
			for k, t in SIDE do
				table.insert(list, box(s * t[1], s * outer, 0, t[2], front, SEAT_Z, "Seats" .. k .. side))
				outer = t[1]
			end
			-- пилоны триумфальной арки у лифта (площадка лифта |x| < 4 — свободна)
			table.insert(list, box(s * 4.05, s * 7.7, 0, 13, 14, cfg.Half.Y - cfg.Wall, "Gate" .. side))
		end
		local inner = front
		for k, t in FRONT do
			local half = SIDE[k][1]
			table.insert(list, box(-half, half, 0, t[2], inner, t[1], "SeatsFront" .. k))
			inner = t[1]
		end
		table.insert(list, box(ARENA.X - 5.6, ARENA.X + 5.6, 0, 0.95, ARENA.Z - 4.6, ARENA.Z + 4.6, "Plinth1"))
		table.insert(list, box(ARENA.X - 5, ARENA.X + 5, 0.95, TOP, ARENA.Z - 4, ARENA.Z + 4, "Plinth2"))
		return list
	end,
	exhibit = { at = Vector3.new(ARENA.X, TOP, ARENA.Z), yaw = 180, scale = 3.4 },
	lamps = {
		-- солнце сквозь окулус навеса — на модель; тёплый свет арены
		{
			at = Vector3.new(ARENA.X, 15.5, ARENA.Z),
			light = { range = 18, brightness = 2.4, color = Color3.fromHex("FFF4E0"), spot = 50 },
		},
		{ at = Vector3.new(0, 15, 4), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFE8C8") } },
		{
			at = Vector3.new(ARENA.X, 6, ARENA.Z + 7),
			light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF0DC") },
		},
	},
})

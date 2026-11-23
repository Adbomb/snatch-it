--!strict
-- Этаж «Золотой микрофон» (первая партия новых этажей, 2026-11-21): этаж — гигантский концертный усилитель. Снаружи —
-- чёрные стены-кейсы с золотыми уголками и хромовыми рёбрами, спереди басовик, столбик динамиков и светящийся
-- эквалайзер, сверху панель усилителя с ручками; по бокам динамик и рупор, кабели; сзади решётка и разъёмы.
-- Внутри — концертный клуб: сцена с рампой, микрофон на круглом подиуме с фиолетовым кольцом под фермой с
-- прожекторами, стены колонок, экран со звуковой волной, акустические панели, гитары, золотые пластинки, танцпол,
-- стойки с бархатным канатом у лифта.
-- Геометрия — scripts/blender/floor_mic.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: сцена, подиум микрофона, стены колонок по бокам сцены.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

local STAGE = { front = -6, height = 1.2 } -- сцена у передней стены
local MIC = Vector3.new(0, 0, -9.5) -- подиум с микрофоном
local TOP = 2.04 -- верх подиума

return MeshTheme.new({
	name = "GoldenMic",
	poche = Color3.fromHex("1A1A20"),
	tones = { glowIn = Color3.fromHex("BEBEBE") }, -- танцпол и экран приглушены: без пересвета
	shell = function(cfg: any, box: any): { any }
		local wall = cfg.Half.X - cfg.Wall
		local front = -(cfg.Half.Y - cfg.Wall)
		local list = {
			box(-wall, wall, 0, STAGE.height, front, STAGE.front, "Stage"),
			box(MIC.X - 2.6, MIC.X + 2.6, STAGE.height, TOP, MIC.Z - 2.6, MIC.Z + 2.6, "Riser"),
		}
		for _, s in { -1, 1 } do
			local side = if s < 0 then "L" else "R"
			table.insert(list, box(s * 11, s * 15.9, STAGE.height, 9, -15, -12.5, "Speakers" .. side))
		end
		return list
	end,
	exhibit = { at = Vector3.new(MIC.X, TOP, MIC.Z), yaw = 180, scale = 3.6 },
	lamps = {
		-- прожектор на микрофон, мягкий свет из зала, цветные отсветы сцены
		{
			at = Vector3.new(MIC.X, 14.5, MIC.Z),
			light = { range = 18, brightness = 2.6, color = Color3.fromHex("FFF6EA"), spot = 45 },
		},
		{ at = Vector3.new(0, 14, 6), light = { range = 40, brightness = 0.5, color = Color3.fromHex("C8BEFF") } },
		{
			at = Vector3.new(MIC.X, 7, MIC.Z + 6.5),
			light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4EA") },
		},
		{ at = Vector3.new(-9, 6, -10), light = { range = 10, brightness = 0.5, color = Color3.fromHex("8B5CF6") } },
		{ at = Vector3.new(9, 6, -10), light = { range = 10, brightness = 0.5, color = Color3.fromHex("FF4FA8") } },
	},
})

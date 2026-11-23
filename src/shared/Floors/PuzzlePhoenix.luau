--!strict
-- Этаж «Феникс-головоломка» (восьмая партия новых этажей, 2026-11-22).
-- Замысел: этаж — мастерская фейерверков. Снаружи — тёмно-синяя «ночная» стена со звёздами, по которой разлетаются
-- три салюта разного размера (светящиеся лучи-искры), внизу — красно-жёлтый цоколь с предупреждающими полосами,
-- ворота цеха, у фасада на пусковых рамах стоят огромные ракеты в полоску, рядом — батареи-кубы из цветных трубок,
-- ящики и катушки фитиля; по парапету — ряд маленьких ракет, готовых к пуску. Внутри — цех: тёмный потолок-небо с
-- вспышками салютов, верстаки с трубками и шарами-звёздками, стеллажи цветных зарядов, большая ракета на стапеле,
-- бочки с порохом, фонарики; экспонат — на стальной пусковой площадке с красно-жёлтым кольцом и стрелками.
-- Геометрия — scripts/blender/floor_fireworks.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: стальная пусковая площадка.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "PuzzlePhoenix",
	poche = Color3.fromHex("22242C"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.9, 3.9, 0, 1.1, -6.9, 0.9, "Pad"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.1, -3), yaw = 180, scale = 2.6 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(-8, 12, -9), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FFB050") } },
		{ at = Vector3.new(8, 12, -1), light = { range = 9, brightness = 0.5, color = Color3.fromHex("80E0FF") } },
	},
})

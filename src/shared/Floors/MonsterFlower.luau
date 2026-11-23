--!strict
-- Этаж «Цветок-монстр» (третья партия новых этажей, 2026-11-21).
-- Замысел: этаж — викторианская оранжерея, из которой вырываются хищные растения. Снаружи — кирпичный цоколь,
-- белый чугунный переплёт с бледно-зелёными стёклами (несколько выбито), веерное окно, гребень с навершиями,
-- огромная мухоловка с раскрытыми створками, лозы с листьями, кувшиночники в горшках, газовый фонарь, сарай для
-- рассады. Внутри — ботанический зал: терракотовая плитка, грядки с мухоловками, кувшиночниками и росянками, рёбра
-- свода, подвесные корзины, стол для пересадки, огромный горшок-постамент.
-- Геометрия — scripts/blender/floor_greenhouse.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: горшок-постамент и грядки у боковых стен.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "MonsterFlower",
	poche = Color3.fromHex("3A5A4A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.3, 3.3, 0, 0.8, -6.3, 0.3, "Pot1"),
			box(-4, 4, 0.8, 1.6, -7, 1, "Pot2"),
			box(-16.88, -13.68, 0, 1, -14.6, 5, "BedL"),
			box(13.68, 16.88, 0, 1, -14.6, 5, "BedR"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.6, -3), yaw = 180, scale = 2.4 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("E8FFE8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("F4FFF0") } },
		{ at = Vector3.new(-12, 6, -6), light = { range = 9, brightness = 0.4, color = Color3.fromHex("6ACB5A") } },
		{ at = Vector3.new(12, 6, -6), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FF8AA0") } },
	},
})

--!strict
-- Этаж «Робо-утёнок» (третья партия новых этажей, 2026-11-21).
-- Замысел: этаж — фабрика роботов-игрушек. Снаружи — красный кирпич, стальные окна в мелкую клетку, пилообразный
-- парапет «шед», манипулятор с огромным утёнком, конвейер с утятами, шестерни, круглая вывеска, кирпичные трубы с
-- дымом, рулонные ворота, цистерны. Внутри — сборочный цех: стальные фермы, П-образный конвейер с утятами, два
-- манипулятора, пресс, покрасочная камера, поворотный стол под порталом с крюком.
-- Геометрия — scripts/blender/floor_roboduck.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: поворотный стол и стойки портала.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "RoboDuck",
	poche = Color3.fromHex("2E3440"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.2, 4.2, 0, 0.6, -7.2, 1.2, "Turntable1"),
			box(-3.6, 3.6, 0.6, 1.2, -6.6, 0.6, "Turntable2"),
			box(-6.5, -5.5, 0, 13, -7.1, -6.1, "PostL"),
			box(5.5, 6.5, 0, 13, -7.1, -6.1, "PostR"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.2, -3), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E0") } },
		{
			at = Vector3.new(0, 12, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(-12, 6, -8), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFC420") } },
		{ at = Vector3.new(12, 6, -8), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFC420") } },
	},
})

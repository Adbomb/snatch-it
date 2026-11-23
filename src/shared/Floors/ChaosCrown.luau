--!strict
-- Этаж «Тёмная корона хаоса» (третья партия новых этажей, 2026-11-21).
-- Замысел: этаж — цитадель тёмного чародея. Снаружи — обсидиановая кладка, контрфорсы с пинаклями, стрельчатые
-- окна, глубокий портал с фиолетовой мглой и парящим кольцом рун, цепи, парапет-корона с самоцветами, парящие
-- обломки, рунные камни, шпиль. Внутри — склеп: рунный круг на полу и потолке, стрельчатые ниши со светом, колонны
-- с фиолетовыми жаровнями, парящие камни, цепи к ступенчатому алтарю.
-- Геометрия — scripts/blender/floor_chaoscrown.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: алтарь из трёх ступеней и четыре колонны.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "ChaosCrown",
	poche = Color3.fromHex("1E1828"),
	tones = { glowIn = Color3.fromHex("C0C0C0") }, -- свечение зала приглушено: без пересвета
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.6, 4.6, 0, 0.5, -7.2, 1.2, "Step1"),
			box(-3.8, 3.8, 0.5, 1, -6.5, 0.5, "Step2"),
			box(-3, 3, 1, 1.6, -5.8, -0.2, "Step3"),
			box(-10.3, -7.7, 0, 9.2, -12.3, -9.7, "Column1"),
			box(7.7, 10.3, 0, 9.2, -12.3, -9.7, "Column2"),
			box(-12.3, -9.7, 0, 9.2, 1.7, 4.3, "Column3"),
			box(9.7, 12.3, 0, 9.2, 1.7, 4.3, "Column4"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.6, -3), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.5, color = Color3.fromHex("D8C8FF") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.4, color = Color3.fromHex("F0E8FF"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.7, color = Color3.fromHex("F4F0FF") } },
		{ at = Vector3.new(-9, 10, -11), light = { range = 9, brightness = 0.6, color = Color3.fromHex("9A4AFF") } },
		{ at = Vector3.new(9, 10, -11), light = { range = 9, brightness = 0.5, color = Color3.fromHex("E040A0") } },
	},
})

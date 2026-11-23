--!strict
-- Этаж «Египетский саркофаг» (одиннадцатая партия новых этажей, 2026-11-22).
-- Замысел: этаж — ночная колоннада Луксорского храма. Снаружи — открытая колоннада: ряд толстых колонн-папирусов с
-- закрытыми бутонами-капителями и цветными поясами, на них — тяжёлый архитрав с иероглифическим фризом (простые
-- знаки: анх, солнечный круг, волны, перо, тростник), за колоннами — тёмно-синяя стена со звёздами, перед
-- колоннадой — аллея с факелами и низкими сфинксами-постаментами без голов (только лапы и постамент), каменные
-- плиты, бассейн-канал. Внутри — гипостильный зал: восемь массивных колонн с росписью, звёздный потолок,
-- саркофаги-ящики и канопы в нишах, свет факелов; экспонат — на погребальных санях (низкий постамент-полозья с
-- золотыми кольцами).
-- Геометрия — scripts/blender/floor_luxor.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: погребальные сани на полозьях.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "EgyptianSarcophagus",
	poche = Color3.fromHex("122046"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.4, 3.4, 0, 1.0, -7.0, 0.6, "Sled"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.0, -3), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 5, -13), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FF9040") } },
		{ at = Vector3.new(-8, 4, -14), light = { range = 8, brightness = 0.5, color = Color3.fromHex("FFB060") } },
	},
})

--!strict
-- Этаж «Верблюжонок-фляга» (девятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — глиняная фактория у колодца в стиле сахельской архитектуры. Снаружи — глиняная стена с круглыми
-- контрфорсами, увенчанными коническими башенками, ряды торчащих деревянных кольев-торонов, высокие ниши, резная
-- деревянная дверь с металлическими шляпками, треугольные продухи; перед ней — колодец с деревянной рамой, воротом
-- и ведром, стойка с висящими флягами, пальмы, кувшины, седло на подставке, ковры на перекладине. Внутри — склад-
-- лавка: квадратные глиняные столбы и потолок из пальмовых брёвен, мешки зерна горкой, стойки с флягами по стенам,
-- большие кувшины, ниши с треугольным верхом; экспонат — на круглом каменном срубе колодца с водой и мотком
-- верёвки.
-- Геометрия — scripts/blender/floor_sahel.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: каменный сруб колодца.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "CanteenCamel",
	poche = Color3.fromHex("5A3A22"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.6, 3.6, 0, 1.3, -6.6, 0.6, "Well"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.3, -3), yaw = 180, scale = 3.0 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(-10, 6, -8), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFB060") } },
		{ at = Vector3.new(10, 8, -4), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFE0B0") } },
	},
})

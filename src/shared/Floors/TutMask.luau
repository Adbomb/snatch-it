--!strict
-- Этаж «Золотая маска Тутанхамона» (вторая партия новых этажей, 2026-11-21).
-- Замысел: этаж — вход в гробницу фараона. Снаружи — храмовый пилон из песчаника, фриз «немес»,
-- крылатый диск, картуши с анкхом, обелиски, колоннады с папирусами. Внутри — сокровищница: звёздный
-- потолок, пояса росписи, колонны-папирусы, ступенчатый постамент из чёрного камня, сундуки, монеты, канопы.
-- Геометрия — scripts/blender/floor_tutmask.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: ступени постамента и четыре колонны.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "TutMask",
	poche = Color3.fromHex("8A6A3E"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.6, 4.6, 0, 0.55, -8.6, 0.6, "Step1"),
			box(-3.8, 3.8, 0.55, 1.1, -7.8, -0.2, "Step2"),
			box(-3, 3, 1.1, 1.6, -7, -1, "Step3"),
			box(-7.85, -6.15, 0, 13.4, -11.35, -9.65, "Column1"),
			box(6.15, 7.85, 0, 13.4, -11.35, -9.65, "Column2"),
			box(-10.35, -8.65, 0, 13.4, 0.65, 2.35, "Column3"),
			box(8.65, 10.35, 0, 13.4, 0.65, 2.35, "Column4"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.6, -4), yaw = 180, scale = 3.4 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.55, color = Color3.fromHex("FFE0A8") } },
		{
			at = Vector3.new(0, 15, -4),
			light = { range = 18, brightness = 2.4, color = Color3.fromHex("FFF2D8"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 3), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF0DC") } },
		{ at = Vector3.new(-4.8, 5.5, 2.2), light = { range = 9, brightness = 0.7, color = Color3.fromHex("FF9A3A") } },
		{ at = Vector3.new(4.8, 5.5, 2.2), light = { range = 9, brightness = 0.7, color = Color3.fromHex("FF9A3A") } },
	},
})

--!strict
-- Этаж «Крысиный трон» (десятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — подземный дворец крысиного короля в старом коллекторе. Снаружи — тёмная кирпичная стена
-- коллектора с большим арочным тоннелем за чугунной решёткой, из которого течёт ручей в канавку, по сторонам —
-- толстые трубы с фланцами и вентилями, над аркой — золотая корона, сырно-жёлтые знамёна, факелы, крысиные дверцы-
-- арочки, кучи «сокровищ» (ящики, банки, монеты), люк и лесенка. Внутри — тронный зал: кирпичные своды-рёбра,
-- трубы под потолком, красная ковровая дорожка, знамёна с короной, канделябры со свечами, горы монет, головки
-- сыра, настенные факелы; экспонат — на ступенчатом бархатном помосте с золотой каймой.
-- Геометрия — scripts/blender/floor_ratthrone.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: ступенчатый бархатный помост.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "RatThrone",
	poche = Color3.fromHex("3A2A28"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.6, 4.6, 0, 0.6, -7.6, 1.6, "Step1"),
			box(-4.1, 4.1, 0.6, 1.2, -7.1, 1.1, "Step2"),
			box(-3.7, 3.7, 1.2, 1.8, -6.7, 0.7, "Step3"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.8, -3), yaw = 180, scale = 2.1 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 7, -13), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FF9040") } },
		{ at = Vector3.new(-12, 5, -6), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFC060") } },
	},
})

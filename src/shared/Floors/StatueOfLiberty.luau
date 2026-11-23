--!strict
-- Этаж «Статуя Свободы» (вторая партия новых этажей, 2026-11-21).
-- Замысел: этаж — пьедестал статуи на острове в гавани. Снаружи — гранит со звёздчатым
-- фортом, рустом, пилястрами, щитами и лоджией; медные факелы-рельефы, лучи короны, скрижаль, окна, фонари.
-- Внутри — зал под плиточным сводом с окнами на гавань и город, статуя на гранитном постаменте, медное
-- пламя, корона, скамьи, стойки с канатом.
-- Геометрия — scripts/blender/floor_liberty.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: постамент из двух ступеней.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "StatueOfLiberty",
	poche = Color3.fromHex("84705E"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.6, 4.6, 0, 0.6, -7.6, 1.6, "Step1"),
			box(-3.6, 3.6, 0.6, 1.2, -6.6, 0.6, "Step2"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.2, -3), yaw = 180, scale = 2.6 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("F4F8FF") } },
		{
			at = Vector3.new(0, 16, -3),
			light = { range = 20, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 8, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(-9.5, 7, -10), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FFB040") } },
		{ at = Vector3.new(9.5, 7, -10), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FFB040") } },
	},
})

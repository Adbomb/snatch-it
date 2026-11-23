--!strict
-- Этаж «Часовой голем» (десятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — мастерская часовщика. Снаружи — тёмно-зелёная викторианская лавка с золотыми полосами, над
-- входом — один большой циферблат с римскими метками и стрелками в латунной раме, рядом — открытая «механика»:
-- шестерни разного размера в сцеплении, витрина с часами разной формы, полосатый навес, латунные трубы, высокие
-- напольные часы-маятник у двери, фонарь на кронштейне. Внутри — зал механизмов: огромные шестерни на боковых
-- стенах, длинный маятник посреди дальней стены, верстак с инструментами и лампой-лупой, полки с часами-домиками,
-- ковёр с узором-шестернёй; экспонат — на платформе-шестерне с зубцами.
-- Геометрия — scripts/blender/floor_clockwork.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: платформа-шестерня.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "ClockGolem",
	poche = Color3.fromHex("2A3A34"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.7, 3.7, 0, 1.4, -6.7, 0.7, "Gear"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.4, -3), yaw = 180, scale = 2.0 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(12, 6, -6), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFC870") } },
		{ at = Vector3.new(-12, 9, -6), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFE0B0") } },
	},
})

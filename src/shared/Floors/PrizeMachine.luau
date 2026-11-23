--!strict
-- Этаж «Легендарный автомат с призами» (третья партия новых этажей, 2026-11-21).
-- Замысел: этаж — цирк-шапито на ярмарке. Снаружи — полосатое полотно над дощатым настилом, фестон из флажков и
-- полосатый скат, мачты с вымпелами, арка входа с лампочками и звездой, касса, гирлянды, колесо обозрения и
-- силомер с тиром на боках, цирковой фургон сзади. Внутри — манеж: бортик в полоску с проходом к лифту, звёздный
-- подиум, купол шатра с люстрой, мачты, трапеция, трибуны, занавес, прожекторы, полки с призами.
-- Геометрия — scripts/blender/floor_circus.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: звёздный подиум, барабан и две мачты.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "PrizeMachine",
	poche = Color3.fromHex("3A2E2A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.4, 4.4, 0, 0.5, -7.4, 1.4, "Star"),
			box(-2.9, 2.9, 0.5, 1, -5.9, -0.1, "Drum"),
			box(-10.1, -9.1, 0, 18, -3.5, -2.5, "MastL"),
			box(9.1, 10.1, 0, 18, -3.5, -2.5, "MastR"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1, -3), yaw = 180, scale = 2.4 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFE8D0") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF4E8"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF0E0") } },
		{ at = Vector3.new(-9, 8, -3), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFB040") } },
		{ at = Vector3.new(9, 8, -3), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FF6A8A") } },
	},
})

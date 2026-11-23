--!strict
-- Этаж «Голова моаи» (вторая партия новых этажей, 2026-11-21).
-- Замысел: этаж — платформа аху на берегу острова. Снаружи — стена из базальтовых глыб, прибой, травяной
-- склон, профили моаи с красными пукао, плита с человеком-птицей, пальмы. Внутри — пляж на закате: лагуна,
-- небо-панорама, звёзды, моаи на ступенчатой аху, факелы тики, пальмы, лодка с балансиром.
-- Геометрия — scripts/blender/floor_moai.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: аху из двух ступеней.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "Moai",
	poche = Color3.fromHex("2E2E34"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-6, 6, 0, 0.8, -6, 0, "Ahu1"),
			box(-5, 5, 0.8, 1.6, -5, -1, "Ahu2"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.6, -3), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 4), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFD8C0") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF2E0"), spot = 50 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF0E0") } },
		{ at = Vector3.new(-7.5, 6, -5.5), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FF9A3A") } },
		{ at = Vector3.new(7.5, 6, -5.5), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FF9A3A") } },
	},
})

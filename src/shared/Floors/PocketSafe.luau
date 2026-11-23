--!strict
-- Этаж «Карманный сейф» (третья партия новых этажей, 2026-11-21).
-- Замысел: этаж — банк в стиле ар-деко с огромным хранилищем. Снаружи — известняк с каннелированными пилястрами,
-- бронзовые пояса, парапет-зиккурат, огромная круглая дверь сейфа со штурвалом, слитки за бархатным канатом,
-- вращающаяся дверь, ящик ночного депозита, камеры, окна с решётками, инкассаторский фургон. Внутри — хранилище:
-- пол в клетку, стены из ячеек, открытая круглая дверь, пирамиды слитков, мешки с монетами, лучи сигнализации,
-- стальной постамент.
-- Геометрия — scripts/blender/floor_vault.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: стальной постамент из двух ступеней.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "PocketSafe",
	poche = Color3.fromHex("4A505A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4, 4, 0, 0.6, -6.6, 0.6, "Plinth1"),
			box(-3.3, 3.3, 0.6, 1.4, -5.9, -0.1, "Plinth2"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.4, -3), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("F0F4FF") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFFAF0"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF8F0") } },
		{ at = Vector3.new(-11, 4, -10), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFD27A") } },
		{ at = Vector3.new(11, 3, -8), light = { range = 8, brightness = 0.3, color = Color3.fromHex("FF4A4A") } },
	},
})

--!strict
-- Этаж «Портативный дракон» (третья партия новых этажей, 2026-11-21).
-- Замысел: этаж — замок, в котором поселился дракон. Снаружи — донжон из грубого камня с машикулями и зубцами,
-- круглые угловые башни, арка ворот с решёткой и подъёмным мостом, зелёный дракон обвил переднюю башню (голова в
-- профиле, крыло по фасаду, хвост по боку), следы когтей, факелы, кран с мешками. Внутри — сокровищница: колонны и
-- рёбра свода, факелы, щиты, горы монет, сундуки, мечи в золоте, гнездо с яйцами.
-- Геометрия — scripts/blender/floor_dragon.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: помост из двух ступеней и четыре колонны.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "PocketDragon",
	poche = Color3.fromHex("3A3A42"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.4, 4.4, 0, 0.7, -7.4, 1.4, "Dais1"),
			box(-3.6, 3.6, 0.7, 1.4, -6.6, 0.6, "Dais2"),
			box(-13.2, -10.8, 0, 12, -11.2, -8.8, "Column1"),
			box(10.8, 13.2, 0, 12, -11.2, -8.8, "Column2"),
			box(-13.2, -10.8, 0, 12, 2.8, 5.2, "Column3"),
			box(10.8, 13.2, 0, 12, 2.8, 5.2, "Column4"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.4, -3), yaw = 180, scale = 3.4 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.55, color = Color3.fromHex("FFD8B0") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF0DC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF0E0") } },
		{ at = Vector3.new(-8, 7, -12), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FF9A3A") } },
		{ at = Vector3.new(8, 7, -12), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FF9A3A") } },
	},
})

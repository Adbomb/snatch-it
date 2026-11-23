--!strict
-- Этаж «НЛО в банке» (вторая партия новых этажей, 2026-11-21).
-- Замысел: этаж — исследовательский комплекс, поймавший летающую тарелку. Снаружи (v2) — светлые
-- бронепанели со световыми щелями, пилоны-излучатели по углам, в центре фасада огромная тарелка выходит из
-- портала удержания, её держат манипуляторы, притягивающий луч бьёт в посадочную площадку; на боках —
-- банки-капсулы с маленькими тарелками внутри и энергомагистрали. Внутри — лаборатория: капсулы с
-- зелёной жидкостью, пульты с
-- экранами, трубы, платформа сканера под аркой с кольцами, ящики, тележка.
-- Геометрия — scripts/blender/floor_ufojar.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: платформа сканера, стойки арки, капсулы у стен.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "UfoJar",
	poche = Color3.fromHex("2C3038"),
	tones = { glowIn = Color3.fromHex("D0D0D0") }, -- свечение зала приглушено: без пересвета
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.2, 4.2, 0, 0.8, -7.2, 1.2, "Scanner1"),
			box(-3.4, 3.4, 0.8, 1.3, -6.4, 0.4, "Scanner2"),
			box(-5.7, -4.7, 0, 13, -3.5, -2.5, "PillarL"),
			box(4.7, 5.7, 0, 13, -3.5, -2.5, "PillarR"),
			box(-16.08, -12.88, 0, 9, -13.6, -4.9, "TanksL"),
			box(12.88, 16.08, 0, 9, -13.6, -4.9, "TanksR"),
			box(-16.08, -12.88, 0, 9, 4.9, 8.1, "TankL3"),
			box(12.88, 16.08, 0, 9, 4.9, 8.1, "TankR3"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.3, -3), yaw = 180, scale = 3.0 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.55, color = Color3.fromHex("E0FFF0") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("F4FFF4"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("F4FFF8") } },
		{ at = Vector3.new(-14, 6, -9), light = { range = 10, brightness = 0.6, color = Color3.fromHex("5CFF6A") } },
		{ at = Vector3.new(14, 6, -9), light = { range = 10, brightness = 0.6, color = Color3.fromHex("5CFF6A") } },
	},
})

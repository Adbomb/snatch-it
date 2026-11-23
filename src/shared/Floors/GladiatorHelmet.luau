--!strict
-- Этаж «Шлем гладиатора» (одиннадцатая партия новых этажей, 2026-11-22).
-- Замысел: этаж — школа гладиаторов (лудус). Снаружи — красная штукатурка с травертиновым цоколем, ворота-арка с
-- тяжёлой решёткой и бронзовыми гвоздями, над ней — бронзовый шлем-эмблема с гребнем и лавровый венок, по бокам —
-- стойки с круглыми и прямоугольными щитами, копья в пирамиде, деревянный тренировочный столб-палус, бочки с
-- водой, амфоры, натянутый тент над скамьёй. Внутри — тренировочный двор под портиком: песчаная арена, столбы-
-- палусы со следами ударов, стойки с деревянными мечами, ряды щитов на стене, скамьи, бронзовые жаровни, крюки с
-- доспехами; экспонат — на круглом бронзовом щите-постаменте с умбоном.
-- Геометрия — scripts/blender/floor_ludus.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: круглый бронзовый щит.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "GladiatorHelmet",
	poche = Color3.fromHex("4A3A2A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.0, 4.0, 0, 1.2, -7.0, 1.0, "Shield"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.2, -3), yaw = 180, scale = 2.9 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 4, 5), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FF9040") } },
		{ at = Vector3.new(12, 8, -6), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFE0B0") } },
	},
})

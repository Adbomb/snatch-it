--!strict
-- Этаж «Трофейный бургер» (вторая партия новых этажей, 2026-11-21).
-- Замысел: этаж — закусочная 1950-х. Снаружи — нержавейка, витрины с красными диванами,
-- навес в полоску, неоновые зигзаги и звёзды, огромная вывеска-бургер, угловые башенки, табло-картинки.
-- Внутри — шашечный пол, стойка с табуретами, кабинки с диванами, музыкальный автомат, лампы, торт-подставка
-- со звёздами.
-- Геометрия — scripts/blender/floor_burger.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: торт-подставка и стойка у передней стены.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "TrophyBurger",
	poche = Color3.fromHex("8E96A4"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.4, 4.4, 0, 0.6, -6.4, 2.4, "Stand1"),
			box(-3.8, 3.8, 0.6, 1.5, -5.8, 1.8, "Stand2"),
			box(-12.2, 12.2, 0, 3.7, -13.08, -11.08, "Counter"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.5, -2), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4F0") } },
		{
			at = Vector3.new(0, 15, -2),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8F0"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 5), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4EC") } },
		{ at = Vector3.new(10.5, 6, 11.5), light = { range = 8, brightness = 0.6, color = Color3.fromHex("FF4FA8") } },
		{ at = Vector3.new(-10, 7, -8), light = { range = 10, brightness = 0.4, color = Color3.fromHex("38D6F0") } },
	},
})

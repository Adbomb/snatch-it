--!strict
-- Этаж «Гриф-вентилятор» (восьмая партия новых этажей, 2026-11-22).
-- Замысел: этаж — мельница-пекарня. Снаружи — белёные стены с тёмным фахверком, кирпичный цоколь и красная
-- черепичная кровля-пояс; на фасаде крутятся четыре огромных крыла мельницы (решётчатые лопасти с парусиной) на
-- деревянной ступице; внизу — витрина пекарни с хлебами под полосатым навесом, дверь с вывеской-кренделем, мешки
-- муки, тележка со снопами, кадки с тюльпанами; по углам — две маленькие белые ветряные турбины на мачтах. Внутри
-- — мукомольный зал: деревянные балки, жернова под вертикальным валом с зубчатым колесом, кирпичная печь с огнём,
-- длинный стол с хлебами, полки с караваями, мешки и снопы, подвесные фонари; экспонат — на круглом жёрнове с
-- бороздами.
-- Геометрия — scripts/blender/floor_windmill.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: круглый жёрнов на деревянном основании.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "FanVulture",
	poche = Color3.fromHex("4E3018"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.9, 3.9, 0, 1.0, -6.9, 0.9, "Millstone"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.0, -3), yaw = 180, scale = 2.6 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(-11, 4, -8), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FF9A40") } },
		{ at = Vector3.new(0, 10, -12), light = { range = 10, brightness = 0.4, color = Color3.fromHex("FFE0B0") } },
	},
})

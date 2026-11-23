--!strict
-- Этаж «Страусёнок-песочник» (восьмая партия новых этажей, 2026-11-22).
-- Замысел: этаж — ферма с красным амбаром. Снаружи — красные доски с белыми углами и наличниками, большие ворота
-- амбара с белыми косыми перекладинами, над ними — дверца сеновала с балкой-блоком и висящим тюком; на левом углу
-- — серебристая силосная башня с куполом, на парапете — флюгер-петушок; перед амбаром — деревянная изгородь,
-- круглые тюки сена, бидоны, корыто, курятник с лесенкой. Внутри — амбар: дощатые стены и балки, стойла с
-- воротцами, ряд гнёзд-ящиков с яйцами, сеновал на столбах с лестницей, кучи сена, вилы, бидоны, фонари; экспонат
-- — в огромном соломенном гнезде с яйцами на дощатом помосте.
-- Геометрия — scripts/blender/floor_farm.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: дощатый помост и соломенное гнездо.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "SandChick",
	poche = Color3.fromHex("5A3A22"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4, 4, 0, 0.5, -7, 1, "Deck"),
			box(-3.8, 3.8, 0.5, 1.1, -6.8, 0.8, "Nest"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.1, -3), yaw = 180, scale = 2.4 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 12, -12), light = { range = 10, brightness = 0.5, color = Color3.fromHex("FFD080") } },
		{ at = Vector3.new(-12, 6, -4), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFE0A0") } },
	},
})

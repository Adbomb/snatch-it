--!strict
-- Этаж «Фенек-загадочник» (восьмая партия новых этажей, 2026-11-22).
-- Замысел: этаж — клуб загадок и шахмат. Снаружи — кремовый особняк: цоколь шахматной клеткой из чёрных и белых
-- плит, высокие окна в тёмно-зелёных рамах, наверху — зубчатый парапет как у шахматной ладьи; у входа под зелёным
-- навесом — огромные фигуры: ладья и король по сторонам двери, ряд пешек вдоль тротуара, над входом — золотая
-- эмблема-пазл; на боках — тот же ритм окон и клетки. Внутри — зал-доска: весь пол вокруг постамента — огромная
-- шахматная доска с фигурами-статуями в разгар партии (ладьи, слоны, ферзь, пешки), по стенам — шкафы с коробками
-- головоломок, столики с маленькими досками и стульями, лампы с зелёными абажурами, кубики-головоломки на полках;
-- экспонат — на квадратной тумбе с клеткой на крышке.
-- Геометрия — scripts/blender/floor_chess.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: квадратная тумба с клеткой.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "FennecRiddler",
	poche = Color3.fromHex("2E3430"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.1, 3.1, 0, 1.1, -6.1, 0.1, "Dais"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.1, -3), yaw = 180, scale = 2.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 9, -12), light = { range = 10, brightness = 0.5, color = Color3.fromHex("FFE0A0") } },
		{ at = Vector3.new(-12, 6, -2), light = { range = 9, brightness = 0.4, color = Color3.fromHex("B0F0C0") } },
	},
})

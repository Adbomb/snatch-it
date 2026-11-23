--!strict
-- Этаж «Статуя Анубиса» (одиннадцатая партия новых этажей, 2026-11-22).
-- Замысел: этаж — Зал взвешивания сердца. Снаружи — чёрный базальт с золотыми поясами и бирюзовыми вставками, по
-- фасаду — ряд высоких золотых жезлов-уас, в центре — огромные золотые весы с чашами (на одной — перо, на другой —
-- сосуд-сердце), под ними — тяжёлая дверь с золотыми полосами, по углам — чёрные обелиски с золотыми вершинами,
-- жаровни с огнём, звёзды по верхнему поясу. Внутри — тёмный зал суда: колонны с золотыми кольцами, вдоль стен —
-- ряд из 12 тронов-ниш, высокие весы рядом с экспонатом, ладьи на подставках, курильницы, синий потолок со
-- звёздами; экспонат — на ступенчатом чёрном постаменте с золотой каймой.
-- Геометрия — scripts/blender/floor_judgment.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: ступенчатый чёрный постамент.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "AnubisStatue",
	poche = Color3.fromHex("1E1E26"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.4, 4.4, 0, 0.6, -7.4, 1.4, "Step1"),
			box(-3.9, 3.9, 0.6, 1.2, -6.9, 0.9, "Step2"),
			box(-3.4, 3.4, 1.2, 1.8, -6.4, 0.4, "Step3"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.8, -3), yaw = 180, scale = 3.0 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 4, 5), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FF9040") } },
		{ at = Vector3.new(-12, 8, -4), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFD070") } },
	},
})

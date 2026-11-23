--!strict
-- Этаж «Золотой банан» (вторая партия новых этажей, 2026-11-21).
-- Замысел: этаж — затерянный храм в джунглях. Снаружи — ступенчатая замшелая кладка, лестница
-- к каменным воротам под ступенчатым «ложным сводом» (створки песчаника с золотым швом и поясом),
-- жаровни, ромб с золотым бананом, водопад в каменную чашу, банановые пальмы, лианы, резные плиты.
-- Внутри (v2) — зал древнего храма, который забирают джунгли: кладка рядами разной высоты с
-- выступающими камнями и выпавшими блоками, пилястры, ниши с урнами и золотыми гроздьями, ступенчатый
-- свод с пологом листьев, корни дерева в углах, пруд с кувшинками, дорожка из плит; за алтарём —
-- ступенчатый портал с тёмной глубиной, по бокам стелы с золотыми поясами и жаровни.
-- Геометрия — scripts/blender/floor_banana.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: платформа, алтарь из двух ступеней, две стелы.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "GoldenBanana",
	poche = Color3.fromHex("3A4234"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-7, 7, 0, 0.4, -11, 1, "Platform"),
			box(-5, 5, 0, 0.8, -9, -1, "Altar1"),
			box(-4, 4, 0.8, 1.6, -8.2, -1.8, "Altar2"),
			box(-7.05, -5.35, 0, 9, -10.45, -8.75, "StelaL"),
			box(5.35, 7.05, 0, 9, -10.45, -8.75, "StelaR"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.6, -5), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.55, color = Color3.fromHex("E0FFD0") } },
		{
			at = Vector3.new(0, 15, -5),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF6D8"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 2), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF8E8") } },
		{ at = Vector3.new(-5.5, 6, 9), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FF9A3A") } },
		{ at = Vector3.new(5.5, 6, 9), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FF9A3A") } },
	},
})

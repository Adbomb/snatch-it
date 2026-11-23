--!strict
-- Этаж «Всевидящее око» (одиннадцатая партия новых этажей, 2026-11-22).
-- Замысел: этаж — театр иллюзиониста. Снаружи — фиолетово-чёрный фасад со звёздами, бархатные шторы-кулисы по
-- обеим сторонам золотой двери, над входом — треугольный фронтон с одним большим символом-оком в лучах (знак
-- театра), афишные тумбы с цилиндром и колодой, огромный перевёрнутый цилиндр с выглядывающими ушами-кроликами
-- (без морды), ящик с пилой, хрустальный шар на подставке, гирлянда лампочек по краю кровли. Внутри — сцена и
-- зрительный зал: полукруглая сцена с бархатным занавесом и рампой, ряды кресел, ложи-балкончики по бокам, люстра,
-- реквизит (ящик-исчезатель, кольца, шкаф-портал), звёзды-блёстки на тёмном потолке; экспонат — на круглой
-- вращающейся тумбе фокусника со звёздами.
-- Геометрия — scripts/blender/floor_illusion.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: тумба фокусника со звёздами.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "AllSeeingEye",
	poche = Color3.fromHex("2A1A3A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.2, 3.2, 0, 1.3, -6.2, 0.2, "Drum"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.3, -3), yaw = 180, scale = 2.3 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 6, -12), light = { range = 10, brightness = 0.6, color = Color3.fromHex("FF70A0") } },
		{ at = Vector3.new(0, 14, 4), light = { range = 10, brightness = 0.5, color = Color3.fromHex("FFF0B0") } },
	},
})

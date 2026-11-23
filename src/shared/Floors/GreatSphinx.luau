--!strict
-- Этаж «Большой Сфинкс» (одиннадцатая партия новых этажей, 2026-11-22).
-- Замысел: этаж — каирский базар у плато Гизы. Снаружи — охристые стены с деревянными решётчатыми эркерами-
-- машрабия на кронштейнах, стрельчатые арки лавок с полосатыми навесами, гирлянды цветных фонарей, ковры на
-- перилах, горки специй в мешках (конусы красного, жёлтого, зелёного), медные кувшины и подносы, корзины с
-- финиками, ослик-тележка (только телега с колёсами и грузом), на крыше — силуэт пирамиды-вывески. Внутри — крытый
-- рынок: ряды прилавков со специями и фонарями, свисающие ковры, гирлянды фонарей под потолком, медная посуда на
-- стенах, пуфы и низкие столики; экспонат — на круглом ковровом помосте с медной каймой.
-- Геометрия — scripts/blender/floor_bazaar.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: круглый ковровый помост.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "GreatSphinx",
	poche = Color3.fromHex("3A2A22"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.8, 3.8, 0, 1.0, -6.8, 0.8, "Rug"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.0, -3), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 12, -8), light = { range = 10, brightness = 0.6, color = Color3.fromHex("FF9050") } },
		{ at = Vector3.new(-12, 6, 4), light = { range = 9, brightness = 0.4, color = Color3.fromHex("60E0B0") } },
	},
})

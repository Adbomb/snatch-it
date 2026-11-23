--!strict
-- Этаж «Египетская кошка» (одиннадцатая партия новых этажей, 2026-11-22).
-- Замысел: этаж — храм богини-кошки Бастет на берегу Нила. Снаружи — белёные стены с голубыми и золотыми поясами,
-- вход между двумя колоннами-папирусами с лотосовыми капителями, над входом — крылатый солнечный диск, по сторонам
-- — статуи сидящих кошек на постаментах (силуэты без лиц), деревянная пристань с папирусной лодкой, полоса воды,
-- заросли папируса, лотосы, корзины с рыбой, амфоры. Внутри — внутренний двор храма: бассейн с лотосами, ряды
-- корзин-лежанок с подушками, курильницы, роспись с кошками и рыбками по стенам, пальмовые балки; экспонат — на
-- круглом голубом постаменте с золотым кольцом-ошейником.
-- Геометрия — scripts/blender/floor_bastet.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: голубой барабан с золотым кольцом.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "EgyptianCat",
	poche = Color3.fromHex("1E3A6A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.8, 3.8, 0, 1.4, -6.8, 0.8, "Drum"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.4, -3), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 3, -12), light = { range = 9, brightness = 0.5, color = Color3.fromHex("90D0FF") } },
		{ at = Vector3.new(-12, 6, -4), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFE0A0") } },
	},
})

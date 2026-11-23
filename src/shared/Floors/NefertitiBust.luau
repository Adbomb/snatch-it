--!strict
-- Этаж «Бюст Нефертити» (одиннадцатая партия новых этажей, 2026-11-22).
-- Замысел: этаж — мастерская скульптора в солнечном городе Амарна. Снаружи — светлая вилла с белыми стенами и
-- голубыми колоннами-пальмами на веранде, над входом — большой солнечный диск Атона с расходящимися лучами,
-- заканчивающимися ладошками, синий пояс с жёлтыми ромбами, на веранде — заготовки из камня, лестница, корзины,
-- пальмы в кадках, колодец-шадуф с журавлём, грядки. Внутри — мастерская: подставки-станки с недоделанными
-- скульптурами (абстрактные головы и вазы без лиц), полки с банками красок и кистями, глыбы известняка,
-- инструменты на стене (резцы, молотки), эскизы на доске, лучи Атона на потолке; экспонат — на синем постаменте-
-- кубе с золотой каймой (как музейная тумба).
-- Геометрия — scripts/blender/floor_amarna.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: синяя тумба-куб с золотой каймой.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "NefertitiBust",
	poche = Color3.fromHex("2A3A6A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.0, 3.0, 0, 2.0, -6.0, 0.0, "Plinth"),
		}
	end,
	exhibit = { at = Vector3.new(0, 2.0, -3), yaw = 180, scale = 3.0 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 16, -3), light = { range = 10, brightness = 0.5, color = Color3.fromHex("FFD070") } },
		{ at = Vector3.new(12, 6, -6), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFF0C8") } },
	},
})

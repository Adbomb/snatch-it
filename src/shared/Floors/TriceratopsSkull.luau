--!strict
-- Этаж «Череп трицератопса» (одиннадцатая партия новых этажей, 2026-11-22).
-- Замысел: этаж — раскоп в красных бэдлендах. Снаружи весь фасад — полосатая столовая гора (слои красного,
-- охристого и кремового песчаника уступами), в скале — раскоп с сеткой из верёвок и торчащими костями (рёбра,
-- позвонки, рог), деревянный кран-укосина поднимает гипсовый «кокон» с костью, лестница-стремянка, палатка
-- экспедиции с флажком, ящики с инструментами, тачка, сито на козлах, кактус и перекати-поле. Внутри — полевая
-- лаборатория: длинные столы с гипсовыми коконами и кисточками, стеллажи с подписанными костями, карта слоёв на
-- стене, лампы-переноски, стенд с позвонками; экспонат — на «пласте» из трёх слоёв песчаника.
-- Геометрия — scripts/blender/floor_badlands.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: пласт из трёх слоёв песчаника.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "TriceratopsSkull",
	poche = Color3.fromHex("5A3A2A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.4, 4.4, 0, 0.5, -7.4, 1.4, "Layer1"),
			box(-4.0, 4.0, 0.5, 1.0, -7.0, 1.0, "Layer2"),
			box(-3.6, 3.6, 1.0, 1.5, -6.6, 0.6, "Layer3"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.5, -3), yaw = 180, scale = 2.4 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 6, -12), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFB070") } },
		{ at = Vector3.new(12, 6, -4), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFE8C0") } },
	},
})

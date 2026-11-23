--!strict
-- Этаж «Улитка-метро» (пятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — старая станция метро. Снаружи — вестибюль в белой «метро»-плитке с синим и жёлтым поясами,
-- большие арочные окна в зелёных чугунных рамах, вход в подземку — лестница вниз под стеклянным козырьком на
-- чугунных опорах, у входа — столб-указатель с цветным диском, круглые часы, карта линий, скамья, автомат с
-- жетонами; бока — вагоны метро вдоль стен (синие, с окнами, дверями и полосой); сзади — пути и светофор. Внутри —
-- подземная платформа: плиточные стены с поясами, колонны, у дальней стены — вагон с открытыми дверями на путях,
-- жёлтая линия края, скамьи, табло, часы над путями, карта линий, турникеты у лифта, лампы-шары; экспонат — на
-- круглом плиточном островке с жёлтой кромкой и кольцом рельсов.
-- Геометрия — scripts/blender/floor_metro.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: круглый плиточный островок.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "SubwaySnail",
	poche = Color3.fromHex("22242C"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.8, 3.8, 0, 1.4, -6.8, 0.8, "Island"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.4, -3), yaw = 180, scale = 2.6 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 4, -12), light = { range = 10, brightness = 0.5, color = Color3.fromHex("FFE0A0") } },
		{ at = Vector3.new(-12, 8, 4), light = { range = 9, brightness = 0.4, color = Color3.fromHex("C8E0FF") } },
	},
})

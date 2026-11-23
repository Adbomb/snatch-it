--!strict
-- Этаж «Кактус-великан» (десятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — викторианская оранжерея пустынных растений. Снаружи — стеклянные стены в белом чугунном
-- переплёте, выступающий центральный ризалит с высокой арочной дверью и полукруглым окном-«веером», пилястры с
-- вазонами, ажурный парапет с шишечками; перед оранжереей — каменистый сад: кактусы-колонны, шары и опунции,
-- валуны, гравийная дорожка, табличка на столбике, тачка с горшками. Внутри — пустынный сад под белыми арочными
-- рёбрами: песчаные грядки с кактусами разных видов, валуны, сухое русло с мостиком, каменная тропа, таблички,
-- скамья; экспонат — в круглой каменной клумбе с песком и галькой.
-- Геометрия — scripts/blender/floor_cactushouse.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: каменная клумба с песком.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "GiantCactus",
	poche = Color3.fromHex("5A7A6A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.8, 3.8, 0, 1.4, -6.8, 0.8, "Bed"),
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
		{ at = Vector3.new(0, 15, -12), light = { range = 10, brightness = 0.5, color = Color3.fromHex("FFF4D0") } },
		{ at = Vector3.new(-12, 6, -6), light = { range = 9, brightness = 0.4, color = Color3.fromHex("D0FFC0") } },
	},
})

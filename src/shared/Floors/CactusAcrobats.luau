--!strict
-- Этаж «Кактусы-акробаты» (девятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — цирк шапито. Снаружи — стены в красно-белую полоску, под карнизом — фестоны жёлто-синих
-- треугольников, красная скатная крыша с белыми полосами, на углах — мачты с вымпелами, вход-арка с лампочками, по
-- бокам — тумбы-барабаны со звёздами, билетная будка с круглой крышей, пушка для акробатов, афиши со звёздами и
-- кактусом, флажки. Внутри — манеж: шатёр-купол из полосатых клиньев под потолком, красный барьер манежа, опилки,
-- трибуны-ступени вдоль стен, трапеция на канатах, канат между двумя мачтами, прожекторы, гирлянды звёзд; экспонат
-- — на цирковой тумбе-барабане в полоску со звёздами.
-- Геометрия — scripts/blender/floor_circus.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: цирковая тумба-барабан.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "CactusAcrobats",
	poche = Color3.fromHex("2A1E3A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.0, 3.0, 0, 1.8, -6.0, 0.0, "Drum"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.8, -3), yaw = 180, scale = 2.6 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 6, -3), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFC070") } },
		{ at = Vector3.new(0, 12, -12), light = { range = 10, brightness = 0.4, color = Color3.fromHex("FFE8C0") } },
	},
})

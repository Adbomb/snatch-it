--!strict
-- Этаж «Конус-паникёр» (пятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — стройка, которую охраняют конусы. Снаружи — недостроенный дом: бетонный каркас с рядами кладки,
-- по фасаду — леса из жёлтых труб с дощатыми настилами и оранжевой сеткой, на крыше — башенный кран-малыш со
-- стрелой и крюком, на крюке — поддон с конусами, у фасада — бетонные блоки-ограждения в красно-белую полосу,
-- мигалки, конусы, тачка, бетономешалка; бока — леса и штабеля кирпича; сзади — кучи песка и трубы. Внутри — голый
-- каркас: бетонный пол с меловой разметкой, жёлтые двутавровые колонны и балки, вышка-тура лесов, поддоны кирпича,
-- мешки цемента, каски, ящик с инструментами, прожекторы на треногах, лампы на проводах, лента «осторожно»;
-- экспонат — на стопке поддонов с жёлто-чёрной кромкой и конусами по углам.
-- Геометрия — scripts/blender/floor_construction.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: стопка поддонов.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "PanicCone",
	poche = Color3.fromHex("3A3830"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.2, 3.2, 0, 1.18, -5.8, -0.2, "Pallets"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.18, -3), yaw = 180, scale = 2.8 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(-12, 5, -10), light = { range = 10, brightness = 0.6, color = Color3.fromHex("FFF0C0") } },
		{ at = Vector3.new(12, 5, -10), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFB060") } },
	},
})

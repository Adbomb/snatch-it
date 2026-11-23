--!strict
-- Этаж «Фенек-лопоух» (девятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — радиостанция «Большое ухо» в пустыне. Снаружи — песочный саман с синими наличниками и голубой
-- полосой, длинное окно аппаратной с жалюзи, на правом углу — решётчатая мачта с красно-белыми поясами и красным
-- огнём, слева — большая тарелка антенны на решётчатой опоре, рупоры-громкоговорители на кронштейнах, кабели по
-- стене, у входа — генератор, ящики, бочка с водой и солнечные панели на стойках. Внутри — аппаратная: пульты с
-- ручками и тумблерами вдоль стен, ряды экранов с волнами, стойки с катушками, карта эфира, лотки кабелей под
-- потолком; экспонат — на круглой тумбе-тарелке с наушниками на стойке.
-- Геометрия — scripts/blender/floor_radio.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: синий барабан с вогнутой чашей.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "FloppyFennec",
	poche = Color3.fromHex("2A3040"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.6, 3.6, 0, 1.2, -6.6, 0.6, "Dais"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.2, -3), yaw = 180, scale = 2.6 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 6, -10), light = { range = 9, brightness = 0.5, color = Color3.fromHex("80F0C0") } },
		{ at = Vector3.new(-12, 8, -4), light = { range = 9, brightness = 0.4, color = Color3.fromHex("C8E0FF") } },
	},
})

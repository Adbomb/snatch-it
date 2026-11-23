--!strict
-- Этаж «Скорпион-лейка» (девятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — садовый центр. Снаружи — шалфейно-зелёный дощатый магазин с белыми наличниками, слева —
-- стеклянная пристройка-оранжерея в белых рамах со скатной крышей, витрина с пирамидой терракотовых горшков, дверь
-- с полукруглым верхом, шпалера с вьющимися розами, ящики с цветами под окнами, вывеска-лейка, стойка с лейками,
-- тачка с землёй, катушка шланга, мешки грунта, кусты в кадках, белый штакетник. Внутри — торговый зал: столы-
-- стеллажи с рядами горшков и рассады, подвесные корзины с ампельными цветами, стена-перфорация с лейками и
-- инструментами, высокие кадки с кактусами, штабель мешков, полки с пакетиками семян; экспонат — на огромном
-- терракотовом горшке с землёй и цветами по краю.
-- Геометрия — scripts/blender/floor_garden.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: огромный терракотовый горшок.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "CanScorpion",
	poche = Color3.fromHex("3A4A3A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.6, 3.6, 0, 1.8, -6.6, 0.6, "Pot"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.8, -3), yaw = 180, scale = 3.4 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(-12, 6, -6), light = { range = 9, brightness = 0.5, color = Color3.fromHex("D0FFC0") } },
		{ at = Vector3.new(12, 8, -6), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFF0D0") } },
	},
})

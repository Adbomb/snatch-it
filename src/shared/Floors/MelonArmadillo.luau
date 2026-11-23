--!strict
-- Этаж «Арбуз-броненосец» (девятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — крытый бахчевой рынок. Снаружи — жёлто-зелёный рыночный павильон с крупной кирпичной кладкой и
-- арками-воротами, над входом — огромная вывеска-ломоть арбуза с семечками, по фасаду — прилавки под полосатыми
-- тентами на шестах, пирамиды арбузов и дынь в ящиках, тележка с арбузами, весы с гирями, ящики-лотки, мешки.
-- Внутри — рыночный зал: ряды прилавков с горками арбузов и дынь, висящие весы, гирлянды из сеток с дынями,
-- полосатые тенты над рядами, ящики штабелями, грифельные доски с ломтиками-ценниками; экспонат — на гигантской
-- половинке арбуза (зелёная корка, красная мякоть с семечками).
-- Геометрия — scripts/blender/floor_melon.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: огромная половинка арбуза.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "MelonArmadillo",
	poche = Color3.fromHex("3A4A2A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.8, 3.8, 0, 1.6, -6.8, 0.8, "Melon"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.6, -3), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 8, -12), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFD890") } },
		{ at = Vector3.new(-12, 8, -4), light = { range = 9, brightness = 0.4, color = Color3.fromHex("C0FFB0") } },
	},
})

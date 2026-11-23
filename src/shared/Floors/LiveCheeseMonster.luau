--!strict
-- Этаж «Живой сыр-монстр» (пятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — альпийская сыроварня. Снаружи — шале: белёный каменный низ, верх из тёмных брёвен, резной
-- деревянный балкон с ящиками красной герани, широкий свес крыши с резными кронштейнами и снежной кромкой, арочная
-- каменная дверь в погреб, у входа — башня из сырных голов, огромный сырный клин-вывеска с дырками, колокольчик,
-- бидоны молока, альпийский рог; бока — поленницы и ставни с ромбическими прорезями; сзади — тележка с бидонами.
-- Внутри — сырный погреб: каменные стены со сводчатыми нишами, деревянные стеллажи с головками сыра, медный котёл
-- над огнём, стол с фондю, клинья сыра, фонари, бочки; экспонат — на огромной сырной голове на деревянной доске-
-- подставке.
-- Геометрия — scripts/blender/floor_cheese.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: доска-подставка и огромная сырная голова.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "LiveCheeseMonster",
	poche = Color3.fromHex("3A3430"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.6, 4.6, 0, 0.35, -7.2, 1.2, "Board"),
			box(-3.6, 3.6, 0.35, 1.2, -6.6, 0.6, "Wheel"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.2, -3), yaw = 180, scale = 2.5 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(8, 3, -12), light = { range = 10, brightness = 0.6, color = Color3.fromHex("FF9A50") } },
		{ at = Vector3.new(-9, 8, -10), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFE0A0") } },
	},
})

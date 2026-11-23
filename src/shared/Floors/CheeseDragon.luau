--!strict
-- Этаж «Сырный дракон» (десятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — альпийская сыроварня у драконьей пещеры. Снаружи — шале: каменный цоколь из крупных валунов,
-- деревянный верх с резным балконом, ящики с красной геранью, глубокий свес крыши на резных кронштейнах, кованая
-- вывеска-дракон с висящей головкой сыра, справа — вход в пещеру с каменной аркой и золотыми «чешуйками», тележка
-- с головками сыра, бидоны, колокольчик, поленница. Внутри — сырный погреб: каменные своды, стеллажи от пола до
-- потолка с головками сыра, медный чан с мешалкой, гнездо с золотыми драконьими яйцами в соломе, драконья чешуя-
-- мозаика на дальней стене, фонари; экспонат — на гигантской головке сыра с дырками.
-- Геометрия — scripts/blender/floor_cheesedragon.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: гигантская головка сыра.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "CheeseDragon",
	poche = Color3.fromHex("4A4038"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.8, 3.8, 0, 1.8, -6.8, 0.8, "Cheese"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.8, -3), yaw = 180, scale = 2.3 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(-7, 3, -12), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FFC040") } },
		{ at = Vector3.new(12, 8, -6), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFE0A0") } },
	},
})

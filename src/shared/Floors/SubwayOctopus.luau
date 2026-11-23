--!strict
-- Этаж «Подземный осьминог» (пятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — затонувшая станция метро, ставшая океанариумом. Снаружи — клёпаная сталь цвета морской волны с
-- медными поясами, огромное панорамное стекло-аквариум с водой, рыбами, кораллами и водорослями, по фасаду из люка
-- на тротуаре выползают и обвивают здание огромные фиолетовые щупальца с присосками, вокруг — якорь на цепи, буи,
-- трубы; бока — ряды иллюминаторов с пузырями; сзади — водолазный колокол. Внутри — подводный зал: стены-аквариумы
-- с рыбами, коралловый риф (ветвистые кораллы, веера, губки), водоросли до потолка, затонувший вагон метро в
-- песке, сундук с монетами, пузыри; экспонат — на огромном открытом люке, обросшем кораллами и ракушками.
-- Геометрия — scripts/blender/floor_aquarium.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: огромный открытый люк.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "SubwayOctopus",
	poche = Color3.fromHex("1A2630"),
	tones = { glowIn = Color3.fromHex("D0D0D0") }, -- свечение зала приглушено: без пересвета
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.9, 3.9, 0, 1.2, -6.9, 0.9, "Manhole"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.2, -3), yaw = 180, scale = 2.4 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 8, -12), light = { range = 10, brightness = 0.6, color = Color3.fromHex("6AD0FF") } },
		{ at = Vector3.new(-10, 6, 4), light = { range = 9, brightness = 0.4, color = Color3.fromHex("B080FF") } },
	},
})

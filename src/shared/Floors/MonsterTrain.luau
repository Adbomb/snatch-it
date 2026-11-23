--!strict
-- Этаж «Поезд-монстр» (восьмая партия новых этажей, 2026-11-22).
-- Замысел: этаж — паровозное депо. Снаружи — кирпичный корпус с белыми арками трёх въездов для паровозов, над ними
-- — круглые часы и пояс-карниз; перед фасадом по рельсам на шпалах стоит паровоз боком — чёрный котёл, труба,
-- сухопарник, будка машиниста, красные колёса с дышлами и путеочиститель; на правом углу — водонапорная башня-бак
-- на ножках с хоботом, рядом — семафор с поднятым крылом и куча угля. Внутри — цех депо: рельсы через весь зал,
-- поворотный круг-постамент, на домкратах — второй котёл в ремонте, колёсные пары у стены, верстаки и стена с
-- ключами, кран-балка с крюком, кучи угля, фонари; экспонат — на поворотном круге с рельсами.
-- Геометрия — scripts/blender/floor_depot.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: поворотный круг с рельсами.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "MonsterTrain",
	poche = Color3.fromHex("3A3430"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.5, 4.5, 0, 0.9, -7.5, 1.5, "Turntable"),
		}
	end,
	exhibit = { at = Vector3.new(0, 0.9, -3), yaw = 180, scale = 2.6 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(-11, 6, -8), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FF9A50") } },
		{ at = Vector3.new(0, 10, -12), light = { range = 10, brightness = 0.4, color = Color3.fromHex("FFE8C0") } },
	},
})

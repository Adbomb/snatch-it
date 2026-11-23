--!strict
-- Этаж «Пицца-НЛО» (десятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — пиццерия-закусочная в стиле космической эры 50-х. Снаружи — бирюзово-кремовая закусочная с
-- наклонными стёклами, крыша-«бумеранг» с козырьком, над входом — летающая тарелка-вывеска с куполом и огнями,
-- рядом — огромный ломоть пиццы с пепперони, звёзды-«спутники», хромированные полосы, окно выдачи с прилавком,
-- табуреты-грибки, ракета-флюгер на стойке, шахматный цоколь. Внутри — зал: красные диваны-кабинки со столиками,
-- стойка с табуретами, кирпичная печь-купол с огнём, музыкальный автомат, шахматный пол, лампы-«спутники», планеты
-- на нитях; экспонат — на огромной пицце на подставке.
-- Геометрия — scripts/blender/floor_pizzaufo.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: огромная пицца на хромированной подставке.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "PizzaUfo",
	poche = Color3.fromHex("2A3A48"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.8, 3.8, 1.15, 1.6, -6.8, 0.8, "Pizza"),
			box(-1.5, 1.5, 0, 1.15, -4.5, -1.5, "Stand"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.6, -3), yaw = 180, scale = 2.6 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(-7, 3, -12), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FF9040") } },
		{ at = Vector3.new(10, 10, -4), light = { range = 9, brightness = 0.4, color = Color3.fromHex("80F0FF") } },
	},
})

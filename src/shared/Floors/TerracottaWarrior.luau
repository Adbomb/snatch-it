--!strict
-- Этаж «Терракотовый воин» (вторая партия новых этажей, 2026-11-21).
-- Замысел: этаж — императорский павильон над раскопом. Снаружи — белая терраса с
-- балюстрадой, красные колонны, решётчатые окна, доугуны, двухъярусная крыша с загнутыми углами, красные
-- врата с гвоздями, фонари. Внутри — раскоп: траншеи с рядами воинов без лиц, слои глины, красная галерея,
-- кессонный потолок, воин на белом постаменте, бронзовые треножники, фонари.
-- Геометрия — scripts/blender/floor_terracotta.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: постамент, земляные перегородки траншей и передний вал.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "TerracottaWarrior",
	poche = Color3.fromHex("3E2818"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.8, 4.8, 0, 0.7, -6.2, 2.2, "Base"),
			box(-4, 4, 0.7, 1.4, -5.4, 1.4, "Top"),
			box(-16.2, -14.8, 0, 2.1, -14.88, 4, "Trench1"),
			box(-11.2, -9.8, 0, 2.1, -14.88, 4, "Trench2"),
			box(9.8, 11.2, 0, 2.1, -14.88, 4, "Trench3"),
			box(14.8, 16.2, 0, 2.1, -14.88, 4, "Trench4"),
			box(-16.88, 16.88, 0, 1.9, -15.88, -13.48, "Rampart"),
			box(-6.3, 6.3, 1.9, 10.3, -13.93, -13.48, "Screen"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.4, -2), yaw = 180, scale = 3.4 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.55, color = Color3.fromHex("FFD8B8") } },
		{
			at = Vector3.new(0, 15, -2),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF2E0"), spot = 50 },
		},
		{ at = Vector3.new(0, 7, 5), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF0E0") } },
		{ at = Vector3.new(-4.5, 13.5, -7), light = { range = 8, brightness = 0.5, color = Color3.fromHex("FF4A3A") } },
		{ at = Vector3.new(4.5, 13.5, 3), light = { range = 8, brightness = 0.5, color = Color3.fromHex("FF4A3A") } },
	},
})

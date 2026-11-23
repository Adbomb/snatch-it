--!strict
-- Этаж «Кристальный скорпион» (десятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — кристальная шахта в скале. Снаружи — скальный фасад из слоёв песчаника, деревянный портал
-- штольни с подпорками и вывеской-киркой, из штольни выходят рельсы с вагонеткой, полной самоцветов, на скале —
-- друзы кристаллов (фиолетовые, голубые, розовые), фонари на крюках, кирки и лопаты у стены, бочки, тачка с рудой,
-- леса-подъёмник с блоком и ведром. Внутри — пещера-жеода: стены с кристальными друзами, деревянные крепи-рамы
-- вдоль зала, рельсы с вагонеткой, светящиеся кристаллы-колонны, ящики с камнями, лампы на проводе; экспонат — на
-- половинке огромной жеоды: тёмная корка и кольцо кристаллов.
-- Геометрия — scripts/blender/floor_crystalmine.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: половинка жеоды с кристаллами.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "CrystalScorpion",
	poche = Color3.fromHex("40364A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.9, 3.9, 0, 1.4, -6.9, 0.9, "Geode"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.4, -3), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 4, -12), light = { range = 10, brightness = 0.7, color = Color3.fromHex("B080FF") } },
		{ at = Vector3.new(-12, 6, -6), light = { range = 9, brightness = 0.5, color = Color3.fromHex("60D8FF") } },
	},
})

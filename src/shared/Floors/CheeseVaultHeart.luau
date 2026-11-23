--!strict
-- Этаж «Сердце сырного хранилища» (десятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — сырный завод. Снаружи — цех из светло-жёлтого профлиста с рёбрами, пилообразный фронтон, большая
-- подъёмная дверь у погрузочной рампы с жёлто-чёрными полосами, конвейер выходит из стены и несёт сырные бруски к
-- кузову грузовичка, справа — два стальных молочных бака с трубой и лесенкой, труба-дымоход, вывеска-ломоть сыра с
-- дырками, поддоны с ящиками, погрузчик. Внутри — производственный цех: два стальных чана с мешалками и мостками,
-- трубы под потолком, конвейер вдоль стены с сырными головками и брусками, стеллажи созревания, пульт с
-- лампочками, полосы безопасности на полу; экспонат — на «сердце хранилища»: стальном барабане с жёлтым светящимся
-- кольцом, болтами и трубами.
-- Геометрия — scripts/blender/floor_cheesefactory.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: стальной барабан с жёлтым кольцом.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "CheeseVaultHeart",
	poche = Color3.fromHex("4A5058"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.8, 3.8, 0, 1.6, -6.8, 0.8, "Heart"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.6, -3), yaw = 180, scale = 2.4 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 2, -3), light = { range = 8, brightness = 0.6, color = Color3.fromHex("FFE070") } },
		{ at = Vector3.new(0, 10, -12), light = { range = 10, brightness = 0.4, color = Color3.fromHex("E8F4FF") } },
	},
})

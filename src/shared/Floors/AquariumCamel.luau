--!strict
-- Этаж «Верблюд-аквариум» (девятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — океанариум посреди пустыни. Снаружи — тёмно-синий фасад с бирюзовыми поясами-волнами, ряд из
-- пяти иллюминаторов, стеклянный вход под козырьком-волной, над ним — большая рыба-скульптура с плавниками и
-- пузырями, по углам — хвост кита из песка и якорь с цепью, кадки с кораллами, буй. Внутри — тёмный зал: большие
-- аквариумы во всю стену с рыбками, водорослями и кораллами, медузы-светильники под потолком, своды-рёбра
-- «подводного туннеля», скамьи; экспонат — на круглом рифе из кораллов с водяным кольцом.
-- Геометрия — scripts/blender/floor_aquarium.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: коралловый риф с водяным кольцом.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "AquariumCamel",
	poche = Color3.fromHex("142A52"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.8, 3.8, 0, 0.5, -6.8, 0.8, "Reef"),
			box(-2.7, 2.7, 0.5, 1.3, -5.7, -0.3, "Rock"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.3, -3), yaw = 180, scale = 2.8 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(-12, 6, -4), light = { range = 10, brightness = 0.6, color = Color3.fromHex("60C8FF") } },
		{ at = Vector3.new(12, 6, -4), light = { range = 10, brightness = 0.6, color = Color3.fromHex("60C8FF") } },
	},
})

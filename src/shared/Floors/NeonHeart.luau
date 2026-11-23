--!strict
-- Этаж «Сердце из неона» (третья партия новых этажей, 2026-11-21).
-- Замысел: этаж — ночной клуб в стиле синтвейв. Снаружи — тёмные панели с хромовыми рёбрами, ретро-солнце в
-- полосах над неоновой сеткой, сердце-вывеска, неоновые пальмы, двери в рамке из лампочек, хромовые пилоны,
-- неоновый эквалайзер на боках, колонки сзади. Внутри — светодиодный танцпол, две неоновые арки от лифта,
-- зеркальный шар, бархатные диваны, пульт диджея, ретро-солнце с горами-сеткой за экспонатом.
-- Геометрия — scripts/blender/floor_neonheart.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: постамент из двух ступеней.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "NeonHeart",
	poche = Color3.fromHex("1E1430"),
	tones = { glowIn = Color3.fromHex("C8C8C8") }, -- свечение зала приглушено: без пересвета
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4, 4, 0, 0.6, -7.6, -0.4, "Base"),
			box(-3.3, 3.3, 0.6, 1.2, -7, -1, "Top"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.2, -4), yaw = 180, scale = 3.0 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.5, color = Color3.fromHex("E0C8FF") } },
		{
			at = Vector3.new(0, 15, -4),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFE8F4"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.7, color = Color3.fromHex("FFF0F8") } },
		{ at = Vector3.new(-12, 6, -6), light = { range = 10, brightness = 0.6, color = Color3.fromHex("FF2E7E") } },
		{ at = Vector3.new(12, 6, -6), light = { range = 10, brightness = 0.6, color = Color3.fromHex("3FE6FF") } },
	},
})

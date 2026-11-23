--!strict
-- Этаж «Кристальный динозавр» (вторая партия новых этажей, 2026-11-21).
-- Замысел: этаж — расколотая жеода. Снаружи — тёмная гранёная скала со светящимися
-- жилами, друзы кристаллов на углах и по краю, пасть жеоды в кольце кристаллов, окаменелые следы. Внутри —
-- кристальная пещера: друзы из стен и пола, кристаллы-сосульки, светящиеся озерца, тропа и следы, постамент
-- с короной кристаллов.
-- Геометрия — scripts/blender/floor_crystal.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: постамент из двух ступеней.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "CrystalDino",
	poche = Color3.fromHex("241E34"),
	tones = { glowIn = Color3.fromHex("D0D0D0") }, -- свечение зала приглушено: без пересвета
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.4, 4.4, 0, 0.7, -7.4, 1.4, "Base"),
			box(-3.6, 3.6, 0.7, 1.3, -6.6, 0.6, "Top"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.3, -3), yaw = 180, scale = 2.5 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.5, color = Color3.fromHex("D8C8FF") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.4, color = Color3.fromHex("F4F0FF"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("F4F4FF") } },
		{ at = Vector3.new(-10, 4, -4), light = { range = 10, brightness = 0.6, color = Color3.fromHex("4FD8F0") } },
		{ at = Vector3.new(10.5, 4, -6), light = { range = 10, brightness = 0.6, color = Color3.fromHex("A66CFF") } },
	},
})

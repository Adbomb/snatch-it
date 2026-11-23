--!strict
-- Этаж «Проклятый телевизор» (третья партия новых этажей, 2026-11-21).
-- Замысел: этаж — дом с привидениями из 80-х. Снаружи — сиреневый сайдинг на каменном цоколе, мансарда с
-- телеантеннами, несимметричные окна (эркер с голубым «снегом», заколоченное, круглое чердачное), крыльцо с
-- навесом, штакетник, тыквы без лиц, сухое дерево, кирпичная труба, гора старых телевизоров. Внутри — гостиная
-- 80-х: панели и обои, диван-авокадо, кресло, торшер, кассеты, проигрыватель, пустые рамы, парящие стул и книги,
-- голубое свечение вокруг тумбы с экспонатом.
-- Геометрия — scripts/blender/floor_cursedtv.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: тумба под телевизор из двух ступеней.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "CursedTV",
	poche = Color3.fromHex("3A3448"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4, 4, 0, 0.7, -7.4, -0.6, "Cabinet1"),
			box(-3.4, 3.4, 0.7, 1.4, -6.8, -1.2, "Cabinet2"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.4, -4), yaw = 180, scale = 2.8 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.5, color = Color3.fromHex("E8E0FF") } },
		{
			at = Vector3.new(0, 15, -4),
			light = { range = 18, brightness = 2.2, color = Color3.fromHex("E8F0FF"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.7, color = Color3.fromHex("F4F0FF") } },
		{ at = Vector3.new(0, 3, 0), light = { range = 10, brightness = 0.8, color = Color3.fromHex("7AA0FF") } },
		{ at = Vector3.new(13.7, 6.5, 8.7), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FFD27A") } },
	},
})

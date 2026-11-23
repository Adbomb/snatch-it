--!strict
-- Этаж «Королевская утка» (третья партия новых этажей, 2026-11-21).
-- Замысел: этаж — королевская купальня. Снаружи — белые стены с поясами изразцов, арочные окна с запотевшим
-- стеклом, башенки под золотыми луковичными куполами, огромный золотой кран (один вентиль) льёт воду в раковину-
-- фонтан с утятами и пеной, корона, балкончики с полотенцами, медный котёл. Внутри — бассейн с утятами и пеной,
-- мостик к острову-постаменту, золотой кран и корона за островом, колонны, ниши с полотенцами и мылом.
-- Геометрия — scripts/blender/floor_bathhouse.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: остров из двух ступеней, мостик и четыре колонны.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "RoyalDuck",
	poche = Color3.fromHex("E2E6EE"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4, 4, 0, 0.7, -7, 1, "Island1"),
			box(-3.3, 3.3, 0.7, 1.4, -6.3, 0.3, "Island2"),
			box(-2.2, 2.2, 0, 0.55, 0, 5.9, "Bridge"),
			box(-13.2, -11.6, 0, 12, -13.2, -11.6, "Column1"),
			box(11.6, 13.2, 0, 12, -13.2, -11.6, "Column2"),
			box(-13.2, -11.6, 0, 12, 5.6, 7.2, "Column3"),
			box(11.6, 13.2, 0, 12, 5.6, 7.2, "Column4"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.4, -3), yaw = 180, scale = 2.8 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("F0F8FF") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8E8"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF8F0") } },
		{ at = Vector3.new(-7, 3, -6), light = { range = 9, brightness = 0.5, color = Color3.fromHex("8AD8F4") } },
		{ at = Vector3.new(7, 3, -6), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFD27A") } },
	},
})

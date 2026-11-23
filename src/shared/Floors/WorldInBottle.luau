--!strict
-- Этаж «Мир в бутылке» (вторая партия новых этажей, 2026-11-21).
-- Замысел: этаж — корма старинного галеона. Снаружи (v2) — корпус из досок над волнами, руль, кормовой
-- балкон с балясинами, два яруса окон в золочёных рамах, резной гакаборт с розой ветров и тремя фонарями,
-- кормовые галереи-башенки с куполами на бортах, пушечные порты с пушками, ванты с выбленками, якорь,
-- спасательные круги, шлюпки. Внутри — каюта капитана: кормовые окна с морем и закатом, полки с
-- бутылками-кораблями, штурвал,
-- стол с картой и глобусом, сундук, канаты, фонари, стол-тумба с латунной подставкой.
-- Геометрия — scripts/blender/floor_bottle.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: стол-тумба и стол с картой.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "WorldInBottle",
	poche = Color3.fromHex("4A2E1C"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4, 4, 0, 0.6, -7, 1, "Table1"),
			box(-3.4, 3.4, 0.6, 1.4, -6.4, 0.4, "Table2"),
			box(7, 13, 0, 2.9, 2, 6, "MapTable"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.4, -3), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.55, color = Color3.fromHex("FFE0B8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF2E0"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF0E0") } },
		{ at = Vector3.new(-6, 12.5, -8), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFB040") } },
		{ at = Vector3.new(6, 12.5, -8), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFB040") } },
	},
})

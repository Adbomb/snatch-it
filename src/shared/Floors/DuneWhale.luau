--!strict
-- Этаж «Кит-бархан» (десятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — клуб песчаных яхт на краю дюн. Снаружи — бело-синий эллинг из досок с широкими воротами под
-- двускатным фронтоном, во фронтоне — штурвал-эмблема, по бокам — медные хвосты кита, ряды круглых окошек-
-- иллюминаторов, мачта с сигнальными флажками, у ворот — две песчаные яхты на колёсах с парусами, бухты каната,
-- якорь, буи, спасательные круги на стене, песок волнами. Внутри — парусная мастерская: паруса и флаги под
-- потолком, корпус лодки на стапеле из рёбер-шпангоутов, стол с картой дюн и компасом, модели яхт на полках, бухты
-- канатов, вёсла на стене; экспонат — на «волне» из песка с палубными досками.
-- Геометрия — scripts/blender/floor_yacht.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: песчаная волна на палубных досках.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "DuneWhale",
	poche = Color3.fromHex("2A3A5A"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.8, 3.8, 0, 0.4, -6.8, 0.8, "Base"),
			box(-3.2, 3.2, 0.4, 1.2, -6.2, 0.2, "Wave"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.2, -3), yaw = 180, scale = 2.9 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 12, -12), light = { range = 9, brightness = 0.4, color = Color3.fromHex("B0D8FF") } },
		{ at = Vector3.new(12, 6, -6), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFE8C0") } },
	},
})

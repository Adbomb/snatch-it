--!strict
-- Этаж «Сурикат-часовой» (восьмая партия новых этажей, 2026-11-22).
-- Замысел: этаж — маяк на скалистом берегу. Снаружи — дом смотрителя: белая обшивка досками, синие ставни и
-- наличники, сланцевый пояс крыши; на углу — красно-белый маяк сужающейся башней с галереей, светящимся фонарным
-- залом и куполом; внизу — серые валуны вдоль цоколя, вода у скал, лодка на камнях, ловушки для омаров, ящики,
-- сети на стене, у входа — большой латунный телескоп на треноге (дозорный пост). Внутри — комната смотрителя:
-- стены из синих досок, винтовая лестница наверх, огромная линза Френеля из светящихся колец за постаментом, стол
-- с морской картой и компасом, полка с кораблём в бутылке, бочонки, якорь на стене; экспонат — на тёмно-синей
-- тумбе с канатом и латунной каймой.
-- Геометрия — scripts/blender/floor_lighthouse.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: тёмно-синяя тумба с канатом.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "MeerkatLookout",
	poche = Color3.fromHex("1E3050"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.9, 3.9, 0, 1.1, -6.9, 0.9, "Dais"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.1, -3), yaw = 180, scale = 2.8 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 8, -12), light = { range = 10, brightness = 0.6, color = Color3.fromHex("FFE890") } },
		{ at = Vector3.new(-12, 8, -4), light = { range = 9, brightness = 0.4, color = Color3.fromHex("C8E0FF") } },
	},
})

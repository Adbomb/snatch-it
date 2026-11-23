--!strict
-- Этаж «Перекати-поле-бегун» (девятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — салун городка Дикого Запада. Снаружи — дощатый дом с высоким ступенчатым фальш-фасадом, крытая
-- галерея на столбах над дощатым тротуаром с перилами, двери-«крылья» салуна, вывеска с подковой, окна второго
-- яруса с балкончиком, коновязь, корыто с водой, бочки, колесо фургона у стены, кактусы, катящиеся шары перекати-
-- поля. Внутри — салун: длинная стойка с латунной подножкой и полками бутылок перед зеркалом, пианино, круглые
-- столы со стульями, лестница на галерею вдоль дальней стены, звёзды-шерифские значки и подковы на стенах, лампы
-- на цепях; экспонат — на круглой деревянной сцене-бочке, окружённой кольцом перекати-поля.
-- Геометрия — scripts/blender/floor_saloon.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: круглая деревянная сцена-бочка.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "TumbleweedRunner",
	poche = Color3.fromHex("4A3020"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.6, 3.6, 0, 1.4, -6.6, 0.6, "Stage"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.4, -3), yaw = 180, scale = 3.0 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(12, 8, -4), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFB060") } },
		{ at = Vector3.new(-12, 8, 6), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFD8A0") } },
	},
})

--!strict
-- Этаж «Крыса-качок» (пятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — старый боксёрский и силовой зал. Снаружи — кирпичный цех с тёмно-синими стальными рамами,
-- большие окна (за стеклом — силуэты тренажёров), на крыше — огромная гантель-вывеска на стойках, над входом —
-- козырёк с полосами-молниями, у входа — гигантские гири, стопка покрышек, штанга на стойке, груша на кронштейне;
-- бока — флаги- баннеры с молниями, пожарная лестница; сзади — водонапорный бак. Внутри — зал: пол из резиновой
-- плитки с цветной разметкой, вдоль стены — зеркала и стойки с блинами, скамьи со штангами, ряд гантелей на
-- стойке, беговые дорожки, груши на цепях, ринг-канаты по углу, табло; экспонат — на помосте для тяжёлой атлетики
-- (деревянный центр, резиновые края) с огромными блинами по бокам.
-- Геометрия — scripts/blender/floor_gym.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: помост для тяжёлой атлетики.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "BuffRat",
	poche = Color3.fromHex("2A2A34"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.4, 4.4, 0, 1, -6.6, 0.6, "Platform"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.0, -3), yaw = 180, scale = 2.4 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(-12, 6, -6), light = { range = 9, brightness = 0.5, color = Color3.fromHex("FFB070") } },
		{ at = Vector3.new(12, 8, 2), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFE0A0") } },
	},
})

--!strict
-- Этаж «Золотой геймпад» (вторая партия новых этажей, 2026-11-21).
-- Замысел: этаж — дневной ретро-игровой зал. Снаружи — светлые стены, три огромных
-- игровых автомата с пиксельными картинками, неоновая пиксельная лента, фрески из тетрамино и сердца,
-- джойстики на углах. Внутри — игровой зал: ковёр с неоновыми искрами, ряды автоматов, автомат с клешнёй,
-- неоновые трубки, пьедестал-монета, парящие пиксельные сердца и звёзды, горка тетрамино.
-- Геометрия — scripts/blender/floor_gamepad.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: пьедестал-монета, ряды автоматов у стен, автомат с клешнёй.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "GoldenGamepad",
	poche = Color3.fromHex("1E1E4A"),
	tones = { glowIn = Color3.fromHex("C8C8C8") }, -- свечение зала приглушено: без пересвета
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4.4, 4.4, 0, 0.7, -7.4, 1.4, "Coin1"),
			box(-3.8, 3.8, 0.7, 1.4, -6.8, 0.8, "Coin2"),
			box(-16.88, -14.48, 0, 8.6, -14.4, 4.4, "CabinetsL"),
			box(14.48, 16.88, 0, 8.6, -14.4, 4.4, "CabinetsR"),
			box(9.5, 13.5, 0, 9.2, 6.5, 10.5, "Claw"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.4, -3), yaw = 180, scale = 3.2 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.55, color = Color3.fromHex("E8E0FF") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.4, color = Color3.fromHex("FFF8F0"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4F0") } },
		{ at = Vector3.new(-12, 8, -6), light = { range = 10, brightness = 0.5, color = Color3.fromHex("FF8AC0") } },
		{ at = Vector3.new(12, 8, -6), light = { range = 10, brightness = 0.5, color = Color3.fromHex("7CC8FF") } },
	},
})

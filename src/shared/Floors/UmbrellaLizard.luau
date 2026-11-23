--!strict
-- Этаж «Ящерка-зонтик» (девятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — пляжный отель на дюнах. Снаружи — белая штукатурка с округлыми углами, два яруса балконов с
-- бирюзовыми перилами и полосатыми маркизами, панорамные окна лобби, над входом — козырёк-волна, у входа — ряд
-- пляжных зонтов-грибков с шезлонгами, доски для сёрфинга у стены, сумка-холодильник, спасательный круг, пальма,
-- волейбольный мяч. Внутри — пляжный клуб: бассейн в полу с бортиком и лесенкой, шезлонги и столики под зонтами,
-- бар-хижина под соломенной крышей, полосатые кабинки для переодевания, полотенца на крючках, гирлянда флажков;
-- экспонат — на круглом островке в виде полосатого пляжного мяча.
-- Геометрия — scripts/blender/floor_beach.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: островок — полосатый пляжный мяч.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "UmbrellaLizard",
	poche = Color3.fromHex("2A5A60"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.4, 3.4, 0, 1.2, -6.4, 0.4, "Ball"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.2, -3), yaw = 180, scale = 3.0 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 3, -11), light = { range = 9, brightness = 0.5, color = Color3.fromHex("90E0FF") } },
		{ at = Vector3.new(12, 8, 2), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFE0A0") } },
	},
})

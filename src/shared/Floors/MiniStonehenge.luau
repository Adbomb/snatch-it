--!strict
-- Этаж «Мини-Стоунхендж» (третья партия новых этажей, 2026-11-21).
-- Замысел: этаж — меловой холм на рассвете. Снаружи — белый меловой обрыв с поясами кремня, дуга трилитов из серых
-- сарсенов с лишайником, дерновый склон и туман, козырёк с полевыми цветами, по бокам — зелёный холм с меловой
-- фигурой коня, сзади — кольцо деревянных столбов и курган. Внутри — рассвет в каменном круге: панорама неба над
-- грядой холмов, солнце встаёт в разрыве холмов за экспонатом, подкова трилитов, синие камни, кольцевой вал,
-- туман, меловая тропа, фонари друидов.
-- Геометрия — scripts/blender/floor_stonehenge.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: камень-алтарь из двух плит.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "MiniStonehenge",
	poche = Color3.fromHex("4A4A50"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-4, 4, 0, 0.6, -7, 1, "Altar1"),
			box(-3.2, 3.2, 0.6, 1.2, -6.2, 0.2, "Altar2"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.2, -3), yaw = 180, scale = 3.0 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFE6D0") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF4E8"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF0E0") } },
		{ at = Vector3.new(-9, 4, -8), light = { range = 9, brightness = 0.6, color = Color3.fromHex("FFB070") } },
		{ at = Vector3.new(9, 4, -8), light = { range = 9, brightness = 0.5, color = Color3.fromHex("B8A8FF") } },
	},
})

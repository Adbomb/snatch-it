--!strict
-- Этаж «Черепаха-остров» (пятая партия новых этажей, 2026-11-22).
-- Замысел: этаж — тропический пляж с тики-баром. Снаружи — хижина из бамбука под многослойной соломенной крышей с
-- бахромой, бамбуковые колонны, стойка бара с кокосовыми коктейлями и табуретами, факелы, пальмы с гамаком, доски
-- для серфинга у стены, полосатый зонт с шезлонгом, кромка песка и волн, ракушки и морские звёзды; бока —
-- бамбуковые решётки и доски; сзади — каноэ на песке. Внутри — лагуна на закате: стены-небо полосами от оранжевого
-- к лиловому с горизонтом моря, песчаный пол, бирюзовая вода вокруг островка, пальмы, тики-бар с кокосами,
-- гирлянды лампочек, гамак, круг-фламинго, морские звёзды; экспонат — на песчаном островке с пальмочкой посреди
-- лагуны.
-- Геометрия — scripts/blender/floor_island.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: песчаный островок из двух ярусов.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

return MeshTheme.new({
	name = "IslandTurtle",
	poche = Color3.fromHex("3A2A40"),
	shell = function(_cfg: any, box: any): { any }
		return {
			box(-3.9, 3.9, 0, 0.5, -6.9, 0.9, "Island1"),
			box(-3.2, 3.2, 0.5, 1.1, -6.2, 0.2, "Island2"),
		}
	end,
	exhibit = { at = Vector3.new(0, 1.1, -3), yaw = 180, scale = 2.6 },
	lamps = {
		-- мягкий общий свет, прожектор на экспонат, свет спереди, цветные отсветы темы
		{ at = Vector3.new(0, 14, 5), light = { range = 40, brightness = 0.6, color = Color3.fromHex("FFF4E8") } },
		{
			at = Vector3.new(0, 15, -3),
			light = { range = 18, brightness = 2.3, color = Color3.fromHex("FFF8EC"), spot = 45 },
		},
		{ at = Vector3.new(0, 7, 4), light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4E8") } },
		{ at = Vector3.new(0, 6, -12), light = { range = 10, brightness = 0.6, color = Color3.fromHex("FFA070") } },
		{ at = Vector3.new(-12, 8, 0), light = { range = 9, brightness = 0.4, color = Color3.fromHex("FFE0A0") } },
	},
})

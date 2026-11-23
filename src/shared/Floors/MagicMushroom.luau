--!strict
-- Этаж «Магический гриб» (первая партия новых этажей, 2026-11-21): этаж — сказочный дом-гриб. Снаружи — стены-ножка
-- с продольными бороздками и круглыми окнами, светящимися янтарём, огромная фиолетовая шляпка в белых пятнах с
-- пластинками снизу, светящиеся грибы на стенах, мох, корни, лианы, светлячки. Внутри — волшебная поляна: потолок —
-- пластинки шляпки лучами, стены — кора и корни, моховой пол, дорожка камней, ручей, светящиеся грибы по углам;
-- гриб-экспонат на старом пне в ведьмином круге, вокруг парят споры.
-- Геометрия — scripts/blender/floor_mushroom.py; сборка темы — Floors/MeshTheme (общий конвейер).
--   shell — каркас: пень и ножки больших грибов по углам.
-- Числа каркаса повторяют размеры из скрипта Blender — менять вместе.
-- Зависит от Floors/MeshTheme.

local MeshTheme = require(script.Parent.MeshTheme)

local STUMP = Vector3.new(0, 0, -3) -- пень с грибом
local TOP = 1.84 -- верх пня
local GIANTS = { { -13, -12, 0.85 }, { 12.6, -12.4, 0.95 }, { -13.6, 6.5, 0.65 }, { 13.6, 2.5, 0.7 } } -- x, z, полуширина

return MeshTheme.new({
	name = "MagicMushroom",
	poche = Color3.fromHex("CDBB98"),
	tones = { glowIn = Color3.fromHex("D8D8D8") },
	shell = function(_cfg: any, box: any): { any }
		local list = {
			box(STUMP.X - 3.6, STUMP.X + 3.6, 0, TOP, STUMP.Z - 3.6, STUMP.Z + 3.6, "Stump"),
		}
		for i, g in GIANTS do
			table.insert(list, box(g[1] - g[3], g[1] + g[3], 0, 4, g[2] - g[3], g[2] + g[3], "Mushroom" .. i))
		end
		return list
	end,
	exhibit = { at = Vector3.new(STUMP.X, TOP, STUMP.Z), yaw = 180, scale = 3.4 },
	lamps = {
		-- волшебный свет: лиловый под шляпкой, белый луч на гриб, мягкий свет спереди
		{ at = Vector3.new(0, 14, 4), light = { range = 40, brightness = 0.55, color = Color3.fromHex("D8CCFF") } },
		{
			at = Vector3.new(STUMP.X, 15, STUMP.Z),
			light = { range = 18, brightness = 2.2, color = Color3.fromHex("FFF4FF"), spot = 50 },
		},
		{
			at = Vector3.new(STUMP.X, 7, STUMP.Z + 7),
			light = { range = 10, brightness = 0.8, color = Color3.fromHex("FFF4FF") },
		},
		{ at = Vector3.new(-12, 6, -11), light = { range = 10, brightness = 0.5, color = Color3.fromHex("FF6FD0") } },
		{ at = Vector3.new(12, 7, -11), light = { range = 10, brightness = 0.5, color = Color3.fromHex("4FE0F0") } },
	},
})

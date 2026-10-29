-- Качалка (D31): площадка с задней стеной, поле, где качаются, и огромная гантель. Вывеска — кирпич
-- "SignBoard" на стене, надпись ставит WorldBuilder.
-- Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

local Gym = {}

-- Огромная гантель на подставках: рукоять вдоль Z, диски по краям. Начало — центр основания.
-- Уровень 1 — Деревянная; модели уровней 2–10 придут из Blender (D30, шаг 3).
function Gym.GiantDumbbell(): { ModelBuilder.Brick }
	local wood, woodDark = hex("A0682F"), Palette.WoodDark
	local y = 6 -- высота оси
	local bricks: { ModelBuilder.Brick } = {
		B(Vector3.new(16, 2.4, 2.4), CFrame.new(0, y, 0) * CFrame.Angles(0, math.rad(90), 0), woodDark, { shape = "Cylinder" }),
	}
	for _, z in { -6.5, 6.5 } do
		-- Подставка под рукоятью, два толстых диска и стопор (у цилиндра ось — X, поэтому поворот на 90°).
		table.insert(bricks, B(Vector3.new(3, y - 1.2, 1), Vector3.new(0, (y - 1.2) / 2, z * 0.45), Palette.Metal))
		for _, dz in { -1.4, 1.4 } do
			table.insert(bricks, B(Vector3.new(2.6, 9, 9), CFrame.new(0, y, z + dz) * CFrame.Angles(0, math.rad(90), 0), wood, {
				shape = "Cylinder",
			}))
		end
		local collar = z - math.sign(z) * 3.2
		table.insert(bricks, B(Vector3.new(1, 3.6, 3.6), CFrame.new(0, y, collar) * CFrame.Angles(0, math.rad(90), 0), woodDark, {
			shape = "Cylinder",
		}))
	end
	return bricks
end

-- Поле, где качаются: резиновый пол цвета акцента и светящаяся рамка. size — по X и Z, начало — центр.
function Gym.Field(size: Vector2): { ModelBuilder.Brick }
	local glow = hex("FFC21A")
	local border = 0.8
	local bricks: { ModelBuilder.Brick } = {
		B(Vector3.new(size.X, 0.2, size.Y), Vector3.new(0, 0.1, 0), hex("FF7043"), { collide = false, shadow = false }),
	}
	for _, sign in { -1, 1 } do
		table.insert(bricks, B(Vector3.new(size.X, 0.3, border), Vector3.new(0, 0.15, sign * (size.Y - border) / 2), glow, {
			material = Enum.Material.Neon,
			collide = false,
			shadow = false,
		}))
		table.insert(bricks, B(Vector3.new(border, 0.3, size.Y - border * 2), Vector3.new(sign * (size.X - border) / 2, 0.15, 0), glow, {
			material = Enum.Material.Neon,
			collide = false,
			shadow = false,
		}))
	end
	return bricks
end

-- Площадка зала: резиновый пол и задняя стена с местом под вывеску "SignBoard". size — по X и Z.
function Gym.Hall(size: Vector2): { ModelBuilder.Brick }
	local floor = hex("37474F")
	local bricks: { ModelBuilder.Brick } = {
		B(Vector3.new(size.X, 0.4, size.Y), Vector3.new(0, -0.2, 0), floor),
		-- Стена выше огромной гантели (верх дисков ~10.5), вывеска над ней.
		B(Vector3.new(1, 17, size.Y), Vector3.new(-size.X / 2 + 0.5, 8.5, 0), Palette.HouseWalls[3]),
		B(Vector3.new(0.6, 4.4, size.Y * 0.6), Vector3.new(-size.X / 2 + 1.3, 13.6, 0), Palette.HouseWalls[2], {
			name = "SignBoard",
			material = Enum.Material.SmoothPlastic,
		}),
	}
	-- Красные полосы-разметка на полу.
	for _, z in { -size.Y / 2 + 2, size.Y / 2 - 2 } do
		table.insert(bricks, B(Vector3.new(size.X - 2, 0.1, 0.8), Vector3.new(1, 0.05, z), Palette.HouseWalls[1], { collide = false, shadow = false }))
	end
	return bricks
end

return Gym

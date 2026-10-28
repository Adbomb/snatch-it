-- Спортзал (D17): площадка с задней стеной и стойки с гантелями. Табличка стойки — кирпич "SignBoard",
-- надпись ставит WorldBuilder. Начало стойки — центр основания, лицевая сторона -Z.
-- Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

-- Цвет и материал гантели по id из GameConfig.Gym.
local LOOKS = {
	Wood = { color = hex("A0682F"), material = Enum.Material.Plastic },
	Iron = { color = hex("78909C"), material = Enum.Material.Plastic },
	Gold = { color = hex("FFC21A"), material = Enum.Material.Plastic },
	Diamond = { color = hex("5CE1FF"), material = Enum.Material.Glass },
}

local Gym = {}

function Gym.Rack(dumbbellId: string): { ModelBuilder.Brick }
	local look = LOOKS[dumbbellId] or LOOKS.Wood
	local bricks: { ModelBuilder.Brick } = {
		B(Vector3.new(6, 0.6, 3), Vector3.new(0, 0.3, 0), Palette.Black),
		B(Vector3.new(0.6, 3.4, 0.6), Vector3.new(-2.4, 2.3, 0), Palette.Metal),
		B(Vector3.new(0.6, 3.4, 0.6), Vector3.new(2.4, 2.3, 0), Palette.Metal),
		B(Vector3.new(5.4, 0.4, 0.8), Vector3.new(0, 3.9, 0), Palette.Metal),
		-- Гантель: рукоять и два диска.
		B(Vector3.new(3.4, 0.4, 0.4), CFrame.new(0, 4.5, 0), Palette.Metal, { shape = "Cylinder", collide = false }),
	}
	for _, x in { -1.6, 1.6 } do
		table.insert(
			bricks,
			B(Vector3.new(0.6, 1.6, 1.6), CFrame.new(x, 4.5, 0), look.color, {
				shape = "Cylinder",
				material = look.material,
				collide = false,
			})
		)
	end
	-- Табличка на ножке перед стойкой.
	table.insert(bricks, B(Vector3.new(0.4, 2, 0.4), Vector3.new(0, 1, -2.4), Palette.WoodDark, { collide = false, shadow = false }))
	table.insert(
		bricks,
		B(Vector3.new(4.6, 2.4, 0.4), Vector3.new(0, 2.8, -2.4), look.color, {
			name = "SignBoard",
			material = Enum.Material.SmoothPlastic, -- табличка с текстом: без пупырышков
			collide = false,
			shadow = false,
		})
	)
	return bricks
end

-- Площадка зала: резиновый пол и задняя стена с местом под вывеску "SignBoard". size — по X и Z.
function Gym.Hall(size: Vector2): { ModelBuilder.Brick }
	local floor = hex("37474F")
	local bricks: { ModelBuilder.Brick } = {
		B(Vector3.new(size.X, 0.4, size.Y), Vector3.new(0, -0.2, 0), floor),
		B(Vector3.new(1, 10, size.Y), Vector3.new(-size.X / 2 + 0.5, 5, 0), Palette.HouseWalls[3]),
		B(Vector3.new(0.6, 4, size.Y * 0.6), Vector3.new(-size.X / 2 + 1.3, 7, 0), Palette.HouseWalls[2], {
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

-- Мелкий декор города: куст, лавочка, фонарь, ящик. Мелочь не отбрасывает тень и не мешает ходить
-- (кроме лавочки и ящика, на которые можно встать). Начало координат — центр основания, «лицо» — сторона -Z.
-- Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick
local DECOR = { collide = false, shadow = false }

local Props = {}

function Props.Bush(variant: number): { ModelBuilder.Brick }
	local green = Palette.Leaves[(variant - 1) % #Palette.Leaves + 1]
	return {
		B(Vector3.new(4, 3, 4), Vector3.new(0, 1.5, 0), Palette.Bush, DECOR),
		B(Vector3.new(3, 2.4, 3), Vector3.new(1.2, 1.2, 1), green, DECOR),
		B(Vector3.new(2.4, 2, 2.4), Vector3.new(-0.6, 3.2, -0.4), green:Lerp(Palette.White, 0.1), DECOR),
	}
end

function Props.Bench(): { ModelBuilder.Brick }
	return {
		B(Vector3.new(5, 0.5, 1.6), Vector3.new(0, 1.6, 0), Palette.Wood, { shadow = false }),
		B(Vector3.new(5, 1.4, 0.4), Vector3.new(0, 2.6, 0.7), Palette.Wood, { shadow = false }),
		B(Vector3.new(0.5, 1.4, 1.4), Vector3.new(-2, 0.7, 0), Palette.Metal, DECOR),
		B(Vector3.new(0.5, 1.4, 1.4), Vector3.new(2, 0.7, 0), Palette.Metal, DECOR),
	}
end

function Props.Lamp(): { ModelBuilder.Brick }
	return {
		B(Vector3.new(1.4, 0.6, 1.4), Vector3.new(0, 0.3, 0), Palette.Black, DECOR),
		B(Vector3.new(0.6, 9, 0.6), Vector3.new(0, 4.5, 0), Palette.Metal, DECOR),
		B(Vector3.new(1.8, 0.4, 1.8), Vector3.new(0, 9.2, 0), Palette.Black, DECOR),
		B(Vector3.new(1.4, 1.2, 1.4), Vector3.new(0, 10, 0), Palette.Lamp, {
			material = Enum.Material.Neon,
			collide = false,
			shadow = false,
			light = { range = 18, brightness = 1.2, color = Palette.Lamp },
		}),
		B(Vector3.new(1.8, 0.4, 1.8), Vector3.new(0, 10.8, 0), Palette.Black, DECOR),
	}
end

function Props.Crate(): { ModelBuilder.Brick }
	return {
		B(Vector3.new(4, 4, 4), Vector3.new(0, 2, 0), Palette.Wood),
		B(Vector3.new(4.2, 0.6, 4.2), Vector3.new(0, 3.2, 0), Palette.WoodDark, DECOR),
	}
end

return Props

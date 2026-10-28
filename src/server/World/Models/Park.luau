-- Модели парка: беседка, мостик через пруд. Начало координат — центр основания.
-- Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick
local DECOR = { collide = false, shadow = false }

local Park = {}

-- Беседка: пол на высоте floorHeight, 4 столба, ступенчатая крыша, низкие перила с трёх сторон.
function Park.Gazebo(floorHeight: number, accent: Color3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local size, postHeight = 12, 6
	table.insert(bricks, B(Vector3.new(size, floorHeight, size), Vector3.new(0, floorHeight / 2, 0), Palette.Wood))
	for _, x in { -1, 1 } do
		for _, z in { -1, 1 } do
			table.insert(
				bricks,
				B(Vector3.new(0.8, postHeight, 0.8), Vector3.new(x * (size / 2 - 0.6), floorHeight + postHeight / 2, z * (size / 2 - 0.6)), Palette.White)
			)
		end
	end
	local y = floorHeight + postHeight
	for i, width in { 14, 10, 6, 2.4 } do
		local color = if i % 2 == 0 then Palette.White else accent
		table.insert(bricks, B(Vector3.new(width, 0.9, width), Vector3.new(0, y + 0.45, 0), color))
		y += 0.9
	end
	-- Перила: всё, кроме входа на стороне -Z.
	for _, spec in {
		{ Vector3.new(size - 1.6, 1, 0.4), Vector3.new(0, 0, size / 2 - 0.6) },
		{ Vector3.new(0.4, 1, size - 1.6), Vector3.new(-size / 2 + 0.6, 0, 0) },
		{ Vector3.new(0.4, 1, size - 1.6), Vector3.new(size / 2 - 0.6, 0, 0) },
	} do
		table.insert(bricks, B(spec[1], spec[2] + Vector3.new(0, floorHeight + 1.6, 0), Palette.White, DECOR))
	end
	return bricks
end

-- Мостик длиной length вдоль Z: настил, пандусы по краям, перила.
function Park.Bridge(length: number): { ModelBuilder.Brick }
	local deckHeight, width, ramp = 1.4, 5, 4
	local bricks: { ModelBuilder.Brick } = {
		B(Vector3.new(width, 0.6, length), Vector3.new(0, deckHeight, 0), Palette.Wood),
		-- У Wedge высокая сторона на +Z: пандус у края -Z стоит как есть, у края +Z развёрнут.
		B(
			Vector3.new(width, deckHeight + 0.3, ramp),
			CFrame.new(0, (deckHeight + 0.3) / 2, length / 2 + ramp / 2) * CFrame.Angles(0, math.pi, 0),
			Palette.Wood,
			{ shape = "Wedge" }
		),
		B(Vector3.new(width, deckHeight + 0.3, ramp), CFrame.new(0, (deckHeight + 0.3) / 2, -length / 2 - ramp / 2), Palette.Wood, {
			shape = "Wedge",
		}),
	}
	for _, x in { -width / 2 + 0.2, width / 2 - 0.2 } do
		table.insert(bricks, B(Vector3.new(0.4, 0.4, length), Vector3.new(x, deckHeight + 1.8, 0), Palette.WoodDark, DECOR))
		for _, z in { -length / 2 + 0.3, 0, length / 2 - 0.3 } do
			table.insert(bricks, B(Vector3.new(0.4, 1.6, 0.4), Vector3.new(x, deckHeight + 1, z), Palette.WoodDark, DECOR))
		end
	end
	return bricks
end

return Park

-- Временная тестовая площадка закрытого босса (MapLayout.TestArenas, этап C босса 10): ровный пол с низким бортом,
-- чтобы проверить настоящую модель, бой, повороты и залп на чистом месте, не трогая зону и её декор. Строится только
-- вместе с закрытым боссом (Studio с DevMode, BossService). Пол — Plastic с общим LegoSquares (D36), верх пола — y = 0
-- (там стоит босс), борт встык снаружи (совпадающих граней нет). Зависит от World/ModelBuilder.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)

local FLOOR = Color3.fromHex("5C6178")
local RIM = Color3.fromHex("3D4152")
local MARK = Color3.fromHex("8A90A8")

local TestArena = {}

-- Площадка size (X × Z, стады) с центром center на высоте пола center.Y (верх пола).
function TestArena.Build(name: string, center: Vector3, size: Vector2, parent: Instance): Model
	local w, d = size.X, size.Y
	local bricks = {
		ModelBuilder.Brick(Vector3.new(w, 1, d), Vector3.new(0, -0.5, 0), FLOOR),
		ModelBuilder.Brick(Vector3.new(w + 2, 1.5, 1), Vector3.new(0, -0.25, d / 2 + 0.5), RIM),
		ModelBuilder.Brick(Vector3.new(w + 2, 1.5, 1), Vector3.new(0, -0.25, -d / 2 - 0.5), RIM),
		ModelBuilder.Brick(Vector3.new(1, 1.5, d), Vector3.new(w / 2 + 0.5, -0.25, 0), RIM),
		ModelBuilder.Brick(Vector3.new(1, 1.5, d), Vector3.new(-w / 2 - 0.5, -0.25, 0), RIM),
		-- метки дистанции перед боссом (+Z): 16 и 30 стадов от центра — залп и уклонение видно глазом
		ModelBuilder.Brick(Vector3.new(24, 0.1, 0.4), Vector3.new(0, 0.05, 16), MARK),
		ModelBuilder.Brick(Vector3.new(24, 0.1, 0.4), Vector3.new(0, 0.05, 30), MARK),
	}
	local model = ModelBuilder.Build(name, bricks, { collide = true, shadow = false })
	for _, part in model:GetDescendants() do
		if part:IsA("BasePart") and part.Size.Y < 0.2 then
			part.CanCollide = false -- метки на полу: не цепляют ноги
		end
	end
	return ModelBuilder.Place(model, CFrame.new(center), parent)
end

return TestArena

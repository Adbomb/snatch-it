-- Серверные проверки намерений игрока: жив ли он и стоит ли рядом с целью.
-- Используется CarryService и MuseumService. Зависит от GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

local Validate = {}

-- Возвращает HumanoidRootPart и Humanoid, только если персонаж существует и жив.
function Validate.GetLiveRoot(player: Player): (BasePart?, Humanoid?)
	local character = player.Character
	if not character then
		return nil, nil
	end
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	local root = character:FindFirstChild("HumanoidRootPart")
	if not humanoid or humanoid.Health <= 0 or not root or not root:IsA("BasePart") then
		return nil, nil
	end
	return root, humanoid
end

-- Игрок жив и находится не дальше maxDistance (+ запас на задержку сети) от точки.
function Validate.IsNear(player: Player, position: Vector3, maxDistance: number): boolean
	local root = Validate.GetLiveRoot(player)
	if not root then
		return false
	end
	return (root.Position - position).Magnitude <= maxDistance + GameConfig.DistanceTolerance
end

return Validate

-- Скорость ходьбы от силы (D24, D29): логарифмически от Progression.Speed.min при нулевой силе до max на
-- потолке cap; груз умножает (GameConfig.Carry.WeightSpeed). Читается сервером. Зависит от GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

local Speed = {}

-- weight — вес груза в руках (Light / Medium / Heavy) или nil.
function Speed.Walk(strength: number, weight: string?): number
	local cfg = GameConfig.Progression.Speed
	local share = math.clamp(math.log10(1 + math.max(strength, 0)) / math.log10(1 + cfg.cap), 0, 1)
	local base = cfg.min + (cfg.max - cfg.min) * share
	local factor = if weight then GameConfig.Carry.WeightSpeed[weight] or 1 else 1
	return base * factor
end

return Speed

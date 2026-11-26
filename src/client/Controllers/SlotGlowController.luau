-- Пульсация подсветки мест у боссов (D71): кольца и ореолы с атрибутом Pulse (постаменты «Свалки») медленно и едва
-- заметно меняют яркость — в нижней точке бледнеют на Pulse (прибавка к прозрачности Alpha), период PulsePeriod.
-- Пульсирует только горящая подсветка (атрибут Lit ставит сервер, World/SlotGlow.Paint); погасшую сервер прячет сам.
-- Места чуть сдвинуты по фазе (атрибут Slot) — кольца «дышат» не строем. Только вид: свойства меняются у этого клиента.
-- Зависит от меток CollectionService «SlotGlow» и атрибутов, которые ставит сервер.

local CollectionService = game:GetService("CollectionService")
local RunService = game:GetService("RunService")

local SlotGlowController = {}

local TAG = "SlotGlow"
local STEP = 1 / 30 -- чаще обновлять незачем: пульсация медленная
local PHASE_PER_SLOT = 0.7 -- сдвиг фазы между местами, рад

local parts: { [BasePart]: boolean } = {}

local function track(instance: Instance)
	if instance:IsA("BasePart") and typeof(instance:GetAttribute("Pulse")) == "number" then
		parts[instance] = true
	end
end

function SlotGlowController.Init()
	for _, instance in CollectionService:GetTagged(TAG) do
		track(instance)
	end
	CollectionService:GetInstanceAddedSignal(TAG):Connect(track)
	CollectionService:GetInstanceRemovedSignal(TAG):Connect(function(instance)
		parts[instance :: BasePart] = nil
	end)
	local wait = 0
	RunService.Heartbeat:Connect(function(dt)
		wait += dt
		if wait < STEP then
			return
		end
		wait = 0
		local now = os.clock()
		for part in parts do
			if not part:GetAttribute("Lit") then
				continue
			end
			local alpha = part:GetAttribute("Alpha")
			local depth = part:GetAttribute("Pulse")
			local period = part:GetAttribute("PulsePeriod")
			local slot = part:GetAttribute("Slot")
			if typeof(alpha) ~= "number" or typeof(depth) ~= "number" or typeof(period) ~= "number" then
				continue
			end
			local phase = 2 * math.pi * now / period + (if typeof(slot) == "number" then slot else 0) * PHASE_PER_SLOT
			part.Transparency = alpha + depth * (0.5 - 0.5 * math.cos(phase))
		end
	end)
end

return SlotGlowController

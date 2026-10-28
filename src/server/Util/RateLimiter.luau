-- Ограничитель частоты: не чаще N запросов в секунду на игрока («ведро жетонов»).
-- Каждый вход (RemoteEvent или подсказка) создаёт свой экземпляр. Зависит от Players.

local Players = game:GetService("Players")

local RateLimiter = {}
RateLimiter.__index = RateLimiter

local allLimiters = {}

function RateLimiter.new(maxPerSecond: number)
	local self = setmetatable({ rate = maxPerSecond, buckets = {} }, RateLimiter)
	table.insert(allLimiters, self)
	return self
end

function RateLimiter:Allow(player: Player): boolean
	local now = os.clock()
	local bucket = self.buckets[player]
	if not bucket then
		bucket = { tokens = self.rate, last = now }
		self.buckets[player] = bucket
	end
	bucket.tokens = math.min(self.rate, bucket.tokens + (now - bucket.last) * self.rate)
	bucket.last = now
	if bucket.tokens < 1 then
		return false
	end
	bucket.tokens -= 1
	return true
end

Players.PlayerRemoving:Connect(function(player)
	for _, limiter in allLimiters do
		limiter.buckets[player] = nil
	end
end)

return RateLimiter

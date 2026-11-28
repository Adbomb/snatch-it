-- Пружина с критическим затуханием: значение плавно догоняет цель без рывков и без перелёта, при любой частоте
-- кадров (шаг считается по формуле, а не по кадрам). Для камеры и крупных движений показа броска (D75): цель можно
-- менять каждый кадр — скорость не теряется, склеек нет. Работает с числами и Vector3.
-- Ни от чего не зависит.

local Spring = {}
Spring.__index = Spring

export type Spring = typeof(setmetatable({} :: { value: any, velocity: any, speed: number }, Spring))

-- speed — жёсткость (1/с): больше — быстрее догоняет. 6 — мягко, 14 — упруго, 30 — почти сразу.
function Spring.new(value: any, speed: number): Spring
	return setmetatable({ value = value, velocity = value * 0, speed = speed }, Spring)
end

-- Шаг на dt секунд к цели target; возвращает новое значение.
function Spring.Step(self: Spring, target: any, dt: number): any
	local w = self.speed
	local step = math.clamp(dt, 0, 0.1)
	local x = self.value - target
	local v = self.velocity
	local decay = math.exp(-w * step)
	local k = (v + x * w) * step
	self.value = target + (x + k) * decay
	self.velocity = (v - k * w) * decay
	return self.value
end

-- Мгновенно поставить значение (скорость — ноль).
function Spring.Set(self: Spring, value: any)
	self.value = value
	self.velocity = value * 0
end

-- Толчок: прибавить скорость (встряска камеры, отдача).
function Spring.Kick(self: Spring, impulse: any)
	self.velocity += impulse
end

return Spring

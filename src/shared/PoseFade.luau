-- Сглаживание разрывов позы босса при смене источника анимации (этап C.2, Король-дракон). Клиент считает позу
-- заново каждый кадр по атрибутам (Shared/BossAnim), и почти все переходы там плавные. Разрыв бывает, когда источник
-- меняется скачком: сервер в одном шаге отменяет план выпада и объявляет залп (замах исчезает за кадр), босс
-- возвращается в кадр после паузы (вне кадра поза не считается). Тогда поза за rig.Fade.Time плавно переходит от
-- последней показанной к новой. Срабатывает, только если при смене ключа источника (или после паузы) поза отличается
-- больше чем на rig.Fade.Jump градусов: обычные стыки клипов (плановый выпад, смена состояния) не трогаются, время
-- клипов и попаданий не меняется. Без rig.Fade — поза как есть (боссы 1–4).
-- Зависит только от формата позы Shared/BossAnim (часть → CFrame).

local PoseFade = {}
PoseFade.__index = PoseFade

local GAP = 0.2 -- с без обновления (босс был вне кадра) — следующая поза сравнивается с последней показанной

export type Fader = typeof(setmetatable(
	{} :: {
		rig: any,
		key: string?,
		last: { [string]: CFrame }?,
		lastClock: number?,
		from: { [string]: CFrame }?,
		fromAt: number,
	},
	PoseFade
))

function PoseFade.new(rig: any): Fader
	return setmetatable({ rig = rig, key = nil, last = nil, lastClock = nil, from = nil, fromAt = 0 }, PoseFade)
end

-- Ключ источника позы: состояние, номер выпада, план (номер, вид, отменён ли), шаг.
function PoseFade.Key(input: any): string
	return ("%s|%s|%s%s|%s|%s"):format(
		tostring(input.state),
		tostring(input.attackSeq or 0),
		tostring(input.planSeq or ""),
		tostring(input.planKind or ""),
		if input.planCancelT then "c" else "",
		if input.moving then "m" else ""
	)
end

local function maxAngle(order: { string }, a: { [string]: CFrame }, b: { [string]: CFrame }): number
	local worst = 0
	for _, part in order do
		local x, y = a[part], b[part]
		if x and y then
			local _, ang = (x:Inverse() * y):ToAxisAngle()
			local d = math.deg(math.abs(ang)) % 360
			if d > 180 then
				d = 360 - d
			end
			if d > worst then
				worst = d
			end
		end
	end
	return worst
end

-- Поза к показу: pose — посчитанная BossAnim, key — PoseFade.Key(input), clock — время кадра (сек).
function PoseFade.Apply(self: Fader, key: string, pose: { [string]: CFrame }, clock: number): { [string]: CFrame }
	local cfg = self.rig.Fade
	if not cfg then
		return pose
	end
	local last = self.last
	local paused = self.lastClock ~= nil and clock - self.lastClock > GAP
	if last and (key ~= self.key or paused) and maxAngle(self.rig.Order, last, pose) > cfg.Jump then
		self.from, self.fromAt = last, clock
	end
	self.key, self.lastClock = key, clock
	local out = pose
	local from = self.from
	if from then
		local w = (clock - self.fromAt) / cfg.Time
		if w >= 1 then
			self.from = nil
		else
			w = w * w * (3 - 2 * w)
			out = {}
			for part, cf in pose do
				local a = from[part]
				out[part] = if a then a:Lerp(cf, w) else cf
			end
		end
	end
	self.last = out
	return out
end

return PoseFade

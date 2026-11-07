--!strict
-- Минимальное время доставки украденного (D53, только запись в лог — сдачу не блокирует). Честный вор не может дойти от
-- места кражи до своего сундука быстрее, чем по прямой на наибольшей своей скорости за переноску: прямая — нижняя
-- граница любого пути (стены только удлиняют), поэтому ложных срабатываний у честного нет. Учитывается: переносы
-- сервером (их путь вычитается — сумма смещений MoveGuard.Teleport за переноску), запас Slack ст. (точка снятия и
-- сдачи в радиусе подсказок), Tolerance к скорости (как MoveGuard) и Lag с (события снятия и сдачи приходят с разной
-- задержкой сети). Чистый модуль (проверяется в Lune, check_theft.luau). Ни от чего не зависит.

local DeliveryRules = {}

export type Params = {
	Tolerance: number, -- множитель к скорости (запас на сеть и рывки)
	Slack: number, -- стадов пути, которые не учитываются
	Lag: number, -- секунд, на которые время доставки может «сжаться» из-за задержки сети
}

-- Наименьшее время честной доставки, секунд. distance — по полу от места снятия до места сдачи; credit — сколько из
-- этого пути перенёс сервер; speed — наибольшая скорость вора за переноску. Скорость неизвестна (≤ 0) — 0 (не судить).
function DeliveryRules.MinSeconds(distance: number, credit: number, speed: number, p: Params): number
	if speed ~= speed or speed <= 0 or distance ~= distance then
		return 0
	end
	local walk = math.max(0, distance - math.max(credit, 0) - p.Slack)
	return math.max(0, walk / (speed * p.Tolerance) - p.Lag)
end

-- Доставка подозрительна: пришла быстрее наименьшего честного времени.
function DeliveryRules.Suspicious(elapsed: number, minSeconds: number): boolean
	return minSeconds > 0 and elapsed < minSeconds
end

return DeliveryRules

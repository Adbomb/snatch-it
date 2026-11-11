-- Игровое время (D37): фаза, день и границы фазы — чистая функция общего времени, поэтому они одинаковы на всех
-- серверах (новый сервер не начинает цикл заново) и у клиентов. Общее время — workspace:GetServerTimeNow():
-- Unix-время сервера, клиент получает его синхронно со своим сервером.
-- Круг: 9 × (день 300 + ночь 30) + 10-й день 300 (последние 120 — подготовка) + Судная ночь 90 = 3 360 с.
-- Ускорение в Studio: атрибуты TimeScale, TimeAnchorReal, TimeAnchorGame на ReplicatedStorage (ставит TimeService
-- через DevTools) — их читают и сервер, и клиент. Зависит от Config/GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(script.Parent.Config.GameConfig)

export type Phase = "Day" | "Preparation" | "Night" | "DoomNight"

export type State = {
	phase: Phase,
	day: number, -- день в круге: 1 … DoomEvery
	cycle: number, -- номер круга от Epoch
	startsAt: number, -- начало фазы (общее время, с)
	endsAt: number, -- конец фазы
}

local cfg = GameConfig.Time
local NORMAL = cfg.DayLength + cfg.NightLength -- обычный день с ночью

local GameTime = {}

GameTime.Names = {
	Day = "День",
	Preparation = "Подготовка",
	Night = "Ночь",
	DoomNight = "Судная ночь",
}

-- Длина круга из DoomEvery дней и ночей.
function GameTime.CycleLength(): number
	return (cfg.DoomEvery - 1) * NORMAL + cfg.DayLength + cfg.DoomNightLength
end

-- Фаза в момент t (общее время, с).
function GameTime.At(t: number): State
	local length = GameTime.CycleLength()
	local cycle = math.floor((t - cfg.Epoch) / length)
	local base = cfg.Epoch + cycle * length
	local x = t - base
	local normalDays = cfg.DoomEvery - 1
	if x < normalDays * NORMAL then
		local index = math.floor(x / NORMAL)
		local dayStart = base + index * NORMAL
		local nightStart = dayStart + cfg.DayLength
		if t < nightStart then
			return { phase = "Day", day = index + 1, cycle = cycle, startsAt = dayStart, endsAt = nightStart }
		end
		return { phase = "Night", day = index + 1, cycle = cycle, startsAt = nightStart, endsAt = dayStart + NORMAL }
	end
	local dayStart = base + normalDays * NORMAL
	local nightStart = dayStart + cfg.DayLength
	local preparationStart = nightStart - cfg.PreparationLength
	local day = cfg.DoomEvery
	if t < preparationStart then
		return { phase = "Day", day = day, cycle = cycle, startsAt = dayStart, endsAt = preparationStart }
	elseif t < nightStart then
		return { phase = "Preparation", day = day, cycle = cycle, startsAt = preparationStart, endsAt = nightStart }
	end
	return {
		phase = "DoomNight",
		day = day,
		cycle = cycle,
		startsAt = nightStart,
		endsAt = nightStart + cfg.DoomNightLength,
	}
end

-- Ночь ли это (обычная или Судная): коридор уровней закрыт.
function GameTime.IsNight(phase: Phase): boolean
	return phase == "Night" or phase == "DoomNight"
end

-- Сколько ночей осталось до Судной (0 — Судная ночь сейчас или сегодня подготовка).
function GameTime.DaysToDoom(state: State): number
	return cfg.DoomEvery - state.day
end

-- Окно доставки (D37, D46): первые DeliveryGrace секунд после Судной ночи — вор с добычей ещё может её донести,
-- новые кражи не начинаются. Возвращает конец окна или nil, если t не в нём.
function GameTime.DeliveryWindowEnd(t: number): number?
	local state = GameTime.At(t)
	if state.phase == "Day" and state.day == 1 and t < state.startsAt + cfg.DeliveryGrace then
		return state.startsAt + cfg.DeliveryGrace
	end
	return nil
end

-- Можно ли менять экспонаты (выставить, снять, заменить, переставить) в момент t (D46): днём и обычной ночью —
-- да; в подготовку, Судную ночь и окно доставки — нет. nil — можно, иначе причина для игрока.
function GameTime.ExhibitLock(t: number): string?
	local phase = GameTime.At(t).phase
	if phase == "Preparation" then
		return "Подготовка к Судной ночи: экспонаты менять нельзя"
	elseif phase == "DoomNight" then
		return "Судная ночь: экспонаты менять нельзя"
	elseif GameTime.DeliveryWindowEnd(t) then
		return "Воры доносят добычу: экспонаты менять нельзя ещё несколько секунд"
	end
	return nil
end

-- Можно ли покупать уровень музея в момент t (D56): в подготовку к Судной ночи, в Судную ночь и ещё DeliveryGrace
-- секунд после неё — нельзя. nil — можно; иначе причина для игрока и общее время, когда запрет кончится (окно
-- «Улучшение музея» показывает отсчёт; решает сервер — MuseumUpgradeService).
function GameTime.UpgradeLock(t: number): (string?, number?)
	local state = GameTime.At(t)
	if state.phase == "Preparation" then
		return "Подготовка к Судной ночи: музей улучшать нельзя",
			state.endsAt + cfg.DoomNightLength + cfg.DeliveryGrace
	elseif state.phase == "DoomNight" then
		return "Судная ночь: музей улучшать нельзя", state.endsAt + cfg.DeliveryGrace
	end
	local windowEnd = GameTime.DeliveryWindowEnd(t)
	if windowEnd then
		return "Судная ночь только что закончилась: улучшение откроется через несколько секунд",
			windowEnd
	end
	return nil, nil
end

-- Идёт ли кража (D37): Судная ночь — можно начинать; окно доставки — только донести начатое.
function GameTime.TheftPhase(t: number): "Open" | "Delivery" | nil
	if GameTime.At(t).phase == "DoomNight" then
		return "Open"
	elseif GameTime.DeliveryWindowEnd(t) then
		return "Delivery"
	end
	return nil
end

-- Номер Судной ночи для лимитов краж (D37): во время неё и в окно доставки после неё — номер её круга; иначе nil.
function GameTime.DoomEventId(t: number): number?
	local phase = GameTime.TheftPhase(t)
	if phase == "Open" then
		return GameTime.At(t).cycle
	elseif phase == "Delivery" then
		return GameTime.At(t).cycle - 1
	end
	return nil
end

-- Общее время сейчас (с ускорением Studio, если оно включено).
function GameTime.Now(): number
	local real = workspace:GetServerTimeNow()
	local scale = ReplicatedStorage:GetAttribute("TimeScale")
	if type(scale) ~= "number" then
		return real
	end
	local anchorReal = ReplicatedStorage:GetAttribute("TimeAnchorReal")
	local anchorGame = ReplicatedStorage:GetAttribute("TimeAnchorGame")
	if type(anchorReal) ~= "number" or type(anchorGame) ~= "number" then
		return real
	end
	return anchorGame + (real - anchorReal) * scale
end

function GameTime.Current(): State
	return GameTime.At(GameTime.Now())
end

return GameTime

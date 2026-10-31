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

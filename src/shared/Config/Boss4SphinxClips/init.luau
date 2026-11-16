-- Клипы босса 4 «Сфинкс-лежебока»: имя → данные клипа (модуль загружается при первом обращении). Сгенерировано
-- scripts/boss4_to_luau.py — руками не править. Проигрыватель — Shared/BossClips. Ни от чего не зависит.

local loaders = {
	sleep_idle = function()
		return require(script.SleepIdle)
	end,
	wake = function()
		return require(script.Wake)
	end,
	combat_idle = function()
		return require(script.CombatIdle)
	end,
	walk = function()
		return require(script.Walk)
	end,
	heavy_paw = function()
		return require(script.HeavyPaw)
	end,
	tail_strike = function()
		return require(script.TailStrike)
	end,
	hit = function()
		return require(script.Hit)
	end,
	victory = function()
		return require(script.Victory)
	end,
	defeat = function()
		return require(script.Defeat)
	end,
	fall_asleep = function()
		return require(script.FallAsleep)
	end,
}

local Clips = {}

Clips.Names = { "sleep_idle", "wake", "combat_idle", "walk", "heavy_paw", "tail_strike", "hit", "victory", "defeat", "fall_asleep" }

-- Данные клипа name (nil — такого клипа нет).
function Clips.Load(name: string): any
	local load = loaders[name]
	return if load then load() else nil
end

return Clips

-- Клипы босса 10 «Король-дракон»: имя → данные клипа (модуль загружается при первом обращении; клип из нескольких
-- частей склеивается по кадрам). Сгенерировано scripts/boss10_to_luau.py — руками не править. Проигрыватель —
-- Shared/BossClips. Ни от чего не зависит.

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
	claw_swipe = function()
		return require(script.ClawSwipe)
	end,
	bite = function()
		return require(script.Bite)
	end,
	tail_strike = function()
		return require(script.TailStrike)
	end,
	wing_buffet = function()
		return require(script.WingBuffet)
	end,
	magic_volley = function()
		return require(script.MagicVolley)
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
	turn_step_left = function()
		return require(script.TurnStepLeft)
	end,
	turn_step_right = function()
		return require(script.TurnStepRight)
	end,
}

local Clips = {}

Clips.Names = { "sleep_idle", "wake", "combat_idle", "walk", "claw_swipe", "bite", "tail_strike", "wing_buffet", "magic_volley", "hit", "victory", "defeat", "fall_asleep", "turn_step_left", "turn_step_right" }

-- Данные клипа name (nil — такого клипа нет).
function Clips.Load(name: string): any
	local load = loaders[name]
	return if load then load() else nil
end

return Clips

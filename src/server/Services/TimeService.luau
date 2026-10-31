-- Игровое время на сервере (D37): раз в GameConfig.Time.TickSeconds считает фазу (Shared/GameTime); при смене —
-- атрибуты ReplicatedStorage для клиентов (Phase, Day, Cycle, PhaseStartsAt, PhaseEndsAt) и вызов подписчиков
-- OnPhaseChanged (ночь, обновление слотов боссов, Судная ночь). В Studio — ускорение и переход к фазе (DevTools).
-- Зависит от Shared/GameTime, GameConfig, Util/Log.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local Log = require(ServerScriptService.Server.Util.Log)

type Listener = (state: GameTime.State, previous: GameTime.State?) -> ()

local listeners: { Listener } = {}
local current: GameTime.State? = nil

local TimeService = {}

-- Подписка на смену фазы: listener(новая, прежняя). Вызывается в отдельном потоке.
function TimeService.OnPhaseChanged(listener: Listener)
	table.insert(listeners, listener)
end

function TimeService.Current(): GameTime.State
	return current or GameTime.Current()
end

local function publish(state: GameTime.State)
	ReplicatedStorage:SetAttribute("Phase", state.phase)
	ReplicatedStorage:SetAttribute("Day", state.day)
	ReplicatedStorage:SetAttribute("Cycle", state.cycle)
	ReplicatedStorage:SetAttribute("PhaseStartsAt", state.startsAt)
	ReplicatedStorage:SetAttribute("PhaseEndsAt", state.endsAt)
end

-- Проверка смены фазы; при смене — атрибуты и подписчики.
local function update()
	local state = GameTime.Current()
	local previous = current
	if previous and previous.phase == state.phase and previous.startsAt == state.startsAt then
		return
	end
	current = state
	publish(state)
	Log.Debug(
		"TimeService",
		("%s, день %d (круг %d), %.0f с"):format(
			GameTime.Names[state.phase],
			state.day,
			state.cycle,
			state.endsAt - state.startsAt
		)
	)
	for _, listener in listeners do
		task.spawn(listener, state, previous)
	end
end

function TimeService.Init()
	update()
	task.spawn(function()
		while true do
			task.wait(GameConfig.Time.TickSeconds)
			update()
		end
	end)
end

-- Studio: ускорение времени (scale раз). Текущий момент игры сохраняется, дальше время идёт быстрее.
function TimeService.SetScale(scale: number)
	if not RunService:IsStudio() or type(scale) ~= "number" or scale <= 0 then
		return
	end
	local now = GameTime.Now()
	ReplicatedStorage:SetAttribute("TimeAnchorReal", workspace:GetServerTimeNow())
	ReplicatedStorage:SetAttribute("TimeAnchorGame", now)
	ReplicatedStorage:SetAttribute("TimeScale", scale)
	update()
end

-- Studio: перейти к ближайшему впереди началу фазы phase минус secondsBefore. Возвращает новую фазу.
function TimeService.SkipTo(phase: GameTime.Phase, secondsBefore: number?): GameTime.State?
	if not RunService:IsStudio() then
		return nil
	end
	local t = GameTime.Now()
	local target: number? = nil
	for _ = 1, 4 * GameConfig.Time.DoomEvery do
		local state = GameTime.At(t)
		t = state.endsAt + 1e-3
		local nextState = GameTime.At(t)
		if nextState.phase == phase then
			target = nextState.startsAt
			break
		end
	end
	if not target then
		return nil
	end
	local scale = ReplicatedStorage:GetAttribute("TimeScale")
	ReplicatedStorage:SetAttribute("TimeAnchorReal", workspace:GetServerTimeNow())
	ReplicatedStorage:SetAttribute("TimeAnchorGame", target - (secondsBefore or 0))
	ReplicatedStorage:SetAttribute("TimeScale", if type(scale) == "number" then scale else 1)
	update()
	return TimeService.Current()
end

-- Studio: вернуть общее время без ускорения.
function TimeService.ResetClock()
	if not RunService:IsStudio() then
		return
	end
	ReplicatedStorage:SetAttribute("TimeScale", nil)
	ReplicatedStorage:SetAttribute("TimeAnchorReal", nil)
	ReplicatedStorage:SetAttribute("TimeAnchorGame", nil)
	update()
end

-- Для серверных тестов: проверить смену фазы сейчас, не дожидаясь такта.
TimeService.Update = update

return TimeService

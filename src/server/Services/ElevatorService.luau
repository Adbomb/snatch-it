--!strict
-- Лифт музея-небоскрёба (этап B, режим башни DEV): одна шахта, подсказка «Лифт» на площадке каждого этажа и в холле
-- (World/TowerBuilder). Подсказка открывает у игрока окно лифта (Remotes.OpenWindow «Elevator»); выбор этажа —
-- RemoteEvent ElevatorGo (участок, этаж 0…N). Всё решает сервер: башня есть и не перестраивается (ShiftLock), игрок
-- жив, не оглушён и не в капкане, стоит у точки лифта этой башни (по серверной позиции), этаж существует, не чаще
-- RateLimits.Elevator. Перенос — MoveGuard.Teleport на свободное место высадки (по кругу, TowerService.NextSpot):
-- каркас пола у каждого этажа есть всегда, поэтому персонаж не падает, даже если убранство у клиента ещё не готово.
-- Ответ — ElevatorResult { ok, plot, index, reason? }. Гостям чужой башни лифт тоже доступен (посещение).
-- Зависит от TowerService, MoveGuard, World/TowerBuilder, Util/*, Remotes, GameConfig.

local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Server = ServerScriptService.Server
local MoveGuard = require(Server.Services.MoveGuard)
local TowerService = require(Server.Services.TowerService)
local TowerBuilder = require(Server.World.TowerBuilder)
local RateLimiter = require(Server.Util.RateLimiter)
local Validate = require(Server.Util.Validate)

local cfg = GameConfig.Tower
local limiter = RateLimiter.new(GameConfig.RateLimits.Elevator)

local ElevatorService = {}

export type Result = { ok: boolean, plot: number?, index: number?, reason: string? }

local function reply(player: any, payload: Result): Result
	Remotes.FireClient(Remotes.Names.ElevatorResult, player, payload)
	return payload
end

local function whole(value: any, low: number, high: number): boolean
	return type(value) == "number" and value == value and value % 1 == 0 and value >= low and value <= high
end

-- Запрос лифта: (участок, этаж). Возвращает ответ (его же получает игрок). extra — тестовые игроки (их нет в
-- Players): места высадки, где они стоят, тоже заняты; с клиента extra не приходит (обёртка RemoteEvent ниже).
local function tryGo(player: any, plotIndex: any, index: any, extra: { any }?): Result?
	if not limiter:Allow(player) then
		return nil
	end
	if not whole(plotIndex, 1, GameConfig.World.PlotCount) or not whole(index, 0, 10000) then
		return nil -- подделка: молча
	end
	local t = TowerService.Get(plotIndex)
	if not t then
		return reply(player, { ok = false, reason = "Башни здесь нет" })
	end
	if os.clock() < t.lockUntil then
		return reply(
			player,
			{ ok = false, reason = "Башня перестраивается — подождите" }
		)
	end
	local root = Validate.GetLiveRoot(player)
	if not root then
		return reply(player, { ok = false, reason = "Сейчас нельзя" })
	end
	if player:GetAttribute("Knocked") or player:GetAttribute("Snared") or MoveGuard.IsPinned(player) then
		return reply(
			player,
			{ ok = false, reason = "Сейчас нельзя: вы оглушены или в капкане" }
		)
	end
	local count = t.model:GetAttribute("FloorCount") or 0
	if index > count then
		return reply(player, { ok = false, reason = "Такого этажа нет" })
	end
	local at = TowerBuilder.IndexAt(t.model, root.Position, count)
	local near = false
	if at then
		local point = TowerBuilder.FloorCFrame(t.model.WorldPivot, at) * CFrame.new(cfg.ElevatorPoint)
		near = (point.Position - root.Position).Magnitude <= cfg.ElevatorDistance + GameConfig.DistanceTolerance
	end
	if not near then
		return reply(player, { ok = false, reason = "Подойдите к лифту" })
	end
	if at ~= index then
		MoveGuard.Teleport(player, TowerService.NextSpot(t, index, extra))
	end
	return reply(player, { ok = true, plot = plotIndex, index = index })
end

function ElevatorService.Init()
	Remotes.Get(Remotes.Names.ElevatorGo).OnServerEvent:Connect(function(player, plotIndex, index)
		tryGo(player, plotIndex, index)
	end)
	ProximityPromptService.PromptTriggered:Connect(function(prompt, player)
		if prompt.Name ~= TowerBuilder.PromptName then
			return
		end
		local plotIndex = prompt:GetAttribute("PlotIndex")
		if type(plotIndex) == "number" and TowerService.Get(plotIndex) then
			Remotes.FireClient(Remotes.Names.OpenWindow, player, "Elevator", plotIndex)
		end
	end)
end

-- Для серверных тестов (Server/Tests/TowerTests): тот же обработчик, что RemoteEvent.
ElevatorService.Handlers = {
	Go = tryGo,
}

return ElevatorService

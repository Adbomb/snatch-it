-- Ночь (D37): с началом ночи (обычной и Судной) вход в коридор уровней закрывает барьер в воротах уровня 1 (только
-- на ночь, карта не меняется), несомые предметы теряются (D37: недоставленное теряется), игроки из опасной зоны
-- (коридор, MapLayout.InDangerZone) переносятся на место появления — Safe Zone. Пока ночь, сервер раз в
-- GameConfig.Time.NightCheckSeconds выводит из коридора тех, кто туда попал. С рассветом барьер убирается.
-- Бои с боссами прерывает BossService (этап 4), слоты боссов обновляет BossLootService (этап 3).
-- Зависит от TimeService, CarryService, Shared/GameTime, World/MapLayout, GameConfig, Util/Notify, Util/Log.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local TimeService = require(Server.Services.TimeService)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local MapLayout = require(Server.World.MapLayout)

local barrier: Part
local world: Instance
local night = false
local random = Random.new()

local NightService = {}

-- Точка в Safe Zone: место появления с небольшим разбросом, чтобы игроки не вставали друг в друга.
local function safePoint(): CFrame
	local spread = GameConfig.Time.SafeSpread
	local offset = Vector3.new(random:NextNumber(-spread, spread), 3, random:NextNumber(-spread, spread))
	local position = MapLayout.Spawn.position + offset
	return CFrame.lookAt(position, position + Vector3.new(0, 0, 1)) -- лицом к музеям
end

-- Выводит игроков из опасной зоны. Возвращает число перенесённых.
local function sweep(players: { Player }): number
	local moved = 0
	for _, player in players do
		local character = player.Character
		local root = character and character:FindFirstChild("HumanoidRootPart")
		if root and root:IsA("BasePart") and MapLayout.InDangerZone(root.Position) then
			(character :: Model):PivotTo(safePoint())
			moved += 1
			Notify.Send(player, "Ночь: коридор уровней закрыт — вы в безопасной зоне", "Stop")
		end
	end
	return moved
end

-- Начало ночи: барьер, потеря несомого, вывод из коридора.
local function startNight(players: { Player })
	night = true
	barrier.Parent = world
	for _, player in players do
		if CarryService.LoseCarried(player, "наступила ночь (D37)") then
			Notify.Send(player, "Наступила ночь — недоставленный предмет потерян", "Stop")
		end
	end
	local moved = sweep(players)
	Log.Debug("NightService", ("Ночь: коридор закрыт, перенесено в Safe Zone: %d"):format(moved))
end

local function startDay()
	night = false
	barrier.Parent = nil
end

-- Применяет фазу: ночь (обычная или Судная) — правила ночи, день и подготовка — коридор открыт.
local function apply(state: GameTime.State, previous: GameTime.State?, players: { Player }?)
	local isNight = GameTime.IsNight(state.phase)
	local wasNight = previous ~= nil and GameTime.IsNight(previous.phase)
	if isNight and not (wasNight and night) then
		startNight(players or Players:GetPlayers())
	elseif not isNight and (night or previous == nil) then
		startDay()
	end
end

function NightService.Init(worldFolder: Instance)
	world = worldFolder
	local door = MapLayout.ZoneDoor
	local height = MapLayout.ZoneWallHeight
	barrier = Instance.new("Part")
	barrier.Name = "NightBarrier"
	barrier.Anchored = true
	barrier.Size = Vector3.new(door, height, 1)
	barrier.CFrame = CFrame.new(0, MapLayout.Heights.Ground + height / 2, MapLayout.ZoneStartZ(1))
	barrier.Material = Enum.Material.ForceField
	barrier.Color = Color3.fromHex("6FB8FF")
	barrier.CastShadow = false
	barrier.CanQuery = false
	barrier.CanTouch = false

	TimeService.OnPhaseChanged(function(state, previous)
		apply(state, previous, nil)
	end)
	apply(TimeService.Current(), nil, nil)
	task.spawn(function()
		while true do
			task.wait(GameConfig.Time.NightCheckSeconds)
			if night then
				sweep(Players:GetPlayers())
			end
		end
	end)
end

function NightService.IsNight(): boolean
	return night
end

-- Для серверных тестов: те же функции с явным списком игроков (тестовых нет в Players:GetPlayers()).
NightService.Handlers = {
	Apply = apply,
	Sweep = sweep,
	Barrier = function(): Part
		return barrier
	end,
}

return NightService

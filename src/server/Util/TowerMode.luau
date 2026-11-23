--!strict
-- Режим музея-небоскрёба (этап B, docs/TOWER_PLAN.md v3): изоляция технического прототипа. Включён только в Studio
-- с GameConfig.DevMode и GameConfig.Tower.DevOnly и только для явно включённых игроков (DevTools «TowerMode <userId>
-- on», серверные тесты, нагрузочная команда). В опубликованной игре For всегда false: TowerService ничего не строит,
-- DataService не трогает башню в профилях, лифт и постройка отказывают.
-- Реальные сохранения не трогаются: настоящему игроку режим включается, только если ProfileStore работает без
-- DataStore (Studio без доступа к API — профили только в памяти); тестовым игрокам — всегда (их профили — Mock).
-- Флаг держится по UserId до выключения (повторный вход тестового игрока — тот же режим).
-- Зависит от GameConfig, Vendor/ProfileStore.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local ProfileStore = require(ServerScriptService.Server.Vendor.ProfileStore)

local TowerMode = {}

local enabled: { [number]: boolean } = {}

-- Можно ли вообще включать режим башни на этом сервере.
function TowerMode.Allowed(): boolean
	return RunService:IsStudio() and GameConfig.DevMode == true and GameConfig.Tower.DevOnly == true
end

local function isTestPlayer(player: any): boolean
	return type(player) == "table" and player.IsTestPlayer == true
end

-- Включён ли режим башни у игрока.
function TowerMode.For(player: any): boolean
	if player == nil or not TowerMode.Allowed() then
		return false
	end
	return enabled[player.UserId] == true
end

-- Включить режим башни игроку. false и причина — нельзя (не Studio DevMode; настоящий игрок при доступе к DataStore).
function TowerMode.Enable(player: any): (boolean, string?)
	if not TowerMode.Allowed() then
		return false, "Режим башни — только в Studio с DevMode"
	end
	if not isTestPlayer(player) then
		local state = ProfileStore.DataStoreState
		if state == "NotReady" then
			return false,
				"ProfileStore ещё не готов — повторите через несколько секунд"
		end
		if state == "Access" then
			return false,
				"Studio с доступом к DataStore: режим башни не включается (сохранения были бы настоящими)"
		end
	end
	enabled[player.UserId] = true
	return true, nil
end

function TowerMode.Disable(player: any)
	if player then
		enabled[player.UserId] = nil
	end
end

return TowerMode

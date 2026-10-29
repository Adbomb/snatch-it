-- Инструменты проверки только в Studio (GameConfig.DevMode): папка ServerStorage.DevTools с BindableFunction,
-- которые вызывает MCP (require из MCP даёт отдельную копию модулей без данных игроков, BUGS.md).
-- В опубликованной игре не создаётся. Зависит от DataService, GymService, GameConfig.
--   Info(userId) → { coins, strength, dumbbellLevel, museumLevel }
--   GiveCoins(userId, amount) → новые монеты (пока нет экономики шага 7)

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local DataService = require(ServerScriptService.Server.Services.DataService)
local GymService = require(ServerScriptService.Server.Services.GymService)

local DevTools = {}

local function bind(folder: Folder, name: string, handler: (Player, ...any) -> any)
	local fn = Instance.new("BindableFunction")
	fn.Name = name
	fn.OnInvoke = function(userId: number, ...)
		local player = Players:GetPlayerByUserId(userId)
		if not player then
			return nil
		end
		return handler(player, ...)
	end
	fn.Parent = folder
end

function DevTools.Init()
	if not (RunService:IsStudio() and GameConfig.DevMode) then
		return
	end
	local folder = Instance.new("Folder")
	folder.Name = "DevTools"
	bind(folder, "Info", function(player)
		local data = DataService.GetData(player)
		return data
			and {
				coins = data.coins,
				strength = data.strength,
				dumbbellLevel = data.dumbbellLevel,
				museumLevel = data.museumLevel,
				museumPower = GymService.MuseumPower(player),
			}
	end)
	bind(folder, "GiveCoins", function(player, amount: number)
		local coins = DataService.AddCoins(player, amount)
		GymService.SyncAttributes(player)
		return coins
	end)
	folder.Parent = ServerStorage
end

return DevTools

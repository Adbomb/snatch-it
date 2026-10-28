-- Точка входа сервера: создаёт RemoteEvent'ы и мир, запускает сервисы по порядку.
-- Связывает вход и выход игрока между сервисами. Зависит от всех Services.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local DataService = require(Server.Services.DataService)
local ItemSpawnService = require(Server.Services.ItemSpawnService)
local MuseumService = require(Server.Services.MuseumService)
local PlotService = require(Server.Services.PlotService)
local StorageService = require(Server.Services.StorageService)
local Notify = require(Server.Util.Notify)
local PartBuilder = require(Server.Util.PartBuilder)

Remotes.CreateAll()

local world = PartBuilder.CreateWorldFolder()
PartBuilder.BuildPlaza(world)
PlotService.Init(world)
CarryService.Init()
MuseumService.Init()
StorageService.Init()
ItemSpawnService.Init(world)

local function onPlayerAdded(player: Player)
	local plot = PlotService.Assign(player)
	if not plot then
		player:Kick(
			"На сервере нет свободного музея. Зайдите на другой сервер."
		)
		return
	end
	if not DataService.LoadAsync(player) then
		return
	end
	MuseumService.LoadMuseum(player)
	StorageService.Sync(player)
	Notify.Send(
		player,
		("Ваш музей — участок %d (ищите табличку со своим именем)"):format(
			plot.index
		)
	)
end

local function onPlayerRemoving(player: Player)
	CarryService.OnPlayerRemoving(player)
	MuseumService.UnloadMuseum(player)
	PlotService.Release(player)
	DataService.Release(player)
end

Players.PlayerAdded:Connect(onPlayerAdded)
Players.PlayerRemoving:Connect(onPlayerRemoving)
for _, player in Players:GetPlayers() do
	task.spawn(onPlayerAdded, player)
end

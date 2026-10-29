-- Точка входа сервера: создаёт RemoteEvent'ы и мир, запускает сервисы по порядку.
-- Связывает вход и выход игрока между сервисами. Зависит от всех Services.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local LegoMaterial = require(ReplicatedStorage.Shared.LegoMaterial)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local DataService = require(Server.Services.DataService)
local ItemSpawnService = require(Server.Services.ItemSpawnService)
local MuseumService = require(Server.Services.MuseumService)
local PlotService = require(Server.Services.PlotService)
local StorageService = require(Server.Services.StorageService)
local ItemFactory = require(Server.Util.ItemFactory)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local PartBuilder = require(Server.Util.PartBuilder)
local MeshBuilder = require(Server.World.MeshBuilder)
local ModelBuilder = require(Server.World.ModelBuilder)
local Preview = require(Server.World.Preview)
local WorldBuilder = require(Server.World.WorldBuilder)

-- Предпросмотр из режима редактирования в игру попадать не должен.
Preview.Clear()

Remotes.CreateAll()
LegoMaterial.Apply()

MeshBuilder.Preload() -- меши музеев и гантелей из Blender (ждёт загрузку один раз)
local world = PartBuilder.CreateWorldFolder()
ModelBuilder.SetTemplateParent(ServerStorage)
WorldBuilder.Build(world)
WorldBuilder.BuildWater()
-- Baseplate шаблона закрыл бы воду вокруг острова.
local baseplate = workspace:FindFirstChild("Baseplate")
if baseplate then
	baseplate:Destroy()
end
-- Игроки появляются только в начале аллеи: чужие SpawnLocation места (например, из шаблона) выключаются.
for _, spawn in workspace:GetDescendants() do
	if spawn:IsA("SpawnLocation") and not spawn:IsDescendantOf(world) then
		spawn.Enabled = false
		spawn.Transparency = 1
		spawn.CanCollide = false
		local decal = spawn:FindFirstChildOfClass("Decal")
		if decal then
			decal.Transparency = 1
		end
	end
end
PlotService.Init(world)
ItemFactory.Preload() -- меши предметов из Blender (ждёт загрузку один раз)
CarryService.Init()
MuseumService.Init()
StorageService.Init()
ItemSpawnService.Init(world)

local partCount = ModelBuilder.CountParts(world)
Log.Debug("Main", ("Карта: %d частей (бюджет %d)"):format(partCount, GameConfig.World.MaxParts))
if partCount > GameConfig.World.MaxParts then
	Log.Warn("Main", ("Карта превышает бюджет: %d > %d частей"):format(partCount, GameConfig.World.MaxParts))
end

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
	PlotService.ShowLevel(plot, DataService.GetData(player).museumLevel)
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

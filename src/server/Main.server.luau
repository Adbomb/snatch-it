-- Точка входа сервера: создаёт RemoteEvent'ы и мир, запускает сервисы по порядку.
-- Вход и выход игрока — Services/PlayerSession. Зависит от всех Services.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local LegoMaterial = require(ReplicatedStorage.Shared.LegoMaterial)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local GymService = require(Server.Services.GymService)
local ItemSpawnService = require(Server.Services.ItemSpawnService)
local MuseumService = require(Server.Services.MuseumService)
local NightService = require(Server.Services.NightService)
local PlayerSession = require(Server.Services.PlayerSession)
local PlotService = require(Server.Services.PlotService)
local StorageService = require(Server.Services.StorageService)
local TimeService = require(Server.Services.TimeService)
local DevTools = require(Server.Util.DevTools)
local ItemFactory = require(Server.Util.ItemFactory)
local Log = require(Server.Util.Log)
local PartBuilder = require(Server.Util.PartBuilder)
local MeshBuilder = require(Server.World.MeshBuilder)
local ModelBuilder = require(Server.World.ModelBuilder)
local Preview = require(Server.World.Preview)
local WorldBuilder = require(Server.World.WorldBuilder)

-- Предпросмотр из режима редактирования в игру попадать не должен.
Preview.Clear()

Remotes.CreateAll()
LegoMaterial.Apply()

local world = PartBuilder.CreateWorldFolder()
ModelBuilder.SetTemplateParent(ServerStorage)
WorldBuilder.Build(world)
WorldBuilder.BuildWater()
-- Baseplate шаблона закрыл бы воду вокруг острова.
local baseplate = workspace:FindFirstChild("Baseplate")
if baseplate then
	baseplate:Destroy()
end
-- Игроки появляются только на площади (D35): чужие SpawnLocation места (например, из шаблона) выключаются.
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
-- Меши музеев и гантелей из Blender (ждёт загрузку один раз) — после карты и точки появления: игрок,
-- вошедший во время загрузки, появляется уже на площади.
MeshBuilder.Preload()
PlotService.Init(world)
ItemFactory.Preload() -- меши предметов из Blender (ждёт загрузку один раз)
CarryService.Init()
MuseumService.Init()
StorageService.Init()
ItemSpawnService.Init(world)
GymService.Init()
TimeService.Init()
NightService.Init(world)
DevTools.Init()

local partCount = ModelBuilder.CountParts(world)
Log.Debug("Main", ("Карта: %d частей (бюджет %d)"):format(partCount, GameConfig.World.MaxParts))
if partCount > GameConfig.World.MaxParts then
	Log.Warn("Main", ("Карта превышает бюджет: %d > %d частей"):format(partCount, GameConfig.World.MaxParts))
end

Players.PlayerAdded:Connect(PlayerSession.Join)
Players.PlayerRemoving:Connect(PlayerSession.Leave)
for _, player in Players:GetPlayers() do
	task.spawn(PlayerSession.Join, player)
end

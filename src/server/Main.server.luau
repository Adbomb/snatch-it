-- Точка входа сервера: создаёт RemoteEvent'ы и мир, запускает сервисы по порядку.
-- Вход и выход игрока — Services/PlayerSession. На тестовом сервере владельца (Util/OwnerTest) играет только
-- владелец, профиль — в памяти (ничего не сохраняется). Зависит от всех Services.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local LegoMaterial = require(ReplicatedStorage.Shared.LegoMaterial)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Server = ServerScriptService.Server
local BattleService = require(Server.Services.BattleService)
local BossLootService = require(Server.Services.BossLootService)
local BossService = require(Server.Services.BossService)
local CarryService = require(Server.Services.CarryService)
local GymService = require(Server.Services.GymService)
local IncomeService = require(Server.Services.IncomeService)
local MoveGuard = require(Server.Services.MoveGuard)
local MuseumService = require(Server.Services.MuseumService)
local NightService = require(Server.Services.NightService)
local OwnerTestService = require(Server.Services.OwnerTestService)
local PlayerSession = require(Server.Services.PlayerSession)
local PlotService = require(Server.Services.PlotService)
local InventoryService = require(Server.Services.InventoryService)
local TowerService = require(Server.Services.TowerService)
local ElevatorService = require(Server.Services.ElevatorService)
local TheftService = require(Server.Services.TheftService)
local PvpService = require(Server.Services.PvpService)
local DefenseService = require(Server.Services.DefenseService)
local MuseumUpgradeService = require(Server.Services.MuseumUpgradeService)
local ShopService = require(Server.Services.ShopService)
local AnnounceService = require(Server.Services.AnnounceService)
local CatchService = require(Server.Services.CatchService)
local ThrowService = require(Server.Services.ThrowService)
local TutorialService = require(Server.Services.TutorialService)
local VaultService = require(Server.Services.VaultService)
local TimeService = require(Server.Services.TimeService)
local DevTools = require(Server.Util.DevTools)
local ItemFactory = require(Server.Util.ItemFactory)
local Log = require(Server.Util.Log)
local OwnerTest = require(Server.Util.OwnerTest)
local PartBuilder = require(Server.Util.PartBuilder)
local MeshBuilder = require(Server.World.MeshBuilder)
local ModelBuilder = require(Server.World.ModelBuilder)
local Preview = require(Server.World.Preview)
local WorldBuilder = require(Server.World.WorldBuilder)

-- Время этапов старта (этап C.2: долгая загрузка) — одной строкой в журнал после запуска сервисов.
local startedAt = os.clock()
local marks: { string } = {}
local function mark(name: string)
	table.insert(marks, ("%s %.2f"):format(name, os.clock() - startedAt))
end

-- Предпросмотр из режима редактирования в игру попадать не должен (карта и временные показы моделей из Blender).
Preview.Clear()
for _, name in { "__WondersPreview", "__BossPreview", "__ArtPreview" } do
	local folder = workspace:FindFirstChild(name)
	if folder then
		folder:Destroy()
	end
end

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
mark("карта")
MeshBuilder.Preload()
mark("меши музеев")
PlotService.Init(world)
VaultService.Init() -- хранилище только владельцу (D48-C)
ItemFactory.Preload() -- меши предметов из Blender (ждёт загрузку один раз)
mark("меши предметов")
MoveGuard.Init() -- невозможные перемещения (D52)
CarryService.Init()
MuseumService.Init()
InventoryService.Init()
TowerService.Init() -- музей-небоскрёб, этап B: только режим башни DEV (Util/TowerMode), в игре ничего не строит
ElevatorService.Init() -- лифт башни (этап B)
TheftService.Init()
PvpService.Init()
DefenseService.Init()
MuseumUpgradeService.Init() -- покупка уровней музея 2–10 (D56)
ShopService.Init() -- магазин Ловибумов (D55)
BossLootService.Init(world)
BossService.Init(world) -- модель босса 1 (меши грузятся один раз)
mark("боссы")
BattleService.Init()
AnnounceService.Init() -- D74: объявления о редких этажах с других серверов
CatchService.Init() -- поимка «Ловибум» (D55): «Поймать» у существа → мини-игра → бой
ThrowService.Init() -- D75: бросок вдаль
TutorialService.Init(world) -- обязательное обучение новичка (D55)
IncomeService.Init()
GymService.Init()
TimeService.Init()
NightService.Init(world)
DevTools.Init()
OwnerTestService.Init() -- тестовый режим владельца (только подтверждённое DEV-место, Util/OwnerTest)

mark("всё")
Log.Debug("Main", "Старт, с от начала: " .. table.concat(marks, ", "))

local partCount = ModelBuilder.CountParts(world)
Log.Debug("Main", ("Карта: %d частей (бюджет %d)"):format(partCount, GameConfig.World.MaxParts))
if partCount > GameConfig.World.MaxParts then
	Log.Warn(
		"Main",
		("Карта превышает бюджет: %d > %d частей"):format(
			partCount,
			GameConfig.World.MaxParts
		)
	)
end

-- Вход игрока. Тестовый сервер владельца: чужих не пускает, профиль владельца — в памяти (ProfileStore.Mock: ни
-- PlayerData, ни Transfers не пишутся), обучение считается пройденным.
local function join(player: Player)
	if OwnerTest.IsTestServer() then
		if not OwnerTest.IsOwner(player) then
			player:Kick("Это закрытый тестовый сервер владельца.")
			return
		end
		if PlayerSession.Join(player, { mock = true, veteran = true }) then
			OwnerTestService.Welcome(player)
		end
		return
	end
	PlayerSession.Join(player)
end

Players.PlayerAdded:Connect(join)
Players.PlayerRemoving:Connect(PlayerSession.Leave)
for _, player in Players:GetPlayers() do
	task.spawn(join, player)
end

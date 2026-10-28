-- Появление предметов на карте в точках с тегом ItemSpawn (DESIGN.md §3). Если точек нет — создаёт 6 на площади.
-- Точка освобождается, когда предмет с неё подняли; через RespawnDelay секунд там появляется новый.
-- Зависит от ItemRegistry, CarryService, Util/ItemFactory, Util/PartBuilder, Config.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local CarryService = require(ServerScriptService.Server.Services.CarryService)
local ItemRegistry = require(ServerScriptService.Server.Services.ItemRegistry)
local ItemFactory = require(ServerScriptService.Server.Util.ItemFactory)
local Log = require(ServerScriptService.Server.Util.Log)
local PartBuilder = require(ServerScriptService.Server.Util.PartBuilder)

local SPAWN_TAG = "ItemSpawn"

local itemIds: { string } = {}
local pointByUid: { [string]: BasePart } = {}
local itemsFolder: Folder
local random = Random.new()

local ItemSpawnService = {}

local function createDefaultPoints(world: Folder)
	local folder = Instance.new("Folder")
	folder.Name = "ItemSpawns"
	folder.Parent = world
	local cfg = GameConfig.Spawn
	for i = 1, cfg.DefaultPointCount do
		local angle = (i - 1) / cfg.DefaultPointCount * math.pi * 2
		local point = PartBuilder.MakePart({
			name = "ItemSpawn_" .. i,
			size = Vector3.new(2, 0.2, 2),
			cframe = CFrame.new(
				math.cos(angle) * cfg.DefaultPointRadius,
				PartBuilder.FloorTop + 0.1,
				math.sin(angle) * cfg.DefaultPointRadius
			),
			color = Color3.fromRGB(255, 210, 0),
			transparency = if GameConfig.DevMode then 0.6 else 1,
			canCollide = false,
			parent = folder,
		})
		point.CanQuery = false
		point.CanTouch = false
		point:SetAttribute("Tier", "Center")
		CollectionService:AddTag(point, SPAWN_TAG)
	end
	Log.Debug(
		"ItemSpawnService",
		("Точек ItemSpawn не было — создано %d на площади"):format(cfg.DefaultPointCount)
	)
end

-- Этап 1: Tier точки не учитывается, предмет выбирается случайно из всех в Config/Items.
local function spawnAt(point: BasePart)
	if not point.Parent then
		return
	end
	local itemId = itemIds[random:NextInteger(1, #itemIds)]
	local part = ItemFactory.Create(itemId)
	part.CFrame = point.CFrame * CFrame.new(0, point.Size.Y / 2 + part.Size.Y / 2, 0)
	local uid = ItemRegistry.CreateOnMap(itemId, part)
	pointByUid[uid] = point
	part.Parent = itemsFolder
	CarryService.RegisterMapItem(uid, part)
end

local function onRegistryChanged(uid: string, fromState: string)
	local point = pointByUid[uid]
	if not point or fromState ~= "OnMap" then
		return
	end
	pointByUid[uid] = nil
	task.delay(GameConfig.Spawn.RespawnDelay, spawnAt, point)
end

function ItemSpawnService.Init(world: Folder)
	for id in Items do
		table.insert(itemIds, id)
	end
	table.sort(itemIds)

	itemsFolder = Instance.new("Folder")
	itemsFolder.Name = "Items"
	itemsFolder.Parent = world

	if #CollectionService:GetTagged(SPAWN_TAG) == 0 then
		createDefaultPoints(world)
	end
	ItemRegistry.OnChanged(onRegistryChanged)
	for _, point in CollectionService:GetTagged(SPAWN_TAG) do
		if point:IsA("BasePart") then
			spawnAt(point)
		end
	end
end

return ItemSpawnService

-- Появление предметов в зонах добычи (D15): точки с тегом ItemSpawn стоят на постаментах, у точки атрибут Zone.
-- Если точек нет — ставит их по MapLayout. Редкость — по шансам зоны (Progression: плавно от зоны 1 к зоне 10,
-- Secret — с SecretFromZone), лежащих и несомых Legendary и Secret на сервере не больше GameConfig.MaxOnMap.
-- Точка освобождается, когда предмет с неё подняли;
-- через RespawnDelay секунд там появляется новый. D10: брошенный предмет, который никто не трогает, мигает и исчезает.
-- Зависит от ItemRegistry, CarryService, Util/ItemFactory, Util/PartBuilder, World/MapLayout, Config.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local Rarities = require(ReplicatedStorage.Shared.Config.Rarities)
local CarryService = require(ServerScriptService.Server.Services.CarryService)
local ItemRegistry = require(ServerScriptService.Server.Services.ItemRegistry)
local ItemFactory = require(ServerScriptService.Server.Util.ItemFactory)
local Log = require(ServerScriptService.Server.Util.Log)
local PartBuilder = require(ServerScriptService.Server.Util.PartBuilder)
local MapLayout = require(ServerScriptService.Server.World.MapLayout)

local SPAWN_TAG = "ItemSpawn"

local itemsByRarity: { [string]: { string } } = {}
local pointByUid: { [string]: BasePart } = {}
local looseTimers: { [string]: number } = {} -- uid → номер таймера D10
local timerCounter = 0
local itemsFolder: Folder
local random = Random.new()

local ItemSpawnService = {}

local function makePoint(folder: Folder, name: string, position: Vector3, zone: number)
	local point = PartBuilder.MakePart({
		name = name,
		size = Vector3.new(2, 0.2, 2),
		cframe = CFrame.new(position + Vector3.new(0, 0.1, 0)),
		color = Color3.fromRGB(255, 210, 0),
		transparency = if GameConfig.DevMode then 0.6 else 1,
		canCollide = false,
		parent = folder,
	})
	point.CanQuery = false
	point.CanTouch = false
	point:SetAttribute("Zone", zone)
	CollectionService:AddTag(point, SPAWN_TAG)
end

-- Точки на постаментах всех зон (MapLayout).
local function createDefaultPoints(world: Folder)
	local folder = Instance.new("Folder")
	folder.Name = "ItemSpawns"
	folder.Parent = world
	for _, spec in MapLayout.SpawnPoints() do
		makePoint(folder, spec.name, spec.position, spec.zone)
	end
	Log.Debug(
		"ItemSpawnService",
		("Точек ItemSpawn не было — создано %d"):format(#folder:GetChildren())
	)
end

-- Веса редкостей в зоне: линейно от RarityFirst (зона 1) к RarityLast (последняя зона); Secret — только
-- с SecretFromZone; редкости, чей лимит на сервере исчерпан, выпадают из броска.
local function zoneWeights(zone: number): { [string]: number }
	local progression = GameConfig.Progression
	local f = (zone - 1) / math.max(#GameConfig.Zones - 1, 1)
	local weights = {}
	for _, rarity in Rarities.Order do
		local first, last = progression.RarityFirst[rarity] or 0, progression.RarityLast[rarity] or 0
		local weight = first + (last - first) * f
		local limit = GameConfig.MaxOnMap[rarity]
		if rarity == "Secret" and zone < progression.SecretFromZone then
			weight = 0
		elseif limit and ItemRegistry.CountLoose(rarity) >= limit then
			weight = 0
		end
		weights[rarity] = weight
	end
	return weights
end

local function rollRarity(weights: { [string]: number }): string
	local total = 0
	for _, rarity in Rarities.Order do
		total += weights[rarity]
	end
	local roll = random:NextNumber(0, total)
	for _, rarity in Rarities.Order do
		local weight = weights[rarity]
		if weight > 0 and roll <= weight then
			return rarity
		end
		roll -= weight
	end
	return Rarities.Order[1]
end

-- Редкость по шансам зоны, затем предмет этой редкости (равные шансы); нет такой — ближайшая более низкая.
local function chooseItemId(zone: number): string?
	local rarity = rollRarity(zoneWeights(zone))
	for rank = Rarities.Rank(rarity), 1, -1 do
		local pool = itemsByRarity[Rarities.Order[rank]]
		if pool and #pool > 0 then
			return pool[random:NextInteger(1, #pool)]
		end
	end
	return nil
end

local function spawnAt(point: BasePart)
	if not point.Parent then
		return
	end
	local zone = point:GetAttribute("Zone")
	local itemId = chooseItemId(if type(zone) == "number" and GameConfig.Zones[zone] then zone else 1)
	if not itemId then
		Log.Warn("ItemSpawnService", "Нет предметов для появления — проверьте Config/Items")
		return
	end
	local part = ItemFactory.Create(itemId)
	part.CFrame = point.CFrame * CFrame.new(0, point.Size.Y / 2 + part.Size.Y / 2, 0)
	local uid = ItemRegistry.CreateOnMap(itemId, part)
	pointByUid[uid] = point
	part.Parent = itemsFolder
	CarryService.RegisterMapItem(uid, part)
end

-- D10: через LooseDespawnTime секунд без касания предмет исчезает, последние LooseBlinkTime секунд мигает.
local function startLooseTimer(uid: string)
	local cfg = GameConfig.Spawn
	timerCounter += 1
	local timer = timerCounter
	looseTimers[uid] = timer
	task.spawn(function()
		task.wait(cfg.LooseDespawnTime - cfg.LooseBlinkTime)
		local blinkEnd = os.clock() + cfg.LooseBlinkTime
		local hidden = false
		while looseTimers[uid] == timer and os.clock() < blinkEnd do
			local entry = ItemRegistry.Get(uid)
			if not entry or not entry.part then
				return
			end
			hidden = not hidden
			ItemFactory.SetVisualTransparency(entry.part, if hidden then cfg.BlinkTransparency else 0)
			task.wait(cfg.BlinkInterval)
		end
		if looseTimers[uid] ~= timer then
			return
		end
		looseTimers[uid] = nil
		local entry = ItemRegistry.Get(uid)
		if entry and entry.state == "OnMap" and ItemRegistry.Discard(uid, "лежал без дела (D10)") then
			if entry.part then
				entry.part:Destroy()
			end
		end
	end)
end

local function onRegistryChanged(uid: string, fromState: string, toState: string?, entry: ItemRegistry.Entry)
	-- Точка освобождается, как только с неё подняли предмет (D10).
	local point = pointByUid[uid]
	if point and fromState == "OnMap" then
		pointByUid[uid] = nil
		task.delay(GameConfig.Spawn.RespawnDelay, spawnAt, point)
	end

	if fromState == "Carried" and toState == "OnMap" then
		startLooseTimer(uid)
	elseif looseTimers[uid] and toState ~= "OnMap" then
		-- Подняли или удалили: таймер сброшен, предмет снова непрозрачный.
		looseTimers[uid] = nil
		if entry.part then
			ItemFactory.SetVisualTransparency(entry.part, 0)
		end
	end
end

function ItemSpawnService.Init(world: Folder)
	for id, def in Items do
		itemsByRarity[def.rarity] = itemsByRarity[def.rarity] or {}
		table.insert(itemsByRarity[def.rarity], id)
	end
	for _, pool in itemsByRarity do
		table.sort(pool)
	end

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

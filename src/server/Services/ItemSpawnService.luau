-- Появление предметов в зонах добычи (D15): точки с тегом ItemSpawn стоят на постаментах, у точки атрибут Zone.
-- Если точек нет — ставит их по MapLayout. Редкость — по весам зоны (GameConfig.Zones), Legendary на сервере
-- не больше MaxLegendaryOnMap, Secret не появляется. Точка освобождается, когда предмет с неё подняли;
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
local NEVER_SPAWNS = "Secret" -- D15: Secret пока не появляется нигде

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

-- Редкость по весам зоны; withoutLegendary — повторный бросок, когда лимит Legendary исчерпан.
local function rollRarity(weights: { [string]: number }, withoutLegendary: boolean): string
	local total = 0
	for _, rarity in Rarities.Order do
		if rarity ~= NEVER_SPAWNS and not (withoutLegendary and rarity == "Legendary") then
			total += weights[rarity] or 0
		end
	end
	local roll = random:NextNumber(0, total)
	for _, rarity in Rarities.Order do
		if rarity ~= NEVER_SPAWNS and not (withoutLegendary and rarity == "Legendary") then
			local weight = weights[rarity] or 0
			if weight > 0 and roll <= weight then
				return rarity
			end
			roll -= weight
		end
	end
	return Rarities.Order[1]
end

-- Редкость по весам зоны, затем предмет этой редкости (равные шансы); нет такой — ближайшая более низкая.
local function chooseItemId(zone: number): string?
	local weights = GameConfig.Zones[zone].weights
	local rarity = rollRarity(weights, false)
	if rarity == "Legendary" and ItemRegistry.CountLoose("Legendary") >= GameConfig.Spawn.MaxLegendaryOnMap then
		rarity = rollRarity(weights, true)
	end
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
		if def.rarity ~= NEVER_SPAWNS then
			itemsByRarity[def.rarity] = itemsByRarity[def.rarity] or {}
			table.insert(itemsByRarity[def.rarity], id)
		end
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

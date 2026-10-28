-- Появление предметов на карте в точках с тегом ItemSpawn (DESIGN.md §3, D11). Если точек нет —
-- строит 12: 4 Near у музеев, 4 Center на площади, 4 Far на крышах и окраине.
-- Редкость выбирается по весам Tier точки, Legendary на сервере не больше MaxLegendaryOnMap, Secret не появляется.
-- Точка освобождается, когда предмет с неё подняли; через RespawnDelay секунд там появляется новый.
-- D10: брошенный предмет, который никто не трогает, мигает и исчезает.
-- Зависит от ItemRegistry, CarryService, Util/ItemFactory, Util/PartBuilder, Config.

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

local SPAWN_TAG = "ItemSpawn"
local NEVER_SPAWNS = "Secret" -- D11: на этапе 2 Secret не появляется

local itemsByRarity: { [string]: { string } } = {}
local pointByUid: { [string]: BasePart } = {}
local looseTimers: { [string]: number } = {} -- uid → номер таймера D10
local timerCounter = 0
local itemsFolder: Folder
local random = Random.new()

local ItemSpawnService = {}

local function makePoint(folder: Folder, name: string, cframe: CFrame, tier: string)
	local point = PartBuilder.MakePart({
		name = name,
		size = Vector3.new(2, 0.2, 2),
		cframe = cframe * CFrame.new(0, 0.1, 0),
		color = Color3.fromRGB(255, 210, 0),
		transparency = if GameConfig.DevMode then 0.6 else 1,
		canCollide = false,
		parent = folder,
	})
	point.CanQuery = false
	point.CanTouch = false
	point:SetAttribute("Tier", tier)
	CollectionService:AddTag(point, SPAWN_TAG)
end

local function ringCFrame(angleDeg: number, radius: number): CFrame
	local angle = math.rad(angleDeg)
	return CFrame.new(math.cos(angle) * radius, PartBuilder.FloorTop, math.sin(angle) * radius)
end

local function createDefaultPoints(world: Folder)
	local cfg = GameConfig.Spawn
	local folder = Instance.new("Folder")
	folder.Name = "ItemSpawns"
	folder.Parent = world

	-- Сдвиги углов разводят точки разных типов, чтобы они не стояли на одной линии с музеями.
	for i = 1, cfg.CenterCount do
		makePoint(folder, "Center_" .. i, ringCFrame(45 + (i - 1) * 360 / cfg.CenterCount, cfg.CenterRadius), "Center")
	end
	for i = 1, cfg.NearCount do
		makePoint(folder, "Near_" .. i, ringCFrame(22.5 + (i - 1) * 360 / cfg.NearCount, cfg.NearRadius), "Near")
	end
	local farCount = 0
	for _, top in PartBuilder.BuildRoofs(world) do
		farCount += 1
		makePoint(folder, "Far_" .. farCount, top, "Far")
	end
	makePoint(folder, "Far_" .. farCount + 1, ringCFrame(cfg.FarGroundAngle, cfg.FarGroundRadius), "Far")

	Log.Debug(
		"ItemSpawnService",
		("Точек ItemSpawn не было — создано %d"):format(#folder:GetChildren())
	)
end

-- Редкость по весам Tier; withoutLegendary — повторный бросок, когда лимит Legendary исчерпан.
local function rollRarity(tier: string, withoutLegendary: boolean): string
	local weights = GameConfig.Spawn.TierWeights[tier] or GameConfig.Spawn.TierWeights[GameConfig.Spawn.DefaultTier]
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

-- D11: редкость по весам, затем предмет этой редкости (равные шансы); нет такой — ближайшая более низкая.
local function chooseItemId(tier: string): string?
	local rarity = rollRarity(tier, false)
	if rarity == "Legendary" and ItemRegistry.CountLoose("Legendary") >= GameConfig.Spawn.MaxLegendaryOnMap then
		rarity = rollRarity(tier, true)
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
	local tier = point:GetAttribute("Tier")
	local itemId = chooseItemId(if type(tier) == "string" then tier else GameConfig.Spawn.DefaultTier)
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
			entry.part.Transparency = if hidden then cfg.BlinkTransparency else 0
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
			entry.part.Transparency = 0
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

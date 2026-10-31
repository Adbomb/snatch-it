-- Предметы у боссов (D37): у каждого из 10 боссов 4 слота на постаментах вокруг него (MapLayout.ArtSlots). Каждый
-- слот независимо выбирает редкость по шансам группы босса (Progression.BossLoot), затем предмет этой редкости из
-- коллекции босса (Config/Items). После каждой ночи (на рассвете) все 4 слота заполняются заново — нетронутые
-- тоже, новые uid. Забранный предмет освобождает слот до следующего рассвета. Забрать предмет — после победы над
-- боссом (этап 4); пока боя нет — только в тестовом режиме Studio (GameConfig.Bosses.FreeTakeInStudio).
-- D10: брошенный предмет, который никто не трогает, мигает и исчезает.
-- Зависит от ItemRegistry, CarryService, TimeService, Util/ItemFactory, Util/Validate, Util/Notify, Util/Log,
-- World/MapLayout, Shared/GameTime, Config.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local Rarities = require(ReplicatedStorage.Shared.Config.Rarities)
local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local TimeService = require(Server.Services.TimeService)
local ItemFactory = require(Server.Util.ItemFactory)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local Validate = require(Server.Util.Validate)
local MapLayout = require(Server.World.MapLayout)

type Slot = { boss: number, slot: number, point: CFrame, uid: string? }

local loot = GameConfig.Progression.BossLoot
local slots: { [number]: { [number]: Slot } } = {}
local pools: { [number]: { [string]: { string } } } = {} -- [босс][редкость] = id предметов
local looseTimers: { [string]: number } = {} -- uid → номер таймера D10
local timerCounter = 0
local itemsFolder: Folder
local random = Random.new()

local BossLootService = {}

-- Шансы редкостей (%) для босса boss.
function BossLootService.Chances(boss: number): { [string]: number }
	for _, tier in loot.Tiers do
		if boss >= tier.from and boss <= tier.to then
			return tier.chances
		end
	end
	error("Нет шансов для босса " .. tostring(boss))
end

-- Редкость одного слота босса boss (rng — для тестов).
function BossLootService.RollRarity(boss: number, rng: Random?): string
	local chances = BossLootService.Chances(boss)
	local roll = (rng or random):NextNumber(0, 100)
	for _, rarity in Rarities.Order do
		local chance = chances[rarity] or 0
		if chance > 0 and roll < chance then
			return rarity
		end
		roll -= chance
	end
	return Rarities.Order[1]
end

-- Предмет редкости rarity из коллекции босса (равные шансы). nil — в коллекции нет такой редкости.
function BossLootService.ChooseItem(boss: number, rarity: string, rng: Random?): string?
	local pool = pools[boss] and pools[boss][rarity]
	if not pool or #pool == 0 then
		return nil
	end
	return pool[(rng or random):NextInteger(1, #pool)]
end

-- Можно ли забрать предмет без боя: только тестовый режим Studio (D37), пока нет боя (этап 4).
function BossLootService.FreeTakeAllowed(): boolean
	return RunService:IsStudio() and GameConfig.DevMode and GameConfig.Bosses.FreeTakeInStudio
end

local tryTake: (Player, Slot) -> ()

local function addPrompt(part: BasePart, entry: Slot)
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "TakePrompt"
	prompt.ActionText = "Забрать"
	prompt.ObjectText = Items[part:GetAttribute("ItemId") :: string].displayName
	prompt.HoldDuration = GameConfig.Bosses.TakeHold
	prompt.MaxActivationDistance = GameConfig.Bosses.TakeDistance
	prompt.RequiresLineOfSight = false
	prompt.Parent = part
	prompt.Triggered:Connect(function(player)
		tryTake(player, entry)
	end)
end

-- Новый предмет в слоте (старый, если он ещё у босса, убирается).
local function fill(entry: Slot)
	local old = entry.uid
	if old then
		local current = ItemRegistry.Get(old)
		if current and current.state == "AtBoss" then
			ItemRegistry.Discard(old, "обновление слотов босса (D37)")
			if current.part then
				current.part:Destroy()
			end
		end
		entry.uid = nil
	end
	local itemId = BossLootService.ChooseItem(entry.boss, BossLootService.RollRarity(entry.boss))
	if not itemId then
		Log.Warn("BossLootService", ("Босс %d: нет предмета нужной редкости"):format(entry.boss))
		return
	end
	local part = ItemFactory.Create(itemId)
	part.Anchored = true
	part.CFrame = entry.point * CFrame.new(0, part.Size.Y / 2, 0)
	part:SetAttribute("Boss", entry.boss)
	part:SetAttribute("BossSlot", entry.slot)
	part.Parent = itemsFolder
	entry.uid = ItemRegistry.CreateAtBoss(itemId, part, entry.boss, entry.slot)
	addPrompt(part, entry)
end

-- Заполнить заново все слоты всех боссов.
local function refresh()
	for _, bossSlots in slots do
		for _, entry in bossSlots do
			fill(entry)
		end
	end
	Log.Debug("BossLootService", "Слоты всех боссов обновлены")
end

tryTake = function(player: Player, entry: Slot)
	local uid = entry.uid
	local item = uid and ItemRegistry.Get(uid)
	if not uid or not item or item.state ~= "AtBoss" or not item.part then
		return
	end
	if not BossLootService.FreeTakeAllowed() then
		Notify.Send(player, "Чтобы забрать предмет, победите босса", "Stop")
		return
	end
	if GameTime.IsNight(TimeService.Current().phase) then
		return
	end
	if ItemRegistry.GetCarriedBy(player) then
		Notify.Send(player, "Руки заняты — сначала бросьте предмет (G)", "Stop")
		return
	end
	if not Validate.IsNear(player, item.part.Position, GameConfig.Bosses.TakeDistance) then
		return
	end
	if not ItemRegistry.Transition(uid, "Carried", { carrier = player }) then
		return
	end
	entry.uid = nil -- слот пуст до рассвета
	local prompt = item.part:FindFirstChild("TakePrompt")
	if prompt then
		prompt:Destroy()
	end
	CarryService.RegisterMapItem(uid, item.part)
	CarryService.AttachCarried(player, uid)
end

-- D10: через LooseDespawnTime секунд без касания брошенный предмет исчезает, последние LooseBlinkTime мигает.
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

function BossLootService.Init(world: Folder)
	for id, def in Items do
		pools[def.boss] = pools[def.boss] or {}
		pools[def.boss][def.rarity] = pools[def.boss][def.rarity] or {}
		table.insert(pools[def.boss][def.rarity], id)
	end
	for _, byRarity in pools do
		for _, pool in byRarity do
			table.sort(pool)
		end
	end
	itemsFolder = Instance.new("Folder")
	itemsFolder.Name = "Items"
	itemsFolder.Parent = world
	for _, spec in MapLayout.ArtSlotPoints() do
		slots[spec.zone] = slots[spec.zone] or {}
		slots[spec.zone][spec.slot] = { boss = spec.zone, slot = spec.slot, point = spec.cframe, uid = nil }
	end
	ItemRegistry.OnChanged(onRegistryChanged)
	refresh()
	TimeService.OnPhaseChanged(function(state, previous)
		if state.phase == "Day" and previous and GameTime.IsNight(previous.phase) then
			refresh()
		end
	end)
end

-- Для серверных тестов: слоты, обновление и попытка забрать.
BossLootService.Handlers = {
	Slots = function(): { [number]: { [number]: Slot } }
		return slots
	end,
	Refresh = refresh,
	Take = function(player: Player, boss: number, slot: number)
		tryTake(player, slots[boss][slot])
	end,
}

return BossLootService

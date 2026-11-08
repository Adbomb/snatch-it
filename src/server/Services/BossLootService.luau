-- Предметы у боссов (D37): у каждого из 10 боссов 4 слота вокруг него — на постаментах (MapLayout.ArtSlots) или прямо
-- на площадке босса (MapLayout.Arenas, D43). Каждый слот независимо выбирает редкость по шансам группы босса
-- (Progression.BossLoot), затем предмет этой редкости из коллекции босса (Config/Items). После каждой ночи (на
-- рассвете) все 4 слота заполняются заново — нетронутые тоже, новые uid. Забранный предмет освобождает слот до
-- следующего рассвета. Забрать предмет — только победой над боссом: «Забрать» у предмета начинает бой (BattleService
-- через OnTakeRequest), на время боя предмет закреплён за бойцом, подсказки у занятого босса выключены. У боссов без
-- боя (пока 3–10) забрать без боя можно только в тестовом режиме Studio (GameConfig.Bosses.FreeTakeInStudio), в
-- опубликованной игре — нельзя.
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

type Slot = { boss: number, slot: number, point: CFrame, drop: number, uid: string?, reservedBy: any? }

local loot = GameConfig.Progression.BossLoot
local slots: { [number]: { [number]: Slot } } = {}
local pools: { [number]: { [string]: { string } } } = {} -- [босс][редкость] = id предметов
local looseTimers: { [string]: number } = {} -- uid → номер таймера D10
local timerCounter = 0
local itemsFolder: Folder
local random = Random.new()

local BossLootService = {}

-- Бой за предмет: задаёт BattleService. Возвращает true, если просьбу «Забрать» взял на себя бой этого босса.
BossLootService.OnTakeRequest = nil :: ((player: Player, boss: number, slot: number) -> boolean)?
local closed: { [number]: boolean } = {} -- босс занят боем или возвращается: подсказки выключены

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
	prompt.Enabled = not closed[entry.boss]
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
	entry.reservedBy = nil
	local rarity = BossLootService.RollRarity(entry.boss)
	local itemId = BossLootService.ChooseItem(entry.boss, rarity)
	-- Черновые коллекции боссов 3–10 неполные: нет нужной редкости — ближайшая ниже.
	local rank = Rarities.Rank(rarity)
	while not itemId and rank > 1 do
		rank -= 1
		itemId = BossLootService.ChooseItem(entry.boss, Rarities.Order[rank])
	end
	if not itemId then
		Log.Warn("BossLootService", ("Босс %d: нет предмета нужной редкости"):format(entry.boss))
		return
	end
	local part = ItemFactory.Create(itemId)
	part.Anchored = true
	part.CFrame = entry.point * CFrame.new(0, part.Size.Y / 2, 0)
	part:SetAttribute("Boss", entry.boss)
	part:SetAttribute("BossSlot", entry.slot)
	-- D55: живое существо — клиенты двигают его вокруг места Home (низ, CFrame) общей функцией Shared/CreatureMotion;
	-- Drop — высота места над полом зоны (убегая, существо спрыгивает с постамента)
	part:SetAttribute("Home", entry.point)
	part:SetAttribute("Drop", entry.drop)
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

-- Отдать предмет слота игроку в руки (после победы или в тестовом режиме). false — не получилось (руки заняты,
-- предмета уже нет); предмет тогда остаётся у босса.
local function give(player: Player, entry: Slot): boolean
	local uid = entry.uid
	local item = uid and ItemRegistry.Get(uid)
	if not uid or not item or item.state ~= "AtBoss" or not item.part then
		return false
	end
	if not ItemRegistry.Transition(uid, "Carried", { carrier = player }) then
		return false
	end
	entry.uid = nil -- слот пуст до рассвета
	entry.reservedBy = nil
	-- D55: больше не живёт у босса — клиенты перестают двигать корень (дальше его ведёт перенос)
	for _, name in { "Home", "Drop", "CatchMode", "CatchSince", "CatchFace", "CatchAnchor" } do
		item.part:SetAttribute(name, nil)
	end
	local prompt = item.part:FindFirstChild("TakePrompt")
	if prompt then
		prompt:Destroy()
	end
	CarryService.RegisterMapItem(uid, item.part)
	CarryService.AttachCarried(player, uid)
	return true
end

tryTake = function(player: Player, entry: Slot)
	local uid = entry.uid
	local item = uid and ItemRegistry.Get(uid)
	if not uid or not item or item.state ~= "AtBoss" or not item.part then
		return
	end
	if closed[entry.boss] then
		Notify.Send(player, "Босс занят: дождитесь конца боя", "Stop")
		return
	end
	local hook = BossLootService.OnTakeRequest
	if hook and hook(player, entry.boss, entry.slot) then
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
	give(player, entry)
end

-- Предмет в слоте: uid и его Part (nil — слот пуст).
function BossLootService.SlotItem(boss: number, slot: number): (string?, BasePart?)
	local entry = slots[boss] and slots[boss][slot]
	local uid = entry and entry.uid
	local item = uid and ItemRegistry.Get(uid)
	if not uid or not item or item.state ~= "AtBoss" then
		return nil, nil
	end
	return uid, item.part
end

-- Подсказки «Забрать» у всех предметов босса: выключены, пока босс занят боем или возвращается.
function BossLootService.SetOpen(boss: number, open: boolean)
	closed[boss] = if open then nil else true
	for _, entry in slots[boss] or {} do
		local item = entry.uid and ItemRegistry.Get(entry.uid)
		local prompt = item and item.part and item.part:FindFirstChild("TakePrompt")
		if prompt then
			(prompt :: ProximityPrompt).Enabled = open
		end
	end
end

function BossLootService.IsOpen(boss: number): boolean
	return not closed[boss]
end

-- Закрепить предмет слота за бойцом на время боя (другие его не заберут).
function BossLootService.Reserve(boss: number, slot: number, player: any): boolean
	local entry = slots[boss] and slots[boss][slot]
	if not entry or not entry.uid or entry.reservedBy then
		return false
	end
	entry.reservedBy = player
	return true
end

-- Бой закончился без победы: предмет снова свободен (он не покидал своё место).
function BossLootService.Release(boss: number, slot: number)
	local entry = slots[boss] and slots[boss][slot]
	if entry then
		entry.reservedBy = nil
	end
end

-- Победа: предмет слота — в руки победителю. false — не получилось, предмет остаётся у босса.
function BossLootService.Award(boss: number, slot: number, player: Player): boolean
	local entry = slots[boss] and slots[boss][slot]
	if not entry or entry.reservedBy ~= player then
		return false
	end
	if not give(player, entry) then
		entry.reservedBy = nil
		return false
	end
	return true
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
		if def.legacy then
			continue -- прежние предметы — только для старых сохранений
		end
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
		local arena = MapLayout.Arenas[spec.zone]
		slots[spec.zone][spec.slot] = {
			boss = spec.zone,
			slot = spec.slot,
			point = spec.cframe,
			drop = if arena then arena.top else MapLayout.PedestalHeight,
			uid = nil,
		}
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

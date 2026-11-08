-- Обязательное обучение новичка (D55): при первом входе, пропустить нельзя, ≈ 2–3 мин. Шаги (Shared/TutorialRules):
-- Intro — идти на уровень 1 к учебному существу; Catch — учебная поимка (CatchService.BeginTutorial: бесплатные броски,
-- первое попадание — захват); Battle — учебный бой с личным псом (всегда победа: короткий бой по сценарию, урона
-- игроку нет); Carry — существо в руках: донести до музея и поставить на постамент (бросить, убрать в сундук нельзя;
-- ночь не отнимает); Income — ждём первое начисление дохода; Done — пройдено. Учебные существо и пёс — личные: стоят на
-- месте обучения в зоне 1 (MapLayout.Tutorial), их видит только ученик (атрибут TutorialOwner — остальные клиенты
-- прячут), другие игроки не могут с ними ничего сделать (сервер проверяет владельца). Существо выбирается один раз
-- (случайное Common босса 1) вместе с uid — запись обучения в профиле; повторный вход его не меняет: вышел с ним в
-- руках — при входе снова в руках (тот же uid). Выставление записывает предмет и «поставлено» в одной записи профиля
-- (MuseumService.OnDisplayed, без yield). Стартовое существо навсегда защищено от кражи (TheftService,
-- TutorialRules.IsProtected). Пока идёт обучение: атрибут игрока Tutorial (ShopService.Sync) — «Магазин» и «Защита»
-- закрыты, ночь, барьер, PvP и кражи на ученика не действуют (NightService, PvpService, TheftService, группа Student).
-- Зависит от BossService, CarryService, CatchService, DataService, IncomeService, InventoryService, ItemRegistry,
-- MuseumService, NightService, ShopService, Shared/TutorialRules, Shared/CreatureMotion, Remotes, Config,
-- Util/ItemFactory, Util/CharacterGroups, Util/Notify, Util/Log, World/MapLayout.

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local CreatureMotion = require(ReplicatedStorage.Shared.CreatureMotion)
local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local TutorialRules = require(ReplicatedStorage.Shared.TutorialRules)
local Server = ServerScriptService.Server
local BossService = require(Server.Services.BossService)
local CarryService = require(Server.Services.CarryService)
local CatchService = require(Server.Services.CatchService)
local DataService = require(Server.Services.DataService)
local IncomeService = require(Server.Services.IncomeService)
local InventoryService = require(Server.Services.InventoryService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local MuseumService = require(Server.Services.MuseumService)
local NightService = require(Server.Services.NightService)
local PlotService = require(Server.Services.PlotService)
local ShopService = require(Server.Services.ShopService)
local CharacterGroups = require(Server.Util.CharacterGroups)
local ItemFactory = require(Server.Util.ItemFactory)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local MapLayout = require(Server.World.MapLayout)

local Tutorial = GameConfig.Catch.Tutorial
local NEAR = 22 -- Intro → Catch: ученик подошёл к существу ближе
local FIGHT_HITS = 5 -- ударов ученика до победы над учебным псом
local FIGHT_STEP = 0.9 -- секунд между ударами

type Personal = {
	creature: BasePart?,
	dog: BossService.Boss?,
	fighting: boolean,
}

local personal: { [any]: Personal } = {}
local folder: Folder

local TutorialService = {}

local function stateOf(player: any): Personal
	local p = personal[player]
	if not p then
		p = { creature = nil, dog = nil, fighting = false }
		personal[player] = p
	end
	return p
end

-- Активна ли запись обучения игрока (профиль загружен и не Done).
local function active(player: any): boolean
	local data = DataService.GetData(player)
	return data ~= nil and TutorialRules.IsActive(data)
end

local function targetPosition(player: any, step: string): any
	local p = personal[player]
	if (step == "Intro" or step == "Catch") and p and p.creature then
		return p.creature
	elseif step == "Battle" and p and p.dog then
		return p.dog.root
	elseif step == "Carry" then
		local plot = PlotService.GetPlotOf(player)
		if plot then
			for slot, showcase in plot.showcases do
				if showcase.Parent and DataService.IsSlotFree(player, slot) then
					return showcase
				end
			end
		end
	end
	return nil
end

-- Шаг ученику (панель задачи и стрелка — TutorialController) и атрибут Tutorial (ShopService.Sync).
local function push(player: any)
	local t = DataService.Tutorial(player)
	if not t then
		return
	end
	ShopService.Sync(player)
	CharacterGroups.Apply(player) -- ученик проходит ночной барьер (группа Student)
	Remotes.FireClient(Remotes.Names.TutorialChanged, player, {
		step = t.step,
		target = targetPosition(player, t.step),
		itemId = t.itemId,
	})
end

local function advance(player: any, step: string): boolean
	local ok = DataService.SetTutorial(player, { step = step })
	if ok then
		DataService.RequestSave(player)
		Log.Debug("TutorialService", ("%s: обучение → %s"):format(player.Name, step))
		push(player)
	end
	return ok
end

local function points(): (CFrame, CFrame)
	return MapLayout.TutorialPoints()
end

local function removeCreature(p: Personal)
	if p.creature then
		p.creature:Destroy()
		p.creature = nil
	end
end

local function removeDog(p: Personal)
	if p.dog then
		p.dog.model:Destroy()
		p.dog = nil
	end
end

local startCatch: (any) -> ()

-- Личное учебное существо на месте обучения (видит только ученик).
local function spawnCreature(player: any)
	local p = stateOf(player)
	local t = DataService.Tutorial(player)
	if p.creature or not t or not t.itemId or not t.uid then
		return
	end
	local home = points()
	local part = ItemFactory.Create(t.itemId)
	part.Anchored = true
	part.CFrame = home * CFrame.new(0, part.Size.Y / 2, 0)
	part:SetAttribute("ItemUid", t.uid) -- зерно движения (в реестре его нет до выдачи)
	part:SetAttribute("Home", home)
	part:SetAttribute("Drop", 0)
	part:SetAttribute("TutorialOwner", player.UserId)
	part.Parent = folder
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "TutorialPrompt"
	prompt.ActionText = "Поймать"
	prompt.ObjectText = Items[t.itemId].displayName
	prompt.HoldDuration = GameConfig.Catch.Game.PromptHold
	prompt.MaxActivationDistance = GameConfig.Catch.Game.PromptDistance
	prompt.RequiresLineOfSight = false
	prompt.Parent = part
	prompt.Triggered:Connect(function(who)
		if who == player then
			startCatch(player)
		end
	end)
	p.creature = part
end

-- Учебный бой: личный пёс просыпается, обмен ударами по сценарию, пёс повален — существо в руки.
local giveCreature: (any) -> boolean

local function startBattle(player: any)
	local p = stateOf(player)
	if p.fighting then
		return
	end
	if not advance(player, "Battle") then
		return
	end
	p.fighting = true
	local _, dogHome = points()
	if not p.dog then
		local dog = BossService.BuildPersonal(1, dogHome, folder)
		dog.model:SetAttribute("TutorialOwner", player.UserId)
		p.dog = dog
	end
	push(player)
	local dog = p.dog :: BossService.Boss
	task.spawn(function()
		local tl = require(ReplicatedStorage.Shared.Config.Battle).Timeline
		for _, entry in { { "Wake", tl.Wake }, { "StandUp", tl.StandUp }, { "ToCombat", tl.ToCombat } } do
			BossService.SetState(dog, entry[1])
			task.wait(entry[2])
		end
		BossService.SetState(dog, "Combat")
		Notify.Send(player, "Учебный бой: стойте рядом — удары идут сами", "Go")
		for i = 1, FIGHT_HITS do
			if player.Parent == nil and typeof(player) == "Instance" then
				p.fighting = false
				return
			end
			task.wait(FIGHT_STEP)
			BossService.Hit(dog)
			if i % 2 == 0 then
				BossService.Attack(dog, "bite") -- пёс замахивается, но учебный бой урона не наносит
			end
		end
		BossService.SetState(dog, "Defeat")
		task.wait(tl.Defeat)
		p.fighting = false
		if giveCreature(player) then
			advance(player, "Carry")
			Notify.Send(
				player,
				"Победа! Несите существо в свой музей и поставьте на постамент",
				"Go"
			)
		end
		BossService.SetState(dog, "FallAsleep")
		task.wait(tl.FallAsleep)
		removeDog(p)
	end)
end

-- Учебное существо — в руки ученику (тот же uid; в реестре — один раз). true — в руках.
giveCreature = function(player: any): boolean
	local t = DataService.Tutorial(player)
	if not t or not t.uid or not t.itemId then
		return false
	end
	if ItemRegistry.GetCarriedBy(player) == t.uid then
		return true
	end
	if ItemRegistry.GetCarriedBy(player) then
		CarryService.LoseCarried(player, "обучение: в руки — учебное существо")
	end
	local p = stateOf(player)
	removeCreature(p)
	local existing = ItemRegistry.Get(t.uid)
	if existing then
		return false -- предмет уже где-то (выставлен) — не дублировать
	end
	local part = ItemFactory.Create(t.itemId)
	part.Anchored = true
	part.CFrame = (points()) * CFrame.new(0, part.Size.Y / 2, 0)
	part.Parent = folder
	if not ItemRegistry.CreateTutorial(t.uid, t.itemId, part) then
		part:Destroy()
		return false
	end
	if not ItemRegistry.Transition(t.uid, "Carried", { carrier = player }) then
		ItemRegistry.Discard(t.uid, "обучение: не вышло дать в руки")
		part:Destroy()
		return false
	end
	CarryService.RegisterMapItem(t.uid, part)
	CarryService.AttachCarried(player, t.uid)
	return true
end

startCatch = function(player: any)
	local t = DataService.Tutorial(player)
	local p = stateOf(player)
	if not t or not p.creature or CatchService.IsCatching(player) then
		return
	end
	if t.step == "Intro" then
		advance(player, "Catch")
		t = DataService.Tutorial(player) :: any
	end
	if t.step ~= "Catch" then
		return
	end
	local part = p.creature :: BasePart
	local def = Items[t.itemId :: string]
	local home = part:GetAttribute("Home") :: CFrame
	CatchService.BeginTutorial(player, {
		boss = Tutorial.ItemBoss,
		slot = 0,
		uid = t.uid :: string,
		itemId = t.itemId :: string,
		rarity = def.rarity,
		part = part,
		home = home,
		height = def.size.Y,
		params = {
			seed = CreatureMotion.SeedOf(t.uid :: string),
			radius = 1.6,
			scale = CreatureMotion.ScaleOf(def.size),
			mode = "Wander",
			drop = 0,
		},
		tutorial = true,
		onCaught = function(who)
			if part.Parent then
				part:SetAttribute("CatchMode", "Hidden")
			end
			startBattle(who)
		end,
		onEnd = function() end,
	})
end

-- Шаг обучения по профилю: учебные объекты и выдача существа (вход, возрождение).
local function setup(player: any)
	local t = DataService.Tutorial(player)
	if not t or t.step == "Done" then
		return
	end
	-- существо выбирается один раз (вместе с uid — к нему привязана защита)
	if not t.itemId or not t.uid then
		local pool = {}
		for id, def in Items do
			if def.boss == Tutorial.ItemBoss and def.rarity == Tutorial.ItemRarity and not def.legacy then
				table.insert(pool, id)
			end
		end
		table.sort(pool)
		local pick = pool[Random.new():NextInteger(1, #pool)]
		DataService.SetTutorial(player, { itemId = pick, uid = HttpService:GenerateGUID(false) })
		DataService.RequestSave(player)
	end
	local resume = TutorialRules.ResumeStep(t.step)
	if resume ~= t.step then
		t.step = resume -- бой прерван выходом: ничего не выдано — снова поимка
	end
	local p = stateOf(player)
	if t.step == "Intro" or t.step == "Catch" then
		spawnCreature(player)
	elseif t.step == "Carry" then
		removeCreature(p)
		if player.Character then
			giveCreature(player)
		end
	end
	push(player)
end

-- Игрок вошёл (PlayerSession.Join, после загрузки профиля).
function TutorialService.OnPlayerLoaded(player: any)
	if not active(player) then
		return
	end
	setup(player)
end

-- Нельзя бросить, отдать или убрать в сундук учебное существо до постамента.
local function locked(player: any, uid: string): string?
	local t = active(player) and DataService.Tutorial(player)
	if t and t.uid == uid and t.step == "Carry" then
		return "Учебное существо нужно поставить на постамент в музее"
	end
	return nil
end

function TutorialService.Init(world: Instance)
	folder = Instance.new("Folder")
	folder.Name = "Tutorial"
	folder.Parent = world
	CarryService.CanDrop = locked
	InventoryService.CanStore = locked
	MuseumService.CanBypassLock = function(player: any, uid: string): boolean
		local t = active(player) and DataService.Tutorial(player)
		return t ~= nil and t ~= false and t.uid == uid
	end
	-- выставили учебное существо: «поставлено» и шаг Income — в той же записи профиля, что и предмет (без yield)
	MuseumService.OnDisplayed = function(player: any, uid: string)
		local t = active(player) and DataService.Tutorial(player)
		if t and t.uid == uid and t.step == "Carry" then
			DataService.SetTutorial(player, { step = "Income", placed = true })
			push(player)
			Notify.Send(player, "Экспонат на месте! Ждём первый доход", "Go")
		end
	end
	-- первое начисление дохода за стартовое существо — обучение пройдено
	IncomeService.OnPaid = function(player: any, amount: number)
		if amount <= 0 or not active(player) then
			return
		end
		local t = DataService.Tutorial(player)
		local entry = t and t.uid and ItemRegistry.Get(t.uid)
		if t and t.step == "Income" and entry and entry.state == "Displayed" then
			if advance(player, "Done") then
				personal[player] = nil
				Notify.Send(
					player,
					"Обучение пройдено! Открыт «Магазин» Ловибумов",
					"Go"
				)
			end
		end
	end
	NightService.IsExempt = function(player: any): boolean
		return player:GetAttribute("Tutorial") ~= nil
	end
	Players.PlayerRemoving:Connect(function(player)
		local p = personal[player]
		if p then
			removeCreature(p)
			removeDog(p)
			personal[player] = nil
		end
	end)
	-- Intro → Catch, когда ученик подошёл; возрождение с существом в руках
	task.spawn(function()
		while true do
			task.wait(0.5)
			for player, p in personal do
				local t = DataService.Tutorial(player)
				if not t or t.step == "Done" then
					continue
				end
				local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
				if
					t.step == "Intro"
					and p.creature
					and root
					and (root.Position - p.creature.Position).Magnitude < NEAR
				then
					advance(player, "Catch")
				elseif t.step == "Carry" and root and ItemRegistry.GetCarriedBy(player) ~= t.uid then
					local entry = ItemRegistry.Get(t.uid :: string)
					if not entry then
						giveCreature(player) -- погиб с существом в руках: снова в руках (тот же uid)
						push(player)
					end
				end
			end
		end
	end)
end

-- Для серверных тестов.
TutorialService.Handlers = {
	Personal = function(player: any): Personal?
		return personal[player]
	end,
	StartCatch = function(player: any)
		startCatch(player)
	end,
	Setup = setup,
}

return TutorialService

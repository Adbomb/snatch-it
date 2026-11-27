-- Серверные тесты на двух игроков (только Studio, в Play): владение участками, профили, запрет действий с чужими
-- витринами, сундуком, хранилищем, гантелью и полем качалки, один носитель у предмета, повторный вход, перестройка
-- музея; время и ночь (этап 2 D37); предметы у боссов (этап 3); босс 1 (D40): каталог из 20 предметов, модели,
-- автобой (победа, поражение с отбросом, повтор без ожидания, один бой на босса, ночь, побег, сила), доход экспонатов
-- и полный путь «победа → витрина → доход → повторный вход»; музей D48-C (места по уровням, хранилище только
-- владельцу, лестница и оболочка в режимах Parts и Mesh, Terrain под хранилищем). Игроки — Tests/TestPlayer с профилями в памяти
-- (ProfileStore.Mock): в DataStore ничего не пишется, участки берутся свободные (настоящий игрок не трогается).
-- Вход и выход — тем же Services/PlayerSession, действия — теми же обработчиками, что вызывают подсказки
-- (Handlers). Это серверная симуляция: подсказки на клиенте, интерфейс, сеть и физику персонажа она не
-- проверяет — для этого нужен тест с настоящими клиентами.
-- Запуск через MCP в Play: game.ServerStorage.DevTools.RunServerTests:Invoke() → отчёт строкой.
-- Зависит от Services/*, Util/ItemFactory, Tests/TestPlayer, GameConfig.

local PhysicsService = game:GetService("PhysicsService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Battle = require(ReplicatedStorage.Shared.Config.Battle)
local BossModels = require(ReplicatedStorage.Shared.Config.BossModels)
local Boss1DogRig = require(ReplicatedStorage.Shared.Config.Boss1DogRig)
local Boss2TraderRig = require(ReplicatedStorage.Shared.Config.Boss2TraderRig)
local ItemModels = require(ReplicatedStorage.Shared.Config.ItemModels)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local Rarities = require(ReplicatedStorage.Shared.Config.Rarities)
local Server = ServerScriptService.Server
local BattleService = require(Server.Services.BattleService)
local BossLootService = require(Server.Services.BossLootService)
local BossService = require(Server.Services.BossService)
local CarryService = require(Server.Services.CarryService)
local DataService = require(Server.Services.DataService)
local DevourService = require(Server.Services.DevourService)
local FloorRules = require(ReplicatedStorage.Shared.FloorRules)
local GymService = require(Server.Services.GymService)
local HandDumbbell = require(Server.World.HandDumbbell)
local IncomeService = require(Server.Services.IncomeService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local MuseumService = require(Server.Services.MuseumService)
local PlayerSession = require(Server.Services.PlayerSession)
local PlotService = require(Server.Services.PlotService)
local ProfileStore = require(Server.Vendor.ProfileStore)
local ProfileTemplate = require(ReplicatedStorage.Shared.Config.ProfileTemplate)
local NightService = require(Server.Services.NightService)
local InventoryService = require(Server.Services.InventoryService)
local TimeService = require(Server.Services.TimeService)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local MapLayout = require(Server.World.MapLayout)
local ItemFactory = require(Server.Util.ItemFactory)
local Prompts = require(Server.Util.Prompts)
local TestPlayer = require(Server.Tests.TestPlayer)
local TheftService = require(Server.Services.TheftService)
local PvpService = require(Server.Services.PvpService)
local MoveGuard = require(Server.Services.MoveGuard)
local DefenseService = require(Server.Services.DefenseService)
local VaultService = require(Server.Services.VaultService)
local CharacterGroups = require(Server.Util.CharacterGroups)
local MuseumLayout = require(ReplicatedStorage.Shared.Config.MuseumLayout)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local CatchRules = require(ReplicatedStorage.Shared.CatchRules)
local DefenseRules = require(ReplicatedStorage.Shared.DefenseRules)
local CatchThrow = require(ReplicatedStorage.Shared.CatchThrow)
local CreatureMotion = require(ReplicatedStorage.Shared.CreatureMotion)
local CreatureRigs = require(ReplicatedStorage.Shared.Config.CreatureRigs)
local TutorialRules = require(ReplicatedStorage.Shared.TutorialRules)
local CatchService = require(Server.Services.CatchService)
local ShopService = require(Server.Services.ShopService)
local TutorialService = require(Server.Services.TutorialService)

local TEST_ITEM = "Moai" -- Common из коллекции босса 1 (D40)
local ITEMS_FOLDER = "__TestItems"

-- note — строка с конкретным результатом теста: печатается в отчёте под строкой теста (D56)
type Context = { track: (any) -> (), items: { string }, note: (string) -> () }

local tests: { { name: string, fn: (any, any, Context) -> () } } = {}

local function test(name: string, fn: (any, any, Context) -> ())
	table.insert(tests, { name = name, fn = fn })
end

local function check(condition: any, message: string)
	if not condition then
		error(message, 0)
	end
end

local function join(player: any): boolean
	return PlayerSession.Join(player, { mock = true, veteran = true }) -- D55: обучение пройдено (тесты обучения — свои)
end

local function leave(player: any)
	player.Parent = nil
	PlayerSession.Leave(player)
	player.Character:Destroy()
end

local function plotOf(player: any): PlotService.Plot
	local plot = PlotService.GetPlotOf(player)
	check(plot, player.Name .. " без участка")
	return plot :: PlotService.Plot
end

-- Встать рядом с деталью (витрина, сундук, табличка): на 4 стада перед ней.
local function near(player: any, part: BasePart)
	player:MoveTo(part.Position + Vector3.new(0, 0, -4))
end

-- Сколько деталей в мире помечено этим uid (больше одной — дубль).
local function countUid(uid: string): number
	local count = 0
	for _, d in workspace:GetDescendants() do
		if d:GetAttribute("ItemUid") == uid then
			count += 1
		end
	end
	return count
end

-- Музей-небоскрёб (этап B, режим башни DEV): свои сценарии — Tests/TowerTests, те же test/check/вход/выход.
require(Server.Tests.TowerTests).Register(test, { check = check, join = join, leave = leave, countUid = countUid })

-- Предмет на карте в точке position (брошенный: Part, uid в реестре, подсказка «Поднять»).
local function mapItem(ctx: Context, position: Vector3, itemId: string?): (string, BasePart)
	local folder = workspace:FindFirstChild(ITEMS_FOLDER)
	if not folder then
		folder = Instance.new("Folder")
		folder.Name = ITEMS_FOLDER
		folder.Archivable = false
		folder.Parent = workspace
	end
	local part = ItemFactory.Create(itemId or TEST_ITEM)
	part.Anchored = true
	part.CFrame = CFrame.new(position)
	part.Parent = folder
	local uid = ItemRegistry.CreateOnMap(itemId or TEST_ITEM, part)
	CarryService.RegisterMapItem(uid, part)
	table.insert(ctx.items, uid)
	return uid, part
end

-- Игрок поднимает новый предмет с карты (через обработчик подсказки «Поднять»).
local function carry(ctx: Context, player: any, itemId: string?): string
	local position = player.Character.PrimaryPart.Position + Vector3.new(0, 0, 3)
	local uid = mapItem(ctx, position, itemId)
	CarryService.Handlers.Pickup(player, uid)
	check(ItemRegistry.GetCarriedBy(player) == uid, player.Name .. " не поднял предмет")
	return uid
end

-- Игрок приносит предмет и выставляет его на свою витрину slot.
local function displayOwn(ctx: Context, player: any, slot: number, itemId: string?): string
	local plot = plotOf(player)
	near(player, plot.showcases[slot])
	local uid = carry(ctx, player, itemId)
	MuseumService.Handlers.Display(player, plot, slot)
	local entry = ItemRegistry.Get(uid)
	local shown = entry and entry.state == "Displayed" and entry.slot == slot
	check(shown, player.Name .. " не выставил на витрину " .. slot)
	return uid
end

test(
	"Двум игрокам — разные участки и профили; участок освобождается при выходе",
	function(A, B)
		local plotA, plotB = plotOf(A), plotOf(B)
		check(plotA ~= plotB, "участки совпали")
		check(plotA.owner == A and plotB.owner == B, "владельцы участков перепутаны")
		check(plotA.model:GetAttribute("OwnerUserId") == A.UserId, "атрибут OwnerUserId участка A")
		check(DataService.GetData(A) ~= DataService.GetData(B), "у игроков один профиль")
		DataService.AddCoins(A, 500)
		check(DataService.GetData(B).coins == 0, "монеты A попали B")
		local index = plotA.index
		leave(A)
		check(PlotService.GetPlots()[index].owner == nil, "участок A не освободился")
		check(plotB.owner == B, "участок B освободился вместе с A")
	end
)

test("Своё выставление пишется только в свой профиль", function(A, B, ctx)
	local uid = displayOwn(ctx, A, 1)
	local record = DataService.GetData(A).items[uid]
	check(record and record.place == "slot" and record.slot == 1, "нет записи в профиле A")
	check(ItemRegistry.Get(uid).owner == A.UserId, "владелец в реестре не A")
	check(plotOf(A).showcases[1]:GetAttribute("Occupied") == true, "витрина A не занята")
	check(next(DataService.GetData(B).items) == nil, "у B появились экспонаты")
end)

test("Нельзя выставить в чужой музей", function(A, B, ctx)
	local plotA = plotOf(A)
	near(B, plotA.showcases[2])
	local uid = carry(ctx, B)
	MuseumService.Handlers.Display(B, plotA, 2)
	check(ItemRegistry.GetCarriedBy(B) == uid, "предмет ушёл из рук B")
	check(not plotA.showcases[2]:GetAttribute("Occupied"), "витрина A занята")
	local anySlot = ItemRegistry.GetSlotItem(A.UserId, 2) or ItemRegistry.GetSlotItem(B.UserId, 2)
	check(anySlot == nil, "реестр витрин")
	check(
		next(DataService.GetData(A).items) == nil and next(DataService.GetData(B).items) == nil,
		"профили изменились"
	)
	check(B:WasNotified("Это чужой музей"), "нет сообщения «Это чужой музей»")
end)

test(
	"Нельзя переставить, повернуть, убрать или подменить чужой экспонат",
	function(A, B, ctx)
		local uid = displayOwn(ctx, A, 1)
		local plotA, plotB = plotOf(A), plotOf(B)
		near(B, plotA.showcases[1])
		MuseumService.Handlers.Move(B, plotA, 1)
		check(B:GetAttribute("MoveSlot") == nil, "B выбрал чужой экспонат")
		MuseumService.Handlers.Rotate(B, plotA, 1)
		InventoryService.Handlers.StoreDisplayed(B, plotA, 1)
		local record = DataService.GetData(A).items[uid]
		check(
			record.place == "slot" and record.slot == 1 and record.rot == 0,
			"запись экспоната A изменилась"
		)
		check(
			ItemRegistry.Get(uid).state == "Displayed" and ItemRegistry.CountStored(B.UserId) == 0,
			"реестр изменился"
		)
		-- «Сюда» в чужой музей: B выбирает свой экспонат и пытается поставить его на витрину A.
		local own = displayOwn(ctx, B, 1)
		near(B, plotB.showcases[1])
		MuseumService.Handlers.Move(B, plotB, 1)
		check(B:GetAttribute("MoveSlot") == 1, "B не выбрал свой экспонат")
		near(B, plotA.showcases[2])
		MuseumService.Handlers.Here(B, plotA, 2)
		check(ItemRegistry.GetSlotItem(B.UserId, 1) == own, "экспонат B ушёл с витрины 1")
		check(DataService.GetData(B).items[own].slot == 1, "запись экспоната B изменилась")
		check(not plotA.showcases[2]:GetAttribute("Occupied"), "витрина A занята экспонатом B")
		MuseumService.CancelMove(B)
	end
)

test("Нельзя убрать предмет в чужой сундук", function(A, B, ctx)
	local plotA = plotOf(A)
	near(B, plotA.chest)
	local uid = carry(ctx, B)
	InventoryService.Handlers.StoreCarried(B, plotA)
	check(ItemRegistry.GetCarriedBy(B) == uid, "предмет ушёл из рук B")
	check(
		ItemRegistry.CountStored(A.UserId) == 0 and ItemRegistry.CountStored(B.UserId) == 0,
		"предмет в хранилище"
	)
	check(B:WasNotified("Это чужой музей"), "нет сообщения «Это чужой музей»")
end)

test(
	"Нельзя выставить предмет из чужого хранилища или по поддельному uid",
	function(A, B, ctx)
		local uid = displayOwn(ctx, A, 1)
		local plotA, plotB = plotOf(A), plotOf(B)
		near(A, plotA.showcases[1])
		InventoryService.Handlers.StoreDisplayed(A, plotA, 1)
		check(ItemRegistry.Get(uid).state == "Stored", "A не убрал экспонат в хранилище")
		near(B, plotB.showcases[1])
		for _, forged in { uid, "не-uid", 42 :: any, string.rep("x", 100) } do
			InventoryService.Handlers.DisplayFromStorage(B, forged, 1)
		end
		local entry = ItemRegistry.Get(uid)
		check(entry.state == "Stored" and entry.owner == A.UserId, "предмет A сдвинулся")
		check(
			ItemRegistry.GetSlotItem(B.UserId, 1) == nil and next(DataService.GetData(B).items) == nil,
			"у B экспонат"
		)
		check(DataService.GetData(A).items[uid].place == "storage", "запись A изменилась")
	end
)

-- Единый инвентарь (D46) ───────────────────────────────────────────────────────────────────────────────────

-- Пауза между вызовами одного входа: ограничитель частоты (GameConfig.RateLimits) режет лишние.
local function settle()
	task.wait(0.3)
end

-- Сколько устройств kind в запасе игрока для музея его нынешнего уровня (D56: запас — по уровням покупки).
local function defenseStock(player: any, kind: string): number
	return DefenseRules.Stock(DataService.Defense(player).owned, kind, DataService.GetData(player).museumLevel)
end

-- Несёт новый предмет и сдаёт его в сундук своего музея (Carried → Stored).
local function toInventory(ctx: Context, player: any, itemId: string?): string
	local plot = plotOf(player)
	near(player, plot.chest)
	local uid = carry(ctx, player, itemId)
	InventoryService.Handlers.StoreCarried(player, plot)
	local entry = ItemRegistry.Get(uid)
	check(
		entry and entry.state == "Stored" and entry.owner == player.UserId,
		player.Name .. ": предмет не в инвентаре"
	)
	settle()
	return uid
end

local function farAway(player: any)
	player:MoveTo(Vector3.new(0, 5, 60)) -- место появления: далеко от музеев
end

test(
	"Инвентарь: выставить, снять и заменить из окна откуда угодно, доход пересчитывается",
	function(A, _B, ctx)
		local first = toInventory(ctx, A, "Moai")
		local second = toInventory(ctx, A, "Sunflowers")
		farAway(A)
		InventoryService.Handlers.Action(A, "Display", first, 2)
		local e1 = ItemRegistry.Get(first)
		check(
			e1.state == "Displayed" and e1.slot == 2,
			"предмет не выставлен из окна издалека"
		)
		check(DataService.GetData(A).items[first].place == "slot", "профиль: не на постаменте")
		IncomeService.Handlers.Refresh(A)
		check(
			A:GetAttribute("Income") == IncomeService.Of("Moai"),
			"доход не равен доходу выставленного"
		)
		settle()
		InventoryService.Handlers.Action(A, "Replace", second, 2)
		local old, new = ItemRegistry.Get(first), ItemRegistry.Get(second)
		check(old.state == "Stored" and new.state == "Displayed" and new.slot == 2, "замена не прошла")
		local data = DataService.GetData(A)
		check(
			data.items[first].place == "storage" and data.items[second].slot == 2,
			"профиль после замены"
		)
		check(countUid(first) == 0 and countUid(second) == 1, "дубли деталей после замены")
		IncomeService.Handlers.Refresh(A)
		check(A:GetAttribute("Income") == IncomeService.Of("Sunflowers"), "доход после замены")
		settle()
		InventoryService.Handlers.Action(A, "Remove", second)
		check(ItemRegistry.Get(second).state == "Stored", "снять не получилось")
		check(not plotOf(A).showcases[2]:GetAttribute("Occupied"), "постамент остался занят")
		IncomeService.Handlers.Refresh(A)
		check((A:GetAttribute("Income") or 0) == 0, "доход остался после снятия")
		local total, displayed = 0, 0
		for _, record in DataService.GetData(A).items do
			total += 1
			displayed += if record.place == "slot" then 1 else 0
		end
		check(total == 2 and displayed == 0, "в инвентаре не 2 предмета")
	end
)

test(
	"Инвентарь: в подготовку, Судную ночь и 10 с доставки экспонаты не меняются (сервер)",
	function(A, _B, ctx)
		local shown = displayOwn(ctx, A, 1)
		local kept = toInventory(ctx, A)
		local plotA = plotOf(A)
		local function locked(label: string)
			near(A, plotA.showcases[1])
			InventoryService.Handlers.StoreDisplayed(A, plotA, 1)
			settle()
			InventoryService.Handlers.Action(A, "Remove", shown)
			settle()
			InventoryService.Handlers.Action(A, "Display", kept, 3)
			settle()
			InventoryService.Handlers.Action(A, "Replace", kept, 1)
			settle()
			MuseumService.Handlers.Move(A, plotA, 1)
			check(
				ItemRegistry.Get(shown).state == "Displayed" and ItemRegistry.Get(shown).slot == 1,
				label .. ": экспонат снят"
			)
			check(ItemRegistry.Get(kept).state == "Stored", label .. ": предмет выставлен")
			check(A:GetAttribute("MoveSlot") == nil, label .. ": перестановка началась")
			local record = DataService.GetData(A).items[shown]
			check(record.place == "slot" and record.slot == 1, label .. ": профиль изменился")
		end
		TimeService.SkipTo("Preparation", -5)
		check(GameTime.Current().phase == "Preparation", "не подготовка")
		locked("подготовка")
		check(
			A:WasNotified("Подготовка к Судной ночи"),
			"нет причины в сообщении"
		)
		local delivered = toInventory(ctx, A) -- сундук принимает добычу в любую фазу
		check(
			ItemRegistry.Get(delivered).state == "Stored",
			"сундук не принял предмет в подготовку"
		)
		TimeService.SkipTo("DoomNight", -5)
		locked("Судная ночь")
		TimeService.SkipTo("Day", -3)
		check(GameTime.DeliveryWindowEnd(GameTime.Now()) ~= nil, "не окно доставки")
		locked("10 с доставки")
		TimeService.SkipTo("Day", -(GameConfig.Time.DeliveryGrace + 5))
		InventoryService.Handlers.Action(A, "Remove", shown)
		check(ItemRegistry.Get(shown).state == "Stored", "днём снять нельзя")
	end
)

test(
	"Инвентарь: повторные и чужие вызовы InventoryAction не дублируют и не трогают чужое",
	function(A, B, ctx)
		local mine = toInventory(ctx, A)
		local shown = displayOwn(ctx, A, 1)
		-- Одна и та же вещь на два постамента подряд: встаёт один раз.
		InventoryService.Handlers.Action(A, "Display", mine, 2)
		InventoryService.Handlers.Action(A, "Display", mine, 3)
		local entry = ItemRegistry.Get(mine)
		check(
			entry.state == "Displayed" and entry.slot == 2 and countUid(mine) == 1,
			"предмет на двух постаментах"
		)
		check(ItemRegistry.GetSlotItem(A.UserId, 3) == nil, "постамент 3 занят")
		settle()
		-- B: снять, заменить и выставить чужое, неверные аргументы, неизвестное действие.
		for _, args in
			{
				{ "Remove", shown },
				{ "Replace", mine, 1 },
				{ "Display", shown, 1 },
				{ "Display", mine, 99 },
				{ "Steal", shown, 1 },
				{ "Remove", 42 :: any },
				{ "Display", string.rep("y", 200), 1 },
			}
		do
			InventoryService.Handlers.Action(B, table.unpack(args))
			settle()
		end
		check(
			ItemRegistry.Get(shown).state == "Displayed" and ItemRegistry.Get(shown).owner == A.UserId,
			"чужой экспонат сдвинут"
		)
		check(next(DataService.GetData(B).items) == nil, "у B появились предметы")
		-- Лишние вызовы режет ограничитель: 20 подряд — не больше, чем позволяет частота.
		for _ = 1, 20 do
			InventoryService.Handlers.Action(A, "Remove", mine)
			InventoryService.Handlers.Action(A, "Display", mine, 2)
		end
		local after = ItemRegistry.Get(mine)
		check(
			after and (after.state == "Stored" or after.state == "Displayed") and countUid(mine) <= 1,
			"дубль после спама"
		)
		local recordOk = DataService.GetData(A).items[mine]
		check(
			recordOk and ((recordOk.place == "slot") == (after.state == "Displayed")),
			"профиль и реестр разошлись"
		)
	end
)

test(
	"Инвентарь без предела: 12 предметов (больше прежних 10), повторный вход без дублей",
	function(A, _B, ctx)
		local uids = {}
		for i = 1, 12 do
			uids[i] = toInventory(ctx, A, if i % 2 == 0 then "Moai" else "Sunflowers")
		end
		InventoryService.Handlers.Action(A, "Display", uids[1], 1)
		check(A:GetAttribute("StorageCount") == 11, "StorageCount не 11")
		local userId = A.UserId
		leave(A)
		local again = TestPlayer.new("Тест_A_снова")
		again.UserId = userId
		ctx.track(again)
		check(join(again), "A не вошёл повторно")
		local total = 0
		for _ in DataService.GetData(again).items do
			total += 1
		end
		check(total == 12, ("после входа предметов %d, а не 12"):format(total))
		check(
			ItemRegistry.Get(uids[1]).state == "Displayed" and countUid(uids[1]) == 1,
			"экспонат не восстановлен"
		)
		for i = 2, 12 do
			check(
				ItemRegistry.Get(uids[i]).state == "Stored" and countUid(uids[i]) == 0,
				"предмет " .. i .. " не в инвентаре"
			)
		end
	end
)

-- Кража в Судную ночь (D37, D46) ───────────────────────────────────────────────────────────────────────────

local function doomNight()
	TimeService.SkipTo("DoomNight", -5)
	check(GameTime.TheftPhase(GameTime.Now()) == "Open", "не Судная ночь")
end

-- Вор держит «Украсть» у постамента slot музея владельца: начало, ожидание hold, завершение.
local function steal(thief: any, owner: any, slot: number, hold: number?)
	local plot = plotOf(owner)
	near(thief, plot.showcases[slot])
	TheftService.Handlers.Begin(thief, plot, slot)
	task.wait(hold or (GameConfig.Theft.HoldSeconds + 0.1))
	TheftService.Handlers.Complete(thief, plot, slot)
end

-- Снять паузу после сорванной попытки (D52) — в тестах, где вор сразу пробует снова; саму паузу проверяет
-- отдельный тест «D52: после сорванной попытки…».
local function rested(thief: any)
	TheftService.Handlers.Ledger.retryAt[thief.UserId] = nil
end

local function deliverHome(thief: any)
	local plot = plotOf(thief)
	near(thief, plot.chest)
	MoveGuard.Mark(thief) -- тестовый перенос — как перенос сервером; невозможные перемещения — тест D52
	InventoryService.Handlers.StoreCarried(thief, plot)
end

test(
	"Кража: удержание 3 с, доставка в инвентарь вора, у владельца удалено, лимиты D37",
	function(A, B, ctx)
		local uid = displayOwn(ctx, A, 1)
		local other = displayOwn(ctx, A, 2)
		doomNight()
		steal(B, A, 1)
		local entry = ItemRegistry.Get(uid)
		check(
			entry.state == "Stolen" and entry.carrier == B and ItemRegistry.GetCarriedBy(B) == uid,
			"B не унёс экспонат"
		)
		check(not plotOf(A).showcases[1]:GetAttribute("Occupied"), "постамент не опустел")
		check(
			DataService.GetData(A).items[uid] ~= nil,
			"до доставки экспонат уже ушёл из профиля A"
		)
		check(A:WasNotified("Вор унёс"), "владельцу нет уведомления")
		deliverHome(B)
		local after = ItemRegistry.Get(uid)
		check(
			after and after.state == "Stored" and after.owner == B.UserId,
			"после доставки не в инвентаре B"
		)
		check(DataService.GetData(A).items[uid] == nil, "у A осталась запись — дубль")
		local record = DataService.GetData(B).items[uid]
		check(
			record and record.place == "storage" and record.source == "raid" and record.from == A.UserId,
			"запись B"
		)
		check(countUid(uid) == 0, "в мире осталась деталь украденного")
		-- подтверждение журнала (сохранения профилей) снимает pending
		local started = os.clock()
		while
			DataService.GetData(B).items[uid].pending ~= nil
			and os.clock() - started < GameConfig.Theft.SaveTimeout + 2
		do
			task.wait(0.2)
		end
		check(
			DataService.GetData(B).items[uid].pending == nil,
			"передача не подтверждена журналом"
		)
		-- лимиты: второй кражи у B нет, музей A больше не теряет
		steal(B, A, 2, 0.1)
		check(ItemRegistry.Get(other).state == "Displayed", "вторая кража B прошла")
		check(B:WasNotified("уже украли"), "нет причины отказа второй кражи")
		local C = TestPlayer.new("Тест_C")
		ctx.track(C)
		check(join(C), "C не вошёл")
		steal(C, A, 2, 0.1)
		check(ItemRegistry.Get(other).state == "Displayed", "музей A потерял второй предмет")
		check(C:WasNotified("уже потерял"), "нет причины отказа C")
	end
)

test(
	"Кража: провалы возвращают экспонат на постамент, лимиты не тратятся",
	function(A, B, ctx)
		local uid = displayOwn(ctx, A, 1)
		doomNight()
		local plotA = plotOf(A)
		-- отпустил E раньше времени
		near(B, plotA.showcases[1])
		TheftService.Handlers.Begin(B, plotA, 1)
		check(ItemRegistry.Get(uid).state == "Lifting", "удержание не началось")
		TheftService.Handlers.Cancel(B)
		check(
			ItemRegistry.Get(uid).state == "Displayed" and ItemRegistry.Get(uid).slot == 1,
			"после отпускания не на месте"
		)
		-- поддельное завершение через 1 с
		rested(B)
		steal(B, A, 1, 1)
		check(ItemRegistry.Get(uid).state == "Displayed", "кража за 1 с прошла")
		-- Triggered без начала удержания
		TheftService.Handlers.Complete(B, plotA, 1)
		check(ItemRegistry.Get(uid).state == "Displayed", "кража без удержания прошла")
		-- поражение вора с добычей
		task.wait(0.3)
		rested(B)
		steal(B, A, 1)
		check(ItemRegistry.Get(uid).state == "Stolen", "вторая попытка не удалась")
		TheftService.OnDefeated(B)
		local back = ItemRegistry.Get(uid)
		check(
			back.state == "Displayed" and back.slot == 1 and back.owner == A.UserId,
			"после поражения не вернулся"
		)
		check(
			ItemRegistry.GetCarriedBy(B) == nil and countUid(uid) == 1,
			"добыча осталась у B или дубль"
		)
		check(
			plotA.showcases[1]:GetAttribute("Occupied") == true,
			"постамент не занят после возврата"
		)
		-- бросил добычу (G)
		task.wait(0.3)
		rested(B)
		steal(B, A, 1)
		CarryService.Drop(B)
		check(ItemRegistry.Get(uid).state == "Displayed", "брошенная добыча не вернулась")
		-- время доставки вышло
		task.wait(0.3)
		rested(B)
		steal(B, A, 1)
		check(ItemRegistry.Get(uid).state == "Stolen", "третья попытка не удалась")
		TimeService.SkipTo("Day", -(GameConfig.Time.DeliveryGrace + 1))
		TheftService.Handlers.Sweep()
		check(ItemRegistry.Get(uid).state == "Displayed", "после 10 с доставки не вернулся")
		check(
			DataService.GetData(A).items[uid] ~= nil and next(DataService.GetData(B).items) == nil,
			"профили изменились"
		)
		check(
			DataService.GetStat(B, "theftEvent") == nil and DataService.GetStat(A, "lossEvent") == nil,
			"лимиты потрачены"
		)
	end
)

test(
	"Кража: два вора на один экспонат, Stored и свои — нельзя, в 10 с доставки новая не начинается",
	function(A, B, ctx)
		local uid = displayOwn(ctx, A, 1)
		local stored = toInventory(ctx, A)
		local own = displayOwn(ctx, B, 1)
		local C = TestPlayer.new("Тест_C")
		ctx.track(C)
		check(join(C), "C не вошёл")
		doomNight()
		local plotA = plotOf(A)
		near(B, plotA.showcases[1])
		near(C, plotA.showcases[1])
		TheftService.Handlers.Begin(B, plotA, 1)
		TheftService.Handlers.Begin(C, plotA, 1)
		check(ItemRegistry.Get(uid).thief == B, "экспонат снимают двое")
		check(C:WasNotified("уже крадут"), "C не получил причину")
		TheftService.Handlers.Cancel(B)
		-- свой экспонат и предмет из инвентаря
		rested(B)
		steal(B, B, 1, 0.1)
		check(ItemRegistry.Get(own).state == "Displayed", "B украл свой экспонат")
		check(ItemRegistry.Get(stored).state == "Stored", "предмет из инвентаря A сдвинулся")
		-- окно доставки: новая кража не начинается
		TimeService.SkipTo("Day", -3)
		check(GameTime.TheftPhase(GameTime.Now()) == "Delivery", "не окно доставки")
		near(C, plotA.showcases[1])
		TheftService.Handlers.Begin(C, plotA, 1)
		check(ItemRegistry.Get(uid).state == "Displayed", "кража в окне доставки началась")
	end
)

test(
	"D52: красть только изнутри музея и при прямой видимости экспоната",
	function(A, B, ctx)
		local uid = displayOwn(ctx, A, 1)
		doomNight()
		local plotA = plotOf(A)
		local showcase = plotA.showcases[1]
		local at = plotA.floorOrigin:PointToObjectSpace(showcase.Position)
		local side = if at.X >= 0 then 1 else -1
		-- снаружи, за наружной стеной зала: до постамента ближе Distance, но не внутри и стена закрывает
		local outside =
			plotA.floorOrigin:PointToWorldSpace(Vector3.new(side * (MuseumLayout.Hall.HalfWidth + 0.8), 3, at.Z))
		check(
			(outside - showcase.Position).Magnitude < GameConfig.Theft.Distance,
			"точка снаружи не в радиусе подсказки"
		)
		B:MoveTo(outside)
		TheftService.Handlers.Begin(B, plotA, 1)
		check(
			ItemRegistry.Get(uid).state == "Displayed",
			"кража снаружи через стену началась"
		)
		check(B:WasNotified("изнутри музея"), "нет причины «изнутри музея»")
		-- внутри, но между вором и экспонатом стена со столкновениями — не видно
		near(B, showcase)
		local root = B.Character.PrimaryPart :: BasePart
		local wall = Instance.new("Part")
		wall.Name = "__TestWall"
		wall.Anchored = true
		wall.CanCollide = true
		wall.Size = Vector3.new(8, 8, 0.4)
		wall.CFrame = CFrame.lookAt((root.Position + showcase.Position) / 2, showcase.Position)
		wall.Parent = plotA.model:FindFirstChild("Building")
		TheftService.Handlers.Begin(B, plotA, 1)
		local blockedState = ItemRegistry.Get(uid).state
		wall:Destroy()
		check(blockedState == "Displayed", "кража сквозь стену внутри зала началась")
		check(B:WasNotified("не видно"), "нет причины «не видно»")
		-- видно и внутри — начинается; ушёл наружу до конца удержания — сорвалась
		TheftService.Handlers.Begin(B, plotA, 1)
		check(
			ItemRegistry.Get(uid).state == "Lifting",
			"кража изнутри при видимости не началась"
		)
		task.wait(GameConfig.Theft.HoldSeconds + 0.1)
		B:MoveTo(outside)
		TheftService.Handlers.Complete(B, plotA, 1)
		check(ItemRegistry.Get(uid).state == "Displayed", "завершили снаружи")
		check(ItemRegistry.GetCarriedBy(B) == nil, "добыча у вора после провала")
		-- срыв в конце удержания — тоже пауза
		near(B, showcase)
		B:ClearSent()
		TheftService.Handlers.Begin(B, plotA, 1)
		check(
			ItemRegistry.Get(uid).state == "Displayed",
			"после срыва в конце удержания паузы нет"
		)
		check(
			B:WasNotified("новая попытка через"),
			"нет причины паузы после срыва"
		)
		-- внутри и видно, но дальше Distance + ReachSlack (свой допуск, не общий +4) — далеко
		rested(B)
		local far = GameConfig.Theft.Distance + GameConfig.Theft.ReachSlack + 1
		B:MoveTo(showcase.Position + (root.Position - showcase.Position).Unit * far)
		TheftService.Handlers.Begin(B, plotA, 1)
		check(ItemRegistry.Get(uid).state == "Displayed", "кража с " .. far .. " ст. началась")
		check(B:WasNotified("Слишком далеко"), "нет причины «далеко»")
	end
)

test(
	"D52: после сорванной попытки — пауза 5 с; музей не занят повторным удержанием",
	function(A, B, ctx)
		local uid = displayOwn(ctx, A, 1)
		doomNight()
		local plotA = plotOf(A)
		near(B, plotA.showcases[1])
		TheftService.Handlers.Begin(B, plotA, 1)
		check(ItemRegistry.Get(uid).state == "Lifting", "кража не началась")
		TheftService.Handlers.Cancel(B)
		B:ClearSent()
		TheftService.Handlers.Begin(B, plotA, 1)
		check(
			ItemRegistry.Get(uid).state == "Displayed",
			"повтор сразу после отмены начался"
		)
		check(B:WasNotified("новая попытка через"), "нет причины паузы")
		-- музей свободен: другой вор начинает сразу
		local C = TestPlayer.new("Тест_C")
		ctx.track(C)
		check(join(C), "C не вошёл")
		near(C, plotA.showcases[1])
		TheftService.Handlers.Begin(C, plotA, 1)
		check(
			ItemRegistry.Get(uid).state == "Lifting" and ItemRegistry.Get(uid).thief == C,
			"другой вор не смог начать"
		)
		TheftService.Handlers.Cancel(C)
		-- через RetrySeconds вор снова может
		task.wait(GameConfig.Theft.RetrySeconds + 0.1)
		TheftService.Handlers.Begin(B, plotA, 1)
		check(
			ItemRegistry.Get(uid).state == "Lifting" and ItemRegistry.Get(uid).thief == B,
			"после паузы не начать"
		)
		TheftService.Handlers.Cancel(B)
	end
)

-- Проверки MoveGuard в режиме «нарушение срывает кражу, капкан возвращает» (по умолчанию — режим логирования, D52).
local function enforced(fn: () -> ())
	local was = GameConfig.MoveGuard.Enforce
	GameConfig.MoveGuard.Enforce = true
	local ok, err = pcall(fn)
	GameConfig.MoveGuard.Enforce = was
	if not ok then
		error(err, 0)
	end
end

-- Площадка под тестовым игроком (высоко над картой, вдали от всего): ровный пол, над головой пусто. base — где стоит
-- корень на площадке.
local function onPlatform(player: any, fn: (base: Vector3, platform: Part) -> ())
	local root = player.Character.PrimaryPart :: BasePart
	local platform = Instance.new("Part")
	platform.Name = "MoveGuardTestFloor"
	platform.Anchored = true
	platform.Archivable = false
	platform.Size = Vector3.new(60, 1, 60)
	platform.CFrame = CFrame.new(root.Position - Vector3.new(0, 10, 0))
	platform.Parent = workspace
	local base = platform.Position + Vector3.new(0, platform.Size.Y / 2 + root.Size.Y / 2, 0)
	local ok, err = pcall(fn, base, platform)
	platform:Destroy()
	if not ok then
		error(err, 0)
	end
end

test(
	"D52: вор с добычей не телепортируется; рывок после лагов — можно; из капкана не уйти",
	function(A, B, ctx)
		enforced(function()
			local uid = displayOwn(ctx, A, 1)
			doomNight()
			local plotA, plotB = plotOf(A), plotOf(B)
			-- телепорт с добычей к своему сундуку: при переноске (sweep) — провал, экспонат владельцу
			steal(B, A, 1)
			check(ItemRegistry.Get(uid).state == "Stolen", "B не унёс экспонат")
			near(B, plotB.chest)
			TheftService.Handlers.Sweep()
			check(
				ItemRegistry.Get(uid).state == "Displayed",
				"телепорт с добычей не замечен при переноске"
			)
			check(
				B:WasNotified("Слишком быстрое перемещение"),
				"нет причины вору"
			)
			-- телепорт прямо к сундуку и сдача сразу — сдача отклонена
			rested(B)
			steal(B, A, 1)
			near(B, plotB.chest)
			InventoryService.Handlers.StoreCarried(B, plotB)
			check(ItemRegistry.Get(uid).state == "Displayed", "сдача после телепорта прошла")
			check(
				DataService.GetData(A).items[uid] ~= nil and DataService.GetData(B).items[uid] == nil,
				"профили изменились"
			)
			-- честный бег челноком по залу не быстрее скорости (пол под ногами) — добыча остаётся
			rested(B)
			steal(B, A, 1)
			local humanoid = B.Character:FindFirstChildOfClass("Humanoid") :: Humanoid
			local root = B.Character.PrimaryPart :: BasePart
			local origin = plotA.floorOrigin
			local half = humanoid.WalkSpeed * 0.75
			B:MoveTo(origin * Vector3.new(-half, 3, 4))
			MoveGuard.Mark(B) -- тестовый перенос в зал — как перенос сервером
			local step = humanoid.WalkSpeed * 0.25
			for i = 1, 4 do
				task.wait(0.25)
				B:MoveTo(origin * Vector3.new(-half + (i % 2) * step, 3, 4))
				TheftService.Handlers.Sweep()
			end
			check(ItemRegistry.Get(uid).state == "Stolen", "честный бег сочтён телепортом")
			-- сеть молчала 1.5 с, затем рывок на столько, сколько можно пробежать за это время — не нарушение
			task.wait(1.5)
			B:MoveTo(origin * Vector3.new(half, 3, 4))
			TheftService.Handlers.Sweep()
			check(
				ItemRegistry.Get(uid).state == "Stolen",
				"рывок после зависания сети сочтён телепортом"
			)
			-- телепорт, который сервер тут же «перенёс» (выброс из чужого хранилища), не прячет нарушение до переноса
			B:MoveTo(origin * Vector3.new(half, 3, 4) + Vector3.new(0, 0, 120))
			MoveGuard.Teleport(B, CFrame.new(origin * Vector3.new(0, 3, -20)))
			TheftService.Handlers.Sweep()
			check(
				ItemRegistry.Get(uid).state == "Displayed",
				"телепорт перед переносом сервером не замечен"
			)
			-- капкан: ушёл дальше PinRadius — сервер возвращает; перенос сервером точку капкана не меняет; после — свободен
			B:MoveTo(plotA.floorOrigin.Position + Vector3.new(0, 3, 0))
			check(PvpService.Handlers.Snare(B, 1), "капкан не сработал")
			local trapAt = root.Position
			local function away(): number
				return Vector3.new(root.Position.X - trapAt.X, 0, root.Position.Z - trapAt.Z).Magnitude
			end
			B:MoveTo(trapAt + Vector3.new(10, 0, 0))
			MoveGuard.CheckPins()
			check(away() <= GameConfig.MoveGuard.PinRadius, "из капкана ушёл: " .. away())
			MoveGuard.Teleport(B, CFrame.new(trapAt + Vector3.new(0, 0, 30))) -- например, выброс из хранилища
			MoveGuard.CheckPins()
			check(
				away() <= GameConfig.MoveGuard.PinRadius,
				"перенос сервером снял капкан: " .. away()
			)
			check(B:GetAttribute("Snared") == true, "капкан снялся от возврата")
			task.wait(1.2)
			check(
				not MoveGuard.IsPinned(B) and B:GetAttribute("Snared") == nil,
				"после капкана не свободен"
			)
			B:MoveTo(trapAt + Vector3.new(10, 0, 0))
			MoveGuard.CheckPins()
			check(
				(root.Position - (trapAt + Vector3.new(10, 0, 0))).Magnitude < 0.5,
				"после капкана вернули к нему"
			)
		end)
	end
)

test(
	"D52: режим логирования — нарушение записано, кража не срывается, капкан не возвращает",
	function(A, B, ctx)
		check(
			not MoveGuard.Enforced(),
			"по умолчанию должен быть режим логирования"
		)
		local uid = displayOwn(ctx, A, 1)
		doomNight()
		local plotA, plotB = plotOf(A), plotOf(B)
		steal(B, A, 1)
		local before = B:GetAttribute("MoveViolations") or 0
		near(B, plotB.chest)
		TheftService.Handlers.Sweep()
		check(
			ItemRegistry.Get(uid).state == "Stolen",
			"в режиме логирования кража сорвалась"
		)
		check((B:GetAttribute("MoveViolations") or 0) > before, "нарушение не записано")
		check(
			not B:WasNotified("Слишком быстрое перемещение"),
			"вору сообщили о срыве"
		)
		CarryService.Drop(B)
		check(ItemRegistry.Get(uid).state == "Displayed", "брошенная добыча не вернулась")
		B:MoveTo(plotA.floorOrigin.Position + Vector3.new(0, 3, 0))
		check(PvpService.Handlers.Snare(B, 1), "капкан не сработал")
		local root = B.Character.PrimaryPart :: BasePart
		local spot = root.Position + Vector3.new(10, 0, 0)
		local count = B:GetAttribute("MoveViolations") or 0
		B:MoveTo(spot)
		MoveGuard.CheckPins()
		check(
			(root.Position - spot).Magnitude < 0.5,
			"в режиме логирования капкан вернул игрока"
		)
		check((B:GetAttribute("MoveViolations") or 0) == count + 1, "уход из капкана не записан")
		task.wait(1.2)
	end
)

test(
	"D52: проверка перемещений — переносы сервера, запоздавшие пакеты и новый персонаж не нарушение",
	function(A)
		local root = A.Character.PrimaryPart :: BasePart
		MoveGuard.Mark(A)
		-- перенос сервером
		local start = root.Position
		MoveGuard.Teleport(A, CFrame.new(start + Vector3.new(200, 0, 0)))
		check((MoveGuard.Step(A)), "перенос сервером сочтён телепортом")
		check(MoveGuard.TransferredWithin(A, 0.5), "перенос не отмечен для защиты")
		-- запоздавшие пакеты клиента ещё возвращают старую точку, потом — новую: не нарушение
		A:MoveTo(start)
		check(
			(MoveGuard.Step(A)),
			"старая точка сразу после переноса сочтена телепортом"
		)
		A:MoveTo(start + Vector3.new(200, 0, 0))
		check(
			(MoveGuard.Step(A)),
			"новая точка после переноса сочтена телепортом"
		)
		-- третья точка в отсрочке — нарушение: перенос не даёт бесплатного телепорта
		A:MoveTo(start + Vector3.new(200, 0, 100))
		check(
			not (MoveGuard.Step(A)),
			"телепорт в отсрочке после переноса не замечен"
		)
		task.wait(GameConfig.MoveGuard.TransferGrace + 0.1)
		check(not MoveGuard.TransferredWithin(A, 0.5), "перенос «недавний» через секунду")
		-- телепорт клиента без переноса сервером — нарушение
		A:MoveTo(root.Position + Vector3.new(200, 0, 0))
		check(not (MoveGuard.Step(A)), "телепорт на 200 ст. не замечен")
		-- телепорт клиента и сразу перенос сервером: нарушение до переноса вернёт следующая проверка
		MoveGuard.Mark(A)
		A:MoveTo(root.Position + Vector3.new(150, 0, 0))
		MoveGuard.Teleport(A, CFrame.new(root.Position + Vector3.new(0, 0, 20)))
		check(
			not (MoveGuard.Step(A)),
			"телепорт перед переносом сервером не замечен"
		)
		check((MoveGuard.Step(A)), "нарушение до переноса засчитано дважды")
		-- падение вниз (по вертикали) — не нарушение
		A:MoveTo(root.Position + Vector3.new(0, -60, 0))
		check((MoveGuard.Step(A)), "падение сочтено телепортом")
		-- новый персонаж (возрождение) — новая отметка
		local old = A.Character
		local copy = old:Clone()
		copy.Parent = old.Parent
		A.Character = copy
		copy.PrimaryPart.CFrame = CFrame.new(root.Position + Vector3.new(500, 0, 0))
		check((MoveGuard.Step(A)), "возрождение сочтено телепортом")
		A.Character = old
		copy:Destroy()
	end
)

test(
	"D52: бег вдвое быстрее, полёт и покачивание — нарушение; бег в допуске, прыжок, падение, край, ферма — нет",
	function(A)
		local humanoid = A.Character:FindFirstChildOfClass("Humanoid") :: Humanoid
		local speed = humanoid.WalkSpeed
		local seconds = GameConfig.MoveGuard.HoverSeconds + 1
		onPlatform(A, function(base: Vector3, platform: Part)
			-- челноком по площадке, шаг раз в 0.25 с: rate — во сколько раз быстрее скорости персонажа
			local function shuttle(rate: number, steps: number): boolean
				A:MoveTo(base)
				MoveGuard.Mark(A)
				local side = 1
				for _ = 1, steps do
					task.wait(0.25)
					side = -side
					A:MoveTo(base + Vector3.new(side * speed * rate * 0.125, 0, 0))
					if not (MoveGuard.Step(A)) then
						return false
					end
				end
				return true
			end
			check(not shuttle(2, 10), "бег вдвое быстрее скорости не замечен")
			check(
				shuttle(1.1, 8),
				"бег в пределах допуска (×1.1) сочтён нарушением"
			)
			-- высота: путь — список высот над площадкой по шагам 0.25 с (последняя повторяется до конца)
			A:MoveTo(base)
			check(
				math.abs((MoveGuard.Gap(A) or -1)) < 0.1,
				"стоящий на площадке не на полу: " .. tostring(MoveGuard.Gap(A))
			)
			local limit = MoveGuard.HoverLimit(A)
			local function fly(at: Vector3, heights: { number }): boolean
				A:MoveTo(at + Vector3.new(0, heights[1], 0))
				MoveGuard.Mark(A)
				local started, i = os.clock(), 1
				while os.clock() - started < seconds do
					task.wait(0.25)
					i += 1
					A:MoveTo(at + Vector3.new(0, heights[math.min(i, #heights)], 0))
					if not (MoveGuard.Step(A)) then
						return false
					end
				end
				return true
			end
			check(fly(base, { limit - 2 }), "высота прыжка сочтена полётом")
			local fall = {}
			for k = 0, 7 do
				fall[k + 1] = limit + 14 - 2 * k -- падение 8 ст./с, всё время выше порога
			end
			fall[9] = 0
			check(fly(base, fall), "падение сочтено полётом")
			check(not fly(base, { limit + 3 }), "полёт выше прыжка не замечен")
			local bob = {}
			for k = 1, 12 do
				bob[k] = limit + (if k % 2 == 0 then 1 else 3) -- вверх-вниз на 2 ст. выше прыжка
			end
			check(not fly(base, bob), "покачивание выше прыжка не замечено")
			-- край площадки: центр корня над пустотой, стопа на краю — не полёт
			local edge = base + Vector3.new(platform.Size.X / 2 + 1, 0, 0)
			check(fly(edge, { 0 }), "стоящий на краю сочтён летящим")
			-- ферма (TrussPart) рядом — лазание, не полёт
			local truss = Instance.new("TrussPart")
			truss.Anchored = true
			truss.Archivable = false
			truss.Size = Vector3.new(2, 30, 2)
			truss.CFrame = CFrame.new(base + Vector3.new(0, 15, 2))
			truss.Parent = workspace
			local ok, climbed = pcall(fly, base, { limit + 6 })
			truss:Destroy()
			check(ok and climbed, "лазание по ферме сочтено полётом")
		end)
	end
)

test(
	"D52: прыжок над ловушкой — не касание; бег и телепорт по полу через неё — касание; перенос сервером — нет",
	function(A, B)
		DataService.AddCoins(A, 1e6)
		TimeService.SkipTo("Preparation", -5)
		settle()
		DefenseService.Handlers.Action(A, "BuyDefense", "Trap")
		settle()
		DefenseService.Handlers.Action(A, "Install", "Trap", Vector3.new(5, 0, 5))
		local museum = DefenseService.Handlers.Museum(A.UserId)
		check(museum.installed.Trap ~= nil, "ловушка не встала")
		TimeService.SkipTo("DoomNight", -5)
		PvpService.Handlers.Reset()
		local origin = plotOf(A).floorOrigin
		local fb = PvpService.Handlers.Fighter(B)
		-- шаг вора по залу (оси участка; y — корень над полом, стоя 3) и такт защиты
		local function stand(z: number, y: number?)
			B.Character.PrimaryPart.CFrame = CFrame.new(origin * Vector3.new(5, y or 3, z))
			DefenseService.Handlers.Tick()
		end
		MoveGuard.Teleport(B, CFrame.new(origin * Vector3.new(5, 3, -6))) -- тестовый перенос в зал
		DefenseService.Handlers.Tick()
		MoveGuard.Teleport(B, CFrame.new(origin * Vector3.new(5, 3, 16))) -- сервер перенёс через ловушку
		DefenseService.Handlers.Tick()
		check(
			fb.hp == fb.maxHp,
			"перенос сервером через ловушку засчитан как пробег"
		)
		-- разбег по 4 ст. за такт, прыжок: над ловушкой — 9 над полом, приземление за ней
		stand(12)
		stand(8)
		stand(5, 9)
		stand(1)
		check(fb.hp == fb.maxHp, "прыжок над ловушкой засчитан как касание")
		-- бег по полу через ловушку за один такт (8 ст.) — касание
		stand(9)
		check(fb.hp < fb.maxHp, "пробежал по полу через ловушку — не сработала")
		-- телепорт клиента по полу через ловушку (дальше TrackStep, сервер не переносил) — касание
		table.clear(museum.cooldowns)
		fb.hp = fb.maxHp
		task.wait(GameConfig.Defense.Tick + 0.4) -- последний перенос сервером уже не «за этот такт»
		stand(-6)
		check(fb.hp < fb.maxHp, "телепорт по полу через ловушку не замечен")
	end
)

test(
	"D52: ошибка при уходе хозяина посреди кражи — добыча не зависает у вора, экспонат у владельца",
	function(A, B, ctx)
		local uid = displayOwn(ctx, A, 1)
		local userId = A.UserId
		doomNight()
		steal(B, A, 1)
		check(
			ItemRegistry.Get(uid).state == "Stolen" and ItemRegistry.GetCarriedBy(B) == uid,
			"B не унёс экспонат"
		)
		local unload = ItemRegistry.Unload
		local failed = false
		ItemRegistry.Unload = function(...)
			if not failed then
				failed = true
				error("сбой выгрузки (проверка D52)")
			end
			return unload(...)
		end
		local ok = pcall(leave, A)
		ItemRegistry.Unload = unload
		check(ok and failed, "сбой не смоделирован или выход упал")
		check(
			ItemRegistry.Get(uid) == nil,
			"экспонат ушедшего хозяина остался в реестре"
		)
		check(
			ItemRegistry.GetCarriedBy(B) == nil and B:GetAttribute("CarryingItemId") == nil,
			"добыча осталась у вора"
		)
		check(countUid(uid) == 0, "деталь экспоната осталась в мире")
		check(B:WasNotified("Хозяин музея ушёл"), "вору не сообщили")
		local again = TestPlayer.new("Тест_A_снова")
		again.UserId = userId
		ctx.track(again)
		check(join(again), "повторный вход не удался")
		local items = DataService.GetData(again).items
		check(items[uid] ~= nil and items[uid].place == "slot", "экспонат пропал у владельца")
		check(DataService.GetData(B).items[uid] == nil, "экспонат и у вора — дубль")
	end
)

test(
	"D52: жертва вышла до подтверждения — её финальное сохранение читается повторно",
	function(A, _B, ctx)
		local victim = TestPlayer.new("Тест_жертва") -- без профиля на сервере: как вышедшая
		ctx.track(victim)
		local id = "D52-проверка"
		local reads, cleared = 0, nil
		local readSaved, clearPending, saveAndWait =
			DataService.ReadSaved, DataService.ClearPending, DataService.SaveAndWait
		DataService.ReadSaved = function(userId: number, ...): (any?, boolean)
			if userId ~= victim.UserId then
				return readSaved(userId, ...)
			end
			reads += 1
			if reads < 3 then
				return nil, false -- финальная запись (конец сессии) ещё не дошла
			end
			return { transfersOut = { [id] = true } }, true
		end
		DataService.ClearPending = function(player: any, uid: string, transferId: string)
			if uid ~= "uid-D52" then
				return clearPending(player, uid, transferId)
			end
			cleared = uid .. "/" .. transferId
		end
		DataService.SaveAndWait = function(player: any, ...): boolean
			if player ~= victim and player ~= A then
				return saveAndWait(player, ...)
			end
			return false
		end
		local ok, err = pcall(TheftService.Handlers.Confirm, victim, A, "uid-D52", id)
		DataService.ReadSaved, DataService.ClearPending, DataService.SaveAndWait = readSaved, clearPending, saveAndWait
		check(ok, tostring(err))
		check(reads >= 3, "финальное сохранение прочитано раз: " .. reads)
		check(
			cleared == "uid-D52/" .. id,
			"передача не подтверждена после повторного чтения"
		)
	end
)

test(
	"D52: ошибка шага выхода не держит профиль и участок; повторный вход — всё на месте",
	function(A, _B, ctx)
		local uid = displayOwn(ctx, A, 1)
		local stored = toInventory(ctx, A)
		local userId = A.UserId
		local original = TheftService.OnPlayerLeaving
		TheftService.OnPlayerLeaving = function()
			error("сбой шага выхода (проверка D52)")
		end
		local ok = pcall(leave, A)
		TheftService.OnPlayerLeaving = original
		check(ok, "выход упал целиком")
		check(DataService.GetData(A) == nil, "сессия профиля не закрыта")
		check(PlotService.GetPlotOf(A) == nil, "участок остался за ушедшим")
		local again = TestPlayer.new("Тест_A_снова")
		again.UserId = userId
		ctx.track(again)
		check(join(again), "повторный вход не удался")
		local items = DataService.GetData(again).items
		check(
			items[uid] ~= nil and items[uid].place == "slot",
			"экспонат пропал после сбоя выхода"
		)
		check(
			items[stored] ~= nil and items[stored].place == "storage",
			"предмет из инвентаря пропал"
		)
		local count = 0
		for _ in items do
			count += 1
		end
		check(
			count == 2,
			"после повторного входа предметов "
				.. count
				.. " (дубль или потеря)"
		)
	end
)

test(
	"D52: сессию перехватили до или во время загрузки — профиль не отдаётся, игрок кикнут",
	function(_A, _B, ctx)
		local store = ProfileStore.New(GameConfig.Data.StoreName, ProfileTemplate).Mock
		-- перехват до конца загрузки
		local C = TestPlayer.new("Тест_C")
		ctx.track(C)
		local first = store:StartSessionAsync(GameConfig.Data.KeyPrefix .. C.UserId)
		check(first ~= nil, "сессия не открылась")
		first:EndSession()
		check(
			not DataService.Handlers.FinishLoad(C, first),
			"неактивный профиль отдан игроку"
		)
		check(DataService.GetData(C) == nil, "у игрока есть данные без сессии")
		check(C.kicked ~= nil, "игрока с перехваченной сессией не кикнули")
		-- перехват посреди загрузки, пока ждём журнал передач
		local D = TestPlayer.new("Тест_D")
		ctx.track(D)
		local second = store:StartSessionAsync(GameConfig.Data.KeyPrefix .. D.UserId)
		check(second ~= nil, "вторая сессия не открылась")
		local resolve = DataService.ResolveTransfers
		DataService.ResolveTransfers = function()
			second:EndSession()
			return nil
		end
		local loaded = DataService.Handlers.FinishLoad(D, second)
		DataService.ResolveTransfers = resolve
		check(not loaded, "профиль, потерянный во время загрузки, отдан")
		check(DataService.GetData(D) == nil, "у игрока данные без сессии")
		check(D.kicked ~= nil, "игрока без профиля не кикнули")
	end
)

test(
	"D52: запросы записи профиля — не чаще MinSaveInterval (лимит DataStore)",
	function(A)
		local profile = DataService.Handlers.Profile(A)
		check(profile ~= nil, "нет профиля")
		local calls = {}
		local save = profile.Save
		profile.Save = function(self, ...)
			table.insert(calls, os.clock())
			return save(self, ...)
		end
		local interval = GameConfig.Data.MinSaveInterval
		DataService.RequestSave(A) -- внеочередное сохранение тоже не чаще интервала (D52)
		local ok = DataService.SaveAndWait(A, interval * 2 + 1, function()
			return false -- подтверждение не приходит: запросы повторяются
		end)
		DataService.RequestSave(A)
		task.wait(0.2)
		profile.Save = nil -- снова метод профиля
		check(not ok, "подтверждение пришло само")
		check(#calls >= 2, "повторных запросов нет: " .. #calls)
		for i = 2, #calls do
			check(
				calls[i] - calls[i - 1] >= interval - 0.05,
				("запросы чаще %d с: %.2f"):format(interval, calls[i] - calls[i - 1])
			)
		end
	end
)

-- D53: время доставки, ждущие передачи, выход во время записи журнала ─────────────────────────────────────

-- Переноску «отодвинуть» в прошлое: как будто вор нёс добычу ещё seconds секунд.
local function carriedFor(thief: any, seconds: number)
	local carried = TheftService.Handlers.Carries[thief.UserId]
	check(carried ~= nil, "переноска не отмечена при снятии")
	carried.at -= seconds
end

-- Сколько раз uid встречается: в профилях игроков players (данные в памяти) и деталях мира.
local function owners(uid: string, players: { any }): number
	local count = 0
	for _, player in players do
		local data = DataService.GetData(player)
		if data and data.items[uid] ~= nil then
			count += 1
		end
	end
	return count
end

-- Есть ли запись id в журнале вора.
local function journaled(thief: any, id: string): boolean
	for _, entry in DataService.JournalRead(thief.UserId) or {} do
		if type(entry) == "table" and entry.id == id then
			return true
		end
	end
	return false
end

-- Условие выполнилось за seconds секунд (проверяется, пока не выполнится; после успеха — не вызывается).
local function eventually(seconds: number, condition: () -> boolean): boolean
	local started = os.clock()
	repeat
		if condition() then
			return true
		end
		task.wait(0.2)
	until os.clock() - started >= seconds
	return condition()
end

-- Незавершённая передача вручную: запись журнала вора; withRecord — у вора уже запись с pending и метка получения.
local function pendingTransfer(thief: any, victim: any, uid: string, itemId: string, id: string, withRecord: boolean)
	local record = {
		id = itemId,
		mods = {},
		place = "storage",
		rot = 0,
		acquiredAt = os.time(),
		source = "raid",
		from = victim.UserId,
	}
	check(
		DataService.JournalUpdate(thief.UserId, function(list)
			table.insert(list, { id = id, uid = uid, from = victim.UserId, record = record, at = os.time() })
			return list
		end),
		"журнал не записан"
	)
	if withRecord then
		local copy = table.clone(record)
		copy.pending = id
		local data = DataService.GetData(thief)
		data.items[uid] = copy
		data.transfersIn[id] = { uid = uid, at = os.time() }
	end
end

-- Жертва отдала экспонат по передаче id и сохранилась с меткой ухода (как после шага 2 и сохранения).
local function victimGave(victim: any, uid: string, id: string)
	local entry = ItemRegistry.Get(uid)
	local part = entry and entry.part
	ItemRegistry.Unload(uid)
	if part then
		part:Destroy()
	end
	local data = DataService.GetData(victim)
	data.items[uid] = nil
	data.transfersOut[id] = { uid = uid, at = os.time() }
	check(
		DataService.SaveAndWait(victim, 15, function(saved)
			return type(saved.transfersOut) == "table" and saved.transfersOut[id] ~= nil
		end),
		"жертва не сохранилась с меткой"
	)
end

test(
	"D53: время доставки — честная (и с лагом) не записана, телепорт записан и не заблокирован, перенос сервером засчитан",
	function(A, B, ctx)
		local first = displayOwn(ctx, A, 1)
		local second = displayOwn(ctx, A, 2)
		local third = displayOwn(ctx, A, 3)
		local plotB = plotOf(B)
		local function suspicious(): number
			return B:GetAttribute("SuspiciousDeliveries") or 0
		end
		-- честная: шёл по прямой на своей скорости, но события пришли на 1 с «раньше» (лаг)
		doomNight()
		steal(B, A, 1)
		local lifted = TheftService.Handlers.Carries[B.UserId]
		local offset = plotB.chest.Position - lifted.from
		local distance = Vector3.new(offset.X, 0, offset.Z).Magnitude
		check(
			distance > 30 and lifted.speed > 0,
			("путь %.1f, скорость %.1f"):format(distance, lifted.speed)
		)
		carriedFor(B, distance / lifted.speed - 1)
		deliverHome(B)
		check(ItemRegistry.Get(first).state == "Stored", "честная доставка не прошла")
		check(suspicious() == 0, "честная доставка записана как подозрительная")
		-- телепорт к сундуку сразу после кражи: записана, но сдача прошла (только лог, D53)
		doomNight()
		steal(B, A, 2)
		deliverHome(B)
		local entry = ItemRegistry.Get(second)
		check(
			entry.state == "Stored" and entry.owner == B.UserId,
			"подозрительная доставка заблокирована"
		)
		check(suspicious() == 1, "телепорт к сундуку не записан")
		-- перенос сервером к сундуку — не подозрительно
		doomNight()
		steal(B, A, 3)
		MoveGuard.Teleport(B, CFrame.new(plotB.chest.Position + Vector3.new(0, 0, -4)))
		InventoryService.Handlers.StoreCarried(B, plotB)
		check(
			ItemRegistry.Get(third).state == "Stored",
			"доставка после переноса сервером не прошла"
		)
		check(
			suspicious() == 1,
			"перенос сервером засчитан как подозрительная доставка"
		)
		check(
			owners(first, { A, B }) == 1 and owners(second, { A, B }) == 1 and owners(third, { A, B }) == 1,
			"дубли"
		)
	end
)

test(
	"D53: передача ждёт жертву после перезахода вора — решается во время сессии, без дублей и потерь",
	function(A, B, ctx)
		local uid = displayOwn(ctx, A, 1)
		doomNight()
		local cfgT = GameConfig.Theft
		local confirmSeconds, retry = cfgT.ConfirmSeconds, cfgT.ResolveRetrySeconds
		local saveAndWait = DataService.SaveAndWait
		local profileA = DataService.Handlers.Profile(A)
		-- сбой DataStore у жертвы: её сохранения не проходят, подтверждение передачи сдаётся быстро
		profileA.Save = function() end
		DataService.SaveAndWait = function(player: any, ...): boolean
			if player == A then
				task.wait(0.1)
				return false
			end
			return saveAndWait(player, ...)
		end
		cfgT.ConfirmSeconds = 0.5
		cfgT.ResolveRetrySeconds = 0.3
		local ok, err = pcall(function()
			steal(B, A, 1)
			deliverHome(B)
			check(ItemRegistry.Get(uid).state == "Stored", "сдача не прошла")
			task.wait(1)
			local id = DataService.GetData(B).items[uid].pending
			check(type(id) == "string", "у вора нет pending")
			local userId = B.UserId
			leave(B)
			local again = TestPlayer.new("Тест_B_снова")
			again.UserId = userId
			ctx.track(again)
			check(join(again), "повторный вход вора не удался")
			local record = DataService.GetData(again).items[uid]
			check(record and record.pending == id, "после входа передача не ждёт жертву")
			check(ItemRegistry.Get(uid) == nil, "ждущая передача попала в реестр")
			task.wait(1)
			check(
				DataService.GetData(again).items[uid].pending == id,
				"без метки жертвы передача решилась"
			)
			-- жертва сохранилась с меткой: следующая перепроверка решает «оставить»
			profileA.Save = nil
			DataService.SaveAndWait = saveAndWait
			check(
				DataService.SaveAndWait(A, 15, function(saved)
					return type(saved.transfersOut) == "table" and saved.transfersOut[id] ~= nil
				end),
				"жертва не сохранилась с меткой"
			)
			check(
				eventually(3, function()
					local now = DataService.GetData(again).items[uid]
					return now ~= nil and now.pending == nil
				end),
				"передача не решилась во время сессии"
			)
			local entry = ItemRegistry.Get(uid)
			check(
				entry and entry.state == "Stored" and entry.owner == again.UserId,
				"решённое не в инвентаре вора"
			)
			check(owners(uid, { A, again }) == 1 and countUid(uid) == 0, "дубль после решения")
			check(
				eventually(20, function()
					return not journaled(again, id)
				end),
				"запись журнала не удалена после подтверждения"
			)
		end)
		profileA.Save = nil
		DataService.SaveAndWait = saveAndWait
		cfgT.ConfirmSeconds, cfgT.ResolveRetrySeconds = confirmSeconds, retry
		if not ok then
			error(err, 0)
		end
	end
)

test(
	"D53: ждущая передача — окно проверок закончилось: ничего не выдано и не убрано, решается при следующем входе",
	function(A, B, ctx)
		local uid = displayOwn(ctx, A, 1)
		local itemId = ItemRegistry.Get(uid).itemId
		local id = "D53-окно"
		pendingTransfer(B, A, uid, itemId, id, true)
		local cfgT = GameConfig.Theft
		local retry, window = cfgT.ResolveRetrySeconds, cfgT.ResolveWindow
		cfgT.ResolveRetrySeconds, cfgT.ResolveWindow = 0.2, 1
		local ok, err = pcall(function()
			local userId = B.UserId
			leave(B)
			local again = TestPlayer.new("Тест_B_снова")
			again.UserId = userId
			ctx.track(again)
			check(join(again), "вход вора не удался")
			task.wait(1.6) -- окно закончилось, жертва метку не сохраняла
			local record = DataService.GetData(again).items[uid]
			check(
				record and record.pending == id,
				"без подтверждения предмет выдан или убран"
			)
			check(
				journaled(again, id),
				"запись журнала пропала — при входе не восстановить"
			)
			check(
				DataService.GetData(A).items[uid] ~= nil and ItemRegistry.Get(uid).state == "Displayed",
				"у жертвы пропал"
			)
			-- жертва отдала и сохранилась уже после окна: частых проверок больше нет — до входа передача ждёт
			victimGave(A, uid, id)
			task.wait(cfgT.ResolveRetrySeconds * 3)
			check(
				DataService.GetData(again).items[uid].pending == id,
				"после окна перепроверки продолжились"
			)
			check(journaled(again, id), "запись журнала пропала после окна")
			-- вор снова входит — решение при входе
			leave(again)
			local third = TestPlayer.new("Тест_B_третий")
			third.UserId = userId
			ctx.track(third)
			check(join(third), "третий вход вора не удался")
			local now = DataService.GetData(third).items[uid]
			check(
				now and now.pending == nil,
				"при следующем входе передача не решилась"
			)
			check(
				ItemRegistry.Get(uid) and ItemRegistry.Get(uid).owner == third.UserId,
				"не в реестре у вора"
			)
			check(owners(uid, { A, third }) == 1, "дубль")
		end)
		cfgT.ResolveRetrySeconds, cfgT.ResolveWindow = retry, window
		if not ok then
			error(err, 0)
		end
	end
)

test(
	"D53: перепроверка во время сессии — выдать (метка у жертвы) и убрать (жертва вышла без метки), без дублей",
	function(A, B, ctx)
		-- выдать: жертва сохранила уход, у вора записи ещё нет (сервер упал до его сохранения)
		local given = displayOwn(ctx, A, 1)
		local itemId = ItemRegistry.Get(given).itemId
		victimGave(A, given, "D53-выдать")
		pendingTransfer(B, A, given, itemId, "D53-выдать", false)
		local left = TheftService.Handlers.ResolveWaitingOnce(B, { "D53-выдать" })
		check(#left == 0, "выдача не решилась")
		local record = DataService.GetData(B).items[given]
		check(
			record and record.pending == nil and DataService.GetData(B).transfersIn["D53-выдать"],
			"вор не получил"
		)
		check(
			ItemRegistry.Get(given) and ItemRegistry.Get(given).owner == B.UserId,
			"выданное не в реестре вора"
		)
		check(owners(given, { A, B }) == 1 and countUid(given) == 0, "дубль после выдачи")
		-- убрать: у вора запись с pending, жертва без метки — пока она в игре, ждать; вышла без метки — кража не состоялась
		local kept = displayOwn(ctx, A, 2)
		pendingTransfer(B, A, kept, ItemRegistry.Get(kept).itemId, "D53-убрать", true)
		left = TheftService.Handlers.ResolveWaitingOnce(B, { "D53-убрать" })
		check(
			#left == 1 and DataService.GetData(B).items[kept].pending == "D53-убрать",
			"живая жертва без метки — решено"
		)
		local userIdA = A.UserId
		leave(A)
		check(
			eventually(5, function()
				left = TheftService.Handlers.ResolveWaitingOnce(B, { "D53-убрать" })
				return #left == 0
			end),
			"после выхода жертвы без метки передача не решилась"
		)
		check(
			DataService.GetData(B).items[kept] == nil,
			"у вора осталось то, что жертва не отдала — дубль"
		)
		check(
			eventually(30, function()
				return not journaled(B, "D53-убрать") and not journaled(B, "D53-выдать")
			end),
			"записи журнала не удалены"
		)
		local againA = TestPlayer.new("Тест_A_снова")
		againA.UserId = userIdA
		ctx.track(againA)
		check(join(againA), "вход жертвы не удался")
		local items = DataService.GetData(againA).items
		check(
			items[kept] and items[kept].place == "slot",
			"у жертвы пропал неотданный экспонат"
		)
		check(items[given] == nil, "отданный вернулся жертве — дубль")
		check(countUid(kept) == 1, "деталей неотданного: " .. countUid(kept))
	end
)

test(
	"D53: выход жертвы или вора во время записи журнала (шаг 1) — кража отменена, без потерь и дублей",
	function(A, B, ctx)
		local uid = displayOwn(ctx, A, 1)
		local other = displayOwn(ctx, A, 2)
		local userIdA, userIdB = A.UserId, B.UserId
		local journalUpdate = DataService.JournalUpdate
		-- жертва выходит, пока пишется журнал
		doomNight()
		steal(B, A, 1)
		local hit = false
		DataService.JournalUpdate = function(...)
			local result = journalUpdate(...)
			if not hit then
				hit = true
				leave(A)
			end
			return result
		end
		local ok, err = pcall(deliverHome, B)
		DataService.JournalUpdate = journalUpdate
		check(ok and hit, "сбой не смоделирован: " .. tostring(err))
		check(
			ItemRegistry.Get(uid) == nil and countUid(uid) == 0,
			"экспонат ушедшей жертвы остался на сервере"
		)
		check(
			DataService.GetData(B).items[uid] == nil,
			"вор получил экспонат ушедшей жертвы"
		)
		check(#(DataService.JournalRead(userIdB) or {}) == 0, "запись журнала осталась")
		local againA = TestPlayer.new("Тест_A_снова")
		againA.UserId = userIdA
		ctx.track(againA)
		check(join(againA), "вход жертвы не удался")
		check(DataService.GetData(againA).items[uid].place == "slot", "у жертвы пропал экспонат")
		check(countUid(uid) == 1, "деталей экспоната: " .. countUid(uid))
		-- вор выходит, пока пишется журнал
		doomNight()
		rested(B)
		steal(B, againA, 2)
		hit = false
		DataService.JournalUpdate = function(...)
			local result = journalUpdate(...)
			if not hit then
				hit = true
				leave(B)
			end
			return result
		end
		ok, err = pcall(deliverHome, B)
		DataService.JournalUpdate = journalUpdate
		check(ok and hit, "сбой не смоделирован: " .. tostring(err))
		local entry = ItemRegistry.Get(other)
		check(
			entry and entry.state == "Displayed" and entry.slot == 2 and countUid(other) == 1,
			"экспонат не вернулся"
		)
		check(DataService.GetData(againA).items[other].place == "slot", "у жертвы пропала запись")
		check(#(DataService.JournalRead(userIdB) or {}) == 0, "запись журнала вора осталась")
		local againB = TestPlayer.new("Тест_B_снова")
		againB.UserId = userIdB
		ctx.track(againB)
		check(join(againB), "вход вора не удался")
		check(DataService.GetData(againB).items[other] == nil, "вор получил экспонат — дубль")
	end
)

-- PvP Судной ночи (D37, D46) ─────────────────────────────────────────────────────────────────────────────────

-- B стоит в point, A — в 3 стадах позади по +Z и смотрит на него (−Z).
local function face(A: any, B: any, point: Vector3)
	B:MoveTo(point)
	A:MoveTo(point + Vector3.new(0, 0, 3))
	MoveGuard.Mark(A)
	MoveGuard.Mark(B)
	task.wait(0.2)
end

test(
	"PvP: урон, перезарядка, нокаут 15 с, лежачего не добить, добыча вора — владельцу",
	function(A, B, ctx)
		local uid = displayOwn(ctx, A, 1)
		doomNight()
		steal(B, A, 1)
		check(ItemRegistry.Get(uid).state == "Stolen", "B не унёс экспонат")
		face(A, B, plotOf(A).showcases[2].Position + Vector3.new(0, 0, -12))
		local fb = PvpService.Handlers.Fighter(B)
		local before = fb.hp
		PvpService.Handlers.Attack(A)
		check(fb.hp < before, "удар не снял HP")
		local hp1 = fb.hp
		PvpService.Handlers.Attack(A)
		check(fb.hp == hp1, "второй удар без перезарядки прошёл")
		for _ = 1, 60 do
			if fb.knockedUntil > 0 then
				break
			end
			task.wait(Battle.Player.AttackInterval + 0.05)
			PvpService.Handlers.Attack(A)
		end
		check(B:GetAttribute("Knocked") == true, "нокаута нет")
		local back = ItemRegistry.Get(uid)
		check(
			back.state == "Displayed" and back.slot == 1 and back.owner == A.UserId,
			"добыча не вернулась владельцу"
		)
		check(ItemRegistry.GetCarriedBy(B) == nil, "добыча осталась у B")
		check(math.abs(fb.knockedUntil - os.clock() - GameConfig.Pvp.KnockSeconds) < 2, "лежит не 15 с")
		task.wait(Battle.Player.AttackInterval + 0.05)
		PvpService.Handlers.Attack(A)
		check(fb.hp == 0, "лежачего добили")
		rested(B)
		steal(B, A, 1, 0.1)
		check(ItemRegistry.Get(uid).state == "Displayed", "оглушённый начал кражу")
		PvpService.Handlers.Recover(B)
		check(B:GetAttribute("Knocked") == nil and fb.hp == fb.maxHp, "не встал с полным HP")
	end
)

test("PvP: у места появления и вне Судной ночи урона нет", function(A, B)
	doomNight()
	PvpService.Handlers.Reset()
	face(A, B, MapLayout.Spawn.position + Vector3.new(0, 3, 0))
	local fb = PvpService.Handlers.Fighter(B)
	PvpService.Handlers.Attack(A)
	check(fb.hp == fb.maxHp, "урон у места появления")
	TimeService.SkipTo("Day", -(GameConfig.Time.DeliveryGrace + 5))
	face(A, B, plotOf(A).showcases[2].Position + Vector3.new(0, 0, -12))
	task.wait(Battle.Player.AttackInterval + 0.05)
	PvpService.Handlers.Attack(A)
	check(fb.hp == fb.maxHp, "урон днём")
end)

-- Защита музея и взлом (D37, D46) ─────────────────────────────────────────────────────────────────────────────

test(
	"Защита: покупка и установка только в подготовку, min(уровень, 5), места, после ночи списано",
	function(A)
		DataService.AddCoins(A, 1e6)
		local museum = DefenseService.Handlers.Museum(A.UserId)
		DefenseService.Handlers.Action(A, "BuyDefense", "Trap")
		check(defenseStock(A, "Trap") == 0, "защиту купили днём")
		TimeService.SkipTo("Preparation", -5)
		settle()
		DefenseService.Handlers.Action(A, "BuyDefense", "Trap")
		settle()
		DefenseService.Handlers.Action(A, "BuyDefense", "Laser")
		settle()
		DefenseService.Handlers.Action(A, "BuyDefense", "Snare")
		check(
			defenseStock(A, "Trap") == 1 and defenseStock(A, "Laser") == 1,
			"в подготовку не купилось"
		)
		check(defenseStock(A, "Snare") == 0, "капкан без утверждённой цены продан")
		settle()
		DefenseService.Handlers.Action(A, "Install", "Trap", Vector3.new(13.4, 0, -2)) -- место 1 (D48-C)
		check(museum.installed.Trap == nil, "ловушку поставили на постамент")
		settle()
		DefenseService.Handlers.Action(A, "Install", "Trap", Vector3.new(5, 0, 5))
		check(museum.installed.Trap ~= nil, "ловушка не встала в проход между рядами")
		settle()
		DefenseService.Handlers.Action(A, "Install", "Laser", "Gallery")
		check(
			museum.installed.Laser == nil and A:WasNotified("Больше устройств"),
			"музей ур. 1 принял второе устройство"
		)
		TimeService.SkipTo("DoomNight", -2)
		DefenseService.Handlers.EndNight()
		check(
			defenseStock(A, "Trap") == 0 and defenseStock(A, "Laser") == 1,
			"после ночи списано не то"
		)
		check(next(museum.installed) == nil, "установленное не исчезло")
	end
)

test(
	"Защита: дверь не пускает вора, взлом 5 с, ловушка бьёт вора",
	function(A, B)
		DataService.AddCoins(A, 1e6)
		DataService.AddCoins(B, 1e6)
		DataService.GetData(A).museumLevel = 2 -- два устройства
		DefenseService.Handlers.Action(B, "BuyHack", 2)
		check((DataService.Defense(B).hacks.L2 or 0) == 1, "взлом днём не купился")
		TimeService.SkipTo("Preparation", -5)
		settle()
		DefenseService.Handlers.Action(A, "BuyDefense", "Door")
		settle()
		DefenseService.Handlers.Action(A, "BuyDefense", "Trap")
		settle()
		DefenseService.Handlers.Action(A, "Install", "Door", "Entrance")
		settle()
		DefenseService.Handlers.Action(A, "Install", "Trap", Vector3.new(5, 0, 5))
		local museum = DefenseService.Handlers.Museum(A.UserId)
		check(museum.installed.Door and museum.installed.Trap, "дверь и ловушка не встали")
		TimeService.SkipTo("DoomNight", -5)
		PvpService.Handlers.Reset()
		local plotA = plotOf(A)
		B:MoveTo(plotA.floorOrigin * Vector3.new(0, 3, 10))
		DefenseService.Handlers.Tick()
		local inside = plotA.floorOrigin:PointToObjectSpace(B.Character.PrimaryPart.Position)
		check(inside.Z < GameConfig.Defense.Door.At.Z, "закрытая дверь пустила вора в зал")
		B:MoveTo(plotA.floorOrigin * Vector3.new(0, 3, -15))
		DefenseService.Handlers.HackBegin(B, A, plotA)
		task.wait(1)
		DefenseService.Handlers.HackComplete(B, A, plotA)
		check(not museum.hacked, "взлом за 1 с прошёл")
		DefenseService.Handlers.HackBegin(B, A, plotA)
		task.wait(GameConfig.Defense.HackSeconds + 0.1)
		DefenseService.Handlers.HackComplete(B, A, plotA)
		check(
			museum.hacked and (DataService.Defense(B).hacks.L2 or 0) == 0,
			"взлом не открыл дверь или устройство не списано"
		)
		B:MoveTo(plotA.floorOrigin * Vector3.new(5, 3, 5))
		local fb = PvpService.Handlers.Fighter(B)
		DefenseService.Handlers.Tick()
		check(fb.hp < fb.maxHp, "ловушка не ударила вора")
		local inHall = plotA.floorOrigin:PointToObjectSpace(B.Character.PrimaryPart.Position)
		check(inHall.Z > 0, "после взлома вора всё равно выставило")
	end
)

-- D49 (проверка на трёх клиентах): вор бежит 14 стадов/с, такт 0.2 с — за такт 2.8 стада, луч 1.2: лазер срабатывал
-- случайно. Теперь смотрит путь вора за такт; перенос (скачок дальше TrackStep) лазер не задевает.
test("Защита: лазер ловит вора, пробежавшего луч за такт (D49)", function(A, B)
	DataService.AddCoins(A, 1e6)
	TimeService.SkipTo("Preparation", -5)
	settle()
	DefenseService.Handlers.Action(A, "BuyDefense", "Laser")
	settle()
	DefenseService.Handlers.Action(A, "Install", "Laser", "Entrance")
	check(DefenseService.Handlers.Museum(A.UserId).installed.Laser ~= nil, "лазер не встал")
	TimeService.SkipTo("DoomNight", -5)
	PvpService.Handlers.Reset()
	local origin = plotOf(A).floorOrigin
	local beam = GameConfig.Defense.Lasers.Entrance
	local function stand(z: number)
		B.Character.PrimaryPart.CFrame = CFrame.new(origin * Vector3.new(0, 3, z))
	end
	local fb = PvpService.Handlers.Fighter(B)
	MoveGuard.Teleport(B, CFrame.new(origin * Vector3.new(0, 3, beam.z - 30))) -- тестовый перенос (D52)
	DefenseService.Handlers.Tick()
	MoveGuard.Teleport(B, CFrame.new(origin * Vector3.new(0, 3, beam.z + 1.5))) -- перенос сервером через луч
	DefenseService.Handlers.Tick()
	check(fb.hp == fb.maxHp, "перенос через луч засчитан как пробег")
	stand(beam.z - 1.5) -- пробежал луч за такт: ни одна из двух точек не в луче
	DefenseService.Handlers.Tick()
	check(fb.hp < fb.maxHp, "лазер не поймал пробежавшего вора")
	check(A:WasNotified("Тревога! Лазер"), "владельцу не пришла тревога")
end)

-- D47: робот на трёх клиентах бил вора и терял HP, но за ночь его не успели доломать (300 HP) — поломка здесь.
test(
	"Защита: робот бьёт вора в радиусе, не трогает владельца, сломанный молчит",
	function(A, B)
		DataService.AddCoins(A, 1e6)
		TimeService.SkipTo("Preparation", -5)
		settle()
		DefenseService.Handlers.Action(A, "BuyDefense", "Robot")
		settle()
		DefenseService.Handlers.Action(A, "Install", "Robot", Vector3.new(-7, 0, 14)) -- боковой проход (D48-C)
		local robot = DefenseService.Handlers.Museum(A.UserId).installed.Robot
		check(robot ~= nil, "робот не встал")
		TimeService.SkipTo("DoomNight", -5)
		PvpService.Handlers.Reset()
		local origin = plotOf(A).floorOrigin
		local robotAt = origin * Vector3.new(-7, 0, 14)
		local function stand(player: any, spot: Vector3)
			local at = origin * spot
			player.Character.PrimaryPart.CFrame = CFrame.lookAt(at, Vector3.new(robotAt.X, at.Y, robotAt.Z))
		end
		stand(A, Vector3.new(-14, 3, 14))
		local fa = PvpService.Handlers.Fighter(A)
		DefenseService.Handlers.Tick()
		check(fa.hp == fa.maxHp, "робот ударил владельца")
		stand(A, Vector3.new(10, 3, -8))
		stand(B, Vector3.new(10, 3, 0)) -- в зале, но дальше радиуса
		local fb = PvpService.Handlers.Fighter(B)
		DefenseService.Handlers.Tick()
		check(fb.hp == fb.maxHp, "робот ударил вора вне радиуса")
		stand(B, Vector3.new(-10.5, 3, 14)) -- в радиусе робота и на расстоянии удара
		DefenseService.Handlers.Tick()
		check(fb.hp < fb.maxHp, "робот не ударил вора в радиусе")
		robot.hp = 1 -- проверяется поломка, а не запас HP
		PvpService.Handlers.Attack(B)
		check(
			robot.broken == true and robot.model.Parent == nil,
			"робот не сломался от удара вора"
		)
		local hp = fb.hp
		robot.lastAttack = nil
		DefenseService.Handlers.Tick()
		check(fb.hp == hp, "сломанный робот бьёт")
		check(
			A:WasNotified("Вашего робота-охранника сломали"),
			"владельцу не сообщили о поломке"
		)
	end
)

-- Проверки по ревью D46 (2026-11-05) ─────────────────────────────────────────────────────────────────────────

test(
	"Ревью: миграция через настоящую загрузку — двойной постамент, вне музея, нечитаемые записи",
	function(A, _B, ctx)
		local keep = displayOwn(ctx, A, 1)
		local data = DataService.GetData(A)
		data.schema = 2
		data.items["dup-late"] = { id = "Moai", mods = {}, place = "slot", slot = 1, rot = 0, acquiredAt = 9e9 }
		data.items["far"] = { id = "Moai", mods = {}, place = "slot", slot = 99, rot = 0 }
		data.items["num"] = 5
		data.items["flag"] = true
		local userId = A.UserId
		leave(A)
		local again = TestPlayer.new("Тест_A_снова")
		again.UserId = userId
		ctx.track(again)
		check(join(again), "A не вошёл после миграции")
		local items = DataService.GetData(again).items
		check(DataService.GetData(again).schema == 5, "схема не 5 (v2 → v3 → v4 D55 → v5 D56)")
		check(
			ItemRegistry.Get(keep).state == "Displayed" and ItemRegistry.Get(keep).slot == 1,
			"старший экспонат не на месте"
		)
		check(
			items["dup-late"].place == "storage" and ItemRegistry.Get("dup-late").state == "Stored",
			"второй на постаменте 1"
		)
		check(items["far"].place == "storage", "экспонат вне музея не в инвентаре")
		check(items["num"] == 5 and items["flag"] == true, "нечитаемые записи потеряны")
		check(
			not DataService.IsSlotFree(again, 1) and DataService.IsSlotFree(again, 2),
			"IsSlotFree споткнулся о запись"
		)
		check(countUid(keep) == 1, "дубль экспоната")
	end
)

test(
	"Ревью: предмет «передаётся» нельзя выставить; поворот и перестановка во время кражи — нет",
	function(A, B, ctx)
		local mine = toInventory(ctx, A)
		DataService.GetData(A).items[mine].pending = "test-transfer"
		InventoryService.Handlers.Action(A, "Display", mine, 2)
		check(
			ItemRegistry.Get(mine).state == "Stored",
			"выставили предмет, который ещё передаётся"
		)
		DataService.GetData(A).items[mine].pending = nil
		local shown = displayOwn(ctx, A, 1)
		doomNight()
		local plotA = plotOf(A)
		near(B, plotA.showcases[1])
		TheftService.Handlers.Begin(B, plotA, 1)
		check(ItemRegistry.Get(shown).state == "Lifting", "кража не началась")
		near(A, plotA.showcases[1])
		MuseumService.Handlers.Rotate(A, plotA, 1)
		check(
			DataService.GetData(A).items[shown].rot == 0,
			"повернули экспонат, который снимает вор"
		)
		TheftService.Handlers.Cancel(B)
		check(ItemRegistry.Get(shown).state == "Displayed", "после отмены не на месте")
	end
)

test(
	"Ревью: залипшее удержание и уход владельца во время кражи",
	function(A, B, ctx)
		local first = displayOwn(ctx, A, 1)
		doomNight()
		local plotA = plotOf(A)
		near(B, plotA.showcases[1])
		TheftService.Handlers.Begin(B, plotA, 1)
		local cfg = GameConfig.Theft
		task.wait(cfg.HoldSeconds + cfg.HoldTolerance + cfg.LiftGrace + 0.3)
		TheftService.Handlers.Sweep()
		check(
			ItemRegistry.Get(first).state == "Displayed",
			"залипшее удержание держит резерв"
		)
		task.wait(0.3)
		rested(B)
		steal(B, A, 1)
		check(ItemRegistry.Get(first).state == "Stolen", "B не унёс экспонат")
		local userId = A.UserId
		leave(A)
		check(
			ItemRegistry.Get(first) == nil and ItemRegistry.GetCarriedBy(B) == nil,
			"после ухода владельца добыча осталась"
		)
		check(countUid(first) == 0, "деталь добычи осталась в мире")
		local again = TestPlayer.new("Тест_A_снова")
		again.UserId = userId
		ctx.track(again)
		check(join(again), "A не вошёл")
		check(DataService.GetData(again).items[first] ~= nil, "экспонат пропал у владельца")
		check(next(DataService.GetData(B).items) == nil, "у B появился предмет")
	end
)

test(
	"Ревью: капкан — 10 с не ходит и не бьёт, по нему бьют, нокаут снимает капкан",
	function(A, B)
		doomNight()
		PvpService.Handlers.Reset()
		face(A, B, plotOf(A).showcases[2].Position + Vector3.new(0, 0, -12))
		check(
			PvpService.Handlers.Snare(B, GameConfig.Defense.Snare.Seconds) == true,
			"капкан не сработал"
		)
		check(
			not PvpService.Handlers.Snare(B, 1),
			"второй капкан сработал на пойманного"
		)
		check(B:GetAttribute("Snared") == true, "нет атрибута Snared")
		-- D53 (три клиента): прыжок в игре — по JumpPower; пойманный не ходит и не прыгает
		local humanoid = B.Character:FindFirstChildOfClass("Humanoid") :: Humanoid
		check(
			humanoid.WalkSpeed == 0 and humanoid.JumpHeight == 0 and humanoid.JumpPower == 0,
			("пойманный может двигаться: скорость %s, прыжок %s/%s"):format(
				tostring(humanoid.WalkSpeed),
				tostring(humanoid.JumpHeight),
				tostring(humanoid.JumpPower)
			)
		)
		local fb = PvpService.Handlers.Fighter(B)
		PvpService.Handlers.Attack(A)
		check(fb.hp < fb.maxHp, "по пойманному не бьётся")
		-- пойманный B не бьёт A
		face(B, A, plotOf(A).showcases[2].Position + Vector3.new(0, 0, -12))
		local fa = PvpService.Handlers.Fighter(A)
		PvpService.Handlers.Attack(B)
		check(fa.hp == fa.maxHp, "пойманный ударил")
		face(A, B, plotOf(A).showcases[2].Position + Vector3.new(0, 0, -12))
		for _ = 1, 60 do
			if B:GetAttribute("Knocked") then
				break
			end
			task.wait(Battle.Player.AttackInterval + 0.05)
			PvpService.Handlers.Attack(A)
		end
		check(
			B:GetAttribute("Knocked") == true and B:GetAttribute("Snared") == nil,
			"нокаут не снял капкан"
		)
		check(
			humanoid.JumpPower == 0 and humanoid.WalkSpeed == 0,
			"оглушённый может прыгать или ходить"
		)
		PvpService.Handlers.Recover(B)
		check(
			humanoid.JumpPower == game:GetService("StarterPlayer").CharacterJumpPower and humanoid.WalkSpeed > 0,
			"после подъёма прыжок или скорость не вернулись"
		)
	end
)

test(
	"Ревью: защита списывается при установке, возвращается до ночи; взлом вне ночи не начинается",
	function(A, B)
		DataService.AddCoins(A, 1e6)
		TimeService.SkipTo("Preparation", -5)
		settle()
		DefenseService.Handlers.Action(A, "BuyDefense", "Trap")
		settle()
		DefenseService.Handlers.Action(A, "Install", "Trap", Vector3.new(5, 0, 5))
		local defense = DataService.Defense(A)
		local placed = defense.installed.Trap
		check(defenseStock(A, "Trap") == 0, "установка не списала ловушку")
		check(
			type(placed) == "table" and placed.cycle == GameTime.Current().cycle and placed.level == 1,
			"запись об установке — не { круг, уровень покупки }"
		)
		settle()
		DefenseService.Handlers.Action(A, "Remove", "Trap")
		check(
			defenseStock(A, "Trap") == 1 and defense.installed.Trap == nil,
			"снятие не вернуло ловушку"
		)
		settle()
		DefenseService.Handlers.Action(A, "Install", "Trap", Vector3.new(5, 0, 5))
		DefenseService.OnPlayerLeaving(A) -- вышел в подготовку
		check(defenseStock(A, "Trap") == 1, "выход до ночи не вернул ловушку")
		DataService.AddCoins(B, 1e6)
		DefenseService.Handlers.HackBegin(B, A, plotOf(A))
		check(
			DefenseService.Handlers.Museum(A.UserId).hackBegan[B] == nil,
			"взлом начался в подготовку"
		)
	end
)

-- Проверка тремя клиентами (2026-11-05): сервер получает конец удержания раньше Triggered в том же кадре.
test(
	"Удержание: конец удержания перед Triggered — завершение, а не отмена",
	function()
		local began = Instance.new("BindableEvent")
		local ended = Instance.new("BindableEvent")
		local triggered = Instance.new("BindableEvent")
		local fake = {
			PromptButtonHoldBegan = began.Event,
			PromptButtonHoldEnded = ended.Event,
			Triggered = triggered.Event,
		}
		local log = {}
		Prompts.BindHold(fake :: any, function()
			table.insert(log, "begin")
		end, function()
			table.insert(log, "cancel")
		end, function()
			table.insert(log, "complete")
		end)
		-- игрок — экземпляр (BindableEvent копирует таблицы, у тестового игрока ключ был бы каждый раз другой)
		local who = Instance.new("Folder")
		local grace = GameConfig.HoldRelease.ReleaseGrace + 0.2
		local function run(order: { BindableEvent }): string
			table.clear(log)
			for _, event in order do
				event:Fire(who)
			end
			task.wait(grace)
			return table.concat(log, ",")
		end
		local roblox = run({ began, ended, triggered })
		check(roblox == "begin,complete", "порядок как в Roblox: " .. roblox)
		local reverse = run({ began, triggered, ended })
		check(reverse == "begin,complete", "обратный порядок: " .. reverse)
		local early = run({ began, ended }) -- отпустил раньше времени
		check(early == "begin,cancel", "отпускание не отменило: " .. early)
		-- отпустил и сразу нажал снова (ревью D47): прежнее удержание отменяется до нового начала
		local again = run({ began, ended, began, triggered })
		check(again == "begin,cancel,begin,complete", "повторное нажатие: " .. again)
		for _, event in { began, ended, triggered } do
			event:Destroy()
		end
		who:Destroy()
	end
)

test("Улучшить можно только свою гантель", function(A, B)
	local price = GameConfig.Progression.Dumbbell.Prices[1]
	DataService.AddCoins(A, price)
	DataService.AddCoins(B, price)
	local plotA = plotOf(A)
	near(B, plotA.signBoard)
	GymService.Handlers.Upgrade(B, plotA)
	check(
		DataService.GetData(B).dumbbellLevel == 1 and DataService.GetData(B).coins == price,
		"B улучшил чужую"
	)
	check(
		DataService.GetData(A).dumbbellLevel == 1 and DataService.GetData(A).coins == price,
		"у A списались монеты"
	)
	check(plotA.model:GetAttribute("DumbbellLevel") == 1, "гантель A сменилась от B")
	near(A, plotA.signBoard)
	GymService.Handlers.Upgrade(A, plotA)
	check(
		DataService.GetData(A).dumbbellLevel == 2 and DataService.GetData(A).coins == 0,
		"A не улучшил свою"
	)
	check(plotA.model:GetAttribute("DumbbellLevel") == 2, "модель гантели A не сменилась")
end)

test("В чужом поле качалки сила не растёт, в своём — растёт", function(A, B)
	local plotA = plotOf(A)
	local inField = plotA.fieldCFrame.Position + Vector3.new(1, 3, 1)
	B:MoveTo(inField)
	GymService.Handlers.TickPlayer(B)
	check(DataService.GetData(B).strength == 0, "B качается в чужом поле")
	check(B:WasNotified("Это гантель игрока " .. A.DisplayName), "нет подсказки гостю")
	A:MoveTo(inField + Vector3.new(2, 0, 0))
	GymService.Handlers.TickPlayer(A)
	check(DataService.GetData(A).strength > 0, "A не качается в своём поле")
end)

-- D51: огромной гантели во дворе нет; гантель уровня — в руке у владельца в своём поле с пустыми руками.
-- У манекена нет рук: кисть R15 для гантели — деталь, приваренная к корню (ходит вместе с ним).
local function giveHand(player: any): BasePart
	local root = player.Character.PrimaryPart :: BasePart
	local hand = Instance.new("Part")
	hand.Name = "RightHand"
	hand.Size = Vector3.new(0.6, 0.6, 0.6)
	hand.CanCollide = false
	hand.Transparency = 1
	hand.CFrame = root.CFrame * CFrame.new(1.5, -1, 0)
	local weld = Instance.new("WeldConstraint")
	weld.Part0 = root
	weld.Part1 = hand
	weld.Parent = hand
	hand.Parent = player.Character
	return hand
end

local function trains(player: any): boolean
	return player:GetAttribute("Training") == true and HandDumbbell.Get(player.Character) ~= nil
end

local function idle(player: any): boolean
	return player:GetAttribute("Training") == nil and HandDumbbell.Get(player.Character) == nil
end

test(
	"D51: гантель в руке — в своём поле; выход, экспонат, нокаут, смерть прекращают; гостю нет",
	function(A, B, ctx)
		local plotA = plotOf(A)
		check(
			plotA.model:FindFirstChild("GiantDumbbell", true) == nil,
			"во дворе стоит огромная гантель"
		)
		local hand = giveHand(A)
		local inField = plotA.fieldCFrame.Position + Vector3.new(1, 3, 1)
		A:MoveTo(inField)
		local data = DataService.GetData(A)
		local before = data.strength
		local gain = GameConfig.Progression.Dumbbell.Power[data.dumbbellLevel] * (1 + GymService.MuseumPower(A))
		GymService.Handlers.TickPlayer(A)
		check(trains(A), "в своём поле тренировка не началась")
		check(
			data.strength == before + gain,
			"сила за такт изменилась: " .. tostring(data.strength - before)
		)
		local model = HandDumbbell.Get(A.Character) :: Model
		check(
			model:GetAttribute("Level") == data.dumbbellLevel,
			"в руке гантель не того уровня"
		)
		local _, size = model:GetBoundingBox()
		local longest = math.max(size.X, size.Y, size.Z)
		check(
			math.abs(longest - GameConfig.Gym.HandDumbbell.Length) < 0.1,
			"гантель не обычного размера: " .. longest
		)
		local parts = 0
		for _, part in model:GetChildren() do
			if part:IsA("BasePart") then
				parts += 1
				check(
					part:IsA("MeshPart"),
					"в руке не модель гантели, а примитив " .. part.Name
				)
				check(
					part.Massless and not part.CanCollide and not part.Anchored,
					"деталь гантели мешает: " .. part.Name
				)
				local welded = part:FindFirstChildOfClass("WeldConstraint")
				check(
					welded and welded.Part0 == hand,
					"деталь гантели не приварена к кисти"
				)
			end
		end
		check(parts > 0, "у гантели в руке нет деталей")
		-- гость в чужом поле: подсказка, без тренировки и гантели
		B:MoveTo(inField + Vector3.new(2, 0, 0))
		GymService.Handlers.TickPlayer(B)
		check(idle(B), "гость тренируется в чужом поле")
		-- экспонат в руках — тренировка прекращается, сила не растёт
		carry(ctx, A)
		GymService.Handlers.Refresh(A)
		check(idle(A), "с экспонатом гантель в руке")
		local carrying = data.strength
		GymService.Handlers.TickPlayer(A)
		check(data.strength == carrying, "с экспонатом в руках сила растёт")
		CarryService.Drop(A)
		GymService.Handlers.Refresh(A)
		check(trains(A), "после броска тренировка не вернулась")
		-- нокаут
		A:SetAttribute("Knocked", true)
		GymService.Handlers.Refresh(A)
		check(idle(A), "в нокауте гантель в руке")
		A:SetAttribute("Knocked", nil)
		GymService.Handlers.Refresh(A)
		check(trains(A), "после нокаута тренировка не вернулась")
		-- вышел из поля
		A:MoveTo(inField + Vector3.new(0, 0, GameConfig.Gym.FieldSize.Y))
		GymService.Handlers.Refresh(A)
		check(idle(A), "вне поля гантель в руке")
		-- смерть
		A:MoveTo(inField)
		GymService.Handlers.Refresh(A)
		check(trains(A), "в поле снова не тренируется")
		local humanoid = A.Character:FindFirstChildOfClass("Humanoid") :: Humanoid
		humanoid.Health = 0
		GymService.Handlers.Refresh(A)
		check(idle(A), "у погибшего гантель в руке")
	end
)

test(
	"D51: гантель в руке меняется с уровнем и не копится, одна на персонажа",
	function(A)
		local cfg = GameConfig.Progression.Dumbbell
		check(GameConfig.Gym.TickSeconds == 1, "такт не 1 с — один подъём в секунду")
		giveHand(A)
		local first = HandDumbbell.Attach(A.Character, 1)
		check(
			first and HandDumbbell.Attach(A.Character, 1) == first,
			"та же гантель пересоздаётся"
		)
		for level = 2, #cfg.Power do
			local model = HandDumbbell.Attach(A.Character, level)
			check(
				model and model:GetAttribute("Level") == level,
				"гантель уровня " .. level .. " не встала"
			)
		end
		local count = 0
		for _, child in A.Character:GetChildren() do
			if child.Name == HandDumbbell.Name then
				count += 1
			end
		end
		check(count == 1, "в руке гантелей: " .. count)
		HandDumbbell.Remove(A.Character)
		check(HandDumbbell.Get(A.Character) == nil, "гантель не убралась")
		check(
			plotOf(A).model:GetAttribute("DumbbellLevel") == 1,
			"уровень гантели участка (табличка) не 1"
		)
	end
)

test(
	"D51: в нокауте сила идёт, гантели нет; у края поля — запас на выход; R6; такт по серверному времени",
	function(A)
		local plotA = plotOf(A)
		giveHand(A)
		local field = plotA.fieldCFrame
		local half = GameConfig.Gym.FieldSize.X / 2
		local margin = GameConfig.Gym.FieldMargin
		A:MoveTo((field * CFrame.new(0, 3, 0)).Position)
		local data = DataService.GetData(A)
		-- нокаут: правило силы как до D51 (своё поле, пустые руки), но лежачий гантель не поднимает
		A:SetAttribute("Knocked", true)
		local before = data.strength
		GymService.Handlers.TickPlayer(A)
		check(data.strength > before, "в нокауте в своём поле сила перестала идти")
		check(idle(A), "в нокауте гантель в руке")
		A:SetAttribute("Knocked", nil)
		GymService.Handlers.Refresh(A)
		check(trains(A), "после нокаута тренировка не вернулась")
		-- у края: тренирующийся чуть за краем (в пределах запаса) продолжает, дальше — нет; новый за краем — не начинает
		A:MoveTo((field * CFrame.new(half + margin / 2, 3, 0)).Position)
		GymService.Handlers.Refresh(A)
		check(trains(A), "у края поля гантель мигает")
		local edge = data.strength
		GymService.Handlers.TickPlayer(A)
		check(data.strength == edge, "за краем поля сила идёт")
		A:MoveTo((field * CFrame.new(half + margin + 0.5, 3, 0)).Position)
		GymService.Handlers.Refresh(A)
		check(idle(A), "за запасом края тренировка не прекратилась")
		A:MoveTo((field * CFrame.new(half + margin / 2, 3, 0)).Position)
		GymService.Handlers.Refresh(A)
		check(idle(A), "за краем поля тренировка началась")
		-- R6: гантель — к низу правой руки (Right Arm)
		local r6 = Instance.new("Model")
		local arm = Instance.new("Part")
		arm.Name = "Right Arm"
		arm.Size = Vector3.new(1, 2, 1)
		arm.Anchored = true
		arm.CanCollide = false
		arm.CFrame = CFrame.new(0, 600, -3000)
		arm.Parent = r6
		r6.Parent = workspace
		local model = HandDumbbell.Attach(r6, 3)
		local ok = model ~= nil
		for _, part in if model then model:GetChildren() else {} do
			local weld = part:FindFirstChildOfClass("WeldConstraint")
			ok = ok and weld ~= nil and weld.Part0 == arm
		end
		local centre = if model then arm.CFrame:PointToObjectSpace(model:GetBoundingBox().Position) else Vector3.zero
		r6:Destroy()
		check(ok, "у R6 гантель не в правой руке")
		check(centre.Y < -0.5, "у R6 гантель не у кулака (низ руки): " .. tostring(centre))
		-- такт: граница целой секунды общего серверного времени, на одной границе — один раз
		check(GymService.NextTick(10.3, 1, -math.huge) == 11, "такт не на следующей границе")
		check(GymService.NextTick(10.999, 1, 10) == 11, "такт пропущен")
		check(GymService.NextTick(11.0001, 1, 11) == 12, "такт повторён на той же границе")
		check(
			GymService.NextTick(10.9999, 1, 11) == 12,
			"такт раньше времени после повтора"
		)
	end
)

test(
	"Предмет несёт только один игрок; чужой экспонат не поднять",
	function(A, B, ctx)
		local plotA = plotOf(A)
		near(A, plotA.showcases[3])
		local uid, part = mapItem(ctx, A.Character.PrimaryPart.Position + Vector3.new(0, 0, 3))
		B:MoveTo(part.Position + Vector3.new(0, 0, 2))
		CarryService.Handlers.Pickup(A, uid)
		CarryService.Handlers.Pickup(B, uid)
		check(
			ItemRegistry.GetCarriedBy(A) == uid and ItemRegistry.GetCarriedBy(B) == nil,
			"у предмета не один носитель"
		)
		MuseumService.Handlers.Display(A, plotA, 3)
		check(ItemRegistry.Get(uid).state == "Displayed", "A не выставил предмет")
		B:MoveTo(plotA.showcases[3].Position + Vector3.new(0, 0, -3))
		CarryService.Handlers.Pickup(B, uid)
		check(
			ItemRegistry.Get(uid).state == "Displayed" and ItemRegistry.GetCarriedBy(B) == nil,
			"B поднял чужой экспонат"
		)
	end
)

test(
	"Реестр не пускает предмет в чужой музей и чужое хранилище",
	function(A, B, ctx)
		local uid = carry(ctx, B)
		local toShowcase = ItemRegistry.Transition(uid, "Displayed", { owner = A.UserId, slot = 4 })
		local toStorage = ItemRegistry.Transition(uid, "Stored", { owner = A.UserId })
		check(not toShowcase and not toStorage, "реестр разрешил переход в чужой музей")
		check(ItemRegistry.GetCarriedBy(B) == uid, "предмет ушёл из рук B")
	end
)

test(
	"Повторный вход A при B: экспонаты, хранилище и монеты на месте, без дублей",
	function(A, B, ctx)
		local shown = displayOwn(ctx, A, 2)
		local stored = displayOwn(ctx, A, 3)
		local plotA = plotOf(A)
		near(A, plotA.showcases[3])
		InventoryService.Handlers.StoreDisplayed(A, plotA, 3)
		check(ItemRegistry.Get(stored).state == "Stored", "A не убрал экспонат в хранилище")
		DataService.AddCoins(A, 777)
		local ownB = displayOwn(ctx, B, 1)
		local userId = A.UserId
		leave(A)
		check(
			ItemRegistry.Get(shown) == nil and ItemRegistry.Get(stored) == nil,
			"экспонаты A остались в реестре"
		)
		check(countUid(shown) == 0, "экспонат A остался в мире")
		check(ItemRegistry.Get(ownB).state == "Displayed", "экспонат B пропал после выхода A")
		local again = TestPlayer.new("Тест_A_снова")
		again.UserId = userId
		ctx.track(again)
		check(join(again), "A не вошёл повторно")
		local entry = ItemRegistry.Get(shown)
		check(
			entry and entry.state == "Displayed" and entry.slot == 2,
			"экспонат A не восстановлен на витрине 2"
		)
		check(
			ItemRegistry.Get(stored) and ItemRegistry.Get(stored).state == "Stored",
			"хранилище A не восстановлено"
		)
		check(DataService.GetData(again).coins == 777, "монеты A не сохранились")
		check(again:GetAttribute("StorageCount") == 1, "StorageCount A")
		check(countUid(shown) == 1 and countUid(stored) == 0, "дубли экспонатов A")
		check(#plotOf(again).exhibits:GetChildren() == 1, "лишние экспонаты на участке A")
		check(
			ItemRegistry.Get(ownB).state == "Displayed" and countUid(ownB) == 1,
			"экспонат B изменился"
		)
	end
)

test(
	"Перестройка музея A (уровни 5, 10, 1) не трогает экспонаты A и B",
	function(A, B, ctx)
		local a1 = displayOwn(ctx, A, 1)
		local a5 = displayOwn(ctx, A, 5)
		local b2 = displayOwn(ctx, B, 2)
		local plotA, plotB = plotOf(A), plotOf(B)
		local buildingB = plotB.model:FindFirstChild("Building")
		for _, level in { 5, 10, 1 } do
			PlotService.ShowLevel(plotA, level)
			local buildings = 0
			for _, child in plotA.model:GetChildren() do
				if child.Name == "Building" then
					buildings += 1
				end
			end
			check(buildings == 1, ("уровень %d: зданий A %d"):format(level, buildings))
			check(
				#plotA.exhibits:GetChildren() == 2,
				("уровень %d: экспонатов A не 2"):format(level)
			)
			check(
				countUid(a1) == 1 and countUid(a5) == 1,
				("уровень %d: дубли или потери у A"):format(level)
			)
			check(
				plotA.showcases[1]:GetAttribute("Occupied") and plotA.showcases[5]:GetAttribute("Occupied"),
				"витрины A"
			)
			check(plotB.model:FindFirstChild("Building") == buildingB, "здание B перестроилось")
			check(#plotB.exhibits:GetChildren() == 1 and countUid(b2) == 1, "экспонаты B изменились")
		end
	end
)

test(
	"Когда свободных участков нет, новый игрок не получает чужой",
	function(_A, _B, ctx)
		local free = 0
		for _, plot in PlotService.GetPlots() do
			if plot.owner == nil then
				free += 1
			end
		end
		for i = 1, free do
			local extra = TestPlayer.new("Тест_X" .. i)
			ctx.track(extra)
			check(join(extra), "свободный участок не выдан")
		end
		local late = TestPlayer.new("Тест_лишний")
		ctx.track(late)
		check(join(late) == false and late.kicked ~= nil, "лишний игрок не получил отказ")
		check(PlotService.GetPlotOf(late) == nil, "лишний игрок получил участок")
	end
)

-- ── Время и ночь (этап 2 D37) ──────────────────────────────────────────────────────────────────────────

test("Время: фазы на границах круга", function()
	local length = GameTime.CycleLength()
	check(length == 3360, "длина круга " .. length)
	local base = GameConfig.Time.Epoch + 123 * length -- любой круг: расписание одинаково
	local cases = {
		{ 0, "Day", 1 },
		{ 299.9, "Day", 1 },
		{ 300, "Night", 1 },
		{ 329.9, "Night", 1 },
		{ 330, "Day", 2 },
		{ 2969.9, "Night", 9 },
		{ 2970, "Day", 10 },
		{ 3149.9, "Day", 10 },
		{ 3150, "Preparation", 10 },
		{ 3269.9, "Preparation", 10 },
		{ 3270, "DoomNight", 10 },
		{ 3359.9, "DoomNight", 10 },
		{ 3360, "Day", 1 },
	}
	for _, case in cases do
		local state = GameTime.At(base + case[1])
		check(
			state.phase == case[2] and state.day == case[3],
			("t=%s: %s день %d, ждали %s день %d"):format(
				case[1],
				state.phase,
				state.day,
				case[2],
				case[3]
			)
		)
	end
	check(GameTime.At(base + 3360).cycle == 124, "новый круг не начался")
end)

test(
	"Время: полный круг шагом 0.1 с — порядок и длительность фаз",
	function()
		local base = GameConfig.Time.Epoch + 77 * GameTime.CycleLength()
		local order, lengths = {}, {}
		local last: string? = nil
		for i = 0, 33599 do
			local state = GameTime.At(base + i / 10)
			local key = state.phase .. state.day
			if key ~= last then
				last = key
				table.insert(order, state.phase)
				table.insert(lengths, state.endsAt - state.startsAt)
			end
		end
		local expected = {}
		for _ = 1, 9 do
			table.insert(expected, "Day")
			table.insert(expected, "Night")
		end
		for _, phase in { "Day", "Preparation", "DoomNight" } do
			table.insert(expected, phase)
		end
		check(
			table.concat(order, ",") == table.concat(expected, ","),
			"порядок фаз: " .. table.concat(order, ",")
		)
		local want = { Day = 300, Night = 30, Preparation = 120, DoomNight = 90 }
		for i, phase in order do
			local need = if phase == "Day" and i == #order - 2 then 180 else want[phase]
			check(math.abs(lengths[i] - need) < 1e-6, ("%s №%d длится %s"):format(phase, i, lengths[i]))
		end
	end
)

test(
	"Время: сервер публикует ту же фазу, что считает общая функция",
	function()
		TimeService.Update()
		local state = GameTime.Current()
		check(ReplicatedStorage:GetAttribute("Phase") == state.phase, "атрибут Phase")
		check(ReplicatedStorage:GetAttribute("Day") == state.day, "атрибут Day")
		check(ReplicatedStorage:GetAttribute("PhaseEndsAt") == state.endsAt, "атрибут PhaseEndsAt")
	end
)

test(
	"Ночь: не успел до Safe Zone — предмет потерян и перенос; успел — предмет при нём",
	function(A, B, ctx)
		local corridor = Vector3.new(10, MapLayout.Heights.Path + 3, MapLayout.ZoneStartZ(1) - 40)
		A:MoveTo(corridor)
		local uidA = carry(ctx, A)
		local safe = MapLayout.Spawn.position + Vector3.new(20, 3, 20)
		B:MoveTo(safe)
		local uidB = carry(ctx, B)
		local bPosition = B.Character.PrimaryPart.Position
		local day = GameTime.At(GameConfig.Time.Epoch)
		local nightState = GameTime.At(GameConfig.Time.Epoch + GameConfig.Time.DayLength)
		NightService.Handlers.Apply(nightState, day, { A, B })
		check(not MapLayout.InDangerZone(A.Character.PrimaryPart.Position), "A остался в коридоре")
		check(
			(A.Character.PrimaryPart.Position - MapLayout.Spawn.position).Magnitude < 20,
			"A не у места появления"
		)
		check(
			ItemRegistry.Get(uidA) == nil and ItemRegistry.GetCarriedBy(A) == nil,
			"предмет A (вне Safe Zone) не потерян"
		)
		check(A:WasNotified("предмет потерян"), "нет сообщения о потере")
		check(ItemRegistry.GetCarriedBy(B) == uidB, "предмет B (в Safe Zone) потерян")
		check((B.Character.PrimaryPart.Position - bPosition).Magnitude < 0.01, "B в Safe Zone перенесли")
		-- B выставляет сохранённый предмет уже ночью.
		local plotB = plotOf(B)
		near(B, plotB.showcases[1])
		MuseumService.Handlers.Display(B, plotB, 1)
		check(
			ItemRegistry.Get(uidB).state == "Displayed",
			"B не смог выставить предмет после наступления ночи"
		)
		check(NightService.Handlers.Barrier().Parent ~= nil, "барьер не поставлен")
		A:MoveTo(corridor)
		check(
			NightService.Handlers.Sweep({ A }) == 1,
			"зашедшего ночью в коридор не вывели"
		)
		NightService.Handlers.Apply(GameTime.At(GameConfig.Time.Epoch + 330), nightState, { A, B })
		check(NightService.Handlers.Barrier().Parent == nil, "барьер не убран на рассвете")
		-- вернуть правила текущей фазы
		NightService.Handlers.Apply(TimeService.Current(), nil, {})
	end
)

-- ── Предметы у боссов (этап 3 D37) ────────────────────────────────────────────────────────────────────

local function bossSlots()
	return BossLootService.Handlers.Slots()
end

-- Днём, чтобы забрать предмет: если сейчас ночь или до неё меньше полутора минут (бой не должен застать ночь),
-- перейти к началу дня (и вернуть часы после теста).
local function ensureDay(): boolean
	local state = TimeService.Current()
	if GameTime.IsNight(state.phase) or state.endsAt - GameTime.Now() < 90 then
		TimeService.SkipTo("Day", 0)
		task.wait(0.3)
		return true
	end
	return false
end

test(
	"Коллекции: босс 1 — 8/8/4, босс 2 и 3 — 12/10/8, босс 4 — 12/9/6/3 с доходом; у черновых нет лишних редкостей",
	function()
		for id, def in Items do
			check(table.find(Rarities.Order, def.rarity), id .. ": редкость " .. tostring(def.rarity))
			check(def.boss >= 1 and def.boss <= #GameConfig.Zones, id .. ": босс " .. tostring(def.boss))
		end
		-- D40 и D42; у босса 2 модели появятся после импорта мешей (до него — заготовки цвета и размера модели).
		local wants = {
			[1] = { Common = 8, Rare = 8, Epic = 4, Legendary = 0, Secret = 0 },
			[2] = { Common = 12, Rare = 10, Epic = 8, Legendary = 0, Secret = 0 },
			[3] = { Common = 12, Rare = 10, Epic = 8, Legendary = 0, Secret = 0 }, -- D54 / D55: 30 существ
			[4] = { Common = 12, Rare = 9, Epic = 6, Legendary = 3, Secret = 0 }, -- D57: 30 существ Пустыни
		}
		for boss = 1, #GameConfig.Zones do
			local want = wants[boss]
			local chances = BossLootService.Chances(boss)
			for _, rarity in Rarities.Order do
				local count = 0
				for id, def in Items do
					if def.boss == boss and def.rarity == rarity and not def.legacy then
						count += 1
						if want then
							check((def.income or 0) > 0, id .. ": нет дохода")
						end
						if boss == 1 then
							check(ItemModels.Models[id], id .. ": нет модели в ItemModels")
						end
					end
				end
				if want then
					check(
						count == want[rarity],
						("босс %d: %s %d, нужно %d"):format(boss, rarity, count, want[rarity])
					)
				elseif (chances[rarity] or 0) == 0 then
					check(count == 0, ("босс %d: %s ему недоступна"):format(boss, rarity))
				end
			end
		end
	end
)

test(
	"Шансы: Legendary только у боссов 4–10, Secret — 8–10; частоты как в таблице",
	function()
		for boss = 1, #GameConfig.Zones do
			local chances = BossLootService.Chances(boss)
			check(((chances.Legendary or 0) > 0) == (boss >= 4), ("босс %d: Legendary"):format(boss))
			check(((chances.Secret or 0) > 0) == (boss >= 8), ("босс %d: Secret"):format(boss))
		end
		local rng = Random.new(37)
		local n = 200000
		for _, tier in GameConfig.Progression.BossLoot.Tiers do
			local total = 0
			for _, chance in tier.chances do
				total += chance
			end
			check(
				math.abs(total - 100) < 1e-9,
				("боссы %d–%d: сумма шансов %s"):format(tier.from, tier.to, total)
			)
			local counts = {}
			for _ = 1, n do
				local rarity = BossLootService.RollRarity(tier.from, rng)
				counts[rarity] = (counts[rarity] or 0) + 1
			end
			for _, rarity in Rarities.Order do
				local got = (counts[rarity] or 0) / n * 100
				local want = tier.chances[rarity] or 0
				local ok = if want == 0 then got == 0 else math.abs(got - want) < 0.3
				check(
					ok,
					("боссы %d–%d: %s %.2f%%, ждали %s%%"):format(tier.from, tier.to, rarity, got, want)
				)
			end
		end
	end
)

test("Слоты: у каждого из 10 боссов 4 предмета из его коллекции", function()
	BossLootService.Handlers.Refresh()
	local slots = bossSlots()
	for boss = 1, #GameConfig.Zones do
		for slot = 1, GameConfig.Progression.BossLoot.Slots do
			local uid = slots[boss][slot].uid
			local entry = uid and ItemRegistry.Get(uid)
			check(entry and entry.state == "AtBoss", ("босс %d слот %d пуст"):format(boss, slot))
			check(
				entry.boss == boss and entry.bossSlot == slot,
				("босс %d слот %d: чужие данные"):format(boss, slot)
			)
			local own = Items[entry.itemId].boss == boss
			check(
				own,
				("босс %d: предмет %s не из его коллекции"):format(boss, entry.itemId)
			)
		end
	end
end)

test(
	"Рассвет: все 40 предметов заменяются новыми uid, старые удалены, дублей нет",
	function()
		local seen = {}
		local previous = {}
		for round = 1, 25 do
			BossLootService.Handlers.Refresh()
			local current = {}
			for boss, bySlot in bossSlots() do
				for slot, entry in bySlot do
					check(
						entry.uid,
						("обновление %d: босс %d слот %d пуст"):format(round, boss, slot)
					)
					check(not seen[entry.uid], "uid повторился: " .. entry.uid)
					seen[entry.uid] = true
					table.insert(current, entry.uid)
				end
			end
			check(#current == 40, ("обновление %d: предметов %d"):format(round, #current))
			for _, old in previous do
				check(ItemRegistry.Get(old) == nil, "старый предмет остался в реестре")
				check(countUid(old) == 0, "старый предмет остался в мире")
			end
			previous = current
		end
	end
)

-- ── Босс 1: модели, автобой, доход, полный путь (D40) ────────────────────────────────────────────────────────

local function waitUntil(condition: () -> boolean, timeout: number): boolean
	local started = os.clock()
	while not condition() do
		if os.clock() - started > timeout then
			return false
		end
		task.wait(0.1)
	end
	return true
end

-- Босс зоны zone дома, спит или засыпает, подсказки открыты (после прошлого боя).
local function waitBossHome(zone: number): boolean
	local boss = BossService.Get(zone) :: BossService.Boss
	return waitUntil(function()
		return BossLootService.IsOpen(zone)
			and not BattleService.Handlers.IsReturning(zone)
			and (boss.state == "Sleep" or boss.state == "FallAsleep")
	end, 45)
end

local function waitDogHome(): boolean
	return waitBossHome(1)
end

-- Начало боя за слот slot босса zone (по умолчанию пса): день, босс дома, свежие предметы; игрок у предмета.
local function prepareFight(player: any, slot: number, zone: number?): (string, BasePart)
	local boss = zone or 1
	ensureDay()
	check(
		waitBossHome(boss),
		("босс %d не вернулся на место после прошлого боя"):format(boss)
	)
	BossLootService.Handlers.Refresh()
	local uid, part = BossLootService.SlotItem(boss, slot)
	check(uid and part, "слот пуст")
	player:MoveTo((part :: BasePart).Position + Vector3.new(0, 0, 4))
	return uid :: string, part :: BasePart
end

local function fightTo(fight: any, timeout: number): boolean
	return waitUntil(function()
		return not fight.active
	end, timeout)
end

test(
	"Модели: у всех 20 предметов и 16 частей пса загружены настоящие меши (импорт FBX)",
	function()
		local missing = {}
		for id, def in Items do
			if def.boss == 1 and not def.legacy and not ItemFactory.HasModel(id) then
				table.insert(missing, id)
			end
		end
		local dog = BossModels[1]
		local parts = 0
		for _, name in Boss1DogRig.Order do
			if dog.meshes[name] then
				parts += 1
			end
		end
		check(
			#missing == 0,
			("нет мешей у %d предметов: %s"):format(#missing, table.concat(missing, ", "))
		)
		check(parts == #Boss1DogRig.Order, ("у пса мешей %d из %d"):format(parts, #Boss1DogRig.Order))
	end
)

test(
	"Сила: урон и HP растут с силой, частота ударов от силы не зависит",
	function()
		local hp0, dmg0 = BattleService.PlayerStats(0)
		local hp1, dmg1 = BattleService.PlayerStats(100)
		local hp2, dmg2 = BattleService.PlayerStats(1e6)
		check(hp0 == Battle.Player.BaseHP and dmg0 == Battle.Player.BaseDamage, "базовые HP и урон")
		check(hp1 > hp0 and dmg1 > dmg0 and hp2 > hp1 and dmg2 > dmg1, "HP и урон не растут с силой")
		check(type(Battle.Player.AttackInterval) == "number", "интервал ударов не число")
		local bossHp, bossDmg = BattleService.BossStats(1)
		check(bossHp > 0 and bossDmg > 0, "у босса 1 нет HP или урона")
	end
)

test(
	"Бой с псом (сила 50): проснулся, HP падают, победа — предмет в руках, соседние на месте, пёс уснул дома",
	function(A)
		DataService.AddStrength(A, 50)
		local uid = prepareFight(A, 2)
		local others = {}
		for slot = 1, 4 do
			if slot ~= 2 then
				others[slot] = BossLootService.SlotItem(1, slot)
			end
		end
		local boss = BossService.Get(1) :: BossService.Boss
		local fight = BattleService.Handlers.Begin(A, 1, 2)
		check(fight, "бой не начался: " .. table.concat(A:Notices(), "; "))
		check(boss.state == "Wake", "пёс не просыпается: " .. boss.state)
		check(
			not BossLootService.IsOpen(1),
			"подсказки у занятого босса не выключены"
		)
		local sawCombat = false
		check(
			waitUntil(function()
				sawCombat = sawCombat or boss.state == "Combat"
				return not fight.active
			end, 60),
			"бой не закончился за минуту"
		)
		check(sawCombat, "пёс не встал в боевую стойку")
		check(
			fight.result == "win",
			"результат " .. tostring(fight.result) .. ": " .. table.concat(fight.log, ", ")
		)
		check(fight.bossHp <= 0, "HP босса не дошло до нуля")
		check(ItemRegistry.GetCarriedBy(A) == uid, "предмет не у победителя")
		check(BossLootService.SlotItem(1, 2) == nil, "слот не опустел")
		for slot, other in others do
			check(
				BossLootService.SlotItem(1, slot) == other,
				("соседний слот %d тронут"):format(slot)
			)
		end
		check(
			waitUntil(function()
				return boss.state == "Sleep"
			end, 45),
			"пёс не уснул: " .. boss.state
		)
		check(
			BossService.DistanceHome(boss) <= Battle.ArriveDistance + 0.5,
			"пёс уснул не на своём месте"
		)
		check(BossLootService.IsOpen(1), "подсказки не открылись после возвращения")
		TimeService.ResetClock()
	end
)

test(
	"Бой при силе 0: удары по-настоящему, HP у обоих уменьшаются, исход — по ударам",
	function(A)
		prepareFight(A, 3)
		local fight = BattleService.Handlers.Begin(A, 1, 3)
		check(fight, "бой не начался: " .. table.concat(A:Notices(), "; "))
		local started = os.clock()
		check(fightTo(fight, 90), "бой не закончился за 90 с")
		local took = os.clock() - started
		local playerHits, bossHits = 0, 0
		for _, line in fight.log do
			if line:find("игрок") then
				playerHits += 1
			elseif line:find("босс −") then
				bossHits += 1
			end
		end
		check(fight.result == "win" or fight.result == "lose", "результат " .. tostring(fight.result))
		check(
			playerHits >= 3 and bossHits >= 1,
			("ударов игрока %d, босса %d"):format(playerHits, bossHits)
		)
		check(took > 5, ("бой длился %.1f с — слишком быстро для силы 0"):format(took))
		if ItemRegistry.GetCarriedBy(A) then
			CarryService.LoseCarried(A, "уборка после теста")
		end
		TimeService.ResetClock()
	end
)

test(
	"Поражение: отброс без телепорта, предмет на постаменте, пёс засыпает, новый бой — сразу",
	function(A)
		local uid = prepareFight(A, 1)
		local cfg = Battle.Bosses[1]
		local saved = cfg.Damage
		cfg.Damage = 1e6 -- первый же укус
		local before = A.Character.PrimaryPart.Position
		local fight = BattleService.Handlers.Begin(A, 1, 1)
		local ok = fight ~= nil and fightTo(fight, 30)
		cfg.Damage = saved
		check(ok, "бой не начался или не закончился")
		check(fight.result == "lose", "результат " .. tostring(fight.result))
		check(A:GetAttribute("KnockedAt") ~= nil, "проигравшего не отбросило")
		check(
			(A.Character.PrimaryPart.Position - before).Magnitude < 0.01,
			"проигравшего телепортировали"
		)
		check(BossLootService.SlotItem(1, 1) == uid, "предмет не вернулся на постамент")
		check(
			ItemRegistry.Get(uid).state == "AtBoss" and ItemRegistry.GetCarriedBy(A) == nil,
			"предмет у проигравшего"
		)
		check(waitDogHome(), "пёс не вернулся и не лёг")
		local again = BattleService.Handlers.Begin(A, 1, 1)
		check(again, "новый бой не начался сразу: " .. table.concat(A:Notices(), "; "))
		BattleService.Handlers.Finish(again, "abort")
		check(waitDogHome(), "пёс не вернулся после второго боя")
		TimeService.ResetClock()
	end
)

test(
	"Один бой на босса: второй игрок не начнёт бой и не заберёт предмет занятого пса",
	function(A, B)
		prepareFight(A, 1)
		local uidB, partB = BossLootService.SlotItem(1, 3)
		B:MoveTo((partB :: BasePart).Position + Vector3.new(0, 0, 4))
		local fight = BattleService.Handlers.Begin(A, 1, 1)
		check(fight, "бой A не начался")
		B:ClearSent()
		BossLootService.Handlers.Take(B, 1, 3)
		local second = BattleService.Handlers.Begin(B, 1, 3)
		local busyNoticed = B:WasNotified("занят")
		local untouched = BossLootService.SlotItem(1, 3) == uidB and ItemRegistry.GetCarriedBy(B) == nil
		BattleService.Handlers.Finish(fight, "abort")
		check(second == nil, "второй бой с тем же боссом начался")
		check(busyNoticed, "B не сообщили, что босс занят")
		check(untouched, "B забрал предмет занятого босса")
		check(waitDogHome(), "пёс не вернулся")
		TimeService.ResetClock()
	end
)

test(
	"Ночь прерывает бой (предмет у пса, на рассвете — новый); отойти от пса — не побег (D49)",
	function(A)
		local uid = prepareFight(A, 4)
		local fight = BattleService.Handlers.Begin(A, 1, 4)
		check(fight, "бой не начался")
		TimeService.SkipTo("Night", 0)
		local ended = fightTo(fight, 5)
		local keptAtNight = BossLootService.SlotItem(1, 4) == uid and ItemRegistry.GetCarriedBy(A) == nil
		TimeService.SkipTo("Day", 0) -- рассвет: все 4 слота обновляются (D37)
		task.wait(0.3)
		local refreshed = BossLootService.SlotItem(1, 4)
		check(ended and fight.result == "night", "ночь не прервала бой: " .. tostring(fight.result))
		check(keptAtNight, "ночью предмет ушёл от пса")
		check(refreshed and refreshed ~= uid, "на рассвете слот не обновился")
		prepareFight(A, 4)
		local stay = BattleService.Handlers.Begin(A, 1, 4)
		check(stay, "второй бой не начался")
		local home = (BossService.Get(1) :: BossService.Boss).home.Position
		A:MoveTo(home + Vector3.new(0, 3, -(Battle.Bosses[1].Leash + 6)))
		local stopped = fightTo(stay, 2)
		BattleService.Handlers.Finish(stay, "abort")
		check(
			not stopped,
			"бой закончился, когда боец отошёл от пса: " .. tostring(stay.result)
		)
		check(waitDogHome(), "пёс не вернулся")
		TimeService.ResetClock()
	end
)

-- D49: боец заперт в зоне босса до конца боя (стены только для него), HP бойца — в здоровье персонажа ─────────────

test(
	"D49: боец заперт в зоне босса, стены только для него; HP — в здоровье персонажа, полоска только у босса",
	function(A, B)
		prepareFight(A, 2)
		local humanoid = A.Character:FindFirstChildOfClass("Humanoid") :: Humanoid
		local savedMax = humanoid.MaxHealth
		local fight = BattleService.Handlers.Begin(A, 1, 2)
		check(fight, "бой не начался")
		local ok, err = pcall(function()
			local Fighter, Lock = CharacterGroups.Fighter, CharacterGroups.ZoneLock
			check(CharacterGroups.GroupOf(A) == Fighter, "боец не в группе стен зоны")
			check(
				A.Character.HumanoidRootPart.CollisionGroup == Fighter,
				"детали бойца не в группе стен"
			)
			check(CharacterGroups.GroupOf(B) ~= Fighter, "посторонний в группе стен")
			check(PhysicsService:CollisionGroupsAreCollidable(Fighter, Lock), "стены не держат бойца")
			check(not PhysicsService:CollisionGroupsAreCollidable("Default", Lock), "стены держат всех")
			check(
				not PhysicsService:CollisionGroupsAreCollidable(CharacterGroups.VaultOwner(plotOf(B).index), Lock),
				"стены держат владельцев музеев"
			)
			local walls = workspace:FindFirstChild("World") and workspace.World:FindFirstChild("BattleWalls")
			check(
				walls and walls:FindFirstChild("ZoneWall_1") and walls:FindFirstChild("ZoneWall_2"),
				"нет стен зоны 1"
			)
			check(
				A.Character.HumanoidRootPart:FindFirstChild("BattleBar") == nil,
				"полоска HP над бойцом"
			)
			check(
				(BossService.Get(1) :: BossService.Boss).root:FindFirstChild("BattleBar") ~= nil,
				"нет полоски над боссом"
			)
			check(
				math.abs(humanoid.MaxHealth - fight.maxHp) < 0.01,
				"здоровье персонажа — не HP боя"
			)
			-- вышел из зоны (телепорт в безопасную зону) — назад в зону, бой идёт
			local z0, z1 = BattleService.Handlers.ZoneBounds(1)
			A.Character.HumanoidRootPart.CFrame = CFrame.new(0, 5, z1 + 20)
			BattleService.Handlers.Step(fight)
			local z = A.Character.HumanoidRootPart.Position.Z
			check(z > z0 and z < z1, ("бойца не вернули в зону: z %.1f"):format(z))
			check(fight.active, "бой закончился после выхода из зоны")
		end)
		BattleService.Handlers.Finish(fight, "abort")
		check(ok, tostring(err))
		check(
			CharacterGroups.GroupOf(A) ~= CharacterGroups.Fighter,
			"после боя боец всё ещё в группе стен"
		)
		check(
			A.Character.HumanoidRootPart.CollisionGroup == CharacterGroups.GroupOf(A),
			"после боя группа деталей прежняя"
		)
		check(
			math.abs(humanoid.MaxHealth - savedMax) < 0.01 and humanoid.Health > 0,
			"здоровье после боя не вернулось"
		)
		check(waitDogHome(), "пёс не вернулся")
		TimeService.ResetClock()
	end
)

-- ── Босс 2 «Торговец-громила»: площадка и бой (D42, D43) ─────────────────────────────────────────────────────

test(
	"Торговец: модель из 12 частей на Motor6D; предметы на площадке без постаментов, у каждого свой поворот",
	function()
		local boss = BossService.Get(2)
		check(boss, "у зоны 2 нет босса")
		local trader = boss :: BossService.Boss
		check(
			trader.model:GetAttribute("BossName") == GameConfig.Zones[2].boss,
			"имя босса не совпадает с зоной"
		)
		local joints = 0
		for _, name in Boss2TraderRig.Order do
			local part = trader.model:FindFirstChild(name)
			local joint = part and part:FindFirstChild(name)
			if joint and joint:IsA("Motor6D") then
				joints += 1
			end
		end
		check(joints == #Boss2TraderRig.Order, ("суставов %d из %d"):format(joints, #Boss2TraderRig.Order))
		check(
			(trader.home.Position - BossService.HomeOf(2).Position).Magnitude < 0.01,
			"торговец не на своём месте"
		)

		BossLootService.Handlers.Refresh()
		local arena = MapLayout.Arenas[2]
		local floorY = MapLayout.ZoneCFrame(2).Position.Y + arena.top
		local looks = {}
		for slot = 1, 4 do
			local uid, part = BossLootService.SlotItem(2, slot)
			check(uid and part, ("слот %d пуст"):format(slot))
			local item = part :: BasePart
			local bottom = item.Position.Y - item.Size.Y / 2
			local message = ("слот %d: низ предмета %.2f, площадка %.2f"):format(
				slot,
				bottom,
				floorY
			)
			check(math.abs(bottom - floorY) < 0.05, message)
			for _, other in looks do
				check(
					item.CFrame.LookVector:Dot(other) < 0.99,
					("слот %d повёрнут как другой"):format(slot)
				)
			end
			table.insert(looks, item.CFrame.LookVector)
		end
		local zones = { workspace:FindFirstChild("Zone1_Junk", true), workspace:FindFirstChild("Zone2_Flea", true) }
		check(zones[1] and zones[2], "нет папок зон 1 и 2")
		local pedestals = { 0, 0 }
		for zone, folder in zones do
			for _, child in (folder :: Instance):GetChildren() do
				if child.Name:sub(1, 9) == "Pedestal_" then
					pedestals[zone] += 1
				end
			end
		end
		local counted = ("постаментов: у пса %d, у торговца %d"):format(
			pedestals[1],
			pedestals[2]
		)
		check(pedestals[1] == 4 and pedestals[2] == 0, counted)
	end
)

test(
	"Бой с торговцем: при силе 0 — поражение, при силе 1000 — победа; имя в сообщениях, полоска HP над головой",
	function(A)
		local uid = prepareFight(A, 1, 2)
		local boss = BossService.Get(2) :: BossService.Boss
		local name = GameConfig.Zones[2].boss
		A:ClearSent()
		local fight = BattleService.Handlers.Begin(A, 2, 1)
		check(fight, "бой не начался: " .. table.concat(A:Notices(), "; "))
		check(
			A:WasNotified(name .. " проснулся"),
			"нет сообщения с именем торговца"
		)
		local bar = boss.root:FindFirstChild("BattleBar") :: BillboardGui?
		check(
			bar and bar.StudsOffsetWorldSpace.Y > BossService.Height(boss),
			"полоска HP не над головой торговца"
		)
		check(fightTo(fight, 60), "бой не закончился за минуту")
		check(
			fight.result == "lose",
			"при силе 0 торговец должен победить: " .. tostring(fight.result)
		)
		check(A:WasNotified(name .. " победил"), "нет сообщения о победе торговца")
		check(
			BossLootService.SlotItem(2, 1) == uid and ItemRegistry.GetCarriedBy(A) == nil,
			"предмет ушёл с площадки"
		)
		check(waitBossHome(2), "торговец не вернулся и не лёг")
		DataService.AddStrength(A, 1000)
		prepareFight(A, 2, 2)
		local win = BattleService.Handlers.Begin(A, 2, 2)
		check(win and fightTo(win, 60), "второй бой не начался или не закончился")
		check(win.result == "win", "при силе 1000 бой не выигран: " .. tostring(win.result))
		local carried = ItemRegistry.GetCarriedBy(A)
		check(carried and ItemRegistry.Get(carried).boss == 2, "добыча торговца не в руках")
		CarryService.LoseCarried(A, "уборка после теста")
		check(waitBossHome(2), "торговец не вернулся после поражения")
		TimeService.ResetClock()
	end
)

-- Босс 4 «Сфинкс-лежебока» (интеграция 2026-11-12): выпады с отметками атрибутов модели в момент выпада.
type Swing = { kind: string, at: number, planned: number?, planBefore: number?, dist: number, canceled: boolean }
local function watchSwings(boss: BossService.Boss, fight: any): { Swing }
	local swings: { Swing } = {}
	local lastSeq = boss.model:GetAttribute("AttackSeq") or 0
	local planBefore = boss.model:GetAttribute("PlanAt")
	local cancelSeen = false
	local conn
	conn = boss.model:GetAttributeChangedSignal("AttackSeq"):Connect(function()
		local seq = boss.model:GetAttribute("AttackSeq") or 0
		if seq ~= lastSeq + 1 then
			lastSeq = seq
			return
		end
		lastSeq = seq
		local root = fight.player.Character and fight.player.Character:FindFirstChild("HumanoidRootPart")
		local flat = if root then (root.Position - boss.root.Position) * Vector3.new(1, 0, 1) else Vector3.zero
		table.insert(swings, {
			kind = boss.model:GetAttribute("AttackKind"),
			at = boss.model:GetAttribute("AttackAt"),
			planned = boss.model:GetAttribute("AttackPlanAt"),
			planBefore = planBefore,
			dist = flat.Magnitude,
			canceled = cancelSeen,
		})
		cancelSeen = false
	end)
	local planConn = boss.model:GetAttributeChangedSignal("PlanAt"):Connect(function()
		planBefore = boss.model:GetAttribute("PlanAt")
	end)
	local cancelConn = boss.model:GetAttributeChangedSignal("PlanCancelAt"):Connect(function()
		cancelSeen = cancelSeen or boss.model:GetAttribute("PlanCancelAt") ~= nil
	end)
	task.spawn(function()
		while fight.active do
			task.wait(0.1)
		end
		conn:Disconnect()
		planConn:Disconnect()
		cancelConn:Disconnect()
	end)
	return swings
end

test(
	"Босс 4: Сфинкс на карте (открыт с коллекцией, D59), 27 частей на суставах, клипы; числа боя прежние, сила 150 000",
	function()
		local boss = BossService.Get(4)
		check(BossService.ClosedAllowed(), "тесты идут не в Studio с DevMode")
		check(boss ~= nil, "босса 4 нет на карте в Studio")
		if not boss then
			return
		end
		local rig = require(ReplicatedStorage.Shared.Config.Boss4SphinxRig) :: any
		local joints = 0
		for _, name in rig.Order do
			local part = boss.model:FindFirstChild(name)
			local joint = part and part:FindFirstChild(name)
			if joint and joint:IsA("Motor6D") then
				joints += 1
			end
		end
		check(#rig.Order == 27 and joints == 27, ("суставов %d из %d"):format(joints, #rig.Order))
		check(BossService.HasClips(boss), "у Сфинкса нет клипов")
		for zone = 1, 3 do
			local other = BossService.Get(zone) :: BossService.Boss
			check(not BossService.HasClips(other), ("у босса %d появились клипы"):format(zone))
		end
		check(Battle.Bosses[4].Closed ~= true, "босс 4 закрыт, хотя коллекция есть (D59)")
		local cfg, base = Battle.Bosses[4], Battle.Bosses[3]
		for _, key in { "HP", "Damage", "AttackInterval", "AttackRange", "Leash", "Speed" } do
			check(
				cfg[key] == base[key],
				("%s босса 4 %s, у боссов 1–3 %s"):format(key, tostring(cfg[key]), tostring(base[key]))
			)
		end
		check(cfg.Strength == 150000, "сила босса 4 " .. tostring(cfg.Strength))
		check(
			BossService.Height(boss) > 14 and BossService.Height(boss) < 19,
			"рост Сфинкса " .. BossService.Height(boss)
		)
		local home = BossService.HomeOf(4)
		check(
			(boss.root.Position - home.Position).Magnitude < 1,
			"Сфинкс не на своём месте в зоне 4"
		)
	end
)

test(
	"Босс 4: бой — замах объявлен заранее, каждый третий «Хвост-кистень», урон один раз за выпад, интервалы прежние",
	function(A, _B, ctx)
		DataService.AddStrength(A, 150000)
		prepareFight(A, 1, 4)
		local boss = BossService.Get(4) :: BossService.Boss
		local fight = BattleService.Handlers.Begin(A, 4, 1)
		check(fight, "бой не начался: " .. table.concat(A:Notices(), "; "))
		if not fight then
			return
		end
		local swings = watchSwings(boss, fight)
		-- первый выпад объявлен в начале ToCombat — запас на задержку сети
		check(
			waitUntil(function()
				return boss.state == "ToCombat"
			end, 5),
			"нет ToCombat"
		)
		task.wait(0.05)
		local planAt, stateAt = boss.model:GetAttribute("PlanAt"), boss.model:GetAttribute("StateAt")
		local ahead = if planAt and stateAt then planAt - stateAt else -1
		check(
			math.abs(ahead - (Battle.Timeline.ToCombat + 0.6 + Battle.AttackPlan.ExpectedDelay)) < 0.05,
			("первый выпад объявлен за %.2f с до него (от начала ToCombat)"):format(
				ahead
			)
		)
		check(boss.model:GetAttribute("PlanKind") == "bite", "первый — не «Тяжёлая лапа»")
		check(fightTo(fight, 90), "бой не закончился")
		check(fight.result == "win", "при силе 150 000 бой не выигран: " .. tostring(fight.result))
		local hits = 0
		for _, line in fight.log do
			if string.find(line, "босс −", 1, true) then
				hits += 1
			end
		end
		check(#swings >= 6, ("выпадов %d"):format(#swings))
		check(
			hits == #swings or hits == #swings - 1,
			("ударов по игроку %d при %d выпадах"):format(hits, #swings)
		)
		local thirds, planned, offs, worst, gaps = true, 0, 0, 0, {}
		local unplanned = {} -- выпад без плана — только после отмены (игрок был вне дальности)
		for i, s in swings do
			thirds = thirds and s.kind == (if i % 3 == 0 then "swipe" else "bite")
			if s.planned then
				planned += 1
				local off = s.at - s.planned
				offs += off
				worst = math.max(worst, math.abs(off))
			else
				table.insert(
					unplanned,
					("№%d (%.1f ст., %s)"):format(
						i,
						s.dist,
						if s.canceled then "план был снят" else "план не снимали"
					)
				)
				check(
					s.canceled,
					("выпад №%d без плана, хотя план не снимали"):format(i)
				)
			end
			if i > 1 then
				table.insert(gaps, s.at - swings[i - 1].at)
			end
		end
		check(thirds, "каждый третий выпад — не «Хвост-кистень»")
		check(
			planned >= #swings - 2,
			("по плану %d выпадов из %d; без плана: %s"):format(
				planned,
				#swings,
				table.concat(unplanned, ", ")
			)
		)
		ctx.note(
			("по плану %d из %d; без плана: %s"):format(
				planned,
				#swings,
				if #unplanned > 0 then table.concat(unplanned, ", ") else "нет"
			)
		)
		ctx.note(
			("выпад позже плана: в среднем %+.3f с, наибольшее %.3f с; ударов по игроку %d"):format(
				offs / math.max(planned, 1),
				worst,
				hits
			)
		)
		check(
			worst < 0.15,
			("выпад позже плана в среднем на %+.3f с, наибольшее расхождение %.3f с"):format(
				offs / math.max(planned, 1),
				worst
			)
		)
		local short = 0
		for _, g in gaps do
			if g < Battle.Bosses[4].AttackInterval - 0.01 then
				short += 1
			end
		end
		check(short == 0, ("выпадов чаще интервала: %d"):format(short))
		CarryService.LoseCarried(A, "уборка после теста")
		check(waitBossHome(4), "Сфинкс не вернулся и не уснул")
		check(
			BossService.DistanceHome(boss) <= Battle.ArriveDistance + 0.5,
			"Сфинкс уснул не на своём месте"
		)
		TimeService.ResetClock()
	end
)

test(
	"Босс 4: поражение при силе 0 посреди выпадов, план отменён; игрок ушёл — план снят, выпад без плана; повторный бой",
	function(A)
		prepareFight(A, 2, 4)
		local boss = BossService.Get(4) :: BossService.Boss
		local fight = BattleService.Handlers.Begin(A, 4, 2)
		check(fight, "бой не начался: " .. table.concat(A:Notices(), "; "))
		if not fight then
			return
		end
		check(fightTo(fight, 60), "бой не закончился")
		check(
			fight.result == "lose",
			"при силе 0 Сфинкс должен победить: " .. tostring(fight.result)
		)
		check(
			boss.state == "Victory",
			"после поражения игрока не победа Сфинкса: " .. boss.state
		)
		local cancel, plan = boss.model:GetAttribute("PlanCancelAt"), boss.model:GetAttribute("PlanAt")
		check(cancel ~= nil and plan ~= nil, "план не отменён в конце боя")
		check(waitBossHome(4), "Сфинкс не вернулся после победы")
		-- второй бой: игрок уходит из дальности — план снимается, вернулся — выпад без плана или с новым планом
		DataService.AddStrength(A, 150000)
		prepareFight(A, 3, 4)
		local again = BattleService.Handlers.Begin(A, 4, 3)
		check(again, "повторный бой не начался")
		if not again then
			return
		end
		local swings = watchSwings(boss, again)
		check(
			waitUntil(function()
				return #swings >= 1
			end, 10),
			"нет первого выпада"
		)
		local root = select(1, A.Character and A.Character:FindFirstChild("HumanoidRootPart")) :: BasePart?
		if root then
			A:MoveTo(root.Position + (root.Position - boss.root.Position).Unit * 9) -- дальше дальности выпада
		end
		check(
			waitUntil(function()
				return boss.model:GetAttribute("PlanCancelAt") ~= nil or not again.active
			end, 3),
			"игрок вне дальности — план не снят"
		)
		check(fightTo(again, 90), "повторный бой не закончился")
		check(again.result == "win", "повторный бой: " .. tostring(again.result))
		CarryService.LoseCarried(A, "уборка после теста")
		check(waitBossHome(4), "Сфинкс не вернулся после повторного боя")
		TimeService.ResetClock()
	end
)

test(
	"Босс 4 в зоне 4: во всех клипах не проваливается, не задевает декор и предметы слотов",
	function(_A, _B, ctx)
		local boss = BossService.Get(4) :: BossService.Boss
		-- настоящая форма — вершины из данных предпросмотра (Tests/MeshFixture, только локально); без них — габариты частей
		local Preview = require(Server.Tests.BossMeshPreview) :: any
		local points: { [string]: { Vector3 } } = {}
		local exact = Preview.Has(4)
		if exact then
			for _, part in (require(ReplicatedStorage.Shared.Config.Boss4SphinxRig) :: any).Order do
				points[part] = Preview.Points(4, part)
			end
		end
		ctx.note(
			if exact
				then "по вершинам мешей (7 916 треугольников)"
				else "по габаритам частей (данных мешей нет)"
		)
		local rig = require(ReplicatedStorage.Shared.Config.Boss4SphinxRig) :: any
		local BossClips = require(ReplicatedStorage.Shared.BossClips) :: any
		local turn = CFrame.Angles(0, math.rad(BossModels[4].turn), 0)
		local home = boss.home
		-- пол под Сфинксом
		local down = workspace:Raycast(
			home.Position + Vector3.new(0, 20, 0),
			Vector3.new(0, -40, 0),
			(function()
				local p = RaycastParams.new()
				p.FilterType = Enum.RaycastFilterType.Exclude
				p.FilterDescendantsInstances = { boss.model }
				return p
			end)()
		)
		local floor = if down then down.Position.Y else home.Y
		check(
			down ~= nil and math.abs(floor - home.Y) < 0.05,
			("пол под Сфинксом на %.2f, место босса на %.2f"):format(floor, home.Y)
		)
		local params = OverlapParams.new()
		params.FilterType = Enum.RaycastFilterType.Exclude
		params.FilterDescendantsInstances = { boss.model }
		local items: { [BasePart]: string } = {}
		for slot = 1, 4 do
			local uid, part = BossLootService.SlotItem(4, slot)
			if uid and part then
				items[part] = uid
			end
		end
		local lowest, lowestAt = math.huge, ""
		local decor: { [string]: { [string]: boolean } } = {} -- «где: деталь» → части и клипы
		local hitItems: { [string]: string } = {}
		local poses = 0
		local function sweep(root: CFrame, names: { string }, label: string)
			for _, name in names do
				local clip = BossClips.Get(rig, name)
				for t = 0, clip.duration, 1 / 15 do
					local pose = BossClips.At(rig, clip, t)
					poses += 1
					local joints = {}
					for _, part in rig.Order do
						local info = rig.Parts[part]
						local transform = pose[part]
						joints[part] = if info.parent
							then joints[info.parent] * CFrame.new(info.pivot - rig.Parts[info.parent].pivot) * transform
							else root * CFrame.new(info.pivot) * transform
						local box = joints[part] * CFrame.new(info.center) * turn
						local corners = {}
						if exact then
							for _, v in points[part] do
								table.insert(corners, joints[part]:PointToWorldSpace(v))
							end
						else
							local half = info.size / 2
							for _, sx in { -1, 1 } do
								for _, sy in { -1, 1 } do
									for _, sz in { -1, 1 } do
										table.insert(corners, box:PointToWorldSpace(half * Vector3.new(sx, sy, sz)))
									end
								end
							end
						end
						for _, c in corners do
							if c.Y < lowest then
								lowest, lowestAt = c.Y, ("%s в %s на %.2f с, %s"):format(part, name, t, label)
							end
						end
						for _, hit in workspace:GetPartBoundsInBox(box, info.size, params) do
							-- верх детали с учётом поворота (у плоского диска площадки Size.Y — диаметр, а не высота)
							local cf, size = hit.CFrame, hit.Size
							local halfY = (
								math.abs(cf.RightVector.Y) * size.X
								+ math.abs(cf.UpVector.Y) * size.Y
								+ math.abs(cf.LookVector.Y) * size.Z
							) / 2
							local solid = hit.CanCollide
								and hit.Transparency < 1
								and hit.Position.Y + halfY > floor + 0.3
							if not (items[hit] or (hit.Parent and items[hit.Parent :: any]) or solid) then
								continue
							end
							-- касание — если вершина части внутри детали (у мешей), иначе — пересечение габаритов
							local inside = not exact
							if exact then
								for _, c in corners do
									local local_ = hit.CFrame:PointToObjectSpace(c)
									local h = hit.Size / 2
									if
										math.abs(local_.X) < h.X
										and math.abs(local_.Y) < h.Y
										and math.abs(local_.Z) < h.Z
									then
										inside = true
										break
									end
								end
							end
							if inside then
								if items[hit] or (hit.Parent and items[hit.Parent :: any]) then
									hitItems[("%s в %s, %s"):format(part, name, label)] = hit:GetFullName()
								else
									local key = ("%s: %s.%s"):format(label, (hit.Parent :: Instance).Name, hit.Name)
									decor[key] = decor[key] or {}
									decor[key][part .. "/" .. name] = true
								end
							end
						end
					end
				end
			end
		end
		-- дома (сон, пробуждение, засыпание — и выпады, если бой начался у места) и в бою у каждого слота: игрок у предмета
		-- (как после поимки), Сфинкс подошёл от своего места на AttackRange − 1.5 и смотрит на него
		sweep(
			home,
			{ "sleep_idle", "wake", "combat_idle", "walk", "hit", "victory", "defeat", "fall_asleep" },
			"дома"
		)
		local atHome = table.clone(decor)
		table.clear(decor)
		sweep(home, { "heavy_paw", "tail_strike" }, "выпад дома")
		local cfg4 = Battle.Bosses[4]
		for slot = 1, 4 do
			local _, part = BossLootService.SlotItem(4, slot)
			if part then
				local at = part.Position + Vector3.new(0, 0, 4)
				local flat = Vector3.new(at.X - home.X, 0, at.Z - home.Z)
				local stop = home.Position
					+ flat.Unit * math.min(math.max(flat.Magnitude - (cfg4.AttackRange - 1.5), 0), cfg4.Leash)
				local root = CFrame.lookAt(stop, Vector3.new(at.X, stop.Y, at.Z)) * CFrame.Angles(0, math.pi, 0)
				sweep(
					root,
					{ "combat_idle", "walk", "heavy_paw", "tail_strike", "hit", "victory", "defeat" },
					"бой у слота " .. slot
				)
			end
		end
		ctx.note(
			("проверено поз: %d; нижняя точка %.2f над полом (%s)"):format(
				poses,
				lowest - floor,
				lowestAt
			)
		)
		check(
			lowest - floor > (if exact then -0.1 else -0.8),
			("часть уходит под пол на %.2f (%s)"):format(floor - lowest, lowestAt)
		)
		local function describe(map: { [string]: { [string]: boolean } }): { string }
			local out = {}
			for key, set in map do
				local parts = {}
				for k in set do
					table.insert(parts, k)
				end
				table.sort(parts)
				table.insert(
					out,
					("%s ← %s%s"):format(
						key,
						table.concat(parts, ", ", 1, math.min(#parts, 4)),
						if #parts > 4 then (" и ещё %d"):format(#parts - 4) else ""
					)
				)
			end
			table.sort(out)
			return out
		end
		local list = describe(atHome)
		check(
			#list == 0,
			("Сфинкс на своём месте задевает декор: %s"):format(table.concat(list, "; "))
		)
		-- выпады дома и бой у слотов зоны 4 (площадки босса 4 ещё нет — постаменты-заготовки D37): что задевается
		local summary = describe(decor)
		ctx.note(
			"в бою задевает: " .. (if #summary > 0 then table.concat(summary, "; ") else "ничего")
		)
		local touched = {}
		for by, what in hitItems do
			table.insert(touched, by .. " → " .. what)
		end
		ctx.note(
			("предметы слотов задеты Сфинксом на месте: %s"):format(
				if #touched > 0 then table.concat(touched, "; ") else "нет"
			)
		)
	end
)

test(
	"Боссы 1–3 без изменений: у них нет атрибутов плана атаки после боёв",
	function()
		for zone = 1, 3 do
			local model = (BossService.Get(zone) :: BossService.Boss).model
			for _, key in { "PlanKind", "PlanAt", "PlanSeq", "PlanCancelAt", "AttackPlanAt" } do
				check(model:GetAttribute(key) == nil, ("у босса %d есть %s"):format(zone, key))
			end
		end
	end
)

test(
	"Доход: свой у каждого экспоната на витрине, сумма в Income, надпись «+X/сек»; в руках и хранилище — 0",
	function(A, B, ctx)
		local moai = displayOwn(ctx, A, 1, "Moai")
		local starry = displayOwn(ctx, A, 2, "StarryNight")
		local m, s = IncomeService.Of("Moai"), IncomeService.Of("StarryNight")
		local coins = DataService.GetData(A).coins
		IncomeService.Handlers.Tick({ A })
		check(DataService.GetData(A).coins == coins + m + s, "за секунду начислено не m + s")
		check(A:GetAttribute("Income") == m + s, "атрибут Income " .. tostring(A:GetAttribute("Income")))
		local label = (ItemRegistry.Get(moai) :: any).part:FindFirstChild("IncomeLabel")
		check(
			label and label.Text.Text == ("+%d/сек"):format(m),
			"нет надписи дохода над экспонатом"
		)
		carry(ctx, A, "TRexSkeleton")
		local plotA = plotOf(A)
		CarryService.LoseCarried(A, "тест")
		near(A, plotA.showcases[2])
		InventoryService.Handlers.StoreDisplayed(A, plotA, 2)
		check(ItemRegistry.Get(starry).state == "Stored", "экспонат не убран в хранилище")
		coins = DataService.GetData(A).coins
		IncomeService.Handlers.Tick({ A })
		check(
			DataService.GetData(A).coins == coins + m,
			"хранилище или руки приносят доход"
		)
		check(A:GetAttribute("Income") == m, "Income не пересчитан после хранилища")
		coins = DataService.GetData(B).coins
		IncomeService.Handlers.Tick({ B })
		check(DataService.GetData(B).coins == coins, "доход A попал B")
	end
)

test(
	"Полный путь: победа → в руках → витрина → доход → повторный вход без дублей",
	function(A, _B, ctx)
		DataService.AddStrength(A, 50)
		local uid = prepareFight(A, 3)
		local fight = BattleService.Handlers.Begin(A, 1, 3)
		check(fight and fightTo(fight, 60) and fight.result == "win", "бой не выигран")
		check(ItemRegistry.GetCarriedBy(A) == uid, "добыча не в руках")
		local itemId = ItemRegistry.Get(uid).itemId
		local plotA = plotOf(A)
		near(A, plotA.showcases[1])
		MuseumService.Handlers.Display(A, plotA, 1)
		check(ItemRegistry.Get(uid).state == "Displayed", "добыча не выставлена")
		local record = DataService.GetData(A).items[uid]
		check(
			record and record.id == itemId and record.boss == 1 and record.source == "boss",
			"запись в профиле неполная"
		)
		local coins = DataService.GetData(A).coins
		IncomeService.Handlers.Tick({ A })
		check(
			DataService.GetData(A).coins == coins + IncomeService.Of(itemId),
			"доход добычи не начислен"
		)
		local userId = A.UserId
		leave(A)
		local again = TestPlayer.new("Тест_A_снова")
		again.UserId = userId
		ctx.track(again)
		check(join(again), "A не вошёл повторно")
		local entry = ItemRegistry.Get(uid)
		check(
			entry and entry.state == "Displayed" and entry.slot == 1 and entry.itemId == itemId,
			"добыча не восстановлена"
		)
		check(countUid(uid) == 1, "дубли добычи после повторного входа")
		local label = (entry :: any).part:FindFirstChild("IncomeLabel")
		check(label ~= nil, "нет надписи дохода после повторного входа")
		coins = DataService.GetData(again).coins
		IncomeService.Handlers.Tick({ again })
		check(
			DataService.GetData(again).coins == coins + IncomeService.Of(itemId),
			"после входа доход не идёт"
		)
		check(waitDogHome(), "пёс не вернулся")
		TimeService.ResetClock()
	end
)

-- ── D48-C: музей на 20 мест, хранилище только владельцу, графика Parts/Mesh ───────────────────────────────────

-- Уровень музея игрока: профиль и здание (как команда DevTools MuseumLevel).
-- D55: у предмета у босса — «Поймать»; бросок в центр существа — попадание, шанс задаёт тест (SetRoll).
local function giveLovibums(player: any, level: number, kind: string, n: number)
	local lovibums = DataService.Lovibums(player) :: any
	local key = "L" .. level
	lovibums[key] = lovibums[key] or {}
	lovibums[key][kind] = (lovibums[key][kind] or 0) + n
end

local function stockOf(player: any, level: number, kind: string): number
	return CatchRules.Stock(DataService.Lovibums(player), level, kind)
end

local CG = GameConfig.Catch.Game

-- Ждать, пока сервер разрешит следующий бросок (полёт и сеть / побег видны всем).
local function waitReady(player: any)
	local a = CatchService.Handlers.Active(player)
	while a and workspace:GetServerTimeNow() < a.session.readyAt + 0.05 do
		task.wait(0.05)
	end
end

-- Жест (как у клиента), который приведёт Ловибум в точку point (на плоскости броска камеры поимки этой мини-игры).
local function gestureTo(a: any, point: Vector3): any
	local look = a.camera.LookVector
	local plane = Vector3.new(look.X, 0, look.Z).Unit
	return CatchThrow.GestureFor(a.camera, point - plane * (point - a.stage):Dot(plane))
end

-- Бросок Ловибума kind жестом: в центр существа в момент прилёта (hit) или мимо кольца; время отпускания — сейчас.
-- Клиент шлёт только жест — точку прилёта считает сервер (CatchThrow.Aim).
local function throw(player: any, kind: string, hit: boolean)
	local a = CatchService.Handlers.Active(player)
	check(a, player.Name .. ": поимка не идёт")
	local t = workspace:GetServerTimeNow()
	local center = CatchService.Handlers.CenterAt(a.target, t + CG.FlightTime)
	local factor = if a.session.tutorial then GameConfig.Catch.Tutorial.CircleFactor else 1
	-- мимо — вбок, в сторону места (уклонившееся существо уже в стороне: туда область броска может не дотянуться)
	local side = if (center - a.stage):Dot(a.camera.RightVector) > 0 then -1 else 1
	local away = a.camera.RightVector * side * (CG.Circle.Max * a.target.params.scale * factor + 0.5)
	local g = gestureTo(a, if hit then center else center + away)
	check(g, player.Name .. ": жест для броска не нашёлся")
	CatchService.Handlers.Action(player, "Throw", kind, g, t)
end

-- Встать у существа в слоте и начать поимку (Ловибумы уровня даются заранее).
local function beginCatch(player: any, boss: number, slot: number): boolean
	local _, part = BossLootService.SlotItem(boss, slot)
	check(part, ("босс %d, слот %d пуст"):format(boss, slot))
	local home = (part :: BasePart):GetAttribute("Home") :: CFrame
	player:MoveTo(home.Position + Vector3.new(0, 3, -5))
	return CatchService.Begin(player, boss, slot)
end

-- Боссы 4 и 5 дерутся (босс 5 — с 2026-11-24, в Studio), поэтому «без боя» — на примере босса 6.
test(
	"Без боя (босс 6, тестовый режим): поимка — и в руки, слот пуст до рассвета, экспонат помнит босса",
	function(A, B)
		local shifted = ensureDay()
		BossLootService.Handlers.Refresh()
		local entry = bossSlots()[6][1]
		local uid = entry.uid :: string
		local part = (ItemRegistry.Get(uid) :: any).part
		A:MoveTo(part.Position + Vector3.new(0, 0, -3))
		CarryService.Handlers.Pickup(A, uid)
		local stillThere = ItemRegistry.Get(uid).state == "AtBoss"
		giveLovibums(A, 6, "Mega", 3)
		CatchService.Handlers.SetRoll(0)
		local started = beginCatch(A, 6, 1)
		if started then
			throw(A, "Mega", true)
			waitUntil(function()
				return ItemRegistry.GetCarriedBy(A) == uid
			end, CG.FlightTime + CG.CaptureTime + 3)
		end
		CatchService.Handlers.SetRoll(nil)
		local taken = ItemRegistry.GetCarriedBy(A) == uid
		local emptied = entry.uid == nil
		giveLovibums(B, 6, "Boom", 1)
		B:MoveTo(part.Position + Vector3.new(0, 0, 3))
		BossLootService.Handlers.Take(B, 6, 1)
		local bEmpty = ItemRegistry.GetCarriedBy(B) == nil and not CatchService.IsCatching(B)
		if shifted then
			TimeService.ResetClock()
		end
		check(stillThere, "предмет у босса подняли обычным «Поднять»")
		check(started, "поимка не началась: " .. table.concat(A:Notices(), "; "))
		check(
			taken and ItemRegistry.Get(uid).boss == 6,
			"A не получил пойманное в тестовом режиме"
		)
		check(stockOf(A, 6, "Mega") == 2, "Ловибум не списан")
		check(
			part:GetAttribute("Home") == nil and part:GetAttribute("CatchMode") == nil,
			"у пойманного остались атрибуты босса"
		)
		check(emptied and bEmpty, "слот не опустел или B что-то получил")
		local plotA = plotOf(A)
		near(A, plotA.showcases[1])
		MuseumService.Handlers.Display(A, plotA, 1)
		local record = DataService.GetData(A).items[uid]
		check(
			record and record.boss == 6 and record.source == "boss",
			"в профиле нет босса-источника"
		)
		BossLootService.Handlers.Refresh()
		check(entry.uid ~= nil, "слот не заполнен на рассвете")
		check(
			ItemRegistry.Get(uid).state == "Displayed",
			"рассвет тронул выставленный экспонат"
		)
	end
)

test("Без боя поймать нельзя вне тестового режима Studio (босс 6)", function(A)
	local shifted = ensureDay() -- ночью отказ был бы «ночь», а не «нет боя»
	BossLootService.Handlers.Refresh()
	local uid = bossSlots()[6][1].uid :: string
	A:MoveTo((ItemRegistry.Get(uid) :: any).part.Position + Vector3.new(0, 0, -3))
	giveLovibums(A, 6, "Boom", 1)
	local saved = GameConfig.Bosses.FreeTakeInStudio
	GameConfig.Bosses.FreeTakeInStudio = false
	local ok, err = pcall(BossLootService.Handlers.Take, A, 6, 1)
	GameConfig.Bosses.FreeTakeInStudio = saved
	check(ok, tostring(err))
	check(ItemRegistry.Get(uid).state == "AtBoss" and ItemRegistry.GetCarriedBy(A) == nil, "забрал без боя")
	check(not CatchService.IsCatching(A), "поимка у босса без боя началась")
	check(
		A:WasNotified("нет боя"),
		"нет сообщения «у этого босса пока нет боя»"
	)
	check(stockOf(A, 6, "Boom") == 1, "Ловибум списан без броска")
	if shifted then
		TimeService.ResetClock()
	end
end)

-- ── D55: магазин Ловибумов, поимка, бой после поимки ─────────────────────────────────────────────────────────

local function waitCatchEnd(player: any, timeout: number): boolean
	return waitUntil(function()
		return not CatchService.IsCatching(player)
	end, timeout)
end

test(
	"D55/D61 магазин: покупка — набор ×3 за цену один раз; отказы (уровень, вид, монеты, запас, обучение, поимка)",
	function(A)
		local data = DataService.GetData(A)
		data.coins = 1e6
		ShopService.Handlers.Action(A, "Buy", 1, "Boom")
		local price = CatchRules.Price(ShopService.Prices(), 1, "Boom")
		check(price == 1000, "цена Бума ур. 1 изменилась: " .. tostring(price))
		check(GameConfig.Catch.PerBuy == 3, "в наборе не 3 Ловибума")
		check(
			stockOf(A, 1, "Boom") == 3 and data.coins == 1e6 - 1000,
			"покупка не выдала 3 за цену один раз"
		)
		-- прежний клиент присылал количество: оно не читается — снова ровно 3 за одну цену
		task.wait(GameConfig.Catch.BuyGap + 0.1)
		ShopService.Handlers.Action(A, "Buy", 1, "Boom", 100)
		check(
			stockOf(A, 1, "Boom") == 6 and data.coins == 1e6 - 2000,
			("количество от клиента учтено: запас %d, монет %d"):format(
				stockOf(A, 1, "Boom"),
				data.coins
			)
		)
		local before = data.coins
		for _, bad in
			{
				{ 0, "Boom" },
				{ 11, "Boom" },
				{ 1.5, "Boom" },
				{ 0 / 0, "Boom" },
				{ 1, "Ultra" },
				{ "1", "Boom" },
				{ 1, nil },
			}
		do
			task.wait(0.3) -- лимит запросов
			ShopService.Handlers.Action(A, "Buy", bad[1], bad[2])
		end
		check(
			data.coins == before and stockOf(A, 1, "Boom") == 6,
			"поддельная покупка что-то изменила"
		)
		-- монет меньше цены набора на 1 — отказ; ровно цена — можно
		task.wait(0.3)
		data.coins = 999
		ShopService.Handlers.Action(A, "Buy", 1, "Boom")
		check(
			data.coins == 999 and stockOf(A, 1, "Boom") == 6 and A:WasNotified("Не хватает"),
			"купил без денег"
		)
		task.wait(GameConfig.Catch.BuyGap + 0.1)
		data.coins = 1000
		ShopService.Handlers.Action(A, "Buy", 1, "Boom")
		check(data.coins == 0 and stockOf(A, 1, "Boom") == 9, "ровно на цену набора не купил")
		-- запас сверх MaxStock: набор не влезает — отказ без списания
		task.wait(GameConfig.Catch.BuyGap + 0.1)
		data.coins = 1e6
		DataService.Lovibums(A).L1.Boom = GameConfig.Catch.MaxStock - 2
		ShopService.Handlers.Action(A, "Buy", 1, "Boom")
		check(
			data.coins == 1e6 and stockOf(A, 1, "Boom") == GameConfig.Catch.MaxStock - 2,
			"набор сверх запаса продан"
		)
		DataService.Lovibums(A).L1.Boom = 9
		task.wait(0.3)
		local saved = data.tutorial
		data.tutorial = { step = "Catch" }
		ShopService.Handlers.Action(A, "Buy", 1, "Boom")
		data.tutorial = saved
		check(
			stockOf(A, 1, "Boom") == 9 and A:WasNotified("после обучения"),
			"во время обучения магазин продал"
		)
		task.wait(0.3)
		local saveIsCatching = ShopService.IsCatching
		ShopService.IsCatching = function()
			return true
		end
		ShopService.Handlers.Action(A, "Buy", 1, "Boom")
		ShopService.IsCatching = saveIsCatching
		check(
			stockOf(A, 1, "Boom") == 9 and A:WasNotified("поимки"),
			"во время поимки магазин продал"
		)
		-- расход: один бросок — одна штука (списание поимки — DataService.SpendLovibum)
		check(
			DataService.SpendLovibum(A, 1, "Boom") and stockOf(A, 1, "Boom") == 8,
			"расход не по одной штуке"
		)
	end
)

test(
	"D55 цены: утверждённые 1–4 прежние, набор ×3 списывает цену один раз, повторы режутся, запас и монеты сохраняются",
	function(A, _B, ctx)
		-- цены: боссы 1–4 — утверждённые (как в опубликованной игре; босс 4 открыт с коллекцией, D59), 5–10 — только в Studio
		local live = CatchRules.Prices(false)
		check(
			live[1] and live[1].Boom == 1000 and live[2].Turbo == 20000 and live[3].Mega == 90000,
			"утверждённые цены 1–3"
		)
		check(
			live[4] and live[4].Boom == 300000 and live[4].Mega == 900000,
			"утверждённая цена 4 (D56)"
		)
		check(live[5] == nil and ShopService.Prices()[5] ~= nil, "босс 5 — только в Studio")
		-- покупка настоящим обработчиком (D61): набор Турбо босса 2 — минус ровно 20K (цена прежняя), плюс 3 в запас
		local data = DataService.GetData(A)
		task.wait(1.1) -- лимит запросов прошлых тестов
		data.coins = 100000
		ShopService.Handlers.Action(A, "Buy", 2, "Turbo")
		check(
			data.coins == 80000 and stockOf(A, 2, "Turbo") == 3,
			("набор Турбо ур. 2: монет %d, запас %d"):format(data.coins, stockOf(A, 2, "Turbo"))
		)
		check(A:GetAttribute("Coins") == 80000, "атрибут Coins не обновился")
		check(
			A:WasNotified("Куплено: Турбо ×3"),
			"нет уведомления «Куплено: Турбо ×3»"
		)
		-- повторные запросы подряд (двойное нажатие, подделка в цикле): принимается одна покупка (Catch.BuyGap)
		task.wait(1.1)
		data.coins = 1e6
		local before = stockOf(A, 1, "Boom")
		for _ = 1, 20 do
			ShopService.Handlers.Action(A, "Buy", 1, "Boom")
		end
		local bought = stockOf(A, 1, "Boom") - before
		check(
			bought == 3,
			("из 20 запросов подряд выдано %d шт. (ждали один набор — 3)"):format(
				bought
			)
		)
		check(
			data.coins == 1e6 - 1000,
			("монеты не сходятся: %d за %d шт."):format(data.coins, bought)
		)
		-- после паузы — снова можно: второй набор
		task.wait(GameConfig.Catch.BuyGap + 0.3)
		ShopService.Handlers.Action(A, "Buy", 1, "Boom")
		check(
			stockOf(A, 1, "Boom") - before == 6 and data.coins == 1e6 - 2000,
			"после паузы второй набор не куплен"
		)
		-- выход и вход: запас и монеты — из профиля
		local coins, turbo, boom = data.coins, stockOf(A, 2, "Turbo"), stockOf(A, 1, "Boom")
		local userId = A.UserId
		leave(A)
		local again = TestPlayer.new("Тест_A_снова")
		again.UserId = userId
		ctx.track(again)
		check(join(again), "A не вошёл снова")
		check(
			stockOf(again, 2, "Turbo") == turbo and stockOf(again, 1, "Boom") == boom,
			"купленные Ловибумы не сохранились"
		)
		check(
			DataService.GetData(again).coins == coins,
			"монеты после покупок не сохранились"
		)
	end
)

test(
	"D55 поимка: три неудачи — побег, босс свободен для второго; у первого пауза 10 с только у этого босса",
	function(A, B)
		local shifted = ensureDay()
		check(waitBossHome(1), "пёс не дома")
		BossLootService.Handlers.Refresh()
		giveLovibums(A, 1, "Boom", 3)
		local uid = BossLootService.SlotItem(1, 2)
		check(beginCatch(A, 1, 2), "поимка не началась: " .. table.concat(A:Notices(), "; "))
		check(A:GetAttribute("Catching") == 1, "нет атрибута Catching")
		local part = (ItemRegistry.Get(uid :: string) :: any).part
		check(part:GetAttribute("CatchMode") == "Catch", "существо не в режиме мини-игры")
		check(not BossLootService.IsOpen(1), "подсказки у босса не выключены")
		for i = 1, 3 do
			waitReady(A)
			throw(A, "Boom", false)
			check(stockOf(A, 1, "Boom") == 3 - i, ("бросок %d не списал Ловибум"):format(i))
		end
		check(
			waitCatchEnd(A, CG.FlightTime + CG.CaptureTime + 4),
			"мини-игра не кончилась после трёх бросков"
		)
		check(BossLootService.SlotItem(1, 2) == uid, "существо ушло со слота")
		check(part:GetAttribute("CatchMode") == "Flee", "существо не убегает")
		check(BossLootService.IsOpen(1), "босс не освободился")
		local left = CatchRules.PauseLeft(CatchService.Handlers.Pauses(), A.UserId, 1, workspace:GetServerTimeNow())
		check(left > 5 and left <= CG.FailPause, ("пауза у этого босса %.1f с"):format(left))
		check(
			CatchRules.PauseLeft(CatchService.Handlers.Pauses(), A.UserId, 2, workspace:GetServerTimeNow()) == 0,
			"пауза у другого босса"
		)
		-- второй игрок начинает сразу, первый — нет
		giveLovibums(B, 1, "Boom", 1)
		check(beginCatch(B, 1, 3), "B не начал поимку сразу: " .. table.concat(B:Notices(), "; "))
		CatchService.Handlers.Action(B, "Leave")
		giveLovibums(A, 1, "Boom", 1)
		check(not beginCatch(A, 1, 3), "A начал поимку в паузе")
		check(A:WasNotified("насторожены"), "A не сказали про паузу")
		if shifted then
			TimeService.ResetClock()
		end
	end
)

test(
	"D74 поимка → без боя: существо сразу в руках с редкостью этажа; постамент, доход с множителем, вход",
	function(A, _B, ctx)
		ensureDay()
		check(waitBossHome(1), "пёс не дома")
		BossLootService.Handlers.Refresh()
		giveLovibums(A, 1, "Turbo", 2)
		local uid = BossLootService.SlotItem(1, 1) :: string
		local itemId = ItemRegistry.Get(uid).itemId
		local def = Items[itemId]
		local roll = 0.9995 -- у любого существа это самая редкая ступень
		local want = FloorRules.Roll(def.rarity, roll)
		check(want == "Diamond", "бросок 0.9995 — не Алмазный: " .. tostring(want))
		CatchService.Handlers.SetRoll(0)
		DevourService.Roll = function()
			return roll
		end
		check(beginCatch(A, 1, 1), "поимка не началась")
		throw(A, "Turbo", true)
		local part = (ItemRegistry.Get(uid) :: any).part
		local carried = waitUntil(function()
			return ItemRegistry.GetCarriedBy(A) == uid
		end, CG.FlightTime + CG.CaptureTime + 3)
		DevourService.Roll = nil
		CatchService.Handlers.SetRoll(nil)
		check(carried, "после поимки существо не в руках")
		check(
			BattleService.Handlers.FightOf(A) == nil and not BattleService.InBattle(A),
			"после поимки начался бой"
		)
		local entry = ItemRegistry.Get(uid)
		check(
			entry.floorRarity == want,
			"редкость этажа не записана в реестр: " .. tostring(entry.floorRarity)
		)
		check(part:GetAttribute("FloorRarity") == want, "редкости этажа нет на предмете")
		check(
			part:GetAttribute("Home") == nil and part:GetAttribute("CatchMode") == nil,
			"в руках — атрибуты босса"
		)
		check(stockOf(A, 1, "Turbo") == 1, "Ловибумы посчитаны неверно")
		check(BossLootService.SlotItem(1, 1) == nil, "слот не опустел до рассвета")
		check(
			BossLootService.IsOpen(1) and not BattleService.Busy(1),
			"после поимки босс остался занят"
		)
		-- доход: существо ÷ средний множитель × множитель редкости этажа; у Деревянного — меньше каталога
		local rich = IncomeService.Of(itemId, want)
		local expected = math.max(1, math.floor(FloorRules.Income(def.income, def.rarity, want) + 0.5))
		check(
			rich == expected,
			("доход Алмазного %s, ждали %s"):format(tostring(rich), tostring(expected))
		)
		check(
			IncomeService.Of(itemId) < def.income and rich > def.income,
			"нормировка: Деревянный не ниже каталога или Алмазный не выше"
		)
		check(
			IncomeService.Of(itemId, "Golden") == IncomeService.Of(itemId),
			"чужой ключ редкости — не Деревянный"
		)
		-- постамент: редкость уходит в профиль, доход идёт с множителем
		local plotA = plotOf(A)
		near(A, plotA.showcases[1])
		MuseumService.Handlers.Display(A, plotA, 1)
		entry = ItemRegistry.Get(uid)
		check(
			entry.state == "Displayed" and entry.floorRarity == want,
			"на постаменте редкость этажа потерялась"
		)
		local record = DataService.GetData(A).items[uid]
		check(record and record.floor == want, "редкости этажа нет в профиле")
		local coins = DataService.GetData(A).coins
		IncomeService.Handlers.Tick({ A })
		check(
			DataService.GetData(A).coins == coins + rich,
			"доход с множителем редкости не начислен"
		)
		check(A:GetAttribute("Income") == rich, "атрибут Income без множителя редкости")
		-- хранилище и обратно: редкость та же
		InventoryService.Handlers.StoreDisplayed(A, plotA, 1)
		check(
			ItemRegistry.Get(uid).floorRarity == want,
			"в хранилище редкость этажа потерялась"
		)
		-- повторный вход: редкость восстановлена из профиля
		local userId = A.UserId
		leave(A)
		local again = TestPlayer.new("Тест_A_снова")
		again.UserId = userId
		ctx.track(again)
		check(join(again), "A не вошёл повторно")
		entry = ItemRegistry.Get(uid)
		check(
			entry and entry.itemId == itemId and entry.floorRarity == want,
			"после входа редкость этажа не восстановлена"
		)
		check(
			entry.state == "Stored" and countUid(uid) == 0,
			"после входа существо не в хранилище или есть дубль"
		)
		check(waitBossHome(1), "пёс не вернулся")
		TimeService.ResetClock()
	end
)

test(
	"D55 занятый босс: второй не ловит, не начинает бой; подделки бросков — отказ без списания",
	function(A, B)
		ensureDay()
		check(waitBossHome(1), "пёс не дома")
		BossLootService.Handlers.Refresh()
		giveLovibums(A, 1, "Boom", 5)
		giveLovibums(B, 1, "Boom", 1)
		check(beginCatch(A, 1, 1), "поимка A не началась")
		B:ClearSent()
		check(not beginCatch(B, 1, 3), "B поймал у занятого босса")
		check(B:WasNotified("ловит"), "B не сказали, что босс занят")
		check(BattleService.Handlers.Begin(B, 1, 3) == nil, "B начал бой с занятым боссом")
		local a = CatchService.Handlers.Active(A)
		local t = workspace:GetServerTimeNow()
		local center = CatchService.Handlers.CenterAt(a.target, t + CG.FlightTime)
		local good = gestureTo(a, center)
		check(good, "жест в существо не нашёлся")
		local TH = GameConfig.Catch.Throw
		local function with(field: string, value: any): any
			local g = table.clone(good)
			g[field] = value
			return g
		end
		local fakes = {
			{ "Mega", good, t }, -- вида нет в запасе
			{ "Ultra", good, t },
			{ "Boom", good, t + 5 }, -- время из будущего
			{ "Boom", good, t - 5 }, -- старое
			{ "Boom", good, 0 / 0 },
			{ "Boom", center, t }, -- точка прицела от клиента (старый формат) — не верим
			{ "Boom", Vector3.new(0 / 0, 0, 0), t },
			{ "Boom", with("length", TH.MinSwipe * 0.5), t }, -- короткий жест — не бросок
			{ "Boom", with("speed", TH.MinSpeed * 0.5), t }, -- медленный
			{ "Boom", with("dx", 5), t }, -- вбок
			{ "Boom", with("dy", 1), t }, -- вниз
			{ "Boom", with("speed", 0 / 0), t },
			{ "Boom", with("length", math.huge), t },
			{ "Boom", { dx = "0", dy = -1, speed = 3, length = 0.3 }, t },
			{ "Boom", "строка", t },
		}
		for _, f in fakes do
			task.wait(0.3)
			CatchService.Handlers.Action(A, "Throw", f[1], f[2], workspace:GetServerTimeNow() + (f[3] - t))
		end
		check(
			stockOf(A, 1, "Boom") == 5 and a.session.throws == 0,
			"поддельный бросок засчитан"
		)
		check(a.last == nil, "поддельный бросок дошёл до проверки попадания")
		CatchService.Handlers.Action(B, "Throw", "Boom", good, workspace:GetServerTimeNow())
		check(stockOf(B, 1, "Boom") == 1, "бросок без своей мини-игры засчитан")
		throw(A, "Boom", false)
		check(stockOf(A, 1, "Boom") == 4, "настоящий бросок не засчитан")
		throw(A, "Boom", false)
		check(stockOf(A, 1, "Boom") == 4, "бросок раньше паузы засчитан")
		CatchService.Handlers.Action(A, "Leave")
		check(waitCatchEnd(A, 3), "«Уйти» не закончило поимку")
		TimeService.ResetClock()
	end
)

test(
	"D55 бросок жестом: точку считает сервер; в существо — попадание, в рывке уклонения — промах",
	function(A)
		ensureDay()
		check(waitBossHome(1), "пёс не дома")
		BossLootService.Handlers.Refresh()
		giveLovibums(A, 1, "Boom", 4)
		check(beginCatch(A, 1, 1), "поимка не началась")
		local a = CatchService.Handlers.Active(A)
		check(typeof(a.camera) == "CFrame" and typeof(a.stage) == "Vector3", "нет камеры поимки")
		check(
			(a.camera.Position - a.stage).Magnitude <= GameConfig.Catch.Game.Camera.Max * 1.1,
			"камера далеко от существа"
		)
		-- в существо: попадание (шанс — побег, чтобы не начинать бой); точка — та, что дал бы клиент
		CatchService.Handlers.SetRoll(0.999)
		local t = workspace:GetServerTimeNow()
		local center = CatchService.Handlers.CenterAt(a.target, t + CG.FlightTime)
		local g = gestureTo(a, center)
		check(g, "жест в существо не нашёлся")
		CatchService.Handlers.Action(A, "Throw", "Boom", g, t)
		check(
			a.last and a.last.outcome == "Escape",
			"бросок в существо — не попадание: " .. tostring(a.last and a.last.outcome)
		)
		local parsed = CatchThrow.Parse(g)
		check(
			parsed and a.last and (a.last.aim - CatchThrow.Aim(a.camera, a.stage, parsed)).Magnitude < 1e-6,
			"сервер посчитал другую точку"
		)
		check(stockOf(A, 1, "Boom") == 3, "попадание не списало Ловибум")
		CatchService.Handlers.SetRoll(nil)
		-- в рывке уклонения: жест в место, где существо стоит обычно, — промах (сервер считает, где оно в момент прилёта)
		waitReady(A)
		local p, target = a.target.params, a.target
		local function dodging(at: number): boolean
			local arrival = at + CG.FlightTime
			local pose = CreatureMotion.Pose(p, arrival)
			local c = CreatureMotion.Center(target.home, pose, target.height)
			local r = CatchRules.CircleRadius(arrival, a.session.since, p.scale)
			return math.abs(pose.dodge) >= 0.99 and not CatchRules.IsHit(a.stage, c, r)
		end
		local found: number? = nil
		local from = workspace:GetServerTimeNow() + 0.3
		for i = 0, 600 do
			local at = from + i * 0.05
			if dodging(at) and dodging(at + 0.1) then
				found = at
				break
			end
		end
		check(found, "нет уклонения в ближайшие 30 с")
		while workspace:GetServerTimeNow() < (found :: number) do
			task.wait()
		end
		CatchService.Handlers.Action(A, "Throw", "Boom", gestureTo(a, a.stage), workspace:GetServerTimeNow())
		check(
			a.last and a.last.outcome == "Miss",
			"в рывке уклонения — не промах: " .. tostring(a.last and a.last.outcome)
		)
		check(stockOf(A, 1, "Boom") == 2, "промах не списал Ловибум")
		CatchService.Handlers.Action(A, "Leave")
		check(waitCatchEnd(A, 3), "«Уйти» не закончило поимку")
		TimeService.ResetClock()
	end
)

test(
	"D55 прерывания: ночь, выход и гибель снимают закрепление, существо возвращается",
	function(A, B)
		ensureDay()
		check(waitBossHome(1), "пёс не дома")
		BossLootService.Handlers.Refresh()
		giveLovibums(A, 1, "Boom", 3)
		check(beginCatch(A, 1, 4), "поимка не началась")
		TimeService.SkipTo("Night", 0)
		check(waitCatchEnd(A, 3), "ночь не прервала поимку")
		check(BossLootService.IsOpen(1), "босс не освободился ночью")
		TimeService.ResetClock()
		ensureDay()
		BossLootService.Handlers.Refresh()
		giveLovibums(B, 1, "Boom", 1)
		check(beginCatch(B, 1, 2), "поимка B не началась")
		local _, humanoid = A.Character, B.Character and B.Character:FindFirstChildOfClass("Humanoid")
		if humanoid then
			humanoid.Health = 0
			check(waitCatchEnd(B, 3), "гибель не прервала поимку")
		else
			CatchService.Abort(B, "Died")
		end
		check(BossLootService.IsOpen(1), "босс не освободился после гибели")
		TimeService.ResetClock()
	end
)

test(
	"D55 Ловибумы сохраняются после выхода и входа; босс 3 с боем",
	function(A, _B, ctx)
		giveLovibums(A, 3, "Mega", 7)
		local userId = A.UserId
		leave(A)
		local again = TestPlayer.new("Тест_A_снова")
		again.UserId = userId
		ctx.track(again)
		check(join(again), "A не вошёл снова")
		check(stockOf(again, 3, "Mega") == 7, "Ловибумы не сохранились")
		check(BossService.Get(3) ~= nil, "у Крысиного короля нет боя")
		check(
			Battle.Bosses[3] and Battle.Bosses[3].Strength == GameConfig.Progression.Bosses[3],
			"сила короля не из Progression"
		)
	end
)

-- ── Босс 3 «Крысиный король» (D54 + D55): полный игровой цикл ────────────────────────────────────────────────

local function boss3Ids(): { string }
	local ids = {}
	for id, def in Items do
		if def.boss == 3 and not def.legacy then
			table.insert(ids, id)
		end
	end
	table.sort(ids)
	return ids
end

test(
	"Босс 3: 30 существ на суставах, по мешу на часть, Part-резерв 8–40; подставка только у трона, осьминога и императора",
	function()
		-- D54 (правила владельца): Stand — декоративная подставка, у живого скрыта; у трона, осьминога и императора — часть
		-- композиции; у билетика с подставкой скрыт и турникет (Grabber). Меши загружены 2026-11-14 — бюджет 8–40 деталей
		-- у Part-версии (резерв на случай, если меши не загрузятся), в игре — меш на каждую видимую часть.
		local KEEP = { RatThrone = true, SubwayOctopus = true, ThreeTailEmperor = true }
		local ids = boss3Ids()
		check(#ids == 30, ("в коллекции босса 3 %d существ"):format(#ids))
		local problems = {}
		local function details(part: Instance): (number, number, number)
			local blocks, meshes, motors = 0, 0, 0
			for _, d in part:GetDescendants() do
				if d:IsA("MeshPart") then
					meshes += 1
				elseif d:IsA("BasePart") then
					blocks += 1
				elseif d:IsA("Motor6D") then
					motors += 1
				end
			end
			return blocks, meshes, motors
		end
		for _, id in ids do
			ItemFactory.SetCreatureMeshes(id, {})
			local reserve = ItemFactory.Create(id)
			ItemFactory.SetCreatureMeshes(id, nil)
			local reserveBlocks = details(reserve)
			reserve:Destroy()
			if reserveBlocks < 8 or reserveBlocks > 40 then
				table.insert(problems, ("%s: Part-версия — блоков %d"):format(id, reserveBlocks))
			end
			local part = ItemFactory.Create(id)
			local blocks, meshes, motors = details(part)
			local loaded = ItemFactory.CreatureMeshCount(id)
			if loaded == 0 or meshes ~= loaded or blocks > 0 then
				table.insert(
					problems,
					("%s: мешей %d из %d, лишних блоков %d"):format(id, meshes, loaded, blocks)
				)
			end
			if part:GetAttribute("Creature") ~= true or motors < 2 then
				table.insert(
					problems,
					("%s: не существо на суставах (моторов %d)"):format(id, motors)
				)
			end
			if (part:FindFirstChild("Stand") ~= nil) ~= (KEEP[id] == true) then
				table.insert(
					problems,
					id .. ": подставка " .. (if KEEP[id] then "скрыта" else "видна")
				)
			end
			if id == "RunawayTicket" and part:FindFirstChild("Grabber") then
				table.insert(problems, "RunawayTicket: турникет не скрыт с подставкой")
			end
			part:Destroy()
		end
		check(#problems == 0, table.concat(problems, "; "))
	end
)

test(
	"Босс 3: у короля 4 существа на подушках, «Поймать», редкости 70/25/5, бродят не дальше подушки",
	function()
		BossLootService.Handlers.Refresh()
		local arena = MapLayout.Arenas[3]
		local radius = CreatureMotion.WanderRadius(3)
		local now = workspace:GetServerTimeNow()
		for slot = 1, 4 do
			local uid, part = BossLootService.SlotItem(3, slot)
			check(uid and part, ("слот %d пуст"):format(slot))
			local p = part :: BasePart
			local def = Items[p:GetAttribute("ItemId") :: string]
			check(
				def and def.boss == 3 and not def.legacy,
				("слот %d: не существо босса 3"):format(slot)
			)
			check(p:GetAttribute("Creature") == true, ("слот %d: не живое существо"):format(slot))
			local drop = p:GetAttribute("Drop")
			check(drop == arena.top, ("слот %d: высота места %s"):format(slot, tostring(drop)))
			local home = p:GetAttribute("Home")
			check(typeof(home) == "CFrame", ("слот %d: нет места Home"):format(slot))
			local prompt = p:FindFirstChild("TakePrompt") :: ProximityPrompt?
			check(
				prompt and prompt.ActionText == "Поймать",
				("слот %d: нет подсказки «Поймать»"):format(slot)
			)
			-- та же функция движения, что у клиентов и у броска: центр не уходит с подушки 3.7 × 3.7 (половина — 1.85)
			local params = {
				seed = CreatureMotion.SeedOf(uid :: string),
				radius = radius,
				scale = CreatureMotion.ScaleOf(def.size),
				mode = "Wander",
				drop = arena.top,
			}
			local farthest = 0
			for k = 0, 600 do
				local pose = CreatureMotion.Pose(params, now + k * 0.37)
				farthest = math.max(farthest, Vector3.new(pose.offset.X, 0, pose.offset.Z).Magnitude)
			end
			check(
				farthest <= math.min(radius + 0.01, 1.85),
				("слот %d: ушёл на %.2f ст. от места"):format(slot, farthest)
			)
		end
		local rng = Random.new(3)
		local counts: { [string]: number } = {}
		local n = 6000
		for _ = 1, n do
			local rarity = BossLootService.RollRarity(3, rng)
			counts[rarity] = (counts[rarity] or 0) + 1
		end
		for rarity, chance in BossLootService.Chances(3) do
			local share = 100 * (counts[rarity] or 0) / n
			check(
				math.abs(share - chance) <= 2,
				("%s: %.1f %% (ждали %s %%)"):format(rarity, share, tostring(chance))
			)
			local itemId = BossLootService.ChooseItem(3, rarity, rng)
			if chance > 0 then
				check(
					itemId and Items[itemId].boss == 3 and Items[itemId].rarity == rarity,
					rarity .. ": нет существа"
				)
			end
		end
	end
)

test(
	"Босс 3: каждое из 30 существ — у короля, «Поймать», победа → в руках, постамент, доход, в инвентарь",
	function(A)
		-- то же, что после победы над королём (Reserve → Award), для каждого существа коллекции по очереди
		local shifted = ensureDay()
		local arena = MapLayout.Arenas[3]
		local plot = plotOf(A)
		local problems = {}
		for _, id in boss3Ids() do
			local def = Items[id]
			BossLootService.Handlers.FillWith(3, 1, id)
			local uid, part = BossLootService.SlotItem(3, 1)
			if not uid or not part then
				table.insert(problems, id .. ": не появился у короля")
				continue
			end
			local p = part :: BasePart
			local prompt = p:FindFirstChild("TakePrompt") :: ProximityPrompt?
			if
				p:GetAttribute("Creature") ~= true
				or p:GetAttribute("Drop") ~= arena.top
				or typeof(p:GetAttribute("Home")) ~= "CFrame"
			then
				table.insert(problems, id .. ": у короля без места живого существа")
			end
			if not prompt or prompt.ActionText ~= "Поймать" or prompt.ObjectText ~= def.displayName then
				table.insert(problems, id .. ": нет подсказки «Поймать» с именем")
			end
			local motors = 0
			for _, d in p:GetDescendants() do
				if d:IsA("Motor6D") then
					motors += 1
				end
			end
			if motors < 2 then
				table.insert(problems, ("%s: суставов %d"):format(id, motors))
			end
			if not (BossLootService.Reserve(3, 1, A) and BossLootService.Award(3, 1, A)) then
				table.insert(problems, id .. ": победа не отдала в руки")
				continue
			end
			if ItemRegistry.GetCarriedBy(A) ~= uid or p:GetAttribute("Home") ~= nil then
				table.insert(problems, id .. ": в руках не то или с атрибутами босса")
			end
			near(A, plot.showcases[1])
			task.wait(0.3) -- лимиты запросов игрока
			MuseumService.Handlers.Display(A, plot, 1)
			local entry = ItemRegistry.Get(uid)
			local shown = entry and entry.part -- музей ставит на постамент свою деталь экспоната
			if
				not entry
				or entry.state ~= "Displayed"
				or not shown
				or shown:GetAttribute("Slot") ~= 1
				or shown:GetAttribute("Creature") ~= true
			then
				table.insert(
					problems,
					("%s: не выставлено живым существом (%s)"):format(
						id,
						tostring(entry and entry.state)
					)
				)
				if ItemRegistry.GetCarriedBy(A) == uid then
					CarryService.LoseCarried(A, "уборка после проверки")
				end
				continue
			end
			local coins = DataService.GetData(A).coins
			IncomeService.Handlers.Tick({ A })
			local got = DataService.GetData(A).coins - coins
			if got ~= IncomeService.Of(id) or def.income <= 0 then
				table.insert(
					problems,
					("%s: доход %s, ждали %s"):format(id, tostring(got), tostring(IncomeService.Of(id)))
				)
			end
			task.wait(0.3)
			InventoryService.Handlers.StoreDisplayed(A, plot, 1)
			entry = ItemRegistry.Get(uid)
			if not entry or entry.state ~= "Stored" then
				table.insert(problems, id .. ": с постамента не убрано в инвентарь")
			end
		end
		BossLootService.Handlers.Refresh()
		check(#problems == 0, table.concat(problems, "; "))
		if shifted then
			TimeService.ResetClock()
		end
	end
)

-- ── Босс 4 «Сфинкс-лежебока»: 30 существ (D57 — каталог и доходы, D58 — веса и подставки, D59 — площадка) ───────

local function boss4Ids(): { string }
	local ids = {}
	for id, def in Items do
		if def.boss == 4 and not def.legacy then
			table.insert(ids, id)
		end
	end
	table.sort(ids)
	return ids
end

test(
	"Босс 4: 30 существ на суставах, по мешу на часть, Part-резерв 8–40; подставка скрыта, «?» и марево; вес 6/17/7 (D58)",
	function()
		local ids = boss4Ids()
		check(#ids == 30, ("в коллекции босса 4 %d существ"):format(#ids))
		local weights: { [string]: number } = {}
		local problems = {}
		local function details(part: Instance): (number, number, number)
			local blocks, meshes, motors = 0, 0, 0
			for _, d in part:GetDescendants() do
				if d:IsA("MeshPart") then
					meshes += 1
				elseif d:IsA("BasePart") then
					blocks += 1
				elseif d:IsA("Motor6D") then
					motors += 1
				end
			end
			return blocks, meshes, motors
		end
		for _, id in ids do
			local def = Items[id]
			weights[def.weight] = (weights[def.weight] or 0) + 1
			-- бюджет деталей предмета 8–40 — у Part-версии (резерв на случай, если меши не загрузятся)
			ItemFactory.SetCreatureMeshes(id, {})
			local reserve = ItemFactory.Create(id)
			ItemFactory.SetCreatureMeshes(id, nil)
			local reserveBlocks = details(reserve)
			reserve:Destroy()
			if reserveBlocks < 8 or reserveBlocks > 40 then
				table.insert(problems, ("%s: Part-версия — блоков %d"):format(id, reserveBlocks))
			end
			-- как в игре: загруженные меши частей (их нет — та же Part-версия)
			local part = ItemFactory.Create(id)
			local blocks, meshes, motors = details(part)
			local loaded = ItemFactory.CreatureMeshCount(id)
			if loaded > 0 and (meshes ~= loaded or blocks > 0) then
				table.insert(
					problems,
					("%s: мешей %d из %d, лишних блоков %d"):format(id, meshes, loaded, blocks)
				)
			end
			if part:GetAttribute("Creature") ~= true or motors < 2 then
				table.insert(
					problems,
					("%s: не существо на суставах (моторов %d)"):format(id, motors)
				)
			end
			if part:FindFirstChild("Stand") then
				table.insert(problems, id .. ": подставка видна")
			end
			if id == "FennecRiddler" and not part:FindFirstChild("Dot") then
				table.insert(problems, "FennecRiddler: нет точки «?» (Dot)")
			end
			if id == "MirageFish" and not part:FindFirstChild("Haze") then
				table.insert(problems, "MirageFish: нет марева (Haze)")
			end
			part:Destroy()
		end
		check(
			weights.Light == 6 and weights.Medium == 17 and weights.Heavy == 7,
			("вес: Light %d, Medium %d, Heavy %d (нужно 6/17/7)"):format(
				weights.Light or 0,
				weights.Medium or 0,
				weights.Heavy or 0
			)
		)
		check(#problems == 0, table.concat(problems, "; "))
	end
)

test(
	"Босс 4: у Сфинкса 4 существа на плитах площадки, «Поймать», редкости 52/30/13/5, бродят не дальше плиты",
	function()
		BossLootService.Handlers.Refresh()
		local arena = MapLayout.Arenas[4]
		local radius = CreatureMotion.WanderRadius(4)
		local now = workspace:GetServerTimeNow()
		local frame = MapLayout.ZoneCFrame(4)
		for slot = 1, 4 do
			local uid, part = BossLootService.SlotItem(4, slot)
			check(uid and part, ("слот %d пуст"):format(slot))
			local p = part :: BasePart
			local def = Items[p:GetAttribute("ItemId") :: string]
			check(
				def and def.boss == 4 and not def.legacy,
				("слот %d: не существо босса 4"):format(slot)
			)
			check(p:GetAttribute("Creature") == true, ("слот %d: не живое существо"):format(slot))
			check(
				p:GetAttribute("Drop") == arena.top,
				("слот %d: высота места %s"):format(slot, tostring(p:GetAttribute("Drop")))
			)
			local home = p:GetAttribute("Home")
			check(typeof(home) == "CFrame", ("слот %d: нет места Home"):format(slot))
			local spot = frame:PointToObjectSpace((home :: CFrame).Position)
			check(
				(Vector2.new(spot.X, spot.Z) - arena.slots[slot]).Magnitude < 0.01,
				("слот %d: не на своей плите (%.1f, %.1f)"):format(slot, spot.X, spot.Z)
			)
			local prompt = p:FindFirstChild("TakePrompt") :: ProximityPrompt?
			check(
				prompt and prompt.ActionText == "Поймать",
				("слот %d: нет подсказки «Поймать»"):format(slot)
			)
			local params = {
				seed = CreatureMotion.SeedOf(uid :: string),
				radius = radius,
				scale = CreatureMotion.ScaleOf(def.size),
				mode = "Wander",
				drop = arena.top,
			}
			local farthest = 0
			for k = 0, 600 do
				local pose = CreatureMotion.Pose(params, now + k * 0.37)
				farthest = math.max(farthest, Vector3.new(pose.offset.X, 0, pose.offset.Z).Magnitude)
			end
			check(
				farthest <= math.min(radius + 0.01, 2.6),
				("слот %d: ушёл на %.2f ст. от места"):format(slot, farthest)
			)
		end
		local rng = Random.new(4)
		local counts: { [string]: number } = {}
		local n = 8000
		for _ = 1, n do
			local rarity = BossLootService.RollRarity(4, rng)
			counts[rarity] = (counts[rarity] or 0) + 1
		end
		local chances = BossLootService.Chances(4)
		check(
			chances.Common == 52 and chances.Rare == 30 and chances.Epic == 13 and chances.Legendary == 5,
			"шансы босса 4 — D37 (52/30/13/5)"
		)
		for rarity, chance in chances do
			local share = 100 * (counts[rarity] or 0) / n
			check(
				math.abs(share - chance) <= 2,
				("%s: %.1f %% (ждали %s %%)"):format(rarity, share, tostring(chance))
			)
			local itemId = BossLootService.ChooseItem(4, rarity, rng)
			if chance > 0 then
				check(
					itemId and Items[itemId].boss == 4 and Items[itemId].rarity == rarity,
					rarity .. ": нет существа"
				)
			end
		end
	end
)

test(
	"Босс 4: каждое из 30 существ — у Сфинкса, «Поймать», победа → в руках, доход только на постаменте, в инвентарь",
	function(A)
		local shifted = ensureDay()
		local arena = MapLayout.Arenas[4]
		local plot = plotOf(A)
		local problems = {}
		for _, id in boss4Ids() do
			local def = Items[id]
			BossLootService.Handlers.FillWith(4, 1, id)
			local uid, part = BossLootService.SlotItem(4, 1)
			if not uid or not part then
				table.insert(problems, id .. ": не появился у Сфинкса")
				continue
			end
			local p = part :: BasePart
			local prompt = p:FindFirstChild("TakePrompt") :: ProximityPrompt?
			if
				p:GetAttribute("Creature") ~= true
				or p:GetAttribute("Drop") ~= arena.top
				or typeof(p:GetAttribute("Home")) ~= "CFrame"
			then
				table.insert(problems, id .. ": у Сфинкса без места живого существа")
			end
			if not prompt or prompt.ActionText ~= "Поймать" or prompt.ObjectText ~= def.displayName then
				table.insert(problems, id .. ": нет подсказки «Поймать» с именем")
			end
			if not (BossLootService.Reserve(4, 1, A) and BossLootService.Award(4, 1, A)) then
				table.insert(problems, id .. ": победа не отдала в руки")
				continue
			end
			if ItemRegistry.GetCarriedBy(A) ~= uid then
				table.insert(problems, id .. ": в руках не то")
			end
			-- в руках дохода нет (D37): сколько даёт музей без этого существа
			local coins0 = DataService.GetData(A).coins
			IncomeService.Handlers.Tick({ A })
			local base = DataService.GetData(A).coins - coins0
			near(A, plot.showcases[1])
			task.wait(0.3) -- лимиты запросов игрока
			MuseumService.Handlers.Display(A, plot, 1)
			local entry = ItemRegistry.Get(uid)
			local shown = entry and entry.part
			if not entry or entry.state ~= "Displayed" or not shown or shown:GetAttribute("Creature") ~= true then
				table.insert(
					problems,
					("%s: не выставлено живым существом (%s)"):format(
						id,
						tostring(entry and entry.state)
					)
				)
				if ItemRegistry.GetCarriedBy(A) == uid then
					CarryService.LoseCarried(A, "уборка после проверки")
				end
				continue
			end
			local coins = DataService.GetData(A).coins
			IncomeService.Handlers.Tick({ A })
			local got = DataService.GetData(A).coins - coins - base
			if got ~= IncomeService.Of(id) then
				table.insert(
					problems,
					("%s: доход %s, ждали %s"):format(id, tostring(got), tostring(IncomeService.Of(id)))
				)
			end
			task.wait(0.3)
			InventoryService.Handlers.StoreDisplayed(A, plot, 1)
			entry = ItemRegistry.Get(uid)
			if not entry or entry.state ~= "Stored" then
				table.insert(problems, id .. ": с постамента не убрано в инвентарь")
			end
		end
		BossLootService.Handlers.Refresh()
		check(#problems == 0, table.concat(problems, "; "))
		if shifted then
			TimeService.ResetClock()
		end
	end
)

test(
	"Босс 4: переноска Light / Medium / Heavy — скорость D24 ×1 / ×0.9 / ×0.8; ночью вне Safe Zone существо теряется",
	function(A, B, ctx)
		local Speed = require(ReplicatedStorage.Shared.Speed)
		local pick: { [string]: string } = {}
		for _, id in boss4Ids() do
			pick[Items[id].weight] = pick[Items[id].weight] or id
		end
		for _, weight in { "Light", "Medium", "Heavy" } do
			local id = pick[weight]
			check(id ~= nil, "нет существа веса " .. weight)
			if id then
				carry(ctx, A, id)
				task.wait(0.4)
				local humanoid = A.Character:FindFirstChildOfClass("Humanoid")
				local want = Speed.Walk(A:GetAttribute("Strength") or 0, weight)
				check(
					humanoid and math.abs(humanoid.WalkSpeed - want) < 0.05,
					("%s (%s): скорость %s, ждали %.2f"):format(
						id,
						weight,
						tostring(humanoid and humanoid.WalkSpeed),
						want
					)
				)
				CarryService.LoseCarried(A, "уборка после проверки")
				check(ItemRegistry.GetCarriedBy(A) == nil, id .. ": не снят с рук")
			end
		end
		-- ночь: в коридоре уровней — потерян, в Safe Zone — остаётся (D37)
		local corridor = Vector3.new(10, MapLayout.Heights.Path + 3, MapLayout.ZoneStartZ(4) - 40)
		A:MoveTo(corridor)
		local uidA = carry(ctx, A, pick.Heavy)
		B:MoveTo(MapLayout.Spawn.position + Vector3.new(20, 3, 20))
		local uidB = carry(ctx, B, pick.Light)
		local day = GameTime.At(GameConfig.Time.Epoch)
		local nightState = GameTime.At(GameConfig.Time.Epoch + GameConfig.Time.DayLength)
		NightService.Handlers.Apply(nightState, day, { A, B })
		check(
			ItemRegistry.Get(uidA) == nil and ItemRegistry.GetCarriedBy(A) == nil,
			"существо в коридоре ночью не потеряно"
		)
		check(ItemRegistry.GetCarriedBy(B) == uidB, "существо в Safe Zone потеряно")
		CarryService.LoseCarried(B, "уборка после проверки")
		NightService.Handlers.Apply(TimeService.Current(), nil, {})
	end
)

-- Точки вращения суставов существа в осях корня (покой): имя мотора → позиция; и меши частей.
local function creatureJoints(part: BasePart): ({ [string]: Vector3 }, { [string]: MeshPart })
	local pivots, meshes = {}, {}
	for _, d in part:GetDescendants() do
		if d:IsA("Motor6D") and d.Part0 then
			pivots[d.Name] = part.CFrame:PointToObjectSpace((d.Part0.CFrame * d.C0).Position)
		elseif d:IsA("MeshPart") then
			meshes[d.Name] = d
		end
	end
	return pivots, meshes
end

test(
	"Босс 3: меши D54 вместо Part-версии — те же суставы, место у короля, поимка, руки, постамент, доход",
	function(A)
		-- До импорта мешей нет: подставляем MeshPart-заглушки с именами и габаритами частей D54 (как после импорта) —
		-- проверяется, что сборка и механики с мешами те же, что с Part-версией (резерв).
		local shifted = ensureDay()
		local plot = plotOf(A)
		local problems = {}
		local function stand(id: string, only: { [string]: boolean }?): ({ [string]: MeshPart }, number)
			local parts, n = {}, 0
			for name, spec in CreatureRigs[id].Parts do
				if not spec.hidden and (not only or only[name]) then
					local m = Instance.new("MeshPart")
					m.Size = spec.size
					parts[name] = m
					n += 1
				end
			end
			return parts, n
		end
		local ok, err = pcall(function()
			for _, id in boss3Ids() do
				local reference = ItemFactory.Create(id) -- Part-версия
				local refPivots = creatureJoints(reference)
				local parts, visible = stand(id)
				ItemFactory.SetCreatureMeshes(id, parts)
				check(ItemFactory.CreatureMeshCount(id) == visible, id .. ": меши не подставились")
				local built = ItemFactory.Create(id)
				local pivots, meshes = creatureJoints(built)
				local blocks = 0
				for _, d in built:GetChildren() do
					if d:IsA("Part") then
						blocks += 1
					end
				end
				local joints, worst = 0, 0
				for name, at in refPivots do
					joints += 1
					worst = math.max(worst, if pivots[name] then (pivots[name] - at).Magnitude else math.huge)
				end
				local meshCount = 0
				for name, m in meshes do
					meshCount += 1
					local spec = CreatureRigs[id].Parts[name]
					if not spec or (m.Size - spec.size).Magnitude > 1e-3 then
						table.insert(problems, ("%s/%s: размер меша"):format(id, name))
					end
				end
				if built.Size ~= reference.Size or meshCount ~= visible or blocks > 0 or worst > 1e-3 then
					table.insert(
						problems,
						("%s: мешей %d из %d, блоков %d, суставов %d, сдвиг точки вращения %.4f"):format(
							id,
							meshCount,
							visible,
							blocks,
							joints,
							worst
						)
					)
				end
				reference:Destroy()
				built:Destroy()
				-- путь игрока: у короля → победа → в руках → постамент (музей строит экспонат заново) → доход → инвентарь
				BossLootService.Handlers.FillWith(3, 1, id)
				local uid, part = BossLootService.SlotItem(3, 1)
				local p = part :: BasePart
				local prompt = p and p:FindFirstChild("TakePrompt") :: ProximityPrompt?
				if
					not uid
					or not prompt
					or prompt.ActionText ~= "Поймать"
					or not p:FindFirstChildWhichIsA("MeshPart")
				then
					table.insert(problems, id .. ": у короля без мешей или без «Поймать»")
					continue
				end
				if not (BossLootService.Reserve(3, 1, A) and BossLootService.Award(3, 1, A)) then
					table.insert(problems, id .. ": победа не отдала в руки")
					continue
				end
				near(A, plot.showcases[1])
				task.wait(0.3) -- лимиты запросов игрока
				MuseumService.Handlers.Display(A, plot, 1)
				local entry = ItemRegistry.Get(uid :: string)
				local shown = entry and entry.part
				if
					not entry
					or entry.state ~= "Displayed"
					or not shown
					or not shown:FindFirstChildWhichIsA("MeshPart")
				then
					table.insert(problems, id .. ": на постаменте не меши")
					if ItemRegistry.GetCarriedBy(A) == uid then
						CarryService.LoseCarried(A, "уборка после проверки")
					end
					continue
				end
				local coins = DataService.GetData(A).coins
				IncomeService.Handlers.Tick({ A })
				if DataService.GetData(A).coins - coins ~= IncomeService.Of(id) then
					table.insert(problems, id .. ": доход не как в каталоге")
				end
				task.wait(0.3)
				InventoryService.Handlers.StoreDisplayed(A, plot, 1)
				entry = ItemRegistry.Get(uid :: string)
				if not entry or entry.state ~= "Stored" then
					table.insert(problems, id .. ": с постамента не убрано в инвентарь")
				end
				ItemFactory.SetCreatureMeshes(id, nil)
			end
			-- часть мешей ещё не импортирована: эти части — меши, остальные — блоки Part-версии, суставы те же
			local id = "CheeseDragon"
			local reference = ItemFactory.Create(id)
			local refPivots = creatureJoints(reference)
			ItemFactory.SetCreatureMeshes(id, (stand(id, { Head = true, Body = true })))
			local mixed = ItemFactory.Create(id)
			local pivots, meshes = creatureJoints(mixed)
			local worst = 0
			for name, at in refPivots do
				worst = math.max(worst, if pivots[name] then (pivots[name] - at).Magnitude else math.huge)
			end
			check(
				meshes.Head and meshes.Body and meshes.Jaw == nil,
				"смешанная сборка: не те части мешами"
			)
			check(
				mixed:FindFirstChild("Jaw") ~= nil and worst <= 1e-3,
				("смешанная сборка: сдвиг %.4f"):format(worst)
			)
			reference:Destroy()
			mixed:Destroy()
		end)
		for _, id in boss3Ids() do
			ItemFactory.SetCreatureMeshes(id, nil)
		end
		BossLootService.Handlers.Refresh()
		if shifted then
			TimeService.ResetClock()
		end
		check(ok, tostring(err))
		check(#problems == 0, table.concat(problems, "; "))
	end
)

test(
	"Босс 4: меши частей вместо Part-версии — те же суставы, у Сфинкса, поимка, руки, постамент, доход (до импорта — заглушки)",
	function(A)
		-- До импорта мешей нет: подставляем MeshPart-заглушки с именами и габаритами частей D54 (как после импорта) —
		-- проверяется, что сборка и механики с мешами те же, что с Part-версией (резерв).
		local shifted = ensureDay()
		local plot = plotOf(A)
		local problems = {}
		local function stand(id: string, only: { [string]: boolean }?): ({ [string]: MeshPart }, number)
			local parts, n = {}, 0
			for name, spec in CreatureRigs[id].Parts do
				if not spec.hidden and (not only or only[name]) then
					local m = Instance.new("MeshPart")
					m.Size = spec.size
					parts[name] = m
					n += 1
				end
			end
			return parts, n
		end
		local ok, err = pcall(function()
			for _, id in boss4Ids() do
				local reference = ItemFactory.Create(id) -- Part-версия
				local refPivots = creatureJoints(reference)
				local parts, visible = stand(id)
				ItemFactory.SetCreatureMeshes(id, parts)
				check(ItemFactory.CreatureMeshCount(id) == visible, id .. ": меши не подставились")
				local built = ItemFactory.Create(id)
				local pivots, meshes = creatureJoints(built)
				local blocks = 0
				for _, d in built:GetChildren() do
					if d:IsA("Part") then
						blocks += 1
					end
				end
				local joints, worst = 0, 0
				for name, at in refPivots do
					joints += 1
					worst = math.max(worst, if pivots[name] then (pivots[name] - at).Magnitude else math.huge)
				end
				local meshCount = 0
				for name, m in meshes do
					meshCount += 1
					local spec = CreatureRigs[id].Parts[name]
					if not spec or (m.Size - spec.size).Magnitude > 1e-3 then
						table.insert(problems, ("%s/%s: размер меша"):format(id, name))
					end
				end
				if built.Size ~= reference.Size or meshCount ~= visible or blocks > 0 or worst > 1e-3 then
					table.insert(
						problems,
						("%s: мешей %d из %d, блоков %d, суставов %d, сдвиг точки вращения %.4f"):format(
							id,
							meshCount,
							visible,
							blocks,
							joints,
							worst
						)
					)
				end
				reference:Destroy()
				built:Destroy()
				-- путь игрока: у Сфинкса → победа → в руках → постамент (музей строит экспонат заново) → доход → инвентарь
				BossLootService.Handlers.FillWith(4, 1, id)
				local uid, part = BossLootService.SlotItem(4, 1)
				local p = part :: BasePart
				local prompt = p and p:FindFirstChild("TakePrompt") :: ProximityPrompt?
				if
					not uid
					or not prompt
					or prompt.ActionText ~= "Поймать"
					or not p:FindFirstChildWhichIsA("MeshPart")
				then
					table.insert(
						problems,
						id .. ": у Сфинкса без мешей или без «Поймать»"
					)
					continue
				end
				if not (BossLootService.Reserve(4, 1, A) and BossLootService.Award(4, 1, A)) then
					table.insert(problems, id .. ": победа не отдала в руки")
					continue
				end
				near(A, plot.showcases[1])
				task.wait(0.3) -- лимиты запросов игрока
				MuseumService.Handlers.Display(A, plot, 1)
				local entry = ItemRegistry.Get(uid :: string)
				local shown = entry and entry.part
				if
					not entry
					or entry.state ~= "Displayed"
					or not shown
					or not shown:FindFirstChildWhichIsA("MeshPart")
				then
					table.insert(problems, id .. ": на постаменте не меши")
					if ItemRegistry.GetCarriedBy(A) == uid then
						CarryService.LoseCarried(A, "уборка после проверки")
					end
					continue
				end
				local coins = DataService.GetData(A).coins
				IncomeService.Handlers.Tick({ A })
				if DataService.GetData(A).coins - coins ~= IncomeService.Of(id) then
					table.insert(problems, id .. ": доход не как в каталоге")
				end
				task.wait(0.3)
				InventoryService.Handlers.StoreDisplayed(A, plot, 1)
				entry = ItemRegistry.Get(uid :: string)
				if not entry or entry.state ~= "Stored" then
					table.insert(problems, id .. ": с постамента не убрано в инвентарь")
				end
				ItemFactory.SetCreatureMeshes(id, nil)
			end
			-- часть мешей ещё не импортирована: эти части — меши, остальные — блоки Part-версии, суставы те же
			local id = "CanteenCamel" -- у верблюжонка есть Head, Body и Jaw
			local reference = ItemFactory.Create(id)
			local refPivots = creatureJoints(reference)
			ItemFactory.SetCreatureMeshes(id, (stand(id, { Head = true, Body = true })))
			local mixed = ItemFactory.Create(id)
			local pivots, meshes = creatureJoints(mixed)
			local worst = 0
			for name, at in refPivots do
				worst = math.max(worst, if pivots[name] then (pivots[name] - at).Magnitude else math.huge)
			end
			check(
				meshes.Head and meshes.Body and meshes.Jaw == nil,
				"смешанная сборка: не те части мешами"
			)
			check(
				mixed:FindFirstChild("Jaw") ~= nil and worst <= 1e-3,
				("смешанная сборка: сдвиг %.4f"):format(worst)
			)
			reference:Destroy()
			mixed:Destroy()
		end)
		for _, id in boss4Ids() do
			ItemFactory.SetCreatureMeshes(id, nil)
		end
		BossLootService.Handlers.Refresh()
		if shifted then
			TimeService.ResetClock()
		end
		check(ok, tostring(err))
		check(#problems == 0, table.concat(problems, "; "))
	end
)

-- После ручного импорта двух FBX и scripts/boss4_bind_after_import.py: меши настоящие, загрузились, с картами D39.
-- До импорта (MeshId нет) — только сведения «ещё не импортированы», не ошибка: Part-версия — утверждённый резерв.
test(
	"Босс 4 после импорта: меши 30 существ и 27 частей Сфинкса загружены, с картами (до импорта — сведения)",
	function(_A, _B, ctx)
		local sphinxOrder = (require(ReplicatedStorage.Shared.Config.Boss4SphinxRig) :: any).Order
		local bound, expected, sphinxBound = 0, 0, 0
		for _, id in boss4Ids() do
			local parts = ItemModels.Creatures[id]
			for name, spec in CreatureRigs[id].Parts do
				if not spec.hidden then
					expected += 1
					bound += if parts and parts[name] then 1 else 0
				end
			end
		end
		for _, name in sphinxOrder do
			sphinxBound += if BossModels[4].meshes[name] then 1 else 0
		end
		local counted = ("частей существ с MeshId %d из %d, частей Сфинкса %d из %d"):format(
			bound,
			expected,
			sphinxBound,
			#sphinxOrder
		)
		if bound == 0 and sphinxBound == 0 then
			ctx.note("меши босса 4 ещё не импортированы: " .. counted)
			return
		end
		check(
			bound == expected and sphinxBound == #sphinxOrder,
			"импорт привязан не полностью: " .. counted
		)
		local problems = {}
		for _, id in boss4Ids() do
			ItemFactory.SetCreatureMeshes(id, nil)
			local visible = 0
			for _, spec in CreatureRigs[id].Parts do
				visible += if spec.hidden then 0 else 1
			end
			local built = ItemFactory.Create(id)
			local _, meshes = creatureJoints(built)
			local count, withMaps, blocks = 0, 0, 0
			for _, m in meshes do
				count += 1
				withMaps += if m:FindFirstChildOfClass("SurfaceAppearance") then 1 else 0
			end
			for _, d in built:GetChildren() do
				blocks += if d:IsA("Part") then 1 else 0
			end
			built:Destroy()
			local loaded = ItemFactory.CreatureMeshCount(id)
			if loaded ~= visible or count ~= visible or withMaps ~= visible or blocks > 0 then
				table.insert(
					problems,
					("%s: загружено %d из %d, мешей %d, с картами %d, блоков %d"):format(
						id,
						loaded,
						visible,
						count,
						withMaps,
						blocks
					)
				)
			end
		end
		local boss = BossService.Get(4) :: BossService.Boss
		for _, name in sphinxOrder do
			local part = boss.model:FindFirstChild(name)
			if not (part and part:IsA("MeshPart") and part:FindFirstChildOfClass("SurfaceAppearance")) then
				table.insert(problems, "Сфинкс/" .. name .. ": не меш с картами")
			end
		end
		check(#problems == 0, table.concat(problems, "; "))
	end
)

-- ── Босс 4: отдельные тесты Сфинкса — занятость для второго игрока, бой, поражение, восстановление, повтор ──────────
-- A и B — серверные NPC-игроки (TestPlayer): проверяются правила сервера, а не игра двух настоящих клиентов.

test(
	"Сфинкс занят для второго (D74, после поимки боя нет): B не ловит, не дерётся и не забирает, пока A ловит, дерётся и Сфинкс идёт домой",
	function(A, B)
		local shifted = ensureDay()
		check(waitBossHome(4), "Сфинкс не дома")
		BossLootService.Handlers.Refresh()
		local uidB = BossLootService.SlotItem(4, 3) :: string
		check(uidB, "слот 3 Сфинкса пуст")
		giveLovibums(A, 4, "Boom", 1)
		giveLovibums(B, 4, "Boom", 1)
		local function blocked(stage: string, word: string)
			B:ClearSent()
			check(not beginCatch(B, 4, 3), stage .. ": B начал поимку у занятого Сфинкса")
			local said = table.concat(B:Notices(), "; ")
			check(B:WasNotified(word), ("%s: B не сказали «%s» (%s)"):format(stage, word, said))
			check(
				BattleService.Handlers.Begin(B, 4, 3) == nil,
				stage .. ": B начал бой с занятым Сфинксом"
			)
			BossLootService.Handlers.Take(B, 4, 3)
			local untouched = BossLootService.SlotItem(4, 3) == uidB and ItemRegistry.GetCarriedBy(B) == nil
			check(untouched, stage .. ": B забрал существо у занятого Сфинкса")
			check(stockOf(B, 4, "Boom") == 1, stage .. ": у B списали Ловибум")
			check(
				not CatchService.IsCatching(B) and not BattleService.InBattle(B),
				stage .. ": B в поимке или в бою"
			)
		end
		-- 1) A ловит существо в слоте 1
		CatchService.Handlers.SetRoll(0)
		check(beginCatch(A, 4, 1), "поимка A не началась: " .. table.concat(A:Notices(), "; "))
		blocked("поимка A", "ловит")
		-- 2) A поймал — боя нет (D74): существо сразу в руках, Сфинкс свободен
		throw(A, "Boom", true)
		local caught = waitUntil(function()
			return ItemRegistry.GetCarriedBy(A) ~= nil
		end, CG.FlightTime + CG.CaptureTime + 3)
		CatchService.Handlers.SetRoll(nil)
		check(caught, "после поимки существо не в руках у A")
		check(
			not BattleService.InBattle(A) and not BattleService.Busy(4),
			"после поимки начался бой"
		)
		check(BossLootService.IsOpen(4), "после поимки Сфинкс остался занят")
		CarryService.LoseCarried(A, "уборка: дальше A проверяет занятость")
		-- 4) Сфинкс дома — B ловит; теперь занят для A
		check(waitBossHome(4), "Сфинкс не вернулся домой")
		check(
			beginCatch(B, 4, 3),
			"Сфинкс дома, а B не может ловить: " .. table.concat(B:Notices(), "; ")
		)
		A:ClearSent()
		check(BattleService.Handlers.Begin(A, 4, 1) == nil, "A начал бой, пока ловит B")
		check(
			not beginCatch(A, 4, 2),
			"A начал вторую поимку у Сфинкса, пока ловит B"
		)
		CatchService.Handlers.Action(B, "Leave")
		check(waitCatchEnd(B, 3), "«Уйти» не закончило поимку B")
		check(stockOf(B, 4, "Boom") == 1, "«Уйти» без броска списало Ловибум B")
		check(waitBossHome(4), "Сфинкс не дома после ухода B")
		if shifted then
			TimeService.ResetClock()
		end
	end
)

test(
	"Сфинкс (D74): Ловибум ур. 4 → поимка при силе 0 → в руки без боя, редкость этажа, Сфинкс дома и свободен",
	function(A)
		local shifted = ensureDay()
		check(waitBossHome(4), "Сфинкс не дома")
		BossLootService.Handlers.Refresh()
		local boss = BossService.Get(4) :: BossService.Boss
		local uid = BossLootService.SlotItem(4, 2) :: string
		check(uid, "слот 2 Сфинкса пуст")
		local part = (ItemRegistry.Get(uid) :: any).part :: BasePart
		-- Ловибум другого уровня у Сфинкса не работает
		giveLovibums(A, 3, "Mega", 1)
		check(not beginCatch(A, 4, 2), "поимка у Сфинкса с Ловибумом уровня 3")
		check(A:WasNotified("уровня 4"), "нет подсказки про Ловибум уровня 4")
		check(stockOf(A, 3, "Mega") == 1, "Ловибум уровня 3 списан")
		giveLovibums(A, 4, "Turbo", 1)
		CatchService.Handlers.SetRoll(0)
		DevourService.Roll = function()
			return 0
		end
		check(beginCatch(A, 4, 2), "поимка не началась: " .. table.concat(A:Notices(), "; "))
		throw(A, "Turbo", true)
		local carried = waitUntil(function()
			return ItemRegistry.GetCarriedBy(A) == uid
		end, CG.FlightTime + CG.CaptureTime + 3)
		DevourService.Roll = nil
		CatchService.Handlers.SetRoll(nil)
		check(carried, "после поимки существо не в руках")
		check(
			not BattleService.InBattle(A) and BattleService.Handlers.FightOf(A) == nil,
			"после поимки начался бой"
		)
		check(
			(ItemRegistry.Get(uid) :: any).floorRarity == "Wood",
			"бросок 0 — не Деревянный этаж"
		)
		check(
			part:GetAttribute("Home") == nil and part:GetAttribute("CatchMode") == nil,
			"в руках — атрибуты Сфинкса"
		)
		check(BossLootService.SlotItem(4, 2) == nil, "слот не опустел до рассвета")
		check(stockOf(A, 4, "Turbo") == 0, "Ловибум ур. 4 не списан")
		check(waitBossHome(4), "Сфинкс не дома после поимки")
		check(boss.model:GetAttribute("TargetUserId") == nil, "у Сфинкса осталась цель")
		check(BossLootService.IsOpen(4) and not BattleService.Busy(4), "Сфинкс дома, но занят")
		check(A:GetAttribute("InBattle") == nil and A:GetAttribute("BattleHP") == nil, "игрок в бою")
		CarryService.LoseCarried(A, "уборка после теста")
		if shifted then
			TimeService.ResetClock()
		end
	end
)

test(
	"Босс 3 (D74): Ловибум ур. 3 → поимка → в руки без боя → постамент → доход с редкостью этажа → вход",
	function(A, _B, ctx)
		local shifted = ensureDay()
		check(waitBossHome(3), "король не дома")
		BossLootService.Handlers.Refresh()
		local uid = BossLootService.SlotItem(3, 1) :: string
		local itemId = ItemRegistry.Get(uid).itemId
		-- Ловибум другого уровня у короля не работает
		giveLovibums(A, 1, "Mega", 1)
		check(not beginCatch(A, 3, 1), "поимка у короля с Ловибумом уровня 1")
		check(A:WasNotified("уровня 3"), "нет подсказки про Ловибум уровня 3")
		check(stockOf(A, 1, "Mega") == 1, "Ловибум уровня 1 списан")
		giveLovibums(A, 3, "Boom", 2)
		local want = FloorRules.Roll(Items[itemId].rarity, 0.75)
		CatchService.Handlers.SetRoll(0)
		DevourService.Roll = function()
			return 0.75
		end
		check(beginCatch(A, 3, 1), "поимка не началась: " .. table.concat(A:Notices(), "; "))
		throw(A, "Boom", true)
		local carried = waitUntil(function()
			return ItemRegistry.GetCarriedBy(A) == uid
		end, CG.FlightTime + CG.CaptureTime + 3)
		DevourService.Roll = nil
		CatchService.Handlers.SetRoll(nil)
		check(carried, "после поимки существо не в руках")
		check(not BattleService.InBattle(A), "после поимки начался бой с королём")
		check(stockOf(A, 3, "Boom") == 1, "Ловибум ур. 3 не списан")
		check(
			want ~= "Wood" and (ItemRegistry.Get(uid) :: any).floorRarity == want,
			"редкость этажа не из броска"
		)
		local pay = IncomeService.Of(itemId, want)
		check(ItemRegistry.GetCarriedBy(A) == uid, "после победы существо не в руках")
		local part = (ItemRegistry.Get(uid) :: any).part
		check(
			part:GetAttribute("Home") == nil and part:GetAttribute("CatchMode") == nil,
			"в руках — атрибуты босса"
		)
		check(BossLootService.SlotItem(3, 1) == nil, "слот не опустел до рассвета")
		-- доставка: в серверной симуляции — переносом; путь ногами и время — проверка в Play
		local plotA = plotOf(A)
		near(A, plotA.showcases[1])
		MuseumService.Handlers.Display(A, plotA, 1)
		local entry = ItemRegistry.Get(uid)
		check(entry.state == "Displayed" and entry.slot == 1, "существо не выставлено")
		check(
			entry.part:GetAttribute("Creature") == true and entry.part:GetAttribute("Slot") == 1,
			"экспонат не существо"
		)
		local record = DataService.GetData(A).items[uid]
		check(
			record and record.id == itemId and record.boss == 3 and record.source == "boss" and record.floor == want,
			"запись в профиле неполная"
		)
		local coins = DataService.GetData(A).coins
		IncomeService.Handlers.Tick({ A })
		check(DataService.GetData(A).coins == coins + pay, "доход существа не начислен")
		local userId = A.UserId
		leave(A)
		local again = TestPlayer.new("Тест_A_снова")
		again.UserId = userId
		ctx.track(again)
		check(join(again), "A не вошёл снова")
		entry = ItemRegistry.Get(uid)
		check(
			entry
				and entry.state == "Displayed"
				and entry.slot == 1
				and entry.itemId == itemId
				and entry.floorRarity == want,
			"не восстановлено"
		)
		check(countUid(uid) == 1, "дубли существа после входа")
		check(
			entry.part:GetAttribute("Creature") == true,
			"после входа экспонат собран не существом"
		)
		coins = DataService.GetData(again).coins
		IncomeService.Handlers.Tick({ again })
		check(DataService.GetData(again).coins == coins + pay, "после входа доход не идёт")
		check(waitBossHome(3), "король не вернулся домой")
		if shifted then
			TimeService.ResetClock()
		end
	end
)

local function setMuseumLevel(player: any, level: number)
	DataService.GetData(player).museumLevel = level
	PlotService.ShowLevel(plotOf(player), level)
end

test(
	"D48: места по уровням max(6, 2 × уровень), галереи с уровня 5",
	function(A, _B, ctx)
		local plot = plotOf(A)
		for level = 1, 10 do
			setMuseumLevel(A, level)
			local standing, open = 0, 0
			for _, showcase in plot.showcases do
				if showcase.Parent then
					standing += 1
				end
				if showcase:GetAttribute("Open") then
					open += 1
				end
			end
			local expectedStanding = if level >= MuseumLayout.Gallery.Level then 20 elseif level >= 4 then 8 else 6
			check(
				standing == expectedStanding,
				("ур. %d: постаментов %d, ждали %d"):format(level, standing, expectedStanding)
			)
			check(
				open == GameConfig.Museum.SlotsByLevel[level],
				("ур. %d: открыто %d мест"):format(level, open)
			)
			check(open == math.max(6, 2 * level), ("ур. %d: формула мест"):format(level))
			check(
				MuseumService.SlotCount(A) == open,
				("ур. %d: сервер считает %d мест"):format(level, MuseumService.SlotCount(A))
			)
			local galleries = 0
			for _, module in plot.model.Building:GetChildren() do
				if
					module:GetAttribute("Module") == "D48_Gallery_L"
					or module:GetAttribute("Module") == "D48_Gallery_R"
				then
					galleries += 1
				end
			end
			check(
				galleries == (if level >= MuseumLayout.Gallery.Level then 2 else 0),
				("ур. %d: галерей %d"):format(level, galleries)
			)
		end
		-- на уровне 4 место 9 закрыто (галерей нет): выставить нельзя; на уровне 5 — можно
		setMuseumLevel(A, 4)
		near(A, plot.showcases[9])
		local uid = carry(ctx, A)
		MuseumService.Handlers.Display(A, plot, 9)
		check(ItemRegistry.Get(uid).state == "Carried", "на закрытое место 9 выставилось")
		setMuseumLevel(A, 5)
		MuseumService.Handlers.Display(A, plot, 9)
		local entry = ItemRegistry.Get(uid)
		check(
			entry.state == "Displayed" and entry.slot == 9,
			"на открытое место 9 галереи не выставилось"
		)
		check(plot.showcases[9]:GetAttribute("Occupied") == true, "место 9 не занято")
		check(DataService.GetData(A).items[uid].slot == 9, "профиль: не место 9")
	end
)

test(
	"D48: хранилище — барьер только для своего владельца, чужого выставляет сервер",
	function(A, B, _ctx)
		local plotA, plotB = plotOf(A), plotOf(B)
		local ownA, barrierA =
			VaultService.Handlers.OwnerGroup(plotA.index), VaultService.Handlers.BarrierGroup(plotA.index)
		local barrierB = VaultService.Handlers.BarrierGroup(plotB.index)
		check(VaultService.Handlers.GroupOf(A) == ownA, "группа владельца A")
		check(
			not PhysicsService:CollisionGroupsAreCollidable(ownA, barrierA),
			"A не проходит свой барьер"
		)
		check(
			PhysicsService:CollisionGroupsAreCollidable(ownA, barrierB),
			"A проходит барьер чужого хранилища B"
		)
		check(
			PhysicsService:CollisionGroupsAreCollidable("Default", barrierA),
			"посторонний проходит барьер A"
		)
		local wall = plotA.model:FindFirstChild("VaultBarrier") :: BasePart
		check(wall and wall.CanCollide and wall.CollisionGroup == barrierA, "барьер в портале A")
		VaultService.Handlers.ApplyGroup(A)
		check(A.Character.HumanoidRootPart.CollisionGroup == ownA, "персонаж A не в своей группе")
		-- чужой в хранилище A — к порталу павильона; владелец остаётся
		local inside = plotA.floorOrigin * CFrame.new(-8, MuseumLayout.Vault.Floor + 3, 10)
		B.Character.HumanoidRootPart.CFrame = inside
		A.Character.HumanoidRootPart.CFrame = inside * CFrame.new(4, 0, 0)
		check(VaultService.Handlers.Tick() >= 1, "чужого не выставили")
		local bAt = plotA.floorOrigin:PointToObjectSpace(B.Character.HumanoidRootPart.Position)
		check(bAt.Y > 0 and bAt.Z < MuseumLayout.Pavilion.Z0, "B не у портала павильона")
		check(B:WasNotified("только для владельца"), "B не получил подсказку")
		local aAt = plotA.floorOrigin:PointToObjectSpace(A.Character.HumanoidRootPart.Position)
		check(aAt.Y < 0, "владельца A выставили из своего хранилища")
		-- в павильоне за порталом — тоже
		B.Character.HumanoidRootPart.CFrame = plotA.floorOrigin * CFrame.new(0, 3, MuseumLayout.Pavilion.Z0 + 2)
		VaultService.Handlers.Tick()
		bAt = plotA.floorOrigin:PointToObjectSpace(B.Character.HumanoidRootPart.Position)
		check(bAt.Z < MuseumLayout.Pavilion.Z0, "B остался в павильоне A")
		-- окна хранилища: только владельцу и рядом
		local terminal = plotA.model:FindFirstChild("VaultTerminal") :: BasePart
		B:MoveTo(terminal.Position)
		B:ClearSent()
		VaultService.Handlers.Open(B, plotA, terminal, "Inventory")
		for _, sent in B.Sent do
			check(
				sent.name ~= Remotes.Names.OpenWindow,
				"чужому открылось окно хранилища A"
			)
		end
		A:MoveTo(terminal.Position)
		A:ClearSent()
		VaultService.Handlers.Open(A, plotA, terminal, "Inventory")
		local opened = false
		for _, sent in A.Sent do
			opened = opened or (sent.name == Remotes.Names.OpenWindow and sent.args[1] == "Inventory")
		end
		check(opened, "владельцу не открылось окно «Инвентарь»")
	end
)

test(
	"D48: лестница физическая, пол и стены хранилища — в обоих режимах графики",
	function(A, _B, _ctx)
		local plot = plotOf(A)
		local params = RaycastParams.new()
		params.FilterType = Enum.RaycastFilterType.Include
		local function probe(): string?
			params.FilterDescendantsInstances = { plot.model.Building }
			for k = 1, MuseumLayout.Stair.Steps do
				-- ступени за проёмом в полу (z > WellZ1) — под плитой пола зала: луч из-под потолка хранилища
				local z = MuseumLayout.Stair.TopZ + k - 0.5
				local from = plot.floorOrigin * Vector3.new(0, if z < MuseumLayout.Stair.WellZ1 then 4 else -2, z)
				local hit = workspace:Raycast(from, Vector3.new(0, -30, 0), params)
				local top = hit and plot.floorOrigin:PointToObjectSpace(hit.Position).Y
				if not hit or not hit.Instance.CanCollide or math.abs(top + k) > 0.05 then
					return ("ступень %d: %s"):format(k, if hit then ("%.2f"):format(top) else "нет")
				end
			end
			local floorHit = workspace:Raycast(plot.floorOrigin * Vector3.new(8, -3, 8), Vector3.new(0, -30, 0), params)
			local floorTop = floorHit and plot.floorOrigin:PointToObjectSpace(floorHit.Position).Y
			if not floorHit or math.abs(floorTop - MuseumLayout.Vault.Floor) > 0.05 then
				return "пол хранилища"
			end
			local wallHit = workspace:Raycast(plot.floorOrigin * Vector3.new(0, -6, 4), Vector3.new(40, 0, 0), params)
			if not wallHit or not wallHit.Instance.CanCollide then
				return "стена хранилища"
			end
			return nil
		end
		local reason = probe()
		check(reason == nil, "Parts: " .. tostring(reason))
		-- Mesh без MeshId: та же оболочка (столкновения), модуль показан Part-версией
		local was = GameConfig.Museum.Visual
		GameConfig.Museum.Visual = "Mesh"
		local ok, err = pcall(function()
			setMuseumLevel(A, 2)
			local meshModules = 0
			for _, module in plot.model.Building:GetChildren() do
				if module:GetAttribute("Mesh") then
					meshModules += 1
				end
			end
			check(meshModules == 0, "Mesh без MeshId: модули без мешей помечены мешами")
			local mreason = probe()
			check(mreason == nil, "Mesh без MeshId: " .. tostring(mreason))
			check(
				plot.showcases[1].Transparency == 0,
				"Mesh без MeshId: тумба места 1 стала невидимой"
			)
		end)
		GameConfig.Museum.Visual = was
		setMuseumLevel(A, 1)
		check(ok, tostring(err))
	end
)

test("D48: под хранилищем нет воды и песка (Terrain вырезан)", function(A, _B, _ctx)
	local plot = plotOf(A)
	local center = plot.floorOrigin * Vector3.new(0, MuseumLayout.Vault.Floor + 5, 4)
	local region = Region3.new(center - Vector3.new(14, 4, 12), center + Vector3.new(14, 4, 12)):ExpandToGrid(4)
	local materials, occupancy = workspace.Terrain:ReadVoxels(region, 4)
	local wet = 0
	for x = 1, materials.Size.X do
		for y = 1, materials.Size.Y do
			for z = 1, materials.Size.Z do
				local m = materials[x][y][z]
				if (m == Enum.Material.Water or m == Enum.Material.Sand) and occupancy[x][y][z] > 0 then
					wet += 1
				end
			end
		end
	end
	check(wet == 0, ("в хранилище воды и песка: %d вокселей"):format(wet))
end)

test(
	"D48: защита — зоны, галереи, лазер «Галерея», робот не бьёт через стену, дверь и галереи",
	function(A, B)
		DataService.AddCoins(A, 1e9)
		setMuseumLevel(A, 5) -- галереи и 5 устройств
		TimeService.SkipTo("Preparation", -5)
		for _, kind in { "Trap", "Laser", "Door", "Robot" } do
			settle()
			DefenseService.Handlers.Action(A, "BuyDefense", kind)
		end
		local museum = DefenseService.Handlers.Museum(A.UserId)
		-- в галерее, у арки, на дорожке, у павильона — нельзя; в боковом проходе — можно
		for _, spot in { Vector3.new(22, 0, 0), Vector3.new(-13, 0, -8), Vector3.new(0, 0, 0), Vector3.new(0, 0, 7) } do
			settle()
			DefenseService.Handlers.Action(A, "Install", "Trap", spot)
			check(
				museum.installed.Trap == nil,
				("ловушку поставили в запретное место %s"):format(tostring(spot))
			)
		end
		settle()
		DefenseService.Handlers.Action(A, "Install", "Trap", Vector3.new(-7, 0, 5))
		check(museum.installed.Trap ~= nil, "ловушка не встала в боковой проход")
		settle()
		DefenseService.Handlers.Action(A, "Install", "Laser", "Gallery")
		check(museum.installed.Laser ~= nil, "лазер «Галерея» не встал")
		settle()
		DefenseService.Handlers.Action(A, "Install", "Robot", Vector3.new(8.7, 0, 1))
		check(museum.installed.Robot ~= nil, "робот не встал в боковой проход")
		settle()
		DefenseService.Handlers.Action(A, "Install", "Door", "Entrance")
		check(museum.installed.Door ~= nil, "дверь не встала")
		TimeService.SkipTo("DoomNight", -5)
		PvpService.Handlers.Reset()
		local origin = plotOf(A).floorOrigin
		-- закрытая дверь выставляет вора и из галереи
		B.Character.PrimaryPart.CFrame = origin * CFrame.new(22, 3, 4)
		DefenseService.Handlers.Tick()
		check(
			origin:PointToObjectSpace(B.Character.PrimaryPart.Position).Z < GameConfig.Defense.Door.At.Z,
			"дверь не выставила вора из галереи"
		)
		museum.hacked = true -- дверь взломана: дальше — устройства
		local fb = PvpService.Handlers.Fighter(B)
		-- в галерее за стеной от робота (9.5 ст. — в радиусе): не бьёт
		B.Character.PrimaryPart.CFrame = origin * CFrame.new(18.2, 3, 1)
		museum.installed.Robot.lastAttack = nil
		DefenseService.Handlers.Tick()
		check(fb.hp == fb.maxHp, "робот ударил вора через стену галереи")
		-- в зале на виду: бьёт
		B.Character.PrimaryPart.CFrame = origin * CFrame.new(7, 3, -4)
		museum.installed.Robot.lastAttack = nil
		DefenseService.Handlers.Tick()
		check(fb.hp < fb.maxHp, "робот не ударил вора в зале")
		-- лазер «Галерея» поперёк дорожки
		local hp = fb.hp
		B.Character.PrimaryPart.CFrame = origin * CFrame.new(0, 3, GameConfig.Defense.Lasers.Gallery.z)
		museum.installed.Robot.broken = true -- только лазер
		DefenseService.Handlers.Tick()
		check(fb.hp < hp, "лазер «Галерея» не ударил вора на дорожке")
		TimeService.ResetClock()
	end
)

test(
	"D55 обучение: новичок при силе 0 — поимка, бой, в руки, постамент, доход; повтор входа и запреты",
	function(A, _B, ctx)
		-- A — новичок: выйти «опытным» и зайти новым профилем
		local userId = A.UserId + 7000
		local S = TestPlayer.new("Тест_ученик")
		S.UserId = userId
		ctx.track(S)
		check(PlayerSession.Join(S, { mock = true }), "ученик не вошёл")
		local t = DataService.Tutorial(S)
		check(
			t and t.step == "Intro" and t.itemId and t.uid,
			"нет записи обучения или существа"
		)
		check(
			Items[t.itemId].boss == 1 and Items[t.itemId].rarity == "Common",
			"учебное существо — не Common босса 1"
		)
		check(S:GetAttribute("Tutorial") == "Intro", "нет атрибута Tutorial")
		local uid, itemId = t.uid, t.itemId
		local p = TutorialService.Handlers.Personal(S)
		check(
			p and p.creature and p.creature:GetAttribute("TutorialOwner") == userId,
			"нет личного существа"
		)
		-- магазин и защита — отказ
		DataService.GetData(S).coins = 1e6
		ShopService.Handlers.Action(S, "Buy", 1, "Boom")
		check(CatchRules.StockOfLevel(DataService.Lovibums(S), 1) == 0, "ученик купил Ловибум")
		-- поимка: бесплатно, первое попадание — захват
		S:MoveTo(p.creature.Position + Vector3.new(0, 2, -5))
		TutorialService.Handlers.StartCatch(S)
		check(CatchService.IsCatching(S), "учебная поимка не началась")
		check(DataService.Tutorial(S).step == "Catch", "шаг не Catch")
		waitReady(S)
		throw(S, "Boom", false) -- промах бесплатный
		waitReady(S)
		throw(S, "Boom", true)
		check(
			waitUntil(function()
				return DataService.Tutorial(S).step == "Carry"
			end, 25),
			"учебный бой не закончился победой: " .. DataService.Tutorial(S).step
		)
		check(ItemRegistry.GetCarriedBy(S) == uid, "учебное существо не в руках")
		check(
			CatchRules.StockOfLevel(DataService.Lovibums(S), 1) == 0,
			"учебные броски попали в запас"
		)
		-- бросить и в сундук нельзя
		CarryService.Drop(S)
		check(
			ItemRegistry.GetCarriedBy(S) == uid and S:WasNotified("постамент"),
			"учебное существо бросили"
		)
		-- выход с существом в руках — при входе снова в руках, тот же uid
		S.Parent = nil
		PlayerSession.Leave(S)
		S.Character:Destroy()
		local S2 = TestPlayer.new("Тест_ученик_снова")
		S2.UserId = userId
		ctx.track(S2)
		check(PlayerSession.Join(S2, { mock = true }), "ученик не вошёл снова")
		check(
			DataService.Tutorial(S2).step == "Carry" and DataService.Tutorial(S2).uid == uid,
			"обучение не продолжилось с Carry"
		)
		check(
			ItemRegistry.GetCarriedBy(S2) == uid,
			"после входа существо не в руках (или другое)"
		)
		-- на постамент: в той же записи — предмет и «поставлено»
		local plot = plotOf(S2)
		near(S2, plot.showcases[1])
		MuseumService.Handlers.Display(S2, plot, 1)
		local data = DataService.GetData(S2)
		check(data.items[uid] and data.items[uid].id == itemId, "предмет не записан")
		check(
			data.tutorial.step == "Income" and data.tutorial.placed == true,
			"«поставлено» не записано вместе с предметом"
		)
		-- кража стартового — отказ (TheftLedger.protected)
		check(TutorialRules.IsProtected(data, uid), "стартовое существо без защиты")
		-- первый доход — обучение пройдено
		IncomeService.Handlers.Tick({ S2 })
		check(
			data.tutorial.step == "Done",
			"обучение не завершилось по первому доходу"
		)
		check(S2:GetAttribute("Tutorial") == nil, "атрибут Tutorial остался")
		check(TutorialRules.IsProtected(data, uid), "после обучения защита пропала")
		ShopService.Handlers.Action(S2, "Buy", 1, "Boom")
		check(
			CatchRules.Stock(DataService.Lovibums(S2), 1, "Boom") == 3,
			"после обучения магазин не открылся (набор ×3)"
		)
	end
)

test(
	"D55 обучение: выход и вход на каждом шаге, ночь, чужой игрок, занятые руки — существо одно",
	function(_A, B, ctx)
		local TG = GameConfig.Catch.Tutorial
		local S = TestPlayer.new("Тест_ученик_1") -- свежий UserId: профиля ещё нет
		local userId = S.UserId
		local n = 1
		local function enter(player: any): any
			ctx.track(player)
			check(PlayerSession.Join(player, { mock = true }), player.Name .. " не вошёл")
			return player
		end
		local function rejoin(old: any): any
			leave(old)
			n += 1
			local again = TestPlayer.new("Тест_ученик_" .. n)
			again.UserId = userId
			return enter(again)
		end
		local function step(player: any): string
			return (DataService.Tutorial(player) :: any).step
		end
		-- учебных существ (ItemId) и псов ученика в мире
		local function personalCount(): (number, number)
			local creatures, dogs = 0, 0
			for _, d in workspace:GetDescendants() do
				if d:GetAttribute("TutorialOwner") == userId then
					if d:GetAttribute("ItemId") ~= nil then
						creatures += 1
					elseif d:IsA("Model") then
						dogs += 1
					end
				end
			end
			return creatures, dogs
		end
		local function toCreature(player: any)
			local p = TutorialService.Handlers.Personal(player)
			check(p and p.creature, player.Name .. ": нет учебного существа")
			player:MoveTo(p.creature.Position + Vector3.new(0, 2, -5))
		end
		local function catchIt(player: any)
			toCreature(player)
			TutorialService.Handlers.StartCatch(player)
			check(CatchService.IsCatching(player), player.Name .. ": учебная поимка не началась")
			waitReady(player)
			throw(player, "Boom", true)
		end

		-- Intro: выбор существа не меняется, существо одно
		enter(S)
		local t = DataService.Tutorial(S) :: any
		local uid, itemId = t.uid, t.itemId
		check(t.step == "Intro" and uid and itemId, "нет записи обучения")
		S = rejoin(S)
		t = DataService.Tutorial(S) :: any
		check(
			t.step == "Intro" and t.uid == uid and t.itemId == itemId,
			"вход на Intro сменил шаг или существо"
		)
		check(
			personalCount() == 1,
			"учебных существ после входа на Intro: " .. personalCount()
		)

		-- Catch, посреди поимки: чужой не мешает, ночь не прерывает; выход — снова поимка, ничего не выдано
		toCreature(S)
		B:MoveTo(S.Character.PrimaryPart.Position + Vector3.new(3, 0, 0))
		TutorialService.Handlers.Prompt(S, B) -- чужой нажал «Поймать» у учебного существа S
		check(
			not CatchService.IsCatching(B) and not CatchService.IsCatching(S),
			"чужое нажатие начало учебную поимку"
		)
		TutorialService.Handlers.StartCatch(S)
		check(CatchService.IsCatching(S), "учебная поимка не началась")
		local session = (CatchService.Handlers.Active(S) :: any).session
		local throwsBefore = session.throws
		CatchService.Handlers.Action(B, "Leave") -- чужие запросы поимки — только к своей (у B её нет)
		TutorialService.Handlers.Prompt(S, B)
		check(
			CatchService.Handlers.Active(S) and session.throws == throwsBefore,
			"чужой изменил учебную поимку"
		)
		TimeService.SkipTo("Night", 0)
		check(GameTime.IsNight(TimeService.Current().phase), "ночь не наступила")
		check(CatchService.IsCatching(S), "ночь или чужой прервали учебную поимку")
		TimeService.ResetClock()
		waitReady(S)
		throw(S, "Boom", false) -- промах: бесплатный
		local catching = S
		S = rejoin(S)
		check(
			CatchService.Handlers.Active(catching) == nil,
			"поимка ушедшего не закончилась"
		)
		check(step(S) == "Catch", "вход посреди поимки: шаг " .. step(S))
		check(ItemRegistry.Get(uid) == nil, "за прерванную поимку выдано существо")
		check(
			personalCount() == 1,
			"учебных существ после входа посреди поимки: " .. personalCount()
		)

		-- Battle, посреди боя: выход — снова поимка, старый бой ничего не выдаёт
		catchIt(S)
		check(
			waitUntil(function()
				local p = TutorialService.Handlers.Personal(S)
				return p ~= nil and p.dog ~= nil and p.fighting
			end, 20),
			"учебный бой не начался"
		)
		task.wait(TG.FightStep * 2)
		local fighting = S
		S = rejoin(S)
		check(step(S) == "Catch", "вход посреди боя: шаг " .. step(S))
		task.wait(TG.FightStep * 2) -- старый бой замечает уход
		check(
			TutorialService.Handlers.Personal(fighting) == nil,
			"учебные объекты ушедшего остались"
		)
		check(
			ItemRegistry.Get(uid) == nil and DataService.GetData(S).items[uid] == nil,
			"прерванный бой выдал существо"
		)
		local creatures, dogs = personalCount()
		check(
			creatures == 1 and dogs == 0,
			("после входа посреди боя: существ %d, псов %d"):format(creatures, dogs)
		)

		-- занятые руки: поимка — отказ; подобранное за время боя при выдаче — на земле, не пропало
		toCreature(S)
		local other = carry(ctx, S)
		TutorialService.Handlers.StartCatch(S)
		check(
			not CatchService.IsCatching(S) and S:WasNotified("Руки заняты"),
			"учебная поимка с занятыми руками"
		)
		CarryService.Drop(S)
		check(ItemRegistry.GetCarriedBy(S) == nil, "чужой предмет не бросился")
		catchIt(S)
		check(
			waitUntil(function()
				return step(S) == "Battle"
			end, 10),
			"бой не начался: " .. step(S)
		)
		task.wait(1.1) -- лимит подбора
		CarryService.Handlers.Pickup(S, other)
		check(ItemRegistry.GetCarriedBy(S) == other, "в бою не поднял предмет")
		check(
			waitUntil(function()
				return step(S) == "Carry"
			end, 25),
			"учебный бой не закончился победой: " .. step(S)
		)
		check(ItemRegistry.GetCarriedBy(S) == uid, "учебное существо не в руках")
		local otherEntry = ItemRegistry.Get(other)
		check(
			otherEntry and otherEntry.state == "OnMap",
			"подобранное в бою пропало при выдаче существа"
		)

		-- Carry ночью в коридоре: существо при нём, не переносят; чужой не поднимет
		local at = S.Character.PrimaryPart.Position
		check(MapLayout.InDangerZone(at), "место обучения не в коридоре")
		local day = GameTime.At(GameConfig.Time.Epoch)
		local nightState = GameTime.At(GameConfig.Time.Epoch + GameConfig.Time.DayLength)
		NightService.Handlers.Apply(nightState, day, { S })
		check(ItemRegistry.GetCarriedBy(S) == uid, "ночь отняла учебное существо")
		check(NightService.Handlers.Sweep({ S }) == 0, "ученика ночью вывели из коридора")
		check((S.Character.PrimaryPart.Position - at).Magnitude < 0.01, "ученика ночью перенесли")
		NightService.Handlers.Apply(TimeService.Current(), nil, {})
		CarryService.Handlers.Pickup(B, uid)
		check(
			ItemRegistry.GetCarriedBy(S) == uid,
			"чужой забрал учебное существо из рук"
		)

		-- гибель с существом в руках: на землю не падает (не подобрать чужим), после возрождения — снова в руках тот же uid
		local humanoid = S.Character:FindFirstChildOfClass("Humanoid") :: Humanoid
		humanoid.Health = 0
		CarryService.Drop(S) -- как при Died (CarryService.watchCharacter)
		check(
			S:WasNotified("после возрождения"),
			"нет сообщения о возврате существа"
		)
		task.wait() -- отложенная потеря
		check(
			ItemRegistry.GetCarriedBy(S) == nil and ItemRegistry.Get(uid) == nil,
			"у погибшего существо в руках или на земле"
		)
		humanoid:Destroy() -- «возродился»: погибший Humanoid не оживает — новый, как у нового персонажа
		local fresh = Instance.new("Humanoid")
		fresh.RequiresNeck = false
		fresh.Parent = S.Character
		check(
			waitUntil(function()
				return ItemRegistry.GetCarriedBy(S) == uid
			end, 3),
			"после возрождения существо не в руках"
		)
		check(
			DataService.GetData(S).items[uid] == nil,
			"существо попало в профиль до постамента"
		)

		-- выход с существом в руках — снова в руках, тот же uid, второго нет
		S = rejoin(S)
		check(step(S) == "Carry" and ItemRegistry.GetCarriedBy(S) == uid, "вход на Carry: не в руках")
		check(
			personalCount() == 0,
			"учебное существо на месте обучения осталось при Carry"
		)

		-- постамент в Судную ночь (экспонаты заперты): стартовое ставится
		local plot = plotOf(S)
		near(S, plot.showcases[1])
		TimeService.SkipTo("DoomNight", -5)
		check(GameTime.ExhibitLock(GameTime.Now()), "экспонаты не заперты")
		MuseumService.Handlers.Display(S, plot, 1)
		local data = DataService.GetData(S)
		check(
			data.items[uid] and data.tutorial.step == "Income" and data.tutorial.placed,
			"в Судную ночь не поставилось"
		)
		-- до первого дохода стартовое не снять в инвентарь (днём, когда экспонаты не заперты)
		TimeService.SkipTo("Day", -(GameConfig.Time.DeliveryGrace + 5))
		settle()
		InventoryService.Handlers.StoreDisplayed(S, plot, 1)
		check(
			ItemRegistry.Get(uid).state == "Displayed" and S:WasNotified("первого дохода"),
			"стартовое сняли до дохода"
		)
		TimeService.ResetClock()

		-- Income: выход до первого дохода — экспонат на месте, в руки второй раз не выдаётся
		S = rejoin(S)
		data = DataService.GetData(S)
		local entry = ItemRegistry.Get(uid)
		check(step(S) == "Income" and data.items[uid], "вход на Income: шаг " .. step(S))
		check(
			entry and entry.state == "Displayed" and entry.owner == userId,
			"после входа экспонат не на витрине"
		)
		check(
			ItemRegistry.GetCarriedBy(S) == nil,
			"после входа на Income существо снова в руках (дубль)"
		)
		IncomeService.Handlers.Tick({ S })
		check(step(S) == "Done", "первый доход не завершил обучение")

		-- Done: ничего не появляется, в профиле — один предмет
		S = rejoin(S)
		data = DataService.GetData(S)
		local count = 0
		for _ in data.items do
			count += 1
		end
		check(
			step(S) == "Done" and S:GetAttribute("Tutorial") == nil,
			"вход после Done: обучение снова"
		)
		check(
			TutorialService.Handlers.Personal(S) == nil and personalCount() == 0,
			"после Done — учебные объекты"
		)
		check(
			count == 1 and data.items[uid] and ItemRegistry.Get(uid).state == "Displayed",
			"предметов в профиле: " .. count
		)
		check(TutorialRules.IsProtected(data, uid), "у стартового нет защиты")
	end
)

-- D56: защита привязана к уровню музея ───────────────────────────────────────────────────────────────────────

-- Последнее состояние защиты, отправленное игроку (DefenseChanged).
local function lastDefense(player: any): any
	local payload = nil
	for _, event in player.Sent do
		if event.name == "DefenseChanged" then
			payload = event.args[1]
		end
	end
	return payload
end

test(
	"D56 защита: устройство привязано к уровню музея при покупке — на другом уровне не ставится и не пропадает",
	function(A)
		local cfg = GameConfig.Defense
		local data = DataService.GetData(A)
		local museum = DefenseService.Handlers.Museum(A.UserId)
		local spot = Vector3.new(5, 0, 5)
		DataService.AddCoins(A, 1e9)
		TimeService.SkipTo("Preparation", -5)
		-- музей уровня 1: две ловушки по цене уровня 1, запас записан за уровнем 1
		local before = data.coins
		for _ = 1, 2 do
			settle()
			DefenseService.Handlers.Action(A, "BuyDefense", "Trap")
		end
		local defense = DataService.Defense(A)
		check(
			defense.owned.Trap.L1 == 2,
			"покупка на уровне 1 не записана за уровнем 1"
		)
		check(data.coins == before - 2 * DefenseRules.Price(cfg, "Trap", 1), "цена — не уровня 1")
		settle()
		DefenseService.Handlers.Action(A, "Install", "Trap", spot)
		check(
			museum.installed.Trap ~= nil and defense.owned.Trap.L1 == 1,
			"до повышения ловушка не встала"
		)
		check(
			defense.installed.Trap.level == 1,
			"у установленной не записан уровень покупки"
		)
		settle()
		DefenseService.Handlers.Action(A, "Remove", "Trap")
		check(
			museum.installed.Trap == nil and defense.owned.Trap.L1 == 2,
			"снятая не вернулась в запас уровня 1"
		)
		-- музей стал уровня 2 (в игре — покупкой уровня днём; здесь — как после неё): старые не ставятся и не пропадают
		setMuseumLevel(A, 2)
		A:ClearSent()
		settle()
		DefenseService.Handlers.Action(A, "Install", "Trap", spot)
		check(museum.installed.Trap == nil, "ловушка уровня 1 встала на музей уровня 2")
		check(
			A:WasNotified("другого уровня"),
			"нет причины отказа про другой уровень"
		)
		defense = DataService.Defense(A)
		check(
			defense.owned.Trap.L1 == 2 and defense.owned.Trap.L2 == nil,
			"старые устройства изменились"
		)
		DefenseService.Sync(A)
		local sent = lastDefense(A)
		check(sent and sent.level == 2 and sent.max == 2, "окну не пришёл уровень 2")
		check(sent.owned.Trap == nil, "окно считает ловушки уровня 1 годными")
		check(
			sent.stale.Trap
				and #sent.stale.Trap == 1
				and sent.stale.Trap[1].level == 1
				and sent.stale.Trap[1].count == 2,
			"окну не пришли устройства прежнего уровня"
		)
		-- покупка на уровне 2: цена уровня 2, запас уровня 2; ставится
		before = data.coins
		settle()
		DefenseService.Handlers.Action(A, "BuyDefense", "Trap")
		check(data.coins == before - DefenseRules.Price(cfg, "Trap", 2), "цена — не уровня 2")
		check(
			defense.owned.Trap.L2 == 1 and defense.owned.Trap.L1 == 2,
			"покупка на уровне 2 смешалась с уровнем 1"
		)
		settle()
		DefenseService.Handlers.Action(A, "Install", "Trap", spot)
		check(
			museum.installed.Trap ~= nil and defense.installed.Trap.level == 2,
			"ловушка уровня 2 не встала"
		)
		check(
			defense.owned.Trap.L2 == nil and defense.owned.Trap.L1 == 2,
			"списано не из запаса уровня 2"
		)
		-- прежние ограничения действуют: каждого вида одно, не больше min(уровень, 5)
		for _, kind in { "Trap", "Laser", "Door" } do
			settle()
			DefenseService.Handlers.Action(A, "BuyDefense", kind)
		end
		A:ClearSent()
		settle()
		DefenseService.Handlers.Action(A, "Install", "Trap", Vector3.new(-5, 0, 5))
		check(
			A:WasNotified("уже стоит") and defense.owned.Trap.L2 == 1,
			"вторая ловушка встала"
		)
		settle()
		DefenseService.Handlers.Action(A, "Install", "Laser", "Entrance")
		check(museum.installed.Laser ~= nil, "второе устройство на уровне 2 не встало")
		A:ClearSent()
		settle()
		DefenseService.Handlers.Action(A, "Install", "Door", "Entrance")
		check(
			museum.installed.Door == nil and A:WasNotified("Больше устройств"),
			"третье устройство на уровне 2 встало"
		)
		-- вышел до ночи: каждое возвращается в запас своего уровня покупки, даже если уровень музея уже другой
		data.museumLevel = 3
		DefenseService.OnPlayerLeaving(A)
		defense = DataService.Defense(A)
		check(
			defense.owned.Trap.L2 == 2 and defense.owned.Laser.L2 == 1,
			"вернулось не в запас уровня покупки"
		)
		check(
			defense.owned.Trap.L1 == 2 and defense.owned.Trap.L3 == nil,
			"возврат задел другие уровни"
		)
		check(next(defense.installed) == nil, "запись об установке осталась")
	end
)

test(
	"D56 защита: после Судной ночи установленное исчезает, запас прежних уровней остаётся",
	function(A)
		DataService.AddCoins(A, 1e9)
		TimeService.SkipTo("Preparation", -5)
		settle()
		DefenseService.Handlers.Action(A, "BuyDefense", "Trap") -- уровень 1
		setMuseumLevel(A, 2)
		for _ = 1, 2 do
			settle()
			DefenseService.Handlers.Action(A, "BuyDefense", "Trap") -- уровень 2
		end
		settle()
		DefenseService.Handlers.Action(A, "Install", "Trap", Vector3.new(5, 0, 5))
		local museum = DefenseService.Handlers.Museum(A.UserId)
		check(museum.installed.Trap ~= nil, "ловушка уровня 2 не встала")
		TimeService.SkipTo("DoomNight", -2)
		DefenseService.Handlers.EndNight()
		local defense = DataService.Defense(A)
		check(
			next(museum.installed) == nil and next(defense.installed) == nil,
			"после ночи защита осталась"
		)
		check(defense.owned.Trap.L2 == 1, "после ночи запас уровня 2 — не 1")
		check(defense.owned.Trap.L1 == 1, "после ночи пропало устройство уровня 1")
	end
)

test(
	"D56 миграция: защита прежнего формата получает сохранённый уровень музея, ничего не теряется",
	function(_A, _B, ctx)
		-- профиль v4 сохранён прежним сервером: запас — числа без уровня, установленное — номер круга; музей уровня 3
		local store = ProfileStore.New(GameConfig.Data.StoreName, ProfileTemplate).Mock
		local C = TestPlayer.new("Тест_C_v4")
		ctx.track(C)
		local cycle = GameTime.Current().cycle
		local old = store:StartSessionAsync(GameConfig.Data.KeyPrefix .. C.UserId)
		check(old ~= nil, "сессия прежнего профиля не открылась")
		old.Data.schema = 4
		old.Data.coins = 5000
		old.Data.museumLevel = 3
		old.Data.tutorial = { step = "Done", migrated = true }
		old.Data.defense = {
			owned = { Trap = 2, Robot = 1, Snare = 0 },
			hacks = { L2 = 1 },
			-- дверь стояла к ещё не наступившей ночи (вернётся), лазер — к прошедшей (отработал)
			installed = { Door = cycle, Laser = cycle - 1 },
		}
		old:EndSession()
		check(join(C), "игрок со старым профилем не вошёл")
		local data = DataService.GetData(C)
		local defense = data.defense
		check(data.schema == 5, "схема не 5")
		check(
			data.museumLevel == 3 and data.coins == 5000,
			"уровень музея или монеты изменились"
		)
		check(
			type(defense.owned.Trap) == "table" and defense.owned.Trap.L3 == 2,
			"ловушки не привязаны к уровню 3"
		)
		check(defense.owned.Robot.L3 == 1, "робот не привязан к уровню 3")
		check(defense.owned.Trap.L1 == nil, "устройства записаны за уровнем 1")
		check(
			defense.owned.Door and defense.owned.Door.L3 == 1,
			"дверь, стоявшая до ночи, не вернулась на уровень 3"
		)
		check(
			defense.owned.Laser == nil or defense.owned.Laser.L3 == nil,
			"лазер, отработавший ночь, вернулся"
		)
		check(defense.hacks.L2 == 1, "устройство взлома потеряно")
		check(next(defense.installed) == nil, "запись об установке осталась")
		local sent = lastDefense(C)
		check(
			sent and sent.level == 3 and sent.owned.Trap == 2 and sent.owned.Door == 1,
			"окну пришёл не запас уровня 3"
		)
		check(
			next(sent.stale) == nil,
			"у мигрировавшего профиля есть «чужие» уровни"
		)
		-- повторный вход ничего не меняет (миграция один раз)
		local userId = C.UserId
		leave(C)
		local again = TestPlayer.new("Тест_C_v5")
		again.UserId = userId
		ctx.track(again)
		check(join(again), "повторный вход не удался")
		defense = DataService.Defense(again)
		check(DataService.GetData(again).schema == 5, "схема после повторного входа")
		check(
			defense.owned.Trap.L3 == 2 and defense.owned.Robot.L3 == 1 and defense.owned.Door.L3 == 1,
			"запас изменился"
		)
		check(defense.hacks.L2 == 1, "взлом изменился после повторного входа")
		-- на музее уровня 3 мигрировавшие устройства ставятся; после повышения до 4 — уже нет
		TimeService.SkipTo("Preparation", -5)
		settle()
		DefenseService.Handlers.Action(again, "Install", "Trap", Vector3.new(5, 0, 5))
		local museum = DefenseService.Handlers.Museum(again.UserId)
		check(
			museum.installed.Trap ~= nil and defense.owned.Trap.L3 == 1,
			"мигрировавшая ловушка не встала на уровне 3"
		)
		settle()
		DefenseService.Handlers.Action(again, "Remove", "Trap")
		setMuseumLevel(again, 4)
		settle()
		DefenseService.Handlers.Action(again, "Install", "Trap", Vector3.new(5, 0, 5))
		check(
			museum.installed.Trap == nil and DataService.Defense(again).owned.Trap.L3 == 2,
			"ловушка уровня 3 встала на уровне 4"
		)
	end
)

-- D56: покупка уровней музея 2–10 ────────────────────────────────────────────────────────────────────────────
do
	local MuseumRules = require(ReplicatedStorage.Shared.MuseumRules)
	local MuseumUpgradeService = require(Server.Services.MuseumUpgradeService)
	local NumberFormat = require(ReplicatedStorage.Shared.NumberFormat)
	local prices = GameConfig.Progression.Museum.Prices
	local Upgrade = MuseumUpgradeService.Handlers.Upgrade

	-- Последний ответ сервера на «Улучшить музей» (MuseumUpgradeResult).
	local function lastUpgrade(player: any): any
		local payload = nil
		for _, event in player.Sent do
			if event.name == "MuseumUpgradeResult" then
				payload = event.args[1]
			end
		end
		return payload
	end

	-- Открытых мест и стоящих постаментов на участке.
	local function places(plot: PlotService.Plot): (number, number)
		local open, standing = 0, 0
		for _, showcase in plot.showcases do
			if showcase.Parent then
				standing += 1
			end
			if showcase:GetAttribute("Open") then
				open += 1
			end
		end
		return open, standing
	end

	local function money(n: number): string
		return "$" .. NumberFormat.Short(n)
	end

	test(
		"D56 музей: уровни 1 → 10 по одному — цена списана ровно, места открыты, здание одно; на 10 покупки нет",
		function(A, B, ctx)
			local data = DataService.GetData(A)
			local plot = plotOf(A)
			local total = 0
			for _, price in prices do
				total += price
			end
			DataService.AddCoins(A, total + 12345)
			check(
				data.museumLevel == 1 and A:GetAttribute("MuseumLevel") == 1,
				"новый игрок не на уровне 1"
			)
			for level = 1, 9 do
				local before = data.coins
				local openBefore = places(plot)
				A:ClearSent()
				Upgrade(A, level + 1)
				local open, standing = places(plot)
				check(data.museumLevel == level + 1, ("уровень %d не куплен"):format(level + 1))
				check(
					before - data.coins == prices[level],
					("ур. %d: списано %s, цена %s"):format(level + 1, before - data.coins, prices[level])
				)
				check(
					open == math.min(20, math.max(6, 2 * (level + 1))),
					("ур. %d: открыто %d мест"):format(level + 1, open)
				)
				check(open >= openBefore, ("ур. %d: мест стало меньше"):format(level + 1))
				check(
					MuseumService.SlotCount(A) == open,
					("ур. %d: сервер считает другое число мест"):format(level + 1)
				)
				check(
					A:GetAttribute("MuseumSlots") == open and A:GetAttribute("MuseumLevel") == level + 1,
					("ур. %d: атрибуты игрока не обновлены"):format(level + 1)
				)
				check(
					A:GetAttribute("Coins") == data.coins,
					("ур. %d: атрибут монет отстал"):format(level + 1)
				)
				check(
					plot.level == level + 1 and plot.model:GetAttribute("MuseumLevel") == level + 1,
					("ур. %d: участок не перестроен"):format(level + 1)
				)
				local buildings, galleries = 0, 0
				for _, child in plot.model:GetChildren() do
					if child.Name == "Building" then
						buildings += 1
					end
				end
				for _, module in plot.model.Building:GetChildren() do
					local name = module:GetAttribute("Module")
					if name == "D48_Gallery_L" or name == "D48_Gallery_R" then
						galleries += 1
					end
				end
				check(buildings == 1, ("ур. %d: зданий %d"):format(level + 1, buildings))
				check(
					galleries == (if level + 1 >= MuseumLayout.Gallery.Level then 2 else 0),
					("ур. %d: галерей %d"):format(level + 1, galleries)
				)
				local sent = lastUpgrade(A)
				check(
					sent
						and sent.ok == true
						and sent.level == level + 1
						and sent.slots == open
						and sent.coins == data.coins,
					("ур. %d: ответ окну не совпал с профилем"):format(level + 1)
				)
				check(
					A:WasNotified("Музей улучшен"),
					("ур. %d: нет уведомления"):format(level + 1)
				)
				ctx.note(
					("ур. %d → %d: −%s, мест %d → %d, постаментов стоит %d"):format(
						level,
						level + 1,
						money(prices[level]),
						openBefore,
						open,
						standing
					)
				)
			end
			check(
				data.coins == 12345,
				"после всех покупок остаток не 12345: " .. tostring(data.coins)
			)
			ctx.note(
				("всего списано %s, остаток $12 345 — до монеты"):format(money(total))
			)
			-- чужой музей не затронут
			check(DataService.GetData(B).museumLevel == 1 and plotOf(B).level == 1, "музей B изменился")
			-- максимум: покупки нет, монеты на месте
			for _, requested in { 11, 10, 2 } do
				A:ClearSent()
				Upgrade(A, requested)
				local sent = lastUpgrade(A)
				check(data.museumLevel == 10 and data.coins == 12345, "на уровне 10 что-то списано")
				check(
					sent and sent.ok == false and sent.code == MuseumRules.Codes.Max,
					"на уровне 10 нет отказа «Max»"
				)
			end
			check(
				A:WasNotified("максимального уровня"),
				"нет сообщения о максимальном уровне"
			)
			ctx.note(
				"уровень 10: запросы 11, 10 и 2 — отказ «максимальный уровень», монеты не тронуты"
			)
		end
	)

	test(
		"D56 музей: не хватает монет — ничего не меняется; ровно цена — покупается; в обучении — закрыто",
		function(A)
			local data = DataService.GetData(A)
			local plot = plotOf(A)
			local building = plot.model:FindFirstChild("Building")
			check(data.coins == 0, "у нового игрока есть монеты")
			for _, coins in { 0, 1, prices[1] - 1 } do
				DataService.AddCoins(A, coins - data.coins)
				A:ClearSent()
				Upgrade(A, 2)
				local sent = lastUpgrade(A)
				check(
					data.museumLevel == 1 and data.coins == coins,
					("с %d монетами что-то изменилось"):format(coins)
				)
				check(
					sent and sent.ok == false and sent.code == MuseumRules.Codes.Coins,
					"нет отказа «Coins»"
				)
				check(sent.level == 1 and sent.coins == coins, "ответ окну — не из профиля")
				check(
					A:WasNotified("Не хватает монет"),
					"нет сообщения о нехватке монет"
				)
				check(
					plot.model:FindFirstChild("Building") == building,
					"здание перестроилось без покупки"
				)
			end
			DataService.AddCoins(A, 1) -- ровно цена
			Upgrade(A, 2)
			check(
				data.museumLevel == 2 and data.coins == 0,
				"ровно цена: уровень 2 не куплен или монеты не списаны"
			)
			-- обучение: закрыто, как «Защита» и «Магазин»
			DataService.AddCoins(A, prices[2])
			A:SetAttribute("Tutorial", "Catch")
			A:ClearSent()
			Upgrade(A, 3)
			local sent = lastUpgrade(A)
			check(data.museumLevel == 2 and data.coins == prices[2], "в обучении уровень куплен")
			check(
				sent and sent.code == MuseumRules.Codes.Tutorial and A:WasNotified("после обучения"),
				"нет отказа обучения"
			)
			A:SetAttribute("Tutorial", nil)
			Upgrade(A, 3)
			check(
				data.museumLevel == 3 and data.coins == 0,
				"после обучения уровень 3 не куплен"
			)
		end
	)

	test(
		"D56 музей: повторные, одновременные и поддельные запросы — одно списание; лимит запросов",
		function(A, B)
			local data = DataService.GetData(A)
			DataService.AddCoins(A, 1e9)
			local start = data.coins
			-- двойное нажатие: два запроса уровня 2 в одном кадре
			Upgrade(A, 2)
			Upgrade(A, 2)
			check(
				data.museumLevel == 2 and start - data.coins == prices[1],
				"двойное нажатие списало дважды или купило два уровня"
			)
			A:ClearSent()
			Upgrade(A, 2)
			local sent = lastUpgrade(A)
			check(
				sent and sent.ok == false and sent.code == MuseumRules.Codes.Stale and sent.level == 2,
				"повтор не отклонён как устаревший"
			)
			check(
				#A:Notices() == 0,
				"на повторное нажатие игроку пришло лишнее уведомление"
			)
			-- три запроса уровня 3 одновременно (разные потоки, один кадр)
			for _ = 1, 3 do
				task.spawn(Upgrade, A, 3)
			end
			check(
				data.museumLevel == 3 and start - data.coins == prices[1] + prices[2],
				"одновременные запросы: уровень " .. tostring(data.museumLevel)
			)
			-- подделки: через уровень, текущий, ниже, дробь, строка, NaN, таблица, огромное, отрицательное, ничего
			local before = data.coins
			for _, forged in { 5, 3, 1, 3.5, "4", 0 / 0, {}, 1e9, -1, math.huge, true } do
				Upgrade(A, forged)
			end
			Upgrade(A, nil)
			check(
				data.museumLevel == 3 and data.coins == before,
				"поддельный запрос изменил уровень или монеты"
			)
			-- клиент не задаёт цену и монеты: лишние аргументы не читаются, цена — из конфига
			local withExtra: any = Upgrade
			withExtra(A, 4, 0, 1e15)
			check(
				data.museumLevel == 4 and before - data.coins == prices[3],
				"цена взята не из конфига"
			)
			-- запрос игрока B меняет только музей B (чужой музей запросом не указать)
			local dataB = DataService.GetData(B)
			Upgrade(B, 2)
			check(
				dataB.museumLevel == 1 and data.museumLevel == 4,
				"запрос B без монет что-то изменил"
			)
			DataService.AddCoins(B, prices[1])
			Upgrade(B, 2)
			check(
				dataB.museumLevel == 2 and dataB.coins == 0 and data.museumLevel == 4,
				"покупка B задела A"
			)
			-- лимит запросов (вход RemoteEvent): 10 запросов подряд — проходят не больше лимита в секунду
			task.wait(1.1) -- полное «ведро» лимита
			before = data.coins
			local level = data.museumLevel
			for _ = 1, 10 do
				MuseumUpgradeService.Handlers.Request(A, data.museumLevel + 1)
			end
			local bought = data.museumLevel - level
			check(
				bought == GameConfig.RateLimits.MuseumUpgrade,
				("лимит запросов: куплено %d уровней за кадр"):format(bought)
			)
			check(
				before - data.coins == prices[4] + prices[5],
				"лимит запросов: списано не за два уровня"
			)
		end
	)

	test(
		"D56 музей: в подготовку, Судную ночь и 10 с после неё покупки нет (сервер); днём и обычной ночью — есть",
		function(A, _B, ctx)
			local data = DataService.GetData(A)
			local time = GameConfig.Time
			DataService.AddCoins(A, 1e9)
			local function locked(label: string, word: string)
				local before = data.coins
				local level = data.museumLevel
				A:ClearSent()
				Upgrade(A, level + 1)
				local sent = lastUpgrade(A)
				check(data.museumLevel == level and data.coins == before, label .. ": уровень куплен")
				check(
					sent and sent.ok == false and sent.code == MuseumRules.Codes.Locked,
					label .. ": нет отказа «Locked»"
				)
				check(A:WasNotified(word), label .. ": нет причины для игрока")
				ctx.note(("%s (%s) — отказ: «%s»"):format(label, GameTime.Current().phase, sent.message))
			end
			local function open(label: string)
				local before = data.coins
				local level = data.museumLevel
				Upgrade(A, level + 1)
				check(
					data.museumLevel == level + 1 and before - data.coins == prices[level],
					label .. ": уровень не куплен"
				)
				ctx.note(
					("%s (%s) — куплен уровень %d"):format(label, GameTime.Current().phase, level + 1)
				)
			end
			TimeService.SkipTo("Preparation", 1)
			check(GameTime.Current().phase == "Day", "за секунду до подготовки — не день")
			open("за 1 с до подготовки")
			TimeService.SkipTo("Preparation", -1)
			locked("1-я секунда подготовки", "Подготовка")
			TimeService.SkipTo("Preparation", -(time.PreparationLength - 1))
			locked("последняя секунда подготовки", "Подготовка")
			TimeService.SkipTo("DoomNight", -1)
			locked("1-я секунда Судной ночи", "Судная ночь")
			TimeService.SkipTo("DoomNight", -(time.DoomNightLength - 1))
			locked("последняя секунда Судной ночи", "Судная ночь")
			TimeService.SkipTo("Day", -1)
			check(
				GameTime.Current().phase == "Day" and GameTime.DeliveryWindowEnd(GameTime.Now()),
				"не окно 10 с после ночи"
			)
			locked("1-я секунда после Судной ночи", "закончилась")
			TimeService.SkipTo("DoomNight", -1)
			TimeService.SkipTo("Day", -(time.DeliveryGrace - 1))
			locked("9-я секунда после Судной ночи", "закончилась")
			TimeService.SkipTo("DoomNight", -1)
			TimeService.SkipTo("Day", -(time.DeliveryGrace + 1))
			open("11-я секунда после Судной ночи")
			TimeService.SkipTo("Night", -5)
			check(GameTime.Current().phase == "Night", "не обычная ночь")
			open("обычная ночь")
			check(data.museumLevel == 4, "итог: уровень " .. tostring(data.museumLevel))
			TimeService.SkipTo("Day", -5)
		end
	)

	test(
		"D56 музей: уровень, монеты, экспонаты и доход переживают выход и вход — без потерь и дублей",
		function(A, _B, ctx)
			local plot = plotOf(A)
			local a1 = displayOwn(ctx, A, 1)
			local a6 = displayOwn(ctx, A, 6)
			local stored = toInventory(ctx, A)
			local data = DataService.GetData(A)
			local income = IncomeService.TotalFor(A.UserId)
			local power = GymService.MuseumPower(A)
			check(
				income == 2 * IncomeService.Of(TEST_ITEM),
				"доход двух экспонатов до улучшения"
			)
			DataService.AddCoins(A, prices[1] + prices[2] + prices[3] + prices[4] + 500 - data.coins)
			for level = 1, 4 do
				Upgrade(A, level + 1)
				-- после каждой покупки: те же предметы на тех же местах, доход и бонус силы те же
				local e1, e6, es = ItemRegistry.Get(a1), ItemRegistry.Get(a6), ItemRegistry.Get(stored)
				check(
					e1 and e1.state == "Displayed" and e1.slot == 1,
					("ур. %d: экспонат места 1 сдвинулся"):format(level + 1)
				)
				check(
					e6 and e6.state == "Displayed" and e6.slot == 6,
					("ур. %d: экспонат места 6 сдвинулся"):format(level + 1)
				)
				check(
					es and es.state == "Stored",
					("ур. %d: предмет инвентаря изменился"):format(level + 1)
				)
				check(
					countUid(a1) == 1 and countUid(a6) == 1 and countUid(stored) == 0,
					("ур. %d: дубль или потеря"):format(level + 1)
				)
				check(
					#plot.exhibits:GetChildren() == 2,
					("ур. %d: экспонатов на участке не 2"):format(level + 1)
				)
				check(
					IncomeService.TotalFor(A.UserId) == income,
					("ур. %d: доход изменился"):format(level + 1)
				)
				check(
					GymService.MuseumPower(A) == power,
					("ур. %d: бонус силы изменился"):format(level + 1)
				)
				check(
					DataService.CountItems(A) == 3,
					("ур. %d: предметов в профиле не 3"):format(level + 1)
				)
				check(
					plot.showcases[1]:GetAttribute("Occupied") and plot.showcases[6]:GetAttribute("Occupied"),
					("ур. %d: места 1 и 6 не заняты"):format(level + 1)
				)
			end
			check(
				data.museumLevel == 5 and data.coins == 500,
				"после четырёх покупок: уровень или остаток"
			)
			-- доход начисляется как прежде
			IncomeService.Handlers.Tick({ A })
			check(
				data.coins == 500 + income,
				"такт дохода после улучшения начислил не доход экспонатов"
			)
			-- новое место 9 (галерея) открыто: выставляется, доход вырос ровно на один экспонат
			near(A, plot.showcases[9])
			local a9 = carry(ctx, A)
			MuseumService.Handlers.Display(A, plot, 9)
			check(
				ItemRegistry.Get(a9).state == "Displayed" and ItemRegistry.Get(a9).slot == 9,
				"на новое место 9 не выставилось"
			)
			check(
				IncomeService.TotalFor(A.UserId) == 3 * IncomeService.Of(TEST_ITEM),
				"доход с новым местом"
			)
			local coins, userId = data.coins, A.UserId
			ctx.note(
				("до выхода: уровень 5, монеты %d, экспонаты на местах 1, 6, 9, в инвентаре 1, доход %d/с"):format(
					coins,
					3 * IncomeService.Of(TEST_ITEM)
				)
			)
			leave(A)
			local again = TestPlayer.new("Тест_A_снова")
			again.UserId = userId
			ctx.track(again)
			check(join(again), "повторный вход не удался")
			local saved = DataService.GetData(again)
			local plotAgain = plotOf(again)
			local open = places(plotAgain)
			check(
				saved.museumLevel == 5 and saved.coins == coins,
				"уровень или монеты не сохранились"
			)
			check(
				plotAgain.level == 5 and open == 10,
				"после входа музей не уровня 5 (10 мест)"
			)
			check(
				again:GetAttribute("MuseumLevel") == 5 and again:GetAttribute("MuseumSlots") == 10,
				"атрибуты после входа"
			)
			for uid, slot in { [a1] = 1, [a6] = 6, [a9] = 9 } do
				local entry = ItemRegistry.Get(uid)
				check(
					entry and entry.state == "Displayed" and entry.slot == slot,
					("после входа экспонат не на месте %d"):format(slot)
				)
				check(
					countUid(uid) == 1,
					("после входа дубль экспоната места %d"):format(slot)
				)
			end
			check(
				ItemRegistry.Get(stored) and ItemRegistry.Get(stored).state == "Stored",
				"после входа предмет инвентаря пропал"
			)
			check(
				DataService.CountItems(again) == 4,
				"после входа предметов в профиле не 4"
			)
			check(
				#plotAgain.exhibits:GetChildren() == 3,
				"после входа экспонатов на участке не 3"
			)
			check(
				IncomeService.TotalFor(again.UserId) == 3 * IncomeService.Of(TEST_ITEM),
				"после входа доход другой"
			)
			ctx.note(
				("после входа: уровень %d, монеты %d, мест %d, экспонаты на местах 1, 6, 9, доход %d/с"):format(
					saved.museumLevel,
					saved.coins,
					open,
					IncomeService.TotalFor(again.UserId)
				)
			)
			-- следующий уровень покупается по своей цене и после входа
			DataService.AddCoins(again, prices[5])
			Upgrade(again, 6)
			check(
				saved.museumLevel == 6 and saved.coins == coins,
				"после входа уровень 6 не куплен по своей цене"
			)
		end
	)

	test(
		"D56 музей и защита: покупка уровня днём — старая защита остаётся в запасе и не ставится, новая ставится",
		function(A, _B, ctx)
			local cfg = GameConfig.Defense
			local data = DataService.GetData(A)
			local museum = DefenseService.Handlers.Museum(A.UserId)
			local spot = Vector3.new(5, 0, 5)
			DataService.AddCoins(A, 1e9)
			-- подготовка на музее уровня 1: две ловушки, одна стоит
			TimeService.SkipTo("Preparation", -5)
			for _ = 1, 2 do
				settle()
				DefenseService.Handlers.Action(A, "BuyDefense", "Trap")
			end
			settle()
			DefenseService.Handlers.Action(A, "Install", "Trap", spot)
			check(
				museum.installed.Trap ~= nil,
				"до повышения ловушка уровня 1 не встала"
			)
			-- пока защита стоит (подготовка и ночь), уровень купить нельзя
			Upgrade(A, 2)
			check(data.museumLevel == 1, "уровень куплен в подготовку")
			TimeService.SkipTo("DoomNight", -2)
			Upgrade(A, 2)
			check(data.museumLevel == 1, "уровень куплен в Судную ночь")
			DefenseService.Handlers.EndNight()
			local defense = DataService.Defense(A)
			check(
				next(museum.installed) == nil and defense.owned.Trap.L1 == 1,
				"после ночи: установленная не исчезла или запас не 1"
			)
			-- днём после ночи: покупка уровня 2
			TimeService.SkipTo("Day", -(GameConfig.Time.DeliveryGrace + 1))
			A:ClearSent()
			Upgrade(A, 2)
			check(data.museumLevel == 2, "днём уровень 2 не куплен")
			defense = DataService.Defense(A)
			check(
				defense.owned.Trap.L1 == 1,
				"покупка уровня удалила старое устройство"
			)
			local sent = lastDefense(A)
			check(
				sent and sent.level == 2 and sent.max == 2,
				"окну «Защита» не пришёл уровень 2"
			)
			check(
				sent.owned.Trap == nil and sent.stale.Trap[1].level == 1 and sent.stale.Trap[1].count == 1,
				"старое устройство не показано как прежнего уровня"
			)
			ctx.note(
				"после покупки уровня 2: ловушка ур. 1 ×1 — в запасе как «прежний уровень», к установке — 0"
			)
			-- следующая подготовка на музее уровня 2
			TimeService.SkipTo("Preparation", -5)
			A:ClearSent()
			settle()
			DefenseService.Handlers.Action(A, "Install", "Trap", spot)
			check(
				museum.installed.Trap == nil and A:WasNotified("другого уровня"),
				"ловушка уровня 1 встала на музей уровня 2"
			)
			local before = data.coins
			settle()
			DefenseService.Handlers.Action(A, "BuyDefense", "Trap")
			check(
				before - data.coins == DefenseRules.Price(cfg, "Trap", 2),
				"новая ловушка — не по цене уровня 2"
			)
			settle()
			DefenseService.Handlers.Action(A, "Install", "Trap", spot)
			check(
				museum.installed.Trap ~= nil and defense.installed.Trap.level == 2,
				"ловушка уровня 2 не встала"
			)
			settle()
			DefenseService.Handlers.Action(A, "BuyDefense", "Laser")
			settle()
			DefenseService.Handlers.Action(A, "Install", "Laser", "Entrance")
			check(
				museum.installed.Laser ~= nil,
				"на уровне 2 второе устройство не встало"
			)
			check(
				defense.owned.Trap.L1 == 1 and defense.owned.Trap.L2 == nil,
				"запас после установки"
			)
			ctx.note(
				("музей ур. 2: ловушка ур. 1 не ставится («другого уровня»), новая за %s встала, второе устройство (лазер) встало"):format(
					money(DefenseRules.Price(cfg, "Trap", 2))
				)
			)
		end
	)
end

-- ── Босс 10 «Король-дракон» (этап B интеграции, 2026-11-15) ──────────────────────────────────────────────────
-- Модель — блоки на суставах (меши — этап C). Цель — тестовый игрок, которого тест ставит по заданному пути.
-- Игрок ставится ступнями на землю в точку local (оси дракона: X — его левый бок, Z — вперёд).
local function placeNearDragon(player: any, boss: BossService.Boss, localPos: Vector3)
	local root = player.Character.PrimaryPart :: BasePart
	local humanoid = player.Character:FindFirstChildOfClass("Humanoid")
	local hip = if humanoid then humanoid.HipHeight else 2
	local ground = boss.root.CFrame:PointToWorldSpace(Vector3.new(localPos.X, 0, localPos.Z))
	player:MoveTo(Vector3.new(ground.X, boss.home.Position.Y + root.Size.Y / 2 + hip, ground.Z))
end

local function dragonFight(A: any, slot: number): any
	prepareFight(A, slot, 10)
	local fight = BattleService.Handlers.Begin(A, 10, slot)
	check(fight, "бой с драконом не начался: " .. table.concat(A:Notices(), "; "))
	if not fight then
		return nil
	end
	check(
		waitUntil(function()
			return fight.phase == "Fight"
		end, 6),
		"дракон не проснулся"
	)
	-- проверка дальности и залпа, не исхода: HP с запасом только на этот бой
	fight.hp, fight.maxHp = 1e15, 1e15
	fight.bossHp, fight.bossMax = 1e15, 1e15
	return fight
end

local function count(fight: any, prefix: string): number
	local n = 0
	for _, line in fight.log do
		if string.sub(line, 1, #prefix) == prefix then
			n += 1
		end
	end
	return n
end

test(
	"Босс 10: Король-дракон закрыт (Studio с DevMode), 52 сустава, числа боя — база 1–4 и сила D56; боссы 1–4 прежние",
	function()
		local cfg = Battle.Bosses[10]
		check(cfg and cfg.Closed == true, "босс 10 не закрыт")
		check(
			cfg.HP == 140 and cfg.Damage == 8 and cfg.AttackInterval == 1.4,
			"база дракона не как у боссов 1–4"
		)
		check(
			cfg.Strength == GameConfig.Progression.Bosses[10],
			"сила дракона не из Progression.Bosses[10]"
		)
		local hp, dmg = BattleService.BossStats(10)
		check(math.abs(hp - 104766407) < 2 and math.abs(dmg - 5986652) < 2, ("HP %.0f, урон %.0f"):format(hp, dmg))
		for zone = 1, 4 do
			local c = Battle.Bosses[zone]
			check(
				c.AttackRange == 9.5
					and c.Leash == 40
					and c.BodyRange == nil
					and c.Volley == nil
					and c.AttackSides == nil,
				("у босса %d появились правила дракона"):format(zone)
			)
		end
		local boss = BossService.Get(10)
		check(boss ~= nil, "в Studio с DevMode дракона нет на карте")
		if not boss then
			return
		end
		local motors = 0
		for _, d in boss.model:GetDescendants() do
			if d:IsA("Motor6D") then
				motors += 1
			end
		end
		check(motors == 52, ("суставов Motor6D %d"):format(motors))
		check(
			boss.orient.MaxAngularVelocity < math.rad(50.5),
			"поворот дракона не ограничен 50°/с"
		)
		check(BossService.HasClips(boss), "у дракона нет клипов")
	end
)

test(
	"Босс 10: дальность до тела 3.5 ст. — автоудары начинаются, прекращаются и возобновляются; бой идёт; дракон на месте и поворачивается не быстрее 50°/с",
	function(A, _B, ctx)
		local boss = BossService.Get(10) :: BossService.Boss
		local fight = dragonFight(A, 1)
		if not fight then
			return
		end
		local function hitsDuring(seconds: number): number
			local before = A:GetAttribute("BattleSwingSeq") or 0
			task.wait(seconds)
			return (A:GetAttribute("BattleSwingSeq") or 0) - before
		end
		-- граница дальности (2.5 + 1 = 3.5 ст., D52) по контуру: напротив середины каждой из сторон 3.4 ст. — в
		-- дальности, 3.6 — нет (расстояние считает сервер, BodyDistance)
		local reach = Battle.Bosses[10].AttackRange + Battle.Player.Reach
		local body = BossService.Rig(boss).Body
		local center = Vector2.zero
		for _, p in body do
			center += p / #body
		end
		local edgeErr = 0
		for i, a in body do
			local b = body[i % #body + 1]
			local mid = (a + b) / 2
			local n = Vector2.new(b.Y - a.Y, a.X - b.X).Unit
			if n:Dot(mid - center) < 0 then
				n = -n
			end
			for _, k in { 3.4, 3.6 } do
				local q = mid + n * k
				local world = boss.root.CFrame:PointToWorldSpace(Vector3.new(q.X, 0, q.Y))
				local d = BattleService.Handlers.BodyDistance(boss, world)
				edgeErr = math.max(edgeErr, math.abs(d - k))
				check(
					(d <= reach) == (k < reach),
					("сторона %d контура, %.1f ст.: расстояние %.2f"):format(i, k, d)
				)
			end
		end
		-- на оси дракона (он не доворачивается): 3.4 ст. — удары идут, 3.6 — нет
		local function onAxis(k: number): Vector3
			local lo, hi = 0, 40
			for _ = 1, 30 do
				local z = (lo + hi) / 2
				local world = boss.root.CFrame:PointToWorldSpace(Vector3.new(0, 0, z))
				if BattleService.Handlers.BodyDistance(boss, world) < k then
					lo = z
				else
					hi = z
				end
			end
			return Vector3.new(0, 0, (lo + hi) / 2)
		end
		placeNearDragon(A, boss, onAxis(3.4))
		local in34 = hitsDuring(2.2)
		placeNearDragon(A, boss, onAxis(3.6))
		task.wait(0.15)
		local out36 = hitsDuring(2.2)
		check(
			in34 >= 2 and out36 == 0,
			("у груди 3.4 ст. — ударов %d, 3.6 ст. — %d"):format(in34, out36)
		)
		ctx.note(
			("граница: %d сторон контура — 3.4 ст. в дальности, 3.6 нет (точность %.3f ст.); у груди 3.4 — %d уд., 3.6 — %d"):format(
				#body,
				edgeErr,
				in34,
				out36
			)
		)
		-- спереди у груди: 3 ст. до контура
		placeNearDragon(A, boss, Vector3.new(0, 0, 12.7 + 3))
		local d = BattleService.Handlers.MeleeDistance(fight, A.Character.PrimaryPart.Position)
		check(math.abs(d - 3) < 0.3, ("до контура спереди %.2f ст."):format(d))
		local atChest = hitsDuring(2.2)
		check(
			atChest >= 2,
			("в дальности (3 ст. от груди) ударов %d за 2.2 с"):format(atChest)
		)
		-- чуть дальше дальности: 4 ст.
		placeNearDragon(A, boss, Vector3.new(0, 0, 12.7 + 4))
		task.wait(0.15)
		local far = hitsDuring(2.2)
		check(far == 0, ("вне дальности (4 ст.) ударов %d"):format(far))
		check(fight.active, "бой кончился, когда игрок вышел из дальности")
		-- вернулся
		placeNearDragon(A, boss, Vector3.new(0, 0, 12.7 + 3))
		local again = hitsDuring(2.2)
		check(again >= 2, ("вернулся — ударов %d"):format(again))
		-- у бока (лапы и бок, не центр): 2 ст. от контура слева
		placeNearDragon(A, boss, Vector3.new(10 + 2, 0, 0))
		local side = hitsDuring(2.2)
		check(side >= 2, ("у левого бока (2 ст. от контура) ударов %d"):format(side))
		ctx.note(
			("ударов за 2.2 с: у груди %d, вне дальности %d, вернулся %d, у бока %d"):format(
				atChest,
				far,
				again,
				side
			)
		)
		-- далеко: дракон не бежит, только поворачивается — и не быстрее 50°/с
		local home = boss.home.Position
		placeNearDragon(A, boss, Vector3.new(-30, 0, -30)) -- сзади справа, далеко
		local function yaw(): number
			local z = boss.root.CFrame.ZVector
			return math.deg(math.atan2(z.X, z.Z))
		end
		local y0 = yaw()
		task.wait(0.5)
		local y1 = yaw()
		local rate = math.abs((y1 - y0 + 540) % 360 - 180) / 0.5
		check(rate <= 55, ("скорость поворота %.0f°/с"):format(rate))
		check(
			waitUntil(function()
				local p = boss.root.CFrame:PointToObjectSpace(A.Character.PrimaryPart.Position)
				return math.abs(math.deg(math.atan2(p.X, p.Z))) < 10
			end, 6),
			"дракон не развернулся к игроку"
		)
		check(
			BossService.DistanceHome(boss) < 0.5,
			("дракон ушёл с места на %.1f ст."):format(BossService.DistanceHome(boss))
		)
		-- все части — в круге арены (31) от места
		local worst = 0
		for _, part in boss.model:GetChildren() do
			if part:IsA("BasePart") and part.Name ~= "Root" then
				worst = math.max(worst, (Vector3.new(part.Position.X - home.X, 0, part.Position.Z - home.Z)).Magnitude)
			end
		end
		check(worst <= 31, ("центры частей до %.1f ст. от места (арена 31)"):format(worst))
		ctx.note(
			("поворот %.0f°/с; дальше всех часть в %.1f ст. от места"):format(
				rate,
				worst
			)
		)
		BattleService.Handlers.Finish(fight, "abort")
		check(waitBossHome(10), "дракон не уснул на месте")
	end
)

-- Арены зоны 10 ещё нет (этап D). С этапа C дракон в Studio стоит на временной площадке сбоку от карты — декор
-- «Замка» далеко, и выключать нечего; если площадки нет: вокруг дракона временный декор (навершия на высоте 13), и
-- развёрнутый к игроку дракон бьёт залпом прямо в навершие. На время проверки залпа декор зоны выше земли не ловит
-- снаряды — как будущая чистая площадка: сервер ищет препятствия с RespectCanCollide, поэтому выключаются и CanQuery, и
-- CanCollide; потом всё возвращается (и так только в этой сессии Play).
local function openDragonLanes(boss: BossService.Boss): () -> ()
	local zones = workspace:FindFirstChild("World")
	zones = zones and zones:FindFirstChild("Map")
	zones = zones and zones:FindFirstChild("Zones")
	local zone = zones and zones:FindFirstChild("Zone10_Castle")
	local changed: { { part: BasePart, query: boolean, collide: boolean } } = {}
	if zone then
		local ground = boss.home.Position.Y
		for _, d in zone:GetDescendants() do
			if d:IsA("BasePart") and d.Position.Y + d.Size.Y / 2 > ground + 1 then
				local p = boss.home:PointToObjectSpace(d.Position)
				if Vector3.new(p.X, 0, p.Z).Magnitude < 120 then
					table.insert(changed, { part = d, query = d.CanQuery, collide = d.CanCollide })
					d.CanQuery = false
					d.CanCollide = false
				end
			end
		end
	end
	return function()
		for _, c in changed do
			c.part.CanQuery = c.query
			c.part.CanCollide = c.collide
		end
	end
end

-- Залп против игрока: тест ставит его в place (оси дракона) и ждёт фиксации направления. Дальше — в мировых осях
-- (дракон ещё может доворачиваться к игроку, и его оси «плывут»): aside(t, pocket) — уход поперёк зафиксированной
-- центральной полосы, стадов (плюс — к левому боку дракона; t — от фиксации, pocket — середина между полосами на
-- дистанции игрока); onLock(origin, dir) — что поставить в момент фиксации (вернуть уборку). Возвращает число попаданий.
local function runVolley(
	fight: any,
	boss: BossService.Boss,
	A: any,
	place: Vector3,
	aside: ((number, number) -> number)?,
	onLock: ((Vector3, Vector3) -> () -> ())?
): number
	fight.nextVolley = 0
	placeNearDragon(A, boss, place)
	local before = count(fight, "залп −")
	local seq0 = boss.model:GetAttribute("VolleySeq") or 0
	check(
		waitUntil(function()
			return (boss.model:GetAttribute("VolleySeq") or 0) > seq0
		end, 4),
		"залп не начался"
	)
	local look0 = boss.root.CFrame.ZVector
	local turned = 0
	local function track()
		turned = math.max(turned, math.deg(math.acos(math.clamp(boss.root.CFrame.ZVector:Dot(look0), -1, 1))))
	end
	check(
		waitUntil(function()
			track()
			return boss.model:GetAttribute("VolleyLockAt") ~= nil
		end, 3),
		"направление не зафиксировано"
	)
	local lockAt = boss.model:GetAttribute("VolleyLockAt") :: number
	local origin = boss.model:GetAttribute("VolleyOrigin") :: Vector3
	local dir = boss.model:GetAttribute("VolleyDir") :: Vector3
	local cleanup = if onLock then onLock(origin, dir) else nil
	local start = (A.Character.PrimaryPart :: BasePart).Position
	local across = Vector3.new(dir.Z, 0, -dir.X).Unit
	if across:Dot(boss.root.CFrame.XVector) < 0 then
		across = -across
	end
	local flat = Vector3.new(start.X - origin.X, 0, start.Z - origin.Z).Magnitude
	local pocket = flat * math.tan(math.rad(Battle.Bosses[10].Volley.Spread)) / 2
	while fight.volley and fight.active do
		if aside then
			A:MoveTo(start + across * aside(workspace:GetServerTimeNow() - lockAt, pocket))
		end
		track()
		task.wait()
	end
	if cleanup then
		cleanup()
	end
	-- во время залпа дракон не поворачивается: круг у скипетра, лапы без шага не скользят
	check(turned < 3, ("дракон повернулся во время залпа на %.1f°"):format(turned))
	return count(fight, "залп −") - before
end

test(
	"Босс 10: залп — дальний игрок перед мордой; стоит — одно попадание; уходит влево или вправо — промах; колонна гасит снаряд",
	function(A, _B, ctx)
		local boss = BossService.Get(10) :: BossService.Boss
		local fight = dragonFight(A, 2)
		if not fight then
			return
		end
		local cfg = Battle.Bosses[10].Volley
		local origin = BossService.Rig(boss).VolleyOrigin
		local restoreLanes = openDragonLanes(boss)
		local ok, err = pcall(function()
			local D = 20
			local spot = Vector3.new(origin.X, 0, origin.Z + D)
			local pocket = D * math.tan(math.rad(cfg.Spread)) / 2
			-- стоит
			local logFrom = #fight.log
			local standHits = runVolley(fight, boss, A, spot, nil)
			local trace = {}
			for i = logFrom + 1, #fight.log do
				table.insert(trace, fight.log[i])
			end
			local feet = tostring(boss.root.CFrame:PointToObjectSpace(A.Character.PrimaryPart.Position))
			local path = table.concat(trace, "; ")
			ctx.note(("стоит: %s; игрок в осях дракона %s"):format(path, feet))
			check(
				standHits == 1,
				("стоит — урон залпом %d раз(а): %s; игрок %s"):format(standHits, path, feet)
			)
			-- уходит влево / вправо через 0.35 с после фиксации, 14 ст/с, на середину между полосами
			local function sidestep(sign: number): (number, number) -> number
				return function(t: number, gap: number): number
					return sign * math.clamp((t - 0.35) * 14, 0, gap)
				end
			end
			local leftHits = runVolley(fight, boss, A, spot, sidestep(1))
			check(leftHits == 0, ("ушёл влево — урон %d: %s"):format(leftHits, fight.log[#fight.log]))
			local rightHits = runVolley(fight, boss, A, spot, sidestep(-1))
			check(
				rightHits == 0,
				("ушёл вправо — урон %d: %s"):format(rightHits, fight.log[#fight.log])
			)
			-- колонна на центральной полосе в 12 ст. от круга (ставится в момент фиксации, до выстрела)
			local coverHits = runVolley(fight, boss, A, spot, nil, function(at: Vector3, dir: Vector3): () -> ()
				local flat = Vector3.new(dir.X, 0, dir.Z).Unit
				local pillar = Instance.new("Part")
				pillar.Name = "TestPillar"
				pillar.Anchored = true
				pillar.CanCollide = true
				pillar.Shape = Enum.PartType.Cylinder
				pillar.Size = Vector3.new(16, 3.2, 3.2)
				local base = at + flat * 12
				pillar.CFrame = CFrame.new(base.X, boss.home.Position.Y + 8, base.Z) * CFrame.Angles(0, 0, math.rad(90))
				pillar.Parent = workspace
				return function()
					pillar:Destroy()
				end
			end)
			check(coverHits == 0, ("за колонной — урон %d"):format(coverHits))
			ctx.note(
				("урон залпом: стоит %d, влево %d, вправо %d, за колонной %d; уход на %.1f ст. через 0.35 с после фиксации"):format(
					standHits,
					leftHits,
					rightHits,
					coverHits,
					pocket
				)
			)
		end)
		restoreLanes()
		if not ok then
			error(err, 0)
		end
		BattleService.Handlers.Finish(fight, "abort")
		check(waitBossHome(10), "дракон не уснул на месте")
	end
)

test(
	"Босс 10: конец боя во время подготовки и во время полёта — залп отменён, снаряды убраны, урона нет",
	function(A, _B, ctx)
		local boss = BossService.Get(10) :: BossService.Boss
		local origin
		for _, when in { "подготовка", "полёт" } do
			local fight = dragonFight(A, if when == "подготовка" then 3 else 4)
			if not fight then
				return
			end
			origin = origin or BossService.Rig(boss).VolleyOrigin
			fight.nextVolley = 0
			placeNearDragon(A, boss, Vector3.new(origin.X, 0, origin.Z + 20))
			local seq0 = boss.model:GetAttribute("VolleySeq") or 0
			check(
				waitUntil(function()
					return (boss.model:GetAttribute("VolleySeq") or 0) > seq0
				end, 4),
				"залп не начался"
			)
			local v = fight.volley
			if when == "подготовка" then
				task.wait(1.0)
			else
				check(
					waitUntil(function()
						return boss.model:GetAttribute("VolleyFireAt") ~= nil
					end, 3),
					"выстрела нет"
				)
				task.wait(0.2)
			end
			local before = count(fight, "залп −")
			BattleService.Handlers.Finish(fight, "abort")
			local cancelAt = boss.model:GetAttribute("VolleyCancelAt")
			check(cancelAt ~= nil, ("%s: залп не отменён (нет VolleyCancelAt)"):format(when))
			check(
				fight.volley == nil and (v == nil or v.conn == nil),
				("%s: цикл снарядов не остановлен"):format(when)
			)
			task.wait(1.5)
			check(count(fight, "залп −") == before, ("%s: урон после конца боя"):format(when))
			ctx.note(("%s: отменён, цикл снарядов остановлен"):format(when))
			check(waitBossHome(10), "дракон не уснул на месте")
		end
	end
)

test(
	"Босс 10 после импорта (этап C): 52 части — меши с картами, Body_2 и глаза на сварке, перепонки skinned, 14 костей на своих частях в покое",
	function(_A, _B, ctx)
		local boss = BossService.Get(10)
		check(boss ~= nil, "в Studio с DevMode дракона нет")
		if not boss then
			return
		end
		local rig = BossService.Rig(boss)
		local model = boss.model
		local meshes, looks = 0, 0
		for _, name in rig.Order do
			local part = model:FindFirstChild(name)
			if part and part:IsA("MeshPart") then
				meshes += 1
				if part:FindFirstChildOfClass("SurfaceAppearance") then
					looks += 1
				end
			end
		end
		check(
			meshes == #rig.Order,
			("мешей у частей %d из %d (остальные — блоки)"):format(meshes, #rig.Order)
		)
		check(looks == #rig.Order, ("карт у частей %d из %d"):format(looks, #rig.Order))
		local extras = 0
		for name, extra in rig.Extras do
			extras += 1
			local mesh = model:FindFirstChild(name)
			check(mesh ~= nil and mesh:IsA("MeshPart"), "нет меша " .. name)
			local weld = mesh and mesh:FindFirstChildOfClass("Weld")
			check(
				weld ~= nil and weld.Part0 == model:FindFirstChild(extra.joint),
				("%s не приварен к %s"):format(name, extra.joint)
			)
			if mesh and extra.eye then
				check(mesh.Material == Enum.Material.Neon, name .. ": глаз не Neon")
			elseif mesh then
				check(mesh:FindFirstChildOfClass("SurfaceAppearance") ~= nil, name .. ": нет карт")
			end
		end
		local membrane = rig.MembraneMesh
		local wings = model:FindFirstChild(membrane.name)
		check(
			wings ~= nil and wings:IsA("MeshPart") and wings.HasSkinnedMesh,
			"перепонки не skinned MeshPart"
		)
		check(
			wings ~= nil and wings:FindFirstChildOfClass("SurfaceAppearance") ~= nil,
			"у перепонок нет карт"
		)
		local bones, worst = 0, 0
		for name in membrane.bones do
			local holder = model:FindFirstChild(name) or boss.root
			local bone = nil -- у части есть и Motor6D с тем же именем — ищется именно Bone
			for _, child in holder:GetChildren() do
				if child:IsA("Bone") and child.Name == name then
					bone = child
				end
			end
			check(bone ~= nil and bone:IsA("Bone"), ("кость %s не на своей части"):format(name))
			local info = rig.Parts[name]
			if bone and info then
				-- на сервере суставы в покое (анимации — у клиентов): кость — в точке вращения своего сустава
				local p = boss.root.CFrame:PointToObjectSpace((bone :: Bone).WorldPosition)
				worst = math.max(worst, (p - info.pivot).Magnitude)
			end
			bones += 1
		end
		check(bones == 14, ("костей перепонок %d"):format(bones))
		check(
			worst < 0.01,
			("кость дальше %.3f ст. от точки вращения сустава"):format(worst)
		)
		ctx.note(
			("мешей частей %d с картами %d, добавочных %d, перепонки skinned, костей %d, отклонение %.4f ст."):format(
				meshes,
				looks,
				extras,
				bones,
				worst
			)
		)
	end
)

-- ── Тестовый режим владельца в опубликованном DEV-месте (решение владельца 2026-11-16) ───────────────────────────
test(
	"Тестовый режим владельца: только резервный сервер DEV-места и только владелец; в Studio и чужом месте выключен",
	function(A)
		local OwnerTest = require(Server.Util.OwnerTest)
		local OwnerTestService = require(Server.Services.OwnerTestService)
		local cfg = GameConfig.OwnerTest
		check(
			type(cfg) == "table" and type(cfg.Enabled) == "boolean",
			"нет настройки GameConfig.OwnerTest.Enabled"
		)
		check(
			cfg.UniverseId == 10776417796 and cfg.PlaceId == 81392528393796,
			"не подтверждённое DEV-место"
		)
		check(
			cfg.Zone == 10 and Battle.Bosses[10].Closed == true,
			"тестовый бой — с закрытым Королём-драконом"
		)
		local function info(fields: { [string]: any }): any
			local base = {
				studio = false,
				gameId = cfg.UniverseId,
				placeId = cfg.PlaceId,
				privateServerId = "",
				privateServerOwnerId = 0,
			}
			for k, v in fields do
				base[k] = v
			end
			return base
		end
		local on = table.clone(cfg)
		on.Enabled = true
		local off = table.clone(cfg)
		off.Enabled = false
		local reserved = { privateServerId = "abc" }
		local cases = {
			{ "резервный сервер DEV-места", on, info(reserved), "Test" },
			{ "обычный сервер DEV-места", on, info({}), "Normal" },
			{
				"частный сервер игрока",
				on,
				info({ privateServerId = "abc", privateServerOwnerId = 42 }),
				"Normal",
			},
			{ "Studio", on, info({ studio = true, privateServerId = "abc" }), "Off" },
			{ "выключен настройкой", off, info(reserved), "Off" },
			{ "чужая вселенная", on, info({ gameId = 1, privateServerId = "abc" }), "Off" },
			{ "чужое место", on, info({ placeId = 2, privateServerId = "abc" }), "Off" },
			{ "нет настройки", nil, info(reserved), "Off" },
		}
		for _, case in cases do
			local kind = OwnerTest.Kind(case[2], case[3])
			check(kind == case[4], ("%s: %s вместо %s"):format(case[1], kind, case[4]))
		end
		check(OwnerTest.IsOwnerId(77, Enum.CreatorType.User, 77), "создатель места — владелец")
		check(
			not OwnerTest.IsOwnerId(78, Enum.CreatorType.User, 77),
			"другой игрок — не владелец"
		)
		check(
			not OwnerTest.IsOwnerId(77, Enum.CreatorType.Group, 77),
			"место группы — владельца-игрока нет"
		)
		check(
			not OwnerTest.IsOwnerId(0, Enum.CreatorType.User, 0),
			"неизвестный создатель — не владелец"
		)
		-- здесь Studio: режим выключен, закрытые боссы — по DevMode, как раньше; команды ничего не делают
		check(
			OwnerTest.ServerKind() == "Off" and not OwnerTest.IsTestServer(),
			"в Studio тестовый режим включился"
		)
		check(not OwnerTest.IsOwner(A), "тестовый игрок оказался владельцем")
		OwnerTestService.Handlers.OnChat(A, "/fight")
		OwnerTestService.Handlers.OnChat(A, "/win")
		-- кнопка «Тест» (RemoteEvent OwnerTest): не владелец, мусор вместо действия, чужой вид сервера — ничего
		OwnerTestService.Handlers.OnRemote(A, "Fight")
		OwnerTestService.Handlers.OnRemote(A, { "Fight" })
		OwnerTestService.Handlers.OnRemote(A, string.rep("x", 200))
		OwnerTestService.Handlers.Run(A, "Fight", "Test")
		OwnerTestService.Handlers.Run(A, "Test", "Normal")
		check(Remotes.Names.OwnerTest ~= nil, "нет RemoteEvent OwnerTest")
		check(BattleService.Handlers.FightOf(A) == nil, "команда не владельца начала бой")
		check(
			BattleService.Handlers.Fight(cfg.Zone) == nil,
			"команда не владельца разбудила дракона"
		)
	end
)

test(
	"Тестовый режим владельца: /fight и /win на драконе — HP только этого боя, числа боя и сила прежние, победа",
	function(A, _B, ctx)
		local OwnerTestService = require(Server.Services.OwnerTestService)
		local cfg = GameConfig.OwnerTest
		prepareFight(A, cfg.Slot, cfg.Zone)
		local data = DataService.GetData(A)
		local strength = data and data.strength
		local bossHp, bossDamage = BattleService.BossStats(cfg.Zone)
		-- «К дракону»: рядом со спящим драконом, боя нет
		local dragon = BossService.Get(cfg.Zone) :: BossService.Boss
		local stateBefore = dragon.state -- после прошлого боя дракон может ещё засыпать (FallAsleep): бой из него начать можно
		OwnerTestService.Handlers.GoTo(A)
		local away = (A.Character:GetPivot().Position - dragon.root.Position).Magnitude
		check(
			away > 20 and away < 70,
			("«К дракону» поставил в %.0f ст. от дракона"):format(away)
		)
		check(
			BattleService.Handlers.FightOf(A) == nil and BattleService.Handlers.Fight(cfg.Zone) == nil,
			"«К дракону» начал бой"
		)
		check(
			dragon.state == stateBefore and (stateBefore == "Sleep" or stateBefore == "FallAsleep"),
			("«К дракону» изменил состояние дракона: %s → %s"):format(
				tostring(stateBefore),
				tostring(dragon.state)
			)
		)
		OwnerTestService.Handlers.StartFight(A)
		local fight = BattleService.Handlers.FightOf(A)
		check(fight ~= nil, "/fight не начал бой: " .. table.concat(A:Notices(), "; "))
		if not fight then
			return
		end
		check(
			fight.zone == cfg.Zone and fight.slot == cfg.Slot,
			"бой не с драконом за свой слот"
		)
		check(
			fight.maxHp == cfg.FightHp and fight.bossMax == cfg.BossHp and A:GetAttribute("BattleMaxHP") == cfg.FightHp,
			"HP боя не из GameConfig.OwnerTest"
		)
		local hp2, dmg2 = BattleService.BossStats(cfg.Zone)
		check(hp2 == bossHp and dmg2 == bossDamage, "числа боя дракона изменились")
		check(DataService.GetData(A).strength == strength, "сила игрока изменилась")
		check(
			waitUntil(function()
				return fight.phase == "Fight"
			end, 6),
			"дракон не проснулся"
		)
		OwnerTestService.Handlers.Win(A)
		check(fight.bossHp == 1 and fight.bossMax == 1, "/win не поставил HP босса 1")
		check(fightTo(fight, 25), "бой после /win не закончился")
		check(
			fight.result == "win",
			"результат " .. tostring(fight.result) .. ": " .. table.concat(fight.log, ", ")
		)
		ctx.note(("бой: %d записей, итог %s"):format(#fight.log, tostring(fight.result)))
	end
)

-- ── Босс 5 «Йети-коллекционер» (D64, подключение 2026-11-24) ─────────────────────────────────────────────────

test(
	"Босс 5: Йети закрыт до выпуска (D64 п. 7), 31 часть на суставах, клипы, линза Neon, лёд глыбы прозрачный; база боя 1–4, сила D56; стоит на «Леднике»",
	function()
		local cfg, base = Battle.Bosses[5], Battle.Bosses[4]
		check(cfg and cfg.Closed == true, "босс 5 не закрыт")
		for _, key in { "HP", "Damage", "AttackInterval", "Leash", "Speed" } do
			check(
				cfg[key] == base[key],
				("%s босса 5 %s, у боссов 1–4 %s"):format(key, tostring(cfg[key]), tostring(base[key]))
			)
		end
		check(cfg.Strength == GameConfig.Progression.Bosses[5], "сила Йети не из Progression.Bosses[5]")
		check(
			cfg.BodyRange == true and cfg.AttackRange == 2.5,
			"дальность Йети — не от контура тела (2.5 + 1)"
		)
		check(BossService.ClosedAllowed(), "тесты идут не в Studio с DevMode")
		local boss = BossService.Get(5)
		check(boss ~= nil, "в Studio с DevMode Йети нет на карте")
		if not boss then
			return
		end
		local rig = BossService.Rig(boss)
		local joints = 0
		for _, d in boss.model:GetDescendants() do
			if d:IsA("Motor6D") then
				joints += 1
			end
		end
		check(#rig.Order == 31 and joints == 31, ("суставов %d из %d"):format(joints, #rig.Order))
		check(BossService.HasClips(boss), "у Йети нет клипов")
		local lens = boss.model:FindFirstChild("Lens") :: BasePart?
		check(lens and lens.Material == Enum.Material.Neon, "линза не Neon")
		for name, value in rig.Transparent do
			local part = boss.model:FindFirstChild(name) :: BasePart?
			check(part and math.abs(part.Transparency - value) < 1e-3, name .. ": лёд не прозрачный")
		end
		local meshes = 0
		for _, name in rig.Order do
			if BossModels[5].meshes[name] then
				meshes += 1
			end
		end
		check(meshes == 31, ("мешей частей %d из 31"):format(meshes))
		local height = BossService.Height(boss)
		check(height > 22 and height < 27, "рост Йети " .. height)
		local home = BossService.HomeOf(5)
		local local_ = MapLayout.ZoneCFrame(5):PointToObjectSpace(home.Position)
		check(
			math.abs(local_.X - MapLayout.BossSpot.X) < 1e-3
				and math.abs(local_.Z - MapLayout.BossSpot.Y) < 1e-3
				and math.abs(local_.Y - MapLayout.Arenas[5].floor) < 1e-3,
			"место Йети — не центр площадки «Ледника»"
		)
		check(
			(boss.root.Position - home.Position).Magnitude < 1,
			"Йети не на своём месте в зоне 5"
		)
		for zone = 1, 4 do
			check(
				Battle.Bosses[zone].BodyRange == nil,
				("у босса %d появилась дальность до тела"):format(zone)
			)
		end
	end
)

test(
	"Босс 5: 30 существ в коллекции, у Йети 4 на плитах площадки «Ледник», «Поймать», бродят не дальше плиты",
	function()
		local active = 0
		for id, def in Items do
			if def.boss == 5 and not def.legacy then
				active += 1
				check(def.kind == "Creature", id .. ": не существо")
			end
		end
		check(active == 30, ("у босса 5 существ %d"):format(active))
		BossLootService.Handlers.Refresh()
		local arena = MapLayout.Arenas[5]
		local frame = MapLayout.ZoneCFrame(5)
		local radius = CreatureMotion.WanderRadius(5)
		local now = workspace:GetServerTimeNow()
		for slot = 1, 4 do
			local uid, part = BossLootService.SlotItem(5, slot)
			check(uid and part, ("слот %d пуст"):format(slot))
			if not part then
				continue
			end
			local def = Items[part:GetAttribute("ItemId") :: string]
			check(
				def and def.boss == 5 and not def.legacy,
				("слот %d: не существо босса 5"):format(slot)
			)
			check(part:GetAttribute("Creature") == true, ("слот %d: не живое существо"):format(slot))
			check(part:GetAttribute("Drop") == arena.top, ("слот %d: высота места"):format(slot))
			local home = part:GetAttribute("Home")
			local spot = typeof(home) == "CFrame" and frame:PointToObjectSpace(home.Position)
			check(
				spot and (Vector2.new(spot.X, spot.Z) - arena.slots[slot]).Magnitude < 0.01,
				("слот %d: не на своей плите"):format(slot)
			)
			local prompt = part:FindFirstChild("TakePrompt") :: ProximityPrompt?
			check(
				prompt and prompt.ActionText == "Поймать",
				("слот %d: нет подсказки «Поймать»"):format(slot)
			)
			local params = {
				seed = CreatureMotion.SeedOf(uid :: string),
				radius = radius,
				scale = CreatureMotion.ScaleOf(def.size),
				mode = "Wander",
				drop = arena.top,
			}
			local farthest = 0
			for k = 0, 600 do
				local pose = CreatureMotion.Pose(params, now + k * 0.37)
				farthest = math.max(farthest, Vector3.new(pose.offset.X, 0, pose.offset.Z).Magnitude)
			end
			check(
				farthest <= math.min(radius + 0.01, 2.6),
				("слот %d: ушёл на %.2f ст. от места"):format(slot, farthest)
			)
		end
	end
)

test(
	"Босс 5: дальность удара до контура тела — 3.4 ст. от любой стороны в дальности, 3.6 — нет; в центре контура 0",
	function()
		local boss = BossService.Get(5) :: BossService.Boss
		if not boss then
			check(false, "Йети нет на карте")
			return
		end
		local reach = Battle.Bosses[5].AttackRange + Battle.Player.Reach
		check(math.abs(reach - 3.5) < 1e-6, "дальность не 3.5 ст.")
		local body = BossService.Rig(boss).Body
		local center = Vector2.zero
		for _, p in body do
			center += p / #body
		end
		for i, a in body do
			local b = body[i % #body + 1]
			if (b - a).Magnitude > 0.5 then
				local mid = (a + b) / 2
				local n = Vector2.new(b.Y - a.Y, a.X - b.X).Unit
				if n:Dot(mid - center) < 0 then
					n = -n
				end
				for _, k in { 3.4, 3.6 } do
					local q = mid + n * k
					local world = boss.root.CFrame:PointToWorldSpace(Vector3.new(q.X, 0, q.Y))
					local d = BattleService.Handlers.BodyDistance(boss, world)
					check(
						(d <= reach) == (k < reach),
						("сторона %d, %.1f ст.: расстояние %.2f"):format(i, k, d)
					)
				end
			end
		end
		check(
			BattleService.Handlers.BodyDistance(boss, boss.root.Position) == 0,
			"в центре Йети расстояние не 0"
		)
	end
)

test(
	"Босс 5: равная сила — победа, существо в руках; Йети вернулся и уснул; сила 0 — поражение, существо на месте",
	function(A, B)
		DataService.AddStrength(A, GameConfig.Progression.Bosses[5])
		local uid = prepareFight(A, 1, 5)
		local boss = BossService.Get(5) :: BossService.Boss
		local fight = BattleService.Handlers.Begin(A, 5, 1)
		check(fight, "бой не начался: " .. table.concat(A:Notices(), "; "))
		if not fight then
			return
		end
		check(boss.state == "Wake", "Йети не просыпается: " .. boss.state)
		check(fightTo(fight, 120), "бой не закончился")
		check(fight.result == "win", "при равной силе не победили: " .. tostring(fight.result))
		check(ItemRegistry.GetCarriedBy(A) == uid, "после победы существо не в руках")
		CarryService.LoseCarried(A, "уборка после теста")
		check(waitBossHome(5), "Йети не вернулся и не уснул после боя")
		-- сила 0: поражение, существо на своей плите
		local uid2 = prepareFight(B, 2, 5)
		local lost = BattleService.Handlers.Begin(B, 5, 2)
		check(lost, "второй бой не начался: " .. table.concat(B:Notices(), "; "))
		if not lost then
			return
		end
		check(fightTo(lost, 90), "второй бой не закончился")
		check(
			lost.result == "lose",
			"при силе 0 Йети должен победить: " .. tostring(lost.result)
		)
		check(
			BossLootService.SlotItem(5, 2) == uid2,
			"после поражения существо не на месте"
		)
		check(waitBossHome(5), "Йети не вернулся после победы")
		TimeService.ResetClock()
	end
)

test(
	"Босс 5: тестовый бой владельца с Йети (/fight 5 → /win) — проснулся, подошёл до контура, бьёт, победа",
	function(A)
		local OwnerTestService = require(Server.Services.OwnerTestService) :: any
		local cfg = GameConfig.OwnerTest
		local ok, err = pcall(function()
			ensureDay()
			check(waitBossHome(5), "Йети не дома")
			BossLootService.Handlers.Refresh()
			local boss = BossService.Get(5) :: BossService.Boss
			OwnerTestService.Handlers.StartFight(A, 5)
			local fight = BattleService.Handlers.FightOf(A)
			check(fight ~= nil, "/fight не начал бой с Йети: " .. table.concat(A:Notices(), "; "))
			if not fight then
				return
			end
			check(
				fight.zone == 5 and fight.maxHp == cfg.FightHp,
				"бой не с Йети или HP не из OwnerTest"
			)
			check(
				waitUntil(function()
					return fight.phase == "Fight"
				end, 8),
				"Йети не проснулся"
			)
			-- игрок стоит в 30 ст. перед Йети: тот идёт к нему и встаёт так, что до контура ≤ 3.5, но не внутри тела
			local reach = Battle.Bosses[5].AttackRange + Battle.Player.Reach
			local root = A.Character and A.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
			local closest = math.huge
			check(
				root ~= nil
					and waitUntil(function()
						closest = BattleService.Handlers.BodyDistance(boss, root.Position)
						return closest <= reach
					end, 15),
				("Йети не подошёл на дальность удара (до контура %.1f)"):format(
					closest
				)
			)
			local swings = A:GetAttribute("BattleSwingSeq") or 0
			task.wait(3)
			check(
				(A:GetAttribute("BattleSwingSeq") or 0) > swings,
				"игрок не бьёт Йети на дальности"
			)
			check(
				BattleService.Handlers.BodyDistance(boss, root.Position) > 0,
				"игрок оказался внутри контура тела Йети"
			)
			OwnerTestService.Handlers.Win(A)
			check(fightTo(fight, 25), "бой после /win не закончился")
			check(fight.result == "win", "результат " .. tostring(fight.result))
			CarryService.LoseCarried(A, "уборка после теста")
			check(waitBossHome(5), "Йети не вернулся после тестового боя")
		end)
		TimeService.ResetClock()
		check(ok, tostring(err))
	end
)

test(
	"Тестовый режим: номер босса в /fight N — 1…10, без числа — босс OwnerTest.Zone, остальное отказ",
	function(A)
		local OwnerTestService = require(Server.Services.OwnerTestService) :: any
		ensureDay()
		OwnerTestService.Handlers.StartFight(A, 6) -- у босса 6 пока нет боя: отказ, бой не начат
		check(BattleService.Handlers.FightOf(A) == nil, "/fight 6 начал бой с боссом без боя")
		check(#A:Notices() > 0, "/fight 6: игрок не узнал об отказе")
		local arg = OwnerTestService.Handlers.ZoneArg
		local okEmpty, zoneEmpty = arg("")
		check(okEmpty and zoneEmpty == nil, "без числа должен быть босс по умолчанию")
		for _, n in { 1, 5, 6, 10 } do
			local ok, zone = arg(tostring(n))
			check(ok and zone == n, "/fight " .. n .. " не принят")
		end
		for _, bad in { "0", "11", "-1", "5x", "5 6", "1.5", "abc", "100" } do
			check(not (arg(bad)), "/fight " .. bad .. " принят")
		end
		check(#GameConfig.Zones == 10, "зон не 10: " .. #GameConfig.Zones)
	end
)

local ServerTests = {}

-- Прогоняет все тесты по очереди: свежие игроки A и B на каждый, после — выход и уборка. Отчёт строкой.
-- filter — часть имени: прогнать только подходящие тесты (долгие бои удобно запускать отдельно).
function ServerTests.Run(filter: string?): string
	if not RunService:IsStudio() then
		return "Серверные тесты запускаются только в Studio"
	end
	local lines, passed, total = {}, 0, 0
	for _, case in tests do
		-- D46: в подготовку, Судную ночь и 10 с доставки экспонаты не меняются — каждый тест начинается днём
		-- (тест краж мог упасть посреди Судной ночи).
		if GameTime.ExhibitLock(GameTime.Now()) then
			TimeService.SkipTo("Day", -(GameConfig.Time.DeliveryGrace + 5))
		end
		if filter and not string.find(case.name, filter, 1, true) then
			continue
		end
		total += 1
		local A, B = TestPlayer.new("Тест_A"), TestPlayer.new("Тест_B")
		local tracked = { A, B }
		local notes: { string } = {}
		local ctx: Context = {
			track = function(player)
				table.insert(tracked, player)
			end,
			items = {},
			note = function(text)
				table.insert(notes, text)
			end,
		}
		local started = DateTime.now().UnixTimestampMillis
		local ok, err = pcall(function()
			check(join(A), "A не вошёл")
			check(join(B), "B не вошёл")
			case.fn(A, B, ctx)
		end)
		for _, player in tracked do
			if player.Parent ~= nil then
				leave(player)
			elseif player.Character.Parent then
				player.Character:Destroy()
			end
		end
		for _, uid in ctx.items do
			local entry = ItemRegistry.Get(uid)
			if entry and entry.state == "OnMap" then
				ItemRegistry.Discard(uid, "уборка после теста")
				if entry.part then
					entry.part:Destroy()
				end
			end
		end
		if ok then
			passed += 1
		end
		local mark = if ok then "OK  " else "FAIL"
		local reason = if ok then "" else ": " .. tostring(err)
		local seconds = (DateTime.now().UnixTimestampMillis - started) / 1000
		table.insert(lines, ("%s %s (%.1f с)%s"):format(mark, case.name, seconds, reason))
		for _, text in notes do
			table.insert(lines, "       · " .. text)
		end
	end
	table.insert(lines, 1, ("Серверные тесты: %d из %d пройдено"):format(passed, total))
	return table.concat(lines, "\n")
end

return ServerTests

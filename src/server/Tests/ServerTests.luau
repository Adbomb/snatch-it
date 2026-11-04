-- Серверные тесты на двух игроков (только Studio, в Play): владение участками, профили, запрет действий с чужими
-- витринами, сундуком, хранилищем, гантелью и полем качалки, один носитель у предмета, повторный вход, перестройка
-- музея; время и ночь (этап 2 D37); предметы у боссов (этап 3); босс 1 (D40): каталог из 20 предметов, модели,
-- автобой (победа, поражение с отбросом, повтор без ожидания, один бой на босса, ночь, побег, сила), доход экспонатов
-- и полный путь «победа → витрина → доход → повторный вход». Игроки — Tests/TestPlayer с профилями в памяти
-- (ProfileStore.Mock): в DataStore ничего не пишется, участки берутся свободные (настоящий игрок не трогается).
-- Вход и выход — тем же Services/PlayerSession, действия — теми же обработчиками, что вызывают подсказки
-- (Handlers). Это серверная симуляция: подсказки на клиенте, интерфейс, сеть и физику персонажа она не
-- проверяет — для этого нужен тест с настоящими клиентами.
-- Запуск через MCP в Play: game.ServerStorage.DevTools.RunServerTests:Invoke() → отчёт строкой.
-- Зависит от Services/*, Util/ItemFactory, Tests/TestPlayer, GameConfig.

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
local GymService = require(Server.Services.GymService)
local IncomeService = require(Server.Services.IncomeService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local MuseumService = require(Server.Services.MuseumService)
local PlayerSession = require(Server.Services.PlayerSession)
local PlotService = require(Server.Services.PlotService)
local NightService = require(Server.Services.NightService)
local InventoryService = require(Server.Services.InventoryService)
local TimeService = require(Server.Services.TimeService)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local MapLayout = require(Server.World.MapLayout)
local ItemFactory = require(Server.Util.ItemFactory)
local TestPlayer = require(Server.Tests.TestPlayer)
local TheftService = require(Server.Services.TheftService)

local TEST_ITEM = "Moai" -- Common из коллекции босса 1 (D40)
local ITEMS_FOLDER = "__TestItems"

type Context = { track: (any) -> (), items: { string } }

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
	return PlayerSession.Join(player, { mock = true })
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

test("Двум игрокам — разные участки и профили; участок освобождается при выходе", function(A, B)
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
end)

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
	check(next(DataService.GetData(A).items) == nil and next(DataService.GetData(B).items) == nil, "профили изменились")
	check(B:WasNotified("Это чужой музей"), "нет сообщения «Это чужой музей»")
end)

test("Нельзя переставить, повернуть, убрать или подменить чужой экспонат", function(A, B, ctx)
	local uid = displayOwn(ctx, A, 1)
	local plotA, plotB = plotOf(A), plotOf(B)
	near(B, plotA.showcases[1])
	MuseumService.Handlers.Move(B, plotA, 1)
	check(B:GetAttribute("MoveSlot") == nil, "B выбрал чужой экспонат")
	MuseumService.Handlers.Rotate(B, plotA, 1)
	InventoryService.Handlers.StoreDisplayed(B, plotA, 1)
	local record = DataService.GetData(A).items[uid]
	check(record.place == "slot" and record.slot == 1 and record.rot == 0, "запись экспоната A изменилась")
	check(ItemRegistry.Get(uid).state == "Displayed" and ItemRegistry.CountStored(B.UserId) == 0, "реестр изменился")
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
end)

test("Нельзя убрать предмет в чужой сундук", function(A, B, ctx)
	local plotA = plotOf(A)
	near(B, plotA.chest)
	local uid = carry(ctx, B)
	InventoryService.Handlers.StoreCarried(B, plotA)
	check(ItemRegistry.GetCarriedBy(B) == uid, "предмет ушёл из рук B")
	check(ItemRegistry.CountStored(A.UserId) == 0 and ItemRegistry.CountStored(B.UserId) == 0, "предмет в хранилище")
	check(B:WasNotified("Это чужой музей"), "нет сообщения «Это чужой музей»")
end)

test("Нельзя выставить предмет из чужого хранилища или по поддельному uid", function(A, B, ctx)
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
	check(ItemRegistry.GetSlotItem(B.UserId, 1) == nil and next(DataService.GetData(B).items) == nil, "у B экспонат")
	check(DataService.GetData(A).items[uid].place == "storage", "запись A изменилась")
end)

-- Единый инвентарь (D46) ───────────────────────────────────────────────────────────────────────────────────

-- Пауза между вызовами одного входа: ограничитель частоты (GameConfig.RateLimits) режет лишние.
local function settle()
	task.wait(0.3)
end

-- Несёт новый предмет и сдаёт его в сундук своего музея (Carried → Stored).
local function toInventory(ctx: Context, player: any, itemId: string?): string
	local plot = plotOf(player)
	near(player, plot.chest)
	local uid = carry(ctx, player, itemId)
	InventoryService.Handlers.StoreCarried(player, plot)
	local entry = ItemRegistry.Get(uid)
	check(entry and entry.state == "Stored" and entry.owner == player.UserId, player.Name .. ": предмет не в инвентаре")
	settle()
	return uid
end

local function farAway(player: any)
	player:MoveTo(Vector3.new(0, 5, 60)) -- место появления: далеко от музеев
end

test("Инвентарь: выставить, снять и заменить из окна откуда угодно, доход пересчитывается", function(A, _B, ctx)
	local first = toInventory(ctx, A, "Moai")
	local second = toInventory(ctx, A, "Sunflowers")
	farAway(A)
	InventoryService.Handlers.Action(A, "Display", first, 2)
	local e1 = ItemRegistry.Get(first)
	check(e1.state == "Displayed" and e1.slot == 2, "предмет не выставлен из окна издалека")
	check(DataService.GetData(A).items[first].place == "slot", "профиль: не на постаменте")
	IncomeService.Handlers.Refresh(A)
	check(A:GetAttribute("Income") == IncomeService.Of("Moai"), "доход не равен доходу выставленного")
	settle()
	InventoryService.Handlers.Action(A, "Replace", second, 2)
	local old, new = ItemRegistry.Get(first), ItemRegistry.Get(second)
	check(old.state == "Stored" and new.state == "Displayed" and new.slot == 2, "замена не прошла")
	local data = DataService.GetData(A)
	check(data.items[first].place == "storage" and data.items[second].slot == 2, "профиль после замены")
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
end)

test("Инвентарь: в подготовку, Судную ночь и 10 с доставки экспонаты не меняются (сервер)", function(A, _B, ctx)
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
		check(ItemRegistry.Get(shown).state == "Displayed" and ItemRegistry.Get(shown).slot == 1, label .. ": экспонат снят")
		check(ItemRegistry.Get(kept).state == "Stored", label .. ": предмет выставлен")
		check(A:GetAttribute("MoveSlot") == nil, label .. ": перестановка началась")
		local record = DataService.GetData(A).items[shown]
		check(record.place == "slot" and record.slot == 1, label .. ": профиль изменился")
	end
	TimeService.SkipTo("Preparation", -5)
	check(GameTime.Current().phase == "Preparation", "не подготовка")
	locked("подготовка")
	check(A:WasNotified("Подготовка к Судной ночи"), "нет причины в сообщении")
	local delivered = toInventory(ctx, A) -- сундук принимает добычу в любую фазу
	check(ItemRegistry.Get(delivered).state == "Stored", "сундук не принял предмет в подготовку")
	TimeService.SkipTo("DoomNight", -5)
	locked("Судная ночь")
	TimeService.SkipTo("Day", -3)
	check(GameTime.DeliveryWindowEnd(GameTime.Now()) ~= nil, "не окно доставки")
	locked("10 с доставки")
	TimeService.SkipTo("Day", -(GameConfig.Time.DeliveryGrace + 5))
	InventoryService.Handlers.Action(A, "Remove", shown)
	check(ItemRegistry.Get(shown).state == "Stored", "днём снять нельзя")
end)

test("Инвентарь: повторные и чужие вызовы InventoryAction не дублируют и не трогают чужое", function(A, B, ctx)
	local mine = toInventory(ctx, A)
	local shown = displayOwn(ctx, A, 1)
	-- Одна и та же вещь на два постамента подряд: встаёт один раз.
	InventoryService.Handlers.Action(A, "Display", mine, 2)
	InventoryService.Handlers.Action(A, "Display", mine, 3)
	local entry = ItemRegistry.Get(mine)
	check(entry.state == "Displayed" and entry.slot == 2 and countUid(mine) == 1, "предмет на двух постаментах")
	check(ItemRegistry.GetSlotItem(A.UserId, 3) == nil, "постамент 3 занят")
	settle()
	-- B: снять, заменить и выставить чужое, неверные аргументы, неизвестное действие.
	for _, args in {
		{ "Remove", shown },
		{ "Replace", mine, 1 },
		{ "Display", shown, 1 },
		{ "Display", mine, 99 },
		{ "Steal", shown, 1 },
		{ "Remove", 42 :: any },
		{ "Display", string.rep("y", 200), 1 },
	} do
		InventoryService.Handlers.Action(B, table.unpack(args))
		settle()
	end
	check(ItemRegistry.Get(shown).state == "Displayed" and ItemRegistry.Get(shown).owner == A.UserId, "чужой экспонат сдвинут")
	check(next(DataService.GetData(B).items) == nil, "у B появились предметы")
	-- Лишние вызовы режет ограничитель: 20 подряд — не больше, чем позволяет частота.
	for _ = 1, 20 do
		InventoryService.Handlers.Action(A, "Remove", mine)
		InventoryService.Handlers.Action(A, "Display", mine, 2)
	end
	local after = ItemRegistry.Get(mine)
	check(after and (after.state == "Stored" or after.state == "Displayed") and countUid(mine) <= 1, "дубль после спама")
	local recordOk = DataService.GetData(A).items[mine]
	check(recordOk and ((recordOk.place == "slot") == (after.state == "Displayed")), "профиль и реестр разошлись")
end)

test("Инвентарь без предела: 12 предметов (больше прежних 10), повторный вход без дублей", function(A, _B, ctx)
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
	check(ItemRegistry.Get(uids[1]).state == "Displayed" and countUid(uids[1]) == 1, "экспонат не восстановлен")
	for i = 2, 12 do
		check(ItemRegistry.Get(uids[i]).state == "Stored" and countUid(uids[i]) == 0, "предмет " .. i .. " не в инвентаре")
	end
end)

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

local function deliverHome(thief: any)
	local plot = plotOf(thief)
	near(thief, plot.chest)
	InventoryService.Handlers.StoreCarried(thief, plot)
end

test("Кража: удержание 3 с, доставка в инвентарь вора, у владельца удалено, лимиты D37", function(A, B, ctx)
	local uid = displayOwn(ctx, A, 1)
	local other = displayOwn(ctx, A, 2)
	doomNight()
	steal(B, A, 1)
	local entry = ItemRegistry.Get(uid)
	check(entry.state == "Stolen" and entry.carrier == B and ItemRegistry.GetCarriedBy(B) == uid, "B не унёс экспонат")
	check(not plotOf(A).showcases[1]:GetAttribute("Occupied"), "постамент не опустел")
	check(DataService.GetData(A).items[uid] ~= nil, "до доставки экспонат уже ушёл из профиля A")
	check(A:WasNotified("Вор унёс"), "владельцу нет уведомления")
	deliverHome(B)
	local after = ItemRegistry.Get(uid)
	check(after and after.state == "Stored" and after.owner == B.UserId, "после доставки не в инвентаре B")
	check(DataService.GetData(A).items[uid] == nil, "у A осталась запись — дубль")
	local record = DataService.GetData(B).items[uid]
	check(record and record.place == "storage" and record.source == "raid" and record.from == A.UserId, "запись B")
	check(countUid(uid) == 0, "в мире осталась деталь украденного")
	-- подтверждение журнала (сохранения профилей) снимает pending
	local started = os.clock()
	while DataService.GetData(B).items[uid].pending ~= nil and os.clock() - started < GameConfig.Theft.SaveTimeout + 2 do
		task.wait(0.2)
	end
	check(DataService.GetData(B).items[uid].pending == nil, "передача не подтверждена журналом")
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
end)

test("Кража: провалы возвращают экспонат на постамент, лимиты не тратятся", function(A, B, ctx)
	local uid = displayOwn(ctx, A, 1)
	doomNight()
	local plotA = plotOf(A)
	-- отпустил E раньше времени
	near(B, plotA.showcases[1])
	TheftService.Handlers.Begin(B, plotA, 1)
	check(ItemRegistry.Get(uid).state == "Lifting", "удержание не началось")
	TheftService.Handlers.Cancel(B)
	check(ItemRegistry.Get(uid).state == "Displayed" and ItemRegistry.Get(uid).slot == 1, "после отпускания не на месте")
	-- поддельное завершение через 1 с
	steal(B, A, 1, 1)
	check(ItemRegistry.Get(uid).state == "Displayed", "кража за 1 с прошла")
	-- Triggered без начала удержания
	TheftService.Handlers.Complete(B, plotA, 1)
	check(ItemRegistry.Get(uid).state == "Displayed", "кража без удержания прошла")
	-- поражение вора с добычей
	task.wait(0.3)
	steal(B, A, 1)
	check(ItemRegistry.Get(uid).state == "Stolen", "вторая попытка не удалась")
	TheftService.OnDefeated(B)
	local back = ItemRegistry.Get(uid)
	check(back.state == "Displayed" and back.slot == 1 and back.owner == A.UserId, "после поражения не вернулся")
	check(ItemRegistry.GetCarriedBy(B) == nil and countUid(uid) == 1, "добыча осталась у B или дубль")
	check(plotA.showcases[1]:GetAttribute("Occupied") == true, "постамент не занят после возврата")
	-- бросил добычу (G)
	task.wait(0.3)
	steal(B, A, 1)
	CarryService.Drop(B)
	check(ItemRegistry.Get(uid).state == "Displayed", "брошенная добыча не вернулась")
	-- время доставки вышло
	task.wait(0.3)
	steal(B, A, 1)
	check(ItemRegistry.Get(uid).state == "Stolen", "третья попытка не удалась")
	TimeService.SkipTo("Day", -(GameConfig.Time.DeliveryGrace + 1))
	TheftService.Handlers.Sweep()
	check(ItemRegistry.Get(uid).state == "Displayed", "после 10 с доставки не вернулся")
	check(DataService.GetData(A).items[uid] ~= nil and next(DataService.GetData(B).items) == nil, "профили изменились")
	check(DataService.GetStat(B, "theftEvent") == nil and DataService.GetStat(A, "lossEvent") == nil, "лимиты потрачены")
end)

test("Кража: два вора на один экспонат, Stored и свои — нельзя, в 10 с доставки новая не начинается", function(A, B, ctx)
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
	steal(B, B, 1, 0.1)
	check(ItemRegistry.Get(own).state == "Displayed", "B украл свой экспонат")
	check(ItemRegistry.Get(stored).state == "Stored", "предмет из инвентаря A сдвинулся")
	-- окно доставки: новая кража не начинается
	TimeService.SkipTo("Day", -3)
	check(GameTime.TheftPhase(GameTime.Now()) == "Delivery", "не окно доставки")
	near(C, plotA.showcases[1])
	TheftService.Handlers.Begin(C, plotA, 1)
	check(ItemRegistry.Get(uid).state == "Displayed", "кража в окне доставки началась")
end)

test("Улучшить можно только свою гантель", function(A, B)
	local price = GameConfig.Progression.Dumbbell.Prices[1]
	DataService.AddCoins(A, price)
	DataService.AddCoins(B, price)
	local plotA = plotOf(A)
	near(B, plotA.signBoard)
	GymService.Handlers.Upgrade(B, plotA)
	check(DataService.GetData(B).dumbbellLevel == 1 and DataService.GetData(B).coins == price, "B улучшил чужую")
	check(DataService.GetData(A).dumbbellLevel == 1 and DataService.GetData(A).coins == price, "у A списались монеты")
	check(plotA.model:GetAttribute("DumbbellLevel") == 1, "гантель A сменилась от B")
	near(A, plotA.signBoard)
	GymService.Handlers.Upgrade(A, plotA)
	check(DataService.GetData(A).dumbbellLevel == 2 and DataService.GetData(A).coins == 0, "A не улучшил свою")
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

test("Предмет несёт только один игрок; чужой экспонат не поднять", function(A, B, ctx)
	local plotA = plotOf(A)
	near(A, plotA.showcases[3])
	local uid, part = mapItem(ctx, A.Character.PrimaryPart.Position + Vector3.new(0, 0, 3))
	B:MoveTo(part.Position + Vector3.new(0, 0, 2))
	CarryService.Handlers.Pickup(A, uid)
	CarryService.Handlers.Pickup(B, uid)
	check(ItemRegistry.GetCarriedBy(A) == uid and ItemRegistry.GetCarriedBy(B) == nil, "у предмета не один носитель")
	MuseumService.Handlers.Display(A, plotA, 3)
	check(ItemRegistry.Get(uid).state == "Displayed", "A не выставил предмет")
	B:MoveTo(plotA.showcases[3].Position + Vector3.new(0, 0, -3))
	CarryService.Handlers.Pickup(B, uid)
	check(ItemRegistry.Get(uid).state == "Displayed" and ItemRegistry.GetCarriedBy(B) == nil, "B поднял чужой экспонат")
end)

test("Реестр не пускает предмет в чужой музей и чужое хранилище", function(A, B, ctx)
	local uid = carry(ctx, B)
	local toShowcase = ItemRegistry.Transition(uid, "Displayed", { owner = A.UserId, slot = 4 })
	local toStorage = ItemRegistry.Transition(uid, "Stored", { owner = A.UserId })
	check(not toShowcase and not toStorage, "реестр разрешил переход в чужой музей")
	check(ItemRegistry.GetCarriedBy(B) == uid, "предмет ушёл из рук B")
end)

test("Повторный вход A при B: экспонаты, хранилище и монеты на месте, без дублей", function(A, B, ctx)
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
	check(ItemRegistry.Get(shown) == nil and ItemRegistry.Get(stored) == nil, "экспонаты A остались в реестре")
	check(countUid(shown) == 0, "экспонат A остался в мире")
	check(ItemRegistry.Get(ownB).state == "Displayed", "экспонат B пропал после выхода A")
	local again = TestPlayer.new("Тест_A_снова")
	again.UserId = userId
	ctx.track(again)
	check(join(again), "A не вошёл повторно")
	local entry = ItemRegistry.Get(shown)
	check(entry and entry.state == "Displayed" and entry.slot == 2, "экспонат A не восстановлен на витрине 2")
	check(ItemRegistry.Get(stored) and ItemRegistry.Get(stored).state == "Stored", "хранилище A не восстановлено")
	check(DataService.GetData(again).coins == 777, "монеты A не сохранились")
	check(again:GetAttribute("StorageCount") == 1, "StorageCount A")
	check(countUid(shown) == 1 and countUid(stored) == 0, "дубли экспонатов A")
	check(#plotOf(again).exhibits:GetChildren() == 1, "лишние экспонаты на участке A")
	check(ItemRegistry.Get(ownB).state == "Displayed" and countUid(ownB) == 1, "экспонат B изменился")
end)

test("Перестройка музея A (уровни 5, 10, 1) не трогает экспонаты A и B", function(A, B, ctx)
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
		check(#plotA.exhibits:GetChildren() == 2, ("уровень %d: экспонатов A не 2"):format(level))
		check(countUid(a1) == 1 and countUid(a5) == 1, ("уровень %d: дубли или потери у A"):format(level))
		check(plotA.showcases[1]:GetAttribute("Occupied") and plotA.showcases[5]:GetAttribute("Occupied"), "витрины A")
		check(plotB.model:FindFirstChild("Building") == buildingB, "здание B перестроилось")
		check(#plotB.exhibits:GetChildren() == 1 and countUid(b2) == 1, "экспонаты B изменились")
	end
end)

test("Когда свободных участков нет, новый игрок не получает чужой", function(_A, _B, ctx)
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
end)

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
			("t=%s: %s день %d, ждали %s день %d"):format(case[1], state.phase, state.day, case[2], case[3])
		)
	end
	check(GameTime.At(base + 3360).cycle == 124, "новый круг не начался")
end)

test("Время: полный круг шагом 0.1 с — порядок и длительность фаз", function()
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
	check(table.concat(order, ",") == table.concat(expected, ","), "порядок фаз: " .. table.concat(order, ","))
	local want = { Day = 300, Night = 30, Preparation = 120, DoomNight = 90 }
	for i, phase in order do
		local need = if phase == "Day" and i == #order - 2 then 180 else want[phase]
		check(math.abs(lengths[i] - need) < 1e-6, ("%s №%d длится %s"):format(phase, i, lengths[i]))
	end
end)

test("Время: сервер публикует ту же фазу, что считает общая функция", function()
	TimeService.Update()
	local state = GameTime.Current()
	check(ReplicatedStorage:GetAttribute("Phase") == state.phase, "атрибут Phase")
	check(ReplicatedStorage:GetAttribute("Day") == state.day, "атрибут Day")
	check(ReplicatedStorage:GetAttribute("PhaseEndsAt") == state.endsAt, "атрибут PhaseEndsAt")
end)

test("Ночь: не успел до Safe Zone — предмет потерян и перенос; успел — предмет при нём", function(A, B, ctx)
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
	check((A.Character.PrimaryPart.Position - MapLayout.Spawn.position).Magnitude < 20, "A не у места появления")
	check(ItemRegistry.Get(uidA) == nil and ItemRegistry.GetCarriedBy(A) == nil, "предмет A (вне Safe Zone) не потерян")
	check(A:WasNotified("предмет потерян"), "нет сообщения о потере")
	check(ItemRegistry.GetCarriedBy(B) == uidB, "предмет B (в Safe Zone) потерян")
	check((B.Character.PrimaryPart.Position - bPosition).Magnitude < 0.01, "B в Safe Zone перенесли")
	-- B выставляет сохранённый предмет уже ночью.
	local plotB = plotOf(B)
	near(B, plotB.showcases[1])
	MuseumService.Handlers.Display(B, plotB, 1)
	check(ItemRegistry.Get(uidB).state == "Displayed", "B не смог выставить предмет после наступления ночи")
	check(NightService.Handlers.Barrier().Parent ~= nil, "барьер не поставлен")
	A:MoveTo(corridor)
	check(NightService.Handlers.Sweep({ A }) == 1, "зашедшего ночью в коридор не вывели")
	NightService.Handlers.Apply(GameTime.At(GameConfig.Time.Epoch + 330), nightState, { A, B })
	check(NightService.Handlers.Barrier().Parent == nil, "барьер не убран на рассвете")
	-- вернуть правила текущей фазы
	NightService.Handlers.Apply(TimeService.Current(), nil, {})
end)

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

test("Коллекции: босс 1 — 8/8/4, босс 2 — 12/10/8 (Common/Rare/Epic) с доходом; у черновых нет лишних редкостей", function()
	for id, def in Items do
		check(table.find(Rarities.Order, def.rarity), id .. ": редкость " .. tostring(def.rarity))
		check(def.boss >= 1 and def.boss <= #GameConfig.Zones, id .. ": босс " .. tostring(def.boss))
	end
	-- D40 и D42; у босса 2 модели появятся после импорта мешей (до него — заготовки цвета и размера модели).
	local wants = {
		[1] = { Common = 8, Rare = 8, Epic = 4, Legendary = 0, Secret = 0 },
		[2] = { Common = 12, Rare = 10, Epic = 8, Legendary = 0, Secret = 0 },
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
				check(count == want[rarity], ("босс %d: %s %d, нужно %d"):format(boss, rarity, count, want[rarity]))
			elseif (chances[rarity] or 0) == 0 then
				check(count == 0, ("босс %d: %s ему недоступна"):format(boss, rarity))
			end
		end
	end
end)

test("Шансы: Legendary только у боссов 4–10, Secret — 8–10; частоты как в таблице", function()
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
		check(math.abs(total - 100) < 1e-9, ("боссы %d–%d: сумма шансов %s"):format(tier.from, tier.to, total))
		local counts = {}
		for _ = 1, n do
			local rarity = BossLootService.RollRarity(tier.from, rng)
			counts[rarity] = (counts[rarity] or 0) + 1
		end
		for _, rarity in Rarities.Order do
			local got = (counts[rarity] or 0) / n * 100
			local want = tier.chances[rarity] or 0
			local ok = if want == 0 then got == 0 else math.abs(got - want) < 0.3
			check(ok, ("боссы %d–%d: %s %.2f%%, ждали %s%%"):format(tier.from, tier.to, rarity, got, want))
		end
	end
end)

test("Слоты: у каждого из 10 боссов 4 предмета из его коллекции", function()
	BossLootService.Handlers.Refresh()
	local slots = bossSlots()
	for boss = 1, #GameConfig.Zones do
		for slot = 1, GameConfig.Progression.BossLoot.Slots do
			local uid = slots[boss][slot].uid
			local entry = uid and ItemRegistry.Get(uid)
			check(entry and entry.state == "AtBoss", ("босс %d слот %d пуст"):format(boss, slot))
			check(entry.boss == boss and entry.bossSlot == slot, ("босс %d слот %d: чужие данные"):format(boss, slot))
			local own = Items[entry.itemId].boss == boss
			check(own, ("босс %d: предмет %s не из его коллекции"):format(boss, entry.itemId))
		end
	end
end)

test("Рассвет: все 40 предметов заменяются новыми uid, старые удалены, дублей нет", function()
	local seen = {}
	local previous = {}
	for round = 1, 25 do
		BossLootService.Handlers.Refresh()
		local current = {}
		for boss, bySlot in bossSlots() do
			for slot, entry in bySlot do
				check(entry.uid, ("обновление %d: босс %d слот %d пуст"):format(round, boss, slot))
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
end)

test("Без боя (босс 3, тестовый режим): слот пуст до рассвета, «Поднять» не берёт, экспонат помнит босса", function(A, B)
	local shifted = ensureDay()
	BossLootService.Handlers.Refresh()
	local entry = bossSlots()[3][1]
	local uid = entry.uid :: string
	local part = (ItemRegistry.Get(uid) :: any).part
	A:MoveTo(part.Position + Vector3.new(0, 0, -3))
	B:MoveTo(part.Position + Vector3.new(0, 0, 3))
	CarryService.Handlers.Pickup(A, uid)
	local stillThere = ItemRegistry.Get(uid).state == "AtBoss"
	BossLootService.Handlers.Take(A, 3, 1)
	local taken = ItemRegistry.GetCarriedBy(A) == uid
	local emptied = entry.uid == nil
	BossLootService.Handlers.Take(B, 3, 1)
	local bEmpty = ItemRegistry.GetCarriedBy(B) == nil
	if shifted then
		TimeService.ResetClock()
	end
	check(stillThere, "предмет у босса подняли обычным «Поднять»")
	check(taken and ItemRegistry.Get(uid).boss == 3, "A не забрал предмет в тестовом режиме")
	check(emptied and bEmpty, "слот не опустел или B что-то получил")
	local plotA = plotOf(A)
	near(A, plotA.showcases[1])
	MuseumService.Handlers.Display(A, plotA, 1)
	local record = DataService.GetData(A).items[uid]
	check(record and record.boss == 3 and record.source == "boss", "в профиле нет босса-источника")
	BossLootService.Handlers.Refresh()
	check(entry.uid ~= nil, "слот не заполнен на рассвете")
	check(ItemRegistry.Get(uid).state == "Displayed", "рассвет тронул выставленный экспонат")
end)

test("Без боя забрать нельзя вне тестового режима Studio (босс 3)", function(A)
	BossLootService.Handlers.Refresh()
	local uid = bossSlots()[3][1].uid :: string
	A:MoveTo((ItemRegistry.Get(uid) :: any).part.Position + Vector3.new(0, 0, -3))
	local saved = GameConfig.Bosses.FreeTakeInStudio
	GameConfig.Bosses.FreeTakeInStudio = false
	local ok, err = pcall(BossLootService.Handlers.Take, A, 3, 1)
	GameConfig.Bosses.FreeTakeInStudio = saved
	check(ok, tostring(err))
	check(ItemRegistry.Get(uid).state == "AtBoss" and ItemRegistry.GetCarriedBy(A) == nil, "забрал без боя")
	check(A:WasNotified("победите босса"), "нет сообщения «победите босса»")
end)

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
	check(waitBossHome(boss), ("босс %d не вернулся на место после прошлого боя"):format(boss))
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

test("Модели: у всех 20 предметов и 16 частей пса загружены настоящие меши (импорт FBX)", function()
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
	check(#missing == 0, ("нет мешей у %d предметов: %s"):format(#missing, table.concat(missing, ", ")))
	check(parts == #Boss1DogRig.Order, ("у пса мешей %d из %d"):format(parts, #Boss1DogRig.Order))
end)

test("Сила: урон и HP растут с силой, частота ударов от силы не зависит", function()
	local hp0, dmg0 = BattleService.PlayerStats(0)
	local hp1, dmg1 = BattleService.PlayerStats(100)
	local hp2, dmg2 = BattleService.PlayerStats(1e6)
	check(hp0 == Battle.Player.BaseHP and dmg0 == Battle.Player.BaseDamage, "базовые HP и урон")
	check(hp1 > hp0 and dmg1 > dmg0 and hp2 > hp1 and dmg2 > dmg1, "HP и урон не растут с силой")
	check(type(Battle.Player.AttackInterval) == "number", "интервал ударов не число")
	local bossHp, bossDmg = BattleService.BossStats(1)
	check(bossHp > 0 and bossDmg > 0, "у босса 1 нет HP или урона")
end)

test("Бой с псом (сила 50): проснулся, HP падают, победа — предмет в руках, соседние на месте, пёс уснул дома", function(A)
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
	check(not BossLootService.IsOpen(1), "подсказки у занятого босса не выключены")
	local sawCombat = false
	check(waitUntil(function()
		sawCombat = sawCombat or boss.state == "Combat"
		return not fight.active
	end, 60), "бой не закончился за минуту")
	check(sawCombat, "пёс не встал в боевую стойку")
	check(fight.result == "win", "результат " .. tostring(fight.result) .. ": " .. table.concat(fight.log, ", "))
	check(fight.bossHp <= 0, "HP босса не дошло до нуля")
	check(ItemRegistry.GetCarriedBy(A) == uid, "предмет не у победителя")
	check(BossLootService.SlotItem(1, 2) == nil, "слот не опустел")
	for slot, other in others do
		check(BossLootService.SlotItem(1, slot) == other, ("соседний слот %d тронут"):format(slot))
	end
	check(waitUntil(function()
		return boss.state == "Sleep"
	end, 45), "пёс не уснул: " .. boss.state)
	check(BossService.DistanceHome(boss) <= Battle.ArriveDistance + 0.5, "пёс уснул не на своём месте")
	check(BossLootService.IsOpen(1), "подсказки не открылись после возвращения")
	TimeService.ResetClock()
end)

test("Бой при силе 0: удары по-настоящему, HP у обоих уменьшаются, исход — по ударам", function(A)
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
	check(playerHits >= 3 and bossHits >= 1, ("ударов игрока %d, босса %d"):format(playerHits, bossHits))
	check(took > 5, ("бой длился %.1f с — слишком быстро для силы 0"):format(took))
	if ItemRegistry.GetCarriedBy(A) then
		CarryService.LoseCarried(A, "уборка после теста")
	end
	TimeService.ResetClock()
end)

test("Поражение: отброс без телепорта, предмет на постаменте, пёс засыпает, новый бой — сразу", function(A)
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
	check((A.Character.PrimaryPart.Position - before).Magnitude < 0.01, "проигравшего телепортировали")
	check(BossLootService.SlotItem(1, 1) == uid, "предмет не вернулся на постамент")
	check(ItemRegistry.Get(uid).state == "AtBoss" and ItemRegistry.GetCarriedBy(A) == nil, "предмет у проигравшего")
	check(waitDogHome(), "пёс не вернулся и не лёг")
	local again = BattleService.Handlers.Begin(A, 1, 1)
	check(again, "новый бой не начался сразу: " .. table.concat(A:Notices(), "; "))
	BattleService.Handlers.Finish(again, "abort")
	check(waitDogHome(), "пёс не вернулся после второго боя")
	TimeService.ResetClock()
end)

test("Один бой на босса: второй игрок не начнёт бой и не заберёт предмет занятого пса", function(A, B)
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
end)

test("Ночь прерывает бой (предмет у пса, на рассвете — новый), побег за поводок — тоже", function(A)
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
	local escape = BattleService.Handlers.Begin(A, 1, 4)
	check(escape, "второй бой не начался")
	local home = (BossService.Get(1) :: BossService.Boss).home.Position
	A:MoveTo(home + Vector3.new(0, 3, Battle.Bosses[1].Leash + 6))
	check(fightTo(escape, 5) and escape.result == "escape", "побег не засчитан: " .. tostring(escape.result))
	check(waitDogHome(), "пёс не вернулся")
	TimeService.ResetClock()
end)

-- ── Босс 2 «Торговец-громила»: площадка и бой (D42, D43) ─────────────────────────────────────────────────────

test("Торговец: модель из 12 частей на Motor6D; предметы на площадке без постаментов, у каждого свой поворот", function()
	local boss = BossService.Get(2)
	check(boss, "у зоны 2 нет босса")
	local trader = boss :: BossService.Boss
	check(trader.model:GetAttribute("BossName") == GameConfig.Zones[2].boss, "имя босса не совпадает с зоной")
	local joints = 0
	for _, name in Boss2TraderRig.Order do
		local part = trader.model:FindFirstChild(name)
		local joint = part and part:FindFirstChild(name)
		if joint and joint:IsA("Motor6D") then
			joints += 1
		end
	end
	check(joints == #Boss2TraderRig.Order, ("суставов %d из %d"):format(joints, #Boss2TraderRig.Order))
	check((trader.home.Position - BossService.HomeOf(2).Position).Magnitude < 0.01, "торговец не на своём месте")

	BossLootService.Handlers.Refresh()
	local arena = MapLayout.Arenas[2]
	local floorY = MapLayout.ZoneCFrame(2).Position.Y + arena.top
	local looks = {}
	for slot = 1, 4 do
		local uid, part = BossLootService.SlotItem(2, slot)
		check(uid and part, ("слот %d пуст"):format(slot))
		local item = part :: BasePart
		local bottom = item.Position.Y - item.Size.Y / 2
		local message = ("слот %d: низ предмета %.2f, площадка %.2f"):format(slot, bottom, floorY)
		check(math.abs(bottom - floorY) < 0.05, message)
		for _, other in looks do
			check(item.CFrame.LookVector:Dot(other) < 0.99, ("слот %d повёрнут как другой"):format(slot))
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
	local counted = ("постаментов: у пса %d, у торговца %d"):format(pedestals[1], pedestals[2])
	check(pedestals[1] == 4 and pedestals[2] == 0, counted)
end)

test("Бой с торговцем: при силе 0 — поражение, при силе 1000 — победа; имя в сообщениях, полоска HP над головой", function(A)
	local uid = prepareFight(A, 1, 2)
	local boss = BossService.Get(2) :: BossService.Boss
	local name = GameConfig.Zones[2].boss
	A:ClearSent()
	local fight = BattleService.Handlers.Begin(A, 2, 1)
	check(fight, "бой не начался: " .. table.concat(A:Notices(), "; "))
	check(A:WasNotified(name .. " проснулся"), "нет сообщения с именем торговца")
	local bar = boss.root:FindFirstChild("BattleBar") :: BillboardGui?
	check(bar and bar.StudsOffsetWorldSpace.Y > BossService.Height(boss), "полоска HP не над головой торговца")
	check(fightTo(fight, 60), "бой не закончился за минуту")
	check(fight.result == "lose", "при силе 0 торговец должен победить: " .. tostring(fight.result))
	check(A:WasNotified(name .. " победил"), "нет сообщения о победе торговца")
	check(BossLootService.SlotItem(2, 1) == uid and ItemRegistry.GetCarriedBy(A) == nil, "предмет ушёл с площадки")
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
end)

test("Доход: свой у каждого экспоната на витрине, сумма в Income, надпись «+X/сек»; в руках и хранилище — 0", function(A, B, ctx)
	local moai = displayOwn(ctx, A, 1, "Moai")
	local starry = displayOwn(ctx, A, 2, "StarryNight")
	local m, s = Items.Moai.income, Items.StarryNight.income
	local coins = DataService.GetData(A).coins
	IncomeService.Handlers.Tick({ A })
	check(DataService.GetData(A).coins == coins + m + s, "за секунду начислено не m + s")
	check(A:GetAttribute("Income") == m + s, "атрибут Income " .. tostring(A:GetAttribute("Income")))
	local label = (ItemRegistry.Get(moai) :: any).part:FindFirstChild("IncomeLabel")
	check(label and label.Text.Text == ("+%d/сек"):format(m), "нет надписи дохода над экспонатом")
	carry(ctx, A, "TRexSkeleton")
	local plotA = plotOf(A)
	CarryService.LoseCarried(A, "тест")
	near(A, plotA.showcases[2])
	InventoryService.Handlers.StoreDisplayed(A, plotA, 2)
	check(ItemRegistry.Get(starry).state == "Stored", "экспонат не убран в хранилище")
	coins = DataService.GetData(A).coins
	IncomeService.Handlers.Tick({ A })
	check(DataService.GetData(A).coins == coins + m, "хранилище или руки приносят доход")
	check(A:GetAttribute("Income") == m, "Income не пересчитан после хранилища")
	coins = DataService.GetData(B).coins
	IncomeService.Handlers.Tick({ B })
	check(DataService.GetData(B).coins == coins, "доход A попал B")
end)

test("Полный путь: победа → в руках → витрина → доход → повторный вход без дублей", function(A, _B, ctx)
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
	check(record and record.id == itemId and record.boss == 1 and record.source == "boss", "запись в профиле неполная")
	local coins = DataService.GetData(A).coins
	IncomeService.Handlers.Tick({ A })
	check(DataService.GetData(A).coins == coins + Items[itemId].income, "доход добычи не начислен")
	local userId = A.UserId
	leave(A)
	local again = TestPlayer.new("Тест_A_снова")
	again.UserId = userId
	ctx.track(again)
	check(join(again), "A не вошёл повторно")
	local entry = ItemRegistry.Get(uid)
	check(entry and entry.state == "Displayed" and entry.slot == 1 and entry.itemId == itemId, "добыча не восстановлена")
	check(countUid(uid) == 1, "дубли добычи после повторного входа")
	local label = (entry :: any).part:FindFirstChild("IncomeLabel")
	check(label ~= nil, "нет надписи дохода после повторного входа")
	coins = DataService.GetData(again).coins
	IncomeService.Handlers.Tick({ again })
	check(DataService.GetData(again).coins == coins + Items[itemId].income, "после входа доход не идёт")
	check(waitDogHome(), "пёс не вернулся")
	TimeService.ResetClock()
end)


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
		local ctx: Context = {
			track = function(player)
				table.insert(tracked, player)
			end,
			items = {},
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
	end
	table.insert(lines, 1, ("Серверные тесты: %d из %d пройдено"):format(passed, total))
	return table.concat(lines, "\n")
end

return ServerTests

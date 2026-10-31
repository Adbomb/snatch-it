-- Серверные тесты на двух игроков (только Studio, в Play): владение участками, профили, запрет действий с чужими
-- витринами, сундуком, хранилищем, гантелью и полем качалки, один носитель у предмета, повторный вход, перестройка
-- музея; время и ночь (этап 2 D37). Игроки — Tests/TestPlayer с профилями в памяти (ProfileStore.Mock): в DataStore
-- ничего не пишется, участки берутся свободные (настоящий игрок не трогается). Вход и выход — тем же Services/PlayerSession, действия
-- — теми же обработчиками, что вызывают подсказки (Handlers). Это серверная симуляция: подсказки на клиенте,
-- интерфейс, сеть и физику персонажа она не проверяет — для этого нужен тест с настоящими клиентами.
-- Запуск через MCP в Play: game.ServerStorage.DevTools.RunServerTests:Invoke() → отчёт строкой.
-- Зависит от Services/*, Util/ItemFactory, Tests/TestPlayer, GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local DataService = require(Server.Services.DataService)
local GymService = require(Server.Services.GymService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local MuseumService = require(Server.Services.MuseumService)
local PlayerSession = require(Server.Services.PlayerSession)
local PlotService = require(Server.Services.PlotService)
local NightService = require(Server.Services.NightService)
local StorageService = require(Server.Services.StorageService)
local TimeService = require(Server.Services.TimeService)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local MapLayout = require(Server.World.MapLayout)
local ItemFactory = require(Server.Util.ItemFactory)
local TestPlayer = require(Server.Tests.TestPlayer)

local TEST_ITEM = "Mug" -- предмет для тестов (до замены хлама на произведения искусства, этап 3 D37)
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

-- Предмет на карте в точке position (как у ItemSpawnService: Part, uid в реестре, подсказка «Поднять»).
local function mapItem(ctx: Context, position: Vector3): (string, BasePart)
	local folder = workspace:FindFirstChild(ITEMS_FOLDER)
	if not folder then
		folder = Instance.new("Folder")
		folder.Name = ITEMS_FOLDER
		folder.Archivable = false
		folder.Parent = workspace
	end
	local part = ItemFactory.Create(TEST_ITEM)
	part.Anchored = true
	part.CFrame = CFrame.new(position)
	part.Parent = folder
	local uid = ItemRegistry.CreateOnMap(TEST_ITEM, part)
	CarryService.RegisterMapItem(uid, part)
	table.insert(ctx.items, uid)
	return uid, part
end

-- Игрок поднимает новый предмет с карты (через обработчик подсказки «Поднять»).
local function carry(ctx: Context, player: any): string
	local position = player.Character.PrimaryPart.Position + Vector3.new(0, 0, 3)
	local uid = mapItem(ctx, position)
	CarryService.Handlers.Pickup(player, uid)
	check(ItemRegistry.GetCarriedBy(player) == uid, player.Name .. " не поднял предмет")
	return uid
end

-- Игрок приносит предмет и выставляет его на свою витрину slot.
local function displayOwn(ctx: Context, player: any, slot: number): string
	local plot = plotOf(player)
	near(player, plot.showcases[slot])
	local uid = carry(ctx, player)
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
	StorageService.Handlers.StoreDisplayed(B, plotA, 1)
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
	StorageService.Handlers.StoreCarried(B, plotA)
	check(ItemRegistry.GetCarriedBy(B) == uid, "предмет ушёл из рук B")
	check(ItemRegistry.CountStored(A.UserId) == 0 and ItemRegistry.CountStored(B.UserId) == 0, "предмет в хранилище")
	check(B:WasNotified("Это чужой музей"), "нет сообщения «Это чужой музей»")
end)

test("Нельзя выставить предмет из чужого хранилища или по поддельному uid", function(A, B, ctx)
	local uid = displayOwn(ctx, A, 1)
	local plotA, plotB = plotOf(A), plotOf(B)
	near(A, plotA.showcases[1])
	StorageService.Handlers.StoreDisplayed(A, plotA, 1)
	check(ItemRegistry.Get(uid).state == "Stored", "A не убрал экспонат в хранилище")
	near(B, plotB.showcases[1])
	for _, forged in { uid, "не-uid", 42 :: any, string.rep("x", 100) } do
		StorageService.Handlers.DisplayFromStorage(B, forged, 1)
	end
	local entry = ItemRegistry.Get(uid)
	check(entry.state == "Stored" and entry.owner == A.UserId, "предмет A сдвинулся")
	check(ItemRegistry.GetSlotItem(B.UserId, 1) == nil and next(DataService.GetData(B).items) == nil, "у B экспонат")
	check(DataService.GetData(A).items[uid].place == "storage", "запись A изменилась")
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
	StorageService.Handlers.StoreDisplayed(A, plotA, 3)
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

test("Ночь: несомое теряется, из коридора — в Safe Zone, барьер до рассвета", function(A, B, ctx)
	local corridor = Vector3.new(10, MapLayout.Heights.Path + 3, MapLayout.ZoneStartZ(1) - 40)
	A:MoveTo(corridor)
	local uidA = carry(ctx, A)
	B:MoveTo(MapLayout.Spawn.position + Vector3.new(20, 3, 20))
	local uidB = carry(ctx, B)
	local day = GameTime.At(GameConfig.Time.Epoch)
	local nightState = GameTime.At(GameConfig.Time.Epoch + GameConfig.Time.DayLength)
	NightService.Handlers.Apply(nightState, day, { A, B })
	check(not MapLayout.InDangerZone(A.Character.PrimaryPart.Position), "A остался в коридоре")
	check((A.Character.PrimaryPart.Position - MapLayout.Spawn.position).Magnitude < 20, "A не у места появления")
	check(ItemRegistry.Get(uidA) == nil and ItemRegistry.GetCarriedBy(A) == nil, "предмет A не потерян")
	check(ItemRegistry.Get(uidB) == nil and ItemRegistry.GetCarriedBy(B) == nil, "предмет B не потерян")
	check(A:WasNotified("недоставленный предмет потерян"), "нет сообщения о потере")
	check(NightService.Handlers.Barrier().Parent ~= nil, "барьер не поставлен")
	A:MoveTo(corridor)
	check(NightService.Handlers.Sweep({ A }) == 1, "зашедшего ночью в коридор не вывели")
	NightService.Handlers.Apply(GameTime.At(GameConfig.Time.Epoch + 330), nightState, { A, B })
	check(NightService.Handlers.Barrier().Parent == nil, "барьер не убран на рассвете")
	-- вернуть правила текущей фазы
	NightService.Handlers.Apply(TimeService.Current(), nil, {})
end)

local ServerTests = {}

-- Прогоняет все тесты по очереди: свежие игроки A и B на каждый, после — выход и уборка. Отчёт строкой.
function ServerTests.Run(): string
	if not RunService:IsStudio() then
		return "Серверные тесты запускаются только в Studio"
	end
	local lines, passed = {}, 0
	for _, case in tests do
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
	table.insert(lines, 1, ("Серверные тесты: %d из %d пройдено"):format(passed, #tests))
	return table.concat(lines, "\n")
end

return ServerTests

-- «Бросок вдаль» на сервере (D75, основной цикл): игрок на площадке запускает шкалу точности, сервер ведёт её фазу по
-- своему времени и принимает от клиента только момент нажатия (Shared/ThrowRules.PressTime: не раньше «сейчас − потолок
-- задержки» и не позже «сейчас» — подделка даёт не больше идеального попадания). По нажатию (или по истечении времени —
-- с точностью 0) списывается один Ловибум и сервер решает всё сразу: дальность (сила × точность × вид, не дальше зоны
-- уровня Ловибума), зону и глубину приземления, удачу, редкость существа (D37) и этажа (D74), шанс босса зоны.
-- Награда — капсула в руки на площадке (реестр: новая запись → Carried, граф §1 не меняется) или сразу продажа, если
-- её берёт фильтр авто-продажи игрока (в том числе повтор «Уже есть»: в башне не бывает двух одинаковых этажей).
-- Клиент только показывает: шкалу (ThrowState), полёт (ThrowFlight — всем, с ником) и экран выпадения (ThrowResult).
-- Порядок: все проверки → запись профиля (Ловибум, рекорд, монеты, босс) → реестр; отказ реестра откатывает запись,
-- между ними нет yield.
-- Ещё: продажа капсулы из рук, фильтр авто-продажи, выбор босса для крыши.
-- ThrowService.Random — подмена случайных чисел по очереди (тесты и DEV): существо, предмет, этаж, босс.
-- ThrowService.Scale — подмена периода и начала шкалы (тесты): { period, phase }.
-- Зависит от DataService, ItemRegistry, CarryService, IncomeService, AnnounceService, TimeService, Remotes,
-- Shared/ThrowRules, CatchRules, TutorialRules, GameTime, Config/Throw, Config/Items, Config/FloorRarity,
-- Config/Rarities, World/MapLayout, Util/ItemFactory, Notify, Validate, RateLimiter, Log.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Shared = ReplicatedStorage.Shared
local CatchRules = require(Shared.CatchRules)
local FloorRarity = require(Shared.Config.FloorRarity)
local GameConfig = require(Shared.Config.GameConfig)
local Items = require(Shared.Config.Items)
local Rarities = require(Shared.Config.Rarities)
local Throw = require(Shared.Config.Throw)
local GameTime = require(Shared.GameTime)
local Remotes = require(Shared.Remotes)
local ThrowRules = require(Shared.ThrowRules)
local TutorialRules = require(Shared.TutorialRules)
local Server = ServerScriptService.Server
local AnnounceService = require(Server.Services.AnnounceService)
local CarryService = require(Server.Services.CarryService)
local DataService = require(Server.Services.DataService)
local IncomeService = require(Server.Services.IncomeService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local TimeService = require(Server.Services.TimeService)
local ItemFactory = require(Server.Util.ItemFactory)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local RateLimiter = require(Server.Util.RateLimiter)
local Validate = require(Server.Util.Validate)
local MapLayout = require(Server.World.MapLayout)

local ThrowService = {}

ThrowService.Random = nil :: (() -> number)?
ThrowService.Scale = nil :: { period: number, phase: number }?

type Session = {
	player: any,
	level: number,
	kind: string,
	startedAt: number, -- время сервера
	period: number,
	phase: number,
	token: number,
}

local rng = Random.new()
local limiter = RateLimiter.new(GameConfig.RateLimits.Throw)
local sessions: { [any]: Session } = {}
local tokens = 0
local itemsFolder: Folder? = nil

local function now(): number
	return workspace:GetServerTimeNow()
end

local function random(): number
	local hook = ThrowService.Random
	return if hook then hook() else rng:NextNumber()
end

local function count(): number
	local n = 0
	for _ in sessions do
		n += 1
	end
	return n
end

-- Набор зоны: существа редкости rarity из коллекции зоны; если такой редкости в коллекции нет — ближайшая ниже.
local pools: { [number]: { [string]: { string } } } = {}
local function pool(zone: number, rarity: string): { string }
	if not pools[zone] then
		local byRarity: { [string]: { string } } = {}
		for id, def in Items do
			if def.boss == zone and not def.legacy and def.income > 0 then
				byRarity[def.rarity] = byRarity[def.rarity] or {}
				table.insert(byRarity[def.rarity], id)
			end
		end
		for _, list in byRarity do
			table.sort(list)
		end
		pools[zone] = byRarity
	end
	for i = Rarities.Rank(rarity), 1, -1 do
		local list = pools[zone][Rarities.Order[i]]
		if list and #list > 0 then
			return list
		end
	end
	return {}
end

-- Есть ли в зоне хоть одно существо (уровни без коллекции бросать нельзя).
function ThrowService.ZoneReady(zone: number): boolean
	return #pool(zone, Rarities.Order[#Rarities.Order]) > 0
end

-- Отказ начала броска (сообщение) или nil.
local function refusal(player: any, level: any, kind: any): string?
	local data = DataService.GetData(player)
	if not data then
		return "Профиль ещё не загружен"
	end
	if TutorialRules.IsActive(data) then
		return "Сначала пройдите обучение"
	end
	if sessions[player] then
		return "Вы уже бросаете"
	end
	if not CatchRules.IsLevel(level) or not CatchRules.IsKind(kind) then
		return "Нет такого Ловибума"
	end
	if GameTime.IsNight(TimeService.Current().phase) then
		return "Ночью трасса закрыта"
	end
	if player:GetAttribute("Catching") then
		return "Сначала закончите поимку"
	end
	if ItemRegistry.GetCarriedBy(player) then
		return "Руки заняты — сначала отнесите или продайте капсулу"
	end
	local pad = MapLayout.ThrowPad
	if not Validate.IsNear(player, pad.position, pad.radius) then
		return "Бросать можно только с площадки"
	end
	if not ThrowService.ZoneReady(level) then
		return "Эта зона ещё не открыта"
	end
	if CatchRules.Stock(DataService.Lovibums(player), level, kind) < 1 then
		return "Нет такого Ловибума — купите в магазине"
	end
	if count() >= Throw.Pad.Places then
		return "Площадка занята — подождите"
	end
	return nil
end

local function sendState(player: any, session: Session?)
	if not session then
		Remotes.FireClient(Remotes.Names.ThrowState, player, nil)
		return
	end
	Remotes.FireClient(Remotes.Names.ThrowState, player, {
		level = session.level,
		kind = session.kind,
		at = session.startedAt,
		period = session.period,
		phase = session.phase,
		timeout = Throw.Scale.Timeout,
	})
end

-- Полёт виден всем (ник над Ловибумом): каждому игроку сервера и бросавшему (тестового игрока нет в Players).
local function broadcastFlight(player: any, payload: { [string]: any })
	local sent = false
	for _, other in Players:GetPlayers() do
		Remotes.FireClient(Remotes.Names.ThrowFlight, other, payload)
		sent = sent or other == player
	end
	if not sent then
		Remotes.FireClient(Remotes.Names.ThrowFlight, player, payload)
	end
end

local function bossKey(zone: number): string
	return "Z" .. zone
end

-- Бросок состоялся: качество нажатия 0…1. Все проверки заново — между шкалой и нажатием прошло время.
local function resolve(session: Session, quality: number)
	local player = session.player
	if sessions[player] ~= session then
		return
	end
	sessions[player] = nil
	sendState(player, nil)
	local data = DataService.GetData(player)
	local throw = DataService.Throw(player)
	if not data or not throw then
		return
	end
	if GameTime.IsNight(TimeService.Current().phase) then
		Notify.Send(player, "Ночью трасса закрыта", "Stop")
		return
	end
	if ItemRegistry.GetCarriedBy(player) then
		Notify.Send(player, "Руки заняты — бросок отменён", "Stop")
		return
	end
	local level, kind = session.level, session.kind

	-- расчёт: дальность, зона, удача, розыгрыш (сервер)
	local distance = ThrowRules.Distance(data.strength, quality, kind, level)
	local zone, depth = ThrowRules.Landing(distance, level)
	local luck = ThrowRules.Luck(depth)
	local rarity = ThrowRules.RollCreature(zone, luck, kind, random())
	local list = pool(zone, rarity)
	if #list == 0 then
		Notify.Send(player, "Эта зона ещё не открыта", "Stop")
		return
	end
	local itemId = list[math.clamp(math.floor(random() * #list) + 1, 1, #list)]
	rarity = Items[itemId].rarity -- если редкости в коллекции не было — выпала ближайшая ниже
	local floor = ThrowRules.RollFloor(rarity, luck, kind, random())
	local boss = ThrowRules.IsBoss(random())
	local chance = ThrowRules.Chance(zone, luck, kind, rarity, floor)
	local duplicate = ItemRegistry.FindTwin(player.UserId, itemId, floor) ~= nil
	local income = IncomeService.Of(itemId, floor)
	local price = ThrowRules.SellPrice(income)
	local sold = ThrowRules.AutoSell(throw.autoSell, rarity, floor, duplicate)

	-- профиль: Ловибум, рекорд, монеты за авто-продажу, босс
	if not DataService.SpendLovibum(player, level, kind) then
		Notify.Send(player, "Нет такого Ловибума — купите в магазине", "Stop")
		return
	end
	local oldRecord, oldRoof = throw.record, throw.roof
	local isRecord = distance > throw.record
	if isRecord then
		throw.record = distance
	end
	if sold then
		DataService.AddCoins(player, price)
	end
	if boss then
		local key = bossKey(zone)
		throw.bosses[key] = (throw.bosses[key] or 0) + 1
		throw.roof = throw.roof or zone -- первый босс сам встаёт на крышу
	end

	-- реестр: капсула в руки (если не продана)
	local uid: string? = nil
	if not sold then
		local part = ItemFactory.Create(itemId)
		local root = Validate.GetLiveRoot(player)
		part.Anchored = true
		part.CFrame = if root then root.CFrame * CFrame.new(0, 0, -3) else CFrame.new(MapLayout.ThrowPad.position)
		part.Parent = itemsFolder or workspace
		local created = ItemRegistry.CreateReward(itemId, part, zone, floor)
		if not ItemRegistry.Transition(created, "Carried", { carrier = player }) then
			-- откат записи профиля: Ловибум, рекорд и босс возвращаются как были
			ItemRegistry.Discard(created, "бросок: капсулу не удалось выдать")
			part:Destroy()
			DataService.RefundLovibum(player, level, kind)
			throw.record, throw.roof = oldRecord, oldRoof
			if boss then
				local key = bossKey(zone)
				throw.bosses[key] = if throw.bosses[key] > 1 then throw.bosses[key] - 1 else nil
			end
			Notify.Send(
				player,
				"Не удалось выдать капсулу — Ловибум возвращён",
				"Stop"
			)
			return
		end
		CarryService.RegisterMapItem(created, part)
		CarryService.AttachCarried(player, created)
		uid = created
	end

	player:SetAttribute("ThrowRecord", math.floor(throw.record + 0.5))
	if sold then
		player:SetAttribute("Coins", data.coins)
	end
	if boss then
		IncomeService.Handlers.Refresh(player)
		AnnounceService.BossWon(player, zone)
	end
	AnnounceService.FloorWon(player, floor)
	DataService.RequestSave(player)
	Log.Debug(
		"ThrowService",
		("%s: %s ур. %d — %.0f м, зона %d (глубина %.2f, удача ×%.2f), %s на этаже «%s»%s%s"):format(
			player.Name,
			kind,
			level,
			distance,
			zone,
			depth,
			luck,
			itemId,
			FloorRarity.Names[floor],
			if sold then (" — продано за %d"):format(price) else "",
			if boss then " + БОСС" else ""
		)
	)
	local at = now()
	broadcastFlight(player, {
		user = player.UserId,
		name = player.DisplayName or player.Name,
		level = level,
		kind = kind,
		distance = distance,
		zone = zone,
		at = at,
	})
	Remotes.FireClient(Remotes.Names.ThrowResult, player, {
		at = at,
		level = level,
		kind = kind,
		quality = quality,
		distance = distance,
		zone = zone,
		depth = depth,
		luck = luck,
		itemId = itemId,
		rarity = rarity,
		floor = floor,
		chance = chance,
		oneIn = ThrowRules.OneIn(chance),
		income = income,
		duplicate = duplicate,
		sold = sold,
		price = price,
		uid = uid,
		boss = if boss then zone else nil,
		record = isRecord,
	})
end

-- Начать бросок: шкала пошла. true — началось.
function ThrowService.Start(player: any, level: any, kind: any): boolean
	local reason = refusal(player, level, kind)
	if reason then
		Notify.Send(player, reason, "Stop")
		return false
	end
	local scale = ThrowService.Scale
	local jitter = (rng:NextNumber() * 2 - 1) * Throw.Scale.PeriodJitter
	tokens += 1
	local session: Session = {
		player = player,
		level = level,
		kind = kind,
		startedAt = now(),
		period = if scale then scale.period else Throw.Scale.Period + jitter,
		phase = if scale then scale.phase else rng:NextNumber(),
		token = tokens,
	}
	sessions[player] = session
	sendState(player, session)
	task.delay(Throw.Scale.Timeout, function()
		if sessions[player] == session then
			resolve(session, 0) -- не нажал вовремя: бросок с точностью 0
		end
	end)
	return true
end

-- Нажатие: claimed — момент нажатия по оценке клиента (время сервера). true — бросок состоялся.
function ThrowService.Press(player: any, claimed: any): boolean
	local session = sessions[player]
	if not session then
		return false
	end
	local t = ThrowRules.PressTime(now(), claimed)
	local position = ThrowRules.ScalePosition(t - session.startedAt, session.period, session.phase)
	resolve(session, ThrowRules.Quality(position))
	return true
end

-- Отменить шкалу до нажатия (Ловибум не тратится).
function ThrowService.Cancel(player: any)
	if sessions[player] then
		sessions[player] = nil
		sendState(player, nil)
	end
end

-- Идёт ли у игрока шкала.
function ThrowService.Throwing(player: any): boolean
	return sessions[player] ~= nil
end

-- Продать капсулу из рук: монеты — доход этажа за SellSeconds секунд. Краденое и учебное существо не продаются.
function ThrowService.SellCarried(player: any): boolean
	local data = DataService.GetData(player)
	local uid = ItemRegistry.GetCarriedBy(player)
	local entry = uid and ItemRegistry.Get(uid)
	if not data or not uid or not entry or entry.state ~= "Carried" or entry.carrier ~= player then
		Notify.Send(player, "В руках нет капсулы на продажу", "Stop")
		return false
	end
	local tutorial = DataService.Tutorial(player)
	if tutorial and tutorial.uid == uid then
		Notify.Send(player, "Учебное существо не продаётся", "Stop")
		return false
	end
	local price = ThrowRules.SellPrice(IncomeService.Of(entry.itemId, entry.floorRarity))
	if not DataService.AddCoins(player, price) then
		return false
	end
	if not CarryService.LoseCarried(player, "продано") then
		DataService.AddCoins(player, -price)
		return false
	end
	player:SetAttribute("Coins", data.coins)
	DataService.RequestSave(player)
	Notify.Send(player, ("Продано: %s — +%d"):format(Items[entry.itemId].displayName, price), "Go")
	return true
end

-- Фильтр авто-продажи: { creature = редкость существа, floor = редкость этажа, duplicates = продавать повторы };
-- nil или пустая таблица — выключить. Чужие ключи отбрасываются.
function ThrowService.SetAutoSell(player: any, filter: any): boolean
	local throw = DataService.Throw(player)
	if not throw then
		return false
	end
	local clean: { [string]: any } = {}
	if type(filter) == "table" then
		if table.find(Rarities.Order, filter.creature) and table.find(FloorRarity.Order, filter.floor) then
			clean.creature, clean.floor = filter.creature, filter.floor
		end
		if filter.duplicates == true then
			clean.duplicates = true
		end
	end
	throw.autoSell = if next(clean) then clean else nil
	DataService.RequestSave(player)
	return true
end

-- Какой из своих боссов стоит на крыше (zone — зона босса, который у игрока есть).
function ThrowService.SetRoof(player: any, zone: any): boolean
	local throw = DataService.Throw(player)
	if not throw or type(zone) ~= "number" or zone ~= math.floor(zone) or (throw.bosses[bossKey(zone)] or 0) < 1 then
		Notify.Send(player, "Такого босса у вас нет", "Stop")
		return false
	end
	throw.roof = zone
	IncomeService.Handlers.Refresh(player)
	DataService.RequestSave(player)
	return true
end

local function onAction(player: any, action: any, a: any, b: any)
	if not limiter:Allow(player) then
		return
	end
	if action == "Start" then
		ThrowService.Start(player, a, b)
	elseif action == "Press" then
		ThrowService.Press(player, a)
	elseif action == "Cancel" then
		ThrowService.Cancel(player)
	elseif action == "Sell" then
		ThrowService.SellCarried(player)
	elseif action == "AutoSell" then
		ThrowService.SetAutoSell(player, a)
	elseif action == "Roof" then
		ThrowService.SetRoof(player, a)
	else
		Log.Warn(
			"ThrowService",
			("%s: неизвестное действие %s — отклонено"):format(
				player.Name,
				tostring(action)
			)
		)
	end
end

-- Игрок вышел или погиб: шкала снимается, Ловибум не тратится.
function ThrowService.OnPlayerRemoving(player: any)
	sessions[player] = nil
end

function ThrowService.Init()
	local folder = Instance.new("Folder")
	folder.Name = "ThrowItems"
	folder.Parent = workspace
	itemsFolder = folder
	Remotes.Get(Remotes.Names.ThrowAction).OnServerEvent:Connect(onAction)
	Players.PlayerRemoving:Connect(ThrowService.OnPlayerRemoving)
	TimeService.OnPhaseChanged(function(state)
		if GameTime.IsNight(state.phase) then -- ночь: трасса закрыта, начатые шкалы снимаются
			for player in sessions do
				ThrowService.Cancel(player)
				Notify.Send(player, "Ночью трасса закрыта", "Stop")
			end
		end
	end)
end

-- Для серверных тестов.
ThrowService.Handlers = {
	Action = onAction,
	Session = function(player: any): Session?
		return sessions[player]
	end,
}

return ThrowService

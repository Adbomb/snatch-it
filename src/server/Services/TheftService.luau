-- Кража в Судную ночь (D37, D46). На каждом постаменте — подсказка «Украсть» с удержанием GameConfig.Theft.HoldSeconds
-- (E на ПК, экранная кнопка на телефоне); клиент показывает её только чужим в Судную ночь, но сервер проверяет всё
-- сам: начало удержания (PromptButtonHoldBegan) резервирует экспонат, музей и вора (Util/TheftLedger), отпускание или
-- уход отменяет, завершение (Triggered) проверяет, что удержание длилось нужное время и вор рядом. Снятый экспонат
-- (Stolen) вор несёт к сундуку своего музея; сдача — передача владения с журналом (DESIGN §6, Util/TransferJournal,
-- DataService): запись — у вора в инвентаре (Stored, без дохода до выставления), у прежнего владельца удалена.
-- Провал — вор отпустил, бросил, проиграл, вышел, его вынесло ночью или вышли 10 с доставки — экспонат сразу
-- возвращается на свой постамент (не падает и не подбирается). Владелец вышел — кража отменяется, экспонат у него.
-- Зависит от ItemRegistry, CarryService, DataService, InventoryService, MuseumService, PlotService, Shared/GameTime,
-- Util/TheftLedger, Util/*, GameConfig, Config/Items.

local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local DataService = require(Server.Services.DataService)
local InventoryService = require(Server.Services.InventoryService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local MuseumService = require(Server.Services.MuseumService)
local PlotService = require(Server.Services.PlotService)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local Prompts = require(Server.Util.Prompts)
local RateLimiter = require(Server.Util.RateLimiter)
local TheftLedger = require(Server.Util.TheftLedger)
local Validate = require(Server.Util.Validate)

local cfg = GameConfig.Theft
local ledger = TheftLedger.new(cfg.HoldSeconds, cfg.HoldTolerance)
local limiter = RateLimiter.new(GameConfig.RateLimits.Steal)
local parts: { [string]: BasePart } = {} -- uid → Part экспоната, снятого с вора на время передачи

local TheftService = {}

local function phase(): string?
	return GameTime.TheftPhase(GameTime.Now())
end

local function nameOf(uid: string): string
	local entry = ItemRegistry.Get(uid)
	local def = entry and Items[entry.itemId]
	return if def then def.displayName else "экспонат"
end

-- Игрок с участком (настоящий или тестовый) по UserId и его участок.
local function ownerOf(userId: number): (any, PlotService.Plot?)
	for _, plot in PlotService.GetPlots() do
		if plot.owner and plot.owner.UserId == userId then
			return plot.owner, plot
		end
	end
	return nil, nil
end

-- Экспонат обратно на свой постамент; владельца нет на сервере — выгрузить (в его профиле он на месте).
local function returnToOwner(theft: TheftLedger.Theft, message: string?)
	local uid = theft.uid
	local entry = ItemRegistry.Get(uid)
	if not entry or (entry.state ~= "Lifting" and entry.state ~= "Stolen") then
		parts[uid] = nil
		return
	end
	local thief = entry.carrier or entry.thief
	local part = parts[uid] or entry.part
	if entry.state == "Stolen" and thief then
		part = CarryService.ReleaseStolen(thief, uid) or part
	end
	parts[uid] = nil
	local owner, plot = ownerOf(theft.owner)
	if not owner or not plot then
		ItemRegistry.Unload(uid)
		if part then
			part:Destroy()
		end
		return
	end
	if not ItemRegistry.Transition(uid, "Displayed", { owner = theft.owner, slot = theft.slot, part = part }) then
		Log.Warn("TheftService", ("%s не вернулся на постамент %d"):format(uid, theft.slot))
		return
	end
	if part then
		local data = DataService.GetData(owner)
		local record = data and data.items[uid]
		MuseumService.PlaceExhibit(part, plot, theft.slot, if record then record.rot or 0 else 0)
	end
	if message then
		local thiefPlayer = ownerOf(theft.thief)
		if thiefPlayer then
			Notify.Send(thiefPlayer, message, "Stop")
		end
		Notify.Send(owner, ("«%s» вернулся на постамент %d"):format(nameOf(uid), theft.slot), "Go")
	end
end

-- Кража сорвалась (кроме передачи владения): резерв снят, лимиты не тратятся, экспонат — владельцу.
local function fail(thief: any, message: string?): boolean
	local theft = ledger:Fail(thief.UserId)
	if theft then
		returnToOwner(theft, message)
		return true
	end
	return false
end

-- Удержание «Украсть» началось.
local function tryBegin(thief: any, plot: PlotService.Plot, slot: number)
	if not limiter:Allow(thief) then
		return
	end
	local owner = plot.owner
	if not owner or not DataService.GetData(thief) or not DataService.GetData(owner) then
		return
	end
	if not Validate.IsNear(thief, plot.showcases[slot].Position, cfg.Distance + 1) then
		return
	end
	local uid = ItemRegistry.GetSlotItem(owner.UserId, slot)
	local entry = uid and ItemRegistry.Get(uid)
	local event = GameTime.DoomEventId(GameTime.Now())
	local args: TheftLedger.BeginArgs = {
		event = event or -1,
		phase = phase(),
		thief = thief.UserId,
		owner = owner.UserId,
		uid = uid or "",
		slot = slot,
		-- экспонат, который уже снимают или несут (Lifting, Stolen), числится за постаментом: отказ «уже крадут»
		displayedBy = if entry
				and (entry.state == "Displayed" or entry.state == "Lifting" or entry.state == "Stolen")
			then entry.owner
			else nil,
		carrying = ItemRegistry.GetCarriedBy(thief) ~= nil,
		thiefDone = event ~= nil and DataService.GetStat(thief, "theftEvent") == event,
		ownerLost = event ~= nil and DataService.GetStat(owner, "lossEvent") == event,
		knocked = thief:GetAttribute("Knocked") == true,
	}
	local ok, reason = ledger:Begin(args, os.clock())
	if not ok then
		Notify.Send(thief, reason or "Украсть нельзя", "Stop")
		return
	end
	if not ItemRegistry.Transition(uid :: string, "Lifting", { thief = thief }) then
		ledger:Fail(thief.UserId)
	end
end

-- Отпустил E или ушёл: снятие отменено (только пока экспонат ещё на постаменте).
local function tryCancel(thief: any)
	local theft = ledger:ByThief(thief.UserId)
	if theft and theft.stage == "Lifting" then
		fail(thief, nil)
	end
end

-- Удержание закончено: экспонат у вора.
local function tryComplete(thief: any, plot: PlotService.Plot, slot: number)
	local theft = ledger:ByThief(thief.UserId)
	local owner = plot.owner
	if not theft or theft.stage ~= "Lifting" or theft.slot ~= slot or not owner or theft.owner ~= owner.UserId then
		return -- без начала удержания (подделанный Triggered) ничего не происходит
	end
	if not Validate.IsNear(thief, plot.showcases[slot].Position, cfg.Distance + 1) then
		fail(thief, "Слишком далеко — кража сорвалась")
		return
	end
	local ok, reason = ledger:Complete(thief.UserId, theft.uid, os.clock(), phase())
	if not ok then
		fail(thief, reason)
		return
	end
	if not ItemRegistry.Transition(theft.uid, "Stolen", { carrier = thief }) then
		fail(thief, "Кража сорвалась")
		return
	end
	plot.showcases[slot]:SetAttribute("Occupied", false)
	if not CarryService.AttachCarried(thief, theft.uid) then
		fail(thief, "Кража сорвалась")
		return
	end
	Notify.Send(
		thief,
		("Добыча у вас: несите «%s» к сундуку своего музея!"):format(
			nameOf(theft.uid)
		),
		"Go"
	)
	Notify.Send(
		owner,
		("Вор унёс «%s» с постамента %d — догоните его!"):format(
			nameOf(theft.uid),
			slot
		),
		"Stop"
	)
end

-- Шаги 3–4 журнала после передачи: сохранить жертву, отметить, сохранить вора, снять pending, удалить запись.
local function confirm(victim: any, thief: any, uid: string, id: string)
	local victimSaved = DataService.SaveAndWait(victim, cfg.SaveTimeout)
	if not victimSaved then
		local items = DataService.ReadSavedItems(victim.UserId)
		victimSaved = items ~= nil and items[uid] == nil
	end
	if not victimSaved then
		Log.Warn(
			"TheftService",
			("передача %s: жертва не сохранилась — решит журнал при входе вора"):format(
				uid
			)
		)
		return
	end
	DataService.JournalUpdate(thief.UserId, function(list)
		for _, entry in list do
			if entry.id == id then
				entry.state = "victimSaved"
			end
		end
		return list
	end)
	DataService.ClearPending(thief, uid, id)
	if DataService.SaveAndWait(thief, cfg.SaveTimeout) then
		DataService.JournalUpdate(thief.UserId, function(list)
			local keep = {}
			for _, entry in list do
				if entry.id ~= id then
					table.insert(keep, entry)
				end
			end
			return keep
		end)
	end
	if DataService.GetData(thief) then
		InventoryService.Sync(thief)
	end
end

-- Передача владения сорвалась до записи профилей: резерв снят, экспонат — владельцу.
local function abortDelivery(thief: any, id: string?, message: string)
	local theft = ledger:AbortDelivery(thief.UserId)
	if id then
		DataService.JournalUpdate(thief.UserId, function(list)
			local keep = {}
			for _, entry in list do
				if entry.id ~= id then
					table.insert(keep, entry)
				end
			end
			return keep
		end)
	end
	if theft then
		returnToOwner(theft, message)
	end
end

-- Вор у сундука своего музея (InventoryService.tryStoreCarried): сдача добычи.
local function deliver(thief: any, plot: PlotService.Plot)
	if plot.owner ~= thief then
		return
	end
	local uid = ItemRegistry.GetCarriedBy(thief)
	local entry = uid and ItemRegistry.Get(uid)
	local theft = ledger:ByThief(thief.UserId)
	if not uid or not entry or entry.state ~= "Stolen" or not theft or theft.uid ~= uid then
		return
	end
	local ok, reason = ledger:StartDelivery(thief.UserId, uid, phase())
	if not ok then
		Notify.Send(thief, reason or "Сдать нельзя", "Stop")
		return
	end
	local victim = ownerOf(theft.owner)
	local victimData = victim and DataService.GetData(victim)
	local original = victimData and victimData.items[uid]
	if not victim or not original then
		abortDelivery(thief, nil, "Хозяина экспоната уже нет — кража сорвалась")
		return
	end
	local part = CarryService.ReleaseStolen(thief, uid)
	if part then
		parts[uid] = part
		part.Parent = nil -- пока идёт передача, экспоната не видно
	end
	local id = HttpService:GenerateGUID(false)
	local record = {
		id = original.id,
		mods = table.clone(original.mods or {}),
		place = "storage",
		rot = 0,
		acquiredAt = os.time(),
		source = "raid",
		boss = original.boss,
		from = theft.owner,
	}
	-- Шаг 1: журнал до любых изменений профилей (ждёт DataStore).
	local journaled = DataService.JournalUpdate(thief.UserId, function(list)
		table.insert(
			list,
			{ id = id, uid = uid, from = theft.owner, record = record, state = "pending", at = os.time() }
		)
		return list
	end)
	local now = ItemRegistry.Get(uid)
	if
		not journaled
		or not DataService.GetData(thief)
		or not DataService.GetData(victim)
		or not now
		or now.state ~= "Stolen"
		or now.carrier ~= thief
	then
		abortDelivery(
			thief,
			if journaled then id else nil,
			"Не удалось сдать добычу — она вернулась владельцу"
		)
		return
	end
	-- Шаг 2: в одном кадре без yield — профили и реестр.
	if not DataService.TransferItem(victim, thief, uid, record, id) then
		abortDelivery(
			thief,
			id,
			"Не удалось сдать добычу — она вернулась владельцу"
		)
		return
	end
	if not ItemRegistry.Transition(uid, "Stored", { owner = thief.UserId }) then
		DataService.UndoTransfer(victim, thief, uid, original)
		abortDelivery(
			thief,
			id,
			"Не удалось сдать добычу — она вернулась владельцу"
		)
		return
	end
	DataService.SetStat(thief, "theftEvent", theft.event)
	DataService.IncrementStat(thief, "thefts")
	DataService.SetStat(victim, "lossEvent", theft.event)
	DataService.IncrementStat(victim, "lost")
	ledger:Finish(thief.UserId, uid)
	local kept = parts[uid]
	parts[uid] = nil
	if kept then
		kept:Destroy()
	end
	InventoryService.Sync(thief)
	InventoryService.Sync(victim)
	local def = Items[record.id]
	local name = if def then def.displayName else tostring(record.id)
	Notify.Send(
		thief,
		("Украдено: «%s» — теперь в вашем инвентаре"):format(name),
		"Go"
	)
	Notify.Send(victim, ("У вас украли «%s»"):format(name), "Stop")
	Log.Debug("TheftService", ("%s украл %s у %s"):format(thief.Name, uid, victim.Name))
	task.spawn(confirm, victim, thief, uid, id)
end

-- Время вышло: снятие — только в Судную ночь, донести — до конца 10 с доставки.
local function sweep()
	local current = phase()
	for _, theft in ledger:All() do
		local thief = ownerOf(theft.thief)
		if theft.stage == "Lifting" and current ~= "Open" then
			local failed = ledger:Fail(theft.thief)
			if failed then
				returnToOwner(
					failed,
					if thief
						then "Судная ночь закончилась — кража сорвалась"
						else nil
				)
			end
		elseif theft.stage == "Carrying" and current == nil then
			local failed = ledger:Fail(theft.thief)
			if failed then
				returnToOwner(
					failed,
					"Время доставки вышло — добыча вернулась владельцу"
				)
			end
		end
	end
end

-- Вор проиграл в PvP (D37): добыча сразу возвращается владельцу.
function TheftService.OnDefeated(player: any)
	fail(player, "Вы проиграли — добыча вернулась владельцу")
end

-- Игрок вышел (PlayerSession.Leave, до выгрузки музея): как вор — провал; как владелец — кража его экспоната
-- отменяется, экспонат остаётся у него в профиле.
function TheftService.OnPlayerLeaving(player: any)
	fail(player, nil)
	for _, uid in ItemRegistry.GetBeingStolenFrom(player.UserId) do
		local theft = ledger:ByUid(uid)
		if theft and theft.stage ~= "Delivering" then
			ledger:Fail(theft.thief)
			local entry = ItemRegistry.Get(uid)
			local carrier = entry and (entry.carrier or entry.thief)
			local part = entry and entry.part
			if entry and entry.state == "Stolen" and carrier then
				part = CarryService.ReleaseStolen(carrier, uid) or part
			end
			ItemRegistry.Unload(uid)
			if part then
				part:Destroy()
			end
			if carrier then
				Notify.Send(carrier, "Хозяин музея ушёл — добыча исчезла", "Stop")
			end
		end
	end
end

-- Кража, которую сейчас ведёт игрок (для интерфейса и тестов).
function TheftService.Current(player: any): TheftLedger.Theft?
	return ledger:ByThief(player.UserId)
end

function TheftService.Init()
	for _, plot in PlotService.GetPlots() do
		for slot, showcase in plot.showcases do
			local prompt = Prompts.Create(showcase, "Steal", "Постамент " .. slot, cfg.Distance)
			prompt.HoldDuration = cfg.HoldSeconds
			prompt.PromptButtonHoldBegan:Connect(function(player)
				tryBegin(player, plot, slot)
			end)
			prompt.PromptButtonHoldEnded:Connect(function(player)
				tryCancel(player)
			end)
			prompt.Triggered:Connect(function(player)
				tryComplete(player, plot, slot)
			end)
		end
	end
	InventoryService.SetStolenDelivery(deliver)
	CarryService.SetStolenHandler(function(player, uid, reason)
		local theft = ledger:ByThief(player.UserId)
		if theft and theft.uid == uid then
			fail(player, ("Добыча вернулась владельцу (%s)"):format(reason))
		end
	end)
	task.spawn(function()
		while true do
			task.wait(cfg.CheckSeconds)
			if next(ledger:All()) ~= nil then
				sweep()
			end
		end
	end)
end

-- Обработчики для серверных тестов: те же функции, что вызывают подсказка и сундук.
TheftService.Handlers = {
	Begin = tryBegin,
	Cancel = tryCancel,
	Complete = tryComplete,
	Deliver = deliver,
	Sweep = sweep,
	Ledger = ledger,
}

return TheftService

-- Кража в Судную ночь (D37, D46). На каждом постаменте — подсказка «Украсть» с удержанием GameConfig.Theft.HoldSeconds
-- (E на ПК, экранная кнопка на телефоне); клиент показывает её только чужим в Судную ночь, но сервер проверяет всё
-- сам: начало удержания (PromptButtonHoldBegan) резервирует экспонат, музей и вора (Util/TheftLedger), отпускание или
-- уход отменяет, завершение (Triggered) проверяет, что удержание длилось нужное время. И в начале, и в конце вор
-- должен быть рядом, внутри музея (зал или открытая галерея) и видеть экспонат — не через стену (D52,
-- Shared/MuseumSpace). После отменённой или сорванной попытки — пауза RetrySeconds (D52). Вор с добычей не может
-- перемещаться быстрее бега (Services/MoveGuard: при переноске и при сдаче), иначе добыча возвращается. Снятый экспонат
-- (Stolen) вор несёт к сундуку своего музея; сдача — передача владения с журналом (DESIGN §6, Util/TransferJournal,
-- DataService): запись — у вора в инвентаре (Stored, без дохода до выставления), у прежнего владельца удалена.
-- Провал — вор отпустил, бросил, проиграл, вышел, его вынесло ночью или вышли 10 с доставки — экспонат сразу
-- возвращается на свой постамент (не падает и не подбирается). Владелец вышел — кража отменяется, экспонат у него.
-- Слишком быстрая доставка (быстрее прямой на скорости вора, Util/DeliveryRules) — только запись в лог (D53).
-- Передачи, которые при входе вора ждали жертву, перепроверяются во время сессии (WatchTransfers, D53).
-- Зависит от ItemRegistry, CarryService, DataService, InventoryService, MuseumService, PlotService, Shared/GameTime,
-- Util/TheftLedger, Util/DeliveryRules, Shared/MuseumSpace, Util/*, GameConfig, Config/Items.

local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local TutorialRules = require(ReplicatedStorage.Shared.TutorialRules) -- D55: стартовое существо
local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local MuseumSpace = require(ReplicatedStorage.Shared.MuseumSpace)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local DataService = require(Server.Services.DataService)
local DeliveryRules = require(Server.Util.DeliveryRules)
local InventoryService = require(Server.Services.InventoryService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local ItemFactory = require(Server.Util.ItemFactory)
local MoveGuard = require(Server.Services.MoveGuard)
local MuseumService = require(Server.Services.MuseumService)
local PlotService = require(Server.Services.PlotService)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local Prompts = require(Server.Util.Prompts)
local RateLimiter = require(Server.Util.RateLimiter)
local TheftLedger = require(Server.Util.TheftLedger)
local Validate = require(Server.Util.Validate)

local cfg = GameConfig.Theft
local ledger = TheftLedger.new(cfg.HoldSeconds, cfg.HoldTolerance, cfg.RetrySeconds)
local limiter = RateLimiter.new(GameConfig.RateLimits.Steal)
local parts: { [string]: BasePart } = {} -- uid → Part экспоната, снятого с вора на время передачи
-- переноска (D53, проверка времени доставки): вор → где и когда снял, наибольшая скорость, переносы сервером к тому
-- времени
type Carry = { uid: string, at: number, from: Vector3, speed: number, moved: number }
local carries: { [number]: Carry } = {}

local TheftService = {}

local IMPOSSIBLE =
	"Слишком быстрое перемещение — добыча вернулась владельцу"

-- Проверка доступа к экспонату (DefenseService.Init): закрытая усиленная дверь не даёт красть снаружи зала.
-- access(вор, владелец, участок) → nil — можно, иначе причина.
local access: ((any, any, PlotService.Plot) -> string?)? = nil

function TheftService.SetAccessCheck(check: (any, any, PlotService.Plot) -> string?)
	access = check
end

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
	local alive = part ~= nil
		and pcall(function()
			(part :: BasePart).Parent = (part :: BasePart).Parent -- уничтоженной детали родителя не задать
		end)
	if not alive then
		part = ItemFactory.Create(entry.itemId)
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

-- Кража сорвалась (кроме передачи владения): резерв снят, лимиты не тратятся, экспонат — владельцу; вору — пауза
-- до новой попытки (D52).
local function fail(thief: any, message: string?): boolean
	local theft = ledger:Fail(thief.UserId, os.clock())
	if theft then
		returnToOwner(theft, message)
		return true
	end
	return false
end

-- Может ли вор дотянуться до экспоната места slot: живой, рядом (Distance + 1 на сеть), внутри музея (зал или
-- открытая галерея, не снаружи и не в хранилище) и видит экспонат — между глазами и верхом тумбы нет стены (D52).
-- nil — можно, иначе причина для вора.
local function reachable(thief: any, plot: PlotService.Plot, slot: number): string?
	local showcase = plot.showcases[slot]
	local root = Validate.GetLiveRoot(thief)
	if not showcase or not root then
		return "Кража сорвалась"
	end
	-- свой допуск (не общий DistanceTolerance +4): иначе подделанный клиент крал бы с 12 ст. через арку (D52)
	if (root.Position - showcase.Position).Magnitude > cfg.Distance + cfg.ReachSlack then
		return "Слишком далеко — подойдите к экспонату"
	end
	if not MuseumSpace.Inside(plot, root.Position) then
		return "Красть можно только изнутри музея"
	end
	local eye = root.Position + Vector3.new(0, cfg.EyeHeight, 0)
	local top = showcase.Position + Vector3.new(0, showcase.Size.Y / 2 + cfg.ExhibitLift, 0)
	if not MuseumSpace.Sees(plot, eye, top, showcase) then
		return "Экспонат не видно — подойдите к нему"
	end
	return nil
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
	local blocked = reachable(thief, plot, slot) or (access and access(thief, owner, plot))
	if blocked then
		Notify.Send(thief, blocked, "Stop")
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
		student = thief:GetAttribute("Tutorial") ~= nil,
		protected = uid ~= nil and TutorialRules.IsProtected(DataService.GetData(owner), uid),
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
	local blocked = reachable(thief, plot, slot) or (access and access(thief, owner, plot))
	if blocked then
		fail(thief, blocked)
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
	MoveGuard.Mark(thief) -- отсюда сервер следит, чтобы вор не двигался быстрее бега (D52)
	local root, humanoid = Validate.GetLiveRoot(thief)
	carries[thief.UserId] = if root and humanoid
		then {
			uid = theft.uid,
			at = os.clock(),
			from = root.Position,
			speed = humanoid.WalkSpeed,
			moved = MoveGuard.TransferDistance(thief),
		}
		else nil
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

-- Шаги 3–4 журнала после передачи: дождаться сохранения жертвы с меткой transfersOut[id], снять pending у вора,
-- дождаться сохранения вора с меткой и записью без pending, удалить запись журнала. Не вышло — запись журнала остаётся,
-- передачу решит TransferJournal при следующем входе вора (по меткам; без дублей и потерь).
local function confirm(victim: any, thief: any, uid: string, id: string)
	local victimSaved = false
	local started = os.clock()
	while not victimSaved and os.clock() - started < cfg.ConfirmSeconds do
		victimSaved = DataService.SaveAndWait(victim, cfg.SaveTimeout, function(saved)
			local marks = saved.transfersOut
			return type(marks) == "table" and marks[id] ~= nil
		end)
		if not victimSaved and not DataService.GetData(victim) then
			-- жертва вышла: её финальное сохранение (EndSession) может ещё писаться — читать до SaveTimeout (D52)
			local readUntil = os.clock() + cfg.SaveTimeout
			repeat
				local data = DataService.ReadSaved(victim.UserId)
				victimSaved = data ~= nil and type(data.transfersOut) == "table" and data.transfersOut[id] ~= nil
				if not victimSaved then
					task.wait(cfg.ReadRetrySeconds)
				end
			until victimSaved or os.clock() > readUntil
			break
		end
	end
	if not victimSaved then
		Log.Warn(
			"TheftService",
			("передача %s: сохранение жертвы не подтверждено — решит журнал"):format(
				uid
			)
		)
		return
	end
	DataService.ClearPending(thief, uid, id)
	local thiefSaved = DataService.SaveAndWait(thief, cfg.SaveTimeout, function(saved)
		local marks = saved.transfersIn
		local record = saved.items and saved.items[uid]
		return type(marks) == "table" and marks[id] ~= nil and type(record) == "table" and record.pending == nil
	end)
	if thiefSaved then
		DataService.JournalRemove(thief.UserId, { id })
	end
	if DataService.GetData(thief) then
		InventoryService.Sync(thief)
	end
end

-- Передача владения сорвалась до записи профилей: резерв снят, экспонат — владельцу.
local function abortDelivery(thief: any, id: string?, message: string)
	local theft = ledger:AbortDelivery(thief.UserId)
	if id then
		DataService.JournalRemove(thief.UserId, { id })
	end
	if theft then
		returnToOwner(theft, message)
	end
end

local transferBody: (any, TheftLedger.Theft, string) -> ()

-- Вор с добычей переместился невозможно (D52, MoveGuard). В режиме логирования (MoveGuard.Enforce = false) — только
-- запись в лог, кража идёт дальше; иначе — срыв, добыча владельцу.
local function impossible(thief: any, uid: string): boolean
	if MoveGuard.Step(thief) then
		return false
	end
	if not MoveGuard.Enforced() then
		Log.Warn(
			"TheftService",
			("%s несёт %s: нарушение перемещения записано, кража идёт (режим логирования)"):format(
				tostring(thief.Name),
				uid
			)
		)
		return false
	end
	return true
end

-- Наибольшая скорость вора за переноску (проверка времени доставки, D53).
local function noteSpeed(thief: any)
	local carry = carries[thief.UserId]
	local _, humanoid = Validate.GetLiveRoot(thief)
	if carry and humanoid then
		carry.speed = math.max(carry.speed, humanoid.WalkSpeed)
	end
end

-- Доставка быстрее наименьшего честного времени (D53): только запись в лог и атрибут SuspiciousDeliveries, сдача идёт.
local function checkDeliveryTime(thief: any, uid: string)
	local carry = carries[thief.UserId]
	carries[thief.UserId] = nil
	local root = Validate.GetLiveRoot(thief)
	if not carry or carry.uid ~= uid or not root then
		return
	end
	noteSpeed(thief)
	local elapsed = os.clock() - carry.at
	local offset = root.Position - carry.from
	local distance = Vector3.new(offset.X, 0, offset.Z).Magnitude
	local credit = MoveGuard.TransferDistance(thief) - carry.moved
	local need = DeliveryRules.MinSeconds(distance, credit, carry.speed, cfg.Delivery)
	if DeliveryRules.Suspicious(elapsed, need) then
		thief:SetAttribute("SuspiciousDeliveries", (thief:GetAttribute("SuspiciousDeliveries") or 0) + 1)
		Log.Warn(
			"TheftService",
			("подозрительная доставка %s: %s — %.1f ст. за %.1f с, честно не меньше %.1f с (скорость %.1f, переносы сервером %.1f ст.) — сдача не заблокирована"):format(
				uid,
				tostring(thief.Name),
				distance,
				elapsed,
				need,
				carry.speed,
				credit
			)
		)
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
	if theft.stage == "Carrying" and impossible(thief, uid) then
		fail(thief, IMPOSSIBLE)
		return
	end
	local ok, reason = ledger:StartDelivery(thief.UserId, uid, phase())
	if not ok then
		Notify.Send(thief, reason or "Сдать нельзя", "Stop")
		return
	end
	local checked, why = pcall(checkDeliveryTime, thief, uid)
	if not checked then
		Log.Warn("TheftService", "проверка времени доставки: " .. tostring(why))
	end
	local done, err = pcall(transferBody, thief, theft, uid)
	if not done then
		Log.Warn("TheftService", ("сдача %s сорвалась: %s"):format(uid, tostring(err)))
		if ledger:ByThief(thief.UserId) == theft then
			abortDelivery(
				thief,
				nil,
				"Не удалось сдать добычу — она вернулась владельцу"
			)
		end
	end
end

transferBody = function(thief: any, theft: TheftLedger.Theft, uid: string)
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
		table.insert(list, { id = id, uid = uid, from = theft.owner, record = record, at = os.time() })
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
		DataService.UndoTransfer(victim, thief, uid, original, id)
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
	local now = os.clock()
	for _, theft in ledger:All() do
		local thief, _ = ownerOf(theft.thief)
		if thief and theft.stage == "Carrying" then
			noteSpeed(thief)
		end
		local _, ownerPlot = ownerOf(theft.owner)
		local showcase = ownerPlot and ownerPlot.showcases[theft.slot]
		local overdue = now - theft.startedAt > cfg.HoldSeconds + cfg.HoldTolerance + cfg.LiftGrace
		local away = thief ~= nil
			and showcase ~= nil
			and not Validate.IsNear(thief, showcase.Position, cfg.Distance + 2)
		if theft.stage == "Lifting" and (overdue or away) then
			local failed = ledger:Fail(theft.thief, now)
			if failed then
				returnToOwner(failed, if thief then "Кража сорвалась" else nil)
			end
		elseif theft.stage == "Lifting" and current ~= "Open" then
			local failed = ledger:Fail(theft.thief, now)
			if failed then
				returnToOwner(
					failed,
					if thief
						then "Судная ночь закончилась — кража сорвалась"
						else nil
				)
			end
		elseif theft.stage == "Carrying" and thief and impossible(thief, theft.uid) then
			local failed = ledger:Fail(theft.thief, now)
			if failed then
				returnToOwner(failed, IMPOSSIBLE)
			end
		elseif theft.stage == "Carrying" and current == nil then
			local failed = ledger:Fail(theft.thief, now)
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
	ledger.retryAt[player.UserId] = nil -- пауза ушедшего не нужна (таблица не копится)
	carries[player.UserId] = nil
	for _, uid in ItemRegistry.GetBeingStolenFrom(player.UserId) do
		local theft = ledger:ByUid(uid)
		if theft and theft.stage ~= "Delivering" then
			ledger:Fail(theft.thief)
			local entry = ItemRegistry.Get(uid)
			local carrier = entry and (entry.carrier or entry.thief)
			local part = entry and entry.part
			-- каждый экспонат отдельно (D52): ошибка посреди не оставит его «Stolen» в реестре и в руках вора без кражи
			local ok, err = pcall(function()
				if entry and entry.state == "Stolen" and carrier then
					part = CarryService.ReleaseStolen(carrier, uid) or part
				end
				ItemRegistry.Unload(uid)
			end)
			if not ok then
				Log.Warn(
					"TheftService",
					("уход владельца, %s: %s — запасная очистка"):format(
						uid,
						tostring(err)
					)
				)
				if entry and entry.state == "Stolen" and carrier then
					pcall(CarryService.ReleaseStolen, carrier, uid)
				end
				pcall(ItemRegistry.Unload, uid)
			end
			if part then
				pcall(part.Destroy, part)
			end
			if carrier then
				Notify.Send(carrier, "Хозяин музея ушёл — добыча исчезла", "Stop")
			end
		end
	end
end

-- Одна перепроверка ждущих передач ids вора (D53): решения журнала — к профилю (DataService.ResolveWaiting), выданное
-- и оставленное — в реестр (в инвентарь), подтверждение сохранением и удаление записей журнала — ConfirmResolved.
-- Возвращает id, которые всё ещё ждут.
local function resolveWaitingOnce(player: any, ids: { string }): { string }
	local applied, left, confirmList = DataService.ResolveWaiting(player, ids)
	if applied == nil then
		return left
	end
	local data = DataService.GetData(player)
	if #applied > 0 and data then
		for _, action in applied do
			local record = data.items[action.uid]
			if
				(action.kind == "grant" or action.kind == "keep")
				and type(record) == "table"
				and record.pending == nil
			then
				local present = ItemRegistry.Get(action.uid)
				if present then
					Log.Warn(
						"TheftService",
						("%s: %s уже на сервере (%s) — в инвентарь не поставлен"):format(
							tostring(player.Name),
							action.uid,
							present.state
						)
					)
				elseif not ItemRegistry.Restore(action.uid, record.id, player.UserId, "storage", nil, nil) then
					Log.Warn(
						"TheftService",
						("%s: %s не поставлен в инвентарь (реестр отказал)"):format(
							tostring(player.Name),
							action.uid
						)
					)
				end
			end
			Log.Warn(
				"TheftService",
				("%s: передача %s решена во время сессии — %s"):format(
					tostring(player.Name),
					action.uid,
					action.kind
				)
			)
		end
		InventoryService.Sync(player)
	end
	if #confirmList > 0 then
		task.spawn(DataService.ConfirmResolved, player, confirmList)
	end
	return left
end

-- После входа (PlayerSession.Join): передачи, которые при загрузке ждали жертву, перепроверять раз в
-- ResolveRetrySeconds, не дольше ResolveWindow (D53). Дальше — при следующем входе: без подтверждения собственности
-- предмет не выдаётся и не убирается, запись журнала остаётся.
function TheftService.WatchTransfers(player: any)
	local ids = DataService.TakeWaitingTransfers(player)
	if not ids or #ids == 0 then
		return
	end
	task.spawn(function()
		local started = os.clock()
		while #ids > 0 and os.clock() - started < cfg.ResolveWindow do
			task.wait(cfg.ResolveRetrySeconds)
			if not DataService.GetData(player) then
				return -- вышел: решится при следующем входе
			end
			local ok, result = pcall(resolveWaitingOnce, player, ids)
			if ok then
				ids = result
			else
				Log.Warn("TheftService", "перепроверка передач: " .. tostring(result))
			end
		end
		if #ids > 0 then
			Log.Warn(
				"TheftService",
				("%s: передач ждут жертву %d — решатся при следующем входе"):format(
					tostring(player.Name),
					#ids
				)
			)
		end
	end)
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
			Prompts.BindHold(
				prompt,
				function(player)
					tryBegin(player, plot, slot)
				end,
				tryCancel,
				function(player)
					tryComplete(player, plot, slot)
				end
			)
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
	Confirm = confirm,
	ResolveWaitingOnce = resolveWaitingOnce,
	Carries = carries,
}

return TheftService

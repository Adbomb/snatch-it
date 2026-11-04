-- Единый инвентарь игрока (D46, бывшее хранилище): все его коллекционные предметы — записи профиля items[uid],
-- Stored (в инвентаре) или Displayed (на постаменте). Количество не ограничено. Входы:
--   сундук у входа — «В инвентарь»: несомый предмет становится собственностью (Carried → Stored), в любую фазу;
--   постамент — «В инвентарь» (Displayed → Stored) и «Выставить из инвентаря» (открывает окно на клиенте);
--   окно «Инвентарь» (RemoteEvent InventoryAction) откуда угодно: Display (uid, постамент), Remove (uid),
--   Replace (uid, постамент) — замена атомарна.
-- Выставлять, снимать и заменять нельзя в подготовку, Судную ночь и 10 с доставки (MuseumService.ExhibitsUnlocked).
-- Порядок как в правке 1.1: все проверки → в одном блоке без yield запись профиля и переход в ItemRegistry; реестр
-- отказал — запись профиля откатывается. Владельцу шлётся весь инвентарь (InventoryChanged).
-- Зависит от ItemRegistry, CarryService, DataService, MuseumService, PlotService, Util/*, Remotes, Config.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local CarryService = require(ServerScriptService.Server.Services.CarryService)
local DataService = require(ServerScriptService.Server.Services.DataService)
local ItemRegistry = require(ServerScriptService.Server.Services.ItemRegistry)
local MuseumService = require(ServerScriptService.Server.Services.MuseumService)
local PlotService = require(ServerScriptService.Server.Services.PlotService)
local ItemFactory = require(ServerScriptService.Server.Util.ItemFactory)
local Log = require(ServerScriptService.Server.Util.Log)
local Notify = require(ServerScriptService.Server.Util.Notify)
local Prompts = require(ServerScriptService.Server.Util.Prompts)
local RateLimiter = require(ServerScriptService.Server.Util.RateLimiter)
local Validate = require(ServerScriptService.Server.Util.Validate)

local MAX_UID_LENGTH = 64

local limiter = RateLimiter.new(GameConfig.RateLimits.Storage)

local InventoryService = {}

local function nameOf(itemId: string): string
	local def = Items[itemId]
	return if def then def.displayName else itemId
end

-- Общие проверки: свой участок, профиль загружен. Возвращает данные профиля или nil.
local function ownPlotData(player: Player, plot: PlotService.Plot): any
	if plot.owner ~= player then
		Notify.Send(player, "Это чужой музей", "Stop")
		return nil
	end
	local data = DataService.GetData(player)
	if not data then
		Notify.Send(player, "Сохранение ещё загружается, подождите")
	end
	return data
end

-- Отправляет владельцу весь инвентарь: { uid, itemId, slot? } (slot — постамент, если выставлен) и атрибуты для
-- подсказок и интерфейса: StorageCount (в инвентаре), MuseumSlots (постаментов в музее).
function InventoryService.Sync(player: Player)
	local list, stored = {}, 0
	for _, uid in ItemRegistry.GetOwnedBy(player.UserId) do
		local entry = ItemRegistry.Get(uid)
		if entry and (entry.state == "Stored" or entry.state == "Displayed") then
			table.insert(list, { uid = uid, itemId = entry.itemId, slot = entry.slot })
			if entry.state == "Stored" then
				stored += 1
			end
		end
	end
	table.sort(list, function(a, b)
		if a.itemId ~= b.itemId then
			return a.itemId < b.itemId
		end
		return a.uid < b.uid
	end)
	player:SetAttribute("StorageCount", stored)
	player:SetAttribute("MuseumSlots", MuseumService.SlotCount(player))
	Remotes.FireClient(Remotes.Names.InventoryChanged, player, list)
end

-- Сундук: несомый предмет в инвентарь (Carried → Stored). В любую фазу и при свободных постаментах (D46).
local function tryStoreCarried(player: Player, plot: PlotService.Plot)
	if not limiter:Allow(player) then
		return
	end
	if not ownPlotData(player, plot) then
		return
	end
	if not Validate.IsNear(player, plot.chest.Position, GameConfig.Museum.ChestDistance) then
		return
	end
	local uid = ItemRegistry.GetCarriedBy(player)
	if not uid then
		Notify.Send(player, "Сначала принесите предмет", "Stop")
		return
	end
	if DataService.HasItem(player, uid) then
		Log.Warn(
			"InventoryService",
			("%s: uid %s уже в профиле — отклонено"):format(player.Name, uid)
		)
		return
	end
	local entry = ItemRegistry.Get(uid)
	if not entry or entry.state ~= "Carried" then
		return
	end

	local recorded = DataService.AddItem(player, uid, {
		id = entry.itemId,
		mods = {},
		place = "storage",
		rot = 0,
		acquiredAt = os.time(),
		source = if entry.boss then "boss" else "map",
		boss = entry.boss, -- уровень босса-источника: локация происхождения (D37, D46)
	})
	if not recorded then
		Notify.Send(
			player,
			"Не удалось сохранить предмет — он остаётся у вас в руках",
			"Stop"
		)
		return
	end
	if not ItemRegistry.Transition(uid, "Stored", { owner = player.UserId }) then
		DataService.RemoveItem(player, uid)
		Notify.Send(
			player,
			"Не удалось убрать предмет — он остаётся у вас в руках",
			"Stop"
		)
		return
	end
	local part = CarryService.ReleaseToMuseum(player, uid)
	if part then
		part:Destroy()
	end
	DataService.IncrementStat(player, "delivered")
	DataService.RequestSave(player)
	InventoryService.Sync(player)
	Notify.Send(player, ("В инвентаре: %s"):format(nameOf(entry.itemId)), "Go")
end

-- Экспонат с постамента в инвентарь (Displayed → Stored): общая часть подсказки и окна.
local function removeFromSlot(player: Player, plot: PlotService.Plot, slot: number): boolean
	local data = DataService.GetData(player)
	local uid = ItemRegistry.GetSlotItem(player.UserId, slot)
	local entry = uid and ItemRegistry.Get(uid)
	if not data or not uid or not entry or entry.state ~= "Displayed" then
		Notify.Send(player, "Постамент пуст", "Stop")
		return false
	end
	local record = data.items[uid]
	if not record or record.place ~= "slot" or record.slot ~= slot then
		Log.Warn(
			"InventoryService",
			("%s: экспонат %s на постаменте %d не совпадает с профилем"):format(
				player.Name,
				uid,
				slot
			)
		)
		return false
	end
	if not DataService.SetItemPlace(player, uid, "storage") then
		Notify.Send(player, "Не удалось снять экспонат", "Stop")
		return false
	end
	if not ItemRegistry.Transition(uid, "Stored", { owner = player.UserId }) then
		DataService.SetItemPlace(player, uid, "slot", slot)
		Notify.Send(player, "Не удалось снять экспонат", "Stop")
		return false
	end
	MuseumService.ClearShowcase(plot, slot, entry.part)
	if player:GetAttribute("MoveSlot") == slot then
		MuseumService.CancelMove(player)
	end
	DataService.RequestSave(player)
	InventoryService.Sync(player)
	Notify.Send(player, ("В инвентаре: %s"):format(nameOf(entry.itemId)), "Go")
	return true
end

-- Подсказка «В инвентарь» на постаменте (игрок рядом).
local function tryStoreDisplayed(player: Player, plot: PlotService.Plot, slot: number)
	if not limiter:Allow(player) then
		return
	end
	if not ownPlotData(player, plot) or not MuseumService.IsValidSlot(player, slot) then
		return
	end
	if not MuseumService.ExhibitsUnlocked(player) then
		return
	end
	if not Validate.IsNear(player, plot.showcases[slot].Position, GameConfig.Museum.DisplayDistance) then
		return
	end
	removeFromSlot(player, plot, slot)
end

-- Предмет из инвентаря игрока (Stored, его и в профиле, и в реестре) или nil с сообщением.
local function storedItem(player: Player, data: any, uid: any): any
	if type(uid) ~= "string" or #uid > MAX_UID_LENGTH then
		return nil
	end
	local entry = ItemRegistry.Get(uid)
	local record = data.items[uid]
	if
		not entry
		or entry.state ~= "Stored"
		or entry.owner ~= player.UserId
		or not record
		or record.place ~= "storage"
	then
		Log.Warn(
			"InventoryService",
			("%s: uid %s не в его инвентаре — отклонено"):format(player.Name, tostring(uid))
		)
		Notify.Send(player, "Этого предмета нет в вашем инвентаре", "Stop")
		return nil
	end
	return entry
end

-- Окно «Инвентарь»: выставить (Stored → Displayed) на свободный постамент slot.
local function display(player: Player, plot: PlotService.Plot, data: any, uid: any, slot: number)
	if not storedItem(player, data, uid) then
		return
	end
	if ItemRegistry.GetSlotItem(player.UserId, slot) or not DataService.IsSlotFree(player, slot) then
		Notify.Send(player, "Этот постамент уже занят", "Stop")
		return
	end
	local entry = ItemRegistry.Get(uid) :: ItemRegistry.Entry
	local part = ItemFactory.Create(entry.itemId) -- может ждать загрузки меша: после неё всё проверяется заново
	if not storedItem(player, data, uid) or ItemRegistry.GetSlotItem(player.UserId, slot) then
		part:Destroy()
		return
	end
	if not DataService.SetItemPlace(player, uid, "slot", slot) then
		part:Destroy()
		Notify.Send(
			player,
			"Не удалось выставить предмет — он остаётся в инвентаре",
			"Stop"
		)
		return
	end
	if not ItemRegistry.Transition(uid, "Displayed", { owner = player.UserId, slot = slot, part = part }) then
		DataService.SetItemPlace(player, uid, "storage")
		part:Destroy()
		Notify.Send(
			player,
			"Не удалось выставить предмет — он остаётся в инвентаре",
			"Stop"
		)
		return
	end
	MuseumService.PlaceExhibit(part, plot, slot, data.items[uid].rot or 0)
	DataService.RequestSave(player)
	InventoryService.Sync(player)
	Notify.Send(player, ("Выставлено: %s (постамент %d)"):format(nameOf(entry.itemId), slot), "Go")
	MuseumService.Present(player, plot, slot, entry.itemId)
end

-- Окно «Инвентарь»: заменить экспонат на постаменте slot предметом uid из инвентаря (атомарно).
local function replace(player: Player, plot: PlotService.Plot, data: any, uid: any, slot: number)
	if not storedItem(player, data, uid) then
		return
	end
	local oldUid = ItemRegistry.GetSlotItem(player.UserId, slot)
	if not oldUid then
		display(player, plot, data, uid, slot) -- постамент освободился — просто выставить
		return
	end
	local entry = ItemRegistry.Get(uid) :: ItemRegistry.Entry
	local part = ItemFactory.Create(entry.itemId)
	local old = ItemRegistry.Get(oldUid)
	local oldRecord = data.items[oldUid]
	if
		not storedItem(player, data, uid)
		or ItemRegistry.GetSlotItem(player.UserId, slot) ~= oldUid
		or not old
		or not oldRecord
		or oldRecord.place ~= "slot"
		or oldRecord.slot ~= slot
	then
		part:Destroy()
		Notify.Send(player, "Не удалось заменить экспонат", "Stop")
		return
	end
	if not DataService.ReplaceInSlot(player, oldUid, uid) then
		part:Destroy()
		Notify.Send(player, "Не удалось заменить экспонат", "Stop")
		return
	end
	local ok, _, oldPart = ItemRegistry.ReplaceSlot(player.UserId, slot, uid, part)
	if not ok then
		DataService.ReplaceInSlot(player, uid, oldUid)
		part:Destroy()
		Notify.Send(player, "Не удалось заменить экспонат", "Stop")
		return
	end
	if oldPart then
		oldPart:Destroy()
	end
	MuseumService.PlaceExhibit(part, plot, slot, data.items[uid].rot or 0)
	if player:GetAttribute("MoveSlot") == slot then
		MuseumService.CancelMove(player)
	end
	DataService.RequestSave(player)
	InventoryService.Sync(player)
	Notify.Send(
		player,
		("Постамент %d: %s вместо %s"):format(slot, nameOf(entry.itemId), nameOf(old.itemId)),
		"Go"
	)
	MuseumService.Present(player, plot, slot, entry.itemId)
end

-- RemoteEvent InventoryAction: (действие, uid, постамент). Всё проверяет сервер; лишние вызовы режет limiter.
local function tryAction(player: Player, action: any, uid: any, slot: any)
	if not limiter:Allow(player) then
		return
	end
	if action ~= "Display" and action ~= "Remove" and action ~= "Replace" then
		Log.Warn(
			"InventoryService",
			("%s: неизвестное действие %s — отклонено"):format(
				player.Name,
				tostring(action)
			)
		)
		return
	end
	local plot = PlotService.GetPlotOf(player)
	local data = plot and ownPlotData(player, plot)
	if not plot or not data then
		return
	end
	if not MuseumService.ExhibitsUnlocked(player) then
		return
	end
	if action == "Remove" then
		if type(uid) ~= "string" or #uid > MAX_UID_LENGTH then
			return
		end
		local entry = ItemRegistry.Get(uid)
		if not entry or entry.state ~= "Displayed" or entry.owner ~= player.UserId or not entry.slot then
			Notify.Send(player, "Этот предмет не выставлен в вашем музее", "Stop")
			return
		end
		removeFromSlot(player, plot, entry.slot)
		return
	end
	if not MuseumService.IsValidSlot(player, slot) then
		Log.Warn(
			"InventoryService",
			("%s: неверный постамент %s — отклонено"):format(player.Name, tostring(slot))
		)
		return
	end
	if action == "Display" then
		display(player, plot, data, uid, slot)
	else
		replace(player, plot, data, uid, slot)
	end
end

function InventoryService.Init()
	for _, plot in PlotService.GetPlots() do
		Prompts.Create(plot.chest, "ChestStore", "Сундук", GameConfig.Museum.ChestDistance).Triggered
			:Connect(function(player)
				tryStoreCarried(player, plot)
			end)
		for slot, showcase in plot.showcases do
			local objectText = "Постамент " .. slot
			local distance = GameConfig.Museum.DisplayDistance
			Prompts.Create(showcase, "Store", objectText, distance).Triggered:Connect(function(player)
				tryStoreDisplayed(player, plot, slot)
			end)
			-- «Выставить из инвентаря» открывает окно на клиенте; на сервер приходит InventoryAction.
			Prompts.Create(showcase, "FromStorage", objectText, distance)
		end
	end
	Remotes.Get(Remotes.Names.InventoryAction).OnServerEvent:Connect(tryAction)
end

-- Обработчики для серверных тестов (Server/Tests): те же функции, что вызывают подсказки и RemoteEvent.
InventoryService.Handlers = {
	StoreCarried = tryStoreCarried,
	StoreDisplayed = tryStoreDisplayed,
	Action = tryAction,
	DisplayFromStorage = function(player: Player, uid: any, slot: any)
		tryAction(player, "Display", uid, slot)
	end,
}

return InventoryService

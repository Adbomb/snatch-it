-- Хранилище музея: сундук у входа, «В хранилище» с рук и с витрины, «Выставить из хранилища».
-- Порядок как в правке 1.1: все проверки → в одном блоке без yield запись профиля и переход в ItemRegistry;
-- реестр отказал — запись профиля откатывается. Владельцу шлётся список хранилища (StorageChanged).
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

local storageLimiter = RateLimiter.new(GameConfig.RateLimits.Storage)

local StorageService = {}

local function capacity(): number
	return GameConfig.Museum.StorageCapacity
end

local function fullMessage(): string
	return ("Хранилище заполнено (%d/%d)"):format(capacity(), capacity())
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

-- Отправляет владельцу содержимое хранилища и число предметов (атрибут StorageCount для подсказок).
function StorageService.Sync(player: Player)
	local list = {}
	for _, uid in ItemRegistry.GetOwnedBy(player.UserId) do
		local entry = ItemRegistry.Get(uid)
		if entry and entry.state == "Stored" then
			table.insert(list, { uid = uid, itemId = entry.itemId })
		end
	end
	table.sort(list, function(a, b)
		if a.itemId ~= b.itemId then
			return a.itemId < b.itemId
		end
		return a.uid < b.uid
	end)
	player:SetAttribute("StorageCount", #list)
	Remotes.Get(Remotes.Names.StorageChanged):FireClient(player, list)
end

-- Сундук: предмет из рук в хранилище (Carried → Stored). Только когда все витрины заняты.
local function tryStoreCarried(player: Player, plot: PlotService.Plot)
	if not storageLimiter:Allow(player) then
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
	if MuseumService.HasFreeSlot(player) then
		Notify.Send(player, "Есть свободная витрина — выставьте предмет на неё", "Stop")
		return
	end
	if ItemRegistry.CountStored(player.UserId) >= capacity() then
		Notify.Send(player, fullMessage() .. " — предмет остаётся у вас в руках", "Stop")
		return
	end
	if DataService.HasItem(player, uid) then
		Log.Warn("StorageService", ("%s: uid %s уже в профиле — отклонено"):format(player.Name, uid))
		return
	end
	local entry = ItemRegistry.Get(uid)
	if not entry then
		return
	end

	local recorded = DataService.AddItem(player, uid, {
		id = entry.itemId,
		mods = {},
		place = "storage",
		rot = 0,
		acquiredAt = os.time(),
		source = "map",
	})
	if not recorded then
		Notify.Send(player, "Не удалось сохранить предмет — он остаётся у вас в руках", "Stop")
		return
	end
	if not ItemRegistry.Transition(uid, "Stored", { owner = player.UserId }) then
		DataService.RemoveItem(player, uid)
		Notify.Send(player, "Не удалось убрать предмет — он остаётся у вас в руках", "Stop")
		return
	end
	local part = CarryService.ReleaseToMuseum(player, uid)
	if part then
		part:Destroy()
	end
	DataService.IncrementStat(player, "delivered")
	DataService.RequestSave(player)
	StorageService.Sync(player)
	Notify.Send(
		player,
		("В хранилище: %s (%d/%d)"):format(
			Items[entry.itemId].displayName,
			ItemRegistry.CountStored(player.UserId),
			capacity()
		),
		"Go"
	)
end

-- Экспонат с витрины в хранилище (Displayed → Stored).
local function tryStoreDisplayed(player: Player, plot: PlotService.Plot, slot: number)
	if not storageLimiter:Allow(player) then
		return
	end
	local data = ownPlotData(player, plot)
	if not data or not MuseumService.IsValidSlot(player, slot) then
		return
	end
	if not Validate.IsNear(player, plot.showcases[slot].Position, GameConfig.Museum.DisplayDistance) then
		return
	end
	local uid = ItemRegistry.GetSlotItem(player.UserId, slot)
	local entry = uid and ItemRegistry.Get(uid)
	if not uid or not entry then
		Notify.Send(player, "Витрина пуста", "Stop")
		return
	end
	local record = data.items[uid]
	if not record or record.place ~= "slot" or record.slot ~= slot then
		Log.Warn(
			"StorageService",
			("%s: экспонат %s на витрине %d не совпадает с профилем"):format(player.Name, uid, slot)
		)
		return
	end
	if ItemRegistry.CountStored(player.UserId) >= capacity() then
		Notify.Send(player, fullMessage() .. " — экспонат остаётся на витрине", "Stop")
		return
	end

	if not DataService.SetItemPlace(player, uid, "storage") then
		Notify.Send(player, "Не удалось убрать экспонат", "Stop")
		return
	end
	if not ItemRegistry.Transition(uid, "Stored", { owner = player.UserId }) then
		DataService.SetItemPlace(player, uid, "slot", slot)
		Notify.Send(player, "Не удалось убрать экспонат", "Stop")
		return
	end
	MuseumService.ClearShowcase(plot, slot, entry.part)
	if player:GetAttribute("MoveSlot") == slot then
		MuseumService.CancelMove(player)
	end
	DataService.RequestSave(player)
	StorageService.Sync(player)
	Notify.Send(
		player,
		("В хранилище: %s (%d/%d)"):format(
			Items[entry.itemId].displayName,
			ItemRegistry.CountStored(player.UserId),
			capacity()
		),
		"Go"
	)
end

-- Клиент выбрал предмет в окне хранилища: (uid, номер витрины). Stored → Displayed.
local function tryDisplayFromStorage(player: Player, uid: any, slot: any)
	if not storageLimiter:Allow(player) then
		return
	end
	if type(uid) ~= "string" or #uid > MAX_UID_LENGTH or not MuseumService.IsValidSlot(player, slot) then
		Log.Warn("StorageService", ("%s: неверные аргументы DisplayFromStorage — отклонено"):format(player.Name))
		return
	end
	local plot = PlotService.GetPlotOf(player)
	local data = plot and ownPlotData(player, plot)
	if not plot or not data then
		return
	end
	if not Validate.IsNear(player, plot.showcases[slot].Position, GameConfig.Museum.DisplayDistance) then
		Notify.Send(player, "Подойдите ближе к витрине", "Stop")
		return
	end
	if ItemRegistry.GetCarriedBy(player) then
		Notify.Send(player, "Руки заняты — сначала бросьте предмет (G)", "Stop")
		return
	end
	local entry = ItemRegistry.Get(uid)
	if not entry or entry.state ~= "Stored" or entry.owner ~= player.UserId then
		Log.Warn(
			"StorageService",
			("%s: uid %s не в его хранилище — отклонено"):format(player.Name, uid)
		)
		Notify.Send(player, "Этого предмета нет в вашем хранилище", "Stop")
		return
	end
	local record = data.items[uid]
	if not record or record.place ~= "storage" then
		Log.Warn(
			"StorageService",
			("%s: uid %s в хранилище реестра, но не в профиле — отклонено"):format(player.Name, uid)
		)
		return
	end
	if ItemRegistry.GetSlotItem(player.UserId, slot) or not DataService.IsSlotFree(player, slot) then
		Notify.Send(player, "Эта витрина уже занята", "Stop")
		return
	end

	local part = ItemFactory.Create(entry.itemId)
	if not DataService.SetItemPlace(player, uid, "slot", slot) then
		part:Destroy()
		Notify.Send(player, "Не удалось выставить предмет — он остаётся в хранилище", "Stop")
		return
	end
	if not ItemRegistry.Transition(uid, "Displayed", { owner = player.UserId, slot = slot, part = part }) then
		DataService.SetItemPlace(player, uid, "storage")
		part:Destroy()
		Notify.Send(player, "Не удалось выставить предмет — он остаётся в хранилище", "Stop")
		return
	end
	MuseumService.PlaceExhibit(part, plot, slot, record.rot or 0)
	DataService.RequestSave(player)
	StorageService.Sync(player)
	Notify.Send(player, ("Выставлено: %s (витрина %d)"):format(Items[entry.itemId].displayName, slot), "Go")
	MuseumService.Present(player, plot, slot, entry.itemId)
end

function StorageService.Init()
	for _, plot in PlotService.GetPlots() do
		Prompts.Create(plot.chest, "ChestStore", "Сундук", GameConfig.Museum.ChestDistance).Triggered:Connect(
			function(player)
				tryStoreCarried(player, plot)
			end
		)
		for slot, showcase in plot.showcases do
			local objectText = "Витрина " .. slot
			local distance = GameConfig.Museum.DisplayDistance
			Prompts.Create(showcase, "Store", objectText, distance).Triggered:Connect(function(player)
				tryStoreDisplayed(player, plot, slot)
			end)
			-- «Выставить из хранилища» открывает окно на клиенте; на сервер приходит DisplayFromStorage.
			Prompts.Create(showcase, "FromStorage", objectText, distance)
		end
	end
	Remotes.Get(Remotes.Names.DisplayFromStorage).OnServerEvent:Connect(tryDisplayFromStorage)
end

return StorageService

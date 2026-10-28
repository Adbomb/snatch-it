-- Музей игрока: подсказка «Выставить» на витринах, запись экспоната в профиль, восстановление при входе.
-- Свои экспонаты с витрины в руки не берутся (D2). Подсказки в чужом музее прячет клиент,
-- но каждый обработчик на сервере сам проверяет владельца, состояние и расстояние.
-- Зависит от ItemRegistry, CarryService, DataService, PlotService, Util/*, Config.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local CarryService = require(ServerScriptService.Server.Services.CarryService)
local DataService = require(ServerScriptService.Server.Services.DataService)
local ItemRegistry = require(ServerScriptService.Server.Services.ItemRegistry)
local PlotService = require(ServerScriptService.Server.Services.PlotService)
local ItemFactory = require(ServerScriptService.Server.Util.ItemFactory)
local Log = require(ServerScriptService.Server.Util.Log)
local Notify = require(ServerScriptService.Server.Util.Notify)
local Prompts = require(ServerScriptService.Server.Util.Prompts)
local RateLimiter = require(ServerScriptService.Server.Util.RateLimiter)
local Validate = require(ServerScriptService.Server.Util.Validate)

local displayLimiter = RateLimiter.new(GameConfig.RateLimits.Display)
local moveLimiter = RateLimiter.new(GameConfig.RateLimits.Move)
local rotateLimiter = RateLimiter.new(GameConfig.RateLimits.Rotate)

-- Выбор «Переставить»: витрина-источник и номер выбора (для таймера отмены).
local selections: { [Player]: { slot: number, token: number } } = {}
local selectionCounter = 0

local MuseumService = {}

local function slotCount(museumLevel: number): number
	return GameConfig.Museum.SlotsByLevel[museumLevel] or GameConfig.Museum.SlotsByLevel[1]
end

-- Сколько витрин у игрока сейчас (0 — профиль не загружен).
function MuseumService.SlotCount(player: Player): number
	local data = DataService.GetData(player)
	return if data then slotCount(data.museumLevel) else 0
end

-- Номер витрины пришёл от клиента: целое число в пределах музея игрока.
function MuseumService.IsValidSlot(player: Player, slot: any): boolean
	return type(slot) == "number" and slot == math.floor(slot) and slot >= 1 and slot <= MuseumService.SlotCount(player)
end

-- Есть ли у игрока витрина, свободная и в реестре, и в профиле.
function MuseumService.HasFreeSlot(player: Player): boolean
	for slot = 1, MuseumService.SlotCount(player) do
		if not ItemRegistry.GetSlotItem(player.UserId, slot) and DataService.IsSlotFree(player, slot) then
			return true
		end
	end
	return false
end

-- Ставит Part экспоната на витрину с поворотом rot (градусы) и помечает витрину занятой.
function MuseumService.PlaceExhibit(part: BasePart, plot: PlotService.Plot, slot: number, rot: number)
	local showcase = plot.showcases[slot]
	part.Anchored = true
	part.CFrame = showcase.CFrame
		* CFrame.new(0, showcase.Size.Y / 2 + part.Size.Y / 2, 0)
		* CFrame.Angles(0, math.rad(rot), 0)
	part:SetAttribute("Slot", slot)
	part.Parent = plot.exhibits
	showcase:SetAttribute("Occupied", true)
end

-- Убирает Part экспоната с витрины (экспонат ушёл в хранилище).
function MuseumService.ClearShowcase(plot: PlotService.Plot, slot: number, part: BasePart?)
	if part then
		part:Destroy()
	end
	plot.showcases[slot]:SetAttribute("Occupied", false)
end

local function tryDisplay(player: Player, plot: PlotService.Plot, slot: number)
	if not displayLimiter:Allow(player) then
		return
	end
	if plot.owner ~= player then
		Notify.Send(player, "Это чужой музей", "Stop")
		return
	end
	local data = DataService.GetData(player)
	if not data then
		Notify.Send(player, "Сохранение ещё загружается, подождите")
		return
	end
	if slot > slotCount(data.museumLevel) then
		return
	end
	local showcase = plot.showcases[slot]
	if not Validate.IsNear(player, showcase.Position, GameConfig.Museum.DisplayDistance) then
		return
	end
	local uid = ItemRegistry.GetCarriedBy(player)
	if not uid then
		Notify.Send(player, "Сначала принесите предмет", "Stop")
		return
	end
	if ItemRegistry.GetSlotItem(player.UserId, slot) or not DataService.IsSlotFree(player, slot) then
		Notify.Send(player, "Эта витрина уже занята", "Stop")
		return
	end
	if DataService.HasItem(player, uid) then
		Log.Warn("MuseumService", ("%s: uid %s уже в профиле — отказ"):format(player.Name, uid))
		return
	end
	local entry = ItemRegistry.Get(uid)
	if not entry or not entry.part or not entry.part.Parent then
		return
	end

	-- Сначала запись в профиль, потом переход. Между ними нет yield, поэтому откат записи
	-- не успевает попасть в DataStore, а обратного перехода Displayed → Carried в графе нет.
	local recorded = DataService.AddItem(player, uid, {
		id = entry.itemId,
		mods = {},
		place = "slot",
		slot = slot,
		rot = 0,
		acquiredAt = os.time(),
		source = "map",
	})
	if not recorded then
		Notify.Send(
			player,
			"Не удалось сохранить экспонат — предмет остаётся у вас в руках",
			"Stop"
		)
		return
	end
	if not ItemRegistry.Transition(uid, "Displayed", { owner = player.UserId, slot = slot }) then
		DataService.RemoveItem(player, uid)
		Notify.Send(
			player,
			"Не удалось выставить предмет — он остаётся у вас в руках",
			"Stop"
		)
		return
	end
	local part = CarryService.ReleaseToMuseum(player, uid) :: BasePart
	MuseumService.PlaceExhibit(part, plot, slot, 0)
	DataService.IncrementStat(player, "delivered")
	DataService.RequestSave(player)
	Notify.Send(player, ("Выставлено: %s (витрина %d)"):format(Items[entry.itemId].displayName, slot), "Go")
end

-- Сброс выбора «Переставить». Атрибут MoveSlot видит клиент (подсветка и «Сюда»), сервер на него не смотрит.
function MuseumService.CancelMove(player: Player)
	selections[player] = nil
	player:SetAttribute("MoveSlot", nil)
end

-- Общие проверки действий над своим экспонатом: свой участок, профиль, витрина, игрок рядом,
-- на витрине экспонат и он совпадает с профилем. Возвращает uid и запись профиля или nil.
local function ownExhibit(player: Player, plot: PlotService.Plot, slot: number): (string?, any)
	if plot.owner ~= player then
		Notify.Send(player, "Это чужой музей", "Stop")
		return nil, nil
	end
	local data = DataService.GetData(player)
	if not data or not MuseumService.IsValidSlot(player, slot) then
		return nil, nil
	end
	if not Validate.IsNear(player, plot.showcases[slot].Position, GameConfig.Museum.DisplayDistance) then
		return nil, nil
	end
	local uid = ItemRegistry.GetSlotItem(player.UserId, slot)
	local record = uid and data.items[uid]
	if not uid or not record or record.place ~= "slot" or record.slot ~= slot then
		return nil, nil
	end
	return uid, record
end

-- E на своём экспонате: выбрать его для перестановки; повторно на нём же — отменить.
local function tryMove(player: Player, plot: PlotService.Plot, slot: number)
	if not moveLimiter:Allow(player) then
		return
	end
	local uid = ownExhibit(player, plot, slot)
	if not uid then
		return
	end
	local current = selections[player]
	if current and current.slot == slot then
		MuseumService.CancelMove(player)
		Notify.Send(player, "Перестановка отменена")
		return
	end
	selectionCounter += 1
	local token = selectionCounter
	selections[player] = { slot = slot, token = token }
	player:SetAttribute("MoveSlot", slot)
	Notify.Send(player, "Выберите витрину — подсказка «Сюда»")
	task.delay(GameConfig.Museum.MoveSelectTimeout, function()
		local selection = selections[player]
		if selection and selection.token == token then
			MuseumService.CancelMove(player)
			Notify.Send(player, "Перестановка отменена: время вышло")
		end
	end)
end

-- «Сюда» на другой своей витрине: пустая — перенос (MoveSlot), занятая — обмен (SwapSlots).
local function tryPlaceHere(player: Player, plot: PlotService.Plot, slot: number)
	if not moveLimiter:Allow(player) then
		return
	end
	local selection = selections[player]
	if not selection or selection.slot == slot then
		return
	end
	if plot.owner ~= player then
		Notify.Send(player, "Это чужой музей", "Stop")
		return
	end
	if not MuseumService.IsValidSlot(player, slot) then
		return
	end
	if not Validate.IsNear(player, plot.showcases[slot].Position, GameConfig.Museum.DisplayDistance) then
		return
	end
	local fromSlot = selection.slot
	local data = DataService.GetData(player)
	local uidA = ItemRegistry.GetSlotItem(player.UserId, fromSlot)
	local recordA = uidA and data and data.items[uidA]
	local entryA = uidA and ItemRegistry.Get(uidA)
	if not uidA or not recordA or not entryA or recordA.place ~= "slot" or recordA.slot ~= fromSlot then
		MuseumService.CancelMove(player)
		Notify.Send(player, "Экспонат уже не на витрине — перестановка отменена", "Stop")
		return
	end
	local uidB = ItemRegistry.GetSlotItem(player.UserId, slot)

	if not uidB then
		if not DataService.IsSlotFree(player, slot) then
			Notify.Send(player, "Эта витрина уже занята", "Stop")
			return
		end
		if not DataService.SetItemPlace(player, uidA, "slot", slot) then
			Notify.Send(player, "Не удалось переставить экспонат", "Stop")
			return
		end
		if not ItemRegistry.MoveSlot(player.UserId, fromSlot, slot) then
			DataService.SetItemPlace(player, uidA, "slot", fromSlot)
			Notify.Send(player, "Не удалось переставить экспонат", "Stop")
			return
		end
		MuseumService.ClearShowcase(plot, fromSlot, nil)
		if entryA.part then
			MuseumService.PlaceExhibit(entryA.part, plot, slot, recordA.rot or 0)
		end
		Notify.Send(player, ("Переставлено на витрину %d"):format(slot), "Go")
	else
		local recordB = data.items[uidB]
		local entryB = ItemRegistry.Get(uidB)
		if not recordB or not entryB or recordB.place ~= "slot" or recordB.slot ~= slot then
			Notify.Send(player, "Не удалось поменять экспонаты местами", "Stop")
			return
		end
		if not DataService.SwapItemSlots(player, uidA, uidB) then
			Notify.Send(player, "Не удалось поменять экспонаты местами", "Stop")
			return
		end
		if not ItemRegistry.SwapSlots(player.UserId, fromSlot, slot) then
			DataService.SwapItemSlots(player, uidA, uidB)
			Notify.Send(player, "Не удалось поменять экспонаты местами", "Stop")
			return
		end
		if entryA.part then
			MuseumService.PlaceExhibit(entryA.part, plot, slot, recordA.rot or 0)
		end
		if entryB.part then
			MuseumService.PlaceExhibit(entryB.part, plot, fromSlot, recordB.rot or 0)
		end
		Notify.Send(player, ("Витрины %d и %d поменялись экспонатами"):format(fromSlot, slot), "Go")
	end
	MuseumService.CancelMove(player)
	DataService.RequestSave(player)
end

-- R на своём экспонате: +RotateStep градусов, сохраняется в профиле (rot).
local function tryRotate(player: Player, plot: PlotService.Plot, slot: number)
	if not rotateLimiter:Allow(player) then
		return
	end
	local uid, record = ownExhibit(player, plot, slot)
	local entry = uid and ItemRegistry.Get(uid)
	if not uid or not entry or not entry.part then
		return
	end
	local rot = ((record.rot or 0) + GameConfig.Museum.RotateStep) % 360
	if not DataService.SetItemRotation(player, uid, rot) then
		return
	end
	MuseumService.PlaceExhibit(entry.part, plot, slot, rot)
	DataService.RequestSave(player)
end

function MuseumService.Init()
	local distance = GameConfig.Museum.DisplayDistance
	for _, plot in PlotService.GetPlots() do
		for slot, showcase in plot.showcases do
			local objectText = "Витрина " .. slot
			Prompts.Create(showcase, "Display", objectText, distance).Triggered:Connect(function(player)
				tryDisplay(player, plot, slot)
			end)
			Prompts.Create(showcase, "Move", objectText, distance).Triggered:Connect(function(player)
				tryMove(player, plot, slot)
			end)
			Prompts.Create(showcase, "Here", objectText, distance).Triggered:Connect(function(player)
				tryPlaceHere(player, plot, slot)
			end)
			Prompts.Create(showcase, "Rotate", objectText, distance).Triggered:Connect(function(player)
				tryRotate(player, plot, slot)
			end)
		end
	end
end

-- После загрузки профиля: расставить сохранённые экспонаты по витринам.
function MuseumService.LoadMuseum(player: Player)
	local plot = PlotService.GetPlotOf(player)
	local data = DataService.GetData(player)
	if not plot or not data then
		return
	end
	local maxSlot = slotCount(data.museumLevel)
	for uid, record in data.items do
		if type(record) ~= "table" or not Items[record.id] then
			Log.Warn(
				"MuseumService",
				("%s: неизвестный предмет %s (uid %s) пропущен"):format(
					player.Name,
					tostring(record.id),
					uid
				)
			)
		elseif record.place == "slot" then
			local slot = record.slot
			if type(slot) ~= "number" or slot < 1 or slot > maxSlot then
				Log.Warn(
					"MuseumService",
					("%s: uid %s на несуществующей витрине %s"):format(
						player.Name,
						uid,
						tostring(slot)
					)
				)
			else
				local part = ItemFactory.Create(record.id)
				if ItemRegistry.Restore(uid, record.id, player.UserId, "slot", slot, part) then
					MuseumService.PlaceExhibit(part, plot, slot, record.rot or 0)
				else
					part:Destroy()
				end
			end
		else
			ItemRegistry.Restore(uid, record.id, player.UserId, record.place, nil, nil)
		end
	end
	Log.Debug(
		"MuseumService",
		("Музей %s восстановлен на участке %d"):format(player.Name, plot.index)
	)
end

-- Игрок вышел: убрать его экспонаты из мира и из реестра (в профиле они остаются).
function MuseumService.UnloadMuseum(player: Player)
	selections[player] = nil
	for _, uid in ItemRegistry.GetOwnedBy(player.UserId) do
		local entry = ItemRegistry.Get(uid)
		ItemRegistry.Unload(uid)
		if entry and entry.part then
			entry.part:Destroy()
		end
	end
	local plot = PlotService.GetPlotOf(player)
	if plot then
		for _, showcase in plot.showcases do
			showcase:SetAttribute("Occupied", false)
		end
	end
end

return MuseumService

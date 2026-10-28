-- Музей игрока: подсказка «Выставить» на витринах, запись экспоната в профиль, восстановление при входе.
-- Свои экспонаты с витрины в руки не берутся (D2). Подсказку в чужом музее прячет клиент, проверяет сервер.
-- Зависит от ItemRegistry, CarryService, DataService, PlotService, Util/*, Config.

local CollectionService = game:GetService("CollectionService")
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
local RateLimiter = require(ServerScriptService.Server.Util.RateLimiter)
local Validate = require(ServerScriptService.Server.Util.Validate)

local DISPLAY_PROMPT_TAG = "DisplayPrompt" -- по этому тегу клиент находит подсказки витрин

local displayLimiter = RateLimiter.new(GameConfig.RateLimits.Display)

local MuseumService = {}

local function slotCount(museumLevel: number): number
	return GameConfig.Museum.SlotsByLevel[museumLevel] or GameConfig.Museum.SlotsByLevel[1]
end

local function placeOnShowcase(part: BasePart, showcase: BasePart, rot: number, parent: Instance)
	part.Anchored = true
	part.CFrame = showcase.CFrame
		* CFrame.new(0, showcase.Size.Y / 2 + part.Size.Y / 2, 0)
		* CFrame.Angles(0, math.rad(rot), 0)
	part.Parent = parent
	showcase:SetAttribute("Occupied", true)
end

local function tryDisplay(player: Player, plot: PlotService.Plot, slot: number)
	if not displayLimiter:Allow(player) then
		return
	end
	if plot.owner ~= player then
		Notify.Send(player, "Это чужой музей")
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
		Notify.Send(player, "Сначала принесите предмет")
		return
	end
	if ItemRegistry.GetSlotItem(player.UserId, slot) or not DataService.IsSlotFree(player, slot) then
		Notify.Send(player, "Эта витрина уже занята")
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

	if not ItemRegistry.Transition(uid, "Displayed", { owner = player.UserId, slot = slot }) then
		return
	end
	local part = CarryService.ReleaseForDisplay(player, uid) :: BasePart
	placeOnShowcase(part, showcase, 0, plot.exhibits)
	DataService.AddItem(player, uid, {
		id = entry.itemId,
		mods = {},
		place = "slot",
		slot = slot,
		rot = 0,
		acquiredAt = os.time(),
		source = "map",
	})
	DataService.IncrementStat(player, "delivered")
	DataService.RequestSave(player)
	Notify.Send(player, ("Выставлено: %s (витрина %d)"):format(Items[entry.itemId].displayName, slot))
end

function MuseumService.Init()
	for _, plot in PlotService.GetPlots() do
		for slot, showcase in plot.showcases do
			local prompt = Instance.new("ProximityPrompt")
			prompt.ActionText = "Выставить"
			prompt.ObjectText = "Витрина " .. slot
			prompt.HoldDuration = 0
			prompt.MaxActivationDistance = GameConfig.Museum.DisplayDistance
			prompt.RequiresLineOfSight = false
			prompt.Parent = showcase
			CollectionService:AddTag(prompt, DISPLAY_PROMPT_TAG)
			prompt.Triggered:Connect(function(player)
				tryDisplay(player, plot, slot)
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
					placeOnShowcase(part, plot.showcases[slot], record.rot or 0, plot.exhibits)
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

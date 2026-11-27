--!strict
-- Музей-небоскрёб участка (этап B, docs/TOWER_PLAN.md v3): только режим башни DEV (Util/TowerMode) — в обычной
-- игре ни одна функция ничего не строит и не меняет. Данные — профиль (DataService: builtAt + tower.order),
-- состояние экземпляров — ItemRegistry (Floor), геометрия — World/TowerBuilder, вид — клиент.
--   LoadTower / UnloadTower — вход и выход владельца (PlayerSession) и переключение режима (Enable / Disable);
--   Build — постройка этажа из инвентаря: проверки → профиль → реестр в одном кадре (отказ реестра откатывает
--     профиль) → модель наверх (State Building ≈ 2 с) → доход, инвентарь, сохранение;
--   Remove — снять этаж (DEV): сначала игроки (на снимаемом — на площадку лифта этажа, который займёт место; выше —
--     вниз на высоту этажа вместе с полом), потом профиль и реестр, потом геометрия; лифт башни закрыт ShiftLock;
--   Move — перестановка этажа (DEV), игроки едут вместе со своим этажом;
--   DevGiveItem / DevFill — тестовые предметы и нагрузочная башня (DEV).
-- Повторный и одновременный запрос того же uid не создаёт второй этаж: запись уже с builtAt, реестр — Floor.
-- Зависит от DataService, ItemRegistry, PlotService, MuseumService, InventoryService, IncomeService, MoveGuard,
-- World/TowerBuilder, Shared/TowerRules, Util/TowerMode, Util/*.

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local TowerRules = require(ReplicatedStorage.Shared.TowerRules)
local Server = ServerScriptService.Server
local DataService = require(Server.Services.DataService)
local IncomeService = require(Server.Services.IncomeService)
local InventoryService = require(Server.Services.InventoryService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local MoveGuard = require(Server.Services.MoveGuard)
local MuseumService = require(Server.Services.MuseumService)
local PlotService = require(Server.Services.PlotService)
local TowerBuilder = require(Server.World.TowerBuilder)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local RateLimiter = require(Server.Util.RateLimiter)
local TowerMode = require(Server.Util.TowerMode)
local Validate = require(Server.Util.Validate)

local cfg = GameConfig.Tower
local MAX_UID_LENGTH = 64

export type Tower = {
	plot: any,
	owner: any,
	model: Model,
	models: { [string]: Model }, -- uid → модель этажа
	lockUntil: number, -- os.clock: до этого лифт башни закрыт (перестройка)
	spotUse: { [number]: { [number]: number } }, -- этаж → место → когда занято
	spotTurn: { [number]: number },
}

local towers: { [number]: Tower } = {} -- по номеру участка
local limiter = RateLimiter.new(GameConfig.RateLimits.TowerBuild)

local TowerService = {}

local function nameOf(itemId: string): string
	local def = Items[itemId]
	return if def then def.displayName else itemId
end

local function bump(t: Tower)
	t.model:SetAttribute("Version", (t.model:GetAttribute("Version") or 0) + 1)
end

local function towerOf(player: any): Tower?
	local plot = PlotService.GetPlotOf(player)
	return if plot then towers[plot.index] else nil
end

-- Башня участка plotIndex (лифт, тесты) или nil.
function TowerService.Get(plotIndex: number): Tower?
	return towers[plotIndex]
end

-- Башня игрока (своего участка) или nil.
function TowerService.Of(player: any): Tower?
	return towerOf(player)
end

-- Все, кого может задеть перестройка или лифт: игроки сервера и переданные тестовые игроки.
local function everyone(extra: { any }?): { any }
	local list: { any } = {}
	for _, p in Players:GetPlayers() do
		table.insert(list, p)
	end
	for _, p in extra or {} do
		if not table.find(list, p) then
			table.insert(list, p)
		end
	end
	return list
end

-- Свободное место высадки на этаже index: по кругу; пропускаются занятые лифтом в последние SpotReuse секунд и те,
-- где уже стоит чей-то персонаж (по серверным позициям). Все заняты — следующее по кругу.
function TowerService.NextSpot(t: Tower, index: number, extra: { any }?): CFrame
	local used = t.spotUse[index] or {}
	t.spotUse[index] = used
	local now = os.clock()
	local turn = t.spotTurn[index] or 0
	local n = #cfg.Spots
	local roots: { Vector3 } = {}
	for _, p in everyone(extra) do
		local root = Validate.GetLiveRoot(p)
		if root then
			table.insert(roots, root.Position)
		end
	end
	local function taken(i: number): boolean
		local at = TowerBuilder.Spot(t.model, index, i).Position
		for _, r in roots do
			if Vector3.new(r.X - at.X, 0, r.Z - at.Z).Magnitude < 1.5 and math.abs(r.Y - at.Y) < 4 then
				return true
			end
		end
		return false
	end
	local chosen = turn % n + 1
	for k = 1, n do
		local i = (turn + k - 1) % n + 1
		if (not used[i] or now - used[i] >= cfg.SpotReuse) and not taken(i) then
			chosen = i
			break
		end
	end
	used[chosen] = now
	t.spotTurn[index] = chosen
	return TowerBuilder.Spot(t.model, index, chosen)
end

-- Башню участка — в мир (вход владельца или включение режима). true — построена.
function TowerService.LoadTower(player: any): boolean
	if not TowerMode.For(player) then
		return false
	end
	local plot = PlotService.GetPlotOf(player)
	local data = DataService.GetData(player)
	if not plot or not data then
		return false
	end
	if towers[plot.index] then
		TowerService.UnloadTower(player)
	end
	PlotService.UseTower(plot, true)
	local model = TowerBuilder.NewTower(plot.index, plot.floorOrigin, plot.accent, player.UserId)
	local t: Tower = {
		plot = plot,
		owner = player,
		model = model,
		models = {},
		lockUntil = 0,
		spotUse = {},
		spotTurn = {},
	}
	towers[plot.index] = t
	-- реестр: всё — как в инвентаре (постаментов в башне нет), затем этажи по порядку → Floor
	for uid, record in data.items do
		if type(record) == "table" and Items[record.id] and record.pending == nil then
			ItemRegistry.Restore(uid, record.id, player.UserId, "storage", nil, nil, record.floor)
		end
	end
	local order = TowerRules.Order(data)
	for index, uid in order do
		local record = data.items[uid]
		if ItemRegistry.Transition(uid, "Floor", { owner = player.UserId }) then
			t.models[uid] = TowerBuilder.NewFloor(model, uid, record.id, index)
			InventoryService.EnsurePreview(record.id) -- модель экспоната у клиентов
		else
			Log.Warn(
				"TowerService",
				("%s: этаж %d (%s) не восстановлен"):format(player.Name, index, uid)
			)
		end
	end
	TowerBuilder.SetRoof(model, #order)
	bump(t)
	model.Parent = plot.model
	player:SetAttribute("TowerMode", true) -- интерфейс режима башни (окно инвентаря: этажи вместо постаментов)
	IncomeService.Handlers.Refresh(player)
	Log.Debug(
		"TowerService",
		("Башня %s: %d этажей на участке %d"):format(player.Name, #order, plot.index)
	)
	return true
end

-- Башню — из мира (выход владельца или выключение режима): экземпляры выгружаются из реестра (в профиле остаются),
-- участку возвращается прежний вид.
function TowerService.UnloadTower(player: any)
	for _, uid in ItemRegistry.GetOwnedBy(player.UserId) do
		ItemRegistry.Unload(uid)
	end
	local plot = PlotService.GetPlotOf(player)
	local t = plot and towers[plot.index]
	if t then
		t.model:Destroy()
		towers[plot.index] = nil
	end
	if plot then
		PlotService.UseTower(plot, false)
	end
	player:SetAttribute("TowerMode", nil)
end

-- Включить режим башни уже вошедшему игроку (DevTools, тесты): миграция профиля, музей → башня. true или причина.
function TowerService.Enable(player: any): (boolean, string?)
	local ok, reason = TowerMode.Enable(player)
	if not ok then
		return false, reason
	end
	if towerOf(player) then
		return true, nil
	end
	if not DataService.EnterTowerMode(player) then
		return true, nil -- профиль ещё грузится: башню построит вход (PlayerSession)
	end
	MuseumService.UnloadMuseum(player)
	TowerService.LoadTower(player)
	InventoryService.Sync(player)
	return true, nil
end

-- Выключить режим башни (DEV): башня → прежний музей. Построенные записи остаются с builtAt и недоступны постаментам.
function TowerService.Disable(player: any)
	if not TowerMode.For(player) then
		return
	end
	TowerService.UnloadTower(player)
	TowerMode.Disable(player)
	if DataService.GetData(player) then
		MuseumService.LoadMuseum(player)
		InventoryService.Sync(player)
	end
end

-- Постройка этажа из инвентаря. opts.quiet — без уведомления и анимации (нагрузочная башня). true или причина.
function TowerService.Build(player: any, uid: any, opts: { quiet: boolean? }?): (boolean, string?)
	if not TowerMode.For(player) then
		return false, "Башня выключена"
	end
	local quiet = opts and opts.quiet
	if not quiet and not limiter:Allow(player) then
		return false, nil
	end
	if type(uid) ~= "string" or #uid > MAX_UID_LENGTH then
		return false, "Нет такого предмета"
	end
	local t = towerOf(player)
	if not t or t.owner ~= player then
		return false, "Башня ещё не построена"
	end
	local entry = ItemRegistry.Get(uid)
	if not entry or entry.state ~= "Stored" or entry.owner ~= player.UserId then
		return false, "Этого предмета нет в вашем инвентаре"
	end
	-- один кадр без yield: профиль → реестр; отказ реестра откатывает профиль
	local ok, reason = DataService.BuildFloor(player, uid)
	if not ok then
		return false, reason
	end
	if not ItemRegistry.Transition(uid, "Floor", { owner = player.UserId }) then
		DataService.UnbuildFloor(player, uid)
		return false, "Этаж не построен — попробуйте ещё раз"
	end
	local index = TowerRules.IndexOf(DataService.GetData(player), uid) :: number
	local model = TowerBuilder.NewFloor(t.model, uid, entry.itemId, index)
	InventoryService.EnsurePreview(entry.itemId) -- модель экспоната у клиентов
	t.models[uid] = model
	TowerBuilder.SetRoof(t.model, index)
	if not quiet then
		model:SetAttribute("State", "Building")
		task.delay(cfg.BuildSeconds, function()
			if model.Parent then
				model:SetAttribute("State", "Built")
			end
		end)
	end
	bump(t)
	IncomeService.Handlers.Refresh(player)
	if not quiet then
		InventoryService.Sync(player)
		DataService.RequestSave(player)
		Notify.Send(player, ("Построен этаж %d: «%s»"):format(index, nameOf(entry.itemId)), "Go")
	end
	return true, nil
end

-- Все игроки в башне t сейчас: { player, index (0 — холл), root }.
local function occupants(t: Tower, count: number, extra: { any }?): { { player: any, index: number, root: BasePart } }
	local list = {}
	for _, p in everyone(extra) do
		local root = Validate.GetLiveRoot(p)
		local index = root and TowerBuilder.IndexAt(t.model, root.Position, count)
		if root and index then
			table.insert(list, { player = p, index = index, root = root })
		end
	end
	return list
end

-- Снять этаж uid (DEV; основа будущей кражи): этажи выше сдвигаются вниз без промежутков. extra — тестовые игроки.
-- Прежний номер или nil и причина.
function TowerService.Remove(player: any, uid: string, extra: { any }?): (number?, string?)
	if not TowerMode.For(player) then
		return nil, "Башня выключена"
	end
	local t = towerOf(player)
	local data = DataService.GetData(player)
	if not t or not data then
		return nil, "Башни нет"
	end
	local index = TowerRules.IndexOf(data, uid)
	if not index then
		return nil, "Такого этажа нет"
	end
	local count = #TowerRules.Order(data)
	local up = t.model.WorldPivot.UpVector
	-- 1) люди — раньше геометрии (тот же кадр: пол и персонаж приходят клиенту вместе)
	for _, o in occupants(t, count, extra) do
		if o.index == index then
			MoveGuard.Teleport(o.player, TowerService.NextSpot(t, math.min(index, count - 1), extra))
		elseif o.index > index then
			MoveGuard.Teleport(o.player, o.root.CFrame - up * cfg.FloorHeight)
		end
	end
	t.lockUntil = os.clock() + cfg.ShiftLock
	-- 2) профиль → реестр
	DataService.UnbuildFloor(player, uid)
	if not ItemRegistry.Transition(uid, "Stored", { owner = player.UserId }) then
		Log.Warn(
			"TowerService",
			("%s: этаж %s снят в профиле, реестр отказал"):format(player.Name, uid)
		)
	end
	-- 3) геометрия
	local model = t.models[uid]
	t.models[uid] = nil
	if model then
		model:Destroy()
	end
	local order = TowerRules.Order(data)
	for i = index, #order do
		local m = t.models[order[i]]
		if m then
			TowerBuilder.PlaceFloor(t.model, m, i)
		end
	end
	TowerBuilder.SetRoof(t.model, #order)
	bump(t)
	IncomeService.Handlers.Refresh(player)
	InventoryService.Sync(player)
	DataService.RequestSave(player)
	return index, nil
end

-- Перестановка этажа uid на номер to (DEV). Игроки на сдвигаемых этажах едут вместе со своим полом.
function TowerService.Move(player: any, uid: string, to: number, extra: { any }?): (boolean, string?)
	if not TowerMode.For(player) then
		return false, "Башня выключена"
	end
	local t = towerOf(player)
	local data = DataService.GetData(player)
	if not t or not data then
		return false, "Башни нет"
	end
	local before = table.clone(TowerRules.Order(data))
	local count = #before
	local people = occupants(t, count, extra)
	if not DataService.MoveFloor(player, uid, to) then
		return false, "Нельзя переставить"
	end
	local up = t.model.WorldPivot.UpVector
	for _, o in people do
		local floorUid = before[o.index]
		local newIndex = floorUid and TowerRules.IndexOf(data, floorUid)
		if newIndex and newIndex ~= o.index then
			local dy = TowerRules.BaseY(newIndex, cfg) - TowerRules.BaseY(o.index, cfg)
			MoveGuard.Teleport(o.player, o.root.CFrame + up * dy)
		end
	end
	t.lockUntil = os.clock() + cfg.ShiftLock
	for i, u in TowerRules.Order(data) do
		local m = t.models[u]
		if m and m:GetAttribute("Index") ~= i then
			TowerBuilder.PlaceFloor(t.model, m, i)
		end
	end
	bump(t)
	InventoryService.Sync(player)
	DataService.RequestSave(player)
	return true, nil
end

-- Тестовый предмет сразу в инвентарь (DEV, только режим башни): та же запись, что после сундука. uid или nil, причина.
function TowerService.DevGiveItem(player: any, itemId: string): (string?, string?)
	if not TowerMode.For(player) then
		return nil, "Режим башни выключен"
	end
	local def = Items[itemId]
	if not def then
		return nil, "Нет предмета " .. tostring(itemId)
	end
	local uid = HttpService:GenerateGUID(false)
	local record = {
		id = itemId,
		mods = {},
		place = "storage",
		rot = 0,
		acquiredAt = os.time(),
		source = "dev",
		boss = def.boss,
	}
	if not DataService.AddItem(player, uid, record) then
		return nil, "Запись отклонена"
	end
	if not ItemRegistry.Restore(uid, itemId, player.UserId, "storage", nil, nil) then
		DataService.RemoveItem(player, uid)
		return nil, "Реестр отказал"
	end
	InventoryService.Sync(player)
	return uid, nil
end

-- Нагрузочная башня (DEV): n этажей разных видов с доходом, без анимации. Сколько построено.
function TowerService.DevFill(player: any, n: number): number
	local data = DataService.GetData(player)
	if not TowerMode.For(player) or not data then
		return 0
	end
	local ids = {}
	for id, def in Items do
		if TowerRules.Buildable(def) and not TowerRules.FloorOf(data, id) then
			table.insert(ids, id)
		end
	end
	table.sort(ids, function(a, b)
		local da, db = Items[a], Items[b]
		return if da.boss == db.boss then a < b else da.boss < db.boss
	end)
	local built = 0
	for i = 1, math.min(n, #ids, cfg.FillMax) do
		local uid = TowerService.DevGiveItem(player, ids[i])
		if uid and TowerService.Build(player, uid, { quiet = true }) then
			built += 1
		end
	end
	InventoryService.Sync(player)
	return built
end

-- Сведения для окна инвентаря: номер этажа и «повтор» (InventoryService.Sync).
local function describe(player: any, uid: string): { [string]: any }?
	if not TowerMode.For(player) then
		return nil
	end
	local data = DataService.GetData(player)
	if not data then
		return nil
	end
	local floor = TowerRules.IndexOf(data, uid)
	return {
		tower = true,
		floor = floor,
		duplicate = if floor then nil else (TowerRules.IsDuplicate(data, uid) or nil),
	}
end

function TowerService.Init()
	InventoryService.SetTowerHooks({
		build = function(player: any, uid: any)
			local ok, reason = TowerService.Build(player, uid)
			if not ok and reason then
				Notify.Send(player, reason, "Stop")
			end
		end,
		describe = describe,
		active = function(player: any): boolean
			return TowerMode.For(player)
		end,
	})
end

-- Для серверных тестов (Server/Tests/TowerTests).
TowerService.Handlers = {
	Towers = function(): { [number]: Tower }
		return towers
	end,
}

return TowerService

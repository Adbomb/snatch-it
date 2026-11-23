--!strict
-- Убранство музея-небоскрёба у клиента (этапы B–C, docs/TOWER_PLAN.md v3 §2.2): весь вид башни строит клиент по
-- серверным моделям (Plots.Plot_n.Tower: Lobby, Floors.F_<uid>, Roof — атрибуты Origin, Index, BaseY, ItemId, State).
-- Сервер держит невидимый каркас со столкновениями у каждого этажа всегда, поэтому вид может появиться позже, чем
-- персонаж, — падать он не будет. Убранство не решает игру: детали без столкновений, лучей и касаний (кроме стен на
-- месте стен каркаса — у этого клиента в них упирается камера), в папке workspace.TowerDecor только у клиента.
-- Уровни детализации (GameConfig.Tower.Lod, раз в Step с): интерьер — этаж персонажа ±1 в этой башне, камера ближе
-- Interior или цель лифта; фасад — ближе Facade; иначе силуэт — он есть у каждого этажа всегда (башня видна целиком
-- с любой дальности и высоты). Уровень покидается на Hysteresis порога, фасад и силуэт меняются не чаще MinSwap
-- (вход в интерьер — сразу), интерьер выгружается через UnloadDelay. Смена уровня — без промежутка: старая модель
-- удаляется в том же кадре, когда готова новая. Сборка — очередью, не больше BuildPartsPerFrame деталей за кадр
-- (сначала интерьеры, потом фасады, потом силуэты; ближние раньше). Новый этаж (State Building) опускается на место за
-- BuildSeconds, сдвиг (смена BaseY) — плавно за ShiftSeconds. Удалённый этаж — убранство сразу удаляется.
-- Экспонат: на сервере у этажа только невидимый хитбокс Exhibit (uid, ItemId, доход, взаимодействие); его модель —
-- копия оригинала предмета из ReplicatedStorage.ItemPreviews (та же, что в инвентаре; одна на вид предмета) — часть
-- интерьера: ставится на место хитбокса, двигается и удаляется вместе с ним, без столкновений и лучей.
-- Счётчики для замеров — атрибуты папки TowerDecor (Views, PartsInterior, PartsFacade, PartsSilhouette, Exhibits,
-- Queue, Builds, LastInteriorMs, MaxInteriorMs): require из MCP получает отдельную копию модуля (BUGS.md).
-- Зависит от Config/GameConfig, Config/Items, Shared/Floors, Shared/TowerRules.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local Items = require(Config:WaitForChild("Items"))
local Floors = require(Shared:WaitForChild("Floors"))
local TowerRules = require(Shared:WaitForChild("TowerRules"))

local cfg = GameConfig.Tower
local lod = cfg.Lod
local FloorBuilder = Floors.FloorBuilder
local player = Players.LocalPlayer
local RISE = 8 -- на сколько выше своего места появляется новый этаж
local MESH_WAIT = 15 -- секунд: сколько ждать шаблоны мешей этажей перед первой сборкой с ними
local meshesWaited = false
local EXHIBIT = "Exhibit" -- хитбокс экспоната на сервере и его модель в интерьере

type Tween = { from: CFrame, to: CFrame, t0: number, dur: number }
type View = {
	server: Model,
	tower: Model,
	kind: string, -- "floor" | "lobby" | "roof"
	shell: Model?,
	shellTier: string?, -- "facade" | "silhouette"
	tierAt: number, -- когда сменился уровень оболочки (MinSwap)
	interior: Model?,
	interiorSeen: number,
	busyShell: boolean,
	busyInterior: boolean,
	pivot: CFrame,
	tween: Tween?,
	dead: boolean,
	priorityUntil: number,
	conns: { RBXScriptConnection },
}
type Job = { view: View, kind: string, tier: string, rank: number, distance: number }

local TowerController = {}

local views: { [Model]: View } = {}
local queue: { Job } = {}
local folder: Folder
local stats = { builds = 0, lastInterior = 0, maxInterior = 0 }

local function originOf(tower: Model): CFrame
	local origin = tower:GetAttribute("Origin")
	return if typeof(origin) == "CFrame" then origin else tower.WorldPivot
end

local function targetPivot(view: View): CFrame
	local y = view.server:GetAttribute("BaseY")
	return originOf(view.tower) * CFrame.new(0, if type(y) == "number" then y else 0, 0)
end

local function indexOf(view: View): number
	local index = view.server:GetAttribute("Index")
	return if type(index) == "number" then index else 0
end

-- Этаж (0 — холл) по высоте корня персонажа в осях башни (как TowerBuilder.IndexAt на сервере).
local function indexAtY(y: number): number
	local feet = y - cfg.SpotHeight
	if feet < cfg.Lobby.Height - cfg.Slab then
		return 0
	end
	return math.floor((feet - cfg.Lobby.Height + cfg.Slab) / cfg.FloorHeight) + 1
end

local function contextOf(view: View): { [string]: any }
	local itemId = view.server:GetAttribute("ItemId")
	local def = if type(itemId) == "string" then Items[itemId] else nil
	local accent = view.tower:GetAttribute("Accent")
	return {
		itemName = if def then def.displayName else "",
		accent = if typeof(accent) == "Color3" then accent else nil,
		stress = workspace:GetAttribute("TowerStress") == true,
	}
end

local function bricksFor(view: View, tier: string): { any }
	if view.kind == "lobby" then
		return Floors.Lobby.decor(cfg, contextOf(view), tier)
	elseif view.kind == "roof" then
		return if tier == "interior" then {} else Floors.Roof.decor(cfg, contextOf(view), tier)
	end
	local itemId = view.server:GetAttribute("ItemId")
	return Floors.Get(if type(itemId) == "string" then itemId else nil).decor(cfg, contextOf(view), tier)
end

local function setTween(view: View, from: CFrame, to: CFrame, dur: number)
	view.tween = { from = from, to = to, t0 = os.clock(), dur = dur }
	view.pivot = from
end

local function destroyView(server: Model)
	local view = views[server]
	if not view then
		return
	end
	views[server] = nil
	view.dead = true
	for _, c in view.conns do
		c:Disconnect()
	end
	if view.shell then
		view.shell:Destroy()
	end
	if view.interior then
		view.interior:Destroy()
	end
end

local function track(server: Model, tower: Model, kind: string)
	if views[server] or not tower:IsDescendantOf(workspace) then
		return
	end
	local view: View = {
		server = server,
		tower = tower,
		kind = kind,
		shell = nil,
		shellTier = nil,
		tierAt = 0,
		interior = nil,
		interiorSeen = 0,
		busyShell = false,
		busyInterior = false,
		pivot = CFrame.identity,
		tween = nil,
		dead = false,
		priorityUntil = 0,
		conns = {},
	}
	view.pivot = targetPivot(view)
	if server:GetAttribute("State") == "Building" then
		setTween(view, view.pivot + view.pivot.UpVector * RISE, view.pivot, cfg.BuildSeconds)
	end
	views[server] = view
	table.insert(
		view.conns,
		server:GetAttributeChangedSignal("BaseY"):Connect(function()
			setTween(view, view.pivot, targetPivot(view), cfg.ShiftSeconds)
		end)
	)
	-- модель ушла из мира (сама или вместе с башней: у вложенных AncestryChanged приходит с прежним родителем, не nil)
	table.insert(
		view.conns,
		server.AncestryChanged:Connect(function()
			if not server:IsDescendantOf(workspace) then
				destroyView(server)
			end
		end)
	)
end

-- Башня ушла из мира (выход владельца, выключение режима): все её виды и убранство — сразу.
local function dropTower(tower: Model)
	for server, view in views do
		if view.tower == tower then
			destroyView(server)
		end
	end
end

local function watchTower(tower: Model)
	tower.AncestryChanged:Connect(function()
		if not tower:IsDescendantOf(workspace) then
			dropTower(tower)
		end
	end)
	local lobby = tower:WaitForChild("Lobby", 10)
	if lobby and lobby:IsA("Model") then
		track(lobby, tower, "lobby")
	end
	local roof = tower:WaitForChild("Roof", 10)
	if roof and roof:IsA("Model") then
		track(roof, tower, "roof")
	end
	local floors = tower:WaitForChild("Floors", 10)
	if not floors then
		return
	end
	local function add(child: Instance)
		if child:IsA("Model") then
			-- атрибуты приходят вместе с моделью; ItemId обязателен для темы
			if child:GetAttribute("ItemId") == nil then
				child:GetAttributeChangedSignal("ItemId"):Wait()
			end
			if child:IsDescendantOf(workspace) then
				track(child, tower, "floor")
			end
		end
	end
	for _, child in floors:GetChildren() do
		task.spawn(add, child)
	end
	floors.ChildAdded:Connect(function(child)
		task.spawn(add, child)
	end)
	floors.ChildRemoved:Connect(function(child)
		if child:IsA("Model") then
			destroyView(child)
		end
	end)
end

local function watchPlot(plot: Instance)
	local function onChild(child: Instance)
		if child.Name == "Tower" and child:IsA("Model") then
			task.spawn(watchTower, child)
		end
	end
	for _, child in plot:GetChildren() do
		onChild(child)
	end
	plot.ChildAdded:Connect(onChild)
end

local function partsIn(model: Model?): number
	if not model then
		return 0
	end
	local n = 0
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") then
			n += 1
		end
	end
	return n
end

-- Модель экспоната в интерьер этажа: копия оригинала предмета из ItemPreviews на месте серверного хитбокса Exhibit
-- (в осях этажа: во время сдвига интерьер и экспонат едут вместе). Без столкновений, лучей и касаний — подбор, защита и
-- кража решаются сервером по хитбоксу. Существо оживляет CreatureController (атрибут TowerFloor — спокойная поза, как
-- на постаменте). false — хитбокса или копии ещё нет (повтор на следующем проходе).
local function attachExhibit(view: View): boolean
	local interior = view.interior
	if not interior or view.kind ~= "floor" or interior:FindFirstChild(EXHIBIT) then
		return true
	end
	local hitbox = view.server:FindFirstChild(EXHIBIT)
	local itemId = view.server:GetAttribute("ItemId")
	local previews = ReplicatedStorage:FindFirstChild("ItemPreviews")
	local source = if previews and type(itemId) == "string" then previews:FindFirstChild(itemId) else nil
	if not (hitbox and hitbox:IsA("BasePart") and source and source:IsA("Model")) then
		return false
	end
	local model = source:Clone()
	model.Name = EXHIBIT
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") then
			d.CanCollide = false
			d.CanQuery = false
			d.CanTouch = false
		elseif d:IsA("LayerCollector") or d:IsA("ProximityPrompt") then
			d:Destroy()
		end
	end
	local scale = hitbox:GetAttribute("Scale")
	if type(scale) == "number" and scale > 0 and math.abs(scale - 1) > 1e-3 then
		model:ScaleTo(scale) -- масштаб показа темы (хитбокс сервера уже такого размера)
	end
	model:PivotTo(view.pivot * targetPivot(view):ToObjectSpace(hitbox.CFrame))
	local root = model.PrimaryPart
	if root then
		root:SetAttribute("ItemUid", view.server:GetAttribute("Uid"))
		root:SetAttribute("TowerFloor", true)
	end
	model.Parent = interior
	return true
end

-- Включает или гасит лампы убранства вида (состояние — в атрибуте модели: новая модель получает его заново).
local function setLights(model: Model?, on: boolean)
	if not model or model:GetAttribute("LightsOn") == on then
		return
	end
	model:SetAttribute("LightsOn", on)
	for _, d in model:GetDescendants() do
		if d:IsA("Light") then
			d.Enabled = on
		end
	end
end

-- Свет этажа — только на своём этаже, если тема этого просит (поле soloLights темы). Лампы убранства без теней и
-- светят сквозь перекрытия (радиус больше высоты этажа): соседние этажи и холл заливали зал снизу и сверху, цвета
-- выгорали (BUGS.md). Пока камера внутри объёма такого этажа, лампы остальных видов этой башни погашены. Камера
-- снаружи, в холле или на этаже без этого поля — все лампы включены, как прежде: вид других этажей не меняется.
local function soloLights(camPos: Vector3)
	local home: View? = nil
	for _, view in views do
		if not view.dead and view.kind == "floor" then
			local rel = view.pivot:PointToObjectSpace(camPos)
			if
				math.abs(rel.X) <= cfg.Half.X
				and math.abs(rel.Z) <= cfg.Half.Y
				and rel.Y >= -cfg.Slab
				and rel.Y < cfg.FloorHeight - cfg.Slab
			then
				local itemId = view.server:GetAttribute("ItemId")
				if Floors.Get(if type(itemId) == "string" then itemId else nil).soloLights then
					home = view
				end
				break
			end
		end
	end
	for _, view in views do
		if not view.dead then
			local on = home == nil or view == home or view.tower ~= (home :: View).tower
			setLights(view.interior, on)
			setLights(view.shell, on)
		end
	end
end

-- Что нужно каждому виду сейчас; задания сборки — в очередь.
local function evaluate()
	local camera = workspace.CurrentCamera
	if not camera then
		return
	end
	local camPos = camera.CFrame.Position
	soloLights(camPos)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local now = os.clock()
	local jobs: { Job } = {}
	for _, view in views do
		if view.dead then
			continue
		end
		local center = (view.pivot * CFrame.new(0, cfg.FloorHeight / 2, 0)).Position
		local distance = (camPos - center).Magnitude
		local wantInterior = false
		if view.kind ~= "roof" then
			if root and root:IsA("BasePart") then
				local rel = originOf(view.tower):PointToObjectSpace(root.Position)
				if math.abs(rel.X) <= cfg.Half.X + 1 and math.abs(rel.Z) <= cfg.Half.Y + 1 then
					if math.abs(indexOf(view) - indexAtY(rel.Y)) <= 1 then
						wantInterior = true
					end
				end
			end
			local limit = lod.Interior * (if view.interior then lod.Hysteresis else 1)
			if distance <= limit or now < view.priorityUntil then
				wantInterior = true
			end
		end
		if wantInterior then
			view.interiorSeen = now
		end
		local keepInterior = wantInterior or (view.interior ~= nil and now - view.interiorSeen < lod.UnloadDelay)
		local facadeLimit = lod.Facade * (if view.shellTier == "facade" then lod.Hysteresis else 1)
		local tier = if keepInterior or distance <= facadeLimit then "facade" else "silhouette"
		if not keepInterior and view.interior then
			view.interior:Destroy()
			view.interior = nil
		end
		-- смена фасада и силуэта не чаще MinSwap (первая оболочка и фасад под интерьер — сразу)
		local settled = view.shellTier == nil or (keepInterior and tier == "facade") or now - view.tierAt >= lod.MinSwap
		if tier ~= view.shellTier and not view.busyShell and settled then
			local rank = if tier == "facade" then 1 else 2
			table.insert(jobs, { view = view, kind = "shell", tier = tier, rank = rank, distance = distance })
		end
		if keepInterior and not view.interior and not view.busyInterior and view.kind ~= "roof" then
			table.insert(jobs, { view = view, kind = "interior", tier = "interior", rank = 0, distance = distance })
		elseif view.interior then
			attachExhibit(view)
		end
	end
	table.sort(jobs, function(a, b)
		if a.rank ~= b.rank then
			return a.rank < b.rank
		end
		return a.distance < b.distance
	end)
	queue = jobs
end

-- Одно задание сборки (в потоке сборщика; ждёт кадры).
local function runJob(job: Job)
	local view = job.view
	if view.dead then
		return
	end
	local started = os.clock()
	if job.kind == "interior" then
		view.busyInterior = true
	else
		view.busyShell = true
	end
	local bricks = bricksFor(view, job.tier)
	if not meshesWaited then
		for _, brick in bricks do
			if brick.mesh then
				-- шаблоны мешей грузит сервер с первой башней; ждём один раз, дальше собираем из того, что есть
				FloorBuilder.WaitMeshes(MESH_WAIT)
				meshesWaited = true
				break
			end
		end
	end
	local model = FloorBuilder.BuildChunked(
		("%s_%s"):format(view.server.Name, job.tier),
		bricks,
		view.pivot,
		{ occlude = true, shadow = job.tier ~= "silhouette" },
		cfg.BuildPartsPerFrame,
		function()
			return view.dead
		end
	)
	if job.kind == "interior" then
		view.busyInterior = false
	else
		view.busyShell = false
	end
	if not model then
		return
	end
	if view.dead then
		model:Destroy()
		return
	end
	model:PivotTo(view.pivot)
	model.Parent = folder
	if job.kind == "interior" then
		if view.interior then
			view.interior:Destroy()
		end
		view.interior = model
		attachExhibit(view)
		local ms = (os.clock() - started) * 1000
		stats.lastInterior = ms
		stats.maxInterior = math.max(stats.maxInterior, ms)
	else
		if view.shell then
			view.shell:Destroy()
		end
		view.shell = model
		view.shellTier = job.tier
		view.tierAt = os.clock()
	end
	stats.builds += 1
end

local function publishStats()
	local interior, facade, silhouette, count, exhibits = 0, 0, 0, 0, 0
	for _, view in views do
		count += 1
		interior += partsIn(view.interior)
		if view.interior and view.interior:FindFirstChild(EXHIBIT) then
			exhibits += 1
		end
		if view.shellTier == "facade" then
			facade += partsIn(view.shell)
		elseif view.shellTier == "silhouette" then
			silhouette += partsIn(view.shell)
		end
	end
	folder:SetAttribute("Views", count)
	folder:SetAttribute("PartsInterior", interior)
	folder:SetAttribute("PartsFacade", facade)
	folder:SetAttribute("PartsSilhouette", silhouette)
	folder:SetAttribute("Exhibits", exhibits)
	folder:SetAttribute("Queue", #queue)
	folder:SetAttribute("Builds", stats.builds)
	folder:SetAttribute("LastInteriorMs", math.floor(stats.lastInterior * 10) / 10)
	folder:SetAttribute("MaxInteriorMs", math.floor(stats.maxInterior * 10) / 10)
end

-- Лифт (ElevatorController): интерьер этажа index башни участка plotIndex — первым в очередь на несколько секунд.
function TowerController.Prioritize(plotIndex: number, index: number)
	for _, view in views do
		if view.tower:GetAttribute("PlotIndex") == plotIndex and indexOf(view) == index and view.kind ~= "roof" then
			view.priorityUntil = os.clock() + 3
		end
	end
	evaluate()
end

-- Собран ли интерьер этажа index (для снятия затемнения лифта).
function TowerController.InteriorReady(plotIndex: number, index: number): boolean
	for _, view in views do
		if view.tower:GetAttribute("PlotIndex") == plotIndex and indexOf(view) == index and view.kind ~= "roof" then
			return view.interior ~= nil and view.shellTier == "facade"
		end
	end
	return false
end

-- Башня участка plotIndex (модель) или nil.
function TowerController.TowerOf(plotIndex: number): Model?
	for _, view in views do
		if view.tower:GetAttribute("PlotIndex") == plotIndex then
			return view.tower
		end
	end
	return nil
end

function TowerController.Init()
	folder = Instance.new("Folder")
	folder.Name = "TowerDecor"
	folder.Parent = workspace
	task.spawn(function()
		local world = workspace:WaitForChild("World")
		local plots = world:WaitForChild("Plots")
		for _, plot in plots:GetChildren() do
			watchPlot(plot)
		end
		plots.ChildAdded:Connect(watchPlot)
	end)
	-- проходы уровней детализации; счётчики — раз в секунду (обход деталей заметен при сотнях этажей)
	task.spawn(function()
		local lastStats = 0
		while true do
			task.wait(lod.Step)
			if next(views) ~= nil then
				evaluate()
			end
			-- счётчики — и когда видов не осталось (иначе после ухода башни висят прежние числа)
			if os.clock() - lastStats >= 1 and (next(views) ~= nil or folder:GetAttribute("Views") ~= 0) then
				lastStats = os.clock()
				publishStats()
			end
		end
	end)
	-- сборщик: одно задание за раз, части — по кадрам
	task.spawn(function()
		while true do
			local job = table.remove(queue, 1)
			if job then
				runJob(job)
			else
				RunService.Heartbeat:Wait()
			end
		end
	end)
	-- анимации появления и сдвига
	RunService.Heartbeat:Connect(function()
		local now = os.clock()
		for _, view in views do
			local tw = view.tween
			if tw then
				local a = math.clamp((now - tw.t0) / tw.dur, 0, 1)
				local eased = 1 - (1 - a) * (1 - a)
				view.pivot = tw.from:Lerp(tw.to, eased)
				if a >= 1 then
					view.pivot = tw.to
					view.tween = nil
				end
				if view.shell then
					view.shell:PivotTo(view.pivot)
				end
				if view.interior then
					view.interior:PivotTo(view.pivot)
				end
			end
		end
	end)
end

TowerController.IndexAtY = indexAtY -- для ElevatorController (свой этаж в списке)
TowerController.BaseY = function(index: number): number
	return TowerRules.BaseY(index, cfg)
end

return TowerController

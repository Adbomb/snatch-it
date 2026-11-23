--!strict
-- Серверная геометрия музея-небоскрёба (этап B, docs/TOWER_PLAN.md v3 §2): модель Tower участка — холл (нулевой
-- этаж: вход, сундук участка остаётся на своём месте, лифт), этажи F_<uid> и крыша. Здесь только то, что решает
-- игру: невидимые детали каркаса со столкновениями и лучами (пол, стены, тумба — у каждого построенного этажа всегда,
-- без включения по требованию), хитбокс главного экспоната («+X/сек»; модель — у клиента), точки лифта (Attachment + подсказка
-- «Лифт») и места высадки. Весь вид — у клиента (Controllers/TowerController по атрибутам модели).
-- Атрибуты: Tower — OwnerUserId, PlotIndex, Version, FloorCount, Accent; F_<uid> — Uid, ItemId, Index, BaseY, State
-- ("Building" | "Built"); у WorldPivot этажа — центр башни на уровне его пола (оси этажа).
-- Зависит от GameConfig, Shared/TowerRules, Shared/Floors, Util/ItemFactory, Services/IncomeService.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Floors = require(ReplicatedStorage.Shared.Floors)
local TowerRules = require(ReplicatedStorage.Shared.TowerRules)
local IncomeService = require(ServerScriptService.Server.Services.IncomeService)
local ItemFactory = require(ServerScriptService.Server.Util.ItemFactory)
local FloorMeshLoader = require(ServerScriptService.Server.World.FloorMeshLoader)

local cfg = GameConfig.Tower
local FloorBuilder = Floors.FloorBuilder

local TowerBuilder = {}

TowerBuilder.PromptName = "ElevatorPrompt" -- подсказка лифта: её слушает ElevatorService (ProximityPromptService)

-- Оси башни участка: центр каркаса на уровне пола музея (пол холла), вход в −Z.
function TowerBuilder.Origin(floorOrigin: CFrame): CFrame
	return floorOrigin * CFrame.new(cfg.Center)
end

-- Оси этажа index (0 — холл) в мире.
function TowerBuilder.FloorCFrame(origin: CFrame, index: number): CFrame
	return origin * CFrame.new(0, TowerRules.BaseY(index, cfg), 0)
end

local function shellModel(name: string, bricks: { any }, pivot: CFrame): Model
	local model = FloorBuilder.Build(name, bricks, pivot, { collide = true, invisible = true })
	for _, part in model:GetChildren() do
		if part:IsA("BasePart") then
			part:SetAttribute("TowerShell", true)
		end
	end
	return model
end

-- Точка лифта и места высадки этажа (Attachment на плите) и подсказка «Лифт».
local function addLiftPoints(slab: BasePart, pivot: CFrame, plotIndex: number, index: number)
	local point = Instance.new("Attachment")
	point.Name = "ElevatorPoint"
	point.WorldCFrame = pivot * CFrame.new(cfg.ElevatorPoint)
	point.Parent = slab
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = TowerBuilder.PromptName
	prompt.ActionText = "Лифт"
	prompt.ObjectText = if index == 0 then "Холл" else ("Этаж %d"):format(index)
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = cfg.ElevatorDistance - 1
	prompt.RequiresLineOfSight = false
	prompt:SetAttribute("PlotIndex", plotIndex)
	prompt.Parent = point
	for i, spot in cfg.Spots do
		local a = Instance.new("Attachment")
		a.Name = "Spot" .. i
		a.WorldCFrame = pivot * CFrame.new(spot)
		a.Parent = slab
	end
end

-- Новая модель башни участка: холл и папка этажей (этажи ставит PlaceFloor, крышу — SetRoof).
function TowerBuilder.NewTower(plotIndex: number, floorOrigin: CFrame, accent: Color3, owner: number): Model
	FloorMeshLoader.Start() -- шаблоны мешей этажей — с первой башней (в игре без режима башни не грузятся)
	local origin = TowerBuilder.Origin(floorOrigin)
	local tower = Instance.new("Model")
	tower.Name = "Tower"
	tower:SetAttribute("PlotIndex", plotIndex)
	tower:SetAttribute("OwnerUserId", owner)
	tower:SetAttribute("Version", 0)
	tower:SetAttribute("FloorCount", 0)
	tower:SetAttribute("Accent", accent)
	tower:SetAttribute("Origin", origin) -- оси башни для клиента (Origin × BaseY — оси этажа)
	tower.WorldPivot = origin
	-- PrimaryPart у моделей не задаётся: точка опоры остаётся осями этажа (иначе PivotTo ставил бы центр плиты)
	local lobby = shellModel("Lobby", Floors.Lobby.shell(cfg), origin)
	lobby:SetAttribute("Index", 0)
	lobby:SetAttribute("BaseY", 0)
	addLiftPoints(lobby:FindFirstChild("Slab") :: BasePart, origin, plotIndex, 0)
	lobby.Parent = tower
	local floors = Instance.new("Folder")
	floors.Name = "Floors"
	floors.Parent = tower
	local roof = shellModel("Roof", Floors.Roof.shell(cfg), TowerBuilder.FloorCFrame(origin, 1))
	roof.Parent = tower
	return tower
end

-- Экспонат этажа: на сервере только невидимый хитбокс по габариту предмета (ItemFactory.SizeOf): uid, ItemId,
-- «+X/сек», столкновения и лучи (взаимодействие, будущие защита и кража). Модель рисует клиент — копию оригинала
-- предмета (Controllers/TowerController); выключенное убранство у клиента ничего не открывает. Место и масштаб
-- показа — у темы (Floors.ExhibitAt).
local function placeExhibit(model: Model, pivot: CFrame, uid: string, itemId: string, theme: any)
	local at, scale = Floors.ExhibitAt(theme, cfg)
	local size = ItemFactory.SizeOf(itemId) * scale
	local part = Instance.new("Part")
	part.Name = "Exhibit"
	part.Anchored = true
	part.Size = size
	part.Transparency = 1
	part.CastShadow = false
	part.CanTouch = false
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.CFrame = pivot * at * CFrame.new(0, size.Y / 2, 0)
	part:SetAttribute("ItemUid", uid)
	part:SetAttribute("Scale", scale) -- масштаб показа темы: клиент увеличивает копию модели так же
	part:SetAttribute("ItemId", itemId)
	part:SetAttribute("TowerHitbox", true)
	part.Parent = model
	IncomeService.Label(part, itemId)
end

-- Новый этаж F_<uid> на месте index: каркас темы предмета (невидимый), экспонат, точки лифта.
function TowerBuilder.NewFloor(tower: Model, uid: string, itemId: string, index: number): Model
	local origin = tower.WorldPivot
	local pivot = TowerBuilder.FloorCFrame(origin, index)
	local theme = Floors.Get(itemId)
	local model = shellModel("F_" .. uid, theme.shell(cfg), pivot)
	local slab = model:FindFirstChild("Slab") :: BasePart
	model:SetAttribute("Uid", uid)
	model:SetAttribute("ItemId", itemId)
	model:SetAttribute("Index", index)
	model:SetAttribute("BaseY", TowerRules.BaseY(index, cfg))
	model:SetAttribute("State", "Built")
	addLiftPoints(slab, pivot, tower:GetAttribute("PlotIndex") :: number, index)
	placeExhibit(model, pivot, uid, itemId, theme)
	model.Parent = tower:FindFirstChild("Floors")
	return model
end

-- Поставить этаж на место index (сдвиг, перестановка): модель целиком (каркас, экспонат, точки) — PivotTo.
function TowerBuilder.PlaceFloor(tower: Model, model: Model, index: number)
	local pivot = TowerBuilder.FloorCFrame(tower.WorldPivot, index)
	model:PivotTo(pivot)
	model:SetAttribute("Index", index)
	model:SetAttribute("BaseY", TowerRules.BaseY(index, cfg))
	local point = model:FindFirstChild("ElevatorPoint", true)
	local prompt = point and point:FindFirstChild(TowerBuilder.PromptName)
	if prompt and prompt:IsA("ProximityPrompt") then
		prompt.ObjectText = ("Этаж %d"):format(index)
	end
end

-- Крыша над верхним этажом (count — этажей в башне).
function TowerBuilder.SetRoof(tower: Model, count: number)
	local roof = tower:FindFirstChild("Roof")
	if roof and roof:IsA("Model") then
		roof:PivotTo(TowerBuilder.FloorCFrame(tower.WorldPivot, count + 1))
		roof:SetAttribute("Index", count + 1)
		roof:SetAttribute("BaseY", TowerRules.BaseY(count + 1, cfg))
	end
	tower:SetAttribute("FloorCount", count)
end

-- Мировое место высадки i этажа index (корень персонажа над полом), лицом к экспонату (−Z).
function TowerBuilder.Spot(tower: Model, index: number, i: number): CFrame
	local pivot = TowerBuilder.FloorCFrame(tower.WorldPivot, index)
	local spot = cfg.Spots[(i - 1) % #cfg.Spots + 1]
	return pivot * CFrame.new(spot + Vector3.new(0, cfg.SpotHeight, 0))
end

-- Этаж, в объёме которого точка (мир): 0 — холл, 1…count — этажи, nil — вне контура башни или выше крыши.
function TowerBuilder.IndexAt(tower: Model, position: Vector3, count: number): number?
	local p = tower.WorldPivot:PointToObjectSpace(position)
	if math.abs(p.X) > cfg.Half.X + 0.5 or math.abs(p.Z) > cfg.Half.Y + 0.5 then
		return nil
	end
	local feet = p.Y - cfg.SpotHeight
	if feet < -cfg.Slab - 2 then
		return nil
	end
	local index = if feet < cfg.Lobby.Height - cfg.Slab
		then 0
		else math.floor((feet - cfg.Lobby.Height + cfg.Slab) / cfg.FloorHeight) + 1
	if index > count then
		return nil
	end
	return index
end

return TowerBuilder

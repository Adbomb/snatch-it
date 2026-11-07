-- Ночь (D37, D41): с началом ночи (обычной и Судной) вход в коридор уровней закрывает сплошной барьер во всю ширину
-- коридора — мерцающее силовое поле с надписью «НОЧЬ» (только на ночь; рамок и ворот на карте нет). Кто в этот момент вне Safe Zone — в опасной зоне (коридор, MapLayout.InDangerZone), —
-- теряет несомый предмет и переносится к месту появления. Кто успел добежать с предметом до Safe Zone, сохраняет
-- его и может выставить позже (доход — только на витрине). Пока ночь, сервер раз в
-- GameConfig.Time.NightCheckSeconds выводит из коридора тех, кто туда попал. С рассветом барьер убирается.
-- Бои с боссами прерывает BossService (этап 4), слоты боссов обновляет BossLootService (этап 3).
-- Зависит от MoveGuard (D52), TimeService, CarryService, Shared/GameTime, World/MapLayout, GameConfig, Util/Notify, Util/Log.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local TimeService = require(Server.Services.TimeService)
local Log = require(Server.Util.Log)
local MoveGuard = require(Server.Services.MoveGuard)
local Notify = require(Server.Util.Notify)
local MapLayout = require(Server.World.MapLayout)

local barrier: Model
local world: Instance
local night = false
local random = Random.new()

local NightService = {}

-- Точка в Safe Zone: место появления с небольшим разбросом, чтобы игроки не вставали друг в друга.
local function safePoint(): CFrame
	local spread = GameConfig.Time.SafeSpread
	local offset = Vector3.new(random:NextNumber(-spread, spread), 3, random:NextNumber(-spread, spread))
	local position = MapLayout.Spawn.position + offset
	return CFrame.lookAt(position, position + Vector3.new(0, 0, 1)) -- лицом к музеям
end

-- Выводит игроков из опасной зоны. Возвращает число перенесённых.
local function sweep(players: { Player }): number
	local moved = 0
	for _, player in players do
		local character = player.Character
		local root = character and character:FindFirstChild("HumanoidRootPart")
		if root and root:IsA("BasePart") and MapLayout.InDangerZone(root.Position) then
			MoveGuard.Teleport(player, safePoint()) -- перенос сервером (D52)
			moved += 1
			Notify.Send(player, "Ночь: коридор уровней закрыт — вы в безопасной зоне", "Stop")
		end
	end
	return moved
end

-- Игрок вне Safe Zone (в опасной зоне)?
local function outside(player: Player): boolean
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	return root ~= nil and root:IsA("BasePart") and MapLayout.InDangerZone(root.Position)
end

-- Начало ночи: барьер; кто вне Safe Zone — теряет несомое и переносится к месту появления.
local function startNight(players: { Player })
	night = true
	barrier.Parent = world
	for _, player in players do
		if outside(player) and CarryService.LoseCarried(player, "ночь застала вне Safe Zone (D37)") then
			Notify.Send(player, "Ночь застала вас вне безопасной зоны — предмет потерян", "Stop")
		end
	end
	local moved = sweep(players)
	Log.Debug("NightService", ("Ночь: коридор закрыт, перенесено в Safe Zone: %d"):format(moved))
end

local function startDay()
	night = false
	barrier.Parent = nil
end

-- Применяет фазу: ночь (обычная или Судная) — правила ночи, день и подготовка — коридор открыт.
local function apply(state: GameTime.State, previous: GameTime.State?, players: { Player }?)
	local isNight = GameTime.IsNight(state.phase)
	local wasNight = previous ~= nil and GameTime.IsNight(previous.phase)
	if isNight and not (wasNight and night) then
		startNight(players or Players:GetPlayers())
	elseif not isNight and (night or previous == nil) then
		startDay()
	end
end

function NightService.Init(worldFolder: Instance)
	world = worldFolder
	barrier = NightService.BuildBarrier()

	TimeService.OnPhaseChanged(function(state, previous)
		apply(state, previous, nil)
	end)
	apply(TimeService.Current(), nil, nil)
	task.spawn(function()
		while true do
			task.wait(GameConfig.Time.NightCheckSeconds)
			if night then
				sweep(Players:GetPlayers())
			end
		end
	end)
end

function NightService.IsNight(): boolean
	return night
end

-- Барьер: сплошное силовое поле от обрыва до обрыва (края уходят в обрывы, низ — в землю: без совпадающих граней) —
-- градиентный занавес и мерцающие соты, надпись на стороне Safe Zone и светящаяся полоса у подножия. Ставится в мир
-- только ночью.
function NightService.BuildBarrier(): Model
	local cfg = MapLayout.Barrier
	local width = MapLayout.CorridorHalf * 2 + 2
	local z = MapLayout.ZoneStartZ(1) - cfg.thickness / 2 - 0.2 -- за линией Safe Zone, на полу зоны 1
	local model = Instance.new("Model")
	model.Name = "NightBarrier"

	-- Стена: невидимая деталь, которая не пускает, с «занавесом» — градиент цвета поля на обеих сторонах (плотнее у
	-- земли, тает кверху) — и мерцающие соты ForceField поверх: цельное силовое поле, а не рамка.
	local wall = Instance.new("Part")
	wall.Name = "Wall"
	wall.Anchored = true
	wall.Transparency = 1
	wall.CastShadow = false
	wall.CanQuery = false
	wall.CanTouch = false
	wall.Size = Vector3.new(width, cfg.height + 1, cfg.thickness)
	wall.CFrame = CFrame.new(0, MapLayout.Heights.Ground + cfg.height / 2 - 0.5, z)
	wall.Parent = model
	for _, face in { Enum.NormalId.Front, Enum.NormalId.Back } do
		local curtain = Instance.new("SurfaceGui")
		curtain.Name = "Curtain"
		curtain.Face = face
		curtain.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		curtain.PixelsPerStud = 4
		curtain.LightInfluence = 0
		curtain.Brightness = 1.6
		curtain.Parent = wall
		local fill = Instance.new("Frame")
		fill.BorderSizePixel = 0
		fill.Size = UDim2.fromScale(1, 1)
		fill.BackgroundColor3 = Color3.new(1, 1, 1)
		fill.Parent = curtain
		local gradient = Instance.new("UIGradient")
		gradient.Rotation = 90 -- сверху вниз
		gradient.Color = ColorSequence.new(Color3.fromHex("6A4BFF"), Color3.fromHex("B39CFF"))
		gradient.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0.92),
			NumberSequenceKeypoint.new(0.55, 0.62),
			NumberSequenceKeypoint.new(1, 0.38),
		})
		gradient.Parent = fill
	end
	local shimmer = Instance.new("Part")
	shimmer.Name = "Shimmer"
	shimmer.Anchored = true
	shimmer.CanCollide = false
	shimmer.CanQuery = false
	shimmer.CanTouch = false
	shimmer.CastShadow = false
	shimmer.Material = Enum.Material.ForceField -- мерцающие соты, анимирует движок
	shimmer.Color = Color3.fromHex("9C80FF")
	shimmer.Size = wall.Size + Vector3.new(0, 0, 0.4)
	shimmer.CFrame = wall.CFrame
	shimmer.Parent = model

	local glow = Instance.new("Part")
	glow.Name = "Glow"
	glow.Anchored = true
	glow.CanCollide = false
	glow.CanQuery = false
	glow.CastShadow = false
	glow.Material = Enum.Material.Neon
	glow.Color = Color3.fromHex("B49BFF")
	glow.Size = Vector3.new(width - 2.4, 0.3, cfg.thickness + 0.6)
	glow.CFrame = CFrame.new(0, MapLayout.Heights.Path + 0.15, z)
	glow.Parent = model

	-- Надпись: отдельная невидимая деталь перед полем, лицом к Safe Zone (+Z).
	local sign = Instance.new("Part")
	sign.Name = "Sign"
	sign.Anchored = true
	sign.CanCollide = false
	sign.CanQuery = false
	sign.CanTouch = false
	sign.CastShadow = false
	sign.Transparency = 1
	sign.Size = Vector3.new(48, 10, 0.2)
	sign.CFrame = CFrame.lookAt(Vector3.new(0, 8, z + 1.2), Vector3.new(0, 8, z + 10))
	sign.Parent = model
	local gui = Instance.new("SurfaceGui")
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 12 -- TextScaled не крупнее 100 px
	gui.LightInfluence = 0
	gui.Brightness = 2
	gui.Parent = sign
	for _, line in {
		{ text = "🌙 НОЧЬ", size = 0.6, y = 0, weight = Enum.FontWeight.Heavy, stroke = 3 },
		{ text = "Уровни закрыты до рассвета", size = 0.3, y = 0.64, weight = Enum.FontWeight.Bold, stroke = 1.5 },
	} do
		local label = Instance.new("TextLabel")
		label.BackgroundTransparency = 1
		label.Size = UDim2.fromScale(1, line.size)
		label.Position = UDim2.fromScale(0, line.y)
		label.TextScaled = true
		label.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", line.weight)
		label.TextColor3 = Color3.fromHex("F3EEFF")
		label.Text = line.text
		local stroke = Instance.new("UIStroke")
		stroke.Color = Color3.fromHex("2A1466")
		stroke.Thickness = line.stroke
		stroke.Parent = label
		label.Parent = gui
	end
	return model
end

-- Для серверных тестов: те же функции с явным списком игроков (тестовых нет в Players:GetPlayers()).
NightService.Handlers = {
	Apply = apply,
	Sweep = sweep,
	Barrier = function(): Model
		return barrier
	end,
}

return NightService

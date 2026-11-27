-- Сигналы редкости этажей у клиента (D74, владелец 2026-11-27; серверная часть — World/FloorSignal):
--   пульсация свечения — детали с меткой FloorPulse медленно переходят от своего цвета к PulseTo и обратно
--     (Мифический, Алмазный); считается здесь, по сети идут только метка и два атрибута;
--   значок над башней — у точки с меткой TowerBeacon: имя владельца и счётчики Золотых, Мифических и Алмазных этажей
--     (иконки Stud-UI), поверх мира, виден до TowerBadge.MaxDistance стадов по земле; вблизи съезжает по оси башни
--     вниз (не выше TowerBadge.MaxElevation над горизонтом взгляда) — с точки появления верх башни не виден;
--   дальний луч — та же точка: дальше FloorRarity.Beam.FarFrom луч рисуется табличкой (её видно с любой точки карты
--     и на самой низкой графике, где движок издалека не рисует ни башню, ни Beam), вблизи — Beam сервера;
--   момент получения — у точки с меткой FloorArrival: вспышка, столб света и звук (видят все рядом).
-- Числа вида — Config/UITokens.TowerBadge, числа сигнала — Config/FloorRarity.
-- Зависит от Shared/StudUI (StudUI, CheckUIIcons), Config/UITokens, Config/FloorRarity.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local FloorRarity = require(Config:WaitForChild("FloorRarity"))
local UITokens = require(Config:WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Icons = require(Shared:WaitForChild("StudUI"):WaitForChild("CheckUIIcons"))

local PULSE_TAG, BEACON_TAG, ARRIVAL_TAG = "FloorPulse", "TowerBeacon", "FloorArrival"
local BADGE = UITokens.TowerBadge
local PULSE_STEP = 0.1 -- секунд между шагами пульсации

local FloorSignalController = {}

local player = Players.LocalPlayer

-- ---------- пульсация ----------
local pulsing: { [BasePart]: { from: Color3, to: Color3, period: number } } = {}

local function addPulse(part: Instance)
	if part:IsA("BasePart") then
		pulsing[part] = {
			from = part.Color,
			to = part:GetAttribute("PulseTo") or part.Color,
			period = part:GetAttribute("PulsePeriod") or 3,
		}
	end
end

local function pulseLoop()
	while true do
		local clock = workspace:GetServerTimeNow()
		for part, p in pulsing do
			part.Color = p.from:Lerp(p.to, 0.5 - 0.5 * math.cos(clock * 2 * math.pi / p.period))
		end
		task.wait(PULSE_STEP)
	end
end

-- ---------- значок над башней ----------
local badges: { [Instance]: BillboardGui } = {}

local function screenScale(): number
	local camera = workspace.CurrentCamera
	local v = if camera then camera.ViewportSize else Vector2.new(1050, 620)
	return math.clamp(math.min(v.X / 1050, v.Y / 620), 0.52, 1.18)
end

local function fill(gui: BillboardGui, anchor: Instance)
	local root = gui:FindFirstChild("Root") :: Frame
	root:ClearAllChildren()
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Scale = screenScale()
	scale.Parent = root
	local owner = anchor:GetAttribute("Owner") or ""
	local shown = {}
	for _, key in FloorRarity.Order do
		local n = anchor:GetAttribute(key)
		if BADGE.Rarity[key] and type(n) == "number" and n > 0 then
			table.insert(shown, { key = key, n = n })
		end
	end
	local rowY = if #shown > 0 then BADGE.NameSize + 6 else 0
	UI.ShadowText(root, owner, {
		Name = "Owner",
		Font = "Heavy",
		TextSize = BADGE.NameSize,
		Size = UDim2.new(1, 0, 0, BADGE.NameSize + 6),
		Position = UDim2.new(0.5, 0, 0, (BADGE.NameSize + 6) / 2),
		Stroke = BADGE.NameStroke,
		Thickness = 3,
	})
	if #shown == 0 then
		return
	end
	-- счётчики: тёмная стеклянная плашка, в ней «иконка ×N» цветом редкости
	local cell = BADGE.Icon + BADGE.CountWidth
	local width = #shown * cell + (#shown - 1) * BADGE.Gap + 16
	local pill = Instance.new("Frame")
	pill.Name = "Counts"
	pill.AnchorPoint = Vector2.new(0.5, 0)
	pill.Position = UDim2.new(0.5, 0, 0, rowY + 2)
	pill.Size = UDim2.fromOffset(width, BADGE.Icon + 8)
	pill.BackgroundColor3 = Color3.new(0, 0, 0)
	pill.BackgroundTransparency = 0.5
	pill.BorderSizePixel = 0
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 6)
	corner.Parent = pill
	local stroke = Instance.new("UIStroke")
	stroke.Color = Color3.new(1, 1, 1)
	stroke.Transparency = 0.75
	stroke.Thickness = 1
	stroke.Parent = pill
	pill.Parent = root
	for i, entry in shown do
		local look = BADGE.Rarity[entry.key]
		local x = 8 + (i - 1) * (cell + BADGE.Gap)
		local icon = Instance.new("ImageLabel")
		icon.Name = "Icone_" .. entry.key
		icon.BackgroundTransparency = 1
		icon.Image = Icons.Get(look.icon)
		icon.Size = UDim2.fromOffset(BADGE.Icon, BADGE.Icon)
		icon.Position = UDim2.fromOffset(x, 4)
		icon.Rotation = -8
		icon.ZIndex = 8
		icon.Parent = pill
		UI.ShadowText(pill, "×" .. entry.n, {
			Name = "Count_" .. entry.key,
			Font = "Gotham",
			TextSize = BADGE.CountSize,
			Size = UDim2.fromOffset(BADGE.CountWidth, BADGE.Icon),
			Position = UDim2.fromOffset(x + BADGE.Icon + BADGE.CountWidth / 2, 4 + BADGE.Icon / 2 + 1),
			Color = look.color,
			Stroke = look.stroke,
			Thickness = 3,
		})
	end
end

-- Дальний луч табличкой: полоса в стадах над маяком, к верху гаснет.
local farBeams: { [Instance]: BillboardGui } = {}

local function addFarBeam(anchor: BasePart)
	local signal = FloorRarity.Signal[anchor:GetAttribute("Best")]
	if not signal or not signal.beam or farBeams[anchor] then
		return
	end
	local cfg = FloorRarity.Beam
	local gui = Instance.new("BillboardGui")
	gui.Name = "TowerBeamFar"
	gui.Adornee = anchor
	gui.Size = UDim2.fromScale(cfg.FarWidth, signal.beam)
	gui.StudsOffsetWorldSpace = Vector3.new(0, signal.beam / 2, 0)
	gui.LightInfluence = 0
	gui.Brightness = 2
	gui.ResetOnSpawn = false
	gui.Enabled = false
	local bar = Instance.new("Frame")
	bar.Name = "Bar"
	bar.Size = UDim2.fromScale(1, 1)
	bar.BackgroundColor3 = Color3.fromHex(signal.glow)
	bar.BorderSizePixel = 0
	local fade = Instance.new("UIGradient")
	fade.Rotation = 90
	fade.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.35, 0.3),
		NumberSequenceKeypoint.new(1, 0),
	})
	fade.Parent = bar
	bar.Parent = gui
	gui.Parent = player:WaitForChild("PlayerGui")
	farBeams[anchor] = gui
end

local function addBeacon(anchor: Instance)
	if not anchor:IsA("BasePart") or badges[anchor] then
		return
	end
	local gui = Instance.new("BillboardGui")
	gui.Name = "TowerBadge"
	gui.Adornee = anchor
	gui.AlwaysOnTop = true
	gui.LightInfluence = 0
	gui.ResetOnSpawn = false
	gui.ClipsDescendants = false
	local s = screenScale()
	gui.Size = UDim2.fromOffset(BADGE.Size.X * s, BADGE.Size.Y * s)
	gui.StudsOffsetWorldSpace = Vector3.new(0, BADGE.Lift, 0)
	-- расстояние считается до значка, а он высоко: к пределу по земле добавляется его высота
	gui.MaxDistance = BADGE.MaxDistance + (anchor:GetAttribute("Rise") or 0)
	local root = Instance.new("Frame")
	root.Name = "Root"
	root.BackgroundTransparency = 1
	root.Size = UDim2.fromOffset(BADGE.Size.X, BADGE.Size.Y)
	root.Parent = gui
	gui.Parent = player:WaitForChild("PlayerGui")
	badges[anchor] = gui
	fill(gui, anchor)
	addFarBeam(anchor)
	anchor.AttributeChanged:Connect(function()
		if badges[anchor] then
			fill(gui, anchor)
		end
	end)
end

-- Высота значков: над башней, но в поле зрения — не выше угла MaxElevation от камеры.
local function badgeLoop()
	local slope = math.tan(math.rad(BADGE.MaxElevation))
	while true do
		local camera = workspace.CurrentCamera
		if camera then
			local eye = camera.CFrame.Position
			for anchor, gui in badges do
				local top = (anchor :: BasePart).Position
				local flat = Vector2.new(top.X - eye.X, top.Z - eye.Z).Magnitude
				local y = math.min(top.Y + BADGE.Lift, math.max(BADGE.MinHeight, eye.Y + flat * slope))
				gui.StudsOffsetWorldSpace = Vector3.new(0, y - top.Y, 0)
				local s = screenScale() * math.clamp(BADGE.FullDistance / math.max(flat, 1), BADGE.MinScale, 1)
				gui.Size = UDim2.fromOffset(BADGE.Size.X * s, BADGE.Size.Y * s)
				local scale = gui:FindFirstChild("WindowScale", true)
				if scale and scale:IsA("UIScale") then
					scale.Scale = s
				end
				local far = farBeams[anchor]
				if far then
					local distant = flat > FloorRarity.Beam.FarFrom
					far.Enabled = distant
					local beam = anchor:FindFirstChild("RarityBeam")
					if beam and beam:IsA("Beam") then
						beam.Enabled = not distant
					end
				end
			end
		end
		task.wait(PULSE_STEP)
	end
end

local function removeBeacon(anchor: Instance)
	local gui = badges[anchor]
	if gui then
		badges[anchor] = nil
		gui:Destroy()
	end
	local far = farBeams[anchor]
	if far then
		farBeams[anchor] = nil
		far:Destroy()
	end
end

-- ---------- момент получения ----------
local function arrive(anchor: Instance)
	if not anchor:IsA("BasePart") then
		return
	end
	local key = anchor:GetAttribute("Rarity")
	local cfg = FloorRarity.Arrival[key]
	local signal = FloorRarity.Signal[key]
	if not cfg or not signal or not signal.glow then
		return
	end
	local color = Color3.fromHex(signal.glow)
	local since = workspace:GetServerTimeNow() - (anchor:GetAttribute("At") or workspace:GetServerTimeNow())
	local left = cfg.time - since
	if left <= 0.3 then
		return
	end
	-- вспышка: светящийся шар раздувается и гаснет
	local flash = Instance.new("Part")
	flash.Name = "ArrivalFlash"
	flash.Shape = Enum.PartType.Ball
	flash.Anchored = true
	flash.CanCollide = false
	flash.CanQuery = false
	flash.CanTouch = false
	flash.CastShadow = false
	flash.Material = Enum.Material.Neon
	flash.Color = color
	flash.Size = Vector3.one * FloorRarity.ArrivalFlash.From
	flash.CFrame = anchor.CFrame
	flash.Parent = anchor
	local grow = TweenService:Create(
		flash,
		TweenInfo.new(FloorRarity.ArrivalFlash.Time, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
		{ Size = Vector3.one * FloorRarity.ArrivalFlash.To, Transparency = 1 }
	)
	grow:Play()
	grow.Completed:Once(function()
		flash:Destroy()
	end)
	-- столб света: от этажа вверх, к концу гаснет
	local a0 = Instance.new("Attachment")
	a0.Position = Vector3.new(0, -8, 0)
	a0.Parent = anchor
	local a1 = Instance.new("Attachment")
	a1.Position = Vector3.new(0, cfg.height, 0)
	a1.Parent = anchor
	local beam = Instance.new("Beam")
	beam.Name = "ArrivalBeam"
	beam.Attachment0, beam.Attachment1 = a0, a1
	beam.FaceCamera = true
	beam.Segments = 1
	beam.Width0, beam.Width1 = FloorRarity.Beam.Width * 2.2, FloorRarity.Beam.Width
	beam.Color = ColorSequence.new(color)
	beam.LightEmission = 1
	beam.LightInfluence = 0
	beam.Brightness = FloorRarity.Beam.Brightness
	beam.Parent = anchor
	local sound = Instance.new("Sound")
	sound.Name = "ArrivalSound"
	sound.SoundId = FloorRarity.ArrivalSound.Id
	sound.Volume = FloorRarity.ArrivalSound.Volume
	sound.RollOffMaxDistance = FloorRarity.ArrivalSound.Distance
	sound.Parent = anchor
	sound:Play()
	task.spawn(function()
		local started = os.clock()
		while anchor.Parent and os.clock() - started < left do
			local t = (os.clock() - started) / left
			local fade = if t < 0.7 then 0.05 else 0.05 + 0.95 * (t - 0.7) / 0.3
			beam.Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, fade),
				NumberSequenceKeypoint.new(1, 1),
			})
			RunService.Heartbeat:Wait()
		end
		beam:Destroy()
	end)
end

local function watch(tag: string, added: (Instance) -> (), removed: ((Instance) -> ())?)
	for _, instance in CollectionService:GetTagged(tag) do
		task.spawn(added, instance)
	end
	CollectionService:GetInstanceAddedSignal(tag):Connect(added)
	if removed then
		CollectionService:GetInstanceRemovedSignal(tag):Connect(removed)
	end
end

function FloorSignalController.Init()
	watch(PULSE_TAG, addPulse, function(part)
		pulsing[part :: BasePart] = nil
	end)
	task.spawn(pulseLoop)
	watch(BEACON_TAG, addBeacon, removeBeacon)
	task.spawn(badgeLoop)
	watch(ARRIVAL_TAG, arrive)
end

return FloorSignalController

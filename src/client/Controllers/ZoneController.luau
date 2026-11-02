-- Уровни коридора на клиенте (D41): плашка входа в уровень и «живые» голограммы названий.
-- Плашка — сверху по центру на 1.5 с: смайлик настроения уровня (GameConfig.Zones[i].mood, от доброго к страшному),
-- «УРОВЕНЬ N» и название; цвет панели — по номеру зоны (UITokens.LevelBanner). Показывается при каждом входе в
-- уровень (из Safe Zone или из соседнего уровня). В какой зоне игрок — по полу зон (workspace.World.Map.Zones,
-- атрибут Zone у папки зоны). Голограммы (тег Hologram) слегка покачиваются и мерцают — только у этого клиента;
-- ночью (на карте NightBarrier) надписи уровней гаснут. Теги Spin и Bob — вращение и покачивание украшений магазинов.
-- Зависит от Config/GameConfig, Config/UITokens, Shared/StudUI, Shared/TextCase.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local TextCase = require(Shared:WaitForChild("TextCase"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))

local player = Players.LocalPlayer
local CFG = UITokens.LevelBanner
local BOB = 0.35 -- стадов: покачивание голограммы
local BOB_PERIOD = 3

type ZoneBox = { index: number, min: Vector3, max: Vector3 }

local ZoneController = {}

local zones: { ZoneBox } = {}
local banner: CanvasGroup
local parts: { [string]: any } = {}
local showSerial = 0

local function gradient(index: number): ColorSequence
	local pair = CFG.Themes[math.clamp(index, 1, #CFG.Themes)]
	return ColorSequence.new(Color3.fromHex(pair[1]), Color3.fromHex(pair[2]))
end

-- Плашка: CanvasGroup (плавное появление всей плашки) → панель Stud-UI, круг со смайликом, номер, название.
local function buildBanner(gui: ScreenGui)
	local group = Instance.new("CanvasGroup")
	group.Name = "LevelBanner"
	group.BackgroundTransparency = 1
	group.AnchorPoint = Vector2.new(0.5, 0)
	group.Size = UDim2.fromOffset(CFG.Size.X + 16, CFG.Size.Y + 16)
	group.Position = UDim2.new(0.5, 0, 0, CFG.Top)
	group.GroupTransparency = 1
	group.Visible = false
	group.Parent = gui
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = group
	local pop = Instance.new("NumberValue")
	pop.Value = 1
	Motion.BindResponsive(scale, 1, pop)

	local panel = UI.StudPanel(group, {
		Name = "Panneau",
		Size = UDim2.fromOffset(CFG.Size.X, CFG.Size.Y),
		Position = UDim2.fromOffset(8, 8),
		Gradient = gradient(1),
		Corner = 14,
	})
	local circle = Instance.new("Frame")
	circle.Name = "Circle"
	circle.BackgroundColor3 = Color3.new(1, 1, 1)
	circle.Size = UDim2.fromOffset(CFG.Emoji, CFG.Emoji)
	circle.AnchorPoint = Vector2.new(0, 0.5)
	circle.Position = UDim2.new(0, 16, 0.5, 0)
	circle.ZIndex = 8
	circle.Parent = panel
	UI.Corner(circle, CFG.Emoji)
	local ring = UI.Stroke(circle, UI.Colors.StrokeDark, 3)
	local emoji = Instance.new("TextLabel")
	emoji.Name = "Emoji"
	emoji.BackgroundTransparency = 1
	emoji.Size = UDim2.fromScale(0.8, 0.8)
	emoji.AnchorPoint = Vector2.new(0.5, 0.5)
	emoji.Position = UDim2.fromScale(0.5, 0.52)
	emoji.TextScaled = true
	emoji.ZIndex = 9
	emoji.Parent = circle

	local left = CFG.Emoji + 32
	local number = UI.Text(panel, "", {
		Name = "Number",
		Font = "Bold",
		TextSize = CFG.NumberSize,
		AlignX = Enum.TextXAlignment.Left,
		AnchorPoint = Vector2.zero,
		Size = UDim2.new(1, -left - 12, 0, CFG.NumberSize + 4),
		Position = UDim2.fromOffset(left, 14),
		ZIndex = 9,
	})
	local title, shadow = UI.ShadowText(panel, "", {
		Name = "Title",
		ShadowName = "TitleShadow",
		Max = CFG.TitleSize,
		AlignX = Enum.TextXAlignment.Left,
		AnchorPoint = Vector2.zero,
		Size = UDim2.new(1, -left - 12, 0, CFG.TitleSize + 6),
		Position = UDim2.fromOffset(left, 36),
	})
	banner = group
	parts = { panel = panel, emoji = emoji, number = number, title = title, shadow = shadow, ring = ring, pop = pop }
end

-- Показать плашку уровня index: появление, 1.5 с на экране, исчезновение (новый вход перебивает старый).
function ZoneController.Show(index: number)
	local zone = GameConfig.Zones[index]
	if not zone or not banner then
		return
	end
	showSerial += 1
	local serial = showSerial
	local degrade = parts.panel:FindFirstChild("Degrade")
	if degrade and degrade:IsA("UIGradient") then
		degrade.Color = gradient(index)
	end
	parts.emoji.Text = zone.mood or "🙂"
	parts.number.Text = ("УРОВЕНЬ %d"):format(index)
	local name = TextCase.Upper(zone.name)
	parts.title.Text = name
	parts.shadow.Text = name

	local home = UDim2.new(0.5, 0, 0, CFG.Top)
	banner.Visible = true
	banner.GroupTransparency = 1
	banner.Position = home - UDim2.fromOffset(0, 24)
	parts.pop.Value = 0.85
	local into = TweenInfo.new(CFG.In, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
	TweenService:Create(banner, into, { GroupTransparency = 0, Position = home }):Play()
	TweenService:Create(parts.pop, into, { Value = 1 }):Play()
	task.delay(CFG.In + CFG.Hold, function()
		if serial ~= showSerial then
			return
		end
		local out = TweenInfo.new(CFG.Out, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
		local fade = TweenService:Create(banner, out, { GroupTransparency = 1, Position = home - UDim2.fromOffset(0, 16) })
		TweenService:Create(parts.pop, out, { Value = 0.92 }):Play()
		fade:Play()
		fade.Completed:Wait()
		if serial == showSerial then
			banner.Visible = false
		end
	end)
end

-- Границы зон по их полу (папки зон с атрибутом Zone, модель Floor).
local function collectZones()
	local map = workspace:WaitForChild("World"):WaitForChild("Map")
	local folder = map:WaitForChild("Zones")
	for _, zone in folder:GetChildren() do
		local index = zone:GetAttribute("Zone")
		local floor = zone:FindFirstChild("Floor")
		if type(index) == "number" and floor and floor:IsA("Model") then
			local cf, size = floor:GetBoundingBox()
			local half = size / 2
			table.insert(zones, {
				index = index,
				min = cf.Position - Vector3.new(half.X, 0, half.Z),
				max = cf.Position + Vector3.new(half.X, 0, half.Z),
			})
		end
	end
end

local function zoneAt(position: Vector3): number?
	for _, zone in zones do
		if
			position.X >= zone.min.X
			and position.X <= zone.max.X
			and position.Z >= zone.min.Z
			and position.Z <= zone.max.Z
		then
			return zone.index
		end
	end
	return nil
end

local function watchZones()
	local current: number? = nil
	while true do
		task.wait(CFG.Check)
		local character = player.Character
		local root = character and character:FindFirstChild("HumanoidRootPart")
		if root and root:IsA("BasePart") then
			local index = zoneAt(root.Position)
			if index ~= current then
				current = index
				if index then
					ZoneController.Show(index)
				end
			end
		end
	end
end

-- Голограммы: покачивание по вертикали и лёгкое мерцание (у каждой своя фаза). Детали с тегом Spin вращаются вокруг
-- вертикали (монета продажи, кристалл ауры), с тегом Bob — плавают вверх-вниз (огоньки ауры).
type Floating = { base: CFrame, phase: number, gui: SurfaceGui?, night: boolean, spin: number, bob: number }
local floating: { [BasePart]: Floating } = {}

local function track(part: Instance, kind: string)
	if not part:IsA("BasePart") then
		return
	end
	local info = floating[part]
	if not info then
		info = {
			base = part.CFrame,
			phase = ((part.Position.X + part.Position.Z) % 7) / 7 * math.pi * 2,
			gui = part:FindFirstChildWhichIsA("SurfaceGui"),
			night = false,
			spin = 0,
			bob = 0,
		}
		floating[part] = info
	end
	if kind == "Hologram" then
		info.bob = BOB
		info.night = part:GetAttribute("Night") == true
	elseif kind == "Spin" then
		info.spin = part:GetAttribute("SpinSpeed") or 1
	elseif kind == "Bob" then
		info.bob = part:GetAttribute("BobHeight") or 0.6
	end
end

local world: Instance? = nil

local function animate()
	local t = os.clock()
	world = world or workspace:FindFirstChild("World")
	-- Ночью коридор закрыт барьером: названия уровней гаснут, не спорят с надписью «НОЧЬ» на барьере.
	local night = world ~= nil and world:FindFirstChild("NightBarrier") ~= nil
	for part, info in floating do
		if not part.Parent then
			floating[part] = nil
			continue
		end
		local hidden = night and info.night
		if info.gui then
			info.gui.Enabled = not hidden
		end
		if hidden then
			continue
		end
		local wave = math.sin(t / BOB_PERIOD * 2 * math.pi + info.phase)
		local cf = info.base * CFrame.new(0, info.bob * wave, 0)
		if info.spin ~= 0 then
			cf = cf * CFrame.Angles(0, t * info.spin, 0)
		end
		part.CFrame = cf
		if info.gui then
			-- мерцание: изредка короткий «сбой» яркости, как у проектора
			local flick = if math.sin(t * 23 + info.phase) > 0.985 then 0.7 else 1
			info.gui.Brightness = 2.2 * flick + 0.2 * wave
		end
	end
end

function ZoneController.Init()
	local gui = UI.ScreenGui("LevelBanner", 30, { Menu = false, ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets })
	gui.Parent = player:WaitForChild("PlayerGui")
	buildBanner(gui)
	task.spawn(function()
		collectZones()
		watchZones()
	end)
	for _, kind in { "Hologram", "Spin", "Bob" } do
		CollectionService:GetInstanceAddedSignal(kind):Connect(function(part)
			track(part, kind)
		end)
		for _, part in CollectionService:GetTagged(kind) do
			track(part, kind)
		end
	end
	RunService.RenderStepped:Connect(animate)
end

return ZoneController

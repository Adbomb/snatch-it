-- Качалка на клиенте (D34, D35): табличка «Улучшение» во дворе каждого музея — SurfaceGui в PlayerGui на обеих сторонах табло
-- участка, текст каждому свой: владельцу — «Уровень N > Уровень N+1», цена и кнопки (Robux — заглушка «Скоро»),
-- гостю — «Гантель игрока <имя>: уровень N», у свободного участка — «Свободный участок». При качании над головой
-- всплывает «+N». Слева внизу — статистика (вид — по референсу владельца 2026-11-17): цветная 2D-наклейка и число
-- жирным курсивом с чёрной обводкой, без рамок — сила (белая) и монеты (зелёные); иконки — UI/HudIcons; доход в
-- секунду — в списке игроков Roblox (IncomeService). Только показывает и
-- просит: улучшение проверяет сервер. Зависит от Remotes, GameConfig, NumberFormat, UITokens, UI/UIKit, Shared/StudUI,
-- UI/HudIcons, UI/HudLayout.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local NumberFormat = require(Shared:WaitForChild("NumberFormat"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UIKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UIKit"))
local HudLayout = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudLayout"))
local HudIcons = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudIcons"))
local StudUI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))

local player = Players.LocalPlayer
local Dumbbell = GameConfig.Progression.Dumbbell
local MAX_LEVEL = #Dumbbell.Power
local SIGN = UITokens.GymSign
local BICEPS = "💪" -- всплывающая прибавка силы над головой
local GAIN = UITokens.GymGain

type Sign = {
	plot: Model,
	title: TextLabel,
	line: TextLabel,
	buy: UIKit.ButtonHandle,
	robux: UIKit.ButtonHandle,
}

local signs: { Sign } = {}

local GymController = {}

local function refresh(sign: Sign)
	local plot = sign.plot
	local owner = plot:GetAttribute("OwnerUserId")
	local level = plot:GetAttribute("DumbbellLevel") or 0
	local mine = owner == player.UserId
	sign.buy.Instance.Visible = false
	sign.robux.Instance.Visible = false
	sign.line.TextColor3 = UITokens.Colors.TextOnColor
	if not owner or owner == 0 or level == 0 then
		sign.title.Text = "Свободный участок"
		sign.line.Text = ""
	elseif not mine then
		sign.title.Text = ("Гантель игрока %s"):format(tostring(plot:GetAttribute("OwnerName") or ""))
		sign.line.Text = ("Уровень %d: %s"):format(level, Dumbbell.Names[level] or "")
	elseif level >= MAX_LEVEL then
		sign.title.Text = "Улучшение"
		sign.line.Text = "МАКСИМУМ"
		sign.line.TextColor3 = SIGN.Level
	else
		local price = Dumbbell.Prices[level]
		sign.title.Text = "Улучшение"
		sign.line.Text = ("Уровень %d > Уровень %d"):format(level, level + 1)
		sign.line.TextColor3 = SIGN.Level
		sign.buy:SetText("$" .. NumberFormat.Short(price))
		sign.buy:SetKind(if (player:GetAttribute("Coins") or 0) >= price then "Go" else "Disabled")
		sign.buy.Instance.Visible = true
		sign.robux.Instance.Visible = true
	end
end

-- Одна сторона табло: SurfaceGui на грани face (Front — к полю качалки, Back — к музею), текст и кнопки те же.
local function buildFace(plot: Model, board: BasePart, face: Enum.NormalId, suffix: string)
	local gui = Instance.new("SurfaceGui")
	gui.Name = "UpgradeSign_" .. plot.Name .. suffix
	gui.Adornee = board
	gui.Face = face
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = SIGN.PixelsPerStud
	gui.MaxDistance = SIGN.MaxDistance
	gui.LightInfluence = 0
	gui.ResetOnSpawn = false
	gui.Parent = player:WaitForChild("PlayerGui")

	local sign: Sign = {
		plot = plot,
		title = UIKit.Text({
			text = "",
			textSize = SIGN.TitleSize,
			size = UDim2.fromScale(0.94, 0.3),
			position = UDim2.fromScale(0.03, 0.04),
			parent = gui,
		}),
		line = UIKit.Text({
			text = "",
			textSize = SIGN.LineSize,
			size = UDim2.fromScale(0.94, 0.22),
			position = UDim2.fromScale(0.03, 0.36),
			parent = gui,
		}),
		buy = UIKit.Button({
			kind = "Go",
			text = "",
			textSize = SIGN.ButtonSize,
			size = UDim2.fromScale(0.52, 0.3),
			position = UDim2.fromScale(0.04, 0.64),
			parent = gui,
		}),
		robux = UIKit.Button({
			kind = "Info",
			text = "Скоро",
			textSize = SIGN.ButtonSize,
			size = UDim2.fromScale(0.36, 0.3),
			position = UDim2.fromScale(0.6, 0.64),
			parent = gui,
		}),
	}
	sign.buy:OnClick(function()
		Remotes.Get(Remotes.Names.GymUpgrade):FireServer()
	end)
	table.insert(signs, sign)
	for _, attribute in { "OwnerUserId", "OwnerName", "DumbbellLevel" } do
		plot:GetAttributeChangedSignal(attribute):Connect(function()
			refresh(sign)
		end)
	end
	refresh(sign)
end

-- Табло двустороннее (этап C.2, решение владельца 2026-11-16): с обратной стороны (от входа в музей) раньше была
-- пустая тёмная грань.
local function buildSign(plot: Model)
	local board = plot:WaitForChild("UpgradeBoard", 30)
	if not board or not board:IsA("BasePart") then
		return
	end
	buildFace(plot, board, Enum.NormalId.Front, "")
	buildFace(plot, board, Enum.NormalId.Back, "_Back")
end

local function refreshAll()
	for _, sign in signs do
		refresh(sign)
	end
end

-- «+N 💪» над головой: всплывает и тает.
local function showGain(amount: number)
	local character = player.Character
	local head = character and character:FindFirstChild("Head")
	if not head or not head:IsA("BasePart") then
		return
	end
	local billboard = Instance.new("BillboardGui")
	billboard.Size = GAIN.Size
	billboard.AlwaysOnTop = true
	local dx = (math.random() * 2 - 1) * GAIN.Spread
	billboard.StudsOffset = Vector3.new(dx, GAIN.Start, 0)
	billboard.Adornee = head
	local label = UIKit.Text({
		text = ("+%s %s"):format(NumberFormat.Short(amount), BICEPS),
		textSize = GAIN.TextSize,
		color = GAIN.Color,
		parent = billboard,
	})
	billboard.Parent = player:WaitForChild("PlayerGui")
	local info = TweenInfo.new(GAIN.Time, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	TweenService:Create(billboard, info, { StudsOffset = Vector3.new(dx, GAIN.Start + GAIN.Rise, 0) }):Play()
	local fade = TweenService:Create(label, info, { TextTransparency = 1 })
	fade:Play()
	fade.Completed:Connect(function()
		billboard:Destroy()
	end)
end

-- Статистика HUD v3 слева внизу (ТЗ владельца 2026-11-17): сила и монеты — иконка (наклон Stud-UI) и число с
-- объёмной тенью, без рамок и подписей. Доход в секунду — в стандартном списке игроков Roblox (leaderstats).
-- Касания не перехватывает (под ним на телефоне — джойстик).
local function buildHud()
	local cfg = UITokens.StatsHud
	local gui = StudUI.ScreenGui("GymHud", 3, { Menu = false })
	gui.Parent = player:WaitForChild("PlayerGui")
	local column = Instance.new("Frame")
	column.Name = "Stats"
	column.BackgroundTransparency = 1
	column.AnchorPoint = Vector2.new(0, 1)
	column.Position = UDim2.new(0, cfg.Margin.X, 1, -cfg.Margin.Y)
	column.Size = UDim2.fromOffset(0, 0)
	column.AutomaticSize = Enum.AutomaticSize.XY
	column.Parent = gui
	local list = Instance.new("UIListLayout")
	list.Padding = UDim.new(0, cfg.Gap)
	list.SortOrder = Enum.SortOrder.LayoutOrder
	list.HorizontalAlignment = Enum.HorizontalAlignment.Left
	list.Parent = column
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = column
	HudLayout.Track(function()
		scale.Scale = HudLayout.InfoScale()
	end)
	-- правый край столбика — граница свободной полосы у нижнего края (строка «Несёте: …» встаёт правее)
	local function reportEdge()
		HudLayout.SetBottom("Left", cfg.Margin.X + column.AbsoluteSize.X)
	end
	column:GetPropertyChangedSignal("AbsoluteSize"):Connect(reportEdge)
	reportEdge()
	local widest = math.max(cfg.Rows.Strength.icon, cfg.Rows.Coins.icon)
	-- строка: иконка в общей по ширине ячейке (числа стоят в одну линию) и число
	local function row(key: string, order: number): (TextLabel, TextLabel)
		local spec = cfg.Rows[key]
		local frame = Instance.new("Frame")
		frame.Name = key
		frame.BackgroundTransparency = 1
		frame.Size = UDim2.fromOffset(0, spec.icon)
		frame.AutomaticSize = Enum.AutomaticSize.X
		frame.LayoutOrder = order
		frame.Parent = column
		StudUI.Image(frame, (HudIcons.Get(key)), {
			Size = UDim2.fromOffset(spec.icon, spec.icon),
			Position = UDim2.fromOffset(widest / 2, spec.icon / 2),
		})
		local text, shadow = StudUI.ShadowText(frame, "", {
			Name = "Valeur",
			ShadowName = "ValeurOmbre",
			Font = StudUI.Fonts.Italic,
			Size = UDim2.fromOffset(0, spec.text + 4),
			Position = UDim2.new(0, widest + cfg.TextGap, 0.5, 0),
			AnchorPoint = Vector2.new(0, 0.5),
			AlignX = Enum.TextXAlignment.Left,
			TextSize = spec.text,
			AutoX = true,
			Color = spec.color,
			Stroke = StudUI.Flat.Stroke,
			Thickness = 3,
		})
		return text, shadow
	end
	local strength, strengthShadow = row("Strength", 1)
	local coins, coinsShadow = row("Coins", 2)
	local function set(label: TextLabel, shadow: TextLabel, text: string)
		label.Text = text
		shadow.Text = text
	end
	local function update()
		set(coins, coinsShadow, "$" .. NumberFormat.Short(player:GetAttribute("Coins") or 0))
		set(strength, strengthShadow, NumberFormat.Short(player:GetAttribute("Strength") or 0))
	end
	player:GetAttributeChangedSignal("Strength"):Connect(update)
	player:GetAttributeChangedSignal("Coins"):Connect(update)
	update()
end

function GymController.Init()
	buildHud()
	Remotes.Get(Remotes.Names.GymGain).OnClientEvent:Connect(showGain)
	player:GetAttributeChangedSignal("Coins"):Connect(refreshAll)
	task.spawn(function()
		local plots = workspace:WaitForChild("World"):WaitForChild("Plots")
		plots.ChildAdded:Connect(function(plot)
			if plot:IsA("Model") then
				task.spawn(buildSign, plot)
			end
		end)
		for _, plot in plots:GetChildren() do
			if plot:IsA("Model") then
				task.spawn(buildSign, plot)
			end
		end
	end)
end

return GymController

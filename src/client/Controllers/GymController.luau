-- Качалка на клиенте (D34, D35): табличка «Улучшение» во дворе каждого музея — SurfaceGui в PlayerGui на табло
-- участка, текст каждому свой: владельцу — «Уровень N > Уровень N+1», цена и кнопки (Robux — заглушка «Скоро»),
-- гостю — «Гантель игрока <имя>: уровень N», у свободного участка — «Свободный участок». При качании над головой
-- всплывает «+N», внизу слева — временные надписи силы и монет (до шага интерфейса Stud-UI).
-- Только показывает и просит: улучшение проверяет сервер. Зависит от Remotes, GameConfig, NumberFormat, UITokens,
-- UI/UIKit.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local NumberFormat = require(Shared:WaitForChild("NumberFormat"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UIKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UIKit"))

local player = Players.LocalPlayer
local Dumbbell = GameConfig.Progression.Dumbbell
local MAX_LEVEL = #Dumbbell.Power
local SIGN = UITokens.GymSign
local GAIN = UITokens.GymGain
local BICEPS = "💪"

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

local function buildSign(plot: Model)
	local board = plot:WaitForChild("UpgradeBoard", 30)
	if not board or not board:IsA("BasePart") then
		return
	end
	local gui = Instance.new("SurfaceGui")
	gui.Name = "UpgradeSign_" .. plot.Name
	gui.Adornee = board
	gui.Face = Enum.NormalId.Front
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

-- Временные надписи силы и монет внизу слева.
local function buildHud()
	local layout = UITokens.Layout.GymHud
	local gui = UIKit.ScreenGui("GymHud")
	-- Столбик снизу вверх: сила, над ней монеты.
	local function pill(row: number, gradient: UITokens.Gradient?): TextLabel
		local frame = UIKit.Pill({
			text = "",
			gradient = gradient,
			size = UDim2.fromOffset(layout.pill.X, layout.pill.Y),
			position = layout.position + UDim2.fromOffset(0, -row * (layout.pill.Y + layout.gap)),
			anchorPoint = Vector2.new(0, 1),
			parent = gui,
		})
		return frame:FindFirstChild("Text", true) :: TextLabel
	end
	local strength = pill(0, nil)
	local coins = pill(1, UITokens.Gradients.Coin)
	local function update()
		strength.Text = ("%s %s"):format(BICEPS, NumberFormat.Short(player:GetAttribute("Strength") or 0))
		coins.Text = "$" .. NumberFormat.Short(player:GetAttribute("Coins") or 0)
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

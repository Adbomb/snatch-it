-- PvP Судной ночи на клиенте (D46): только ввод и эффекты, всё решает сервер (PvpService).
-- Удар — ЛКМ на ПК или кнопка «Удар» (Stud-UI, справа над «Бросить»; видна только в Судную ночь); клиент не чаще
-- AttackInterval шлёт PvpAttack. Эффекты по PvpEffect: замах руки ударившего (плечевой Motor6D, локально у каждого),
-- вспышка цели, всплывающее «-N», «НОКАУТ!», лёгкая тряска камеры у того, по кому попали. Свой нокаут — лечь
-- (PlatformStand) на 15 с; звёзды над головой (BillboardGui от сервера, тег KnockStars) крутятся у всех.
-- Без загруженных ассетов: только Motor6D, Highlight, BillboardGui и Stud-UI.
-- Зависит от Remotes, Shared/StudUI, Config/Battle, Config/UITokens.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local Battle = require(Config:WaitForChild("Battle"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Config:WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))

local T = UITokens.Pvp
local player = Players.LocalPlayer

local PvpController = {}

local lastSent = -math.huge
local button: GuiButton
local spinning: { [BillboardGui]: true } = {}

local function doomNight(): boolean
	return ReplicatedStorage:GetAttribute("Phase") == "DoomNight"
end

local function attack()
	if not doomNight() or player:GetAttribute("Knocked") == true then
		return
	end
	local now = os.clock()
	if now - lastSent < Battle.Player.AttackInterval then
		return
	end
	lastSent = now
	Remotes.Get(Remotes.Names.PvpAttack):FireServer()
end

local function characterOf(userId: number?): Model?
	local other = userId and Players:GetPlayerByUserId(userId)
	return other and other.Character
end

-- Замах правой рукой: плечевой Motor6D (R15 RightShoulder, R6 Right Shoulder) — C0 вперёд и обратно.
local function swing(character: Model)
	local shoulder = character:FindFirstChild("RightShoulder", true) or character:FindFirstChild("Right Shoulder", true)
	if not shoulder or not shoulder:IsA("Motor6D") or shoulder:GetAttribute("Swinging") then
		return
	end
	shoulder:SetAttribute("Swinging", true)
	local base = shoulder.C0
	local half = TweenInfo.new(T.Swing / 2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	local forward = TweenService:Create(shoulder, half, { C0 = base * CFrame.Angles(math.rad(T.SwingAngle), 0, 0) })
	forward:Play()
	forward.Completed:Connect(function()
		local back = TweenService:Create(shoulder, half, { C0 = base })
		back:Play()
		back.Completed:Connect(function()
			shoulder:SetAttribute("Swinging", nil)
		end)
	end)
end

local function floatText(character: Model, text: string, color: Color3)
	local head = character:FindFirstChild("Head") or character.PrimaryPart
	if not head then
		return
	end
	local gui = Instance.new("BillboardGui")
	gui.Name = "PvpTexte"
	gui.Size = UDim2.fromScale(T.Damage.X, T.Damage.Y)
	gui.StudsOffset = Vector3.new(math.random(-10, 10) / 10, 2, 0)
	gui.AlwaysOnTop = true
	gui.LightInfluence = 0
	local label = UI.Text(gui, text, { Font = "Gotham", Max = 60, Color = color, Thickness = 3 })
	gui.Parent = head
	local info = TweenInfo.new(T.DamageTime, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	TweenService:Create(gui, info, { StudsOffset = gui.StudsOffset + Vector3.new(0, T.DamageRise, 0) }):Play()
	local fade = TweenService:Create(label, info, { TextTransparency = 1 })
	fade:Play()
	fade.Completed:Connect(function()
		gui:Destroy()
	end)
end

local function flash(character: Model)
	local h = Instance.new("Highlight")
	h.FillColor = Color3.new(1, 1, 1)
	h.FillTransparency = 0.3
	h.OutlineTransparency = 1
	h.DepthMode = Enum.HighlightDepthMode.Occluded
	h.Parent = character
	task.delay(T.Flash, function()
		h:Destroy()
	end)
end

local function shake()
	local camera = workspace.CurrentCamera
	for i = 1, 4 do
		task.delay(i * 0.04, function()
			local d = T.Shake * (5 - i) / 4
			camera.CFrame *= CFrame.new(math.random(-10, 10) / 10 * d, math.random(-10, 10) / 10 * d, 0)
		end)
	end
end

local function onEffect(payload: any)
	if type(payload) ~= "table" then
		return
	end
	local attacker = characterOf(payload.attacker)
	local target = characterOf(payload.target)
	if payload.kind == "Swing" or payload.kind == "Hit" then
		if attacker then
			swing(attacker)
		end
	end
	if payload.kind == "Hit" and target then
		flash(target)
		floatText(target, ("-%d"):format(math.max(1, math.floor((payload.damage or 0) + 0.5))), T.DamageColor)
		if payload.target == player.UserId then
			shake()
		end
	elseif payload.kind == "Knock" and target then
		floatText(target, "НОКАУТ!", T.KnockColor)
	end
end

-- Свой нокаут: лечь на 15 с (сервер держит скорость 0 и не даёт бить).
local function onKnocked()
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not humanoid then
		return
	end
	if player:GetAttribute("Knocked") == true then
		humanoid.PlatformStand = true
	else
		humanoid.PlatformStand = false
		humanoid:ChangeState(Enum.HumanoidStateType.GettingUp)
	end
end

local function refreshButton()
	local holder = button.Parent :: GuiObject
	holder.Visible = doomNight()
	UI.SetDisabled(button, player:GetAttribute("Knocked") == true)
end

local function buildButton()
	local gui = UI.ScreenGui("PvpHud", 6, { Menu = false })
	gui.Parent = player:WaitForChild("PlayerGui")
	local holder = Instance.new("Frame")
	holder.Name = "Racine"
	holder.BackgroundTransparency = 1
	holder.Size = UDim2.fromOffset(T.Button.X, T.Button.Y)
	holder.Position = T.ButtonPosition
	holder.AnchorPoint = Vector2.new(1, 0.5)
	holder.Parent = gui
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = holder
	Motion.BindResponsive(scale)
	button = UI.Button(holder, {
		Name = "Frapper",
		Theme = "red",
		Size = T.Button,
		Position = UDim2.fromScale(0.5, 0.5),
		Text = "Удар",
		TextSize = 30,
	})
	Motion.BindButton(button, 1.06, nil, attack)
	refreshButton()
end

local function trackStars(gui: Instance)
	if gui:IsA("BillboardGui") then
		spinning[gui] = true
		gui.Destroying:Connect(function()
			spinning[gui] = nil
		end)
	end
end

function PvpController.Init()
	buildButton()
	Remotes.Get(Remotes.Names.PvpEffect).OnClientEvent:Connect(onEffect)
	ReplicatedStorage:GetAttributeChangedSignal("Phase"):Connect(refreshButton)
	player:GetAttributeChangedSignal("Knocked"):Connect(function()
		refreshButton()
		onKnocked()
	end)
	UserInputService.InputBegan:Connect(function(input, processed)
		if not processed and input.UserInputType == Enum.UserInputType.MouseButton1 then
			attack()
		end
	end)
	CollectionService:GetInstanceAddedSignal("KnockStars"):Connect(trackStars)
	for _, gui in CollectionService:GetTagged("KnockStars") do
		trackStars(gui)
	end
	RunService.Heartbeat:Connect(function(dt)
		if next(spinning) == nil then
			return
		end
		for gui in spinning do
			local label = gui:FindFirstChild("Texte")
			if label and label:IsA("TextLabel") then
				label.Rotation = (label.Rotation + T.StarSpin * dt) % 360
			end
		end
	end)
end

return PvpController

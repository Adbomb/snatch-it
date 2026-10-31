-- Таймер фазы (D37): название фазы, обратный отсчёт и день круга с отсчётом до Судной ночи. Фазу клиент считает
-- сам той же функцией, что и сервер (Shared/GameTime от общего времени), поэтому таймер верен с первой секунды,
-- даже при входе посреди цикла. Панель Stud-UI внизу справа (D27), на сенсорном экране — над кнопкой прыжка.
-- Зависит от Shared/GameTime, Shared/StudUI, Config/UITokens.

local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local Players = game:GetService("Players")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameTime = require(Shared:WaitForChild("GameTime"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))

local TimeController = {}

local function themeFor(phase: GameTime.Phase): ColorSequence
	local cfg = UITokens.TimeHud
	if phase == "DoomNight" then
		return ColorSequence.new(cfg.DoomNight[1], cfg.DoomNight[2])
	end
	return UI.PanelThemes[cfg.Theme[phase]]
end

local function clock(seconds: number): string
	local s = math.max(0, math.ceil(seconds))
	return ("%d:%02d"):format(s // 60, s % 60)
end

local function info(state: GameTime.State): string
	if state.phase == "DoomNight" then
		return "Кражи из музеев разрешены"
	elseif state.phase == "Preparation" then
		return "Расставьте защиту музея"
	end
	local left = GameTime.DaysToDoom(state)
	return ("День %d · до Судной ночи: %d"):format(state.day, left)
end

-- Собирает панель таймера в gui и возвращает функцию отрисовки render(state, remaining). Отдельно от Init, чтобы
-- панель можно было показать в Studio без игрока (снимки интерфейса через MCP).
function TimeController.Build(gui: ScreenGui, touch: boolean): (GameTime.State, number) -> ()
	local cfg = UITokens.TimeHud
	local holder = Instance.new("Frame")
	holder.Name = "Holder"
	holder.BackgroundTransparency = 1
	holder.AnchorPoint = Vector2.new(1, 1)
	holder.Size = UDim2.fromOffset(cfg.Size.X, cfg.Size.Y)
	holder.Position = UDim2.new(1, -cfg.Margin, 1, -cfg.Margin - (if touch then cfg.TouchLift else 0))
	holder.Parent = gui
	local scale = Instance.new("UIScale")
	scale.Parent = holder
	Motion.BindResponsive(scale)

	local panel = UI.StudPanel(holder, {
		Name = "Panel",
		Size = UDim2.fromScale(1, 1),
		Gradient = themeFor("Day"),
		Corner = 12,
	})
	local pop = Instance.new("UIScale")
	pop.Name = "ButtonScale" -- его анимирует Motion.PopIn при смене фазы
	pop.Parent = panel
	local phaseText, phaseShadow = UI.ShadowText(panel, "", {
		Name = "Phase",
		ShadowName = "PhaseShadow",
		Size = UDim2.new(0.62, 0, 0, cfg.PhaseSize + 4),
		Position = UDim2.new(0.05, 0, 0, 8),
		AnchorPoint = Vector2.zero,
		AlignX = Enum.TextXAlignment.Left,
		TextSize = cfg.PhaseSize,
	})
	local timeText, timeShadow = UI.ShadowText(panel, "", {
		Name = "Time",
		ShadowName = "TimeShadow",
		Size = UDim2.new(0.4, 0, 0, cfg.TimeSize + 4),
		Position = UDim2.new(0.95, 0, 0, 4),
		AnchorPoint = Vector2.new(1, 0),
		AlignX = Enum.TextXAlignment.Right,
		TextSize = cfg.TimeSize,
	})
	local infoText = UI.Text(panel, "", {
		Name = "Info",
		Font = "Bold",
		Size = UDim2.new(0.9, 0, 0, cfg.InfoSize + 4),
		Position = UDim2.new(0.05, 0, 1, -10),
		AnchorPoint = Vector2.new(0, 1),
		AlignX = Enum.TextXAlignment.Left,
		TextSize = cfg.InfoSize,
		ZIndex = 9,
	})

	local shownPhase: string? = nil
	local shownStart = -1
	return function(state: GameTime.State, remaining: number)
		if state.phase ~= shownPhase or state.startsAt ~= shownStart then
			shownPhase, shownStart = state.phase, state.startsAt
			local gradient = panel:FindFirstChild("Degrade")
			if gradient and gradient:IsA("UIGradient") then
				gradient.Color = themeFor(state.phase)
			end
			local name = GameTime.Names[state.phase]
			phaseText.Text = name
			phaseShadow.Text = name
			infoText.Text = info(state)
			Motion.PopIn(panel)
		end
		local text = clock(remaining)
		timeText.Text = text
		timeShadow.Text = text
		local warn = remaining <= cfg.Warning and math.floor(remaining * 2) % 2 == 0
		timeText.TextColor3 = if warn then UI.Colors.Danger else UI.Colors.White
	end
end

function TimeController.Init()
	local gui = UI.ScreenGui("TimeHud", 5, { Menu = false })
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	local render = TimeController.Build(gui, UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled)
	local elapsed = UITokens.TimeHud.Refresh
	RunService.Heartbeat:Connect(function(dt)
		elapsed += dt
		if elapsed < UITokens.TimeHud.Refresh then
			return
		end
		elapsed = 0
		local state = GameTime.Current()
		render(state, state.endsAt - GameTime.Now())
	end)
end

return TimeController

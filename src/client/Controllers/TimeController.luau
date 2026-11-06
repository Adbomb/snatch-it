-- Таймер фазы (D37) — HUD v2 (D48 v2): сверху по центру, под кнопками Roblox (CoreUISafeInsets) — капсула с иконкой
-- фазы, названием и обратным отсчётом, под ней полоса фазы и строка «до Судной ночи». Фазу клиент считает сам той же
-- функцией, что и сервер (Shared/GameTime от общего времени), поэтому таймер верен с первой секунды, даже при входе
-- посреди цикла. Зависит от Shared/GameTime, Shared/StudUI, Config/UITokens, UI/HudIcons.

local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local Players = game:GetService("Players")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameTime = require(Shared:WaitForChild("GameTime"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local HudIcons = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudIcons"))

local TimeController = {}

-- Название в капсуле: у дня — его номер в круге.
local function title(state: GameTime.State): string
	local name = UITokens.TimeHud.Titles[state.phase] or GameTime.Names[state.phase]
	return if state.phase == "Day" then ("%s %d"):format(name, state.day) else name
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
	return ("до Судной ночи: %d дн."):format(left)
end

-- Собирает таймер в gui и возвращает функцию отрисовки render(state, remaining). Отдельно от Init, чтобы таймер
-- можно было показать в Studio без игрока (снимки интерфейса через MCP). touch оставлен для совместимости: место одно.
function TimeController.Build(gui: ScreenGui, _touch: boolean): (GameTime.State, number) -> ()
	local cfg = UITokens.TimeHud
	local holder = Instance.new("Frame")
	holder.Name = "Holder"
	holder.BackgroundTransparency = 1
	holder.AnchorPoint = Vector2.new(0.5, 0)
	holder.Size = UDim2.fromOffset(cfg.Size.X, cfg.Size.Y + cfg.Bar.Y + cfg.InfoSize + 18)
	holder.Position = UDim2.new(0.5, 0, 0, cfg.Top)
	holder.Parent = gui
	local scale = Instance.new("UIScale")
	scale.Parent = holder
	Motion.BindResponsive(scale)

	local capsule = Instance.new("Frame")
	capsule.Name = "Capsule"
	capsule.BackgroundColor3 = cfg.Fill
	capsule.Size = UDim2.fromOffset(cfg.Size.X, cfg.Size.Y)
	capsule.AnchorPoint = Vector2.new(0.5, 0)
	capsule.Position = UDim2.fromScale(0.5, 0)
	capsule.Parent = holder
	UI.Corner(capsule, math.floor(cfg.Size.Y / 2))
	local stroke = UI.Stroke(capsule, cfg.Stroke.Day, 3)
	local pop = Instance.new("UIScale")
	pop.Name = "ButtonScale" -- его анимирует Motion.PopIn при смене фазы
	pop.Parent = capsule
	local icon = UI.Image(capsule, "", {
		Name = "Icone",
		Size = UDim2.fromOffset(cfg.Icon, cfg.Icon),
		Position = UDim2.new(0, cfg.Icon / 2 + 8, 0.5, 0),
		Rotation = -8,
		ZIndex = 8,
	})
	local phaseText, phaseShadow = UI.ShadowText(capsule, "", {
		Name = "Phase",
		ShadowName = "PhaseShadow",
		Size = UDim2.new(0.5, 0, 0, cfg.PhaseSize + 4),
		Position = UDim2.new(0, cfg.Icon + 16, 0.5, 2),
		AnchorPoint = Vector2.new(0, 0.5),
		AlignX = Enum.TextXAlignment.Left,
		TextSize = cfg.PhaseSize,
	})
	local timeText, timeShadow = UI.ShadowText(capsule, "", {
		Name = "Time",
		ShadowName = "TimeShadow",
		Size = UDim2.new(0.38, 0, 0, cfg.TimeSize + 4),
		Position = UDim2.new(1, -18, 0.5, 2),
		AnchorPoint = Vector2.new(1, 0.5),
		AlignX = Enum.TextXAlignment.Right,
		TextSize = cfg.TimeSize,
	})
	local bar = Instance.new("Frame")
	bar.Name = "Barre"
	bar.BackgroundColor3 = cfg.Fill
	bar.BackgroundTransparency = 0.25
	bar.Size = UDim2.fromOffset(cfg.Bar.X, cfg.Bar.Y)
	bar.AnchorPoint = Vector2.new(0.5, 0)
	bar.Position = UDim2.new(0.5, 0, 0, cfg.Size.Y + 6)
	bar.Parent = holder
	UI.Corner(bar, math.floor(cfg.Bar.Y / 2))
	local fill = Instance.new("Frame")
	fill.Name = "Remplissage"
	fill.BackgroundColor3 = cfg.PhaseColor.Day
	fill.BorderSizePixel = 0
	fill.Size = UDim2.fromScale(0, 1)
	fill.Parent = bar
	UI.Corner(fill, math.floor(cfg.Bar.Y / 2))
	local infoText = UI.Text(holder, "", {
		Name = "Info",
		Font = "Bold",
		Size = UDim2.new(1, 40, 0, cfg.InfoSize + 4),
		Position = UDim2.new(0.5, 0, 0, cfg.Size.Y + cfg.Bar.Y + 10),
		AnchorPoint = Vector2.new(0.5, 0),
		TextSize = cfg.InfoSize,
		ZIndex = 9,
	})

	local shownPhase: string? = nil
	local shownStart = -1
	return function(state: GameTime.State, remaining: number)
		if state.phase ~= shownPhase or state.startsAt ~= shownStart then
			shownPhase, shownStart = state.phase, state.startsAt
			local name = title(state)
			phaseText.Text = name
			phaseShadow.Text = name
			phaseText.TextColor3 = cfg.PhaseColor[state.phase]
			stroke.Color = cfg.Stroke[state.phase]
			fill.BackgroundColor3 = cfg.PhaseColor[state.phase]
			capsule.BackgroundColor3 = if state.phase == "DoomNight" then cfg.DoomFill else cfg.Fill
			icon.Image = HudIcons.Get(state.phase)
			infoText.Text = info(state)
			Motion.PopIn(capsule)
		end
		local text = clock(remaining)
		timeText.Text = text
		timeShadow.Text = text
		local length = math.max(state.endsAt - state.startsAt, 1)
		fill.Size = UDim2.fromScale(math.clamp(1 - remaining / length, 0, 1), 1)
		local warn = remaining <= cfg.Warning and math.floor(remaining * 2) % 2 == 0
		timeText.TextColor3 = if warn then UI.Colors.Danger else UI.Colors.White
	end
end

function TimeController.Init()
	local gui = UI.ScreenGui("TimeHud", 5, { Menu = false, ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets })
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

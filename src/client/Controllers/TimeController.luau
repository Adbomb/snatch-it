-- Таймер фазы (D37; вид — по референсу владельца 2026-11-17): справа внизу — маленький плоский значок фазы (белый
-- силуэт с чёрной обводкой) и две короткие строки белым жирным курсивом с чёрной обводкой: «День 0:57» (в последние
-- секунды отсчёт мигает красным) и подпись: «до Судной ночи: N дней», в последние два дня — «Судная ночь — завтра /
-- сегодня», в подготовку и Судную ночь — что делать (D50). Панели и полосы прогресса нет; под блоком едва заметная
-- тёмная полоса, как на референсе. На касании блок стоит левее кнопки прыжка (маленький экран) или в углу под ней
-- (планшет), на ПК — в правом нижнем углу (UI/HudLayout). Касания не перехватывает.
-- Фазу клиент считает сам той же функцией, что и сервер (Shared/GameTime от общего времени), поэтому таймер верен с
-- первой секунды, даже при входе посреди цикла.
-- Зависит от Shared/GameTime, Shared/StudUI, Config/UITokens, UI/HudIcons, UI/HudLayout.

local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameTime = require(Shared:WaitForChild("GameTime"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local HudIcons = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudIcons"))
local HudLayout = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudLayout"))

local TimeController = {}

-- Название фазы без номера дня (D51: сколько осталось до Судной ночи — в подписи).
local function title(state: GameTime.State): string
	return UITokens.TimeHud.Titles[state.phase] or GameTime.Names[state.phase]
end

local function clock(seconds: number): string
	local s = math.max(0, math.ceil(seconds))
	return ("%d:%02d"):format(s // 60, s % 60)
end

-- «1 день», «2 дня», «5 дней».
local function days(n: number): string
	local tail, tens = n % 10, n % 100
	local word = if tail == 1 and tens ~= 11
		then "день"
		elseif tail >= 2 and tail <= 4 and (tens < 12 or tens > 14) then "дня"
		else "дней"
	return ("%d %s"):format(n, word)
end

-- Подпись и её цвет: в последний день — предупреждение (D50: было «до Судной ночи: 0 дн.»).
local function info(state: GameTime.State): (string, Color3)
	local cfg = UITokens.TimeHud
	if state.phase == "DoomNight" then
		return "Кражи разрешены", cfg.Danger
	elseif state.phase == "Preparation" then
		return "Расставьте защиту", UI.Colors.White
	end
	local left = GameTime.DaysToDoom(state)
	if left <= 0 then
		return "Судная ночь — сегодня", cfg.Danger
	elseif left == 1 then
		return "Судная ночь — завтра", UI.Colors.White
	end
	return "до Судной ночи: " .. days(left), UI.Colors.White
end

-- Место блока: правый нижний угол; на касании с маленьким экраном — левее кнопки прыжка (она у самого низа), на
-- планшете кнопка выше — блок в углу под ней.
local function place(holder: Frame, scale: UIScale)
	local cfg = UITokens.TimeHud
	scale.Scale = HudLayout.InfoScale()
	local right = HudLayout.TimerRight()
	holder.Position = UDim2.new(1, -right, 1, -cfg.Margin.Y)
	holder:SetAttribute("Right", right)
end

-- Собирает таймер в gui и возвращает функцию отрисовки render(state, remaining). Отдельно от Init, чтобы таймер
-- можно было показать в Studio без игрока (снимки интерфейса через MCP).
function TimeController.Build(gui: ScreenGui): (GameTime.State, number) -> ()
	local cfg = UITokens.TimeHud
	-- едва заметная тёмная полоса под блоком (к левому краю сходит на нет): текст читается на светлой земле
	local strip = Instance.new("Frame")
	strip.Name = "Bande"
	strip.BackgroundColor3 = UI.Flat.Stroke
	strip.BorderSizePixel = 0
	strip.ZIndex = 1
	strip.Parent = gui
	UI.Corner(strip, UI.Flat.SlotCorner)
	local fade = Instance.new("UIGradient")
	fade.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.35, cfg.Strip),
		NumberSequenceKeypoint.new(1, cfg.Strip),
	})
	fade.Parent = strip

	local holder = Instance.new("Frame")
	holder.Name = "Holder"
	holder.BackgroundTransparency = 1
	holder.AnchorPoint = Vector2.new(1, 1)
	holder.Size = UDim2.fromOffset(0, cfg.Icon)
	holder.AutomaticSize = Enum.AutomaticSize.X
	holder.ZIndex = 2
	holder.Parent = gui
	local scale = Instance.new("UIScale")
	scale.Parent = holder
	local row = Instance.new("UIListLayout")
	row.FillDirection = Enum.FillDirection.Horizontal
	row.VerticalAlignment = Enum.VerticalAlignment.Center
	row.SortOrder = Enum.SortOrder.LayoutOrder
	row.Padding = UDim.new(0, cfg.Gap)
	row.Parent = holder

	local iconHolder = Instance.new("Frame")
	iconHolder.Name = "IconeCadre"
	iconHolder.BackgroundTransparency = 1
	iconHolder.Size = UDim2.fromOffset(cfg.Icon, cfg.Icon)
	iconHolder.LayoutOrder = 1
	iconHolder.ZIndex = 8
	iconHolder.Parent = holder
	local pop = Instance.new("UIScale")
	pop.Name = "ButtonScale" -- его анимирует Motion.PopIn при смене фазы
	pop.Parent = iconHolder
	local icon = UI.Glyph(iconHolder, "", { Name = "Icone", Size = UDim2.fromScale(1, 1), ZIndex = 8, Thickness = 2 })

	local lines = Instance.new("Frame")
	lines.Name = "Lignes"
	lines.BackgroundTransparency = 1
	lines.Size = UDim2.fromOffset(0, cfg.PhaseSize + cfg.InfoSize + cfg.LineGap + 4)
	lines.AutomaticSize = Enum.AutomaticSize.X
	lines.LayoutOrder = 2
	lines.Parent = holder
	local column = Instance.new("UIListLayout")
	column.FillDirection = Enum.FillDirection.Vertical
	column.HorizontalAlignment = Enum.HorizontalAlignment.Left
	column.SortOrder = Enum.SortOrder.LayoutOrder
	column.Padding = UDim.new(0, cfg.LineGap)
	column.Parent = lines
	local phaseText = UI.Text(lines, "", {
		Name = "Phase",
		Font = UI.Fonts.Italic,
		Size = UDim2.fromOffset(0, cfg.PhaseSize + 4),
		Position = UDim2.new(),
		AnchorPoint = Vector2.zero,
		AlignX = Enum.TextXAlignment.Left,
		TextSize = cfg.PhaseSize,
		AutoX = true,
		Rich = true,
		Stroke = UI.Flat.Stroke,
		Thickness = 2.4,
		ZIndex = 9,
	})
	phaseText.LayoutOrder = 1
	local infoText = UI.Text(lines, "", {
		Name = "Info",
		Font = UI.Fonts.Italic,
		Size = UDim2.fromOffset(0, cfg.InfoSize),
		Position = UDim2.new(),
		AnchorPoint = Vector2.zero,
		AlignX = Enum.TextXAlignment.Left,
		TextSize = cfg.InfoSize,
		AutoX = true,
		Stroke = UI.Flat.Stroke,
		Thickness = 2.2,
		ZIndex = 9,
	})
	infoText.LayoutOrder = 2

	HudLayout.Track(function()
		place(holder, scale)
	end)
	-- левый край блока — граница свободной полосы у нижнего края (ноша встаёт левее); полоса — под блоком
	local function reportEdge()
		HudLayout.SetBottom("Right", (holder:GetAttribute("Right") or 0) + holder.AbsoluteSize.X)
		local pad = cfg.StripPad * scale.Scale
		local origin = gui.AbsolutePosition
		strip.Position = UDim2.fromOffset(
			holder.AbsolutePosition.X - origin.X - pad * 3,
			holder.AbsolutePosition.Y - origin.Y - pad / 2
		)
		strip.Size = UDim2.fromOffset(holder.AbsoluteSize.X + pad * 4, holder.AbsoluteSize.Y + pad)
	end
	holder:GetPropertyChangedSignal("AbsoluteSize"):Connect(reportEdge)
	holder:GetPropertyChangedSignal("AbsolutePosition"):Connect(reportEdge)
	holder:GetAttributeChangedSignal("Right"):Connect(reportEdge)
	reportEdge()

	local shownPhase: string? = nil
	local shownStart = -1
	local shownText = ""
	return function(state: GameTime.State, remaining: number)
		if state.phase ~= shownPhase or state.startsAt ~= shownStart then
			shownPhase, shownStart = state.phase, state.startsAt
			UI.SetGlyph(icon, (HudIcons.Get(state.phase)))
			infoText.Text, infoText.TextColor3 = info(state)
			shownText = ""
			Motion.PopIn(iconHolder)
		end
		local warn = remaining <= cfg.Warning and math.floor(remaining * 2) % 2 == 0
		local text = if warn
			then ('%s <font color="#%s">%s</font>'):format(title(state), cfg.Danger:ToHex(), clock(remaining))
			else title(state) .. " " .. clock(remaining)
		if text ~= shownText then -- строка меняется раз в секунду (и при мигании), не каждый такт
			shownText = text
			phaseText.Text = text
		end
	end
end

function TimeController.Init()
	local gui = UI.ScreenGui("TimeHud", 5, { Menu = false })
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	local render = TimeController.Build(gui)
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

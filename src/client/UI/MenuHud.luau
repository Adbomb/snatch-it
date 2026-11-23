-- Меню HUD (вид — по референсу владельца 2026-11-17): слева посередине — столбик квадратных плоских кнопок только
-- со значком, без подписей (решение владельца: подписи занимают лишнее место): «Магазин» (зелёная, корзина),
-- «Инвентарь» (голубая, рюкзак; клавиша B на ПК), «Музей» (оранжевая, здание с колоннами), «Защита» (красная, щит).
-- Значок — белый силуэт с чёрной обводкой (UI/HudIcons); на ПК у кнопки с клавишей — её значок в углу; наведение и
-- нажатие — пружина StudMotion. Кнопки добавляют контроллеры окон (Add); цвет и порядок — UITokens.MenuHud (по
-- имени кнопки); скрытая кнопка (Visible = false у её рамки) места не занимает. Название кнопки хранится в её
-- атрибуте Label (проверки, отладка); подписью оно рисуется, только если значка у кнопки нет.
-- Столбик стоит по центру экрана, но не выше кнопок Roblox или панели обучения (HudLayout.LeftTop) и не ниже
-- монет и силы слева внизу; один масштаб на весь столбик (Shared/HudMath.Menu: на очень низком экране — мельче).
-- Зависит от Shared/StudUI, Shared/HudMath, Config/UITokens, UI/HudIcons, UI/HudLayout.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local HudIcons = require(script.Parent:WaitForChild("HudIcons"))
local HudLayout = require(script.Parent:WaitForChild("HudLayout"))
local HudMath = require(Shared:WaitForChild("HudMath"))

local T = UITokens.MenuHud
local MenuHud = {}

export type Options = {
	icon: string?, -- ключ UITokens.HudIcons
	key: Enum.KeyCode?, -- значок клавиши на ПК (саму клавишу привязывает контроллер окна, здесь — только значок)
}

local column: Frame? = nil
local uiScale: UIScale? = nil

local function relayout()
	local frame, scale = column, uiScale
	if not frame or not scale then
		return
	end
	local count = 0
	for _, child in frame:GetChildren() do
		if child:IsA("GuiObject") and child.Visible then
			count += 1
		end
	end
	local view = HudLayout.Screen()
	-- рамка столбика — по экрану без верхней панели Roblox (IgnoreGuiInset), вырезы экрана уже учтены (DeviceSafeInsets)
	local topLimit = math.max(HudLayout.TopBar(), HudLayout.LeftTop())
	local top, s = HudMath.Menu(count, view.Y, HudLayout.Scale(), topLimit, HudLayout.InfoScale())
	scale.Scale = s
	frame.Position = UDim2.fromOffset(T.Margin, top)
end

local function getColumn(): Frame
	if column then
		return column
	end
	local player = Players.LocalPlayer
	local gui = UI.ScreenGui("MenuHud", 4, { Menu = false })
	gui.Parent = player:WaitForChild("PlayerGui")
	local frame = Instance.new("Frame")
	frame.Name = "Colonne"
	frame.BackgroundTransparency = 1
	frame.AnchorPoint = Vector2.zero
	frame.Size = UDim2.fromOffset(T.Button.X, 0)
	frame.AutomaticSize = Enum.AutomaticSize.Y
	frame.Parent = gui
	local list = Instance.new("UIListLayout")
	list.Padding = UDim.new(0, T.Gap)
	list.SortOrder = Enum.SortOrder.LayoutOrder
	list.HorizontalAlignment = Enum.HorizontalAlignment.Left
	list.Parent = frame
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = frame
	column = frame
	uiScale = scale
	HudLayout.Track(relayout)
	return frame
end

-- Кнопка меню: имя, название (атрибут Label; подписью не рисуется), тема кнопки и порядок сверху вниз (если имени нет в UITokens.MenuHud), действие;
-- opts — иконка и клавиша. Возвращает кнопку; прятать — её рамку (button.Parent.Visible).
function MenuHud.Add(
	name: string,
	text: string,
	theme: string,
	order: number,
	onClick: () -> (),
	opts: Options?
): GuiButton
	local o = opts or {}
	local holder = Instance.new("Frame")
	holder.Name = name
	holder.BackgroundTransparency = 1
	holder.Size = UDim2.fromOffset(T.Button.X, T.Button.Y)
	holder.LayoutOrder = T.Order[name] or order
	holder.Parent = getColumn()
	local icon = HudIcons.Get(o.icon or name) -- силуэт отмечен в наборе: кнопка нарисует его с обводкой
	local button = UI.Button(holder, {
		Name = "Bouton",
		Theme = T.Themes[name] or theme,
		Size = T.Button,
		Position = UDim2.fromScale(0.5, 0.5),
		-- только значок; подпись — запасной вид для кнопки без значка
		Text = if icon == "" then text else nil,
		TextSize = T.Text,
		Icon = if icon ~= "" then icon else nil,
		IconSize = T.IconSize,
	})
	button:SetAttribute("Label", text)
	if o.key and UserInputService.KeyboardEnabled then
		local badge = Instance.new("Frame")
		badge.Name = "Touche"
		badge.BackgroundColor3 = UI.Colors.White
		badge.Size = UDim2.fromOffset(T.KeySize, T.KeySize)
		badge.AnchorPoint = Vector2.new(0.5, 0.5)
		badge.Position = UDim2.new(1, -3, 0, 3)
		badge.ZIndex = 12
		badge.Parent = holder
		UI.Corner(badge, 5)
		UI.Stroke(badge, UI.Flat.Stroke, 2)
		UI.Text(badge, o.key.Name, {
			Name = "Texte",
			TextSize = T.KeySize - 7,
			ZIndex = 13,
			Color = UI.Flat.Stroke,
			Thickness = 0,
		})
	end
	Motion.BindButton(button, T.Hover, nil, onClick)
	-- кнопку прячут и показывают её рамкой (обучение, магазин): место освобождается, столбик встаёт заново
	holder:GetPropertyChangedSignal("Visible"):Connect(relayout)
	relayout()
	return button
end

return MenuHud

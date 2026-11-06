-- Колонка меню HUD v2 (D48 v2, Stud-UI): справа посередине — «Инвентарь» (портфель, клавиша B на ПК), «Защита» (щит)…
-- Кнопка — иконка без рамки (наклон −8°, пружина Stud-UI) и подпись с объёмной тенью под ней; на ПК — значок
-- клавиши. Одна WindowScale на колонку: на телефоне колонка выше кнопки прыжка. Кнопки добавляют контроллеры (Add);
-- порядок — order. Иконки — UI/HudIcons (UITokens.HudIcons). Зависит от Shared/StudUI, Config/UITokens, UI/HudIcons.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local HudIcons = require(script.Parent:WaitForChild("HudIcons"))

local T = UITokens.MenuHud
local MenuHud = {}

export type Options = {
	icon: string?, -- ключ UITokens.HudIcons
	key: Enum.KeyCode?, -- значок клавиши на ПК (саму клавишу привязывает контроллер окна, здесь — только значок)
}

local column: Frame? = nil

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
	frame.AnchorPoint = Vector2.new(1, 0.5)
	frame.Position = UDim2.new(1, -T.Margin, 0.5, 0)
	frame.Size = UDim2.fromOffset(T.Icon + T.Margin, 0)
	frame.AutomaticSize = Enum.AutomaticSize.Y
	frame.Parent = gui
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, T.Gap)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.Parent = frame
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = frame
	Motion.BindResponsive(scale)
	column = frame
	return frame
end

-- Кнопка меню: имя, подпись, тема Stud-UI (у кнопок-иконок не видна, оставлена для совместимости), порядок сверху
-- вниз, действие; opts — иконка и клавиша.
function MenuHud.Add(
	name: string,
	text: string,
	_theme: string,
	order: number,
	onClick: () -> (),
	opts: Options?
): GuiButton
	local o = opts or {}
	local holder = Instance.new("Frame")
	holder.Name = name
	holder.BackgroundTransparency = 1
	holder.Size = UDim2.fromOffset(T.Icon + T.Margin, T.Icon + T.LabelGap + T.Label + 4)
	holder.LayoutOrder = order
	holder.Parent = getColumn()
	local button = Instance.new("ImageButton")
	button.Name = "Bouton"
	button.BackgroundTransparency = 1
	button.Image = HudIcons.Get(o.icon or name)
	button.ScaleType = Enum.ScaleType.Fit
	button.Size = UDim2.fromOffset(T.Icon, T.Icon)
	button.AnchorPoint = Vector2.new(0.5, 0)
	button.Position = UDim2.fromScale(0.5, 0)
	button.Rotation = T.Tilt
	button.Parent = holder
	local scale = Instance.new("UIScale")
	scale.Name = "ButtonScale"
	scale.Parent = button
	UI.ShadowText(holder, text, {
		Name = "Label",
		ShadowName = "LabelShadow",
		Size = UDim2.new(1, 16, 0, T.Label + 4),
		Position = UDim2.new(0.5, 0, 0, T.Icon + T.LabelGap),
		AnchorPoint = Vector2.new(0.5, 0),
		TextSize = T.Label,
	})
	if o.key and UserInputService.KeyboardEnabled then
		local badge = Instance.new("Frame")
		badge.Name = "Touche"
		badge.BackgroundColor3 = UI.Colors.White
		badge.Size = UDim2.fromOffset(T.KeySize, T.KeySize)
		badge.AnchorPoint = Vector2.new(1, 1)
		badge.Position = UDim2.new(0.5, T.Icon / 2, 0, T.Icon)
		badge.ZIndex = 12
		badge.Parent = holder
		UI.Corner(badge, 6)
		UI.Stroke(badge, UI.Colors.StrokeDark, 2.5)
		UI.Text(badge, o.key.Name, { Name = "Texte", TextSize = T.KeySize - 8, ZIndex = 13 })
	end
	Motion.BindButton(button, T.Hover, nil, onClick)
	return button
end

return MenuHud

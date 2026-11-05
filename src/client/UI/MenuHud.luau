-- Колонка кнопок меню в HUD (D46, Stud-UI): «Инвентарь», «Защита» … — одна колонка слева, над столбиком надписей
-- силы и монет (UITokens.Layout.GymHud), под одним WindowScale: на телефоне не налезает на столбик и джойстик, на ПК —
-- не под чатом. Кнопки добавляют контроллеры (Add); порядок — order. Зависит от Shared/StudUI, Config/UITokens.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))

local T = UITokens.MenuHud
local MenuHud = {}

local column: Frame? = nil

local function getColumn(): Frame
	if column then
		return column
	end
	local player = Players.LocalPlayer
	local gui = UI.ScreenGui("MenuHud", 4, { Menu = false })
	gui.Parent = player:WaitForChild("PlayerGui")
	-- над столбиком надписей (снизу вверх: 3 надписи и промежутки между ними), отступ AbovePills
	local pills = UITokens.Layout.GymHud
	local stack = 3 * pills.pill.Y + 2 * pills.gap
	local frame = Instance.new("Frame")
	frame.Name = "Colonne"
	frame.BackgroundTransparency = 1
	frame.AnchorPoint = Vector2.new(0, 1)
	frame.Position = UDim2.new(0, T.Margin, pills.position.Y.Scale, -(stack + T.AbovePills))
	frame.Size = UDim2.fromOffset(T.Button.X, 0)
	frame.AutomaticSize = Enum.AutomaticSize.Y
	frame.Parent = gui
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, T.Gap)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.VerticalAlignment = Enum.VerticalAlignment.Bottom
	layout.Parent = frame
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = frame
	Motion.BindResponsive(scale)
	column = frame
	return frame
end

-- Кнопка меню: текст, тема Stud-UI, порядок сверху вниз, действие.
function MenuHud.Add(name: string, text: string, theme: string, order: number, onClick: () -> ()): GuiButton
	local holder = Instance.new("Frame")
	holder.Name = name
	holder.BackgroundTransparency = 1
	holder.Size = UDim2.fromOffset(T.Button.X, T.Button.Y)
	holder.LayoutOrder = order
	holder.Parent = getColumn()
	local button = UI.Button(holder, {
		Name = "Bouton",
		Theme = theme,
		Size = T.Button,
		Position = UDim2.fromScale(0.5, 0.5),
		Text = text,
		TextSize = 26,
	})
	Motion.BindButton(button, 1.04, nil, onClick)
	return button
end

return MenuHud

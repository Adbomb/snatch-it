-- Колонка меню HUD v2 (D48 v2, Stud-UI): справа посередине — «Инвентарь» (портфель, клавиша B на ПК), «Защита» (щит),
-- «Магазин» (тележка), «Музей» (дом, D56). Кнопка — иконка без рамки (наклон −8°, пружина Stud-UI) и подпись с
-- объёмной тенью под ней; на ПК — значок клавиши. Одна WindowScale на меню. Кнопки добавляют контроллеры (Add);
-- порядок — order, скрытая кнопка (Visible = false у её рамки) места не занимает.
-- D56: столбик по центру экрана должен уместиться между кнопками Roblox сверху и низом экрана, а на касании — кнопкой
-- прыжка (UITokens.MenuHud: TopReserve, BottomReserve, Jump, JumpSmall). Не умещается — кнопки встают сеткой в два
-- столбца; число столбцов сообщается UI/HudLayout (уведомления держатся левее меню; «Удар» при одном столбце —
-- левее меню, при сетке — над ней: сетка на касании стоит между местом «Удара» и кнопкой прыжка). В Studio экран
-- подменяют атрибуты игрока DevViewport и DevTouch (как у окон «Инвентарь» и «Магазин»).
-- Иконки — UI/HudIcons (UITokens.HudIcons). Зависит от Shared/StudUI, Config/GameConfig, Config/UITokens, UI/HudIcons,
-- UI/HudLayout.

local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local HudIcons = require(script.Parent:WaitForChild("HudIcons"))
local HudLayout = require(script.Parent:WaitForChild("HudLayout"))

local T = UITokens.MenuHud
local CELL = Vector2.new(T.Icon + T.Margin, T.Icon + T.LabelGap + T.Label + 4) -- рамка кнопки: иконка и подпись
local MenuHud = {}

export type Options = {
	icon: string?, -- ключ UITokens.HudIcons
	key: Enum.KeyCode?, -- значок клавиши на ПК (саму клавишу привязывает контроллер окна, здесь — только значок)
}

local column: Frame? = nil
local grid: UIGridLayout? = nil

-- Сколько столбцов нужно count кнопкам на экране viewport (px) при масштабе scale: один, если столбик по центру экрана
-- не задевает ни кнопки Roblox сверху, ни низ экрана (на касании — кнопку прыжка); иначе два.
function MenuHud.ColumnsFor(count: number, viewport: Vector2, scale: number, touch: boolean): number
	if count <= 2 then
		return 1 -- две кнопки умещаются на любом экране, одной сетка не нужна
	end
	local height = (count * CELL.Y + (count - 1) * T.Gap) * scale
	local bottom = if not touch
		then T.BottomReserve
		elseif math.min(viewport.X, viewport.Y) <= T.SmallSide then T.JumpSmall
		else T.Jump
	local top = viewport.Y / 2 - height / 2
	local low = viewport.Y / 2 + height / 2
	return if top >= T.TopReserve and low <= viewport.Y - bottom then 1 else 2
end

-- Экран, по которому считается раскладка: настоящий или подменённый в Studio (DevViewport, DevTouch).
local function screen(): (Vector2, number, boolean)
	local player = Players.LocalPlayer
	local fake = GameConfig.DevMode and player:GetAttribute("DevViewport")
	if typeof(fake) == "Vector2" then
		local scale = math.clamp(
			math.min(fake.X / Motion.REFERENCE.X, fake.Y / Motion.REFERENCE.Y),
			Motion.MIN_SCALE,
			Motion.MAX_SCALE
		)
		return fake, scale, player:GetAttribute("DevTouch") == true
	end
	local touch = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
	return workspace.CurrentCamera.ViewportSize, Motion.ScreenScale(), touch
end

-- Расставить видимые кнопки: столбик или сетка в два столбца; размер рамки меню — по ним.
local function relayout()
	local frame, layout = column, grid
	if not frame or not layout then
		return
	end
	local count = 0
	for _, child in frame:GetChildren() do
		if child:IsA("GuiObject") and child.Visible then
			count += 1
		end
	end
	local viewport, scale, touch = screen()
	local columns = MenuHud.ColumnsFor(count, viewport, scale, touch)
	local rows = math.max(math.ceil(count / columns), 1)
	layout.FillDirectionMaxCells = columns
	frame.Size = UDim2.fromOffset(columns * CELL.X + (columns - 1) * T.ColumnGap, rows * CELL.Y + (rows - 1) * T.Gap)
	-- сетка на касании — посередине между местом кнопки «Удар» (в Судную ночь она встаёт над сеткой у правого края,
	-- Controllers/PvpController) и кнопкой прыжка; в остальных случаях — по центру экрана
	if columns > 1 and touch then
		local pvp = UITokens.Pvp
		local top = GuiService:GetGuiInset().Y
			+ pvp.ButtonTop
			+ math.max(pvp.Button.Y * scale, pvp.MinTouch)
			+ T.SlotGap
		local jump = if math.min(viewport.X, viewport.Y) <= T.SmallSide then T.JumpSmall else T.Jump
		frame.Position = UDim2.new(1, -T.Margin, 0, math.floor((top + viewport.Y - jump) / 2))
	else
		frame.Position = UDim2.new(1, -T.Margin, 0.5, 0)
	end
	HudLayout.SetMenuColumns(columns)
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
	frame.AnchorPoint = Vector2.new(1, 0.5)
	frame.Position = UDim2.new(1, -T.Margin, 0.5, 0)
	frame.Size = UDim2.fromOffset(CELL.X, CELL.Y)
	frame.Parent = gui
	local layout = Instance.new("UIGridLayout")
	layout.CellSize = UDim2.fromOffset(CELL.X, CELL.Y)
	layout.CellPadding = UDim2.fromOffset(T.ColumnGap, T.Gap)
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.FillDirectionMaxCells = 1
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Right
	layout.VerticalAlignment = Enum.VerticalAlignment.Top
	layout.Parent = frame
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = frame
	Motion.BindResponsive(scale)
	column = frame
	grid = layout
	workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(relayout)
	player:GetAttributeChangedSignal("DevViewport"):Connect(relayout)
	player:GetAttributeChangedSignal("DevTouch"):Connect(relayout)
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
	holder.Size = UDim2.fromOffset(CELL.X, CELL.Y)
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
	-- кнопку прячут и показывают её рамкой (обучение, магазин): место освобождается, раскладка считается заново
	holder:GetPropertyChangedSignal("Visible"):Connect(relayout)
	relayout()
	return button
end

return MenuHud

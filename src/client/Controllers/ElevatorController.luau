--!strict
-- Окно лифта музея-небоскрёба (этапы B–C, режим башни DEV): компактный технический список этажей в скине Flat
-- (финальное оформление — позже, по HUD v4). Открывает сервер (подсказка «Лифт» → Remotes.OpenWindow «Elevator»,
-- участок). Вверху — быстрый переход: «Холл» и «Верх» (поехать), «−10» / «+10» (листать) и номера показанной страницы;
-- ниже — страница по PAGE этажей «Этаж N · название предмета» (сверху — верхние) по моделям башни (атрибуты Index,
-- ItemId), обновляется по Version. Открывается страница своего этажа. Свой этаж подсвечен и не нажимается. Нажатие —
-- только просьба (ElevatorGo: участок, этаж); переносит сервер. Пока идёт перенос — короткое затемнение; снимается,
-- когда интерьер этажа собран (TowerController), но не позже 1 с. Отказ сервера (ElevatorResult без ok) —
-- уведомлением. На касании кнопки не ниже MinTouchButton (D32).
-- Зависит от Shared/StudUI, Remotes, Config/GameConfig, Config/Items, Config/UITokens, TowerController,
-- NotifyController.

local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local Items = require(Config:WaitForChild("Items"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Config:WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local NotifyController = require(script.Parent:WaitForChild("NotifyController"))
local TowerController = require(script.Parent:WaitForChild("TowerController"))

local cfg = GameConfig.Tower
local player = Players.LocalPlayer

local ElevatorController = {}

local gui: ScreenGui? = nil
local menu: any = nil
local list: ScrollingFrame? = nil
local plotOpen: number? = nil
local versionConn: RBXScriptConnection? = nil
local fade: Frame? = nil
local fadeToken = 0
local listWidth = 300 -- ширина строки списка в опорных пикселях окна (задаёт build)
local nav: Frame? = nil -- быстрый переход над списком
local PAGE = 10 -- этажей на странице списка
local page = 1 -- показанная страница (1 — этажи 1…PAGE)

local function touch(): boolean
	local fake = GameConfig.DevMode and player:GetAttribute("DevTouch")
	return fake == true or (UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled)
end

local function myIndex(tower: Model): number?
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local origin = tower:GetAttribute("Origin")
	if not root or not root:IsA("BasePart") or typeof(origin) ~= "CFrame" then
		return nil
	end
	local rel = origin:PointToObjectSpace(root.Position)
	if math.abs(rel.X) > cfg.Half.X + 1 or math.abs(rel.Z) > cfg.Half.Y + 1 then
		return nil
	end
	return TowerController.IndexAtY(rel.Y)
end

local function ensureFade(): Frame
	if fade and fade.Parent then
		return fade
	end
	local screen = Instance.new("ScreenGui")
	screen.Name = "LiftFade"
	screen.IgnoreGuiInset = true
	screen.DisplayOrder = 40
	screen.ResetOnSpawn = false
	screen.Parent = player:WaitForChild("PlayerGui")
	local frame = Instance.new("Frame")
	frame.Size = UDim2.fromScale(1, 1)
	frame.BackgroundColor3 = Color3.new(0, 0, 0)
	frame.BackgroundTransparency = 1
	frame.BorderSizePixel = 0
	frame.Parent = screen
	fade = frame
	return frame
end

-- Затемнение на время переноса: снимается, когда интерьер этажа собран, но не позже 1 с.
local function flash(plotIndex: number, index: number)
	fadeToken += 1
	local token = fadeToken
	local frame = ensureFade()
	TweenService:Create(frame, TweenInfo.new(0.15), { BackgroundTransparency = 0.1 }):Play()
	task.spawn(function()
		local t0 = os.clock()
		task.wait(0.3)
		while os.clock() - t0 < 1 and not TowerController.InteriorReady(plotIndex, index) do
			task.wait(0.05)
		end
		if token == fadeToken then
			TweenService:Create(frame, TweenInfo.new(0.25), { BackgroundTransparency = 1 }):Play()
		end
	end)
end

local function go(plotIndex: number, index: number)
	TowerController.Prioritize(plotIndex, index)
	Remotes.Get(Remotes.Names.ElevatorGo):FireServer(plotIndex, index)
	flash(plotIndex, index)
	if menu then
		menu.Close()
	end
end

local function rowHeight(): number
	return if touch() then math.max(44, UITokens.Layout.MinTouchButton.Y) else 40
end

-- Кнопка окна: свой этаж — зелёная и не нажимается.
local function liftButton(
	parent: Instance,
	name: string,
	text: string,
	width: number,
	current: boolean,
	order: number,
	onClick: () -> ()
)
	local button = UI.Button(parent, {
		Name = name,
		Theme = if current then "green" else "blue",
		Size = Vector2.new(width, rowHeight()),
		Text = text,
		TextSize = 20,
		ZIndex = 6,
	})
	button.LayoutOrder = order
	button.AnchorPoint = Vector2.zero
	if not current then
		Motion.BindButton(button, 1.03, nil, onClick)
	end
	return button
end

local function fill(plotIndex: number)
	local frame, bar = list, nav
	local tower = TowerController.TowerOf(plotIndex)
	if not frame or not bar or not tower then
		return
	end
	for _, container in { frame, bar } do
		for _, child in container:GetChildren() do
			if child:IsA("GuiObject") then
				child:Destroy()
			end
		end
	end
	local names: { [number]: string } = {}
	local count = 0
	local floors = tower:FindFirstChild("Floors")
	for _, f in if floors then floors:GetChildren() else {} do
		local index, itemId = f:GetAttribute("Index"), f:GetAttribute("ItemId")
		if type(index) == "number" then
			local def = if type(itemId) == "string" then Items[itemId] else nil
			names[index] = if def then def.displayName else "?"
			count = math.max(count, index)
		end
	end
	local pages = math.max(1, math.ceil(count / PAGE))
	page = math.clamp(page, 1, pages)
	local here = myIndex(tower)
	-- быстрый переход: «Холл», «−10», «41–50», «+10», «Верх» (листать — только если этажей больше страницы)
	local gap = 6
	local paged = count > PAGE
	local cells = if paged then 5 else 1
	local cell = math.floor((listWidth - gap * (cells - 1)) / cells)
	liftButton(
		bar,
		"Hall",
		if here == 0 then "Холл · вы здесь" else "Холл",
		cell,
		here == 0,
		1,
		function()
			go(plotIndex, 0)
		end
	)
	if paged then
		local function turn(delta: number)
			page = math.clamp(page + delta, 1, pages)
			fill(plotIndex)
		end
		local down = liftButton(bar, "Down", "−10", cell, false, 2, function()
			turn(-1)
		end)
		local up = liftButton(bar, "Up", "+10", cell, false, 4, function()
			turn(1)
		end)
		UI.SetDisabled(down, page <= 1)
		UI.SetDisabled(up, page >= pages)
		local label = UI.Text(bar, ("%d–%d"):format((page - 1) * PAGE + 1, math.min(count, page * PAGE)), {
			Name = "Page",
			Size = UDim2.fromOffset(cell, rowHeight()),
			AnchorPoint = Vector2.zero,
			Position = UDim2.fromScale(0, 0),
			Max = 22,
			ZIndex = 6,
		})
		label.LayoutOrder = 3
		liftButton(bar, "Top", ("Верх · %d"):format(count), cell, here == count, 5, function()
			go(plotIndex, count)
		end)
	end
	-- страница этажей, сверху — верхние, как в лифте
	local rowH = rowHeight()
	local first, last = (page - 1) * PAGE + 1, math.min(count, page * PAGE)
	local order = 0
	for index = last, first, -1 do
		order += 1
		local text = ("Этаж %d · %s"):format(index, names[index] or "?")
		local current = index == here
		liftButton(
			frame,
			"Etage_" .. index,
			if current then text .. " · вы здесь" else text,
			listWidth,
			current,
			order,
			function()
				go(plotIndex, index)
			end
		)
	end
	if count == 0 then
		UI.Text(frame, "Этажей пока нет — постройте первый из инвентаря", {
			Name = "Vide",
			Size = UDim2.fromOffset(listWidth, rowH),
			AnchorPoint = Vector2.zero,
			Max = 20,
			ZIndex = 6,
		})
	end
	frame.CanvasSize = UDim2.fromOffset(0, math.max(1, order) * (rowH + 6) + 6)
end

local builtFor: Vector2? = nil -- экран, под который собрано окно (сменился — пересобрать, как у других окон)

local function build()
	local viewport = workspace.CurrentCamera.ViewportSize
	if gui and builtFor == viewport then
		return
	end
	if gui then
		if menu and menu.Destroy then
			menu.Destroy()
		end
		gui:Destroy()
		gui, menu, list, nav = nil, nil, nil, nil
	end
	builtFor = viewport
	local screen = UI.ScreenGui("Ascenseur", 12)
	screen.Enabled = false
	screen.Parent = player:WaitForChild("PlayerGui")
	gui = screen
	local inset = GuiService:GetGuiInset().Y
	local size = Vector2.new(math.min(460, viewport.X - 40), math.min(520, viewport.Y - inset - 40))
	local win = UI.Window(screen, {
		Size = size,
		Title = "Лифт",
		Header = "blue",
		TitleWidth = math.min(300, size.X - 120),
		Position = UDim2.new(0.5, 0, 0.5, inset / 2),
	})
	local corps = win.Corps
	listWidth = math.max(160, win.Width - 5 - 16 - 14) -- корпус окна минус поля и полоса прокрутки
	local barH = rowHeight()
	local bar = Instance.new("Frame")
	bar.Name = "Navigation"
	bar.BackgroundTransparency = 1
	bar.Size = UDim2.new(1, -16 - 14, 0, barH)
	bar.Position = UDim2.fromOffset(8, 8)
	bar.ZIndex = 5
	bar.Parent = corps
	local barLayout = Instance.new("UIListLayout")
	barLayout.FillDirection = Enum.FillDirection.Horizontal
	barLayout.Padding = UDim.new(0, 6)
	barLayout.SortOrder = Enum.SortOrder.LayoutOrder
	barLayout.VerticalAlignment = Enum.VerticalAlignment.Center
	barLayout.Parent = bar
	nav = bar
	local scroll = Instance.new("ScrollingFrame")
	scroll.Name = "Etages"
	scroll.BackgroundTransparency = 1
	scroll.BorderSizePixel = 0
	scroll.Size = UDim2.new(1, -16, 1, -16 - barH - 8)
	scroll.Position = UDim2.fromOffset(8, 8 + barH + 8)
	scroll.ScrollBarThickness = 6
	scroll.ZIndex = 5
	scroll.Parent = corps
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 6)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.Parent = scroll
	list = scroll
	menu = Motion.Window(screen, win.Fenetre, { Keep = { Toasts = true, Ascenseur = true, LiftFade = true } })
end

function ElevatorController.Open(plotIndex: number)
	build()
	plotOpen = plotIndex
	if versionConn then
		versionConn:Disconnect()
		versionConn = nil
	end
	local tower = TowerController.TowerOf(plotIndex)
	if tower then
		versionConn = tower:GetAttributeChangedSignal("Version"):Connect(function()
			if menu and menu.IsOpen and plotOpen == plotIndex then
				fill(plotIndex)
			end
		end)
	end
	-- страница своего этажа (в холле — первая)
	local here = if tower then myIndex(tower) else nil
	page = if here and here > 0 then math.ceil(here / PAGE) else 1
	menu.Open()
	task.defer(fill, plotIndex) -- размер списка известен после открытия
end

function ElevatorController.Init()
	Remotes.Get(Remotes.Names.OpenWindow).OnClientEvent:Connect(function(name, plotIndex)
		if name == "Elevator" and type(plotIndex) == "number" then
			ElevatorController.Open(plotIndex)
		end
	end)
	Remotes.Get(Remotes.Names.ElevatorResult).OnClientEvent:Connect(function(result)
		if type(result) == "table" and not result.ok and type(result.reason) == "string" then
			fadeToken += 1
			if fade then
				fade.BackgroundTransparency = 1
			end
			NotifyController.Show(result.reason, "Stop")
		end
	end)
end

return ElevatorController

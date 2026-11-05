-- Окно «Защита» и расстановка (D37, D46, Stud-UI). Вкладка «Защита»: пять устройств — цена для своего музея (доля
-- цены взлома; у капкана цена не утверждена — купить нельзя), сколько куплено, что стоит; «Купить» и «Поставить» —
-- только в подготовку. Ловушка, робот и капкан ставятся свободно: полупрозрачный образец следует за курсором или
-- касанием по полу своего зала, зелёный — можно, красный — нельзя с причиной (Shared/DefenseRules — те же правила, что
-- на сервере); «Поставить» на панели внизу или ЛКМ. Дверь — на вход, лазер — на одно из размеченных мест прохода.
-- Вкладка «Взлом»: устройства взлома для музеев уровней 1–10, покупка днём. Всё проверяет сервер (DefenseAction).
-- Кнопка «Защита» в HUD под «Инвентарём». Зависит от Shared/StudUI, Shared/DefenseRules, Shared/GameTime,
-- Shared/NumberFormat, Remotes, Config/GameConfig, Config/UITokens.

local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local DefenseRules = require(Shared:WaitForChild("DefenseRules"))
local GameConfig = require(Config:WaitForChild("GameConfig"))
local GameTime = require(Shared:WaitForChild("GameTime"))
local NumberFormat = require(Shared:WaitForChild("NumberFormat"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Config:WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local MenuHud = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("MenuHud"))

local T = UITokens.Defense
local cfg = GameConfig.Defense
local player = Players.LocalPlayer

local DefenseController = {}

local state: any = { owned = {}, hacks = {}, installed = {}, level = 1, max = 1 }
local tab = "Defense" -- "Defense" | "Hack"
local gui: ScreenGui
local win: any
local menu: any
local list: ScrollingFrame
local info: TextLabel
local tabButtons: { [string]: GuiButton } = {}

-- Расстановка
local placing: string? = nil
local ghost: BasePart? = nil
local ghostSpot: Vector3? = nil
local ghostReason: string? = "Наведите на пол своего зала"
local bar: Frame
local barText: TextLabel
local placeButton: GuiButton
local pointer: Vector2? = nil -- касание (экранные координаты без вставки GUI), за которым идёт образец
local pointerTouch: InputObject? = nil
-- Постаменты и сундук для localLists не двигаются: на время расстановки считаются один раз (образец обновляется
-- каждый кадр, а FindFirstChild с поиском по всему музею на слабом телефоне заметен).
local fixedLists: { plot: Model, origin: CFrame, showcases: { Vector3 }, chest: Vector3 }? = nil
local counter: TextLabel

local function currentPhase(): string
	return GameTime.At(GameTime.Now()).phase
end

local function send(...)
	Remotes.Get(Remotes.Names.DefenseAction):FireServer(...)
end

local function myPlot(): Model?
	local plots = workspace:FindFirstChild("World") and workspace.World:FindFirstChild("Plots")
	for _, plot in if plots then plots:GetChildren() else {} do
		if plot:GetAttribute("OwnerUserId") == player.UserId then
			return plot :: Model
		end
	end
	return nil
end

local function money(n: number): string
	return "$" .. NumberFormat.Short(n)
end

local function clearList()
	for _, child in list:GetChildren() do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
end

local function row(order: number, title: string, details: string): Frame
	local frame = UI.InsetBox(list, { Name = "Ligne", Size = UDim2.fromOffset(T.Row.X, T.Row.Y), LayoutOrder = order })
	UI.Text(frame, title, {
		Name = "Nom",
		Size = UDim2.fromOffset(T.TextWidth, 34),
		Position = UDim2.fromOffset(18, 28),
		AnchorPoint = Vector2.new(0, 0.5),
		AlignX = Enum.TextXAlignment.Left,
		TextSize = T.NameText,
		ZIndex = 5,
	})
	UI.Text(frame, details, {
		Name = "Infos",
		Font = "Bold",
		Size = UDim2.fromOffset(T.TextWidth, 28),
		Position = UDim2.fromOffset(18, 64),
		AnchorPoint = Vector2.new(0, 0.5),
		AlignX = Enum.TextXAlignment.Left,
		Max = T.InfoText,
		Min = 12,
		Color = UI.Colors.Secondary,
		Rich = true,
		ZIndex = 5,
	})
	return frame
end

local function button(parent: Instance, text: string, theme: string, x: number, enabled: boolean, onClick: () -> ())
	local b = UI.Button(parent, {
		Name = "Bouton",
		Theme = theme,
		Size = T.Button,
		Position = UDim2.new(1, x, 0.5, 0),
		Text = text,
		TextSize = 22,
		ZIndex = 6,
	})
	UI.SetDisabled(b, not enabled)
	Motion.BindButton(b, 1.05, nil, function()
		if enabled then
			onClick()
		else
			Motion.Shake(b)
		end
	end)
end

local startPlacing: (string) -> ()

local function renderDefense()
	local phase = currentPhase()
	local prep = phase == "Preparation"
	for order, kind in DefenseRules.Types do
		local price = DefenseRules.Price(cfg, kind, state.level)
		local owned = state.owned[kind] or 0
		local installed = state.installed[kind]
		local where = ""
		if installed then
			local spot = installed.spot
			where = if typeof(spot) == "Vector3"
				then ' · <font color="#60E87A">стоит в зале</font>'
				else (' · <font color="#60E87A">стоит: %s</font>'):format(
					T.SpotNames[spot] or tostring(spot)
				)
		end
		local priceText = if price then money(price) else "цена не утверждена"
		local frame =
			row(order, DefenseRules.Names[kind], ("%s · куплено: %d%s"):format(priceText, owned, where))
		-- «Купить» левее мест расстановки: у лазера их два, у остальных — одна кнопка
		local buyX = if kind == "Laser" then -415 else -255
		button(frame, "Купить", "cash", buyX, prep and price ~= nil, function()
			send("BuyDefense", kind)
		end)
		if installed then
			button(frame, "Снять", "red", -95, prep, function()
				send("Remove", kind)
			end)
		elseif kind == "Laser" then
			local spots = DefenseRules.FixedSpots(cfg, kind) or {}
			for i, spot in spots do
				button(frame, T.SpotButtons[spot] or spot, "green", -95 - (i - 1) * 160, prep and owned > 0, function()
					send("Install", kind, spot)
				end)
			end
		elseif kind == "Door" then
			button(frame, "На вход", "green", -95, prep and owned > 0, function()
				send("Install", kind, "Entrance")
			end)
		else
			button(frame, "Поставить", "green", -95, prep and owned > 0, function()
				startPlacing(kind)
			end)
		end
	end
end

local function renderHack()
	local day = currentPhase() == "Day"
	for level = 1, #cfg.HackPrices do
		local have = state.hacks["L" .. level] or 0
		local frame = row(
			level,
			("Взлом музея ур. %d"):format(level),
			("%s · есть: %d"):format(money(DefenseRules.HackPrice(cfg, level)), have)
		)
		button(frame, "Купить", "cash", -95, day, function()
			send("BuyHack", level)
		end)
	end
end

local function render()
	if not win then
		return
	end
	clearList()
	local count = 0
	for _ in state.installed do
		count += 1
	end
	local phase = currentPhase()
	local hint = if tab == "Hack"
		then (if phase == "Day"
			then "Устройства взлома покупают заранее, днём"
			else "Сейчас не день: купить взлом нельзя")
		elseif phase == "Preparation" then "Подготовка: покупайте и ставьте защиту"
		else "Защиту покупают и ставят только в подготовку к Судной ночи"
	info.Text = hint
	counter.Text = ('Устройств: <font color="%s">%d/%d</font>'):format(
		UI.Colors.HighlightHex,
		count,
		state.max
	)
	for name, b in tabButtons do
		UI.Recolor(b, if name == tab then "purple" else "gray")
	end
	if tab == "Defense" then
		renderDefense()
	else
		renderHack()
	end
end

-- ── Свободная расстановка ─────────────────────────────────────────────────────────────────────────────────────

local function resetBar(text: string)
	ghostSpot = nil
	ghostReason = text
	barText.Text = text
	barText.TextColor3 = UI.Colors.Danger
	UI.SetDisabled(placeButton, true)
end

local function stopPlacing()
	placing = nil
	fixedLists = nil
	pointer = nil
	pointerTouch = nil
	if ghost then
		ghost:Destroy()
		ghost = nil
	end
	resetBar("Наведите на пол своего зала")
	bar.Visible = false
	player:SetAttribute("PlacingDefense", nil)
end

-- Указатель мыши над панелью расстановки: образец не двигается, ЛКМ не ставит. at — координаты мыши во вьюпорте
-- (GetMouseLocation, со вставкой GUI сверху); GetGuiObjectsAtPosition ждёт координаты без вставки.
local function overInterface(at: Vector2): boolean
	at -= GuiService:GetGuiInset()
	local playerGui = player:FindFirstChildOfClass("PlayerGui")
	if not playerGui then
		return false
	end
	for _, object in playerGui:GetGuiObjectsAtPosition(at.X, at.Y) do
		if object:IsDescendantOf(bar) then
			return true
		end
	end
	return false
end

local function localLists(plot: Model, origin: CFrame): ({ Vector3 }, Vector3, { Vector3 })
	if not fixedLists or fixedLists.plot ~= plot or fixedLists.origin ~= origin then
		local showcases = {}
		local folder = plot:FindFirstChild("Showcases")
		for _, showcase in if folder then folder:GetChildren() else {} do
			if showcase:IsA("BasePart") then
				table.insert(showcases, origin:PointToObjectSpace(showcase.Position))
			end
		end
		local chest = plot:FindFirstChild("Chest", true)
		local chestLocal = if chest and chest:IsA("BasePart")
			then origin:PointToObjectSpace(chest.Position)
			else Vector3.zero
		fixedLists = { plot = plot, origin = origin, showcases = showcases, chest = chestLocal }
	end
	local lists = fixedLists :: { plot: Model, origin: CFrame, showcases: { Vector3 }, chest: Vector3 }
	local showcases, chestLocal = lists.showcases, lists.chest
	local others = {}
	for kind, device in state.installed do
		if kind ~= placing and typeof(device.spot) == "Vector3" then
			table.insert(others, device.spot)
		end
	end
	return showcases, chestLocal, others
end

local function updateGhost()
	local kind = placing
	local plot = myPlot()
	if not kind or not ghost or not plot then
		return
	end
	local origin = plot:GetAttribute("FloorOrigin")
	if typeof(origin) ~= "CFrame" then
		return
	end
	local camera = workspace.CurrentCamera
	local ray
	if pointer then
		ray = camera:ScreenPointToRay(pointer.X, pointer.Y) -- касание: координаты без вставки GUI
	else
		local mouse = UserInputService:GetMouseLocation() -- мышь: координаты вьюпорта (со вставкой)
		if overInterface(mouse) then
			return
		end
		ray = camera:ViewportPointToRay(mouse.X, mouse.Y)
	end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { ghost, player.Character :: Instance }
	local hit = workspace:Raycast(ray.Origin, ray.Direction * 300, params)
	if not hit then
		resetBar("Наведите на пол своего зала")
		return
	end
	local spot = origin:PointToObjectSpace(hit.Position)
	spot = Vector3.new(spot.X, 0, spot.Z)
	local showcases, chest, others = localLists(plot, origin)
	ghostReason = DefenseRules.CheckFreeSpot(cfg, spot, showcases, chest, others)
	ghostSpot = spot
	local size = ghost.Size
	ghost.CFrame = origin * CFrame.new(spot + Vector3.new(0, size.Y / 2, 0))
	ghost.Color = if ghostReason then T.GhostBad else T.GhostOk
	barText.Text = ghostReason or ("%s: можно поставить здесь"):format(DefenseRules.Names[kind])
	barText.TextColor3 = if ghostReason then UI.Colors.Danger else UI.Colors.Positive
	UI.SetDisabled(placeButton, ghostReason ~= nil)
end

local function confirmPlacing()
	if placing and ghostSpot and not ghostReason then
		send("Install", placing, ghostSpot)
		stopPlacing()
	end
end

startPlacing = function(kind: string)
	menu.Close()
	stopPlacing()
	placing = kind
	local part = Instance.new("Part")
	part.Name = "ApercuDefense"
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	part.Material = Enum.Material.SmoothPlastic
	part.Transparency = T.GhostTransparency
	part.Size = T.Ghost[kind]
	part.Parent = workspace
	ghost = part
	resetBar("Наведите на пол своего зала")
	bar.Visible = true
	player:SetAttribute("PlacingDefense", true)
	updateGhost()
end

local function buildBar()
	local hud = UI.ScreenGui("DefensePose", 13, { Menu = false })
	hud.Parent = player:WaitForChild("PlayerGui")
	bar = Instance.new("Frame")
	bar.Name = "Barre"
	bar.BackgroundTransparency = 1
	bar.Size = UDim2.fromOffset(T.Bar.X, T.Bar.Y)
	bar.Position = UDim2.new(0.5, 0, 1, -16)
	bar.AnchorPoint = Vector2.new(0.5, 1)
	bar.Visible = false
	bar.Parent = hud
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = bar
	Motion.BindResponsive(scale)
	local box = UI.InsetBox(bar, { Size = UDim2.fromScale(1, 1), Transparency = 0.15 })
	barText = UI.Text(box, "", {
		Name = "Aide",
		Font = "Bold",
		Size = UDim2.new(1, -24, 0, 34),
		Position = UDim2.new(0.5, 0, 0, 26),
		Max = 24,
		Min = UITokens.Inventory.MinText,
		ZIndex = 6,
	})
	placeButton = UI.Button(box, {
		Name = "Poser",
		Theme = "green",
		Size = T.Button,
		Position = UDim2.new(0.5, -90, 1, -40),
		Text = "Поставить",
		TextSize = 22,
		ZIndex = 6,
	})
	Motion.BindButton(placeButton, 1.05, nil, confirmPlacing)
	local cancel = UI.Button(box, {
		Name = "Annuler",
		Theme = "gray",
		Size = T.Button,
		Position = UDim2.new(0.5, 90, 1, -40),
		Text = "Отмена",
		TextSize = 22,
		ZIndex = 6,
	})
	Motion.BindButton(cancel, 1.05, nil, stopPlacing)
end

local function build()
	gui = UI.ScreenGui("Defense", 12)
	gui.Enabled = false
	gui.Parent = player:WaitForChild("PlayerGui")
	win = UI.Window(gui, { Size = T.Window, Title = "Защита музея", Header = T.Header, TitleWidth = 620 })
	local corps = win.Corps
	local W = win.Width - 5
	info = UI.Text(corps, "", {
		Name = "Etat",
		Font = "Bold",
		Size = UDim2.fromOffset(W - 380, 26),
		Position = UDim2.fromOffset(18, 22),
		AnchorPoint = Vector2.new(0, 0.5),
		AlignX = Enum.TextXAlignment.Left,
		TextSize = T.InfoText,
		ZIndex = 4,
	})
	info.TextWrapped = true
	counter = UI.Text(corps, "", {
		Name = "Compteur",
		Font = "Bold",
		Size = UDim2.fromOffset(W - 380, 26),
		Position = UDim2.fromOffset(18, 48),
		AnchorPoint = Vector2.new(0, 0.5),
		AlignX = Enum.TextXAlignment.Left,
		TextSize = T.InfoText,
		Rich = true,
		ZIndex = 4,
	})
	for i, entry in { { "Defense", "Защита" }, { "Hack", "Взлом" } } do
		local b = UI.Button(corps, {
			Name = "Onglet",
			Style = "Chunky",
			Theme = "gray",
			Size = Vector2.new(160, 48),
			Position = UDim2.new(1, -(18 + 80 + (2 - i) * 170), 0, 34),
			Text = entry[2],
			TextSize = 22,
			ZIndex = 4,
		})
		Motion.BindButton(b, 1.05, nil, function()
			tab = entry[1]
			render()
		end)
		tabButtons[entry[1]] = b
	end
	list = UI.ScrollList(corps, {
		Name = "Liste",
		Size = UDim2.fromOffset(W - 8, corps.Size.Y.Offset - 80),
		Position = UDim2.fromOffset(4, 70),
		Padding = T.RowGap,
		PadTop = 6,
		PadLeft = 26,
		ZIndex = 3,
	})
	-- крестик «Fermer» привязывает сам Motion.Window (второй BindButton давал двойные твины и Close)
	menu = Motion.Window(gui, win.Fenetre, { Keep = { Toasts = true, Defense = true } })
end

-- Кнопка «Защита» в общей колонке HUD (UI/MenuHud), под «Инвентарём».
local function buildHud()
	MenuHud.Add("Defense", "Защита", "purple", 2, function()
		if menu.IsOpen then
			menu.Close()
		else
			stopPlacing()
			render()
			menu.Open()
		end
	end)
end

function DefenseController.Init()
	build()
	buildBar()
	buildHud()
	Remotes.Get(Remotes.Names.DefenseChanged).OnClientEvent:Connect(function(payload)
		if type(payload) == "table" then
			state = payload
			if menu.IsOpen then
				render()
			end
		end
	end)
	ReplicatedStorage:GetAttributeChangedSignal("Phase"):Connect(function()
		if placing and currentPhase() ~= "Preparation" then
			stopPlacing()
		end
		if menu.IsOpen then
			render()
		end
	end)
	UserInputService.InputBegan:Connect(function(input, processed)
		if not placing or processed then
			return
		end
		if input.UserInputType == Enum.UserInputType.MouseButton1 then
			if not overInterface(UserInputService:GetMouseLocation()) then
				confirmPlacing()
			end
		elseif input.UserInputType == Enum.UserInputType.Touch and pointerTouch == nil then
			-- касание по миру (не по кнопкам и джойстику): образец идёт за этим пальцем
			pointerTouch = input
			pointer = Vector2.new(input.Position.X, input.Position.Y)
		end
	end)
	UserInputService.InputChanged:Connect(function(input)
		if placing and input == pointerTouch then
			pointer = Vector2.new(input.Position.X, input.Position.Y)
		end
	end)
	UserInputService.InputEnded:Connect(function(input)
		if input == pointerTouch then
			pointerTouch = nil -- образец остаётся, где отпустили; «Поставить» — на панели
		end
	end)
	RunService.RenderStepped:Connect(function()
		if placing then
			updateGhost()
		end
	end)
end

return DefenseController

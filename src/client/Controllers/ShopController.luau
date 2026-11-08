-- Окно «Магазин» Ловибумов (D55, Stud-UI D20: красная кнопка и розовая шапка — магазин). Сверху — уровни 1–10
-- (Ловибум уровня N ловит только существ босса N), ниже три карточки: Бум, Турбо, Мега — вращающаяся 3D-модель
-- (World/LovibumModel), бонус к шансу, запас, цена, количество (−, число, +; касание числа: 1 → 5 → 10) и «Купить».
-- Покупку проверяет и проводит сервер (ShopAction → ShopService); окно только показывает его ответ (LovibumsChanged).
-- Кнопки «Магазин» нет, пока не пройдено обучение; во время поимки (атрибут Catching) окно не открывается и
-- закрывается. Цены не утверждены владельцем: без цен — «Скоро», в Studio — тестовые с пометкой.
-- Адаптивно, как «Инвентарь»: размер окна — по экрану (ниже кнопок Roblox), на телефоне масштаб не меньше PhoneScale,
-- кнопки на касание не ниже MinTouch px; в Studio экран подменяют атрибуты игрока DevViewport и DevTouch.
-- Зависит от Shared/StudUI, Shared/NumberFormat, Remotes, Config/GameConfig, Config/UITokens, UI/MenuHud, UI/HudIcons,
-- World/LovibumModel.

local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local NumberFormat = require(Shared:WaitForChild("NumberFormat"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Config:WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local Client = script.Parent.Parent
local HudIcons = require(Client:WaitForChild("UI"):WaitForChild("HudIcons"))
local MenuHud = require(Client:WaitForChild("UI"):WaitForChild("MenuHud"))
local LovibumModel = require(Client:WaitForChild("World"):WaitForChild("LovibumModel"))

local T = UITokens.Shop
local Catch = GameConfig.Catch
local player = Players.LocalPlayer

local ShopController = {}

type Profile = { key: string, window: Vector2, boost: number, button: number, touch: boolean, compact: boolean }
type Card = {
	stock: TextLabel,
	price: TextLabel,
	qty: TextLabel,
	buy: GuiButton,
	view: ViewportFrame,
	camera: Camera,
	center: Vector3,
	distance: number,
}

local state: any = { lovibums = {}, coins = 0, prices = nil, open = false, test = false }
local level = 1
local qty: { [string]: number } = { Boom = 1, Turbo = 1, Mega = 1 }
local profile: Profile
local gui: ScreenGui? = nil
local win: any
local menu: any
local tabs: { GuiButton } = {}
local subtitle: TextLabel
local footer: TextLabel
local cards: { [string]: Card } = {}
local hudButton: GuiButton? = nil
local spin = 0

local function money(n: number): string
	return "$" .. NumberFormat.Short(n)
end

local function stockOf(lvl: number, kind: string): number
	local byKind = state.lovibums and state.lovibums["L" .. lvl]
	return byKind and byKind[kind] or 0
end

local function priceOf(lvl: number, kind: string): number?
	local byLevel = state.prices and (state.prices[lvl] or state.prices[tostring(lvl)])
	return byLevel and byLevel[kind] or nil
end

-- Раскладка под текущий экран (как у «Инвентаря»).
local function measure(): Profile
	local fake = GameConfig.DevMode and player:GetAttribute("DevViewport")
	local inset = GuiService:GetGuiInset().Y
	local viewport = if typeof(fake) == "Vector2" then fake else workspace.CurrentCamera.ViewportSize
	local screen = math.clamp(
		math.min(viewport.X / Motion.REFERENCE.X, viewport.Y / Motion.REFERENCE.Y),
		Motion.MIN_SCALE or 0.52,
		Motion.MAX_SCALE or 1.18
	)
	local touch = if typeof(fake) == "Vector2"
		then player:GetAttribute("DevTouch") == true
		else UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
	local scale = if touch then math.max(screen, T.PhoneScale) else screen
	local w = math.clamp(math.floor((viewport.X - 2 * T.Margin) / scale), T.MinWindow.X, T.Window.X)
	local h = math.clamp(math.floor((viewport.Y - inset - 2 * T.Margin) / scale), T.MinWindow.Y, T.Window.Y)
	local button = if touch then math.max(T.Button, math.ceil(T.MinTouch / scale)) else T.Button
	return {
		key = ("%dx%d:%d"):format(w, h, button),
		window = Vector2.new(w, h),
		boost = scale / Motion.ScreenScale(),
		button = button,
		touch = touch,
		compact = h < 470,
	}
end

local function send(...)
	Remotes.Get(Remotes.Names.ShopAction):FireServer(...)
end

local render: () -> ()

-- 3D-превью Ловибума: модель во ViewportFrame, камера обходит её по кругу (модель не двигается).
local function preview(parent: GuiObject, kind: string, z: number): (ViewportFrame, Camera, Vector3, number)
	local view = Instance.new("ViewportFrame")
	view.Name = "Apercu"
	view.BackgroundTransparency = 1
	view.Size = UDim2.fromScale(1, 1)
	view.Ambient = Color3.fromRGB(170, 170, 180)
	view.LightColor = Color3.new(1, 1, 1)
	view.LightDirection = Vector3.new(-0.5, -1, -0.7)
	view.ZIndex = z
	view.Parent = parent
	local model = LovibumModel.Build(kind)
	LovibumModel.Place(model, CFrame.new(), 0, 1, true)
	model.Parent = view
	local size, center = LovibumModel.Bounds(kind)
	local camera = Instance.new("Camera")
	camera.FieldOfView = 32
	camera.Parent = view
	view.CurrentCamera = camera
	local distance = size.Magnitude / 2 / math.sin(math.rad(camera.FieldOfView / 2)) * 1.08
	return view, camera, center, distance
end

local function placeCamera(card: Card, angle: number)
	local dir = Vector3.new(math.sin(angle), 0.42, math.cos(angle)).Unit -- лицо Ловибума смотрит в +Z
	card.camera.CFrame = CFrame.lookAt(card.center + dir * card.distance, card.center)
end

local function setQty(kind: string, value: number)
	qty[kind] = math.clamp(math.floor(value), 1, Catch.MaxBuy)
	render()
end

local function card(parent: Instance, kind: string, x: number, width: number, height: number)
	local b = profile.button
	local pad = T.Pad
	local box = UI.InsetBox(parent, {
		Name = "Carte_" .. kind,
		Size = UDim2.fromOffset(width, height),
		Position = UDim2.fromOffset(x, 0),
		ZIndex = 4,
	})
	local textTop = height - pad - b - 8 - 2 * (T.InfoText + 4) - (T.NameText + 6)
	local stage = Instance.new("Frame")
	stage.Name = "Scene"
	stage.BackgroundTransparency = 1
	stage.Size = UDim2.new(1, -2 * pad, 0, textTop - pad)
	stage.Position = UDim2.fromOffset(pad, pad)
	stage.ZIndex = 5
	stage.Parent = box
	UI.Sunburst(stage, math.min(width, textTop) * 0.9).ZIndex = 5
	local view, camera, center, distance = preview(stage, kind, 6)
	local title = UI.Text(
		box,
		('%s  <font size="%d" color="#FFFFFF">шанс ×%s</font>'):format(
			Catch.Names[kind],
			T.InfoText,
			tostring(Catch.Bonus[kind])
		),
		{
			Name = "Nom",
			Size = UDim2.new(1, -2 * pad, 0, T.NameText + 6),
			Position = UDim2.fromOffset(pad, textTop),
			AnchorPoint = Vector2.zero,
			AlignX = Enum.TextXAlignment.Left,
			TextSize = T.NameText,
			Color = T.KindColor[kind],
			Rich = true,
			ZIndex = 7,
		}
	)
	title.Name = "Nom"
	local function info(name: string, y: number): TextLabel
		return UI.Text(box, "", {
			Name = name,
			Font = "Bold",
			Size = UDim2.new(1, -2 * pad, 0, T.InfoText + 4),
			Position = UDim2.fromOffset(pad, y),
			AnchorPoint = Vector2.zero,
			AlignX = Enum.TextXAlignment.Left,
			Max = T.InfoText,
			Min = 12,
			Rich = true,
			ZIndex = 7,
		})
	end
	local stockText = info("Stock", textTop + T.NameText + 6)
	local priceText = info("Prix", textTop + T.NameText + 6 + T.InfoText + 4)
	local rowY = height - pad - b / 2
	local minus = UI.Button(box, {
		Name = "Moins",
		Style = "Chunky",
		Theme = "gray",
		Size = Vector2.new(b, b),
		Position = UDim2.fromOffset(pad + b / 2, rowY),
		Text = "−",
		TextSize = 28,
		ZIndex = 7,
	})
	Motion.BindButton(minus, 1.05, nil, function()
		setQty(kind, qty[kind] - 1)
	end)
	local value = Instance.new("TextButton")
	value.Name = "Quantite"
	value.BackgroundTransparency = 1
	value.Text = ""
	value.Size = UDim2.fromOffset(T.QtyValue, b)
	value.Position = UDim2.fromOffset(pad + b + 4, rowY - b / 2)
	value.ZIndex = 7
	value.Parent = box
	local qtyText = UI.Text(value, "1", { Name = "Texte", TextSize = 26, ZIndex = 8 })
	Motion.BindButton(value, 1.05, nil, function()
		-- быстрый выбор: 1 → 5 → 10 → 1
		local presets = T.Presets
		local nextValue = presets[1]
		for i, p in presets do
			if qty[kind] < p or (qty[kind] == p and i < #presets) then
				nextValue = if qty[kind] == p then presets[i + 1] else p
				break
			end
		end
		setQty(kind, nextValue)
	end)
	local plus = UI.Button(box, {
		Name = "Plus",
		Style = "Chunky",
		Theme = "gray",
		Size = Vector2.new(b, b),
		Position = UDim2.fromOffset(pad + b * 1.5 + T.QtyValue + 8, rowY),
		Text = "+",
		TextSize = 28,
		ZIndex = 7,
	})
	Motion.BindButton(plus, 1.05, nil, function()
		setQty(kind, qty[kind] + 1)
	end)
	local buyWidth = math.max(width - (2 * pad + 2 * b + T.QtyValue + 20), 96)
	local buy = UI.Button(box, {
		Name = "Acheter",
		Theme = "green",
		Size = Vector2.new(buyWidth, b),
		Position = UDim2.new(1, -pad - buyWidth / 2, 0, rowY),
		Text = "Купить",
		TextSize = 24,
		ZIndex = 7,
	})
	Motion.BindButton(buy, 1.05, nil, function()
		local price = priceOf(level, kind)
		if not state.open or not price or state.coins < price * qty[kind] then
			Motion.Shake(buy)
			return
		end
		send("Buy", level, kind, qty[kind])
	end)
	cards[kind] = {
		stock = stockText,
		price = priceText,
		qty = qtyText,
		buy = buy,
		view = view,
		camera = camera,
		center = center,
		distance = distance,
	}
	placeCamera(cards[kind], 0)
end

local function build()
	profile = measure()
	if gui then
		if menu and menu.Destroy then
			menu.Destroy()
		end
		gui:Destroy()
	end
	local screen = UI.ScreenGui("Magasin", 12)
	screen.Enabled = false
	screen.Parent = player:WaitForChild("PlayerGui")
	gui = screen
	local inset = GuiService:GetGuiInset().Y
	win = UI.Window(screen, {
		Size = profile.window,
		Title = "Магазин Ловибумов",
		Header = T.Header,
		Icon = HudIcons.Get("Shop"),
		TitleWidth = math.min(620, profile.window.X - 180),
		Position = UDim2.new(0.5, 0, 0.5, inset / 2),
	})
	local corps = win.Corps
	local W = win.Width - 5
	local H = corps.Size.Y.Offset
	local pad = T.Pad
	local b = profile.button
	-- уровни 1–10 в ряд
	tabs = {}
	local tabW = math.floor((W - 2 * pad - 9 * 6) / 10)
	for lvl = 1, Catch.Levels do
		local tab = UI.Button(corps, {
			Name = "Niveau" .. lvl,
			Style = "Chunky",
			Theme = "gray",
			Size = Vector2.new(tabW, b),
			Position = UDim2.fromOffset(pad + (lvl - 1) * (tabW + 6) + tabW / 2, pad + b / 2),
			Text = tostring(lvl),
			TextSize = 26,
			ZIndex = 5,
		})
		Motion.BindButton(tab, 1.05, nil, function()
			level = lvl
			render()
		end)
		tabs[lvl] = tab
	end
	local subY = pad + b + 6
	subtitle = UI.Text(corps, "", {
		Name = "Niveau",
		Font = "Bold",
		Size = UDim2.fromOffset(W - 2 * pad, T.InfoText + 8),
		Position = UDim2.fromOffset(pad, subY),
		AnchorPoint = Vector2.zero,
		AlignX = Enum.TextXAlignment.Left,
		Max = T.InfoText,
		Min = 12,
		Rich = true,
		ZIndex = 5,
	})
	local footY = H - pad - (T.InfoText + 4)
	footer = UI.Text(corps, "", {
		Name = "Pied",
		Font = "Bold",
		Size = UDim2.fromOffset(W - 2 * pad, T.InfoText + 4),
		Position = UDim2.fromOffset(pad, footY),
		AnchorPoint = Vector2.zero,
		AlignX = Enum.TextXAlignment.Left,
		Max = T.InfoText,
		Min = 12,
		Rich = true,
		ZIndex = 5,
	})
	local cardsTop = subY + T.InfoText + 14
	local cardH = footY - 8 - cardsTop
	local row = Instance.new("Frame")
	row.Name = "Cartes"
	row.BackgroundTransparency = 1
	row.Size = UDim2.fromOffset(W - 2 * pad, cardH)
	row.Position = UDim2.fromOffset(pad, cardsTop)
	row.ZIndex = 4
	row.Parent = corps
	local gap = 12
	local cardW = math.floor((W - 2 * pad - 2 * gap) / 3)
	cards = {}
	for i, kind in Catch.Kinds do
		card(row, kind, (i - 1) * (cardW + gap), cardW, cardH)
	end
	-- крестик «Fermer» привязывает сам Motion.Window
	menu = Motion.Window(screen, win.Fenetre, { Keep = { Toasts = true, Magasin = true }, Size = profile.boost })
	Motion.SpinSunbursts(screen)
end

render = function()
	if not menu then
		return
	end
	for lvl, tab in tabs do
		UI.Recolor(tab, if lvl == level then "red" else "gray")
	end
	local zone = GameConfig.Zones[level]
	subtitle.Text = ('Уровень <font color="%s">%d — %s</font>: Ловибумы ловят только существ босса «%s»'):format(
		UI.Colors.HighlightHex,
		level,
		zone.name,
		zone.boss
	)
	for _, kind in Catch.Kinds do
		local c = cards[kind]
		local price = priceOf(level, kind)
		local n = qty[kind]
		c.qty.Text = tostring(n)
		c.stock.Text = ('Есть: <font color="%s">%s</font>'):format(
			UI.Colors.HighlightHex,
			NumberFormat.Short(stockOf(level, kind))
		)
		if price then
			local total = price * n
			local afford = state.coins >= total
			c.price.Text = ('Цена: %s · Итого: <font color="%s">%s</font>'):format(
				money(price),
				if afford then "#60E87A" else "#FF6A6A",
				money(total)
			)
			UI.SetButtonText(c.buy, "Купить")
			UI.SetDisabled(c.buy, not afford or not state.open)
		else
			c.price.Text = "Цена: пока не утверждена"
			UI.SetButtonText(c.buy, "Скоро")
			UI.SetDisabled(c.buy, true)
		end
	end
	footer.Text = ('У вас: <font color="#60E87A">%s</font>%s'):format(
		money(state.coins or 0),
		if not state.prices
			then "   ·   Продажа начнётся, когда будут утверждены цены"
			elseif state.test then '   ·   <font color="#FFD23F">тестовые цены (Studio)</font>'
			else ""
	)
end

local function isOpen(): boolean
	return menu ~= nil and menu.IsOpen
end

-- Открыть магазин (кнопка HUD). Во время поимки и обучения — нельзя (сервер всё равно откажет в покупке).
function ShopController.Open()
	if player:GetAttribute("Catching") then
		return
	end
	if not state.open then
		return
	end
	if not menu or measure().key ~= profile.key then
		build()
	end
	render()
	menu.Open()
	send("Open")
end

local function toggle()
	if isOpen() then
		menu.Close()
	else
		ShopController.Open()
	end
end

local function updateHud()
	if hudButton and hudButton.Parent then
		(hudButton.Parent :: GuiObject).Visible = state.open == true
	end
end

function ShopController.Init()
	-- Кнопка «Магазин» в колонке меню HUD v2 (третья, под «Защитой»); у ученика её нет до конца обучения.
	hudButton = MenuHud.Add("Shop", "Магазин", "red", 3, toggle, { icon = "Shop" })
	updateHud()
	Remotes.Get(Remotes.Names.LovibumsChanged).OnClientEvent:Connect(function(payload)
		if type(payload) ~= "table" then
			return
		end
		state = payload
		updateHud()
		if isOpen() then
			if not state.open then
				menu.Close()
			else
				render()
			end
		end
	end)
	player:GetAttributeChangedSignal("Coins"):Connect(function()
		local coins = player:GetAttribute("Coins")
		if type(coins) == "number" then
			state.coins = coins
			if isOpen() then
				render()
			end
		end
	end)
	player:GetAttributeChangedSignal("Catching"):Connect(function()
		if player:GetAttribute("Catching") and isOpen() then
			menu.Close()
		end
	end)
	-- превью медленно обходит Ловибумов, пока окно открыто
	RunService.RenderStepped:Connect(function(dt)
		if not isOpen() then
			return
		end
		spin += dt * T.Turn * 2 * math.pi
		for _, c in cards do
			placeCamera(c, spin)
		end
	end)
end

return ShopController

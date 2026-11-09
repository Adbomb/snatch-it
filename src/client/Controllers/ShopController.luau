-- Окно «Магазин» Ловибумов (D55, Stud-UI D20: красная кнопка и розовая шапка — магазин). Сверху — уровни 1–10
-- (Ловибум уровня N ловит только существ босса N), ниже три карточки: Бум, Турбо, Мега — вращающаяся 3D-модель
-- (World/LovibumModel), бонус к шансу, запас, цена, количество (−, число, +; касание числа: 1 → 5 → 10) и «Купить».
-- Покупку проверяет и проводит сервер (ShopAction → ShopService); окно только показывает его ответ (LovibumsChanged).
-- Кнопки «Магазин» нет, пока не пройдено обучение; во время поимки (атрибут Catching) окно не открывается и
-- закрывается. Цены боссов 1–3 утверждены (Config/Catch.Prices); уровень без утверждённой цены — «Скоро», в Studio
-- + DevMode — предварительная цена с пометкой «предварительно» в подвале.
-- Адаптивно, как «Инвентарь»: размер окна — по экрану (ниже кнопок Roblox), на телефоне масштаб не меньше PhoneScale,
-- кнопки на касание не ниже MinTouch px; в Studio экран подменяют атрибуты игрока DevViewport и DevTouch. Низкое или
-- узкое окно (телефон) — компактная раскладка «уровень → вид → количество»: три карточки-выбора вида (превью, запас,
-- цена; выбранная — салатовая рамка) и одна строка внизу: итог, «−», число, «+», «Купить» для выбранного вида.
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

type Profile = {
	key: string,
	window: Vector2,
	boost: number,
	button: number,
	touch: boolean,
	compact: boolean,
	qty: number, -- ширина числа в карточке ПК
}
type Card = {
	stock: TextLabel,
	price: TextLabel,
	qty: TextLabel?, -- у карточки ПК; на телефоне — общая строка (bar)
	buy: GuiButton?,
	select: GuiObject?, -- рамка выбора (телефон)
	view: ViewportFrame,
	camera: Camera,
	center: Vector3,
	distance: number,
}

local state: any = { lovibums = {}, coins = 0, prices = nil, open = false }
local waitingUntil = 0 -- после «Купить» — ждём ответа сервера (LovibumsChanged), повторное нажатие не шлём
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
local selected = "Boom" -- выбранный вид (телефон)
local bar: { qty: TextLabel, buy: GuiButton, total: TextLabel }? = nil
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
	-- карточка ПК вмещает «−», число, «+» и «Купить» не уже BuyMin (зазор не меньше 4); не влезает — число уже
	-- (QtyCompact); и так не влезает — компактная раскладка
	local row = math.floor((w - 5 - 2 * T.Pad - 2 * T.Gap) / 3) - 2 * T.Pad
	local qtyWidth = if row >= 2 * button + T.QtyValue + 12 + T.BuyMin then T.QtyValue else T.QtyCompact
	local fits = row >= 2 * button + qtyWidth + 12 + T.BuyMin
	return {
		key = ("%dx%d:%d"):format(w, h, button),
		window = Vector2.new(w, h),
		boost = scale / Motion.ScreenScale(),
		button = button,
		touch = touch,
		compact = h < T.CompactHeight or not fits,
		qty = qtyWidth,
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

-- Строка покупки: «−», число (касание: 1 → 5 → 10), «+», «Купить» (прижата к концу width, не уже BuyMin). kindOf —
-- вид, к которому она относится сейчас (у карточки ПК — свой, у строки телефона — выбранный).
local function buyRow(parent: Instance, kindOf: () -> string, x: number, rowY: number, width: number, qtyWidth: number)
	local b = profile.button
	local minus = UI.Button(parent, {
		Name = "Moins",
		Style = "Chunky",
		Theme = "gray",
		Size = Vector2.new(b, b),
		Position = UDim2.fromOffset(x + b / 2, rowY),
		Text = "−",
		TextSize = 28,
		ZIndex = 7,
	})
	Motion.BindButton(minus, 1.05, nil, function()
		setQty(kindOf(), qty[kindOf()] - 1)
	end)
	local value = Instance.new("TextButton")
	value.Name = "Quantite"
	value.BackgroundTransparency = 1
	value.Text = ""
	value.Size = UDim2.fromOffset(qtyWidth, b)
	value.Position = UDim2.fromOffset(x + b + 4, rowY - b / 2)
	value.ZIndex = 7
	value.Parent = parent
	local qtyText = UI.Text(value, "1", { Name = "Texte", TextSize = 26, ZIndex = 8 })
	Motion.BindButton(value, 1.05, nil, function()
		-- быстрый выбор: 1 → 5 → 10 → 1
		local kind = kindOf()
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
	local plus = UI.Button(parent, {
		Name = "Plus",
		Style = "Chunky",
		Theme = "gray",
		Size = Vector2.new(b, b),
		Position = UDim2.fromOffset(x + b * 1.5 + qtyWidth + 8, rowY),
		Text = "+",
		TextSize = 28,
		ZIndex = 7,
	})
	Motion.BindButton(plus, 1.05, nil, function()
		setQty(kindOf(), qty[kindOf()] + 1)
	end)
	local buyX = x + 2 * b + qtyWidth + 20
	local buyWidth = math.max(width - (buyX - x), T.BuyMin)
	local buy = UI.Button(parent, {
		Name = "Acheter",
		Theme = "green",
		Size = Vector2.new(buyWidth, b),
		Position = UDim2.fromOffset(x + width - buyWidth / 2, rowY),
		Text = "Купить",
		TextSize = 24,
		ZIndex = 7,
	})
	Motion.BindButton(buy, 1.05, nil, function()
		local kind = kindOf()
		local price = priceOf(level, kind)
		if not state.open or not price or state.coins < price * qty[kind] then
			Motion.Shake(buy)
			return
		end
		if os.clock() < waitingUntil then
			return -- прошлая покупка ещё не подтверждена сервером
		end
		waitingUntil = os.clock() + T.BuyWait
		send("Buy", level, kind, qty[kind])
	end)
	return qtyText, buy
end

-- Карточка вида. ПК: превью сверху во всю ширину, под ним название, запас, цена и строка покупки. Телефон: превью
-- слева, текст справа, вся карточка — кнопка выбора вида (покупка — в общей строке).
local function card(parent: Instance, kind: string, x: number, width: number, height: number)
	local compact = profile.compact
	local b = profile.button
	local pad = if compact then T.PadCompact else T.Pad
	local box = UI.InsetBox(parent, {
		Name = "Carte_" .. kind,
		Size = UDim2.fromOffset(width, height),
		Position = UDim2.fromOffset(x, 0),
		ZIndex = 4,
	})
	local textTop = if compact then pad else height - pad - b - 8 - 2 * (T.InfoText + 4) - (T.NameText + 6)
	local stageSize = if compact then math.min(height - 2 * pad, math.floor(width * 0.45)) else textTop - pad
	local textX = if compact then pad + stageSize + 8 else pad
	local textW = width - textX - pad
	local stage = Instance.new("Frame")
	stage.Name = "Scene"
	stage.BackgroundTransparency = 1
	stage.Size = if compact then UDim2.fromOffset(stageSize, stageSize) else UDim2.new(1, -2 * pad, 0, stageSize)
	stage.Position = UDim2.fromOffset(pad, pad)
	stage.ZIndex = 5
	stage.Parent = box
	UI.Sunburst(stage, math.min(if compact then stageSize else width, stageSize) * 0.9).ZIndex = 5
	local view, camera, center, distance = preview(stage, kind, 6)
	-- ПК: название крупно, «шанс» мельче (размер в разметке; без TextScaled). Телефон: одним размером и уменьшается
	-- целиком, если не влезает (TextScaled с размером в разметке ломает пропорции).
	local chance = "шанс ×" .. tostring(Catch.Bonus[kind])
	local title = UI.Text(
		box,
		if compact
			then ('%s  <font color="#FFFFFF">%s</font>'):format(Catch.Names[kind], chance)
			else ('%s  <font size="%d" color="#FFFFFF">%s</font>'):format(Catch.Names[kind], T.InfoText, chance),
		{
			Name = "Nom",
			Size = UDim2.fromOffset(textW, T.NameText + 6),
			Position = UDim2.fromOffset(textX, textTop),
			AnchorPoint = Vector2.zero,
			AlignX = Enum.TextXAlignment.Left,
			TextSize = if compact then nil else T.NameText,
			Max = if compact then T.NameCompact else nil,
			Min = if compact then 14 else nil,
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
			Size = UDim2.fromOffset(textW, T.InfoText + 4),
			Position = UDim2.fromOffset(textX, y),
			AnchorPoint = Vector2.zero,
			AlignX = Enum.TextXAlignment.Left,
			Max = T.InfoText,
			Min = 12,
			Rich = true,
			ZIndex = 7,
		})
	end
	local c: Card = {
		stock = info("Stock", textTop + T.NameText + 6),
		price = info("Prix", textTop + T.NameText + 6 + T.InfoText + 4),
		view = view,
		camera = camera,
		center = center,
		distance = distance,
	}
	if compact then
		-- выбор вида: салатовая рамка Stud-UI (как выбранный слот) и касание по всей карточке
		local frame = Instance.new("Frame")
		frame.Name = "Selection"
		frame.BackgroundTransparency = 1
		frame.Size = UDim2.fromScale(1, 1)
		frame.ZIndex = 8
		frame.Visible = false
		frame.Parent = box
		UI.Corner(frame, 6)
		UI.Stroke(frame, UI.Colors.Selection, 3)
		c.select = frame
		local pick = Instance.new("TextButton")
		pick.Name = "Choisir"
		pick.BackgroundTransparency = 1
		pick.Text = ""
		pick.Size = UDim2.fromScale(1, 1)
		pick.ZIndex = 9
		pick.Parent = box
		pick.Activated:Connect(function()
			selected = kind
			render()
		end)
	else
		c.qty, c.buy = buyRow(box, function()
			return kind
		end, pad, height - pad - b / 2, width - 2 * pad, profile.qty)
	end
	cards[kind] = c
	placeCamera(c, 0)
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
	local function line(name: string, y: number, width: number, max: number): TextLabel
		return UI.Text(corps, "", {
			Name = name,
			Font = "Bold",
			Size = UDim2.fromOffset(width, max + 6),
			Position = UDim2.fromOffset(pad, y),
			AnchorPoint = Vector2.zero,
			AlignX = Enum.TextXAlignment.Left,
			Max = max,
			Min = 12,
			Rich = true,
			ZIndex = 5,
		})
	end
	local footY = H - pad - (T.InfoText + 6)
	footer = line("Pied", footY, W - 2 * pad, T.InfoText)
	local cardsTop, cardsBottom
	bar = nil
	if profile.compact then
		-- телефон: строки уровня нет (уровень — в подвале), над подвалом — общая строка покупки выбранного вида
		subtitle = nil :: any
		cardsTop = pad + b + 10
		local rowY = footY - 6 - b / 2
		local rowW = 2 * b + T.QtyCompact + 20 + T.Buy
		local rowX = W - pad - rowW
		local qtyText, buy = buyRow(corps, function()
			return selected
		end, rowX, rowY, rowW, T.QtyCompact)
		local total = line("Total", rowY - (T.BarText + 6) / 2, rowX - 2 * pad - 10, T.BarText)
		bar = { qty = qtyText, buy = buy, total = total }
		cardsBottom = rowY - b / 2 - 10
	else
		local subY = pad + b + 6
		subtitle = line("Niveau", subY, W - 2 * pad, T.InfoText)
		cardsTop = subY + T.InfoText + 14
		cardsBottom = footY - 8
	end
	local cardH = cardsBottom - cardsTop
	local row = Instance.new("Frame")
	row.Name = "Cartes"
	row.BackgroundTransparency = 1
	row.Size = UDim2.fromOffset(W - 2 * pad, cardH)
	row.Position = UDim2.fromOffset(pad, cardsTop)
	row.ZIndex = 4
	row.Parent = corps
	local gap = T.Gap
	local cardW = math.floor((W - 2 * pad - 2 * gap) / 3)
	cards = {}
	for i, kind in Catch.Kinds do
		card(row, kind, (i - 1) * (cardW + gap), cardW, cardH)
	end
	-- крестик «Fermer» привязывает сам Motion.Window
	menu = Motion.Window(screen, win.Fenetre, { Keep = { Toasts = true, Magasin = true }, Size = profile.boost })
	Motion.SpinSunbursts(screen)
end

-- Число, «Купить» и итог для вида kind (общее у карточки ПК и строки телефона); head — начало строки цены.
local function priceLine(kind: string, qtyLabel: TextLabel, buy: GuiButton, head: string?): string
	local price = priceOf(level, kind)
	local n = qty[kind]
	qtyLabel.Text = tostring(n)
	if not price then
		UI.SetButtonText(buy, "Скоро")
		UI.SetDisabled(buy, true)
		return "Цена: скоро"
	end
	local total = price * n
	local afford = state.coins >= total
	UI.SetButtonText(buy, "Купить")
	UI.SetDisabled(buy, not afford or not state.open)
	return ('%sИтого: <font color="%s">%s</font>'):format(
		head or ("Цена: %s · "):format(money(price)),
		if afford then "#60E87A" else "#FF6A6A",
		money(total)
	)
end

render = function()
	if not menu then
		return
	end
	for lvl, tab in tabs do
		UI.Recolor(tab, if lvl == level then "red" else "gray")
	end
	local zone = GameConfig.Zones[level]
	-- в подвале телефона — коротко (длинная строка сжалась бы до нечитаемой)
	local levelText = (if bar
		then 'Уровень <font color="%s">%d — %s</font>: только босс «%s»'
		else 'Уровень <font color="%s">%d — %s</font>: Ловибумы ловят только существ босса «%s»'):format(
		UI.Colors.HighlightHex,
		level,
		zone.name,
		zone.boss
	)
	if subtitle then
		subtitle.Text = levelText
	end
	for _, kind in Catch.Kinds do
		local c = cards[kind]
		c.stock.Text = ('Есть: <font color="%s">%s</font>'):format(
			UI.Colors.HighlightHex,
			NumberFormat.Short(stockOf(level, kind))
		)
		if c.qty and c.buy then
			c.price.Text = priceLine(kind, c.qty, c.buy)
		else
			local price = priceOf(level, kind)
			c.price.Text = if price then "Цена: " .. money(price) else "Цена: скоро"
		end
		if c.select then
			c.select.Visible = kind == selected
		end
	end
	if bar then
		bar.total.Text = priceLine(
			selected,
			bar.qty,
			bar.buy,
			('<font color="#%s">%s</font> ×%d · '):format(
				T.KindColor[selected]:ToHex(),
				Catch.Names[selected],
				qty[selected]
			)
		)
	end
	local coins = ('У вас: <font color="#60E87A">%s</font>'):format(money(state.coins or 0))
	-- уровень без утверждённой цены: в игре — «скоро», в Studio — предварительная цена с пометкой
	local approved = Catch.Prices and Catch.Prices[level] ~= nil
	local sold = priceOf(level, "Boom") ~= nil
	local note = if approved
		then ""
		elseif sold then '   ·   <font color="#FFD23F">' .. (if bar
			then "предв. цены"
			else "предварительные цены (Studio)") .. "</font>"
		else (if bar
			then "   ·   скоро"
			else "   ·   Ловибумы этого уровня — скоро")
	footer.Text = if bar then coins .. "   ·   " .. levelText .. note else coins .. note
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
		waitingUntil = 0 -- сервер ответил
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

-- Окно «Улучшение музея» (D56, Stud-UI D20: золотая шапка — рост). Слева карточка «Сейчас», справа — «После
-- улучшения»: уровень, сколько мест открыто, сколько устройств защиты можно поставить; между ними стрелка. Ниже —
-- полоса из 20 мест (открытые, те, что откроются, закрытые), цена следующего уровня, состояние и кнопка «Улучшить».
-- Состояния кнопки: можно купить; не хватает монет (сколько не хватает); временный запрет — подготовка, Судная ночь и
-- 10 с после неё (причина и отсчёт до открытия); максимальный уровень. Окно только показывает и просит: уровень и
-- монеты — атрибуты игрока MuseumLevel и Coins (ставит сервер), цена и места — Shared/MuseumRules по общему конфигу,
-- запрет — Shared/GameTime.UpgradeLock; покупку проверяет и проводит сервер (MuseumUpgrade → MuseumUpgradeService),
-- клиент шлёт только номер следующего уровня и показывает ответ (MuseumUpgradeResult).
-- Кнопка «Музей» в колонке меню HUD — четвёртая, под «Магазином»; пока идёт обучение (атрибут Tutorial), её нет; во
-- время поимки (атрибут Catching) окно не открывается и закрывается.
-- Адаптивно, как «Магазин»: размер окна — по экрану (ниже кнопок Roblox), на телефоне масштаб не меньше PhoneScale,
-- кнопка на касание не ниже MinTouch px; низкое окно — тесная раскладка. В Studio экран подменяют атрибуты игрока
-- DevViewport и DevTouch.
-- Зависит от Shared/StudUI, Shared/MuseumRules, Shared/DefenseRules, Shared/GameTime, Shared/NumberFormat, Remotes,
-- Config/GameConfig, Config/UITokens, UI/MenuHud, UI/HudIcons.

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
local MuseumRules = require(Shared:WaitForChild("MuseumRules"))
local NumberFormat = require(Shared:WaitForChild("NumberFormat"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Config:WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local Client = script.Parent.Parent
local HudIcons = require(Client:WaitForChild("UI"):WaitForChild("HudIcons"))
local MenuHud = require(Client:WaitForChild("UI"):WaitForChild("MenuHud"))

local T = UITokens.MuseumUpgrade
local Codes = MuseumRules.Codes
local MAX_LEVEL = MuseumRules.MaxLevel(GameConfig)
local MAX_SLOTS = GameConfig.Museum.MaxSlots
local player = Players.LocalPlayer

local MuseumUpgradeController = {}

type Profile = {
	key: string,
	window: Vector2,
	boost: number,
	button: Vector2,
	compact: boolean,
}
type Card = {
	box: Frame,
	caption: TextLabel,
	level: TextLabel,
	levelShadow: TextLabel,
	lines: { TextLabel },
	icon: ImageLabel,
}

local profile: Profile
local gui: ScreenGui? = nil
local win: any
local menu: any
local cards: { current: Card, next: Card }
local arrow: ImageLabel
local pips: { Frame } = {}
local pipsLabel: TextLabel
local price: TextLabel
local status: TextLabel
local buy: GuiButton
local hudButton: GuiButton? = nil
local waitingUntil = 0 -- после «Улучшить» ждём ответа сервера: повторное нажатие не шлём
local refusal: { text: string, untilTime: number }? = nil -- ответ сервера об отказе (показывается MessageTime секунд)
local shown: { [any]: any } = {} -- что уже показано (тексты и состояния меняются только при изменении)

local function money(n: number): string
	return "$" .. NumberFormat.Short(n)
end

local function hex(color: Color3): string
	return "#" .. color:ToHex()
end

-- «до N устройств» (родительный падеж: до 1 устройства, до 2…5 устройств).
local function devices(level: number): string
	local n = DefenseRules.MaxDevices(GameConfig.Defense, level)
	return if n == 1 then "до 1 устройства" else ("до %d устройств"):format(n)
end

-- Раскладка под текущий экран (как у «Магазина»).
local function measure(): Profile
	local fake = GameConfig.DevMode and player:GetAttribute("DevViewport")
	local inset = GuiService:GetGuiInset().Y
	local viewport = if typeof(fake) == "Vector2" then fake else workspace.CurrentCamera.ViewportSize
	local screen = math.clamp(
		math.min(viewport.X / Motion.REFERENCE.X, viewport.Y / Motion.REFERENCE.Y),
		Motion.MIN_SCALE,
		Motion.MAX_SCALE
	)
	local touch = if typeof(fake) == "Vector2"
		then player:GetAttribute("DevTouch") == true
		else UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
	local scale = if touch then math.max(screen, T.PhoneScale) else screen
	local w = math.clamp(math.floor((viewport.X - 2 * T.Margin) / scale), T.MinWindow.X, T.Window.X)
	local h = math.clamp(math.floor((viewport.Y - inset - 2 * T.Margin) / scale), T.MinWindow.Y, T.Window.Y)
	local compact = h < T.CompactHeight
	local base = if compact then T.ButtonCompact else T.Button
	local height = if touch then math.max(base.Y, math.ceil(T.MinTouch / scale)) else base.Y
	return {
		key = ("%dx%d:%d"):format(w, h, height),
		window = Vector2.new(w, h),
		boost = scale / Motion.ScreenScale(),
		button = Vector2.new(base.X, height),
		compact = compact,
	}
end

-- Поменять свойство, только если значение другое (окно обновляется несколько раз в секунду ради отсчёта запрета).
local function set(object: Instance, property: string, value: any)
	local key = object
	local slot = shown[key]
	if not slot then
		slot = {}
		shown[key] = slot
	end
	if slot[property] ~= value then
		slot[property] = value;
		(object :: any)[property] = value
	end
end

-- Карточка уровня: сверху подпись и объёмное «Уровень N», справа от них иконка-наклейка (дом; у максимума — кубок);
-- ниже три строки во всю ширину (одного размера). lead — отступ текста слева: на край правой карточки заходит
-- стрелка; reserve — тот же отступ в расчёте ширины заголовка у обеих карточек (заголовки одного размера, иконка их
-- не касается); sun — лучи за иконкой.
local function card(
	parent: Instance,
	name: string,
	x: number,
	y: number,
	w: number,
	h: number,
	color: Color3,
	lead: number,
	reserve: number,
	sun: boolean
): Card
	local compact = profile.compact
	local inner = if compact then 8 else 14
	local levelText = if compact then T.LevelCompact else T.LevelText
	local lineText = if compact then T.LineCompact else T.LineText
	local box = UI.InsetBox(parent, {
		Name = name,
		Size = UDim2.fromOffset(w, h),
		Position = UDim2.fromOffset(x, y),
		ZIndex = 4,
	})
	local usable = h - 2 * inner
	local captionH = math.min(T.CaptionText + 6, math.floor(usable * 0.16))
	local levelH = math.min(levelText + 10, math.floor(usable * 0.34))
	local lineH = math.min(lineText + 8, math.floor((usable - captionH - levelH - 14) / 3))
	-- содержимое — по высоте в середине карточки
	local top = inner + math.max(math.floor((usable - captionH - levelH - 3 * lineH - 14) / 2), 0)
	local headH = captionH + levelH + 4
	local iconSize = math.min(headH + 2 * inner, math.floor(w * 0.27))
	local textX = inner + lead
	local fullW = w - textX - inner
	local headW = w - 2 * inner - reserve - iconSize - T.IconGap
	local function label(labelName: string, at: number, width: number, height: number, max: number): TextLabel
		return UI.Text(box, "", {
			Name = labelName,
			Font = "Bold",
			Size = UDim2.fromOffset(width, height),
			Position = UDim2.fromOffset(textX, at),
			AnchorPoint = Vector2.zero,
			AlignX = Enum.TextXAlignment.Left,
			Max = max,
			Min = T.MinText,
			Rich = true,
			ZIndex = 6,
		})
	end
	local caption = label("Legende", top, headW, captionH, T.CaptionText)
	caption.TextColor3 = color
	local level, levelShadow = UI.ShadowText(box, "", {
		Name = "Niveau",
		ShadowName = "NiveauOmbre",
		Size = UDim2.fromOffset(headW, levelH),
		Position = UDim2.fromOffset(textX, top + captionH + 4),
		AnchorPoint = Vector2.zero,
		AlignX = Enum.TextXAlignment.Left,
		Max = levelText,
		Min = 18,
		Thickness = 3,
		ZIndex = 6,
	})
	local lines = {}
	for i = 1, 3 do
		lines[i] = label("Ligne" .. i, top + headH + 10 + (i - 1) * (lineH + 2), fullW, lineH, lineText)
	end
	-- иконка-наклейка Stud-UI: справа от заголовка, с наклоном, чуть выступает за край карточки
	local stage = Instance.new("Frame")
	stage.Name = "Vitrine"
	stage.BackgroundTransparency = 1
	stage.Size = UDim2.fromOffset(iconSize, iconSize)
	stage.AnchorPoint = Vector2.new(1, 0.5)
	stage.Position = UDim2.new(1, -inner + 6, 0, top + math.floor(headH / 2))
	stage.ZIndex = 5
	stage.Parent = box
	if sun then
		UI.Sunburst(stage, math.floor(iconSize * 1.3)).ZIndex = 5
	end
	local icon = Instance.new("ImageLabel")
	icon.Name = "Icone"
	icon.BackgroundTransparency = 1
	icon.ScaleType = Enum.ScaleType.Fit
	icon.Size = UDim2.fromScale(1, 1)
	icon.Rotation = T.Tilt
	icon.ZIndex = 7
	icon.Parent = stage
	return { box = box, caption = caption, level = level, levelShadow = levelShadow, lines = lines, icon = icon }
end

local render: () -> ()

local function onBuy()
	local level = MuseumRules.Level(GameConfig, player:GetAttribute("MuseumLevel"))
	local coins = player:GetAttribute("Coins")
	local lock = GameTime.UpgradeLock(GameTime.Now())
	if MuseumRules.Check(GameConfig, level, if type(coins) == "number" then coins else 0, lock) ~= nil then
		Motion.Shake(buy) -- причина уже написана рядом с кнопкой
		return
	end
	if os.clock() < waitingUntil then
		return -- прошлый запрос ещё не подтверждён сервером
	end
	waitingUntil = os.clock() + T.Wait
	refusal = nil
	-- только номер следующего уровня: цену, монеты и сам уровень сервер берёт из профиля
	Remotes.Get(Remotes.Names.MuseumUpgrade):FireServer(level + 1)
	render()
end

local function build()
	profile = measure()
	if gui then
		if menu and menu.Destroy then
			menu.Destroy()
		end
		gui:Destroy()
	end
	table.clear(shown)
	local screen = UI.ScreenGui("MuseeNiveau", 12)
	screen.Enabled = false
	screen.Parent = player:WaitForChild("PlayerGui")
	gui = screen
	local inset = GuiService:GetGuiInset().Y
	win = UI.Window(screen, {
		Size = profile.window,
		Title = "Улучшение музея",
		Header = T.Header,
		Icon = HudIcons.Get("Museum"),
		TitleWidth = math.min(620, profile.window.X - 180),
		Position = UDim2.new(0.5, 0, 0.5, inset / 2),
	})
	local corps = win.Corps
	local W = win.Width - 5
	local H = corps.Size.Y.Offset
	local compact = profile.compact
	local pad = if compact then T.PadCompact else T.Pad
	local gap = if compact then T.GapCompact else T.Gap
	local b = profile.button

	-- низ: слева цена и состояние, справа кнопка
	local bottomY = H - pad - b.Y
	local textW = W - 2 * pad - b.X - gap
	local priceText = if compact then T.PriceCompact else T.PriceText
	local statusText = if compact then T.StatusCompact else T.StatusText
	local priceH = math.floor(b.Y * 0.52)
	price = UI.Text(corps, "", {
		Name = "Prix",
		Size = UDim2.fromOffset(textW, priceH),
		Position = UDim2.fromOffset(pad, bottomY),
		AnchorPoint = Vector2.zero,
		AlignX = Enum.TextXAlignment.Left,
		Max = priceText,
		Min = T.MinText,
		Rich = true,
		ZIndex = 6,
	})
	status = UI.Text(corps, "", {
		Name = "Etat",
		Font = "Bold",
		Size = UDim2.fromOffset(textW, b.Y - priceH),
		Position = UDim2.fromOffset(pad, bottomY + priceH),
		AnchorPoint = Vector2.zero,
		AlignX = Enum.TextXAlignment.Left,
		Max = statusText,
		Min = T.MinText,
		Rich = true,
		ZIndex = 6,
	})
	buy = UI.Button(corps, {
		Name = "Ameliorer",
		Theme = "green",
		Size = b,
		Position = UDim2.fromOffset(W - pad - b.X / 2, bottomY + b.Y / 2),
		Text = "Улучшить",
		TextSize = if compact then 26 else 30,
		ZIndex = 7,
	})
	Motion.BindButton(buy, 1.05, nil, onBuy)

	-- полоса из 20 мест над нижней строкой: подпись и квадратики
	local pip = if compact then T.PipCompact else T.Pip
	local labelW = math.min(T.PipsLabel, math.floor(W * 0.24))
	local room = W - 2 * pad - labelW - gap
	local pipGap = math.clamp(math.floor((room - MAX_SLOTS * pip) / (MAX_SLOTS - 1)), 2, T.PipGap)
	pip = math.min(pip, math.floor((room - (MAX_SLOTS - 1) * pipGap) / MAX_SLOTS))
	local pipsY = bottomY - gap - pip
	pipsLabel = UI.Text(corps, "", {
		Name = "Places",
		Font = "Bold",
		Size = UDim2.fromOffset(labelW, pip + 4),
		Position = UDim2.fromOffset(pad, pipsY - 2),
		AnchorPoint = Vector2.zero,
		AlignX = Enum.TextXAlignment.Left,
		Max = statusText,
		Min = T.MinText,
		Rich = true,
		ZIndex = 6,
	})
	pips = {}
	for slot = 1, MAX_SLOTS do
		local frame = Instance.new("Frame")
		frame.Name = "Place" .. slot
		frame.BorderSizePixel = 0
		frame.BackgroundColor3 = T.PipClosed
		frame.Size = UDim2.fromOffset(pip, pip)
		frame.Position = UDim2.fromOffset(pad + labelW + gap + (slot - 1) * (pip + pipGap), pipsY)
		frame.ZIndex = 5
		frame.Parent = corps
		UI.Corner(frame, 4)
		UI.Stroke(frame, UI.Colors.InsetStroke, 2)
		pips[slot] = frame
	end

	-- карточки «Сейчас» и «После улучшения», между ними стрелка-наклейка
	local cardsTop = pad
	local cardsH = pipsY - gap - cardsTop
	local cardW = math.floor((W - 2 * pad - gap) / 2)
	local arrowSize = math.min(if compact then T.ArrowCompact else T.Arrow, math.floor(cardsH * 0.45))
	-- текст правой карточки начинается правее стрелки, которая заходит на её край
	local lead = math.floor(arrowSize / 2)
	cards = {
		current = card(corps, "Maintenant", pad, cardsTop, cardW, cardsH, T.Current, 0, lead, false),
		next = card(corps, "Apres", pad + cardW + gap, cardsTop, cardW, cardsH, T.Next, lead, lead, true),
	}
	arrow = Instance.new("ImageLabel")
	arrow.Name = "Fleche"
	arrow.BackgroundTransparency = 1
	arrow.Image = HudIcons.Get("Upgrade")
	arrow.ScaleType = Enum.ScaleType.Fit
	arrow.Size = UDim2.fromOffset(arrowSize, arrowSize)
	arrow.AnchorPoint = Vector2.new(0.5, 0.5)
	arrow.Position = UDim2.fromOffset(pad + cardW + gap / 2, cardsTop + cardsH / 2)
	arrow.ZIndex = 9
	arrow.Parent = corps

	-- крестик «Fermer» привязывает сам Motion.Window
	menu = Motion.Window(screen, win.Fenetre, { Keep = { Toasts = true, MuseeNiveau = true }, Size = profile.boost })
	Motion.SpinSunbursts(screen)
end

render = function()
	if not menu then
		return
	end
	local level = MuseumRules.Level(GameConfig, player:GetAttribute("MuseumLevel"))
	local coinsValue = player:GetAttribute("Coins")
	local coins = if type(coinsValue) == "number" then coinsValue else 0
	local now = GameTime.Now()
	local lock, unlockAt = GameTime.UpgradeLock(now)
	local code = MuseumRules.Check(GameConfig, level, coins, lock)
	local isMax = code == Codes.Max
	local slots = MuseumRules.Slots(GameConfig, level)
	local nextLevel = math.min(level + 1, MAX_LEVEL)
	local nextSlots = MuseumRules.Slots(GameConfig, nextLevel)
	local nextColor = hex(T.Next)

	-- карточка «Сейчас»
	local current = cards.current
	set(current.caption, "Text", "СЕЙЧАС")
	set(current.level, "Text", ("Уровень %d"):format(level))
	set(current.levelShadow, "Text", ("Уровень %d"):format(level))
	set(current.icon, "Image", HudIcons.Get("Museum"))
	set(current.lines[1], "Text", ("Мест: %d из %d"):format(slots, MAX_SLOTS))
	set(current.lines[2], "Text", "Защита: " .. devices(level))
	local galleries = GameConfig.Defense.Galleries.Level
	local noGalleries = ("Галереи — с уровня %d"):format(galleries)
	set(current.lines[3], "Text", if level >= galleries then "Галереи открыты" else noGalleries)

	-- карточка «После улучшения» (или «Максимум»)
	local after = cards.next
	-- между карточками: стрелка «станет» (стрелка «вверх» из набора, повёрнутая к правой карточке) или замок запрета
	local locked = code == Codes.Locked
	set(arrow, "Visible", not isMax)
	set(arrow, "Image", HudIcons.Get(if locked then "Lock" else "Upgrade"))
	set(arrow, "Rotation", if locked then T.Tilt else 90)
	set(after.icon, "Image", HudIcons.Get(if isMax then "Trophy" else "MuseumNext"))
	set(after.levelShadow, "Text", ("Уровень %d"):format(nextLevel))
	if isMax then
		set(after.caption, "Text", "МАКСИМУМ")
		set(after.caption, "TextColor3", T.Max)
		set(after.level, "Text", ("Уровень %d"):format(MAX_LEVEL))
		set(after.lines[1], "Text", ("Все %d мест открыты"):format(MAX_SLOTS))
		set(after.lines[2], "Text", "Защита: " .. devices(MAX_LEVEL))
		set(after.lines[3], "Text", "Галереи открыты")
	else
		local moreSlots = nextSlots - slots
		local moreDevices = DefenseRules.MaxDevices(GameConfig.Defense, nextLevel)
			- DefenseRules.MaxDevices(GameConfig.Defense, level)
		set(after.caption, "Text", "ПОСЛЕ УЛУЧШЕНИЯ")
		set(after.caption, "TextColor3", T.Next)
		set(after.level, "Text", ("Уровень %d"):format(nextLevel))
		set(
			after.lines[1],
			"Text",
			if moreSlots > 0
				then ('Мест: %d <font color="%s">(+%d)</font>'):format(nextSlots, nextColor, moreSlots)
				else ("Мест: %d (столько же)"):format(nextSlots)
		)
		set(
			after.lines[2],
			"Text",
			if moreDevices > 0
				then ('Защита: %s <font color="%s">(+%d)</font>'):format(
					devices(nextLevel),
					nextColor,
					moreDevices
				)
				else "Защита: " .. devices(nextLevel)
		)
		set(
			after.lines[3],
			"Text",
			if nextLevel == galleries
				then ('<font color="%s">Откроются две галереи</font>'):format(nextColor)
				elseif nextLevel > galleries then "Галереи открыты"
				else noGalleries
		)
	end

	-- полоса мест
	for slot, frame in pips do
		set(
			frame,
			"BackgroundColor3",
			if slot <= slots then T.PipOpen elseif slot <= nextSlots and not isMax then T.PipNew else T.PipClosed
		)
	end
	set(
		pipsLabel,
		"Text",
		if isMax or nextSlots == slots
			then ("Места: %d из %d"):format(slots, MAX_SLOTS)
			else ('Места: %d <font color="%s">→ %d</font>'):format(slots, nextColor, nextSlots)
	)

	-- цена, состояние и кнопка
	local priceValue = MuseumRules.Price(GameConfig, level)
	local waiting = os.clock() < waitingUntil
	local note = refusal
	if note and os.clock() >= note.untilTime then
		refusal = nil
		note = nil
	end
	local good, bad, warn = hex(UI.Colors.Positive), hex(UI.Colors.Danger), hex(T.Warn)
	local priceLine, statusLine, buttonText, enabled
	if isMax or not priceValue then
		priceLine = ('<font color="%s">Музей максимального уровня</font>'):format(hex(T.Max))
		statusLine = ("Все %d мест открыты — улучшать больше нечего"):format(
			MAX_SLOTS
		)
		buttonText, enabled = "Максимум", false
	else
		priceLine = ('Уровень %d — <font color="%s">%s</font>'):format(
			nextLevel,
			if code == Codes.Coins then bad else good,
			money(priceValue)
		)
		if code == Codes.Locked then
			-- коротко, в одну строку: что идёт и когда откроется (полную причину сервер пишет в уведомлении)
			local left = if unlockAt then math.max(unlockAt - now, 0) else 0
			local phase = GameTime.At(now).phase
			local why = if phase == "Preparation"
				then "Подготовка к Судной ночи"
				elseif phase == "DoomNight" then "Идёт Судная ночь"
				else "Судная ночь закончилась"
			statusLine = ('<font color="%s">%s</font> · откроется через %s'):format(
				warn,
				why,
				Motion.Duration(math.ceil(left))
			)
			buttonText, enabled = "Закрыто", false
		elseif code == Codes.Coins then
			statusLine = ('Не хватает <font color="%s">%s</font> · у вас %s'):format(
				bad,
				money(priceValue - coins),
				money(coins)
			)
			buttonText, enabled = "Не хватает", false
		elseif code ~= nil then
			statusLine = MuseumRules.Texts[code] or ""
			buttonText, enabled = "Улучшить", false
		else
			statusLine = ('У вас: <font color="%s">%s</font> — хватает'):format(good, money(coins))
			buttonText, enabled = "Улучшить", true
		end
	end
	if waiting then
		buttonText, enabled = "…", false
	end
	if note then
		statusLine = ('<font color="%s">%s</font>'):format(bad, note.text) -- ответ сервера важнее расчёта окна
	end
	set(price, "Text", priceLine)
	set(status, "Text", statusLine)
	local slot = shown[buy] or {}
	shown[buy] = slot
	if slot.text ~= buttonText then
		slot.text = buttonText
		UI.SetButtonText(buy, buttonText)
	end
	if slot.enabled ~= enabled then
		slot.enabled = enabled
		-- Stud-UI: зелёная — подтвердить покупку, серая и приглушённая — сейчас недоступно
		UI.Recolor(buy, if enabled then "green" else "gray")
		UI.SetDisabled(buy, not enabled)
	end
end

local function isOpen(): boolean
	return menu ~= nil and menu.IsOpen
end

local function available(): boolean
	return player:GetAttribute("Tutorial") == nil
end

-- Открыть окно (кнопка HUD). В обучении и во время поимки — нельзя (сервер всё равно откажет в покупке).
function MuseumUpgradeController.Open()
	if not available() or player:GetAttribute("Catching") then
		return
	end
	if not menu or measure().key ~= profile.key then
		build()
	end
	render()
	menu.Open()
end

local function toggle()
	if isOpen() then
		menu.Close()
	else
		MuseumUpgradeController.Open()
	end
end

local function updateHud()
	if hudButton and hudButton.Parent then
		(hudButton.Parent :: GuiObject).Visible = available()
	end
	if isOpen() and not available() then
		menu.Close()
	end
end

function MuseumUpgradeController.Init()
	-- Кнопка «Музей» в колонке меню HUD v2 (четвёртая, под «Магазином»); у ученика её нет до конца обучения.
	hudButton = MenuHud.Add("Museum", "Музей", "blue", 4, toggle, { icon = "Museum" })
	updateHud()
	player:GetAttributeChangedSignal("Tutorial"):Connect(updateHud)
	Remotes.Get(Remotes.Names.MuseumUpgradeResult).OnClientEvent:Connect(function(payload)
		waitingUntil = 0 -- сервер ответил
		if type(payload) ~= "table" then
			return
		end
		if payload.ok then
			refusal = nil
			if isOpen() then
				Motion.Float(buy, ("Уровень %s!"):format(tostring(payload.level)), UI.Colors.FloatSuccess)
			end
		elseif payload.code ~= Codes.Stale and type(payload.message) == "string" then
			refusal = { text = payload.message, untilTime = os.clock() + T.MessageTime }
			if isOpen() then
				Motion.Shake(buy)
			end
		end
		if isOpen() then
			render()
		end
	end)
	for _, attribute in { "Coins", "MuseumLevel" } do
		player:GetAttributeChangedSignal(attribute):Connect(function()
			if isOpen() then
				render()
			end
		end)
	end
	player:GetAttributeChangedSignal("Catching"):Connect(function()
		if player:GetAttribute("Catching") and isOpen() then
			menu.Close()
		end
	end)
	ReplicatedStorage:GetAttributeChangedSignal("Phase"):Connect(function()
		if isOpen() then
			render()
		end
	end)
	-- отсчёт до конца запрета и возврат кнопки после ожидания ответа — пока окно открыто
	local since = 0
	RunService.Heartbeat:Connect(function(dt)
		since += dt
		if since >= T.Refresh then
			since = 0
			if isOpen() then
				render()
			end
		end
	end)
end

return MuseumUpgradeController

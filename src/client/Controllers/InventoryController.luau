-- Окно «Инвентарь» (D46, Stud-UI D20, вид — D50): все предметы игрока компактными карточками — 3D-превью (копия
-- модели из ReplicatedStorage.ItemPreviews) на мягком фоне цвета редкости, редкость, название, доход в секунду,
-- локация происхождения, статус («В музее · место N» или «В инвентаре»), повторы одного предмета — «×N». Карточка —
-- тёмная подложка со скруглением и тонкой рамкой цвета редкости (D50: вместо толстой чёрной рамки Stud-UI).
-- Кнопка «Выставить» открывает выбор постамента (свободный — «Поставить», занятый — «Заменить»), «Снять» возвращает
-- экспонат в инвентарь. Сортировка по доходу и редкости, фильтр по локации (строка «чипов»), поиск по названию,
-- счётчики предметов, постаментов и дохода. Подсказка постамента «Выставить из инвентаря» открывает окно сразу для
-- этого постамента (OpenForSlot).
-- Адаптивно: размер окна — по экрану (ниже кнопок Roblox), на телефоне масштаб не меньше PhoneScale, кнопки на
-- касание не меньше MinTouch px (D32); число колонок сетки — по ширине окна, карточки растягиваются на всю строку.
-- В низком окне (телефон: высота меньше CompactBelow) карточки — строки: превью слева, текст, кнопка справа.
-- Окно собирается при первом открытии и пересобирается, если поменялся размер экрана.
-- Клиент только показывает и просит: InventoryAction проверяет сервер; в подготовку, Судную ночь и 10 с доставки
-- кнопки неактивны и окно объясняет почему (Shared/GameTime.ExhibitLock — то же правило, что на сервере).
-- Зависит от Shared/StudUI, Shared/GameTime, Shared/NumberFormat, Shared/TextCase, Remotes, Config/Items,
-- Config/Rarities, Config/GameConfig, Config/UITokens, UI/MenuHud.

local ContextActionService = game:GetService("ContextActionService")
local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local GameTime = require(Shared:WaitForChild("GameTime"))
local Items = require(Config:WaitForChild("Items"))
local NumberFormat = require(Shared:WaitForChild("NumberFormat"))
local Rarities = require(Config:WaitForChild("Rarities"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local TextCase = require(Shared:WaitForChild("TextCase"))
local UITokens = require(Config:WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local MenuHud = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("MenuHud"))

local T = UITokens.Inventory
local player = Players.LocalPlayer

type Owned = { uid: string, itemId: string, slot: number?, pending: boolean? }
type Card = { itemId: string, uids: { string }, slot: number?, count: number, pending: boolean? }
-- Раскладка под экран: размер окна (px опорного экрана), множитель масштаба окна, высота кнопок и карточки.
type Profile = {
	key: string,
	window: Vector2,
	boost: number,
	button: number,
	card: number, -- высота карточки (в компактном режиме — строки)
	chip: number, -- высота «чипов» сортировки и фильтра и поля поиска (на касании — как у кнопок, D32)
	chipText: number,
	touch: boolean,
	compact: boolean,
}

local InventoryController = {}

local owned: { Owned } = {}
local sortMode = "Income" -- "Income" | "Rarity"
local origin: number? = nil -- фильтр: номер босса (локация), nil — все
local query = ""
local picking: Card? = nil -- выбран предмет — показан выбор постамента
local forSlot: number? = nil -- окно открыто с постамента: выбрать предмет для него

local gui: ScreenGui? = nil
local win: any
local menu: any = nil
local profile: Profile
local corps: Frame
local statsText: TextLabel
local sortBar: ScrollingFrame
local grid: ScrollingFrame
local gridWidth = 0 -- ширина сетки, px опорного экрана
local lockPill: Frame
local lockText: TextLabel
local actionButtons: { GuiButton } = {}
local lastLock: string? = nil

local function def(itemId: string): any
	return Items[itemId] or { displayName = itemId, rarity = "Common", income = 0 }
end

local function originName(itemId: string): string
	local boss = def(itemId).boss
	local zone = boss and GameConfig.Zones[boss]
	return if zone then zone.name else "—"
end

local function rarityGradient(rarity: string): ColorSequence
	return UITokens.ToColorSequence(UITokens.Rarity[rarity] or UITokens.Rarity.Common)
end

local function lockReason(): string?
	return GameTime.ExhibitLock(GameTime.Now())
end

local function send(action: string, uid: string, slot: number?)
	if lockReason() then
		return
	end
	Remotes.Get(Remotes.Names.InventoryAction):FireServer(action, uid, slot)
end

-- Раскладка под текущий экран (см. шапку).
-- В Studio (GameConfig.DevMode) экран можно подменить атрибутами игрока DevViewport (Vector2, px) и DevTouch —
-- проверка раскладки телефона без эмулятора: окно собирается тем же кодом в размере телефона.
local function measure(): Profile
	local fake = GameConfig.DevMode and player:GetAttribute("DevViewport")
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
	local inset = GuiService:GetGuiInset().Y
	local w = math.clamp(math.floor((viewport.X - 2 * T.Margin) / scale), T.MinWindow.X, T.Window.X)
	local h = math.clamp(math.floor((viewport.Y - inset - 2 * T.Margin) / scale), T.MinWindow.Y, T.Window.Y)
	local button = if touch then math.max(T.ButtonHeight, math.ceil(T.MinTouch / scale)) else T.ButtonHeight
	local compact = h < T.CompactBelow
	return {
		key = ("%dx%d:%d"):format(w, h, button),
		window = Vector2.new(w, h),
		boost = scale / Motion.ScreenScale(), -- множитель к масштабу окна StudMotion (по настоящему экрану)
		button = button,
		card = if compact then math.max(T.Row.Height, button + 2 * T.CardPad) else T.CardBody + button,
		chip = if touch then math.max(T.Chip.Height, button) else T.Chip.Height,
		chipText = if touch then T.Chip.TouchText else T.Chip.Text,
		touch = touch,
		compact = compact,
	}
end

-- Карточки: выставленные — по одной (у каждого своя кнопка «Снять»), в инвентаре — стопкой по предмету «×N».
local function buildCards(): { Card }
	local total: { [string]: number } = {}
	for _, item in owned do
		total[item.itemId] = (total[item.itemId] or 0) + 1
	end
	local cards: { Card } = {}
	local stacks: { [string]: Card } = {}
	for _, item in owned do
		if item.slot then
			table.insert(
				cards,
				{ itemId = item.itemId, uids = { item.uid }, slot = item.slot, count = total[item.itemId] }
			)
		elseif item.pending then
			-- украденное ещё передаётся по журналу (D46): отдельная карточка без кнопки
			table.insert(
				cards,
				{ itemId = item.itemId, uids = { item.uid }, count = total[item.itemId], pending = true }
			)
		else
			local stack = stacks[item.itemId]
			if not stack then
				stack = { itemId = item.itemId, uids = {}, count = total[item.itemId] }
				stacks[item.itemId] = stack
				table.insert(cards, stack)
			end
			table.insert(stack.uids, item.uid)
		end
	end
	local q = TextCase.Lower(query, true) -- кириллица: string.lower её не меняет
	local out = {}
	for _, card in cards do
		local d = def(card.itemId)
		local fits = (origin == nil or d.boss == origin)
			and (q == "" or string.find(TextCase.Lower(d.displayName, true), q, 1, true) ~= nil)
			and (forSlot == nil or card.slot == nil)
		if fits then
			table.insert(out, card)
		end
	end
	table.sort(out, function(a, b)
		local da, db = def(a.itemId), def(b.itemId)
		local ia, ib = da.income or 0, db.income or 0
		local ra, rb = Rarities.Rank(da.rarity), Rarities.Rank(db.rarity)
		if sortMode == "Rarity" and ra ~= rb then
			return ra > rb
		end
		if ia ~= ib then
			return ia > ib
		end
		if ra ~= rb then
			return ra > rb
		end
		if (a.slot ~= nil) ~= (b.slot ~= nil) then
			return a.slot ~= nil
		end
		if da.displayName ~= db.displayName then
			return da.displayName < db.displayName
		end
		return (a.slot or 0) < (b.slot or 0)
	end)
	return out
end

-- 3D-превью: копия модели из ItemPreviews во ViewportFrame; пока её нет — круг цвета редкости с буквой.
local function preview(parent: GuiObject, itemId: string, z: number)
	local folder = ReplicatedStorage:FindFirstChild("ItemPreviews")
	local source = folder and folder:FindFirstChild(itemId)
	if source and source:IsA("Model") then
		local view = Instance.new("ViewportFrame")
		view.Name = "Apercu"
		view.BackgroundTransparency = 1
		view.Size = UDim2.fromScale(1, 1)
		view.Ambient = Color3.fromRGB(165, 165, 175)
		view.LightColor = Color3.new(1, 1, 1)
		view.LightDirection = Vector3.new(-0.6, -1, -0.8)
		view.ZIndex = z
		local model = source:Clone()
		model.Parent = view
		local cf, box = model:GetBoundingBox()
		local camera = Instance.new("Camera")
		camera.FieldOfView = 30
		local radius = box.Magnitude / 2
		local distance = radius / math.sin(math.rad(camera.FieldOfView / 2)) * 1.05
		local dir = CFrame.Angles(0, math.rad(T.Turn), 0) * Vector3.new(0, 0.35, -1).Unit -- лицо модели смотрит в −Z
		camera.CFrame = CFrame.lookAt(cf.Position + dir * distance, cf.Position)
		camera.Parent = view
		view.CurrentCamera = camera
		view.Parent = parent
		return
	end
	local d = def(itemId)
	local dot = Instance.new("Frame")
	dot.Name = "Pastille"
	dot.Size = UDim2.fromScale(0.55, 0.55)
	dot.SizeConstraint = Enum.SizeConstraint.RelativeYY
	dot.Position = UDim2.fromScale(0.5, 0.5)
	dot.AnchorPoint = Vector2.new(0.5, 0.5)
	dot.BackgroundColor3 = Color3.new(1, 1, 1)
	dot.ZIndex = z
	UI.Corner(dot, 999)
	UI.Gradient(dot, rarityGradient(d.rarity), 90)
	UI.Stroke(dot, T.CardColor, 2)
	UI.Text(dot, utf8.char(utf8.codepoint(d.displayName, 1)), { TextSize = 34, ZIndex = z + 1 })
	dot.Parent = parent
end

-- Карточка D50: тёмная подложка со скруглением, тонкая рамка цвета accent (редкость) или нейтральная.
local function cardFrame(parent: Instance, order: number, accent: Color3?): Frame
	local card = Instance.new("Frame")
	card.Name = "Carte"
	card.BackgroundColor3 = T.CardColor
	card.BackgroundTransparency = T.CardTransparency
	card.BorderSizePixel = 0
	card.LayoutOrder = order
	card.ZIndex = 2
	UI.Corner(card, T.CardCorner)
	UI.Stroke(card, accent or T.CardNeutral, T.CardStroke, if accent then 0.1 else 0.4, nil, "Bord")
	card.Parent = parent
	return card
end

-- Кнопка карточки (cellWidth — ширина ячейки сетки, px опорного экрана): в карточке — внизу во всю ширину,
-- в строке (телефон) — справа посередине.
local function actionButton(
	parent: Instance,
	cellWidth: number,
	text: string,
	theme: string,
	onClick: () -> ()
): GuiButton
	local width = if profile.compact then T.Row.Button else cellWidth - 2 * T.CardPad
	local button = UI.Button(parent, {
		Name = "Action",
		Theme = theme,
		Size = Vector2.new(width, profile.button),
		Position = if profile.compact
			then UDim2.new(1, -(T.CardPad + width / 2), 0.5, 0)
			else UDim2.new(0.5, 0, 1, -(profile.button / 2 + T.CardPad)),
		Text = text,
		TextSize = T.ButtonText,
		ZIndex = 5,
	})
	Motion.BindButton(button, 1.04, nil, function()
		if lockReason() then
			Motion.Shake(button)
			return
		end
		onClick()
	end)
	table.insert(actionButtons, button)
	return button
end

local function clearGrid()
	table.clear(actionButtons)
	for _, child in grid:GetChildren() do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
end

-- Строка текста карточки: по умолчанию во всю ширину с отступами; opts.X и opts.W — свой столбец (строка-карточка).
local function line(parent: Instance, name: string, text: string, y: number, h: number, opts: { [string]: any })
	local x, w = opts.X, opts.W
	opts.X, opts.W = nil, nil
	local props = {
		Name = name,
		Size = if w then UDim2.fromOffset(w, h) else UDim2.new(1, -2 * T.CardPad, 0, h),
		Position = UDim2.fromOffset(x or T.CardPad, y),
		AnchorPoint = Vector2.zero,
		AlignX = opts.AlignX or Enum.TextXAlignment.Left,
		Stroke = UI.Colors.StrokeSlot,
		Thickness = opts.Thickness or 1.5,
		ZIndex = 6,
	}
	for k, v in opts do
		props[k] = v
	end
	return UI.Text(parent, text, props)
end

local render: () -> ()

-- Превью на мягком фоне цвета редкости (положение и размер — px опорного экрана внутри карточки).
local function stageFor(frame: Frame, itemId: string, rarityColor: Color3, position: UDim2, size: UDim2)
	local stage = Instance.new("Frame")
	stage.Name = "Vitrine"
	stage.BackgroundColor3 = rarityColor
	stage.BorderSizePixel = 0
	stage.Size = size
	stage.Position = position
	stage.ZIndex = 3
	UI.Corner(stage, T.CardCorner - 2)
	local glow = Instance.new("UIGradient")
	glow.Rotation = 90
	glow.Transparency = NumberSequence.new(T.PreviewGlow, 0.97)
	glow.Parent = stage
	stage.Parent = frame
	preview(stage, itemId, 4)
end

-- Статус предмета и его цвет.
local function statusOf(card: Card): (string, Color3)
	local status = if card.slot
		then ("В музее · место %d"):format(card.slot)
		elseif card.pending then "Передаётся…"
		else "В инвентаре"
	return status, if card.slot then UI.Colors.Positive elseif card.pending then T.Muted else UI.Colors.TagGold
end

-- Кнопка действия предмета: «Снять» (выставлен), «На место N» (окно открыто с постамента), «Выставить».
local function cardAction(frame: Frame, card: Card, cellWidth: number)
	if card.pending then
		return
	elseif card.slot then
		-- «Снять» — спокойная серая (красный в Stud-UI — уничтожить), «Выставить» — главная зелёная
		actionButton(frame, cellWidth, "Снять", "gray", function()
			send("Remove", card.uids[1])
		end)
	elseif forSlot then
		actionButton(frame, cellWidth, ("На место %d"):format(forSlot), "green", function()
			local slot = forSlot :: number
			send("Display", card.uids[1], slot)
			menu.Close()
		end)
	else
		actionButton(frame, cellWidth, "Выставить", "green", function()
			picking = card
			render()
		end)
	end
end

-- Карточка-строка (телефон): превью слева; редкость и «×N», название, доход и локация, статус; кнопка справа.
local function itemRow(card: Card, order: number, cellWidth: number)
	local d = def(card.itemId)
	local rarityColor = UITokens.RarityColor(d.rarity)
	local frame = cardFrame(grid, order, rarityColor)
	local pad = T.CardPad
	local side = profile.card - 2 * pad
	stageFor(frame, card.itemId, rarityColor, UDim2.fromOffset(pad, pad), UDim2.fromOffset(side, side))
	local x = pad + side + 10
	local w = cellWidth - x - T.Row.Button - 2 * pad
	local gap = math.max(0, (side - 16 - 24 - 18 - 16) / 3)
	local y = pad
	line(frame, "Rarete", Rarities.Names[d.rarity] or d.rarity, y, 16, {
		X = x,
		W = w,
		TextSize = T.InfoText,
		Gradient = rarityGradient(d.rarity),
	})
	if card.count > 1 then
		line(frame, "Quantite", "×" .. card.count, y, 16, {
			X = x,
			W = w,
			AlignX = Enum.TextXAlignment.Right,
			TextSize = T.InfoText + 1,
			Color = UI.Colors.TagGold,
		})
	end
	y += 16 + gap
	line(frame, "Nom", d.displayName, y, 24, { X = x, W = w, Max = T.NameText, Min = T.MinText, Thickness = 2 })
	y += 24 + gap
	line(frame, "Revenu", ("+%s/сек"):format(NumberFormat.Short(d.income or 0)), y, 18, {
		X = x,
		W = w,
		Font = "Gotham",
		TextSize = T.IncomeText,
		Gradient = UI.TextGradients.Money,
		Stroke = Color3.fromRGB(15, 51, 0),
	})
	line(frame, "Origine", originName(card.itemId), y + 1, 16, {
		X = x,
		W = w,
		Font = "Bold",
		AlignX = Enum.TextXAlignment.Right,
		Max = T.InfoText,
		Min = T.MinText,
		Color = T.Muted,
	})
	y += 18 + gap
	local status, color = statusOf(card)
	line(frame, "Statut", status, y, 16, {
		X = x,
		W = w,
		Font = "Bold",
		Max = T.InfoText,
		Min = T.MinText,
		Color = color,
	})
	cardAction(frame, card, cellWidth)
end

local function itemCard(card: Card, order: number, cellWidth: number)
	if profile.compact then
		itemRow(card, order, cellWidth)
		return
	end
	local d = def(card.itemId)
	local rarityColor = UITokens.RarityColor(d.rarity)
	local frame = cardFrame(grid, order, rarityColor)
	local pad = T.CardPad
	line(frame, "Rarete", Rarities.Names[d.rarity] or d.rarity, pad, 18, {
		TextSize = T.InfoText,
		Gradient = rarityGradient(d.rarity),
	})
	if card.count > 1 then
		line(frame, "Quantite", "×" .. card.count, pad, 18, {
			AlignX = Enum.TextXAlignment.Right,
			TextSize = T.InfoText + 1,
			Color = UI.Colors.TagGold,
		})
	end
	stageFor(frame, card.itemId, rarityColor, UDim2.fromOffset(pad, pad + 22), UDim2.new(1, -2 * pad, 0, T.Preview))
	local y = pad + 22 + T.Preview + 6
	local name = line(frame, "Nom", d.displayName, y, 42, {
		AlignX = Enum.TextXAlignment.Center,
		Max = T.NameText,
		Min = T.MinText,
		Thickness = 2,
	})
	name.TextWrapped = true
	y += 44
	line(frame, "Revenu", ("+%s/сек"):format(NumberFormat.Short(d.income or 0)), y, 20, {
		Font = "Gotham",
		TextSize = T.IncomeText,
		Gradient = UI.TextGradients.Money,
		Stroke = Color3.fromRGB(15, 51, 0),
	})
	line(frame, "Origine", originName(card.itemId), y + 2, 18, {
		Font = "Bold",
		AlignX = Enum.TextXAlignment.Right,
		Max = T.InfoText,
		Min = T.MinText,
		Color = T.Muted,
	})
	y += 22
	local status, color = statusOf(card)
	line(frame, "Statut", status, y, 18, {
		Font = "Bold",
		AlignX = Enum.TextXAlignment.Center,
		Max = T.InfoText,
		Min = T.MinText,
		Color = color,
	})
	cardAction(frame, card, cellWidth)
end

-- Выбор постамента для picking: свободный — «Поставить», занятый — «Заменить» (атомарно на сервере).
local function pedestalCard(slot: number, order: number, cellWidth: number)
	local occupant: Owned? = nil
	for _, item in owned do
		if item.slot == slot then
			occupant = item
		end
	end
	local frame = cardFrame(grid, order, if occupant then nil else UI.Colors.Positive)
	local pad = T.CardPad
	-- строка (телефон): текст слева от кнопки; карточка — по центру над кнопкой
	local column = if profile.compact
		then { X = pad + 6, W = cellWidth - T.Row.Button - 3 * pad - 6, AlignX = Enum.TextXAlignment.Left }
		else { AlignX = Enum.TextXAlignment.Center }
	local function col(opts: { [string]: any }): { [string]: any }
		for k, v in column do
			opts[k] = v
		end
		return opts
	end
	line(frame, "Numero", ("Место %d"):format(slot), pad, 28, col({ TextSize = T.NameText, Thickness = 2 }))
	local card = picking :: Card
	if occupant then
		local d = def(occupant.itemId)
		local text = ("%s · +%s/сек"):format(d.displayName, NumberFormat.Short(d.income or 0))
		line(
			frame,
			"Occupant",
			text,
			pad + 32,
			40,
			col({
				Font = "Bold",
				Max = T.InfoText,
				Min = T.MinText,
				Color = T.Muted,
			})
		).TextWrapped =
			true
		actionButton(frame, cellWidth, "Заменить", "orange", function()
			send("Replace", card.uids[1], slot)
			picking = nil
			render()
		end)
	else
		line(
			frame,
			"Libre",
			"Свободно",
			pad + 36,
			22,
			col({
				Font = "Bold",
				TextSize = T.InfoText + 2,
				Color = UI.Colors.Positive,
			})
		)
		actionButton(frame, cellWidth, "Поставить", "green", function()
			send("Display", card.uids[1], slot)
			picking = nil
			render()
		end)
	end
end

local function updateLock()
	local reason = lockReason()
	lastLock = reason
	lockPill.Visible = reason ~= nil
	lockText.Text = reason or ""
	for _, button in actionButtons do
		if button.Parent then
			UI.SetDisabled(button, reason ~= nil)
		end
	end
end

local function updateStats()
	local slots = player:GetAttribute("MuseumSlots") or GameConfig.Museum.SlotsByLevel[1]
	local displayed = 0
	for _, item in owned do
		if item.slot then
			displayed += 1
		end
	end
	-- в компактной шапке места мало: короткие подписи
	statsText.Text = (if profile.compact
		then 'Предметов: <font color="%s">%d</font>  Мест: <font color="%s">%d/%d</font>  '
			.. '<font color="#60E87A">+%s/сек</font>'
		else 'Предметов: <font color="%s">%d</font>   Постаменты: <font color="%s">%d/%d</font>   '
			.. 'Доход: <font color="#60E87A">+%s/сек</font>'):format(
		UI.Colors.HighlightHex,
		#owned,
		UI.Colors.HighlightHex,
		displayed,
		slots,
		NumberFormat.Short(player:GetAttribute("Income") or 0)
	)
end

-- «Чип» сортировки и фильтра (D50): плоская кнопка-капсула, выбранный — синий.
local function chip(text: string, active: boolean, order: number, onClick: () -> ())
	local c = T.Chip
	local button = Instance.new("TextButton")
	button.Name = "Filtre"
	button.AutoButtonColor = false
	button.AutomaticSize = Enum.AutomaticSize.X
	button.Size = UDim2.fromOffset(0, profile.chip)
	button.BackgroundColor3 = if active then c.Active else c.Idle
	button.BackgroundTransparency = if active then 0 else 0.15
	button.BorderSizePixel = 0
	button.FontFace = UI.Fonts.Bold
	button.TextSize = profile.chipText
	button.TextColor3 = if active then Color3.new(1, 1, 1) else c.IdleText
	button.Text = text
	button.LayoutOrder = order
	button.ZIndex = 4
	UI.Corner(button, profile.chip // 2)
	UI.Stroke(button, if active then Color3.new(1, 1, 1) else c.IdleStroke, 1.5, if active then 0.55 else 0.2)
	local padding = Instance.new("UIPadding")
	padding.PaddingLeft = UDim.new(0, c.Pad)
	padding.PaddingRight = UDim.new(0, c.Pad)
	padding.Parent = button
	Motion.BindButton(button, 1.05, nil, onClick)
	button.Parent = sortBar
	return button
end

-- Сортировка и фильтр по локации (локации — только те, откуда у игрока есть предметы).
local function buildBar()
	for _, child in sortBar:GetChildren() do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
	if picking then
		chip("← Назад", false, 1, function()
			picking = nil
			render()
		end)
		local question = UI.Text(
			sortBar,
			("Куда поставить «%s»?"):format(def((picking :: Card).itemId).displayName),
			{
				Name = "Question",
				Size = UDim2.fromOffset(700, profile.chip),
				AlignX = Enum.TextXAlignment.Left,
				Max = T.NameText,
				ZIndex = 4,
			}
		)
		question.LayoutOrder = 2
		return
	end
	chip("По доходу", sortMode == "Income", 1, function()
		sortMode = "Income"
		render()
	end)
	chip("По редкости", sortMode == "Rarity", 2, function()
		sortMode = "Rarity"
		render()
	end)
	local present: { [number]: boolean } = {}
	for _, item in owned do
		local boss = def(item.itemId).boss
		if boss then
			present[boss] = true
		end
	end
	local divider = Instance.new("Frame")
	divider.Name = "Separateur"
	divider.BackgroundColor3 = T.Chip.IdleStroke
	divider.BorderSizePixel = 0
	divider.Size = UDim2.fromOffset(2, profile.chip - 10)
	divider.LayoutOrder = 3
	divider.Parent = sortBar
	chip("Все", origin == nil, 4, function()
		origin = nil
		render()
	end)
	local order = 5
	for boss, zone in GameConfig.Zones do
		if present[boss] then
			chip(zone.name, origin == boss, order + boss, function()
				origin = if origin == boss then nil else boss
				render()
			end)
		end
	end
end

-- Сетка: столько колонок, сколько помещается карточек не уже Card.X; карточки растягиваются на всю строку.
-- Возвращает ширину ячейки.
local function fitGrid(cellHeight: number, minWidth: number): number
	local layout = grid:FindFirstChildOfClass("UIGridLayout") :: UIGridLayout
	local usable = gridWidth - 2 * T.GridPad - 8 -- полоса прокрутки
	-- строки (телефон) на узком экране — одной колонкой, карточки — не меньше двух колонок
	local columns = math.max(if profile.compact then 1 else 2, math.floor((usable + T.Gap) / (minWidth + T.Gap)))
	local width = math.floor((usable - T.Gap * (columns - 1)) / columns)
	layout.CellSize = UDim2.fromOffset(width, cellHeight)
	return width
end

render = function()
	if not win then
		return
	end
	if forSlot then
		-- в компактной шапке справа счётчики: коротко (кнопки карточек и так «На место N»)
		win.Titre.Text = ("Место %d" .. (if profile.compact then "" else ": что поставить?")):format(
			forSlot
		)
	else
		win.Titre.Text = "Инвентарь"
	end
	buildBar()
	clearGrid()
	if picking then
		local height = if profile.compact then profile.card else T.Pedestal.Y + profile.button
		local width = fitGrid(height, if profile.compact then T.Row.MinWidth else T.Pedestal.X)
		local slots = player:GetAttribute("MuseumSlots") or GameConfig.Museum.SlotsByLevel[1]
		for slot = 1, slots do
			pedestalCard(slot, slot, width)
		end
	else
		local width = fitGrid(profile.card, if profile.compact then T.Row.MinWidth else T.Card.X)
		local cards = buildCards()
		for order, card in cards do
			itemCard(card, order, width)
		end
		if #cards == 0 then
			local layout = grid:FindFirstChildOfClass("UIGridLayout") :: UIGridLayout
			layout.CellSize = UDim2.fromOffset(gridWidth - 2 * T.GridPad - 8, 90) -- пустое состояние — во всю ширину
			UI.Text(
				grid,
				if #owned == 0
					then "Пока пусто: победите босса и донесите добычу до сундука музея"
					else "Ничего не найдено",
				{
					Name = "Vide",
					Font = "Bold",
					Size = UDim2.fromOffset(gridWidth - 80, 60),
					Max = 24,
					Color = T.Muted,
					ZIndex = 4,
				}
			).LayoutOrder =
				1
		end
	end
	updateStats()
	updateLock()
end

local function build()
	profile = measure()
	local old = gui
	if old then
		old:Destroy()
	end
	local screen = UI.ScreenGui("Inventaire", 12)
	screen.Enabled = false
	screen.Parent = player:WaitForChild("PlayerGui")
	gui = screen
	local inset = GuiService:GetGuiInset().Y
	win = UI.Window(screen, {
		Size = profile.window,
		Title = "Инвентарь",
		Header = T.Header,
		TitleWidth = math.min(640, profile.window.X - 140),
		Position = UDim2.new(0.5, 0, 0.5, inset / 2), -- ниже кнопок Roblox
	})
	corps = win.Corps
	local W = win.Width - 5
	-- телефон (низкое окно): счётчики — в шапке справа от названия, поиск — в одной строке с «чипами»;
	-- иначе счётчики и поиск — первая строка, «чипы» — вторая
	local compact = profile.compact
	local bar = if compact then 0 else math.max(T.BarHeight, profile.chip + 6)
	local searchWidth = if compact then T.Row.Search else T.SearchWidth
	local chipsY = 12 + (if compact then 0 else bar + 6)

	statsText = UI.Text(if compact then win.Entete else corps, "", {
		Name = "Compteurs",
		Size = if compact
			then UDim2.fromOffset(W - T.Row.TitleSpace - T.Row.CloseSpace, T.StatsText + 8)
			else UDim2.fromOffset(W - T.SearchWidth - 48, bar),
		Position = if compact
			then UDim2.fromOffset(W - T.Row.CloseSpace, win.HeaderHeight / 2)
			else UDim2.fromOffset(18, 12 + bar / 2),
		AnchorPoint = if compact then Vector2.new(1, 0.5) else Vector2.new(0, 0.5),
		AlignX = if compact then Enum.TextXAlignment.Right else Enum.TextXAlignment.Left,
		Max = T.StatsText,
		Min = T.MinText,
		Rich = true,
		ZIndex = if compact then 11 else 4,
	})
	local searchHeight = if compact then profile.chip else bar - 6
	local searchFrame = UI.InsetBox(corps, {
		Name = "Recherche",
		Size = UDim2.fromOffset(searchWidth, searchHeight),
		Position = if compact
			then UDim2.new(1, -18, 0, chipsY + (profile.chip + 6) / 2)
			else UDim2.new(1, -18, 0, 12 + bar / 2),
		AnchorPoint = Vector2.new(1, 0.5),
		ZIndex = 4,
	})
	local searchBox = Instance.new("TextBox")
	searchBox.Name = "Saisie"
	searchBox.BackgroundTransparency = 1
	searchBox.Size = UDim2.new(1, -24, 1, 0)
	searchBox.Position = UDim2.fromOffset(12, 0)
	searchBox.FontFace = UI.Fonts.Bold
	searchBox.TextSize = T.SearchText
	searchBox.TextColor3 = Color3.new(1, 1, 1)
	searchBox.PlaceholderText = "Поиск по названию"
	searchBox.PlaceholderColor3 = T.Muted
	searchBox.TextXAlignment = Enum.TextXAlignment.Left
	searchBox.ClearTextOnFocus = false
	searchBox.Text = query
	searchBox.ZIndex = 6
	searchBox.Parent = searchFrame
	local typed = 0
	searchBox:GetPropertyChangedSignal("Text"):Connect(function()
		typed += 1
		local mark = typed
		task.delay(T.SearchDelay, function()
			if mark == typed then -- перерисовать один раз после паузы в наборе
				query = searchBox.Text
				if not picking then
					render()
				end
			end
		end)
	end)

	sortBar = Instance.new("ScrollingFrame")
	sortBar.Name = "Tri"
	sortBar.BackgroundTransparency = 1
	sortBar.BorderSizePixel = 0
	sortBar.ScrollingDirection = Enum.ScrollingDirection.X
	sortBar.ScrollBarThickness = 3
	sortBar.ScrollBarImageColor3 = Color3.new(1, 1, 1)
	sortBar.AutomaticCanvasSize = Enum.AutomaticSize.X -- больше локаций, чем помещается, — полоса прокручивается
	sortBar.CanvasSize = UDim2.new()
	sortBar.Size = UDim2.fromOffset(W - 36 - (if compact then searchWidth + 12 else 0), profile.chip + 6)
	sortBar.Position = UDim2.fromOffset(18, chipsY)
	sortBar.ZIndex = 4
	sortBar.Parent = corps
	local chips = Instance.new("UIListLayout")
	chips.FillDirection = Enum.FillDirection.Horizontal
	chips.VerticalAlignment = Enum.VerticalAlignment.Center
	chips.SortOrder = Enum.SortOrder.LayoutOrder
	chips.Padding = UDim.new(0, T.Chip.Gap)
	chips.Parent = sortBar

	local top = chipsY + profile.chip + 6 + 10
	gridWidth = W - 8
	grid = UI.ScrollList(corps, {
		Name = "Grille",
		Size = UDim2.fromOffset(gridWidth, corps.Size.Y.Offset - top - 6),
		Position = UDim2.fromOffset(4, top),
		Grid = T.Card,
		GridGap = T.Gap,
		PadTop = 4,
		PadLeft = T.GridPad,
		PadBottom = 60,
		ZIndex = 3,
	})

	lockPill = UI.Pill(corps, "", {
		Name = "Verrou",
		Width = math.min(W - 120, 760),
		Height = 40,
		TextSize = 20,
		Position = UDim2.new(0.5, 0, 1, -30),
		ZIndex = 30,
	})
	lockText = lockPill:FindFirstChild("Texte") :: TextLabel
	lockText.TextColor3 = UI.Colors.Danger
	lockPill.Visible = false

	-- крестик «Fermer» привязывает сам Motion.Window (второй BindButton давал двойные твины и Close)
	menu = Motion.Window(screen, win.Fenetre, { Keep = { Toasts = true, Inventaire = true }, Size = profile.boost })
end

local function open(slot: number?)
	if player:GetAttribute("PlacingDefense") then
		return -- идёт расстановка защиты: сначала поставить или отменить
	end
	if not menu or measure().key ~= profile.key then
		build() -- первое открытие или другой экран (поворот, окно ПК)
	end
	forSlot = slot
	picking = nil
	render()
	menu.Open()
end

local function isOpen(): boolean
	return menu ~= nil and menu.IsOpen
end

-- Открыть окно (из HUD или клавишей).
function InventoryController.Open()
	open(nil)
end

-- Окно для своего пустого постамента slot (подсказка «Выставить из инвентаря»).
function InventoryController.OpenForSlot(slot: number)
	open(slot)
end

local function toggle()
	if isOpen() then
		menu.Close()
	else
		InventoryController.Open()
	end
end

function InventoryController.Init()
	-- Кнопка «Инвентарь» в колонке меню HUD v2 (UI/MenuHud: справа, портфель, клавиша B на ПК).
	MenuHud.Add("Inventaire", "Инвентарь", "blue", 1, toggle, { icon = "Inventory", key = Enum.KeyCode.B })
	Remotes.Get(Remotes.Names.InventoryChanged).OnClientEvent:Connect(function(list: { Owned })
		owned = list
		if isOpen() then
			if picking then
				-- выбранного предмета уже нет в инвентаре (выставлен или заменён) — назад к списку
				local still = false
				for _, item in owned do
					if item.uid == (picking :: Card).uids[1] and item.slot == nil then
						still = true
					end
				end
				if not still then
					picking = nil
				end
			end
			render()
		end
	end)
	player:GetAttributeChangedSignal("Income"):Connect(function()
		if isOpen() then
			updateStats()
		end
	end)
	ContextActionService:BindAction("InventaireToggle", function(_, inputState)
		if inputState == Enum.UserInputState.Begin then
			toggle()
		end
		return Enum.ContextActionResult.Pass
	end, false, T.HotKey)
	-- Пока окно открыто, раз в Refresh секунд — проверка фазы (кнопки и причина запрета).
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		if not isOpen() then
			return
		end
		acc += dt
		if acc < T.Refresh then
			return
		end
		acc = 0
		if lockReason() ~= lastLock then
			updateLock()
		end
	end)
	-- Превью появляются по мере того, как сервер создаёт копии (первый предмет в инвентаре): перерисовать окно.
	task.spawn(function()
		local folder = ReplicatedStorage:WaitForChild("ItemPreviews")
		folder.ChildAdded:Connect(function(child)
			if not isOpen() or picking then
				return
			end
			for _, item in owned do
				if item.itemId == child.Name then
					render() -- пришло превью своего предмета (чужие не перерисовывают окно)
					return
				end
			end
		end)
	end)
end

return InventoryController

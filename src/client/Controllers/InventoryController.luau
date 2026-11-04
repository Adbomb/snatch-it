-- Окно «Инвентарь» (D46, Stud-UI D20): все предметы игрока карточками — 3D-превью (копия модели из
-- ReplicatedStorage.ItemPreviews), название, редкость, доход в секунду, локация происхождения, статус («В музее» с
-- номером постамента или «В инвентаре»), повторы одного предмета — «×N». Кнопка «Выставить» открывает выбор
-- постамента (свободный — «Поставить», занятый — «Заменить»), «Снять» возвращает экспонат в инвентарь. Сортировка
-- по доходу и редкости, фильтр по локации, поиск по названию, счётчики предметов, постаментов и дохода.
-- Подсказка постамента «Выставить из инвентаря» открывает окно сразу для этого постамента (OpenForSlot).
-- Клиент только показывает и просит: InventoryAction проверяет сервер; в подготовку, Судную ночь и 10 с доставки
-- кнопки неактивны и окно объясняет почему (Shared/GameTime.ExhibitLock — то же правило, что на сервере).
-- Зависит от Shared/StudUI, Shared/GameTime, Shared/NumberFormat, Remotes, Config/Items, Config/Rarities,
-- Config/GameConfig, Config/UITokens.

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local GameTime = require(Shared:WaitForChild("GameTime"))
local Items = require(Config:WaitForChild("Items"))
local NumberFormat = require(Shared:WaitForChild("NumberFormat"))
local Rarities = require(Config:WaitForChild("Rarities"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Config:WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))

local T = UITokens.Inventory
local player = Players.LocalPlayer

type Owned = { uid: string, itemId: string, slot: number?, pending: boolean? }
type Card = { itemId: string, uids: { string }, slot: number?, count: number, pending: boolean? }

local InventoryController = {}

local owned: { Owned } = {}
local sortMode = "Income" -- "Income" | "Rarity"
local origin: number? = nil -- фильтр: номер босса (локация), nil — все
local query = ""
local picking: Card? = nil -- выбран предмет — показан выбор постамента
local forSlot: number? = nil -- окно открыто с постамента: выбрать предмет для него

local gui: ScreenGui
local win: any
local menu: any
local corps: Frame
local statsText: TextLabel
local searchBox: TextBox
local sortBar: Frame
local grid: ScrollingFrame
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
	local q = string.lower(query)
	local out = {}
	for _, card in cards do
		local d = def(card.itemId)
		local fits = (origin == nil or d.boss == origin)
			and (q == "" or string.find(string.lower(d.displayName), q, 1, true) ~= nil)
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
local function preview(parent: GuiObject, itemId: string, size: Vector2, z: number)
	local folder = ReplicatedStorage:FindFirstChild("ItemPreviews")
	local source = folder and folder:FindFirstChild(itemId)
	if source and source:IsA("Model") then
		local view = Instance.new("ViewportFrame")
		view.Name = "Apercu"
		view.BackgroundTransparency = 1
		view.Size = UDim2.fromOffset(size.X, size.Y)
		view.Position = UDim2.fromScale(0.5, 0.5)
		view.AnchorPoint = Vector2.new(0.5, 0.5)
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
	dot.Size = UDim2.fromOffset(size.Y * 0.7, size.Y * 0.7)
	dot.Position = UDim2.fromScale(0.5, 0.5)
	dot.AnchorPoint = Vector2.new(0.5, 0.5)
	dot.BackgroundColor3 = Color3.new(1, 1, 1)
	dot.ZIndex = z
	UI.Corner(dot, math.floor(size.Y * 0.35))
	UI.Gradient(dot, rarityGradient(d.rarity), 90)
	UI.Stroke(dot, UI.Colors.SlotStroke, 3)
	UI.Text(dot, utf8.char(utf8.codepoint(d.displayName, 1)), { TextSize = 40, ZIndex = z + 1 })
	dot.Parent = parent
end

-- Тёмная карточка Stud-UI: полупрозрачный фон, рамка 3 px, светлая внутренняя линия.
local function slotFrame(parent: Instance, size: Vector2, order: number, accent: ColorSequence?): Frame
	local card = Instance.new("Frame")
	card.Name = "Carte"
	card.BackgroundColor3 = UI.Colors.Slot
	card.BackgroundTransparency = 0.35
	card.BorderSizePixel = 0
	card.Size = UDim2.fromOffset(size.X, size.Y)
	card.LayoutOrder = order
	card.ZIndex = 2
	UI.Stroke(card, UI.Colors.SlotStroke, 3, 0, nil, "Bord")
	local line = Instance.new("Frame")
	line.Name = "Lisere"
	line.BackgroundTransparency = 1
	line.Size = UDim2.new(1, -8, 1, -8)
	line.Position = UDim2.fromScale(0.5, 0.5)
	line.AnchorPoint = Vector2.new(0.5, 0.5)
	line.ZIndex = 2
	UI.Stroke(line, UI.Colors.SlotLine, 1.4, 0.15, nil, "Trait")
	line.Parent = card
	if accent then
		local band = Instance.new("Frame")
		band.Name = "Bande"
		band.BackgroundColor3 = Color3.new(1, 1, 1)
		band.BorderSizePixel = 0
		band.Size = UDim2.new(1, -6, 0, 6)
		band.Position = UDim2.fromOffset(3, 3)
		band.ZIndex = 3
		UI.Gradient(band, accent, 0)
		band.Parent = card
	end
	card.Parent = parent
	return card
end

local function actionButton(parent: Instance, text: string, theme: string, width: number, onClick: () -> ()): GuiButton
	local button = UI.Button(parent, {
		Name = "Action",
		Theme = theme,
		Size = Vector2.new(width, T.ButtonHeight),
		Position = UDim2.new(0.5, 0, 1, -(T.ButtonHeight / 2 + 10)),
		Text = text,
		TextSize = 24,
		ZIndex = 5,
	})
	Motion.BindButton(button, 1.05, nil, function()
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

local render: () -> ()

local function itemCard(card: Card, order: number)
	local d = def(card.itemId)
	local frame = slotFrame(grid, T.Card, order, rarityGradient(d.rarity))
	local w = T.Card.X
	UI.Text(frame, Rarities.Names[d.rarity] or d.rarity, {
		Name = "Rarete",
		Size = UDim2.fromOffset(w - 70, 24),
		Position = UDim2.fromOffset(12, 14),
		AnchorPoint = Vector2.zero,
		AlignX = Enum.TextXAlignment.Left,
		TextSize = T.InfoText,
		Gradient = rarityGradient(d.rarity),
		Stroke = UI.Colors.StrokeSlot,
		ZIndex = 6,
	})
	if card.count > 1 then
		UI.Text(frame, "×" .. card.count, {
			Name = "Quantite",
			Size = UDim2.fromOffset(60, 24),
			Position = UDim2.new(1, -12, 0, 14),
			AnchorPoint = Vector2.new(1, 0),
			AlignX = Enum.TextXAlignment.Right,
			TextSize = T.InfoText + 2,
			Color = UI.Colors.TagGold,
			Stroke = UI.Colors.StrokeSlot,
			ZIndex = 6,
		})
	end
	local holder = Instance.new("Frame")
	holder.Name = "Vitrine"
	holder.BackgroundTransparency = 1
	holder.Size = UDim2.new(1, -16, 0, T.Preview)
	holder.Position = UDim2.fromOffset(8, 40)
	holder.ZIndex = 3
	holder.Parent = frame
	preview(holder, card.itemId, Vector2.new(w - 16, T.Preview), 3)
	local y = 40 + T.Preview
	local name = UI.Text(frame, d.displayName, {
		Name = "Nom",
		Size = UDim2.new(1, -16, 0, 50),
		Position = UDim2.fromOffset(w / 2, y + 26),
		Max = T.NameText,
		Min = 16,
		Stroke = UI.Colors.StrokeSlot,
		Thickness = 2.6,
		ZIndex = 6,
	})
	name.TextWrapped = true
	UI.Text(frame, ("+%s/сек"):format(NumberFormat.Short(d.income or 0)), {
		Name = "Revenu",
		Font = "Gotham",
		Size = UDim2.new(1, -16, 0, 26),
		Position = UDim2.fromOffset(w / 2, y + 64),
		TextSize = T.IncomeText,
		Gradient = UI.TextGradients.Money,
		Stroke = Color3.fromRGB(15, 51, 0),
		ZIndex = 6,
	})
	UI.Text(frame, originName(card.itemId), {
		Name = "Origine",
		Font = "Bold",
		Size = UDim2.new(1, -16, 0, 22),
		Position = UDim2.fromOffset(w / 2, y + 88),
		Max = T.InfoText,
		Min = 14,
		Color = UI.Colors.Secondary,
		Stroke = UI.Colors.StrokeSlot,
		Thickness = 2,
		ZIndex = 6,
	})
	local status = if card.slot
		then ("В музее, место %d"):format(card.slot)
		elseif card.pending then "Передаётся…"
		else "В инвентаре"
	UI.Text(frame, status, {
		Name = "Statut",
		Font = "Bold",
		Size = UDim2.new(1, -16, 0, 22),
		Position = UDim2.fromOffset(w / 2, y + 110),
		Max = T.InfoText,
		Min = 14,
		Color = if card.slot then UI.Colors.Positive else UI.Colors.TagGold,
		Stroke = UI.Colors.StrokeSlot,
		Thickness = 2,
		ZIndex = 6,
	})
	if card.pending then
		return
	elseif card.slot then
		actionButton(frame, "Снять", "red", w - 40, function()
			send("Remove", card.uids[1])
		end)
	elseif forSlot then
		actionButton(frame, ("На постамент %d"):format(forSlot), "green", w - 30, function()
			local slot = forSlot :: number
			send("Display", card.uids[1], slot)
			menu.Close()
		end)
	else
		actionButton(frame, "Выставить", "green", w - 40, function()
			picking = card
			render()
		end)
	end
end

-- Выбор постамента для picking: свободный — «Поставить», занятый — «Заменить» (атомарно на сервере).
local function pedestalCard(slot: number, order: number)
	local occupant: Owned? = nil
	for _, item in owned do
		if item.slot == slot then
			occupant = item
		end
	end
	local frame = slotFrame(grid, T.Pedestal, order, nil)
	local w = T.Pedestal.X
	UI.Text(frame, ("Постамент %d"):format(slot), {
		Name = "Numero",
		Size = UDim2.new(1, -16, 0, 30),
		Position = UDim2.fromOffset(w / 2, 26),
		TextSize = T.NameText,
		Stroke = UI.Colors.StrokeSlot,
		ZIndex = 6,
	})
	local card = picking :: Card
	if occupant then
		local d = def(occupant.itemId)
		UI.Text(frame, ("%s · +%s/сек"):format(d.displayName, NumberFormat.Short(d.income or 0)), {
			Name = "Occupant",
			Font = "Bold",
			Size = UDim2.new(1, -16, 0, 24),
			Position = UDim2.fromOffset(w / 2, 60),
			Max = T.InfoText,
			Min = 12,
			Color = UI.Colors.Secondary,
			Stroke = UI.Colors.StrokeSlot,
			ZIndex = 6,
		})
		actionButton(frame, "Заменить", "orange", w - 40, function()
			send("Replace", card.uids[1], slot)
			picking = nil
			render()
		end)
	else
		UI.Text(frame, "Свободно", {
			Name = "Libre",
			Font = "Bold",
			Size = UDim2.new(1, -16, 0, 24),
			Position = UDim2.fromOffset(w / 2, 60),
			TextSize = T.InfoText,
			Color = UI.Colors.Positive,
			Stroke = UI.Colors.StrokeSlot,
			ZIndex = 6,
		})
		actionButton(frame, "Поставить", "green", w - 40, function()
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
	statsText.Text = (
		'Предметов: <font color="%s">%d</font>   Постаменты: <font color="%s">%d/%d</font>   '
		.. 'Доход: <font color="#60E87A">+%s/сек</font>'
	):format(
		UI.Colors.HighlightHex,
		#owned,
		UI.Colors.HighlightHex,
		displayed,
		slots,
		NumberFormat.Short(player:GetAttribute("Income") or 0)
	)
end

-- Кнопки сортировки и фильтра по локации (локации — только те, откуда у игрока есть предметы).
local function buildBar()
	for _, child in sortBar:GetChildren() do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
	local x = 0
	local function chip(text: string, active: boolean, width: number, onClick: () -> ())
		local button = UI.Button(sortBar, {
			Name = "Filtre",
			Style = "Chunky",
			Theme = if active then "blue" else "gray",
			Size = Vector2.new(width, 42),
			Position = UDim2.fromOffset(x + width / 2, 25),
			Text = text,
			TextSize = 20,
			ZIndex = 4,
		})
		Motion.BindButton(button, 1.05, nil, onClick)
		x += width + 8
	end
	if picking then
		chip("← Назад", false, 150, function()
			picking = nil
			render()
		end)
		UI.Text(sortBar, ("Куда поставить «%s»?"):format(def((picking :: Card).itemId).displayName), {
			Name = "Question",
			Size = UDim2.fromOffset(700, 40),
			Position = UDim2.fromOffset(x + 4, 25),
			AnchorPoint = Vector2.new(0, 0.5),
			AlignX = Enum.TextXAlignment.Left,
			Max = 26,
			ZIndex = 4,
		})
		return
	end
	chip("По доходу", sortMode == "Income", 150, function()
		sortMode = "Income"
		render()
	end)
	chip("По редкости", sortMode == "Rarity", 160, function()
		sortMode = "Rarity"
		render()
	end)
	x += 12
	local present: { [number]: boolean } = {}
	for _, item in owned do
		local boss = def(item.itemId).boss
		if boss then
			present[boss] = true
		end
	end
	chip("Все", origin == nil, 80, function()
		origin = nil
		render()
	end)
	for boss, zone in GameConfig.Zones do
		if present[boss] and x < T.Window.X - 180 then
			chip(zone.name, origin == boss, 150, function()
				origin = if origin == boss then nil else boss
				render()
			end)
		end
	end
end

render = function()
	if not win then
		return
	end
	if forSlot then
		win.Titre.Text = ("Постамент %d: что поставить?"):format(forSlot)
	else
		win.Titre.Text = "Инвентарь"
	end
	buildBar()
	clearGrid()
	local layout = grid:FindFirstChildOfClass("UIGridLayout") :: UIGridLayout
	if picking then
		layout.CellSize = UDim2.fromOffset(T.Pedestal.X, T.Pedestal.Y)
		local slots = player:GetAttribute("MuseumSlots") or GameConfig.Museum.SlotsByLevel[1]
		for slot = 1, slots do
			pedestalCard(slot, slot)
		end
	else
		layout.CellSize = UDim2.fromOffset(T.Card.X, T.Card.Y)
		local cards = buildCards()
		for order, card in cards do
			itemCard(card, order)
		end
		if #cards == 0 then
			layout.CellSize = UDim2.fromOffset(T.Window.X - 80, 90) -- пустое состояние — во всю ширину
			UI.Text(
				grid,
				if #owned == 0
					then "Пока пусто: победите босса и донесите добычу до сундука музея"
					else "Ничего не найдено",
				{
					Name = "Vide",
					Font = "Bold",
					Size = UDim2.fromOffset(T.Window.X - 80, 60),
					Max = 26,
					Color = UI.Colors.Secondary,
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
	gui = UI.ScreenGui("Inventaire", 12)
	gui.Enabled = false
	gui.Parent = player:WaitForChild("PlayerGui")
	win = UI.Window(gui, { Size = T.Window, Title = "Инвентарь", Header = T.Header, TitleWidth = 640 })
	corps = win.Corps
	local W = win.Width - 5
	local bar = T.BarHeight

	statsText = UI.Text(corps, "", {
		Name = "Compteurs",
		Size = UDim2.fromOffset(W - T.SearchWidth - 48, bar),
		Position = UDim2.fromOffset(18, 14 + bar / 2),
		AnchorPoint = Vector2.new(0, 0.5),
		AlignX = Enum.TextXAlignment.Left,
		Max = 22,
		Rich = true,
		ZIndex = 4,
	})
	local searchFrame = UI.InsetBox(corps, {
		Name = "Recherche",
		Size = UDim2.fromOffset(T.SearchWidth, bar - 6),
		Position = UDim2.new(1, -18, 0, 14 + bar / 2),
		AnchorPoint = Vector2.new(1, 0.5),
		ZIndex = 4,
	})
	searchBox = Instance.new("TextBox")
	searchBox.Name = "Saisie"
	searchBox.BackgroundTransparency = 1
	searchBox.Size = UDim2.new(1, -24, 1, 0)
	searchBox.Position = UDim2.fromOffset(12, 0)
	searchBox.FontFace = UI.Fonts.Bold
	searchBox.TextSize = 22
	searchBox.TextColor3 = Color3.new(1, 1, 1)
	searchBox.PlaceholderText = "Поиск по названию"
	searchBox.PlaceholderColor3 = UI.Colors.Secondary
	searchBox.TextXAlignment = Enum.TextXAlignment.Left
	searchBox.ClearTextOnFocus = false
	searchBox.Text = ""
	searchBox.ZIndex = 6
	searchBox.Parent = searchFrame
	searchBox:GetPropertyChangedSignal("Text"):Connect(function()
		query = searchBox.Text
		if not picking then
			render()
		end
	end)

	sortBar = Instance.new("Frame")
	sortBar.Name = "Tri"
	sortBar.BackgroundTransparency = 1
	sortBar.Size = UDim2.fromOffset(W - 36, bar)
	sortBar.Position = UDim2.fromOffset(18, 14 + bar + 8)
	sortBar.ZIndex = 4
	sortBar.Parent = corps

	local top = 14 + bar * 2 + 18
	grid = UI.ScrollList(corps, {
		Name = "Grille",
		Size = UDim2.fromOffset(W - 8, corps.Size.Y.Offset - top - 8),
		Position = UDim2.fromOffset(4, top),
		Grid = T.Card,
		GridGap = T.Gap,
		PadTop = 6,
		PadLeft = 18,
		PadBottom = 70,
		ZIndex = 3,
	})

	lockPill = UI.Pill(corps, "", {
		Name = "Verrou",
		Width = W - 120,
		Height = 40,
		TextSize = 20,
		Position = UDim2.new(0.5, 0, 1, -34),
		ZIndex = 30,
	})
	lockText = lockPill:FindFirstChild("Texte") :: TextLabel
	lockText.TextColor3 = UI.Colors.Danger
	lockPill.Visible = false

	menu = Motion.Window(gui, win.Fenetre, { Keep = { Toasts = true, Inventaire = true } })
	Motion.BindButton(win.Fermer, 1.06, nil, function()
		menu.Close()
	end)
end

local function open(slot: number?)
	forSlot = slot
	picking = nil
	render()
	menu.Open()
end

-- Открыть окно (из HUD или клавишей).
function InventoryController.Open()
	open(nil)
end

-- Окно для своего пустого постамента slot (подсказка «Выставить из инвентаря»).
function InventoryController.OpenForSlot(slot: number)
	open(slot)
end

-- Кнопка «Инвентарь» в HUD: слева посередине (выше столбика монет, не под джойстиком телефона).
local function buildHud()
	local hud = UI.ScreenGui("InventaireHud", 4, { Menu = false })
	hud.Parent = player:WaitForChild("PlayerGui")
	local holder = Instance.new("Frame")
	holder.Name = "Racine"
	holder.BackgroundTransparency = 1
	holder.Size = UDim2.fromOffset(T.Hud.X, T.Hud.Y)
	holder.Position = T.HudPosition
	holder.AnchorPoint = Vector2.new(0, 0.5)
	holder.Parent = hud
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = holder
	Motion.BindResponsive(scale)
	local button = UI.Button(holder, {
		Name = "Inventaire",
		Theme = "blue",
		Size = T.Hud,
		Position = UDim2.fromScale(0.5, 0.5),
		Text = "Инвентарь",
		TextSize = 26,
	})
	Motion.BindButton(button, 1.04, nil, function()
		if menu.IsOpen then
			menu.Close()
		else
			InventoryController.Open()
		end
	end)
end

function InventoryController.Init()
	build()
	buildHud()
	Remotes.Get(Remotes.Names.InventoryChanged).OnClientEvent:Connect(function(list: { Owned })
		owned = list
		if menu.IsOpen then
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
		if menu.IsOpen then
			updateStats()
		end
	end)
	ContextActionService:BindAction("InventaireToggle", function(_, inputState)
		if inputState == Enum.UserInputState.Begin then
			if menu.IsOpen then
				menu.Close()
			else
				InventoryController.Open()
			end
		end
		return Enum.ContextActionResult.Pass
	end, false, T.HotKey)
	-- Пока окно открыто, раз в Refresh секунд — проверка фазы (кнопки и причина запрета).
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		if not menu.IsOpen then
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
		folder.ChildAdded:Connect(function()
			if menu.IsOpen and not picking then
				render()
			end
		end)
	end)
end

return InventoryController

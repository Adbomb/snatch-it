-- Обучение новичка на клиенте (D55, Stud-UI): панель задачи слева сверху («Обучение · шаг N из 5» и что сделать;
-- во время поимки её нет — там своя подсказка), жёлтая линия от игрока к цели (Beam) и метка над целью; шаг и цель
-- присылает сервер (TutorialChanged) — клиент только показывает; после возрождения линия строится от нового
-- персонажа. Учебные существо и пёс других учеников (атрибут TutorialOwner ≠ мой UserId) у меня спрятаны: детали
-- невидимы и не твёрдые, подсказки и подписи выключены. Пока идёт обучение (атрибут Tutorial), кнопки «Защита» в меню
-- HUD нет («Магазин» прячет ShopController, «Музей» — MuseumUpgradeController). ПК и телефон: панель — одна WindowScale, текст переносится; на узком
-- телефоне панель кончается до таймера дня и становится выше (текст не мельче MinText); на низком экране столбик монет
-- и силы (GymHud, середина высоты) налез бы на панель — пока идёт обучение, он опускается под неё (на ПК и планшете
-- места хватает — всё на своих местах).
-- Зависит от Shared/StudUI, Remotes, Config/UITokens, UI/HudLayout.

local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextService = game:GetService("TextService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Remotes = require(Shared:WaitForChild("Remotes"))
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local HudLayout = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudLayout"))

local T = UITokens.Tutorial
local player = Players.LocalPlayer

local TutorialController = {}

local TEXTS = {
	Intro = "Идите на уровень 1 «Свалка» по жёлтой линии — там ждёт учебное существо",
	Catch = "Нажмите «Поймать» у существа и бросьте Ловибум жестом вверх. Первое попадание — поймано!",
	Battle = "Учебный бой с псом: стойте рядом — удары идут сами",
	Carry = "Несите существо в свой музей и поставьте на свободный постамент",
	Income = "Отлично! Экспонат на месте — ждём первый доход…",
}
local ORDER = { Intro = 1, Catch = 2, Battle = 3, Carry = 4, Income = 5 }

local gui: ScreenGui
local panel: Frame
local title: TextLabel
local body: TextLabel
local beam: Beam? = nil
local from: Attachment? = nil
local to: Attachment? = nil
local marker: BillboardGui? = nil

local function clearGuide()
	if beam then
		beam:Destroy()
		beam = nil
	end
	if to then
		to:Destroy()
		to = nil
	end
	if marker then
		marker:Destroy()
		marker = nil
	end
end

local function guide(target: Instance?)
	clearGuide()
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not target or not target:IsA("BasePart") or not root then
		return
	end
	if not from or from.Parent ~= root then
		if from then
			from:Destroy()
		end
		local a = Instance.new("Attachment")
		a.Name = "TutorialFrom"
		a.Parent = root
		from = a
	end
	local a1 = Instance.new("Attachment")
	a1.Name = "TutorialTo"
	a1.Position = Vector3.new(0, (target :: BasePart).Size.Y / 2 + 0.5, 0)
	a1.Parent = target
	to = a1
	local b = Instance.new("Beam")
	b.Name = "TutorialGuide"
	b.Attachment0 = from
	b.Attachment1 = a1
	b.Color = ColorSequence.new(T.Guide)
	b.Width0, b.Width1 = T.GuideWidth, T.GuideWidth
	b.FaceCamera = true
	b.LightEmission = 0.6
	b.Transparency = NumberSequence.new(T.GuideTransparency)
	b.Segments = 1
	b.Parent = a1
	beam = b
	local m = Instance.new("BillboardGui")
	m.Name = "TutorialMarker"
	m.Size = UDim2.fromOffset(T.Marker, T.Marker)
	m.StudsOffsetWorldSpace = Vector3.new(0, (target :: BasePart).Size.Y / 2 + 2.5, 0)
	m.AlwaysOnTop = true
	m.Adornee = target :: BasePart
	UI.Text(m, "▼", { Name = "Fleche", TextSize = T.Marker - 8, Color = T.Guide })
	m.Parent = gui
	marker = m
end

local last: any = nil
local fitPanel: () -> () -- размер панели по экрану и тексту (ниже)

local function render(payload: any)
	last = payload
	local step = payload and payload.step
	local active = type(step) == "string" and step ~= "Done" and TEXTS[step] ~= nil
	local catching = player:GetAttribute("Catching") ~= nil
	gui.Enabled = active and not catching
	if not active or catching then
		clearGuide() -- на экране поимки линии и метки нет (там свой прицел)
		return
	end
	title.Text = ("Обучение · шаг %d из 5"):format(ORDER[step])
	if body.Text ~= TEXTS[step] then
		body.Text = TEXTS[step]
		task.spawn(fitPanel)
	end
	guide(if typeof(payload.target) == "Instance" then payload.target else nil)
end

-- Чужие учебные модели — невидимы и неактивны у меня: не твёрдые (существо по своему месту двигает CreatureController,
-- невидимый хитбокс иначе толкал бы меня), лучи сквозь них.
local function hideForeign(d: Instance)
	local owner = d:GetAttribute("TutorialOwner")
	if owner == nil or owner == player.UserId then
		return
	end
	local function apply(x: Instance)
		if x:IsA("BasePart") then
			x.LocalTransparencyModifier = 1
			x.CanCollide = false
			x.CanQuery = false
			x.CanTouch = false
		elseif x:IsA("ProximityPrompt") or x:IsA("BillboardGui") then
			(x :: any).Enabled = false
		end
	end
	apply(d)
	for _, x in d:GetDescendants() do
		apply(x)
	end
	d.DescendantAdded:Connect(apply)
end

-- Экран (px) и его масштаб (StudMotion). В Studio (GameConfig.DevMode) экран подменяет атрибут игрока DevViewport
-- (Vector2) — раскладка телефона считается тем же кодом без эмулятора (как в InventoryController).
local function screen(): (Vector2, number)
	local fake = GameConfig.DevMode and player:GetAttribute("DevViewport")
	local view = if typeof(fake) == "Vector2" then fake else workspace.CurrentCamera.ViewportSize
	local s = math.clamp(
		math.min(view.X / Motion.REFERENCE.X, view.Y / Motion.REFERENCE.Y),
		Motion.MIN_SCALE,
		Motion.MAX_SCALE
	)
	return view, s
end

-- Столбик монет и силы (GymHud.Stats, UITokens.StatsHud): пока идёт обучение и он по своему месту налез бы на панель
-- (низкий экран) — под панелью; иначе — на своём месте.
local function placeStats()
	local pg = player:FindFirstChild("PlayerGui")
	local hud = pg and pg:FindFirstChild("GymHud")
	local stats = hud and hud:FindFirstChild("Stats")
	if not stats or not stats:IsA("GuiObject") then
		return
	end
	local S = UITokens.StatsHud
	local view, s = screen()
	-- px от верха экрана (GymHud — без отступа под кнопками Roblox, панель — под ними); высота столбика — его строки
	local rows = S.Rows.Coins.icon + S.Rows.Income.icon + S.Rows.Strength.icon + 2 * S.Gap
	local below = GuiService:GetGuiInset().Y + T.Top + panel.Size.Y.Offset * s + T.Gap
	local top = S.Y * view.Y - rows * s / 2
	if player:GetAttribute("Tutorial") ~= nil and top < below then
		stats.AnchorPoint = Vector2.zero
		stats.Position = UDim2.fromOffset(S.Margin, below)
	else
		stats.AnchorPoint = Vector2.new(0, 0.5)
		stats.Position = UDim2.new(0, S.Margin, S.Y, 0)
	end
end

-- Размер панели: обычный; если слева от таймера дня места меньше (узкий телефон) — уже и выше, чтобы текст шага
-- поместился не мельче MinText. Потом — столбик монет (placeStats).
local fitToken = 0
fitPanel = function()
	fitToken += 1
	local token = fitToken
	local view, s = screen()
	local room = view.X / 2 - UITokens.TimeHud.Size.X / 2 * s - T.Gap - T.Left -- до капсулы таймера (по центру)
	local width = math.min(T.Panel.X, room / s)
	local height = T.Panel.Y
	if width < T.Panel.X and body.Text ~= "" then
		local params = Instance.new("GetTextBoundsParams")
		params.Text = body.Text
		params.Font = body.FontFace
		params.Size = T.MinText -- ограничение размера текста — в пикселях экрана
		params.Width = (width - T.BodyPad.X) * s
		local ok, bounds = pcall(TextService.GetTextBoundsAsync, TextService, params)
		if token ~= fitToken then
			return -- пока считали, пришёл новый шаг или размер экрана
		end
		if ok then
			-- запас полстроки: без него последняя строка не влезала из-за округления (TextFits = false)
			height = math.max(T.Panel.Y, (bounds.Y + T.MinText / 2) / s + T.BodyTop + T.BodyPad.Y)
		end
	end
	panel.Size = UDim2.fromOffset(width, height)
	placeStats()
end

local function updateMenu()
	local hud = player:FindFirstChild("PlayerGui") and player.PlayerGui:FindFirstChild("MenuHud")
	local defense = hud and hud:FindFirstChild("Defense", true)
	if defense and defense:IsA("GuiObject") then
		defense.Visible = player:GetAttribute("Tutorial") == nil
	end
end

function TutorialController.Init()
	gui = UI.ScreenGui("Tutoriel", 9, { Menu = false, ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets })
	gui.Enabled = false
	gui.Parent = player:WaitForChild("PlayerGui")
	panel = Instance.new("Frame")
	panel.Name = "Panneau"
	panel.BackgroundTransparency = 1
	panel.Size = UDim2.fromOffset(T.Panel.X, T.Panel.Y)
	panel.AnchorPoint = Vector2.zero
	panel.Position = UDim2.fromOffset(T.Left, T.Top)
	panel.Parent = gui
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = panel
	Motion.BindResponsive(scale)
	local box = UI.InsetBox(panel, { Size = UDim2.fromScale(1, 1), Transparency = 0.12 })
	title = UI.Text(box, "", {
		Name = "Titre",
		Size = UDim2.new(1, -24, 0, T.TitleText + 6),
		Position = UDim2.new(0.5, 0, 0, 8 + T.TitleText / 2),
		TextSize = T.TitleText,
		Color = T.Guide,
		ZIndex = 6,
	})
	body = UI.Text(box, "", {
		Name = "Tache",
		Font = "Bold",
		-- под заголовком до низа панели (панель на узком телефоне выше — текст растягивается с ней)
		Size = UDim2.new(1, -T.BodyPad.X, 1, -(T.BodyTop + T.BodyPad.Y)),
		Position = UDim2.fromOffset(T.BodyPad.X / 2, T.BodyTop),
		AnchorPoint = Vector2.zero,
		Max = T.BodyText,
		Min = T.MinText,
		ZIndex = 6,
	})
	body.TextWrapped = true
	Remotes.Get(Remotes.Names.TutorialChanged).OnClientEvent:Connect(render)
	player:GetAttributeChangedSignal("Tutorial"):Connect(function()
		updateMenu()
		placeStats()
	end)
	task.spawn(function()
		local hud = player:WaitForChild("PlayerGui"):WaitForChild("GymHud", 30)
		local stats = hud and hud:WaitForChild("Stats", 10)
		if stats and stats:IsA("GuiObject") then
			stats:GetPropertyChangedSignal("AbsoluteSize"):Connect(placeStats) -- масштаб по экрану, число строк
		end
	end)
	HudLayout.Track(function()
		task.defer(fitPanel) -- после пересчёта масштаба (BindResponsive); fitPanel ставит и столбик монет
	end)
	player:GetAttributeChangedSignal("DevViewport"):Connect(fitPanel)
	player:GetAttributeChangedSignal("Catching"):Connect(function()
		render(last)
	end)
	task.defer(updateMenu)
	-- новый персонаж (возрождение; первый вход, если шаг пришёл раньше персонажа) — линия от него заново
	player.CharacterAdded:Connect(function(character)
		from = nil
		if character:WaitForChild("HumanoidRootPart", 10) and player.Character == character then
			render(last)
		end
	end)
	for _, d in workspace:GetDescendants() do
		if d:GetAttribute("TutorialOwner") ~= nil then
			hideForeign(d)
		end
	end
	workspace.DescendantAdded:Connect(function(d)
		task.defer(function()
			if d.Parent and d:GetAttribute("TutorialOwner") ~= nil then
				hideForeign(d)
			end
		end)
	end)
end

return TutorialController

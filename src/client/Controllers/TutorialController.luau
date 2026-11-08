-- Обучение новичка на клиенте (D55, Stud-UI): панель задачи сверху («Обучение · шаг N из 5» и что сделать), жёлтая
-- линия от игрока к цели (Beam) и метка над целью; шаг и цель присылает сервер (TutorialChanged) — клиент только
-- показывает. Учебные существо и пёс других учеников (атрибут TutorialOwner ≠ мой UserId) у меня спрятаны: детали
-- невидимы, подсказки и подписи выключены. Пока идёт обучение (атрибут Tutorial), кнопки «Защита» в меню HUD нет
-- («Магазин» прячет ShopController). ПК и телефон: панель — одна WindowScale, текст переносится.
-- Зависит от Shared/StudUI, Remotes, Config/UITokens.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))

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

local function render(payload: any)
	local step = payload and payload.step
	local active = type(step) == "string" and step ~= "Done" and TEXTS[step] ~= nil
	gui.Enabled = active
	if not active then
		clearGuide()
		return
	end
	title.Text = ("Обучение · шаг %d из 5"):format(ORDER[step])
	body.Text = TEXTS[step]
	guide(if typeof(payload.target) == "Instance" then payload.target else nil)
end

-- Чужие учебные модели — невидимы и неактивны у меня.
local function hideForeign(d: Instance)
	local owner = d:GetAttribute("TutorialOwner")
	if owner == nil or owner == player.UserId then
		return
	end
	local function apply(x: Instance)
		if x:IsA("BasePart") then
			x.LocalTransparencyModifier = 1
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

local function updateMenu()
	local hud = player:FindFirstChild("PlayerGui") and player.PlayerGui:FindFirstChild("MenuHud")
	local defense = hud and hud:FindFirstChild("Defense", true)
	if defense and defense:IsA("GuiObject") then
		defense.Visible = player:GetAttribute("Tutorial") == nil
	end
end

function TutorialController.Init()
	gui = UI.ScreenGui("Tutoriel", 9, { Menu = false })
	gui.Enabled = false
	gui.Parent = player:WaitForChild("PlayerGui")
	local panel = Instance.new("Frame")
	panel.Name = "Panneau"
	panel.BackgroundTransparency = 1
	panel.Size = UDim2.fromOffset(T.Panel.X, T.Panel.Y)
	panel.AnchorPoint = Vector2.new(0.5, 0)
	panel.Position = UDim2.new(0.5, 0, 0, T.Top)
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
		Size = UDim2.new(1, -28, 1, -(T.TitleText + 18)),
		Position = UDim2.new(0.5, 0, 1, -(T.Panel.Y - T.TitleText - 14) / 2 - 6),
		Max = T.BodyText,
		Min = T.MinText,
		ZIndex = 6,
	})
	body.TextWrapped = true
	Remotes.Get(Remotes.Names.TutorialChanged).OnClientEvent:Connect(render)
	player:GetAttributeChangedSignal("Tutorial"):Connect(updateMenu)
	task.defer(updateMenu)
	player.CharacterAdded:Connect(function()
		from = nil -- новая точка у нового персонажа (линия — при следующем шаге)
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

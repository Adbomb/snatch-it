-- Пока игрок что-то несёт (вид — по референсу владельца 2026-11-17): у нижнего края по центру — тёмный полупрозрачный
-- скруглённый слот с 3D-видом предмета (как слоты инструментов на референсе), правее — название цветом редкости и
-- красная плоская кнопка «Бросить» (на ПК — значок клавиши G). Персонажа не закрывает; стоит между силой и монетами
-- слева и таймером справа (UI/HudLayout.BottomBand), по центру экрана, если помещается; на самом узком телефоне,
-- где блоку места нет, слот убирается — остаются название и кнопка.
-- Отправляет серверу только намерение «брось», без аргументов.
-- Зависит от Remotes, Config/Items, Config/UITokens, Shared/StudUI, Shared/HudMath, UI/HudLayout; вид предмета —
-- ReplicatedStorage.ItemPreviews (те же модели, что в инвентаре) или сама ноша над головой.

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Items = require(Shared:WaitForChild("Config"):WaitForChild("Items"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local HudLayout = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudLayout"))
local HudMath = require(Shared:WaitForChild("HudMath"))

local ACTION_NAME = "SnatchDropItem"
local T = UITokens.CarryHud

local CarryController = {}

-- Что показать в слоте: копия предмета из ItemPreviews (есть у предметов из инвентарей) или внешний вид самой ноши —
-- детали предмета, приваренной к корню персонажа (CarryService). Возвращает модель и её «лицо» (CFrame), nil — пока
-- ни того, ни другого нет (сварка ещё не пришла).
local function source(player: Player, itemId: string): (Model?, CFrame?)
	local folder = ReplicatedStorage:FindFirstChild("ItemPreviews")
	local ready = folder and folder:FindFirstChild(itemId)
	if ready and ready:IsA("Model") then
		local model = ready:Clone()
		return model, (model:GetBoundingBox())
	end
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not root or not root:IsA("BasePart") then
		return nil, nil
	end
	for _, joint in root:GetJoints() do
		if joint:IsA("WeldConstraint") then
			local other = if joint.Part0 == root then joint.Part1 else joint.Part0
			local visual = other and other:GetAttribute("ItemId") == itemId and other:FindFirstChild("Visual")
			if other and visual then
				local model = Instance.new("Model")
				local copy = visual:Clone()
				copy.Parent = model
				for _, d in model:GetDescendants() do -- в слоте нужен только внешний вид
					if
						d:IsA("LayerCollector")
						or d:IsA("ProximityPrompt")
						or d:IsA("ParticleEmitter")
						or d:IsA("Beam")
					then
						d:Destroy()
					end
				end
				local cf = model:GetBoundingBox()
				return model, CFrame.new(cf.Position) * other.CFrame.Rotation
			end
		end
	end
	return nil, nil
end

-- 3D-вид предмета в слоте (ViewportFrame); пока его нет — первая буква названия. true — вид собран.
local function preview(slot: Frame, player: Player, itemId: string, displayName: string): boolean
	local old = slot:FindFirstChild("Apercu")
	if old then
		old:Destroy()
	end
	local model, face = source(player, itemId)
	if model and face then
		local view = Instance.new("ViewportFrame")
		view.Name = "Apercu"
		view.BackgroundTransparency = 1
		view.Size = UDim2.new(1, -8, 1, -8)
		view.Position = UDim2.fromScale(0.5, 0.5)
		view.AnchorPoint = Vector2.new(0.5, 0.5)
		view.Ambient = Color3.fromRGB(165, 165, 175)
		view.LightColor = Color3.new(1, 1, 1)
		view.LightDirection = Vector3.new(-0.6, -1, -0.8)
		view.ZIndex = 5
		model.Parent = view
		local _, box = model:GetBoundingBox()
		local camera = Instance.new("Camera")
		camera.FieldOfView = 30
		local distance = box.Magnitude / 2 / math.sin(math.rad(camera.FieldOfView / 2)) * 1.05
		-- лицо модели смотрит в −Z: камера — спереди, чуть сбоку и сверху
		local dir = face:VectorToWorldSpace(CFrame.Angles(0, math.rad(T.Turn), 0) * Vector3.new(0, 0.35, -1).Unit)
		camera.CFrame = CFrame.lookAt(face.Position + dir * distance, face.Position)
		camera.Parent = view
		view.CurrentCamera = camera
		view.Parent = slot
		return true
	end
	local letter =
		UI.Text(slot, utf8.char(utf8.codepoint(displayName, 1)), { Name = "Apercu", TextSize = 34, ZIndex = 5 })
	letter.Size = UDim2.fromScale(1, 1)
	return false
end

function CarryController.Init()
	local player = Players.LocalPlayer
	local dropRemote = Remotes.Get(Remotes.Names.DropItem)
	local gui = UI.ScreenGui("CarryHud", 4, { Menu = false })
	gui.Parent = player:WaitForChild("PlayerGui")

	local width = T.Slot + T.Gap + T.Side
	local row = Instance.new("Frame")
	row.Name = "Rangee"
	row.BackgroundTransparency = 1
	row.AnchorPoint = Vector2.new(0.5, 1)
	row.Size = UDim2.fromOffset(width, T.Slot)
	row.Visible = false
	row.Parent = gui
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = row

	local slot = UI.InsetBox(row, { Name = "Slot", Size = UDim2.fromOffset(T.Slot, T.Slot) })
	local side = Instance.new("Frame")
	side.Name = "Cote"
	side.BackgroundTransparency = 1
	side.Position = UDim2.fromOffset(T.Slot + T.Gap, 0)
	side.Size = UDim2.fromOffset(T.Side, T.Slot)
	side.Parent = row
	local nameHeight = T.Slot - T.Button.Y
	local name = UI.Text(side, "", {
		Name = "Nom",
		Size = UDim2.new(1, 0, 0, nameHeight),
		Position = UDim2.new(),
		AnchorPoint = Vector2.zero,
		AlignX = Enum.TextXAlignment.Left,
		Max = T.NameText,
		Min = T.MinText,
		Stroke = UI.Flat.Stroke,
		Thickness = 2,
		ZIndex = 6,
	})
	-- одна строка: длинное название становится мельче, а не переносится (перенос выключается до TextScaled, иначе
	-- масштабирование по одной строке не включается)
	name.TextScaled = false
	name.TextWrapped = false
	name.TextScaled = true
	local nameLimit = name:FindFirstChildOfClass("UITextSizeConstraint") :: UITextSizeConstraint
	local rarityColor = Instance.new("UIGradient")
	rarityColor.Rotation = 90
	rarityColor.Parent = name

	local dropButton = UI.Button(side, {
		Name = "Button",
		Theme = "red",
		Size = T.Button,
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Text = "Бросить",
		FixedTextSize = T.ButtonText,
	})
	Motion.BindButton(dropButton, 1.05, nil, function()
		dropRemote:FireServer()
	end)
	local key = Instance.new("Frame")
	key.Name = "Touche"
	key.BackgroundColor3 = UI.Colors.White
	key.Size = UDim2.fromOffset(T.KeySize, T.KeySize)
	key.AnchorPoint = Vector2.new(0.5, 0.5)
	key.Position = UDim2.new(1, -3, 0, 3)
	key.ZIndex = 12
	key.Visible = false
	key.Parent = dropButton
	UI.Corner(key, 5)
	UI.Stroke(key, UI.Flat.Stroke, 2)
	UI.Text(key, "G", {
		Name = "Texte",
		TextSize = T.KeySize - 7,
		ZIndex = 13,
		Color = UI.Flat.Stroke,
		Thickness = 0,
	})

	HudLayout.Track(function()
		local left, right = HudLayout.BottomBand()
		local screen, hud = gui.AbsoluteSize.X, HudLayout.Scale()
		local center, s = HudMath.Fit(width, screen, left, right, hud)
		local compact = s < hud * T.MinFull -- самый узкий телефон: без слота, колонка — по ширине кнопки
		if compact then
			center, s = HudMath.Fit(T.Button.X, screen, left, right, hud)
		end
		slot.Visible = not compact
		side.Position = UDim2.fromOffset(if compact then 0 else T.Slot + T.Gap, 0)
		side.Size = UDim2.fromOffset(if compact then T.Button.X else T.Side, T.Slot)
		row.Size = UDim2.fromOffset(if compact then T.Button.X else width, T.Slot)
		-- предел размера текста задаётся в px экрана (UITextSizeConstraint не знает про UIScale): считаем его сами
		nameLimit.MaxTextSize = math.max(T.MinText, math.floor(T.NameText * s + 0.5))
		scale.Scale = s
		row.Position = UDim2.new(0, math.floor(center), 1, -T.Bottom)
	end)

	local function onAction(_, inputState: Enum.UserInputState)
		if inputState == Enum.UserInputState.Begin then
			dropRemote:FireServer()
		end
		return Enum.ContextActionResult.Sink
	end

	local shown: string? = nil
	local function refresh()
		ContextActionService:UnbindAction(ACTION_NAME)
		local itemId = player:GetAttribute("CarryingItemId")
		local def = if type(itemId) == "string" then Items[itemId] else nil
		row.Visible = def ~= nil
		if not def then
			shown = nil
			return
		end
		-- D55: учебное существо бросить нельзя (сервер откажет) — кнопки нет, пока его несут к постаменту
		local canDrop = player:GetAttribute("Tutorial") ~= "Carry"
		dropButton.Visible = canDrop
		-- на клавиатуре подсказываем клавишу; экранная кнопка нужна и на телефоне, и на ПК
		key.Visible = UserInputService.KeyboardEnabled
		ContextActionService:BindAction(ACTION_NAME, onAction, false, Enum.KeyCode.G)
		name.Text = def.displayName
		local colors = UITokens.Rarity[def.rarity] or UITokens.Rarity.Common
		rarityColor.Color = ColorSequence.new(colors.top, colors.bottom)
		if shown ~= itemId then -- вид предмета собирается один раз на ношу, а не при каждом обновлении
			shown = itemId
			if not preview(slot, player, itemId, def.displayName) then
				-- сварка ноши с персонажем ещё не пришла: несколько повторов, пока несут тот же предмет
				task.spawn(function()
					for _ = 1, T.PreviewTries do
						task.wait(T.PreviewWait)
						if shown ~= itemId or player:GetAttribute("CarryingItemId") ~= itemId then
							return
						end
						if preview(slot, player, itemId, def.displayName) then
							return
						end
					end
				end)
			end
		end
	end

	player:GetAttributeChangedSignal("CarryingItemId"):Connect(refresh)
	player:GetAttributeChangedSignal("Tutorial"):Connect(refresh)
	refresh()
end

return CarryController

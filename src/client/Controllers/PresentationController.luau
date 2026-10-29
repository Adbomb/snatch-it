-- Презентация экспоната после размещения (UI_KIT.md): Common/Uncommon — только уведомление сервера;
-- Rare/Legendary/Secret — прожектор на витрину и крупное название с плашкой редкости над экспонатом.
-- Владелец дополнительно видит баннер на экране, подъём-вращение экспоната и слышит звук (если задан).
-- Всё создаётся только на этом клиенте. Зависит от Remotes, Items, GameConfig, UIKit, UITokens.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local Items = require(Shared:WaitForChild("Config"):WaitForChild("Items"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UIKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UIKit"))

type Payload = { itemId: string, slot: number, plot: number }

local EXHIBIT_WAIT = 1 -- секунд ждём, пока Part экспоната дойдёт до клиента
local SOUND_LIFETIME = 10 -- секунд до удаления объекта Sound после запуска

local player = Players.LocalPlayer
local gui: ScreenGui

local PresentationController = {}

local function findPlot(index: number): Model?
	local world = workspace:FindFirstChild("World")
	local plots = world and world:FindFirstChild("Plots")
	for _, plot in if plots then plots:GetChildren() else {} do
		if plot:GetAttribute("PlotIndex") == index then
			return plot :: Model
		end
	end
	return nil
end

local function findExhibit(plot: Model, slot: number): BasePart?
	local deadline = os.clock() + EXHIBIT_WAIT
	repeat
		local exhibits = plot:FindFirstChild("Exhibits")
		for _, part in if exhibits then exhibits:GetChildren() else {} do
			if part:IsA("BasePart") and part:GetAttribute("Slot") == slot then
				return part
			end
		end
		task.wait()
	until os.clock() > deadline
	return nil
end

local function playSound(soundId: string)
	if soundId == "" then
		return
	end
	local sound = Instance.new("Sound")
	sound.SoundId = soundId
	SoundService:PlayLocalSound(sound)
	task.delay(SOUND_LIFETIME, sound.Destroy, sound)
end

-- Прожектор цветом редкости: SpotLight в лампе над витриной (Lamps/Lamp_<slot>/Bulb/PresentationLight).
-- Если лампы нет — временный прожектор над витриной. Возвращает функцию, которая всё возвращает как было.
local function addSpotlight(plot: Model, showcase: BasePart, slot: number, rarity: string): () -> ()
	local cfg = GameConfig.Presentation
	local lamps = plot:FindFirstChild("Lamps")
	local lamp = lamps and lamps:FindFirstChild("Lamp_" .. slot)
	local bulb = lamp and lamp:FindFirstChild("Bulb")
	local light = bulb and bulb:FindFirstChild("PresentationLight")
	if light and light:IsA("SpotLight") then
		light.Color = UITokens.RarityColor(rarity)
		light.Range = cfg.LightRange
		light.Angle = cfg.LightAngle
		light.Brightness = cfg.LightBrightness
		light.Shadows = true
		light.Enabled = true
		return function()
			light.Enabled = false
		end
	end
	local attachment = Instance.new("Attachment")
	attachment.Name = "PresentationLight"
	attachment.Position = Vector3.new(0, showcase.Size.Y / 2 + cfg.LightHeight, 0)
	local spot = Instance.new("SpotLight")
	spot.Face = Enum.NormalId.Bottom
	spot.Color = UITokens.RarityColor(rarity)
	spot.Range = cfg.LightRange
	spot.Angle = cfg.LightAngle
	spot.Brightness = cfg.LightBrightness
	spot.Shadows = true
	spot.Parent = attachment
	attachment.Parent = showcase
	return function()
		attachment:Destroy()
	end
end

-- Крупное название и плашка редкости над экспонатом (BillboardGui в PlayerGui, Adornee — экспонат).
local function addTitle(adornee: BasePart, def: Items.ItemDef): Instance
	local cfg = GameConfig.Presentation
	local billboard = Instance.new("BillboardGui")
	billboard.Name = "PresentationTitle"
	billboard.Adornee = adornee
	billboard.Size = cfg.TitleSize
	billboard.StudsOffset = Vector3.new(0, adornee.Size.Y / 2 + cfg.TitleHeight, 0)
	billboard.MaxDistance = cfg.TitleMaxDistance
	billboard.AlwaysOnTop = true
	billboard.ResetOnSpawn = false

	local layout = Instance.new("UIListLayout")
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = billboard
	UIKit.Text({
		text = def.displayName,
		textSize = UITokens.TextSize.Huge,
		color = UITokens.RarityColor(def.rarity),
		parent = billboard,
		size = UDim2.fromScale(1, 0.62),
		layoutOrder = 1,
	})
	UIKit.RarityTag(def.rarity, { parent = billboard, size = UDim2.fromScale(0.55, 0.34), layoutOrder = 2 })
	billboard.Parent = player:WaitForChild("PlayerGui")
	return billboard
end

-- Баннер на экране владельца: название и редкость.
local function addBanner(def: Items.ItemDef): Instance
	local cfg = UITokens.Layout.PresentationBanner
	local panel, body = UIKit.Panel({
		parent = gui,
		anchorPoint = Vector2.new(0.5, 0),
		position = cfg.position,
		size = cfg.size,
	})
	UIKit.Constrain(panel, { minSize = cfg.minSize, maxSize = cfg.maxSize })
	local layout = Instance.new("UIListLayout")
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.VerticalAlignment = Enum.VerticalAlignment.Center
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = body
	UIKit.Text({
		text = def.displayName,
		onLight = true,
		textSize = UITokens.TextSize.Huge,
		parent = body,
		size = UDim2.fromScale(1, 0.58),
		layoutOrder = 1,
	})
	UIKit.RarityTag(def.rarity, { parent = body, size = UDim2.fromScale(0.45, 0.38), layoutOrder = 2 })
	return panel
end

-- Подъём и оборот экспоната у владельца: двигается локальная копия, оригинал на время скрыт.
local function liftAndSpin(exhibit: BasePart, duration: number): () -> ()
	local cfg = GameConfig.Presentation
	local copy = exhibit:Clone()
	-- У копии оставляем только детали (модель «Visual»), подпись и прочее убираем.
	for _, child in copy:GetChildren() do
		if not child:IsA("BasePart") then
			child:Destroy()
		end
	end
	copy.Anchored = true
	copy.CanCollide = false
	copy.CanQuery = false
	copy.Parent = workspace
	local hidden = { exhibit }
	for _, d in exhibit:GetDescendants() do
		if d:IsA("BasePart") then
			table.insert(hidden, d)
		end
	end
	for _, p in hidden do
		p.LocalTransparencyModifier = 1
	end
	local label = exhibit:FindFirstChild("Label")
	if label and label:IsA("BillboardGui") then
		label.Enabled = false
	end

	local base = exhibit.CFrame
	local progress = Instance.new("NumberValue")
	progress.Changed:Connect(function(t: number)
		copy.CFrame = base
			* CFrame.new(0, cfg.LiftHeight * math.sin(math.pi * t), 0)
			* CFrame.Angles(0, 2 * math.pi * cfg.SpinTurns * t, 0)
	end)
	local tween = TweenService:Create(progress, TweenInfo.new(duration, Enum.EasingStyle.Sine), { Value = 1 })
	tween:Play()

	return function()
		tween:Cancel()
		progress:Destroy()
		copy:Destroy()
		for _, p in hidden do
			p.LocalTransparencyModifier = 0
		end
		if label and label:IsA("BillboardGui") then
			label.Enabled = true
		end
	end
end

local function present(payload: Payload)
	if type(payload) ~= "table" or type(payload.itemId) ~= "string" then
		return
	end
	local def = Items[payload.itemId]
	if not def then
		return
	end
	local isOwnerEvent = false
	local plot = findPlot(payload.plot)
	if plot then
		isOwnerEvent = plot:GetAttribute("OwnerUserId") == player.UserId
	end
	if isOwnerEvent then
		playSound(GameConfig.Sounds.Place)
	end
	local duration = GameConfig.Presentation.Duration[def.rarity] or 0
	if duration <= 0 or not plot then
		return
	end
	local showcases = plot:FindFirstChild("Showcases")
	local showcase = showcases and showcases:FindFirstChild("Showcase_" .. payload.slot)
	local exhibit = findExhibit(plot, payload.slot)
	if not showcase or not showcase:IsA("BasePart") or not exhibit then
		return
	end

	local cleanup: { () -> () } = {}
	table.insert(cleanup, addSpotlight(plot, showcase, payload.slot, def.rarity))
	local title = addTitle(exhibit, def)
	table.insert(cleanup, function()
		title:Destroy()
	end)
	if isOwnerEvent then
		local banner = addBanner(def)
		table.insert(cleanup, function()
			banner:Destroy()
		end)
		table.insert(cleanup, liftAndSpin(exhibit, duration))
		playSound(GameConfig.Sounds.Presentation[def.rarity] or "")
	end
	task.delay(duration, function()
		for _, step in cleanup do
			step()
		end
	end)
end

function PresentationController.Init()
	gui = UIKit.ScreenGui("Presentation", 8)
	Remotes.Get(Remotes.Names.ExhibitPlaced).OnClientEvent:Connect(present)
end

return PresentationController

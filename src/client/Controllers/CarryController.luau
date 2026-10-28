-- Пока игрок что-то несёт: плашка «Ты несёшь…» внизу по центру и кнопка «Бросить» (UI_KIT.md), клавиша G.
-- Отправляет серверу только намерение «брось», без аргументов. Зависит от Remotes, Items, UIKit, UITokens.

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Items = require(Shared:WaitForChild("Config"):WaitForChild("Items"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UIKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UIKit"))

local ACTION_NAME = "SnatchDropItem"

local CarryController = {}

local function buildCarryPill(gui: ScreenGui): (Frame, TextLabel, Frame)
	local cfg = UITokens.Layout.CarryPill
	local holder = Instance.new("Frame")
	holder.Name = "CarryPill"
	holder.BackgroundTransparency = 1
	holder.AnchorPoint = Vector2.new(0.5, 1)
	holder.Position = cfg.position
	holder.Size = cfg.size
	holder.Parent = gui
	UIKit.Constrain(holder, { minSize = cfg.minSize, maxSize = cfg.maxSize })

	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.VerticalAlignment = Enum.VerticalAlignment.Center
	layout.Padding = UDim.new(0, UITokens.Spacing.Small)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = holder

	local pill = UIKit.Pill({ text = "", parent = holder, size = cfg.nameSize, layoutOrder = 1 })
	local label = pill:FindFirstChild("Text") :: TextLabel
	local tag = UIKit.RarityTag("Common", { parent = holder, size = cfg.tagSize, layoutOrder = 2 })
	return holder, label, tag
end

function CarryController.Init()
	local player = Players.LocalPlayer
	local dropRemote = Remotes.Get(Remotes.Names.DropItem)
	local gui = UIKit.ScreenGui("CarryHud")

	local cfg = UITokens.Layout.DropButton
	local dropButton = UIKit.Button({
		kind = "Stop",
		text = "Бросить",
		parent = gui,
		anchorPoint = Vector2.new(1, 1),
		position = cfg.position,
		size = cfg.size,
	})
	UIKit.Constrain(dropButton.Instance, { aspect = cfg.aspect, minSize = cfg.minSize, maxSize = cfg.maxSize })
	dropButton:OnClick(function()
		dropRemote:FireServer()
	end)

	local pillHolder, pillLabel, rarityTag = buildCarryPill(gui)
	local currentTag = rarityTag

	local function onAction(_, inputState: Enum.UserInputState)
		if inputState == Enum.UserInputState.Begin then
			dropRemote:FireServer()
		end
		return Enum.ContextActionResult.Sink
	end

	local function refresh()
		ContextActionService:UnbindAction(ACTION_NAME)
		local itemId = player:GetAttribute("CarryingItemId")
		local def = if type(itemId) == "string" then Items[itemId] else nil
		dropButton.Instance.Visible = def ~= nil
		pillHolder.Visible = def ~= nil
		if not def then
			return
		end
		-- На клавиатуре подсказываем клавишу; экранная кнопка нужна и на телефоне, и на ПК.
		ContextActionService:BindAction(ACTION_NAME, onAction, false, Enum.KeyCode.G)
		dropButton:SetText(if UserInputService.KeyboardEnabled then "Бросить (G)" else "Бросить")
		pillLabel.Text = "Ты несёшь: " .. def.displayName
		local newTag = UIKit.RarityTag(def.rarity, {
			parent = pillHolder,
			size = currentTag.Size,
			layoutOrder = currentTag.LayoutOrder,
		})
		currentTag:Destroy()
		currentTag = newTag
	end

	player:GetAttributeChangedSignal("CarryingItemId"):Connect(refresh)
	refresh()
end

return CarryController

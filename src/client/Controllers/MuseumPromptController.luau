-- Показывает подсказки музея только там, где действие имеет смысл: в своём музее, по состоянию витрины,
-- рукам, хранилищу и выбору «Переставить». Только внешний вид: каждое действие всё равно проверяет сервер.
-- «Выставить из хранилища» открывает окно хранилища; выбранный для перестановки экспонат подсвечивается.
-- Зависит от тега MuseumPrompt, атрибутов, StorageController, UITokens.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("GameConfig"))
local UITokens = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("UITokens"))
local StorageController = require(script.Parent:WaitForChild("StorageController"))

local PROMPT_TAG = "MuseumPrompt"

local player = Players.LocalPlayer
local prompts: { [ProximityPrompt]: true } = {}
local watched: { [Instance]: true } = {}
local highlight: Highlight?

local MuseumPromptController = {}

local function allShowcasesOccupied(plot: Model): boolean
	local folder = plot:FindFirstChild("Showcases")
	if not folder then
		return false
	end
	for _, showcase in folder:GetChildren() do
		if showcase:GetAttribute("Occupied") ~= true then
			return false
		end
	end
	return true
end

local function shouldShow(prompt: ProximityPrompt): boolean
	local holder = prompt.Parent
	local plot = holder and holder:FindFirstAncestorWhichIsA("Model")
	if not holder or not plot or plot:GetAttribute("OwnerUserId") ~= player.UserId then
		return false
	end
	local action = prompt:GetAttribute("Action")
	local carrying = player:GetAttribute("CarryingItemId") ~= nil
	local stored = player:GetAttribute("StorageCount") or 0
	local occupied = holder:GetAttribute("Occupied") == true
	local moveSlot = player:GetAttribute("MoveSlot")
	local slot = holder:GetAttribute("Slot")

	if action == "Move" then
		-- На выбранном экспонате та же клавиша отменяет выбор.
		prompt.ActionText = if moveSlot == slot then "Отменить" else "Переставить"
		return occupied and (moveSlot == nil or moveSlot == slot)
	elseif action == "Here" then
		return moveSlot ~= nil and moveSlot ~= slot
	elseif moveSlot ~= nil then
		return false -- пока идёт перестановка, остальные подсказки витрин прячутся
	elseif action == "Display" then
		return not occupied and carrying
	elseif action == "FromStorage" then
		return not occupied and not carrying and stored > 0
	elseif action == "Rotate" then
		return occupied
	elseif action == "Store" then
		return occupied and stored < GameConfig.Museum.StorageCapacity
	elseif action == "ChestStore" then
		return carrying and allShowcasesOccupied(plot)
	end
	return false
end

-- Экспонат на витрине moveSlot своего музея (у Part экспоната атрибут Slot).
local function findSelectedExhibit(moveSlot: number): BasePart?
	for prompt in prompts do
		local plot = prompt.Parent and prompt.Parent:FindFirstAncestorWhichIsA("Model")
		if plot and plot:GetAttribute("OwnerUserId") == player.UserId then
			local exhibits = plot:FindFirstChild("Exhibits")
			for _, part in if exhibits then exhibits:GetChildren() else {} do
				if part:IsA("BasePart") and part:GetAttribute("Slot") == moveSlot then
					return part
				end
			end
			return nil
		end
	end
	return nil
end

local function refreshHighlight()
	local moveSlot = player:GetAttribute("MoveSlot")
	local target = if type(moveSlot) == "number" then findSelectedExhibit(moveSlot) else nil
	if highlight and target and highlight.Parent == target then
		return
	end
	-- Подсветка живёт внутри Part экспоната и может исчезнуть вместе с ним — пересоздаём.
	if highlight then
		highlight:Destroy()
		highlight = nil
	end
	if target then
		local h = Instance.new("Highlight")
		h.FillColor = UITokens.Highlight.Fill
		h.FillTransparency = UITokens.Highlight.FillTransparency
		h.OutlineColor = UITokens.Highlight.Outline
		h.DepthMode = Enum.HighlightDepthMode.Occluded
		-- У предмета-модели корень невидимый: подсвечиваем саму модель («Visual»).
		local visual = target:FindFirstChild("Visual")
		h.Adornee = if visual and visual:IsA("BasePart") then visual else target
		h.Parent = target
		highlight = h
	end
end

local function refreshAll()
	for prompt in prompts do
		prompt.Enabled = shouldShow(prompt)
	end
	refreshHighlight()
end

local function watch(instance: Instance?, attribute: string)
	if instance and not watched[instance] then
		watched[instance] = true
		instance:GetAttributeChangedSignal(attribute):Connect(refreshAll)
	end
end

local function track(prompt: Instance)
	if not prompt:IsA("ProximityPrompt") then
		return
	end
	prompts[prompt] = true
	local holder = prompt.Parent
	watch(holder, "Occupied")
	watch(holder and holder:FindFirstAncestorWhichIsA("Model"), "OwnerUserId")
	if prompt:GetAttribute("Action") == "FromStorage" then
		prompt.Triggered:Connect(function()
			local slot = holder and holder:GetAttribute("Slot")
			if type(slot) == "number" then
				StorageController.Open(slot)
			end
		end)
	end
	prompt.Enabled = shouldShow(prompt)
end

function MuseumPromptController.Init()
	CollectionService:GetInstanceAddedSignal(PROMPT_TAG):Connect(track)
	CollectionService:GetInstanceRemovedSignal(PROMPT_TAG):Connect(function(prompt)
		prompts[prompt :: ProximityPrompt] = nil
	end)
	for _, prompt in CollectionService:GetTagged(PROMPT_TAG) do
		track(prompt)
	end
	player:GetAttributeChangedSignal("CarryingItemId"):Connect(refreshAll)
	player:GetAttributeChangedSignal("StorageCount"):Connect(refreshAll)
	player:GetAttributeChangedSignal("MoveSlot"):Connect(refreshAll)
end

return MuseumPromptController

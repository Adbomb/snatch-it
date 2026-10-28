-- Показывает подсказки музея только там, где действие имеет смысл: в своём музее, по состоянию витрины,
-- рукам и хранилищу. Только внешний вид: каждое действие всё равно проверяет сервер.
-- «Выставить из хранилища» открывает окно хранилища. Зависит от тега MuseumPrompt, атрибутов, StorageController.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("GameConfig"))
local StorageController = require(script.Parent:WaitForChild("StorageController"))

local PROMPT_TAG = "MuseumPrompt"

local player = Players.LocalPlayer
local prompts: { [ProximityPrompt]: true } = {}
local watched: { [Instance]: true } = {}

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

	if action == "Display" then
		return not occupied and carrying
	elseif action == "FromStorage" then
		return not occupied and not carrying and stored > 0
	elseif action == "Store" then
		return occupied and stored < GameConfig.Museum.StorageCapacity
	elseif action == "ChestStore" then
		return carrying and allShowcasesOccupied(plot)
	end
	return false
end

local function refreshAll()
	for prompt in prompts do
		prompt.Enabled = shouldShow(prompt)
	end
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
end

return MuseumPromptController

-- Показывает подсказки музея только там, где действие имеет смысл: в своём музее, по состоянию витрины,
-- рукам, хранилищу и выбору «Переставить». Только внешний вид: каждое действие всё равно проверяет сервер.
-- «Выставить из инвентаря» открывает окно выбора предмета; выбранный для перестановки экспонат подсвечивается.
-- «Украсть» — только когда игрок внутри этого музея (зал или открытая галерея, Shared/MuseumSpace — то же правило, что
-- на сервере, D52): снаружи сквозь стену подсказки нет; в Судную ночь проверяется 4 раза в секунду, во время удержания
-- подсказка не прячется (иначе удержание сорвалось бы). Видимость экспоната проверяет сервер.
-- Зависит от тега MuseumPrompt, атрибутов, InventoryController, UITokens, Shared/MuseumSpace.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("GameConfig"))
local UITokens = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("UITokens"))
local MuseumSpace = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("MuseumSpace"))
local InventoryController = require(script.Parent:WaitForChild("InventoryController"))

local PROMPT_TAG = "MuseumPrompt"

local player = Players.LocalPlayer
local prompts: { [ProximityPrompt]: true } = {}
-- слабые ключи: витрины и двери защиты уничтожаются (конец ночи, выход владельца) — таблица их не держит
local watched: { [Instance]: true } = setmetatable({}, { __mode = "k" }) :: any
local highlight: Highlight?
local holding: { [ProximityPrompt]: boolean } = {} -- «Украсть», которую сейчас держат

local MuseumPromptController = {}

local STEAL_CHECK = 0.25 -- секунд между проверками «внутри музея» в Судную ночь

-- Игрок внутри музея участка plot (зал или открытая галерея) — по тому же правилу, что сервер (D52).
local function insideOf(plot: Model): boolean
	local origin = plot:GetAttribute("FloorOrigin")
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if typeof(origin) ~= "CFrame" or not root or not root:IsA("BasePart") then
		return false
	end
	local space = { model = plot, floorOrigin = origin, level = plot:GetAttribute("MuseumLevel") or 1 }
	return MuseumSpace.Inside(space, root.Position)
end

local function shouldShow(prompt: ProximityPrompt): boolean
	local holder = prompt.Parent
	local plot = holder and holder:FindFirstAncestorWhichIsA("Model")
	local action = prompt:GetAttribute("Action")
	if holder and holder:GetAttribute("Open") == false then
		return false -- место музея ещё закрыто (D48-C: откроется на уровне UnlockLevel)
	end
	if action == "Hack" then
		-- Взлом усиленной двери (D37): чужая дверь, Судная ночь, есть устройство взлома. Уровень проверяет сервер.
		local owner = nil
		local node = holder
		while node and owner == nil do
			owner = node:GetAttribute("OwnerUserId")
			node = node.Parent
		end
		return owner ~= nil
			and owner ~= player.UserId
			and ReplicatedStorage:GetAttribute("Phase") == "DoomNight"
			and (player:GetAttribute("HackDevices") or 0) > 0
			and player:GetAttribute("Knocked") ~= true
	end
	if action == "Steal" then
		-- Судная ночь (D46): чужой выставленный экспонат, руки свободны, вор не оглушён. Остальное решает сервер.
		local owner = plot and plot:GetAttribute("OwnerUserId")
		return holder ~= nil
			and owner ~= nil
			and owner ~= player.UserId
			and holder:GetAttribute("Occupied") == true
			and ReplicatedStorage:GetAttribute("Phase") == "DoomNight"
			and player:GetAttribute("CarryingItemId") == nil
			and player:GetAttribute("Knocked") ~= true
			and (holding[prompt] or insideOf(plot :: Model))
	end
	if not holder or not plot or plot:GetAttribute("OwnerUserId") ~= player.UserId then
		return false
	end
	local carrying = player:GetAttribute("CarryingItemId") ~= nil
	local stored = player:GetAttribute("StorageCount") or 0
	local occupied = holder:GetAttribute("Occupied") == true
	local moveSlot = player:GetAttribute("MoveSlot")
	local slot = holder:GetAttribute("Slot")

	if action == "VaultInventory" or action == "VaultDefense" then
		return true -- своё хранилище (D48-C); окно откроет сервер после проверки
	elseif action == "Move" then
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
		return occupied
	elseif action == "ChestStore" then
		return carrying -- D46: несомое — в инвентарь в любой момент
	elseif action == "Upgrade" then
		-- Табличка «Улучшение» своего двора (D34): пока гантель не максимальная и руки пустые.
		return not carrying and (player:GetAttribute("DumbbellLevel") or 1) < #GameConfig.Progression.Dumbbell.Power
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
	if prompt:GetAttribute("Action") == "Steal" then
		prompt.PromptButtonHoldBegan:Connect(function()
			holding[prompt] = true
		end)
		prompt.PromptButtonHoldEnded:Connect(function()
			holding[prompt] = nil
		end)
	end
	if prompt:GetAttribute("Action") == "FromStorage" then
		prompt.Triggered:Connect(function()
			local slot = holder and holder:GetAttribute("Slot")
			if type(slot) == "number" then
				InventoryController.OpenForSlot(slot)
			end
		end)
	end
	prompt.Enabled = shouldShow(prompt)
end

function MuseumPromptController.Init()
	CollectionService:GetInstanceAddedSignal(PROMPT_TAG):Connect(track)
	CollectionService:GetInstanceRemovedSignal(PROMPT_TAG):Connect(function(prompt)
		prompts[prompt :: ProximityPrompt] = nil
		holding[prompt :: ProximityPrompt] = nil
	end)
	for _, prompt in CollectionService:GetTagged(PROMPT_TAG) do
		track(prompt)
	end
	player:GetAttributeChangedSignal("CarryingItemId"):Connect(refreshAll)
	player:GetAttributeChangedSignal("StorageCount"):Connect(refreshAll)
	player:GetAttributeChangedSignal("MoveSlot"):Connect(refreshAll)
	player:GetAttributeChangedSignal("DumbbellLevel"):Connect(refreshAll)
	player:GetAttributeChangedSignal("Knocked"):Connect(refreshAll)
	player:GetAttributeChangedSignal("HackDevices"):Connect(refreshAll)
	ReplicatedStorage:GetAttributeChangedSignal("Phase"):Connect(refreshAll)
	-- «Украсть» зависит от того, где стоит игрок: в Судную ночь — проверять по ходу
	task.spawn(function()
		while true do
			task.wait(STEAL_CHECK)
			if ReplicatedStorage:GetAttribute("Phase") == "DoomNight" then
				for prompt in prompts do
					if prompt:GetAttribute("Action") == "Steal" then
						prompt.Enabled = shouldShow(prompt)
					end
				end
			end
		end
	end)
end

return MuseumPromptController

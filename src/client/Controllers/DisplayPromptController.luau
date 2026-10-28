-- Показывает «Выставить» только на пустых витринах своего музея; в чужом подсказки не видно.
-- Только внешний вид: всё равно проверяет сервер. Зависит от тега DisplayPrompt и атрибутов участка.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")

local DISPLAY_PROMPT_TAG = "DisplayPrompt"

local DisplayPromptController = {}

local function track(prompt: Instance)
	if not prompt:IsA("ProximityPrompt") then
		return
	end
	local showcase = prompt.Parent
	local plot = showcase and showcase:FindFirstAncestorWhichIsA("Model")
	if not showcase or not plot then
		return
	end
	local userId = Players.LocalPlayer.UserId

	local function refresh()
		local mine = plot:GetAttribute("OwnerUserId") == userId
		local free = showcase:GetAttribute("Occupied") ~= true
		prompt.Enabled = mine and free
	end

	plot:GetAttributeChangedSignal("OwnerUserId"):Connect(refresh)
	showcase:GetAttributeChangedSignal("Occupied"):Connect(refresh)
	refresh()
end

function DisplayPromptController.Init()
	CollectionService:GetInstanceAddedSignal(DISPLAY_PROMPT_TAG):Connect(track)
	for _, prompt in CollectionService:GetTagged(DISPLAY_PROMPT_TAG) do
		track(prompt)
	end
end

return DisplayPromptController

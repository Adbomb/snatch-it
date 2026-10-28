-- Бросок предмета: клавиша G и экранная кнопка «Бросить» на телефоне, пока игрок что-то несёт.
-- Отправляет серверу только намерение «брось», без аргументов. Зависит от Remotes, ContextActionService.

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Remotes"))

local ACTION_NAME = "SnatchDropItem"

local CarryController = {}

function CarryController.Init()
	local player = Players.LocalPlayer
	local dropRemote = Remotes.Get(Remotes.Names.DropItem)

	local function onAction(_, inputState: Enum.UserInputState)
		if inputState == Enum.UserInputState.Begin then
			dropRemote:FireServer()
		end
		return Enum.ContextActionResult.Sink
	end

	local function refresh()
		ContextActionService:UnbindAction(ACTION_NAME)
		if player:GetAttribute("CarryingItemId") then
			ContextActionService:BindAction(ACTION_NAME, onAction, true, Enum.KeyCode.G)
			ContextActionService:SetTitle(ACTION_NAME, "Бросить")
		end
	end

	player:GetAttributeChangedSignal("CarryingItemId"):Connect(refresh)
	refresh()
end

return CarryController

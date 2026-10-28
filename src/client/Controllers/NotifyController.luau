-- Показывает короткие сообщения сервера стандартным уведомлением Roblox в углу экрана.
-- Зависит от Remotes (Notify) и StarterGui.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterGui = game:GetService("StarterGui")

local Remotes = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Remotes"))

local NotifyController = {}

function NotifyController.Init()
	Remotes.Get(Remotes.Names.Notify).OnClientEvent:Connect(function(text: string)
		-- SetCore может ошибиться, пока стандартный интерфейс не готов, — поэтому pcall.
		pcall(StarterGui.SetCore, StarterGui, "SendNotification", {
			Title = "Утащи это!",
			Text = text,
			Duration = 4,
		})
	end)
end

return NotifyController

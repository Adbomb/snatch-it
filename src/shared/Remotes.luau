-- Имена всех RemoteEvent'ов игры. Сервер создаёт их при старте (CreateAll),
-- клиент получает через Get, который ждёт их появления (WaitForChild).

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local FOLDER_NAME = "Remotes"

local Remotes = {}

Remotes.Names = {
	DropItem = "DropItem", -- клиент → сервер: «брось то, что я несу» (без аргументов)
	Notify = "Notify", -- сервер → клиент: короткое сообщение (текст, вид)
	StorageChanged = "StorageChanged", -- сервер → владельцу: содержимое хранилища { {uid, itemId} }
	DisplayFromStorage = "DisplayFromStorage", -- клиент → сервер: (uid, номер витрины)
}

function Remotes.CreateAll()
	assert(RunService:IsServer(), "Remotes.CreateAll вызывается только на сервере")
	local folder = Instance.new("Folder")
	folder.Name = FOLDER_NAME
	for _, name in Remotes.Names do
		local remote = Instance.new("RemoteEvent")
		remote.Name = name
		remote.Parent = folder
	end
	folder.Parent = ReplicatedStorage
end

function Remotes.Get(name: string): RemoteEvent
	assert(Remotes.Names[name], "Неизвестный RemoteEvent: " .. tostring(name))
	if RunService:IsServer() then
		return ReplicatedStorage:FindFirstChild(FOLDER_NAME):FindFirstChild(name) :: RemoteEvent
	end
	return ReplicatedStorage:WaitForChild(FOLDER_NAME):WaitForChild(name) :: RemoteEvent
end

return Remotes

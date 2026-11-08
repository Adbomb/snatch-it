-- Имена всех RemoteEvent'ов игры. Сервер создаёт их при старте (CreateAll),
-- клиент получает через Get, который ждёт их появления (WaitForChild).

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local FOLDER_NAME = "Remotes"

local Remotes = {}

Remotes.Names = {
	DropItem = "DropItem", -- клиент → сервер: «брось то, что я несу» (без аргументов)
	Notify = "Notify", -- сервер → клиент: короткое сообщение (текст, вид)
	InventoryChanged = "InventoryChanged", -- сервер → владельцу: весь инвентарь { {uid, itemId, slot?} } (D46)
	InventoryAction = "InventoryAction", -- клиент → сервер: ("Display" | "Remove" | "Replace", uid, постамент?)
	ExhibitPlaced = "ExhibitPlaced", -- сервер → владельцу и игрокам рядом: { itemId, slot, plot }
	GymUpgrade = "GymUpgrade", -- клиент → сервер: «улучши мою гантель» (без аргументов)
	GymGain = "GymGain", -- сервер → владельцу: прибавка силы за такт качания (число)
	DefenseAction = "DefenseAction", -- клиент → сервер: ("BuyDefense", вид) | ("BuyHack", уровень) | ("Install", вид, место) | ("Remove", вид)
	DefenseChanged = "DefenseChanged", -- сервер → владельцу: { owned, hacks, installed, level, max, coins }
	PvpAttack = "PvpAttack", -- клиент → сервер: «ударь» (без аргументов, цель выбирает сервер), D46
	PvpEffect = "PvpEffect", -- сервер → игрокам рядом: { kind = "Swing" | "Hit" | "Knock", attacker, target?, damage }
	OpenWindow = "OpenWindow", -- сервер → владельцу: открыть окно ("Inventory" | "Defense") — подсказки хранилища D48-C
	-- D55: магазин Ловибумов, поимка, обучение
	ShopAction = "ShopAction", -- клиент → сервер: ("Buy", уровень, вид, количество) | ("Open")
	LovibumsChanged = "LovibumsChanged", -- сервер → владельцу: { lovibums, coins, prices?, open, reason? }
	CatchAction = "CatchAction", -- клиент → сервер: ("Throw", вид, точка прилёта Vector3, время отпускания) | ("Leave")
	CatchState = "CatchState", -- сервер → ловящему: { state, boss, slot, uid, since, throws, max, face, … } | nil
	CatchEffect = "CatchEffect", -- сервер → игрокам рядом: { kind = "Throw" | "Result" | …, … } (видят все рядом)
	TutorialChanged = "TutorialChanged", -- сервер → ученику: { step, target?, … }
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

-- Событие сервера одному игроку. Тестовый игрок (Server/Tests/TestPlayer — таблица, а не Instance) получает его
-- в свой журнал Sent вместо отправки: так серверные тесты проходят тем же путём, что и игра.
function Remotes.FireClient(name: string, player: Player, ...: any)
	if typeof(player) ~= "Instance" then
		local sent = (player :: any).Sent
		if type(sent) == "table" then
			table.insert(sent, { name = name, args = table.pack(...) })
		end
		return
	end
	Remotes.Get(name):FireClient(player, ...)
end

return Remotes

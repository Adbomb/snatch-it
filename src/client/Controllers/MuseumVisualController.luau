-- Вид музея D48-C только у владельца (клиент): обстановка хранилища (шаблон ReplicatedStorage.MuseumVisual.VaultDecor
-- копируется к своему участку — другие игроки её не видят и не грузят), решётка павильона у своего музея открыта
-- (у остальных закрыта; проход решает сервер — барьер VaultService), экран сканера зелёный. По просьбе сервера
-- (подсказки хранилища, Remotes.OpenWindow) открывает окно «Инвентарь» или «Защита». Только вид: доступ проверяет сервер.
-- Зависит от Remotes, UITokens, InventoryController, DefenseController.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local InventoryController = require(script.Parent:WaitForChild("InventoryController"))
local DefenseController = require(script.Parent:WaitForChild("DefenseController"))

local player = Players.LocalPlayer
local cfg = UITokens.Museum

local decor: Model? = nil
local decorPlot: Model? = nil
local watched: { [Model]: boolean } = {}

local MuseumVisualController = {}

-- Решётка и сканер в здании участка plot: own — участок свой.
local function styleBuilding(plot: Model, own: boolean)
	local building = plot:FindFirstChild("Building")
	if not building then
		return
	end
	for _, module in building:GetChildren() do
		local name = module:GetAttribute("Module")
		if name == "D48_GateLeaf" then
			for _, part in module:GetDescendants() do
				if part:IsA("BasePart") then
					part.LocalTransparencyModifier = if own then 1 else 0
				end
			end
		elseif name == "D48_Scanner" then
			local screen = module:FindFirstChild("Screen", true)
			if screen and screen:IsA("BasePart") then
				screen.Color = if own then cfg.ScannerOwner else cfg.ScannerIdle
			end
		end
	end
end

local function removeDecor()
	if decor then
		decor:Destroy()
	end
	decor, decorPlot = nil, nil
end

-- Обстановка хранилища у своего участка: копия шаблона в начале участка (атрибут FloorOrigin).
local function showDecor(plot: Model)
	if decorPlot == plot and decor and decor.Parent then
		return
	end
	removeDecor()
	local origin = plot:GetAttribute("FloorOrigin")
	local folder = ReplicatedStorage:FindFirstChild("MuseumVisual")
	local template = folder and folder:FindFirstChild("VaultDecor")
	if typeof(origin) ~= "CFrame" or not template or not template:IsA("Model") then
		return
	end
	local copy = template:Clone()
	copy.Name = "__VaultDecor"
	copy:PivotTo(origin)
	copy.Parent = workspace
	decor, decorPlot = copy, plot
end

local function refresh(plot: Model)
	local own = plot:GetAttribute("OwnerUserId") == player.UserId
	styleBuilding(plot, own)
	if own then
		showDecor(plot)
	elseif decorPlot == plot then
		removeDecor()
	end
end

local function watch(plot: Instance)
	if not plot:IsA("Model") or watched[plot] then
		return
	end
	watched[plot] = true
	plot:GetAttributeChangedSignal("OwnerUserId"):Connect(function()
		refresh(plot)
	end)
	-- здание перестраивается при смене уровня: новые створки — снова открыть у своего участка
	plot.ChildAdded:Connect(function(child)
		if child.Name == "Building" then
			task.defer(refresh, plot)
		end
	end)
	refresh(plot)
end

function MuseumVisualController.Init()
	Remotes.Get(Remotes.Names.OpenWindow).OnClientEvent:Connect(function(window)
		if window == "Inventory" then
			InventoryController.Open()
		elseif window == "Defense" then
			DefenseController.Open()
		end
	end)
	task.spawn(function()
		local plots = workspace:WaitForChild("World"):WaitForChild("Plots")
		plots.ChildAdded:Connect(watch)
		for _, plot in plots:GetChildren() do
			watch(plot)
		end
	end)
end

return MuseumVisualController

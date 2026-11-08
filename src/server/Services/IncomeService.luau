-- Доход экспонатов (D37, D40): у каждого произведения свой доход в секунду (Config/Items.income, без множителей
-- редкости). Раз в секунду сервер начисляет каждому игроку сумму дохода его экспонатов на витринах (Displayed): в
-- руках, в хранилище и у босса предмет дохода не приносит. Атрибуты игрока для интерфейса: Coins и Income (общий
-- доход в секунду, пересчитывается при каждом изменении витрин). Надпись «+X/сек» над экспонатом ставит
-- MuseumService (IncomeService.Label). Зависит от ItemRegistry, DataService, Config/Items, Shared/NumberFormat.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Items = require(ReplicatedStorage.Shared.Config.Items)
local NumberFormat = require(ReplicatedStorage.Shared.NumberFormat)
local Server = ServerScriptService.Server
local DataService = require(Server.Services.DataService)
local ItemRegistry = require(Server.Services.ItemRegistry)

local TICK = 1 -- секунд между начислениями
local SAVE_EVERY = 60 -- раз в столько секунд начисленное просится в DataStore (на выходе сохраняется всегда)
local LABEL_NAME = "IncomeLabel"
local LABEL_GAP = 2.6 -- над названием предмета, стадов
local LABEL_COLOR = Color3.fromHex("5BEA72")

local IncomeService = {}

-- Доход предмета в секунду.
function IncomeService.Of(itemId: string): number
	local def = Items[itemId]
	return if def then def.income or 0 else 0
end

-- Общий доход владельца в секунду: сумма по экспонатам на витринах.
function IncomeService.TotalFor(userId: number): number
	local total = 0
	for _, uid in ItemRegistry.GetOwnedBy(userId) do
		local entry = ItemRegistry.Get(uid)
		if entry and entry.state == "Displayed" then
			total += IncomeService.Of(entry.itemId)
		end
	end
	return total
end

-- Надпись «+X/сек» над экспонатом (видна всем).
function IncomeService.Label(part: BasePart, itemId: string)
	local income = IncomeService.Of(itemId)
	local billboard = part:FindFirstChild(LABEL_NAME) :: BillboardGui?
	if income <= 0 then
		if billboard then
			billboard:Destroy()
		end
		return
	end
	if not billboard then
		local gui = Instance.new("BillboardGui")
		gui.Name = LABEL_NAME
		gui.Size = UDim2.fromOffset(170, 34)
		gui.MaxDistance = 30 -- D50: дальние надписи не видны сквозь арки и проёмы соседних залов
		gui.StudsOffset = Vector3.new(0, part.Size.Y / 2 + LABEL_GAP, 0)
		local text = Instance.new("TextLabel")
		text.Name = "Text"
		text.Size = UDim2.fromScale(1, 1)
		text.BackgroundTransparency = 1
		text.TextScaled = true
		text.Font = Enum.Font.GothamBlack
		text.TextColor3 = LABEL_COLOR
		text.TextStrokeTransparency = 0.2
		text.Parent = gui
		gui.Parent = part
		billboard = gui
	end
	local label = (billboard :: BillboardGui):FindFirstChild("Text") :: TextLabel
	label.Text = ("+%s/сек"):format(NumberFormat.Short(income))
end

-- Обновить атрибут общего дохода игрока.
local function refreshIncome(player: any)
	local total = IncomeService.TotalFor(player.UserId)
	if player:GetAttribute("Income") ~= total then
		player:SetAttribute("Income", total)
	end
end

-- Один такт начисления для списка игроков. Возвращает начисленное по игрокам (для тестов).
local ticks = 0
local function tick(players: { any }): { [any]: number }
	ticks += 1
	local paid = {}
	for _, player in players do
		local total = IncomeService.TotalFor(player.UserId)
		player:SetAttribute("Income", total)
		if total > 0 then
			local coins = DataService.AddCoins(player, total)
			if coins then
				player:SetAttribute("Coins", coins)
				paid[player] = total
				local onPaid = IncomeService.OnPaid
				if onPaid then
					onPaid(player, total) -- D55: первое начисление завершает обучение
				end
				if ticks % SAVE_EVERY == 0 then
					DataService.RequestSave(player)
				end
			end
		end
	end
	return paid
end

-- После начисления игроку (задаёт TutorialService, D55).
IncomeService.OnPaid = nil :: ((player: any, amount: number) -> ())?

function IncomeService.Init()
	ItemRegistry.OnChanged(function(_uid, fromState, toState, entry)
		if (fromState == "Displayed" or toState == "Displayed") and entry.owner then
			local player = Players:GetPlayerByUserId(entry.owner)
			if player then
				refreshIncome(player)
			end
		end
	end)
	task.spawn(function()
		while true do
			task.wait(TICK)
			tick(Players:GetPlayers())
		end
	end)
end

-- Для серверных тестов: такт с явным списком игроков (тестовых нет в Players:GetPlayers()).
IncomeService.Handlers = {
	Tick = tick,
	Refresh = refreshIncome,
}

return IncomeService

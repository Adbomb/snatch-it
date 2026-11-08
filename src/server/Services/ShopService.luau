-- Магазин Ловибумов (D55): покупка за монеты — уровень босса 1–10, вид, количество. Все аргументы от клиента
-- проверяет Shared/CatchRules.CheckBuy (целые без NaN, уровень, вид, 1…MaxBuy, запас ≤ MaxStock, хватает монет); монеты
-- и запас меняются в одном кадре (DataService.BuyLovibums). Отказ: обучение не пройдено (кнопки «Магазин» у ученика нет,
-- D55), идёт поимка (CatchService). ЦЕНЫ НЕ УТВЕРЖДЕНЫ: в опубликованной игре магазин не продаёт; в Studio + DevMode —
-- тестовые цены (Config/Catch.TestPrices). Владельцу — LovibumsChanged: запас, монеты, цены, открыт ли магазин.
-- Зависит от DataService, Shared/CatchRules, Shared/TutorialRules, Remotes, Config/GameConfig, Util/RateLimiter,
-- Util/Notify, Util/Log.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")

local CatchRules = require(ReplicatedStorage.Shared.CatchRules)
local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local TutorialRules = require(ReplicatedStorage.Shared.TutorialRules)
local Server = ServerScriptService.Server
local DataService = require(Server.Services.DataService)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local RateLimiter = require(Server.Util.RateLimiter)

local Catch = GameConfig.Catch
local limiter = RateLimiter.new(GameConfig.RateLimits.Shop)

local ShopService = {}

-- Идёт ли у игрока поимка (задаёт CatchService): во время поимки магазин закрыт.
ShopService.IsCatching = nil :: ((player: any) -> boolean)?

-- Тестовые цены — только в Studio с DevMode (проверка покупки до утверждения цен владельцем).
local function testMode(): boolean
	return RunService:IsStudio() and GameConfig.DevMode
end

function ShopService.Prices(): { [number]: { [string]: number } }?
	return CatchRules.Prices(testMode())
end

local function copy(lovibums: { [string]: { [string]: number } }): { [string]: { [string]: number } }
	local out = {}
	for key, byKind in lovibums do
		out[key] = table.clone(byKind)
	end
	return out
end

-- Запас, монеты, цены и доступность магазина — владельцу (и атрибут Lovibums — всего штук, для HUD).
function ShopService.Sync(player: any)
	local data = DataService.GetData(player)
	local lovibums = DataService.Lovibums(player)
	if not data or not lovibums then
		return
	end
	local total = 0
	for _, byKind in lovibums do
		for _, n in byKind do
			total += n
		end
	end
	player:SetAttribute("Lovibums", total)
	player:SetAttribute("Tutorial", if TutorialRules.IsActive(data) then data.tutorial.step else nil)
	Remotes.FireClient(Remotes.Names.LovibumsChanged, player, {
		lovibums = copy(lovibums),
		coins = data.coins,
		prices = ShopService.Prices(),
		open = TutorialRules.ShopAllowed(data),
		test = Catch.Prices == nil and testMode(),
	})
end

local function tryAction(player: any, action: any, level: any, kind: any, count: any)
	if not limiter:Allow(player) then
		return
	end
	local data = DataService.GetData(player)
	if not data then
		return
	end
	if action == "Open" then
		ShopService.Sync(player)
		return
	end
	if action ~= "Buy" then
		return
	end
	if not TutorialRules.ShopAllowed(data) then
		Notify.Send(player, "Магазин откроется после обучения", "Stop")
		return
	end
	local catching = ShopService.IsCatching
	if catching and catching(player) then
		Notify.Send(player, "Во время поимки магазин закрыт", "Stop")
		return
	end
	local total, reason = CatchRules.CheckBuy(ShopService.Prices(), level, kind, count, data.coins, data.lovibums)
	if not total then
		Notify.Send(player, reason or "Покупка не прошла", "Stop")
		ShopService.Sync(player)
		return
	end
	if not DataService.BuyLovibums(player, level, kind, count, total) then
		Notify.Send(player, "Покупка не прошла", "Stop")
		ShopService.Sync(player)
		return
	end
	player:SetAttribute("Coins", data.coins)
	DataService.RequestSave(player)
	Log.Debug(
		"ShopService",
		("%s купил %s ×%d (уровень %d) за %d"):format(player.Name, kind, count, level, total)
	)
	ShopService.Sync(player)
	Notify.Send(player, ("Куплено: %s ×%d — уровень %d"):format(Catch.Names[kind], count, level), "Go")
end

function ShopService.Init()
	Remotes.Get(Remotes.Names.ShopAction).OnServerEvent:Connect(tryAction)
end

-- Для серверных тестов.
ShopService.Handlers = {
	Action = tryAction,
}

return ShopService

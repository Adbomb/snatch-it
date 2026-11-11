-- Улучшение музея (D56): покупка следующего уровня (2…10) за монеты из окна «Улучшение музея» (кнопка «Музей» в
-- HUD) — откуда угодно. Клиент присылает только номер уровня, который хочет купить; уровень, цену и монеты сервер
-- берёт из профиля и конфига. Все проверки — здесь: профиль и свой участок, обучение (закрыто, как «Защита» и
-- «Магазин»), запрос ровно следующего уровня (повторное нажатие и подделки отбрасываются), последний уровень, запрет
-- по фазе (подготовка, Судная ночь и 10 с после неё — Shared/GameTime.UpgradeLock), монеты (Shared/MuseumRules).
-- Порядок: проверки → запись профиля (DataService.UpgradeMuseum: монеты и уровень одним действием) → мир и клиент
-- (здание и открытые места — PlotService.ShowLevel; атрибуты, инвентарь, защита) → сохранение. Между проверками и
-- записью нет yield. Предметы, их места и доход не меняются: 20 постаментов стоят на участке с самого начала, у
-- нового уровня открываются следующие места.
-- Зависит от DataService, PlotService, InventoryService, DefenseService, Shared/MuseumRules, Shared/GameTime,
-- Shared/NumberFormat, Util/RateLimiter, Util/Notify, Util/Log, Remotes, GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local MuseumRules = require(ReplicatedStorage.Shared.MuseumRules)
local NumberFormat = require(ReplicatedStorage.Shared.NumberFormat)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Server = ServerScriptService.Server
local DataService = require(Server.Services.DataService)
local DefenseService = require(Server.Services.DefenseService)
local InventoryService = require(Server.Services.InventoryService)
local PlotService = require(Server.Services.PlotService)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local RateLimiter = require(Server.Util.RateLimiter)

local Codes = MuseumRules.Codes
local limiter = RateLimiter.new(GameConfig.RateLimits.MuseumUpgrade)

local MuseumUpgradeService = {}

-- Ответ окну: получилось ли, почему нет и что в профиле сейчас (уровень, места, монеты).
local function answer(player: any, ok: boolean, code: string?, message: string?)
	local data = DataService.GetData(player)
	local level = MuseumRules.Level(GameConfig, data and data.museumLevel)
	Remotes.FireClient(Remotes.Names.MuseumUpgradeResult, player, {
		ok = ok,
		code = code,
		message = message,
		level = level,
		slots = MuseumRules.Slots(GameConfig, level),
		coins = if data then data.coins else 0,
	})
end

-- Отказ: уведомление игроку (если есть что сказать) и ответ окну.
local function refuse(player: any, code: string, message: string?)
	if message then
		Notify.Send(player, message, "Stop")
	end
	answer(player, false, code, message)
end

-- Мир и клиент — по уровню из профиля: здание и открытые места участка, монеты, инвентарь (атрибуты MuseumLevel и
-- MuseumSlots), защита (сколько устройств можно, какие подходят к этому уровню).
function MuseumUpgradeService.Refresh(player: any)
	local data = DataService.GetData(player)
	if not data then
		return
	end
	local plot = PlotService.GetPlotOf(player)
	if plot then
		local ok, err = pcall(PlotService.ShowLevel, plot, data.museumLevel)
		if not ok then
			-- уровень уже куплен и записан; здание перестроится при следующем входе
			Log.Warn(
				"MuseumUpgradeService",
				("%s: музей уровня %d не перестроен: %s"):format(
					player.Name,
					data.museumLevel,
					tostring(err)
				)
			)
		end
	end
	player:SetAttribute("Coins", data.coins)
	InventoryService.Sync(player)
	DefenseService.Sync(player)
end

-- Покупка уровня requested (должен быть ровно следующим). Все проверки — здесь.
local function upgrade(player: any, requested: any)
	local data = DataService.GetData(player)
	local plot = PlotService.GetPlotOf(player)
	if not data or not plot or plot.owner ~= player then
		refuse(player, Codes.Busy, MuseumRules.Texts.Busy)
		return
	end
	if player:GetAttribute("Tutorial") ~= nil then
		refuse(player, Codes.Tutorial, MuseumRules.Texts.Tutorial)
		return
	end
	local level = data.museumLevel
	if MuseumRules.IsLevel(GameConfig, level) and level >= MuseumRules.MaxLevel(GameConfig) then
		refuse(player, Codes.Max, MuseumRules.Texts.Max)
		return
	end
	if not MuseumRules.IsNext(GameConfig, level, requested) then
		-- двойное нажатие, устаревшее окно или подделка: без уведомления — окно получит то, что в профиле сейчас
		refuse(player, Codes.Stale, nil)
		return
	end
	local lock = GameTime.UpgradeLock(GameTime.Now())
	local code = MuseumRules.Check(GameConfig, level, data.coins, lock)
	if code then
		local message = MuseumRules.Texts[code]
		if code == Codes.Locked then
			message = lock
		elseif code == Codes.Coins then
			local price = MuseumRules.Price(GameConfig, level) :: number
			message = ("Не хватает монет: уровень %d стоит $%s"):format(
				level + 1,
				NumberFormat.Short(price)
			)
		end
		refuse(player, code, message)
		return
	end
	local price = MuseumRules.Price(GameConfig, level) :: number
	if not DataService.UpgradeMuseum(player, level) then
		refuse(player, Codes.Stale, nil)
		return
	end
	local slots = MuseumRules.Slots(GameConfig, level + 1)
	MuseumUpgradeService.Refresh(player)
	DataService.RequestSave(player)
	Log.Debug(
		"MuseumUpgradeService",
		("%s: музей %d → %d за %s, мест %d"):format(
			player.Name,
			level,
			level + 1,
			NumberFormat.Short(price),
			slots
		)
	)
	Notify.Send(player, ("Музей улучшен: уровень %d, мест %d"):format(level + 1, slots), "Go")
	answer(player, true, nil, nil)
end

-- Запрос клиента: не чаще GameConfig.RateLimits.MuseumUpgrade в секунду.
local function request(player: any, requested: any)
	if limiter:Allow(player) then
		upgrade(player, requested)
	end
end

function MuseumUpgradeService.Init()
	Remotes.Get(Remotes.Names.MuseumUpgrade).OnServerEvent:Connect(request)
end

-- Для серверных тестов: Request — тот же вход, что у RemoteEvent (с лимитом запросов); Upgrade — без лимита.
MuseumUpgradeService.Handlers = { Request = request, Upgrade = upgrade }

return MuseumUpgradeService

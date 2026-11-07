-- Вход и выход игрока: участок, профиль, гантель, музей, хранилище — в одном порядке для игры и серверных тестов
-- (Main вызывает Join/Leave на PlayerAdded/PlayerRemoving, Server/Tests — для тестовых игроков с профилем в памяти).
-- Зависит от CarryService, DataService, GymService, MuseumService, PlotService, InventoryService, TheftService, DefenseService,
-- VaultService, Util/Notify, Util/Log.

local ServerScriptService = game:GetService("ServerScriptService")

local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local DataService = require(Server.Services.DataService)
local GymService = require(Server.Services.GymService)
local MuseumService = require(Server.Services.MuseumService)
local PlotService = require(Server.Services.PlotService)
local InventoryService = require(Server.Services.InventoryService)
local TheftService = require(Server.Services.TheftService)
local DefenseService = require(Server.Services.DefenseService)
local VaultService = require(Server.Services.VaultService)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)

export type JoinOptions = {
	mock: boolean?, -- профиль в памяти (ProfileStore.Mock), только серверные тесты
}

local PlayerSession = {}

-- Игрок вошёл: участок, профиль (ждёт), здание и гантель его уровня, экспонаты, хранилище.
-- true — игрок в игре; false — участка нет или профиль не загрузился (игрока кикнули).
function PlayerSession.Join(player: Player, options: JoinOptions?): boolean
	local plot = PlotService.Assign(player)
	if not plot then
		player:Kick(
			"На сервере нет свободного музея. Зайдите на другой сервер."
		)
		return false
	end
	VaultService.OnPlotAssigned(player) -- свой барьер хранилища пропускает (D48-C)
	if not DataService.LoadAsync(player, options and options.mock) then
		return false
	end
	local data = DataService.GetData(player)
	if not data then
		return false -- сессию перехватили сразу после загрузки (игрока кикнули): дальше не строим
	end
	PlotService.ShowLevel(plot, data.museumLevel)
	GymService.OnPlayerLoaded(player, plot)
	MuseumService.LoadMuseum(player)
	InventoryService.Sync(player)
	DefenseService.OnPlayerLoaded(player) -- поставленное к ещё не прошедшей ночи — снова в запасе
	DefenseService.Sync(player)
	Notify.Send(
		player,
		("Ваш музей — участок %d (ищите табличку со своим именем)"):format(
			plot.index
		)
	)
	return true
end

-- Игрок вышел: предмет из рук исчезает (D3), экспонаты выгружаются, участок свободен, профиль сохраняется.
-- Каждый шаг — отдельно (D52): ошибка в одном не оставляет профиль занятым (вход на другой сервер ждал бы перехвата
-- сессии) и участок — за ушедшим; сессия профиля закрывается всегда, последней.
function PlayerSession.Leave(player: Player)
	local steps = {
		{ "кража", TheftService.OnPlayerLeaving }, -- вор провалил, у ушедшего владельца — отменена (D46)
		{ "защита", DefenseService.OnPlayerLeaving }, -- установленная защита убирается (не сохраняется, D37)
		{ "руки", CarryService.OnPlayerRemoving },
		{ "музей", MuseumService.UnloadMuseum },
		{ "участок", PlotService.Release },
	}
	for _, step in steps do
		local ok, err = pcall(step[2], player)
		if not ok then
			Log.Warn(
				"PlayerSession",
				("выход %s, шаг «%s»: %s"):format(tostring(player.Name), step[1], tostring(err))
			)
		end
	end
	local ok, err = pcall(DataService.Release, player)
	if not ok then
		Log.Warn(
			"PlayerSession",
			("выход %s, сохранение: %s"):format(tostring(player.Name), tostring(err))
		)
	end
end

return PlayerSession

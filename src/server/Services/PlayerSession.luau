-- Вход и выход игрока: участок, профиль, гантель, музей, хранилище — в одном порядке для игры и серверных тестов
-- (Main вызывает Join/Leave на PlayerAdded/PlayerRemoving, Server/Tests — для тестовых игроков с профилем в памяти).
-- Зависит от CarryService, DataService, GymService, MuseumService, PlotService, StorageService, Util/Notify.

local ServerScriptService = game:GetService("ServerScriptService")

local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local DataService = require(Server.Services.DataService)
local GymService = require(Server.Services.GymService)
local MuseumService = require(Server.Services.MuseumService)
local PlotService = require(Server.Services.PlotService)
local StorageService = require(Server.Services.StorageService)
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
	if not DataService.LoadAsync(player, options and options.mock) then
		return false
	end
	PlotService.ShowLevel(plot, DataService.GetData(player).museumLevel)
	GymService.OnPlayerLoaded(player, plot)
	MuseumService.LoadMuseum(player)
	StorageService.Sync(player)
	Notify.Send(
		player,
		("Ваш музей — участок %d (ищите табличку со своим именем)"):format(
			plot.index
		)
	)
	return true
end

-- Игрок вышел: предмет из рук исчезает (D3), экспонаты выгружаются, участок свободен, профиль сохраняется.
function PlayerSession.Leave(player: Player)
	CarryService.OnPlayerRemoving(player)
	MuseumService.UnloadMuseum(player)
	PlotService.Release(player)
	DataService.Release(player)
end

return PlayerSession

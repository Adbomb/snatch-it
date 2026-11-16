-- Тестовый режим владельца в опубликованном DEV-месте (решение владельца 2026-11-16: проверить Короля-дракона обычным
-- клиентом Roblox). Решает, какой это сервер:
--   "Off"    — режим недоступен: Studio (там свой путь — DevMode), выключен настройкой GameConfig.OwnerTest.Enabled
--              или это не подтверждённое место (вселенная UniverseId и место PlaceId). Ничего не создаётся.
--   "Normal" — обычный сервер подтверждённого места: игра как всегда, владельцу доступна только команда /test.
--   "Test"   — резервный сервер этого места (PrivateServerId есть, владельца частного сервера нет: такой создаёт только
--              команда /test, Services/OwnerTestService). Здесь играет только владелец, все профили — в памяти
--              (ProfileStore.Mock — ни PlayerData, ни Transfers не пишутся), закрытые боссы стоят на тестовых
--              площадках (BossService.ClosedAllowed).
-- Владелец — создатель места (game.CreatorId при CreatorType = User). Чистые функции Kind и IsOwnerId — для серверных
-- тестов. Зависит от GameConfig.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

export type Kind = "Off" | "Normal" | "Test"
export type ServerInfo = {
	studio: boolean,
	gameId: number,
	placeId: number,
	privateServerId: string,
	privateServerOwnerId: number,
}

local OwnerTest = {}

-- Вид сервера по настройке cfg (GameConfig.OwnerTest) и сведениям о сервере info.
function OwnerTest.Kind(cfg: any, info: ServerInfo): Kind
	if info.studio or type(cfg) ~= "table" or cfg.Enabled ~= true then
		return "Off"
	end
	if info.gameId ~= cfg.UniverseId or info.placeId ~= cfg.PlaceId then
		return "Off"
	end
	if info.privateServerId ~= "" and info.privateServerOwnerId == 0 then
		return "Test" -- резервный сервер (у частного сервера игрока владелец есть)
	end
	return "Normal"
end

-- Сведения о текущем сервере.
function OwnerTest.CurrentInfo(): ServerInfo
	return {
		studio = RunService:IsStudio(),
		gameId = game.GameId,
		placeId = game.PlaceId,
		privateServerId = game.PrivateServerId,
		privateServerOwnerId = game.PrivateServerOwnerId,
	}
end

local cached: Kind? = nil

-- Вид этого сервера (не меняется за время жизни сервера).
function OwnerTest.ServerKind(): Kind
	if not cached then
		cached = OwnerTest.Kind(GameConfig.OwnerTest, OwnerTest.CurrentInfo())
	end
	return cached :: Kind
end

function OwnerTest.IsTestServer(): boolean
	return OwnerTest.ServerKind() == "Test"
end

-- Владелец ли userId: место принадлежит пользователю (не группе) с этим id.
function OwnerTest.IsOwnerId(userId: number, creatorType: Enum.CreatorType, creatorId: number): boolean
	return creatorType == Enum.CreatorType.User and creatorId > 0 and userId == creatorId
end

function OwnerTest.IsOwner(player: Player): boolean
	return player.Parent == Players and OwnerTest.IsOwnerId(player.UserId, game.CreatorType, game.CreatorId)
end

return OwnerTest

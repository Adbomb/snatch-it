-- Команды тестового режима владельца в чате (решение владельца 2026-11-16; где и что разрешено — Util/OwnerTest).
-- Команды принимает только владелец места (сервер проверяет каждый раз), остальным они ничего не делают:
--   обычный сервер подтверждённого DEV-места: /test — перенос на новый резервный тестовый сервер (только владелец);
--   тестовый сервер: /fight — бой с Королём-драконом за предмет Slot (HP бойца и босса только этого боя —
--   GameConfig.OwnerTest, профиль, сила и числа боя не меняются), /win — HP босса 1 и боец ближе к морде (следующий
--   удар — победа), /day и /night — переход к фазе (бой ночью не начинается), /exit — на обычный сервер, /help.
-- На тестовом сервере все профили — в памяти (Main: PlayerSession.Join с mock), поэтому ни бой, ни награда, ни
-- что-либо ещё не попадает в сохранения. Команды — через Player.Chatted (работает и со старым, и с новым чатом).
-- Зависит от Util/OwnerTest, BattleService, BossLootService, TimeService, GameConfig, Util/Notify, Util/Log.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local TeleportService = game:GetService("TeleportService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Server = ServerScriptService.Server
local BattleService = require(Server.Services.BattleService)
local BossLootService = require(Server.Services.BossLootService)
local TimeService = require(Server.Services.TimeService)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local OwnerTest = require(Server.Util.OwnerTest)

local OwnerTestService = {}

local lastCommand: { [Player]: number } = {}
local teleporting: { [Player]: boolean } = {}

local HELP =
	"Тест: /fight — бой с драконом, /win — победа, /day, /night, /exit — выйти"

-- Перенос владельца: на новый резервный сервер (reserve) или на обычный сервер места.
local function teleport(player: Player, reserve: boolean)
	if teleporting[player] then
		return
	end
	teleporting[player] = true
	local options = Instance.new("TeleportOptions")
	options.ShouldReserveServer = reserve
	local ok, err = pcall(function()
		TeleportService:TeleportAsync(game.PlaceId, { player }, options)
	end)
	if not ok then
		teleporting[player] = nil
		Log.Warn("OwnerTestService", "перенос не удался: " .. tostring(err))
		Notify.Send(player, "Перенос не удался, попробуйте ещё раз", "Stop")
	end
end

-- HP только этого боя и место бойца в осях босса (x — левый бок, z — вперёд), лицом к боссу.
local function setUp(fight: any, hp: number?, bossHp: number, at: Vector2)
	if hp then
		fight.hp, fight.maxHp = hp, hp
		fight.player:SetAttribute("BattleMaxHP", hp)
	end
	fight.bossHp, fight.bossMax = bossHp, bossHp
	fight.boss.model:SetAttribute("MaxHP", bossHp)
	local character = fight.player.Character
	if character then
		local boss = fight.boss
		local point = boss.root.CFrame:PointToWorldSpace(Vector3.new(at.X, 0, at.Y))
		local y = boss.home.Position.Y + 3
		local look = Vector3.new(boss.root.Position.X, y, boss.root.Position.Z)
		character:PivotTo(CFrame.lookAt(Vector3.new(point.X, y, point.Z), look))
	end
end

local function startFight(player: Player)
	local cfg = GameConfig.OwnerTest
	if BattleService.Handlers.FightOf(player) then
		Notify.Send(player, "Бой уже идёт: /win — победа", "Stop")
		return
	end
	local _, part = BossLootService.SlotItem(cfg.Zone, cfg.Slot)
	local character = player.Character
	if not part or not character then
		Notify.Send(player, "Нет предмета у босса или персонажа", "Stop")
		return
	end
	character:PivotTo(CFrame.new(part.Position + Vector3.new(0, 3, 5)))
	task.wait(0.3)
	local fight = BattleService.Begin(player, cfg.Zone, cfg.Slot)
	if fight then -- отказ Begin уже сообщил игроку
		setUp(fight, cfg.FightHp, cfg.BossHp, cfg.FightAt)
		Notify.Send(player, "Тестовый бой начат (в сохранения не попадает)", "Go")
	end
end

local function win(player: Player)
	local fight = BattleService.Handlers.FightOf(player)
	if not fight then
		Notify.Send(player, "Сначала /fight", "Stop")
		return
	end
	setUp(fight, nil, 1, GameConfig.OwnerTest.WinAt)
	Notify.Send(player, "У босса 1 HP — следующий удар побеждает", "Go")
end

local function onChat(player: Player, message: string)
	if not OwnerTest.IsOwner(player) then
		return -- команды только владельцу
	end
	local command = string.lower(string.match(message, "^%s*(/%S+)") or "")
	if command == "" then
		return
	end
	local now = os.clock()
	if now - (lastCommand[player] or -math.huge) < GameConfig.OwnerTest.CommandCooldown then
		return
	end
	lastCommand[player] = now
	local kind = OwnerTest.ServerKind()
	if kind == "Normal" then
		if command == "/test" then
			Notify.Send(player, "Перенос на тестовый сервер…", "Info")
			teleport(player, true)
		end
		return
	end
	if kind ~= "Test" then
		return
	end
	if command == "/fight" then
		startFight(player)
	elseif command == "/win" then
		win(player)
	elseif command == "/day" or command == "/night" then
		local state = TimeService.SkipTo(if command == "/day" then "Day" else "Night", 0)
		Notify.Send(player, if state then "Фаза: " .. state.phase else "Не получилось", "Info")
	elseif command == "/exit" then
		Notify.Send(player, "Перенос на обычный сервер…", "Info")
		teleport(player, false)
	elseif command == "/help" then
		Notify.Send(player, HELP, "Info")
	end
end

local function watch(player: Player)
	player.Chatted:Connect(function(message: string)
		onChat(player, message)
	end)
end

-- Владелец вошёл на тестовый сервер (Main, после загрузки профиля в памяти).
function OwnerTestService.Welcome(player: Player)
	Notify.Send(
		player,
		"Тестовый сервер владельца: прогресс здесь не сохраняется",
		"Info"
	)
	Notify.Send(player, HELP, "Info")
end

function OwnerTestService.Init()
	local kind = OwnerTest.ServerKind()
	if kind == "Off" then
		return -- Studio, режим выключен или чужое место: ничего не создаётся
	end
	Players.PlayerAdded:Connect(watch)
	for _, player in Players:GetPlayers() do
		watch(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		lastCommand[player] = nil
		teleporting[player] = nil
	end)
	TeleportService.TeleportInitFailed:Connect(function(player: Player, result, message: string)
		teleporting[player] = nil
		Log.Warn("OwnerTestService", ("перенос не начался: %s %s"):format(tostring(result), message))
		Notify.Send(player, "Перенос не удался, попробуйте ещё раз", "Stop")
	end)
	Log.Debug("OwnerTestService", "Тестовый режим владельца: сервер " .. kind)
end

-- Для серверных тестов.
OwnerTestService.Handlers = {
	OnChat = onChat,
	StartFight = startFight,
	Win = win,
}

return OwnerTestService

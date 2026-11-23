-- Тестовый режим владельца: действия (решение владельца 2026-11-16; где и что разрешено — Util/OwnerTest).
-- Действия принимает только владелец места (сервер проверяет каждый раз: владелец, вид сервера, пауза между
-- действиями), остальным они ничего не делают. Два входа с одним обработчиком:
--   кнопка «Тест» в HUD владельца (Controllers/OwnerTestController, RemoteEvent OwnerTest — имя действия) —
--     добавлена 2026-11-17: на телефоне чат неудобен или недоступен, из-за чего дракона было не открыть;
--   команды чата (Player.Chatted): /test, /goto, /fight, /win, /day, /night, /exit, /help.
-- Обычный сервер подтверждённого DEV-места: Test — перенос на новый резервный тестовый сервер.
-- Тестовый сервер: Goto — к спящему дракону; Fight — бой за предмет Slot (HP бойца и босса только этого боя —
-- GameConfig.OwnerTest, профиль, сила и числа боя не меняются); Win — HP босса 1 и боец ближе к морде (следующий удар
-- — победа); Day и Night — переход к фазе (бой ночью не начинается); Exit — на обычный сервер.
-- На тестовом сервере все профили — в памяти (Main: PlayerSession.Join с mock), поэтому ни бой, ни награда, ни
-- что-либо ещё не попадает в сохранения. Владельцу ставится атрибут игрока OwnerTest = "Normal" | "Test" — по нему
-- клиент показывает кнопку (сам атрибут прав не даёт).
-- Зависит от Util/OwnerTest, BattleService, BossLootService, BossService, TimeService, GameConfig, Shared/Remotes,
-- Util/Notify, Util/Log.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local TeleportService = game:GetService("TeleportService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Server = ServerScriptService.Server
local BattleService = require(Server.Services.BattleService)
local BossLootService = require(Server.Services.BossLootService)
local BossService = require(Server.Services.BossService)
local TimeService = require(Server.Services.TimeService)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local OwnerTest = require(Server.Util.OwnerTest)

local OwnerTestService = {}

local lastAction: { [Player]: number } = {}
local teleporting: { [Player]: boolean } = {}

local HELP = "Тест: кнопка «Тест» или чат — /goto, /fight, /win, /day, /night, /exit"
-- команда чата → действие
local CHAT = {
	["/test"] = "Test",
	["/goto"] = "Goto",
	["/fight"] = "Fight",
	["/win"] = "Win",
	["/day"] = "Day",
	["/night"] = "Night",
	["/exit"] = "Exit",
	["/help"] = "Help",
}

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

-- Поставить персонажа в точку at осей босса (x — левый бок, z — вперёд), лицом к боссу.
local function standAt(player: Player, boss: any, at: Vector2): boolean
	local character = player.Character
	if not character then
		return false
	end
	local point = boss.root.CFrame:PointToWorldSpace(Vector3.new(at.X, 0, at.Y))
	local y = boss.home.Position.Y + 3
	local look = Vector3.new(boss.root.Position.X, y, boss.root.Position.Z)
	character:PivotTo(CFrame.lookAt(Vector3.new(point.X, y, point.Z), look))
	return true
end

-- HP только этого боя и место бойца.
local function setUp(fight: any, hp: number?, bossHp: number, at: Vector2)
	if hp then
		fight.hp, fight.maxHp = hp, hp
		fight.player:SetAttribute("BattleMaxHP", hp)
	end
	fight.bossHp, fight.bossMax = bossHp, bossHp
	fight.boss.model:SetAttribute("MaxHP", bossHp)
	standAt(fight.player, fight.boss, at)
end

-- К спящему дракону: посмотреть модель, текстуры и ауру без боя.
local function goTo(player: Player)
	local cfg = GameConfig.OwnerTest
	if BattleService.Handlers.FightOf(player) then
		Notify.Send(player, "Идёт бой: «Победа» завершит его", "Stop")
		return
	end
	local boss = BossService.Get(cfg.Zone)
	if not boss or not standAt(player, boss, cfg.ViewAt) then
		Notify.Send(player, "Дракона или персонажа нет", "Stop")
		return
	end
	Notify.Send(player, "Король-дракон перед вами", "Go")
end

local function startFight(player: Player)
	local cfg = GameConfig.OwnerTest
	if BattleService.Handlers.FightOf(player) then
		Notify.Send(player, "Бой уже идёт: «Победа» завершит его", "Stop")
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
		Notify.Send(player, "Сначала начните бой", "Stop")
		return
	end
	setUp(fight, nil, 1, GameConfig.OwnerTest.WinAt)
	Notify.Send(player, "У босса 1 HP — следующий удар побеждает", "Go")
end

-- Действие владельца на сервере вида kind. Чужой игрок, неизвестное действие, слишком частое или не для этого
-- вида сервера — ничего не происходит.
local function run(player: Player, action: string, kind: OwnerTest.Kind)
	if not OwnerTest.IsOwner(player) then
		return
	end
	local now = os.clock()
	if now - (lastAction[player] or -math.huge) < GameConfig.OwnerTest.CommandCooldown then
		return
	end
	lastAction[player] = now
	if kind == "Normal" then
		if action == "Test" then
			Notify.Send(player, "Перенос на тестовый сервер…", "Info")
			teleport(player, true)
		end
		return
	end
	if kind ~= "Test" then
		return
	end
	if action == "Goto" then
		goTo(player)
	elseif action == "Fight" then
		startFight(player)
	elseif action == "Win" then
		win(player)
	elseif action == "Day" or action == "Night" then
		local state = TimeService.SkipTo(action :: any, 0)
		Notify.Send(player, if state then "Фаза: " .. state.phase else "Не получилось", "Info")
	elseif action == "Exit" then
		Notify.Send(player, "Перенос на обычный сервер…", "Info")
		teleport(player, false)
	elseif action == "Help" then
		Notify.Send(player, HELP, "Info")
	end
end

local function onChat(player: Player, message: string)
	local action = CHAT[string.lower(string.match(message, "^%s*(/%S+)") or "")]
	if action then
		run(player, action, OwnerTest.ServerKind())
	end
end

-- Запрос кнопки HUD: клиент присылает только имя действия.
local function onRemote(player: Player, action: any)
	if type(action) ~= "string" or #action > 12 then
		return
	end
	run(player, action, OwnerTest.ServerKind())
end

local function watch(player: Player)
	if OwnerTest.IsOwner(player) then
		player:SetAttribute("OwnerTest", OwnerTest.ServerKind()) -- клиент покажет кнопку «Тест»
	end
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
	Notify.Send(
		player,
		"Кнопка «Тест» слева: к дракону, бой, победа, день и ночь",
		"Info"
	)
end

function OwnerTestService.Init()
	local kind = OwnerTest.ServerKind()
	if kind == "Off" then
		return -- Studio, режим выключен или чужое место: ничего не создаётся, запросы никто не слушает
	end
	Remotes.Get(Remotes.Names.OwnerTest).OnServerEvent:Connect(onRemote)
	Players.PlayerAdded:Connect(watch)
	for _, player in Players:GetPlayers() do
		watch(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		lastAction[player] = nil
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
	OnRemote = onRemote,
	Run = run,
	StartFight = startFight,
	GoTo = goTo,
	Win = win,
}

return OwnerTestService

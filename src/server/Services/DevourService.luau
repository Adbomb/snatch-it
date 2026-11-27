-- Вместо боя после поимки (D74, этап А): босс «съедает» пойманное существо и «отрыгивает» этаж. Сервер сразу, в том
-- же кадре, бросает редкость этажа (Shared/FloorRules: шансы со сдвигом от редкости существа) и отдаёт существо в руки
-- поймавшему с этой редкостью (BossLootService.Award → реестр AtBoss → Carried, граф §1 не меняется). После выдачи —
-- катсцена: босс проходит состояния Wake → StandUp → Eat → FallAsleep → Sleep по времени (Config/Battle.Timeline и
-- Config/Devour), игроки рядом получают событие DevourCutscene. Катсцена ничего не решает: выход, гибель и ночь во
-- время неё — как для любой переноски; пока босс не начал засыпать, новая поимка у него не начинается
-- (DevourService.Eating, BattleService.Busy). Если состоянием босса занялся кто-то другой (бой владельца, DEV) —
-- катсцена молча отступает.
-- DevourService.Roll — подмена случайного числа 0…1 (тесты и DEV); nil — обычный Random.
-- DevourService.TimeScale — множитель длительностей катсцены (тесты): 0 — без катсцены, состояние босса не меняется.
-- Зависит от BossLootService, BossService, ItemRegistry, Remotes, Config/Items, Config/FloorRarity, Config/Battle,
-- Config/Devour, Shared/FloorRules, Util/Validate, Util/Log.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Battle = require(ReplicatedStorage.Shared.Config.Battle)
local Devour = require(ReplicatedStorage.Shared.Config.Devour)
local FloorRarity = require(ReplicatedStorage.Shared.Config.FloorRarity)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local FloorRules = require(ReplicatedStorage.Shared.FloorRules)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Server = ServerScriptService.Server
local BossLootService = require(Server.Services.BossLootService)
local BossService = require(Server.Services.BossService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local Log = require(Server.Util.Log)
local Validate = require(Server.Util.Validate)

local DevourService = {}

DevourService.Roll = nil :: (() -> number)?
DevourService.TimeScale = 1

local rng = Random.new()
-- [зона] = номер идущей катсцены (новая поимка во время засыпания начинает следующую, прежняя отступает)
local eating: { [number]: number } = {}
local serial = 0

-- Идёт ли у босса катсцена до засыпания: в это время новая поимка не начинается.
function DevourService.Eating(zone: number): boolean
	local boss = BossService.Get(zone)
	return eating[zone] ~= nil and boss ~= nil and boss.state ~= "FallAsleep" and boss.state ~= "Sleep"
end

-- Событие катсцены: игрокам рядом с боссом и поймавшему (тестовому игроку — в его журнал).
local function announce(boss: BossService.Boss, player: any, itemId: string, key: string, scale: number)
	local tl = Battle.Timeline
	local at = workspace:GetServerTimeNow()
	local eat = at + (tl.Wake + tl.StandUp) * scale
	local burp = eat + (Devour.Grab + Devour.Chew) * scale
	local payload = {
		boss = boss.zone,
		user = player.UserId,
		itemId = itemId,
		floor = key,
		at = at,
		eat = eat,
		burp = burp,
		sleep = burp + Devour.Burp * scale,
	}
	local position = BossService.Position(boss)
	local sent = false
	for _, other in Players:GetPlayers() do
		local root = Validate.GetLiveRoot(other)
		if other == player or (root and (root.Position - position).Magnitude <= Devour.SeeRadius) then
			Remotes.FireClient(Remotes.Names.DevourCutscene, other, payload)
			sent = sent or other == player
		end
	end
	if not sent then
		Remotes.FireClient(Remotes.Names.DevourCutscene, player, payload)
	end
end

-- Состояния босса по времени. Каждый шаг проверяет, что катсцена всё ещё эта и что состояние босса никто не сменил.
local function cutscene(boss: BossService.Boss, scale: number)
	local zone = boss.zone
	serial += 1
	local token = serial
	eating[zone] = token
	local tl = Battle.Timeline
	local steps = {
		{ "Wake", tl.Wake },
		{ "StandUp", tl.StandUp },
		{ "Eat", Devour.Grab + Devour.Chew + Devour.Burp },
		{ "FallAsleep", tl.FallAsleep },
	}
	task.spawn(function()
		local expected = boss.state
		for _, step in steps do
			if eating[zone] ~= token then
				return -- началась следующая катсцена
			end
			if boss.state ~= expected then
				eating[zone] = nil -- боссом занялся кто-то другой (бой владельца, DEV)
				return
			end
			BossService.SetState(boss, step[1])
			expected = step[1]
			task.wait(step[2] * scale)
		end
		if eating[zone] ~= token then
			return
		end
		eating[zone] = nil
		if boss.state == "FallAsleep" then
			BossService.SetState(boss, "Sleep")
		end
	end)
end

-- Поимка удалась: бросок редкости этажа и выдача существа слота slot босса boss игроку player (слот уже закреплён за
-- ним — BossLootService.Reserve в начале поимки). Возвращает ключ редкости этажа; nil — выдать не удалось (существа
-- уже нет, руки заняты): предмет остаётся у босса, слот освобождает вызывающий, катсцены нет.
function DevourService.Begin(player: Player, boss: number, slot: number): string?
	local uid = BossLootService.SlotItem(boss, slot)
	local entry = uid and ItemRegistry.Get(uid)
	if not entry or entry.state ~= "AtBoss" then
		return nil
	end
	local itemId = entry.itemId
	local def = Items[itemId]
	local hook = DevourService.Roll
	local roll = if hook then hook() else rng:NextNumber()
	local key = FloorRules.Roll(if def then def.rarity else nil, roll)
	if not BossLootService.Award(boss, slot, player, key) then
		return nil
	end
	Log.Debug(
		"DevourService",
		("%s: босс %d съел %s — этаж «%s»"):format(player.Name, boss, itemId, FloorRarity.Names[key])
	)
	-- показ: после выдачи и без yield в этом кадре (состояния идут в своём потоке)
	local model = BossService.Get(boss)
	local scale = DevourService.TimeScale
	if model and scale > 0 then
		announce(model, player, itemId, key, scale)
		cutscene(model, scale)
	end
	return key
end

return DevourService

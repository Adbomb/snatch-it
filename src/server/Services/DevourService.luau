-- Вместо боя после поимки (D74, этап А): босс «съедает» пойманное существо и «отрыгивает» этаж. Сервер сразу, в том
-- же кадре, бросает редкость этажа (Shared/FloorRules: шансы со сдвигом от редкости существа) и отдаёт существо в руки
-- поймавшему с этой редкостью (BossLootService.Award → реестр AtBoss → Carried, граф §1 не меняется). Катсцена и
-- прокрутка у клиентов (следующие подпункты этапа А) — только показ: решает этот модуль.
-- DevourService.Roll — подмена случайного числа 0…1 (тесты и DEV); nil — обычный Random.
-- Зависит от BossLootService, ItemRegistry, Config/Items, Config/FloorRarity, Shared/FloorRules, Util/Log.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local FloorRarity = require(ReplicatedStorage.Shared.Config.FloorRarity)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local FloorRules = require(ReplicatedStorage.Shared.FloorRules)
local Server = ServerScriptService.Server
local BossLootService = require(Server.Services.BossLootService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local Log = require(Server.Util.Log)

local DevourService = {}

DevourService.Roll = nil :: (() -> number)?

local rng = Random.new()

-- Поимка удалась: бросок редкости этажа и выдача существа слота slot босса boss игроку player (слот уже закреплён за
-- ним — BossLootService.Reserve в начале поимки). Возвращает ключ редкости этажа; nil — выдать не удалось (существа
-- уже нет, руки заняты): предмет остаётся у босса, слот освобождает вызывающий.
function DevourService.Begin(player: Player, boss: number, slot: number): string?
	local uid = BossLootService.SlotItem(boss, slot)
	local entry = uid and ItemRegistry.Get(uid)
	if not entry or entry.state ~= "AtBoss" then
		return nil
	end
	local def = Items[entry.itemId]
	local hook = DevourService.Roll
	local roll = if hook then hook() else rng:NextNumber()
	local key = FloorRules.Roll(if def then def.rarity else nil, roll)
	if not BossLootService.Award(boss, slot, player, key) then
		return nil
	end
	Log.Debug(
		"DevourService",
		("%s: босс %d съел %s — этаж «%s»"):format(
			player.Name,
			boss,
			entry.itemId,
			FloorRarity.Names[key]
		)
	)
	return key
end

return DevourService

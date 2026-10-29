-- Профили игроков через ProfileStore (с блокировкой сессии): загрузка, Reconcile, запись, сохранение.
-- Схема профиля — Config/ProfileTemplate (DESIGN.md §2). Повторы и pcall делает сам ProfileStore.
-- Зависит от Vendor/ProfileStore, ProfileTemplate, GameConfig, Util/Log.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local ProfileTemplate = require(ReplicatedStorage.Shared.Config.ProfileTemplate)
local ProfileStore = require(ServerScriptService.Server.Vendor.ProfileStore)
local Log = require(ServerScriptService.Server.Util.Log)

local store = ProfileStore.New(GameConfig.Data.StoreName, ProfileTemplate)
local profiles: { [Player]: any } = {}
local saveState: { [Player]: { last: number, pending: boolean } } = {}

local DataService = {}

local function getActiveProfile(player: Player): any
	local profile = profiles[player]
	if profile and profile:IsActive() then
		return profile
	end
	return nil
end

-- Загружает профиль (ждёт). true — профиль готов; false — игрока кикнули или он уже вышел.
function DataService.LoadAsync(player: Player): boolean
	local profile = store:StartSessionAsync(GameConfig.Data.KeyPrefix .. player.UserId, {
		Cancel = function()
			return player.Parent ~= Players
		end,
	})
	if profile == nil then
		if player.Parent == Players then
			player:Kick(
				"Не удалось загрузить сохранение. Попробуйте зайти ещё раз."
			)
		end
		return false
	end

	profile:AddUserId(player.UserId)
	profile:Reconcile()
	-- Миграция: schema 1 → 2 — новые поля (strength, dumbbellLevel) уже добавил Reconcile.
	if profile.Data.schema == 1 then
		profile.Data.schema = 2
	end
	if profile.Data.schema ~= ProfileTemplate.schema then
		Log.Warn(
			"DataService",
			("%s: schema %s, ожидалась %d"):format(
				player.Name,
				tostring(profile.Data.schema),
				ProfileTemplate.schema
			)
		)
	end

	profile.OnSessionEnd:Connect(function()
		profiles[player] = nil
		saveState[player] = nil
		if player.Parent == Players then
			player:Kick("Сохранение открыто на другом сервере. Перезайдите.")
		end
	end)

	if player.Parent ~= Players then
		profile:EndSession()
		return false
	end
	profiles[player] = profile
	Log.Debug(
		"DataService",
		("Профиль %s загружен, экспонатов: %d"):format(
			player.Name,
			DataService.CountItems(player)
		)
	)
	return true
end

-- Игрок вышел: сохранить и снять блокировку сессии.
function DataService.Release(player: Player)
	local profile = profiles[player]
	profiles[player] = nil
	saveState[player] = nil
	if profile then
		profile:EndSession()
	end
end

-- Данные профиля только для чтения; менять их можно лишь функциями ниже.
function DataService.GetData(player: Player): any
	local profile = getActiveProfile(player)
	return if profile then profile.Data else nil
end

function DataService.CountItems(player: Player): number
	local data = DataService.GetData(player)
	local count = 0
	if data then
		for _ in data.items do
			count += 1
		end
	end
	return count
end

function DataService.HasItem(player: Player, uid: string): boolean
	local data = DataService.GetData(player)
	return data ~= nil and data.items[uid] ~= nil
end

function DataService.IsSlotFree(player: Player, slot: number): boolean
	local data = DataService.GetData(player)
	if not data then
		return false
	end
	for _, record in data.items do
		if record.place == "slot" and record.slot == slot then
			return false
		end
	end
	return true
end

-- Запись экспоната. Один экземпляр — одно место: uid и витрина не должны быть заняты.
function DataService.AddItem(player: Player, uid: string, record: { [string]: any }): boolean
	local data = DataService.GetData(player)
	if not data then
		Log.Warn(
			"DataService",
			player.Name .. ": профиль не загружен, запись отклонена"
		)
		return false
	end
	if data.items[uid] ~= nil then
		Log.Warn("DataService", ("%s: uid %s уже есть в профиле"):format(player.Name, uid))
		return false
	end
	if record.place == "slot" and not DataService.IsSlotFree(player, record.slot) then
		Log.Warn(
			"DataService",
			("%s: витрина %s уже занята в профиле"):format(player.Name, tostring(record.slot))
		)
		return false
	end
	data.items[uid] = record
	return true
end

-- Перенос записи между витриной и хранилищем. Поворот (rot) сохраняется.
-- Откат — тот же вызов со старыми place/slot в том же кадре.
function DataService.SetItemPlace(player: Player, uid: string, place: string, slot: number?): boolean
	local data = DataService.GetData(player)
	local record = data and data.items[uid]
	if not record then
		Log.Warn("DataService", ("%s: uid %s нет в профиле"):format(player.Name, uid))
		return false
	end
	if place == "slot" then
		if type(slot) ~= "number" or not DataService.IsSlotFree(player, slot) then
			Log.Warn(
				"DataService",
				("%s: витрина %s занята или не указана"):format(player.Name, tostring(slot))
			)
			return false
		end
	elseif place ~= "storage" then
		return false
	end
	record.place = place
	record.slot = if place == "slot" then slot else nil
	return true
end

-- Обмен витринами двух экспонатов одного игрока. Откат — тот же вызов ещё раз.
function DataService.SwapItemSlots(player: Player, uidA: string, uidB: string): boolean
	local data = DataService.GetData(player)
	local a = data and data.items[uidA]
	local b = data and data.items[uidB]
	if not a or not b or a.place ~= "slot" or b.place ~= "slot" or uidA == uidB then
		Log.Warn("DataService", ("%s: обмен %s ↔ %s невозможен"):format(player.Name, uidA, uidB))
		return false
	end
	a.slot, b.slot = b.slot, a.slot
	return true
end

function DataService.SetItemRotation(player: Player, uid: string, rot: number): boolean
	local data = DataService.GetData(player)
	local record = data and data.items[uid]
	if not record then
		return false
	end
	record.rot = rot
	return true
end

-- Только для отката AddItem в том же кадре (без yield между ними), если переход в ItemRegistry отказал.
function DataService.RemoveItem(player: Player, uid: string)
	local data = DataService.GetData(player)
	if data then
		data.items[uid] = nil
	end
end

-- Сила от качания (D30): прибавка, потолок GameConfig.Gym.MaxStrength. Возвращает новую силу или nil.
function DataService.AddStrength(player: Player, amount: number): number?
	local data = DataService.GetData(player)
	if not data or amount ~= amount or amount <= 0 then
		return nil
	end
	data.strength = math.min(data.strength + amount, GameConfig.Gym.MaxStrength)
	return data.strength
end

-- Улучшение гантели за монеты: списывает price и поднимает уровень на 1. false — не хватает монет
-- или уровень уже последний (проверки — в GymService, здесь последняя защита данных).
function DataService.UpgradeDumbbell(player: Player, price: number, maxLevel: number): boolean
	local data = DataService.GetData(player)
	if not data or data.dumbbellLevel >= maxLevel or data.coins < price then
		return false
	end
	data.coins -= price
	data.dumbbellLevel += 1
	return true
end

-- Монеты (только DevTools в Studio, пока нет экономики шага 7).
function DataService.AddCoins(player: Player, amount: number): number?
	local data = DataService.GetData(player)
	if not data or amount ~= amount then
		return nil
	end
	data.coins = math.max(data.coins + amount, 0)
	return data.coins
end

function DataService.IncrementStat(player: Player, statName: string)
	local data = DataService.GetData(player)
	if data then
		data.stats[statName] = (data.stats[statName] or 0) + 1
	end
end

-- Внеочередное сохранение, не чаще раза в SaveCooldown секунд (лишние запросы склеиваются).
function DataService.RequestSave(player: Player)
	if not getActiveProfile(player) then
		return
	end
	local state = saveState[player]
	if not state then
		state = { last = -math.huge, pending = false }
		saveState[player] = state
	end
	if state.pending then
		return
	end
	local delay = state.last + GameConfig.Data.SaveCooldown - os.clock()
	state.pending = true
	task.delay(math.max(delay, 0), function()
		state.pending = false
		local profile = getActiveProfile(player)
		if profile then
			state.last = os.clock()
			profile:Save()
		end
	end)
end

return DataService

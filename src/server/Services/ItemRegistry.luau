-- Серверный реестр экземпляров предметов: uid → состояние и данные (DESIGN.md §1).
-- Единственное место, где меняется состояние; недопустимый переход = отказ + warn.
-- Зависит от HttpService, Config/Items, Util/Log.

local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")

local Items = require(ReplicatedStorage.Shared.Config.Items)
local Log = require(ServerScriptService.Server.Util.Log)

export type State = "AtBoss" | "OnMap" | "Carried" | "Displayed" | "Stored" | "Lifting" | "Stolen" | "Dropped"

export type Entry = {
	uid: string,
	itemId: string,
	state: State,
	carrier: Player?, -- кто несёт (Carried)
	owner: number?, -- UserId владельца (Displayed / Stored)
	slot: number?, -- номер витрины (Displayed)
	part: BasePart?, -- видимый предмет в мире (у Stored его нет)
	boss: number?, -- босс-источник (D37): с какого уровня предмет (для дохода, этап 6)
	bossSlot: number?, -- слот у босса, пока предмет там (AtBoss)
}

type Listener = (uid: string, fromState: State, toState: State?, entry: Entry) -> ()

-- Полный граф переходов из DESIGN.md §1 (+ AtBoss, D37). Реализованы AtBoss, OnMap, Carried, Displayed, Stored.
local ALLOWED: { [State]: { [State]: boolean } } = {
	AtBoss = { Carried = true }, -- забрать у босса (после победы, этап 4; пока — тестовый режим Studio)
	OnMap = { Carried = true },
	Carried = { OnMap = true, Displayed = true, Stored = true },
	Displayed = { Stored = true, Lifting = true },
	Stored = { Displayed = true },
	Lifting = { Stolen = true, Displayed = true },
	Stolen = { Displayed = true, Stored = true, Dropped = true },
	Dropped = { Displayed = true },
}

local entries: { [string]: Entry } = {}
local carrierIndex: { [Player]: string } = {} -- кто что несёт
local slotIndex: { [number]: { [number]: string } } = {} -- [владелец][витрина] = uid
local listeners: { Listener } = {}

local ItemRegistry = {}

local function refuse(uid: string, fromState: string, toState: string, reason: string): (boolean, string)
	Log.Warn("ItemRegistry", ("Отказ %s → %s (uid %s): %s"):format(fromState, toState, uid, reason))
	return false, reason
end

-- Носитель — настоящий игрок; в Studio ещё и тестовый игрок серверных тестов (Server/Tests/TestPlayer).
local function isCarrier(value: any): boolean
	if typeof(value) == "Instance" then
		return value:IsA("Player")
	end
	return RunService:IsStudio() and type(value) == "table" and value.IsTestPlayer == true
end

local function snapshot(entry: Entry): Entry
	return table.freeze(table.clone(entry))
end

local function notify(uid: string, fromState: State, toState: State?, entry: Entry)
	local copy = snapshot(entry)
	for _, listener in listeners do
		task.spawn(listener, uid, fromState, toState, copy)
	end
end

-- Снимает экземпляр со всех индексов текущего состояния (вызывается только после всех проверок).
local function detach(entry: Entry)
	if entry.carrier then
		carrierIndex[entry.carrier] = nil
		entry.carrier = nil
	end
	if entry.owner and entry.slot then
		local slots = slotIndex[entry.owner]
		if slots and slots[entry.slot] == entry.uid then
			slots[entry.slot] = nil
		end
	end
	entry.owner = nil
	entry.slot = nil
	entry.bossSlot = nil
end

local function occupySlot(entry: Entry, owner: number, slot: number)
	slotIndex[owner] = slotIndex[owner] or {}
	slotIndex[owner][slot] = entry.uid
	entry.owner = owner
	entry.slot = slot
end

local function isSlotFree(owner: number, slot: number): boolean
	local slots = slotIndex[owner]
	return slots == nil or slots[slot] == nil
end

-- Подписка на любые изменения: listener(uid, было, стало (nil = удалён), копия записи).
function ItemRegistry.OnChanged(listener: Listener)
	table.insert(listeners, listener)
end

-- Новый экземпляр на карте. uid выдаётся здесь и только здесь.
function ItemRegistry.CreateOnMap(itemId: string, part: BasePart): string
	assert(Items[itemId], "Нет предмета в Config/Items: " .. tostring(itemId))
	local uid = HttpService:GenerateGUID(false)
	while entries[uid] do
		uid = HttpService:GenerateGUID(false)
	end
	entries[uid] = { uid = uid, itemId = itemId, state = "OnMap", part = part }
	part:SetAttribute("ItemUid", uid)
	Log.Debug("ItemRegistry", ("Появился %s (%s)"):format(itemId, uid))
	return uid
end

-- Новый экземпляр у босса boss в слоте slot (D37). uid выдаётся здесь.
function ItemRegistry.CreateAtBoss(itemId: string, part: BasePart, boss: number, slot: number): string
	local uid = ItemRegistry.CreateOnMap(itemId, part)
	local entry = entries[uid]
	entry.state = "AtBoss"
	entry.boss = boss
	entry.bossSlot = slot
	return uid
end

-- Восстановление экспоната из сохранённого профиля (Displayed или Stored).
function ItemRegistry.Restore(
	uid: string,
	itemId: string,
	owner: number,
	place: string,
	slot: number?,
	part: BasePart?
): (boolean, string?)
	if entries[uid] then
		return refuse(uid, entries[uid].state, "Restore", "uid уже есть на сервере")
	end
	if not Items[itemId] then
		return refuse(uid, "-", "Restore", "нет предмета в Config/Items: " .. tostring(itemId))
	end
	local entry: Entry = { uid = uid, itemId = itemId, state = "Stored", part = part }
	if place == "slot" then
		if type(slot) ~= "number" or not part then
			return refuse(uid, "-", "Displayed", "для витрины нужны номер и Part")
		end
		if not isSlotFree(owner, slot) then
			return refuse(uid, "-", "Displayed", ("витрина %d уже занята"):format(slot))
		end
		entry.state = "Displayed"
		occupySlot(entry, owner, slot)
	elseif place == "storage" then
		entry.owner = owner
	else
		return refuse(uid, "-", "Restore", "неизвестное place: " .. tostring(place))
	end
	entries[uid] = entry
	if part then
		part:SetAttribute("ItemUid", uid)
	end
	return true, nil
end

-- Единая функция смены состояния. args зависят от целевого состояния:
--   Carried   { carrier = Player }
--   OnMap     {}
--   Displayed { owner = UserId, slot = number, part = BasePart (только из Stored: у хранимого нет Part) }
--   Stored    { owner = UserId } — Part экспоната удаляет вызывающий сервис
function ItemRegistry.Transition(uid: string, toState: State, args: { [string]: any }?): (boolean, string?)
	local params = args or {}
	local entry = entries[uid]
	if not entry then
		return refuse(uid, "?", toState, "нет такого uid")
	end
	local fromState = entry.state
	local allowed = ALLOWED[fromState]
	if not (allowed and allowed[toState]) then
		return refuse(uid, fromState, toState, "переход запрещён")
	end

	if toState == "Carried" then
		local carrier = params.carrier
		if not isCarrier(carrier) then
			return refuse(uid, fromState, toState, "не указан игрок")
		end
		if carrierIndex[carrier] then
			return refuse(uid, fromState, toState, carrier.Name .. " уже несёт предмет")
		end
		detach(entry)
		entry.carrier = carrier
		carrierIndex[carrier] = uid
	elseif toState == "OnMap" then
		detach(entry)
	elseif toState == "Displayed" then
		local owner, slot = params.owner, params.slot
		if type(owner) ~= "number" or type(slot) ~= "number" then
			return refuse(uid, fromState, toState, "не указан владелец или витрина")
		end
		if fromState == "Carried" and (entry.carrier :: Player).UserId ~= owner then
			return refuse(uid, fromState, toState, "выставить можно только в свой музей")
		end
		local part = params.part
		if fromState == "Stored" then
			if entry.owner ~= owner then
				return refuse(uid, fromState, toState, "предмет из чужого хранилища")
			end
			if typeof(part) ~= "Instance" or not part:IsA("BasePart") then
				return refuse(uid, fromState, toState, "для витрины нужен Part")
			end
		end
		if not isSlotFree(owner, slot) then
			return refuse(uid, fromState, toState, ("витрина %d уже занята"):format(slot))
		end
		detach(entry)
		occupySlot(entry, owner, slot)
		if fromState == "Stored" then
			entry.part = part
			part:SetAttribute("ItemUid", uid)
		end
	elseif toState == "Stored" then
		local owner = params.owner
		if type(owner) ~= "number" then
			return refuse(uid, fromState, toState, "не указан владелец")
		end
		if fromState == "Carried" and (entry.carrier :: Player).UserId ~= owner then
			return refuse(uid, fromState, toState, "убрать можно только в своё хранилище")
		elseif fromState == "Displayed" and entry.owner ~= owner then
			return refuse(uid, fromState, toState, "чужой экспонат")
		elseif fromState ~= "Carried" and fromState ~= "Displayed" then
			return refuse(uid, fromState, toState, "переход ещё не реализован (этап 5)")
		end
		detach(entry)
		entry.owner = owner
		entry.part = nil
	else
		return refuse(uid, fromState, toState, "переход ещё не реализован")
	end

	entry.state = toState
	Log.Debug("ItemRegistry", ("%s: %s → %s"):format(uid, fromState, toState))
	notify(uid, fromState, toState, entry)
	return true, nil
end

-- Перестановка экспоната на пустую витрину того же владельца. Меняет только индекс витрин:
-- состояние остаётся Displayed, профиль меняет вызывающий сервис в том же кадре.
function ItemRegistry.MoveSlot(owner: number, fromSlot: number, toSlot: number): (boolean, string?)
	local label = ("MoveSlot %d→%d"):format(fromSlot, toSlot)
	local uid = ItemRegistry.GetSlotItem(owner, fromSlot)
	local entry = uid and entries[uid]
	if not uid or not entry then
		return refuse("-", "Displayed", label, "на витрине нет экспоната")
	end
	if entry.state ~= "Displayed" then
		return refuse(uid, entry.state, label, "экспонат не на витрине")
	end
	if fromSlot == toSlot or not isSlotFree(owner, toSlot) then
		return refuse(uid, entry.state, label, "целевая витрина занята")
	end
	local slots = slotIndex[owner]
	slots[fromSlot] = nil
	slots[toSlot] = uid
	entry.slot = toSlot
	Log.Debug("ItemRegistry", ("%s: витрина %d → %d"):format(uid, fromSlot, toSlot))
	notify(uid, "Displayed", "Displayed", entry)
	return true, nil
end

-- Обмен витринами двух экспонатов одного владельца. Обе записи меняются без yield, состояние — Displayed.
function ItemRegistry.SwapSlots(owner: number, slotA: number, slotB: number): (boolean, string?)
	local label = ("SwapSlots %d↔%d"):format(slotA, slotB)
	local uidA = ItemRegistry.GetSlotItem(owner, slotA)
	local uidB = ItemRegistry.GetSlotItem(owner, slotB)
	local a = uidA and entries[uidA]
	local b = uidB and entries[uidB]
	if not uidA or not uidB or not a or not b or slotA == slotB then
		return refuse(uidA or "-", "Displayed", label, "на одной из витрин нет экспоната")
	end
	if a.state ~= "Displayed" or b.state ~= "Displayed" then
		return refuse(uidA, a.state, label, "экспонат не на витрине")
	end
	local slots = slotIndex[owner]
	slots[slotA], slots[slotB] = uidB, uidA
	a.slot, b.slot = slotB, slotA
	Log.Debug("ItemRegistry", ("%s ↔ %s: витрины %d ↔ %d"):format(uidA, uidB, slotA, slotB))
	notify(uidA, "Displayed", "Displayed", a)
	notify(uidB, "Displayed", "Displayed", b)
	return true, nil
end

-- D3: предмет с карты, из рук или у босса (обновление слотов, D37) пропадает без следа. Сохранённые
-- экспонаты так удалить нельзя.
function ItemRegistry.Discard(uid: string, reason: string): boolean
	local entry = entries[uid]
	if not entry then
		return false
	end
	if entry.state ~= "OnMap" and entry.state ~= "Carried" and entry.state ~= "AtBoss" then
		refuse(uid, entry.state, "Discard", "сохраняемый предмет нельзя уничтожить")
		return false
	end
	local fromState = entry.state
	detach(entry)
	entries[uid] = nil
	Log.Debug("ItemRegistry", ("%s удалён (%s)"):format(uid, reason))
	notify(uid, fromState, nil, entry)
	return true
end

-- Владелец вышел: экспонат выгружается из памяти сервера (в профиле он остаётся).
function ItemRegistry.Unload(uid: string): boolean
	local entry = entries[uid]
	if not entry then
		return false
	end
	if entry.state ~= "Displayed" and entry.state ~= "Stored" then
		refuse(uid, entry.state, "Unload", "выгружать можно только экспонаты")
		return false
	end
	local fromState = entry.state
	detach(entry)
	entries[uid] = nil
	notify(uid, fromState, nil, entry)
	return true
end

-- Копия записи только для чтения (изменить состояние через неё нельзя).
function ItemRegistry.Get(uid: string): Entry?
	local entry = entries[uid]
	return if entry then snapshot(entry) else nil
end

function ItemRegistry.GetCarriedBy(player: Player): string?
	return carrierIndex[player]
end

function ItemRegistry.GetSlotItem(owner: number, slot: number): string?
	local slots = slotIndex[owner]
	return if slots then slots[slot] else nil
end

function ItemRegistry.GetOwnedBy(owner: number): { string }
	local result = {}
	for uid, entry in entries do
		if entry.owner == owner and (entry.state == "Displayed" or entry.state == "Stored") then
			table.insert(result, uid)
		end
	end
	return result
end

-- Сколько экземпляров лежит в хранилище владельца.
function ItemRegistry.CountStored(owner: number): number
	local count = 0
	for _, entry in entries do
		if entry.owner == owner and entry.state == "Stored" then
			count += 1
		end
	end
	return count
end

return ItemRegistry

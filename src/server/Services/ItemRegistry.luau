-- Серверный реестр экземпляров предметов: uid → состояние и данные (DESIGN.md §1).
-- Единственное место, где меняется состояние; недопустимый переход = отказ + warn.
-- Зависит от HttpService, Config/Items, Util/Log.

local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Items = require(ReplicatedStorage.Shared.Config.Items)
local Log = require(ServerScriptService.Server.Util.Log)

export type State = "OnMap" | "Carried" | "Displayed" | "Stored" | "Lifting" | "Stolen" | "Dropped"

export type Entry = {
	uid: string,
	itemId: string,
	state: State,
	carrier: Player?, -- кто несёт (Carried)
	owner: number?, -- UserId владельца (Displayed / Stored)
	slot: number?, -- номер витрины (Displayed)
	part: BasePart?, -- видимый предмет в мире (у Stored его нет)
}

type Listener = (uid: string, fromState: State, toState: State?, entry: Entry) -> ()

-- Полный граф переходов из DESIGN.md §1. Этап 1 реализует только OnMap, Carried, Displayed.
local ALLOWED: { [State]: { [State]: boolean } } = {
	OnMap = { Carried = true },
	Carried = { OnMap = true, Displayed = true },
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
--   Displayed { owner = UserId, slot = number }
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
		if typeof(carrier) ~= "Instance" or not carrier:IsA("Player") then
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
		if not isSlotFree(owner, slot) then
			return refuse(uid, fromState, toState, ("витрина %d уже занята"):format(slot))
		end
		detach(entry)
		occupySlot(entry, owner, slot)
	else
		return refuse(uid, fromState, toState, "переход ещё не реализован (этап 1)")
	end

	entry.state = toState
	Log.Debug("ItemRegistry", ("%s: %s → %s"):format(uid, fromState, toState))
	notify(uid, fromState, toState, entry)
	return true, nil
end

-- D3: предмет с карты или из рук пропадает без следа. Сохранённые экспонаты так удалить нельзя.
function ItemRegistry.Discard(uid: string, reason: string): boolean
	local entry = entries[uid]
	if not entry then
		return false
	end
	if entry.state ~= "OnMap" and entry.state ~= "Carried" then
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

return ItemRegistry

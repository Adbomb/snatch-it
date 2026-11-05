--!strict
-- Журнал передачи владения при краже (DESIGN.md §6, D46): худший случай при падении сервера — задержка выдачи или
-- отмена кражи, но не дубль и не потеря. Решение «чей предмет» принимается по меткам самой передачи, а не по тому,
-- есть ли uid в профиле (uid мог потом уйти законно — следующей кражей):
--   у жертвы data.transfersOut[id] — «предмет ушёл по передаче id», у вора data.transfersIn[id] — «получен по id».
-- Метки пишутся в одном кадре с переносом записи (DataService.TransferItem), поэтому сохранение профиля содержит
-- либо и метку, и изменение предметов, либо ни то, ни другое.
-- Порядок передачи (TheftService):
--   1) журнал to_<вор>: { id, uid, from, record, at } — до любых изменений профилей;
--   2) один кадр: жертве — удалить запись + transfersOut[id]; вору — запись с pending = id + transfersIn[id];
--   3) дождаться сохранения жертвы, в котором есть transfersOut[id];
--   4) снять pending у вора, дождаться сохранения вора с transfersIn[id] и записью без pending, удалить запись журнала.
-- При загрузке вора Resolve по каждой записи журнала (и по записям с pending без журнала) решает, что делать, глядя на
-- сохранённые метки жертвы. Чистый модуль без Instance (проверяется в Lune, check_theft.luau). Ни от чего не зависит.

local TransferJournal = {}

export type Entry = {
	id: string,
	uid: string,
	from: number, -- UserId жертвы
	record: { [string]: any }, -- запись предмета для профиля вора
	at: number, -- время записи (os.time)
	state: string?, -- прежний формат (не используется)
}

export type Action = {
	kind: string, -- "grant" | "keep" | "drop" | "done" | "wait"
	uid: string,
	id: string,
	record: { [string]: any }?,
	journal: boolean, -- есть запись журнала (её удалить после подтверждения)
}

-- Сколько секунд передача может ждать сохранения жертвы, если её сессия ещё активна (живая сессия ещё не сохранила
-- удаление). Дольше — живой сессии без сохранения не бывает (автосохранение ProfileStore — раз в 300 с).
TransferJournal.SessionGrace = 1800

-- Метки старше этого (секунд) удаляются при загрузке, если на них не ссылаются журнал и pending.
TransferJournal.MarkerTtl = 30 * 24 * 3600

function TransferJournal.Key(thief: number): string
	return "to_" .. tostring(thief)
end

-- victimOut(from, id, age) → true (в сохранённых данных жертвы есть transfersOut[id]), false (нет, и живой сессии,
-- которая могла не успеть сохраниться, тоже нет), nil (неизвестно — подождать).
type VictimOut = (number, string, number) -> boolean?

local function decide(entry: Entry, data: any, now: number, victimOut: VictimOut, journal: boolean): Action
	local items = data.items or {}
	local marks = data.transfersIn or {}
	local mine = items[entry.uid]
	local base = { uid = entry.uid, id = entry.id, journal = journal }
	if marks[entry.id] ~= nil then
		-- получение уже сохранено у вора вместе с меткой
		if type(mine) ~= "table" or mine.pending ~= entry.id then
			base.kind = "done" -- подтверждено раньше или предмет потом законно ушёл — ничего не выдавать
			return base :: Action
		end
		local out = victimOut(entry.from, entry.id, now - entry.at)
		base.kind = if out == true then "keep" elseif out == false then "drop" else "wait"
		return base :: Action
	end
	-- у вора получения нет
	local out = victimOut(entry.from, entry.id, now - entry.at)
	if out == true then
		base.kind = "grant"
		base.record = entry.record
	elseif out == false then
		base.kind = "drop" -- жертва не сохранила удаление: кража не состоялась
	else
		base.kind = "wait"
	end
	return base :: Action
end

-- Решение по каждой незавершённой передаче при загрузке вора: записи журнала и записи с pending без журнала.
function TransferJournal.Resolve(entries: { Entry }, data: any, now: number, victimOut: VictimOut): { Action }
	local actions: { Action } = {}
	local seen: { [string]: boolean } = {}
	for _, entry in entries do
		if type(entry) == "table" and type(entry.id) == "string" and type(entry.uid) == "string" then
			seen[entry.id] = true
			table.insert(actions, decide(entry, data, now, victimOut, true))
		end
	end
	for uid, record in data.items or {} do
		if type(record) == "table" and type(record.pending) == "string" and not seen[record.pending] then
			local orphan: Entry = {
				id = record.pending,
				uid = uid,
				from = if type(record.from) == "number" then record.from else 0,
				record = record,
				at = if type(record.acquiredAt) == "number" then record.acquiredAt else 0,
			}
			table.insert(actions, decide(orphan, data, now, victimOut, false))
		end
	end
	return actions
end

-- Применяет действия к данным вора (в памяти). Возвращает ids записей журнала: done — удалить сразу; confirm —
-- удалить только после сохранения, в котором есть результат (Confirmed).
function TransferJournal.Apply(actions: { Action }, data: any, now: number): ({ string }, { Action })
	data.items = data.items or {}
	data.transfersIn = data.transfersIn or {}
	local done, confirm = {}, {}
	for _, action in actions do
		if action.kind == "grant" then
			if data.items[action.uid] == nil and action.record then
				local record = table.clone(action.record)
				record.pending = nil
				data.items[action.uid] = record
			end
			data.transfersIn[action.id] = { uid = action.uid, at = now }
			table.insert(confirm, action)
		elseif action.kind == "keep" then
			local record = data.items[action.uid]
			if type(record) == "table" and record.pending == action.id then
				record.pending = nil
			end
			table.insert(confirm, action)
		elseif action.kind == "drop" then
			local record = data.items[action.uid]
			if type(record) == "table" and record.pending == action.id then
				data.items[action.uid] = nil
			end
			data.transfersIn[action.id] = nil
			table.insert(confirm, action)
		elseif action.kind == "done" and action.journal then
			table.insert(done, action.id)
		end
	end
	return done, confirm
end

-- Сохранённые данные вора уже содержат результат действия (можно удалять запись журнала).
function TransferJournal.Confirmed(action: Action, saved: any): boolean
	local items = saved and saved.items or {}
	local marks = saved and saved.transfersIn or {}
	local record = items[action.uid]
	if action.kind == "grant" or action.kind == "keep" then
		return marks[action.id] ~= nil and type(record) == "table" and record.pending == nil
	elseif action.kind == "drop" then
		return marks[action.id] == nil and (type(record) ~= "table" or record.pending ~= action.id)
	end
	return true
end

-- Старые метки (на которые не ссылаются журнал и pending) удаляются.
function TransferJournal.Prune(data: any, entries: { Entry }, now: number)
	local keep: { [string]: boolean } = {}
	for _, entry in entries do
		if type(entry) == "table" and type(entry.id) == "string" then
			keep[entry.id] = true
		end
	end
	for _, record in data.items or {} do
		if type(record) == "table" and type(record.pending) == "string" then
			keep[record.pending] = true
		end
	end
	for _, field in { "transfersIn", "transfersOut" } do
		local marks = data[field]
		if type(marks) == "table" then
			for id, mark in marks do
				local at = if type(mark) == "table" and type(mark.at) == "number" then mark.at else 0
				if not keep[id] and now - at > TransferJournal.MarkerTtl then
					marks[id] = nil
				end
			end
		end
	end
end

return TransferJournal

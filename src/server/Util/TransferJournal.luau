--!strict
-- Журнал передачи владения при краже (DESIGN.md §6, D46): худший случай при падении сервера — задержка выдачи или
-- отмена кражи, но не дубль и не потеря. Чистая часть без Instance (проверяется в Lune, check_theft.luau); запись в
-- DataStore делает TheftService через переданное хранилище.
-- Порядок передачи (TheftService):
--   1) журнал to_<вор>: запись { id, uid, from, record, state = "pending", at } — до любых изменений профилей;
--   2) в одном кадре: у жертвы запись items[uid] удаляется, вору добавляется с pending = id (предмет «передаётся»:
--      его нельзя выставить);
--   3) сохранить жертву, дождаться записи → журнал state = "victimSaved";
--   4) сохранить вора → у записи вора pending снимается, запись журнала удаляется.
-- При загрузке вора Resolve решает по журналу (и, если нужно, по сохранённому профилю жертвы), что делать с каждой
-- передачей. Ни от чего не зависит.

local TransferJournal = {}

export type Entry = {
	id: string,
	uid: string,
	from: number, -- UserId жертвы
	record: { [string]: any }, -- запись предмета для профиля вора
	state: string, -- "pending" | "victimSaved"
	at: number, -- время записи (os.time)
}

export type Action = {
	kind: string, -- "keep" (снять pending), "grant" (выдать запись), "drop" (убрать запись вора), "wait" (решить позже)
	uid: string,
	id: string,
	record: { [string]: any }?,
}

-- Сколько секунд передача в state = "pending" ждёт, прежде чем её решат по профилю жертвы (жертва могла ещё не
-- успеть сохраниться на другом сервере).
TransferJournal.Grace = 120

-- Ключ журнала вора.
function TransferJournal.Key(thief: number): string
	return "to_" .. tostring(thief)
end

-- Решение для каждой незавершённой передачи при загрузке профиля вора.
--   entries — записи журнала вора; items — items его профиля; now — os.time();
--   victimHas(from, uid) → true / false / nil (сохранённый профиль жертвы прочитать не удалось).
-- Возвращает список действий; записи журнала с kind ~= "wait" после применения удаляются.
function TransferJournal.Resolve(
	entries: { Entry },
	items: { [string]: any },
	now: number,
	victimHas: (number, string) -> boolean?
): { Action }
	local actions: { Action } = {}
	local seen: { [string]: boolean } = {}
	for _, entry in entries do
		seen[entry.uid] = true
		local mine = items[entry.uid]
		local ours = type(mine) == "table" and mine.pending == entry.id
		if entry.state == "victimSaved" then
			-- жертва уже сохранена без предмета: он принадлежит вору
			table.insert(actions, {
				kind = if mine then "keep" else "grant",
				uid = entry.uid,
				id = entry.id,
				record = entry.record,
			})
		elseif now - entry.at < TransferJournal.Grace then
			table.insert(actions, { kind = "wait", uid = entry.uid, id = entry.id })
		else
			local has = victimHas(entry.from, entry.uid)
			if has == nil then
				table.insert(actions, { kind = "wait", uid = entry.uid, id = entry.id })
			elseif has then
				-- жертва сохранилась с предметом: кража не состоялась
				table.insert(actions, { kind = if ours then "drop" else "keep", uid = entry.uid, id = entry.id })
			else
				table.insert(actions, {
					kind = if mine then "keep" else "grant",
					uid = entry.uid,
					id = entry.id,
					record = entry.record,
				})
			end
		end
	end
	-- Запись вора с pending без журнала: журнал пишется до записи профиля, так быть не должно — решаем по жертве.
	for uid, record in items do
		if type(record) == "table" and record.pending ~= nil and not seen[uid] then
			local from = record.from
			local has = if type(from) == "number" then victimHas(from, uid) else nil
			if has == true then
				table.insert(actions, { kind = "drop", uid = uid, id = tostring(record.pending) })
			elseif has == false then
				table.insert(actions, { kind = "keep", uid = uid, id = tostring(record.pending) })
			else
				table.insert(actions, { kind = "wait", uid = uid, id = tostring(record.pending) })
			end
		end
	end
	return actions
end

-- Применяет действия к items профиля вора. Возвращает id записей журнала, которые можно удалить.
function TransferJournal.Apply(actions: { Action }, items: { [string]: any }): { string }
	local cleared = {}
	for _, action in actions do
		if action.kind == "grant" then
			if items[action.uid] == nil and action.record then
				local record = table.clone(action.record)
				record.pending = nil
				items[action.uid] = record
			end
			table.insert(cleared, action.id)
		elseif action.kind == "keep" then
			local record = items[action.uid]
			if type(record) == "table" then
				record.pending = nil
			end
			table.insert(cleared, action.id)
		elseif action.kind == "drop" then
			local record = items[action.uid]
			if type(record) == "table" and record.pending ~= nil then
				items[action.uid] = nil
			end
			table.insert(cleared, action.id)
		end
	end
	return cleared
end

return TransferJournal

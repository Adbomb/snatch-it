--!nocheck
-- Проверка краж Судной ночи без Roblox Studio (D37, D46): правила и лимиты (Server/Util/TheftLedger), гонки воров,
-- номер события на границах фаз (Shared/GameTime), передача владения с журналом (Server/Util/TransferJournal) — перебор
-- падения сервера на каждом шаге и автосохранений в любой момент: у предмета всегда ровно один владелец, без дублей
-- и потерь. Профили — таблицы в памяти. Запуск из корня репозитория: lune run scripts/lune/check_theft.luau.

local process = require("@lune/process")

local Env = require("./env")

local GameConfig = Env.Require("ReplicatedStorage.Shared.Config.GameConfig")
local GameTime = Env.Require("ReplicatedStorage.Shared.GameTime")
local TheftLedger = Env.Require("ServerScriptService.Server.Util.TheftLedger")
local TransferJournal = Env.Require("ServerScriptService.Server.Util.TransferJournal")

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

local HOLD = 3
local THIEF, THIEF2, OWNER, OWNER2 = 101, 102, 201, 202
local EVENT = 7

local function args(over)
	local a = {
		event = EVENT,
		phase = "Open",
		thief = THIEF,
		owner = OWNER,
		uid = "u1",
		slot = 1,
		displayedBy = OWNER,
		carrying = false,
		thiefDone = false,
		ownerLost = false,
		knocked = false,
	}
	for k, v in over or {} do
		a[k] = v
	end
	return a
end

print("Правила начала кражи:")
do
	local L = TheftLedger.new(HOLD)
	local cases = {
		{ { phase = "None" }, "вне Судной ночи" },
		{ { phase = "Delivery" }, "в 10 с доставки новую кражу не начать" },
		{ { owner = THIEF, displayedBy = THIEF }, "свой экспонат" },
		{ { displayedBy = 0 }, "не выставлен (Stored) — красть нельзя" },
		{ { displayedBy = OWNER2 }, "экспонат другого владельца на этом участке" },
		{ { carrying = true }, "руки заняты — второй предмет не взять" },
		{ { thiefDone = true }, "вор уже украл этой ночью (по профилю)" },
		{ { ownerLost = true }, "музей уже потерял предмет (по профилю)" },
		{ { knocked = true }, "оглушённый не крадёт" },
	}
	for _, case in cases do
		local ok = L:CanBegin(args(case[1]))
		check(not ok, "отказ: " .. case[2])
	end
	check(L:CanBegin(args()), "обычная кража разрешена")
end

print("Удержание 3 с и завершение:")
do
	local L = TheftLedger.new(HOLD)
	check(L:Begin(args(), 100), "начало удержания")
	check(
		not L:Complete(THIEF, "u1", 101, "Open"),
		"через 1 с не завершить (поддельный Triggered)"
	)
	check(not L:Complete(THIEF, "u2", 103.5, "Open"), "чужой uid не завершить")
	check(
		not L:Complete(THIEF, "u1", 103.5, nil),
		"после конца Судной ночи не завершить"
	)
	check(L:Complete(THIEF, "u1", 103, "Open"), "через 3 с завершено")
	check(not L:Complete(THIEF, "u1", 104, "Open"), "повторное завершение отклонено")
	check(not L:StartDelivery(THIEF, "u1", nil), "после 10 с доставки не сдать")
	check(L:StartDelivery(THIEF, "u1", "Delivery"), "в 10 с доставки сдать можно")
	check(not L:StartDelivery(THIEF, "u1", "Delivery"), "повторная сдача отклонена")
	check(L:Fail(THIEF) == nil, "во время передачи провал не срабатывает")
	local ok = L:Finish(THIEF, "u1")
	check(ok, "передача закончена")
	check(
		not L:Finish(THIEF, "u1"),
		"повторная выдача отклонена (нет двойной добычи)"
	)
	check(
		not L:CanBegin(args({ uid = "u9", owner = OWNER2, displayedBy = OWNER2 })),
		"второй успешной кражи нет"
	)
	check(
		not L:CanBegin(args({ thief = THIEF2, uid = "u3" })),
		"музей не теряет второй предмет"
	)
	check(
		L:CanBegin(args({ thief = THIEF2, owner = OWNER2, displayedBy = OWNER2, uid = "u4" })),
		"другой вор, другой музей — можно"
	)
	check(
		L:CanBegin(args({ event = EVENT + 1 })),
		"в следующую Судную ночь лимиты новые"
	)
end

print("Провал не тратит лимиты, резервы атомарны:")
do
	local L = TheftLedger.new(HOLD)
	check(L:Begin(args(), 0), "вор 1 начал в музее 1")
	check(
		not L:Begin(args({ thief = THIEF2, uid = "u1" }), 0),
		"вор 2 тот же экспонат одновременно — отказ"
	)
	check(
		not L:Begin(args({ thief = THIEF2, uid = "u2", slot = 2 }), 0),
		"вор 2 другой экспонат того же музея — отказ"
	)
	check(
		not L:Begin(args({ uid = "u5", owner = OWNER2, displayedBy = OWNER2 }), 0),
		"вор 1 вторую кражу параллельно — отказ"
	)
	local theft = L:Fail(THIEF)
	check(
		theft and theft.uid == "u1" and theft.slot == 1,
		"провал возвращает, что и откуда вернуть"
	)
	check(
		L:Begin(args({ thief = THIEF2, uid = "u1" }), 1),
		"после провала вор 2 может красть этот музей"
	)
	check(
		L:CanBegin(args({ uid = "u6", owner = OWNER2, displayedBy = OWNER2 })),
		"вор 1 после провала может красть снова"
	)
	check(L:Complete(THIEF2, "u1", 4, "Open") and L:StartDelivery(THIEF2, "u1", "Open"), "вор 2 донёс")
	local aborted = L:AbortDelivery(THIEF2)
	check(aborted and aborted.uid == "u1", "сорванная передача снимает резерв")
	check(
		L:CanBegin(args({ thief = THIEF2, uid = "u1" })),
		"сорванная передача не тратит лимиты"
	)
	-- много воров на один экспонат «одновременно»
	local L2 = TheftLedger.new(HOLD)
	local winners = 0
	for i = 1, 20 do
		if L2:Begin(args({ thief = 1000 + i }), 0) then
			winners += 1
		end
	end
	check(winners == 1, "20 воров на один экспонат: начал ровно один")
end

print("Номер события и фазы (GameTime):")
do
	local cfg = GameConfig.Time
	local length = GameTime.CycleLength()
	local base = cfg.Epoch + length * 500
	local doomStart = base + (cfg.DoomEvery - 1) * (cfg.DayLength + cfg.NightLength) + cfg.DayLength
	local doomEnd = doomStart + cfg.DoomNightLength
	local id = GameTime.DoomEventId(doomStart + 1)
	check(
		id ~= nil and GameTime.DoomEventId(doomEnd + 5) == id,
		"Судная ночь и её 10 с доставки — одно событие"
	)
	check(GameTime.DoomEventId(doomEnd + cfg.DeliveryGrace) == nil, "после доставки события нет")
	check(GameTime.DoomEventId(doomStart - 1) == nil, "в подготовку события нет")
	check(
		GameTime.DoomEventId(doomStart + length + 1) == id + 1,
		"следующая Судная ночь — следующий номер"
	)
end

print("Передача владения: падение сервера на каждом шаге (DESIGN §6):")
do
	local function copy(t)
		if type(t) ~= "table" then
			return t
		end
		local out = {}
		for k, v in t do
			out[k] = copy(v)
		end
		return out
	end
	local UID = "stolen"
	local RECORD =
		{ id = "Moai", mods = {}, place = "slot", slot = 2, rot = 0, acquiredAt = 1, source = "boss", boss = 1 }
	-- Шаги TheftService (TransferJournal, шапка): после шага k сервер может упасть; автосохранение любого из профилей
	-- может случиться после любого шага.
	local scenarios, bad = 0, 0
	for crashAfter = 0, 4 do
		for victimAuto = -1, 4 do
			for thiefAuto = -1, 4 do
				for _, late in { false, true } do
					scenarios += 1
					local victim = { items = { [UID] = copy(RECORD) } }
					local thief = { items = {} }
					local victimSaved, thiefSaved = copy(victim), copy(thief)
					local journal = {}
					local at = 1000
					local function steps(k)
						if k == 1 then
							table.insert(journal, {
								id = "t1",
								uid = UID,
								from = OWNER,
								record = {
									id = "Moai",
									mods = {},
									place = "storage",
									rot = 0,
									source = "raid",
									from = OWNER,
								},
								state = "pending",
								at = at,
							})
						elseif k == 2 then
							victim.items[UID] = nil
							local record = copy(journal[1].record)
							record.pending = "t1"
							thief.items[UID] = record
						elseif k == 3 then
							victimSaved = copy(victim)
							journal[1].state = "victimSaved"
						elseif k == 4 then
							thief.items[UID].pending = nil
							thiefSaved = copy(thief)
							table.clear(journal)
						end
					end
					for k = 0, crashAfter do
						if k > 0 then
							steps(k)
						end
						if victimAuto == k then
							victimSaved = copy(victim)
						end
						if thiefAuto == k then
							thiefSaved = copy(thief)
						end
					end
					-- После падения: вор загружается со своим сохранением, жертва — со своим.
					local now = if late then at + TransferJournal.Grace + 1 else at + 5
					local loaded = copy(thiefSaved)
					local actions = TransferJournal.Resolve(journal, loaded.items, now, function(from, uid)
						return from == OWNER and victimSaved.items[uid] ~= nil
					end)
					TransferJournal.Apply(actions, loaded.items)
					local victimOwns = victimSaved.items[UID] ~= nil
					local thiefRecord = loaded.items[UID]
					local thiefOwns = thiefRecord ~= nil and thiefRecord.pending == nil
					local journalWaits = false
					for _, action in actions do
						journalWaits = journalWaits or (action.uid == UID and action.kind == "wait")
					end
					local waiting = (thiefRecord ~= nil and thiefRecord.pending ~= nil) or journalWaits
					local okCase
					if late then
						okCase = (victimOwns ~= thiefOwns) and not waiting
					else
						-- раньше Grace передача может ждать, но никогда не выдаёт вору то, что осталось у жертвы
						okCase = not (victimOwns and thiefOwns) and (victimOwns or thiefOwns or waiting)
					end
					if not okCase then
						bad += 1
						print(
							("    сбой: падение после %d, автосохранение жертвы %d, вора %d, поздно %s — жертва %s, вор %s"):format(
								crashAfter,
								victimAuto,
								thiefAuto,
								tostring(late),
								tostring(victimOwns),
								tostring(thiefOwns)
							)
						)
					end
				end
			end
		end
	end
	check(
		bad == 0,
		("%d сценариев падения и автосохранений: ни дублей, ни потерь"):format(
			scenarios
		)
	)

	-- Жертва ещё не успела сохраниться на другом сервере: до Grace передачу не трогаем.
	local items = { [UID] = { id = "Moai", pending = "t1", from = OWNER } }
	local actions = TransferJournal.Resolve(
		{ { id = "t1", uid = UID, from = OWNER, record = {}, state = "pending", at = 1000 } },
		items,
		1010,
		function()
			return true
		end
	)
	check(
		#actions == 1 and actions[1].kind == "wait",
		"свежая передача ждёт, а не отбирается"
	)
	local unknown = TransferJournal.Resolve(
		{ { id = "t1", uid = UID, from = OWNER, record = {}, state = "pending", at = 0 } },
		items,
		1000,
		function()
			return nil
		end
	)
	check(
		unknown[1].kind == "wait",
		"профиль жертвы не прочитан — решение откладывается"
	)
end

print(("Проверок: %d, не прошло: %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end
print("Все проверки краж прошли")

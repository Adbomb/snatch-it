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

print("Пауза после сорванной попытки (D52):")
do
	local RETRY = GameConfig.Theft.RetrySeconds
	check(RETRY == 5, "пауза 5 с в конфиге")
	local L = TheftLedger.new(HOLD, nil, RETRY)
	-- «щит»: друг владельца держит 2.5 с, отпускает и снова жмёт — музей больше не занят им всю ночь
	check(L:Begin(args(), 100), "первая попытка")
	check(L:Fail(THIEF, 102.5) ~= nil, "отпустил на 2.5 с — провал")
	local ok, reason = L:Begin(args(), 102.6)
	check(not ok and reason ~= nil and reason:find("через") ~= nil, "сразу снова нельзя: " .. tostring(reason))
	check(not L:Begin(args(), 107.4), "через 4.9 с ещё нельзя")
	check(L:Begin(args({ thief = THIEF2 }), 102.7), "другой вор может красть из этого музея сразу")
	check(L:Fail(THIEF2, 103) ~= nil, "другой вор сорвался")
	check(L:Begin(args(), 107.6), "через 5 с первая попытка снова разрешена")
	-- пауза сброшена успешным началом; провал без вины вора (хозяин вышел) паузы не даёт
	check(L:Fail(THIEF) ~= nil, "провал без вины вора")
	check(L:Begin(args(), 107.7), "без вины — пауза не ставится")
	-- провал при переноске (бросил, время доставки вышло) — тоже пауза
	check(L:Complete(THIEF, "u1", 110.8, "Open"), "снято")
	check(L:Fail(THIEF, 111) ~= nil, "добычу уронил")
	check(not L:Begin(args({ uid = "u2", slot = 2 }), 112), "после провала с добычей — пауза")
	check(L:Begin(args({ uid = "u2", slot = 2 }), 116.1), "после паузы — можно")
	-- без паузы в конфиге (retry 0) — как раньше
	local L0 = TheftLedger.new(HOLD)
	check(L0:Begin(args(), 0) and L0:Fail(THIEF, 1) ~= nil and L0:Begin(args(), 1), "без паузы — сразу")
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

print(
	"Передача владения: падение сервера, несвежие сохранения, повторный вход (DESIGN §6, метки передачи):"
)
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
	local UID, ID, AT = "stolen", "t1", 1000
	local RECORD =
		{ id = "Moai", mods = {}, place = "slot", slot = 2, rot = 0, acquiredAt = 1, source = "boss", boss = 1 }
	local THIEF_RECORD =
		{ id = "Moai", mods = {}, place = "storage", rot = 0, source = "raid", from = OWNER, acquiredAt = AT }

	-- Профиль: живые данные, сохранённые данные и «снимок в очереди» (сохранение, начатое раньше, ещё не записано).
	local function newProfile(items)
		local live = { items = items, transfersIn = {}, transfersOut = {} }
		return { live = live, saved = copy(live), queued = nil }
	end
	local function snapshot(p)
		p.queued = copy(p.live) -- сохранение началось
	end
	local function land(p)
		if p.queued then
			p.saved = p.queued -- сохранение записано (может быть несвежим)
			p.queued = nil
		end
	end
	-- Шаги TheftService: 1 журнал; 2 передача в одном кадре; 3 сохранение жертвы с меткой; 4 снять pending, сохранить
	-- вора с меткой, удалить журнал. Подтверждения засчитываются только по содержимому сохранений.
	local function run(crashAfter, victimSnapAt, thiefSnapAt, landOrder, late)
		local victim = newProfile({ [UID] = copy(RECORD) })
		local thief = newProfile({})
		local journal = {}
		for k = 0, crashAfter do
			if k == 1 then
				table.insert(journal, { id = ID, uid = UID, from = OWNER, record = copy(THIEF_RECORD), at = AT })
			elseif k == 2 then
				victim.live.items[UID] = nil
				victim.live.transfersOut[ID] = { uid = UID, at = AT }
				local r = copy(THIEF_RECORD)
				r.pending = ID
				thief.live.items[UID] = r
				thief.live.transfersIn[ID] = { uid = UID, at = AT }
			elseif k == 3 then
				snapshot(victim)
				land(victim)
				if not (victim.saved.transfersOut[ID] ~= nil) then
					break -- подтверждение жертвы не получено: дальше не идём
				end
			elseif k == 4 then
				thief.live.items[UID].pending = nil
				snapshot(thief)
				land(thief)
				local r = thief.saved.items[UID]
				if thief.saved.transfersIn[ID] ~= nil and r and r.pending == nil then
					table.clear(journal)
				end
			end
			-- несвежие автосохранения: снимок в момент victimSnapAt / thiefSnapAt, записывается позже (landOrder)
			if victimSnapAt == k then
				snapshot(victim)
			end
			if thiefSnapAt == k then
				snapshot(thief)
			end
			if landOrder == k then
				land(victim)
				land(thief)
			end
		end
		-- падение: незаписанные снимки пропадают; вор входит со своим сохранением
		local loaded = copy(thief.saved)
		local now = if late then AT + 10 * TransferJournal.SessionGrace else AT + 5
		local victimOut = function(from, id, age)
			assert(from == OWNER)
			if victim.saved.transfersOut[id] ~= nil then
				return true
			end
			-- после падения живой сессии жертвы нет; до SessionGrace считаем, что она могла быть
			if not late and age < TransferJournal.SessionGrace then
				return nil
			end
			return false
		end
		local actions = TransferJournal.Resolve(journal, loaded, now, victimOut)
		local done, confirm = TransferJournal.Apply(actions, loaded, now)
		local victimOwns = victim.saved.items[UID] ~= nil
		local r = loaded.items[UID]
		local thiefOwns = r ~= nil and r.pending == nil
		local waiting = (r ~= nil and r.pending ~= nil)
		for _, action in actions do
			waiting = waiting or action.kind == "wait"
		end
		return victimOwns, thiefOwns, waiting, #done + #confirm
	end
	local scenarios, bad = 0, 0
	for crashAfter = 0, 4 do
		for victimSnapAt = -1, 4 do
			for thiefSnapAt = -1, 4 do
				for landOrder = -1, 4 do
					for _, late in { false, true } do
						scenarios += 1
						local victimOwns, thiefOwns, waiting =
							run(crashAfter, victimSnapAt, thiefSnapAt, landOrder, late)
						local ok
						if late then
							ok = victimOwns ~= thiefOwns and not waiting
						else
							ok = not (victimOwns and thiefOwns) and (victimOwns or thiefOwns or waiting)
						end
						if not ok then
							bad += 1
							if bad <= 5 then
								print(
									("    сбой: падение после %d, снимки жертвы %d, вора %d, запись %d, поздно %s — жертва %s, вор %s, ждёт %s"):format(
										crashAfter,
										victimSnapAt,
										thiefSnapAt,
										landOrder,
										tostring(late),
										tostring(victimOwns),
										tostring(thiefOwns),
										tostring(waiting)
									)
								)
							end
						end
					end
				end
			end
		end
	end
	check(
		bad == 0,
		("%d сценариев падения и несвежих сохранений: ни дублей, ни потерь"):format(
			scenarios
		)
	)

	-- Без падения: подтверждение вора не прошло, запись журнала осталась; предмет потом законно украли у вора (метка
	-- получения сохранена, записи нет) — повторный вход не выдаёт его снова.
	local data = { items = {}, transfersIn = { [ID] = { uid = UID, at = AT } }, transfersOut = {} }
	local actions = TransferJournal.Resolve(
		{ { id = ID, uid = UID, from = OWNER, record = copy(THIEF_RECORD), at = AT } },
		data,
		AT + 99999,
		function()
			return true
		end
	)
	check(
		#actions == 1 and actions[1].kind == "done",
		"предмет ушёл позже законно — повторной выдачи нет"
	)
	TransferJournal.Apply(actions, data, AT + 99999)
	check(data.items[UID] == nil, "запись не появилась заново")

	-- Жертва ещё в живой сессии, которая могла не сохранить удаление: ждём, а не отбираем у вора.
	local pendingData = {
		items = { [UID] = { id = "Moai", pending = ID, from = OWNER, acquiredAt = AT } },
		transfersIn = { [ID] = { uid = UID, at = AT } },
	}
	local wait = TransferJournal.Resolve({}, pendingData, AT + 10, function()
		return nil
	end)
	check(
		#wait == 1 and wait[1].kind == "wait",
		"pending без журнала при неизвестной жертве — ждёт"
	)
	-- Подтверждение по содержимому сохранения, а не по любому OnAfterSave.
	local grant = { kind = "grant", uid = UID, id = ID, journal = true }
	check(
		not TransferJournal.Confirmed(grant, { items = {}, transfersIn = {} }),
		"несвежее сохранение без метки не подтверждает"
	)
	check(
		TransferJournal.Confirmed(grant, { items = { [UID] = { id = "Moai" } }, transfersIn = { [ID] = {} } }),
		"сохранение с меткой и записью подтверждает"
	)
end

print(("Проверок: %d, не прошло: %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end
print("Все проверки краж прошли")

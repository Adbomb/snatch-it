--!strict
-- Учёт краж Судной ночи на сервере (D37, D46): кто что крадёт, резервы и лимиты. Чистый модуль без Instance —
-- проверяется в Lune (scripts/lune/check_theft.luau); живые объекты (подсказки, Part, профили) — в TheftService.
-- Правила: красть можно только в Судную ночь (фаза Open), только чужой выставленный экспонат; удержание HoldSeconds;
-- у вора одна кража за раз и одна успешная за событие (по UserId), у музея — один украденный предмет за событие;
-- резерв атомарный (пока экспонат крадут, его и этот музей другой вор не трогает); провал резерв снимает и лимит
-- не тратит, но вор ждёт retry секунд до новой попытки (D52: повторным удержанием нельзя держать музей занятым всю
-- ночь). Донести можно в Судную ночь и в окно доставки (фаза Delivery). Ни от чего не зависит.

local TheftLedger = {}
TheftLedger.__index = TheftLedger

export type Stage = "Lifting" | "Carrying" | "Delivering"

export type Theft = {
	thief: number,
	owner: number,
	uid: string,
	slot: number,
	event: number,
	stage: Stage,
	startedAt: number,
}

export type BeginArgs = {
	event: number, -- номер Судной ночи (GameTime.DoomEventId)
	phase: string?, -- GameTime.TheftPhase: "Open" | "Delivery" | nil
	thief: number,
	owner: number, -- владелец музея, где стоит экспонат
	uid: string,
	slot: number,
	displayedBy: number?, -- владелец экспоната, если он сейчас выставлен (Displayed), иначе nil
	carrying: boolean, -- у вора что-то в руках
	thiefDone: boolean, -- в профиле вора уже есть успешная кража этого события
	ownerLost: boolean, -- в профиле владельца уже есть потеря этого события
	knocked: boolean?, -- вор оглушён (PvP)
	student: boolean?, -- D55: вор проходит обучение (кражи на ученика не действуют)
	protected: boolean?, -- D55: стартовое существо владельца (навсегда защищено от кражи)
}

export type Ledger = typeof(setmetatable(
	{} :: {
		hold: number,
		tolerance: number,
		byThief: { [number]: Theft },
		byOwner: { [number]: Theft },
		byUid: { [string]: Theft },
		done: { [number]: number }, -- вор → событие его успешной кражи
		lost: { [number]: number }, -- владелец → событие потери
		retry: number, -- пауза после сорванной попытки, секунд
		retryAt: { [number]: number }, -- вор → когда снова можно начать
	},
	TheftLedger
))

function TheftLedger.new(holdSeconds: number, tolerance: number?, retrySeconds: number?): Ledger
	return setmetatable({
		hold = holdSeconds,
		tolerance = tolerance or 0.25,
		byThief = {},
		byOwner = {},
		byUid = {},
		done = {},
		lost = {},
		retry = retrySeconds or 0,
		retryAt = {},
	}, TheftLedger)
end

-- Можно ли начать кражу (now — для паузы после сорванной попытки). Возвращает причину отказа для игрока.
function TheftLedger.CanBegin(self: Ledger, a: BeginArgs, now: number?): (boolean, string?)
	if a.phase ~= "Open" then
		return false, "Красть можно только в Судную ночь"
	end
	local waitUntil = self.retryAt[a.thief]
	if now and waitUntil and now < waitUntil then
		return false,
			("Кража сорвалась — новая попытка через %d с"):format(
				math.ceil(waitUntil - now)
			)
	end
	if a.thief == a.owner then
		return false, "Это ваш экспонат"
	end
	if a.student then
		return false, "Сначала пройдите обучение"
	end
	if a.protected then
		return false, "Стартовое существо защищено от кражи"
	end
	if a.displayedBy ~= a.owner then
		return false, "Этого экспоната нет на постаменте"
	end
	if a.knocked then
		return false, "Вы оглушены"
	end
	if a.carrying or self.byThief[a.thief] then
		return false, "Руки заняты: вор несёт только один предмет"
	end
	if a.thiefDone or self.done[a.thief] == a.event then
		return false, "Вы уже украли предмет этой ночью"
	end
	if a.ownerLost or self.lost[a.owner] == a.event then
		return false, "Этот музей уже потерял предмет этой ночью"
	end
	if self.byUid[a.uid] then
		return false, "Этот экспонат уже крадут"
	end
	if self.byOwner[a.owner] then
		return false, "Из этого музея уже крадут"
	end
	return true, nil
end

-- Начало удержания: резервирует экспонат, музей и вора. Проверки — те же, что CanBegin.
function TheftLedger.Begin(self: Ledger, a: BeginArgs, now: number): (boolean, string?)
	local ok, reason = self:CanBegin(a, now)
	if not ok then
		return false, reason
	end
	local theft: Theft = {
		thief = a.thief,
		owner = a.owner,
		uid = a.uid,
		slot = a.slot,
		event = a.event,
		stage = "Lifting",
		startedAt = now,
	}
	self.byThief[a.thief] = theft
	self.byOwner[a.owner] = theft
	self.byUid[a.uid] = theft
	self.retryAt[a.thief] = nil
	return true, nil
end

-- Удержание закончено: экспонат у вора. Проверяет, что удержание шло не меньше HoldSeconds и фаза ещё Open.
function TheftLedger.Complete(self: Ledger, thief: number, uid: string, now: number, phase: string?): (boolean, string?)
	local theft = self.byThief[thief]
	if not theft or theft.uid ~= uid or theft.stage ~= "Lifting" then
		return false, "Кража не начата"
	end
	if phase ~= "Open" then
		return false, "Судная ночь закончилась"
	end
	if now - theft.startedAt < self.hold - self.tolerance then
		return false, "Слишком быстро"
	end
	theft.stage = "Carrying"
	return true, nil
end

-- Вор у своего сундука: начинается передача владения (журнал §6). Повторный вызов отклоняется.
function TheftLedger.StartDelivery(self: Ledger, thief: number, uid: string, phase: string?): (boolean, string?)
	local theft = self.byThief[thief]
	if not theft or theft.uid ~= uid or theft.stage ~= "Carrying" then
		return false, "Нечего сдавать"
	end
	if phase ~= "Open" and phase ~= "Delivery" then
		return false, "Время доставки вышло"
	end
	theft.stage = "Delivering"
	return true, nil
end

local function release(self: Ledger, theft: Theft)
	if self.byThief[theft.thief] == theft then
		self.byThief[theft.thief] = nil
	end
	if self.byOwner[theft.owner] == theft then
		self.byOwner[theft.owner] = nil
	end
	if self.byUid[theft.uid] == theft then
		self.byUid[theft.uid] = nil
	end
end

-- Успех: предмет перешёл вору. Лимиты события тратятся, резервы снимаются. Повтор — false.
function TheftLedger.Finish(self: Ledger, thief: number, uid: string): (boolean, Theft?)
	local theft = self.byThief[thief]
	if not theft or theft.uid ~= uid or theft.stage ~= "Delivering" then
		return false, nil
	end
	self.done[thief] = theft.event
	self.lost[theft.owner] = theft.event
	release(self, theft)
	return true, theft
end

-- Провал (отпустил E, ушёл, проиграл, время вышло, вышел из игры): резервы снимаются, лимиты не тратятся.
-- Возвращает кражу, чтобы сервис вернул экспонат владельцу. Во время передачи (Delivering) не срабатывает.
-- now — провал по вине вора (отпустил, сорвалась): до now + retry новая попытка не начнётся; nil — не его вина
-- (хозяин музея вышел).
function TheftLedger.Fail(self: Ledger, thief: number, now: number?): Theft?
	local theft = self.byThief[thief]
	if not theft or theft.stage == "Delivering" then
		return nil
	end
	release(self, theft)
	if now then
		self.retryAt[thief] = now + self.retry
	end
	return theft
end

-- Передача владения сорвалась (журнал не записан, владелец ушёл): резерв снимается, лимиты не тратятся.
function TheftLedger.AbortDelivery(self: Ledger, thief: number): Theft?
	local theft = self.byThief[thief]
	if not theft or theft.stage ~= "Delivering" then
		return nil
	end
	release(self, theft)
	return theft
end

function TheftLedger.ByThief(self: Ledger, thief: number): Theft?
	return self.byThief[thief]
end

function TheftLedger.ByUid(self: Ledger, uid: string): Theft?
	return self.byUid[uid]
end

function TheftLedger.ByOwner(self: Ledger, owner: number): Theft?
	return self.byOwner[owner]
end

-- Все идущие кражи (копия списка).
function TheftLedger.All(self: Ledger): { Theft }
	local out = {}
	for _, theft in self.byThief do
		table.insert(out, theft)
	end
	return out
end

return TheftLedger

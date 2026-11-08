--!strict
-- Обязательное обучение новичка (D55): шаги, продолжение после входа, миграция старых профилей (v3 → v4), защита
-- стартового существа от кражи. Чистые функции без Instance: их вызывают DataService (миграция при загрузке),
-- TutorialService (шаги), TheftService / Util/TheftLedger (защита), ShopService и DefenseService (во время обучения —
-- отказ), клиент (подсказки); проверяет scripts/lune/check_tutorial.luau.
-- Запись профиля tutorial = { step, itemId?, uid?, placed?, migrated? }:
--   step — текущий шаг (Steps); itemId — учебное существо (случайное Common босса 1, выбирается сервером один раз);
--   uid — его uid (выдаётся один раз вместе с itemId и больше не меняется: к нему навсегда привязана защита от кражи);
--   placed — существо поставлено (предмет записан в items той же записью профиля); migrated — старый профиль, обучение
--   засчитано без стартового существа и защиты.
-- Ни от чего не зависит.

local TutorialRules = {}

-- Шаги по порядку. Intro — приветствие и путь к уровню 1; Catch — учебная поимка (бесплатные броски, первое
-- попадание — захват); Battle — учебный бой с личным псом (всегда победа); Carry — существо в руках: донести и
-- поставить на постамент; Income — ждём первое начисление дохода за него; Done — обучение пройдено.
TutorialRules.Steps = { "Intro", "Catch", "Battle", "Carry", "Income", "Done" }

local index: { [string]: number } = {}
for i, step in TutorialRules.Steps do
	index[step] = i
end

export type State = {
	step: string,
	itemId: string?,
	uid: string?,
	placed: boolean?,
	migrated: boolean?,
}

function TutorialRules.Default(): State
	return { step = "Intro" }
end

function TutorialRules.IsStep(step: any): boolean
	return type(step) == "string" and index[step] ~= nil
end

-- Номер шага (1…6), неизвестный — 1.
function TutorialRules.Index(step: string): number
	return index[step] or 1
end

-- Запись обучения в порядке. Испорченный шаг — с начала, но учебные существо и uid сохраняются (выданное один раз
-- не выдаётся заново и защита не теряется); поля неверного типа убираются. Меняет data.tutorial.
function TutorialRules.Normalize(data: any): State
	local t = data.tutorial
	if type(t) ~= "table" then
		t = TutorialRules.Default()
		data.tutorial = t
	end
	if t.itemId ~= nil and type(t.itemId) ~= "string" then
		t.itemId = nil
	end
	if t.uid ~= nil and type(t.uid) ~= "string" then
		t.uid = nil
	end
	if not TutorialRules.IsStep(t.step) then
		t.step = if t.placed == true then "Income" elseif t.itemId and t.uid then "Catch" else "Intro"
	end
	local items = if type(data.items) == "table" then data.items else {}
	local present = type(t.uid) == "string" and items[t.uid] ~= nil
	-- существо поставлено — значит есть и запись предмета: без неё шаг Income откатывается к Carry (донести заново
	-- тем же uid); после Done ничего не трогаем (предмет мог законно уйти — украден, перемещён)
	if t.step == "Income" and not present then
		t.step = if t.itemId and t.uid then "Carry" else "Intro"
		t.placed = nil
	elseif (t.step == "Catch" or t.step == "Battle" or t.step == "Carry") and present then
		-- запись предмета уже есть (выставлен, шаг не успел сохраниться): второй раз в руки его не выдавать
		t.step = "Income"
		t.placed = true
	end
	return t
end

-- Изменение записи обучения (DataService.SetTutorial): step — только на разрешённый следующий шаг; itemId и uid —
-- один раз (защита навсегда у одного uid, D55); placed = true — только когда запись предмета uid есть. Меняет t;
-- false — отказ (ничего не меняется).
function TutorialRules.Apply(t: State, items: any, fields: { [string]: any }): boolean
	local step = fields.step
	if step ~= nil and step ~= t.step and not TutorialRules.CanAdvance(t.step, step) then
		return false
	end
	for _, key in { "itemId", "uid" } do
		local value = fields[key]
		if value ~= nil and (type(value) ~= "string" or ((t :: any)[key] ~= nil and (t :: any)[key] ~= value)) then
			return false
		end
	end
	if fields.placed ~= nil then
		local uid = fields.uid or t.uid
		if fields.placed ~= true or type(uid) ~= "string" or type(items) ~= "table" or items[uid] == nil then
			return false
		end
	end
	if step ~= nil then
		t.step = step
	end
	if fields.itemId ~= nil then
		t.itemId = fields.itemId
	end
	if fields.uid ~= nil then
		t.uid = fields.uid
	end
	if fields.placed ~= nil then
		t.placed = true
	end
	return true
end

-- Миграция schema 3 → 4 (один раз; после разбора журнала передач и проверки записей): есть хотя бы один свой предмет
-- (на постаменте или в инвентаре; «передаётся» — pending — не считается) — обучение засчитано, без стартового
-- существа и защиты; иначе — обучение один раз. Повторный вызов (schema уже 4) ничего не меняет. true — мигрировал.
function TutorialRules.Migrate(data: any, schema: number): boolean
	if data.schema ~= schema - 1 then
		return false
	end
	if type(data.lovibums) ~= "table" then
		data.lovibums = {}
	end
	-- Профиль уже был v4, а старый сервер (без D55) сохранил его со схемой 3: начатое или пройденное обучение не
	-- трогать (иначе стартовое существо выдалось бы снова, а защита uid пропала бы).
	local t = data.tutorial
	if type(t) == "table" and (t.step ~= "Intro" or t.itemId ~= nil or t.uid ~= nil or t.placed or t.migrated) then
		data.schema = schema
		return true
	end
	local own = false
	if type(data.items) == "table" then
		for _, record in data.items do
			if type(record) == "table" and record.pending == nil then
				own = true
				break
			end
		end
	end
	data.tutorial = if own then { step = "Done", migrated = true } else TutorialRules.Default()
	data.schema = schema
	return true
end

-- Обучение идёт (не пройдено).
function TutorialRules.IsActive(data: any): boolean
	local t = type(data) == "table" and data.tutorial
	return not (type(t) == "table" and t.step == "Done")
end

-- С какого шага продолжить после входа: поимка и бой начинаются заново (ничего ещё не выдано — повтор ничего не
-- копит), существо в руках — снова в руках (тот же uid), поставленное — ждём доход.
function TutorialRules.ResumeStep(step: string): string
	if step == "Battle" then
		return "Catch"
	end
	return if TutorialRules.IsStep(step) then step else "Intro"
end

-- Переход from → to разрешён (только вперёд на один шаг; Battle → Catch — учебный бой прерван).
function TutorialRules.CanAdvance(from: string, to: string): boolean
	if from == "Battle" and to == "Catch" then
		return true
	end
	return TutorialRules.IsStep(from) and TutorialRules.IsStep(to) and index[to] == index[from] + 1
end

-- Стартовое существо: навсегда защищено от кражи (D55). Защита — только у uid из записи обучения, поставленного
-- в обучении (не у мигрировавших профилей); перенести её на другой предмет нельзя.
function TutorialRules.IsProtected(data: any, uid: string): boolean
	local t = type(data) == "table" and data.tutorial
	return type(t) == "table" and t.migrated ~= true and t.placed == true and type(t.uid) == "string" and t.uid == uid
end

-- Во время обучения «Магазин» и «Защита» недоступны (кнопок нет, сервер отказывает).
function TutorialRules.ShopAllowed(data: any): boolean
	return not TutorialRules.IsActive(data)
end

return TutorialRules

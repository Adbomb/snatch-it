--!nocheck
-- Проверка обучения новичка без Roblox Studio (D55, Shared/TutorialRules): миграция старых профилей v3 → v4 (экспонаты
-- на постаменте, только в инвентаре, только «передаётся», пусто с монетами и силой, пусто, уже v4 — и повтор),
-- продолжение с каждого шага, переходы только вперёд, запись в порядке, защита стартового uid (только поставленный в
-- обучении, не у мигрировавших, не переносится), «Магазин» и «Защита» во время обучения закрыты; цепочка загрузки
-- DataService (Inventory.Normalize не откатывает схему 4). Запуск: lune run scripts/lune/check_tutorial.luau.

local process = require("@lune/process")

local Env = require("./env")

local Inventory = Env.Require("ReplicatedStorage.Shared.Inventory")
local Items = Env.Require("ReplicatedStorage.Shared.Config.Items")
local ProfileTemplate = Env.Require("ReplicatedStorage.Shared.Config.ProfileTemplate")
local TutorialRules = Env.Require("ReplicatedStorage.Shared.TutorialRules")
local CatchRules = Env.Require("ReplicatedStorage.Shared.CatchRules")

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

local SCHEMA = ProfileTemplate.schema
check(SCHEMA == 4, "схема профиля 4")
check(
	ProfileTemplate.tutorial.step == "Intro" and type(ProfileTemplate.lovibums) == "table",
	"шаблон: обучение и Ловибумы"
)

-- Загрузка как в DataService: Reconcile (недостающие поля шаблона) → Normalize (v2 → v3) → Migrate (v3 → v4) →
-- проверка Ловибумов и записи обучения.
local function deepCopy(t)
	local out = {}
	for k, v in t do
		out[k] = if type(v) == "table" then deepCopy(v) else v
	end
	return out
end
local function reconcile(data)
	for k, v in ProfileTemplate do
		if data[k] == nil then
			data[k] = if type(v) == "table" then deepCopy(v) else v
		end
	end
end
local function load(data)
	reconcile(data)
	Inventory.Normalize(data, 6, Items, 45)
	local migrated = TutorialRules.Migrate(data, SCHEMA)
	data.lovibums = CatchRules.Normalize(data.lovibums)
	TutorialRules.Normalize(data)
	return migrated
end

local function v3(items, extra)
	local data =
		{ schema = 3, coins = 0, museumLevel = 1, strength = 0, dumbbellLevel = 1, items = items or {}, stats = {} }
	for k, v in extra or {} do
		data[k] = v
	end
	return data
end

print("· миграция v3 → v4")
local onSlot = v3({ a = { id = "Moai", place = "slot", slot = 1, rot = 0 } })
check(load(onSlot) and onSlot.schema == 4, "экспонат на постаменте: мигрировал")
check(onSlot.tutorial.step == "Done" and onSlot.tutorial.migrated == true, "  обучение засчитано")
check(
	onSlot.tutorial.uid == nil and not TutorialRules.IsProtected(onSlot, "a"),
	"  без стартового существа и защиты"
)
local inStorage = v3({ b = { id = "Moai", place = "storage" } })
load(inStorage)
check(inStorage.tutorial.step == "Done", "только в инвентаре — засчитано")
local pendingOnly = v3({ c = { id = "Moai", place = "storage", pending = "t1", from = 5 } })
load(pendingOnly)
check(
	pendingOnly.tutorial.step == "Intro",
	"только «передаётся» — обучение один раз"
)
local rich = v3({}, { coins = 1e9, strength = 5e6 })
load(rich)
check(
	rich.tutorial.step == "Intro" and rich.coins == 1e9,
	"пусто с монетами и силой — обучение, монеты целы"
)
local empty = v3({})
load(empty)
check(empty.tutorial.step == "Intro" and empty.schema == 4, "пусто — обучение")
local v2 = { schema = 2, coins = 5, items = { d = { id = "Moai", place = "slot", slot = 1 } }, stats = {} }
load(v2)
check(v2.schema == 4 and v2.tutorial.step == "Done", "v2 → v3 → v4 за одну загрузку")

print("· повторная загрузка ничего не меняет")
local before = deepCopy(onSlot)
check(not load(onSlot), "миграция второй раз не идёт")
check(
	onSlot.tutorial.step == before.tutorial.step and onSlot.tutorial.migrated == true and onSlot.schema == 4,
	"  запись та же"
)
local done = v3({})
load(done)
done.tutorial = { step = "Done", itemId = "Moai", uid = "start", placed = true }
done.items.start = { id = "Moai", place = "slot", slot = 1 }
load(done)
check(
	done.schema == 4 and done.tutorial.step == "Done" and TutorialRules.IsProtected(done, "start"),
	"уже v4: награда одна, защита на месте"
)
local fresh = deepCopy(ProfileTemplate)
check(
	not load(fresh) and fresh.tutorial.step == "Intro",
	"новый профиль: сразу v4, обучение с начала"
)
check(
	Inventory.Normalize(fresh, 6, Items, 45) and fresh.schema == 4,
	"Inventory.Normalize не откатывает схему 4"
)

print("· продолжение после входа")
for _, step in TutorialRules.Steps do
	local resume = TutorialRules.ResumeStep(step)
	check(TutorialRules.IsStep(resume), step .. " → " .. resume)
end
check(
	TutorialRules.ResumeStep("Battle") == "Catch",
	"бой прерван выходом — снова поимка (ничего не выдано)"
)
check(TutorialRules.ResumeStep("Carry") == "Carry", "в руках — снова в руках")
check(TutorialRules.ResumeStep("Income") == "Income", "поставлено — ждём доход")
check(TutorialRules.ResumeStep("???") == "Intro", "мусор — с начала")

print("· переходы")
check(
	TutorialRules.CanAdvance("Intro", "Catch") and TutorialRules.CanAdvance("Catch", "Battle"),
	"вперёд по одному"
)
check(TutorialRules.CanAdvance("Battle", "Catch"), "бой прерван — к поимке")
check(
	not TutorialRules.CanAdvance("Intro", "Carry") and not TutorialRules.CanAdvance("Carry", "Done"),
	"через шаг нельзя"
)
check(not TutorialRules.CanAdvance("Done", "Intro"), "назад после Done нельзя")

print("· запись обучения в порядке")
local broken = { tutorial = { step = "Nope", itemId = 5, uid = {} }, items = {} }
TutorialRules.Normalize(broken)
check(broken.tutorial.step == "Intro" and broken.tutorial.itemId == nil, "испорченная — с начала")
local lost = { tutorial = { step = "Income", itemId = "Moai", uid = "u1", placed = true }, items = {} }
TutorialRules.Normalize(lost)
check(
	lost.tutorial.step == "Carry" and lost.tutorial.uid == "u1",
	"Income без предмета — снова Carry тем же uid"
)
local ok =
	{ tutorial = { step = "Income", itemId = "Moai", uid = "u1", placed = true }, items = { u1 = { id = "Moai" } } }
TutorialRules.Normalize(ok)
check(ok.tutorial.step == "Income", "Income с предметом — как было")

print("· защита стартового существа")
local data = { tutorial = { step = "Done", itemId = "Moai", uid = "start", placed = true }, items = {} }
check(TutorialRules.IsProtected(data, "start"), "стартовый uid защищён")
check(
	not TutorialRules.IsProtected(data, "other"),
	"другой предмет — нет (даже последний в музее)"
)
data.tutorial.placed = nil
check(
	not TutorialRules.IsProtected(data, "start"),
	"не поставлен в обучении — нет защиты"
)
check(
	not TutorialRules.IsProtected({ tutorial = { step = "Done", uid = "x", placed = true, migrated = true } }, "x"),
	"мигрировавший — нет защиты"
)
check(
	not TutorialRules.IsProtected(nil, "x") and not TutorialRules.IsProtected({}, "x"),
	"без записи — нет"
)

print("· «Магазин» и «Защита»")
check(
	not TutorialRules.ShopAllowed({ tutorial = { step = "Catch" } }),
	"во время обучения закрыты"
)
check(TutorialRules.ShopAllowed({ tutorial = { step = "Done" } }), "после — открыты")
check(
	TutorialRules.IsActive({}) and TutorialRules.IsActive(nil),
	"без записи — обучение идёт (сервер подставит)"
)

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
process.exit(if failed == 0 then 0 else 1)

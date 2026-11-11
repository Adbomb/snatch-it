-- Шаблон профиля игрока строго по DESIGN.md §2 (schema = 2: + сила и уровень гантели, D30; schema = 3: единый
-- инвентарь D46 — проверка записей items, Shared/Inventory; schema = 4: Ловибумы и обучение D55 — Shared/CatchRules,
-- Shared/TutorialRules; schema = 5: запас защиты по уровням музея D56 — Shared/DefenseRules.Normalize).
-- Используется DataService: новые профили и Reconcile. Ни от чего не зависит.

return {
	schema = 5,
	coins = 0,
	museumLevel = 1,
	strength = 0,
	dumbbellLevel = 1,
	items = {},
	stats = { delivered = 0 },
	-- Защита (D37, D46, D56): купленные и не установленные устройства (вид → { L<уровень музея при покупке> →
	-- количество }: устройство ставится только на музей своего уровня), устройства взлома (L<уровень музея-цели> →
	-- количество) и установленные (вид → { cycle — круг их Судной ночи, level — уровень покупки }: списаны, вернутся
	-- в запас своего уровня, если ночь не наступила).
	defense = { owned = {}, hacks = {}, installed = {} },
	-- Метки передач украденного (DESIGN §6, Util/TransferJournal): id → { uid, at }. Ушло по краже / получено кражей.
	transfersOut = {},
	transfersIn = {},
	-- Ловибумы (D55): L<уровень босса> → { Boom, Turbo, Mega → количество } (Shared/CatchRules).
	lovibums = {},
	-- Обучение новичка (D55, Shared/TutorialRules): шаг, учебное существо и его uid (защита от кражи).
	tutorial = { step = "Intro" },
}

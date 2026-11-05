-- Шаблон профиля игрока строго по DESIGN.md §2 (schema = 2: + сила и уровень гантели, D30; schema = 3: единый
-- инвентарь D46 — проверка записей items, Shared/Inventory).
-- Используется DataService: новые профили и Reconcile. Ни от чего не зависит.

return {
	schema = 3,
	coins = 0,
	museumLevel = 1,
	strength = 0,
	dumbbellLevel = 1,
	items = {},
	stats = { delivered = 0 },
	-- Защита (D37, D46): купленные и не установленные устройства (вид → количество), устройства взлома (L<уровень> →
	-- количество) и установленные (вид → номер круга их Судной ночи: списаны, вернутся, если ночь не наступила).
	defense = { owned = {}, hacks = {}, installed = {} },
	-- Метки передач украденного (DESIGN §6, Util/TransferJournal): id → { uid, at }. Ушло по краже / получено кражей.
	transfersOut = {},
	transfersIn = {},
}

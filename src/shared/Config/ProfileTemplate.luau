-- Шаблон профиля игрока строго по DESIGN.md §2 (schema = 2: + сила и уровень гантели, D30).
-- Используется DataService: новые профили и Reconcile. Ни от чего не зависит.

return {
	schema = 2,
	coins = 0,
	museumLevel = 1,
	strength = 0,
	dumbbellLevel = 1,
	items = {},
	stats = { delivered = 0 },
}

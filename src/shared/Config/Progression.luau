-- Числа долгой прогрессии (D29): боссы, круги качалки, перерождение, музей, доход, редкость, модификаторы,
-- каталог, скорость. Только данные — игра берёт их через GameConfig.Progression, а симулятор
-- scripts/sim/progression.py читает этот же файл. Поэтому формат простой: числа, строки и вложенные таблицы.
-- Ни от чего не зависит.

return {
	-- Сила боссов зон 1..10 (D22: автобой, победа при силе ≥ силы босса).
	Bosses = { 0, 450, 20000, 220000, 4700000, 39000000, 110000000, 1700000000, 4200000000, 17000000000 },

	-- Круги качалки (D25): сила в секунду, нужная сила и перерождения для открытия.
	Circles = {
		{ rate = 1, strength = 0, rebirths = 0 },
		{ rate = 5, strength = 60, rebirths = 0 },
		{ rate = 25, strength = 1500, rebirths = 0 },
		{ rate = 100, strength = 25000, rebirths = 0 },
		{ rate = 500, strength = 0, rebirths = 3 },
		{ rate = 2500, strength = 0, rebirths = 6 },
		{ rate = 10000, strength = 0, rebirths = 9 },
		{ rate = 50000, strength = 0, rebirths = 12 },
	},

	-- Перерождение: порог силы растёт ×strengthGrowth, цена в монетах ×coinGrowth за каждое перерождение.
	-- Награда навсегда за каждое: +strengthBonus к набору силы, +incomeBonus к доходу.
	Rebirth = {
		strength = 30000,
		strengthGrowth = 3,
		coins = 2000,
		coinGrowth = 2.2,
		strengthBonus = 0.5,
		incomeBonus = 0.1,
	},

	-- Музей (D26): витрин на уровнях 1..10 и цена перехода на следующий уровень (9 цен).
	Museum = {
		Slots = { 2, 4, 6, 8, 10, 12, 14, 16, 18, 20 },
		Prices = { 900, 62000, 280000, 880000, 6500000, 37000000, 120000000, 510000000, 1700000000 },
	},

	-- Доход экспоната в секунду, пока владелец в игре.
	Income = { Common = 1, Uncommon = 5, Rare = 25, Legendary = 150, Secret = 1000 },

	-- Шансы редкости (веса) в зоне 1 и в зоне 10, между ними — линейно. Secret — с зоны SecretFromZone.
	RarityFirst = { Common = 90, Uncommon = 9.5, Rare = 0.5, Legendary = 0, Secret = 0 },
	RarityLast = { Common = 40, Uncommon = 35, Rare = 20, Legendary = 4.9, Secret = 0.1 },
	SecretFromZone = 8,

	-- Модификаторы при появлении предмета: шанс и множитель дохода.
	Modifiers = {
		Golden = { chance = 0.02, income = 2 },
		Giant = { chance = 0.01, income = 3 },
		Rainbow = { chance = 0.005, income = 5 },
	},

	-- Каталог: набор = все предметы одной редкости в одном виде (5 редкостей × 4 вида = 20 наборов).
	-- Собранный набор навсегда добавляет к доходу Rarity[редкость] × Variant[вид].
	Catalog = {
		Rarity = { Common = 0.05, Uncommon = 0.1, Rare = 0.2, Legendary = 0.4, Secret = 1 },
		Variant = { Normal = 1, Golden = 2, Giant = 3, Rainbow = 5 },
	},

	-- Скорость (D24): 14 при нулевой силе → 20 на потолке, логарифмически.
	Speed = { min = 14, max = 20, cap = 1000000000000 },

	-- Предметов в каждой редкости (D23).
	ItemCounts = { Common = 10, Uncommon = 8, Rare = 6, Legendary = 4, Secret = 2 },
}

-- Редкость этажа (D74): лестница Деревянный … Космический — шансы прокрутки, множители дохода и сдвиг шансов вверх от
-- редкости съеденного существа (решения владельца 2026-11-26/27). Названия — только ярлыки, не стиль этажа.
-- Правила — Shared/FloorRules, проверка — scripts/lune/check_floor_rules.luau. Ни от чего не зависит.

local FloorRarity = {}

-- Порядок ступеней: от частой к редкой. Запись предмета хранит ключ (пусто — Wood).
FloorRarity.Order = { "Wood", "Stone", "Marble", "Gold", "Mythic", "Cosmic" }
FloorRarity.Default = "Wood"

FloorRarity.Names = {
	Wood = "Деревянный",
	Stone = "Каменный",
	Marble = "Мраморный",
	Gold = "Золотой",
	Mythic = "Мифический",
	Cosmic = "Космический",
}

-- Шанс ступени, % (без сдвига; в сумме 100), и множитель дохода этажа.
FloorRarity.Chance = { Wood = 60, Stone = 25, Marble = 10, Gold = 4, Mythic = 0.9, Cosmic = 0.1 }
FloorRarity.Mult = { Wood = 1, Stone = 2, Marble = 4, Gold = 8, Mythic = 20, Cosmic = 60 }

-- Сдвиг от редкости существа: вес ступени k (0 — Wood) умножается на Shift ^ k, затем веса нормируются.
FloorRarity.Shift = { Common = 1, Rare = 1.15, Epic = 1.3, Legendary = 1.5, Secret = 1.8 }

-- Удержание существа в Ловибуме по силе (отношение силы игрока к силе босса): не меньше 1 — обычный шанс; меньше 1 —
-- шанс × отношение, но не ниже Min; от BonusAt и выше — шанс × (1 + Bonus), между 1 и BonusAt — плавно.
FloorRarity.Hold = { Min = 0.05, BonusAt = 2, Bonus = 0.25 }

return FloorRarity

-- Редкости: порядок от низшей к высшей и названия для интерфейса.
-- Цвета редкостей — в UITokens (UI_KIT.md). Читается сервером и клиентом. Ни от чего не зависит.

local Rarities = {}

Rarities.Order = { "Common", "Rare", "Epic", "Legendary", "Secret" } -- D37

Rarities.Names = {
	Common = "Обычный",
	Rare = "Редкий",
	Epic = "Эпический",
	Legendary = "Легендарный",
	Secret = "Секретный",
}

-- Позиция редкости в Order (1 — Common). Неизвестная редкость считается Common.
function Rarities.Rank(rarity: string): number
	return table.find(Rarities.Order, rarity) or 1
end

return Rarities

-- Редкость этажа (D74): лестница Деревянный … Алмазный — шансы прокрутки, множители дохода и сдвиг шансов вверх от
-- редкости съеденного существа (решения владельца 2026-11-26/27). Названия — только ярлыки, не стиль этажа.
-- Правила — Shared/FloorRules, проверка — scripts/lune/check_floor_rules.luau. Ни от чего не зависит.

local FloorRarity = {}

-- Порядок ступеней: от частой к редкой. Запись предмета хранит ключ (пусто — Wood).
FloorRarity.Order = { "Wood", "Stone", "Marble", "Gold", "Mythic", "Diamond" }
FloorRarity.Default = "Wood"

FloorRarity.Names = {
	Wood = "Деревянный",
	Stone = "Каменный",
	Marble = "Мраморный",
	Gold = "Золотой",
	Mythic = "Мифический",
	Diamond = "Алмазный",
}

-- Шанс ступени, % (без сдвига; в сумме 100), и множитель дохода этажа.
FloorRarity.Chance = { Wood = 60, Stone = 25, Marble = 10, Gold = 4, Mythic = 0.9, Diamond = 0.1 }
FloorRarity.Mult = { Wood = 1, Stone = 2, Marble = 4, Gold = 8, Mythic = 20, Diamond = 60 }

-- Сдвиг от редкости существа: вес ступени k (0 — Wood) умножается на Shift ^ k, затем веса нормируются.
FloorRarity.Shift = { Common = 1, Rare = 1.15, Epic = 1.3, Legendary = 1.5, Secret = 1.8 }

-- Удержание существа в Ловибуме по силе (отношение силы игрока к силе босса): не меньше 1 — обычный шанс; меньше 1 —
-- шанс × отношение, но не ниже Min; от BonusAt и выше — шанс × (1 + Bonus), между 1 и BonusAt — плавно.
FloorRarity.Hold = { Min = 0.05, BonusAt = 2, Bonus = 0.25 }

-- Сигнал редкости издалека (владелец 2026-11-27): вблизи этаж — продолжение монстра, издалека — редкость, которую
-- видят все. Дальняя версия этажа (от FarDistance стадов) красится в цвет редкости, а не монстра.
--   frame, cap — колонны и их оголовки; slab — плита; window — подсветка окна (nil — цвет комнаты);
--   foil — каркас из Foil (золото); glow — светящийся пояс и рёбра (Neon — только Золотой и выше, только как сигнал);
--   pulse — второй цвет и период пульсации свечения, секунд; spread — выросты каркаса за след башни, стадов на
--   сторону (соседние башни — через 75); beam — высота луча над башней, если этаж лучший в ней, стадов;
--   sparks — искры: частиц в секунду (одна система на этаж); badge — счётчик на значке башни; announce — кому объявление о выпадении.
FloorRarity.FarDistance = 120
FloorRarity.Signal = {
	Wood = { frame = "7A5E44", cap = "5E4631", slab = "33291F" },
	Stone = { frame = "767B84", cap = "595D66", slab = "2E3138" },
	Marble = { frame = "F3F0EA", cap = "D9D4CA", slab = "B9B4AA", window = "FFFDF4" },
	Gold = {
		frame = "F0BC3C",
		cap = "C4922A",
		slab = "6E4E12",
		foil = true,
		glow = "FFC23A",
		window = "FFE9A8",
		badge = true,
	},
	Mythic = {
		frame = "5A2FC2",
		cap = "3C1C8C",
		slab = "2A1466",
		glow = "C79BFF",
		pulse = { color = "7A3DF0", period = 3.2 },
		window = "E9D6FF",
		spread = 4,
		beam = 120,
		sparks = 3,
		badge = true,
		announce = "Server",
	},
	Diamond = {
		frame = "EAF8FF",
		cap = "BFE9FF",
		slab = "7FC4EC",
		foil = true,
		glow = "CFF4FF",
		pulse = { color = "FFFFFF", period = 2.0 },
		window = "F4FDFF",
		spread = 8,
		beam = 250,
		sparks = 6,
		badge = true,
		announce = "Global",
	},
}

-- Луч над башней (цвет лучшего этажа): ширина у основания и наверху, стадов; яркость и прозрачность у основания.
-- FarFrom — с какого расстояния по земле луч рисуется табличкой (BillboardGui): на низкой графике дальше ~600 стадов
-- движок не рисует ни детали, ни Beam; FarWidth — её ширина, стадов.
FloorRarity.Beam = {
	Width = 12,
	TopWidth = 5,
	Brightness = 3,
	Transparency = 0.1,
	FarFrom = 420,
	FarWidth = 14,
}
-- Светящийся пояс у подножия башни (цвет лучшего этажа, Золотой и выше): вынос за след, высота и толщина полосы,
-- подъём над землёй, стадов.
FloorRarity.Halo = { Out = 2.2, Height = 1.2, Depth = 1.0, Lift = 0.3 }
-- Искры этажа: время жизни частицы, с; размер, стадов; скорость и ускорение вверх; яркость.
FloorRarity.Sparks = { Lifetime = 2.6, Size = 1.6, Speed = 2, Rise = 1.5, Brightness = 3 }

-- Объявление «<имя> выбил <редкость> этаж!»: Мифический — всем на сервере, Алмазный — на все серверы
-- (MessagingService, тема Topic); не чаще одного сообщения в PublishGap секунд с сервера, чужие — не чаще ShowGap.
FloorRarity.Announce = { Topic = "FloorJackpot", PublishGap = 20, ShowGap = 4 }

-- Момент получения (редкий этаж встал на место): вспышка и столб света, секунд, и высота столба, стадов.
FloorRarity.Arrival =
	{ Gold = { time = 5, height = 90 }, Mythic = { time = 7, height = 160 }, Diamond = { time = 10, height = 300 } }
-- Вспышка момента получения: шар от From до To стадов за Time секунд. Звук — встроенный в Roblox (без загрузок).
FloorRarity.ArrivalFlash = { From = 8, To = 80, Time = 0.8 }
FloorRarity.ArrivalSound = { Id = "rbxasset://sounds/electronicpingshort.wav", Volume = 1, Distance = 400 }

return FloorRarity

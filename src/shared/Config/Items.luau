-- Каталог произведений искусства (D37, D40, D42): у каждого из 10 боссов своя коллекция. Босс 1 «Музей чудес» (D40)
-- — 20 предметов, босс 2 «Музей безумных находок» (D42) — 30 (docs/CATALOG.md): модели из Blender (Config/ItemModels,
-- пока меш не загружен — заготовка цвета и размера модели) и свой доход в секунду (income, предварительный баланс, без
-- множителей редкости). Коллекции боссов 3–10 — черновик (вид — заготовка, дохода нет), до их очереди. legacy —
-- прежние предметы (народные промыслы босса 1 D38, антиквариат-черновик босса 2): у босса не появляются, но описание
-- остаётся, чтобы старые сохранения загружались. id не повторяются и не переиспользуются для другого произведения.
-- Шансы редкостей у боссов — Progression.BossLoot.
-- Читается сервером и клиентом. Ни от чего не зависит.

export type ItemDef = {
	id: string,
	displayName: string,
	rarity: string, -- Common | Rare | Epic | Legendary | Secret (см. Config/Rarities)
	boss: number, -- босс (уровень 1–10), в чьей коллекции предмет
	kind: string, -- Painting | Sculpture | Vase | Mask | Artifact | Jewel | Instrument | Textile
	source: string?, -- автор и время для реальных произведений
	weight: string, -- Light | Medium | Heavy
	shape: string, -- Enum.PartType заготовки: Block | Ball | Cylinder | Wedge (у Ball размер берётся по X)
	color: Color3,
	size: Vector3,
	material: Enum.Material?, -- по умолчанию Plastic; Neon — для свечения
	income: number, -- доход в секунду на витрине музея (D37, D40); 0 — не приносит
	legacy: boolean?, -- прежний предмет: только для старых сохранений, у босса не появляется
}

local Items: { [string]: ItemDef } = {}

local function art(
	id: string,
	boss: number,
	rarity: string,
	displayName: string,
	kind: string,
	weight: string,
	shape: string,
	color: string,
	size: Vector3,
	source: string?
)
	assert(Items[id] == nil, "Повтор предмета " .. id)
	Items[id] = {
		id = id,
		displayName = displayName,
		rarity = rarity,
		boss = boss,
		kind = kind,
		source = source,
		weight = weight,
		shape = shape,
		color = Color3.fromHex(color),
		size = size,
		income = 0,
	}
end

-- Предмет коллекции с моделью из Blender и своим доходом в секунду (D40 — босс 1, D42 — босс 2). Форма, цвет и
-- размер — запасной вид, пока меш не загружен; размер равен размеру модели.
local function collectible(
	boss: number,
	id: string,
	rarity: string,
	displayName: string,
	kind: string,
	weight: string,
	income: number,
	color: string,
	size: Vector3,
	source: string
)
	art(id, boss, rarity, displayName, kind, weight, "Block", color, size, source)
	Items[id].income = income
end

local function wonder(...)
	collectible(1, ...)
end

local function find(...)
	collectible(2, ...)
end

local V = Vector3.new

-- 1. Свалка — «Сторожевой пёс»: «Музей чудес» (D40). Доход — предварительный баланс, не утверждён.
-- Common
wonder("Moai", "Common", "Голова моаи", "Sculpture", "Medium", 16, "8A8278", V(2, 3.05, 1.59),
	"остров Пасхи, 1250–1500")
wonder("EgyptianCat", "Common", "Египетская кошка", "Sculpture", "Light", 10, "2C2D36", V(1.24, 2.45, 1.55),
	"Египет, ок. 600 до н. э.")
wonder("AnubisStatue", "Common", "Статуя Анубиса", "Sculpture", "Medium", 13, "26272F", V(1.24, 2.628, 1.92),
	"Египет, гробница Тутанхамона")
wonder("TerracottaWarrior", "Common", "Терракотовый воин", "Sculpture", "Medium", 12, "C2845A", V(1.2, 2.8, 1.15),
	"Китай, ок. 210 до н. э.")
wonder("MiniStonehenge", "Common", "Мини-Стоунхендж", "Artifact", "Heavy", 15, "A7A196", V(3.1, 1.68, 3.1),
	"Британия, ок. 3000–2000 до н. э.")
wonder("TriceratopsSkull", "Common", "Череп трицератопса", "Artifact", "Medium", 18, "E9DDBF", V(2.611, 2.669, 3.309),
	"окаменелость, меловой период")
wonder("EgyptianSarcophagus", "Common", "Египетский саркофаг", "Artifact", "Medium", 14, "EFBF3A",
	V(1.24, 2.62, 1.09), "Египет, Новое царство")
wonder("GladiatorHelmet", "Common", "Шлем гладиатора", "Artifact", "Light", 11, "D19A3E", V(1.84, 2.66, 1.84),
	"Рим, I век")
-- Rare
wonder("Sunflowers", "Rare", "Подсолнухи", "Painting", "Medium", 35, "E8B530", V(3.2, 4.56, 1.285),
	"Винсент ван Гог, 1888")
wonder("GreatWave", "Rare", "Большая волна в Канагаве", "Painting", "Medium", 38, "B8322A", V(4.04, 3.98, 1.285),
	"Кацусика Хокусай, ок. 1831")
wonder("PearlEarring", "Rare", "Девушка с жемчужной серёжкой", "Painting", "Medium", 40, "6B4228",
	V(3.1, 4.64, 1.285), "Ян Вермеер, ок. 1665")
wonder("TheScream", "Rare", "Крик", "Painting", "Medium", 42, "E0782C", V(3.1, 4.64, 1.285), "Эдвард Мунк, 1893")
wonder("GreatSphinx", "Rare", "Большой Сфинкс", "Sculpture", "Heavy", 45, "D9B26E", V(1.9, 1.7, 3.16),
	"Гиза, ок. 2500 до н. э.")
wonder("NefertitiBust", "Rare", "Бюст Нефертити", "Sculpture", "Light", 48, "2E5BA8", V(1.24, 2.112, 1.04),
	"Тутмос, ок. 1345 до н. э.")
wonder("GizaPyramids", "Rare", "Пирамиды Гизы", "Artifact", "Heavy", 50, "E0B66C", V(3.2, 1.24, 2.64),
	"Гиза, ок. 2600–2500 до н. э.")
wonder("Colosseum", "Rare", "Колизей", "Artifact", "Heavy", 55, "E3CFA3", V(3.56, 1.515, 2.88), "Рим, 80 год")
-- Epic
wonder("StarryNight", "Epic", "Звёздная ночь", "Painting", "Medium", 180, "1E3A8A", V(3.7, 3.98, 1.285),
	"Винсент ван Гог, 1889")
wonder("StatueOfLiberty", "Epic", "Статуя Свободы", "Sculpture", "Medium", 165, "5FB59A", V(1.9, 4.326, 1.94),
	"Фредерик Бартольди, 1886")
wonder("TRexSkeleton", "Epic", "Скелет тираннозавра", "Artifact", "Heavy", 200, "EDE3C8", V(3.866, 2.04, 1.28),
	"окаменелость, меловой период")
wonder("TutMask", "Epic", "Золотая маска Тутанхамона", "Mask", "Light", 150, "EFBF3A", V(2.1, 2.82, 1.59),
	"Египет, ок. 1323 до н. э.")

-- Прежние предметы босса 1 (народные промыслы D38): только для старых сохранений.
for _, entry in {
	{ "FolkWhistle", "Common", "Глиняная свистулька", "Sculpture", "Light", "Block", "E8D5B0", V(1.2, 1.6, 1.8) },
	{ "PaintedTray", "Common", "Расписной поднос", "Artifact", "Light", "Cylinder", "1E1E1E", V(0.3, 2.6, 2.6) },
	{ "NestingDoll", "Rare", "Матрёшка-великан", "Sculpture", "Medium", "Ball", "D93A3A", V(2.2, 2.2, 2.2) },
	{ "RockingHorse", "Rare", "Лошадка-качалка", "Sculpture", "Medium", "Wedge", "F2A93B", V(1.4, 2, 2.8) },
} do
	art(entry[1], 1, entry[2], entry[3], entry[4], entry[5], entry[6], entry[7], entry[8])
	Items[entry[1]].legacy = true
end

-- 2. Барахолка — «Торговец-громила»: «Музей безумных находок» (D42), 12 Common, 10 Rare, 8 Epic. Доход —
-- предварительный баланс, не утверждён. №20 и №22 — золотой микрофон и золотой геймпад вместо исключённых картин.
-- Common
find("GoldenBanana", "Common", "Золотой банан", "Artifact", "Light", 34, "F7C531", V(3.11, 2.39, 1.94),
	"находка Барахолки")
find("CursedTV", "Common", "Проклятый телевизор", "Artifact", "Medium", 38, "E0782C", V(2.2, 3.46, 2),
	"находка Барахолки")
find("UfoJar", "Common", "НЛО в банке", "Artifact", "Light", 42, "A8E6F0", V(1.88, 3.1, 2.01), "находка Барахолки")
find("AstroCat", "Common", "Кот в шлеме", "Sculpture", "Medium", 40, "EEF0F3", V(2.24, 3.14, 2), "находка Барахолки")
find("MagicMushroom", "Common", "Магический гриб", "Sculpture", "Light", 36, "8E44D9", V(2.55, 2.87, 2.69),
	"находка Барахолки")
find("LivingCassette", "Common", "Живая кассета", "Artifact", "Light", 33, "26272E", V(2.8, 2.06, 1.51),
	"находка Барахолки")
find("TrophyBurger", "Common", "Трофейный бургер", "Artifact", "Medium", 35, "E39A43", V(2.92, 2.73, 2.2),
	"находка Барахолки")
find("CrystalHotDog", "Common", "Кристальный хот-дог", "Jewel", "Light", 39, "FF4F7B", V(3.32, 2.01, 1.7),
	"находка Барахолки")
find("RoboDuck", "Common", "Робо-утёнок", "Sculpture", "Light", 41, "FFD12E", V(1.6, 2.64, 2.5), "находка Барахолки")
find("MagicSoda", "Common", "Магическая газировка", "Artifact", "Light", 32, "E040A0", V(2.12, 3.72, 1.89),
	"находка Барахолки")
find("MonsterRadio", "Common", "Монстр-радио", "Instrument", "Medium", 37, "D8352A", V(2.84, 3.42, 1.4),
	"находка Барахолки")
find("PocketSafe", "Common", "Карманный сейф", "Artifact", "Heavy", 44, "3E6B9E", V(2.6, 2.6, 1.97),
	"находка Барахолки")
-- Rare
find("MimicChest", "Rare", "Живой сундук-мимик", "Artifact", "Heavy", 120, "8A4E2B", V(2.91, 2.55, 2.94),
	"находка Барахолки")
find("PortalMirror", "Rare", "Зеркало-портал", "Artifact", "Medium", 128, "7A3FD8", V(3.26, 4.85, 1.2),
	"находка Барахолки")
find("AllSeeingEye", "Rare", "Всевидящее око", "Artifact", "Medium", 115, "F2C230", V(2.97, 3.8, 1.75),
	"находка Барахолки")
find("RoyalDuck", "Rare", "Королевская утка", "Sculpture", "Medium", 110, "FFD12E", V(2.36, 3.26, 2.2),
	"находка Барахолки")
find("MonsterFlower", "Rare", "Цветок-монстр", "Sculpture", "Medium", 112, "E040A0", V(2.46, 4.17, 1.56),
	"находка Барахолки")
find("WorldInBottle", "Rare", "Мир в бутылке", "Artifact", "Medium", 125, "A8E6F0", V(3.34, 1.78, 1.52),
	"находка Барахолки")
find("MonaLisa", "Rare", "Мона Лиза", "Painting", "Medium", 150, "E8B530", V(3.18, 4.73, 1.28),
	"Леонардо да Винчи, 1503–1506")
find("GoldenMic", "Rare", "Золотой микрофон", "Instrument", "Light", 140, "F2C230", V(2.05, 4, 1.85),
	"находка Барахолки")
find("VanGoghSelfPortrait", "Rare", "Автопортрет ван Гога", "Painting", "Medium", 132, "2F5BD8", V(3.28, 3.53,
	1.8), "Винсент ван Гог, 1887")
find("GoldenGamepad", "Rare", "Золотой геймпад", "Artifact", "Medium", 136, "F2C230", V(3.08, 2.57, 1.74),
	"находка Барахолки")
-- Epic
find("GoldenThrone", "Epic", "Золотой трон", "Artifact", "Heavy", 480, "F2C230", V(3.16, 4.66, 2.44),
	"находка Барахолки")
find("BlackCatIdol", "Epic", "Чёрная кошка-идол", "Sculpture", "Medium", 440, "26232E", V(2, 2.82, 1.7),
	"находка Барахолки")
find("CrystalDino", "Epic", "Кристальный динозавр", "Sculpture", "Heavy", 520, "4FD8F0", V(4.33, 4.37, 1.74),
	"находка Барахолки")
find("PrizeMachine", "Epic", "Легендарный автомат с призами", "Artifact", "Heavy", 460, "D8352A", V(1.72, 4.2,
	1.79), "находка Барахолки")
find("PocketDragon", "Epic", "Портативный дракон", "Sculpture", "Medium", 540, "3FBF5A", V(2.84, 2.42, 1.79),
	"находка Барахолки")
find("NeonHeart", "Epic", "Сердце из неона", "Artifact", "Medium", 420, "FF2E7E", V(2.78, 3.05, 1.4),
	"находка Барахолки")
find("SpaceHelmet", "Epic", "Гигантский космический шлем", "Artifact", "Medium", 450, "EEF0F3", V(2.52, 3.44,
	2.34), "находка Барахолки")
find("ChaosCrown", "Epic", "Тёмная корона хаоса", "Jewel", "Medium", 600, "2A1F3D", V(2.89, 2.64, 2.16),
	"находка Барахолки")

-- Черновик-антиквариат босса 2 до D42: только для старых сохранений.
art("PorcelainDog", 2, "Common", "Фарфоровая собачка", "Sculpture", "Light", "Block", "F5F0E6", V(1.4, 1.8, 1.8))
art("MantelClock", 2, "Common", "Каминные часы", "Artifact", "Light", "Block", "8A5A2B", V(2, 2, 1))
art("Gramophone", 2, "Rare", "Граммофон", "Instrument", "Medium", "Wedge", "C9A227", V(2, 2.6, 2.4))
art("MusicBox", 2, "Rare", "Музыкальная шкатулка", "Artifact", "Light", "Block", "6B2E5F", V(2, 1.4, 1.4))
for _, id in { "PorcelainDog", "MantelClock", "Gramophone", "MusicBox" } do
	Items[id].legacy = true
end

-- 3. Склад — «Робот-охранник»: запасники музея.
art("CratedVase", 3, "Common", "Ваза в ящике", "Vase", "Medium", "Block", "B98B5B", V(2.2, 2.2, 2.2))
art("PlasterBust", 3, "Common", "Гипсовый бюст", "Sculpture", "Medium", "Block", "EDEDED", V(1.6, 2.4, 1.4))
art("KnightArmor", 3, "Rare", "Рыцарские доспехи", "Sculpture", "Heavy", "Block", "A8B2BD", V(1.8, 3.4, 1.4))
art("BronzeHorse", 3, "Rare", "Бронзовый конь", "Sculpture", "Heavy", "Wedge", "8C6A3D", V(1.4, 2.4, 3))

-- 4. Пустыня — «Сфинкс»: Древний Египет.
art("CanopicJar", 4, "Common", "Канопа", "Vase", "Light", "Cylinder", "D9C7A1", V(2.2, 1.3, 1.3))
art("ScarabAmulet", 4, "Common", "Амулет-скарабей", "Jewel", "Light", "Ball", "1F8A70", V(1.6, 1.6, 1.6))
art("BastetCat", 4, "Rare", "Статуэтка кошки Бастет", "Sculpture", "Medium", "Block", "23262B", V(1.2, 2.8, 1.6))
art("GoldenAnkh", 4, "Rare", "Золотой анх", "Jewel", "Light", "Block", "E3B341", V(1.6, 2.6, 0.5))
art("Nefertiti", 4, "Legendary", "Бюст Нефертити", "Sculpture", "Medium", "Block", "2C6EB5", V(1.6, 3, 1.8),
	"Тутмос, ок. 1345 до н. э.")

-- 5. Ледник — «Полярный медведь»: северное искусство.
art("VikingFigure", 5, "Common", "Фигурка викинга", "Sculpture", "Light", "Block", "8D6E63", V(1.2, 2.2, 1.2))
art("RuneStone", 5, "Common", "Рунический камень", "Artifact", "Heavy", "Block", "8E9AA5", V(1.6, 2.8, 0.8))
art("Longship", 5, "Rare", "Ладья викингов", "Sculpture", "Medium", "Wedge", "9C6B3C", V(1.2, 1.8, 3.4))
art("IceSwan", 5, "Rare", "Ледяной лебедь", "Sculpture", "Medium", "Block", "BFE9FF", V(1.6, 2.4, 2.4))
art("NinthWave", 5, "Legendary", "Девятый вал", "Painting", "Medium", "Block", "3A8F8C", V(3.4, 2.2, 0.4),
	"Иван Айвазовский, 1850")

-- 6. Джунгли — «Горилла»: Мезоамерика.
art("MayaVessel", 6, "Common", "Сосуд майя", "Vase", "Light", "Cylinder", "B5653A", V(2, 1.5, 1.5))
art("JadeMask", 6, "Common", "Нефритовая маска", "Mask", "Light", "Block", "3E9C6B", V(1.8, 2.2, 0.6))
art("JaguarTotem", 6, "Rare", "Тотем-ягуар", "Sculpture", "Heavy", "Block", "C98A2B", V(1.4, 3.2, 1.4))
art("FeatheredSerpent", 6, "Rare", "Пернатый змей", "Sculpture", "Medium", "Wedge", "2F9E5B", V(1.4, 1.8, 3))
art("OlmecHead", 6, "Epic", "Голова ольмеков", "Sculpture", "Heavy", "Block", "7D7A70", V(2.6, 2.8, 2.4),
	"Ольмеки, ок. 1200 до н. э.")
art("SunStone", 6, "Legendary", "Камень Солнца", "Artifact", "Heavy", "Cylinder", "A89F91", V(0.8, 3.2, 3.2),
	"Ацтеки, 1502–1521")

-- 7. Банк — «Бронированный охранник»: сокровищница.
art("SilverMedal", 7, "Common", "Серебряная медаль", "Jewel", "Light", "Cylinder", "C9CED6", V(0.4, 2, 2))
art("Candelabra", 7, "Common", "Канделябр", "Artifact", "Light", "Block", "D9B45A", V(1.6, 2.8, 1))
art("JewelCasket", 7, "Rare", "Шкатулка с самоцветами", "Jewel", "Medium", "Block", "7A1F3D", V(2.2, 1.6, 1.6))
art("GoldenGoblet", 7, "Rare", "Золотой кубок", "Jewel", "Light", "Cylinder", "E8C14A", V(2.4, 1.4, 1.4))
art("TheKiss", 7, "Epic", "Поцелуй", "Painting", "Medium", "Block", "D6A93A", V(2.8, 2.8, 0.4), "Густав Климт, 1907–1908")
art("CoronationEgg", 7, "Legendary", "Коронационное яйцо", "Jewel", "Light", "Ball", "E5B93C", V(2, 2, 2),
	"Карл Фаберже, 1897")

-- 8. Вулкан — «Лавовый голем»: античность.
art("MeanderAmphora", 8, "Common", "Амфора с меандром", "Vase", "Medium", "Cylinder", "C2662D", V(2.8, 1.5, 1.5))
art("IonicColumn", 8, "Common", "Ионическая колонна", "Sculpture", "Medium", "Cylinder", "ECE6D8", V(3, 1.2, 1.2))
art("HopliteHelmet", 8, "Rare", "Шлем гоплита", "Artifact", "Medium", "Block", "B8862E", V(1.6, 2.2, 1.8))
art("GreekLyre", 8, "Rare", "Лира", "Instrument", "Light", "Block", "C69C52", V(1.8, 2.6, 0.5))
art("AlexanderMosaic", 8, "Epic", "Мозаика Александра", "Painting", "Heavy", "Block", "9C6B4E", V(3.4, 2, 0.5),
	"Помпеи, ок. 100 до н. э.")
art("WingedVictory", 8, "Legendary", "Ника Самофракийская", "Sculpture", "Heavy", "Block", "F2EEE6", V(2.6, 3.4, 1.8),
	"Греция, ок. 190 до н. э.")
art("AgamemnonMask", 8, "Secret", "Маска Агамемнона", "Mask", "Medium", "Block", "E6B83A", V(2, 2.4, 0.8),
	"Микены, ок. 1550 до н. э.")

-- 9. Космопорт — «Пришелец-генерал»: небо и звёзды.
art("SaturnModel", 9, "Common", "Модель Сатурна", "Artifact", "Light", "Ball", "E3C07A", V(2, 2, 2))
art("Meteorite", 9, "Common", "Метеорит на подставке", "Artifact", "Medium", "Ball", "5B4E4A", V(1.8, 1.8, 1.8))
art("Astrolabe", 9, "Rare", "Астролябия", "Instrument", "Light", "Cylinder", "C49A3A", V(0.4, 2.4, 2.4))
art("BrassTelescope", 9, "Rare", "Латунный телескоп", "Instrument", "Medium", "Cylinder", "B5893A", V(3.2, 0.9, 0.9))
art("StarryRhone", 9, "Epic", "Звёздная ночь над Роной", "Painting", "Medium", "Block", "1F3A6E", V(3.2, 2.2, 0.4),
	"Винсент ван Гог, 1888")
art("PragueOrloj", 9, "Legendary", "Пражские куранты", "Artifact", "Heavy", "Cylinder", "2E5D9F", V(0.8, 3, 3),
	"Микулаш из Кадани, 1410")

-- 10. Замок — «Король-дракон»: королевская коллекция.
art("CrestGoblet", 10, "Common", "Кубок с гербом", "Artifact", "Light", "Cylinder", "9AA3AD", V(2, 1.2, 1.2))
art("DragonShield", 10, "Common", "Щит с драконом", "Artifact", "Medium", "Block", "B3261E", V(2.4, 2.8, 0.5))
art("SwordInStone", 10, "Rare", "Меч в камне", "Artifact", "Heavy", "Block", "7C7F86", V(1.8, 3.2, 1.8))
art("MiniThrone", 10, "Rare", "Малый трон", "Artifact", "Heavy", "Block", "8E1F2F", V(2, 3, 2))
art("LadyUnicorn", 10, "Epic", "Дама с единорогом", "Textile", "Medium", "Block", "A3262A", V(2.6, 3.2, 0.3),
	"Гобелен, Франция, ок. 1500")
art("MonomakhCap", 10, "Legendary", "Шапка Мономаха", "Jewel", "Medium", "Cylinder", "D4A23A", V(2.2, 2, 2),
	"Русь, XIII–XIV века")
-- «Мона Лиза» черновика босса 10 убрана (D42): это произведение — в коллекции босса 2, id MonaLisa теперь его.

return Items

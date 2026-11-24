-- Каталог произведений искусства (D37, D40, D42): у каждого из 10 боссов своя коллекция. Босс 1 «Музей чудес» (D40)
-- — 20 предметов, босс 2 «Музей безумных находок» (D42) — 30 (docs/CATALOG.md): модели из Blender (Config/ItemModels,
-- пока меш не загружен — заготовка цвета и размера модели) и свой доход в секунду (income, предварительный баланс, без
-- множителей редкости). Босс 3 «Крысиный король» (D54) — 30 живых существ D55 (Config/CreatureRigs). Коллекции
-- боссов 4–10 — черновик (вид — заготовка, дохода нет), до их очереди. legacy —
-- прежние предметы (народные промыслы босса 1 D38, антиквариат-черновик босса 2): у босса не появляются, но описание
-- остаётся, чтобы старые сохранения загружались. id не повторяются и не переиспользуются для другого произведения.
-- Шансы редкостей у боссов — Progression.BossLoot.
-- Читается сервером и клиентом. Ни от чего не зависит.

export type ItemDef = {
	id: string,
	displayName: string,
	rarity: string, -- Common | Rare | Epic | Legendary | Secret (см. Config/Rarities)
	boss: number, -- босс (уровень 1–10), в чьей коллекции предмет
	kind: string, -- Painting | Sculpture | Vase | Mask | Artifact | Jewel | Instrument | Textile | Creature (D55)
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

-- 3. Подземка — «Крысиный король»: коллекция «Крысиный король» (D54, каталог утверждён владельцем 2026-11-08,
-- docs/CATALOG.md) — 30 живых существ D55: 12 Common, 10 Rare, 8 Epic. Модель — из подвижных частей
-- (Config/CreatureRigs: скелет D54 и Part-версия до импорта мешей), цвет и размер — живого существа без подставки.
-- Доход — предварительный баланс, не утверждён.
local function creature(
	id: string,
	rarity: string,
	displayName: string,
	weight: string,
	income: number,
	color: string,
	size: Vector3
)
	collectible(3, id, rarity, displayName, "Creature", weight, income, color, size, "существо Подземки")
end
-- Живое существо босса 4 «Сфинкс-лежебока» (D57, D58): доход и вес утверждены, модель — Config/CreatureRigs.
local function creature4(
	id: string,
	rarity: string,
	displayName: string,
	weight: string,
	income: number,
	color: string,
	size: Vector3
)
	collectible(4, id, rarity, displayName, "Creature", weight, income, color, size, "существо Пустыни")
end
-- Живое существо босса 5 «Йети-коллекционер» (D64): доход — ступень 3.2 (вариант А), вес D58, модель — Config/CreatureRigs.
local function creature5(
	id: string,
	rarity: string,
	displayName: string,
	weight: string,
	income: number,
	color: string,
	size: Vector3
)
	collectible(5, id, rarity, displayName, "Creature", weight, income, color, size, "существо Ледника")
end

-- D55: коллекция босса 3 (сгенерировано scripts/creature_rigs_to_luau.py — руками не править)
creature("LiveCheeseMonster", "Common", "Живой сыр-монстр", "Medium", 110, "E8AC2C", V(3.081, 2.234, 1.954))
creature("PizzaRat", "Common", "Пицца-крыса", "Heavy", 104, "E1B04C", V(3.393, 1.718, 3.42))
creature("RunawayTicket", "Common", "Билетик-беглец", "Medium", 98, "F7D974", V(2.96, 2.416, 1.321))
creature("RatKnight", "Common", "Крыса-рыцарь", "Medium", 95, "ACB3C0", V(2.401, 2.911, 2.066))
creature("MutantSoda", "Common", "Газировка-мутант", "Medium", 108, "2DAD58", V(2.2, 2.6, 2.188))
creature("SubwaySnail", "Common", "Улитка-метро", "Medium", 112, "2A609E", V(2.859, 1.848, 2.135))
creature("WalkingSuitcase", "Common", "Чемодан на ножках", "Medium", 100, "E45946", V(2.201, 2.02, 1.245))
creature("AngryAlarmClock", "Common", "Злой будильник", "Medium", 115, "DB6336", V(1.942, 2.821, 1.125))
creature("SneakerTenant", "Common", "Кроссовок с жильцом", "Heavy", 102, "D13439", V(3.22, 2.623, 2.076))
creature("DuckInspector", "Common", "Утка-контролёр", "Light", 118, "E4BC37", V(2.146, 2.13, 2.196))
creature("PanicCone", "Common", "Конус-паникёр", "Medium", 120, "EAEBE4", V(2.14, 2.74, 1.78))
creature("CheeseSkater", "Common", "Сырный скейтер", "Medium", 125, "BDBFC8", V(2.6, 2.163, 1.545))
creature("DevourerVending", "Rare", "Автомат-пожиратель", "Heavy", 380, "AF2634", V(2, 3.7, 1.957))
creature("RoyalRatTrain", "Rare", "Королевский крысовоз", "Medium", 340, "9F2E4E", V(2.914, 2.32, 1.95))
creature("BuffRat", "Rare", "Крыса-качок", "Heavy", 320, "7486B3", V(3.11, 3.533, 1.798))
creature("TrashGobbler", "Rare", "Мусорный обжора", "Medium", 330, "267A3E", V(1.639, 2.953, 2.581))
creature("RatWizard", "Rare", "Крысиный маг", "Heavy", 370, "4B2A8B", V(2.475, 3.316, 1.553))
creature("RatMimic", "Rare", "Сундук-мимик", "Medium", 350, "76472A", V(2.021, 2.277, 2.643))
creature("ThreeHeadedRat", "Rare", "Трёхголовая крыса", "Heavy", 345, "848DAC", V(3.114, 3.336, 2.166))
creature("TurnstileTerminator", "Rare", "Турникет-терминатор", "Heavy", 360, "283049", V(2.744, 3.28, 1.041))
creature("PizzaUfo", "Rare", "Пицца-НЛО", "Medium", 400, "D49B48", V(3.154, 3.108, 3.13))
creature("RubyThief", "Rare", "Рубиновый воришка", "Medium", 335, "4E5A6E", V(2.864, 2.65, 1.567))
creature("RatThrone", "Epic", "Крысиный трон", "Heavy", 1500, "E2B734", V(3.56, 3.762, 3.56))
creature("MonsterTrain", "Epic", "Поезд-монстр", "Medium", 1600, "C12D27", V(2.993, 2.061, 2.466))
creature("CheeseDragon", "Epic", "Сырный дракон", "Heavy", 1450, "EFA222", V(3.505, 3.283, 3.171))
creature("GoldenRatMech", "Epic", "Золотой крысомех", "Heavy", 1300, "E1B42F", V(2.981, 3.795, 1.324))
creature("SubwayOctopus", "Epic", "Подземный осьминог", "Heavy", 1400, "CA981F", V(3.5, 4.05, 3.5))
creature("ClockGolem", "Epic", "Часовой голем", "Heavy", 1250, "212C57", V(3.08, 4.122, 0.961))
creature("CheeseVaultHeart", "Epic", "Сердце сырного хранилища", "Heavy", 1350, "E4B62D", V(3.321, 2.101, 2.414))
creature("ThreeTailEmperor", "Epic", "Император трёх хвостов", "Heavy", 1700, "DEB22E", V(3.5, 4.55, 3.5))
-- D55: конец коллекции босса 3

-- Черновик «Склада» (запасники музея, D38) до D54: только для старых сохранений.
art("CratedVase", 3, "Common", "Ваза в ящике", "Vase", "Medium", "Block", "B98B5B", V(2.2, 2.2, 2.2))
art("PlasterBust", 3, "Common", "Гипсовый бюст", "Sculpture", "Medium", "Block", "EDEDED", V(1.6, 2.4, 1.4))
art("KnightArmor", 3, "Rare", "Рыцарские доспехи", "Sculpture", "Heavy", "Block", "A8B2BD", V(1.8, 3.4, 1.4))
art("BronzeHorse", 3, "Rare", "Бронзовый конь", "Sculpture", "Heavy", "Wedge", "8C6A3D", V(1.4, 2.4, 3))
for _, id in { "CratedVase", "PlasterBust", "KnightArmor", "BronzeHorse" } do
	Items[id].legacy = true
end

-- 4. Пустыня — «Сфинкс-лежебока»: 30 живых существ (D57 — каталог и доходы, D58 — веса и подставки).
-- D57: коллекция босса 4 (сгенерировано scripts/creature_rigs_to_luau.py — руками не править)
creature4("CactusBoxer", "Common", "Кактус-боксёр", "Medium", 386, "3BA245", V(2.48, 2.384, 1.975))
creature4("FloppyFennec", "Common", "Фенек-лопоух", "Medium", 328, "DCB365", V(1.921, 3.083, 1.369))
creature4("TumbleweedRunner", "Common", "Перекати-поле-бегун", "Medium", 312, "B18437", V(1.967, 2.448, 2.017))
creature4("CanteenCamel", "Common", "Верблюжонок-фляга", "Medium", 376, "D5A05C", V(2.384, 2.58, 1.023))
creature4("DuneTurtle", "Common", "Черепаха-бархан", "Medium", 336, "E79F61", V(2.12, 1.392, 2.389))
creature4("UmbrellaLizard", "Common", "Ящерка-зонтик", "Medium", 352, "FCFAF1", V(2.218, 2.511, 1.74))
creature4("MelonArmadillo", "Common", "Арбуз-броненосец", "Medium", 304, "489C3F", V(1.76, 1.361, 2.66))
creature4("StrawSnake", "Common", "Змейка-соломинка", "Light", 344, "6D4122", V(2.177, 1.839, 1.371))
creature4("DropBeetle", "Common", "Жук-капелька", "Light", 320, "3FC0D0", V(1.521, 2.046, 1.53))
creature4("MeerkatLookout", "Common", "Сурикат-часовой", "Light", 360, "CB9C56", V(1.484, 2.06, 2.193))
creature4("CanScorpion", "Common", "Скорпион-лейка", "Light", 402, "E87B26", V(2, 2.151, 2.198))
creature4("SandChick", "Common", "Страусёнок-песочник", "Medium", 368, "EDC553", V(1.426, 3.1, 1.66))
creature4("AquariumCamel", "Rare", "Верблюд-аквариум", "Medium", 1220, "E0A351", V(2.868, 2.876, 1.228))
creature4("CactusAcrobats", "Rare", "Кактусы-акробаты", "Heavy", 1160, "399E3F", V(1.507, 3.301, 1.34))
creature4("DrillWorm", "Rare", "Песчаный червь-бурильщик", "Light", 1040, "BE5932", V(2, 1.721, 1.994))
creature4("FanVulture", "Rare", "Гриф-вентилятор", "Medium", 1190, "8147B7", V(2.863, 2.24, 1.615))
creature4("CobraFountain", "Rare", "Кобра-фонтан", "Medium", 1130, "D8C090", V(2.08, 2.416, 2.08))
creature4("DustDevil", "Rare", "Смерч-озорник", "Medium", 1070, "F6DDA8", V(2.603, 2.383, 2.196))
creature4("KaleidoChameleon", "Rare", "Хамелеон-калейдоскоп", "Medium", 1100, "D4AF35", V(2.673, 1.948, 0.82))
creature4("FennecRiddler", "Rare", "Фенек-загадочник", "Heavy", 1250, "E29736", V(3.066, 3.894, 1.98))
creature4("MirageFish", "Rare", "Рыба-мираж", "Light", 1010, "37C4CF", V(2.139, 2.362, 1.12))
creature4("DuneWhale", "Epic", "Кит-бархан", "Medium", 4100, "E6CE98", V(2.841, 2.81, 2.66))
creature4("IslandTurtle", "Epic", "Черепаха-остров", "Medium", 5200, "349CCD", V(2.621, 2.07, 2.97))
creature4("BlazeOstrich", "Epic", "Жар-страус", "Heavy", 4500, "D83B2B", V(2.393, 3.433, 2.483))
creature4("CloudCamel", "Epic", "Верблюд-туча", "Heavy", 4900, "E2A355", V(2.889, 3.536, 1.7))
creature4("CrystalScorpion", "Epic", "Кристальный скорпион", "Medium", 4720, "D59931", V(2.12, 2.544, 2.055))
creature4("GiantCactus", "Epic", "Кактус-великан", "Heavy", 4300, "287B33", V(2.07, 3.367, 1.019))
creature4("SpringAntelope", "Legendary", "Антилопа-родник", "Heavy", 12700, "E4E1DA", V(2.679, 3.409, 1.741))
creature4("PuzzlePhoenix", "Legendary", "Феникс-головоломка", "Medium", 13880, "F1A533", V(2.776, 2.69, 2.126))
creature4("TornadoKing", "Legendary", "Царь-смерч", "Heavy", 15000, "5349A1", V(3.077, 4.04, 2.24))
-- D57: конец коллекции босса 4

-- Черновик «Древнего Египта» зоны 4 до D57 (заготовки без дохода): только для старых сохранений.
art("CanopicJar", 4, "Common", "Канопа", "Vase", "Light", "Cylinder", "D9C7A1", V(2.2, 1.3, 1.3))
art("ScarabAmulet", 4, "Common", "Амулет-скарабей", "Jewel", "Light", "Ball", "1F8A70", V(1.6, 1.6, 1.6))
art("BastetCat", 4, "Rare", "Статуэтка кошки Бастет", "Sculpture", "Medium", "Block", "23262B", V(1.2, 2.8, 1.6))
art("GoldenAnkh", 4, "Rare", "Золотой анх", "Jewel", "Light", "Block", "E3B341", V(1.6, 2.6, 0.5))
art("Nefertiti", 4, "Legendary", "Бюст Нефертити", "Sculpture", "Medium", "Block", "2C6EB5", V(1.6, 3, 1.8),
	"Тутмос, ок. 1345 до н. э.")
for _, id in { "CanopicJar", "ScarabAmulet", "BastetCat", "GoldenAnkh", "Nefertiti" } do
	Items[id].legacy = true
end

-- 5. Ледник — «Йети-коллекционер»: 30 живых существ (D64 — каталог docs/BOSS5_CATALOG.md, доходы по ступени 3.2, вес D58).
-- D64: коллекция босса 5 (сгенерировано scripts/creature_rigs_to_luau.py — руками не править)
creature5("PenguinGiraffe", "Common", "Пингвин-жираф", "Heavy", 1280, "243666", V(1.639, 4.289, 1.441))
creature5("SnowSlime", "Common", "Снежный слизень", "Medium", 1150, "8CDCFB", V(2.624, 2.145, 2.436))
creature5("TwoHeadFox", "Common", "Двухголовый песец", "Light", 1200, "D6D9DF", V(2.006, 2.14, 1.986))
creature5("FluffCyclops", "Common", "Пушистик-циклоп", "Heavy", 1230, "AD83E3", V(2.4, 3.44, 2.145))
creature5("MustacheWalrus", "Common", "Морж-усач", "Medium", 1180, "BB805C", V(2.879, 2.322, 2.826))
creature5("SealCaterpillar", "Common", "Тюлень-гусеница", "Heavy", 1020, "A0AEC1", V(1.264, 1.556, 3.228))
creature5("HedgeOwl", "Common", "Сова-ёж", "Medium", 1070, "9F7049", V(2.565, 2.382, 2.35))
creature5("IceCrab", "Common", "Краб-льдина", "Medium", 1120, "E25338", V(3.128, 1.776, 2.91))
creature5("SkiEarHare", "Common", "Заяц-лыжник", "Medium", 1110, "E0E4EB", V(1.19, 2.302, 3.069))
creature5("SnowWorm", "Common", "Снежный червь", "Medium", 1000, "DADFE8", V(2.509, 2.027, 2.176))
creature5("WalkingFish", "Common", "Рыба на лапках", "Medium", 970, "81998C", V(1.525, 2.31, 3.15))
creature5("AntlerFawn", "Common", "Оленёнок-рога", "Heavy", 1050, "EFDFBE", V(3.099, 3.281, 2.303))
creature5("SpringMammoth", "Rare", "Мамонтёнок-пружина", "Heavy", 3900, "BB6E39", V(1.521, 2.305, 3.324))
creature5("AccordionBear", "Rare", "Медведь-гармошка", "Heavy", 3710, "F0F4FB", V(1.138, 1.45, 3.202))
creature5("IceSpider", "Rare", "Ледяной паук", "Medium", 3810, "E5E9EF", V(2.911, 1.786, 2.405))
creature5("LeggedNarwhal", "Rare", "Нарвал на ножках", "Heavy", 3615, "6277A4", V(1.806, 1.587, 3.403))
creature5("PenguinStack", "Rare", "Пингвинья пирамида", "Medium", 4000, "949DB4", V(2.762, 2.454, 1.13))
creature5("SwivelOwl", "Rare", "Филин-вертушка", "Medium", 3420, "BBBFC9", V(1.56, 2.791, 1.62))
creature5("WalkingJelly", "Rare", "Медуза-ходок", "Heavy", 3330, "ED93C6", V(3.484, 2.692, 3.053))
creature5("ElephantSeal", "Rare", "Морской слон-надувала", "Heavy", 3520, "907A6A", V(2.012, 1.875, 3.418))
creature5("ToothBeaver", "Rare", "Бобр-зубастик", "Medium", 3230, "7F5237", V(1.36, 2.164, 2.386))
creature5("WingedWalrus", "Epic", "Морж с крылышками", "Medium", 15100, "AD7350", V(2.639, 2.958, 2.55))
creature5("OwlTotem", "Epic", "Сова-тотем", "Heavy", 16600, "4871C6", V(1.458, 3.842, 1.375))
creature5("NestDeer", "Epic", "Олень-гнездо", "Heavy", 12720, "A27044", V(2.191, 3.699, 3.04))
creature5("GiantPenguin", "Epic", "Пингвин-гигант", "Heavy", 13800, "233565", V(3.377, 3.222, 2.492))
creature5("BallBear", "Epic", "Медведь-шар", "Medium", 15700, "E4E8EF", V(3.196, 3.11, 2.971))
creature5("StiltWhale", "Epic", "Кит на ходулях", "Heavy", 14784, "364F95", V(2.13, 4.223, 2.559))
creature5("YetiCub", "Legendary", "Йетёнок-коллекционер", "Heavy", 48000, "E7EAF1", V(2.401, 3.205, 1.919))
creature5("IcebergNarwhal", "Legendary", "Нарвал-айсберг", "Heavy", 44352, "46608F", V(2.993, 2.95, 3.56))
creature5("ThreeHeadSerpent", "Legendary", "Ледяной змей", "Heavy", 40704, "56B7DD", V(2.898, 3.626, 2.898))
-- D64: конец коллекции босса 5

-- Черновик «Полярного медведя» зоны 5 до D64 (заготовки без дохода): только для старых сохранений.
art("VikingFigure", 5, "Common", "Фигурка викинга", "Sculpture", "Light", "Block", "8D6E63", V(1.2, 2.2, 1.2))
art("RuneStone", 5, "Common", "Рунический камень", "Artifact", "Heavy", "Block", "8E9AA5", V(1.6, 2.8, 0.8))
art("Longship", 5, "Rare", "Ладья викингов", "Sculpture", "Medium", "Wedge", "9C6B3C", V(1.2, 1.8, 3.4))
art("IceSwan", 5, "Rare", "Ледяной лебедь", "Sculpture", "Medium", "Block", "BFE9FF", V(1.6, 2.4, 2.4))
art("NinthWave", 5, "Legendary", "Девятый вал", "Painting", "Medium", "Block", "3A8F8C", V(3.4, 2.2, 0.4),
	"Иван Айвазовский, 1850")
for _, id in { "VikingFigure", "RuneStone", "Longship", "IceSwan", "NinthWave" } do
	Items[id].legacy = true
end

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

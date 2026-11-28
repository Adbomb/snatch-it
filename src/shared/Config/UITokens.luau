-- Токены интерфейса из UI_KIT.md: цвета, градиенты, редкость, скругления, обводки, шрифты, раскладка.
-- Единственное место с числами внешнего вида; UIKit и подписи над предметами берут их отсюда.
-- Читается сервером и клиентом. Ни от чего не зависит.

local UITokens = {}

export type Gradient = { top: Color3, bottom: Color3 }

local function gradient(top: string, bottom: string): Gradient
	return { top = Color3.fromHex(top), bottom = Color3.fromHex(bottom) }
end

UITokens.Colors = {
	Ink = Color3.fromHex("1B1530"),
	InkSoft = Color3.fromHex("2B2350"),
	Panel = Color3.fromHex("F4F8FF"),
	Header = Color3.fromHex("3D7BFF"),
	TextOnColor = Color3.fromHex("FFFFFF"), -- текст на цветных кнопках, шапках и плашках
}

-- Градиенты кнопок: сверху вниз.
UITokens.Gradients = {
	Go = gradient("5BEA72", "1FA83A"),
	Info = gradient("5CB0FF", "2366E8"),
	Stop = gradient("FF6B6B", "D92D3A"),
	Coin = gradient("FFE15A", "F5A400"),
	Night = gradient("B04BFF", "FF2E63"),
	Disabled = gradient("C9D0DA", "8E98A8"),
}

-- Редкость (D20): градиенты подписей Stud-UI, верх светлый → низ насыщенный. Secret — цвета Cosmic.
UITokens.Rarity = {
	Common = gradient("D9D7E3", "ADA6B4"),
	Rare = gradient("84CAE8", "3D8EE0"),
	Epic = gradient("E2B0FF", "9A3EF0"), -- лестница Stud-UI
	Legendary = gradient("FFE27A", "F5A215"),
	Secret = gradient("CDBCFF", "6A45F5"),
}

UITokens.Corner = {
	Button = UDim.new(0, 16),
	IconButton = UDim.new(0, 18),
	Card = UDim.new(0, 20),
	Window = UDim.new(0, 24),
	Pill = UDim.new(0.5, 0),
}

UITokens.Stroke = {
	Border = 3, -- UIStroke Border, цвет Ink
	Text = 2, -- UIStroke Contextual, цвет Ink
}

UITokens.Button = {
	DarkBar = 6, -- нижняя тёмная полоса, px
	DarkBarShade = 0.35, -- насколько нижний цвет градиента темнеет к Ink в полосе
	Shadow = 5, -- тень Ink вниз, px
	PressOffset = 4, -- на сколько опускается при нажатии, px
	PressTime = 0.08, -- секунды
}

-- Шрифты. Body — один токен на весь текст: если кириллица в Nunito не отрисуется,
-- меняем BodyFamily на "rbxasset://fonts/families/BuilderSans.json" (Bold).
UITokens.Fonts = {
	Logo = Font.fromEnum(Enum.Font.LuckiestGuy), -- только латиница
	BodyFamily = "rbxasset://fonts/families/Nunito.json",
	Heavy = Enum.FontWeight.Heavy,
	ExtraBold = Enum.FontWeight.ExtraBold,
	Bold = Enum.FontWeight.Bold,
}

function UITokens.BodyFont(weight: Enum.FontWeight?): Font
	return Font.new(UITokens.Fonts.BodyFamily, weight or UITokens.Fonts.Heavy)
end

UITokens.TextSize = {
	Small = 16,
	Body = 20,
	Title = 26,
	Huge = 40,
}

-- Подсветка экспоната, выбранного для «Переставить».
UITokens.Highlight = {
	Fill = Color3.fromHex("FFE15A"), -- верх градиента Coin
	FillTransparency = 0.55,
	Outline = Color3.fromHex("FFFFFF"),
}

UITokens.Motion = {
	Slide = 0.2, -- выезд и уезд уведомлений и окон, секунды
}

UITokens.Spacing = {
	Small = 6,
	Medium = 12,
	Large = 20,
}

-- Раскладка экрана (UI_KIT.md, «Раскладка»). Позиции и размеры — в Scale.
UITokens.Layout = {
	RobloxMenu = Vector2.new(210, 56), -- верхний левый угол, не занимать
	MinTouchButton = Vector2.new(52, 52),
	-- Уведомления: колонка справа, ниже верхней панели Roblox.
	Toasts = {
		-- HUD v3: сверху по центру под местом плашки входа в зону (timerGap — зазор под ней); при открытом окне меню —
		-- в полосе справа от окна (menuGap — зазоры до окна и края экрана)
		menuGap = 12,
		timerGap = 6,
		size = UDim2.fromScale(0.26, 0.3), -- невысокая: на телефоне одно уведомление, персонажа не закрывает
		minWidth = 180,
		maxWidth = 360,
		itemHeight = 56,
		lifetime = 4, -- секунды
		maxCount = 4, -- не больше, чем помещается в высоту колонки (на телефоне — 2)
		displayOrder = 14, -- поверх окон «Инвентарь» и «Защита» (12) и расстановки защиты (13), под плашкой зоны (30)
		windowCheck = 0.25, -- секунд между проверками, открыто ли окно меню (колонка — справа от окна)
	},
	-- Окно хранилища: по центру экрана.
	StorageWindow = {
		size = UDim2.fromScale(0.6, 0.7),
		minSize = Vector2.new(300, 280),
		maxSize = Vector2.new(720, 560),
		headerHeight = 52,
		cardSize = Vector2.new(150, 150),
	},
	-- Баннер презентации экспоната у владельца: сверху по центру, правее меню Roblox.
	PresentationBanner = {
		position = UDim2.fromScale(0.5, 0.14),
		size = UDim2.fromScale(0.42, 0.12),
		minSize = Vector2.new(260, 70),
		maxSize = Vector2.new(560, 110),
	},
}

-- Табличка «Улучшение» во дворе (D34): SurfaceGui на табло участка и всплывающее «+N» при качании.
UITokens.GymSign = {
	PixelsPerStud = 50,
	MaxDistance = 90, -- дальше табличку не рисуем
	Level = Color3.fromHex("5BEA72"), -- строка «Уровень N > N+1» (верх градиента Go)
	TitleSize = 46,
	LineSize = 34,
	ButtonSize = 30,
}
UITokens.GymGain = {
	Color = Color3.fromHex("FFE15A"), -- верх градиента Coin
	Size = UDim2.fromScale(6, 1.6), -- BillboardGui, стады
	Start = 3, -- стадов над головой
	Rise = 3, -- на сколько всплывает
	Spread = 1.5, -- разброс по горизонтали, стады
	Time = 0.9, -- секунды
	TextSize = 40,
}

-- Таймер фазы (вид — по референсу владельца 2026-11-17): справа внизу — маленький значок фазы и две короткие строки
-- белым жирным курсивом с чёрной обводкой: «День 0:57» и подпись про Судную ночь; под ними едва заметная тёмная
-- полоса. Без панели и полосы прогресса. На касании — левее кнопки прыжка или под ней (Client/UI/HudLayout).
UITokens.TimeHud = {
	Icon = 34, -- px при масштабе 1 (масштаб надписей HUD — Client/UI/HudLayout.InfoScale)
	Gap = 6, -- между значком и текстом
	PhaseSize = 19, -- «День 0:57»
	InfoSize = 16, -- «Судная ночь — завтра»
	LineGap = 0,
	Margin = Vector2.new(12, 6), -- от правого и нижнего края (на касании справа — от зоны кнопки прыжка)
	Refresh = 0.2, -- секунды между обновлениями отсчёта
	Strip = 0.87, -- прозрачность тёмной полосы под таймером у её правого края (к левому — прозрачная)
	StripPad = 10, -- поля полосы вокруг значка и текста
	Danger = Color3.fromHex("FF6A6A"), -- отсчёт в последние секунды фазы и подпись «Судная ночь — сегодня»
	-- Названия фаз (номер дня не пишется, D51).
	Titles = {
		Day = "День",
		Preparation = "Подготовка",
		Night = "Ночь",
		DoomNight = "Судная ночь",
	},
	Warning = 15, -- последние секунды фазы: отсчёт мигает цветом Danger
}

-- Плашка входа в уровень (D41; HUD v3 — маленькая и короткая): сверху по центру под кнопками Roblox, цвет — от
-- спокойного зелёного к тревожному (по номеру зоны). Персонажа и дорогу не закрывает.
UITokens.LevelBanner = {
	Size = Vector2.new(250, 46), -- пиксели при масштабе 1 (масштаб HUD — Client/UI/HudLayout.Scale)
	Top = 6, -- от низа кнопок Roblox
	Hold = 1.1, -- секунд на экране после появления
	In = 0.25,
	Out = 0.25,
	Emoji = 30, -- круг со смайликом
	TitleSize = 22,
	Check = 0.15, -- секунды между проверками, в какой зоне игрок
	-- Градиенты панели по номеру зоны 1…10 (верх → низ): добрый зелёный → жёлтый → оранжевый → красный → тёмный.
	Themes = {
		{ "7DF06A", "2BB84A" },
		{ "B6F04E", "56C223" },
		{ "FFE45A", "E8B10C" },
		{ "FFC048", "F08A12" },
		{ "FF9F4A", "E85F16" },
		{ "FF7A5A", "D93A2A" },
		{ "FF5A6E", "C21A3A" },
		{ "E24A8A", "9C1460" },
		{ "B04BFF", "6A1FC9" },
		{ "6A5A7A", "1E1428" },
	},
}

-- Круглое фото и ник владельца над входом в музей (D41): размеры в стадах (BillboardGui в мире).
UITokens.OwnerTag = {
	Size = Vector2.new(10, 8.2), -- ширина и высота подписи, стадов (фото — в середине сверху, ник — снизу во всю ширину)
	Ring = Color3.fromHex("FFFFFF"),
	RingDark = Color3.fromHex("1E2433"),
	MaxDistance = 260,
}

-- Значок над башней (D74, сигнал редкости): имя владельца и счётчики редких этажей. Размеры — пиксели при масштабе
-- экрана 1 (значок на экране одного размера с любого расстояния); MaxDistance — стадов по земле; Lift — над маяком.
-- Иконки — Stud-UI (CheckUIIcons), цвета счётчиков — по редкости этажа, обводка — тёмный оттенок того же цвета.
UITokens.TowerBadge = {
	Size = Vector2.new(260, 82),
	MaxDistance = 400,
	Lift = 16,
	-- вблизи значок съезжает по оси башни вниз, чтобы оставаться в кадре: не выше этого угла над взглядом по
	-- горизонту (градусы) и не ниже MinHeight стадов над землёй; издалека он над башней
	MaxElevation = 24,
	MinHeight = 26,
	-- дальше FullDistance стадов по земле значок уменьшается (до MinScale), чтобы значки соседних башен не слипались
	FullDistance = 170,
	MinScale = 0.5,
	NameSize = 28,
	NameStroke = Color3.fromHex("1E2433"),
	CountSize = 26,
	CountWidth = 40,
	Icon = 34,
	Gap = 8,
	Rarity = {
		Gold = {
			icon = "Currency/Diamond/Golden Diamond 1st Outline",
			color = Color3.fromHex("FFD23F"),
			stroke = Color3.fromHex("3A2602"),
		},
		Mythic = {
			icon = "Currency/Diamond/Purple Diamond 1st Outline",
			color = Color3.fromHex("D9B8FF"),
			stroke = Color3.fromHex("22093F"),
		},
		Diamond = {
			icon = "Currency/Diamond/Blue Diamond 1st Outline",
			color = Color3.fromHex("BFF2FF"),
			stroke = Color3.fromHex("062A3A"),
		},
	},
}

-- Обводка живых существ у боссов (визуальный QA босса 3): тонкий светлый контур, чтобы силуэт не сливался с
-- подушкой и ковром (красные существа на красном бархате). Только контур (заливки нет), сквозь стены не виден.
UITokens.CreatureOutline = {
	Color = Color3.fromHex("FFF4D6"),
	Transparency = 0.55, -- контур полупрозрачный — ненавязчивый
	Distance = 45, -- стадов от камеры
	Max = 8, -- не больше столько ближайших (у Roblox предел — 31 обводка на кадр)
	Every = 0.25, -- секунд между выборами существ с обводкой
}

-- Подпись над предметом (D45): две строки — название цветом редкости и «Редкость · +доход/сек». Ширина — по длине
-- названия, пиксели — при масштабе 1 (экран высотой ScreenHeight); на экране подписи не накладываются: дальние
-- поднимаются над ближними (Controllers/ItemLabelController, Shared/LabelLayout).
UITokens.ItemLabel = {
	Height = 46, -- px
	CharWidth = 13, -- px на букву названия
	Padding = 30, -- px по бокам вместе
	MinWidth = 130,
	MaxWidth = 320,
	NameShare = 0.62, -- доля высоты под название
	NameTextSize = Vector2.new(12, 30), -- мин. и макс. размер текста названия
	InfoTextSize = Vector2.new(10, 19),
	Income = Color3.fromHex("5BEA72"), -- доход — как надпись «+X/сек» над экспонатом
	MaxDistance = 60, -- стадов: дальше подпись не рисуется
	Gap = 1.2, -- стадов между верхом предмета и подписью
	StackGap = 4, -- px между подписями, поднятыми друг над другом
	MaxStack = 4, -- подъём не выше 4 высот подписи: по одной на каждый из 4 слотов босса
	ScreenHeight = 720, -- высота экрана (px), при которой масштаб 1
	Scale = Vector2.new(0.6, 1.1), -- пределы масштаба по высоте экрана: телефон — 0.6
	Update = 0.1, -- секунд между раскладками
	-- Визуальный QA босса 3: фигура босса перед подписью — препятствие (подпись поднимается над ней не выше BossLift
	-- высот подписи, иначе плавно гаснет); «Z z z» — неподвижное препятствие; таймер вверху и плашка зоны — запретные
	-- зоны (подпись гаснет); подпись экспоната, которую закрывает стена или колонна музея, гаснет целиком.
	BossLift = 5, -- высот подписи
	BossGap = 6, -- px между подписью и верхом фигуры босса
	ZoneMargin = 6, -- px вокруг таймера и плашки зоны
	FadeSpeed = 8, -- скорость появления и угасания (доля в секунду)
	BossRange = 120, -- стадов: дальше фигуры боссов препятствиями не считаются
	-- «Z z z» (BossAnimController): поднимается от 4.5 до 6.5 стада над головой и качается на ±0.6 — препятствие
	-- занимает весь этот путь, чтобы подписи над ним не прыгали
	ZzzRise = Vector2.new(4.5, 6.5),
	ZzzSway = 0.6,
	WallEvery = 0.3, -- секунд: как долго помнится, закрыта ли подпись экспоната стеной музея
	WallPerLayout = 8, -- не больше столько таких проверок за раскладку (без всплесков на телефоне)
	Follow = 12, -- скорость, с которой подпись догоняет своё место (1/с)
}

-- Иконки HUD (Client/UI/HudIcons). Значение — путь CheckUIIcons «Категория/Подкатегория/Имя» или готовый
-- "rbxassetid://<id>"; таблица { glyph = … } — плоский силуэт: интерфейс рисует его белым с чёрной обводкой
-- (Shared/StudUI — UI.Glyph), как значки на кнопках референса владельца (2026-11-17).
-- Силуэты — «… White» из CheckUIIcons (проверены в Studio) и три своих плоских рисунка (scripts/hud_glyphs.py,
-- assets/ui/hud/glyph_*_256.png, ID — assets/ui/hud/IDS.md): музей, солнце, луна с облаком.
-- Монеты и сила — цветные 2D-наклейки CheckUIIcons с тёмным контуром (как наклейки у чисел на референсе).
UITokens.HudIcons = {
	Coins = "Currency/Coin/Golden Coin 1st Outline",
	Strength = "Player/Arm/Arm 1st Outline",
	Inventory = { glyph = "Item/Backpack/Backpack White" },
	Defense = { glyph = "Item/Shield/Shield White" },
	Shop = { glyph = "Main/Shopping Cart/Shopping Cart White" }, -- «Магазин» Ловибумов (D55)
	Museum = { glyph = "rbxassetid://107254124592158" }, -- кнопка меню и шапка окна «Улучшение музея» (D56)
	OwnerTest = { glyph = "Main/Settings/Settings White" }, -- кнопка «Тест» владельца
	Day = { glyph = "rbxassetid://101917311109817" },
	Preparation = { glyph = "Item/Clock/Clock White" },
	Night = { glyph = "rbxassetid://89574346976067" },
	DoomNight = { glyph = "Player/Skull/Skull White" },
	-- окно «Улучшение музея»: музей следующего уровня; стрелка «станет», замок запрета, кубок максимума
	MuseumNext = { glyph = "rbxassetid://107254124592158" },
	Upgrade = "Main/Upgrade/Golden Upgrade 1st Outline",
	Lock = "Item/Lock/Lock 1st Outline",
	Trophy = "Item/Trophy/Golden Trophy 1st Outline",
	Lovibum = "Currency/Crystal/Crystal Blue Outline", -- раздел «Ловибумы» в инвентаре: кристалл — знак Ловибумов
}

-- Камера в музее (D50, Controllers/MuseumCameraController): детали здания между персонажем и камерой гаснут у этого
-- игрока — камера не прижимается к голове в узких галереях.
UITokens.MuseumCamera = {
	Fade = 0.75, -- LocalTransparencyModifier закрывающей детали (≥ 0.25 — камера Roblox её не считает преградой)
	ReturnSpeed = 10, -- как быстро деталь возвращается, когда перестала закрывать (доля в секунду)
	Probe = 0.6, -- толщина отрезка «фокус → камера»: столько вокруг линии взгляда тоже гаснет (стадов)
	FallbackDistance = 12, -- расстояние камеры, если модуль камеры Roblox не отдал выбранное игроком
	Margin = 1, -- запас к объёму музея (стадов)
	FloorTolerance = 0.3, -- детали с верхом ниже ног + столько (пол, ступени) не гаснут (стадов)
	-- С ношей (босс 3, визуальный QA): гаснут и детали, что закрывают ношу от камеры или проходят сквозь неё (низкая
	-- крыша галереи); в галереях камера не дальше CarryGalleryZoom, на выходе — снова выбранное игроком расстояние.
	CarryGalleryZoom = 9, -- стадов
	CarryRescan = 0.5, -- секунд между поисками ноши, пока сварка с персонажем ещё не пришла
	-- Экспонаты рядом (D55): гаснут и стены и постаменты между камерой и ближайшими экспонатами в той же части музея
	-- (зал или галерея), что и персонаж, — не дальше ExhibitRadius от него, не больше ExhibitMax, только в кадре.
	ExhibitRadius = 10, -- стадов
	ExhibitMax = 4,
	-- Камера не заходит внутрь места (тумба и экспонат над ней): её подтягивает к персонажу до края места минус
	-- ColumnMargin (сразу), обратно отпускает со скоростью ColumnRelease стадов в секунду.
	ColumnMargin = 0.3,
	ColumnRelease = 24,
	NearCamera = 1.5, -- детали музея и экспонаты ближе этого к камере гаснут (не заслоняют кадр вплотную), стадов
	-- камера в другой части музея, чем персонаж (за стеной галереи — в зале и наоборот): экспонаты и постаменты той
	-- части ближе OtherRoomRadius к камере гаснут — передний план чужой комнаты не загромождает кадр
	OtherRoomRadius = 9,
}

-- Тренировка с гантелью в руке (D51, Controllers/TrainingController): подъём к бицепсу и опускание — процедурно (D18).
UITokens.Training = {
	Blend = 0.25, -- секунд на плавное включение и выключение позы
	-- доли такта (один подъём за GameConfig.Gym.TickSeconds): задержка вверху (в начале такта — начисление силы),
	-- опускание, задержка внизу; остальное — подъём
	Curve = { Top = 0.08, Down = 0.5, Bottom = 0.06 },
	-- R15: углы сгибания (градусы) внизу и вверху; кисть и откид корпуса — вверху
	R15 = { ShoulderRest = 6, ShoulderTop = 20, ElbowRest = 14, ElbowTop = 122, Wrist = 14, Lean = 4 },
	R6 = { Rest = 8, Top = 100 }, -- R6 без локтя: подъём прямой руки вперёд
}

-- Меню HUD (вид — по референсу владельца 2026-11-17): слева посередине — столбик квадратных плоских кнопок только
-- со значком, без подписей (решение владельца: подписи занимают лишнее место на экране) — как квадратные кнопки
-- референса: яркая заливка, тонкий тёмный контур, светлая рамка внутри, по центру белый значок с чёрной обводкой.
-- Цвета — с референса: «Магазин» зелёный, «Инвентарь» голубой, «Музей» оранжевый, «Защита» красная. Квадратная
-- кнопка референса — 34 × 36 px при экране 880 × 405. Столбик стоит между кнопками Roblox (или панелью обучения)
-- сверху и монетами снизу (Client/UI/HudLayout).
UITokens.MenuHud = {
	Button = Vector2.new(48, 48), -- px при масштабе 1 (масштаб HUD — Client/UI/HudLayout.Scale); телефон — 41 × 41
	Text = 15, -- подпись рисуется, только если у кнопки нет значка
	IconSize = 0.68, -- доля стороны кнопки
	Gap = 6, -- между кнопками
	Margin = 12, -- от левого края (безопасной зоны экрана)
	KeySize = 18, -- значок клавиши на ПК
	Hover = 1.06,
	Themes = { Shop = "green", Inventaire = "blue", Museum = "orange", Defense = "red", OwnerTest = "teal" },
	Order = { Shop = 1, Inventaire = 2, Museum = 3, Defense = 4, OwnerTest = 9 },
	EdgeGap = 8, -- px экрана: от столбика до кнопок Roblox сверху и до монет снизу
}

-- Ноша (Controllers/CarryController; вид — по референсу владельца 2026-11-17): у нижнего края по центру — тёмный
-- полупрозрачный скруглённый слот с 3D-видом предмета (как слоты инструментов на референсе), правее — название
-- и красная плоская кнопка «Бросить». Px при масштабе 1 (масштаб HUD — Client/UI/HudLayout.Scale).
UITokens.CarryHud = {
	Slot = 64, -- сторона слота (на референсе 59 px при экране 880 × 405)
	Side = 176, -- ширина колонки справа: название (во всю ширину) и кнопка (слева)
	Button = Vector2.new(132, 40), -- «Бросить»
	ButtonText = 19,
	Gap = 8, -- между слотом и колонкой
	Bottom = 6, -- px от нижнего края
	BandGap = 10, -- px экрана: до монет слева и таймера справа
	NameText = 16, -- название предмета (цветом редкости)
	MinText = 10,
	KeySize = 20, -- значок клавиши G на ПК
	Turn = 25, -- поворот предмета в слоте вокруг вертикали, градусов
	PreviewWait = 0.25, -- секунд между попытками собрать вид ноши, пока её сварка с персонажем не пришла
	PreviewTries = 12,
	-- самый узкий телефон: блок не помещается между монетами и таймером хотя бы в MinFull от масштаба HUD —
	-- слот убирается, остаются название и кнопка «Бросить»
	MinFull = 0.8,
}

-- Панель действий тестового режима владельца (Controllers/OwnerTestController): правее столбика меню, видна только
-- владельцу в DEV-месте. id — действие для сервера (Services/OwnerTestService).
UITokens.OwnerTest = {
	Button = Vector2.new(170, 40), -- px при масштабе 1 (масштаб HUD)
	Text = 16,
	Gap = 6,
	Pad = 10,
	Left = 10, -- px от столбика меню
	Columns = 2,
	Actions = {
		Normal = { { id = "Test", text = "На тестовый сервер", theme = "teal" } },
		Test = {
			{ id = "Goto", text = "К дракону", theme = "blue" },
			{ id = "Fight", text = "Бой", theme = "red" },
			{ id = "Win", text = "Победа", theme = "green" },
			{ id = "Day", text = "День", theme = "orange" },
			{ id = "Night", text = "Ночь", theme = "purple" },
			{ id = "Exit", text = "Выход", theme = "gray" },
		},
	},
}

-- Общее для HUD v3 (Client/UI/HudLayout): масштаб и зоны экрана.
UITokens.Hud = {
	-- опорный экран и нижний предел масштаба — как у окон (StudMotion.REFERENCE, MIN_SCALE); верхний предел выше,
	-- чем у окон (1.18): на мониторе 1920 × 1080 и больше кнопки HUD не должны быть крошечными (там кнопка меню —
	-- 63 px в высоту, на 1280 × 720 — 49 px)
	Reference = Vector2.new(1050, 620),
	MinScale = 0.52,
	MaxScale = 1.5,
	TouchScale = 0.85, -- на касании масштаб кнопок HUD не меньше: кнопки меню не мельче ~40 px
	-- на касании масштаб надписей без нажатия (монеты, сила, таймер) не меньше: на узком телефоне они не должны
	-- занимать весь нижний край (между ними встаёт «Бросить»)
	InfoTouchScale = 0.72,
	TopBar = 58, -- px: кнопки Roblox сверху (GuiService:GetGuiInset бывает 0 в первые кадры)
	-- кнопка прыжка Roblox (PlayerModule/TouchJump): на экране с меньшей стороной ≤ SmallSide — 70 px у края,
	-- иначе 120 px выше; Left — от правого края до левого края кнопки, Top — от низа до её верха, с запасом
	SmallSide = 500,
	JumpSmall = { Left = 103, Top = 96 },
	Jump = { Left = 178, Top = 216 },
	JumpLow = 150, -- кнопка прыжка ниже этого (px от низа до её верха) — таймер встаёт левее неё, а не под ней
}

-- Окно «Улучшение музея» (D56, Stud-UI: золотая шапка — рост и награда). Слева карточка «Сейчас», справа — «После
-- улучшения» (уровень, мест, устройств защиты), между ними стрелка; ниже полоса из 20 мест (открытые, новые,
-- закрытые), цена, состояние и кнопка «Улучшить». Окно — по экрану, как «Магазин»: наибольшее Window, на маленьком
-- экране — по экрану без Margin, не меньше MinWindow; на касании масштаб не меньше PhoneScale, кнопка не ниже MinTouch
-- px. Окно ниже CompactHeight — тесная раскладка (телефон): отступы и шрифты меньше.
UITokens.MuseumUpgrade = {
	Window = Vector2.new(820, 480),
	MinWindow = Vector2.new(640, 360),
	Margin = 16,
	PhoneScale = 0.78,
	MinTouch = 52,
	Header = "orange", -- как кнопка «Музей»
	Pad = 16,
	PadCompact = 10,
	Gap = 12,
	GapCompact = 8,
	CompactHeight = 430,
	Arrow = 76, -- стрелка между карточками (наклейка, заходит на обе)
	Tilt = 0, -- наклон иконок: на референсе владельца значки стоят прямо
	IconGap = 8, -- от заголовка «Уровень N» до иконки карточки
	ArrowCompact = 56,
	CaptionText = 20, -- «Сейчас» / «После улучшения»
	LevelText = 54, -- «Уровень 4»
	LevelCompact = 38,
	LineText = 23, -- «Мест: 8», «Защита: до 4 устройств»
	LineCompact = 18,
	Pip = 24, -- квадратик места в полосе
	PipCompact = 18,
	PipGap = 6,
	PipOpen = Color3.fromHex("5AC8FF"), -- место открыто
	PipNew = Color3.fromHex("B4FF19"), -- откроется после улучшения
	PipClosed = Color3.fromHex("232833"), -- закрыто
	PipsLabel = 150, -- ширина подписи слева от полосы
	Button = Vector2.new(260, 66), -- «Улучшить» (на касании — не ниже MinTouch px экрана)
	ButtonCompact = Vector2.new(220, 56),
	PriceText = 30,
	PriceCompact = 24,
	StatusText = 20,
	StatusCompact = 17,
	MinText = 13, -- мельче текст не сжимается
	Current = Color3.fromHex("9FE3FF"), -- подпись карточки «Сейчас»
	Next = Color3.fromHex("B4FF19"), -- подпись карточки «После улучшения» и прибавки
	Max = Color3.fromHex("FFD23F"), -- максимальный уровень
	Warn = Color3.fromHex("FFD23F"), -- временный запрет
	Wait = 1.5, -- секунд: после «Улучшить» ждём ответа сервера, повторное нажатие не шлём
	MessageTime = 4, -- секунд: сколько показывается ответ сервера об отказе
	Refresh = 0.25, -- секунд: как часто обновляется отсчёт запрета, пока окно открыто
}

-- Статистика (вид — по референсу владельца 2026-11-17): слева внизу — сила и монеты, цветная 2D-наклейка и число
-- жирным курсивом с чёрной обводкой; сила белая, монеты ярко-зелёные (цвет с референса). Без рамок. Дохода в секунду
-- здесь нет: он в стандартном списке игроков Roblox (leaderstats «Доход/сек», IncomeService).
UITokens.StatsHud = {
	Margin = Vector2.new(12, 6), -- от левого и нижнего края
	Rows = {
		Strength = { icon = 38, text = 29 },
		Coins = { icon = 38, text = 29, color = Color3.fromHex("19FA00") },
	},
	Gap = 1,
	TextGap = 5,
}

-- Окно «Инвентарь» (D46, Stud-UI): пиксели опорного экрана 1050 × 620, весь корень масштабирует WindowScale
-- (StudMotion: телефон 844 × 390 → × 0.63, поэтому текст не меньше 19 px).
UITokens.Inventory = {
	-- Окно (px опорного экрана 1050 × 620, масштаб — StudMotion): наибольший размер; на маленьком экране — по экрану
	-- без Margin по краям и ниже кнопок Roblox, но не меньше MinWindow.
	Window = Vector2.new(1060, 640),
	MinWindow = Vector2.new(720, 380),
	Margin = 16, -- px экрана
	PhoneScale = 0.78, -- на сенсорном экране без клавиатуры масштаб окна не меньше (текст читается)
	MinTouch = 52, -- px: кнопки на сенсорном экране не меньше (D32)
	Header = "blue", -- как кнопка «Инвентарь»
	-- Карточка D50: наименьшая ширина (сетка растягивает до строки), высота без кнопки — CardBody.
	Card = Vector2.new(178, 0),
	CardBody = 228, -- отступ, редкость, превью, название (2 строки), доход и локация, статус, отступы
	CardPad = 10,
	CardCorner = 8,
	CardStroke = 2, -- рамка цвета редкости
	CardColor = Color3.fromHex("000000"), -- тёмная полупрозрачная плашка, как слоты на референсе владельца
	CardTransparency = 0.4,
	CardNeutral = Color3.fromHex("6A7280"), -- рамка карточки без редкости (занятый постамент)
	Muted = Color3.fromHex("B8C3D6"), -- второстепенный текст
	Preview = 86, -- высота 3D-превью
	PreviewGlow = 0.55, -- прозрачность фона цвета редкости вверху превью (книзу — почти прозрачный)
	Pedestal = Vector2.new(178, 104), -- карточка постамента в выборе места (высота без кнопки)
	CompactBelow = 520, -- окно ниже (px опорного экрана) — карточки-строки (телефон)
	-- строка (телефон): высота, ширина кнопки, наименьшая ширина; поиск в строке «чипов»; место в шапке под название
	-- (слева) и под крестик (справа) — между ними счётчики
	Row = { Height = 96, Button = 150, MinWidth = 430, Search = 240, TitleSpace = 300, CloseSpace = 90 },
	LovibumRow = 84, -- раздел «Ловибумы» (D55): высота строки уровня и наименьшая ширина
	LovibumMin = 300,
	Gap = 12,
	GridPad = 14,
	BarHeight = 44, -- строка счётчиков и поиска
	SearchWidth = 300,
	StatsText = 21,
	SearchText = 20,
	NameText = 20,
	IncomeText = 18,
	InfoText = 15,
	MinText = 12,
	ButtonHeight = 36,
	ButtonText = 19,
	-- сортировка и фильтр (D50): плоские плашки в стиле референса владельца — выбранная голубая с тёмным контуром
	-- (цвет кнопки «Инвентарь»), остальные тёмные полупрозрачные; подпись белая с чёрной обводкой
	Chip = {
		Height = 34,
		Text = 17,
		TouchText = 22, -- на касании плашка высотой с кнопку (D32), текст крупнее
		Pad = 14,
		Gap = 8,
		Corner = 5,
		Active = Color3.fromHex("01C8FF"),
		ActiveStroke = Color3.fromHex("001A43"),
		Idle = Color3.fromHex("000000"),
		IdleTransparency = 0.45,
		IdleStroke = Color3.fromHex("6A7280"), -- черта между сортировкой и фильтром
	},
	HotKey = Enum.KeyCode.B, -- ПК: открыть / закрыть (I и O — зум камеры Roblox)
	Refresh = 0.5, -- секунд между проверками фазы, пока окно открыто
	SearchDelay = 0.2, -- поиск: перерисовать после паузы в наборе
	Turn = 25, -- поворот превью вокруг вертикали, градусов
}

-- Окно «Защита» и расстановка (D46, Stud-UI): пиксели опорного экрана 1050 × 620.
UITokens.Defense = {
	Window = Vector2.new(940, 580),
	-- окно — по экрану: ширина постоянная (строки устройств), высота — сколько помещается ниже кнопок Roblox без
	-- Margin по краям, не меньше MinHeight (список прокручивается); на касании масштаб не меньше PhoneScale
	MinHeight = 300,
	Margin = 16,
	PhoneScale = 0.78,
	Header = "red", -- как кнопка «Защита»
	Row = Vector2.new(880, 92), -- строка устройства
	TextWidth = 380, -- колонка названия и подробностей; правее — кнопки (до 3 × 150 + промежутки)
	RowGap = 10,
	NameText = 26,
	InfoText = 20,
	-- строка «Прежние уровни музея» (D56): устройства, которые на музей нынешнего уровня не ставятся
	StaleColor = Color3.fromHex("FFD23F"),
	StaleMinText = 14, -- длинный список уровней сжимается не мельче этого
	Button = Vector2.new(150, 52),
	Bar = Vector2.new(560, 120), -- панель расстановки внизу экрана
	Ghost = {
		Trap = Vector3.new(2.4, 0.6, 2.4),
		Robot = Vector3.new(2.4, 5.8, 1.8),
		Snare = Vector3.new(1.9, 0.6, 1.9),
	},
	GhostOk = Color3.fromHex("5BEA72"),
	GhostBad = Color3.fromHex("FF5A5A"),
	GhostTransparency = 0.45,
	SpotNames = { Entrance = "вход", Gallery = "галерея" }, -- в строке «стоит: …»
	SpotButtons = { Entrance = "Вход", Gallery = "Галерея" }, -- на кнопках мест лазера
	RobotBar = { -- полоска HP робота-охранника (BillboardGui, стады)
		Size = Vector2.new(3, 0.4),
		Lift = 2.4,
		MaxDistance = 60,
		Back = Color3.fromHex("1E1E24"),
		Fill = Color3.fromHex("5BEA72"),
	},
}

-- Магазин Ловибумов (D55, Stud-UI: красная шапка — магазин). Окно — по экрану, как «Инвентарь»: наибольшее Window,
-- на маленьком экране — по экрану без Margin, не меньше MinWindow; на касании масштаб не меньше PhoneScale, кнопки не
-- ниже MinTouch px. Сверху — уровни 1–10 (Ловибум уровня N — только для существ босса N), ниже три карточки: Бум,
-- Турбо, Мега — 3D-модель, бонус, запас, цена набора, наклейка «×3» (одна покупка — 3 штуки, D61) и «Купить».
UITokens.Shop = {
	Window = Vector2.new(980, 600),
	MinWindow = Vector2.new(700, 380),
	Margin = 16,
	PhoneScale = 0.78,
	MinTouch = 52,
	Header = "green", -- как кнопка «Магазин»
	Pad = 14,
	PadCompact = 8, -- внутри карточки телефона
	Gap = 12, -- между карточками
	CompactHeight = 470, -- окно ниже — раскладка телефона (и если карточка ПК не вмещает строку покупки даже с узким числом)
	Tab = Vector2.new(0, 50), -- вкладка уровня: ширина — по окну (10 в ряд), высота
	Button = 52, -- высота кнопок (на касании — не меньше MinTouch / масштаб)
	Pack = 58, -- ширина наклейки «×3» перед «Купить»
	PackText = 32,
	PackColor = Color3.fromHex("FFD23F"), -- жёлтая наклейка (Stud-UI: акцент)
	PackTilt = 0, -- градусов: на референсе владельца значки стоят прямо
	Buy = 150, -- ширина «Купить» (строка телефона)
	BuyMin = 96, -- «Купить» в карточке ПК не уже
	BarText = 24, -- итог в строке телефона
	NameText = 30,
	NameCompact = 24, -- название вида в карточке телефона
	InfoText = 19,
	SmallText = 16,
	Turn = 0.35, -- оборотов превью в секунду
	CardTop = { Boom = "amber", Turbo = "cyan", Mega = "violet" }, -- градиент полоски карточки (UI.StudPanel)
	KindColor = { Boom = Color3.fromHex("FFC21A"), Turbo = Color3.fromHex("5AC8FF"), Mega = Color3.fromHex("C482FF") },
	BuyWait = 1.5, -- секунд: после «Купить» ждём ответа сервера, повторное нажатие не шлём
}

-- Мини-игра поимки «Ловибум» (D55, от первого лица): кольца вокруг существа, 3D-Ловибум внизу по центру (берут и
-- смахивают вверх), справа внизу — выбор вида (запас каждого), слева вверху — «Уйти», вверху — имя, шанс, броски.
-- Кнопки и подписи — px опорного экрана (масштаб — StudMotion); Ловибум — доля высоты экрана.
UITokens.Catch = {
	KindButton = Vector2.new(112, 96), -- карточка вида: превью и запас
	KindGap = 12,
	Margin = 16,
	Leave = Vector2.new(150, 56),
	MinTouch = 52, -- px: «Уйти» на сенсорном экране не ниже (D32)
	TouchText = 0.8, -- плашка и подсказка на касании не мельче (масштаб): текст ≥ 14 pt на телефоне
	Panel = Vector2.new(440, 66), -- плашка вверху: имя; редкость, шанс, броски
	PanelTop = 8, -- от верха экрана (поверх середины полосы Roblox)
	PanelPad = 6,
	PanelTransparency = 0.18,
	TitleText = 26,
	TitleLong = 22, -- имя длиннее LongName букв
	LongName = 24,
	InfoText = 18,
	HintText = 18, -- подсказка слева от Ловибума
	HintHeight = 32,
	HintGap = 14,
	Ball = 0.22, -- Ловибум внизу: диаметр — доля высоты экрана (мышь)
	BallTouch = 0.27, -- на касании — крупнее (под палец)
	BallFit = 0.72, -- насколько плотно модель вписана в этот круг (меньше — крупнее)
	BallMin = 72, -- и не меньше, px
	BallDepth = 2.2, -- откуда начинается полёт: столько стадов от камеры
	BallSpin = 0.9, -- лежит и поворачивается, радиан в секунду
	Bob = 0.05, -- покачивание (доля радиуса)
	BobSpeed = 2.2,
	Grab = 1.6, -- жест начинается не дальше радиус × Grab от Ловибума (мышь)
	GrabTouch = 1.8, -- палец
	Pending = 1.5, -- после броска Ловибум внизу появится, когда сервер ответит (или через столько секунд)
	NoteTime = 1.8, -- подсказка «смахните быстрее» и т. п.
	-- кольца: цветная линия поверх тёмного контура, у цветного — лёгкая заливка (куда бросать)
	OuterRing = Color3.fromHex("FFFFFF"), -- белое кольцо: наибольший размер
	OuterThickness = 3,
	OuterTransparency = 0.2,
	RingThickness = 6,
	RingEdge = 2, -- тёмный контур с каждой стороны линии, px
	RingDark = Color3.fromHex("0B0E14"),
	RingDarkTransparency = 0.35,
	RingFill = 0.88, -- прозрачность заливки цветного кольца (существо не тонируется)
	WaitTransparency = 0.8, -- пока Ловибум летит и качается
	-- цвет сжимающегося кольца — базовая сложность захвата выбранным видом (шанс без учёта кольца)
	Difficulty = {
		{ at = 0.6, color = Color3.fromHex("5BEA72") }, -- легко
		{ at = 0.35, color = Color3.fromHex("FFD23F") },
		{ at = 0.15, color = Color3.fromHex("FF9A2E") },
		{ at = 0, color = Color3.fromHex("FF4D4D") }, -- трудно
	},
	-- фон спокойнее: края притемнены (доля экрана; Edge — прозрачность чёрного у самого края: 0.5 — затемнение 50 %,
	-- в углах полосы складываются), дальний план размыт
	Vignette = { Side = 0.24, Top = 0.2, Edge = 0.5 },
	Focus = { Radius = 5, Far = 0.75 }, -- DepthOfField: в фокусе ± Radius стадов от существа
}

-- PvP Судной ночи (D46): кнопка «Удар» (телефон и мышь), звёзды нокаута, числа урона.
-- Вид музея D48-C у владельца (Controllers/MuseumVisualController): экран сканера у павильона хранилища.
-- Обучение новичка (D55): панель задачи сверху по центру, жёлтая линия к цели и метка над ней.
UITokens.Tutorial = {
	Panel = Vector2.new(460, 116),
	-- слева сверху под кнопками Roblox (CoreUISafeInsets): выше столбика монет и силы, левее таймера дня, не заслоняет
	-- плашку «Ты несёшь…» внизу; во время поимки панели нет
	Left = 16,
	Top = 8,
	Gap = 8, -- от низа панели до столбика монет и силы, если его пришлось опустить (низкий экран телефона)
	TitleText = 22,
	BodyText = 22,
	MinText = 14,
	BodyTop = 34, -- текст шага: от верха панели (под заголовком)
	BodyPad = Vector2.new(28, 6), -- поля текста: по ширине всего, снизу
	Guide = Color3.fromHex("FFD23F"),
	GuideWidth = 0.35,
	GuideTransparency = 0.25,
	Marker = 56,
}

UITokens.Museum = {
	ScannerOwner = Color3.fromHex("4CE07A"), -- свой музей: проход открыт
	ScannerIdle = Color3.fromHex("39E1FF"), -- чужой: решётка закрыта
}

UITokens.Pvp = {
	Button = Vector2.new(150, 72), -- кнопка «Удар» (px опорного экрана, масштаб — StudMotion)
	MinTouch = 52, -- px: на телефоне кнопка не ниже (D32) — масштаб не меньше MinTouch / Button.Y
	-- HUD v3: у правого края над кнопкой прыжка (UI/HudLayout.Jump); только телефон и только в Судную ночь
	Right = 22, -- px от правого края
	JumpGap = 8, -- px между верхом зоны прыжка и кнопкой
	Stars = Vector2.new(4, 1.4), -- звёзды над головой оглушённого, стадов
	StarsLift = 2.6,
	StarColor = Color3.fromHex("FFD23F"),
	StarSpin = 120, -- градусов в секунду
	Damage = Vector2.new(4, 1.6), -- всплывающее «-12», стадов
	DamageColor = Color3.fromHex("FF7A7A"),
	KnockColor = Color3.fromHex("FFD23F"),
	DamageRise = 2.5,
	DamageTime = 0.7,
	Flash = 0.15, -- вспышка цели, секунд
	Swing = 0.22, -- замах руки, секунд
	SwingAngle = 110, -- градусов
	Shake = 0.35, -- тряска камеры у того, по кому попали (стадов)
	ShakeTime = 0.18, -- секунд
	-- камера лежащего в нокауте: смотрит на точку над телом (стадов над корнем), не ближе MinZoom
	KnockCamera = { Height = 3, MinZoom = 8 },
}

-- Бросок вдаль (D75): строго по записи референса владельца (2026-11-28). Размеры и места — в пикселях кадра
-- 960 × 540 этой записи (UI/ThrowHud пересчитывает их по высоте экрана); At — доли экрана.
UITokens.Throw = {
	Order = 60, -- DisplayOrder: поверх остального интерфейса
	Scale = {
		At = Vector2.new(0.5, 0.45), -- центр шкалы
		Size = Vector2.new(70, 310),
		Stroke = 5,
		Marker = Vector2.new(86, 16),
		MarkerFill = Color3.fromHex("F4F4F4"),
		MarkerEdge = Color3.fromHex("5A5A5A"),
		Ticks = 5,
		Top = Color3.fromHex("9AD98A"), -- сверху вниз: светло-зелёный, жёлто-зелёный, оранжевый, красный
		High = Color3.fromHex("C2DD80"),
		Mid = Color3.fromHex("F0BE78"),
		Low = Color3.fromHex("E8533C"),
		Value = 26, -- число у бегунка
		ValueGap = 18, -- от бегунка до числа
		Caption = 26, -- «Нажмите, чтобы бросить!»
		CaptionGap = 37, -- от низа шкалы до середины подписи
		Power = 28, -- «+N Мощность»
		PowerShift = 20, -- левый край — от оси шкалы
		Perfect = 30, -- «Идеально!»
	},
	Bars = 0.107, -- чёрные поля кино, доля высоты экрана каждое
	Flight = {
		Plate = Vector2.new(304, 72),
		PlateTop = 10,
		PlateAlpha = 0.85, -- прозрачность светлой плашки
		Luck = 40,
		LuckAt = 36,
		Word = 14,
		WordAt = 72,
		Band = Color3.fromHex("14324A"),
		BandAlpha = 0.45,
		BandTop = 96,
		BandHeight = 40,
		BandWidth = 0.62, -- доля ширины экрана, края тают
		Zone = 26,
	},
	Reveal = {
		OneIn = 30,
		OneInAt = 87,
		Lucky = 26,
		LuckyAt = 33,
		Rays = Color3.fromHex("FF4458"),
		RaysSize = 190,
		Name = 30,
		NameAt = 448,
	},
	Card = {
		Rarity = 18,
		RarityAt = 410,
		Name = 26,
		NameAt = 450,
		Income = 24,
		IncomeAt = 492,
		NameColor = Color3.fromHex("F2EFA0"),
		IncomeColor = Color3.fromHex("E6F08C"),
		Tag = Vector2.new(100, 40),
		TagShift = 190, -- от середины экрана вправо
		TagAt = 430,
		TagTurn = -12,
		TagFill = Color3.fromHex("F2A640"),
		TagEdge = Color3.fromHex("3A2408"),
		TagText = 18,
	},
	-- Панель выбора вида Ловибума у края обрыва (решение владельца 2026-11-28; в записи референса её нет):
	-- три плашки внизу по центру, выбранная — зелёная.
	Kinds = {
		Size = Vector2.new(124, 34),
		Gap = 8,
		Bottom = 64, -- от низа экрана до середины плашек
		Text = 16,
		Fill = Color3.fromHex("1B1530"),
		Alpha = 0.3,
		On = Color3.fromHex("2FBF4A"),
		Empty = Color3.fromHex("8E98A8"), -- текст вида, которого нет в запасе
	},
	Flash = Color3.fromHex("FFFFFF"),
	Dip = Color3.fromHex("05070C"),
}

-- Основной цвет редкости (для подписи над предметом и т. п.).
function UITokens.RarityColor(rarity: string): Color3
	local g = UITokens.Rarity[rarity] or UITokens.Rarity.Common
	return g.bottom -- насыщенный край: им светят прожектор и подсветка
end

function UITokens.ToColorSequence(g: Gradient): ColorSequence
	return ColorSequence.new(g.top, g.bottom)
end

return UITokens

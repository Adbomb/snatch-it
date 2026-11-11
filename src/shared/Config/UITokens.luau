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
		-- справа, левее колонки меню HUD v2 и ниже таймера (D49: не перекрываются; Client/UI/HudLayout): зазоры до
		-- колонки меню и до низа таймера
		menuGap = 12,
		timerGap = 10,
		size = UDim2.fromScale(0.26, 0.5),
		minWidth = 180, -- на телефоне шире не помещается: справа колонка меню, по центру плашка «Бросить»
		maxWidth = 360,
		itemHeight = 56,
		lifetime = 4, -- секунды
		maxCount = 4, -- не больше, чем помещается в высоту колонки (на телефоне — 2)
		displayOrder = 14, -- поверх окон «Инвентарь» и «Защита» (12) и расстановки защиты (13), под плашкой зоны (30)
		windowCheck = 0.25, -- секунд между проверками, открыто ли окно меню (колонка — справа от окна)
	},
	-- «Бросить»: внизу по центру над плашкой «Ты несёшь…» (контекст HUD v2, D48 v2; справа — колонка меню, D49).
	DropButton = {
		-- низ кнопки — над верхом плашки CarryPill при любой высоте экрана: плашка не выше 60 px + зазор 8 px
		position = UDim2.new(0.5, 0, 0.86, -68),
		size = UDim2.fromScale(0.15, 0.1),
		aspect = 2.6,
		minSize = Vector2.new(52 * 2.6, 52),
		maxSize = Vector2.new(220, 84),
	},
	-- «Ты несёшь…»: внизу по центру, между джойстиком и прыжком.
	CarryPill = {
		position = UDim2.fromScale(0.5, 0.86),
		size = UDim2.fromScale(0.36, 0.07),
		minSize = Vector2.new(220, 44),
		maxSize = Vector2.new(460, 60),
		nameSize = UDim2.fromScale(0.68, 1), -- плашка с названием
		tagSize = UDim2.fromScale(0.3, 0.8), -- плашка редкости справа
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

-- Таймер фазы HUD v2 (D48 v2: сверху по центру, под кнопками Roblox — ScreenInsets CoreUISafeInsets): капсула с
-- иконкой фазы, названием и отсчётом, полоса фазы и строка «до Судной ночи».
UITokens.TimeHud = {
	Size = Vector2.new(300, 54), -- капсула, px при масштабе 1 (UIScale по экрану, StudMotion.BindResponsive)
	Top = 6,
	InfoGap = 16, -- отступы полосы и капсулы подписи (высота блока — Client/UI/HudLayout.TimerHeight)
	Icon = 40,
	PhaseSize = 22,
	TimeSize = 32,
	InfoSize = 18,
	InfoPill = { Transparency = 0.25, Pad = 8, Side = 12 }, -- тёмная капсула под подписью (D50: читается на любом фоне)
	Bar = Vector2.new(250, 8), -- полоса фазы под капсулой
	Refresh = 0.2, -- секунды между обновлениями отсчёта
	Fill = Color3.fromHex("1C2440"), -- капсула
	Stroke = {
		Day = Color3.fromHex("E9B43C"),
		Preparation = Color3.fromHex("FFB020"),
		Night = Color3.fromHex("8E7CFF"),
		DoomNight = Color3.fromHex("FF3B3B"),
	},
	PhaseColor = {
		Day = Color3.fromHex("FFD23F"),
		Preparation = Color3.fromHex("FFB020"),
		Night = Color3.fromHex("B9AEFF"),
		DoomNight = Color3.fromHex("FF7A7A"),
	},
	DoomFill = Color3.fromHex("4A0F1C"), -- капсула в Судную ночь
	-- Названия в капсуле прописными (string.upper кириллицу не меняет); номер дня не пишется (D51).
	Titles = {
		Day = "ДЕНЬ",
		Preparation = "ПОДГОТОВКА",
		Night = "НОЧЬ",
		DoomNight = "СУДНАЯ НОЧЬ",
	},
	Warning = 15, -- последние секунды фазы: отсчёт мигает цветом Danger
}

-- Плашка входа в уровень (D41): сверху по центру, 1.5 с, цвет — от спокойного зелёного к тревожному (по номеру зоны).
UITokens.LevelBanner = {
	Size = Vector2.new(380, 96), -- пиксели при масштабе 1 (UIScale по экрану, StudMotion.BindResponsive)
	Gap = 12, -- зазор под таймером-капсулой HUD v2 (Client/UI/HudLayout: низ таймера при текущем масштабе)
	Hold = 1.5, -- секунд на экране после появления
	In = 0.35,
	Out = 0.3,
	Emoji = 64, -- круг со смайликом
	TitleSize = 38,
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

-- Иконки HUD v2 (D48 v2, утверждено 2026-11-06): путь CheckUIIcons «Категория/Подкатегория/Имя» (проверенные иконки
-- Stud-UI) или готовый "rbxassetid://<id>". Новые иконки D48 (assets/concepts/d48/v2/icons: портфель, щит, монета,
-- доход, кулак силы) ещё не загружены — после разрешённой загрузки вписать их ID сюда, больше ничего менять не нужно.
UITokens.HudIcons = {
	Coins = "Currency/Coin/Golden Coin 1st Outline",
	Income = "Main/Upgrade/Green Upgrade 1st Outline",
	Strength = "Player/Arm/Arm 1st Outline", -- до загрузки кулака (готов: assets/ui/hud/icon_fist_256.png)
	Inventory = "Item/Backpack/Backpack 1st Outline", -- до загрузки портфеля (icon_briefcase.png)
	Defense = "Item/Shield/Shield 1st Outline",
	Shop = "Main/Shopping Cart/Red Shopping Cart 1st Outline", -- «Магазин» Ловибумов (D55): красный — магазин (Stud-UI)
	-- «Музей» (D56): кнопка меню и шапка окна «Улучшение музея»; стрелка «станет», замок запрета, кубок максимума
	Museum = "Main/House/Blue House 1st Outline",
	MuseumNext = "Main/House/Green House 1st Outline", -- музей следующего уровня в карточке «После улучшения»
	Upgrade = "Main/Upgrade/Golden Upgrade 1st Outline",
	Lock = "Item/Lock/Lock 1st Outline",
	Trophy = "Item/Trophy/Golden Trophy 1st Outline",
	Lovibum = "Currency/Crystal/Crystal Blue Outline", -- раздел «Ловибумы» в инвентаре: кристалл — знак Ловибумов
	Day = "Main/Star/Golden Star 1st Outline",
	Preparation = "UI/Warning/Warning 1st Outline",
	Night = "Nature/Cloud/Cloud 1st Outline",
	DoomNight = "Player/Skull/Skull 1st Outline",
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

-- Колонка меню HUD v2 (D48 v2): справа посередине — иконка, подпись под ней, на ПК клавиша (B — «Инвентарь»).
UITokens.MenuHud = {
	Icon = 92, -- px при масштабе 1 (WindowScale, StudMotion.BindResponsive)
	Label = 22, -- размер подписи
	LabelGap = 2,
	Gap = 14, -- между кнопками
	Margin = 18, -- от правого края
	Tilt = -8, -- наклон иконки (Stud-UI)
	KeySize = 28, -- значок клавиши
	Hover = 1.08,
	-- наклонная иконка-наклейка выступает левее кнопки: уведомления и «Удар» держатся левее и этого (визуальный QA:
	-- второе уведомление в Судную ночь наезжало на «Инвентарь»)
	IconOverflow = 14, -- px при масштабе 1
	-- D56 (четвёртая кнопка «Музей»): столбик стоит по центру экрана и должен уместиться между кнопками Roblox сверху
	-- (TopReserve, px экрана) и низом экрана (BottomReserve), а на касании — верхом кнопки прыжка (Jump — от низа
	-- экрана с запасом; JumpSmall — на экране с меньшей стороной ≤ SmallSide: там кнопки Roblox мельче). Не умещается —
	-- кнопки встают сеткой в два столбца (ColumnGap между ними, px при масштабе 1).
	ColumnGap = 4,
	SlotGap = 6, -- px экрана: между кнопкой «Удар» (над сеткой, только касание и Судная ночь) и сеткой меню
	TopReserve = 48,
	BottomReserve = 16,
	Jump = 218,
	JumpSmall = 98,
	SmallSide = 500,
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
	Header = "gold",
	Pad = 16,
	PadCompact = 10,
	Gap = 12,
	GapCompact = 8,
	CompactHeight = 430,
	Arrow = 76, -- стрелка между карточками (наклейка, заходит на обе)
	Tilt = -8, -- наклон иконок-наклеек (Stud-UI)
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

-- Статистика HUD v2 (D48 v2): слева посередине — иконка + число, без рамок; доход зелёный, сила с подписью.
UITokens.StatsHud = {
	Margin = 18,
	Width = 260, -- строка: иконка и число (D50: уже — плашка зоны на iPad не задевает)
	Y = 0.42, -- середина столбика по высоте экрана
	Rows = {
		Coins = { icon = 56, text = 40 },
		Income = { icon = 44, text = 30, color = Color3.fromHex("8BF06B") },
		Strength = { icon = 44, text = 30, note = 24 }, -- подпись «сила» крупнее (D50: на телефоне читается)
	},
	Gap = 8,
	TextGap = 8,
	Tilt = -8,
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
	Header = "blue", -- шапка окна: синяя — навигация (Stud-UI)
	-- Карточка D50: наименьшая ширина (сетка растягивает до строки), высота без кнопки — CardBody.
	Card = Vector2.new(178, 0),
	CardBody = 228, -- отступ, редкость, превью, название (2 строки), доход и локация, статус, отступы
	CardPad = 10,
	CardCorner = 10,
	CardStroke = 2, -- рамка цвета редкости (вместо чёрной 3 px Stud-UI)
	CardColor = Color3.fromHex("1B2238"),
	CardTransparency = 0.06,
	CardNeutral = Color3.fromHex("3A4560"), -- рамка карточки без редкости (занятый постамент)
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
	Chip = { -- сортировка и фильтр (D50): плоские капсулы вместо толстых кнопок
		Height = 34,
		Text = 17,
		TouchText = 22, -- на касании капсула высотой с кнопку (D32), текст крупнее
		Pad = 14,
		Gap = 8,
		Active = Color3.fromHex("2F7BFF"),
		Idle = Color3.fromHex("26304A"),
		IdleText = Color3.fromHex("C9D2E3"),
		IdleStroke = Color3.fromHex("3A4560"),
	},
	HotKey = Enum.KeyCode.B, -- ПК: открыть / закрыть (I и O — зум камеры Roblox)
	Refresh = 0.5, -- секунд между проверками фазы, пока окно открыто
	SearchDelay = 0.2, -- поиск: перерисовать после паузы в наборе
	Turn = 25, -- поворот превью вокруг вертикали, градусов
}

-- Окно «Защита» и расстановка (D46, Stud-UI): пиксели опорного экрана 1050 × 620.
UITokens.Defense = {
	Window = Vector2.new(940, 580),
	Header = "purple",
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
-- Турбо, Мега — 3D-модель, бонус, запас, цена, количество (−, число, +; касание числа: 1 → 5 → 10), «Купить».
UITokens.Shop = {
	Window = Vector2.new(980, 600),
	MinWindow = Vector2.new(700, 380),
	Margin = 16,
	PhoneScale = 0.78,
	MinTouch = 52,
	Header = "pink",
	Pad = 14,
	PadCompact = 8, -- внутри карточки телефона
	Gap = 12, -- между карточками
	CompactHeight = 470, -- окно ниже — раскладка телефона (и если карточка ПК не вмещает строку покупки даже с узким числом)
	Tab = Vector2.new(0, 50), -- вкладка уровня: ширина — по окну (10 в ряд), высота
	Button = 52, -- высота кнопок (на касании — не меньше MinTouch / масштаб)
	QtyButton = 52, -- «−» и «+»: квадрат
	QtyValue = 64, -- ширина числа
	QtyCompact = 48, -- ширина числа в строке телефона и в тесной карточке (планшет)
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
	Presets = { 1, 5, 10 },
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
	-- справа вверху сразу под кнопками Roblox (CoreUISafeInsets), левее колонки меню HUD v2 (D50: кнопка 52 px над
	-- колонкой задевала её на узких телефонах); только телефон. Отступы: сверху и до колонки меню. D56: когда меню
	-- стоит сеткой в два столбца (невысокий экран), левее меню кнопка упёрлась бы в таймер — она встаёт над сеткой у
	-- правого края (как в D49), сетка стоит ниже неё (UI/MenuHud)
	ButtonTop = 4,
	MenuGap = 8,
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

-- Основной цвет редкости (для подписи над предметом и т. п.).
function UITokens.RarityColor(rarity: string): Color3
	local g = UITokens.Rarity[rarity] or UITokens.Rarity.Common
	return g.bottom -- насыщенный край: им светят прожектор и подсветка
end

function UITokens.ToColorSequence(g: Gradient): ColorSequence
	return ColorSequence.new(g.top, g.bottom)
end

return UITokens

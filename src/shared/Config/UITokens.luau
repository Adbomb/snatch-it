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
		position = UDim2.fromScale(0.985, 0.18),
		size = UDim2.fromScale(0.26, 0.5),
		minWidth = 220,
		maxWidth = 360,
		itemHeight = 56,
		lifetime = 4, -- секунды
		maxCount = 4,
	},
	-- «Бросить»: справа, выше кнопки прыжка на телефоне.
	DropButton = {
		position = UDim2.fromScale(0.97, 0.6),
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
	-- Временные надписи силы и монет: внизу слева (до шага интерфейса Stud-UI).
	GymHud = {
		position = UDim2.fromScale(0.015, 0.97), -- нижний левый угол столбика
		pill = Vector2.new(190, 44), -- надпись, px (кнопок нет — 52×52 не нужно)
		gap = 8, -- между надписями, px
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

-- Таймер фазы (D37, место — D27: внизу справа; на телефоне — над кнопкой прыжка).
UITokens.TimeHud = {
	Size = Vector2.new(250, 84), -- пиксели при масштабе 1 (дальше — UIScale по экрану, StudMotion.BindResponsive)
	Margin = 16,
	TouchLift = 170, -- на сенсорном экране поднять над кнопкой прыжка
	PhaseSize = 22,
	TimeSize = 34,
	InfoSize = 14,
	Refresh = 0.2, -- секунды между обновлениями отсчёта
	-- Градиенты панели по фазам (верх → низ); день и ночь — из тем Stud-UI.
	Theme = { Day = "blue", Preparation = "amber", Night = "violet" },
	DoomNight = { Color3.fromHex("FF5A5A"), Color3.fromHex("B3122E") },
	Warning = 15, -- последние секунды фазы: отсчёт мигает цветом Danger
}

-- Плашка входа в уровень (D41): сверху по центру, 1.5 с, цвет — от спокойного зелёного к тревожному (по номеру зоны).
UITokens.LevelBanner = {
	Size = Vector2.new(380, 96), -- пиксели при масштабе 1 (UIScale по экрану, StudMotion.BindResponsive)
	Top = 64, -- отступ сверху (под кнопками Roblox)
	Hold = 1.5, -- секунд на экране после появления
	In = 0.35,
	Out = 0.3,
	Emoji = 64, -- круг со смайликом
	NumberSize = 16,
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
	Follow = 12, -- скорость, с которой подпись догоняет своё место (1/с)
}

-- Колонка кнопок меню в HUD (D46): слева над столбиком надписей силы и монет (UI/MenuHud), одна WindowScale.
UITokens.MenuHud = {
	Button = Vector2.new(196, 64),
	Gap = 10,
	Margin = 16,
	AbovePills = 12, -- отступ над столбиком надписей (Layout.GymHud)
}

-- Окно «Инвентарь» (D46, Stud-UI): пиксели опорного экрана 1050 × 620, весь корень масштабирует WindowScale
-- (StudMotion: телефон 844 × 390 → × 0.63, поэтому текст не меньше 19 px).
UITokens.Inventory = {
	Window = Vector2.new(980, 600),
	Header = "blue", -- шапка окна: синяя — навигация (Stud-UI)
	Card = Vector2.new(218, 336), -- карточка предмета: 4 в ряд; название в 2 строки, локация и статус — по строке
	Gap = 14,
	Preview = 110, -- высота 3D-превью в карточке
	Pedestal = Vector2.new(214, 150), -- плитка постамента в выборе места
	BarHeight = 50, -- строка счётчиков и поиска, строка сортировки и фильтров
	SearchWidth = 300,
	NameText = 26,
	IncomeText = 24,
	InfoText = 20,
	ButtonHeight = 48,
	HotKey = Enum.KeyCode.B, -- ПК: открыть / закрыть (I и O — зум камеры Roblox)
	Refresh = 0.5, -- секунд между проверками фазы, пока окно открыто
	SearchDelay = 0.2, -- поиск: перерисовать после паузы в наборе
	ChipBar = 42, -- высота кнопок сортировки и фильтра (полоса прокручивается по горизонтали)
	MinText = 19, -- нижний предел текста карточек (на телефоне × 0.63 ≈ 12 px)
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
	Button = Vector2.new(150, 52),
	Bar = Vector2.new(560, 120), -- панель расстановки внизу экрана
	Ghost = { Trap = Vector3.new(2.4, 0.6, 2.4), Robot = Vector3.new(2.4, 5.8, 1.8), Snare = Vector3.new(1.9, 0.6, 1.9) },
	GhostOk = Color3.fromHex("5BEA72"),
	GhostBad = Color3.fromHex("FF5A5A"),
	GhostTransparency = 0.45,
	SpotNames = { Entrance = "вход", Middle = "середина" }, -- в строке «стоит: …»
	SpotButtons = { Entrance = "Вход", Middle = "Середина" }, -- на кнопках мест лазера
	RobotBar = { -- полоска HP робота-охранника (BillboardGui, стады)
		Size = Vector2.new(3, 0.4),
		Lift = 2.4,
		MaxDistance = 60,
		Back = Color3.fromHex("1E1E24"),
		Fill = Color3.fromHex("5BEA72"),
	},
}

-- PvP Судной ночи (D46): кнопка «Удар» (телефон и мышь), звёзды нокаута, числа урона.
UITokens.Pvp = {
	Button = Vector2.new(150, 72), -- кнопка «Удар» (px опорного экрана, масштаб — StudMotion)
	ButtonPosition = UDim2.new(1, -16, 0.25, 0), -- справа вверху: не на таймере фазы (на телефоне он поднят) и не на «Бросить»
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

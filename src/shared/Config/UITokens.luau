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
	Uncommon = gradient("C4F79A", "43C22E"),
	Rare = gradient("84CAE8", "3D8EE0"),
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

-- Основной цвет редкости (для подписи над предметом и т. п.).
function UITokens.RarityColor(rarity: string): Color3
	local g = UITokens.Rarity[rarity] or UITokens.Rarity.Common
	return g.bottom -- насыщенный край: им светят прожектор и подсветка
end

function UITokens.ToColorSequence(g: Gradient): ColorSequence
	return ColorSequence.new(g.top, g.bottom)
end

return UITokens

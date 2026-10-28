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

-- Редкость: у всех, кроме Secret, верх и низ совпадают (сплошной цвет).
UITokens.Rarity = {
	Common = gradient("B8C4D0", "B8C4D0"),
	Uncommon = gradient("4CD964", "4CD964"),
	Rare = gradient("3FA2FF", "3FA2FF"),
	Legendary = gradient("FFB800", "FFB800"),
	Secret = gradient("FF3DAA", "8C3DFF"),
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
}

-- Основной цвет редкости (для подписи над предметом и т. п.).
function UITokens.RarityColor(rarity: string): Color3
	local g = UITokens.Rarity[rarity] or UITokens.Rarity.Common
	return g.top
end

function UITokens.ToColorSequence(g: Gradient): ColorSequence
	return ColorSequence.new(g.top, g.bottom)
end

return UITokens

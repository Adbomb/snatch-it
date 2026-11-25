-- Свет по зонам (план docs/LANES_PLAN.md, раздел Б; одобрен владельцем 2026-11-25): у зоны с профилем свет плавно
-- меняется, когда игрок в неё входит, и возвращается к исходному (настройки места) при выходе. Только у клиента.
-- Зона 5 «Ледник»: голубые тени (Ambient, OutdoorAmbient), синеватая дымка с бледным вечерне-фиолетовым горизонтом
-- (Atmosphere: дальний ледник светлее и отделяется от неба), белое не выжигается (ExposureCompensation,
-- ColorCorrection). Aurora — мягкое северное сияние высоко за ледником (решение владельца по снимку: включено или нет).
-- Числа подобраны по кадрам от входа в зону.

export type Profile = {
	Ambient: Color3?,
	OutdoorAmbient: Color3?,
	ExposureCompensation: number?,
	Atmosphere: { Color: Color3?, Decay: Color3?, Density: number?, Haze: number?, Glare: number? }?,
	ColorCorrection: { TintColor: Color3?, Brightness: number?, Contrast: number?, Saturation: number? }?,
	Aurora: boolean?,
}

local ZoneAtmosphere = {}

ZoneAtmosphere.Fade = 1.5 -- секунд на переход света

ZoneAtmosphere.Profiles = {
	[5] = {
		Ambient = Color3.new(0.36, 0.42, 0.55),
		OutdoorAmbient = Color3.new(0.5, 0.58, 0.75),
		ExposureCompensation = -0.45,
		Atmosphere = {
			Color = Color3.new(0.84, 0.86, 0.99),
			Decay = Color3.new(0.62, 0.58, 0.88),
			Density = 0.36,
			Haze = 1.9,
			Glare = 0,
		},
		ColorCorrection = { TintColor = Color3.new(0.92, 0.96, 1), Brightness = -0.04 },
		Aurora = true,
	} :: Profile,
}

-- Сияние (второй заход 2026-11-25: «мягкое», не бруски): каждая лента — луч Beam без текстуры, изогнутый
-- S-образно, прозрачность к концам плавно растёт до 1; поверх ядра — вдвое шире и бледнее ореол. Координаты зоны
-- (x поперёк, z вдоль от входа −47.5 к выходу +47.5, y от пола): x центра, y середины, z, длина, ширина, подъём
-- правого конца над левым, цвет.
-- Ленты тонкие, почти параллельные (не скрещиваются), высоко и далеко за ледником; вдоль ленты цвет переходит от
-- бледно-мятного к бледно-сиреневому (color → color2).
ZoneAtmosphere.Aurora = {
	Core = 0.6, -- прозрачность середины ядра (1 — не видно)
	Halo = 0.88, -- прозрачность середины ореола
	HaloWidth = 2.2, -- ореол шире ядра во столько раз
	Curve = 9, -- изгиб ленты (стадов)
	Sway = 3, -- колыхание изгиба (стадов)
	Period = 12, -- секунд
	Ribbons = {
		{
			x = -18,
			y = 78,
			z = 135,
			length = 120,
			width = 4,
			rise = 12,
			color = Color3.fromRGB(185, 245, 220),
			color2 = Color3.fromRGB(220, 205, 255),
		},
		{
			x = -6,
			y = 92,
			z = 150,
			length = 130,
			width = 3.2,
			rise = 12,
			color = Color3.fromRGB(200, 240, 250),
			color2 = Color3.fromRGB(225, 210, 255),
		},
		{
			x = 30,
			y = 70,
			z = 125,
			length = 70,
			width = 2.6,
			rise = 9,
			color = Color3.fromRGB(185, 245, 220),
			color2 = Color3.fromRGB(205, 235, 255),
		},
	},
}

return ZoneAtmosphere

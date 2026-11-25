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
			Color = Color3.new(0.82, 0.82, 0.97),
			Decay = Color3.new(0.55, 0.52, 0.82),
			Density = 0.33,
			Haze = 1.5,
			Glare = 0,
		},
		ColorCorrection = { TintColor = Color3.new(0.92, 0.96, 1), Brightness = -0.04 },
		Aurora = true,
	} :: Profile,
}

-- Сияние: ленты в координатах зоны (x поперёк, z вдоль от входа −47.5 к выходу +47.5, y от пола): x центра, y низа,
-- z, длина, высота, наклон (градусы) и цвет. Бледные, полупрозрачные, медленно колышутся.
ZoneAtmosphere.Aurora = {
	Transparency = 0.62,
	Segments = 7,
	Sway = 2.5, -- стадов: колыхание по высоте
	Period = 9, -- секунд
	Ribbons = {
		{ x = -40, y = 62, z = 80, length = 70, height = 5, tilt = 6, color = Color3.fromRGB(176, 245, 214) },
		{ x = 25, y = 70, z = 95, length = 80, height = 4, tilt = -5, color = Color3.fromRGB(186, 232, 245) },
		{ x = -5, y = 78, z = 110, length = 90, height = 3.5, tilt = 3, color = Color3.fromRGB(176, 245, 214) },
		{ x = 45, y = 58, z = 70, length = 50, height = 3, tilt = -8, color = Color3.fromRGB(214, 200, 245) },
	},
}

return ZoneAtmosphere

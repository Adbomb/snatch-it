-- Цвета участков-музеев: акцент у каждого участка свой (поле качалки, D36). Здание музея — D48-C
-- (World/MuseumVisual, World/Models/MuseumD48). Ни от чего не зависит.

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

local Museum = {}

-- Цвет акцента у каждого участка свой (8 участков).
Museum.Accents = {
	hex("E53935"), -- красный
	hex("FB8C00"), -- оранжевый
	hex("FDD835"), -- жёлтый
	hex("43A047"), -- зелёный
	hex("00ACC1"), -- бирюзовый
	hex("1E88E5"), -- синий
	hex("8E24AA"), -- фиолетовый
	hex("EC407A"), -- розовый
}

return Museum

-- Цвета мира в стиле LEGO (D13): сочные, без серо-бурых оттенков. Ни от чего не зависит.

local function rgb(hex: string): Color3
	return Color3.fromHex(hex)
end

return {
	Grass = rgb("4CD43B"),
	GrassDark = rgb("2FA52A"),
	Hill = rgb("3CC03A"),
	Asphalt = rgb("4A4E58"),
	Curb = rgb("C8CCD4"),
	Marking = rgb("FFFFFF"),
	Street = rgb("9AA0AA"),
	Plaza = rgb("E8DCC0"),
	PlazaAccent = rgb("D2B98C"),
	Pavement = rgb("BFC4CC"),
	Water = rgb("3DB4FF"),
	Stone = rgb("A7ADB8"),
	Wood = rgb("8A5A2B"),
	WoodDark = rgb("5E3A1A"),
	Trunk = rgb("7A4A22"),
	Leaves = { rgb("3FBF3A"), rgb("2E9E30"), rgb("5AD84A") },
	Bush = rgb("37B23A"),
	BorderWall = { rgb("D93A3A"), rgb("F2C230"), rgb("3A7BD9") },
	Metal = rgb("6B7280"),
	Lamp = rgb("FFE08A"),
	White = rgb("FFFFFF"),
	Black = rgb("1B1530"),
	Glass = rgb("BFE6FF"),
	Door = rgb("7A3E1C"),
	-- Стены и крыши домов: яркие стены, контрастные крыши.
	HouseWalls = { rgb("E53935"), rgb("FDD835"), rgb("1E88E5"), rgb("FB8C00") },
	HouseRoofs = { rgb("263238"), rgb("6A1B9A"), rgb("2E7D32"), rgb("C62828") },
	-- Полосатые навесы ларьков: пары цветов.
	Awnings = {
		{ rgb("2EBD4E"), rgb("FFFFFF") },
		{ rgb("E53935"), rgb("FFFFFF") },
		{ rgb("1E88E5"), rgb("FFFFFF") },
		{ rgb("FFB300"), rgb("FFFFFF") },
	},
}

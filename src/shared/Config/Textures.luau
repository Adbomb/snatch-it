-- Текстуры поверхности (D36): «квадратные пупырышки» — мелкие вдавленные квадратики (один на стад) и шахматка клеток
-- 4 × 4 стада. Картинки генерирует scripts/textures/square_studs.py (assets/textures/lego_squares*), загружены в
-- Roblox; плитка 8 × 8 стадов, поэтому StudsPerTile = 8. Три рельефа:
-- Squares — весь Plastic (трава, постройки), SquaresDeep — земляные обрывы, SquaresSoft — музеи (спокойная шахматка).
-- Круглые пупырышки (LegoStuds) больше не используются. Ни от чего не зависит.

export type Variant = { name: string, color: string, normal: string, roughness: string, studsPerTile: number }

local ROUGHNESS = "rbxassetid://86272303409120"

return {
	-- Заменяет весь Plastic (MaterialService.PlasticName / SetBaseMaterialOverride).
	Squares = {
		name = "LegoSquares",
		color = "rbxassetid://90809959209755",
		normal = "rbxassetid://108191277429237",
		roughness = ROUGHNESS,
		studsPerTile = 8,
	},
	SquaresDeep = {
		name = "LegoSquaresDeep",
		color = "rbxassetid://91540160577187",
		normal = "rbxassetid://116664288395547",
		roughness = ROUGHNESS,
		studsPerTile = 8,
	},
	SquaresSoft = {
		name = "LegoSquaresSoft",
		color = "rbxassetid://94676505361870",
		normal = "rbxassetid://95409488837994",
		roughness = ROUGHNESS,
		studsPerTile = 8,
	},
	-- Предметы искусства (референсы владельца 2026-10-31): крупные выпуклые скруглённые квадраты с тонкими швами,
	-- без шахматки; 4 × 4 квадрата на плитку (scripts/textures/art_squares.py), квадрат ≈ 0.6 стада.
	SquaresArt = {
		name = "LegoSquaresArt",
		color = "rbxassetid://89532853999247",
		normal = "rbxassetid://131709166848159",
		roughness = ROUGHNESS,
		studsPerTile = 2.4,
	},
} :: { [string]: Variant }

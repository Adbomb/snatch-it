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
	-- Предметы искусства и боссы (референсы владельца 2026-10-31): редкие вдавленные квадраты с фаской, без
	-- шахматки (square_studs.py, вариант squares_item); квадрат — полстада (StudsPerTile 4).
	SquaresItem = {
		name = "LegoSquaresItem",
		color = "rbxassetid://72169564431115",
		normal = "rbxassetid://116456877518185",
		roughness = ROUGHNESS,
		studsPerTile = 4,
	},
	-- Архитектура этажей музея-небоскрёба в стиле D39 (образец sample_d39, 2026-11-19): те же отдельные скруглённые
	-- квадраты-контуры, что запекаются в карты предметов и боссов (шаг 0.6 стада, квадрат 0.42, скругление 0.1,
	-- контур 0.03, затемнение 22 %); плитка 4 × 4 квадрата = 2.4 стада, фон белый — цвет даёт деталь
	-- (scripts/textures/rings_d39.py).
	RingsD39 = {
		name = "LegoRingsD39",
		color = "rbxassetid://93780113976638",
		normal = "rbxassetid://121354316727204",
		roughness = ROUGHNESS,
		studsPerTile = 2.4,
	},
	-- Объекты на этажах музея-небоскрёба (статуи, звери, мебель, машины) — в стиле предметов и боссов (решение владельца
	-- 2026-11-21, эталон — босс 3 «Крысиный король»): тот же рисунок RingsD39, но в масштабе боссов (×3: шаг 1.8 стада).
	RingsD39Boss = {
		name = "LegoRingsD39Boss",
		color = "rbxassetid://93780113976638",
		normal = "rbxassetid://121354316727204",
		roughness = ROUGHNESS,
		studsPerTile = 7.2,
	},
	-- Этажи музея-небоскрёба по референсу владельца 2026-11-19 (забор из брусков): крупные вдавленные квадраты с
	-- фаской, по одному на стад, дно через один светлее и темнее; плитка 2 × 2 стада. Блоки этажа выровнены по сетке
	-- в один стад — квадраты не режутся краями (scripts/textures/squares_bold.py).
	SquaresBold = {
		name = "LegoSquaresBold",
		color = "rbxassetid://96497926936161",
		normal = "rbxassetid://136219700983341",
		roughness = ROUGHNESS,
		studsPerTile = 2,
	},
	-- Тот же рисунок и сетка, но для ткани этажей (бархат, ковёр, потолок): квадраты едва заметны, через один —
	-- алый / малиновый оттенок; глаз отдыхает, золото и экспонат становятся акцентом (2026-11-20).
	SquaresQuiet = {
		name = "LegoSquaresQuiet",
		color = "rbxassetid://104945001541305",
		normal = "rbxassetid://84552646501158",
		roughness = ROUGHNESS,
		studsPerTile = 2,
	},
	-- Золото фасадов этажей: рисунок SquaresBold, но мягче и чуть размыт — фасад видят издалека, мелкий рисунок
	-- там рябит (2026-11-20).
	SquaresFar = {
		name = "LegoSquaresFar",
		color = "rbxassetid://80091990664920",
		normal = "rbxassetid://98136649032051",
		roughness = ROUGHNESS,
		studsPerTile = 2,
	},
} :: { [string]: Variant }

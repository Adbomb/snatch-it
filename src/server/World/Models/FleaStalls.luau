-- Павильоны и большие вещи «Барахолки» (D44, полировка D45): шесть разных торговых павильонов с крышами, вывесками, витринами,
-- товаром и подсветкой и гигантские декорации — гора сокровищ с огромным сундуком (фон для босса), карманные часы,
-- стопка монет, мачты с ценником и монетой, рекламные щиты на обрывах. Это декорации: настоящие предметы босса
-- стоят только на площадке (MapLayout.ArtSlots). Павильон — функция кирпичей в своих координатах: начало — середина
-- переднего края на полу, ширина вдоль X, глубина в +Z, лицо (витрина) смотрит в −Z. Крупные части (стены, крыши,
-- помосты) твёрдые и с тенью, мелкий товар — без столкновений и тени. Свет — один источник на павильон.
-- Зависит от World/Models/FleaKit.

local ServerScriptService = game:GetService("ServerScriptService")

local FleaKit = require(ServerScriptService.Server.World.Models.FleaKit)

type Brick = FleaKit.Brick

local B, V, C = FleaKit.B, FleaKit.V, FleaKit.C
local Box, Disc, Round = FleaKit.Box, FleaKit.Disc, FleaKit.Round
local Neon, Board, Gem, Label, Put = FleaKit.Neon, FleaKit.Board, FleaKit.Gem, FleaKit.Label, FleaKit.Put
local DECOR, BALL, GLASS, WEDGE = FleaKit.DECOR, FleaKit.BALL, FleaKit.GLASS, FleaKit.WEDGE
local SOLID = { collide = true, shadow = true } -- круглые крупные части (по умолчанию круглые — декор)
local SIDES = { Enum.NormalId.Left, Enum.NormalId.Right }

-- Свет павильона: тёплый у золота, холодный у бирюзы.
local function lamp(range: number, color: Color3): { range: number, brightness: number, color: Color3 }
	return { range = range, brightness = 1, color = color }
end

-- Свес карниза вдоль края ската (z — край, y — его высота, slope — подъём ската на стад): пологий клин, высокий
-- край спрятан под скатом, низкий выступает на depth наружу (side −1 — вперёд, 1 — назад) — край будто загнут вверх.
-- По наружной кромке — золотая планка, на углах — золотые «рога» высокой стороной наружу (размер horn).
local function eave(
	out: { Brick },
	width: number,
	z: number,
	y: number,
	slope: number,
	depth: number,
	side: number,
	color: Color3,
	horn: number
)
	local inside = 0.4 / slope
	local at = CFrame.new(0, y, z + side * (depth / 2 - inside))
	if side > 0 then
		at *= FleaKit.TURN
	end
	table.insert(out, B(V(width, 0.8, depth), at, color, WEDGE))
	local edge = z + side * (depth - inside)
	table.insert(
		out,
		Box(-width / 2 - 0.2, width / 2 + 0.2, y - 0.75, y - 0.3, edge - 0.15, edge + 0.15, C.gold, DECOR)
	)
	for _, s in { -1, 1 } do
		local turn = math.rad(if side < 0 then s * 135 else s * 45)
		local tip = CFrame.new(s * (width / 2 + 0.2), y + 0.5 * horn, edge) * CFrame.Angles(0, turn, 0)
		table.insert(out, B(V(0.8, 2.4, 2) * horn, tip, C.gold, FleaKit.With(WEDGE, DECOR)))
	end
end

local FleaStalls = {}

-- «Пагода находок» (28 × 24): помост, бирюзовые стены, четыре столба, прилавок с кубками, двухъярусная крыша с
-- загнутыми золотыми углами, ярус с медальоном-монетой, шпиль с самоцветом, фонарики по краям, вывеска над
-- прилавком и подвесная поперёк фасада.
function FleaStalls.Pagoda(): { Brick }
	local out = {
		Box(-14, 14, 0, 0.8, 0, 24, C.graphite),
		Box(-10, 10, 0, 0.4, -1.4, 0.2, C.graphiteLight),
		Box(-14.1, 14.1, 0.5, 0.9, -0.15, 0.15, C.gold, DECOR),
		Box(-13, 13, 0.8, 13.4, 20.5, 22, C.tealDeep),
		Box(-13.2, -12.2, 0.8, 13.3, 10, 22.2, C.tealDeep),
		Box(12.2, 13.2, 0.8, 13.3, 10, 22.2, C.tealDeep),
		Box(-14.6, 14.6, 12, 13.4, 0.3, 2.9, C.graphiteDark),
		Box(-14.4, 14.4, 12.4, 13, 0.2, 0.5, C.gold, DECOR),
	}
	for _, x in { -13, -4.6, 4.6, 13 } do
		table.insert(out, Box(x - 0.7, x + 0.7, 0.8, 12, 0.9, 2.3, C.graphiteDark))
		table.insert(out, Box(x - 0.95, x + 0.95, 0.8, 1.8, 0.65, 2.55, C.gold, DECOR))
		table.insert(out, Box(x - 0.95, x + 0.95, 11.2, 12.1, 0.65, 2.55, C.gold, DECOR))
	end
	-- Прилавок с товаром.
	table.insert(out, Box(-9, 9, 0.8, 4.2, 3.4, 5.8, C.teal))
	table.insert(out, Box(-9.3, 9.3, 4.2, 4.6, 3.1, 6.1, C.cream))
	table.insert(out, Box(-8.8, 8.8, 2.9, 3.5, 3.3, 3.5, C.orange, DECOR))
	Put(out, FleaKit.Trophy(C.gold, 1.3, true), CFrame.new(-6, 4.6, 4.6))
	Put(out, FleaKit.Trophy(C.silver, 1.1, true), CFrame.new(6.2, 4.6, 4.4))
	table.insert(out, Gem(0.9, V(-2.6, 5.25, 4.4), C.purpleLight))
	table.insert(out, Gem(0.8, V(2.8, 5.2, 4.8), C.tealLight))
	table.insert(out, B(V(1.2, 1.2, 1.2), V(0, 5.2, 4.6), C.goldLight, BALL))
	-- Полки на задней стене: вазы и самоцветы.
	for _, y in { 5, 8.4 } do
		table.insert(out, Box(-11, 11, y, y + 0.3, 18.4, 20.5, C.metal, DECOR))
	end
	for i, x in { -8, -3, 3, 8 } do
		local color = ({ C.orange, C.gold, C.purple, C.teal })[i]
		table.insert(out, Disc(1.4, 5.3, 7.1, x, 19.4, color))
		table.insert(out, Gem(0.9, V(x + 1.4, 9.3, 19.4), ({ C.red, C.tealLight, C.goldLight, C.purpleLight })[i]))
	end
	-- Фонарь под крышей — свет павильона (тёплый).
	table.insert(out, Neon(V(1.4, 1.4, 1.4), V(0, 10.6, 12), C.orangeLight))
	out[#out].light = lamp(22, C.orangeLight)
	-- Фонарики между столбами.
	for _, x in { -8.8, 8.8 } do
		table.insert(out, Box(x - 0.06, x + 0.06, 10.6, 12, 1.55, 1.65, C.metal, DECOR))
		table.insert(
			out,
			B(V(1.7, 1.7, 1.7), V(x, 9.8, 1.6), C.orange, FleaKit.With(BALL, { material = Enum.Material.Neon }))
		)
		table.insert(out, Disc(1, 10.55, 10.85, x, 1.6, C.gold))
		table.insert(out, Disc(0.5, 8.6, 9, x, 1.6, C.red))
	end
	-- Нижняя крыша: скаты, пологие свесы с золотой кромкой, загнутые углы, конёк, монеты на торцах.
	FleaKit.Gable(out, -15.5, 15.5, -1.6, 25.6, 13.4, 5.2, { C.tealDark })
	eave(out, 31, -1.6, 13.4, 5.2 / 13.6, 3.4, -1, C.tealDark, 1)
	eave(out, 31, 25.6, 13.4, 5.2 / 13.6, 3.4, 1, C.tealDark, 1)
	table.insert(out, Box(-15.7, 15.7, 18.35, 18.95, 11.6, 12.4, C.gold))
	for _, x in { -15.65, 15.65 } do
		table.insert(out, B(V(0.4, 3.4, 3.4), V(x, 15.3, 12), C.gold, FleaKit.ROUND))
	end
	-- Верхний ярус: кремовые стены, золотые углы, медальон-монета с самоцветом.
	table.insert(out, Box(-7.5, 7.5, 15.5, 21.5, 6.5, 17.5, C.cream))
	for _, x in { -7.6, 7.6 } do
		table.insert(out, Box(x - 0.5, x + 0.5, 16, 21.7, 6.2, 7.2, C.gold, DECOR))
	end
	table.insert(out, Round(4.6, 0.5, CFrame.new(0, 18.6, 6.35), C.gold))
	table.insert(out, Round(3.2, 0.3, CFrame.new(0, 18.6, 6), C.goldLight))
	table.insert(out, Gem(1.2, V(0, 18.6, 5.6), C.purple))
	-- Верхняя крыша, свесы, углы, конёк, шпиль.
	FleaKit.Gable(out, -9.5, 9.5, 4.2, 19.8, 21.5, 4.6, { C.teal })
	eave(out, 19, 4.2, 21.5, 4.6 / 7.8, 2.6, -1, C.teal, 0.75)
	eave(out, 19, 19.8, 21.5, 4.6 / 7.8, 2.6, 1, C.teal, 0.75)
	table.insert(out, Box(-9.7, 9.7, 25.8, 26.4, 11.6, 12.4, C.gold))
	table.insert(out, Disc(1.6, 26.3, 27.7, 0, 12, C.gold))
	table.insert(out, B(V(2, 2, 2), V(0, 28.6, 12), C.goldLight, BALL))
	table.insert(out, Gem(1.4, V(0, 30.3, 12), C.purple))
	-- Вывески: подвесная поперёк фасада (читается вдоль коридора) и над прилавком.
	table.insert(out, Box(-13.2, -12.8, 12.3, 12.7, -8.2, 0.9, C.graphiteDark, DECOR))
	for _, z in { -7.4, -2.6 } do
		table.insert(out, Box(-13.06, -12.94, 11.4, 12.3, z - 0.06, z + 0.06, C.metal, DECOR))
	end
	table.insert(out, Board(V(0.4, 4.4, 6), V(-13, 9.2, -5), C.orange, Label("ДЁШЕВО!", SIDES)))
	table.insert(out, Box(-13.15, -12.85, 6.8, 11.6, -8.2, -1.8, C.gold, DECOR))
	table.insert(out, Board(V(7.4, 1.8, 0.3), V(0, 10.9, 0.45), C.orange, Label("НАХОДКИ")))
	table.insert(out, Box(-3.9, 3.9, 9.85, 11.95, 0.55, 0.75, C.gold, DECOR))
	return out
end

-- «Купол редкостей» (24 × 24): круглый помост, фиолетовый барабан с золотыми пилястрами, карниз с неоновым кольцом,
-- бирюзовый купол с золотым поясом, фонарь с огромным кубком наверху, витрина-окно со светящимся фоном, вывеска,
-- стеклянные кубы с самоцветами у входа, подвесные знамёна.
function FleaStalls.Rotunda(): { Brick }
	local cz = 12
	local out = {
		Disc(22, 0, 1, 0, cz, C.graphite, SOLID),
		Disc(22.4, 0.3, 0.8, 0, cz, C.gold),
		Box(-6, 6, 0, 0.5, -1.4, 3, C.graphiteLight),
		Disc(18, 1, 12, 0, cz, C.purple, SOLID),
		Disc(20, 12, 13.2, 0, cz, C.gold, SOLID),
		Disc(19, 13.2, 13.6, 0, cz, C.purpleLight, { material = Enum.Material.Neon }),
		B(V(17, 17, 17), V(0, 13.4, cz), C.teal, FleaKit.With(BALL, SOLID)),
		Disc(16.6, 16.2, 16.7, 0, cz, C.gold),
		Disc(4.2, 20.8, 22.8, 0, cz, C.gold),
		Disc(3.4, 22.8, 24.4, 0, cz, C.purple),
		Disc(4.4, 24.4, 24.8, 0, cz, C.goldDark),
	}
	Put(out, FleaKit.Trophy(C.gold, 3.2, true), CFrame.new(0, 24.8, cz))
	-- Пилястры по барабану (у окна их нет).
	for k = 1, 3 do
		for _, s in { -1, 1 } do
			local angle = math.rad(s * (22.5 + k * 45))
			local at = CFrame.new(0, 0, cz) * CFrame.Angles(0, angle, 0) * CFrame.new(0, 6.5, -9.1)
			table.insert(out, B(V(1.4, 11, 0.5), at, C.gold, DECOR))
		end
	end
	-- Знамёна под карнизом: полотно и золотой треугольный низ.
	for i, deg in { -58, 58, -150, 150 } do
		local turn = CFrame.new(0, 0, cz) * CFrame.Angles(0, math.rad(deg), 0)
		local color = if i % 2 == 1 then C.teal else C.orange
		table.insert(out, B(V(2.6, 5.4, 0.25), turn * CFrame.new(0, 9.3, -9.3), color, DECOR))
		table.insert(
			out,
			B(V(1.84, 1.84, 0.3), turn * CFrame.new(0, 6.6, -9.3) * CFrame.Angles(0, 0, math.rad(45)), C.gold, DECOR)
		)
	end
	-- Витрина-окно: рама, светящийся фон (свет павильона), стекло, редкости на подоконнике.
	table.insert(out, Box(-5.4, 5.4, 1, 2.6, 1.4, 5.2, C.purpleDark))
	table.insert(out, Box(-5.4, 5.4, 7.6, 9.2, 1.4, 5.2, C.purpleDark))
	table.insert(out, Box(-5.4, -4.2, 2.6, 7.6, 1.4, 5.2, C.purpleDark))
	table.insert(out, Box(4.2, 5.4, 2.6, 7.6, 1.4, 5.2, C.purpleDark))
	table.insert(out, Neon(V(8.4, 5, 0.4), V(0, 5.1, 3.8), C.cream))
	out[#out].light = lamp(18, C.purpleLight)
	table.insert(out, Box(-4.2, 4.2, 2.6, 7.6, 1.5, 1.7, C.glass, GLASS))
	Put(out, FleaKit.Trophy(C.silver, 1.2, true), CFrame.new(-2.5, 2.6, 2.8))
	table.insert(out, Gem(1.3, V(0, 3.5, 2.8), C.purpleLight))
	table.insert(out, B(V(1.3, 1.3, 1.3), V(2.5, 3.25, 2.8), C.goldLight, BALL))
	-- Вывеска на кронштейнах.
	table.insert(out, Board(V(12, 2.4, 0.5), V(0, 10.6, 1.6), C.orange, Label("РЕДКОСТИ")))
	table.insert(out, Box(-6.3, 6.3, 9.1, 12.1, 1.8, 2.1, C.gold, DECOR))
	for _, x in { -5, 5 } do
		table.insert(out, Box(x - 0.3, x + 0.3, 10.2, 11, 2.1, 6, C.graphite, DECOR))
	end
	-- Стеклянные кубы с самоцветами по бокам от входа.
	for i, x in { -8.6, 8.6 } do
		table.insert(out, Box(x - 1.2, x + 1.2, 0, 2.4, -2.7, -0.3, C.graphite))
		table.insert(out, Box(x - 1.1, x + 1.1, 2.4, 5, -2.6, -0.4, C.glass, GLASS))
		table.insert(out, Gem(1.1, V(x, 3.7, -1.5), if i == 1 then C.teal else C.red))
		table.insert(out, Box(x - 1.3, x + 1.3, 5, 5.4, -2.8, -0.2, C.gold, DECOR))
	end
	return out
end

-- «Сюрпризы» — большой полосатый шатёр (24 × 20): помост, столбы, крыша оранжево-кремовыми полосами, кромка с
-- флажками, флаги на коньке и торцах, вывеска; внутри чемоданы, подарочные коробки и ящик «?»; тёплая лампа.
function FleaStalls.Tent(): { Brick }
	local out = {
		Box(-12, 12, 0, 0.6, 0, 20, C.graphite),
		Box(-12.1, 12.1, 0.3, 0.7, -0.15, 0.15, C.orange, DECOR),
		Box(-11.6, 11.6, 0.6, 10.2, 19.4, 19.8, C.purpleDark),
	}
	for _, x in { -11.4, 11.4 } do
		for _, z in { 0.8, 19.2 } do
			table.insert(out, Box(x - 0.4, x + 0.4, 0.6, 10.3, z - 0.4, z + 0.4, C.graphiteDark))
		end
	end
	FleaKit.Gable(out, -13, 13, -1.4, 21.4, 10.2, 8, { C.orange, C.cream }, 3.25)
	table.insert(out, Box(-13.2, 13.2, 18, 18.6, 9.6, 10.4, C.gold))
	-- Кромка и флажки: ромбы за кромкой, видна нижняя половина — треугольники.
	table.insert(out, Box(-13.2, 13.2, 9.4, 10.6, -1.75, -1.45, C.orangeDark, DECOR))
	local flags = { C.teal, C.goldLight, C.purple }
	for i = 0, 7 do
		local x = -11.4 + i * 3.25
		local at = CFrame.new(x, 9.4, -1.3) * CFrame.Angles(0, 0, math.rad(45))
		table.insert(out, B(V(1.7, 1.7, 0.2), at, flags[i % 3 + 1], DECOR))
	end
	-- Флаги: на коньке и над торцами.
	for _, flag in { { 0, 23.5, 3.6, C.teal }, { -13.15, 21.2, 2.4, C.purple }, { 13.15, 21.2, 2.4, C.orange } } do
		local x, top, w, color = flag[1], flag[2], flag[3], flag[4]
		local dir = if x < 0 then -1 else 1 -- флаг развевается наружу
		table.insert(out, Box(x - 0.15, x + 0.15, 17.6, top, 9.85, 10.15, C.metal, DECOR))
		local x0, x1 = x + dir * 0.15, x + dir * (0.15 + w)
		table.insert(out, Box(math.min(x0, x1), math.max(x0, x1), top - 1.9, top - 0.1, 9.92, 10.08, color, DECOR))
		table.insert(out, B(V(0.7, 0.7, 0.7), V(x, top + 0.3, 10), C.gold, BALL))
	end
	table.insert(out, Board(V(11, 2.8, 0.4), V(0, 12.3, -1.75), C.purple, Label("СЮРПРИЗЫ")))
	table.insert(out, Box(-5.8, 5.8, 10.6, 14, -1.5, -1.2, C.gold, DECOR))
	-- Товар: стол с чемоданами, подарки, ящик «?».
	table.insert(out, Box(-10, -1.5, 0.6, 3.2, 8, 12.5, C.wood))
	Put(out, FleaKit.Suitcases(), CFrame.new(-5.6, 3.2, 10.2) * CFrame.Angles(0, 0.15, 0))
	Put(out, FleaKit.GiftBoxes(), CFrame.new(3, 0.6, 9) * CFrame.Angles(0, -0.2, 0))
	table.insert(out, Box(7, 10.4, 0.6, 4, 5.2, 8.6, C.teal))
	table.insert(out, Board(V(2.6, 2.6, 0.2), V(8.7, 2.3, 5.1), C.goldLight, Label("?")))
	-- Лампа под коньком.
	table.insert(out, Box(-0.06, 0.06, 9.6, 10.3, 9.94, 10.06, C.metal, DECOR))
	table.insert(out, Neon(V(1.2, 1.2, 1.2), V(0, 9, 10), C.orangeLight))
	out[#out].light = lamp(18, C.orangeLight)
	return out
end

-- «Скупка» — два морских контейнера крест-накрест (26 × 16): нижний бирюзовый — лавка с поднятой шторкой, прилавком,
-- кассой и полками, неоновая лампа под потолком (свет); верхний оранжевый нависает над проходом, на нём вывеска в
-- неоновой раме; сбоку лестница, спереди ящики и мешок.
function FleaStalls.Containers(): { Brick }
	local out = {
		Box(-12, 12, 0, 0.6, 2, 16, C.graphite),
		Box(-11.2, 11.2, 0.6, 9, 15.2, 16, C.teal),
		Box(-12, -11.2, 0.6, 9, 2, 16, C.teal),
		Box(11.2, 12, 0.6, 9, 2, 16, C.teal),
		Box(-12.2, 12.2, 9, 9.8, 1.8, 16.2, C.tealDark),
		Box(-12.4, -11, 0, 9.9, 1.6, 2.4, C.orange),
		Box(11, 12.4, 0, 9.9, 1.6, 2.4, C.orange),
		-- Шторка поднята до половины.
		Box(-11.2, 11.2, 8, 9, 1.4, 2.3, C.graphiteDark),
		Box(-11, 11, 6.2, 8, 1.75, 1.95, C.metal, DECOR),
		Box(-11.1, 11.1, 6.8, 7, 1.65, 1.8, C.graphite, DECOR),
		Box(-11.1, 11.1, 7.4, 7.6, 1.65, 1.8, C.graphite, DECOR),
	}
	-- Рёбра стенок.
	for _, z in { 4, 6.4, 8.8, 11.2, 13.6 } do
		table.insert(out, Box(-12.25, -11.9, 0.9, 8.7, z - 0.3, z + 0.3, C.tealDark, DECOR))
		table.insert(out, Box(11.9, 12.25, 0.9, 8.7, z - 0.3, z + 0.3, C.tealDark, DECOR))
	end
	-- Внутри: полки с товаром, прилавок, касса, звонок, неоновая лампа (холодный свет).
	for _, y in { 3.4, 6 } do
		table.insert(out, Box(-10.5, 10.5, y, y + 0.3, 13.2, 15.2, C.metal, DECOR))
	end
	Put(out, FleaKit.Trophy(C.gold, 1.1, true), CFrame.new(-7, 3.7, 14.2))
	table.insert(out, Gem(1, V(-2, 4.4, 14.2), C.purpleLight))
	table.insert(out, Box(2, 4.6, 3.7, 5.4, 13.6, 14.8, C.red, DECOR))
	table.insert(out, B(V(0.3, 1.1, 1.1), CFrame.new(3.3, 4.55, 13.5) * FleaKit.ALONG_Z, C.graphite, FleaKit.ROUND))
	table.insert(out, Box(6, 8.4, 6.3, 8.1, 13.6, 14.8, C.blue, DECOR))
	table.insert(out, B(V(1.4, 1.4, 1.4), V(-5, 7, 14.2), C.goldLight, BALL))
	table.insert(out, Box(-8, 8, 0.6, 3.8, 3.4, 5.6, C.orange))
	table.insert(out, Box(-8.3, 8.3, 3.8, 4.2, 3.1, 5.9, C.graphiteDark))
	table.insert(out, Box(-7.8, 7.8, 2, 2.6, 3.25, 3.45, C.goldLight, DECOR))
	table.insert(out, Box(3, 6, 4.2, 5.6, 4, 5.4, C.graphite, DECOR))
	table.insert(out, Neon(V(2.2, 1, 0.2), CFrame.new(4.5, 6.1, 5) * CFrame.Angles(math.rad(-15), 0, 0), C.tealLight))
	table.insert(out, Disc(0.9, 4.2, 4.45, -5, 4.6, C.gold))
	table.insert(out, B(V(0.8, 0.8, 0.8), V(-5, 4.65, 4.6), C.gold, BALL))
	table.insert(out, Neon(V(16, 0.3, 0.4), V(0, 8.75, 9.2), C.tealLight))
	out[#out].light = lamp(18, C.tealLight)
	-- Верхний контейнер поперёк, нависает над проходом: двери с запорами спереди, рёбра по бокам.
	table.insert(out, Box(-5.5, 5.5, 9.8, 19, -3, 20, C.orange))
	table.insert(out, Box(-5.6, 5.6, 18.4, 19.1, -3.2, -2.8, C.orangeDark, DECOR))
	for _, x in { -3.2, -1, 1, 3.2 } do
		table.insert(out, Box(x - 0.15, x + 0.15, 10.4, 18.4, -3.25, -2.95, C.metal, DECOR))
	end
	for _, z in { 0, 3.5, 7, 10.5, 14, 17.5 } do
		table.insert(out, Box(-5.75, -5.4, 10.2, 18.6, z - 0.3, z + 0.3, C.orangeDark, DECOR))
		table.insert(out, Box(5.4, 5.75, 10.2, 18.6, z - 0.3, z + 0.3, C.orangeDark, DECOR))
	end
	-- Вывеска в неоновой раме на верхнем контейнере.
	table.insert(out, Board(V(14, 3.8, 0.5), V(0, 21.6, -2.2), C.graphiteDark, Label("СКУПКА")))
	table.insert(out, Neon(V(14.4, 0.3, 0.2), V(0, 23.65, -2.5), C.orange))
	table.insert(out, Neon(V(14.4, 0.3, 0.2), V(0, 19.55, -2.5), C.orange))
	table.insert(out, Neon(V(0.3, 4.3, 0.3), V(-7.15, 21.6, -2.5), C.orange))
	table.insert(out, Neon(V(0.3, 4.3, 0.3), V(7.15, 21.6, -2.5), C.orange))
	for _, x in { -4, 4 } do
		table.insert(out, Box(x - 0.3, x + 0.3, 19, 19.7, -2, 2, C.graphite, DECOR))
	end
	-- Лестница сбоку, ящики и мешок у входа.
	table.insert(out, B(V(2, 18, 2), V(13.4, 9, 10), C.metal, { shape = "Truss" }))
	Put(out, FleaKit.NeonCrates(), CFrame.new(-9.5, 0, -3) * CFrame.Angles(0, 0.3, 0))
	FleaKit.Sack(out, CFrame.new(9.5, 0, -1.6) * CFrame.Angles(0, -0.4, 0), 1.1)
	return out
end

-- «Ломбард» — сейф (26 × 16): помост, графитовый корпус с золотыми поясами, колонны, огромная круглая дверь сейфа со
-- штурвалом и болтами, вывеска, ступенчатый аттик с башенками, золотой ключ, воткнутый в крышу; у входа слитки и
-- мешок; настенные лампы (тёплый свет).
function FleaStalls.Vault(): { Brick }
	local out = {
		Box(-13, 13, 0, 0.8, 0, 16, C.graphiteDark),
		Box(-9, 9, 0, 0.4, -1.4, 0.2, C.graphiteLight),
		Box(-11.5, 11.5, 0.8, 14.5, 3, 16, C.graphite),
		Box(-11.7, 11.7, 0.8, 1.6, 2.8, 16.2, C.gold),
		Box(-11.7, 11.7, 10.4, 11, 2.8, 16.2, C.gold),
		Board(V(15, 2.6, 0.4), V(0, 12.6, 2.75), C.graphiteDark, Label("ЛОМБАРД")),
		Box(-7.8, 7.8, 11.1, 14.1, 2.7, 3.05, C.gold, DECOR),
		Box(-12.2, 12.2, 14.5, 15.5, 2.4, 16.6, C.gold),
		Box(-9.5, 9.5, 15.5, 16.8, 4, 15, C.graphite),
		Box(-6.5, 6.5, 16.8, 18, 5.6, 13.4, C.gold),
	}
	for _, x in { -11, 11 } do
		table.insert(out, Disc(2.6, 15.5, 18.5, x, 4.2, C.graphiteLight, SOLID))
		table.insert(out, B(V(1.8, 1.8, 1.8), V(x, 19.2, 4.2), C.gold, BALL))
	end
	for _, x in { -8.6, 8.6 } do
		table.insert(out, Disc(2, 1.6, 10.2, x, 1.6, C.gold, SOLID))
		table.insert(out, Box(x - 1.3, x + 1.3, 0.8, 1.6, 0.3, 2.7, C.goldDark))
		table.insert(out, Box(x - 1.3, x + 1.3, 10.2, 11.1, 0.3, 2.7, C.goldDark))
	end
	-- Дверь сейфа: обод, дверь, внутреннее кольцо, ступица, штурвал из трёх спиц с шарами, болты, петли.
	local door = CFrame.new(0, 6, 0)
	table.insert(out, Round(10, 0.8, door * CFrame.new(0, 0, 2.6), C.goldDark))
	table.insert(out, Round(8.6, 0.6, door * CFrame.new(0, 0, 2), C.gold))
	table.insert(out, Round(6, 0.3, door * CFrame.new(0, 0, 1.6), C.goldLight))
	table.insert(out, Round(2.2, 0.6, door * CFrame.new(0, 0, 1.2), C.graphite))
	for k = 0, 2 do
		table.insert(
			out,
			B(V(7, 0.45, 0.4), door * CFrame.new(0, 0, 0.9) * CFrame.Angles(0, 0, math.rad(k * 60)), C.goldDark, DECOR)
		)
	end
	for k = 0, 5 do
		local a = math.rad(k * 60)
		table.insert(
			out,
			B(V(0.8, 0.8, 0.8), door * CFrame.new(3.5 * math.cos(a), 3.5 * math.sin(a), 0.9), C.goldLight, BALL)
		)
	end
	for k = 0, 7 do
		local a = math.rad(22.5 + k * 45)
		table.insert(out, Round(0.6, 0.3, door * CFrame.new(4.65 * math.cos(a), 4.65 * math.sin(a), 2.1), C.goldLight))
	end
	table.insert(out, Box(4.6, 6, 7.5, 8.5, 1.6, 2.8, C.graphite, DECOR))
	table.insert(out, Box(4.6, 6, 3.5, 4.5, 1.6, 2.8, C.graphite, DECOR))
	-- Настенные лампы у двери.
	for _, x in { -6.2, 6.6 } do
		table.insert(out, Neon(V(0.8, 1.2, 0.5), V(x, 8.6, 2.7), C.goldLight))
	end
	out[#out].light = lamp(18, C.goldLight)
	-- Ключ, воткнутый в крышу: стержень, воротник, кольцо-бородка с «дыркой» и самоцветом, зубцы у крыши.
	local key = {
		Disc(1.3, 17.6, 27, 0, 0, C.gold, SOLID),
		Disc(2.2, 26.6, 27.6, 0, 0, C.goldDark),
		Round(7, 1.4, CFrame.new(0, 30.9, 0), C.gold, SOLID),
		Round(3.6, 1.6, CFrame.new(0, 30.9, 0), C.graphiteDark),
		Gem(1.8, V(0, 30.9, 0), C.purple),
		Box(0.6, 2.6, 18.6, 20, -0.4, 0.4, C.gold),
		Box(0.6, 1.9, 20.6, 21.6, -0.4, 0.4, C.gold),
		Disc(2.4, 23.4, 23.9, 0, 0, C.goldLight),
	}
	Put(out, key, CFrame.new(0, 0, 9.5) * CFrame.Angles(0, math.rad(-20), 0) * CFrame.Angles(0, 0, math.rad(6)))
	-- Слитки и мешок у входа.
	Put(out, FleaKit.GoldBars(), CFrame.new(-9.4, 0, -2.6) * CFrame.Angles(0, 0.25, 0))
	Put(out, FleaKit.GoldBars(), CFrame.new(10, 0, -2.4) * CFrame.Angles(0, -0.35, 0))
	FleaKit.Sack(out, CFrame.new(-12.4, 0, -3.2) * CFrame.Angles(0, 0.5, 0), 0.9)
	return out
end

-- Подарочная коробка с лентами крест-накрест (без банта): начало — центр низа.
local function gift(size: Vector3, color: Color3, ribbon: Color3): { Brick }
	local at = V(0, size.Y / 2, 0)
	return {
		B(size, at, color, DECOR),
		B(V(size.X * 0.22, size.Y + 0.1, size.Z + 0.1), at, ribbon, DECOR),
		B(V(size.X + 0.1, size.Y + 0.2, size.Z * 0.22), at, ribbon, DECOR),
	}
end

-- «Призы» — призовой терминал (24 × 16): здание-лавка, а не отдельный автомат. Большая открытая витрина — полки с
-- призами на тёмном фоне, стойка выдачи с люком и призом, экран и вывеска «ВЫДАЧА», полосатый
-- навес, световой короб с лампочками (средняя — свет павильона) и вывеской «ПРИЗЫ», звезда наверху, золотые колонны по углам. Куполов с
-- капсулами и рычагов, как у предмета «Легендарный автомат с призами», здесь нет.
function FleaStalls.PrizeTerminal(): { Brick }
	local out = {
		Box(-12, 12, 0, 0.4, 0, 16, C.purpleDark),
		Box(-11, 11, 0.4, 15, 5, 16, C.purple),
		Box(-12, 12, 15, 18.6, 3.6, 16.4, C.graphiteDark),
		Neon(V(23.6, 0.3, 0.3), V(0, 18.35, 3.45), C.orange),
		Board(V(14, 2.6, 0.3), V(0, 16.7, 3.45), C.orange, Label("ПРИЗЫ")),
		Box(-0.3, 0.3, 18.6, 19.6, 9.7, 10.3, C.gold, DECOR),
		B(V(3.4, 3.4, 0.5), V(0, 21.2, 10), C.gold, DECOR),
		B(V(3.4, 3.4, 0.6), CFrame.new(0, 21.2, 10) * CFrame.Angles(0, 0, math.rad(45)), C.goldLight, DECOR),
	}
	-- Лампочки по низу светового короба; средняя — свет павильона: ровно освещает витрину и стойку снаружи.
	for i = 0, 8 do
		local color = if i % 2 == 0 then C.goldLight else C.orange
		local bulb = FleaKit.With(BALL, { material = Enum.Material.Neon })
		table.insert(out, B(V(0.7, 0.7, 0.7), V(-10.4 + i * 2.6, 15.15, 3.4), color, bulb))
		if i == 4 then
			out[#out].light = lamp(20, C.purpleLight)
		end
	end
	for _, x in { -11.6, 11.6 } do
		table.insert(out, Box(x - 0.6, x + 0.6, 0.4, 15, 4.4, 5.6, C.gold))
	end
	-- Витрина: рама, тёмный фон, две полки, призы.
	table.insert(out, Box(-10, 2, 0.4, 3.2, 3.4, 5.2, C.purpleDark))
	table.insert(out, Box(-10, 2, 12.6, 14, 3.4, 5.2, C.purpleDark))
	table.insert(out, Box(-10, -9, 3.2, 12.6, 3.4, 5.2, C.purpleDark))
	table.insert(out, Box(1, 2, 3.2, 12.6, 3.4, 5.2, C.purpleDark))
	-- Витрина открытая (стекло отражало небо и прятало призы), фон тёмный, как у ювелирной витрины.
	local backdrop = { material = Enum.Material.SmoothPlastic, collide = false }
	table.insert(out, B(V(10, 9.4, 0.3), V(-4, 7.9, 4.95), C.purpleDark, backdrop))
	for _, y in { 6.2, 9.4 } do
		table.insert(out, Box(-9, 1, y, y + 0.3, 3.8, 4.8, C.metal, DECOR))
	end
	Put(out, gift(V(1.8, 1.5, 1.2), C.teal, C.goldLight), CFrame.new(-6.8, 3.2, 4.2))
	table.insert(out, B(V(1.6, 1.6, 1.6), V(-4, 4, 4.2), C.orange, BALL))
	Put(out, FleaKit.Trophy(C.gold, 1.2, true), CFrame.new(-1.2, 3.2, 4.2))
	table.insert(out, Gem(1.2, V(-7.4, 7.3, 4.2), C.purpleLight))
	Put(out, gift(V(1.6, 1.3, 1.1), C.red, C.cream), CFrame.new(-4.3, 6.5, 4.2) * CFrame.Angles(0, 0.3, 0))
	table.insert(out, B(V(1.4, 1.4, 1.4), V(-1.4, 7.2, 4.2), C.blue, BALL))
	Put(out, FleaKit.Trophy(C.silver, 0.9, true), CFrame.new(-7.2, 9.7, 4.2))
	table.insert(out, B(V(1.5, 1.5, 1.5), V(-4.4, 10.45, 4.2), C.teal, BALL))
	Put(out, gift(V(1.5, 1.2, 1.1), C.goldLight, C.purple), CFrame.new(-1.5, 9.7, 4.2) * CFrame.Angles(0, -0.25, 0))
	-- Стойка выдачи: прилавок, люк в золотой раме, приз на прилавке, экран, вывеска, звонок, навес.
	table.insert(out, Box(3.4, 11, 0.4, 4, 2.6, 5, C.teal))
	table.insert(out, Box(3.2, 11.2, 4, 4.3, 2.4, 5.1, C.cream))
	table.insert(out, Box(5, 9.6, 4.3, 8.9, 4.7, 5.1, C.gold))
	table.insert(out, Box(5.5, 9.1, 4.5, 8.5, 4.6, 4.9, C.graphiteDark, DECOR))
	Put(out, gift(V(1.8, 1.4, 1.4), C.purple, C.goldLight), CFrame.new(7.3, 4.3, 3.6) * CFrame.Angles(0, 0.2, 0))
	table.insert(out, Neon(V(5.8, 2.2, 0.2), V(7.3, 10.5, 4.85), C.teal))
	table.insert(out, Board(V(5.8, 1.1, 0.2), V(7.3, 12.45, 4.85), C.graphiteDark, Label("ВЫДАЧА")))
	table.insert(out, Disc(0.9, 4.3, 4.55, 4.2, 3.2, C.gold))
	table.insert(out, B(V(0.8, 0.8, 0.8), V(4.2, 4.6, 3.2), C.gold, BALL))
	for i, color in { C.teal, C.cream, C.teal } do
		local w = 8.4 / 3
		table.insert(out, B(V(w, 1.6, 3), V(3.2 + (i - 0.5) * w, 14, 3.5), color, WEDGE))
	end
	return out
end

-- Гора сокровищ с огромным сундуком — фон для босса (34 × 17, высота с крышкой ~22): широкая невысокая груда
-- золота из перекрывающихся «холмов» в два яруса с самородками, монетами и самоцветами, на ней обычный открытый
-- бирюзовый сундук, полный золота (тёплый свет), монеты, слитки и корона сверху, мешки у подножия; на предмет
-- «Живой сундук-мимик» (коричневый, с замком, глазами и зубами) не похож. Лицо — к −Z (к
-- боссу). Нижний ярус — без столкновений (на него можно зайти), спереди на нём только плоские монеты.
function FleaStalls.TreasureHoard(): { Brick }
	local LOWER, UPPER = 1.4, 4.6 -- верх ярусов (у среднего холма; боковые на 0.1 ниже — верх не совпадает, D36)
	local out = {}
	for i, x in { -9, 0, 9 } do
		local middle = i == 2
		local top = if middle then LOWER else LOWER - 0.1
		table.insert(out, Disc(13, 0, top, x, if middle then 0 else 0.6, if middle then C.goldDark else C.gold))
	end
	for i, x in { -7, 0, 7 } do
		local middle = i == 2
		local top = if middle then UPPER else UPPER - 0.1
		table.insert(out, Disc(10, LOWER - 0.1, top, x, 1.2, if middle then C.gold else C.goldLight, SOLID))
	end
	-- Самородки по бокам и сзади, впереди — плоские монеты.
	local nuggets = {
		{ -14, LOWER, -1, 2.6 },
		{ -13, LOWER, 3.6, 2.2 },
		{ 14, LOWER, -0.6, 2.8 },
		{ 13.4, LOWER, 4, 2.2 },
		{ -10.6, UPPER, 0.4, 2 },
		{ 10.8, UPPER, 1, 2.2 },
		{ -11, LOWER, -3.4, 1.8 },
		{ 11.2, LOWER, -3.6, 1.6 },
	}
	for i, n in nuggets do
		local color = if i % 3 == 0 then C.gold else C.goldLight
		table.insert(out, B(V(n[4], n[4], n[4]), V(n[1], n[2] + n[4] * 0.3, n[3]), color, BALL))
	end
	local flat = {
		{ -6, -5.2, 0.25 },
		{ -3.4, -6, 0.3 },
		{ 0.4, -6.2, 0.2 },
		{ 3.6, -5.6, 0.35 },
		{ 6.4, -5, 0.25 },
		{ -1.6, -4.4, 0.4 },
	}
	for _, c in flat do
		local coin = FleaKit.Coin(c[1], c[2], c[3], 2)
		coin.cframe = CFrame.new(0, LOWER, 0) * coin.cframe
		table.insert(out, coin)
	end
	local gems = {
		{ -8.4, UPPER + 0.6, -2.6, C.purple },
		{ 8.2, UPPER + 0.6, -2.4, C.teal },
		{ -13.4, LOWER + 1, 1.2, C.red },
		{ 12.6, LOWER + 1, 2, C.blue },
	}
	for _, g in gems do
		table.insert(out, Gem(1.6, V(g[1], g[2], g[3]), g[4]))
	end
	-- Сундук (в своих координатах низ — 0, ставится на верхний ярус) — обычный сундук сокровищ, не мимик: бирюзовый
	-- корпус с золотой оковкой и светлыми филёнками, вместо замка — монета-эмблема с самоцветом, ступенчатая крышка,
	-- внутри золото (тёплый свет), стопки монет, слитки и самоцветы; без шаров-«глаз», зубов и красного.
	local chest = {
		Box(-10, 10, 0.2, 8.7, -0.5, 8.5, C.tealDeep),
		Box(-10.4, -8.8, -0.05, 8.8, -0.9, 8.9, C.gold),
		Box(8.8, 10.4, -0.05, 8.8, -0.9, 8.9, C.gold),
		Box(-10.3, 10.3, 0, 1.1, -0.75, 8.75, C.goldDark),
		Box(-10.3, 10.3, 7.3, 8.3, -0.75, 8.75, C.goldDark),
		Box(-8.2, -1.6, 2, 6.6, -0.65, -0.45, C.teal),
		Box(1.6, 8.2, 2, 6.6, -0.65, -0.45, C.teal),
		Round(3.8, 0.5, CFrame.new(0, 4.4, -0.6), C.gold),
		Round(2.6, 0.3, CFrame.new(0, 4.4, -0.95), C.goldLight),
		Gem(1.1, V(0, 4.4, -1.25), C.purple),
		Box(-9.2, 9.2, 8.7, 9.9, 0.1, 7.9, C.goldLight),
	}
	chest[#chest].light = { range = 30, brightness = 1.6, color = C.goldLight }
	for i, x in { -4.9, 4.9 } do
		for j, y in { 3.2, 5.6 } do
			local color = if (i + j) % 2 == 0 then C.purpleLight else C.tealLight
			table.insert(chest, Gem(0.8, V(x + (j - 1.5) * 2.4, y, -0.75), color))
		end
	end
	-- Крышка: плита, ступень сверху, золотые кромки.
	local lid = CFrame.new(0, 8.7, 8.5) * CFrame.Angles(math.rad(100), 0, 0) * CFrame.new(0, 0.7, -4.5)
	table.insert(chest, B(V(20.4, 1.4, 9), lid, C.tealDeep))
	table.insert(chest, B(V(17.6, 1.2, 6.6), lid * CFrame.new(0, 1.2, 0), C.teal))
	table.insert(chest, B(V(20.8, 1.6, 1.2), lid * CFrame.new(0, 0, -3.9), C.gold, DECOR))
	for _, x in { -9.6, 9.6 } do
		table.insert(chest, B(V(1.6, 1.6, 9.2), lid * CFrame.new(x, 0, 0), C.gold, DECOR))
	end
	-- Сверху: стопки монет, монеты на ребре, слитки, самоцветы, корона.
	for _, stack in { { -6.2, 2.4, 1.2 }, { 5.6, 2.2, 1 }, { -2, 5.6, 0.8 }, { 6.6, 5.8, 0.7 } } do
		table.insert(chest, Disc(2.2, 9.9, 9.9 + stack[3], stack[1], stack[2], C.gold))
	end
	for i, c in { { -8, 1.2, 25 }, { -3.6, 1.6, -30 }, { 2.6, 1.4, 35 }, { 8.2, 4.6, -20 }, { -6.8, 6.4, 15 } } do
		local at = CFrame.new(c[1], 11, c[2] + 0.6) * CFrame.Angles(math.rad(c[3]), math.rad(i * 40), 0)
		table.insert(
			chest,
			B(V(0.35, 2.4, 2.4), at * FleaKit.UPRIGHT, if i % 2 == 0 then C.gold else C.goldDark, FleaKit.ROUND)
		)
	end
	for i, bar in { { -3.2, 3.2, 0.3 }, { 1.6, 4.6, -0.4 }, { 3.6, 1.8, 0.9 } } do
		local at = CFrame.new(bar[1], 10.2, bar[2]) * CFrame.Angles(0, bar[3], 0)
		table.insert(chest, B(V(2.2, 0.7, 1.1), at, if i % 2 == 0 then C.goldLight else C.gold, DECOR))
	end
	table.insert(chest, Gem(2, V(-7.4, 11.1, 6), C.purple))
	table.insert(chest, Gem(1.8, V(7.8, 10.9, 2.6), C.teal))
	table.insert(chest, Gem(1.5, V(0.8, 11, 6.8), C.blue))
	table.insert(chest, Disc(3.6, 9.7, 12.5, 2.2, 3.4, C.gold))
	for k = 0, 4 do
		local ang = math.rad(18 + k * 72)
		table.insert(
			chest,
			B(V(0.9, 0.9, 0.9), V(2.2 + 1.6 * math.cos(ang), 12.85, 3.4 + 1.6 * math.sin(ang)), C.goldLight, BALL)
		)
	end
	table.insert(chest, Gem(1, V(2.2, 12.3, 1.55), C.purpleLight))
	-- Монеты, свисающие через передний край.
	for i, x in { -5.4, 0.6, 6.2 } do
		local at = CFrame.new(x, 8.6, -0.9) * CFrame.Angles(math.rad(70 + i * 5), 0, math.rad(i * 12))
		table.insert(chest, B(V(0.3, 2, 2), at * FleaKit.UPRIGHT, C.gold, FleaKit.ROUND))
	end
	Put(out, chest, CFrame.new(0, UPPER - 0.1, 0))
	FleaKit.Sack(out, CFrame.new(-16.6, 0, -1.6) * CFrame.Angles(0, 0.4, 0), 1.2)
	FleaKit.Sack(out, CFrame.new(16.8, 0, -1) * CFrame.Angles(0, -0.5, 0), 1.05)
	return out
end

-- Гигантские карманные часы (12 × 19): тумба с ложементом, часы с наклоном назад — корпус, золотой ободок,
-- циферблат с метками, стрелки, заводная головка с кольцом и цепочка.
function FleaStalls.PocketWatch(): { Brick }
	local out = {
		Box(-4.5, 4.5, 0, 1.2, -2.5, 2.5, C.graphite),
		Box(-4.65, 4.65, 0.3, 0.9, -2.65, 2.65, C.gold, DECOR),
		Box(-5.6, -3.4, 1.2, 4.4, -1.4, 1.4, C.graphiteDark),
		Box(3.4, 5.6, 1.2, 4.4, -1.4, 1.4, C.graphiteDark),
	}
	local watch = {
		Round(12.4, 2.2, CFrame.new(), C.goldDark, SOLID),
		Round(11.6, 0.6, CFrame.new(0, 0, -1), C.gold),
		Round(10, 0.4, CFrame.new(0, 0, -1.35), C.cream),
		Round(0.9, 0.5, CFrame.new(0, 0, -1.9), C.gold),
		Disc(1.6, 6, 7.4, 0, 0, C.gold),
		Disc(2.6, 7.4, 8.6, 0, 0, C.goldDark),
		Round(3.6, 0.6, CFrame.new(0, 10.1, 0), C.gold),
		Round(2, 0.8, CFrame.new(0, 10.1, 0), C.graphiteDark),
	}
	for k = 0, 11 do
		local a = math.rad(k * 30)
		local major = k % 3 == 0
		local at = CFrame.new(4.1 * math.sin(a), 4.1 * math.cos(a), -1.6) * CFrame.Angles(0, 0, -a)
		table.insert(
			watch,
			B(V(if major then 0.5 else 0.3, if major then 1.3 else 0.7, 0.2), at, C.graphiteDark, DECOR)
		)
	end
	for _, hand in
		{
			{ 3, 0.55, -60, -1.7, C.graphiteDark },
			{ 4.2, 0.4, 150, -1.78, C.graphiteDark },
			{ 4.4, 0.16, 215, -1.84, C.red },
		}
	do
		local at = CFrame.new(0, 0, hand[4])
			* CFrame.Angles(0, 0, math.rad(-hand[3]))
			* CFrame.new(0, hand[1] * 0.42, 0)
		table.insert(watch, B(V(hand[2], hand[1], 0.08), at, hand[5], DECOR))
	end
	Put(out, watch, CFrame.new(0, 7.6, 0.4) * CFrame.Angles(math.rad(10), 0, 0))
	-- Цепочка: звенья от кольца вниз к тумбе.
	for i, p in
		{
			{ 2.2, 16.2, 2.2 },
			{ 3.8, 14.6, 2.4 },
			{ 5.2, 12.8, 2.2 },
			{ 6.2, 10.6, 1.8 },
			{ 6.6, 8.2, 1.2 },
			{ 6.4, 5.6, 0.6 },
		}
	do
		table.insert(out, B(V(0.9, 0.9, 0.9), V(p[1], p[2], p[3]), if i % 2 == 0 then C.gold else C.goldDark, BALL))
	end
	return out
end

-- Стопка гигантских монет (14 × 11): восемь монет со сдвигом, рельеф-кольцо на верхней, монета на ребре
-- прислонена к стопке, две монеты на полу.
function FleaStalls.CoinStack(): { Brick }
	local out = {}
	local y = 0
	local shifts = {
		{ 0, 0 },
		{ 0.5, -0.3 },
		{ -0.2, 0.4 },
		{ 0.6, 0.2 },
		{ 0.1, -0.2 },
		{ -0.4, 0.3 },
		{ 0.3, 0.5 },
		{ 0, -0.1 },
	}
	for i, shift in shifts do
		table.insert(out, Disc(8, y, y + 1.2, shift[1], shift[2], if i % 2 == 0 then C.goldDark else C.gold, SOLID))
		y += 1.2
	end
	table.insert(out, Disc(5.6, y, y + 0.15, 0, -0.1, C.goldLight))
	table.insert(out, Gem(1.6, V(0, y + 1, -0.1), C.teal))
	local edge = CFrame.new(-6.8, 4.3, -0.8) * CFrame.Angles(0, math.rad(-20), math.rad(-12))
	table.insert(out, Round(8.6, 1.2, edge, C.gold, SOLID))
	table.insert(out, Round(6, 1.4, edge, C.goldLight))
	table.insert(out, Gem(1.6, (edge * CFrame.new(0, 0, -1)).Position, C.purple))
	table.insert(out, FleaKit.Coin(4.8, -3.4, 0.3, 2.6))
	table.insert(out, FleaKit.Coin(2.4, -4.8, 0.4, 2.2))
	return out
end

-- Мачта-символ: столб, кронштейн к −Z и подвешенный знак: ценник с надписью text (с обеих сторон) или, без text,
-- огромная монета с самоцветом.
function FleaStalls.SymbolMast(text: string?): { Brick }
	local out = {
		Box(-1, 1, 0, 0.6, -1, 1, C.graphite),
		Box(-0.4, 0.4, 0.6, 22, -0.4, 0.4, C.graphiteDark),
		Box(-0.55, 0.55, 7, 7.8, -0.55, 0.55, C.gold, DECOR),
		Box(-0.25, 0.25, 21.4, 21.9, -6.4, 0.3, C.graphiteDark, DECOR),
		B(V(0.8, 0.8, 0.8), V(0, 22.4, 0), C.gold, BALL),
	}
	if text then
		local tag = CFrame.new(0, 15, -4.8) * CFrame.Angles(math.rad(8), 0, 0)
		table.insert(out, Box(-0.06, 0.06, 18.3, 21.4, -4.86, -4.74, C.metal, DECOR))
		table.insert(out, Board(V(0.4, 5.4, 3.8), tag, C.orange, Label(text, SIDES)))
		table.insert(
			out,
			B(V(0.4, 2.69, 2.69), tag * CFrame.new(0, 2.7, 0) * CFrame.Angles(math.rad(45), 0, 0), C.orange, DECOR)
		)
		table.insert(out, B(V(0.6, 0.9, 0.9), tag * CFrame.new(0, 3.2, 0), C.cream, FleaKit.ROUND))
		table.insert(out, B(V(0.3, 5.9, 4.4), tag * CFrame.new(0, -0.35, 0), C.goldDark, DECOR))
	else
		table.insert(out, Box(-0.06, 0.06, 18.2, 21.4, -4.86, -4.74, C.metal, DECOR))
		table.insert(out, B(V(0.8, 6.4, 6.4), V(0, 15, -4.8), C.gold, FleaKit.ROUND))
		table.insert(out, B(V(1, 4.6, 4.6), V(0, 15, -4.8), C.goldLight, FleaKit.ROUND))
		table.insert(out, Gem(1.6, V(0, 15, -4.8), C.purple))
	end
	return out
end

-- Тележка с зонтом (7 × 11): корпус на двух колёсах с опорой, прилавок с товаром, зонт ступенями двух цветов с
-- золотой кромкой и шариком.
function FleaStalls.UmbrellaCart(color: Color3, stripe: Color3): { Brick }
	local out = {
		Box(-3, 3, 1.4, 3.6, -1.6, 1.6, color),
		Box(-3.3, 3.3, 3.6, 3.9, -1.9, 1.9, C.cream),
		Box(-3.1, 3.1, 2.2, 2.6, -1.7, 1.7, C.gold, DECOR),
		Box(2.2, 2.7, 0, 1.4, -0.4, 0.4, C.graphiteDark),
		Round(2.8, 0.4, CFrame.new(-1.4, 1.4, -1.85), C.graphiteDark),
		Round(2.8, 0.4, CFrame.new(-1.4, 1.4, 1.85), C.graphiteDark),
		Round(1, 0.6, CFrame.new(-1.4, 1.4, -1.9), C.gold),
		Round(1, 0.6, CFrame.new(-1.4, 1.4, 1.9), C.gold),
		Disc(0.35, 3.9, 9.4, 0.6, 0, C.metal),
		Disc(8.6, 8.4, 8.7, 0.6, 0, C.goldLight),
		Disc(8.2, 8.6, 9.1, 0.6, 0, color),
		Disc(6.8, 9.1, 9.6, 0.6, 0, stripe),
		Disc(5, 9.6, 10.1, 0.6, 0, color),
		Disc(2.8, 10.1, 10.6, 0.6, 0, stripe),
		B(V(1, 1, 1), V(0.6, 11, 0), C.gold, BALL),
		Gem(0.8, V(-2, 4.5, -0.4), C.purpleLight),
		Gem(0.7, V(2.2, 4.45, 0.3), C.tealLight),
		Disc(1, 3.9, 4.5, 1.2, -0.6, C.gold),
	}
	Put(out, FleaKit.Trophy(C.gold, 0.9, true), CFrame.new(-0.6, 3.9, 0.4))
	return out
end

-- Золотая башня-прожектор (4 × 25): тумба, бирюзовая колонна с золотыми кольцами, фонарь на макушке (неон в золотых
-- стойках, крыша ступенями, шар), знамя цвета banner и прожектор на высоте 13.5 — мягко светит на target (в
-- координатах башни).
function FleaStalls.LightTower(target: Vector3, banner: Color3): { Brick }
	local out = {
		Box(-1.8, 1.8, 0, 1, -1.8, 1.8, C.graphite),
		Box(-1.95, 1.95, 0.6, 1.2, -1.95, 1.95, C.gold, DECOR),
		Disc(1.8, 1, 19.5, 0, 0, C.teal, SOLID),
		Box(-1.6, 1.6, 19.5, 20, -1.6, 1.6, C.goldDark),
		Neon(V(1.6, 2.4, 1.6), V(0, 21.2, 0), C.orangeLight),
		Box(-1.8, 1.8, 22.4, 23, -1.8, 1.8, C.gold),
		Box(-1.1, 1.1, 23, 23.7, -1.1, 1.1, C.goldDark),
		B(V(1.2, 1.2, 1.2), V(0, 24.3, 0), C.goldLight, BALL),
		Box(-0.15, 0.15, 14.5, 15, -0.15, 3.4, C.graphiteDark, DECOR),
		B(V(0.2, 5.6, 2.4), V(0, 11.9, 2.4), banner, DECOR),
		B(V(0.3, 1.7, 1.7), CFrame.new(0, 9.1, 2.4) * CFrame.Angles(math.rad(45), 0, 0), C.gold, DECOR),
	}
	for _, y in { 6, 11, 16 } do
		table.insert(out, Disc(2.3, y, y + 0.6, 0, 0, C.gold))
	end
	for _, x in { -1.25, 1.25 } do
		for _, z in { -1.25, 1.25 } do
			table.insert(out, Box(x - 0.2, x + 0.2, 20, 22.4, z - 0.2, z + 0.2, C.gold, DECOR))
		end
	end
	-- Прожектор на высоте 13.5 под знаменем: свет ложится на корпус босса, а не только на макушку; яркость 1 —
	-- в Studio при 3 верх босса засвечивался до белого (2026-11-04).
	local from = V(0, 13.5, 0)
	local head = CFrame.lookAt(from + (target - from).Unit * 1.8, target)
	table.insert(
		out,
		B(V(2, 1.6, 2.4), head, C.graphiteDark, {
			collide = false,
			shadow = false,
			light = { range = 46, brightness = 1, color = C.spot, angle = 60 },
		})
	)
	table.insert(out, Neon(V(1.6, 1.2, 0.2), head * CFrame.new(0, 0, -1.25), C.goldLight))
	return out
end

-- Гирлянда флажков вдоль X от 0 до length на высоте top с провисом sag посередине: шнур из двух отрезков и
-- флажки-ромбики через шаг около step по очереди цветов colors.
function FleaStalls.Bunting(length: number, top: number, sag: number, step: number, colors: { Color3 }): { Brick }
	local out = {}
	local function y(x: number): number
		return top - sag * (1 - math.abs(2 * x / length - 1))
	end
	for half = 0, 1 do
		local x0, x1 = half * length / 2, (half + 1) * length / 2
		local a, b = V(x0, y(x0), 0), V(x1, y(x1), 0)
		table.insert(out, B(V(0.12, 0.12, (b - a).Magnitude), CFrame.lookAt((a + b) / 2, b), C.graphiteDark, DECOR))
	end
	local count = math.floor(length / step)
	for i = 1, count - 1 do
		local x = i * length / count
		local at = CFrame.new(x, y(x) - 0.75, 0) * CFrame.Angles(0, 0, math.rad(45))
		table.insert(out, B(V(1, 1, 0.1), at, colors[(i - 1) % #colors + 1], DECOR))
	end
	return out
end

-- Штабель контейнеров (за павильонами): контейнеры 12 × 5 × 5 цветов colors друг на друге, каждый следующий повёрнут
-- на turn; у каждого запоры дверей с торца и тёмная кромка крыши.
function FleaStalls.ContainerStack(colors: { Color3 }, turn: number): { Brick }
	local out = {}
	for i, color in colors do
		local at = CFrame.new(0, (i - 0.5) * 5, 0) * CFrame.Angles(0, (i - 1) * turn, 0)
		table.insert(out, B(V(12, 5, 5), at, color))
		table.insert(out, B(V(12.2, 0.4, 5.2), at * CFrame.new(0, 2.4, 0), color:Lerp(C.graphiteDark, 0.45), DECOR))
		for _, z in { -0.9, 0.9 } do
			table.insert(out, B(V(0.25, 4, 0.25), at * CFrame.new(-6.1, 0, z), C.metal, DECOR))
		end
	end
	return out
end

-- Рекламный щит на обрыве (24 × 9, низ на высоте 19): рама, табличка с надписью text цвета color, неоновые полосы
-- сверху и снизу, кронштейны в стену обрыва (сторона +Z).
function FleaStalls.Billboard(text: string, color: Color3): { Brick }
	return {
		Box(-12.6, 12.6, 19.4, 27.8, 0, 0.6, C.graphiteDark),
		Board(V(24, 7.2, 0.4), V(0, 23.6, -0.1), color, Label(text)),
		Neon(V(25.2, 0.4, 0.4), V(0, 28, -0.1), C.goldLight),
		Neon(V(25.2, 0.4, 0.4), V(0, 19.2, -0.1), C.goldLight),
		Box(-9, -8, 18, 19.4, 0, 1.4, C.graphite, DECOR),
		Box(8, 9, 18, 19.4, 0, 1.4, C.graphite, DECOR),
	}
end

return FleaStalls

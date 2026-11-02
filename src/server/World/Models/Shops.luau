-- Лавки безопасной зоны (D41): «Продажа» и «Аура» — по одной на каждом краю у входа в коридор (MapLayout.Shops).
-- Только оформление: что продаёт «Продажа» и что даёт «Аура» — не решено (NEXT_TASK), механики здесь нет.
-- «Продажа» — торговый павильон: зелёная крыша с золотой каймой, полосатый навес, прилавок с кассой, весами (на
-- одной чаше монеты, на другой — ваза: обмен добычи на деньги), стопки монет, мешки и сундук с золотом, полки с
-- товаром, над крышей вращается большая монета «$». «Аура» — магическая беседка: круглый помост с магическим кругом,
-- пять колонн с парящими кристаллами, алтарь, над ним вращается большой кристалл, вокруг плавают огоньки цветов аур.
-- Названия — голограммы (WorldBuilder). Начало координат — центр основания, лицо — сторона −Z. Детали с именем
-- Spin вращаются, Bob — плавают (WorldBuilder ставит теги, анимирует ZoneController). Зависит от ModelBuilder,
-- Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

type Brick = ModelBuilder.Brick

local B = ModelBuilder.Brick
local DECOR = { collide = false, shadow = false }
local UPRIGHT = CFrame.Angles(0, 0, math.rad(90))
local ALONG_Z = CFrame.Angles(0, math.rad(90), 0)
local DIAMOND = CFrame.Angles(math.rad(45), 0, math.rad(45)) -- куб на вершине: кристалл

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

local Shops = {}

Shops.SellTitleHeight = 22.6 -- центр голограммы «ПРОДАЖА» над основанием
Shops.AuraTitleHeight = 17.5

local function neon(size: Vector3, at: CFrame | Vector3, color: Color3, range: number?, name: string?): Brick
	return B(size, at, color, {
		material = Enum.Material.Neon,
		collide = false,
		shadow = false,
		name = name,
		light = if range then { range = range, brightness = 1.4, color = color } else nil,
	})
end

function Shops.Sell(): { Brick }
	local green, greenDark = hex("2EBD4E"), hex("1F8F3A")
	local gold, goldDark = hex("F2C230"), hex("C9952A")
	local cream, stone = hex("F3EFE6"), hex("D9D4C7")
	local wood, woodDark = Palette.Wood, Palette.WoodDark
	local bricks: { Brick } = {
		-- помост, ступень
		B(Vector3.new(26, 0.6, 20), Vector3.new(0, 0.3, 0), stone),
		B(Vector3.new(14, 0.3, 2), Vector3.new(0, 0.15, -10.9), hex("C9C2B2")),
		-- задняя стена (концы внутри боковых), боковые стены
		B(Vector3.new(22.6, 9.6, 1), Vector3.new(0, 5.4, 9), cream),
		B(Vector3.new(1, 9.6, 10), Vector3.new(-11.5, 5.4, 4), cream),
		B(Vector3.new(1, 9.6, 10), Vector3.new(11.5, 5.4, 4), cream),
		B(Vector3.new(22.6, 0.6, 0.2), Vector3.new(0, 1.2, 8.45), greenDark, DECOR), -- цоколь стены
		-- крыша: зелёная плита, золотая кайма, верхняя ступень
		B(Vector3.new(26, 0.8, 20), Vector3.new(0, 10.6, 0.5), green),
		B(Vector3.new(26.4, 0.4, 20.4), Vector3.new(0, 11.2, 0.5), gold),
		B(Vector3.new(22, 0.8, 16), Vector3.new(0, 11.8, 0.5), greenDark),
		-- прилавок с золотой полосой
		B(Vector3.new(16, 3, 2.4), Vector3.new(0, 2.1, -5), wood),
		B(Vector3.new(16.8, 0.4, 3), Vector3.new(0, 3.8, -5), woodDark),
		B(Vector3.new(14, 0.7, 0.12), Vector3.new(0, 2.6, -6.24), gold, DECOR),
		-- касса: корпус, зелёное табло, клавиши
		B(Vector3.new(2.2, 1.2, 1.6), Vector3.new(-5.5, 4.6, -5), hex("5A6270")),
		B(Vector3.new(1.5, 0.6, 0.12), CFrame.new(-5.5, 5.5, -5.55) * CFrame.Angles(math.rad(-20), 0, 0), hex("43E05A"), {
			material = Enum.Material.Neon,
			collide = false,
			shadow = false,
		}),
		B(Vector3.new(1.8, 0.14, 0.7), Vector3.new(-5.5, 5.27, -5.4), hex("E3E6EA"), DECOR),
		-- весы: на левой чаше монеты, на правой — ваза (обмен добычи на деньги)
		B(Vector3.new(1.6, 0.3, 1.2), Vector3.new(0, 4.15, -5), goldDark),
		B(Vector3.new(0.36, 2.4, 0.36), Vector3.new(0, 5.5, -5), gold, DECOR),
		B(Vector3.new(4.2, 0.25, 0.25), Vector3.new(0, 6.75, -5), gold, DECOR),
		B(Vector3.new(0.5, 0.5, 0.5), Vector3.new(0, 6.95, -5), goldDark, { shape = "Ball", collide = false }),
	}
	for _, x in { -1.95, 1.95 } do
		table.insert(bricks, B(Vector3.new(0.08, 0.9, 0.08), Vector3.new(x, 6.2, -5), Palette.Metal, DECOR))
		table.insert(bricks, B(Vector3.new(0.15, 1.6, 1.6), CFrame.new(x, 5.6, -5) * UPRIGHT, gold, { shape = "Cylinder", collide = false }))
	end
	for i = 0, 2 do
		table.insert(bricks, B(Vector3.new(0.2, 0.7 - i * 0.08, 0.7 - i * 0.08), CFrame.new(-1.95, 5.775 + i * 0.2, -5) * UPRIGHT, gold, DECOR))
	end
	table.insert(bricks, B(Vector3.new(0.6, 0.8, 0.6), Vector3.new(1.95, 6.08, -5), hex("2F6BD8"), DECOR)) -- ваза
	table.insert(bricks, B(Vector3.new(0.36, 0.3, 0.36), Vector3.new(1.95, 6.62, -5), hex("2F6BD8"), DECOR))
	-- стопки монет на прилавке
	for i, h in { 1.2, 0.8, 1.6 } do
		local x = 3.6 + i * 1.3
		table.insert(bricks, B(Vector3.new(h, 1.0, 1.0), CFrame.new(x, 4 + h / 2, -5 + (i % 2) * 0.3) * UPRIGHT, gold, {
			shape = "Cylinder",
			collide = false,
		}))
	end
	-- мешки с деньгами у прилавка
	for _, bag in { { -9.2, 2.6 }, { -7.2, 1.8 } } do
		local x, size = bag[1], bag[2]
		table.insert(bricks, B(Vector3.new(size, size, size), Vector3.new(x, 0.6 + size / 2 - 0.1, -4.2), hex("D8B98A"), {
			shape = "Ball",
		}))
		table.insert(bricks, B(Vector3.new(size * 0.38, size * 0.25, size * 0.38), Vector3.new(x, 0.6 + size - 0.05, -4.2), woodDark, DECOR))
		table.insert(bricks, B(Vector3.new(size * 0.28, size * 0.3, size * 0.28), Vector3.new(x, 0.6 + size + 0.2, -4.2), hex("D8B98A"), DECOR))
	end
	-- сундук с золотом, крышка откинута
	table.insert(bricks, B(Vector3.new(3, 1.8, 2), Vector3.new(8.6, 1.5, -3.2), wood))
	table.insert(bricks, B(Vector3.new(3.1, 0.3, 2.1), Vector3.new(8.6, 1.2, -3.2), gold, DECOR))
	table.insert(bricks, B(Vector3.new(2.6, 0.5, 1.6), Vector3.new(8.6, 2.55, -3.2), gold, DECOR))
	table.insert(bricks, B(Vector3.new(3, 0.3, 2), CFrame.new(8.6, 3.0, -1.75) * CFrame.Angles(math.rad(65), 0, 0), woodDark, DECOR))
	-- полки на задней стене с товаром (вазы, рамы, статуэтки)
	local goods = { hex("E53935"), hex("2F6BD8"), hex("F2C230"), hex("8E44AD"), hex("43A047"), hex("FB8C00") }
	for row, y in { 4.4, 7.2 } do
		table.insert(bricks, B(Vector3.new(18, 0.3, 1.4), Vector3.new(0, y, 7.9), woodDark))
		for i = 1, 6 do
			local x = -7.5 + (i - 1) * 3 + (row - 1) * 0.8
			local h = 0.8 + ((i + row) % 3) * 0.35
			table.insert(bricks, B(Vector3.new(0.9, h, 0.8), Vector3.new(x, y + 0.15 + h / 2, 7.8), goods[(i + row) % #goods + 1], DECOR))
		end
	end
	-- колонны с золотыми капителями
	for _, x in { -11.5, 11.5 } do
		table.insert(bricks, B(Vector3.new(1.4, 9, 1.4), Vector3.new(x, 5.1, -8), Palette.White))
		table.insert(bricks, B(Vector3.new(1.8, 0.6, 1.8), Vector3.new(x, 9.9, -8), gold))
		table.insert(bricks, B(Vector3.new(1.8, 0.4, 1.8), Vector3.new(x, 0.8, -8), gold))
	end
	-- полосатый навес над прилавком
	local stripes = 8
	local width = 24 / stripes
	local tilt = CFrame.new(0, 9.5, -11.4) * CFrame.Angles(math.rad(-25), 0, 0)
	for i = 1, stripes do
		local x = -12 + (i - 0.5) * width
		table.insert(bricks, B(Vector3.new(width, 0.3, 4.4), tilt * CFrame.new(x, 0, 0), if i % 2 == 0 then Palette.White else green, DECOR))
	end
	-- тёплые лампы под крышей
	for _, x in { -6, 6 } do
		table.insert(bricks, neon(Vector3.new(0.9, 0.9, 0.9), Vector3.new(x, 9.75, -2), Palette.Lamp, 16))
	end
	-- большая монета «$» над крышей (вращается): ребро и лицевой диск
	table.insert(bricks, B(Vector3.new(1.0, 7.6, 7.6), CFrame.new(0, 16.4, 2) * ALONG_Z, goldDark, {
		shape = "Cylinder",
		collide = false,
		name = "Spin",
	}))
	table.insert(bricks, B(Vector3.new(1.2, 7, 7), CFrame.new(0, 16.4, 2) * ALONG_Z, gold, {
		shape = "Cylinder",
		collide = false,
		name = "Spin",
	}))
	return bricks
end

function Shops.Aura(): { Brick }
	local base, tier = hex("3B2A6B"), hex("5B3FA0")
	local lilac, marble, gold = hex("8E6FD6"), hex("EDE7FF"), hex("F2C230")
	local glow = { hex("5CE1FF"), hex("FF6AD5"), hex("B98CFF"), hex("FFE45A"), hex("6CFF9E") }
	local bricks: { Brick } = {
		-- круглый помост в два яруса, ступень, магический круг
		B(Vector3.new(0.8, 24, 24), CFrame.new(0, 0.4, 0) * UPRIGHT, base, { shape = "Cylinder" }),
		B(Vector3.new(0.6, 19, 19), CFrame.new(0, 1.1, 0) * UPRIGHT, tier, { shape = "Cylinder" }),
		B(Vector3.new(8, 0.4, 3), Vector3.new(0, 0.2, -12.6), base),
		B(Vector3.new(0.06, 15, 15), CFrame.new(0, 1.43, 0) * UPRIGHT, hex("C77DFF"), {
			shape = "Cylinder",
			material = Enum.Material.Neon,
			collide = false,
			shadow = false,
		}),
		B(Vector3.new(0.08, 13.8, 13.8), CFrame.new(0, 1.45, 0) * UPRIGHT, tier, { shape = "Cylinder", collide = false }),
		-- алтарь
		B(Vector3.new(3.4, 1.6, 3.4), Vector3.new(0, 2.2, 2), lilac),
		B(Vector3.new(2.4, 0.6, 2.4), Vector3.new(0, 3.3, 2), gold),
		-- большой кристалл над алтарём (вращается и светится)
		B(Vector3.new(3, 3, 3), CFrame.new(0, 7.2, 2) * DIAMOND, glow[2], {
			material = Enum.Material.Neon,
			collide = false,
			shadow = false,
			name = "Spin",
			light = { range = 30, brightness = 2, color = glow[2] },
		}),
	}
	-- пять колонн по кругу (спереди проход), капители, парящие кристаллы
	local radius = 8.5
	local pillars = {}
	for i, angle in { -120, -60, 0, 60, 120 } do
		local a = math.rad(angle)
		local p = Vector3.new(radius * math.sin(a), 0, radius * math.cos(a))
		table.insert(pillars, p)
		table.insert(bricks, B(Vector3.new(2.2, 0.6, 2.2), Vector3.new(p.X, 1.7, p.Z), lilac))
		table.insert(bricks, B(Vector3.new(1.6, 8.8, 1.6), Vector3.new(p.X, 6.0, p.Z), marble))
		table.insert(bricks, B(Vector3.new(2.2, 0.6, 2.2), Vector3.new(p.X, 10.7, p.Z), gold))
		local color = glow[(i - 1) % #glow + 1]
		table.insert(bricks, B(Vector3.new(1.5, 1.5, 1.5), CFrame.new(p.X, 12.3, p.Z) * DIAMOND, color, {
			material = Enum.Material.Neon,
			collide = false,
			shadow = false,
			name = "Bob",
			light = { range = 12, brightness = 1.2, color = color },
		}))
	end
	-- золотые балки между колоннами (кроме прохода спереди)
	for i = 1, #pillars - 1 do
		local a, b = pillars[i], pillars[i + 1]
		local mid = (a + b) / 2
		local d = b - a
		local at = CFrame.new(mid.X, 11.2, mid.Z) * CFrame.Angles(0, -math.atan2(d.Z, d.X), 0)
		table.insert(bricks, B(Vector3.new(d.Magnitude, 0.4, 0.6), at, gold, DECOR))
	end
	-- огоньки цветов аур вокруг алтаря
	for i, color in glow do
		local a = math.rad(i * 72)
		table.insert(bricks, B(Vector3.new(0.8, 0.8, 0.8), Vector3.new(3.6 * math.cos(a), 4.6 + (i % 3) * 0.8, 2 + 3.6 * math.sin(a)), color, {
			shape = "Ball",
			material = Enum.Material.Neon,
			collide = false,
			shadow = false,
			name = "Bob",
		}))
	end
	return bricks
end

return Shops

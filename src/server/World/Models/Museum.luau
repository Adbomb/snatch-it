-- Здание музея из кирпичей (V2): цветные стены, фасад с колоннами и ступенями, двускатная крыша, окна,
-- флажки, пол в шахматку; декор витрины (основание, колпак, канаты), подвесная лампа и сундук.
-- Начало координат — центр участка на уровне пола, вход — сторона -Z. Части с механикой (Floor, витрины
-- Showcase_i, Chest, табличка) строит Util/PartBuilder; здесь только их окружение.
-- Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick
local DECOR = { collide = false, shadow = false }

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

Museum.Size = 44
Museum.WallHeight = 14
Museum.FacadeZ = -19 -- фасадная стена (перед ней портик с колоннами)
Museum.Entrance = Vector2.new(12, 10) -- ширина и высота проёма
Museum.RoofHeight = 8
Museum.SignY = 11.5

local CREAM = hex("FFF1D2")
local FLOOR_A, FLOOR_B = hex("F3E5C0"), hex("C9B48A")
local GOLD = hex("FFC21A")
local VELVET = hex("B71C1C")

function Museum.Building(accent: Color3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	local half = Museum.Size / 2
	local h = Museum.WallHeight
	local wallBase = accent:Lerp(Palette.Black, 0.35)
	local roof = accent:Lerp(Palette.Black, 0.5)
	local facadeZ = Museum.FacadeZ

	-- Стены: боковые и задняя, тёмный цоколь и светлый карниз.
	local depth = half - facadeZ
	local midZ = (half + facadeZ) / 2
	for _, x in { -half + 0.5, half - 0.5 } do
		table.insert(bricks, B(Vector3.new(1, h, depth), Vector3.new(x, h / 2, midZ), accent))
		table.insert(bricks, B(Vector3.new(1.4, 1.5, depth), Vector3.new(x, 0.75, midZ), wallBase))
		table.insert(bricks, B(Vector3.new(1.6, 1, depth + 0.6), Vector3.new(x, h - 0.5, midZ), CREAM))
	end
	table.insert(bricks, B(Vector3.new(Museum.Size, h, 1), Vector3.new(0, h / 2, half - 0.5), accent))
	table.insert(bricks, B(Vector3.new(Museum.Size, 1.5, 1.4), Vector3.new(0, 0.75, half - 0.5), wallBase))

	-- Фасад: стена с проёмом входа и перемычкой.
	local entrance = Museum.Entrance
	local sideWidth = (Museum.Size - entrance.X) / 2
	for _, sign in { -1, 1 } do
		local x = sign * (entrance.X / 2 + sideWidth / 2)
		table.insert(bricks, B(Vector3.new(sideWidth, h, 1), Vector3.new(x, h / 2, facadeZ), accent))
		table.insert(bricks, B(Vector3.new(sideWidth, 1.5, 1.4), Vector3.new(x, 0.75, facadeZ), wallBase))
	end
	table.insert(bricks, B(Vector3.new(entrance.X, h - entrance.Y, 1), Vector3.new(0, (h + entrance.Y) / 2, facadeZ), accent))
	-- Рамка проёма.
	for _, x in { -entrance.X / 2 - 0.3, entrance.X / 2 + 0.3 } do
		table.insert(bricks, B(Vector3.new(0.6, entrance.Y, 1.4), Vector3.new(x, entrance.Y / 2, facadeZ), CREAM, DECOR))
	end
	table.insert(bricks, B(Vector3.new(entrance.X + 1.2, 0.6, 1.4), Vector3.new(0, entrance.Y + 0.3, facadeZ), CREAM, DECOR))

	-- Портик: 4 колонны (база, ствол, капитель) перед фасадом.
	local columnZ = -half + 1.2
	for _, x in { -16, -9, 9, 16 } do
		table.insert(bricks, B(Vector3.new(2.4, 0.8, 2.4), Vector3.new(x, 0.4, columnZ), CREAM))
		table.insert(bricks, B(Vector3.new(1.6, h - 1.6, 1.6), Vector3.new(x, h / 2, columnZ), CREAM))
		table.insert(bricks, B(Vector3.new(2.4, 0.8, 2.4), Vector3.new(x, h - 0.4, columnZ), CREAM))
	end
	-- Ступень перед входом: от уровня аллеи до пола (пол выше аллеи на 1).
	table.insert(bricks, B(Vector3.new(18, 0.5, 2), Vector3.new(0, -0.75, -half - 1), CREAM))

	-- Двускатная крыша: два клина, конёк вдоль Z, фронтон смотрит на аллею.
	local roofLength = half - columnZ + 2.4 + 1
	local roofMidZ = (half + 1 + columnZ - 1.4) / 2
	local roofHalfWidth = half + 1
	for _, sign in { -1, 1 } do
		-- У Wedge высокая сторона на +Z; поворот на ±90° направляет её к коньку (x = 0).
		local at = CFrame.new(sign * roofHalfWidth / 2, h + Museum.RoofHeight / 2, roofMidZ) * CFrame.Angles(0, -sign * math.rad(90), 0)
		table.insert(bricks, B(Vector3.new(roofLength, Museum.RoofHeight, roofHalfWidth), at, roof, { shape = "Wedge" }))
	end
	-- Фронтон: светлая полоса под крышей по всей ширине.
	table.insert(bricks, B(Vector3.new(Museum.Size + 2, 1, 1), Vector3.new(0, h + 0.5, columnZ - 1.4), CREAM))

	-- Окна по бокам (рамка + стекло).
	for _, sign in { -1, 1 } do
		for _, z in { -8, 4, 16 } do
			local x = sign * (half + 0.05)
			table.insert(bricks, B(Vector3.new(0.3, 4.6, 4), Vector3.new(x, 7, z), CREAM, DECOR))
			table.insert(bricks, B(Vector3.new(0.4, 3.8, 3.2), Vector3.new(x, 7, z), Palette.Glass, {
				material = Enum.Material.Glass,
				transparency = 0.3,
				collide = false,
				shadow = false,
			}))
		end
	end

	-- Флажки на углах фасада.
	for _, sign in { -1, 1 } do
		local x = sign * (half + 0.6)
		table.insert(bricks, B(Vector3.new(0.4, h + 6, 0.4), Vector3.new(x, (h + 6) / 2, columnZ), Palette.Metal, DECOR))
		table.insert(bricks, B(Vector3.new(0.2, 2, 3), Vector3.new(x, h + 4.8, columnZ + 1.6), accent, DECOR))
	end

	-- Пол в шахматку внутри стен.
	local innerX = half - 1
	local fromZ, toZ = facadeZ + 0.5, half - 1
	local columns, rows = 7, 6
	local tileW = innerX * 2 / columns
	local tileD = (toZ - fromZ) / rows
	table.insert(bricks, B(Vector3.new(innerX * 2, 0.1, toZ - fromZ), Vector3.new(0, 0.05, (fromZ + toZ) / 2), FLOOR_A, DECOR))
	for column = 0, columns - 1 do
		for row = 0, rows - 1 do
			if (column + row) % 2 == 1 then
				local x = -innerX + (column + 0.5) * tileW
				local z = fromZ + (row + 0.5) * tileD
				table.insert(bricks, B(Vector3.new(tileW, 0.12, tileD), Vector3.new(x, 0.06, z), FLOOR_B, DECOR))
			end
		end
	end
	return bricks
end

-- Окружение витрины: основание, золотой бортик, стеклянный колпак, столбики с бархатными канатами.
-- Начало — центр витрины на уровне пола; pedestal — размер самой витрины (Showcase_i).
function Museum.ShowcaseDecor(pedestal: Vector3, accent: Color3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {
		B(Vector3.new(pedestal.X + 1.2, 0.6, pedestal.Z + 1.2), Vector3.new(0, 0.3, 0), accent:Lerp(Palette.Black, 0.4)),
		-- Золотой пояс у верхнего края витрины (верх витрины свободен под экспонат).
		B(Vector3.new(pedestal.X + 0.4, 0.5, pedestal.Z + 0.4), Vector3.new(0, pedestal.Y - 0.25, 0), GOLD, DECOR),
		B(Vector3.new(pedestal.X, 6.4, pedestal.Z), Vector3.new(0, pedestal.Y + 3.2, 0), Palette.Glass, {
			name = "GlassCap",
			material = Enum.Material.Glass,
			transparency = 0.6,
			shadow = false,
		}),
	}
	local r = pedestal.X / 2 + 1.6
	local corners = { Vector2.new(-r, -r), Vector2.new(r, -r), Vector2.new(r, r), Vector2.new(-r, r) }
	for i, c in corners do
		table.insert(bricks, B(Vector3.new(0.4, 2.4, 0.4), Vector3.new(c.X, 1.2, c.Y), GOLD, DECOR))
		table.insert(bricks, B(Vector3.new(0.8, 0.4, 0.8), Vector3.new(c.X, 2.6, c.Y), GOLD, DECOR))
		local n = corners[i % #corners + 1]
		local mid = (c + n) / 2
		local length = (n - c).Magnitude
		local alongX = math.abs(n.X - c.X) > 0.1
		local size = if alongX then Vector3.new(length, 0.3, 0.3) else Vector3.new(0.3, 0.3, length)
		table.insert(bricks, B(size, Vector3.new(mid.X, 2.1, mid.Y), VELVET, DECOR))
	end
	return bricks
end

-- Подвесная лампа-прожектор над витриной. «Bulb» несёт SpotLight для презентации (ставит PartBuilder).
function Museum.Lamp(height: number): { ModelBuilder.Brick }
	return {
		B(Vector3.new(0.3, Museum.WallHeight - height, 0.3), Vector3.new(0, (Museum.WallHeight + height) / 2, 0), Palette.Black, DECOR),
		B(Vector3.new(2, 0.8, 2), Vector3.new(0, height + 0.4, 0), Palette.Black, DECOR),
		B(Vector3.new(1.4, 0.3, 1.4), Vector3.new(0, height - 0.15, 0), Palette.Lamp, {
			name = "Bulb",
			material = Enum.Material.Neon,
			collide = false,
			shadow = false,
		}),
	}
end

-- Сундук: крышка, золотые полосы и замок вокруг корпуса (корпус — часть Chest от PartBuilder).
-- Начало — центр корпуса.
function Museum.ChestDecor(body: Vector3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {
		B(Vector3.new(body.X + 0.3, 0.9, body.Z + 0.3), Vector3.new(0, body.Y / 2 + 0.45, 0), Palette.WoodDark),
	}
	for _, x in { -body.X / 3, body.X / 3 } do
		table.insert(bricks, B(Vector3.new(0.4, body.Y + 1, body.Z + 0.4), Vector3.new(x, 0.45, 0), GOLD, DECOR))
	end
	table.insert(bricks, B(Vector3.new(0.8, 0.9, 0.3), Vector3.new(0, body.Y / 2 - 0.1, -body.Z / 2 - 0.25), GOLD, DECOR))
	return bricks
end

return Museum

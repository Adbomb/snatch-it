-- Окружение витрин и сундука из кирпичей: декор витрины (основание, колпак, канаты), подвесная лампа и сундук;
-- цвета участков. Здание музея — модели из Blender (World/MeshBuilder, D33). Начало координат — центр
-- участка на уровне пола, вход — сторона -Z. Части с механикой (Floor, витрины Showcase_i, Chest, табличка)
-- строит Util/PartBuilder; здесь только их окружение.
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

local GOLD = Palette.MuseumGold
local VELVET = hex("9E2A2A")

-- Окружение витрины: основание, золотой бортик, стеклянный колпак, столбики с бархатными канатами.
-- Начало — центр витрины на уровне пола; pedestal — размер самой витрины (Showcase_i).
function Museum.ShowcaseDecor(pedestal: Vector3, accent: Color3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {
		B(Vector3.new(pedestal.X + 1.2, 0.6, pedestal.Z + 1.2), Vector3.new(0, 0.3, 0), accent:Lerp(Palette.Black, 0.4)),
		-- Золотой пояс у верхнего края витрины, верхом на 0.1 ниже крышки (иначе грани совпадают и мерцают, D36).
		B(Vector3.new(pedestal.X + 0.4, 0.5, pedestal.Z + 0.4), Vector3.new(0, pedestal.Y - 0.35, 0), GOLD, DECOR),
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

-- Подвесная лампа-прожектор над витриной на шнуре до потолка ceiling. «Bulb» несёт SpotLight для презентации
-- (ставит PartBuilder).
function Museum.Lamp(height: number, ceiling: number): { ModelBuilder.Brick }
	return {
		B(Vector3.new(0.3, ceiling - height, 0.3), Vector3.new(0, (ceiling + height) / 2, 0), Palette.Black, DECOR),
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

-- Строит карту (D36, D22) по MapLayout: остров травы, земляные обрывы с травой поверху вокруг безопасной зоны
-- (сзади и по бокам — уступом с травяной террасой) и коридора уровней, деревья на террасах и плато, лавки
-- «Аура» и «Продажа», точку появления и 10 зон одним коридором без рамок (D41) — пол с узором зоны, полоса-граница
-- цвета зоны, голографическое название, постаменты (у зоны с площадкой босса — без них, D43), декор; у входа в
-- коридор — разметка «Безопасная зона».
-- Воду вокруг острова строит BuildWater (Terrain; только в Play), под музеями — без воды по объёму хранилищ (D48-C);
-- в плите травы — проёмы под хранилищами. Участки-музеи с полем качалки строит PlotService.
-- Совпадающих граней у разных деталей нет (D36): трава обрывов, свесы и «натёки» лежат встык или с выступом.
-- Зависит от MapLayout, ModelBuilder, Palette, Studs, Hologram, Signs, World/Models/*, GameConfig, ZonePatterns,
-- Config/MuseumLayout.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local MuseumLayout = require(ReplicatedStorage.Shared.Config.MuseumLayout)
local ZonePatterns = require(ReplicatedStorage.Shared.Config.ZonePatterns)
local World = ServerScriptService.Server.World
local Hologram = require(World.Hologram)
local MapLayout = require(World.MapLayout)
local ModelBuilder = require(World.ModelBuilder)
local Palette = require(World.Palette)
local Signs = require(World.Signs)
local Studs = require(World.Studs)
local FleaMarket = require(World.Models.FleaMarket)
local Junkyard = require(World.Models.Junkyard)
local Shops = require(World.Models.Shops)
local Props = require(World.Models.Props)
local Tree = require(World.Models.Tree)
local ZoneDecor = require(World.Models.ZoneDecor)

local B = ModelBuilder.Brick
local H = MapLayout.Heights
local SLAB = 0.4 -- толщина плит покрытия
local GROUND = 2 -- толщина плиты травы
local UPRIGHT = CFrame.Angles(0, 0, math.rad(90)) -- ось цилиндра вертикально
local LINE = { width = 1, height = 0.2 } -- полосы на полу: граница Safe Zone и границы зон
local SAFE_LINE = Color3.fromHex("E5484D")
local DEEP = "LegoSquaresDeep" -- рельеф обрывов
local DRIP_SEED = 7

local WorldBuilder = {}

local function folder(name: string, parent: Instance): Folder
	local f = Instance.new("Folder")
	f.Name = name
	f.Parent = parent
	return f
end

-- Плита покрытия с верхом на высоте top.
local function slab(name: string, size: Vector2, center: Vector3, top: number, color: Color3, parent: Instance): Model
	local model = ModelBuilder.Build(name, {
		B(Vector3.new(size.X, SLAB, size.Y), Vector3.new(center.X, top - SLAB / 2, center.Z), color),
	})
	model.Parent = parent
	return model
end

local function place(key: string, build: () -> { ModelBuilder.Brick }, at: CFrame, parent: Instance): Model
	local model = ModelBuilder.FromTemplate(key, function()
		return ModelBuilder.Build(key, build())
	end)
	return ModelBuilder.Place(model, at, parent)
end

-- Брусок по границам (x0 < x1, z0 < z1).
local function box(
	x0: number,
	x1: number,
	y0: number,
	y1: number,
	z0: number,
	z1: number,
	color: Color3,
	extra: { [string]: any }?
)
	local size = Vector3.new(x1 - x0, y1 - y0, z1 - z0)
	return B(size, Vector3.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), color, extra)
end

-- Проём под хранилищем музея index (D48-C): контур зала по плану, мировые x0, x1, z0, z1.
local function vaultHole(index: number): (number, number, number, number)
	local c = MapLayout.PlotCFrame(index).Position
	local hall = MuseumLayout.Hall
	return c.X - hall.HalfWidth, c.X + hall.HalfWidth, c.Z + hall.Front, c.Z + hall.Back
end

local function buildGround(parent: Instance)
	local island = MapLayout.Island
	-- Шире обрывов на 2: боковые грани земли и обрывов не совпадают (D36). Плита травы — вокруг проёмов под
	-- хранилищами пяти музеев (D48-C): полоса до проёмов, полоса за ними и куски между проёмами.
	local x0, x1 = island.minX - 2, island.maxX + 2
	local y0, y1 = H.Ground - GROUND, H.Ground
	local holes = {}
	for index = 1, GameConfig.World.PlotCount do
		local a, b, c, d = vaultHole(index)
		table.insert(holes, { a, b, c, d })
	end
	table.sort(holes, function(p, q)
		return p[1] < q[1]
	end)
	local hz0, hz1 = holes[1][3], holes[1][4]
	for _, hole in holes do
		assert(hole[3] == hz0 and hole[4] == hz1, "WorldBuilder: проёмы хранилищ не в одном ряду")
	end
	local bricks = {
		box(x0, x1, y0, y1, island.minZ - 2, hz0, Palette.Field),
		box(x0, x1, y0, y1, hz1, island.maxZ + 2, Palette.Field),
	}
	local from = x0
	for _, hole in holes do
		table.insert(bricks, box(from, hole[1], y0, y1, hz0, hz1, Palette.Field))
		from = hole[2]
	end
	table.insert(bricks, box(from, x1, y0, y1, hz0, hz1, Palette.Field))
	ModelBuilder.Build("Ground", bricks).Parent = parent
end

-- «Натёки» травы на грани обрыва: бруски разной длины свисают с травы. Грань — along ("x" или "z") от a до b
-- на fixed, inward — куда смотрит грань (±1 по другой оси), top — верх земли, maxLen — длиннейший натёк.
-- Натёк выступает из грани на 1.4 (дальше свеса травы на 1), верх уходит в траву.
local function drips(
	bricks: { ModelBuilder.Brick },
	random: Random,
	along: string,
	a: number,
	b: number,
	fixed: number,
	inward: number,
	top: number,
	maxLen: number
)
	local t = a + 2 -- от края грани отступ: натёк не совпадает гранью со свесом соседней грани
	while t < b - 2 do
		local w = math.min(random:NextInteger(3, 7), b - 2 - t)
		local len = random:NextInteger(1, maxLen)
		local c = fixed + inward * 0.4
		local center = t + w / 2
		local y = top - len / 2 + 0.5
		if along == "x" then
			table.insert(bricks, B(Vector3.new(w, len + 1, 2), Vector3.new(center, y, c), Palette.CliffGrass))
		else
			table.insert(bricks, B(Vector3.new(2, len + 1, w), Vector3.new(c, y, center), Palette.CliffGrass))
		end
		t += w + random:NextInteger(1, 4)
	end
end

-- Обрывы вокруг безопасной зоны и коридора. Земляные блоки не перекрываются; трава поверху — по их следу,
-- свесы травы (lip) — отдельными полосами вдоль открытых граней, обрезанными так, чтобы не накладываться.
local function buildCliffs(parent: Instance)
	local f = folder("Cliffs", parent)
	local c = MapLayout.Cliff
	local SX, SZ, CX = MapLayout.SafeZone.halfX, MapLayout.SafeZone.back, MapLayout.CorridorHalf
	local D, HI, LO, L = c.terrace, c.height, c.low, c.lip
	local ZE = MapLayout.ZonesEnd
	local OX = SX + D + c.outer
	local deep = { variant = DEEP }
	local dirt, grass = Palette.CliffDirt, Palette.CliffGrass
	local bricks: { ModelBuilder.Brick } = {}
	local function block(x0, x1, z0, z1, top, grassH)
		table.insert(bricks, box(x0, x1, 0, top, z0, z1, dirt, deep))
		table.insert(bricks, box(x0, x1, top, top + grassH, z0, z1, grass))
	end
	-- Нижние террасы: сзади и по бокам безопасной зоны.
	block(-SX, SX, SZ, SZ + D, LO, c.lowGrass)
	-- Верхний обрыв сзади.
	block(-(SX + D), SX + D, SZ + D, SZ + D + c.outer, HI, c.grass)
	-- Конец коридора.
	block(-CX, CX, ZE - c.outer, ZE, HI, c.grass)
	for _, s in { -1, 1 } do
		local function X(a: number, b: number): (number, number)
			return math.min(s * a, s * b), math.max(s * a, s * b)
		end
		local x0, x1 = X(SX, SX + D)
		block(x0, x1, 0, SZ + D, LO, c.lowGrass)
		x0, x1 = X(SX + D, OX)
		block(x0, x1, 0, SZ + D + c.outer, HI, c.grass)
		-- Передний обрыв: от коридора до края острова, вдоль всего коридора.
		x0, x1 = X(CX, OX)
		block(x0, x1, ZE - c.outer, 0, HI, c.grass)

		-- Свесы травы: боковая терраса, боковой верхний обрыв, передний обрыв со стороны поля, стенка коридора.
		x0, x1 = X(SX - L, SX)
		table.insert(bricks, box(x0, x1, LO, LO + c.lowGrass, 0, SZ - L, grass))
		x0, x1 = X(SX + D - L, SX + D)
		table.insert(bricks, box(x0, x1, HI, HI + c.grass, L, SZ + D - L, grass))
		x0, x1 = X(CX, SX + D)
		table.insert(bricks, box(x0, x1, HI, HI + c.grass, 0, L, grass))
		x0, x1 = X(CX - L, CX)
		table.insert(bricks, box(x0, x1, HI, HI + c.grass, ZE + L, 0, grass))
	end
	table.insert(bricks, box(-SX, SX, LO, LO + c.lowGrass, SZ - L, SZ, grass))
	table.insert(bricks, box(-(SX + D), SX + D, HI, HI + c.grass, SZ + D - L, SZ + D, grass))
	table.insert(bricks, box(-(CX - L), CX - L, HI, HI + c.grass, ZE, ZE + L, grass))

	-- Натёки травы на открытых гранях.
	local random = Random.new(DRIP_SEED)
	drips(bricks, random, "x", -SX, SX, SZ, -1, LO, 4)
	drips(bricks, random, "x", -(SX + D), SX + D, SZ + D, -1, HI, 6)
	drips(bricks, random, "x", -CX, CX, ZE, 1, HI, 8)
	for _, s in { -1, 1 } do
		drips(bricks, random, "z", 0, SZ, s * SX, -s, LO, 4)
		drips(bricks, random, "z", 0, SZ + D, s * (SX + D), -s, HI, 6)
		local a, b = math.min(s * CX, s * (SX + D)), math.max(s * CX, s * (SX + D))
		drips(bricks, random, "x", a, b, 0, 1, HI, 8)
		drips(bricks, random, "z", ZE, 0, s * CX, -s, HI, 8)
	end
	ModelBuilder.Build("Cliffs", bricks).Parent = f

	-- Деревья: на задней террасе — в просветах между музеями и по углам, на боковых террасах, на плато у края.
	local trees: { { pos: Vector3, size: string } } = {}
	local terrace = LO + c.lowGrass
	for _, x in { -165, -112, -37, 37, 112, 165 } do
		table.insert(trees, { pos = Vector3.new(x, terrace, SZ + D / 2), size = "M" })
	end
	for _, s in { -1, 1 } do
		for _, z in { 25, 70, 112 } do
			table.insert(trees, { pos = Vector3.new(s * (SX + D / 2), terrace, z), size = "M" })
		end
		for _, z in { 10, 60, 120, 160 } do
			table.insert(trees, { pos = Vector3.new(s * (SX + D + 9), HI + c.grass, z), size = "L" })
		end
	end
	for _, x in { -150, -75, 0, 75, 150 } do
		table.insert(trees, { pos = Vector3.new(x + 20, HI + c.grass, SZ + D + 10), size = "L" })
	end
	for i, tree in trees do
		local color = i % #Palette.Leaves + 1
		place(("Tree_%s_%d"):format(tree.size, color), function()
			return Tree(tree.size, color)
		end, CFrame.new(tree.pos) * CFrame.Angles(0, i, 0), f)
	end
end

-- Лавки «Аура» и «Продажа» (D41, World/Models/Shops): павильоны лицом к полю (+Z), название — голограмма над крышей.
-- Детали с именами Spin и Bob получают теги (вращение и покачивание делает клиент), у кристалла ауры — искры.
local SHOP_BUILD = { ["Продажа"] = Shops.Sell, ["Аура"] = Shops.Aura }
local SHOP_STYLE = {
	["Продажа"] = { title = "💰 Продажа", accent = Color3.fromHex("2EBD4E"), size = Vector2.new(22, 5.5),
		height = Shops.SellTitleHeight, z = 2 },
	["Аура"] = { title = "✨ Аура", accent = Color3.fromHex("B04BFF"), size = Vector2.new(18, 5.5),
		height = Shops.AuraTitleHeight, z = 0 },
}
local SPARKLES = "rbxasset://textures/particles/sparkles_main.dds" -- встроенная текстура Roblox

local function buildShops(parent: Instance)
	local f = folder("Shops", parent)
	for _, shop in MapLayout.Shops do
		local model = ModelBuilder.Build(shop.title, SHOP_BUILD[shop.title]())
		model:ScaleTo(MapLayout.ShopScale)
		local base = shop.position + Vector3.new(0, H.Ground, 0)
		local at = CFrame.lookAt(base, base + Vector3.new(0, 0, 1))
		ModelBuilder.Place(model, at, f)
		for _, part in model:GetChildren() do
			if part.Name == "Spin" or part.Name == "Bob" then
				CollectionService:AddTag(part, part.Name)
				if part.Name == "Bob" then
					part:SetAttribute("BobHeight", 0.4)
				end
			end
		end
		local style = SHOP_STYLE[shop.title]
		if shop.title == "Продажа" then
			-- «$» на обеих сторонах монеты (круглые грани цилиндра — Left и Right)
			for _, part in model:GetChildren() do
				if part.Name == "Spin" and part.Size.X > 1.1 then
					for _, face in { Enum.NormalId.Left, Enum.NormalId.Right } do
						local gui = Instance.new("SurfaceGui")
						gui.Face = face
						gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
						gui.PixelsPerStud = 14
						gui.LightInfluence = 0.3
						gui.Parent = part
						local label = Instance.new("TextLabel")
						label.BackgroundTransparency = 1
						label.Size = UDim2.fromScale(1, 1)
						label.TextScaled = true
						label.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
						label.TextColor3 = Color3.fromHex("FFF4C2")
						label.Text = "$"
						label.Parent = gui
						local stroke = Instance.new("UIStroke")
						stroke.Color = Color3.fromHex("8A5A12")
						stroke.Thickness = 4
						stroke.Parent = label
					end
				end
			end
		else
			for _, part in model:GetChildren() do
				if part.Name == "Spin" then
					local sparks = Instance.new("ParticleEmitter")
					sparks.Texture = SPARKLES
					sparks.Color = ColorSequence.new(Color3.fromHex("FFB8F0"), Color3.fromHex("9FE8FF"))
					sparks.LightEmission = 1
					sparks.Rate = 14
					sparks.Lifetime = NumberRange.new(1.2, 2)
					sparks.Speed = NumberRange.new(1, 2.5)
					sparks.SpreadAngle = Vector2.new(180, 180)
					sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 0) })
					sparks.Parent = part
				end
			end
		end
		Hologram.Build({
			title = style.title,
			accent = style.accent,
			size = style.size * MapLayout.ShopScale,
		}, at * CFrame.new(0, style.height * MapLayout.ShopScale, -style.z * MapLayout.ShopScale), model)
	end
end

local function buildSpawn(parent: Instance)
	-- Точка появления игроков лицом к музеям. Своя SpawnLocation; чужие выключает Main (только в Play).
	local spawn = Instance.new("SpawnLocation")
	spawn.Name = "FieldSpawn"
	spawn.Anchored = true
	spawn.Neutral = true
	spawn.Duration = 0
	spawn.Size = MapLayout.Spawn.size
	local center = MapLayout.Spawn.position + Vector3.new(0, MapLayout.Spawn.size.Y / 2, 0)
	spawn.CFrame = CFrame.lookAt(center, center + Vector3.new(0, 0, 1))
	spawn.Transparency = 1 -- видна площадка вокруг
	local decal = spawn:FindFirstChildOfClass("Decal")
	if decal then
		decal:Destroy()
	end
	local f = folder("Spawn", parent)
	spawn.Parent = f
	-- Круглая площадка появления: светлая плита в два яруса и голубое светящееся кольцо (D41).
	local ground = MapLayout.Spawn.position
	local pad = ModelBuilder.Build("SpawnPad", {
		B(Vector3.new(0.3, 16, 16), CFrame.new(0, 0.15, 0) * UPRIGHT, Palette.MuseumTrim, { shape = "Cylinder" }),
		B(Vector3.new(0.12, 14.2, 14.2), CFrame.new(0, 0.36, 0) * UPRIGHT, Color3.fromHex("5CB0FF"), {
			shape = "Cylinder",
			material = Enum.Material.Neon,
			collide = false,
			shadow = false,
		}),
		B(Vector3.new(0.2, 13, 13), CFrame.new(0, 0.4, 0) * UPRIGHT, Palette.White, { shape = "Cylinder" }),
	})
	ModelBuilder.Place(pad, CFrame.new(ground), f)
end

-- Граница Safe Zone у входа в коридор (D41, как у референса владельца): красная линия поперёк и надпись
-- «БЕЗОПАСНАЯ ЗОНА» на траве — со стороны Safe Zone, читается, когда идёшь к уровням.
local function buildSafeLine(parent: Instance)
	local f = folder("SafeLine", parent)
	local half = MapLayout.CorridorHalf
	local line = Instance.new("Part")
	line.Name = "Line"
	line.Anchored = true
	line.Color = SAFE_LINE
	line.Size = Vector3.new(half * 2 - 0.4, LINE.height, LINE.width)
	line.CFrame = CFrame.new(0, H.Ground + LINE.height / 2, LINE.width / 2 + 0.1)
	line.Parent = f
	Studs.Apply(line)

	local label = Instance.new("Part")
	label.Name = "Label"
	label.Anchored = true
	label.CanCollide = false
	label.CanQuery = false
	label.CanTouch = false
	label.CastShadow = false
	label.Transparency = 1
	-- Холст грани Top идёт вдоль оси Z детали: длинная сторона — по Z, поворот на −90° кладёт её поперёк коридора,
	-- надпись читается со стороны Safe Zone (проверено в Studio).
	label.Size = Vector3.new(MapLayout.SafeLabel.Y, 0.2, MapLayout.SafeLabel.X)
	label.CFrame = CFrame.new(0, H.Ground + 0.15, MapLayout.SafeLabel.Y / 2 + 2.5) * CFrame.Angles(0, -math.pi / 2, 0)
	label.Parent = f
	local gui = Instance.new("SurfaceGui")
	gui.Face = Enum.NormalId.Top
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 10 -- TextScaled не крупнее 100 px
	gui.LightInfluence = 0.4
	gui.Parent = label
	local text = Instance.new("TextLabel")
	text.BackgroundTransparency = 1
	text.Size = UDim2.fromScale(1, 1)
	text.TextScaled = true
	text.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
	text.TextColor3 = Color3.new(1, 1, 1)
	text.TextTransparency = 0.1
	text.Text = "🛡 БЕЗОПАСНАЯ ЗОНА 🛡"
	text.Parent = gui
	local stroke = Instance.new("UIStroke")
	stroke.Color = Color3.fromHex("1E3A5A")
	stroke.Thickness = 2
	stroke.Transparency = 0.2
	stroke.Parent = text
end

local function buildZone(index: number, parent: Instance)
	local zone = GameConfig.Zones[index]
	local frame = MapLayout.ZoneCFrame(index)
	local size = MapLayout.ZoneSize
	local f = folder(("Zone%d_%s"):format(index, zone.id), parent)
	f:SetAttribute("Zone", index)
	local ground = CFrame.new(frame.Position.X, H.Ground, frame.Position.Z) * frame.Rotation
	local accent = Color3.fromHex(zone.accent)

	-- Пол с узором зоны (Texture поверх пупырышков): зоны различаются полом, а не рамками (D41).
	local floor = slab("Floor", Vector2.new(MapLayout.ZoneHalfWidth * 2, size), frame.Position, H.Path, Color3.fromHex(zone.floor), f)
	local spec = zone.pattern
	local top = floor:FindFirstChildWhichIsA("BasePart")
	if spec and top then
		local texture = Instance.new("Texture")
		texture.Name = "Pattern"
		texture.Face = Enum.NormalId.Top
		texture.Texture = ZonePatterns[spec.kind]
		texture.Color3 = Color3.fromHex(spec.color)
		texture.Transparency = 1 - spec.alpha
		texture.StudsPerTileU = spec.tile
		texture.StudsPerTileV = spec.tile
		texture.Parent = top
	end

	-- Граница с предыдущей зоной — светящаяся полоса цвета зоны поперёк коридора (у зоны 1 — линия Safe Zone).
	if index > 1 then
		local line = Instance.new("Part")
		line.Name = "Border"
		line.Anchored = true
		line.Material = Enum.Material.Neon
		line.Color = accent
		line.Transparency = 0.2
		line.CastShadow = false
		line.Size = Vector3.new((MapLayout.PylonX - 2) * 2, LINE.height, LINE.width) -- от столбика до столбика
		line.CFrame = CFrame.new(0, H.Path + LINE.height / 2, MapLayout.ZoneStartZ(index))
		line.Parent = f
	end

	-- Голографическое название уровня высоко над входом, лицом к входящему (D41): только название (D49 — без номера
	-- уровня и имени босса). Низ надписи — выше головы игрока и выше босса: не закрывает обзор.
	Hologram.Build({
		title = zone.name,
		accent = accent,
		size = MapLayout.HologramSize,
		hideAtNight = true,
	}, ground * CFrame.new(0, MapLayout.HologramHeight, -size / 2 + MapLayout.HologramInset), f)

	-- Светящиеся столбики у обрывов на границе с предыдущей зоной (цвет зоны): смена уровня без рамок.
	if index > 1 then
		for _, x in { -MapLayout.PylonX, MapLayout.PylonX } do
			local at = CFrame.new(x, H.Path, MapLayout.ZoneStartZ(index))
			place("Pylon_" .. zone.id, function()
				return {
					B(Vector3.new(3, 1, 3), Vector3.new(0, 0.5, 0), Palette.Stone),
					B(Vector3.new(1.6, 8, 1.6), Vector3.new(0, 5, 0), accent:Lerp(Palette.White, 0.35)),
					B(Vector3.new(2.6, 0.4, 2.6), Vector3.new(0, 9, 0), accent:Lerp(Palette.Black, 0.4)),
					B(Vector3.new(2.2, 2.2, 2.2), Vector3.new(0, 10.3, 0), accent, {
						material = Enum.Material.Neon,
						collide = false,
						shadow = false,
						light = { range = 16, brightness = 1.2, color = accent },
					}),
				}
			end, at, f)
		end
	end

	-- Постаменты под 4 предмета босса (D37); у зоны с площадкой босса предметы стоят на площадке (D43).
	if not MapLayout.Arenas[index] then
		for i, spot in MapLayout.ArtSlots do
			place("Pedestal_" .. zone.id, function()
				return ZoneDecor.Pedestal(accent)
			end, frame * CFrame.new(spot.X, 0, spot.Y), f).Name = "Pedestal_" .. i
		end
	end

	-- Декор по теме зоны.
	local decor: { ModelBuilder.Brick } = {}
	local signs: { FleaMarket.Sign } = {}
	if zone.id == "Junk" then
		decor = Junkyard.Zone() -- уровень 1 «Свалка» (D41)
	elseif zone.id == "Flea" then
		decor, signs = FleaMarket.Zone() -- уровень 2 «Барахолка» (D43)
	elseif zone.id == "Warehouse" then
		decor = ZoneDecor.Warehouse()
		for i, spot in { Vector3.new(-24, 0, -16), Vector3.new(24, 0, -16), Vector3.new(24, 4, -16), Vector3.new(-24, 0, -11) } do
			place("Crate", Props.Crate, frame * CFrame.new(spot) * CFrame.Angles(0, i * 0.2, 0), f)
		end
	elseif zone.id == "Bank" then
		decor = ZoneDecor.Bank(size)
	elseif zone.id == "Jungle" then
		decor = ZoneDecor.Jungle()
		for i, spot in { Vector2.new(-24, -14), Vector2.new(24, -4), Vector2.new(-24, 26), Vector2.new(24, 20) } do
			place("Tree_L_2", function()
				return Tree("L", 2)
			end, frame * CFrame.new(spot.X, 0, spot.Y) * CFrame.Angles(0, i, 0), f)
		end
	elseif ZoneDecor[zone.id] then
		decor = ZoneDecor[zone.id]()
	end
	local model = ModelBuilder.Place(ModelBuilder.Build("Decor", decor), frame, f)
	for _, sign in signs do
		local part = model:FindFirstChild(sign.name)
		if part and part:IsA("BasePart") then
			for _, face in sign.faces do
				Signs.Write(part, face, { { text = sign.text, scale = 0.8 } }, part.Color)
			end
		end
	end
end


function WorldBuilder.Build(parent: Instance)
	local map = folder("Map", parent)
	buildGround(map)
	buildCliffs(map)
	buildShops(map)
	buildSpawn(map)
	buildSafeLine(map)
	local zones = folder("Zones", map)
	for index in GameConfig.Zones do
		buildZone(index, zones)
	end
end

-- Вода до горизонта и песчаное дно (Terrain). Только в Play: в режиме редактирования Terrain
-- сохранился бы в месте.
local WATER_SIZE = 3000
local WATER_DEPTH = 10

function WorldBuilder.BuildWater()
	local terrain = workspace.Terrain
	terrain.WaterColor = Palette.Water
	terrain.WaterTransparency = 0.4
	terrain.WaterWaveSize = 0.1
	local island = MapLayout.Island
	local center = Vector3.new(0, H.Water - WATER_DEPTH / 2, (island.minZ + island.maxZ) / 2)
	terrain:FillBlock(CFrame.new(center), Vector3.new(WATER_SIZE, WATER_DEPTH, WATER_SIZE), Enum.Material.Water)
	terrain:FillBlock(
		CFrame.new(center - Vector3.new(0, WATER_DEPTH / 2 + 2, 0)),
		Vector3.new(WATER_SIZE, 4, WATER_SIZE),
		Enum.Material.Sand
	)
	-- Под каждым музеем — хранилище (D48-C): вода и песок вырезаются по его объёму (контур зала, от низа пола
	-- хранилища до низа пола зала), выровненному на сетку вокселей Terrain (4 ст.). Ровно по объёму нельзя: вокселей
	-- на границе вода остаётся целиком и заходит в комнату до 1.6 ст. (проверено в Play на участках 2–4). Сетка
	-- добавляет не больше 4 ст. за наружными стенами — это под плитой травы, снаружи не видно. Только в Play —
	-- исходное место не меняется.
	for index = 1, GameConfig.World.PlotCount do
		local volume = WorldBuilder.VaultVolume(index)
		local half = volume.size / 2
		local mid = volume.cframe.Position
		terrain:FillRegion(Region3.new(mid - half, mid + half):ExpandToGrid(4), 4, Enum.Material.Air)
	end
end

-- Объём хранилища участка index в мире: центр и размер (контур зала × от низа пола хранилища до низа пола зала).
function WorldBuilder.VaultVolume(index: number): { cframe: CFrame, size: Vector3 }
	local x0, x1, z0, z1 = vaultHole(index)
	local floor = H.Floor
	local bottom = floor + MuseumLayout.Vault.Floor - MuseumLayout.Hall.Slab
	local top = floor - MuseumLayout.Hall.Slab
	return {
		cframe = CFrame.new((x0 + x1) / 2, (bottom + top) / 2, (z0 + z1) / 2),
		size = Vector3.new(x1 - x0, top - bottom, z1 - z0),
	}
end

return WorldBuilder

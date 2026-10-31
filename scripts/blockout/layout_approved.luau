-- Утверждённый 3D-макет карты (рисунок заказчика 2026-10-31, docs/memory/NEXT_TASK.md). Резервная копия:
-- выполнить в Studio (Edit) через MCP execute_luau или командную строку — соберёт workspace.__Blockout
-- (Archivable = false, в место не сохраняется). Использует модули игры из ServerScriptService (через FreshRequire).
-- Координаты: безопасная зона x ±183, z 0…131; музеи у z 100 (x 150, 75, 0, −75, −150; +X — левая рука игрока,
-- смотрящего на музеи); коридор уровней x ±92 от z 0 вниз.

local MaterialService = game:GetService("MaterialService")
local S = game.ServerScriptService.Server
local fresh = require(S.World.FreshRequire)
local PartBuilder = fresh(S.Util.PartBuilder)
local MeshBuilder = fresh(S.World.MeshBuilder)
local Museum = fresh(S.World.Models.Museum)
local ModelBuilder = fresh(S.World.ModelBuilder)
local Gym = fresh(S.World.Models.Gym)
local Gate = fresh(S.World.Models.Gate)
local ZoneWall = fresh(S.World.Models.ZoneWall)
local Plaza = fresh(S.World.Models.Plaza)
local Signs = fresh(S.World.Signs)
local Palette = fresh(S.World.Palette)

local function variant(name, color, normal, roughness)
	local v = MaterialService:FindFirstChild(name) or Instance.new("MaterialVariant")
	v.Name = name
	v.BaseMaterial = Enum.Material.Plastic
	v.ColorMap = color
	v.NormalMap = normal
	v.RoughnessMap = roughness
	v.StudsPerTile = 8
	v.Parent = MaterialService
end
variant("LegoSquares", "rbxassetid://90809959209755", "rbxassetid://108191277429237", "rbxassetid://86272303409120")
variant("LegoSquaresDeep", "rbxassetid://122253275040553", "rbxassetid://113477796768810", "rbxassetid://86272303409120")
MaterialService:SetBaseMaterialOverride(Enum.Material.Plastic, "LegoSquares")

local old = workspace:FindFirstChild("__Blockout")
if old then
	old:Destroy()
end
local root = Instance.new("Folder")
root.Name = "__Blockout"
root.Archivable = false

local GRASS = Color3.fromHex("8CDF3C")
local DIRT = Color3.fromHex("A8784B")
local TOP = Color3.fromHex("6FD63A")

local function part(name, size, cframe, color, parent, opts)
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.Size = size
	p.CFrame = if typeof(cframe) == "Vector3" then CFrame.new(cframe) else cframe
	p.Color = color
	p.Material = Enum.Material.Plastic
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	if opts then
		for k, v in opts do
			p[k] = v
		end
	end
	p.Parent = parent
	return p
end
local function box(name, x0, z0, x1, z1, y0, y1, color, parent, opts)
	local size = Vector3.new(x1 - x0, y1 - y0, z1 - z0)
	return part(name, size, Vector3.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), color, parent, opts)
end

local ZX, ZN, CX, CEND = 183, 131, 92, -250
local OX, ON = 243, 191
local H = 30
local land = Instance.new("Folder")
land.Name = "Land"
land.Parent = root
box("Ground", -OX, CEND, OX, ON, -2, 0.1, GRASS, land)

local deep = { MaterialVariant = "LegoSquaresDeep" }
local cliffs = Instance.new("Folder")
cliffs.Name = "Cliffs"
cliffs.Parent = root
local blocks = { -- {имя, x0, z0, x1, z1, нависание травы: +X, -X, +Z, -Z}
	{ "W", -OX, CEND, -ZX, ON, { 1, 0, 0, 0 } },
	{ "E", ZX, CEND, OX, ON, { 0, 1, 0, 0 } },
	{ "N", -ZX, ZN, ZX, ON, { 0, 0, 0, 1 } },
	{ "FL", -ZX, CEND, -CX, 0, { 1, 0, 1, 0 } },
	{ "FR", CX, CEND, ZX, 0, { 0, 1, 1, 0 } },
}
for _, b in blocks do
	local name, x0, z0, x1, z1, lip = b[1], b[2], b[3], b[4], b[5], b[6]
	box("Cliff" .. name, x0, z0, x1, z1, 0, H, DIRT, cliffs, deep)
	box("Top" .. name, x0 - lip[2], z0 - lip[4], x1 + lip[1], z1 + lip[3], H, H + 3, TOP, cliffs)
end
local random = Random.new(7)
local function drips(fromA, toA, fixed, along, inward)
	local t = fromA + 1
	while t < toA - 2 do
		local w = math.min(random:NextInteger(3, 7), toA - 1 - t)
		local len = random:NextInteger(2, 9)
		local c = fixed + inward * 0.4
		local center = t + w / 2
		local pos = if along == "z"
			then Vector3.new(c, H - len / 2 + 0.5, center)
			else Vector3.new(center, H - len / 2 + 0.5, c)
		local size = if along == "z" then Vector3.new(2, len + 1, w) else Vector3.new(w, len + 1, 2)
		part("Drip", size, pos, TOP, cliffs)
		t += w + random:NextInteger(0, 3)
	end
end
drips(0, ZN, -ZX, "z", 1)
drips(0, ZN, ZX, "z", -1)
drips(-ZX, ZX, ZN, "x", -1)
drips(-ZX, -CX, 0, "x", 1)
drips(CX, ZX, 0, "x", 1)
drips(CEND, 0, -CX, "z", 1)
drips(CEND, 0, CX, "z", -1)
task.wait()

-- Музеи: гантель спереди слева, табличка «Улучшение» рядом.
local plots = Instance.new("Folder")
plots.Name = "Plots"
plots.Parent = root
local spots = {
	{ x = 150, museum = 1, dumbbell = 1, owner = "Игрок1" },
	{ x = 75, museum = 1, owner = nil },
	{ x = 0, museum = 1, dumbbell = 2, owner = "Игрок3" },
	{ x = -75, museum = 4, dumbbell = 5, owner = "Игрок4" },
	{ x = -150, museum = 7, dumbbell = 9, owner = "Игрок5" },
}
local MZ = 100
for i, spot in spots do
	local accent = Museum.Accents[i]
	local parts = PartBuilder.BuildPlot(i, CFrame.new(spot.x, 0, MZ), 6, plots)
	PartBuilder.SetBuilding(parts.model, parts.floorOrigin, accent, spot.museum)
	local model = parts.model
	for _, name in { "Yard", "YardPath", "GymField", "SignPost" } do
		local o = model:FindFirstChild(name)
		if o then
			o:Destroy()
		end
	end
	local fieldAt = CFrame.new(spot.x + 20, 0.12, MZ - 32)
	local field =
		ModelBuilder.Place(ModelBuilder.Build("GymField", Gym.Field(Vector2.new(12, 12), accent)), fieldAt, model)
	field:SetAttribute("GymField", true)
	local signAt = CFrame.new(spot.x + 7, 0.12, MZ - 30)
	ModelBuilder.Place(ModelBuilder.Build("SignPost", Gym.SignPost()), signAt, model)
	parts.signBoard.CFrame = signAt * CFrame.new(0, Gym.SignHeight, 0)
	if spot.owner then
		local at = fieldAt * CFrame.new(0, Gym.DumbbellHeight, 0) * CFrame.Angles(0, math.rad(90), 0)
		MeshBuilder.Build(("Dumbbell%02d"):format(spot.dumbbell), at, model, { accent = accent, name = "GiantDumbbell" })
		parts.signLabel.Text = "МУЗЕЙ " .. spot.owner
		Signs.Write(parts.signBoard, Enum.NormalId.Front, {
			{ text = "Улучшение", scale = 0.4 },
			{ text = "Ур. 1 > Ур. 2", scale = 0.3 },
		})
	else
		parts.signLabel.Text = "СВОБОДНЫЙ УЧАСТОК"
	end
	-- Пояс витрины ниже крышки на 0.1 (иначе z-fighting — подтверждено снимками).
	for _, d in model.ShowcaseDecor:GetDescendants() do
		if d:IsA("BasePart") and math.abs(d.Size.Y - 0.5) < 0.01 and d.Color == Color3.fromHex("FFC21A") then
			d.Position -= Vector3.new(0, 0.1, 0)
		end
	end
	task.wait()
end

-- Лавки «Аура» (+X) и «Продажа» (−X) у переднего края, прилавком в зону.
local shops = Instance.new("Folder")
shops.Name = "Shops"
shops.Parent = root
for _, spec in { { "Аура", CX, Palette.Awnings[2] }, { "Продажа", -CX, Palette.Awnings[3] } } do
	local at = CFrame.lookAt(Vector3.new(spec[2], 0.1, 12), Vector3.new(spec[2], 0.1, 0))
	local stall = ModelBuilder.Place(ModelBuilder.Build("Stall", Plaza.Stall(spec[3][1], spec[3][2])), at, shops)
	stall:ScaleTo(2.6)
	stall:PivotTo(at)
	stall.Name = spec[1]
	local board = part("Board", Vector3.new(16, 4, 0.6), CFrame.new(spec[2], 23, 4.5), Color3.fromHex("1E2A4A"), stall, {
		Material = Enum.Material.SmoothPlastic,
	})
	Signs.Write(board, Enum.NormalId.Back, { { text = string.upper(spec[1]), scale = 0.7 } })
end

box("Spawn", -4, 36, 4, 44, 0.1, 0.5, Color3.fromHex("5BEA72"), land)

-- Коридор уровней: вход в уровень 1 (граница безопасной зоны) и граница уровней 1 и 2. Табло — к безопасной зоне.
local zones = Instance.new("Folder")
zones.Name = "Levels"
zones.Parent = root
for _, spec in { { 0, "1. Свалка", "8D6E63" }, { -95, "2. Барахолка", "43C22E" } } do
	local z, title, color = spec[1], spec[2], Color3.fromHex(spec[3])
	local wallAt = CFrame.lookAt(Vector3.new(0, 0.1, z), Vector3.new(0, 0.1, z - 1))
	-- Стена начинается внутри стойки ворот: торцы стены и стойки не совпадают.
	ModelBuilder.Place(ModelBuilder.Build("ZoneWall", ZoneWall(CX, 16 + 2.4, 8, color)), wallAt, zones)
	local gateAt = CFrame.lookAt(Vector3.new(0, 0.1, z), Vector3.new(0, 0.1, z + 1))
	local gate = ModelBuilder.Place(ModelBuilder.Build("ZoneGate", Gate.Zone(16, color)), gateAt, zones)
	local sb = gate:FindFirstChild("SignBoard")
	if sb then
		Signs.Write(sb, Enum.NormalId.Front, { { text = title, scale = 0.5 } })
	end
end
root.Parent = workspace
return ("утверждённый макет: %d объектов"):format(#root:GetDescendants())

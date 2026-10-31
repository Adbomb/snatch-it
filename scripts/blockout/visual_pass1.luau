-- Визуальный проход 1 (2026-10-31) поверх утверждённого макета (layout_approved.luau): новый стартовый музей на
-- участке 1 и участок окружения рядом с ним. Планировка не меняется: границы, участки, гантели, лавки, коридор
-- на прежних местах. Выполнять в Studio (Edit) после layout_approved.luau.

local S = game.ServerScriptService.Server
local fresh = require(S.World.FreshRequire)
local ModelBuilder = fresh(S.World.ModelBuilder)
local Tree = fresh(S.World.Models.Tree)
local Museum = fresh(S.World.Models.Museum)

local root = workspace.__Blockout

-- ── Палитра: спокойный зелёный, светлая архитектура, умеренный тёплый коричневый ─────────────────
local P = {
	grass = Color3.fromHex("7FC75A"), -- поле (тёмная клетка шахматки — та же × 0.8 из текстуры)
	grassTop = Color3.fromHex("6CB84C"), -- трава на обрывах: чуть темнее поля, край читается
	dirt = Color3.fromHex("B48A60"), -- земля обрывов, глубокие тёмные квадратики из текстуры
	wall = Color3.fromHex("F3EFE6"), -- стены музея
	trim = Color3.fromHex("E0D9CA"), -- цоколь, карниз, ступени
	column = Color3.fromHex("FAF7F0"),
	floor = Color3.fromHex("E6DFD0"), -- пол и подиум музея
	glass = Color3.fromHex("A9D8F0"),
	leaves = Color3.fromHex("5FAE45"),
	fieldFloor = Color3.fromHex("ECE6D8"), -- пол поля гантели
}

local function recolor(container, from, to)
	for _, d in container:GetDescendants() do
		if d:IsA("BasePart") and d.Color == from then
			d.Color = to
		end
	end
end
root.Land.Ground.Color = P.grass
recolor(root.Cliffs, Color3.fromHex("A8784B"), P.dirt)
recolor(root.Cliffs, Color3.fromHex("6FD63A"), P.grassTop)

local function part(name, size, cframe, color, parent, opts)
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.Size = size
	p.CFrame = cframe
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

-- ── Окружение у участка 1: обрыв за музеями и справа от него — уступом с травяной террасой ───────────
-- Граница (нижний край обрыва) на прежнем месте: z = 131 сзади, x = 183 справа. Меняется только профиль.
local deep = { MaterialVariant = "LegoSquaresDeep" }
local cliffs = root.Cliffs
local LOW, HIGH = 12, 30 -- высота нижнего уступа и верхнего обрыва
local X0 = 41 -- участок окружения: от прохода между музеями 2 и 3 до правой стены
for _, name in { "CliffN", "TopN", "CliffE", "TopE" } do
	cliffs[name]:Destroy()
end
for _, d in cliffs:GetChildren() do
	-- Натёки старой высоты на перестраиваемых гранях.
	if d.Name == "Drip" then
		local p = d.Position
		if (p.Z > 130 and p.X > X0) or (p.X > 182 and p.Z > 0) then
			d:Destroy()
		end
	end
end
local function box(name, x0, z0, x1, z1, y0, y1, color, opts)
	local size = Vector3.new(x1 - x0, y1 - y0, z1 - z0)
	return part(name, size, CFrame.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), color, cliffs, opts)
end
-- Задний обрыв: слева от участка — как был; справа — нижний уступ (14 вглубь) и верхний обрыв.
box("CliffN", -183, 131, X0, 191, 0, HIGH, P.dirt, deep)
box("TopN", -183, 130, X0, 191, HIGH, HIGH + 3, P.grassTop)
box("CliffNLow", X0, 131, 183, 145, 0, LOW, P.dirt, deep)
box("TopNLow", X0, 130, 183, 145, LOW, LOW + 2, P.grassTop)
box("CliffNHigh", X0, 145, 183, 191, 0, HIGH, P.dirt, deep)
box("TopNHigh", X0, 144, 183, 191, HIGH, HIGH + 3, P.grassTop)
-- Правый обрыв: у безопасной зоны — нижний уступ (14 вглубь), дальше верхний; вдоль коридора — как был.
box("CliffE", 183, -250, 243, 0, 0, HIGH, P.dirt, deep)
box("TopE", 183, -250, 243, 0, HIGH, HIGH + 3, P.grassTop) -- без нависания: рядом трава коридора на той же высоте
box("CliffELow", 183, 0, 197, 145, 0, LOW, P.dirt, deep)
box("TopELow", 182, 0, 197, 145, LOW, LOW + 2, P.grassTop)
box("CliffEHigh", 197, 0, 243, 191, 0, HIGH, P.dirt, deep)
box("TopEHigh", 196, 0, 243, 191, HIGH, HIGH + 3, P.grassTop)
box("CliffECorner", 183, 145, 197, 191, 0, HIGH, P.dirt, deep)
box("TopECorner", 183, 144, 196, 191, HIGH, HIGH + 3, P.grassTop)
-- Короткие натёки травы на гранях уступов (выступают на 0.6, верх уходит под траву).
local random = Random.new(11)
local function drips(fromA, toA, fixed, along, inward, top, maxLen)
	local t = fromA + 1
	while t < toA - 2 do
		local w = math.min(random:NextInteger(3, 7), toA - 1 - t)
		local len = random:NextInteger(1, maxLen)
		local c = fixed + inward * 0.4
		local center = t + w / 2
		local pos = if along == "z"
			then Vector3.new(c, top - len / 2 + 0.5, center)
			else Vector3.new(center, top - len / 2 + 0.5, c)
		local size = if along == "z" then Vector3.new(2, len + 1, w) else Vector3.new(w, len + 1, 2)
		part("Drip", size, CFrame.new(pos), P.grassTop, cliffs)
		t += w + random:NextInteger(1, 4)
	end
end
drips(X0, 183, 131, "x", -1, LOW, 4)
drips(X0, 183, 145, "x", -1, HIGH, 6)
drips(0, 145, 183, "z", -1, LOW, 4)
drips(0, 145, 197, "z", -1, HIGH, 6)
-- Несколько деревьев на террасе — смягчают обрыв, не заслоняя музеи.
for i, spot in { Vector2.new(58, 138), Vector2.new(112, 139), Vector2.new(170, 137), Vector2.new(190, 96), Vector2.new(190, 30) } do
	local tree = ModelBuilder.Place(ModelBuilder.Build("Tree", Tree("M", 1)), CFrame.new(spot.X, LOW + 2, spot.Y) * CFrame.Angles(0, i, 0), cliffs)
	for _, d in tree:GetDescendants() do
		if d:IsA("BasePart") and d.Color.G > d.Color.R * 1.3 then
			d.Color = if d.Size.Y < 3.5 then P.leaves:Lerp(Color3.new(1, 1, 1), 0.12) else P.leaves
		end
	end
end
task.wait()

-- ── Стартовый музей на участке 1: небольшой, светлый, классический ─────────────────────────────────
-- Координаты участка: x вправо, y от пола (верх подиума 1.4), вход в -Z. Витрины (x −10…10, z −2…12),
-- сундук (x −12, z −8), табличка (y 11.5, z −12.75) и лампы — на прежних местах (их строит PartBuilder).
local plot = root.Plots.Plot_1
local accent = Museum.Accents[1]
local muted = accent:Lerp(Color3.fromHex("6B5B53"), 0.3) -- крыша, фриз, эмблема: цвет участка, приглушённый
for _, name in { "Building", "Walls" } do
	local o = plot:FindFirstChild(name)
	if o then
		o:Destroy()
	end
end
plot.Floor.Color = P.floor
for _, d in plot.GymField:GetDescendants() do
	if d:IsA("BasePart") and d.Material ~= Enum.Material.Neon then
		d.Color = P.fieldFloor
	end
end
local floorOrigin = plot.Floor.CFrame * CFrame.new(0, plot.Floor.Size.Y / 2, 0)
local building = Instance.new("Model")
building.Name = "Building"
building.Parent = plot
local function L(name, size, center, color, opts)
	return part(name, size, floorOrigin * CFrame.new(center), color, building, opts)
end
local function LB(name, x0, x1, y0, y1, z0, z1, color, opts)
	return L(name, Vector3.new(x1 - x0, y1 - y0, z1 - z0), Vector3.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), color, opts)
end
local H, HW = 14.4, 18 -- высота стен и полуширина зала (наружная грань)
local FZ, BZ = -12.7, 20.7 -- наружные грани фасада и задней стены
local T = 1.4
local DOOR, DOORH = 6, 10
-- Стены зала.
for _, s in { -1, 1 } do
	LB("SideWall", s > 0 and HW - T or -HW, s > 0 and HW or -HW + T, 0, H, FZ, BZ, P.wall)
end
LB("BackWall", -HW + T, HW - T, 0, H, BZ - T, BZ, P.wall)
LB("FrontWall", -HW + T, -DOOR, 0, H, FZ, FZ + T, P.wall)
LB("FrontWall", DOOR, HW - T, 0, H, FZ, FZ + T, P.wall)
LB("Lintel", -DOOR, DOOR, DOORH, H, FZ, FZ + T, P.wall)
-- Цоколь (0.3 наружу) и карниз (0.4 наружу) — торцы встык, без перекрытий.
for _, band in { { 0, 1.2, 0.3, "Base" }, { H - 1, H, 0.4, "Cornice" } } do
	local y0, y1, out, name = band[1], band[2], band[3], band[4]
	for _, s in { -1, 1 } do
		local x0, x1 = if s > 0 then HW - 0.1 else -HW - out, if s > 0 then HW + out else -HW + 0.1
		LB(name, x0, x1, y0, y1, FZ - out, BZ + out, P.trim)
	end
	LB(name, -HW + 0.1, HW - 0.1, y0, y1, BZ - 0.1, BZ + out, P.trim)
	if name == "Base" then
		LB(name, -HW + 0.1, -DOOR, y0, y1, FZ - out, FZ + 0.1, P.trim)
		LB(name, DOOR, HW - 0.1, y0, y1, FZ - out, FZ + 0.1, P.trim)
	else
		LB(name, -HW + 0.1, HW - 0.1, y0, y1, FZ - out, FZ + 0.1, P.trim)
	end
end
-- Окна по бокам: рама (0.1 наружу) и стекло (0.15 наружу).
for _, s in { -1, 1 } do
	for _, z in { -1, 11 } do
		LB("WindowFrame", s > 0 and HW - 0.05 or -HW - 0.1, s > 0 and HW + 0.1 or -HW + 0.05, 3.6, 10.4, z - 2.4, z + 2.4, P.trim)
		LB("Window", s > 0 and HW - 0.05 or -HW - 0.15, s > 0 and HW + 0.15 or -HW + 0.05, 4, 10, z - 2, z + 2, P.glass, {
			Material = Enum.Material.Glass,
			Transparency = 0.25,
		})
	end
end
-- Потолок над залом и портиком; фриз цвета участка по переднему краю.
local PZ = -23 -- передний край портика (подиум кончается на −22)
LB("Ceiling", -HW - 0.4, HW + 0.4, H, H + 0.6, PZ, BZ + 0.4, P.trim)
LB("Frieze", -HW - 0.4, HW + 0.4, H + 0.1, H + 0.5, PZ - 0.2, PZ + 0.2, muted)
-- Портик: четыре колонны (база, ствол, капитель).
for _, x in { -15, -9, 9, 15 } do
	LB("ColumnBase", x - 1.2, x + 1.2, 0, 0.6, -20.7, -18.3, P.trim)
	LB("Column", x - 0.9, x + 0.9, 0.6, H - 0.8, -20.4, -18.6, P.column)
	LB("ColumnCap", x - 1.3, x + 1.3, H - 0.8, H, -20.8, -18.2, P.trim)
end
-- Двускатная крыша (конёк вдоль глубины) и белый фронтон с эмблемой цвета участка.
-- Клин: высокая сторона WedgePart — на +Z детали; поворот на ∓90° по Y направляет её к коньку (x = 0).
local function wedge(name, size, cframe, color)
	local w = Instance.new("WedgePart")
	w.Name = name
	w.Anchored = true
	w.Size = size
	w.CFrame = cframe
	w.Color = color
	w.Material = Enum.Material.Plastic
	w.Parent = building
	return w
end
local RH, RHW = 7, HW + 1.4
local RZ0, RZ1 = PZ - 0.5, BZ + 0.9
local roofMid = (RZ0 + RZ1) / 2
for _, s in { -1, 1 } do
	local turn = CFrame.Angles(0, -s * math.rad(90), 0)
	wedge("Roof", Vector3.new(RZ1 - RZ0, RH, RHW), floorOrigin * CFrame.new(s * RHW / 2, H + 0.6 + RH / 2, roofMid) * turn, muted)
	-- Фронтон чуть меньше крыши (виден край кровли) и выходит вперёд, задняя грань — внутри крыши.
	local w = RHW - 1.6
	local h = RH * w / RHW
	wedge("Pediment", Vector3.new(0.8, h, w), floorOrigin * CFrame.new(s * w / 2, H + 0.6 + h / 2, RZ0 - 0.1) * turn, P.wall)
end
local emblem = L("Emblem", Vector3.new(0.4, 3.2, 3.2), Vector3.zero, muted)
emblem.Shape = Enum.PartType.Cylinder
emblem.CFrame = floorOrigin * CFrame.new(0, H + 0.6 + 2.4, RZ0 - 0.6) * CFrame.Angles(0, math.rad(90), 0)
-- Ступени к порталу (от травы до пола зала).
LB("Step", -10, 10, -1.3, -0.65, -25, -22, P.trim)
LB("Step", -10, 10, -0.65, 0, -23.5, -22, P.trim)
return ("стартовый музей: %d деталей; окружение обновлено"):format(#building:GetChildren())

-- Проверка раскладки HUD v3 в Studio (Client, Play): вставить в MCP execute_luau. Читает настоящие прямоугольники
-- HUD на текущем экране (размер окна Studio = размер проверяемого экрана) и зоны кнопок Roblox (верхняя панель,
-- прыжок — по PlayerModule/TouchJump), возвращает пересечения и выходы за экран. TOUCH = true — раскладка телефона
-- (атрибут игрока DevTouch; настоящих кнопок Roblox в Studio нет — рисуются полупрозрачные заглушки __PhoneMock,
-- это эмуляция, не устройство). SHOW = true — показать всё сразу (худший случай): плашку зоны, строку «Несёте»,
-- кнопку «Удар». CLEAN = true — убрать заглушки и подмены. Ни от чего в репозитории не зависит (читает PlayerGui).
local TOUCH, SHOW, CLEAN = true, true, false

local player = game.Players.LocalPlayer
local pg = player.PlayerGui
local old = pg:FindFirstChild("__PhoneMock")
if old then
	old:Destroy()
end
if CLEAN then
	player:SetAttribute("DevTouch", nil)
	player:SetAttribute("CarryingItemId", nil)
	return "убрано"
end
player:SetAttribute("DevTouch", if TOUCH then true else nil)
local view = workspace.CurrentCamera.ViewportSize
local inset = game:GetService("GuiService"):GetGuiInset().Y
local rects: { { name: string, x0: number, y0: number, x1: number, y1: number, system: boolean } } = {}

local function add(name: string, x0: number, y0: number, x1: number, y1: number, system: boolean?)
	table.insert(rects, { name = name, x0 = x0, y0 = y0, x1 = x1, y1 = y1, system = system == true })
end

-- прямоугольник объекта в px экрана (AbsolutePosition — от низа верхней панели Roblox)
local function of(name: string, object: Instance?)
	if object and object:IsA("GuiObject") and object.Visible then
		local p, s = object.AbsolutePosition, object.AbsoluteSize
		add(name, p.X, p.Y + inset, p.X + s.X, p.Y + inset + s.Y)
	end
end

if SHOW then
	player:SetAttribute("CarryingItemId", "Astrolabe")
	local banner = pg:FindFirstChild("LevelBanner") and pg.LevelBanner:FindFirstChild("LevelBanner")
	if banner then
		banner.Visible = true
		banner.GroupTransparency = 0
	end
	local pvp = pg:FindFirstChild("PvpHud") and pg.PvpHud:FindFirstChild("Racine")
	if pvp and TOUCH then
		pvp.Visible = true
	end
end
task.wait(0.4)

local mock = Instance.new("ScreenGui")
mock.Name = "__PhoneMock"
mock.IgnoreGuiInset = true
mock.DisplayOrder = 50
mock.ResetOnSpawn = false
mock.Parent = pg
local function blob(x: number, y: number, w: number, h: number)
	local f = Instance.new("Frame")
	f.BackgroundColor3 = Color3.new(1, 1, 1)
	f.BackgroundTransparency = 0.6
	f.Position = UDim2.fromOffset(x, y)
	f.Size = UDim2.fromOffset(w, h)
	f.Parent = mock
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(1, 0)
	c.Parent = f
end
-- верхняя панель Roblox: значок и капсула меню слева сверху
blob(12, 10, 44, 44)
blob(64, 10, 132, 44)
add("Roblox: верхняя панель", 0, 0, 210, 58, true)
if TOUCH then
	local small = math.min(view.X, view.Y) <= 500
	local size = if small then 70 else 120
	local x = view.X - (size * 1.5 - 10)
	local y = if small then view.Y - size - 20 else view.Y - size * 1.75
	blob(x, y, size, size)
	add("Roblox: прыжок", x, y, x + size, y + size, true)
end

local menu = pg:FindFirstChild("MenuHud") and pg.MenuHud:FindFirstChild("Colonne")
if menu then
	for _, holder in menu:GetChildren() do
		of("меню: " .. holder.Name, holder)
	end
end
of("сила и монеты", pg:FindFirstChild("GymHud") and pg.GymHud:FindFirstChild("Stats"))
of("таймер", pg:FindFirstChild("TimeHud") and pg.TimeHud:FindFirstChild("Holder"))
of("плашка зоны", pg:FindFirstChild("LevelBanner") and pg.LevelBanner:FindFirstChild("LevelBanner"))
of("несёте", pg:FindFirstChild("CarryHud") and pg.CarryHud:FindFirstChild("Rangee"))
of("удар", pg:FindFirstChild("PvpHud") and pg.PvpHud:FindFirstChild("Racine"))
of(
	"обучение",
	pg:FindFirstChild("Tutoriel") and pg.Tutoriel.Enabled and pg.Tutoriel:FindFirstChild("Panneau") or nil
)
of("тест владельца", pg:FindFirstChild("OwnerTestHud") and pg.OwnerTestHud:FindFirstChild("Panneau"))

local problems = {}
for i, a in rects do
	if not a.system and (a.x0 < 0 or a.y0 < 0 or a.x1 > view.X + 0.5 or a.y1 > view.Y + 0.5) then
		table.insert(problems, ("за экраном: %s (%d,%d–%d,%d)"):format(a.name, a.x0, a.y0, a.x1, a.y1))
	end
	for j = i + 1, #rects do
		local b = rects[j]
		if not (a.system and b.system) and a.x0 < b.x1 and b.x0 < a.x1 and a.y0 < b.y1 and b.y0 < a.y1 then
			table.insert(problems, ("пересечение: %s × %s"):format(a.name, b.name))
		end
	end
end
local lines =
	{ ("экран %d×%d, касание %s, элементов %d"):format(view.X, view.Y, tostring(TOUCH), #rects) }
for _, r in rects do
	table.insert(
		lines,
		("  %s: %d,%d–%d,%d (%d×%d)"):format(r.name, r.x0, r.y0, r.x1, r.y1, r.x1 - r.x0, r.y1 - r.y0)
	)
end
table.insert(lines, if #problems == 0 then "пересечений нет" else table.concat(problems, "\n"))
return table.concat(lines, "\n")

-- Моделирование HUD на экране телефона в Studio (D49): вставить в MCP execute_luau (Client, Play) и снять
-- screen_capture. Не настоящее устройство (StudioDeviceEmulatorService скриптам недоступен): копии экранов HUD в
-- рамке размера телефона, масштаб WindowScale как у StudMotion для этого размера, соседи таймера и меню — как в
-- client/UI/HudLayout; зоны кнопок Roblox (верхняя панель 58, прыжок, джойстик) — по PlayerModule. Скрытые элементы
-- (плашка зоны, «Бросить», «Удар») показаны все сразу — худший случай. Уведомления: перед запуском вызвать пару
-- настоящих (например DefenseAction BuyHack ночью). Возвращает пересечения прямоугольников. Убрать — удалить
-- PlayerGui.__PhoneSim. Ни от чего в репозитории не зависит (читает PlayerGui).
local W, H, NOTCH, LABEL = 844, 390, 47, "iPhone 14" -- SE 667×375/0, Android 740×360/0, iPad 1024×768/0
-- плашка зоны видна (худший случай: уведомления на это время ниже неё, D50); false — обычное состояние без плашки
local BANNER = true
local pg = game.Players.LocalPlayer.PlayerGui
local old = pg:FindFirstChild("__PhoneSim")
if old then
	old:Destroy()
end
local TOP = 58
local function screenScale(x, y)
	return math.clamp(math.min(x / 1050, y / 620), 0.52, 1.18)
end
local vp = workspace.CurrentCamera.ViewportSize
local cur = screenScale(vp.X, vp.Y)
local s = screenScale(W, H)

local sim = Instance.new("ScreenGui")
sim.Name = "__PhoneSim"
sim.IgnoreGuiInset = true
sim.DisplayOrder = 1000
sim.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
sim.Archivable = false
local back = Instance.new("Frame")
back.Size = UDim2.fromScale(1, 1)
back.BackgroundColor3 = Color3.new(0.08, 0.08, 0.1)
back.Parent = sim
local zoom = math.min((vp.X - 40) / W, (vp.Y - 110) / H)
local phone = Instance.new("Frame")
phone.Name = "Phone"
phone.AnchorPoint = Vector2.new(0.5, 0.5)
phone.Position = UDim2.new(0.5, 0, 0.5, 30)
phone.Size = UDim2.fromOffset(W, H)
phone.BackgroundColor3 = Color3.fromRGB(120, 170, 120)
phone.ClipsDescendants = true
phone.Parent = sim
local z = Instance.new("UIScale")
z.Scale = zoom
z.Parent = phone
local title = Instance.new("TextLabel")
title.Size = UDim2.new(1, 0, 0, 40)
title.Position = UDim2.fromOffset(0, TOP + 4)
title.BackgroundTransparency = 1
title.TextColor3 = Color3.new(1, 1, 1)
title.TextSize = 28
title.Font = Enum.Font.GothamBold
title.Text = ("%s — %d×%d, масштаб HUD %.2f (моделирование)"):format(LABEL, W, H, s)
title.Parent = back

local function box(parent, name, x, y, w, h, color, zIndex, text)
	local f = Instance.new("Frame")
	f.Name = name
	f.Position = UDim2.fromOffset(x, y)
	f.Size = UDim2.fromOffset(w, h)
	f.BackgroundColor3 = color
	f.BackgroundTransparency = 0.45
	f.ZIndex = zIndex
	f.Parent = parent
	if text then
		local t = Instance.new("TextLabel")
		t.Size = UDim2.fromScale(1, 1)
		t.BackgroundTransparency = 1
		t.Text = text
		t.TextScaled = true
		t.TextColor3 = Color3.new(1, 1, 1)
		t.ZIndex = zIndex
		t.Parent = f
	end
	return f
end

local safeW = W - 2 * NOTCH
for _, name in { "GymHud", "MenuHud", "TimeHud", if BANNER then "LevelBanner" else "", "PvpHud", "CarryHud", "Toasts" } do
	local g = pg:FindFirstChild(name)
	if g then
		local core = g.ScreenInsets == Enum.ScreenInsets.CoreUISafeInsets
		local holder = Instance.new("Frame")
		holder.Name = name
		holder.BackgroundTransparency = 1
		holder.Position = UDim2.fromOffset(NOTCH, if core then TOP else 0)
		holder.Size = UDim2.fromOffset(safeW, if core then H - TOP else H)
		holder.ZIndex = g.DisplayOrder + 5
		holder.Parent = phone
		for _, child in g:GetChildren() do
			if child:IsA("GuiObject") then
				local c = child:Clone()
				for _, d in c:GetDescendants() do
					if d:IsA("LuaSourceContainer") then
						d:Destroy()
					end
				end
				for _, d in c:GetDescendants() do
					if d:IsA("UIScale") and (d.Name == "WindowScale" or d.Name == "UIScale") then
						-- MinScale — нижняя граница масштаба (кнопка «Удар» не ниже 52 px, D50)
						d.Scale = math.max(
							d.Scale / math.max(cur, d:GetAttribute("MinScale") or 0) * s,
							d:GetAttribute("MinScale") or 0
						)
					end
				end
				if c:IsA("UIScale") then
					c.Scale = c.Scale * s / cur
				end
				c.Visible = true
				if c:IsA("CanvasGroup") then
					c.GroupTransparency = 0
				end
				-- как client/UI/HudLayout: таймер 96 px при масштабе 1, плашка зоны 380×96 под ним, колонка
				-- уведомлений 26 % ширины (180…360 px) левее меню; заходит под видимую плашку — спрятана (D50)
				local below = 6 + 96 * s
				if name == "Toasts" then
					local right = 18 + 110 * s + 12
					local left = safeW - right - math.clamp(0.26 * safeW, 180, 360)
					c.Position = UDim2.new(1, -right, 0, below + 10)
					c.Visible = not (BANNER and left < safeW / 2 + 190 * s)
				end
				if name == "PvpHud" then -- левее колонки меню (client/UI/HudLayout.LeftOfMenu, отступ 8)
					c.Position = UDim2.new(1, -(18 + 110 * s + 8), 0, 4)
				end
				if name == "LevelBanner" then
					c.Position = UDim2.new(0.5, 0, 0, below + 12)
				end
				c.Parent = holder
			end
		end
	end
end
-- Кнопки Roblox: верхняя панель, прыжок и джойстик (PlayerModule: экран с меньшей стороной ≤ 500 — малые кнопки)
box(phone, "Topbar", 0, 0, W, TOP, Color3.fromRGB(40, 40, 40), 2)
box(phone, "RobloxMenu", NOTCH + 12, 8, 44, 44, Color3.fromRGB(230, 230, 230), 3, "≡")
box(phone, "RobloxChat", NOTCH + 64, 8, 44, 44, Color3.fromRGB(230, 230, 230), 3, "чат")
local small = math.min(W, H) <= 500
local jump = if small then 70 else 120
local jx = if small then W - NOTCH - 95 else W - NOTCH - 170
local jy = if small then H - 90 else H - 210
box(phone, "Jump", jx, jy, jump, jump, Color3.fromRGB(255, 255, 255), 100, "прыжок")
local stick = if small then 90 else 120
box(phone, "Stick", NOTCH + 30, H - stick - 30, stick, stick, Color3.fromRGB(255, 255, 255), 100, "джойстик")
sim.Parent = pg

-- пересечения кнопок и плашек
task.wait(0.3)
local rects = {}
local function add(label, gui)
	if gui and gui:IsA("GuiObject") and gui.Visible and gui.AbsoluteSize.X > 1 then
		table.insert(rects, { label, gui.AbsolutePosition, gui.AbsolutePosition + gui.AbsoluteSize })
	end
end
local function find(holder, path)
	local node = phone:FindFirstChild(holder)
	for _, part in string.split(path, ".") do
		node = node and node:FindFirstChild(part)
	end
	return node
end
add("stats", find("GymHud", "Stats"))
add("menu", find("MenuHud", "Colonne"))
add("timer", find("TimeHud", "Holder"))
add("banner", find("LevelBanner", "LevelBanner"))
add("punch", find("PvpHud", "Racine"))
add("drop", find("CarryHud", "Button"))
add("pill", find("CarryHud", "CarryPill"))
-- уведомления: две последние; как NotifyController.capacity — если колонка по ширине заходит на «Бросить», только
-- те, что выше кнопки
local toasts = {}
local toastColumn = find("Toasts", "Column")
for _, t in if toastColumn and toastColumn.Visible then toastColumn:GetChildren() else {} do
	if t:IsA("GuiObject") then
		table.insert(toasts, t)
	end
end
table.sort(toasts, function(a, b)
	return a.LayoutOrder > b.LayoutOrder
end)
local drop = find("CarryHud", "Button")
for i, t in toasts do
	local blocked = drop
		and t.AbsolutePosition.X < drop.AbsolutePosition.X + drop.AbsoluteSize.X
		and t.AbsolutePosition.Y + t.AbsoluteSize.Y > drop.AbsolutePosition.Y
	if i > 2 or blocked then
		t:Destroy()
	else
		add("toast", t)
	end
end
add("jump", phone.Jump)
add("stick", phone.Stick)
add("topbar", phone.Topbar)
local out = { title.Text }
for i = 1, #rects do
	for j = i + 1, #rects do
		local a, b = rects[i], rects[j]
		if a[2].X < b[3].X and b[2].X < a[3].X and a[2].Y < b[3].Y and b[2].Y < a[3].Y then
			table.insert(out, "ПЕРЕСЕЧЕНИЕ " .. a[1] .. " × " .. b[1])
		end
	end
end
for _, r in rects do
	local sz = (r[3] - r[2]) / zoom
	local p = (r[2] - phone.AbsolutePosition) / zoom
	table.insert(out, ("%s: (%.0f, %.0f) %.0f×%.0f"):format(r[1], p.X, p.Y, sz.X, sz.Y))
end
return table.concat(out, "\n")

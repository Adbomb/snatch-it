-- Замер окна «Улучшение музея» (D56) в Studio: вставить в MCP execute_luau (Client, Play) при открытом окне и снять
-- screen_capture. Экран подменяется атрибутами игрока (только Studio + DevMode), как у «Магазина» и «Инвентаря»:
--   player:SetAttribute("DevViewport", Vector2.new(844, 390)); player:SetAttribute("DevTouch", true)
-- затем закрыть и снова открыть окно кнопкой «Музей» (раскладка считается при открытии). Сбросить — оба атрибута nil.
-- Это не настоящее устройство: окно рисуется того размера в px, какого было бы на таком экране, но посреди экрана
-- Studio. Проверяет: окно умещается на экране (с полями и под кнопками Roblox), кнопка «Улучшить» на касании не ниже
-- 52 px, все надписи умещаются в свои рамки и не мельче MIN_TEXT px, стрелка и иконки не закрывают надписи, 20
-- квадратиков мест — внутри окна и не налезают друг на друга, меню HUD не задевает кнопку прыжка.
-- Ни от чего в репозитории не зависит (читает PlayerGui). Возвращает строки отчёта.
local MARGIN, MIN_TOUCH, MIN_TEXT = 16, 52, 9

local Players = game:GetService("Players")
local GuiService = game:GetService("GuiService")
local player = Players.LocalPlayer
local pg = player.PlayerGui
local gui = pg:FindFirstChild("MuseeNiveau")
if not gui or not gui.Enabled then
	return "окно «Улучшение музея» закрыто — откройте кнопкой «Музей»"
end
local fen = gui.Fenetre
local fake = player:GetAttribute("DevViewport")
local touch = player:GetAttribute("DevTouch") == true
local real = workspace.CurrentCamera.ViewportSize
local vp = if typeof(fake) == "Vector2" then fake else real
local inset = GuiService:GetGuiInset().Y
local out, problems = {}, 0
local function line(ok: boolean, text: string)
	table.insert(out, (if ok then "ок      " else "ОШИБКА  ") .. text)
	if not ok then
		problems += 1
	end
end
local function rect(o: GuiObject): (Vector2, Vector2)
	return o.AbsolutePosition, o.AbsolutePosition + o.AbsoluteSize
end
-- рамка самого текста (надписи выровнены влево, по высоте — по центру)
local function textRect(t: TextLabel): (Vector2, Vector2)
	local a = t.AbsolutePosition
	local s, b = t.AbsoluteSize, t.TextBounds
	local x0 = if t.TextXAlignment == Enum.TextXAlignment.Left
		then a.X
		elseif t.TextXAlignment == Enum.TextXAlignment.Right then a.X + s.X - b.X
		else a.X + (s.X - b.X) / 2
	local y0 = a.Y + (s.Y - b.Y) / 2
	return Vector2.new(x0, y0), Vector2.new(x0 + b.X, y0 + b.Y)
end
local function overlap(a0: Vector2, a1: Vector2, b0: Vector2, b1: Vector2): boolean
	return a0.X < b1.X - 1 and b0.X < a1.X - 1 and a0.Y < b1.Y - 1 and b0.Y < a1.Y - 1
end

local scale = fen.WindowScale.Scale
local size = fen.AbsoluteSize
table.insert(
	out,
	("экран %d×%d%s, окно %d×%d px (масштаб %.2f)"):format(
		vp.X,
		vp.Y,
		if touch then " касание" else "",
		size.X,
		size.Y,
		scale
	)
)
line(
	size.X <= vp.X - 2 * MARGIN + 1 and size.Y <= vp.Y - inset - 2 * MARGIN + 1,
	("окно умещается: по ширине запас %d px, по высоте %d px (под кнопками Roblox %d px)"):format(
		vp.X - 2 * MARGIN - size.X,
		vp.Y - inset - 2 * MARGIN - size.Y,
		inset
	)
)

local corps = fen.Corps
local buy = corps.Ameliorer
line(
	not touch or buy.AbsoluteSize.Y >= MIN_TOUCH - 0.5,
	("кнопка «%s»: %d×%d px"):format(buy.Texte.Text, buy.AbsoluteSize.X, buy.AbsoluteSize.Y)
)

-- надписи: умещаются и читаются
local texts, smallest, smallestName, unfit = {}, math.huge, "", {}
for _, d in fen:GetDescendants() do
	if d:IsA("TextLabel") and d.Visible and d.Text ~= "" and not string.find(d.Name, "Ombre") then
		table.insert(texts, d)
		local height = d.TextBounds.Y
		if d.Parent ~= buy and height < smallest then
			smallest, smallestName = height, d.Name .. " «" .. string.sub(d.ContentText, 1, 40) .. "»"
		end
		if not d.TextFits then
			table.insert(unfit, d.Name)
		end
	end
end
line(#unfit == 0, ("надписей %d, не умещаются: %s"):format(#texts, if #unfit == 0 then "нет" else table.concat(unfit, ", ")))
line(smallest >= MIN_TEXT, ("самая мелкая надпись: %.0f px — %s"):format(smallest, smallestName))

-- строки карточек одного размера (в каждой карточке)
for _, name in { "Maintenant", "Apres" } do
	local box = corps[name]
	local sizes = {}
	for i = 1, 3 do
		local t = box["Ligne" .. i]
		if t.Text ~= "" then
			table.insert(sizes, math.floor(t.TextBounds.Y + 0.5))
		end
	end
	local same = true
	for _, s in sizes do
		same = same and math.abs(s - sizes[1]) <= 1
	end
	line(same, ("карточка %s: высота строк %s px"):format(name, table.concat(sizes, ", ")))
end

-- стрелка и иконки не закрывают надписи
local covers = {}
local blockers = { corps.Fleche, corps.Maintenant.Vitrine, corps.Apres.Vitrine }
for _, blocker in blockers do
	if blocker.Visible then
		local b0, b1 = rect(blocker)
		for _, t in texts do
			if t:IsDescendantOf(corps.Maintenant) or t:IsDescendantOf(corps.Apres) then
				local t0, t1 = textRect(t)
				if overlap(b0, b1, t0, t1) then
					table.insert(covers, blocker.Name .. " × " .. t.Name)
				end
			end
		end
	end
end
line(#covers == 0, "стрелка и иконки поверх надписей: " .. (if #covers == 0 then "нет" else table.concat(covers, ", ")))

-- 20 мест: внутри окна, по порядку, без наложений
local w0, w1 = rect(fen)
local inside, apart, last = true, true, nil
local pip = 0
for slot = 1, 20 do
	local frame = corps["Place" .. slot]
	local p0, p1 = rect(frame)
	pip = frame.AbsoluteSize.X
	inside = inside and p0.X >= w0.X and p1.X <= w1.X and p0.Y >= w0.Y and p1.Y <= w1.Y
	if last then
		apart = apart and p0.X >= last
	end
	last = p1.X
end
line(inside and apart, ("20 мест: квадратик %.0f px, внутри окна и не налезают"):format(pip))

-- меню HUD на этом экране: столбцов, и не задевает ли кнопку прыжка (зоны — как в scripts/studio/hud_phone_sim.luau)
local column = pg.MenuHud.Colonne
local layout = column:FindFirstChildOfClass("UIGridLayout")
local hudScale = math.clamp(math.min(vp.X / 1050, vp.Y / 620), 0.52, 1.18)
local unit = column.AbsoluteSize / column.WindowScale.Scale -- размер меню при масштабе 1
local menu = unit * hudScale
-- по центру экрана или, у сетки на касании, на своей высоте (UI/MenuHud ставит её между «Ударом» и прыжком)
local centerY = if column.Position.Y.Scale > 0 then vp.Y / 2 else column.Position.Y.Offset
local top, low = centerY - menu.Y / 2, centerY + menu.Y / 2
local small = math.min(vp.X, vp.Y) <= 500
local jumpTop = if not touch then vp.Y elseif small then vp.Y - 90 else vp.Y - 210
line(
	top >= 48 and low <= jumpTop,
	("меню HUD: столбцов %d, %d×%d px, по высоте %d…%d (кнопки Roblox до 48, %s %d)"):format(
		layout.FillDirectionMaxCells,
		menu.X,
		menu.Y,
		top,
		low,
		if touch then "прыжок с" else "низ экрана",
		jumpTop
	)
)
table.insert(out, if problems == 0 then "ИТОГ: замечаний нет" else ("ИТОГ: замечаний %d"):format(problems))
return table.concat(out, "\n")

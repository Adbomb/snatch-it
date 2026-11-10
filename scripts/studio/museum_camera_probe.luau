-- Проверка камеры в музее (D55): клиент в Play через MCP execute_luau (Studio на переднем плане — иначе RenderStep
-- не идёт). Музей своего участка заполнен (DevTools MuseumLevel / Exhibit). Персонаж ставится в точки зала и
-- галерей, камера Roblox — на 12 стадов (Min = Max zoom), по кругу: поворот 0…330° через 30°, наклон +8° (снизу),
-- −5°, −20°, −40°. В каждом положении считается: прижалась ли камера (< 10.5 при отрезке без помех), закрыты ли голова
-- и корень персонажа видимыми деталями участка (прозрачность с локальной < 0.5; экспонаты — по видимым деталям),
-- закрыты ли ближайшие экспонаты той же части музея (до 10 стадов, в кадре; свой постамент не считается) и не внутри
-- ли камера места (тумба и экспонат над ней). Печатает сводку и чем закрыто. Меняет только позицию персонажа и зум
-- (зум возвращается).

local P = game:GetService("Players").LocalPlayer
local RS = game:GetService("RunService")
local L = require(game:GetService("ReplicatedStorage").Shared.Config.MuseumLayout)
local plot
for _, p in workspace.World.Plots:GetChildren() do
	if p:GetAttribute("OwnerUserId") == P.UserId then
		plot = p
	end
end
local o = plot:GetAttribute("FloorOrigin")
local ch = P.Character
local root = ch.HumanoidRootPart
local cam = workspace.CurrentCamera
local function box(part)
	return {
		part = part,
		inv = part.CFrame:Inverse(),
		half = part.Size / 2,
		center = part.Position,
		radius = (part.Size / 2).Magnitude,
	}
end
local boxes, exhibits = {}, {}
for _, d in plot:GetDescendants() do
	if d:IsA("BasePart") and not d:IsDescendantOf(plot.Exhibits) and d.Transparency < 0.5 then
		table.insert(boxes, box(d))
	end
end
for _, ex in plot.Exhibits:GetChildren() do
	if ex:IsA("BasePart") then
		local b = box(ex)
		b.slot = ex:GetAttribute("Slot")
		table.insert(exhibits, b)
	end
end
local function hits(b, a, c)
	local ab = c - a
	local len2 = ab:Dot(ab)
	local t = if len2 > 1e-6 then math.clamp((b.center - a):Dot(ab) / len2, 0, 1) else 0
	if (a + ab * t - b.center).Magnitude > b.radius then
		return false
	end
	local oo, dd = b.inv * a, b.inv:VectorToWorldSpace(ab)
	local t0, t1 = 0, 1
	for _, axis in { "X", "Y", "Z" } do
		local oa, da, h = oo[axis], dd[axis], b.half[axis]
		if math.abs(da) < 1e-6 then
			if oa < -h or oa > h then
				return false
			end
		else
			local u, v = (-h - oa) / da, (h - oa) / da
			if u > v then
				u, v = v, u
			end
			t0, t1 = math.max(t0, u), math.min(t1, v)
			if t0 > t1 then
				return false
			end
		end
	end
	return true
end
-- экспонат виден, если хотя бы одна его видимая деталь не погашена
local function exhibitOpaque(part)
	for _, d in { part, table.unpack(part:GetDescendants()) } do
		if d:IsA("BasePart") and d.Transparency < 0.95 and d.Transparency + d.LocalTransparencyModifier < 0.5 then
			return true
		end
	end
	return false
end
local kinds = {}
local function blockers(a, c, skip, withExhibits)
	local list = {}
	for _, b in boxes do
		local p = b.part
		if
			p.Parent
			and p.Transparency + p.LocalTransparencyModifier < 0.5
			and not (skip and (p == skip or p:IsDescendantOf(skip)))
			and hits(b, a, c)
		then
			local key = p.Parent.Name .. "/" .. p.Name
			table.insert(list, key)
			kinds[key] = (kinds[key] or 0) + 1
		end
	end
	if withExhibits then
		for _, b in exhibits do
			if exhibitOpaque(b.part) and hits(b, a, c) then
				local key = "экспонат " .. tostring(b.slot)
				table.insert(list, key)
				kinds[key] = (kinds[key] or 0) + 1
			end
		end
	end
	return list
end
local function sideOf(pos)
	local x = o:PointToObjectSpace(pos).X
	return if x > L.Hall.HalfWidth then 1 elseif x < -L.Hall.HalfWidth then -1 else 0
end
-- места: тумба + экспонат над ней
local columns = {}
for _, sc in plot.Showcases:GetChildren() do
	local slot = sc:GetAttribute("Slot")
	local top = sc.Position.Y + sc.Size.Y / 2
	for _, b in exhibits do
		if b.slot == slot then
			top = math.max(top, b.center.Y + b.half.Y)
		end
	end
	table.insert(columns, { cf = sc.CFrame, half = sc.Size / 2, bottom = sc.Position.Y - sc.Size.Y / 2, top = top })
end
local function insideColumn(c)
	for _, col in columns do
		local l = col.cf:PointToObjectSpace(c)
		if math.abs(l.X) < col.half.X and math.abs(l.Z) < col.half.Z and c.Y > col.bottom and c.Y < col.top then
			return true
		end
	end
	return false
end
P.CameraMinZoomDistance, P.CameraMaxZoomDistance = 12, 12
local spots = {
	hall = Vector3.new(0, 3, 4),
	hallSlot1 = Vector3.new(9.6, 3, -2),
	hallSlot6 = Vector3.new(-9.6, 3, 10.2),
	galL = Vector3.new(-21.5, 3, 3.75),
	galL2 = Vector3.new(-21.5, 3, -14.5),
	galR = Vector3.new(21.5, 3, 9.85),
	galR2 = Vector3.new(21.5, 3, -2.35),
}
local report, total = {}, { n = 0, short = 0, body = 0, ex = 0, inside = 0 }
for name, at in spots do
	root.CFrame = o * CFrame.new(at)
	for _ = 1, 10 do
		RS.RenderStepped:Wait()
	end
	local short, bodyBlocked, exBlocked, inside, n = 0, 0, 0, 0, 0
	local samples = {}
	for yaw = 0, 330, 30 do
		for _, pitch in { 8, -5, -20, -40 } do
			local focus = cam.Focus.Position
			local dir = (CFrame.Angles(0, math.rad(yaw), 0) * CFrame.Angles(math.rad(pitch), 0, 0)).LookVector
			cam.CFrame = CFrame.lookAt(focus - dir * 12, focus)
			for _ = 1, 4 do
				RS.RenderStepped:Wait()
			end
			local camPos = cam.CFrame.Position
			local d = (camPos - cam.Focus.Position).Magnitude
			n += 1
			local isInside = insideColumn(camPos)
			if isInside then
				inside += 1
			end
			local hb = blockers(camPos, ch.Head.Position, nil, true)
			local rb = blockers(camPos, root.Position, nil, true)
			if #hb > 0 or #rb > 0 then
				bodyBlocked += 1
			end
			if d < 10.5 then
				short += 1
			end
			local eb = {}
			local side = sideOf(root.Position)
			for _, b in exhibits do
				local ex = b.part
				if sideOf(ex.Position) == side and (ex.Position - root.Position).Magnitude < 10 then
					local _, onScreen = cam:WorldToViewportPoint(ex.Position)
					if onScreen then
						local own = b.slot and plot.Showcases:FindFirstChild("Showcase_" .. b.slot)
						local bl = blockers(camPos, ex.Position, own, false)
						if #bl > 0 then
							table.insert(eb, (b.slot or "?") .. ":" .. bl[1])
						end
					end
				end
			end
			if #eb > 0 then
				exBlocked += 1
			end
			if (#hb > 0 or #rb > 0 or #eb > 0 or isInside) and #samples < 3 then
				table.insert(
					samples,
					("y%d p%d d%.1f%s голова[%s] тело[%s] эксп[%s]"):format(
						yaw,
						pitch,
						d,
						if isInside then " ВНУТРИ МЕСТА" else "",
						table.concat(hb, ","),
						table.concat(rb, ","),
						table.concat(eb, " ")
					)
				)
			end
		end
	end
	total.n += n
	total.short += short
	total.body += bodyBlocked
	total.ex += exBlocked
	total.inside += inside
	table.insert(
		report,
		("%s: проб %d, ближе 10.5 — %d, игрок закрыт %d, экспонат закрыт %d, камера в месте %d\n   %s"):format(
			name,
			n,
			short,
			bodyBlocked,
			exBlocked,
			inside,
			table.concat(samples, "\n   ")
		)
	)
end
P.CameraMinZoomDistance, P.CameraMaxZoomDistance = 0.5, 400
local k = {}
for key, c in kinds do
	table.insert(k, key .. "=" .. c)
end
table.sort(k)
local viewport = cam.ViewportSize
return ("Экран %dx%d. Проб %d: камера ближе 10.5 — %d, игрок закрыт %d, экспонат закрыт %d, камера внутри места %d\n"):format(
	viewport.X,
	viewport.Y,
	total.n,
	total.short,
	total.body,
	total.ex,
	total.inside
) .. table.concat(report, "\n") .. "\nЧем закрыто: " .. table.concat(k, ", ")

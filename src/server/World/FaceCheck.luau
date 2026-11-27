-- Проверка мерцания (D36): ищет видимые пары совпадающих граней — две детали, у которых грани лежат в одной
-- плоскости, смотрят в одну сторону и перекрываются по площади, причём точка прямо перед гранью не закрыта
-- третьей деталью. Такие пары дают z-fighting при движении камеры. Учитываются только бруски, стоящие по осям
-- (повёрнутые, шары и цилиндры пропускаются), прозрачные больше чем наполовину — тоже.
-- Вызывается через MCP в Edit после Preview.Build:
--   local W = game.ServerScriptService.Server.World
--   require(W.FreshRequire)(W.FaceCheck).Report(workspace.__Preview)
-- Ни от чего не зависит.

local FaceCheck = {}

local CELL = 16 -- сетка поиска закрывающих деталей, стадов
local BIG = 400 -- детали больше этого по X или Z проверяются отдельно (земля, обрывы)
local PROBES = { 0.2, 0.5, 0.8 }

type Box = { part: BasePart, lo: Vector3, hi: Vector3 }

local function aligned(cf: CFrame): boolean
	for _, v in { cf.RightVector, cf.UpVector, cf.LookVector } do
		if math.max(math.abs(v.X), math.abs(v.Y), math.abs(v.Z)) < 0.999 then
			return false
		end
	end
	return true
end

-- Пары: { count, groups = { ["Модель/Деталь × Модель/Деталь"] = { n, example } } }.
function FaceCheck.Scan(root: Instance): (number, { [string]: { n: number, example: string } })
	local boxes: { Box } = {}
	local grid: { [string]: { Box } } = {}
	local big: { Box } = {}
	local faces: { [string]: { any } } = {}
	for i, p in root:GetDescendants() do
		if p:IsA("Part") and p.Shape == Enum.PartType.Block and p.Transparency < 0.5 and aligned(p.CFrame) then
			local r = p.CFrame:VectorToWorldSpace(p.Size / 2)
			r = Vector3.new(math.abs(r.X), math.abs(r.Y), math.abs(r.Z))
			local b: Box = { part = p, lo = p.Position - r, hi = p.Position + r }
			table.insert(boxes, b)
			if b.hi.X - b.lo.X >= BIG or b.hi.Z - b.lo.Z >= BIG then
				table.insert(big, b)
			else
				for gx = math.floor(b.lo.X / CELL), math.floor(b.hi.X / CELL) do
					for gz = math.floor(b.lo.Z / CELL), math.floor(b.hi.Z / CELL) do
						local key = gx .. ":" .. gz
						grid[key] = grid[key] or {}
						table.insert(grid[key], b)
					end
				end
			end
			local lo, hi = { b.lo.X, b.lo.Y, b.lo.Z }, { b.hi.X, b.hi.Y, b.hi.Z }
			for axis = 1, 3 do
				local a1, a2 = axis % 3 + 1, (axis + 1) % 3 + 1
				for _, s in { -1, 1 } do
					local coord = if s > 0 then hi[axis] else lo[axis]
					local key = axis * 10 + s + 1 .. ":" .. math.round(coord * 20)
					faces[key] = faces[key] or {}
					table.insert(faces[key], {
						box = b,
						axis = axis,
						s = s,
						coord = coord,
						a1 = a1,
						a2 = a2,
						u0 = lo[a1],
						u1 = hi[a1],
						v0 = lo[a2],
						v1 = hi[a2],
					})
				end
			end
		end
		if i % 3000 == 0 then
			task.wait()
		end
	end

	local function covered(pt: Vector3, a: Box, b: Box): boolean
		local function test(list: { Box }): boolean
			for _, o in list do
				if
					o ~= a
					and o ~= b
					and pt.X > o.lo.X + 1e-3
					and pt.X < o.hi.X - 1e-3
					and pt.Y > o.lo.Y + 1e-3
					and pt.Y < o.hi.Y - 1e-3
					and pt.Z > o.lo.Z + 1e-3
					and pt.Z < o.hi.Z - 1e-3
				then
					return true
				end
			end
			return false
		end
		return test(grid[math.floor(pt.X / CELL) .. ":" .. math.floor(pt.Z / CELL)] or {}) or test(big)
	end

	local count, groups = 0, {}
	for _, list in faces do
		for i = 1, #list do
			for j = i + 1, #list do
				local f, g = list[i], list[j]
				local u0, u1 = math.max(f.u0, g.u0), math.min(f.u1, g.u1)
				local v0, v1 = math.max(f.v0, g.v0), math.min(f.v1, g.v1)
				if u1 - u0 > 0.05 and v1 - v0 > 0.05 then
					local visible = false
					for _, fu in PROBES do
						for _, fv in PROBES do
							local c = {}
							c[f.axis] = f.coord + f.s * 0.03
							c[f.a1] = u0 + (u1 - u0) * fu
							c[f.a2] = v0 + (v1 - v0) * fv
							if not covered(Vector3.new(c[1], c[2], c[3]), f.box, g.box) then
								visible = true
							end
						end
					end
					if visible then
						count += 1
						local function tag(x): string
							local parent = x.box.part.Parent
							return (if parent then parent.Name else "?") .. "/" .. x.box.part.Name
						end
						local key = tag(f) .. " × " .. tag(g)
						local group = groups[key] or { n = 0, example = "" }
						group.n += 1
						if group.example == "" then
							local axisName = ({ "x", "y", "z" })[f.axis]
							group.example = ("%s = %.2f у %s"):format(axisName, f.coord, tostring(f.box.part.Position))
						end
						groups[key] = group
					end
				end
			end
		end
	end
	return count, groups
end

-- ── Грани под любым углом (2026-11-14) ──────────────────────────────────────────────────────────────────────────
-- Scan видит только бруски по осям. ScanAny ищет то же мерцание у повёрнутых брусков, клиньев и торцов цилиндров
-- (на них стоят вывески под наклоном, ромбы, диски-площадки): две грани смотрят в одну сторону (угол между
-- нормалями меньше ≈ 1.8°), лежат почти в одной плоскости (ближе PLANE) и перекрываются по площади больше MIN_AREA,
-- а точка перед общим участком не закрыта третьей деталью (брусок, клин, цилиндр, шар). Пары двух брусков по осям
-- считает Scan — здесь их нет.
local PLANE = 0.015
local SAME = 0.9995 -- косинус угла между нормалями
local MIN_AREA = 0.05
local NQ = 50 -- шаг корзин нормалей 0.02
local DQ = 20 -- шаг корзин плоскостей 0.05
local CAP = 16 -- торец цилиндра — правильный 16-угольник

type Face = { part: any, n: Vector3, d: number, mid: Vector3, pts: { Vector3 }, axisPart: boolean }
type Solid = { part: any, cf: CFrame, half: Vector3, lo: Vector3, hi: Vector3, shape: any }

-- Многоугольник a, обрезанный выпуклым многоугольником clip (оба — точки на плоскости {x, y}, clip против часовой).
local function clipPolygon(a: { { number } }, clip: { { number } }): { { number } }
	local out = a
	for i = 1, #clip do
		local p, q = clip[i], clip[i % #clip + 1]
		local function inside(v): boolean
			return (q[1] - p[1]) * (v[2] - p[2]) - (q[2] - p[2]) * (v[1] - p[1]) >= -1e-9
		end
		local input = out
		out = {}
		for j = 1, #input do
			local s, e = input[j], input[j % #input + 1]
			local sIn, eIn = inside(s), inside(e)
			if sIn then
				table.insert(out, s)
			end
			if sIn ~= eIn then
				local dx, dy = e[1] - s[1], e[2] - s[2]
				local den = (q[1] - p[1]) * dy - (q[2] - p[2]) * dx
				if math.abs(den) > 1e-12 then
					local t = ((q[1] - p[1]) * (p[2] - s[2]) - (q[2] - p[2]) * (p[1] - s[1])) / den
					table.insert(out, { s[1] + dx * t, s[2] + dy * t })
				end
			end
		end
		if #out == 0 then
			return out
		end
	end
	return out
end

local function area(poly: { { number } }): number
	local sum = 0
	for i = 1, #poly do
		local a, b = poly[i], poly[i % #poly + 1]
		sum += a[1] * b[2] - b[1] * a[2]
	end
	return sum / 2
end

-- Форма детали: у Part — Shape, клин WedgePart — Wedge; другое — nil.
local function shapeOf(p: any): any
	if p:IsA("WedgePart") then
		return Enum.PartType.Wedge
	end
	return if p:IsA("Part") then p.Shape else nil
end

-- Грани детали: бруска (6), клина (5) или торцы цилиндра (2); nil — другая форма.
local function facesOf(p: any): { { Vector3 } }?
	local cf, s = p.CFrame, p.Size / 2
	local function w(x: number, y: number, z: number): Vector3
		return cf * Vector3.new(x, y, z)
	end
	local shape = shapeOf(p)
	if shape == Enum.PartType.Block then
		local x, y, z = s.X, s.Y, s.Z
		return {
			{ w(x, -y, -z), w(x, y, -z), w(x, y, z), w(x, -y, z) },
			{ w(-x, -y, -z), w(-x, -y, z), w(-x, y, z), w(-x, y, -z) },
			{ w(-x, y, -z), w(-x, y, z), w(x, y, z), w(x, y, -z) },
			{ w(-x, -y, -z), w(x, -y, -z), w(x, -y, z), w(-x, -y, z) },
			{ w(-x, -y, z), w(x, -y, z), w(x, y, z), w(-x, y, z) },
			{ w(-x, -y, -z), w(-x, y, -z), w(x, y, -z), w(x, -y, -z) },
		}
	elseif shape == Enum.PartType.Wedge then
		local x, y, z = s.X, s.Y, s.Z
		return {
			{ w(-x, -y, -z), w(x, -y, -z), w(x, -y, z), w(-x, -y, z) }, -- низ
			{ w(-x, -y, z), w(x, -y, z), w(x, y, z), w(-x, y, z) }, -- зад
			{ w(-x, -y, -z), w(-x, y, z), w(x, y, z), w(x, -y, -z) }, -- скат
			{ w(x, -y, -z), w(x, y, z), w(x, -y, z) },
			{ w(-x, -y, -z), w(-x, -y, z), w(-x, y, z) },
		}
	elseif shape == Enum.PartType.Cylinder then
		local r = math.min(s.Y, s.Z)
		local caps = {}
		for _, side in { -1, 1 } do
			local pts = {}
			for k = 0, CAP - 1 do
				local a = 2 * math.pi * k / CAP
				table.insert(pts, w(side * s.X, r * math.cos(a), r * math.sin(a)))
			end
			table.insert(caps, pts)
		end
		return caps
	end
	return nil
end

-- Пары (как Scan): число и группы «Модель/Деталь × Модель/Деталь».
function FaceCheck.ScanAny(root: Instance): (number, { [string]: { n: number, example: string } }, { any })
	local faces: { Face } = {}
	local buckets: { [string]: { Face } } = {}
	local grid: { [string]: { Solid } } = {}
	local big: { Solid } = {}
	local function bucketKey(n: Vector3, d: number, dx: number, dy: number, dz: number, dd: number): string
		return ("%d:%d:%d:%d"):format(
			math.round(n.X * NQ) + dx,
			math.round(n.Y * NQ) + dy,
			math.round(n.Z * NQ) + dz,
			math.floor(d * DQ) + dd
		)
	end
	for i, p in root:GetDescendants() do
		local shape = if p:IsA("BasePart") and p.Transparency < 0.5 then shapeOf(p) else nil
		if shape then
			local polys = facesOf(p)
			local center = p.CFrame.Position
			if polys then
				local axisPart = shape == Enum.PartType.Block and aligned(p.CFrame)
				for _, pts in polys do
					local mid = Vector3.new(0, 0, 0)
					for _, v in pts do
						mid += v
					end
					mid /= #pts
					local n = (pts[2] - pts[1]):Cross(pts[3] - pts[1])
					if n.Magnitude > 1e-6 then
						n = n.Unit
						if n:Dot(mid - center) < 0 then
							n = -n
						end
						local f: Face = { part = p, n = n, d = n:Dot(mid), mid = mid, pts = pts, axisPart = axisPart }
						table.insert(faces, f)
						local key = bucketKey(n, f.d, 0, 0, 0, 0)
						buckets[key] = buckets[key] or {}
						table.insert(buckets[key], f)
					end
				end
			end
			if shape ~= Enum.PartType.CornerWedge then
				local ext = Vector3.new(0, 0, 0)
				local cf, size = p.CFrame, p.Size
				for _, v in { cf.RightVector * size.X / 2, cf.UpVector * size.Y / 2, cf.LookVector * size.Z / 2 } do
					ext += Vector3.new(math.abs(v.X), math.abs(v.Y), math.abs(v.Z))
				end
				local s: Solid = {
					part = p,
					cf = p.CFrame,
					half = p.Size / 2,
					lo = center - ext,
					hi = center + ext,
					shape = shape,
				}
				if ext.X * 2 >= BIG or ext.Z * 2 >= BIG then
					table.insert(big, s)
				else
					for gx = math.floor(s.lo.X / CELL), math.floor(s.hi.X / CELL) do
						for gz = math.floor(s.lo.Z / CELL), math.floor(s.hi.Z / CELL) do
							local key = gx .. ":" .. gz
							grid[key] = grid[key] or {}
							table.insert(grid[key], s)
						end
					end
				end
			end
		end
		if i % 3000 == 0 then
			task.wait()
		end
	end

	local function inside(o: Solid, pt: Vector3): boolean
		local l = o.cf:PointToObjectSpace(pt)
		local h, e = o.half, 1e-3
		if math.abs(l.X) >= h.X - e or math.abs(l.Y) >= h.Y - e or math.abs(l.Z) >= h.Z - e then
			return false
		end
		if o.shape == Enum.PartType.Cylinder then
			local r = math.min(h.Y, h.Z) - e
			return l.Y * l.Y + l.Z * l.Z < r * r
		elseif o.shape == Enum.PartType.Ball then
			local r = math.min(h.X, h.Y, h.Z) - e
			return l.Magnitude < r
		elseif o.shape == Enum.PartType.Wedge then
			return l.Y / h.Y < l.Z / h.Z -- ниже ската (скат — от верха сзади к низу спереди)
		end
		return true
	end
	local function covered(pt: Vector3, a: any, b: any): boolean
		for _, list in { grid[math.floor(pt.X / CELL) .. ":" .. math.floor(pt.Z / CELL)] or {}, big } do
			for _, o in list do
				if o.part ~= a and o.part ~= b and inside(o, pt) then
					return true
				end
			end
		end
		return false
	end

	local seen: { [string]: boolean } = {} -- пара деталей считается один раз
	local ids: { [any]: number } = {}
	local lastId = 0
	local function id(p: any): number
		if not ids[p] then
			lastId += 1
			ids[p] = lastId
		end
		return ids[p]
	end
	local count, groups = 0, {}
	local list = {} -- пары подробно: { a, b, at, area } (до 2000)
	for fi, f in faces do
		-- плоскость грани f: оси u, v
		local u = (f.pts[2] - f.pts[1]).Unit
		local v = f.n:Cross(u)
		local origin = f.pts[1]
		local function flat(pt: Vector3): { number }
			local r = pt - origin
			return { r:Dot(u), r:Dot(v) }
		end
		local clip = {}
		for _, pt in f.pts do
			table.insert(clip, flat(pt))
		end
		if area(clip) < 0 then
			local rev = {}
			for k = #clip, 1, -1 do
				table.insert(rev, clip[k])
			end
			clip = rev
		end
		for dx = -1, 1 do
			for dy = -1, 1 do
				for dz = -1, 1 do
					for dd = -1, 1 do
						for _, g in buckets[bucketKey(f.n, f.d, dx, dy, dz, dd)] or {} do
							if
								g.part ~= f.part
								and not (f.axisPart and g.axisPart)
								and f.n:Dot(g.n) >= SAME
								-- расстояние между плоскостями — от точки к точке: разность d = n·mid вдали от начала
								-- координат (предпросмотр у x = 4000) ошибается на десятые доли стада — крошечная
								-- погрешность нормали умножается на тысячи стадов (ложные пары, 2026-11-27)
								and math.abs(f.n:Dot(g.mid - f.mid)) <= PLANE
							then
								local a, b = id(f.part), id(g.part)
								local poly = {}
								for _, pt in g.pts do
									table.insert(poly, flat(pt))
								end
								if area(poly) < 0 then
									local rev = {}
									for k = #poly, 1, -1 do
										table.insert(rev, poly[k])
									end
									poly = rev
								end
								local common = clipPolygon(poly, clip)
								local s = if #common >= 3 then math.abs(area(common)) else 0
								local pairKey = if a < b then a .. ":" .. b else b .. ":" .. a
								if s > MIN_AREA and not seen[pairKey] then
									local cx, cy = 0, 0
									for _, c in common do
										cx += c[1]
										cy += c[2]
									end
									cx /= #common
									cy /= #common
									local visible = false
									local probes = { { cx, cy } }
									for k = 1, math.min(4, #common) do
										local c = common[math.floor((k - 1) * #common / 4) + 1]
										table.insert(probes, { (cx + c[1]) / 2, (cy + c[2]) / 2 })
									end
									for _, pr in probes do
										local pt = origin + u * pr[1] + v * pr[2] + f.n * 0.03
										if not covered(pt, f.part, g.part) then
											visible = true
											break
										end
									end
									if visible then
										seen[pairKey] = true
										if #list < 2000 then
											table.insert(
												list,
												{ a = f.part, b = g.part, at = origin + u * cx + v * cy, area = s }
											)
										end
										count += 1
										local function tag(x: any): string
											local parent = x.Parent
											return (if parent then parent.Name else "?") .. "/" .. x.Name
										end
										local gkey = tag(f.part) .. " × " .. tag(g.part)
										local group = groups[gkey] or { n = 0, example = "" }
										group.n += 1
										if group.example == "" then
											local at = origin + u * cx + v * cy
											group.example = ("у (%.1f, %.1f, %.1f), площадь %.2f"):format(
												at.X,
												at.Y,
												at.Z,
												s
											)
										end
										groups[gkey] = group
									end
								end
							end
						end
					end
				end
			end
		end
		if fi % 4000 == 0 then
			task.wait()
		end
	end
	return count, groups, list
end

-- Отчёт строкой: число видимых пар (по осям и под любым углом) и до 20 самых частых групп.
function FaceCheck.Report(root: Instance): string
	local count, groups = FaceCheck.Scan(root)
	local countAny, groupsAny = FaceCheck.ScanAny(root)
	count += countAny
	for key, group in groupsAny do
		groups["∠ " .. key] = group
	end
	local list = {}
	for key, group in groups do
		table.insert(list, { key = key, n = group.n, example = group.example })
	end
	table.sort(list, function(a, b)
		return a.n > b.n
	end)
	local lines = { ("Видимых пар совпадающих граней: %d"):format(count) }
	for k = 1, math.min(20, #list) do
		table.insert(lines, ("%d × %s  [%s]"):format(list[k].n, list[k].key, list[k].example))
	end
	return table.concat(lines, "\n")
end

return FaceCheck

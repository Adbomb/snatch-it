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
				if o ~= a and o ~= b and pt.X > o.lo.X + 1e-3 and pt.X < o.hi.X - 1e-3 and pt.Y > o.lo.Y + 1e-3
					and pt.Y < o.hi.Y - 1e-3 and pt.Z > o.lo.Z + 1e-3 and pt.Z < o.hi.Z - 1e-3
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

-- Отчёт строкой: число видимых пар и до 20 самых частых групп.
function FaceCheck.Report(root: Instance): string
	local count, groups = FaceCheck.Scan(root)
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

-- Предпросмотр босса из мешей Blender без загрузки в Roblox (только Studio, в Edit через MCP; интеграция босса 4
-- 2026-11-12): данные Tests/MeshFixture/Boss<N>_<Часть> (scripts/blender/boss4_sphinx_fixture.py, в репозиторий не
-- идут) → EditableMesh каждой части → MeshPart с картами из Server/Looks (Boss<N>_<группа>). Build ставит модель в
-- место босса, Pose — суставы в позу BossAnim.Sample по цепочке (сустав = родитель · сдвиг(pivot − pivot родителя) ·
-- Transform): в Edit физика не считает Transform моторов. Модель — workspace.__BossMeshPreview<N>; после проверки
-- удалить. Зависит от AssetService, Config/Boss4SphinxRig, Shared/BossAnim.

local AssetService = game:GetService("AssetService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local BossAnim = require(ReplicatedStorage.Shared.BossAnim)

local RIGS = { [4] = require(ReplicatedStorage.Shared.Config.Boss4SphinxRig) :: any }

local BossMeshPreview = {}

local ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
local LOOKUP: { [number]: number } = {}
for i = 1, 64 do
	LOOKUP[string.byte(ALPHABET, i)] = i - 1
end
local VERTEX = 13 -- байт на вершину (scripts/blender/boss4_sphinx_fixture.py)

local function decode(s: string): buffer
	local pad = if string.sub(s, -2) == "==" then 2 elseif string.sub(s, -1) == "=" then 1 else 0
	local size = #s // 4 * 3 - pad
	local out = buffer.create(size)
	local o = 0
	for i = 1, #s, 4 do
		local a, b, c, d = string.byte(s, i, i + 3)
		local v = LOOKUP[a] * 262144 + LOOKUP[b] * 4096 + (LOOKUP[c] or 0) * 64 + (LOOKUP[d] or 0)
		for k = 2, 0, -1 do
			if o < size then
				buffer.writeu8(out, o, (v // 256 ^ k) % 256)
			end
			o += 1
		end
	end
	return out
end

local function fixture(zone: number, part: string): any
	local folder = script.Parent:FindFirstChild("MeshFixture")
	local module = folder and folder:FindFirstChild(("Boss%d_%s"):format(zone, part))
	return if module then (require :: any)(module) else nil
end

-- Есть ли данные предпросмотра у всех частей босса zone.
function BossMeshPreview.Has(zone: number): boolean
	local rig = RIGS[zone]
	if not rig then
		return false
	end
	for _, part in rig.Order do
		if not fixture(zone, part) then
			return false
		end
	end
	return true
end

-- Вершины части (от её точки вращения, оси Roblox); nil — данных предпросмотра нет. Для проверок по настоящей форме.
function BossMeshPreview.Points(zone: number, part: string): { Vector3 }?
	local data = fixture(zone, part)
	if not data then
		return nil
	end
	local vb = decode(data.v)
	local out = table.create(data.nv)
	for i = 0, data.nv - 1 do
		local o = i * VERTEX
		out[i + 1] = Vector3.new(buffer.readi16(vb, o), buffer.readi16(vb, o + 2), buffer.readi16(vb, o + 4)) / data.pos
	end
	return out
end

local function meshPart(zone: number, data: any): MeshPart
	local mesh = AssetService:CreateEditableMesh()
	local vb, tb = decode(data.v), decode(data.t)
	local verts, normals, uvs = table.create(data.nv), table.create(data.nv), table.create(data.nv)
	for i = 0, data.nv - 1 do
		local o = i * VERTEX
		local at = Vector3.new(buffer.readi16(vb, o), buffer.readi16(vb, o + 2), buffer.readi16(vb, o + 4)) / data.pos
		local normal = Vector3.new(buffer.readi8(vb, o + 6), buffer.readi8(vb, o + 7), buffer.readi8(vb, o + 8))
		verts[i + 1] = mesh:AddVertex(at)
		normals[i + 1] = mesh:AddNormal(if normal.Magnitude > 0 then normal.Unit else Vector3.yAxis)
		uvs[i + 1] = mesh:AddUV(Vector2.new(buffer.readu16(vb, o + 9), buffer.readu16(vb, o + 11)) / 65535)
	end
	for t = 0, data.nt - 1 do
		local a = buffer.readu16(tb, t * 6) + 1
		local b = buffer.readu16(tb, t * 6 + 2) + 1
		local c = buffer.readu16(tb, t * 6 + 4) + 1
		local face = mesh:AddTriangle(verts[a], verts[b], verts[c])
		mesh:SetFaceNormals(face, { normals[a], normals[b], normals[c] })
		mesh:SetFaceUVs(face, { uvs[a], uvs[b], uvs[c] })
	end
	local part = AssetService:CreateMeshPartAsync(Content.fromObject(mesh), {
		CollisionFidelity = Enum.CollisionFidelity.Box,
	})
	part.Name = data.part
	part.Material = Enum.Material.SmoothPlastic
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	local look = ServerScriptService.Server.Looks:FindFirstChild(("Boss%d_%s"):format(zone, data.map))
	if look then
		look:Clone().Parent = part
	end
	return part
end

-- Модель босса zone из мешей Blender на месте home (лицо модели — +Z). Части — по точке вращения (меш не центрирован).
function BossMeshPreview.Build(zone: number, home: CFrame, parent: Instance?): Model
	local rig = RIGS[zone]
	local name = "__BossMeshPreview" .. zone
	local old = workspace:FindFirstChild(name)
	if old then
		old:Destroy()
	end
	local model = Instance.new("Model")
	model.Name = name
	model:SetAttribute("Home", home)
	for _, partName in rig.Order do
		local part = meshPart(zone, fixture(zone, partName))
		part.CFrame = home * CFrame.new(rig.Parts[partName].pivot)
		part.Parent = model
		task.wait()
	end
	model.Parent = parent or workspace
	return model
end

-- Поставить модель в позу состояния (input — как у BossAnim.Sample). Возвращает мировые CFrame точек вращения.
function BossMeshPreview.Pose(model: Model, zone: number, input: any): { [string]: CFrame }
	local rig = RIGS[zone]
	local home = model:GetAttribute("Home") :: CFrame
	local pose = BossAnim.Sample(rig, input)
	local joints = {}
	for _, partName in rig.Order do
		local info = rig.Parts[partName]
		local transform = pose[partName] or CFrame.identity
		if info.parent then
			joints[partName] = joints[info.parent] * CFrame.new(info.pivot - rig.Parts[info.parent].pivot) * transform
		else
			joints[partName] = home * CFrame.new(info.pivot) * transform
		end
		local part = model:FindFirstChild(partName) :: BasePart?
		if part then
			part.CFrame = joints[partName]
		end
	end
	return joints
end

return BossMeshPreview

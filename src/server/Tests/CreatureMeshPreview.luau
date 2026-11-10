-- Предпросмотр мешей D54 существ босса 3 в Studio без загрузки в Roblox (D55, только Studio, в Edit через MCP):
-- данные Tests/MeshFixture/<id> (scripts/creature_mesh_fixture.py, в репозиторий не идут) → EditableMesh каждой
-- части (вершины от центра габарита, повёрнуты как кладёт импорт) + карта цвета 128² (EditableImage) → MeshPart.
-- Templates(id) отдаёт меши частей для ItemFactory.SetCreatureMeshes — существо собирается тем же кодом, что после
-- импорта. Pose — поставить суставы в позу CreatureAnim (в Edit физика не считает Transform моторов).
-- Зависит от AssetService, Config/CreatureRigs, Shared/CreatureAnim.

local AssetService = game:GetService("AssetService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CreatureAnim = require(ReplicatedStorage.Shared.CreatureAnim)
local CreatureRigs = require(ReplicatedStorage.Shared.Config.CreatureRigs)

local CreatureMeshPreview = {}

local ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
local LOOKUP: { [number]: number } = {}
for i = 1, 64 do
	LOOKUP[string.byte(ALPHABET, i)] = i - 1
end
local POS = 10000 -- позиции в int16 (scripts/creature_mesh_fixture.py)
local VERTEX = 13 -- байт на вершину

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

-- Есть ли данные предпросмотра для существа.
function CreatureMeshPreview.Has(itemId: string): boolean
	local fixture = script.Parent:FindFirstChild("MeshFixture")
	return fixture ~= nil and fixture:FindFirstChild(itemId) ~= nil
end

-- Меши частей существа из данных предпросмотра; nil — данных нет.
function CreatureMeshPreview.Templates(itemId: string): { [string]: MeshPart }?
	local fixture = script.Parent:FindFirstChild("MeshFixture")
	local module = fixture and fixture:FindFirstChild(itemId)
	if not module then
		return nil
	end
	local data = (require :: any)(module)
	local image: EditableImage? = nil
	if data.tex then
		local n = data.texSize
		local rgb = decode(data.tex)
		local rgba = buffer.create(n * n * 4)
		for i = 0, n * n - 1 do
			buffer.writeu8(rgba, i * 4, buffer.readu8(rgb, i * 3))
			buffer.writeu8(rgba, i * 4 + 1, buffer.readu8(rgb, i * 3 + 1))
			buffer.writeu8(rgba, i * 4 + 2, buffer.readu8(rgb, i * 3 + 2))
			buffer.writeu8(rgba, i * 4 + 3, 255)
		end
		image = AssetService:CreateEditableImage({ Size = Vector2.new(n, n) })
		image:WritePixelsBuffer(Vector2.zero, Vector2.new(n, n), rgba)
	end
	local out = {}
	for name, p in data.parts do
		local mesh = AssetService:CreateEditableMesh()
		local vb, tb = decode(p.v), decode(p.t)
		local verts, normals, uvs = table.create(p.nv), table.create(p.nv), table.create(p.nv)
		for i = 0, p.nv - 1 do
			local o = i * VERTEX
			local at = Vector3.new(buffer.readi16(vb, o), buffer.readi16(vb, o + 2), buffer.readi16(vb, o + 4)) / POS
			local normal = Vector3.new(buffer.readi8(vb, o + 6), buffer.readi8(vb, o + 7), buffer.readi8(vb, o + 8))
			verts[i + 1] = mesh:AddVertex(at)
			normals[i + 1] = mesh:AddNormal(if normal.Magnitude > 0 then normal.Unit else Vector3.yAxis)
			uvs[i + 1] = mesh:AddUV(Vector2.new(buffer.readu16(vb, o + 9), buffer.readu16(vb, o + 11)) / 65535)
		end
		for t = 0, p.nt - 1 do
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
		part.Name = name
		part.Material = Enum.Material.SmoothPlastic
		if image then
			part.TextureContent = Content.fromObject(image)
		end
		out[name] = part
	end
	return out
end

-- Поставить суставы существа (копия для показа — корень root из ItemFactory.Create) в позу CreatureAnim: в Edit
-- Transform моторов не применяется — суставы выключаются, детали ставятся по цепочке C0 · Transform · C1⁻¹ от корня.
function CreatureMeshPreview.Pose(root: BasePart, seed: number, t: number, mode: string)
	local rig = CreatureRigs[root:GetAttribute("ItemId") :: string]
	local out = {}
	CreatureAnim.Transforms(rig, seed, t, mode, false, 0, out, nil)
	local motors: { [string]: Motor6D } = {}
	local welds: { [BasePart]: { Weld } } = {}
	for _, d in root:GetDescendants() do
		if d:IsA("Motor6D") then
			motors[d.Name] = d
			d.Enabled = false
		elseif d:IsA("Weld") and d.Part0 then
			welds[d.Part0] = welds[d.Part0] or {}
			table.insert(welds[d.Part0], d)
			d.Enabled = false
		end
	end
	for _, name in rig.Order do
		local motor = motors[name]
		if motor and motor.Part0 and motor.Part1 then
			local cf = motor.Part0.CFrame * motor.C0 * (out[name] or CFrame.identity) * motor.C1:Inverse()
			motor.Part1.CFrame = cf
			for _, w in welds[motor.Part1] or {} do
				(w.Part1 :: BasePart).CFrame = cf * w.C0 * w.C1:Inverse()
			end
		end
	end
end

return CreatureMeshPreview

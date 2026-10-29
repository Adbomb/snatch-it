-- Собирает модели из Blender (World/MeshModels): меши загружаются один раз при старте (AssetService), дальше
-- модель — клоны шаблонов, расставленные по данным. Импорт FBX повернул данные мешей на 180° вокруг вертикали
-- (BUGS.md), поэтому каждая деталь стоит в своём центре и повёрнута на π. Цвет — из данных роли, роли участка
-- (Accent, AccentDark, DecorAccent) красятся цветом участка. Стекло — Glass с прозрачностью, неон — Neon без тени.
-- Детали без столкновений и без запросов (не мешают подсказкам): стены, где нужны, ставит владелец модели.
-- Зависит от AssetService, GameConfig, World/MeshModels.

local AssetService = game:GetService("AssetService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local MeshModels = require(ServerScriptService.Server.World.MeshModels)

local FLIP = CFrame.Angles(0, math.pi, 0)

local templates: { [string]: MeshPart } = {}
local loaded = false

local MeshBuilder = {}

-- Загружает все меши из MeshModels параллельно и ждёт конца. Меш, который не загрузился, пропускается с
-- предупреждением — модель соберётся без этой детали. Повторный вызов ничего не делает.
function MeshBuilder.Preload()
	if loaded then
		return
	end
	loaded = true
	local ids: { [string]: boolean } = {}
	for _, model in MeshModels do
		for _, part in model.parts do
			ids[part.mesh] = true
		end
	end
	local pending = 0
	for id in ids do
		pending += 1
		task.spawn(function()
			local ok, result = pcall(function()
				return AssetService:CreateMeshPartAsync(Content.fromUri(id))
			end)
			if ok and result then
				templates[id] = result :: MeshPart
			else
				warn(("[MeshBuilder] Меш %s не загрузился: %s"):format(id, tostring(result)))
			end
			pending -= 1
		end)
	end
	while pending > 0 do
		task.wait()
	end
end

function MeshBuilder.Get(name: string): MeshModels.MeshModel?
	return MeshModels[name]
end

local function roleColor(code: string, accent: Color3): Color3
	if code == "Accent" or code == "DecorAccent" then
		return accent
	elseif code == "AccentDark" then
		return accent:Lerp(Color3.new(0, 0, 0), GameConfig.Models.AccentDarken)
	end
	return Color3.fromHex(code)
end

export type BuildOptions = {
	accent: Color3?, -- цвет участка для ролей Accent / AccentDark / DecorAccent
	decor: boolean?, -- показывать детали декора (чётные уровни музея)
	name: string?,
}

-- Модель name в точке cframe (начало модели — центр у пола, лицо в -z). nil — такой модели нет.
function MeshBuilder.Build(name: string, cframe: CFrame, parent: Instance, options: BuildOptions?): Model?
	local data = MeshModels[name]
	if not data then
		warn("[MeshBuilder] Нет модели " .. name)
		return nil
	end
	MeshBuilder.Preload() -- в игре уже загружено в Main; в предпросмотре (свежие копии модулей) — здесь
	local opts = options or {}
	local accent = opts.accent or Color3.fromHex(GameConfig.Models.DefaultAccent)
	local model = Instance.new("Model")
	model.Name = opts.name or name
	local first: MeshPart? = nil
	for _, part in data.parts do
		local template = templates[part.mesh]
		if not template or (part.decor and not opts.decor) then
			continue
		end
		local mesh = template:Clone()
		mesh.Name = part.role
		mesh.Size = part.size
		mesh.CFrame = cframe * CFrame.new(part.center) * FLIP
		mesh.Color = roleColor(part.color, accent)
		mesh.Material = (Enum.Material :: any)[part.material]
		mesh.Transparency = if part.material == "Glass" then GameConfig.Models.GlassTransparency else 0
		mesh.CastShadow = part.material ~= "Neon"
		mesh.Anchored = true
		mesh.CanCollide = false
		mesh.CanQuery = false
		mesh.CanTouch = false
		mesh.Parent = model
		first = first or mesh
	end
	if data.lights and first then
		for i, light in data.lights do
			local attachment = Instance.new("Attachment")
			attachment.Name = "Light_" .. i
			attachment.Parent = first
			attachment.WorldPosition = cframe:PointToWorldSpace(light.position)
			local point = Instance.new("PointLight")
			point.Color = Color3.fromHex(light.color)
			point.Range = light.range
			point.Brightness = light.brightness
			point.Shadows = false
			point.Parent = attachment
		end
	end
	model.WorldPivot = cframe
	model.Parent = parent
	return model
end

return MeshBuilder

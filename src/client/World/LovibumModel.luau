-- Модель Ловибума на клиенте (D55): превью в магазине и инвентаре (ViewportFrame), в руке, в полёте и при поимке.
-- Пока меши не импортированы (импорт и загрузка запрещены владельцем) — Part-версия из Config/LovibumRigs: детали
-- закреплены (Anchored), без столкновений и запросов; положение и раскрытие когтей ставит Place одним BulkMoveTo
-- (в ViewportFrame — CFrame по одной: там BulkMoveTo не нужен, суставов нет). Ядро — Neon (решение владельца
-- 2026-11-08); кристалл — стекло (этап C.2, решение владельца 2026-11-15): прозрачная оболочка той же формы цвета
-- кристалла, внутри — светящееся Neon-сердце меньшего размера (видно сквозь стекло; в превью магазина и инвентаря,
-- где Neon не светится, кристалл читается как самоцвет в стекле, а не как голубой пластик). Когти, основа и металл —
-- без изменений. Свет ядра — один PointLight и только по запросу (SetLight: полёт и поимка), на слабых телефонах не
-- включается без нужды.
-- Зависит от Config/LovibumRigs.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config")
local LovibumRigs = require(Config:WaitForChild("LovibumRigs"))

local LovibumModel = {}

-- offset — от точки вращения части; size — размер при масштабе 1; base — своя прозрачность (у стекла не 0)
type PartInfo = { part: BasePart, group: string, offset: CFrame, size: Vector3, base: number }
type Built = {
	kind: string,
	parts: { PartInfo },
	pivots: { [string]: Vector3 },
	axes: { [string]: Vector3 },
	lift: number,
	light: PointLight?,
}

local built: { [Model]: Built } = setmetatable({}, { __mode = "k" }) :: any

LovibumModel.Kinds = LovibumRigs.Order

-- Стекло кристалла: материал, прозрачность, отражение, доля белого в цвете оболочки; размер Neon-сердца от кристалла.
-- SmoothPlastic, а не Glass: на кристалле размером меньше стада материал Glass почти не виден (снимки Studio, C.2),
-- полупрозрачный гладкий пластик с отражением даёт грани и блики, сердце видно сквозь него.
local GLASS = { material = Enum.Material.SmoothPlastic, transparency = 0.5, reflectance = 0.25, tint = 0.45 }
local HEART_SCALE = 0.55

-- Габариты закрытого Ловибума вида kind (Size, Center — от низа).
function LovibumModel.Bounds(kind: string): (Vector3, Vector3)
	local rig = LovibumRigs.Types[kind]
	return rig.Size, rig.Center
end

-- Новая модель (не в мире). Начало координат — низ по центру, лицо в +Z.
function LovibumModel.Build(kind: string): Model
	local rig = LovibumRigs.Types[kind]
	assert(rig, "Нет Ловибума " .. tostring(kind))
	local model = Instance.new("Model")
	model.Name = "Lovibum_" .. kind
	model:SetAttribute("LovibumKind", kind)
	local info: Built = { kind = kind, parts = {}, pivots = {}, axes = {}, lift = rig.CrystalLift, light = nil }
	for name, group in rig.Groups do
		info.pivots[name] = group.pivot
		if group.axis then
			info.axes[name] = group.axis
		end
	end
	-- центр кристалла — середина его деталей: от него сердце меньше в HEART_SCALE
	local sum, n = Vector3.zero, 0
	for _, spec in rig.Parts do
		if spec.g == "Crystal" then
			sum += spec.cf.Position
			n += 1
		end
	end
	local center = if n > 0 then sum / n else Vector3.zero
	local function add(name: string, spec: any, size: Vector3, cf: CFrame, color: Color3, material: Enum.Material)
		local part = Instance.new("Part")
		part.Name = name
		if spec.shape ~= "Block" then
			part.Shape = (Enum.PartType :: any)[spec.shape]
		end
		part.Size = size
		part.Color = color
		part.Material = material
		part.Anchored = true
		part.CanCollide = false
		part.CanQuery = false
		part.CanTouch = false
		part.CastShadow = false
		part.Massless = true
		part.CFrame = cf
		part.Parent = model
		local pivot = info.pivots[spec.g] or Vector3.zero
		table.insert(
			info.parts,
			{ part = part, group = spec.g, offset = CFrame.new(-pivot) * cf, size = size, base = 0 }
		)
		return part
	end
	for i, spec in rig.Parts do
		local color = Color3.fromHex(spec.color)
		if spec.g == "Crystal" then
			local glass = add(
				spec.g .. "_" .. i,
				spec,
				spec.size,
				spec.cf,
				color:Lerp(Color3.new(1, 1, 1), GLASS.tint),
				GLASS.material
			)
			glass.Transparency = GLASS.transparency
			glass.Reflectance = GLASS.reflectance
			info.parts[#info.parts].base = GLASS.transparency
			local at = center + (spec.cf.Position - center) * HEART_SCALE
			add("Heart_" .. i, spec, spec.size * HEART_SCALE, spec.cf.Rotation + at, color, Enum.Material.Neon)
		else
			add(
				spec.g .. "_" .. i,
				spec,
				spec.size,
				spec.cf,
				color,
				if spec.neon then Enum.Material.Neon else Enum.Material.Plastic
			)
		end
	end
	built[model] = info
	return model
end

-- Поставить модель: низ в cf, когти раскрыты на долю open (0…1, кристалл поднимается), масштаб scale (по умолчанию 1:
-- размер меняется у деталей только при смене масштаба). inViewport — по одной детали (в ViewportFrame).
function LovibumModel.Place(model: Model, cf: CFrame, open: number?, scale: number?, inViewport: boolean?)
	local info = built[model]
	if not info then
		return
	end
	local s = scale or 1
	if model:GetAttribute("Scale") ~= s then
		model:SetAttribute("Scale", s)
		for _, entry in info.parts do
			entry.part.Size = entry.size * s
		end
	end
	local f = math.clamp(open or 0, 0, 1)
	local angle = math.rad(LovibumRigs.OpenDeg) * f
	local frames: { [string]: CFrame } = {}
	for name, pivot in info.pivots do
		local axis = info.axes[name]
		local local_ = CFrame.new(pivot * s)
		if axis then
			local_ *= CFrame.fromAxisAngle(axis, angle)
		elseif name == "Crystal" then
			local_ += Vector3.new(0, info.lift * f * s, 0)
		end
		frames[name] = cf * local_
	end
	if inViewport or not model:IsDescendantOf(workspace) then
		for _, entry in info.parts do
			local o = entry.offset
			entry.part.CFrame = frames[entry.group] * (if s == 1 then o else o.Rotation + o.Position * s)
		end
		return
	end
	local parts, cframes = table.create(#info.parts), table.create(#info.parts)
	for i, entry in info.parts do
		local o = entry.offset
		parts[i] = entry.part
		cframes[i] = frames[entry.group] * (if s == 1 then o else o.Rotation + o.Position * s)
	end
	workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
end

-- Свет ядра (цвет свечения вида): только когда нужен (полёт, сеть, захват); range — радиус, 0 — выключить.
function LovibumModel.SetLight(model: Model, range: number, brightness: number?)
	local info = built[model]
	if not info then
		return
	end
	if range <= 0 then
		if info.light then
			info.light.Enabled = false
		end
		return
	end
	if not info.light then
		local host = nil
		for _, entry in info.parts do
			if entry.group == "Core" or (entry.group == "Crystal" and not host) then
				host = entry.part
				if entry.group == "Core" then
					break
				end
			end
		end
		if not host then
			return
		end
		local light = Instance.new("PointLight")
		light.Name = "CoreLight"
		light.Color = Color3.fromHex(LovibumRigs.Types[info.kind].Glow)
		light.Shadows = false
		light.Parent = host
		info.light = light
	end
	local light = info.light :: PointLight
	light.Range = range
	light.Brightness = brightness or 1.5
	light.Enabled = true
end

-- Прозрачность всех деталей (появление и исчезновение): у стекла — поверх своей.
function LovibumModel.SetTransparency(model: Model, value: number)
	local info = built[model]
	if info then
		for _, entry in info.parts do
			entry.part.Transparency = 1 - (1 - entry.base) * (1 - value)
		end
	end
end

return LovibumModel

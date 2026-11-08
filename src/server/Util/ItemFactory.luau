-- Создаёт видимый предмет с подписью над ним (BillboardGui, D45): название цветом редкости и строка «Редкость ·
-- +доход/сек», ширина — по длине названия (UITokens.ItemLabel); раскладку на экране делает клиент
-- (ItemLabelController).
-- Корень предмета — всегда один Part: с ним работают реестр, перенос, витрины и сохранение.
-- Если для предмета загружен меш (Config/ItemModels), корень — невидимый хитбокс по габаритам модели, а модель из
-- Blender («Visual», MeshPart с SurfaceAppearance D39) приварена к нему внутри. Иначе корень — сам цветной Part
-- нужной формы (заготовка до импорта). Карты SurfaceAppearance игровой скрипт задать не может (права плагина) —
-- копируется шаблон из Server/Looks (его создаёт Rojo, scripts/make_looks.py). Только внешний вид, без логики.
-- Живое существо из частей (D55, Config/CreatureRigs — босс 3): корень — невидимый хитбокс, каждая видимая часть —
-- блоки Part-версии; первый блок части — её сустав: Motor6D (имя = имя части) от блока родителя (или от корня),
-- остальные блоки приварены к нему. Скрытые части (подставка D54) блоков не имеют — их дети крепятся к ближайшему
-- видимому предку. Лицо — вперёд (−Z). Оживляет клиент (Transform моторов, Controllers/CreatureController).
-- Зависит от AssetService, Config/Items, Config/ItemModels, Config/CreatureRigs, Config/Rarities, Config/UITokens,
-- Shared/NumberFormat, Server/Looks.

local AssetService = game:GetService("AssetService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local CreatureRigs = require(ReplicatedStorage.Shared.Config.CreatureRigs)
local ItemModels = require(ReplicatedStorage.Shared.Config.ItemModels)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local NumberFormat = require(ReplicatedStorage.Shared.NumberFormat)
local Rarities = require(ReplicatedStorage.Shared.Config.Rarities)
local UITokens = require(ReplicatedStorage.Shared.Config.UITokens)
local Looks = ServerScriptService.Server.Looks

local VISUAL_NAME = "Visual"
local BLOCK_NAME = "Blk" -- блок Part-версии существа (D55)
local FACE = CFrame.Angles(0, math.pi, 0) -- скелет D54 смотрит в +Z, предметы — вперёд (−Z)

local templates: { [string]: MeshPart } = {}

local ItemFactory = {}

-- Меш предмета с картами D39 по описанию из ItemModels (ждёт сеть). nil — меша нет или он не загрузился.
local function loadModel(itemId: string): MeshPart?
	local model = ItemModels.Models[itemId]
	if not model or not model.mesh then
		return nil
	end
	local ok, result = pcall(function()
		return AssetService:CreateMeshPartAsync(Content.fromUri(model.mesh :: string))
	end)
	if not ok or not result then
		warn(("[ItemFactory] Меш %s не загрузился: %s"):format(itemId, tostring(result)))
		return nil
	end
	local mesh = result :: MeshPart
	mesh.Name = VISUAL_NAME
	mesh.Size = model.size
	mesh.Material = Enum.Material.SmoothPlastic -- цвет, кольца и тени — в SurfaceAppearance
	mesh.Anchored = false
	mesh.Massless = true
	mesh.CanCollide = false
	mesh.CanQuery = false
	mesh.CanTouch = false
	local look = Looks:FindFirstChild(itemId)
	if look then
		look:Clone().Parent = mesh
	else
		warn(("[ItemFactory] Нет шаблона карт Looks/%s (scripts/make_looks.py)"):format(itemId))
	end
	mesh:SetAttribute("Turn", model.turn or 0)
	return mesh
end

-- Загружает меши всех предметов один раз при старте (параллельно, ждёт сеть), чтобы Create дальше работал без
-- задержек. Ошибка загрузки — предмет останется заготовкой.
function ItemFactory.Preload()
	local pending = 0
	for itemId in ItemModels.Models do
		pending += 1
		task.spawn(function()
			templates[itemId] = loadModel(itemId)
			pending -= 1
		end)
	end
	while pending > 0 do
		task.wait()
	end
end

-- Есть ли у предмета загруженная модель (для тестов и проверок).
function ItemFactory.HasModel(itemId: string): boolean
	return templates[itemId] ~= nil
end

-- Строка подписи: размер текста в пределах limits (мин., макс.), белая обводка цвета Ink.
local function labelText(name: string, size: UDim2, position: UDim2, limits: Vector2, parent: Instance): TextLabel
	local label = Instance.new("TextLabel")
	label.Name = name
	label.Size = size
	label.Position = position
	label.BackgroundTransparency = 1
	label.TextScaled = true
	label.FontFace = UITokens.BodyFont()
	label.Parent = parent
	local constraint = Instance.new("UITextSizeConstraint")
	constraint.MinTextSize = limits.X
	constraint.MaxTextSize = limits.Y
	constraint.Parent = label
	local stroke = Instance.new("UIStroke")
	stroke.Color = UITokens.Colors.Ink
	stroke.Thickness = UITokens.Stroke.Text
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
	stroke.Parent = label
	return label
end

-- Подпись над предметом: название (Name) и «Редкость · +доход/сек» (Info). Атрибуты BaseWidth, BaseHeight и BaseLift —
-- исходные размер и подъём: от них клиент считает масштаб под экран и подъём над соседними подписями.
local function addLabel(part: BasePart, def: Items.ItemDef)
	local cfg = UITokens.ItemLabel
	local width = math.clamp((utf8.len(def.displayName) or 0) * cfg.CharWidth + cfg.Padding, cfg.MinWidth, cfg.MaxWidth)
	local lift = part.Size.Y / 2 + cfg.Gap
	local billboard = Instance.new("BillboardGui")
	billboard.Name = "Label"
	billboard.Size = UDim2.fromOffset(width, cfg.Height)
	billboard.StudsOffset = Vector3.new(0, lift, 0)
	billboard.MaxDistance = cfg.MaxDistance
	billboard:SetAttribute("BaseWidth", width)
	billboard:SetAttribute("BaseHeight", cfg.Height)
	billboard:SetAttribute("BaseLift", lift)
	billboard.Parent = part

	local color = UITokens.RarityColor(def.rarity)
	local name = labelText("Name", UDim2.fromScale(1, cfg.NameShare), UDim2.new(), cfg.NameTextSize, billboard)
	name.TextColor3 = color
	name.Text = def.displayName
	if def.rarity == "Secret" then
		-- У Secret цвет — градиент: текст белый, цвет даёт UIGradient.
		name.TextColor3 = UITokens.Colors.TextOnColor
		local gradient = Instance.new("UIGradient")
		gradient.Color = UITokens.ToColorSequence(UITokens.Rarity.Secret)
		gradient.Parent = name
	end

	local share = cfg.NameShare
	local infoSize, infoPosition = UDim2.fromScale(1, 1 - share), UDim2.fromScale(0, share)
	local info = labelText("Info", infoSize, infoPosition, cfg.InfoTextSize, billboard)
	info.TextColor3 = UITokens.Colors.TextOnColor
	info.RichText = true
	local rarity = ('<font color="#%s">%s</font>'):format(color:ToHex(), Rarities.Names[def.rarity] or def.rarity)
	local income = def.income or 0
	info.Text = if income > 0
		then ('%s · <font color="#%s">+%s/сек</font>'):format(rarity, cfg.Income:ToHex(), NumberFormat.Short(income))
		else rarity
end

local function block(size: Vector3, color: string): Part
	local b = Instance.new("Part")
	b.Name = BLOCK_NAME
	b.Size = size
	b.Color = Color3.fromHex(color)
	b.Material = Enum.Material.Plastic
	b.TopSurface = Enum.SurfaceType.Smooth
	b.BottomSurface = Enum.SurfaceType.Smooth
	b.Anchored = false
	b.Massless = true
	b.CanCollide = false
	b.CanQuery = false
	b.CanTouch = false
	return b
end

-- Существо из частей (D55) внутри корня root. Возвращает число блоков.
local function buildCreature(root: Part, rig: any): number
	-- низ живого существа — на низ корня, середина — по центру, лицо вперёд
	local origin = FACE * CFrame.new(-rig.Center.X, -root.Size.Y / 2 - rig.Lift, -rig.Center.Z)
	local frames: { [string]: CFrame } = {} -- точка вращения части в осях корня (покой)
	local joints: { [string]: { part: BasePart, offset: Vector3 } } = {} -- сустав: первый блок и его центр от pivot
	local count = 0
	-- ближайший предок с блоками (у скрытой подставки их нет); nil — крепить к корню
	local function visibleAncestor(name: string?): string?
		while name and not joints[name] do
			name = rig.Parts[name].parent
		end
		return name
	end
	for _, name in rig.Order do
		local spec = rig.Parts[name]
		frames[name] = origin * CFrame.new(spec.pivot)
		if #spec.blocks == 0 then
			continue
		end
		local first = spec.blocks[1]
		local joint = block(first[2], first[3])
		joint.Name = name
		joint.CFrame = root.CFrame * frames[name] * CFrame.new(first[1])
		local motor = Instance.new("Motor6D")
		motor.Name = name
		motor.Part1 = joint
		local ancestor = visibleAncestor(spec.parent)
		if ancestor then
			-- C0: точка вращения части в осях блока-сустава предка (его покой — pivot предка + центр блока)
			local j = joints[ancestor]
			motor.Part0 = j.part
			motor.C0 = (frames[ancestor] * CFrame.new(j.offset)):Inverse() * frames[name]
		else
			motor.Part0 = root
			motor.C0 = frames[name]
		end
		motor.C1 = CFrame.new(-first[1]) -- от точки вращения к центру блока
		motor.Parent = joint
		joint.Parent = root
		joints[name] = { part = joint, offset = first[1] }
		count += 1
		for i = 2, #spec.blocks do
			local entry = spec.blocks[i]
			local b = block(entry[2], entry[3])
			b.CFrame = joint.CFrame * CFrame.new(entry[1] - first[1])
			local weld = Instance.new("Weld")
			weld.Part0 = joint
			weld.Part1 = b
			weld.C0 = CFrame.new(entry[1] - first[1])
			weld.Parent = b
			b.Parent = root
			count += 1
		end
	end
	root:SetAttribute("Creature", true)
	return count
end

function ItemFactory.Create(itemId: string): Part
	local def = Items[itemId]
	assert(def, "Нет предмета в Config/Items: " .. tostring(itemId))
	local template = templates[itemId]

	local part = Instance.new("Part")
	part.Name = itemId
	part.Anchored = true
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part:SetAttribute("ItemId", itemId)
	local rig = CreatureRigs[itemId]
	if template then
		-- Невидимый хитбокс по размеру модели, модель приварена к нему.
		part.Size = template.Size
		part.Transparency = 1
		part.CastShadow = false
		local visual = template:Clone()
		local turn = CFrame.Angles(0, math.rad(template:GetAttribute("Turn") or 0), 0)
		visual.CFrame = part.CFrame * turn
		visual.Parent = part
		-- Weld (не WeldConstraint): жёстко держит модель в центре корня, даже когда закреплённый
		-- корень переставляют через CFrame (WeldConstraint в этом случае модель не тянул).
		local weld = Instance.new("Weld")
		weld.Part0 = part
		weld.Part1 = visual
		weld.C0 = turn
		weld.C1 = CFrame.identity
		weld.Parent = visual
	elseif rig then
		-- Живое существо из частей (D55): невидимый хитбокс по габаритам существа, блоки частей на суставах.
		part.Size = def.size
		part.Transparency = 1
		part.CastShadow = false
		buildCreature(part, rig)
	else
		part.Shape = (Enum.PartType :: any)[def.shape] or Enum.PartType.Block
		part.Size = def.size
		part.Color = def.color
		part.Material = def.material or Enum.Material.Plastic
	end
	addLabel(part, def)
	return part
end

-- Прозрачность видимой части предмета (мигание D10): у модели — меш, у существа — его блоки, у простого Part — сам Part.
function ItemFactory.SetVisualTransparency(part: BasePart, transparency: number)
	local visual = part:FindFirstChild(VISUAL_NAME)
	if visual and visual:IsA("BasePart") then
		visual.Transparency = transparency
	elseif part:GetAttribute("Creature") then
		for _, child in part:GetChildren() do
			if child:IsA("BasePart") then
				child.Transparency = transparency
			end
		end
	else
		part.Transparency = transparency
	end
end

return ItemFactory

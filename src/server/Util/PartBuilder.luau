-- Строит участки-музеи D48-C: постоянные части с механикой и здание по уровню (World/MuseumVisual, D48). Постоянные:
-- невидимая точка участка Floor (круглое фото владельца OwnerTag, D41, и свет зала и галерей), 20 мест Showcase_n
-- (тумба 5 × 3 × 5 — она же столкновение постамента; табличка World/Plaque — «СВОБОДНО» с голограммой, название и
-- доход экспоната или «откроется на ур. N», D50; верх-индикатор состояния, точка лампы Lamp с прожектором презентации
-- и подсветкой ниши), сундук Chest, поле качалки и табличка «Улучшение» (D34, D36).
-- SetLevel меняет здание и решает, какие места стоят (постамент есть на этом уровне) и какие открыты
-- (GameConfig.Museum.SlotsByLevel): места без постамента убраны из мира, закрытые — табличка уровня и серый верх.
-- Только геометрия, без логики. Карту строит World/WorldBuilder.
-- Зависит от GameConfig, Config/MuseumLayout, Config/Textures, World/MapLayout, World/ModelBuilder, World/MuseumVisual,
-- World/Models/MuseumD48, World/Models/Museum, World/Models/Gym, World/Palette, World/Plaque.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local MuseumLayout = require(ReplicatedStorage.Shared.Config.MuseumLayout)
local Textures = require(ReplicatedStorage.Shared.Config.Textures)
local MapLayout = require(ServerScriptService.Server.World.MapLayout)
local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local MuseumVisual = require(ServerScriptService.Server.World.MuseumVisual)
local Gym = require(ServerScriptService.Server.World.Models.Gym)
local Museum = require(ServerScriptService.Server.World.Models.Museum)
local MuseumD48 = require(ServerScriptService.Server.World.Models.MuseumD48)
local Palette = require(ServerScriptService.Server.World.Palette)
local Plaque = require(ServerScriptService.Server.World.Plaque)

local PartBuilder = {}

-- Верх пола участков (выше травы и дорог, см. MapLayout.Heights).
PartBuilder.FloorTop = MapLayout.Heights.Floor

-- Над входом, перед портиком: круглое фото владельца (D41).
local OWNER_TAG = Vector3.new(0, 19.5, -25)
-- Высота ламп ниш над полом (там же прожектор презентации и подсветка занятого места).
local LAMP_Y = 9.3
-- Свободное место — бледная бирюза гладким пластиком (D50: стекло отражало зал и серело, прежний 39E1FF был
-- кислотным), занятое — золото.
local TOP = {
	size = Vector3.new(4.6, 0.06, 4.6),
	open = Color3.fromHex("9FE6F2"),
	taken = MuseumD48.Colors.gold,
}
local LOCKED = MuseumD48.Colors.steelDark
-- Свет музея слабый намеренно (D50): освещение Roblox «Realistic» накапливает отражённый свет в закрытом зале со
-- светлыми стенами — при прежних 1.1 / 1.0 / 2.2 за 10–30 с белое выбивалось в сплошной белый (пересвет); 0.2 / 0.15 /
-- 0.6 — темновато, 0.4 / 0.3 / 1.0 — проверено в Play после минуты накопления (D50).
local NICHE_LIGHT = { color = Color3.fromHex("FFE2B0"), range = 14, angle = 55, brightness = 1.0 }
-- Свет зала и галерей (на точке участка): позиция в осях участка, только для галерей — gallery.
local HALL_LIGHTS = {
	{ name = "HallLight_1", at = Vector3.new(0, 13.5, -3), range = 22, brightness = 0.4 },
	{ name = "HallLight_2", at = Vector3.new(0, 13.5, 14), range = 22, brightness = 0.4 },
	{ name = "GalleryLight_L", at = Vector3.new(-23.8, 8.5, 0), range = 18, brightness = 0.3, gallery = true },
	{ name = "GalleryLight_R", at = Vector3.new(23.8, 8.5, 0), range = 18, brightness = 0.3, gallery = true },
}

export type PlotParts = {
	model: Model,
	showcases: { [number]: BasePart },
	exhibits: Folder,
	chest: BasePart,
	floorOrigin: CFrame, -- центр участка на уровне пола, вход в -Z
	accent: Color3,
	fieldCFrame: CFrame, -- центр поля качалки на уровне двора
	signBoard: BasePart, -- табло таблички «Улучшение» (лицо — сторона -Z, к полю)
}

-- То, что нужно SetLevel (PlotService.Plot тоже подходит).
export type LevelTarget = {
	model: Model,
	showcases: { [number]: BasePart },
	chest: BasePart,
	floorOrigin: CFrame,
}

type PartProps = {
	name: string,
	size: Vector3,
	cframe: CFrame,
	color: Color3,
	parent: Instance?,
	material: Enum.Material?,
	transparency: number?,
	canCollide: boolean?,
}

function PartBuilder.MakePart(props: PartProps): Part
	local part = Instance.new("Part")
	part.Name = props.name
	part.Anchored = true
	part.Size = props.size
	part.CFrame = props.cframe
	part.Color = props.color
	part.Material = props.material or Enum.Material.Plastic
	part.Transparency = props.transparency or 0
	part.CanCollide = if props.canCollide == nil then true else props.canCollide
	if not part.CanCollide then
		part.CanQuery = false
		part.CanTouch = false
	end
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Parent = props.parent
	return part
end

function PartBuilder.CreateWorldFolder(): Folder
	local world = Instance.new("Folder")
	world.Name = "World"
	world.Parent = workspace
	return world
end

-- Экспонат на месте (папка Exhibits участка, атрибут Slot) — для таблички с названием.
local function exhibitAt(showcase: BasePart): BasePart?
	local folders = showcase.Parent and showcase.Parent.Parent
	local exhibits = folders and folders:FindFirstChild("Exhibits")
	local slot = showcase:GetAttribute("Slot")
	for _, part in if exhibits then exhibits:GetChildren() else {} do
		if part:IsA("BasePart") and part:GetAttribute("Slot") == slot then
			return part
		end
	end
	return nil
end

-- Состояние места: открыто и свободно — бирюзовый верх и голограмма, занято — золотой верх и подсветка ниши,
-- закрыто — серый верх.
local function refreshPlace(showcase: BasePart)
	local open = showcase:GetAttribute("Open") == true
	local taken = open and showcase:GetAttribute("Occupied") == true
	local top = showcase:FindFirstChild("Top") :: BasePart?
	if top then
		local free = open and not taken
		top.Color = if not open then LOCKED elseif taken then TOP.taken else TOP.open
		top.Material = if free then Enum.Material.SmoothPlastic else Enum.Material.Plastic -- свободное — гладкое
	end
	local lamp = showcase:FindFirstChild("Lamp")
	local light = lamp and lamp:FindFirstChild("NicheLight") :: SpotLight?
	if light then
		light.Enabled = taken
	end
	local exhibit = if taken then exhibitAt(showcase) else nil
	Plaque.Write(showcase, {
		kind = if not open then "locked" elseif taken then "taken" else "free",
		slot = showcase:GetAttribute("Slot"),
		itemId = exhibit and exhibit:GetAttribute("ItemId"),
		unlock = showcase:GetAttribute("UnlockLevel"),
	})
end

local function spot(name: string, parent: Instance, props: { [string]: any }): SpotLight
	local light = Instance.new("SpotLight")
	light.Name = name
	light.Face = Enum.NormalId.Bottom
	light.Shadows = false
	light.Enabled = false
	for key, value in props do
		(light :: any)[key] = value
	end
	light.Parent = parent
	return light
end

-- Тумба места place: столкновение и опора экспоната (верх — на высоте ShowcaseSize.Y), лицом в проход.
local function makeShowcase(place: MuseumLayout.Place, floorOrigin: CFrame): BasePart
	local size = GameConfig.Museum.ShowcaseSize
	local center = place.center + Vector3.new(0, size.Y / 2, 0)
	local cframe = floorOrigin * CFrame.lookAt(center, center + place.face)
	local showcase = PartBuilder.MakePart({
		name = "Showcase_" .. place.slot,
		size = size,
		cframe = cframe,
		color = MuseumD48.Colors.pil,
	})
	showcase.MaterialVariant = Textures.SquaresSoft.name
	showcase:SetAttribute("Slot", place.slot)
	showcase:SetAttribute("Occupied", false)
	showcase:SetAttribute("Open", false)
	showcase:SetAttribute("Zone", place.zone)
	showcase:SetAttribute("UnlockLevel", place.unlock)
	local top = PartBuilder.MakePart({
		name = "Top",
		size = TOP.size,
		cframe = cframe * CFrame.new(0, size.Y / 2 + TOP.size.Y / 2, 0),
		color = LOCKED,
		canCollide = false,
		parent = showcase,
	})
	top.CastShadow = false
	local lamp = Instance.new("Attachment")
	lamp.Name = "Lamp"
	lamp.Position = Vector3.new(0, LAMP_Y - size.Y / 2, 0)
	lamp.Parent = showcase
	spot("PresentationLight", lamp, {}) -- прожектор презентации: включает PresentationController у зрителей
	spot("NicheLight", lamp, {
		Color = NICHE_LIGHT.color,
		Range = NICHE_LIGHT.range,
		Angle = NICHE_LIGHT.angle,
		Brightness = NICHE_LIGHT.brightness,
	})
	showcase:GetAttributeChangedSignal("Occupied"):Connect(function()
		refreshPlace(showcase)
	end)
	return showcase
end

-- Участок index стоит по MapLayout и смотрит входом (сторона -Z) на поле. Здание уровня 1 — сразу (SetLevel).
function PartBuilder.BuildPlot(index: number, origin: CFrame, parent: Instance): PlotParts
	local top = PartBuilder.FloorTop
	local accent = Museum.Accents[(index - 1) % #Museum.Accents + 1]
	local floorOrigin = origin * CFrame.new(0, top, 0)

	local model = Instance.new("Model")
	model.Name = "Plot_" .. index
	model:SetAttribute("PlotIndex", index)
	model:SetAttribute("OwnerUserId", 0)

	-- Точка участка: невидимая, без столкновений; на ней фото владельца и свет зала и галерей.
	local floor = PartBuilder.MakePart({
		name = "Floor",
		size = Vector3.new(1, 0.2, 1),
		cframe = floorOrigin,
		color = Palette.MuseumFloor,
		transparency = 1,
		canCollide = false,
		parent = model,
	})
	model.PrimaryPart = floor
	local tag = Instance.new("Attachment")
	tag.Name = "OwnerTag"
	tag.Parent = floor
	tag.WorldPosition = (floorOrigin * CFrame.new(OWNER_TAG)).Position
	for _, spec in HALL_LIGHTS do
		local attachment = Instance.new("Attachment")
		attachment.Name = spec.name
		attachment.Parent = floor
		attachment.WorldPosition = (floorOrigin * CFrame.new(spec.at)).Position
		attachment:SetAttribute("Gallery", spec.gallery == true)
		local light = Instance.new("PointLight")
		light.Range = spec.range
		light.Brightness = spec.brightness
		light.Color = Color3.fromHex("FFE8B0")
		light.Shadows = false
		light.Parent = attachment
	end

	-- 20 мест D48-C; в мире только те, у которых на этом уровне есть постамент (SetLevel).
	local showcaseFolder = Instance.new("Folder")
	showcaseFolder.Name = "Showcases"
	showcaseFolder.Parent = model
	local showcases = {}
	for _, place in MuseumLayout.Places do
		showcases[place.slot] = makeShowcase(place, floorOrigin)
	end

	-- Сундук у входа слева (D48-C: x −9, освобождает подход к арке галереи), замок смотрит в зал.
	local chestSize = GameConfig.Museum.ChestSize
	local chest = PartBuilder.MakePart({
		name = "Chest",
		size = chestSize,
		cframe = floorOrigin * CFrame.new(MuseumLayout.Chest.Center + Vector3.new(0, chestSize.Y / 2, 0)),
		color = MuseumD48.Colors.chest,
		parent = model,
	})
	chest.MaterialVariant = Textures.SquaresSoft.name

	-- Поле качалки и табличка «Улучшение» перед музеем, спереди слева (D34, D36).
	local yard = MapLayout.PlotYard
	local yardOrigin = origin * CFrame.new(0, MapLayout.Heights.Ground, 0)
	local fieldCFrame = yardOrigin * CFrame.new(yard.field.X, 0, yard.field.Y)
	local fieldBricks = Gym.Field(GameConfig.Gym.FieldSize, Palette.Muted(accent))
	local field = ModelBuilder.Place(ModelBuilder.Build("GymField", fieldBricks), fieldCFrame, model)
	field:SetAttribute("GymField", true)
	local signCFrame = yardOrigin * CFrame.new(yard.sign.X, 0, yard.sign.Y)
	ModelBuilder.Place(ModelBuilder.Build("SignPost", Gym.SignPost()), signCFrame, model)
	local signBoard = PartBuilder.MakePart({
		name = "UpgradeBoard",
		size = Gym.SignBoard,
		cframe = signCFrame * CFrame.new(0, Gym.SignHeight, 0),
		color = Palette.SignBoard,
		material = Enum.Material.SmoothPlastic, -- табличка с текстом: без пупырышков
		parent = model,
	})

	local exhibits = Instance.new("Folder")
	exhibits.Name = "Exhibits"
	exhibits.Parent = model
	-- замена экспоната на том же месте не меняет Occupied: табличку обновляет и сам экспонат (пришёл, ушёл)
	local function refreshSlot(part: Instance)
		local showcase = showcases[part:GetAttribute("Slot")]
		if showcase then
			refreshPlace(showcase)
		end
	end
	exhibits.ChildAdded:Connect(function(part)
		task.defer(refreshSlot, part)
	end)
	exhibits.ChildRemoved:Connect(refreshSlot)

	local parts: PlotParts = {
		model = model,
		showcases = showcases,
		exhibits = exhibits,
		chest = chest,
		floorOrigin = floorOrigin,
		accent = accent,
		fieldCFrame = fieldCFrame,
		signBoard = signBoard,
	}
	PartBuilder.SetLevel(parts, 1)
	model.Parent = parent
	return parts
end

-- Места, у которых на уровне level стоит постамент (по модулям раскладки).
local function placesWithPlinth(level: number): { [number]: boolean }
	local out = {}
	for _, m in MuseumVisual.Modules(level) do
		if m.model == "D48_Plinth" then
			for _, place in MuseumLayout.Places do
				if (place.center - m.position).Magnitude < 0.01 then
					out[place.slot] = true
				end
			end
		end
	end
	return out
end

-- Здание и места музея уровня level (1–10, D48-C): прежнее здание участка заменяется.
function PartBuilder.SetLevel(plot: LevelTarget, level: number)
	local model = plot.model
	local old = model:FindFirstChild("Building")
	if old then
		old:Destroy()
	end
	MuseumVisual.Build(level, plot.floorOrigin, model)
	model:SetAttribute("MuseumLevel", level)

	local slots = GameConfig.Museum.SlotsByLevel
	local open = slots[level] or slots[1]
	local standing = placesWithPlinth(level)
	local folder = model:FindFirstChild("Showcases")
	local meshPlinth = MuseumVisual.UsesMesh("D48_Plinth")
	for slot, showcase in plot.showcases do
		local isOpen = standing[slot] == true and slot <= open
		showcase:SetAttribute("Open", isOpen)
		showcase.Transparency = if meshPlinth then 1 else 0
		showcase.Parent = if standing[slot] then folder else nil
		refreshPlace(showcase)
	end
	plot.chest.Transparency = if MuseumVisual.UsesMesh("D48_Chest") then 1 else 0

	local floor = model:FindFirstChild("Floor")
	for _, attachment in if floor then floor:GetChildren() else {} do
		if attachment:GetAttribute("Gallery") then
			local light = attachment:FindFirstChildOfClass("PointLight")
			if light then
				light.Enabled = level >= MuseumLayout.Gallery.Level
			end
		end
	end
end

return PartBuilder

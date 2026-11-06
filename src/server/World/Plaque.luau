-- Табличка и голограмма места музея (D50, по концепту D48 v2 05_place_empty / 06_place_filled): тёмная плашка на
-- лицевой грани постамента, выступает на Thick (совпадающих граней нет). Свободное место — «СВОБОДНО» бирюзовым и
-- «место N · для экспоната», над стеклом медленно вращается и плавает голограмма-куб (теги Spin и Bob — анимирует
-- клиент, Controllers/ZoneController). Занятое — название экспоната и доход «+X/сек» зелёным. Закрытое — «МЕСТО N» и
-- «откроется на ур. N» серым. Полоса сверху — цвет состояния. Плашка — часть постамента: сквозь стены не видна.
-- Только вид, без логики. Зависит от Config/Items, Shared/NumberFormat, Shared/TextCase.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Items = require(ReplicatedStorage.Shared.Config.Items)
local NumberFormat = require(ReplicatedStorage.Shared.NumberFormat)
local TextCase = require(ReplicatedStorage.Shared.TextCase)

local SIZE = Vector3.new(4.2, 1.7, 0.14) -- плашка, стадов
local THICK = 0.07 -- половина толщины: на столько центр вынесен за грань постамента
local DROP = 0.3 -- ниже середины лицевой грани
local PLATE = Color3.fromHex("1A2440")
local PIXELS_PER_STUD = 80
local HEAVY = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
local BOLD = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Bold)
local COLORS = {
	free = Color3.fromHex("6FE3F2"),
	taken = Color3.fromHex("E9B43C"),
	locked = Color3.fromHex("8A96AA"),
	text = Color3.fromHex("FFFFFF"),
	income = Color3.fromHex("5BEA72"),
	sub = Color3.fromHex("B8C3D6"),
	stroke = Color3.fromHex("0B1020"),
}
local CUBE = { size = 1.0, lift = 1.9, color = Color3.fromHex("7FE0F0"), transparency = 0.2, spin = 0.9, bob = 0.25 }

export type State = { kind: "free" | "taken" | "locked", slot: number, itemId: string?, unlock: number? }

local Plaque = {}

-- Плашка и голограмма в осях постамента размера showcaseSize (их же считает scripts/lune/check_museum_layout).
function Plaque.Parts(
	showcaseSize: Vector3
): { plate: { size: Vector3, offset: CFrame }, cube: { size: Vector3, offset: CFrame } }
	return {
		plate = { size = SIZE, offset = CFrame.new(0, -DROP, -(showcaseSize.Z / 2 + THICK)) },
		cube = {
			size = Vector3.one * CUBE.size,
			offset = CFrame.new(0, showcaseSize.Y / 2 + CUBE.lift, 0) * CFrame.Angles(math.rad(35), 0, math.rad(35)),
		},
	}
end

local function text(parent: Instance, name: string, value: string, font: Font, color: Color3, y: number, h: number)
	local label = Instance.new("TextLabel")
	label.Name = name
	label.BackgroundTransparency = 1
	label.Position = UDim2.fromScale(0.05, y)
	label.Size = UDim2.fromScale(0.9, h)
	label.FontFace = font
	label.TextScaled = true
	label.TextColor3 = color
	label.Text = value
	local stroke = Instance.new("UIStroke")
	stroke.Color = COLORS.stroke
	stroke.Thickness = 3
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
	stroke.Parent = label
	label.Parent = parent
	return label
end

-- Тексты таблички по состоянию: заголовок, его цвет, вторая строка, её цвет, цвет полосы.
local function lines(state: State): (string, Color3, string, Color3, Color3)
	if state.kind == "free" then
		return "СВОБОДНО",
			COLORS.free,
			("место %d · для экспоната"):format(state.slot),
			COLORS.sub,
			COLORS.free
	elseif state.kind == "taken" then
		local def = state.itemId and Items[state.itemId]
		local name = if def then TextCase.Upper(def.displayName) else ("МЕСТО %d"):format(state.slot)
		local income = if def then def.income or 0 else 0
		local sub = if income > 0
			then ("+%s/сек"):format(NumberFormat.Short(income))
			else ("место %d"):format(state.slot)
		return name, COLORS.text, sub, if income > 0 then COLORS.income else COLORS.sub, COLORS.taken
	end
	return ("МЕСТО %d"):format(state.slot),
		COLORS.locked,
		("откроется на ур. %d"):format(state.unlock or 1),
		COLORS.sub,
		COLORS.locked
end

-- Табличка и голограмма места: прежние убираются, новые — по состоянию.
function Plaque.Write(showcase: BasePart, state: State)
	for _, name in { "Plaque", "FreeCube" } do
		local old = showcase:FindFirstChild(name)
		if old then
			old:Destroy()
		end
	end
	local parts = Plaque.Parts(showcase.Size)
	local plate = Instance.new("Part")
	plate.Name = "Plaque"
	plate.Anchored = true
	plate.CanCollide = false
	plate.CanQuery = false
	plate.CanTouch = false
	plate.CastShadow = false
	plate.Material = Enum.Material.SmoothPlastic -- табличка с текстом: без пупырышков (D36)
	plate.Color = PLATE
	plate.Size = parts.plate.size
	plate.CFrame = showcase.CFrame * parts.plate.offset
	plate.TopSurface = Enum.SurfaceType.Smooth
	plate.BottomSurface = Enum.SurfaceType.Smooth

	local gui = Instance.new("SurfaceGui")
	gui.Name = "Text"
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = PIXELS_PER_STUD
	gui.LightInfluence = 0
	gui.Parent = plate
	local title, titleColor, sub, subColor, bar = lines(state)
	local stripe = Instance.new("Frame")
	stripe.Name = "Bar"
	stripe.BorderSizePixel = 0
	stripe.BackgroundColor3 = bar
	stripe.Size = UDim2.fromScale(1, 0.1)
	stripe.Parent = gui
	text(gui, "Title", title, HEAVY, titleColor, 0.2, 0.42)
	text(gui, "Sub", sub, BOLD, subColor, 0.64, 0.26)
	plate.Parent = showcase

	if state.kind == "free" then
		local cube = Instance.new("Part")
		cube.Name = "FreeCube"
		cube.Anchored = true
		cube.CanCollide = false
		cube.CanQuery = false
		cube.CanTouch = false
		cube.CastShadow = false
		cube.Material = Enum.Material.Glass
		cube.Color = CUBE.color
		cube.Transparency = CUBE.transparency
		cube.Size = parts.cube.size
		cube.CFrame = showcase.CFrame * parts.cube.offset
		cube:SetAttribute("SpinSpeed", CUBE.spin)
		cube:SetAttribute("BobHeight", CUBE.bob)
		CollectionService:AddTag(cube, "Spin")
		CollectionService:AddTag(cube, "Bob")
		cube.Parent = showcase
	end
end

return Plaque

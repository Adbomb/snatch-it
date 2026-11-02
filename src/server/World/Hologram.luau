-- Голографическое название уровня (D41): светящаяся надпись в воздухе над полом зоны, без таблички — невидимая
-- деталь с SurfaceGui (свечение Brightness, без влияния света), градиент цвета зоны по буквам, под ней — светящийся
-- «проектор» на полу. Лицо надписи — сторона Front детали; клиент слегка покачивает и мерцает надписью
-- (Controllers/ZoneController, тег Hologram). Зависит от Palette, Shared/TextCase.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local TextCase = require(ReplicatedStorage.Shared.TextCase)

local Palette = require(ServerScriptService.Server.World.Palette)

local PIXELS_PER_STUD = 12 -- TextScaled не крупнее 100 px: плотность такая, чтобы название влезало крупно
local FONT = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
local BOLD = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Bold)
local TAG = "Hologram"

export type Spec = {
	number: number,
	title: string,
	subtitle: string,
	accent: Color3,
	size: Vector2, -- ширина и высота надписи, стадов
}

local Hologram = {}

local function text(parent: Instance, value: string, props: { [string]: any }): TextLabel
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.TextScaled = true
	label.TextColor3 = Color3.new(1, 1, 1)
	label.Text = value
	for key, v in props do
		(label :: any)[key] = v
	end
	label.Parent = parent
	return label
end

-- Надпись в точке at (центр надписи; лицо — LookVector), проектор на полу под ней (верх пола — floorY).
function Hologram.Build(spec: Spec, at: CFrame, floorY: number, parent: Instance): Model
	local model = Instance.new("Model")
	model.Name = "Hologram"
	local glow = spec.accent:Lerp(Color3.new(1, 1, 1), 0.55)
	local dark = spec.accent:Lerp(Palette.Black, 0.6)

	local panel = Instance.new("Part")
	panel.Name = "Panel"
	panel.Anchored = true
	panel.CanCollide = false
	panel.CanQuery = false
	panel.CanTouch = false
	panel.CastShadow = false
	panel.Transparency = 1
	panel.Size = Vector3.new(spec.size.X, spec.size.Y, 0.2)
	panel.CFrame = at
	panel.Parent = model
	CollectionService:AddTag(panel, TAG)

	local gui = Instance.new("SurfaceGui")
	gui.Name = "Hologram"
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = PIXELS_PER_STUD
	gui.LightInfluence = 0
	gui.Brightness = 2.2 -- светится (свечение Bloom)
	gui.AlwaysOnTop = false
	gui.Parent = panel

	local number = text(gui, ("УРОВЕНЬ %d"):format(spec.number), {
		Name = "Number",
		FontFace = BOLD,
		Size = UDim2.fromScale(1, 0.2),
		Position = UDim2.fromScale(0, 0.02),
		TextColor3 = glow,
	})
	local stroke = Instance.new("UIStroke")
	stroke.Color = dark
	stroke.Thickness = 1.5
	stroke.Parent = number

	local title = text(gui, TextCase.Upper(spec.title), {
		Name = "Title",
		FontFace = FONT,
		Size = UDim2.fromScale(1, 0.5),
		Position = UDim2.fromScale(0, 0.2),
	})
	local shade = Instance.new("UIGradient")
	shade.Rotation = 90
	shade.Color = ColorSequence.new(Color3.new(1, 1, 1), glow)
	shade.Parent = title
	local outline = Instance.new("UIStroke")
	outline.Color = dark
	outline.Thickness = 3
	outline.Parent = title

	local subtitle = text(gui, spec.subtitle, {
		Name = "Subtitle",
		FontFace = BOLD,
		Size = UDim2.fromScale(1, 0.2),
		Position = UDim2.fromScale(0, 0.74),
	})
	local subStroke = Instance.new("UIStroke")
	subStroke.Color = dark
	subStroke.Thickness = 1.5
	subStroke.Parent = subtitle

	-- Проектор: светящаяся полоса на полу под надписью (верх на 0.32 над полом — выше плит декора, без совпадающих граней).
	local base = Instance.new("Part")
	base.Name = "Projector"
	base.Anchored = true
	base.CanCollide = false
	base.CanQuery = false
	base.CastShadow = false
	base.Material = Enum.Material.Neon
	base.Color = spec.accent
	base.Transparency = 0.15
	base.Size = Vector3.new(spec.size.X * 0.55, 0.32, 1.2)
	base.CFrame = CFrame.new(at.Position.X, floorY + 0.16, at.Position.Z) * at.Rotation
	base.Parent = model

	model.Parent = parent
	return model
end

return Hologram

-- Голографические надписи в воздухе (D41): название уровня («УРОВЕНЬ N», название, босс) и вывески магазинов — без
-- табличек: невидимая деталь с SurfaceGui (свечение Brightness, без влияния света), градиент цвета по буквам. Висят
-- высоко, над головой игрока и над боссом, не закрывают обзор. Лицо надписи — сторона Front детали (LookVector);
-- клиент слегка покачивает и мерцает надписью, ночью гасит надписи уровней (Controllers/ZoneController, тег Hologram;
-- атрибут Night = false — не гасить). Зависит от Palette, Shared/TextCase.

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
	top: string?, -- мелкая строка над названием («УРОВЕНЬ 1»); nil — нет
	title: string,
	subtitle: string?, -- строка под названием (имя босса); nil — нет
	accent: Color3,
	size: Vector2, -- ширина и высота надписи, стадов
	hideAtNight: boolean?, -- гаснуть ночью (надписи уровней: коридор закрыт)
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

local function stroke(label: TextLabel, color: Color3, thickness: number)
	local s = Instance.new("UIStroke")
	s.Color = color
	s.Thickness = thickness
	s.Parent = label
end

-- Надпись с центром в at (лицо — LookVector).
function Hologram.Build(spec: Spec, at: CFrame, parent: Instance): BasePart
	local glow = spec.accent:Lerp(Color3.new(1, 1, 1), 0.55)
	local dark = spec.accent:Lerp(Palette.Black, 0.6)

	local panel = Instance.new("Part")
	panel.Name = "Hologram"
	panel.Anchored = true
	panel.CanCollide = false
	panel.CanQuery = false
	panel.CanTouch = false
	panel.CastShadow = false
	panel.Transparency = 1
	panel.Size = Vector3.new(spec.size.X, spec.size.Y, 0.2)
	panel.CFrame = at
	panel:SetAttribute("Night", spec.hideAtNight == true)
	CollectionService:AddTag(panel, TAG)

	local gui = Instance.new("SurfaceGui")
	gui.Name = "Hologram"
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = PIXELS_PER_STUD
	gui.LightInfluence = 0
	gui.Brightness = 2.2 -- светится (свечение Bloom)
	gui.Parent = panel

	-- Доли высоты: строка сверху, название, строка снизу (что есть — то и делится).
	local topShare = if spec.top then 0.22 else 0
	local subShare = if spec.subtitle then 0.24 else 0
	local titleShare = 1 - topShare - subShare
	if spec.top then
		local top = text(gui, TextCase.Upper(spec.top), {
			Name = "Top",
			FontFace = BOLD,
			Size = UDim2.fromScale(1, topShare * 0.9),
			TextColor3 = glow,
		})
		stroke(top, dark, 1.5)
	end
	local title = text(gui, TextCase.Upper(spec.title), {
		Name = "Title",
		FontFace = FONT,
		Size = UDim2.fromScale(1, titleShare),
		Position = UDim2.fromScale(0, topShare),
	})
	local shade = Instance.new("UIGradient")
	shade.Rotation = 90
	shade.Color = ColorSequence.new(Color3.new(1, 1, 1), glow)
	shade.Parent = title
	stroke(title, dark, 3)
	if spec.subtitle then
		local subtitle = text(gui, spec.subtitle, {
			Name = "Subtitle",
			FontFace = BOLD,
			Size = UDim2.fromScale(1, subShare * 0.9),
			Position = UDim2.fromScale(0, topShare + titleShare + subShare * 0.05),
		})
		stroke(subtitle, dark, 1.5)
	end

	panel.Parent = parent
	return panel
end

return Hologram

-- Надписи на вывесках мира (SurfaceGui): шрифт, белый текст и толстая обводка Ink из UI_KIT.md.
-- Зависит от Config/UITokens.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local UITokens = require(ReplicatedStorage.Shared.Config.UITokens)

local PIXELS_PER_STUD = 50
local STROKE = 4 -- толще, чем в интерфейсе: вывеску читают издалека

export type Line = { text: string, scale: number } -- scale — доля высоты вывески

local Signs = {}

-- Пишет строки сверху вниз на грани face детали part.
function Signs.Write(part: BasePart, face: Enum.NormalId, lines: { Line })
	local gui = Instance.new("SurfaceGui")
	gui.Name = "Sign"
	gui.Face = face
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = PIXELS_PER_STUD
	gui.LightInfluence = 0
	gui.Parent = part

	local layout = Instance.new("UIListLayout")
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.VerticalAlignment = Enum.VerticalAlignment.Center
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.Parent = gui

	for order, line in lines do
		local label = Instance.new("TextLabel")
		label.BackgroundTransparency = 1
		label.Size = UDim2.fromScale(0.94, line.scale)
		label.LayoutOrder = order
		label.FontFace = UITokens.BodyFont(UITokens.Fonts.Heavy)
		label.TextScaled = true
		label.TextColor3 = UITokens.Colors.TextOnColor
		label.Text = line.text
		local stroke = Instance.new("UIStroke")
		stroke.Color = UITokens.Colors.Ink
		stroke.Thickness = STROKE
		stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
		stroke.Parent = label
		label.Parent = gui
	end
end

return Signs

-- Надписи на вывесках мира (SurfaceGui): GothamBlack (Check-UI, D20), белый текст, толстая чёрная обводка.
-- Ни от чего не зависит.

local PIXELS_PER_STUD = 50
local STROKE = 4 -- толще, чем в интерфейсе: вывеску читают издалека
local FONT = Font.fromEnum(Enum.Font.GothamBlack)
local TEXT = Color3.new(1, 1, 1)
local OUTLINE = Color3.new(0, 0, 0)

export type Line = { text: string, scale: number } -- scale — доля высоты вывески

local Signs = {}

-- Пишет строки сверху вниз на грани face детали part. Возвращает подписи (чтобы менять текст позже).
function Signs.Write(part: BasePart, face: Enum.NormalId, lines: { Line }): { TextLabel }
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

	local labels: { TextLabel } = {}
	for order, line in lines do
		local label = Instance.new("TextLabel")
		label.BackgroundTransparency = 1
		label.Size = UDim2.fromScale(0.94, line.scale)
		label.LayoutOrder = order
		label.FontFace = FONT
		label.TextScaled = true
		label.TextColor3 = TEXT
		label.Text = line.text
		local stroke = Instance.new("UIStroke")
		stroke.Color = OUTLINE
		stroke.Thickness = STROKE
		stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
		stroke.Parent = label
		label.Parent = gui
		table.insert(labels, label)
	end
	return labels
end

return Signs

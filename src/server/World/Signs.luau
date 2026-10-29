-- Надписи на вывесках мира (SurfaceGui) в стиле Stud-UI (D20): Montserrat Heavy, белый текст, толстая обводка
-- тёмного оттенка цвета вывески (или чёрная). Ни от чего не зависит.

local PIXELS_PER_STUD = 50
local STROKE = 4 -- толще, чем в интерфейсе: вывеску читают издалека
local FONT = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
local TEXT = Color3.new(1, 1, 1)
local OUTLINE = Color3.new(0, 0, 0)
local TINT_DARKEN = 0.65 -- насколько обводка темнее цвета вывески

export type Line = { text: string, scale: number } -- scale — доля высоты вывески

local Signs = {}

-- Пишет строки сверху вниз на грани face детали part. tint — цвет вывески: обводка будет его тёмным оттенком.
-- Возвращает подписи (чтобы менять текст позже).
function Signs.Write(part: BasePart, face: Enum.NormalId, lines: { Line }, tint: Color3?): { TextLabel }
	local outline = if tint then tint:Lerp(OUTLINE, TINT_DARKEN) else OUTLINE
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
		stroke.Color = outline
		stroke.Thickness = STROKE
		stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
		stroke.Parent = label
		label.Parent = gui
		table.insert(labels, label)
	end
	return labels
end

return Signs

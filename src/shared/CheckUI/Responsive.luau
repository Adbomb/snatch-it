--!strict
-- Check-UI (D20): масштаб окон под экран (§4 спецификации), только клиент.
-- Копия scripts/Responsive.lua из навыка, путь в игре: ReplicatedStorage.Shared.CheckUI.Responsive.
-- Every UIScale named "WindowScale" inside the ScreenGui follows the device scale:
--   min(viewport.X / 1050, viewport.Y / 620), clamped to [0.52, 1.18].
-- On top of that, a window never grows past the safe area of its ScreenGui (fit-to-container),
-- because one global multiplier alone does not guarantee that a big modal fits a phone.

local Responsive = {}

Responsive.Baseline = Vector2.new(1050, 620)
Responsive.Min = 0.52
Responsive.Max = 1.18
Responsive.SafeMargin = 0.94 -- share of the container a window may occupy

function Responsive.DeviceScale(viewport: Vector2): number
	if viewport.X <= 0 or viewport.Y <= 0 then
		return 1
	end
	local factor = math.min(viewport.X / Responsive.Baseline.X, viewport.Y / Responsive.Baseline.Y)
	return math.clamp(factor, Responsive.Min, Responsive.Max)
end

-- Scale for one window: device scale, reduced further if the window's base pixel size
-- would not fit into the container (ScreenGui absolute size, which respects ScreenInsets).
local function windowScale(window: GuiObject, container: Vector2, device: number): number
	local base = window.Size
	local w = base.X.Offset + base.X.Scale * container.X
	local h = base.Y.Offset + base.Y.Scale * container.Y
	if w <= 0 or h <= 0 then
		return device
	end
	local fit = math.min(container.X * Responsive.SafeMargin / w, container.Y * Responsive.SafeMargin / h)
	return math.min(device, fit)
end

-- Keeps all WindowScale objects in screenGui up to date. Returns a disconnect function.
function Responsive.Attach(screenGui: ScreenGui): () -> ()
	local camera = workspace.CurrentCamera
	local function update()
		local device = Responsive.DeviceScale(camera.ViewportSize)
		local container = screenGui.AbsoluteSize
		for _, descendant in screenGui:GetDescendants() do
			if descendant:IsA("UIScale") and descendant.Name == "WindowScale" then
				local window = descendant.Parent
				if window and window:IsA("GuiObject") then
					descendant.Scale = windowScale(window, container, device)
				end
			end
		end
	end
	local connections = {
		camera:GetPropertyChangedSignal("ViewportSize"):Connect(update),
		screenGui:GetPropertyChangedSignal("AbsoluteSize"):Connect(update),
		screenGui.DescendantAdded:Connect(function(d)
			if d:IsA("UIScale") and d.Name == "WindowScale" then
				task.defer(update)
			end
		end),
	}
	update()
	return function()
		for _, c in connections do
			c:Disconnect()
		end
	end
end

return Responsive

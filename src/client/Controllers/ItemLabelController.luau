-- Подписи над предметами (D45): раскладывает на экране BillboardGui «Label» (ItemFactory) и «IncomeLabel»
-- (IncomeService) так, чтобы подписи соседних предметов не накладывались: ближние стоят на своих местах, дальние
-- поднимаются над ними ступенькой (Shared/LabelLayout). Размер подписей — по высоте экрана (на телефоне меньше,
-- UITokens.ItemLabel.Scale). У экспоната с надписью дохода вторая строка подписи скрыта: доход уже написан над ним.
-- Только вид, без логики: свойства меняются у себя на клиенте. Включение подписей (Enabled) не трогает — им управляет
-- PresentationController. Зависит от Shared/LabelLayout, Config/UITokens.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local LabelLayout = require(Shared:WaitForChild("LabelLayout"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))

local cfg = UITokens.ItemLabel
local NAMES = { Label = true, IncomeLabel = true }

type State = { lift: number, target: number }

local ItemLabelController = {}

local tracked: { [BillboardGui]: State } = {}

-- Исходные ширина, высота (px) и подъём (стады): атрибуты сервера у Label, у IncomeLabel — запоминаем при появлении.
local function base(gui: BillboardGui): (number, number, number)
	if gui:GetAttribute("BaseWidth") == nil then
		gui:SetAttribute("BaseWidth", gui.Size.X.Offset)
		gui:SetAttribute("BaseHeight", gui.Size.Y.Offset)
		gui:SetAttribute("BaseLift", gui.StudsOffset.Y)
	end
	return gui:GetAttribute("BaseWidth"), gui:GetAttribute("BaseHeight"), gui:GetAttribute("BaseLift")
end

local function track(instance: Instance)
	if instance:IsA("BillboardGui") and NAMES[instance.Name] then
		tracked[instance] = { lift = 0, target = 0 }
	end
end

-- Вторая строка подписи не нужна, если над экспонатом уже есть надпись дохода.
local function fitInfo(gui: BillboardGui)
	if gui.Name ~= "Label" then
		return
	end
	local name, info = gui:FindFirstChild("Name"), gui:FindFirstChild("Info")
	if not (name and info and name:IsA("GuiObject") and info:IsA("GuiObject")) then
		return
	end
	local parent = gui.Parent
	local showInfo = not (parent and parent:FindFirstChild("IncomeLabel"))
	if info.Visible ~= showInfo then
		info.Visible = showInfo
		name.Size = if showInfo then UDim2.fromScale(1, cfg.NameShare) else UDim2.fromScale(1, 1)
	end
end

-- Раскладка: масштаб под экран, экранные прямоугольники подписей и подъём каждой (цель; догоняет плавно).
local function layout()
	local camera = Workspace.CurrentCamera
	if not camera then
		return
	end
	local viewport = camera.ViewportSize
	local scale = math.clamp(viewport.Y / cfg.ScreenHeight, cfg.Scale.X, cfg.Scale.Y)
	local studsPerPixel = 2 * math.tan(math.rad(camera.FieldOfView) / 2) / viewport.Y -- на глубине 1
	local entries: { LabelLayout.Entry } = {}
	local guis: { BillboardGui } = {}
	for gui, state in tracked do
		local adornee = gui.Adornee or gui.Parent
		if gui.Parent == nil or not (adornee and adornee:IsA("BasePart")) then
			continue
		end
		fitInfo(gui)
		local width, height, lift = base(gui)
		gui.Size = UDim2.fromOffset(width * scale, height * scale)
		local anchor = (adornee :: BasePart).Position + camera.CFrame.UpVector * lift
		local point, visible = camera:WorldToViewportPoint(anchor)
		if gui.Enabled and visible and point.Z > 0 and point.Z < gui.MaxDistance then
			table.insert(entries, { x = point.X, y = point.Y, w = width * scale, h = height * scale, depth = point.Z })
			table.insert(guis, gui)
		else
			state.target = 0
		end
	end
	local lifts = LabelLayout.Place(entries, cfg.StackGap * scale, cfg.MaxStack * cfg.Height * scale)
	for i, gui in guis do
		tracked[gui].target = lifts[i] * entries[i].depth * studsPerPixel
	end
end

function ItemLabelController.Init()
	for _, instance in Workspace:GetDescendants() do
		track(instance)
	end
	Workspace.DescendantAdded:Connect(track)
	Workspace.DescendantRemoving:Connect(function(instance)
		tracked[instance :: any] = nil
	end)
	local sinceLayout = 0
	RunService.RenderStepped:Connect(function(dt: number)
		sinceLayout += dt
		if sinceLayout >= cfg.Update then
			sinceLayout = 0
			layout()
		end
		local follow = math.min(1, dt * cfg.Follow)
		for gui, state in tracked do
			if math.abs(state.target - state.lift) > 1e-3 then
				state.lift += (state.target - state.lift) * follow
				gui.StudsOffset = Vector3.new(0, (gui:GetAttribute("BaseLift") or 0) + state.lift, 0)
			end
		end
	end)
end

return ItemLabelController

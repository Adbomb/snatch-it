-- Подписи над предметами (D45): раскладывает на экране BillboardGui «Label» (ItemFactory) и «IncomeLabel»
-- (IncomeService) так, чтобы подписи соседних предметов не накладывались: ближние стоят на своих местах, дальние
-- поднимаются над ними ступенькой (Shared/LabelLayout). Размер подписей — по высоте экрана (на телефоне меньше,
-- UITokens.ItemLabel.Scale). У экспоната с надписью дохода вторая строка подписи скрыта: доход уже написан над ним.
-- Визуальный QA босса 3: «Z z z» спящего босса — неподвижное препятствие (подписи поднимаются над ним); фигура босса
-- перед подписью — препятствие: подпись поднимается над её верхом, а если слишком высоко — плавно гаснет (сквозь
-- босса подписи не видны); таймер вверху и плашка зоны — запретные зоны: подпись под ними гаснет; подпись экспоната,
-- которую закрывает стена или колонна музея (MuseumCameraController.Blocked), гаснет целиком, а не обрывком.
-- Только вид, без логики: свойства меняются у себя на клиенте. Включение подписей (Enabled) не трогает — им управляет
-- PresentationController. Зависит от Shared/LabelLayout, Config/UITokens, Controllers/MuseumCameraController.

local CollectionService = game:GetService("CollectionService")
local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local LabelLayout = require(Shared:WaitForChild("LabelLayout"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local MuseumCameraController = require(script.Parent:WaitForChild("MuseumCameraController"))

local cfg = UITokens.ItemLabel
local NAMES = { Label = true, IncomeLabel = true }
local BOSS_TAG = "Boss"

-- Угасание: исходные прозрачности частей подписи (заполняется при первом угасании).
type Fade = { instance: Instance, property: string, base: number }
type State = {
	lift: number,
	target: number,
	alpha: number,
	alphaTarget: number,
	fades: { Fade }?,
	wall: boolean, -- закрыта ли стеной музея (последняя проверка)
	wallAt: number, -- когда проверяли
}

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
		tracked[instance] =
			{ lift = 0, target = 0, alpha = 1, alphaTarget = 1, fades = nil, wall = false, wallAt = -math.huge }
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

-- Части подписи, которые гаснут, и их исходные прозрачности.
local function fadesOf(gui: BillboardGui): { Fade }
	local list: { Fade } = {}
	local function add(instance: Instance, property: string)
		local value = (instance :: any)[property]
		if value < 1 then
			table.insert(list, { instance = instance, property = property, base = value })
		end
	end
	for _, d in gui:GetDescendants() do
		if d:IsA("TextLabel") or d:IsA("TextButton") then
			add(d, "TextTransparency")
			add(d, "TextStrokeTransparency")
			add(d, "BackgroundTransparency")
		elseif d:IsA("ImageLabel") then
			add(d, "ImageTransparency")
			add(d, "BackgroundTransparency")
		elseif d:IsA("Frame") then
			add(d, "BackgroundTransparency")
		elseif d:IsA("UIStroke") then
			add(d, "Transparency")
		end
	end
	return list
end

local function applyAlpha(gui: BillboardGui, state: State)
	if not state.fades then
		state.fades = fadesOf(gui)
	end
	for _, f in state.fades :: { Fade } do
		if f.instance.Parent then
			(f.instance :: any)[f.property] = 1 - (1 - f.base) * state.alpha
		end
	end
end

-- Прямоугольник на экране по коробке детали (8 углов); nil — коробка позади камеры.
local function screenBox(camera: Camera, cf: CFrame, size: Vector3): LabelLayout.Rect?
	local h = size / 2
	local x0, y0, x1, y1, depth = math.huge, math.huge, -math.huge, -math.huge, math.huge
	for _, sx in { -1, 1 } do
		for _, sy in { -1, 1 } do
			for _, sz in { -1, 1 } do
				local v = camera:WorldToViewportPoint(cf * Vector3.new(sx * h.X, sy * h.Y, sz * h.Z))
				if v.Z <= 0 then
					return nil
				end
				x0, x1 = math.min(x0, v.X), math.max(x1, v.X)
				y0, y1 = math.min(y0, v.Y), math.max(y1, v.Y)
				depth = math.min(depth, v.Z)
			end
		end
	end
	return { x0 = x0, x1 = x1, y0 = y0, y1 = y1, depth = depth }
end

-- Чужой учебный пёс или существо (TutorialOwner — другой ученик): у меня спрятаны — не препятствие.
local function foreign(instance: Instance): boolean
	local owner = instance:GetAttribute("TutorialOwner")
	return owner ~= nil and owner ~= Players.LocalPlayer.UserId
end

-- Фигуры боссов рядом с камерой: прямоугольники их частей (у Part-версии — суставы по габариту части).
local function bossRects(camera: Camera): { LabelLayout.Rect }
	local out = {}
	local eye = camera.CFrame.Position
	for _, model in CollectionService:GetTagged(BOSS_TAG) do
		if
			model:IsA("Model")
			and model.Parent
			and not foreign(model)
			and (model:GetPivot().Position - eye).Magnitude < cfg.BossRange
		then
			for _, part in model:GetChildren() do
				if part:IsA("BasePart") and part.Name ~= "Root" then
					local rect = screenBox(camera, part.CFrame, part.Size)
					if rect then
						table.insert(out, rect)
					end
				end
			end
		end
	end
	return out
end

-- «Z z z» спящих боссов (BossAnimController): неподвижные препятствия для подписей.
local function zzzEntries(camera: Camera): { LabelLayout.Entry }
	local out = {}
	for _, model in CollectionService:GetTagged(BOSS_TAG) do
		local head = model:FindFirstChild("Head")
		local gui = head and head:FindFirstChild("Zzz")
		if gui and gui:IsA("BillboardGui") and gui.Enabled and not foreign(model) then
			-- весь путь подъёма и качания: низ и верх пути
			local at = (head :: BasePart).Position
			local low, lowVisible = camera:WorldToViewportPoint(at + Vector3.new(0, cfg.ZzzRise.X, 0))
			local high, highVisible = camera:WorldToViewportPoint(at + Vector3.new(0, cfg.ZzzRise.Y, 0))
			local side = camera:WorldToViewportPoint(
				at + Vector3.new(0, cfg.ZzzRise.X, 0) + camera.CFrame.RightVector * cfg.ZzzSway
			)
			if lowVisible and highVisible and low.Z > 0 and low.Z < gui.MaxDistance then
				local sway = math.abs(side.X - low.X)
				-- глубина меньше любой подписи: ставится первой и не двигается
				table.insert(out, {
					x = low.X,
					y = (low.Y + high.Y) / 2,
					w = gui.Size.X.Offset + 2 * sway,
					h = gui.Size.Y.Offset + math.abs(low.Y - high.Y),
					depth = -1,
				})
			end
		end
	end
	return out
end

-- Запретные зоны вверху экрана: таймер с подписью и видимая плашка зоны (в координатах камеры).
local function hudZones(): { LabelLayout.Rect }
	local zones = {}
	local playerGui = Players.LocalPlayer:FindFirstChildOfClass("PlayerGui")
	if not playerGui then
		return zones
	end
	local inset = GuiService:GetGuiInset()
	local m = cfg.ZoneMargin
	for _, pair in { { "TimeHud", "Holder" }, { "LevelBanner", "LevelBanner" } } do
		local screen = playerGui:FindFirstChild(pair[1])
		local frame = screen and screen:FindFirstChild(pair[2])
		if
			screen
			and screen:IsA("ScreenGui")
			and screen.Enabled
			and frame
			and frame:IsA("GuiObject")
			and frame.Visible
		then
			local dy = if screen.IgnoreGuiInset then 0 else inset.Y
			local p, s = frame.AbsolutePosition, frame.AbsoluteSize
			if s.X > 1 and s.Y > 1 then
				table.insert(
					zones,
					{ x0 = p.X - m, x1 = p.X + s.X + m, y0 = p.Y + dy - m, y1 = p.Y + s.Y + dy + m, depth = 0 }
				)
			end
		end
	end
	return zones
end

-- Ширина текста подписи (px, не больше рамки w): поля рамки по бокам пустые — их стена может закрывать без вреда.
local function textWidth(gui: BillboardGui, w: number): number
	local widest = 0
	for _, d in gui:GetDescendants() do
		if d:IsA("TextLabel") and d.Visible then
			widest = math.max(widest, d.TextBounds.X)
		end
	end
	return if widest > 0 then math.min(widest, w) else w
end

-- Закрывает ли подпись стена или колонна музея: центр и края текста подписи на её высоте.
local function hiddenInMuseum(camera: Camera, adornee: BasePart, anchor: Vector3, halfWidth: number): boolean
	if adornee:GetAttribute("Slot") == nil then
		return false
	end
	local eye = camera.CFrame.Position
	local right = camera.CFrame.RightVector * halfWidth
	for _, point in { anchor, anchor + right, anchor - right } do
		if MuseumCameraController.Blocked(eye, point) then
			return true
		end
	end
	return false
end

-- Раскладка: масштаб под экран, экранные прямоугольники подписей, подъём каждой и угасание (цели; догоняют плавно).
local function layout()
	local camera = Workspace.CurrentCamera
	if not camera then
		return
	end
	local viewport = camera.ViewportSize
	local scale = math.clamp(viewport.Y / cfg.ScreenHeight, cfg.Scale.X, cfg.Scale.Y)
	local studsPerPixel = 2 * math.tan(math.rad(camera.FieldOfView) / 2) / viewport.Y -- на глубине 1
	local entries: { LabelLayout.Entry } = zzzEntries(camera)
	local fixed = #entries -- первые — «Z z z», их подъём не применяется
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
			state.alphaTarget = 1
		end
	end
	-- подписи друг над другом и над фигурами боссов — одним проходом: поднятые над королём не налезают друг на друга
	local lifts, hiddenByBoss = LabelLayout.Arrange(
		entries,
		cfg.StackGap * scale,
		cfg.MaxStack * cfg.Height * scale,
		bossRects(camera),
		cfg.BossGap * scale,
		cfg.BossLift * cfg.Height * scale
	)
	local zones = hudZones()
	local now = os.clock()
	local wallChecks = 0
	for k, gui in guis do
		local i = fixed + k
		local e = entries[i]
		local lift, hidden = lifts[i], hiddenByBoss[i]
		local state = tracked[gui]
		if not hidden and LabelLayout.InZone(e, lift, zones) then
			hidden = true
		end
		local adornee = (gui.Adornee or gui.Parent) :: BasePart
		if not hidden and adornee:GetAttribute("Slot") ~= nil then
			-- стены музея: проверка помнится WallEvery, за раскладку — не больше WallPerLayout (без всплесков)
			if now - state.wallAt >= cfg.WallEvery and wallChecks < cfg.WallPerLayout then
				wallChecks += 1
				state.wallAt = now
				local up = (gui:GetAttribute("BaseLift") or 0) + lift * e.depth * studsPerPixel
				local anchor = adornee.Position + camera.CFrame.UpVector * up
				local half = textWidth(gui, e.w) / 2 * e.depth * studsPerPixel
				state.wall = hiddenInMuseum(camera, adornee, anchor, half)
			end
			hidden = state.wall
		end
		if hidden then
			state.alphaTarget = 0 -- место не меняем: гаснет там, где стоит
		else
			state.alphaTarget = 1
			state.target = lift * e.depth * studsPerPixel
		end
	end
end

function ItemLabelController.Init()
	for _, instance in Workspace:GetDescendants() do
		track(instance)
	end
	Workspace.DescendantAdded:Connect(track)
	Workspace.DescendantRemoving:Connect(function(instance)
		local state = tracked[instance :: any]
		if state and state.fades and state.alpha < 1 then
			-- вернуть исходные прозрачности: если подпись вернётся в мир, она не останется погашенной
			state.alpha = 1
			applyAlpha(instance :: any, state)
		end
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
		local fade = math.min(1, dt * cfg.FadeSpeed)
		for gui, state in tracked do
			if math.abs(state.target - state.lift) > 1e-3 then
				state.lift += (state.target - state.lift) * follow
				gui.StudsOffset = Vector3.new(0, (gui:GetAttribute("BaseLift") or 0) + state.lift, 0)
			end
			if math.abs(state.alphaTarget - state.alpha) > 1e-3 then
				state.alpha += (state.alphaTarget - state.alpha) * fade
				if math.abs(state.alphaTarget - state.alpha) <= 0.01 then
					state.alpha = state.alphaTarget
				end
				applyAlpha(gui, state)
			end
		end
	end)
end

return ItemLabelController

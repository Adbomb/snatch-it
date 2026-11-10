-- Камера в музее (D50): стены, которые реально закрывают персонажа от камеры, становятся полупрозрачными только у
-- этого игрока (LocalTransparencyModifier) — стандартная камера Roblox не считает полупрозрачное преградой и не
-- прижимается к голове в узких галереях; весь музей не прозрачный, только детали на отрезке «персонаж → камера».
-- Каждый кадр, пока персонаж внутри музея (зал, галереи, хранилище — по осям участка из атрибута FloorOrigin): отрезок
-- от фокуса камеры до места, где камера стояла бы на выбранном игроком расстоянии, и четыре соседних луча по краям
-- кадра проверяются против коробок деталей здания (Building) этого участка — своими силами, потому что у декоративных
-- деталей без столкновений выключен CanQuery и лучи Roblox их не видят. Найденные детали гаснут сразу (камера в
-- том же кадре их пропускает), остальные плавно возвращаются. Вышел из музея, сменился персонаж, перестроился музей —
-- всё возвращается. Детали, которые прячет другой код (створки решётки хранилища у владельца), не трогаются; пол и
-- ступени ниже ног персонажа не гаснут никогда — иначе камера Roblox уходит под пол.
-- С ношей над головой (крупные существа босса 3): гаснут и детали между камерой и ношей (центр и верх), и детали,
-- сквозь которые ноша проходит (крыша галереи); в галерее камера не дальше UITokens.MuseumCamera.CarryGalleryZoom,
-- на выходе из галереи — снова выбранное игроком расстояние. Blocked — для подписей экспонатов (ItemLabelController):
-- закрыт ли отрезок непрозрачной деталью здания этого музея.
-- Зависит от Config/MuseumLayout, Config/UITokens.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config")
local MuseumLayout = require(Config:WaitForChild("MuseumLayout"))
local UITokens = require(Config:WaitForChild("UITokens"))

local T = UITokens.MuseumCamera
local L = MuseumLayout
local player = Players.LocalPlayer

type Box = { part: BasePart, inv: CFrame, half: Vector3, center: Vector3, radius: number, top: number }
type Cache = { building: Instance, boxes: { Box }, dirty: boolean }

local MuseumCameraController = {}

local caches: { [Instance]: Cache } = {} -- участок → коробки деталей здания
local faded: { [BasePart]: number } = {} -- деталь → наша текущая прозрачность
local cameraModule: any = nil

-- Выбранное игроком расстояние камеры (до сдвига камеры к стене); без модуля камеры — запасное из токенов.
local function wantedDistance(camera: Camera): number
	if cameraModule == nil then
		local ok, cams = pcall(function()
			local playerModule = player:WaitForChild("PlayerScripts"):FindFirstChild("PlayerModule")
			return playerModule and (require(playerModule) :: any):GetCameras()
		end)
		cameraModule = if ok and cams then cams else false
	end
	local controller = cameraModule and cameraModule.activeCameraController
	if controller and controller.GetCameraToSubjectDistance then
		local ok, d = pcall(controller.GetCameraToSubjectDistance, controller)
		if ok and type(d) == "number" and d > 0 then
			return d
		end
	end
	return math.max((camera.CFrame.Position - camera.Focus.Position).Magnitude, T.FallbackDistance)
end

-- Участок, в музее которого стоит точка (зал, галереи с их уровня, хранилище), и её координаты в осях участка.
local function plotAt(at: Vector3): Model?
	local plots = workspace:FindFirstChild("World") and workspace.World:FindFirstChild("Plots")
	for _, plot in if plots then plots:GetChildren() else {} do
		local origin = plot:GetAttribute("FloorOrigin")
		if typeof(origin) == "CFrame" then
			local p = origin:PointToObjectSpace(at)
			local galleries = (plot:GetAttribute("MuseumLevel") or 1) >= L.Gallery.Level
			local halfX = (if galleries then L.Gallery.Out else L.Hall.HalfWidth) + T.Margin
			if
				math.abs(p.X) <= halfX
				and p.Z >= L.Gallery.Z0 - T.Margin
				and p.Z <= L.Hall.Back + T.Margin
				and p.Y >= L.Vault.Floor - T.Margin
				and p.Y <= L.Hall.Ceiling + T.Margin
			then
				return plot :: Model
			end
		end
	end
	return nil
end

local function cacheOf(plot: Instance): Cache?
	local building = plot:FindFirstChild("Building")
	if not building then
		return nil
	end
	local cache = caches[plot]
	if cache and cache.building == building and not cache.dirty then
		return cache
	end
	local fresh = not cache or cache.building ~= building
	local boxes: { Box } = {}
	for _, d in building:GetDescendants() do
		if d:IsA("BasePart") and (d.Transparency < 0.95 or d.CanCollide) then
			local half = d.Size / 2
			local cf = d.CFrame
			local extentY = math.abs(cf.RightVector.Y) * half.X
				+ math.abs(cf.UpVector.Y) * half.Y
				+ math.abs(cf.LookVector.Y) * half.Z
			table.insert(boxes, {
				part = d,
				inv = cf:Inverse(),
				half = half,
				center = d.Position,
				radius = half.Magnitude,
				top = d.Position.Y + extentY, -- верх детали в мире: пол и ступени ниже ног не гасим
			})
		end
	end
	local built: Cache = { building = building, boxes = boxes, dirty = false }
	caches[plot] = built
	if fresh then -- перестройка музея (уровень): коробки собрать заново
		local function dirty()
			local current = caches[plot]
			if current and current.building == building then
				current.dirty = true
			end
		end
		building.DescendantAdded:Connect(dirty)
		building.DescendantRemoving:Connect(dirty)
	end
	return built
end

-- Отрезок a → b пересекает коробку детали (тест плит в осях детали).
local function hits(box: Box, a: Vector3, b: Vector3): boolean
	-- грубо: центр детали дальше от отрезка, чем её радиус
	local ab = b - a
	local len2 = ab:Dot(ab)
	local t = if len2 > 1e-6 then math.clamp((box.center - a):Dot(ab) / len2, 0, 1) else 0
	if (a + ab * t - box.center).Magnitude > box.radius then
		return false
	end
	local o = box.inv * a
	local d = box.inv:VectorToWorldSpace(ab)
	local t0, t1 = 0, 1
	for _, axis in { "X", "Y", "Z" } do
		local oa, da, h = (o :: any)[axis], (d :: any)[axis], (box.half :: any)[axis]
		if math.abs(da) < 1e-6 then
			if oa < -h or oa > h then
				return false
			end
		else
			local u, v = (-h - oa) / da, (h - oa) / da
			if u > v then
				u, v = v, u
			end
			t0, t1 = math.max(t0, u), math.min(t1, v)
			if t0 > t1 then
				return false
			end
		end
	end
	return true
end

local function setFade(part: BasePart, value: number)
	if value <= 0.001 then
		if part.Parent and math.abs(part.LocalTransparencyModifier - (faded[part] or 0)) < 0.001 then
			part.LocalTransparencyModifier = 0
		end
		faded[part] = nil
	else
		part.LocalTransparencyModifier = value
		faded[part] = value
	end
end

-- Вернуть всё сразу (выход из музея, новый персонаж).
local function restoreAll()
	for part in faded do
		setFade(part, 0)
	end
end

-- Ноша над головой: деталь предмета, приваренная к корню персонажа (CarryService). Ищем по суставам корня, пока
-- сварка не пришла — не чаще CarryRescan.
local carried: BasePart? = nil
local carriedId: any = nil
local lastScan = 0
local function carriedPart(root: BasePart): BasePart?
	local id = player:GetAttribute("CarryingItemId")
	if id == nil then
		carried, carriedId = nil, nil
		return nil
	end
	if carried and carried.Parent and carriedId == id then
		return carried
	end
	if os.clock() - lastScan < T.CarryRescan then
		return nil
	end
	lastScan = os.clock()
	carried, carriedId = nil, id
	for _, joint in root:GetJoints() do
		if joint:IsA("WeldConstraint") then
			local other = if joint.Part0 == root then joint.Part1 else joint.Part0
			if other and other:GetAttribute("ItemId") == id then
				carried = other
				break
			end
		end
	end
	return carried
end

-- В галерее (за стенами зала по оси x участка).
local function inGallery(plot: Model, at: Vector3): boolean
	local origin = plot:GetAttribute("FloorOrigin")
	return typeof(origin) == "CFrame" and math.abs(origin:PointToObjectSpace(at).X) > L.Hall.HalfWidth
end

-- Камера ближе в галерее с ношей: прежний предел и выбранное расстояние, чтобы вернуть их на выходе.
local zoomCap: { max: number, distance: number }? = nil
local function setGalleryZoom(on: boolean, camera: Camera?)
	if on and not zoomCap and camera then
		zoomCap = { max = player.CameraMaxZoomDistance, distance = wantedDistance(camera) }
		player.CameraMaxZoomDistance = math.min(player.CameraMaxZoomDistance, T.CarryGalleryZoom)
	elseif not on and zoomCap then
		local saved = zoomCap
		zoomCap = nil
		player.CameraMaxZoomDistance = saved.max
		if not player:GetAttribute("Knocked") and saved.distance > T.CarryGalleryZoom then
			-- вернуть отдаление игрока: на кадр поднять нижний предел до прежнего расстояния
			local min = player.CameraMinZoomDistance
			player.CameraMinZoomDistance = math.min(saved.distance, saved.max)
			task.defer(function()
				player.CameraMinZoomDistance = min
			end)
		end
	end
end

-- Закрыт ли отрезок a → b непрозрачной деталью здания музея, в котором стоит точка b (подписи экспонатов).
function MuseumCameraController.Blocked(a: Vector3, b: Vector3): boolean
	local plot = plotAt(b)
	local cache = plot and cacheOf(plot)
	if not cache then
		return false
	end
	for _, box in cache.boxes do
		local part = box.part
		if part.Parent and part.Transparency < 0.5 and part.LocalTransparencyModifier < 0.5 and hits(box, a, b) then
			return true
		end
	end
	return false
end

local function step(dt: number)
	local camera = workspace.CurrentCamera
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
	local plot = root and camera and camera.CameraType == Enum.CameraType.Custom and plotAt(root.Position)
	local cache = plot and cacheOf(plot)
	local want: { [BasePart]: boolean } = {}
	if cache and camera and root then
		-- ниже ног — пол, ступени, потолок хранилища под залом: их не гасить, иначе камера уходит под пол (D50)
		local humanoid = root.Parent and root.Parent:FindFirstChildOfClass("Humanoid")
		local feet = root.Position.Y - root.Size.Y / 2 - (if humanoid then humanoid.HipHeight else 2) + T.FloorTolerance
		local focus = camera.Focus.Position
		local look = camera.CFrame.LookVector
		local far = focus - look * wantedDistance(camera)
		local right = camera.CFrame.RightVector * T.Probe
		local up = camera.CFrame.UpVector * T.Probe
		local segments = {}
		for _, ends in { far, far + right, far - right, far + up, far - up } do
			table.insert(segments, { focus, ends })
		end
		local load = carriedPart(root)
		if load then
			-- ноша: от камеры к её центру и верху; и сама ноша сквозь детали (вертикали по центру и углам)
			local c, h = load.Position, load.Size.Y / 2
			table.insert(segments, { far, c })
			table.insert(segments, { far, c + Vector3.new(0, h, 0) })
			local hx, hz = load.Size.X / 2, load.Size.Z / 2
			for _, off in
				{
					Vector3.zero,
					Vector3.new(hx, 0, hz),
					Vector3.new(-hx, 0, hz),
					Vector3.new(hx, 0, -hz),
					Vector3.new(-hx, 0, -hz),
				}
			do
				table.insert(segments, { c + off - Vector3.new(0, h, 0), c + off + Vector3.new(0, h, 0) })
			end
		end
		for _, seg in segments do
			for _, box in cache.boxes do
				if not want[box.part] and box.top > feet and box.part.Parent and hits(box, seg[1], seg[2]) then
					-- чужая локальная прозрачность (спрятанные створки) — не наша
					local own = faded[box.part]
					if own ~= nil or box.part.LocalTransparencyModifier < 0.001 then
						want[box.part] = true
					end
				end
			end
		end
	end
	local gallery = false
	if cache and root and plot and carriedPart(root) then
		gallery = inGallery(plot, root.Position)
	end
	setGalleryZoom(gallery, camera)
	for part in want do
		if (faded[part] or 0) < T.Fade then
			setFade(part, T.Fade) -- сразу: камера в этом же кадре не считает деталь преградой
		end
	end
	local k = math.min(1, dt * T.ReturnSpeed)
	for part, value in faded do
		if not want[part] then
			setFade(part, if part.Parent then value * (1 - k) else 0)
		end
	end
end

function MuseumCameraController.Init()
	-- раньше камеры Roblox: погашенные в этом кадре детали она уже не считает преградой
	RunService:BindToRenderStep("MuseumCameraFade", Enum.RenderPriority.Camera.Value - 2, step)
	player.CharacterRemoving:Connect(restoreAll)
	player.CharacterAdded:Connect(restoreAll)
end

return MuseumCameraController

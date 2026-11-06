-- Камера в музее (D50): стены, которые реально закрывают персонажа от камеры, становятся полупрозрачными только у
-- этого игрока (LocalTransparencyModifier) — стандартная камера Roblox не считает полупрозрачное преградой и не
-- прижимается к голове в узких галереях; весь музей не прозрачный, только детали на отрезке «персонаж → камера».
-- Каждый кадр, пока персонаж внутри музея (зал, галереи, хранилище — по осям участка из атрибута FloorOrigin): отрезок
-- от фокуса камеры до места, где камера стояла бы на выбранном игроком расстоянии, и четыре соседних луча по краям
-- кадра проверяются против коробок деталей здания (Building) этого участка — своими силами, потому что у декоративных
-- деталей без столкновений выключен CanQuery и лучи Roblox их не видят. Найденные детали гаснут сразу (камера в
-- том же кадре их пропускает), остальные плавно возвращаются. Вышел из музея, сменился персонаж, перестроился музей —
-- всё возвращается. Детали, которые прячет другой код (створки решётки хранилища у владельца), не трогаются.
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

type Box = { part: BasePart, inv: CFrame, half: Vector3, center: Vector3, radius: number }
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
			table.insert(boxes, {
				part = d,
				inv = d.CFrame:Inverse(),
				half = half,
				center = d.Position,
				radius = half.Magnitude,
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

local function step(dt: number)
	local camera = workspace.CurrentCamera
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
	local plot = root and camera and camera.CameraType == Enum.CameraType.Custom and plotAt(root.Position)
	local cache = plot and cacheOf(plot)
	local want: { [BasePart]: boolean } = {}
	if cache and camera then
		local focus = camera.Focus.Position
		local look = camera.CFrame.LookVector
		local far = focus - look * wantedDistance(camera)
		local right = camera.CFrame.RightVector * T.Probe
		local up = camera.CFrame.UpVector * T.Probe
		for _, ends in { far, far + right, far - right, far + up, far - up } do
			for _, box in cache.boxes do
				if not want[box.part] and box.part.Parent and hits(box, focus, ends) then
					-- чужая локальная прозрачность (спрятанные створки) — не наша
					local own = faded[box.part]
					if own ~= nil or box.part.LocalTransparencyModifier < 0.001 then
						want[box.part] = true
					end
				end
			end
		end
	end
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

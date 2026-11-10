-- Камера в музее (D50): стены, которые реально закрывают персонажа от камеры, становятся полупрозрачными только у
-- этого игрока (LocalTransparencyModifier) — стандартная камера Roblox не считает полупрозрачное преградой и не
-- прижимается к голове в узких галереях; весь музей не прозрачный, только детали на отрезке «персонаж → камера».
-- Каждый кадр, пока персонаж внутри музея (зал, галереи, хранилище — по осям участка из атрибута FloorOrigin): отрезок
-- толщиной Probe от фокуса камеры до места, где камера стояла бы на выбранном игроком расстоянии, проверяется против
-- коробок деталей здания (Building) этого участка — своими силами, потому что у декоративных
-- деталей без столкновений выключен CanQuery и лучи Roblox их не видят. Найденные детали гаснут сразу (камера в
-- том же кадре их пропускает), остальные плавно возвращаются. Вышел из музея, сменился персонаж, перестроился музей —
-- всё возвращается. Детали, которые прячет другой код (створки решётки хранилища у владельца), не трогаются; пол и
-- ступени ниже ног персонажа не гаснут никогда — иначе камера Roblox уходит под пол.
-- С ношей над головой (крупные существа босса 3): гаснут и детали между камерой и ношей (центр и верх), и детали,
-- сквозь которые ноша проходит (крыша галереи); в галерее камера не дальше UITokens.MuseumCamera.CarryGalleryZoom,
-- на выходе из галереи — снова выбранное игроком расстояние. Blocked — для подписей экспонатов (ItemLabelController):
-- закрыт ли отрезок непрозрачной деталью здания этого музея.
-- Постаменты (тумбы Showcases, их верх и табличка) гаснут так же, как стены, а отрезок от камеры идёт ещё и к корпусу:
-- низкая камера за тумбой не закрывает персонажа и не прижимается к нему (камера Roblox не считает погашенное
-- преградой); надписи погашенной детали (табличка — SurfaceGui) на это время выключены; постамент гаснет целиком.
-- Экспонаты рядом: гаснут и детали между камерой и серединой ближайших экспонатов (толстый отрезок) в той же части
-- музея (зал, левая или правая
-- галерея), что и персонаж, — не дальше ExhibitRadius, не больше ExhibitMax, только в кадре; тумба самого экспоната
-- не гаснет. Экспонат между камерой и персонажем гаснет так же (видимые детали); детали и экспонаты вплотную к камере
-- (ближе NearCamera — низкая камера между тумбами) тоже гаснут; камера в другой части музея, чем персонаж (за стеной
-- галереи), — гаснут экспонаты и постаменты той части ближе OtherRoomRadius к камере. Перед проверкой отрезков детали
-- отбираются по общему габариту отрезков и каждого отрезка — на телефоне дёшево.
-- Место (тумба и экспонат над ней) камера не пересекает изнутри: после камеры Roblox (Camera + 1) камеру внутри места
-- подтягивает к персонажу до края места (сразу), обратно — плавно (ColumnRelease); место, на котором стоит сам
-- персонаж, не считается. Выбранное игроком расстояние не меняется.
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

type Box = {
	part: BasePart,
	inv: CFrame,
	half: Vector3,
	center: Vector3,
	radius: number,
	top: number,
	slot: number?, -- деталь постамента этого места (тумба, верх, табличка); nil — здание
}
-- тумба места: её CFrame, половина размера и высота центра (для подтягивания камеры от места)
type Column = { slot: number, cf: CFrame, half: Vector3, y: number }
type Cache = { building: Instance, boxes: { Box }, pedestals: { Box }, columns: { Column }, dirty: boolean }
-- slot — отрезок к экспонату: его постамент не гасить; pad — толщина отрезка (стадов)
type Segment = { a: Vector3, b: Vector3, slot: number?, pad: number? }

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
	local function collect(d: Instance, slot: number?)
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
				slot = slot,
			})
		end
	end
	for _, d in building:GetDescendants() do
		collect(d, nil)
	end
	local showcases = plot:FindFirstChild("Showcases")
	local columns: { Column } = {}
	for _, showcase in if showcases then showcases:GetChildren() else {} do
		local slot = showcase:GetAttribute("Slot")
		if type(slot) == "number" and showcase:IsA("BasePart") then
			table.insert(
				columns,
				{ slot = slot, cf = showcase.CFrame, half = showcase.Size / 2, y = showcase.Position.Y }
			)
		end
		if type(slot) == "number" then
			collect(showcase, slot)
			for _, d in showcase:GetDescendants() do
				collect(d, slot)
			end
		end
	end
	local pedestals: { Box } = {}
	for _, box in boxes do
		if box.slot then
			table.insert(pedestals, box)
		end
	end
	-- удалённая деталь помечает кэш (DescendantRemoving) — в горячих циклах Parent не проверяется
	local built: Cache = { building = building, boxes = boxes, pedestals = pedestals, columns = columns, dirty = false }
	caches[plot] = built
	if fresh then -- перестройка музея (уровень), новые детали постаментов: коробки собрать заново
		local function dirty()
			local current = caches[plot]
			if current and current.building == building then
				current.dirty = true
			end
		end
		building.DescendantAdded:Connect(dirty)
		building.DescendantRemoving:Connect(dirty)
		if showcases then
			showcases.DescendantAdded:Connect(dirty)
			showcases.DescendantRemoving:Connect(dirty)
		end
	end
	return built
end

-- Одна ось теста плит: сужает [t0, t1]; nil — мимо.
local function slab(o: number, d: number, h: number, t0: number, t1: number): (number?, number)
	if math.abs(d) < 1e-6 then
		if o < -h or o > h then
			return nil, t1
		end
		return t0, t1
	end
	local u, v = (-h - o) / d, (h - o) / d
	if u > v then
		u, v = v, u
	end
	t0, t1 = math.max(t0, u), math.min(t1, v)
	if t0 > t1 then
		return nil, t1
	end
	return t0, t1
end

-- Отрезок a → b толщиной pad (коробка детали раздута на pad) пересекает коробку детали (тест плит в осях детали).
local function hits(box: Box, a: Vector3, b: Vector3, pad: number?): boolean
	local p = pad or 0
	-- грубо: центр детали дальше от отрезка, чем её радиус
	local ab = b - a
	local len2 = ab:Dot(ab)
	local t = if len2 > 1e-6 then math.clamp((box.center - a):Dot(ab) / len2, 0, 1) else 0
	if (a + ab * t - box.center).Magnitude > box.radius + p then
		return false
	end
	local o = box.inv * a
	local d = box.inv:VectorToWorldSpace(ab)
	local h = box.half
	local t0: number?, t1 = slab(o.X, d.X, h.X + p, 0, 1)
	if t0 then
		t0, t1 = slab(o.Y, d.Y, h.Y + p, t0, t1)
	end
	if t0 then
		t0, t1 = slab(o.Z, d.Z, h.Z + p, t0, t1)
	end
	return t0 ~= nil
end

-- Надписи на погашенной детали (табличка постамента — SurfaceGui с тёмным фоном): прозрачность детали на них не
-- действует, поэтому, пока деталь погашена больше чем наполовину, они выключены, потом — включаются обратно.
local hiddenGuis: { [BasePart]: { SurfaceGui } } = {}
local function setGuis(part: BasePart, hide: boolean)
	if hide and not hiddenGuis[part] then
		local list = {}
		for _, d in part:GetDescendants() do
			if d:IsA("SurfaceGui") and d.Enabled then
				d.Enabled = false
				table.insert(list, d)
			end
		end
		hiddenGuis[part] = list
	elseif not hide and hiddenGuis[part] then
		for _, gui in hiddenGuis[part] do
			if gui.Parent then
				gui.Enabled = true
			end
		end
		hiddenGuis[part] = nil
	end
end

local function setFade(part: BasePart, value: number)
	if value <= 0.001 then
		if part.Parent and math.abs(part.LocalTransparencyModifier - (faded[part] or 0)) < 0.001 then
			part.LocalTransparencyModifier = 0
		end
		faded[part] = nil
		setGuis(part, false)
	else
		part.LocalTransparencyModifier = value
		faded[part] = value
		setGuis(part, value >= 0.5)
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
		if
			box.slot == nil -- постаменты подписи не закрывают (прежнее поведение подписей)
			and part.Parent
			and part.Transparency < 0.5
			and part.LocalTransparencyModifier < 0.5
			and hits(box, a, b)
		then
			return true
		end
	end
	return false
end

-- Часть музея по оси x участка: −1 — левая галерея, 0 — зал (и хранилище под ним), 1 — правая галерея.
local function sideOf(origin: CFrame, at: Vector3): number
	local x = origin:PointToObjectSpace(at).X
	return if x > L.Hall.HalfWidth then 1 elseif x < -L.Hall.HalfWidth then -1 else 0
end

-- Отрезки от камеры к ближайшим экспонатам в той же части музея, что и персонаж (в кадре, не дальше ExhibitRadius).
local function exhibitSegments(plot: Model, camera: Camera, root: BasePart, far: Vector3, segments: { Segment })
	local origin = plot:GetAttribute("FloorOrigin")
	local exhibits = plot:FindFirstChild("Exhibits")
	if typeof(origin) ~= "CFrame" or not exhibits then
		return
	end
	local side = sideOf(origin, root.Position)
	local near: { { part: BasePart, dist: number } } = {}
	for _, ex in exhibits:GetChildren() do
		if ex:IsA("BasePart") and type(ex:GetAttribute("Slot")) == "number" then
			local dist = (ex.Position - root.Position).Magnitude
			if dist <= T.ExhibitRadius and sideOf(origin, ex.Position) == side then
				local _, visible = camera:WorldToViewportPoint(ex.Position)
				if visible then
					table.insert(near, { part = ex, dist = dist })
				end
			end
		end
	end
	table.sort(near, function(a, b)
		return a.dist < b.dist
	end)
	for i = 1, math.min(#near, T.ExhibitMax) do
		-- один толстый отрезок к середине экспоната (по высоте — от центра до верхней трети)
		local ex = near[i].part
		local slot = ex:GetAttribute("Slot") :: number
		local mid = ex.Position + Vector3.new(0, ex.Size.Y * 0.2, 0)
		table.insert(segments, { a = far, b = mid, slot = slot, pad = ex.Size.Y * 0.2 })
	end
end

-- Расстояние от точки до коробки детали (0 — внутри).
local function boxDistance(box: Box, at: Vector3): number
	local l = box.inv * at
	local h = box.half
	local clamped = Vector3.new(math.clamp(l.X, -h.X, h.X), math.clamp(l.Y, -h.Y, h.Y), math.clamp(l.Z, -h.Z, h.Z))
	return (l - clamped).Magnitude
end

-- Видимые детали экспоната (корень и детали внутри, у которых прозрачность < 0.95): собираются один раз на экспонат
-- (экспонат на постаменте — новая деталь, ключи слабые) и заново, если в нём появилось новое (модель приходит на
-- клиент по частям).
local partsOf: { [BasePart]: { BasePart } } = setmetatable({}, { __mode = "k" }) :: any
local function visibleParts(ex: BasePart): { BasePart }
	local list = partsOf[ex]
	if not list then
		local fresh = {}
		for _, d in { ex :: Instance, table.unpack(ex:GetDescendants()) } do
			if d:IsA("BasePart") and d.Transparency < 0.95 then
				table.insert(fresh, d)
			end
		end
		partsOf[ex] = fresh
		ex.DescendantAdded:Once(function()
			partsOf[ex] = nil
		end)
		list = fresh
	end
	return list
end

-- Экспонаты, которые закрывают персонажа (отрезки к нему — первые count в segments), стоят вплотную к камере (eye)
-- или на переднем плане чужой части музея (otherSide — часть, где камера, если персонаж в другой): их видимые
-- детали — в want.
local function fadeBlockingExhibits(
	plot: Model,
	segments: { Segment },
	count: number,
	eye: Vector3,
	otherSide: number?,
	want: { [BasePart]: boolean }
)
	local exhibits = plot:FindFirstChild("Exhibits")
	local origin = plot:GetAttribute("FloorOrigin")
	for _, ex in if exhibits then exhibits:GetChildren() else {} do
		if not ex:IsA("BasePart") then
			continue
		end
		local center = ex.Position
		local half = ex.Size / 2
		local radius = half.Magnitude
		local toEye = (center - eye).Magnitude
		local blocking = otherSide ~= nil
			and toEye < T.OtherRoomRadius
			and typeof(origin) == "CFrame"
			and sideOf(origin, center) == otherSide
		if not blocking then
			-- точная проверка (коробка с обратным CFrame) — только если сфера экспоната рядом с камерой или отрезком
			local box: Box? = nil
			if toEye - radius < T.NearCamera then
				box = { part = ex, inv = ex.CFrame:Inverse(), half = half, center = center, radius = radius, top = 0 }
				blocking = boxDistance(box :: Box, eye) < T.NearCamera
			end
			for i = 1, math.min(count, #segments) do
				if blocking then
					break
				end
				local seg = segments[i]
				local pad = seg.pad or 0
				local ab = seg.b - seg.a
				local len2 = ab:Dot(ab)
				local t = if len2 > 1e-6 then math.clamp((center - seg.a):Dot(ab) / len2, 0, 1) else 0
				if (seg.a + ab * t - center).Magnitude <= radius + pad then
					box = box
						or {
							part = ex,
							inv = ex.CFrame:Inverse(),
							half = half,
							center = center,
							radius = radius,
							top = 0,
						}
					blocking = hits(box :: Box, seg.a, seg.b, seg.pad)
				end
			end
		end
		if blocking then
			for _, d in visibleParts(ex) do
				if d.Parent and (faded[d] ~= nil or d.LocalTransparencyModifier < 0.001) then
					want[d] = true
				end
			end
		end
	end
end

-- Камера внутри места (тумба и экспонат над ней) — подтянуть к персонажу до края места; после камеры Roblox.
local clampDistance = math.huge
-- участок и коробки, которые нашёл шаг гашения в этом кадре (он раньше камеры Roblox, подтягивание — после)
local currentPlot: Model? = nil
local currentCache: Cache? = nil
-- место и верх экспоната (экспонат на постаменте неподвижен; новый экспонат — новая деталь, ключи слабые)
local exhibitTop: { [BasePart]: { slot: number, top: number } } = setmetatable({}, { __mode = "k" }) :: any
local function clampStep(dt: number)
	local camera = workspace.CurrentCamera
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
	local plot, cache = currentPlot, currentCache
	if not plot or not cache or not camera or not root or camera.CameraType ~= Enum.CameraType.Custom then
		clampDistance = math.huge
		return
	end
	local focus = camera.Focus.Position
	local cf = camera.CFrame
	local offset = cf.Position - focus
	local length = offset.Magnitude
	if length < 0.5 then
		return
	end
	local tops: { [number]: number } = {} -- верх экспоната на месте
	local exhibits = plot:FindFirstChild("Exhibits")
	for _, ex in if exhibits then exhibits:GetChildren() else {} do
		if ex:IsA("BasePart") then
			local info = exhibitTop[ex]
			if not info then
				local slot = ex:GetAttribute("Slot")
				info = { slot = if type(slot) == "number" then slot else -1, top = ex.Position.Y + ex.Size.Y / 2 }
				exhibitTop[ex] = info
			end
			tops[info.slot] = math.max(tops[info.slot] or -math.huge, info.top)
		end
	end
	-- места: коробка в осях тумбы по высоте до верха экспоната (с запасом); место под персонажем не считается
	local m = T.ColumnMargin
	local columns: { { frame: CFrame, box: Vector3 } } = {}
	for _, col in cache.columns do
		local half = col.half
		local bottom = col.y - half.Y
		local top = math.max(col.y + half.Y, tops[col.slot] or -math.huge)
		local box = Vector3.new(half.X + m, (top - bottom) / 2 + m, half.Z + m)
		local frame = col.cf * CFrame.new(0, (top + bottom) / 2 - col.y, 0)
		local feet = frame:PointToObjectSpace(root.Position)
		if math.abs(feet.X) >= box.X or math.abs(feet.Z) >= box.Z then
			table.insert(columns, { frame = frame, box = box })
		end
	end
	-- точка на расстоянии dist внутри места — к входу в него отрезка «фокус → камера»; вытянутая из одного места
	-- может оказаться в соседнем — повторить
	local dir = offset.Unit
	local function settle(dist: number): number
		for _ = 1, 4 do
			local point = focus + dir * dist
			local nearest = math.huge
			for _, col in columns do
				local at = col.frame:PointToObjectSpace(point)
				local box = col.box
				if math.abs(at.X) < box.X and math.abs(at.Y) < box.Y and math.abs(at.Z) < box.Z then
					local o = col.frame:PointToObjectSpace(focus)
					local d = at - o
					local enter = 0
					for _, axis in { "X", "Y", "Z" } do
						local oa, da, h = (o :: any)[axis], (d :: any)[axis], (box :: any)[axis]
						if math.abs(da) > 1e-6 then
							enter = math.max(enter, math.min((-h - oa) / da, (h - oa) / da))
						end
					end
					nearest = math.min(nearest, math.max(enter * dist - m, 0.5))
				end
			end
			if nearest == math.huge then
				break
			end
			dist = nearest
		end
		return dist
	end
	local target = settle(length)
	if target < length - 1e-3 and target < clampDistance then
		clampDistance = target -- сразу: камера не должна оказаться внутри места
	elseif clampDistance < length then
		-- отпускать плавно; если по дороге точка внутри места — сразу в свободное положение
		clampDistance = math.min(target, clampDistance + T.ColumnRelease * dt)
		if settle(clampDistance) < clampDistance - 1e-3 then
			clampDistance = target
		end
	else
		clampDistance = math.huge -- не держим: камера Roblox сама (зум игрока не трогаем)
	end
	if clampDistance < length then
		camera.CFrame = cf + dir * (clampDistance - length)
	end
end

local function step(dt: number)
	local camera = workspace.CurrentCamera
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
	local plot = root and camera and camera.CameraType == Enum.CameraType.Custom and plotAt(root.Position)
	local cache = plot and cacheOf(plot)
	currentPlot = if cache then plot :: Model else nil
	currentCache = cache or nil
	local want: { [BasePart]: boolean } = {}
	if cache and camera and root then
		-- ниже ног — пол, ступени, потолок хранилища под залом: их не гасить, иначе камера уходит под пол (D50)
		local humanoid = root.Parent and root.Parent:FindFirstChildOfClass("Humanoid")
		local feet = root.Position.Y - root.Size.Y / 2 - (if humanoid then humanoid.HipHeight else 2) + T.FloorTolerance
		local focus = camera.Focus.Position
		local look = camera.CFrame.LookVector
		local far = focus - look * wantedDistance(camera)
		-- от фокуса к камере — один отрезок толщиной Probe (вместо пяти лучей по краям кадра)
		local segments: { Segment } = { { a = focus, b = far, pad = T.Probe } }
		-- и к корпусу: снизу (камера ниже головы) тумба закрывает тело, а не фокус у головы
		table.insert(segments, { a = far, b = root.Position })
		-- камера в другой части музея, чем персонаж: передний план той части гаснет
		local origin = (plot :: Model):GetAttribute("FloorOrigin")
		local eyeSide = if typeof(origin) == "CFrame" then sideOf(origin, camera.CFrame.Position) else nil
		local otherSide = if typeof(origin) == "CFrame" and eyeSide ~= sideOf(origin, root.Position)
			then eyeSide
			else nil
		fadeBlockingExhibits(plot :: Model, segments, #segments, camera.CFrame.Position, otherSide, want)
		local load = carriedPart(root)
		if load then
			-- ноша: от камеры к её центру и верху; и сама ноша сквозь детали (вертикали по центру и углам)
			local c, h = load.Position, load.Size.Y / 2
			table.insert(segments, { a = far, b = c })
			table.insert(segments, { a = far, b = c + Vector3.new(0, h, 0) })
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
				table.insert(segments, { a = c + off - Vector3.new(0, h, 0), b = c + off + Vector3.new(0, h, 0) })
			end
		end
		exhibitSegments(plot :: Model, camera, root, far, segments)
		-- отбор: только детали, задевающие общий габарит всех отрезков (выше ног)
		local eye = camera.CFrame.Position -- камера прошлого кадра (после подтягивания от мест)
		local near = Vector3.one * T.NearCamera
		local lo, hi = focus:Min(eye - near), focus:Max(eye + near)
		for _, seg in segments do
			lo = lo:Min(seg.a):Min(seg.b)
			hi = hi:Max(seg.a):Max(seg.b)
		end
		local candidates: { Box } = {}
		local pad = 0 -- наибольшая толщина отрезков
		for _, seg in segments do
			pad = math.max(pad, seg.pad or 0)
		end
		for _, box in cache.boxes do
			local c, r = box.center, box.radius + pad
			if
				box.top > feet
				and c.X + r >= lo.X
				and c.X - r <= hi.X
				and c.Y + r >= lo.Y
				and c.Y - r <= hi.Y
				and c.Z + r >= lo.Z
				and c.Z - r <= hi.Z
			then
				table.insert(candidates, box)
			end
		end
		-- вплотную к камере (низкая камера между тумбами): гаснут, чтобы не заслонять кадр
		for _, box in candidates do
			if (box.center - eye).Magnitude - box.radius < T.NearCamera and boxDistance(box, eye) < T.NearCamera then
				if faded[box.part] ~= nil or box.part.LocalTransparencyModifier < 0.001 then
					want[box.part] = true
				end
			end
		end
		for _, seg in segments do
			-- быстрый отсев по габариту отрезка до точной проверки (на телефоне дорог каждый вызов)
			local a, b, segPad = seg.a, seg.b, seg.pad or 0
			local x0, x1 = math.min(a.X, b.X), math.max(a.X, b.X)
			local y0, y1 = math.min(a.Y, b.Y), math.max(a.Y, b.Y)
			local z0, z1 = math.min(a.Z, b.Z), math.max(a.Z, b.Z)
			for _, box in candidates do
				local c, r = box.center, box.radius + segPad
				-- к экспонату: его собственный постамент не гасить
				if
					c.X + r >= x0
					and c.X - r <= x1
					and c.Y + r >= y0
					and c.Y - r <= y1
					and c.Z + r >= z0
					and c.Z - r <= z1
					and not want[box.part]
					and (seg.slot == nil or box.slot ~= seg.slot)
					and hits(box, a, b, segPad)
				then
					-- чужая локальная прозрачность (спрятанные створки) — не наша
					local own = faded[box.part]
					if own ~= nil or box.part.LocalTransparencyModifier < 0.001 then
						want[box.part] = true
					end
				end
			end
		end
		-- постамент гаснет целиком (тумба, верх, табличка): иначе сквозь тумбу видна непогашенная табличка
		local slots: { [number]: boolean } = {}
		for _, box in candidates do
			if box.slot and want[box.part] then
				slots[box.slot] = true
			end
		end
		if otherSide ~= nil then
			-- и постаменты переднего плана чужой части музея (камера за стеной комнаты персонажа)
			for _, box in cache.pedestals do
				if
					not slots[box.slot :: number]
					and (box.center - eye).Magnitude < T.OtherRoomRadius
					and sideOf(origin :: CFrame, box.center) == otherSide
				then
					slots[box.slot :: number] = true
				end
			end
		end
		if next(slots) then
			for _, box in cache.pedestals do
				if slots[box.slot :: number] then
					if faded[box.part] ~= nil or box.part.LocalTransparencyModifier < 0.001 then
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
	-- после камеры Roblox: не пускать камеру внутрь места с экспонатом
	RunService:BindToRenderStep("MuseumCameraColumn", Enum.RenderPriority.Camera.Value + 1, clampStep)
	player.CharacterRemoving:Connect(restoreAll)
	player.CharacterAdded:Connect(restoreAll)
end

return MuseumCameraController

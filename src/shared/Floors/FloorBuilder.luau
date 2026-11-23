--!strict
-- Сборка деталей башни из кирпичей (этапы B–C): тот же формат, что у World/ModelBuilder (size, cframe, color,
-- material, shape, transparency, name, light, variant), плюс text — табличка с надписью (SurfaceGui на грани −Z).
-- Нужен и серверу (каркас этажа: столкновения, невидимый) и клиенту (убранство: без столкновений, CanQuery и CanTouch
-- выключены). Всё Anchored и Plastic по умолчанию — квадратные пупырышки даёт MaterialVariant LegoSquares (D36,
-- Shared/LegoMaterial); темы этажей ставят своим деталям LegoSquaresSoft (variant), как у музеев.
-- Кирпич с полем mesh — MeshPart: клон шаблона из ReplicatedStorage.FloorMeshes (грузит сервер,
-- World/FloorMeshLoader); cframe — центр габаритов меша, color — Color (умножается на цвета вершин), без столкновений.
-- Шаблона нет (меш не загрузился) — деталь пропускается.
-- Build — сразу; BuildChunked — частями за кадр (клиент, не больше perFrame деталей за кадр).
-- Ни от чего не зависит.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local MESH_FOLDER = "FloorMeshes"

local FloorBuilder = {}

export type Brick = {
	size: Vector3,
	cframe: CFrame,
	color: Color3,
	material: Enum.Material?,
	shape: string?, -- Block | Ball | Cylinder | Wedge | CornerWedge
	transparency: number?,
	name: string?,
	light: { range: number, brightness: number, color: Color3, spot: number? }?, -- spot — прожектор вниз, градусы
	text: { text: string, color: Color3?, size: number? }?, -- табличка: SmoothPlastic, надпись на грани −Z
	variant: string?, -- MaterialVariant у Plastic (темы этажей — LegoSquaresSoft, как музеи D36)
	-- стена каркаса в убранстве клиента: при opts.occlude сталкивается у этого клиента (камера Roblox упирается в неё,
	-- а не уходит сквозь невидимую серверную стену). Стоит ровно на месте стены каркаса (Lune check_tower).
	occlude: boolean?,
	mesh: string?, -- имя шаблона MeshPart в ReplicatedStorage.FloorMeshes (size — габарит меша, для проверок)
}

-- collide — столкновения и лучи (каркас сервера); invisible — каркас без вида (вид рисует клиент); shadow — тени;
-- occlude — у кирпичей occlude включить столкновения (только убранство клиента).
export type Options = { collide: boolean?, invisible: boolean?, shadow: boolean?, occlude: boolean? }

function FloorBuilder.Brick(size: Vector3, at: Vector3 | CFrame, color: Color3, extra: { [string]: any }?): Brick
	local brick: { [string]: any } = {
		size = size,
		cframe = if typeof(at) == "CFrame" then at else CFrame.new(at :: Vector3),
		color = color,
	}
	if extra then
		for key, value in extra do
			brick[key] = value
		end
	end
	return brick :: Brick
end

-- Шаблон меша этажа по имени (nil — ещё не загружен или не загрузился).
function FloorBuilder.MeshTemplate(name: string): MeshPart?
	local folder = ReplicatedStorage:FindFirstChild(MESH_FOLDER)
	local template = if folder then folder:FindFirstChild(name) else nil
	return if template and template:IsA("MeshPart") then template else nil
end

-- Загружены ли все шаблоны мешей (атрибут Ready папки); ждёт не дольше timeout секунд.
function FloorBuilder.WaitMeshes(timeout: number): boolean
	local deadline = os.clock() + timeout
	while os.clock() < deadline do
		local folder = ReplicatedStorage:FindFirstChild(MESH_FOLDER)
		if folder and folder:GetAttribute("Ready") == true then
			return true
		end
		task.wait(0.1)
	end
	return false
end

local function makeMesh(brick: Brick, options: Options): BasePart?
	local template = FloorBuilder.MeshTemplate(brick.mesh :: string)
	if not template then
		return nil
	end
	local part = template:Clone()
	part.Name = brick.name or (brick.mesh :: string)
	part.Anchored = true
	part.CFrame = brick.cframe
	part.Color = brick.color
	part.Material = brick.material or Enum.Material.SmoothPlastic
	if brick.variant and part.Material == Enum.Material.Plastic then
		part.MaterialVariant = brick.variant
	end
	part.Transparency = if options.invisible then 1 else (brick.transparency or 0)
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	return part
end

-- Деталь по кирпичу; nil — меш кирпича не загружен (деталь пропускается).
function FloorBuilder.MakePart(brick: Brick, opts: Options?): BasePart?
	local options = opts or {}
	if brick.mesh then
		return makeMesh(brick, options)
	end
	local part = Instance.new("Part")
	if brick.shape and brick.shape ~= "Block" then
		part.Shape = (Enum.PartType :: any)[brick.shape]
	end
	part.Name = brick.name or "Brick"
	part.Anchored = true
	part.Size = brick.size
	part.CFrame = brick.cframe
	part.Color = brick.color
	part.Material = brick.material or (if brick.text then Enum.Material.SmoothPlastic else Enum.Material.Plastic)
	if brick.variant and part.Material == Enum.Material.Plastic then
		part.MaterialVariant = brick.variant
	end
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Transparency = if options.invisible then 1 else (brick.transparency or 0)
	local solid = options.collide == true or (options.occlude == true and brick.occlude == true)
	part.CanCollide = solid
	part.CanQuery = solid
	part.CanTouch = false
	part.CastShadow = options.shadow ~= false and not options.invisible
	if brick.light and not options.invisible then
		-- spot — прожектор вниз (угол в градусах), иначе точечный свет
		local spot = brick.light.spot
		local light: Light = if spot then Instance.new("SpotLight") else Instance.new("PointLight")
		if spot then
			local s = light :: SpotLight
			s.Range = brick.light.range
			s.Angle = spot
			s.Face = Enum.NormalId.Bottom
		else
			(light :: PointLight).Range = brick.light.range
		end
		light.Brightness = brick.light.brightness
		light.Color = brick.light.color
		light.Shadows = false
		light.Parent = part
	end
	if brick.text and not options.invisible then
		local gui = Instance.new("SurfaceGui")
		gui.Face = Enum.NormalId.Front
		gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		gui.PixelsPerStud = 40
		gui.LightInfluence = 0
		local label = Instance.new("TextLabel")
		label.BackgroundTransparency = 1
		label.Size = UDim2.fromScale(1, 1)
		label.Font = Enum.Font.GothamBlack
		label.Text = brick.text.text
		label.TextScaled = true
		label.TextColor3 = brick.text.color or Color3.new(1, 1, 1)
		label.TextStrokeTransparency = 0.2
		label.Parent = gui
		gui.Parent = part
	end
	return part
end

-- Модель из кирпичей сразу. Точка опоры — начало координат кирпичей (pivot).
function FloorBuilder.Build(name: string, bricks: { Brick }, pivot: CFrame, opts: Options?): Model
	local model = Instance.new("Model")
	model.Name = name
	for _, brick in bricks do
		local part = FloorBuilder.MakePart(brick, opts)
		if part then
			part.CFrame = pivot * brick.cframe
			part.Parent = model
		end
	end
	model.WorldPivot = pivot
	return model
end

-- Модель из кирпичей частями: не больше perFrame деталей за кадр (клиент). cancelled() — прервать (этаж удалён).
-- Возвращает модель (не в мире) или nil, если прервано. Вызывать в своём потоке (ждёт кадры).
function FloorBuilder.BuildChunked(
	name: string,
	bricks: { Brick },
	pivot: CFrame,
	opts: Options?,
	perFrame: number,
	cancelled: (() -> boolean)?
): Model?
	local model = Instance.new("Model")
	model.Name = name
	local made = 0
	for _, brick in bricks do
		if cancelled and cancelled() then
			model:Destroy()
			return nil
		end
		local part = FloorBuilder.MakePart(brick, opts)
		if part then
			part.CFrame = pivot * brick.cframe
			part.Parent = model
		end
		made += 1
		if made % perFrame == 0 then
			RunService.Heartbeat:Wait()
		end
	end
	model.WorldPivot = pivot
	return model
end

return FloorBuilder

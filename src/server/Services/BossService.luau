-- Боссы на карте (D40, D42): модель из частей на Motor6D (скелет Config/Boss<N>…Rig, меши и карты Config/BossModels) на
-- своём месте в центре зоны (MapLayout.BossSpot), лицом ко входу. Движение — физикой: невидимый корень с
-- AlignPosition и AlignOrientation, владелец — сервер, поэтому все клиенты видят плавное движение. Состояние для
-- анимаций — атрибуты модели: State и StateAt (время сервера начала), FromState и FromAt (прошлое состояние и его
-- начало), Moving и MovingAt (когда начал или перестал идти — шаг в анимации включается и гаснет плавно),
-- AttackSeq/AttackKind/AttackAt, HitSeq/HitAt, HP/MaxHP. Анимации считает каждый клиент (Shared/BossAnim, Controllers/BossAnimController).
-- Пока меш части не загружен (импорт FBX), часть — блок цвета скелета; у Крысиного короля — Part-версия по
-- утверждённой модели D54 (Config/Boss3RatKingParts: невидимый сустав части и её детали на сварке, позы те же).
-- Босс 4 «Сфинкс-лежебока» играет клипы (Config/Boss4SphinxRig, Shared/BossClips) и получает план атаки — атрибуты
-- PlanKind/PlanAt/PlanSeq/PlanCancelAt и AttackPlanAt (пишет BattleService через Plan, CancelPlan, Attack). Закрытый босс
-- (Battle.Bosses[N].Closed — коллекции ещё нет) строится только в Studio с DevMode: тесты и проверки.
-- Босс 10 «Король-дракон» (этап B интеграции): скелет и клипы Config/Boss10DragonRig, закрыт; поворот на месте не быстрее
-- Battle.Bosses[10].TurnRate °/с (AlignOrientation.MaxAngularVelocity — у остальных без ограничения, как раньше); залп —
-- атрибуты VolleySeq/VolleyAt (начало клипа), VolleyLockAt/VolleyDir (фиксация, центральное направление),
-- VolleyFireAt, VolleyOrigin, VolleyEndL/C/R (конец снаряда) и VolleyCancelAt — пишет BattleService (Volley…).
-- Босс 5 «Йети-коллекционер» (D64): скелет и клипы Config/Boss5YetiRig, закрыт до выпуска (D64 п. 7); глыба — его
-- части (во сне стоит рядом, при пробуждении — на спине: это клипы); лёд глыбы прозрачный (rig.Transparent), линза
-- монокля (rig.Eyes, часть Lens) — Neon, гаснет во сне по каналу клипа (клиент). Дальность удара — до контура тела.
-- Этап C: настоящие меши и карты дракона (6 групп). Добавочные меши rig.Extras (Body_2 — правая половина корпуса,
-- EyeL/R — глаза, цвет глаз меняет клиент по каналу клипа) приварены к своему суставу. Перепонки rig.MembraneMesh —
-- skinned MeshPart на сварке к корпусу; их кости (Bone с именами суставов, покой — из импорта) сидят на частях своих
-- суставов: Motor6D двигает часть, кость едет с ней, перепонка гнётся как в Blender. Пока закрыт, дракон стоит на
-- временной площадке сбоку от карты (MapLayout.TestArenas, World/Models/TestArena) — только в Studio с DevMode и на
-- тестовом сервере владельца (Util/OwnerTest).
-- Карты — копии шаблонов Server/Looks
-- (Boss<N>_<группа>, создаёт Rojo: игровой скрипт карты SurfaceAppearance задать не может). Сейчас модели есть у
-- боссов 1 (пёс), 2 (торговец), 3 (Крысиный король, D55) и 4 (Сфинкс, закрыт до коллекции); у остальных зон боя нет.
-- Бой и последовательность состояний ведёт BattleService. Зависит от AssetService, CollectionService, Config,
-- World/MapLayout, World/Models/TestArena, Util/OwnerTest, Util/Log.

local AssetService = game:GetService("AssetService")
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")

local Battle = require(ReplicatedStorage.Shared.Config.Battle)
local Boss1DogRig = require(ReplicatedStorage.Shared.Config.Boss1DogRig)
local Boss2TraderRig = require(ReplicatedStorage.Shared.Config.Boss2TraderRig)
local Boss3RatKingParts = require(ReplicatedStorage.Shared.Config.Boss3RatKingParts)
local Boss3RatKingRig = require(ReplicatedStorage.Shared.Config.Boss3RatKingRig)
local Boss4SphinxRig = require(ReplicatedStorage.Shared.Config.Boss4SphinxRig)
local Boss5YetiRig = require(ReplicatedStorage.Shared.Config.Boss5YetiRig)
local Boss10DragonRig = require(ReplicatedStorage.Shared.Config.Boss10DragonRig)
local BossModels = require(ReplicatedStorage.Shared.Config.BossModels)
local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Server = ServerScriptService.Server
local Log = require(Server.Util.Log)
local Looks = Server.Looks
local MapLayout = require(Server.World.MapLayout)
local TestArena = require(Server.World.Models.TestArena)
local OwnerTest = require(Server.Util.OwnerTest)

export type Boss = {
	zone: number,
	model: Model,
	root: BasePart,
	home: CFrame,
	align: AlignPosition,
	orient: AlignOrientation,
	target: Vector3, -- куда идёт
	state: string,
}

local TAG = "Boss"
local RIGS = { -- 3 — D55 (D54)
	[1] = Boss1DogRig,
	[2] = Boss2TraderRig,
	[3] = Boss3RatKingRig,
	[4] = Boss4SphinxRig,
	[5] = Boss5YetiRig,
	[10] = Boss10DragonRig,
}
-- Part-версия по утверждённой модели (пока меши не загружены): детали каждой части. Без неё — блок по габариту части.
local PART_BLOCKS: { [number]: { [string]: { any } } } = { [3] = Boss3RatKingParts }
local BLOCK_NAME = "Block"

local bosses: { [number]: Boss } = {}

local BossService = {}

local function now(): number
	return workspace:GetServerTimeNow()
end

-- Часть скелета: меш из импорта с картами D39 или блок-заготовка того же размера и цвета.
local function makePart(zone: number, cfg: BossModels.BossModel, name: string, info: any): BasePart
	local meshId = cfg.meshes[name]
	local part: BasePart
	if meshId then
		local ok, result = pcall(function()
			return AssetService:CreateMeshPartAsync(Content.fromUri(meshId))
		end)
		if ok and result then
			local mesh = result :: MeshPart
			mesh.Size = info.size
			mesh.Material = Enum.Material.SmoothPlastic
			local rig = RIGS[zone]
			if info.eye then
				-- линза Йети (rig.Eyes): без карт, Neon открытого цвета — гаснет по каналу клипа (клиент)
				mesh.Material = Enum.Material.Neon
				mesh.Color = Color3.fromHex(rig.Eyes.Open)
				mesh.CastShadow = false
			else
				-- основа — средний цвет части: если карты SurfaceAppearance не отрисуются (в Studio бывает, этап C.2),
				-- часть будет своего цвета, а не серой; при картах цвет основы не виден
				if info.color then
					mesh.Color = Color3.fromHex(info.color)
				end
				local look = Looks:FindFirstChild(("Boss%d_%s"):format(zone, info.map))
				if look then
					look:Clone().Parent = mesh
				else
					Log.Warn("BossService", ("Нет шаблона карт Looks/Boss%d_%s"):format(zone, info.map))
				end
			end
			-- прозрачная часть (rig.Transparent — лёд глыбы Йети): экспонаты внутри видны
			local transparent = rig.Transparent and rig.Transparent[name]
			if transparent then
				mesh.Transparency = transparent
			end
			part = mesh
		else
			Log.Warn(
				"BossService",
				("Меш части %s не загрузился: %s"):format(name, tostring(result))
			)
		end
	end
	if not part then
		part = Instance.new("Part")
		part.Size = info.size
		part.Color = Color3.fromHex(info.color)
		part.TopSurface = Enum.SurfaceType.Smooth
		part.BottomSurface = Enum.SurfaceType.Smooth
		local blocks = PART_BLOCKS[zone] and PART_BLOCKS[zone][name]
		if blocks and #blocks > 0 then
			-- Part-версия: сама часть — невидимый сустав по габариту, видимое — её детали на сварке
			part.Transparency = 1
			part.CastShadow = false
			local toPart = (CFrame.new(info.center) * CFrame.Angles(0, math.rad(cfg.turn), 0)):Inverse()
			for _, spec in blocks do
				local block = Instance.new("Part")
				block.Name = BLOCK_NAME
				block.Size = spec[2]
				block.Color = Color3.fromHex(spec[3])
				block.Material = Enum.Material.Plastic
				block.TopSurface = Enum.SurfaceType.Smooth
				block.BottomSurface = Enum.SurfaceType.Smooth
				block.Anchored = false
				block.Massless = true
				block.CanCollide = false
				block.CanQuery = false
				block.CanTouch = false
				local p, r = spec[1], spec[4]
				local offset = if r then CFrame.new(p.X, p.Y, p.Z, table.unpack(r)) else CFrame.new(p)
				local weld = Instance.new("Weld")
				weld.Part0 = part
				weld.Part1 = block
				weld.C0 = toPart * offset -- от точки вращения части (оси модели) к её центру с поворотом меша
				weld.Parent = block
				block.Parent = part
			end
		end
	end
	part.Name = name
	part.Anchored = false
	part.Massless = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	return part
end

-- Добавочный меш (rig.Extras: половина корпуса или глаз) или перепонки (rig.MembraneMesh): MeshPart из импорта; нет
-- меша — nil (тогда видна только основная часть). Глаз — Neon цвета открытого глаза (дальше цвет ведёт клиент).
local function extraMesh(zone: number, cfg: BossModels.BossModel, rig: any, name: string, info: any): MeshPart?
	local meshId = cfg.meshes[name]
	if not meshId then
		return nil
	end
	local ok, result = pcall(function()
		return AssetService:CreateMeshPartAsync(Content.fromUri(meshId))
	end)
	if not ok or not result then
		Log.Warn("BossService", ("Меш %s не загрузился: %s"):format(name, tostring(result)))
		return nil
	end
	local mesh = result :: MeshPart
	mesh.Name = name
	mesh.Size = info.size
	if info.eye then
		mesh.Material = Enum.Material.Neon
		mesh.Color = Color3.fromHex(rig.Eyes.Open)
		mesh.CastShadow = false
	else
		mesh.Material = Enum.Material.SmoothPlastic
		-- основа — цвет сустава (как у makePart): без карт часть не серая
		local joint = info.joint and rig.Parts[info.joint]
		local base = info.color or (joint and joint.color)
		if base then
			mesh.Color = Color3.fromHex(base)
		end
		local look = Looks:FindFirstChild(("Boss%d_%s"):format(zone, info.map))
		if look then
			look:Clone().Parent = mesh
		else
			Log.Warn("BossService", ("Нет шаблона карт Looks/Boss%d_%s"):format(zone, info.map))
		end
	end
	mesh.Anchored = false
	mesh.Massless = true
	mesh.CanCollide = false
	mesh.CanQuery = false
	mesh.CanTouch = false
	return mesh
end

-- Сварка mesh к части сустава part: offset — от рамки части к рамке меша (оба от одной точки вращения сустава).
local function weldTo(part: BasePart, mesh: BasePart, offset: CFrame)
	mesh.CFrame = part.CFrame * offset
	local weld = Instance.new("Weld")
	weld.Part0 = part
	weld.Part1 = mesh
	weld.C0 = offset
	weld.Parent = mesh
end

-- Модель босса зоны zone в позе покоя на месте home (лицо модели — +Z).
local function build(zone: number, home: CFrame, parent: Instance): Boss
	local rig = RIGS[zone]
	local cfg = BossModels[zone] :: BossModels.BossModel
	local meshTurn = CFrame.Angles(0, math.rad(cfg.turn), 0)
	local model = Instance.new("Model")
	model.Name = ("Boss%d"):format(zone)

	local root = Instance.new("Part")
	root.Name = "Root"
	root.Size = Vector3.new(4, 1, 6)
	root.Transparency = 1
	root.CanCollide = false
	root.CanQuery = false
	root.CanTouch = false
	root.CFrame = home
	root.Parent = model
	local attachment = Instance.new("Attachment")
	attachment.Name = "Align"
	attachment.Parent = root

	-- Части параллельно (меши грузятся по сети), затем суставы.
	local parts: { [string]: BasePart } = {}
	local pending = #rig.Order
	for _, name in rig.Order do
		task.spawn(function()
			parts[name] = makePart(zone, cfg, name, rig.Parts[name])
			pending -= 1
		end)
	end
	while pending > 0 do
		task.wait()
	end
	for _, name in rig.Order do
		local info = rig.Parts[name]
		local part = parts[name]
		part.CFrame = home * CFrame.new(info.pivot) * CFrame.new(info.center) * meshTurn
		part.Parent = model
		local joint = Instance.new("Motor6D")
		joint.Name = name
		joint.C1 = (CFrame.new(info.center) * meshTurn):Inverse()
		if info.parent then
			local parentInfo = rig.Parts[info.parent]
			joint.Part0 = parts[info.parent]
			joint.C0 = (CFrame.new(parentInfo.center) * meshTurn):Inverse() * CFrame.new(info.pivot - parentInfo.pivot)
		else
			joint.Part0 = root
			joint.C0 = CFrame.new(info.pivot)
		end
		joint.Part1 = part
		joint.Parent = part
	end

	-- добавочные меши и перепонки (этап C): параллельно, как части; ставятся в покое — до первого кадра анимации
	local extras: { [string]: MeshPart } = {}
	local wanted = table.clone(rig.Extras or {})
	local membrane = rig.MembraneMesh
	if membrane then
		wanted[membrane.name] = membrane
	end
	local waiting = 0
	for name, info in wanted do
		waiting += 1
		task.spawn(function()
			extras[name] = extraMesh(zone, cfg, rig, name, info) :: any
			waiting -= 1
		end)
	end
	while waiting > 0 do
		task.wait()
	end
	for name, extra in rig.Extras or {} do
		local mesh = extras[name]
		local info = rig.Parts[extra.joint]
		if mesh then
			weldTo(
				parts[extra.joint],
				mesh,
				(CFrame.new(info.center) * meshTurn):Inverse() * CFrame.new(extra.center) * meshTurn
			)
			mesh.Parent = model
		end
	end
	local wings = membrane and extras[membrane.name]
	if membrane and wings then
		local body = parts.Body
		weldTo(body, wings, body.CFrame:Inverse() * home * CFrame.new(membrane.center) * meshTurn)
		wings.Parent = model
		for name, bone in membrane.bones do
			local holder = parts[name] or root -- кость Root (без весов) — на корне модели
			local b = Instance.new("Bone")
			b.Name = name
			b.CFrame = holder.CFrame:Inverse() * wings.CFrame * bone.cframe
			b.Parent = holder
		end
	end

	local align = Instance.new("AlignPosition")
	align.Mode = Enum.PositionAlignmentMode.OneAttachment
	align.Attachment0 = attachment
	align.MaxForce = math.huge
	align.Responsiveness = 30
	align.MaxVelocity = Battle.Bosses[zone].Speed
	align.Position = home.Position
	align.Parent = root
	local orient = Instance.new("AlignOrientation")
	orient.Mode = Enum.OrientationAlignmentMode.OneAttachment
	orient.Attachment0 = attachment
	orient.MaxTorque = math.huge
	orient.Responsiveness = 25
	local turnRate = Battle.Bosses[zone].TurnRate
	if turnRate then
		orient.MaxAngularVelocity = math.rad(turnRate) -- большой босс поворачивается на месте шагом, не рывком
	end
	orient.CFrame = home.Rotation
	orient.Parent = root

	model.PrimaryPart = root
	model:SetAttribute("Zone", zone)
	model:SetAttribute("BossName", cfg.name)
	model:SetAttribute("State", "Sleep")
	model:SetAttribute("StateAt", now())
	model:SetAttribute("Moving", false)
	model:SetAttribute("MovingAt", now())
	model:SetAttribute("AttackSeq", 0)
	model:SetAttribute("HitSeq", 0)
	model.Parent = parent
	CollectionService:AddTag(model, TAG)
	if RunService:IsRunning() then
		root:SetNetworkOwner(nil) -- сервер двигает босса, клиенты видят движение плавным
	end
	return {
		zone = zone,
		model = model,
		root = root,
		home = home,
		align = align,
		orient = orient,
		target = home.Position,
		state = "Sleep",
	}
end

-- Личный босс (D55, учебный пёс): та же модель и анимации (атрибуты, тег), но не на карте боссов — бой по сценарию
-- ведёт TutorialService. Видит только ученик (атрибут TutorialOwner — остальные клиенты прячут).
function BossService.BuildPersonal(zone: number, home: CFrame, parent: Instance): Boss
	return build(zone, home, parent)
end

-- Рост босса стоя (от земли до макушки по габаритам частей скелета), стадов: над ним — полоска HP.
function BossService.Height(boss: Boss): number
	local top = 0
	for _, info in RIGS[boss.zone].Parts do
		top = math.max(top, info.pivot.Y + info.center.Y + info.size.Y / 2)
	end
	return top
end

-- Место босса зоны: центр зоны (на полу площадки, если он приподнят), лицом ко входу (лицо модели +Z → мировая +Z).
function BossService.HomeOf(zone: number): CFrame
	local frame = MapLayout.ZoneCFrame(zone)
	local spot = MapLayout.BossSpot
	local arena = MapLayout.Arenas[zone]
	-- у площадки с приподнятым полом (Arenas[N].floor, зона 4) босс стоит и ходит на её верху
	local position = (frame * CFrame.new(spot.X, if arena and arena.floor then arena.floor else 0, spot.Y)).Position
	local test = MapLayout.TestArenas[zone]
	if test and Battle.Bosses[zone].Closed and BossService.ClosedAllowed() then
		-- закрытый босс (Studio, тестовый сервер владельца) — на временной площадке сбоку от карты, в полосе z своей зоны (D49 держит по z)
		return CFrame.new(test.x, 0, position.Z)
	end
	return CFrame.new(position)
end

function BossService.Init(world: Instance)
	local folder = Instance.new("Folder")
	folder.Name = "Bosses"
	folder.Parent = world
	for zone in RIGS do
		if not GameConfig.Throw.OldLoop then
			continue -- D75: старый цикл выключен — боссов на карте нет (боссы — награды броска)
		end
		if Battle.Bosses[zone].Closed and not BossService.ClosedAllowed() then
			continue -- коллекции ещё нет: в опубликованной игре босса нет
		end
		local home = BossService.HomeOf(zone)
		local test = MapLayout.TestArenas[zone]
		if test and Battle.Bosses[zone].Closed then
			TestArena.Build(("TestArena%d"):format(zone), home.Position, test.size, folder)
		end
		bosses[zone] = build(zone, home, folder)
	end
	RunService.Heartbeat:Connect(function()
		for _, boss in bosses do
			local moving = (Vector3.new(boss.target.X, 0, boss.target.Z) - Vector3.new(
				boss.root.Position.X,
				0,
				boss.root.Position.Z
			)).Magnitude > 0.6
			if boss.model:GetAttribute("Moving") ~= moving then
				boss.model:SetAttribute("Moving", moving)
				boss.model:SetAttribute("MovingAt", now())
			end
		end
	end)
	Log.Debug("BossService", ("Боссов на карте: %d"):format(#bosses))
end

-- Закрытые боссы (Battle.Bosses[N].Closed) есть только в Studio с DevMode и на тестовом сервере владельца
-- (Util/OwnerTest: резервный сервер подтверждённого DEV-места, профили в памяти).
function BossService.ClosedAllowed(): boolean
	return (RunService:IsStudio() and GameConfig.DevMode == true) or OwnerTest.IsTestServer()
end

-- Босс зоны (nil — у зоны пока нет модели и боя).
function BossService.Get(zone: number): Boss?
	return bosses[zone]
end

function BossService.SetState(boss: Boss, state: string)
	-- прошлое состояние и его начало — анимация продолжит с позы, где застали (разбудили, пока засыпал)
	boss.model:SetAttribute("FromState", boss.state)
	boss.model:SetAttribute("FromAt", boss.model:GetAttribute("StateAt"))
	boss.state = state
	boss.model:SetAttribute("State", state)
	boss.model:SetAttribute("StateAt", now())
end

-- Идти к точке (по земле, со скоростью speed стадов в секунду).
function BossService.MoveTo(boss: Boss, position: Vector3, speed: number?)
	boss.target = Vector3.new(position.X, boss.home.Y, position.Z)
	boss.align.MaxVelocity = speed or Battle.Bosses[boss.zone].Speed
	boss.align.Position = boss.target
end

-- Остановиться там, где стоит.
function BossService.Stop(boss: Boss)
	BossService.MoveTo(boss, boss.root.Position)
end

-- Повернуться лицом к точке.
function BossService.Face(boss: Boss, position: Vector3)
	local from = boss.root.Position
	local flat = Vector3.new(position.X, from.Y, position.Z)
	if (flat - from).Magnitude < 0.05 then
		return
	end
	-- lookAt смотрит −Z в цель, лицо модели — +Z: разворот на 180°.
	boss.orient.CFrame = CFrame.lookAt(from, flat).Rotation * CFrame.Angles(0, math.pi, 0)
end

-- Держать нынешнее направление (залп босса 10: цель поворота — куда смотрит сейчас, иначе он доворачивал бы к прежней
-- цели посреди клипа — круг скипетра уезжал бы, лапы скользили без шага).
function BossService.HoldFacing(boss: Boss)
	BossService.Face(boss, boss.root.Position + boss.root.CFrame.ZVector * 10)
end

-- Лицом ко входу, как на месте.
function BossService.FaceHome(boss: Boss)
	boss.orient.CFrame = boss.home.Rotation
end

function BossService.Position(boss: Boss): Vector3
	return boss.root.Position
end

-- Идёт ли босс (как атрибут Moving: до цели больше 0.6 стада; считается в Heartbeat).
function BossService.IsMoving(boss: Boss): boolean
	return boss.model:GetAttribute("Moving") == true
end

-- Расстояние по земле до места босса.
function BossService.DistanceHome(boss: Boss): number
	local p, h = boss.root.Position, boss.home.Position
	return Vector3.new(p.X - h.X, 0, p.Z - h.Z).Magnitude
end

-- Играет ли босс клипы (тогда ему нужен план атаки).
function BossService.HasClips(boss: Boss): boolean
	return RIGS[boss.zone].Clips ~= nil
end

-- Выпад (анимация укуса или удара лапой). plannedAt — у босса с клипами: время из плана этого выпада (nil — без
-- плана); клиент ведёт клип от него, чтобы замах и удар шли одним движением.
function BossService.Attack(boss: Boss, kind: string, plannedAt: number?)
	if BossService.HasClips(boss) then
		boss.model:SetAttribute("AttackPlanAt", plannedAt) -- до AttackSeq: номер выпада — последним
	end
	boss.model:SetAttribute("AttackKind", kind)
	boss.model:SetAttribute("AttackAt", now())
	boss.model:SetAttribute("AttackSeq", (boss.model:GetAttribute("AttackSeq") or 0) + 1)
end

-- План следующего выпада (только у босса с клипами): вид, время сервера и номер — следующий после AttackSeq.
function BossService.Plan(boss: Boss, kind: string, at: number)
	if not BossService.HasClips(boss) then
		return
	end
	boss.model:SetAttribute("PlanKind", kind)
	boss.model:SetAttribute("PlanAt", at)
	boss.model:SetAttribute("PlanSeq", (boss.model:GetAttribute("AttackSeq") or 0) + 1)
	boss.model:SetAttribute("PlanCancelAt", nil)
end

-- Отмена плана (игрок вне дальности, бой кончился): начатый замах у клиентов гаснет.
function BossService.CancelPlan(boss: Boss)
	if BossService.HasClips(boss) and boss.model:GetAttribute("PlanAt") ~= nil then
		boss.model:SetAttribute("PlanCancelAt", now())
	end
end

-- Попадание по боссу (анимация реакции).
function BossService.Hit(boss: Boss)
	boss.model:SetAttribute("HitAt", now())
	boss.model:SetAttribute("HitSeq", (boss.model:GetAttribute("HitSeq") or 0) + 1)
end

-- Скелет босса (Config/Boss<N>…Rig).
function BossService.Rig(boss: Boss): any
	return RIGS[boss.zone]
end

-- Залп (босс 10): начало клипа залпа (время сервера at) и центр магического круга. Номер — последним: клиенты
-- начинают новый залп, когда остальное уже на месте.
function BossService.Volley(boss: Boss, at: number, origin: Vector3)
	local model = boss.model
	model:SetAttribute("VolleyAt", at)
	model:SetAttribute("VolleyOrigin", origin)
	model:SetAttribute("VolleyLockAt", nil)
	model:SetAttribute("VolleyDir", nil)
	model:SetAttribute("VolleyFireAt", nil)
	model:SetAttribute("VolleyCancelAt", nil)
	for _, side in { "L", "C", "R" } do
		model:SetAttribute("VolleyEnd" .. side, nil)
	end
	model:SetAttribute("VolleySeq", (model:GetAttribute("VolleySeq") or 0) + 1)
end

-- Направление зафиксировано: центральное направление dir (время сервера at).
function BossService.VolleyLock(boss: Boss, dir: Vector3, at: number)
	boss.model:SetAttribute("VolleyDir", dir)
	boss.model:SetAttribute("VolleyLockAt", at)
end

-- Выстрел (время сервера at).
function BossService.VolleyFire(boss: Boss, at: number)
	boss.model:SetAttribute("VolleyFireAt", at)
end

-- Снаряд стороны side (−1, 0, 1) кончился в момент at (время сервера): попал, о землю, о препятствие или на дальности.
function BossService.VolleyEnd(boss: Boss, side: number, at: number)
	boss.model:SetAttribute("VolleyEnd" .. (if side < 0 then "L" elseif side > 0 then "R" else "C"), at)
end

-- Залп отменён (бой кончился, боец пропал): предупреждения и снаряды у клиентов исчезают.
function BossService.CancelVolley(boss: Boss)
	if boss.model:GetAttribute("VolleyAt") ~= nil then
		boss.model:SetAttribute("VolleyCancelAt", now())
	end
end

-- Для тестов: мгновенно поставить босса на место (без физики).
function BossService.SnapHome(boss: Boss)
	BossService.MoveTo(boss, boss.home.Position)
	boss.model:PivotTo(boss.home)
	BossService.FaceHome(boss)
end

return BossService

-- Боссы на карте (D40, D42): модель из частей на Motor6D (скелет Config/Boss<N>…Rig, меши и карты Config/BossModels) на
-- своём месте в центре зоны (MapLayout.BossSpot), лицом ко входу. Движение — физикой: невидимый корень с
-- AlignPosition и AlignOrientation, владелец — сервер, поэтому все клиенты видят плавное движение. Состояние для
-- анимаций — атрибуты модели: State и StateAt (время сервера начала), Moving, AttackSeq/AttackKind/AttackAt,
-- HitSeq/HitAt, HP/MaxHP. Анимации считает каждый клиент (Shared/BossAnim, Controllers/BossAnimController).
-- Пока меш части не загружен (импорт FBX), часть — блок цвета скелета; у Крысиного короля — Part-версия по
-- утверждённой модели D54 (Config/Boss3RatKingParts: невидимый сустав части и её детали на сварке, позы те же).
-- Карты — копии шаблонов Server/Looks
-- (Boss<N>_<группа>, создаёт Rojo: игровой скрипт карты SurfaceAppearance задать не может). Сейчас модели есть у
-- боссов 1 (пёс), 2 (торговец) и 3 (Крысиный король, D55); у остальных зон боя нет.
-- Бой и последовательность состояний ведёт BattleService. Зависит от AssetService, CollectionService, Config,
-- World/MapLayout, Util/Log.

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
local BossModels = require(ReplicatedStorage.Shared.Config.BossModels)
local Server = ServerScriptService.Server
local Log = require(Server.Util.Log)
local Looks = Server.Looks
local MapLayout = require(Server.World.MapLayout)

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
local RIGS = { [1] = Boss1DogRig, [2] = Boss2TraderRig, [3] = Boss3RatKingRig } -- 3 — D55 (D54)
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
			local look = Looks:FindFirstChild(("Boss%d_%s"):format(zone, info.map))
			if look then
				look:Clone().Parent = mesh
			else
				Log.Warn("BossService", ("Нет шаблона карт Looks/Boss%d_%s"):format(zone, info.map))
			end
			part = mesh
		else
			Log.Warn("BossService", ("Меш части %s не загрузился: %s"):format(name, tostring(result)))
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
	orient.CFrame = home.Rotation
	orient.Parent = root

	model.PrimaryPart = root
	model:SetAttribute("Zone", zone)
	model:SetAttribute("BossName", cfg.name)
	model:SetAttribute("State", "Sleep")
	model:SetAttribute("StateAt", now())
	model:SetAttribute("Moving", false)
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

-- Место босса зоны: центр зоны, лицом ко входу (лицо модели +Z → мировая +Z).
function BossService.HomeOf(zone: number): CFrame
	local frame = MapLayout.ZoneCFrame(zone)
	local spot = MapLayout.BossSpot
	local position = (frame * CFrame.new(spot.X, 0, spot.Y)).Position
	return CFrame.new(position)
end

function BossService.Init(world: Instance)
	local folder = Instance.new("Folder")
	folder.Name = "Bosses"
	folder.Parent = world
	for zone in RIGS do
		bosses[zone] = build(zone, BossService.HomeOf(zone), folder)
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
			end
		end
	end)
	Log.Debug("BossService", ("Боссов на карте: %d"):format(#bosses))
end

-- Босс зоны (nil — у зоны пока нет модели и боя).
function BossService.Get(zone: number): Boss?
	return bosses[zone]
end

function BossService.SetState(boss: Boss, state: string)
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

-- Лицом ко входу, как на месте.
function BossService.FaceHome(boss: Boss)
	boss.orient.CFrame = boss.home.Rotation
end

function BossService.Position(boss: Boss): Vector3
	return boss.root.Position
end

-- Расстояние по земле до места босса.
function BossService.DistanceHome(boss: Boss): number
	local p, h = boss.root.Position, boss.home.Position
	return Vector3.new(p.X - h.X, 0, p.Z - h.Z).Magnitude
end

-- Выпад (анимация укуса или удара лапой).
function BossService.Attack(boss: Boss, kind: string)
	boss.model:SetAttribute("AttackKind", kind)
	boss.model:SetAttribute("AttackAt", now())
	boss.model:SetAttribute("AttackSeq", (boss.model:GetAttribute("AttackSeq") or 0) + 1)
end

-- Попадание по боссу (анимация реакции).
function BossService.Hit(boss: Boss)
	boss.model:SetAttribute("HitAt", now())
	boss.model:SetAttribute("HitSeq", (boss.model:GetAttribute("HitSeq") or 0) + 1)
end

-- Для тестов: мгновенно поставить босса на место (без физики).
function BossService.SnapHome(boss: Boss)
	BossService.MoveTo(boss, boss.home.Position)
	boss.model:PivotTo(boss.home)
	BossService.FaceHome(boss)
end

return BossService

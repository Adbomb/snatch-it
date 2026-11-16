-- Анимации боссов на клиенте (D18, D40): у каждой модели с тегом Boss каждый кадр ставит Transform суставов
-- (Motor6D) по состоянию с сервера — атрибуты State/StateAt, FromState/FromAt, Moving/MovingAt, AttackKind/AttackAt, HitAt — через
-- Shared/BossAnim. Все клиенты считают одинаково, поэтому анимации видны всем игрокам, а по сети идут только
-- атрибуты. Спящий босс выпускает «Z z z». У босса 4 (клипы, Shared/BossClips) ещё и план атаки — PlanKind, PlanAt,
-- PlanSeq, PlanCancelAt, AttackPlanAt; его анимации не считаются, когда он вне кадра и не рядом (боссы 1–3 — как раньше).
-- Босс 10 «Король-дракон» (этап B): тот же путь клипов; модель поворачивается на месте (сервер ограничивает скорость) —
-- здесь по пройденному углу считается шаг на месте (rig.Turn: turnDir, turnT, turnWeight для BossClips), лапы не
-- скользят; большой босс считается дальше (NEAR_BIG). Этап C: кости перепонок (skinned mesh) сидят на частях своих
-- суставов (BossService) — их двигает тот же Motor6D, здесь их не трогают; глаза (rig.Eyes) — цвет по каналу клипа.
-- Зависит от Shared/BossAnim, Shared/BossClips, Config/Boss1DogRig, Config/Boss2TraderRig, Config/Boss3RatKingRig (D55), Config/Boss4SphinxRig,
-- Config/Boss10DragonRig, Shared/PoseFade (этап C.2: разрыв позы при смене источника — план → залп в одном шаге
-- сервера, возврат в кадр — сглаживается только у скелета с rig.Fade, у дракона).

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local BossAnim = require(Shared:WaitForChild("BossAnim"))
local BossClips = require(Shared:WaitForChild("BossClips"))
local PoseFade = require(Shared:WaitForChild("PoseFade"))
local Boss1DogRig = require(Shared:WaitForChild("Config"):WaitForChild("Boss1DogRig"))
local Boss2TraderRig = require(Shared:WaitForChild("Config"):WaitForChild("Boss2TraderRig"))
local Boss3RatKingRig = require(Shared:WaitForChild("Config"):WaitForChild("Boss3RatKingRig"))
local Boss4SphinxRig = require(Shared:WaitForChild("Config"):WaitForChild("Boss4SphinxRig"))
local Boss10DragonRig = require(Shared:WaitForChild("Config"):WaitForChild("Boss10DragonRig"))

local RIGS =
	{ [1] = Boss1DogRig, [2] = Boss2TraderRig, [3] = Boss3RatKingRig, [4] = Boss4SphinxRig, [10] = Boss10DragonRig }
local TAG = "Boss"
local MAX_DISTANCE = 220 -- дальше анимации не считаются (экономия на телефонах)
-- Босс с клипами вне кадра и дальше NEAR не считается; рамка кадра расширена на MARGIN (босс большой).
local NEAR, MARGIN = 40, 0.25
local NEAR_BIG = 80 -- у босса с шагом на месте (rig.Turn — дракон, ~30 стадов от центра до кончика хвоста)
local TURN_MIN = 4 -- °/с: медленнее — модель стоит, шага нет
local TURN_FADE = 0.25 -- с: шаг на месте набирает силу и гаснет

type Turn = { yaw: number?, acc: number, dir: number, weight: number }
type Tracked = {
	model: Model,
	rig: any,
	joints: { [string]: Motor6D },
	turn: Turn?,
	zzz: BillboardGui?,
	eyeValue: number?, -- последнее значение глаз (rig.Eyes), уже показанное
	fade: any, -- Shared/PoseFade: разрыв позы при смене источника (только rig.Fade — дракон)
}

local tracked: { [Model]: Tracked } = {}

local BossAnimController = {}

local function zzzLabel(model: Model): BillboardGui?
	local head = model:FindFirstChild("Head")
	if not head or not head:IsA("BasePart") then
		return nil
	end
	local gui = Instance.new("BillboardGui")
	gui.Name = "Zzz"
	gui.Size = UDim2.fromOffset(90, 60)
	gui.StudsOffsetWorldSpace = Vector3.new(0, 4.5, 0)
	gui.MaxDistance = 90
	gui.Adornee = head
	local text = Instance.new("TextLabel")
	text.Name = "Text"
	text.Size = UDim2.fromScale(1, 1)
	text.BackgroundTransparency = 1
	text.Font = Enum.Font.GothamBlack
	text.TextScaled = true
	text.TextColor3 = Color3.fromHex("DDEBFF")
	text.TextStrokeTransparency = 0.3
	text.Text = "Z z z"
	text.Parent = gui
	gui.Parent = head
	return gui
end

-- Глаза (rig.Eyes, отдельные меши у головы): цвет закрытого → открытого по каналу клипа, открытые — Neon (горят, как
-- в Blender); свойства меняются только при смене значения (шаг 0.05).
local function applyEyes(entry: Tracked, model: Model, value: number)
	local q = math.floor(math.clamp(value, 0, 1) * 20 + 0.5) / 20
	if entry.eyeValue == q then
		return
	end
	local cfg = entry.rig.Eyes
	local color = Color3.fromHex(cfg.Closed):Lerp(Color3.fromHex(cfg.Open), q)
	local material = if q >= 0.5 then Enum.Material.Neon else Enum.Material.SmoothPlastic
	local found = 0
	for _, name in cfg.Parts do
		local part = model:FindFirstChild(name, true)
		if part and part:IsA("BasePart") then
			part.Color = color
			part.Material = material
			found += 1
		end
	end
	if found == #cfg.Parts then
		entry.eyeValue = q -- глаза ещё не пришли (стриминг) — попробовать в следующем кадре
	end
end

-- Шаг на месте: по повороту корня за кадр — направление, пройденный угол (время в клипе шага) и сила.
local function turnInput(entry: Tracked, root: BasePart, dt: number): (number?, number?, number?)
	local turn = entry.turn
	if not turn then
		return nil, nil, nil
	end
	local look = root.CFrame.ZVector -- лицо модели — +Z
	local yaw = math.deg(math.atan2(look.X, look.Z))
	local d = if turn.yaw then (yaw - turn.yaw + 540) % 360 - 180 else 0
	turn.yaw = yaw
	local rate = if dt > 0 then math.abs(d) / dt else 0
	local turning = rate > TURN_MIN
	if turning then
		turn.dir = if d > 0 then 1 else -1
		turn.acc += math.abs(d)
	end
	local step = if TURN_FADE > 0 then dt / TURN_FADE else 1
	turn.weight = math.clamp(turn.weight + (if turning then step else -step), 0, 1)
	local cfg = entry.rig.Turn
	local clip = BossClips.Get(entry.rig, if turn.dir > 0 then cfg.Left else cfg.Right)
	local t = (turn.acc % cfg.Degrees) / cfg.Degrees * clip.duration
	return turn.dir, t, turn.weight * turn.weight * (3 - 2 * turn.weight)
end

local function track(model: Model)
	local zone = model:GetAttribute("Zone")
	local rig = RIGS[zone]
	if not rig or tracked[model] then
		return
	end
	local joints = {}
	for _, name in rig.Order do
		local part = model:WaitForChild(name, 10)
		local joint = part and part:WaitForChild(name, 10)
		if joint and joint:IsA("Motor6D") then
			joints[name] = joint
		end
	end
	tracked[model] = {
		model = model,
		rig = rig,
		joints = joints,
		turn = if rig.Turn then { yaw = nil, acc = 0, dir = 1, weight = 0 } else nil,
		zzz = zzzLabel(model),
		fade = PoseFade.new(rig),
	}
	if rig.Clips then
		-- клипы разбираются заранее, по одному за кадр (≈ 40 мс на все), а не посреди боя
		for _, name in rig.Clips.Names do
			BossClips.Get(rig, name)
			task.wait()
		end
	end
end

local function since(model: Model, attribute: string): number?
	local at = model:GetAttribute(attribute)
	if type(at) ~= "number" then
		return nil
	end
	return workspace:GetServerTimeNow() - at
end

-- Сколько длилось прошлое состояние к началу нынешнего (FromAt → StateAt), секунд.
local function lasted(model: Model): number?
	local from, at = model:GetAttribute("FromAt"), model:GetAttribute("StateAt")
	if type(from) ~= "number" or type(at) ~= "number" then
		return nil
	end
	return at - from
end

-- Виден ли босс: ближе near или в кадре (с запасом по краям).
local function visible(camera: Camera, at: Vector3, near: number): boolean
	if (camera.CFrame.Position - at).Magnitude <= near then
		return true
	end
	local point, front = camera:WorldToViewportPoint(at)
	if not front then
		return false
	end
	local size = camera.ViewportSize
	return point.X > -size.X * MARGIN
		and point.X < size.X * (1 + MARGIN)
		and point.Y > -size.Y * MARGIN
		and point.Y < size.Y * (1 + MARGIN)
end

local function update(_time: number, dt: number)
	local camera = workspace.CurrentCamera
	local clock = workspace:GetServerTimeNow()
	for model, entry in tracked do
		if not model.Parent then
			tracked[model] = nil
			continue
		end
		local root = model.PrimaryPart
		if camera and root and (camera.CFrame.Position - root.Position).Magnitude > MAX_DISTANCE then
			continue
		end
		local near = if entry.rig.Turn then NEAR_BIG else NEAR
		local turnDir, turnT, turnWeight
		if root then
			turnDir, turnT, turnWeight = turnInput(entry, root, dt) -- и вне кадра: угол копится, шаг не сбивается
		end
		if entry.rig.Clips and camera and root and not visible(camera, root.Position, near) then
			continue
		end
		local state = model:GetAttribute("State") or "Sleep"
		local input = {
			state = state,
			t = since(model, "StateAt") or 0,
			moving = model:GetAttribute("Moving") == true,
			movingT = since(model, "MovingAt"),
			fromState = model:GetAttribute("FromState"),
			fromT = lasted(model),
			attackKind = model:GetAttribute("AttackKind"),
			attackT = since(model, "AttackAt"),
			hitT = since(model, "HitAt"),
			clock = clock,
			attackSeq = model:GetAttribute("AttackSeq"),
			attackPlanT = since(model, "AttackPlanAt"),
			planKind = model:GetAttribute("PlanKind"),
			planSeq = model:GetAttribute("PlanSeq"),
			planT = since(model, "PlanAt"),
			planCancelT = since(model, "PlanCancelAt"),
			turnDir = turnDir,
			turnT = turnT,
			turnWeight = turnWeight,
		}
		local pose = entry.fade:Apply(PoseFade.Key(input), BossAnim.Sample(entry.rig, input), clock)
		if entry.rig.Eyes then
			applyEyes(entry, model, BossClips.Eyes(entry.rig, input))
		end
		for name, joint in entry.joints do
			local transform = pose[name]
			if transform then
				joint.Transform = transform
			end
		end
		local zzz = entry.zzz
		if zzz then
			zzz.Enabled = state == "Sleep"
			if zzz.Enabled then
				local phase = clock % 2.4 / 2.4
				zzz.StudsOffsetWorldSpace = Vector3.new(0.6 * math.sin(phase * 6), 4.5 + 2 * phase, 0)
				local label = zzz:FindFirstChild("Text") :: TextLabel
				label.TextTransparency = phase ^ 2
			end
		end
	end
end

function BossAnimController.Init()
	CollectionService:GetInstanceAddedSignal(TAG):Connect(function(model)
		if model:IsA("Model") then
			task.spawn(track, model)
		end
	end)
	for _, model in CollectionService:GetTagged(TAG) do
		if model:IsA("Model") then
			task.spawn(track, model)
		end
	end
	-- Stepped: после анимаций движка и до физики, Transform попадает в кадр.
	RunService.Stepped:Connect(update)
end

return BossAnimController

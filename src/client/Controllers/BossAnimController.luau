-- Анимации боссов на клиенте (D18, D40): у каждой модели с тегом Boss каждый кадр ставит Transform суставов
-- (Motor6D) по состоянию с сервера — атрибуты State/StateAt, Moving, AttackSeq/AttackKind/AttackAt, HitAt — через
-- Shared/BossAnim. Все клиенты считают одинаково, поэтому анимации видны всем игрокам, а по сети идут только
-- атрибуты. Спящий пёс выпускает «Z z z». Зависит от Shared/BossAnim, Config/Boss1DogRig.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local BossAnim = require(Shared:WaitForChild("BossAnim"))
local Boss1DogRig = require(Shared:WaitForChild("Config"):WaitForChild("Boss1DogRig"))

local RIGS = { [1] = Boss1DogRig }
local TAG = "Boss"
local MAX_DISTANCE = 220 -- дальше анимации не считаются (экономия на телефонах)

type Tracked = { model: Model, rig: any, joints: { [string]: Motor6D }, zzz: BillboardGui? }

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
	tracked[model] = { model = model, rig = rig, joints = joints, zzz = zzzLabel(model) }
end

local function since(model: Model, attribute: string): number?
	local at = model:GetAttribute(attribute)
	if type(at) ~= "number" then
		return nil
	end
	return workspace:GetServerTimeNow() - at
end

local function update()
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
		local state = model:GetAttribute("State") or "Sleep"
		local pose = BossAnim.Sample(entry.rig, {
			state = state,
			t = since(model, "StateAt") or 0,
			moving = model:GetAttribute("Moving") == true,
			attackKind = model:GetAttribute("AttackKind"),
			attackT = since(model, "AttackAt"),
			hitT = since(model, "HitAt"),
			clock = clock,
		})
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

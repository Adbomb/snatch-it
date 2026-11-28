-- Поза персонажа при броске вдаль (D75): стойка у края, замах с приседом, хлёсткий бросок и доводка — кодом, без
-- загруженных анимаций. Суставы (Transform у Motor6D или AnimationConstraint) ставятся каждый шаг физики поверх обычной анимации; поза — смесь
-- ключевых поз по времени с плавными кривыми (замедление в замахе, резкий хлёст, упругая доводка). R15 — полная поза,
-- R6 — упрощённая (рука и корпус). Только у своего персонажа: другим игрокам поза не передаётся.
-- Ни от чего не зависит.

local RunService = game:GetService("RunService")

local ThrowPose = {}

type Pose = { [string]: Vector3 } -- сустав → углы (градусы) вокруг X, Y, Z; "Lift" — (вперёд, вверх, 0) корпуса

-- Оси R15 (персонаж смотрит в −Z): X+ — рука и нога вперёд, корпус назад; Y+ — поворот влево.
local R15: { [string]: Pose } = {
	Rest = {},
	Aim = { -- стойка: Ловибум в правой руке на уровне плеча, корпус чуть развёрнут
		Waist = Vector3.new(0, -12, 0),
		RightShoulder = Vector3.new(95, 0, -12),
		RightElbow = Vector3.new(55, 0, 0),
		LeftShoulder = Vector3.new(18, 0, 6),
		Neck = Vector3.new(0, 8, 0),
		Lift = Vector3.new(0, 0, 0),
	},
	Cock = { -- замах: рука за головой, корпус скручен вправо и откинут, присед
		Waist = Vector3.new(14, -46, 0),
		Root = Vector3.new(6, -10, 0),
		RightShoulder = Vector3.new(205, 0, -18),
		RightElbow = Vector3.new(82, 0, 0),
		LeftShoulder = Vector3.new(70, 0, 18),
		LeftElbow = Vector3.new(20, 0, 0),
		RightHip = Vector3.new(-22, 0, 0),
		LeftHip = Vector3.new(26, 0, 0),
		RightKnee = Vector3.new(-30, 0, 0),
		LeftKnee = Vector3.new(-34, 0, 0),
		Neck = Vector3.new(-8, 26, 0),
		Lift = Vector3.new(0.5, -0.55, 0),
	},
	Whip = { -- бросок: рука хлещет вперёд-вниз, корпус разворачивается и уходит вперёд, шаг левой
		Waist = Vector3.new(-24, 38, 0),
		Root = Vector3.new(-14, 12, 0),
		RightShoulder = Vector3.new(58, 0, 14),
		RightElbow = Vector3.new(6, 0, 0),
		LeftShoulder = Vector3.new(-48, 0, 12),
		RightHip = Vector3.new(-38, 0, 0),
		LeftHip = Vector3.new(34, 0, 0),
		LeftKnee = Vector3.new(-42, 0, 0),
		RightKnee = Vector3.new(-12, 0, 0),
		Neck = Vector3.new(10, -18, 0),
		Lift = Vector3.new(-1.1, -0.35, 0),
	},
	Follow = { -- доводка: рука прошла вниз, корпус выпрямляется
		Waist = Vector3.new(-12, 20, 0),
		Root = Vector3.new(-6, 6, 0),
		RightShoulder = Vector3.new(20, 0, 10),
		LeftShoulder = Vector3.new(-20, 0, 8),
		RightHip = Vector3.new(-18, 0, 0),
		LeftHip = Vector3.new(16, 0, 0),
		LeftKnee = Vector3.new(-18, 0, 0),
		Lift = Vector3.new(-0.6, -0.1, 0),
	},
}

-- R6: суставы повёрнуты иначе (ось плеча — Z сустава); правая и левая рука зеркальны.
local R6: { [string]: Pose } = {
	Rest = {},
	Aim = { ["Right Shoulder"] = Vector3.new(0, 0, 95), ["Left Shoulder"] = Vector3.new(0, 0, -15) },
	Cock = {
		["Right Shoulder"] = Vector3.new(0, 0, 200),
		["Left Shoulder"] = Vector3.new(0, 0, -70),
		RootJoint = Vector3.new(-12, 0, 0),
		Lift = Vector3.new(0.4, -0.4, 0),
	},
	Whip = {
		["Right Shoulder"] = Vector3.new(0, 0, 55),
		["Left Shoulder"] = Vector3.new(0, 0, 45),
		RootJoint = Vector3.new(16, 0, 0),
		Lift = Vector3.new(-0.9, -0.2, 0),
	},
	Follow = {
		["Right Shoulder"] = Vector3.new(0, 0, 20),
		RootJoint = Vector3.new(6, 0, 0),
		Lift = Vector3.new(-0.4, 0, 0),
	},
}

-- Кривые
local function smooth(t: number): number
	local x = math.clamp(t, 0, 1)
	return x * x * (3 - 2 * x)
end
local function easeIn(t: number): number
	local x = math.clamp(t, 0, 1)
	return x * x * x
end
local function easeOutBack(t: number): number
	local x = math.clamp(t, 0, 1) - 1
	return 1 + x * x * (2.6 * x + 1.6)
end

-- Замах по доле времени u (0…1): стойка → замах (0…0.5) → держит и дожимает (0.5…0.62) → хлёст (0.62…0.78) →
-- доводка (0.78…1). Release — доля, на которой Ловибум покидает руку.
ThrowPose.Release = 0.74
local KEYS = {
	{ from = "Aim", to = "Cock", a = 0, b = 0.5, curve = smooth },
	{ from = "Cock", to = "Cock", a = 0.5, b = 0.62, curve = smooth },
	{ from = "Cock", to = "Whip", a = 0.62, b = 0.78, curve = easeIn },
	{ from = "Whip", to = "Follow", a = 0.78, b = 1, curve = easeOutBack },
}

export type Handle = {
	Aim: (self: Handle, weight: number) -> (),
	Windup: (self: Handle, u: number) -> (),
	Hand: (self: Handle) -> CFrame?,
	Stop: (self: Handle) -> (),
}

-- Начать управлять позой персонажа. nil — у персонажа нет суставов.
function ThrowPose.Start(character: Model): Handle?
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	local root = character:FindFirstChild("HumanoidRootPart")
	if not humanoid or not root then
		return nil
	end
	local r15 = humanoid.RigType == Enum.HumanoidRigType.R15
	local set = if r15 then R15 else R6
	-- суставы: прежние Motor6D или новые AnimationConstraint — у обоих есть Transform
	local motors: { [string]: any } = {}
	for _, d in character:GetDescendants() do
		if d:IsA("Motor6D") or d:IsA("AnimationConstraint") then
			motors[d.Name] = d
		end
	end
	local lift = motors[if r15 then "Root" else "RootJoint"]
	local hand = character:FindFirstChild(if r15 then "RightHand" else "Right Arm")

	local current: Pose = {}
	local weight = 0 -- сколько позы поверх обычной анимации (плавный вход и выход)
	local function blend(a: Pose, b: Pose, t: number)
		for name in motors do
			local va, vb = a[name] or Vector3.zero, b[name] or Vector3.zero
			current[name] = va:Lerp(vb, t)
		end
		current.Lift = (a.Lift or Vector3.zero):Lerp(b.Lift or Vector3.zero, t)
	end
	blend(set.Rest, set.Rest, 0)

	local connection = RunService.Stepped:Connect(function()
		if weight <= 0 then
			return
		end
		for name, motor in motors do
			local v = current[name]
			if v and v.Magnitude > 1e-3 then
				local target = CFrame.Angles(math.rad(v.X), math.rad(v.Y), math.rad(v.Z))
				motor.Transform = motor.Transform:Lerp(target, weight)
			end
		end
		local l = current.Lift
		if lift and l and l.Magnitude > 1e-3 then
			-- сдвиг корпуса: вперёд (−Z персонажа) и вверх; у R6 корневой сустав повёрнут — оси другие
			local shift = if r15 then CFrame.new(0, l.Y, l.X) else CFrame.new(0, l.X, l.Y)
			lift.Transform = lift.Transform * CFrame.new():Lerp(shift, weight)
		end
	end)

	local handle = {} :: any
	-- Стойка у края: weight 0…1 — плавный вход.
	function handle:Aim(w: number)
		weight = math.clamp(w, 0, 1)
		blend(set.Aim, set.Aim, 0)
	end
	function handle:Windup(u: number)
		weight = 1
		for _, key in KEYS do
			if u <= key.b or key == KEYS[#KEYS] then
				blend(set[key.from], set[key.to], key.curve((u - key.a) / (key.b - key.a)))
				break
			end
		end
	end
	-- Ладонь (мир): где держится Ловибум.
	function handle:Hand(): CFrame?
		if hand and hand:IsA("BasePart") then
			return hand.CFrame * CFrame.new(0, if r15 then -0.35 else -1.1, -0.2)
		end
		return nil
	end
	function handle:Stop()
		connection:Disconnect()
		weight = 0
	end
	return handle :: Handle
end

return ThrowPose

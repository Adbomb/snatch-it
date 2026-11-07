-- Тренировка на клиенте (D51, D18): у каждого игрока с атрибутом Training (ставит сервер, GymService) рука с
-- гантелью (World/HandDumbbell) поднимается к бицепсу и опускается — один подъём за GameConfig.Gym.TickSeconds; верх
-- подъёма — в момент начисления силы: фаза по общему серверному времени (workspace:GetServerTimeNow), по нему же
-- сервер начисляет силу. Подъём быстрее, опускание медленнее, короткая задержка вверху и внизу; корпус чуть
-- откидывается назад. Процедурно, без анимаций-ассетов: смещения поз суставов поверх анимаций Roblox (Motor6D или
-- AnimationConstraint — Util/Joints, ключ "Training") — R15: плечо, локоть, кисть, поясница (Waist); R6: плечо.
-- Сгибание — поворот вокруг поперечной оси персонажа, поэтому одинаково для R6 и R15. Анимирует каждый клиент у всех
-- тренирующихся, поэтому движение видят все. Включение и выключение плавные; после выключения смещения сняты и
-- суставы снова только под анимациями Roblox. Замах «Удар» (PvpController) складывается со своим ключом.
-- Зависит от Config/GameConfig, Config/UITokens, Util/Joints.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local UITokens = require(Config:WaitForChild("UITokens"))

local Joints = require(script.Parent.Parent:WaitForChild("Util"):WaitForChild("Joints"))

local T = UITokens.Training

type Joint = { joint: Joints.Joint, angle: (k: number) -> number }
type Rig = { character: Model, root: BasePart, joints: { Joint }, weight: number }

local TrainingController = {}

local rigs: { [Player]: Rig } = {}
local NONE = CFrame.new() -- без смещения

local function smooth(x: number): number
	return x * x * (3 - 2 * x)
end

local function lerp(a: number, b: number, k: number): number
	return a + (b - a) * k
end

-- Насколько поднята гантель (0 — рука внизу, 1 — у бицепса) в фазе p такта: верх в p = 0 (начисление силы),
-- затем задержка, медленное опускание, задержка внизу и подъём к следующему такту.
function TrainingController.Curl(p: number): number
	local c = T.Curve
	if p < c.Top then
		return 1
	end
	p -= c.Top
	if p < c.Down then
		return 1 - smooth(p / c.Down)
	end
	p -= c.Down
	if p < c.Bottom then
		return 0
	end
	p -= c.Bottom
	local lift = 1 - c.Top - c.Down - c.Bottom
	return smooth(math.clamp(p / lift, 0, 1))
end

-- Суставы и их углы по подъёму k (градусы из UITokens.Training): сгибание вперёд — поворот вокруг поперечной оси
-- персонажа (вправо от корня), переведённой в оси позы сустава каждый кадр.
local function rigOf(character: Model): Rig?
	local root = character:FindFirstChild("HumanoidRootPart")
	if not root or not root:IsA("BasePart") then
		return nil
	end
	local joints: { Joint } = {}
	local function add(name: string, angle: (k: number) -> number)
		local joint = Joints.Find(character, name)
		if joint then
			table.insert(joints, { joint = joint, angle = angle })
		end
	end
	local r15 = T.R15
	if Joints.Find(character, "RightElbow") then
		add("RightShoulder", function(k)
			return lerp(r15.ShoulderRest, r15.ShoulderTop, k)
		end)
		add("RightElbow", function(k)
			return lerp(r15.ElbowRest, r15.ElbowTop, k)
		end)
		add("RightWrist", function(k)
			return r15.Wrist * k
		end)
		add("Waist", function(k)
			return r15.Lean * k -- корпус чуть назад (поворот вокруг оси вправо: верх уходит назад)
		end)
	else
		local r6 = T.R6
		add("Right Shoulder", function(k)
			return lerp(r6.Rest, r6.Top, k)
		end)
	end
	if #joints == 0 then
		return nil
	end
	return { character = character, root = root, joints = joints, weight = 0 }
end

local function restore(rig: Rig)
	for _, item in rig.joints do
		Joints.SetOffset(item.joint, "Training", nil)
	end
end

local function step(dt: number)
	local period = GameConfig.Gym.TickSeconds
	local phase = (workspace:GetServerTimeNow() % period) / period
	local curl = TrainingController.Curl(phase)
	local blend = math.min(1, dt / T.Blend)
	for _, player in Players:GetPlayers() do
		local character = player.Character
		local on = player:GetAttribute("Training") == true and character ~= nil
		local rig = rigs[player]
		if rig and rig.character ~= character then
			restore(rig) -- новый персонаж: старые суставы вернуть (если ещё живы) и собрать заново
			rigs[player] = nil
			rig = nil
		end
		if on and not rig and character then
			rig = rigOf(character)
			rigs[player] = rig
		end
		if rig then
			rig.weight = math.clamp(rig.weight + (if on then blend else -blend), 0, 1)
			if rig.weight <= 0 and not on then
				restore(rig)
				rigs[player] = nil
			else
				for _, item in rig.joints do
					-- вес: при включении и выключении поза плавно приходит из исходной и уходит в неё
					-- ось — каждый кадр: прыжок или эмоция в начале тренировки не перекосят сгибание
					local axis = Joints.Axis(item.joint, rig.root.CFrame.RightVector)
					local pose = CFrame.fromAxisAngle(axis, math.rad(item.angle(curl)))
					Joints.SetOffset(item.joint, "Training", NONE:Lerp(pose, rig.weight))
				end
			end
		end
	end
end

function TrainingController.Init()
	RunService.RenderStepped:Connect(step)
	Players.PlayerRemoving:Connect(function(player)
		local rig = rigs[player]
		if rig then
			restore(rig)
			rigs[player] = nil
		end
	end)
end

return TrainingController

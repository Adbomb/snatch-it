-- Суставы персонажа для процедурных движений (D18, D51). Сустав — Motor6D или, у обновлённых суставов аватаров,
-- AnimationConstraint (так в Studio 2026-11-07 у R15). Аниматор Roblox каждый кадр пишет в сустав Transform — у
-- AnimationConstraint он ещё и гасит любое смещение точек крепления, поэтому смещение позы накладывается на Transform:
-- каждый кадр в PreSimulation (после аниматора, до физики) Transform = offset × Transform аниматора. offset — в осях
-- позы сустава (C0 мотора или Attachment0), как раньше C0 × offset. Смещения от разных источников (тренировка, замах
-- «Удар») складываются по ключам. Если аниматор этот сустав не пишет, прежнее смещение не копится: берётся последний
-- его Transform. Меняется только у этого клиента — каждый клиент двигает суставы всех игроков сам.
-- Ни от чего не зависит.

local RunService = game:GetService("RunService")

local Joints = {}

export type Joint = Motor6D | AnimationConstraint

type State = {
	offsets: { [string]: CFrame },
	anim: CFrame?, -- последний Transform аниматора
	written: CFrame?, -- что мы записали (прочитано обратно)
}

local states: { [Instance]: State } = {}
local started = false

-- Сустав name персонажа: Motor6D или AnimationConstraint с обеими точками крепления.
function Joints.Find(character: Model, name: string): Joint?
	for _, d in character:GetDescendants() do
		if d.Name == name then
			if d:IsA("Motor6D") then
				return d
			elseif d:IsA("AnimationConstraint") and d.Attachment0 and d.Attachment1 then
				return d
			end
		end
	end
	return nil
end

-- Мировое направление direction в осях позы сустава: вокруг него поворачивать offset (у R6 и R15 оси поз разные,
-- а «согнуть вперёд» — всегда вокруг поперечной оси персонажа).
function Joints.Axis(joint: Joint, direction: Vector3): Vector3
	local frame = CFrame.identity
	if joint:IsA("Motor6D") then
		frame = if joint.Part0 then joint.Part0.CFrame * joint.C0 else joint.C0
	elseif joint:IsA("AnimationConstraint") and joint.Attachment0 then
		frame = joint.Attachment0.WorldCFrame
	end
	return frame:VectorToObjectSpace(direction).Unit
end

local function apply()
	for joint, state in states do
		local j = joint :: any
		if not joint.Parent then
			states[joint] = nil
			continue
		end
		local current: CFrame = j.Transform
		local anim = if state.written and current == state.written then state.anim or current else current
		local total = CFrame.identity
		local any = false
		for _, offset in state.offsets do
			total *= offset
			any = true
		end
		if any then
			j.Transform = total * anim
			state.anim = anim
			state.written = j.Transform
		else
			j.Transform = anim -- смещений больше нет: позу аниматора как есть
			states[joint] = nil
		end
	end
end

-- Смещение позы сустава от источника key (nil — убрать). Действует с ближайшего кадра.
function Joints.SetOffset(joint: Joint, key: string, offset: CFrame?)
	local state = states[joint]
	if not state then
		if offset == nil then
			return
		end
		state = { offsets = {} }
		states[joint] = state
	end
	state.offsets[key] = offset
	if not started then
		started = true
		RunService.PreSimulation:Connect(apply)
	end
end

return Joints

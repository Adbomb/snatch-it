-- Гантель в руке (D51): модель гантели уровня владельца (World/MeshModels, Dumbbell01…10 — та же, что раньше стояла
-- огромной во дворе, не примитивы) уменьшена до GameConfig.Gym.HandDumbbell.Length по длине грифа и приварена к
-- правой кисти: R15 — RightHand, R6 — низ Right Arm. Хват молотковый: гриф по направлению кисти вперёд, диски перед
-- кулаком и за ним — не задевают бедро при подъёме. Детали без массы, столкновений, касаний и запросов; модель лежит
-- в персонаже, поэтому её видят все. Лампы огромной модели в руке не нужны — убираются. Анимацию подъёма делает
-- клиент у каждого (Controllers/TrainingController). Только вид. Зависит от World/MeshBuilder, Config/GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local MeshBuilder = require(ServerScriptService.Server.World.MeshBuilder)

local CFG = GameConfig.Gym.HandDumbbell
local warned: { [string]: boolean } = {} -- модели без загруженных мешей: предупредить один раз

local HandDumbbell = {}

HandDumbbell.Name = "HandDumbbell"

-- Кисть персонажа и место гантели в её осях (R15 — кисть, R6 — вся рука, кулак внизу).
local function grip(character: Model): (BasePart?, CFrame)
	local hand = character:FindFirstChild("RightHand")
	if hand and hand:IsA("BasePart") then
		return hand, CFG.R15Hold
	end
	local arm = character:FindFirstChild("Right Arm")
	if arm and arm:IsA("BasePart") then
		return arm, CFG.R6Hold
	end
	return nil, CFrame.identity
end

function HandDumbbell.Get(character: Model?): Model?
	local model = character and character:FindFirstChild(HandDumbbell.Name)
	return if model and model:IsA("Model") then model else nil
end

function HandDumbbell.Remove(character: Model?)
	local model = HandDumbbell.Get(character)
	if model then
		model:Destroy()
	end
end

-- Гантель уровня level в правую руку (та же уже в руке — ничего не делает; другой уровень — заменяет).
function HandDumbbell.Attach(character: Model, level: number): Model?
	local current = HandDumbbell.Get(character)
	if current and current:GetAttribute("Level") == level then
		return current
	end
	HandDumbbell.Remove(character)
	local hand, hold = grip(character)
	local name = ("Dumbbell%02d"):format(level)
	if not hand then
		return nil
	end
	-- меши не загрузились (ассеты недоступны): гантели нет, рука качается пустой; не собирать каждые StateCheck
	if not MeshBuilder.IsReady(name) then
		if not warned[name] then
			warned[name] = true
			warn(
				("[HandDumbbell] меши %s не загружены — тренировка без гантели в руке"):format(
					name
				)
			)
		end
		return nil
	end
	local model = MeshBuilder.Build(name, CFrame.identity, nil :: any, {
		name = HandDumbbell.Name,
	})
	if not model then
		return nil
	end
	for _, d in model:GetDescendants() do
		if d:IsA("Light") or d:IsA("Attachment") then
			d:Destroy()
		end
	end
	local parts: { BasePart } = {}
	for _, d in model:GetChildren() do
		if d:IsA("BasePart") then
			table.insert(parts, d)
		end
	end
	if #parts == 0 then
		model:Destroy()
		return nil
	end
	-- уменьшить вокруг центра модели: длина по грифу (ось X модели) — Length
	local box, size = model:GetBoundingBox()
	local scale = CFG.Length / math.max(size.X, 0.01)
	local target = hand.CFrame * hold
	for _, part in parts do
		local offset = box:ToObjectSpace(part.CFrame)
		part.Size *= scale
		part.CFrame = target * CFrame.new(offset.Position * scale) * offset.Rotation
		part.Anchored = false
		part.Massless = true
		part.CanCollide = false
		part.CanQuery = false
		part.CanTouch = false
		local weld = Instance.new("WeldConstraint")
		weld.Part0 = hand
		weld.Part1 = part
		weld.Parent = part
	end
	model.PrimaryPart = parts[1]
	model:SetAttribute("Level", level)
	model.Parent = character
	return model
end

return HandDumbbell

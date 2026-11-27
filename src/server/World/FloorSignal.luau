-- Сигналы редкости этажа, которые видят все (D74, владелец 2026-11-27): вблизи этаж — продолжение монстра, издалека —
-- редкость. Здесь то, что не кирпичи (кирпичи и свечение — World/Models/MonsterFloor):
--   Decorate — после постановки модели этажа: детали с именем Pulse получают метку FloorPulse (пульсацию ведёт клиент —
--              Controllers/FloorSignalController), у Мифического и Алмазного — искры (одна система на этаж);
--   Beacon   — маяк над башней: невидимая точка с меткой TowerBeacon и атрибутами (владелец, счётчики Золотых,
--              Мифических и Алмазных этажей, лучший этаж) — по ним клиент рисует значок; луч в цвет лучшего этажа
--              (Мифический — средний, Алмазный — высокий; у Золотого луча нет); издалека клиент показывает луч
--              табличкой — на низкой графике дальше ~600 стадов движок не рисует ни детали, ни Beam (проверено в
--              Play на уровне 1), а табличка видна с любой точки карты; у подножия башни — светящийся пояс
--              в цвет лучшего этажа (Золотой и выше): с точки появления верх высокой башни не виден, пояс — на
--              уровне глаз;
--   Arrive   — момент получения: редкий этаж встал на место — метка FloorArrival, клиенты рядом показывают вспышку,
--              столб света и звук; точка сама исчезает.
-- Числа — Config/FloorRarity (Signal, Beam, Sparks, Arrival). Текстур и звуков из загрузок нет: частица — встроенная.
-- Зависит от Config/FloorRarity, Config/GameConfig.

local CollectionService = game:GetService("CollectionService")
local Debris = game:GetService("Debris")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local FloorRarity = require(ReplicatedStorage.Shared.Config.FloorRarity)
local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

local FloorSignal = {}

FloorSignal.PulseTag = "FloorPulse"
FloorSignal.BeaconTag = "TowerBeacon"
FloorSignal.ArrivalTag = "FloorArrival"

local HX, HZ = GameConfig.Tower.Half.X, GameConfig.Tower.Half.Y

local function signalOf(tier: number): any
	return FloorRarity.Signal[FloorRarity.Order[tier]]
end

local function point(name: string, at: CFrame, size: Vector3?): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	part.Transparency = 1
	part.Size = size or Vector3.one
	part.CFrame = at
	return part
end

-- Модель этажа model редкости tier поставлена на место frame (низ плиты, перед — −Z), высота этажа height.
function FloorSignal.Decorate(model: Model, tier: number, frame: CFrame, height: number)
	local signal = signalOf(tier)
	if signal.pulse then
		local to = Color3.fromHex(signal.pulse.color)
		for _, d in model:GetDescendants() do
			if d:IsA("BasePart") and d.Name == "Pulse" then
				d:SetAttribute("PulseTo", to)
				d:SetAttribute("PulsePeriod", signal.pulse.period)
				CollectionService:AddTag(d, FloorSignal.PulseTag)
			end
		end
	end
	if signal.sparks then
		-- искры поднимаются вдоль фасада и боков: один излучатель — плоский объём перед стеклом
		local cfg = FloorRarity.Sparks
		local spread = signal.spread or 0
		local box = point(
			"Sparks",
			frame * CFrame.new(0, height * 0.5, -HZ - 1.5),
			Vector3.new((HX + spread) * 2, height * 0.8, 1)
		)
		local emitter = Instance.new("ParticleEmitter")
		emitter.Name = "RaritySparks"
		emitter.Rate = signal.sparks
		emitter.Lifetime = NumberRange.new(cfg.Lifetime * 0.7, cfg.Lifetime)
		emitter.Speed = NumberRange.new(cfg.Speed * 0.5, cfg.Speed)
		emitter.EmissionDirection = Enum.NormalId.Top
		emitter.SpreadAngle = Vector2.new(25, 25)
		emitter.Acceleration = Vector3.new(0, cfg.Rise, 0)
		emitter.Shape = Enum.ParticleEmitterShape.Box
		emitter.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
		emitter.Size = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0),
			NumberSequenceKeypoint.new(0.2, cfg.Size),
			NumberSequenceKeypoint.new(1, 0),
		})
		emitter.Color = ColorSequence.new(Color3.fromHex(signal.glow))
		emitter.LightEmission = 1
		emitter.LightInfluence = 0
		emitter.Brightness = cfg.Brightness
		emitter.Rotation = NumberRange.new(0, 360)
		emitter.Parent = box
		box.Parent = model
	end
end

-- Маяк над башней: top — верх башни (над колпаком), tiers — редкости её этажей (1…6), owner — имя владельца для
-- значка, base — низ башни (центр следа; nil — без пояса у подножия). Возвращает точку маяка.
function FloorSignal.Beacon(parent: Instance, top: CFrame, tiers: { number }, owner: string, base: CFrame?): BasePart
	local counts = { 0, 0, 0, 0, 0, 0 }
	local best = 1
	for _, tier in tiers do
		counts[tier] += 1
		best = math.max(best, tier)
	end
	local anchor = point("TowerBeacon", top)
	anchor:SetAttribute("Owner", owner)
	anchor:SetAttribute("Best", FloorRarity.Order[best])
	anchor:SetAttribute("Rise", top.Position.Y) -- высота над землёй: значок виден с земли с положенного расстояния
	for tier, key in FloorRarity.Order do
		if FloorRarity.Signal[key].badge then
			anchor:SetAttribute(key, counts[tier])
		end
	end
	local signal = signalOf(best)
	if signal.beam then
		local cfg = FloorRarity.Beam
		local a0 = Instance.new("Attachment")
		a0.Name = "BeamBase"
		a0.Parent = anchor
		local a1 = Instance.new("Attachment")
		a1.Name = "BeamTop"
		a1.Position = Vector3.new(0, signal.beam, 0)
		a1.Parent = anchor
		local beam = Instance.new("Beam")
		beam.Name = "RarityBeam"
		beam.Attachment0 = a0
		beam.Attachment1 = a1
		beam.FaceCamera = true
		beam.Segments = 1
		beam.Width0 = cfg.Width
		beam.Width1 = cfg.TopWidth
		beam.Color = ColorSequence.new(Color3.fromHex(signal.glow))
		beam.LightEmission = 1
		beam.LightInfluence = 0
		beam.Brightness = cfg.Brightness
		beam.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, cfg.Transparency),
			NumberSequenceKeypoint.new(0.7, cfg.Transparency + (1 - cfg.Transparency) * 0.35),
			NumberSequenceKeypoint.new(1, 1),
		})
		beam.Parent = anchor
	end
	if base and signal.glow then
		-- пояс у подножия: четыре светящиеся полосы вокруг следа башни
		local cfg = FloorRarity.Halo
		local color = Color3.fromHex(signal.glow)
		local function strip(size: Vector3, offset: Vector3)
			local part = point("Pulse", base * CFrame.new(offset), size)
			part.Transparency = 0
			part.Material = Enum.Material.Neon
			part.Color = color
			if signal.pulse then
				part:SetAttribute("PulseTo", Color3.fromHex(signal.pulse.color))
				part:SetAttribute("PulsePeriod", signal.pulse.period)
				CollectionService:AddTag(part, FloorSignal.PulseTag)
			end
			part.Parent = anchor
		end
		local y = cfg.Lift + cfg.Height / 2
		for _, s in { -1, 1 } do
			strip(
				Vector3.new((HX + cfg.Out) * 2, cfg.Height, cfg.Depth),
				Vector3.new(0, y, s * (HZ + cfg.Out - cfg.Depth / 2))
			)
			strip(
				Vector3.new(cfg.Depth, cfg.Height, (HZ + cfg.Out - cfg.Depth) * 2),
				Vector3.new(s * (HX + cfg.Out - cfg.Depth / 2), y, 0)
			)
		end
	end
	CollectionService:AddTag(anchor, FloorSignal.BeaconTag)
	anchor.Parent = parent
	return anchor
end

-- Момент получения: этаж редкости tier встал на место at (центр этажа). nil — у этой редкости момента нет.
function FloorSignal.Arrive(parent: Instance, at: CFrame, tier: number): BasePart?
	local key = FloorRarity.Order[tier]
	local cfg = FloorRarity.Arrival[key]
	if not cfg then
		return nil
	end
	local anchor = point("FloorArrival", at)
	anchor:SetAttribute("Rarity", key)
	anchor:SetAttribute("At", workspace:GetServerTimeNow())
	CollectionService:AddTag(anchor, FloorSignal.ArrivalTag)
	anchor.Parent = parent
	Debris:AddItem(anchor, cfg.time + 1)
	return anchor
end

return FloorSignal

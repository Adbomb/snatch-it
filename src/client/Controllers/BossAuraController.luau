-- Фиолетовая аура Короля-дракона (босс 10) у каждого клиента (Config/BossAura). У настоящего босса — вариант
-- BossAura.Active; атрибут workspace.BossAuraPrototype = имя варианта ("C3", "Vortex", "Veil", "RoyalAura" …) или
-- "off" перекрывает его (сравнение в Studio). Только вид: урона, усилений и запросов к серверу нет.
-- Эмиттеры (ParticleEmitter) — на частях модели дракона (у клиента, не реплицируются), один PointLight у груди.
-- Сила — по состоянию босса (State, StateAt; сон — слабая пульсация, пробуждение — рост, бой — полная, поражение —
-- угасание; у варианта — свои таблицы state, sleepPulse, sleepLayer), по залпу (VolleyAt: рост на подготовке,
-- всплеск на выстреле) и всплескам варианта (bursts: пробуждение, начало выпада). Частота частиц × дальность камеры ×
-- качество графики игрока; дальше Lod.far — эмиттеры и свет выключены. Пересчёт — 10 раз в секунду, не каждый кадр.
-- Частицы выпускаются своим счётчиком (Emit), Rate эмиттеров = 0: движок урезает Rate по своему качеству графики
-- (в Studio при «Автоматическом» — в разы), а частая запись Rate сбивает его накопление; так вид зависит только от
-- чисел Config/BossAura и наших множителей дальности и качества. У слоя byArea частота части — по её площади
-- (большие части гуще, мелкие реже), бюджет maxParticles — по сумме.
-- Кроме частиц слоёв: ленты Beam (ribbons — нити вдоль цепочек частей и кольца), пул разрядов (arcs) и орбиты
-- (orbits — точки, которые каждый кадр кружат вокруг части и выпускают частицы по касательной; бюджет частиц общий
-- со слоями). У варианта vary — плавная волна силы слоя, volleyLayer — своя доля усиления в залп. Всё созданное
-- (эмиттеры, ленты, Attachment, свет) хранится в записи ауры и удаляется вместе с ней (смена варианта, босс убран
-- с карты или снят тег); соединений на ауру нет — только общие в Init.
-- Зависит от Config/BossAura.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local BossAura = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("BossAura"))

local TAG = "Boss"
local STEP = 0.1 -- с между пересчётами силы
local REBUILD_QUIET = 0.5 -- с без новых частей модели до пересборки ауры (части догружаются после тега)
local AREA_REF = 150 -- ст.²: часть с такой площадью (половина поверхности) — частота слоя как есть

-- phase — сдвиг волны силы слоя (cfg.vary): соседние эмиттеры и ленты дышат не в такт
type Emitter = { emitter: ParticleEmitter, layer: string, rate: number, acc: number, shown: number, phase: number }
-- Лента (Beam) варианта: strand — номер нити (на низком качестве графики показываются не все), brightness — своя.
-- minQuality — ниже такой доли качества графики лента не показывается (второстепенные кольца и нити — на телефонах)
type Ribbon = {
	beam: Beam,
	layer: string,
	strand: number,
	strands: number,
	brightness: number,
	phase: number,
	minQuality: number,
}
-- Точка орбиты (cfg.orbits): Attachment на части кружит вокруг неё каждый кадр (в осях части: центр center,
-- плоскость u × v, радиус radius); эмиттеры на ней выпускают частицы по касательной — энергия идёт вокруг тела.
type Orbit = { att: Attachment, center: Vector3, u: Vector3, v: Vector3, radius: number, speed: number, phase: number }
-- Разряд: короткая вспышка Beam между двумя случайными точками на частях (пул, у каждого — две свои точки).
type Arc = { beam: Beam, a0: Attachment, a1: Attachment, offAt: number }
type ArcSet = { spec: any, parts: { BasePart }, pool: { Arc }, nextAt: number }
type Aura = {
	model: Model,
	variant: string,
	emitters: { Emitter },
	ribbons: { Ribbon },
	attachments: { Attachment },
	arcs: ArcSet?,
	orbits: { Orbit },
	visible: boolean, -- аура видна (дальность, качество, сила) — орбиты крутятся только тогда
	-- части модели приходят к клиенту не сразу (тег — раньше): новая часть → пересборка через REBUILD_QUIET
	conn: RBXScriptConnection?,
	dirtyAt: number?,
	light: PointLight?,
	lightBrightness: number,
	scale: number, -- урезание частот до бюджета maxParticles
	level: number, -- сглаженная сила
	defeatAt: number?,
}

local auras: { [Model]: Aura } = {}

local BossAuraController = {}

local function numberSeq(points: { { number } }): NumberSequence
	local keys = {}
	for _, p in points do
		table.insert(keys, NumberSequenceKeypoint.new(p[1], p[2], p[3] or 0))
	end
	return NumberSequence.new(keys)
end

local function colorSeq(points: { { any } }): ColorSequence
	local keys = {}
	for _, p in points do
		table.insert(keys, ColorSequenceKeypoint.new(p[1], Color3.fromHex(p[2])))
	end
	return ColorSequence.new(keys)
end

local function makeEmitter(layer: any, part: Instance): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Name = "Aura" .. layer.name
	e.Texture = layer.texture
	e.Color = colorSeq(layer.color)
	e.Size = numberSeq(layer.size)
	e.Transparency = numberSeq(layer.transparency)
	if layer.squash then
		e.Squash = numberSeq(layer.squash)
	end
	e.Lifetime = NumberRange.new(layer.lifetime[1], layer.lifetime[2])
	e.Speed = NumberRange.new(layer.speed[1], layer.speed[2])
	e.SpreadAngle = Vector2.new(layer.spread, layer.spread)
	e.Acceleration = layer.acceleration
	e.Drag = layer.drag or 0
	e.LightEmission = layer.lightEmission
	e.LightInfluence = layer.lightInfluence
	e.Brightness = layer.brightness
	e.ZOffset = layer.zOffset or 0
	if layer.rotation then
		e.Rotation = NumberRange.new(layer.rotation[1], layer.rotation[2])
	end
	if layer.rotSpeed then
		e.RotSpeed = NumberRange.new(layer.rotSpeed[1], layer.rotSpeed[2])
	end
	if layer.orientation then
		e.Orientation = Enum.ParticleOrientation[layer.orientation]
	end
	if layer.flipbook then
		e.FlipbookLayout = Enum.ParticleFlipbookLayout[layer.flipbook]
		e.FlipbookMode = Enum.ParticleFlipbookMode[layer.flipbookMode or "OneShot"]
	end
	e.Shape = Enum.ParticleEmitterShape[layer.shape or "Box"]
	e.ShapeStyle = Enum.ParticleEmitterShapeStyle[layer.shapeStyle or "Surface"]
	e.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
	if layer.emitUp then
		-- эмиттер на части, которая поворачивается с суставом: «вверх» задаёт ускорение, направление — наружу
		e.EmissionDirection = Enum.NormalId.Top
	end
	-- lockedToPart — частицы держатся части (пелена и вихри не отстают от тела при движении)
	e.LockedToPart = layer.lockedToPart == true
	e.Rate = 0
	e.Parent = part
	return e
end

local function destroy(aura: Aura)
	if aura.conn then
		aura.conn:Disconnect()
		aura.conn = nil
	end
	for _, item in aura.emitters do
		item.emitter:Destroy()
	end
	for _, item in aura.ribbons do
		item.beam:Destroy()
	end
	for _, att in aura.attachments do
		att:Destroy()
	end
	if aura.arcs then
		for _, arc in aura.arcs.pool do
			arc.beam:Destroy()
			arc.a0:Destroy()
			arc.a1:Destroy()
		end
	end
	if aura.light then
		aura.light:Destroy()
	end
	auras[aura.model] = nil
end

-- ── Ленты: нити вдоль цепочек частей, кольца, разряды ──────────────────────────────────────────────────────────

local UP = Vector3.yAxis

-- Половина габарита части в направлении dir (мира): насколько от центра до поверхности коробки.
-- Части скруглённые: берём вписанный в габарит эллипсоид (у коробки по диагонали точка ушла бы далеко от меша).
local function support(part: BasePart, dir: Vector3): number
	local cf, s = part.CFrame, part.Size
	local x, y, z = dir:Dot(cf.RightVector) * s.X, dir:Dot(cf.UpVector) * s.Y, dir:Dot(cf.LookVector) * s.Z
	return math.sqrt(x * x + y * y + z * z) / 2
end

-- Точка ленты на части: Attachment в осях части, ось X (направление кривой Beam) — axis мира, вторая — side.
local function attach(aura: Aura, part: BasePart, at: Vector3, axis: Vector3, side: Vector3): Attachment
	local att = Instance.new("Attachment")
	att.Name = "AuraPoint"
	local x = part.CFrame:VectorToObjectSpace(axis.Unit)
	local y = part.CFrame:VectorToObjectSpace(side)
	y = (y - x * y:Dot(x))
	if y.Magnitude < 1e-3 then
		y = if math.abs(x.Y) < 0.9 then Vector3.yAxis else Vector3.xAxis
		y = (y - x * y:Dot(x))
	end
	att.CFrame = CFrame.fromMatrix(part.CFrame:PointToObjectSpace(at), x, y.Unit)
	att.Parent = part
	table.insert(aura.attachments, att)
	return att
end

local function makeBeam(spec: any, a0: Attachment, a1: Attachment, width0: number, width1: number): Beam
	local b = Instance.new("Beam")
	b.Name = "Aura" .. spec.name
	b.Texture = spec.texture
	b.TextureMode = Enum.TextureMode[spec.textureMode or "Wrap"]
	b.TextureLength = spec.textureLength or 8
	b.TextureSpeed = spec.textureSpeed or 1
	b.Color = colorSeq(spec.color)
	b.Transparency = numberSeq(spec.transparency or { { 0, 0 }, { 1, 0 } })
	b.LightEmission = spec.lightEmission or 1
	b.LightInfluence = spec.lightInfluence or 0
	b.Brightness = 0
	b.FaceCamera = spec.faceCamera ~= false
	b.Segments = spec.segments or 8
	b.Width0, b.Width1 = width0, width1
	b.ZOffset = spec.zOffset or 0
	b.Attachment0, b.Attachment1 = a0, a1
	b.Parent = a0.Parent
	return b
end

-- Нити вдоль цепочки частей (spec.chains): у каждой части точка на её поверхности под углом нити вокруг оси цепочки
-- (twist — поворот на следующей части: нити спиралью обвивают тело), отрезки между соседними точками — Beam,
-- выгнутые наружу (bulge), открытые концы цепочки гаснут. tip — продолжить до конца последней части.
local function buildChains(aura: Aura, model: Model, spec: any)
	local strands = spec.strands or 1
	for _, chain in spec.chains do
		local parts: { BasePart } = {}
		for _, name in chain do
			local part = model:FindFirstChild(name, true)
			if part and part:IsA("BasePart") then
				table.insert(parts, part)
			end
		end
		if #parts < 2 and not (spec.tip and #parts == 1) then
			continue
		end
		local centers = {}
		for i, part in parts do
			centers[i] = part.Position
		end
		local n = #parts
		local function tangent(i: number): Vector3
			local a = centers[math.max(i - 1, 1)]
			local b = centers[math.min(i + 1, n)]
			local d = b - a
			return if d.Magnitude > 1e-3 then d.Unit else UP
		end
		local ground = model:GetPivot().Position.Y + (spec.minHeight or 1.5) -- пивот модели — на полу
		for s = 1, strands do
			local points: { { part: BasePart, at: Vector3, out: Vector3 } } = {}
			for i, part in parts do
				local d = tangent(i)
				local e1 = d:Cross(UP)
				e1 = if e1.Magnitude > 0.1 then e1.Unit else d:Cross(Vector3.xAxis).Unit
				local e2 = e1:Cross(d).Unit -- «верх» поперёк цепочки
				-- угол нити: angles — свои (0 — сверху, ± — бока; под брюхо не уходят), иначе поровну по кругу;
				-- twist — спираль, wobble — нити переплетаются, не уходя со своей стороны
				local base = if spec.angles
					then spec.angles[(s - 1) % #spec.angles + 1]
					else 2 * math.pi * (s - 1) / strands
				local angle = base
					+ (spec.phase or 0)
					+ (i - 1) * (spec.twist or 0)
					+ (spec.wobble or 0) * math.sin((i - 1) * 1.7 + s * 2.1)
				local out = e2 * math.cos(angle) + e1 * math.sin(angle)
				local r = support(part, out) * (spec.radial or 1) + (spec.margin or 0)
				local at = centers[i] + out * r
				if at.Y < ground then
					at = Vector3.new(at.X, ground, at.Z) -- лежит на полу: нить над полом, не под ним
				end
				table.insert(points, { part = part, at = at, out = out })
			end
			if spec.tip then
				local last = points[#points]
				local d = tangent(n)
				local reach = support(parts[n], d) * (spec.tipReach or 1)
				table.insert(points, { part = last.part, at = last.at + d * reach, out = last.out })
			end
			local speed = (spec.textureSpeed or 1) * (1 + 0.18 * ((s % 3) - 1)) -- нити не в такт
			for k = 1, #points - 1 do
				local p, q = points[k], points[k + 1]
				local t = q.at - p.at
				local len = t.Magnitude
				if len < 0.2 then
					continue
				end
				t = t.Unit
				local bulge = spec.bulge or 0.35
				local a0 = attach(aura, p.part, p.at, t + p.out * bulge, p.out)
				local a1 = attach(aura, q.part, q.at, t - q.out * bulge, q.out)
				local beam = makeBeam(spec, a0, a1, spec.width[1], spec.width[2] or spec.width[1])
				beam.CurveSize0, beam.CurveSize1 = len / 3, len / 3
				beam.TextureSpeed = speed
				-- открытые концы цепочки: появление у начала и угасание у конца
				local fadeIn, fadeOut = k == 1, k == #points - 1
				if fadeIn or fadeOut then
					local base = spec.transparency or { { 0, 0 }, { 1, 0 } }
					local a = base[1][2]
					beam.Transparency = numberSeq({
						{ 0, if fadeIn then 1 else a },
						{ 0.45, a },
						{ 1, if fadeOut then 1 else a },
					})
				end
				table.insert(aura.ribbons, {
					beam = beam,
					layer = spec.name,
					strand = s,
					strands = strands,
					minQuality = spec.minQuality or 0,
					brightness = spec.brightness or 1,
					phase = math.random() * 2 * math.pi,
				})
			end
		end
	end
end

-- Кольца (spec.rings): окружность радиуса radius (доля габарита части или стады) вокруг центра части в плоскости
-- с нормалью normal (оси части), из segments дуг Beam (кривые Безье по касательной — почти ровный круг).
local function buildRings(aura: Aura, model: Model, spec: any)
	for _, ring in spec.rings do
		local part = model:FindFirstChild(ring.part, true)
		if not part or not part:IsA("BasePart") then
			continue
		end
		local cf = part.CFrame
		local normal = cf:VectorToWorldSpace(ring.normal or Vector3.yAxis).Unit
		local toward = ring.toward and model:FindFirstChild(ring.toward, true)
		if toward and toward:IsA("BasePart") and (toward.Position - part.Position).Magnitude > 0.1 then
			normal = (toward.Position - part.Position).Unit -- кольцо поперёк оси «часть → соседняя часть»
		end
		local u = normal:Cross(if math.abs(normal.Y) < 0.9 then UP else Vector3.xAxis).Unit
		local v = normal:Cross(u).Unit
		local radius = ring.radius
		if ring.radiusK then
			radius = math.max(support(part, u), support(part, v)) * ring.radiusK
		end
		-- центр: offset — в осях части, shift — стады вдоль нормали (к соседней части): не зависит от поворота меша
		local center = cf:PointToWorldSpace(ring.offset or Vector3.zero) + normal * (ring.shift or 0)
		local n = ring.segments or 6
		local curve = 4 / 3 * math.tan(math.pi / (2 * n)) * radius
		for k = 0, n - 1 do
			local f0, f1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
			local p0 = center + (u * math.cos(f0) + v * math.sin(f0)) * radius
			local p1 = center + (u * math.cos(f1) + v * math.sin(f1)) * radius
			local t0 = -u * math.sin(f0) + v * math.cos(f0)
			local t1 = -u * math.sin(f1) + v * math.cos(f1)
			local a0 = attach(aura, part, p0, t0, normal)
			local a1 = attach(aura, part, p1, t1, normal)
			local beam = makeBeam(spec, a0, a1, spec.width[1], spec.width[2] or spec.width[1])
			beam.CurveSize0, beam.CurveSize1 = curve, curve
			beam.TextureSpeed = (spec.textureSpeed or 1) * (ring.speed or 1)
			table.insert(aura.ribbons, {
				beam = beam,
				layer = spec.name,
				strand = 1,
				strands = 1,
				minQuality = ring.minQuality or spec.minQuality or 0,
				brightness = (spec.brightness or 1) * (ring.brightness or 1),
				phase = math.random() * 2 * math.pi,
			})
		end
	end
end

-- Пул разрядов (spec — cfg.arcs): Beam с текстурой молнии, точки переносятся на случайные части при вспышке.
local function buildArcs(aura: Aura, model: Model, spec: any)
	local parts = {}
	for _, name in spec.parts do
		local part = model:FindFirstChild(name, true)
		if part and part:IsA("BasePart") then
			table.insert(parts, part)
		end
	end
	if #parts < 2 then
		return
	end
	local set: ArcSet = { spec = spec, parts = parts, pool = {}, nextAt = 0 }
	for _ = 1, spec.pool do
		local a0 = Instance.new("Attachment")
		a0.Name = "AuraArc"
		a0.Parent = parts[1]
		local a1 = Instance.new("Attachment")
		a1.Name = "AuraArc"
		a1.Parent = parts[2]
		local beam = makeBeam(spec, a0, a1, spec.width[1], spec.width[2] or spec.width[1])
		beam.Enabled = false
		table.insert(set.pool, { beam = beam, a0 = a0, a1 = a1, offAt = 0 })
	end
	aura.arcs = set
end

-- Случайная точка на поверхности части (в её осях): одна грань коробки, по ней — случайно в пределах 80 %.
local function surfacePoint(part: BasePart): Vector3
	local s = part.Size / 2
	local axis = math.random(3)
	local sign = if math.random() < 0.5 then -1 else 1
	local p = {
		(math.random() * 1.6 - 0.8) * s.X,
		(math.random() * 1.6 - 0.8) * s.Y,
		(math.random() * 1.6 - 0.8) * s.Z,
	}
	p[axis] = sign * ({ s.X, s.Y, s.Z })[axis] * 1.05
	return Vector3.new(p[1], p[2], p[3])
end

local function fireArc(set: ArcSet, arc: Arc, now: number, brightness: number)
	local spec = set.spec
	for _ = 1, 6 do
		local pa = set.parts[math.random(#set.parts)]
		local pb = set.parts[math.random(#set.parts)]
		if pa ~= pb and (pa.Position - pb.Position).Magnitude <= spec.maxLength then
			arc.a0.Parent, arc.a1.Parent = pa, pb
			arc.a0.Position, arc.a1.Position = surfacePoint(pa), surfacePoint(pb)
			arc.a0.Axis = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5).Unit
			arc.a1.Axis = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5).Unit
			local len = (arc.a0.WorldPosition - arc.a1.WorldPosition).Magnitude
			arc.beam.CurveSize0 = len * (math.random() * 0.4 + 0.1)
			arc.beam.CurveSize1 = len * (math.random() * 0.4 + 0.1)
			arc.beam.Brightness = (spec.brightness or 1) * brightness
			arc.beam.Enabled = true
			arc.offAt = now + spec.life[1] + math.random() * (spec.life[2] - spec.life[1])
			return
		end
	end
end

-- Разряды: гаснут по времени; новый — через случайную паузу every (короче при силе выше 1 — залп, всплески).
local function updateArcs(set: ArcSet, now: number, level: number, visible: boolean)
	for _, arc in set.pool do
		if arc.beam.Enabled and (now >= arc.offAt or not visible) then
			arc.beam.Enabled = false
		end
	end
	if not visible or level < 0.05 or now < set.nextAt then
		return
	end
	for _, arc in set.pool do
		if not arc.beam.Enabled then
			fireArc(set, arc, now, math.min(level, 1.6))
			break
		end
	end
	local every = set.spec.every
	set.nextAt = now + (every[1] + math.random() * (every[2] - every[1])) / math.max(level, 0.3)
end

-- Орбиты (cfg.orbits): count точек равномерно по окружности радиуса radiusK × габарит части вокруг оси
-- «часть → toward» (центр сдвинут на shift вдоль неё); на каждой точке — эмиттеры слоёв spec.layers, частицы
-- летят по касательной (EmissionDirection Top = ось Y точки). Возвращает оценку активных частиц.
local function buildOrbits(aura: Aura, model: Model, spec: any): number
	local part = model:FindFirstChild(spec.part, true)
	if not part or not part:IsA("BasePart") then
		return 0
	end
	local cf = part.CFrame
	local normal = cf.LookVector
	local toward = spec.toward and model:FindFirstChild(spec.toward, true)
	if toward and toward:IsA("BasePart") and (toward.Position - part.Position).Magnitude > 0.1 then
		normal = (toward.Position - part.Position).Unit
	end
	local u = normal:Cross(if math.abs(normal.Y) < 0.9 then UP else Vector3.xAxis).Unit
	local v = normal:Cross(u).Unit
	local radius = math.max(support(part, u), support(part, v)) * (spec.radiusK or 1.2)
	local center = part.Position + normal * (spec.shift or 0)
	local budget = 0
	for k = 1, spec.count or 1 do
		local att = Instance.new("Attachment")
		att.Name = "AuraOrbit"
		att.Parent = part
		table.insert(aura.attachments, att)
		table.insert(aura.orbits, {
			att = att,
			center = cf:PointToObjectSpace(center),
			u = cf:VectorToObjectSpace(u),
			v = cf:VectorToObjectSpace(v),
			radius = radius,
			speed = spec.speed or 1,
			phase = 2 * math.pi * (k - 1) / (spec.count or 1),
		})
		for _, layer in spec.layers do
			table.insert(aura.emitters, {
				emitter = makeEmitter(layer, att),
				layer = layer.name,
				rate = layer.rate,
				acc = 0,
				shown = 0,
				phase = math.random() * 2 * math.pi,
			})
			budget += layer.rate * (layer.lifetime[1] + layer.lifetime[2]) / 2
		end
	end
	return budget
end

-- Точки орбит — каждый кадр (их единицы): угол phase + speed·t, ось Y — по касательной движения.
local function updateOrbits(aura: Aura, clock: number)
	for _, o in aura.orbits do
		local a = o.phase + o.speed * clock
		local c, s = math.cos(a), math.sin(a)
		local pos = o.center + (o.u * c + o.v * s) * o.radius
		local tangent = (o.v * c - o.u * s) * (if o.speed >= 0 then 1 else -1)
		local outward = o.u * c + o.v * s
		o.att.CFrame = CFrame.fromMatrix(pos, outward, tangent)
	end
end

local function build(model: Model, variant: string): Aura?
	local cfg = BossAura.Variants[variant]
	if not cfg then
		return nil
	end
	local aura: Aura = {
		model = model,
		variant = variant,
		emitters = {},
		ribbons = {},
		attachments = {},
		arcs = nil,
		orbits = {},
		visible = false,
		light = nil,
		lightBrightness = cfg.light.brightness,
		scale = 1,
		level = 0,
	}
	local budget = 0
	for _, layer in cfg.layers do
		for _, name in layer.parts do
			local part = model:FindFirstChild(name, true)
			if part and part:IsA("BasePart") then
				local rate = layer.rate
				if layer.byArea then
					local s = part.Size
					local area = s.X * s.Y + s.Y * s.Z + s.X * s.Z
					rate *= math.clamp(math.sqrt(area / AREA_REF), 0.45, 2.2)
				end
				table.insert(aura.emitters, {
					emitter = makeEmitter(layer, part),
					layer = layer.name,
					rate = rate,
					acc = 0,
					shown = 0,
					phase = math.random() * 2 * math.pi,
				})
				budget += rate * (layer.lifetime[1] + layer.lifetime[2]) / 2
			end
		end
	end
	for _, spec in cfg.orbits or {} do
		budget += buildOrbits(aura, model, spec)
	end
	aura.scale = math.min(1, cfg.maxParticles / math.max(budget, 1)) -- общий бюджет частиц слоёв и орбит
	updateOrbits(aura, workspace:GetServerTimeNow())
	for _, spec in cfg.ribbons or {} do
		if spec.chains then
			buildChains(aura, model, spec)
		end
		if spec.rings then
			buildRings(aura, model, spec)
		end
	end
	if cfg.arcs then
		buildArcs(aura, model, cfg.arcs)
	end
	local holder = model:FindFirstChild(cfg.light.part, true)
	if holder and holder:IsA("BasePart") then
		local light = Instance.new("PointLight")
		light.Name = "AuraLight"
		light.Color = Color3.fromHex(cfg.light.color)
		light.Range = cfg.light.range
		light.Brightness = 0
		light.Shadows = false
		light.Parent = holder
		aura.light = light
	end
	aura.conn = model.DescendantAdded:Connect(function(d)
		if d:IsA("BasePart") then
			aura.dirtyAt = os.clock()
		end
	end)
	auras[model] = aura
	return aura
end

local function since(model: Model, attribute: string): number?
	local at = model:GetAttribute(attribute)
	if type(at) ~= "number" then
		return nil
	end
	return workspace:GetServerTimeNow() - at
end

-- Сила по состоянию (до сглаживания): 0…1, во сне — пульсация.
local function stateLevel(model: Model, clock: number, cfg: any): (number, string)
	local state = model:GetAttribute("State") or "Sleep"
	local level = (cfg.state or BossAura.State)[state] or 1
	if state == "Sleep" or state == "FallAsleep" then
		local p = cfg.sleepPulse or BossAura.SleepPulse
		level *= 1 - p.depth * (0.5 + 0.5 * math.sin(clock * 2 * math.pi / p.period))
	elseif state == "Defeat" then
		local t = since(model, "StateAt") or 0
		level = math.max(0, 1 - t / BossAura.DefeatFade)
	end
	return level, state
end

-- Множитель залпа: подготовка — рост до peak·0.7, выстрел — всплеск peak, потом обратно к 1.
local function volleyBoost(model: Model): number
	local t = since(model, "VolleyAt")
	if not t or t < 0 then
		return 1
	end
	local cancel = since(model, "VolleyCancelAt")
	if cancel and cancel >= 0 and cancel < t then
		return 1
	end
	local v = BossAura.Volley
	if t < v.prepFrom then
		return 1
	elseif t < v.fire then
		local k = math.clamp((t - v.prepFrom) / v.prep, 0, 1)
		return 1 + (v.peak - 1) * 0.7 * k
	elseif t < v.fire + v.hold then
		return v.peak
	elseif t < v.fire + v.hold + v.back then
		local k = (t - v.fire - v.hold) / v.back
		return v.peak + (1 - v.peak) * k
	end
	return 1
end

-- Кратковременные всплески варианта (cfg.bursts): пробуждение — первые time секунд состояния Wake, начало выпада
-- (не залпа) — time секунд от AttackAt; форма — колокол до peak.
local function burst(model: Model, cfg: any): number
	local b = cfg.bursts
	if not b then
		return 1
	end
	local k = 1
	if b.wake and model:GetAttribute("State") == "Wake" then
		local t = since(model, "StateAt") or 99
		if t >= 0 and t < b.wake.time then
			k = math.max(k, 1 + (b.wake.peak - 1) * math.sin(math.pi * t / b.wake.time))
		end
	end
	if b.attack and model:GetAttribute("AttackKind") ~= "volley" then
		local t = since(model, "AttackAt")
		if t and t >= 0 and t < b.attack.time then
			k = math.max(k, 1 + (b.attack.peak - 1) * math.sin(math.pi * t / b.attack.time))
		end
	end
	return k
end

local function qualityShare(): number
	-- только Studio: workspace.BossAuraQuality (0…1) — доля как у игрока с таким качеством (снимки для сравнения)
	local forced = RunService:IsStudio() and workspace:GetAttribute("BossAuraQuality")
	if type(forced) == "number" then
		return math.clamp(forced, 0, 1)
	end
	local ok, level = pcall(function()
		return UserSettings():GetService("UserGameSettings").SavedQualityLevel
	end)
	local q = BossAura.Quality
	if not ok or level == Enum.SavedQualitySetting.Automatic then
		return q.auto
	end
	local n = tonumber(string.match(level.Name, "%d+")) or 10
	if n <= q.low then
		return q.lowShare
	elseif n <= q.mid then
		return q.midShare
	end
	return 1
end

local function lodShare(model: Model): number
	local camera = workspace.CurrentCamera
	local root = model.PrimaryPart
	if not camera or not root then
		return 0
	end
	local d = (camera.CFrame.Position - root.Position).Magnitude
	local lod = BossAura.Lod
	if d >= lod.far then
		return 0
	elseif d <= lod.near then
		return 1
	end
	return 1 - (1 - lod.minShare) * (d - lod.near) / (lod.far - lod.near)
end

local MAX_BURST = 12 -- частиц за один пересчёт с эмиттера (после паузы — без залпа частиц)

local function update(aura: Aura, dt: number, clock: number)
	local model = aura.model
	local cfg = BossAura.Variants[aura.variant]
	local target, state = stateLevel(model, clock, cfg)
	local blend = math.clamp(dt / BossAura.Blend, 0, 1)
	aura.level += (target - aura.level) * blend
	local boost = volleyBoost(model)
	local level = aura.level * boost * burst(model, cfg)
	local share = lodShare(model) * qualityShare() * aura.scale
	local sleepy = state == "Sleep" or state == "FallAsleep" or state == "Wake"
	local sleepLayer = cfg.sleepLayer or BossAura.SleepLayer
	local vary = cfg.vary or {}
	local volleyLayer = cfg.volleyLayer or {}
	-- множитель слоя: плавная волна силы (vary: период, глубина) и своя добавка залпа (volleyLayer: доля сверх общей)
	local function layerWave(layer: string, phase: number): number
		local k = 1
		local w = vary[layer]
		if w then
			k *= 1 + w.depth * math.sin(2 * math.pi * clock / w.period + phase)
		end
		local extra = volleyLayer[layer]
		if extra and boost > 1 then
			k *= 1 + (boost - 1) * extra
		end
		return k
	end
	for _, item in aura.emitters do
		local layerK = (if sleepy then sleepLayer[item.layer] or 1 else 1) * layerWave(item.layer, item.phase)
		local rate = item.rate * level * layerK * share
		item.acc = math.min(item.acc + rate * dt, MAX_BURST)
		local n = math.floor(item.acc)
		if n > 0 then
			item.emitter:Emit(n)
			item.acc -= n
		end
		if math.abs(rate - item.shown) > 0.05 * math.max(rate, item.shown, 0.1) then
			item.shown = rate
			item.emitter:SetAttribute("AuraRate", rate) -- для проверки (частиц в секунду сейчас)
		end
	end
	-- ленты: яркость по силе (во сне — доля слоя), на низком качестве графики — только часть нитей
	local visible = share > 0 and level > 0.02
	aura.visible = visible
	local quality = qualityShare()
	for _, item in aura.ribbons do
		local layerK = (if sleepy then sleepLayer[item.layer] or 1 else 1) * layerWave(item.layer, item.phase)
		local keep = item.strand <= math.max(1, math.ceil(item.strands * quality - 1e-6)) and quality >= item.minQuality
		local on = visible and keep
		if item.beam.Enabled ~= on then
			item.beam.Enabled = on
		end
		if on then
			item.beam.Brightness = item.brightness * math.min(level * layerK, 1.8)
		end
	end
	if aura.arcs then
		local arcK = (if sleepy then sleepLayer.Arc or 1 else 1) * layerWave("Arc", 0)
		updateArcs(aura.arcs, clock, level * arcK, visible)
	end
	if aura.light then
		aura.light.Brightness = aura.lightBrightness * math.min(level, 1.6) * (if share > 0 then 1 else 0)
		aura.light.Enabled = share > 0 and level > 0.02
	end
end

local function syncAll()
	local variant = workspace:GetAttribute(BossAura.Attribute)
	if variant == nil then
		variant = BossAura.Active -- настоящий босс без атрибута сравнения
	end
	for model, aura in auras do
		if aura.variant ~= variant or not model.Parent then
			destroy(aura)
		end
	end
	if type(variant) ~= "string" or not BossAura.Variants[variant] then
		return
	end
	for _, model in CollectionService:GetTagged(TAG) do
		if model:IsA("Model") and model:GetAttribute("Zone") == BossAura.Zone and not auras[model] then
			build(model, variant)
		end
	end
end

-- Для проверки (MCP): сколько эмиттеров и частиц в секунду сейчас и оценка активных частиц.
function BossAuraController.Stats(): { [string]: number }
	local out = { emitters = 0, enabled = 0, rate = 0, active = 0, ribbons = 0, ribbonsOn = 0, arcs = 0 }
	for _, aura in auras do
		for _, item in aura.ribbons do
			out.ribbons += 1
			if item.beam.Enabled then
				out.ribbonsOn += 1
			end
		end
		if aura.arcs then
			out.arcs += #aura.arcs.pool
		end
		for _, item in aura.emitters do
			local e = item.emitter
			out.emitters += 1
			if item.shown > 0.01 then
				out.enabled += 1
				out.rate += item.shown
				out.active += item.shown * (e.Lifetime.Min + e.Lifetime.Max) / 2
			end
		end
	end
	return out
end

function BossAuraController.Init()
	workspace:GetAttributeChangedSignal(BossAura.Attribute):Connect(syncAll)
	CollectionService:GetInstanceAddedSignal(TAG):Connect(function()
		task.defer(syncAll)
	end)
	CollectionService:GetInstanceRemovedSignal(TAG):Connect(function(model)
		local aura = auras[model]
		if aura then
			destroy(aura)
		end
	end)
	syncAll()
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		if next(auras) == nil then
			return
		end
		local clock = workspace:GetServerTimeNow()
		-- орбиты — каждый кадр, но только у видимой ауры (их точек единицы); остальное — STEP
		for _, aura in auras do
			if aura.visible and #aura.orbits > 0 then
				updateOrbits(aura, clock)
			end
		end
		acc += dt
		if acc < STEP then
			return
		end
		local rebuild: { [Model]: string } = {}
		for model, aura in auras do
			if not model.Parent then
				destroy(aura)
			elseif aura.dirtyAt and os.clock() - aura.dirtyAt >= REBUILD_QUIET then
				rebuild[model] = aura.variant -- догрузились части: собрать заново по полной модели
				destroy(aura)
			else
				update(aura, acc, clock)
			end
		end
		for model, variant in rebuild do
			build(model, variant)
		end
		acc = 0
	end)
end

return BossAuraController

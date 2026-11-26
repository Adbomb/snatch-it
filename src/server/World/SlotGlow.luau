-- Подсветка плит добычи цветом редкости (D71): под каждым местом предмета у босса — светящееся кольцо и свет снизу.
-- Арена строит кольцо в своём модуле (Ring — кирпичи с меткой SlotGlow, атрибутами Zone/Slot и нейтральным цветом), обод
-- плиты — в прежнем стиле арены. BossLootService красит кольцо: слот занят — неон цвета редкости предмета
-- (UITokens.RarityColor), пуст — нейтральный пластик без света. Кольцо на полу низкое (по нему пробегают, D66).
-- Кольцо с hideEmpty (у постаментов «Свалки») без предмета не видно; к нему — мягкий полупрозрачный ореол (Halo).
-- Пульсацию яркости ведёт клиент (Controllers/SlotGlowController) по атрибутам Pulse/PulsePeriod/Alpha/Lit.
-- Зависит от ModelBuilder (метки и атрибуты кирпичей), Config/UITokens, Config/Items.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Items = require(ReplicatedStorage.Shared.Config.Items)
local UITokens = require(ReplicatedStorage.Shared.Config.UITokens)
local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)

type Brick = ModelBuilder.Brick

local SlotGlow = {}

SlotGlow.Tag = "SlotGlow"
-- Вид кольца: число сторон (8 — восьмигранник D39, 4 — квадрат под квадратную подушку), свет снизу (дальность, яркость),
-- высота над полом (≥ 0.1 — без мерцания граней, D36).
SlotGlow.Look = {
	Sides = 8,
	LightRange = 9,
	LightBrightness = 0.8,
	Height = 0.12,
	-- пульсация яркости у колец с pulse (клиент): период, с; насколько бледнеет в нижней точке (прибавка к прозрачности)
	PulsePeriod = 2.6,
	PulseRing = 0.2,
	PulseHalo = 0.12,
	-- ореол: прозрачность, высота над полом (ниже кольца — кольцо читается поверх)
	HaloAlpha = 0.62,
	HaloHeight = 0.07,
}

export type RingOptions = {
	height: number?, -- высота над полом (по умолчанию Look.Height)
	sides: number?, -- 8 или 4 (по умолчанию Look.Sides)
	light: boolean?, -- свет снизу (по умолчанию да; в зонах с бюджетом света 10 — нет)
	hideEmpty: boolean?, -- без предмета не видно (по умолчанию — нейтральный пластик)
	pulse: boolean?, -- медленная пульсация яркости на клиенте
}

-- Стороны многоугольного кольца rIn…rOut высотой h вокруг at: CFrame и размер каждой стороны. Восьмигранник — хорды по
-- внешнему краю (контур без щелей; у внутреннего края соседние перекрываются — через одну тоньше); квадрат — две
-- длинные стороны и две короткие между ними (бруски по осям не перекрываются, совпадающих граней нет).
local function sides(at: CFrame, rIn: number, rOut: number, h: number, n: number): { { cframe: CFrame, size: Vector3 } }
	local out = {}
	for k = 0, n - 1 do
		local length = if n == 4 then (if k % 2 == 0 then 2 * rOut else 2 * rIn) else 2 * rOut * math.tan(math.pi / n)
		-- у восьмигранника нечётные стороны тоньше (на 0.02 выше низа и на 0.03 ниже верха): их грани в перекрытии спрятаны
		-- внутри соседа (не мерцают)
		local odd = n ~= 4 and k % 2 == 1
		local y0 = if odd then 0.03 else 0.01 -- низ над полом: не совпадает с низом соседних деталей пола
		local hk = if odd then h - 0.06 else h - 0.01
		local frame = at * CFrame.Angles(0, k * 2 * math.pi / n, 0) * CFrame.new(0, y0 + hk / 2, (rIn + rOut) / 2)
		table.insert(out, { cframe = frame, size = Vector3.new(length, hk, rOut - rIn) })
	end
	return out
end

-- Кольцо вокруг места предмета: at — центр места на верхе пола (CFrame в координатах модели зоны), rIn…rOut — ширина
-- кольца (у квадрата — от центра до сторон), neutral — цвет пустого места. Возвращает кирпичи сторон с меткой SlotGlow и
-- (если light) невидимый источник света в центре.
function SlotGlow.Ring(
	zone: number,
	slot: number,
	at: CFrame,
	rIn: number,
	rOut: number,
	neutral: Color3,
	opts: RingOptions?
): { Brick }
	local o = opts or {}
	local look = SlotGlow.Look
	local attrs: { [string]: any } = { Zone = zone, Slot = slot, Neutral = neutral }
	if o.hideEmpty then
		attrs.Alpha = 0
	end
	if o.pulse then
		attrs.Pulse = look.PulseRing
		attrs.PulsePeriod = look.PulsePeriod
	end
	local out: { Brick } = {}
	for _, side in sides(at, rIn, rOut, o.height or look.Height, o.sides or look.Sides) do
		table.insert(
			out,
			ModelBuilder.Brick(side.size, side.cframe, neutral, {
				name = "SlotGlow",
				collide = false,
				shadow = false,
				material = if o.hideEmpty then Enum.Material.Neon else nil,
				transparency = if o.hideEmpty then 1 else nil,
				tags = { SlotGlow.Tag },
				attributes = attrs,
			})
		)
	end
	if o.light ~= false then
		-- свет снизу: маленький невидимый кубик в центре места, чуть над полом (под предметом)
		table.insert(
			out,
			ModelBuilder.Brick(Vector3.new(0.2, 0.2, 0.2), at * CFrame.new(0, 0.15, 0), neutral, {
				name = "SlotGlowLight",
				collide = false,
				shadow = false,
				transparency = 1,
				light = { range = look.LightRange, brightness = 0, color = neutral },
				tags = { SlotGlow.Tag },
				attributes = attrs,
			})
		)
	end
	return out
end

-- Ореол вокруг кольца (восьмигранник rIn…rOut, стороны вдоль осей — как у Ring): мягкий полупрозрачный неон, без
-- предмета не виден; пульсирует, если pulse. Детали встык, без нахлёста (прозрачные слои внахлёст дали бы тёмные углы):
-- 8 брусков по внутренней хорде и в каждом углу два клина — прямоугольные треугольники между концом бруска и внешней
-- вершиной (гипотенуза — по биссектрисе угла).
function SlotGlow.Halo(
	zone: number,
	slot: number,
	at: CFrame,
	rIn: number,
	rOut: number,
	neutral: Color3,
	pulse: boolean?
): { Brick }
	local look = SlotGlow.Look
	local attrs: { [string]: any } = { Zone = zone, Slot = slot, Neutral = neutral, Alpha = look.HaloAlpha }
	if pulse then
		attrs.Pulse = look.PulseHalo
		attrs.PulsePeriod = look.PulsePeriod
	end
	local t = math.tan(math.pi / 8)
	local h = look.HaloHeight - 0.02
	local y = 0.02 + h / 2 -- низ 0.02 над полом: не вровень с низом кольца (0.01 / 0.03)
	local width = rOut - rIn
	local out: { Brick } = {}
	local function piece(size: Vector3, cframe: CFrame, shape: string?)
		table.insert(
			out,
			ModelBuilder.Brick(size, cframe, neutral, {
				name = "SlotGlowHalo",
				shape = shape,
				material = Enum.Material.Neon,
				transparency = 1,
				collide = false,
				shadow = false,
				tags = { SlotGlow.Tag },
				attributes = attrs,
			})
		)
	end
	for k = 0, 7 do
		local side = at * CFrame.Angles(0, k * math.pi / 4, 0)
		piece(Vector3.new(2 * rIn * t, h, width), side * CFrame.new(0, y, (rIn + rOut) / 2))
		-- клин: толщина — по вертикали (ось X клина), прямой угол — у внешнего конца бруска
		local cx = rIn * t + width * t / 2
		for _, s in { 1, -1 } do
			local frame = CFrame.fromMatrix(
				Vector3.new(s * cx, y, (rIn + rOut) / 2),
				Vector3.new(0, -s, 0),
				Vector3.new(s, 0, 0),
				Vector3.new(0, 0, 1)
			)
			piece(Vector3.new(h, width * t, width), side * frame, "Wedge")
		end
	end
	return out
end

-- Обод вокруг кольца в стиле арены (не светится): rIn…rOut, высота height (выше кольца — обод читается).
function SlotGlow.Rim(at: CFrame, rIn: number, rOut: number, color: Color3, height: number, n: number?): { Brick }
	local out: { Brick } = {}
	for _, side in sides(at, rIn, rOut, height, n or SlotGlow.Look.Sides) do
		table.insert(
			out,
			ModelBuilder.Brick(side.size, side.cframe, color, { name = "SlotRim", collide = false, shadow = false })
		)
	end
	return out
end

-- Пометить уже построенный кирпич арены как подсветку места (у «Ледника» — неоновый диск под плитой).
function SlotGlow.Mark(brick: Brick, zone: number, slot: number, neutral: Color3): Brick
	local b = brick :: any
	b.tags = { SlotGlow.Tag }
	b.attributes = { Zone = zone, Slot = slot, Neutral = neutral }
	return brick
end

-- Цвет подсветки для предмета itemId (nil — место пустое).
function SlotGlow.ColorFor(itemId: string?): Color3?
	local def = itemId and Items[itemId]
	return def and UITokens.RarityColor(def.rarity) or nil
end

-- Покрасить подсветку места zone/slot: itemId — предмет на месте (nil — пусто). Только детали в мире (шаблоны в
-- ServerStorage не трогаем). Возвращает, сколько деталей покрашено.
function SlotGlow.Paint(zone: number, slot: number, itemId: string?): number
	local color = SlotGlow.ColorFor(itemId)
	local painted = 0
	for _, part in CollectionService:GetTagged(SlotGlow.Tag) do
		if not part:IsA("BasePart") or not part:IsDescendantOf(workspace) then
			continue
		end
		if part:GetAttribute("Zone") ~= zone or part:GetAttribute("Slot") ~= slot then
			continue
		end
		local neutral = part:GetAttribute("Neutral")
		local tone = color or (if typeof(neutral) == "Color3" then neutral else part.Color)
		local light = part:FindFirstChildWhichIsA("Light")
		if light then
			light.Color = tone
			light.Brightness = if color then SlotGlow.Look.LightBrightness else 0
		end
		local alpha = part:GetAttribute("Alpha")
		if typeof(alpha) == "number" then
			-- кольцо и ореол с hideEmpty: без предмета не видно; Lit — клиенту, пульсировать ли
			part.Color = tone
			part.Transparency = if color then alpha else 1
			part:SetAttribute("Lit", color ~= nil)
		elseif part.Transparency < 1 then
			part.Color = tone
			part.Material = if color then Enum.Material.Neon else Enum.Material.Plastic
		end
		painted += 1
	end
	return painted
end

return SlotGlow

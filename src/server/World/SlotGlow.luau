-- Подсветка плит добычи цветом редкости (D71): под каждым местом предмета у босса — светящееся кольцо и свет снизу.
-- Арена строит кольцо в своём модуле (Ring — кирпичи с меткой SlotGlow, атрибутами Zone/Slot и нейтральным цветом), обод
-- плиты — в прежнем стиле арены. BossLootService красит кольцо: слот занят — неон цвета редкости предмета
-- (UITokens.RarityColor), пуст — нейтральный пластик без света. Кольцо на полу низкое (по нему пробегают, D66).
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
}

export type RingOptions = {
	height: number?, -- высота над полом (по умолчанию Look.Height)
	sides: number?, -- 8 или 4 (по умолчанию Look.Sides)
	light: boolean?, -- свет снизу (по умолчанию да; в зонах с бюджетом света 10 — нет)
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
	local attrs = { Zone = zone, Slot = slot, Neutral = neutral }
	local out: { Brick } = {}
	for _, side in sides(at, rIn, rOut, o.height or look.Height, o.sides or look.Sides) do
		table.insert(
			out,
			ModelBuilder.Brick(side.size, side.cframe, neutral, {
				name = "SlotGlow",
				collide = false,
				shadow = false,
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
		if part.Transparency < 1 then
			part.Color = tone
			part.Material = if color then Enum.Material.Neon else Enum.Material.Plastic
		end
		painted += 1
	end
	return painted
end

return SlotGlow

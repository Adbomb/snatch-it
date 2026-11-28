-- Путь Ловибума при броске вдаль (D75), общий для своего и чужих полётов: точка приземления по зоне и глубине
-- (границы зон — по полам зон на карте), время полёта (не дольше Show.FlightMax даже до конца трассы: скорость растёт
-- с дальностью) и положение на дуге в долю времени u. Только расчёт, без объектов.
-- Зависит от Config/GameConfig (Throw.Show).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))

local Show = GameConfig.Throw.Show

local ThrowPath = {}

export type Zone = { index: number, near: number, far: number, floor: number, halfX: number }

local zones: { [number]: Zone } = {}
local edge: { halfX: number, z0: number, z1: number, top: number }? = nil

-- Зоны и полоса броска с карты (один раз; карта строится сервером до входа игрока).
local function collect()
	if next(zones) then
		return
	end
	local world = workspace:FindFirstChild("World")
	local map = world and world:FindFirstChild("Map")
	local folder = map and map:FindFirstChild("Zones")
	if not folder then
		return
	end
	for _, zone in folder:GetChildren() do
		local index = zone:GetAttribute("Zone")
		local floor = zone:FindFirstChild("Floor")
		if type(index) == "number" and floor and floor:IsA("Model") then
			local cf, size = floor:GetBoundingBox()
			zones[index] = {
				index = index,
				near = cf.Position.Z + size.Z / 2,
				far = cf.Position.Z - size.Z / 2,
				floor = cf.Position.Y + size.Y / 2,
				halfX = size.X / 2,
			}
		end
	end
	local strip = map and map:FindFirstChild("ThrowEdge")
	if strip then
		edge = {
			halfX = strip:GetAttribute("HalfX") or 46,
			z0 = strip:GetAttribute("Z0") or 1.3,
			z1 = strip:GetAttribute("Z1") or 10.3,
			top = strip:GetAttribute("Top") or 0.22,
		}
	end
end

function ThrowPath.Zone(index: number): Zone?
	collect()
	return zones[index]
end

-- Полоса броска у края обрыва (nil — карта ещё не пришла).
function ThrowPath.Edge(): { halfX: number, z0: number, z1: number, top: number }?
	collect()
	return edge
end

-- Стоит ли точка на полосе броска (как проверяет сервер, чуть строже: без запаса).
function ThrowPath.OnEdge(position: Vector3): boolean
	local e = ThrowPath.Edge()
	return e ~= nil and math.abs(position.X) <= e.halfX and position.Z >= -1 and position.Z <= e.z1
end

-- Подходит ли точка к полосе броска (до неё не дальше reach стадов): здесь видна панель выбора вида.
function ThrowPath.NearEdge(position: Vector3, reach: number): boolean
	local e = ThrowPath.Edge()
	return e ~= nil and math.abs(position.X) <= e.halfX + 8 and position.Z >= -1 and position.Z <= e.z1 + reach
end

-- Зона под точкой (по z) или nil.
function ThrowPath.ZoneAt(z: number): number?
	collect()
	for index, zone in zones do
		if z <= zone.near and z > zone.far then
			return index
		end
	end
	return nil
end

-- Длина всей трассы, стадов.
function ThrowPath.Length(): number
	collect()
	local near, far = 0, 0
	for _, zone in zones do
		near = math.max(near, zone.near)
		far = math.min(far, zone.far)
	end
	return math.max(1, near - far)
end

-- Точка приземления: зона, глубина 0…1 в ней и смещение по x (от места броска — к оси трассы).
function ThrowPath.Landing(zone: number, depth: number, fromX: number): Vector3?
	local z = ThrowPath.Zone(zone)
	if not z then
		return nil
	end
	local d = math.clamp(depth, 0.02, 0.98)
	-- рядом с осевой линией (на 5 правее), а не на ней: линия не закрывает Ловибум на раскрытии
	return Vector3.new(math.clamp(fromX * 0.2 - 5, -z.halfX + 8, z.halfX - 8), z.floor, z.near - d * (z.near - z.far))
end

-- Время полёта от from до to, секунды.
function ThrowPath.Duration(from: Vector3, to: Vector3): number
	local part = math.clamp(math.abs(to.Z - from.Z) / ThrowPath.Length(), 0, 1)
	return Show.FlightMin + (Show.FlightMax - Show.FlightMin) * part ^ Show.FlightPower
end

-- Доля пути в долю времени u: быстрый старт, к концу мягче (скорость в конце — 0.6 начальной), без остановок.
function ThrowPath.Progress(u: number): number
	local t = math.clamp(u, 0, 1)
	return t * (1.4 - 0.4 * t)
end

-- Положение на дуге: from → to, u — доля времени 0…1. Вторым числом — доля пути.
function ThrowPath.At(from: Vector3, to: Vector3, u: number): (Vector3, number)
	local p = ThrowPath.Progress(u)
	local flat = from:Lerp(to, p)
	local span = (Vector3.new(to.X, 0, to.Z) - Vector3.new(from.X, 0, from.Z)).Magnitude
	local arc = math.min(Show.ArcMax, Show.Arc * span + 2)
	return flat + Vector3.new(0, arc * 4 * p * (1 - p), 0), p
end

return ThrowPath

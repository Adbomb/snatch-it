--!nocheck
-- Проверка мира без Roblox Studio (Lune): декор зон 1 «Свалка» и 2 «Барахолка» на плитах пола зон — нет видимых пар
-- совпадающих граней (World/FaceCheck, D36); у «Барахолки» (D44) — части в бюджете, света мало, круг площадки
-- босса свободен (только плоский пол), в круге, куда босс заходит в бою, нет ничего выше LOW, у каждой надписи есть
-- табличка. Декор не зависит от Random, поэтому здесь он тот же,
-- что в игре. Запуск из корня репозитория: lune run scripts/lune/check_world.luau. Ошибка — код возврата 1.

local process = require("@lune/process")

local Env = require("./env")

local roblox = Env.roblox
local Vector3, CFrame, Vector2 = roblox.Vector3, roblox.CFrame, roblox.Vector2

local FaceCheck = Env.Require("ServerScriptService.Server.World.FaceCheck")
local MapLayout = Env.Require("ServerScriptService.Server.World.MapLayout")
local Junkyard = Env.Require("ServerScriptService.Server.World.Models.Junkyard")
local FleaMarket = Env.Require("ServerScriptService.Server.World.Models.FleaMarket")

local Battle = Env.Require("ReplicatedStorage.Shared.Config.Battle")

local FLEA_PARTS = 1300 -- бюджет декора одной зоны (карта целиком ≤ 12 000; было 802 до D44)
local FLEA_LIGHTS = 10 -- по одному на павильон и сундук, 2 прожектора (у столбиков границы зоны — свои)
local LOW = 2 -- в круге боя выше этого нет ничего: босс без столкновений прошёл бы сквозь декор
local FLAT = 0.6 -- выше этого над полом — уже не пол (ромб под боссом 0.5, бордюр 0.55)

local failed = 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if not ok then
		failed += 1
	end
end

-- Кирпичи декора зоны index в мировых координатах.
local function placed(index: number, bricks: { any }): { any }
	local frame = MapLayout.ZoneCFrame(index)
	for _, brick in bricks do
		brick.cframe = frame * brick.cframe
	end
	return bricks
end

-- Плита пола зоны (как в WorldBuilder: верх на Heights.Path, толщина 0.4).
local function floorOf(index: number): any
	local center = MapLayout.ZoneCFrame(index).Position
	return {
		size = Vector3.new(MapLayout.ZoneHalfWidth * 2, 0.4, MapLayout.ZoneSize),
		cframe = CFrame.new(center.X, MapLayout.Heights.Path - 0.2, center.Z),
	}
end

local junk = placed(1, Junkyard.Zone())
local fleaBricks, signs = FleaMarket.Zone()
local flea = placed(2, fleaBricks)

print("Грани (D36):")
local groups = {
	{ name = "Junk", bricks = junk },
	{ name = "Flea", bricks = flea },
	{ name = "Floor", bricks = { floorOf(1), floorOf(2) } },
}
local pairsCount, found = FaceCheck.Scan(Env.FakeRoot(groups))
for key, group in found do
	print(("    %s: %d (%s)"):format(key, group.n, group.example))
end
check(pairsCount == 0, ("видимых пар совпадающих граней: %d"):format(pairsCount))

print("Барахолка:")
check(#flea <= FLEA_PARTS, ("частей декора: %d из %d"):format(#flea, FLEA_PARTS))

local lights = 0
for _, brick in fleaBricks do
	if brick.light then
		lights += 1
	end
end
check(lights <= FLEA_LIGHTS, ("источников света: %d (не больше %d)"):format(lights, FLEA_LIGHTS))

-- Круг площадки — только плоский пол: бою ничего не мешает. Локальные координаты зоны: начало — центр пола.
local arena = MapLayout.Arenas[2]
local frame = MapLayout.ZoneCFrame(2)
local spot = MapLayout.BossSpot
local blocking = {}
for _, brick in flea do
	local p = frame:PointToObjectSpace(brick.cframe.Position)
	local cf, size = brick.cframe, brick.size
	local halfY = (
		math.abs(cf.RightVector.Y) * size.X
		+ math.abs(cf.UpVector.Y) * size.Y
		+ math.abs(cf.LookVector.Y) * size.Z
	) / 2
	local inside = (Vector2.new(p.X, p.Z) - spot).Magnitude < arena.radius + 1
	if inside and p.Y + halfY > FLAT and p.Y - halfY < 12 then
		table.insert(blocking, ("%s (%.1f, %.1f, %.1f)"):format(brick.name or "Brick", p.X, p.Y, p.Z))
	end
end
check(
	#blocking == 0,
	"на площадке босса нет декора выше пола"
		.. (if #blocking > 0 then ": " .. table.concat(blocking, "; ", 1, math.min(#blocking, 5)) else "")
)

-- Круг, куда босс заходит в бою: игрок не дальше Leash от места босса, босс останавливается в AttackRange − 1.5 от
-- игрока, плюс полкорпуса. Расстояние — от места босса до прямоугольника детали на полу.
local bossCfg = Battle.Bosses[2]
local roam = bossCfg.Leash - (bossCfg.AttackRange - 1.5) + 2
local tall = {}
for _, brick in flea do
	local p = frame:PointToObjectSpace(brick.cframe.Position)
	local cf, size = brick.cframe, brick.size
	local function half(axis: string): number
		return (
			math.abs(cf.RightVector[axis]) * size.X
			+ math.abs(cf.UpVector[axis]) * size.Y
			+ math.abs(cf.LookVector[axis]) * size.Z
		) / 2
	end
	local dx = math.max(math.abs(p.X - spot.X) - half("X"), 0)
	local dz = math.max(math.abs(p.Z - spot.Y) - half("Z"), 0)
	if math.sqrt(dx * dx + dz * dz) < roam and p.Y + half("Y") > LOW then
		table.insert(tall, ("%s (%.1f, %.1f, %.1f)"):format(brick.name or "Brick", p.X, p.Y, p.Z))
	end
end
check(
	#tall == 0,
	("в круге боя (r %.0f) нет декора выше %d"):format(roam, LOW)
		.. (if #tall > 0 then ": " .. table.concat(tall, "; ", 1, math.min(#tall, 5)) else "")
)

local names = {}
for _, brick in fleaBricks do
	if brick.name then
		names[brick.name] = (names[brick.name] or 0) + 1
	end
end
local badSigns = {}
for _, sign in signs do
	if names[sign.name] ~= 1 or sign.text == "" or #sign.faces == 0 then
		table.insert(badSigns, sign.name)
	end
end
check(
	#signs > 0 and #badSigns == 0,
	("надписей: %d, у каждой одна табличка%s"):format(
		#signs,
		if #badSigns > 0 then " (нет: " .. table.concat(badSigns, ", ") .. ")" else ""
	)
)

-- Предметы босса 2 стоят на площадке, без постаментов, у каждого свой поворот.
local points = {}
for _, point in MapLayout.ArtSlotPoints() do
	if point.zone == 2 then
		table.insert(points, point)
	end
end
local onArena, turns = true, {}
for _, point in points do
	local p = frame:PointToObjectSpace(point.cframe.Position)
	onArena = onArena
		and math.abs(p.Y - arena.top) < 1e-3
		and (Vector2.new(p.X, p.Z) - spot).Magnitude < arena.radius - 3
	local look = frame:VectorToObjectSpace(point.cframe.LookVector)
	turns[("%.2f"):format(math.atan2(look.X, look.Z))] = true
end
local distinct = 0
for _ in turns do
	distinct += 1
end
check(
	#points == 4 and onArena,
	("слотов босса 2 на площадке (высота %.2f): %d из 4"):format(arena.top, #points)
)
check(distinct == 4, ("разных поворотов предметов: %d из 4"):format(distinct))

if failed > 0 then
	print(("Проверок не прошло: %d"):format(failed))
	process.exit(1)
end
print("Все проверки мира прошли")

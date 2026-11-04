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

-- Надписи читаются с камеры игрока (D45): из точек камеры в проходе (x ±30, высота 8–16, по всей длине зоны) надписи
-- не закрывают столбы редкостей (то, что стоит у прохода перед павильонами). Для каждой грани с надписью: из точек,
-- откуда она видна и читается (спереди, ближе 70, под углом не круче 70° к грани), доля точек, где столбы закрывают
-- больше SIGN_HIDDEN, — не больше SIGN_BAD_SHARE, и нигде не больше SIGN_WORST. Закрытость — доля из 15 точек грани,
-- луч к которым пересекает столб. Таблички редкостей стоят в ряд, как уличные указатели: друг другу не помеха.
-- Перекрытия вывесок друг другом под острым углом (подвесная вывеска пагоды, ценник перед щитом) — свойство
-- композиции: печатаются для сведения, проверку не валят.
local SIGN_HIDDEN, SIGN_BAD_SHARE, SIGN_WORST = 0.25, 0.1, 0.6
local SIGN_GRAZING = math.cos(math.rad(70))
local FACES = {
	Front = { Vector3.new(0, 0, -1), Vector3.new(-1, 0, 0) },
	Back = { Vector3.new(0, 0, 1), Vector3.new(1, 0, 0) },
	Left = { Vector3.new(-1, 0, 0), Vector3.new(0, 0, 1) },
	Right = { Vector3.new(1, 0, 0), Vector3.new(0, 0, -1) },
}
-- Отрезок from→to (без последних 2 %) пересекает повёрнутый брусок?
local function crosses(brick, from, to): boolean
	local o = brick.cframe:PointToObjectSpace(from)
	local d = brick.cframe:VectorToObjectSpace(to - from)
	local half = brick.size / 2
	local t0, t1 = 0, 0.98
	for _, axis in { "X", "Y", "Z" } do
		local oa, da, h = o[axis], d[axis], half[axis]
		if math.abs(da) < 1e-9 then
			if oa < -h or oa > h then
				return false
			end
		else
			local a, b = (-h - oa) / da, (h - oa) / da
			if a > b then
				a, b = b, a
			end
			t0, t1 = math.max(t0, a), math.min(t1, b)
			if t0 > t1 then
				return false
			end
		end
	end
	return true
end
local byName, poles, boards = {}, {}, {}
for _, brick in flea do
	if brick.name then
		byName[brick.name] = brick
		if brick.name == "RarityPole" then
			table.insert(poles, brick)
		elseif brick.name:sub(1, 5) == "Sign_" then
			table.insert(boards, brick)
		end
	end
end
local textOf = {}
for _, sign in signs do
	textOf[sign.name] = sign.text
end
local rarityText = {}
for _, name in Env.Require("ReplicatedStorage.Shared.Config.Rarities").Names do
	rarityText[name] = true
end
local cameras = {}
for x = -30, 30, 15 do
	for z = -60, 45, 15 do
		for y = 8, 16, 4 do
			table.insert(cameras, frame * Vector3.new(x, y, z))
		end
	end
end
-- Доля из 15 точек грани, закрытых деталями list (кроме самой таблички), и кто закрыл.
local function hiddenShare(board, camera, center, n, r, up, width, list, who)
	local blocked = 0
	for i = -2, 2 do
		for j = -1, 1 do
			local point = center + r * (i * width * 0.2) + up * (j * board.size.Y * 0.3)
			for _, other in list do
				if other ~= board and crosses(other, camera, point) then
					blocked += 1
					who[textOf[other.name] or other.name] = true
					break
				end
			end
		end
	end
	return blocked / 15
end
local hiddenSigns, overlaps = {}, {}
for _, sign in signs do
	local board = byName[sign.name]
	for _, face in sign.faces do
		local axes = FACES[face.Name]
		local n, r = board.cframe:VectorToWorldSpace(axes[1]), board.cframe:VectorToWorldSpace(axes[2])
		local up = board.cframe.UpVector
		local center = board.cframe.Position + n * (math.abs(axes[1]:Dot(board.size)) / 2 + 0.01)
		local width = math.abs(axes[2]:Dot(board.size))
		local seen, bad, worst, byBoards = 0, 0, 0, 0
		local who = {}
		for _, camera in cameras do
			local away = camera - center
			if away.Unit:Dot(n) > SIGN_GRAZING and away.Magnitude < 70 then
				seen += 1
				local share = if rarityText[sign.text]
					then 0
					else hiddenShare(board, camera, center, n, r, up, width, poles, who)
				worst = math.max(worst, share)
				if share > SIGN_HIDDEN then
					bad += 1
				end
				if hiddenShare(board, camera, center, n, r, up, width, boards, {}) > SIGN_HIDDEN then
					byBoards += 1
				end
			end
		end
		if seen > 0 and (bad / seen > SIGN_BAD_SHARE or worst > SIGN_WORST) then
			table.insert(
				hiddenSigns,
				("«%s» %s: закрыта у %d из %d, до %.0f%%"):format(
					sign.text,
					face.Name,
					bad,
					seen,
					worst * 100
				)
			)
		end
		if byBoards > 0 then
			table.insert(overlaps, ("«%s» %d/%d"):format(sign.text, byBoards, seen))
		end
	end
end
check(
	#hiddenSigns == 0,
	"столбы редкостей не закрывают надписи с камеры игрока"
		.. (if #hiddenSigns > 0 then ": " .. table.concat(hiddenSigns, "; ") else "")
)
if #overlaps > 0 then
	print(
		"    для сведения — вывеска за вывеской (точек камеры): "
			.. table.concat(overlaps, ", ")
	)
end

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

--!nocheck
-- Проверка мира без Roblox Studio (Lune): декор зон 1 «Свалка», 2 «Барахолка» и 3 «Подземка» на плитах пола зон —
-- нет видимых пар совпадающих граней (World/FaceCheck, D36); у «Барахолки» (D44) и «Подземки» (D54) — части в
-- бюджете, света мало, круг площадки босса свободен (только плоский пол), в круге, куда босс заходит в бою, нет
-- ничего выше LOW, у каждой надписи есть табличка, надписи не закрыты столбами, 4 слота на площадке с разными
-- поворотами. Сквозные полосы (D66, MapLayout.Lane) свободны во всех 10 зонах (зоны 6–10 собираются так же, как в
-- WorldBuilder: декор ZoneDecor, дорожки, постаменты, столбики). Декор не зависит от Random, поэтому здесь он тот же,
-- что в игре. Запуск из корня репозитория: lune run scripts/lune/check_world.luau. Ошибка — код возврата 1.
-- Зависит от env, FaceCheck, MapLayout, GameConfig, Battle, Rarities, World/Models/* (Junkyard, FleaMarket,
-- SubwayStation, DesertOasis, GlacierHall, ZoneDecor, Tree).

local process = require("@lune/process")

local Env = require("./env")

local roblox = Env.roblox
local Vector3, CFrame, Vector2, Color3 = roblox.Vector3, roblox.CFrame, roblox.Vector2, roblox.Color3

local FaceCheck = Env.Require("ServerScriptService.Server.World.FaceCheck")
local MapLayout = Env.Require("ServerScriptService.Server.World.MapLayout")
local Junkyard = Env.Require("ServerScriptService.Server.World.Models.Junkyard")
local FleaMarket = Env.Require("ServerScriptService.Server.World.Models.FleaMarket")
local SubwayStation = Env.Require("ServerScriptService.Server.World.Models.SubwayStation")
local DesertOasis = Env.Require("ServerScriptService.Server.World.Models.DesertOasis")
local GlacierHall = Env.Require("ServerScriptService.Server.World.Models.GlacierHall")
local ZoneDecor = Env.Require("ServerScriptService.Server.World.Models.ZoneDecor")
local Tree = Env.Require("ServerScriptService.Server.World.Models.Tree")
local GameConfig = Env.Require("ReplicatedStorage.Shared.Config.GameConfig")

local Battle = Env.Require("ReplicatedStorage.Shared.Config.Battle")

local ZONE_PARTS = 1300 -- бюджет декора одной зоны (карта целиком ≤ 12 000; у «Барахолки» было 802 до D44)
local ZONE_LIGHTS = 10 -- «Барахолка»: по одному на павильон и сундук, 2 прожектора (у столбиков границы — свои)
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

local junkBricks, junkSigns = Junkyard.Zone()
local junk = placed(1, junkBricks)
local fleaBricks, fleaSigns = FleaMarket.Zone()
local flea = placed(2, fleaBricks)
local subwayBricks, subwaySigns = SubwayStation.Zone()
local subway = placed(3, subwayBricks)
local desertBricks, desertSigns = DesertOasis.Zone()
local desert = placed(4, desertBricks)
local glacierBricks, glacierSigns = GlacierHall.Zone()
local glacier = placed(5, glacierBricks)

-- Зоны без своего оформления (6–10) — как их собирает WorldBuilder.buildZone: декор ZoneDecor (у «Джунглей» ещё
-- деревья), дорожки ZoneDecor.Path (середина и сквозные полосы), постаменты на MapLayout.ArtSlots, столбики границы
-- на ±PylonX у входа. Кирпичи — в мировых координатах.
local function plainZone(index: number): { any }
	local zone = GameConfig.Zones[index]
	local frame = MapLayout.ZoneCFrame(index)
	local size = MapLayout.ZoneSize
	local accent = Color3.fromHex(zone.accent)
	local out = {}
	local function put(at, bricks: { any }, label: string)
		for _, brick in bricks do
			brick.cframe = at * brick.cframe
			brick.name = brick.name or label
			table.insert(out, brick)
		end
	end
	local decor = {}
	if zone.id == "Bank" then
		decor = ZoneDecor.Bank(size)
	elseif ZoneDecor[zone.id] then
		decor = ZoneDecor[zone.id]()
	end
	put(frame, decor, "Decor_" .. zone.id)
	put(frame, ZoneDecor.Path(size, accent), "Path")
	if zone.id == "Jungle" then
		-- места деревьев — как в WorldBuilder.buildZone
		for i, spot in { Vector2.new(-24, -14), Vector2.new(24, -4), Vector2.new(-24, 26), Vector2.new(24, 20) } do
			put(frame * CFrame.new(spot.X, 0, spot.Y) * CFrame.Angles(0, i, 0), Tree("L", 2), "Tree")
		end
	end
	if not MapLayout.Arenas[index] then
		for _, spot in MapLayout.ArtSlots do
			put(frame * CFrame.new(spot.X, 0, spot.Y), ZoneDecor.Pedestal(accent), "Pedestal")
		end
	end
	if index > 1 then
		-- габариты столбика — как в WorldBuilder.buildZone (светящийся куб — без столкновений)
		for _, x in { -MapLayout.PylonX, MapLayout.PylonX } do
			put(CFrame.new(x, MapLayout.Heights.Path, MapLayout.ZoneStartZ(index)), {
				{ size = Vector3.new(3, 1, 3), cframe = CFrame.new(0, 0.5, 0) },
				{ size = Vector3.new(1.6, 8, 1.6), cframe = CFrame.new(0, 5, 0) },
				{ size = Vector3.new(2.6, 0.4, 2.6), cframe = CFrame.new(0, 9, 0) },
				{ size = Vector3.new(2.2, 2.2, 2.2), cframe = CFrame.new(0, 10.3, 0), collide = false },
			}, "Pylon")
		end
	end
	return out
end

local plain = {}
for index = 6, #GameConfig.Zones do
	plain[index] = plainZone(index)
end

print("Грани (D36):")
local groups = {
	{ name = "Junk", bricks = junk },
	{ name = "Flea", bricks = flea },
	{ name = "Subway", bricks = subway },
	{ name = "Desert", bricks = desert },
	{ name = "Glacier", bricks = glacier },
}
local floors = {}
for index = 1, #GameConfig.Zones do
	table.insert(floors, floorOf(index))
	if plain[index] then
		table.insert(groups, { name = ("Zone%d_%s"):format(index, GameConfig.Zones[index].id), bricks = plain[index] })
	end
end
table.insert(groups, { name = "Floor", bricks = floors })
local pairsCount, found = FaceCheck.Scan(Env.FakeRoot(groups))
for key, group in found do
	print(("    %s: %d (%s)"):format(key, group.n, group.example))
end
check(pairsCount == 0, ("видимых пар совпадающих граней: %d"):format(pairsCount))
-- то же для повёрнутых брусков, клиньев и торцов цилиндров (вывески под наклоном, ромбы, диски)
local anyCount, anyFound = FaceCheck.ScanAny(Env.FakeRoot(groups))
for key, group in anyFound do
	print(("    ∠ %s: %d (%s)"):format(key, group.n, group.example))
end
check(
	anyCount == 0,
	("видимых пар совпадающих граней под углом и у дисков: %d"):format(
		anyCount
	)
)

-- Проверки зоны с площадкой босса: zone — номер, flea — кирпичи в мировых координатах, fleaBricks — в координатах
-- зоны, signs — надписи (имена переменных — от первой такой зоны, «Барахолки»).
local function checkArenaZone(zone: number, title: string, flea: { any }, fleaBricks: { any }, signs: { any })
	print(title .. ":")
	check(#flea <= ZONE_PARTS, ("частей декора: %d из %d"):format(#flea, ZONE_PARTS))

	local lights = 0
	for _, brick in fleaBricks do
		if brick.light then
			lights += 1
		end
	end
	check(
		lights <= ZONE_LIGHTS,
		("источников света: %d (не больше %d)"):format(lights, ZONE_LIGHTS)
	)

	-- Круг площадки — только плоский пол: бою ничего не мешает. Локальные координаты зоны: начало — центр пола.
	local arena = MapLayout.Arenas[zone]
	local frame = MapLayout.ZoneCFrame(zone)
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
		-- Предмет на подушке (Arenas.top выше FLAT): подушка — тоже пол площадки.
		if inside and p.Y + halfY > math.max(FLAT, arena.top) + 1e-3 and p.Y - halfY < 12 then
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
	local bossCfg = Battle.Bosses[zone] or Battle.Bosses[2] -- у босса 3 числа боя — на шаге E (те же базовые)
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
		if point.zone == zone then
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
		("слотов босса %d на площадке (высота %.2f): %d из 4"):format(
			zone,
			arena.top,
			#points
		)
	)
	check(distinct == 4, ("разных поворотов предметов: %d из 4"):format(distinct))
end

checkArenaZone(1, "Свалка", junk, junkBricks, junkSigns)
checkArenaZone(2, "Барахолка", flea, fleaBricks, fleaSigns)
checkArenaZone(3, "Подземка", subway, subwayBricks, subwaySigns)
checkArenaZone(4, "Пустыня", desert, desertBricks, desertSigns)
checkArenaZone(5, "Ледник", glacier, glacierBricks, glacierSigns)

-- «Храм спящего Сфинкса» (D60): по обе стороны от арены и храма — свободный путь к следующей зоне вдоль всей зоны
-- (полосы |x| DesertOasis.Lane): ни одной твёрдой детали выше пола (0.3 — мощение) и ниже 7 (листья пальм выше
-- головы не мешают) и обход храма за его крыльями (DesertOasis.Bypass); храм и всё высокое — вне круга боя.
do
	local lane, bypass = DesertOasis.Lane, DesertOasis.Bypass
	local frame = MapLayout.ZoneCFrame(4) -- кирпичи уже в мировых координатах (placed): обратно в координаты зоны
	local blocked, around = {}, {}
	for _, brick in desert do
		if brick.collide ~= false then
			local cf, size = frame:ToObjectSpace(brick.cframe), brick.size
			local function half(axis: string): number
				return (
					math.abs(cf.RightVector[axis]) * size.X
					+ math.abs(cf.UpVector[axis]) * size.Y
					+ math.abs(cf.LookVector[axis]) * size.Z
				) / 2
			end
			local p = cf.Position
			-- |x| детали — от lo до hi (у детали через ось lo < 0)
			local lo, hi = math.abs(p.X) - half("X"), math.abs(p.X) + half("X")
			local solid = p.Y - half("Y") < 7 and p.Y + half("Y") > 0.3
			if solid and hi > lane[1] and lo < lane[2] then
				table.insert(blocked, ("%s (%.1f, %.1f, %.1f)"):format(brick.name or "Brick", p.X, p.Y, p.Z))
			end
			-- обход храма: полоса за крыльями до выхода зоны
			if
				solid
				and hi > bypass[1]
				and lo < bypass[2]
				and p.Z + half("Z") > bypass[3]
				and p.Z - half("Z") < bypass[4]
			then
				table.insert(around, ("%s (%.1f, %.1f, %.1f)"):format(brick.name or "Brick", p.X, p.Y, p.Z))
			end
		end
	end
	check(
		#blocked == 0,
		("Пустыня: путь |x| %d–%d вдоль зоны свободен"):format(lane[1], lane[2])
			.. (if #blocked > 0 then ": " .. table.concat(blocked, "; ", 1, math.min(#blocked, 5)) else "")
	)
	check(
		#around == 0,
		("Пустыня: обход храма |x| %.1f–%d (z %d–%.1f) к следующей зоне свободен"):format(
			bypass[1],
			bypass[2],
			bypass[3],
			bypass[4]
		) .. (if #around > 0 then ": " .. table.concat(around, "; ", 1, math.min(#around, 5)) else "")
	)
end

-- Пути от босса к следующему уровню (запрос владельца 2026-11-14): на видимых дорожках «Барахолки» (в обход горы
-- сокровищ к выходу) и «Подземки» (по бокам: от входа к площадке и от неё к выходу в обход киоска) нет твёрдых деталей
-- выше пола (0.3) и ниже 7.
local function pathFree(zone: number, title: string, bricks: { any }, u0: number, u1: number, z0: number, z1: number)
	local frame = MapLayout.ZoneCFrame(zone)
	local blocked = {}
	for _, brick in bricks do
		if brick.collide ~= false then
			local cf, size = frame:ToObjectSpace(brick.cframe), brick.size
			local function half(axis: string): number
				return (
					math.abs(cf.RightVector[axis]) * size.X
					+ math.abs(cf.UpVector[axis]) * size.Y
					+ math.abs(cf.LookVector[axis]) * size.Z
				) / 2
			end
			local p = cf.Position
			local lo, hi = math.abs(p.X) - half("X"), math.abs(p.X) + half("X")
			local solid = p.Y - half("Y") < 7 and p.Y + half("Y") > 0.3
			if solid and hi > u0 and lo < u1 and p.Z + half("Z") > z0 and p.Z - half("Z") < z1 then
				table.insert(blocked, ("%s (%.1f, %.1f, %.1f)"):format(brick.name or "Brick", p.X, p.Y, p.Z))
			end
		end
	end
	check(
		#blocked == 0,
		("%s: путь |x| %.1f–%.1f (z %.1f–%.1f) к следующему уровню свободен"):format(
			title,
			u0,
			u1,
			z0,
			z1
		) .. (if #blocked > 0 then ": " .. table.concat(blocked, "; ", 1, math.min(#blocked, 5)) else "")
	)
end
do
	local exit = FleaMarket.Exit
	local back = MapLayout.BossSpot.Y + MapLayout.Arenas[2].radius + 3
	pathFree(2, "Барахолка", flea, exit.inner, exit.outer, back + 2, MapLayout.ZoneSize / 2)
	pathFree(2, "Барахолка", flea, 0, exit.inner, back, back + 6)
	local way = SubwayStation.Way
	pathFree(3, "Подземка", subway, way.inner, way.outer, -MapLayout.ZoneSize / 2, MapLayout.ZoneSize / 2)
end

-- Скалы у стен обрыва (D60): с твёрдой детали у стен (|x| > 76) не допрыгнуть до кромки обрыва (верх травы 32.7 над
-- полом зоны, прыжок ≈ 6.4) — верх твёрдой детали не выше 24; верхние ярусы скал — без столкновений.
do
	local frame = MapLayout.ZoneCFrame(4)
	local high = {}
	for _, brick in desert do
		if brick.collide ~= false then
			local cf, size = frame:ToObjectSpace(brick.cframe), brick.size
			local halfX = (
				math.abs(cf.RightVector.X) * size.X
				+ math.abs(cf.UpVector.X) * size.Y
				+ math.abs(cf.LookVector.X) * size.Z
			) / 2
			local halfY = (
				math.abs(cf.RightVector.Y) * size.X
				+ math.abs(cf.UpVector.Y) * size.Y
				+ math.abs(cf.LookVector.Y) * size.Z
			) / 2
			local p = cf.Position
			if math.abs(p.X) + halfX > 76 and p.Y + halfY > 24 then
				table.insert(high, ("%s (%.1f, %.1f, %.1f)"):format(brick.name or "Brick", p.X, p.Y + halfY, p.Z))
			end
		end
	end
	check(
		#high == 0,
		"Пустыня: у стен нет твёрдых уступов выше 24 (за кромку обрыва не запрыгнуть)"
			.. (if #high > 0 then ": " .. table.concat(high, "; ", 1, math.min(#high, 5)) else "")
	)
end

-- «Ледник» (D64): видимые пути GlacierHall.Paths (от входа к площадке и от неё к выходу в обход ледника) свободны —
-- вдоль отрезка в полосе его ширины нет твёрдых деталей выше порога 1.1 (площадка, плиты и уступ — шагом) и ниже 7; у
-- стен обрыва (|x| > 76) верх твёрдых деталей не выше 24 (за кромку обрыва не запрыгнуть).
do
	local frame = MapLayout.ZoneCFrame(5)
	local blocked, high = {}, {}
	for _, brick in glacier do
		if brick.collide ~= false then
			local cf, size = frame:ToObjectSpace(brick.cframe), brick.size
			local function half(axis: string): number
				return (
					math.abs(cf.RightVector[axis]) * size.X
					+ math.abs(cf.UpVector[axis]) * size.Y
					+ math.abs(cf.LookVector[axis]) * size.Z
				) / 2
			end
			local p = cf.Position
			local hx, hy, hz = half("X"), half("Y"), half("Z")
			if p.Y - hy < 7 and p.Y + hy > 1.1 then
				for _, seg in GlacierHall.Paths do
					local a, b, w = Vector2.new(seg[1], seg[2]), Vector2.new(seg[3], seg[4]), seg[5]
					local hit = false
					for k = 0, 40 do
						local q = a:Lerp(b, k / 40)
						local dx = math.max(math.abs(q.X - p.X) - hx, 0)
						local dz = math.max(math.abs(q.Y - p.Z) - hz, 0)
						if dx * dx + dz * dz < (w / 2) ^ 2 then
							hit = true
						end
					end
					if hit then
						table.insert(blocked, ("%s (%.1f, %.1f, %.1f)"):format(brick.name or "Brick", p.X, p.Y, p.Z))
						break
					end
				end
			end
			if math.abs(p.X) + hx > 76 and p.Y + hy > 24 then
				table.insert(high, ("%s (%.1f, %.1f, %.1f)"):format(brick.name or "Brick", p.X, p.Y + hy, p.Z))
			end
		end
	end
	check(
		#blocked == 0,
		("Ледник: пути к площадке и к выходу (%d) свободны"):format(
			#GlacierHall.Paths
		) .. (if #blocked > 0 then ": " .. table.concat(blocked, "; ", 1, math.min(#blocked, 5)) else "")
	)
	check(
		#high == 0,
		"Ледник: у стен нет твёрдых уступов выше 24"
			.. (if #high > 0 then ": " .. table.concat(high, "; ", 1, math.min(#high, 5)) else "")
	)
end

-- Сквозные полосы (D66): во всех зонах в полосах |x| MapLayout.Lane по всей длине зоны нет твёрдых деталей на
-- высоте MapLayout.LaneHeight над полом. У стен обрыва (|x| > 76) зон 1–2 верх твёрдого не выше 24 (у зон 4–5 —
-- выше; стены станции зоны 3 так задуманы), декор зон 1–2 не уходит в стену обрыва (|x| ≤ ZoneHalfWidth).
local LANE, LANE_Y = MapLayout.Lane, MapLayout.LaneHeight

-- Центр детали в координатах зоны и половины её габарита по осям зоны.
local function inZone(frame, brick)
	local cf, size = frame:ToObjectSpace(brick.cframe), brick.size
	local function half(axis: string): number
		return (
			math.abs(cf.RightVector[axis]) * size.X
			+ math.abs(cf.UpVector[axis]) * size.Y
			+ math.abs(cf.LookVector[axis]) * size.Z
		) / 2
	end
	return cf.Position, half("X"), half("Y"), half("Z")
end

local function listed(items: { string }): string
	return if #items > 0 then ": " .. table.concat(items, "; ", 1, math.min(#items, 6)) else ""
end

local function laneFree(index: number, title: string, bricks: { any })
	local frame = MapLayout.ZoneCFrame(index)
	local length = MapLayout.ZoneSize / 2
	local blocked = {}
	for _, brick in bricks do
		if brick.collide ~= false then
			local p, hx, hy, hz = inZone(frame, brick)
			local lo, hi = math.abs(p.X) - hx, math.abs(p.X) + hx
			if
				p.Y - hy < LANE_Y[2]
				and p.Y + hy > LANE_Y[1]
				and hi > LANE[1] + 1e-3
				and lo < LANE[2] - 1e-3
				and p.Z + hz > -length
				and p.Z - hz < length
			then
				table.insert(blocked, ("%s (%.1f, %.1f, %.1f)"):format(brick.name or "Brick", p.X, p.Y, p.Z))
			end
		end
	end
	check(
		#blocked == 0,
		("%s: сквозные полосы |x| %d–%d свободны (высота %.1f–%d)"):format(
			title,
			LANE[1],
			LANE[2],
			LANE_Y[1],
			LANE_Y[2]
		) .. listed(blocked)
	)
end

local function nearWalls(index: number, title: string, bricks: { any })
	local frame = MapLayout.ZoneCFrame(index)
	local high, deep = {}, {}
	for _, brick in bricks do
		local p, hx, hy = inZone(frame, brick)
		if brick.collide ~= false and math.abs(p.X) + hx > 76 and p.Y + hy > 24 then
			table.insert(high, ("%s (%.1f, %.1f, %.1f)"):format(brick.name or "Brick", p.X, p.Y + hy, p.Z))
		end
		if math.abs(p.X) + hx > MapLayout.ZoneHalfWidth + 1e-3 then
			table.insert(deep, ("%s (%.1f, %.1f, %.1f)"):format(brick.name or "Brick", p.X, p.Y, p.Z))
		end
	end
	check(#high == 0, title .. ": у стен нет твёрдых уступов выше 24" .. listed(high))
	check(
		#deep == 0,
		("%s: декор не уходит в стену обрыва (|x| ≤ %d)"):format(
			title,
			MapLayout.ZoneHalfWidth
		) .. listed(deep)
	)
end

print("Сквозные полосы (D66):")
local titled = {
	{ 1, "Свалка", junk },
	{ 2, "Барахолка", flea },
	{ 3, "Подземка", subway },
	{ 4, "Пустыня", desert },
	{ 5, "Ледник", glacier },
}
for index = 6, #GameConfig.Zones do
	table.insert(titled, { index, GameConfig.Zones[index].name, plain[index] })
end
for _, entry in titled do
	laneFree(entry[1], entry[2], entry[3])
end
nearWalls(1, "Свалка", junk)
nearWalls(2, "Барахолка", flea)

-- Для сведения: части декора по зонам (у 6–10 — с дорожками, постаментами и столбиками; карта целиком ≤ 12 000
-- вместе с обрывами, лавками и музеями).
local counts, total = {}, 0
for _, entry in titled do
	table.insert(counts, ("%d: %d"):format(entry[1], #entry[3]))
	total += #entry[3]
end
print(("    частей в зонах (%s), всего %d"):format(table.concat(counts, ", "), total))

if failed > 0 then
	print(("Проверок не прошло: %d"):format(failed))
	process.exit(1)
end
print("Все проверки мира прошли")

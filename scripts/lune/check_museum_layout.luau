--!nocheck
-- Проверка раскладки музея D48-C без Roblox Studio (Lune): 20 мест с уровнями открытия max(6, 2 × уровень), места не
-- налезают друг на друга и стоят внутри зала или галереи, зоны защиты не задевают постаменты, проходы и лазеры, модули
-- Blender есть на каждом уровне. Источник — Config/MuseumLayout (генерирует scripts/d48_to_luau.py).
-- Запуск из корня репозитория: lune run scripts/lune/check_museum_layout.luau. Ошибка — код возврата 1.

local process = require("@lune/process")

local Env = require("./env")

local MuseumLayout = Env.Require("ReplicatedStorage.Shared.Config.MuseumLayout")
local Plaque = Env.Require("ServerScriptService.Server.World.Plaque")

local failed = 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if not ok then
		failed += 1
	end
end

local L = MuseumLayout
local places = L.Places
local hall, gallery = L.Hall, L.Gallery

print("Места:")
check(#places == 20, ("мест: %d из 20"):format(#places))
local slotsOk = true
for i, place in places do
	slotsOk = slotsOk and place.slot == i
end
check(slotsOk, "номера мест 1…20 по порядку")

-- Открытие: место n открыто на уровне, где max(6, 2 × уровень) ≥ n.
local unlockOk = true
for _, place in places do
	local first = nil
	for level = 1, 10 do
		if math.max(6, 2 * level) >= place.slot then
			first = level
			break
		end
	end
	unlockOk = unlockOk and place.unlock == first
end
check(unlockOk, "уровень открытия каждого места = max(6, 2 × уровень)")

local galleryOk = true
for _, place in places do
	if place.zone == "Gallery" then
		galleryOk = galleryOk and place.unlock >= gallery.Level
	end
end
check(
	galleryOk,
	("места галерей открываются не раньше уровня %d (галереи строятся с него)"):format(
		gallery.Level
	)
)

-- Постаменты не налезают: основание Base × Base, между краями не меньше 0.5.
local base = L.Showcase.Base
local closest = math.huge
for i = 1, #places do
	for j = i + 1, #places do
		local a, b = places[i].center, places[j].center
		local gap = math.max(math.abs(a.X - b.X), math.abs(a.Z - b.Z)) - base
		closest = math.min(closest, gap)
	end
end
check(
	closest >= 0.5,
	("зазор между основаниями постаментов ≥ 0.5 (наименьший %.2f)"):format(
		closest
	)
)

-- Внутри своего помещения с зазором от стен.
local function inside(place): boolean
	local c, h = place.center, base / 2
	if place.zone == "Hall" then
		return math.abs(c.X) + h <= hall.InnerX and c.Z - h >= hall.InnerZ0 and c.Z + h <= hall.InnerZ1 + 0.01
	end
	return math.abs(c.X) - h >= gallery.In
		and math.abs(c.X) + h <= gallery.InnerX
		and c.Z - h >= gallery.InnerZ0
		and c.Z + h <= gallery.InnerZ1 + 0.01
end
local insideOk = true
for _, place in places do
	insideOk = insideOk and inside(place)
end
check(insideOk, "каждый постамент внутри своего зала или галереи")

-- Лицо постамента — в проход (к центру музея по x).
local faceOk = true
for _, place in places do
	faceOk = faceOk and place.face.X == -math.sign(place.center.X) and place.face.Z == 0
end
check(faceOk, "постаменты смотрят в проход")

print("Зоны защиты:")
local function overlap(a, b): boolean
	return a[1] < b[2] and b[1] < a[2] and a[3] < b[4] and b[3] < a[4]
end
local plinthHits = {}
for _, rect in L.Defense.Allowed do
	for _, place in places do
		local c, h = place.center, base / 2
		if overlap(rect, { c.X - h, c.X + h, c.Z - h, c.Z + h }) then
			table.insert(plinthHits, place.slot)
		end
	end
end
check(#plinthHits == 0, "разрешённые зоны не заходят на постаменты")

local laserHits = 0
for _, rect in L.Defense.Allowed do
	for _, laser in L.Lasers do
		if overlap(rect, { -laser.length / 2, laser.length / 2, laser.z - 0.6, laser.z + 0.6 }) then
			laserHits += 1
		end
	end
end
check(laserHits == 0, "разрешённые зоны не на линиях лазеров")

local inHall = true
for _, rect in L.Defense.Allowed do
	inHall = inHall
		and rect[1] >= -hall.InnerX
		and rect[2] <= hall.InnerX
		and rect[3] >= hall.InnerZ0
		and rect[4] <= hall.InnerZ1
end
check(inHall, "разрешённые зоны — на полу главного зала")

local galleryRects = 0
for _, rect in L.Defense.GalleryForbidden do
	if math.min(math.abs(rect[1]), math.abs(rect[2])) >= gallery.In - 0.01 then
		galleryRects += 1
	end
end
check(galleryRects == 2, "обе галереи целиком в запрещённой зоне")

print("Лазеры и проходы:")
local function half(laser)
	return laser.length / 2
end
check(half(L.Lasers.Entrance) <= hall.DoorHalf + 0.01, "лазер «Вход» не шире проёма входа")
check(
	L.Lasers.Gallery.z > L.Lasers.Entrance.z and L.Lasers.Gallery.z < L.Pavilion.Z0,
	"лазер «Галерея» — между входом и павильоном"
)
check(
	L.Chest.Center.Z < gallery.Arch.Z0 or math.abs(L.Chest.Center.X) < hall.InnerX - 4,
	"сундук не в проёме арки"
)

print("Модули по уровням:")
local needed = { "D48_Hall", "D48_Roof", "D48_Pavilion", "D48_Stair", "D48_VaultShell", "D48_Chest" }
local modulesOk = true
for level = 1, 10 do
	local present = {}
	local plinths = 0
	for _, m in L.Modules do
		if level >= m.from and level <= m.to then
			present[m.model] = true
			if m.model == "D48_Plinth" then
				plinths += 1
			end
		end
	end
	for _, name in needed do
		modulesOk = modulesOk and present[name] == true
	end
	local expected = if level >= gallery.Level then 20 elseif level >= 4 then 8 else 6
	modulesOk = modulesOk and plinths == expected
	modulesOk = modulesOk and (present.D48_Gallery_L == true) == (level >= gallery.Level)
end
check(
	modulesOk,
	"на каждом уровне — зал, крыша, павильон, лестница, хранилище, сундук и нужное число постаментов"
)

-- ── Part-версия здания (World/Models/MuseumD48): у каждого модуля раскладки есть Part-версия, на каждом уровне
-- нет видимых пар совпадающих граней (D36) и деталей не больше бюджета (ТЗ: ≤ 400 на музей, считая обстановку
-- хранилища у владельца). Оси участка; вокруг — трава с проёмом под хранилищем, как в WorldBuilder.
local roblox = Env.roblox
local Vector3, CFrame = roblox.Vector3, roblox.CFrame
local FaceCheck = Env.Require("ServerScriptService.Server.World.FaceCheck")
local MuseumD48 = Env.Require("ServerScriptService.Server.World.Models.MuseumD48")
local GameConfig = Env.Require("ReplicatedStorage.Shared.Config.GameConfig")

local BUDGET = 400
local SHOWCASE = GameConfig.Museum.ShowcaseSize

print("Part-версия здания:")
local missing = {}
for _, m in L.Modules do
	if not MuseumD48.Has(m.model) then
		missing[m.model] = true
	end
end
check(next(missing) == nil, "у каждого модуля раскладки есть Part-версия")

local function boxBrick(x0, x1, y0, y1, z0, z1)
	return {
		size = Vector3.new(x1 - x0, y1 - y0, z1 - z0),
		cframe = CFrame.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
	}
end

-- Трава вокруг музея (верх — Hall.Ground) с проёмом по контуру зала.
local G = hall.Ground
local grass = {
	boxBrick(-60, 60, G - 2, G, -60, hall.Front),
	boxBrick(-60, 60, G - 2, G, hall.Back, 60),
	boxBrick(-60, -hall.HalfWidth, G - 2, G, hall.Front, hall.Back),
	boxBrick(hall.HalfWidth, 60, G - 2, G, hall.Front, hall.Back),
}

-- Кирпичи уровня level в осях участка: модули, тумбы мест с верхом, корпус сундука. server — без деталей вида
-- хранилища (их строит клиент владельца), vault — только они.
local function levelBricks(level: number): ({ any }, number, number)
	local all, server, vault = {}, 0, 0
	local plinthAt = {}
	for _, m in L.Modules do
		if level >= m.from and level <= m.to then
			local at = CFrame.new(m.position) * CFrame.Angles(0, math.rad(m.yaw), 0)
			for _, brick in MuseumD48.Module(m.model) do
				brick.cframe = at * brick.cframe
				table.insert(all, brick)
				if MuseumD48.VaultModules[m.model] and not brick.shell then
					vault += 1
				else
					server += 1
				end
			end
			if m.model == "D48_Plinth" then
				plinthAt[m.position] = true
			end
		end
	end
	for _, place in places do
		local standing = false
		for position in plinthAt do
			standing = standing or (position - place.center).Magnitude < 0.01
		end
		if standing then
			local center = place.center + Vector3.new(0, SHOWCASE.Y / 2, 0)
			local frame = CFrame.lookAt(center, center + place.face)
			table.insert(all, { name = "Showcase", size = SHOWCASE, cframe = frame })
			table.insert(all, {
				name = "Top",
				size = Vector3.new(4.6, 0.06, 4.6),
				cframe = frame * CFrame.new(0, SHOWCASE.Y / 2 + 0.03, 0),
			})
			-- D50: табличка и (у свободного места, худший случай) голограмма
			local plaque = Plaque.Parts(SHOWCASE)
			table.insert(all, { name = "Plaque", size = plaque.plate.size, cframe = frame * plaque.plate.offset })
			table.insert(all, { name = "FreeCube", size = plaque.cube.size, cframe = frame * plaque.cube.offset })
			server += 4
		end
	end
	local chest = GameConfig.Museum.ChestSize
	table.insert(
		all,
		{ name = "Chest", size = chest, cframe = CFrame.new(L.Chest.Center + Vector3.new(0, chest.Y / 2, 0)) }
	)
	server += 2 -- сундук и невидимая точка участка Floor
	return all, server, vault
end

local worst = { level = 0, total = 0 }
for level = 1, 10 do
	local bricks, server, vault = levelBricks(level)
	local count, found = FaceCheck.Scan(Env.FakeRoot({
		{ name = "Museum", bricks = bricks },
		{ name = "Grass", bricks = grass },
	}))
	if count > 0 then
		for key, group in found do
			print(("    ур. %d %s: %d (%s)"):format(level, key, group.n, group.example))
		end
	end
	check(count == 0, ("ур. %d: видимых пар совпадающих граней %d"):format(level, count))
	local total = server + vault
	if total > worst.total then
		worst = { level = level, total = total }
	end
	print(
		("    ур. %d: деталей на сервере %d, обстановка хранилища у владельца %d, всего %d"):format(
			level,
			server,
			vault,
			total
		)
	)
	check(total <= BUDGET, ("ур. %d: деталей %d из %d"):format(level, total, BUDGET))
end
print(("    больше всего — ур. %d: %d"):format(worst.level, worst.total))

if failed > 0 then
	print(("ИТОГ: ошибок %d"):format(failed))
	process.exit(1)
end
print("ИТОГ: ошибок нет")

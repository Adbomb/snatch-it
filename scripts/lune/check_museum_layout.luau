--!nocheck
-- Проверка раскладки музея D48-C без Roblox Studio (Lune): 20 мест с уровнями открытия max(6, 2 × уровень), места не
-- налезают друг на друга и стоят внутри зала или галереи, зоны защиты не задевают постаменты, проходы и лазеры, модули
-- Blender есть на каждом уровне. Источник — Config/MuseumLayout (генерирует scripts/d48_to_luau.py).
-- Запуск из корня репозитория: lune run scripts/lune/check_museum_layout.luau. Ошибка — код возврата 1.

local process = require("@lune/process")

local Env = require("./env")

local MuseumLayout = Env.Require("ReplicatedStorage.Shared.Config.MuseumLayout")

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

if failed > 0 then
	print(("ИТОГ: ошибок %d"):format(failed))
	process.exit(1)
end
print("ИТОГ: ошибок нет")

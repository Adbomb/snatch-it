-- Генератор этажа башни из «ДНК существа» (D74, решение владельца 2026-11-27: этаж — продолжение монстра, а не общая
-- архитектура с монстром внутри). Ручной темы нет: палитра, семья силуэта, главная черта и зона берутся из
-- Shared/FloorDna, комната — World/Models/ZoneRooms, собственные меши существа — заявки для World/MonsterParts.
-- Общий скелет одинаков у всех этажей (цельность башни): 4 колонны на общих осях, плиты одной толщины и одного
-- нейтрального тёмного цвета, по кромке — тонкий кант редкости (названия редкостей — только ярлык и кант).
-- Редкость = насколько этаж превращается в монстра (каждая ступень добавляет к предыдущей):
--   1 Деревянный — облицовка колонн по семье силуэта и перемычка в его цветах, подиум и комната — его дом,
--                  маленькая эмблема — голова существа в его цветах над стеклом;
--   2 Каменный   — + рельеф главной черты на передних колоннах;
--   3 Мраморный  — + капители: крупные скульптуры главной черты;
--   4 Золотой    — + золотой бюст над стеклом: собственная голова существа целиком в золоте (Foil), черты в золоте;
--   5 Мифический — + тело прорастает сквозь каркас: руки по бокам (до 4 стадов), хвост сзади, пояса на колоннах;
--   6 Алмазный   — этаж = монстр-дом: голова у верхней плиты (ниже неё), стекло — живот, колонны — ноги со ступнями,
--                  руки и выросты каркаса до 8 стадов, алмазные друзы.
-- Издалека (MonsterFloor.Far, от FloorRarity.FarDistance) этаж — сигнал РЕДКОСТИ, который видят все (владелец
-- 2026-11-27): каркас и плита в цвете редкости (Config/FloorRarity.Signal), монстр — только жилец в светлом окне;
-- Золотой и выше светятся (Neon — только как сигнал редкости; детали с именем Pulse пульсируют у клиента —
-- Controllers/FloorSignalController), у Мифического и Алмазного — выросты каркаса за след башни.
-- Облицовка колонн — 6 наборов на 9 семей силуэта (FAMILY_SET). Координаты — в осях этажа: начало — центр низа
-- плиты, перед — −Z. Зависит от ShowcaseKit, ZoneRooms, ShowcaseFloor (колпак), Shared/FloorDna, Config/CreatureRigs.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local CreatureRigs = require(ReplicatedStorage.Shared.Config.CreatureRigs)
local FloorRarity = require(ReplicatedStorage.Shared.Config.FloorRarity)
local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local FloorDna = require(ReplicatedStorage.Shared.FloorDna)
local Models = ServerScriptService.Server.World.Models
local Kit = require(Models.ShowcaseKit)
local ZoneRooms = require(Models.ZoneRooms)

local MonsterFloor = {}

local HX, HZ, SLAB, W = Kit.HX, Kit.HZ, Kit.SLAB, Kit.W
local box, tilt, cylZ, cylX, hex = Kit.box, Kit.tilt, Kit.cylZ, Kit.cylX, Kit.hex
local DECO = Kit.DECO

MonsterFloor.HeightFactor = { 1, 1.35, 1.6, 1.9, 2.3, 3 }
MonsterFloor.Budget = { 250, 300, 350, 400, 450, 500 }
MonsterFloor.FarBudget = 40

function MonsterFloor.Height(tier: number): number
	return math.floor(GameConfig.Tower.FloorHeight * MonsterFloor.HeightFactor[tier] + 0.5)
end

-- Общий скелет: нейтральные тёмные плиты; кант редкости — единственное, что берётся от названия редкости.
local SLAB_CORE, SLAB_BAND = hex("23252B"), hex("33363F")
local KANT = { hex("F0D29A"), hex("A7ABB3"), hex("F5F2EC"), Kit.GOLD, hex("B98CFF"), hex("F2FAFF") }
local KANT_GEM = hex("A8E0FF")
-- Свечение редкости (только Золотой и выше): пояс плиты, рёбра колонн, острия выростов; Pulse — пульсирует у клиента.
local NEON = { material = Enum.Material.Neon, collide = false, shadow = false }
local PULSE = { material = Enum.Material.Neon, collide = false, shadow = false, name = "Pulse" }
local GLASS_COLOR = hex("D6F0FF")
local WHITE, BLACK = Color3.new(1, 1, 1), Color3.new(0, 0, 0)

-- Набор облицовки колонн по семье силуэта.
local FAMILY_SET = {
	Biped = "Leg",
	Tall = "Leg",
	Wide = "Leg",
	Quadruped = "Hoof",
	Bird = "Talon",
	Aquatic = "Fin",
	Tentacle = "Fin",
	Blob = "Roll",
	Wheeled = "Wheel",
}
MonsterFloor.FamilySet = FAMILY_SET

local function shade(c: Color3, k: number): Color3
	return c:Lerp(BLACK, k)
end
local function tint(c: Color3, k: number): Color3
	return c:Lerp(WHITE, k)
end

local function signalOf(tier: number): any
	return FloorRarity.Signal[FloorRarity.Order[tier]]
end

local function slab(out, tier: number, y: number)
	local e = 0.6
	box(out, HX * 2, SLAB, HZ * 2, 0, y + SLAB / 2, 0, SLAB_CORE)
	local mid = y + SLAB / 2
	local function belt(depth: number, h: number, color: Color3, extra: any?)
		for _, s in { -1, 1 } do
			box(out, (HX + depth) * 2, h, depth, 0, mid, s * (HZ + depth / 2), color, extra)
			box(out, depth, h, HZ * 2, s * (HX + depth / 2), mid, 0, color, extra)
		end
	end
	belt(e, SLAB, SLAB_BAND)
	local signal = signalOf(tier)
	if signal.glow then -- Золотой и выше: кант светится — сигнал редкости
		belt(e + 0.16, 0.36, hex(signal.glow), if signal.pulse then PULSE else NEON)
	else
		belt(e + 0.16, 0.36, KANT[tier], DECO)
	end
	if tier == 6 then -- камни-ромбы по канту
		local turnZ, turnX = CFrame.Angles(0, 0, math.rad(45)), CFrame.Angles(math.rad(45), 0, 0)
		for k = -2, 2 do
			for _, s in { -1, 1 } do
				tilt(out, 0.75, 0.75, 0.3, CFrame.new(k * 8, mid, s * (HZ + e + 0.22)) * turnZ, KANT_GEM, Kit.GEM)
			end
		end
		for k = -1, 1 do
			for _, s in { -1, 1 } do
				tilt(out, 0.3, 0.75, 0.75, CFrame.new(s * (HX + e + 0.22), mid, k * 10) * turnX, KANT_GEM, Kit.GEM)
			end
		end
	end
end

-- Облицовка угловой колонны по набору семьи силуэта: «нога» существа в его цветах. Сечение не меньше W.
local function column(out, dna, sx: number, sz: number, y0: number, y1: number)
	local body, second, accent, foot = dna.palette[1], dna.palette[2], dna.palette[3], dna.foot
	local cx, cz = sx * (HX - W / 2), sz * (HZ - W / 2)
	local H = y1 - y0
	local set = FAMILY_SET[dna.family] or "Leg"
	local function lvl(side: number, h: number, y: number, color: Color3, extra: any?)
		box(out, side, h, side, cx, y + h / 2, cz, color, extra)
	end
	-- накладка на обеих наружных гранях: ширина along, высота tall, вынос proud от грани стороны side
	local function plate(side: number, along: number, tall: number, proud: number, yc: number, color: Color3)
		box(out, along, tall, proud, cx, yc, cz + sz * (side / 2 + proud / 2), color, DECO)
		box(out, proud, tall, along, cx + sx * (side / 2 + proud / 2), yc, cz, color, DECO)
	end
	if set == "Leg" then -- нога в обуви: подошва, башмак с носком, голень, колено, манжета
		lvl(W + 1.3, 0.4, y0, shade(foot, 0.45))
		lvl(W + 1.0, 1.7, y0 + 0.4, foot)
		plate(W + 1.0, W * 0.7, 1.1, 0.5, y0 + 0.95, tint(foot, 0.25))
		lvl(W + 0.2, H - 4.5, y0 + 2.1, body)
		lvl(W + 0.8, 1.1, y0 + H * 0.42, second)
		lvl(W + 0.6, 0.8, y1 - 2.4, accent)
		lvl(W + 0.9, 1.6, y1 - 1.6, second)
	elseif set == "Hoof" then -- четвероногий: копыто, пясть, колено, бедро с пятнами, плечо
		lvl(W + 0.9, 1.5, y0, shade(foot, 0.4))
		lvl(W, 2.3, y0 + 1.5, foot)
		lvl(W + 1.0, 1.7, y0 + 3.8, body)
		lvl(W + 0.2, H * 0.4, y0 + 5.5, body)
		lvl(W + 0.8, H * 0.6 - 7.0, y0 + 5.5 + H * 0.4, body)
		plate(W + 0.8, 1.6, 1.6, 0.15, y0 + 5.5 + H * 0.4 + (H * 0.6 - 7.0) * 0.35, second)
		plate(W + 0.8, 1.1, 1.1, 0.15, y0 + 5.5 + H * 0.4 + (H * 0.6 - 7.0) * 0.75, second)
		lvl(W + 1.1, 1.5, y1 - 1.5, second)
	elseif set == "Talon" then -- птица: три пальца с когтями, чешуйчатая цевка, ярусы перьев, воротник
		local toe = tint(foot, 0.1)
		box(out, 1.1, 0.8, 1.6, cx, y0 + 0.4, cz + sz * (W / 2 + 0.6), toe, DECO)
		box(out, 1.6, 0.8, 1.1, cx + sx * (W / 2 + 0.6), y0 + 0.4, cz, toe, DECO)
		local diag = CFrame.new(cx + sx * (W / 2 + 0.3), y0 + 0.4, cz + sz * (W / 2 + 0.3))
			* CFrame.Angles(0, math.rad(45 * sx * sz), 0)
		tilt(out, 1.1, 0.78, 1.7, diag, toe, DECO)
		lvl(W + 0.5, 0.9, y0, shade(foot, 0.2))
		local legTop = y0 + H * 0.52
		lvl(W, legTop - y0 - 0.9, y0 + 0.9, foot)
		for k = 1, 3 do
			lvl(W + 0.28, 0.3, y0 + 0.9 + (legTop - y0 - 0.9) * k / 4, shade(foot, 0.3), DECO)
		end
		local tier = (y1 - 1.1 - legTop) / 3
		lvl(W + 0.5, tier, legTop, body)
		lvl(W + 0.9, tier, legTop + tier, second)
		lvl(W + 1.2, tier, legTop + tier * 2, body)
		lvl(W + 0.8, 1.1, y1 - 1.1, accent)
	elseif set == "Fin" then -- водный: волна у подножия, гладкое тело со светлым брюшком, плавники на гранях
		lvl(W + 1.1, 1.0, y0, second)
		lvl(W + 0.6, 0.8, y0 + 1.0, tint(second, 0.35))
		lvl(W + 0.2, H - 3.2, y0 + 1.8, body)
		plate(W + 0.2, W * 0.55, H - 6, 0.14, y0 + H * 0.5, tint(body, 0.45))
		for k = 0, 2 do
			local fy = y0 + H * (0.24 + k * 0.24)
			box(out, 0.35, 2.6, 1.0, cx + sx * 1.0, fy, cz + sz * (W / 2 + 0.6), accent, DECO)
			box(out, 0.35, 1.5, 0.6, cx + sx * 1.0, fy + 2.0, cz + sz * (W / 2 + 0.4), accent, DECO)
			box(out, 1.0, 2.6, 0.35, cx + sx * (W / 2 + 0.6), fy, cz + sz * 1.0, accent, DECO)
			box(out, 0.6, 1.5, 0.35, cx + sx * (W / 2 + 0.4), fy + 2.0, cz + sz * 1.0, accent, DECO)
		end
		lvl(W + 0.9, 1.4, y1 - 1.4, second)
	elseif set == "Roll" then -- без ног: складки-валики
		local n = math.max(4, math.floor(H / 3.4))
		local seg = (H - 1.0) / n
		for k = 0, n - 1 do
			lvl(W + 1.0, seg * 0.62, y0 + seg * k, if k % 2 == 0 then body else tint(body, 0.12))
			lvl(W + 0.3, seg * 0.38, y0 + seg * k + seg * 0.62, second)
		end
		lvl(W + 0.8, 1.0, y1 - 1.0, accent)
	else -- "Wheel": колесо у подножия, корпус с заклёпочными поясами
		lvl(W + 0.6, 4.4, y0, shade(second, 0.25))
		cylZ(out, 2.0, 0.5, cx, y0 + 2.2, cz + sz * (W / 2 + 0.55), shade(foot, 0.5), DECO)
		cylZ(out, 0.8, 0.3, cx, y0 + 2.2, cz + sz * (W / 2 + 0.9), accent, DECO)
		cylX(out, 2.0, 0.5, cx + sx * (W / 2 + 0.55), y0 + 2.2, cz, shade(foot, 0.5), DECO)
		cylX(out, 0.8, 0.3, cx + sx * (W / 2 + 0.9), y0 + 2.2, cz, accent, DECO)
		lvl(W + 0.2, H - 6.0, y0 + 4.4, body)
		for k = 1, math.max(1, math.floor(H / 9)) do
			lvl(W + 0.5, 0.5, y0 + 4.4 + (H - 6.0) * k / (math.floor(H / 9) + 1), second, DECO)
		end
		lvl(W + 0.9, 1.6, y1 - 1.6, second)
	end
end

-- Высота перемычки над стеклом: эмблема (1–3), золотой бюст (4–5), голова (6 — по высоте головы).
local function lintelOf(tier: number, headTall: number): number
	return if tier <= 3 then 2.6 elseif tier <= 5 then 6.8 else headTall + 0.6
end

-- Цельное стекло фасада и боков, порог и перемычка в цветах монстра; задняя стена — его «спина».
local function glazing(out, dna, y0: number, y1: number, lintel: number, niche: boolean)
	local body, second = dna.palette[1], dna.palette[2]
	local sill = 0.7
	local function run(alongX: boolean, half: number, fixed: number, tall: number)
		local function put(sa: number, sy: number, sd: number, y: number, color: Color3, extra: any?)
			if alongX then
				box(out, sa, sy, sd, 0, y, fixed, color, extra)
			else
				box(out, sd, sy, sa, fixed, y, 0, color, extra)
			end
		end
		local g0, g1 = y0 + sill, y1 - 0.4 - tall
		put(half * 2, sill, 0.8, y0 + sill / 2, shade(body, 0.4))
		put(half * 2, tall, 0.9, y1 - 0.4 - tall / 2, if niche and alongX then shade(body, 0.45) else body)
		put(half * 2, 0.34, 1.1, g1 + 0.05, second, DECO)
		put(half * 2, g1 - g0, 0.2, (g0 + g1) / 2, GLASS_COLOR, Kit.GLASS)
	end
	run(true, HX - W + 0.4, -HZ + 1.0, lintel)
	run(false, HZ - W + 0.4, -HX + 1.0, math.min(lintel, 2.6))
	run(false, HZ - W + 0.4, HX - 1.0, math.min(lintel, 2.6))
	local half = HX - W + 0.4
	box(out, half * 2, y1 - y0 - 0.45, 0.5, 0, (y0 + y1 - 0.45) / 2, HZ - 0.45, shade(body, 0.18))
	for _, x in { -8, 0, 8 } do
		box(out, 2.4, y1 - y0 - 1.4, 0.25, x, (y0 + y1 - 0.45) / 2, HZ - 0.075, second, DECO)
	end
end

-- Собственные части существа: заявки для MonsterParts. size — габарит части в осях скелета.
local function sizeOf(rig: any, name: string?): Vector3?
	local spec = name and rig.Parts[name]
	return if spec and not spec.hidden then spec.size else nil
end

-- Часть с мордой: голова, а у кого морда на теле — тело.
local function facePart(rig: any, dna): string?
	if dna.head then
		return dna.head
	end
	return if rig.Parts.Body and not rig.Parts.Body.hidden then "Body" else nil
end

-- Заявки на часть name и всё, что к ней крепится (глаза, уши, шляпа — потомки в скелете): центр части — at, множитель
-- k; потомки встают на свои места относительно неё. Так голова получается целиком, а не «лысой».
local RIG_FACE = CFrame.Angles(0, math.pi, 0) -- скелет смотрит в +Z, этаж — в −Z
local function group(requests, rig: any, name: string, at: CFrame, k: number, gold: boolean?)
	local root = rig.Parts[name]
	local origin = root.pivot + root.center
	for _, other in rig.Order do
		local spec = rig.Parts[other]
		local up, inside = other, false
		while up do
			if up == name then
				inside = true
				break
			end
			up = rig.Parts[up] and rig.Parts[up].parent
		end
		if inside and not spec.hidden and spec.role ~= "stand" then
			local offset = RIG_FACE * ((spec.pivot + spec.center - origin) * k)
			table.insert(requests, { part = other, at = at * CFrame.new(offset), scale = k, gold = gold })
		end
	end
end

-- Габарит части вместе с потомками (в осях скелета, от центра самой части): размер и сдвиг центра.
local function groupSize(rig: any, name: string): (Vector3, Vector3)
	local root = rig.Parts[name]
	local origin = root.pivot + root.center
	local lo, hi = -root.size / 2, root.size / 2
	for _, other in rig.Order do
		local spec = rig.Parts[other]
		local up, inside = spec.parent, false
		while up do
			if up == name then
				inside = true
				break
			end
			up = rig.Parts[up] and rig.Parts[up].parent
		end
		if inside and not spec.hidden then
			local c = spec.pivot + spec.center - origin
			lo = lo:Min(c - spec.size / 2)
			hi = hi:Max(c + spec.size / 2)
		end
	end
	return hi - lo, (hi + lo) / 2
end

-- Выросты каркаса за след башни (Мифический — до 4 стадов на сторону, Алмазный — до 8; соседние башни — через 75):
-- ступенчатые контрфорсы у колонн по бокам (±X), в своей полосе высоты, с остриём. zs — у каких колонн (−1 —
-- передние, 1 — задние).
local function growths(
	out,
	tier: number,
	y0: number,
	y1: number,
	zs: { number },
	main: Color3,
	mainExtra: any,
	tip: Color3,
	tipExtra: any
)
	local reach = signalOf(tier).spread or 0
	if reach <= 0 then
		return
	end
	local H = y1 - y0
	local inner = HX - 0.55 -- начинается внутри колонны
	local outer = HX + reach - 0.1
	local turn = CFrame.Angles(0, math.rad(45), 0)
	for _, sx in { -1, 1 } do
		for _, sz in zs do
			local cz = sz * (HZ - W / 2)
			local base = y0 + H * 0.11
			local lowH, upH = H * 0.41, H * 0.24
			local mid = inner + (outer - inner) * 0.52
			box(out, outer - inner, lowH, W - 0.7, sx * (inner + outer) / 2, base + lowH / 2, cz, main, mainExtra)
			box(out, mid - inner, upH, W - 1.3, sx * (inner + mid) / 2, base + lowH + upH / 2, cz, main, mainExtra)
			local tipR = math.min(1.7, reach * 0.22)
			local tipH = H * 0.19
			tilt(
				out,
				tipR,
				tipH,
				tipR,
				CFrame.new(sx * (outer - tipR * 0.75), base + lowH + tipH / 2 - 0.25, cz) * turn,
				tip,
				tipExtra
			)
		end
	end
end

-- Высота головы монстра-дома (Алмазный) и её множитель: ширина до 21, высота и глубина до 17.
local function headScale(rig: any, dna): (number, number)
	local size = sizeOf(rig, facePart(rig, dna))
	if not size then
		return 0, 0
	end
	local k = math.min(21 / size.X, 17 / size.Y, 17 / size.Z)
	return k, size.Y * k
end

-- Рельеф, эмблема, капители, руки, хвост, ступни, голова — по редкости. far — только то, что видно издалека.
local function monsterParts(out, requests, dna, rig, tier: number, y0: number, y1: number, lintel: number, far: boolean)
	local H = y1 - y0
	local body, second, accent = dna.palette[1], dna.palette[2], dna.palette[3]
	local gold = tier >= 4
	local feature = dna.feature
	local function featureFor(sx: number): (string?, Vector3?)
		local name = if sx > 0 and dna.featurePair then dna.featurePair else feature
		return name, sizeOf(rig, name)
	end
	local zf = -HZ + 1.0 - 0.45
	for _, sx in { -1, 1 } do
		local cx, cz = sx * (HX - W / 2), -(HZ - W / 2)
		local name, size = featureFor(sx)
		if name and size then
			if tier >= 2 and not far then -- рельеф главной черты на передних колоннах
				local k = 2.6 / math.max(size.X, size.Y, size.Z)
				box(out, W - 0.4, size.Y * k + 0.8, 0.2, cx, y0 + H * 0.5, cz - W / 2 - 0.2, second, DECO)
				table.insert(requests, {
					part = name,
					at = CFrame.new(cx, y0 + H * 0.5, cz - W / 2 - 0.25 - size.Z * k * 0.3),
					scale = k,
					gold = gold,
				})
			end
			if tier >= 3 then -- капители: крупные скульптуры главной черты на консолях
				local k = math.min(5.0 / math.max(size.X, size.Y), 3.4 / size.Z)
				local yc = y1 - 0.5 - size.Y * k / 2
				if not far then
					box(out, W + 0.4, 0.7, 2.2, cx, yc - size.Y * k / 2 - 0.35, cz - W / 2 - 0.6, second, DECO)
				end
				table.insert(requests, {
					part = name,
					at = CFrame.new(cx, yc, cz - W / 2 - size.Z * k / 2 + 0.7),
					scale = k,
					gold = gold,
				})
				if not far then
					box(out, W + 0.4, 0.7, 2.2, cx, yc - size.Y * k / 2 - 0.35, -cz + W / 2 + 0.6, second, DECO)
					table.insert(requests, {
						part = name,
						at = CFrame.new(cx, yc, -cz + W / 2 + size.Z * k / 2 - 0.7) * CFrame.Angles(0, math.pi, 0),
						scale = k,
						gold = gold,
					})
				end
			end
		end
	end
	local face = facePart(rig, dna)
	local faceSize = sizeOf(rig, face)
	if tier <= 3 and face and faceSize and not far then -- эмблема: голова существа в его цветах над стеклом
		local yc = y1 - 0.4 - lintel / 2
		cylZ(out, 1.75, 0.3, 0, yc, zf - 0.15, accent, DECO)
		cylZ(out, 1.5, 0.5, 0, yc, zf - 0.25, second, DECO)
		local whole, shift = groupSize(rig, face)
		local k = math.min(2.5 / math.max(whole.X, whole.Y), 0.85 / whole.Z)
		local centre = Vector3.new(0, yc, zf - 0.35 - whole.Z * k / 2) - RIG_FACE * (shift * k)
		group(requests, rig, face, CFrame.new(centre), k)
	end
	if (tier == 4 or tier == 5) and face and faceSize and not far then
		-- золотой бюст: собственная голова существа целиком в золоте (Foil), в нише перемычки на золотой полке;
		-- за общий след башни не выходит (перед — не дальше кромки плиты)
		local whole, shift = groupSize(rig, face)
		local k = math.min(12 / whole.X, (lintel - 1.1) / whole.Y, 5.4 / whole.Z)
		local yc = y1 - 0.4 - lintel / 2 + 0.25
		local front = -HZ - 0.6
		local centre = Vector3.new(0, yc, front + whole.Z * k / 2) - RIG_FACE * (shift * k)
		box(out, whole.X * k + 2.2, lintel - 0.5, 0.2, 0, y1 - 0.4 - lintel / 2, zf - 0.1, shade(body, 0.55), DECO)
		box(out, whole.X * k + 1.2, 0.5, 1.5, 0, yc - whole.Y * k / 2 - 0.25, -HZ + 0.15, Kit.GOLD2, DECO)
		group(requests, rig, face, CFrame.new(centre), k, true)
	end
	local arms = if #dna.limbs.arm > 0 then dna.limbs.arm else { feature, dna.featurePair or feature }
	if tier >= 5 then -- тело прорастает сквозь каркас: руки по бокам, хвост сзади, пояса на колоннах
		local reach = signalOf(tier).spread or 4 -- вынос за след башни: Мифический — 4, Алмазный — 8
		local tall = if tier == 6 then 15 else 8.5
		for i, sx in { -1, 1 } do
			local name = arms[i] or arms[1]
			local size = sizeOf(rig, name)
			if name and size then
				local k = math.min(tall / size.Y, (reach + 0.5) / size.X, (if tier == 6 then 9 else 7) / size.Z)
				table.insert(requests, {
					part = name,
					at = CFrame.new(sx * (HX - 0.6 + size.X * k / 2), y0 + H * 0.46, -HZ + W / 2),
					scale = k,
				})
			end
		end
		local tail = dna.limbs.tail[1]
		local tailSize = sizeOf(rig, tail)
		if tail and tailSize and not far then
			local k = math.min(7 / math.max(tailSize.X, tailSize.Y), 5.5 / tailSize.Z)
			table.insert(requests, {
				part = tail,
				at = CFrame.new(0, y0 + H * 0.3, HZ - 0.6 + tailSize.Z * k / 2),
				scale = k,
			})
		end
		if not far then
			for _, sx in { -1, 1 } do
				for _, sz in { -1, 1 } do
					for _, t in { 0.3, 0.72 } do
						box(
							out,
							W + 1.3,
							1.2,
							W + 1.3,
							sx * (HX - W / 2),
							y0 + H * t,
							sz * (HZ - W / 2),
							tint(body, 0.1),
							DECO
						)
					end
				end
			end
		end
	end
	if tier == 6 then -- монстр-дом: голова у верхней плиты (ниже неё), ступни у передних колонн, алмазные друзы
		if face and faceSize then
			local k, tall = headScale(rig, dna)
			local deep = faceSize.Z * k
			group(
				requests,
				rig,
				face,
				CFrame.new(0, y1 - 0.5 - tall / 2, -HZ - math.min(5.6, deep * 0.45) + deep / 2),
				k
			)
		end
		for i, sx in { -1, 1 } do
			local name = dna.limbs.leg[i] or dna.limbs.leg[1]
			local size = sizeOf(rig, name)
			if name and size and not far then
				local k = math.min(5.5 / size.Y, 5.0 / size.X, 6.4 / size.Z)
				table.insert(requests, {
					part = name,
					at = CFrame.new(sx * (HX - W / 2), y0 - 0.5 + size.Y * k / 2, -HZ + 1.4 - size.Z * k / 2),
					scale = k,
				})
			end
			if not far then
				Kit.druse(out, sx * (HX - W - 1.3), y0 + 0.7, -HZ + 0.35, 1.9, Kit.DIAMOND)
				for _, sz in { -1, 1 } do
					local under = Vector3.new(sx * (HX + 0.3), y1 - 2.2, sz * (HZ + 0.3))
					Kit.crystal(out, under, Vector3.new(sx * 0.45, -1, sz * 0.45), 5.6, 0.8, Kit.DIAMOND)
				end
			end
		end
	end
end

export type Built = {
	bricks: { any },
	parts: { any },
	height: number,
	resident: Vector3,
	scale: number,
	item: string,
}

-- Этаж существа itemId редкости tier (1…6). nil — у существа нет скелета (не существо коллекции).
function MonsterFloor.Build(itemId: string, tier: number): Built?
	local dna = FloorDna.Of(itemId)
	local rig = CreatureRigs[itemId]
	if not dna or not rig then
		return nil
	end
	local out, requests = {}, {}
	local h = MonsterFloor.Height(tier)
	local _, headTall = headScale(rig, dna)
	local lintel = lintelOf(tier, headTall)
	slab(out, tier, 0)
	for _, sx in { -1, 1 } do
		for _, sz in { -1, 1 } do
			column(out, dna, sx, sz, SLAB, h)
		end
	end
	glazing(out, dna, SLAB, h, lintel, tier == 6)
	local at = ZoneRooms.Build(out, dna, tier, SLAB, h, requests, sizeOf(rig, dna.feature))
	monsterParts(out, requests, dna, rig, tier, SLAB, h, lintel, false)
	if tier == 6 then -- выросты каркаса у задних колонн (у передних — руки): тело монстра с алмазными остриями
		growths(out, tier, SLAB, h, { 1 }, tint(dna.palette[1], 0.12), DECO, Kit.DIAMOND, Kit.GEM)
	elseif tier == 5 then
		growths(out, tier, SLAB, h, { 1 }, dna.palette[2], DECO, hex(signalOf(tier).glow), PULSE)
	end
	return {
		bricks = out,
		parts = requests,
		height = h,
		resident = at,
		scale = ZoneRooms.Scale(dna, tier),
		item = itemId,
	}
end

-- Дальняя версия (от FloorRarity.FarDistance): сигнал редкости, а не монстр. Каркас и плита — в цвете редкости
-- (Деревянный и Каменный — приглушённые, фон башни; Мраморный — светлый; Золотой — Foil и тёплый светящийся пояс;
-- Мифический — фиолетовый со светящимися пульсирующими рёбрами; Алмазный — бело-голубой, сияние, острия-кристаллы),
-- монстр — только настоящий жилец в светлом окне. Выросты каркаса — у Мифического (до 4) и Алмазного (до 8 стадов).
function MonsterFloor.Far(itemId: string, tier: number): Built?
	local dna = FloorDna.Of(itemId)
	if not dna or not CreatureRigs[itemId] then
		return nil
	end
	local out = {}
	local h = MonsterFloor.Height(tier)
	local signal = signalOf(tier)
	local frame, cap, plate = hex(signal.frame), hex(signal.cap), hex(signal.slab)
	local FAR = { variant = "LegoSquaresFar", collide = false }
	local SKIN = if signal.foil then { material = Enum.Material.Foil, collide = false } else FAR
	local glow = if signal.glow then hex(signal.glow) else nil
	local LIT = if signal.pulse then PULSE else NEON
	local e, sof = 0.6, 0.4
	local bh, by = SLAB - sof, (SLAB + sof) / 2
	box(out, (HX + e) * 2, sof, (HZ + e) * 2, 0, sof / 2, 0, shade(plate, 0.55), FAR)
	box(out, (HX + e) * 2, bh, (HZ + e) * 2, 0, by, 0, plate, FAR)
	if glow then -- светящийся пояс по плите
		box(out, (HX + e) * 2 + 1.0, 0.8, (HZ + e) * 2 + 1.0, 0, by, 0, glow, LIT)
	else
		box(out, (HX + e) * 2 + 0.3, 0.4, (HZ + e) * 2 + 0.3, 0, by, 0, KANT[tier], FAR)
	end
	local shaft = h - SLAB - 1.6
	for _, sx in { -1, 1 } do
		for _, sz in { -1, 1 } do
			local cx, cz = sx * (HX - W / 2), sz * (HZ - W / 2)
			box(out, W + 0.4, shaft, W + 0.4, cx, SLAB + shaft / 2, cz, frame, SKIN)
			box(out, W + 1.0, 1.6, W + 1.0, cx, h - 0.8, cz, cap, SKIN)
			if glow and signal.pulse then -- светящееся ребро по наружному углу колонны
				box(
					out,
					0.7,
					shaft - 0.7,
					0.7,
					sx * (HX + 0.2),
					SLAB + 0.35 + (shaft - 0.7) / 2,
					sz * (HZ + 0.2),
					glow,
					LIT
				)
			end
		end
	end
	local zf, xs = -HZ + 1.0, HX - 1.0
	local zb = HZ - 0.7
	local zc = (zf + zb) / 2
	local floorY = SLAB + 0.36
	local at, px, pz, ph = ZoneRooms.Spot(dna, tier, floorY)
	local zg = at.Z + pz / 2 + 0.6
	local top = 2.2
	local window = if signal.window then hex(signal.window) else ZoneRooms.Glow(dna, tier)
	box(out, xs * 2, h - floorY - top, zb - zg, 0, (floorY + h - top) / 2, (zg + zb) / 2, window, {
		material = Enum.Material.SmoothPlastic,
		collide = false,
		shadow = false,
		name = "Glow",
	})
	box(out, xs * 2 + 0.6, top, zb - zf + 0.6, 0, h - 0.05 - top / 2, zc - 0.05, cap, FAR)
	box(out, xs * 2 + 0.6, 0.36, zb - zf + 0.3, 0, SLAB + 0.18, zc - 0.15, window:Lerp(shade(frame, 0.5), 0.5), FAR)
	box(out, xs * 2 - 1, 0.7, 0.8, 0, SLAB + 0.35, zf, cap, FAR)
	for _, s in { -1, 1 } do
		box(out, 0.8, 0.7, zg - zf, s * xs, SLAB + 0.35, (zf + zg) / 2 + 0.2, cap, FAR)
	end
	box(out, xs * 2 - 0.5, h - SLAB - 0.1, 0.5, 0, (SLAB + h - 0.1) / 2, zb + 0.25, shade(frame, 0.3), FAR)
	box(out, px, ph, pz, 0, floorY + ph / 2, at.Z, window:Lerp(frame, 0.35), FAR)
	if glow then
		growths(out, tier, SLAB, h, { -1, 1 }, frame, SKIN, glow, LIT)
	end
	return {
		bricks = out,
		parts = {},
		height = h,
		resident = at,
		scale = ZoneRooms.Scale(dna, tier),
		item = itemId,
	}
end

-- Плита-кровля над верхним этажом (под колпак башни).
function MonsterFloor.Roof(tier: number): { any }
	local out = {}
	slab(out, tier, 0)
	return out
end

return MonsterFloor

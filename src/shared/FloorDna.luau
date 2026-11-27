-- «ДНК существа» для генератора этажей (D74, этаж — продолжение монстра): всё берётся из данных, которые уже есть
-- у существа, без ручной темы — Config/CreatureRigs (части, роли, блоки с цветами, габариты) и Config/Items (босс).
--   palette  — три цвета: тело (самый большой объём блоков), второй (следующий заметно другой), акцент (самый
--              насыщенный из заметных); foot — цвет ног (обувь/лапы) для подножия колонн;
--   family   — семья силуэта по ролям частей и пропорциям → набор облицовки колонн (FloorDna.Families);
--   feature  — главная черта: часть существа с признаком вида (перчатка, рюкзак, веер, рог…) и её пара L/R;
--   head     — часть-голова (у кого морда на теле — nil), limbs — руки, ноги, хвост, уши, крылья (для выростов);
--   zone     — зона босса (комната этажа). Ручные поправки — FloorDna.Overrides (только где правило ошиблось).
-- Чистые функции (сервер, клиент, проверки Lune). Зависит от Config/CreatureRigs, Config/Items.

local CreatureRigs = require(script.Parent.Config.CreatureRigs)
local Items = require(script.Parent.Config.Items)

local FloorDna = {}

-- Семьи силуэта (порядок — как проверяются). Набор колонн на семью — World/Models/MonsterFloor.
FloorDna.Families = { "Wheeled", "Tentacle", "Bird", "Aquatic", "Blob", "Quadruped", "Tall", "Wide", "Biped" }

-- Ручные поправки: [itemId] = { feature = "Часть", family = "Семья", palette = { "HEX", "HEX", "HEX" } }.
FloorDna.Overrides = {} :: { [string]: { [string]: any } }

export type Dna = {
	itemId: string,
	zone: number,
	rarity: string,
	size: Vector3,
	palette: { Color3 },
	foot: Color3,
	family: string,
	feature: string?,
	featurePair: string?,
	head: string?,
	limbs: { [string]: { string } },
}

-- Роли, которые не бывают «главной чертой»: служебные и мелочь лица.
local PLAIN =
	{ stand = true, body = true, leg = true, eye = true, brow = true, jaw = true, tongue = true, whisker = true }
-- Вес роли при выборе главной черты: особые роли (веер, колокол, корона, пружина…) — признак вида.
local ROLE_WEIGHT = { arm = 1.2, hat = 1.5, ear = 0.9, wing = 1.1, tail = 0.8, head = 0.45, paw = 0.9, tenant = 1.3 }
local SPECIAL_WEIGHT = 1.6

local function distance(a: Color3, b: Color3): number
	return math.sqrt((a.R - b.R) ^ 2 + (a.G - b.G) ^ 2 + (a.B - b.B) ^ 2)
end

local function saturation(c: Color3): number
	local _, s, v = c:ToHSV()
	return s * v
end

-- Объём блоков по цветам для списка частей: { { color, volume } } по убыванию, близкие оттенки склеены.
local function clusters(rig: any, pick: (name: string, spec: any) -> boolean): { { color: Color3, volume: number } }
	local list = {}
	for name, spec in rig.Parts do
		if not spec.hidden and pick(name, spec) then
			for _, b in spec.blocks do
				local color = Color3.fromHex(b[3])
				local volume = b[2].X * b[2].Y * b[2].Z
				local found = false
				for _, c in list do
					if distance(c.color, color) < 0.11 then
						-- оттенок кластера — взвешенное среднее
						local total = c.volume + volume
						c.color = c.color:Lerp(color, volume / total)
						c.volume = total
						found = true
						break
					end
				end
				if not found then
					table.insert(list, { color = color, volume = volume })
				end
			end
		end
	end
	table.sort(list, function(a, b)
		return a.volume > b.volume
	end)
	return list
end

local function palette(rig: any): ({ Color3 }, Color3)
	local all = clusters(rig, function(_, spec)
		return spec.role ~= "eye" and spec.role ~= "stand"
	end)
	local total = 0
	for _, c in all do
		total += c.volume
	end
	local body = if all[1] then all[1].color else Color3.fromHex("9AA0A8")
	local second, accent = nil, nil
	local bestAccent = 0
	for i = 2, #all do
		local c = all[i]
		local share = c.volume / math.max(total, 1e-6)
		if not second and distance(c.color, body) > 0.22 and share > 0.03 then
			second = c.color
		end
		local score = saturation(c.color) * distance(c.color, body) * math.min(1, share / 0.02)
		if share > 0.006 and score > bestAccent then
			bestAccent, accent = score, c.color
		end
	end
	local h, s, v = body:ToHSV()
	second = second or Color3.fromHSV(h, s * 0.7, math.clamp(v * (if v > 0.55 then 0.72 else 1.35), 0, 1))
	if not accent or distance(accent, second) < 0.12 then
		accent = Color3.fromHSV((h + 0.5) % 1, math.max(0.55, s), math.max(0.8, v))
	end
	local legs = clusters(rig, function(_, spec)
		return spec.role == "leg" or spec.role == "paw"
	end)
	local foot = if legs[1] then legs[1].color else second
	return { body, second, accent }, foot
end

local function volumeOf(spec: any): number
	return spec.size.X * spec.size.Y * spec.size.Z
end

local function partColor(spec: any): Color3?
	local best, bestVolume = nil, 0
	for _, b in spec.blocks do
		local volume = b[2].X * b[2].Y * b[2].Z
		if volume > bestVolume then
			best, bestVolume = Color3.fromHex(b[3]), volume
		end
	end
	return best
end

-- Пара части по имени: ArmL ↔ ArmR, EarL ↔ EarR.
local function pairOf(rig: any, name: string): string?
	local stem, side = name:match("^(.-)([LR])$")
	if not stem then
		return nil
	end
	local other = stem .. (if side == "L" then "R" else "L")
	return if rig.Parts[other] and not rig.Parts[other].hidden then other else nil
end

function FloorDna.Has(itemId: string): boolean
	return CreatureRigs[itemId] ~= nil and Items[itemId] ~= nil
end

function FloorDna.Of(itemId: string): Dna?
	local rig = CreatureRigs[itemId]
	local def = Items[itemId]
	if not rig or not def then
		return nil
	end
	local override = FloorDna.Overrides[itemId] or {}
	local colors, foot = palette(rig)
	if override.palette then
		colors = {}
		for i, code in override.palette do
			colors[i] = Color3.fromHex(code)
		end
	end
	local body = colors[1]

	local limbs: { [string]: { string } } = { arm = {}, leg = {}, tail = {}, ear = {}, wing = {}, hat = {} }
	local counts: { [string]: number } = {}
	local head, headVolume = nil, 0
	local feature, featureScore = nil, 0
	for _, name in rig.Order do
		local spec = rig.Parts[name]
		if spec.hidden then
			continue
		end
		local role = spec.role
		counts[role] = (counts[role] or 0) + 1
		local group = if role == "paw" then "leg" else role
		if limbs[group] then
			table.insert(limbs[group], name)
		end
		if role == "head" and volumeOf(spec) > headVolume then
			head, headVolume = name, volumeOf(spec)
		end
		if not PLAIN[role] then
			local color = partColor(spec)
			local weight = ROLE_WEIGHT[role] or SPECIAL_WEIGHT
			local contrast = if color then 0.35 + distance(color, body) else 0.35
			local score = volumeOf(spec) ^ 0.5 * weight * contrast
			if score > featureScore then
				feature, featureScore = name, score
			end
		end
	end
	if override.feature then
		feature = override.feature
	end

	local legs = (counts.leg or 0) + (counts.paw or 0)
	local aspect = rig.Size.Y / math.max(rig.Size.X, rig.Size.Z)
	local family
	if (counts.wheel or 0) > 0 or (counts.bogie or 0) > 0 then
		family = "Wheeled"
	elseif (counts.tentacle or 0) > 0 then
		family = "Tentacle"
	elseif (counts.wing or 0) > 0 then
		family = "Bird"
	elseif legs == 0 and (counts.tail or 0) > 0 then
		family = "Aquatic"
	elseif legs == 0 then
		family = "Blob"
	elseif legs >= 4 then
		family = "Quadruped"
	elseif aspect >= 1.45 then
		family = "Tall"
	elseif aspect <= 0.72 then
		family = "Wide"
	else
		family = "Biped"
	end

	return {
		itemId = itemId,
		zone = def.boss or 0,
		rarity = def.rarity,
		size = rig.Size,
		palette = colors,
		foot = foot,
		family = override.family or family,
		feature = feature,
		featurePair = if feature then pairOf(rig, feature) else nil,
		head = head,
		limbs = limbs,
	}
end

return FloorDna

--!nocheck
-- Проверка «ДНК существа» для генератора этажей (D74) без Roblox Studio: у каждого существа с Config/CreatureRigs
-- есть три цвета палитры, семья силуэта из списка FloorDna.Families и главная черта — видимая часть его скелета.
-- Печатает сводку: сколько существ в каждой семье (сколько наборов колонн нужно) и по зонам (наборов комнат).
-- Запуск из корня репозитория: lune run scripts/lune/check_floor_dna.luau [подробно].

local process = require("@lune/process")

local Env = require("./env")

local CreatureRigs = Env.Require("ReplicatedStorage.Shared.Config.CreatureRigs")
local FloorDna = Env.Require("ReplicatedStorage.Shared.FloorDna")

local verbose = process.args[1] ~= nil
local failed, total = 0, 0
local families, zones, noFeature = {}, {}, {}
local known = {}
for _, f in FloorDna.Families do
	known[f] = true
end

local ids = {}
for id in CreatureRigs do
	table.insert(ids, id)
end
table.sort(ids)
for _, id in ids do
	local dna = FloorDna.Of(id)
	if not dna then
		continue -- скелет без записи в Config/Items (черновик)
	end
	total += 1
	local function check(ok, message)
		if not ok then
			print(("  ОШИБКА %s: %s"):format(id, message))
			failed += 1
		end
	end
	check(#dna.palette == 3, "в палитре не три цвета")
	check(known[dna.family], "неизвестная семья " .. tostring(dna.family))
	local rig = CreatureRigs[id]
	if dna.feature then
		check(
			rig.Parts[dna.feature] and not rig.Parts[dna.feature].hidden,
			"главная черта — не видимая часть"
		)
	else
		table.insert(noFeature, id)
	end
	check(dna.head == nil or rig.Parts[dna.head] ~= nil, "голова — не часть скелета")
	families[dna.family] = (families[dna.family] or 0) + 1
	zones[dna.zone] = (zones[dna.zone] or 0) + 1
	if verbose then
		print(
			("%-22s зона %d  %-10s черта %-10s пара %-8s голова %-8s  %s %s %s"):format(
				id,
				dna.zone,
				dna.family,
				tostring(dna.feature),
				tostring(dna.featurePair),
				tostring(dna.head),
				dna.palette[1]:ToHex(),
				dna.palette[2]:ToHex(),
				dna.palette[3]:ToHex()
			)
		)
	end
end

print("· семьи силуэта (наборы колонн)")
for _, f in FloorDna.Families do
	print(("  %-10s %d"):format(f, families[f] or 0))
end
print("· зоны боссов (наборы комнат)")
for zone = 1, 10 do
	if zones[zone] then
		print(("  зона %d: %d"):format(zone, zones[zone]))
	end
end
print(
	("· без главной черты (эмблемой будет голова или тело): %d %s"):format(
		#noFeature,
		table.concat(noFeature, ", ")
	)
)
print(("Итог: существ %d, ошибок %d"):format(total, failed))
process.exit(if failed == 0 then 0 else 1)

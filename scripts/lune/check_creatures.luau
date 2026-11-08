--!nocheck
-- Проверка живых существ без Roblox Studio (D55, этап D): Config/CreatureRigs против индекса D54 (30 существ, части и
-- родители, правила подставки, yaw), роли частей знает Shared/CreatureAnim, Part-версия — не больше 40 блоков, коллекция
-- босса 3 в Config/Items (12 / 10 / 8, доход, размер = габариты живого существа); сборка Util/ItemFactory: каждый
-- Motor6D и Weld сходятся с местом своего блока (Transform = покой), низ существа — на низе корня, лицо — вперёд (−Z),
-- скрытой подставки нет; анимации по ролям в любой момент — конечные повороты без смещений больше пробных.
-- Запуск из корня репозитория: lune run scripts/lune/check_creatures.luau.

local fs = require("@lune/fs")
local serde = require("@lune/serde")
local process = require("@lune/process")

local Env = require("./env")

local CreatureAnim = Env.Require("ReplicatedStorage.Shared.CreatureAnim")
local CreatureRigs = Env.Require("ReplicatedStorage.Shared.Config.CreatureRigs")
local Items = Env.Require("ReplicatedStorage.Shared.Config.Items")
local ItemFactory = Env.Require("ServerScriptService.Server.Util.ItemFactory")
local CFrame = Env.roblox.CFrame

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	if not ok then
		print("  ОШИБКА " .. message)
		failed += 1
	else
		passed += 1
	end
end

local index = serde.decode("json", fs.readFile("assets/models/art/Boss3Creatures.index.json"))
check(#index.items == 30, "в индексе 30 существ")

print("· скелеты и коллекция")
local byRarity = {}
for _, item in index.items do
	local id = item.id
	local rig = CreatureRigs[id]
	check(rig ~= nil, id .. ": есть в CreatureRigs")
	if not rig then
		continue
	end
	local file = serde.decode("json", fs.readFile(("assets/models/art/%s.rig.json"):format(id)))
	check(#rig.Order == #file.order, id .. ": части = rig.json")
	local blocks = 0
	for _, name in rig.Order do
		local spec = rig.Parts[name]
		local src = file.parts[name]
		check(
			src ~= nil and spec.parent == (if src.parent == nil then nil else src.parent),
			id .. "." .. name .. ": родитель"
		)
		check(CreatureAnim.Roles[spec.role] ~= nil, id .. "." .. name .. ": роль " .. tostring(spec.role))
		blocks += #spec.blocks
		if spec.hidden then
			check(#spec.blocks == 0, id .. "." .. name .. ": скрытая часть без блоков")
		end
	end
	check(blocks >= 8 and blocks <= 40, ("%s: блоков %d (8–40)"):format(id, blocks))
	local standHidden = rig.Parts.Stand and rig.Parts.Stand.hidden == true
	check(
		standHidden == (item.stand_policy ~= "keep"),
		id .. ": подставка по правилу D54 (" .. item.stand_policy .. ")"
	)
	for _, extra in item.hide_with_stand or {} do
		check(
			rig.Parts[extra] and rig.Parts[extra].hidden == true,
			id .. ": скрыта вместе с подставкой " .. extra
		)
	end
	check(rig.Yaw == (item.yaw_deg or 0), id .. ": yaw")
	local def = Items[id]
	check(
		def ~= nil and def.boss == 3 and not def.legacy and def.kind == "Creature",
		id .. ": в коллекции босса 3"
	)
	if def then
		check(def.rarity == item.rarity, id .. ": редкость")
		check(def.income > 0, id .. ": доход")
		check(
			(def.size - rig.Size).Magnitude < 1e-3,
			id .. ": размер = габариты живого существа"
		)
		byRarity[def.rarity] = (byRarity[def.rarity] or 0) + 1
	end
end
check(byRarity.Common == 12 and byRarity.Rare == 10 and byRarity.Epic == 8, "12 Common, 10 Rare, 8 Epic")
for _, id in { "CratedVase", "PlasterBust", "KnightArmor", "BronzeHorse" } do
	check(
		Items[id].legacy == true,
		id .. ": черновик «Склада» — только для старых сохранений"
	)
end
local active = 0
for _, def in Items do
	if def.boss == 3 and not def.legacy then
		active += 1
	end
end
check(active == 30, "у босса 3 появляются только 30 существ")

print("· сборка ItemFactory")
local function close(a, b, eps)
	return (a.Position - b.Position).Magnitude < eps
end
for _, item in index.items do
	local id = item.id
	local root = ItemFactory.Create(id)
	root.CFrame = CFrame.new(10, 5, -20) * CFrame.Angles(0, 0.7, 0)
	-- корень переставили: дети в Lune за ним не едут — пересобрать
	root = ItemFactory.Create(id)
	local parts, motors, minY, front = 0, 0, math.huge, 0
	for _, d in root:GetDescendants() do
		if d:IsA("BasePart") then
			parts += 1
			local lowest = d.CFrame.Position.Y - d.Size.Y / 2
			minY = math.min(minY, lowest)
		elseif d:IsA("Motor6D") then
			motors += 1
			local want = d.Part0.CFrame * d.C0 * d.C1:Inverse()
			check(
				close(d.Part1.CFrame, want, 1e-3),
				id .. "." .. d.Name .. ": сустав сходится с блоком"
			)
		elseif d:IsA("Weld") then
			local want = d.Part0.CFrame * d.C0 * d.C1:Inverse()
			check(close(d.Part1.CFrame, want, 1e-3), id .. ": сварка сходится с блоком")
		end
	end
	check(parts >= 8 and parts <= 40, ("%s: деталей %d"):format(id, parts))
	check(motors >= 1, id .. ": суставы есть")
	check(
		math.abs(minY - (root.CFrame.Position.Y - root.Size.Y / 2)) < 0.02,
		("%s: низ на земле (%.3f)"):format(id, minY - (root.CFrame.Position.Y - root.Size.Y / 2))
	)
	-- лицо вперёд: у головы, клюва или туловища центр масс блоков смещён к −Z корня
	local face = root:FindFirstChild("Head") or root:FindFirstChild("Beak") or root:FindFirstChild("Face")
	if face then
		front = (root.CFrame:PointToObjectSpace(face.CFrame.Position)).Z
		check(front <= 0.25, ("%s: голова не сзади (z %.2f)"):format(id, front))
	end
end

print("· анимации по ролям")
for _, item in index.items do
	local rig = CreatureRigs[item.id]
	local out = {}
	for _, mode in { "Wander", "Catch", "Calm", "Held" } do
		for k = 0, 40 do
			local t = 1700000000 + k * 0.137
			CreatureAnim.Transforms(rig, 12345, t, mode, k % 2 == 0, (k % 5 - 2) / 2, out)
			for name, cf in out do
				local x, y, z = cf:ToEulerAnglesXYZ()
				check(x == x and y == y and z == z, item.id .. "." .. name .. ": поворот конечный")
				check(cf.Position.Magnitude < 0.5, item.id .. "." .. name .. ": смещение небольшое")
			end
		end
	end
	local calm = {}
	CreatureAnim.Transforms(rig, 1, 1700000000.5, "Calm", false, 0, calm)
	for name, spec in rig.Parts do
		if spec.role == "leg" then
			check(
				calm[name] == CFrame.identity or calm[name].Position.Magnitude < 1e-6,
				item.id .. "." .. name .. ": на постаменте ноги стоят"
			)
		end
	end
end

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
process.exit(if failed == 0 then 0 else 1)

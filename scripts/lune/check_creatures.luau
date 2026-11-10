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

print("· существа особого внимания (D54)")
local Vector3 = Env.roblox.Vector3
-- ось вращения части: из скелета (axis), иначе — пробной позы
local function spinAxis(spec)
	return spec.axis or (spec.demo and spec.demo.Magnitude > 0 and spec.demo.Unit) or nil
end
for _, item in index.items do
	local rig = CreatureRigs[item.id]
	local axes = {}
	for name, spec in rig.Parts do
		if spec.role == "wheel" or spec.role == "bogie" then
			local a = spinAxis(spec)
			check(a ~= nil, item.id .. "." .. name .. ": у колеса есть ось")
			table.insert(axes, a)
		end
	end
	for i = 2, #axes do
		check(
			math.abs(axes[i]:Dot(axes[1])) > 0.999,
			item.id .. ": колёса крутятся вокруг одной оси"
		)
	end
end
local rat = CreatureRigs.ThreeHeadedRat
check(
	rat.Parts.HeadL.role == "head_angry"
		and rat.Parts.HeadC.role == "head_sleepy"
		and rat.Parts.HeadR.role == "head_silly",
	"трёхголовая крыса: три головы — три характера"
)
local prop = spinAxis(rat.Parts.Propeller)
check(
	math.abs(math.deg(math.acos(prop:Dot(Vector3.yAxis))) - 26) < 0.5,
	"пропеллер: ось наклонена на 26°"
)
local train = CreatureRigs.MonsterTrain
check(
	train.Parts.WheelF.role == "bogie" and train.Parts.WheelB.role == "bogie",
	"поезд-монстр: тележки качаются"
)
check(
	train.Parts.Jaw.role == "jaw_wide",
	"поезд-монстр: пасть открывается вниз и кусает"
)
local vault = CreatureRigs.CheeseVaultHeart
local emperor = CreatureRigs.ThreeTailEmperor
check(
	emperor.Parts.Crown.role == "crown" and emperor.Parts.Crown.parent == "Head",
	"император: корона за головой"
)
local out, maxDoor, closed = {}, 0, false
local heads = { HeadL = {}, HeadC = {}, HeadR = {} }
for _, mode in { "Wander", "Catch", "Calm", "Held", "Flee" } do
	for k = 0, 400 do
		local t = 1700000000 + k * 0.071
		CreatureAnim.Transforms(rat, 777, t, mode, false, 0, out)
		-- пропеллер крутится вокруг своей оси: ось на месте
		check(
			(out.Propeller:VectorToWorldSpace(prop) - prop).Magnitude < 1e-3,
			"пропеллер вращается вокруг своей оси"
		)
		if mode == "Wander" then
			for name, list in heads do
				local x, y, z = out[name]:ToEulerAnglesXYZ()
				table.insert(list, Vector3.new(x, y, z))
			end
		end
		CreatureAnim.Transforms(vault, 4242, t, mode, false, 0, out)
		local l, r = out.DoorL, out.DoorR
		check(
			l.UpVector.Y > 0.9999 and r.UpVector.Y > 0.9999,
			"створки — только вокруг вертикальных петель"
		)
		local al = math.deg(math.atan2(l.LookVector.X, l.LookVector.Z) + math.pi) % 360
		local ar = math.deg(math.atan2(r.LookVector.X, r.LookVector.Z) + math.pi) % 360
		al = if al > 180 then al - 360 else al
		ar = if ar > 180 then ar - 360 else ar
		check(
			math.abs(al + ar) < 1e-3,
			"створки — навстречу друг другу, одновременно"
		)
		maxDoor = math.max(maxDoor, math.abs(al))
		closed = closed or math.abs(al) > 90
	end
end
check(maxDoor <= 96.01, ("створки не заходят друг за друга (до %.1f°)"):format(maxDoor))
check(closed, "створки хоть раз захлопываются")
-- характеры голов: злая — резкие короткие кивки (кивок за 0.1 с), сонная — медленная (самый большой размах), глупая —
-- болтается по нескольким осям
local function span(list, axis)
	local lo, hi = math.huge, -math.huge
	for _, v in list do
		local c = if axis == "X" then v.X elseif axis == "Y" then v.Y else v.Z
		lo, hi = math.min(lo, c), math.max(hi, c)
	end
	return math.deg(hi - lo)
end
local function fastest(list)
	local best = 0
	for i = 2, #list do
		best = math.max(best, math.deg(math.abs(list[i].X - list[i - 1].X)))
	end
	return best
end
check(fastest(heads.HeadL) > 2 * fastest(heads.HeadC), "злая голова кивает резче сонной")
check(
	span(heads.HeadC, "X") > span(heads.HeadL, "X"),
	"сонная голова клюёт носом ниже злой"
)
check(
	span(heads.HeadR, "Y") > 3 and span(heads.HeadR, "Z") > 3,
	"глупая голова болтается в разные стороны"
)
-- стражи сейфа поворачиваются к зрителю (справа — направо), не дальше 35°; без зрителя — оглядываются сами
CreatureAnim.Transforms(vault, 4242, 1700000000.3, "Wander", false, 0, out, Vector3.new(5, 0, 5))
local gl = math.deg(math.atan2(out.GuardL.LookVector.X, out.GuardL.LookVector.Z) + math.pi) % 360
check(gl > 25 and gl < 50, ("страж поворачивается к игроку справа (%.1f°)"):format(gl))
CreatureAnim.Transforms(vault, 4242, 1700000000.3, "Wander", false, 0, out, Vector3.new(-5, 0, -1))
gl = math.deg(math.atan2(out.GuardL.LookVector.X, out.GuardL.LookVector.Z) + math.pi) % 360
check(gl > 360 - 40 and gl < 360 - 30, ("страж не дальше 35° (%.1f°)"):format(gl))
print("· все 30: живые (суставы двигаются в каждом режиме) и ловятся (точный бросок попадает)")
do
	local CreatureMotion = Env.Require("ReplicatedStorage.Shared.CreatureMotion")
	local CatchThrow = Env.Require("ReplicatedStorage.Shared.CatchThrow")
	local CatchRules = Env.Require("ReplicatedStorage.Shared.CatchRules")
	local Catch = Env.Require("ReplicatedStorage.Shared.Config.Catch")
	local G = Catch.Game
	local T0 = 1700000000
	local summary = {}
	for _, item in index.items do
		local rig = CreatureRigs[item.id]
		local def = Items[item.id]
		-- сколько суставов поворачивается больше чем на 3° за 6 с (у босса стоя и на ходу, на постаменте, в руках)
		local moving = {}
		for _, case in { { "Wander", false }, { "Wander", true }, { "Calm", false }, { "Held", false } } do
			local first, swing = {}, {}
			local out = {}
			for k = 0, 90 do
				CreatureAnim.Transforms(rig, 777, T0 + k / 15, case[1], case[2], 0, out, Vector3.new(0, 0, 5))
				for name, cf in out do
					first[name] = first[name] or cf
					local _, angle = (first[name]:Inverse() * cf):ToAxisAngle()
					swing[name] = math.max(swing[name] or 0, math.deg(math.abs(angle)))
				end
			end
			local n = 0
			for _, a in swing do
				if a > 3 then
					n += 1
				end
			end
			table.insert(moving, n)
		end
		-- каждая вращающаяся часть (пропеллер, лампы, колёса, часы) у босса действительно вращается
		local spinOut, spinFirst, spinMax = {}, {}, {}
		for k = 0, 60 do
			CreatureAnim.Transforms(rig, 777, T0 + k / 20, "Wander", true, 0, spinOut)
			for name, spec in rig.Parts do
				local role = CreatureAnim.Roles[spec.role]
				if role and role.kind == "spin" and not spec.hidden then
					local cf = spinOut[name]
					spinFirst[name] = spinFirst[name] or cf
					local _, angle = (spinFirst[name]:Inverse() * cf):ToAxisAngle()
					spinMax[name] = math.max(spinMax[name] or 0, math.deg(math.abs(angle)))
				end
			end
		end
		for name, a in spinMax do
			check(a > 20, ("%s.%s: вращается (%.1f° за 3 с)"):format(item.id, name, a))
		end
		local joints = #rig.Order - 1
		check(
			moving[1] >= math.min(3, joints) and moving[2] >= math.min(3, joints) and moving[3] >= 2 and moving[4] >= 2,
			("%s: живое — двигаются у босса %d/%d, на ходу %d, на постаменте %d, в руках %d"):format(
				item.id,
				moving[1],
				joints,
				moving[2],
				moving[3],
				moving[4]
			)
		)
		table.insert(summary, ("%s %d/%d"):format(item.id, moving[1], joints))
		-- бросок: камера поимки как у сервера (CatchService: место, размер, масштаб), жест точно в центр существа в
		-- момент прилёта — попадание; центр существа в кадре камеры
		local home = CFrame.new(0, 2, 0)
		local params = {
			seed = CreatureMotion.SeedOf("каждое-" .. item.id),
			radius = CreatureMotion.WanderRadius(3),
			scale = CreatureMotion.ScaleOf(def.size),
			mode = "Catch",
			since = T0,
			face = 0.4,
			drop = 2,
		}
		local cam, stage = CatchThrow.Frame(home, params, def.size.Y)
		local hits = 0
		for _, release in { T0 + 1.2, T0 + 2.9, T0 + 4.4 } do
			local arrival = release + G.FlightTime
			local center = CreatureMotion.Center(home, CreatureMotion.Pose(params, arrival), def.size.Y)
			local g = CatchThrow.GestureFor(cam, center)
			local parsed = g and CatchThrow.Parse(g)
			local aim = parsed and CatchThrow.Aim(cam, stage, parsed)
			local radius = CatchRules.CircleRadius(arrival, params.since, params.scale)
			if aim and CatchRules.IsHit(aim, center, radius) then
				hits += 1
			end
		end
		check(hits == 3, ("%s: точный бросок попадает %d/3"):format(item.id, hits))
		local top = stage + Vector3.new(0, def.size.Y / 2, 0)
		local look = (top - cam.Position).Unit:Dot(cam.LookVector)
		check(look > math.cos(math.rad(30)), ("%s: верх существа в кадре поимки (%.2f)"):format(item.id, look))
	end
	print("  суставы в движении у босса: " .. table.concat(summary, ", "))
end

print("· Крысиный король: Part-версия по модели D54")
do
	local KingRig = Env.Require("ReplicatedStorage.Shared.Config.Boss3RatKingRig")
	local KingParts = Env.Require("ReplicatedStorage.Shared.Config.Boss3RatKingParts")
	local total = 0
	for _, name in KingRig.Order do
		local list = KingParts[name]
		check(list ~= nil and #list > 0, "король." .. name .. ": есть детали")
		-- габарит деталей части = габарит меша D54 (с выступами накладок ≤ 0.45): размер детали по её осям, а не по
		-- осям Blender (ревью: высота и глубина были перепутаны)
		local lo = Vector3.new(math.huge, math.huge, math.huge)
		local hi = -lo
		for _, spec in list or {} do
			local half = spec[2] / 2
			local r = spec[4]
			local ext = if r
				then Vector3.new(
					math.abs(r[1]) * half.X + math.abs(r[2]) * half.Y + math.abs(r[3]) * half.Z,
					math.abs(r[4]) * half.X + math.abs(r[5]) * half.Y + math.abs(r[6]) * half.Z,
					math.abs(r[7]) * half.X + math.abs(r[8]) * half.Y + math.abs(r[9]) * half.Z
				)
				else half
			lo = lo:Min(spec[1] - ext)
			hi = hi:Max(spec[1] + ext)
		end
		local size = KingRig.Parts[name].size
		local diff = (hi - lo) - size
		check(
			math.max(math.abs(diff.X), math.abs(diff.Y), math.abs(diff.Z)) <= 0.45,
			("король.%s: габарит деталей = габарит части (%.2f)"):format(
				name,
				math.max(math.abs(diff.X), math.abs(diff.Y), math.abs(diff.Z))
			)
		)
		for _, spec in list or {} do
			total += 1
			local s = spec[2]
			check(s.X > 0.01 and s.Y > 0.01 and s.Z > 0.01, "король." .. name .. ": размер детали")
			-- деталь не дальше габарита части (с запасом): нет «улетевших» блоков
			local info = KingRig.Parts[name]
			local d = (spec[1] - info.center).Magnitude
			check(
				d <= info.size.Magnitude / 2 + 1.5,
				("король.%s: деталь в габарите части (%.2f)"):format(name, d)
			)
			local r = spec[4]
			if r then
				local x = Vector3.new(r[1], r[4], r[7])
				local y = Vector3.new(r[2], r[5], r[8])
				local z = Vector3.new(r[3], r[6], r[9])
				check(
					math.abs(x.Magnitude - 1) < 1e-3 and math.abs(y.Magnitude - 1) < 1e-3 and math.abs(x:Dot(y)) < 1e-3,
					"король." .. name .. ": поворот без масштаба"
				)
				check(
					x:Cross(y):Dot(z) > 0.999,
					"король." .. name .. ": поворот без отражения"
				)
			end
		end
	end
	check(total >= 150 and total <= 450, ("король: деталей %d (150–450)"):format(total))
end
print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
process.exit(if failed == 0 then 0 else 1)

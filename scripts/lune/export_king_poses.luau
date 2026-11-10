--!nocheck
-- Позы Крысиного короля для проверки граней Part-версии (scripts/blender/boss_parts.py): те же Transform суставов,
-- что считает клиент (Shared/BossAnim.Sample по Config/Boss3RatKingRig), и те же C0/C1, что ставит BossService.build,
-- — для каждой выборки поз положение каждой части в осях модели (home = единичный): D = part.CFrame ·
-- (pivot · center · поворот меша)⁻¹, деталь модели x в позе — D · x. Выборки — состояния и фазы, которые держатся
-- заметное время (сон с дыханием, бой и ходьба по фазам, пики ударов, победа, поражение) и переходы.
-- Пишет assets/models/Boss3_RatKing.poses.json: { poses = { имя = { часть = [12 чисел CFrame:GetComponents()] } },
-- held = [имена] } — held: позы, которые держатся (сон, бой, ходьба, возврат, стойка, победный танец, головокружение
-- поражения); в переходах и на пике удара грани проходят совпадение за кадр-два — мерцания не видно.
-- Запуск: lune run scripts/lune/export_king_poses.luau

local fs = require("@lune/fs")
local serde = require("@lune/serde")

local Env = require("./env")
local CFrame = Env.roblox.CFrame

local BossAnim = Env.Require("ReplicatedStorage.Shared.BossAnim")
local Rig = Env.Require("ReplicatedStorage.Shared.Config.Boss3RatKingRig")
local BossModels = Env.Require("ReplicatedStorage.Shared.Config.BossModels")
local Battle = Env.Require("ReplicatedStorage.Shared.Config.Battle")

local DST = "assets/models/Boss3_RatKing.poses.json"
local tl = Battle.Timeline
local turn = CFrame.Angles(0, math.rad(BossModels[3].turn), 0)

-- Положение частей в позе: Part1 = Part0 · C0 · Transform · C1⁻¹ (как у Motor6D), корень — единичный.
local function place(transforms: { [string]: CFrame }): { [string]: CFrame }
	local cf: { [string]: CFrame } = {}
	for _, name in Rig.Order do
		local info = Rig.Parts[name]
		local c1 = (CFrame.new(info.center) * turn):Inverse()
		local part0, c0
		if info.parent then
			local parentInfo = Rig.Parts[info.parent]
			part0 = cf[info.parent]
			c0 = (CFrame.new(parentInfo.center) * turn):Inverse() * CFrame.new(info.pivot - parentInfo.pivot)
		else
			part0 = CFrame.new()
			c0 = CFrame.new(info.pivot)
		end
		cf[name] = part0 * c0 * (transforms[name] or CFrame.new()) * c1:Inverse()
	end
	local out = {}
	for _, name in Rig.Order do
		local info = Rig.Parts[name]
		out[name] = cf[name] * (CFrame.new(info.pivot) * CFrame.new(info.center) * turn):Inverse()
	end
	return out
end

local samples = {}
local held = {}
local function add(name: string, input, keep: boolean?)
	if keep then
		table.insert(held, name)
	end
	input.t = input.t or 0
	input.moving = input.moving == true
	input.clock = input.clock or 0
	samples[name] = place(BossAnim.Sample(Rig, input))
end

for i, clock in { 0, 0.8, 1.6, 2.4, 4.0, 5.3 } do
	add("sleep" .. i, { state = "Sleep", clock = clock }, true)
end
for i, f in { 0.3, 0.6, 1 } do
	add("wake" .. i, { state = "Wake", t = tl.Wake * f })
	add("standup" .. i, { state = "StandUp", t = tl.StandUp * f })
	add("tocombat" .. i, { state = "ToCombat", t = tl.ToCombat * f })
	add("fallasleep" .. i, { state = "FallAsleep", t = tl.FallAsleep * f })
end
for i, clock in { 0, 0.225, 0.45, 0.675 } do
	add("combat" .. i, { state = "Combat", t = 5, clock = clock }, true)
	add("walk" .. i, { state = "Combat", t = 5, clock = clock * 0.6, moving = true }, true)
	add("return" .. i, { state = "Return", t = 1, clock = clock * 0.6, moving = true }, true)
end
for _, kind in { "bite", "swipe" } do
	for i, at in { 0.1, 0.2, 0.35 } do
		add(kind .. i, { state = "Combat", t = 5, attackKind = kind, attackT = at })
	end
end
for i, ht in { 0.08, 0.2 } do
	add("hit" .. i, { state = "Combat", t = 5, hitT = ht })
end
for i, t in { 0.2, 0.6, 1.0, tl.Victory - 0.2 } do
	add("victory" .. i, { state = "Victory", t = t }, i == 2 or i == 3)
end
for i, t in { 0.1, 0.5, 1.0, 1.5, tl.Defeat - 0.3 } do
	add("defeat" .. i, { state = "Defeat", t = t }, i >= 2 and i <= 4)
end
add("stand", { state = "Return", t = 1 }, true)
table.sort(held)

local out = { poses = {}, held = held }
local count = 0
for name, parts in samples do
	local entry = {}
	for part, cf in parts do
		local c = { cf:GetComponents() }
		for k, v in c do
			c[k] = math.round(v * 1e5) / 1e5
		end
		entry[part] = c
	end
	out.poses[name] = entry
	count += 1
end
fs.writeFile(DST, serde.encode("json", out, true))
print(("Позы короля: %d выборок (держатся — %d) → %s"):format(count, #held, DST))

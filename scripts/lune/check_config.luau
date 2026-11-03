--!nocheck
-- Проверка данных игры без Roblox Studio (Lune): коллекции боссов 1 и 2 (12/10/8 у «Музея безумных находок», доход,
-- id MonaLisa — только у босса 2), скелеты боссов (у каждой позы — все части, позы для Shared/BossAnim, карты частей
-- есть в BossModels, Shared/BossAnim считает все состояния боя без ошибок), бой босса 2 (сила из Progression), имена
-- боссов совпадают. Запуск из корня репозитория: lune run scripts/lune/check_config.luau. Ошибка — код возврата 1.

local process = require("@lune/process")

local Env = require("./env")

local Battle = Env.Require("ReplicatedStorage.Shared.Config.Battle")
local BossAnim = Env.Require("ReplicatedStorage.Shared.BossAnim")
local Boss1DogRig = Env.Require("ReplicatedStorage.Shared.Config.Boss1DogRig")
local Boss2TraderRig = Env.Require("ReplicatedStorage.Shared.Config.Boss2TraderRig")
local BossModels = Env.Require("ReplicatedStorage.Shared.Config.BossModels")
local GameConfig = Env.Require("ReplicatedStorage.Shared.Config.GameConfig")
local Items = Env.Require("ReplicatedStorage.Shared.Config.Items")
local Progression = Env.Require("ReplicatedStorage.Shared.Config.Progression")

local RIGS = { [1] = Boss1DogRig, [2] = Boss2TraderRig }
-- Позы, которые берёт Shared/BossAnim.
local POSES = {
	"sleep",
	"alert",
	"stand",
	"combat",
	"combat2",
	"walkA",
	"walkB",
	"bite",
	"swipe",
	"hit",
	"bark",
	"bark2",
	"dizzy",
}
local COLLECTIONS = { [1] = { Common = 8, Rare = 8, Epic = 4 }, [2] = { Common = 12, Rare = 10, Epic = 8 } }

local failed = 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if not ok then
		failed += 1
	end
end

print("Коллекции:")
for boss, want in COLLECTIONS do
	local got, noIncome = {}, {}
	for id, def in Items do
		if type(def) == "table" and def.boss == boss and not def.legacy then
			got[def.rarity] = (got[def.rarity] or 0) + 1
			if not (type(def.income) == "number" and def.income > 0) then
				table.insert(noIncome, id)
			end
		end
	end
	local same = true
	for rarity, count in want do
		same = same and got[rarity] == count
	end
	for rarity in got do
		same = same and want[rarity] ~= nil
	end
	check(
		same,
		("босс %d: Common %d, Rare %d, Epic %d (нужно %d/%d/%d)"):format(
			boss,
			got.Common or 0,
			got.Rare or 0,
			got.Epic or 0,
			want.Common,
			want.Rare,
			want.Epic
		)
	)
	check(
		#noIncome == 0,
		("босс %d: доход есть у всех%s"):format(
			boss,
			if #noIncome > 0 then " (нет: " .. table.concat(noIncome, ", ") .. ")" else ""
		)
	)
end
local mona = Items.MonaLisa
check(
	mona ~= nil and mona.boss == 2 and not mona.legacy,
	"MonaLisa — предмет босса 2 (заготовки босса 10 нет)"
)

print("Боссы:")
for zone, rig in RIGS do
	local model = BossModels[zone]
	check(
		model ~= nil and model.name == GameConfig.Zones[zone].boss,
		("босс %d: имя «%s»"):format(zone, model and model.name or "?")
	)
	local missing = {}
	for _, part in rig.Order do
		local info = rig.Parts[part]
		if not info then
			table.insert(missing, "часть " .. part)
		elseif not (model and model.maps[info.map]) then
			table.insert(missing, ("карты %s у %s"):format(tostring(info.map), part))
		end
	end
	for _, pose in POSES do
		local data = rig.Poses[pose]
		if not data then
			table.insert(missing, "поза " .. pose)
		else
			for _, part in rig.Order do
				if not data[part] or #data[part] ~= 12 then
					table.insert(missing, ("%s.%s"):format(pose, part))
				end
			end
		end
	end
	check(
		#missing == 0,
		("босс %d: %d частей, все позы и карты%s"):format(
			zone,
			#rig.Order,
			if #missing > 0 then " (нет: " .. table.concat(missing, ", ", 1, math.min(#missing, 6)) .. ")" else ""
		)
	)
	local fight = Battle.Bosses[zone]
	check(
		fight ~= nil and fight.Strength == Progression.Bosses[zone],
		("босс %d: сила боя %s = Progression.Bosses[%d] (%s)"):format(
			zone,
			tostring(fight and fight.Strength),
			zone,
			tostring(Progression.Bosses[zone])
		)
	)
end

print("Анимации:")
local STATES = { "Sleep", "Wake", "StandUp", "ToCombat", "Combat", "Victory", "Defeat", "Return", "FallAsleep" }
for zone, rig in RIGS do
	local problems = {}
	for _, state in STATES do
		for _, t in { 0, 0.1, 0.3, 0.7, 1.5, 2.5 } do
			for _, extra in {
				{ moving = false },
				{ moving = true },
				{ attackKind = "bite", attackT = 0.1 },
				{ attackKind = "swipe", attackT = 0.3 },
				{ hitT = 0.05 },
			} do
				local input = { state = state, t = t, clock = t, moving = extra.moving == true }
				input.attackKind, input.attackT, input.hitT = extra.attackKind, extra.attackT, extra.hitT
				local ok, pose = pcall(BossAnim.Sample, rig, input)
				if not ok then
					table.insert(problems, ("%s t=%.1f: %s"):format(state, t, tostring(pose)))
				else
					for _, part in rig.Order do
						if typeof(pose[part]) ~= "CFrame" then
							table.insert(problems, ("%s t=%.1f: нет %s"):format(state, t, part))
						end
					end
				end
			end
		end
	end
	check(#problems == 0, ("босс %d: все состояния считаются%s"):format(
		zone,
		if #problems > 0 then " (" .. table.concat(problems, "; ", 1, math.min(#problems, 3)) .. ")" else ""
	))
end

if failed > 0 then
	print(("Проверок не прошло: %d"):format(failed))
	process.exit(1)
end
print("Все проверки данных прошли")

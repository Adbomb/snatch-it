--!nocheck
-- Проверка данных игры без Roblox Studio (Lune): коллекции боссов 1 и 2 (12/10/8 у «Музея безумных находок», доход,
-- id MonaLisa — только у босса 2), скелеты боссов (у каждой позы — все части, позы для Shared/BossAnim, карты частей
-- есть в BossModels, Shared/BossAnim считает все состояния боя без ошибок), бой босса 2 (сила из Progression), имена
-- боссов совпадают. Запуск из корня репозитория: lune run scripts/lune/check_config.luau. Ошибка — код возврата 1.

local process = require("@lune/process")

local Env = require("./env")

local Vector3, CFrame = Env.roblox.Vector3, Env.roblox.CFrame

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

print("Дальность боя (D52):")
-- игрок достаёт босса не дальше, чем босс начинает выпад (BattleService: одна дальность AttackRange + Reach), а
-- попадание выпада (AttackRange + 2.5) — с запасом на шаг назад за время HitDelay
check(
	Battle.Player.Reach <= 1,
	("игрок не бьёт издалека: Reach = %s (было 3 — удары без ответа с 10.5…12.5 ст.)"):format(
		tostring(Battle.Player.Reach)
	)
)
check(Battle.Player.Reach + 1.5 <= 2.5, "попадание босса дальше начала выпада хотя бы на 1.5 ст.")

print("Анимации:")
local STATES = { "Sleep", "Wake", "StandUp", "ToCombat", "Combat", "Victory", "Defeat", "Return", "FallAsleep" }
for zone, rig in RIGS do
	local problems = {}
	for _, state in STATES do
		for _, t in { 0, 0.1, 0.3, 0.7, 1.5, 2.5 } do
			for _, extra in
				{
					{ moving = false },
					{ moving = true },
					{ attackKind = "bite", attackT = 0.1 },
					{ attackKind = "swipe", attackT = 0.3 },
					{ hitT = 0.05 },
				}
			do
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
	check(
		#problems == 0,
		("босс %d: все состояния считаются%s"):format(
			zone,
			if #problems > 0 then " (" .. table.concat(problems, "; ", 1, math.min(#problems, 3)) .. ")" else ""
		)
	)
end

-- Подписи над предметами (D45): раскладка Shared/LabelLayout — ближняя на месте, дальняя над ней, предел подъёма;
-- и сцена «Свалки»: камеры на подходе к псу, 4 предмета с самыми длинными названиями на постаментах, экраны ПК и
-- телефона — доля кадров, где подписи перекрываются, у прежних подписей (200 × 36 px, без раскладки) и у новых.
print("Подписи предметов:")
local LabelLayout = Env.Require("ReplicatedStorage.Shared.LabelLayout")
local UITokens = Env.Require("ReplicatedStorage.Shared.Config.UITokens")
local MapLayout = Env.Require("ServerScriptService.Server.World.MapLayout")
do
	local pair = {
		{ x = 100, y = 100, w = 200, h = 46, depth = 20 },
		{ x = 130, y = 112, w = 180, h = 46, depth = 35 },
	}
	local lifts = LabelLayout.Place(pair, 4, 1000)
	local bottom = pair[2].y + pair[2].h / 2 - lifts[2]
	check(
		lifts[1] == 0 and math.abs(bottom - (pair[1].y - pair[1].h / 2 - 4)) < 1e-6,
		"дальняя подпись поднята ровно над ближней, ближняя на месте"
	)
	local apart =
		{ { x = 100, y = 100, w = 200, h = 46, depth = 20 }, { x = 400, y = 100, w = 200, h = 46, depth = 30 } }
	local still = LabelLayout.Place(apart, 4, 1000)
	check(
		still[1] == 0 and still[2] == 0,
		"подписи далеко друг от друга не двигаются"
	)
	local stack = {}
	for i = 1, 4 do
		table.insert(stack, { x = 200 + i * 10, y = 300, w = 220, h = 46, depth = 10 * i })
	end
	local stacked = LabelLayout.Place(stack, 4, 1000)
	check(
		LabelLayout.Overlaps(stack, stacked) == 0,
		"четыре подписи друг за другом встают ступеньками без наложений"
	)
	local capped = LabelLayout.Place(stack, 4, 60)
	check(math.max(table.unpack(capped)) <= 60, "подъём не больше предела")
end

do
	local cfg = UITokens.ItemLabel
	local frame = MapLayout.ZoneCFrame(1)
	local longest = {}
	for id, def in Items do
		if type(def) == "table" and def.boss == 1 and not def.legacy then
			table.insert(longest, def)
		end
	end
	table.sort(longest, function(a, b)
		return utf8.len(a.displayName) > utf8.len(b.displayName)
	end)
	local anchors = {}
	for _, point in MapLayout.ArtSlotPoints() do
		if point.zone == 1 then
			local def = longest[point.slot]
			local lift = def.size.Y + cfg.Gap
			local width =
				math.clamp(utf8.len(def.displayName) * cfg.CharWidth + cfg.Padding, cfg.MinWidth, cfg.MaxWidth)
			table.insert(anchors, { at = point.cframe.Position + Vector3.new(0, lift, 0), width = width })
		end
	end
	-- Проекция точки камерой eye → target (поле зрения 70° по вертикали, как Camera.FieldOfView).
	local function project(eye, target, p, w, h)
		local view = CFrame.lookAt(eye, target):PointToObjectSpace(p)
		local depth = -view.Z
		local t = math.tan(math.rad(35))
		return (view.X / (depth * t * w / h) + 1) / 2 * w, (1 - view.Y / (depth * t)) / 2 * h, depth
	end
	for _, screen in { { "ПК", 1366, 768 }, { "телефон", 844, 390 } } do
		local w, h = screen[2], screen[3]
		local scale = math.clamp(h / cfg.ScreenHeight, cfg.Scale.X, cfg.Scale.Y)
		local frames, before, after = 0, 0, 0
		for x = -30, 30, 6 do
			for z = -47, -20, 3 do
				for y = 7, 16, 3 do
					local eye = (frame * CFrame.new(x, y, z)).Position
					local target = (frame * CFrame.new(0, 4, -5)).Position
					local old, new = {}, {}
					for _, a in anchors do
						local sx, sy, depth = project(eye, target, a.at, w, h)
						if depth > 0 and depth < cfg.MaxDistance and sx > 0 and sx < w and sy > 0 and sy < h then
							table.insert(old, { x = sx, y = sy, w = 200, h = 36, depth = depth })
							table.insert(
								new,
								{ x = sx, y = sy, w = a.width * scale, h = cfg.Height * scale, depth = depth }
							)
						end
					end
					if #old >= 2 then
						frames += 1
						if LabelLayout.Overlaps(old) > 0 then
							before += 1
						end
						local lifts = LabelLayout.Place(new, cfg.StackGap * scale, cfg.MaxStack * cfg.Height * scale)
						if LabelLayout.Overlaps(new, lifts) > 0 then
							after += 1
						end
					end
				end
			end
		end
		check(
			after == 0,
			("«Свалка», %s: подписи перекрываются в %d из %d кадров (было %d)"):format(
				screen[1],
				after,
				frames,
				before
			)
		)
	end
end

if failed > 0 then
	print(("Проверок не прошло: %d"):format(failed))
	process.exit(1)
end
print("Все проверки данных прошли")

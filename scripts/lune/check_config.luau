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
-- игрок достаёт босса не дальше, чем босс начинает выпад (BattleService: одна дальность AttackRange + Reach); начатый
-- выпад попадает (отскок не спасает)
check(
	Battle.Player.Reach <= 1,
	("игрок не бьёт издалека: Reach = %s (было 3 — удары без ответа с 10.5…12.5 ст.)"):format(
		tostring(Battle.Player.Reach)
	)
)

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
	-- визуальный QA босса 3: фигура босса перед подписью — подпись над ней или прячется; позади подписи — не мешает;
	-- «Z z z» (глубина −1) ставится первым и не двигается; таймер вверху — запретная зона
	local label = { x = 300, y = 300, w = 180, h = 46, depth = 40 }
	local king = { x0 = 250, x1 = 380, y0 = 220, y1 = 500, depth = 25 }
	local lift, hidden = LabelLayout.Clear(label, 0, { king }, 6, 400)
	check(
		not hidden and math.abs((label.y + label.h / 2 - lift) - (king.y0 - 6)) < 1e-6,
		"подпись поднята над королём"
	)
	local _, tooHigh = LabelLayout.Clear(label, 0, { king }, 6, 50)
	check(
		tooHigh,
		"слишком высоко над королём — подпись прячется, а не висит на нём"
	)
	local behind = { x0 = 250, x1 = 380, y0 = 220, y1 = 500, depth = 60 }
	local same, notHidden = LabelLayout.Clear(label, 0, { behind }, 6, 50)
	check(same == 0 and not notHidden, "король позади подписи ей не мешает")
	local zzz = { x = 300, y = 300, w = 90, h = 60, depth = -1 }
	local near = { x = 310, y = 305, w = 180, h = 46, depth = 20 }
	local zl = LabelLayout.Place({ zzz, near }, 4, 1000)
	check(
		zl[1] == 0 and zl[2] > 0 and LabelLayout.Overlaps({ zzz, near }, zl) == 0,
		"подпись над «Z z z», он на месте"
	)
	local timer = { x0 = 800, x1 = 1100, y0 = 40, y1 = 160, depth = 0 }
	check(
		LabelLayout.InZone({ x = 950, y = 150, w = 160, h = 40, depth = 30 }, 0, { timer }),
		"подпись под таймером"
	)
	check(
		not LabelLayout.InZone({ x = 950, y = 260, w = 160, h = 40, depth = 30 }, 0, { timer }),
		"ниже таймера — свободно"
	)
	-- Arrange: без препятствий — как Place; две подписи за королём поднимаются над ним и не налезают друг на друга
	-- (кадр со входа в «Подземку»); слишком высоко — прячется и места не занимает
	local plain =
		{ { x = 100, y = 100, w = 160, h = 40, depth = 10 }, { x = 120, y = 110, w = 160, h = 40, depth = 20 } }
	local placeLifts = LabelLayout.Place(plain, 4, 200)
	local arrangeLifts = LabelLayout.Arrange(plain, 4, 200, {}, 6, 400)
	check(
		placeLifts[1] == arrangeLifts[1] and placeLifts[2] == arrangeLifts[2],
		"Arrange без препятствий = Place"
	)
	local pair =
		{ { x = 280, y = 320, w = 180, h = 46, depth = 40 }, { x = 330, y = 330, w = 180, h = 46, depth = 45 } }
	local pl, ph = LabelLayout.Arrange(pair, 4, 200, { king }, 6, 400)
	check(
		not ph[1]
			and not ph[2]
			and LabelLayout.Overlaps(pair, pl) == 0
			and pair[1].y + pair[1].h / 2 - pl[1] <= king.y0 - 6 + 1e-6
			and pair[2].y + pair[2].h / 2 - pl[2] <= king.y0 - 6 + 1e-6,
		"две подписи над королём — без наложения"
	)
	-- подпись, которую ближняя высокая подпись перекинула через узкую фигуру выше предела, опускается на предел —
	-- там фигура: прячется (а не рисуется поверх неё)
	local thin = { x0 = 250, x1 = 380, y0 = 400, y1 = 450, depth = 25 }
	local stackOver = {
		{ x = 315, y = 500, w = 180, h = 300, depth = 10 },
		{ x = 315, y = 600, w = 180, h = 46, depth = 50 },
	}
	local sl, sh = LabelLayout.Arrange(stackOver, 4, 150, { thin }, 6, 400)
	check(
		sh[2] and not sh[1] and sl[1] == 0,
		"подпись на пределе подъёма над фигурой — спрятана"
	)
	local free = LabelLayout.Arrange(stackOver, 4, 150, {}, 6, 400)
	check(free[2] == 150, "без фигуры — на пределе подъёма (как Place)")
	local zz = { { x = 300, y = 100, w = 90, h = 60, depth = -1 }, { x = 310, y = 110, w = 90, h = 60, depth = -1 } }
	local zzl, zzh = LabelLayout.Arrange(zz, 4, 200, { king }, 6, 400)
	check(
		zzl[1] == 0 and zzl[2] == 0 and not zzh[1] and not zzh[2],
		"два «Z z z» — на месте, не прячутся"
	)
	local hl, hh = LabelLayout.Arrange(pair, 4, 200, { king }, 6, 50)
	check(
		hh[1] and hh[2] and hl[1] == 0,
		"слишком высоко над королём — обе спрятаны"
	)
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

-- Токены интерфейса во всём src (кроме самого UITokens): `local x = UITokens.Раздел[.Подраздел]` и дальше `x.Имя`,
-- а также прямые `UITokens.Раздел.Имя` — раздел есть, и каждое имя в нём есть (визуальный QA босса 3: пропавший
-- ItemLabel.Update ронял раскладку подписей каждый кадр, LovibumRow читались не из того раздела). Псевдоним,
-- объявленный в файле больше одного раза, не проверяется (неоднозначно).
do
	local fs = require("@lune/fs")
	local missing, used = {}, 0
	local function resolve(path: string): any
		local node: any = UITokens
		for key in string.gmatch(path, "[^%.]+") do
			if type(node) ~= "table" then
				return nil
			end
			node = node[key]
		end
		return node
	end
	local function scan(dir: string)
		for _, name in fs.readDir(dir) do
			local path = dir .. "/" .. name
			if fs.isDir(path) then
				scan(path)
			elseif string.match(name, "%.luau$") and name ~= "UITokens.luau" then
				local source = fs.readFile(path)
				-- псевдонимы: сколько раз объявлен вообще и к каким разделам UITokens (раздел, а не элемент: не «[…]»)
				local declared: { [string]: number } = {}
				for alias in string.gmatch(source, "local%s+([%a_][%w_]*)%s*=") do
					declared[alias] = (declared[alias] or 0) + 1
				end
				local aliases: { [string]: { [string]: number } } = {}
				for alias, section, after in
					string.gmatch(source, "local%s+([%a_][%w_]*)%s*=%s*UITokens%.([%a_][%w_%.]*)([^%w_%.]?)")
				do
					if after ~= "[" and after ~= "(" and after ~= ":" then
						section = string.gsub(section, "%.$", "")
						aliases[alias] = aliases[alias] or {}
						aliases[alias][section] = (aliases[alias][section] or 0) + 1
					end
				end
				for alias, sections in aliases do
					local section, count = next(sections)
					-- одно и то же объявление (в разных функциях) — проверяем; иначе неоднозначно
					if next(sections, section) ~= nil or count ~= declared[alias] then
						continue
					end
					local tokens = resolve(section)
					if tokens == nil then
						used += 1
						table.insert(
							missing,
							("%s: %s = UITokens.%s (нет раздела)"):format(path, alias, section)
						)
					elseif type(tokens) == "table" then
						for field in string.gmatch(source, "%f[%w_]" .. alias .. "%.([%a_][%w_]*)") do
							used += 1
							if tokens[field] == nil then
								table.insert(missing, ("%s: %s.%s (UITokens.%s)"):format(path, alias, field, section))
							end
						end
					end
				end
				for section, field in string.gmatch(source, "%f[%w_]UITokens%.([%a_][%w_]*)%.([%a_][%w_]*)") do
					used += 1
					local tokens = UITokens[section]
					if tokens == nil then
						table.insert(missing, ("%s: UITokens.%s (нет раздела)"):format(path, section))
					elseif type(tokens) == "table" and tokens[field] == nil then
						table.insert(missing, ("%s: UITokens.%s.%s"):format(path, section, field))
					end
				end
			end
		end
	end
	scan("src")
	check(
		#missing == 0,
		("токены интерфейса в src: %d обращений, нет в UITokens: %s"):format(
			used,
			if #missing == 0 then "—" else table.concat(missing, ", ")
		)
	)
end

-- Экономика D56 (утверждено владельцем 2026-11-11): числа конфигов совпадают с утверждёнными; неизменяемое (мощность
-- гантелей, формула бонуса музея, доли цен защиты, боссы 1–3 и гантели 2–3) не тронуто.
print("Экономика D56:")
do
	local function same(got: { number }, want: { number }): boolean
		if type(got) ~= "table" or #got ~= #want then
			return false
		end
		for i, value in want do
			if got[i] ~= value then
				return false
			end
		end
		return true
	end
	local function rising(list: { number }): boolean
		for i = 2, #list do
			if list[i] < list[i - 1] then
				return false
			end
		end
		return true
	end
	check(
		same(Progression.Bosses, { 0, 140, 1100, 150e3, 2.9e6, 33e6, 300e6, 5.3e9, 82e9, 560e9 }),
		"сила боссов 1–10: 0, 140, 1.1K, 150K, 2.9M, 33M, 300M, 5.3B, 82B, 560B"
	)
	check(
		same(Progression.Dumbbell.Power, { 1, 6, 36, 210, 1200, 7700, 46000, 270000, 1600000, 10000000 }),
		"мощность гантелей не менялась"
	)
	check(
		same(Progression.Dumbbell.Prices, { 37e3, 520e3, 16e6, 420e6, 3e9, 33e9, 630e9, 3.2e12, 5.5e12 }),
		"цены гантелей 2–10: 37K, 520K, 16M, 420M, 3B, 33B, 630B, 3.2T, 5.5T"
	)
	check(
		same(Progression.Museum.Prices, { 10e3, 100e3, 610e3, 94e6, 680e6, 3.7e9, 46e9, 630e9, 3.2e12 }),
		"цены уровней музея 2–10: 10K, 100K, 610K, 94M, 680M, 3.7B, 46B, 630B, 3.2T"
	)
	check(
		rising(Progression.Museum.Prices) and rising(Progression.Dumbbell.Prices) and rising(Progression.Bosses),
		"цены и сила боссов не убывают с уровнем"
	)
	local slotsOk = #GameConfig.Museum.SlotsByLevel == 10 and #Progression.Museum.Slots == 10
	for level = 1, 10 do
		local want = math.min(20, math.max(6, 2 * level))
		slotsOk = slotsOk and GameConfig.Museum.SlotsByLevel[level] == want and Progression.Museum.Slots[level] == want
	end
	check(
		slotsOk,
		"мест в музее: max(6, 2 × уровень), не больше 20 (игра и симулятор одинаково)"
	)
	check(
		same(GameConfig.Defense.HackPrices, { 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 3e10, 8e10 }),
		"цены взлома: уровни 1–6 — D37, 7–10 — 1B / 10B / 30B / 80B"
	)
	local share = GameConfig.Defense.Share
	check(
		share.Trap == 0.10 and share.Laser == 0.15 and share.Door == 0.20 and share.Robot == 0.30 and share.Snare == nil,
		"доли цен защиты не менялись (10 / 15 / 20 / 30 %, капкан не продаётся)"
	)
	local power = Progression.MuseumPower
	check(
		power.cap == 3
			and power.Rarity.Common == 0.01
			and power.Rarity.Rare == 0.05
			and power.Rarity.Epic == 0.08
			and power.Rarity.Legendary == 0.12
			and power.Rarity.Secret == 0.3,
		"формула бонуса музея не менялась (потолок +300 %)"
	)
	-- боссы 1–3 (утверждены раньше): силы и цены гантелей 2–3 прежние; босса 2 берут гантелью 1, босса 3 — гантелью 2
	-- за минуты тренировки даже без бонуса музея, босса 4 — гантелью 3: гантель 4 (16M) для боссов 1–4 не нужна
	local p = Progression.Dumbbell.Power
	local toBoss2 = Progression.Bosses[2] / p[1]
	local toBoss3 = (Progression.Bosses[3] - Progression.Bosses[2]) / p[2]
	local toBoss4 = (Progression.Bosses[4] - Progression.Bosses[3]) / p[3]
	check(
		toBoss2 <= 300 and toBoss3 <= 300,
		("боссы 2 и 3 — гантелями 1 и 2: %d с и %d с тренировки без бонуса"):format(
			toBoss2,
			toBoss3
		)
	)
	check(
		toBoss4 <= 1.5 * 3600,
		("босс 4 — гантелью 3 (гантель 4 не нужна): %.2f ч тренировки без бонуса"):format(
			toBoss4 / 3600
		)
	)
	-- доходы существ боссов 4–10: правило (×Growth за уровень от среднего босса 3) и таблица совпадают
	local income = Progression.CreatureIncome
	local base, count = {}, {}
	for _, def in Items do
		if type(def) == "table" and def.boss == 3 and not def.legacy then
			base[def.rarity] = (base[def.rarity] or 0) + def.income
			count[def.rarity] = (count[def.rarity] or 0) + 1
		end
	end
	local incomeOk = income.Growth == 3.2 and income.LegendaryOfEpic == 3 and income.SecretOfLegendary == 3
	for boss = 1, 3 do
		incomeOk = incomeOk and next(income.ByBoss[boss]) == nil
	end
	local worst = 0
	for boss = 4, 10 do
		local row = income.ByBoss[boss]
		local k = income.Growth ^ (boss - 3)
		local epic = base.Epic / count.Epic * k
		local want = {
			Common = base.Common / count.Common * k,
			Rare = base.Rare / count.Rare * k,
			Epic = epic,
			Legendary = epic * income.LegendaryOfEpic,
			Secret = if boss >= 8 then epic * income.LegendaryOfEpic * income.SecretOfLegendary else nil,
		}
		for _, rarity in { "Common", "Rare", "Epic", "Legendary", "Secret" } do
			local got, need = row[rarity], want[rarity]
			if (got == nil) ~= (need == nil) then
				incomeOk = false
			elseif got and need then
				worst = math.max(worst, math.abs(got - need) / need)
			end
		end
	end
	check(
		incomeOk and worst < 0.002,
		("доходы существ боссов 4–10 — по правилу ×3.2 за уровень (расхождение с таблицей ≤ %.3f %%)"):format(
			worst * 100
		)
	)
end

if failed > 0 then
	print(("Проверок не прошло: %d"):format(failed))
	process.exit(1)
end
print("Все проверки данных прошли")

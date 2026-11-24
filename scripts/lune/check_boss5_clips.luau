--!nocheck
-- Проверка данных босса 5 «Йети-коллекционер» без Studio (D64, подключение по docs/BOSS5_INTEGRATION_PLAN.md):
-- настоящие модули игры Config/Boss5YetiRig, Config/Boss5YetiClips и Shared/BossClips против экспорта Blender
-- (assets/models/Boss5_Yeti.rig.json и .anim.json, пишут scripts/blender/boss5_yeti.py и boss5_yeti_anim.py):
--   1) скелет: 31 часть, порядок и родители (родитель раньше ребёнка), позы, выпады → клипы, линза, лёд глыбы;
--   2) 10 клипов разбираются проигрывателем и совпадают с экспортом кадр в кадр;
--   3) подошвы по цепочке суставов не уходят под землю (точная проверка по вершинам — boss5_yeti_anim.py check:
--      0 кадров под землёй; здесь — середина низа стоп, габариты повёрнутых коробок дают ложные углы);
--   4) стыки клипов с позами, циклы замкнуты, нет рывков сустава больше 35° за 1/30 с (пальцы, брови и веки —
--      мелкие, вздрагивают быстрее: до 45°);
--   5) канал линзы: значения 0…1, во сне погасла, в бою светится;
--   6) контур тела (дальность 3.5 стада от него) — выпуклый, по туловищу и ногам, а не по размаху рук.
-- Ничего не пишет. Запуск из корня репозитория: lune run scripts/lune/check_boss5_clips.luau

local fs = require("@lune/fs")
local process = require("@lune/process")
local serde = require("@lune/serde")

local Env = require("./env")
local CFrame = Env.roblox.CFrame
local Vector3 = Env.roblox.Vector3

local BossClips = Env.Require("ReplicatedStorage.Shared.BossClips")
local Battle = Env.Require("ReplicatedStorage.Shared.Config.Battle")
local rig = Env.Require("ReplicatedStorage.Shared.Config.Boss5YetiRig")
local rigData = serde.decode("json", fs.readFile("assets/models/Boss5_Yeti.rig.json"))
local anim = serde.decode("json", fs.readFile("assets/models/Boss5_Yeti.anim.json"))

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

-- Угол между поворотами a и b, 0…180°.
local function angle(a, b): number
	local _, ang = (a:Inverse() * b):ToAxisAngle()
	local d = math.deg(math.abs(ang)) % 360
	return if d > 180 then 360 - d else d
end

-- ── 1. Скелет ──────────────────────────────────────────────────────────────────────────────────────────────
print("1. Скелет")
check(#rig.Order == 31, ("частей %d"):format(#rig.Order))
local sameOrder = #rig.Order == #rigData.order
local parentsFirst = true
local index = {}
for i, name in rig.Order do
	index[name] = i
	sameOrder = sameOrder and rigData.order[i] == name
end
for i, name in rig.Order do
	local par = rig.Parts[name].parent
	parentsFirst = parentsFirst and (par == nil or (index[par] ~= nil and index[par] < i))
	sameOrder = sameOrder and par == rigData.parts[name].parent
end
check(sameOrder, "порядок и родители как в экспорте")
check(
	parentsFirst,
	"у каждой части родитель раньше в порядке (Motor6D собираются по порядку)"
)
check(rig.Poses.stand and rig.Poses.combat and rig.Poses.sleep, "позы stand, combat, sleep")
check(#rig.Clips.Names == 10, ("клипов %d"):format(#rig.Clips.Names))
check(
	rig.AttackClips.bite == "smash" and rig.AttackClips.swipe == "ice_clap" and rig.AttackDefault == "smash",
	"выпады → клипы: укус — удар кулаком, взмах — ледяной хлопок, по умолчанию — удар"
)
check(
	BossClips.Get(rig, rig.AttackClips.bite) ~= nil and BossClips.Get(rig, rig.AttackClips.swipe) ~= nil,
	"клипы выпадов есть"
)
local lensOnly = #rig.Eyes.Parts == 1 and rig.Eyes.Parts[1] == "Lens" and rig.Parts.Lens.eye == true
check(
	lensOnly,
	"линза — единственная «глазная» часть (Neon, гаснет по каналу клипа)"
)
local ice = 0
for name, value in rig.Transparent do
	ice += 1
	check(rig.Parts[name] ~= nil and value > 0 and value < 1, name .. ": прозрачный лёд глыбы")
end
check(ice == #rigData.ice_parts, ("прозрачных частей %d = экспорт"):format(ice))
local cfg = Battle.Bosses[5]
check(cfg.Closed == true, "закрыт до выпуска (D64 п. 7)")
check(
	cfg.BodyRange == true and cfg.AttackRange == 2.5,
	"дальность удара — от контура тела, 2.5 + досягаемость 1"
)

-- ── 2. Клипы против экспорта ───────────────────────────────────────────────────────────────────────────────
print("2. Клипы против экспорта")
local worstDeg, worstPos = 0, 0
for _, name in rig.Clips.Names do
	local clip = BossClips.Get(rig, name)
	local src = anim.clips[name]
	local step = math.floor(anim.fps / clip.fps + 0.5)
	local ok = src ~= nil and clip.duration == src.duration and clip.loop == src.loop
	for i, frame in clip.frames do
		local row = src.frames[(i - 1) * step + 1]
		for j, part in rig.Order do
			local v = row[j]
			local ref = CFrame.new(v[1], v[2], v[3], v[4], v[5], v[6], v[7])
			local d, p = angle(frame[part], ref), (frame[part].Position - ref.Position).Magnitude
			worstDeg, worstPos = math.max(worstDeg, d), math.max(worstPos, p)
			ok = ok and d < 0.05 and p < 0.002
		end
	end
	check(
		ok,
		("%s: %d кадров (%d/с), %.2f с, совпадает с экспортом"):format(
			name,
			clip.count,
			clip.fps,
			clip.duration
		)
	)
end
print(("     наибольшее расхождение: %.4f° и %.5f ст."):format(worstDeg, worstPos))

-- ── 3. Земля ───────────────────────────────────────────────────────────────────────────────────────────────
print("3. Подошвы не уходят под землю")
local function world(frame)
	local out = {}
	for _, name in rig.Order do
		local info = rig.Parts[name]
		if info.parent then
			local par = rig.Parts[info.parent]
			out[name] = out[info.parent] * CFrame.new(info.pivot - par.pivot) * frame[name]
		else
			out[name] = CFrame.new(info.pivot) * frame[name]
		end
	end
	return out
end
-- середина низа стопы (центр габарита минус половина высоты) в мире
local function sole(W, foot: string): number
	local info = rig.Parts[foot]
	return (W[foot] * (info.center - Vector3.new(0, info.size.Y / 2, 0))).Y
end
for _, name in rig.Clips.Names do
	local clip = BossClips.Get(rig, name)
	local worst, where, planted = math.huge, "", math.huge
	for i = 1, clip.count do
		local W = world(clip.frames[i])
		for _, foot in { "FootL", "FootR" } do
			local y = sole(W, foot)
			if y < worst then
				worst, where = y, ("%s, кадр %d"):format(foot, i)
			end
		end
		planted = math.min(planted, math.max(sole(W, "FootL"), sole(W, "FootR")))
	end
	check(
		worst > -0.15,
		("%s: подошвы не ниже земли (наименьшая %.2f — %s)"):format(name, worst, where)
	)
	if name == "combat_idle" or name == "walk" then
		-- хотя бы одна стопа стоит на земле в каждом кадре (не парит): выше 0.6 нет кадра, где обе в воздухе
		local hang = 0
		for i = 1, clip.count do
			local W = world(clip.frames[i])
			if math.min(sole(W, "FootL"), sole(W, "FootR")) > 0.6 then
				hang += 1
			end
		end
		check(
			hang == 0,
			("%s: в каждом кадре хотя бы одна стопа на земле (кадров в воздухе %d)"):format(
				name,
				hang
			)
		)
	end
end

-- ── 4. Стыки и рывки ───────────────────────────────────────────────────────────────────────────────────────
print("4. Стыки клипов с позами и циклы")
local function pose(name)
	local out = {}
	for part, n in rig.Poses[name] do
		out[part] = CFrame.new(n[1], n[2], n[3], n[4], n[5], n[6], n[7], n[8], n[9], n[10], n[11], n[12])
	end
	return out
end
local function gap(a, b)
	local d, p = 0, 0
	for _, part in rig.Order do
		if a[part] and b[part] then
			d = math.max(d, angle(a[part], b[part]))
			p = math.max(p, (a[part].Position - b[part].Position).Magnitude)
		end
	end
	return d, p
end
for _, name in rig.Clips.Names do
	local src = anim.clips[name]
	local clip = BossClips.Get(rig, name)
	if src.start_pose and rig.Poses[src.start_pose] then
		local d, p = gap(clip.frames[1], pose(src.start_pose))
		check(
			d < 3 and p < 0.3,
			("%s, начало — поза %s (%.2f°, %.3f ст.)"):format(name, src.start_pose, d, p)
		)
	end
	if src.end_pose and rig.Poses[src.end_pose] and not clip.loop then
		local d, p = gap(clip.frames[clip.count], pose(src.end_pose))
		check(
			d < 3 and p < 0.3,
			("%s, конец — поза %s (%.2f°, %.3f ст.)"):format(name, src.end_pose, d, p)
		)
	end
	local jump, where = 0, ""
	local n = clip.count
	local per = 30 / clip.fps
	for i = 1, (if clip.loop then n else n - 1) do
		for _, part in rig.Order do
			local small = part:find("Fingers") or part:find("Brow") or part:find("Eyelid")
			local d = angle(clip.frames[i][part], clip.frames[i % n + 1][part]) / per * (if small then 35 / 45 else 1)
			if d > jump then
				jump, where = d, part
			end
		end
	end
	check(
		jump < 35,
		("%s: наибольший поворот за 1/30 с %.1f° (%s)%s"):format(
			name,
			jump,
			where,
			if clip.loop then ", цикл замкнут" else ""
		)
	)
end

-- ── 5. Линза ───────────────────────────────────────────────────────────────────────────────────────────────
print("5. Канал линзы")
local inRange = true
for _, name in rig.Clips.Names do
	local keys = BossClips.Get(rig, name).eyes
	if keys then
		for i = 2, #keys, 2 do
			inRange = inRange and keys[i] >= 0 and keys[i] <= 1
		end
	end
end
check(inRange, "яркость линзы во всех клипах 0…1")
local sleep = BossClips.Get(rig, "sleep_idle").eyes
local dark = sleep ~= nil
if sleep then
	for i = 2, #sleep, 2 do
		dark = dark and sleep[i] < 0.2
	end
end
check(dark, "во сне линза погасла")
local combat = BossClips.Get(rig, "combat_idle").eyes
local lit = true
if combat then
	for i = 2, #combat, 2 do
		lit = lit and combat[i] > 0.8
	end
end
check(lit, "в боевой стойке линза светится")
check(
	BossClips.Eyes(rig, { state = "Combat", t = 1, clock = 11 }) > 0.8,
	"BossClips.Eyes в бою — светится"
)

-- ── 6. Контур тела ─────────────────────────────────────────────────────────────────────────────────────────
print("6. Контур тела для дальности ближнего боя")
local body = rig.Body
local convex, sign = true, 0
for i = 1, #body do
	local a, b, c = body[i], body[i % #body + 1], body[(i + 1) % #body + 1]
	local cross = (b.X - a.X) * (c.Y - b.Y) - (b.Y - a.Y) * (c.X - b.X)
	local s = if cross > 0 then 1 elseif cross < 0 then -1 else 0
	if s ~= 0 then
		if sign == 0 then
			sign = s
		elseif s ~= sign then
			convex = false
		end
	end
end
check(convex and #body >= 8, ("контур выпуклый, %d точек"):format(#body))
local function edge(dx, dz)
	local function inside(x, z)
		local sg = 0
		for i = 1, #body do
			local a, b = body[i], body[i % #body + 1]
			local cr = (b.X - a.X) * (z - a.Y) - (b.Y - a.Y) * (x - a.X)
			local s = if cr > 0 then 1 elseif cr < 0 then -1 else 0
			if s ~= 0 then
				if sg == 0 then
					sg = s
				elseif s ~= sg then
					return false
				end
			end
		end
		return true
	end
	local r = 0
	while inside(dx * r, dz * r) and r < 60 do
		r += 0.05
	end
	return r
end
local front, back, left, right = edge(0, 1), edge(0, -1), edge(1, 0), edge(-1, 0)
print(
	("     от центра до края: вперёд %.1f, назад %.1f, влево %.1f, вправо %.1f ст."):format(
		front,
		back,
		left,
		right
	)
)
check(
	math.max(front, back, left, right) < 10 and math.min(front, back, left, right) > 3,
	"корпус и ноги, без размаха рук: край от центра 3…10 ст. (от центра нужно было бы 9.5+)"
)

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end

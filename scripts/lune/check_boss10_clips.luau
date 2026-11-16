--!nocheck
-- Проверка данных босса 10 «Король-дракон» без Studio (этап A интеграции): настоящие модули игры Config/Boss10DragonRig,
-- Config/Boss10DragonClips и Shared/BossClips против экспорта Blender (assets/models/Boss10_Dragon.rig.json и
-- .anim.json, пишет scripts/blender/dragon10/v7_export.py):
--   1) скелет: 52 сустава, порядок и родители (родитель раньше ребёнка), позы stand / combat / sleep;
--   2) 15 клипов разбираются проигрывателем и совпадают с экспортом кадр в кадр;
--   3) прямая кинематика: цепочка суставов (как Motor6D в игре) ставит контрольные точки частей туда же, где их
--      поставил Blender (проверка осей, точек вращения и порядка);
--   4) стыки клипов с позами, цикл шага на месте сходится сам с собой;
--   5) контур тела (дальность 3.5 стада) — выпуклый, без крыльев и хвоста: края от центра;
--   6) размер данных и память после разбора.
-- Ничего не пишет. Запуск из корня репозитория: lune run scripts/lune/check_boss10_clips.luau

local fs = require("@lune/fs")
local process = require("@lune/process")
local serde = require("@lune/serde")

local Env = require("./env")
local CFrame = Env.roblox.CFrame
local Vector3 = Env.roblox.Vector3

local BossClips = Env.Require("ReplicatedStorage.Shared.BossClips")
local rig = Env.Require("ReplicatedStorage.Shared.Config.Boss10DragonRig")
local rigData = serde.decode("json", fs.readFile("assets/models/Boss10_Dragon.rig.json"))
local anim = serde.decode("json", fs.readFile("assets/models/Boss10_Dragon.anim.json"))

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

-- Угол между поворотами a и b, 0…180° (ToAxisAngle у Lune отдаёт и углы больше 180°).
local function angle(a, b): number
	local _, ang = (a:Inverse() * b):ToAxisAngle()
	local d = math.deg(math.abs(ang)) % 360
	return if d > 180 then 360 - d else d
end
-- Детали скипетра симметричны: древко с кристаллом — на 90°, осколки — на 120° (цикл вращения сходится по
-- симметрии). Осколки в залпе крутятся быстро нарочно (магия) — для скачков за кадр их не считаем.
local SYMMETRY = { Scepter = 90, ScepterShards = 120 }
local function symAngle(part: string, a, b): number
	local d = angle(a, b)
	local sym = SYMMETRY[part]
	if sym then
		local m = d % sym
		d = math.min(m, sym - m)
	end
	return d
end

-- ── 1. Скелет ──────────────────────────────────────────────────────────────────────────────────────────────
print("1. Скелет")
check(#rig.Order == 52, ("суставов %d (49 частей дракона и 3 скипетра)"):format(#rig.Order))
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
end
check(sameOrder, "порядок суставов как в экспорте")
check(parentsFirst, "у каждого сустава родитель раньше в порядке (Motor6D собираются по порядку)")
local poses = 0
for _ in rig.Poses do
	poses += 1
end
check(rig.Poses.stand and rig.Poses.combat and rig.Poses.sleep and poses == 3, "позы stand, combat, sleep")
check(#rig.Clips.Names == 15, ("клипов %d (13 + шаг на месте влево и вправо)"):format(#rig.Clips.Names))
check(rig.Turn and rig.Turn.Rate == 50 and rig.Turn.Degrees == 90, "шаг на месте: 50°/с, 90° за цикл")
check(rig.AttackClips.claw == "claw_swipe" and rig.AttackClips.volley == "magic_volley", "выпады → клипы")

-- ── 2. Клипы против экспорта ───────────────────────────────────────────────────────────────────────────────
print("2. Клипы против экспорта")
local before = collectgarbage("count")
local worstDeg, worstPos = 0, 0
for _, name in rig.Clips.Names do
	local clip = BossClips.Get(rig, name)
	local src = anim.clips[name]
	local step = math.floor(30 / clip.fps + 0.5)
	local ok = clip.duration == src.duration and clip.loop == src.loop
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
	check(ok, ("%s: %d кадров (%d/с), %.2f с, совпадает с экспортом"):format(name, clip.count, clip.fps, clip.duration))
end
print(("     наибольшее расхождение: %.4f° и %.5f ст."):format(worstDeg, worstPos))
local memory = collectgarbage("count") - before

-- ── 3. Прямая кинематика ───────────────────────────────────────────────────────────────────────────────────
print("3. Цепочка суставов ставит части туда же, где Blender")
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
for clipName, probe in anim.probe do
	local clip = BossClips.Get(rig, clipName)
	local step = math.floor(30 / clip.fps + 0.5)
	local i = probe.frame // step + 1
	local W = world(clip.frames[i])
	local worst = 0
	for name, v in probe.points do
		local got = W[name] * Vector3.new(v[1], v[2], v[3])
		worst = math.max(worst, (got - Vector3.new(v[4], v[5], v[6])).Magnitude)
	end
	check(worst < 0.03, ("%s, кадр %d: точки 52 частей на месте (наибольшее отклонение %.4f ст.)"):format(clipName, probe.frame, worst))
end

-- ── 4. Стыки ───────────────────────────────────────────────────────────────────────────────────────────────
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
		d = math.max(d, symAngle(part, a[part], b[part]))
		p = math.max(p, (a[part].Position - b[part].Position).Magnitude)
	end
	return d, p
end
for name, src in anim.clips do
	local clip = BossClips.Get(rig, name)
	if src.start_pose then
		local d, p = gap(clip.frames[1], pose(src.start_pose))
		-- шаг на месте входит весом за 0.25 с (BossAnimController) — ему достаточно быть близко к стойке
		local limit = if string.find(name, "turn_step", 1, true) then 25 else 3
		check(d < limit and p < 0.3, ("%s, начало — поза %s (%.2f°, %.3f ст.)"):format(name, src.start_pose, d, p))
	end
	if src.end_pose and not clip.loop then
		local d, p = gap(clip.frames[clip.count], pose(src.end_pose))
		check(d < 3 and p < 0.3, ("%s, конец — поза %s (%.2f°, %.3f ст.)"):format(name, src.end_pose, d, p))
	end
	-- наибольший поворот сустава за 1/30 с (цикл — и через конец); осколки скипетра не в счёт. Предел 35°: опускание
	-- лапы в шаге перед постановкой (≈ 1000°/с) — самое быстрое движение клипов; рывки доводки были 40–46°.
	local jump, where = 0, ""
	local n = clip.count
	local per = 30 / clip.fps
	for i = 1, (if clip.loop then n else n - 1) do
		for _, part in rig.Order do
			-- в залпе скипетр нарочно вращается и бьёт тычком на выстреле — его тоже не считаем
			if part ~= "ScepterShards" and not (name == "magic_volley" and part == "Scepter") then
				local d = symAngle(part, clip.frames[i][part], clip.frames[i % n + 1][part]) / per
				if d > jump then
					jump, where = d, part
				end
			end
		end
	end
	check(jump < 35, ("%s: наибольший поворот сустава за 1/30 с %.1f° (%s)%s"):format(name, jump, where, if clip.loop then ", цикл замкнут" else ""))
end

-- ── 5. Контур тела ─────────────────────────────────────────────────────────────────────────────────────────
print("5. Контур тела для дальности ближнего боя")
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
	local r = 0
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
	while inside(dx * r, dz * r) and r < 60 do
		r += 0.05
	end
	return r
end
local front, back, left, right = edge(0, 1), edge(0, -1), edge(1, 0), edge(-1, 0)
print(("     от центра до края: вперёд %.1f, назад %.1f, влево %.1f, вправо %.1f ст."):format(front, back, left, right))
check(front > 11 and front < 15 and left > 8 and left < 12 and right > 8 and right < 12 and back > 11 and back < 15,
	"грудь, бока и лапы — без крыльев, хвоста и морды (у морды было бы ≥ 25, у хвоста ≥ 23)")
check(rig.VolleyOrigin.Z > 25 and rig.VolleyOrigin.Y > 10, ("центр круга залпа %s — перед драконом"):format(tostring(rig.VolleyOrigin)))

-- ── 6. Размер ──────────────────────────────────────────────────────────────────────────────────────────────
print("6. Размер и память")
local chars = 0
for _, file in fs.readDir("src/shared/Config/Boss10DragonClips") do
	chars += #fs.readFile("src/shared/Config/Boss10DragonClips/" .. file)
end
local frames = 0
for _, name in rig.Clips.Names do
	frames += BossClips.Get(rig, name).count
end
print(("     модули клипов: %d знаков; в памяти %d кадров × %d суставов = %d CFrame, ≈ %.0f КБ кучи Lune"):format(chars, frames, #rig.Order, frames * #rig.Order, memory))
check(chars < 1600000, "данные клипов меньше 1.6 млн знаков")

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end

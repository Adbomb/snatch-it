--!strict
-- Движение живых существ (D55): положение и поза — функция общего времени сервера (workspace:GetServerTimeNow) и
-- зерна существа, без случайностей и без сети: сервер (попадание броска) и все клиенты (вид) считают одно и то же.
-- Режимы: Wander — ходит и прыгает у своего места, оглядывается; Catch — мини-игра поимки: покачивается и иногда
-- уклоняется с заметным замахом (уклонение — часть движения, не скрытый промах); Flee — убегает недалеко и
-- возвращается; Calm — экспонат на постаменте музея: спокойно на месте, без перемещения.
-- Поза — в осях места существа (CFrame места: низ существа, −Z — его «вперёд»): offset — сдвиг, yaw — поворот вокруг
-- вертикали, lean / roll — наклоны вперёд и вбок, squash — «сжатие» (1 — нет; для анимаций по ролям), hop — высота
-- прыжка (0 — на земле), dodge — замах или уклонение (−1…1 по стороне), moving — идёт / бежит.
-- Дискретные решения (куда идти, прыгать ли, уклоняться ли) — целочисленный хэш bit32 (точно одинаков везде); плавные
-- покачивания — sin / cos (расхождения в последних битах не видны). Числа — Config/Catch.Creature.
-- Ни от чего не зависит, кроме Config/Catch; проверяет scripts/lune/check_creatures.luau.

local Catch = require(script.Parent.Config.Catch)

local C = Catch.Creature
local TAU = 2 * math.pi
local TWO32 = 4294967296

local CreatureMotion = {}

export type Params = {
	seed: number, -- CreatureMotion.SeedOf(uid)
	radius: number, -- радиус блуждания (CreatureMotion.WanderRadius)
	scale: number, -- CreatureMotion.ScaleOf(размер)
	mode: string, -- "Wander" | "Catch" | "Flee" | "Calm"
	since: number?, -- начало режима Catch / Flee (общее время)
	anchor: number?, -- Flee: начало мини-игры — побег начинается оттуда, где существо стояло в мини-игре
	face: number?, -- Catch / Flee: поворот к ловящему (радианы в осях места)
	drop: number?, -- высота места над землёй (постамент): убегая, существо спрыгивает вниз
}

export type Pose = {
	offset: Vector3,
	yaw: number,
	lean: number,
	roll: number,
	squash: number,
	hop: number,
	dodge: number,
	moving: boolean,
}

-- 32-битный хэш зерна и номера (xorshift): 0 ≤ результат < 1, одинаков на любой машине.
local function hash(seed: number, k: number): number
	local x = bit32.bxor(seed, (k % 1048576) * 2654435761 % TWO32)
	for _ = 1, 2 do
		x = bit32.bxor(x, bit32.lshift(x, 13))
		x = bit32.bxor(x, bit32.rshift(x, 17))
		x = bit32.bxor(x, bit32.lshift(x, 5))
	end
	return x / TWO32
end
CreatureMotion.Hash = hash

-- Зерно из uid (FNV-1a, 32 бита; умножение на 16777619 = 2^24 + 403 — без потери точности).
function CreatureMotion.SeedOf(text: string): number
	local h = 2166136261
	for i = 1, #text do
		h = bit32.bxor(h, string.byte(text, i))
		h = (bit32.lshift(h, 24) + (h * 403) % TWO32) % TWO32
	end
	return if h == 0 then 1 else h
end

-- Масштаб существа по размеру (≈ 1 у существа 2 стада в ширину).
function CreatureMotion.ScaleOf(size: Vector3): number
	return math.clamp(math.max(size.X, size.Z) / 2, 0.6, 2)
end

-- Радиус блуждания у места босса zone.
function CreatureMotion.WanderRadius(zone: number): number
	return (C.Wander :: any)[zone] or C.Wander.Default
end

local function smooth(x: number): number
	x = math.clamp(x, 0, 1)
	return x * x * (3 - 2 * x)
end

local function lerpAngle(a: number, b: number, t: number): number
	local d = (b - a + math.pi) % TAU - math.pi
	return a + d * t
end

-- Точка шага k внутри круга радиуса r.
local function point(p: Params, k: number): (number, number)
	local r = p.radius * math.sqrt(hash(p.seed, k * 4 + 1))
	local a = TAU * hash(p.seed, k * 4 + 2)
	return r * math.cos(a), r * math.sin(a)
end

-- Поворот на шаге k: по направлению перехода; короткий переход — просто «оглянуться» в случайную сторону.
local function moveYaw(p: Params, k: number): number
	local x0, z0 = point(p, k - 1)
	local x1, z1 = point(p, k)
	local dx, dz = x1 - x0, z1 - z0
	if dx * dx + dz * dz > 0.01 then
		return math.atan2(-dx, -dz) -- −Z вперёд: CFrame.Angles(0, yaw, 0) смотрит на (dx, dz)
	end
	return (hash(p.seed, k * 4 + 4) - 0.5) * 2.4
end

local function wander(p: Params, t: number): Pose
	local L, M = C.Segment, C.Move
	local s = (t + hash(p.seed, 7) * L) / L
	local k = math.floor(s)
	local u = (s - k) * L
	local x0, z0 = point(p, k - 1)
	local x1, z1 = point(p, k)
	local hop = hash(p.seed, k * 4 + 3) < C.HopChance
	local yaw1 = moveYaw(p, k)
	local pose: Pose = {
		offset = Vector3.new(x1, 0, z1),
		yaw = yaw1,
		lean = 0,
		roll = 0,
		squash = 1 + 0.03 * math.sin(TAU * t / 1.6 + p.seed % 7),
		hop = 0,
		dodge = 0,
		moving = false,
	}
	if u < M then
		local f = u / M
		local e = smooth(f)
		local y = if hop
			then 4 * C.HopHeight * p.scale * f * (1 - f)
			else 0.06 * p.scale * math.abs(math.sin(math.pi * 3 * f))
		pose.offset = Vector3.new(x0 + (x1 - x0) * e, y, z0 + (z1 - z0) * e)
		pose.yaw = lerpAngle(moveYaw(p, k - 1), yaw1, smooth(u / 0.3))
		pose.lean = (if hop then -0.1 else 0.12) * math.sin(math.pi * f) -- в начале и в конце шага — прямо
		pose.hop = if hop then y else 0
		pose.moving = true
		if hop then
			pose.squash = 1 + 0.06 * math.sin(math.pi * f) -- в полёте чуть вытягивается
		end
	else
		if hop and u - M < 0.2 then
			pose.squash = 1 - 0.15 * (1 - (u - M) / 0.2) -- приземлился: присел и выпрямился
		end
		-- осмотр: один взгляд влево-вправо за остаток шага, к концу — снова прямо (шаги стыкуются без скачка)
		local f = (u - M) / (L - M)
		pose.yaw = yaw1 + C.Look * math.sin(TAU * f) * smooth(f * 4) * smooth((1 - f) * 4)
		pose.roll = 0.05 * math.sin(TAU * f * 2)
	end
	return pose
end

-- Мини-игра: покачивание вбок, уклонения по циклам (первый цикл без уклонения — успеть прицелиться). Уклонение:
-- замах (присед, наклон в сторону), рывок вбок (на площадке) или прыжок вверх (на постаменте), пауза, возврат.
local function catchPose(p: Params, t: number): Pose
	local face = p.face or 0
	local since = p.since or t
	local d = math.max(t - since, 0)
	local start = wander(p, since)
	local base = Vector3.new(start.offset.X, 0, start.offset.Z) -- без телепорта: оттуда, где бродило
	local rightX, rightZ = math.cos(face), -math.sin(face)
	local turn = smooth(d / 0.4) -- первые 0.4 с: от позы блуждания к позе мини-игры
	local side = C.Sway * p.scale * math.sin(TAU * d / 2.1 + hash(p.seed, 11) * TAU) * turn
	local up = 0.05 * p.scale * math.abs(math.sin(TAU * d / 1.05))
	local squash, roll, dodge = 1 + 0.04 * math.sin(TAU * d / 0.9), 0.0, 0.0
	local cycle = C.DodgeEvery
	local j = math.floor(d / cycle)
	local w = d - j * cycle
	if j >= 1 and hash(p.seed, 1000 + j) < C.DodgeChance then
		local dir = if hash(p.seed, 2000 + j) < 0.5 then -1 else 1
		local leap = p.radius < 1.5
		local a, b, c = C.DodgeWindup, C.DodgeWindup + C.DodgeDash, C.DodgeWindup + C.DodgeDash + C.DodgeHold
		local amount = 0
		if w < a then
			-- присед заметен сразу (за четверть секунды), потом существо дрожит в нём до рывка
			local f = smooth(w / 0.25)
			local g = smooth(w / a)
			squash = 1 - 0.22 * f + 0.03 * math.sin(TAU * w * 6) * f
			roll = -dir * (0.18 * f + 0.14 * g)
			dodge = dir * (0.3 * f + 0.2 * g)
			amount = -0.12 * g -- отклоняется в другую сторону, готовясь прыгнуть
		elseif w < b then
			amount = smooth((w - a) / C.DodgeDash)
			dodge = dir
		elseif w < c then
			amount = 1
			dodge = dir
		elseif w < c + C.DodgeBack then
			amount = 1 - smooth((w - c) / C.DodgeBack)
			dodge = dir * amount
		end
		if leap then
			up += math.max(amount, 0) * C.DodgeLeap * p.scale
			side += dir * math.min(amount, 0) * C.DodgeSide * p.scale
		else
			side += dir * amount * C.DodgeSide * p.scale
		end
	end
	return {
		offset = base + Vector3.new(rightX * side, up * turn + start.offset.Y * (1 - turn), rightZ * side),
		yaw = lerpAngle(start.yaw, face + 0.12 * math.sin(TAU * d / 3.1), turn),
		lean = 0.05 * math.sin(TAU * d / 1.7),
		roll = roll,
		squash = squash,
		hop = up,
		dodge = dodge,
		moving = math.abs(dodge) > 0.2,
	}
end

-- Место мини-игры (в осях места, низ, без прыжка): где существо бродило в начале режима Catch (камера поимки и
-- плоскость броска — Shared/CatchThrow).
function CreatureMotion.CatchBase(p: Params): Vector3
	local start = wander(p, p.since or 0)
	return Vector3.new(start.offset.X, 0, start.offset.Z)
end

-- Побег: прочь от ловящего (с постамента — спрыгнуть), постоять, оглянуться, вернуться.
local function anchorOf(p: Params): Vector3
	if not p.anchor then
		return Vector3.zero
	end
	local start = wander(p, p.anchor)
	return Vector3.new(start.offset.X, 0, start.offset.Z)
end

local function fleePose(p: Params, t: number): Pose
	local face = p.face or 0
	local d = math.max(t - (p.since or t), 0)
	local base = anchorOf(p)
	-- первые 0.3 с — от последней позы мини-игры (покачивание, уклонение) к побегу
	local from = Vector3.zero
	if p.anchor and p.since and d < 0.3 then
		local last = catchPose(
			{ seed = p.seed, radius = p.radius, scale = p.scale, mode = "Catch", since = p.anchor, face = face },
			p.since
		)
		from = (last.offset - base) * (1 - smooth(d / 0.3))
	end
	local T = Catch.Game.FleeTime
	local awayX, awayZ = math.sin(face), math.cos(face) -- от ловящего (назад от лица)
	local dist, y, yaw, moving = 0, 0, face + math.pi, false
	local drop = p.drop or 0
	local run, back = T * 0.27, T * 0.6
	if d < run then
		local f = d / run
		dist = smooth(f) * Catch.Game.FleeDistance
		y = -drop * smooth(f) + 4 * 0.5 * p.scale * f * (1 - f)
		moving = true
	elseif d < back then
		dist = Catch.Game.FleeDistance
		y = -drop
		yaw = face + math.pi + 0.8 * math.sin(TAU * (d - run) / (back - run))
	elseif d < T then
		local f = (d - back) / (T - back)
		dist = (1 - smooth(f)) * Catch.Game.FleeDistance
		y = -drop * (1 - smooth(f)) + 4 * 0.6 * p.scale * f * (1 - f)
		yaw = face
		moving = true
	end
	return {
		offset = base + from + Vector3.new(awayX * dist, y, awayZ * dist),
		yaw = yaw,
		lean = if moving then 0.15 else 0,
		roll = 0,
		squash = 1,
		hop = if moving then 0.3 * p.scale else 0,
		dodge = 0,
		moving = moving,
	}
end

-- Экспонат на постаменте: дыхание, лёгкий поворот и покачивание на месте (D55: без перемещения).
local function calmPose(p: Params, t: number): Pose
	local phase = hash(p.seed, 3) * TAU
	return {
		offset = Vector3.zero,
		yaw = 0.16 * math.sin(TAU * t / 6.5 + phase),
		lean = 0.035 * math.sin(TAU * t / 3.3 + phase),
		roll = 0.025 * math.sin(TAU * t / 4.1 + phase),
		squash = 1 + 0.035 * math.sin(TAU * t / 1.8 + phase),
		hop = 0,
		dodge = 0,
		moving = false,
	}
end

-- Поза существа в момент t (общее время сервера).
function CreatureMotion.Pose(p: Params, t: number): Pose
	if p.mode == "Catch" then
		return catchPose(p, t)
	elseif p.mode == "Flee" and p.since and t - p.since < Catch.Game.FleeTime then
		return fleePose(p, t)
	elseif p.mode == "Flee" and p.since and t - p.since < Catch.Game.FleeTime + Catch.Game.Blend then
		local pose = wander(p, t)
		local k = smooth((t - p.since - Catch.Game.FleeTime) / Catch.Game.Blend)
		local base = anchorOf(p)
		pose.offset = base + (pose.offset - base) * k
		pose.yaw = lerpAngle(p.face or 0, pose.yaw, k)
		return pose
	elseif p.mode == "Calm" then
		return calmPose(p, t)
	end
	return wander(p, t)
end

-- CFrame низа существа в мире: место home (CFrame места, низ существа) + поза.
function CreatureMotion.WorldCFrame(home: CFrame, pose: Pose): CFrame
	return home * CFrame.new(pose.offset) * CFrame.Angles(0, pose.yaw, 0) * CFrame.Angles(pose.lean, 0, pose.roll)
end

-- Центр существа (цель броска): середина по высоте height над низом.
function CreatureMotion.Center(home: CFrame, pose: Pose, height: number): Vector3
	return (home * CFrame.new(pose.offset + Vector3.new(0, height / 2, 0))).Position
end

return CreatureMotion

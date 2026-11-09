--!strict
-- Анимации частей живых существ по ролям (D55, правила владельца D54): каждая часть только поворачивается вокруг своей
-- точки вращения (и чуть смещается — как в пробной позе D54), без разрывов. Направление и размах — из пробной позы
-- части (demo, градусы XYZ в осях модели), без неё — по роли. У моделей с повёрнутым корпусом (Yaw ≠ 0: улитка,
-- кроссовок, крысовоз, поезд-монстр) поворот считается в осях, повёрнутых на Yaw (оси их шарниров). Ритм — от общего
-- времени и зерна существа (у каждого свой), пары ног — враскачку, головы и хвосты — со сдвигом фаз. Существа
-- «особого внимания» (D54) — свои роли: три характера голов трёхголовой крысы, тележки поезда-монстра, створки и
-- стражи сейфа, корона императора; ось вращения колёс и пропеллера — axis из скелета. Режимы:
-- Wander (у босса: ноги шагают, когда идёт), Catch (мини-игра: живее, присед перед уклонением), Calm (экспонат на
-- постаменте: медленно и вполовину), Held (в руках: «трепыхание»). Результат — Transform суставов Motor6D (имя
-- мотора = имя части, Util/ItemFactory). Ни от чего не зависит; вызывает Controllers/CreatureController.

local CreatureAnim = {}

local TAU = 2 * math.pi
local X, Y, Z = Vector3.xAxis, Vector3.yAxis, Vector3.zAxis

-- Роль → ось по умолчанию (оси модели), размах (градусы), частота (Гц), вид движения:
--   swing — туда-обратно; open — от покоя в позу и назад (челюсть, крышка); spin — вращение без конца;
--   bob — смещение вверх-вниз; wobble — мелкая дрожь; snap — два резких кивка и пауза; doze — медленно вниз и
--   рывком вверх; dangle — болтается по трём осям; slam — изредка захлопнуться, подержать и открыться (у пары створок
--   одна фаза, левая и правая — навстречу); look — поворот к зрителю (view) с переминанием.
-- own — ось и размах роли, пробная поза не задаёт направление; follow — фаза вдвое чаще фазы родителя и позже на
-- follow радиан (корона за головой).
type Role = {
	axis: Vector3,
	deg: number,
	freq: number,
	kind: string,
	shift: Vector3?,
	own: boolean?,
	follow: number?,
}
local ROLES: { [string]: Role } = {
	leg = { axis = X, deg = 24, freq = 1.6, kind = "swing" },
	arm = { axis = Z, deg = 28, freq = 1.1, kind = "swing" },
	paw = { axis = X, deg = 16, freq = 1.8, kind = "swing" },
	body = { axis = Z, deg = 5, freq = 0.6, kind = "swing", shift = Vector3.new(0, 0.06, 0) },
	head = { axis = Y, deg = 16, freq = 0.35, kind = "swing" },
	eye = { axis = Y, deg = 10, freq = 0.3, kind = "swing" },
	eyestalk = { axis = Z, deg = 14, freq = 0.8, kind = "swing" },
	ear = { axis = Z, deg = 14, freq = 0.9, kind = "swing" },
	tail = { axis = Y, deg = 26, freq = 1.3, kind = "swing" },
	jaw = { axis = X, deg = 20, freq = 0.5, kind = "open" },
	lid = { axis = X, deg = 24, freq = 0.4, kind = "open" },
	door = { axis = Y, deg = 35, freq = 0.25, kind = "open" },
	wheel = { axis = X, deg = 180, freq = 0.5, kind = "spin" },
	spin = { axis = Y, deg = 120, freq = 0.5, kind = "spin" },
	hands = { axis = Z, deg = 90, freq = 0.5, kind = "spin" },
	float = { axis = Y, deg = 60, freq = 0.5, kind = "spin", shift = Vector3.new(0, 0.12, 0) },
	wing = { axis = Z, deg = 26, freq = 1.4, kind = "swing" },
	tentacle = { axis = X, deg = 18, freq = 0.7, kind = "swing" },
	tenant = { axis = Y, deg = 20, freq = 0.4, kind = "swing", shift = Vector3.new(0, 0.1, 0) },
	hat = { axis = Z, deg = 7, freq = 1.2, kind = "swing", shift = Vector3.new(0, 0.05, 0) },
	sway = { axis = Z, deg = 6, freq = 0.5, kind = "swing" },
	tongue = { axis = X, deg = 14, freq = 1.7, kind = "swing" },
	tab = { axis = X, deg = 18, freq = 1.4, kind = "swing" },
	bell = { axis = Z, deg = 9, freq = 6, kind = "wobble" },
	brow = { axis = X, deg = 6, freq = 0.4, kind = "open", shift = Vector3.new(0, -0.04, 0) },
	whisker = { axis = Y, deg = 12, freq = 1.6, kind = "swing" },
	spit = { axis = X, deg = 0, freq = 0.7, kind = "open", shift = Vector3.new(0, 0.15, 0.25) },
	lift = { axis = X, deg = 0, freq = 0.6, kind = "open", shift = Vector3.new(0, 0.18, 0) },
	stand = { axis = Y, deg = 0, freq = 0, kind = "none" },

	-- Существа «особого внимания» (D54, правила владельца; роли — SPECIAL_ROLES scripts/creature_rigs_to_luau.py).
	-- own — ось и размах роли (пробная поза D54 направления не задаёт).
	head_angry = { axis = X, deg = 14, freq = 0.75, kind = "snap", own = true }, -- злая: два резких кивка «щёлк»
	head_sleepy = { axis = X, deg = 20, freq = 0.16, kind = "doze", own = true }, -- сонная: медленно клюёт носом
	head_silly = { axis = Z, deg = 15, freq = 0.8, kind = "dangle", own = true }, -- глупая: болтается во все стороны
	bogie = { axis = Z, deg = 7, freq = 0.9, kind = "swing", own = true }, -- тележка с рамой качается на оси
	jaw_wide = { axis = Z, deg = 20, freq = 0.45, kind = "swing" }, -- пасть-кабина: вниз — открыта, вверх — «кусь»
	vault_door = { axis = Y, deg = 96, freq = 0.1, kind = "slam", own = true }, -- створки захлопываются навстречу
	guard = { axis = Y, deg = 35, freq = 0.5, kind = "look", own = true }, -- страж: к игроку, переминается
	crown = { axis = Z, deg = 8, freq = 0.7, kind = "swing", follow = 1.1 }, -- за головой с запаздыванием
}
CreatureAnim.Roles = ROLES

-- Режим → множители (частота, размах).
local MODES: { [string]: { speed: number, amp: number } } = {
	Wander = { speed = 1, amp = 1 },
	Catch = { speed = 1.35, amp = 1.15 },
	Flee = { speed = 1.8, amp = 1.2 },
	Calm = { speed = 0.55, amp = 0.45 },
	Held = { speed = 2.6, amp = 1.1 },
}

local function smooth(u: number): number
	return u * u * (3 - 2 * u)
end

-- Импульс 0 → 1 → 0 в доле цикла p: начало start, длина len; быстрый подъём (30 %), задержка, спад.
local function pulse(p: number, start: number, len: number): number
	local u = (p - start) / len
	if u <= 0 or u >= 1 then
		return 0
	elseif u < 0.3 then
		return smooth(u / 0.3)
	elseif u < 0.6 then
		return 1
	end
	return smooth((1 - u) / 0.4)
end

local function wave(kind: string, phase: number): number
	if kind == "swing" or kind == "look" then
		return math.sin(phase)
	elseif kind == "open" then
		-- от покоя в позу и обратно, с паузой в покое: 0…1
		local s = math.sin(phase)
		return if s > 0 then s * s else 0
	elseif kind == "wobble" then
		return math.sin(phase) * (0.5 + 0.5 * math.sin(phase * 0.13))
	end
	local p = (phase % TAU) / TAU
	if kind == "snap" then
		return pulse(p, 0, 0.12) + pulse(p, 0.16, 0.12)
	elseif kind == "doze" then
		if p < 0.75 then
			return smooth(p / 0.75)
		elseif p < 0.82 then
			return 1 - smooth((p - 0.75) / 0.07)
		end
		return 0
	elseif kind == "slam" then
		if p < 0.6 then
			return 0
		elseif p < 0.64 then
			return smooth((p - 0.6) / 0.04)
		elseif p < 0.76 then
			return 1
		elseif p < 0.88 then
			return 1 - smooth((p - 0.76) / 0.12)
		end
		return 0
	end
	return 0
end

-- Фаза части: своя у каждой (зерно и номер), у ног и лап — враскачку по сторонам (и спереди-сзади).
local function phaseOf(seed: number, index: number, role: string, pivot: Vector3): number
	if role == "leg" or role == "paw" or role == "arm" then
		local side = if pivot.X >= 0 then 0 else math.pi
		local front = if role == "leg" and pivot.Z < -0.05 then math.pi else 0
		return side + front + (if role == "arm" then 0.4 else 0)
	end
	if role == "vault_door" then
		return (seed % 997) * 0.618 % TAU -- обе створки — одновременно
	end
	return ((seed % 997) * 0.618 + index * 2.39) % TAU
end

export type Rig = {
	Yaw: number,
	Order: { string },
	Parts: {
		[string]: {
			role: string,
			parent: string?,
			pivot: Vector3,
			demo: Vector3?,
			shift: Vector3?,
			axis: Vector3?,
			hidden: boolean?,
		},
	},
}

local phases: { [string]: number } = {} -- фазы частей текущего вызова (для follow): Transforms не уступает поток

-- Transform суставов существа rig в момент t: out[имя части] = CFrame (повторно используется таблица out).
-- moving — существо идёт (ноги шагают быстрее), dodge — присед перед уклонением (−1…1); view — направление к зрителю
-- в осях модели (лицо — +Z; без него стражи просто оглядываются).
function CreatureAnim.Transforms(
	rig: Rig,
	seed: number,
	t: number,
	mode: string,
	moving: boolean,
	dodge: number,
	out: { [string]: CFrame },
	view: Vector3?
): { [string]: CFrame }
	local m = MODES[mode] or MODES.Wander
	local yaw = math.rad(rig.Yaw or 0)
	local turn = if yaw ~= 0 then CFrame.Angles(0, yaw, 0) else nil
	for index, name in rig.Order do
		local spec = rig.Parts[name]
		local role = ROLES[spec.role] or ROLES.sway
		if role.kind == "none" or spec.hidden then
			out[name] = CFrame.identity
			continue
		end
		local speed, amp = m.speed, m.amp
		if spec.role == "leg" then
			-- ноги: шагают, когда существо идёт; на месте — едва переминаются; на постаменте — стоят
			speed *= if moving then 2.2 else 0.5
			amp *= if moving then 1 elseif mode == "Calm" then 0 else 0.25
		elseif role.kind == "slam" then
			amp = math.min(amp, 1) -- створки не заходят друг за друга (в руках размах больше единицы)
		end
		local phase = phaseOf(seed, index, spec.role, spec.pivot) + TAU * role.freq * speed * t
		local parentPhase = role.follow and spec.parent and phases[spec.parent]
		if parentPhase then
			phase = 2 * parentPhase - (role.follow :: number)
		end
		phases[name] = phase
		local w = wave(role.kind, phase) * amp
		local rot: CFrame
		if role.kind == "spin" then
			local axis = spec.axis or (if spec.demo and spec.demo.Magnitude > 0 then spec.demo.Unit else role.axis)
			rot = CFrame.fromAxisAngle(axis, math.rad(role.deg) * speed * t + phase)
		elseif role.kind == "dangle" then
			local a = math.rad(role.deg) * amp
			rot = CFrame.Angles(
				0.35 * a * math.sin(phase * 1.7 + 0.5),
				0.7 * a * math.sin(phase * 0.63 + 1.3),
				a * math.sin(phase)
			)
		elseif role.kind == "look" then
			-- к зрителю (сзади — зеркально, без скачка), не дальше deg; поверх — переминание с боку на бок
			local turnTo = 0
			if view and view.Magnitude > 1e-3 then
				local limit = math.rad(role.deg)
				turnTo = math.clamp(math.atan2(view.X, math.abs(view.Z)), -limit, limit)
			elseif spec.demo then
				turnTo = math.rad(spec.demo.Y) * 0.8 * w
			end
			rot = CFrame.Angles(0, turnTo, 0) * CFrame.Angles(0, 0, math.rad(4) * w)
		elseif role.own then
			local sign = if role.kind == "slam" then (if spec.pivot.X < 0 then 1 else -1) else 1
			rot = CFrame.fromAxisAngle(spec.axis or role.axis, math.rad(role.deg) * w * sign)
		elseif spec.demo and spec.demo.Magnitude > 0 then
			local d = spec.demo * (w * (if role.kind == "open" then 1 else 0.8))
			rot = CFrame.fromEulerAnglesXYZ(math.rad(d.X), math.rad(d.Y), math.rad(d.Z))
		else
			-- без пробной позы: ось роли; крылья и уши — зеркально по сторонам
			local sign = if (spec.role == "wing" or spec.role == "ear" or spec.role == "arm")
					and spec.pivot.X < 0
				then -1
				else 1
			rot = CFrame.fromAxisAngle(role.axis, math.rad(role.deg) * w * sign)
		end
		local shift = (spec.shift or role.shift)
		if shift then
			local k = if role.kind == "spin" then 0.5 + 0.5 * math.sin(TAU * 0.4 * t + phase) else math.abs(w)
			rot = CFrame.new(shift * k * (if spec.shift then 1 else amp)) * rot
		end
		if spec.role == "body" and dodge ~= 0 then
			-- присед и наклон перед уклонением (мини-игра)
			rot = CFrame.new(0, -0.12 * math.abs(dodge), 0) * CFrame.Angles(0, 0, math.rad(-12) * dodge) * rot
		end
		out[name] = if turn then turn * rot * turn:Inverse() else rot
	end
	return out
end

return CreatureAnim

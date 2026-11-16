-- Математика магического залпа Короля-дракона (босс 10): одна для сервера (BattleService — попадания, урон) и клиентов
-- (Controllers/BossVolleyController — полосы, снаряды), поэтому видимое совпадает с проверкой. Перенос
-- scripts/blender/dragon10/volley_sim.py. Снаряды летят по прямым от центра магического круга: центральный — в грудь
-- бойца в момент фиксации, боковые повёрнуты на ±Spread в плане; после выстрела — без поправок. Попадание — отрезок пути
-- снаряда за шаг против капсулы бойца (от ступней на PlayerHeight), с допуском Grace в пользу уклоняющегося.
-- Числа — Battle.Bosses[10].Volley. Ни от чего не зависит.

export type Params = {
	Speed: number,
	Radius: number,
	Spread: number,
	Range: number,
	AimHeight: number,
	PlayerRadius: number,
	PlayerHeight: number,
	Grace: number,
}

local BossVolley = {}

BossVolley.Sides = { -1, 0, 1 }

-- Направление dir, повёрнутое вокруг вертикали на deg градусов.
local function turn(dir: Vector3, deg: number): Vector3
	return CFrame.fromAxisAngle(Vector3.yAxis, math.rad(deg)):VectorToWorldSpace(dir)
end

-- Точка прицела: грудь бойца над ступнями feet.
function BossVolley.Aim(feet: Vector3, cfg: Params): Vector3
	return feet + Vector3.new(0, cfg.AimHeight, 0)
end

-- Направления снарядов из origin на бойца со ступнями feet: [-1], [0], [1] (0 — центральный).
function BossVolley.Directions(origin: Vector3, feet: Vector3, cfg: Params): { [number]: Vector3 }
	local d = BossVolley.Aim(feet, cfg) - origin
	d = if d.Magnitude > 1e-6 then d.Unit else Vector3.new(0, 0, 1)
	return { [-1] = turn(d, cfg.Spread), [0] = d, [1] = turn(d, -cfg.Spread) }
end

-- Боковые по центральному (у клиента после фиксации — из атрибута VolleyDir).
function BossVolley.FromCenter(center: Vector3, cfg: Params): { [number]: Vector3 }
	return { [-1] = turn(center, cfg.Spread), [0] = center, [1] = turn(center, -cfg.Spread) }
end

-- Сколько стадов снаряд летит до земли на высоте groundY (центр снаряда — на земле); вверх или вдоль — бесконечно.
function BossVolley.ToGround(origin: Vector3, dir: Vector3, groundY: number): number
	if dir.Y >= -1e-6 then
		return math.huge
	end
	return math.max(origin.Y - groundY, 0) / -dir.Y
end

-- Длина пути снаряда: до земли, до препятствия (obstacle — расстояние, nil — нет) или до дальности; и почему кончился.
function BossVolley.Limit(
	origin: Vector3,
	dir: Vector3,
	cfg: Params,
	groundY: number,
	obstacle: number?
): (number, string)
	local ground = BossVolley.ToGround(origin, dir, groundY)
	local limit, why = cfg.Range, "range"
	if ground < limit then
		limit, why = ground, "ground"
	end
	if obstacle and obstacle < limit then
		limit, why = obstacle, "obstacle"
	end
	return limit, why
end

-- Центр снаряда через age секунд после выстрела (не дальше limit).
function BossVolley.Position(origin: Vector3, dir: Vector3, cfg: Params, age: number, limit: number): Vector3
	return origin + dir * math.clamp(age * cfg.Speed, 0, limit)
end

-- Полоса предупреждения на земле: от проекции круга до точки, где снаряд коснётся земли (или конца пути); ширина —
-- диаметр снаряда. Совпадает с тем, где пройдёт снаряд.
function BossVolley.Lane(
	origin: Vector3,
	dir: Vector3,
	cfg: Params,
	groundY: number,
	limit: number?
): (Vector3, Vector3, number)
	local length = limit or (BossVolley.Limit(origin, dir, cfg, groundY, nil))
	local stop = origin + dir * length
	return Vector3.new(origin.X, groundY, origin.Z), Vector3.new(stop.X, groundY, stop.Z), cfg.Radius * 2
end

-- Расстояние между отрезками [p1, q1] и [p2, q2].
function BossVolley.SegmentDistance(p1: Vector3, q1: Vector3, p2: Vector3, q2: Vector3): number
	local d1, d2, r = q1 - p1, q2 - p2, p1 - p2
	local a, e, f = d1:Dot(d1), d2:Dot(d2), d2:Dot(r)
	local s, t
	if a <= 1e-9 and e <= 1e-9 then
		return r.Magnitude
	end
	if a <= 1e-9 then
		s, t = 0, math.clamp(f / e, 0, 1)
	else
		local c = d1:Dot(r)
		if e <= 1e-9 then
			s, t = math.clamp(-c / a, 0, 1), 0
		else
			local b = d1:Dot(d2)
			local den = a * e - b * b
			s = if den > 1e-9 then math.clamp((b * f - c * e) / den, 0, 1) else 0
			t = (b * s + f) / e
			if t < 0 then
				s, t = math.clamp(-c / a, 0, 1), 0
			elseif t > 1 then
				s, t = math.clamp((b - c) / a, 0, 1), 1
			end
		end
	end
	return ((p1 + d1 * s) - (p2 + d2 * t)).Magnitude
end

-- Ось капсулы бойца со ступнями feet: от feet + r до feet + H − r.
function BossVolley.Capsule(feet: Vector3, cfg: Params): (Vector3, Vector3)
	local r = cfg.PlayerRadius
	return feet + Vector3.new(0, r, 0), feet + Vector3.new(0, cfg.PlayerHeight - r, 0)
end

-- Насколько снаряд, прошедший за шаг отрезок [a, b], вошёл в капсулу бойца (ступни в начале шага feet0 и в конце
-- feet1): плюс — вошёл на столько стадов, минус — прошёл мимо с таким зазором.
function BossVolley.Overlap(a: Vector3, b: Vector3, feet0: Vector3, feet1: Vector3, cfg: Params): number
	local c0, c1 = BossVolley.Capsule(feet0, cfg)
	local e0, e1 = BossVolley.Capsule(feet1, cfg)
	local dist = math.min(BossVolley.SegmentDistance(a, b, c0, c1), BossVolley.SegmentDistance(a, b, e0, e1))
	return cfg.Radius + cfg.PlayerRadius - dist
end

-- Попадание: вошёл не меньше чем на Grace.
function BossVolley.Hits(overlap: number, cfg: Params): boolean
	return overlap >= cfg.Grace
end

return BossVolley

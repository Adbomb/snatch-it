-- Бросок Ловибума (D55, поимка от первого лица): общая модель для сервера и клиента.
-- • Камера поимки (Frame) — от места, где существо стояло в начале мини-игры, и направления на ловящего: существо
--   крупно в центре экрана, фон — настоящая локация. Её считает сервер и присылает клиенту (CatchState).
-- • Жест (Gesture) — всё, что присылает клиент: направление и скорость смахивания в конце жеста и длина жеста, в долях
--   высоты экрана (от размеров и формы экрана не зависит). Parse проверяет жест: короткий, медленный, вбок, вниз или с
--   испорченными числами — не бросок (Ловибум не тратится).
-- • Aim — где траектория пересекает вертикальную плоскость через место существа: направление жеста — куда (влево,
--   вправо), скорость — сила (медленнее — недолёт ниже, быстрее — перелёт выше). Попадание по этой точке и положению
--   существа в момент прилёта считает сервер (CatchRules.IsHit + CreatureMotion); точке от клиента сервер не верит.
-- • GestureFor — обратная задача (серверные тесты: жест, который приведёт в нужную точку). Origin — где лежит
--   Ловибум внизу экрана (начало полёта у ловящего).
-- Зависит от Config/Catch (Throw, Game.Camera), Shared/CreatureMotion; проверяет scripts/lune/check_catch.luau.

local Catch = require(script.Parent.Config.Catch)
local CreatureMotion = require(script.Parent.CreatureMotion)

local C = Catch.Game.Camera
local T = Catch.Throw

local CatchThrow = {}

export type Gesture = {
	dx: number, -- направление смахивания в конце жеста (единичный вектор; x — вправо, y — вниз)
	dy: number,
	speed: number, -- высот экрана в секунду
	length: number, -- длина всего жеста, высот экрана
}

local function finite(x: any): boolean
	return type(x) == "number" and x == x and x ~= math.huge and x ~= -math.huge
end

local function scale(): number
	return 2 * math.tan(math.rad(C.FOV / 2))
end

-- Камера поимки и центр места мини-игры (куда она смотрит). home — CFrame места (низ существа), p — параметры
-- движения в режиме Catch (since, face), height — рост существа, near — не дальше этого (сервер: стена между
-- существом и камерой — камера ближе).
function CatchThrow.Frame(home: CFrame, p: CreatureMotion.Params, height: number, near: number?): (CFrame, Vector3)
	local base = CreatureMotion.CatchBase(p)
	local stage = (home * CFrame.new(base + Vector3.new(0, height / 2, 0))).Position
	local look = home:VectorToWorldSpace(CFrame.Angles(0, p.face or 0, 0).LookVector) -- к ловящему
	local toward = Vector3.new(look.X, 0, look.Z)
	toward = if toward.Magnitude > 1e-3 then toward.Unit else Vector3.zAxis
	local fit = math.max(height, 2 * p.scale)
	local distance = math.min(math.clamp(fit * C.Fit, C.Min, C.Max), near or math.huge)
	local eye = stage + toward * distance + Vector3.new(0, distance * C.Rise, 0)
	return CFrame.lookAt(eye, stage), stage
end

-- Жест от клиента → проверенный жест или nil и причина ("bad" — испорченный, "short", "slow", "side").
function CatchThrow.Parse(g: any): (Gesture?, string?)
	if type(g) ~= "table" then
		return nil, "bad"
	end
	local dx, dy, speed, length = g.dx, g.dy, g.speed, g.length
	if not (finite(dx) and finite(dy) and finite(speed) and finite(length)) then
		return nil, "bad"
	end
	if length > T.MaxSwipe then
		return nil, "bad"
	end
	if length < T.MinSwipe then
		return nil, "short"
	end
	if speed < T.MinSpeed then
		return nil, "slow"
	end
	local m = math.sqrt(dx * dx + dy * dy)
	if m < 1e-6 then
		return nil, "bad"
	end
	dx, dy = dx / m, dy / m
	if -dy < math.cos(math.rad(T.MaxAngle)) then
		return nil, "side" -- вниз или слишком вбок
	end
	return { dx = dx, dy = dy, speed = math.min(speed, T.MaxSpeed), length = length }, nil
end

-- Точка экрана, куда ведёт жест (доли высоты экрана от центра; v — вниз): линия от Ловибума внизу по направлению жеста
-- до высоты существа, по высоте — недолёт или перелёт от скорости (скорость уже в MinSpeed…MaxSpeed — Parse).
function CatchThrow.Screen(g: Gesture): (number, number)
	local u = T.BallY * g.dx / -g.dy
	local v = T.Spread * math.log(T.Ideal / g.speed)
	return u, v
end

-- Луч камеры cam через точку экрана (u, v).
function CatchThrow.Ray(cam: CFrame, u: number, v: number): Vector3
	local k = scale()
	return cam:VectorToWorldSpace(Vector3.new(u * k, -v * k, -1)).Unit
end

-- Где Ловибум пересекает вертикальную плоскость через место stage (поперёк взгляда камеры).
function CatchThrow.Aim(cam: CFrame, stage: Vector3, g: Gesture): Vector3
	local u, v = CatchThrow.Screen(g)
	local dir = CatchThrow.Ray(cam, u, v)
	local look = cam.LookVector
	local n = Vector3.new(look.X, 0, look.Z).Unit
	local t = (stage - cam.Position):Dot(n) / math.max(dir:Dot(n), 1e-3)
	return cam.Position + dir * t
end

-- Жест, который приведёт Ловибум в точку point плоскости (обратная задача; nil — туда не бросить: нужна скорость вне
-- MinSpeed…MaxSpeed или угол больше MaxAngle).
function CatchThrow.GestureFor(cam: CFrame, point: Vector3): Gesture?
	local rel = cam:PointToObjectSpace(point)
	if rel.Z > -1e-3 then
		return nil
	end
	local k = scale()
	local u = rel.X / -rel.Z / k
	local v = -(rel.Y / -rel.Z) / k
	local speed = T.Ideal * math.exp(-v / T.Spread)
	if speed < T.MinSpeed or speed > T.MaxSpeed then
		return nil
	end
	local dx = u / T.BallY
	local m = math.sqrt(dx * dx + 1)
	return (CatchThrow.Parse({ dx = dx / m, dy = -1 / m, speed = speed, length = 0.3 }))
end

-- Где лежит Ловибум внизу экрана (начало полёта у ловящего): depth стадов от камеры.
function CatchThrow.Origin(cam: CFrame, depth: number): Vector3
	return cam.Position + CatchThrow.Ray(cam, 0, T.BallY) * depth
end

return CatchThrow

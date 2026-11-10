-- Раскладка подписей на экране (D45): ближние подписи стоят на своих местах, а дальнюю, которая перекрывает уже
-- поставленную, поднимаем над ней ступенькой — подписи соседних предметов не накладываются; фигура босса перед
-- подписью — тоже препятствие (Clear: поднять над ней или спрятать; Arrange — то и другое одним проходом), верх
-- экрана с таймером — запретная зона (InZone).
-- Только расчёт, без
-- экземпляров: экранные прямоугольники подставляет клиент (Controllers/ItemLabelController), проверка —
-- scripts/lune/check_config.luau, тот же расчёт для предпросмотра — scripts/blender/preview_zone.py.
-- Ни от чего не зависит.

-- Подпись на экране: центр и размер в пикселях (y растёт вниз), depth — расстояние от камеры.
export type Entry = { x: number, y: number, w: number, h: number, depth: number }

local LabelLayout = {}

-- Подъём каждой подписи в пикселях вверх по экрану (в порядке entries). gap — зазор между подписями, maxLift —
-- предел подъёма: подпись, которой мало и его, остаётся на maxLift.
function LabelLayout.Place(entries: { Entry }, gap: number, maxLift: number): { number }
	local order = {}
	for i in entries do
		table.insert(order, i)
	end
	table.sort(order, function(a, b)
		return entries[a].depth < entries[b].depth
	end)
	local placed = {}
	local lifts = table.create(#entries, 0)
	for _, i in order do
		local e = entries[i]
		local lift = 0
		-- Каждый проход поднимает подпись над одной из мешающих; проходов не больше, чем уже поставленных.
		for _ = 1, #placed + 1 do
			local moved = false
			for _, p in placed do
				local top, bottom = e.y - e.h / 2 - lift, e.y + e.h / 2 - lift
				local apart = math.abs(e.x - p.x) >= (e.w + p.w) / 2 + gap
				if not apart and bottom > p.top - gap and top < p.bottom + gap then
					lift = e.y + e.h / 2 - (p.top - gap)
					moved = true
				end
			end
			if not moved then
				break
			end
		end
		lift = math.min(lift, maxLift)
		lifts[i] = lift
		table.insert(placed, { x = e.x, w = e.w, top = e.y - e.h / 2 - lift, bottom = e.y + e.h / 2 - lift })
	end
	return lifts
end

-- Прямоугольник на экране (px, y вниз); depth — расстояние от камеры до ближней точки (у запретных зон HUD — 0).
export type Rect = { x0: number, x1: number, y0: number, y1: number, depth: number }

-- Поднять подпись над препятствиями, которые стоят перед ней (фигура босса): пока прямоугольник подписи при подъёме
-- lift перекрывает препятствие ближе неё — поднимаем над его верхом. Не хватает maxLift — подпись прячется
-- (возвращает lift, спрятать?).
function LabelLayout.Clear(e: Entry, lift: number, obstacles: { Rect }, gap: number, maxLift: number): (number, boolean)
	for _ = 1, #obstacles + 1 do
		local moved = false
		for _, o in obstacles do
			if o.depth < e.depth then
				local top, bottom = e.y - e.h / 2 - lift, e.y + e.h / 2 - lift
				local overlapX = e.x + e.w / 2 > o.x0 - gap and e.x - e.w / 2 < o.x1 + gap
				if overlapX and bottom > o.y0 - gap and top < o.y1 + gap then
					lift = e.y + e.h / 2 - (o.y0 - gap)
					moved = true
				end
			end
		end
		if not moved then
			return lift, false
		end
		if lift > maxLift then
			return lift, true
		end
	end
	return lift, lift > maxLift
end

-- Place и Clear одним проходом: в порядке глубины каждую подпись поднимаем, пока она перекрывает уже поставленную
-- подпись или препятствие ближе неё (фигура босса), — поднятые над боссом подписи не налезают друг на друга. Подъём
-- только из-за подписей — не выше maxLift (как Place); если мешало препятствие и подъём выше maxObstacleLift — подпись
-- прячется (не занимает места). Возвращает подъёмы и флаги «спрятать» (в порядке entries).
function LabelLayout.Arrange(
	entries: { Entry },
	gap: number,
	maxLift: number,
	obstacles: { Rect },
	obstacleGap: number,
	maxObstacleLift: number
): ({ number }, { boolean })
	local order = {}
	for i in entries do
		table.insert(order, i)
	end
	table.sort(order, function(a, b)
		return entries[a].depth < entries[b].depth
	end)
	local placed = {}
	local lifts = table.create(#entries, 0)
	local hidden = table.create(#entries, false)
	-- перекрывает ли подпись при подъёме lift препятствие ближе неё
	local function onObstacle(e: Entry, lift: number): boolean
		local top, bottom = e.y - e.h / 2 - lift, e.y + e.h / 2 - lift
		for _, o in obstacles do
			if
				o.depth < e.depth
				and e.x + e.w / 2 > o.x0 - obstacleGap
				and e.x - e.w / 2 < o.x1 + obstacleGap
				and bottom > o.y0 - obstacleGap
				and top < o.y1 + obstacleGap
			then
				return true
			end
		end
		return false
	end
	for _, i in order do
		local e = entries[i]
		local lift, blocked = 0, false
		if e.depth < 0 then
			-- неподвижные («Z z z», глубина −1): на месте, другие поднимаются над ними
			table.insert(placed, { x = e.x, w = e.w, top = e.y - e.h / 2, bottom = e.y + e.h / 2 })
			continue
		end
		for _ = 1, #placed + #obstacles + 1 do
			local moved = false
			for _, p in placed do
				local top, bottom = e.y - e.h / 2 - lift, e.y + e.h / 2 - lift
				local apart = math.abs(e.x - p.x) >= (e.w + p.w) / 2 + gap
				if not apart and bottom > p.top - gap and top < p.bottom + gap then
					lift = e.y + e.h / 2 - (p.top - gap)
					moved = true
				end
			end
			for _, o in obstacles do
				if o.depth < e.depth then
					local top, bottom = e.y - e.h / 2 - lift, e.y + e.h / 2 - lift
					local overlapX = e.x + e.w / 2 > o.x0 - obstacleGap and e.x - e.w / 2 < o.x1 + obstacleGap
					if overlapX and bottom > o.y0 - obstacleGap and top < o.y1 + obstacleGap then
						lift = e.y + e.h / 2 - (o.y0 - obstacleGap)
						moved, blocked = true, true
					end
				end
			end
			if not moved or (blocked and lift > maxObstacleLift) then
				break
			end
		end
		if not blocked and lift > maxLift then
			-- подписям мало предела: подпись остаётся на maxLift (как Place), но если там фигура босса — прячется
			lift = maxLift
			blocked = onObstacle(e, lift)
			if blocked then
				lift = math.huge
			end
		end
		if blocked and lift > maxObstacleLift then
			hidden[i] = true
		else
			lifts[i] = lift
			table.insert(placed, { x = e.x, w = e.w, top = e.y - e.h / 2 - lift, bottom = e.y + e.h / 2 - lift })
		end
	end
	return lifts, hidden
end

-- Задевает ли подпись (при подъёме lift) одну из зон (таймер и плашка зоны вверху экрана).
function LabelLayout.InZone(e: Entry, lift: number, zones: { Rect }): boolean
	local top, bottom = e.y - e.h / 2 - lift, e.y + e.h / 2 - lift
	for _, z in zones do
		if e.x + e.w / 2 > z.x0 and e.x - e.w / 2 < z.x1 and bottom > z.y0 and top < z.y1 then
			return true
		end
	end
	return false
end

-- Сколько пар подписей перекрывается при подъёмах lifts (для проверок и отчётов).
function LabelLayout.Overlaps(entries: { Entry }, lifts: { number }?): number
	local count = 0
	for i = 1, #entries do
		for j = i + 1, #entries do
			local a, b = entries[i], entries[j]
			local la, lb = if lifts then lifts[i] else 0, if lifts then lifts[j] else 0
			local dx = math.abs(a.x - b.x) < (a.w + b.w) / 2
			local dy = math.abs((a.y - la) - (b.y - lb)) < (a.h + b.h) / 2
			if dx and dy then
				count += 1
			end
		end
	end
	return count
end

return LabelLayout

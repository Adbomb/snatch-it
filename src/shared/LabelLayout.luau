-- Раскладка подписей на экране (D45): ближние подписи стоят на своих местах, а дальнюю, которая перекрывает уже
-- поставленную, поднимаем над ней ступенькой — подписи соседних предметов не накладываются. Только расчёт, без
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

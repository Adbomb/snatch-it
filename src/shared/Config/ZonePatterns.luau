-- Узоры пола зон коридора (D41): Texture на верхней грани пола зоны поверх квадратных пупырышков. Картинки — белые
-- фигуры на прозрачном фоне (scripts/textures/zone_patterns.py → assets/textures/zone_<узор>.png), загружены в Roblox.
-- Цвет, размер плитки и прозрачность задаёт зона (GameConfig.Zones[i].pattern). Ни от чего не зависит.

return table.freeze({
	tiles = "rbxassetid://125997718806608", -- шахматка крупных плит
	grid = "rbxassetid://107756944121378", -- сетка швов
	waves = "rbxassetid://77695667904177", -- волны
	diamonds = "rbxassetid://101254285806460", -- ромбы
	gravel = "rbxassetid://125623146041474", -- утоптанная земля с камешками (свалка)
})

-- Текстуры игры. LEGO-пупырышки (D13) — MaterialVariant «LegoStuds», заменяет весь Plastic.
-- Картинки — assets/textures (от дизайнера), загружены в Roblox; на картинке 4×4 пупырышка,
-- поэтому StudsPerTile = 4 даёт один пупырышек на стад. Ни от чего не зависит.

return {
	LegoStuds = {
		name = "LegoStuds",
		color = "rbxassetid://133407646216237",
		normal = "rbxassetid://95611195247391",
		roughness = "rbxassetid://135539982711389",
		studsPerTile = 4,
	},
}

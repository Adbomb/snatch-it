-- Иконки HUD: ключ → изображение. Значение в UITokens.HudIcons — путь проверенной иконки CheckUIIcons
-- («Категория/Подкатегория/Имя») или готовый "rbxassetid://<id>"; таблица { glyph = … } — плоский силуэт: он
-- отмечается в Shared/StudUI (UI.GlyphImages), и кнопки и шапки окон рисуют его белым с чёрной обводкой, как
-- значки на референсе владельца (2026-11-17). Несуществующих ImageId здесь нет: пустая строка — иконки не будет,
-- интерфейс работает.
-- Зависит от Config/UITokens, StudUI/CheckUIIcons, StudUI/StudUI.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local CheckUIIcons = require(Shared:WaitForChild("StudUI"):WaitForChild("CheckUIIcons"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))

local HudIcons = {}

local function resolve(value: string): string
	if value == "" or string.sub(value, 1, 13) == "rbxassetid://" then
		return value
	end
	return CheckUIIcons.Get(value)
end

-- Изображение иконки key и признак «силуэт» (его рисуют через UI.Glyph).
function HudIcons.Get(key: string): (string, boolean)
	local value = UITokens.HudIcons[key]
	if type(value) == "table" and type(value.glyph) == "string" then
		local image = resolve(value.glyph)
		if image ~= "" then
			UI.GlyphImages[image] = true
		end
		return image, true
	end
	if type(value) ~= "string" then
		return "", false
	end
	return resolve(value), false
end

return HudIcons

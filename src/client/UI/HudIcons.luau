-- Иконки HUD v2 (D48 v2): ключ → изображение. Значение в UITokens.HudIcons — путь проверенной иконки CheckUIIcons
-- («Категория/Подкатегория/Имя») или готовый "rbxassetid://<id>" (новые иконки D48 после разрешённой загрузки).
-- Несуществующих ImageId здесь нет: пустая строка — иконки не будет, интерфейс работает.
-- Зависит от Config/UITokens, StudUI/CheckUIIcons.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local CheckUIIcons = require(Shared:WaitForChild("StudUI"):WaitForChild("CheckUIIcons"))

local HudIcons = {}

function HudIcons.Get(key: string): string
	local value = UITokens.HudIcons[key]
	if type(value) ~= "string" or value == "" then
		return ""
	end
	if string.sub(value, 1, 13) == "rbxassetid://" then
		return value
	end
	return CheckUIIcons.Get(value)
end

return HudIcons

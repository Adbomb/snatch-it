-- Раскладка HUD v3 (ТЗ владельца 2026-11-17, по референсу): одна схема для телефона и ПК, отличаются размеры и отступы.
--   слева посередине — столбик кнопок меню (UI/MenuHud); слева внизу — сила и монеты (GymController);
--   справа внизу — таймер фазы (TimeController): на касании левее кнопки прыжка или под ней; над прыжком — «Удар»;
--   сверху по центру под кнопками Roblox — короткая плашка зоны и уведомления; слева сверху — панель обучения.
-- Здесь — общий масштаб HUD (на касании не мельче UITokens.Hud.TouchScale), экран (в Studio его подменяют атрибуты
-- игрока DevViewport и DevTouch) и зоны кнопок Roblox. Соседи подписываются через Track: их ставят заново при
-- смене размера экрана (поворот телефона, окно ПК), подмене экрана и когда меняется занятое место слева сверху
-- (панель обучения — SetLeftTop) или у нижнего края (монеты слева, таймер справа — SetBottom; между ними встаёт
-- строка «Несёте: …»).
-- Расчёты — Shared/HudMath (их же проверяет Lune). Зависит от Config/GameConfig, Config/UITokens, Shared/HudMath.

local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local HudMath = require(Shared:WaitForChild("HudMath"))

local T = UITokens.Hud
local HudLayout = {}

local tracked: { () -> () } = {}
local leftTop = 0
local bottom = { Left = 0, Right = 0 }
local bound = false

-- Экран, по которому считается раскладка: размер (px), сенсорный ли. В Studio (GameConfig.DevMode) — подменённый
-- атрибутами игрока DevViewport (Vector2) и DevTouch.
function HudLayout.Screen(): (Vector2, boolean)
	local player = Players.LocalPlayer
	local fake = GameConfig.DevMode and player:GetAttribute("DevViewport")
	local forcedTouch = GameConfig.DevMode and player:GetAttribute("DevTouch") == true
	local touch = forcedTouch or (UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled)
	if typeof(fake) == "Vector2" then
		return fake, touch
	end
	return workspace.CurrentCamera.ViewportSize, touch
end

-- Масштаб HUD на текущем экране (Shared/HudMath.Scale).
function HudLayout.Scale(): number
	return HudMath.Scale(HudLayout.Screen())
end

-- Масштаб надписей HUD без нажатия — монеты, сила, таймер (Shared/HudMath.InfoScale).
function HudLayout.InfoScale(): number
	return HudMath.InfoScale(HudLayout.Screen())
end

-- Низ кнопок Roblox, px от верха экрана.
function HudLayout.TopBar(): number
	return math.max(GuiService:GetGuiInset().Y, T.TopBar)
end

-- Зона кнопки прыжка на касании (Shared/HudMath.Jump); nil — кнопки нет (ПК).
function HudLayout.Jump(): { Left: number, Top: number }?
	return HudMath.Jump(HudLayout.Screen())
end

-- Отступ таймера от правого края (Shared/HudMath.TimerRight).
function HudLayout.TimerRight(): number
	return HudMath.TimerRight(HudLayout.Screen())
end

-- Занятое место слева сверху (панель обучения): низ, px от верха экрана; 0 — свободно.
function HudLayout.LeftTop(): number
	return leftTop
end

local function replace()
	for _, place in tracked do
		place()
	end
end

function HudLayout.SetLeftTop(px: number)
	px = math.max(0, math.floor(px))
	if px ~= leftTop then
		leftTop = px
		replace()
	end
end

-- Занято у нижнего края: Left — правый край силы и монет (px от левого края экрана), Right — левый край таймера
-- (px от правого края). Сообщают GymController и TimeController.
function HudLayout.SetBottom(side: "Left" | "Right", px: number)
	px = math.max(0, math.ceil(px))
	if bottom[side] ~= px then
		bottom[side] = px
		replace()
	end
end

-- Свободная полоса у нижнего края: сколько занято слева и справа, px от краёв экрана.
function HudLayout.BottomBand(): (number, number)
	return bottom.Left, bottom.Right
end

-- Вызвать place сейчас и при каждом изменении экрана или раскладки.
function HudLayout.Track(place: () -> ())
	table.insert(tracked, place)
	if not bound then
		bound = true
		local player = Players.LocalPlayer
		workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(replace)
		player:GetAttributeChangedSignal("DevViewport"):Connect(replace)
		player:GetAttributeChangedSignal("DevTouch"):Connect(replace)
		UserInputService:GetPropertyChangedSignal("TouchEnabled"):Connect(replace)
		UserInputService:GetPropertyChangedSignal("KeyboardEnabled"):Connect(replace)
	end
	place()
end

return HudLayout

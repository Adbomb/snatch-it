-- Раскладка HUD v2 (D48 v2, D49): где кончаются таймер-капсула сверху и колонка меню справа при текущем масштабе
-- экрана. От них отсчитываются соседи — плашка зоны и уведомления под таймером, уведомления левее колонки, — чтобы
-- ничто не наезжало друг на друга ни на ПК, ни на телефоне (масштаб на телефоне ~0.6, фиксированные отступы ПК там
-- не годятся). Отступ сверху — в ScreenGui с CoreUISafeInsets (под кнопками Roblox), справа — от правого края.
-- Зависит от Config/UITokens, Shared/StudUI/StudMotion.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))

local HudLayout = {}

-- Высота блока таймера при масштабе 1: капсула, полоса фазы, подпись и отступы (TimeController).
function HudLayout.TimerHeight(): number
	local t = UITokens.TimeHud
	return t.Size.Y + t.Bar.Y + t.InfoSize + t.InfoGap
end

-- Низ блока таймера + gap, px от верха области под кнопками Roblox.
function HudLayout.BelowTimer(gap: number): number
	return UITokens.TimeHud.Top + HudLayout.TimerHeight() * Motion.ScreenScale() + gap
end

-- Половина ширины плашки входа в зону (ZoneController, по центру под таймером), px (D50: на узком телефоне колонка
-- уведомлений заходит под неё — на время плашки уведомления прячутся).
function HudLayout.BannerHalfWidth(): number
	return UITokens.LevelBanner.Size.X / 2 * Motion.ScreenScale()
end

-- Левый край колонки меню + gap, px от правого края экрана.
function HudLayout.LeftOfMenu(gap: number): number
	local m = UITokens.MenuHud
	return m.Margin + (m.Icon + m.Margin) * Motion.ScreenScale() + gap
end

-- Вызвать place сейчас и при каждом изменении размера экрана (поворот телефона, окно ПК).
function HudLayout.Track(place: () -> ())
	place()
	workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(place)
end

return HudLayout

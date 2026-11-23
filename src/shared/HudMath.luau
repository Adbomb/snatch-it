-- Расчёты раскладки HUD (ТЗ владельца 2026-11-17) без обращения к экрану и сервисам: масштаб по размеру экрана,
-- зона кнопки прыжка Roblox, место столбика меню слева и блока ноши у нижнего края. Ими пользуются
-- Client/UI/HudLayout, UI/MenuHud и Controllers/CarryController; те же функции проверяет Lune
-- (scripts/lune/check_hud.luau) на размерах телефонов, планшета и мониторов — в том числе тех, что в окне Studio не
-- показать. Числа — Config/UITokens (Hud, MenuHud, StatsHud, CarryHud). Зависит только от Config/UITokens.

local UITokens = require(script.Parent.Config.UITokens)

local T = UITokens.Hud
local HudMath = {}

-- Масштаб HUD на экране view: по опорному экрану Reference в пределах MinScale…MaxScale (нижний — как у окон,
-- верхний выше: на больших мониторах HUD растёт дальше окон); на касании — не мельче TouchScale.
function HudMath.Scale(view: Vector2, touch: boolean): number
	if view.X <= 0 or view.Y <= 0 then
		return 1
	end
	local scale = math.clamp(math.min(view.X / T.Reference.X, view.Y / T.Reference.Y), T.MinScale, T.MaxScale)
	return if touch then math.max(scale, T.TouchScale) else scale
end

-- Масштаб надписей HUD без нажатия (монеты, сила, таймер): на касании — не мельче InfoTouchScale (мельче кнопок).
function HudMath.InfoScale(view: Vector2, touch: boolean): number
	if view.X <= 0 or view.Y <= 0 then
		return 1
	end
	local scale = math.clamp(math.min(view.X / T.Reference.X, view.Y / T.Reference.Y), T.MinScale, T.MaxScale)
	return if touch then math.max(scale, T.InfoTouchScale) else scale
end

-- Зона кнопки прыжка на касании: Left — от правого края экрана до её левого края, Top — от низа экрана до её верха
-- (px, с запасом). nil — кнопки нет (ПК).
function HudMath.Jump(view: Vector2, touch: boolean): { Left: number, Top: number }?
	if not touch then
		return nil
	end
	return if math.min(view.X, view.Y) <= T.SmallSide then T.JumpSmall else T.Jump
end

-- Отступ таймера от правого края: в углу; на касании с маленьким экраном кнопка прыжка у самого низа — левее неё.
function HudMath.TimerRight(view: Vector2, touch: boolean): number
	local jump = HudMath.Jump(view, touch)
	if jump and jump.Top < T.JumpLow then
		return jump.Left + 4
	end
	return UITokens.TimeHud.Margin.X
end

-- Высота столбика меню из count кнопок, px при масштабе 1.
function HudMath.MenuHeight(count: number): number
	local M = UITokens.MenuHud
	return count * M.Button.Y + math.max(count - 1, 0) * M.Gap
end

-- Высота строк силы и монет слева внизу вместе с отступом от низа экрана, px при масштабе 1.
function HudMath.StatsHeight(): number
	local S = UITokens.StatsHud
	return S.Rows.Strength.icon + S.Rows.Coins.icon + S.Gap + S.Margin.Y
end

-- Столбик меню из count кнопок на экране высотой viewHeight при масштабе HUD scale: верх (px от верха экрана) и
-- масштаб столбика. Стоит по центру экрана, но в полосе между topLimit (низ кнопок Roblox или панели обучения) и
-- монетами (их масштаб — infoScale); если полоса короче столбика (очень низкий экран) — столбик мельче.
function HudMath.Menu(
	count: number,
	viewHeight: number,
	scale: number,
	topLimit: number,
	infoScale: number
): (number, number)
	local gap = UITokens.MenuHud.EdgeGap
	local high = topLimit + gap
	local low = viewHeight - HudMath.StatsHeight() * infoScale - gap
	local full = math.max(HudMath.MenuHeight(count), 1)
	local s = math.min(scale, math.max(low - high, 1) / full)
	local height = full * s
	local top = math.clamp(viewHeight / 2 - height / 2, high, math.max(low - height, high))
	return math.floor(top), s
end

-- Строка шириной width (px при масштабе 1) в свободной полосе нижнего края экрана шириной screen: середина (px от
-- левого края) и масштаб. По центру экрана, если помещается между left и right (занято слева и справа, px от
-- краёв), иначе — как можно ближе к центру; не помещается и так — мельче.
function HudMath.Fit(width: number, screen: number, left: number, right: number, scale: number): (number, number)
	local gap = UITokens.CarryHud.BandGap
	local low, high = left + gap, screen - right - gap
	local room = math.max(high - low, 1)
	local s = math.min(scale, room / width)
	local half = width * s / 2
	local center = math.clamp(screen / 2, low + half, math.max(high - half, low + half))
	return center, s
end

return HudMath

-- Проверка раскладки HUD (вид — по референсу владельца 2026-11-17) без Studio: расчёты Shared/HudMath на размерах
-- телефонов, планшета и мониторов — в том числе тех, что в окне Studio не показать (1920 × 1080). Для каждого экрана:
-- масштаб в пределах, столбик меню (4 кнопки и 5 — с кнопкой «Тест» владельца; во время обучения — под панелью) стоит
-- между кнопками Roblox и монетами, кнопки на касании не мельче MIN_BUTTON px, таймер не заходит на кнопку прыжка,
-- ноша (слот, название и «Бросить») помещается между монетами и таймером (на самом узком телефоне — без слота),
-- «Удар» над прыжком не выходит за экран. Размеры блоков с текстом (монеты, таймер) — с запасом (NOMINAL). Запуск:
--   lune run scripts/lune/check_hud.luau

local process = require("@lune/process")
local roblox = require("@lune/roblox")

local Env = require("./env")

local Vector2 = (roblox :: any).Vector2

local UITokens = Env.Require("ReplicatedStorage.Shared.Config.UITokens")
local HudMath = Env.Require("ReplicatedStorage.Shared.HudMath")

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	if not ok then
		print("  ОШИБКА " .. message)
		failed += 1
	else
		passed += 1
	end
end

local TOPBAR = UITokens.Hud.TopBar
-- px: сторона квадратной кнопки меню на касании (квадратная кнопка референса — 34 × 36 px при экране 880 × 405);
-- на экране ниже TINY — MIN_BUTTON_TINY
local MIN_BUTTON = 40
local MIN_BUTTON_TINY, TINY = 33, 340 -- 33 px — пять кнопок (с «Тест» владельца) на экране высотой 320
local MIN_DROP = 32 -- px: высота кнопки «Бросить» на касании
-- ширина блоков с текстом при масштабе 1 с запасом: «$999.9K» и «Судная ночь — сегодня»
local NOMINAL = { Stats = 180, Timer = 235 }
local TUTORIAL = UITokens.Tutorial

local SCREENS = {
	{ "iPhone SE (1-го поколения)", 568, 320, true },
	{ "iPhone SE", 667, 375, true },
	{ "Android 740 × 360", 740, 360, true },
	{ "iPhone 14", 844, 390, true },
	{ "iPhone 14 Pro Max", 932, 430, true },
	{ "iPad", 1024, 768, true },
	{ "iPad Pro 12.9", 1366, 1024, true },
	{ "окно ПК 800 × 500", 800, 500, false },
	{ "окно ПК 1024 × 576", 1024, 576, false },
	{ "ПК 1280 × 720", 1280, 720, false },
	{ "ПК 1366 × 768", 1366, 768, false },
	{ "ПК 1920 × 1080", 1920, 1080, false },
	{ "ПК 2560 × 1440", 2560, 1440, false },
}

print("Раскладка HUD по экранам:")
for _, screen in SCREENS do
	local name, w, h, touch = screen[1], screen[2], screen[3], screen[4]
	local view = Vector2.new(w, h)
	local scale = HudMath.Scale(view, touch)
	local info = HudMath.InfoScale(view, touch)
	local notes = {}
	check(
		scale >= UITokens.Hud.MinScale and scale <= UITokens.Hud.MaxScale,
		("%s: масштаб %.2f вне пределов"):format(name, scale)
	)
	check(
		not touch or scale >= UITokens.Hud.TouchScale,
		("%s: на касании масштаб %.2f мал"):format(name, scale)
	)

	-- столбик меню: обычная игра (4 кнопки), владелец (5), обучение (панель слева сверху, «Защита» скрыта — 3 и 4)
	local statsTop = h - HudMath.StatsHeight() * info
	local tutorialBottom = TOPBAR
		+ TUTORIAL.Top
		+ TUTORIAL.Panel.Y
			* math.clamp(
				math.min(w / UITokens.Hud.Reference.X, h / UITokens.Hud.Reference.Y),
				UITokens.Hud.MinScale,
				UITokens.Hud.MaxScale
			)
	for _, case in
		{
			{ 4, TOPBAR, "меню" },
			{ 5, TOPBAR, "меню владельца" },
			{ 3, tutorialBottom, "меню в обучении" },
		}
	do
		local count, limit, label = case[1], case[2], case[3]
		local top, s = HudMath.Menu(count, h, scale, limit, info)
		local bottom = top + HudMath.MenuHeight(count) * s
		check(top >= limit, ("%s: %s выше границы (%d < %d)"):format(name, label, top, limit))
		check(
			bottom <= statsTop + 0.5,
			("%s: %s заходит на монеты (%d > %d)"):format(name, label, bottom, statsTop)
		)
		local button = UITokens.MenuHud.Button.Y * s
		check(
			not touch or button >= (if h < TINY then MIN_BUTTON_TINY else MIN_BUTTON),
			("%s: %s — кнопка %.0f px, меньше %d"):format(name, label, button, MIN_BUTTON)
		)
		if count == 4 then
			table.insert(notes, ("меню %d–%d, кнопка %.0f px"):format(top, bottom, button))
		end
	end

	-- таймер и прыжок
	local jump = HudMath.Jump(view, touch)
	local timerRight = HudMath.TimerRight(view, touch)
	local timerHeight = (UITokens.TimeHud.Icon + UITokens.TimeHud.Margin.Y) * info
	if jump then
		-- таймер либо левее кнопки прыжка, либо целиком под ней (кнопка высоко — планшет)
		local buttonBottom = jump.Top - (if jump == UITokens.Hud.JumpSmall then 70 else 120)
		check(
			timerRight >= jump.Left or timerHeight <= buttonBottom,
			("%s: таймер заходит на кнопку прыжка (высота %.0f, под кнопкой %.0f)"):format(
				name,
				timerHeight,
				buttonBottom
			)
		)
		-- «Удар» над прыжком
		local pvp = UITokens.Pvp
		local pvpScale = math.max(scale, pvp.MinTouch / pvp.Button.Y)
		local pvpTop = h - (jump.Top + pvp.JumpGap) - pvp.Button.Y * pvpScale
		check(pvpTop >= TOPBAR, ("%s: «Удар» выше кнопок Roblox (%d)"):format(name, pvpTop))
		check(pvp.Right + pvp.Button.X * pvpScale <= w, ("%s: «Удар» шире экрана"):format(name))
	end
	check(not jump or timerRight >= UITokens.TimeHud.Margin.X, name .. ": таймер за правым краем")

	-- ноша (слот, название и «Бросить») между монетами и таймером
	local C = UITokens.CarryHud
	local width = C.Slot + C.Gap + C.Side
	local left = UITokens.StatsHud.Margin.X + NOMINAL.Stats * info
	local right = timerRight + NOMINAL.Timer * info
	local center, s = HudMath.Fit(width, w, left, right, scale)
	local mode = "слот"
	if s < scale * C.MinFull then
		-- самый узкий телефон: слот убирается, остаются название и кнопка «Бросить»
		width = C.Button.X
		center, s = HudMath.Fit(width, w, left, right, scale)
		mode = "кнопка"
		check(touch, ("%s: ноша не поместилась на экране без касания"):format(name))
		check(
			s >= scale * 0.98,
			("%s: кнопка «Бросить» не помещается (%.2f при масштабе %.2f)"):format(
				name,
				s,
				scale
			)
		)
	end
	check(
		not touch or C.Button.Y * s >= MIN_DROP,
		("%s: кнопка «Бросить» %.0f px, меньше %d"):format(name, C.Button.Y * s, MIN_DROP)
	)
	local x0, x1 = center - width * s / 2, center + width * s / 2
	check(
		x0 >= left + C.BandGap - 0.5,
		("%s: ноша заходит на монеты (%.0f < %.0f)"):format(name, x0, left)
	)
	check(
		x1 <= w - right - C.BandGap + 0.5,
		("%s: ноша заходит на таймер (%.0f > %.0f)"):format(name, x1, w - right)
	)
	table.insert(notes, ("ноша %s %.0f–%.0f ×%.2f"):format(mode, x0, x1, s))
	print(("  %-28s %4d × %-4d масштаб %.2f · %s"):format(name, w, h, scale, table.concat(notes, " · ")))
end

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end

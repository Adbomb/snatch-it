# Иконки HUD (2026-11-17, вид — по референсу владельца)

Значки HUD — плоские 2D. Чёрную обводку добавляет интерфейс (`Shared/StudUI` — `UI.Glyph`), в файлах её нет.
Подключены в `UITokens.HudIcons`.

## Свои плоские рисунки (в игре)

Нарисованы кодом (`scripts/hud_glyphs.py`, Pillow, без Blender). Загружены на текущий аккаунт владельца места через
Studio (upload_image). Каждая картинка просмотрена до загрузки: здание с колоннами, солнце, луна с облаком.

| Ключ | Файл | Asset ID | Где |
|---|---|---|---|
| Museum, MuseumNext | glyph_museum_256.png | 107254124592158 | кнопка «Музей», шапка и карточки окна «Улучшение музея» |
| Day | glyph_sun_256.png | 101917311109817 | таймер: день |
| Night | glyph_moon_256.png | 89574346976067 | таймер: ночь |

Первый вариант музея (четыре колонны, мелкие детали сливались) — Asset ID 96887155414046, в игре не используется.
Лист для просмотра — `glyphs_sheet.png`.

## Из библиотеки CheckUIIcons (в игре)

Белые силуэты «… White» и цветные наклейки «… 1st Outline»; проверены в Studio (отрисовались).

| Ключ | Путь в библиотеке | Где |
|---|---|---|
| Shop | Main/Shopping Cart/Shopping Cart White | кнопка «Магазин», шапка окна |
| Inventory | Item/Backpack/Backpack White | кнопка «Инвентарь», шапка окна |
| Defense | Item/Shield/Shield White | кнопка «Защита», шапка окна |
| OwnerTest | Main/Settings/Settings White | кнопка «Тест» владельца |
| Preparation | Item/Clock/Clock White | таймер: подготовка |
| DoomNight | Player/Skull/Skull White | таймер: Судная ночь |
| Coins | Currency/Coin/Golden Coin 1st Outline | монеты |
| Strength | Player/Arm/Arm 1st Outline | сила |

## Не используются (HUD v3, отклонён владельцем 2026-11-17)

Рендеры Blender в стиле D39 (`scripts/blender/d48_icons.py`, `scripts/hud_icons.py`), файлы `icon_<Ключ>_256.png` и
лист `hud_icons_sheet.png`. Загружены на аккаунт владельца, из игры убраны.

| Ключ | Файл | Asset ID |
|---|---|---|
| Shop | icon_Shop_256.png | 78001121219533 |
| Inventory | icon_Inventory_256.png | 126869080685841 |
| Museum | icon_Museum_256.png | 127909762356652 |
| Defense | icon_Defense_256.png | 107558260614980 |
| Coins | icon_Coins_256.png | 126199857200324 |
| Strength | icon_Strength_256.png | 104913722577388 |
| Day | icon_Day_256.png | 79185311821233 |
| Preparation | icon_Preparation_256.png | 132352303357158 |
| Night | icon_Night_256.png | 84779278837676 |
| DoomNight | icon_DoomNight_256.png | 81791641671725 |

Старые `icon_fist_256.png` / `_512.png` (D48 v2) не загружались.

# SNATCH IT! — UI-kit v1 (токены для кода)

Визуальный лист: [SNATCH IT! UI Kit](https://claude.ai/artifact/M2haasJyVBMcmjYN1pcUie)

Правило: в Figma рисуем только то, что Roblox умеет повторить (UICorner, UIStroke, UIGradient, жёсткая тень вторым Frame). Никакого blur, inner shadow и blend modes.

## Цвета

| Токен | Значение | Где |
|-------|----------|-----|
| Ink | #1B1530 | все обводки, тени, обводка текста |
| InkSoft | #2B2350 | фон плашки валюты, фон полос прогресса |
| Panel | #F4F8FF | фон окон и карточек |
| Header | #3D7BFF | шапки окон |
| Go | #5BEA72 → #1FA83A | главное действие |
| Info | #5CB0FF → #2366E8 | навигация |
| Stop | #FF6B6B → #D92D3A | отмена, бросить |
| Coin | #FFE15A → #F5A400 | покупка, монеты |
| Night | #B04BFF → #FF2E63 | всё, что связано с Судной ночью |
| Disabled | #C9D0DA → #8E98A8 | неактивно |

## Редкость

Common #B8C4D0 · Uncommon #4CD964 · Rare #3FA2FF · Legendary #FFB800 · Secret #FF3DAA → #8C3DFF

## Форма

- Обводка: 3 px Ink (UIStroke, Border). Текст: UIStroke 2 px Ink, Contextual.
- Скругление: кнопки 16, иконки-кнопки 18, карточки 20, окна 24, плашки 999 (UICorner 0.5 Scale).
- Кнопка: градиент сверху вниз (UIGradient Rotation 90) + нижняя тёмная полоса 6 px + тень Ink 5 px вниз. Нажатие: кнопка опускается на 4 px, тень исчезает, 0.08 с.

## Шрифты

- Логотип: Luckiest Guy (Enum.Font.LuckiestGuy) — только латиница.
- Весь остальной текст: Nunito, Heavy/ExtraBold/Bold. Кириллицу проверить в Studio на первом экране; если не отрисуется — Builder Sans Bold.

## Раскладка

- Верхний левый угол ~210×56 px — меню Roblox, не занимать.
- Телефон: левый нижний круг — джойстик, правый нижний — прыжок. Свои кнопки ставить выше/левее.
- Размеры в Scale + UIAspectRatioConstraint, минимальная кнопка на телефоне 52×52.
- Презентация экспоната: Common — только уведомление; Rare 1.5 с; Legendary 3 с; Secret 4 с + объявление серверу.

# Известные ошибки и особенности

## Игра
- В Output при старте: `ContentId: rbxassetid://203785492 failed due to: Asset type does not match` (×3).
  Не из нашего кода (в `src/` этого ID нет) — вероятно, плагин или настройки места. Не мешает.
- Замена Plastic на «LegoStuds» действует на всё Plastic, включая части аватаров игроков (пупырышки на теле).
  Пока считается допустимым для LEGO-стиля.
- Интерфейс пока на UIKit/UITokens; переход на Stud-UI (D20) — шаг 8.
- Stud-UI: 9 собственных текстур набора (`UI.Assets.Studs`, `ShopHeader`, `Basket`, `RobuxCoin`, плашки
  редкостей `UI.Rarities.*.panel`) в нашем месте дают Failure — без них нет пупырышков на кнопках и плашек.
  Из реестра иконок не грузятся 7: Nature/Banana/Banana_1st, Social/Discord/Gamepad_* (5), Social/Twitter/Bird_White.
  Решение D32: плашки и заголовки — Frame + UIGradient + UIStroke, пупырышки — LegoStuds, монета Robux — иконка реестра.

## Перед релизом (загрузить в Roblox / проверить)
- Всё, что подключено через `rbxasset://` (локальные файлы Studio), у игроков не загрузится — заменить загруженными ID.
  Сейчас таких нет: LegoStuds (3 карты), палитра предметов и меш уточки уже загружены (`Config/Textures`, `Config/ItemModels`).
- `GameConfig.DevMode = false`.
- Звуки `GameConfig.Sounds` — ID выбирает дизайнер.

## Studio и инструменты
- `require` из MCP (Edit и Play) получает отдельную копию модулей, не ту, что у игры, и кэширует её.
  Реальное состояние сервера через неё не видно; для предпросмотра — `World/FreshRequire`.
- `ProximityPrompt:InputHoldBegin()` из MCP после перезапуска Studio перестал срабатывать.
  Нажимать подсказки через MCP `user_keyboard_input` (E/R/F), кнопки окон — через `user_mouse_input`.
- Сервер видит телепорт персонажа с задержкой: после `root.CFrame = …` подождать ~1 с перед действием.
- `screen_capture` даёт чёрный кадр, если Studio не на переднем плане. Выводить вперёд самому: `AppActivate`
  из WScript.Shell возвращает False (Windows не даёт), работает user32 `SetForegroundWindow` с нажатием Alt
  (`keybd_event 0x12`) по `MainWindowHandle` процесса RobloxStudioBeta. Снимки — по одному: пачка из нескольких
  `screen_capture` подряд даёт таймауты и MCP отключается на ~10 с — `list_roblox_studios` и повторить.
- Для снимков в Edit вода (Terrain) и песок не видны: воду строит только Play, песок закрыт Baseplate.
  Временно: Baseplate в ServerStorage, `WorldBuilder.BuildWater()`, после снимков `Terrain:Clear()` и вернуть.
- В клиенте Play `loadstring` недоступен (в Edit — доступен).
- `Lighting.Technology` в этой версии Studio нет (есть `LightingStyle`, `PrioritizeLightingQuality`).
  `MaterialService.PlasticName` скрипты и плагины не пишут — поэтому `LegoMaterial` вызывает
  `SetBaseMaterialOverride` на сервере и клиенте.
- Rojo: изменения `$properties` служб из проекта на лету не применяются; после перезапуска `rojo serve`
  плагин надо переподключить (кнопка Connect в Studio). Вместо этого значения Lighting из проекта можно
  выставить через MCP в Edit (те же числа, что в `default.project.json`) — так сделано 2026-10-29. Rojo 7.7.0 — `~/.aftman/tool-storage/rojo-rbx/rojo/7.7.0/rojo.exe`.
- `WeldConstraint`, созданный до попадания деталей в мир, не тянет приваренную деталь, когда закреплённый
  корень переставляют через CFrame. Для меша предмета используется `Weld` с C0/C1.
- Blender MCP в сессии Claude Code не подключён; Blender 5.2 запускается из командной строки
  (`--background --python`), пути к файлам передавать абсолютные.
- Импорт FBX в Studio через MCP невозможен — только File → Import 3D руками.
- Windows PowerShell 5.1 читает `.ps1` в UTF-8 только с BOM.

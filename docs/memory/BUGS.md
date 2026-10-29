# Известные ошибки и особенности

## Игра
- В Output при старте: `ContentId: rbxassetid://203785492 failed due to: Asset type does not match` (×3).
  Не из нашего кода (в `src/` этого ID нет) — вероятно, плагин или настройки места. Не мешает.
- Замена Plastic на «LegoStuds» действует на всё Plastic, включая части аватаров игроков (пупырышки на теле).
  Пока считается допустимым для LEGO-стиля.
- Интерфейс пока по UI_KIT.md, а стандарт заказчика — Check-UI; решение о переходе не принято (см. NEXT_TASK).

## Studio и инструменты
- `require` из MCP (Edit и Play) получает отдельную копию модулей, не ту, что у игры, и кэширует её.
  Реальное состояние сервера через неё не видно; для предпросмотра — `World/FreshRequire`.
- `ProximityPrompt:InputHoldBegin()` из MCP после перезапуска Studio перестал срабатывать.
  Нажимать подсказки через MCP `user_keyboard_input` (E/R/F), кнопки окон — через `user_mouse_input`.
- Сервер видит телепорт персонажа с задержкой: после `root.CFrame = …` подождать ~1 с перед действием.
- `screen_capture` даёт чёрный кадр, если Studio не на переднем плане. После таймаутов снимков MCP иногда
  отключается на несколько секунд — `list_roblox_studios` и повторить.
- В клиенте Play `loadstring` недоступен (в Edit — доступен).
- `Lighting.Technology` в этой версии Studio нет (есть `LightingStyle`, `PrioritizeLightingQuality`).
  `MaterialService.PlasticName` скрипты и плагины не пишут — поэтому `LegoMaterial` вызывает
  `SetBaseMaterialOverride` на сервере и клиенте.
- Rojo: изменения `$properties` служб из проекта на лету не применяются; после перезапуска `rojo serve`
  плагин надо переподключить (кнопка Connect в Studio). Rojo 7.7.0 — `~/.aftman/tool-storage/rojo-rbx/rojo/7.7.0/rojo.exe`.
- Windows PowerShell 5.1 читает `.ps1` в UTF-8 только с BOM.

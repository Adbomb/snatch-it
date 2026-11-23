# Ввод в курс дела для новой сессии Claude

Составлено 2026-11-18 в конце длинной сессии (HUD v3 → v4). Здесь — как устроен проект, как работать с владельцем,
какие инструменты и где что лежит. **Задач здесь нет — их даёт владелец.** Раздел 9 — только состояние на сейчас.

Порядок чтения в начале сессии: `CLAUDE.md` → этот файл → верхний блок `docs/memory/NEXT_TASK.md` → при нужде
`ARCHITECTURE.md`, `BUGS.md`, нужные решения в `DESIGN.md`.

---

## 1. Проект в двух словах

**«Утащи это!» / SNATCH IT!** — Roblox-игра на Luau (место «Snatch It DEV»: Experience `10776417796`, Place
`81392528393796`, приватное). Код в репозитории `C:\Users\uzhgb\snatch-it`, в Studio попадает через Rojo.

Игровой круг: у игрока музей на участке (5 участков в линию). Впереди — 10 уровней-зон, у каждой босс и коллекция
из 30 «живых существ»-экспонатов. Существо ловят Ловибумом (мини-игра от первого лица, Ловибумы покупаются в
магазине за монеты, набор ×3 — D61), потом бой с боссом за добычу, добычу несут в музей и выставляют на постамент
(или кладут в сундук-инвентарь). Экспонаты дают доход в секунду. Сила качается гантелью во дворе (10 уровней).
День/ночь: раз в цикл — **Судная ночь**, когда можно красть из чужих музеев (PvP «Удар», защита музея: ловушки,
лазер, дверь, робот, капкан; устройства взлома). Музей улучшается до уровня 10 (D56: 20 мест). Есть обучение
новичка (5 шагов), окна «Магазин», «Инвентарь», «Улучшение музея», «Защита».

Готово в игре: боссы 1–4 и 10 (дракон №10 — только на тестовом сервере владельца, этап D запрещён), зоны 1–4
оформлены; 5–9 — заготовки (план `docs/BOSSES_5_10_PLAN.md` ждёт утверждения).

## 2. Владелец и как с ним работать

- Пишет по-русски, часто большими ТЗ-вставками. Отвечать по-русски, коротко и по делу.
- **ТЗ владельца — главный приказ на сейчас.** Если оно расходится с `CLAUDE.md` (например, `CLAUDE.md` велит
  push после каждого шага, а последние ТЗ — «не коммить и не пушь без моего отдельного разрешения») — действует
  последнее слово владельца. Сомнение — спросить.
- `DESIGN.md` — источник правды (решения D1…D62). Нет решения — спросить, не придумывать. Менять `DESIGN.md` —
  только с его «ок».
- **Референс = буквальная копия вида** (память `reference-means-literal-copy`). HUD v3 был отклонён именно за
  «авторскую интерпретацию»: свои Blender-иконки и Stud-UI-стиль вместо вида с его скриншота.
- Не просить его заходить в игру после каждой правки — проверять самому через Studio MCP. Если без него никак —
  одна короткая инструкция и зачем.
- Честность: эмуляцию телефона в Studio называть эмуляцией; серверные тесты не выдавать за проверку отрисовки;
  что не проверено — так и писать. Не говорить «исправлено» без подтверждения.
- Визуальную работу показывать снимками рядом с референсом (до / после), не меньше двух кругов
  «снимок → разбор → правка» (память `visual-render-review-loop`).
- Он любит, когда экран свободен: всё мелкое и по краям, центр и верх пустые. Последнее его слово по HUD: кнопки
  меню — только значки, без подписей («подписи занимают лишнее место»).

## 3. Постоянные запреты

- Не публиковать игру, не делать commit и push без отдельного разрешения (последние ТЗ 2026-11-17).
- Не переводить Experience в Public, не создавать новый Experience, не удалять сохранения игроков.
- Не менять утверждённые механики, экономику (D56), цены, награды, сохранения; не трогать боссов, карты и
  модель дракона без прямой задачи; этап D (дракон в зоне 10 для всех) и зону 10 — не начинать.
- **Никакой наготы и ничего пограничного** в картинках: аккаунт владельца забанен за две загруженные классические
  картины (память `roblox-nudity-ban`). Каждую картинку смотреть до `upload_image`, пачками непросмотренное не
  грузить, картин с людьми не делать. Не предлагать новый аккаунт.
- Запрещённые Asset ID `115188607358965` и `91016959329136` — только в `check_project.FORBIDDEN_IDS`. Asset ID
  не выдумывать: только загруженные нами, переданные владельцем или проверенные в Studio.
- Не копировать чужие ассеты из референсов; можно лицензированные (CheckUIIcons — MIT) или свои.
- Личные данные владельца (почта, ник Roblox, аватар) не писать в репозиторий и во внешние запросы; персонажа на
  снимках прятать (`LocalTransparencyModifier = 1`).
- `rojo serve` из сессии не запускать; сторож Rojo — только по прямой просьбе владельца (раздел 6).
- Настройки Norton и защиты Windows не трогать.

## 4. Документы

| Где | Что |
|---|---|
| `CLAUDE.md` | правила разработки (код, стиль, проверки, коммиты) |
| `DESIGN.md` | все решения D1…D62 (зачёркнутые заменены более поздними) |
| `docs/memory/NEXT_TASK.md` | текущая и следующая задача, открытые вопросы (одна страница, ≤ 150 строк) |
| `docs/memory/HISTORY.md` | подробная история этапов (прежний NEXT_TASK, сверху — свежее) |
| `docs/OVERVIEW.md` | обзор проекта: игра, системы, боссы, открытые вопросы |
| `docs/memory/ARCHITECTURE.md` | устройство кода, данных, мира, проверок |
| `docs/memory/BUGS.md` | особенности Roblox, Studio, MCP, Rojo, публикации — **читать перед работой в Studio** |
| `docs/memory/PROGRESS.md` | завершённые этапы с коммитами (свежее сверху) |
| `docs/BOSSES_5_10_PLAN.md`, `docs/CATALOG.md`, `docs/IMPORT_LEVEL2.md`, `docs/D48_INTEGRATION.md` | планы, каталог коллекций, порядок импорта мешей, интеграция музея |
| `assets/concepts/<этап>/REPORT*.md` | отчёты этапов со снимками |
| `UI_KIT.md` | устарел; действует только раскладка |

Автопамять Claude (вне репозитория): `C:\Users\uzhgb\.claude\projects\C--Users-uzhgb-snatch-it\memory\` —
индекс `MEMORY.md` подгружается сам; там выводы о владельце и инструментах (бан, Norton, Rojo, стиль D39, боссы).

## 5. Код

**Rojo** (`default.project.json`): `src/shared` → `ReplicatedStorage.Shared`, `src/server` →
`ServerScriptService.Server`, `src/client` → `StarterPlayer.StarterPlayerScripts.Client`; там же свойства места
(StreamingEnabled = false, свет, MaterialService).

**Правила** (подробно — `CLAUDE.md`): сервер решает всё, клиент только показывает и просит; каждый обработчик
сам проверяет владельца, состояние, расстояние, руки, место. Состояния предметов — только через
`Services/ItemRegistry` (проверки → запись профиля `DataService` → переход в реестре, без `yield` между ними).
Числа баланса — `Config/GameConfig` (+ `Progression`), числа вида — `Config/UITokens`. Модели мира — кодом
(`World/ModelBuilder`, `World/Models/*`), всё Plastic + MaterialVariant LegoSquares (D36). Комментарии и тексты —
по-русски, шапка модуля: что делает и от чего зависит. StyLua (табы, 120) и selene.

**Сервер** (`src/server`): `Main.server` (старт, вход игрока, тестовый сервер владельца), `Services/*`
(DataService — ProfileStore, PlotService, CarryService, MuseumService, InventoryService, BossService,
BattleService, CatchService, ShopService, DefenseService, TheftService, PvpService, NightService, TimeService,
IncomeService — доход и `leaderstats «Доход/сек»`, TutorialService, MuseumUpgradeService, OwnerTestService…),
`Util/DevTools` (команды проверки, только Studio + DevMode), `Tests/ServerTests` (124 теста), `World/*`.

**Клиент** (`src/client`): `Main.client` запускает `Controllers/*` (по контроллеру на окно и систему HUD),
`UI/MenuHud` (столбик кнопок слева), `UI/HudLayout` (масштаб, зоны экрана, прыжок, свободные полосы),
`UI/HudIcons` (ключ → картинка), `UI/UIKit` (старый набор, ещё у табличек и тостов).

**Общее** (`src/shared`): `Config/*`, `HudMath` (чистая математика раскладки — её же проверяет Lune), `GameTime`,
`Remotes`, `StudUI/StudUI` (набор интерфейса), `StudUI/StudMotion` (пружины, окна, размытие),
`StudUI/CheckUIIcons` (1022 иконки, путь «Категория/Подкатегория/Имя»).

**Интерфейс сейчас** (D20/D32 — стандарт Stud-UI, но вид переключён на референс владельца, в `DESIGN.md` ещё не
записано): в конце `StudUI.luau` — раздел 7 «скин Flat» (`UI.Skin = "Flat"`). Те же вызовы `UI.Button`,
`UI.Window`, `UI.InsetBox`, `UI.Pill`, `UI.StudPanel`, `UI.CloseButton`, `UI.Recolor` рисуют плоские кнопки
референса: заливка в два тона, тонкий тёмный контур, светлая рамка внутри, белый Montserrat с чёрной обводкой;
окна — цветная шапка и тёмное полупрозрачное тело. `UI.Glyph` — белый силуэт с чёрной обводкой (копии со сдвигом);
силуэты помечаются через `HudIcons` (значение `{ glyph = … }`). Цвета тем — `UI.FlatThemes` (зелёный, голубой,
красный, оранжевый, бирюзовый сняты пипеткой с референса). `UI.Skin = "Stud"` возвращает прежний вид набора.
Французские имена (`Fenetre`, `Entete`, `Corps`, `Face`, `Texte`, `Ombre`…) не менять — по ним работают окна.

Тестовый режим владельца (`Util/OwnerTest`, `OwnerTestService`, `OwnerTestController`): в DEV-месте владелец
кнопкой «Тест» в HUD или командой чата `/test` уходит на резервный сервер без сохранений, где открыт дракон №10
(«К дракону», «Бой», «Победа», «День», «Ночь», «Выход»).

## 6. Инструменты

**Версии** — `rokit.toml` (Rojo 7.7.1, selene 0.32.0, StyLua 2.6.0); бинарники в `~/.aftman/bin`
(`rojo`, `lune`, `stylua`, `selene`). Python 3 с Pillow — для скриптов `scripts/*.py`.

**Rojo.** Сервер держит сторож `scripts/rojo-serve.ps1` — отдельный процесс, сам перезапускает Rojo (журнал
`%TEMP%\snatch-it-rojo.log`). Жив ли: `Invoke-WebRequest http://127.0.0.1:34872/api/rojo` (не `localhost`).
Запуск сторожа — `Invoke-CimMethod Win32_Process Create` с `powershell -NoProfile -ExecutionPolicy Bypass -File
scripts\rojo-serve.ps1`, **только если владелец попросил** («подключись к роджо»). Плагин в Studio обычно
подключается сам; если висит на «Connect» — `~\.aftman\bin\rojo.exe plugin install` из корня (перезагружает
плагин, подождать ~30 с). Проверка — Source модуля в Studio совпадает с диском. Пока Rojo работает, папки в `src`
не удалять целиком: сначала файлы, потом папку. Подробно — память `rojo-connect-from-edit`, `BUGS.md`.

**Roblox Studio MCP** (`mcp__Roblox_Studio__*`, схемы грузятся через ToolSearch): `list_roblox_studios` (id
меняется после перезапуска Studio), `get_studio_state`, `execute_luau` (Edit / Server / Client), `start_stop_play`,
`get_console_output`, `screen_capture`, `user_mouse_input` и `user_keyboard_input` (только Client; кликать по
`instance_path`), `upload_image` (нужен http-адрес: `python -m http.server 35031 --bind 127.0.0.1` в папке с
картинками, после загрузки остановить), `save_place`, `open_cloud_invoke`. Особенности (обязательно прочитать
`BUGS.md` «Studio и инструменты»):
- `require` из MCP даёт отдельную копию модулей — данные игры смотреть атрибутами, действия — через DevTools или
  клики по GUI.
- `screen_capture` не снимает CoreGui (панель Roblox) — для честных снимков `scripts/studio/window.ps1`.
- Escape из MCP открывает невидимое на снимках меню Roblox, оно ловит клики — окна закрывать «X»
  (`…Fenetre.Entete.Fermer`).
- Пока открыто окно меню, остальной HUD выключен (StudMotion прячет ScreenGui).
- Studio в фоне не рендерит: снимки — с окном на переднем плане (`window.ps1 -Action front`).
- MCP-вызов на клиенте возвращает тип камеры, который был в начале.

**DevTools в Play** (сервер, атрибуты `ServerStorage.DevTools`): `Command` = строка, ответ — `CommandResult`.
Команды: `Tutorial <uid> Done`, `GiveCoins <uid> <n>`, `Strength <uid> <n>`, `TimeSkip Day|Preparation|Night|DoomNight <с>`,
`TimeScale`, `TimeReset`, `MuseumLevel <uid> <1–10>`, `Exhibit <uid> <место> <ItemId>` (паузы ≥ 1.2 с, сначала день),
`Lovibums <uid> <уровень> Boom|Turbo|Mega <n>`, `GiveDefense <uid> <вид> <n>`, `InstallDefense`, `Fight`, `FightTest`,
`BossSlot`, `CatchRoll`, `CatchThrow`. Серверные тесты: атрибут `RunTests` = "" (все) или часть имени, отчёт —
`TestReport` («идёт» → текст; полный прогон — несколько минут, сервер в это время отвечает медленно).
Профиль в Studio не сохраняется (DataStore выключен) — после каждого Play подготовку повторять.
Известные ошибки консоли, которые не баги: `rbxassethash`, `203785492 … Asset type does not match`,
`StudioAccessToApisNotAllowed … ____PS`.

**Снимки и экраны без эмулятора** (эмулятор устройств из MCP недоступен):
- `scripts/studio/window.ps1 -Action size -Process RobloxStudioBeta -Width W -Height H` → вид игры = окно −
  455 × 563: 1299×953 → 844×390 (телефон), 1122×938 → 667×375, 1735×1283 → 1280×720; потом `-Action max`.
  1920×1080 на этом мониторе не помещается — его проверяет только Lune.
- Раскладка телефона: атрибуты игрока `DevTouch = true` и `DevViewport = Vector2` (работают при DevMode); кнопки
  Roblox (прыжок, джойстик) в Studio не рисуются — на снимках полупрозрачные заглушки (`scripts/studio/hud_probe.luau`
  ставит их и ищет пересечения прямоугольников HUD).
- `window.ps1 -Action shot -Out x.png` → `python scripts/studio/crop_view.py x.png view.png [zoom]` → лист сравнения
  `python scripts/studio/compare_shots.py out.jpg "Референс" ref.jpg "Сейчас" view.png`.
- После проверки: Stop, убрать `__PhoneMock` и прочие `__`-объекты, развернуть окно Studio.

**Проверки без Studio** (из корня репозитория):
- `for f in scripts/lune/check_*.luau; do lune run "$f"; done` — 20 наборов (`check_hud` — раскладка HUD на 13
  экранах, `check_config` — данные и токены интерфейса, `check_catch`, `check_defense`, `check_theft`…).
- `python scripts/check_project.py` — запрещённые ассеты, `require`, модели.
- `PYTHONIOENCODING=utf-8 python scripts/d48_to_luau.py --check`.
- `selene <файлы>`; `stylua --check <файлы>` — только свои файлы по именам: на всю папку StyLua переформатирует
  чужое; `ServerTests.luau`, `GameConfig.luau`, `InventoryController.luau`, `ShopController.luau` имеют старые
  расхождения со StyLua — не форматировать целиком.

**Blender.** Модели, иконки и концепты — скриптами в `scripts/blender/` (Blender без интерфейса) и через Blender MCP
(`mcp__blender__*`). Для HUD Blender больше не использовать (решение владельца). Особенности uv/Norton — память
`uv-norton-tls-blender-mcp`.

**Публикация** (только с разрешения): MCP публиковать не умеет; File → Publish to Roblox (Alt+P) в окне Studio
(`window.ps1 -Action keys -Text "%p"`), итог — строка Output «Published new changes». Обычный Roblox Player на этом
ПК не входит в игру (Norton подменяет TLS) — проверить опубликованное можно только с телефона владельца.

**Референсы из чата.** Картинки, что владелец вставляет в чат, после сжатия контекста пропадают из памяти, но
лежат base64 в журнале сессии `C:\Users\uzhgb\.claude\projects\C--Users-uzhgb-snatch-it\<id>.jsonl`. Референс HUD
уже сохранён: `assets/concepts/hud_v4/reference_owner.jpeg`.

## 7. Где что лежит

- `assets/concepts/<этап>/` — концепты, листы, отчёты, снимки этапов (`hud_v3/`, `hud_v4/`, `bosses_5_10/`, `boss4/`…).
- `assets/ui/hud/` — значки HUD: свои плоские `glyph_*_256.png` (`scripts/hud_glyphs.py`), лист `glyphs_sheet.png`,
  ID — `IDS.md`; старые Blender-иконки `icon_*` в игре не используются.
- `assets/models/`, `assets/textures/` — FBX и карты; `scripts/bind_maps.py`, `bind_meshes.py`, `make_looks.py` —
  привязка после загрузки (порядок — `docs/IMPORT_LEVEL2.md`).
- `scripts/lune/` — проверки; `scripts/studio/` — вставки для MCP и помощники снимков; `scripts/sim/` — симуляторы
  экономики.

## 8. Роли контроллеров HUD (раскладка по референсу)

- Слева посередине — `UI/MenuHud`: квадратные кнопки-значки «Магазин» (зелёная, корзина), «Инвентарь» (голубая,
  рюкзак, клавиша B), «Музей» (оранжевая, здание), «Защита» (красная, щит), у владельца ещё «Тест» (бирюзовая,
  шестерёнка). Название кнопки — атрибут `Label`.
- Слева внизу — `GymController`: сила и монеты (2D-наклейка и число курсивом).
- Справа внизу — `TimeController`: значок фазы и две строки курсивом; на телефоне левее кнопки прыжка.
- Снизу по центру — `CarryController`: слот с 3D-видом ноши, название цветом редкости, «Бросить» (G на ПК).
- Сверху по центру — короткая плашка зоны (`ZoneController`) и уведомления (`NotifyController`); над прыжком —
  «Удар» в Судную ночь (`PvpController`); слева сверху — панель обучения (`TutorialController`).
- Доход в секунду — только в списке игроков Roblox (`IncomeService`, leaderstats «Доход/сек»).

## 9. Состояние на 2026-11-18 (не задачи)

- **Git:** HEAD `ad82832` (последнее в `origin/main`). Не закоммичены HUD v3 и поверх него HUD v4 — 27 изменённых
  файлов в `src/`, `docs/memory/`, `scripts/` и новые файлы (`ONBOARDING.md`, `scripts/hud_glyphs.py`,
  `scripts/studio/window.ps1`, `crop_view.py`, `compare_shots.py`, `assets/ui/hud/glyph_*`, `assets/concepts/hud_v4/`,
  много старых концептов боссов). Ничего не опубликовано: в DEV — версия 104 (прежний HUD).
- **HUD v4 (вид по референсу):** сделан и снят в Studio на 844×390, 667×375, 1280×720, 2121×845 (эмуляция,
  пересечений нет); снимки и сравнение с референсом — `assets/concepts/hud_v4/`. На тех снимках у кнопок меню
  ещё есть подписи; после них по слову владельца кнопки стали квадратными значками без подписей — **это изменение
  в Studio ещё не проверено**, Lune `check_hud` (218 проверок) проходит.
- **Не сделано по HUD v4:** результат ServerTests после изменений не получен (Studio закрылась во время прогона;
  прежний результат — 124/124 на HUD v3); в новом стиле не осмотрены поимка, уведомления, «Удар», панель «Тест»;
  отчёт `assets/concepts/hud_v4/REPORT*.md` не написан; `ARCHITECTURE.md` (блок «HUD v3»), `BUGS.md` и
  `NEXT_TASK.md` описывают ещё HUD v3.
- **Studio и Rojo:** Studio открыта на «Snatch It DEV» (Edit). 2026-11-18 по просьбе владельца сторож Rojo запущен,
  плагин переподключился сам, 214 скриптов в Studio совпадают с диском (HUD v4 теперь в Studio). Новая сессия —
  сначала проверить, жив ли сервер (раздел 6).
- **Переработка «небоскрёб»** (ТЗ 2026-11-18): аудит и план — `docs/TOWER_PLAN.md`, ждёт ответов владельца (§7).
- **Решения за владельцем:** коммит и push; публикация в DEV; запись нового вида HUD в `DESIGN.md` (расходится с
  D20/D32 — стиль Stud-UI, D48 v2, D49–D51, D55, D56); дракон в зоне 10 для всех (этап D); панель Ловибумов внизу
  по центру (решения нет); план боссов 5–10.

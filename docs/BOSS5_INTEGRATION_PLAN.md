# Босс 5 «Йети-коллекционер»: план подключения к игре (ждёт «ок» владельца)

Загружено 2026-11-24:
- модели Open Cloud: Йети `115856961352655` (31 часть), существа `132714481201297` (155 частей, 30 существ);
- 62 из 66 карт.

ID лежат в файлах:
- `assets/models/Boss5_models.json`;
- `assets/models/Boss5_meshids.json` — сверено со скелетами, все 186 частей;
- `assets/textures/art/boss5/Boss5_maps.json`;
- `assets/textures/art/Boss5Yeti_maps.json`.

Карты моржа №5 и филина №18 (4 штуки) ждут просмотра: после исправления групп частей у них новая развёртка.
Порядок — как у боссов 4 и 10. По D64 п. 7 босс остаётся **закрытым** до общего выпуска: его видно только в Studio
и на тестовом сервере владельца.

## Файлы

### Генераторы (scripts)

| Файл | Что делает |
|---|---|
| `scripts/boss5_to_luau.py` (новый) | Из `Boss5_Yeti.rig.json` и `anim.json` пишет `Config/Boss5YetiRig` и 10 модулей `Config/Boss5YetiClips/*` (как `boss10_to_luau.py`). Канал `lens` клипов → `BossClips.Lens`. Контур тела `Body` (капсулы) — для дальности удара. |
| `scripts/creature_rigs_to_luau.py` | Добавить босса 5: 30 существ → `Config/CreatureRigs` и строки `creature5(...)` в `Config/Items` между метками D64. Доход, вес D58 и имена — из каталога и `weights.json`. |
| `scripts/boss5_bind_after_import.py` (новый) | `Boss5_meshids.json` и карты → `bind_meshes.py` и `bind_maps.py` → `ItemModels.CREATURE_MESHES`, `BossModels[5]`; затем `make_looks.py` (шаблоны `Looks`). Проверки — как у `boss4_bind_after_import.py`. |
| `scripts/lune/check_boss5_clips.luau` (новый) | Клипы в Luau: под землю 0 кадров, недотяг ног 0, `lens` в 0…1. |

### Конфиг (src/shared/Config)

| Файл | Изменение |
|---|---|
| `Boss5YetiRig.luau`, `Boss5YetiClips/` (новые, из генератора) | Скелет из 31 части, 10 клипов, линза и контур тела. |
| `Battle.luau` | `Bosses[5]`: база как у боссов 1–4, `Strength` — `Progression.Bosses[5]` (D56). **Дальность удара** — по контуру тела `BodyRange`, как у дракона (Йети 24.7 стада, корпус ≈ 8 стадов от центра; 9.5 от центра даёт удар изнутри тела). `AttackRange` 2.5 + `Reach` 1 = 3.5 стада. `Leash` 40, `Speed` 10, ходит за игроком (клип `walk`). `Closed = true`. |
| `BossModels.luau` | `[5]`: меши частей, карты `Head`/`Body`/`Limbs`, лёд глыбы `Block`/`BlockTop` — прозрачность 0.45, части экспонатов. |
| `CreatureRigs.luau`, `Items.luau`, `ItemModels.luau` | 30 существ зоны 5 (генератор); прозрачные части медузы и слизня — как `transparent_parts`. |
| `Catch.luau`, `MuseumLayout.luau` | Только если у зоны 5 нужны свои числа поимки и витрин. Иначе не трогать. |

### Мир (src/server/World)

| Файл | Изменение |
|---|---|
| `World/Models/GlacierHall.luau` (новый) | Арена «Ледник» по утверждённому концепт-листу (`boss5_v2/2_arena.png`): ледяной пол-площадка r ≈ 32 под рост и глыбу Йети (сон — глыба рядом, ≈ 9 стадов в сторону), одна стена ледника со смещёнными пиками (не замок), 3D-витрины без ниш-«картин», сияние неоном, сугробы. Части и Plastic по правилам, LegoSquares; бюджет ≤ 800 частей зоны (D64 п. 1). |
| `World/Models/GlacierKit.luau` (новый, если нужен) | Набор: торос, сугроб, витрина, кристалл. |
| `World/MapLayout.luau` | `Arenas[5]`: `floor`, `top`, `radius` 32, `slots` — 4 места существ на краю, не под Йети и не в зоне глыбы; пути зоны (D62) — свободны. |
| `World/ZoneDecor.luau` | Подключить «Ледник» в зону 5 вместо прежнего декора. |

### Сервер и клиент

| Файл | Изменение |
|---|---|
| `Services/BossService.luau` | `[5] = Boss5YetiRig`; сон и пробуждение с глыбой (глыба в мире ↔ на спине — уже в клипах); `Closed` — как у дракона. |
| `client/Controllers/BossAnimController.luau` | `[5] = Boss5YetiRig`; гасит линзу по каналу `lens`. |
| `shared/BossClips.luau` | Общий канал прозрачности или цвета части (линза), рядом с `Eyes` дракона. |

### Тесты

| Файл | Изменение |
|---|---|
| `server/Tests/ServerTests.luau` | Босс 5: равная сила — победа; сила 0 — поражение; удар по контуру (3.5 стада от тела); 30 существ, 4 у Йети по редкостям; закрыт вне Studio и теста владельца. |
| `scripts/lune/check_creatures.luau`, `check_config.luau` | Зона 5 в проверках. |
| `scripts/check_project.py` | `BossModels[5]`, `CREATURE_MESHES` зоны 5. |

Проверка в Studio: Play → Output → Stop. Проверки этапа 2 — без изменений. Ещё бой с Йети, сон и пробуждение,
поимка существа зоны 5, `FaceCheck` арены (видимых пар 0), снимки.

### Документы

- `DESIGN.md` — D65 «Босс 5 подключён». Пишется только после «ок» на запись.
- `docs/memory/*`.

## Решения владельца (до кода)

1. Дальность удара: по контуру тела (`BodyRange`, как у дракона) или от центра, но больше 9.5. Рекомендую контур:
   Йети широкий, от центра игрок «бьёт изнутри».
2. Радиус площадки 32 (как у Сфинкса) и место глыбы во сне справа от Йети — согласны?
3. Карты моржа и филина (лист `sheets/maps_fix_walrus_owl.png`) — можно загружать?

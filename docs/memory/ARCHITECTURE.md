# Архитектура

Обновлено: 2026-11-02. Подробности решений — `DESIGN.md`.

## Сборка
- Rojo (`default.project.json`): `src/shared` → `ReplicatedStorage.Shared`, `src/server` → `ServerScriptService.Server`,
  `src/client` → `StarterPlayer.StarterPlayerScripts.Client`.
- Там же свойства мест: `Workspace.StreamingEnabled = false` (D14), свет (LightingStyle Realistic,
  PrioritizeLightingQuality, Atmosphere, ColorCorrection, Bloom, SunRays, DepthOfField, Sky — последние четыре до 2026-11-03 были только в облачном месте), `MaterialService` с вариантами LegoSquares / LegoSquaresDeep / LegoSquaresSoft (D36) и `PlasticName`.
- Предметы-меши (V3): `scripts/blender/*.py` строит модель из LEGO-кирпичей в Blender без интерфейса →
  `assets/models/*.fbx` → импорт в Studio (File → Import 3D, делает заказчик) → ID меша и текстуры в
  `Config/ItemModels`. Текстура-палитра всех предметов — `assets/textures/item_palette.png` (4×4 цвета).
  Материал мешей — SmoothPlastic (пупырышки у модели свои). Оригинал импорта лежит в `ServerStorage.ImportedModels`.
- Произведения искусства (D39): `scripts/blender/art_style.py` (инструменты) + `art_boss<N>.py` (геометрия коллекции
  босса) → `assets/models/Art_Boss<N>.fbx` (меш `Art_<id>` на предмет; Blender z вверх, лицо в −y, низ на z = 0) и
  карты `assets/textures/art/<id>_{color,normal}.png` для SurfaceAppearance (шероховатость общая). Предпросмотр в
  Studio — EditableMesh из `<id>.json` (оси Roblox) через временный модуль `src/server/__Preview`.
  Коллекция босса 1 «Музей чудес» (D40) — `scripts/blender/art_wonders.py`: FBX на каждый предмет
  `assets/models/art/<id>.fbx`. Картина: `Art.paint_image` (изображение спереди в окно холста, пропорции сохраняются)
  и `uv_boost` (остров холста в развёртке крупнее: ≈ 500 × 650 пикселей на карте 1024²); исходники картин и их права —
  `assets/art_sources/` (`SOURCES.md`). Рамы ровняются по сетке квадратов D39 (планки 0.44–0.5, центры на шаге 0.6).
- Боссы (D40): `scripts/blender/boss<N>_<имя>.py` на тех же инструментах. Модель из подвижных частей (`Art.group`):
  после запекания `split_groups` режет меш на части с началом координат в точке вращения → FBX
  `assets/models/Boss<N>_<Имя>.fbx`, части `<Имя><Часть>`. Собирается в масштабе предметов (квадраты D39 того же
  вида) и увеличивается в SCALE раз; окклюзия печётся с разнесёнными частями (в любой позе нет чужих теней). Две
  карты 1024² (голова, тело). Позы (`POSES`: поворот части относительно родителя + сдвиг) → `rig.json` в осях Roblox
  для предпросмотра; анимации боя — процедурные Motor6D по этим частям и позам (D18, шаг 6 D40).
- Босс 3 «Крысиный король» (D54): `scripts/blender/boss3_ratking.py` → `assets/models/Boss3_RatKing.fbx` (21 часть:
  Torso → Head → Jaw, EyelidL/R, EarL/R, Crown; Torso → Cape, Pouch, Tail1 → Tail2; руки и ноги из двух частей;
  ArmLowerR → Scepter), карты `Boss3_RatKing{Head,Body,Limbs}_{color,normal}.png`. Формы — блоки и восьмигранники
  (`oct_x/oct_y/oct_z`, `regular_oct` — «пиксельный круг» ушей). Веки сдвигаются (как у пса): вверх под надбровье —
  прищур, назад внутрь головы — открыты. Скипетр в позах задаётся мировым углом (`held` считает поворот относительно
  предплечья). Режимы: `check` (сборка, грани), `quick` (рендеры без запекания; масштаб — у объекта, чтобы рисунок
  D39 был в единицах модели), `where` (где кисть, фонарь и корона в каждой позе), `rig` (модуль скелета
  `Config/Boss3RatKingRig.luau`, к игре подключается на шаге E). Листы рендеров — `assets/concepts/d54/boss3/`.
- Part-версия Крысиного короля в игре (визуальный QA, 2026-11-10; мешей нет): `scripts/blender/boss_parts.py`
  повторяет сборку `boss3_ratking.py` (подмена `Art.box/prism/frustum/extrude/frame`) и переводит 250 фигур в 387
  деталей: брусок — деталь того же размера и поворота, призма — полосы (восьмигранник — 3 ступени), усечённая
  пирамида — 2–3 ступени, рамка — бруски; оси Roblox `AX`, размер — по осям детали, поворот на 90° → без поворота
  (`aligned`). `separate()` разводит совпадающие грани (и одного цвета — пупырышки мерцают) при любом повороте
  деталей: сравнение по параллельным нормалям, перекрытие в плоскости — разделяющими осями (порог 0.04, с запасом
  к 0.05 FaceCheck); детали от больших к меньшим, веки — последними; внутри части грань меньшей — на OVERLAY 0.1,
  между частями — на 0.055; сдвиг ≤ 0.1 (своя часть) / ≤ 0.2 (другая, только внутрь; одного цвета — только наружу;
  веко — в любую сторону), деталь не уже половины исходной, 6 проходов. **Позы:** `scripts/lune/export_king_poses.luau`
  выгружает 48 поз из `Shared/BossAnim` (те же C0/C1/Transform, что в игре) в `assets/models/Boss3_RatKing.poses.json`;
  разводятся грани в покое и в 24 позах, что держатся (`held`: сон, бой, ходьба, возврат, стойка, победа,
  головокружение) — пары разных частей в позах с учётом видимости (сетка 5 × 5 по меньшей грани, как FaceCheck),
  внутри части и в покое — все. Переходы и пики ударов не разводятся (совпадение — кадр-два). `flush_pairs()` после
  разведения — видимых пар вровень 0 (с запасом и строго). Поворот в Luau — 5 знаков (4 давали пары на пороге).
  Позы сна и поражения после этого поправлены (вариант C2, 2026-11-10: мантия −7°, хвост из-под опушки) без
  пересборки деталей — `parts.json` разведён по позам D54, `poses.json` уже новый; новый запуск `boss_parts.py`
  разведёт по новым позам и может сдвинуть детали на сотые (в игре по новым позам совпадений нет).
  → `assets/models/Boss3_RatKing.parts.json` → `scripts/boss3_parts_to_luau.py` → `Config/Boss3RatKingParts.luau`.
  `BossService.makePart`: часть скелета — невидимая, блоки Plastic на Weld (`PART_BLOCKS[3]`). FaceCheck короля в
  Play — 0 пар (только покой и детали по осям); полная проверка в игре — OBB-пары по всем деталям в 15 позах — 0;
  сравнение с FBX — рендеры `king_*_{fbx,blocks}.png` (лист — `boss3_visual_qa/11`), итоговые кадры —
  `boss3_visual_qa/21`; Lune — габарит блоков части против скелета.
- Коллекция босса 3 по каталогу владельца 2026-11-08 (живые предметы и существа, D54) — `scripts/blender/art_rats.py`:
  тот же конвейер (check / quick / id…), FBX `assets/models/art/<id>.fbx`, карты `<id>_{color,normal}.png`. Свои
  помощники: `eye` (глаз-кубик лицом к −y: белок, зрачок со смещением look, блик, веко lid — прищур), `stand`
  (круглая подставка: Common — бирюзовая со светлой каймой, Rare — фиолетовая с золотой; Epic — своя гора золота),
  `chain` (хвосты из брусков), `peek_hole` (дырка в сыре с глазками). Общий кадр масштаба — каждый предмет на
  площадке 3.7 × 3.7 рядом с манекеном. Рендеры — `assets/concepts/d54/catalog_v2/` (партии — `common/` …).
  **Подвижные части (владелец 2026-11-08: предметы станут живыми существами, поимка — D55):** `part(a, имя, родитель,
  точка)` — следующие детали идут в часть скелета; корень — Stand (подставка/трон, у живого существа её можно
  скрыть). Запекание с разнесёнными частями (`explode`, как у босса) → `S.split_groups` → FBX из частей
  `Art_<id>_<Часть>` (начало координат — точка вращения) и скелет `assets/models/art/<id>.rig.json` (оси Roblox:
  parent, pivot, center, size, пробная поза). Проверка `rig_check` (каждая группа — часть, один корень) и кадр
  `Art_<id>_pose.png` в пробной позе `a.pose`; перед связыванием частей — `view_layer.update()`, иначе дети уезжают.
  Скрытые грани убираются только внутри своей части — при движении дыр нет.
  Проверка FBX против скелетов — `scripts/blender/check_rigs.py`; индекс для кода —
  `assets/models/art/Boss3Creatures.index.json` (`scripts/build_creature_index.py`); спецификация — `docs/BOSS3_CREATURES.md`.
- Поимка D55, данные и правила (этап B): `Config/Catch` (через `GameConfig.Catch`: виды и бонусы, шансы, цены — `Prices`
  утверждены для боссов 1–3, `PreliminaryPrices` 4–10 — только Studio + DevMode; `CatchRules.Prices(testMode)` собирает
  действующую таблицу 1…10, `IsPreliminary(level)`; мини-игра, блуждание, обучение), `Shared/CatchRules`
  (шанс, проверка покупки, запас `lovibums` = { L<уровень> → { вид → n } }, круг и попадание, автомат сессии, личная
  пауза), `Shared/CreatureMotion` (поза существа = функция общего времени и зерна uid: Wander / Catch / Flee / Calm;
  дискретные решения — хэш bit32, одинаков везде; FNV-1a зерна сверен с Python), `Shared/TutorialRules` (шаги
  Intro → Catch → Battle → Carry → Income → Done, миграция v3 → v4, защита стартового uid). Профиль schema 4:
  `lovibums`, `tutorial`; миграция в `DataService` после журнала передач и `Inventory.Normalize` (он теперь только
  повышает схему до 3); `DataService.BuyLovibums` / `SpendLovibum` / `Tutorial` / `SetTutorial` — без yield.
  Lune: `check_catch` (338 714 проверок), `check_tutorial`; расчёт цен и сверка конфига — `scripts/sim/lovibum_prices.py`
  (`--check`). Магазин: повторная покупка раньше `Catch.BuyGap` (0.3 с) не принимается, клиент после «Купить» ждёт
  ответа (`UITokens.Shop.BuyWait`).
- Модель броска D55 (общая): `Shared/CatchThrow` — камера поимки `Frame(home, params, height)` (от места существа
  в начале мини-игры `CreatureMotion.CatchBase` к ловящему, расстояние по размеру, FOV 70), жест `{dx, dy, speed,
  length}` в долях высоты экрана — `Parse` (не бросок: short / slow / side / bad), `Aim` (точка на вертикальной
  плоскости через место: направление → вбок, скорость → по высоте через ln), `GestureFor` (обратная, для тестов),
  `Origin`. Числа — `Config/Catch.Throw`, `Catch.Game.Camera`.
- Поимка D55 на клиенте (от первого лица): `Controllers/CatchController` — камера = `state.camera` от сервера (подлёт
  Tween), FOV, свой персонаж и HUD игры спрятаны, подписи предметов (BillboardGui у частей с ItemId) выключены;
  два ScreenGui: `CaptureVisee` (без вставок: кольца и 3D-Ловибум; координаты камеры → GUI = минус
  `AbsolutePosition + GuiInset`) и `Capture` (CoreUISafeInsets: «Уйти», заголовок, кнопка вида и список). Жест —
  только с Ловибума внизу; скорость — за последние `Throw.Window` секунд движения (замер ≤ `Grace` не обнуляет);
  шлёт «Throw», вид, жест, время; сразу `LovibumFx.LocalThrow` к той же точке. Studio: атрибуты `DevCatchScreen`
  (Vector3 ширина, высота, вырез — моделирование экрана телефона: интерфейс в рамке, снимок обрезать) и
  `DevTouch`. `Controllers/LovibumFxController` (CatchEffect: Start — Ловибум в руке у других; Throw — полёт,
  промах; попадание — вспышка, подскок, втягивание существа, падение, 3 покачивания (побег — после 1–3 по времени
  броска), поймано — закрытый Ловибум лежит, пока CatchMode = Hidden; свои броски — `pending` по времени
  отпускания, исход подставляется из CatchEffect; звуки — `GameConfig.Sounds.Lovibum`, пусто).
  `World/LovibumModel` — Part-версия из `Config/LovibumRigs` (Place одним BulkMoveTo, раскрытие когтей, SetLight).
- Обучение D55 (этап G): `Services/TutorialService` (шаги `TutorialRules`; личные существо и пёс в
  `World.Tutorial` с атрибутом TutorialOwner на `MapLayout.TutorialPoints()`; учебная поимка — `CatchService.BeginTutorial`;
  бой по сценарию на `BossService.BuildPersonal`; выдача — `ItemRegistry.CreateTutorial` (uid из профиля) → Carried;
  хуки: `CarryService.CanDrop`, `InventoryService.CanStore`, `MuseumService.CanBypassLock` / `OnDisplayed`,
  `IncomeService.OnPaid`, `NightService.IsExempt`; группа столкновений Student проходит NightBarrier; PvP, защита и
  кражи — по атрибуту игрока Tutorial (`ShopService.Sync`); `TheftLedger` — флаги student и protected).
  Выход — `TutorialService.OnPlayerLeaving` в шагах `PlayerSession.Leave` (прервать учебную поимку, убрать существо и
  пса; бой проверяет `gone()` после каждой паузы и ничего не выдаёт). Поимка — с пустыми руками; выдача (`giveCreature`)
  только на шаге Carry и без записи предмета в профиле, подобранное чужое кладёт на землю (`CarryService.Drop`).
  `CanStore` проверяют и сундук, и «снять с постамента» (`InventoryService.removeFromSlot`): стартовое на Income не
  снять. Цикл 0.5 с — `watchStudent` под pcall. Учебное существо на сервере CanCollide/CanQuery/CanTouch = false.
  Тестам и DevTools — `Handlers.Prompt(owner, who)`, `Handlers.Reset` (команда `Tutorial <uid> <шаг>` пересобирает).
  `Controllers/TutorialController` — панель задачи, Beam к цели (на экране поимки и после возрождения — заново), чужие
  учебные модели скрыты и не твёрдые, кнопка «Защита» скрыта. Раскладка (`fitPanel`, `placeStats`): панель слева
  сверху; если до капсулы таймера места меньше 460 px (узкий телефон, iPad) — уже и выше (текст не мельче MinText,
  GetTextBoundsAsync + полстроки запаса); если столбик монет и силы (GymHud.Stats, 0.42 высоты) налез бы на панель
  (телефон) — пока идёт обучение, он под панелью. В Studio экран подменяет атрибут игрока DevViewport.
- Поимка D55 на сервере (этап E): `Services/CatchService` — «Поймать» (подсказка `BossLootService`, `OnTakeRequest`) →
  проверки начала, `BossLootService.Reserve` + `SetOpen(false)`, атрибуты корня CatchMode/Since/Face, камера поимки
  `CatchThrow.Frame` (в Active и CatchState); бросок (`CatchAction` "Throw", вид, жест, время отпускания):
  `CatchThrow.Parse` (не бросок — ничего не списано) → `CatchRules.CheckThrow` → `DataService.SpendLovibum` → точка
  `CatchThrow.Aim` (считает сервер) → попадание (`CreatureMotion` в момент прилёта, кольцо `CatchRules.CircleRadius`)
  → шанс; `a.last` — исход и точка (тесты); `CatchEffect` всем в
  `Catch.Game.EffectRadius`, `CatchState` — ловящему; поимка → CatchMode Hidden → `BattleService.Begin(…, { caught =
  true })`; поражение / прерывание боя — `BossLootService.Release` снимает Hidden; конец без поимки — Flee, пауза
  `CatchRules.SetPause`, босс свободен. Учебная — `CatchService.BeginTutorial(player, target)` (onCaught, onEnd).
  Сторож раз в 0.5 с (бездействие, сторож, «кончились», нокаут). Бой Крысиного короля: `RIGS[3]` в BossService и
  BossAnimController, `BossModels[3]` (мешей нет — блоки), `Battle.Bosses[3]` (как у боссов 1–2, сила
  Progression.Bosses[3]). Тесты: `PlayerSession.Join(…, { veteran = true })`, `CatchService.Handlers.SetRoll`.
  DevTools: `Lovibums`, `Tutorial`, `CatchRoll`.
- Живые существа (D55, этап D): поза у босса — `Shared/CreatureMotion` (общее время + зерно uid), сервер пишет на
  корень предмета атрибуты Home (CFrame низа места), Drop (высота места над полом), CatchMode / CatchSince /
  CatchFace / CatchAnchor; `Controllers/CreatureController` двигает корень локально у всех клиентов (у сервера он на
  месте), части — Transform моторов по ролям D54 (`Shared/CreatureAnim`: роль → ось, размах, ритм; пробная поза —
  направление; Yaw — сопряжение поворотом). Экспонат (атрибут Slot) — только суставы / покачивание Visual-сварки,
  корень не трогается; в руках — Held. Существа босса 3: `Config/CreatureRigs` (генерирует
  `scripts/creature_rigs_to_luau.py` из индекса D54, rig.json и `Boss3Creatures.parts.json`; он же вписывает 30
  строк `creature(...)` в `Config/Items` между метками), Part-версия — `scripts/blender/creature_parts.py`
  (вокселизация части, метка цвета ближайшей грани, жадное слияние; ≤ 40 блоков; скрываемая подставка не
  строится). `Util/ItemFactory.buildCreature`: первый блок части — сустав (Motor6D с именем части от блока предка),
  остальные блоки — Weld; лицо скелета D54 (+Z) повёрнуто вперёд (−Z). Lune `check_creatures`.
  Существа «особого внимания» (D54): генератор задаёт им свои роли (`SPECIAL_ROLES`) и оси вращения (`axis`:
  второе колесо — ось парного с пробной позой, пропеллер трёхголовой крысы — наклон 26°). Роли с `own` берут ось и
  размах роли, не пробную позу; виды движения snap / doze / dangle (три головы крысы), slam (створки сейфа: одна
  фаза у пары, навстречу, ≤ 96°), look (стражи сейфа — к камере: `Transforms(…, view)`, view — направление к
  зрителю в осях модели, считает `CreatureController`), follow (корона императора — фаза головы ×2 с отставанием).
  Тележки поезда-монстра — `bogie` (качание на оси, не вращение: в части рама с колёсами).
  Меши D54 вместо Part-версии (подготовлено 2026-11-10, импорта ещё нет): `ItemModels.Creatures[id][часть]` (блок
  `CREATURE_MESHES`, ключ `<id>_<Часть>`, пишет `scripts/bind_meshes.py`), `CreatureTurn` 180, `ForceCreatureParts`.
  `ItemFactory.Preload` грузит меш каждой части (коробка столкновений, Looks/<id>), `buildCreature` ставит видимую
  часть мешем (центр габарита `spec.center`, размер `spec.size` из CreatureRigs, поворот CreatureTurn) или блоками,
  если меша нет; сустав любой части — Motor6D с тем же C0 (точка вращения), C1 = смещение детали⁻¹. Только Studio:
  `ItemFactory.SetCreatureMeshes(id, parts?)`, `CreatureMeshCount(id)`; предпросмотр — `Tests/CreatureMeshPreview`
  (EditableMesh из `Tests/MeshFixture`, не в репозитории). Готовность моделей — `scripts/blender/check_creature_import.py`.
  Порядок импорта — docs/BOSS3_CREATURES.md.
- Существа босса 4 «Сфинкс-лежебока» (D57 — каталог и доходы, D58 — веса и подставки, D59 — площадка): модели
  `scripts/blender/art_oasis.py` → `assets/models/art/boss4/<id>.{fbx,rig.json}`, карты `assets/textures/art/boss4/`
  (№20 — файлы `FennecRiddler_v2.*`, id в игре `FennecRiddler`; объекты FBX `Art_FennecRiddler_<Часть>`). Индекс —
  `scripts/build_boss4_index.py` → `Boss4Creatures.index.json` (роли словами D54, точные оси лопастей грифа), Part-версия —
  `creature_parts.py --boss 4` → `Boss4Creatures.parts.json`, готовность к импорту — `check_boss4_import.py`.
  `scripts/creature_rigs_to_luau.py` пишет обе коллекции: `Config/CreatureRigs` (у босса 4 Order «родитель раньше детей»;
  у босса 3 ноги стоят раньше туловища и крепятся к корню — так утверждено, не менялось) и строки `creature4(...)` в
  `Config/Items` между метками D57 (зона 4; вес — из каталога, не пересчитывается). Подставка прячется у всех 30;
  детали композиции — свои части: №20 `Dot`, №21 `Haze`. Карты загружены (`Boss4_maps.json` → `bind_maps.py` →
  `make_looks.py`), меши частей — после импорта FBX (`bind_meshes.py`). Черновик «Египта» зоны 4 — `legacy`.
  После ручного импорта двух FBX: `scripts/studio/collect_boss4_meshes.luau` (Studio Edit, MCP execute_luau — блок
  BOSS4_IMPORT: имя|MeshId|размер|метки) → файл → `scripts/boss4_bind_after_import.py <файл>` (имена против
  CreatureRigs/Boss4SphinxRig, MeshId, размеры, карты; затем `bind_meshes.py`, сверка, check_project, Lune;
  `--dry-run`, `--synthetic`) → `assets/models/Boss4_meshids.json`. Скелеты и клипы — в коде, из FBX не нужны.
  Импорт 2026-11-13 сделан через Open Cloud (MCP `open_cloud_invoke`, `POST /assets/v1/assets`, тип Model, FBX из
  `assets/models`) → `insert_asset` в `ServerStorage.Boss4Import` (Edit) → сборщик → привязка: меши 30 существ (218)
  и Сфинкса (27) в `ItemModels`/`BossModels`; ориентация такая же, как у File → Import 3D (поворот 180°,
  `CreatureTurn`/`turn`), — сверено по вершинам.
  Зона 4 «Храм спящего Сфинкса» (D60, по `assets/concepts/boss4/zone4_temple/reference.png`): `World/Models/DesertOasis`
  — арена «Ложе Сфинкса» (высоты D59, мощение и синяя мозаика), борт из пяти ярусов r 32–41.5 сегментами по
  внутренней хорде (у 0°/90°/270° — проходы, у 180° — парадная лестница), жаровни, стелы, дороги и мощёные пути с
  меандром `DesertOasis.Lane` (|x| 48–66) и обход храма `DesertOasis.Bypass` (|x| 41.5–48, z ≥ 24) — свободны, `check_world`; `World/Models/DesertTemple` — колоннада у выхода
  (z 34.5–47.4, верх 39) с крыльями-водопадами и набор (Stele, Brazier, Pyramid, Palm, Ruin, Vase, Crate, Bush, Rock,
  CliffRock, Waterfall, Path, Road; у фасада — утопленный проём, карниз, анты); `World/Models/DesertCanyon` —
  ландшафт: слой песка `Sand` (LegoSquaresSoft), `Dune`, скала у стены `Cliff` (твёрдый низ ≤ `SolidTop` 21, верхние
  ярусы и шпиль без столкновений, повороты ≥ 3° — иначе FaceCheck считает их ровными), `Seam` между соседними скалами,
  `Flowers`, `Oasis` (два бассейна, кромка и ступени, водопад из расщелины). Стены коридора (`WorldBuilder.buildCliffs`)
  не меняются — их закрывают скалы. 1107 деталей, без света; неон — огонь, анхи, блики. `MapLayout.Arenas[4]` со
  своими местами `slots` (их берёт `MapLayout.ArtSlotPoints`). Босс 4 открыт (в `Config/Battle` нет `Closed`), Ловибумы
  уровня 4 — в `Config/Catch.Prices`. Проверки: Lune `check_creatures` (оба индекса), `check_config` (12/9/6/3,
  средние = ByBoss[4]), `check_world` (зона 4), `check_catch`; серверные тесты «Босс 4: …».
  Интеграция 30 существ (D55, 2026-11-10): `CreatureController.track` собирает суставы и сварку меша и сразу, и по
  `DescendantAdded` корня (модель приходит на клиент по частям; связь снимается, когда корень пропал);
  `CreatureAnim` у spin берёт угол `% TAU` до CFrame (t — время сервера ~1.8·10⁹ с, CFrame — float32).
  `BossLootService.Handlers.FillWith(boss, slot, itemId)` и DevTools `BossSlot <босс> <1–4> <предмет>` — положить
  нужное существо в слот (только Studio). Проверки: серверный тест «каждое из 30 существ — у короля…» (слот → Home,
  «Поймать», ≥ 2 суставов → победа в руки → постамент → доход каталога → в инвентарь), Lune `check_creatures` —
  раздел «все 30: живые и ловятся» (суставы движутся в Wander / Calm / Held, spin крутится, бросок в центр попадает
  3/3, верх к камере ≤ 30°).
  Обводка (визуальный QA босса 3): у ближайших `UITokens.CreatureOutline.Max` существ у боссов — Highlight только
  контуром. Highlight на детали обводит только её саму, а блоки — дети невидимого корня: на время обводки
  `CreatureController.setOutline` перекладывает блоки корня в локальную модель «Outline» внутри корня (её и обводит),
  при снятии — обратно (копия экспоната `PresentationController` и `ItemFactory.SetVisualTransparency` на сервере
  видят прежнее устройство). У меша — Highlight на «Visual».
- Ловибумы в игре (D55, этап A): геометрия v5 — `scripts/blender/lovibum_shapes.py` (общая с концептами; части
  `a.group`: Base, Core, Claw1…4, Crystal; `a.rig`, `a.axes` — ось раскрытия когтя, `a.lift`, `a.light`).
  `scripts/blender/lovibum_models.py` → `assets/models/lovibums/Lovibum_<Вид>.fbx` (меши Lovibum<Вид><Часть>,
  начало — точка вращения), `<Вид>.rig.json`, карты D39 512² `assets/textures/lovibums/`, `parts.json` — Part-версия:
  те же вызовы деталей пишет `PartArt` примитивами Roblox (брусок → Block; восьмигранник → Block + 2 Block + 4 Wedge,
  светящийся — Cylinder; пирамида → 4 CornerWedge, вершина CornerWedge — угол (+X, +Y, −Z), проверено лучами в
  Studio; многоугольник → Wedge по прямоугольным треугольникам; Wedge — прямой угол у (−Y, +Z)). Проверки: ≤ 2 000
  треуг., совпадающих граней 0 у меша и у Part-версии (точное перекрытие многоугольников, скрытые внутри деталей
  грани не считаются). `scripts/lovibum_rig_to_luau.py` → `src/shared/Config/LovibumRigs.luau` (сгенерирован, StyLua
  не запускать). Лист `scripts/d55_lovibum_sheets.py --models` → `assets/concepts/d55/lovibums_models/models.jpg`.
  Кристалл и ядро — Neon; меши не импортированы (импорт и загрузка запрещены владельцем) — в игре Part-версия.
- Концепты Ловибумов (D55, этап 0; не в игре; v5 «кристалл в когтях»; листы прежних версий — `assets/concepts/d55/`
  `lovibums/` (v1 с лицами, отклонён), `lovibums_v2/`, `lovibums_v3/` (капсулы, v3 — «батарейки», не утверждён),
  `lovibums_v4/` (направление верное, нужен проход силуэтов), их код — в истории git) —
  `scripts/blender/lovibum_concepts.py` на `art_style.Art` без запекания: `lovibum(name, opened)` → по виду `boom`,
  `turbo`, `mega` (`BUILD`); общие `claws`/`claw` (коготь-пластина в вертикальной плоскости: сегменты `bar_side`
  сужаются, чередуют толщину — без совпадающих граней; заклёпка-колпачок `cap`, одна широкая полоса `strip`, крючок;
  `opened` — поворот наружу вокруг основания на `OPEN_DEG`), `crystal` (бипирамида, поворот `turn`; у Меги два —
  «огранка»), детали по виду (защёлки, стабилизаторы `extrude`, зубцы-короны с камнями); кадры телефона 844 × 390
  (`phone_hand_*`, `phone_throw_*`, `phone_net_*`; лист `phone.jpg`
  1 : 1 без увеличения), светящиеся ключи
  (`GLOW`: сила эмиссии после `build`), свет ядра — точечный источник-ребёнок Ловибума; эффекты захвата — отдельные
  `Art` (`net_dome`, `net_cube`, `sparks`, `trail`); существо для кадров — FBX босса 3 с картой цвета (части FBX —
  верхние объекты, двигать каждую); манекены — родитель-пустышка, `view_layer.update()` перед `bounds`. Свечение:
  каждый главный кадр рендерится второй раз без света и неба (`<кадр>_glow.png`), листы `scripts/d55_lovibum_sheets.py`
  (Pillow) размывают его и добавляют экраном → `assets/concepts/d55/lovibums_v5/`. Проверка граней у повёрнутых
  деталей может давать ложные совпадения (сравнивает габариты).
- Прежняя коллекция босса 3 «Подземка» (D54, до замены каталога; модели сохранены, в игру не идут) — `scripts/blender/art_subway.py` (группы COMMON / RARE / EPIC): FBX
  на предмет `assets/models/art/<id>.fbx`, карты `<id>_{color,normal}.png`; режимы `check`, `quick` (без запекания),
  список id — только эти предметы. Свои помощники: `pixel_boxes` (пиксельный знак прямоугольниками без общих граней,
  в том числе на наклонной грани), `cushion` (бархатная подушка с кистями), `gem`, `sparkle` (блик из трёх брусков —
  «плюс» с любой стороны). Невыпуклое тело (головка сыра «пакманом», кольцо корки) — одной деталью `a.extrude`:
  из двух выпуклых половин проверка граней находит совпадения (она сравнивает габариты). Сыр без квадратов D39 —
  его рисунок дырки. Коллекционная вагонетка — красная с золотом (серые вагонетки — декор станции,
  `SubwayParts.MineCart`). Листы рендеров и кадр с манекеном — `assets/concepts/d54/items/` (партии — в подпапках,
  `batch1_common/` …). Ещё помощники: `text_rows` + `FONT6` — слово пиксельными буквами (бирка «НАЙДЕНО»),
  `a.transform` — поворот группы деталей (фонарь к главному ракурсу, кусок пиццы). Проверка граней сравнивает габариты:
  пиксельный знак, повёрнутый вокруг оси в своей плоскости или наклонённый, даёт ложные «совпадения» соседних
  пикселей — такие знаки ставить ровно (наклон вокруг оси X допустим, только если в знаке нет пикселей одного
  столбца, близких по высоте).
- Пачки моделей мира (шаг 3, D33): библиотека `scripts/blender/lego.py` (блоки с фаской 1–2 сегмента, цилиндры,
  купола, скаты, призмы, вазы, «пиксельные» диски и шары; координаты как в Roblox; bmesh; `rot()` — поворот в
  градусах вокруг осей Roblox) + скрипт пачки `scripts/blender/packN_*.py` → `assets/models/PackN.fbx` (без
  материалов и текстур) и `PackN.layout.json`. Деталь = «роль» = цвет, объект `<Модель>_<Роль>`; в layout для
  каждой: центр и размер в координатах модели (центр габаритов = точка опоры MeshPart), color (hex или Accent /
  AccentDark / DecorAccent — цвет участка), material (Plastic / Glass / Neon), decor (только чётные уровни),
  triangles. В игре MeshPart: Color, Material, без TextureID — квадратные пупырышки даёт MaterialVariant LegoSquares (D36).
  Музей: фасад z = −12, портик с колоннами z ≈ −19.4, вход 12×10, вывеска y = 11.5; высоты стен и ламп — в layout.
  Гантели (D34, `pack1_dumbbells.py`, диски — `Model.voxel_plate`): центр рукояти в начале, ось x; у светящихся в
  layout `lights` (PointLight без теней). Превью — Blender с текстурой пупырышков и ореолом неона.
- Концепты D48 v2 (не в игре): `scripts/blender/d48_kit.py` — Blender-детали ровно тех форм, что в Roblox (Block, Cylinder с осью X, Ball, Wedge скосом к −Z), координаты участка, повороты как у CFrame; выгрузка `assets/concepts/d48/v2/bricks/*.json` (shape, size, cframe, color, material, variant, group) — для сборки кодом через ModelBuilder без мешей (план — `docs/D48_INTEGRATION.md`).
- Финальные модули D48-C (не в игре, ждут фазы 3 и разрешения загрузок): `scripts/blender/d48_final.py` → `assets/models/Pack3_d48.*` (музей) и `d48_final_devices.py` → `Pack4_d48_defense.*` (защита), формат пачки как выше; где какой модуль на уровнях 1–10 — `assets/concepts/d48/c2/mesh_placement.json`, состояния устройств — `c2/defense_rigs.json` (начало подвижной части = точка вращения). Проверка — `scripts/blender/d48_check_fbx.py`. План внедрения — `docs/D48_INTEGRATION.md` §10.
- После импорта: модели → `ServerStorage.ImportedModels` (Rojo его не трогает), ID мешей →
  `assets/models/PackN.meshids.json`, затем `python scripts/models_to_luau.py` пишет `World/MeshModels.luau`.
  `World/MeshBuilder` грузит меши при старте (`CreateMeshPartAsync`) и собирает модель: деталь в центр из layout
  и поворот на π (импорт повернул меши), без столкновений и запросов; Glass — прозрачность из GameConfig.Models.
- `assets/textures` — LEGO-текстуры дизайнера (загружены в Roblox, ID в `Config/Textures`).
  `scripts/install-textures.ps1` копирует их в content установленной Studio (запасной путь `rbxasset://`).

## Данные
- Профиль — ProfileStore (`Server/Vendor`), шаблон `Config/ProfileTemplate` (schema 5; миграции в
  `DataService.LoadAsync` по порядку: v1 → v2 — strength, dumbbellLevel; v2 → v3 — единый инвентарь D46; v3 → v4 —
  Ловибумы и обучение D55 (`TutorialRules.Migrate` — по своей схеме `TutorialRules.Schema = 4`, не по номеру
  шаблона); v4 → v5 — защита по уровням музея D56).
- Защита в профиле (D56, schema 5): `defense.owned[вид] = { ["L<уровень музея при покупке>"] = количество }`,
  `defense.installed[вид] = { cycle, level }`, `defense.hacks["L<уровень цели>"]`. Прежний формат (вид → число, вид →
  круг) переводит `Shared/DefenseRules.Normalize(defense, museumLevel)` — при каждой загрузке и в
  `DataService.Defense`: устройствам назначается сохранённый уровень музея игрока, количества и неизвестные виды не
  теряются. Менять запас — только `DefenseRules.Add / Take`, читать — `Stock` (свой уровень), `OtherStock`, `StockAt`,
  `Stale` (прежние уровни списком `{ level, count }` для окна).
- Улучшение музея (D56): `Services/MuseumUpgradeService` — RemoteEvent MuseumUpgrade (клиент шлёт только номер
  следующего уровня) → ответ MuseumUpgradeResult `{ ok, code?, message?, level, slots, coins }`. Проверки по порядку:
  профиль и свой участок, обучение, последний уровень, «ровно следующий» (повторы и подделки — тихий отказ `Stale`),
  запрет по фазе (`Shared/GameTime.UpgradeLock`: подготовка, Судная ночь, 10 с после — причина и время открытия),
  монеты (`Shared/MuseumRules.Check`). Запись — `DataService.UpgradeMuseum(player, fromLevel)`: уровень в профиле
  обязан быть ровно `fromLevel`, цена — `MuseumRules.Price` из `Progression.Museum.Prices`, монеты и уровень меняются
  в одном кадре. Потом `MuseumUpgradeService.Refresh`: `PlotService.ShowLevel`, атрибуты игрока Coins, MuseumSlots и
  MuseumLevel (ставит `InventoryService.Sync`), `DefenseService.Sync`; сохранение. Предметы и доход не трогаются:
  20 постаментов стоят с начала, открываются места. Уровень музея при загрузке — `MuseumRules.Level` (1…10).
- Кража (D46, D37): `Services/TheftService` — подсказка «Украсть» на каждом постаменте (удержание
  `GameConfig.Theft.HoldSeconds`; клиент показывает её чужим в Судную ночь), начало удержания резервирует экспонат,
  музей и вора (`Util/TheftLedger` — чистые правила: фаза, свой/чужой, Displayed, руки, лимиты события по профилю
  `stats.theftEvent` / `stats.lossEvent`, проверка времени удержания), отпускание или уход отменяет, завершение — Stolen
  у вора (`CarryService` несёт так же; бросок, смерть, выход, ночной вынос — возврат через `SetStolenHandler`).
  Сдача — в свой сундук (`InventoryService` зовёт TheftService): журнал DESIGN §6 (`Util/TransferJournal`,
  DataStore «Transfers» при `ProfileStore.DataStoreState == "Access"`, иначе память). Решение «чей предмет» — по меткам
  передачи, которые пишутся в одном кадре с переносом записи: у жертвы `data.transfersOut[id]`, у вора
  `data.transfersIn[id]` (не по наличию uid — uid мог потом законно уйти). Запись журнала удаляется только после
  сохранения, в котором есть результат (`DataService.SaveAndWait` с проверкой содержимого `last_saved_data`); при входе
  вора `ResolveTransfers` → grant / keep / drop / done / wait, подтверждение — `ConfirmResolved`. Запись вора с `pending`
  до подтверждения (выставить нельзя, в реестр при загрузке не ставится, в окне «Передаётся…»). Провал — экспонат на свой постамент; время
  проверяет цикл раз в `CheckSeconds`; ушедший владелец — кража отменена, экспонат у него (`OnPlayerLeaving`).
  Реестр: Displayed → Lifting → Stolen → Stored(вор) или обратно Displayed; владелец и постамент за экспонатом
  сохраняются, пока его крадут.
- Защита музея и взлом (D37, D46): `Services/DefenseService` — RemoteEvent DefenseAction (BuyDefense — только в
  подготовку, цена — `Shared/DefenseRules.Price`: доля цены взлома уровня своего музея, капкан без цены не продаётся;
  BuyHack — днём, по уровню музея-цели; Install / Remove — в подготовку: свободно по `CheckFreeSpot` для ловушки, робота,
  капкана, дверь — «Entrance», лазер — места `GameConfig.Defense.Lasers`), событие DefenseChanged; купленное — в профиле
  `data.defense` (owned, hacks L1…L10), установленное — нет. D56: купленное устройство привязано к уровню музея на
  момент покупки и ставится только на музей этого уровня (`CanInstall` получает запас своего уровня и «чужих»
  уровней — причина отказа «куплено для музея другого уровня»); снятое и не отработавшее возвращается в запас
  своего уровня покупки; DefenseChanged несёт `owned` (вид → n для нынешнего уровня) и `stale` (прежние уровни),
  окно «Защита» показывает их строкой «Прежние уровни музея». Модели — `World/Models/Defense` (ModelBuilder) в папке
  Defense участка. Такт `Defense.Tick` в Судную ночь: дверь выставляет чужих из зала, ловушка (урон и вариант
  эффекта), капкан (10 с, одноразовый), лазер (урон и тревога владельцу), робот (бьёт воров в радиусе, его ломают
  ударами — `PvpService.AddTargetProvider`). Лазер, ловушка и капкан смотрят путь вора за такт (`museum.last` →
  `DefenseRules.CrossedLaser` / `PathDistance`): бегущий вор не проскакивает их между проверками; скачок дальше
  `Defense.TrackStep` и выброс дверью — перенос, путь не считается. Взлом — подсказка «Взломать» на двери (удержание 5 с, устройство уровня ≥
  уровня музея, расходуется, дверь открыта до конца ночи; начало взлома засчитывается только у чужой закрытой двери в
  Судную ночь рядом с ней). Устройство списывается при установке, в `data.defense.installed` пишется номер круга его
  ночи: снял в подготовку или вышел (упал сервер) до ночи — возвращается (`DefenseRules.Settle`, `OnPlayerLoaded`);
  ночь началась — отработало. Закрытая дверь: красть можно только изнутри зала (`TheftService.SetAccessCheck`).
  Клиент `DefenseController`: окно «Защита» (вкладки «Защита» / «Взлом»), расстановка по образцу (зелёный/красный,
  те же правила; над панелью образец замирает, на телефоне идёт за касанием, начатым по миру), атрибут игрока
  PlacingDefense; участок отдаёт оси атрибутом `FloorOrigin`. Числа — `UITokens.Defense`.
  D48-C: зоны расстановки — `GameConfig.Defense.Hall` Allowed / Forbidden / GalleryForbidden (из `Config/MuseumLayout`,
  боковые проходы вдоль павильона и за ним), лазеры «Вход» и «Галерея» поперёк дорожки; «в музее» — зал и (с уровня
  `Defense.Galleries.Level`) галереи; робот бьёт, только если видит вора (луч до него не задевает Building и
  Showcases участка). Модели устройств — Part-версия в палитре D48, детали Glow — цвет состояния (`Defense.States`).
- Табличка места (D50): `World/Plaque` — плашка на лицевой грани постамента (`Plaque.Parts` — размеры и смещения,
  их же считает `check_museum_layout`) и у свободного места голограмма-куб (теги Spin и Bob, анимирует
  `ZoneController`). Пишет `PartBuilder.refreshPlace` при смене Open / Occupied и при появлении или уходе экспоната
  в папке Exhibits (замена на том же месте). Название экспоната — на табличке, плавающую подпись `Label` снимает
  `MuseumService.PlaceExhibit`; «+X/сек» над экспонатом — `IncomeService.Label` (D37), видна до 30 ст.
- Камера в музее (D50): `Controllers/MuseumCameraController` — пока персонаж в музее (оси участка из атрибута
  `FloorOrigin`, галереи — с `MuseumLevel` ≥ `Gallery.Level`), отрезок от фокуса камеры до места на выбранном игроком
  расстоянии (`PlayerModule:GetCameras().activeCameraController:GetCameraToSubjectDistance()`) и 4 соседних луча
  проверяются против коробок деталей `Building` этого участка своими силами (у декора без столкновений CanQuery
  выключен). Найденные детали — `LocalTransparencyModifier` 0.75 сразу (до камеры Roblox, `BindToRenderStep`
  Camera − 2), остальные плавно возвращаются; выход, новый персонаж — сразу; пол и ступени ниже ног не гаснут никогда. Чужую локальную прозрачность (створки
  решётки у владельца) не трогает. Числа — `UITokens.MuseumCamera`.
  С ношей (босс 3): ещё отрезки от камеры к центру и верху ноши и 5 вертикальных сквозь неё (ноша — деталь на
  WeldConstraint с корнем, ItemId = `CarryingItemId`); в галерее (|x участка| > `Hall.HalfWidth`) камера не дальше
  `CarryGalleryZoom` 9 (CameraMaxZoomDistance), на выходе — прежний предел и расстояние. `MuseumCameraController.Blocked(a, b)`
  — закрыт ли отрезок деталью здания (для подписей экспонатов; постаменты не считаются).
  D55 (2026-11-10, «стены и постаменты не перекрывают игрока и экспонаты»): в коробках ещё постаменты (`Showcases`:
  тумба, Top, Plaque — гаснут целиком); отрезки — толстый «фокус → камера» (Probe), «камера → корпус», к ≤ ExhibitMax
  экспонатам той же части музея (зал / галерея, ≤ ExhibitRadius, в кадре; свой постамент не гаснет); гаснут и
  экспонаты между камерой и персонажем, детали ближе NearCamera к камере, передний план чужой части (OtherRoomRadius,
  когда камера в зале, а персонаж в галерее, и наоборот); SurfaceGui погашенной детали выключаются. После камеры
  Roblox (`Camera + 1`, `clampStep`) камеру внутри места (тумба + экспонат) подтягивает к персонажу до края места,
  отпускает плавно (ColumnRelease). Отсев: общий габарит отрезков → габарит каждого → сфера → плиты. Стоимость (ПК,
  музей 20 существ): 0.16–0.20 мс/кадр (старый — 0.34–0.41). Проверка — `scripts/studio/museum_camera_probe.luau`.
- **HUD v3 (ТЗ владельца 2026-11-17, по референсу; заменяет раскладку HUD v2 ниже — DESIGN.md ещё не обновлён, ждёт
  согласования):** одна схема на телефоне и ПК.
  - Слева посередине — столбик кнопок `UI/MenuHud`: `UI.Button` стиля «Chunky» 168 × 48 со своей иконкой слева,
    подпись одного размера; цвет и порядок — `UITokens.MenuHud.Themes/Order` по имени кнопки («Магазин» зелёная,
    «Инвентарь» синяя + клавиша B, «Музей» жёлтая, «Защита» красная, «Тест» — только владельцу). API `MenuHud.Add`
    прежний.
  - Слева внизу — сила и монеты (`GymController.buildHud`), дохода нет: он в списке игроков Roblox —
    `IncomeService.publishIncome` ведёт `leaderstats/«Доход/сек»` (IntValue) вместе с атрибутом `Income`.
  - Справа внизу — таймер (`TimeController`): иконка фазы, «День 0:57» (RichText: фаза цветом, отсчёт белым), подпись
    про Судную ночь; без рамки. На касании с маленьким экраном — левее кнопки прыжка, на планшете — в углу под ней.
  - Низ по центру — `CarryController`: строка «Несёте: … · редкость · [Бросить]»; на узком телефоне, где строка не
    помещается (`CarryHud.MinFull`), — только кнопка с названием над ней.
  - Сверху по центру под кнопками Roblox — короткая плашка зоны (`ZoneController`, 250 × 46, ~1 с) и под её местом
    уведомления (`NotifyController`; колонка невысокая: на телефоне одно). «Удар» (`PvpController`) — у правого края
    над кнопкой прыжка. Панель обучения слева сверху сообщает свой низ (`HudLayout.SetLeftTop`) — меню встаёт ниже.
  - `UI/HudLayout` — экран (подмена `DevViewport`/`DevTouch` в Studio), масштабы, зоны, `Track`; занятое у нижнего
    края сообщают статы и таймер (`SetBottom` → `BottomBand`). Расчёты — чистый `Shared/HudMath` (Scale — кнопки, на
    касании ≥ 0.85; InfoScale — надписи, на касании ≥ 0.72; Jump — зона прыжка Roblox; Menu; Fit), их же гоняет Lune
    `check_hud` на 13 экранах (568 × 320 … 2560 × 1440).
  - Иконки HUD — свои (стиль D39): `scripts/blender/d48_icons.py` (рендер, аргумент — список имён) →
    `scripts/hud_icons.py` (контур, 256 px) → `assets/ui/hud/`, ID — `assets/ui/hud/IDS.md`, `UITokens.HudIcons`.
    Те же иконки — в шапках окон (магазин, инвентарь, музей, защита).
  - Проверка на экране: `scripts/studio/hud_probe.luau` (прямоугольники HUD и зон Roblox, пересечения).
  - Кнопка владельца «Тест»: `Controllers/OwnerTestController` — по атрибуту игрока `OwnerTest` ("Normal" | "Test",
    ставит `OwnerTestService` только владельцу в DEV-месте), панель действий правее меню, RemoteEvent `OwnerTest`
    (имя действия); сервер: `OwnerTestService.run` — владелец, вид сервера, пауза; действия те же, что у команд
    чата, плюс `Goto` («К дракону» без боя, `GameConfig.OwnerTest.ViewAt`).
- HUD v2 (D48 v2): иконки — `client/UI/HudIcons` по `UITokens.HudIcons` (путь CheckUIIcons или rbxassetid); колонка
  меню `UI/MenuHud` справа (иконка + подпись, значок клавиши B у «Инвентаря» — саму клавишу привязывает
  `InventoryController` через ContextActionService, колонка её не слушает), статистика слева (`GymController`), таймер —
  капсула сверху (`TimeController`, CoreUISafeInsets). Соседи отсчитываются от реального масштаба экрана
  (`client/UI/HudLayout`: низ таймера, левый край колонки меню): плашка входа в зону и уведомления — под таймером,
  уведомления — левее колонки и не ниже верха «Бросить», если на узком телефоне заходят на неё по ширине; «Удар» —
  только телефон (касание без клавиатуры) и Судная ночь, сразу под кнопками Roblox левее колонки (D50; масштаб не
  ниже `Pvp.MinTouch / Button.Y` — кнопка ≥ 52 px). Уведомления (D50, `NotifyController`): DisplayOrder 14 — поверх
  окон; пока видна плашка зоны и колонка заходит под неё — спрятаны; пока открыто окно меню (видна `Fenetre`, проверка
  4 раза в секунду) — в полосе справа от окна, а если она уже `minWidth` (телефон) — ждут закрытия окна (срок жизни
  уведомления идёт только пока колонка видна). Окно Stud-UI (`StudMotion.Window`) отдаёт `menu.Destroy()` —
  отключить подписки при пересборке окна (инвентарь пересобирается при смене экрана; размер — по безопасной зоне). Подпись
  таймера — на тёмной капсуле: «до Судной ночи: N дней», «Судная ночь — завтра / сегодня». Фиксированные
  отступы ПК на телефоне (масштаб ~0.6) не годятся; проверка — `scripts/studio/hud_phone_sim.luau` (моделирование,
  `BANNER` — с плашкой зоны). Ниже — описание до D48 (колонка была слева).
- Колонка кнопок меню в HUD (`client/UI/MenuHud`): «Инвентарь», «Защита» — слева над столбиком надписей силы и монет,
  одна WindowScale (`UITokens.MenuHud`). StudMotion: список спрятанных GUI и базовое FOV общие для всех окон
  (переключение окон не теряет HUD и не растит FOV). Поиск — `Shared/TextCase.Lower` (кириллица, ё → е).
- PvP (D46, D37): `Services/PvpService` — RemoteEvent PvpAttack без аргументов, цель и урон решает сервер
  (`Util/PvpRules`: фаза — только Судная ночь, Safe Zone у места появления `GameConfig.Pvp.SpawnSafeRadius`,
  оглушение, перезарядка `Battle.Player.AttackInterval`, ближайший соперник впереди в `Range`, урон и HP — формула
  `Battle.Player` от силы). HP 0 — нокаут: отброс (как у босса), скорость и прыжок 0, звёзды (BillboardGui, тег
  KnockStars), атрибут Knocked, 15 с неуязвим, потом полный HP; вор с добычей — `TheftService.OnDefeated`.
  Клиент `PvpController`: ЛКМ и кнопка «Удар» (Stud-UI, только телефон и Судная ночь), эффекты PvpEffect (замах плечом
  через `Util/Joints`, ключ Swing; вспышка Highlight, «-N», «НОКАУТ!», тряска камеры), свой нокаут — PlatformStand;
  числа — `UITokens.Pvp`.
- Пространство музея (D52): `Shared/MuseumSpace` (сервер и клиент: подсказка «Украсть» только внутри музея) — Inside (зал или открытая галерея в осях участка; ею же пользуется DefenseService) и Sees (луч через Building и Showcases участка, детали без столкновений лучу не мешают). `TheftService.reachable` — рядом, внутри и видит экспонат; `TheftLedger` — пауза RetrySeconds после провала по вине вора (Fail с now).
- Сохранения (D52): `DataService.saveIfAllowed` — единственный путь записи профиля из наших вызовов (SaveAndWait и таймер RequestSave): только активный профиль этого игрока и не чаще `GameConfig.Data.MinSaveInterval`; отказ таймера — перенос на позже. Загрузка — `finishLoad` (конец сессии ловится сразу, неактивный профиль не отдаётся, игрок кикнут; Join без данных — тоже кик), `DataService.Handlers` (FinishLoad, Profile) — для тестов; `PlayerSession.Leave` — шаги в pcall, Release всегда; `TheftService.OnPlayerLeaving` — каждый экспонат ушедшего хозяина в pcall с запасной очисткой; `TheftService.confirm` — у ушедшей жертвы читает сохранение повторно (`Theft.ReadRetrySeconds`, до SaveTimeout), дальше — журнал; `TransferJournal.Prune` чистит только transfersIn.
- Ждущие передачи и время доставки (D53): при загрузке вора `DataService.ResolveTransfers` возвращает и id передач с решением «ждать»; `TheftService.WatchTransfers` (из `PlayerSession.Join`) раз в `Theft.ResolveRetrySeconds` до `Theft.ResolveWindow` вызывает `DataService.ResolveWaiting` (все чтения — до решений; решение только однозначное: метка жертвы → выдать/оставить, нет живой сессии и метки → убрать; живая сессия — ждать) и ставит выданное в реестр (Stored), подтверждение — `ConfirmResolved`. Время доставки: `TheftService` (carries: место, время, скорость, `MoveGuard.TransferDistance` при снятии) → `Util/DeliveryRules.MinSeconds` при сдаче → лог и атрибут `SuspiciousDeliveries`, без блокировки.
- Невозможные перемещения (D52): `Services/MoveGuard` — Step: «копилка» пути по горизонтали (пополнение скорость Humanoid × Tolerance в секунду, ёмкость Slack + скорость × Burst, смещение тратит, минус — нарушение) и полёт (коробка FootSize вниз мимо персонажей: выше прыжка + HoverSlack дольше HoverSeconds; сбрасывает только пол, падение не нарушение, у TrussPart — лазание, в капкане не проверяется). Mark — отметка (начало кражи, тестовые переносы). Teleport — единственный перенос сервером: путь до него проверяется (если игрока проверяли за Live секунд; нарушение вернёт следующий Step), в новой точке отметка, TransferGrace секунд не засчитывается только точка до переноса; точку капкана не меняет. Вызывают: DefenseService выброс у двери, VaultService, NightService, BattleService.keepInZone, CheckPins. Новый персонаж — новая отметка сам. TransferredWithin — для защиты: путь дальнего скачка (> TrackStep) не проверяется, только если сервер переносил за этот такт. Pin/Unpin (капкан, PvpService), CheckPins раз в Tick. Числа — `GameConfig.MoveGuard`; `Enforce` = false — режим логирования (нарушения в лог и атрибут игрока `MoveViolations`; TheftService не срывает кражу, CheckPins не возвращает). TheftService: при переноске (sweep) и сдаче — Step; при Enforce нарушение → добыча владельцу. Без банов.
- Устройства защиты (D52): путь вора за такт проверяется с высотой — `DefenseRules.ZoneHit` (ловушка, капкан: круг радиуса по полу и высота меньше TrapHeight на отрезке пути), `CrossedLaser(..., top)` (высота на отрезке пересечения луча); высота между тактами — по прямой. `m.last` хранит точку и корень: нокаут, смерть, новый персонаж — без пути.
- Процедурные движения суставов (D18, D51): `client/Util/Joints` — сустав Motor6D или AnimationConstraint (так у R15 в
  Studio 2026-11-07); смещение позы по ключу накладывается на Transform аниматора в PreSimulation (у AnimationConstraint
  смещение точек крепления аниматор гасит), смещения складываются, без накопления. Сгибать — вокруг поперечной оси
  персонажа (`Joints.Axis`), так одинаково у R6 и R15. `Controllers/TrainingController` — подъём гантели у всех игроков с
  атрибутом Training: фаза по `workspace:GetServerTimeNow()`, верх подъёма в момент начисления силы; R15 — плечо, локоть,
  кисть, поясница; R6 — плечо; числа — `UITokens.Training`.
- Единый инвентарь (D46): все предметы игрока — `items[uid]`, place `slot` (Displayed) или `storage` (Stored), без
  ограничения количества. `Shared/Inventory` — чистые функции: `Normalize` (миграция и проверка при каждой загрузке:
  экспонаты на несуществующих или занятых постаментах — в инвентарь, ничего не удаляется, повтор не меняет данные),
  `Summary` (всего, выставлено, доход), `CountOnSlot`. Правило фаз — `Shared/GameTime`: `ExhibitLock(t)` (менять
  экспонаты нельзя в подготовку, Судную ночь и 10 с доставки), `TheftPhase(t)` (Open / Delivery),
  `DeliveryWindowEnd(t)`; `GameConfig.Time.DeliveryGrace` = 10.
  В профиль попадают только экспонаты (`Displayed`) и хранилище (`Stored`).
- Состояния экземпляра предмета — `ItemRegistry` (uid → state), граф в DESIGN.md §1:
  OnMap → Carried → Displayed ⇄ Stored, MoveSlot / SwapSlots на витринах.

## Сервер (`src/server`)
- `Main.server` — RemoteEvent'ы, LEGO-материал, постройка мира, запуск сервисов; вход/выход — `Services/PlayerSession`.
- Services: `DataService` (профиль), `PlotService` (5 участков, музей D48-C), `ItemRegistry` (состояния), `CarryService`
  (подбор/перенос/бросок, `AttachCarried`), `BossLootService` (4 предмета у каждого босса, D37, D10 исчезновение), `MuseumService`
  (выставить, переставить, повернуть, презентация), `InventoryService` (D46: единый инвентарь — сундук «В инвентарь», постамент «В инвентарь», окно: InventoryAction Display / Remove / Replace откуда угодно, правило фаз `MuseumService.ExhibitsUnlocked`, событие InventoryChanged — весь инвентарь; шлётся и по `ItemRegistry.OnChanged` (Stored/Displayed владельца, раз в кадр) — окно видит выставление из рук, перестановку и кражу), `GymService` (D34:
  такт качания — владелец в поле своего двора, сила = Power[уровень] × (1 + сила музея D31); гостю подсказка;
  «Улучшить» — подсказка на табло и запрос GymUpgrade, все проверки на сервере; атрибуты игрока Strength,
  Coins, DumbbellLevel; D51: огромной гантели во дворе нет — тренирующийся (своё поле, пустые руки, жив, не в
  нокауте; проверка каждые `Gym.StateCheck` с и сразу по CarryingItemId / Knocked / Died) получает атрибут Training и
  гантель уровня в правую руку — `World/HandDumbbell` (модель `Dumbbell01…10` из MeshModels, уменьшенная до
  `Gym.HandDumbbell.Length`, MeshPart без массы и столкновений, WeldConstraint к RightHand / Right Arm); сила — на
  границах `Gym.TickSeconds` общего серверного времени). Скорость от силы — `Shared/Speed` + `CarryService.RefreshSpeed`.
- `Services/PlayerSession` — вход (участок → профиль → здание и гантель → музей → хранилище → сообщение) и выход;
  один путь для игры и тестов (`Join(player, { mock = true })` — профиль в памяти, ProfileStore.Mock).
- Тесты (`Server/Tests`, только Studio, в Play): `ServerTests.Run()` через `ServerStorage.DevTools.RunServerTests`
  — 23 сценария (двое тестовых игроков, время и ночь, предметы у боссов) (`TestPlayer`: таблица с полями Player и персонаж-манекен, UserId < 0).
  Действия — теми же обработчиками, что подсказки (`MuseumService/InventoryService/GymService/CarryService.Handlers`).
  События клиенту — `Remotes.FireClient` (тестовому игроку пишет в журнал `Sent`). Это серверная симуляция:
  подсказки, интерфейс и сеть проверяются только на настоящих клиентах.
- Время (D37): `Shared/GameTime` — фаза, день и границы фазы как функция общего времени
  (`workspace:GetServerTimeNow()`, `GameConfig.Time`), круг 3 360 с, одинаково на всех серверах и у клиента.
  `Services/TimeService` — такт 0.25 с, атрибуты ReplicatedStorage (Phase, Day, Cycle, PhaseStartsAt, PhaseEndsAt),
  `OnPhaseChanged`; Studio: `DevTools.TimeScale/TimeSkip/TimeReset` (атрибуты TimeScale, TimeAnchorReal,
  TimeAnchorGame — их читает и клиент). `Services/NightService` — ночью барьер `NightBarrier` в воротах уровня 1
  (только на ночь), потеря несомого (`CarryService.LoseCarried`), вывод из коридора (`MapLayout.InDangerZone`) к
  месту появления и проверка раз в 0.5 с. Клиент: `Controllers/TimeController` — панель Stud-UI внизу справа
  (`UITokens.TimeHud`), фазу считает сам через `GameTime`.
- Босс 1 и бой (D40): `Config/Boss1DogRig` (скелет пса: 16 частей, точки вращения, габариты, 13 ключевых поз —
  генерирует `scripts/blender/boss1_dog.py -- . <превью> rig`), `Config/BossModels` (MeshId частей после импорта и
  карты), `Config/Battle` (тестовые числа боя, длительности состояний). `Services/BossService` — модель из частей на
  Motor6D от невидимого корня с AlignPosition/AlignOrientation (владелец — сервер), атрибуты для анимаций (State,
  StateAt, Moving, AttackSeq/Kind/At, HitSeq/At, HP/MaxHP); пока меша нет — блок цвета части. `Services/BattleService`
  — автобой: «Забрать» у предмета (BossLootService.OnTakeRequest) → Reserve предмета, подсказки босса выключены
  (SetOpen) → Wake → StandUp → ToCombat → Combat (удары по интервалам в цикле 0.1 с, урон в момент удара, промах если
  отошёл) → win (Award: предмет в руки) / lose (отброс LinearVelocity, без телепорта) / night / abort → Victory или
  Defeat → Return → FallAsleep (подсказки открыты) → Sleep. D49: побега нет — босс не уходит дальше Leash от места,
  боец заперт в зоне: стены `World/BattleWalls/ZoneWall_<n>` на границах зон (группа ZoneLock) сталкиваются только с
  группой ZoneFighter (атрибут InBattle → `Util/CharacterGroups`), сервер возвращает вышедшего в зону. Полоска HP
  (BillboardGui) — только над боссом; HP бойца — в Humanoid (MaxHealth = HP боя, Health ≥ 1, после боя прежнее) —
  стандартная полоса Roblox. Клиент: `Shared/BossAnim` (Transform суставов по состоянию и времени — смешение поз, циклы дыхания,
  шагов, выпады и попадания поверх) + `Controllers/BossAnimController` (Stepped, у всех клиентов одинаково, «Z z z»).
  Стыки без скачков (2026-11-10): каждый переход идёт по прежнему пути между ключевыми позами (`bridge`), а живые
  отклонения того, что играло (дыхание, покачивание стойки, шаг, выпад, танец, качание головы), гаснут, того, что
  будет, — нарастают; прямое смешение живой позы с ключевой нельзя: у пса задние ноги в позах сна и ходьбы повёрнуты
  почти на 180°, и `CFrame:Lerp` выбирал то одну, то другую сторону (скачок голени 1.4 ст. за кадр). Шаг в бою и по
  дороге домой включается и гаснет за WALK_BLEND (полшага) от смены Moving — атрибут `MovingAt`; уснув, дыхание и
  подёргивание уха набирают силу за полвдоха; разбудили, пока засыпал, — пробуждение с позы, где застали
  (`FromState`/`FromAt`, BossService.SetState); последний удар игрока в начале поражения не накладывается дважды.
  BattleService.goHome засыпает, когда босс остановился (Moving = false, не дольше `Battle.StopWait`), а не на ходу с
  `ArriveDistance`. Длительности `Battle.Timeline`, темп ходьбы и позы не менялись; проверка —
  `scripts/lune/check_boss_anim.luau` (75: стыки совпадают ≤ 1e-4, по кадрам нет одиночных скачков). Остаётся сетевая
  задержка (~2 кадра): новое состояние приходит с t ≈ 0.03, короткий рывок «бой → поражение» (0.15 с) начинается не с
  нуля — быстрая поза, не скачок.
- Босс 2 (D42, D43): `Config/Boss2TraderRig` (12 частей, 13 поз с теми же именами — `boss2_trader.py -- . <превью>
  rig`), `BossModels[2]` (карты Head/Body/Limbs, `TRADER_MESHES` пусто до импорта). Скелеты по номеру зоны — `RIGS`
  в BossService и BossAnimController (боссов без скелета нет на карте, их предметы без боя только в Studio).
  `BossService.Height` — рост по скелету (полоска HP над макушкой), сообщения боя — с `GameConfig.Zones[i].boss`.
- Босс 4 «Сфинкс-лежебока» (интеграция 2026-11-12, решения D57 ещё нет — владелец запретил править DESIGN.md):
  клипы вместо поз. `scripts/boss4_to_luau.py` из `assets/models/Boss4_Sphinx.{rig,anim,colors}.json` пишет
  `Config/Boss4SphinxRig` (27 частей, 13 поз, `Clips`) и `Config/Boss4SphinxClips/<Клип>` (10 модулей, ≤ 85 тыс.
  знаков; сон и стойка — 15 кадров/с, остальное 30; кватернион + сдвиг только у частей со сдвигом). `BossAnim.Sample`:
  у скелета с `Clips` — `Shared/BossClips` (боссы 1–3 прежним путём). BossClips: Sleep — sleep_idle от StateAt;
  Wake/StandUp/ToCombat — один клип wake по Timeline; Combat — combat_idle, шаг walk по MovingAt, выпад, реакция на
  удар (во время выпада или шага — только голова и платок); Victory/Defeat/FallAsleep — свои клипы; Return — walk
  поверх позы stand; смена состояния — прошлое продолжается и гаснет за 0.25 с (разбудили, пока засыпал, — за
  Timeline.Wake). Раскачка стойки гаснет рядом с выпадами (`Calm`): клипы выпадов начинаются и кончаются позой combat,
  иначе хвост дёргался на стыке. **План атаки** (только боссы с клипами): BattleService пишет `PlanKind/PlanAt/PlanSeq`
  (время сервера будущего выпада + `Battle.AttackPlan.ExpectedDelay` 0.055 — средняя задержка цикла 0.1 с), первый —
  в начале ToCombat (запас 0.66 с на задержку сети), отмена — `PlanCancelAt` (игрок вне дальности, конец боя), у
  выпада — `AttackPlanAt` (пишется ДО AttackSeq). Клиент ведёт замах и выпад от времени плана; выпад без плана —
  сокращённый замах догоняет попадание. Время выпада, урон, HitDelay, интервалы — прежние. `Battle.Bosses[4].Closed` —
  босс строится только в Studio с DevMode (`BossService.ClosedAllowed`), в опубликованной игре зона 4 как раньше.
  Модель: игровая копия `assets/models/Boss4_Sphinx_game.{blend,fbx}` (7 916 треугольников, `boss4_sphinx_optimize.py`
  сняла 57 невидимых граней; утверждённая v2 не меняется), карты загружены (`assets/textures/art/IDS.md`, шаблоны
  `Server/Looks/Boss4_*`), мешей нет — блоки-заготовки цвета `colors.json`. Предпросмотр без загрузки:
  `scripts/blender/boss4_sphinx_fixture.py` → `Tests/MeshFixture/Boss4_*` (.gitignore) → `Tests/BossMeshPreview`
  (Edit, MCP). Проверки — `scripts/lune/check_boss4_player.luau` (50) и серверные тесты «Босс 4».
- Босс 5 «Йети-коллекционер» (шаг 2 D64, этап П — производство в Blender, в игру не подключён): каталог —
  `docs/BOSS5_CATALOG.md`, план файлов — `docs/BOSS5_STEP2.md`. Модель — `scripts/blender/boss5_yeti.py` (модуль и
  скрипт): формы утверждённого концепта `boss5/yeti.py`, 30 частей (Torso → Head/Jaw/EyelidL,R/BrowL,R/Monocle;
  UpperArm → ForeArm → Hand → Fingers; Thigh → Shin → Foot; Block (лёд) → BlockFrame, BlockTop (лёд) →
  BlockTopFrame, 4 экспоната Ex*), карты Head/Body/Limbs 1024², масштаб 2.03 (рост 24 стада). Позы — параметры
  скелета концепта (`frames(P)` → `pose_world` → `transforms` как у Motor6D; ноги — обратная кинематика по целям стоп;
  глыба на спине или в мире, `blend` матриц), у руки пятый параметр — поворот внутрь. Пишет `Boss5_Yeti.{fbx,blend,
  rig.json,colors.json}` (rig: 13 поз, `head_parts`, `ice_parts`, `attack_clips` bite→smash, swipe→ice_clap).
  Клипы — `boss5_yeti_anim.py` → `Boss5_Yeti.anim.json` (10 клипов, формат Сфинкса; проверка провала под землю с
  допуском 0.1 ед. и недотяга ног). Существа — `scripts/blender/creature_kit.py` (цикл art_oasis.py без изменений
  поведения, карта по редкости: Common 512²) + `art_glacier.py` (30 строителей) → `assets/models/art/boss5/`,
  `assets/textures/art/boss5/`; собирать по одному существу на процесс (`scripts/run_glacier.sh`): в одном процессе
  свет студии копится. Листы на просмотр и таблица весов D58 — `scripts/boss5_sheets.py` → `assets/concepts/boss5/sheets/`.
  Набор анатомии (D64) — `scripts/blender/anatomy_kit.py` (`import anatomy_kit as A`): `body` (ярусы-усечённые
  призмы по профилю egg / barrel / drop / pear / ball / dome, фаска D39, кольца яруса подобны — грани плоские, низы
  разных тел на разной высоте — без совпадений), `ball`, `limb` (звенья + шар-сустав), `flipper`, `foot`,
  `folded_wing`, `eye` (по нормали, утоплен ≥ 0.05; `closed` — сон), `snout`, `beak`, `facial_disc`. Мелкие тела
  (< 0.3) без фаски — бюджет треугольников. `GLACIER_OUT` — полная сборка вне assets (листы «до/после»).
  Анатомия (D64): `scripts/blender/joint_check.py` — `check_joints` (щель часть↔родитель > 0.05 стада, летающие куски,
  ось дальше 0.5 стада; тело на подставке может опираться на ноги-детей или ноги-соседей) и `check_bends` (пустота
  вокруг оси — сгиб раскрывается); вызывается из `creature_kit.run` и `boss5_yeti.py` (у Йети — во всех позах,
  экспонаты Ex* вне проверки — вморожены по замыслу). Лист-аудит — `scripts/boss5_anatomy_audit.py` (быстрая сборка
  `bash scripts/run_glacier.sh assets/concepts/boss5/audit/creatures quick` и
  `YETI_SHOTS=none … boss5_yeti.py -- . assets/concepts/boss5/audit/yeti quick` → отчёты).
- Босс 5 «Йети-коллекционер» подключён 2026-11-24 (`docs/BOSS5_INTEGRATION_PLAN.md`), закрыт до выпуска (D64 п. 7):
  `scripts/boss5_to_luau.py` (rig.json + anim.json + colors.json) → `Config/Boss5YetiRig` (31 часть, 13 поз; поза
  `sleep` — первый кадр клипа сна: в rig.json нет опускания корня; `AttackClips` bite → smash, swipe → ice_clap,
  `AttackDefault`; `Eyes` — линза `Lens` (Neon, гаснет по каналу `lens` клипов); `Body` — выпуклый контур корпуса и ног;
  `Transparent` — лёд глыбы 0.45) и `Config/Boss5YetiClips/*` (10 клипов, в `.styluaignore`). `BossService.makePart`:
  часть с `eye` — Neon без карт, `rig.Transparent` — прозрачность меша. `Battle.Bosses[5]`: база 1–4, сила D56,
  `BodyRange` (удар от контура, 3.5 ст.), ходит за игроком (`Leash` 40): погоня останавливает центр дальше на вынос
  контура в сторону игрока (`BattleService`, `outline`). Коллекция: `build_boss5_index.py` (роли ROLES5, OVERRIDE для
  ходуль кита, transparency желе и купола) → `creature_parts.py --boss 5` → `creature_rigs_to_luau.py` (метки D64,
  `creature5`); `ItemFactory` даёт части `transparency` и атрибут `GlassTransparency` (мигание D10 от неё). Меши —
  `Boss5_meshids_flat.json` → `bind_meshes.py` (`Boss5Yeti` → `YETI_MESHES`), карты — `bind_maps.py`, шаблоны —
  `make_looks.py`. Пока босс закрыт, `BossLootService` не выставляет слоты закрытого босса с живой коллекцией вне
  Studio/теста владельца (заготовки зон 6–10 стоят, как раньше).
  Зона 5 «Ледник» — `World/Models/GlacierHall` (610 частей, 3 света): «замёрзшее озеро» r 32 из шести дисков (верх
  центра — `Arenas[5].floor` 0.7, плиты существ — `top` 1.08), снежинка-мозаика, столбики с канатом r 34.4 (проходы
  к входу и к дорожкам выхода), ледник одной стеной (глыбы на LegoSquaresSoft, пики из двух клиньев со смещённой
  вершиной, карниз-козырёк, сосульки, круглая дверь хранилища), 10 витрин (стекло, экспонаты — только предметы), гряды
  у стен (твёрдые ≤ 13, пики без столкновений), трещины, ели, сугробы, сияние (Neon в небе за ледником), указатели
  «В ДЖУНГЛИ». Пути `GlacierHall.Paths` (5 отрезков) свободны — `check_world` (порог 1.1, круг боя r 41).
  Проверки: `scripts/lune/check_boss5_clips.luau` (скелет, клипы = экспорт, подошвы, стыки, линза, контур),
  `check_creatures` и `check_world` с зоной 5, `check_project.py` (раздел босса 5), ServerTests «Босс 5: …» (4 теста).
- Босс 10 «Король-дракон» (этапы A и B, 2026-11-15; DESIGN.md не правился — исключение D52 для залпа ждёт записи):
  тот же путь, что у Сфинкса, — `scripts/blender/dragon10/v7_export.py` (поверх `v7_anim5.py`) →
  `assets/models/Boss10_Dragon.{rig,anim}.json` → `scripts/boss10_to_luau.py` → `Config/Boss10DragonRig` (52 части:
  49 дракона + 3 скипетра, `AttackClips`, `Turn`, `HeadParts`, `Membranes`, `Body` — контур тела, `VolleyOrigin`) и
  `Config/Boss10DragonClips/*` (15 клипов, 1.34 млн знаков; сон и стойка через кадр). До этапа C части — блоки.
  Новое включается только полями `Battle.Bosses[10]` (у 1–9 их нет, путь прежний):
  - `BodyRange` — дальность от контура тела в осях дракона (`BattleService.bodyDistance`, выпуклый многоугольник),
    иначе от центра; `reach = AttackRange + Reach` (D52) для обоих — 2.5 + 1 = 3.5 ст.
  - `Leash = 0` — не бежит, стоит на месте (`MoveTo(home)`), поворачивается к игроку; `TurnRate` (°/с) ограничивает
    `AlignOrientation.MaxAngularVelocity`. Клиент считает скорость поворота корня и ведёт клип «шаг на месте»
    (`Turn.Left/Right`, 90° за цикл) по накопленному углу — `BossAnimController.turnInput` → `BossAnim.Input.turn*`.
  - `AttackSides` — вид выпада по стороне игрока (спереди по кругу, слева хвост, справа укус); урон и интервал прежние.
  - `Volley` — залп (`Shared/BossVolley` — математика, общая с Lune): готов, если игрок вне ближнего боя, дальше
    `MinDistance` от круга и перед мордой (`FacingAngle`); объявляется планом `kind = "volley"` за `Announce`, затем
    `BattleService.startVolley` — цикл на Heartbeat: фиксация на `Lock` (`VolleyDir`), выстрел на `Fire` — Spherecast
    по карте (без босса и персонажей, RespectCanCollide) и земля, полёт — отрезок против капсулы, допуск `Grace`, урон
    `roll(bossDamage) × DamageScale` не больше `MaxHits` за залп. `finish` и пропажа цели — `endVolley` (отмена,
    `VolleyCancelAt`). Атрибуты модели `VolleySeq/At/Origin/LockAt/Dir/FireAt/EndL|C|R/CancelAt` → клиент
    `Controllers/BossVolleyController` (круг, руны, полосы, снаряды Neon с Trail, вспышки; без источников света).
  - Удар игрока: сервер на каждом автоударе пишет игроку `BattleSwingAt`/`BattleSwingSeq`;
    `Controllers/PlayerSwingController` играет `Battle.Player.Swing.Animation` (Action, движение не трогает) только
    в зонах `Swing.Zones` — анимации нет (`nil`), механизм молчит.
  - Перепонки (вариант A): `Rig.Membranes` + `BossAnimController.membraneBones` (`Bone.Transform = rest⁻¹·T·rest`) —
    спят до импорта skinned MeshPart (этап C). Проверки: Lune `check_boss10_clips` (68), `_player` (14), `_volley` (10),
    серверные тесты «Босс 10» (4), `check_project.py` (подключение).
  - Этап C (2026-11-15, настоящая модель): `scripts/blender/dragon10/v7_game_export.py` запекает 6 атласов 1024²
    (BodyA/BodyB — половины корпуса, Head, Front, Hind + скипетр, Tail + перепонки; ~17 текселей/стад, кольца D39 —
    1.3–1.5 текселя) и пишет `Boss10_Dragon_game.fbx` (52 части + Body_2 + EyeL/R) и `Boss10_Dragon_wings_game.fbx`
    (перепонки + скелет крыльев, ≤ 2 кости на вершину), сводку `Boss10_Dragon_game.json`; режим `eyes` — канал глаз
    клипов → `Boss10_Dragon.eyes.json`. Загрузка — Open Cloud (Model 139253334200457 и 104012151110699), карты —
    upload_image (`assets/textures/art/boss10/Boss10_maps.json`); привязка — `scripts/boss10_bind_after_import.py`
    (вывод сборщика в Studio → BossModels `DRAGON_MESHES`, `Boss10_meshids.json`, `Boss10_wings_bones.json`), затем
    `make_looks.py` и `boss10_to_luau.py` (Extras, MembraneMesh, Eyes, eyes в клипах). BossService: добавочные меши на
    Weld к суставу, перепонки на Weld к Body, их Bone — на частях своих суставов (их двигает тот же Motor6D; клиент
    кости не трогает). Глаза: `BossClips.Eyes` (тот же клип и время, что поза) → BossAnimController `applyEyes`
    (Neon FFB020 ↔ SmoothPlastic 43258F). Закрытый дракон в Studio стоит на `World/Models/TestArena`
    (`MapLayout.TestArenas[10]`, x 330, в полосе z зоны 10). DevTools `FightTest` — HP боя и место бойца (Studio).
  - Этап C.1 (2026-11-15, на просмотре): клипы перевыгружены через `scripts/blender/dragon10/v7_paw_fix.py`
    (подменяет поправку наручей v7_anim5: норма касаний — от обеих стоек, отвод — огибающая ≤ 3°/кадр; режимы
    export / check / diag; прежние данные — `assets/models/backup_anim5/`). Текстуры v2 (не подключены):
    `scripts/blender/dragon10/v7_tex_v2.py` запекает по загруженным FBX (та же развёртка) окклюзию всех частей вместе
    (1.4 и 6 ст.), нормаль и высоту → `scripts/boss10_tex_v2.py` собирает цвет поверх v1 + карты металла,
    шероховатости и маску свечения (`assets/textures/art/boss10_v2/`, ID — `Boss10v2_maps.json`). Подключение —
    новые Looks (make_looks) с этими ID; поменять ColorMap во время игры нельзя (новая картинка не грузится).
- Доход (D40): `Config/Items.income` у каждого предмета; `Services/IncomeService` — раз в секунду монеты владельцу за
  экспонаты Displayed, атрибуты Coins и Income, надпись «+X/сек» над экспонатом (MuseumService.PlaceExhibit);
  клиент — плашка «+X/сек» над монетами (GymController).
- Модели предметов D39: `Config/ItemModels` (Models: MeshId из импорта, карты, размер, turn; Roughness);
  `Util/ItemFactory` — MeshPart + копия SurfaceAppearance из `Server/Looks`, приварен к невидимому хитбоксу; без меша —
  заготовка из Items. `Server/Looks/*.model.json` — шаблоны карт (Rojo; `scripts/make_looks.py` из ItemModels и
  BossModels): свойства карт SurfaceAppearance скрипт игры задать не может. MeshId после импорта —
  `scripts/bind_meshes.py <json>` (json — имена MeshPart импорта → MeshId).
- Предметы у боссов (D37, D38): `Config/Items` — коллекции босса 1 «Музей чудес» (20, D40, `wonder`) и босса 2
  «Музей безумных находок» (30, D42, `find`; до импорта — заготовки), черновые 3–10 (вид — заготовка), прежние
  предметы боссов 1–2 — `legacy` (только для старых сохранений);
  `Progression.BossLoot` — шансы по группам боссов. `Services/BossLootService` — слоты `MapLayout.ArtSlotPoints()`
  вокруг `MapLayout.BossSpot` в каждой зоне (верх постаментов или площадка `MapLayout.Arenas[i]` с поворотами), заполнение при старте и на каждом рассвете (`TimeService`), состояние реестра
  `AtBoss` (`ItemRegistry.CreateAtBoss`, у записи `boss`), подсказка «Забрать» — без боя только в Studio+DevMode
  (`GameConfig.Bosses.FreeTakeInStudio`), D10 для брошенных. В профиле у экспоната `boss` и `source = "boss"`.
- Util: `ItemFactory` (вид предмета: корень-Part; если есть меш в `Config/ItemModels` — корень невидимый хитбокс,
  а меш «Visual» приварен Weld'ом; `Preload` грузит меши при старте), `PartBuilder` (участок: части с механикой — Floor,
  Showcases/Showcase_i, Chest, Sign, Lamps/Lamp_i/Bulb/PresentationLight, Exhibits; здание `Building` — меши
  музея уровня ceil(L/2), декор на чётных, `SetBuilding`; невидимые стены `Walls`; окружение витрин — `Models/Museum`),
  `Prompts` (подсказки музея с атрибутом Action; `BindHold` — удержание «Украсть»/«Взломать»: отмена ждёт
  `GameConfig.HoldRelease.ReleaseGrace`, т. к. конец удержания приходит раньше Triggered), `Validate`, `RateLimiter`,
  `Notify`, `Log`, `DevTools` (только Studio + DevMode: `ServerStorage.DevTools` — BindableFunction Info, GiveCoins,
  RunServerTests и TimeScale/TimeSkip/TimeReset; из MCP — атрибуты `RunTests` → `TestReport` и `Command` →
  `CommandResult`; команда `BossSlot` кладёт выбранный предмет в слот босса).
- Тестовый режим владельца (решение владельца 2026-11-16, проверка дракона обычным клиентом): `Util/OwnerTest` —
  вид сервера `Off` (Studio, `GameConfig.OwnerTest.Enabled = false` или не DEV-место 10776417796 / 81392528393796),
  `Normal` (обычный сервер DEV-места), `Test` (резервный сервер DEV-места: `PrivateServerId` есть,
  `PrivateServerOwnerId == 0`; создаёт только `OwnerTestService` — check_project следит, что `ReserveServer` /
  `ShouldReserveServer` больше нигде нет). Владелец — `game.CreatorId` при `CreatorType.User`. `OwnerTestService` —
  команды чата через `Player.Chatted` (место на старом `LegacyChatService`): на обычном сервере `/test` → перенос
  владельца `TeleportAsync` с `ShouldReserveServer`; на тестовом `/fight` (бой за слот 1 дракона, HP бойца и босса
  только этого боя из `GameConfig.OwnerTest`; `/fight N` — с боссом зоны N 1…10, решение владельца 2026-11-24; зона
  без боя — отказ `BattleService.Begin`; место бойца — `OwnerTest.Spots[N]` или `DefaultSpot`), `/win` (HP босса 1,
  боец на `WinAt`, если оно есть — у дракона; ходящие боссы подходят сами), `/day`, `/night`
  (`TimeService.SkipTo` разрешён и тут), `/exit`, `/help`. `Main`: на тестовом сервере чужих кикает, владельцу —
  `PlayerSession.Join(player, { mock = true, veteran = true })`: профиль `ProfileStore.Mock`, журнал Transfers в
  памяти — в DataStore ничего не пишется. `BossService.ClosedAllowed` = Studio+DevMode или тестовый сервер.
- Участок (D35, музей D48-C): `PartBuilder.BuildPlot` — постоянные части: невидимая точка `Floor` (OwnerTag, свет
  зала и галерей), 20 мест `Showcase_n` (тумба 5 × 3 × 5 — она же столкновение постамента и опора экспоната, лицом в
  проход; дочерние `Top` — верх-индикатор: стекло — свободно, золото — занято, серый — закрыто; `Lamp` — SpotLight
  презентации и подсветки ниши; атрибуты Slot, Occupied, Open, Zone, UnlockLevel), `Chest` (x −9), двор: GymField,
  SignPost, UpgradeBoard. `PartBuilder.SetLevel` (из `PlotService.ShowLevel`) — здание уровня (`World/MuseumVisual`),
  места: без постамента на уровне — вне мира (Parent nil), открыты — `GameConfig.Museum.SlotsByLevel`
  (max(6, 2 × уровень)); атрибут участка MuseumLevel. `PlotService.ShowDumbbell` — огромная гантель уровня владельца.
- Музей D48-C: раскладка — `Config/MuseumLayout` (генерирует `scripts/d48_to_luau.py` из `d48c_layout.py` и
  `mesh_placement.json`: места, зал, галереи, павильон, лестница, хранилище, лазеры, зоны защиты, модули по уровням).
  `World/Models/MuseumD48` — временная Part-версия модулей с теми же именами и осями, что модули Blender; кирпич
  `collide = true` — оболочка (пол, стены, ступени, тумбы), она строится всегда. `World/MuseumVisual` ставит модули:
  `GameConfig.Museum.Visual` "Parts" — кирпичи; "Mesh" — меши (`MeshBuilder`) при наличии MeshId, оболочка тогда
  невидима (столкновения те же), без MeshId — Part-версия с предупреждением. Детали вида модулей хранилища — шаблон
  `ReplicatedStorage.MuseumVisual.VaultDecor` (оси участка), его копирует к себе только клиент владельца.
- Хранилище (D48-C): `Services/VaultService` — барьер в портале павильона (группа VaultBarrier_<участок>), персонаж
  владельца — VaultOwner_<участок> (с барьером своего участка не сталкивается); раз в 0.25 с чужого в объёме хранилища
  или павильона переносит к порталу; подсказки терминала и центра безопасности → `Remotes.OpenWindow` после проверки
  владельца и расстояния. В плите травы — проёмы под хранилищами, Terrain-вода вырезана по объёму хранилища на сетке
  вокселей (`WorldBuilder.VaultVolume`).
- World: `MapLayout` (раскладка аллеи, коридора зон и контур острова данными), `WorldBuilder` (строит карту;
  `BuildWater` — вода Terrain, только в Play), `ModelBuilder`
  (модель из списка кирпичей, шаблоны в `ServerStorage.Templates`), `Models/*` (кирпичные модели),
  `Signs` (надписи на вывесках), `Palette`, `Studs`, `Preview` + `FreshRequire` (предпросмотр в Edit).

## Клиент (`src/client`)
- `Main.client` — LEGO-материал на клиенте, запуск контроллеров.
- `MuseumVisualController` (D48-C): у своего участка — копия обстановки хранилища, открытая решётка павильона
  (LocalTransparencyModifier), зелёный сканер; окна по `Remotes.OpenWindow`.
- Controllers: `NotifyController` (тосты), `CarryController` («Бросить», «Ты несёшь…»),
  `InventoryController` (D46, Stud-UI: окно «Инвентарь» — карточки с 3D-превью из `ReplicatedStorage.ItemPreviews` (копии моделей делает `InventoryService`), редкость, доход, локация, статус, «×N» повторы; выставленные — по одной с «Снять», в инвентаре — стопкой с «Выставить» → выбор постамента «Поставить» / «Заменить»; сортировка по доходу и редкости, фильтр по локации, поиск, счётчики; правило фаз — неактивные кнопки и причина; кнопка «Инвентарь» в HUD слева посередине, клавиша B; подсказка постамента открывает окно для него — `OpenForSlot`; размеры — `UITokens.Inventory`; вид D50: компактные карточки с тонкой рамкой цвета редкости, «чипы» сортировки и фильтра, сетка по ширине окна; окно собирается при первом открытии и заново при смене экрана (`measure` → профиль); низкое окно (телефон) — карточки-строки, счётчики в шапке, кнопки и «чипы» на касании ≥ 52 px; в Studio экран телефона подменяют атрибуты игрока `DevViewport` (Vector2) и `DevTouch`, только при `GameConfig.DevMode`), `MuseumPromptController` (какие подсказки показывать, подсветка
  перестановки, «Улучшить гантель» на своей табличке), `PresentationController` (прожектор и название при
  выставлении), `GymController` (табличка «Улучшение» — SurfaceGui в PlayerGui на обеих сторонах UpgradeBoard каждого участка,
  текст владельцу/гостю свой; «+N» над головой; временные надписи силы и монет внизу слева).
- `UI/UIKit` — фабрики интерфейса по UI_KIT.md.
- C.2: `AssetLoaderController` (запускается первым в `Main.client`, без ожидания) — порядок загрузки ассетов:
  MaterialVariant LEGO → интерфейс и всё ближе `GameConfig.AssetLoad.CriticalRadius` от персонажа → остальное (ближние
  вперёд) → добавленное сервером позже (раз в WatchInterval). `ContentProvider:PreloadAsync` пачками, неудачные —
  повторы по `RetryDelays`, оставшиеся — `warn` с ID; замеры — атрибуты игрока `AssetLoad*`, `AssetQueueMax`,
  `AssetQueueEmptyAt`. Качество графики и StreamingEnabled не трогает. Сервер пишет время этапов старта
  (`[Main] Старт, с от начала: …`).
- C.2: `World/LovibumModel` — кристалл Ловибума стеклянный (решение владельца 2026-11-15): оболочка той же формы
  (SmoothPlastic, прозрачность 0.5, отражение 0.25, цвет кристалла светлее) и Neon-сердце ×0.55 внутри (группа Crystal, двигается
  с ним); у деталей хранятся свой размер и своя прозрачность (`SetTransparency` — поверх стекла).
- C.1 (прототип, на просмотре): `BossAuraController` — фиолетовая аура Короля-дракона по `Config/BossAura` (варианты
  A/B), только при атрибуте `workspace.BossAuraPrototype` = "A" | "B". Эмиттеры и один PointLight — у клиента на
  частях дракона; сила по State/StateAt и залпу (VolleyAt), дальность камеры (Lod) и качество графики игрока;
  частицы — своим счётчиком через `Emit()` 10 раз в секунду (Rate = 0). Урона и сети нет.
  C.2: у настоящего босса — вариант `BossAura.Active` ("C2", на просмотре; nil — без ауры), атрибут
  `BossAuraPrototype` = "A" | "B" | "C2" | "off" перекрывает его. У варианта свои `state`, `sleepPulse`, `sleepLayer`,
  `bursts` (пробуждение, начало выпада); у слоя `byArea` частота части — по её площади (`AREA_REF` 150 ст.²).
  Доработка C.2: вариант C3 (Active, на утверждении) — на основе C2 через `tweak` слоёв: языки насыщеннее
  (LightEmission 0.25), дым темнее и плотнее, штрихи длиннее, плюс лапы, кости крыльев, весь хвост; во сне сила 1.
  Финал C.2 (2026-11-16): C3 не утверждена; три варианта энергетического поля на выбор — `Flow`, `Vortex`, `Veil`
  (Active пока "C3"). У варианта, кроме частиц `layers`, есть `ribbons` и `arcs`: `chains` — нити Beam вдоль цепочек
  частей (точка на поверхности вписанного эллипсоида части под углом нити `angles`/`twist`/`wobble`, не ниже пола,
  отрезки выгнуты наружу `bulge`, у каждого конца отрезка своя Attachment, открытые концы гаснут, `tip` — до конца
  последней части); `rings` — кольца из дуг Beam вокруг части (`toward` — нормаль на соседнюю часть, `shift` — вдоль
  неё); `arcs` — пул разрядов: Beam-молния между случайными точками поверхности частей на 0.08–0.2 с. Яркость лент —
  по силе (сон — `sleepLayer`), на низком качестве — только часть нитей. Свои текстуры —
  `scripts/blender/boss10_aura_textures.py` (Blender без интерфейса). Lune `check_boss10_aura` (44) проверяет части,
  свободные морду, корону, Neck4, скипетр с кругом и перепонки (пальцы — только лентами), лент ≤ 90, разрядов ≤ 6.
  RoyalAura (утверждена владельцем 2026-11-16, `BossAura.Active`): у варианта ещё `orbits` — Attachment на части кружит каждый кадр (только
  видимая аура), эмиттеры на ней выпускают частицы по касательной (EmissionDirection Top = ось Y точки); бюджет частиц
  общий со слоями. `vary` — волна силы слоя (период, глубина), `volleyLayer` — доля надбавки залпа по слою,
  `minQuality` у колец и лент — ниже такой доли качества графики не показываются. Аура держит одно соединение
  `DescendantAdded` модели: новая часть → пересборка через 0.5 с (части дракона приходят к клиенту после тега); всё
  созданное удаляется вместе с аурой. Правка владельца «броня у груди читается»: вихри корпуса (Body, Body_2) —
  отдельный слой с тем же именем `Swirl` (та же волна и залп), `zOffset` −2.5 и прозрачнее; кольцо груди
  `brightness` 0.45, орбита у груди — `ORBIT_LAYERS_CHEST` (тусклее). Слои с одинаковым именем допустимы: имя — ключ
  `sleepLayer`/`vary`/`volleyLayer`.
- `BossService`: у мешей боссов цвет основы — средний цвет части из рига (у добавочных — цвет сустава): если карты
  SurfaceAppearance не отрисуются (BUGS — пакеты текстур), часть своего цвета, а не серая.
- C.2: `BossAnimController` пропускает позу `BossAnim.Sample` через `Shared/PoseFade` (только у рига с `Fade`):
  смена источника позы (`PoseFade.Key`: состояние, номера выпада и плана, вид плана, отмена, ходьба) или пауза
  > 0.2 с при разнице > `Fade.Jump`° — плавный догон за `Fade.Time`. Внеплановый выпад входит за `rig.CatchUpIn`
  (`BossClips`). Сервер и тайминги боя не участвуют.
- D56: `MuseumUpgradeController` — окно «Улучшение музея» (Stud-UI, золотая шапка): карточки «Сейчас» и «После
  улучшения» (уровень, мест, устройств защиты, галереи), полоса из 20 мест, цена, состояние, кнопка. Данные — атрибуты
  игрока MuseumLevel и Coins, цена и места — `Shared/MuseumRules`, запрет и отсчёт — `GameTime.UpgradeLock`; шлёт
  только номер следующего уровня (MuseumUpgrade), показывает ответ (MuseumUpgradeResult). Размер — по экрану, как
  «Магазин» (`measure`, атрибуты DevViewport / DevTouch в Studio). Кнопка «Музей» — четвёртая в `UI/MenuHud`, скрыта в
  обучении.
- `UI/MenuHud` (D56): UIGridLayout; `ColumnsFor` — один столбик, если он умещается между кнопками Roblox и низом
  экрана (на касании — кнопкой прыжка), иначе сетка в два столбца между местом «Удара» и прыжком; число столбцов —
  в `UI/HudLayout.SetMenuColumns` (соседи из `HudLayout.Track` переставляются; «Удар» при сетке — над ней).
  Замеры: `scripts/studio/museum_upgrade_ui_probe.luau` (окно) и `scripts/studio/hud_phone_sim.luau` (весь HUD).

## Общее (`src/shared`)
- Config: `GameConfig` (баланс, 10 зон D22, лимиты `MaxOnMap`; `GameConfig.Progression` = `Progression.luau` — числа D29–D31,
  только данные: его же читает симулятор `scripts/sim/progression.py`, `--tune --ratio 6 --passes 4 --tune-seeds 5`
  подбирает боссов, цены музея и гантели), `Items` (10 предметов), `Rarities`, `UITokens`, `Textures`.
- `NumberFormat.Short` — числа для игрока: 1.2K / 3.4M / 5.6B / 7.8T / 9.1Qa (D29).
- `Remotes` — имена RemoteEvent'ов, `LegoMaterial` — включение пупырышков.
- `StudUI/StudUI`, `StudUI/StudMotion`, `StudUI/CheckUIIcons` — стандарт интерфейса Stud-UI (D20), копия `src/`
  из Skill `stud-ui-clean-roblox` (MIT, LICENSE и THIRD_PARTY_NOTICES рядом). Пока не используются: переход
  интерфейса — шаг 8. Instance-имена набора французские (`Fenetre`, `Entete`, `Corps`…) — так требует Skill.

## Мир (D36, D22, D34)
- Безопасная зона: поле травы x ±183, z 0 … 131 между обрывами (`MapLayout.SafeZone`). Музеи у дальней стены:
  центры x 150, 75, 0, −75, −150, z 100 (участок 1 по +X — левая рука игрока, смотрящего на музеи), вход в −Z.
  Перед каждым спереди слева (`MapLayout.PlotYard`) поле качалки 12 × 12 (x + 20, z − 32 от центра) с гантелью и
  табличка (x + 7, z − 30). Лавки «Аура» (+X) и «Продажа» (−X) на x ±92, z 12 — ларёк ×2.6 с табло. Точка
  появления (0, 40) лицом к музеям. Фонтана, дорожек, заборов нет.
- Коридор уровней x ±92 от z = 0 вниз: 10 зон по 95 (`ZoneSize`), вход в зону 1 — граница безопасной зоны. Рамок,
  ворот и стен нет (D41): у зоны — пол с узором (Texture на верхней грани, `Config/ZonePatterns`, картинки —
  `scripts/textures/zone_patterns.py`), неоновая полоса-граница цвета зоны, голограмма названия (`World/Hologram`:
  невидимая деталь с SurfaceGui, Brightness, тег Hologram, атрибут Night — гаснуть ночью; размеры и высота —
  `MapLayout.Hologram*`, у зоны свой масштаб `HologramScale[id]` — «ПУСТЫНЯ» ×0.65), столбики `Pylon_<зона>` у обрывов (`MapLayout.PylonX`). Уровень 1 — `Models/Junkyard`
  (вещи-функции кирпичей + `Junkyard.Zone()`; пол — `Junkyard.Ground()`: дорога из плит, бугры `MOUNDS`, мусор по
  `Random.new(41)` вне `KEEP_OUT`, высота мусора на бугре — `groundHeight`). Уровень 2 — D44 (полировка D45), три модуля:
  `Models/FleaKit` — цвета `C`, помощники (`Box`, `Disc`, `Round`, `Neon`, `Board`, `Gem`, `Gable` — двускатная
  крыша из клиньев, высокая сторона клина на +Z), список надписей (`Reset`/`Label`/`Signs`, таблички `Sign_<n>`) и
  мелкий товар (`CoinSacks`, `GoldChest`, `Suitcases`, `NeonCrates`, `GiftBoxes`, `GoldBars`, `Lamp`,
  `RarityPole` — детали столба названы «RarityPole» для проверки вывесок); `Models/FleaStalls` — павильоны
  (`Pagoda`, `Rotunda`, `Tent`, `Containers`, `Vault`, `PrizeTerminal`: начало — середина переднего края, ширина
  вдоль X, лицо −Z) и большие вещи (`TreasureHoard`,
  `PocketWatch`, `CoinStack`, `SymbolMast`, `UmbrellaCart`, `LightTower` — SpotLight на цель, `Bunting`,
  `ContainerStack`; щиты на обрывах убраны на этапе C.2); `Models/FleaMarket` — `Ground()` (слои пола `TOP` с шагом 0.05: мощение до |x| 30,
  променады до бордюра `CURB` 41.5, дорожка, площадка-монета r `Arenas[2].radius` 24, поле верхом `Arenas[2].top`
  0.3) и `Zone()` → (кирпичи, надписи): павильоны передним краем на |x| `FRONT` 43, гора сокровищ `HOARD` (0, 36.4),
  часы и монеты по бокам, башни (±28, 22), тележки у входа, фонари/столбы/гирлянды на |x| 39.7, щиты на обрывах.
  Надписи пишет WorldBuilder (`World/Signs`). Без Random; у зоны с `Arenas` постаментов нет.
  Уровень 3 «Подземка» (D54) — три модуля: `Models/SubwayKit` (цвета станции `C`, общие помощники из FleaKit — тот же
  список надписей, мелочь: крысята `RatMinion`, скамейки, мусор, шар-лампа, колёса), `Models/SubwayParts` (вагоны
  `Wagon`/`ThroneWagon` длиной вдоль X, дрезина и вагонетки вдоль Z на рельсах x = ±GAUGE/2, упоры, светофоры,
  колонны, рёбра свода `Rib`, эскалатор, касса, турникеты, табло, плакаты, фонари-прожекторы `SpotPost`),
  `Models/SubwayStation` (`Ground()` — перрон |x| < 30, пути на x ±39, боковые платформы с 47, ковровая дорожка и
  площадка «Королевский люк» r `Arenas[3].radius`; подушки под предметы — верх `Arenas[3].top` 0.6; `Zone()` — стены у
  обрывов с x 86 с проёмами тоннелей и решётки эскалатора, расстановка). Стороны — для входящего игрока: слева
  (`L` = +x зоны) вагон, касса, турникеты; справа (`R` = −x) дрезина, вагонетки, эскалатор. Свет — 6 источников.
  Стены высотой `WALL_TOP` 31.5 (закрывают срез обрыва) и навес `canopy` (x 66…86, низ `CANOPY.bottom` 29.5) кончаются
  на |z| `WALL_END` = HALF − 1.6: у границ зон на x ±`MapLayout.PylonX` (86) стоят столбики. Большие поверхности —
  `SubwayKit.SOFT` (LegoSquaresSoft): `FLOOR` у плит, `{ variant = SOFT }` у тела стены и навеса.
  `export_zone.luau` пишет у детали `var` (MaterialVariant), `preview_zone.py` берёт для Soft/Deep свои карты пупырышков;
  голограмма уровня в выгрузке — невидимая деталь с надписью (как в игре), без контура. Лавки — `Models/Shops` (`Sell`, `Aura`), `MapLayout.Shops`,
  `ShopScale`; детали с именами Spin/Bob получают теги, клиент (ZoneController) вращает и покачивает их.
  У входа в коридор — `Map/SafeLine` (красная линия и «БЕЗОПАСНАЯ ЗОНА» на грани Top, холст идёт вдоль оси Z детали).
  Ночной барьер — `NightService.BuildBarrier` (невидимая стена + занавес-градиент SurfaceGui с обеих сторон + соты
  ForceField + неоновая полоса + надпись), `MapLayout.Barrier`. Постаменты — `MapLayout.ArtSlots`, место босса
  `BossSpot`, точки `ZoneEntrance(i)` и `NightReturn` (D21).
- Подписи предметов (D45): `Util/ItemFactory` — BillboardGui «Label» (Name цветом редкости, Info «Редкость ·
  +доход/сек», ширина по названию, атрибуты BaseWidth/BaseHeight/BaseLift); клиент `Controllers/ItemLabelController`
  раз в 0.1 с масштабирует подписи (Label и IncomeLabel) по высоте экрана и поднимает дальние над ближними
  (`Shared/LabelLayout.Place`, плавно); Enabled не трогает (им управляет PresentationController). Числа —
  `UITokens.ItemLabel`. Препятствия (визуальный QA босса 3): «Z z z» спящего босса — неподвижная подпись (весь путь
  подъёма); фигура босса — прямоугольники его частей на экране (`LabelLayout.Arrange` — стопка подписей и фигуры одним
  проходом: подпись дальше фигуры поднимается над ней до `BossLift` высот, иначе плавно гаснет и места не занимает —
  сквозь короля подписи не видны, поднятые не налезают друг на друга); таймер и плашка зоны — запретные
  зоны (`LabelLayout.InZone` → гаснет); подпись экспоната, у которой центр или края текста (`TextBounds`, не поля
  рамки) закрыты стеной музея (`MuseumCameraController.Blocked`), гаснет целиком; не больше `WallPerLayout` таких
  проверок за раскладку, результат помнится `WallEvery`. Угасание — множитель к исходным прозрачностям частей подписи.
- Клиент (D41): `Controllers/ZoneController` — плашка входа в уровень (CanvasGroup + StudPanel, `UITokens.LevelBanner`,
  смайлик `GameConfig.Zones[i].mood`; зона — по габаритам пола `World/Map/Zones/*/Floor`), покачивание голограмм, ночью
  они гаснут; `Controllers/OwnerTagController` — круглое фото (rbxthumb AvatarHeadShot) и ник над входом в музей
  (BillboardGui в стадах у Attachment `Floor/OwnerTag`, `MuseumHall.OwnerTag`, `UITokens.OwnerTag`).
- `Shared/TextCase.Upper` — заглавные для кириллицы (string.upper в Luau меняет только латиницу).
- Обрывы (`WorldBuilder.buildCliffs`): земля CliffDirt с вариантом LegoSquaresDeep, трава CliffGrass поверху,
  свесы травы и «натёки» на открытых гранях; сзади и по бокам поля — уступом (терраса 12 вглубь 14 с
  деревьями, выше обрыв 30), коридор — обрыв 30. Блоки не перекрываются, свесы обрезаны друг о друга.
  Земля (`Island`) — одна плита, вода Terrain вокруг (только Play).
- Музей (`World/Models/MuseumHall`): главный зал 36 × 33.4, высота 14.4, фасад z −12.7, вход 12 × 10, портик до
  z −23; уровни: 1–2 зал + портик 4 колонны; 3–4 + боковые залы x до ±29 (проход 8 × 8); 5–6 портик 6 колонн и
  парапеты; 7–8 купол; 9–10 позолота; чётные — кадки/фонари/знамёна/статуи/вазы. Все детали LegoSquaresSoft.
  Цвета — `Palette` (Museum*, Muted, Roof). Пол участка — Floor (MuseumFloor, LegoSquaresSoft).
- Проверка мерцания: `require(W.FreshRequire)(W.FaceCheck).Report(workspace.__Preview)` после Preview.Build.
  Вся карта ≈ 3 500 деталей без декора уровня 2; декор уровня 2 — 1 172 (D44), свет — 9. Предпросмотр в Edit:
  `local W = game.ServerScriptService.Server.World; require(W.FreshRequire)(W.Preview).Build()`.

## Проверки без Studio
`python scripts/check_project.py` — запрещённые ассеты и файлы (бан 2026-11-02), все `require` по путям Rojo, согласованность `Config/ItemModels` ↔ `server/Looks` ↔ MeshId ↔ FBX, шаблоны карт боссов, коллекция босса 2 в `Config/Items`, подключение босса 2 и «Барахолки». Код выхода 1 — есть ошибки. `rojo build default.project.json -o <файл>.rbxl` — локальное место из репозитория.
Lune (`~/.aftman/bin/lune`, из корня репозитория): `scripts/lune/env.luau` исполняет модули `src/` как после Rojo
(пути `game:GetService(…)`, `script.Parent`, типы из `@lune/roblox`, службы — заглушки);
`check_inventory.luau` — миграция профиля v2 → v3 на копиях данных и правило фаз (D46); `check_defense.luau` — цены, фазы, лимиты, места на полу, взлом, списание; `check_pvp.luau` — урон и HP от силы, частота, цель, запреты, нокаут; `check_theft.luau` —
правила и лимиты краж, гонки воров, номер события, 360 сценариев падения сервера при передаче (ни дублей, ни потерь);
`check_config.luau` — коллекции, скелеты, позы, анимации всех состояний (`Shared/BossAnim`), сила боя;
и раздел «Экономика D56» (утверждённые числа, неизменяемое не тронуто); `check_museum_upgrade.luau` — правила
улучшения музея (уровни, места, цены, коды отказа) и запрет по фазам на всём круге с шагом 0.5 с;
`check_boss_anim.luau` — стыки состояний и смены Moving у трёх скелетов: позы совпадают (≤ 1e-4), шаг включается со
скоростью обычной ходьбы, по кадрам внутри переходов нет одиночных скачков;
`check_world.luau` — `World/FaceCheck` декора зон 1–3 на плитах пола; у зон с площадкой босса (2 «Барахолка»,
3 «Подземка») — бюджет частей и света, пустая площадка (подушки предметов — тоже пол, до `Arenas.top`), круг боя
(r 34 от места босса) без декора выше 2, таблички надписей, столбы редкостей не закрывают надписи (лучи из 120 точек
камеры игрока), слоты; `check_config.luau` — ещё раскладка подписей (`LabelLayout`: Place, Clear, InZone, «Z z z») и
сцена «Свалки» без наложений на ПК и телефоне, а также токены интерфейса клиентских модулей (`local x =
UITokens.Раздел` → каждое `x.Имя` есть в разделе); `check_creatures.luau` — ещё Part-версия короля (части, размеры,
поворот, число блоков 150–450, габарит блоков части против скелета ≤ 0.45); `export_zone.luau <зона> <json> [id,…]` (детали, свет, надписи,
подписи предметов, окружение: соседние полы, обрывы, столбики, контур голограммы) +
`scripts/blender/preview_zone.py <json> <папка> [виды.json]` — рендер EEVEE, свет подогнан по снимку Studio
(`SUN`, `AMBIENT`, `EXPOSURE`; пупырышки картой LegoSquares, неон, стекло с прозрачностью детали, свет деталей,
надписи вывесок, фигурки игрока 5 стадов); у вида `"labels": "old" | "new"` — подписи предметов прежние или D45;
виды — в координатах зоны, `--fast` — Workbench.
Карты и меши после загрузки: `scripts/bind_maps.py` (карты → ItemModels), `scripts/bind_meshes.py` (MeshId,
дописывает), `scripts/make_looks.py` (шаблоны Looks всех предметов и боссов); порядок — `docs/IMPORT_LEVEL2.md`.

## 2026-11-14: Ловибумы ×3 (D61), пути к следующему уровню и мерцание (D62), импорт боссов 2–3
- Магазин Ловибумов (D61): `Config/Catch.PerBuy = 3` — одна покупка всегда 3 штуки, цена из `Prices` списывается один
  раз; `CatchRules.CheckBuy(prices, level, kind, coins, lovibums)` (без количества), `DataService.BuyLovibums(player,
  level, kind, price)`, `ShopAction("Buy", уровень, вид)` — количество от клиента не читается; окно — наклейка «×3»
  (`UITokens.Shop.Pack*`) вместо «−, число, +». Бросок тратит 1 (`SpendLovibum`).
- `World/FaceCheck.ScanAny` — мерцание у деталей под любым углом, клиньев и торцов цилиндров (многоугольники граней,
  обрезка Сазерленда — Ходжмена; закрывают бруски, клинья, цилиндры, шары); `Report` и `check_world` считают обе
  проверки. Вся карта (предпросмотр, 6 917 деталей) — 0 пар.
- Пути к следующему уровню (D62): «Барахолка» — `FleaMarket.Exit` (перемычка за площадкой и дорожки |x| 16.5–20.5 в
  обход горы сокровищ), «Подземка» — `SubwayStation.Way` (те же |x|, от входа к кольцу и от кольца к выходу),
  зоны 5–10 — `ZoneDecor.Path` (вызывает `WorldBuilder.buildZone` у зон без своего оформления). `check_world.pathFree`
  — на путях нет твёрдого выше 0.3 и ниже 7. Указатели «К ПОДЗЕМКЕ», «В ПУСТЫНЮ».
- Меши и карты: торговец (`TRADER_MESHES`), Крысиный король (`RATKING_MESHES`, карты `BossModels[3]`), 30 предметов
  босса 2 (`MESHES`) и 30 существ босса 3 (`CREATURE_MESHES`) загружены и привязаны; Part-версии остались запасом
  на часть без меша. Сводный FBX существ — `scripts/blender/pack_boss3_fbx.py`; `bind_meshes.py` знает
  `Boss3_RatKing*`. ID — `assets/textures/art/IDS.md`.
- План боссов 5–10 (на утверждение) — `docs/BOSSES_5_10_PLAN.md`.

## 2026-11-18/19: музей-небоскрёб — этап B (технический прототип, только режим башни DEV)
Спецификация — `docs/TOWER_PLAN.md` v3. В опубликованной игре не работает: `Util/TowerMode.For` — только Studio +
`GameConfig.DevMode` + `Tower.DevOnly` и явно включённые UserId (DevTools `TowerMode <uid> on`, тесты, `TowerFill`);
настоящему игроку — только при `ProfileStore.DataStoreState ~= "Access"` (профиль в памяти).
- **Данные.** Этаж — запись `items[uid]` + `builtAt` (place остаётся `"storage"`: `Inventory.Normalize` сбрасывает
  незнакомые place); порядок — `data.tower.order` (uid снизу вверх), FloorIndex — позиция, уникальность — `id` у
  владельца. Чистые правила — `Shared/TowerRules` (`CanBuild`, `AddFloor`, `RemoveFloor`, `MoveFloor`, `Normalize`,
  `Migrate` v5 → v6, `Check`). `DataService.TowerOnLoad` после `Inventory.Normalize`: миграция — только в режиме башни,
  `Normalize` — в режиме или если в профиле уже есть башня; шаблон профиля не менялся.
- **Защита построенного** (одно место — `DataService.refuseBuilt`): `SetItemPlace`, `ReplaceInSlot`, `RemoveItem`,
  `TransferItem` отказывают записи с `builtAt`. Реестр: состояние `Floor` (Stored → Floor, Floor → Stored только DEV),
  индекс `floorIndex[owner][itemId]` — второй Floor вида у владельца невозможен; `GetOwnedBy` включает Floor, `Unload`
  принимает Floor. Доход — `IncomeService.TotalFor` считает Displayed и Floor.
- **Сервер.** `Services/TowerService` (LoadTower/UnloadTower, Enable/Disable, Build, Remove со сдвигом — игроки раньше
  геометрии, Move, DevGiveItem, DevFill, NextSpot — места высадки по кругу и не занятые персонажами),
  `World/TowerBuilder` (модель `Plot_n.Tower`: Lobby, Floors/F_<uid>, Roof; невидимый каркас со столкновениями у
  каждого этажа всегда — плита, 4 стены, тумба; экспонат `ItemFactory`; Attachment `ElevatorPoint` + подсказка
  `ElevatorPrompt`, места `Spot1–4`; атрибуты Tower: Origin, Version, FloorCount, Accent; F_: Uid, ItemId, Index, BaseY,
  State; PrimaryPart не задаётся — точка опоры = оси этажа), `Services/ElevatorService` (подсказка → OpenWindow
  «Elevator»; ElevatorGo: башня, ShiftLock, жив, Knocked / Snared / IsPinned, у точки лифта по серверу, этаж есть,
  лимит → `MoveGuard.Teleport`). `PlotService.UseTower` снимает Building и Showcases участка и возвращает их;
  `ShowLevel` в режиме башни здание не строит. `PlayerSession`: в режиме — LoadTower / UnloadTower вместо музея.
  `InventoryService`: `SetTowerHooks` (build, describe, active) — действие «Build», поля окна `tower / floor /
  duplicate`; в режиме башни постаментные действия отказывают.
- **Клиент.** `Controllers/TowerController` — убранство из `Shared/Floors` (`FloorBuilder`, `Placeholder`,
  `Floors.Lobby`, `Floors.Roof`) в `workspace.TowerDecor`: LOD интерьер / фасад / силуэт (`Tower.Lod`), очередь сборки
  ≤ BuildPartsPerFrame, анимации появления (State Building) и сдвига (BaseY), счётчики-атрибуты папки (Views,
  PartsInterior/Facade/Silhouette, Queue, Builds, Last/MaxInteriorMs). Стены убранства на месте стен каркаса —
  `occlude`: сталкиваются только у этого клиента (камера Roblox не уходит сквозь невидимую серверную стену).
  `Controllers/ElevatorController` — окно «Лифт» (Flat, синяя шапка), затемнение до сборки интерьера (≤ 1 с).
  `InventoryController`: «Построить этаж», «Этаж N», «Повтор · только продажа» (без запрета по фазе — не утверждён).
- **DEV.** DevTools: `TowerMode`, `GiveItem`, `BuildFloor`, `RemoveFloor`, `MoveFloor`, `TowerFill <N>` (тестовые
  владельцы на свободных участках, N этажей у всех башен), `TowerStats`. Нагрузка интерьера — атрибут Workspace
  `TowerStress`. Замеры клиента — `scripts/studio/tower_probe.luau`.
- **Проверки.** Lune `check_tower` (правила, миграция, починка, 10 000 случайных шагов, бюджет LOD, площадка лифта,
  FaceCheck, стены occlude внутри каркаса); серверные `Tests/TowerTests` (16, подключены в `ServerTests` одной строкой).

## 2026-11-19: музей-небоскрёб — этап C (дальний вид, экспонаты, три эталонных этажа; только режим башни DEV)
Отчёт — `assets/concepts/tower_c/REPORT.md`.
- **LOD.** `TowerController`: у каждого вида всегда есть оболочка — фасад (ближе `Lod.Facade`, выход на Hysteresis)
  или силуэт; дальше ничего не прячется. Смена фасад ↔ силуэт не чаще `Lod.MinSwap` (вход в интерьер — сразу),
  старая модель удаляется, когда готова новая. Счётчики папки обновляются и когда видов не осталось.
  Дальний силуэт этажа (`<prefix>_S_All`, ≤ 400 треугольников, один MeshPart) с 2026-11-23 — из
  `scripts/blender/lod_silhouette.py` (основа прежнего силуэта + крупные детали фасада, без граней разного цвета в
  одной плоскости), меши `assets/models/floors_lod/<Тема>Sil.fbx`, ID — `floors_lod/lod_asset_ids.json`, проверка —
  `scripts/blender/lod_check.py`; привязка — `floor_bind_meshes.py` (BUGS.md, «Выкатка дальнего LOD»).
- **Экспонат.** Сервер (`TowerBuilder.placeExhibit`) — одна невидимая деталь `Exhibit` (габарит
  `ItemFactory.SizeOf` × масштаб темы; атрибуты ItemUid, ItemId, TowerHitbox, Scale; «+X/сек»; столкновения и лучи).
  Клиент — копия `ReplicatedStorage.ItemPreviews[itemId]` (`InventoryService.EnsurePreview`, её зовёт TowerService)
  внутри модели интерьера на месте хитбокса, `ScaleTo(Scale)`, без столкновений; у корня `ItemUid` и `TowerFloor` —
  `CreatureController` оживляет её спокойной позой, хитбокс (`TowerHitbox`) пропускает. Превью теперь с суставами и
  сваркой (во ViewportFrame не мешают).
- **Темы.** `Shared/Floors/init` — THEMES { GoldenThrone, TRexSkeleton, SpaceHelmet }, `Floors.ExhibitAt(theme, cfg)`
  → (CFrame верха подставки с поворотом, масштаб); у темы `shell`, `exhibit`, `decor(cfg, ctx, tier)`. Общие детали —
  `Floors/Kit`: стены с проёмами-объединениями и поясами цвета (строки по высоте, слияние одинаковых), стекло в
  толще стены, двери лифта в нише задней стены (площадка лифта пуста), пояса, кромка плиты, потолок, пол, каркас
  (`Slab` — первая деталь). Детали тем — `LegoSquaresSoft` (`Kit.B`, поле `variant` у `FloorBuilder`). Каждая деталь
  этажа — в полосе высоты −плита…19, поэтому любые темы стыкуются без пересечений (`check_tower`: все пары тем).
- **Интерфейс режима башни.** Атрибут игрока `TowerMode` (TowerService Load/Unload): `InventoryController` — «Этажей:
  N», плашка запрета скрыта; `ElevatorController` — быстрый переход «Холл / −10 / страница / +10 / Верх», страницы по
  10 этажей.
- **Стиль тем (2026-11-19, позже).** `Kit.B` ставит деталям тем `LegoSquaresItem` (`Kit.Tile`, контурные квадраты
  предметов D39); `Kit.Bone(points, z, thick, depth)` — изогнутая сужающаяся кость из отрезков в плоскости XY;
  `FloorBuilder` — `light.spot` (прожектор вниз). Наружный декор может выступать за контур 36 × 34 (портик «Трона» —
  до −22.4 по Z), но остаётся в полосе высоты этажа.

## 2026-11-19: этажи из мешей Blender (эталон — «Золотой трон»; только режим башни DEV)
- **Конвейер.** `scripts/blender/floorkit.py` (тела с фаской, рамы, плоскости с проёмами на регулярной сетке, стёганая
  обивка, огранка камней, затенение лучами в цвета вершин) + `floor_golden_throne.py` (геометрия в осях этажа, рендеры)
  → `assets/models/floors/GoldenThroneFloor.fbx` и `.json` (центры, размеры). Загрузка — Open Cloud (модель), MeshId —
  `.ids.json`, привязка — `scripts/floor_bind_meshes.py` → `Shared/Floors/FloorMeshes`.
- **Вид.** Один MeshPart на материал и уровень: tile (Plastic + LegoSquaresItem), smooth, glass. Оттенки и затенение — в
  цветах вершин, цвет детали — Color в теме (`LOOK`), поэтому палитра меняется без повторной загрузки. Детали Accent
  несут свои цвета в вершинах (ковёр, камни), Color у них — общее приглушение.
- **Игра.** `World/FloorMeshLoader.Start()` (зовёт `TowerBuilder.NewTower`) грузит шаблоны в
  `ReplicatedStorage.FloorMeshes` (атрибут Ready); `FloorBuilder`: кирпич с полем `mesh` — клон шаблона (без
  столкновений, лучей и теней), `WaitMeshes`; `TowerController` ждёт шаблоны один раз (до 15 с). Каркас сервера —
  прежние невидимые детали по форме зала (помост «плюсом», пилоны, стены, скамьи); стены упора камеры спрятаны
  между обшивками зала и фасада.
- **Проверки.** `check_tower`: меши есть в FloorMeshes и стоят на своём месте, треугольники ≤ 14 000 / 12 000 / 400,
  каркас ≤ 24; грани и площадка лифта — по обычным деталям.
- **Этаж в стиле D39 (2026-11-19, ночь).** Детали этажа — два вида: Rings (Plastic + MaterialVariant `LegoRingsD39`,
  `Config/Textures.RingsD39`: плитка 2.4 стада = 4 × 4 квадрата-контура с числами `art_style.RING`, фон белый) и
  Smooth (SmoothPlastic). Цвета (палитра предмета) и затенение — в цветах вершин, Color детали — множитель яркости
  из темы. Вариант создаёт Rojo из `default.project.json`; `LegoMaterial.ensure` в игре создать его не может
  (нужны права плагина) — теперь при неудаче предупреждает, а не роняет запуск сервера.
- **Свет и тени этажа из мешей (2026-11-19, под утро).** Объём даёт не свет игры, а запекание в цвета вершин:
  `floorkit.Part(grid=…)` режет меш сеткой (зал 1.25 / 2.5 стада, фасад 2 / 3), `shade_parts` кладёт окклюзию по
  сетке, множитель стороны блока (`form`) и зоны зала (`zone`); узкие грани детали с квадратами уходят в гладкую
  (`partner`, `narrow`). В теме — одна лампа в центре зала. `TowerController.soloLights`: камера внутри этажа или
  холла — лампы остальных видов этой башни погашены (атрибут модели `LightsOn`), камера снаружи — все включены.
- **Этаж в стиле «крупные квадраты» (2026-11-19, утро).** Детали Rings — Plastic + MaterialVariant `LegoSquaresBold`
  (`Config/Textures.SquaresBold`, плитка 2 стада, один вдавленный квадрат на стад). Геометрия блоков с квадратами —
  на целых координатах этажа; узкие грани (< 0.9) уходят в гладкую деталь. `floorkit.adaptive_cut` (до finish) режет
  крупные грани только там, где меняется окклюзия; `Part(adapt=True)`. Поле темы `soloLights = true` включает
  гашение ламп остальных видов башни, пока камера на этом этаже (`TowerController.soloLights`).
- **Три материала этажа (2026-11-20).** Золото зала — `LegoSquaresBold`, золото фасада — `LegoSquaresFar` (мягче, его
  видят издалека), ткань — `LegoSquaresQuiet` (квадраты едва заметны); все три — одна сетка в стад, плитка 2 стада
  (`scripts/textures/squares_bold.py`). В скрипте этажа ткань переносится в детали *_Quiet по цвету
  (`Part.give_tones`), у брусков с рисунком — фаска рёбер (`Part(bevel=…)`), узкие фаски уходят в гладкую деталь.
- **Предметы на этажах — текстура боссов (2026-11-21, решение владельца).** Архитектура этажа — квадраты эталона
  GoldenThrone (`LegoSquaresFar`/`Bold`/`Quiet`); вещи внутри и на фасаде (мебель, фигуры, механизмы) — кольца D39
  в масштабе боссов: MaterialVariant `LegoRingsD39Boss` (`Config/Textures.RingsD39Boss` — те же карты, что у
  предметов, плитка 7.2 стада = шаг 1.8, как у боссов ×3; эталон — Крысиный король). Детали `F_Props`/`I_Props`
  (`floorbase.Floor.FP/IP`) → в `MeshTheme.look` суффикс `_Props$` = Plastic + `LegoRingsD39Boss`. Разводка в
  `floorkit.Part.route`: тело гладкой детали с длиной ≥ 8 и толщиной ≥ 0.4 → архитектура (квадраты), толщина ≥ 0.5
  и средний размер ≥ 0.9 → Props (кольца), иначе гладкое; накладки `slab`/`chamfer` ≥ 0.9 в плоскости → квадраты;
  узкие грани Props < 0.5 → гладкая. Якоря-«невидимки» симметричны (фасад ±30, зал ±17/±16), чтобы центр рисунка
  совпадал с целой координатой этажа.
- **Вещи на утверждённых этажах (2026-11-21, «да, перевести»).** 13 утверждённых этажей (GoldenThrone, TRexSkeleton,
  SpaceHelmet, Colosseum, MagicMushroom, GoldenMic, Moai, TutMask, TerracottaWarrior, StatueOfLiberty, GoldenGamepad,
  CrystalDino, TrophyBurger) пересобраны с Props, архитектура не тронута: `B.Floor(..., keep_arch=True)` выключает
  автоматическую разводку, на кольца уходят только тела в участках `F.objects(True)` … `F.objects(False)` (у эталонов
  GoldenThrone/TRex/Space — своя `objects()`); в участке гладкие и брусковые тела (FS/IS, FR/IR) толщиной ≥ 0.25 и
  средним размером ≥ 0.6 идут в FP/IP (`floorkit.FORCE_THICK/FORCE_MID`), ткань (Quiet) и стекло — как были. Пустые
  детали (≤ 4 треугольников — только якоря, с 2026-11-22; раньше ≤ 2) `floor_bind_meshes.py` не привязывает. Откат —
  `assets/concepts/tower_props/backup_v1/` (скрипты, темы, модели, кадры «до»).
- **Общий декор этажей (партия 4, 2026-11-22)** — `scripts/blender/floordecor.py`: `palm`, `torch`, `barrel`, `crate`,
  `lantern`, `bush`, `flower`, `chain` (провис, возвращает точки — на них вешают лампочки/фонари). Этажи партии 4
  собраны на `B.Floor` без `keep_arch` (автоматическая разводка); экспонат у всех — (0, TOP, −3), постамент-каркас
  в теме повторяет ступени из скрипта.
- **Партия 5 этажей (2026-11-22)** — тот же конвейер; `floorbase._art_path(kind, name)` ищет FBX предмета и карту
  цвета в `assets/<kind>/art/` и подпапках (`boss4/` и др.) — только для предпросмотра экспоната в Blender. Темы —
  раздел «пятая партия» в `Floors/init.luau`; SubwayOctopus — масштаб экспоната 2.4. Реквизит перед фасадом — не
  дальше ≈ −FZ−7.6 (дальше он висит над этажом ниже).

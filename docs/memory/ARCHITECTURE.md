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
- После импорта: модели → `ServerStorage.ImportedModels` (Rojo его не трогает), ID мешей →
  `assets/models/PackN.meshids.json`, затем `python scripts/models_to_luau.py` пишет `World/MeshModels.luau`.
  `World/MeshBuilder` грузит меши при старте (`CreateMeshPartAsync`) и собирает модель: деталь в центр из layout
  и поворот на π (импорт повернул меши), без столкновений и запросов; Glass — прозрачность из GameConfig.Models.
- `assets/textures` — LEGO-текстуры дизайнера (загружены в Roblox, ID в `Config/Textures`).
  `scripts/install-textures.ps1` копирует их в content установленной Studio (запасной путь `rbxasset://`).

## Данные
- Профиль — ProfileStore (`Server/Vendor`), шаблон `Config/ProfileTemplate` (schema 2: + strength, dumbbellLevel;
  миграция v1 → v2 в `DataService.LoadAsync`, DESIGN.md §2).
  В профиль попадают только экспонаты (`Displayed`) и хранилище (`Stored`).
- Состояния экземпляра предмета — `ItemRegistry` (uid → state), граф в DESIGN.md §1:
  OnMap → Carried → Displayed ⇄ Stored, MoveSlot / SwapSlots на витринах.

## Сервер (`src/server`)
- `Main.server` — RemoteEvent'ы, LEGO-материал, постройка мира, запуск сервисов; вход/выход — `Services/PlayerSession`.
- Services: `DataService` (профиль), `PlotService` (8 участков), `ItemRegistry` (состояния), `CarryService`
  (подбор/перенос/бросок, `AttachCarried`), `BossLootService` (4 предмета у каждого босса, D37, D10 исчезновение), `MuseumService`
  (выставить, переставить, повернуть, презентация), `StorageService` (сундук и хранилище), `GymService` (D34:
  такт качания — владелец в поле своего двора, сила = Power[уровень] × (1 + сила музея D31); гостю подсказка;
  «Улучшить» — подсказка на табло и запрос GymUpgrade, все проверки на сервере; атрибуты игрока Strength,
  Coins, DumbbellLevel). Скорость от силы — `Shared/Speed` + `CarryService.RefreshSpeed`.
- `Services/PlayerSession` — вход (участок → профиль → здание и гантель → музей → хранилище → сообщение) и выход;
  один путь для игры и тестов (`Join(player, { mock = true })` — профиль в памяти, ProfileStore.Mock).
- Тесты (`Server/Tests`, только Studio, в Play): `ServerTests.Run()` через `ServerStorage.DevTools.RunServerTests`
  — 23 сценария (двое тестовых игроков, время и ночь, предметы у боссов) (`TestPlayer`: таблица с полями Player и персонаж-манекен, UserId < 0).
  Действия — теми же обработчиками, что подсказки (`MuseumService/StorageService/GymService/CarryService.Handlers`).
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
  отошёл) → win (Award: предмет в руки) / lose (отброс LinearVelocity, без телепорта) / escape (дальше Leash) / night /
  abort → Victory или Defeat → Return → FallAsleep (подсказки открыты) → Sleep. Полоски HP — BillboardGui над боссом
  и бойцом. Клиент: `Shared/BossAnim` (Transform суставов по состоянию и времени — смешение поз, циклы дыхания,
  шагов, выпады и попадания поверх) + `Controllers/BossAnimController` (Stepped, у всех клиентов одинаково, «Z z z»).
- Доход (D40): `Config/Items.income` у каждого предмета; `Services/IncomeService` — раз в секунду монеты владельцу за
  экспонаты Displayed, атрибуты Coins и Income, надпись «+X/сек» над экспонатом (MuseumService.PlaceExhibit);
  клиент — плашка «+X/сек» над монетами (GymController).
- Модели предметов D39: `Config/ItemModels` (Models: MeshId из импорта, карты, размер, turn; Roughness);
  `Util/ItemFactory` — MeshPart + копия SurfaceAppearance из `Server/Looks`, приварен к невидимому хитбоксу; без меша —
  заготовка из Items. `Server/Looks/*.model.json` — шаблоны карт (Rojo; `scripts/make_looks.py` из ItemModels и
  BossModels): свойства карт SurfaceAppearance скрипт игры задать не может. MeshId после импорта —
  `scripts/bind_meshes.py <json>` (json — имена MeshPart импорта → MeshId).
- Предметы у боссов (D37, D38): `Config/Items` — коллекция босса 1 «Музей чудес» (20, D40, `wonder`) и черновые
  коллекции 2–10 (вид — заготовка), прежние предметы босса 1 — `legacy` (только для старых сохранений);
  `Progression.BossLoot` — шансы по группам боссов. `Services/BossLootService` — слоты `MapLayout.ArtSlots` вокруг
  `MapLayout.BossSpot` в каждой зоне, заполнение при старте и на каждом рассвете (`TimeService`), состояние реестра
  `AtBoss` (`ItemRegistry.CreateAtBoss`, у записи `boss`), подсказка «Забрать» — без боя только в Studio+DevMode
  (`GameConfig.Bosses.FreeTakeInStudio`), D10 для брошенных. В профиле у экспоната `boss` и `source = "boss"`.
- Util: `ItemFactory` (вид предмета: корень-Part; если есть меш в `Config/ItemModels` — корень невидимый хитбокс,
  а меш «Visual» приварен Weld'ом; `Preload` грузит меши при старте), `PartBuilder` (участок: части с механикой — Floor,
  Showcases/Showcase_i, Chest, Sign, Lamps/Lamp_i/Bulb/PresentationLight, Exhibits; здание `Building` — меши
  музея уровня ceil(L/2), декор на чётных, `SetBuilding`; невидимые стены `Walls`; окружение витрин — `Models/Museum`),
  `Prompts` (подсказки музея с атрибутом Action), `Validate`, `RateLimiter`, `Notify`, `Log`, `DevTools` (только
  Studio + DevMode: `ServerStorage.DevTools` — BindableFunction Info, GiveCoins, RunServerTests и TimeScale/TimeSkip/TimeReset для проверок через MCP).
- Участок (D35): `PartBuilder.BuildPlot` — музей, витрины, сундук и двор: Yard, YardPath, GymField (поле с
  неоновыми плитками цвета участка), SignPost и UpgradeBoard (табло; текст рисует клиент); `PlotService.ShowDumbbell`
  ставит огромную гантель уровня владельца (`GiantDumbbell`), атрибуты модели OwnerUserId, OwnerName, DumbbellLevel.
- World: `MapLayout` (раскладка аллеи, коридора зон и контур острова данными), `WorldBuilder` (строит карту;
  `BuildWater` — вода Terrain, только в Play), `ModelBuilder`
  (модель из списка кирпичей, шаблоны в `ServerStorage.Templates`), `Models/*` (кирпичные модели),
  `Signs` (надписи на вывесках), `Palette`, `Studs`, `Preview` + `FreshRequire` (предпросмотр в Edit).

## Клиент (`src/client`)
- `Main.client` — LEGO-материал на клиенте, запуск контроллеров.
- Controllers: `NotifyController` (тосты), `CarryController` («Бросить», «Ты несёшь…»),
  `StorageController` (окно хранилища), `MuseumPromptController` (какие подсказки показывать, подсветка
  перестановки, «Улучшить гантель» на своей табличке), `PresentationController` (прожектор и название при
  выставлении), `GymController` (табличка «Улучшение» — SurfaceGui в PlayerGui на UpgradeBoard каждого участка,
  текст владельцу/гостю свой; «+N» над головой; временные надписи силы и монет внизу слева).
- `UI/UIKit` — фабрики интерфейса по UI_KIT.md.

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
  `MapLayout.Hologram*`), столбики `Pylon_<зона>` у обрывов (`MapLayout.PylonX`). Уровень 1 — `Models/Junkyard`
  (вещи-функции кирпичей + `Junkyard.Zone()`; пол — `Junkyard.Ground()`: дорога из плит, бугры `MOUNDS`, мусор по
  `Random.new(41)` вне `KEEP_OUT`, высота мусора на бугре — `groundHeight`). Лавки — `Models/Shops` (`Sell`, `Aura`), `MapLayout.Shops`,
  `ShopScale`; детали с именами Spin/Bob получают теги, клиент (ZoneController) вращает и покачивает их.
  У входа в коридор — `Map/SafeLine` (красная линия и «БЕЗОПАСНАЯ ЗОНА» на грани Top, холст идёт вдоль оси Z детали).
  Ночной барьер — `NightService.BuildBarrier` (невидимая стена + занавес-градиент SurfaceGui с обеих сторон + соты
  ForceField + неоновая полоса + надпись), `MapLayout.Barrier`. Постаменты — `MapLayout.ArtSlots`, место босса
  `BossSpot`, точки `ZoneEntrance(i)` и `NightReturn` (D21).
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
  Вся карта ≈ 3 500 деталей. Предпросмотр в Edit:
  `local W = game.ServerScriptService.Server.World; require(W.FreshRequire)(W.Preview).Build()`.

## Проверки без Studio
`python scripts/check_project.py` — запрещённые ассеты и файлы (бан 2026-11-02), все `require` по путям Rojo, согласованность `Config/ItemModels` ↔ `server/Looks` ↔ MeshId ↔ FBX, файлы коллекции босса 2 и совпадения id. Код выхода 1 — есть ошибки. `rojo build default.project.json -o <файл>.rbxl` — локальное место из репозитория.

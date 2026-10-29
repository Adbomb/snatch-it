# Архитектура

Обновлено: 2026-10-29. Подробности решений — `DESIGN.md`.

## Сборка
- Rojo (`default.project.json`): `src/shared` → `ReplicatedStorage.Shared`, `src/server` → `ServerScriptService.Server`,
  `src/client` → `StarterPlayer.StarterPlayerScripts.Client`.
- Там же свойства мест: `Workspace.StreamingEnabled = false` (D14), свет (LightingStyle Realistic,
  PrioritizeLightingQuality, Atmosphere, ColorCorrection), `MaterialService` с вариантом «LegoStuds» и `PlasticName`.
- Предметы-меши (V3): `scripts/blender/*.py` строит модель из LEGO-кирпичей в Blender без интерфейса →
  `assets/models/*.fbx` → импорт в Studio (File → Import 3D, делает заказчик) → ID меша и текстуры в
  `Config/ItemModels`. Текстура-палитра всех предметов — `assets/textures/item_palette.png` (4×4 цвета).
  Материал мешей — SmoothPlastic (пупырышки у модели свои). Оригинал импорта лежит в `ServerStorage.ImportedModels`.
- Пачки моделей мира (шаг 3, D33): библиотека `scripts/blender/lego.py` (блоки с фаской 1–2 сегмента, цилиндры,
  купола, скаты, призмы, вазы, «пиксельные» диски и шары; координаты как в Roblox; bmesh; `rot()` — поворот в
  градусах вокруг осей Roblox) + скрипт пачки `scripts/blender/packN_*.py` → `assets/models/PackN.fbx` (без
  материалов и текстур) и `PackN.layout.json`. Деталь = «роль» = цвет, объект `<Модель>_<Роль>`; в layout для
  каждой: центр и размер в координатах модели (центр габаритов = точка опоры MeshPart), color (hex или Accent /
  AccentDark / DecorAccent — цвет участка), material (Plastic / Glass / Neon), decor (только чётные уровни),
  triangles. В игре MeshPart: Color, Material, без TextureID — пупырышки даёт MaterialVariant «LegoStuds».
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
- `Main.server` — RemoteEvent'ы, LEGO-материал, постройка мира, запуск сервисов, вход/выход игроков.
- Services: `DataService` (профиль), `PlotService` (8 участков), `ItemRegistry` (состояния), `CarryService`
  (подбор/перенос/бросок), `ItemSpawnService` (предметы в зонах, D10 исчезновение), `MuseumService`
  (выставить, переставить, повернуть, презентация), `StorageService` (сундук и хранилище), `GymService` (D34:
  такт качания — владелец в поле своего двора, сила = Power[уровень] × (1 + сила музея D31); гостю подсказка;
  «Улучшить» — подсказка на табло и запрос GymUpgrade, все проверки на сервере; атрибуты игрока Strength,
  Coins, DumbbellLevel). Скорость от силы — `Shared/Speed` + `CarryService.RefreshSpeed`.
- Util: `ItemFactory` (вид предмета: корень-Part; если есть меш в `Config/ItemModels` — корень невидимый хитбокс,
  а меш «Visual» приварен Weld'ом; `Preload` грузит меши при старте), `PartBuilder` (участок: части с механикой — Floor,
  Showcases/Showcase_i, Chest, Sign, Lamps/Lamp_i/Bulb/PresentationLight, Exhibits; здание `Building` — меши
  музея уровня ceil(L/2), декор на чётных, `SetBuilding`; невидимые стены `Walls`; окружение витрин — `Models/Museum`),
  `Prompts` (подсказки музея с атрибутом Action), `Validate`, `RateLimiter`, `Notify`, `Log`, `DevTools` (только
  Studio + DevMode: `ServerStorage.DevTools` — BindableFunction Info и GiveCoins для проверок через MCP).
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

## Мир (D35, D22, D34)
- База (D35): 5 музеев в линию (центры x = −116 … 116 шагом 58, z = −32), фасадом к зонам (−Z); перед каждым
  двор 44 × 26 (дорожка 12, поле 14 × 20 справа по x участка, табличка слева). Площадь z −130 … −80 в клетку:
  точка появления (0, −95) смотрит на музеи, фонтан (0, −113), фонари, кусты в проходах, деревья за музеями.
  Ворота в зоны на z = −130.
- За воротами двор (12) и 10 зон одним коридором шириной 60, каждая 60 в длину (z −142 → −742): игрок проходит
  зону N, чтобы попасть в N+1. На входе каждой зоны — стена `ZoneWall` с проёмом 16 и ворота с вывеской
  «N. Название» и «Босс 💪 сила». В зоне 5 постаментов-точек `ItemSpawn` с атрибутом `Zone`, место босса
  `MapLayout.GuardSpot`, точка возврата `ZoneEntrance(i)` и ночная `NightReturn` (D21).
- Остров = прямоугольник базы (x ±160, z −130 … 14) + коридор (`MapLayout.Outline`, `IslandRects`). Стена-граница в шахматку и два
  ряда холмов с деревьями — по контуру; дальше трава, песок (плиты без перекрытий) и вода Terrain до горизонта
  с песчаным дном. Baseplate шаблона Main удаляет в Play.
- Музей: пол на ступень выше площади (1.4), здание — меши уровня (D33), свой цвет участка
  (`Museum.Accents`). Вся карта около 4 000 частей. Предпросмотр в Edit:
  `local W = game.ServerScriptService.Server.World; require(W.FreshRequire)(W.Preview).Build()`.

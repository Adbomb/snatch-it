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
- `assets/textures` — LEGO-текстуры дизайнера (загружены в Roblox, ID в `Config/Textures`).
  `scripts/install-textures.ps1` копирует их в content установленной Studio (запасной путь `rbxasset://`).

## Данные
- Профиль — ProfileStore (`Server/Vendor`), шаблон `Config/ProfileTemplate` (schema 1, DESIGN.md §2).
  В профиль попадают только экспонаты (`Displayed`) и хранилище (`Stored`).
- Состояния экземпляра предмета — `ItemRegistry` (uid → state), граф в DESIGN.md §1:
  OnMap → Carried → Displayed ⇄ Stored, MoveSlot / SwapSlots на витринах.

## Сервер (`src/server`)
- `Main.server` — RemoteEvent'ы, LEGO-материал, постройка мира, запуск сервисов, вход/выход игроков.
- Services: `DataService` (профиль), `PlotService` (8 участков), `ItemRegistry` (состояния), `CarryService`
  (подбор/перенос/бросок), `ItemSpawnService` (предметы в зонах, D10 исчезновение), `MuseumService`
  (выставить, переставить, повернуть, презентация), `StorageService` (сундук и хранилище).
- Util: `ItemFactory` (вид предмета: корень-Part; если есть меш в `Config/ItemModels` — корень невидимый хитбокс,
  а меш «Visual» приварен Weld'ом; `Preload` грузит меши при старте), `PartBuilder` (участок: части с механикой — Floor,
  Showcases/Showcase_i, Chest, Sign, Lamps/Lamp_i/Bulb/PresentationLight, Exhibits; здание — `Models/Museum`),
  `Prompts` (подсказки музея с атрибутом Action), `Validate`, `RateLimiter`, `Notify`, `Log`.
- World: `MapLayout` (раскладка аллеи и зон данными), `WorldBuilder` (строит карту), `ModelBuilder`
  (модель из списка кирпичей, шаблоны в `ServerStorage.Templates`), `Models/*` (кирпичные модели),
  `Signs` (надписи на вывесках), `Palette`, `Studs`, `Preview` + `FreshRequire` (предпросмотр в Edit).

## Клиент (`src/client`)
- `Main.client` — LEGO-материал на клиенте, запуск контроллеров.
- Controllers: `NotifyController` (тосты), `CarryController` («Бросить», «Ты несёшь…»),
  `StorageController` (окно хранилища), `MuseumPromptController` (какие подсказки показывать, подсветка
  перестановки), `PresentationController` (прожектор и название при выставлении).
- `UI/UIKit` — фабрики интерфейса по UI_KIT.md.

## Общее (`src/shared`)
- Config: `GameConfig` (баланс, зоны D15, гантели D17; `GameConfig.Progression` = `Progression.luau` — числа D29,
  только данные: его же читает симулятор `scripts/sim/progression.py`, `--tune` подбирает боссов и цены музея), `Items` (10 предметов), `Rarities`, `UITokens`, `Textures`.
- `Remotes` — имена RemoteEvent'ов, `LegoMaterial` — включение пупырышков.
- `CheckUI/CheckUI`, `CheckUI/Responsive` — стандарт интерфейса Check-UI (D20), копия модулей из Skill.
  Пока не используются: переход интерфейса — отдельный шаг.

## Мир (D12, D15)
- Аллея вдоль Z: старт и спортзал на +Z, ворота на -Z. Музеи по 4 с каждой стороны, входом на аллею.
- За воротами дорожка и 4 зоны (Свалка, Барахолка, Склад, Банк) — дальше от ворот = реже предметы.
  В каждой зоне 5 постаментов-точек `ItemSpawn` с атрибутом `Zone`.
- Граница: стена из кирпичей в шахматку и два ряда ступенчатых холмов с деревьями (детали ≤ 40 стадов),
  на траве крупные пятна другого оттенка.
- Музей (`World/Models/Museum`): пол на ступень выше аллеи (1.4), здание ~190 частей, свой цвет участка
  (`Museum.Accents`). Вся карта около 3650 частей. Предпросмотр в Edit:
  `local W = game.ServerScriptService.Server.World; require(W.FreshRequire)(W.Preview).Build()`.

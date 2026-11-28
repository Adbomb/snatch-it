-- Точка входа клиента: запускает контроллеры. Клиент только показывает и отправляет намерения.
-- Зависит от Controllers/*, Shared/LegoMaterial.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Controllers = script.Parent:WaitForChild("Controllers")

-- LEGO-пупырышки на всём Plastic (D13): замена материала действует только у того, кто её включил.
task.spawn(require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("LegoMaterial")).Apply)
-- Порядок загрузки ассетов (материалы мира → рядом с игроком → остальное), без ожидания: отдельный поток.
require(Controllers:WaitForChild("AssetLoaderController")).Start()

require(Controllers:WaitForChild("NotifyController")).Init()
require(Controllers:WaitForChild("CarryController")).Init()
require(Controllers:WaitForChild("InventoryController")).Init()
require(Controllers:WaitForChild("MuseumPromptController")).Init()
require(Controllers:WaitForChild("PresentationController")).Init()
require(Controllers:WaitForChild("GymController")).Init()
require(Controllers:WaitForChild("TrainingController")).Init()
require(Controllers:WaitForChild("TimeController")).Init()
require(Controllers:WaitForChild("BossAnimController")).Init()
require(Controllers:WaitForChild("BossVolleyController")).Init() -- босс 10: эффекты магического залпа
require(Controllers:WaitForChild("BossAuraController")).Init() -- босс 10: прототип ауры C.1 (только по атрибуту)
require(Controllers:WaitForChild("PlayerSwingController")).Init() -- анимация автоудара (пока без анимации)
require(Controllers:WaitForChild("ZoneController")).Init()
require(Controllers:WaitForChild("ZoneAtmosphereController")).Init() -- свет по зонам и сияние «Ледника»
require(Controllers:WaitForChild("SlotGlowController")).Init() -- D71: пульсация подсветки постаментов
require(Controllers:WaitForChild("OwnerTagController")).Init()
require(Controllers:WaitForChild("ItemLabelController")).Init()
require(Controllers:WaitForChild("PvpController")).Init()
require(Controllers:WaitForChild("DefenseController")).Init()
require(Controllers:WaitForChild("ShopController")).Init() -- D55: магазин Ловибумов
require(Controllers:WaitForChild("MuseumUpgradeController")).Init() -- D56: улучшение музея
require(Controllers:WaitForChild("CreatureController")).Init() -- D55: живые существа
require(Controllers:WaitForChild("CatchController")).Init() -- D55: мини-игра поимки (ловящий)
require(Controllers:WaitForChild("LovibumFxController")).Init() -- D55: эффекты поимки у всех рядом
require(Controllers:WaitForChild("ThrowController")).Init() -- D75: бросок вдаль с края обрыва
require(Controllers:WaitForChild("ThrowFlightController")).Init() -- D75: чужие полёты (Ловибум, след, ник)
require(Controllers:WaitForChild("TutorialController")).Init() -- D55: обучение новичка
require(Controllers:WaitForChild("OwnerTestController")).Init() -- кнопка «Тест» владельца (только DEV-место)
require(Controllers:WaitForChild("MuseumVisualController")).Init()
require(Controllers:WaitForChild("MuseumCameraController")).Init()
-- музей-небоскрёб (этап B, режим башни DEV): убранство башен по уровням детализации и окно лифта; без башен в мире
-- (обычная игра) ничего не строят
require(Controllers:WaitForChild("TowerController")).Init()
require(Controllers:WaitForChild("FloorSignalController")).Init() -- D74: сигналы редкости этажей
require(Controllers:WaitForChild("ElevatorController")).Init()

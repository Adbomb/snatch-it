-- Точка входа клиента: запускает контроллеры. Клиент только показывает и отправляет намерения.
-- Зависит от Controllers/*, Shared/LegoMaterial.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Controllers = script.Parent:WaitForChild("Controllers")

-- LEGO-пупырышки на всём Plastic (D13): замена материала действует только у того, кто её включил.
task.spawn(require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("LegoMaterial")).Apply)

require(Controllers:WaitForChild("NotifyController")).Init()
require(Controllers:WaitForChild("CarryController")).Init()
require(Controllers:WaitForChild("InventoryController")).Init()
require(Controllers:WaitForChild("MuseumPromptController")).Init()
require(Controllers:WaitForChild("PresentationController")).Init()
require(Controllers:WaitForChild("GymController")).Init()
require(Controllers:WaitForChild("TrainingController")).Init()
require(Controllers:WaitForChild("TimeController")).Init()
require(Controllers:WaitForChild("BossAnimController")).Init()
require(Controllers:WaitForChild("ZoneController")).Init()
require(Controllers:WaitForChild("OwnerTagController")).Init()
require(Controllers:WaitForChild("ItemLabelController")).Init()
require(Controllers:WaitForChild("PvpController")).Init()
require(Controllers:WaitForChild("DefenseController")).Init()
require(Controllers:WaitForChild("ShopController")).Init() -- D55: магазин Ловибумов
require(Controllers:WaitForChild("CreatureController")).Init() -- D55: живые существа
require(Controllers:WaitForChild("CatchController")).Init() -- D55: мини-игра поимки (ловящий)
require(Controllers:WaitForChild("LovibumFxController")).Init() -- D55: эффекты поимки у всех рядом
require(Controllers:WaitForChild("TutorialController")).Init() -- D55: обучение новичка
require(Controllers:WaitForChild("MuseumVisualController")).Init()
require(Controllers:WaitForChild("MuseumCameraController")).Init()

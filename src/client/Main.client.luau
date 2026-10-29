-- Точка входа клиента: запускает контроллеры. Клиент только показывает и отправляет намерения.
-- Зависит от Controllers/*, Shared/LegoMaterial.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Controllers = script.Parent:WaitForChild("Controllers")

-- LEGO-пупырышки на всём Plastic (D13): замена материала действует только у того, кто её включил.
task.spawn(require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("LegoMaterial")).Apply)

require(Controllers:WaitForChild("NotifyController")).Init()
require(Controllers:WaitForChild("CarryController")).Init()
require(Controllers:WaitForChild("StorageController")).Init()
require(Controllers:WaitForChild("MuseumPromptController")).Init()
require(Controllers:WaitForChild("PresentationController")).Init()
require(Controllers:WaitForChild("GymController")).Init()

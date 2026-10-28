-- Точка входа клиента: запускает контроллеры. Клиент только показывает и отправляет намерения.
-- Зависит от Controllers/*.

local Controllers = script.Parent:WaitForChild("Controllers")

require(Controllers:WaitForChild("NotifyController")).Init()
require(Controllers:WaitForChild("CarryController")).Init()
require(Controllers:WaitForChild("StorageController")).Init()
require(Controllers:WaitForChild("MuseumPromptController")).Init()
require(Controllers:WaitForChild("PresentationController")).Init()

-- Включает LEGO-пупырышки (D13): MaterialVariant «LegoStuds» в MaterialService и замену им всего Plastic.
-- Вариант и MaterialService.PlasticName задаёт default.project.json; этот модуль — гарантия на случай,
-- если синхронизация Rojo их не выставила (PlasticName из скриптов не пишется, только через
-- SetBaseMaterialOverride). Вызывается на сервере и на клиенте. Зависит от Config/Textures.

local MaterialService = game:GetService("MaterialService")
local RunService = game:GetService("RunService")

local Textures = require(script.Parent:WaitForChild("Config"):WaitForChild("Textures"))

local LegoMaterial = {}

function LegoMaterial.Apply()
	local cfg = Textures.LegoStuds
	local variant = MaterialService:FindFirstChild(cfg.name)
	if not variant and RunService:IsServer() then
		local created = Instance.new("MaterialVariant")
		created.Name = cfg.name
		created.BaseMaterial = Enum.Material.Plastic
		created.ColorMap = cfg.color
		created.NormalMap = cfg.normal
		created.RoughnessMap = cfg.roughness
		created.StudsPerTile = cfg.studsPerTile
		created.Parent = MaterialService
		variant = created
	elseif not variant then
		variant = MaterialService:WaitForChild(cfg.name, 10)
	end
	if variant then
		MaterialService:SetBaseMaterialOverride(Enum.Material.Plastic, cfg.name)
	end
end

return LegoMaterial

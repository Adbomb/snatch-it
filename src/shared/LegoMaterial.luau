-- Включает квадратные пупырышки (D36): три MaterialVariant из Config/Textures в MaterialService и замену первым
-- (LegoSquares) всего Plastic; два других детали ставят себе сами (MaterialVariant = имя). Варианты и
-- MaterialService.PlasticName задаёт default.project.json; этот модуль — гарантия на случай, если синхронизация
-- Rojo их не выставила (PlasticName из скриптов не пишется, только через SetBaseMaterialOverride).
-- Вызывается на сервере и на клиенте. Зависит от Config/Textures.

local MaterialService = game:GetService("MaterialService")
local RunService = game:GetService("RunService")

local Textures = require(script.Parent:WaitForChild("Config"):WaitForChild("Textures"))

local LegoMaterial = {}

local function ensure(cfg: Textures.Variant): MaterialVariant?
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
		return created
	elseif not variant then
		return MaterialService:WaitForChild(cfg.name, 10) :: MaterialVariant?
	end
	return variant :: MaterialVariant
end

function LegoMaterial.Apply()
	ensure(Textures.SquaresDeep)
	ensure(Textures.SquaresSoft)
	ensure(Textures.SquaresArt)
	if ensure(Textures.Squares) then
		MaterialService:SetBaseMaterialOverride(Enum.Material.Plastic, Textures.Squares.name)
	end
end

return LegoMaterial

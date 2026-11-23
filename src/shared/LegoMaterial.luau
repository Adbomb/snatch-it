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
		-- запасной путь: в игре свойства варианта скрипту обычно недоступны (нужны права плагина) — тогда вариант
		-- должен прийти из default.project.json; без него детали останутся с обычным Plastic, игра не падает
		local created = Instance.new("MaterialVariant")
		local ok, err = pcall(function()
			created.Name = cfg.name
			created.BaseMaterial = Enum.Material.Plastic
			created.ColorMap = cfg.color
			created.NormalMap = cfg.normal
			created.RoughnessMap = cfg.roughness
			created.StudsPerTile = cfg.studsPerTile
			created.Parent = MaterialService
		end)
		if not ok then
			warn(
				("[LegoMaterial] Нет варианта %s в MaterialService (default.project.json): %s"):format(
					cfg.name,
					tostring(err)
				)
			)
			created:Destroy()
			return nil
		end
		return created
	elseif not variant then
		return MaterialService:WaitForChild(cfg.name, 10) :: MaterialVariant?
	end
	return variant :: MaterialVariant
end

function LegoMaterial.Apply()
	ensure(Textures.SquaresDeep)
	ensure(Textures.SquaresSoft)
	ensure(Textures.SquaresItem)
	ensure(Textures.RingsD39)
	ensure(Textures.RingsD39Boss)
	ensure(Textures.SquaresBold)
	ensure(Textures.SquaresQuiet)
	ensure(Textures.SquaresFar)
	if ensure(Textures.Squares) then
		MaterialService:SetBaseMaterialOverride(Enum.Material.Plastic, Textures.Squares.name)
	end
end

return LegoMaterial

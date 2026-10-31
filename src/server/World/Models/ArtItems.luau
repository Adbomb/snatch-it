-- Произведения искусства в стиле референсов владельца (2026-10-31, блочные Roblox-персонажи): предмет собран из
-- крупных прямоугольных брусков, детали (узоры, лица, накладки) — тонкие плашки поверх, цвета плоские; рельеф
-- скруглённых квадратов даёт материал LegoSquaresArt (Config/Textures.SquaresArt), а не геометрия.
-- Начало модели — центр низа, лицо смотрит в -z; размеры в стадах (до масштаба s).
-- Зависит от World/ModelBuilder, Config/Textures.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Textures = require(ReplicatedStorage.Shared.Config.Textures)
local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)

local ART = Textures.SquaresArt.name

local ArtItems = {}

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

-- Брусок по центру и размеру с материалом предметов.
local function box(bricks, s: number, name: string, center: Vector3, size: Vector3, color: Color3)
	table.insert(bricks, ModelBuilder.Brick(size * s, center * s, color, { name = name, variant = ART }))
end

-- «Амфора с меандром» (босс 8, Common): кремовое тело, оранжевые пята, горло, венчик и ручки, пояс с «ГГ».
function ArtItems.MeanderAmphora(s: number?): { ModelBuilder.Brick }
	local k = s or 0.8
	local cream, orange, key, dark = hex("F7DDB2"), hex("F28A1E"), hex("C2560E"), hex("5C2A10")
	local b = {}
	box(b, k, "Foot", Vector3.new(0, 0.175, 0), Vector3.new(2.0, 0.35, 2.0), orange)
	box(b, k, "Stem", Vector3.new(0, 0.5, 0), Vector3.new(1.3, 0.3, 1.3), orange)
	box(b, k, "Body", Vector3.new(0, 1.5, 0), Vector3.new(2.4, 1.7, 2.4), cream)
	box(b, k, "Band", Vector3.new(0, 1.25, 0), Vector3.new(2.5, 0.5, 2.5), orange)
	box(b, k, "Shoulder", Vector3.new(0, 2.525, 0), Vector3.new(1.8, 0.35, 1.8), cream)
	box(b, k, "Neck", Vector3.new(0, 2.975, 0), Vector3.new(1.0, 0.55, 1.0), orange)
	box(b, k, "Lip", Vector3.new(0, 3.39, 0), Vector3.new(1.6, 0.28, 1.6), orange)
	box(b, k, "Mouth", Vector3.new(0, 3.545, 0), Vector3.new(0.9, 0.03, 0.9), dark)
	-- Меандр «ГГ» плашками на поясе спереди и сзади.
	for _, side in { -1, 1 } do
		local z = side * 1.27
		for _, x0 in { -0.62, 0.12 } do
			box(b, k, "Key", Vector3.new(x0 + 0.05, 1.25, z), Vector3.new(0.1, 0.36, 0.04), key)
			box(b, k, "Key", Vector3.new(x0 + 0.25, 1.38, z), Vector3.new(0.5, 0.1, 0.04), key)
			box(b, k, "Key", Vector3.new(x0 + 0.45, 1.27, z), Vector3.new(0.1, 0.12, 0.04), key)
		end
	end
	-- Ручки: нижнее плечо от тела, стойка, верхнее плечо в горло.
	for _, side in { -1, 1 } do
		box(b, k, "Handle", Vector3.new(side * 1.43, 1.85, 0), Vector3.new(0.56, 0.28, 0.42), orange)
		box(b, k, "Handle", Vector3.new(side * 1.57, 2.36, 0), Vector3.new(0.28, 1.3, 0.42), orange)
		box(b, k, "Handle", Vector3.new(side * 1.08, 2.86, 0), Vector3.new(1.26, 0.28, 0.42), orange)
	end
	return b
end

return ArtItems

-- Качалка во дворе музея (D34, D35): поле, где качаются, — тёмный резиновый пол и светящиеся плитки цвета
-- участка по краю (как на референсе), и стойка таблички «Улучшение». Огромная гантель — модель из Blender
-- (World/MeshBuilder), табло таблички — деталь участка (Util/PartBuilder). Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick
local DECOR = { collide = false, shadow = false }

local Gym = {}

-- Высота оси огромной гантели над полем: диски (радиус 5.1) не касаются поля, как на референсе.
Gym.DumbbellHeight = 6
-- Табло таблички: размер и высота центра над двором.
Gym.SignBoard = Vector3.new(9, 5, 0.6)
Gym.SignHeight = 5.2

local FLOOR = Color3.fromHex("2B2F3A")
local TILE = 2 -- сторона светящейся плитки
local TILE_STEP = 3.4 -- шаг плиток по краю поля

-- Поле: size — по X и Z, начало — центр поля на уровне двора; glow — цвет плиток (цвет участка).
function Gym.Field(size: Vector2, glow: Color3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {
		B(Vector3.new(size.X, 0.2, size.Y), Vector3.new(0, 0.1, 0), FLOOR, DECOR),
	}
	-- Плитки по краю, чуть повёрнутые (детерминированно), как разбросанные неоновые кирпичики.
	local hx, hz = size.X / 2 - TILE / 2 - 0.3, size.Y / 2 - TILE / 2 - 0.3
	local points: { Vector2 } = {}
	for x = -hx, hx + 0.01, TILE_STEP do
		table.insert(points, Vector2.new(x, -hz))
		table.insert(points, Vector2.new(x, hz))
	end
	for z = -hz + TILE_STEP, hz - TILE_STEP + 0.01, TILE_STEP do
		table.insert(points, Vector2.new(-hx, z))
		table.insert(points, Vector2.new(hx, z))
	end
	for i, p in points do
		local turn = math.rad((i * 37) % 30 - 15)
		local at = CFrame.new(p.X, 0.25, p.Y) * CFrame.Angles(0, turn, 0)
		table.insert(bricks, B(Vector3.new(TILE, 0.3, TILE), at, glow, {
			material = Enum.Material.Neon,
			collide = false,
			shadow = false,
		}))
	end
	return bricks
end

-- Стойка таблички: столб под табло и основание. Начало — точка на дворе под табло.
function Gym.SignPost(): { ModelBuilder.Brick }
	local bottom = Gym.SignHeight - Gym.SignBoard.Y / 2
	return {
		B(Vector3.new(1, bottom, 1), Vector3.new(0, bottom / 2, 0.6), Palette.Black),
		B(Vector3.new(2.4, 0.5, 2.4), Vector3.new(0, 0.25, 0.6), Palette.Black),
	}
end

return Gym

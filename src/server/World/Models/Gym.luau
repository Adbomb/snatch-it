-- Качалка во дворе музея (D34, D36): поле, где качаются, — светлый пол и плитки приглушённого цвета участка по
-- краю, и стойка таблички «Улучшение». Огромная гантель — модель из Blender (World/MeshBuilder), табло таблички —
-- деталь участка (Util/PartBuilder). Зависит от ModelBuilder, Palette.

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

local TILE = 2 -- сторона плитки
local TILE_GAP = 1.2 -- примерный зазор между плитками по краю

-- Поле: size — по X и Z, начало — центр поля на уровне травы; tile — цвет плиток (приглушённый цвет участка).
function Gym.Field(size: Vector2, tile: Color3): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {
		B(Vector3.new(size.X, 0.2, size.Y), Vector3.new(0, 0.1, 0), Palette.FieldFloor, DECOR),
	}
	-- Плитки по краю поровну, чуть повёрнутые (детерминированно), выше пола на 0.1.
	local hx, hz = size.X / 2 - TILE / 2 - 0.3, size.Y / 2 - TILE / 2 - 0.3
	local nx = math.max(2, math.floor(2 * hx / (TILE + TILE_GAP)) + 1)
	local nz = math.max(2, math.floor(2 * hz / (TILE + TILE_GAP)) + 1)
	local points: { Vector2 } = {}
	for i = 0, nx - 1 do
		local x = -hx + 2 * hx * i / (nx - 1)
		table.insert(points, Vector2.new(x, -hz))
		table.insert(points, Vector2.new(x, hz))
	end
	for i = 1, nz - 2 do
		local z = -hz + 2 * hz * i / (nz - 1)
		table.insert(points, Vector2.new(-hx, z))
		table.insert(points, Vector2.new(hx, z))
	end
	for i, p in points do
		local turn = math.rad((i * 37) % 24 - 12)
		local at = CFrame.new(p.X, 0.25, p.Y) * CFrame.Angles(0, turn, 0)
		table.insert(bricks, B(Vector3.new(TILE, 0.3, TILE), at, tile, DECOR))
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

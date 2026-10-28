-- Дом квартала: яркие стены, контрастная плоская крыша (по ней можно ходить), окна, дверь,
-- путь на крышу: ladder (деревянная лестница), crates (ящики-ступеньки), fire (пожарная лестница).
-- Начало координат — центр основания, дверь на стороне -Z, путь на крышу — на стороне +X.
-- Зависит от ModelBuilder, Palette.

local ServerScriptService = game:GetService("ServerScriptService")

local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local Palette = require(ServerScriptService.Server.World.Palette)

local B = ModelBuilder.Brick

export type Params = {
	w: number,
	d: number,
	h: number,
	wall: Color3,
	roof: Color3,
	access: string,
	roofThickness: number,
}

local WINDOW_SPACING = 6
local FLOOR_HEIGHT = 6
local CRATE = 4

local function addWindows(bricks: { ModelBuilder.Brick }, p: Params)
	-- Для каждой стороны: центр грани, направление наружу, длина грани.
	local faces = {
		{ CFrame.new(0, 0, -p.d / 2), p.w, true },
		{ CFrame.new(0, 0, p.d / 2) * CFrame.Angles(0, math.pi, 0), p.w, false },
		{ CFrame.new(p.w / 2, 0, 0) * CFrame.Angles(0, -math.pi / 2, 0), p.d, false },
		{ CFrame.new(-p.w / 2, 0, 0) * CFrame.Angles(0, math.pi / 2, 0), p.d, false },
	}
	for _, face in faces do
		local origin: CFrame, length: number, isFront: boolean = face[1], face[2], face[3]
		local columns = math.floor((length - 4) / WINDOW_SPACING)
		local y = FLOOR_HEIGHT / 2 + 1
		while y + 2.5 < p.h - 1 do
			for column = 1, columns do
				local x = (column - (columns + 1) / 2) * WINDOW_SPACING
				-- Над дверью окна первого этажа нет.
				if not (isFront and y < FLOOR_HEIGHT and math.abs(x) < WINDOW_SPACING / 2) then
					local at = origin * CFrame.new(x, y, 0)
					table.insert(
						bricks,
						B(Vector3.new(3.6, 4.2, 0.3), at * CFrame.new(0, 0, -0.1), Palette.White, { collide = false, shadow = false })
					)
					table.insert(
						bricks,
						B(Vector3.new(2.8, 3.4, 0.3), at * CFrame.new(0, 0, -0.25), Palette.Glass, {
							material = Enum.Material.SmoothPlastic,
							collide = false,
							shadow = false,
						})
					)
				end
			end
			y += FLOOR_HEIGHT
		end
	end
end

local function addAccess(bricks: { ModelBuilder.Brick }, p: Params)
	local roofTop = p.h + p.roofThickness
	local side = p.w / 2
	if p.access == "ladder" or p.access == "fire" then
		-- TrussPart: по нему персонаж лезет вверх. Чуть выше крыши, чтобы удобно было сойти.
		local height = math.ceil((roofTop + 2) / 2) * 2
		local color = if p.access == "fire" then Palette.Metal else Palette.Wood
		table.insert(bricks, B(Vector3.new(2, height, 2), Vector3.new(side + 1, height / 2, 0), color, { shape = "Truss" }))
		if p.access == "fire" then
			-- Площадки пожарной лестницы на каждом этаже (декор).
			local y = FLOOR_HEIGHT
			while y < p.h do
				table.insert(
					bricks,
					B(Vector3.new(3, 0.4, 6), Vector3.new(side + 1.5, y, 0), Palette.Metal, { collide = false, shadow = false })
				)
				table.insert(
					bricks,
					B(Vector3.new(0.3, 1.6, 6), Vector3.new(side + 3, y + 1, 0), Palette.Metal, { collide = false, shadow = false })
				)
				y += FLOOR_HEIGHT
			end
		end
	elseif p.access == "crates" then
		-- Стопки ящиков вдоль стены: каждая на CRATE выше предыдущей, последняя — почти вровень с крышей.
		local columns = math.ceil(roofTop / CRATE) - 1
		for column = 1, columns do
			local z = p.d / 2 - CRATE / 2 - (column - 1) * CRATE
			for level = 1, column do
				local color = if (column + level) % 2 == 0 then Palette.Wood else Palette.WoodDark
				table.insert(
					bricks,
					B(Vector3.new(CRATE, CRATE, CRATE), Vector3.new(side + CRATE / 2, (level - 0.5) * CRATE, z), color)
				)
			end
		end
	end
end

return function(p: Params): { ModelBuilder.Brick }
	local bricks: { ModelBuilder.Brick } = {}
	-- Цоколь, стены, крыша.
	table.insert(bricks, B(Vector3.new(p.w + 0.4, 1, p.d + 0.4), Vector3.new(0, 0.5, 0), p.wall:Lerp(Palette.Black, 0.35)))
	table.insert(bricks, B(Vector3.new(p.w, p.h, p.d), Vector3.new(0, p.h / 2, 0), p.wall))
	table.insert(bricks, B(Vector3.new(p.w, p.roofThickness, p.d), Vector3.new(0, p.h + p.roofThickness / 2, 0), p.roof))
	-- Карниз: тонкая полоса под крышей контрастным цветом.
	table.insert(
		bricks,
		B(Vector3.new(p.w + 0.6, 0.6, p.d + 0.6), Vector3.new(0, p.h - 0.3, 0), p.roof, { collide = false, shadow = false })
	)
	-- Дверь с ручкой и козырьком.
	table.insert(bricks, B(Vector3.new(4, 7, 0.4), Vector3.new(0, 3.5 + 1, -p.d / 2 - 0.2), Palette.Door, { collide = false }))
	table.insert(
		bricks,
		B(Vector3.new(0.5, 0.5, 0.4), Vector3.new(1.3, 4.5, -p.d / 2 - 0.5), Palette.Lamp, { collide = false, shadow = false })
	)
	table.insert(bricks, B(Vector3.new(6, 0.5, 2), Vector3.new(0, 8.8, -p.d / 2 - 1), p.roof, { collide = false }))
	addWindows(bricks, p)
	addAccess(bricks, p)
	return bricks
end

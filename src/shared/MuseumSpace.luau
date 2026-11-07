-- Пространство музея (D47, D52) — общее для сервера и клиента. «Внутри»: точка в главном зале (пол зала с запасом HallMargin к стенам,
-- от проёма входа до задней стены) или в открытой галерее (с уровня Galleries.Level), по высоте — HallHeight от пола
-- зала; хранилище внизу и крыша — не «внутри». «Видно»: луч от точки до цели не упирается в стену или тумбу здания
-- участка (папки Building и Showcases); детали без столкновений (декор, таблички, голограммы) лучу не мешают — сквозь
-- них видно, сквозь стены нет. Используют защита (ловушка, капкан, робот, дверь), кражи (D52: красть только изнутри
-- и с прямой видимостью экспоната) и клиент (подсказка «Украсть» — только внутри музея). plot — таблица участка
-- сервера (PlotService.Plot) или на клиенте { model, floorOrigin, level } из атрибутов модели участка.
-- Зависит от Config/GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("GameConfig"))

local cfg = GameConfig.Defense
local STEP = 0.05 -- на сколько продвинуть луч за деталь без столкновений
local MAX_HITS = 12 -- сколько деталей без столкновений луч может пройти

local MuseumSpace = {}

-- Точка мира в осях участка (начало — центр пола зала, вход в -z).
function MuseumSpace.Local(plot: any, world: Vector3): Vector3
	return plot.floorOrigin:PointToObjectSpace(world)
end

-- Точка (в осях участка) внутри главного зала или — если galleries — открытой галереи.
function MuseumSpace.InsideLocal(at: Vector3, galleries: boolean?): boolean
	if at.Y <= cfg.HallHeight.X or at.Y >= cfg.HallHeight.Y then
		return false
	end
	local hall = cfg.Hall
	if
		at.X > hall.MinX - cfg.HallMargin
		and at.X < hall.MaxX + cfg.HallMargin
		and at.Z > cfg.Door.At.Z
		and at.Z < hall.MaxZ + cfg.HallMargin
	then
		return true
	end
	local g = cfg.Galleries
	local x = math.abs(at.X)
	return galleries == true
		and x > g.MinX
		and x < g.MaxX + cfg.HallMargin
		and at.Z > g.MinZ - cfg.HallMargin
		and at.Z < g.MaxZ + cfg.HallMargin
end

-- Галереи открыты на уровне музея участка.
function MuseumSpace.HasGalleries(plot: any): boolean
	return (plot.level or 1) >= cfg.Galleries.Level
end

-- Мировая точка внутри музея участка (зал или открытая галерея).
function MuseumSpace.Inside(plot: any, world: Vector3): boolean
	return MuseumSpace.InsideLocal(MuseumSpace.Local(plot, world), MuseumSpace.HasGalleries(plot))
end

-- Из from видно to: луч не упирается в деталь здания или постамент со столкновениями. target — цель (деталь, её
-- потомки тоже): дойти до неё — значит видно.
function MuseumSpace.Sees(plot: any, from: Vector3, to: Vector3, target: Instance?): boolean
	local list: { Instance } = {}
	for _, name in { "Building", "Showcases" } do
		local folder = plot.model:FindFirstChild(name)
		if folder then
			table.insert(list, folder)
		end
	end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = list
	local origin = from
	for _ = 1, MAX_HITS do
		local direction = to - origin
		if direction.Magnitude < STEP then
			return true
		end
		local hit = workspace:Raycast(origin, direction, params)
		if not hit then
			return true
		end
		local part = hit.Instance
		if target and (part == target or part:IsDescendantOf(target)) then
			return true
		end
		if part:IsA("BasePart") and part.CanCollide then
			return false
		end
		origin = hit.Position + direction.Unit * STEP
	end
	return false
end

return MuseumSpace

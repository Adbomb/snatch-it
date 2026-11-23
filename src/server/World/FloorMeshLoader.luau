--!strict
-- Шаблоны мешей этажей музея-небоскрёба: один раз грузит меши из Floors/FloorMeshes (AssetService) и кладёт
-- MeshPart-шаблоны в ReplicatedStorage.FloorMeshes (имя детали = имя шаблона). Клиент клонирует их в убранство
-- (Floors/FloorBuilder, кирпич с полем mesh); сам MeshId из скрипта задать нельзя. Когда всё загружено — атрибут
-- папки Ready = true (клиент ждёт его перед сборкой вида, Floors.WaitMeshes). Меш, который не загрузился после
-- повторов, пропускается с предупреждением: этаж соберётся без этой детали.
-- Шаблоны без столкновений (коробка), лучей и теней: столкновения этажа — невидимый каркас сервера.
-- Зависит от AssetService, Shared/Floors/FloorMeshes.

local AssetService = game:GetService("AssetService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local FloorMeshes = require(ReplicatedStorage.Shared.Floors.FloorMeshes)

local FOLDER = "FloorMeshes"
local RETRIES = 3

local FloorMeshLoader = {}

local started = false

local function load(name: string, id: string, folder: Folder)
	for attempt = 1, RETRIES do
		local ok, result = pcall(function()
			return AssetService:CreateMeshPartAsync(Content.fromUri(id), {
				CollisionFidelity = Enum.CollisionFidelity.Box,
				RenderFidelity = Enum.RenderFidelity.Automatic,
			})
		end)
		if ok and result then
			local part = result :: MeshPart
			part.Name = name
			part.Anchored = true
			part.CanCollide = false
			part.CanQuery = false
			part.CanTouch = false
			part.CastShadow = false
			part.Parent = folder
			return
		end
		if attempt == RETRIES then
			warn(("[FloorMeshLoader] Меш %s (%s) не загрузился: %s"):format(name, id, tostring(result)))
		else
			task.wait(1)
		end
	end
end

-- Запускает загрузку (не ждёт конца). Повторный вызов ничего не делает.
function FloorMeshLoader.Start()
	if started then
		return
	end
	started = true
	local folder = Instance.new("Folder")
	folder.Name = FOLDER
	folder:SetAttribute("Ready", false)
	folder.Parent = ReplicatedStorage
	local pending = 0
	for _, theme in FloorMeshes do
		for name, info in theme.parts do
			pending += 1
			task.spawn(function()
				load(name, info.mesh, folder)
				pending -= 1
				if pending == 0 then
					folder:SetAttribute("Ready", true)
				end
			end)
		end
	end
	if pending == 0 then
		folder:SetAttribute("Ready", true)
	end
end

return FloorMeshLoader

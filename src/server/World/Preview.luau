-- Предпросмотр карты в режиме редактирования: собирает город и участки в workspace.__Preview,
-- чтобы облетать их камерой без Play. Вызывается через MCP (FreshRequire берёт свежий код, а не кэш):
--   local World = game.ServerScriptService.Server.World
--   require(World.FreshRequire)(World.Preview).Build()   -- собрать
--   require(World.FreshRequire)(World.Preview).Clear()   -- убрать
-- Папка Archivable = false: в сохранение места и в копию для Play она не попадает;
-- Main.server на всякий случай удаляет её при старте.
-- Зависит от WorldBuilder, MeshBuilder, ModelBuilder, MapLayout, Util/PartBuilder, GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local PartBuilder = require(ServerScriptService.Server.Util.PartBuilder)
local MapLayout = require(ServerScriptService.Server.World.MapLayout)
local MeshBuilder = require(ServerScriptService.Server.World.MeshBuilder)
local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local WorldBuilder = require(ServerScriptService.Server.World.WorldBuilder)

local FOLDER_NAME = "__Preview"

local Preview = {}

Preview.FolderName = FOLDER_NAME

function Preview.Clear()
	local existing = workspace:FindFirstChild(FOLDER_NAME)
	if existing then
		existing:Destroy()
	end
end

function Preview.Build(): string
	Preview.Clear()
	local root = Instance.new("Folder")
	root.Name = FOLDER_NAME
	root.Archivable = false

	ModelBuilder.SetTemplateParent(nil)
	MeshBuilder.Preload()
	WorldBuilder.Build(root)
	local plots = Instance.new("Folder")
	plots.Name = "Plots"
	plots.Parent = root
	for index = 1, GameConfig.World.PlotCount do
		PartBuilder.BuildPlot(index, MapLayout.PlotCFrame(index), GameConfig.Museum.SlotsByLevel[1], plots)
	end
	local points = Instance.new("Folder")
	points.Name = "ArtSlots"
	points.Parent = root
	for _, spec in MapLayout.ArtSlotPoints() do
		PartBuilder.MakePart({
			name = spec.name,
			size = Vector3.new(2, 0.2, 2),
			cframe = spec.cframe * CFrame.new(0, 0.1, 0),
			color = Color3.fromRGB(255, 210, 0),
			transparency = 0.3,
			canCollide = false,
			parent = points,
		})
	end

	root.Parent = workspace
	return ("Предпросмотр собран: %d частей (бюджет %d)"):format(ModelBuilder.CountParts(root), GameConfig.World.MaxParts)
end

return Preview

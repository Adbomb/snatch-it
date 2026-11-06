-- Участки-музеи (5 в ряд, D35): строит их при старте, выдаёт при входе, освобождает при выходе.
-- Хранит владельца участка на сервере; круглое фото и ник владельца над входом рисует клиент по атрибутам (D41).
-- Музей D48-C уровня владельца (здание, галереи, открытые места; у свободного участка — уровень 1); шаблон обстановки
-- хранилища для клиента владельца. Во дворе — огромная гантель уровня владельца (D34), у свободного участка её нет.
-- Атрибуты модели участка для клиента: OwnerUserId, OwnerName, MuseumLevel, FloorOrigin, DumbbellLevel (0 — нет).
-- Зависит от Util/PartBuilder, World/MapLayout, World/MeshBuilder, World/MuseumVisual, GameConfig, Util/Log.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Log = require(ServerScriptService.Server.Util.Log)
local MapLayout = require(ServerScriptService.Server.World.MapLayout)
local MeshBuilder = require(ServerScriptService.Server.World.MeshBuilder)
local PartBuilder = require(ServerScriptService.Server.Util.PartBuilder)
local MuseumVisual = require(ServerScriptService.Server.World.MuseumVisual)

export type Plot = {
	index: number,
	owner: Player?,
	model: Model,
	showcases: { [number]: BasePart },
	exhibits: Folder,
	chest: BasePart,
	floorOrigin: CFrame,
	accent: Color3,
	level: number,
	fieldCFrame: CFrame,
	dumbbellCFrame: CFrame,
	signBoard: BasePart,
	dumbbell: Model?,
}

local plots: { Plot } = {}
local plotByPlayer: { [Player]: Plot } = {}

local PlotService = {}

function PlotService.Init(world: Folder)
	local folder = Instance.new("Folder")
	folder.Name = "Plots"
	folder.Parent = world
	MuseumVisual.PublishVaultDecor() -- обстановку хранилища видит только владелец (копия на его клиенте)
	local count = GameConfig.World.PlotCount
	for index = 1, count do
		local parts = PartBuilder.BuildPlot(index, MapLayout.PlotCFrame(index), folder)
		plots[index] = {
			index = index,
			owner = nil,
			model = parts.model,
			showcases = parts.showcases,
			exhibits = parts.exhibits,
			chest = parts.chest,
			floorOrigin = parts.floorOrigin,
			accent = parts.accent,
			level = 1,
			fieldCFrame = parts.fieldCFrame,
			dumbbellCFrame = parts.dumbbellCFrame,
			signBoard = parts.signBoard,
		}
		parts.model:SetAttribute("OwnerName", "")
		parts.model:SetAttribute("FloorOrigin", parts.floorOrigin) -- оси участка для расстановки защиты (D46)
		parts.model:SetAttribute("DumbbellLevel", 0)
	end
end

function PlotService.GetPlots(): { Plot }
	return plots
end

function PlotService.GetPlotOf(player: Player): Plot?
	return plotByPlayer[player]
end

-- Выдаёт первый свободный участок. nil — свободных нет.
function PlotService.Assign(player: Player): Plot?
	if plotByPlayer[player] then
		return plotByPlayer[player]
	end
	for _, plot in plots do
		if plot.owner == nil then
			plot.owner = player
			plotByPlayer[player] = plot
			plot.model:SetAttribute("OwnerUserId", player.UserId)
			plot.model:SetAttribute("OwnerName", player.DisplayName)
			Log.Debug("PlotService", ("%s получил участок %d"):format(player.Name, plot.index))
			return plot
		end
	end
	Log.Warn("PlotService", "Нет свободного участка для " .. player.Name)
	return nil
end

-- Показывает музей уровня level на участке (D48-C): здание, галереи с уровня Gallery.Level, открытые места.
-- Если уровень тот же — ничего не меняется.
function PlotService.ShowLevel(plot: Plot, level: number)
	if plot.level == level then
		return
	end
	plot.level = level
	PartBuilder.SetLevel(plot, level)
end

-- Огромная гантель уровня level во дворе участка (nil — убрать). Модель меняется сразу, видна всем.
function PlotService.ShowDumbbell(plot: Plot, level: number?)
	if plot.dumbbell then
		plot.dumbbell:Destroy()
		plot.dumbbell = nil
	end
	plot.model:SetAttribute("DumbbellLevel", level or 0)
	if level then
		plot.dumbbell = MeshBuilder.Build(("Dumbbell%02d"):format(level), plot.dumbbellCFrame, plot.model, {
			accent = plot.accent,
			name = "GiantDumbbell",
		})
	end
end

function PlotService.Release(player: Player)
	local plot = plotByPlayer[player]
	if not plot then
		return
	end
	plotByPlayer[player] = nil
	plot.owner = nil
	plot.model:SetAttribute("OwnerUserId", 0)
	plot.model:SetAttribute("OwnerName", "")
	PlotService.ShowDumbbell(plot, nil)
	PlotService.ShowLevel(plot, 1)
	Log.Debug("PlotService", ("Участок %d освобождён"):format(plot.index))
end

return PlotService

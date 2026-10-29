-- 8 участков-музеев по кругу: строит их при старте, выдаёт при входе, освобождает при выходе.
-- Хранит владельца участка на сервере и пишет его имя на табличке (DESIGN.md §3). Здание — модель уровня
-- музея владельца (D33), у свободного участка — руины (уровень 1).
-- Зависит от Util/PartBuilder, World/MapLayout, GameConfig, Util/Log.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Log = require(ServerScriptService.Server.Util.Log)
local MapLayout = require(ServerScriptService.Server.World.MapLayout)
local PartBuilder = require(ServerScriptService.Server.Util.PartBuilder)

export type Plot = {
	index: number,
	owner: Player?,
	model: Model,
	showcases: { [number]: BasePart },
	exhibits: Folder,
	signLabel: TextLabel,
	chest: BasePart,
	floorOrigin: CFrame,
	accent: Color3,
	level: number,
}

local FREE_SIGN_TEXT = "СВОБОДНЫЙ УЧАСТОК"

local plots: { Plot } = {}
local plotByPlayer: { [Player]: Plot } = {}

local PlotService = {}

function PlotService.Init(world: Folder)
	local folder = Instance.new("Folder")
	folder.Name = "Plots"
	folder.Parent = world
	local count = GameConfig.World.PlotCount
	local slotCount = GameConfig.Museum.SlotsByLevel[1]
	for index = 1, count do
		local parts = PartBuilder.BuildPlot(index, MapLayout.PlotCFrame(index), slotCount, folder)
		parts.signLabel.Text = FREE_SIGN_TEXT
		plots[index] = {
			index = index,
			owner = nil,
			model = parts.model,
			showcases = parts.showcases,
			exhibits = parts.exhibits,
			signLabel = parts.signLabel,
			chest = parts.chest,
			floorOrigin = parts.floorOrigin,
			accent = parts.accent,
			level = 1,
		}
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
			plot.signLabel.Text = "МУЗЕЙ " .. player.DisplayName
			Log.Debug("PlotService", ("%s получил участок %d"):format(player.Name, plot.index))
			return plot
		end
	end
	Log.Warn("PlotService", "Нет свободного участка для " .. player.Name)
	return nil
end

-- Показывает здание музея уровня level на участке (если уровень другой — модель меняется).
function PlotService.ShowLevel(plot: Plot, level: number)
	if plot.level == level then
		return
	end
	plot.level = level
	PartBuilder.SetBuilding(plot.model, plot.floorOrigin, plot.accent, level)
end

function PlotService.Release(player: Player)
	local plot = plotByPlayer[player]
	if not plot then
		return
	end
	plotByPlayer[player] = nil
	plot.owner = nil
	plot.model:SetAttribute("OwnerUserId", 0)
	plot.signLabel.Text = FREE_SIGN_TEXT
	PlotService.ShowLevel(plot, 1)
	Log.Debug("PlotService", ("Участок %d освобождён"):format(plot.index))
end

return PlotService

-- Участки-музеи (5 в ряд, D35): строит их при старте, выдаёт при входе, освобождает при выходе.
-- Хранит владельца участка на сервере; круглое фото и ник владельца над входом рисует клиент по атрибутам (D41).
-- Музей D48-C уровня владельца (здание, галереи, открытые места; у свободного участка — уровень 1); шаблон обстановки
-- хранилища для клиента владельца. Огромной гантели во дворе нет (D51: гантель — в руке у тренирующегося,
-- GymService); уровень гантели владельца — атрибут для таблички «Улучшение».
-- Атрибуты модели участка для клиента: OwnerUserId, OwnerName, MuseumLevel, FloorOrigin, DumbbellLevel (0 — нет).
-- Зависит от Util/PartBuilder, World/MapLayout, World/MuseumVisual, GameConfig, Util/Log.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Log = require(ServerScriptService.Server.Util.Log)
local MapLayout = require(ServerScriptService.Server.World.MapLayout)
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
	signBoard: BasePart,
	tower: boolean?, -- этап B: на участке башня (режим башни DEV), здание и постаменты сняты
	parked: { Instance }?, -- снятые здание и постаменты (вернуть при выходе из режима башни)
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
	if plot.tower then
		-- режим башни (этап B): уровень музея запоминается, здание не строится (вернётся при выходе из режима)
		plot.model:SetAttribute("MuseumLevel", level)
		return
	end
	PartBuilder.SetLevel(plot, level)
end

-- Режим башни на участке (этап B, только DEV — решает TowerService): on — здание D48-C и постаменты снимаются из мира
-- и хранятся (двор, сундук, табличка и точка пола остаются); off — возвращаются и здание пересобирается по уровню.
function PlotService.UseTower(plot: Plot, on: boolean)
	if on == (plot.tower == true) then
		return
	end
	local model = plot.model
	if on then
		plot.tower = true
		plot.parked = {}
		for _, name in { "Building", "Showcases" } do
			local child = model:FindFirstChild(name)
			if child then
				child.Parent = nil
				table.insert(plot.parked :: { Instance }, child)
			end
		end
		model:SetAttribute("TowerMode", true)
	else
		plot.tower = nil
		for _, child in plot.parked or {} do
			child.Parent = model
		end
		plot.parked = nil
		PartBuilder.SetLevel(plot, plot.level)
		model:SetAttribute("TowerMode", nil)
	end
end

-- Уровень гантели владельца участка (nil — участок свободен): атрибут DumbbellLevel для таблички «Улучшение».
function PlotService.ShowDumbbell(plot: Plot, level: number?)
	plot.model:SetAttribute("DumbbellLevel", level or 0) -- модели во дворе нет (D51), только уровень для таблички
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

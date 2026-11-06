-- Подземное хранилище музея D48-C — только для владельца (решение 2 D48-C, 2026-11-06). Отдельной неуязвимости и
-- Safe Zone нет: доступ ограничивают архитектура и сервер.
-- • Барьер: невидимая стенка в портале павильона (группа столкновений VaultBarrier_<участок>). Персонажа владельца
--   сервер переводит в группу VaultOwner_<участок>, которая с барьером своего участка не сталкивается; все
--   остальные (и владельцы других музеев) упираются в барьер.
-- • Страховка: раз в CheckSeconds сервер проверяет объём хранилища и павильона; чужой персонаж внутри (телепорт,
--   застревание, смена владельца) переносится к порталу павильона.
-- • Терминал (окно «Инвентарь») и центр безопасности (окно «Защита») — подсказки; сервер проверяет владельца и
--   расстояние и только тогда просит клиент открыть окно (Remotes.OpenWindow).
-- Зависит от GameConfig, Config/MuseumLayout, PlotService, Util/Prompts, Util/Notify, Util/Validate, Util/RateLimiter,
-- Util/Log, Remotes.

local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local MuseumLayout = require(ReplicatedStorage.Shared.Config.MuseumLayout)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local PlotService = require(ServerScriptService.Server.Services.PlotService)
local Log = require(ServerScriptService.Server.Util.Log)
local Notify = require(ServerScriptService.Server.Util.Notify)
local Prompts = require(ServerScriptService.Server.Util.Prompts)
local RateLimiter = require(ServerScriptService.Server.Util.RateLimiter)
local Validate = require(ServerScriptService.Server.Util.Validate)

local cfg = GameConfig.Museum.Vault
local L = MuseumLayout
local DEFAULT_GROUP = "Default"

local openLimiter = RateLimiter.new(cfg.OpensPerSecond)
local noticeAt: { [any]: number } = {}

local VaultService = {}

local function barrierGroup(index: number): string
	return "VaultBarrier_" .. index
end

local function ownerGroup(index: number): string
	return "VaultOwner_" .. index
end

-- Объёмы «только для владельца» в осях участка: хранилище под залом и павильон за порталом (x0, x1, y0, y1, z0, z1).
local function volumes(): { { number } }
	local hall, vault, pav = L.Hall, L.Vault, L.Pavilion
	return {
		{ -hall.HalfWidth, hall.HalfWidth, vault.Floor - hall.Slab, -0.5, hall.Front, hall.Back },
		{ -pav.HalfX + 0.6, pav.HalfX - 0.6, -0.5, pav.Height, pav.Z0 + 0.6, pav.Z1 - 0.6 },
	}
end
local VOLUMES = volumes()

-- Точка участка at — внутри хранилища или павильона.
function VaultService.IsInside(at: Vector3): boolean
	for _, v in VOLUMES do
		if at.X > v[1] and at.X < v[2] and at.Y > v[3] and at.Y < v[4] and at.Z > v[5] and at.Z < v[6] then
			return true
		end
	end
	return false
end

-- Куда переносить чужого: перед порталом павильона, лицом ко входу в музей.
local function exitCFrame(plot: PlotService.Plot): CFrame
	local at = Vector3.new(0, cfg.ExitHeight, L.Pavilion.Z0 - cfg.ExitDistance)
	return plot.floorOrigin * CFrame.new(at) * CFrame.Angles(0, math.pi, 0)
end

-- Группа столкновений всех деталей персонажа.
local function setGroup(character: Instance?, group: string)
	if not character then
		return
	end
	for _, part in character:GetDescendants() do
		if part:IsA("BasePart") then
			part.CollisionGroup = group
		end
	end
end

-- Группа персонажа игрока: владелец участка — свой VaultOwner_<участок>, остальные — Default.
local function groupOf(player: any): string
	local plot = PlotService.GetPlotOf(player)
	return if plot then ownerGroup(plot.index) else DEFAULT_GROUP
end

local function applyGroup(player: any)
	setGroup(player.Character, groupOf(player))
end

local function watchCharacter(player: Player, character: Model)
	setGroup(character, groupOf(player))
	character.DescendantAdded:Connect(function(part)
		if part:IsA("BasePart") then
			part.CollisionGroup = groupOf(player)
		end
	end)
end

-- Владелец участка сменился (вход, выход): группа персонажа нового владельца. Вызывает PlayerSession после
-- выдачи участка; при выходе персонаж уходит вместе с игроком.
function VaultService.OnPlotAssigned(player: any)
	applyGroup(player)
end

-- Все, кто может оказаться в музее: игроки сервера и владельцы участков (в тестах — тестовые игроки).
local function everyone(): { any }
	local list = {}
	local seen = {}
	for _, player in Players:GetPlayers() do
		seen[player] = true
		table.insert(list, player)
	end
	for _, plot in PlotService.GetPlots() do
		if plot.owner and not seen[plot.owner] then
			table.insert(list, plot.owner)
		end
	end
	return list
end

-- Один такт проверки: чужой в хранилище или павильоне — к порталу. Возвращает число переносов (для тестов).
local function tick(): number
	local moved = 0
	local list = everyone()
	for _, plot in PlotService.GetPlots() do
		for _, player in list do
			if player ~= plot.owner then
				local root = Validate.GetLiveRoot(player)
				if root and VaultService.IsInside(plot.floorOrigin:PointToObjectSpace(root.Position)) then
					root.CFrame = exitCFrame(plot)
					root.AssemblyLinearVelocity = Vector3.zero
					moved += 1
					local now = os.clock()
					if now - (noticeAt[player] or 0) >= cfg.NoticeCooldown then
						noticeAt[player] = now
						Notify.Send(
							player,
							"Хранилище — только для владельца музея",
							"Stop"
						)
					end
				end
			end
		end
	end
	return moved
end

-- Подсказка «Инвентарь» / «Защита» в хранилище: владелец рядом — клиент открывает окно.
local function tryOpen(player: any, plot: PlotService.Plot, anchor: BasePart, window: string)
	if not openLimiter:Allow(player) then
		return
	end
	if plot.owner ~= player then
		Notify.Send(player, "Это чужое хранилище", "Stop")
		return
	end
	if not Validate.IsNear(player, anchor.Position, cfg.PromptDistance) then
		return
	end
	Remotes.FireClient(Remotes.Names.OpenWindow, player, window)
end

local function anchorPart(plot: PlotService.Plot, name: string, at: Vector3, size: Vector3): BasePart
	local part = Instance.new("Part")
	part.Name = name
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.Transparency = 1
	part.Size = size
	part.CFrame = plot.floorOrigin * CFrame.new(at)
	part.Parent = plot.model
	return part
end

function VaultService.Init()
	for _, plot in PlotService.GetPlots() do
		local barrier, owner = barrierGroup(plot.index), ownerGroup(plot.index)
		for _, group in { barrier, owner } do
			if not PhysicsService:IsCollisionGroupRegistered(group) then
				PhysicsService:RegisterCollisionGroup(group)
			end
		end
		PhysicsService:CollisionGroupSetCollidable(owner, barrier, false)

		-- Барьер в портале павильона (решётку видно; проходит только владелец).
		local pav, stair = L.Pavilion, L.Stair
		local wall = anchorPart(
			plot,
			"VaultBarrier",
			Vector3.new(0, cfg.BarrierHeight / 2, pav.Z0 + 0.3),
			Vector3.new(stair.HalfWidth * 2, cfg.BarrierHeight, 0.4)
		)
		wall.CanCollide = true
		wall.CollisionGroup = barrier

		-- Терминал инвентаря у торца лестницы и центр безопасности у правой стены хранилища.
		local floor = L.Vault.Floor
		local terminal =
			anchorPart(plot, "VaultTerminal", Vector3.new(0, floor + 2.5, stair.TopZ - 1.7), Vector3.new(4.4, 1, 1.4))
		local security = anchorPart(plot, "VaultSecurity", Vector3.new(14.5, floor + 2.5, -4), Vector3.new(2.2, 1, 7.6))
		Prompts.Create(terminal, "VaultInventory", "Терминал хранилища", cfg.PromptDistance).Triggered
			:Connect(function(player)
				tryOpen(player, plot, terminal, "Inventory")
			end)
		Prompts.Create(security, "VaultDefense", "Центр безопасности", cfg.PromptDistance).Triggered
			:Connect(function(player)
				tryOpen(player, plot, security, "Defense")
			end)
	end

	local function onPlayer(player: Player)
		player.CharacterAdded:Connect(function(character)
			watchCharacter(player, character)
		end)
		if player.Character then
			watchCharacter(player, player.Character)
		end
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, player in Players:GetPlayers() do
		onPlayer(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		noticeAt[player] = nil
	end)

	task.spawn(function()
		while true do
			task.wait(cfg.CheckSeconds)
			local ok, err = pcall(tick)
			if not ok then
				Log.Warn("VaultService", "проверка хранилищ: " .. tostring(err))
			end
		end
	end)
end

-- Для серверных тестов: такт проверки, группа персонажа, открытие окна.
VaultService.Handlers = {
	Tick = tick,
	GroupOf = groupOf,
	ApplyGroup = applyGroup,
	Open = tryOpen,
	BarrierGroup = barrierGroup,
	OwnerGroup = ownerGroup,
}

return VaultService

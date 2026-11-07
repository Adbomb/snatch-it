-- Качалка (D31, D34, D35, D51): у каждого участка своё поле во дворе. Владелец, который стоит в поле своего двора
-- с пустыми руками, живой и не в нокауте, тренируется: у него атрибут Training и гантель своего уровня в правой руке
-- (World/HandDumbbell, видна всем; подъём рисует клиент, Controllers/TrainingController). Состояние проверяется
-- каждые GameConfig.Gym.StateCheck секунд и сразу при подъёме экспоната и нокауте; вышел, взял экспонат, нокаут,
-- смерть — гантель пропадает. Сила = сила гантели × (1 + сила музея, D31) — раз в TickSeconds по общему серверному
-- времени (клиенты по нему же ставят верх подъёма в момент начисления). Чужой в поле — только подсказка «Это гантель
-- игрока X». Улучшение гантели за монеты — подсказка «Улучшить гантель» и кнопка на табличке своего двора; сервер
-- сам проверяет владельца, расстояние, уровень и монеты. Сила, монеты и уровень гантели — в профиле; для
-- интерфейса — атрибуты игрока Strength, Coins, DumbbellLevel, Training.
-- Зависит от DataService, PlotService, CarryService, Config/Items, GameConfig, Remotes, NumberFormat,
-- World/HandDumbbell, Util/Prompts, Util/Notify, Util/RateLimiter, Util/Validate.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local NumberFormat = require(ReplicatedStorage.Shared.NumberFormat)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local DataService = require(Server.Services.DataService)
local PlotService = require(Server.Services.PlotService)
local HandDumbbell = require(Server.World.HandDumbbell)
local Notify = require(Server.Util.Notify)
local Prompts = require(Server.Util.Prompts)
local RateLimiter = require(Server.Util.RateLimiter)
local Validate = require(Server.Util.Validate)

local Dumbbell = GameConfig.Progression.Dumbbell
local MAX_LEVEL = #Dumbbell.Power

local upgradeLimiter = RateLimiter.new(GameConfig.Gym.UpgradesPerSecond)
local lastHint: { [Player]: number } = {}
local training: { [Player]: boolean } = {} -- кто сейчас качается (атрибут Training и гантель в руке)

local GymService = {}

-- Атрибуты игрока для интерфейса (табличка, «+N», надписи силы и монет) из профиля.
function GymService.SyncAttributes(player: Player)
	local data = DataService.GetData(player)
	if data then
		player:SetAttribute("Strength", data.strength)
		player:SetAttribute("Coins", data.coins)
		player:SetAttribute("DumbbellLevel", data.dumbbellLevel)
	end
end

-- Сила музея (D31): сумма бонусов экспонатов на витринах — редкость × вид (лучший из модификаторов), потолок cap.
function GymService.MuseumPower(player: Player): number
	local data = DataService.GetData(player)
	if not data then
		return 0
	end
	local cfg = GameConfig.Progression.MuseumPower
	local total = 0
	for _, record in data.items do
		local def = Items[record.id]
		if record.place == "slot" and def then
			local variant = 1
			for _, mod in record.mods or {} do
				variant = math.max(variant, cfg.Variant[mod] or 1)
			end
			total += (cfg.Rarity[def.rarity] or 0) * variant
		end
	end
	return math.min(total, cfg.cap)
end

-- Участок, в поле которого стоит точка (или nil).
local function fieldAt(position: Vector3): PlotService.Plot?
	local size = GameConfig.Gym.FieldSize
	for _, plot in PlotService.GetPlots() do
		local p = plot.fieldCFrame:PointToObjectSpace(position)
		local inside = math.abs(p.X) <= size.X / 2 and math.abs(p.Z) <= size.Y / 2
		if inside and p.Y >= 0 and p.Y <= GameConfig.Gym.FieldHeight then
			return plot
		end
	end
	return nil
end

local function train(player: Player)
	local data = DataService.GetData(player)
	if not data then
		return
	end
	local gain = Dumbbell.Power[data.dumbbellLevel] * (1 + GymService.MuseumPower(player))
	local strength = DataService.AddStrength(player, gain)
	if strength then
		player:SetAttribute("Strength", strength)
		CarryService.RefreshSpeed(player)
		Remotes.FireClient(Remotes.Names.GymGain, player, gain)
	end
end

local function hintGuest(player: Player, owner: Player)
	local now = os.clock()
	if (lastHint[player] or -math.huge) + GameConfig.Gym.GuestHintCooldown > now then
		return
	end
	lastHint[player] = now
	Notify.Send(
		player,
		("Это гантель игрока %s — качаться можно только на своей"):format(
			owner.DisplayName
		)
	)
end

-- Может ли игрок качаться сейчас и в чьём поле стоит: владелец в поле своего двора, живой (GetLiveRoot), руки
-- пустые, не в нокауте.
local function stateOf(player: Player): (boolean, PlotService.Plot?)
	local root = Validate.GetLiveRoot(player)
	local plot = root and fieldAt(root.Position)
	if not plot or plot.owner ~= player then
		return false, plot
	end
	local free = player:GetAttribute("CarryingItemId") == nil and player:GetAttribute("Knocked") ~= true
	return free, plot
end

-- Тренировка видна: атрибут Training и гантель уровня в руке; не тренируется — ни того ни другого.
local function setTraining(player: Player, on: boolean)
	local character = player.Character
	local data = DataService.GetData(player)
	if on and character and data then
		HandDumbbell.Attach(character, data.dumbbellLevel)
	else
		on = false
		HandDumbbell.Remove(character)
	end
	training[player] = if on then true else nil
	if player:GetAttribute("Training") ~= (if on then true else nil) then
		player:SetAttribute("Training", if on then true else nil)
	end
end

local function refresh(player: Player): (boolean, PlotService.Plot?)
	local on, plot = stateOf(player)
	setTraining(player, on)
	return on, plot
end

-- Такт качания одного игрока: владелец в своём поле с пустыми руками качается, гость — получает подсказку.
local function tickPlayer(player: Player)
	local on, plot = refresh(player)
	if on then
		train(player)
	elseif plot and plot.owner and plot.owner ~= player then
		hintGuest(player, plot.owner)
	end
end

local function tick()
	for _, player in Players:GetPlayers() do
		tickPlayer(player)
	end
end

-- Сразу прекратить или начать по событиям (экспонат в руках, нокаут, смерть), не дожидаясь проверки по времени.
local function watch(player: Player)
	for _, attribute in { "CarryingItemId", "Knocked" } do
		player:GetAttributeChangedSignal(attribute):Connect(function()
			refresh(player)
		end)
	end
	local function onCharacter(character: Model)
		local humanoid = character:WaitForChild("Humanoid", 10)
		if humanoid and humanoid:IsA("Humanoid") then
			humanoid.Died:Connect(function()
				setTraining(player, false)
			end)
		end
	end
	player.CharacterAdded:Connect(onCharacter)
	player.CharacterRemoving:Connect(function()
		training[player] = nil
		player:SetAttribute("Training", nil)
	end)
	if player.Character then
		task.spawn(onCharacter, player.Character)
	end
end

-- Улучшение гантели у таблички plot. Все проверки здесь: владелец, расстояние, уровень, монеты.
local function upgrade(player: Player, plot: PlotService.Plot?)
	if not plot then
		return
	end
	if plot.owner ~= player then
		local owner = plot.owner
		local text = if owner
			then ("Это гантель игрока %s"):format(owner.DisplayName)
			else "Это свободный участок"
		Notify.Send(player, text, "Stop")
		return
	end
	if not Validate.IsNear(player, plot.signBoard.Position, GameConfig.Gym.SignDistance) then
		Notify.Send(
			player,
			"Подойдите к табличке «Улучшение» у своего музея",
			"Stop"
		)
		return
	end
	local data = DataService.GetData(player)
	if not data then
		return
	end
	local level = data.dumbbellLevel
	if level >= MAX_LEVEL then
		Notify.Send(player, "Гантель уже максимального уровня", "Info")
		return
	end
	local price = Dumbbell.Prices[level]
	if data.coins < price then
		Notify.Send(
			player,
			("Не хватает монет: нужно $%s"):format(NumberFormat.Short(price)),
			"Stop"
		)
		return
	end
	if not DataService.UpgradeDumbbell(player, price, MAX_LEVEL) then
		return
	end
	GymService.SyncAttributes(player)
	PlotService.ShowDumbbell(plot, level + 1)
	if training[player] and player.Character then
		HandDumbbell.Attach(player.Character, level + 1) -- в руке — гантель нового уровня
	end
	DataService.RequestSave(player)
	Notify.Send(
		player,
		("Гантель улучшена: %s (уровень %d)"):format(Dumbbell.Names[level + 1], level + 1),
		"Go"
	)
end

-- Игрок загружен и получил участок: атрибуты, уровень гантели участка (для таблички), скорость от силы.
function GymService.OnPlayerLoaded(player: Player, plot: PlotService.Plot)
	GymService.SyncAttributes(player)
	PlotService.ShowDumbbell(plot, DataService.GetData(player).dumbbellLevel)
	CarryService.RefreshSpeed(player)
end

function GymService.Init()
	for _, plot in PlotService.GetPlots() do
		local prompt = Prompts.Create(plot.signBoard, "Upgrade", "Гантель", GameConfig.Gym.SignDistance)
		prompt.Triggered:Connect(function(player)
			if upgradeLimiter:Allow(player) then
				upgrade(player, plot)
			end
		end)
	end
	Remotes.Get(Remotes.Names.GymUpgrade).OnServerEvent:Connect(function(player)
		if upgradeLimiter:Allow(player) then
			upgrade(player, PlotService.GetPlotOf(player))
		end
	end)
	Players.PlayerAdded:Connect(watch)
	for _, player in Players:GetPlayers() do
		watch(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		lastHint[player] = nil
		training[player] = nil
	end)
	-- гантель в руке появляется и пропадает быстро (вошёл в поле, вышел)
	task.spawn(function()
		while true do
			task.wait(GameConfig.Gym.StateCheck)
			for _, player in Players:GetPlayers() do
				refresh(player)
			end
		end
	end)
	-- сила — на границах TickSeconds общего серверного времени: клиенты по нему же ставят верх подъёма гантели
	task.spawn(function()
		local period = GameConfig.Gym.TickSeconds
		local last = -math.huge
		while true do
			local now = workspace:GetServerTimeNow()
			local index = math.max(math.floor(now / period) + 1, last + 1)
			task.wait(math.max(0, index * period - now))
			last = index
			tick()
		end
	end)
end

-- Обработчики для серверных тестов (Server/Tests): те же функции, что вызывают подсказки и такт.
GymService.Handlers = { Upgrade = upgrade, TickPlayer = tickPlayer, Refresh = refresh }

return GymService

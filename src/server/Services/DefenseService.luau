-- Защита музея и взлом (D37, D46). Покупка защиты — только в подготовку, по цене уровня своего музея (доля цены
-- взлома); устройство взлома — заранее, днём, по уровню музея-цели. Установка и снятие — только в подготовку:
-- ловушка, робот и капкан — в разрешённых зонах пола своего зала (D48-C, Shared/DefenseRules.CheckFreeSpot),
-- усиленная дверь — на входе, лазер — «Вход» или «Галерея» поперёк дорожки; не больше min(уровень, 5), каждого вида по
-- одному. В Судную ночь раз в GameConfig.Defense.Tick сервер проверяет чужих (воров) у устройств: дверь не пускает в
-- музей (зал и галереи) без взлома, ловушка — урон и замедление (вариант в конфиге), капкан — 10 с обездвижен
-- (одноразовый), лазер — урон и тревога владельцу, робот — бьёт воров в радиусе, если видит их (стены здания
-- закрывают), его можно сломать ударами. Лазер, ловушка и капкан смотрят путь вора за такт (DefenseRules.CrossedLaser,
-- PathDistance): бегущий вор не проскакивает их между проверками. Подсветка устройства: дежурит — бирюзовая, сработало — красная. Взлом двери — удержание 5 с, уроном не прерывается,
-- устройство расходуется, дверь открыта для всех до конца ночи. Устройство списывается при установке (из data.defense.owned)
-- и записывается в data.defense.installed с номером круга Судной ночи: снял в подготовку или вышел до ночи — вернётся
-- (DefenseRules.Settle при входе), отработало ночь — исчезает; купленное и не установленное остаётся.
-- Зависит от MoveGuard (D52), DataService, PlotService, PvpService, TimeService, Shared/DefenseRules, Shared/GameTime, World/Models/Defense,
-- World/ModelBuilder, Util/*, Remotes, GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local DefenseRules = require(ReplicatedStorage.Shared.DefenseRules)
local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local UITokens = require(ReplicatedStorage.Shared.Config.UITokens)
local Server = ServerScriptService.Server
local DataService = require(Server.Services.DataService)
local MoveGuard = require(Server.Services.MoveGuard)
local PlotService = require(Server.Services.PlotService)
local PvpService = require(Server.Services.PvpService)
local TheftService = require(Server.Services.TheftService)
local TimeService = require(Server.Services.TimeService)
local Log = require(Server.Util.Log)
local MuseumSpace = require(Server.Util.MuseumSpace)
local Notify = require(Server.Util.Notify)
local Prompts = require(Server.Util.Prompts)
local RateLimiter = require(Server.Util.RateLimiter)
local Validate = require(Server.Util.Validate)
local ModelBuilder = require(Server.World.ModelBuilder)
local DefenseModels = require(Server.World.Models.Defense)

local cfg = GameConfig.Defense
local FOLDER = "Defense"

type Device = {
	kind: string,
	spot: any, -- имя фиксированного места или Vector3 (оси участка)
	model: Model,
	at: Vector3, -- центр в осях участка
	hp: number?, -- робот
	lastAttack: number?,
	broken: boolean?, -- робот сломан / капкан сработал
}

type Museum = {
	installed: { [string]: Device },
	hacked: boolean,
	cooldowns: { [string]: number }, -- "<вид>:<UserId>" → os.clock следующего срабатывания
	hackBegan: { [any]: number },
	last: { [any]: Vector3 }, -- где был вор на прошлом такте (оси участка): лазер, ловушка и капкан смотрят весь путь
}

local museums: { [number]: Museum } = {}
local limiter = RateLimiter.new(GameConfig.RateLimits.Storage)

local DefenseService = {}

local function museumOf(ownerId: number): Museum
	local m = museums[ownerId]
	if not m then
		m = { installed = {}, hacked = false, cooldowns = {}, hackBegan = {}, last = {} }
		museums[ownerId] = m
	end
	return m
end

local function phase(): string
	return GameTime.At(GameTime.Now()).phase
end

local function doomOpen(): boolean
	return GameTime.TheftPhase(GameTime.Now()) == "Open"
end

local function levelOf(player: any): number
	local data = DataService.GetData(player)
	return if data then data.museumLevel or 1 else 1
end

local function toLocal(plot: PlotService.Plot, world: Vector3): Vector3
	return plot.floorOrigin:PointToObjectSpace(world)
end

-- Постаменты, которые стоят на этом уровне музея (места без постамента убраны из мира).
local function showcasesLocal(plot: PlotService.Plot): { Vector3 }
	local list = {}
	for _, showcase in plot.showcases do
		if showcase.Parent then
			table.insert(list, toLocal(plot, showcase.Position))
		end
	end
	return list
end

local function hasGalleries(plot: PlotService.Plot): boolean
	return MuseumSpace.HasGalleries(plot)
end

-- Подсветка устройства (детали Glow): цвет состояния; seconds — вернуть дежурный цвет через столько секунд.
local function glow(device: any, state: string, seconds: number?)
	local color = DefenseModels.States[state]
	if not color or not device.model then
		return
	end
	for _, part in device.model:GetDescendants() do
		if part:IsA("BasePart") and part.Name == "Glow" then
			part.Color = color
		end
	end
	if seconds then
		device.glowToken = (device.glowToken or 0) + 1
		local token = device.glowToken
		task.delay(seconds, function()
			if device.glowToken == token and not device.broken then
				glow(device, "idle")
			end
		end)
	end
end

local function freeDevices(m: Museum, except: string?): { Vector3 }
	local list = {}
	for kind, device in m.installed do
		if kind ~= except and DefenseRules.Placement[kind] == "Free" then
			table.insert(list, device.at)
		end
	end
	return list
end

local function participants(): { any }
	local list = {}
	for _, plot in PlotService.GetPlots() do
		if plot.owner then
			table.insert(list, plot.owner)
		end
	end
	return list
end

-- Состояние защиты владельцу (окно «Защита»).
function DefenseService.Sync(player: any)
	local defense = DataService.Defense(player)
	if not defense then
		return
	end
	local m = museumOf(player.UserId)
	local installed = {}
	for kind, device in m.installed do
		installed[kind] = { spot = device.spot, broken = device.broken == true }
	end
	local level = levelOf(player)
	player:SetAttribute(
		"HackDevices",
		(function()
			local n = 0
			for _, count in defense.hacks do
				n += count
			end
			return n
		end)()
	)
	Remotes.FireClient(Remotes.Names.DefenseChanged, player, {
		owned = table.clone(defense.owned),
		hacks = table.clone(defense.hacks),
		installed = installed,
		level = level,
		max = DefenseRules.MaxDevices(cfg, level),
		hacked = m.hacked,
	})
end

local function coinsChanged(player: any)
	local data = DataService.GetData(player)
	if data then
		player:SetAttribute("Coins", data.coins)
	end
end

local function folderOf(plot: PlotService.Plot): Folder
	local folder = plot.model:FindFirstChild(FOLDER)
	if not folder then
		folder = Instance.new("Folder")
		folder.Name = FOLDER
		folder.Parent = plot.model
	end
	return folder :: Folder
end

local function robotBar(device: Device)
	local head = device.model:FindFirstChild("Eye")
	if not head then
		return
	end
	local gui = device.model:FindFirstChild("HP", true) :: BillboardGui?
	if not gui then
		local bar = UITokens.Defense.RobotBar
		local g = Instance.new("BillboardGui")
		g.Name = "HP"
		g.Size = UDim2.fromScale(bar.Size.X, bar.Size.Y)
		g.StudsOffset = Vector3.new(0, bar.Lift, 0)
		g.MaxDistance = bar.MaxDistance
		local back = Instance.new("Frame")
		back.Name = "Fond"
		back.Size = UDim2.fromScale(1, 1)
		back.BackgroundColor3 = bar.Back
		back.Parent = g
		local fill = Instance.new("Frame")
		fill.Name = "Barre"
		fill.Size = UDim2.fromScale(1, 1)
		fill.BackgroundColor3 = bar.Fill
		fill.BorderSizePixel = 0
		fill.Parent = back
		g.Parent = head
		gui = g
	end
	local fill = (gui :: BillboardGui):FindFirstChild("Barre", true) :: Frame
	fill.Size = UDim2.fromScale(math.clamp((device.hp or 0) / cfg.Robot.HP, 0, 1), 1)
end

-- Модель устройства в музее. Возвращает центр в осях участка и модель.
local function buildDevice(plot: PlotService.Plot, kind: string, spot: any): (Model, Vector3)
	local bricks, localCFrame, center
	if kind == "Door" then
		bricks = DefenseModels.Door(cfg.Door.Size)
		center = Vector3.new(0, 0, cfg.Door.At.Z)
		localCFrame = CFrame.new(center)
	elseif kind == "Laser" then
		local laser = cfg.Lasers[spot]
		bricks = DefenseModels.Laser(laser.x1 - laser.x0, laser.y)
		center = Vector3.new((laser.x0 + laser.x1) / 2, 0, laser.z)
		localCFrame = CFrame.new(center)
	else
		bricks = (DefenseModels :: any)[kind]()
		center = Vector3.new(spot.X, 0, spot.Z)
		-- робот смотрит на вход (−Z участка)
		localCFrame = CFrame.new(center)
	end
	local model = ModelBuilder.Build("Defense_" .. kind, bricks, { collide = false, shadow = false })
	ModelBuilder.Place(model, plot.floorOrigin * localCFrame, folderOf(plot))
	glow({ model = model }, "idle")
	return model, center
end

local function removeDevice(m: Museum, kind: string)
	local device = m.installed[kind]
	if device then
		device.model:Destroy()
		m.installed[kind] = nil
	end
end

-- Точка в осях участка — внутри музея (за дверью): главный зал, а при galleries — и галереи (вход в них только из
-- зала, D48-C).
-- «В зале или открытой галерее» — общая проверка пространства музея (Util/MuseumSpace, её же берут кражи, D52).
local insideHall = MuseumSpace.InsideLocal

-- Робот видит вора: между корпусом и вором нет стен и тумб здания своего участка.
local function robotSees(plot: PlotService.Plot, from: Vector3, root: BasePart): boolean
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	local list: { Instance } = {}
	for _, name in { "Building", "Showcases" } do
		local folder = plot.model:FindFirstChild(name)
		if folder then
			table.insert(list, folder)
		end
	end
	params.FilterDescendantsInstances = list
	return workspace:Raycast(from, root.Position - from, params) == nil
end

local function nearDoor(thief: any, plot: PlotService.Plot): boolean
	local root = Validate.GetLiveRoot(thief)
	return root ~= nil and (root.Position - plot.floorOrigin * cfg.Door.At).Magnitude <= cfg.HackDistance
end

-- Взлом двери: удержание «Взломать». Начало засчитывается только по правилам: Судная ночь, чужая закрытая дверь,
-- взломщик рядом и не оглушён (иначе «начать заранее и сразу завершить» обошло бы 5 с у двери).
local function hackBegin(thief: any, owner: any, plot: PlotService.Plot)
	local m = museumOf(owner.UserId)
	m.hackBegan[thief] = nil
	if
		thief == owner
		or not doomOpen()
		or not m.installed.Door
		or m.hacked
		or thief:GetAttribute("Knocked")
		or not nearDoor(thief, plot)
	then
		return
	end
	m.hackBegan[thief] = os.clock()
end

local function hackEnd(thief: any, owner: any)
	local m = museums[owner.UserId] -- не создавать: владелец мог уже выйти (отмена приходит с задержкой)
	if m then
		m.hackBegan[thief] = nil
	end
end

local function hackComplete(thief: any, owner: any, plot: PlotService.Plot)
	local m = museumOf(owner.UserId)
	local began = m.hackBegan[thief]
	m.hackBegan[thief] = nil
	local door = m.installed.Door
	if not door or m.hacked or thief == owner or not doomOpen() or thief:GetAttribute("Knocked") then
		return
	end
	if not began or os.clock() - began < cfg.HackSeconds - GameConfig.Theft.HoldTolerance then
		return -- без удержания (подделанный Triggered) взлом не засчитывается
	end
	if not nearDoor(thief, plot) then
		return
	end
	local defense = DataService.Defense(thief)
	if not defense then
		return
	end
	local need = levelOf(owner)
	local used = nil
	for level = need, #cfg.HackPrices do
		local key = "L" .. level
		if (defense.hacks[key] or 0) > 0 then
			defense.hacks[key] -= 1
			used = level
			break
		end
	end
	if not used then
		Notify.Send(
			thief,
			("Нужно устройство взлома для музея уровня %d"):format(need),
			"Stop"
		)
		return
	end
	m.hacked = true
	for _, part in door.model:GetDescendants() do
		if part:IsA("BasePart") then
			part.Transparency = 0.75
		elseif part:IsA("ProximityPrompt") then
			part:Destroy()
		end
	end
	DataService.RequestSave(thief)
	DefenseService.Sync(thief)
	DefenseService.Sync(owner)
	Notify.Send(thief, "Дверь взломана — она открыта до конца ночи", "Go")
	Notify.Send(owner, "Вашу дверь взломали!", "Stop")
end

local function addDoorPrompt(device: Device, owner: any, plot: PlotService.Plot)
	local panel = device.model:FindFirstChild("Panel")
	if not panel or not panel:IsA("BasePart") then
		return
	end
	local prompt = Prompts.Create(panel, "Hack", "Усиленная дверь", cfg.HackDistance - 2)
	prompt.HoldDuration = cfg.HackSeconds
	Prompts.BindHold(prompt, function(player)
		hackBegin(player, owner, plot)
	end, function(player)
		hackEnd(player, owner)
	end, function(player)
		hackComplete(player, owner, plot)
	end)
end

local function install(player: any, kind: any, spot: any)
	local plot = PlotService.GetPlotOf(player)
	local defense = DataService.Defense(player)
	if not plot or not defense or not DefenseRules.IsType(kind) then
		return
	end
	local m = museumOf(player.UserId)
	local reason = DefenseRules.CanInstall(cfg, kind, phase(), levelOf(player), m.installed, defense.owned[kind] or 0)
	if not reason then
		if DefenseRules.Placement[kind] == "Free" then
			if typeof(spot) ~= "Vector3" then
				reason = "Выберите место на полу"
			else
				reason = DefenseRules.CheckFreeSpot(
					cfg,
					spot,
					showcasesLocal(plot),
					toLocal(plot, plot.chest.Position),
					freeDevices(m, kind),
					hasGalleries(plot)
				)
			end
		else
			local spots = DefenseRules.FixedSpots(cfg, kind) or {}
			if type(spot) ~= "string" or not table.find(spots, spot) then
				reason =
					"Это устройство ставится только на размеченное место"
			end
		end
	end
	if reason then
		Notify.Send(player, reason, "Stop")
		return
	end
	local model, center = buildDevice(plot, kind, spot)
	local device: Device = { kind = kind, spot = spot, model = model, at = center }
	if kind == "Robot" then
		device.hp = cfg.Robot.HP
		robotBar(device)
	elseif kind == "Door" then
		addDoorPrompt(device, player, plot)
	end
	m.installed[kind] = device
	defense.owned[kind] = math.max((defense.owned[kind] or 0) - 1, 0)
	defense.installed = defense.installed or {}
	defense.installed[kind] = GameTime.At(GameTime.Now()).cycle -- ночь этого круга (подготовка — его 10-й день)
	DataService.RequestSave(player)
	DefenseService.Sync(player)
	Notify.Send(player, ("Установлено: %s"):format(DefenseRules.Names[kind]), "Go")
end

local function tryAction(player: any, action: any, a: any, b: any)
	if not limiter:Allow(player) then
		return
	end
	local data = DataService.GetData(player)
	local defense = DataService.Defense(player)
	if not data or not defense then
		return
	end
	if action == "BuyDefense" then
		local reason = DefenseRules.CanBuyDefense(cfg, a, phase(), data.coins, levelOf(player))
		if reason then
			Notify.Send(player, reason, "Stop")
			return
		end
		local price = DefenseRules.Price(cfg, a, levelOf(player)) :: number
		if not DataService.Spend(player, price) then
			return
		end
		defense.owned[a] = (defense.owned[a] or 0) + 1
		coinsChanged(player)
		DataService.RequestSave(player)
		DefenseService.Sync(player)
		Notify.Send(player, ("Куплено: %s"):format(DefenseRules.Names[a]), "Go")
	elseif action == "BuyHack" then
		local reason = DefenseRules.CanBuyHack(cfg, a, phase(), data.coins)
		if reason then
			Notify.Send(player, reason, "Stop")
			return
		end
		if not DataService.Spend(player, DefenseRules.HackPrice(cfg, a)) then
			return
		end
		local key = "L" .. a
		defense.hacks[key] = (defense.hacks[key] or 0) + 1
		coinsChanged(player)
		DataService.RequestSave(player)
		DefenseService.Sync(player)
		Notify.Send(
			player,
			("Куплено устройство взлома для музея уровня %d"):format(a),
			"Go"
		)
	elseif action == "Install" then
		install(player, a, b)
	elseif action == "Remove" then
		if phase() ~= "Preparation" or not DefenseRules.IsType(a) then
			Notify.Send(player, "Снимать защиту можно только в подготовку", "Stop")
			return
		end
		local m = museumOf(player.UserId)
		if m.installed[a] then
			removeDevice(m, a)
			defense.owned[a] = (defense.owned[a] or 0) + 1
			if type(defense.installed) == "table" then
				defense.installed[a] = nil
			end
			DataService.RequestSave(player)
		end
		DefenseService.Sync(player)
	end
end

local function ready(m: Museum, key: string, seconds: number): boolean
	local now = os.clock()
	if (m.cooldowns[key] or 0) > now then
		return false
	end
	m.cooldowns[key] = now + seconds
	return true
end

-- Один такт защиты всех музеев (Судная ночь).
local function tick()
	if not doomOpen() then
		return
	end
	local players = participants()
	for _, plot in PlotService.GetPlots() do
		local owner = plot.owner
		local m = owner and museums[owner.UserId]
		if owner and m and next(m.installed) then
			for _, thief in players do
				local root, humanoid = Validate.GetLiveRoot(thief)
				if
					thief ~= owner
					and root
					and humanoid
					and humanoid.Health > 0
					and not thief:GetAttribute("Knocked")
				then
					local at = toLocal(plot, root.Position)
					local id = tostring(thief.UserId)
					local inside = insideHall(at, hasGalleries(plot))
					-- путь за такт: бегущий вор проходит луч и ловушку между проверками; дальний скачок — перенос
					local from = m.last[thief]
					if from and (at - from).Magnitude > cfg.TrackStep then
						from = nil
					end
					m.last[thief] = at
					-- отброс от устройства — к выходу (источник чуть глубже в зале)
					local push = plot.floorOrigin * (at + Vector3.new(0, 0, cfg.PushDepth))
					if m.installed.Door and not m.hacked and inside then
						root.CFrame = plot.floorOrigin
							* CFrame.new(
								cfg.Door.At.X + cfg.DoorEject.X,
								cfg.DoorEject.Y,
								cfg.Door.At.Z + cfg.DoorEject.Z
							)
							* CFrame.Angles(0, math.pi, 0)
						MoveGuard.Mark(thief) -- выброс у двери — перенос сервером (D52)
						if ready(m, "Door:" .. id, cfg.NoticeCooldown) then
							Notify.Send(thief, "Усиленная дверь: нужен взлом", "Stop")
						end
						m.last[thief] = nil -- перенос: путь от зала до улицы — не бег через лазер
						continue -- выставлен наружу: остальные устройства его уже не видят
					end
					local trap = m.installed.Trap
					if
						trap
						and inside
						and DefenseRules.PathDistance(trap.at, from, at) <= cfg.Trap.Radius
						and math.abs(at.Y) < cfg.TrapHeight
					then
						if ready(m, "Trap:" .. id, cfg.Trap.Cooldown) then
							glow(trap, "active", 1)
							PvpService.DamagePlayer(thief, PvpService.MaxHP(thief) * cfg.Trap.Damage, push)
							if cfg.Trap.Effect == "Slow" then
								PvpService.Slow(thief, cfg.Trap.Slow, cfg.Trap.SlowSeconds)
							elseif cfg.Trap.Effect == "Stun" then
								PvpService.Snare(thief, cfg.Trap.StunSeconds)
							end
						end
					end
					local snare = m.installed.Snare
					if
						snare
						and not snare.broken
						and inside
						and math.abs(at.Y) < cfg.TrapHeight
						and DefenseRules.PathDistance(snare.at, from, at) <= cfg.Snare.Radius
						and PvpService.Snare(thief, cfg.Snare.Seconds) -- одноразовый: тратится, только если поймал
					then
						snare.broken = true
						glow(snare, "broken")
						for _, part in snare.model:GetDescendants() do
							if part:IsA("BasePart") then
								part.Transparency = 0.6
							end
						end
						Notify.Send(owner, ("Капкан поймал %s!"):format(thief.Name), "Go")
					end
					local laser = m.installed.Laser
					if laser then
						local beam = cfg.Lasers[laser.spot]
						if
							beam
							and DefenseRules.CrossedLaser(cfg, beam, from, at)
							and at.Y < beam.y + cfg.LaserHeight
							and ready(m, "Laser:" .. id, cfg.Laser.Cooldown)
						then
							glow(laser, "active", 1)
							PvpService.DamagePlayer(thief, PvpService.MaxHP(thief) * cfg.Laser.Damage, push)
							Notify.Send(
								owner,
								("Тревога! Лазер: %s в вашем музее"):format(thief.Name),
								"Stop"
							)
						end
					end
					local robot = m.installed.Robot
					if
						robot
						and not robot.broken
						and inside
						and Vector3.new(at.X - robot.at.X, 0, at.Z - robot.at.Z).Magnitude <= cfg.Robot.Radius
						and robotSees(plot, robot.model:GetPivot().Position + Vector3.new(0, cfg.RobotAim, 0), root)
					then
						local now = os.clock()
						if now - (robot.lastAttack or 0) >= cfg.Robot.Interval then
							robot.lastAttack = now
							local pivot = robot.model:GetPivot()
							robot.model:PivotTo(
								CFrame.lookAt(
									pivot.Position,
									Vector3.new(root.Position.X, pivot.Position.Y, root.Position.Z)
								)
							)
							glow(robot, "attack", cfg.Robot.Interval * 0.6)
							PvpService.DamagePlayer(thief, cfg.Robot.Damage, pivot.Position)
						end
					end
				end
			end
		end
	end
end

-- Судная ночь закончилась: установленное исчезает (списано при установке), купленное остаётся (D37).
local function endNight()
	for ownerId, m in museums do
		local owner = nil
		for _, player in participants() do
			if player.UserId == ownerId then
				owner = player
			end
		end
		local defense = owner and DataService.Defense(owner)
		if defense and type(defense.installed) == "table" and next(defense.installed) then
			defense.installed = {} -- отработали ночь (списаны при установке)
			DataService.RequestSave(owner)
		end
		for kind in m.installed do
			removeDevice(m, kind)
		end
		m.hacked = false
		table.clear(m.cooldowns)
		table.clear(m.hackBegan)
		table.clear(m.last)
		if owner then
			DefenseService.Sync(owner)
		end
	end
end

-- Начало Судной ночи круга cycle (общее время).
local function nightStart(cycle: number): number
	local t = GameConfig.Time
	return t.Epoch + (cycle + 1) * GameTime.CycleLength() - t.DoomNightLength
end

-- Вход: устройства, поставленные к ещё не прошедшей ночи (вышел или упал сервер до неё), — снова в запасе.
function DefenseService.OnPlayerLoaded(player: any)
	local defense = DataService.Defense(player)
	if defense and DefenseRules.Settle(defense, GameTime.Now(), nightStart) > 0 then
		DataService.RequestSave(player)
	end
end

-- Игрок вышел: модели убираются; поставленное к ещё не прошедшей ночи — снова в запасе, в Судную ночь — отработало.
function DefenseService.OnPlayerLeaving(player: any)
	local defense = DataService.Defense(player)
	if defense and not doomOpen() then
		DefenseRules.Settle(defense, GameTime.Now(), nightStart)
	end
	local m = museums[player.UserId]
	if m then
		for kind in m.installed do
			removeDevice(m, kind)
		end
		museums[player.UserId] = nil
	end
end

function DefenseService.Init()
	Remotes.Get(Remotes.Names.DefenseAction).OnServerEvent:Connect(tryAction)
	-- Закрытая усиленная дверь: красть можно только изнутри зала (снаружи — через проём — нельзя).
	TheftService.SetAccessCheck(function(thief, owner, plot)
		local m = museums[owner.UserId]
		local root = Validate.GetLiveRoot(thief)
		local inside = root and insideHall(toLocal(plot, root.Position), hasGalleries(plot))
		if m and m.installed.Door and not m.hacked and root and not inside then
			return "Усиленная дверь: сначала взломайте её"
		end
		return nil
	end)
	TimeService.OnPhaseChanged(function(state, previous)
		if previous and previous.phase == "DoomNight" and state.phase ~= "DoomNight" then
			endNight()
		end
	end)
	-- Робот — цель для ударов воров (D37: вор может его уничтожить до конца ночи).
	PvpService.AddTargetProvider(function(attacker)
		local list = {}
		for _, plot in PlotService.GetPlots() do
			local owner = plot.owner
			local m = owner and museums[owner.UserId]
			local robot = m and m.installed.Robot
			if robot and owner ~= attacker and not robot.broken then
				table.insert(list, {
					position = robot.model:GetPivot().Position + Vector3.new(0, cfg.RobotAim, 0),
					onHit = function(damage: number)
						robot.hp = (robot.hp or 0) - damage
						robotBar(robot)
						if robot.hp <= 0 then
							robot.broken = true
							robot.model:Destroy()
							Notify.Send(owner, "Вашего робота-охранника сломали", "Stop")
							Notify.Send(attacker, "Робот-охранник сломан", "Go")
						end
					end,
				})
			end
		end
		return list
	end)
	task.spawn(function()
		while true do
			task.wait(cfg.Tick)
			local ok, err = pcall(tick)
			if not ok then
				Log.Warn("DefenseService", "такт защиты: " .. tostring(err))
			end
		end
	end)
end

-- Для серверных тестов: те же функции, что у RemoteEvent и подсказки.
DefenseService.Handlers = {
	Action = tryAction,
	Tick = tick,
	EndNight = endNight,
	HackBegin = hackBegin,
	HackComplete = hackComplete,
	Museum = museumOf,
}

return DefenseService

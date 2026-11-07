-- Автоматический бой с боссом (D22, D40, D42). «Забрать» у предмета возле спящего босса начинает бой: сервер проверяет
-- босса и предмет, закрепляет предмет за бойцом (другие его не заберут, подсказки у босса выключены), босс
-- просыпается, встаёт и становится в стойку, дальше игрок и босс бьют сами по своим интервалам, пока HP одного не
-- станет 0. Таймера и заранее решённого исхода нет: каждый удар считается в момент удара (Config/Battle, сила
-- игрока — урон и HP). Победа: предмет — в руки бойцу, босс повален, встаёт, идёт на место и засыпает. Поражение:
-- игрока отбрасывает (без телепорта), предмет остаётся на месте, босс торжествует, идёт на место и засыпает — после
-- этого бой можно начать сразу снова. Ночь, выход игрока, гибель персонажа — бой прерывается. С одним боссом бьётся
-- один игрок, помочь ему нельзя; остальные видят бой (анимации и HP — у всех). D49: полоска HP — только над боссом;
-- HP бойца — в стандартной полосе здоровья Roblox (урон боя переносится в здоровье персонажа, до нуля не доходит,
-- после боя здоровье прежнее). Боец заперт в зоне босса до конца боя: невидимые стены на границах зон (группа
-- ZoneLock) сталкиваются только с бойцами (Util/CharacterGroups), сервер возвращает бойца в зону, если тот оказался
-- снаружи. Побега по расстоянию нет; босс не уходит дальше Leash от своего места (площадка без декора, D43).
-- Зависит от MoveGuard (D52), BossService, BossLootService, CarryService, DataService, TimeService, Config/Battle, Shared/GameTime,
-- World/MapLayout, Util/CharacterGroups, Util/Notify, Util/Validate, Util/Log.

local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Battle = require(ReplicatedStorage.Shared.Config.Battle)
local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local NumberFormat = require(ReplicatedStorage.Shared.NumberFormat)
local Server = ServerScriptService.Server
local BossLootService = require(Server.Services.BossLootService)
local BossService = require(Server.Services.BossService)
local DataService = require(Server.Services.DataService)
local MoveGuard = require(Server.Services.MoveGuard)
local ItemRegistry = require(Server.Services.ItemRegistry)
local TimeService = require(Server.Services.TimeService)
local MapLayout = require(Server.World.MapLayout)
local CharacterGroups = require(Server.Util.CharacterGroups)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local Validate = require(Server.Util.Validate)

export type Fight = {
	zone: number,
	slot: number,
	player: any,
	boss: BossService.Boss,
	active: boolean,
	phase: string, -- "Waking" | "Fight"
	hp: number,
	maxHp: number,
	damage: number,
	bossHp: number,
	bossMax: number,
	bossDamage: number,
	nextPlayer: number,
	nextBoss: number,
	attacks: number,
	result: string?,
	log: { string },
	health: { max: number, value: number }?, -- здоровье персонажа до боя (вернуть после)
}

local fights: { [number]: Fight } = {} -- по зоне
local byPlayer: { [any]: Fight } = {}
local returning: { [number]: boolean } = {} -- босс ещё идёт на место после боя
local random = Random.new()
local BAR_ABOVE_BOSS = 3.2 -- полоска HP над макушкой босса, стадов

local BattleService = {}

-- Имя босса зоны для сообщений («Сторожевой пёс победил!»).
local function bossName(zone: number): string
	return GameConfig.Zones[zone].boss
end

-- Множитель силы: HP и урон × (1 + сила) ^ Growth.
local function power(strength: number): number
	return (1 + math.max(strength, 0)) ^ Battle.Player.Growth
end

-- Характеристики игрока с силой strength.
function BattleService.PlayerStats(strength: number): (number, number)
	local p = power(strength)
	return Battle.Player.BaseHP * p, Battle.Player.BaseDamage * p
end

-- Характеристики босса зоны zone.
function BattleService.BossStats(zone: number): (number, number)
	local cfg = Battle.Bosses[zone]
	local p = power(cfg.Strength)
	return cfg.HP * p, cfg.Damage * p
end

local function strengthOf(player: any): number
	local data = DataService.GetData(player)
	return if data then data.strength else 0
end

local function roll(value: number): number
	return value * (1 + random:NextNumber(-Battle.DamageSpread, Battle.DamageSpread))
end

local function flat(v: Vector3): Vector3
	return Vector3.new(v.X, 0, v.Z)
end

-- Полоска HP над боссом (видна всем).
local function makeBar(adornee: BasePart, name: string, offset: number, color: Color3): BillboardGui
	local gui = Instance.new("BillboardGui")
	gui.Name = name
	gui.Size = UDim2.fromScale(6, 1)
	gui.StudsOffsetWorldSpace = Vector3.new(0, offset, 0)
	gui.AlwaysOnTop = true
	gui.MaxDistance = 120
	gui.Adornee = adornee
	local back = Instance.new("Frame")
	back.Name = "Back"
	back.Size = UDim2.fromScale(1, 0.55)
	back.Position = UDim2.fromScale(0, 0.45)
	back.BackgroundColor3 = Color3.fromHex("1B1B22")
	back.BorderSizePixel = 0
	back.Parent = gui
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0.3, 0)
	corner.Parent = back
	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.Size = UDim2.fromScale(1, 1)
	fill.BackgroundColor3 = color
	fill.BorderSizePixel = 0
	fill.Parent = back
	corner:Clone().Parent = fill
	local label = Instance.new("TextLabel")
	label.Name = "Text"
	label.Size = UDim2.fromScale(1, 0.5)
	label.BackgroundTransparency = 1
	label.TextScaled = true
	label.Font = Enum.Font.GothamBold
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextStrokeTransparency = 0.3
	label.Parent = gui
	gui.Parent = adornee
	return gui
end

local function setBar(gui: BillboardGui?, title: string, hp: number, maxHp: number)
	if not gui or not gui.Parent then
		return
	end
	local back = gui:FindFirstChild("Back") :: Frame
	local fill = back:FindFirstChild("Fill") :: Frame
	fill.Size = UDim2.fromScale(math.clamp(hp / maxHp, 0, 1), 1)
	local label = gui:FindFirstChild("Text") :: TextLabel
	label.Text = ("%s  %s / %s"):format(title, NumberFormat.Short(math.max(math.ceil(hp), 0)), NumberFormat.Short(math.ceil(maxHp)))
end

-- HP бойца — в здоровье персонажа (стандартная полоса Roblox): не меньше 1, чтобы персонаж не погиб.
local function mirrorHealth(fight: Fight)
	local _, humanoid = Validate.GetLiveRoot(fight.player)
	if humanoid then
		humanoid.MaxHealth = fight.maxHp
		humanoid.Health = math.clamp(fight.hp, 1, fight.maxHp)
	end
end

local function refreshBars(fight: Fight)
	local bossBar = fight.boss.root:FindFirstChild("BattleBar") :: BillboardGui?
	setBar(bossBar, fight.boss.model:GetAttribute("BossName") or "Босс", fight.bossHp, fight.bossMax)
	fight.boss.model:SetAttribute("HP", math.max(fight.bossHp, 0))
	fight.player:SetAttribute("BattleHP", math.max(fight.hp, 0))
	mirrorHealth(fight)
end

local function clearBars(fight: Fight)
	local bossBar = fight.boss.root:FindFirstChild("BattleBar")
	if bossBar then
		bossBar:Destroy()
	end
	-- здоровье персонажа — как до боя
	local saved = fight.health
	local character = fight.player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if saved and humanoid and humanoid.Health > 0 then
		humanoid.MaxHealth = saved.max
		humanoid.Health = saved.value
	end
end

-- Границы зоны zone по z (мир): вход (ближе к безопасной зоне) и выход.
local function zoneBounds(zone: number): (number, number)
	local start = MapLayout.ZoneStartZ(zone)
	return start - MapLayout.ZoneSize, start
end

-- Боец снаружи своей зоны (телепорт, сбой физики) — назад, на Battle.ZoneLock.Margin внутрь от границы.
local function keepInZone(fight: Fight, root: BasePart)
	local z0, z1 = zoneBounds(fight.zone)
	local margin = Battle.ZoneLock.Margin
	local z = root.Position.Z
	if z > z0 and z < z1 then
		return
	end
	local inside = math.clamp(z, z0 + margin, z1 - margin)
	local p = root.Position
	MoveGuard.Teleport(fight.player, CFrame.new(p.X, p.Y, inside) * root.CFrame.Rotation) -- перенос сервером (D52)
	table.insert(fight.log, "вернули в зону")
end

-- Отброс проигравшего: толчок от босса вверх и назад, без телепорта (D40).
local function knockback(player: any, from: Vector3)
	local root = Validate.GetLiveRoot(player)
	if not root then
		return
	end
	local away = flat(root.Position - from)
	away = if away.Magnitude > 0.01 then away.Unit else Vector3.new(0, 0, 1)
	local cfg = Battle.Knockback
	local attachment = Instance.new("Attachment")
	attachment.Name = "Knockback"
	attachment.Parent = root
	local push = Instance.new("LinearVelocity")
	push.Name = "Knockback"
	push.Attachment0 = attachment
	push.RelativeTo = Enum.ActuatorRelativeTo.World
	push.MaxForce = math.huge
	push.VectorVelocity = away * cfg.Speed + Vector3.new(0, cfg.Up, 0)
	push.Parent = root
	player:SetAttribute("KnockedAt", os.clock())
	player:SetAttribute("KnockedFrom", from)
	task.delay(cfg.Time, function()
		push:Destroy()
		attachment:Destroy()
	end)
end

-- Босс возвращается на место и засыпает; после этого его снова можно будить.
local function goHome(boss: BossService.Boss, after: string?, afterTime: number?)
	local zone = boss.zone
	returning[zone] = true
	if after then
		BossService.Stop(boss)
		BossService.SetState(boss, after)
		task.wait(afterTime or 0)
	end
	BossService.SetState(boss, "Return")
	BossService.MoveTo(boss, boss.home.Position)
	BossService.Face(boss, boss.home.Position)
	local started = os.clock()
	while BossService.DistanceHome(boss) > Battle.ArriveDistance and os.clock() - started < 20 do
		task.wait(Battle.TickSeconds)
		BossService.Face(boss, boss.home.Position)
	end
	if BossService.DistanceHome(boss) > Battle.ArriveDistance then
		BossService.SnapHome(boss) -- застрял — на место без ожидания
	end
	BossService.FaceHome(boss)
	BossService.SetState(boss, "FallAsleep")
	returning[zone] = nil
	BossLootService.SetOpen(zone, true) -- дома: можно сразу начинать новый бой
	task.wait(Battle.Timeline.FallAsleep)
	if boss.state == "FallAsleep" then
		BossService.SetState(boss, "Sleep")
	end
end

local function finish(fight: Fight, result: string)
	if not fight.active then
		return
	end
	fight.active = false
	fight.result = result
	fights[fight.zone] = nil
	byPlayer[fight.player] = nil
	clearBars(fight)
	fight.player:SetAttribute("InBattle", nil)
	CharacterGroups.Apply(fight.player) -- стены зон снова пропускают
	fight.player:SetAttribute("BattleHP", nil)
	fight.player:SetAttribute("BattleMaxHP", nil)
	fight.boss.model:SetAttribute("TargetUserId", nil)
	local boss = fight.boss
	local tl = Battle.Timeline
	Log.Debug("BattleService", ("Бой %s с боссом %d: %s"):format(fight.player.Name, fight.zone, result))
	if result == "win" then
		if BossLootService.Award(fight.zone, fight.slot, fight.player) then
			Notify.Send(fight.player, "Победа! Несите добычу в свой музей", "Go")
		else
			BossLootService.Release(fight.zone, fight.slot)
			Notify.Send(fight.player, "Победа, но предмет забрать не вышло", "Stop")
		end
		task.spawn(goHome, boss, "Defeat", tl.Defeat)
	elseif result == "lose" then
		knockback(fight.player, BossService.Position(boss))
		BossLootService.Release(fight.zone, fight.slot)
		Notify.Send(fight.player, ("%s победил! Набери силы и попробуй снова"):format(bossName(fight.zone)), "Stop")
		task.spawn(goHome, boss, "Victory", tl.Victory)
	else
		BossLootService.Release(fight.zone, fight.slot)
		if result == "night" then
			Notify.Send(fight.player, "Ночь: бой прерван", "Stop")
		end
		task.spawn(goHome, boss, nil, nil)
	end
end

-- Можно ли начать бой: сообщение отказа или nil.
function BattleService.CanStart(player: any, zone: number, slot: number): string?
	local boss = BossService.Get(zone)
	if not boss then
		return "У этого босса пока нет боя"
	end
	if fights[zone] then
		return ("Босс занят боем с %s"):format(fights[zone].player.Name)
	end
	if returning[zone] or (boss.state ~= "Sleep" and boss.state ~= "FallAsleep") then
		return "Босс возвращается на место"
	end
	if byPlayer[player] then
		return "Вы уже в бою"
	end
	if GameTime.IsNight(TimeService.Current().phase) then
		return "Ночью коридор закрыт"
	end
	if ItemRegistry.GetCarriedBy(player) then
		return "Руки заняты — сначала бросьте предмет (G)"
	end
	local uid, part = BossLootService.SlotItem(zone, slot)
	if not uid or not part then
		return "Здесь уже пусто"
	end
	if not Validate.IsNear(player, part.Position, GameConfig.Bosses.TakeDistance) then
		return "Подойдите ближе"
	end
	return nil
end

local function step(fight: Fight)
	if not fight.active then
		return
	end
	local player = fight.player
	local root = Validate.GetLiveRoot(player)
	if not root or player.Parent == nil then
		finish(fight, "abort")
		return
	end
	local boss = fight.boss
	local bossCfg = Battle.Bosses[fight.zone]
	local bossPos = BossService.Position(boss)
	local toPlayer = flat(root.Position - bossPos)
	local dist = toPlayer.Magnitude
	keepInZone(fight, root) -- D49: из зоны босса до конца боя не выйти
	mirrorHealth(fight) -- стандартная полоса не «отрастает» между ударами
	BossService.Face(boss, root.Position)
	if fight.phase ~= "Fight" then
		return
	end
	-- Босс держит дистанцию атаки: далеко — бежит к игроку.
	if dist > bossCfg.AttackRange - 0.5 then
		local stopAt = root.Position - toPlayer.Unit * (bossCfg.AttackRange - 1.5)
		-- дальше Leash от своего места босс не идёт (его площадка свободна от декора, D43): ждёт на краю
		local fromHome = flat(stopAt - boss.home.Position)
		if fromHome.Magnitude > bossCfg.Leash then
			stopAt = boss.home.Position + fromHome.Unit * bossCfg.Leash
		end
		BossService.MoveTo(boss, stopAt, bossCfg.Speed)
	else
		BossService.Stop(boss)
	end
	local now = os.clock()
	-- Одна дальность на двоих (D52): игрок достаёт босса ровно с той дистанции, с которой босс начинает выпад, —
	-- безнаказанно бить издалека (у края поводка, отступая) нельзя.
	local reach = bossCfg.AttackRange + Battle.Player.Reach
	-- Удар игрока: автоматически, если достаёт.
	if now >= fight.nextPlayer and dist <= reach then
		fight.nextPlayer = now + Battle.Player.AttackInterval
		local hit = roll(fight.damage)
		fight.bossHp -= hit
		BossService.Hit(boss)
		table.insert(fight.log, ("игрок −%.1f"):format(hit))
		refreshBars(fight)
		if fight.bossHp <= 0 then
			finish(fight, "win")
			return
		end
	end
	-- Выпад босса: начатый в дальности — попадает через HitDelay (D52: отскок сразу после своего удара не спасает —
	-- иначе «ударил и отошёл» бил бы босса без ответа; бой автоматический, уворотов нет).
	if now >= fight.nextBoss and dist <= reach then
		fight.nextBoss = now + bossCfg.AttackInterval
		fight.attacks += 1
		BossService.Attack(boss, if fight.attacks % 3 == 0 then "swipe" else "bite")
		task.delay(Battle.HitDelay, function()
			if not fight.active then
				return
			end
			if not Validate.GetLiveRoot(player) then
				table.insert(fight.log, "босс промахнулся")
				return
			end
			local hit = roll(fight.bossDamage)
			fight.hp -= hit
			table.insert(fight.log, ("босс −%.1f"):format(hit))
			refreshBars(fight)
			if fight.hp <= 0 then
				finish(fight, "lose")
			end
		end)
	end
end

-- Начать бой за предмет в слоте slot у босса зоны zone. Возвращает бой или nil (отказ — сообщение игроку).
function BattleService.Begin(player: any, zone: number, slot: number): Fight?
	local refusal = BattleService.CanStart(player, zone, slot)
	if refusal then
		Notify.Send(player, refusal, "Stop")
		return nil
	end
	local boss = BossService.Get(zone) :: BossService.Boss
	if not BossLootService.Reserve(zone, slot, player) then
		Notify.Send(player, "Этот предмет уже разыгрывается", "Stop")
		return nil
	end
	BossLootService.SetOpen(zone, false)
	local maxHp, damage = BattleService.PlayerStats(strengthOf(player))
	local bossMax, bossDamage = BattleService.BossStats(zone)
	local fight: Fight = {
		zone = zone,
		slot = slot,
		player = player,
		boss = boss,
		active = true,
		phase = "Waking",
		hp = maxHp,
		maxHp = maxHp,
		damage = damage,
		bossHp = bossMax,
		bossMax = bossMax,
		bossDamage = bossDamage,
		nextPlayer = math.huge,
		nextBoss = math.huge,
		attacks = 0,
		result = nil,
		log = {},
	}
	fights[zone] = fight
	byPlayer[player] = fight
	player:SetAttribute("InBattle", zone)
	player:SetAttribute("BattleMaxHP", maxHp)
	CharacterGroups.Apply(player) -- D49: стены зоны теперь держат бойца
	boss.model:SetAttribute("MaxHP", bossMax)
	boss.model:SetAttribute("TargetUserId", player.UserId)
	makeBar(boss.root, "BattleBar", BossService.Height(boss) + BAR_ABOVE_BOSS, Color3.fromHex("E5484D"))
	local _, humanoid = Validate.GetLiveRoot(player)
	if humanoid then
		fight.health = { max = humanoid.MaxHealth, value = humanoid.Health }
	end
	refreshBars(fight)
	Notify.Send(player, ("%s проснулся! Бой начался"):format(bossName(zone)), "Go")
	Log.Debug("BattleService", ("%s будит босса %d (слот %d): HP %.0f, урон %.1f против HP %.0f, урон %.1f"):format(
		player.Name, zone, slot, maxHp, damage, bossMax, bossDamage))

	task.spawn(function()
		local tl = Battle.Timeline
		for _, entry in { { "Wake", tl.Wake }, { "StandUp", tl.StandUp }, { "ToCombat", tl.ToCombat } } do
			if not fight.active then
				return
			end
			BossService.SetState(boss, entry[1])
			task.wait(entry[2])
		end
		if not fight.active then
			return
		end
		BossService.SetState(boss, "Combat")
		fight.phase = "Fight"
		local now = os.clock()
		fight.nextPlayer = now + 0.3
		fight.nextBoss = now + 0.6
	end)
	task.spawn(function()
		while fight.active do
			step(fight)
			task.wait(Battle.TickSeconds)
		end
	end)
	return fight
end

-- Невидимые стены на всех границах зон коридора (вход в зону 1 … конец последней): только для бойцов.
local function buildZoneWalls()
	CharacterGroups.Register(CharacterGroups.ZoneLock)
	CharacterGroups.Register(CharacterGroups.Fighter)
	for _, group in PhysicsService:GetRegisteredCollisionGroups() do
		local collides = group.name == CharacterGroups.Fighter
		PhysicsService:CollisionGroupSetCollidable(group.name, CharacterGroups.ZoneLock, collides)
	end
	local cfg = Battle.ZoneLock
	local world = workspace:FindFirstChild("World") or workspace
	local folder = Instance.new("Folder")
	folder.Name = "BattleWalls"
	local width = (MapLayout.CorridorHalf + cfg.Overlap) * 2
	for index = 1, #GameConfig.Zones + 1 do
		local z = if index <= #GameConfig.Zones then MapLayout.ZoneStartZ(index) else MapLayout.ZonesEnd
		local wall = Instance.new("Part")
		wall.Name = "ZoneWall_" .. index
		wall.Anchored = true
		wall.CanCollide = true
		wall.CanQuery = false
		wall.CanTouch = false
		wall.CastShadow = false
		wall.Transparency = 1
		wall.Size = Vector3.new(width, cfg.Height, cfg.Thickness)
		wall.CFrame = CFrame.new(0, MapLayout.Heights.Path + cfg.Height / 2, z)
		wall.CollisionGroup = CharacterGroups.ZoneLock
		wall.Parent = folder
	end
	folder.Parent = world
end

function BattleService.Init()
	buildZoneWalls()
	BossLootService.OnTakeRequest = function(player: Player, zone: number, slot: number): boolean
		if not BossService.Get(zone) then
			return false -- у босса пока нет боя
		end
		BattleService.Begin(player, zone, slot)
		return true
	end
	TimeService.OnPhaseChanged(function(state)
		if GameTime.IsNight(state.phase) then
			for _, fight in fights do
				finish(fight, "night")
			end
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		local fight = byPlayer[player]
		if fight then
			finish(fight, "abort")
		end
	end)
end

-- Для серверных тестов.
BattleService.Handlers = {
	Begin = BattleService.Begin,
	Fight = function(zone: number): Fight?
		return fights[zone]
	end,
	FightOf = function(player: any): Fight?
		return byPlayer[player]
	end,
	Finish = finish,
	IsReturning = function(zone: number): boolean
		return returning[zone] == true
	end,
	Step = step,
	ZoneBounds = zoneBounds,
}

return BattleService

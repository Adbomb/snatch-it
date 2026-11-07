-- PvP в Судную ночь (D37, D46): клиент только просит удар (RemoteEvent PvpAttack, ЛКМ на ПК или кнопка «Удар» на
-- телефоне), сервер решает всё — фаза, Safe Zone у места появления, оглушение, перезарядка (частота фиксирована:
-- Battle.Player.AttackInterval), цель (ближайший соперник впереди в радиусе), урон от силы (формула боя с боссом).
-- HP 0 — нокаут: отброс от ударившего, 15 с лежит со звёздами над головой, не ходит, не прыгает, не бьёт и неуязвим,
-- потом встаёт на месте с полным HP. Вор с добычей проиграл — добыча сразу у владельца (TheftService.OnDefeated).
-- Эффекты (замах, попадание, нокаут) — событие PvpEffect игрокам рядом, рисует клиент (PvpController).
-- Правила — Util/PvpRules (проверяются в Lune). Бой с боссами не меняется.
-- Зависит от MoveGuard (D52), DataService, CarryService, PlotService, TheftService, TimeService, Shared/GameTime, World/MapLayout,
-- Util/*, Remotes, Config/Battle, GameConfig.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local StarterPlayer = game:GetService("StarterPlayer")

local Battle = require(ReplicatedStorage.Shared.Config.Battle)
local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local UITokens = require(ReplicatedStorage.Shared.Config.UITokens)
local Server = ServerScriptService.Server
local CarryService = require(Server.Services.CarryService)
local DataService = require(Server.Services.DataService)
local PlotService = require(Server.Services.PlotService)
local MoveGuard = require(Server.Services.MoveGuard)
local TheftService = require(Server.Services.TheftService)
local TimeService = require(Server.Services.TimeService)
local Log = require(Server.Util.Log)
local PvpRules = require(Server.Util.PvpRules)
local RateLimiter = require(Server.Util.RateLimiter)
local Validate = require(Server.Util.Validate)
local MapLayout = require(Server.World.MapLayout)

local cfg = GameConfig.Pvp
local STARS_TAG = "KnockStars"

local fighters: { [any]: PvpRules.Fighter } = {}
-- Дополнительные цели удара (роботы-охранники, D37): provider(attacker) → { { position, onHit(damage) } }.
local targetProviders: { (any) -> { any } } = {}
local limiter = RateLimiter.new(GameConfig.RateLimits.PvpAttack)
local random = Random.new()
local snareCount = 0 -- номер последнего капкана (атрибут SnareToken)

local PvpService = {}

local function isOpen(): boolean
	return GameTime.TheftPhase(GameTime.Now()) == "Open"
end

-- Safe Zone у места появления: урона нет (D37).
local function inSafe(position: Vector3): boolean
	local spawn = MapLayout.Spawn.position
	return Vector3.new(position.X - spawn.X, 0, position.Z - spawn.Z).Magnitude <= cfg.SpawnSafeRadius
end

local function strengthOf(player: any): number
	local data = DataService.GetData(player)
	return if data then data.strength or 0 else 0
end

local function publish(player: any, f: PvpRules.Fighter)
	player:SetAttribute("PvpHP", f.hp)
	player:SetAttribute("PvpMaxHP", f.maxHp)
end

local function fighter(player: any): PvpRules.Fighter
	local f = fighters[player]
	if not f then
		f = PvpRules.NewFighter(player.UserId, PvpRules.MaxHP(Battle.Player, strengthOf(player)))
		fighters[player] = f
		publish(player, f)
	end
	return f
end

-- Все игроки с участками (настоящие и тестовые).
local function participants(): { any }
	local list = {}
	for _, plot in PlotService.GetPlots() do
		if plot.owner then
			table.insert(list, plot.owner)
		end
	end
	return list
end

local function byUserId(userId: number): any
	for _, player in participants() do
		if player.UserId == userId then
			return player
		end
	end
	return nil
end

-- Эффект для клиентов рядом: kind ("Swing" | "Hit" | "Knock"), кто бил, по кому, урон.
local function effect(kind: string, attacker: any, target: any?, damage: number)
	local root = Validate.GetLiveRoot(attacker)
	local payload = { kind = kind, attacker = attacker.UserId, target = target and target.UserId, damage = damage }
	for _, player in participants() do
		local other = Validate.GetLiveRoot(player)
		if root and other and (other.Position - root.Position).Magnitude <= cfg.EffectRadius then
			Remotes.FireClient(Remotes.Names.PvpEffect, player, payload)
		end
	end
end

-- Отброс от точки from (как отброс боя с боссом, Battle.Knockback): LinearVelocity на короткое время.
local function knockback(player: any, from: Vector3)
	local root = Validate.GetLiveRoot(player)
	if not root then
		return
	end
	local away = Vector3.new(root.Position.X - from.X, 0, root.Position.Z - from.Z)
	away = if away.Magnitude > 0.01 then away.Unit else Vector3.new(0, 0, 1)
	local k = Battle.Knockback
	local attachment = Instance.new("Attachment")
	attachment.Name = "PvpKnockback"
	attachment.Parent = root
	local push = Instance.new("LinearVelocity")
	push.Name = "PvpKnockback"
	push.Attachment0 = attachment
	push.RelativeTo = Enum.ActuatorRelativeTo.World
	push.MaxForce = math.huge
	push.VectorVelocity = away * k.Speed + Vector3.new(0, k.Up, 0)
	push.Parent = root
	task.delay(k.Time, function()
		push:Destroy()
		attachment:Destroy()
	end)
end

-- Звёзды над головой оглушённого (видны всем; крутит их клиент по тегу).
local function stars(player: any, show: boolean)
	local character = player.Character
	local head = character and (character:FindFirstChild("Head") or character.PrimaryPart)
	if not head then
		return
	end
	local old = head:FindFirstChild("Etoiles")
	if old then
		old:Destroy()
	end
	if not show then
		return
	end
	local t = UITokens.Pvp
	local gui = Instance.new("BillboardGui")
	gui.Name = "Etoiles"
	gui.Size = UDim2.fromScale(t.Stars.X, t.Stars.Y)
	gui.StudsOffset = Vector3.new(0, t.StarsLift, 0)
	gui.MaxDistance = cfg.EffectRadius
	gui.LightInfluence = 0
	local label = Instance.new("TextLabel")
	label.Name = "Texte"
	label.BackgroundTransparency = 1
	label.Size = UDim2.fromScale(1, 1)
	label.Text = "★ ★ ★"
	label.TextScaled = true
	label.FontFace = Font.new("rbxasset://fonts/families/GothamSSm.json", Enum.FontWeight.Heavy)
	label.TextColor3 = t.StarColor
	label.TextStrokeTransparency = 0.2
	label.Parent = gui
	gui.Parent = head
	CollectionService:AddTag(gui, STARS_TAG)
end

local function setFrozen(player: any, frozen: boolean)
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not humanoid then
		return
	end
	if frozen then
		humanoid.WalkSpeed = 0
		humanoid.JumpHeight = 0
	else
		humanoid.JumpHeight = StarterPlayer.CharacterJumpHeight
		CarryService.RefreshSpeed(player)
	end
end

local function release(player: any)
	MoveGuard.Unpin(player)
	if player:GetAttribute("Snared") then
		player:SetAttribute("Snared", nil)
	end
end

local function recover(player: any)
	local f = fighters[player]
	if f then
		f.knockedUntil = 0
		f.hp = f.maxHp
		publish(player, f)
	end
	player:SetAttribute("Knocked", nil)
	release(player)
	stars(player, false)
	setFrozen(player, false)
end

-- HP 0: нокаут (D37).
local function knockOut(target: any, from: Vector3, attacker: any?)
	release(target) -- капкан снимается, начинается обычное оглушение (таймеры не складываются, D37)
	target:SetAttribute("Knocked", true)
	local f = fighters[target]
	local untilAt = f and f.knockedUntil or 0
	-- подъём назначается первым: что бы ни случилось дальше, игрок не останется лежать навсегда
	task.delay(cfg.KnockSeconds, function()
		-- встаёт, если за это время его не нокаутировали заново (неуязвим, поэтому не должны)
		local now = fighters[target]
		if not now or now.knockedUntil == untilAt then
			recover(target)
		end
	end)
	local ok, err = pcall(TheftService.OnDefeated, target) -- добыча вора — сразу владельцу
	if not ok then
		Log.Warn("PvpService", "возврат добычи после нокаута: " .. tostring(err))
	end
	knockback(target, from)
	setFrozen(target, true)
	stars(target, true)
	effect("Knock", attacker or target, target, 0)
	Log.Debug(
		"PvpService",
		("%s нокаутирован (%s)"):format(target.Name, if attacker then attacker.Name else "защита")
	)
end

-- Запрос удара от клиента (без аргументов: цель выбирает сервер).
local function tryAttack(player: any)
	if not limiter:Allow(player) then
		return
	end
	local root, humanoid = Validate.GetLiveRoot(player)
	if not root or not humanoid then
		return
	end
	local now = os.clock()
	local f = fighter(player)
	local interval = Battle.Player.AttackInterval - cfg.SwingTolerance -- клиент шлёт не чаще AttackInterval; запас на сеть
	if PvpRules.CanSwing(f, now, isOpen(), inSafe(root.Position), interval) then
		return
	end
	if player:GetAttribute("Snared") then
		return -- в капкане не бьют (D37)
	end
	f.lastAttack = now
	local candidates = {}
	for _, other in participants() do
		if other ~= player then
			local r, h = Validate.GetLiveRoot(other)
			if r and h then
				table.insert(candidates, {
					id = other.UserId,
					position = r.Position,
					knocked = PvpRules.IsKnocked(fighter(other), now),
					safe = inSafe(r.Position),
					alive = h.Health > 0,
				})
			end
		end
	end
	local targetId = PvpRules.PickTarget(root.Position, root.CFrame.LookVector, candidates, cfg.Range, cfg.FrontDot)
	local target = targetId and byUserId(targetId)
	local damageOut = PvpRules.Damage(Battle.Player, strengthOf(player), Battle.DamageSpread, random:NextNumber(-1, 1))
	if not target then
		-- робот-охранник ближе любого игрока? (вор может его сломать, D37)
		local flatLook = Vector3.new(root.CFrame.LookVector.X, 0, root.CFrame.LookVector.Z)
		local best, bestDistance = nil, cfg.Range
		for _, provider in targetProviders do
			for _, extra in provider(player) do
				local offset = extra.position - root.Position
				local flat = Vector3.new(offset.X, 0, offset.Z)
				local dot = if flat.Magnitude > 1e-3 and flatLook.Magnitude > 1e-3
					then flat.Unit:Dot(flatLook.Unit)
					else 1
				if offset.Magnitude <= bestDistance and dot >= cfg.FrontDot then
					best, bestDistance = extra, offset.Magnitude
				end
			end
		end
		effect("Swing", player, nil, 0)
		if best then
			best.onHit(damageOut)
		end
		return
	end
	local tf = fighter(target)
	local dealt, ko = PvpRules.Hit(tf, damageOut, now, cfg.KnockSeconds)
	publish(target, tf)
	effect("Hit", player, target, dealt)
	if ko then
		knockOut(target, root.Position, player)
	end
end

-- Новая Судная ночь — у всех полный HP по текущей силе; после неё — PvP-состояния сбрасываются (лежачие встают
-- по своему таймеру).
local function reset()
	for player, f in fighters do
		if not PvpRules.IsKnocked(f, os.clock()) then
			fighters[player] = nil
			player:SetAttribute("PvpHP", nil)
			player:SetAttribute("PvpMaxHP", nil)
		end
	end
end

-- Урон от защиты музея (D37): ловушка, лазер, робот. amount — HP; HP 0 — нокаут, как от удара.
function PvpService.DamagePlayer(target: any, amount: number, from: Vector3)
	if not isOpen() then
		return
	end
	local tf = fighter(target)
	local now = os.clock()
	local dealt, ko = PvpRules.Hit(tf, amount, now, cfg.KnockSeconds)
	if dealt <= 0 then
		return
	end
	publish(target, tf)
	effect("Hit", target, target, dealt)
	if ko then
		knockOut(target, from, nil)
	end
end

-- Максимальный HP игрока в PvP (для урона долей HP).
function PvpService.MaxHP(player: any): number
	return fighter(player).maxHp
end

-- Капкан (D37): seconds обездвижен и не бьёт, по нему можно бить; нокаут снимает капкан.
function PvpService.Snare(target: any, seconds: number): boolean
	if target:GetAttribute("Knocked") or target:GetAttribute("Snared") then
		return false -- уже лежит или пойман: капкан не тратится
	end
	snareCount += 1
	local token = snareCount
	target:SetAttribute("Snared", true)
	target:SetAttribute("SnareToken", token)
	setFrozen(target, true)
	MoveGuard.Pin(target) -- из капкана не уйти даже читом: дальше PinRadius сервер вернёт (D52)
	task.delay(seconds, function()
		-- снимает только свой капкан: после нокаута и нового капкана старый таймер не освобождает раньше срока
		if
			target:GetAttribute("SnareToken") == token
			and target:GetAttribute("Snared")
			and not target:GetAttribute("Knocked")
		then
			release(target)
			setFrozen(target, false)
		end
	end)
	return true
end

-- Ловушка (вариант Slow): скорость × factor на seconds.
function PvpService.Slow(target: any, factor: number, seconds: number)
	local character = target.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not humanoid or target:GetAttribute("Knocked") or target:GetAttribute("Snared") then
		return
	end
	-- замедление учитывает CarryService.RefreshSpeed, пока не истечёт (пересчёт скорости его не снимает)
	local untilAt = workspace:GetServerTimeNow() + seconds
	target:SetAttribute("SlowFactor", factor)
	target:SetAttribute("SlowUntil", untilAt)
	CarryService.RefreshSpeed(target)
	task.delay(seconds, function()
		if target:GetAttribute("SlowUntil") == untilAt then
			target:SetAttribute("SlowFactor", nil)
			target:SetAttribute("SlowUntil", nil)
			CarryService.RefreshSpeed(target)
		end
	end)
end

-- Дополнительные цели удара (роботы-охранники).
function PvpService.AddTargetProvider(provider: (any) -> { any })
	table.insert(targetProviders, provider)
end

function PvpService.Init()
	Remotes.Get(Remotes.Names.PvpAttack).OnServerEvent:Connect(tryAttack)
	TimeService.OnPhaseChanged(function(state, previous)
		if state.phase == "DoomNight" or (previous and previous.phase == "DoomNight") then
			reset()
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		fighters[player] = nil
	end)
	-- Новый персонаж (упал в пустоту и т. п.) — без нокаута и капкана: прыжок и скорость как обычно.
	local function watch(player: Player)
		player.CharacterAdded:Connect(function()
			if player:GetAttribute("Knocked") or player:GetAttribute("Snared") then
				recover(player)
			end
		end)
	end
	Players.PlayerAdded:Connect(watch)
	for _, player in Players:GetPlayers() do
		watch(player)
	end
end

-- Для серверных тестов: тот же обработчик, что у RemoteEvent, и доступ к состоянию.
PvpService.Handlers = {
	Attack = tryAttack,
	Fighter = fighter,
	Recover = recover,
	Snare = PvpService.Snare,
	Reset = reset,
}

return PvpService

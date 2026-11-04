-- PvP в Судную ночь (D37, D46): клиент только просит удар (RemoteEvent PvpAttack, ЛКМ на ПК или кнопка «Удар» на
-- телефоне), сервер решает всё — фаза, Safe Zone у места появления, оглушение, перезарядка (частота фиксирована:
-- Battle.Player.AttackInterval), цель (ближайший соперник впереди в радиусе), урон от силы (формула боя с боссом).
-- HP 0 — нокаут: отброс от ударившего, 15 с лежит со звёздами над головой, не ходит, не прыгает, не бьёт и неуязвим,
-- потом встаёт на месте с полным HP. Вор с добычей проиграл — добыча сразу у владельца (TheftService.OnDefeated).
-- Эффекты (замах, попадание, нокаут) — событие PvpEffect игрокам рядом, рисует клиент (PvpController).
-- Правила — Util/PvpRules (проверяются в Lune). Бой с боссами не меняется.
-- Зависит от DataService, CarryService, PlotService, TheftService, TimeService, Shared/GameTime, World/MapLayout,
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
local limiter = RateLimiter.new(GameConfig.RateLimits.PvpAttack)
local random = Random.new()

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

local function recover(player: any)
	local f = fighters[player]
	if f then
		f.knockedUntil = 0
		f.hp = f.maxHp
		publish(player, f)
	end
	player:SetAttribute("Knocked", nil)
	stars(player, false)
	setFrozen(player, false)
end

-- HP 0: нокаут (D37).
local function knockOut(target: any, from: Vector3, attacker: any)
	target:SetAttribute("Knocked", true)
	TheftService.OnDefeated(target) -- добыча вора — сразу владельцу
	knockback(target, from)
	setFrozen(target, true)
	stars(target, true)
	effect("Knock", attacker, target, 0)
	local f = fighters[target]
	local untilAt = f and f.knockedUntil or 0
	task.delay(cfg.KnockSeconds, function()
		-- встаёт, если за это время его не нокаутировали заново (неуязвим, поэтому не должны)
		local now = fighters[target]
		if not now or now.knockedUntil == untilAt then
			recover(target)
		end
	end)
	Log.Debug("PvpService", ("%s нокаутировал %s"):format(attacker.Name, target.Name))
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
	if PvpRules.CanSwing(f, now, isOpen(), inSafe(root.Position), Battle.Player.AttackInterval) then
		return
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
	if not target then
		effect("Swing", player, nil, 0)
		return
	end
	local tf = fighter(target)
	local damage = PvpRules.Damage(Battle.Player, strengthOf(player), Battle.DamageSpread, random:NextNumber(-1, 1))
	local dealt, ko = PvpRules.Hit(tf, damage, now, cfg.KnockSeconds)
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
end

-- Для серверных тестов: тот же обработчик, что у RemoteEvent, и доступ к состоянию.
PvpService.Handlers = {
	Attack = tryAttack,
	Fighter = fighter,
	Recover = recover,
	Reset = reset,
}

return PvpService

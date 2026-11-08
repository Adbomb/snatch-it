-- Поимка «Ловибум» (D55) — сервер. «Поймать» у существа (подсказка BossLootService) → проверки начала: день, у босса
-- есть бой (или тестовый режим Studio), босс спит и свободен, существо на месте и не закреплено, игрок рядом, не в паузе
-- у этого босса, руки пустые, не в бою и не в нокауте, жив, обучение пройдено, есть Ловибум уровня босса. Затем босс
-- и слот закреплены за ловящим (подсказки у босса выключены), существо переходит в режим мини-игры (атрибуты корня —
-- клиенты считают его движение той же функцией Shared/CreatureMotion), камеру поимки считает сервер
-- (Shared/CatchThrow.Frame) и присылает ловящему. Бросок (CatchAction "Throw", kind, жест, время отпускания): клиент
-- присылает только жест — направление, скорость и длину смахивания; точке прилёта от клиента сервер не верит. Порядок:
-- жест (короткий, медленный, вбок, испорченный — не бросок, Ловибум не тратится) → проверки сессии и времени
-- (Shared/CatchRules) → Ловибум списывается в профиле → точку прилёта сервер считает сам по жесту и камере поимки
-- (CatchThrow.Aim), попадание — она внутри кольца вокруг существа в момент прилёта (та же функция движения, с
-- уклонениями) → шанс (база редкости × бонус вида; размер кольца на шанс не влияет). Итог видят все рядом
-- (CatchEffect), прицел — только ловящий (CatchState). Поимка — существо в закрытом Ловибуме на месте (Hidden), после
-- трёх покачиваний начинается бой (BattleService, слот уже закреплён); поражение и прерывание боя — существо снова на
-- месте (BossLootService.Release). Конец без поимки (три неудачи, кончились Ловибумы уровня, «Уйти», ночь, выход, гибель,
-- нокаут, бездействие, сторож) — существо убегает и возвращается, босс сразу свободен, у игрока — личная пауза
-- FailPause у этого босса. Учебная поимка (TutorialService) — личное существо: броски бесплатные, первое попадание —
-- захват, без паузы и лимита, ночь не прерывает.
-- Зависит от BattleService, BossService, BossLootService, DataService, ItemRegistry, ShopService, TimeService,
-- Shared/CatchRules, Shared/CatchThrow, Shared/CreatureMotion, Shared/GameTime, Shared/TutorialRules, Remotes, Config,
-- Util/RateLimiter, Util/Notify, Util/Validate, Util/Log.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local CatchRules = require(ReplicatedStorage.Shared.CatchRules)
local CatchThrow = require(ReplicatedStorage.Shared.CatchThrow)
local CreatureMotion = require(ReplicatedStorage.Shared.CreatureMotion)
local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local GameTime = require(ReplicatedStorage.Shared.GameTime)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local TutorialRules = require(ReplicatedStorage.Shared.TutorialRules)
local Server = ServerScriptService.Server
local BattleService = require(Server.Services.BattleService)
local BossLootService = require(Server.Services.BossLootService)
local BossService = require(Server.Services.BossService)
local DataService = require(Server.Services.DataService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local ShopService = require(Server.Services.ShopService)
local TimeService = require(Server.Services.TimeService)
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)
local RateLimiter = require(Server.Util.RateLimiter)
local Validate = require(Server.Util.Validate)

local Catch = GameConfig.Catch
local G = Catch.Game
local limiter = RateLimiter.new(GameConfig.RateLimits.Catch)
local random = Random.new()
local forcedRoll: number? = nil -- серверные тесты: исход шанса (0 — поймано, 0.999 — побег)

-- Цель поимки: существо у босса или личное учебное (TutorialService).
export type Target = {
	boss: number,
	slot: number, -- 0 — учебное
	uid: string,
	itemId: string,
	rarity: string,
	part: BasePart,
	home: CFrame, -- низ места
	height: number,
	params: CreatureMotion.Params,
	tutorial: boolean,
	onCaught: ((player: any) -> ())?, -- учебная: что делать после поимки (вместо обычного боя)
	onEnd: ((player: any, reason: string) -> ())?,
}

type Active = {
	player: any,
	session: CatchRules.Session,
	target: Target,
	ending: boolean,
	died: RBXScriptConnection?,
	camera: CFrame, -- камера поимки (CatchThrow.Frame): по ней сервер считает траекторию броска
	stage: Vector3, -- центр места мини-игры
	last: { outcome: string, aim: Vector3 }?, -- последний бросок (серверные тесты)
}

local active: { [any]: Active } = {} -- по игроку
local byBoss: { [number]: Active } = {} -- обычная поимка: босс закреплён за ловящим
local pauses: CatchRules.Pauses = {}

local CatchService = {}

local function now(): number
	return workspace:GetServerTimeNow()
end

local function setAttrs(part: BasePart, mode: string?, since: number?, face: number?, anchor: number?)
	part:SetAttribute("CatchMode", mode)
	part:SetAttribute("CatchSince", since)
	part:SetAttribute("CatchFace", face)
	part:SetAttribute("CatchAnchor", anchor)
end

-- Игроки рядом с точкой (видят броски, сеть, захват и побег).
local function nearby(position: Vector3): { Player }
	local out = {}
	for _, other in Players:GetPlayers() do
		local root = Validate.GetLiveRoot(other)
		if root and (root.Position - position).Magnitude <= G.EffectRadius then
			table.insert(out, other)
		end
	end
	return out
end

local function effect(target: Target, payload: { [string]: any }, catcher: any)
	payload.boss = target.boss
	payload.slot = target.slot
	payload.uid = target.uid
	payload.part = target.part
	if target.tutorial then
		-- учебное существо видит только ученик
		Remotes.FireClient(Remotes.Names.CatchEffect, catcher, payload)
		return
	end
	local sent = false
	for _, other in nearby(target.home.Position) do
		Remotes.FireClient(Remotes.Names.CatchEffect, other, payload)
		sent = sent or other == catcher
	end
	if not sent then
		Remotes.FireClient(Remotes.Names.CatchEffect, catcher, payload)
	end
end

local function sendState(a: Active?, player: any)
	if not a then
		Remotes.FireClient(Remotes.Names.CatchState, player, nil)
		return
	end
	local s, t = a.session, a.target
	Remotes.FireClient(Remotes.Names.CatchState, player, {
		state = s.state,
		boss = t.boss,
		slot = t.slot,
		uid = t.uid,
		itemId = t.itemId,
		rarity = t.rarity,
		part = t.part,
		since = s.since,
		throws = s.throws,
		max = if s.tutorial then 0 else G.MaxThrows,
		readyAt = s.readyAt,
		face = t.params.face,
		camera = a.camera,
		stage = a.stage,
		tutorial = s.tutorial,
		circle = if s.tutorial then Catch.Tutorial.CircleFactor else 1,
	})
end

-- Камера поимки не за стеной: луч от центра места к камере; видимое препятствие — камера ближе (на Pad перед ним, не
-- ближе Near). Существо, персонажи и предметы у боссов не мешают, невидимые барьеры — тоже. Считается один раз.
local function catchCamera(target: Target): (CFrame, Vector3)
	local camera, stage = CatchThrow.Frame(target.home, target.params, target.height)
	local c = G.Camera
	local ignore: { Instance } = { target.part }
	for _, p in Players:GetPlayers() do
		if p.Character then
			table.insert(ignore, p.Character)
		end
	end
	local world = workspace:FindFirstChild("World")
	local items = world and world:FindFirstChild("Items")
	if items then
		table.insert(ignore, items)
	end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	local ray = camera.Position - stage
	for _ = 1, 8 do
		params.FilterDescendantsInstances = ignore
		local hit = workspace:Raycast(stage, ray, params)
		if not hit then
			return camera, stage
		end
		if hit.Instance:IsA("BasePart") and hit.Instance.Transparency < 0.9 then
			local flat = Vector3.new(ray.X, 0, ray.Z).Magnitude
			local near = math.max(flat * (hit.Distance / ray.Magnitude) - c.Pad, c.Near)
			return CatchThrow.Frame(target.home, target.params, target.height, near)
		end
		table.insert(ignore, hit.Instance)
	end
	return camera, stage
end

-- Поза существа цели в момент time (мини-игра) и центр для попадания.
local function centerAt(target: Target, time: number): Vector3
	local pose = CreatureMotion.Pose(target.params, time)
	return CreatureMotion.Center(target.home, pose, target.height)
end

-- Закончить мини-игру. reason: "Caught" — поймано (дальше бой); иначе — без поимки: побег, пауза, босс свободен.
local function finish(a: Active, reason: string)
	if a.ending then
		return
	end
	a.ending = true
	local player, target, session = a.player, a.target, a.session
	active[player] = nil
	if byBoss[target.boss] == a then
		byBoss[target.boss] = nil
	end
	if a.died then
		a.died:Disconnect()
	end
	if player.Parent ~= nil or typeof(player) ~= "Instance" then
		player:SetAttribute("Catching", nil)
	end
	sendState(nil, player)
	local part = target.part
	if reason == "Caught" then
		effect(target, { kind = "End", user = player.UserId, reason = reason, caught = true }, player)
		if target.onCaught then
			target.onCaught(player)
			return
		end
		setAttrs(part, "Hidden", now())
		-- бой: слот уже закреплён за ловящим (BossLootService.Reserve в начале поимки)
		if BossService.Get(target.boss) then
			local fight = BattleService.Begin(player, target.boss, target.slot, { caught = true })
			if not fight then
				BossLootService.Release(target.boss, target.slot)
				BossLootService.SetOpen(target.boss, true)
			end
		elseif BossLootService.FreeTakeAllowed() then
			-- тестовый режим Studio: у босса нет боя — поймал, значит забрал
			if not BossLootService.Award(target.boss, target.slot, player) then
				BossLootService.Release(target.boss, target.slot)
			end
			BossLootService.SetOpen(target.boss, true)
		end
		return
	end
	if not session.tutorial then
		CatchRules.SetPause(pauses, player.UserId, target.boss, now())
	end
	effect(target, { kind = "End", user = player.UserId, reason = reason, caught = false }, player)
	Log.Debug(
		"CatchService",
		("%s: поимка у босса %d закончилась (%s)"):format(player.Name, target.boss, reason)
	)
	-- существо убегает недалеко и возвращается (если слот ещё его)
	if part.Parent then
		local t = now()
		setAttrs(part, "Flee", t, target.params.face, session.since)
		task.delay(G.FleeTime + G.Blend + 0.2, function()
			if part.Parent and part:GetAttribute("CatchMode") == "Flee" and part:GetAttribute("CatchSince") == t then
				setAttrs(part, nil)
			end
		end)
	end
	if not session.tutorial then
		BossLootService.Release(target.boss, target.slot)
		BossLootService.SetOpen(target.boss, true)
	end
	if target.onEnd then
		target.onEnd(player, reason)
	end
end

-- Отказ начала (сообщение) или nil. Для обычной поимки у босса.
local function refusal(player: any, boss: number): string?
	local data = DataService.GetData(player)
	if not data then
		return "Профиль ещё не загружен"
	end
	if TutorialRules.IsActive(data) then
		return "Сначала пройдите обучение"
	end
	if active[player] then
		return "Вы уже ловите"
	end
	if GameTime.IsNight(TimeService.Current().phase) then
		return "Ночью коридор закрыт"
	end
	if not BossService.Get(boss) and not BossLootService.FreeTakeAllowed() then
		return "У этого босса пока нет боя"
	end
	if byBoss[boss] then
		return ("Босс занят: ловит %s"):format(byBoss[boss].player.Name)
	end
	if BattleService.Busy(boss) or not BossLootService.IsOpen(boss) then
		return "Босс занят: дождитесь конца боя"
	end
	local left = CatchRules.PauseLeft(pauses, player.UserId, boss, now())
	if left > 0 then
		return ("Существа этого босса насторожены: ещё %d с"):format(math.ceil(left))
	end
	if ItemRegistry.GetCarriedBy(player) then
		return "Руки заняты — сначала бросьте предмет (G)"
	end
	if BattleService.InBattle(player) then
		return "Вы в бою"
	end
	if player:GetAttribute("Knocked") then
		return "Вы в нокауте"
	end
	if CatchRules.StockOfLevel(DataService.Lovibums(player), boss) < 1 then
		return ("Нужен Ловибум уровня %d — купите в «Магазине»"):format(boss)
	end
	return nil
end

-- Цель — существо в слоте босса (сервер считает его положение той же функцией, что клиенты).
local function slotTarget(boss: number, slot: number): Target?
	local uid, part = BossLootService.SlotItem(boss, slot)
	if not uid or not part then
		return nil
	end
	local itemId = part:GetAttribute("ItemId") :: string
	local def = Items[itemId]
	local home = part:GetAttribute("Home")
	if not def or typeof(home) ~= "CFrame" then
		return nil
	end
	return {
		boss = boss,
		slot = slot,
		uid = uid,
		itemId = itemId,
		rarity = def.rarity,
		part = part,
		home = home,
		height = def.size.Y,
		params = {
			seed = CreatureMotion.SeedOf(uid),
			radius = CreatureMotion.WanderRadius(boss),
			scale = CreatureMotion.ScaleOf(def.size),
			mode = "Wander",
			drop = part:GetAttribute("Drop") :: number?,
		},
		tutorial = false,
	}
end

-- Начать мини-игру с целью target (проверки обычной поимки — уже сделаны). Возвращает сессию.
local function start(player: any, target: Target): Active?
	local root = Validate.GetLiveRoot(player)
	if not root then
		return nil
	end
	local t = now()
	local here = centerAt(target, t)
	if (root.Position - here).Magnitude > G.PromptDistance + GameConfig.DistanceTolerance + target.params.radius then
		Notify.Send(player, "Подойдите ближе", "Stop")
		return nil
	end
	-- лицом к ловящему (в осях места): поворот вокруг вертикали
	local rel = target.home:PointToObjectSpace(root.Position)
	target.params.face = math.atan2(-rel.X, -rel.Z)
	target.params.mode = "Catch"
	target.params.since = t
	local camera, stage = catchCamera(target)
	local a: Active = {
		player = player,
		session = CatchRules.NewSession(
			player.UserId,
			target.boss,
			target.slot,
			target.uid,
			target.rarity,
			t,
			target.tutorial
		),
		target = target,
		ending = false,
		died = nil,
		camera = camera,
		stage = stage,
		last = nil,
	}
	active[player] = a
	if not target.tutorial then
		byBoss[target.boss] = a
	end
	setAttrs(target.part, "Catch", t, target.params.face)
	player:SetAttribute("Catching", target.boss)
	local _, humanoid = Validate.GetLiveRoot(player)
	if humanoid then
		a.died = humanoid.Died:Connect(function()
			finish(a, "Died")
		end)
	end
	sendState(a, player)
	effect(target, { kind = "Start", user = player.UserId }, player)
	Log.Debug(
		"CatchService",
		("%s ловит %s у босса %d (слот %d)%s"):format(
			player.Name,
			target.itemId,
			target.boss,
			target.slot,
			if target.tutorial then " — обучение" else ""
		)
	)
	return a
end

-- «Поймать» у существа в слоте slot босса boss. true — мини-игра началась.
function CatchService.Begin(player: any, boss: number, slot: number): boolean
	local reason = refusal(player, boss)
	if reason then
		Notify.Send(player, reason, "Stop")
		return false
	end
	local target = slotTarget(boss, slot)
	if not target then
		Notify.Send(player, "Здесь уже пусто", "Stop")
		return false
	end
	if not BossLootService.Reserve(boss, slot, player) then
		Notify.Send(player, "Это существо уже ловят", "Stop")
		return false
	end
	BossLootService.SetOpen(boss, false)
	if not start(player, target) then
		BossLootService.Release(boss, slot)
		BossLootService.SetOpen(boss, true)
		return false
	end
	return true
end

-- Учебная поимка (TutorialService): личное существо, без Ловибумов и паузы. true — началась.
function CatchService.BeginTutorial(player: any, target: Target): boolean
	if active[player] then
		return false
	end
	target.tutorial = true
	return start(player, target) ~= nil
end

local function onThrow(player: any, kind: any, gesture: any, release: any)
	local a = active[player]
	if not a or a.ending then
		return
	end
	local s, target = a.session, a.target
	local t = now()
	-- жест: не бросок — ничего не списано (клиент такие не шлёт: подделка или сбой)
	local g, why = CatchThrow.Parse(gesture)
	if not g then
		Log.Debug("CatchService", ("%s: жест не принят (%s)"):format(player.Name, tostring(why)))
		return
	end
	local stock = if s.tutorial then 0 else CatchRules.Stock(DataService.Lovibums(player), target.boss, kind)
	local reason = CatchRules.CheckThrow(s, t, kind, stock, release)
	if reason then
		if reason ~= "Подождите" then
			Notify.Send(player, reason, "Stop")
		end
		sendState(a, player)
		return
	end
	-- сначала Ловибум списан (D55: до результата), потом попадание и шанс
	if not s.tutorial then
		if not DataService.SpendLovibum(player, target.boss, kind) then
			Notify.Send(player, "Ловибумы этого вида кончились", "Stop")
			sendState(a, player)
			return
		end
		DataService.RequestSave(player)
		ShopService.Sync(player)
	end
	-- точка прилёта — по жесту и камере поимки (сервер считает сам), существо — где оно в момент прилёта
	local aim = CatchThrow.Aim(a.camera, a.stage, g)
	local arrival = release + G.FlightTime
	local center = centerAt(target, arrival)
	local factor = if s.tutorial then Catch.Tutorial.CircleFactor else 1
	local radius = CatchRules.CircleRadius(arrival, s.since, target.params.scale, factor)
	local hit = CatchRules.IsHit(aim, center, radius)
	local chance = CatchRules.Chance(target.rarity, if s.tutorial then "Boom" else kind)
	local outcome = CatchRules.Outcome(s, hit, chance, forcedRoll or random:NextNumber())
	CatchRules.AfterThrow(s, outcome, release)
	a.last = { outcome = outcome, aim = aim }
	effect(target, {
		kind = "Throw",
		user = player.UserId,
		lovibum = if s.tutorial then "Boom" else kind,
		aim = aim,
		center = center,
		release = release,
		arrival = arrival,
		outcome = outcome,
	}, player)
	sendState(a, player)
	Log.Debug(
		"CatchService",
		("%s: бросок %s — %s (круг %.2f, промах %.2f, шанс %.0f%%)"):format(
			player.Name,
			tostring(kind),
			outcome,
			radius,
			(aim - center).Magnitude,
			chance * 100
		)
	)
	if outcome == "Caught" then
		task.delay(G.FlightTime + G.CaptureTime, function()
			if active[player] == a then
				finish(a, "Caught")
			end
		end)
	elseif s.state == "Over" then
		task.delay(G.FlightTime + G.CaptureTime + G.EscapeRest, function()
			if active[player] == a then
				finish(a, "Throws")
			end
		end)
	end
end

local function onAction(player: any, action: any, ...: any)
	if not limiter:Allow(player) then
		return
	end
	if action == "Throw" then
		onThrow(player, ...)
	elseif action == "Leave" then
		local a = active[player]
		if a and a.session.state == "Aim" then
			finish(a, "Leave")
		end
	end
end

-- Идёт ли у игрока поимка (магазин закрыт).
function CatchService.IsCatching(player: any): boolean
	return active[player] ~= nil
end

-- Закреплён ли босс за чьей-то поимкой.
function CatchService.IsBusy(boss: number): boolean
	return byBoss[boss] ~= nil
end

-- Прервать поимку игрока (выход, обучение, тесты).
function CatchService.Abort(player: any, reason: string)
	local a = active[player]
	if a then
		finish(a, reason)
	end
end

-- Сторож: бездействие, слишком долгая сессия, кончились Ловибумы, нокаут, игрок пропал.
local function watch()
	local t = now()
	for player, a in active do
		if a.ending then
			continue
		end
		local stockOfLevel = if a.session.tutorial
			then 0
			else CatchRules.StockOfLevel(DataService.Lovibums(player) or {}, a.target.boss)
		local reason = CatchRules.ShouldEnd(a.session, t, stockOfLevel)
		if not reason and not a.session.tutorial and player:GetAttribute("Knocked") then
			reason = "Knocked"
		end
		if not reason and (not a.target.part.Parent or (typeof(player) == "Instance" and player.Parent == nil)) then
			reason = "Gone"
		end
		if reason then
			finish(a, reason)
		end
	end
end

function CatchService.Init()
	Remotes.Get(Remotes.Names.CatchAction).OnServerEvent:Connect(onAction)
	ShopService.IsCatching = CatchService.IsCatching
	BattleService.IsCatchBusy = CatchService.IsBusy
	BossLootService.OnTakeRequest = function(player: Player, boss: number, slot: number): boolean
		CatchService.Begin(player, boss, slot)
		return true
	end
	TimeService.OnPhaseChanged(function(state)
		if GameTime.IsNight(state.phase) then
			for _, a in active do
				if not a.session.tutorial then
					finish(a, "Night")
				end
			end
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		CatchService.Abort(player, "Leave")
	end)
	task.spawn(function()
		while true do
			task.wait(0.5)
			local ok, err = pcall(watch)
			if not ok then
				Log.Warn("CatchService", "сторож: " .. tostring(err))
			end
		end
	end)
end

-- Для серверных тестов.
CatchService.Handlers = {
	Action = onAction,
	Active = function(player: any): Active?
		return active[player]
	end,
	Pauses = function(): CatchRules.Pauses
		return pauses
	end,
	Watch = watch,
	Finish = finish,
	CenterAt = centerAt,
	SetRoll = function(value: number?)
		forcedRoll = value
	end,
}

return CatchService

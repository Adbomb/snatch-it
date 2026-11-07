-- Проверка невозможных перемещений на сервере (D52). Персонажем управляет клиент, поэтому читер может телепортироваться
-- или летать; сервер это видит по позиции корня. Step(player) — «копилка» пути по горизонтали: пополняется со скоростью
-- Humanoid (её ставит сервер) × Tolerance, ёмкость — Slack + скорость × Burst (лаги и рывок после зависания сети),
-- смещение её тратит; ушла в минус — перемещение невозможное. Постоянно бежать быстрее Tolerance × скорость нельзя,
-- накопить стоянием на дальний прыжок — не больше ёмкости. Полёт: выше прыжка над полом (под стопой — коробка FootSize,
-- край галереи и ступень — пол; у фермы TrussPart — лазание) дольше HoverSeconds, отсчёт сбрасывает только пол
-- (покачивание вверх-вниз не спасает), падение (опускание больше FallStep за проверку) нарушением не считается.
-- Переносы сервером — только Teleport: путь до точки переноса проверяется как обычно (если игрока проверяли только что —
-- иначе отметки нет), нарушение вернёт следующий Step; в новой точке — отметка и TransferGrace секунд, когда запоздавшие
-- пакеты клиента могут вернуть точку до переноса (её не засчитывают; любую третью — засчитывают). TransferredWithin —
-- защите: дальний скачок — перенос сервером, а не прыжок. Новый персонаж (возрождение) — новая отметка. Pin: игрок стоит
-- на месте (капкан) — точка капкана переносом не меняется. Никаких банов: нарушения — в лог и в атрибут игрока
-- MoveViolations; при GameConfig.MoveGuard.Enforce = false (режим логирования, решение владельца 2026-11-07) капкан не
-- возвращает, а кражу не срывает и TheftService (Enforced()).
-- Зависит от GameConfig, Util/Validate, Util/Log.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local StarterPlayer = game:GetService("StarterPlayer")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Log = require(ServerScriptService.Server.Util.Log)
local Validate = require(ServerScriptService.Server.Util.Validate)

local cfg = GameConfig.MoveGuard

type Mark = {
	root: BasePart,
	position: Vector3,
	at: number,
	speed: number,
	budget: number, -- сколько ещё можно пройти по горизонтали, стадов
	graceUntil: number, -- до этого времени после переноса сервером точку до переноса не засчитывать
	graceFrom: Vector3?, -- точка до переноса
	airSince: number?, -- с какого времени выше прыжка над полом
	owed: string?, -- нарушение до переноса сервером: вернёт следующий Step
}
type Pin = { position: Vector3, warned: boolean }

local MoveGuard = {}

local marks: { [any]: Mark } = {}
local pins: { [any]: Pin } = {}
local transfers: { [any]: number } = {} -- игрок → когда его последний раз перенёс сервер

local function flat(v: Vector3): number
	return Vector3.new(v.X, 0, v.Z).Magnitude
end

local function capacity(speed: number): number
	return cfg.Slack + speed * cfg.Burst
end

local function fresh(root: BasePart, humanoid: Humanoid): Mark
	return {
		root = root,
		position = root.Position,
		at = os.clock(),
		speed = humanoid.WalkSpeed,
		budget = cfg.Slack, -- с места — только запас; дальше копится со временем
		graceUntil = 0,
		graceFrom = nil,
		airSince = nil,
		owed = nil,
	}
end

-- Режим: true — нарушение срывает кражу и капкан возвращает; false — только лог (D52).
function MoveGuard.Enforced(): boolean
	return cfg.Enforce == true
end

-- Отметка: отсюда и с этого момента считается путь (например, кража началась).
function MoveGuard.Mark(player: any)
	local root, humanoid = Validate.GetLiveRoot(player)
	marks[player] = if root and humanoid then fresh(root, humanoid) else nil
end

local function violation(player: any, what: string)
	Log.Warn(
		"MoveGuard",
		("%s: невозможное перемещение — %s%s"):format(
			tostring(player.Name),
			what,
			if MoveGuard.Enforced() then "" else " (режим логирования)"
		)
	)
	player:SetAttribute("MoveViolations", (player:GetAttribute("MoveViolations") or 0) + 1)
end

-- Высота прыжка персонажа: по свойствам Humanoid и настройкам игры (капкан ставит JumpHeight = 0 — порог не падает).
local function jumpHeight(humanoid: Humanoid): number
	local height = math.max(humanoid.JumpHeight, StarterPlayer.CharacterJumpHeight)
	if humanoid.UseJumpPower then
		local power = math.max(humanoid.JumpPower, StarterPlayer.CharacterJumpPower)
		height = math.max(height, power * power / (2 * workspace.Gravity))
	end
	return height
end

local function castParams(root: BasePart): RaycastParams
	local ignore: { Instance } = {}
	for _, other in Players:GetPlayers() do
		if other.Character then
			table.insert(ignore, other.Character)
		end
	end
	local character = root.Parent
	if character and not table.find(ignore, character) then
		table.insert(ignore, character)
	end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
	return params
end

-- Высота стопы над полом под корнем (коробка FootSize вниз мимо персонажей: край галереи или ступени — тоже пол),
-- nil — пола нет в пределах HoverProbe.
local function gapBelow(root: BasePart, humanoid: Humanoid): number?
	local hit = workspace:Blockcast(
		CFrame.new(root.Position),
		cfg.FootSize,
		Vector3.new(0, -cfg.HoverProbe, 0),
		castParams(root)
	)
	if not hit then
		return nil
	end
	return math.max(0, root.Position.Y - hit.Position.Y - root.Size.Y / 2 - humanoid.HipHeight)
end

-- Рядом ферма (TrussPart) — по ней лезут, это не полёт.
local function climbing(root: BasePart): boolean
	local overlap = OverlapParams.new()
	overlap.FilterType = Enum.RaycastFilterType.Exclude
	overlap.FilterDescendantsInstances = castParams(root).FilterDescendantsInstances
	for _, part in workspace:GetPartBoundsInRadius(root.Position, cfg.ClimbRadius, overlap) do
		if part:IsA("TrussPart") then
			return true
		end
	end
	return false
end

-- Высота стопы над полом (проверки и тесты), nil — пола нет.
function MoveGuard.Gap(player: any): number?
	local root, humanoid = Validate.GetLiveRoot(player)
	return if root and humanoid then gapBelow(root, humanoid) else nil
end

-- Выше этого над полом дольше HoverSeconds — полёт (проверки и тесты).
function MoveGuard.HoverLimit(player: any): number
	local _, humanoid = Validate.GetLiveRoot(player)
	return (if humanoid then jumpHeight(humanoid) else StarterPlayer.CharacterJumpHeight) + cfg.HoverSlack
end

-- Один шаг проверки отметки mark до текущей точки корня. Возвращает (возможно ли, смещение).
local function advance(player: any, mark: Mark, root: BasePart, humanoid: Humanoid): (boolean, number)
	local now = os.clock()
	local speed = math.max(humanoid.WalkSpeed, mark.speed)
	mark.budget = math.min(capacity(speed), mark.budget + speed * cfg.Tolerance * (now - mark.at))
	mark.at, mark.speed = now, humanoid.WalkSpeed
	local position = root.Position
	if now < mark.graceUntil and mark.graceFrom and flat(position - mark.graceFrom) <= cfg.Slack then
		return true, 0 -- запоздавший пакет клиента вернул точку до переноса: отметка остаётся в новой
	end
	local moved = flat(position - mark.position)
	local descending = position.Y < mark.position.Y - cfg.FallStep
	mark.position = position
	mark.budget -= moved
	-- полёт: выше прыжка над полом дольше HoverSeconds; сбрасывает только пол, падение не нарушение
	local flying = false
	if pins[player] == nil then
		local gap = gapBelow(root, humanoid)
		local high = (gap == nil or gap > jumpHeight(humanoid) + cfg.HoverSlack) and not climbing(root)
		if not high then
			mark.airSince = nil
		else
			mark.airSince = mark.airSince or now
			flying = not descending and now - mark.airSince > cfg.HoverSeconds
		end
	end
	if mark.budget < 0 or flying then
		violation(player, if flying then "полёт" else ("рывок %.1f ст."):format(moved))
		mark.budget = math.max(mark.budget, 0)
		mark.airSince = nil
		return false, moved
	end
	return true, moved
end

-- Проверка пути с прошлой отметки. Возвращает (возможно ли, смещение, остаток копилки). Без персонажа или с новым
-- персонажем — отметка заново и «возможно».
function MoveGuard.Step(player: any): (boolean, number, number)
	local root, humanoid = Validate.GetLiveRoot(player)
	if not root or not humanoid then
		marks[player] = nil
		return true, 0, 0
	end
	local mark = marks[player]
	if not mark or mark.root ~= root then
		MoveGuard.Mark(player)
		return true, 0, 0
	end
	local owed = mark.owed
	mark.owed = nil
	local ok, moved = advance(player, mark, root, humanoid)
	return ok and owed == nil, moved, mark.budget
end

-- Перенос сервером: путь до места, где игрок сейчас, проверяется (если его проверяли за последние Live секунд), затем
-- корень ставится в cframe, отметка — там же с отсрочкой TransferGrace. Точка капкана не меняется.
function MoveGuard.Teleport(player: any, cframe: CFrame)
	local root, humanoid = Validate.GetLiveRoot(player)
	if not root or not humanoid then
		return
	end
	local owed: string? = nil
	local mark = marks[player]
	if mark and mark.root == root then
		owed = mark.owed
		if os.clock() - mark.at <= cfg.Live and not advance(player, mark, root, humanoid) then
			owed = "до переноса"
		end
	end
	local before = root.Position
	root.CFrame = cframe
	root.AssemblyLinearVelocity = Vector3.zero
	local arrived = fresh(root, humanoid)
	arrived.graceUntil = os.clock() + cfg.TransferGrace
	arrived.graceFrom = before
	arrived.owed = owed
	marks[player] = arrived
	transfers[player] = os.clock()
end

-- Сервер переносил игрока за последние seconds секунд (защита: дальний скачок — перенос, а не прыжок через устройство).
function MoveGuard.TransferredWithin(player: any, seconds: number): boolean
	local at = transfers[player]
	return at ~= nil and os.clock() - at <= seconds
end

-- Игрок должен стоять на месте (капкан): дальше PinRadius от точки — вернуть (в режиме логирования — только лог).
function MoveGuard.Pin(player: any)
	local root = Validate.GetLiveRoot(player)
	pins[player] = if root then { position = root.Position, warned = false } else nil
end

function MoveGuard.Unpin(player: any)
	pins[player] = nil
end

function MoveGuard.IsPinned(player: any): boolean
	return pins[player] ~= nil
end

-- Проверка закреплённых (раз в Tick; тестам — напрямую): вернуть в точку капкана, без подъёма.
function MoveGuard.CheckPins()
	for player, pin in pins do
		local root = Validate.GetLiveRoot(player)
		if not root or player.Parent == nil then
			pins[player] = nil
			continue
		end
		if (root.Position - pin.position).Magnitude > cfg.PinRadius then
			if not pin.warned then
				pin.warned = true
				violation(player, "ушёл из капкана")
			end
			if MoveGuard.Enforced() then
				MoveGuard.Teleport(player, CFrame.new(pin.position) * root.CFrame.Rotation)
			end
		end
	end
end

function MoveGuard.Forget(player: any)
	marks[player] = nil
	pins[player] = nil
	transfers[player] = nil
end

function MoveGuard.Init()
	Players.PlayerRemoving:Connect(MoveGuard.Forget)
	task.spawn(function()
		while true do
			task.wait(cfg.Tick)
			if next(pins) ~= nil then
				local ok, err = pcall(MoveGuard.CheckPins)
				if not ok then
					Log.Warn("MoveGuard", tostring(err))
				end
			end
		end
	end)
end

return MoveGuard

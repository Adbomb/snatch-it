-- Проверка невозможных перемещений на сервере (D52). Персонажем управляет клиент, поэтому читер может телепортироваться;
-- сервер это видит по позиции корня. Step(player): горизонтальное смещение с прошлой отметки не больше того, что можно
-- пробежать — скорость Humanoid (её ставит сервер) × время × Tolerance + Slack на лаги и толчки. Пока игрок не
-- двигается (или сеть молчит), время копится, но не больше MaxStall — рывок после зависания сети не нарушение, а
-- телепорт не быстрее бега. Переносы, которые делает сам сервер (выброс у двери, выход из хранилища, ночь, возврат в
-- зону босса), отмечаются Mark — точка отсчёта сдвигается; новый персонаж (возрождение) — новая отметка. Pin: игрок
-- должен стоять на месте (капкан) — дальше PinRadius сервер возвращает его к точке. Никаких банов: решение (сорвать
-- кражу, вернуть) — у вызывающего, нарушения пишутся в лог. Зависит от GameConfig, Util/Validate, Util/Log.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Log = require(ServerScriptService.Server.Util.Log)
local Validate = require(ServerScriptService.Server.Util.Validate)

local cfg = GameConfig.MoveGuard

type Mark = { root: BasePart, position: Vector3, at: number, speed: number }
type Pin = { position: Vector3, warned: boolean }

local MoveGuard = {}

local marks: { [any]: Mark } = {}
local pins: { [any]: Pin } = {}

local function flat(v: Vector3): number
	return Vector3.new(v.X, 0, v.Z).Magnitude
end

-- Отметка: отсюда и с этого момента считается следующее смещение (сервер сам перенёс игрока, кража началась).
function MoveGuard.Mark(player: any)
	local root, humanoid = Validate.GetLiveRoot(player)
	if root and humanoid then
		marks[player] = { root = root, position = root.Position, at = os.clock(), speed = humanoid.WalkSpeed }
	else
		marks[player] = nil
	end
	local pin = pins[player]
	if pin and root then
		pin.position = root.Position -- перенос сервером переносит и точку капкана
	end
end

-- Перенос сервером (разрешённый телепорт): ставит корень в cframe и отмечает новое место.
function MoveGuard.Teleport(player: any, cframe: CFrame)
	local root = Validate.GetLiveRoot(player)
	if root then
		root.CFrame = cframe
		root.AssemblyLinearVelocity = Vector3.zero
	end
	MoveGuard.Mark(player)
end

-- Проверка смещения с прошлой отметки. Возвращает (возможно ли, смещение, допустимое). Без персонажа или с новым
-- персонажем — отметка заново и «возможно».
function MoveGuard.Step(player: any): (boolean, number, number)
	local root, humanoid = Validate.GetLiveRoot(player)
	if not root or not humanoid then
		marks[player] = nil
		return true, 0, 0
	end
	local mark = marks[player]
	local now = os.clock()
	if not mark or mark.root ~= root then
		MoveGuard.Mark(player)
		return true, 0, 0
	end
	local moved = flat(root.Position - mark.position)
	local speed = math.max(humanoid.WalkSpeed, mark.speed)
	local allowed = speed * math.min(now - mark.at, cfg.MaxStall) * cfg.Tolerance + cfg.Slack
	if moved < cfg.Still then
		-- стоит или сеть молчит: время копится (до MaxStall), скорость берём наибольшую за это время
		mark.speed = speed
		return true, moved, allowed
	end
	marks[player] = { root = root, position = root.Position, at = now, speed = humanoid.WalkSpeed }
	if moved > allowed then
		Log.Warn(
			"MoveGuard",
			("%s: невозможное перемещение %.1f ст. (можно %.1f)"):format(
				tostring(player.Name),
				moved,
				allowed
			)
		)
		return false, moved, allowed
	end
	return true, moved, allowed
end

-- Игрок должен стоять на месте (капкан): дальше PinRadius от точки — вернуть.
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

-- Проверка закреплённых (раз в Tick; тестам — напрямую).
function MoveGuard.CheckPins()
	for player, pin in pins do
		local root = Validate.GetLiveRoot(player)
		if not root or player.Parent == nil then
			pins[player] = nil
			continue
		end
		if flat(root.Position - pin.position) > cfg.PinRadius then
			if not pin.warned then
				pin.warned = true
				Log.Warn(
					"MoveGuard",
					("%s ушёл из капкана — возвращён"):format(tostring(player.Name))
				)
			end
			local up = Vector3.new(0, math.max(0, root.Position.Y - pin.position.Y), 0)
			root.CFrame = CFrame.new(pin.position + up) * root.CFrame.Rotation
			root.AssemblyLinearVelocity = Vector3.zero
			MoveGuard.Mark(player)
		end
	end
end

function MoveGuard.Forget(player: any)
	marks[player] = nil
	pins[player] = nil
end

function MoveGuard.Init()
	game:GetService("Players").PlayerRemoving:Connect(MoveGuard.Forget)
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

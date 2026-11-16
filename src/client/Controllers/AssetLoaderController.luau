-- Порядок загрузки ассетов у клиента при входе (этап C.2: «мыльный» мир и долгие текстуры). Карта без
-- StreamingEnabled приходит целиком, и все меши и карты встают в одну очередь ContentProvider без приоритета: материалы
-- мира, интерфейс и то, что вокруг игрока, ждут боссов, существ и дальних зон. Здесь очередь получает порядок:
--   1) материалы мира — MaterialVariant LEGO (на них держится вид всей карты);
--   2) интерфейс игрока и всё ближе GameConfig.AssetLoad.CriticalRadius от персонажа (площадь, свой музей, соседи);
--   3) остальное: дальние зоны, боссы, существа, превью в ReplicatedStorage;
--   4) то, что сервер добавит позже (он достраивает мир после входа: предметы у боссов, существа, экспонаты) — раз в
--      WatchInterval пачкой, ближние вперёд.
-- ContentProvider:PreloadAsync только поднимает нужное вперёд — игру ничто не ждёт (всё в отдельных потоках).
-- Неудачные (Failure, TimedOut) повторяются после пауз RetryDelays; оставшиеся после повторов — в журнал с ID:
-- ошибка загрузки не прячется за размытием.
-- Для проверки — строка «[AssetLoader] …» в Output и атрибуты игрока (только у клиента), секунды от старта клиента:
-- AssetLoadWorld, AssetLoadCritical, AssetLoadAll; AssetLoadCount, AssetLoadRetried, AssetLoadFailed,
-- AssetLoadFailedIds (первые пять); AssetQueueMax и AssetQueueEmptyAt — наибольшая очередь ContentProvider и когда
-- она последний раз опустела (первые QueueWatch секунд).
-- Качество графики игрока и StreamingEnabled не меняются: снижение разрешения текстур на слабом устройстве или при
-- нехватке памяти — решение движка Roblox.
-- Зависит от Config/GameConfig.

local ContentProvider = game:GetService("ContentProvider")
local MaterialService = game:GetService("MaterialService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("GameConfig"))

local cfg = GameConfig.AssetLoad
local player = Players.LocalPlayer

local AssetLoaderController = {}

-- Классы, у которых есть загружаемое содержимое (картинки, меши).
local CONTENT = {
	SurfaceAppearance = true,
	MeshPart = true,
	Decal = true,
	Texture = true,
	ParticleEmitter = true,
	Beam = true,
	Trail = true,
	ImageLabel = true,
	ImageButton = true,
	MaterialVariant = true,
}

local BAD = { [Enum.AssetFetchStatus.Failure] = true, [Enum.AssetFetchStatus.TimedOut] = true }

local started = os.clock()
local status: { [string]: Enum.AssetFetchStatus } = {}
local count = 0
local retried = 0
local failedForGood: { [string]: boolean } = {}
local reported = 0 -- сколько неудач уже записано в журнал (повторно одно и то же не пишется)

local function since(): number
	return math.floor((os.clock() - started) * 100 + 0.5) / 100
end

local function hasContent(inst: Instance): boolean
	return CONTENT[inst.ClassName] == true
end

local function positionOf(inst: Instance): Vector3?
	local part = if inst:IsA("BasePart") then inst else inst:FindFirstAncestorWhichIsA("BasePart")
	return part and part.Position
end

local function rootPosition(): Vector3?
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if root and root:IsA("BasePart") then
		return root.Position
	end
	local camera = workspace.CurrentCamera
	return camera and camera.CFrame.Position
end

-- Ближние вперёд (без позиции — в конец).
local function byDistance(list: { Instance }, at: Vector3?)
	if not at then
		return
	end
	local d = {}
	for _, inst in list do
		local p = positionOf(inst)
		d[inst] = if p then (p - at).Magnitude else math.huge
	end
	table.sort(list, function(a, b)
		return d[a] < d[b]
	end)
end

-- Ещё не ушедшие на повторы неудачные ID.
local function newFailures(): { string }
	local out = {}
	for id, s in status do
		if BAD[s] and not failedForGood[id] then
			table.insert(out, id)
		end
	end
	return out
end

local function report()
	local failed = {}
	for id in failedForGood do
		if BAD[status[id]] then
			table.insert(failed, id)
		end
	end
	table.sort(failed)
	player:SetAttribute("AssetLoadCount", count)
	player:SetAttribute("AssetLoadRetried", retried)
	player:SetAttribute("AssetLoadFailed", #failed)
	player:SetAttribute("AssetLoadFailedIds", table.concat(failed, " ", 1, math.min(5, #failed)))
	if #failed > reported then
		reported = #failed
		warn(
			("[AssetLoader] не загрузилось после повторов: %d — %s"):format(
				#failed,
				table.concat(failed, " ", 1, math.min(10, #failed))
			)
		)
	end
end

-- Пачками: PreloadAsync на длинном списке держит поток до конца; пачки дают повторам и следующему этапу идти раньше.
local function preload(list: { any })
	for i = 1, #list, cfg.Batch do
		local batch = table.move(list, i, math.min(i + cfg.Batch - 1, #list), 1, {})
		local ok, err = pcall(function()
			ContentProvider:PreloadAsync(batch, function(id: string, s: Enum.AssetFetchStatus)
				if status[id] == nil then
					count += 1
				end
				status[id] = s
			end)
		end)
		if not ok then
			warn(("[AssetLoader] PreloadAsync: %s"):format(tostring(err)))
		end
	end
end

-- Повторы неудачных из списка ids: только они, после пауз RetryDelays; потом — итог в журнал.
local function retry(ids: { string }, attempt: number)
	if #ids == 0 then
		return
	end
	if attempt > #cfg.RetryDelays then
		report()
		return
	end
	retried += if attempt == 1 then #ids else 0
	task.delay(cfg.RetryDelays[attempt], function()
		preload(ids)
		local still = {}
		for _, id in ids do
			if BAD[status[id]] then
				table.insert(still, id)
			end
		end
		retry(still, attempt + 1)
	end)
end

local function scheduleRetries()
	local ids = newFailures()
	for _, id in ids do
		failedForGood[id] = true
	end
	retry(ids, 1)
end

-- Очередь ContentProvider в первые QueueWatch секунд: наибольшая длина и когда последний раз опустела.
local function watchQueue()
	local peak, emptyAt, wasBusy = 0, 0, false
	while os.clock() - started < cfg.QueueWatch do
		local size = ContentProvider.RequestQueueSize
		peak = math.max(peak, size)
		if size > 0 then
			wasBusy = true
		elseif wasBusy then
			emptyAt = since()
			wasBusy = false
		end
		player:SetAttribute("AssetQueueMax", peak)
		player:SetAttribute("AssetQueueEmptyAt", emptyAt)
		task.wait(0.25)
	end
end

local function run()
	-- 1) материалы мира
	local variants = {}
	for _, v in MaterialService:GetDescendants() do
		if v:IsA("MaterialVariant") then
			table.insert(variants, v)
		end
	end
	preload(variants)
	player:SetAttribute("AssetLoadWorld", since())

	-- 2) интерфейс и всё рядом с персонажем
	if not game:IsLoaded() then
		game.Loaded:Wait()
	end
	local character = player.Character or player.CharacterAdded:Wait()
	character:WaitForChild("HumanoidRootPart", cfg.CharacterWait)
	local at = rootPosition()
	local critical, rest = {}, {}
	local gui = player:FindFirstChildOfClass("PlayerGui")
	if gui then
		for _, d in gui:GetDescendants() do
			if (d:IsA("ImageLabel") or d:IsA("ImageButton")) and d.Image ~= "" then
				table.insert(critical, d)
			end
		end
	end
	for _, d in workspace:GetDescendants() do
		if hasContent(d) then
			local p = positionOf(d)
			if at and p and (p - at).Magnitude <= cfg.CriticalRadius then
				table.insert(critical, d)
			else
				table.insert(rest, d)
			end
		end
	end
	preload(critical)
	player:SetAttribute("AssetLoadCritical", since())

	-- 3) остальное
	for _, d in ReplicatedStorage:GetDescendants() do
		if hasContent(d) then
			table.insert(rest, d)
		end
	end
	byDistance(rest, at)
	preload(rest)
	player:SetAttribute("AssetLoadAll", since())
	print(
		("[AssetLoader] материалы %.2f с, важное (%d) %.2f с, остальное (%d) %.2f с"):format(
			player:GetAttribute("AssetLoadWorld"),
			#critical,
			player:GetAttribute("AssetLoadCritical"),
			#rest,
			player:GetAttribute("AssetLoadAll")
		)
	)
	scheduleRetries()
	report()
end

-- 4) появившееся позже: пачкой раз в WatchInterval, ближние вперёд.
local function watchLater()
	local pending: { Instance } = {}
	workspace.DescendantAdded:Connect(function(d)
		if hasContent(d) then
			table.insert(pending, d)
		end
	end)
	while true do
		task.wait(cfg.WatchInterval)
		if #pending > 0 then
			local list = pending
			pending = {}
			byDistance(list, rootPosition())
			preload(list)
			scheduleRetries()
			report()
		end
	end
end

function AssetLoaderController.Start()
	task.spawn(run)
	task.spawn(watchLater)
	task.spawn(watchQueue)
end

return AssetLoaderController

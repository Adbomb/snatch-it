-- Подбор («Поднять»), перенос над головой и бросок предметов карты; скорость от силы и груза (D24).
-- Смерть с предметом → предмет падает рядом; выход с предметом → исчезает (D3).
-- Зависит от ItemRegistry, Util/Validate, Util/RateLimiter, Util/Notify, Remotes, Speed, Config.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Speed = require(ReplicatedStorage.Shared.Speed)
local ItemRegistry = require(ServerScriptService.Server.Services.ItemRegistry)
local Notify = require(ServerScriptService.Server.Util.Notify)
local RateLimiter = require(ServerScriptService.Server.Util.RateLimiter)
local Validate = require(ServerScriptService.Server.Util.Validate)

local CARRY_HEIGHT = 2.8 -- насколько выше центра персонажа держится низ предмета

local pickupLimiter = RateLimiter.new(GameConfig.RateLimits.Pickup)
local dropLimiter = RateLimiter.new(GameConfig.RateLimits.Drop)

local holds: { [Player]: { uid: string, weld: WeldConstraint, weight: string } } = {}
local prompts: { [string]: ProximityPrompt } = {}

local CarryService = {}

local function setCarryPhysics(part: BasePart, carrying: boolean)
	part.CanCollide = not carrying
	part.CanTouch = not carrying
	part.Massless = carrying
end

-- Снимает предмет с персонажа (сварка, скорость, атрибут). Состояние меняет только ItemRegistry.
local function releaseHold(player: Player)
	local hold = holds[player]
	holds[player] = nil
	if hold then
		hold.weld:Destroy()
	end
	player:SetAttribute("CarryingItemId", nil)
	CarryService.RefreshSpeed(player)
end

-- Точка на земле перед игроком (или под ним). nil — под игроком пустота.
local function findDropCFrame(player: Player, part: BasePart): CFrame?
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local origin = if root and root:IsA("BasePart") then root.Position else part.Position
	local look = if root and root:IsA("BasePart") then root.CFrame.LookVector else Vector3.new(0, 0, -1)
	local flat = Vector3.new(look.X, 0, look.Z)
	flat = if flat.Magnitude > 0.01 then flat.Unit else Vector3.new(0, 0, -1)

	local ignore: { Instance } = { part }
	for _, other in Players:GetPlayers() do
		if other.Character then
			table.insert(ignore, other.Character)
		end
	end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore

	for _, start in { origin + flat * GameConfig.Carry.DropForward, origin } do
		local hit = workspace:Raycast(start + Vector3.new(0, 4, 0), Vector3.new(0, -60, 0), params)
		if hit then
			local position = hit.Position + Vector3.new(0, part.Size.Y / 2, 0)
			return CFrame.lookAt(position, position + flat)
		end
	end
	return nil
end

local function tryPickup(player: Player, uid: string)
	if not pickupLimiter:Allow(player) then
		return
	end
	local entry = ItemRegistry.Get(uid)
	if not entry or entry.state ~= "OnMap" then
		return
	end
	if ItemRegistry.GetCarriedBy(player) then
		Notify.Send(player, "Руки заняты — сначала бросьте предмет (G)", "Stop")
		return
	end
	local part = entry.part
	local root, humanoid = Validate.GetLiveRoot(player)
	if not part or not part.Parent or not root or not humanoid then
		return
	end
	if not Validate.IsNear(player, part.Position, GameConfig.Carry.PickupDistance) then
		return
	end
	if not ItemRegistry.Transition(uid, "Carried", { carrier = player }) then
		return
	end
	CarryService.AttachCarried(player, uid)
end

-- После перехода в Carried (подбор с карты или предмет у босса, D37): предмет над головой, скорость от груза,
-- атрибут CarryingItemId. false — предмет не в руках этого игрока или нет персонажа.
function CarryService.AttachCarried(player: Player, uid: string): boolean
	local entry = ItemRegistry.Get(uid)
	local root = Validate.GetLiveRoot(player)
	if not entry or entry.state ~= "Carried" or entry.carrier ~= player or not entry.part or not root then
		return false
	end
	local part = entry.part
	local prompt = prompts[uid]
	if prompt then
		prompt.Enabled = false
	end
	part.CFrame = root.CFrame * CFrame.new(0, CARRY_HEIGHT + part.Size.Y / 2, 0)
	setCarryPhysics(part, true)
	local weld = Instance.new("WeldConstraint")
	weld.Part0 = root
	weld.Part1 = part
	weld.Parent = part
	part.Anchored = false
	holds[player] = { uid = uid, weld = weld, weight = Items[entry.itemId].weight }
	CarryService.RefreshSpeed(player)
	player:SetAttribute("CarryingItemId", entry.itemId)
	return true
end

local function onPartDestroyed(uid: string)
	prompts[uid] = nil
	local entry = ItemRegistry.Get(uid)
	if not entry then
		return
	end
	if entry.state == "Carried" then
		local carrier = entry.carrier
		ItemRegistry.Discard(uid, "Part уничтожен")
		if carrier then
			releaseHold(carrier)
		end
	elseif entry.state == "OnMap" then
		ItemRegistry.Discard(uid, "Part уничтожен")
	end
end

local function watchCharacter(player: Player, character: Model)
	local humanoid = character:WaitForChild("Humanoid", 10)
	if humanoid and humanoid:IsA("Humanoid") then
		CarryService.RefreshSpeed(player)
		humanoid.Died:Connect(function()
			if player.Parent == Players then
				CarryService.Drop(player)
			end
		end)
	end
end

local function watchPlayer(player: Player)
	player.CharacterAdded:Connect(function(character)
		watchCharacter(player, character)
	end)
	if player.Character then
		task.spawn(watchCharacter, player, player.Character)
	end
end

-- Скорость ходьбы от силы (атрибут Strength) и груза в руках (D24). Вызывается при подборе, броске,
-- появлении персонажа и росте силы.
function CarryService.RefreshSpeed(player: Player)
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if humanoid then
		local hold = holds[player]
		humanoid.WalkSpeed = Speed.Walk(player:GetAttribute("Strength") or 0, hold and hold.weight)
	end
end

function CarryService.Init()
	Remotes.Get(Remotes.Names.DropItem).OnServerEvent:Connect(function(player)
		if dropLimiter:Allow(player) then
			CarryService.Drop(player)
		end
	end)
	Players.PlayerAdded:Connect(watchPlayer)
	for _, player in Players:GetPlayers() do
		watchPlayer(player)
	end
end

-- Делает предмет на карте поднимаемым: подсказка «Поднять» и защита от потери Part.
function CarryService.RegisterMapItem(uid: string, part: BasePart)
	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText = "Поднять"
	prompt.ObjectText = Items[part:GetAttribute("ItemId") :: string].displayName
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = GameConfig.Carry.PickupDistance
	prompt.RequiresLineOfSight = false
	prompt.Parent = part
	prompts[uid] = prompt
	prompt.Triggered:Connect(function(player)
		tryPickup(player, uid)
	end)
	part.Destroying:Connect(function()
		onPartDestroyed(uid)
	end)
end

-- Бросить то, что игрок несёт: предмет ложится на землю перед ним и снова доступен всем.
function CarryService.Drop(player: Player)
	local uid = ItemRegistry.GetCarriedBy(player)
	if not uid then
		return
	end
	local entry = ItemRegistry.Get(uid)
	local part = entry and entry.part
	if not part or not part.Parent then
		ItemRegistry.Discard(uid, "Part потерян")
		releaseHold(player)
		return
	end
	local target = findDropCFrame(player, part)
	if not target then
		ItemRegistry.Discard(uid, "под игроком пустота")
		releaseHold(player)
		part:Destroy()
		return
	end
	if not ItemRegistry.Transition(uid, "OnMap") then
		return
	end
	releaseHold(player)
	part.Anchored = true
	part.CFrame = target
	setCarryPhysics(part, false)
	local prompt = prompts[uid]
	if prompt then
		prompt.Enabled = true
	end
end

-- Вызывается после перехода Carried → Displayed или Carried → Stored: снимает предмет с персонажа
-- и убирает «Поднять» (D2). Возвращает Part (для Stored его удаляет вызывающий).
function CarryService.ReleaseToMuseum(player: Player, uid: string): BasePart?
	local hold = holds[player]
	if not hold or hold.uid ~= uid then
		return nil
	end
	local part = hold.weld.Part1
	releaseHold(player)
	local prompt = prompts[uid]
	prompts[uid] = nil
	if prompt then
		prompt:Destroy()
	end
	if part then
		part.Anchored = true
		setCarryPhysics(part, false)
	end
	return part
end

-- Несомый предмет теряется: исчезает из рук и с сервера (D3 — выход из игры, D37 — наступление ночи).
-- true — предмет был.
function CarryService.LoseCarried(player: Player, reason: string): boolean
	local uid = ItemRegistry.GetCarriedBy(player)
	if uid then
		local entry = ItemRegistry.Get(uid)
		ItemRegistry.Discard(uid, reason)
		if entry and entry.part then
			entry.part:Destroy()
		end
	end
	releaseHold(player)
	return uid ~= nil
end

-- D3: игрок вышел с предметом в руках — предмет исчезает.
function CarryService.OnPlayerRemoving(player: Player)
	CarryService.LoseCarried(player, "игрок вышел (D3)")
end

-- Обработчики для серверных тестов (Server/Tests): та же функция, что вызывает подсказка «Поднять».
CarryService.Handlers = { Pickup = tryPickup }

return CarryService

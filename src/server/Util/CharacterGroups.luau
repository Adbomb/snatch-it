-- Группы столкновений персонажей (D48-C, D49): какая группа у персонажа и как её поставить всем его деталям.
-- • В бою с боссом (атрибут игрока InBattle) — Fighter: упирается в невидимые стены на границах зон (ZoneLock), все
--   остальные проходят сквозь них (BattleService).
-- • Владелец участка — VaultOwner_<участок>: проходит барьер своего хранилища (VaultBarrier_<участок>, VaultService).
-- • Ученик (D55, атрибут Tutorial) — Student: проходит ночной барьер (NightBarrier), обучение ночью не прерывается.
-- • Остальные — Default.
-- Зависит от PlotService.

local PhysicsService = game:GetService("PhysicsService")
local ServerScriptService = game:GetService("ServerScriptService")

local PlotService = require(ServerScriptService.Server.Services.PlotService)

local CharacterGroups = {}

CharacterGroups.Default = "Default"
CharacterGroups.Fighter = "ZoneFighter"
CharacterGroups.ZoneLock = "ZoneLock"
CharacterGroups.Student = "Student"
CharacterGroups.NightBarrier = "NightBarrier"

function CharacterGroups.VaultBarrier(index: number): string
	return "VaultBarrier_" .. index
end

function CharacterGroups.VaultOwner(index: number): string
	return "VaultOwner_" .. index
end

-- Зарегистрировать группу (повторно — ничего не делает). Стены зон (ZoneLock) держат только бойцов: новая группа
-- сквозь них проходит.
function CharacterGroups.Register(group: string)
	if not PhysicsService:IsCollisionGroupRegistered(group) then
		PhysicsService:RegisterCollisionGroup(group)
	end
	local lock = CharacterGroups.ZoneLock
	if group ~= lock and PhysicsService:IsCollisionGroupRegistered(lock) then
		PhysicsService:CollisionGroupSetCollidable(group, lock, group == CharacterGroups.Fighter)
	end
	-- ночной барьер держит всех, кроме ученика (D55)
	local barrier, student = CharacterGroups.NightBarrier, CharacterGroups.Student
	if PhysicsService:IsCollisionGroupRegistered(barrier) and PhysicsService:IsCollisionGroupRegistered(student) then
		PhysicsService:CollisionGroupSetCollidable(barrier, student, false)
	end
end

-- Группа персонажа игрока сейчас.
function CharacterGroups.GroupOf(player: any): string
	if player:GetAttribute("InBattle") ~= nil then
		return CharacterGroups.Fighter
	end
	if player:GetAttribute("Tutorial") ~= nil and PhysicsService:IsCollisionGroupRegistered(CharacterGroups.Student) then
		return CharacterGroups.Student
	end
	local plot = PlotService.GetPlotOf(player)
	return if plot then CharacterGroups.VaultOwner(plot.index) else CharacterGroups.Default
end

-- Поставить группу всем деталям персонажа игрока.
function CharacterGroups.Apply(player: any)
	local character = player.Character
	if not character then
		return
	end
	local group = CharacterGroups.GroupOf(player)
	for _, part in character:GetDescendants() do
		if part:IsA("BasePart") then
			part.CollisionGroup = group
		end
	end
end

-- Новый персонаж: группа сразу и у деталей, добавленных позже (аксессуары, инструменты).
function CharacterGroups.Watch(player: Player, character: Model)
	CharacterGroups.Apply(player)
	character.DescendantAdded:Connect(function(part)
		if part:IsA("BasePart") then
			part.CollisionGroup = CharacterGroups.GroupOf(player)
		end
	end)
end

return CharacterGroups

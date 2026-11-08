-- Группы столкновений персонажей (D48-C, D49): какая группа у персонажа и как её поставить всем его деталям.
-- • В бою с боссом (атрибут игрока InBattle) — Fighter: упирается в невидимые стены на границах зон (ZoneLock), все
--   остальные проходят сквозь них (BattleService).
-- • Владелец участка — VaultOwner_<участок>: проходит барьер своего хранилища (VaultBarrier_<участок>, VaultService).
-- • Ученик (D55, атрибут Tutorial) — Student_<участок>: проходит ночной барьер (NightBarrier, обучение ночью не
--   прерывается) и барьер своего хранилища.
-- • Остальные — Default.
-- Зависит от PlotService.

local PhysicsService = game:GetService("PhysicsService")
local ServerScriptService = game:GetService("ServerScriptService")

local PlotService = require(ServerScriptService.Server.Services.PlotService)

local CharacterGroups = {}

CharacterGroups.Default = "Default"
CharacterGroups.Fighter = "ZoneFighter"
CharacterGroups.ZoneLock = "ZoneLock"
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

end

-- Группа ученика участка index (D55, регистрируется при первом вызове): ночной барьер и барьер своего хранилища —
-- насквозь, остальное — как у всех.
function CharacterGroups.Student(index: number?): string
	local name = "Student_" .. tostring(index or 0)
	CharacterGroups.Register(name)
	if PhysicsService:IsCollisionGroupRegistered(CharacterGroups.NightBarrier) then
		PhysicsService:CollisionGroupSetCollidable(name, CharacterGroups.NightBarrier, false)
	end
	if index and PhysicsService:IsCollisionGroupRegistered(CharacterGroups.VaultBarrier(index)) then
		PhysicsService:CollisionGroupSetCollidable(name, CharacterGroups.VaultBarrier(index), false)
	end
	return name
end

-- Группа персонажа игрока сейчас.
function CharacterGroups.GroupOf(player: any): string
	if player:GetAttribute("InBattle") ~= nil then
		return CharacterGroups.Fighter
	end
	local plot = PlotService.GetPlotOf(player)
	if player:GetAttribute("Tutorial") ~= nil then
		return CharacterGroups.Student(if plot then plot.index else nil)
	end
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

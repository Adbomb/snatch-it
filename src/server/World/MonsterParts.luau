-- Собственные части существа как детали этажа (D74, этаж — продолжение монстра): увеличенная копия меша части
-- (перчатка, голова, лапа…) с её же картой цвета и колец — без новых загрузок, цвета совпадают сами. Заявки на части
-- выдаёт генератор World/Models/MonsterFloor (кирпичи он строит сам, меши — здесь, потому что меши существ загружены
-- только в потоке игры: Util/ItemFactory.Preload). Если меша нет (режим редактирования, меш не загрузился) — часть
-- собирается из блоков скелета Config/CreatureRigs в тех же цветах (Part-версия) с кольцами D39.
-- Заявка: { part = имя части, at = CFrame центра габарита части в осях этажа (существо лицом в −Z), scale = множитель,
-- gold = true — золотая скульптура (Foil, без карты); gold = "tint" — позолота: карта существа остаётся, но
-- окрашена в золото (черты лица читаются и на низкой графике) }.
-- Зависит от Util/ItemFactory, Config/CreatureRigs, World/Models/ShowcaseKit.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local CreatureRigs = require(ReplicatedStorage.Shared.Config.CreatureRigs)
local Server = ServerScriptService.Server
local ItemFactory = require(Server.Util.ItemFactory)
local Kit = require(Server.World.Models.ShowcaseKit)

export type Request = { part: string, at: CFrame, scale: number, gold: (boolean | string)? }

local MonsterParts = {}

local FACE = CFrame.Angles(0, math.pi, 0) -- скелет смотрит в +Z, существо в игре — в −Z

local function finish(part: BasePart, gold: (boolean | string)?)
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.Massless = true
	if gold == "tint" and part:FindFirstChildOfClass("SurfaceAppearance") then
		(part:FindFirstChildOfClass("SurfaceAppearance") :: SurfaceAppearance).Color = Kit.GOLD
	elseif gold then
		local look = part:FindFirstChildOfClass("SurfaceAppearance")
		if look then
			look:Destroy()
		end
		part.Material = Enum.Material.Foil
		part.Color = Kit.GOLD
	end
end

-- Добавляет в модель этажа model (её начало — frame) части существа itemId по заявкам. Возвращает число деталей.
function MonsterParts.Add(model: Model, frame: CFrame, itemId: string, requests: { Request }): number
	local rig = CreatureRigs[itemId]
	if not rig or #requests == 0 then
		return 0
	end
	local count = 0
	-- образец существа: его детали-меши клонируются; после сборки образец удаляется
	local ok, sample = pcall(ItemFactory.Create, itemId)
	local root = if ok then sample else nil
	if root then
		root.CFrame = CFrame.new()
	end
	for _, request in requests do
		local spec = rig.Parts[request.part]
		if not spec then
			continue
		end
		local source = root and root:FindFirstChild(request.part)
		if source and source:IsA("MeshPart") then
			local turn = source.CFrame.Rotation -- поворот детали при существе лицом в −Z
			local clone = source:Clone()
			for _, child in clone:GetChildren() do
				if child:IsA("JointInstance") then
					child:Destroy()
				end
			end
			clone.Name = "Monster_" .. request.part
			clone.Size = source.Size * request.scale
			finish(clone, request.gold)
			clone.CFrame = frame * request.at * turn
			clone.Parent = model
			count += 1
		else
			-- Part-версия: блоки скелета от центра габарита части
			for _, b in spec.blocks do
				local offset = FACE * ((b[1] - spec.center) * request.scale)
				local part = Instance.new("Part")
				part.Name = "Monster_" .. request.part
				part.Size = b[2] * request.scale
				part.Color = Color3.fromHex(b[3])
				part.Material = Enum.Material.Plastic
				part.MaterialVariant = "LegoRingsD39Boss"
				part.TopSurface = Enum.SurfaceType.Smooth
				part.BottomSurface = Enum.SurfaceType.Smooth
				part.CastShadow = false
				finish(part, request.gold)
				part.CFrame = frame * request.at * CFrame.new(offset)
				part.Parent = model
				count += 1
			end
		end
	end
	if root then
		root:Destroy()
	end
	return count
end

return MonsterParts

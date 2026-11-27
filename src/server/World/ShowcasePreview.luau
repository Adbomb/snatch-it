-- Предпросмотр этажей-витрин (D74, вариант B) в Play для снимков владельцу: стопка «Деревянный салун + Космический
-- салун + плита-кровля» и живые жильцы (готовая модель существа, спокойная анимация — как у экспоната этажа).
-- Только DEV: вызывается через MCP в запущенной игре, в место ничего не сохраняет.
--   local W = game.ServerScriptService.Server.World
--   require(W.ShowcasePreview).Build(CFrame.new(x, y, z))   -- низ стопки, перед — −Z
--   require(W.ShowcasePreview).Clear()
-- Зависит от World/Models/ShowcaseFloor, ModelBuilder, Util/ItemFactory.

local HttpService = game:GetService("HttpService")
local ServerScriptService = game:GetService("ServerScriptService")

local Server = ServerScriptService.Server
local ItemFactory = require(Server.Util.ItemFactory)
local ModelBuilder = require(Server.World.ModelBuilder)
local ShowcaseFloor = require(Server.World.Models.ShowcaseFloor)

local ShowcasePreview = {}

local FOLDER = "__ShowcasePreview"

-- Увеличить существо в k раз: детали, сочленения и вложения (ItemFactory делает модель в натуральный размер).
local function scaleCreature(root: BasePart, k: number)
	local function scaled(cf: CFrame): CFrame
		return cf.Rotation + cf.Position * k
	end
	for _, d in root:GetDescendants() do
		if d:IsA("BasePart") then
			d.Size *= k
		elseif d:IsA("JointInstance") then
			d.C0, d.C1 = scaled(d.C0), scaled(d.C1)
		elseif d:IsA("SpecialMesh") then
			d.Scale *= k
		elseif d:IsA("Attachment") then
			d.Position *= k
		end
	end
	root.Size *= k
end

local function resident(parent: Instance, itemId: string, at: CFrame, scale: number)
	local part = ItemFactory.Create(itemId)
	scaleCreature(part, scale)
	part.Anchored = true
	part.CFrame = at * CFrame.new(0, part.Size.Y / 2, 0)
	part:SetAttribute("ItemUid", HttpService:GenerateGUID(false))
	part:SetAttribute("TowerFloor", 1) -- клиент оживляет как экспонат этажа (спокойная анимация на месте)
	part.Parent = parent
end

function ShowcasePreview.Clear()
	local old = workspace:FindFirstChild(FOLDER)
	if old then
		old:Destroy()
	end
end

-- Стопка из двух этажей на месте at (низ плиты нижнего этажа, перед — −Z). Возвращает число деталей.
function ShowcasePreview.Build(at: CFrame): number
	ShowcasePreview.Clear()
	local folder = Instance.new("Folder")
	folder.Name = FOLDER
	folder.Parent = workspace
	local y = 0
	for _, tier in { 1, 6 } do
		local built = ShowcaseFloor.Saloon(tier)
		local frame = at * CFrame.new(0, y, 0)
		ModelBuilder.Place(ModelBuilder.Build("Showcase_" .. tier, built.bricks), frame, folder)
		resident(folder, "CactusBoxer", frame * CFrame.new(built.resident), built.scale)
		y += built.height
	end
	ModelBuilder.Place(ModelBuilder.Build("Showcase_Roof", ShowcaseFloor.Roof(6)), at * CFrame.new(0, y, 0), folder)
	return ModelBuilder.CountParts(folder)
end

return ShowcasePreview

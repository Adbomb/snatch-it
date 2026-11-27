-- Предпросмотр этажей-витрин (D74, вариант B) для снимков владельцу. Только DEV, в место ничего не сохраняет
-- (папка workspace.__ShowcasePreview, Archivable = false). Режимы (строка mode, слова через пробел):
--   "row Saloon" | "row Ocean"  — шесть редкостей темы в ряд (у каждой плита-кровля), с живыми жильцами;
--   "tower"                     — башня из 12 этажей вперемешку, плита-кровля и колпак C;
--   "old"                       — новый Космический салун и рядом прошлый вариант (ShowcaseFloorV1);
--   добавка "far"               — дальние версии этажей (без жильцов), "stage" — площадка-земля под снимки.
-- В Play строит поток игры (атрибуты ServerStorage.DevTools: ShowcaseMode, затем Showcase = CFrame): у потока MCP свои
-- копии модулей без загруженных мешей существ. В Edit — через FreshRequire (жильцы там — заглушки):
--   local W = game.ServerScriptService.Server.World
--   require(W.FreshRequire)(W.ShowcasePreview).Build(CFrame.new(0, 0, 0), "row Saloon stage")
-- Зависит от World/Models/ShowcaseFloor, ShowcaseFloorV1, ModelBuilder, Util/ItemFactory.

local HttpService = game:GetService("HttpService")
local ServerScriptService = game:GetService("ServerScriptService")

local Server = ServerScriptService.Server
local ItemFactory = require(Server.Util.ItemFactory)
local ModelBuilder = require(Server.World.ModelBuilder)
local ShowcaseFloor = require(Server.World.Models.ShowcaseFloor)
local ShowcaseFloorV1 = require(Server.World.Models.ShowcaseFloorV1)

local ShowcasePreview = {}

local FOLDER = "__ShowcasePreview"
ShowcasePreview.Pitch = 70 -- шаг ряда, стадов
-- Башня из 12 этажей вперемешку (снизу вверх): редкость и тема.
ShowcasePreview.Tower = {
	{ 1, "Saloon" },
	{ 3, "Ocean" },
	{ 1, "Ocean" },
	{ 2, "Saloon" },
	{ 5, "Ocean" },
	{ 1, "Saloon" },
	{ 2, "Ocean" },
	{ 4, "Saloon" },
	{ 1, "Ocean" },
	{ 6, "Saloon" },
	{ 2, "Saloon" },
	{ 3, "Ocean" },
}

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
	local ok, part = pcall(ItemFactory.Create, itemId)
	if not ok or not part then
		return
	end
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

-- Один этаж на месте frame (низ плиты, перед — −Z). Возвращает высоту этажа.
local function place(folder: Instance, frame: CFrame, theme: string, tier: number, far: boolean): number
	local name = ("%s_%d%s"):format(theme, tier, if far then "_Far" else "")
	local built = if far then ShowcaseFloor.Far(theme, tier) else ShowcaseFloor.Build(theme, tier)
	ModelBuilder.Place(ModelBuilder.Build(name, built.bricks), frame, folder)
	resident(folder, built.item, frame * CFrame.new(built.resident), built.scale)
	return built.height
end

local function roof(folder: Instance, frame: CFrame, tier: number)
	ModelBuilder.Place(ModelBuilder.Build("Roof", ShowcaseFloor.Roof(tier)), frame, folder)
end

-- Строит предпросмотр на месте at (низ, перед — −Z). Возвращает отчёт: число деталей и счёт по моделям.
function ShowcasePreview.Build(at: CFrame, mode: string?): string
	ShowcasePreview.Clear()
	local words = {}
	for word in (mode or "row Saloon"):gmatch("%S+") do
		words[word] = true
	end
	local far = words.far == true
	local folder = Instance.new("Folder")
	folder.Name = FOLDER
	folder.Archivable = false
	if words.stage then
		local ground = Instance.new("Part")
		ground.Name = "Stage"
		ground.Anchored = true
		ground.Size = Vector3.new(900, 2, 900)
		ground.CFrame = at * CFrame.new(0, -1, -250)
		ground.Color = Color3.fromHex("6FB04A")
		ground.Material = Enum.Material.Plastic
		ground.TopSurface = Enum.SurfaceType.Smooth
		ground.Parent = folder
	end
	if words.tower then
		local y, last = 0, 1
		for i, spec in ShowcasePreview.Tower do
			y += place(folder, at * CFrame.new(0, y, 0), spec[2], spec[1], far)
			last = spec[1]
			if i % 3 == 0 then
				task.wait()
			end
		end
		roof(folder, at * CFrame.new(0, y, 0), last)
		local cap = ModelBuilder.Build("Cap", ShowcaseFloor.Cap())
		ModelBuilder.Place(cap, at * CFrame.new(0, y + ShowcaseFloor.Slab, 0), folder)
	elseif words.old then
		local h = place(folder, at * CFrame.new(-30, 0, 0), "Saloon", 6, false)
		roof(folder, at * CFrame.new(-30, h, 0), 6)
		local old = ShowcaseFloorV1.Saloon(6)
		local frame = at * CFrame.new(30, 0, 0)
		ModelBuilder.Place(ModelBuilder.Build("Old_6", old.bricks), frame, folder)
		resident(folder, "CactusBoxer", frame * CFrame.new(old.resident), old.scale)
		ModelBuilder.Place(
			ModelBuilder.Build("OldRoof", ShowcaseFloorV1.Roof(6)),
			frame * CFrame.new(0, old.height, 0),
			folder
		)
	else
		local theme = if words.Ocean then "Ocean" else "Saloon"
		for tier = 1, 6 do
			local frame = at * CFrame.new((3.5 - tier) * ShowcasePreview.Pitch, 0, 0) -- слева направо для зрителя спереди
			local h = place(folder, frame, theme, tier, far)
			roof(folder, frame * CFrame.new(0, h, 0), tier)
			task.wait()
		end
	end
	folder.Parent = workspace
	local counts = {}
	for _, model in folder:GetChildren() do
		if model:IsA("Model") and not model.Name:find("Roof") then
			local lights = 0
			for _, d in model:GetDescendants() do
				if d:IsA("Light") then
					lights += 1
				end
			end
			table.insert(counts, ("%s=%d/%d"):format(model.Name, ModelBuilder.CountParts(model), lights))
		end
	end
	return ("деталей %d; этажи (детали/свет): %s"):format(
		ModelBuilder.CountParts(folder),
		table.concat(counts, " ")
	)
end

return ShowcasePreview

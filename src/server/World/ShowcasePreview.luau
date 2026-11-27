-- Предпросмотр этажей-витрин (D74, вариант B) для снимков владельцу. Только DEV, в место ничего не сохраняет
-- (папка workspace.__ShowcasePreview, Archivable = false). Режимы (строка mode, слова через пробел):
--   "row Saloon" | "row Ocean"  — шесть редкостей темы в ряд (у каждой плита-кровля), с живыми жильцами;
--   "tower"                     — башня из 12 этажей вперемешку, плита-кровля и колпак C;
--   "monsters <ItemId> [t=146]" — этаж-монстр существа (генератор MonsterFloor) в редкостях из t (по умолчанию 1, 4, 6);
--   "mtower"                    — башня из 12 этажей-монстров четырёх существ вперемешку и колпак C;
--   "signal"                    — проверка сигнала редкости: башня с 1 Алмазным, 1 Мифическим и 2 Золотыми этажами и
--                                 обычная башня рядом (через 75 стадов, как участки), у каждой маяк (луч, значок);
--   "farm"                      — 5 башен по 20 этажей на местах участков (замер FPS);
--   добавка "far"               — дальние версии этажей, "stage" — площадка-земля под снимки,
--   "eye=x,y,z"                 — точка зрителя в осях предпросмотра: этажи ближе FloorRarity.FarDistance к ней —
--                                 полные, остальные — дальние (как сменит версии клиент).
-- В Play строит поток игры (атрибуты ServerStorage.DevTools: ShowcaseMode, затем Showcase = CFrame): у потока MCP свои
-- копии модулей без загруженных мешей существ. В Edit — через FreshRequire (жильцы там — заглушки):
--   local W = game.ServerScriptService.Server.World
--   require(W.FreshRequire)(W.ShowcasePreview).Build(CFrame.new(0, 0, 0), "row Saloon stage")
-- Зависит от World/Models/ShowcaseFloor, MonsterFloor, World/MonsterParts, World/FloorSignal, ModelBuilder,
-- Util/ItemFactory, FloorDna, Config/FloorRarity.

local HttpService = game:GetService("HttpService")
local ServerScriptService = game:GetService("ServerScriptService")

local Server = ServerScriptService.Server
local ItemFactory = require(Server.Util.ItemFactory)
local ModelBuilder = require(Server.World.ModelBuilder)
local ShowcaseFloor = require(Server.World.Models.ShowcaseFloor)
local MonsterFloor = require(Server.World.Models.MonsterFloor)
local MonsterParts = require(Server.World.MonsterParts)
local FloorSignal = require(Server.World.FloorSignal)
local FloorRarity = require(game:GetService("ReplicatedStorage").Shared.Config.FloorRarity)
local FloorDna = require(game:GetService("ReplicatedStorage").Shared.FloorDna)

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

-- Башня из 12 этажей-монстров (снизу вверх): существо и редкость. Четыре существа трёх зон и четырёх семей силуэта.
ShowcasePreview.MonsterTower = {
	{ "CactusBoxer", 1 },
	{ "PizzaRat", 4 },
	{ "YetiCub", 1 },
	{ "BlazeOstrich", 1 },
	{ "CactusBoxer", 6 },
	{ "PizzaRat", 1 },
	{ "YetiCub", 4 },
	{ "BlazeOstrich", 4 },
	{ "CactusBoxer", 4 },
	{ "YetiCub", 6 },
	{ "PizzaRat", 1 },
	{ "BlazeOstrich", 6 },
}

-- Этаж-монстр существа itemId на месте frame: кирпичи, собственные части существа, жилец. Возвращает высоту.
local function placeMonster(folder: Instance, frame: CFrame, itemId: string, tier: number, far: boolean): number
	local built = if far then MonsterFloor.Far(itemId, tier) else MonsterFloor.Build(itemId, tier)
	assert(built, "нет ДНК существа " .. itemId)
	local name = ("%s_%d%s"):format(itemId, tier, if far then "_Far" else "")
	local model = ModelBuilder.Place(ModelBuilder.Build(name, built.bricks), frame, folder)
	MonsterParts.Add(model, frame, itemId, built.parts)
	model:SetAttribute("MeshRequests", #built.parts) -- в Play каждая заявка — одна деталь-меш
	FloorSignal.Decorate(model, tier, frame, built.height)
	resident(folder, built.item, frame * CFrame.new(built.resident), built.scale)
	return built.height
end

-- Проверка сигнала редкости: башня с редкими этажами (1 Алмазный, 1 Мифический, 2 Золотых) и обычная башня.
ShowcasePreview.SignalTower = {
	{ "CactusBoxer", 1 },
	{ "PizzaRat", 2 },
	{ "YetiCub", 1 },
	{ "BlazeOstrich", 4 },
	{ "PizzaRat", 1 },
	{ "YetiCub", 3 },
	{ "CactusBoxer", 6 },
	{ "BlazeOstrich", 2 },
	{ "YetiCub", 5 },
	{ "PizzaRat", 4 },
	{ "CactusBoxer", 1 },
	{ "BlazeOstrich", 2 },
}
ShowcasePreview.PlainTower = {
	{ "PizzaRat", 1 },
	{ "CactusBoxer", 2 },
	{ "BlazeOstrich", 1 },
	{ "YetiCub", 1 },
	{ "PizzaRat", 3 },
	{ "CactusBoxer", 1 },
	{ "YetiCub", 2 },
	{ "BlazeOstrich", 1 },
	{ "PizzaRat", 1 },
	{ "YetiCub", 2 },
	{ "CactusBoxer", 3 },
	{ "BlazeOstrich", 1 },
}
ShowcasePreview.PlotXs = { 150, 75, 0, -75, -150 } -- как участки карты (MapLayout)
local CAP_HEIGHT = 37 -- колпак C над плитой-кровлей

-- Башня этажей-монстров spec (снизу вверх) на месте at с плитой-кровлей, колпаком и маяком. eye — точка зрителя
-- (мир): этажи ближе FloorRarity.FarDistance — полные, остальные — дальние; без eye — все по флагу far.
local function monsterTower(folder: Instance, at: CFrame, spec: { { any } }, far: boolean, eye: Vector3?, owner: string)
	local y, last = 0, 1
	local tiers = {}
	for i, floor in spec do
		local tier = floor[2]
		local distant = far
		if eye then
			local centre = (at * CFrame.new(0, y + MonsterFloor.Height(tier) / 2, 0)).Position
			distant = (centre - eye).Magnitude >= FloorRarity.FarDistance
		end
		y += placeMonster(folder, at * CFrame.new(0, y, 0), floor[1], tier, distant)
		table.insert(tiers, tier)
		last = tier
		if i % 3 == 0 then
			task.wait()
		end
	end
	ModelBuilder.Place(ModelBuilder.Build("Roof", MonsterFloor.Roof(last)), at * CFrame.new(0, y, 0), folder)
	local cap = ModelBuilder.Build("Cap", ShowcaseFloor.Cap())
	ModelBuilder.Place(cap, at * CFrame.new(0, y + ShowcaseFloor.Slab, 0), folder)
	FloorSignal.Beacon(folder, at * CFrame.new(0, y + ShowcaseFloor.Slab + CAP_HEIGHT, 0), tiers, owner)
end

-- 20 этажей башни номер k для замера: существа по кругу, редкости — по весам, близким к игре, но с редкими этажами.
local function farmTower(k: number): { { any } }
	local creatures = { "CactusBoxer", "PizzaRat", "YetiCub", "BlazeOstrich" }
	local weights = { 50, 25, 12, 8, 4, 1 }
	local random = Random.new(100 + k)
	local spec = {}
	for i = 1, 20 do
		local roll, tier = random:NextNumber() * 100, 1
		for t, w in weights do
			roll -= w
			if roll <= 0 then
				tier = t
				break
			end
		end
		table.insert(spec, { creatures[(i + k) % 4 + 1], tier })
	end
	if k == 2 then
		spec[9][2] = 6 -- одна башня точно с Алмазным
	end
	return spec
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
	local eye: Vector3? = nil
	for word in (mode or ""):gmatch("%S+") do
		local x, y, z = word:match("^eye=([%-%d%.]+),([%-%d%.]+),([%-%d%.]+)$")
		if x then
			eye = (at * CFrame.new(tonumber(x) :: number, tonumber(y) :: number, tonumber(z) :: number)).Position
		end
	end
	if words.mtower then
		monsterTower(folder, at, ShowcasePreview.MonsterTower, far, eye, "Игрок")
	elseif words.signal then
		monsterTower(folder, at, ShowcasePreview.SignalTower, far, eye, "Везунчик")
		monsterTower(folder, at * CFrame.new(-75, 0, 0), ShowcasePreview.PlainTower, far, eye, "Сосед")
	elseif words.farm then
		for k, x in ShowcasePreview.PlotXs do
			monsterTower(folder, at * CFrame.new(x, 0, 0), farmTower(k), far, eye, "Игрок " .. k)
		end
	elseif words.monsters then
		local tiers = { 1, 4, 6 }
		local itemId = "CactusBoxer"
		for word in (mode or ""):gmatch("%S+") do
			local list = word:match("^t=(%d+)$")
			if list then
				tiers = {}
				for digit in list:gmatch("%d") do
					table.insert(tiers, tonumber(digit) :: number)
				end
			elseif FloorDna.Has(word) then
				itemId = word
			end
		end
		for i, tier in tiers do
			local frame = at * CFrame.new(((#tiers + 1) / 2 - i) * ShowcasePreview.Pitch, 0, 0)
			local h = placeMonster(folder, frame, itemId, tier, far)
			ModelBuilder.Place(ModelBuilder.Build("Roof", MonsterFloor.Roof(tier)), frame * CFrame.new(0, h, 0), folder)
			task.wait()
		end
	elseif words.tower then
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
			local parts = ModelBuilder.CountParts(model)
			local requests = model:GetAttribute("MeshRequests")
			if requests then -- собственные части существа считаются по заявкам (в Edit они собраны из блоков)
				parts = requests
				for _, d in model:GetDescendants() do
					if d:IsA("BasePart") and d.Name:sub(1, 8) ~= "Monster_" then
						parts += 1
					end
				end
			end
			table.insert(counts, ("%s=%d/%d"):format(model.Name, parts, lights))
		end
	end
	return ("деталей %d; этажи (детали/свет): %s"):format(
		ModelBuilder.CountParts(folder),
		table.concat(counts, " ")
	)
end

return ShowcasePreview

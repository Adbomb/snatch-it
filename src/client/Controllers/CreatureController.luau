-- Живые существа на клиенте (D55): все клиенты двигают их одинаково — поза существа у босса — функция общего времени
-- сервера и зерна uid (Shared/CreatureMotion), её же сервер считает при броске Ловибума. Сеть не нужна: сервер только
-- пишет атрибуты предмета — Home (место у босса, CFrame низа), Drop (высота места над землёй), CatchMode ("Catch" |
-- "Flee" | "Hidden"), CatchSince, CatchFace, CatchAnchor. У босса клиент ставит корень предмета в позу (локально, у
-- сервера он на месте); части существ из скелета (босс 3) — Transform моторов по ролям (Shared/CreatureAnim).
-- Части, которые смотрят на игрока (стражи сейфа), поворачиваются к камере этого клиента.
-- Экспонат на постаменте (атрибут Slot) — спокойно на месте: только суставы и лёгкое покачивание меша (D55: без
-- перемещения, корень не трогается — презентация и сервер двигают его сами); в руках — «трепыхание». Дальние (дальше
-- Catch.Creature.ViewRadius от камеры) не считаются, средние — через кадр. Пойманное (Hidden) спрятано до конца боя.
-- У ближайших существ у боссов — тонкая светлая обводка (UITokens.CreatureOutline: силуэт не сливается с подушкой);
-- во время своей поимки обводок нет. Highlight на детали обводит только её саму, а блоки существа — дети невидимого
-- корня: на время обводки блоки у этого клиента лежат в модели «Outline» внутри корня (её и обводит Highlight), потом
-- возвращаются в корень — копия экспоната (PresentationController) и сервер видят прежнее устройство.
-- Зависит от Shared/CreatureMotion, Shared/CreatureAnim, Config/Items, Config/CreatureRigs, Config/GameConfig,
-- Config/UITokens.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local CreatureAnim = require(Shared:WaitForChild("CreatureAnim"))
local CreatureMotion = require(Shared:WaitForChild("CreatureMotion"))
local CreatureRigs = require(Config:WaitForChild("CreatureRigs"))
local GameConfig = require(Config:WaitForChild("GameConfig"))
local Items = require(Config:WaitForChild("Items"))
local UITokens = require(Config:WaitForChild("UITokens"))

local C = GameConfig.Catch.Creature
local OUTLINE = UITokens.CreatureOutline
local NEAR = 60 -- ближе — каждый кадр, дальше — через кадр

local CreatureController = {}

type Entry = {
	root: BasePart,
	itemId: string,
	seed: number,
	rig: any?,
	motors: { [string]: Motor6D },
	out: { [string]: CFrame },
	params: CreatureMotion.Params,
	visualWeld: Weld?,
	visualC0: CFrame?,
	hidden: boolean,
	odd: boolean,
	looks: boolean, -- есть части, которые поворачиваются к зрителю (стражи сейфа)
	outline: Highlight?,
	group: Model?, -- модель «Outline» с блоками на время обводки
}

local tracked: { [BasePart]: Entry } = {}
local frame = 0
local sinceOutline = math.huge

-- Включить или снять обводку существа: Highlight только контуром на меше «Visual» или на модели «Outline», куда на это
-- время переложены блоки корня; снятие возвращает блоки в корень.
local function setOutline(entry: Entry, on: boolean)
	local root = entry.root
	if on and not entry.outline then
		local adornee: Instance
		local visual = root:FindFirstChild("Visual")
		if visual and visual:IsA("BasePart") then
			adornee = visual
		else
			local blocks = {}
			for _, child in root:GetChildren() do
				if child:IsA("BasePart") then
					table.insert(blocks, child)
				end
			end
			local group = Instance.new("Model")
			group.Name = "Outline"
			group.Archivable = false
			group.Parent = root
			for _, b in blocks do
				b.Parent = group
			end
			entry.group = group
			adornee = group
		end
		local h = Instance.new("Highlight")
		h.Name = "Outline"
		h.FillTransparency = 1
		h.OutlineColor = OUTLINE.Color
		h.OutlineTransparency = OUTLINE.Transparency
		h.DepthMode = Enum.HighlightDepthMode.Occluded
		h.Adornee = adornee
		h.Parent = root
		entry.outline = h
	elseif not on and entry.outline then
		entry.outline:Destroy()
		entry.outline = nil
		local group = entry.group
		entry.group = nil
		if group then
			for _, child in group:GetChildren() do
				child.Parent = root
			end
			group:Destroy()
		end
	end
end

-- Обводка у ближайших существ у боссов (не больше OUTLINE.Max в OUTLINE.Distance), кроме спрятанных и во время своей
-- поимки.
local function updateOutlines(eye: Vector3)
	local catching = Players.LocalPlayer:GetAttribute("Catching") ~= nil
	local near: { { entry: Entry, dist: number } } = {}
	if not catching then
		for root, entry in tracked do
			-- чужое учебное существо (TutorialOwner — другой ученик) у меня спрятано: без обводки
			local owner = root:GetAttribute("TutorialOwner")
			local foreign = owner ~= nil and owner ~= Players.LocalPlayer.UserId
			if
				root.Parent
				and root.Anchored
				and typeof(root:GetAttribute("Home")) == "CFrame"
				and not entry.hidden
				and not foreign
			then
				local dist = (root.Position - eye).Magnitude
				if dist < OUTLINE.Distance then
					table.insert(near, { entry = entry, dist = dist })
				end
			end
		end
		table.sort(near, function(a, b)
			return a.dist < b.dist
		end)
	end
	local on: { [Entry]: boolean } = {}
	for i = 1, math.min(#near, OUTLINE.Max) do
		on[near[i].entry] = true
	end
	for _, entry in tracked do
		setOutline(entry, on[entry] == true)
	end
end

local function track(root: BasePart)
	if tracked[root] then
		return
	end
	local itemId = root:GetAttribute("ItemId")
	local uid = root:GetAttribute("ItemUid")
	local def = type(itemId) == "string" and Items[itemId]
	if not def or type(uid) ~= "string" then
		return
	end
	local seed = CreatureMotion.SeedOf(uid)
	local entry: Entry = {
		root = root,
		itemId = itemId,
		seed = seed,
		rig = CreatureRigs[itemId],
		motors = {},
		out = {},
		params = {
			seed = seed,
			radius = CreatureMotion.WanderRadius(def.boss),
			scale = CreatureMotion.ScaleOf(def.size),
			mode = "Wander",
		},
		visualWeld = nil,
		visualC0 = nil,
		hidden = false,
		odd = seed % 2 == 1,
		looks = false,
	}
	if entry.rig then
		for _, spec in entry.rig.Parts do
			local role = CreatureAnim.Roles[spec.role]
			if role and role.kind == "look" and not spec.hidden then
				entry.looks = true
			end
		end
		for _, d in root:GetDescendants() do
			if d:IsA("Motor6D") then
				entry.motors[d.Name] = d
			end
		end
	else
		local visual = root:FindFirstChild("Visual")
		local weld = visual and visual:FindFirstChildOfClass("Weld")
		if weld then
			entry.visualWeld = weld
			entry.visualC0 = weld.C0
		end
	end
	tracked[root] = entry
end

local function setHidden(entry: Entry, hidden: boolean)
	if entry.hidden == hidden then
		return
	end
	entry.hidden = hidden
	for _, d in entry.root:GetDescendants() do
		if d:IsA("BasePart") then
			d.LocalTransparencyModifier = if hidden then 1 else 0
		elseif d:IsA("BillboardGui") then
			d.Enabled = not hidden
		end
	end
end

local function attrNumber(root: BasePart, name: string): number?
	local v = root:GetAttribute(name)
	return if type(v) == "number" then v else nil
end

local function step(dt: number)
	frame += 1
	local camera = workspace.CurrentCamera
	if not camera then
		return
	end
	local eye = camera.CFrame.Position
	local now = workspace:GetServerTimeNow()
	sinceOutline += dt
	if sinceOutline >= OUTLINE.Every then
		sinceOutline = 0
		updateOutlines(eye)
	end
	for root, entry in tracked do
		if not root.Parent then
			tracked[root] = nil
			continue
		end
		local dist = (root.Position - eye).Magnitude
		if dist > C.ViewRadius or (dist > NEAR and (frame % 2 == 0) == entry.odd) then
			continue
		end
		local home = root:GetAttribute("Home")
		local mode, moving, dodge = "Wander", false, 0
		if typeof(home) == "CFrame" and root.Anchored then
			-- у босса: поза — общая функция (сервер считает так же)
			local p = entry.params
			local catchMode = root:GetAttribute("CatchMode")
			setHidden(entry, catchMode == "Hidden")
			p.mode = if catchMode == "Catch" or catchMode == "Flee" then catchMode else "Wander"
			p.since = attrNumber(root, "CatchSince")
			p.face = attrNumber(root, "CatchFace")
			p.anchor = attrNumber(root, "CatchAnchor")
			p.drop = attrNumber(root, "Drop")
			local pose = CreatureMotion.Pose(p, now)
			root.CFrame = CreatureMotion.WorldCFrame(home, pose) * CFrame.new(0, root.Size.Y / 2, 0)
			mode, moving, dodge = p.mode, pose.moving, pose.dodge
		else
			setHidden(entry, false)
			mode = if root.Anchored and root:GetAttribute("Slot") ~= nil then "Calm" else "Held"
		end
		if entry.rig then
			-- к зрителю — в осях модели (скелет смотрит в +Z, корень — в −Z: поворот на 180°)
			local view: Vector3? = nil
			if entry.looks then
				local l = root.CFrame:PointToObjectSpace(eye)
				view = Vector3.new(-l.X, l.Y, -l.Z)
			end
			CreatureAnim.Transforms(entry.rig, entry.seed, now, mode, moving, dodge, entry.out, view)
			for name, cf in entry.out do
				local motor = entry.motors[name]
				if motor then
					motor.Transform = cf
				end
			end
		elseif entry.visualWeld and entry.visualC0 and mode ~= "Wander" and mode ~= "Catch" and mode ~= "Flee" then
			-- меш на постаменте и в руках: покачивание вокруг центра (корень не двигается)
			local p = table.clone(entry.params)
			p.mode = "Calm"
			local pose = CreatureMotion.Pose(p, if mode == "Held" then now * 3 else now)
			entry.visualWeld.C0 = entry.visualC0 * CFrame.Angles(pose.lean, pose.yaw * 0.5, pose.roll)
		end
	end
end

function CreatureController.Init()
	for _, d in workspace:GetDescendants() do
		if d:IsA("BasePart") and d:GetAttribute("ItemUid") ~= nil then
			track(d)
		end
	end
	workspace.DescendantAdded:Connect(function(d)
		if d:IsA("BasePart") then
			-- атрибут ItemUid ставится сразу после создания: подождать кадр
			task.defer(function()
				if d.Parent and d:GetAttribute("ItemUid") ~= nil then
					track(d)
				end
			end)
		end
	end)
	RunService.PreSimulation:Connect(step)
end

return CreatureController

-- Вид музея D48-C по уровню (ТЗ владельца 2026-11-06): ставит модули по Config/MuseumLayout.Modules и для каждого
-- решает, чем его показать. GameConfig.Museum.Visual = "Parts" — временная Part-версия (World/Models/MuseumD48);
-- "Mesh" — меши пачки Pack3_d48 (World/MeshBuilder), если у модуля есть MeshId и все его меши загрузились, иначе тот же
-- модуль из Part-версии (с предупреждением в Output). Оболочка модуля (пол, стены, ступени — кирпичи с collide) строится всегда; при мешах
-- она невидима, поэтому столкновения и запросы одинаковы в обоих режимах и не пропадают без MeshId.
-- Детали вида модулей хранилища в здание не входят: их шаблон (ReplicatedStorage.MuseumVisual.VaultDecor, оси
-- участка) копирует к себе только клиент владельца (Controllers/MuseumVisualController).
-- Зависит от GameConfig, Config/MuseumLayout, World/ModelBuilder, World/MeshBuilder, World/Models/MuseumD48, Util/Log.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local MuseumLayout = require(ReplicatedStorage.Shared.Config.MuseumLayout)
local Log = require(ServerScriptService.Server.Util.Log)
local MeshBuilder = require(ServerScriptService.Server.World.MeshBuilder)
local ModelBuilder = require(ServerScriptService.Server.World.ModelBuilder)
local MuseumD48 = require(ServerScriptService.Server.World.Models.MuseumD48)

local FOLDER = "MuseumVisual"
local VAULT_DECOR = "VaultDecor"
local SOFT = "LegoSquaresSoft" -- плитка D36 по UV мешей (1 единица UV = 8 ст.)

local warned = false

local MuseumVisual = {}

-- Модуль model показывается мешами: режим Mesh и у модуля есть меши в World/MeshModels.
function MuseumVisual.UsesMesh(model: string): boolean
	if GameConfig.Museum.Visual ~= "Mesh" then
		return false
	end
	if MeshBuilder.IsReady(model) then
		return true
	end
	if not warned then
		warned = true
		Log.Warn(
			"MuseumVisual",
			"режим Mesh: у модулей музея D48 нет MeshId или меши не загрузились (World/MeshModels) — такие модули "
				.. "показаны Part-версией, стены и столкновения те же"
		)
	end
	return false
end

-- Модули уровня level (по раскладке).
function MuseumVisual.Modules(level: number): { MuseumLayout.Module }
	local out = {}
	for _, m in MuseumLayout.Modules do
		if level >= m.from and level <= m.to then
			table.insert(out, m)
		end
	end
	return out
end

local function frame(origin: CFrame, m: MuseumLayout.Module): CFrame
	return origin * CFrame.new(m.position) * CFrame.Angles(0, math.rad(m.yaw), 0)
end

-- Кирпичи модуля для здания: оболочка (при мешах — невидимая) и, если модуль из Part-версии, детали вида;
-- детали хранилища — только в шаблоне клиента.
local function buildingBricks(name: string, mesh: boolean): { ModelBuilder.Brick }
	local out = {}
	for _, brick in MuseumD48.Module(name) or {} do
		local b = brick :: any
		if b.shell then
			if mesh then
				b.transparency = 1
				b.shadow = false
			end
			table.insert(out, brick)
		elseif not mesh and not MuseumD48.VaultModules[name] then
			table.insert(out, brick)
		end
	end
	return out
end

-- Здание музея уровня level у участка с началом origin (центр участка на полу зала): модель Building в parent.
-- Каждый модуль — своя Model с атрибутом Module (по нему клиент находит, например, створки решётки).
function MuseumVisual.Build(level: number, origin: CFrame, parent: Instance): Model
	local building = Instance.new("Model")
	building.Name = "Building"
	for i, m in MuseumVisual.Modules(level) do
		local at = frame(origin, m)
		local mesh = MuseumVisual.UsesMesh(m.model)
		local model = ModelBuilder.Build(m.model, buildingBricks(m.model, mesh))
		model.Name = ("%s_%d"):format(m.model, i)
		model:SetAttribute("Module", m.model)
		model:SetAttribute("Mesh", mesh)
		ModelBuilder.Place(model, at, building)
		if mesh and not MuseumD48.VaultModules[m.model] then
			MeshBuilder.Build(m.model, at, model, { name = "Mesh", variant = SOFT })
		end
	end
	building.WorldPivot = origin
	building.Parent = parent
	return building
end

-- Свет хранилища (только у владельца): точечные лампы в осях участка.
local VAULT_LIGHTS = {
	{ at = Vector3.new(-8, -3.2, 4), color = Color3.fromHex("BFEFFF"), range = 26, brightness = 1.1 },
	{ at = Vector3.new(8, -3.2, 4), color = Color3.fromHex("BFEFFF"), range = 26, brightness = 1.1 },
	{ at = Vector3.new(0, -3.2, 15), color = Color3.fromHex("FFE2A8"), range = 18, brightness = 0.9 },
}

-- Шаблон обстановки хранилища в осях участка: детали вида модулей хранилища (Part-версия или меши) и свет.
-- Строится один раз; клиент владельца копирует его и ставит в начало своего участка.
function MuseumVisual.PublishVaultDecor()
	local folder = ReplicatedStorage:FindFirstChild(FOLDER) or Instance.new("Folder")
	folder.Name = FOLDER
	local old = folder:FindFirstChild(VAULT_DECOR)
	if old then
		old:Destroy()
	end
	local decor = Instance.new("Model")
	decor.Name = VAULT_DECOR
	for _, m in MuseumVisual.Modules(1) do
		if MuseumD48.VaultModules[m.model] then
			local at = frame(CFrame.identity, m)
			if MuseumVisual.UsesMesh(m.model) then
				MeshBuilder.Build(m.model, at, decor, { name = m.model, variant = SOFT })
			else
				local bricks = {}
				for _, brick in MuseumD48.Module(m.model) or {} do
					if not (brick :: any).shell then
						table.insert(bricks, brick)
					end
				end
				ModelBuilder.Place(ModelBuilder.Build(m.model, bricks), at, decor)
			end
		end
	end
	local holder = Instance.new("Part")
	holder.Name = "Lights"
	holder.Anchored = true
	holder.CanCollide = false
	holder.CanQuery = false
	holder.CanTouch = false
	holder.Transparency = 1
	holder.Size = Vector3.new(1, 1, 1)
	holder.CFrame = CFrame.new(0, MuseumLayout.Vault.Floor + 1, 0)
	holder.Parent = decor
	for i, light in VAULT_LIGHTS do
		local attachment = Instance.new("Attachment")
		attachment.Name = "Light_" .. i
		attachment.Parent = holder
		attachment.WorldPosition = light.at
		local point = Instance.new("PointLight")
		point.Color = light.color
		point.Range = light.range
		point.Brightness = light.brightness
		point.Shadows = false
		point.Parent = attachment
	end
	decor.WorldPivot = CFrame.identity
	decor.Parent = folder
	folder.Parent = ReplicatedStorage
end

return MuseumVisual

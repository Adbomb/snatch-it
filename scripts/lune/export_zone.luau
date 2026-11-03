--!nocheck
-- Выгрузка зоны для предпросмотра без Roblox Studio (Lune → JSON → scripts/blender/preview_zone.py): плита пола
-- зоны, декор, босс в стойке (части скелета блоками цвета, как до импорта мешей) и заготовки 4 предметов на местах
-- слотов. Координаты — мировые, Roblox (Y вверх). Пока сделано для зон 1 и 2.
-- Запуск из корня репозитория: lune run scripts/lune/export_zone.luau <зона> <файл.json>

local fs = require("@lune/fs")
local process = require("@lune/process")
local serde = require("@lune/serde")

local Env = require("./env")

local roblox = Env.roblox
local Vector3, CFrame, Color3 = roblox.Vector3, roblox.CFrame, roblox.Color3

local GameConfig = Env.Require("ReplicatedStorage.Shared.Config.GameConfig")
local Items = Env.Require("ReplicatedStorage.Shared.Config.Items")
local MapLayout = Env.Require("ServerScriptService.Server.World.MapLayout")
local Junkyard = Env.Require("ServerScriptService.Server.World.Models.Junkyard")
local FleaMarket = Env.Require("ServerScriptService.Server.World.Models.FleaMarket")

local RIGS = {
	[1] = Env.Require("ReplicatedStorage.Shared.Config.Boss1DogRig"),
	[2] = Env.Require("ReplicatedStorage.Shared.Config.Boss2TraderRig"),
}
local DECOR = {
	[1] = Junkyard.Zone,
	[2] = function()
		return (FleaMarket.Zone())
	end,
}

local zone = tonumber(process.args[1] or "2") or 2
local target = process.args[2] or "zone.json"
assert(DECOR[zone], "Выгрузка есть только для зон 1 и 2")

local out = {}

local function add(size, cframe, color, shape: string?, material: string?, transparency: number?)
	table.insert(out, {
		s = { size.X, size.Y, size.Z },
		cf = { cframe:GetComponents() },
		c = { color.R, color.G, color.B },
		shape = shape or "Block",
		mat = material or "Plastic",
		t = transparency or 0,
	})
end

local frame = MapLayout.ZoneCFrame(zone)
local cfg = GameConfig.Zones[zone]

-- Пол зоны (как в WorldBuilder: верх на Heights.Path).
local center = frame.Position
add(
	Vector3.new(MapLayout.ZoneHalfWidth * 2, 0.4, MapLayout.ZoneSize),
	CFrame.new(center.X, MapLayout.Heights.Path - 0.2, center.Z),
	Color3.fromHex(cfg.floor)
)

for _, brick in DECOR[zone]() do
	add(
		brick.size,
		frame * brick.cframe,
		brick.color,
		brick.shape,
		brick.material and brick.material.Name,
		brick.transparency
	)
end

-- Босс в стойке: части-заготовки по скелету (как BossService до импорта мешей).
local rig = RIGS[zone]
local spot = MapLayout.BossSpot
local home = CFrame.new((frame * CFrame.new(spot.X, 0, spot.Y)).Position)
local stand = rig.Poses.stand
local world = {}
for _, name in rig.Order do
	local info = rig.Parts[name]
	local n = stand[name]
	local transform = CFrame.new(n[1], n[2], n[3], n[4], n[5], n[6], n[7], n[8], n[9], n[10], n[11], n[12])
	local joint
	if info.parent then
		local parentInfo = rig.Parts[info.parent]
		joint = world[info.parent] * CFrame.new(info.pivot - parentInfo.pivot) * transform
	else
		joint = home * CFrame.new(info.pivot) * transform
	end
	world[name] = joint
	add(info.size, joint * CFrame.new(info.center), Color3.fromHex(info.color))
end

-- Заготовки предметов на слотах: первые по алфавиту предметы босса этой зоны (как ItemFactory до импорта).
local ids = {}
for id, def in Items do
	if type(def) == "table" and def.boss == zone and not def.legacy then
		table.insert(ids, id)
	end
end
table.sort(ids)
local slot = 0
for _, point in MapLayout.ArtSlotPoints() do
	if point.zone == zone then
		slot += 1
		local def = Items[ids[slot]]
		local color = if typeof(def.color) == "Color3" then def.color else Color3.fromHex(def.color)
		add(def.size, point.cframe * CFrame.new(0, def.size.Y / 2, 0), color)
	end
end

fs.writeFile(target, serde.encode("json", { zone = zone, center = { center.X, center.Y, center.Z }, bricks = out }))
print(("Зона %d: %d деталей → %s"):format(zone, #out, target))

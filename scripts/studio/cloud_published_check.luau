-- Проверка опубликованной версии DEV-места на сервере Roblox (этап C.2.4): Open Cloud Luau Execution —
-- POST /cloud/v2/universes/10776417796/places/81392528393796/luau-execution-session-tasks, тело {"script": <этот файл>},
-- право universe.place.luau-execution-session:write (выдаёт владелец в Studio → Assistant → MCP Permissions).
-- Скрипты места в задаче не запускаются: только require конфигов. Возвращает версию места, вид сервера тестового
-- режима, Active ауры и загрузку всех мешей (CreateMeshPartAsync, как в игре) с отказами по ID. Ничего не сохраняет.
local AssetService = game:GetService("AssetService")
local RS = game:GetService("ReplicatedStorage")
local SSS = game:GetService("ServerScriptService")
local started = os.clock()
local result = {
	placeVersion = game.PlaceVersion,
	gameId = game.GameId,
	placeId = game.PlaceId,
	creatorId = game.CreatorId,
	privateServerId = game.PrivateServerId,
}
local ok, err = pcall(function()
	local OwnerTest = require(SSS.Server.Util.OwnerTest)
	result.ownerTestKind = OwnerTest.ServerKind()
	local GameConfig = require(RS.Shared.Config.GameConfig)
	result.ownerTestEnabled = GameConfig.OwnerTest and GameConfig.OwnerTest.Enabled
	result.devMode = GameConfig.DevMode
	local BossAura = require(RS.Shared.Config.BossAura)
	result.auraActive = BossAura.Active
	local BossService = require(SSS.Server.Services.BossService)
	result.closedAllowed = BossService.ClosedAllowed()
end)
result.requireOk = ok
result.requireErr = if ok then nil else tostring(err)

local ids, order = {}, {}
local function add(v, src)
	if type(v) == "number" then
		v = "rbxassetid://" .. v
	end
	if type(v) ~= "string" then
		return
	end
	local n = string.match(v, "rbxassetid://(%d+)") or string.match(v, "^(%d+)$")
	if n and not ids[n] then
		ids[n] = src
		table.insert(order, n)
	end
end
local function scan(t, src, depth, meshKey)
	if depth > 10 or type(t) ~= "table" then
		return
	end
	for k, v in t do
		local key = string.lower(tostring(k))
		local isMesh = meshKey or string.find(key, "mesh", 1, true) ~= nil
		if type(v) == "table" then
			scan(v, src, depth + 1, isMesh)
		elseif isMesh then
			add(v, src)
		end
	end
end
local sources = {
	{ "BossModels", RS.Shared.Config:FindFirstChild("BossModels") },
	{ "ItemModels", RS.Shared.Config:FindFirstChild("ItemModels") },
	{ "CreatureRigs", RS.Shared.Config:FindFirstChild("CreatureRigs") },
	{ "LovibumRigs", RS.Shared.Config:FindFirstChild("LovibumRigs") },
	{ "Boss10DragonRig", RS.Shared.Config:FindFirstChild("Boss10DragonRig") },
	{ "MeshModels", SSS.Server.World:FindFirstChild("MeshModels") },
}
for _, s in sources do
	if s[2] then
		local okm, mod = pcall(require, s[2])
		if okm then
			scan(mod, s[1], 0, false)
		end
	end
end
result.meshTotal = #order

local failed, okCount, done = {}, 0, 0
local nextIndex = 0
local function worker()
	while true do
		nextIndex += 1
		local i = nextIndex
		if i > #order or os.clock() - started > 250 then
			return
		end
		local id = order[i]
		local okp, e = pcall(function()
			local part = AssetService:CreateMeshPartAsync(Content.fromUri("rbxassetid://" .. id))
			part:Destroy()
		end)
		done += 1
		if okp then
			okCount += 1
		else
			table.insert(failed, ids[id] .. " " .. id .. ": " .. string.sub(tostring(e), 1, 120))
		end
	end
end
local running = 0
for _ = 1, 16 do
	running += 1
	task.spawn(function()
		worker()
		running -= 1
	end)
end
while running > 0 and os.clock() - started < 270 do
	task.wait(0.5)
end
result.meshChecked = done
result.meshOk = okCount
result.meshFailed = #failed
result.failedList = failed
result.seconds = math.floor(os.clock() - started)
return result

--!nocheck
-- Загрузчик модулей проекта для Lune (проверки без Roblox Studio, 2026-11-03): исполняет модули src/ так, как их
-- видит игра после Rojo — game:GetService(…), require(путь), script.Parent, WaitForChild. Типы Roblox (Vector3,
-- CFrame, Instance, Enum…) — из @lune/roblox; Random — своя замена (другая последовательность, чем в Roblox, поэтому
-- декор, который проверяется здесь, не должен зависеть от Random). Службы движка (CollectionService, RunService,
-- Players…) — заглушки: годится для данных и построения моделей, не для игровой логики.
-- Используется: lune run scripts/lune/check_world.luau, lune run scripts/lune/check_config.luau.

local fs = require("@lune/fs")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")
local task = require("@lune/task")

local MOUNTS = {
	{ path = { "ReplicatedStorage", "Shared" }, dir = "src/shared" },
	{ path = { "ServerScriptService", "Server" }, dir = "src/server" },
	{ path = { "StarterPlayer", "StarterPlayerScripts", "Client" }, dir = "src/client" },
}

local Env = {}

local PathMT = {}

local function proxy(path: { string })
	return setmetatable({ __path = path }, PathMT)
end

local function child(path: { string }, name: string)
	local out = table.clone(path)
	table.insert(out, name)
	return proxy(out)
end

-- Файл модуля по пути в дереве Rojo (nil — вне проекта или такого нет).
function Env.FileOf(path: { string }): string?
	for _, mount in MOUNTS do
		local n = #mount.path
		local same = #path >= n
		for i = 1, n do
			same = same and path[i] == mount.path[i]
		end
		if same then
			local rest = table.concat(path, "/", n + 1)
			local base = mount.dir .. (if rest ~= "" then "/" .. rest else "")
			for _, ext in { ".luau", ".server.luau", ".client.luau", "/init.luau" } do
				if fs.isFile(base .. ext) then
					return base .. ext
				end
			end
			return nil
		end
	end
	return nil
end

PathMT.__index = function(self, key)
	local path = rawget(self, "__path")
	if key == "WaitForChild" then
		return function(_, name)
			return child(path, name)
		end
	elseif key == "FindFirstChild" then
		return function(_, name)
			return child(path, name)
		end
	elseif key == "Name" then
		return path[#path]
	elseif key == "Parent" then
		local out = table.clone(path)
		table.remove(out)
		return proxy(out)
	end
	return child(path, key)
end
PathMT.__tostring = function(self)
	return table.concat(rawget(self, "__path"), ".")
end

-- Random как в Roblox (NextNumber, NextInteger), но своя последовательность.
local Random = {}
Random.__index = Random
function Random.new(seed: number?)
	return setmetatable({ state = (seed or os.time()) % 2147483647 + 1 }, Random)
end
function Random:NextNumber(min: number?, max: number?): number
	self.state = (self.state * 48271) % 2147483647
	local x = self.state / 2147483647
	if min then
		return min + (max - min) * x
	end
	return x
end
function Random:NextInteger(min: number, max: number): number
	return math.floor(self:NextNumber(min, max + 1 - 1e-9))
end

local stub = setmetatable({}, {
	__index = function(_, _key)
		return function()
			return nil
		end
	end,
})

local services = {
	ReplicatedStorage = proxy({ "ReplicatedStorage" }),
	ServerScriptService = proxy({ "ServerScriptService" }),
	StarterPlayer = proxy({ "StarterPlayer" }),
	RunService = {
		IsStudio = function()
			return false
		end,
		IsRunning = function()
			return false
		end,
		IsServer = function()
			return true
		end,
		Heartbeat = { Connect = function() end },
		Stepped = { Connect = function() end },
	},
	CollectionService = { AddTag = function() end, HasTag = function()
		return false
	end, GetTagged = function()
		return {}
	end },
}

local game = {
	GetService = function(_, name)
		return services[name] or stub
	end,
}
game.ServerScriptService = services.ServerScriptService
game.ReplicatedStorage = services.ReplicatedStorage

local cache: { [string]: any } = {}
local requireModule

local function makeEnv(own: { string })
	local env = {}
	for _, name in {
		"Vector3", "Vector2", "CFrame", "Color3", "ColorSequence", "ColorSequenceKeypoint", "NumberSequence",
		"NumberSequenceKeypoint", "NumberRange", "UDim", "UDim2", "Rect", "Ray", "Region3", "BrickColor", "Font",
		"Enum", "Instance", "PhysicalProperties", "Faces", "Axes",
	} do
		env[name] = roblox[name]
	end
	env.Random = Random
	env.game = game
	env.workspace = stub
	env.task = task
	env.warn = function(...)
		print("[warn]", ...)
	end
	env.script = proxy(own)
	env.require = requireModule
	return setmetatable(env, { __index = _G })
end

requireModule = function(target)
	local path = if type(target) == "table" then rawget(target, "__path") else nil
	assert(path, "require: не путь Rojo — " .. tostring(target))
	local file = Env.FileOf(path)
	assert(file, "require: нет модуля " .. table.concat(path, "."))
	if cache[file] == nil then
		local source = fs.readFile(file)
		local fn = luau.load(source, { debugName = file, environment = makeEnv(path) })
		cache[file] = fn()
	end
	return cache[file]
end

-- Модуль по пути вида "ServerScriptService.Server.World.MapLayout".
function Env.Require(dotted: string)
	return requireModule(proxy(string.split(dotted, ".")))
end

-- Детали для World/FaceCheck из кирпичей ModelBuilder: у деталей Lune нет вычисляемого Position, поэтому — таблицы
-- с теми полями, что читает проверка (IsA, Shape, Transparency, CFrame, Size, Position, Name, Parent).
function Env.FakeRoot(groups: { { name: string, bricks: { any } } })
	local list = {}
	for _, group in groups do
		local model = { Name = group.name }
		for _, b in group.bricks do
			local isTruss = b.shape == "Truss"
			table.insert(list, {
				Name = b.name or "Brick",
				Parent = model,
				Shape = if b.shape and b.shape ~= "Block" and not isTruss
					then (roblox.Enum.PartType :: any)[b.shape]
					else roblox.Enum.PartType.Block,
				Transparency = b.transparency or 0,
				CFrame = b.cframe,
				Size = b.size,
				Position = b.cframe.Position,
				IsA = function(_, cls)
					return not isTruss and (cls == "Part" or cls == "BasePart")
				end,
			})
		end
	end
	return {
		GetDescendants = function()
			return list
		end,
	}
end

Env.roblox = roblox
Env.Random = Random -- своя замена Random (для проверок со случайностью)
Env.services = services
return Env

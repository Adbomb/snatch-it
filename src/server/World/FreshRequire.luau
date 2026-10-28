-- Загружает ModuleScript заново вместе со всеми его зависимостями, минуя кэш require.
-- Нужно только для предпросмотра в режиме редактирования: там require (MCP, плагины) запоминает модули,
-- и правки кода, пришедшие через Rojo, не видны до перезапуска Studio. В игре не используется.
--   require(game.ServerScriptService.Server.World.FreshRequire)(game.ServerScriptService.Server.World.Preview).Build()
-- Этот модуль менять не нужно (его самого кэш не обновит). Ни от чего не зависит.

return function(root: ModuleScript): any
	local loaded: { [ModuleScript]: any } = {}
	local function load(module: ModuleScript): any
		if loaded[module] ~= nil then
			return loaded[module]
		end
		local chunk, err = loadstring(module.Source, "=" .. module:GetFullName())
		assert(chunk, err)
		local env = setmetatable({
			script = module,
			require = function(target: any): any
				if typeof(target) == "Instance" and target:IsA("ModuleScript") then
					return load(target)
				end
				return require(target)
			end,
		}, { __index = getfenv(0) })
		setfenv(chunk, env)
		local result = chunk()
		loaded[module] = result
		return result
	end
	return load(root)
end

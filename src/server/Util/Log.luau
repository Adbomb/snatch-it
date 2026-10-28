-- Единый формат логов сервера. Debug печатается только при GameConfig.DevMode.
-- Зависит от Shared/Config/GameConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

local Log = {}

function Log.Debug(tag: string, message: string)
	if GameConfig.DevMode then
		print(("[%s] %s"):format(tag, message))
	end
end

function Log.Warn(tag: string, message: string)
	warn(("[%s] %s"):format(tag, message))
end

return Log

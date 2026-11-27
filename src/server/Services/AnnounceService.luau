-- Объявления о редком этаже (D74, сигнал редкости; владелец 2026-11-27): «<имя> выбил <редкость> этаж!».
-- Мифический — всем на сервере (тост Notify); Алмазный — ещё и на все серверы (MessagingService, тема
-- FloorRarity.Announce.Topic). Частота: сервер публикует не чаще раза в PublishGap секунд, чужие объявления
-- показывает не чаще раза в ShowGap секунд (лишние пропускаются). Кому объявлять — Config/FloorRarity.Signal
-- (announce = "Server" | "Global"). В Studio без доступа к API публикация молча не проходит — свой сервер объявление
-- получает всегда.
-- AnnounceService.Audience — подмена списка получателей, AnnounceService.Publish — подмена публикации (тесты).
-- Зависит от Config/FloorRarity, Util/Notify, Util/Log.

local MessagingService = game:GetService("MessagingService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local FloorRarity = require(ReplicatedStorage.Shared.Config.FloorRarity)
local Server = ServerScriptService.Server
local Log = require(Server.Util.Log)
local Notify = require(Server.Util.Notify)

local AnnounceService = {}

AnnounceService.Audience = nil :: (() -> { any })?
AnnounceService.Publish = nil :: ((payload: { [string]: any }) -> ())?

local CFG = FloorRarity.Announce
local NAME_MAX = 40 -- длиннее имён Roblox не бывает: защита от мусора в чужом сообщении
local lastPublish, lastShow = -math.huge, -math.huge

-- Текст объявления.
function AnnounceService.Text(name: string, key: string): string
	return ("%s выбил %s этаж!"):format(name, FloorRarity.Names[key])
end

local function everyone(): { any }
	local hook = AnnounceService.Audience
	return if hook then hook() else Players:GetPlayers()
end

local function show(name: string, key: string)
	local text = AnnounceService.Text(name, key)
	for _, player in everyone() do
		Notify.Send(player, text, "Go")
	end
end

-- Игрок player выбил этаж редкости key: объявление по правилу его редкости (у частых редкостей объявления нет).
function AnnounceService.FloorWon(player: any, key: string)
	local signal = FloorRarity.Signal[key]
	local scope = signal and signal.announce
	if not scope then
		return
	end
	local name = player.DisplayName or player.Name
	show(name, key)
	if scope ~= "Global" then
		return
	end
	local now = os.clock()
	if now - lastPublish < CFG.PublishGap then
		return -- слишком часто: на другие серверы не уходит
	end
	lastPublish = now
	local payload = { name = name, rarity = key, job = game.JobId }
	local hook = AnnounceService.Publish
	if hook then
		hook(payload)
		return
	end
	task.spawn(function()
		local ok, err = pcall(MessagingService.PublishAsync, MessagingService, CFG.Topic, payload)
		if not ok then
			Log.Debug(
				"AnnounceService",
				"объявление на другие серверы не ушло: " .. tostring(err)
			)
		end
	end)
end

-- Объявление с другого сервера: проверка содержимого и частоты. Возвращает, показано ли оно.
function AnnounceService.Receive(data: any): boolean
	if type(data) ~= "table" or type(data.name) ~= "string" or type(data.rarity) ~= "string" then
		return false
	end
	local signal = FloorRarity.Signal[data.rarity]
	if not signal or signal.announce ~= "Global" or #data.name == 0 or #data.name > NAME_MAX then
		return false
	end
	if data.job == game.JobId and game.JobId ~= "" then
		return false -- своё объявление этот сервер уже показал
	end
	local now = os.clock()
	if now - lastShow < CFG.ShowGap then
		return false
	end
	lastShow = now
	show(data.name, data.rarity)
	return true
end

-- Сброс счётчиков частоты (тесты).
function AnnounceService.Reset()
	lastPublish, lastShow = -math.huge, -math.huge
end

function AnnounceService.Init()
	task.spawn(function()
		local ok, err = pcall(function()
			MessagingService:SubscribeAsync(CFG.Topic, function(message)
				AnnounceService.Receive(message.Data)
			end)
		end)
		if not ok then
			Log.Debug(
				"AnnounceService",
				"подписка на объявления не удалась: " .. tostring(err)
			)
		end
	end)
end

return AnnounceService

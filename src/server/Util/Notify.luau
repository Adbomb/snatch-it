-- Короткие сообщения игроку («Это чужой музей», «Руки заняты»).
-- Отправляет текст через RemoteEvent Notify. Зависит от Shared/Remotes.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = require(ReplicatedStorage.Shared.Remotes)

local Notify = {}

function Notify.Send(player: Player, text: string)
	Remotes.Get(Remotes.Names.Notify):FireClient(player, text)
end

return Notify

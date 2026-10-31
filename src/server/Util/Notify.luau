-- Короткие сообщения игроку («Это чужой музей», «Руки заняты»).
-- Отправляет текст и вид уведомления через RemoteEvent Notify. Зависит от Shared/Remotes.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = require(ReplicatedStorage.Shared.Remotes)

local Notify = {}

-- kind — цвет уведомления на клиенте: "Info" (по умолчанию), "Stop" (отказ), "Go" (успех).
function Notify.Send(player: Player, text: string, kind: string?)
	Remotes.FireClient(Remotes.Names.Notify, player, text, kind or "Info")
end

return Notify

-- Анимация автоудара бойца (подготовка, 2026-11-15): на каждый удар, засчитанный сервером (атрибуты игрока
-- BattleSwingSeq и BattleSwingAt пишет BattleService), играет Battle.Player.Swing.Animation приоритетом Action —
-- только в бою с боссами из Swing.Zones (сейчас — Король-дракон). Анимации пока нет (Animation не задана, Asset ID не
-- выдумываем) — ничего не играется и ничего не имитируется. Ходьба, бег, повороты и камера не трогаются: Humanoid не
-- останавливается, персонаж не закрепляется; анимация должна двигать только руки и корпус (ноги остаются за ходьбой).
-- Зависит от Config/Battle.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Battle = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("Battle"))

local PlayerSwingController = {}

local track: AnimationTrack? = nil
local trackOf: Animator? = nil

local function swing()
	local cfg = Battle.Player.Swing
	local id = cfg.Animation
	local player = Players.LocalPlayer
	local zone = player:GetAttribute("InBattle")
	if not id or type(zone) ~= "number" or not cfg.Zones[zone] then
		return
	end
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	local animator = humanoid and humanoid:FindFirstChildOfClass("Animator")
	if not animator then
		return
	end
	if trackOf ~= animator then
		local animation = Instance.new("Animation")
		animation.AnimationId = id
		track = animator:LoadAnimation(animation)
		trackOf = animator
		if track then
			track.Priority = Enum.AnimationPriority.Action
			track.Looped = false
		end
	end
	if track then
		track:Play(0.05)
	end
end

function PlayerSwingController.Init()
	Players.LocalPlayer:GetAttributeChangedSignal("BattleSwingSeq"):Connect(swing)
end

return PlayerSwingController

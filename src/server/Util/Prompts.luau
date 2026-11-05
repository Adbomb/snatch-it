-- Подсказки музея (ProximityPrompt) с атрибутом Action и тегом MuseumPrompt.
-- Клиент по тегу и Action решает, какие показать; сервер в каждом Triggered сам проверяет всё заново.
-- Клавиши: E — основное действие, R — «Повернуть», F — «В инвентарь». BindHold — удержание (кража, взлом).
-- Зависит от CollectionService, Config/GameConfig.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)

local Prompts = {}

Prompts.Tag = "MuseumPrompt"

type ActionSpec = { text: string, key: Enum.KeyCode, gamepadKey: Enum.KeyCode, offset: Vector2, hold: number? }

-- Подсказки на одной витрине разнесены по вертикали (UIOffset, px), чтобы не перекрывать друг друга.
Prompts.Actions = {
	Display = { text = "Выставить", key = Enum.KeyCode.E, gamepadKey = Enum.KeyCode.ButtonX, offset = Vector2.zero },
	FromStorage = {
		text = "Выставить из инвентаря",
		key = Enum.KeyCode.E,
		gamepadKey = Enum.KeyCode.ButtonX,
		offset = Vector2.zero,
	},
	Move = { text = "Переставить", key = Enum.KeyCode.E, gamepadKey = Enum.KeyCode.ButtonX, offset = Vector2.zero },
	Here = { text = "Сюда", key = Enum.KeyCode.E, gamepadKey = Enum.KeyCode.ButtonX, offset = Vector2.zero },
	Rotate = {
		text = "Повернуть",
		key = Enum.KeyCode.R,
		gamepadKey = Enum.KeyCode.ButtonY,
		offset = Vector2.new(0, 80),
	},
	Store = {
		text = "В инвентарь",
		key = Enum.KeyCode.F,
		gamepadKey = Enum.KeyCode.ButtonB,
		offset = Vector2.new(0, 160),
	},
	Upgrade = {
		text = "Улучшить гантель",
		key = Enum.KeyCode.E,
		gamepadKey = Enum.KeyCode.ButtonX,
		offset = Vector2.zero,
	},
	ChestStore = {
		text = "В инвентарь",
		key = Enum.KeyCode.E,
		gamepadKey = Enum.KeyCode.ButtonX,
		offset = Vector2.zero,
	},
	-- Судная ночь (D46): удержание (GameConfig.Theft.HoldSeconds ставит TheftService); на телефоне — экранная кнопка
	-- подсказки с тем же удержанием.
	-- Взлом усиленной двери (D37): удержание GameConfig.Defense.HackSeconds ставит DefenseService.
	Hack = {
		text = "Взломать",
		key = Enum.KeyCode.E,
		gamepadKey = Enum.KeyCode.ButtonX,
		offset = Vector2.zero,
	},
	Steal = {
		text = "Украсть",
		key = Enum.KeyCode.E,
		gamepadKey = Enum.KeyCode.ButtonX,
		offset = Vector2.zero,
	},
} :: { [string]: ActionSpec }

function Prompts.Create(parent: BasePart, action: string, objectText: string, distance: number): ProximityPrompt
	local spec = Prompts.Actions[action]
	assert(spec, "Неизвестное действие подсказки: " .. tostring(action))
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = action .. "Prompt"
	prompt.ActionText = spec.text
	prompt.ObjectText = objectText
	prompt.KeyboardKeyCode = spec.key
	prompt.GamepadKeyCode = spec.gamepadKey
	prompt.UIOffset = spec.offset
	prompt.HoldDuration = spec.hold or 0
	prompt.MaxActivationDistance = distance
	prompt.RequiresLineOfSight = false
	prompt:SetAttribute("Action", action)
	prompt.Parent = parent
	CollectionService:AddTag(prompt, Prompts.Tag)
	return prompt
end

-- Удержание: начало, отмена (отпустил или ушёл) и завершение. Roblox на сервере шлёт PromptButtonHoldEnded раньше
-- Triggered в том же кадре (проверено тремя клиентами 2026-11-05): немедленная отмена срывала каждую кражу и взлом.
-- Поэтому отмена ждёт GameConfig.HoldRelease.ReleaseGrace: пришёл Triggered — это завершение, отмены нет. Конец
-- удержания сразу после Triggered (обратный порядок) — тоже не отмена.
function Prompts.BindHold(
	prompt: ProximityPrompt,
	onBegin: (Player) -> (),
	onCancel: (Player) -> (),
	onComplete: (Player) -> ()
)
	local DONE = 0 -- только что завершено
	local pending: { [Player]: number } = {} -- номер отпускания, которое ждёт отмены, или DONE
	local count = 0
	local grace = GameConfig.HoldRelease.ReleaseGrace
	prompt.PromptButtonHoldBegan:Connect(function(player)
		pending[player] = nil
		onBegin(player)
	end)
	prompt.PromptButtonHoldEnded:Connect(function(player)
		if pending[player] == DONE then
			pending[player] = nil
			return
		end
		count += 1
		local token = count
		pending[player] = token
		task.delay(grace, function()
			if pending[player] == token then
				pending[player] = nil
				onCancel(player)
			end
		end)
	end)
	prompt.Triggered:Connect(function(player)
		pending[player] = DONE
		onComplete(player)
		task.delay(grace, function()
			if pending[player] == DONE then
				pending[player] = nil
			end
		end)
	end)
end

return Prompts

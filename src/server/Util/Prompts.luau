-- Подсказки музея (ProximityPrompt) с атрибутом Action и тегом MuseumPrompt.
-- Клиент по тегу и Action решает, какие показать; сервер в каждом Triggered сам проверяет всё заново.
-- Клавиши: E — основное действие, R — «Повернуть», F — «В хранилище». Зависит от CollectionService.

local CollectionService = game:GetService("CollectionService")

local Prompts = {}

Prompts.Tag = "MuseumPrompt"

type ActionSpec = { text: string, key: Enum.KeyCode, gamepadKey: Enum.KeyCode, offset: Vector2 }

-- Подсказки на одной витрине разнесены по вертикали (UIOffset, px), чтобы не перекрывать друг друга.
Prompts.Actions = {
	Display = { text = "Выставить", key = Enum.KeyCode.E, gamepadKey = Enum.KeyCode.ButtonX, offset = Vector2.zero },
	FromStorage = {
		text = "Выставить из хранилища",
		key = Enum.KeyCode.E,
		gamepadKey = Enum.KeyCode.ButtonX,
		offset = Vector2.zero,
	},
	Store = {
		text = "В хранилище",
		key = Enum.KeyCode.F,
		gamepadKey = Enum.KeyCode.ButtonB,
		offset = Vector2.new(0, 160),
	},
	ChestStore = {
		text = "В хранилище",
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
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = distance
	prompt.RequiresLineOfSight = false
	prompt:SetAttribute("Action", action)
	prompt.Parent = parent
	CollectionService:AddTag(prompt, Prompts.Tag)
	return prompt
end

return Prompts

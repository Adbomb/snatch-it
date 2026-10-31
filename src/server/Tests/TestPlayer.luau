-- Тестовый игрок для серверных тестов (только Studio): таблица с полями и методами Player, которые нужны
-- сервисам (UserId < 0, Name, DisplayName, Parent, Character, атрибуты, Kick), и настоящий персонаж-манекен
-- в workspace (HumanoidRootPart + Humanoid), чтобы работали проверки расстояния. События клиенту
-- (Remotes.FireClient) складываются в журнал Sent. Это не замена настоящему клиенту: подсказки, интерфейс, сеть
-- и физику персонажа он не проверяет. Ни от чего не зависит.

local Players = game:GetService("Players")

local FOLDER_NAME = "__TestCharacters"

local TestPlayer = {}
TestPlayer.__index = TestPlayer

export type TestPlayer = typeof(setmetatable(
	{} :: {
		IsTestPlayer: boolean,
		UserId: number,
		Name: string,
		DisplayName: string,
		Parent: Instance?,
		Character: Model,
		Sent: { { name: string, args: { [number]: any, n: number } } },
		attributes: { [string]: any },
		kicked: string?,
	},
	TestPlayer
))

local counter = 0

local function folder(): Folder
	local existing = workspace:FindFirstChild(FOLDER_NAME)
	if existing then
		return existing :: Folder
	end
	local created = Instance.new("Folder")
	created.Name = FOLDER_NAME
	created.Archivable = false
	created.Parent = workspace
	return created
end

-- Новый тестовый игрок с персонажем в точке position (по умолчанию — высоко над картой, вдали от всего).
function TestPlayer.new(name: string, position: Vector3?): TestPlayer
	counter += 1
	local model = Instance.new("Model")
	model.Name = "TestCharacter_" .. name
	local root = Instance.new("Part")
	root.Name = "HumanoidRootPart"
	root.Size = Vector3.new(2, 2, 1)
	root.Anchored = true
	root.CanCollide = false
	root.CanQuery = false
	root.Transparency = 0.5
	root.CFrame = CFrame.new(position or Vector3.new(0, 500, -2000 - counter * 10))
	root.Parent = model
	local humanoid = Instance.new("Humanoid")
	humanoid.RequiresNeck = false -- у манекена нет головы и шеи: без этого Humanoid считал бы его погибшим
	humanoid.Parent = model
	model.PrimaryPart = root
	model.Parent = folder()
	local self = {
		IsTestPlayer = true,
		UserId = -1000 - counter,
		Name = name,
		DisplayName = name,
		Parent = Players,
		Character = model,
		Sent = {},
		attributes = {},
		kicked = nil,
	}
	return setmetatable(self, TestPlayer)
end

function TestPlayer.GetAttribute(self: TestPlayer, key: string): any
	return self.attributes[key]
end

function TestPlayer.SetAttribute(self: TestPlayer, key: string, value: any)
	self.attributes[key] = value
end

function TestPlayer.Kick(self: TestPlayer, message: string?)
	self.kicked = message or ""
	self.Parent = nil
end

-- Ставит персонажа в точку (мгновенно, без физики).
function TestPlayer.MoveTo(self: TestPlayer, position: Vector3)
	(self.Character.PrimaryPart :: BasePart).CFrame = CFrame.new(position)
end

-- Тексты уведомлений Notify, полученные с начала теста (или после ClearSent).
function TestPlayer.Notices(self: TestPlayer): { string }
	local texts = {}
	for _, event in self.Sent do
		if event.name == "Notify" then
			table.insert(texts, event.args[1])
		end
	end
	return texts
end

-- Было ли уведомление, содержащее text.
function TestPlayer.WasNotified(self: TestPlayer, text: string): boolean
	for _, notice in self:Notices() do
		if string.find(notice, text, 1, true) then
			return true
		end
	end
	return false
end

function TestPlayer.ClearSent(self: TestPlayer)
	table.clear(self.Sent)
end

-- Игрок «вышел»: персонаж убран.
function TestPlayer.Destroy(self: TestPlayer)
	self.Parent = nil
	self.Character:Destroy()
end

return TestPlayer

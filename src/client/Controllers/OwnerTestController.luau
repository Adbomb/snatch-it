-- Кнопка «Тест» владельца в HUD (тестовый режим владельца, решение владельца 2026-11-16; кнопка — 2026-11-17: на
-- телефоне чат неудобен или недоступен). Кнопка есть только у того, кому сервер поставил атрибут игрока OwnerTest
-- ("Normal" — обычный сервер DEV-места, "Test" — тестовый сервер); у остальных игроков и в обычной игре её нет.
-- По нажатию — маленькая панель действий правее столбика меню: на обычном сервере — «На тестовый сервер», на
-- тестовом — «К дракону», «Бой», «Победа», «День», «Ночь», «Выход». Клиент только просит (RemoteEvent OwnerTest,
-- имя действия): владельца, вид сервера и паузу между действиями проверяет сервер (Services/OwnerTestService).
-- Зависит от Shared/Remotes, Shared/StudUI, Config/GameConfig, Config/UITokens, UI/MenuHud, UI/HudLayout.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local Remotes = require(Shared:WaitForChild("Remotes"))
local UITokens = require(Shared:WaitForChild("Config"):WaitForChild("UITokens"))
local UI = require(Shared:WaitForChild("StudUI"):WaitForChild("StudUI"))
local Motion = require(Shared:WaitForChild("StudUI"):WaitForChild("StudMotion"))
local Client = script.Parent.Parent
local HudLayout = require(Client:WaitForChild("UI"):WaitForChild("HudLayout"))
local MenuHud = require(Client:WaitForChild("UI"):WaitForChild("MenuHud"))

local T = UITokens.OwnerTest
local player = Players.LocalPlayer

local OwnerTestController = {}

local menuButton: GuiButton? = nil
local panel: Frame? = nil
local builtFor: string? = nil
local lastClick = -math.huge

-- Собрать панель действий для сервера вида kind (старая — убирается).
local function build(kind: string)
	if panel then
		panel:Destroy()
		panel = nil
	end
	builtFor = kind
	local actions = T.Actions[kind]
	if not actions then
		return
	end
	local gui = player:WaitForChild("PlayerGui"):FindFirstChild("OwnerTestHud")
	if not gui then
		gui = UI.ScreenGui("OwnerTestHud", 6, { Menu = false })
		gui.Parent = player.PlayerGui
	end
	local columns = math.min(T.Columns, #actions)
	local rows = math.ceil(#actions / columns)
	local frame = Instance.new("Frame")
	frame.Name = "Panneau"
	frame.BackgroundTransparency = 1
	frame.AnchorPoint = Vector2.new(0, 0.5)
	frame.Size = UDim2.fromOffset(
		columns * T.Button.X + (columns - 1) * T.Gap + 2 * T.Pad,
		rows * T.Button.Y + (rows - 1) * T.Gap + 2 * T.Pad
	)
	frame.Visible = false
	frame.Parent = gui
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = frame
	UI.InsetBox(frame, { Size = UDim2.fromScale(1, 1), Transparency = 0.2 })
	for i, action in actions do
		local column, row = (i - 1) % columns, (i - 1) // columns
		local button = UI.Button(frame, {
			Name = action.id,
			Theme = action.theme,
			Size = T.Button,
			AnchorPoint = Vector2.zero,
			Position = UDim2.fromOffset(T.Pad + column * (T.Button.X + T.Gap), T.Pad + row * (T.Button.Y + T.Gap)),
			Text = action.text,
			TextSize = T.Text, -- длинная подпись («На тестовый сервер») сжимается под кнопку
			ZIndex = 5,
		})
		Motion.BindButton(button, 1.04, nil, function()
			-- та же пауза, что на сервере: лишние нажатия не уходят
			local now = os.clock()
			if now - lastClick < GameConfig.OwnerTest.CommandCooldown then
				return
			end
			lastClick = now
			Remotes.Get(Remotes.Names.OwnerTest):FireServer(action.id)
		end)
	end
	HudLayout.Track(function()
		if frame.Parent then
			local s = HudLayout.Scale()
			scale.Scale = s
			local menu = UITokens.MenuHud
			frame.Position = UDim2.new(0, menu.Margin + menu.Button.X * s + T.Left, 0.5, 0)
		end
	end)
	panel = frame
end

local function toggle()
	if panel then
		panel.Visible = not panel.Visible
	end
end

-- Атрибут OwnerTest появился, сменился или пропал: кнопка и панель — только пока он есть.
local function refresh()
	local kind = player:GetAttribute("OwnerTest")
	local known = type(kind) == "string" and T.Actions[kind] ~= nil
	if known and not menuButton then
		menuButton = MenuHud.Add("OwnerTest", "Тест", "teal", 9, toggle)
	end
	if menuButton and menuButton.Parent then
		(menuButton.Parent :: GuiObject).Visible = known
	end
	if known and builtFor ~= kind then
		build(kind :: string)
	elseif not known and panel then
		panel.Visible = false
	end
end

function OwnerTestController.Init()
	player:GetAttributeChangedSignal("OwnerTest"):Connect(refresh)
	refresh()
end

return OwnerTestController

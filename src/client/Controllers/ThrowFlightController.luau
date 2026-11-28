-- Чужие полёты при броске вдаль (D75): лёгкий показ у всех, кроме бросавшего, — Ловибум, белый след и ник над ним;
-- без камеры, частиц и света. Событие ThrowFlight приходит от сервера всем: старт — у края обрыва, где стоит
-- бросавший (его замах идёт Show.Windup × ThrowPose.Release секунд — на столько полёт отложен), путь и время — те же,
-- что у своего полёта (World/ThrowPath). Все полёты ведёт один шаг кадра; после приземления Ловибум недолго лежит и
-- исчезает. Свой полёт показывает Controllers/ThrowController.
-- Зависит от LovibumModel, ThrowPath, ThrowPose, Config/GameConfig, Config/LovibumRigs, Remotes.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local LovibumRigs = require(Config:WaitForChild("LovibumRigs"))
local Remotes = require(Shared:WaitForChild("Remotes"))

local Client = script.Parent.Parent
local LovibumModel = require(Client:WaitForChild("World"):WaitForChild("LovibumModel"))
local ThrowPath = require(Client:WaitForChild("World"):WaitForChild("ThrowPath"))
local ThrowPose = require(Client:WaitForChild("World"):WaitForChild("ThrowPose"))

local Show = GameConfig.Throw.Show
local player = Players.LocalPlayer

local ThrowFlightController = {}

local MAX = 12 -- полётов одновременно (как шкал на сервере)
local REST = 1.4 -- секунд Ловибум лежит после приземления
local NICK = Vector2.new(140, 30) -- плашка ника, пикселей

type Flight = {
	model: Model,
	carrier: BasePart,
	kind: string,
	from: Vector3,
	to: Vector3,
	t: number,
	duration: number,
}

local flights: { Flight } = {}
local folder: Folder? = nil

local function holder(): Folder
	if not folder or not folder.Parent then
		local f = Instance.new("Folder")
		f.Name = "ThrowFlights"
		f.Parent = workspace
		folder = f
	end
	return folder :: Folder
end

local function begin(payload: any)
	if #flights >= MAX or not LovibumRigs.Types[payload.kind] then
		return
	end
	local thrower = Players:GetPlayerByUserId(payload.user)
	local character = thrower and thrower.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local edge = ThrowPath.Edge()
	local from = if root and root:IsA("BasePart")
		then root.Position + Vector3.new(0.9, 1.6, -1.2)
		else Vector3.new(0, (if edge then edge.top else 0) + 4, if edge then edge.z0 else 2)
	local floor = ThrowPath.Landing(payload.zone, payload.depth or 0.5, from.X)
	if not floor then
		return
	end
	local half = LovibumRigs.Types[payload.kind].Size.Y * Show.LovibumScale / 2
	local model = LovibumModel.Build(payload.kind)
	model.Parent = holder()
	-- след и ник — на невидимой детали, которая идёт за Ловибумом
	local carrier = Instance.new("Part")
	carrier.Name = "Carrier"
	carrier.Transparency = 1
	carrier.Size = Vector3.new(0.5, 0.5, 0.5)
	carrier.Anchored = true
	carrier.CanCollide = false
	carrier.CanQuery = false
	carrier.CanTouch = false
	carrier.CastShadow = false
	carrier.CFrame = CFrame.new(from)
	carrier.Parent = model
	local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
	a0.Position, a1.Position = Vector3.new(0, 0.6, 0), Vector3.new(0, -0.6, 0)
	a0.Parent, a1.Parent = carrier, carrier
	local trail = Instance.new("Trail")
	trail.Attachment0, trail.Attachment1 = a0, a1
	trail.Lifetime = 0.4
	trail.LightEmission = 1
	trail.Color = ColorSequence.new(Color3.new(1, 1, 1))
	trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) })
	trail.Parent = carrier
	local board = Instance.new("BillboardGui")
	board.Name = "Nick"
	board.Size = UDim2.fromOffset(NICK.X, NICK.Y)
	board.StudsOffset = Vector3.new(0, 2.6, 0)
	board.MaxDistance = 400
	board.Parent = carrier
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Size = UDim2.fromScale(1, 1)
	label.FontFace = Font.fromEnum(Enum.Font.LuckiestGuy)
	label.TextScaled = true
	label.TextColor3 = Color3.new(1, 1, 1)
	label.Text = tostring(payload.name or "")
	label.Parent = board
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 2
	stroke.Parent = label
	table.insert(flights, {
		model = model,
		carrier = carrier,
		kind = payload.kind,
		from = from,
		to = floor + Vector3.new(0, half, 0),
		t = -Show.Windup * ThrowPose.Release, -- пока идёт замах бросавшего
		duration = ThrowPath.Duration(from, floor),
	})
end

local function step(dt: number)
	for i = #flights, 1, -1 do
		local f = flights[i]
		f.t += dt
		if f.t >= f.duration + REST then
			f.model:Destroy()
			table.remove(flights, i)
		elseif f.t >= 0 then
			local u = math.clamp(f.t / f.duration, 0, 1)
			local at = ThrowPath.At(f.from, f.to, u)
			local half = LovibumRigs.Types[f.kind].Size.Y * Show.LovibumScale / 2
			local turn = if u < 1 then CFrame.Angles(f.t * 8.5, f.t * 2.1, 0) else CFrame.identity
			LovibumModel.Place(f.model, CFrame.new(at) * turn * CFrame.new(0, -half, 0), 0, Show.LovibumScale)
			f.carrier.CFrame = CFrame.new(at)
		end
	end
end

function ThrowFlightController.Init()
	Remotes.Get(Remotes.Names.ThrowFlight).OnClientEvent:Connect(function(payload)
		if type(payload) == "table" and payload.user ~= player.UserId and type(payload.zone) == "number" then
			begin(payload)
		end
	end)
	RunService.RenderStepped:Connect(step)
end

return ThrowFlightController

-- Замеры музея-небоскрёба на клиенте (этапы B–C): вставить в MCP execute_luau (Client, Play). Ждёт, пока очередь
-- сборки убранства опустеет (не дольше WAIT с), потом считает детали мира и убранства башен по уровням детализации
-- (атрибуты папки workspace.TowerDecor от TowerController), копии экспонатов, память, кадры в секунду и худший кадр за
-- SECONDS (Studio должна быть на переднем плане — в фоне она рисует ~15 кадров/с; 60 — потолок Studio, запас сверх
-- него не виден), время сборки интерьера. Серверная часть — команда DevTools «TowerStats». Это ПК в Studio; телефон
-- так не измеряется. Ни от чего не зависит.
local SECONDS = 5
local WAIT = 20

local Stats = game:GetService("Stats")
local RunService = game:GetService("RunService")
local folder = workspace:FindFirstChild("TowerDecor")
local a = function(name)
	return folder and folder:GetAttribute(name) or 0
end
local t0 = os.clock()
task.wait(1.2) -- счётчики обновляются раз в секунду
while a("Queue") > 0 and os.clock() - t0 < WAIT do
	task.wait(0.25)
end
local settle = os.clock() - t0
local all, decor = 0, 0
for _, d in workspace:GetDescendants() do
	if d:IsA("BasePart") then
		all += 1
		if folder and d:IsDescendantOf(folder) then
			decor += 1
		end
	end
end
local frames, worst, t1 = 0, 0, os.clock()
local conn = RunService.RenderStepped:Connect(function(dt)
	frames += 1
	worst = math.max(worst, dt)
end)
task.wait(SECONDS)
conn:Disconnect()
return string.format(
	"клиент: деталей %d (убранство башен %d: интерьер %d, фасады %d, силуэты %d; экспонатов %d; видов %d, очередь %d, "
		.. "собрано %d, ждал %.1f с); InstanceCount %d; память %.0f МБ; кадров/с %.1f; худший кадр %.1f мс; "
		.. "интерьер: последний %.1f мс, худший %.1f мс; экран %s",
	all,
	decor,
	a("PartsInterior"),
	a("PartsFacade"),
	a("PartsSilhouette"),
	a("Exhibits"),
	a("Views"),
	a("Queue"),
	a("Builds"),
	settle,
	Stats.InstanceCount,
	Stats:GetTotalMemoryUsageMb(),
	frames / (os.clock() - t1),
	worst * 1000,
	a("LastInteriorMs"),
	a("MaxInteriorMs"),
	tostring(workspace.CurrentCamera.ViewportSize)
)

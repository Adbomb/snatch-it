-- Инструменты проверки только в Studio (GameConfig.DevMode): папка ServerStorage.DevTools с BindableFunction,
-- которые вызывает MCP (require из MCP даёт отдельную копию модулей без данных игроков, BUGS.md).
-- В опубликованной игре не создаётся. Зависит от DataService, GymService, GameConfig.
--   Info(userId) → { coins, strength, dumbbellLevel, museumLevel }
--   GiveCoins(userId, amount) → новые монеты (пока нет экономики шага 7)
--   RunServerTests(filter?) → отчёт серверных тестов на двух тестовых игроков (Server/Tests/ServerTests); filter —
--   часть имени теста. Из MCP — атрибутом RunTests ("" — все), отчёт — атрибут TestReport
--   TimeScale(scale) / TimeSkip(phase, secondsBefore) / TimeReset() → ускорение и переход к фазе (D37)
--   Battle(userId, slot) → бой настоящим персонажем с псом за предмет слота (показ анимаций)
--   BossState(state) → состояние пса для показа анимаций
--   Showroom(boss?, origin?) → все предметы коллекции босса в ряд (папка __Showroom, только показ)

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local DataService = require(ServerScriptService.Server.Services.DataService)
local GymService = require(ServerScriptService.Server.Services.GymService)

local DevTools = {}

local function bind(folder: Folder, name: string, handler: (Player, ...any) -> any)
	local fn = Instance.new("BindableFunction")
	fn.Name = name
	fn.OnInvoke = function(userId: number, ...)
		local player = Players:GetPlayerByUserId(userId)
		if not player then
			return nil
		end
		return handler(player, ...)
	end
	fn.Parent = folder
end

function DevTools.Init()
	if not (RunService:IsStudio() and GameConfig.DevMode) then
		return
	end
	local folder = Instance.new("Folder")
	folder.Name = "DevTools"
	bind(folder, "Info", function(player)
		local data = DataService.GetData(player)
		return data
			and {
				coins = data.coins,
				strength = data.strength,
				dumbbellLevel = data.dumbbellLevel,
				museumLevel = data.museumLevel,
				museumPower = GymService.MuseumPower(player),
			}
	end)
	bind(folder, "GiveCoins", function(player, amount: number)
		local coins = DataService.AddCoins(player, amount)
		GymService.SyncAttributes(player)
		return coins
	end)
	-- Бой настоящим персонажем для показа анимаций (тот же BattleService.Begin, что у подсказки «Забрать»). bossHp и
	-- bossDamage — только на этот бой (сильный игрок иначе побеждает с одного удара), потом числа возвращаются.
	bind(folder, "Battle", function(player, slot: number, bossHp: number?, bossDamage: number?)
		local Battle = require(ReplicatedStorage.Shared.Config.Battle)
		local BossLootService = require(ServerScriptService.Server.Services.BossLootService)
		local BattleService = require(ServerScriptService.Server.Services.BattleService)
		local _, part = BossLootService.SlotItem(1, slot)
		local character = player.Character
		if not part or not character then
			return "слот пуст или нет персонажа"
		end
		character:PivotTo(CFrame.new(part.Position + Vector3.new(0, 1, 5)))
		task.wait(0.3)
		local cfg = Battle.Bosses[1]
		local savedHp, savedDamage = cfg.HP, cfg.Damage
		cfg.HP, cfg.Damage = bossHp or savedHp, bossDamage or savedDamage
		local started = BattleService.Begin(player, 1, slot) ~= nil
		cfg.HP, cfg.Damage = savedHp, savedDamage
		return started
	end)
	-- Состояние пса для показа анимаций (Sleep, Wake, StandUp, ToCombat, Combat, Victory, Defeat, Return, FallAsleep).
	local bossState = Instance.new("BindableFunction")
	bossState.Name = "BossState"
	bossState.OnInvoke = function(state: string)
		local BossService = require(ServerScriptService.Server.Services.BossService)
		local boss = BossService.Get(1)
		if boss then
			BossService.SetState(boss, state)
		end
		return boss ~= nil
	end
	bossState.Parent = folder
	-- Выставка всех предметов коллекции босса в ряд на поле Safe Zone (только показ, без реестра и подсказок).
	local showroom = Instance.new("BindableFunction")
	showroom.Name = "Showroom"
	showroom.OnInvoke = function(boss: number?, origin: Vector3?): number
		local Items = require(ReplicatedStorage.Shared.Config.Items)
		local Rarities = require(ReplicatedStorage.Shared.Config.Rarities)
		local ItemFactory = require(ServerScriptService.Server.Util.ItemFactory)
		local old = workspace:FindFirstChild("__Showroom")
		if old then
			old:Destroy()
		end
		local hall = Instance.new("Folder")
		hall.Name = "__Showroom"
		hall.Archivable = false
		local ids = {}
		for id, def in Items do
			if def.boss == (boss or 1) and not def.legacy then
				table.insert(ids, id)
			end
		end
		table.sort(ids, function(a, b)
			local ra, rb = Rarities.Rank(Items[a].rarity), Rarities.Rank(Items[b].rarity)
			return if ra == rb then a < b else ra < rb
		end)
		local start = origin or Vector3.new(-60, 0.1, 70)
		for i, id in ids do
			local part = ItemFactory.Create(id)
			local row, col = (i - 1) // 10, (i - 1) % 10
			local x = start.X + col * 6
			local z = start.Z - row * 9
			part.CFrame = CFrame.new(x, start.Y + part.Size.Y / 2, z) -- лицом к −Z (к коридору уровней)
			part.Parent = hall
		end
		hall.Parent = workspace
		return #ids
	end
	showroom.Parent = folder
	local runTests = Instance.new("BindableFunction")
	runTests.Name = "RunServerTests"
	runTests.OnInvoke = function(filter: string?)
		return require(ServerScriptService.Server.Tests.ServerTests).Run(filter)
	end
	runTests.Parent = folder
	-- Запуск тестов атрибутом (MCP): folder.RunTests = "" (все) или часть имени. Тесты идут в потоке этого скрипта —
	-- Studio не даёт потоку MCP вызывать BindableFunction с правами игры (Capabilities: Network, 2026-11-05).
	-- Отчёт — атрибут TestReport («идёт» → текст отчёта).
	folder:GetAttributeChangedSignal("RunTests"):Connect(function()
		local filter = folder:GetAttribute("RunTests")
		if type(filter) ~= "string" then
			return
		end
		folder:SetAttribute("RunTests", nil)
		folder:SetAttribute("TestReport", "идёт")
		task.spawn(function()
			local ok, report = pcall(function()
				return require(ServerScriptService.Server.Tests.ServerTests).Run(if filter == "" then nil else filter)
			end)
			folder:SetAttribute("TestReport", if ok then report else "ошибка: " .. tostring(report))
		end)
	end)
	local TimeService = require(ServerScriptService.Server.Services.TimeService)
	for name, handler in {
		TimeScale = TimeService.SetScale,
		TimeSkip = TimeService.SkipTo,
		TimeReset = TimeService.ResetClock,
	} :: { [string]: (...any) -> any } do
		local fn = Instance.new("BindableFunction")
		fn.Name = name
		fn.OnInvoke = function(...)
			local state = handler(...)
			return state and ("%s, день %d"):format(state.phase, state.day) or nil
		end
		fn.Parent = folder
	end
	folder.Parent = ServerStorage
end

return DevTools

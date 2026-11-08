-- Инструменты проверки только в Studio (GameConfig.DevMode): папка ServerStorage.DevTools с BindableFunction,
-- которые вызывает MCP (require из MCP даёт отдельную копию модулей без данных игроков, BUGS.md).
-- В опубликованной игре не создаётся. Зависит от DataService, GymService, GameConfig.
--   Info(userId) → { coins, strength, dumbbellLevel, museumLevel }
--   GiveCoins(userId, amount) → новые монеты (пока нет экономики шага 7)
--   RunServerTests(filter?) → отчёт серверных тестов на двух тестовых игроков (Server/Tests/ServerTests); filter —
--   часть имени теста. Из MCP — атрибутом RunTests ("" — все), отчёт — атрибут TestReport
--   TimeScale(scale) / TimeSkip(phase, secondsBefore) / TimeReset() → ускорение и переход к фазе (D37); из MCP —
--   атрибутом Command («TimeSkip DoomNight 5», «GiveCoins <userId> <сумма>»…), ответ — атрибут CommandResult
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
	-- Команды атрибутом (MCP, проверка несколькими клиентами): folder.Command = "TimeSkip DoomNight 5" |
	-- "TimeScale 10" | "TimeReset" | "GiveCoins <userId> <сумма>" | "MuseumLevel <userId> <1..10>" |
	-- "GiveDefense <userId> <вид> <сколько>" | "Exhibit <userId> <место> [предмет]" |
	-- "InstallDefense <userId> <вид> <x,z | Entrance | Gallery>" | "Strength <userId> <сила>" (только Studio, D53) |
	-- D55: "Lovibums <userId> <уровень> <вид> <n>" | "Tutorial <userId> <шаг>" | "CatchRoll <0…1 | off>".
	-- Выполняются в потоке этого скрипта (как RunTests),
	-- ответ — атрибут CommandResult.
	folder:GetAttributeChangedSignal("Command"):Connect(function()
		local line = folder:GetAttribute("Command")
		if type(line) ~= "string" then
			return
		end
		folder:SetAttribute("Command", nil)
		local words = string.split(line, " ")
		local ok, result = pcall(function(): any
			local command = words[1]
			if command == "TimeSkip" then
				local state = TimeService.SkipTo(words[2] :: any, tonumber(words[3]))
				return state and ("%s, день %d"):format(state.phase, state.day)
			elseif command == "TimeScale" then
				TimeService.SetScale(tonumber(words[2]) or 1)
				return "ок"
			elseif command == "TimeReset" then
				TimeService.ResetClock()
				return "ок"
			elseif command == "GiveCoins" then
				local player = Players:GetPlayerByUserId(tonumber(words[2]) or 0)
				if not player then
					return "нет игрока"
				end
				local coins = DataService.AddCoins(player, tonumber(words[3]) or 0)
				GymService.SyncAttributes(player)
				return coins
			elseif command == "MuseumLevel" or command == "GiveDefense" then
				-- проверка защиты (D47) и музея D48-C: уровень музея — сколько устройств можно поставить и сколько мест
				-- открыто (здание и места перестраиваются); устройство в запас — в том числе капкан, у которого нет
				-- утверждённой цены. Только в Studio. Ниже занятых мест уровень не опускается.
				local player = Players:GetPlayerByUserId(tonumber(words[2]) or 0)
				local data = player and DataService.GetData(player)
				if not player or not data then
					return "нет игрока"
				end
				local DefenseService = require(ServerScriptService.Server.Services.DefenseService)
				if command == "MuseumLevel" then
					local level = math.clamp(math.floor(tonumber(words[3]) or 1), 1, 10)
					local open = GameConfig.Museum.SlotsByLevel[level]
					for _, record in data.items do
						if type(record) == "table" and record.place == "slot" and (record.slot or 0) > open then
							return ("на месте %d экспонат — уровень ниже не ставится"):format(record.slot)
						end
					end
					data.museumLevel = level
					local PlotService = require(ServerScriptService.Server.Services.PlotService)
					local InventoryService = require(ServerScriptService.Server.Services.InventoryService)
					local plot = PlotService.GetPlotOf(player)
					if plot then
						PlotService.ShowLevel(plot, level)
					end
					InventoryService.Sync(player)
				else
					local defense = DataService.Defense(player)
					local kind = words[3]
					defense.owned[kind] = (defense.owned[kind] or 0) + math.max(0, math.floor(tonumber(words[4]) or 1))
				end
				DefenseService.Sync(player)
				return "ок"
			elseif command == "Exhibit" then
				-- подготовка проверки краж (D48-C, ТЗ «D49 — финальное тестирование»): экспонат на место slot тем же
				-- путём, что в игре — предмет на карте у игрока → «Поднять» → «Выставить» (обработчики подсказок, все
				-- проверки сервера: владелец, открытое место, фаза дня, расстояние). Игрока переносит к постаменту.
				local player = Players:GetPlayerByUserId(tonumber(words[2]) or 0)
				local slot = tonumber(words[3])
				local Server = ServerScriptService.Server
				local PlotService = require(Server.Services.PlotService)
				local plot = player and PlotService.GetPlotOf(player)
				local showcase = plot and slot and plot.showcases[slot]
				local root = player and player.Character and player.Character:FindFirstChild("HumanoidRootPart")
				if not plot or not showcase or not root then
					return "нет игрока, участка или места"
				end
				local CarryService = require(Server.Services.CarryService)
				local ItemRegistry = require(Server.Services.ItemRegistry)
				local MuseumService = require(Server.Services.MuseumService)
				local ItemFactory = require(Server.Util.ItemFactory)
				local stand = showcase.CFrame * CFrame.new(0, 0, -5)
				root.CFrame = CFrame.lookAt(stand.Position, showcase.Position)
				local items = workspace:FindFirstChild("__DevItems") or Instance.new("Folder")
				items.Name = "__DevItems"
				items.Archivable = false
				items.Parent = workspace
				local itemId = words[4] or "Moai"
				local part = ItemFactory.Create(itemId)
				part.Anchored = true
				part.CFrame = root.CFrame * CFrame.new(0, 0, -2)
				part.Parent = items
				local uid = ItemRegistry.CreateOnMap(itemId, part)
				CarryService.RegisterMapItem(uid, part)
				CarryService.Handlers.Pickup(player, uid)
				MuseumService.Handlers.Display(player, plot, slot)
				local entry = ItemRegistry.Get(uid)
				return if entry and entry.state == "Displayed"
					then ("%s на месте %d"):format(itemId, slot)
					else "не выставлено: " .. tostring(entry and entry.state)
			elseif command == "InstallDefense" then
				-- подготовка проверки защиты: установка тем же обработчиком, что окно «Защита» (подготовка, лимит,
				-- зоны D48-C). Место — "x,z" в осях участка или имя места (Entrance, Gallery).
				local player = Players:GetPlayerByUserId(tonumber(words[2]) or 0)
				if not player then
					return "нет игрока"
				end
				local DefenseService = require(ServerScriptService.Server.Services.DefenseService)
				local kind = words[3]
				local x, z = string.match(words[4] or "", "^(%-?[%d%.]+),(%-?[%d%.]+)$")
				local spot: any = if x then Vector3.new(tonumber(x) :: number, 0, tonumber(z) :: number) else words[4]
				DefenseService.Handlers.Action(player, "Install", kind, spot)
				local installed = DefenseService.Handlers.Museum(player.UserId).installed[kind]
				return if installed then "установлено" else "отказ (см. уведомление игроку)"
			elseif command == "Strength" then
				-- проверка капкана и нокаута на трёх клиентах (D53): сила игрока — урон в PvP. Только в локальном
				-- Studio: в опубликованной игре DevTools не создаётся, и команда сама проверяет Studio ещё раз.
				if not RunService:IsStudio() then
					return "только в Studio"
				end
				local player = Players:GetPlayerByUserId(tonumber(words[2]) or 0)
				local data = player and DataService.GetData(player)
				if not player or not data then
					return "нет игрока"
				end
				local value = math.floor(tonumber(words[3]) or 0)
				data.strength = math.clamp(value, 0, GameConfig.Gym.MaxStrength)
				GymService.SyncAttributes(player)
				require(ServerScriptService.Server.Services.CarryService).RefreshSpeed(player) -- скорость — от силы
				return data.strength
			elseif command == "Lovibums" or command == "Tutorial" or command == "CatchRoll" then
				-- D55 (только Studio): «Lovibums <userId> <уровень> <вид> <сколько>» — Ловибумы в запас без покупки (цены не
				-- утверждены); «Tutorial <userId> <шаг>» — шаг обучения (Done — пройдено); «CatchRoll <0…1 | off>» —
				-- исход шанса захвата для проверки (0 — поймано, 0.999 — побег, off — случайно).
				if not RunService:IsStudio() then
					return "только в Studio"
				end
				local Server = ServerScriptService.Server
				if command == "CatchRoll" then
					local value = tonumber(words[2])
					require(Server.Services.CatchService).Handlers.SetRoll(value)
					return if value then ("шанс: %.3f"):format(value) else "случайно"
				end
				local player = Players:GetPlayerByUserId(tonumber(words[2]) or 0)
				local data = player and DataService.GetData(player)
				if not player or not data then
					return "нет игрока"
				end
				local ShopService = require(Server.Services.ShopService)
				if command == "Lovibums" then
					local CatchRules = require(ReplicatedStorage.Shared.CatchRules)
					local level, kind = tonumber(words[3]), words[4]
					local n = math.floor(tonumber(words[5]) or 1)
					if not CatchRules.IsLevel(level) or not CatchRules.IsKind(kind) or n < 1 then
						return "уровень 1–10, вид Boom | Turbo | Mega"
					end
					local lovibums = DataService.Lovibums(player) :: any
					local key = CatchRules.LevelKey(level :: number)
					lovibums[key] = lovibums[key] or {}
					lovibums[key][kind] = math.min((lovibums[key][kind] or 0) + n, GameConfig.Catch.MaxStock)
					ShopService.Sync(player)
					return lovibums[key][kind]
				end
				local TutorialRules = require(ReplicatedStorage.Shared.TutorialRules)
				local step = words[3]
				if not TutorialRules.IsStep(step) then
					return "шаги: " .. table.concat(TutorialRules.Steps, ", ")
				end
				data.tutorial = if step == "Done" then { step = "Done", migrated = true } else { step = step }
				ShopService.Sync(player)
				return step
			end
			return "неизвестная команда"
		end)
		folder:SetAttribute("CommandResult", (if ok then "" else "ошибка: ") .. tostring(result))
	end)
	folder.Parent = ServerStorage
end

return DevTools

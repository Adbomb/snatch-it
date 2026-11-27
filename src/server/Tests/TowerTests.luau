-- Серверные тесты музея-небоскрёба (этап B, docs/TOWER_PLAN.md v3 §4.5): тестовые игроки (Tests/TestPlayer, профили
-- в памяти — ProfileStore.Mock, в DataStore ничего не пишется) включают режим башни (TowerService.Enable) после
-- обычного входа. Постройка, повторы, отказы и защита построенного экземпляра, сохранение и повторный вход, миграция
-- v5 → v6, починка испорченного профиля, лифт, снятие и перестановка со сдвигом, несколько игроков на разных этажах,
-- гость, возврат обычного участка, откат постройки при отказе реестра, окно инвентаря. Это серверная симуляция:
-- клиентское убранство, интерфейс и физику настоящего персонажа она не проверяет (это — проверка в Play).
-- Подключается из ServerTests одной строкой: Register(test, helpers).
-- Зависит от TowerService, ElevatorService, DataService, ItemRegistry, IncomeService, InventoryService, PlayerSession,
-- PlotService, World/TowerBuilder, Shared/TowerRules, Tests/TestPlayer, Config.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local GameConfig = require(ReplicatedStorage.Shared.Config.GameConfig)
local Items = require(ReplicatedStorage.Shared.Config.Items)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local TowerRules = require(ReplicatedStorage.Shared.TowerRules)
local Server = ServerScriptService.Server
local DataService = require(Server.Services.DataService)
local ElevatorService = require(Server.Services.ElevatorService)
local IncomeService = require(Server.Services.IncomeService)
local InventoryService = require(Server.Services.InventoryService)
local ItemRegistry = require(Server.Services.ItemRegistry)
local PlotService = require(Server.Services.PlotService)
local TowerService = require(Server.Services.TowerService)
local TowerBuilder = require(Server.World.TowerBuilder)
local TestPlayer = require(Server.Tests.TestPlayer)

local cfg = GameConfig.Tower

local TowerTests = {}

-- предметы с доходом по боссам (детерминированно) и предметы без этажа
local BUILDABLE: { string } = {}
local LEGACY: string? = nil
local DRAFT: string? = nil
for id, def in Items do
	if TowerRules.Buildable(def) then
		table.insert(BUILDABLE, id)
	elseif def.legacy and not LEGACY then
		LEGACY = id
	elseif not def.legacy and (def.income or 0) == 0 and not DRAFT then
		DRAFT = id
	end
end
table.sort(BUILDABLE, function(a, b)
	local da, db = Items[a], Items[b]
	return if da.boss == db.boss then a < b else da.boss < db.boss
end)

function TowerTests.Register(test: (string, (any, any, any) -> ()) -> (), h: { [string]: any })
	local check = h.check
	local join = h.join
	local leave = h.leave
	local countUid = h.countUid

	local function enable(player: any)
		local ok, reason = TowerService.Enable(player)
		check(ok, "режим башни не включился: " .. tostring(reason))
		check(TowerService.Of(player) ~= nil, player.Name .. ": башни нет")
	end

	local function give(player: any, itemId: string): string
		local uid, reason = TowerService.DevGiveItem(player, itemId)
		check(uid, ("%s: %s не выдан: %s"):format(player.Name, itemId, tostring(reason)))
		return uid :: string
	end

	local function build(player: any, uid: string)
		local ok, reason = TowerService.Build(player, uid, { quiet = true })
		check(ok, ("%s: этаж %s не построен: %s"):format(player.Name, uid, tostring(reason)))
	end

	local function buildMany(player: any, n: number, from: number?): { string }
		local uids = {}
		for i = (from or 1), (from or 1) + n - 1 do
			local uid = give(player, BUILDABLE[i])
			build(player, uid)
			table.insert(uids, uid)
		end
		return uids
	end

	local function order(player: any): { string }
		return TowerRules.Order(DataService.GetData(player))
	end

	local function invariants(player: any)
		local ok, problems = TowerRules.Check(DataService.GetData(player), Items)
		check(ok, player.Name .. ": инварианты башни: " .. table.concat(problems, "; "))
	end

	local function towerOf(player: any): any
		local t = TowerService.Of(player)
		check(t, player.Name .. ": нет башни")
		return t
	end

	local function stand(player: any, owner: any, index: number, spot: number?)
		local t = towerOf(owner)
		player:MoveTo(TowerBuilder.Spot(t.model, index, spot or 1).Position)
	end

	-- Под игроком плита этажа index башни owner (луч вниз по серверному каркасу).
	local function onFloor(player: any, owner: any, index: number): boolean
		local t = towerOf(owner)
		local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		if not root then
			return false
		end
		local params = RaycastParams.new()
		params.FilterType = Enum.RaycastFilterType.Include
		params.FilterDescendantsInstances = { t.model }
		local hit = workspace:Raycast(root.Position, Vector3.new(0, -8, 0), params)
		local model = hit and hit.Instance:FindFirstAncestorOfClass("Model")
		return model ~= nil and hit.Instance.Name == "Slab" and model:GetAttribute("Index") == index
	end

	-- Гость-персонаж (без участка и профиля: участков всего 5, а гостю они не нужны — лифт и сдвиг смотрят на персонажа).
	local function extraPlayer(ctx: any, name: string): any
		local p = TestPlayer.new(name)
		ctx.track(p)
		return p
	end

	local function lastInventory(player: any): { any }?
		for i = #player.Sent, 1, -1 do
			local event = player.Sent[i]
			if event.name == Remotes.Names.InventoryChanged then
				return event.args[1]
			end
		end
		return nil
	end

	test(
		"Башня: первый этаж — Stored → Floor, builtAt и порядок, доход этажа, модель наверху",
		function(A, _B, ctx)
			enable(A)
			local uid = give(A, "GoldenThrone")
			check(ItemRegistry.Get(uid).state == "Stored", "выданный предмет не в инвентаре")
			local ok, reason = TowerService.Build(A, uid)
			check(ok, "не построен: " .. tostring(reason))
			local data = DataService.GetData(A)
			check(#order(A) == 1 and order(A)[1] == uid, "порядок этажей")
			check(type(data.items[uid].builtAt) == "number" and data.items[uid].place == "storage", "builtAt / place")
			check(ItemRegistry.Get(uid).state == "Floor", "реестр не Floor")
			check(ItemRegistry.GetFloor(A.UserId, "GoldenThrone") == uid, "индекс этажей реестра")
			local t = towerOf(A)
			local model = t.models[uid]
			check(
				model and model:GetAttribute("Index") == 1 and model:GetAttribute("State") == "Building",
				"модель этажа 1"
			)
			check(math.abs(model:GetAttribute("BaseY") - TowerRules.BaseY(1, cfg)) < 1e-6, "высота этажа 1")
			check(IncomeService.TotalFor(A.UserId) == IncomeService.Of("GoldenThrone"), "доход этажа")
			check(A:GetAttribute("Income") == IncomeService.Of("GoldenThrone"), "атрибут Income")
			check(t.model:GetAttribute("FloorCount") == 1, "FloorCount")
			check(countUid(uid) == 1, "экспонат этажа в мире — один")
			task.wait(cfg.BuildSeconds + 0.2)
			check(
				model:GetAttribute("State") == "Built",
				"анимация постройки не закончилась"
			)
			invariants(A)
			ctx.note(
				("этаж 1: %s, доход %d/с"):format(
					Items.GoldenThrone.displayName,
					IncomeService.TotalFor(A.UserId)
				)
			)
		end
	)

	test(
		"Башня: 2-й и 10-й уникальный этажи — порядок снизу вверх, высоты, коробки этажей не пересекаются",
		function(A)
			enable(A)
			local uids = buildMany(A, 10)
			check(#order(A) == 10, "этажей не 10")
			local t = towerOf(A)
			local income = 0
			for i, uid in uids do
				check(order(A)[i] == uid, "порядок: этаж " .. i)
				local m = t.models[uid]
				check(m:GetAttribute("Index") == i, "Index этажа " .. i)
				check(math.abs(m:GetAttribute("BaseY") - TowerRules.BaseY(i, cfg)) < 1e-6, "BaseY этажа " .. i)
				income += IncomeService.Of(ItemRegistry.Get(uid).itemId)
			end
			check(IncomeService.TotalFor(A.UserId) == income, "сумма доходов 10 этажей")
			check(t.model:GetAttribute("FloorCount") == 10, "в лифте не 11 пунктов (холл + 10)")
			-- каркас этажа i целиком ниже плиты этажа i+1
			for i = 1, 9 do
				local top, bottom = -math.huge, math.huge
				for _, p in t.models[uids[i]]:GetChildren() do
					if p:IsA("BasePart") and p:GetAttribute("TowerShell") then
						top = math.max(top, p.Position.Y + p.Size.Y / 2)
					end
				end
				for _, p in t.models[uids[i + 1]]:GetChildren() do
					if p:IsA("BasePart") and p:GetAttribute("TowerShell") then
						bottom = math.min(bottom, p.Position.Y - p.Size.Y / 2)
					end
				end
				check(
					top <= bottom + 1e-3,
					("каркасы этажей %d и %d пересекаются"):format(i, i + 1)
				)
			end
			invariants(A)
		end
	)

	test(
		"Башня: тот же ItemID ещё раз — отказ и «повтор»; у другого игрока — свой этаж того же вида",
		function(A, B)
			enable(A)
			enable(B)
			local a1 = give(A, "Moai")
			build(A, a1)
			local a2 = give(A, "Moai")
			local ok, reason = TowerService.Build(A, a2, { quiet = true })
			check(
				not ok and reason and string.find(reason, "уже есть"),
				"второй Moai построен: " .. tostring(reason)
			)
			check(TowerRules.IsDuplicate(DataService.GetData(A), a2), "второй Moai не повтор")
			check(ItemRegistry.Get(a2).state == "Stored" and #order(A) == 1, "повтор изменил башню")
			local b1 = give(B, "Moai")
			build(B, b1)
			check(
				#order(B) == 1 and ItemRegistry.GetFloor(B.UserId, "Moai") == b1,
				"у B нет своего этажа Moai"
			)
			check(ItemRegistry.GetFloor(A.UserId, "Moai") == a1, "этаж A изменился")
			invariants(A)
			invariants(B)
		end
	)

	test(
		"Башня: повторный и одновременный Build одного uid и спам запросов — один этаж",
		function(A, _B, ctx)
			enable(A)
			local uid = give(A, "SpaceHelmet")
			local results = {}
			for _ = 1, 3 do
				task.spawn(function()
					table.insert(results, (TowerService.Build(A, uid)))
				end)
			end
			local okCount = 0
			for _, r in results do
				if r then
					okCount += 1
				end
			end
			check(okCount == 1 and #order(A) == 1, "одновременные Build: построено " .. okCount)
			task.wait(1.1)
			-- спам по разным uid: лимит RateLimits.TowerBuild в секунду
			local uids = {}
			for i = 1, 8 do
				table.insert(uids, give(A, BUILDABLE[i + 20]))
			end
			local built = 0
			for _, u in uids do
				if TowerService.Build(A, u) then
					built += 1
				end
			end
			check(
				built <= GameConfig.RateLimits.TowerBuild,
				"лимит запросов не сработал: " .. built
			)
			local seen = {}
			for _, u in order(A) do
				check(not seen[u], "uid в башне дважды")
				seen[u] = true
			end
			invariants(A)
			ctx.note(
				("спам 8 запросов за секунду: построено %d (лимит %d)"):format(
					built,
					GameConfig.RateLimits.TowerBuild
				)
			)
		end
	)

	test(
		"Башня: отказы постройки и защита построенного — постамент, удаление, передача, чужое, подделки",
		function(A, B, ctx)
			enable(A)
			local floor = give(A, "GoldenThrone")
			build(A, floor)
			local data = DataService.GetData(A)
			-- чужой, поддельный, слишком длинный uid
			enable(B)
			local foreign = give(B, "Moai")
			check(not TowerService.Build(A, foreign, { quiet = true }), "построен чужой предмет")
			check(
				not TowerService.Build(A, "нет-такого", { quiet = true }),
				"построен поддельный uid"
			)
			check(not TowerService.Build(A, string.rep("x", 200), { quiet = true }), "длинный uid")
			check(not TowerService.Build(A, 42, { quiet = true }), "uid-число")
			-- pending, legacy, без дохода, неизвестный
			local pend = give(A, "TRexSkeleton")
			data.items[pend].pending = "проверка"
			check(not TowerService.Build(A, pend, { quiet = true }), "построен pending")
			data.items[pend].pending = nil
			if LEGACY then
				check(not TowerService.Build(A, give(A, LEGACY), { quiet = true }), "построен legacy")
			end
			if DRAFT then
				local draft = give(A, DRAFT)
				check(
					not TowerService.Build(A, draft, { quiet = true }),
					"построен предмет без дохода"
				)
				check(
					not TowerRules.IsDuplicate(data, draft),
					"предмет без дохода стал повтором"
				)
			end
			check(
				TowerService.DevGiveItem(A, "НетТакогоПредмета") == nil,
				"выдан неизвестный предмет"
			)
			-- режим выключен
			local C = extraPlayer(ctx, "Тест_C")
			local ok, reason = TowerService.Build(C, foreign)
			check(
				not ok and reason == "Башня выключена",
				"постройка без режима башни: " .. tostring(reason)
			)
			-- построенный экземпляр недоступен операциям инвентаря и прежней кражи (DataService — единая проверка)
			check(
				not DataService.SetItemPlace(A, floor, "slot", 1),
				"этаж поставлен на постамент"
			)
			check(
				not DataService.SetItemPlace(A, floor, "storage"),
				"этаж переведён в инвентарь мимо башни"
			)
			DataService.RemoveItem(A, floor)
			check(
				data.items[floor] ~= nil,
				"этаж удалён общей функцией (продажа/удаление)"
			)
			check(
				not DataService.TransferItem(A, B, floor, table.clone(data.items[floor]), "t-1"),
				"этаж передан кражей"
			)
			check(
				data.items[floor] ~= nil and DataService.GetData(B).items[floor] == nil,
				"передача изменила профили"
			)
			check(
				not ItemRegistry.Transition(floor, "Displayed", { owner = A.UserId, slot = 1 }),
				"реестр: этаж → постамент"
			)
			check(not ItemRegistry.Transition(floor, "Carried", { carrier = A }), "реестр: этаж в руки")
			check(
				not ItemRegistry.Transition(floor, "Lifting", { thief = B }),
				"реестр: этаж крадут прежней кражей"
			)
			InventoryService.Handlers.Action(A, "Display", floor, 1)
			check(
				ItemRegistry.Get(floor).state == "Floor" and data.items[floor].place == "storage",
				"окно выставило этаж"
			)
			check(not TowerService.Build(A, floor, { quiet = true }), "этаж построен второй раз")
			check(#order(A) == 1, "башня изменилась от отказов")
			invariants(A)
		end
	)

	test(
		"Башня: сохранение и повторный вход — этажи, порядок, реестр, доход, модели без дублей",
		function(A, _B, ctx)
			enable(A)
			local uids = buildMany(A, 3, 5)
			local dup = give(A, BUILDABLE[5]) -- повтор первого этажа
			local income = IncomeService.TotalFor(A.UserId)
			local userId = A.UserId
			leave(A)
			for _, uid in uids do
				check(
					ItemRegistry.Get(uid) == nil and countUid(uid) == 0,
					"этаж A остался после выхода"
				)
			end
			local again = TestPlayer.new("Тест_A_снова")
			again.UserId = userId
			ctx.track(again)
			check(join(again), "A не вошёл повторно")
			check(TowerService.Of(again) ~= nil, "башня не восстановлена")
			local restored = order(again)
			check(#restored == 3, "этажей после входа: " .. #restored)
			for i, uid in uids do
				check(restored[i] == uid, "порядок после входа: этаж " .. i)
				check(ItemRegistry.Get(uid).state == "Floor", "реестр после входа: этаж " .. i)
				check(countUid(uid) == 1, "дубль модели этажа " .. i)
			end
			check(#TowerService.Of(again).model.Floors:GetChildren() == 3, "лишние модели этажей")
			check(TowerRules.IsDuplicate(DataService.GetData(again), dup), "повтор после входа")
			check(IncomeService.TotalFor(userId) == income, "доход после входа")
			invariants(again)
		end
	)

	test(
		"Башня: миграция v5 → v6 тестовой копии профиля — уникальные выставленные → этажи, повторно — без изменений",
		function(A)
			local data = DataService.GetData(A)
			local function put(uid: string, id: string, place: string, slot: number?)
				data.items[uid] = { id = id, mods = {}, place = place, slot = slot, rot = 0, acquiredAt = 1 }
			end
			put("m1", "Moai", "slot", 1)
			put("m2", "Moai", "slot", 2)
			put("m3", "Moai", "storage")
			put("t1", "GoldenThrone", "slot", 3)
			if LEGACY then
				put("lg", LEGACY, "slot", 4)
			end
			local before = 0
			for _ in data.items do
				before += 1
			end
			enable(A)
			check(
				#order(A) == 2 and order(A)[1] == "m1" and order(A)[2] == "t1",
				"этажи после миграции"
			)
			check(TowerRules.IsDuplicate(data, "m2") and TowerRules.IsDuplicate(data, "m3"), "повторы Moai")
			check(LEGACY == nil or data.items.lg.builtAt == nil, "legacy стал этажом")
			local after = 0
			for uid, r in data.items do
				after += 1
				check(r.place == "storage" and r.slot == nil, uid .. " остался на постаменте")
			end
			check(after == before, "записей стало меньше")
			check(
				type(data.migration) == "table" and type(data.migration.tower) == "table",
				"нет отметки миграции"
			)
			local snapshot = table.clone(order(A))
			DataService.EnterTowerMode(A)
			check(
				#order(A) == #snapshot and order(A)[1] == snapshot[1],
				"повторная миграция изменила башню"
			)
			invariants(A)
		end
	)

	test(
		"Башня: испорченный профиль при входе чинится — лишние и чужие uid, два этажа вида, неизвестный предмет",
		function(A, _B, ctx)
			enable(A)
			local uids = buildMany(A, 2, 30)
			local data = DataService.GetData(A)
			-- порча: несуществующий uid, повтор uid, второй этаж того же вида вне порядка, этаж неизвестного предмета
			table.insert(data.tower.order, "призрак")
			table.insert(data.tower.order, uids[1])
			data.items.sameKind =
				{ id = BUILDABLE[30], mods = {}, place = "storage", rot = 0, acquiredAt = 1, builtAt = 5 }
			data.items.unknown =
				{ id = "НетТакого", mods = {}, place = "storage", rot = 0, acquiredAt = 1, builtAt = 6 }
			table.insert(data.tower.order, "unknown")
			local userId = A.UserId
			leave(A)
			local again = TestPlayer.new("Тест_A_снова")
			again.UserId = userId
			ctx.track(again)
			check(join(again), "A не вошёл")
			local fixed = order(again)
			check(
				#fixed == 2 and fixed[1] == uids[1] and fixed[2] == uids[2],
				"порядок после починки"
			)
			local d = DataService.GetData(again)
			check(
				d.items.sameKind and d.items.sameKind.builtAt == nil,
				"второй этаж того же вида не снят"
			)
			check(
				d.items.unknown ~= nil and d.items.unknown.builtAt == nil,
				"неизвестный предмет: данные потеряны или этаж"
			)
			check(ItemRegistry.Get("unknown") == nil, "неизвестный предмет в реестре")
			invariants(again)
		end
	)

	test(
		"Башня: лифт — переносы в холл и на этажи, отказы, место высадки на полу своего этажа",
		function(A, _B, ctx)
			enable(A)
			buildMany(A, 3, 40)
			local plot = PlotService.GetPlotOf(A)
			local t = towerOf(A)
			local index = plot.index
			stand(A, A, 0)
			local r = ElevatorService.Handlers.Go(A, index, 2)
			check(r and r.ok, "лифт холл → 2: " .. tostring(r and r.reason))
			check(onFloor(A, A, 2), "после лифта не на полу этажа 2")
			task.wait(0.4)
			r = ElevatorService.Handlers.Go(A, index, 0)
			check(r and r.ok and onFloor(A, A, 0), "лифт 2 → холл")
			task.wait(0.4)
			r = ElevatorService.Handlers.Go(A, index, 9)
			check(
				r and not r.ok and r.reason == "Такого этажа нет",
				"несуществующий этаж: " .. tostring(r and r.reason)
			)
			task.wait(0.4)
			A:MoveTo(TowerBuilder.FloorCFrame(t.model.WorldPivot, 0).Position + Vector3.new(0, 3, -12))
			r = ElevatorService.Handlers.Go(A, index, 1)
			check(
				r and not r.ok and r.reason == "Подойдите к лифту",
				"далеко от лифта: " .. tostring(r and r.reason)
			)
			task.wait(0.4)
			stand(A, A, 0)
			A:SetAttribute("Knocked", true)
			r = ElevatorService.Handlers.Go(A, index, 1)
			check(r and not r.ok, "оглушённый уехал")
			A:SetAttribute("Knocked", nil)
			task.wait(0.4)
			A:SetAttribute("Snared", true)
			r = ElevatorService.Handlers.Go(A, index, 1)
			check(r and not r.ok, "в капкане уехал")
			A:SetAttribute("Snared", nil)
			task.wait(0.4)
			check(
				ElevatorService.Handlers.Go(A, "1", 1) == nil and ElevatorService.Handlers.Go(A, index, 1.5) == nil,
				"подделка"
			)
			task.wait(0.4)
			t.lockUntil = os.clock() + 1
			r = ElevatorService.Handlers.Go(A, index, 1)
			check(
				r and not r.ok and string.find(r.reason, "перестраивается"),
				"лифт во время перестройки"
			)
			t.lockUntil = 0
			task.wait(0.4)
			for target = 1, 3 do
				r = ElevatorService.Handlers.Go(A, index, target)
				check(r and r.ok and onFloor(A, A, target), "лифт на этаж " .. target)
				task.wait(0.4)
			end
			ctx.note(
				"лифт: холл ↔ 1…3, отказы — нет этажа, далеко, оглушён, капкан, подделка, перестройка"
			)
		end
	)

	test(
		"Башня: снятие этажей — 5 из 10, верхний, первый, единственный; выше сдвигаются, игроки на своём полу",
		function(A, _B, ctx)
			enable(A)
			local uids = buildMany(A, 10, 10)
			local t = towerOf(A)
			local C = extraPlayer(ctx, "Тест_C")
			local D = extraPlayer(ctx, "Тест_D")
			local E = extraPlayer(ctx, "Тест_E")
			local F = extraPlayer(ctx, "Тест_F")
			stand(C, A, 7)
			stand(D, A, 9)
			stand(E, A, 5) -- стоит на снимаемом
			stand(F, A, 0)
			local was = TowerService.Remove(A, uids[5], { C, D, E, F })
			check(was == 5 and #order(A) == 9, "снят не 5-й")
			for i, uid in order(A) do
				check(t.models[uid]:GetAttribute("Index") == i, "Index после сдвига: " .. i)
				check(
					math.abs(t.models[uid]:GetAttribute("BaseY") - TowerRules.BaseY(i, cfg)) < 1e-6,
					"промежуток: этаж " .. i
				)
			end
			task.wait(0.2)
			check(onFloor(C, A, 6), "C (был на 7) не на полу этажа 6")
			check(onFloor(D, A, 8), "D (был на 9) не на полу этажа 8")
			check(onFloor(E, A, 5), "E (стоял на снятом) не на площадке нового 5-го")
			check(onFloor(F, A, 0), "F в холле сдвинулся")
			check(t.models[uids[6]]:GetAttribute("Index") == 5, "бывший 6-й не стал 5-м")
			check(ItemRegistry.Get(uids[5]).state == "Stored", "снятый — не в инвентаре")
			task.wait(cfg.ShiftLock)
			-- верхний, первый, потом до единственного и его
			check(TowerService.Remove(A, order(A)[#order(A)]) == 9, "верхний")
			check(TowerService.Remove(A, order(A)[1]) == 1, "первый")
			while #order(A) > 1 do
				TowerService.Remove(A, order(A)[1])
			end
			stand(C, A, 1)
			check(TowerService.Remove(A, order(A)[1], { C }) == 1 and #order(A) == 0, "единственный")
			task.wait(0.2)
			check(onFloor(C, A, 0), "C с единственного этажа не в холле")
			check(
				t.model:GetAttribute("FloorCount") == 0 and #t.model.Floors:GetChildren() == 0,
				"остались модели"
			)
			invariants(A)
			ctx.note(
				"снятие 5/10: игроки 7→6, 9→8, со снятого — на новый 5-й, холл не тронут; верхний, первый, единственный"
			)
		end
	)

	test(
		"Башня: перестановка и лифт после постройки, снятия и перестановки — список и высоты новые",
		function(A, _B, ctx)
			enable(A)
			local uids = buildMany(A, 4, 50)
			local plot = PlotService.GetPlotOf(A)
			local t = towerOf(A)
			local C = extraPlayer(ctx, "Тест_C")
			stand(C, A, 4)
			check(TowerService.Move(A, uids[4], 1, { C }), "перестановка 4 → 1")
			check(
				order(A)[1] == uids[4] and order(A)[2] == uids[1],
				"порядок после перестановки"
			)
			task.wait(0.2)
			check(onFloor(C, A, 1), "C не уехал вместе со своим этажом")
			task.wait(cfg.ShiftLock)
			stand(A, A, 0)
			local r = ElevatorService.Handlers.Go(A, plot.index, 4)
			check(r and r.ok and onFloor(A, A, 4), "лифт на 4 после перестановки")
			task.wait(0.4)
			local extra = give(A, BUILDABLE[60])
			build(A, extra)
			check(t.model:GetAttribute("FloorCount") == 5, "новый этаж не в списке")
			r = ElevatorService.Handlers.Go(A, plot.index, 5)
			check(r and r.ok and onFloor(A, A, 5), "лифт на новый 5-й")
			task.wait(0.4)
			TowerService.Remove(A, uids[2], { A })
			task.wait(cfg.ShiftLock)
			r = ElevatorService.Handlers.Go(A, plot.index, 4)
			check(
				r and r.ok and onFloor(A, A, 4) and t.model:GetAttribute("FloorCount") == 4,
				"лифт после снятия"
			)
			invariants(A)
		end
	)

	test(
		"Башня: игроки на 3, 20, 40 и в лифте — одновременно постройка и снятие 10-го; все на полу",
		function(A, _B, ctx)
			enable(A)
			local uids = {}
			for i = 1, 41 do
				local uid = give(A, BUILDABLE[i])
				build(A, uid)
				table.insert(uids, uid)
			end
			local plot = PlotService.GetPlotOf(A)
			local C = extraPlayer(ctx, "Тест_C")
			local D = extraPlayer(ctx, "Тест_D")
			local E = extraPlayer(ctx, "Тест_E")
			local F = extraPlayer(ctx, "Тест_F")
			stand(C, A, 3)
			stand(D, A, 20)
			stand(E, A, 40)
			stand(F, A, 0)
			local r = ElevatorService.Handlers.Go(F, plot.index, 40, { C, D, E })
			check(r and r.ok and onFloor(F, A, 40), "F в лифте не доехал до 40")
			build(A, give(A, BUILDABLE[42]))
			TowerService.Remove(A, uids[10], { C, D, E, F })
			task.wait(0.2)
			check(onFloor(C, A, 3), "C на 3")
			check(onFloor(D, A, 19), "D (20) не на 19")
			check(onFloor(E, A, 39) and onFloor(F, A, 39), "E и F (40) не на 39")
			local e = E.Character.HumanoidRootPart.Position
			local f = F.Character.HumanoidRootPart.Position
			check((e - f).Magnitude > 1, "E и F в одной точке")
			check(#order(A) == 41, "этажей после постройки и снятия")
			invariants(A)
			ctx.note(
				"41 этаж, игроки на 3/20/40 и в лифте; постройка 42-го и снятие 10-го — все на своих полах"
			)
		end
	)

	test(
		"Башня: гость — лифт чужой башни работает, постройка в чужой башне — нет",
		function(A, B)
			enable(A)
			buildMany(A, 2, 70)
			local plot = PlotService.GetPlotOf(A)
			stand(B, A, 0)
			local r = ElevatorService.Handlers.Go(B, plot.index, 2)
			check(r and r.ok and onFloor(B, A, 2), "гость не доехал")
			local uid = order(A)[1]
			check(
				not TowerService.Build(B, uid, { quiet = true }),
				"гость построил этаж владельца"
			)
			enable(B)
			check(
				not TowerService.Build(B, uid, { quiet = true }),
				"B с режимом построил чужой uid"
			)
			invariants(A)
		end
	)

	test(
		"Башня: выключение режима — участок как прежде (дерево и детали), у соседа ничего не менялось",
		function(A, B)
			local function summary(plot: any): string
				local parts = {}
				for _, child in plot.model:GetChildren() do
					local n = 0
					for _, d in child:GetDescendants() do
						if d:IsA("BasePart") then
							n += 1
						end
					end
					if child:IsA("BasePart") then
						n += 1
					end
					table.insert(parts, child.Name .. "=" .. n)
				end
				table.sort(parts)
				return table.concat(parts, ",")
			end
			local plotA, plotB = PlotService.GetPlotOf(A), PlotService.GetPlotOf(B)
			local beforeA, beforeB = summary(plotA), summary(plotB)
			enable(A)
			buildMany(A, 2, 80)
			check(
				plotA.model:FindFirstChild("Building") == nil and plotA.model:FindFirstChild("Tower"),
				"башня вместо здания"
			)
			check(summary(plotB) == beforeB, "участок соседа изменился")
			TowerService.Disable(A)
			check(
				summary(plotA) == beforeA,
				"участок после выключения: " .. summary(plotA) .. " ≠ " .. beforeA
			)
			check(summary(plotB) == beforeB, "участок соседа после выключения")
		end
	)

	test(
		"Башня: отказ реестра посреди постройки — профиль откатывается, промежуточного состояния нет",
		function(A)
			enable(A)
			local u1 = give(A, "GoldenThrone")
			build(A, u1)
			-- рассинхрон: профиль «забыл» этаж, реестр ещё держит Floor этого вида
			local data = DataService.GetData(A)
			TowerRules.RemoveFloor(data, u1)
			local u2 = give(A, "GoldenThrone")
			local ok = TowerService.Build(A, u2, { quiet = true })
			check(not ok, "постройка прошла при отказе реестра")
			check(
				data.items[u2].builtAt == nil and TowerRules.IndexOf(data, u2) == nil,
				"профиль не откатился"
			)
			check(ItemRegistry.Get(u2).state == "Stored", "реестр изменил второй экземпляр")
			check(TowerService.Of(A).models[u2] == nil, "модель этажа осталась")
		end
	)

	test(
		"Башня: окно инвентаря — номер этажа, «повтор», без постаментов; обычный режим — без полей башни",
		function(A, B)
			enable(A)
			local floor = give(A, "GoldenThrone")
			build(A, floor)
			local dup = give(A, "GoldenThrone")
			local free = give(A, "Moai")
			A:ClearSent()
			InventoryService.Sync(A)
			local list = lastInventory(A)
			check(list, "окно не получило инвентарь")
			local rows = {}
			for _, row in list :: { any } do
				rows[row.uid] = row
			end
			check(rows[floor] and rows[floor].floor == 1 and rows[floor].tower, "этаж в окне")
			check(rows[dup] and rows[dup].duplicate == true and rows[dup].floor == nil, "повтор в окне")
			check(rows[free] and not rows[free].duplicate and not rows[free].floor, "уникальный в окне")
			B:ClearSent()
			InventoryService.Sync(B)
			for _, row in lastInventory(B) or {} do
				check(row.tower == nil and row.floor == nil, "у обычного игрока поля башни")
			end
		end
	)
end

return TowerTests

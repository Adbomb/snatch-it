--!nocheck
-- Проверка правил музея-небоскрёба без Roblox Studio (этап B, docs/TOWER_PLAN.md v3): Shared/TowerRules — постройка,
-- повторы, снятие, перестановка, миграция v5 → v6, починка испорченных профилей, совместимость с Inventory.Normalize,
-- инварианты на 10 000 случайных последовательностях; темы Shared/Floors — бюджет деталей по LOD, согласие каркаса и
-- вида, пустая площадка лифта, нет совпадающих граней (World/FaceCheck). Все профили — таблицы в памяти.
-- Запуск из корня: lune run scripts/lune/check_tower.luau. Ошибка — код возврата 1.

local process = require("@lune/process")
local roblox = require("@lune/roblox")

local Env = require("./env")

local Color3 = roblox.Color3
local CFrame = roblox.CFrame

local GameConfig = Env.Require("ReplicatedStorage.Shared.Config.GameConfig")
local Items = Env.Require("ReplicatedStorage.Shared.Config.Items")
local Inventory = Env.Require("ReplicatedStorage.Shared.Inventory")
local TowerRules = Env.Require("ReplicatedStorage.Shared.TowerRules")
local Floors = Env.Require("ReplicatedStorage.Shared.Floors")
local FaceCheck = Env.Require("ServerScriptService.Server.World.FaceCheck")
local FloorMeshes = Env.Require("ReplicatedStorage.Shared.Floors.FloorMeshes")

-- бюджет треугольников мешей этажа по уровням детализации (силуэт виден у каждого этажа всегда)
local MESH_TRIS = { facade = 14000, interior = 12000, silhouette = 400 }

local cfg = GameConfig.Tower
local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	if not ok then
		print("  ОШИБКА " .. message)
		failed += 1
	else
		passed += 1
	end
end
local function section(name: string)
	print("— " .. name)
end

local function deepCopy(value)
	if type(value) ~= "table" then
		return value
	end
	local out = {}
	for k, v in value do
		out[k] = deepCopy(v)
	end
	return out
end

local function deepEqual(a, b): boolean
	if type(a) ~= type(b) then
		return false
	end
	if type(a) ~= "table" then
		return a == b
	end
	for k, v in a do
		if not deepEqual(v, b[k]) then
			return false
		end
	end
	for k in b do
		if a[k] == nil then
			return false
		end
	end
	return true
end

local function count(t): number
	local n = 0
	for _ in t do
		n += 1
	end
	return n
end

-- предметы с доходом, отсортированные (для детерминированных профилей)
local buildable = {}
for id, def in Items do
	if TowerRules.Buildable(def) then
		table.insert(buildable, id)
	end
end
table.sort(buildable)
local legacyId, draftId
for id, def in Items do
	if def.legacy and not legacyId then
		legacyId = id
	elseif not def.legacy and def.income == 0 and not draftId then
		draftId = id
	end
end

local function record(id: string, extra)
	local r = { id = id, mods = {}, place = "storage", rot = 0, acquiredAt = 1 }
	for k, v in extra or {} do
		r[k] = v
	end
	return r
end

local function profile(items)
	return { schema = 5, coins = 0, museumLevel = 1, items = items or {} }
end

section("обычный профиль без башни")
do
	local data = profile({ a = record("Moai"), b = record("Moai", { place = "slot", slot = 1 }) })
	local before = deepCopy(data)
	local report = TowerRules.Normalize(data, Items)
	check(
		not report.changed and data.tower == nil and deepEqual(data, before),
		"Normalize не трогает профиль без башни"
	)
	check(not TowerRules.HasTower(data), "HasTower = false у обычного профиля")
end

section("постройка, повторы, отказы")
do
	local data = profile({
		m1 = record("Moai"),
		m2 = record("Moai"),
		t1 = record("GoldenThrone"),
		leg = record(legacyId or "Moai"),
		draft = record(draftId or "Moai"),
		unk = record("NoSuchItem"),
		pend = record("TRexSkeleton", { pending = "tr-1" }),
		shown = record("SpaceHelmet", { place = "slot", slot = 2 }),
	})
	local ok = TowerRules.CanBuild(data, "m1", Items)
	check(ok, "первый Moai строится")
	TowerRules.AddFloor(data, "m1", 100)
	check(TowerRules.IndexOf(data, "m1") == 1 and data.items.m1.builtAt == 100, "этаж 1 = m1, builtAt")
	local ok2, why2 = TowerRules.CanBuild(data, "m2", Items)
	check(
		not ok2 and why2 and string.find(why2, "уже есть"),
		"второй Moai — отказ (вид уже стоит)"
	)
	check(TowerRules.IsDuplicate(data, "m2"), "m2 — повтор")
	check(not TowerRules.IsDuplicate(data, "m1"), "этаж — не повтор")
	local okAgain = TowerRules.CanBuild(data, "m1", Items)
	check(not okAgain, "этаж нельзя построить второй раз")
	check(TowerRules.CanBuild(data, "t1", Items), "другой вид строится")
	if legacyId then
		check(not TowerRules.CanBuild(data, "leg", Items), "legacy — отказ")
	end
	if draftId then
		check(not TowerRules.CanBuild(data, "draft", Items), "черновик без дохода — отказ")
		check(not TowerRules.IsDuplicate(data, "draft"), "предмет без дохода — не повтор")
	end
	check(not TowerRules.CanBuild(data, "unk", Items), "неизвестный предмет — отказ")
	check(not TowerRules.CanBuild(data, "pend", Items), "pending — отказ")
	check(not TowerRules.CanBuild(data, "shown", Items), "выставленный — отказ")
	check(not TowerRules.CanBuild(data, "nope", Items), "нет записи — отказ")
	check(not TowerRules.CanBuild(data, 42, Items), "не строка — отказ")
	TowerRules.AddFloor(data, "t1", 101)
	check(TowerRules.Check(data, Items), "инварианты после двух построек")
	-- у другого игрока тот же вид — свой этаж
	local other = profile({ x = record("Moai") })
	check(TowerRules.CanBuild(other, "x", Items), "другой игрок строит тот же вид")
end

section("снятие, повторное восстановление, перестановка")
do
	local data = profile({})
	for i = 1, 10 do
		data.items["u" .. i] = record(buildable[i])
		TowerRules.AddFloor(data, "u" .. i, i)
	end
	check(#TowerRules.Order(data) == 10 and TowerRules.Check(data, Items), "10 этажей")
	local was = TowerRules.RemoveFloor(data, "u5")
	check(was == 5 and #TowerRules.Order(data) == 9, "снят 5-й")
	check(
		TowerRules.IndexOf(data, "u6") == 5 and TowerRules.IndexOf(data, "u10") == 9,
		"выше 5-го сдвинулись вниз"
	)
	check(
		data.items.u5 and data.items.u5.builtAt == nil and data.items.u5.place == "storage",
		"u5 — снова предмет"
	)
	check(TowerRules.CanBuild(data, "u5", Items), "снятый вид можно построить снова")
	TowerRules.AddFloor(data, "u5", 50)
	check(TowerRules.IndexOf(data, "u5") == 10, "восстановленный — наверху")
	check(
		TowerRules.MoveFloor(data, "u5", 1) == 10 and TowerRules.IndexOf(data, "u5") == 1,
		"перестановка на 1-й"
	)
	check(TowerRules.MoveFloor(data, "u5", 99) == nil, "перестановка за пределы — отказ")
	check(TowerRules.RemoveFloor(data, "nope") == nil, "снять несуществующий — nil")
	for _ = 1, 10 do
		TowerRules.RemoveFloor(data, TowerRules.Order(data)[1])
	end
	check(
		#TowerRules.Order(data) == 0 and TowerRules.Check(data, Items),
		"сняты все, включая единственный"
	)
	check(TowerRules.BaseY(0, cfg) == 0 and TowerRules.BaseY(1, cfg) == cfg.Lobby.Height, "BaseY холла и 1-го")
	check(TowerRules.BaseY(10, cfg) == cfg.Lobby.Height + 9 * cfg.FloorHeight, "BaseY 10-го")
end

section("миграция v5 → v6")
do
	local data = profile({
		a = record("Moai", { place = "slot", slot = 1 }),
		b = record("Moai", { place = "slot", slot = 2 }),
		c = record("Moai"),
		d = record(legacyId or "Moai", { place = "slot", slot = 3 }),
		e = record("NoSuchItem", { place = "slot", slot = 4 }),
		f = record("GoldenThrone", { place = "slot", slot = 5 }),
	})
	local itemsBefore = count(data.items)
	check(TowerRules.Migrate(data, Items, 1000), "миграция выполнена")
	check(count(data.items) == itemsBefore, "записей столько же")
	local order = TowerRules.Order(data)
	check(
		#order == 2 and order[1] == "a" and order[2] == "f",
		"этажи: Moai (место 1), Золотой трон"
	)
	for uid, r in data.items do
		check(r.place == "storage" and r.slot == nil, "после миграции " .. uid .. " в инвентаре")
	end
	check(
		TowerRules.IsDuplicate(data, "b") and TowerRules.IsDuplicate(data, "c"),
		"второй и третий Moai — повторы"
	)
	check(TowerRules.Check(data, Items), "инварианты после миграции")
	local after = deepCopy(data)
	check(
		not TowerRules.Migrate(data, Items, 2000) and deepEqual(data, after),
		"повторная миграция ничего не меняет"
	)
	local report = TowerRules.Normalize(data, Items)
	check(
		not report.changed and deepEqual(data, after),
		"Normalize после миграции ничего не меняет"
	)
end

section("починка испорченного профиля")
do
	local data = profile({
		a = record("Moai", { builtAt = 1 }),
		b = record("Moai", { builtAt = 2 }), -- второй этаж того же вида
		c = record("GoldenThrone", { builtAt = 3 }), -- этаж вне порядка
		d = record("TRexSkeleton", { builtAt = 4, pending = "tr" }), -- передаётся
		e = record(legacyId or "Moai", { builtAt = 5 }), -- без дохода
		f = record("SpaceHelmet", { builtAt = 6, place = "slot", slot = 7 }), -- этаж на постаменте
	})
	data.tower = { v = 1, order = { "a", "ghost", "a", "b", "d", 7, "f" } }
	local report = TowerRules.Normalize(data, Items)
	local okCheck, problems = TowerRules.Check(data, Items)
	check(
		report.changed and okCheck,
		"после Normalize инварианты держатся: " .. table.concat(problems, "; ")
	)
	local order = TowerRules.Order(data)
	check(
		order[1] == "a" and order[2] == "f" and order[3] == "c" and #order == 3,
		"порядок: a, f, затем c сверху"
	)
	check(
		data.items.b.builtAt == nil and TowerRules.IsDuplicate(data, "b"),
		"лишний этаж того же вида — повтор"
	)
	check(data.items.d.builtAt == 4 and data.items.d.pending == "tr", "pending не тронут")
	check(legacyId == nil or data.items.e.builtAt == nil, "без дохода — признак снят")
	check(data.items.f.place == "storage" and data.items.f.slot == nil, "этаж убран с постамента")
	check(count(data.items) == 6, "ничего не удалено")
	local snap = deepCopy(data)
	local again = TowerRules.Normalize(data, Items)
	check(not again.changed and deepEqual(snap, data), "повторный Normalize ничего не меняет")
	-- нечитаемая башня
	local broken = profile({ x = record("Moai", { builtAt = 1 }) })
	broken.tower = "мусор"
	TowerRules.Normalize(broken, Items)
	check(
		TowerRules.IndexOf(broken, "x") == 1 and TowerRules.Check(broken, Items),
		"нечитаемая башня восстановлена"
	)
end

section("совместимость с Inventory.Normalize")
do
	local data = profile({})
	for i = 1, 5 do
		data.items["u" .. i] = record(buildable[i])
		TowerRules.AddFloor(data, "u" .. i, i)
	end
	data.items.extra = record(buildable[1])
	local function towerState(d)
		local out = { order = deepCopy(d.tower.order) }
		for uid, r in d.items do
			out[uid] = { r.builtAt, r.place, r.slot }
		end
		return out
	end
	local snap = towerState(data)
	-- Inventory.Normalize дописывает записям поле boss — башню и признаки этажей он трогать не должен
	Inventory.Normalize(data, 20, Items, GameConfig.Museum.RotateStep)
	check(deepEqual(snap, towerState(data)), "Inventory.Normalize не трогает башню")
	TowerRules.Normalize(data, Items)
	check(deepEqual(snap, towerState(data)), "Inventory.Normalize + TowerRules.Normalize не меняют башню")
	check(TowerRules.IsDuplicate(data, "extra"), "повтор остаётся повтором")
end

section("10 000 случайных шагов")
do
	local seed = 20261118
	local function rnd(n: number): number
		seed = (seed * 1103515245 + 12345) % 2147483648
		return seed % n + 1
	end
	local pool = {}
	for i = 1, 40 do
		table.insert(pool, buildable[i])
	end
	if legacyId then
		table.insert(pool, legacyId)
	end
	table.insert(pool, "NoSuchItem")
	local data = profile({})
	local nextUid = 0
	local bad = 0
	for step = 1, 10000 do
		local op = rnd(10)
		if op <= 3 then
			nextUid += 1
			data.items["r" .. nextUid] = record(pool[rnd(#pool)])
		elseif op <= 6 then
			local uids = {}
			for uid in data.items do
				table.insert(uids, uid)
			end
			table.sort(uids)
			if #uids > 0 then
				local uid = uids[rnd(#uids)]
				if TowerRules.CanBuild(data, uid, Items) then
					TowerRules.AddFloor(data, uid, step)
				end
			end
		elseif op == 7 then
			local order = TowerRules.Order(data)
			if #order > 0 then
				TowerRules.RemoveFloor(data, order[rnd(#order)])
			end
		elseif op == 8 then
			local order = TowerRules.Order(data)
			if #order > 1 then
				TowerRules.MoveFloor(data, order[rnd(#order)], rnd(#order))
			end
		elseif op == 9 then
			-- «повторный вход»: проверки загрузки
			Inventory.Normalize(data, 20, Items, GameConfig.Museum.RotateStep)
			local snap = deepCopy(data)
			local report = TowerRules.Normalize(data, Items)
			if report.changed or not deepEqual(snap, data) then
				bad += 1
			end
		else
			-- порча данных, затем загрузка чинит
			local order = TowerRules.Order(data)
			local kind = rnd(4)
			if kind == 1 and #order > 0 then
				data.items[order[rnd(#order)]] = nil
			elseif kind == 2 and #order > 0 then
				table.insert(data.tower.order, order[rnd(#order)])
			elseif kind == 3 then
				nextUid += 1
				data.items["r" .. nextUid] = record(pool[rnd(#pool)], { builtAt = step })
			elseif #order > 0 then
				data.items[order[rnd(#order)]].builtAt = nil
			end
			TowerRules.Normalize(data, Items)
		end
		local ok, problems = TowerRules.Check(data, Items)
		if not ok then
			bad += 1
			if bad < 5 then
				print("    шаг " .. step .. ": " .. table.concat(problems, "; "))
			end
		end
	end
	check(
		bad == 0,
		("инварианты на всех шагах (нарушений %d, этажей в конце %d)"):format(
			bad,
			#TowerRules.Order(data)
		)
	)
end

section(
	"темы этажей: бюджет, каркас и вид, площадка лифта, экспонат, грани (каждая тема и пары тем в башне)"
)
do
	check(Floors.Get("Unknown") == Floors.Placeholder, "предмет без темы — временный этаж")
	local THEMES = { Placeholder = Floors.Placeholder }
	for id, theme in Floors.Themes() do
		check(Floors.Get(id) == theme and Floors.HasTheme(id), "тема " .. id .. " зарегистрирована")
		check(
			Items[id] ~= nil and (Items[id].income or 0) > 0,
			"тема " .. id .. " — предмет с доходом"
		)
		THEMES[id] = theme
	end
	local names = {}
	for id in THEMES do
		table.insert(names, id)
	end
	table.sort(names)
	local ctx = { itemName = "Предмет", accent = Color3.fromHex("2F6FD6") }
	local hx, hz = cfg.Half.X, cfg.Half.Y
	local lc, lh = cfg.Landing.Center, cfg.Landing.Half
	local function moved(list, dy)
		local out = {}
		for _, b in list do
			local copy = table.clone(b)
			copy.cframe = CFrame.new(0, dy, 0) * b.cframe
			table.insert(out, copy)
		end
		return out
	end
	local function intrudes(b): boolean
		local p, s = b.cframe.Position, b.size
		local x0, x1 = p.X - s.X / 2, p.X + s.X / 2
		local z0, z1 = p.Z - s.Z / 2, p.Z + s.Z / 2
		local y0, y1 = p.Y - s.Y / 2, p.Y + s.Y / 2
		local inXZ = x0 < lc.X + lh.X - 1e-6
			and x1 > lc.X - lh.X + 1e-6
			and z0 < lc.Z + lh.Y - 1e-6
			and z1 > lc.Z - lh.Y + 1e-6
		return inXZ and y1 > 0.15 + 1e-6 and y0 < 8
	end
	-- брусок b целиком внутри одного из list (по осям; стены и опоры каркаса — по осям)
	local function inside(b, list): boolean
		local p, s = b.cframe.Position, b.size
		for _, w in list do
			local q, r = w.cframe.Position, w.size
			local ok = true
			for _, axis in { "X", "Y", "Z" } do
				local lo, hi = p[axis] - s[axis] / 2, p[axis] + s[axis] / 2
				local wlo, whi = q[axis] - r[axis] / 2, q[axis] + r[axis] / 2
				if lo < wlo - 1e-4 or hi > whi + 1e-4 then
					ok = false
				end
			end
			if ok then
				return true
			end
		end
		return false
	end
	local function faces(groups, label: string)
		local pairsCount, found = FaceCheck.Scan(Env.FakeRoot(groups))
		local anyCount, foundAny = FaceCheck.ScanAny(Env.FakeRoot(groups))
		if pairsCount + anyCount > 0 then
			for key, v in found do
				print("    грань: " .. key .. " ×" .. v.n .. " — " .. v.example)
			end
			for key, v in foundAny do
				print("    грань (any): " .. key .. " ×" .. v.n .. " — " .. v.example)
			end
		end
		check(
			pairsCount + anyCount == 0,
			("совпадающих граней %s: %d / %d"):format(label, pairsCount, anyCount)
		)
	end
	local h1, h2 = TowerRules.BaseY(1, cfg), TowerRules.BaseY(2, cfg)
	local built = {}
	for _, id in names do
		local theme = THEMES[id]
		local shell = theme.shell(cfg)
		local allInterior = theme.decor(cfg, ctx, "interior")
		local allFacade = theme.decor(cfg, ctx, "facade")
		local allSil = theme.decor(cfg, ctx, "silhouette")
		-- меши (кирпич с mesh): габарит проверяется по полосе этажа, форма — в Blender; в проверках граней и
		-- площадки лифта участвуют только обычные детали
		local meshInfo = FloorMeshes[id] and FloorMeshes[id].parts or {}
		local meshCount, meshBad = 0, 0
		local function partsOnly(list, tier: string)
			local out, tris = {}, 0
			for _, b in list do
				if b.mesh then
					meshCount += 1
					local info = meshInfo[b.mesh]
					if
						not info
						or info.tier ~= tier
						or not string.match(info.mesh, "^rbxassetid://%d+$")
						or (b.size - info.size).Magnitude > 1e-3
						or (b.cframe.Position - info.center).Magnitude > 1e-3
					then
						meshBad += 1
					else
						tris += info.tris
					end
				else
					table.insert(out, b)
				end
			end
			return out, tris
		end
		local interior, trisInterior = partsOnly(allInterior, "interior")
		local facade, trisFacade = partsOnly(allFacade, "facade")
		local sil, trisSil = partsOnly(allSil, "silhouette")
		if meshCount > 0 then
			print(
				("    %s: мешей %d, треугольников — интерьер %d, фасад %d, силуэт %d"):format(
					id,
					meshCount,
					trisInterior,
					trisFacade,
					trisSil
				)
			)
			check(
				meshBad == 0,
				id
					.. ": меши есть в FloorMeshes, с MeshId, в своём уровне и на своём месте (нет: "
					.. meshBad
					.. ")"
			)
			check(
				trisInterior <= MESH_TRIS.interior
					and trisFacade <= MESH_TRIS.facade
					and trisSil <= MESH_TRIS.silhouette,
				id .. ": треугольники мешей в бюджете (14 000 / 12 000 / 400)"
			)
		end
		built[id] = { shell = shell, interior = interior, facade = facade, sil = sil }
		print(
			("    %s: каркас %d, интерьер %d, фасад %d, силуэт %d"):format(
				id,
				#shell,
				#allInterior,
				#allFacade,
				#allSil
			)
		)
		-- каркас: у зала не коробкой (порталы, сходящиеся стены, скамьи) столкновений больше, чем у комнаты с колоннами
		check(#shell <= 24, id .. ": каркас ≤ 24")
		check(#allInterior <= 300, id .. ": интерьер ≤ 300")
		check(#allFacade <= 170, id .. ": фасад ≤ 170")
		check(#allSil >= 1 and #allSil <= 12, id .. ": силуэт 1…12")
		local slab = shell[1]
		check(
			slab.name == "Slab" and math.abs(slab.size.X - hx * 2) < 1e-6 and math.abs(slab.size.Z - hz * 2) < 1e-6,
			id .. ": первая деталь каркаса — плита во весь контур"
		)
		-- всё в своей полосе высоты (−плита … до плиты следующего): этажи стыкуются без пересечений
		local outBand = 0
		for _, list in { shell, allInterior, allFacade, allSil } do
			for _, b in list do
				local y = b.cframe.Position.Y
				local r = b.cframe:VectorToWorldSpace(b.size / 2)
				local half = math.abs(r.Y)
				-- повёрнутые: оценка по габариту осей
				local ext = 0
				for _, v in
					{
						b.cframe.RightVector * b.size.X / 2,
						b.cframe.UpVector * b.size.Y / 2,
						b.cframe.LookVector * b.size.Z / 2,
					}
				do
					ext += math.abs(v.Y)
				end
				half = math.max(half, ext)
				if y - ext < -cfg.Slab - 1e-4 or y + ext > cfg.FloorHeight - cfg.Slab + 1e-4 then
					outBand += 1
				end
			end
		end
		check(
			outBand == 0,
			id .. ": все детали в полосе своего этажа (вне: " .. outBand .. ")"
		)
		local blocked = 0
		for _, list in { shell, interior, facade } do
			for _, b in list do
				if intrudes(b) then
					blocked += 1
				end
			end
		end
		check(blocked == 0, id .. ": площадка лифта пуста (мешают " .. blocked .. ")")
		-- экспонат стоит на верхе опоры каркаса
		local at = Floors.ExhibitAt(theme, cfg).Position
		local standing = false
		for _, b in shell do
			local p, s = b.cframe.Position, b.size
			if
				math.abs(p.Y + s.Y / 2 - at.Y) < 1e-4
				and math.abs(at.X - p.X) <= s.X / 2
				and math.abs(at.Z - p.Z) <= s.Z / 2
			then
				standing = true
			end
		end
		check(standing, id .. ": экспонат на верхе опоры каркаса")
		local occl, occlOut = 0, 0
		for _, list in { facade, interior } do
			for _, b in list do
				if b.occlude then
					occl += 1
					if not inside(b, shell) then
						occlOut += 1
					end
				end
			end
		end
		check(
			occl > 0 and occlOut == 0,
			("%s: стены occlude внутри каркаса (%d из %d вне)"):format(id, occlOut, occl)
		)
		-- грани: этаж и такой же над ним, холл и крыша
		faces({
			{ name = "LobbyFacade", bricks = Floors.Lobby.decor(cfg, ctx, "facade") },
			{ name = "LobbyInside", bricks = Floors.Lobby.decor(cfg, ctx, "interior") },
			{ name = "Floor1", bricks = moved(interior, h1) },
			{ name = "Floor1Facade", bricks = moved(facade, h1) },
			{ name = "Floor2", bricks = moved(facade, h2) },
			{ name = "Floor2In", bricks = moved(interior, h2) },
			{ name = "Roof", bricks = moved(Floors.Roof.decor(cfg, ctx, "facade"), h2 + cfg.FloorHeight) },
		}, id)
		faces({
			{ name = "LobbySil", bricks = Floors.Lobby.decor(cfg, ctx, "silhouette") },
			{ name = "S1", bricks = moved(sil, h1) },
			{ name = "S2", bricks = moved(sil, h2) },
			{ name = "F3", bricks = moved(facade, h2 + cfg.FloorHeight) },
		}, id .. " (силуэты)")
	end
	-- пары разных тем одна над другой: фасад+интерьер на фасад+интерьер, силуэт под фасадом и над ним
	local pairsChecked = 0
	for _, a in names do
		for _, b in names do
			if a ~= b then
				local A, Bt = built[a], built[b]
				faces({
					{ name = a .. "In", bricks = moved(A.interior, h1) },
					{ name = a, bricks = moved(A.facade, h1) },
					{ name = b, bricks = moved(Bt.facade, h2) },
					{ name = b .. "In", bricks = moved(Bt.interior, h2) },
					{ name = b .. "Sil", bricks = moved(Bt.sil, h2 + cfg.FloorHeight) },
				}, a .. " под " .. b)
				pairsChecked += 1
			end
		end
	end
	print(("    пар тем одна над другой: %d"):format(pairsChecked))
	local lobbyShell = Floors.Lobby.shell(cfg)
	check(#lobbyShell <= 10, "каркас холла ≤ 10")
	local outside, solids = 0, 0
	for _, b in Floors.Lobby.decor(cfg, ctx, "facade") do
		if b.occlude then
			solids += 1
			if not inside(b, lobbyShell) then
				outside += 1
			end
		end
	end
	check(
		solids > 0 and outside == 0,
		("холл: стены occlude внутри каркаса (%d из %d вне)"):format(outside, solids)
	)
end

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end

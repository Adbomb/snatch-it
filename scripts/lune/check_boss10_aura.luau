--!nocheck
-- Аура Короля-дракона (Config/BossAura) без Studio, этап C.2: настоящие Config/BossAura и Config/Boss10DragonRig.
--   1) у каждого варианта все части слоёв есть у дракона (суставы или добавочные меши);
--   2) морда, корона (голова), челюсть, перепонки крыльев и скипетр не горят — читаются;
--   3) оценка активных частиц при полной силе (частота × жизнь, частота по площади части у byArea) — в бюджете
--      maxParticles (иначе контроллер урезает частоты); пик залпа и всплесков — ниже 1.8 бюджета;
--   4) у настоящего босса — существующий вариант (Active), во сне сила C2 и C3 не ниже 0.8 (по ТЗ — мощная и во сне;
--      у C3 — полная), после поражения гаснет (Defeat = 0);
--   5) энергетическое поле (Flow, Vortex, Veil, RoyalAura — у настоящего босса; у RoyalAura ещё орбиты — в бюджете и не у морды): ленты, кольца и разряды — на частях дракона, не на морде, короне,
--      скипетре и перепонках (кости крыльев — только лентами), лент не больше 90, разрядов в пуле не больше 6; во сне —
--      полная сила.
-- Ничего не пишет. Запуск из корня репозитория: lune run scripts/lune/check_boss10_aura.luau

local process = require("@lune/process")

local Env = require("./env")

local BossAura = Env.Require("ReplicatedStorage.Shared.Config.BossAura")
local rig = Env.Require("ReplicatedStorage.Shared.Config.Boss10DragonRig")

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

local function sizeOf(name: string): Vector3?
	local p = rig.Parts[name] or (rig.Extras and rig.Extras[name])
	return p and p.size
end

local FREE = { Head = true, Jaw = true, Neck4 = true, Scepter = true, ScepterCircle = true, WingMembranes = true }
-- кости крыльев (пальцы): частицам нельзя ни у одного варианта, лентам энергетического поля — можно (тонко, по краю
-- перепонок)
local FINGERS = {}
for i = 1, 4 do
	FINGERS["Finger" .. i .. "L"], FINGERS["Finger" .. i .. "R"] = true, true
end
local AREA_REF = 150

for name, cfg in BossAura.Variants do
	print(("Вариант %s — %s"):format(name, cfg.title))
	local missing, onFace, active = {}, {}, 0
	for _, layer in cfg.layers do
		for _, part in layer.parts do
			local size = sizeOf(part)
			if not size then
				table.insert(missing, layer.name .. "/" .. part)
				continue
			end
			if (FREE[part] or FINGERS[part]) and layer.name ~= "Spark" then
				table.insert(onFace, layer.name .. "/" .. part)
			end
			local rate = layer.rate
			if layer.byArea then
				local area = size.X * size.Y + size.Y * size.Z + size.X * size.Z
				rate *= math.clamp(math.sqrt(area / AREA_REF), 0.45, 2.2)
			end
			active += rate * (layer.lifetime[1] + layer.lifetime[2]) / 2
		end
	end
	for _, orbit in cfg.orbits or {} do
		if not sizeOf(orbit.part) then
			table.insert(missing, "orbit/" .. orbit.part)
		end
		if FREE[orbit.part] or FINGERS[orbit.part] or (orbit.toward and FREE[orbit.toward]) then
			table.insert(onFace, "orbit/" .. orbit.part)
		end
		for _, layer in orbit.layers do
			active += (orbit.count or 1) * layer.rate * (layer.lifetime[1] + layer.lifetime[2]) / 2
		end
	end
	check(
		#missing == 0,
		("части слоёв есть у дракона (нет: %s)"):format(table.concat(missing, ", "))
	)
	check(
		#onFace == 0,
		("морда, корона, перепонки и скипетр не горят (горят: %s)"):format(
			table.concat(onFace, ", ")
		)
	)
	local scale = math.min(1, cfg.maxParticles / math.max(active, 1))
	local full = active * scale
	check(
		full <= cfg.maxParticles + 1e-6,
		("активных частиц при полной силе ≈ %.0f (бюджет %d)"):format(
			full,
			cfg.maxParticles
		)
	)
	local peak = BossAura.Volley.peak
	if cfg.bursts then
		peak = math.max(peak, cfg.bursts.wake.peak, cfg.bursts.attack.peak)
	end
	check(
		full * peak <= cfg.maxParticles * 1.8,
		("пик залпа и всплесков ≈ %.0f (×%.2f)"):format(full * peak, peak)
	)
	if cfg.ribbons or cfg.arcs then
		local bad, beams = {}, 0
		local function use(where: string, part: string)
			if not sizeOf(part) then
				table.insert(bad, where .. "/" .. part .. " (нет)")
			elseif FREE[part] then
				table.insert(bad, where .. "/" .. part)
			end
		end
		for _, spec in cfg.ribbons or {} do
			for _, chain in spec.chains or {} do
				for _, part in chain do
					use(spec.name, part)
				end
				beams += (spec.strands or 1) * (#chain - 1 + (if spec.tip then 1 else 0))
			end
			for _, ring in spec.rings or {} do
				use(spec.name, ring.part)
				if ring.toward then
					use(spec.name, ring.toward)
				end
				beams += ring.segments or 6
			end
		end
		if cfg.arcs then
			for _, part in cfg.arcs.parts do
				use("Arc", part)
				if FINGERS[part] then
					table.insert(bad, "Arc/" .. part .. " (разряд на перепонке)")
				end
			end
		end
		check(
			#bad == 0,
			("ленты и разряды не на морде, короне, скипетре и перепонках (%s)"):format(
				table.concat(bad, ", ")
			)
		)
		check(beams <= 90, ("лент (Beam) %d — не больше 90"):format(beams))
		check(cfg.arcs == nil or cfg.arcs.pool <= 6, "разрядов в пуле не больше 6")
		check(
			cfg.state ~= nil and cfg.state.Sleep >= 1 and cfg.state.Defeat == 0,
			"во сне полная сила, после поражения гаснет"
		)
	end
end

print("RoyalAura — основа «Вихрь» + лёгкий «Покров»")
do
	local royal, veil = BossAura.Variants.RoyalAura, BossAura.Variants.Veil
	local function layerOf(cfg: any, name: string): any
		for _, layer in cfg and cfg.layers or {} do
			if layer.name == name then
				return layer
			end
		end
		return nil
	end
	check(royal ~= nil, "вариант RoyalAura есть")
	local flames = {}
	for _, layer in royal and royal.layers or {} do
		if layer.name == "Flame" or layer.name == "Streak" or layer.name == "Smoke" then
			table.insert(flames, layer.name)
		end
	end
	check(#flames == 0, ("нет огненных слоёв C3 (есть: %s)"):format(table.concat(flames, ", ")))
	local light, full = layerOf(royal, "VeilLight"), layerOf(veil, "Veil")
	local function minTransparency(layer: any): number
		local m = 1
		for _, p in layer.transparency do
			m = math.min(m, p[2])
		end
		return m
	end
	check(
		light ~= nil and full ~= nil and light.rate <= full.rate * 0.5,
		("покров реже самостоятельного «Покрова» хотя бы вдвое (%.2f против %.2f)"):format(
			light and light.rate or -1,
			full and full.rate or -1
		)
	)
	check(
		light ~= nil and minTransparency(light) >= 0.6,
		("покров прозрачный: не плотнее 0.6 (%.2f)"):format(
			light and minTransparency(light) or -1
		)
	)
	local veilFree = {}
	for _, part in light and light.parts or {} do
		if FREE[part] or FINGERS[part] or string.find(part, "Wing", 1, true) or part == "Neck2" or part == "Neck3" then
			table.insert(veilFree, part)
		end
	end
	check(
		#veilFree == 0,
		("покров не на голове, шее у головы, крыльях и скипетре (есть: %s)"):format(
			table.concat(veilFree, ", ")
		)
	)
	check(
		royal ~= nil and royal.orbits ~= nil and #royal.orbits >= 3,
		"энергия идёт вокруг корпуса (орбиты ≥ 3)"
	)
	check(
		royal ~= nil
			and royal.volleyLayer ~= nil
			and (royal.volleyLayer.Swirl or 0) > 1
			and (royal.volleyLayer.Arc or 0) > 1,
		"в залп вихри и разряды усиливаются больше остального"
	)
	check(
		BossAura.Active == "RoyalAura",
		"RoyalAura — у настоящего босса (утверждена владельцем 2026-11-16)"
	)
	check(
		royal ~= nil and royal.state.Sleep >= 1 and royal.state.Combat >= 1 and royal.state.Defeat == 0,
		"RoyalAura: во сне и в бою полная сила, после поражения гаснет"
	)
	-- правка владельца 2026-11-16: прямо перед нагрудником розовое свечение слабее, остальная аура та же
	local chestRing, otherRings = nil, {}
	for _, ribbon in royal and royal.ribbons or {} do
		for _, ring in ribbon.rings or {} do
			if ring.part == "Body" and ring.toward == "Neck1" then
				chestRing = ring
			else
				table.insert(otherRings, ring)
			end
		end
	end
	local dimmed = 0
	for _, ring in otherRings do
		if (ring.brightness or 1) < 1 then
			dimmed += 1
		end
	end
	check(
		chestRing ~= nil and (chestRing.brightness or 1) <= 0.6 and dimmed == 0,
		("у нагрудника кольцо приглушено (%.2f), остальные кольца — полной силы (приглушённых: %d)"):format(
			chestRing and chestRing.brightness or 1,
			dimmed
		)
	)
	local chestOrbit, otherOrbit = nil, nil
	for _, orbit in royal and royal.orbits or {} do
		if orbit.part == "Body" and orbit.toward == "Neck1" then
			chestOrbit = orbit
		elseif not otherOrbit then
			otherOrbit = orbit
		end
	end
	local chestSwirl = chestOrbit and layerOf({ layers = chestOrbit.layers }, "OrbitSwirl")
	local fullSwirl = otherOrbit and layerOf({ layers = otherOrbit.layers }, "OrbitSwirl")
	check(
		chestSwirl ~= nil
			and fullSwirl ~= nil
			and chestSwirl.brightness < fullSwirl.brightness
			and chestSwirl.lightEmission < fullSwirl.lightEmission,
		"у нагрудника вихри орбиты тусклее, на остальных орбитах — прежние"
	)
	-- вихри корпуса — тот же слой «Swirl» (волна силы и залп те же), но за поверхностью и прозрачнее; на остальных
	-- частях вихри прежние, и корпус без вихрей не остался
	local torso, rest = nil, nil
	for _, layer in royal and royal.layers or {} do
		if layer.name == "Swirl" then
			if table.find(layer.parts, "Body") then
				torso = layer
			else
				rest = layer
			end
		end
	end
	check(
		torso ~= nil
			and rest ~= nil
			and table.find(torso.parts, "Body_2") ~= nil
			and table.find(rest.parts, "Body") == nil
			and (torso.zOffset or 0) <= -2
			and (rest.zOffset or 0) == 0
			and torso.brightness < rest.brightness
			and minTransparency(torso) > minTransparency(rest),
		"вихри корпуса — за поверхностью и прозрачнее (броня читается), на остальных частях — прежние"
	)
	for _, name in { "C3", "Vortex", "Veil", "RoyalAura" } do
		check(
			BossAura.Variants[name] ~= nil,
			name .. ": доступен для переключения атрибутом"
		)
	end
end

print("Настоящий босс")
local active = BossAura.Active
check(
	active == nil or BossAura.Variants[active] ~= nil,
	("Active = %s — есть такой вариант"):format(tostring(active))
)
for _, name in { "C2", "C3" } do
	local v = BossAura.Variants[name]
	check(v ~= nil and v.state.Sleep >= 0.8, name .. ": во сне сила ≥ 0.8 (мощная и во сне)")
	check(v ~= nil and v.state.Defeat == 0, name .. ": после поражения гаснет")
	check(v ~= nil and v.state.FallAsleep >= 0.8, name .. ": засыпание — снова полная база")
end
local c3 = BossAura.Variants.C3
check(
	c3 ~= nil and c3.state.Sleep >= 1,
	"C3: во сне — полная сила (замечания владельца)"
)

print(("Итог: %d проверок, ошибок %d"):format(passed + failed, failed))
process.exit(if failed > 0 then 1 else 0)

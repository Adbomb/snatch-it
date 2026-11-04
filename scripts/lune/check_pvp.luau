--!nocheck
-- Проверка PvP Судной ночи без Roblox Studio (D37, D46): урон и HP от силы (формула боя с боссом), фиксированная
-- частота ударов, выбор цели, Safe Zone, нокаут 15 с с неуязвимостью (нельзя «добить» лежачего), восстановление HP.
-- Запуск из корня репозитория: lune run scripts/lune/check_pvp.luau.

local process = require("@lune/process")

local Env = require("./env")

local Vector3 = Env.roblox.Vector3
local Battle = Env.Require("ReplicatedStorage.Shared.Config.Battle")
local GameConfig = Env.Require("ReplicatedStorage.Shared.Config.GameConfig")
local PvpRules = Env.Require("ServerScriptService.Server.Util.PvpRules")

local failed, passed = 0, 0
local function check(ok: boolean, message: string)
	print((if ok then "  ок   " else "  ОШИБКА ") .. message)
	if ok then
		passed += 1
	else
		failed += 1
	end
end

local P = Battle.Player
local cfg = GameConfig.Pvp

print("Урон, HP и частота (Config/Battle.Player):")
do
	check(PvpRules.Damage(P, 0, Battle.DamageSpread, 0) == P.BaseDamage, "при силе 0 урон базовый")
	check(
		PvpRules.Damage(P, 1000, Battle.DamageSpread, 0) > PvpRules.Damage(P, 10, Battle.DamageSpread, 0),
		"урон растёт с силой"
	)
	check(PvpRules.MaxHP(P, 1000) > PvpRules.MaxHP(P, 0), "HP растёт с силой")
	local lo = PvpRules.Damage(P, 50, Battle.DamageSpread, -1)
	local hi = PvpRules.Damage(P, 50, Battle.DamageSpread, 1)
	check(
		math.abs(hi / lo - (1 + Battle.DamageSpread) / (1 - Battle.DamageSpread)) < 1e-9,
		"разброс ± DamageSpread"
	)
	local weak, strong = PvpRules.NewFighter(1, 100), PvpRules.NewFighter(2, 100)
	local hitsWeak, hitsStrong = 0, 0
	for t = 0, 10, 0.05 do
		if PvpRules.CanSwing(weak, t, true, false, P.AttackInterval) == nil then
			weak.lastAttack = t
			hitsWeak += 1
		end
		if PvpRules.CanSwing(strong, t, true, false, P.AttackInterval) == nil then
			strong.lastAttack = t
			hitsStrong += 1
		end
	end
	check(
		hitsWeak == hitsStrong and hitsWeak == math.floor(10 / P.AttackInterval) + 1,
		"частота ударов одна и та же при любой силе"
	)
end

print("Запреты:")
do
	local f = PvpRules.NewFighter(1, 100)
	check(
		PvpRules.CanSwing(f, 0, false, false, P.AttackInterval) ~= nil,
		"не в Судную ночь — нельзя"
	)
	check(
		PvpRules.CanSwing(f, 0, true, true, P.AttackInterval) ~= nil,
		"у места появления — нельзя"
	)
	f.knockedUntil = 5
	check(PvpRules.CanSwing(f, 1, true, false, P.AttackInterval) ~= nil, "оглушённый не бьёт")
	f.knockedUntil = 0
	f.lastAttack = 10
	check(
		PvpRules.CanSwing(f, 10.5, true, false, P.AttackInterval) ~= nil,
		"перезарядка (повторный RemoteEvent)"
	)
	check(
		PvpRules.CanSwing(f, 10 + P.AttackInterval, true, false, P.AttackInterval) == nil,
		"после перезарядки можно"
	)
end

print("Выбор цели:")
do
	local me = Vector3.new(0, 0, 0)
	local look = Vector3.new(0, 0, -1)
	local function c(id, x, z, extra)
		local out = { id = id, position = Vector3.new(x, 0, z), knocked = false, safe = false, alive = true }
		for k, v in extra or {} do
			out[k] = v
		end
		return out
	end
	local pick = PvpRules.PickTarget(me, look, { c(1, 0, -5), c(2, 0, -3), c(3, 0, 3) }, cfg.Range, cfg.FrontDot)
	check(pick == 2, "ближайший впереди")
	check(
		PvpRules.PickTarget(me, look, { c(3, 0, 4) }, cfg.Range, cfg.FrontDot) == nil,
		"за спиной не бьём"
	)
	check(
		PvpRules.PickTarget(me, look, { c(4, 0, -(cfg.Range + 1)) }, cfg.Range, cfg.FrontDot) == nil,
		"дальше радиуса — мимо"
	)
	check(
		PvpRules.PickTarget(me, look, { c(5, 0, -2, { knocked = true }) }, cfg.Range, cfg.FrontDot) == nil,
		"лежачего не бьём"
	)
	check(
		PvpRules.PickTarget(me, look, { c(6, 0, -2, { safe = true }) }, cfg.Range, cfg.FrontDot) == nil,
		"в Safe Zone не бьём"
	)
	check(
		PvpRules.PickTarget(me, look, { c(7, 0, -2, { alive = false }) }, cfg.Range, cfg.FrontDot) == nil,
		"мёртвого не бьём"
	)
end

print("Нокаут D37: 15 с, неуязвим, встаёт с полным HP:")
do
	local t = PvpRules.NewFighter(1, 30)
	local dealt, ko = PvpRules.Hit(t, 20, 0, cfg.KnockSeconds)
	check(dealt == 20 and not ko and t.hp == 10, "удар снимает HP")
	dealt, ko = PvpRules.Hit(t, 25, 1, cfg.KnockSeconds)
	check(dealt == 10 and ko and t.hp == 0, "HP 0 — нокаут, урон не уходит в минус")
	check(PvpRules.IsKnocked(t, 1 + cfg.KnockSeconds - 0.01), "лежит 15 с")
	dealt, ko = PvpRules.Hit(t, 50, 5, cfg.KnockSeconds)
	check(
		dealt == 0 and not ko and t.knockedUntil == 1 + cfg.KnockSeconds,
		"лежачего не добить: таймер не продлевается"
	)
	check(not PvpRules.Recover(t, 10), "раньше 15 с не встаёт")
	check(PvpRules.Recover(t, 1 + cfg.KnockSeconds) and t.hp == t.maxHp, "встал с полным HP")
	check(cfg.KnockSeconds == 15, "15 с — число D37")
end

print(("Проверок: %d, не прошло: %d"):format(passed + failed, failed))
if failed > 0 then
	process.exit(1)
end
print("Все проверки PvP прошли")

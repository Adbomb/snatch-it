--!strict
-- Правила PvP Судной ночи (D37, D46) без Instance — проверяются в Lune (scripts/lune/check_pvp.luau): урон и HP от
-- силы (та же формула, что у игрока в бою с боссом, Config/Battle.Player), фиксированная частота ударов, выбор цели
-- (ближайший соперник впереди в радиусе удара), запреты (не Судная ночь, Safe Zone у места появления, оглушён,
-- перезарядка), нокаут: 15 с лежит, неуязвим, потом HP полный. Живые объекты — в Services/PvpService.
-- Зависит только от переданных конфигов (Battle.Player, GameConfig.Pvp).

local PvpRules = {}

export type Fighter = {
	id: number,
	hp: number,
	maxHp: number,
	lastAttack: number, -- os.clock последнего удара (-inf — не бил)
	knockedUntil: number, -- до какого момента лежит (0 — не оглушён)
}

export type Candidate = { id: number, position: Vector3, knocked: boolean, safe: boolean, alive: boolean }

-- Множитель силы: (1 + сила) ^ Growth.
function PvpRules.Power(player: any, strength: number): number
	return (1 + math.max(strength, 0)) ^ player.Growth
end

function PvpRules.MaxHP(player: any, strength: number): number
	return player.BaseHP * PvpRules.Power(player, strength)
end

-- Урон удара: базовый × множитель силы × (1 ± spread · roll), roll ∈ [-1, 1].
function PvpRules.Damage(player: any, strength: number, spread: number, roll: number): number
	return player.BaseDamage * PvpRules.Power(player, strength) * (1 + spread * math.clamp(roll, -1, 1))
end

function PvpRules.NewFighter(id: number, maxHp: number): Fighter
	return { id = id, hp = maxHp, maxHp = maxHp, lastAttack = -math.huge, knockedUntil = 0 }
end

function PvpRules.IsKnocked(f: Fighter, now: number): boolean
	return now < f.knockedUntil
end

-- Можно ли ударить сейчас (без цели): фаза, оглушение, Safe Zone, перезарядка. nil — можно.
function PvpRules.CanSwing(f: Fighter, now: number, phaseOpen: boolean, safe: boolean, interval: number): string?
	if not phaseOpen then
		return "PvP — только в Судную ночь"
	end
	if PvpRules.IsKnocked(f, now) then
		return "Вы оглушены"
	end
	if safe then
		return "У места появления драться нельзя"
	end
	if now - f.lastAttack < interval - 1e-6 then
		return "Перезарядка"
	end
	return nil
end

-- Цель удара: ближайший живой, не оглушённый, не в Safe Zone соперник в радиусе range и не за спиной
-- (cos угла между взглядом и направлением на цель ≥ frontDot). nil — некого бить.
function PvpRules.PickTarget(
	position: Vector3,
	look: Vector3,
	candidates: { Candidate },
	range: number,
	frontDot: number
): number?
	local best, bestDistance = nil, math.huge
	local flatLook = Vector3.new(look.X, 0, look.Z)
	flatLook = if flatLook.Magnitude > 1e-3 then flatLook.Unit else Vector3.new(0, 0, -1)
	for _, c in candidates do
		if c.alive and not c.knocked and not c.safe then
			local offset = c.position - position
			local distance = offset.Magnitude
			local flat = Vector3.new(offset.X, 0, offset.Z)
			local dot = if flat.Magnitude > 1e-3 then flat.Unit:Dot(flatLook) else 1
			if distance <= range and dot >= frontDot and distance < bestDistance then
				best, bestDistance = c.id, distance
			end
		end
	end
	return best
end

-- Удар по цели: HP уменьшается; оглушённую цель бить нельзя (неуязвима). Возвращает (нанесено, нокаут).
function PvpRules.Hit(target: Fighter, damage: number, now: number, knockSeconds: number): (number, boolean)
	if PvpRules.IsKnocked(target, now) or damage <= 0 then
		return 0, false
	end
	local dealt = math.min(damage, target.hp)
	target.hp -= dealt
	if target.hp <= 0 then
		target.hp = 0
		target.knockedUntil = now + knockSeconds
		return dealt, true
	end
	return dealt, false
end

-- Оглушение прошло: HP снова полный. true — встал.
function PvpRules.Recover(f: Fighter, now: number): boolean
	if f.knockedUntil > 0 and now >= f.knockedUntil then
		f.knockedUntil = 0
		f.hp = f.maxHp
		return true
	end
	return false
end

return PvpRules

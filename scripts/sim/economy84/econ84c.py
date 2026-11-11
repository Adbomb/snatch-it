"""Модель 84 ч, версия 3. Основа — «по дизайну» (10 уровней музея, до 20 мест). Отличия от версии 2:
1. Тренировка в подготовку и в Судную ночь — как в коде (GymService фазу не проверяет): Судная ночь 90 с — тренировка;
   в подготовку игрок тренируется и может ловить, покупка и расстановка защиты — DEF_TIME секунд без тренировки.
2. Экспонаты в подготовку и Судную ночь менять нельзя (GameTime.ExhibitLock): пойманное в подготовку ставится после ночи.
3. Защита — вариант Б (взлом ур. 7–10: 2B / 8B / 30B / 80B, ур. 1–6 — D37); у каждого игрока свой список устройств
   и бюджет в минутах дохода.
4. Порядок покупок (policy): greedy — что доступно; no_museum — уровни музея выше 4 не берёт (проверка «всё в гантели»).
Скорость тренировки, мощность гантелей и формула бонуса музея — как в коде, не меняются."""
import json
import math
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).parent
ns = {"__file__": str(HERE / "econ84.py")}
exec(compile((HERE / "econ84.py").read_text(encoding="utf-8").replace('if __name__ == "__main__":', "if False:"),
             "econ84", "exec"), ns)
R, BASE, BONUS, MULT, MPOWER, POWER = ns["R"], ns["BASE"], ns["BONUS"], ns["MULT"], ns["MPOWER"], ns["POWER"]
DAY, NIGHT, DOOM = ns["DAY"], ns["NIGHT"], ns["DOOM"]
AIM, FLIGHT, CAPTURE, MISS_REST, ESC_REST, FIGHT, PAUSE, SHOP = (ns[k] for k in (
    "AIM", "FLIGHT", "CAPTURE", "MISS_REST", "ESC_REST", "FIGHT", "PAUSE", "SHOP"))
TRIP, HACK, SHARE, DEF_EFFECT, TARGET_AT, WIN = (ns[k] for k in ("TRIP", "HACK", "SHARE", "DEF_EFFECT", "TARGET_AT", "WIN"))
tier, short, slots_of, sig2, nice, base_cfg = (ns[k] for k in ("tier", "short", "slots_of", "sig2", "nice", "base_cfg"))
HACK_B = HACK[:6] + [2e9, 8e9, 30e9, 80e9]  # вариант Б
PREP = 120  # подготовка: последние секунды 10-го дня
DEF_TIME = 30  # купить и расставить защиту (без тренировки)
MAX_DEVICES = 5
DB_AT = {4: 0.15, 5: 0.2, 6: 0.25, 7: 0.3, 8: 0.35, 9: 0.35}  # доля этапа L, на которой покупается гантель L
MUS_AT = 0.55  # доля этапа L, на которой покупается уровень музея L+1


class Sc:
    def __init__(self, name, hit, taken, kinds, loss, defense, budget, policy="greedy"):
        self.name, self.hit, self.taken, self.kinds, self.loss = name, hit, taken, kinds, loss
        self.defense, self.budget, self.policy = defense, budget, policy


TYP = Sc("обычный", 0.70, 0.25, {"Legendary": "Mega", "Secret": "Mega", "Epic": "Turbo"}, 0.30, ("Trap", "Laser"), 3)
SKL = Sc("опытный", 0.85, 0.10, {"Legendary": "Mega", "Secret": "Mega"}, 0.30, ("Door", "Trap", "Laser", "Robot"), 6)
UNL = Sc("неудачливый", 0.55, 0.45, {}, 0.35, ("Trap",), 2)
WORST = Sc("худший случай", 0.55, 0.60, {}, 1.0, (), 0)


def simulate3(cfg, sc, rng, stop_after=None, endgame_h=0.0, cap_h=400, hold=None, policy=None, train_doom=True):
    policy = policy or sc.policy
    mean, pool, boom, S_boss, DP, MP = cfg["mean"], cfg["pool"], cfg["boom"], cfg["S"], cfg["DP"], cfg["MP"]
    hack = cfg.get("hack", HACK_B)
    t, coins, S, db, ml, day, L = 0.0, 0.0, 0.0, 1, 1, 0, 1
    museum = [["Common", 1, pool[1]["Common"][0], True]]  # учебное Common босса 1 (не крадут)
    phases, buys, dooms = [], [], []

    def power():
        return min(3, sum(MPOWER[m[0]] for m in museum))

    def new_phase():
        inc0 = sum(m[2] for m in museum)
        return {"L": L, "start": t, "catch": 0.0, "train": 0.0, "wait": 0.0, "night": 0.0, "doomnight": 0.0,
                "defbuy": 0.0, "shop": 0.0, "lov": 0.0, "dbc": 0.0, "mus": 0.0, "def": 0.0, "lost": 0, "catches": 0,
                "fail_out": 0, "dooms": 0, "defended": 0, "devices": 0, "db_at": {}, "ml_at": {}, "db_inc": {},
                "ml_inc": {}, "S0": S, "arrive_income": inc0, "min_income": inc0, "max_wait": 0.0, "gain_by_db": {},
                "mp_time": 0.0, "train_time": 0.0, "cap_time": 0.0, "earned": 0.0, "coins0": coins, "ml0": ml,
                "mp0": power(), "db0": db}

    def close(cur):
        comp = {r: sum(1 for m in museum if m[0] == r) for r in R}
        cur.update({"time": t - cur["start"], "income": sum(m[2] for m in museum), "db": db, "ml": ml, "at": t,
                    "S": S, "coins": coins, "mp_end": power(), "slots": slots_of(ml), "filled": len(museum),
                    "comp": comp})
        phases.append(cur)

    cur = new_phase()
    end_t = None
    while True:
        inc = sum(m[2] for m in museum)
        mp = power()
        need = WIN * S_boss[L] if L < 10 else math.inf
        if hold is not None and L == hold[0]:
            need = math.inf
            if t - cur["start"] >= hold[1]:
                close(cur)
                return phases, buys, dooms
        reserve = 5 * boom[L]
        day_left = DAY

        def spend(dt, kind):
            nonlocal t, coins, day_left
            t += dt
            coins += inc * dt
            cur["earned"] += inc * dt
            day_left -= dt
            cur[kind] += dt

        def train(dt):
            nonlocal S
            gain = POWER[db - 1] * (1 + mp) * dt
            S += gain
            cur["gain_by_db"][db] = cur["gain_by_db"].get(db, 0.0) + gain
            cur["mp_time"] += mp * dt
            cur["train_time"] += dt
            if mp >= 3:
                cur["cap_time"] += dt

        while policy == "museum_first" and ml < 10 and MP[ml + 1] and coins - MP[ml + 1] >= reserve:
            coins -= MP[ml + 1]
            cur["mus"] += MP[ml + 1]
            ml += 1
            cur["ml_at"][ml] = t - cur["start"]
            cur["ml_inc"][ml] = inc
            spend(SHOP, "shop")
            buys.append((t, "музей", ml))
        while db < 10 and DP[db + 1] and coins - DP[db + 1] >= reserve:
            coins -= DP[db + 1]
            cur["dbc"] += DP[db + 1]
            db += 1
            cur["db_at"][db] = t - cur["start"]
            cur["db_inc"][db] = inc
            spend(SHOP, "shop")
            buys.append((t, "гантель", db))
        while ml < 10 and MP[ml + 1] and coins - MP[ml + 1] >= reserve and not (policy == "no_museum" and ml >= 4):
            coins -= MP[ml + 1]
            cur["mus"] += MP[ml + 1]
            ml += 1
            cur["ml_at"][ml] = t - cur["start"]
            cur["ml_inc"][ml] = inc
            spend(SHOP, "shop")
            buys.append((t, "музей", ml))
        cap = slots_of(ml)
        doom_day = day % 10 == 9
        reserved = DEF_TIME if (doom_day and sc.defense) else 0
        floor = mean[L]["Common"]
        pending = []  # пойманное в подготовку: на постамент — после Судной ночи

        def place(item):
            if len(museum) >= cap:
                museum.remove(min(museum, key=lambda m: m[2]))
            museum.append(item)

        spawns = []
        for _ in range(4):
            r = rng.choices(R, weights=[tier(L)[x] for x in R])[0]
            if rng.random() >= sc.taken:
                spawns.append((r, rng.choice(pool[L][r])))
        spawns.sort(key=lambda p: -p[1])
        at_boss = False
        half = TRIP[L] / 2
        for r, income in spawns:
            if day_left < reserved + TRIP[L] + FIGHT + 20:
                break
            held_now = museum + pending
            worst = min(m[2] for m in held_now) if len(held_now) >= cap else -1
            good = len(held_now) >= cap and all(m[2] >= floor for m in held_now)
            if income <= worst or (good and income < 1.05 * worst):
                continue
            kind = sc.kinds.get(r, "Boom")
            cost = boom[L] * MULT[kind]
            caught, tries = False, 0
            while not caught and day_left > reserved + TRIP[L] + FIGHT + 15 and tries < 6:
                if coins < cost:
                    wait = (cost - coins) / max(inc, 1e-9)
                    if wait > day_left - reserved - 30 - (half if at_boss else 0):
                        break
                    if at_boss:  # за деньгами — домой, на тренировку
                        spend(half, "catch")
                        at_boss = False
                    spend(wait, "wait")
                    train(wait)
                    cur["max_wait"] = max(cur["max_wait"], wait)
                    if day_left <= reserved + TRIP[L] + FIGHT + 15:
                        break
                if not at_boss:
                    spend(half, "catch")
                    at_boss = True
                tries += 1
                for _ in range(3):
                    if coins < cost:
                        break
                    coins -= cost
                    cur["lov"] += cost
                    hit = rng.random() < sc.hit
                    dt = AIM + FLIGHT + (CAPTURE if hit else MISS_REST)
                    if hit and rng.random() < min(1, BASE[r] * BONUS[kind]):
                        caught = True
                    elif hit:
                        dt += ESC_REST
                    spend(dt, "catch")
                    if caught:
                        break
                if not caught:
                    spend(PAUSE, "catch")
                    if rng.random() < sc.taken * 0.5:
                        break
            if caught:
                spend(FIGHT + half, "catch")
                at_boss = False
                cur["catches"] += 1
                item = [r, L, income, False]
                if doom_day and day_left <= PREP:
                    pending.append(item)  # подготовка: экспонаты менять нельзя
                else:
                    place(item)
                    inc = sum(m[2] for m in museum)
                    mp = power()
        if at_boss:  # вылазка без добычи: дорога домой
            spend(half, "catch")
            cur["fail_out"] += 1
        rest = max(0.0, day_left)
        if doom_day:
            allowed = sc.defense[:min(ml, MAX_DEVICES)]
            bought, price = 0, 0.0
            for k in range(len(allowed), 0, -1):
                p = sum(SHARE[d] for d in allowed[:k]) * hack[ml - 1]
                if p <= sc.budget * 60 * max(inc, 1) and coins - p >= reserve:
                    bought, price = k, p
                    break
            if bought:
                coins -= price
                cur["def"] += price
                cur["defended"] += 1
                cur["devices"] += bought
                dt = min(DEF_TIME, rest)
                spend(dt, "defbuy")
                rest -= dt
            spend(rest, "train")
            train(rest)
            cur["dooms"] += 1
            dooms.append((ml, L, inc, max(m[2] for m in museum), bought, price))
            t += DOOM
            coins += inc * DOOM
            cur["earned"] += inc * DOOM
            cur["doomnight"] += DOOM
            if train_doom:
                train(DOOM)  # в Судную ночь игрок в своей качалке (GymService фазу не проверяет)
            can = [m for m in museum if not m[3]]
            if can and rng.random() < sc.loss * (1 - DEF_EFFECT[bought]):
                victim = max(can, key=lambda m: m[2]) if rng.random() < 0.6 else rng.choice(can)
                museum.remove(victim)
                cur["lost"] += 1
                cur["min_income"] = min(cur["min_income"], sum(m[2] for m in museum))
            for item in pending:
                place(item)
        else:
            spend(rest, "train")
            train(rest)
            t += NIGHT  # ночью коридор закрыт — тренировка
            coins += inc * NIGHT
            cur["earned"] += inc * NIGHT
            cur["night"] += NIGHT
            train(NIGHT)
        day += 1
        if L < 10 and S >= need:
            close(cur)
            if stop_after is not None and L >= stop_after:
                return phases, buys, dooms
            L += 1
            cur = new_phase()
            if L == 10:
                end_t = t
        if (L == 10 and t - end_t >= endgame_h * 3600) or t > cap_h * 3600:
            close(cur)
            return phases, buys, dooms


def load(name):
    raw = json.load(open(HERE / name))
    cfg = base_cfg()
    cfg["S"], cfg["DP"], cfg["MP"] = raw["S"], raw["DP"], raw["MP"]
    cfg["boom"] = {int(k): v for k, v in raw["boom"].items()}
    cfg["hack"] = raw.get("hack", HACK_B)
    return cfg


def save(cfg, name):
    keep = {k: cfg[k] for k in ("S", "DP", "MP", "hack")}
    keep["boom"] = {str(k): v for k, v in cfg["boom"].items()}
    json.dump(keep, open(HERE / name, "w"))


def done(ph, L, cfg):
    return len(ph) >= L and ph[L - 1]["L"] == L and ph[L - 1]["S"] >= WIN * cfg["S"][L]


def arrival(cfg, L, n, seed):
    """Медиана времени прихода к боссу L+1 (обычный игрок), секунд."""
    rng = random.Random(seed)
    ats = []
    for _ in range(n):
        ph, _, _ = simulate3(cfg, TYP, rng, stop_after=L, cap_h=600)
        ats.append(ph[L - 1]["at"] if done(ph, L, cfg) else math.inf)
    return statistics.median(ats)


def buy_time(cfg, L, key, kind, level, target, n, seed):
    """Медиана момента покупки (гантели / уровня музея) от начала этапа L; этап держится target секунд."""
    rng = random.Random(seed)
    offs = []
    for _ in range(n):
        ph, buys, _ = simulate3(cfg, TYP, rng, hold=(L, target))
        if len(ph) < L:
            continue
        p = ph[L - 1]
        x = math.inf
        for tt, k, lv in buys:
            if k == kind and lv == level:
                x = -1.0 if tt < p["start"] else tt - p["start"]
                break
        offs.append(x)
    return statistics.median(offs)


def bisect_price(cfg, key, kind, level, L, want, target, n, seed, iters=10):
    lo, hi = math.log(max(cfg[key][level], 1) / 30), math.log(max(cfg[key][level], 1) * 30)
    for _ in range(iters):
        mid = (lo + hi) / 2
        cfg[key][level] = math.exp(mid)
        if buy_time(cfg, L, key, kind, level, target, n, seed) < want:
            lo = mid  # покупают раньше нужного — дороже
        else:
            hi = mid
    cfg[key][level] = sig2(math.exp((lo + hi) / 2))


def fit_boss(cfg, L, n, seed, iters=10):
    target = TARGET_AT[L + 1] * 3600
    lo, hi = math.log(cfg["S"][L] / 4), math.log(cfg["S"][L] * 4)
    for _ in range(iters):
        mid = (lo + hi) / 2
        cfg["S"][L] = math.exp(mid)
        if arrival(cfg, L, n, seed) < target:
            lo = mid
        else:
            hi = mid
    cfg["S"][L] = sig2(math.exp((lo + hi) / 2))


def calibrate3(start="econ84b_design.json", n=40, seed=100, log=print):
    cfg = load(start)
    cfg["hack"] = list(HACK_B)
    for L in range(3, 10):
        target = (TARGET_AT[L + 1] - TARGET_AT[L]) * 3600
        for rep in range(3):
            if L >= 4:
                bisect_price(cfg, "DP", "гантель", L, L, DB_AT[L] * target, target, n, seed + 7 * rep)
            bisect_price(cfg, "MP", "музей", L + 1, L, MUS_AT * target, target, n, seed + 7 * rep + 3)
        fit_boss(cfg, L, 100, seed + 500)
        rng = random.Random(seed + 900)
        arr = []
        for _ in range(120):
            ph, _, _ = simulate3(cfg, TYP, rng, stop_after=L, cap_h=600)
            if done(ph, L, cfg):
                arr.append(ph[L - 1]["income"])
        inc = statistics.median(arr)
        ratio = cfg["boom"][L + 1] / (60 * inc)
        note = ""
        if not 0.7 <= ratio <= 1.4:
            cfg["boom"][L + 1] = nice(60 * inc)
            note = f" → Бум {L + 1} = {short(cfg['boom'][L + 1])}"
        log(f"этап {L}: гантель {L} {short(cfg['DP'][L])}, музей {L + 1} {short(cfg['MP'][L + 1])}, босс {L + 1} "
            f"{short(cfg['S'][L])}, приход {arrival(cfg, L, 200, seed + 950) / 3600:.2f} ч (цель {TARGET_AT[L + 1]}); "
            f"Бум {L + 1} = {ratio:.2f} мин дохода{note}")
    rng = random.Random(seed + 990)
    arr = [simulate3(cfg, TYP, rng, stop_after=9, cap_h=600)[0] for _ in range(100)]
    inc = statistics.median([p[8]["income"] for p in arr if done(p, 9, cfg)])
    cfg["DP"][10] = sig2(max(1.5 * cfg["DP"][9], 12 * 3600 * inc))  # цель после босса 10
    return cfg


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = calibrate3()
    save(cfg, "calibrated_variant_b.json")
    print(json.dumps({k: cfg[k] for k in ("S", "DP", "MP")} | {"boom": cfg["boom"]}))

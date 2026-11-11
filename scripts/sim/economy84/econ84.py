"""Экономика D55 по уточнённым требованиям (только расчёт): 2 ч игры в день; боссы 1–7 за 14 ч, босс 8 — 28 ч,
9 — 56 ч, 10 — 84 ч. Сила — только тренировкой (гантель × (1 + сила музея)), бои силу не дают, скорость тренировки и
множители не меняются. Гантели и уровни музея покупаются по мере денег (как в игре — только за монеты, по порядку).
Калибруются: сила боссов 4–10, цены гантелей 4–10, уровней музея 4–10, Бум 4–10 (правило D55: ≈ 1 мин дохода новичка).
Утверждённое не трогается: шансы, множители, цены Ловибумов 1–3, правила музея и Судной ночи, боссы 1–3."""
import json
import math
import random
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ITEMS = (ROOT / "src/shared/Config/Items.luau").read_text(encoding="utf-8")
R = ["Common", "Rare", "Epic", "Legendary", "Secret"]
BASE = {"Common": 0.6, "Rare": 0.35, "Epic": 0.3, "Legendary": 0.14, "Secret": 0.06}
BONUS = {"Boom": 1, "Turbo": 1.5, "Mega": 2}
MULT = {"Boom": 1, "Turbo": 2, "Mega": 3}
TIERS = [(1, 3, {"Common": 70, "Rare": 25, "Epic": 5, "Legendary": 0, "Secret": 0}),
         (4, 7, {"Common": 52, "Rare": 30, "Epic": 13, "Legendary": 5, "Secret": 0}),
         (8, 10, {"Common": 32.5, "Rare": 35, "Epic": 20, "Legendary": 11.25, "Secret": 1.25})]
MPOWER = {"Common": 0.01, "Rare": 0.05, "Epic": 0.08, "Legendary": 0.12, "Secret": 0.3}  # Progression.MuseumPower
POWER = [1, 6, 36, 210, 1200, 7700, 46000, 270000, 1.6e6, 10e6]  # Progression.Dumbbell.Power — не меняем
DAY, NIGHT, DOOM = 300, 30, 90
AIM, FLIGHT, CAPTURE, MISS_REST, ESC_REST, FIGHT, PAUSE, SHOP = 2.5, 0.6, 2.9, 0.6, 0.5, 18, 10, 6
TRIP = {L: 25 + 12.5 * (L - 1) for L in range(1, 11)}
HACK = [1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 1e11, 1e12]  # D37
SHARE = {"Trap": 0.10, "Laser": 0.15, "Door": 0.20, "Robot": 0.30}
DEF_EFFECT = {0: 0.0, 1: 0.35, 2: 0.55, 3: 0.65, 4: 0.75}
NICE = (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10)
TARGET_AT = {2: 0.25, 3: 0.6, 4: 2.0, 5: 4.5, 6: 8.5, 7: 14.0, 8: 28.0, 9: 56.0, 10: 84.0}
WIN = 0.8  # победа при силе ≥ 0.8 × силы босса (формула Battle: ≈ 0.72, с запасом на разброс урона)


def tier(L):
    return next(ch for a, b, ch in TIERS if a <= L <= b)


def nice(x):
    if x <= 0:
        return 0
    k = 10 ** int(math.floor(math.log10(x)))
    return min((n * k for n in NICE), key=lambda v: abs(math.log(v / x)))


def short(n):
    for div, suf in ((1e18, "Qi"), (1e15, "Qa"), (1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            return f"{n / div:.2f}".rstrip("0").rstrip(".") + suf
    return f"{n:.0f}"


def slots_of(level):  # GameConfig.Museum: max(6, 2 × уровень), не больше 20 — правило не меняем
    return min(20, max(6, 2 * level))


def incomes(step=3.2, leg=3.0, sec=3.0, common_up=1.0):
    pool = {}
    for fn, boss in (("wonder", 1), ("find", 2)):
        for m in re.finditer(r"\n" + fn + r'\("(\w+)", "(\w+)", "[^"]*", "\w+", "\w+", (\d+(?:\.\d+)?)', ITEMS):
            pool.setdefault(boss, {}).setdefault(m.group(2), []).append(float(m.group(3)))
    for m in re.finditer(r'\ncreature\("(\w+)", "(\w+)", "[^"]*", "\w+", (\d+(?:\.\d+)?)', ITEMS):
        v = float(m.group(3))
        pool.setdefault(3, {}).setdefault(m.group(2), []).append(round(v * common_up) if m.group(2) == "Common" else v)
    mean = {L: {r: statistics.mean(v) for r, v in pool[L].items()} for L in (1, 2, 3)}
    for L in range(4, 11):
        mean[L] = {r: mean[L - 1][r] * step for r in ("Common", "Rare", "Epic")}
        mean[L]["Legendary"] = leg * mean[L]["Epic"]
        mean[L]["Secret"] = sec * mean[L]["Legendary"]
        pool[L] = {r: [mean[L][r] * f for f in (0.88, 0.94, 1.0, 1.06, 1.12)] for r in mean[L]}
    return mean, pool


class Scenario:
    def __init__(self, name, hit, taken, kinds, loss, defense, hours_day):
        self.name, self.hit, self.taken, self.kinds = name, hit, taken, kinds
        self.loss, self.defense, self.hours_day = loss, defense, hours_day


TYPICAL = Scenario("типичный", 0.70, 0.25, {"Legendary": "Mega", "Secret": "Mega", "Epic": "Turbo"}, 0.30,
                   ("Trap", "Laser"), 2.0)
SKILLED = Scenario("умелый", 0.85, 0.10, {"Legendary": "Mega", "Secret": "Mega"}, 0.30,
                   ("Trap", "Laser", "Door", "Robot"), 2.0)
UNLUCKY = Scenario("неудачливый", 0.55, 0.45, {}, 0.35, ("Trap",), 2.0)


def simulate(cfg, sc, rng, stop_after=None, endgame_h=0.0, cap_h=300, hold=None):
    mean, pool, boom, S_boss, DP, MP = cfg["mean"], cfg["pool"], cfg["boom"], cfg["S"], cfg["DP"], cfg["MP"]
    t, coins, S, db, ml, day, L = 0.0, 0.0, 0.0, 1, 1, 0, 1
    museum = [["Common", 1, pool[1]["Common"][0]]]  # учебное Common босса 1
    phases, buys = [], []

    def new_phase():
        return {"L": L, "start": t, "catch": 0.0, "train": 0.0, "night": 0.0, "doom": 0.0, "shop": 0.0,
                "lov": 0.0, "dbc": 0.0, "mus": 0.0, "def": 0.0, "lost": 0, "catches": 0, "S0": S,
                "arrive_income": sum(m[2] for m in museum), "gain_by_db": {}, "mp_time": 0.0, "train_time": 0.0,
                "db_at": {}, "ml_at": {}, "db0": db, "ml0": ml}

    cur = new_phase()
    end_t = None
    while True:
        inc = sum(m[2] for m in museum)
        mp = min(3, sum(MPOWER[m[0]] for m in museum))
        need = WIN * S_boss[L] if L < 10 else math.inf
        if hold is not None and L == hold[0]:
            need = math.inf
            if t - cur["start"] >= hold[1]:
                cur.update({"time": t - cur["start"], "income": sum(m[2] for m in museum), "db": db, "ml": ml,
                            "at": t, "S": S, "coins": coins, "mp_end": min(3, sum(MPOWER[m[0]] for m in museum))})
                phases.append(cur)
                return phases, buys
        reserve = 5 * boom[L]
        day_left = DAY

        def spend(dt, kind):
            nonlocal t, coins, day_left
            t += dt
            coins += inc * dt
            day_left -= dt
            cur[kind] += dt

        def train(dt):
            nonlocal S
            gain = POWER[db - 1] * (1 + mp) * dt
            S += gain
            cur["gain_by_db"][db] = cur["gain_by_db"].get(db, 0.0) + gain
            cur["mp_time"] += mp * dt
            cur["train_time"] += dt

        # покупки (как в игре: по порядку, за монеты; игрок покупает, как только хватает с запасом на Ловибумы)
        while db < 10 and DP[db + 1] and coins - DP[db + 1] >= reserve:
            coins -= DP[db + 1]
            cur["dbc"] += DP[db + 1]
            db += 1
            cur["db_at"][db] = t - cur["start"]
            spend(SHOP, "shop")
            buys.append((t, "гантель", db))
        while ml < 10 and MP[ml + 1] and coins - MP[ml + 1] >= reserve:
            coins -= MP[ml + 1]
            cur["mus"] += MP[ml + 1]
            ml += 1
            cur["ml_at"][ml] = t - cur["start"]
            spend(SHOP, "shop")
            buys.append((t, "музей", ml))
        cap = slots_of(ml)
        doom_day = day % 10 == 9
        reserved = 60 if doom_day else 0
        floor = mean[L]["Common"]
        spawns = []
        for _ in range(4):
            r = rng.choices(R, weights=[tier(L)[x] for x in R])[0]
            if rng.random() >= sc.taken:
                spawns.append((r, rng.choice(pool[L][r])))
        spawns.sort(key=lambda p: -p[1])
        for r, income in spawns:
            if day_left < reserved + TRIP[L] + FIGHT + 20:
                break
            worst = min(m[2] for m in museum) if len(museum) >= cap else -1
            good = len(museum) >= cap and all(m[2] >= floor for m in museum)
            if income <= worst or (good and income < 1.05 * worst):
                continue
            kind = sc.kinds.get(r, "Boom")
            cost = boom[L] * MULT[kind]
            caught, tries = False, 0
            while not caught and day_left > reserved + TRIP[L] + FIGHT + 15 and tries < 6:
                if coins < cost:
                    wait = (cost - coins) / max(inc, 1e-9)
                    if wait > day_left - reserved - 30:
                        break
                    spend(wait, "train")
                    train(wait)
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
                spend(FIGHT + TRIP[L], "catch")
                cur["catches"] += 1
                if len(museum) >= cap:
                    museum.remove(min(museum, key=lambda m: m[2]))
                museum.append([r, L, income])
                inc = sum(m[2] for m in museum)
                mp = min(3, sum(MPOWER[m[0]] for m in museum))
        rest = max(0.0, day_left)
        if doom_day:
            part = max(0.0, rest - 60)
            spend(part, "train")
            train(part)
            price = sum(SHARE[d] for d in sc.defense) * HACK[ml - 1]
            bought = 0
            if price <= 3 * 60 * max(inc, 1) and coins - price >= reserve:
                coins -= price
                cur["def"] += price
                bought = len(sc.defense)
            spend(min(60.0, max(0.0, day_left)), "doom")
            t += DOOM
            coins += inc * DOOM
            cur["doom"] += DOOM
            if len(museum) > 1 and rng.random() < sc.loss * (1 - DEF_EFFECT[bought]):
                victim = max(museum, key=lambda m: m[2]) if rng.random() < 0.6 else rng.choice(museum)
                museum.remove(victim)
                cur["lost"] += 1
        else:
            spend(rest, "train")
            train(rest)
            t += NIGHT  # ночью коридор закрыт — тренировка
            coins += inc * NIGHT
            cur["night"] += NIGHT
            train(NIGHT)
        day += 1
        if L < 10 and S >= need:
            cur.update({"time": t - cur["start"], "income": sum(m[2] for m in museum), "db": db, "ml": ml,
                        "at": t, "S": S, "coins": coins, "mp_end": min(3, sum(MPOWER[m[0]] for m in museum))})
            phases.append(cur)
            if stop_after is not None and L >= stop_after:
                return phases, buys
            L += 1
            cur = new_phase()
            if L == 10:
                end_t = t
        if (L == 10 and t - end_t >= endgame_h * 3600) or t > cap_h * 3600:
            cur.update({"time": t - cur["start"], "income": sum(m[2] for m in museum), "db": db, "ml": ml, "at": t,
                        "S": S, "coins": coins, "mp_end": min(3, sum(MPOWER[m[0]] for m in museum))})
            phases.append(cur)
            return phases, buys


def base_cfg():
    mean, pool = incomes()
    return {"mean": mean, "pool": pool,
            "S": [None, 140, 1100, 0, 0, 0, 0, 0, 0, 0, 0],  # S[L] — сила босса L+1; 2 и 3 — как в игре
            "DP": [None, None, 37e3, 520e3, 0, 0, 0, 0, 0, 0, 0],  # DP[d] — цена гантели d; 2 и 3 — как в игре
            "MP": [None, None, 10e3, 100e3, 0, 0, 0, 0, 0, 0, 0],  # MP[m] — цена уровня музея m; 2 и 3 — D37
            "boom": {1: 1000, 2: 10000, 3: 30000}}


def run_until(cfg, sc, phase, n, seed, with_buys=False):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        ph, buys = simulate(cfg, sc, rng, stop_after=phase)
        if len(ph) >= phase:
            out.append((ph[phase - 1], buys) if with_buys else ph[phase - 1])
    return out


def sig2(x):
    """Две значащие цифры (точнее «красивых» чисел: сила и цены задают время этапов)."""
    if x <= 0:
        return 0
    e = 10 ** (math.floor(math.log10(x)) - 1)
    return round(x / e) * e


def buy_offset(p, buys, kind, level):
    """Время покупки (гантели / уровня музея) от начала этапа: < 0 — купили раньше этапа, None — не купили."""
    for t, k, lv in buys:
        if k == kind and lv == level:
            return t - p["start"] if t <= p["start"] + p["time"] else None
    return None


DB_AT = {4: 0.15, 5: 0.2, 6: 0.25, 7: 0.3, 8: 0.35, 9: 0.35}  # когда в этапе L покупается гантель L (доля этапа)
MUS_AT = 0.55  # когда в этапе L покупается уровень музея L+1


def held(cfg, L, target, n, seed):
    """Этап L без конца (сила босса недостижима) на время target: покупки этапа — как в игре."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        ph, buys = simulate(cfg, TYPICAL, rng, hold=(L, target))
        if len(ph) >= L:
            out.append((ph[L - 1], buys))
    return out


def bisect_price(cfg, key, level, kind, L, want, target, n, seed, iters=9):
    """Цена, при которой покупка (гантели / уровня музея) в этапе L приходится на want секунд от начала (медиана)."""
    lo, hi = math.log(max(cfg[key][level], 1) / 200), math.log(max(cfg[key][level], 1) * 200)
    for _ in range(iters):
        mid = (lo + hi) / 2
        cfg[key][level] = math.exp(mid)
        res = held(cfg, L, target, n, seed)
        offs = []
        for p, b in res:
            x = buy_offset(p, b, kind, level)
            offs.append(-1.0 if x is not None and x < 0 else (math.inf if x is None else x))
        m = statistics.median(offs)
        if m < want:
            lo = mid  # покупают раньше — дороже
        else:
            hi = mid
    cfg[key][level] = sig2(math.exp((lo + hi) / 2))


def fit_strength(cfg, L, target, n, seed, iters=6):
    for it in range(iters):
        ph = run_until(cfg, TYPICAL, L, n, seed + it)
        T = statistics.median([p["time"] for p in ph])
        cfg["S"][L] *= max(0.3, min(3.0, target / T))
    cfg["S"][L] = sig2(cfg["S"][L])
    return T


def calibrate(n=28, seed=100, log=print):
    cfg = base_cfg()
    for L in range(4, 11):
        cfg["boom"][L] = 0
    mean = cfg["mean"]
    for L in range(3, 10):
        ref = slots_of(L + 1) * sum(tier(L)[r] / 100 * mean[L].get(r, 0) for r in R) * 1.5
        ph = (TARGET_AT[L + 1] - TARGET_AT[L]) * 3600
        cfg["S"][L] = 0.6 * ph * POWER[L - 1] * 1.8 / WIN
        if L >= 4:
            cfg["DP"][L] = DB_AT[L] * ph * ref * 0.6
        cfg["MP"][L + 1] = MUS_AT * ph * ref * 0.4
    saved_dp, saved_mp = list(cfg["DP"]), list(cfg["MP"])
    for L in range(3, 10):
        # покупки позже этапа L пока выключены
        for d in range(L + 1, 11):
            cfg["DP"][d] = 0
        for m in range(L + 2, 11):
            cfg["MP"][m] = 0
        if L >= 4:
            arrive = statistics.median([p["income"] for p in run_until(cfg, TYPICAL, L - 1, n, seed)])
            cfg["boom"][L] = nice(60 * arrive)
        target = (TARGET_AT[L + 1] - TARGET_AT[L]) * 3600
        for rep in range(2):
            if L >= 4:
                cfg["DP"][L] = cfg["DP"][L] or saved_dp[L]
                bisect_price(cfg, "DP", L, "гантель", L, DB_AT[L] * target, target, n, seed + 10 * rep)
            cfg["MP"][L + 1] = cfg["MP"][L + 1] or saved_mp[L + 1]
            bisect_price(cfg, "MP", L + 1, "музей", L, MUS_AT * target, target, n, seed + 10 * rep + 5)
        T = fit_strength(cfg, L, target, n, seed)
        log(f"этап {L}: гантель {short(cfg['DP'][L] or 0)}, музей {short(cfg['MP'][L + 1])}, сила {short(cfg['S'][L])}, "
            f"{T / 3600:.2f} ч (цель {target / 3600:.2f})")
        if L < 9:
            cfg["DP"][L + 1] = saved_dp[L + 1]
    arrive = statistics.median([p["income"] for p in run_until(cfg, TYPICAL, 9, n, seed)])
    cfg["boom"][10] = nice(60 * arrive)
    cfg["DP"][10] = sig2(max(1.5 * cfg["DP"][9], 12 * 3600 * arrive))  # цель после босса 10
    # итог: все цены включены — ещё раз сила каждого этапа по порядку
    for L in range(3, 10):
        target = (TARGET_AT[L + 1] - TARGET_AT[L]) * 3600
        T = fit_strength(cfg, L, target, n, seed + 50, iters=4)
        log(f"итог этап {L}: сила {short(cfg['S'][L])}, {T / 3600:.2f} ч (цель {target / 3600:.2f})")
    return cfg


def save(cfg, name="econ84_cfg.json"):
    keep = {k: cfg[k] for k in ("S", "DP", "MP")}
    keep["boom"] = {str(k): v for k, v in cfg["boom"].items()}
    json.dump(keep, open(Path(__file__).with_name(name), "w"))


def load(name="econ84_cfg.json"):
    raw = json.load(open(Path(__file__).with_name(name)))
    cfg = base_cfg()
    cfg["S"], cfg["DP"], cfg["MP"] = raw["S"], raw["DP"], raw["MP"]
    cfg["boom"] = {int(k): v for k, v in raw["boom"].items()}
    return cfg


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = calibrate()
    save(cfg)
    print(json.dumps({k: cfg[k] for k in ("S", "DP", "MP")} | {"boom": cfg["boom"]}))

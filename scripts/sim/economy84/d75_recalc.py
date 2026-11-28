"""Экономика D75 «бросок вдаль»: калибровка дохода наград по зонам под цели D56 (зоны 7 / 8 / 9 / 10 — на 14 / 28 /
56 / 84 ч у обычного игрока). Цены Ловибумов (набор из 3, D61), пороги силы (D56), редкость этажа (D74) — утверждённые.
Правила D75 (решения владельца 2026-11-28 и ответы на план):
  1. Видимых существ нет: бросок с площадки = розыгрыш (существо набора зоны по шансам D37, редкость этажа D74),
     поимка не срывается, дороги в зону нет.
  2. Дальность, м = 10 × (1 + сила)^0.25 × точность (1 … 1.18) × вид (Бум 1, Турбо 1.06, Мега 1.12); отметка зоны N —
     та же формула при силе босса N; Ловибум уровня N дальше конца зоны N не летит.
  3. Удача по глубине: f — доля пути между отметками зоны приземления; удача = 1 + f; вес каждой следующей ступени
     редкости существа и этажа умножается на удача^0.5. Вид Ловибума — «охота»: веса верхних редкостей существ
     (Legendary, Secret) и этажей (Мифический, Алмазный) умножаются на KIND_HUNT (Бум — фарм, Турбо и Мега — охота).
  4. Башня: мест — как у музея по уровню (до 20), только лучшие этажи; двух одинаковых этажей (то же существо и та же
     редкость этажа) быть не может — повтор продаётся.
  5. Ненужная капсула продаётся: доход этажа × SELL_S секунд.
  6. Босс зоны: 1 из 2 500 с броска; на крыше один (лучший), доход = Легендарное существо на Золотом этаже своей зоны.
  7. Калибровка: доход наград зоны N × K[N]; K подбирается по зонам, цены не меняются.
Игрок бросает, пока ожидаемая прибавка дохода башни за HORIZON секунд (плюс выручка от продажи) окупает бросок.

Запуск: python scripts/sim/economy84/d75_recalc.py [число прогонов, по умолчанию 60] > report_d75.md
"""

import bisect
import json
import math
import random
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
PER_BUY = 3  # Config/Catch.PerBuy (D61)
CUTSCENE = 14  # D74: катсцена и прокрутка, с

FLOORS = ["Деревянный", "Каменный", "Мраморный", "Золотой", "Мифический", "Алмазный"]
FLOOR_CHANCE = [60, 25, 10, 4, 0.9, 0.1]
FLOOR_MULT = [1, 2, 4, 8, 20, 60]
SHIFT = {"Common": 1.0, "Rare": 1.15, "Epic": 1.3, "Legendary": 1.5, "Secret": 1.8}
GOLD = 3  # индекс Золотого этажа

METRE_K, METRE_P = 10, 0.25
END_MARK = 15000  # конец трассы, м: самый дальний бросок в игре
ACC_MAX = 0.18
KIND_RANGE = {"Boom": 1.0, "Turbo": 1.06, "Mega": 1.12}
# Охота: множители весов (Legendary и Secret существа, Мифический и Алмазный этажи). Турбо стоит 2 Бума, Мега — 3.
KIND_HUNT = {"Boom": (1.0, 1.0), "Turbo": (1.4, 2.5), "Mega": (1.75, 3.6)}
KINDS = ["Boom", "Turbo", "Mega"]
# Какими видами бросает игрок (доля покупок): фарм Бумом, охота — иногда.
MIX = {"обычный": [85, 10, 5], "опытный": [70, 20, 10], "неудачливый": [100, 0, 0]}
KIND_OF = {"обычный": "Boom", "опытный": "Mega", "неудачливый": "Boom"}  # вид для рекорда дальности
LUCK_DEPTH = 1.0  # удача у конца зоны: ×(1 + LUCK_DEPTH)
LUCK_POWER = 0.5  # вес следующей ступени редкости × удача^LUCK_POWER
ACC = {"обычный": 0.50, "опытный": 0.80, "неудачливый": 0.25}
T_SCALE, T_FLY, T_REVEAL, T_QUICK, T_CARRY = 3, 8, 5, 5, 16
HORIZON = 1200
P_BOSS = 1 / 2500
SELL_S = 60  # продажа капсулы: секунд её дохода
F_BUCKETS = [0.0, 0.25, 0.5, 0.75, 1.0]


def metres(strength):
    return METRE_K * (1 + strength) ** METRE_P


def floor_weights(rarity, luck=1.0, hunt=1.0):
    s = SHIFT[rarity] * luck**LUCK_POWER
    w = [c * s**k for k, c in enumerate(FLOOR_CHANCE)]
    w[4] *= hunt
    w[5] *= hunt
    total = sum(w)
    return [x / total for x in w]


def expected_mult(rarity):
    return sum(p * m for p, m in zip(floor_weights(rarity), FLOOR_MULT))


def creature_weights(tier_chances, R, luck=1.0, hunt=1.0):
    s = luck**LUCK_POWER
    w = [tier_chances[r] * s**k for k, r in enumerate(R)]
    w[3] *= hunt
    w[4] *= hunt
    return w


src = (HERE / "econ84c.py").read_text(encoding="utf-8").replace('if __name__ == "__main__":', "if False:")


def patch(text, old, new):
    assert text.count(old) == 1, old[:60]
    return text.replace(old, new)


src = patch(
    src,
    '    museum = [["Common", 1, pool[1]["Common"][0], True]]  # учебное Common босса 1 (не крадут)\n',
    '    museum = [["Common", 1, pool[1]["Common"][0], True, ("учебное",)]]  # учебное Common босса 1 (не крадут)\n'
    "    stock = {}  # D61: запас Ловибумов по (уровень, вид)\n"
    '    pack = cfg.get("pack", 1)\n'
    '    d74 = cfg.get("d74", False)\n'
    '    rolls = cfg.setdefault("rolls", [])\n'
    '    stats = cfg.setdefault("stats", {})\n'
    '    K = cfg.get("K", {})\n'
    "    roof = 0.0  # D75: доход босса на крыше (один, лучший)\n"
    '    kind = "Boom"\n'
    "    end_hit = False\n",
)
src_d74 = patch(
    src,
    "                if coins < cost:\n                    wait = (cost - coins)",
    "                if not stock.get((L, kind)) and coins < cost:\n                    wait = (cost - coins)",
)
src_d74 = patch(
    src_d74,
    """                    if coins < cost:
                        break
                    coins -= cost
                    cur["lov"] += cost
""",
    """                    if not stock.get((L, kind)):
                        if coins < cost:
                            break
                        coins -= cost
                        cur["lov"] += cost
                        stock[(L, kind)] = pack
                    stock[(L, kind)] -= 1
""",
)
src_d74 = patch(
    src_d74,
    "                item = [r, L, income, False]\n",
    "                k = rng.choices(range(len(FLOOR_MULT)), weights=floor_weights(r))[0]\n"
    "                item = [r, L, income / expected_mult(r) * FLOOR_MULT[k], False]\n",
)

a = src.index("        spawns = []\n")
b = src.index('            cur["fail_out"] += 1\n') + len('            cur["fail_out"] += 1\n')
THROW = '''        first = True
        acc = ACC[sc.name]
        while day_left > reserved + T_SCALE + T_FLY + T_REVEAL + T_CARRY + 5:
            held_now = museum + pending
            full = len(held_now) >= cap
            worst = min(m[2] for m in held_now) if full else 0.0
            base_d = metres(S)
            f_now = min(1.0, max(0.0, (base_d * (1 + ACC_MAX * acc) - MARK[L]) / (MARK[L + 1] - MARK[L])))
            if not stock.get((L, kind)):  # набор кончился: какой вид купить
                kind = rng.choices(KINDS, weights=MIX[sc.name])[0]
                if kind != "Boom" and value(L, f_now, worst, K.get(L, 1.0), kind) < boom[L] * MULT[kind] / pack:
                    kind = "Boom"  # охота не окупается — фарм
            price = boom[L] * MULT[kind]
            if value(L, f_now, worst, K.get(L, 1.0), kind) < price / pack:
                break  # бросок не окупается: копить и тренироваться
            if not stock.get((L, kind)):
                if coins < price:
                    break
                coins -= price
                cur["lov"] += price
                stats["lov"] = stats.get("lov", 0.0) + price
                stock[(L, kind)] = pack
            stock[(L, kind)] -= 1
            bonus = 1 + ACC_MAX * min(1.0, max(0.0, rng.gauss(acc, 0.2)))
            dist = min(base_d * bonus * KIND_RANGE[kind], MARK[L + 1])
            zone = L
            while zone > 1 and dist < MARK[zone]:
                zone -= 1
            f = min(1.0, max(0.0, (dist - MARK[zone]) / (MARK[zone + 1] - MARK[zone])))
            luck = 1 + LUCK_DEPTH * f
            hc, hf = KIND_HUNT[kind]
            r = rng.choices(R, weights=creature_weights(tier(zone), R, luck, hc))[0]
            k = rng.choices(range(len(FLOOR_MULT)), weights=floor_weights(r, luck, hf))[0]
            stats["k_" + kind] = stats.get("k_" + kind, 0) + 1
            idx = rng.randrange(len(pool[zone][r]))
            kz = K.get(zone, 1.0)
            income = pool[zone][r][idx] / expected_mult(r) * FLOOR_MULT[k] * kz
            ident = (zone, r, idx, k)
            rolls.append((zone, r, k))
            stats["throws"] = stats.get("throws", 0) + 1
            stats["short"] = stats.get("short", 0) + (1 if zone < L else 0)
            stats["luck"] = stats.get("luck", 0.0) + luck
            dt = (T_SCALE + T_FLY + T_REVEAL) if first else T_QUICK
            first = False
            if rng.random() < P_BOSS:
                stats["bosses"] = stats.get("bosses", 0) + 1
                roof = max(roof, boss_income(mean, zone) * kz)
                dt += T_CARRY
            dup = any(m[4] == ident for m in held_now)
            if dup or income <= worst:
                stats["dups"] = stats.get("dups", 0) + (1 if dup and income > worst else 0)
                gain_coins = income * SELL_S  # авто-продажа
                coins += gain_coins
                stats["sold"] = stats.get("sold", 0.0) + gain_coins
            else:
                stats["kept"] = stats.get("kept", 0) + 1
                cur["catches"] += 1
                dt += T_CARRY
                item = [r, zone, income, False, ident]
                if doom_day and day_left <= PREP:
                    pending.append(item)
                else:
                    if len(museum) >= cap:
                        out = min((m for m in museum if not m[3]), key=lambda m: m[2], default=None) or min(
                            museum, key=lambda m: m[2])
                        museum.remove(out)
                        coins += out[2] * SELL_S
                    museum.append(item)
                    inc = sum(m[2] for m in museum) + roof
                    mp = power()
            spend(dt, "catch")
'''
src_d75 = src[:a] + THROW + src[b:]
src_d75 = patch(
    src_d75,
    "        need = WIN * S_boss[L] if L < 10 else math.inf\n",
    "        need = S_boss[L] / (1 + ACC_MAX * ACC[sc.name]) ** 4 if L < 10 else math.inf\n",
)
src_d75 = patch(src_d75, "        inc = sum(m[2] for m in museum)\n        mp = power()\n        need",
                "        inc = sum(m[2] for m in museum) + roof\n        mp = power()\n        need")
src_d75 = patch(src_d75, "        day += 1\n",
                "        day += 1\n"
                "        if not end_hit and S >= END_S[sc.name]:\n"
                "            end_hit = True\n"
                "            cfg.setdefault('end_times', []).append(t)\n")
src_d75 = patch(src_d75, "dooms.append((ml, L, inc, max(m[2] for m in museum), bought, price))",
                "dooms.append((ml, L, inc, max((m[2] for m in museum), default=0), bought, price))")
src_d75 = patch(
    src_d75,
    "            for item in pending:\n                place(item)\n",
    "            for item in pending:\n"
    "                if any(m[4] == item[4] for m in museum):\n"
    "                    coins += item[2] * SELL_S\n"
    "                else:\n"
    "                    place(item)\n",
)

GAIN = {}  # [(зона, f, вид)] = (отсортированные доходы наград при K = 1, суммы с конца)
MARK = {}
# Сила, при которой обычный бросок игрока (его точность, его вид Ловибума) долетает до конца трассы.
END_S = {name: (END_MARK / (METRE_K * (1 + ACC_MAX * ACC[name]) * KIND_RANGE[KIND_OF[name]])) ** (1 / METRE_P) - 1
         for name in ACC}


def boss_income(mean, zone):
    """Доход босса зоны: Легендарное существо на Золотом этаже (зоны без Легендарных: 3 × Эпическое, D56)."""
    leg = mean[zone].get("Legendary") or 3 * mean[zone]["Epic"]
    return leg / expected_mult("Legendary") * FLOOR_MULT[GOLD]


def make_tables(cfg, tier, R):
    S = [0] + list(cfg["S"][1:10])
    for n in range(1, 11):
        MARK[n] = metres(S[n - 1]) if n > 1 else 0.0
    MARK[11] = END_MARK
    rng = random.Random(7)
    for zone in range(1, 11):
        for f in F_BUCKETS:
            luck = 1 + LUCK_DEPTH * f
            for kind in KINDS:
                hc, hf = KIND_HUNT[kind]
                xs = []
                for _ in range(4000):
                    r = rng.choices(R, weights=creature_weights(tier(zone), R, luck, hc))[0]
                    k = rng.choices(range(len(FLOOR_MULT)), weights=floor_weights(r, luck, hf))[0]
                    xs.append(rng.choice(cfg["pool"][zone][r]) / expected_mult(r) * FLOOR_MULT[k])
                xs.sort()
                tail = [0.0] * (len(xs) + 1)
                for i in range(len(xs) - 1, -1, -1):
                    tail[i] = tail[i + 1] + xs[i]
                GAIN[(zone, f, kind)] = (xs, tail)


def value(zone, f, worst, kz, kind="Boom"):
    """Ожидаемая ценность броска в монетах: прибавка дохода башни за HORIZON + выручка от продажи ненужного."""
    fb = min(F_BUCKETS, key=lambda x: abs(x - f))
    xs, tail = GAIN[(zone, fb, kind)]
    w = worst / kz
    i = bisect.bisect_right(xs, w)
    n = len(xs)
    gain = (tail[i] - w * (n - i)) / n
    sold = (tail[0] - tail[i]) / n
    return kz * (gain * HORIZON + sold * SELL_S)


def build(text, name):
    g = {"__file__": str(HERE / "econ84c.py"), "FLOOR_MULT": FLOOR_MULT, "floor_weights": floor_weights,
         "expected_mult": expected_mult, "creature_weights": creature_weights, "metres": metres, "value": value,
         "boss_income": boss_income, "MARK": MARK, "ACC": ACC, "ACC_MAX": ACC_MAX, "KIND_RANGE": KIND_RANGE,
         "KIND_HUNT": KIND_HUNT, "KINDS": KINDS, "MIX": MIX, "END_S": END_S, "LUCK_DEPTH": LUCK_DEPTH, "T_SCALE": T_SCALE, "T_FLY": T_FLY, "T_REVEAL": T_REVEAL,
         "T_QUICK": T_QUICK, "T_CARRY": T_CARRY, "P_BOSS": P_BOSS, "SELL_S": SELL_S}
    exec(compile(text, name, "exec"), g)
    return g


G74, G75 = build(src_d74, "econ84c_d74"), build(src_d75, "econ84c_d75")
load, short, TARGET_AT = G74["load"], G74["short"], G74["TARGET_AT"]
TYP, SKL, UNL = G74["TYP"], G74["SKL"], G74["UNL"]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60


def variant(d75, K=None):
    cfg = load("approved.json")
    cfg["pack"] = PER_BUY
    cfg["d74"] = not d75
    cfg["K"] = dict(K or {})
    cfg["stats"] = {}
    return cfg


def runs(g, cfg, sc, seed, n=None, stop_after=None):
    g["FIGHT"] = CUTSCENE
    sc = {s.name: s for s in (g["TYP"], g["SKL"], g["UNL"])}[sc.name]
    rng = random.Random(seed)
    out = []
    for _ in range(n or N):
        ph, _, _ = g["simulate3"](cfg, sc, rng, cap_h=700, stop_after=stop_after)
        out.append(ph)
    return out


def reached(ph, L, cfg, d75, sc):
    if len(ph) < L or ph[L - 1]["L"] != L:
        return False
    need = cfg["S"][L] / (1 + ACC_MAX * ACC[sc.name]) ** 4 if d75 else G74["WIN"] * cfg["S"][L]
    return ph[L - 1]["S"] >= need


def at(phs, L, cfg, d75, sc):
    return [ph[L - 1]["at"] / 3600 if reached(ph, L, cfg, d75, sc) else math.inf for ph in phs]


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))]


def fmt(xs):
    return f"**{statistics.median(xs):.1f}** ({q(xs, 0.1):.1f}–{q(xs, 0.9):.1f})"


cfg74 = variant(False)
make_tables(cfg74, G75["tier"], G75["R"])

# --- калибровка: K зоны L подбирается так, чтобы обычный игрок долетал до зоны L + 1 в цель ---
# Пределы K: не ниже K_MIN (и не ниже 0.45 от прошлой зоны — следующая зона должна оставаться выгоднее прошлой: доходы
# каталога растут в 3.2 раза за зону) и не выше K_MAX.
K_MIN, K_MAX = 0.3, 1.2
K = {n: 1.0 for n in range(1, 11)}
bound = {}  # зона → "низ" | "верх": цель недостижима доходом этой зоны
for L in range(3, 10):
    target = TARGET_AT[L + 1]
    floor_k = max(K_MIN, 0.45 * K[L - 1])
    lo, hi = floor_k, K_MAX
    for _ in range(9):
        mid = math.sqrt(lo * hi)
        K[L] = mid
        cfg = variant(True, K)
        med = statistics.median(at(runs(G75, cfg, TYP, 100, n=24, stop_after=L), L, cfg, True, TYP))
        if med > target:  # медленно — дохода мало
            lo = mid
        else:
            hi = mid
    K[L] = round(math.sqrt(lo * hi), 2)
    if K[L] <= floor_k * 1.03:
        bound[L] = "низ"
    elif K[L] >= K_MAX * 0.97:
        bound[L] = "верх"
K[10] = K[9]
(HERE / "d75_income_k.json").write_text(json.dumps({str(n): K[n] for n in K}, indent=1), encoding="utf-8")

data74 = {sc.name: runs(G74, cfg74, sc, 100) for sc in (TYP, SKL, UNL)}
data75, stats75, cfg75 = {}, {}, None
for sc in (TYP, SKL, UNL):
    cfg75 = variant(True, K)
    data75[sc.name] = runs(G75, cfg75, sc, 100)
    stats75[sc.name] = dict(cfg75["stats"])
raw = variant(True, {})
data_raw = runs(G75, raw, TYP, 100)

S = [0] + list(cfg75["S"][1:10])
print(f"# Экономика D75 «бросок вдаль»: калибровка дохода наград по зонам (модель econ84c, {N} прогонов, одни зёрна)\n")
print("Цены Ловибумов, пороги силы, редкость этажа — утверждённые (D56, D61, D74). Правила броска, удачи, продажи, "
      "босса и запрет одинаковых этажей — решения владельца по D75. Числа удачи и продажи — предложение.\n")

print("## Трасса и удача\n")
print(f"дальность, м = {METRE_K} × (1 + сила)^{METRE_P} × точность (до ×{1 + ACC_MAX:.2f}) × вид "
      "(" + ", ".join(f"{k} ×{v:.2f}" for k, v in KIND_RANGE.items()) + f"); конец трассы — {END_MARK:,} м.\n".replace(",", " "))
print(f"удача = 1 + {LUCK_DEPTH:g} × глубина; вес каждой следующей ступени редкости существа и этажа × "
      f"удача^{LUCK_POWER:g}. Вид Ловибума — «охота» на верхние редкости (таблица ниже).\n")
print("| Зона | порог силы | отметка, м | множитель дохода K (итог калибровки) |")
print("|---|---|---|---|")
for n in range(1, 11):
    note = {"низ": " — нижний предел: цель долёта до следующей зоны доходом не достигается (слишком быстро)",
            "верх": " — верхний предел: цель доходом не достигается (слишком медленно)"}.get(bound.get(n), "")
    print(f"| {n} | {short(S[n - 1]) if n > 1 else '0'} | {MARK[n]:,.0f} | ×{K[n]:g}{note} |".replace(",", " "))
print()
print(f"Пределы K: от {K_MIN:g} (и не ниже 0.45 от прошлой зоны — иначе следующая зона невыгоднее прошлой) до "
      f"{K_MAX:g}. K зон 1–2 = 1 (первые минуты игры не трогаются), K зоны 10 = K зоны 9.\n")

R = G75["R"]
print("## Что даёт удача (зоны 4–7, существо Common → этаж; шансы, %)\n")
print("| Удача | Legendary существо | Золотой | Мифический | Алмазный | средний доход броска |")
print("|---|---|---|---|---|---|")
base_ev = None
for luck in (1.0, 1.25, 1.5, 2.0):
    cw = creature_weights(G75["tier"](5), R, luck)
    tot = sum(cw)
    ev = 0.0
    for r, w in zip(R, cw):
        if w:
            fw = floor_weights(r, luck)
            ev += w / tot * cfg75["mean"][5][r] / expected_mult(r) * sum(p * m for p, m in zip(fw, FLOOR_MULT))
    base_ev = base_ev or ev
    fw = floor_weights("Common", luck)
    print(f"| ×{luck:g} | {cw[3] / tot * 100:.1f} | {fw[3] * 100:.1f} | {fw[4] * 100:.2f} | {fw[5] * 100:.2f} "
          f"| ×{ev / base_ev:.2f} |")
print()

print("## Виды Ловибумов: фарм и охота (в среднем по зонам 1–10 и глубине 0.25 / 0.5 / 0.75; Бум = 1)\n")
print("Охота умножает веса верхних редкостей: существа Legendary и Secret, этажи Мифический и Алмазный.\n")
print("| Вид | цена | дальность | существа ×, этажи × | доход за монету | Алмазный за монету | Мифический за монету "
      "| Legendary + Secret за монету | за бросок в зоне 5: Legendary, Алмазный |")
print("|---|---|---|---|---|---|---|---|---|")


def kind_stats(zone, luck, kind):
    hc, hf = KIND_HUNT[kind]
    cw = creature_weights(G75["tier"](zone), R, luck, hc)
    tot = sum(cw)
    ev = dia = myth = 0.0
    for r, w in zip(R, cw):
        if w:
            fw = floor_weights(r, luck, hf)
            ev += w / tot * cfg75["mean"][zone][r] / expected_mult(r) * sum(p * m for p, m in zip(fw, FLOOR_MULT))
            dia += w / tot * fw[5]
            myth += w / tot * fw[4]
    return [ev, dia, myth, (cw[3] + cw[4]) / tot]


PRICE_OF = {"Boom": 1, "Turbo": 2, "Mega": 3}
for kind in KINDS:
    acc_ = [0.0] * 4
    n_ = 0
    for zone in range(1, 11):
        a_, b_ = MARK[zone], MARK[zone + 1]
        for f in (0.25, 0.5, 0.75):
            d_ = a_ + f * (b_ - a_)
            base_ = kind_stats(zone, 1 + f, "Boom")
            fk = (min(d_ * KIND_RANGE[kind], b_) - a_) / (b_ - a_)
            vals = kind_stats(zone, 1 + fk, kind)
            for i in range(4):
                acc_[i] += (vals[i] / base_[i] if base_[i] else 1.0) / PRICE_OF[kind]
            n_ += 1
    one = kind_stats(5, 1.5, kind)
    hc, hf = KIND_HUNT[kind]
    print(f"| {kind} | ×{PRICE_OF[kind]} | ×{KIND_RANGE[kind]:.2f} | ×{hc:g}, ×{hf:g} | {acc_[0] / n_:.2f} | {acc_[1] / n_:.2f} "
          f"| {acc_[2] / n_:.2f} | {acc_[3] / n_:.2f} | {one[3] * 100:.1f} %, {one[1] * 100:.2f} % |")
print()
print("Редких существ за монету охота не даёт больше Бума ни при каких числах с доходом за монету 0.8: Legendary и Secret "
      "существа и есть основная часть дохода броска. За монету охота выигрывает редкими этажами, за бросок — и тем, и "
      "другим.\n")

for sc in (TYP, SKL, UNL):
    print(f"## Долёт до зон, часы игры — {sc.name} игрок: медиана (1 из 10 быстрее – 9 из 10 не позже)\n")
    head = "| Зона | цель | D74 (поимка у босса) | D75 с калибровкой |"
    print(head + (" D75 без калибровки |" if sc is TYP else ""))
    print("|---|---|---|---|" + ("---|" if sc is TYP else ""))
    for L in range(1, 10):
        tgt = TARGET_AT.get(L + 1)
        tg = (f"{tgt:g}" if L + 1 >= 7 else f"({tgt:g})") if tgt else ""
        row = f"| {L + 1} | {tg} | {fmt(at(data74[sc.name], L, cfg74, False, sc))} | {fmt(at(data75[sc.name], L, cfg75, True, sc))} |"
        if sc is TYP:
            row += f" {statistics.median(at(data_raw, L, raw, True, TYP)):.1f} |"
        print(row)
    print()

print("## Броски, продажа и повторы — D75 с калибровкой, в среднем на игрока за всю игру\n")
print("| Игрок | бросков | оставлено | повторов «Уже есть» | недолётов | средняя удача | на Ловибумы | выручка продажи "
      "| боссов |")
print("|---|---|---|---|---|---|---|---|---|")
for sc in (TYP, SKL, UNL):
    st = stats75[sc.name]
    th = max(1, st.get("throws", 0))
    print(f"| {sc.name} | {th / N:,.0f} | {st.get('kept', 0) / th * 100:.0f} % | {st.get('dups', 0) / th * 100:.1f} % "
          f"| {st.get('short', 0) / th * 100:.1f} % | ×{st.get('luck', 0) / th:.2f} | {short(st.get('lov', 0) / N)} "
          f"| {short(st.get('sold', 0) / N)} ({st.get('sold', 0) / max(1, st.get('lov', 1)) * 100:.0f} % трат) "
          f"| {st.get('bosses', 0) / N:.2f} |".replace(",", " "))
print()

print("## Доход башни при долёте до зоны — обычный игрок, медианы\n")
print("| Зона | D74, /с | D75, /с | D75 / D74 | доход босса зоны, /с |")
print("|---|---|---|---|---|")
for L in range(1, 10):
    v = []
    for data, cfg, d75 in ((data74, cfg74, False), (data75, cfg75, True)):
        xs = [ph[L - 1]["income"] for ph in data[TYP.name] if reached(ph, L, cfg, d75, TYP)]
        v.append(statistics.median(xs) if xs else float("nan"))
    print(f"| {L + 1} | {short(v[0])} | {short(v[1])} | {v[1] / v[0]:.2f} | "
          f"{short(boss_income(cfg75['mean'], L + 1) * K[L + 1])} |")
print()

print("## Конец трассы и рекорд дальности\n")
print(f"Конец трассы — {END_MARK} м. Сила, при которой обычный бросок игрока долетает до конца: "
      + "; ".join(f"{name} ({KIND_OF[name]}, точность {ACC[name]:.2f}) — {short(END_S[name])}" for name in ACC) + ".\n")
print("| Игрок | доля прогонов, где конец достигнут | час достижения: медиана (1 из 10 – 9 из 10) | часов после зоны 10 |")
print("|---|---|---|---|")
for sc in (TYP, SKL, UNL):
    cfg_e = variant(True, K)
    phs = []
    g_ = G75
    rng_ = random.Random(100)
    sc_ = {s.name: s for s in (g_["TYP"], g_["SKL"], g_["UNL"])}[sc.name]
    for _ in range(N):
        ph, _, _ = g_["simulate3"](cfg_e, sc_, rng_, cap_h=700, endgame_h=250)
        phs.append(ph)
    ends = [x / 3600 for x in cfg_e.get("end_times", [])]
    z10 = statistics.median(at(phs, 9, cfg_e, True, sc))
    if ends:
        med = statistics.median(ends)
        print(f"| {sc.name} | {len(ends) / N * 100:.0f} % | {med:.0f} ({q(ends, 0.1):.0f}–{q(ends, 0.9):.0f}) | {med - z10:+.0f} |")
    else:
        print(f"| {sc.name} | 0 % | не достигнут за 250 ч после зоны 10 | — |")
print()

rolls = cfg75["rolls"]
print(f"## Выпавшие этажи — D75 с калибровкой ({len(rolls)} бросков)\n")
print("| " + " | ".join(FLOORS) + " |")
print("|" + "---|" * len(FLOORS))
counts = [sum(1 for x in rolls if x[2] == k) for k in range(len(FLOORS))]
print("| " + " | ".join(f"{c / max(1, len(rolls)) * 100:.2f} %" for c in counts) + " |")

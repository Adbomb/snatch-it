"""Пересчёт экономики D56 под D75 («бросок вдаль»: в зонах нет видимых существ и боссов, игрок бросает Ловибум с
площадки, в зоне приземления сервер разыгрывает существо, редкость этажа и крошечный шанс босса). Только расчёт: цены,
сила боссов (= пороги зон), Ловибумы (набор из 3, D61), редкость этажа и нормировка дохода (D74) — утверждённые.

Что меняет D75 в модели econ84c:
  1. Видимых существ нет: игрок не выбирает лучшее из четырёх, каждый бросок — розыгрыш (редкость существа по шансам
     набора зоны, D37; редкость этажа — D74). Поимка не срывается: бросок = награда.
  2. Дороги в зону нет: бросок с площадки. Время броска — шкала, полёт (первый бросок за день; дальше быстрый режим),
     экран выпадения; нужную капсулу игрок несёт в башню (CARRY), ненужную бросает (DROP).
  3. Зона приземления — по дальности: метры = 10 × (1 + сила)^0.25 × точность (1 … 1.18) × вид Ловибума; отметка зоны N —
     те же метры при силе босса N (D56). Сила S_N гарантирует зону N, точность лишь добавляет. Ловибум уровня N дальше
     зоны N не летит.
  4. Игрок бросает, пока ожидаемая прибавка дохода башни за HORIZON секунд окупает цену броска (вслепую, по шансам);
     иначе копит на гантель и уровень музея и тренируется. Раньше его ограничивали 4 существа за день.
  5. Босс зоны: шанс P_BOSS с броска, встаёт на крышу (места в башне не занимает), доход BOSS_MULT × базовый Common зоны.
Сравнение — с D74 (поимка-прицел, катсцена «съел», этажи) на тех же зёрнах.

Запуск: python scripts/sim/economy84/d75_recalc.py [число прогонов, по умолчанию 60] > отчёт.md
"""

import bisect
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

# --- D75: предложение (на утверждение) ---
METRE_K, METRE_P = 10, 0.25  # дальность, м = METRE_K × (1 + сила) ^ METRE_P
ACC_MAX = 0.18  # идеальное попадание по шкале: +18 % дальности
KIND_RANGE = {"Boom": 1.0, "Turbo": 1.06, "Mega": 1.12}  # вид Ловибума: дальность
ACC = {"обычный": 0.50, "опытный": 0.80, "неудачливый": 0.25}  # средняя доля бонуса точности
T_SCALE, T_FLY, T_REVEAL = 3, 8, 5  # шкала, полёт с камерой, экран выпадения, с
T_QUICK = 5  # быстрый режим: шкала и сразу результат, с
T_CARRY, T_DROP = 16, 2  # донести капсулу до башни и вернуться; бросить ненужную, с
HORIZON = 1200  # с: бросок окупается ожидаемой прибавкой дохода за это время
P_BOSS = 1 / 2500  # шанс босса с броска
BOSS_MULT = 150  # доход босса на крыше = BOSS_MULT × базовый доход Common его зоны
INCOME_K = 1.0  # рычаг калибровки: доход наград × INCOME_K (нормировка: бросок вслепую, наград больше)
BOOM_K = 1.0  # рычаг калибровки: цены Ловибумов × BOOM_K


def metres(strength):
    return METRE_K * (1 + strength) ** METRE_P


def floor_weights(rarity):
    s = SHIFT[rarity]
    w = [c * s**k for k, c in enumerate(FLOOR_CHANCE)]
    total = sum(w)
    return [x / total for x in w]


def expected_mult(rarity):
    return sum(p * m for p, m in zip(floor_weights(rarity), FLOOR_MULT))


src = (HERE / "econ84c.py").read_text(encoding="utf-8").replace('if __name__ == "__main__":', "if False:")


def patch(text, old, new):
    assert text.count(old) == 1, old[:60]
    return text.replace(old, new)


# общее с D74: набор из 3 Ловибумов, этаж случайной редкости
src = patch(
    src,
    '    museum = [["Common", 1, pool[1]["Common"][0], True]]  # учебное Common босса 1 (не крадут)\n',
    '    museum = [["Common", 1, pool[1]["Common"][0], True]]  # учебное Common босса 1 (не крадут)\n'
    "    stock = {}  # D61: запас Ловибумов по (уровень, вид)\n"
    '    pack = cfg.get("pack", 1)\n'
    '    d74 = cfg.get("d74", False)\n'
    '    d75 = cfg.get("d75", False)\n'
    '    rolls = cfg.setdefault("rolls", [])\n'
    '    stats = cfg.setdefault("stats", {"throws": 0, "kept": 0, "short": 0, "bosses": 0, "lov": 0.0})\n'
    "    roof = 0  # D75: боссы на крыше (мест не занимают)\n",
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
    "                if d74:\n"
    "                    k = rng.choices(range(len(FLOOR_MULT)), weights=floor_weights(r))[0]\n"
    "                    rolls.append((L, r, k))\n"
    "                    item = [r, L, income / expected_mult(r) * FLOOR_MULT[k], False]\n"
    "                else:\n"
    "                    item = [r, L, income, False]\n",
)

# D75: вместо «увидел существ → пошёл → поймал» — броски с площадки
a = src.index("        spawns = []\n")
b = src.index('            cur["fail_out"] += 1\n') + len('            cur["fail_out"] += 1\n')
THROW = '''        first = True
        acc = ACC[sc.name]
        while day_left > reserved + T_SCALE + T_FLY + T_REVEAL + T_CARRY + 5:
            held_now = museum + pending
            full = len(held_now) >= cap + roof
            worst = min(m[2] for m in held_now) if full else 0.0
            kind = "Boom"
            price = boom[L] * MULT[kind] * BOOM_K
            if INCOME_K * gain(L, worst / INCOME_K) * HORIZON < price / pack:
                break  # бросок не окупается: копить и тренироваться
            if not stock.get((L, kind)):
                if coins < price:
                    break
                coins -= price
                cur["lov"] += price
                stats["lov"] += price
                stock[(L, kind)] = pack
            stock[(L, kind)] -= 1
            bonus = 1 + ACC_MAX * min(1.0, max(0.0, rng.gauss(acc, 0.2)))
            zone = L
            if L > 1 and metres(S) * bonus * KIND_RANGE[kind] < metres(S_boss[L - 1]):
                zone = L - 1  # недолёт: Ловибум упал в прошлой зоне
                stats["short"] += 1
            r = rng.choices(R, weights=[tier(zone)[x] for x in R])[0]
            k = rng.choices(range(len(FLOOR_MULT)), weights=floor_weights(r))[0]
            income = rng.choice(pool[zone][r]) / expected_mult(r) * FLOOR_MULT[k] * INCOME_K
            rolls.append((zone, r, k))
            stats["throws"] += 1
            dt = (T_SCALE + T_FLY + T_REVEAL) if first else T_QUICK
            first = False
            if rng.random() < P_BOSS:
                roof += 1
                stats["bosses"] += 1
                museum.append(["Common", zone, INCOME_K * BOSS_MULT * mean[zone]["Common"] / expected_mult("Common"), True])
                dt += T_CARRY
            if income > worst:
                stats["kept"] += 1
                cur["catches"] += 1
                dt += T_CARRY
                item = [r, zone, income, False]
                if doom_day and day_left <= PREP:
                    pending.append(item)
                else:
                    if len(museum) >= cap + roof:
                        museum.remove(min((m for m in museum if not m[3]), key=lambda m: m[2]))
                    museum.append(item)
                    inc = sum(m[2] for m in museum)
                    mp = power()
            else:
                dt += T_DROP
            spend(dt, "catch")
'''
src_d75 = src[:a] + THROW + src[b:]
src_d75 = patch(
    src_d75,
    "        need = WIN * S_boss[L] if L < 10 else math.inf\n",
    "        need = S_boss[L] / (1 + ACC_MAX * ACC[sc.name]) ** 4 if L < 10 else math.inf\n",
)
src_d75 = patch(src_d75, "        cap = slots_of(ml)\n", "        cap = slots_of(ml)\n        cap_roof = cap + roof\n")
src_d75 = patch(src_d75, "dooms.append((ml, L, inc, max(m[2] for m in museum), bought, price))",
                "dooms.append((ml, L, inc, max((m[2] for m in museum), default=0), bought, price))")
src_d75 = patch(
    src_d75,
    "            if len(museum) >= cap:\n                museum.remove(min(museum, key=lambda m: m[2]))\n",
    "            if len(museum) >= cap_roof:\n                museum.remove(min(museum, key=lambda m: m[2]))\n",
)

GAIN = {}  # [зона] = (отсортированные доходы наград, суммы с конца)


def make_gain(cfg, tier, R):
    rng = random.Random(7)
    for zone in range(1, 11):
        xs = []
        for _ in range(8000):
            r = rng.choices(R, weights=[tier(zone)[x] for x in R])[0]
            k = rng.choices(range(len(FLOOR_MULT)), weights=floor_weights(r))[0]
            xs.append(rng.choice(cfg["pool"][zone][r]) / expected_mult(r) * FLOOR_MULT[k])
        xs.sort()
        tail = [0.0] * (len(xs) + 1)
        for i in range(len(xs) - 1, -1, -1):
            tail[i] = tail[i + 1] + xs[i]
        GAIN[zone] = (xs, tail)


def gain(zone, worst):
    """Ожидаемая прибавка дохода башни с одного броска в зону: E[max(0, награда − худший этаж)]."""
    xs, tail = GAIN[zone]
    i = bisect.bisect_right(xs, worst)
    return (tail[i] - worst * (len(xs) - i)) / len(xs)


def build(text, name):
    g = {"__file__": str(HERE / "econ84c.py"), "FLOOR_MULT": FLOOR_MULT, "floor_weights": floor_weights,
         "expected_mult": expected_mult, "metres": metres, "gain": gain, "ACC": ACC, "ACC_MAX": ACC_MAX,
         "KIND_RANGE": KIND_RANGE, "T_SCALE": T_SCALE, "T_FLY": T_FLY, "T_REVEAL": T_REVEAL, "T_QUICK": T_QUICK,
         "T_CARRY": T_CARRY, "T_DROP": T_DROP, "HORIZON": HORIZON, "P_BOSS": P_BOSS, "BOSS_MULT": BOSS_MULT,
         "INCOME_K": INCOME_K, "BOOM_K": BOOM_K}
    exec(compile(text, name, "exec"), g)
    return g


G74, G75 = build(src_d74, "econ84c_d74"), build(src_d75, "econ84c_d75")
load, done, short, TARGET_AT = G74["load"], G74["done"], G74["short"], G74["TARGET_AT"]
TYP, SKL, UNL = G74["TYP"], G74["SKL"], G74["UNL"]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60


def variant(d75):
    cfg = load("approved.json")
    cfg["pack"] = PER_BUY
    cfg["d74"], cfg["d75"] = not d75, d75
    return cfg


def runs(g, cfg, sc, seed, horizon=None, income_k=1.0, boom_k=1.0):
    if horizon:
        g["HORIZON"] = horizon
    g["INCOME_K"], g["BOOM_K"] = income_k, boom_k
    g["FIGHT"] = CUTSCENE
    sc = {s.name: s for s in (g["TYP"], g["SKL"], g["UNL"])}[sc.name]
    rng = random.Random(seed)
    out = []
    for _ in range(N):
        ph, _, _ = g["simulate3"](cfg, sc, rng, cap_h=600)
        out.append(ph)
    g["HORIZON"] = HORIZON
    g["INCOME_K"], g["BOOM_K"] = 1.0, 1.0
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


cfg74, cfg75 = variant(False), variant(True)
make_gain(cfg75, G75["tier"], G75["R"])
data74 = {sc.name: runs(G74, cfg74, sc, 100) for sc in (TYP, SKL, UNL)}
data75 = {}
stats75 = {}
for sc in (TYP, SKL, UNL):
    cfg75["stats"] = {"throws": 0, "kept": 0, "short": 0, "bosses": 0, "lov": 0.0}
    data75[sc.name] = runs(G75, cfg75, sc, 100)
    stats75[sc.name] = dict(cfg75["stats"])

S = [0] + [x for x in cfg75["S"][1:10]]  # сила босса N = порог зоны N
print(f"# Пересчёт экономики под D75 «бросок вдаль» (модель econ84c, {N} прогонов на вариант, одинаковые зёрна)\n")
print("Цены, пороги силы, набор из 3 Ловибумов, редкость и доход этажа — утверждённые (D56, D61, D74). Всё, что "
      "помечено «предложение», ждёт решения владельца.\n")

print("## Формула дальности (предложение)\n")
print(f"**дальность, м = {METRE_K} × (1 + сила)^{METRE_P} × точность × вид Ловибума**\n")
print(f"- точность по шкале: от ×1.00 (мимо) до ×{1 + ACC_MAX:.2f} (идеально) — сила босса N гарантирует зону N, "
      "точность только добавляет;")
print("- вид: " + ", ".join(f"{k} ×{v:.2f}" for k, v in KIND_RANGE.items()) + ";")
print("- Ловибум уровня N дальше конца зоны N не летит.\n")
print("| Зона | порог силы (D56) | отметка на трассе, м | сила для зоны с идеальной шкалой и Мегой |")
print("|---|---|---|---|")
best = (1 + ACC_MAX) * KIND_RANGE["Mega"]
for n in range(1, 11):
    m = metres(S[n - 1]) if n > 1 else 0
    need = ((metres(S[n - 1]) / best / METRE_K) ** (1 / METRE_P) - 1) if n > 1 else 0
    print(f"| {n} | {short(S[n - 1]) if n > 1 else '0'} | {m:,.0f} | {short(max(0, need)) if n > 1 else '0'} |".replace(",", " "))
print()
print(f"Лучший бросок (идеальная шкала и Мега) даёт ×{best:.2f} дальности — это сила в ×{best ** (1 / METRE_P):.1f} раза "
      "меньше порога; пороги соседних зон различаются в 7–136 раз, перепрыгнуть зону точностью нельзя.\n")

for sc in (TYP, SKL, UNL):
    print(f"## Долёт до зон, часы игры — {sc.name} игрок: медиана (1 из 10 быстрее – 9 из 10 не позже)\n")
    print("| Зона | цель | D74 (поимка у босса) | D75 (бросок) | D75 против D74 |")
    print("|---|---|---|---|---|")
    for L in range(1, 10):
        a74 = at(data74[sc.name], L, cfg74, False, sc)
        a75 = at(data75[sc.name], L, cfg75, True, sc)
        m74, m75 = statistics.median(a74), statistics.median(a75)
        tgt = TARGET_AT.get(L + 1)
        tg = (f"{tgt:g}" if L + 1 >= 7 else f"({tgt:g})") if tgt else ""
        print(f"| {L + 1} | {tg} | {fmt(a74)} | {fmt(a75)} | {m75 - m74:+.1f} ч ({(m75 - m74) / m74 * 100:+.0f} %) |")
    print()

print("## Броски и траты — D75, в среднем на одного игрока за всю игру (до зоны 10 и дальше до конца прогона)\n")
print("| Игрок | бросков | оставлено наград | недолётов | потрачено на Ловибумы | боссов при шансе 1/2500 |")
print("|---|---|---|---|---|---|")
for sc in (TYP, SKL, UNL):
    st = stats75[sc.name]
    print(f"| {sc.name} | {st['throws'] / N:,.0f} | {st['kept'] / N:,.0f} ({st['kept'] / max(1, st['throws']) * 100:.0f} %) "
          f"| {st['short'] / max(1, st['throws']) * 100:.1f} % | {short(st['lov'] / N)} | {st['bosses'] / N:.2f} |".replace(",", " "))
print()

print("## Бросков к приходу в зону — обычный игрок, медианы (для выбора шанса босса)\n")
print("| К зоне | часов | бросков всего | боссов в среднем при 1/1000 | при 1/2500 | при 1/5000 |")
print("|---|---|---|---|---|---|")
for L in (3, 6, 7, 8, 9):
    xs, hs = [], []
    for ph in data75[TYP.name]:
        if reached(ph, L, cfg75, True, TYP):
            xs.append(sum(p["catches"] for p in ph[:L]))
            hs.append(ph[L - 1]["at"] / 3600)
    if xs:
        kept = statistics.median(xs)
        share = stats75[TYP.name]["kept"] / max(1, stats75[TYP.name]["throws"])
        throws = kept / max(share, 1e-9)
        print(f"| {L + 1} | {statistics.median(hs):.1f} | {throws:,.0f} | {throws / 1000:.2f} | {throws / 2500:.2f} "
              f"| {throws / 5000:.2f} |".replace(",", " "))
print()

print("## Доход башни при приходе в зону — обычный игрок, медианы\n")
print("| Зона | D74, /с | D75, /с | D75 / D74 |")
print("|---|---|---|---|")
for L in range(1, 10):
    v = []
    for data, cfg, d75 in ((data74, cfg74, False), (data75, cfg75, True)):
        xs = [ph[L - 1]["income"] for ph in data[TYP.name] if reached(ph, L, cfg, d75, TYP)]
        v.append(statistics.median(xs) if xs else float("nan"))
    print(f"| {L + 1} | {short(v[0])} | {short(v[1])} | {v[1] / v[0]:.2f} |")
print()

print("## Чем вернуть темп 14 / 28 / 56 / 84 ч: два рычага (обычный игрок, часы до зоны)\n")
print("При прежних ценах и доходах D75 быстрее целей: нет дороги в зону и срывов поимки, бросков за день — сколько "
      "хватит монет, из многих наград башня оставляет лучшие.\n")
print("| Рычаг | зона 7 (14) | зона 8 (28) | зона 9 (56) | зона 10 (84) | бросков за игру |")
print("|---|---|---|---|---|---|")
best = None
for label, ik, bk in [("как есть", 1.0, 1.0), ("доход наград ×0.85", 0.85, 1.0), ("доход наград ×0.75", 0.75, 1.0),
                      ("доход наград ×0.65", 0.65, 1.0), ("доход наград ×0.5", 0.5, 1.0),
                      ("цены Ловибумов ×1.5", 1.0, 1.5), ("цены Ловибумов ×2", 1.0, 2.0),
                      ("цены Ловибумов ×3", 1.0, 3.0)]:
    cfg = variant(True)
    cfg["stats"] = {"throws": 0, "kept": 0, "short": 0, "bosses": 0, "lov": 0.0}
    phs = runs(G75, cfg, TYP, 100, income_k=ik, boom_k=bk)
    med = [statistics.median(at(phs, L, cfg, True, TYP)) for L in (6, 7, 8, 9)]
    err = sum(abs(math.log(m / t)) for m, t in zip(med, (14, 28, 56, 84)))
    if ik != 1.0 and bk == 1.0 and (best is None or err < best[0]):
        best = (err, ik, label)
    print(f"| {label} | " + " | ".join(f"{m:.1f}" for m in med)
          + f" | {cfg['stats']['throws'] / N:,.0f} |".replace(",", " "))
print()
print(f"Ближе всего к целям без изменения цен — **{best[2]}** (нормировка дохода существ, как в D74). Расчёт для "
      "этого варианта:\n")
for sc in (TYP, SKL, UNL):
    cfg = variant(True)
    phs = runs(G75, cfg, sc, 100, income_k=best[1])
    print(f"- {sc.name} игрок, часы до зон 7 / 8 / 9 / 10: "
          + " / ".join(fmt(at(phs, L, cfg, True, sc)) for L in (6, 7, 8, 9)))
print()

print("## Чувствительность: как долго игрок готов окупать бросок (обычный игрок, часы до зоны)\n")
print("| Окупаемость броска | зона 7 | зона 8 | зона 9 | зона 10 |")
print("|---|---|---|---|---|")
for h in (300, 1200, 4800):
    cfg = variant(True)
    phs = data75[TYP.name] if h == HORIZON else runs(G75, cfg, TYP, 100, horizon=h)
    cells = [f"{statistics.median(at(phs, L, cfg, True, TYP)):.1f}" for L in (6, 7, 8, 9)]
    print(f"| {h // 60} мин{' (основной расчёт)' if h == HORIZON else ''} | " + " | ".join(cells) + " |")
print()

rolls = cfg75["rolls"]
print(f"## Выпавшие этажи во всех прогонах D75 ({len(rolls)} бросков)\n")
print("| " + " | ".join(FLOORS) + " |")
print("|" + "---|" * len(FLOORS))
counts = [sum(1 for x in rolls if x[2] == k) for k in range(len(FLOORS))]
print("| " + " | ".join(f"{c} ({c / max(1, len(rolls)) * 100:.2f} %)" for c in counts) + " |")

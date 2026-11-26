"""Пересчёт экономики D56 после D74 (без боя: босс съедает пойманное и отрыгивает этаж случайной редкости). Только расчёт:
цены, сила боссов, шансы поимки и Ловибумы — утверждённые (approved.json = Config/Progression, Config/Catch), набор из 3
Ловибумов (D61) — как в коде.

Что меняет D74 в модели econ84c:
  1. Боя нет: вместо FIGHT = 18 с — катсцена «отобрал → съел → отрыгнул» и прокрутка, CUTSCENE с.
  2. Этаж получает редкость (Деревянный … Космический) по шансам FLOOR_CHANCE, сдвинутым вверх редкостью существа
     (вес ступени k умножается на SHIFT[редкость]^k), доход этажа = доход существа / E[множитель] × множитель.
     Матожидание дохода с поимки — как в D56, редкие этажи — джекпот.
  3. Игрок решает, ловить ли, по ожидаемому доходу (редкость этажа до прокрутки неизвестна), а в башне держит лучшие
     этажи — отбор лучших из случайных поднимает доход выше матожидания; отчёт показывает, насколько.
  4. Варианты существ Golden / Giant / Rainbow и наборы каталога по видам: модель D56 их не считала (в коде они не
     выпадают — Progression.Modifiers «не утверждены и не используются»), поэтому их удаление часов не меняет.
Удержание по силе (D74): сила ≥ силы босса — обычный шанс; ниже порога модель, как и с боем, считает, что игрок к боссу
не идёт (порог WIN × сила босса — прежний).

Запуск: python scripts/sim/economy84/d74_recalc.py [число прогонов, по умолчанию 60] > отчёт.md
"""

import math
import random
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
PER_BUY = 3  # Config/Catch.PerBuy (D61)
CUTSCENE = 14  # с: отобрал → съел → отрыгнул (~8) + прокрутка (~6)

FLOORS = ["Деревянный", "Каменный", "Мраморный", "Золотой", "Мифический", "Космический"]
FLOOR_CHANCE = [60, 25, 10, 4, 0.9, 0.1]  # %, D74
FLOOR_MULT = [1, 2, 4, 8, 20, 60]  # D74
# Сдвиг вверх от редкости пойманного существа (предложение, на утверждение): вес ступени k × SHIFT^k.
SHIFT = {"Common": 1.0, "Rare": 1.15, "Epic": 1.3, "Legendary": 1.5, "Secret": 1.8}


def floor_weights(rarity):
    s = SHIFT[rarity]
    w = [c * s**k for k, c in enumerate(FLOOR_CHANCE)]
    total = sum(w)
    return [x / total for x in w]


def expected_mult(rarity):
    return sum(p * m for p, m in zip(floor_weights(rarity), FLOOR_MULT))


src = (HERE / "econ84c.py").read_text(encoding="utf-8").replace('if __name__ == "__main__":', "if False:")
patches = [
    # D61: набор из 3 Ловибумов — как в d61_recalc.py
    ('    museum = [["Common", 1, pool[1]["Common"][0], True]]  # учебное Common босса 1 (не крадут)\n',
     '    museum = [["Common", 1, pool[1]["Common"][0], True]]  # учебное Common босса 1 (не крадут)\n'
     '    stock = {}  # D61: запас Ловибумов по (уровень, вид)\n'
     '    pack = cfg.get("pack", 1)\n'
     '    d74 = cfg.get("d74", False)\n'
     '    rolls = cfg.setdefault("rolls", [])\n'),
    ("                if coins < cost:\n                    wait = (cost - coins)",
     "                if not stock.get((L, kind)) and coins < cost:\n                    wait = (cost - coins)"),
    ("""                    if coins < cost:
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
"""),
    # D74: этаж случайной редкости; доход нормирован на ожидаемый множитель редкости существа
    ("                item = [r, L, income, False]\n",
     "                if d74:\n"
     "                    k = rng.choices(range(len(FLOOR_MULT)), weights=floor_weights(r))[0]\n"
     "                    rolls.append((L, r, k))\n"
     "                    item = [r, L, income / expected_mult(r) * FLOOR_MULT[k], False]\n"
     "                else:\n"
     "                    item = [r, L, income, False]\n"),
]
for old, new in patches:
    assert src.count(old) == 1, old[:60]
    src = src.replace(old, new)
g = {"__file__": str(HERE / "econ84c.py"), "FLOOR_MULT": FLOOR_MULT, "floor_weights": floor_weights,
     "expected_mult": expected_mult}
exec(compile(src, "econ84c_d74", "exec"), g)
simulate3, load, done, short, TARGET_AT = g["simulate3"], g["load"], g["done"], g["short"], g["TARGET_AT"]
TYP, SKL, UNL = g["TYP"], g["SKL"], g["UNL"]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60


def variant(name):
    cfg = load("approved.json")
    cfg["pack"] = PER_BUY
    cfg["d74"] = name == "D74"
    return cfg


def runs(cfg, sc, seed, fight):
    g["FIGHT"] = fight
    rng = random.Random(seed)
    out = []
    for _ in range(N):
        ph, _, _ = simulate3(cfg, sc, rng, cap_h=600)
        out.append(ph)
    return out


def at(phs, L, cfg):
    return [ph[L - 1]["at"] / 3600 if done(ph, L, cfg) else math.inf for ph in phs]


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))]


def fmt(xs):
    return f"**{statistics.median(xs):.1f}** ({q(xs, 0.1):.1f}–{q(xs, 0.9):.1f})"


VARS = [("D61 (как сейчас, с боем)", "D61", g["FIGHT"]), ("D74 (катсцена, этажи)", "D74", CUTSCENE)]
cfgs = {key: variant(key) for _, key, _ in VARS}
data = {(key, sc.name): runs(cfgs[key], sc, 100, fight) for _, key, fight in VARS for sc in (TYP, SKL, UNL)}

print(f"# Пересчёт экономики после D74 (модель econ84c, {N} прогонов на вариант, одинаковые зёрна)\n")
print("Цены, сила боссов, шансы поимки, Ловибумы (набор из 3, D61) — утверждённые. Меняются: бой → катсцена "
      f"({CUTSCENE} с вместо боя 18 с) и доход экспоната → доход этажа случайной редкости, "
      "нормированный на матожидание.\n")

print("## Редкость этажа: шансы после сдвига от редкости существа (предложение сдвига — на утверждение)\n")
print("| Существо | сдвиг | " + " | ".join(FLOORS) + " | средний множитель = делитель базы |")
print("|---|---|" + "---|" * len(FLOORS) + "---|")
for r in ("Common", "Rare", "Epic", "Legendary", "Secret"):
    w = floor_weights(r)
    print(f"| {r} | ×{SHIFT[r]:g} на ступень | " + " | ".join(f"{p * 100:.2f} %" for p in w)
          + f" | {expected_mult(r):.3f} |")
print()
print("Множители дохода: " + " / ".join(f"{n} ×{m}" for n, m in zip(FLOORS, FLOOR_MULT)) + ".\n")

print("## Нормированный базовый доход существ, /с (Деревянный этаж = база; средний по редкости, D56 → D74)\n")
mean = cfgs["D74"]["mean"]
print("| Босс | " + " | ".join(f"{r}: D56 → база D74" for r in ("Common", "Rare", "Epic", "Legendary", "Secret"))
      + " |")
print("|---|" + "---|" * 5)
for L in range(1, 11):
    cells = []
    for r in ("Common", "Rare", "Epic", "Legendary", "Secret"):
        v = mean[L].get(r)
        cells.append(f"{short(v)} → {short(v / expected_mult(r))}" if v else "—")
    print(f"| {L} | " + " | ".join(cells) + " |")
print()

for sc in (TYP, SKL, UNL):
    print(f"## Приход к боссам, часы игры — {sc.name} игрок: медиана (1 из 10 быстрее – 9 из 10 не позже)\n")
    print("| Босс | цель | " + " | ".join(n for n, _, _ in VARS) + " | D74 против D61 |")
    print("|---|---|" + "---|" * len(VARS) + "---|")
    for L in range(1, 10):
        cols = [at(data[(key, sc.name)], L, cfgs[key]) for _, key, _ in VARS]
        a, c = statistics.median(cols[0]), statistics.median(cols[1])
        tgt = TARGET_AT.get(L + 1)
        tg = (f"{tgt:g}" if L + 1 >= 7 else f"({tgt:g})") if tgt else ""
        print(f"| {L + 1} | {tg} | " + " | ".join(fmt(x) for x in cols)
              + f" | {c - a:+.1f} ч ({(c - a) / a * 100:+.0f} %) |")
    print()

print("## Доход при приходе к боссу — обычный игрок, медианы (башня держит лучшие этажи)\n")
print("| Босс | D61, /с | D74, /с | D74 / D61 |")
print("|---|---|---|---|")
for L in range(1, 10):
    vals = []
    for key in ("D61", "D74"):
        xs = [ph[L - 1]["income"] for ph in data[(key, TYP.name)] if done(ph, L, cfgs[key])]
        vals.append(statistics.median(xs) if xs else float("nan"))
    print(f"| {L + 1} | {short(vals[0])} | {short(vals[1])} | {vals[1] / vals[0]:.2f} |")
print()

rolls = cfgs["D74"]["rolls"]
print(f"## Выпавшие этажи во всех прогонах D74 ({len(rolls)} поимок)\n")
print("| " + " | ".join(FLOORS) + " |")
print("|" + "---|" * len(FLOORS))
counts = [sum(1 for x in rolls if x[2] == k) for k in range(len(FLOORS))]
print("| " + " | ".join(f"{c} ({c / max(1, len(rolls)) * 100:.1f} %)" for c in counts) + " |")
print()

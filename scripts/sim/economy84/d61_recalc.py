"""Пересчёт модели D56 после D61 (одна покупка Ловибумов — набор из 3 штук за прежнюю цену). Только расчёт: цены,
доходы, сила боссов и шансы не меняются (утверждённые числа — approved.json = Config/Progression, Config/Catch).

Три варианта одной и той же модели econ84c (версия 3, утверждённая экономика):
  «до D61»   — как считала модель при утверждении D56: бросок стоит цену покупки;
  «÷3»       — оценка 2026-11-14 (lovibum_x3_effect.py): бросок стоит цену покупки / 3;
  «как в коде» — набор: при пустом запасе вида и уровня покупается набор из Catch.PerBuy = 3 штук за цену покупки,
               бросок тратит 1 штуку; запас переносится между поимками, а остаток уровня N сгорает при переходе
               к боссу N+1 (Ловибум уровня N действует только на существ босса N).

Запуск: python scripts/sim/economy84/d61_recalc.py [число прогонов, по умолчанию 60] > отчёт.md
"""

import math
import random
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
PER_BUY = 3  # Config/Catch.PerBuy

src = (HERE / "econ84c.py").read_text(encoding="utf-8").replace('if __name__ == "__main__":', "if False:")
# набор Ловибумов: запас по (уровень, вид); покупка — только при пустом запасе
patches = [
    ('    museum = [["Common", 1, pool[1]["Common"][0], True]]  # учебное Common босса 1 (не крадут)\n',
     '    museum = [["Common", 1, pool[1]["Common"][0], True]]  # учебное Common босса 1 (не крадут)\n'
     '    stock = {}  # D61: запас Ловибумов по (уровень, вид)\n'
     '    pack = cfg.get("pack", 1)\n'),
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
]
for old, new in patches:
    assert src.count(old) == 1, old[:60]
    src = src.replace(old, new)
g = {"__file__": str(HERE / "econ84c.py")}
exec(compile(src, "econ84c_d61", "exec"), g)
simulate3, load, done, short, TARGET_AT = g["simulate3"], g["load"], g["done"], g["short"], g["TARGET_AT"]
TYP, SKL, UNL = g["TYP"], g["SKL"], g["UNL"]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60


def variant(name):
    cfg = load("approved.json")
    if name == "÷3":
        cfg["boom"] = {L: v / PER_BUY for L, v in cfg["boom"].items()}
    elif name == "как в коде":
        cfg["pack"] = PER_BUY
    return cfg


def runs(cfg, sc, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(N):
        ph, _, _ = simulate3(cfg, sc, rng, cap_h=600)
        out.append(ph)
    return out


def at(phs, L, cfg):
    """Часы прихода к боссу L+1 по прогонам (inf — не дошёл)."""
    return [ph[L - 1]["at"] / 3600 if done(ph, L, cfg) else math.inf for ph in phs]


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))]


def fmt(xs):
    return f"**{statistics.median(xs):.1f}** ({q(xs, 0.1):.1f}–{q(xs, 0.9):.1f})"


def with_growth(cfg, growth, first=5):
    """Средние доходы существ боссов first…10 при другом Growth (ступень между боссами): цепочка от босса first−1,
    Legendary = 3 × Epic, Secret = 3 × Legendary, разброс ±12 % — как в econ84.incomes. Боссы до first−1 не трогаются."""
    mean, pool = cfg["mean"], cfg["pool"]
    for L in range(first, 11):
        mean[L] = {r: mean[L - 1][r] * growth for r in ("Common", "Rare", "Epic")}
        mean[L]["Legendary"] = 3 * mean[L]["Epic"]
        mean[L]["Secret"] = 3 * mean[L]["Legendary"]
        pool[L] = {r: [mean[L][r] * f for f in (0.88, 0.94, 1.0, 1.06, 1.12)] for r in mean[L]}
    return cfg


def fit(n_runs=120):
    """Подбор Growth боссов 5–10 при D61 (как в коде), чтобы обычный игрок снова приходил к 7 / 8 / 9 / 10 в цели."""
    print("## Предложение (не применено): средние доходы существ боссов 5–10 при D61\n")
    print("Цены D56 не трогаются; коллекций боссов 5–10 ещё нет, их средние (Progression.CreatureIncome.ByBoss) — "
          "единственные утверждённые числа, которые в игре пока не работают. Growth — ступень дохода между боссами "
          "(сейчас 3.2).\n")
    print("| Growth 5–10 | к 7 | к 8 | к 9 | к 10 |")
    print("|---|---|---|---|---|")
    global N
    keep, N = N, n_runs
    for gr in (3.2, 3.0, 2.9, 2.8, 2.7):
        cfg = with_growth(variant("как в коде"), gr)
        phs = runs(cfg, TYP, 100)
        cells = [f"{statistics.median(at(phs, L, cfg)):.1f}" for L in (6, 7, 8, 9)]
        print(f"| {gr} | " + " | ".join(cells) + " |")
    N = keep
    print()


if len(sys.argv) > 2 and sys.argv[2] == "fit":
    fit()
    sys.exit(0)

VARS = ["до D61", "÷3", "как в коде"]
cfgs = {v: variant(v) for v in VARS}
data = {(v, sc.name): runs(cfgs[v], sc, 100) for v in VARS for sc in (TYP, SKL, UNL)}

print(f"# Пересчёт экономики D56 после D61 (модель econ84c, {N} прогонов на вариант, одинаковые зёрна)\n")
print("Цены, доходы, сила боссов, шансы — утверждённые (approved.json = код). Меняется только цена броска.\n")
for sc in (TYP, SKL, UNL):
    print(f"## Приход к боссам, часы игры — {sc.name} игрок: медиана (1 из 10 быстрее – 9 из 10 не позже)\n")
    print("| Босс | цель | " + " | ".join(VARS) + " | как в коде против до D61 |")
    print("|---|---|" + "---|" * len(VARS) + "---|")
    for L in range(1, 10):
        cols = [at(data[(v, sc.name)], L, cfgs[v]) for v in VARS]
        a, c = statistics.median(cols[0]), statistics.median(cols[2])
        tgt = TARGET_AT.get(L + 1)
        tg = (f"{tgt:g}" if L + 1 >= 7 else f"({tgt:g})") if tgt else ""
        print(f"| {L + 1} | {tg} | " + " | ".join(fmt(x) for x in cols) + f" | {c - a:+.1f} ч ({(c - a) / a * 100:+.0f} %) |")
    print()

print("## Куда уходят монеты и время — обычный игрок, медианы по этапам\n")
print("| Этап | Ловибумы, доля заработанного: до D61 → как в коде | поимка, доля времени: до → как в коде | "
      "длина этапа: до → как в коде |")
print("|---|---|---|---|")
for L in range(1, 10):
    row = []
    for key in ("lov_share", "catch_share", "time"):
        vals = []
        for v in ("до D61", "как в коде"):
            xs = []
            for ph in data[(v, TYP.name)]:
                if len(ph) >= L and done(ph, L, cfgs[v]):
                    p = ph[L - 1]
                    if key == "lov_share":
                        xs.append(p["lov"] / max(p["earned"], 1))
                    elif key == "catch_share":
                        xs.append(p["catch"] / max(p["time"], 1))
                    else:
                        xs.append(p["time"] / 3600)
            vals.append(statistics.median(xs) if xs else float("nan"))
        if key == "time":
            row.append(f"{vals[0]:.1f} → {vals[1]:.1f} ч")
        else:
            row.append(f"{vals[0] * 100:.0f} % → {vals[1] * 100:.0f} %")
    print(f"| {L}→{L + 1} | " + " | ".join(row) + " |")
print()
print("## Ловибумы в коде (D61): цена покупки = набор из 3\n")
print("| Босс | Бум / Турбо / Мега за набор | 1 Бум |")
print("|---|---|---|")
boom = cfgs["до D61"]["boom"]
for L in range(1, 11):
    print(f"| {L} | {short(boom[L])} / {short(2 * boom[L])} / {short(3 * boom[L])} | {short(boom[L] / PER_BUY)} |")

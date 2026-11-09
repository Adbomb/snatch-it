"""Цены Ловибумов (D55): расчёт, по которому владелец утвердил цены боссов 1–3 (2026-11-09); 4–10 — предварительно.

Модель (вывод — таблица Markdown):
  • доход существа — Config/Items (income) для боссов 1–3; 4–10 — продолжение роста 1 → 3 по каждой редкости,
    Legendary = 4 × Epic, Secret = 4 × Legendary (ПРЕДВАРИТЕЛЬНО: коллекций 4–10 ещё нет);
  • средний слот — шансы редкостей Progression.BossLoot; витрин — max(6, 2 × уровень) (GameConfig.Museum);
  • «новичок уровня» — только дошёл до босса L: витрины из существ уровня L − 1 (на боссе 1 — одно учебное Common);
    «прокачанный» — витрины из существ уровня L;
  • Бум уровня 1 = 1K (новичок после обучения копит ~1 мин); уровня L ≥ 2 — 35 с «среднего» дохода
    √(новичок × прокачанный), округлено; Турбо = 2 Бума, Мега = 3 Бума (бонусы к шансу ×1 / ×1.5 / ×2 — D55);
  • стоимость поимки — цена / (0.7 попаданий × шанс), шансы D55.

  python scripts/sim/lovibum_prices.py           — таблица
  python scripts/sim/lovibum_prices.py --check   — сверить Config/Catch: Prices 1–3 — с утверждёнными числами (APPROVED),
                                                  PreliminaryPrices 4–10 — с расчётом; Турбо = 2 Бума, Мега = 3 Бума
"""

import math
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ITEMS = ROOT / "src" / "shared" / "Config" / "Items.luau"
CATCH = ROOT / "src" / "shared" / "Config" / "Catch.luau"
R = ["Common", "Rare", "Epic", "Legendary", "Secret"]
BASE = {"Common": 0.6, "Rare": 0.35, "Epic": 0.3, "Legendary": 0.14, "Secret": 0.06}
BONUS = {"Boom": 1, "Turbo": 1.5, "Mega": 2}
PRICE_MULT = {"Boom": 1, "Turbo": 2, "Mega": 3}
HIT = 0.7
TIERS = [
    (1, 3, {"Common": 70, "Rare": 25, "Epic": 5, "Legendary": 0, "Secret": 0}),
    (4, 7, {"Common": 52, "Rare": 30, "Epic": 13, "Legendary": 5, "Secret": 0}),
    (8, 10, {"Common": 32.5, "Rare": 35, "Epic": 20, "Legendary": 11.25, "Secret": 1.25}),
]
NICE = (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10)
APPROVED = {1: 1000, 2: 10000, 3: 30000}  # Бум, утверждено владельцем 2026-11-09 (не пересчитывается моделью)


def incomes():
    text = ITEMS.read_text(encoding="utf-8")
    out = {}
    for fn, boss in (("wonder", 1), ("find", 2)):
        for m in re.finditer(r"\n" + fn + r'\("(\w+)", "(\w+)", "[^"]*", "\w+", "\w+", (\d+(?:\.\d+)?)', text):
            out.setdefault(boss, {}).setdefault(m.group(2), []).append(float(m.group(3)))
    for m in re.finditer(r'\ncreature\("(\w+)", "(\w+)", "[^"]*", "\w+", (\d+(?:\.\d+)?)', text):
        out.setdefault(3, {}).setdefault(m.group(2), []).append(float(m.group(3)))
    mean = {L: {r: statistics.mean(v) for r, v in out[L].items()} for L in (1, 2, 3)}
    growth = {r: math.sqrt(mean[3][r] / mean[1][r]) for r in ("Common", "Rare", "Epic")}
    for L in range(4, 11):
        mean[L] = {r: mean[3][r] * growth[r] ** (L - 3) for r in growth}
        mean[L]["Legendary"] = 4 * mean[L]["Epic"]
        mean[L]["Secret"] = 4 * mean[L]["Legendary"]
    return mean


def tier(level):
    return next(ch for a, b, ch in TIERS if a <= level <= b)


def nice(x):
    k = 10 ** int(math.floor(math.log10(x)))
    return min((n * k for n in NICE), key=lambda v: abs(math.log(v / x)))


def model():
    mean = incomes()
    slot = {L: sum(tier(L)[r] / 100 * mean[L].get(r, 0) for r in R) for L in range(1, 11)}
    slots = {L: max(6, 2 * L) for L in range(1, 11)}
    fresh = {1: mean[1]["Common"]}
    for L in range(2, 11):
        fresh[L] = slots[L] * slot[L - 1]
    adv = {L: slots[L] * slot[L] for L in range(1, 11)}
    boom = dict(APPROVED)
    for L in range(2, 11):
        if L not in APPROVED:
            boom[L] = int(nice(35 * math.sqrt(fresh[L] * adv[L])))
    return mean, slot, fresh, adv, boom


def short(n):
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            return f"{n / div:.1f}".rstrip("0").rstrip(".") + suf
    return f"{n:.0f}"


def dur(sec):
    if sec < 60:
        return f"{sec:.0f} с"
    if sec < 3600:
        return f"{sec / 60:.1f} мин"
    return f"{sec / 3600:.1f} ч"


def config_prices():
    """Цены из Config/Catch.luau: утверждённые {уровень: (Бум, Турбо, Мега)} и предварительные Бумы {уровень: Бум}."""
    text = CATCH.read_text(encoding="utf-8")
    final = {
        int(m.group(1)): (float(m.group(2)), float(m.group(3)), float(m.group(4)))
        for m in re.finditer(r"\[(\d+)\] = \{ Boom = ([\d.e_]+), Turbo = ([\d.e_]+), Mega = ([\d.e_]+) \}", text)
    }
    block = re.search(r"PreliminaryPrices = \(function\(\)\s*local boom = \{([^}]*)\}", text)
    if not final or not block:
        sys.exit("Не нашёл Prices / PreliminaryPrices в Config/Catch.luau — формат изменился, обнови разбор")
    pre = {int(m.group(1)): float(m.group(2)) for m in re.finditer(r"\[(\d+)\] = ([\d.e_]+)", block.group(1))}
    return final, pre


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    mean, slot, fresh, adv, boom = model()
    if "--check" in sys.argv:
        final, pre = config_prices()
        bad = [L for L, b in APPROVED.items() if final.get(L) != (b, 2 * b, 3 * b)]
        bad += [L for L in range(4, 11) if pre.get(L) != boom[L]]
        bad += [L for L in final if L not in APPROVED]  # в Prices — только утверждённые
        print("Config/Catch совпадает: 1–3 — утверждённые, 4–10 — расчёт" if not bad else f"РАСХОЖДЕНИЕ на уровнях {bad}")
        sys.exit(1 if bad else 0)
    print("## Цены Ловибумов (D55): 1–3 утверждены 2026-11-09, 4–10 — ⚠ предварительно\n")
    print("| Босс | Бум | Турбо | Мега | Средний доход существа, /с | Новичок: 1 / 3 Бума | Прокачанный: 1 / 3 Бума |")
    print("|---|---|---|---|---|---|---|")
    for L in range(1, 11):
        p, mark = boom[L], "" if L in APPROVED else " ⚠"
        print(f"| {L}{mark} | {short(p)} | {short(2 * p)} | {short(3 * p)} | {short(slot[L])} | "
              f"{dur(p / fresh[L])} / {dur(3 * p / fresh[L])} | {dur(p / adv[L])} / {dur(3 * p / adv[L])} |")
    print("\n### Стоимость успешной поимки (Бумом, 70 % попаданий; в скобках — окупаемость существа)\n")
    print("| Босс | " + " | ".join(R) + " |")
    print("|---|" + "---|" * len(R))
    for L in range(1, 11):
        cells = []
        for r in R:
            if tier(L)[r] == 0:
                cells.append("—")
                continue
            cost = boom[L] / (HIT * min(1, BASE[r]))
            cells.append(f"{short(cost)} ({dur(cost / mean[L][r])})")
        print(f"| {L}{'' if L in APPROVED else ' ⚠'} | " + " | ".join(cells) + " |")
    print("\n### Бросков на поимку / стоимость в Бумах\n")
    print("| | Бум | Турбо | Мега |\n|---|---|---|---|")
    for r in R:
        cells = [f"{1 / (HIT * min(1, BASE[r] * BONUS[k])):.1f} / {PRICE_MULT[k] / (HIT * min(1, BASE[r] * BONUS[k])):.1f}"
                 for k in BONUS]
        print(f"| {r} | " + " | ".join(cells) + " |")


main()

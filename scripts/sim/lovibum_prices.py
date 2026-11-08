"""Цены Ловибумов (D55) — итоговая таблица на согласование владельцу. ЦЕНЫ НЕ УТВЕРЖДЕНЫ: в игру — только после «ок».

Правило D55: цена зависит только от уровня босса и вида, ощутима и для новичка, и для прокачанного (с учётом трёх
бросков и повторов после поражения). Модель: Бум уровня L = HOLD секунд дохода типичного игрока, который сейчас ловит
на уровне L (музей max(6, 2L) мест, заполненных существами уровня L − 1; на уровне 1 — две Common после обучения);
Турбо ×2, Мега ×3 (бонус ×1.5 и ×2 к шансу).
Доход среднего случайного слота босса: боссы 1–2 — Config/Items (income), босс 3 — docs/CATALOG.md (предварительный),
4–10 — продолжение средним множителем роста 1 → 3. Шансы слота — Progression.BossLoot, шансы захвата — Config/Catch.

  python scripts/sim/lovibum_prices.py            — таблица (Markdown)
  python scripts/sim/lovibum_prices.py --luau     — та же таблица строкой для Config/Catch.Prices (после «ок»)
"""

import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ITEMS = ROOT / "src" / "shared" / "Config" / "Items.luau"
CATALOG = ROOT / "docs" / "CATALOG.md"
HOLD = 20  # секунд дохода на один Бум
KIND_MULT = {"Boom": 1, "Turbo": 2, "Mega": 3}
BONUS = {"Boom": 1, "Turbo": 1.5, "Mega": 2}
BASE = {"Common": 0.6, "Rare": 0.35, "Epic": 0.3, "Legendary": 0.14, "Secret": 0.06}
SLOT_CHANCE = {1: {"Common": 0.70, "Rare": 0.25, "Epic": 0.05}}  # D37, боссы 1–3
HIT = 0.7  # доля попаданий у обычного игрока (оценка)
NAMES = {"Boom": "Бум", "Turbo": "Турбо", "Mega": "Мега"}


def incomes_from_items():
    text = ITEMS.read_text(encoding="utf-8")
    out = {1: {}, 2: {}}
    for fn, boss in (("wonder", 1), ("find", 2)):
        for m in re.finditer(fn + r'\("(\w+)", "(\w+)", "[^"]*", "\w+", "\w+", (\d+(?:\.\d+)?)', text):
            out[boss].setdefault(m.group(2), []).append(float(m.group(3)))
    return out


def incomes_boss3():
    text = CATALOG.read_text(encoding="utf-8")
    part = text[text.index("## Босс 3"):text.index("## Боссы 4–10")]
    out = {}
    for line in part.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 6 and cells[0].isdigit():
            out.setdefault(cells[1], []).append(float(cells[5].replace(" ", "")))
    return out


def mean(v):
    return sum(v) / len(v)


NICE = (1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 10)


def nice(x):
    """Круглая цена из ряда 1 · 1.5 · 2 · 2.5 · 3 · 3.5 · 4 · 5 · 6 · 7 · 8 × 10^k (500, 3 500, 10 000 …)."""
    k = 10 ** int(math.floor(math.log10(x)))
    return int(round(min((n * k for n in NICE), key=lambda v: abs(v - x))))


def short(n):
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            v = n / div
            return (f"{v:.1f}".rstrip("0").rstrip(".")) + suf
    return str(int(n))


def main():
    by = incomes_from_items()
    by[3] = incomes_boss3()
    slot = {}
    for boss in (1, 2, 3):
        slot[boss] = sum(SLOT_CHANCE[1][r] * mean(by[boss][r]) for r in SLOT_CHANCE[1])
    growth = math.sqrt(slot[3] / slot[1])  # средний рост за уровень (1 → 3)
    for boss in range(4, 11):
        slot[boss] = slot[boss - 1] * growth
    rows = []
    for level in range(1, 11):
        if level == 1:
            income = 2 * mean(by[1]["Common"])  # после обучения: стартовое Common и ещё одно
        else:
            income = max(6, 2 * level) * slot[level - 1]
        boom = nice(HOLD * income)
        rows.append((level, income, {k: boom * m for k, m in KIND_MULT.items()}))
    if "--luau" in sys.argv:
        parts = [f"[{lvl}] = {{ Boom = {p['Boom']}, Turbo = {p['Turbo']}, Mega = {p['Mega']} }}" for lvl, _, p in rows]
        print("Prices = {\n\t" + ",\n\t".join(parts) + ",\n},")
        return
    print("## Цены Ловибумов — на согласование (не утверждены)\n")
    print(f"Средний случайный слот, монет/с: " + ", ".join(f"ур. {b} — {slot[b]:.1f}" for b in range(1, 4))
          + f"; дальше ×{growth:.2f} за уровень (оценка: доходы 4–10 ещё не заданы).\n")
    print(f"Бум = {HOLD} с дохода игрока, который ловит на этом уровне; Турбо ×2, Мега ×3.\n")
    print("| Уровень | Доход игрока, /с | Бум | Турбо | Мега |")
    print("|---|---|---|---|---|")
    for level, income, p in rows:
        print(f"| {level} | {short(income)} | {short(p['Boom'])} | {short(p['Turbo'])} | {short(p['Mega'])} |")
    print("\nСколько Бумов в среднем уходит на одно существо (попаданий ~70 %, бой выигран):")
    for rarity in ("Common", "Rare", "Epic"):
        per = 1 / (HIT * BASE[rarity] * BONUS["Boom"])
        print(f"- {rarity}: ≈ {per:.1f} Бума; Мегой — ≈ {1 / (HIT * min(1, BASE[rarity] * 2)):.1f} Меги")
    first = rows[0][2]["Boom"] / rows[0][1]
    print(f"\nНовичок после обучения (одно Common ур. 1, ≈ {mean(by[1]['Common']):.0f}/с): Бум за {short(rows[0][2]['Boom'])}"
          f" — ≈ {first * 2:.0f} с его дохода.")


main()

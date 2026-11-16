"""Оценка D61 для боссов 5–10: одна покупка = 3 Ловибума за прежнюю цену. Цены НЕ меняются — только считаем эффект.

Статика (lovibum_prices.model): цена покупки Бума (D56) → цена одного Ловибума до (×1) и после (÷3); ожидаемая цена
поимки среднего слота Бумом (шансы редкостей D37, 70 % попаданий, шансы захвата D55) и сколько минут дохода «только
дошедшего» игрока она стоит. Динамика (economy84/econ84c, утверждённая экономика approved.json): медиана прихода
обычного игрока к боссам 5–10 при цене одного Ловибума = цена покупки (как в модели до D61) и = цена покупки / 3.

  python scripts/sim/lovibum_x3_effect.py [число прогонов, по умолчанию 60]
"""

import contextlib
import copy
import io
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
with contextlib.redirect_stdout(io.StringIO()):  # модуль печатает свою таблицу при импорте
    import lovibum_prices as LP  # noqa: E402

ECON = HERE / "economy84"
g = {"__file__": str(ECON / "econ84c.py")}
exec(compile((ECON / "econ84c.py").read_text(encoding="utf-8").replace('if __name__ == "__main__":', "if False:"),
             "econ84c", "exec"), g)

N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
PER_BUY = 3


def static():
    mean, slot, fresh, adv, boom = LP.model()
    print("### Цена одного Ловибума и средней поимки (Бум, цены D56 без изменений)\n")
    print("| Босс | Покупка Бума (3 шт.) | 1 Бум до D61 | 1 Бум после | Средняя поимка до | после | "
          "= минут дохода «только дошедшего»: до → после |")
    print("|---|---|---|---|---|---|---|")
    for L in range(5, 11):
        ch = LP.tier(L)
        throws = sum(ch[r] / 100 / (LP.HIT * min(1, LP.BASE[r])) for r in LP.R if ch[r])
        before, after = boom[L] * throws, boom[L] / PER_BUY * throws
        print(f"| {L} | {LP.short(boom[L])} | {LP.short(boom[L])} | {LP.short(boom[L] / PER_BUY)} | "
              f"{LP.short(before)} | {LP.short(after)} | {before / fresh[L] / 60:.1f} → {after / fresh[L] / 60:.1f} |")
    print()


def dynamic():
    base = g["load"]("approved.json")
    cheap = copy.deepcopy(base)
    cheap["boom"] = {L: v / PER_BUY for L, v in base["boom"].items()}
    print(f"### Приход обычного игрока к боссам (модель econ84c, медиана {N} прогонов, ч)\n")
    print("| К боссу | Ловибум = цена покупки | Ловибум = цена / 3 (D61) | разница |")
    print("|---|---|---|---|")
    for L in range(4, 10):
        a = g["arrival"](base, L, N, 100 + L) / 3600
        b = g["arrival"](cheap, L, N, 100 + L) / 3600
        print(f"| {L + 1} | {a:.1f} | {b:.1f} | {b - a:+.1f} ({(b - a) / a * 100:+.1f} %) |")
    print()


if __name__ == "__main__":
    static()
    dynamic()
    print("Цели D56 — приход к боссам 7 / 8 / 9 / 10 за 14 / 28 / 56 / 84 ч; сравнивать с колонкой D61. "
          "Цены, доходы и шансы не менялись; это только оценка.")

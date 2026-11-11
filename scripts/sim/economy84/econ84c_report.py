"""Отчёт по модели версии 3 (вариант «по дизайну», защита Б, тренировка в Судную ночь)."""
import math
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).parent
src = (HERE / "econ84c.py").read_text(encoding="utf-8").replace('if __name__ == "__main__":', "if False:")
g = {"__file__": str(HERE / "econ84c.py")}
exec(compile(src, "econ84c", "exec"), g)
sys.stdout.reconfigure(encoding="utf-8")
short, slots_of, tier, R, POWER, TARGET_AT, WIN = (g[k] for k in ("short", "slots_of", "tier", "R", "POWER", "TARGET_AT", "WIN"))
HACK, HACK_B, SHARE, done = g["HACK"], g["HACK_B"], g["SHARE"], g["done"]
simulate3 = g["simulate3"]
CYCLE = 3360.0
NAME = sys.argv[1] if len(sys.argv) > 1 else "approved.json"


def fh(sec):
    hh = sec / 3600
    return f"{hh:.1f} ч" if hh >= 0.95 else f"{hh * 60:.0f} мин"


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else float("nan")


def pct(xs, q):
    xs = sorted(xs)
    return xs[int(q * (len(xs) - 1))]


def runs(cfg, sc, n, seed, cap=700, **kw):
    rng = random.Random(seed)
    return [simulate3(cfg, sc, rng, endgame_h=4.0, cap_h=cap, **kw) for _ in range(n)]


def arrivals(rs, cfg, L):
    return [r[0][L - 2]["at"] / 3600 if done(r[0], L - 1, cfg) else math.inf for r in rs]


def rows_of(rs, cfg, L):
    return [r[0][L - 1] for r in rs if done(r[0], L, cfg)]


def params(cfg, old):
    mean = cfg["mean"]
    print("### Параметры по боссам (было до калибровки версии 3 → стало)")
    print("| Босс | сила босса | гантель N: цена (мощность) | уровень музея N: цена (мест) | Бум / Турбо / Мега | доход C / R / E / L / S, /с |")
    print("|---|---|---|---|---|---|")

    def ch(a, b):
        return short(b) if a == b or not a else f"{short(a)} → {short(b)}"

    for L in range(1, 11):
        m = mean[L]
        inc = " / ".join(short(m[r]) for r in R if tier(L)[r] > 0)
        sb = "0" if L == 1 else ch(old["S"][L - 1], cfg["S"][L - 1])
        dp = f"— ({short(POWER[0])}/с)" if L == 1 else f"{ch(old['DP'][L], cfg['DP'][L])} ({short(POWER[L - 1])}/с)"
        mp = "— (6)" if L == 1 else f"{ch(old['MP'][L], cfg['MP'][L])} ({slots_of(L)})"
        b = cfg["boom"][L]
        bm = f"{short(b)} / {short(2 * b)} / {short(3 * b)}" + ("" if old["boom"][L] == b else f" (было {short(old['boom'][L])})")
        print(f"| {L} | {sb} | {dp} | {mp} | {bm} | {inc} |")
    print()
    print("### Защита и взлом по уровням музея (цены взлома — из файла параметров; ур. 1–6 — D37)")
    print("| Уровень музея | взлом | ловушка 10 % | лазер 15 % | дверь 20 % | робот 30 % | устройств можно |")
    print("|---|---|---|---|---|---|---|")
    for ml in range(1, 11):
        H = cfg["hack"][ml - 1]
        print(f"| {ml} | {short(H)}" + ("" if H == HACK[ml - 1] else f" (D37: {short(HACK[ml - 1])})") + " | "
              + " | ".join(short(H * SHARE[k]) for k in ("Trap", "Laser", "Door", "Robot")) + f" | {min(ml, 5)} |")
    print()


def progression(all_runs, cfg):
    print("### Приход к боссам, часы игры: медиана (1 из 10 быстрее – 9 из 10 не позже), день при 2 ч в день")
    print("| Босс | цель | " + " | ".join(all_runs) + " |")
    print("|---|---|" + "---|" * len(all_runs))
    for L in range(2, 11):
        cells = []
        for name, rs in all_runs.items():
            at = arrivals(rs, cfg, L)
            m = statistics.median(at)
            dev = f", {(m / TARGET_AT[L] - 1) * 100:+.0f} %" if L >= 7 and name == "обычный" else ""
            cells.append(f"**{m:.1f}** ({pct(at, 0.1):.1f}–{pct(at, 0.9):.1f}), день {math.ceil(m / 2 - 1e-9)}{dev}")
        tgt = f"{TARGET_AT[L]:g}" if L >= 7 else f"({TARGET_AT[L]:g})"
        print(f"| {L} | {tgt} | " + " | ".join(cells) + " |")
    print()


def tables(rs, cfg):
    P = range(1, 10)
    print("#### Время по занятиям (обычный игрок, медианы)")
    print("| Этап | длина | тренировка днём | ночью | в Судные ночи | тренировка всего | поимка | покупка защиты |")
    print("|---|---|---|---|---|---|---|---|")
    for L in P:
        rows = rows_of(rs, cfg, L)
        T = med([p["time"] for p in rows])
        day = med([p["train"] + p["wait"] for p in rows])
        tr = med([p["train"] + p["wait"] + p["night"] + p["doomnight"] for p in rows])
        c = {k: med([p[k] for p in rows]) for k in ("night", "doomnight", "catch", "defbuy")}
        print(f"| {L}→{L + 1} | {fh(T)} | {fh(day)} | {fh(c['night'])} | {fh(c['doomnight'])} | {fh(tr)} ({tr / T * 100:.0f} %) | "
              f"{fh(c['catch'])} ({c['catch'] / T * 100:.0f} %) | {fh(c['defbuy'])} |")
    print()
    print("#### Деньги: доход и на что уходит заработанное (обычный игрок, медианы)")
    print("| Этап | доход/с: начало → конец | заработано | Ловибумы | гантели | музей | защита | монет к концу |")
    print("|---|---|---|---|---|---|---|---|")
    for L in P:
        rows = rows_of(rs, cfg, L)
        ia, ie = med([p["arrive_income"] for p in rows]), med([p["income"] for p in rows])
        sh = {k: med([p[k] / max(p["earned"], 1) for p in rows]) for k in ("lov", "dbc", "mus", "def")}
        print(f"| {L}→{L + 1} | {short(ia)} → {short(ie)} | {short(med([p['earned'] for p in rows]))} | "
              + " | ".join(f"{sh[k] * 100:.0f} %" if sh[k] >= 0.005 else f"{sh[k] * 100:.1f} %" for k in ("lov", "dbc", "mus", "def"))
              + f" | {short(med([p['coins'] for p in rows]))} |")
    print()
    print("#### Покупки этапа (обычный игрок, медианы): когда, доля этапа, цена, сколько часов дохода стоит")
    print("| Этап | гантель | уровень музея |")
    print("|---|---|---|")
    for L in P:
        rows = rows_of(rs, cfg, L)
        T = med([p["time"] for p in rows])
        d = "—"
        if L >= 2:
            got = [p["db_at"][L] for p in rows if L in p["db_at"]]
            if len(got) > len(rows) / 2:
                hi = med([cfg["DP"][L] / p["db_inc"][L] / 3600 for p in rows if L in p["db_inc"]])
                d = f"№{L}: на {fh(med(got))} ({med(got) / T * 100:.0f} % этапа), {short(cfg['DP'][L])} = {hi:.1f} ч дохода"
            else:
                early = sum(1 for p in rows if p["db0"] >= L)
                d = f"№{L}: куплена до этапа" if early > len(rows) / 2 else f"№{L}: позже, на следующем этапе"
        got = [p["ml_at"][L + 1] for p in rows if L + 1 in p["ml_at"]]
        if len(got) > len(rows) / 2:
            hi = med([cfg["MP"][L + 1] / p["ml_inc"][L + 1] / 3600 for p in rows if L + 1 in p["ml_inc"]])
            m = f"ур. {L + 1}: на {fh(med(got))} ({med(got) / T * 100:.0f} % этапа), {short(cfg['MP'][L + 1])} = {hi:.1f} ч дохода"
        else:
            early = sum(1 for p in rows if p["ml0"] >= L + 1)
            m = f"ур. {L + 1}: куплен до этапа" if early > len(rows) / 2 else f"ур. {L + 1}: позже"
        print(f"| {L}→{L + 1} | {d} | {m} |")
    print()
    print("#### Музей и поимка (обычный игрок, медианы)")
    print("| Этап | уровень музея | мест / занято | состав C/R/E/L/S | прибавка силы: начало → конец | средний множитель | поймано (в час) | вылазок без добычи |")
    print("|---|---|---|---|---|---|---|---|")
    for L in P:
        rows = rows_of(rs, cfg, L)
        T = med([p["time"] for p in rows])
        comp = "/".join(f"{med([p['comp'][r] for p in rows]):.0f}" for r in R)
        mpav = med([p["mp_time"] / max(p["train_time"], 1) for p in rows])
        cat = med([p["catches"] for p in rows])
        print(f"| {L}→{L + 1} | {med([p['ml0'] for p in rows]):.0f} → {med([p['ml'] for p in rows]):.0f} | "
              f"{med([p['slots'] for p in rows]):.0f} / {med([p['filled'] for p in rows]):.0f} | {comp} | "
              f"+{med([p['mp0'] for p in rows]) * 100:.0f} % → +{med([p['mp_end'] for p in rows]) * 100:.0f} % | "
              f"×{1 + mpav:.2f} | {cat:.0f} ({cat / (T / 3600):.1f}) | {med([p['fail_out'] for p in rows]):.0f} |")
    print()
    print("#### Откуда сила на этапах 7–9 (обычный игрок, медианы)")
    for L in (7, 8, 9):
        rows = rows_of(rs, cfg, L)
        parts = []
        for d in sorted({d for p in rows for d in p["gain_by_db"]}):
            gain = med([p["gain_by_db"].get(d, 0) for p in rows])
            if gain > 0:
                parts.append(f"гантель {d} ({short(POWER[d - 1])}/с): +{short(gain)}")
        print(f"- Этап {L}→{L + 1}: нужно 0.8 × {short(cfg['S'][L])} = {short(WIN * cfg['S'][L])}; было "
              f"{short(med([p['S0'] for p in rows]))}; " + "; ".join(parts))
    print()


def defense(all_runs, cfg):
    print("#### Защита по этапам: Судных ночей / из них с защитой / устройств за защищённую ночь / траты (доля заработка) / украдено")
    print("| Этап | " + " | ".join(all_runs) + " |")
    print("|---|" + "---|" * len(all_runs))
    for L in range(3, 10):
        cells = []
        for name, rs in all_runs.items():
            rows = rows_of(rs, cfg, L)
            dn = med([p["dooms"] for p in rows])
            df = med([p["defended"] for p in rows])
            dev = med([p["devices"] / p["defended"] for p in rows if p["defended"]]) if any(p["defended"] for p in rows) else 0
            sp = med([p["def"] for p in rows])
            sh = med([p["def"] / max(p["earned"], 1) for p in rows])
            cells.append(f"{dn:.0f} / {df:.0f} / {dev:.1f} / {short(sp)} ({sh * 100:.1f} %) / {med([p['lost'] for p in rows]):.0f}")
        print(f"| {L}→{L + 1} | " + " | ".join(cells) + " |")
    tot = []
    for name, rs in all_runs.items():
        ok = [r for r in rs if done(r[0], 9, cfg)]
        dn = med([sum(p["dooms"] for p in r[0][:9]) for r in ok])
        df = med([sum(p["defended"] for p in r[0][:9]) for r in ok])
        lost = med([sum(p["lost"] for p in r[0][:9]) for r in ok])
        caught = med([sum(p["catches"] for p in r[0][:9]) for r in ok])
        tot.append(f"{dn:.0f} ночей, защита в {df:.0f} ({df / dn * 100:.0f} %), украдено {lost:.0f} из {caught:.0f} пойманных")
    print("| **до босса 10** | " + " | ".join(tot) + " |")
    print()


def hack_table(rs, cfg):
    by = {}
    for r in rs:
        for ml, L, inc, best, bought, price in r[2]:
            by.setdefault(ml, []).append((inc, best, L))
    boom = cfg["boom"]
    print("#### Взлом глазами владельца и вора (обычный игрок; доход и лучший экспонат — в моменты Судных ночей)")
    print("| Уровень музея | доход владельца/с | взлом | = мин дохода | ловушка + лазер = мин дохода | дверь = мин дохода | все 4 = доля дохода между Судными ночами | лучший экспонат /с | взлом окупается за | поймать такой же Legendary / Secret Мегой (ожидаемая цена Ловибумов) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for ml in range(4, 11):
        if ml not in by:
            continue
        inc = statistics.median([x[0] for x in by[ml]])
        best = statistics.median([x[1] for x in by[ml]])
        L = int(statistics.median([x[2] for x in by[ml]]))
        H = cfg["hack"][ml - 1]
        leg = 3 * boom[L] / (0.70 * min(1, 0.14 * 2))
        sec = 3 * boom[L] / (0.70 * min(1, 0.06 * 2))
        alt = f"босс {L}: {short(leg)}" + (f" / {short(sec)}" if L >= 8 else " / —")
        print(f"| {ml} | {short(inc)} | {short(H)} | {H / inc / 60:.1f} | {0.25 * H / inc / 60:.1f} | {0.2 * H / inc / 60:.1f} | "
              f"{0.75 * H / (inc * CYCLE) * 100:.0f} % | {short(best)} | {fh(H / best)} | {alt} |")
    print()


def deadlocks(all_runs, cfg):
    print("| Игрок | босс 7 | босс 8 | босс 9 | босс 10 | дошли до босса 10 | самое долгое ожидание денег на Ловибум | самый низкий доход после кражи (доля от дохода при входе в этап) |")
    print("|---|---|---|---|---|---|---|---|")
    for name, rs in all_runs.items():
        cells = []
        for L in range(7, 11):
            at = arrivals(rs, cfg, L)
            m, p9 = statistics.median(at), pct(at, 0.9)
            cells.append(f"{m:.1f} ({p9:.1f})" if math.isfinite(p9) else (f"{m:.1f} (—)" if math.isfinite(m) else "—"))
        reach = sum(1 for r in rs if done(r[0], 9, cfg)) / len(rs)
        waits = [max(p["max_wait"] for p in r[0]) for r in rs]
        low = [min(p["min_income"] / max(p["arrive_income"], 1) for p in r[0] if p["L"] >= 2) for r in rs]
        print(f"| {name} | " + " | ".join(cells) + f" | {reach * 100:.0f} % | {pct(waits, 0.9) / 60:.1f} мин | "
              f"{pct(low, 0.1) * 100:.0f} % |")
    print()


if __name__ == "__main__":
    cfg = g["load"](NAME)
    old = g["load"]("econ84b_design.json")
    N = 300
    params(cfg, old)
    typ = runs(cfg, g["TYP"], N, 7)
    skl = runs(cfg, g["SKL"], 200, 8)
    unl = runs(cfg, g["UNL"], 200, 9)
    three = {"обычный": typ, "опытный": skl, "неудачливый": unl}
    progression(three, cfg)
    tables(typ, cfg)
    defense(three, cfg)
    hack_table(typ, cfg)
    print("### Тупики и устойчивость")
    wst = runs(cfg, g["WORST"], 150, 10, cap=1500)
    deadlocks({**three, "худший случай": wst}, cfg)
    print("Проверки стратегий (обычный игрок), приход к боссам 7 / 8 / 9 / 10, ч:")
    for label, kw in (("не тренируется в Судную ночь (ворует или обороняется)", dict(train_doom=False)),
                      ("всё в гантели: уровни музея выше 4 не покупает", dict(policy="no_museum"))):
        rs = runs(cfg, g["TYP"], 150, 7, cap=1500, **kw)
        print(f"- {label}: " + " / ".join(f"{statistics.median(arrivals(rs, cfg, L)):.1f}" for L in (7, 8, 9, 10)))
    for label, sc in (("обычный без защиты совсем", g["Sc"]("x", 0.70, 0.25, g["TYP"].kinds, 0.30, (), 0)),
                      ("обычный, защита каждую ночь любой ценой (ловушка + лазер)", g["Sc"]("x", 0.70, 0.25, g["TYP"].kinds, 0.30, ("Trap", "Laser"), 1e9)),
                      ("обычный, все 4 устройства каждую ночь", g["Sc"]("x", 0.70, 0.25, g["TYP"].kinds, 0.30, ("Door", "Trap", "Laser", "Robot"), 1e9))):
        rs = runs(cfg, sc, 150, 7, cap=1500)
        ok = [r for r in rs if done(r[0], 9, cfg)]
        lost = med([sum(p["lost"] for p in r[0][:9]) for r in ok])
        share = med([sum(p["def"] for p in r[0][6:9]) / max(sum(p["earned"] for p in r[0][6:9]), 1) for r in ok])
        print(f"- {label}: " + " / ".join(f"{statistics.median(arrivals(rs, cfg, L)):.1f}" for L in (7, 8, 9, 10))
              + f"; украдено до босса 10: {lost:.0f}; на защиту на этапах 7–9: {share * 100:.1f} % заработка")

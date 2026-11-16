"""Король-дракон №10, этап C.1: исправление дёргания передних лап (прежде всего левой) в клипах anim5.

Причина (найдена в данных клипа, подтверждена замером в Play и подсчётом касаний, режим diag): наручи не должны уходить
в корпус, поэтому в кадрах с касанием локоть лапы отводится наружу (канал F<сторона>_bend; подбор 0–50° в
bracer_resolve и доводка 8/16/24° в exact_fixes). Норма касаний в bracer_resolve бралась только из стойки «стоя»
(0 пар), а в утверждённой боевой стойке левый наруч уже касается корпуса (4 пары; правый — 0). При каждом вдохе боевой
стойки касание то есть, то нет, и подбор бросал левый локоть то на 0°, то на 50° (последний угол перебора — касание
отвод не убирает). Сглаживание «max(среднее по окну, сырое значение)» превращало это в рывки: левое плечо до 10° за
кадр (в игре, где стойка через кадр, до 25° за шаг), правое — 1.5°.

Исправление — только поправка наручей:
1) норма касаний — наибольшая из стоек «стоя» и боевой (как уже было в exact_fixes);
2) если ни один угол касание не убрал — наименьший угол с наименьшим числом касаний, и только если он лучше, чем без
   отвода (раньше — всегда 50°);
3) сглаживание — огибающая с ограниченной скоростью изменения (не меньше сырой поправки ни в одном кадре; меняется не
   быстрее SLEW градусов за кадр, углы скруглены) — и для подбора, и для доводки.
Всё остальное — anim5 без изменений (модуль подменяет функции v7_anim5 до расчёта клипов; сам v7_anim5.py
не меняется).

Режимы (после «-- <репо> <папка>»):
- raw — сырые поправки наручей по клипам (печать);
- export — игровые данные с исправлением: assets/models/Boss10_Dragon.{rig,anim}.json (прежние сохраняются в
  assets/models/backup_anim5/), как v7_export.py data.

- check — касания по клипам игры (<папка>/anim_report.json; с PAW_ORIG=1 — без исправления, для сравнения);
- diag — число касаний наруча с корпусом при каждом угле отвода (печать).

  blender --background --factory-startup --python scripts/blender/dragon10/v7_paw_fix.py -- <репо> <папка> <режим>
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import v7_anim5 as A  # noqa: E402

SLEW = float(os.environ.get("PAW_SLEW", "3"))  # градусов поправки за кадр (30 к/с) — 90°/с (в anim5 — до 10° за кадр)
MODE = A.MODE
RAW = {}


def envelope(raw, loop, slew=SLEW, pin=False):
    """Наименьшая кривая ≥ raw (по модулю, знак — по наибольшему), меняющаяся не быстрее slew за кадр; углы скруглены
    (среднее трёх соседних по кривой, построенной для расширенной на ±1 кадр сырой поправки — тоже не меньше raw).
    pin — у цикла, который начинается и кончается позой combat (шаги разворота): на краях отвод 0, скорость — не меньше
    той, с которой он успевает вырасти к нужному кадру."""
    n = len(raw)
    if not any(raw):
        return list(raw)
    sign = 1.0 if max(raw, key=abs) >= 0 else -1.0
    r = [abs(v) for v in raw]
    if loop and not pin and sum(1 for v in r if v) >= n // 2:
        # цикл, где отвод нужен бо́льшую часть времени (сон): отвод постоянный — наибольший нужный, локоть не ходит
        # туда-сюда на каждом вдохе
        return [sign * max(r)] * n
    idx = (lambda f: f % n) if loop else (lambda f: min(max(f, 0), n - 1))
    wide = [max(r[idx(f + j)] for j in (-1, 0, 1)) for f in range(n)]
    if pin and wide[0] == 0 and wide[n - 1] == 0:
        slew = max([slew] + [wide[f] / f for f in range(1, n)] + [wide[f] / (n - 1 - f) for f in range(n - 1)])
    else:
        pin = False
    e = list(wide)
    for _ in range(2 if loop else 1):  # у цикла — два круга, чтобы ограничение прошло через стык
        for f in range(n):
            if f > 0 or loop:
                e[f] = max(e[f], e[idx(f - 1)] - slew)
        for f in range(n - 1, -1, -1):
            if f < n - 1 or loop:
                e[f] = max(e[f], e[idx(f + 1)] - slew)
    out = [(e[idx(f - 1)] + e[f] + e[idx(f + 1)]) / 3 for f in range(n)]
    if pin:
        out[0] = out[n - 1] = 0.0
    return [sign * v for v in out]


def pinned(clip):
    return bool(clip.loop and getattr(clip, "start", None))


def bracer_resolve(rg, clip, poses):
    """Как v7_anim5.bracer_resolve (тот же подбор угла по касанию), но поправка — огибающая envelope()."""
    rig = getattr(rg, "rig", None)
    if rig is None:
        return
    me = rig["dragon"].data
    polys = [list(pl.vertices) for pl in me.polygons]
    tags = rig["tags"]
    arm = {x: [polys[i] for i in tags["bracer" + x]] for x in "LR"}
    body = [polys[i] for i in tags["body"]]
    if not hasattr(rg, "bracer_base2"):
        # норма касаний — наибольшая из стойки «стоя» и боевой стойки (как в exact_fixes): в утверждённой боевой
        # стойке левый наруч уже касается корпуса (4 пары против 0 «стоя»), это не ошибка кадра
        base = {x: 0 for x in "LR"}
        for pose in (A.STAND, A.COMBAT):
            A.show(rg, rig, dict(pose))
            co = A.eval_points(rig["dragon"]).tolist()
            bt = A.BVHTree.FromPolygons(co, body)
            for x in "LR":
                base[x] = max(base[x], len(A.BVHTree.FromPolygons(co, arm[x]).overlap(bt)))
        rg.bracer_base2 = base
    n = len(poses)
    raw = {x: [0.0] * n for x in "LR"}
    for f, (p, lag) in enumerate(poses):
        k = {x: 0 for x in "LR"}
        seen = {x: [] for x in "LR"}  # (касаний, номер угла) по опробованным углам
        while True:
            q = dict(p)
            for x in "LR":
                q[f"F{x}_bend"] += A.BEND_TRY[k[x]]
            A.show(rg, rig, q, lag)
            co = A.eval_points(rig["dragon"]).tolist()
            bt = A.BVHTree.FromPolygons(co, body)
            bad = []
            for x in "LR":
                c = len(A.BVHTree.FromPolygons(co, arm[x]).overlap(bt))
                if not seen[x] or seen[x][-1][1] != k[x]:
                    seen[x].append((c, k[x]))
                if c > rg.bracer_base2[x] + 2 and k[x] < len(A.BEND_TRY) - 1:
                    bad.append(x)
            if not bad:
                break
            for x in bad:
                k[x] += 1
        for x in "LR":
            c_last, k_last = seen[x][-1]
            if c_last > rg.bracer_base2[x] + 2:
                # ни один угол не убрал касание: наименьший угол с наименьшим числом касаний, и только если он
                # лучше, чем без отвода (иначе локоть бросался бы на 50° без пользы)
                best = min(seen[x], key=lambda ck: (ck[0], ck[1]))
                k_last = best[1] if best[0] < seen[x][0][0] else 0
            raw[x][f] = A.BEND_TRY[k_last]
    RAW.setdefault(clip.name, {})["resolve"] = {x: list(raw[x]) for x in "LR"}
    for x in "LR":
        if not any(raw[x]):
            continue
        env = envelope(raw[x], clip.loop, pin=pinned(clip))
        for f, (p, lag) in enumerate(poses):
            p[f"F{x}_bend"] += env[f]


def exact_fix_raw(rg, clip, poses, measure, cands):
    """Как v7_anim5.exact_fix, но возвращает сырые поправки по кадрам (без применения)."""
    rig = rg.rig
    raw = [None] * len(poses)
    for f, (p, lag) in enumerate(poses):
        A.show(rg, rig, p, lag)
        bad0 = measure(A.eval_points(rig["dragon"]))
        if bad0 <= 0:
            continue
        best = (bad0, None)
        for c in cands(p, bad0):
            q, lg = dict(p), dict(lag)
            for k, v in c.items():
                A._add(q, lg, k, v)
            A.show(rg, rig, q, lg)
            b = measure(A.eval_points(rig["dragon"]))
            if b < best[0]:
                best = (b, c)
            if b <= 0:
                break
        raw[f] = best[1]
    return raw


def exact_fixes(rg, clip, poses, smooth=True):
    """v7_anim5.exact_fixes без изменений для рогов и пола; для наручей — та же доводка, огибающая вместо окна."""
    rig = rg.rig
    if not hasattr(rg, "exact_base"):
        A.show(rg, rig, dict(A.STAND))
        c1 = A.eval_points(rig["dragon"])
        A.show(rg, rig, dict(A.COMBAT))
        c2 = A.eval_points(rig["dragon"])
        rg.exact_base = {f"{a}|{b}": max(A.pair_count(rig, c1, a, b), A.pair_count(rig, c2, a, b))
                         for a, b in (("horns", "wingL"), ("horns", "wingR"), ("tail", "hindlegL"), ("tail", "hindlegR"))}
        for x in "LR":
            rg.exact_base[f"bracer|{x}"] = max(A.pair_count(rig, c1, "bracer" + x, "body"),
                                               A.pair_count(rig, c2, "bracer" + x, "body"))
    for x in "LR":
        allow = rg.exact_base[f"horns|wing{x}"]
        A.exact_fix(rg, clip, poses,
                    lambda co, x=x, allow=allow: max(0, A.pair_count(rig, co, "horns", "wing" + x) - allow),
                    lambda p, bad, x=x: [{f"w{x}_sweep": 5.0}, {f"w{x}_sweep": -5.0}, {f"w{x}_raise": -5.0},
                                         {f"w{x}_raise": 5.0}, {f"w{x}_sweep": 10.0}, {f"w{x}_sweep": -10.0},
                                         {f"w{x}_raise": -10.0}, {f"w{x}_sweep": 10.0, f"w{x}_raise": -8.0},
                                         {f"w{x}_sweep": 16.0}, {f"w{x}_raise": -16.0}], "horns|wing" + x, smooth)
    for x, s in ((("L", 1.0), ("R", -1.0)) if smooth else ()):
        allow = rg.exact_base.get(f"bracer|{x}", 0) + 2

        def cands(p, bad, x=x, s=s):
            out = [{f"F{x}_bend": 8.0}, {f"F{x}_bend": 16.0}, {f"F{x}_bend": 24.0}]
            if p[f"F{x}_z"] > A.COMBAT[f"F{x}_z"] + 0.15:
                out += [{f"F{x}_x": 0.15 * s}, {f"F{x}_x": 0.3 * s}, {f"F{x}_x": 0.3 * s, f"F{x}_bend": 16.0}]
            return out
        raw = exact_fix_raw(rg, clip, poses,
                            lambda co, x=x, allow=allow: max(0, A.pair_count(rig, co, "bracer" + x, "body") - allow),
                            cands)
        RAW.setdefault(clip.name, {})[f"exact_{x}"] = [dict(c) if c else {} for c in raw]
        for key in (f"F{x}_bend", f"F{x}_x"):
            series = [(c or {}).get(key, 0.0) for c in raw]
            if not any(series):
                continue
            # сдвиг лапы (F_x) — с той же скоростью по доле от наибольшего, угол — SLEW
            peak = max(abs(v) for v in series)
            slew = SLEW if key.endswith("bend") else SLEW / 24.0 * peak
            env = envelope(series, clip.loop, slew, pin=pinned(clip))
            for f, (p, lag) in enumerate(poses):
                A._add(p, lag, key, env[f])
    for leg, keyz in (("forelegL", "FL_z"), ("forelegR", "FR_z"), ("hindlegL", "HL_z"), ("hindlegR", "HR_z")):
        A.exact_fix(rg, clip, poses,
                    lambda co, leg=leg: max(0.0, A.FIX_FLOOR - float(co[A.tverts(rig, leg), 2].min())),
                    lambda p, bad, keyz=keyz: [{keyz: bad + 0.01}, {keyz: 2 * bad + 0.02}, {"body_z": bad + 0.01},
                                               {keyz: bad + 0.01, "body_z": bad + 0.01}], "floor " + leg, smooth)


_exact_fix0 = A.exact_fix


def exact_fix_logged(rg, clip, poses, measure, cands, label, smooth=True):
    """v7_anim5.exact_fix без изменений; кадры, где доводка сработала, — в RAW (для отчёта)."""
    before = [dict(p) for p, _ in poses]
    _exact_fix0(rg, clip, poses, measure, cands, label, smooth)
    hit = [f for f, (p, _) in enumerate(poses)
           if any(isinstance(v, float) and abs(v - before[f].get(k, v)) > 1e-9 for k, v in p.items())]
    if hit:
        RAW.setdefault(clip.name, {}).setdefault("other", []).append([label, smooth, hit])


# подмена в модуле anim5: clip_frames вызывает их по имени модуля (PAW_ORIG=1 — без подмены, для сравнения в check)
if not os.environ.get("PAW_ORIG"):
    A.bracer_resolve = bracer_resolve
    A.exact_fixes = exact_fixes
    A.exact_fix = exact_fix_logged


def diag(names=("combat_idle", "hit", "walk", "wake")):
    """Число пересечений наруча с корпусом по кадрам при каждом угле BEND_TRY (поправки наручей выключены)."""
    col, rig = A.setup()
    rg = A.Rig(rig["arm"])
    rg.samples = A.leg_samples(rig)
    rg.rig = rig
    me = rig["dragon"].data
    polys = [list(pl.vertices) for pl in me.polygons]
    tags = rig["tags"]
    arm = {x: [polys[i] for i in tags["bracer" + x]] for x in "LR"}
    body = [polys[i] for i in tags["body"]]

    def count(p, lag, x, bend):
        q = dict(p)
        q[f"F{x}_bend"] += bend
        A.show(rg, rig, q, lag)
        co = A.eval_points(rig["dragon"]).tolist()
        return len(A.BVHTree.FromPolygons(co, arm[x]).overlap(A.BVHTree.FromPolygons(co, body)))

    for pose in ("STAND", "COMBAT"):
        print("BASE", pose, {x: count(dict(getattr(A, pose)), None, x, 0.0) for x in "LR"}, flush=True)
    A.bracer_resolve = lambda rg, clip, poses: None
    for make in A.CLIPS:
        clip = make()
        if clip.name not in names:
            continue
        times = [i / A.FPS for i in range(clip.frames())]
        poses = [A.pose_at(clip, t) for t in times]
        A.horn_clearance(rg, clip, poses)
        for f in range(0, len(poses), 3):
            p, lag = poses[f]
            print("DIAG", clip.name, f, {x: [count(p, lag, x, b) for b in A.BEND_TRY] for x in "LR"}, flush=True)


def main():
    if MODE == "diag":
        diag()
    elif MODE == "check":
        # касания и выход за пол по клипам игры (как v7_anim5 check) → <папка>/anim_report.json
        import v7_export as E
        col, rig = A.setup()
        rg = A.Rig(rig["arm"])
        rg.samples = A.leg_samples(rig)
        rg.rig = rig
        clips = [c for c in A.CLIPS if c().name != "turn_left"] + [lambda: E.turn_step("left"),
                                                                   lambda: E.turn_step("right")]
        A.run_check(rig, rg, clips)
    elif MODE == "raw":
        col, rig = A.setup()
        rg = A.Rig(rig["arm"])
        rg.samples = A.leg_samples(rig)
        rg.rig = rig
        for make in A.CLIPS:
            clip = make()
            A.clip_frames(rg, clip)
            r = RAW.get(clip.name, {})
            res = r.get("resolve", {})
            ex = {x: [round((c or {}).get(f"F{x}_bend", 0.0)) for c in r.get(f"exact_{x}", [])] for x in "LR"}
            print("RAW", clip.name, "resolve L", [int(v) for v in res.get("L", [])], "| resolve R",
                  [int(v) for v in res.get("R", [])], "| exact L", ex["L"], "| exact R", ex["R"], flush=True)
    elif MODE == "export":
        models = os.path.join(A.REPO, "assets", "models")
        backup = os.path.join(models, "backup_anim5")
        os.makedirs(backup, exist_ok=True)
        for name in ("Boss10_Dragon.rig.json", "Boss10_Dragon.anim.json"):
            dst = os.path.join(backup, name)
            if not os.path.exists(dst):
                shutil.copy(os.path.join(models, name), dst)
        import v7_export as E  # тот же модуль anim5 (уже с подменой) — экспорт как в этапе A
        col, rig = A.setup()
        rg = A.Rig(rig["arm"])
        rg.samples = A.leg_samples(rig)
        rg.rig = rig
        E.export_data(col, rig, rg)
        dump = os.environ.get("PAW_RAW_JSON")  # сырые поправки по клипам — для отчёта
        if dump:
            import json
            with open(dump, "w", encoding="utf-8") as fh:
                json.dump(RAW, fh, ensure_ascii=False)
        print("PAWFIX_EXPORT_OK", SLEW, flush=True)


if __name__ == "__main__":
    main()

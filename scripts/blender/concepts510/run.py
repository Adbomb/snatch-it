"""Кадры концептов боссов 5–10 (черновые блочные модели, без запекания и экспорта).

Запуск: blender --background --factory-startup --python scripts/blender/concepts510/run.py -- <репо> <задача>
Задачи: boss:<N> — виды спереди/сбоку/сзади/3-4, атаки, сон; arena:<N> — арена с ракурса игрока и зона сверху;
creatures:<N> — 10 существ по одному; lineup — шесть боссов, Сфинкс-силуэт и манекен рядом.
Кадры — assets/concepts/bosses_5_10/raw/<задача>/.
"""

import importlib
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ck  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, TASK = os.path.abspath(argv[0]), argv[1]
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "raw", TASK.replace(":", "_"))
os.makedirs(OUT, exist_ok=True)


def expose(mod):
    bpy.context.scene.view_settings.exposure = getattr(mod, "EXPOSURE", 0.0)


def boss_task(n):
    mod = importlib.import_module(f"boss{n}")
    # виды в боевой стойке
    col = ck.reset_scene()
    objs = mod.build(col, "idle")
    lo, hi = ck.bounds(objs)
    size = max(hi - lo)
    cam = ck.studio(col, size=max(1.0, size / 6.0))
    expose(mod)
    ck.turn_shots(cam, objs, OUT, f"boss{n}", res=(800, 1000), lens=60)
    cz = (lo.z + hi.z) / 2
    dist = 1.75 * size + 1.0
    ck.shot(cam, os.path.join(OUT, f"boss{n}_hero.png"), (-0.62 * dist, -0.85 * dist, cz + 0.45 * size),
            (0, 0, cz - 0.05 * size), 60, (1100, 1100))
    ck.shot(cam, os.path.join(OUT, f"boss{n}_face.png"), (0, -0.9 * dist, hi.z - 0.12 * size),
            (0, 0, hi.z - 0.2 * size), 85, (900, 900))
    # позы: атаки и сон — 3/4
    for pose in ("attack1", "attack2", "sleep"):
        col = ck.reset_scene()
        objs = mod.build(col, pose)
        lo, hi = ck.bounds(objs)
        size = max(hi - lo)
        cam = ck.studio(col, size=max(1.0, size / 6.0))
        expose(mod)
        cz = (lo.z + hi.z) / 2
        dist = 1.7 * size + 1.0
        ck.shot(cam, os.path.join(OUT, f"boss{n}_{pose}.png"), (-0.55 * dist, -0.85 * dist, cz + 0.3 * size),
                (0, 0, cz), 60, (1000, 1000))


def arena_task(n):
    import arenas  # noqa: E402

    arenas.render(n, OUT)


def creatures_task(n):
    mod = importlib.import_module(f"creatures{n}")
    for i, (cid, name, rarity, fn) in enumerate(mod.CREATURES):
        col = ck.reset_scene()
        objs = fn(col)
        lo, hi = ck.bounds(objs)
        size = max(hi - lo)
        cam = ck.studio(col, size=max(0.5, size / 3.0))
        expose(mod)
        cz = (lo.z + hi.z) / 2
        dist = 2.6 * size + 0.6
        ck.shot(cam, os.path.join(OUT, f"{i + 1:02d}_{cid}.png"), (-0.55 * dist, -0.85 * dist, cz + 0.35 * size),
                (0, 0, cz), 60, (700, 700))


def reference(col):
    """Масштаб: габарит Сфинкса в игре (13.3 × 16.8 стада / 3) и игрок (≈ 5 стадов / 3) — в единицах моделей."""
    a = ck.new_art("Refs")
    a.paint("ghost", "8A90A6")
    a.paint("player", "FFD23F")
    a.paint("shirt", "2F6BFF")
    a.paint("pants", "26355E")
    a.prism("ghost", ck.octa((0, 0), 13.29 / 3, 2.6, 0.0, 16.77 / 3, cut=0.4)[0], 0.0, 16.77 / 3)
    for s in (1, -1):
        a.box("pants", 3.6 + s * 0.13 - 0.12, 3.6 + s * 0.13 + 0.12, -0.12, 0.12, 0.0, 0.62)
        a.box("player", 3.6 + s * 0.38 - 0.11, 3.6 + s * 0.38 + 0.11, -0.12, 0.12, 0.62, 1.2)
    a.box("shirt", 3.35, 3.85, -0.13, 0.13, 0.62, 1.25)
    a.box("player", 3.45, 3.75, -0.15, 0.15, 1.25, 1.62)
    obj = ck.finish(a, col)
    return obj


def lineup_task():
    import json

    col = ck.reset_scene()
    ref = reference(col)
    ref.location.x = -4.0
    items = [("ref", -4.0 + 1.8, 16.77 / 3)]
    x = 1.0
    for n in (5, 6, 7, 8, 9, 10):
        mod = importlib.import_module(f"boss{n}")
        objs = mod.build(col, "idle")
        lo, hi = ck.bounds(objs)
        w = hi.x - lo.x
        x += w / 2 + 1.0
        for o in objs:
            o.location.x += x - (lo.x + hi.x) / 2
        items.append((n, x, hi.z))
        x += w / 2 + 1.0
    left, right = -6.5, x
    cx = (left + right) / 2
    for o in col.objects:
        o.location.x -= cx
    cam = ck.studio(col, size=4.0)
    lens, res = 50, (2600, 900)
    half = (right - left) / 2 + 1.0
    dist = half / (18.0 / lens)
    cz = 5.0
    ck.shot(cam, os.path.join(OUT, "lineup.png"), (0, -dist, cz + 1.0), (0, 0, cz), lens, res)
    f_px = lens / 36.0 * res[0]
    marks = [{"id": str(n), "u": res[0] / 2 + f_px * (bx - cx) / dist, "top": top} for n, bx, top in items]
    json.dump(marks, open(os.path.join(OUT, "lineup.json"), "w"))


if TASK.startswith("boss:"):
    boss_task(int(TASK.split(":")[1]))
elif TASK.startswith("arena:"):
    arena_task(int(TASK.split(":")[1]))
elif TASK.startswith("creatures:"):
    creatures_task(int(TASK.split(":")[1]))
elif TASK == "lineup":
    lineup_task()
print("DONE", TASK, OUT, flush=True)

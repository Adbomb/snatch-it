"""Кадры Короля-дракона v3 (стиль D39): однотонно, в цвете с квадратами-контурами D39, крупные планы, счёт.

Запуск: blender --background --factory-startup --python scripts/blender/dragon10/render_d39.py -- <репо> <задача>
Задачи: clay, color, close, sphinx (Сфинкс и дракон рядом, один свет), all. Кадры и stats.json —
assets/concepts/bosses_5_10/boss10_v3/raw/. Материалы — art_style (как у концептов Сфинкса до запекания).
"""

import json
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "concepts510"))
import ck  # noqa: E402
import dragon_d39 as D  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
REPO, TASK = os.path.abspath(argv[0]), argv[1]
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss10_v3", "raw")
os.makedirs(OUT, exist_ok=True)


def scene(clay, quality="hero"):
    col = ck.reset_scene()
    art = D.build(quality)
    obj = art.build(col)
    if clay:
        m = bpy.data.materials.new("Clay")
        m.use_nodes = True
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = (0.27, 0.25, 0.23, 1)
        b.inputs["Roughness"].default_value = 0.6
        for i in range(len(obj.data.materials)):
            obj.data.materials[i] = m
    cam = ck.studio(col, size=1.9, bg=(0.72, 0.74, 0.8))
    bpy.context.scene.view_settings.exposure = -0.55 if clay else -0.2
    return art, obj, cam


def stats(art, obj, name="stats"):
    per = {}
    for poly, g in zip(obj.data.polygons, art.face_groups):
        per[g] = per.get(g, 0) + len(poly.vertices) - 2
    obj.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    lo, hi = ck.bounds([obj])
    data = dict(art.stats, per_part=per, parts=len(per), size=[round(hi.x - lo.x, 2), round(hi.y - lo.y, 2),
                                                               round(hi.z - lo.z, 2)])
    with open(os.path.join(OUT, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("STATS", {k: data[k] for k in ("tris", "parts", "coplanar", "flipped", "degenerate", "size")}, flush=True)


def views(obj, cam, prefix):
    lo, hi = ck.bounds([obj])
    h, cz = hi.z - lo.z, (lo.z + hi.z) / 2
    for label, ang in (("front", 0), ("side", -90), ("back", 180), ("34", -35)):
        obj.rotation_euler = (0, 0, math.radians(ang))
        span = max(h, (hi.x - lo.x) if ang in (0, 180, -35) else (hi.y - lo.y) + 1.0)
        dist = 1.12 * span / (2 * (18 / 55))
        ck.shot(cam, os.path.join(OUT, f"{prefix}_{label}.png"), (0, -dist, cz + 0.12 * h), (0, 0, cz), 55, (1100, 1100))
    obj.rotation_euler = (0, 0, 0)


CLOSE = {
    "head": ((-3.6, -8.6, 10.9), (0, -1.2, 9.3), 55),
    "crown": ((-1.9, -4.6, 12.3), (0, -0.25, 10.75), 55),
    "armor": ((-3.6, -8.2, 6.6), (0.5, -0.5, 4.9), 55),
    "wing": ((5.5, 12.5, 12.5), (3.6, 3.0, 6.6), 45),
    "tail": ((7.4, -2.6, 2.9), (3.5, 1.6, 0.6), 50),
}

if TASK in ("clay", "all"):
    art, obj, cam = scene(True)
    views(obj, cam, "clay")
    stats(art, obj)
if TASK in ("color", "all"):
    art, obj, cam = scene(False)
    views(obj, cam, "color")
if TASK in ("close", "all"):
    art, obj, cam = scene(False)
    for name, (eye, target, lens) in CLOSE.items():
        ck.shot(cam, os.path.join(OUT, f"close_{name}.png"), eye, target, lens, (1100, 1100))
if TASK in ("game", "all"):  # игровая копия: счёт и кадры для сравнения
    art, obj, cam = scene(False, "game")
    stats(art, obj, "stats_game")
    lo, hi = ck.bounds([obj])
    cz = (lo.z + hi.z) / 2
    obj.rotation_euler = (0, 0, math.radians(-35))
    ck.shot(cam, os.path.join(OUT, "game_34.png"), (0, -21.0, cz + 1.3), (0, 0, cz), 55, (1100, 1100))
    obj.rotation_euler = (0, 0, 0)
    ck.shot(cam, os.path.join(OUT, "game_head.png"), *CLOSE["head"][:2], CLOSE["head"][2], (1100, 1100))
print("DONE", TASK, OUT, flush=True)

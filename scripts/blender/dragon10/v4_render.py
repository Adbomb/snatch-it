"""Кадры силуэтов Короля-дракона v4 (этап A): три варианта в одном нейтральном материале, один свет, один масштаб.

Запуск: blender --background --factory-startup --python scripts/blender/dragon10/v4_render.py -- <репо>
Кадры: assets/concepts/bosses_5_10/boss10_v4/raw/ — {A,B,C}_{front,side,34}.png, те же *_sil.png (прозрачный фон,
для чёрных силуэтов), lineup_34.png, lineup_front.png, lineup_side.png, stats.json.
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
import v4_dragons as D  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
REPO = os.path.abspath(argv[0])
ONLY = argv[1] if len(argv) > 1 else "ABC"
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss10_v4", "raw")
os.makedirs(OUT, exist_ok=True)
LENS = 55
TANH = 18 / LENS
VIEWS = (("front", 0), ("side", -90), ("34", -35))


def clay():
    m = bpy.data.materials.new("Clay")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.27, 0.25, 0.23, 1)
    b.inputs["Roughness"].default_value = 0.6
    return m


def place(fn, col, mat):
    art = fn()
    obj = art.build(col)
    for i in range(len(obj.data.materials)):
        obj.data.materials[i] = mat
    return art, obj


def setup(col):
    cam = ck.studio(col, size=2.2, bg=(0.72, 0.74, 0.8))
    bpy.context.scene.view_settings.exposure = -0.5
    return cam


def shot(cam, objs, path, dist, cz, sil):
    scene = bpy.context.scene
    floor = bpy.data.objects.get("Floor")
    ck.shot(cam, path + ".png", (0, -dist, cz + 1.2), (0, 0, cz), LENS, (1200, 1200))
    if sil:
        scene.render.film_transparent = True
        floor.hide_render = True
        ck.shot(cam, path + "_sil.png", (0, -dist, cz + 1.2), (0, 0, cz), LENS, (1200, 1200))
        scene.render.film_transparent = False
        floor.hide_render = False


def main():
    # общий масштаб: размеры всех трёх вариантов
    col = ck.reset_scene()
    mat = clay()
    dims, stats = {}, {}
    for k, (name, fn) in D.VARIANTS.items():
        art, obj = place(fn, col, mat)
        lo, hi = ck.bounds([obj])
        dims[k] = (lo, hi)
        stats[k] = {"name": name, "tris": art.stats["tris"], "size": [round(hi[i] - lo[i], 2) for i in range(3)]}
    span = max(max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z) for lo, hi in dims.values())
    cz = max(hi.z for lo, hi in dims.values()) / 2
    dist = 1.06 * span / (2 * TANH)
    with open(os.path.join(OUT, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats | {"common_span": round(span, 2)}, f, ensure_ascii=False, indent=1)
    print("STATS", stats, flush=True)

    for k, (name, fn) in D.VARIANTS.items():
        if k not in ONLY:
            continue
        col = ck.reset_scene()
        mat = clay()
        art, obj = place(fn, col, mat)
        lo, hi = dims[k]
        obj.location.x = -(lo.x + hi.x) / 2
        cam = setup(col)
        for label, ang in VIEWS:
            obj.rotation_euler = (0, 0, math.radians(ang))
            shot(cam, [obj], os.path.join(OUT, f"{k}_{label}"), dist, cz, sil=True)

    if ONLY not in ("ABC", "L"):
        return
    # все три рядом: спереди, 3/4 и сбоку в одном масштабе
    for label, ang in VIEWS:
        col = ck.reset_scene()
        mat = clay()
        objs = []
        for k, (name, fn) in D.VARIANTS.items():
            art, obj = place(fn, col, mat)
            objs.append((k, obj))
        gap = 1.5
        widths = []
        for k, obj in objs:
            obj.rotation_euler = (0, 0, math.radians(ang))
            bpy.context.view_layer.update()
            lo, hi = ck.bounds([obj])
            widths.append((obj, lo, hi))
        total = sum(hi.x - lo.x for _, lo, hi in widths) + gap * 2
        x = -total / 2
        for obj, lo, hi in widths:
            obj.location.x = x - lo.x
            x += (hi.x - lo.x) + gap
        bpy.context.view_layer.update()
        cam = ck.studio(col, size=4.0, bg=(0.72, 0.74, 0.8))
        bpy.context.scene.view_settings.exposure = -0.5
        d2 = 1.3 * max(total, span) / (2 * TANH)
        ck.shot(cam, os.path.join(OUT, f"lineup_{label}.png"), (0, -d2, cz + 1.2), (0, 0, cz), LENS, (2400, 1000))
    print("DONE", OUT, flush=True)


main()

"""Кадры Короля-дракона v6 и сравнение с v5 одними камерами.

Запуск: blender --background --factory-startup --python scripts/blender/dragon10/v6_render.py -- <репо>
Кадры: assets/concepts/bosses_5_10/boss10_v6/raw/ — v6_{front,side,back,34}.png, v6_head_{front,34}.png,
v6_{front,side,34}_sil.png, v5_{front,side,34}.png (те же камеры и масштаб), stats.json (габариты, треугольники,
масштаб под 35 стадов, размах крыльев).
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "concepts510"))
import ck  # noqa: E402
import v5_dragon  # noqa: E402
import v6_dragon  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
REPO = os.path.abspath(argv[0])
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss10_v6", "raw")
os.makedirs(OUT, exist_ok=True)
LENS = 55
TANH = 18 / LENS
TARGET_STUDS = 35.0
ARENA = 62.0


def clay(obj):
    m = bpy.data.materials.new("Clay")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.27, 0.25, 0.23, 1)
    b.inputs["Roughness"].default_value = 0.6
    for i in range(len(obj.data.materials)):
        obj.data.materials[i] = m


def scene_with(fn):
    col = ck.reset_scene()
    art = fn()
    obj = art.build(col)
    clay(obj)
    cam = ck.studio(col, size=2.4, bg=(0.72, 0.74, 0.8))
    bpy.context.scene.view_settings.exposure = -0.5
    return art, obj, cam


def main():
    art, obj, cam = scene_with(v6_dragon.dragon)
    lo, hi = ck.bounds([obj])
    size = [hi[i] - lo[i] for i in range(3)]
    offset = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, 0.0))  # общий сдвиг для v6 и v5
    k = TARGET_STUDS / size[2]
    stats = {"tris": art.stats["tris"], "size_model": [round(v, 2) for v in size],
             "export_scale": round(k, 3), "size_studs": [round(v * k, 1) for v in size],
             "wingspan_studs": round(size[0] * k, 1), "arena_diameter": ARENA}
    span = max(size)
    cz = (hi.z + lo.z) / 2
    dist = 1.08 * span / (2 * TANH)
    cams = {"front": 0, "side": -90, "34": -35, "back": 180}
    scene = bpy.context.scene
    floor = bpy.data.objects.get("Floor")
    obj.location = offset
    for label, ang in cams.items():
        obj.rotation_euler = (0, 0, math.radians(ang))
        ck.shot(cam, os.path.join(OUT, f"v6_{label}.png"), (0, -dist, cz + 1.4), (0, 0, cz), LENS, (1400, 1400))
        if label != "back":
            scene.render.film_transparent = True
            floor.hide_render = True
            ck.shot(cam, os.path.join(OUT, f"v6_{label}_sil.png"), (0, -dist, cz + 1.4), (0, 0, cz), LENS, (1400, 1400))
            scene.render.film_transparent = False
            floor.hide_render = False
    obj.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    head = Vector((0.0, -5.6, 10.0)) + offset
    ck.shot(cam, os.path.join(OUT, "v6_head_front.png"), head + Vector((0.0, -9.5, 0.6)), head, 55, (1400, 1400))
    ck.shot(cam, os.path.join(OUT, "v6_head_34.png"), head + Vector((-5.2, -7.2, 1.5)), head, 55, (1400, 1400))
    # v5 теми же камерами, тем же сдвигом и масштабом
    art5, obj5, cam5 = scene_with(v5_dragon.dragon)
    stats["tris_v5"] = art5.stats["tris"]
    obj5.location = offset
    for label in ("front", "side", "34"):
        obj5.rotation_euler = (0, 0, math.radians(cams[label]))
        ck.shot(cam5, os.path.join(OUT, f"v5_{label}.png"), (0, -dist, cz + 1.4), (0, 0, cz), LENS, (1400, 1400))
    obj5.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    ck.shot(cam5, os.path.join(OUT, "v5_head_front.png"), head + Vector((0.0, -9.5, 0.6)), head, 55, (1400, 1400))
    with open(os.path.join(OUT, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print("STATS", stats, flush=True)
    print("DONE", OUT, flush=True)


main()

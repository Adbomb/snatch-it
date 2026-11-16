"""Кадры Короля-дракона v5 (гибрид A+B, только форма): спереди, сбоку, 3/4, сзади, голова; силуэты; счёт.

Запуск: blender --background --factory-startup --python scripts/blender/dragon10/v5_render.py -- <репо>
Кадры: assets/concepts/bosses_5_10/boss10_v5/raw/ — {front,side,34,back,head}.png, {front,side,34}_sil.png, stats.json.
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
import v5_dragon as D  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
REPO = os.path.abspath(argv[0])
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss10_v5", "raw")
os.makedirs(OUT, exist_ok=True)
LENS = 55
TANH = 18 / LENS


def main():
    col = ck.reset_scene()
    art = D.dragon()
    obj = art.build(col)
    m = bpy.data.materials.new("Clay")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.27, 0.25, 0.23, 1)
    b.inputs["Roughness"].default_value = 0.6
    for i in range(len(obj.data.materials)):
        obj.data.materials[i] = m
    lo, hi = ck.bounds([obj])
    obj.location.x = -(lo.x + hi.x) / 2
    obj.location.y = -(lo.y + hi.y) / 2
    bpy.context.view_layer.update()
    lo, hi = ck.bounds([obj])
    size = [round(hi[i] - lo[i], 2) for i in range(3)]
    with open(os.path.join(OUT, "stats.json"), "w", encoding="utf-8") as f:
        json.dump({"tris": art.stats["tris"], "size": size}, f, ensure_ascii=False, indent=1)
    print("STATS", art.stats["tris"], size, flush=True)
    cam = ck.studio(col, size=2.4, bg=(0.72, 0.74, 0.8))
    scene = bpy.context.scene
    scene.view_settings.exposure = -0.5
    floor = bpy.data.objects.get("Floor")
    span = max(size)
    cz = (hi.z + lo.z) / 2
    dist = 1.08 * span / (2 * TANH)
    for label, ang in (("front", 0), ("side", -90), ("34", -35), ("back", 180)):
        obj.rotation_euler = (0, 0, math.radians(ang))
        ck.shot(cam, os.path.join(OUT, f"{label}.png"), (0, -dist, cz + 1.4), (0, 0, cz), LENS, (1400, 1400))
        if label != "back":
            scene.render.film_transparent = True
            floor.hide_render = True
            ck.shot(cam, os.path.join(OUT, f"{label}_sil.png"), (0, -dist, cz + 1.4), (0, 0, cz), LENS, (1400, 1400))
            scene.render.film_transparent = False
            floor.hide_render = False
    obj.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    t = Vector((0.0, -5.7, 10.0)) + obj.location  # голова в мировых координатах после центрирования
    ck.shot(cam, os.path.join(OUT, "head.png"), t + Vector((-4.2, -7.6, 1.8)), t, 50, (1400, 1400))
    print("DONE", OUT, flush=True)


main()

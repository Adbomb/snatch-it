"""Кадры Королевы-мухоловки (босс 6, концепт D64): позы стойка / сон / бой / поражение, силуэты, крупные планы, числа.

Запуск: blender --background --factory-startup --python scripts/blender/boss6/render.py -- <репо> <позы через запятую> [quick]
Кадры: assets/concepts/bosses_5_10/boss6_v2/raw/ (вне git):
- stand_{front,side,back,34}.png, stand_{front,side}_sil.png, head_{front,34}.png, collar.png, buds.png;
- sleep_34.png, combat_34.png, defeat_34.png (+ _front у боевых поз);
- stats.json — треугольники, габариты, масштаб в стадах.
Зависит от flytrap.py и concepts510/ck.py (студия, кадр).
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
import flytrap  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
REPO = os.path.abspath(argv[0])
POSES = argv[1].split(",") if len(argv) > 1 else ["stand"]
QUICK = "quick" in argv[2:]
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss6_v2", "raw")
os.makedirs(OUT, exist_ok=True)
RES = (800, 800) if QUICK else (1300, 1300)
LENS = 55
TARGET_STUDS = 24.0  # рост в стойке (с короной) — как у Йети
EXPOSURE = -0.3


def materials(art):
    """Золото металлическое, роса полупрозрачная, самоцветы — глянец."""
    for mat in art.materials:
        k = mat.name.rsplit("_", 1)[-1]
        b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b is None:
            continue
        if k.startswith("gold"):
            b.inputs["Metallic"].default_value = 0.45
            b.inputs["Roughness"].default_value = 0.32
        elif k == "dew":
            b.inputs["Roughness"].default_value = 0.08
            b.inputs["Alpha"].default_value = 0.6
            try:
                mat.surface_render_method = "BLENDED"
            except AttributeError:
                mat.blend_method = "BLEND"
            mat.use_backface_culling = True  # одна грань льда на луч — экспонаты внутри не выцветают
            try:
                mat.use_transparency_overlap = False
            except AttributeError:
                pass
        elif k == "gemD":
            b.inputs["Roughness"].default_value = 0.15


def build(col, pose):
    art = flytrap.flytrap(pose)
    obj = ck.finish(art, col, glow=4.0)
    obj.name = f"Flytrap_{pose}"
    materials(art)
    return art, obj


def main():
    stats = {}
    for pose in POSES:
        col = ck.reset_scene()
        art, obj = build(col, pose)
        cam = ck.studio(col, size=1.5, bg=(0.7, 0.76, 0.86))
        bpy.context.scene.view_settings.exposure = EXPOSURE
        lo, hi = ck.bounds([obj])
        size = hi - lo
        obj.location = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
        bpy.context.view_layer.update()
        span = max(size.x, size.z, 9.0)
        cz = size.z / 2
        dist = 1.12 * span / (2 * 18 / LENS)
        views = {"front": 0, "34": -35, "side": -90}
        if pose == "stand" and not QUICK:
            views.update({"side": -90, "back": 180})
        if pose != "stand":
            views = {"34": -35} if QUICK else {"34": -35, "front": 0}
        for label, ang in views.items():
            obj.rotation_euler = (0, 0, math.radians(ang))
            bpy.context.view_layer.update()
            ck.shot(cam, os.path.join(OUT, f"{pose}_{label}.png"), (0, -dist, cz + 1.6), (0, 0, cz), LENS, RES)
            if pose == "stand" and label in ("front", "side") and not QUICK:
                scene = bpy.context.scene
                scene.render.film_transparent = True
                bpy.data.objects["Floor"].hide_render = True
                ck.shot(cam, os.path.join(OUT, f"{pose}_{label}_sil.png"), (0, -dist, cz + 1.6), (0, 0, cz), LENS, RES)
                scene.render.film_transparent = False
                bpy.data.objects["Floor"].hide_render = False
        obj.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
        if pose == "stand":
            # голова — по самой высокой точке маски (группа Head), пояс и глыба
            head = [obj.matrix_world @ obj.data.vertices[i].co for p, g in zip(obj.data.polygons, art.face_groups)
                    if g == "Head" for i in p.vertices]
            hc = Vector([sum(v[i] for v in head) / len(head) for i in range(3)])
            ck.shot(cam, os.path.join(OUT, "head_front.png"), hc + Vector((0, -9.5, 0.6)), hc, 55, RES)
            ck.shot(cam, os.path.join(OUT, "head_34.png"), hc + Vector((-5.6, -7.8, 1.4)), hc, 55, RES)
            col_c = Vector((0, -0.5, hc.z - 2.6))
            ck.shot(cam, os.path.join(OUT, "collar.png"), col_c + Vector((-4.5, -8.0, 1.5)), col_c, 55, RES)
            bud = Vector((-5.6, -3.8, 1.0)) - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
            ck.shot(cam, os.path.join(OUT, "buds.png"), bud + Vector((-2.5, -6.0, 2.2)), bud, 55, RES)
        k = TARGET_STUDS / size.z if pose == "stand" else None
        stats[pose] = {"tris": art.stats["tris"], "coplanar": art.stats.get("coplanar"),
                       "flipped": art.stats.get("flipped"), "size_model": [round(v, 2) for v in size]}
        if k:
            stats["export_scale"] = round(k, 3)
    if "export_scale" in stats:
        for pose in POSES:
            stats[pose]["size_studs"] = [round(v * stats["export_scale"], 1) for v in stats[pose]["size_model"]]
    stats["palette"] = {kk: v[0] for kk, v in flytrap.PALETTE.items()}
    path = os.path.join(OUT, "stats.json" if not QUICK else "stats_quick.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print("STATS", json.dumps({p: stats[p] for p in POSES}, ensure_ascii=False), flush=True)
    print("DONE", OUT, flush=True)


main()

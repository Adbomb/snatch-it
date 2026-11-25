"""Кадры Королевы-мухоловки v2 (босс 6, концепт D64): позы стойка / сон / бой / поражение, силуэты, крупные планы, числа.

Запуск: blender --background --factory-startup --python scripts/blender/boss6/render.py -- <репо> <позы через запятую> [quick]
Кадры: assets/concepts/bosses_5_10/boss6_v2/raw/ (вне git):
- stand_{front,side,back,34}.png, stand_{front,side}_sil.png, head_{front,34}.png, collar.png (амулет на стебле),
  buds.png (закрытые бутоны-фрейлины), buds_combat.png (бутон раскрыт в бою);
- sleep_34.png, combat_34.png, defeat_34.png (+ _front у боевых поз);
- stats.json — треугольники (всего и по частям рига), детали, габариты, масштаб в стадах, палитра.
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


def group_points(obj, art, group):
    return [obj.matrix_world @ obj.data.vertices[i].co for p, g in zip(obj.data.polygons, art.face_groups)
            if g == group for i in p.vertices]


def centroid(pts):
    return Vector([sum(v[i] for v in pts) / len(pts) for i in range(3)])


def tris_by_group(obj, art):
    """Треугольники по частям рига — видно, где тратится бюджет игровой копии."""
    me = obj.data
    me.calc_loop_triangles()
    out = {}
    for t in me.loop_triangles:
        g = art.face_groups[t.polygon_index] or "-"
        out[g] = out.get(g, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def build(col, pose):
    art = flytrap.flytrap(pose)
    obj = ck.finish(art, col, glow=4.0)
    obj.name = f"Flytrap_{pose}"
    materials(art)
    return art, obj


def main():
    # stats.json дополняется: прогон части поз не стирает числа остальных
    path = os.path.join(OUT, "stats.json" if not QUICK else "stats_quick.json")
    stats = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                stats = json.load(f)
        except (OSError, ValueError):
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
        dist = 1.3 * span / (2 * 18 / LENS)  # +6 %: розетка спереди входит в кадр целиком
        views = {"front": 0, "34": -35, "side": -90}
        if pose == "stand":
            views.update({"side": -90, "back": 180})
        if pose != "stand":
            views = {"34": -35} if QUICK else {"34": -35, "front": 0}
        for label, ang in views.items():
            obj.rotation_euler = (0, 0, math.radians(ang))
            bpy.context.view_layer.update()
            ck.shot(cam, os.path.join(OUT, f"{pose}_{label}.png"), (0, -dist, cz + 1.2), (0, 0, cz - 0.4), LENS, RES)
            if pose == "stand" and label in ("front", "side") and not QUICK:
                scene = bpy.context.scene
                scene.render.film_transparent = True
                bpy.data.objects["Floor"].hide_render = True
                ck.shot(cam, os.path.join(OUT, f"{pose}_{label}_sil.png"), (0, -dist, cz + 1.2), (0, 0, cz - 0.4),
                        LENS, RES)
                scene.render.film_transparent = False
                bpy.data.objects["Floor"].hide_render = False
        obj.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
        if pose == "stand":
            head = group_points(obj, art, "Head")
            hc = centroid(head)
            ck.shot(cam, os.path.join(OUT, "head_front.png"), hc + Vector((0, -9.5, 0.6)), hc, 55, RES)
            ck.shot(cam, os.path.join(OUT, "head_34.png"), hc + Vector((-5.6, -7.8, 1.4)), hc, 55, RES)
            # «collar.png» в v2 — амулет на стебле крупно (камера смотрит на медальон, а не на зубы)
            am = centroid(group_points(obj, art, "Amulet"))
            ck.shot(cam, os.path.join(OUT, "collar.png"), am + Vector((-3.6, -7.4, 0.6)), am + Vector((0, 0, 0.4)),
                    55, RES)
            # бутон целиком (стебелёк + чаша + яйцо): правый бутон, камера выше (~32°) и снаружи справа —
            # поднятая правая лоза и левая ладонь за кадром
            bud = centroid([p for p in group_points(obj, art, "Buds") if p.x > 0])
            ck.shot(cam, os.path.join(OUT, "buds.png"), bud + Vector((4.6, -4.4, 4.0)), bud + Vector((0, 0, 0.5)),
                    55, RES)
        if pose == "combat":  # раскрытый бутон-фрейлина в бою (тоже без лица)
            bud = centroid([p for p in group_points(obj, art, "Buds") if p.x > 0])
            ck.shot(cam, os.path.join(OUT, "buds_combat.png"), bud + Vector((4.6, -4.4, 4.0)),
                    bud + Vector((0, 0, 0.5)), 55, RES)
        k = TARGET_STUDS / size.z if pose == "stand" else None
        stats[pose] = {"tris": art.stats["tris"], "parts": art.stats["parts"],
                       "tris_by_group": tris_by_group(obj, art), "coplanar": art.stats.get("coplanar"),
                       "flipped": art.stats.get("flipped"), "size_model": [round(v, 2) for v in size]}
        if k:
            stats["export_scale"] = round(k, 3)
    if "export_scale" in stats:
        for pose in [p for p in flytrap.POSES if p in stats]:
            stats[pose]["size_studs"] = [round(v * stats["export_scale"], 1) for v in stats[pose]["size_model"]]
    stats["palette"] = {kk: v[0] for kk, v in flytrap.PALETTE.items()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print("STATS", json.dumps({p: stats[p] for p in POSES}, ensure_ascii=False), flush=True)
    print("DONE", OUT, flush=True)


main()

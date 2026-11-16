"""Кадры Короля-дракона v7 (королевское оформление) и сравнение с v6 одними камерами; .blend и числа.

Запуск: blender --background --factory-startup --python scripts/blender/dragon10/v7_render.py -- <репо> [quick]
Кадры: assets/concepts/bosses_5_10/boss10_v7/raw/:
- v7_{front,side,back,34}.png;
- v7_head_{front,34,side}.png, v7_chest.png, v7_scepter.png;
- v7_{front,side,34}_sil.png;
- v6_{front,side,34,head_front}.png — v6 в глине, те же камеры и масштаб;
- stats.json.
Модель: boss10_v7/boss10_v7.blend — дракон и скипетр отдельными объектами, группы вершин по частям рига.
Камеры и масштаб берутся по габаритам формы v6, поэтому сравнение честное.
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
import v6_dragon  # noqa: E402
import v7_dragon  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
REPO = os.path.abspath(argv[0])
QUICK = "quick" in argv[1:]
BOSS = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss10_v7")
OUT = os.path.join(BOSS, "raw")
os.makedirs(OUT, exist_ok=True)
LENS = 55
TANH = 18 / LENS
TARGET_STUDS = 35.0
ARENA = 62.0
RES = (900, 900) if QUICK else (1400, 1400)
EXPOSURE = -0.35


def clay(obj):
    m = bpy.data.materials.new("Clay")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.27, 0.25, 0.23, 1)
    b.inputs["Roughness"].default_value = 0.6
    for i in range(len(obj.data.materials)):
        obj.data.materials[i] = m


def metal(art):
    """Золото чуть металлическое, кристаллы — глянец: материал по ключу, цвет и кольца D39 не меняются."""
    for mat in art.materials:
        k = mat.name.split("_", 1)[-1]
        b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b is None:
            continue
        if k.startswith("gold"):
            b.inputs["Metallic"].default_value = 0.45
            b.inputs["Roughness"].default_value = 0.32
        elif k in ("neonCrystal", "crystalD"):
            b.inputs["Roughness"].default_value = 0.15


def rig_groups(obj, art):
    """Группы вершин по частям рига (Head, Jaw, Neck, Torso, ForeLegL…, MantleL1…, Scepter)."""
    names = sorted({g for g in art.face_groups if g})
    vg = {n: obj.vertex_groups.new(name=n) for n in names}
    for poly, g in zip(obj.data.polygons, art.face_groups):
        if g:
            vg[g].add(list(poly.vertices), 1.0, "REPLACE")
    return names


def group_tris(obj, art):
    out = {}
    for poly, g in zip(obj.data.polygons, art.face_groups):
        out[g or "-"] = out.get(g or "-", 0) + len(poly.vertices) - 2
    return out


def build_v7(col):
    art = v7_dragon.dragon(royal=True, with_scepter=False)
    obj = ck.finish(art, col, glow=5.0)
    obj.name = "KingDragon_v7"
    metal(art)
    sart = v7_dragon.new_art("Scepter")
    v7_dragon.scepter(sart)
    sobj = ck.finish(sart, col, glow=5.0)
    sobj.name = "Scepter_v7"
    metal(sart)
    sobj.parent = obj
    return art, obj, sart, sobj


def main():
    # 1. Габариты формы v6 — от них камеры и масштаб (как в v6_render)
    col = ck.reset_scene()
    a6 = v6_dragon.dragon()
    o6 = a6.build(col)
    lo, hi = ck.bounds([o6])
    size6 = [hi[i] - lo[i] for i in range(3)]
    offset = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, 0.0))
    k = TARGET_STUDS / size6[2]
    span = max(size6)
    cz = (hi.z + lo.z) / 2
    dist = 1.08 * span / (2 * TANH)
    cams = {"front": 0, "side": -90, "34": -35, "back": 180}
    head = Vector((0.0, -5.6, 10.55)) + offset  # чуть выше и дальше, чем у v6: корона целиком в кадре
    head_cams = {"head_front": head + Vector((0.0, -10.6, 0.6)), "head_34": head + Vector((-6.0, -8.2, 1.6))}
    head_side = Vector((-5.6, 0.0, 10.55)) + offset  # голова после поворота дракона на −90° (как кадр «сбоку»)

    def turntable(obj, prefix, views, sil=False):
        scene = bpy.context.scene
        floor = bpy.data.objects.get("Floor")
        obj.location = offset
        for label in views:
            obj.rotation_euler = (0, 0, math.radians(cams[label]))
            bpy.context.view_layer.update()
            ck.shot(cam, os.path.join(OUT, f"{prefix}_{label}.png"), (0, -dist, cz + 1.4), (0, 0, cz), LENS, RES)
            if sil and label != "back":
                scene.render.film_transparent = True
                floor.hide_render = True
                ck.shot(cam, os.path.join(OUT, f"{prefix}_{label}_sil.png"), (0, -dist, cz + 1.4), (0, 0, cz), LENS,
                        RES)
                scene.render.film_transparent = False
                floor.hide_render = False
        obj.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()

    # 2. v6 в глине теми же камерами
    if not QUICK:
        clay(o6)
        cam = ck.studio(col, size=2.4, bg=(0.72, 0.74, 0.8))
        bpy.context.scene.view_settings.exposure = -0.5
        turntable(o6, "v6", ("front", "side", "34"))
        o6.location = offset
        ck.shot(cam, os.path.join(OUT, "v6_head_front.png"), head_cams["head_front"], head, 55, RES)
    # 3. v7
    col = ck.reset_scene()
    art, obj, sart, sobj = build_v7(col)
    cam = ck.studio(col, size=2.4, bg=(0.72, 0.74, 0.8))
    bpy.context.scene.view_settings.exposure = EXPOSURE
    lo7, hi7 = ck.bounds([obj, sobj])
    lod, hid = ck.bounds([obj])
    size7 = [hi7[i] - lo7[i] for i in range(3)]
    sized = [hid[i] - lod[i] for i in range(3)]
    groups = rig_groups(obj, art)
    gtris = group_tris(obj, art)
    turntable(obj, "v7", ("front", "34") if QUICK else ("front", "side", "back", "34"), sil=not QUICK)
    obj.location = offset
    bpy.context.view_layer.update()
    for label, eye in head_cams.items():
        ck.shot(cam, os.path.join(OUT, f"v7_{label}.png"), eye, head, 55, RES)
    if not QUICK:
        obj.rotation_euler = (0, 0, math.radians(-90))
        bpy.context.view_layer.update()
        ck.shot(cam, os.path.join(OUT, "v7_head_side.png"), head_side + Vector((0.6, -11.6, 0.9)), head_side, 55, RES)
        obj.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
    chest = Vector((0.0, -3.9, 5.3)) + offset
    ck.shot(cam, os.path.join(OUT, "v7_chest.png"), chest + Vector((-4.6, -9.0, 1.2)), chest, 55, RES)
    flank = Vector((2.4, -1.2, 4.6)) + offset
    ck.shot(cam, os.path.join(OUT, "v7_flank.png"), flank + Vector((9.0, -4.0, 1.5)), flank, 55, RES)
    if not QUICK:
        obj.location = (0, 0, 0)
        bpy.context.preferences.filepaths.save_version = 0  # без копии .blend1
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BOSS, "boss10_v7.blend"), compress=True)
        obj.location = offset
    # 4. скипетр отдельно
    col = ck.reset_scene()
    sart2 = v7_dragon.new_art("ScepterSolo")
    v7_dragon.scepter(sart2, base=(0.0, 0.0))
    so = ck.finish(sart2, col, glow=5.0)
    metal(sart2)
    cam = ck.studio(col, size=1.0, bg=(0.72, 0.74, 0.8))
    bpy.context.scene.view_settings.exposure = EXPOSURE
    slo, shi = ck.bounds([so])
    sc = Vector((0, 0, (slo.z + shi.z) / 2))
    ck.shot(cam, os.path.join(OUT, "v7_scepter.png"), sc + Vector((-6.5, -13.0, 2.0)), sc, 55, (900, 1400))
    stats = {
        "tris": art.stats["tris"], "tris_scepter": sart.stats["tris"], "tris_total": art.stats["tris"] + sart.stats["tris"],
        "tris_v6": a6.stats["tris"], "hidden_faces": art.stats.get("hidden_faces"),
        "coplanar": art.stats.get("coplanar"), "flipped": art.stats.get("flipped"),
        "degenerate": art.stats.get("degenerate"), "group_tris": gtris, "groups": groups,
        "size_v6_model": [round(v, 2) for v in size6], "export_scale": round(k, 3),
        "size_v6_studs": [round(v * k, 1) for v in size6],
        "size_dragon_model": [round(v, 2) for v in sized], "size_dragon_studs": [round(v * k, 1) for v in sized],
        "size_with_scepter_studs": [round(v * k, 1) for v in size7], "top_v6": round(hi.z, 2), "top_v7": round(hid.z, 2),
        "wingspan_studs": round(sized[0] * k, 1), "arena_diameter": ARENA,
        "scepter_model": [round(v, 2) for v in (shi - slo)], "scepter_studs": round((shi.z - slo.z) * k, 1),
        "palette": {kk: v[0] for kk, v in v7_dragon.PALETTE.items()},
    }
    with open(os.path.join(OUT, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print("STATS", json.dumps(stats, ensure_ascii=False), flush=True)
    print("DONE", OUT, flush=True)


main()

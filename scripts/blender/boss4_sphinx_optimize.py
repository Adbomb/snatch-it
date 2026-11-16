"""Босс 4 «Сфинкс-лежебока»: игровая копия утверждённой модели v2 в бюджете D33 (≤ 8 000 треугольников).

Утверждённые assets/models/Boss4_Sphinx.{blend,fbx,rig.json} и карты НЕ меняются: скрипт открывает .blend, работает
с копией в памяти и пишет отдельные файлы assets/models/Boss4_Sphinx_game.{blend,fbx} и отчёт <папка>/optimize.json.

Что убирается: только грани, которые не видны ни в одной позе, — из любой их точки луч в любую из 600 сторон
упирается в ТУ ЖЕ часть (блоки части собраны встык и внахлёст; часть — твёрдое тело, поэтому от позы это не зависит). Форма,
силуэт, развёртка, карты, точки вращения и габариты частей остаются прежними. Проверка: число треугольников по
частям, габариты частей до и после, и одинаковые рендеры до и после (сравнение по пикселям — optimize.json).

Запуск: blender --background assets/models/Boss4_Sphinx.blend --python scripts/blender/boss4_sphinx_optimize.py --
        <репо> <папка отчёта> [dry]      (dry — только посчитать, файлы модели не писать)
Зависит от scripts/blender/art_style.py (экспорт FBX теми же настройками, что у утверждённой модели).
"""

import json
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
DRY = len(argv) > 2 and argv[2] == "dry"
os.makedirs(OUT, exist_ok=True)

BUDGET = 8000
EPS = 0.004  # на сколько точка грани отступает наружу перед проверкой «внутри другого блока» (единицы модели)
DEEP = 0.012  # грань убирается, только если она утоплена в другой блок не меньше чем на столько по всей площади
RAYS = [Vector(v).normalized() for v in ((0.31, 0.74, 0.59), (-0.67, 0.22, 0.71), (0.52, -0.61, -0.6))]
SCENE = bpy.context.scene
PARTS = sorted((o for o in SCENE.objects if o.name.startswith("Boss4_Sphinx")), key=lambda o: o.name)
assert len(PARTS) == 27, f"частей {len(PARTS)}, а не 27"
random.seed(4)


def tri_count(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def islands(bm):
    """Связные куски меша: список наборов граней."""
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, group = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            group.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        out.append(group)
    return out


def closed(group):
    return all(len(e.link_faces) == 2 for f in group for e in f.edges)


def tree_of(group):
    verts, index, polys = [], {}, []
    for f in group:
        poly = []
        for v in f.verts:
            if v.index not in index:
                index[v.index] = len(verts)
                verts.append(v.co.copy())
            poly.append(index[v.index])
        polys.append(poly)
    return BVHTree.FromPolygons(verts, polys, all_triangles=False, epsilon=0.0)


def inside(tree, p):
    """Точка внутри замкнутого куска: нечётное число пересечений луча с ним (по большинству из трёх лучей)."""
    votes = 0
    for d in RAYS:
        hits, origin = 0, p
        for _ in range(64):
            loc, _n, _i, _dist = tree.ray_cast(origin, d)
            if loc is None:
                break
            hits += 1
            origin = loc + d * 1e-5
        votes += hits % 2
    return votes >= 2


def samples(f):
    """Точки по всей грани: середина, вдоль каждого ребра у самого края, у вершин и случайные внутри."""
    c = f.calc_center_median()
    pts = [c]
    vs = [v.co for v in f.verts]
    n = len(vs)
    for i in range(n):
        a, b = vs[i], vs[(i + 1) % n]
        for k in (0.03, 0.2, 0.4, 0.6, 0.8, 0.97):
            q = a.lerp(b, k)
            pts.append(q.lerp(c, 0.02))
            pts.append(q.lerp(c, 0.25))
        pts.append(a.lerp(c, 0.03))
    for _ in range(12):  # случайные точки в треугольниках веера от середины
        i = random.randrange(n)
        u, v = sorted((random.random(), random.random()))
        pts.append(c * u + vs[i] * (v - u) + vs[(i + 1) % n] * (1 - v))
    return pts


def sphere_dirs(n):
    """n направлений, равномерно по сфере (спираль Фибоначчи), в случайном порядке."""
    out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(1 - z * z, 0.0))
        a = math.pi * (3 - math.sqrt(5)) * i
        out.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    random.shuffle(out)
    return out


DIRS = sphere_dirs(600)


def enclosed(tree, p):
    """Точку не видно снаружи части: луч в любую сторону упирается в саму часть."""
    for d in DIRS:
        if tree.ray_cast(p, d)[0] is None:
            return False
    return True


def hidden_faces(bm):
    """Грани, которые не видны ни с одной стороны: все точки грани (чуть над ней и глубже) закрыты самой частью.
    Часть — твёрдое тело, поэтому результат не зависит от позы и от других частей."""
    groups = islands(bm)
    tree = BVHTree.FromBMesh(bm, epsilon=0.0)
    out = []
    for f in bm.faces:
        n = f.normal
        c = f.calc_center_median()
        if not enclosed(tree, c + n * EPS):  # быстрый отсев: середина грани видна
            continue
        if all(enclosed(tree, p + n * EPS) and enclosed(tree, p + n * DEEP) for p in samples(f)):
            out.append(f)
    return out, len(groups), sum(1 for g in groups if not closed(g))


def bounds(o):
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return [round(c, 5) for c in lo + hi]


def render_views(tag):
    """Одинаковые кадры модели в покое с 10 сторон: до и после сравниваются по пикселям."""
    for o in SCENE.objects:
        if o.name.startswith("Mannequin"):
            o.hide_render = True
    pts = [o.matrix_world @ Vector(c) for o in PARTS for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    mid, r = (lo + hi) / 2, (hi - lo).length
    cam = SCENE.camera
    cam.data.lens = 40
    SCENE.render.resolution_x = SCENE.render.resolution_y = 800
    props = SCENE.render.image_settings.bl_rna.properties
    if "media_type" in props:
        SCENE.render.image_settings.media_type = "IMAGE"
    SCENE.render.image_settings.file_format = "PNG"
    views = [(a, 18) for a in range(0, 360, 45)] + [(30, 75), (200, -35)]
    files = []
    for k, (az, el) in enumerate(views):
        a, e = math.radians(az), math.radians(el)
        eye = mid + Vector((math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e))) * r * 1.5
        cam.location = eye
        cam.rotation_euler = (eye - mid).to_track_quat("Z", "Y").to_euler()
        path = os.path.join(OUT, f"{tag}_{k:02d}.png")
        SCENE.render.filepath = path
        bpy.ops.render.render(write_still=True)
        files.append(path)
    return files


report = {"budget": BUDGET, "parts": {}, "before": 0, "after": 0}
before_bounds = {o.name: bounds(o) for o in PARTS}
before_files = render_views("before")
for o in PARTS:
    me = o.data
    name = o.name.rsplit("_", 1)[1]
    t0 = tri_count(me)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    bm.verts.index_update()
    bm.normal_update()
    faces, n_groups, n_open = hidden_faces(bm)
    removed = sum(len(f.verts) - 2 for f in faces)
    if faces:
        bmesh.ops.delete(bm, geom=faces, context="FACES")
        bm.to_mesh(me)
        me.update()
    bm.free()
    t1 = tri_count(me)
    assert t0 - t1 == removed, (name, t0, t1, removed)
    report["parts"][name] = {"before": t0, "after": t1, "hidden_faces": len(faces), "blocks": n_groups, "open_blocks": n_open}
    report["before"] += t0
    report["after"] += t1
    print(f"OPT {name:9s} блоков {n_groups:3d} (незамкнутых {n_open}) треугольников {t0:5d} → {t1:5d} (скрытых граней {len(faces)})")
after_bounds = {o.name: bounds(o) for o in PARTS}
report["bounds_changed"] = [n for n in before_bounds if before_bounds[n] != after_bounds[n]]
after_files = render_views("after")
diffs = []
for a, b in zip(before_files, after_files):
    ia, ib = bpy.data.images.load(a), bpy.data.images.load(b)
    pa, pb = np.array(ia.pixels[:], dtype=np.float32), np.array(ib.pixels[:], dtype=np.float32)
    d = np.abs(pa - pb)
    diffs.append({"view": os.path.basename(a), "max": round(float(d.max()), 5), "changed_pixels": int((d.reshape(-1, 4).max(axis=1) > 2 / 255).sum())})
report["render_diff"] = diffs
report["render_diff_max"] = max(d["max"] for d in diffs)
report["render_changed_pixels"] = sum(d["changed_pixels"] for d in diffs)
print("OPT ИТОГО", report["before"], "→", report["after"], "| габариты изменились у:", report["bounds_changed"],
      "| рендеры: наибольшая разница", report["render_diff_max"], "изменённых пикселей", report["render_changed_pixels"])
with open(os.path.join(OUT, "optimize.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
if not DRY and report["after"] <= BUDGET and not report["bounds_changed"]:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(REPO, "assets", "models", "Boss4_Sphinx_game.blend"), copy=True)
    # В .blend модель стоит в позе «стойка» на земле; в FBX части должны быть в покое: начало координат каждой —
    # её точка вращения из rig.json (оси Roblox x, y, z → Blender x, −z, y), как в утверждённом Boss4_Sphinx.fbx.
    with open(os.path.join(REPO, "assets", "models", "Boss4_Sphinx.rig.json"), encoding="utf-8") as f:
        rig = json.load(f)
    for o in PARTS:
        x, y, z = rig["parts"][o.name.rsplit("_", 1)[1]]["pivot"]
        o.matrix_world = Matrix.Translation((x, -z, y))
    bpy.context.view_layer.update()
    S.export_fbx(PARTS, os.path.join(REPO, "assets", "models", "Boss4_Sphinx_game.fbx"))
    print("OPT_SAVED Boss4_Sphinx_game.blend, Boss4_Sphinx_game.fbx")
print("OPT_OK")

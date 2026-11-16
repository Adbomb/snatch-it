"""Проверка игрового FBX существа босса 4 перед импортом в Roblox (art_oasis.py): части и имена, точки вращения и
габариты против rig.json, одна развёртка в пределах 0…1, один материал, треугольники, вывернутые грани, масштаб,
лишние объекты. Печатает строки CHECK и итог OK/FAIL.
С <id эталона> — ещё сверка с другой версией той же модели (полировка): скелет и точки вращения в rig.json, вершины
и грани каждой части совпадают (до 0.0001 стада) — значит, форма, пропорции и совместимость анимаций не изменились.
Запуск: blender --background --factory-startup --python scripts/blender/check_oasis_fbx.py -- <репо> <id> [<id эталона>]
"""

import json
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, ITEM = os.path.abspath(argv[0]), argv[1]
REF = argv[2] if len(argv) > 2 else None
BASE = os.path.join(REPO, "assets", "models", "art", "boss4", ITEM)
BUDGET = 3000  # D39: предмет ≤ 3 000 треугольников


def geometry(path):
    """Части FBX: отсортированные вершины (в мире, округлённые) и грани (наборы вершин), положение начала."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    out = {}
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        m = o.matrix_world
        co = [tuple(round(c, 4) for c in m @ v.co) for v in o.data.vertices]
        faces = sorted(tuple(sorted(co[i] for i in p.vertices)) for p in o.data.polygons)
        out[o.name.split("_", 2)[-1]] = (sorted(co), faces, tuple(round(c, 4) for c in m.translation))
    return out


ref_geo = geometry(os.path.join(os.path.dirname(BASE), REF + ".fbx")) if REF else None
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=BASE + ".fbx")
rig = json.load(open(BASE + ".rig.json", encoding="utf-8"))
objs = list(bpy.context.scene.objects)
meshes = [o for o in objs if o.type == "MESH"]
errors = []


def check(ok, text):
    print(("CHECK ok   " if ok else "CHECK FAIL ") + text)
    if not ok:
        errors.append(text)


def rbx(v):
    return Vector((v.x, v.z, -v.y))  # Blender → Roblox


names = {o.name.split("_", 2)[-1]: o for o in meshes}
check(len(objs) == len(meshes), f"лишних объектов нет (всего {len(objs)}, мешей {len(meshes)})")
check(sorted(names) == sorted(rig["order"]), f"части как в скелете: {len(names)} из {len(rig['order'])}")
tris = 0
worst_pivot = worst_center = worst_size = 0.0
flipped = 0
mats = set()
for part, info in rig["parts"].items():
    o = names.get(part)
    if not o:
        continue
    me = o.data
    me.calc_loop_triangles()
    tris += len(me.loop_triangles)
    m = o.matrix_world
    pivot = rbx(m.translation)
    pts = [rbx(m @ v.co) for v in me.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    worst_pivot = max(worst_pivot, (pivot - Vector(info["pivot"])).length)
    worst_center = max(worst_center, ((lo + hi) / 2 - pivot - Vector(info["center"])).length)
    worst_size = max(worst_size, ((hi - lo) - Vector(info["size"])).length)
    check(len(me.uv_layers) == 1, f"{part}: одна развёртка")
    us = [c for l in me.uv_layers[0].data for c in l.uv]
    check(min(us) >= -1e-4 and max(us) <= 1 + 1e-4, f"{part}: развёртка в пределах 0…1")
    mats |= {s.material.name for s in o.material_slots if s.material}
    check(abs(m.to_scale().x - 1) < 1e-3 and o.parent is None, f"{part}: масштаб 1, без родителя")
    # вывернутая грань: нормаль смотрит внутрь детали — центр грани, сдвинутый наружу, оказывается внутри меша
    for p in me.polygons:
        if sum(me.vertices[i].normal.dot(p.normal) for i in p.vertices) < 0:
            flipped += 1
check(tris <= BUDGET, f"треугольников {tris} (бюджет D39 {BUDGET})")
# плотность карты на самом существе (подставку в игре прячут) и на подставке, текселей на стад
for label, keep in (("существо", lambda g: g != "Stand"), ("подставка", lambda g: g == "Stand")):
    uv_area = surf = 0.0
    for part, o in names.items():
        if not keep(part):
            continue
        me = o.data
        uv = me.uv_layers[0].data
        for lt in me.loop_triangles:
            a_, b_, c_ = (Vector(uv[i].uv) for i in lt.loops)
            uv_area += abs((b_ - a_).cross(c_ - a_)) / 2
            surf += lt.area
    print(f"CHECK плотность карты, {label}: {1024 * (uv_area / surf) ** 0.5:.0f} текселей на стад, {uv_area:.1%} карты")
check(worst_pivot < 1e-3 and worst_center < 1e-3 and worst_size < 1e-3,
      f"точки вращения, центры и размеры как в rig.json (расхождение {worst_pivot:.4f} / {worst_center:.4f} / {worst_size:.4f})")
check(len(mats) == 1, f"материалов {len(mats)}")
check(flipped == 0, f"граней с нормалью против вершин: {flipped}")
allp = [rbx(o.matrix_world @ v.co) for o in meshes for v in o.data.vertices]
lo = Vector([min(p[i] for p in allp) for i in range(3)])
hi = Vector([max(p[i] for p in allp) for i in range(3)])
print(f"CHECK габариты (Roblox, стады): ширина {hi.x - lo.x:.2f}, высота {hi.y - lo.y:.2f}, глубина {hi.z - lo.z:.2f}; "
      f"низ на {lo.y:.3f}")
check(abs(lo.y) < 1e-3, "низ модели на y = 0")
if REF:
    ref_rig = json.load(open(os.path.join(os.path.dirname(BASE), REF + ".rig.json"), encoding="utf-8"))
    check(ref_rig["order"] == rig["order"] and ref_rig["parts"] == rig["parts"],
          f"скелет как у {REF}: порядок, родители, точки вращения, центры и размеры частей")
    geo = {}
    for name, o in names.items():
        m = o.matrix_world
        co = [tuple(round(c, 4) for c in m @ v.co) for v in o.data.vertices]
        geo[name] = (sorted(co), sorted(tuple(sorted(co[i] for i in p.vertices)) for p in o.data.polygons),
                     tuple(round(c, 4) for c in m.translation))
    same = [g for g in ref_geo if g in geo and geo[g] == ref_geo[g]]
    check(sorted(same) == sorted(ref_geo) == sorted(geo),
          f"вершины, грани и начала частей как у {REF}: совпали {len(same)} из {len(ref_geo)}")
print("CHECK_OK" if not errors else f"CHECK_FAIL {len(errors)}")

"""Проверка скелетов существ босса 3 (D54/D55): каждый assets/models/art/<id>.rig.json против своего FBX.

Импортирует FBX (Blender без интерфейса) и сверяет: имена частей Art_<id>_<Часть> = order скелета; положение каждой
части = её pivot (оси Roblox: x, z, −y Blender); габариты меша относительно точки вращения = center/size скелета;
корень один — Stand; точка вращения не дальше 0.6 стада от своей части (иначе — предупреждение); у Stand нет дочерних
объектов в FBX (части плоские — подставку можно скрыть отдельно). Печатает RIGCHECK по предметам и RIGS_OK/RIGS_FAIL.
Запуск: blender --background --factory-startup --python scripts/blender/check_rigs.py -- <репо> [id…]
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO = os.path.abspath(argv[0])
ART = os.path.join(REPO, "assets", "models", "art")
TEX = os.path.join(REPO, "assets", "textures", "art")
ids = argv[1:] or sorted(f[:-9] for f in os.listdir(ART) if f.endswith(".rig.json"))


def to_rbx(v):
    return Vector((v.x, v.z, -v.y))


fails, warns_total = 0, 0
for item_id in ids:
    rig = json.load(open(os.path.join(ART, f"{item_id}.rig.json"), encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(ART, f"{item_id}.fbx"))
    bpy.context.view_layer.update()
    objs = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
    prefix = f"Art_{item_id}_"
    names = {n[len(prefix):]: o for n, o in objs.items() if n.startswith(prefix)}
    errs, warns = [], []
    if set(names) != set(rig["order"]):
        errs.append(f"части FBX {sorted(set(names) - set(rig['order']))} / скелет {sorted(set(rig['order']) - set(names))}")
    roots = [p for p, d in rig["parts"].items() if d["parent"] is None]
    if roots != ["Stand"]:
        errs.append(f"корни {roots}")
    for p, d in rig["parts"].items():
        if d["parent"] is not None and d["parent"] not in rig["parts"]:
            errs.append(f"{p}: нет родителя {d['parent']}")
    tris = 0
    for p, o in names.items():
        if p not in rig["parts"]:
            continue
        d = rig["parts"][p]
        if o.parent is not None or o.children:
            errs.append(f"{p}: в FBX есть иерархия (нужны плоские части)")
        piv = to_rbx(o.matrix_world.translation)
        if (piv - Vector(d["pivot"])).length > 0.01:
            errs.append(f"{p}: pivot FBX {tuple(round(c, 3) for c in piv)} ≠ скелет {d['pivot']}")
        rot = o.matrix_world.to_euler()
        if max(abs(a) for a in rot) > 1e-3 or max(abs(s - 1) for s in o.matrix_world.to_scale()) > 1e-3:
            errs.append(f"{p}: у объекта есть поворот или масштаб")
        co = [to_rbx(o.matrix_world.to_3x3() @ v.co) for v in o.data.vertices]
        if not co:
            errs.append(f"{p}: пустой меш")
            continue
        lo = Vector([min(c[i] for c in co) for i in range(3)])
        hi = Vector([max(c[i] for c in co) for i in range(3)])
        if ((lo + hi) / 2 - Vector(d["center"])).length > 0.01 or ((hi - lo) - Vector(d["size"])).length > 0.01:
            errs.append(f"{p}: габариты FBX не совпадают со скелетом")
        gap = Vector([max(lo[i] - 0, 0, 0 - hi[i]) for i in range(3)]).length  # от точки вращения до габарита
        if gap > 0.6 and p != "Stand":
            warns.append(f"{p}: точка вращения в {gap:.2f} от части")
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
    for kind in ("color", "normal"):
        if not os.path.exists(os.path.join(TEX, f"{item_id}_{kind}.png")):
            errs.append(f"нет карты {kind}")
    if tris > 3000:
        errs.append(f"треугольников {tris} > 3000")
    stand = rig["parts"].get("Stand")
    creature = [p for p in rig["order"] if p != "Stand"]
    status = "OK" if not errs else "FAIL"
    fails += bool(errs)
    warns_total += len(warns)
    print("RIGCHECK", item_id, status, json.dumps({"parts": len(rig["order"]), "creature_parts": len(creature),
                                                    "tris": tris, "errors": errs, "warnings": warns},
                                                   ensure_ascii=False))
print(("RIGS_OK" if not fails else "RIGS_FAIL"), len(ids), "предметов,", fails, "с ошибками,", warns_total, "предупреждений")

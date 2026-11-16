"""Сводный FBX существ босса 3 для одной загрузки (2026-11-14, по образцу pack_boss4_fbx.py): все части всех 30 существ
D54 в одном файле.

Берёт assets/models/art/Boss3Creatures.index.json и FBX каждого существа; подставки (Stand) берёт тоже — у части
существ D54 подставка видна в игре (stand_policy). Объекты сохраняют имена `Art_<id>_<Часть>` и свою геометрию относительно начала координат (точки
вращения), поэтому после импорта MeshId привязываются по имени (`scripts/bind_meshes.py`), как у 30 отдельных файлов;
существа разнесены рядами, чтобы не наслаивались в окне импорта. Пишет assets/models/Boss3Creatures_all.fbx и печатает
PACK_OK <частей> <треугольников>.
Запуск: blender --background --factory-startup --python scripts/blender/pack_boss3_fbx.py -- <репо>
"""

import json
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO = os.path.abspath(argv[0])
ART = os.path.join(REPO, "assets", "models", "art")
OUT = os.path.join(REPO, "assets", "models", "Boss3Creatures_all.fbx")
index = json.load(open(os.path.join(ART, "Boss3Creatures.index.json"), encoding="utf-8"))

bpy.ops.wm.read_factory_settings(use_empty=True)
keep, tris = [], 0
for k, item in enumerate(index["items"]):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(REPO, item["fbx"]))
    new = [o for o in bpy.data.objects if o not in before]
    dx, dy = (k % 6) * 6.0, (k // 6) * 6.0
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        o.location.x += dx
        o.location.y += dy
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
        keep.append(o)
names = [o.name for o in keep]
assert len(names) == len(set(names)), "повтор имён частей"
bpy.ops.object.select_all(action="DESELECT")
for o in keep:
    o.select_set(True)
# те же настройки, что у отдельных FBX (art_style.export_fbx): импорт Studio видит те же меши
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                         apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE",
                         add_leaf_bones=False, bake_anim=False, path_mode="STRIP")
print("PACK_OK", len(keep), tris, OUT, flush=True)

"""Сводный FBX существ босса 5 для одной загрузки (Open Cloud, как у босса 4): видимые части всех 30 существ.

Берёт FBX каждого существа из assets/models/art/boss5/ (art_glacier.py); подставки (Stand — в игре прячется, D58)
не берёт. Объекты сохраняют имена `Art_<id>_<Часть>` и свою геометрию относительно точки вращения, поэтому MeshId
привязываются по имени; существа разнесены рядами, чтобы не наслаивались. Пишет assets/models/Boss5Creatures_all.fbx
и печатает PACK_OK <существ> <частей> <треугольников>; ASYM — пары L/R разного размера (>25 %, проверить глазами:
ошибка группы или задуманная асимметрия).
Запуск: blender --background --factory-startup --python scripts/blender/pack_boss5_fbx.py -- <репо>
"""

import glob
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO = os.path.abspath(argv[0])
ART = os.path.join(REPO, "assets", "models", "art", "boss5")
OUT = os.path.join(REPO, "assets", "models", "Boss5Creatures_all.fbx")
files = sorted(glob.glob(os.path.join(ART, "*.fbx")))

bpy.ops.wm.read_factory_settings(use_empty=True)
keep, tris = [], 0
for k, path in enumerate(files):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    dx, dy = (k % 6) * 6.0, (k // 6) * 6.0
    for o in new:
        if o.type != "MESH" or o.name.endswith("_Stand"):
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        o.location.x += dx
        o.location.y += dy
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
        keep.append(o)
names = [o.name for o in keep]
assert len(names) == len(set(names)), "повтор имён частей"
# пары L/R: размеры должны совпадать (деталь, нарисованная после цикла по сторонам, попадает в последнюю часть цикла)
by = {o.name: o for o in keep}
asym = []
for nm, o in by.items():
    if nm.endswith("L") and nm[:-1] + "R" in by:
        a, b = sorted(o.dimensions), sorted(by[nm[:-1] + "R"].dimensions)
        if max(abs(x - y) / max(x, y, 1e-6) for x, y in zip(a, b)) > 0.25:
            asym.append(nm[:-1])
print("ASYM", asym, flush=True)
bpy.ops.object.select_all(action="DESELECT")
for o in keep:
    o.select_set(True)
# те же настройки, что у отдельных FBX (art_style.export_fbx): Studio видит те же меши
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                         apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE",
                         add_leaf_bones=False, bake_anim=False, path_mode="STRIP")
print("PACK_OK", len(files), len(keep), tris, OUT, flush=True)

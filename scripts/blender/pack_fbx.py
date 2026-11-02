"""Сводный FBX коллекции для одного импорта в Studio: все assets/models/art/<id>.fbx в одном файле.

Каждый предмет остаётся отдельным мешем Art_<id> (после импорта — отдельная MeshPart со своим MeshId); предметы
разнесены по x, чтобы не наслаивались в окне импорта. Геометрия и развёртка не меняются — карты SurfaceAppearance
те же, что уже загружены (assets/textures/art/IDS.md).
Запуск: blender --background --factory-startup --python scripts/blender/pack_fbx.py -- <репо> <вывод.fbx> <id…>
"""

import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT, IDS = os.path.abspath(argv[0]), os.path.abspath(argv[1]), argv[2:]

bpy.ops.wm.read_factory_settings(use_empty=True)
objs = []
x = 0.0
for item_id in IDS:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(REPO, "assets", "models", "art", f"{item_id}.fbx"))
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if len(new) != 1:
        raise RuntimeError(f"{item_id}: ожидался один меш, найдено {len(new)}")
    o = new[0]
    o.name = f"Art_{item_id}"
    o.location.x += x
    x += 6.0
    objs.append(o)
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                         axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP")
print("PACK_OK", len(objs), OUT)

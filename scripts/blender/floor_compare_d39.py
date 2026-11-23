"""Сравнение нового этажа «Золотой трон» с утверждёнными моделями в одной студии (art_style.Preview): настоящая ваза
v13 и предмет GoldenThrone с их картами стоят перед фасадом этажа. Фасад — меши из
assets/models/floors/GoldenThroneFloor.fbx (то, что загружено в игру): цвета — из цветов вершин, на деталях Rings —
те же контурные квадраты D39 (art_style._ring_material, как у предметов), детали Smooth — гладкие.
Ничего не пишет в игру. Запуск:
blender --background --factory-startup --python scripts/blender/floor_compare_d39.py -- <репо> <папка кадров>
"""

import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Compare")
bpy.context.scene.collection.children.link(collection)


def vertex_material(name, rings):
    """Цвет из вершин; rings — с контурными квадратами D39 поверх (тот же материал, что запекается у предметов)."""
    mat = S._ring_material(name, "FFFFFF", 0.0) if rings else S._flat_material(name, "FFFFFF")
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    if rings:
        nt.links.new(attr.outputs["Color"], nt.nodes["RingShade"].inputs["Color1"])
    else:
        nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    for link in list(bsdf.inputs["Emission Color"].links):
        nt.links.remove(link)
    bsdf.inputs["Emission Strength"].default_value = 0.0
    mat.use_backface_culling = True
    return mat


before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=os.path.join(REPO, "assets", "models", "floors", "GoldenThroneFloor.fbx"))
floor = bpy.data.objects.new("Floor", None)
collection.objects.link(floor)
names = [o.name for o in bpy.data.objects if o not in before and o is not floor]
for name in names:  # удаление объекта обесценивает ссылки на остальные — каждый берём заново по имени
    o = bpy.data.objects[name]
    if o.type != "MESH" or not name.startswith("GT_F_"):
        bpy.data.objects.remove(o, do_unlink=True)
for name in names:
    o = bpy.data.objects.get(name)
    if o is None:
        continue
    if o.data.color_attributes and o.data.color_attributes[0].name != "Col":
        o.data.color_attributes[0].name = "Col"
    o.data.materials.clear()
    o.data.materials.append(vertex_material(o.name, o.name.endswith("Rings")))
    o.parent = floor
floor.location = (0.0, 21.5, -0.25)  # ярусы ковра трона — у ног зрителя, корпус уходит за фон студии


def reference(tag, fbx, prefix, at):
    seen = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=fbx)
    mat = bpy.data.materials.new(f"M_{tag}")
    mat.use_nodes = True
    mat.use_backface_culling = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.5
    col = nt.nodes.new("ShaderNodeTexImage")
    col.image = bpy.data.images.load(prefix + "_color.png")
    nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    nrm = nt.nodes.new("ShaderNodeTexImage")
    nrm.image = bpy.data.images.load(prefix + "_normal.png")
    nrm.image.colorspace_settings.name = "Non-Color"
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    root = bpy.data.objects.new(f"Root_{tag}", None)
    collection.objects.link(root)
    for o in [o for o in bpy.data.objects if o not in seen and o is not root]:
        if o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(mat)
        if o.parent is None:
            o.parent = root
    root.location = at


reference("VaseV13", os.path.join(REPO, "assets", "models", "ArtV13_Vase.fbx"),
          os.path.join(REPO, "assets", "textures", "art", "v13_vase"), (-11.0, -5.2, 0.0))
reference("GoldenThrone", os.path.join(REPO, "assets", "models", "art", "GoldenThrone.fbx"),
          os.path.join(REPO, "assets", "textures", "art", "GoldenThrone"), (-6.2, -5.6, 0.0))

prev = S.Preview(collection)
prev.aim_lights(Vector((-7.0, 0, 0)))
for name, eye, target, lens in (("06_compare_close", (-11.5, -17.0, 4.2), (-7.6, -1.5, 2.6), 50),
                                ("06_compare_wide", (-4.0, -34.0, 9.0), (-1.0, 0.0, 5.0), 40)):
    prev.shot(os.path.join(OUT, name + ".png"), eye, target, lens, (1920, 1080))
    print("SHOT", name, flush=True)
print("DONE", flush=True)

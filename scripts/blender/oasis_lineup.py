"""Ряд существ босса 4 одной камерой: цветной кадр (три четверти, студия) и силуэты (чёрное на белом, без подставок) —
проверка, что силуэты разные, а масштаб и качество одного уровня с эталоном. Модели — игровые FBX и их карты.
Запуск: blender --background --factory-startup --python scripts/blender/oasis_lineup.py -- <репо> <папка> <id> [<id> …]
Пишет <папка>/lineup_color.png и <папка>/lineup_silhouette.png (подписи — отдельным листом).
Зависит от art_style.py (студия).
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT, IDS = os.path.abspath(argv[0]), os.path.abspath(argv[1]), argv[2:]
MODELS = os.path.join(REPO, "assets", "models", "art", "boss4")
TEXDIR = os.path.join(REPO, "assets", "textures", "art", "boss4")
STEP = 3.6  # шаг ряда — площадка 3.7 × 3.7
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Lineup")
bpy.context.scene.collection.children.link(collection)


def material(item):
    mat = bpy.data.materials.new(f"M_{item}")
    mat.use_nodes = True
    mat.use_backface_culling = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.5
    col = nt.nodes.new("ShaderNodeTexImage")
    col.image = bpy.data.images.load(os.path.join(TEXDIR, f"{item}_color.png"))
    nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    nrm = nt.nodes.new("ShaderNodeTexImage")
    nrm.image = bpy.data.images.load(os.path.join(TEXDIR, f"{item}_normal.png"))
    nrm.image.colorspace_settings.name = "Non-Color"
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


rows = []
x0 = -(len(IDS) - 1) * STEP / 2
for i, item in enumerate(IDS):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(MODELS, f"{item}.fbx"))
    objs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    mat = material(item)
    root = bpy.data.objects.new(f"Root_{item}", None)
    collection.objects.link(root)
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.parent = root
    root.location = (x0 + i * STEP, 0, 0)
    root.rotation_euler = (0, 0, math.radians(-28))  # три четверти: морда к камере чуть слева
    rows.append((item, root, objs))
bpy.context.view_layer.update()

prev = S.Preview(collection)
prev.aim_lights(Vector((0, 0, 0)))
for light, _ in prev.lights:  # ряд широкий: свет шире и сильнее, одинаково для всех
    light.data.size *= 2.5
    light.data.energy *= 2.2
width = len(IDS) * STEP
dist = width * 1.25 + 4
prev.shot(os.path.join(OUT, "lineup_color.png"), (0, -dist, dist * 0.32), (0, 0, 1.5), 50, (len(IDS) * 700, 900))

# спереди, ортографически, без подставок: сначала в цвете, затем силуэтом (чёрная эмиссия на белом фоне)
scene = bpy.context.scene
for item, root, objs in rows:
    root.rotation_euler = (0, 0, 0)
    for o in objs:
        if o.name.split(".")[0].endswith("_Stand"):
            o.hide_render = True
bpy.data.objects["Floor"].hide_render = True
cam = prev.cam_data
cam.type = "ORTHO"
cam.ortho_scale = width + 0.6
prev.cam.location = (0, -30, 2.0)
prev.cam.rotation_euler = (math.radians(90), 0, 0)
scene.render.resolution_x, scene.render.resolution_y = len(IDS) * 700, 1100
scene.render.filepath = os.path.join(OUT, "lineup_front.png")
bpy.ops.render.render(write_still=True)
black = bpy.data.materials.new("Silhouette")
black.use_nodes = True
nt = black.node_tree
for n in list(nt.nodes):
    if n.type != "OUTPUT_MATERIAL":
        nt.nodes.remove(n)
emit = nt.nodes.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = (0, 0, 0, 1)
nt.links.new(emit.outputs["Emission"], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
for item, root, objs in rows:
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(black)
white = bpy.data.worlds.new("White")
white.use_nodes = True
bg = next(n for n in white.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = (1, 1, 1, 1), 1.0
scene.world = white
scene.view_settings.view_transform = "Standard"
scene.render.filepath = os.path.join(OUT, "lineup_silhouette.png")
bpy.ops.render.render(write_still=True)
print("LINEUP_OK", IDS)

"""Резиновая уточка из настоящих LEGO-кирпичей: кирпичи и пластины с щелями между ними,
круглые пупырышки только там, где их видно. Цвета — из общей палитры предметов.
Запуск из корня репозитория:
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup \\
    --python scripts/blender/lego_duck.py -- . <preview.png>
"""
import math
import os
import sys

import bmesh
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
REPO, PREVIEW = argv[0], argv[1]

# Пропорции LEGO: шаг пупырышка 1, кирпич 1.2, пластина 0.4; пупырышек Ø0.6, высота 0.2.
PITCH, PLATE = 1.0, 0.4
STUD_R, STUD_H, STUD_SEGMENTS = 0.3, 0.2, 14
GAP = 0.02  # щель между деталями, чтобы читались швы
BEVEL = 0.03

PALETTE = [
    (255, 214, 10), (255, 140, 0), (27, 21, 48), (250, 250, 250),
    (229, 57, 53), (255, 150, 200), (138, 90, 43), (94, 58, 26),
    (67, 160, 71), (46, 125, 50), (158, 158, 158), (84, 90, 100),
    (30, 136, 229), (0, 200, 230), (142, 36, 170), (255, 194, 26),
]
YELLOW, ORANGE, BLACK, WHITE, GOLD = 0, 1, 2, 3, 15
GRID = 4

# Детали: (x0, y0, ширина по X, длина по Y, z в пластинах, высота в пластинах, цвет).
# Y — вперёд (к клюву), Z — вверх.
PIECES = [
    (-2, -3, 4, 6, 0, 3, YELLOW),  # низ тела 4x6
    (-2, -2, 4, 4, 3, 3, YELLOW),  # тело 4x4
    (-3, -1, 1, 3, 3, 2, GOLD),  # крыло левое
    (2, -1, 1, 3, 3, 2, GOLD),  # крыло правое
    (-1, -3, 2, 2, 3, 3, YELLOW),  # хвост
    (-1, -4, 2, 2, 6, 3, YELLOW),  # кончик хвоста, выше и дальше
    (-1, 0, 2, 2, 6, 3, YELLOW),  # шея
    (-1, 0, 2, 3, 9, 3, YELLOW),  # голова, нижний ряд
    (-1, 0, 2, 3, 12, 3, YELLOW),  # голова, верхний ряд
    (-1, 3, 2, 1, 10, 2, ORANGE),  # клюв
]
# Мелочь без пупырышков: глаза и блики на передней грани головы (центр x, y, z, размер).
DETAILS = [
    (-0.5, 3.0, 13.6 * PLATE, (0.35, 0.08, 0.45), BLACK),
    (0.5, 3.0, 13.6 * PLATE, (0.35, 0.08, 0.45), BLACK),
    (-0.42, 3.05, 13.8 * PLATE, (0.1, 0.05, 0.12), WHITE),
    (0.58, 3.05, 13.8 * PLATE, (0.1, 0.05, 0.12), WHITE),
]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

palette_path = os.path.join(REPO, "assets", "textures", "item_palette.png")
image = bpy.data.images.load(palette_path)
material = bpy.data.materials.new("ItemPalette")
material.use_nodes = True
nodes = material.node_tree.nodes
bsdf = nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 0.2
tex = nodes.new("ShaderNodeTexImage")
tex.image = image
tex.interpolation = "Closest"
material.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])


def cell_uv(index):
    return ((index % GRID + 0.5) / GRID, (index // GRID + 0.5) / GRID)


def paint(obj, color):
    mesh = obj.data
    if len(mesh.uv_layers) == 0:
        mesh.uv_layers.new(name="UVMap")
    u, v = cell_uv(color)
    for layer in mesh.uv_layers:
        for loop in layer.data:
            loop.uv = (u, v)
    mesh.materials.append(material)


def box(name, center, size, color, bevel=BEVEL):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    paint(obj, color)
    return obj


def stud(x, y, z, color):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=STUD_SEGMENTS, radius=STUD_R, depth=STUD_H, location=(x, y, z + STUD_H / 2), end_fill_type="NGON"
    )
    obj = bpy.context.active_object
    # Нижняя крышка не видна — убираем лишние треугольники.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bottom = [f for f in bm.faces if f.normal.z < -0.9]
    bmesh.ops.delete(bm, geom=bottom, context="FACES")
    bm.to_mesh(obj.data)
    bm.free()
    for poly in obj.data.polygons:
        poly.use_smooth = abs(poly.normal.z) < 0.5
    paint(obj, color)
    return obj


# Какие клетки сверху чем-то закрыты: (x, y, z в пластинах) — нижняя грань детали.
covered = set()
for x0, y0, w, d, z, h, _ in PIECES:
    for x in range(x0, x0 + w):
        for y in range(y0, y0 + d):
            covered.add((x, y, z))

objects = []
for i, (x0, y0, w, d, z, h, color) in enumerate(PIECES):
    center = ((x0 + w / 2) * PITCH, (y0 + d / 2) * PITCH, (z + h / 2) * PLATE)
    size = (w * PITCH - GAP, d * PITCH - GAP, h * PLATE - GAP)
    objects.append(box(f"Piece{i}", center, size, color))
    top = z + h
    for x in range(x0, x0 + w):
        for y in range(y0, y0 + d):
            if (x, y, top) not in covered:
                objects.append(stud((x + 0.5) * PITCH, (y + 0.5) * PITCH, top * PLATE - GAP / 2, color))
for i, (x, y, z, size, color) in enumerate(DETAILS):
    objects.append(box(f"Detail{i}", (x, y, z), size, color, bevel=0.01))

bpy.ops.object.select_all(action="DESELECT")
for obj in objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = objects[0]
bpy.ops.object.join()
duck = bpy.context.active_object
duck.name = "RubberDuck"
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
duck.location = (0, 0, duck.dimensions.z / 2)
bpy.ops.object.transform_apply(location=True)

bm = bmesh.new()
bm.from_mesh(duck.data)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
triangles = len(bm.faces)
bm.free()

models = os.path.join(REPO, "assets", "models")
os.makedirs(models, exist_ok=True)
fbx_path = os.path.join(models, "RubberDuck.fbx")
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=True,
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL",
    axis_forward="-Z",
    axis_up="Y",
    mesh_smooth_type="FACE",
    path_mode="COPY",
    embed_textures=True,
)

# Превью.
bpy.ops.object.camera_add(location=(12.0, 11.0, 9.5))
camera = bpy.context.active_object
target = duck.location.copy()
target.z = 2.6
camera.rotation_euler = (camera.location - target).to_track_quat("Z", "Y").to_euler()
scene.camera = camera
bpy.ops.object.light_add(type="SUN", location=(3, 3, 6))
sun = bpy.context.active_object
sun.data.energy = 4
sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(30))
world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.75, 0.95, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
scene.view_settings.view_transform = "Standard"  # цвета как в палитре, без киношной тонировки
engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.filepath = PREVIEW
bpy.ops.render.render(write_still=True)

print(f"DUCK_OK triangles={triangles} dims={tuple(round(d, 2) for d in duck.dimensions)} fbx={fbx_path}")

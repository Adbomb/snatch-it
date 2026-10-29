"""Пилот: резиновая уточка в LEGO/воксельном стиле. Запуск из корня репозитория:
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup     --python scripts/blender/rubber_duck.py -- . <preview.png>
Строит модель из скруглённых блоков, красит через общую текстуру-палитру 4x4,
экспортирует assets/models/RubberDuck.fbx и сохраняет палитру assets/textures/item_palette.png.
"""
import math
import os
import sys

import bmesh
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
REPO, PREVIEW = argv[0], argv[1]

# Палитра: 16 цветов, сетка 4x4 (индекс 0 — левый нижний угол).
PALETTE = [
    (255, 214, 10), (255, 140, 0), (27, 21, 48), (250, 250, 250),
    (229, 57, 53), (255, 150, 200), (138, 90, 43), (94, 58, 26),
    (67, 160, 71), (46, 125, 50), (158, 158, 158), (84, 90, 100),
    (30, 136, 229), (0, 200, 230), (142, 36, 170), (255, 194, 26),
]
YELLOW, ORANGE, BLACK, WHITE = 0, 1, 2, 3
CELL = 16
GRID = 4

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# --- палитра -------------------------------------------------------------------------------
size = CELL * GRID
image = bpy.data.images.new("item_palette", width=size, height=size, alpha=False)
pixels = []
for y in range(size):
    for x in range(size):
        index = (y // CELL) * GRID + (x // CELL)
        r, g, b = PALETTE[index]
        pixels += [r / 255, g / 255, b / 255, 1.0]
image.pixels = pixels
palette_path = os.path.join(REPO, "assets", "textures", "item_palette.png")
image.filepath_raw = palette_path
image.file_format = "PNG"
image.save()

material = bpy.data.materials.new("ItemPalette")
material.use_nodes = True
nodes = material.node_tree.nodes
bsdf = nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 0.25  # глянцевый пластик
tex = nodes.new("ShaderNodeTexImage")
tex.image = image
tex.interpolation = "Closest"
material.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])


def cell_uv(index):
    col, row = index % GRID, index // GRID
    return ((col + 0.5) / GRID, (row + 0.5) / GRID)


def block(name, size, location, color, bevel=0.12, rotation=(0, 0, 0)):
    """Скруглённый блок одного цвета палитры."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = bevel
    mod.segments = 2
    mod.limit_method = "NONE"
    bpy.ops.object.modifier_apply(modifier=mod.name)
    mesh = obj.data
    # У куба уже есть развёртка: красим все слои, чтобы экспорт взял нужный цвет палитры.
    if len(mesh.uv_layers) == 0:
        mesh.uv_layers.new(name="UVMap")
    u, v = cell_uv(color)
    for layer in mesh.uv_layers:
        for loop in layer.data:
            loop.uv = (u, v)
    mesh.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


# --- уточка (Y — вперёд у Blender, Z — вверх) -------------------------------------------------
parts = [
    block("Body", (1.6, 2.4, 1.2), (0, -0.1, 0.6), YELLOW, bevel=0.3),
    block("Belly", (1.4, 1.6, 0.4), (0, 0.15, 0.2), YELLOW, bevel=0.15),
    block("Tail", (1.0, 0.7, 0.7), (0, -1.25, 1.15), YELLOW, bevel=0.2, rotation=(math.radians(-35), 0, 0)),
    block("WingL", (0.22, 1.2, 0.55), (-0.84, -0.25, 0.75), YELLOW, bevel=0.1, rotation=(math.radians(-12), 0, 0)),
    block("WingR", (0.22, 1.2, 0.55), (0.84, -0.25, 0.75), YELLOW, bevel=0.1, rotation=(math.radians(-12), 0, 0)),
    block("Neck", (0.9, 0.8, 0.5), (0, 0.65, 1.3), YELLOW, bevel=0.15),
    block("Head", (1.2, 1.15, 1.1), (0, 0.75, 1.95), YELLOW, bevel=0.3),
    block("Beak", (0.8, 0.7, 0.28), (0, 1.55, 1.82), ORANGE, bevel=0.1),
    block("EyeL", (0.14, 0.12, 0.26), (-0.32, 1.3, 2.15), BLACK, bevel=0.04),
    block("EyeR", (0.14, 0.12, 0.26), (0.32, 1.3, 2.15), BLACK, bevel=0.04),
    block("ShineL", (0.06, 0.06, 0.08), (-0.29, 1.37, 2.22), WHITE, bevel=0.02),
    block("ShineR", (0.06, 0.06, 0.08), (0.35, 1.37, 2.22), WHITE, bevel=0.02),
]

bpy.ops.object.select_all(action="DESELECT")
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
duck = bpy.context.active_object
duck.name = "RubberDuck"
# Начало координат — центр низа модели.
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

# --- превью -------------------------------------------------------------------------------
bpy.ops.object.camera_add(location=(5.0, 4.2, 3.0))
camera = bpy.context.active_object
direction = duck.location.copy()
direction.z = 1.0
look = camera.location - direction
camera.rotation_euler = look.to_track_quat("Z", "Y").to_euler()
scene.camera = camera
bpy.ops.object.light_add(type="SUN", location=(3, 3, 6))
bpy.context.active_object.data.energy = 4
bpy.context.active_object.rotation_euler = (math.radians(40), math.radians(10), math.radians(30))
world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.75, 0.95, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE"
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.filepath = PREVIEW
bpy.ops.render.render(write_still=True)

print(f"DUCK_OK triangles={triangles} dims={tuple(round(d, 2) for d in duck.dimensions)} fbx={fbx_path}")

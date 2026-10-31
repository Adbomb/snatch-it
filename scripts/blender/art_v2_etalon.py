"""Эталон нового стиля предметов (D38, референс владельца 2026-10-31): «Матрёшка-великан» (босс 1, Rare) →
assets/models/ArtV2_NestingDoll.fbx (+ .layout.json, данные меша для проверки в Studio) и рендеры.

Запуск: blender --background --factory-startup --python scripts/blender/art_v2_etalon.py -- <репо> <превью> <референс>
"""

import json
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cubic  # noqa: E402
from cubic import Kit, hex_rgb, to_bl  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS, REFERENCE = os.path.abspath(argv[0]), os.path.abspath(argv[1]), argv[2] if len(argv) > 2 else None
os.makedirs(PREVIEWS, exist_ok=True)

# Палитра эталона: тёплый красный, золотисто-жёлтый платок, сливочное лицо, чёрные глаза с голубыми бликами.
C = {
    "red": "D8343A", "darkred": "A82230", "yellow": "F2B73A", "cream": "FFF1DC", "black": "1C1D22",
    "blue": "BFE4FF", "brown": "6B3A22", "pink": "F08BB4", "green": "4CB848", "white": "F7F7F2", "gold": "E9A825",
}


def face(k, x, y, z, s=1.0):
    """Лицо в платке на передней грани головы (z — передняя плоскость)."""
    k.rounded_box("cream", (x, y, z - 0.05 * s), (0.92 * s, 0.74 * s, 0.12 * s), radius=0.06 * s)
    k.rounded_box("brown", (x, y + 0.3 * s, z - 0.12 * s), (0.86 * s, 0.14 * s, 0.08 * s), radius=0.04 * s)
    for side in (-1, 1):
        ex = x + side * 0.22 * s
        k.rounded_box("black", (ex, y + 0.04 * s, z - 0.13 * s), (0.2 * s, 0.26 * s, 0.07 * s), radius=0.03 * s)
        k.rounded_box("blue", (ex + 0.04 * s, y + 0.1 * s, z - 0.17 * s), (0.07 * s, 0.08 * s, 0.03 * s),
                      radius=0.012 * s, segments=2)
        k.rounded_box("brown", (ex, y + 0.21 * s, z - 0.14 * s), (0.2 * s, 0.05 * s, 0.05 * s), radius=0.02 * s,
                      segments=2)
        k.rounded_box("pink", (x + side * 0.33 * s, y - 0.17 * s, z - 0.12 * s), (0.13 * s, 0.09 * s, 0.05 * s),
                      radius=0.02 * s, segments=2)
    k.rounded_box("red", (x, y - 0.23 * s, z - 0.13 * s), (0.16 * s, 0.06 * s, 0.05 * s), radius=0.02 * s, segments=2)


def flower(k, x, y, z, s=1.0):
    """Цветок на фартуке: жёлтая серединка, четыре розовых лепестка, зелёные листья."""
    k.rounded_box("pink", (x, y + 0.2 * s, z), (0.2 * s, 0.2 * s, 0.08 * s), radius=0.05 * s)
    k.rounded_box("pink", (x, y - 0.2 * s, z), (0.2 * s, 0.2 * s, 0.08 * s), radius=0.05 * s)
    k.rounded_box("pink", (x - 0.2 * s, y, z), (0.2 * s, 0.2 * s, 0.08 * s), radius=0.05 * s)
    k.rounded_box("pink", (x + 0.2 * s, y, z), (0.2 * s, 0.2 * s, 0.08 * s), radius=0.05 * s)
    k.rounded_box("yellow", (x, y, z - 0.03 * s), (0.18 * s, 0.18 * s, 0.1 * s), radius=0.05 * s)
    for side in (-1, 1):
        k.rounded_box("green", (x + side * 0.24 * s, y - 0.36 * s, z + 0.01), (0.22 * s, 0.11 * s, 0.07 * s),
                      radius=0.04 * s, rotation=cubic.rot(z=side * 30))
    k.rounded_box("green", (x, y - 0.42 * s, z + 0.01), (0.07 * s, 0.24 * s, 0.07 * s), radius=0.025 * s)


def doll(k, x0, s=1.0):
    """Матрёшка из блоков: широкий низ, корпус, голова в платке, фартук с цветком, ручки, узел платка."""
    # Низ и корпус — красные с рельефом; золотая полоса между ними.
    cell = max(0.4 * s, 0.3)  # у маленькой куклы квадраты не мельче 0.3 стада
    k.block("red", (x0, 0.5 * s, 0), (1.72 * s, 1.0 * s, 1.5 * s), faces="+x -x +z +y", cell=cell)
    k.rounded_box("gold", (x0, 1.03 * s, 0), (1.62 * s, 0.1 * s, 1.42 * s), radius=0.04 * s)
    k.block("red", (x0, 1.45 * s, 0), (1.5 * s, 0.76 * s, 1.32 * s), faces="+x -x +z", cell=cell)
    k.rounded_box("darkred", (x0, 0.05 * s, 0), (1.8 * s, 0.1 * s, 1.58 * s), radius=0.04 * s)
    # Голова в жёлтом платке с рельефом.
    k.block("yellow", (x0, 2.3 * s, 0.02 * s), (1.36 * s, 1.0 * s, 1.24 * s), faces="+x -x +y +z", cell=cell)
    face(k, x0, 2.28 * s, -0.6 * s, s)
    # Узел платка под подбородком и концы.
    k.rounded_box("yellow", (x0, 1.82 * s, -0.66 * s), (0.4 * s, 0.24 * s, 0.22 * s), radius=0.07 * s)
    for side in (-1, 1):
        k.rounded_box("yellow", (x0 + side * 0.2 * s, 1.62 * s, -0.68 * s), (0.18 * s, 0.32 * s, 0.1 * s),
                      radius=0.04 * s, rotation=cubic.rot(z=-side * 18))
    # Фартук сливочный с рельефом и цветок; ручки по бокам.
    k.block("cream", (x0, 1.05 * s, -0.7 * s), (1.12 * s, 1.5 * s, 0.14 * s), faces="-z", cell=max(0.36 * s, 0.3),
            radius=0.05 * s)
    flower(k, x0, 1.18 * s, -0.82 * s, s)
    for side in (-1, 1):
        k.rounded_box("cream", (x0 + side * 0.66 * s, 1.3 * s, -0.68 * s), (0.22 * s, 0.22 * s, 0.16 * s),
                      radius=0.06 * s)


for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
collection = bpy.data.collections.new("ArtV2")
bpy.context.scene.collection.children.link(collection)

kit = Kit("Art_NestingDoll")
doll(kit, -0.28, 1.0)
doll(kit, 1.12, 0.42)
objects = kit.build(collection)
tris = cubic.triangles(objects)

# FBX и раскладка (роль = цвет), как у гантелей.
models = os.path.join(REPO, "assets", "models")
bpy.ops.object.select_all(action="DESELECT")
for obj in objects:
    obj.select_set(True)
bpy.ops.export_scene.fbx(filepath=os.path.join(models, "ArtV2_NestingDoll.fbx"), use_selection=True,
                         apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                         mesh_smooth_type="FACE", path_mode="STRIP")
layout, studio = {}, []
for obj in objects:
    color = obj.name.split("_", 2)[2]
    mesh = obj.data
    mesh.calc_loop_triangles()
    lo = [min(v.co[i] for v in mesh.vertices) for i in range(3)]
    hi = [max(v.co[i] for v in mesh.vertices) for i in range(3)]
    mid = [(lo[i] + hi[i]) / 2 for i in range(3)]
    layout[color] = {"center": [round(mid[0], 3), round(mid[2], 3), round(-mid[1], 3)],
                     "size": [round(hi[0] - lo[0], 3), round(hi[2] - lo[2], 3), round(hi[1] - lo[1], 3)],
                     "color": C[color], "material": "SmoothPlastic", "triangles": len(mesh.loop_triangles)}
    # Для проверки в Studio (EditableMesh): вершины (позиция + нормаль угла) и треугольники, оси Roblox.
    verts, index, tri = [], {}, []
    for lt in mesh.loop_triangles:
        ids = []
        for loop_index in lt.loops:
            loop = mesh.loops[loop_index]
            co = mesh.vertices[loop.vertex_index].co
            nr = loop.normal if hasattr(loop, "normal") else lt.normal
            key = (round(co.x, 4), round(co.y, 4), round(co.z, 4), round(nr.x, 2), round(nr.y, 2), round(nr.z, 2))
            if key not in index:
                index[key] = len(verts)
                verts.append(key)
            ids.append(index[key])
        tri.append(ids)
    studio.append({"color": C[color], "v": [[k[0], k[2], -k[1]] for k in verts], "n": [[k[3], k[5], -k[4]] for k in verts],
                   "t": tri})
with open(os.path.join(models, "ArtV2_NestingDoll.layout.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump({"Art_NestingDoll": {"parts": layout}}, f, ensure_ascii=False, indent=1)
with open(os.path.join(PREVIEWS, "studio_mesh.json"), "w", encoding="utf-8") as f:
    json.dump(studio, f)

# Материалы: матовый пластик с лёгким бликом.
for obj in objects:
    code = C[obj.name.split("_", 2)[2]]
    mat = bpy.data.materials.get("V2_" + code) or bpy.data.materials.new("V2_" + code)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_rgb(code), 1)
    bsdf.inputs["Roughness"].default_value = 0.42
    obj.data.materials.clear()
    obj.data.materials.append(mat)

# Свет и сцена: тёмный фон как на референсе; мягкий ключевой, заполняющий и контровой.
scene = bpy.context.scene
engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
scene.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in
                                                        scene.view_settings.bl_rna.properties["view_transform"].enum_items] \
    else "Standard"
try:
    scene.eevee.use_raytracing = True
    scene.eevee.fast_gi_method = "GLOBAL_ILLUMINATION"
except AttributeError:
    pass
world = bpy.data.worlds.new("W")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.07, 0.13, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
scene.world = world


def area(name, loc, energy, size, color=(1, 1, 1)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.size, data.color = energy, size, color
    obj = bpy.data.objects.new(name, data)
    obj.location = to_bl(loc)
    obj.rotation_euler = (obj.location - to_bl((0.2, 1.3, 0))).to_track_quat("Z", "Y").to_euler()
    scene.collection.objects.link(obj)


area("Key", (-4, 6, -5), 900, 4)
area("Fill", (5, 3, -3), 300, 5, (0.85, 0.9, 1))
area("Rim", (1, 5, 5), 500, 3)
floor = bpy.data.meshes.new("Floor")
floor.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)])
floor_obj = bpy.data.objects.new("Floor", floor)
fm = bpy.data.materials.new("FloorMat")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.045, 0.09, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
floor.materials.append(fm)
collection.objects.link(floor_obj)

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def shot(name, eye, target, lens, res=(900, 1100)):
    scene.render.resolution_x, scene.render.resolution_y = res
    cam_data.lens = lens
    cam.location = to_bl(eye)
    cam.rotation_euler = (cam.location - to_bl(target)).to_track_quat("Z", "Y").to_euler()
    scene.render.filepath = os.path.join(PREVIEWS, name + ".png")
    bpy.ops.render.render(write_still=True)


shot("v2_front", (0.2, 1.45, -9), (0.2, 1.35, 0), 50)
shot("v2_side", (9, 1.45, 0.2), (0.2, 1.35, 0), 50)
shot("v2_34", (-4.6, 3.6, -6.4), (0.2, 1.3, 0), 45)
shot("v2_relief", (-2.3, 1.7, 1.6), (-1.1, 1.3, 0.2), 70, res=(900, 900))

# Сравнение с референсом: референс слева, эталон справа, одинаковая высота.
if REFERENCE and os.path.exists(REFERENCE):
    ref = bpy.data.images.load(REFERENCE)
    ours = bpy.data.images.load(os.path.join(PREVIEWS, "v2_front.png"))
    h = 1100
    ref.scale(int(ref.size[0] * h / ref.size[1]), h)
    ours.scale(int(ours.size[0] * h / ours.size[1]), h)
    a = np.array(ref.pixels[:]).reshape(h, ref.size[0], 4)
    b = np.array(ours.pixels[:]).reshape(h, ours.size[0], 4)
    gap = np.ones((h, 30, 4))
    out = np.concatenate([a, gap, b], axis=1)
    img = bpy.data.images.new("compare", out.shape[1], h)
    img.pixels = out.ravel()
    img.filepath_raw = os.path.join(PREVIEWS, "v2_compare.png")
    img.file_format = "PNG"
    img.save()

print(f"ETALON_OK triangles={tris} parts={len(objects)}")

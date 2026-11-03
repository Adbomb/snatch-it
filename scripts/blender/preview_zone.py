"""Предпросмотр зоны без Roblox Studio: строит детали из JSON (scripts/lune/export_zone.luau) и рендерит виды в PNG.

Только для глаз разработчика и заказчика — в игру ничего не попадает. Детали: Block — куб, Cylinder — цилиндр по оси
X (как в Roblox), Ball — шар; Neon светится, Glass полупрозрачное. Оси Roblox (Y вверх) → Blender (Z вверх):
(x, y, z) → (x, −z, y). Пупырышков (MaterialVariant) нет — только формы и цвета.

Запуск:
  blender --background --factory-startup --python scripts/blender/preview_zone.py -- <zone.json> <папка для PNG>
Виды: entrance (от входа в зону на босса), top (сверху), left и right (вдоль торговых рядов), boss (площадка).
Стекло (прозрачность > 0.4) не рисуется — видно, что внутри витрин и автоматов.
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SOURCE = argv[0] if argv else "zone.json"
OUT = argv[1] if len(argv) > 1 else "."

P = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))  # Roblox → Blender


def to_blender(v):
    return P @ Vector(v)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def build(data):
    meshes = {}

    def base(shape):
        if shape in meshes:
            return meshes[shape]
        if shape == "Cylinder":
            bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.5, depth=1.0)
            obj = bpy.context.active_object
            obj.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))  # ось цилиндра — X, как в Roblox
        elif shape == "Ball":
            bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=0.5)
            obj = bpy.context.active_object
        else:
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            obj = bpy.context.active_object
        mesh = obj.data
        bpy.data.objects.remove(obj)
        meshes[shape] = mesh
        return mesh

    for i, b in enumerate(data["bricks"]):
        if b["t"] > 0.4:
            continue
        shape = b["shape"] if b["shape"] in ("Cylinder", "Ball") else "Block"
        obj = bpy.data.objects.new(f"b{i}", base(shape))
        bpy.context.scene.collection.objects.link(obj)
        cf = b["cf"]
        rot = Matrix(((cf[3], cf[4], cf[5]), (cf[6], cf[7], cf[8]), (cf[9], cf[10], cf[11])))
        # Размеры заданы в осях детали Roblox: масштаб и поворот — в осях Roblox, затем перевод в оси Blender.
        linear = P @ rot @ Matrix.Diagonal(Vector(b["s"])) @ P.transposed()
        obj.matrix_world = Matrix.Translation(to_blender(cf[0:3])) @ linear.to_4x4()
        bright = 1.25 if b["mat"] == "Neon" else 1.0  # неон чуть светлее: в Workbench нет свечения
        color = [min(1.0, ch * bright) for ch in b["c"]]
        obj.color = (color[0], color[1], color[2], 1.0)


def setup_render(scene):
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "OBJECT"
    shading.show_shadows = True
    shading.shadow_intensity = 0.35
    shading.show_cavity = True
    shading.cavity_type = "WORLD"
    shading.show_object_outline = True
    shading.object_outline_color = (0.08, 0.08, 0.1)
    scene.display.light_direction = (0.35, -0.45, 0.82)
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("sky")
    scene.world.color = (0.62, 0.8, 0.95)
    scene.view_settings.view_transform = "Standard"


def camera(scene, name, location, target, lens=24, ortho=None):
    cam = bpy.data.cameras.new(name)
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    else:
        cam.lens = lens
    cam.clip_end = 2000
    obj = bpy.data.objects.new(name, cam)
    scene.collection.objects.link(obj)
    obj.location = to_blender(location)
    direction = to_blender(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = obj
    return obj


def main():
    with open(SOURCE, encoding="utf-8") as f:
        data = json.load(f)
    clear()
    scene = bpy.context.scene
    build(data)
    setup_render(scene)
    cx, cy, cz = data["center"]
    # Локальные координаты зоны: +X зоны = −X мира, вход — мировая z центра + 47.5 (вход на +Z мира).
    boss = (cx, cy + 7, cz + 5)
    views = {
        "entrance": ((cx, cy + 16, cz + 78), boss, 22, None),
        "top": ((cx, cy + 300, cz + 0.01), (cx, cy, cz), 24, 200),
        "left": ((cx + 30, cy + 9, cz + 46), (cx + 82, cy + 5, cz - 10), 20, None),
        "right": ((cx - 30, cy + 9, cz + 46), (cx - 82, cy + 5, cz - 10), 20, None),
        "boss": ((cx + 14, cy + 9, cz + 30), boss, 26, None),
    }
    os.makedirs(OUT, exist_ok=True)
    for name, (location, target, lens, ortho) in views.items():
        camera(scene, name, location, target, lens, ortho)
        scene.render.filepath = os.path.join(OUT, f"zone{data['zone']}_{name}.png")
        bpy.ops.render.render(write_still=True)
        print("written", scene.render.filepath)


main()

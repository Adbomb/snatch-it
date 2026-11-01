"""Ваза v11 (2026-11-01) — по замечанию владельца к v10: как утка/цыплёнок/собака из TikTok — чистые гладкие блоки
сплошного цвета, без текстуры квадратов. Силуэт — с листа стиля (ярусы квадратного сечения, ручки-скобы, устье);
детали — отдельные плоские накладки другого цвета (как клюв и глаза у утки): меандр на поясе — выпуклые пластины.
Поверхность — только цвет + мягкая запечённая тень в стыках (окклюзия), до 3 000 тр.

Пишет assets/models/ArtV11_Vase.fbx, assets/textures/art/v11_vase_{color,roughness}.png, превью (повороты,
деталь, масштаб с манекеном) и данные меша для Studio.
Запуск: blender --background --factory-startup --python scripts/blender/art_v11_flat.py -- <репо> <превью>
"""

import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
TEXDIR = os.path.join(REPO, "assets", "textures", "art")
os.makedirs(PREVIEWS, exist_ok=True)
os.makedirs(TEXDIR, exist_ok=True)

TEX = 1024
BEVEL = 0.04  # небольшая фаска, как у блоков утки
COLORS = {"orange": "F7901C", "cream": "F4D6A4", "band": "E5701A", "key": "FFC24A", "inside": "6B3312"}

# Ярусы снизу вверх: (ширина, высота, цвет). Перекрытие 0.02 — без совпадающих граней.
TIERS = [(1.35, 0.2, "orange"), (1.0, 0.2, "orange"), (1.2, 0.26, "cream"), (1.55, 0.3, "cream"),
         (1.85, 0.34, "cream"), (2.05, 0.6, "band"), (1.9, 0.55, "cream"), (1.2, 0.25, "cream"),
         (1.55, 0.34, "orange")]
HEIGHT = sum(t[1] for t in TIERS)
# Меандр: «ключ» из непересекающихся прямоугольников (столбец, строка сверху, ширина, высота) в клетках 5 × 5.
KEY_RECTS = [(0, 0, 1, 5), (1, 0, 4, 1), (4, 1, 1, 3), (2, 2, 1, 2), (3, 3, 1, 1)]
CELL = 0.1
KEY_DEPTH = 0.05


def rgb(code):
    return [int(code[i : i + 2], 16) / 255 for i in (0, 2, 4)]


def lin(code):
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb(code)]


def to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def flat_material(name, code):
    """Сплошной цвет; для запекания тот же цвет идёт в эмиссию."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*lin(code), 1)
    bsdf.inputs["Emission Color"].default_value = (*lin(code), 1)
    bsdf.inputs["Roughness"].default_value = 0.5
    target = nt.nodes.new("ShaderNodeTexImage")
    target.name = "BakeTarget"
    return mat


def box(x0, x1, y0, y1, z0, z1, bevel=BEVEL, segments=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=segments, affect="EDGES", profile=0.5,
                        clamp_overlap=True)
    return bm


def add(target, part, mat_index, matrix=None):
    if matrix is not None:
        bmesh.ops.transform(part, matrix=matrix, verts=part.verts)
    for f in part.faces:
        f.material_index = mat_index
    me = bpy.data.meshes.new("_part")
    part.to_mesh(me)
    part.free()
    target.from_mesh(me)
    bpy.data.meshes.remove(me)


for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
scene = bpy.context.scene
collection = bpy.data.collections.new("ArtV11")
scene.collection.children.link(collection)
mats = [flat_material(name, code) for name, code in COLORS.items()]
M = {name: i for i, name in enumerate(COLORS)}

vase = bmesh.new()
z = 0.0
band_z = None
for i, (width, height, kind) in enumerate(TIERS):
    z0, z1 = (z - 0.02 if i else 0.0), z + height
    half = width / 2
    part = box(-half, half, -half, half, z0, z1)
    if kind == "band":
        band_z = (z, z1, half)
    if i == len(TIERS) - 1:  # устье: верх — рамка, середина уходит вниз
        top = max(part.faces, key=lambda f: (f.calc_center_median().z, f.calc_area()))
        bmesh.ops.inset_individual(part, faces=[top], thickness=0.2, depth=0.0)
        ret = bmesh.ops.extrude_face_region(part, geom=[top])
        bmesh.ops.translate(part, vec=(0, 0, -0.3), verts=[e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)])
        bmesh.ops.delete(part, geom=[top], context="FACES")
        bmesh.ops.recalc_face_normals(part, faces=part.faces)
        inner = half - 0.2 - BEVEL + 0.001
        for f in part.faces:
            c = f.calc_center_median()
            inside = abs(c.x) < inner and abs(c.y) < inner and c.z > z1 - 0.32
            f.material_index = M["inside"] if inside else M[kind]
        me = bpy.data.meshes.new("_lip")
        part.to_mesh(me)
        part.free()
        vase.from_mesh(me)
        bpy.data.meshes.remove(me)
    else:
        add(vase, part, M["band" if kind == "band" else kind])
    z = z1

# Меандр: по два «ключа» на каждой грани пояса — плоские выпуклые накладки.
bz0, bz1, bhalf = band_z
key_w = 5 * CELL
for k in range(4):
    turn = Matrix.Rotation(math.pi / 2 * k, 4, "Z")
    for cx in (-0.5, 0.5):
        left, top = cx - key_w / 2, (bz0 + bz1) / 2 + key_w / 2
        for col, row, w, h in KEY_RECTS:
            x0, x1 = left + col * CELL, left + (col + w) * CELL
            zt, zb = top - row * CELL, top - (row + h) * CELL
            add(vase, box(x0, x1, -bhalf - KEY_DEPTH, -bhalf + 0.02, zb, zt, bevel=0), M["key"], turn)

# Ручки-скобы: от пояса наружу, вверх и обратно в плечо.
shoulder_top = bz1 + TIERS[6][1]
for s in (1, -1):
    for (xa, xb), (za, zb), bev in (((0.95, 1.42), (bz0 + 0.12, bz0 + 0.38), BEVEL),
                                    ((1.28, 1.58), (bz0 + 0.12, shoulder_top - 0.08), 0.08),
                                    ((0.85, 1.45), (shoulder_top - 0.34, shoulder_top - 0.08), BEVEL)):
        xs = sorted((s * xa, s * xb))
        add(vase, box(xs[0], xs[1], -0.16, 0.16, za, zb, bevel=bev), M["orange"])

mesh = bpy.data.meshes.new("ArtV11_Vase")
vase.to_mesh(mesh)
vase.free()
obj = bpy.data.objects.new("ArtV11_Vase", mesh)
collection.objects.link(obj)
for m in mats:
    mesh.materials.append(m)
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
mesh.calc_loop_triangles()
TRIS = len(mesh.loop_triangles)

# ── Развёртка и запекание: цвет + окклюзия ───────────────────────────────────────────────────────────────
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.004)
bpy.ops.object.mode_set(mode="OBJECT")
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.render.bake.margin = 12
scene.world = scene.world or bpy.data.worlds.new("Bake")
scene.world.light_settings.distance = 0.5


def bake(kind):
    img = bpy.data.images.new(f"bake_{kind}", TEX, TEX, alpha=False, float_buffer=True)
    for m in mats:
        target = m.node_tree.nodes["BakeTarget"]
        target.image = img
        m.node_tree.nodes.active = target
        bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Emission Strength"].default_value = 1.0 if kind == "color" else 0.0
    scene.cycles.samples = 1 if kind == "color" else 64
    bpy.ops.object.bake(type="EMIT" if kind == "color" else "AO")
    arr = np.empty(TEX * TEX * 4, np.float32)
    img.pixels.foreach_get(arr)
    return arr.reshape(TEX, TEX, 4)[::-1, :, :3]


color, ao = bake("color"), bake("ao")


def save(path, arr):
    h, w = arr.shape[:2]
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = arr
    img.pixels.foreach_set(rgba[::-1].ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()


maps = {"color": to_srgb(color * (0.62 + 0.38 * ao[..., :1])), "roughness": np.full((64, 64, 3), 0.5, np.float32)}
for kind, arr in maps.items():
    save(os.path.join(TEXDIR, f"v11_vase_{kind}.png"), arr)

final = bpy.data.materials.new("ArtV11_Vase")
final.use_nodes = True
final.use_backface_culling = True  # как в Roblox
nt = final.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
for kind in maps:
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(TEXDIR, f"v11_vase_{kind}.png"))
    t.image.colorspace_settings.name = "sRGB" if kind == "color" else "Non-Color"
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color" if kind == "color" else "Roughness"])
mesh.materials.clear()
mesh.materials.append(final)
for poly in mesh.polygons:
    poly.material_index = 0

bpy.ops.export_scene.fbx(filepath=os.path.join(REPO, "assets", "models", "ArtV11_Vase.fbx"), use_selection=True,
                         apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                         mesh_smooth_type="FACE", path_mode="STRIP")
uvl = mesh.uv_layers.active.data
verts, index, tri = [], {}, []
for lt in mesh.loop_triangles:
    ids = []
    for li in lt.loops:
        co = mesh.vertices[mesh.loops[li].vertex_index].co
        nr = mesh.corner_normals[li].vector
        uv = uvl[li].uv
        k = (round(co.x, 4), round(co.y, 4), round(co.z, 4), round(nr.x, 3), round(nr.y, 3), round(nr.z, 3),
             round(uv[0], 5), round(uv[1], 5))
        if k not in index:
            index[k] = len(verts)
            verts.append(k)
        ids.append(index[k])
    tri.append(ids)
with open(os.path.join(PREVIEWS, "studio_mesh.json"), "w", encoding="utf-8") as f:
    json.dump({"v": [[k[0], k[2], -k[1]] for k in verts], "n": [[k[3], k[5], -k[4]] for k in verts],
               "uv": [[k[6], 1 - k[7]] for k in verts], "t": tri}, f)

# ── Превью: тёмный фон, повороты, деталь, масштаб с манекеном ────────────────────────────────────────────
engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
try:
    scene.eevee.use_raytracing = True
except AttributeError:
    pass
world = bpy.data.worlds.new("Studio")
world.use_nodes = True
wbg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
wbg.inputs["Color"].default_value = (0.75, 0.78, 0.85, 1)
wbg.inputs["Strength"].default_value = 0.55
scene.world = world
floor = bpy.data.meshes.new("Floor")
sweep = [(-60.0, 0.0), (5.0, 0.0)] + [(5.0 + 8 * math.sin(math.pi / 2 * k / 12), 8 - 8 * math.cos(math.pi / 2 * k / 12))
                                    for k in range(1, 13)] + [(13.0, 40.0)]
floor.from_pydata([(x, y, zz) for (y, zz) in sweep for x in (-60.0, 60.0)], [],
                  [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(sweep) - 1)])
for poly in floor.polygons:
    poly.use_smooth = True
fm = bpy.data.materials.new("Floor")
fm.use_nodes = True
fb = next(n for n in fm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
fb.inputs["Base Color"].default_value = (0.018, 0.022, 0.04, 1)
fb.inputs["Roughness"].default_value = 0.6
floor.materials.append(fm)
collection.objects.link(bpy.data.objects.new("Floor", floor))
for name, loc, energy, size in (("Key", (-5, -9, 9), 1900, 7), ("Fill", (7, -6, 4), 900, 8), ("Rim", (2, 8, 7), 1600, 6)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.size = energy, size
    light = bpy.data.objects.new(name, data)
    light.location = loc
    light.rotation_euler = (Vector(loc) - Vector((0, 0, 1.5))).to_track_quat("Z", "Y").to_euler()
    scene.collection.objects.link(light)
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def shot(name, eye, target, lens, res):
    scene.render.resolution_x, scene.render.resolution_y = res
    cam_data.lens = lens
    cam.location = eye
    cam.rotation_euler = (Vector(eye) - Vector(target)).to_track_quat("Z", "Y").to_euler()
    path = os.path.join(PREVIEWS, name + ".png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


turns = []
for label, angle in (("front", 0), ("34", -40), ("side", -90), ("back", 180)):
    obj.rotation_euler = (0, 0, math.radians(angle))
    turns.append(shot(f"turn_{label}", (0, -9.5, 2.6), (0, 0, 1.5), 75, (700, 900)))
obj.rotation_euler = (0, 0, math.radians(-30))
shot("detail", (0.9, -3.4, 2.0), (0.35, -0.6, 1.55), 70, (900, 900))
obj.rotation_euler = (0, 0, 0)

grey = bpy.data.materials.new("Mannequin")
grey.use_nodes = True
next(n for n in grey.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (
    *lin("9FA9BC"), 1)
for center, size in (((0, 0, 4.65), (1.15, 1.15, 1.15)), ((0, 0, 3.2), (2.0, 1.0, 1.75)),
                     ((-1.5, 0, 3.2), (0.95, 0.95, 1.75)), ((1.5, 0, 3.2), (0.95, 0.95, 1.75)),
                     ((-0.5, 0, 1.15), (0.95, 0.95, 2.3)), ((0.5, 0, 1.15), (0.95, 0.95, 2.3))):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.05, segments=2, affect="EDGES")
    bmesh.ops.translate(bm, vec=Vector(center) + Vector((4.0, 0.2, 0)), verts=bm.verts)
    me = bpy.data.meshes.new("Mannequin")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(grey)
    collection.objects.link(bpy.data.objects.new("Mannequin", me))
shot("scale", (2.2, -12, 3.6), (2.2, 0, 2.4), 45, (1000, 900))

tiles = []
for path in turns:
    im = bpy.data.images.load(path)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(px)
    tiles.append(px.reshape(h, w, 4))
strip = np.concatenate(tiles, axis=1)
out = bpy.data.images.new("turns", strip.shape[1], strip.shape[0], alpha=False)
out.colorspace_settings.name = "Non-Color"
out.pixels.foreach_set(strip.ravel())
out.filepath_raw = os.path.join(PREVIEWS, "turns.png")
out.file_format = "PNG"
out.save()
print(f"V11_OK {TRIS} тр.")

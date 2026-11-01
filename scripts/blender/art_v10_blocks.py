"""Ваза v10 — по листу стиля владельца («Пример одного предмета — ваза», вариант А, 2026-11-01): ступенчатый
силуэт из крупных блоков квадратного сечения с мягкими фасками; на всех гранях — квадратный рельеф со скруглёнными
углами (крупные плитки-«подушки», ~5 на ширину венчика); на оранжевом поясе — выпуклый меандр; блочные ручки-скобы;
у венчика настоящее устье. Рельеф — не геометрия, а запечённые карты (цвет с тенью в швах, нормали), до 3 000 тр.

Конвейер: блоки (bmesh, фаски) → один меш → Smart UV → Cycles: цвет (EMIT), окклюзия (AO), нормали (NORMAL из
Bump) → assets/textures/art/v10_vase_{color,normal,roughness}.png; меш — assets/models/ArtV10_Vase.fbx.
Превью как на листе: спереди, 3/4, сбоку, сзади, деталь рельефа, масштаб рядом с манекеном; данные меша для Studio.
Запуск: blender --background --factory-startup --python scripts/blender/art_v10_blocks.py -- <репо> <превью>
"""

import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
TEXDIR = os.path.join(REPO, "assets", "textures", "art")
os.makedirs(PREVIEWS, exist_ok=True)
os.makedirs(TEXDIR, exist_ok=True)

TEX = 1024
TILE = 0.34  # желаемый размер плитки рельефа, стад
BEVEL = 0.06  # мягкая фаска блоков
COLORS = {"orange": "F28A1C", "cream": "F4D8AA", "band": "E06E14", "key": "FF9F33", "inside": "5A2A10"}

# Ярусы снизу вверх: (ширина, высота, материал). Перекрытие 0.02 — без совпадающих граней.
TIERS = [(1.35, 0.2, "orange"), (1.0, 0.2, "orange"), (1.2, 0.26, "cream"), (1.55, 0.3, "cream"),
         (1.85, 0.34, "cream"), (2.05, 0.6, "band"), (1.9, 0.55, "cream"), (1.2, 0.25, "cream"),
         (1.55, 0.34, "orange")]
HEIGHT = sum(t[1] for t in TIERS)


def rgb(code):
    return [int(code[i : i + 2], 16) / 255 for i in (0, 2, 4)]


def lin(code):
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb(code)]


def to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


# ── Материалы: плитки и меандр в координатах граней ──────────────────────────────────────────────────────
def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for key, value in inputs.items():
        if isinstance(value, (int, float, tuple, list)):
            n.inputs[key].default_value = value
        else:
            nt.links.new(value, n.inputs[key])
    return n


def math_op(nt, op, a, b=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


def face_coords(nt):
    """(u, v, top): u — вдоль грани, v — вверх; на горизонтальных гранях u, v = x, y; top = 1 на горизонтальных."""
    coord = nt.nodes.new("ShaderNodeTexCoord")
    p = node(nt, "ShaderNodeSeparateXYZ", Vector=coord.outputs["Object"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nrm = node(nt, "ShaderNodeSeparateXYZ", Vector=geo.outputs["Normal"])
    ax, ay, az = (math_op(nt, "ABSOLUTE", nrm.outputs[k]) for k in "XYZ")
    top = math_op(nt, "GREATER_THAN", az, 0.7)
    side_x = math_op(nt, "GREATER_THAN", ax, ay)  # грань смотрит по x → вдоль неё идёт y
    along = math_op(nt, "ADD", p.outputs["X"], math_op(nt, "MULTIPLY", side_x,
                                                       math_op(nt, "SUBTRACT", p.outputs["Y"], p.outputs["X"])))
    u = math_op(nt, "ADD", along, math_op(nt, "MULTIPLY", top, math_op(nt, "SUBTRACT", p.outputs["X"], along)))
    v = math_op(nt, "ADD", p.outputs["Z"], math_op(nt, "MULTIPLY", top,
                                                   math_op(nt, "SUBTRACT", p.outputs["Y"], p.outputs["Z"])))
    return u, v, top, p.outputs["Z"]


def tiles_height(nt, u, v, size_u, size_v, off_u, off_v):
    """Плитка-«подушка»: 1 на плитке, 0 в шве; скругление углов и мягкий скат к шву."""
    gap, rad, slope = 0.06, 0.2, 0.16
    d2 = None
    for coord, size, off in ((u, size_u, off_u), (v, size_v, off_v)):
        q = math_op(nt, "SUBTRACT", math_op(nt, "FRACT", math_op(nt, "DIVIDE", math_op(nt, "SUBTRACT", coord, off),
                                                                size)), 0.5)
        d = math_op(nt, "MAXIMUM", math_op(nt, "SUBTRACT", math_op(nt, "ABSOLUTE", q), 0.5 - gap - rad), 0.0)
        sq = math_op(nt, "MULTIPLY", d, d)
        d2 = sq if d2 is None else math_op(nt, "ADD", d2, sq)
    dist = math_op(nt, "SUBTRACT", math_op(nt, "SQRT", d2), rad)
    rng = node(nt, "ShaderNodeMapRange", Value=dist)
    rng.interpolation_type = "SMOOTHSTEP"
    rng.inputs["From Min"].default_value, rng.inputs["From Max"].default_value = -slope, 0.0
    rng.inputs["To Min"].default_value, rng.inputs["To Max"].default_value = 1.0, 0.0
    return rng.outputs["Result"]


def finish(nt, color, height, z, rough=0.5):
    """Цвет × свет сверху → эмиссия (для запекания) и Base Color; рельеф → Bump → нормаль."""
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    light = node(nt, "ShaderNodeMapRange", Value=z)
    light.inputs["From Min"].default_value, light.inputs["From Max"].default_value = 0.0, HEIGHT
    light.inputs["To Min"].default_value, light.inputs["To Max"].default_value = 0.84, 1.04
    lit = node(nt, "ShaderNodeMixRGB", Fac=1.0, Color1=color, Color2=light.outputs["Result"])
    lit.blend_type = "MULTIPLY"
    nt.links.new(lit.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(lit.outputs["Color"], bsdf.inputs["Emission Color"])
    bump = node(nt, "ShaderNodeBump", Height=height, Strength=1.0, Distance=0.035)
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = rough
    target = nt.nodes.new("ShaderNodeTexImage")
    target.name = "BakeTarget"


def tile_material(name, base, width, z0, z1):
    """Плитки, подогнанные к ярусу: целое число по ширине и по высоте, швы от края грани."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    u, v, top, z = face_coords(nt)
    n_u, n_v = max(1, round(width / TILE)), max(1, round((z1 - z0) / TILE))
    size_u, size_v_side = width / n_u, (z1 - z0) / n_v
    size_v = math_op(nt, "ADD", size_v_side, math_op(nt, "MULTIPLY", top, size_u - size_v_side))
    off_v = math_op(nt, "ADD", z0, math_op(nt, "MULTIPLY", top, -width / 2 - z0))
    h = tiles_height(nt, u, v, size_u, size_v, -width / 2, off_v)
    shade = math_op(nt, "ADD", 0.74, math_op(nt, "MULTIPLY", h, 0.26))  # шов чуть темнее плитки
    col = node(nt, "ShaderNodeMixRGB", Fac=1.0, Color1=(*lin(base), 1), Color2=shade)
    col.blend_type = "MULTIPLY"
    finish(nt, col.outputs["Color"], h, z)
    return mat


def key_image():
    """Маска меандра на один «ключ»: R — высота (с мягким скатом), G — тёмный контур."""
    glyph = np.array([[1, 1, 1, 1, 1, 0],
                      [1, 0, 0, 0, 1, 0],
                      [1, 0, 1, 0, 1, 0],
                      [1, 0, 1, 1, 1, 0],
                      [1, 0, 0, 0, 0, 0]], np.float32)
    w, h = 384, 224
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    gx = ((xx / w - 0.09) / 0.84 * 6).astype(int)
    gy = ((yy / h - 0.12) / 0.76 * 5).astype(int)
    inside = (gx >= 0) & (gx < 6) & (gy >= 0) & (gy < 5)
    mask = np.where(inside, glyph[np.clip(gy, 0, 4), np.clip(gx, 0, 5)], 0).astype(np.float32)
    soft = mask.copy()
    for _ in range(3):  # мягкий скат
        soft = (soft + np.roll(soft, 1, 0) + np.roll(soft, -1, 0) + np.roll(soft, 1, 1) + np.roll(soft, -1, 1)) / 5
    gy_, gx_ = np.gradient(soft)
    edge = np.clip(np.hypot(gx_, gy_) * 6, 0, 1)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = soft, edge, 0
    img = bpy.data.images.new("KeyMask", w, h, alpha=False, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(rgba[::-1].ravel())
    img.pack()
    return img


def band_material(width, z0, z1):
    mat = bpy.data.materials.new("band")
    mat.use_nodes = True
    nt = mat.node_tree
    u, v, top, z = face_coords(nt)
    keys = 2  # ключей на грань
    cu = math_op(nt, "DIVIDE", math_op(nt, "SUBTRACT", u, -width / 2), width / keys)
    cv = math_op(nt, "DIVIDE", math_op(nt, "SUBTRACT", v, z0), z1 - z0)
    vec = node(nt, "ShaderNodeCombineXYZ", X=cu, Y=cv)
    tex = node(nt, "ShaderNodeTexImage", Vector=vec.outputs["Vector"])
    tex.image, tex.extension, tex.interpolation = KEY_IMAGE, "REPEAT", "Linear"
    chan = node(nt, "ShaderNodeSeparateColor", Color=tex.outputs["Color"])
    side = math_op(nt, "SUBTRACT", 1.0, top)
    h = math_op(nt, "MULTIPLY", chan.outputs["Red"], side)
    edge = math_op(nt, "MULTIPLY", chan.outputs["Green"], side)
    col = node(nt, "ShaderNodeMixRGB", Fac=h, Color1=(*lin(COLORS["band"]), 1), Color2=(*lin(COLORS["key"]), 1))
    dark = node(nt, "ShaderNodeMixRGB", Fac=math_op(nt, "MULTIPLY", edge, 0.55), Color1=col.outputs["Color"],
                Color2=(0.02, 0.008, 0.0, 1))
    finish(nt, dark.outputs["Color"], h, z)
    return mat


def plain_material(name, base):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    coord = nt.nodes.new("ShaderNodeTexCoord")
    p = node(nt, "ShaderNodeSeparateXYZ", Vector=coord.outputs["Object"])
    rgbn = nt.nodes.new("ShaderNodeRGB")
    rgbn.outputs[0].default_value = (*lin(base), 1)
    finish(nt, rgbn.outputs[0], 0.0, p.outputs["Z"], rough=0.8)
    return mat


# ── Геометрия ────────────────────────────────────────────────────────────────────────────────────────────
def box(x0, x1, y0, y1, z0, z1, bevel=BEVEL, segments=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=segments, affect="EDGES", profile=0.5,
                    clamp_overlap=True)
    return bm


def add(target, part, mat_index):
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
collection = bpy.data.collections.new("ArtV10")
scene.collection.children.link(collection)
KEY_IMAGE = key_image()

mats, vase = [], bmesh.new()
z = 0.0
for i, (width, height, kind) in enumerate(TIERS):
    z0, z1 = (z - 0.02 if i else 0.0), z + height
    half = width / 2
    mats.append(band_material(width, z, z1) if kind == "band" else tile_material(f"tier{i}", COLORS[kind], width,
                                                                                    z, z1))
    part = box(-half, half, -half, half, z0, z1)
    if i == len(TIERS) - 1:  # устье: верхняя грань — рамка, середина уходит вниз
        top = max(part.faces, key=lambda f: (f.calc_center_median().z, f.calc_area()))
        bmesh.ops.inset_individual(part, faces=[top], thickness=0.2, depth=0.0)
        ret = bmesh.ops.extrude_face_region(part, geom=[top])
        bmesh.ops.translate(part, vec=(0, 0, -0.3), verts=[e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)])
        bmesh.ops.delete(part, geom=[top], context="FACES")
        bmesh.ops.recalc_face_normals(part, faces=part.faces)
        inner = half - 0.2 - BEVEL + 0.001
        mats.append(plain_material("inside", COLORS["inside"]))
        for f in part.faces:
            c = f.calc_center_median()
            f.material_index = len(mats) - 1 if (abs(c.x) < inner and abs(c.y) < inner and c.z > z1 - 0.32) else i
        me = bpy.data.meshes.new("_lip")
        part.to_mesh(me)
        part.free()
        vase.from_mesh(me)
        bpy.data.meshes.remove(me)
    else:
        add(vase, part, i)
    z = z1

# Ручки-скобы: от пояса наружу, вверх и обратно в плечо.
band_z = sum(t[1] for t in TIERS[:5])
shoulder_top = band_z + TIERS[5][1] + TIERS[6][1]
handle_mat = len(mats)
mats.append(tile_material("handle", COLORS["orange"], 0.32, band_z, shoulder_top))
for s in (1, -1):
    xs = sorted((s * 0.95, s * 1.42))
    add(vase, box(xs[0], xs[1], -0.16, 0.16, band_z + 0.12, band_z + 0.38), handle_mat)
    xs = sorted((s * 1.28, s * 1.58))
    add(vase, box(xs[0], xs[1], -0.16, 0.16, band_z + 0.12, shoulder_top - 0.08, bevel=0.1), handle_mat)
    xs = sorted((s * 0.85, s * 1.45))
    add(vase, box(xs[0], xs[1], -0.16, 0.16, shoulder_top - 0.34, shoulder_top - 0.08), handle_mat)

mesh = bpy.data.meshes.new("ArtV10_Vase")
vase.to_mesh(mesh)
vase.free()
obj = bpy.data.objects.new("ArtV10_Vase", mesh)
collection.objects.link(obj)
for m in mats:
    mesh.materials.append(m)
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
mesh.calc_loop_triangles()
TRIS = len(mesh.loop_triangles)

# ── Развёртка и запекание ────────────────────────────────────────────────────────────────────────────────
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
        nt = m.node_tree
        target = nt.nodes["BakeTarget"]
        target.image = img
        nt.nodes.active = target
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Emission Strength"].default_value = 1.0 if kind == "color" else 0.0
    scene.cycles.samples = {"color": 1, "ao": 64, "normal": 8}[kind]
    if kind == "normal":
        bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
    else:
        bpy.ops.object.bake(type="EMIT" if kind == "color" else "AO")
    arr = np.empty(TEX * TEX * 4, np.float32)
    img.pixels.foreach_get(arr)
    return arr.reshape(TEX, TEX, 4)[::-1, :, :3]


color, ao, normal = bake("color"), bake("ao"), bake("normal")


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


maps = {"color": to_srgb(color * (0.5 + 0.5 * ao[..., :1])), "normal": normal,
        "roughness": np.full((64, 64, 3), 0.5, np.float32)}
for kind, arr in maps.items():
    save(os.path.join(TEXDIR, f"v10_vase_{kind}.png"), arr)

final = bpy.data.materials.new("ArtV10_Vase")
final.use_nodes = True
final.use_backface_culling = True  # как в Roblox
nt = final.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
for kind in maps:
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(TEXDIR, f"v10_vase_{kind}.png"))
    t.image.colorspace_settings.name = "sRGB" if kind == "color" else "Non-Color"
    if kind == "normal":
        nmap = node(nt, "ShaderNodeNormalMap", Color=t.outputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    else:
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color" if kind == "color" else "Roughness"])
mesh.materials.clear()
mesh.materials.append(final)
for poly in mesh.polygons:
    poly.material_index = 0

bpy.ops.export_scene.fbx(filepath=os.path.join(REPO, "assets", "models", "ArtV10_Vase.fbx"), use_selection=True,
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

# ── Превью: тёмно-синий фон как на листе, повороты, деталь, масштаб с манекеном ──────────────────────────
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
for name, loc, energy, size in (("Key", (-5, -9, 9), 2600, 7), ("Fill", (7, -6, 4), 900, 8), ("Rim", (2, 8, 7), 1600, 6)):
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

# Манекен Roblox (R15, ≈ 5.2) справа — масштаб.
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

# Полоса поворотов, как на листе.
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
print(f"V10_OK {TRIS} тр.")

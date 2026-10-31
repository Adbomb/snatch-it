"""Эталон стиля предметов v4 (замечания владельца 2026-10-31): цельная гладкая модель с кубическим характером, а не
воксели. Ваза — «Амфора с меандром» (босс 8, Common).

Корпус — один гладкий лофт: в сечении скруглённый квадрат (кубический характер), по высоте — пята, ножка, тело с
прямыми стенками, плечо, горло и раструб; мягкие скругления — частые кольца у переходов. Ручки — гладкие петли
(протяжка скруглённого квадрата по кривой). Квадратный рельеф — только декор: выпуклый пояс с меандром и несколько
скруглённых квадратных панелей на стенках. Цвета — роли, как у гантелей; материал в игре — SmoothPlastic.

Запуск: blender --background --factory-startup --python scripts/blender/art_v4_vase.py -- <репо> <превью>
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(PREVIEWS, exist_ok=True)

CREAM, ORANGE, KEY, INSIDE = "F7DEB2", "F28A1E", "C2560E", "7A3A12"


def bl(p):
    """Roblox (x вправо, y вверх, z назад) → Blender."""
    return Vector((p[0], -p[2], p[1]))


def hex_rgb(code):
    return tuple((int(code[i : i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4))


def rsquare(hw, ratio=0.38, seg=3):
    """Скруглённый квадрат полуширины hw: четыре дуги-угла (стороны между ними прямые)."""
    r = hw * ratio
    pts = []
    for cx, cz, a0 in ((hw - r, hw - r, 0), (-(hw - r), hw - r, 90), (-(hw - r), -(hw - r), 180),
                       (hw - r, -(hw - r), 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


parts = {}


def part(color):
    return parts.setdefault(color, bmesh.new())


def orient(bm, faces, outward):
    """Нормали граней — от оси вазы (outward) или к оси; Roblox не рисует обратные стороны."""
    for f in faces:
        f.normal_update()
        c = f.calc_center_median()
        radial = Vector((c.x, c.y, 0))
        if radial.length < 1e-6:
            continue
        if (f.normal.dot(radial) > 0) != outward:
            bmesh.ops.reverse_faces(bm, faces=[f])


def loft(color, profile, cap_bottom=False, cap_top=False, outward=True):
    """Кольца (y, полуширина) снизу вверх → гладкая поверхность с сечением «скруглённый квадрат»."""
    bm = part(color)
    rings = [[bm.verts.new(bl((x, y, z))) for x, z in rsquare(hw)] for y, hw in profile]
    n = len(rings[0])
    faces = []
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    orient(bm, faces, outward)
    # Наружная поверхность: низ смотрит вниз, верх — вверх; внутренняя (устье): дно смотрит вверх.
    for ring, want_up, cap in ((rings[0], not outward, cap_bottom), (rings[-1], outward, cap_top)):
        if cap:
            f = bm.faces.new(ring)
            f.normal_update()
            if (f.normal.z > 0) != want_up:
                bmesh.ops.reverse_faces(bm, faces=[f])


def rounded_box(color, center, size, bevel, tilt=None, segments=1):
    """Брусок с фаской (сглаженный — читается мягко скруглённым). tilt — поворот (Matrix 4×4, оси Blender)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(size[0], size[2], size[1]), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=segments, affect="EDGES", clamp_overlap=True)
    if tilt is not None:
        bmesh.ops.transform(bm, matrix=tilt, verts=bm.verts)
    bmesh.ops.translate(bm, vec=bl(center), verts=bm.verts)
    scratch = bpy.data.meshes.get("__v4") or bpy.data.meshes.new("__v4")
    bm.to_mesh(scratch)
    bm.free()
    part(color).from_mesh(scratch)


def tile(color, center, frame, w, h, depth=0.035, corner=0.07, chamfer=0.03):
    """Скруглённый квадрат-«подушечка» на стене: мягкий профиль из трёх колец (низ утоплен в стену)."""
    n, u, v = (Vector(a) for a in frame)
    o = Vector(center)
    bm = part(color)

    def outline(ww, hh, rr):
        rr = min(rr, ww / 2 - 1e-4, hh / 2 - 1e-4)
        pts = []
        for cx, cy, a0 in ((ww / 2 - rr, hh / 2 - rr, 0), (-ww / 2 + rr, hh / 2 - rr, 90),
                           (-ww / 2 + rr, -hh / 2 + rr, 180), (ww / 2 - rr, -hh / 2 + rr, 270)):
            for k in range(3):
                a = math.radians(a0 + 45 * k)
                pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        return pts

    def ring(inset, height):
        return [bm.verts.new(bl(o + u * x + v * y + n * height))
                for x, y in outline(w - 2 * inset, h - 2 * inset, max(corner - inset, 0.01))]

    rings = [ring(0, -0.02), ring(chamfer * 0.45, depth * 0.7), ring(chamfer, depth)]
    count = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for i in range(count):
            j = (i + 1) % count
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(rings[-1])


def sweep(color, path, width, depth, steps=5):
    """Петля-ручка: протяжка скруглённого квадрата width × depth по кривой Catmull-Rom в плоскости x-y."""
    def cr(p0, p1, p2, p3, t):
        return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                      + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)

    pts = [Vector(p) for p in path]
    ext = [pts[0] + (pts[0] - pts[1])] + pts + [pts[-1] + (pts[-1] - pts[-2])]
    curve = []
    for s in range(1, len(ext) - 2):
        for k in range(steps):
            curve.append(cr(ext[s - 1], ext[s], ext[s + 1], ext[s + 2], k / steps))
    curve.append(pts[-1])
    section = [(0.5 * width * x, 0.5 * depth * y) for x, y in
               ((1, 0.55), (0.55, 1), (-0.55, 1), (-1, 0.55), (-1, -0.55), (-0.55, -1), (0.55, -1), (1, -0.55))]
    bm = part(color)
    rings, centers = [], []
    for i, c in enumerate(curve):
        t = (curve[min(i + 1, len(curve) - 1)] - curve[max(i - 1, 0)]).normalized()
        b = Vector((0, 0, 1))
        nrm = b.cross(t).normalized()
        rings.append([bm.verts.new(bl(c + nrm * a + b * d)) for a, d in section])
        centers.append(bl(c))
    m = len(section)
    for ring_a, ring_b, center in zip(rings, rings[1:], centers):
        for i in range(m):
            j = (i + 1) % m
            f = bm.faces.new((ring_a[i], ring_a[j], ring_b[j], ring_b[i]))
            f.normal_update()
            if f.normal.dot(f.calc_center_median() - center) < 0:
                bmesh.ops.reverse_faces(bm, faces=[f])


# ── Корпус ─────────────────────────────────────────────────────────────────────────────────────────────
BELLY = 1.08  # полуширина тела с прямыми стенками
BAND = BELLY + 0.06  # пояс выступает
loft(ORANGE, [(0.0, 0.78), (0.03, 0.84), (0.09, 0.87), (0.21, 0.87), (0.26, 0.83), (0.3, 0.7), (0.34, 0.56),
              (0.44, 0.5), (0.52, 0.53)], cap_bottom=True)
loft(CREAM, [(0.52, 0.53), (0.62, 0.66), (0.72, 0.86), (0.82, 1.0), (0.9, BELLY), (1.27, BELLY)])
loft(ORANGE, [(1.27, BELLY), (1.3, BAND - 0.02), (1.33, BAND), (1.57, BAND), (1.6, BAND - 0.02), (1.63, BELLY)])
loft(CREAM, [(1.63, BELLY), (1.98, BELLY), (2.07, 1.0), (2.16, 0.84), (2.25, 0.64), (2.31, 0.5)])
loft(ORANGE, [(2.31, 0.5), (2.36, 0.42), (2.44, 0.4), (2.62, 0.4), (2.69, 0.47), (2.75, 0.6), (2.8, 0.66),
              (2.9, 0.66), (2.95, 0.6), (2.96, 0.5), (2.96, 0.44)])
loft(INSIDE, [(2.7, 0.33), (2.94, 0.38), (2.96, 0.44)], cap_bottom=True, outward=False)  # устье и его дно

# ── Меандр (греческий ключ) на поясе спереди и сзади: прямые планки с чёткими углами ───────────────────────
T, P = 0.06, 0.035  # толщина планки и выступ над поясом
for zsign in (-1, 1):
    z = zsign * (BAND + P / 2 - 0.004)

    def bar(x0, x1, y0, y1):
        rounded_box(KEY, ((x0 + x1) / 2, (y0 + y1) / 2, z), (x1 - x0, y1 - y0, P), 0.008)

    y0, y1 = 1.35, 1.55  # низ и верх узора
    bar(-0.62, 0.62, y0 - T / 2, y0 + T / 2)  # нижняя линия
    for x0 in (-0.62, 0.02):
        w = 0.56
        bar(x0, x0 + T, y0, y1 + T / 2)  # левая стойка
        bar(x0, x0 + w, y1 - T / 2, y1 + T / 2)  # верх
        bar(x0 + w - T, x0 + w, y1 - 0.13, y1)  # правая стойка вниз
        bar(x0 + w - 0.3, x0 + w, y1 - 0.13 - T, y1 - 0.13)  # загиб внутрь

# ── Скруглённые квадратные панели (рельеф) на прямых стенках спереди и сзади: ряд выше и ряд ниже пояса ────
for y in (1.09, 1.81):
    for i in (-1, 0, 1):
        tile(CREAM, (i * 0.38, y, -BELLY), ((0, 0, -1), (0, 1, 0), (1, 0, 0)), 0.28, 0.28)
        tile(CREAM, (i * 0.38, y, BELLY), ((0, 0, 1), (1, 0, 0), (0, 1, 0)), 0.28, 0.28)

# ── Ручки-петли по бокам: от пояса наружу, вверх и в горло ─────────────────────────────────────────────
for xs in (1, -1):
    path = [(xs * 1.0, 1.45, 0), (xs * 1.36, 1.49, 0), (xs * 1.54, 1.75, 0), (xs * 1.48, 2.08, 0),
            (xs * 1.15, 2.32, 0), (xs * 0.3, 2.47, 0)]
    sweep(ORANGE, path, 0.2, 0.26, steps=3)

# ── Сборка ─────────────────────────────────────────────────────────────────────────────────────────────
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
collection = bpy.data.collections.new("ArtV4")
bpy.context.scene.collection.children.link(collection)
objects = []
for color, bm in parts.items():
    bm.normal_update()
    mesh = bpy.data.meshes.new(f"Art_MeanderAmphora_{color}")
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(obj)
    mat = bpy.data.materials.new("M_" + color)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_rgb(color), 1)
    bsdf.inputs["Roughness"].default_value = 0.4
    mesh.materials.append(mat)
    objects.append(obj)
bpy.ops.object.select_all(action="DESELECT")
for obj in objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = objects[0]
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
tris = 0
for obj in objects:
    obj.data.calc_loop_triangles()
    tris += len(obj.data.loop_triangles)

bpy.ops.export_scene.fbx(filepath=os.path.join(REPO, "assets", "models", "ArtV4_MeanderAmphora.fbx"),
                         use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                         axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP")

# ── Рендер ─────────────────────────────────────────────────────────────────────────────────────────────
scene = bpy.context.scene
engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
try:
    scene.eevee.use_raytracing = True
except AttributeError:
    pass
world = bpy.data.worlds.new("W")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.035, 0.045, 0.085, 1)
scene.world = world
for name, loc, energy, size in (("Key", (-4, 6, -5), 700, 4), ("Fill", (5, 3, -4), 260, 5), ("Back", (0, 5, 6), 400, 4)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.size = energy, size
    light = bpy.data.objects.new(name, data)
    light.location = bl(loc)
    light.rotation_euler = (light.location - bl((0, 1.4, 0))).to_track_quat("Z", "Y").to_euler()
    scene.collection.objects.link(light)
floor = bpy.data.meshes.new("Floor")
floor.from_pydata([(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)], [], [(0, 1, 2, 3)])
fm = bpy.data.materials.new("FloorMat")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.025, 0.035, 0.07, 1)
floor.materials.append(fm)
collection.objects.link(bpy.data.objects.new("Floor", floor))
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def shot(name, eye, target=(0, 1.5, 0), lens=50, res=(800, 900)):
    scene.render.resolution_x, scene.render.resolution_y = res
    cam_data.lens = lens
    cam.location = bl(eye)
    cam.rotation_euler = (cam.location - bl(target)).to_track_quat("Z", "Y").to_euler()
    scene.render.filepath = os.path.join(PREVIEWS, name + ".png")
    bpy.ops.render.render(write_still=True)


shot("front", (0, 1.8, -10))
shot("side", (10, 1.8, 0))
shot("34", (-6.6, 3.6, -7.0))
shot("relief", (-1.2, 1.7, -3.1), (0.0, 1.45, -1.1), 70, res=(800, 800))
print(f"V4_OK triangles={tris} parts={len(objects)}")

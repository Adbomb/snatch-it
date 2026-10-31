"""Три варианта вазы (замечания владельца 2026-10-31): цельный stylized Roblox-проп — округлый гладкий корпус,
крупные чистые ручки, аккуратные горло и пята, крупный простой орнамент; без кубиков и сетки квадратов.
1 — минимализм, 2 — декоративная, 3 — премиум (редкая). Рядом — блочный манекен Roblox (рост ≈ 5.2) для масштаба.

Запуск: blender --background --factory-startup --python scripts/blender/art_v6_vases.py -- <репо> <превью>
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(PREVIEWS, exist_ok=True)

CREAM, ORANGE, DEEP, INSIDE = "F6E2BC", "F28A1E", "D4661A", "6E3414"
GOLD, GEM, MANNEQUIN = "F2C14E", "2E7BEB", "D3D8E0"
SEG = 28  # сегментов по окружности корпуса


def bl(p):
    return Vector((p[0], -p[2], p[1]))


def hex_rgb(code):
    return tuple((int(code[i : i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4))


class Prop:
    """Детали по цветам; offset — где стоит модель (Roblox-координаты)."""

    def __init__(self, name, offset):
        self.name, self.offset = name, Vector(offset)
        self.parts = {}

    def bm(self, color):
        return self.parts.setdefault(color, bmesh.new())

    def lathe(self, color, profile, outward=True, cap_bottom=False, seg=SEG):
        """Тело вращения: (y, радиус) снизу вверх."""
        bm = self.bm(color)
        rings = []
        for y, r in profile:
            ring = []
            for i in range(seg):
                a = 2 * math.pi * i / seg
                ring.append(bm.verts.new(bl(self.offset + Vector((r * math.cos(a), y, r * math.sin(a))))))
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for i in range(seg):
                j = (i + 1) % seg
                f = bm.faces.new((a[i], a[j], b[j], b[i]))
                f.normal_update()
                c = f.calc_center_median() - bl(self.offset)
                radial = Vector((c.x, c.y, 0))
                if radial.length > 1e-6 and (f.normal.dot(radial) > 0) != outward:
                    bmesh.ops.reverse_faces(bm, faces=[f])
        if cap_bottom:
            f = bm.faces.new(rings[0])
            f.normal_update()
            if (f.normal.z > 0) != (not outward):
                bmesh.ops.reverse_faces(bm, faces=[f])

    def handle(self, color, path, rx, rz, steps=4, seg=10):
        """Ручка: протяжка эллипса rx × rz по гладкой кривой в плоскости x-y."""
        def cr(p0, p1, p2, p3, t):
            return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)

        pts = [Vector(p) for p in path]
        ext = [pts[0] + (pts[0] - pts[1])] + pts + [pts[-1] + (pts[-1] - pts[-2])]
        curve = [cr(ext[s - 1], ext[s], ext[s + 1], ext[s + 2], k / steps)
                 for s in range(1, len(ext) - 2) for k in range(steps)] + [pts[-1]]
        bm = self.bm(color)
        rings, centers = [], []
        for i, c in enumerate(curve):
            t = (curve[min(i + 1, len(curve) - 1)] - curve[max(i - 1, 0)]).normalized()
            b = Vector((0, 0, 1))
            n = b.cross(t).normalized()
            ring = []
            for k in range(seg):
                a = 2 * math.pi * k / seg
                ring.append(bm.verts.new(bl(self.offset + c + n * (rx * math.cos(a)) + b * (rz * math.sin(a)))))
            rings.append(ring)
            centers.append(bl(self.offset + c))
        for ra, rb, center in zip(rings, rings[1:], centers):
            for i in range(seg):
                j = (i + 1) % seg
                f = bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
                f.normal_update()
                if f.normal.dot(f.calc_center_median() - center) < 0:
                    bmesh.ops.reverse_faces(bm, faces=[f])

    def piece(self, color, build, matrix):
        """Деталь из bmesh-построителя, перенесённая матрицей (оси Blender) и offset."""
        bm = bmesh.new()
        build(bm)
        bmesh.ops.transform(bm, matrix=Matrix.Translation(bl(self.offset)) @ matrix, verts=bm.verts)
        scratch = bpy.data.meshes.get("__v6") or bpy.data.meshes.new("__v6")
        bm.to_mesh(scratch)
        bm.free()
        self.bm(color).from_mesh(scratch)

    def build(self, collection):
        objs = []
        for color, bm in self.parts.items():
            bm.normal_update()
            mesh = bpy.data.meshes.new(f"{self.name}_{color}")
            bm.to_mesh(mesh)
            bm.free()
            for poly in mesh.polygons:
                poly.use_smooth = True
            obj = bpy.data.objects.new(mesh.name, mesh)
            collection.objects.link(obj)
            objs.append(obj)
        return objs


def surface_matrix(angle, y, radius, tilt=0.0, spin=0.0):
    """Матрица детали на боку корпуса: смотрит наружу под углом angle (рад), высота y, радиус radius."""
    out = Vector((math.cos(angle), 0, math.sin(angle)))
    pos = out * radius + Vector((0, y, 0))
    yaw = Matrix.Rotation(-angle + math.pi / 2, 4, "Z")  # локальная -Y Blender (лицо) → наружу
    return Matrix.Translation(bl(pos)) @ yaw @ Matrix.Rotation(math.radians(tilt), 4, "X") @ \
        Matrix.Rotation(math.radians(spin), 4, "Y")


def rounded_cube(sx, sy, sz, bevel, segments=3):
    def build(bm):
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(sx, sz, sy), verts=bm.verts)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=segments, affect="EDGES", clamp_overlap=True)
    return build


def disc(radius, depth, segments=28):
    def build(bm):
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius,
                              depth=depth, matrix=Matrix.Rotation(math.radians(90), 4, "X"))
        bmesh.ops.bevel(bm, geom=[e for e in bm.edges if not e.is_manifold or True], offset=depth * 0.35,
                        segments=2, affect="EDGES", clamp_overlap=True)
    return build


def cabochon(radius, height):
    def build(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=7, radius=radius)
        bmesh.ops.scale(bm, vec=(1, height / radius, 1), verts=bm.verts)
    return build


# ── Общий корпус: округлое тело, пята, горло, раструб; цвета задаёт вариант ──────────────────────────────
FOOT = [(0.0, 0.74), (0.03, 0.82), (0.1, 0.86), (0.2, 0.84), (0.26, 0.74), (0.3, 0.6), (0.36, 0.5), (0.46, 0.48)]
BODY = [(0.46, 0.48), (0.56, 0.74), (0.7, 0.98), (0.9, 1.15), (1.15, 1.24), (1.42, 1.23), (1.68, 1.13), (1.92, 0.94),
        (2.1, 0.72), (2.22, 0.55)]
NECK = [(2.22, 0.55), (2.32, 0.44), (2.6, 0.42), (2.7, 0.52), (2.8, 0.66), (2.92, 0.72), (3.0, 0.66), (3.03, 0.55),
        (3.03, 0.47)]
MOUTH = [(2.76, 0.36), (3.0, 0.42), (3.02, 0.47)]


def body_radius(y):
    for (y0, r0), (y1, r1) in zip(BODY, BODY[1:]):
        if y0 <= y <= y1:
            return r0 + (r1 - r0) * (y - y0) / (y1 - y0)
    return BODY[-1][1]


def band(p, color, y0, y1, lift=0.05):
    """Пояс поверх тела с мягко скруглёнными краями."""
    prof = [(y0 - 0.02, body_radius(y0 - 0.02) - 0.02), (y0, body_radius(y0) + lift * 0.6),
            (y0 + 0.03, body_radius(y0 + 0.03) + lift)]
    k = 3
    for i in range(1, k):
        y = y0 + 0.03 + (y1 - y0 - 0.06) * i / k
        prof.append((y, body_radius(y) + lift))
    prof += [(y1 - 0.03, body_radius(y1 - 0.03) + lift), (y1, body_radius(y1) + lift * 0.6),
             (y1 + 0.02, body_radius(y1 + 0.02) - 0.02)]
    p.lathe(color, prof)


def handles(p, color, rx=0.13, rz=0.17):
    for xs in (1, -1):
        p.handle(color, [(xs * 0.8, 1.76, 0), (xs * 1.42, 1.92, 0), (xs * 1.6, 2.2, 0), (xs * 1.5, 2.52, 0),
                         (xs * 1.1, 2.66, 0), (xs * 0.35, 2.58, 0)], rx, rz)


def base_vase(p, foot, body, neck, handle):
    p.lathe(foot, FOOT, cap_bottom=True)
    p.lathe(body, BODY)
    p.lathe(neck, NECK)
    p.lathe(INSIDE, MOUTH, outward=False, cap_bottom=True)
    handles(p, handle)


def vase_minimal(offset):
    p = Prop("Vase1", offset)
    base_vase(p, ORANGE, CREAM, ORANGE, ORANGE)
    band(p, ORANGE, 1.1, 1.42)
    return p


def vase_decorative(offset):
    p = Prop("Vase2", offset)
    base_vase(p, ORANGE, CREAM, ORANGE, ORANGE)
    band(p, ORANGE, 0.98, 1.56)
    # Крупный простой орнамент: кремовые ромбы по поясу (8 штук), тёмные полосы-канты.
    for i in range(8):
        a = 2 * math.pi * i / 8 + math.pi / 8
        r = body_radius(1.27) + 0.05
        p.piece(CREAM, rounded_cube(0.3, 0.3, 0.07, 0.05, segments=2), surface_matrix(a, 1.27, r + 0.02, spin=45))
    p.lathe(DEEP, [(0.95, body_radius(0.95) - 0.01), (0.965, body_radius(0.965) + 0.07), (0.99, body_radius(0.99) + 0.07),
                   (1.0, body_radius(1.0) - 0.01)])
    p.lathe(DEEP, [(1.54, body_radius(1.54) - 0.01), (1.55, body_radius(1.55) + 0.07), (1.575, body_radius(1.575) + 0.07),
                   (1.59, body_radius(1.59) - 0.01)])
    p.lathe(DEEP, [(2.86, 0.72), (2.88, 0.735), (2.93, 0.735), (2.95, 0.72)])  # кант на раструбе
    return p


def vase_premium(offset):
    p = Prop("Vase3", offset)
    base_vase(p, GOLD, CREAM, ORANGE, GOLD)
    p.lathe(GOLD, [(2.78, 0.66), (2.86, 0.74), (2.95, 0.74), (3.0, 0.68), (3.03, 0.58), (3.03, 0.5)])  # золотой венчик
    band(p, ORANGE, 1.0, 1.54)
    band(p, GOLD, 0.97, 1.03, lift=0.08)
    band(p, GOLD, 1.51, 1.57, lift=0.08)
    # Медальоны с камнями спереди и сзади; по бокам пояса — крупные золотые волны-ромбы.
    for a in (-math.pi / 2, math.pi / 2):
        r = body_radius(1.27) + 0.05
        p.piece(GOLD, disc(0.3, 0.09), surface_matrix(a, 1.27, r + 0.03))
        p.piece(GEM, cabochon(0.17, 0.09), surface_matrix(a, 1.27, r + 0.085))
        for side in (-1, 1):
            p.piece(GOLD, rounded_cube(0.2, 0.2, 0.06, 0.04, segments=2), surface_matrix(a + side * 0.42, 1.27, r + 0.02,
                                                                                          spin=45))
    return p


def mannequin(offset):
    """Блочный манекен Roblox R15 (≈ 5.2 стада): голова, торс, руки, ноги — скруглённые бруски."""
    p = Prop("Mannequin", offset)
    for center, size in (((0, 4.65, 0), (1.15, 1.15, 1.15)), ((0, 3.2, 0), (2.0, 1.75, 1.0)),
                         ((-1.5, 3.2, 0), (0.95, 1.75, 0.95)), ((1.5, 3.2, 0), (0.95, 1.75, 0.95)),
                         ((-0.5, 1.15, 0), (0.95, 2.3, 0.95)), ((0.5, 1.15, 0), (0.95, 2.3, 0.95))):
        p.piece(MANNEQUIN, rounded_cube(*size, 0.1, segments=4), Matrix.Translation(bl(center)))
    return p


for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
collection = bpy.data.collections.new("ArtV6")
bpy.context.scene.collection.children.link(collection)
# Камера смотрит в +z, поэтому +x на снимке слева: манекен, затем вазы 1, 2, 3 слева направо.
props = {"Vase1": vase_minimal((7.6, 0, 0)), "Vase2": vase_decorative((3.8, 0, 0)), "Vase3": vase_premium((0, 0, 0)),
         "Mannequin": mannequin((11.2, 0, 0.3))}
objects, report = {}, []
for name, p in props.items():
    objects[name] = p.build(collection)
    if name != "Mannequin":
        tris = 0
        for obj in objects[name]:
            obj.data.calc_loop_triangles()
            tris += len(obj.data.loop_triangles)
        report.append(f"{name}: {tris} тр.")
all_objs = [o for objs in objects.values() for o in objs]
bpy.ops.object.select_all(action="DESELECT")
for obj in all_objs:
    obj.select_set(True)
bpy.context.view_layer.objects.active = all_objs[0]
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(55))

for name in ("Vase1", "Vase2", "Vase3"):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects[name]:
        obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(REPO, "assets", "models", f"ArtV6_{name}.fbx"), use_selection=True,
                             apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                             mesh_smooth_type="FACE", path_mode="STRIP")

for obj in all_objs:
    code = obj.name.rsplit("_", 1)[1]
    mat = bpy.data.materials.get("M_" + code)
    if not mat:
        mat = bpy.data.materials.new("M_" + code)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*hex_rgb(code), 1)
        bsdf.inputs["Roughness"].default_value = 0.32 if code in (GOLD, GEM) else 0.45
        bsdf.inputs["Metallic"].default_value = 0.35 if code == GOLD else 0.0
    obj.data.materials.append(mat)

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
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.44, 0.47, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
scene.world = world
for name, loc, energy, size in (("Key", (-3, 9, -9), 1800, 7), ("Fill", (12, 5, -6), 700, 8), ("Rim", (3, 7, 8), 900, 6)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.size = energy, size
    light = bpy.data.objects.new(name, data)
    light.location = bl(loc)
    light.rotation_euler = (light.location - bl((2.5, 1.5, 0))).to_track_quat("Z", "Y").to_euler()
    scene.collection.objects.link(light)
floor = bpy.data.meshes.new("Floor")
floor.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
fm = bpy.data.materials.new("Floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.36, 0.38, 0.41, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
floor.materials.append(fm)
collection.objects.link(bpy.data.objects.new("Floor", floor))
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def shot(name, eye, target, lens, res):
    scene.render.resolution_x, scene.render.resolution_y = res
    cam_data.lens = lens
    cam.location = bl(eye)
    cam.rotation_euler = (cam.location - bl(target)).to_track_quat("Z", "Y").to_euler()
    scene.render.filepath = os.path.join(PREVIEWS, name + ".png")
    bpy.ops.render.render(write_still=True)


shot("lineup", (5.4, 4.2, -18), (5.4, 2.1, 0), 40, (1800, 900))
for name, x in (("Vase1", 7.6), ("Vase2", 3.8), ("Vase3", 0)):
    shot(name + "_34", (x - 3.6, 3.4, -5.6), (x, 1.5, 0), 45, (800, 900))
print("V6_OK " + "; ".join(report))

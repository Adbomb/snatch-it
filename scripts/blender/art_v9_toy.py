"""Концепты стиля предметов v9 (2026-10-31): игрушечный коллекционный Roblox-стиль — крупные мягкие формы, гладкие
поверхности с мягкими фасками, читаемый силуэт, чистые цвета с лёгким градиентом. Фирменный квадрат — только эмблема
(вариант 5). Пять концептов амфоры отличаются силуэтом, пропорциями, ручками, верхом и основанием:
  1 «Пузатик» — милый и компактный; 2 «Коллекционная» — высокая и стройная; 3 «Сокровище» — круглая на ножках-шариках,
  корона, камень и кольца; 4 «Эпическая» — крылья, крышка, светящийся кристалл; 5 «Гибрид» — пухлая, золото, эмблема.

Конвейер: детали (тело вращения со скруглёнными углами профиля, трубки-ручки и пластины из кривых с фаской, камни)
→ один меш → развёртка Smart UV → запекание в Cycles: цвет, окклюзия, шероховатость, металл → карты SurfaceAppearance.
Светящиеся детали — отдельный меш (в Roblox — Neon).

Пишет assets/models/ArtV9_Amphora<N>.fbx, assets/textures/art/v9_amphora<N>_{color,roughness,metalness}.png,
превью (ряд с подписями, ракурсы 3/4) и данные мешей для проверки в Studio.
Запуск: blender --background --factory-startup --python scripts/blender/art_v9_toy.py -- <репо> <превью>
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
SEG = 32  # граней по окружности у тел вращения
GRADIENT_TOP = 3.6  # высота, на которой цвет доходит до «верхнего»

# Цвет: (низ, верх) — лёгкий градиент снизу вверх. Поверхность: (шероховатость, металл).
PALETTE = {
    "coral": ("F04A63", "FF8C9A"), "coral_in": ("8E2232", "B23A4A"), "cream": ("F5DDBA", "FFF5E4"),
    "blue": ("1F40D8", "4C7BFF"), "blue_in": ("0F1F70", "1A2E9A"),
    "gold": ("E39E1E", "FFD65E"),
    "purple": ("6A28D8", "A56BFF"), "purple_in": ("33106E", "4A1C96"), "pink_gem": ("FF2A86", "FF7CC0"),
    "red": ("B81630", "F2465A"),
    "teal": ("0BA898", "47E2CE"), "teal_in": ("06524B", "0B7068"), "ruby": ("D8142E", "FF5466"),
}
SURFACE = {"gold": (0.28, 0.9), "pink_gem": (0.08, 0.0), "ruby": (0.08, 0.0), "cream": (0.42, 0.0)}
FLAT = {"pink_gem", "ruby"}  # гранёные камни — без сглаживания
GLOW = "5CF2FF"


def rgb(code):
    return [int(code[i : i + 2], 16) / 255 for i in (0, 2, 4)]


def lin(code):
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb(code)]


def to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


# ── Формы ───────────────────────────────────────────────────────────────────────────────────────────────
def rounded(points):
    """Профиль (r, z, фаска, материал отрезка) → гладкая ломаная [(r, z, материал)]. Фаска 9 — предельно мягко
    (угол скругляется до середин соседних отрезков, профиль становится плавной кривой)."""
    out = [(points[0][0], points[0][1], points[0][3])]
    for k in range(1, len(points) - 1):
        a, p, b = Vector(points[k - 1][:2]), Vector(points[k][:2]), Vector(points[k + 1][:2])
        d1, d2 = a - p, b - p
        t1, t2 = min(points[k][2], 0.5 * d1.length), min(points[k][2], 0.5 * d2.length)
        if points[k][2] <= 0 or t1 < 1e-4 or t2 < 1e-4:
            out.append((p.x, p.y, points[k][3]))
            continue
        q0, q2 = p + d1.normalized() * t1, p + d2.normalized() * t2
        steps = max(2, math.ceil((180 - math.degrees(d1.angle(d2))) / 18))
        for s in range(steps + 1):
            t = s / steps
            q = (1 - t) ** 2 * q0 + 2 * (1 - t) * t * p + t * t * q2
            out.append((q.x, q.y, points[k - 1][3] if t < 0.5 else points[k][3]))
    out.append((points[-1][0], points[-1][1], points[-1][3]))
    clean = [out[0]]
    for o in out[1:]:
        if math.hypot(o[0] - clean[-1][0], o[1] - clean[-1][1]) > 1e-4:
            clean.append(o)
    return clean


def radius_at(prof, z):
    """Радиус наружной стороны профиля на высоте z (первое пересечение снизу)."""
    for (r0, z0, _), (r1, z1, _) in zip(prof, prof[1:]):
        if z1 > z0 and z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    raise ValueError(z)


def torus(major, rr, rz=None, seg=28, sseg=8):
    rz = rz or rr
    bm = bmesh.new()
    rings = [[bm.verts.new(((major + rr * math.cos(b)) * math.cos(a), (major + rr * math.cos(b)) * math.sin(a),
                            rz * math.sin(b))) for b in (2 * math.pi * j / sseg for j in range(sseg))]
             for a in (2 * math.pi * i / seg for i in range(seg))]
    for i in range(seg):
        for j in range(sseg):
            bm.faces.new((rings[i][j], rings[(i + 1) % seg][j], rings[(i + 1) % seg][(j + 1) % sseg],
                          rings[i][(j + 1) % sseg]))
    return bm


def sphere(r):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r)
    return bm


def gem(radius, n=8, table=0.55, crown=0.32, pavilion=0.7):
    """Гранёный камень: площадка, корона, рундист, павильон. Ось — z (наружу)."""
    bm = bmesh.new()
    ang = [2 * math.pi * i / n for i in range(n)]
    top = [bm.verts.new((radius * table * math.cos(a), radius * table * math.sin(a), radius * crown)) for a in ang]
    gir = [bm.verts.new((radius * math.cos(a), radius * math.sin(a), 0)) for a in ang]
    cul = bm.verts.new((0, 0, -radius * pavilion))
    bm.faces.new(top)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((gir[i], gir[j], top[j], top[i]))
        bm.faces.new((gir[j], gir[i], cul))
    return bm


def crystal(radius, height, n=6):
    """Кристалл: шестигранная призма с остриями."""
    bm = bmesh.new()
    ang = [2 * math.pi * i / n for i in range(n)]
    lo = [bm.verts.new((radius * math.cos(a), radius * math.sin(a), 0.24 * height)) for a in ang]
    hi = [bm.verts.new((radius * math.cos(a), radius * math.sin(a), 0.7 * height)) for a in ang]
    bot, tip = bm.verts.new((0, 0, 0)), bm.verts.new((0, 0, height))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bm.faces.new((lo[j], lo[i], bot))
        bm.faces.new((hi[i], hi[j], tip))
    return bm


def curve_bm(cu):
    obj = bpy.data.objects.new("_curve", cu)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(me)
    bpy.data.curves.remove(cu)
    return bm


def tube(points, radius, scales, res=3):
    """Ручка: трубка по гладкой кривой, толщина по точкам (scales), торцы закрыты."""
    cu = bpy.data.curves.new("tube", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution, cu.use_fill_caps, cu.resolution_u = radius, res, True, 5
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p, s in zip(sp.bezier_points, points, scales):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        bp.radius = s
    return curve_bm(cu)


def plaque(outline, depth, bevel, poly=False):
    """Плоская деталь с мягкой фаской по контуру (крыло, эмблема) в плоскости XY."""
    cu = bpy.data.curves.new("plaque", "CURVE")
    cu.dimensions, cu.fill_mode = "2D", "BOTH"
    cu.extrude, cu.bevel_depth, cu.bevel_resolution, cu.resolution_u = depth, bevel, 3, 6
    if poly:
        sp = cu.splines.new("POLY")
        sp.points.add(len(outline) - 1)
        for pt, (x, y) in zip(sp.points, outline):
            pt.co = (x, y, 0, 1)
    else:
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(outline) - 1)
        for bp, (x, y) in zip(sp.bezier_points, outline):
            bp.co = (x, y, 0)
            bp.handle_left_type = bp.handle_right_type = "AUTO"
    sp.use_cyclic_u = True
    return curve_bm(cu)


def superellipse(half, n=4.0, count=40):
    pts = []
    for i in range(count):
        a = 2 * math.pi * i / count
        c, s = math.cos(a), math.sin(a)
        pts.append((half * math.copysign(abs(c) ** (2 / n), c), half * math.copysign(abs(s) ** (2 / n), s)))
    return pts


FRONT = Matrix.Rotation(math.radians(90), 4, "X")  # локальная z → вперёд (−y), локальная y → вверх (z)


class Model:
    """Собирает детали в один bmesh; у каждой грани — индекс материала по имени из PALETTE."""

    def __init__(self, name):
        self.name, self.bm, self.mats, self.glow = name, bmesh.new(), [], None

    def mat(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def add(self, part, mat, matrix=None, recalc=True):
        if matrix is not None:
            bmesh.ops.transform(part, matrix=matrix, verts=part.verts)
        if recalc:
            bmesh.ops.recalc_face_normals(part, faces=part.faces)
        if mat is not None:
            for f in part.faces:
                f.material_index = self.mat(mat)
        me = bpy.data.meshes.new("_part")
        part.to_mesh(me)
        part.free()
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    def lathe(self, points):
        prof = rounded(points)
        bm = bmesh.new()
        rings = []
        for r, z, _ in prof:
            if r < 1e-5:
                rings.append([bm.verts.new((0, 0, z))])
            else:
                rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / SEG), r * math.sin(2 * math.pi * i / SEG),
                                            z)) for i in range(SEG)])
        for k in range(len(rings) - 1):
            a, b = rings[k], rings[k + 1]
            idx = self.mat(prof[k][2])
            for i in range(SEG):
                j = (i + 1) % SEG
                if len(a) == 1:
                    f = bm.faces.new((a[0], b[i], b[j]))
                elif len(b) == 1:
                    f = bm.faces.new((a[i], a[j], b[0]))
                else:
                    f = bm.faces.new((a[i], a[j], b[j], b[i]))
                f.material_index = idx
        self.add(bm, None)
        return prof

    def band(self, prof, z, rr, rz, mat):
        self.add(torus(radius_at(prof, z), rr, rz), mat, Matrix.Translation((0, 0, z)))

    def handles(self, path, radius, scales, mat):
        for side in (1, -1):
            self.add(tube([(side * x, 0, z) for x, z in path], radius, scales), mat)

    def build(self, collection):
        mesh = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        obj = bpy.data.objects.new(self.name, mesh)
        collection.objects.link(obj)
        for name in self.mats:
            mesh.materials.append(MATS[name])
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
        for poly in mesh.polygons:
            if self.mats[poly.material_index] in FLAT:
                poly.use_smooth = False
        return obj


# ── Пять концептов (ось — z, перед — −y; размеры в стадах) ───────────────────────────────────────────────
def v1_chubby(m):
    """«Пузатик»: низкий круглый живот, короткое горлышко, толстый губастый венчик, маленькие ушки-ручки."""
    prof = m.lathe([(0, 0, 0, "cream"), (0.62, 0, 0.1, "cream"), (0.66, 0.18, 0.08, "cream"), (0.5, 0.26, 0.06, "coral"),
                    (1.32, 0.62, 9, "coral"), (1.4, 1.5, 9, "coral"), (0.6, 2.02, 9, "coral"), (0.52, 2.16, 0.08, "cream"),
                    (0.8, 2.3, 0.12, "cream"), (0.82, 2.48, 0.1, "cream"), (0.58, 2.5, 0.06, "coral_in"),
                    (0.46, 2.36, 0.1, "coral_in"), (0, 2.24, 0, None)])
    m.band(prof, 1.08, 0.06, 0.11, "cream")
    m.handles([(0.95, 1.7), (1.42, 1.8), (1.6, 2.06), (1.44, 2.3), (0.95, 2.28), (0.5, 2.14)], 0.14,
              [0.8, 1.0, 1.15, 1.1, 1.0, 0.8], "coral")


def v2_collector(m):
    """«Коллекционная»: высокая и стройная, ножка-стебель, раструб, длинные золотые ручки-завитки."""
    prof = m.lathe([(0, 0, 0, "gold"), (0.82, 0, 0.1, "gold"), (0.84, 0.16, 0.08, "gold"), (0.56, 0.26, 0.08, "gold"),
                    (0.4, 0.42, 0.1, "blue"), (0.38, 0.6, 9, "blue"), (1.12, 1.2, 9, "blue"), (1.12, 2.0, 9, "blue"),
                    (0.46, 2.6, 9, "blue"), (0.38, 2.86, 0.12, "blue"), (0.44, 3.05, 0.1, "blue"),
                    (0.82, 3.36, 0.1, "gold"), (0.84, 3.48, 0.08, "gold"), (0.66, 3.5, 0.05, "blue_in"),
                    (0.52, 3.34, 0.1, "blue_in"), (0, 3.2, 0, None)])
    m.band(prof, 1.6, 0.05, 0.09, "gold")
    m.add(torus(0.4, 0.075), "gold", Matrix.Translation((0, 0, 2.92)))
    m.handles([(0.9, 2.2), (1.42, 2.42), (1.62, 2.85), (1.42, 3.2), (0.9, 3.14), (0.42, 2.96)], 0.11,
              [0.8, 1.0, 1.1, 1.0, 0.9, 0.75], "gold")


def v3_treasure(m):
    """«Сокровище»: шар на четырёх ножках-шариках, корона из шариков, камень в оправе, кольца по бокам."""
    prof = m.lathe([(0, 0.22, 0, "purple"), (0.55, 0.22, 9, "purple"), (1.25, 0.75, 9, "purple"),
                    (1.28, 1.75, 9, "purple"), (0.62, 2.32, 9, "purple"), (0.5, 2.42, 0.08, "gold"),
                    (0.5, 2.52, 0.06, "gold"), (0.72, 2.6, 0.08, "gold"), (0.74, 2.82, 0.08, "gold"),
                    (0.6, 2.86, 0.05, "purple_in"), (0.5, 2.7, 0.1, "purple_in"), (0, 2.6, 0, None)])
    for k in range(4):
        a = math.radians(45 + 90 * k)
        m.add(sphere(0.22), "gold", Matrix.Translation((0.62 * math.cos(a), 0.62 * math.sin(a), 0.22)))
    for k in range(8):
        a = 2 * math.pi * k / 8
        m.add(sphere(0.12), "gold", Matrix.Translation((0.66 * math.cos(a), 0.66 * math.sin(a), 2.86)))
    r = radius_at(prof, 1.3)
    m.add(torus(0.37, 0.075), "gold", Matrix.Translation((0, -r + 0.02, 1.3)) @ FRONT)
    m.add(gem(0.34), "pink_gem", Matrix.Translation((0, -r - 0.05, 1.3)) @ FRONT)
    for side in (1, -1):
        m.add(sphere(0.13), "gold", Matrix.Translation((side * 1.22, 0, 1.74)))
        m.add(torus(0.3, 0.07), "gold", Matrix.Translation((side * 1.5, 0, 1.72)) @ FRONT)


def v4_epic(m):
    """«Эпическая»: перевёрнутая капля на тонкой ножке, крышка-купол, золотые крылья, светящийся кристалл."""
    m.lathe([(0, 0, 0, "gold"), (0.9, 0, 0.1, "gold"), (0.92, 0.2, 0.08, "gold"), (0.5, 0.32, 0.1, "gold"),
             (0.34, 0.5, 0.1, "red"), (0.6, 0.95, 9, "red"), (1.32, 1.9, 9, "red"), (1.12, 2.5, 9, "red"),
             (0.62, 2.62, 0.1, "gold"), (0.66, 2.78, 0.08, "gold"), (0.5, 2.84, 0.06, "red"), (0.42, 3.1, 9, "red"),
             (0.2, 3.3, 0.06, "gold"), (0.22, 3.4, 0.05, "gold"), (0, 3.42, 0, None)])
    wing = [(0.0, -0.05), (0.45, -0.32), (1.05, -0.28), (0.82, -0.02), (1.32, 0.12), (1.06, 0.36), (1.45, 0.58),
            (1.18, 0.86), (0.7, 0.92), (0.25, 0.62)]
    for side in (1, -1):
        outline = [(side * x * 0.85, y * 0.85) for x, y in wing]
        matrix = Matrix.Translation((side * 1.1, 0.05, 2.0)) @ Matrix.Rotation(math.radians(side * 22), 4, "Z") @ FRONT
        m.add(plaque(outline, 0.07, 0.06), "gold", matrix)
    m.glow = crystal(0.26, 1.05)
    bmesh.ops.translate(m.glow, vec=(0, 0, 3.36), verts=m.glow.verts)
    bmesh.ops.recalc_face_normals(m.glow, faces=m.glow.faces)


def v5_hybrid(m):
    """«Гибрид»: пухлый корпус, короткая ножка, золотые ручки-завитки и венчик, эмблема «квадрат в квадрате»."""
    prof = m.lathe([(0, 0, 0, "gold"), (0.72, 0, 0.1, "gold"), (0.74, 0.18, 0.08, "gold"), (0.5, 0.28, 0.08, "teal"),
                    (0.46, 0.4, 0.1, "teal"), (1.25, 0.85, 9, "teal"), (1.3, 1.75, 9, "teal"), (0.58, 2.3, 9, "teal"),
                    (0.46, 2.48, 0.1, "teal"), (0.5, 2.62, 0.08, "gold"), (0.74, 2.8, 0.1, "gold"),
                    (0.76, 2.96, 0.08, "gold"), (0.56, 2.98, 0.05, "teal_in"), (0.44, 2.82, 0.1, "teal_in"),
                    (0, 2.7, 0, None)])
    m.band(prof, 0.95, 0.05, 0.1, "cream")
    r = radius_at(prof, 1.55)
    m.add(plaque(superellipse(0.3), 0.05, 0.05, poly=True), "gold", Matrix.Translation((0, -r + 0.03, 1.55)) @ FRONT)
    m.add(gem(0.27, n=4, table=0.6, crown=0.3, pavilion=0.6), "ruby",
          Matrix.Translation((0, -r - 0.09, 1.55)) @ FRONT @ Matrix.Rotation(math.radians(45), 4, "Z"))
    m.handles([(0.95, 1.95), (1.45, 2.1), (1.62, 2.45), (1.45, 2.72), (1.0, 2.66), (0.48, 2.52)], 0.12,
              [0.8, 1.0, 1.12, 1.05, 0.95, 0.75], "gold")


VARIANTS = [
    (1, "Пузатик", v1_chubby, 0.0),
    (2, "Коллекционная", v2_collector, 3.8),
    (3, "Сокровище", v3_treasure, 7.6),
    (4, "Эпическая", v4_epic, 12.0),
    (5, "Гибрид", v5_hybrid, 16.4),
]


# ── Материалы и запекание ────────────────────────────────────────────────────────────────────────────────
def make_material(name):
    lo, hi = PALETTE[name]
    rough, metal = SURFACE.get(name, (0.36, 0.0))
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    coord, sep = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeSeparateXYZ")
    rng, mix = nt.nodes.new("ShaderNodeMapRange"), nt.nodes.new("ShaderNodeMixRGB")
    rng.name, mix.name = "Range", "Gradient"
    rng.inputs["From Min"].default_value, rng.inputs["From Max"].default_value = 0.0, GRADIENT_TOP
    mix.inputs["Color1"].default_value, mix.inputs["Color2"].default_value = (*lin(lo), 1), (*lin(hi), 1)
    nt.links.new(coord.outputs["Object"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], rng.inputs["Value"])
    nt.links.new(rng.outputs["Result"], mix.inputs["Fac"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value, bsdf.inputs["Metallic"].default_value = rough, metal
    target = nt.nodes.new("ShaderNodeTexImage")
    target.name = "BakeTarget"
    mat["rough"], mat["metal"] = rough, metal
    return mat


def emission_mode(mat, mode):
    """Для запекания EMIT: эмиссия = цвет (градиент) или константа шероховатости/металла."""
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    for link in list(nt.links):
        if link.to_socket == bsdf.inputs["Emission Color"]:
            nt.links.remove(link)
    if mode == "color":
        nt.links.new(nt.nodes["Gradient"].outputs["Color"], bsdf.inputs["Emission Color"])
    else:
        v = mat[mode]
        bsdf.inputs["Emission Color"].default_value = (v, v, v, 1)
    bsdf.inputs["Emission Strength"].default_value = 1.0


def bake(obj, kind):
    img = bpy.data.images.new(f"{obj.name}_{kind}", TEX, TEX, alpha=False, float_buffer=True)
    for slot in obj.material_slots:
        node = slot.material.node_tree.nodes["BakeTarget"]
        node.image = img
        slot.material.node_tree.nodes.active = node
        if kind != "ao":
            emission_mode(slot.material, kind)
    bpy.context.scene.cycles.samples = 64 if kind == "ao" else 1
    bpy.ops.object.bake(type="AO" if kind == "ao" else "EMIT")
    arr = np.empty(TEX * TEX * 4, np.float32)
    img.pixels.foreach_get(arr)
    return arr.reshape(TEX, TEX, 4)[::-1, :, :3]


def save(path, arr):
    img = bpy.data.images.new(os.path.basename(path), TEX, TEX, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    rgba = np.ones((TEX, TEX, 4), np.float32)
    rgba[..., :3] = arr
    img.pixels.foreach_set(rgba[::-1].ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()


# ── Сборка ───────────────────────────────────────────────────────────────────────────────────────────────
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
scene = bpy.context.scene
collection = bpy.data.collections.new("ArtV9")
scene.collection.children.link(collection)
MATS = {name: make_material(name) for name in PALETTE}
glow_mat = bpy.data.materials.new("Glow")
glow_mat.use_nodes = True
glow_bsdf = glow_mat.node_tree.nodes["Principled BSDF"]
glow_bsdf.inputs["Base Color"].default_value = (*lin(GLOW), 1)
glow_bsdf.inputs["Emission Color"].default_value = (*lin(GLOW), 1)
glow_bsdf.inputs["Emission Strength"].default_value = 4.0

objects, glows = {}, {}
for n, title, func, x in VARIANTS:
    m = Model(f"ArtV9_Amphora{n}")
    func(m)
    objects[n] = m.build(collection)
    if m.glow:
        gm = bpy.data.meshes.new(f"ArtV9_Amphora{n}_Glow")
        m.glow.to_mesh(gm)
        m.glow.free()
        glows[n] = bpy.data.objects.new(gm.name, gm)
        gm.materials.append(glow_mat)
        collection.objects.link(glows[n])

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.render.bake.margin = 12
scene.world = scene.world or bpy.data.worlds.new("Bake")
scene.world.light_settings.distance = 0.6
studio, report = [], []
for n, title, func, x in VARIANTS:
    obj = objects[n]
    others = [o for o in list(objects.values()) + list(glows.values()) if o is not obj]
    for o in others:
        o.location.z -= 500
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.006)
    bpy.ops.object.mode_set(mode="OBJECT")
    color, ao = bake(obj, "color"), bake(obj, "ao")
    rough, metal = bake(obj, "rough")[..., 0], bake(obj, "metal")[..., 0]
    for o in others:
        o.location.z += 500
    maps = {"color": to_srgb(color * (0.45 + 0.55 * ao[..., :1])), "roughness": np.repeat(rough[..., None], 3, -1)}
    if metal.max() > 0.01:
        maps["metalness"] = np.repeat(metal[..., None], 3, -1)
    final = bpy.data.materials.new(f"ArtV9_{n}")
    final.use_nodes = True
    final.use_backface_culling = True  # как в Roblox
    nt = final.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    for kind, arr in maps.items():
        path = os.path.join(TEXDIR, f"v9_amphora{n}_{kind}.png")
        save(path, arr)
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(path)
        node.image.colorspace_settings.name = "sRGB" if kind == "color" else "Non-Color"
        socket = {"color": "Base Color", "roughness": "Roughness", "metalness": "Metallic"}[kind]
        nt.links.new(node.outputs["Color"], bsdf.inputs[socket])
    obj.data.materials.clear()
    obj.data.materials.append(final)
    for poly in obj.data.polygons:
        poly.material_index = 0

    # FBX (начало — центр дна) и данные для Studio: оси Roblox (x, z, −y), нормали углов, uv.
    parts = [obj] + ([glows[n]] if n in glows else [])
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=os.path.join(REPO, "assets", "models", f"ArtV9_Amphora{n}.fbx"),
                             use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP")
    entry = {"model": n, "title": title, "maps": sorted(maps)}
    for key, o in (("main", obj), ("glow", glows.get(n))):
        if o is None:
            continue
        mesh = o.data
        mesh.calc_loop_triangles()
        uvl = mesh.uv_layers.active.data if mesh.uv_layers.active else None
        normals = mesh.corner_normals
        verts, index, tri = [], {}, []
        for lt in mesh.loop_triangles:
            ids = []
            for li in lt.loops:
                co = mesh.vertices[mesh.loops[li].vertex_index].co
                nr = normals[li].vector if mesh.polygons[lt.polygon_index].use_smooth else lt.normal
                uv = uvl[li].uv if uvl else (0, 0)
                k = (round(co.x, 4), round(co.y, 4), round(co.z, 4), round(nr.x, 3), round(nr.y, 3), round(nr.z, 3),
                     round(uv[0], 5), round(uv[1], 5))
                if k not in index:
                    index[k] = len(verts)
                    verts.append(k)
                ids.append(index[k])
            tri.append(ids)
        entry[key] = {"v": [[k[0], k[2], -k[1]] for k in verts], "n": [[k[3], k[5], -k[4]] for k in verts],
                      "uv": [[k[6], 1 - k[7]] for k in verts], "t": tri}
        report.append(f"{n}{'' if key == 'main' else ' свечение'}: {len(tri)} тр.")
    if n in glows:
        entry["glowColor"] = GLOW
    studio.append(entry)
with open(os.path.join(PREVIEWS, "studio_mesh.json"), "w", encoding="utf-8") as f:
    json.dump(studio, f)

# ── Превью: нейтральный фон, манекен Roblox (R15 ≈ 5.2) слева, подписи над предметами ───────────────────
for n, title, func, x in VARIANTS:
    objects[n].location.x = x
    if n in glows:
        glows[n].location.x = x
grey = bpy.data.materials.new("Mannequin")
grey.use_nodes = True
grey.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin("D3D8E0"), 1)
for center, size in (((0, 0, 4.65), (1.15, 1.15, 1.15)), ((0, 0, 3.2), (2.0, 1.0, 1.75)),
                     ((-1.5, 0, 3.2), (0.95, 0.95, 1.75)), ((1.5, 0, 3.2), (0.95, 0.95, 1.75)),
                     ((-0.5, 0, 1.15), (0.95, 0.95, 2.3)), ((0.5, 0, 1.15), (0.95, 0.95, 2.3))):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.05, segments=2, affect="EDGES")
    bmesh.ops.translate(bm, vec=Vector(center) + Vector((-4.2, 0.3, 0)), verts=bm.verts)
    me = bpy.data.meshes.new("Mannequin")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(grey)
    collection.objects.link(bpy.data.objects.new("Mannequin", me))
font = bpy.data.fonts.load("C:/Windows/Fonts/segoeuib.ttf")
ink = bpy.data.materials.new("Ink")
ink.use_nodes = True
ink.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin("2B2F38"), 1)
labels = []
for n, title, func, x in VARIANTS:
    cu = bpy.data.curves.new(f"Label{n}", "FONT")
    cu.body, cu.font, cu.size, cu.align_x = f"{n} · {title}", font, 0.42, "CENTER"
    label = bpy.data.objects.new(f"Label{n}", cu)
    label.location, label.rotation_euler = (x, 0, 4.85), (math.radians(90), 0, 0)
    cu.materials.append(ink)
    collection.objects.link(label)
    labels.append(label)

engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
try:
    scene.eevee.use_raytracing = True
except AttributeError:
    pass
world = bpy.data.worlds.new("Studio")
world.use_nodes = True
wn = world.node_tree
wbg = wn.nodes["Background"]
gen, wsep, wrng, wmix = (wn.nodes.new(t) for t in ("ShaderNodeTexCoord", "ShaderNodeSeparateXYZ", "ShaderNodeMapRange",
                                                     "ShaderNodeMixRGB"))
wrng.inputs["From Min"].default_value, wrng.inputs["From Max"].default_value = -0.1, 0.7
wmix.inputs["Color1"].default_value, wmix.inputs["Color2"].default_value = (0.32, 0.33, 0.35, 1), (0.95, 0.97, 1.0, 1)
wn.links.new(gen.outputs["Generated"], wsep.inputs["Vector"])
wn.links.new(wsep.outputs["Z"], wrng.inputs["Value"])
wn.links.new(wrng.outputs["Result"], wmix.inputs["Fac"])
wn.links.new(wmix.outputs["Color"], wbg.inputs["Color"])
wbg.inputs["Strength"].default_value = 0.8
cam_bg = wn.nodes.new("ShaderNodeBackground")
cam_bg.inputs["Color"].default_value = (0.6, 0.63, 0.68, 1)
path, wshader = wn.nodes.new("ShaderNodeLightPath"), wn.nodes.new("ShaderNodeMixShader")
wn.links.new(path.outputs["Is Camera Ray"], wshader.inputs["Fac"])
wn.links.new(wbg.outputs["Background"], wshader.inputs[1])
wn.links.new(cam_bg.outputs["Background"], wshader.inputs[2])
wn.links.new(wshader.outputs["Shader"], wn.nodes["World Output"].inputs["Surface"])
scene.world = world
CX = 6.1
lights = []
for name, loc, energy, size in (("Key", (CX - 9, -13, 12), 3800, 9), ("Fill", (CX + 12, -9, 5), 1600, 10),
                                ("Rim", (CX + 2, 10, 9), 2600, 8)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.size = energy, size
    light = bpy.data.objects.new(name, data)
    light.location = loc
    light.rotation_euler = (Vector(loc) - Vector((CX, 0, 1.6))).to_track_quat("Z", "Y").to_euler()
    scene.collection.objects.link(light)
floor = bpy.data.meshes.new("Floor")
sweep = [(-60.0, 0.0), (6.0, 0.0)] + [(6.0 + 9 * math.sin(math.pi / 2 * k / 12), 9 - 9 * math.cos(math.pi / 2 * k / 12))
                                     for k in range(1, 13)] + [(15.0, 40.0)]
fverts = [(x, y, z) for (y, z) in sweep for x in (-70.0, 70.0)]
floor.from_pydata(fverts, [], [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(sweep) - 1)])
for poly in floor.polygons:
    poly.use_smooth = True
fm = bpy.data.materials.new("Floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.4, 0.42, 0.47, 1)
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
    cam.location = eye
    cam.rotation_euler = (Vector(eye) - Vector(target)).to_track_quat("Z", "Y").to_euler()
    scene.render.filepath = os.path.join(PREVIEWS, name + ".png")
    bpy.ops.render.render(write_still=True)


shot("lineup", (CX, -26, 5.6), (CX, 0, 2.3), 34, (2200, 1100))
hideable = [o for o in collection.objects if o.name.startswith(("ArtV9", "Mannequin", "Label"))]
for n, title, func, x in VARIANTS:
    keep = {objects[n].name, glows[n].name if n in glows else ""}
    for o in hideable:
        o.hide_render = o.name not in keep
    shot(f"concept{n}_34", (x - 4.0, -6.4, 3.9), (x, 0, 1.75), 50, (1000, 1100))
for o in hideable:
    o.hide_render = False
print("V9_OK " + "; ".join(report))

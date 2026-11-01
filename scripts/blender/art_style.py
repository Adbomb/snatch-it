"""Общий стиль произведений искусства D39 (эталон — ваза v13, scripts/blender/art_v13_rings.py).

Инструменты, а не генератор: геометрию каждого произведения проектирует свой скрипт (art_boss<N>.py), отсюда берёт
блоки, призмы, пиксельные накладки, кольца D39, развёртку, запекание, экспорт и проверочные рендеры.

Стиль D39: блоки с острыми рёбрами (фаска BEVEL в один сегмент), яркие чистые цвета; на крупных деталях — отдельные
скруглённые квадраты-контуры (тонкое вдавленное кольцо, шаг RING["step"]) одного масштаба на всей модели: проекция по
осям объекта, квадраты обрезаются краями деталей. Мелкие детали-накладки — гладкие.
Модель — один меш; цвет, окклюзия и нормали запекаются в карты TEX × TEX для SurfaceAppearance; шероховатость общая
(константа 0.5, уже загружена: ROUGHNESS_ID). Подвижный персонаж (босс) — тот же меш с группами деталей (Art.group):
после запекания split_groups режет его на части с точками вращения для Motor6D (D18).

Координаты Blender: z вверх, лицевая сторона смотрит в -y, 1 единица = 1 стад, низ модели на z = 0.
Studio: (x, y, z) Blender → (x, z, -y) Roblox; экспорт FBX (-Z вперёд, Y вверх).
Зависит только от Blender (bpy, bmesh, numpy).
"""

import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

TEX = 1024
BEVEL = 0.012  # рёбра почти острые: тонкий блик на ребре
RING = {"step": 0.6, "size": 0.42, "rad": 0.1, "width": 0.03, "dark": 0.22}  # D39
AO_MIX = 0.72  # итоговый цвет = цвет × (AO_MIX + (1 − AO_MIX) × окклюзия)
ROUGHNESS_ID = "rbxassetid://120633114716941"  # константа 0.5 (загружена с вазой v12/v13)
EPS = 1e-4


# ── Цвет ─────────────────────────────────────────────────────────────────────────────────────────────────────


def rgb(code):
    return [int(code[i : i + 2], 16) / 255 for i in (0, 2, 4)]


def lin(code):
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb(code)]


def to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


# ── Материалы для запекания ──────────────────────────────────────────────────────────────────────────────────


def _math(nt, op, a, b=None):
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


def _flat_material(name, code):
    """Сплошной цвет; для запекания тот же цвет идёт в эмиссию."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*lin(code), 1)
    bsdf.inputs["Emission Color"].default_value = (*lin(code), 1)
    bsdf.inputs["Roughness"].default_value = 0.5
    nt.nodes.new("ShaderNodeTexImage").name = "BakeTarget"
    return mat


def _face_coords(nt):
    """(u, v, top) рисунка: на боковых гранях u — вдоль грани (по касательной), v — высота; сверху u, v = x, y."""
    p = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], p.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(nt.nodes.new("ShaderNodeNewGeometry").outputs["True Normal"], n.inputs["Vector"])
    px, py, pz = p.outputs["X"], p.outputs["Y"], p.outputs["Z"]
    nx, ny, nz = n.outputs["X"], n.outputs["Y"], n.outputs["Z"]
    top = _math(nt, "GREATER_THAN", _math(nt, "ABSOLUTE", nz), 0.7)
    flat = _math(nt, "MAXIMUM", _math(nt, "SQRT", _math(nt, "ADD", _math(nt, "MULTIPLY", nx, nx),
                                                          _math(nt, "MULTIPLY", ny, ny))), 0.01)
    along = _math(nt, "DIVIDE", _math(nt, "SUBTRACT", _math(nt, "MULTIPLY", py, nx), _math(nt, "MULTIPLY", px, ny)), flat)
    u = _math(nt, "ADD", along, _math(nt, "MULTIPLY", top, _math(nt, "SUBTRACT", px, along)))
    v = _math(nt, "ADD", pz, _math(nt, "MULTIPLY", top, _math(nt, "SUBTRACT", py, pz)))
    return u, v, top


def _ring_material(name, code, z0):
    """Сплошной цвет + отдельные скруглённые квадраты-контуры D39 одной сеткой на весь объект (ряд по центру z0)."""
    mat = _flat_material(name, code)
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    u, v, top = _face_coords(nt)
    step, inner = RING["step"], RING["size"] / 2 - RING["rad"]
    off_v = _math(nt, "SUBTRACT", step / 2, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", 1.0, top), z0))
    d2 = None
    for coord, off in ((u, step / 2), (v, off_v)):
        frac = _math(nt, "FRACT", _math(nt, "DIVIDE", _math(nt, "ADD", coord, off), step))
        q = _math(nt, "ABSOLUTE", _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", frac, 0.5), step))
        a = _math(nt, "MAXIMUM", _math(nt, "SUBTRACT", q, inner), 0.0)
        sq = _math(nt, "MULTIPLY", a, a)
        d2 = sq if d2 is None else _math(nt, "ADD", d2, sq)
    dist = _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", _math(nt, "SQRT", d2), RING["rad"]))
    groove = nt.nodes.new("ShaderNodeMapRange")
    groove.interpolation_type = "SMOOTHSTEP"
    nt.links.new(dist, groove.inputs["Value"])
    groove.inputs["From Min"].default_value, groove.inputs["From Max"].default_value = RING["width"] / 2, 0.0
    g = groove.outputs["Result"]
    shade = nt.nodes.new("ShaderNodeMixRGB")
    shade.blend_type = "MULTIPLY"
    shade.inputs["Fac"].default_value = 1.0
    shade.inputs["Color1"].default_value = (*lin(code), 1)
    nt.links.new(_math(nt, "SUBTRACT", 1.0, _math(nt, "MULTIPLY", g, RING["dark"])), shade.inputs["Color2"])
    nt.links.new(shade.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(shade.outputs["Color"], bsdf.inputs["Emission Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value, bump.inputs["Distance"].default_value = 0.8, 0.012
    nt.links.new(_math(nt, "SUBTRACT", 1.0, g), bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


# ── Геометрия ────────────────────────────────────────────────────────────────────────────────────────────────


class _Solid:
    """Выпуклое тело детали (до фаски) для проверки «грань спрятана внутри другой детали»."""

    def __init__(self, planes, matrix):
        self.planes = planes  # [(нормаль, d)] в локальных координатах: внутри, если n·p ≤ d
        self.inv = matrix.inverted()

    def contains(self, p):
        q = self.inv @ p
        return all(n.dot(q) <= d + EPS for n, d in self.planes)


def _convex_planes(bm):
    planes = []
    for f in bm.faces:
        n = f.normal.copy()
        planes.append((n, n.dot(f.verts[0].co)))
    return planes


def _bevel(bm, bevel):
    """Фаска на настоящих рёбрах (рёбра внутри плоской грани не трогает)."""
    if bevel > 0:
        edges = [e for e in bm.edges if not e.is_manifold or e.calc_face_angle(0.0) > 0.02]
        bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=1, affect="EDGES", profile=0.5, clamp_overlap=True)


AXES = {"z": Matrix.Identity(4), "y": Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))),
        "x": Matrix(((0, 0, 1, 0), (0, 1, 0, 0), (1, 0, 0, 0), (0, 0, 0, 1)))}


def octagon(x0, x1, y0, y1, cut):
    """Прямоугольник со срезанными углами (точки по часовой стрелке не важны — нормали пересчитываются)."""
    return [(x0 + cut, y0), (x1 - cut, y0), (x1, y0 + cut), (x1, y1 - cut), (x1 - cut, y1), (x0 + cut, y1),
            (x0, y1 - cut), (x0, y0 + cut)]


def _inset(pts, d):
    """Выпуклый многоугольник, сдвинутый внутрь на d (пересечение сдвинутых сторон)."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sign = 1 if area > 0 else -1  # против часовой — внутренняя нормаль слева от стороны
    lines = []
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        ex, ey = x1 - x0, y1 - y0
        length = math.hypot(ex, ey)
        nx, ny = -ey / length * sign, ex / length * sign
        lines.append(((x0 + nx * d, y0 + ny * d), (ex, ey)))
    out = []
    for i in range(n):
        (px, py), (ax, ay) = lines[i - 1]
        (qx, qy), (bx, by) = lines[i]
        den = ax * by - ay * bx
        t = ((qx - px) * by - (qy - py) * bx) / den
        out.append((px + ax * t, py + ay * t))
    return out


def greedy_rects(mask):
    """Прямоугольники, покрывающие маску [строка][столбец] (жадно: вправо, потом вниз) → (столбец, строка, ш, в)."""
    h, w = len(mask), len(mask[0])
    used = [[False] * w for _ in range(h)]
    rects = []
    for r in range(h):
        for c in range(w):
            if not mask[r][c] or used[r][c]:
                continue
            cw = 1
            while c + cw < w and mask[r][c + cw] and not used[r][c + cw]:
                cw += 1
            rh = 1
            while r + rh < h and all(mask[r + rh][c + k] and not used[r + rh][c + k] for k in range(cw)):
                rh += 1
            for rr in range(r, r + rh):
                for cc in range(c, c + cw):
                    used[rr][cc] = True
            rects.append((c, r, cw, rh))
    return rects


class Art:
    """Одно произведение: детали по цветам → один меш с материалами (для запекания)."""

    def __init__(self, name, ring_z0=0.0):
        self.name = name
        self.ring_z0 = ring_z0  # высота центра ряда квадратов D39
        self.colors = {}  # ключ → (hex, кольца?)
        self.parts = []  # (bmesh, ключ, тело, группа)
        self.group = None  # подвижная часть, к которой идут следующие детали (у предметов — одна, None)
        self.transform = None  # Matrix: сдвиг всех следующих деталей (поднять голову, не переписывая координаты)

    def paint(self, key, code, rings=False):
        self.colors[key] = (code, rings)

    def _add(self, bm, key, planes, matrix):
        """planes = None — деталь невыпуклая: она не прячет чужие грани и не проходит проверку нормалей."""
        if key not in self.colors:
            raise KeyError(f"{self.name}: нет цвета {key}")
        if self.transform is not None:
            matrix = self.transform @ (matrix if matrix is not None else Matrix.Identity(4))
        if matrix is not None:
            bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        solid = None if planes is None else _Solid(planes, matrix if matrix is not None else Matrix.Identity(4))
        self.parts.append((bm, key, solid, self.group))

    def extrude(self, key, pts, a0, a1, axis="y", bevel=0.0, matrix=None):
        """Любой простой (в том числе невыпуклый, ступенчатый) многоугольник, вытянутый по оси: цельная деталь
        без швов между ступенями (полозья, силуэты). Без фаски: во внутренних углах фаска выворачивает тонкие
        грани (полосы в карте нормалей)."""
        bm = bmesh.new()
        lo = [bm.verts.new((u, w, a0)) for u, w in pts]
        hi = [bm.verts.new((u, w, a1)) for u, w in pts]
        bm.faces.new(lo)
        bm.faces.new(hi)
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bmesh.ops.transform(bm, matrix=AXES[axis], verts=bm.verts)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        # невыпуклые торцы — на выпуклые куски: иначе триангуляция даёт иглы и полосы в запечённых картах
        bmesh.ops.connect_verts_concave(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
        _bevel(bm, bevel)
        self._add(bm, key, None, matrix)

    def frame(self, key, pts, inset, a0, a1, axis="y", bevel=BEVEL, matrix=None):
        """Рамка: выпуклый многоугольник pts без такого же, сдвинутого внутрь на inset; толщина по оси от a0 до a1."""
        inner = _inset(pts, inset)
        bm = bmesh.new()
        ol, oh = [bm.verts.new((u, w, a0)) for u, w in pts], [bm.verts.new((u, w, a1)) for u, w in pts]
        il, ih = [bm.verts.new((u, w, a0)) for u, w in inner], [bm.verts.new((u, w, a1)) for u, w in inner]
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            bm.faces.new((oh[i], oh[j], ih[j], ih[i]))
            bm.faces.new((ol[i], il[i], il[j], ol[j]))
            bm.faces.new((ol[i], ol[j], oh[j], oh[i]))
            bm.faces.new((il[i], ih[i], ih[j], il[j]))
        bmesh.ops.transform(bm, matrix=AXES[axis], verts=bm.verts)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        _bevel(bm, bevel)
        self._add(bm, key, None, matrix)

    def box(self, key, x0, x1, y0, y1, z0, z1, bevel=BEVEL, matrix=None):
        x0, x1, y0, y1, z0, z1 = min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
        bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        planes = _convex_planes(bm)
        _bevel(bm, min(bevel, (x1 - x0) / 3, (y1 - y0) / 3, (z1 - z0) / 3))
        self._add(bm, key, planes, matrix)

    def frustum(self, key, bottom, top, z0, z1, axis="z", bevel=BEVEL, matrix=None):
        """Усечённая пирамида: прямоугольник bottom = (x0, x1, y0, y1) на z0 и top на z1 (клыки, шипы, пирамиды).
        Верх нулевого размера — острая вершина."""
        bm = bmesh.new()
        lo = [bm.verts.new((x, y, z0)) for x, y in ((bottom[0], bottom[2]), (bottom[1], bottom[2]),
                                                     (bottom[1], bottom[3]), (bottom[0], bottom[3]))]
        bm.faces.new(lo)
        if top[1] - top[0] < 1e-6 and top[3] - top[2] < 1e-6:
            apex = bm.verts.new((top[0], top[2], z1))
            for i in range(4):
                bm.faces.new((lo[i], lo[(i + 1) % 4], apex))
        else:
            hi = [bm.verts.new((x, y, z1)) for x, y in ((top[0], top[2]), (top[1], top[2]), (top[1], top[3]),
                                                         (top[0], top[3]))]
            bm.faces.new(hi)
            for i in range(4):
                j = (i + 1) % 4
                bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bmesh.ops.transform(bm, matrix=AXES[axis], verts=bm.verts)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        planes = _convex_planes(bm)
        _bevel(bm, bevel)
        self._add(bm, key, planes, matrix)

    def prism(self, key, pts, a0, a1, axis="z", bevel=BEVEL, matrix=None):
        """Выпуклый многоугольник pts (в плоскости, поперечной оси axis), вытянутый по оси от a0 до a1."""
        bm = bmesh.new()
        lo = [bm.verts.new((u, w, a0)) for u, w in pts]
        hi = [bm.verts.new((u, w, a1)) for u, w in pts]
        bm.faces.new(lo)
        bm.faces.new(hi)
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bmesh.ops.transform(bm, matrix=AXES[axis], verts=bm.verts)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        planes = _convex_planes(bm)
        _bevel(bm, bevel)
        self._add(bm, key, planes, matrix)

    def pixels(self, rows, palette, cell, h0, z_top, plane, at, sides=(-1,), flip=False):
        """Пиксельная накладка: rows — строки символов сверху вниз, palette — символ → (ключ цвета, выступ).
        plane "xz": по горизонтали x (h0 — левый край), грань y = side·at; "yz": по горизонтали y, грань x = side·at.
        flip — столбцы идут в сторону уменьшения координаты. Накладки без фаски, утоплены в основу на 0.02."""
        for ch, (key, depth) in palette.items():
            mask = [[c == ch for c in row] for row in rows]
            for c, r, cw, rh in greedy_rects(mask):
                h_a = h0 + (-1 if flip else 1) * c * cell
                h_b = h_a + (-1 if flip else 1) * cw * cell
                z1, z0 = z_top - r * cell, z_top - (r + rh) * cell
                for s in sides:
                    d0, d1 = s * (at - 0.02), s * (at + depth)
                    if plane == "xz":
                        self.box(key, h_a, h_b, d0, d1, z0, z1, bevel=0)
                    else:
                        self.box(key, d0, d1, h_a, h_b, z0, z1, bevel=0)

    def build(self, collection):
        """Убирает грани, целиком спрятанные в других деталях, собирает один меш, проверяет совпадающие грани."""
        boxes = []
        for bm, _, _, _ in self.parts:
            co = [v.co for v in bm.verts]
            boxes.append((Vector([min(c[i] for c in co) for i in range(3)]),
                          Vector([max(c[i] for c in co) for i in range(3)])))
        # Нормали: детали выпуклые, поэтому вся деталь должна лежать позади каждой своей грани.
        flipped = degenerate = 0
        for bm, _, solid, _ in self.parts:
            for f in bm.faces:
                c = f.calc_center_median()
                if solid is not None and max(f.normal.dot(v.co - c) for v in bm.verts) > 1e-4:
                    flipped += 1
                if f.calc_area() < 1e-7:
                    degenerate += 1
        hidden = 0
        for i, (bm, _, _, group) in enumerate(self.parts):
            dead = []
            for f in bm.faces:
                pts = [v.co for v in f.verts]
                lo = Vector([min(p[k] for p in pts) for k in range(3)])
                hi = Vector([max(p[k] for p in pts) for k in range(3)])
                for j, (_, _, solid, other) in enumerate(self.parts):
                    # подвижные части прячут грани только внутри себя: в другой позе грань откроется
                    if j == i or solid is None or other != group or any(lo[k] > boxes[j][1][k] + EPS or hi[k] < boxes[j][0][k] - EPS for k in range(3)):
                        continue
                    if all(solid.contains(p) for p in pts):
                        dead.append(f)
                        break
            hidden += len(dead)
            bmesh.ops.delete(bm, geom=dead, context="FACES")
        keys = list(self.colors)
        mats = []
        for key in keys:
            code, rings = self.colors[key]
            mats.append(_ring_material(f"{self.name}_{key}", code, self.ring_z0) if rings
                        else _flat_material(f"{self.name}_{key}", code))
        whole = bmesh.new()
        owner = []  # номер детали у каждой грани итогового меша
        self.face_groups = []  # подвижная часть у каждой грани
        for i, (bm, key, _, group) in enumerate(self.parts):
            for f in bm.faces:
                f.material_index = keys.index(key)
            me = bpy.data.meshes.new("_part")
            bm.to_mesh(me)
            owner += [i] * len(me.polygons)
            self.face_groups += [group] * len(me.polygons)
            whole.from_mesh(me)
            bpy.data.meshes.remove(me)
            bm.free()
        mesh = bpy.data.meshes.new(self.name)
        whole.to_mesh(mesh)
        whole.free()
        for m in mats:
            mesh.materials.append(m)
        obj = bpy.data.objects.new(self.name, mesh)
        collection.objects.link(obj)
        mesh.calc_loop_triangles()
        self.stats = {"tris": len(mesh.loop_triangles), "parts": len(self.parts), "hidden_faces": hidden,
                      "flipped": flipped, "degenerate": degenerate, "coplanar": _coplanar_pairs(mesh, owner)}
        self.materials = mats
        return obj


def _coplanar_pairs(mesh, owner):
    """Пары видимых осевых граней разных деталей в одной плоскости, смотрящих в одну сторону и перекрывающихся
    (мерцание в игре). Должно быть 0."""
    groups = {}
    for poly in mesh.polygons:
        n = poly.normal
        axis = max(range(3), key=lambda k: abs(n[k]))
        if abs(n[axis]) < 0.999:
            continue
        co = [mesh.vertices[v].co for v in poly.vertices]
        key = (axis, n[axis] > 0, round(co[0][axis], 3))
        others = [k for k in range(3) if k != axis]
        rect = tuple((min(c[k] for c in co), max(c[k] for c in co)) for k in others)
        groups.setdefault(key, []).append((owner[poly.index], rect))
    pairs = []
    for (axis, positive, coord), items in groups.items():
        for a in range(len(items)):
            for b in range(a + 1, len(items)):
                (oa, ra), (ob, rb) = items[a], items[b]
                if oa != ob and all(min(ra[k][1], rb[k][1]) - max(ra[k][0], rb[k][0]) > 0.002 for k in range(2)):
                    pairs.append(f"{'+' if positive else '-'}{'xyz'[axis]}={coord} детали {oa}/{ob} {ra}")
    return pairs


# ── Развёртка, запекание, экспорт ────────────────────────────────────────────────────────────────────────────


def _select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def bake(obj, art, texdir, prefix):
    """Развёртка, запекание цвета (эмиссия), окклюзии и нормалей, итоговые карты и материал для превью и FBX.
    Пишет <prefix>_color.png и <prefix>_normal.png; возвращает статистику развёртки."""
    scene = bpy.context.scene
    others = [o for o in scene.objects if o is not obj and o.type == "MESH"]
    for o in others:
        o.hide_render = True
    _select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.0, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin_method="FRACTION", margin=0.004, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.bake.margin = 8
    scene.world = scene.world or bpy.data.worlds.new("Bake")
    scene.world.light_settings.distance = 0.5

    def run(kind):
        img = bpy.data.images.new(f"{prefix}_{kind}", TEX, TEX, alpha=False, float_buffer=True)
        for m in art.materials:
            target = m.node_tree.nodes["BakeTarget"]
            target.image = img
            m.node_tree.nodes.active = target
            bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            bsdf.inputs["Emission Strength"].default_value = 1.0 if kind == "color" else 0.0
        scene.cycles.samples = {"color": 4, "ao": 64, "normal": 8}[kind]
        if kind == "normal":
            bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
        else:
            bpy.ops.object.bake(type="EMIT" if kind == "color" else "AO")
        arr = np.empty(TEX * TEX * 4, np.float32)
        img.pixels.foreach_get(arr)
        return arr.reshape(TEX, TEX, 4)[::-1, :, :3]

    color, ao, normal = run("color"), run("ao"), run("normal")
    maps = {"color": to_srgb(color * (AO_MIX + (1 - AO_MIX) * ao[..., :1])), "normal": normal}
    paths = {}
    for kind, arr in maps.items():
        paths[kind] = os.path.join(texdir, f"{prefix}_{kind}.png")
        _save_png(paths[kind], arr)
    rough = os.path.join(texdir, "art_roughness.png")
    if not os.path.exists(rough):
        _save_png(rough, np.full((64, 64, 3), 0.5, np.float32))
    paths["roughness"] = rough

    final = bpy.data.materials.new(obj.name)
    final.use_nodes = True
    final.use_backface_culling = True  # как в Roblox: вывернутая грань сразу видна дырой
    nt = final.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    for kind, path in paths.items():
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path)
        t.image.colorspace_settings.name = "sRGB" if kind == "color" else "Non-Color"
        if kind == "normal":
            nmap = nt.nodes.new("ShaderNodeNormalMap")
            nt.links.new(t.outputs["Color"], nmap.inputs["Color"])
            nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        else:
            nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color" if kind == "color" else "Roughness"])
    obj.data.materials.clear()
    obj.data.materials.append(final)
    for poly in obj.data.polygons:
        poly.material_index = 0
    for o in others:
        o.hide_render = False

    # Доля текстуры под развёрткой и плотность текселей (на стад).
    me = obj.data
    me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    uv_area = surf = 0.0
    for lt in me.loop_triangles:
        a, b, c = (Vector(uv[i].uv) for i in lt.loops)
        uv_area += abs((b - a).cross(c - a)) / 2
        surf += lt.area
    return {"uv_fill": uv_area, "texels_per_stud": TEX * math.sqrt(uv_area / surf) if surf else 0}


def _save_png(path, arr):
    h, w = arr.shape[:2]
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = arr
    img.pixels.foreach_set(rgba[::-1].ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()


def split_groups(obj, art, pivots, collection):
    """Запечённый меш → отдельные объекты по группам art.face_groups; начало координат каждого — его точка вращения
    pivots[группа] (Vector в координатах модели). Материал общий. Исходный объект удаляется."""
    out = {}
    me = obj.data
    for group, pivot in pivots.items():
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        dead = [f for f in bm.faces if art.face_groups[f.index] != group]
        bmesh.ops.delete(bm, geom=dead, context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bmesh.ops.translate(bm, vec=-Vector(pivot), verts=bm.verts)
        part = bpy.data.meshes.new(f"{obj.name}_{group}")
        bm.to_mesh(part)
        bm.free()
        part.materials.append(me.materials[0])
        o = bpy.data.objects.new(f"{obj.name}_{group}", part)
        o.location = pivot
        collection.objects.link(o)
        out[group] = o
    missing = set(art.face_groups) - set(pivots)
    if missing:
        raise KeyError(f"{obj.name}: нет точек вращения для {missing}")
    bpy.data.objects.remove(obj)
    return out


def export_fbx(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP")


def studio_json(obj, path):
    """Меш в осях Roblox для предпросмотра в Studio (EditableMesh): вершины, нормали углов, UV."""
    me = obj.data
    me.calc_loop_triangles()
    uvl = me.uv_layers.active.data
    verts, index, tri = [], {}, []
    for lt in me.loop_triangles:
        ids = []
        for li in lt.loops:
            co = me.vertices[me.loops[li].vertex_index].co
            nr = me.corner_normals[li].vector
            u = uvl[li].uv
            k = (round(co.x, 4), round(co.y, 4), round(co.z, 4), round(nr.x, 3), round(nr.y, 3), round(nr.z, 3),
                 round(u[0], 5), round(u[1], 5))
            if k not in index:
                index[k] = len(verts)
                verts.append(k)
            ids.append(index[k])
        tri.append(ids)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"v": [[k[0], k[2], -k[1]] for k in verts], "n": [[k[3], k[5], -k[4]] for k in verts],
                   "uv": [[k[6], 1 - k[7]] for k in verts], "t": tri}, f)


# ── Проверочные рендеры ──────────────────────────────────────────────────────────────────────────────────────


class Preview:
    """Тёмная студия (как у эталона): пол-циклорама, три источника, камера; кадры PNG."""

    def __init__(self, collection):
        scene = bpy.context.scene
        self.scene = scene
        engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
        scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
        scene.view_settings.view_transform = "Standard"
        try:
            scene.eevee.use_raytracing = True
        except AttributeError:
            pass
        world = bpy.data.worlds.new("Studio")
        world.use_nodes = True
        bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
        bg.inputs["Color"].default_value = (0.75, 0.78, 0.85, 1)
        bg.inputs["Strength"].default_value = 0.55
        scene.world = world
        floor = bpy.data.meshes.new("Floor")
        sweep = [(-80.0, 0.0), (6.0, 0.0)] + [(6.0 + 9 * math.sin(math.pi / 2 * k / 12),
                                                9 - 9 * math.cos(math.pi / 2 * k / 12)) for k in range(1, 13)]
        sweep.append((15.0, 50.0))
        floor.from_pydata([(x, y, z) for (y, z) in sweep for x in (-80.0, 80.0)], [],
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
        self.lights = []
        for name, loc, energy, size in (("Key", (-5, -9, 9), 1900, 7), ("Fill", (7, -6, 4), 900, 8),
                                        ("Rim", (2, 8, 7), 1600, 6)):
            data = bpy.data.lights.new(name, "AREA")
            data.energy, data.size = energy, size
            light = bpy.data.objects.new(name, data)
            light.location = loc
            light.rotation_euler = (Vector(loc) - Vector((0, 0, 1.5))).to_track_quat("Z", "Y").to_euler()
            scene.collection.objects.link(light)
            self.lights.append((light, Vector(loc)))
        self.cam_data = bpy.data.cameras.new("Cam")
        self.cam = bpy.data.objects.new("Cam", self.cam_data)
        scene.collection.objects.link(self.cam)
        scene.camera = self.cam

    def aim_lights(self, center):
        """Свет следует за группой (для общего кадра со смещённым центром)."""
        for light, loc in self.lights:
            light.location = loc + Vector((center.x, 0, 0))
            light.rotation_euler = (light.location - Vector((center.x, 0, 1.5))).to_track_quat("Z", "Y").to_euler()

    def shot(self, path, eye, target, lens, res):
        self.scene.render.resolution_x, self.scene.render.resolution_y = res
        self.cam_data.lens = lens
        self.cam.location = eye
        self.cam.rotation_euler = (Vector(eye) - Vector(target)).to_track_quat("Z", "Y").to_euler()
        self.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        return path


def bounds(obj):
    co = [obj.matrix_world @ v.co for v in obj.data.vertices]
    lo = Vector([min(c[i] for c in co) for i in range(3)])
    hi = Vector([max(c[i] for c in co) for i in range(3)])
    return lo, hi


def render_item(prev, obj, out_dir):
    """Повороты (спереди, 3/4, сбоку, сзади) одной полосой и крупный кадр 3/4; остальные модели скрыты."""
    hidden = [o for o in bpy.context.scene.objects if o.type == "MESH" and o is not obj and o.name != "Floor"]
    for o in hidden:
        o.hide_render = True
    lo, hi = bounds(obj)
    size = max(hi - lo)
    cz = (lo.z + hi.z) / 2
    dist = 2.7 * size + 1.0
    tiles = []
    for label, angle in (("front", 0), ("34", -40), ("side", -90), ("back", 180)):
        obj.rotation_euler = (0, 0, math.radians(angle))
        path = os.path.join(out_dir, f"{obj.name}_turn_{label}.png")
        tiles.append(prev.shot(path, (0, -dist, cz + 0.28 * size), (0, 0, cz), 75, (700, 900)))
    obj.rotation_euler = (0, 0, 0)
    hero = prev.shot(os.path.join(out_dir, f"{obj.name}_hero.png"),
                     (-0.62 * dist, -0.85 * dist, cz + 0.55 * size), (0, 0, cz - 0.05 * size), 75, (1100, 1100))
    strip(tiles, os.path.join(out_dir, f"{obj.name}_turns.png"))
    for o in hidden:
        o.hide_render = False
    return hero


def strip(paths, out_path, gap=0):
    tiles = []
    for p in paths:
        im = bpy.data.images.load(p)
        w, h = im.size
        px = np.empty(w * h * 4, np.float32)
        im.pixels.foreach_get(px)
        tiles.append(px.reshape(h, w, 4))
        if gap:
            tiles.append(np.ones((h, gap, 4), np.float32))
    if gap:
        tiles = tiles[:-1]
    row = np.concatenate(tiles, axis=1)
    out = bpy.data.images.new("strip", row.shape[1], row.shape[0], alpha=False)
    out.colorspace_settings.name = "Non-Color"
    out.pixels.foreach_set(row.ravel())
    out.filepath_raw = out_path
    out.file_format = "PNG"
    out.save()
    return out_path


def mannequin(collection, x, y=0.2):
    """Блочный манекен Roblox (рост ≈ 5.2 стада) для сравнения масштаба."""
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
        bmesh.ops.translate(bm, vec=Vector(center) + Vector((x, y, 0)), verts=bm.verts)
        me = bpy.data.meshes.new("Mannequin")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(grey)
        collection.objects.link(bpy.data.objects.new("Mannequin", me))

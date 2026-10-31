"""Амфора v8 — качество как у моделей на скриншотах владельца: гранёная низкополигональная форма (12 граней, чёткие
фаски) + своя развёртка и нарисованная текстура цвета и рельефа: тень снизу и в стыках, тонкие тёмные контуры
швов, вдавленные квадраты по граням (редко, стенки сверху-слева в тени), меандр на поясе плеч, лучи внизу тела,
запечённая окклюзия (Cycles). Один меш — один набор карт (в Roblox: MeshPart + SurfaceAppearance: ColorMap,
NormalMap, RoughnessMap, у золота MetalnessMap). Варианты: 1 минимализм, 2 декоративная, 3 премиум.

Пишет assets/models/ArtV8_Amphora<N>.fbx, assets/textures/art/amphora<N>_{color,normal,roughness,metalness}.png,
превью и данные мешей (с UV) для проверки в Studio.
Запуск: blender --background --factory-startup --python scripts/blender/art_v8_amphora.py -- <репо> <превью>
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

SEG = 12  # граней по окружности
TEX = 1024
VB = 0.74  # доля развёртки под корпус (снизу), выше — устье, ручки, камень
V_MOUTH = (0.745, 0.775)
V_HANDLE = (0.79, 0.975)
V_GEM = (0.982, 0.998)

# Профиль снаружи (высота, радиус) снизу вверх; фаски — короткие наклонные участки.
PROFILE = [
    (0.00, 0.84), (0.05, 0.92), (0.20, 0.92), (0.26, 0.84), (0.27, 0.62), (0.32, 0.55), (0.48, 0.46), (0.54, 0.6),
    (0.60, 0.62), (0.66, 0.74), (0.92, 1.08), (1.22, 1.28), (1.52, 1.34), (1.58, 1.36), (1.98, 1.36), (2.04, 1.3),
    (2.26, 0.98), (2.42, 0.62), (2.48, 0.5), (2.84, 0.45), (2.88, 0.56), (2.98, 0.56), (3.02, 0.62), (3.12, 0.78),
    (3.18, 0.78), (3.22, 0.7), (3.22, 0.6),
]
MOUTH = [(3.22, 0.6), (3.18, 0.5), (2.92, 0.42)]
H = 3.22

PALETTES = {
    1: {"foot": "EE8A22", "body": "F4DDB2", "band": "EE8A22", "neck": "EE8A22", "collar": "EE8A22", "lip": "EE8A22",
        "handle": "EE8A22", "key": None, "rays": None},
    2: {"foot": "E57D1E", "body": "F4DDB2", "band": "EE8A22", "neck": "EE8A22", "collar": "F4DDB2", "lip": "EE8A22",
        "handle": "EE8A22", "key": "8E3A12", "rays": "EE8A22"},
    3: {"foot": "E8B437", "body": "F6E6C4", "band": "E8B437", "neck": "D9701C", "collar": "E8B437", "lip": "E8B437",
        "handle": "E8B437", "key": "9A4A10", "rays": "D9701C"},
}
LINE = 0.55  # тёмный контур шва: доля яркости
INSIDE = "4A2410"
GEM = "2F7BF0"


def bl(p):
    return Vector((p[0], -p[2], p[1]))


def rgb(code):
    return np.array([int(code[i : i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)


def lin(c):
    return tuple(float(x) ** 2.2 for x in c)


# ── Геометрия с развёрткой ─────────────────────────────────────────────────────────────────────────────
def arc_lengths(profile):
    s = [0.0]
    for (y0, r0), (y1, r1) in zip(profile, profile[1:]):
        s.append(s[-1] + math.hypot(y1 - y0, r1 - r0))
    return s


S_BODY = arc_lengths(PROFILE)
L_BODY = S_BODY[-1]


def lathe_uv(bm, uv, profile, vrange, offset, inward=False):
    """Тело вращения с развёрткой: u — по окружности (шов на u = 1), v — по длине профиля в vrange."""
    s = arc_lengths(profile)
    total = s[-1]
    rings = []
    for (y, r) in profile:
        rings.append([bm.verts.new(bl(offset + Vector((r * math.cos(2 * math.pi * i / SEG), y,
                                                       r * math.sin(2 * math.pi * i / SEG))))) for i in range(SEG)])
    for k in range(len(profile) - 1):
        v0 = vrange[0] + (vrange[1] - vrange[0]) * s[k] / total
        v1 = vrange[0] + (vrange[1] - vrange[0]) * s[k + 1] / total
        for i in range(SEG):
            j = (i + 1) % SEG
            quad = [rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]]
            uvs = [(i / SEG, v0), ((i + 1) / SEG, v0), ((i + 1) / SEG, v1), (i / SEG, v1)]
            if rings[k][i].co == rings[k][j].co:  # вырожденный (радиус 0) — пропуск
                continue
            # обход quad даёт нормаль к оси: наружная поверхность — обратный порядок, устье — прямой
            f = bm.faces.new(quad if inward else list(reversed(quad)))
            for loop, t in zip(f.loops, uvs if inward else list(reversed(uvs))):
                loop[uv].uv = t
    return rings


def cap(bm, uv, ring, up, uvpoint):
    f = bm.faces.new(ring)
    f.normal_update()
    if (f.normal.z > 0) != up:
        bmesh.ops.reverse_faces(bm, faces=[f])
    for loop in f.loops:
        loop[uv].uv = uvpoint


def handle_uv(bm, uv, path, rx, rz, offset, steps=3, seg=8):
    """Ручка: протяжка восьмиугольника по кривой; u — вдоль ручки, v — вокруг сечения (полоса V_HANDLE)."""
    def cr(p0, p1, p2, p3, t):
        return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                      + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)

    pts = [Vector(p) for p in path]
    ext = [pts[0] + (pts[0] - pts[1])] + pts + [pts[-1] + (pts[-1] - pts[-2])]
    curve = [cr(ext[s - 1], ext[s], ext[s + 1], ext[s + 2], k / steps)
             for s in range(1, len(ext) - 2) for k in range(steps)] + [pts[-1]]
    rings = []
    for i, c in enumerate(curve):
        t = (curve[min(i + 1, len(curve) - 1)] - curve[max(i - 1, 0)]).normalized()
        b = Vector((0, 0, 1))
        n = b.cross(t).normalized()
        rings.append([bm.verts.new(bl(offset + c + n * (rx * math.cos(2 * math.pi * k / seg) * 1.0)
                                      + b * (rz * math.sin(2 * math.pi * k / seg)))) for k in range(seg)])
    m = len(curve) - 1
    for a in range(m):
        center = bl(offset + curve[a])
        for k in range(seg):
            q = (k + 1) % seg
            f = bm.faces.new((rings[a][k], rings[a][q], rings[a + 1][q], rings[a + 1][k]))
            f.normal_update()
            uvs = [(a / m, k / seg), (a / m, (k + 1) / seg), ((a + 1) / m, (k + 1) / seg), ((a + 1) / m, k / seg)]
            if f.normal.dot(f.calc_center_median() - center) < 0:
                bmesh.ops.reverse_faces(bm, faces=[f])
            for loop in f.loops:
                # восстановить uv по вершине (после возможного разворота)
                idx = [rings[a][k], rings[a][q], rings[a + 1][q], rings[a + 1][k]].index(loop.vert)
                u0, v0 = uvs[idx]
                loop[uv].uv = (u0, V_HANDLE[0] + (V_HANDLE[1] - V_HANDLE[0]) * v0)


def radius_at(y):
    for (y0, r0), (y1, r1) in zip(PROFILE, PROFILE[1:]):
        if y0 <= y <= y1 and y1 > y0:
            return r0 + (r1 - r0) * (y - y0) / (y1 - y0)
    return 1.0


def gem_uv(bm, uv, center, normal, radius, height, offset):
    """Камень-кабошон: развёрнут целиком в маленький квадрат V_GEM (синий с бликом)."""
    nrm = Vector(normal).normalized()
    side = nrm.cross(Vector((0, 1, 0))).normalized()
    up = side.cross(nrm).normalized()
    rings = []
    for k, (rr, hh) in enumerate(((radius, 0), (radius * 0.86, height * 0.6), (radius * 0.45, height))):
        rings.append([bm.verts.new(bl(offset + Vector(center) + nrm * hh
                                      + (side * math.cos(2 * math.pi * i / 8) + up * math.sin(2 * math.pi * i / 8)) * rr))
                      for i in range(8)])
    faces = []
    for a, b in zip(rings, rings[1:]):
        for i in range(8):
            j = (i + 1) % 8
            faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    faces.append(bm.faces.new(rings[-1]))
    for f in faces:
        f.normal_update()
        if f.normal.dot(f.calc_center_median() - bl(offset + Vector(center))) < 0:
            bmesh.ops.reverse_faces(bm, faces=[f])
        for loop in f.loops:
            c = (loop.vert.co - bl(offset + Vector(center)))
            du, dv = c.dot(bl(side)) / radius, c.dot(bl(up)) / radius
            loop[uv].uv = (0.5 + 0.007 * du, (V_GEM[0] + V_GEM[1]) / 2 + 0.007 * dv)


def build_amphora(name, variant, offset, collection):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    off = Vector(offset)
    lathe_uv(bm, uv, PROFILE, (0.0, VB), off)
    rings = lathe_uv(bm, uv, MOUTH, V_MOUTH, off, inward=True)
    bottom = [bm.verts.new(bl(off + Vector((PROFILE[0][1] * math.cos(2 * math.pi * i / SEG), 0,
                                            PROFILE[0][1] * math.sin(2 * math.pi * i / SEG))))) for i in range(SEG)]
    cap(bm, uv, bottom, False, (0.5, V_MOUTH[0] + 0.004))
    cap(bm, uv, rings[-1], True, (0.5, V_MOUTH[0] + 0.004))
    for xs in (1, -1):
        handle_uv(bm, uv, [(xs * 1.05, 1.95, 0), (xs * 1.58, 2.12, 0), (xs * 1.72, 2.55, 0), (xs * 1.5, 2.95, 0),
                           (xs * 0.98, 3.04, 0), (xs * 0.5, 2.94, 0)], 0.15, 0.2, off)
    if variant == 3:
        for zs in (-1, 1):
            r = radius_at(1.78)
            gem_uv(bm, uv, (0, 1.78, zs * (r - 0.02)), (0, 0, zs), 0.2, 0.13, off)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = False  # гранёный вид
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


# ── Текстура: цвет и рельеф ───────────────────────────────────────────────────────────────────────────
def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


GOLD = "E8B437"
WALL_DARK = np.array([0.66, 0.57, 0.5], np.float32)  # стенка квадрата в тени — тёплый тон основы
HALF, WALL, PITCH = 0.17, 0.06, 0.5  # полуразмер квадрата, ширина стенки, шаг рядов (стады по поверхности)
# Пояса с квадратами (по высоте) — ряды центрируются в поясе, квадрат не режется швом цвета.
SQUARES = {1: [(0.7, 1.56), (1.58, 1.98), (2.0, 2.42)], 2: [(1.1, 1.56), (2.0, 2.42)], 3: [(1.1, 1.56), (2.0, 2.42)]}
Y_OF = [p[0] for p in PROFILE[:-1]]


def s_of_y(y):
    return float(np.interp(y, Y_OF, S_BODY[:-1]))


def hash01(a):
    return (np.sin(a * 12.9898 + 78.233) * 43758.5453) % 1.0


def paint(variant, ao):
    """Цвет, рельеф, шероховатость и металл по развёртке; ao — запечённая тень (0..1, сверху вниз)."""
    pal = {k: (rgb(v) if v else None) for k, v in PALETTES[variant].items()}
    yy, xx = np.mgrid[0:TEX, 0:TEX].astype(np.float32) + 0.5
    u = xx / TEX
    v = 1 - yy / TEX
    color = np.zeros((TEX, TEX, 3), np.float32)
    height = np.zeros((TEX, TEX), np.float32)
    rough = np.full((TEX, TEX), 0.55, np.float32)
    metal = np.zeros((TEX, TEX), np.float32)
    gold = np.zeros((TEX, TEX), bool)

    # Корпус: v → длина профиля → высота и радиус.
    body = v < VB
    s = np.clip(v / VB, 0, 1) * L_BODY
    ys = np.interp(s, S_BODY, [p[0] for p in PROFILE]).astype(np.float32)
    rs = np.interp(s, S_BODY, [p[1] for p in PROFILE]).astype(np.float32)
    fidx = np.clip(np.floor(u * SEG), 0, SEG - 1)
    facet = u * SEG - fidx  # положение внутри грани 0..1
    fw = 2 * rs * math.sin(math.pi / SEG)  # ширина грани в стадах

    def region(y0, y1):
        return (ys >= y0) & (ys < y1)

    c = np.zeros_like(color)
    c[:] = pal["body"]
    for key, (y0, y1) in (("foot", (0, 0.6)), ("band", (1.58, 1.98)), ("neck", (2.42, 2.88)),
                          ("collar", (2.88, 2.98)), ("lip", (2.98, H + 0.01))):
        c[region(y0, y1)] = pal[key]
        if PALETTES[variant][key] == GOLD:
            gold |= body & region(y0, y1)
    # Лучи внизу тела: треугольники от пояса ножки вверх, один на грань.
    if pal["rays"] is not None:
        t = (ys - 0.66) / (1.08 - 0.66)
        ray = region(0.66, 1.08) & (np.abs(facet - 0.5) < 0.5 * (1 - t))
        c[ray] = pal["rays"]
        edge = region(0.66, 1.08) & (np.abs(np.abs(facet - 0.5) - 0.5 * (1 - t)) < 0.018)
        c[edge] *= LINE
        height[ray] += 0.35
    # Меандр на поясе плеч: один «ключ» на грань (рисунок 6 × 5 клеток), чуть выпуклый.
    if pal["key"] is not None:
        glyph = np.array([[1, 1, 1, 1, 1, 0],
                          [1, 0, 0, 0, 1, 0],
                          [1, 0, 1, 0, 1, 0],
                          [1, 0, 1, 1, 1, 0],
                          [1, 0, 0, 0, 0, 0]], np.int32)
        band = region(1.62, 1.94)
        gy = ((1 - (ys - 1.62) / (1.94 - 1.62)) * 5).astype(np.int32).clip(0, 4)
        gx = (facet * 6).astype(np.int32).clip(0, 5)
        on = band & (glyph[gy, gx] == 1)
        line_y = band & (((ys - 1.62) < 0.035) | ((1.94 - ys) < 0.035))
        c[on | line_y] = pal["key"]
        gold &= ~(on | line_y)
        height[on | line_y] += 0.6
    color[body] = c[body]

    # Вдавленные квадраты: редко и неровно (не на каждой грани), стенки сверху-слева в тени, снизу-справа светлее.
    for ri, (y0, y1) in enumerate(SQUARES[variant]):
        sa, sb = s_of_y(y0), s_of_y(y1)
        length = sb - sa
        n = max(1, int((length - 2 * HALF - 0.08) / PITCH) + 1)
        first = sa + (length - (n - 1) * PITCH) / 2
        row = np.clip(np.round((s - first) / PITCH), 0, n - 1)
        keep = body & (s >= sa) & (s < sb) & (hash01(fidx * 7.0 + row * 13.0 + ri * 31.0 + variant * 3.0) < 0.72)
        hx = np.minimum(HALF, 0.36 * fw)
        room = np.maximum(0.5 * fw - hx - 0.04, 0)
        dx = (facet - 0.5) * fw - (hash01(fidx * 5.0 + row * 11.0 + ri * 17.0) - 0.5) * 1.2 * room
        dy = s - (first + row * PITCH)
        rad = 0.04
        qx = np.abs(dx) - (hx - rad)
        qy = np.abs(dy) - (HALF - rad)
        sd = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rad
        aa = smooth(0.006, -0.006, sd) * keep
        height -= np.clip(-sd / WALL, 0, 1) * keep
        top_left = ((qy >= qx) & (dy > 0)) | ((qx > qy) & (dx > 0))  # u растёт вправо-налево
        wall_col = np.where(top_left[..., None], color * WALL_DARK, np.minimum(color * 1.12 + 0.05, 1))
        rec = np.where((sd > -WALL)[..., None], wall_col, color * 0.85)
        color = color * (1 - aa[..., None]) + rec * aa[..., None]

    # Тёмные контуры на стыках цветов.
    for b in (0.6, 1.58, 1.98, 2.42, 2.88, 2.98):
        color[body & (np.abs(ys - b) < 0.012)] *= LINE + 0.15
    # Свет сверху: книзу темнее, в вогнутых стыках профиля мягкая тень.
    shade = 0.82 + 0.22 * smooth(0.0, 2.4, ys)
    for (yc, depth) in ((0.27, 0.45), (0.6, 0.3), (2.42, 0.4), (2.88, 0.25), (2.98, 0.2)):
        shade *= 1 - depth * np.exp(-((ys - yc) / 0.07) ** 2)
    color[body] *= shade[body, None]

    # Устье — тёмное.
    mouth = (v >= V_MOUTH[0]) & (v < V_MOUTH[1] + 0.004)
    color[mouth] = rgb(INSIDE) * 0.9
    rough[mouth] = 0.85
    # Ручки: цвет ручки, к концам темнее, тонкие тёмные рёбра граней сечения.
    hnd = (v >= V_HANDLE[0]) & (v <= V_HANDLE[1])
    hv = (v - V_HANDLE[0]) / (V_HANDLE[1] - V_HANDLE[0]) * 8 % 1.0
    hcol = np.broadcast_to(pal["handle"], color.shape).copy()
    hcol *= (0.82 + 0.22 * np.sin(np.pi * np.clip(u, 0, 1)))[..., None]
    hcol[(hv < 0.05) | (hv > 0.95)] *= 0.8
    color[hnd] = hcol[hnd]
    if PALETTES[variant]["handle"] == GOLD:
        gold |= hnd
    # Камень: синий, светлее к центру, блик.
    gem = v > V_GEM[0] - 0.004
    du, dv = (u - 0.5) / 0.007, (v - (V_GEM[0] + V_GEM[1]) / 2) / 0.007
    rr = np.hypot(du, dv)
    gcol = rgb(GEM)[None, None, :] * (1.15 - 0.45 * np.clip(rr, 0, 1))[..., None]
    gcol[np.hypot(du + 0.35, dv - 0.35) < 0.22] = 1.0
    color[gem] = gcol[gem]
    rough[gem] = 0.12

    # Запечённая тень (AO) с тёплым оттенком: под ручками, в устье, в стыках.
    a = 0.5 + 0.5 * np.clip(ao, 0, 1)
    color *= np.stack([a ** 0.75, a, a ** 1.2], axis=-1)
    # Золото — металл с бликом.
    rough[gold] = 0.3
    metal[gold] = 0.65

    color = np.clip(color, 0, 1)
    hz = height * 6.0
    gy_, gx_ = np.gradient(hz)
    normal = np.stack([-gx_, gy_, np.ones_like(hz)], axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    return color, normal * 0.5 + 0.5, rough, metal


def bake_ao(obj, others):
    """Запекает окклюзию (Cycles) в развёртку объекта; соседей на время убирает подальше."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.world.light_settings.distance = 0.7
    scene.render.bake.margin = 8
    img = bpy.data.images.new(obj.name + "_AO", TEX, TEX, alpha=False, float_buffer=True)
    img.generated_color = (1, 1, 1, 1)
    mat = bpy.data.materials.new(obj.name + "_Bake")
    mat.use_nodes = True
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img
    mat.node_tree.nodes.active = node
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for o in others:
        o.location.z -= 500
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.bake(type="AO")
    for o in others:
        o.location.z += 500
    obj.data.materials.clear()
    return np.array(img.pixels[:], np.float32).reshape(TEX, TEX, 4)[::-1, :, 0]


def save(path, arr):
    h, w, _ = arr.shape
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = arr
    img.pixels.foreach_set(rgba[::-1].ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return img


# ── Сцена ──────────────────────────────────────────────────────────────────────────────────────────────
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
collection = bpy.data.collections.new("ArtV8")
bpy.context.scene.collection.children.link(collection)

positions = {1: 8.0, 2: 4.0, 3: 0.0}  # камера смотрит в +z: +x слева → 1, 2, 3 слева направо
objects, studio, report = {}, [], []
for n, x in positions.items():
    objects[n] = build_amphora(f"ArtV8_Amphora{n}", n, (x, 0, 0), collection)


def gray(arr):
    return np.repeat(arr[..., None], 3, axis=-1)


for n, x in positions.items():
    obj = objects[n]
    ao = bake_ao(obj, [o for k, o in objects.items() if k != n])
    color, normal, rough, metal = paint(n, ao)
    paths = {"color": color, "normal": normal, "roughness": gray(rough)}
    if metal.max() > 0:
        paths["metalness"] = gray(metal)
    for kind, arr in paths.items():
        save(os.path.join(TEXDIR, f"amphora{n}_{kind}.png"), arr)
    mat = bpy.data.materials.new(f"Amphora{n}")
    mat.use_nodes = True
    mat.use_backface_culling = True  # как в Roblox: вывернутые грани сразу видны на превью
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]

    def tex_node(kind, colorspace):
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(os.path.join(TEXDIR, f"amphora{n}_{kind}.png"))
        node.image.colorspace_settings.name = colorspace
        return node

    nt.links.new(tex_node("color", "sRGB").outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex_node("roughness", "Non-Color").outputs["Color"], bsdf.inputs["Roughness"])
    if "metalness" in paths:
        nt.links.new(tex_node("metalness", "Non-Color").outputs["Color"], bsdf.inputs["Metallic"])
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex_node("normal", "Non-Color").outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    obj.data.materials.append(mat)
    obj.data.calc_loop_triangles()
    report.append(f"{n}: {len(obj.data.loop_triangles)} тр.")
    # FBX с развёрткой и данные для Studio (позиция, нормаль, uv по углам треугольников).
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    obj.location = (-x, 0, 0)  # FBX — с началом в центре низа
    bpy.ops.export_scene.fbx(filepath=os.path.join(REPO, "assets", "models", f"ArtV8_Amphora{n}.fbx"),
                             use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP")
    obj.location = (0, 0, 0)
    mesh = obj.data
    uvl = mesh.uv_layers.active.data
    verts, index, tri = [], {}, []
    for lt in mesh.loop_triangles:
        ids = []
        for li in lt.loops:
            co = mesh.vertices[mesh.loops[li].vertex_index].co - Vector((x, 0, 0))
            nr = lt.normal
            uvv = uvl[li].uv
            key = (round(co.x, 4), round(co.y, 4), round(co.z, 4), round(nr.x, 3), round(nr.y, 3), round(nr.z, 3),
                   round(uvv.x, 5), round(uvv.y, 5))
            if key not in index:
                index[key] = len(verts)
                verts.append(key)
            ids.append(index[key])
        tri.append(ids)
    studio.append({"model": n, "maps": sorted(paths), "v": [[k[0], k[2], -k[1]] for k in verts],
                   "n": [[k[3], k[5], -k[4]] for k in verts], "uv": [[k[6], 1 - k[7]] for k in verts], "t": tri})
with open(os.path.join(PREVIEWS, "studio_mesh.json"), "w", encoding="utf-8") as f:
    json.dump(studio, f)

# Манекен Roblox (R15, ≈ 5.2) слева.
grey = bpy.data.materials.new("Mannequin")
grey.use_nodes = True
grey.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin(rgb("D3D8E0")), 1)
for center, size in (((0, 4.65, 0), (1.15, 1.15, 1.15)), ((0, 3.2, 0), (2.0, 1.75, 1.0)), ((-1.5, 3.2, 0), (0.95, 1.75, 0.95)),
                     ((1.5, 3.2, 0), (0.95, 1.75, 0.95)), ((-0.5, 1.15, 0), (0.95, 2.3, 0.95)),
                     ((0.5, 1.15, 0), (0.95, 2.3, 0.95))):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(size[0], size[2], size[1]), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.05, segments=1, affect="EDGES")
    bmesh.ops.translate(bm, vec=bl(Vector(center) + Vector((11.8, 0, 0.3))), verts=bm.verts)
    me = bpy.data.meshes.new("Mannequin")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("Mannequin", me)
    me.materials.append(grey)
    collection.objects.link(o)

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
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.53, 0.57, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65
scene.world = world
for name, loc, energy, size in (("Key", (-2, 10, -10), 2600, 8), ("Fill", (14, 5, -6), 800, 9), ("Rim", (4, 8, 9), 1400, 6)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.size = energy, size
    light = bpy.data.objects.new(name, data)
    light.location = bl(loc)
    light.rotation_euler = (light.location - bl((4, 1.6, 0))).to_track_quat("Z", "Y").to_euler()
    scene.collection.objects.link(light)
floor = bpy.data.meshes.new("Floor")
floor.from_pydata([(-80, -80, 0), (80, -80, 0), (80, 80, 0), (-80, 80, 0)], [], [(0, 1, 2, 3)])
fm = bpy.data.materials.new("Floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.4, 0.42, 0.45, 1)
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


shot("lineup", (5.8, 4.4, -19), (5.8, 2.2, 0), 40, (1800, 900))
for n, x in positions.items():
    shot(f"amphora{n}_34", (x - 3.8, 3.8, -6.2), (x, 1.65, 0), 45, (900, 1000))
print("V8_OK " + "; ".join(report))

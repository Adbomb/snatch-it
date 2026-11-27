"""Быстрое сравнение вида башни (D74, запрос владельца 2026-11-27): 6 этажей 1-6-3-5-2-4, кадры с 60, 150 и 300 стадов
от земли (глаза игрока, поле зрения 70°), колпак C у всех. Детали не прорабатываются — сравниваются силуэты.

  A — как сейчас (лист Б v4): стопка тематических домиков (сцены floor_d39_v4.py).
  B — «Башня-витрина»: единый каркас на всю башню (одинаковые угловые колонны и плиты); фасад этажа — большое стекло,
      за ним тематическая комната-диорама и жилец; редкость — материал каркаса этажа (дерево / камень / мрамор / золото /
      фиолетовый кристалл / радужный), высота этажа и богатство диорамы; у Космического каркас шире и светится, по
      бокам — крупные выступы. Больше ничего не торчит.
  C — единый каркас + тематические фасадные панели (без стекла и диорам): крупные формы, без мелких окон.
Числа треугольников печатаются (TRIS). Только концепт: в игру не экспортируется.

Запуск: blender -b --factory-startup --python scripts/blender/tower_compare.py -- <репо> <v4> <папка>
        (<v4> — сцены floor_d39_v4.py: saloon_v4.blend, aquarium_v4.blend)
"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import floorkit as K  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, V4, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1]), os.path.abspath(argv[2])
os.makedirs(OUT, exist_ok=True)
X, Z = 18.12, 17.12
H = [20, 27, 32, 38, 46, 60]
ORDER = [(1, "aq"), (6, "cb"), (3, "aq"), (5, "cb"), (2, "cb"), (4, "aq")]  # редкость, тема (как в листе Б v4)
TX = 400.0
SLAB = 2.0  # плита этажа (единая)
COLW = 2.6  # угловая колонна (единая)

COL = {
    "wood": "D9B37A", "wood2": "C29A60", "stone": "9EA2A8", "marble": "F4F2EC", "vein": "BDB8B0", "gold": "E9B43A",
    "crystal": "8E44D8", "r1": "E53935", "r2": "FB8C00", "r3": "FDD835", "r4": "43A047", "r5": "1E88E5", "r6": "8E24AA",
    "frame": "3E3F45", "glass": "BFE3F2", "grass": "6FB35A",
    "s_floor": "8A5A34", "s_wall": "9A6A3E", "s_wall2": "835632", "s_dark": "5A3A20", "s_red": "C0392B",
    "s_cream": "F2E6D0", "s_glove": "D2302B", "s_green": "3FA14B", "s_green2": "2E8A3E", "s_rope": "F2E6D0",
    "a_floor": "E6D3A3", "a_wall": "1E3A6E", "a_wall2": "264A86", "a_teal": "2FC4B2", "a_aqua": "62D6EA",
    "a_fish": "FF8A3D", "a_coral": "FF7AA2", "a_coral2": "FF9F45", "a_tan": "D8A65A", "a_tanl": "EBC68C",
    "white": "F6F4EE", "black": "1C1C1C", "blush": "FF8FB0", "mouth": "7A1F2B", "lamp": "FFD27A",
    "cap_green": "4E9A3A", "cap_gold": "E9B43A", "cap_crystal": "38D6E0",
}
GLOW = {"a_aqua": 0.8, "lamp": 1.4, "r1": 0.5, "r2": 0.5, "r3": 0.5, "r4": 0.5, "r5": 0.5, "r6": 0.5, "crystal": 0.25,
        "cap_crystal": 0.4}
_mats = {}


def mat(key):
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new("TC_" + key)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    rgb = [int(COL[key][i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    b.inputs["Base Color"].default_value = (*lin, 1)
    b.inputs["Roughness"].default_value = 0.6
    if key in ("gold", "cap_gold"):
        b.inputs["Metallic"].default_value = 0.5
        b.inputs["Roughness"].default_value = 0.35
    if key in GLOW:
        b.inputs["Emission Color"].default_value = (*lin, 1)
        b.inputs["Emission Strength"].default_value = GLOW[key]
    if key == "glass":
        b.inputs["Alpha"].default_value = 0.1
        b.inputs["Roughness"].default_value = 0.3
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "BLENDED"  # ровное стекло без зерна
        else:
            m.blend_method = "BLEND"
    _mats[key] = m
    return m


class Batch:
    """Бруски и призмы одного варианта: копятся по материалам, build() — по одному мешу на материал."""

    def __init__(self, coll, ox=TX):
        self.coll, self.ox = coll, ox
        self.v, self.f = {}, {}

    def _add(self, key, verts, faces):
        v, f = self.v.setdefault(key, []), self.f.setdefault(key, [])
        k = len(v)
        v.extend(verts)
        f.extend(tuple(k + i for i in face) for face in faces)

    def box(self, key, x0, x1, y0, y1, z0, z1):
        p = [K.P(x + self.ox, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        self._add(key, p, [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])

    def prism(self, key, poly, a0, a1, axis="y"):
        """Призма: poly — в плоскости поперёк оси ('y': (x, z); 'z': (x, y); 'x': (z, y)), от a0 до a1 вдоль оси."""
        def P(u, v, w):
            if axis == "y":
                return K.P(u + self.ox, w, v)
            if axis == "z":
                return K.P(u + self.ox, v, w)
            return K.P(w + self.ox, v, u)

        n = len(poly)
        verts = [P(u, v, a0) for u, v in poly] + [P(u, v, a1) for u, v in poly]
        faces = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        self._add(key, verts, faces)

    def ngon(self, cx, cy, r, n=8, rot=22.5):
        return [(cx + r * math.cos(math.radians(rot) + 2 * math.pi * k / n), cy + r * math.sin(math.radians(rot)
                                                                                                 + 2 * math.pi * k / n))
                for k in range(n)]

    def bipyramid(self, key, cx, cz, r, y0, ym, y1):
        p = [K.P(cx + self.ox, y0, cz)] + [K.P(cx + self.ox + r * math.cos(a), ym, cz + r * math.sin(a))
                                           for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)] + [K.P(cx + self.ox, y1, cz)]
        self._add(key, p, [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1), (5, 2, 1), (5, 3, 2), (5, 4, 3), (5, 1, 4)])

    def build(self):
        objs = []
        for key, v in self.v.items():
            me = bpy.data.meshes.new("TC_" + key)
            me.from_pydata(v, [], self.f[key])
            me.materials.append(mat(key))
            o = bpy.data.objects.new("TC_" + key, me)
            self.coll.objects.link(o)
            objs.append(o)
        bpy.context.view_layer.update()
        for o in objs:
            bm_fix(o)
        return objs


def bm_fix(o):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()


def tris(objs):
    n = 0
    for o in objs:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            n += len(o.data.loop_triangles)
    return n


# ── единый каркас ──────────────────────────────────────────────────────────────────────────────────────────────
def frame_keys(tier, k):
    """Материал каркаса по редкости; k — номер сегмента (радужный — по кругу, дерево — два тона)."""
    return {1: "wood" if k % 2 == 0 else "wood2", 2: "stone", 3: "marble", 4: "gold", 5: "crystal",
            6: "r%d" % (1 + k % 6)}[tier]


def frame(b, tier, y, h):
    """Каркас этажа: плита снизу (кант — материал редкости), четыре угловые колонны; у Космического — шире."""
    out = 2.4 if tier == 6 else 0.0
    cw = COLW + out
    b.box("frame", -X, X, y, y + SLAB, -Z, Z)
    seg = 6.0
    e = 0.5 + out
    for x0, x1, z0, z1, along in ((-X - e, X + e, -Z - e, -Z, "x"), (-X - e, X + e, Z, Z + e, "x"),
                                  (-X - e, -X, -Z, Z, "z"), (X, X + e, -Z, Z, "z")):
        a0, a1 = (x0, x1) if along == "x" else (z0, z1)
        n = max(1, round((a1 - a0) / seg))
        for k in range(n):
            s0, s1 = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
            if along == "x":
                b.box(frame_keys(tier, k), s0, s1, y, y + SLAB, z0, z1)
            else:
                b.box(frame_keys(tier, k), x0, x1, y, y + SLAB, s0, s1)
    n = max(1, round((h - SLAB) / 9.0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, x1 = sorted((sx * (X - COLW + 0.4), sx * (X + 0.4 + out)))
            z0, z1 = sorted((sz * (Z - COLW + 0.4), sz * (Z + 0.4 + out)))
            for k in range(n):
                y0 = y + SLAB + (h - SLAB) * k / n
                y1 = y + SLAB + (h - SLAB) * (k + 1) / n
                b.box(frame_keys(tier, k + (sx > 0) + 2 * (sz > 0)), x0, x1, y0, y1, z0, z1)
    if tier == 3:  # прожилки мрамора на колоннах
        for sx in (-1, 1):
            for j in range(3):
                yy = y + SLAB + (h - SLAB) * (0.2 + 0.3 * j)
                x0, x1 = sorted((sx * (X - COLW + 0.6), sx * (X + 0.2)))
                b.box("vein", x0, x1, yy, yy + 0.25, -Z - 0.47, -Z - 0.4)


def side_wings(b, theme, y, h):
    """Крупные выступы по бокам Космического этажа (вынос ≤ 6): салун — руки-кактусы с перчатками, океанариум —
    плавники."""
    for sx in (-1, 1):
        if theme == "cb":
            x0, x1 = sorted((sx * X, sx * (X + 4.4)))
            b.box("s_green", x0, x1, y + h * 0.42, y + h * 0.5, -2.0, 2.0)
            x0, x1 = sorted((sx * (X + 2.2), sx * (X + 5.6)))
            b.box("s_green", x0, x1, y + h * 0.42, y + h * 0.66, -2.0, 2.0)
            x0, x1 = sorted((sx * (X + 1.4), sx * (X + 6.0)))
            b.box("white", x0, x1, y + h * 0.66, y + h * 0.69, -2.3, 2.3)
            b.box("s_glove", x0, x1, y + h * 0.69, y + h * 0.82, -2.6, 2.6)
        else:
            for j in range(3):
                x0, x1 = sorted((sx * X, sx * (X + 5.6 - j * 1.6)))
                b.box("a_teal", x0, x1, y + h * (0.3 + 0.14 * j), y + h * (0.42 + 0.14 * j), -5.0 + j * 2, 5.0 - j * 2)


# ── B: комната-диорама за стеклом ──────────────────────────────────────────────────────────────────────────────
def room_shell(b, theme, y0, y1):
    f, w, w2 = ("s_floor", "s_wall", "s_wall2") if theme == "cb" else ("a_floor", "a_wall", "a_wall2")
    b.box(f, -X + 0.5, X - 0.5, y0, y0 + 0.3, -Z + 0.5, Z - 0.5)
    b.box(w, -X + 0.5, X - 0.5, y0, y1, Z - 1.2, Z - 0.3)  # задняя стена
    n = 4
    for k in range(n):  # крупные полосы задней стены
        if k % 2 == 0:
            x0 = -X + 0.5 + (2 * X - 1) * k / n
            b.box(w2, x0, x0 + (2 * X - 1) / n, y0, y1, Z - 1.35, Z - 1.2)
    b.box(w2 if theme == "cb" else "a_teal", -X + 0.5, X - 0.5, y1 - 0.3, y1, -Z + 0.5, Z - 0.5)  # потолок: с земли виден он


def glass_walls(b, tier, y0, y1):
    """Большое стекло спереди и по бокам; импосты — в цвет каркаса этажа (2 спереди, 1 сбоку)."""
    b.box("glass", -X + COLW - 0.4, X - COLW + 0.4, y0, y1, -Z + 0.2, -Z + 0.35)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (X - 0.35), sx * (X - 0.2)))
        b.box("glass", x0, x1, y0, y1, -Z + COLW - 0.4, Z - COLW + 0.4)
        b.box(frame_keys(tier, 0), sx * (X - 0.45) - 0.25, sx * (X - 0.45) + 0.25, y0, y1, -0.25, 0.25)
    for x in (-5.2, 5.2):
        b.box(frame_keys(tier, 0), x - 0.25, x + 0.25, y0, y1, -Z + 0.05, -Z + 0.55)


def diorama(b, theme, tier, y0, y1):
    """Крупные предметы темы; богатство растёт с редкостью."""
    h = y1 - y0
    if theme == "cb":  # салун
        b.box("s_dark", -15.0, -4.0, y0 + 0.3, y0 + 3.6, 11.0, 13.6)  # стойка
        b.box("s_cream", -15.4, -3.6, y0 + 3.6, y0 + 4.1, 10.6, 14.0)
        b.box("s_glove", 5.0, 12.0, y0 + h * 0.5, y0 + h * 0.5 + min(6.0, h * 0.3), Z - 1.9, Z - 1.3)  # перчатка-эмблема
        b.box("white", 6.5, 10.5, y0 + h * 0.5 - 1.4, y0 + h * 0.5, Z - 1.9, Z - 1.3)
        if tier >= 2:
            for k in range(3):
                b.prism("s_dark", b.ngon(11.0 + k * 0.0, 9.0 - k * 3.0, 1.5), y0 + 0.3, y0 + 3.4)
        if tier >= 3:  # ринг: помост, столбы, канаты
            b.box("s_red", -8.5, 8.5, y0 + 0.3, y0 + 1.6, -11.5, 4.5)
            b.box("s_cream", -8.0, 8.0, y0 + 1.6, y0 + 1.9, -11.0, 4.0)
            for sx in (-1, 1):
                for z in (-11.0, 4.0):
                    b.box("s_dark", sx * 8.0 - 0.4, sx * 8.0 + 0.4, y0 + 1.9, y0 + 6.2, z - 0.4, z + 0.4)
                for yy in (3.4, 5.0):
                    b.box("s_rope", sx * 8.0 - 0.12, sx * 8.0 + 0.12, y0 + yy, y0 + yy + 0.25, -11.0, 4.0)
            for z in (-11.0, 4.0):
                for yy in (3.4, 5.0):
                    b.box("s_rope", -8.0, 8.0, y0 + yy, y0 + yy + 0.25, z - 0.12, z + 0.12)
        if tier >= 4:  # флаги-вымпелы и лампы
            for k in range(6):
                x = -13.0 + k * 5.2
                b.box("s_red" if k % 2 == 0 else "s_cream", x - 1.2, x + 1.2, y1 - 3.6, y1 - 0.6, Z - 1.9, Z - 1.5)
            for x in (-9.0, 0.0, 9.0):
                b.box("lamp", x - 0.8, x + 0.8, y1 - 2.6, y1 - 1.4, -5.0, -3.4)
        if tier >= 5:  # кактусы по углам и кубок
            for sx in (-1, 1):
                b.box("s_green", sx * 13.0 - 1.4, sx * 13.0 + 1.4, y0 + 0.3, y0 + h * 0.6, -12.5, -9.7)
                b.box("s_green2", sx * 13.0 - 2.8, sx * 13.0 + 2.8, y0 + h * 0.3, y0 + h * 0.36, -11.8, -10.4)
        if tier >= 6:  # второй ярус-балкон внутри и гигантские перчатки
            b.box("s_dark", -X + 0.6, X - 0.6, y0 + h * 0.55, y0 + h * 0.55 + 0.8, 6.0, Z - 1.2)
            for sx in (-1, 1):
                b.box("s_glove", sx * 11.0 - 3.0, sx * 11.0 + 3.0, y0 + h * 0.62, y0 + h * 0.62 + 7.0, 7.5, 12.5)
                b.box("white", sx * 11.0 - 2.4, sx * 11.0 + 2.4, y0 + h * 0.62 - 1.6, y0 + h * 0.62, 8.0, 12.0)
    else:  # океанариум
        tw = min(h - 3.0, 12.0)
        b.box("a_aqua", -14.0, 14.0, y0 + 1.0, y0 + 1.0 + tw, Z - 3.6, Z - 1.3)  # большой аквариум у задней стены
        b.box("a_teal", -14.6, 14.6, y0 + 0.3, y0 + 1.0, Z - 4.0, Z - 1.2)
        for k in range(4):
            fx = -10.0 + k * 6.6
            fy = y0 + 2.5 + (k % 2) * tw * 0.45
            b.box("a_fish", fx - 1.4, fx + 1.4, fy, fy + 1.6, Z - 3.9, Z - 3.6)
            b.box("a_coral2", fx + 1.4, fx + 2.2, fy + 0.2, fy + 1.4, Z - 3.9, Z - 3.6)
        if tier >= 2:
            for sx in (-1, 1):
                b.box("a_coral", sx * 12.5 - 1.3, sx * 12.5 + 1.3, y0 + 0.3, y0 + 3.4, -1.0, 1.6)
                b.box("a_coral2", sx * 10.4 - 0.9, sx * 10.4 + 0.9, y0 + 0.3, y0 + 2.2, 0.0, 1.8)
        if tier >= 3:  # колонны-пузырьки
            for sx in (-1, 1):
                b.prism("a_aqua", b.ngon(sx * 13.5, -11.0, 1.4), y0 + 0.3, y1 - 0.3)
        if tier >= 4:  # медузы-лампы и песчаный помост
            for x in (-8.0, 0.0, 8.0):
                b.box("lamp", x - 1.0, x + 1.0, y1 - 3.0, y1 - 1.6, -4.0, -2.0)
            b.prism("a_tanl", b.ngon(0, -6.0, 7.5), y0 + 0.3, y0 + 1.2)
        if tier >= 5:
            b.box("a_teal", -X + 0.6, X - 0.6, y0 + h * 0.55, y0 + h * 0.55 + 0.6, 4.0, Z - 3.6)
        if tier >= 6:
            for sx in (-1, 1):
                b.box("a_aqua", sx * 12.0 - 3.0, sx * 12.0 + 3.0, y0 + h * 0.6, y1 - 1.0, 5.0, 11.0)


def big_face(b, theme, cx, cy, zf, s):
    """Крупное лицо существа на панели (как у существ коллекции)."""
    for d in (-1, 1):
        ex = cx + d * 2.9 * s
        b.box("white", ex - 1.6 * s, ex + 1.6 * s, cy - 1.3 * s, cy + 1.3 * s, zf - 0.5, zf)
        b.box("black", ex - d * 0.45 * s - 0.6 * s, ex - d * 0.45 * s + 0.6 * s, cy - 0.95 * s, cy + 0.25 * s, zf - 0.75, zf - 0.5)
        b.box("s_green2" if theme == "cb" else "a_wall2", ex - 2.1 * s, ex + 2.1 * s, cy + 1.9 * s, cy + 2.6 * s, zf - 0.6, zf)
        b.box("blush", ex + d * 2.2 * s - 0.9 * s, ex + d * 2.2 * s + 0.9 * s, cy - 2.6 * s, cy - 2.0 * s, zf - 0.4, zf)
    b.box("mouth", cx - 3.2 * s, cx + 3.2 * s, cy - 4.8 * s, cy - 3.2 * s, zf - 0.4, zf)
    for x in (-1.8, -0.6, 0.6, 1.8):
        b.box("white", cx + (x - 0.45) * s, cx + (x + 0.45) * s, cy - 3.9 * s, cy - 3.2 * s, zf - 0.6, zf - 0.4)


def panels(b, theme, tier, y0, y1):
    """C: фасадные панели темы — крупные формы, без мелких окон."""
    h = y1 - y0
    zf = -Z + 0.3
    if theme == "cb":
        base, band, body = "s_wall", "s_wall2", "s_green"
    else:
        base, band, body = "a_wall", "a_wall2", "a_tan"
    for face in ("front", "left", "right", "back"):
        if face in ("front", "back"):
            s = -1 if face == "front" else 1
            z0, z1 = sorted((s * (Z - 0.3), s * (Z - 1.0)))
            b.box(base, -X + 0.4, X - 0.4, y0, y1, z0, z1)
            zz0, zz1 = sorted((s * (Z - 0.3), s * (Z - 0.05)))
            b.box(band, -X + 0.4, X - 0.4, y0 + h * 0.0, y0 + h * 0.22, zz0, zz1)  # цоколь-полоса
            b.box("s_red" if theme == "cb" else "a_teal", -X + 0.4, X - 0.4, y0 + h * 0.22, y0 + h * 0.22 + 1.0, zz0 - 0.1 * (s < 0),
                  zz1 + 0.1 * (s > 0))
        else:
            s = -1 if face == "left" else 1
            x0, x1 = sorted((s * (X - 0.3), s * (X - 1.0)))
            b.box(base, x0, x1, y0, y1, -Z + 0.4, Z - 0.4)
            xx0, xx1 = sorted((s * (X - 0.3), s * (X - 0.05)))
            b.box(band, xx0, xx1, y0, y0 + h * 0.22, -Z + 0.4, Z - 0.4)
            b.box("s_red" if theme == "cb" else "a_teal", xx0 - 0.1 * (s < 0), xx1 + 0.1 * (s > 0), y0 + h * 0.22, y0 + h * 0.22 + 1.0,
                  -Z + 0.4, Z - 0.4)
            # боковая крупная форма
            cy = y0 + h * 0.62
            r = min(5.0, h * 0.22)
            if theme == "cb":
                b.box("s_glove", xx0 - 0.3 * (s < 0), xx1 + 0.3 * (s > 0), cy - r, cy + r, -r * 0.9, r * 0.9)
                b.box("white", xx0 - 0.3 * (s < 0), xx1 + 0.3 * (s > 0), cy - r - 1.6, cy - r, -r * 0.7, r * 0.7)
            else:
                b.prism("a_aqua", [(u, v) for u, v in b.ngon(0, cy, r)], min(xx0, xx1) - 0.3 * (s < 0), max(xx0, xx1) + 0.3 * (s > 0),
                        axis="x")
    cy = y0 + h * 0.62
    if tier >= 5:  # существо на фасаде крупно: тело-плашка и лицо
        w = 11.0 if tier == 5 else 14.0
        b.box(body, -w, w, y0 + h * 0.22 + 1.0, y1 - 1.0, zf - 0.7, zf)
        big_face(b, theme, 0, y0 + h * 0.68, zf - 0.7, 1.25 if tier == 5 else 1.7)
    elif theme == "cb":  # перчатка-эмблема растёт с редкостью
        r = min(2.6 + tier * 0.9, h * 0.25)
        b.box("s_glove", -r, r, cy - r * 0.8, cy + r, zf - 0.7, zf)
        b.box("s_glove", -r * 1.35, -r * 0.9, cy - r * 0.3, cy + r * 0.4, zf - 0.7, zf)
        b.box("white", -r * 0.8, r * 0.8, cy - r * 0.8 - 1.6, cy - r * 0.8, zf - 0.7, zf)
        b.box("s_dark", -3.4, 3.4, y0, y0 + min(8.5, h * 0.36), zf - 0.5, zf)  # двери-крылья
        b.box("s_cream", -2.8, 2.8, y0 + 2.2, y0 + min(6.6, h * 0.3), zf - 0.7, zf - 0.5)
    else:  # большой иллюминатор с рыбой
        r = min(2.8 + tier * 1.0, h * 0.27)
        b.prism("a_teal", b.ngon(0, cy, r + 0.9), zf - 0.6, zf, axis="z")
        b.prism("a_aqua", b.ngon(0, cy, r), zf - 0.8, zf - 0.6, axis="z")
        b.box("a_fish", -r * 0.5, r * 0.35, cy - r * 0.28, cy + r * 0.28, zf - 1.0, zf - 0.8)
        b.box("a_coral2", r * 0.35, r * 0.62, cy - r * 0.3, cy + r * 0.3, zf - 1.0, zf - 0.8)
        b.box("a_wall2", -3.2, 3.2, y0, y0 + min(7.5, h * 0.34), zf - 0.5, zf)
        b.box("a_aqua", -2.6, 2.6, y0 + 0.4, y0 + min(6.9, h * 0.31), zf - 0.7, zf - 0.5)


def cap_c(b, ry):
    """Колпак C: сад, золотое кольцо, кристалл в четырёх когтях."""
    b.box("cap_green", -X + 1, X - 1, ry, ry + 1.5, -Z + 1, Z - 1)
    for k in range(10):
        a = 2 * math.pi * k / 10
        b.box("cap_green", math.cos(a) * 13.5 - 1.8, math.cos(a) * 13.5 + 1.8, ry + 1.5, ry + 3.6, math.sin(a) * 12.5 - 1.8,
              math.sin(a) * 12.5 + 1.8)
    b.prism("cap_gold", b.ngon(0, 0, 10.0), ry + 1.5, ry + 4.5)
    b.bipyramid("cap_crystal", 0, 0, 8.5, ry + 5.0, ry + 19.0, ry + 35.0)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        cx, cz = math.cos(a) * 9.2, math.sin(a) * 9.2
        b.box("cap_gold", cx - 1.6, cx + 1.6, ry + 4.5, ry + 23.0, cz - 1.6, cz + 1.6)


# ══ сцена ════════════════════════════════════════════════════════════════════════════════════════════════════
bpy.ops.wm.open_mainfile(filepath=os.path.join(V4, "saloon_v4.blend"))
scene = bpy.context.scene
cb_base = [o for o in bpy.data.objects if o.name.startswith(("CB_F_", "CB_I_"))]
with bpy.data.libraries.load(os.path.join(V4, "aquarium_v4.blend")) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith(("AQ_F_", "AQ_I_"))]
    dst.collections = ["Q1", "Q3", "Q4"]
aq_base = [o for o in dst.objects if o is not None]
aqc = {k: list(c.all_objects) for k, c in zip(("Q1", "Q3", "Q4"), dst.collections)}
scc = {k: list(bpy.data.collections[k].all_objects) for k in ("Q2", "Q4", "Q5", "Q6")}
for c in scene.collection.children:
    c.hide_render = True


def new_coll(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


def copy_tree(objs, coll, offset):
    made = {}
    for o in objs:
        c = o.copy()
        coll.objects.link(c)
        made[o] = c
    for o, c in made.items():
        if o.parent in made:
            c.parent = made[o.parent]
        else:
            c.location = o.location + offset
    return list(made.values())


RES = {"cb": [o for o in scc["Q4"] if o.name.startswith("Resident") or (o.parent and o.parent.name.startswith("Resident"))],
       "aq": [o for o in aqc["Q4"] if o.name.startswith("Resident") or (o.parent and o.parent.name.startswith("Resident"))]}


def resident(theme, coll, x, y, z, height):
    """Жилец — готовая модель коллекции: копия, рост height, низ — на y, центр — (x, z)."""
    objs = copy_tree(RES[theme], coll, Vector((0, 0, 0)))
    root = next(o for o in objs if o.parent is None)
    bpy.context.view_layer.update()

    def bb():
        pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
        return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
                Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))

    lo, hi = bb()
    k = height / max(1e-6, hi.z - lo.z)
    root.scale = root.scale * k
    bpy.context.view_layer.update()
    lo, hi = bb()
    t = K.P(x + TX, y, z)
    root.location += Vector((t.x - (lo.x + hi.x) / 2, t.y - (lo.y + hi.y) / 2, t.z - lo.z))
    return [o for o in objs if o.type == "MESH"]


counts = {}
# A — как сейчас (v4)
A = new_coll("VarA")
y = 0.0
a_objs = []
src_a = {(1, "aq"): aqc["Q1"] + aq_base, (6, "cb"): scc["Q6"], (3, "aq"): aqc["Q3"] + aq_base, (5, "cb"): scc["Q5"] + cb_base,
         (2, "cb"): scc["Q2"] + cb_base, (4, "aq"): aqc["Q4"] + aq_base}
for t, th in ORDER:
    a_objs += copy_tree(src_a[(t, th)], A, Vector((-TX, 0, y + 1.0)))
    y += H[t - 1]
RY = y
ba = Batch(A)
cap_c(ba, RY)
ba.build()
counts["A"] = tris(a_objs)

# B — «Башня-витрина»
Bc = new_coll("VarB")
bb_ = Batch(Bc)
y = 0.0
res_objs = []
for t, th in ORDER:
    h = H[t - 1]
    frame(bb_, t, y, h)
    room_shell(bb_, th, y + SLAB, y + h)
    diorama(bb_, th, t, y + SLAB, y + h)
    glass_walls(bb_, t, y + SLAB, y + h)
    if t == 6:
        side_wings(bb_, th, y, h)
    res_objs += resident(th, Bc, 0.0, y + SLAB + (1.9 if (th == "cb" and t >= 3) else 1.2 if (th == "aq" and t >= 4) else 0.3),
                         -5.0, min(h - SLAB - 3.5, 8.0 + t * 3.2))
    lamp = bpy.data.objects.new("RoomLight", bpy.data.lights.new("RoomLight", "POINT"))
    lamp.data.energy, lamp.data.color, lamp.data.use_shadow = 1500 + 500 * t, (1.0, 0.94, 0.85), False
    lamp.data.specular_factor = 0.0
    lamp.location = K.P(TX, y + h - 2.5, -4.0)
    Bc.objects.link(lamp)
    y += h
b_frame = Batch(Bc)
cap_c(b_frame, RY)
b_objs = bb_.build()
b_frame.build()
counts["B"] = tris(b_objs)
counts["B_res"] = tris(res_objs)

# C — каркас + панели
Cc = new_coll("VarC")
bc = Batch(Cc)
y = 0.0
for t, th in ORDER:
    h = H[t - 1]
    frame(bc, t, y, h)
    panels(bc, th, t, y + SLAB, y + h)
    if t == 6:
        side_wings(bc, th, y, h)
    y += h
c_objs = bc.build()
bcap = Batch(Cc)
cap_c(bcap, RY)
bcap.build()
counts["C"] = tris(c_objs)
print("TRIS", counts, "TOWER_HEIGHT", RY, flush=True)

# земля и кадры
G = new_coll("Ground")
bg = Batch(G)
bg.box("grass", -900, 900, -1.0, 0.0, -900, 900)
bg.build()
cam = scene.camera
scene.render.resolution_x, scene.render.resolution_y = 750, 1000
cam.data.angle_y = math.radians(70)
cam.data.clip_end = 3000
SHOTS = {60: ((-14, 5, -Z - 60), (0, 58, -Z)), 150: ((-36, 5, -Z - 150), (0, 100, 0)), 300: ((-72, 5, -Z - 300), (0, 118, 0))}
for name, coll in (("A", A), ("B", Bc), ("C", Cc)):
    for c in (A, Bc, Cc):
        c.hide_render = c is not coll
    G.hide_render = False
    for dist, (eye, target) in SHOTS.items():
        e, t_ = K.P(eye[0] + TX, eye[1], eye[2]), K.P(target[0] + TX, target[1], target[2])
        cam.location = e
        cam.rotation_euler = (e - t_).to_track_quat("Z", "Y").to_euler()
        scene.render.filepath = os.path.join(OUT, "%s_%d.png" % (name, dist))
        bpy.ops.render.render(write_still=True)
        print("SHOT", name, dist, flush=True)
print("DONE_COMPARE", flush=True)

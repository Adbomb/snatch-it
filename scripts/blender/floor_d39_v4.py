"""Лист Б v4 (D74): Мифический и Космический этажи «существо-дом» в стиле D39 — как наши боссы (королева, Йети).

Решения владельца 2026-11-27: микро-воксели отменены (рябь, чужой стиль рядом с D39, вес 45–75 тыс.). Та же идея
«существо-дом», но D39: крупные блоки с фаской, ступени-«кольца» вместо гладких кривых, чистые цвета без пооттеночной
ряби, врезанные окна и двери (рама наружу, стекло в глубине), лицо как у существ коллекции (прямоугольные глаза,
квадратные зрачки, брови-бруски, румянец). Без текстуры «кубики».
  Дом-кактус: рёбра крупными гранями, 6 крупных колючек-клиньев, перчатка, лицо; дом-верблюд: горбы-аквариумы
  (ступенчатое стекло + рыбы), иллюминаторы, морда. Мифический — органика сквозь здание D39 (лист Б v3).
  Вес: Космический ≤ 15 000 треугольников, Мифический ≤ 10 000, дальняя версия ≤ 1 500 (печатается).
  Жилец за стеклом атриума Золотого — готовая модель существа из коллекции (assets/models/art/boss4).
Модуль прежний: плиты и кант из сцен floor_rarity_v3.py, след по сетке, CHECK_TOP.

Запуск (папка <v3> — сцены floor_rarity_v3.py; кадры и сцены v4 — в <v4>):
  blender -b --factory-startup --python scripts/blender/floor_d39_v4.py -- <репо> <v3> <v4> saloon | aquarium | tower
Только концепт: в игру не экспортируется.
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import floorkit as K  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, V3, OUT, MODE = (os.path.abspath(argv[0]), os.path.abspath(argv[1]), os.path.abspath(argv[2]), argv[3])
os.makedirs(OUT, exist_ok=True)
X, Z = 18.12, 17.12
H = [20, 27, 32, 38, 46, 60]
SLAB = 2.6
NAMES = ["Деревянный", "Каменный", "Мраморный", "Золотой", "Мифический", "Космический"]
CH = 0.45  # фаска D39
COL = {
    "green": "3FA14B", "green2": "2E8A3E", "green_d": "245A2C", "spine": "F5E6B0", "white": "F6F4EE",
    "black": "1C1C1C", "mouth": "7A1F2B", "blush": "FF8FB0", "glove": "D2302B", "glove_d": "A8231F",
    "pink": "FF6FA8", "glow": "FFE07A", "wood": "8A5A34", "wood_d": "5A3A20", "door": "4A2E18",
    "glassw": "FFD27A", "tan": "D8A65A", "tan_l": "EBC68C", "tan_d": "B8833F", "hoof": "5A3A22", "teal": "2FC4B2",
    "teal_d": "1F6F7A", "aqua": "62D6EA", "glassq": "5FD0E8", "fish": "FF8A3D", "fish_d": "D9661F",
}
_mats = {}


def mat(key):
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new("V4_" + key)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    rgb = [int(COL[key][i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    b.inputs["Base Color"].default_value = (*lin, 1)
    b.inputs["Roughness"].default_value = 0.6
    if key in ("glow", "glassw", "aqua"):  # светящиеся акценты — мягко, не неон
        b.inputs["Emission Color"].default_value = (*lin, 1)
        b.inputs["Emission Strength"].default_value = 0.9
    if key == "glassq":  # стекло горбов: видны рыбы внутри
        b.inputs["Alpha"].default_value = 0.45
        b.inputs["Roughness"].default_value = 0.05
        b.inputs["Emission Color"].default_value = (*lin, 1)
        b.inputs["Emission Strength"].default_value = 0.08
    _mats[key] = m
    return m


class Kit:
    """Детали D39 одной сборки: всё в координатах игры (y — вверх), каждая деталь — свой объект в коллекции."""

    def __init__(self, coll):
        self.coll = coll
        self.objs = []

    def _obj(self, bm, key, name="P"):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat(key))
        o = bpy.data.objects.new(name, me)
        self.coll.objects.link(o)
        self.objs.append(o)
        return o

    def prism(self, poly, y0, y1, key, ch=CH, axis="y", at=0.0, all_edges=False):
        """Призма: многоугольник poly (в плоскости поперёк оси) от y0 до y1 вдоль оси axis; фаска ch по рёбрам
        оснований (all_edges — и по боковым)."""
        bm = bmesh.new()

        def P(u, v, w):  # u, v — в плоскости многоугольника, w — вдоль оси
            if axis == "y":
                return K.P(u, w, v)
            if axis == "x":
                return K.P(w, v, u)
            return K.P(u, v, w)

        lo = [bm.verts.new(P(u, v, y0)) for u, v in poly]
        hi = [bm.verts.new(P(u, v, y1)) for u, v in poly]
        n = len(poly)
        bm.faces.new(lo[::-1])
        bm.faces.new(hi)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bm.normal_update()
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if ch > 0:
            cap = set(lo) | set(hi)
            edges = [e for e in bm.edges if all_edges or (e.verts[0] in cap and e.verts[1] in cap
                                                         and ((e.verts[0] in lo) == (e.verts[1] in lo)))]
            size = min(abs(y1 - y0), min(max(u for u, _ in poly) - min(u for u, _ in poly),
                                         max(v for _, v in poly) - min(v for _, v in poly)))
            bmesh.ops.bevel(bm, geom=edges, offset=min(ch, size * 0.3), segments=1, affect="EDGES",
                            clamp_overlap=True)
        return self._obj(bm, key)

    def box(self, x0, x1, y0, y1, z0, z1, key, ch=CH):
        poly = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        return self.prism(poly, y0, y1, key, ch=ch, all_edges=True)

    def rbox(self, cx, cy, cz, sx, sy, sz, key, rot=0.0, ch=CH * 0.6, normal="z"):
        """Брусок с поворотом rot (градусы) вокруг нормали грани ('z' — перед/зад, 'x' — бока): брови, ресницы."""
        o = self.box(-sx / 2, sx / 2, -sy / 2, sy / 2, -sz / 2, sz / 2, key, ch=ch)
        r = Matrix.Rotation(math.radians(rot), 4, "Y" if normal == "z" else "X")
        o.matrix_world = Matrix.Translation(K.P(cx, cy, cz)) @ r
        return o

    def oct(self, cx, cz, rx, rz, y0, y1, key, cut=0.3, ch=CH, n=8):
        """Восьмигранник (скруглённый прямоугольник со срезанными углами) — «кольцо» D39."""
        if n == 8:
            cx_, cz_ = rx * cut, rz * cut
            poly = [(cx - rx + cx_, cz - rz), (cx + rx - cx_, cz - rz), (cx + rx, cz - rz + cz_), (cx + rx, cz + rz - cz_),
                    (cx + rx - cx_, cz + rz), (cx - rx + cx_, cz + rz), (cx - rx, cz + rz - cz_), (cx - rx, cz - rz + cz_)]
        else:
            poly = [(cx + rx * math.cos(2 * math.pi * k / n), cz + rz * math.sin(2 * math.pi * k / n)) for k in range(n)]
        return self.prism(poly, y0, y1, key, ch=ch)

    def spike(self, base, direction, r, length, key):
        """Колючка-клин: четырёхгранная пирамида от base (игра) по direction (игра)."""
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=r, radius2=0.0, depth=length)
        o = self._obj(bm, key, "Spike")
        d = K.P(*direction) - K.P(0, 0, 0)
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        o.matrix_world = Matrix.Translation(K.P(*base) + d.normalized() * (length / 2)) @ q.to_matrix().to_4x4() \
            @ Matrix.Rotation(math.radians(45), 4, "Z")
        return o

    def disc(self, center, normal, r, depth, key, n=8):
        """Плоский восьмигранник (стекло иллюминатора) с осью по нормали ('x' или 'z' игры)."""
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r, radius2=r, depth=depth)
        o = self._obj(bm, key, "Disc")
        rot = Matrix.Rotation(math.radians(90), 4, "X") if normal == "z" else Matrix.Rotation(math.radians(90), 4, "Y")
        o.matrix_world = Matrix.Translation(K.P(*center)) @ rot @ Matrix.Rotation(math.radians(22.5), 4, "Z")
        return o

    # ── составные детали ──
    def window(self, face, a, y, w, h, frame="wood", glass="glassw", shutters=None, sill=True):
        """Врезанное окно: стекло в плоскости стены, рама наружу на 0.7 (стекло смотрится в глубине), подоконник."""
        fz = {"front": -1, "back": 1}.get(face)
        d = 0.7
        if fz is not None:
            zf = fz * PLANE[face]
            z0, z1 = sorted((zf, zf + fz * d))
            self.box(a - w / 2, a + w / 2, y - h / 2, y + h / 2, min(zf, zf + fz * 0.05), max(zf, zf + fz * 0.05), glass, ch=0)
            for x0, x1, y0, y1 in ((a - w / 2 - 0.5, a - w / 2, y - h / 2, y + h / 2), (a + w / 2, a + w / 2 + 0.5, y - h / 2,
                                                                                          y + h / 2),
                                   (a - w / 2 - 0.5, a + w / 2 + 0.5, y + h / 2, y + h / 2 + 0.5)):
                self.box(x0, x1, y0, y1, z0, z1, frame, ch=0)
            if sill:
                self.box(a - w / 2 - 0.8, a + w / 2 + 0.8, y - h / 2 - 0.6, y - h / 2, min(z0, z1) - 0.2 * (fz < 0),
                         max(z0, z1) + 0.2 * (fz > 0), frame, ch=0.15)
            if shutters:
                for s in (-1, 1):
                    xs = a + s * (w / 2 + 1.25)
                    self.box(xs - 0.65, xs + 0.65, y - h / 2, y + h / 2, z0, z1, shutters, ch=0.15)
        else:
            sx = -1 if face == "left" else 1
            xf = sx * PLANE[face]
            x0, x1 = sorted((xf, xf + sx * d))
            self.box(min(xf, xf + sx * 0.05), max(xf, xf + sx * 0.05), y - h / 2, y + h / 2, a - w / 2, a + w / 2, glass, ch=0)
            for z0, z1, y0, y1 in ((a - w / 2 - 0.5, a - w / 2, y - h / 2, y + h / 2), (a + w / 2, a + w / 2 + 0.5, y - h / 2,
                                                                                          y + h / 2),
                                   (a - w / 2 - 0.5, a + w / 2 + 0.5, y + h / 2, y + h / 2 + 0.5)):
                self.box(x0, x1, y0, y1, z0, z1, frame, ch=0)
            if sill:
                self.box(x0 - 0.2 * (sx < 0), x1 + 0.2 * (sx > 0), y - h / 2 - 0.6, y - h / 2, a - w / 2 - 0.8, a + w / 2 + 0.8,
                         frame, ch=0.15)
            if shutters:
                for s in (-1, 1):
                    zs = a + s * (w / 2 + 1.25)
                    self.box(x0, x1, y - h / 2, y + h / 2, zs - 0.65, zs + 0.65, shutters, ch=0.15)

    def porthole(self, face, a, y, r, frame="teal_d", glass="aqua"):
        """Иллюминатор: восьмигранная рама (8 брусков) наружу и стекло-восьмигранник в плоскости стены."""
        normal = "z" if face in ("front", "back") else "x"
        s = -1 if face in ("front", "left") else 1
        p = s * PLANE[face]
        c = (a, y, p) if normal == "z" else (p, y, a)
        self.disc(c, normal, r, 0.12, glass)
        h = math.pi / 8
        ri, ro = (r + 0.05) / math.cos(h), (r + 0.75) / math.cos(h)  # рама — трапеции между восьмиугольниками
        for k in range(8):
            a0, a1 = 2 * math.pi * k / 8 - h, 2 * math.pi * k / 8 + h
            pts = [(ri * math.cos(a0), ri * math.sin(a0)), (ri * math.cos(a1), ri * math.sin(a1)),
                   (ro * math.cos(a1), ro * math.sin(a1)), (ro * math.cos(a0), ro * math.sin(a0))]
            w0, w1 = sorted((p, p + s * 0.6))
            if normal == "z":
                self.prism([(a + u, y + v) for u, v in pts], w0, w1, frame, ch=0.08, axis="z")
            else:
                self.prism([(a + u, y + v) for u, v in pts], w0, w1, frame, ch=0.08, axis="x")

    def face(self, cx, cy, zf, s, mood="fight", sock="green_d", brow="green_d"):
        """Лицо существа коллекции на плоскости z = zf (перед — −z): глазницы, белки, квадратные зрачки, брови-бруски,
        рот с квадратными зубами, румянец."""
        for d in (-1, 1):
            ex = cx + d * 2.9 * s
            self.box(ex - 2.0 * s, ex + 2.0 * s, cy - 1.7 * s, cy + 1.7 * s, zf - 0.25, zf, sock, ch=0.2)
            self.box(ex - 1.6 * s, ex + 1.6 * s, cy - 1.3 * s, cy + 1.3 * s, zf - 0.55, zf - 0.25, "white", ch=0.15)
            px = ex - d * 0.45 * s
            self.box(px - 0.6 * s, px + 0.6 * s, cy - 0.95 * s, cy + 0.25 * s, zf - 0.8, zf - 0.55, "black", ch=0.08)
            rot = 14 * d if mood == "fight" else -8 * d
            self.rbox(ex, cy + 2.35 * s, zf - 0.45, 4.2 * s, 0.75 * s, 0.6, brow, rot=rot)
            self.box(ex + d * 2.2 * s - 0.9 * s, ex + d * 2.2 * s + 0.9 * s, cy - 2.6 * s, cy - 2.0 * s, zf - 0.35, zf,
                     "blush", ch=0.1)
        my = cy - 4.0 * s
        self.box(cx - 3.4 * s, cx + 3.4 * s, my - 0.9 * s, my + 0.9 * s, zf - 0.4, zf, "mouth", ch=0.2)
        self.box(cx + 2.6 * s, cx + 4.0 * s, my - 0.2 * s, my + 1.4 * s, zf - 0.4, zf, "mouth", ch=0.15)  # ухмылка
        for x in (-1.8, -0.6, 0.6, 1.8):
            self.box(cx + (x - 0.45) * s, cx + (x + 0.45) * s, my + 0.15 * s, my + 0.85 * s, zf - 0.65, zf - 0.4,
                     "white", ch=0.05)

    def glove(self, cx, cy, cz, s):
        """Боксёрская перчатка ступенями D39: кулак (3 яруса), большой палец, белая манжета."""
        self.box(cx - 2.2 * s, cx + 2.2 * s, cy, cy + 3.6 * s, cz - 2.0 * s, cz + 2.0 * s, "glove", ch=0.6 * s)
        self.box(cx - 1.8 * s, cx + 1.8 * s, cy + 3.6 * s, cy + 4.6 * s, cz - 1.6 * s, cz + 1.6 * s, "glove", ch=0.4 * s)
        self.box(cx - 1.4 * s, cx + 1.4 * s, cy - 0.5 * s, cy, cz - 1.4 * s, cz + 1.4 * s, "glove_d", ch=0.2)
        self.box(cx - 1.0 * s, cx + 0.6 * s, cy + 1.0 * s, cy + 2.8 * s, cz - 2.7 * s, cz - 1.8 * s, "glove_d", ch=0.3 * s)
        self.box(cx - 1.9 * s, cx + 1.9 * s, cy - 1.7 * s, cy - 0.5 * s, cz - 1.9 * s, cz + 1.9 * s, "white", ch=0.3 * s)

    def flower(self, cx, cy, cz, s=1.0):
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            self.box(cx + dx * 1.0 * s - 0.8 * s, cx + dx * 1.0 * s + 0.8 * s, cy, cy + 1.2 * s, cz + dz * 1.0 * s - 0.8 * s,
                     cz + dz * 1.0 * s + 0.8 * s, "pink", ch=0.25)
        self.box(cx - 0.6 * s, cx + 0.6 * s, cy + 0.6 * s, cy + 1.6 * s, cz - 0.6 * s, cz + 0.6 * s, "glow", ch=0.15)

    def fish(self, cx, cy, cz, s, face_x=-1):
        self.box(cx - 1.3 * s, cx + 1.3 * s, cy - 0.8 * s, cy + 0.8 * s, cz - 0.5 * s, cz + 0.5 * s, "fish", ch=0.25 * s)
        tx = cx - face_x * 1.3 * s
        self.box(min(tx, tx - face_x * 1.0 * s), max(tx, tx - face_x * 1.0 * s), cy - 0.9 * s, cy + 0.9 * s, cz - 0.15 * s,
                 cz + 0.15 * s, "fish_d", ch=0.08)
        ex = cx + face_x * 0.7 * s
        self.box(ex - 0.25 * s, ex + 0.25 * s, cy + 0.1 * s, cy + 0.5 * s, cz - 0.6 * s, cz + 0.6 * s, "black", ch=0.0)


PLANE = {"front": 16.6, "back": 16.6, "left": 17.6, "right": 17.6}


def band_top(t):
    return -1 + H[t - 1] - SLAB


# ══ Космический: дом-кактус ═══════════════════════════════════════════════════════════════════════════════════
def cosmic_saloon(k, far=False):
    top = band_top(6)
    rx, rz, cut = 17.6, 16.6, 0.26
    levels = [(0.2, 11.0)] + [(11.0 + i * 11.35, 11.0 + (i + 1) * 11.35) for i in range(4)]
    for i, (y0, y1) in enumerate(levels):  # ярусы-кольца: тело и тёмный пояс-уступ на стыке
        last = i == len(levels) - 1
        if far:
            break
        k.oct(0, 0, rx, rz, y0, y1 - 0.8 if not last else y1 - 3.2, "green", cut=cut)
        if not last:
            k.oct(0, 0, rx - 0.6, rz - 0.6, y1 - 0.8, y1, "green_d", cut=cut, ch=0.2)
        else:  # скруглённая макушка ступенями под верхней плитой
            k.oct(0, 0, rx - 1.4, rz - 1.4, y1 - 3.2, y1 - 1.4, "green", cut=cut + 0.04)
            k.oct(0, 0, rx - 3.2, rz - 3.2, y1 - 1.4, min(y1, top), "green2", cut=cut + 0.08)
    if far:  # дальняя версия: тело одной призмой, перчатка — брусок
        k.oct(0, 0, rx, rz, 0.2, top - 1.0, "green", cut=cut, ch=0)
        k.box(-23.6, -18.4, 28, 42, -2.2, 2.8, "glove", ch=0)
        return
    # рёбра крупными гранями: спереди крайние — во всю высоту, средние — до лица; бока и зад — во всю высоту
    for x in (-13.0, -6.5, 0.0, 6.5, 13.0):
        yt = top - 3.5 if abs(x) > 10 else 30.0
        k.box(x - 0.9, x + 0.9, 1.0, yt, -rz - 1.3, -rz + 0.2, "green2", ch=0.5)
        k.box(x - 0.9, x + 0.9, 1.0, top - 3.5, rz - 0.2, rz + 1.3, "green2", ch=0.5)
    for z in (-10.0, -3.5, 3.5, 10.0):
        for s in (-1, 1):
            k.box(min(s * (rx - 0.2), s * (rx + 1.3)), max(s * (rx - 0.2), s * (rx + 1.3)), 1.0, top - 3.5, z - 0.9, z + 0.9,
                  "green2", ch=0.5)
    # шесть крупных колючек-клиньев на рёбрах
    for base, dirv in (((-13.0, 20.0, -rz - 1.3), (0, 0.25, -1)), ((13.0, 44.0, -rz - 1.3), (0, 0.25, -1)),
                       ((-rx - 1.3, 14.0, -3.5), (-1, 0.25, 0)), ((-rx - 1.3, 38.0, 10.0), (-1, 0.25, 0)),
                       ((rx + 1.3, 26.0, 3.5), (1, 0.25, 0)), ((6.5, 32.0, rz + 1.3), (0, 0.25, 1))):
        k.spike(base, dirv, 1.7, 4.4, "spine")
    # лицо на фасаде (между крайними рёбрами)
    k.face(0, 44.0, -rz, 1.55, mood="fight")
    # рука с перчаткой — на левом боку (виден в главном ракурсе)
    k.box(-22.0, -rx + 0.3, 27.0, 30.4, -1.2, 2.2, "green", ch=0.6)
    k.box(-23.0, -19.8, 27.0, 35.4, -1.2, 2.2, "green", ch=0.6)
    k.glove(-21.4, 35.4, 0.5, 1.15)
    for c in ((-14.6, top - 1.6, -13.6), (14.6, top - 1.6, -13.6), (-14.6, top - 1.6, 13.6)):
        k.flower(*c, s=1.1)
    # окна салуна врезаны между рёбрами; дверь со створками и фонарь
    for x in (-9.75, 9.75):
        k.window("front", x, 6.5, 3.2, 4.6, shutters="glove")
    for x in (-9.75, -3.25, 3.25, 9.75):
        k.window("front", x, 17.2, 3.2, 4.6, shutters=None)
    for y in (6.5, 17.2, 28.5, 39.8, 50.0):
        for z in (-6.75, 0.0, 6.75):
            k.window("left", z, y, 3.0, 4.4)
            k.window("right", z, y, 3.0, 4.4)
        for x in (-9.75, -3.25, 3.25, 9.75):
            k.window("back", x, y, 3.0, 4.4)
    k.box(-3.6, 3.6, 0.2, 9.8, -rz - 0.8, -rz + 0.1, "wood_d", ch=0.3)
    k.box(-2.9, 2.9, 0.2, 8.9, -rz - 0.9, -rz - 0.6, "door", ch=0.1)
    for s in (-1, 1):
        k.box(s * 0.15, s * 2.7, 2.4, 6.6, -rz - 1.4, -rz - 1.0, "wood", ch=0.15)
    k.box(4.4, 5.6, 7.8, 9.4, -rz - 1.9, -rz - 0.7, "glow", ch=0.2)


# ══ Космический: дом-верблюд-аквариум ═══════════════════════════════════════════════════════════════════════════
def cosmic_camel(k, far=False):
    top = band_top(6)
    if far:
        k.oct(0, 0, 17.6, 16.6, 0.2, 37.0, "tan", cut=0.32, ch=0)
        for zc in (-7.6, 8.2):
            k.oct(0, zc, 10.0, 7.2, 37.0, 47.0, "glassq", ch=0)
            k.oct(0, zc, 6.5, 4.6, 47.0, top - 0.5, "glassq", ch=0)
        k.box(-6.0, 6.0, 30.0, 46.0, -22.6, -14.0, "tan", ch=0)
        return
    for sx in (-1, 1):  # ноги-опоры и копыта
        for sz in (-1, 1):
            k.oct(sx * 12.4, sz * 11.4, 4.4, 4.4, 1.6, 10.5, "tan_d", cut=0.3)
            k.oct(sx * 12.4, sz * 11.4, 4.8, 4.8, 0.2, 1.6, "hoof", cut=0.3, ch=0.3)
    for y0, y1, ins, key in ((8.5, 10.5, 2.2, "tan"), (10.5, 12.5, 0.8, "tan"), (12.5, 33.0, 0.0, "tan"),
                             (33.0, 35.0, 0.8, "tan"), (35.0, 37.0, 2.2, "tan_l")):
        k.oct(0, 0, 17.6 - ins, 16.6 - ins, y0, y1, key, cut=0.32)
    k.oct(0, 0, 18.0, 17.0, 25.8, 27.4, "teal", cut=0.32, ch=0.3)  # пояс
    for zc in (-7.6, 8.2):  # горбы-аквариумы: ступенчатое стекло, латунный обод, рыбы и пузырьки внутри
        k.oct(0, zc, 10.8, 7.6, 37.0, 37.9, "teal_d", cut=0.32, ch=0.2)
        for y0, y1, rx, rz in ((37.9, 41.6, 10.4, 7.3), (41.6, 45.2, 9.6, 6.7), (45.2, 48.6, 8.4, 5.9),
                               (48.6, 51.6, 6.8, 4.8), (51.6, top - 0.1, 4.8, 3.4)):
            k.oct(0, zc, rx, rz, y0, y1, "glassq", cut=0.32, ch=0.3)
        for j, (fx, fy, fz) in enumerate(((-4.5, 40.5, zc - 2.0), (3.5, 44.0, zc + 1.6), (-1.5, 48.0, zc - 0.5))):
            k.fish(fx, fy, fz, 1.15, face_x=-1 if j % 2 == 0 else 1)
        for b in ((2.5, 41.0, zc - 3.0), (3.0, 43.5, zc - 2.6), (-3.0, 46.5, zc + 2.4)):
            k.box(b[0] - 0.35, b[0] + 0.35, b[1] - 0.35, b[1] + 0.35, b[2] - 0.35, b[2] + 0.35, "white", ch=0.1)
    # голова и морда (вынос вперёд ≤ 6)
    k.box(-3.6, 3.6, 29.0, 37.5, -19.2, -14.0, "tan", ch=0.8)
    k.box(-6.0, 6.0, 35.5, 45.5, -21.4, -14.6, "tan", ch=1.0)
    k.box(-4.6, 4.6, 34.6, 39.6, -22.6, -19.4, "tan_l", ch=0.8)
    for d in (-1, 1):
        k.box(d * 5.2 - 0.9, d * 5.2 + 0.9, 44.2, 47.6, -18.6, -16.6, "tan_d", ch=0.4)  # уши
        ex = d * 2.9
        k.box(ex - 1.5, ex + 1.5, 40.3, 43.3, -21.95, -21.3, "white", ch=0.15)
        k.box(ex - 0.55 - d * 0.3, ex + 0.55 - d * 0.3, 40.6, 41.9, -22.2, -21.9, "black", ch=0.05)
        for j in (-1, 0, 1):
            k.rbox(ex + j * 0.9, 43.75, -21.7, 0.35, 1.0, 0.4, "black", rot=-j * 18, ch=0.05)  # ресницы
        k.box(d * 1.5 - 0.5, d * 1.5 + 0.5, 37.9, 38.7, -22.85, -22.55, "hoof", ch=0.05)  # ноздри
    for x0, x1, y0 in ((-2.6, -1.2, 36.4), (-1.2, 1.2, 35.9), (1.2, 2.6, 36.4)):  # улыбка ступенями
        k.box(x0, x1, y0, y0 + 0.55, -22.85, -22.55, "hoof", ch=0.05)
    k.box(-6.2, -4.6, 37.0, 38.0, -21.7, -21.3, "blush", ch=0.05)
    k.box(4.6, 6.2, 37.0, 38.0, -21.7, -21.3, "blush", ch=0.05)
    # иллюминаторы
    for y in (17.0, 31.0):
        for z in (-9.0, 0.0, 9.0):
            k.porthole("left", z, y, 2.6)
            k.porthole("right", z, y, 2.6)
        for x in (-9.0, 0.0, 9.0):
            k.porthole("back", x, y, 2.6)
    for x in (-11.0, 11.0):
        k.porthole("front", x, 18.0, 2.6)


# ══ Мифический: существо проступает сквозь здание D39 ═══════════════════════════════════════════════════════════
def mythic_saloon(k, far=False):
    top = band_top(5)
    for cx, cz in ((-15.2, -14.2), (15.2, 14.2)):
        if far:
            k.oct(cx, cz, 4.2, 4.2, 0.2, top - 0.5, "green", ch=0)
            continue
        for y0 in range(0, 42, 7):
            y1 = min(y0 + 7, top - 0.6)
            k.oct(cx, cz, 4.2, 4.2, y0 + 0.2, y1 - 0.7, "green", cut=0.29)
            k.oct(cx, cz, 3.7, 3.7, y1 - 0.7, y1, "green_d", cut=0.29, ch=0.2)
        for a in (0, 90, 180, 270):  # рёбра колонны
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            ex, ez = cx + ca * 4.4, cz + sa * 4.4
            k.box(ex - 0.6 - abs(sa) * 0.0, ex + 0.6, 1.0, top - 2.0, ez - 0.6, ez + 0.6, "green2", ch=0.35)
    if far:
        k.box(-11, -2.5, 25, 38, -19.6, -16.6, "glove", ch=0)
        return
    for base, dirv in (((-19.6, 12.0, -14.2), (-1, 0.25, 0)), ((-15.2, 22.0, -18.6), (0, 0.25, -1)),
                       ((15.2, 30.0, 18.6), (0, 0.25, 1)), ((19.6, 16.0, 14.2), (1, 0.25, 0))):
        k.spike(base, dirv, 1.2, 2.6, "spine")
    k.face(-15.2, 33.5, -18.45, 0.62, mood="fight")
    k.box(-11.0, -4.0, 25.0, 28.0, -19.4, -16.7, "green", ch=0.5)
    k.box(-5.6, -2.6, 25.0, 32.6, -19.4, -16.7, "green", ch=0.5)
    k.glove(-4.1, 32.6, -18.0, 0.9)
    for c in ((-15.2, top - 1.0, -14.2), (15.2, top - 1.0, 14.2)):
        k.flower(*c, s=0.9)


def mythic_camel(k, far=False):
    top = band_top(5)
    if far:
        for sx in (-1, 1):
            k.oct(sx * 15.0, -14.0, 3.0, 3.0, 0.2, 19.0, "tan_d", ch=0)
            k.box(sx * 18.12, sx * 22.0, 26, 40, -8, 8, "glassq", ch=0)
        k.box(-5, 5, 28, 38, -21.9, -17, "tan", ch=0)
        return
    for sx in (-1, 1):  # передние ноги-опоры
        k.oct(sx * 15.0, -14.0, 3.0, 3.0, 1.6, 19.0, "tan_d", cut=0.3)
        k.oct(sx * 15.0, -14.0, 3.3, 3.3, 0.2, 1.6, "hoof", cut=0.3, ch=0.25)
    # голова вырывается из фасада второго яруса
    k.box(-3.2, 3.2, 27.5, 34.0, -19.4, -17.0, "tan", ch=0.6)
    k.box(-5.0, 5.0, 29.0, 37.4, -20.6, -17.0, "tan", ch=0.8)
    k.box(-3.8, 3.8, 28.4, 32.4, -21.9, -19.6, "tan_l", ch=0.6)
    for d in (-1, 1):
        k.box(d * 4.3 - 0.7, d * 4.3 + 0.7, 36.4, 39.2, -18.8, -17.2, "tan_d", ch=0.3)
        ex = d * 2.4
        k.box(ex - 1.2, ex + 1.2, 33.4, 35.8, -21.15, -20.6, "white", ch=0.12)
        k.box(ex - 0.45 - d * 0.25, ex + 0.45 - d * 0.25, 33.7, 34.8, -21.4, -21.1, "black", ch=0.05)
        for j in (-1, 0, 1):
            k.rbox(ex + j * 0.75, 36.15, -20.9, 0.3, 0.85, 0.35, "black", rot=-j * 18, ch=0.04)
        k.box(d * 1.2 - 0.4, d * 1.2 + 0.4, 31.0, 31.7, -22.1, -21.85, "hoof", ch=0.04)
    for x0, x1, y0 in ((-2.1, -1.0, 29.4), (-1.0, 1.0, 29.0), (1.0, 2.1, 29.4)):
        k.box(x0, x1, y0, y0 + 0.45, -22.1, -21.85, "hoof", ch=0.04)
    # горбы-аквариумы выпирают из боковых стен ступенями
    for sx in (-1, 1):
        for x0, x1, rz, ry in ((0.0, 1.2, 8.0, 6.2), (1.2, 2.4, 7.0, 5.4), (2.4, 3.4, 5.6, 4.2), (3.4, 4.2, 3.8, 2.8)):
            poly = [(z, y) for z, y in ((-rz * 0.7, 33 - ry), (rz * 0.7, 33 - ry), (rz, 33 - ry * 0.6), (rz, 33 + ry * 0.6),
                                        (rz * 0.7, 33 + ry), (-rz * 0.7, 33 + ry), (-rz, 33 + ry * 0.6), (-rz, 33 - ry * 0.6))]
            a, b = sx * (18.12 + x0), sx * (18.12 + x1)
            k.prism(poly, min(a, b), max(a, b), "glassq", ch=0.25, axis="x")
        for j, (fy, fz) in enumerate(((31.0, -3.0), (35.0, 2.5))):
            k.fish(sx * 19.8, fy, fz, 0.8, face_x=-sx)


# ══ сборка темы ═══════════════════════════════════════════════════════════════════════════════════════════════
def tris(objs):
    n = 0
    for o in objs:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            n += len(o.data.loop_triangles)
    return n


def import_resident(theme, coll, at, height):
    """Готовая модель существа из коллекции (FBX + цветовая карта), лицом к стеклу атриума."""
    name = "CactusBoxer" if theme == "saloon" else "AquariumCamel"
    path = os.path.join(REPO, "assets", "models", "art", "boss4", name + ".fbx")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    img = bpy.data.images.load(os.path.join(REPO, "assets", "textures", "art", "boss4", name + "_color.png"))
    m = bpy.data.materials.new(name + "_Res")
    m.use_nodes = True
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = img
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    root = bpy.data.objects.new("Resident_" + name, None)
    coll.objects.link(root)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
        if o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(m)
        if o.parent is None:
            o.parent = root
    bpy.context.view_layer.update()
    zs = [(o.matrix_world @ Vector(c)).z for o in new if o.type == "MESH" for c in o.bound_box]
    s = height / max(1e-6, max(zs) - min(zs))
    root.scale = (s, s, s)
    root.rotation_euler = (0, 0, math.radians(0 if theme == "saloon" else -35))  # лицом к стеклу атриума
    root.location = K.P(*at)
    bpy.context.view_layer.update()
    zs = [(o.matrix_world @ Vector(c)).z for o in new if o.type == "MESH" for c in o.bound_box]
    root.location.z += at[1] - min(zs)
    return [o for o in new if o.type == "MESH"]


def theme_build(theme):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(V3, theme + "_base.blend"))
    scene = bpy.context.scene
    pre = "CB" if theme == "saloon" else "AQ"
    base = [o for o in bpy.data.objects if o.name.startswith((pre + "_F_", pre + "_I_"))]
    base_coll = base[0].users_collection[0]
    T = {t: list(bpy.data.collections["T%d" % t].objects) for t in range(1, 7)}

    def mk(name, objs=()):
        c = bpy.data.collections.new(name)
        scene.collection.children.link(c)
        for o in objs:
            c.objects.link(o)
        return c

    def matk(o):
        return o.data.materials[0].name if (o.type == "MESH" and o.data.materials) else ""

    nums = {}
    for t in (1, 2, 3):
        mk("Q%d" % t, T[t])
    # Золотой: атриум (v3) + готовый жилец + свет
    Q4 = mk("Q4", T[4])
    res = import_resident(theme, Q4, (0.0, 19.3, -Z + (5.0 if theme == "saloon" else 6.0)), 12.0)
    nums["resident_tris"] = tris(res)
    lamp = bpy.data.objects.new("AtriumLight", bpy.data.lights.new("AtriumLight", "POINT"))
    lamp.data.energy, lamp.data.color = 2600, (1.0, 0.92, 0.8)
    lamp.location = K.P(0, 31, -Z + 2.5)
    Q4.objects.link(lamp)
    # Мифический: D39 без «геройского» знака + существо сквозь здание
    sign = (0.0, 19.0 + (45 - 2.6 - 19.0) / 3 + 0.5 + 2.3 * 2.3, -Z - 2.5)
    keep5 = [o for o in T[5] if not (matk(o).startswith(("R_glove", "R_cuff", "R_trim", "R_fish", "R_fin", "R_eye",
                                                         "R_black"))
                                     and (o.matrix_world.translation - K.P(*sign)).length < 9.5)]
    Q5 = mk("Q5", keep5)
    k5 = Kit(Q5)
    (mythic_saloon if theme == "saloon" else mythic_camel)(k5)
    nums["mythic_tris"] = tris(k5.objs)
    # Космический: существо-дом целиком; плиты во весь след и кант — из v3
    crisp6 = [o for o in T[6] if (matk(o).startswith("R_slab") and o.dimensions.x > 35 and o.dimensions.y > 33)
              or matk(o).startswith("R_k_") or (matk(o)[:3] == "R_r" and matk(o)[3:4].isdigit())]
    Q6 = mk("Q6", crisp6)
    k6 = Kit(Q6)
    (cosmic_saloon if theme == "saloon" else cosmic_camel)(k6)
    nums["cosmic_tris"] = tris(k6.objs)
    # дальние версии (в кадр не идут)
    farc = mk("Far")
    kf = Kit(farc)
    (cosmic_saloon if theme == "saloon" else cosmic_camel)(kf, far=True)
    nums["cosmic_far"] = tris(kf.objs) + tris(crisp6)
    kf2 = Kit(farc)
    (mythic_saloon if theme == "saloon" else mythic_camel)(kf2, far=True)
    nums["mythic_far"] = tris(kf2.objs)
    farc.hide_render = True
    for c in list(scene.collection.children):
        if c.name.startswith("T") and c.name[1:].isdigit():
            c.hide_render = True
    bpy.context.view_layer.update()
    for t, objs, with_base in ((5, k5.objs + keep5, True), (6, k6.objs + crisp6, False)):
        allo = objs + (base if with_base else [])
        top = max((o.matrix_world @ Vector(c)).z for o in allo if o.type == "MESH" for c in o.bound_box
                  if abs(c[0]) < 29.5 and abs(c[1]) < 29.5)
        lo = Vector((1e9,) * 3)
        hi = Vector((-1e9,) * 3)
        for o in (k5.objs if t == 5 else k6.objs):
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                lo, hi = Vector(map(min, lo, w)), Vector(map(max, hi, w))
        side, front = max(hi.x, -lo.x) - X, -lo.y - Z
        nums["check_%d" % t] = [round(top, 2), H[t - 1] - 1, round(side, 2), round(front, 2)]
        print("CHECK_TOP %s %s %s: верх %.2f ≤ %d; вынос существа вбок %.1f, вперёд %.1f" % (
            "OK" if top <= H[t - 1] - 1 + 1e-3 else "FAIL", theme, NAMES[t - 1], top, H[t - 1] - 1, side, front),
            flush=True)
    print("NUMS", json.dumps(nums), flush=True)
    json.dump(nums, open(os.path.join(OUT, theme + "_v4_numbers.json"), "w"))
    cam = scene.camera
    scene.render.resolution_x, scene.render.resolution_y = 900, 1100

    def aim(eye, target, fov):
        cam.data.angle_y = math.radians(fov)
        e, t_ = K.P(*eye), K.P(*target)
        cam.location = e
        cam.rotation_euler = (e - t_).to_track_quat("Z", "Y").to_euler()

    def show(name, with_base):
        for c in scene.collection.children:
            if c.name.startswith(("Q", "Far")):
                c.hide_render = c.name != name
        base_coll.hide_render = not with_base

    def render(n):
        scene.render.filepath = os.path.join(OUT, "%s_%s.png" % (theme, n))
        bpy.ops.render.render(write_still=True)
        print("SHOT", n, flush=True)

    aim((-104, 40, -118), (0, 27, -2), 36)
    show("Q5", True)
    render("v4_5")
    show("Q6", False)
    render("v4_6")
    aim((-26, 44, -64), (0, 36, -14), 44)
    render("v4_6_close")
    show("Q5", True)
    aim((-30, 34, -56), (-6, 28, -16), 44)
    render("v4_5_close")
    show("Q4", True)
    aim((-10, 27, -42), (0, 25.5, -14), 40)
    render("v4_4_atrium")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, theme + "_v4.blend"))
    print("DONE_THEME", flush=True)


# ══ башня 1-6-3-5-2-4 (v4) ════════════════════════════════════════════════════════════════════════════════════
def tower():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "saloon_v4.blend"))
    scene = bpy.context.scene
    cb = [o for o in bpy.data.objects if o.name.startswith(("CB_F_", "CB_I_"))]
    with bpy.data.libraries.load(os.path.join(OUT, "aquarium_v4.blend")) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(("AQ_F_", "AQ_I_"))]
        dst.collections = ["Q1", "Q3", "Q4"]
    aq = [o for o in dst.objects if o is not None]
    aqc = {k: list(c.all_objects) for k, c in zip(("Q1", "Q3", "Q4"), dst.collections)}
    sc = {k: list(bpy.data.collections[k].objects) for k in ("Q2", "Q5", "Q6")}
    for c in scene.collection.children:
        c.hide_render = True
    TX = 400.0
    order = [(1, aqc["Q1"], aq), (6, sc["Q6"], []), (3, aqc["Q3"], aq), (5, sc["Q5"], cb), (2, sc["Q2"], cb),
             (4, aqc["Q4"], aq)]
    tw = bpy.data.collections.new("Tower")
    scene.collection.children.link(tw)
    y = 0.0
    yfl = {}
    for t, over, base in order:
        oy = y + 1.0
        made = {}
        for o in over + base:
            c = o.copy()
            tw.objects.link(c)
            made[o] = c
        for o, c in made.items():  # иерархия жильца: копии детей — к копии корня
            if o.parent in made:
                c.parent = made[o.parent]
            elif o.parent is None:
                c.location = o.location + Vector((-TX, 0, oy))
        bpy.context.view_layer.update()
        top = max((c.matrix_world @ Vector(cc)).z for c in made.values() if c.type == "MESH" for cc in c.bound_box
                  if abs(cc[0]) < 29.5 and abs(cc[1]) < 29.5) - oy
        print("CHECK_TOP %s башня %s: верх %.2f ≤ %d" % ("OK" if top <= H[t - 1] - 1 + 1e-3 else "FAIL", NAMES[t - 1],
                                                        top, H[t - 1] - 1), flush=True)
        yfl[t] = y
        y += H[t - 1]
    ry = y
    k = Kit(tw)
    k.box(-X + 1 + TX * -1 * 0 - 0, X - 1, ry, ry + 1.5, -Z + 1, Z - 1, "green2", ch=0.3)  # колпак C (как в v3)
    for o in k.objs:
        o.location.x -= TX
    cap = Kit(tw)
    cap.oct(-TX * -1 * 0 + 0, 0, 9.5, 9.5, ry + 1.5, ry + 4.5, "glow", ch=0.3)
    cap.oct(0, 0, 8.5, 8.5, ry + 4.5, ry + 19.0, "aqua", cut=0.5, ch=0.3)
    for o in cap.objs:
        o.location.x -= TX
    tw.hide_render = False
    cam = scene.camera

    def aim(eye, target, fov, w, h):
        scene.render.resolution_x, scene.render.resolution_y = w, h
        cam.data.angle_y = math.radians(fov)
        e, t_ = K.P(eye[0] + TX, eye[1], eye[2]), K.P(target[0] + TX, target[1], target[2])
        cam.location = e
        cam.rotation_euler = (e - t_).to_track_quat("Z", "Y").to_euler()

    def render(n):
        scene.render.filepath = os.path.join(OUT, "tower_%s.png" % n)
        bpy.ops.render.render(write_still=True)
        print("SHOT", n, flush=True)

    mid = ry / 2 + 10
    aim((-230, mid + 70, -270), (0, mid + 14, 0), 52, 900, 1600)
    render("full")
    y6 = yfl[6] + 30
    aim((-14, y6 + 4, -60 - Z), (0, y6, -Z), 64, 1200, 900)
    render("60_cosmic")
    y5 = yfl[5] + 24
    aim((-14, y5 + 4, -60 - Z), (0, y5, -Z), 64, 1200, 900)
    render("60_mythic")
    print("TOWER_HEIGHT", ry, "DONE_TOWER", flush=True)


if MODE == "tower":
    tower()
else:
    theme_build(MODE)

"""Набор мешей для эталонной модели Короля-дракона (босс 10): свои сетки вместо стопок кубов.

Основа — лофт сечений вдоль изогнутых осей (сплайн Катмулла — Рома): каждое сечение — «суперэллипс» с заданной
квадратностью, поэтому формы гранёные и ступенчатые (стиль D39), но с анатомией и сужениями. Плюс ступенчатые купола
(наплечники, наколенники), оболочки брони по поверхности тела, пластины, камни в оправе, перепонки с прогибом.
Все объекты — с началом координат в нуле мира (повороты кадров вращают модель целиком). Плоское затенение.
Зависит только от bpy/bmesh/mathutils.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

V = Vector


def superellipse(n, w, h, p=2.6, top=1.0, bottom=1.0, phase=None):
    """Сечение (x, z): полуоси w и h, квадратность p (2 — эллипс, больше — квадратнее), top/bottom — верх и низ."""
    phase = math.pi / n if phase is None else phase
    pts = []
    for i in range(n):
        t = phase + 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        x = w * math.copysign(abs(c) ** (2 / p), c)
        z = h * math.copysign(abs(s) ** (2 / p), s)
        pts.append((x, z * (top if z > 0 else bottom)))
    return pts


def spline(pts, n):
    """Катмулл — Ром через точки pts, n равномерных по параметру отсчётов."""
    P = [V(p) for p in pts]
    P = [P[0]] + P + [P[-1]]
    segs = len(pts) - 1
    out = []
    for i in range(n):
        t = i / (n - 1) * segs
        k = min(int(t), segs - 1)
        u = t - k
        p0, p1, p2, p3 = P[k], P[k + 1], P[k + 2], P[k + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return out


def frames(pts, up=(0, 0, 1)):
    """Для каждой точки пути: (центр, вправо, вверх). Профиль (x, z) → центр + вправо·x + вверх·z."""
    up = V(up)
    out = []
    for i, p in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        f = (b - a).normalized()
        r = f.cross(up)
        if r.length < 1e-5:
            r = f.cross(V((0, 1, 0)))
        r.normalize()
        out.append((p, r, r.cross(f).normalized()))
    return out


def basis(origin, normal, up=(0, 0, 1)):
    """Матрица: локальная −Y смотрит по normal (наружу), Z — вверх, X — вправо. Плоские детали лежат в XZ."""
    n = V(normal).normalized()
    z = V(up) - n * V(up).dot(n)
    if z.length < 1e-5:
        z = V((0, 1, 0)) - n * n.y
    z.normalize()
    y = -n
    x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = V(origin)
    return m


class Mesh:
    """Одна подвижная часть (будущий MeshPart): bmesh + список материалов по ключам."""

    gem_n = 8  # граней у камней (игровая копия — меньше)

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.keys = []

    def mi(self, key):
        if key not in self.keys:
            self.keys.append(key)
        return self.keys.index(key)

    # ── базовые построения ──────────────────────────────────────────────────────────────────────────
    def rings(self, key, rings, cap0=True, cap1=True, closed=False):
        """Лофт через кольца одинаковой длины. closed — путь замкнут (кольцо вокруг шеи, обод короны)."""
        bm = self.bm
        vs = [[bm.verts.new(V(p)) for p in ring] for ring in rings]
        n = len(rings[0])
        faces = []
        pairs = list(zip(vs, vs[1:])) + ([(vs[-1], vs[0])] if closed else [])
        for a, b in pairs:
            for j in range(n):
                faces.append(bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j])))
        if not closed:
            if cap0:
                faces.append(bm.faces.new(list(reversed(vs[0]))))
            if cap1:
                faces.append(bm.faces.new(vs[-1]))
        idx = self.mi(key)
        for f in faces:
            f.material_index = idx
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        return faces

    def tube(self, key, pts, prof, up=(0, 0, 1), samples=None, cap0=True, cap1=True, closed=False):
        """Труба вдоль пути: prof(t) → точки сечения (x, z), t от 0 до 1 по пути."""
        P = spline(pts, samples) if samples else [V(p) for p in pts]
        fr = frames(P + ([P[0]] if closed else []), up)[: len(P)]
        rings = []
        for i, (c, r, u) in enumerate(fr):
            t = i / max(len(P) - 1, 1)
            rings.append([c + r * x + u * z for x, z in prof(t)])
        return self.rings(key, rings, cap0, cap1, closed)

    def flat(self, key, pts2d, depth, m, back=0.0):
        """Плоская деталь: многоугольник (u, v) в плоскости XZ матрицы m, толщина от −back до depth наружу."""
        bm = self.bm
        lo = [bm.verts.new(m @ V((u, back, v))) for u, v in pts2d]
        hi = [bm.verts.new(m @ V((u, -depth, v))) for u, v in pts2d]
        faces = [bm.faces.new(lo), bm.faces.new(list(reversed(hi)))]
        n = len(pts2d)
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((lo[i], lo[j], hi[j], hi[i])))
        idx = self.mi(key)
        for f in faces:
            f.material_index = idx
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        res = bmesh.ops.connect_verts_concave(bm, faces=[f for f in faces if len(f.verts) > 4])
        for f in res.get("faces", []):
            f.material_index = idx
        return faces

    def dome(self, key, center, axis, radii, step, n=12, p=2.4, lip=0.92, keys=None):
        """Ступенчатый купол вдоль axis: ярусы радиусов radii, высота яруса step (наплечник, наколенник, шлем)."""
        c, a = V(center), V(axis).normalized()
        ref = V((0, 0, 1)) if abs(a.z) < 0.9 else V((0, 1, 0))
        x = a.cross(ref).normalized()
        y = a.cross(x).normalized()

        def ring(r, h):
            return [c + a * h + x * px + y * pz for px, pz in superellipse(n, r, r, p)]

        rings, h = [], 0.0
        for k, r in enumerate(radii):
            rings.append(ring(r, h))
            rings.append(ring(r * lip, h + step))
            h += step
        faces = self.rings(key, rings)
        if keys:  # чередование цветов ярусов
            per = n * 2
            for k in range(len(radii)):
                for f in faces[k * per: k * per + n]:
                    f.material_index = self.mi(keys[k % len(keys)])
        return faces

    def gem(self, key, center, normal, size, n=None, up=(0, 0, 1), bezel=None):
        """Огранённый камень наружу по normal; bezel — ключ оправы-кольца."""
        n = n or self.gem_n
        m = basis(center, normal, up)
        prof = [(math.cos(2 * math.pi * i / n + math.pi / n), math.sin(2 * math.pi * i / n + math.pi / n))
                for i in range(n)]

        def ring(r, d):
            return [m @ V((r * u, -d, r * v)) for u, v in prof]

        self.rings(key, [ring(size * 0.05, -size * 0.35), ring(size, 0.0), ring(size * 0.95, size * 0.12),
                         ring(size * 0.6, size * 0.32)])
        if bezel:
            self.rings(bezel, [ring(size * 1.0, -0.02), ring(size * 1.28, -0.02), ring(size * 1.28, size * 0.12),
                               ring(size * 1.06, size * 0.14)], cap0=False, cap1=False)

    def ball(self, key, center, r, n=8, rows=5, sz=1.0):
        c = V(center)
        rings = []
        for k in range(1, rows):
            phi = math.pi * k / rows - math.pi / 2
            rr, zz = r * math.cos(phi), r * math.sin(phi) * sz
            rings.append([c + V((rr * math.cos(2 * math.pi * i / n + math.pi / n),
                                 rr * math.sin(2 * math.pi * i / n + math.pi / n), zz)) for i in range(n)])
        return self.rings(key, rings)

    def membrane(self, key, loop, billow, thick, normal_hint):
        """Перепонка: веер от центра петли loop, центр выгнут на billow по нормали; толщина thick (две стороны)."""
        bm = self.bm
        L = [V(p) for p in loop]
        c = sum(L, V()) / len(L)
        nrm = V(normal_hint).normalized()
        front_c = bm.verts.new(c + nrm * billow)
        back_c = bm.verts.new(c + nrm * (billow - thick))
        fv = [bm.verts.new(p) for p in L]
        bv = [bm.verts.new(p - nrm * thick) for p in L]
        faces = []
        n = len(L)
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((front_c, fv[i], fv[j])))
            faces.append(bm.faces.new((back_c, bv[j], bv[i])))
            faces.append(bm.faces.new((fv[i], bv[i], bv[j], fv[j])))
        idx = self.mi(key)
        for f in faces:
            f.material_index = idx
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        return faces

    # ── отделка ─────────────────────────────────────────────────────────────────────────────────────
    def contour(self, faces, rim_key, thickness=0.05, depth=0.015):
        """Контур D39 по краю пластины: вдавленная кромка вокруг группы граней (не сетка по всей модели)."""
        faces = [f for f in faces if f.is_valid]
        if not faces:
            return
        res = bmesh.ops.inset_region(self.bm, faces=faces, thickness=thickness, depth=-depth, use_even_offset=True)
        idx = self.mi(rim_key)
        for f in res["faces"]:
            f.material_index = idx

    def tris(self):
        return sum(len(f.verts) - 2 for f in self.bm.faces)

    def build(self, collection, materials):
        me = bpy.data.meshes.new(self.name)
        self.bm.normal_update()
        self.bm.to_mesh(me)
        for p in me.polygons:
            p.use_smooth = False
        for k in self.keys:
            me.materials.append(materials[k])
        ob = bpy.data.objects.new(self.name, me)
        collection.objects.link(ob)
        return ob


def mirror_x(pts):
    return [V((-p[0], p[1], p[2])) for p in pts]

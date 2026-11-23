"""Набор для архитектуры этажей музея-небоскрёба из мешей (стиль D39): тела с острыми рёбрами и фаской, рамы,
плоскости с проёмами, огранённые камни; затенение (окклюзия по сетке вершин grid, яркость сторон блока и зон —
shade_parts) и оттенки — в цветах вершин, цвет детали в игре —
Color у MeshPart (палитра настраивается в Studio без повторной загрузки), контурные квадраты — MaterialVariant
LegoSquaresItem (ложится на MeshPart своей проекцией, BUGS.md). Проверено загрузкой 2026-11-19: цвета вершин из FBX
через Open Cloud доходят до MeshPart и умножаются на Color.

Координаты этажа (как в Floors/Kit): X вправо, Y вверх, пол на Y = 0, фасад смотрит в −Z, лифт у +Z.
Blender: точка этажа (X, Y, Z) → (−X, Z, Y); после загрузки меш в Roblox стоит в осях этажа без поворота
(импорт поворачивает меш на 180° вокруг вертикали, BUGS.md), точка опоры MeshPart — центр габаритов.
Зависит только от Blender (bpy, bmesh, mathutils).
"""

import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SQ2 = 2 - math.sqrt(2)  # смещение среза восьмиугольника при параллельном отступе


def rgb(code):
    return tuple(int(code[i : i + 2], 16) / 255 for i in (0, 2, 4))


def tone(v):
    """Оттенок грани: число (серый множитель) или hex-цвет."""
    if isinstance(v, str):
        return rgb(v)
    if isinstance(v, (int, float)):
        return (v, v, v)
    return tuple(v)


def P(x, y, z):
    return Vector((-x, z, y))


def rect(a0, a1, b0, b1):
    return [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]


def octa(cx, cy, hw, hh, cut):
    """Восьмиугольник: прямоугольник 2hw × 2hh со срезанными углами (катет cut)."""
    return [(cx - hw + cut, cy - hh), (cx + hw - cut, cy - hh), (cx + hw, cy - hh + cut), (cx + hw, cy + hh - cut),
            (cx + hw - cut, cy + hh), (cx - hw + cut, cy + hh), (cx - hw, cy + hh - cut), (cx - hw, cy - hh + cut)]


def octa_in(cx, cy, hw, hh, cut, d):
    """Тот же восьмиугольник с параллельным отступом внутрь на d."""
    return octa(cx, cy, hw - d, hh - d, max(cut - d * SQ2, 0.02))


def ngon(cx, cy, r, n=8, turn=0.5):
    return [(cx + r * math.cos(2 * math.pi * (k + turn) / n), cy + r * math.sin(2 * math.pi * (k + turn) / n))
            for k in range(n)]


def xy(pts, z):
    return [P(x, y, z) for x, y in pts]


def xz(pts, y):
    return [P(x, y, z) for x, z in pts]


def zy(pts, x):
    return [P(x, y, z) for z, y in pts]


def _bevel(bm, bevel):
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, offset_type="OFFSET", segments=1, profile=0.5,
                        affect="EDGES", clamp_overlap=True)


def _solid(a, b, bevel):
    bm = bmesh.new()
    va = [bm.verts.new(p) for p in a]
    vb = [bm.verts.new(p) for p in b]
    n = len(va)
    bm.faces.new(va)
    bm.faces.new(vb)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((va[i], va[j], vb[j], vb[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _bevel(bm, bevel)
    return bm


def _cone(a, apex, bevel):
    bm = bmesh.new()
    va = [bm.verts.new(p) for p in a]
    top = bm.verts.new(apex)
    n = len(va)
    bm.faces.new(va)
    for i in range(n):
        bm.faces.new((va[i], va[(i + 1) % n], top))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _bevel(bm, bevel)
    return bm


def _frame(ob, ot, ib, it, bevel):
    bm = bmesh.new()
    vob, vot = [bm.verts.new(p) for p in ob], [bm.verts.new(p) for p in ot]
    vib, vit = [bm.verts.new(p) for p in ib], [bm.verts.new(p) for p in it]
    n = len(vob)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vob[i], vob[j], vib[j], vib[i]))
        bm.faces.new((vot[i], vot[j], vit[j], vit[i]))
        bm.faces.new((vob[i], vob[j], vot[j], vot[i]))
        bm.faces.new((vib[i], vib[j], vit[j], vit[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _bevel(bm, bevel)
    return bm


def refine(bm, limit):
    """Дробит длинные рёбра (сетка без T-стыков): затенение в вершинах получает точки на больших гранях."""
    for _ in range(10):
        long = [e for e in bm.edges if e.calc_length() > limit]
        if long:
            bmesh.ops.subdivide_edges(bm, edges=long, cuts=1, use_grid_fill=True)
        big = [f for f in bm.faces if len(f.verts) > 4]
        if big:
            bmesh.ops.triangulate(bm, faces=big)
        if not long and not big:
            break


def grid_cut(bm, step):
    """Режет весь меш плоскостями через step стадов по трём осям: у каждой грани появляются вершины внутри, и
    затенение в цветах вершин ложится тенью у стыков и под выступами, а не одной заливкой на грань (BUGS.md)."""
    for axis in (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))):
        vals = [v.co.dot(axis) for v in bm.verts]
        lo, hi = min(vals), max(vals)
        k = math.ceil(lo / step) * step
        while k < hi - 1e-3:
            if k > lo + 1e-3:
                bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-4, plane_co=axis * k,
                                       plane_no=axis, clear_inner=False, clear_outer=False)
            k += step


ARCH_MIN, ARCH_THICK, PROP_THICK, PROP_MID = 8.0, 0.4, 0.5, 0.9  # габариты разводки тел (стады)
FORCE_THICK, FORCE_MID = 0.25, 0.6  # явно отмеченные вещи (force): тоньше — гладкие накладки, как у предметов (0.25: пластины 0.3 с погрешностью — тоже вещь)


class Part:
    """Один MeshPart: копит тела с оттенками граней. material: tile | smooth | glass | neon.
    grid — шаг сетки вершин под затенение (0 — прежнее дробление длинных рёбер по limit);
    partner и narrow — узкие грани (уже narrow стадов) уходят в деталь partner: квадраты D39 остаются только на
    крупных поверхностях, кромки, рамы и торцы — гладкие, как мелкие накладки у предметов."""

    def __init__(self, name, tier, material, tint, shade=(0.5, 0.5, 0.5), ao=1.0, limit=3.0, occlude=True, grid=0.0,
                 partner=None, narrow=0.0, adapt=False, bevel=0.0, bevel_min=0.5):
        self.name, self.tier, self.material, self.tint = name, tier, material, tint
        self.shade, self.ao, self.limit, self.occlude = shade, ao, limit, occlude
        self.grid, self.partner, self.narrow = grid, partner, narrow
        self.adapt, self.gave = adapt, False  # adapt — сетку под затенение кладёт adaptive_cut (только где нужна)
        # bevel — фаска рёбер по умолчанию у box и рам (скруглённое ребро бруска, как на референсе); тела тоньше
        # bevel_min — без фаски (накладки, кромки)
        self.bevel, self.bevel_min = bevel, bevel_min
        self.bm = bmesh.new()
        self.bm.loops.layers.float_color.new("tone")
        self.bm.faces.layers.int.new("wide")
        self.obj = None
        # Разводка тел гладкой детали (этажи, 2026-11-21): крупные объекты (статуи, звери, мебель, машины) — в деталь
        # route_props (квадраты-контуры D39 в масштабе босса), крупные части здания — в route_arch (квадраты этажа);
        # тонкие накладки и мелочь остаются гладкими. noroute — тело уже разведено вызывающим (slab, chamfer).
        self.route_props, self.route_arch, self.noroute = None, None, 0
        # force — деталь, куда идут все тела, пока скрипт этажа отметил участок как вещи (утверждённые этажи: только
        # явная разметка, архитектура не меняется)
        self.force = None

    def route(self, tmp):
        """Куда положить тело: self, route_props или route_arch (по габаритам тела)."""
        if self.noroute or (self.route_props is None and self.force is None) or not tmp.verts:
            return self
        lo = [min(v.co[i] for v in tmp.verts) for i in range(3)]
        hi = [max(v.co[i] for v in tmp.verts) for i in range(3)]
        e = sorted(hi[i] - lo[i] for i in range(3))
        if self.force is not None:
            return self.force if e[0] >= FORCE_THICK and e[1] >= FORCE_MID else self
        if e[2] >= ARCH_MIN and e[0] >= ARCH_THICK:  # часть здания: на квадраты этажа или, без route_arch, гладкая
            return self.route_arch if self.route_arch is not None else self
        if e[0] >= PROP_THICK and e[1] >= PROP_MID:
            return self.route_props
        return self

    def take(self, tmp, t):
        dst = self.route(tmp)
        if dst is not self:
            dst.take(tmp, t)
            return
        layer = tmp.loops.layers.float_color.get("tone") or tmp.loops.layers.float_color.new("tone")
        c = (*tone(t), 1.0)
        for f in tmp.faces:
            for loop in f.loops:
                loop[layer] = c
        me = bpy.data.meshes.new("tmp")
        tmp.to_mesh(me)
        tmp.free()
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    # тела в координатах этажа
    def box(self, x0, x1, y0, y1, z0, z1, t=1.0, bevel=0.0):
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        z0, z1 = sorted((z0, z1))
        if not bevel and min(x1 - x0, y1 - y0, z1 - z0) >= self.bevel_min:
            bevel = self.bevel
        self.take(_solid(xz(rect(x0, x1, z0, z1), y0), xz(rect(x0, x1, z0, z1), y1), bevel), t)

    def prism_xy(self, pts, z0, z1, t=1.0, bevel=0.0):
        self.take(_solid(xy(pts, z0), xy(pts, z1), bevel), t)

    def prism_xz(self, pts, y0, y1, t=1.0, bevel=0.0):
        self.take(_solid(xz(pts, y0), xz(pts, y1), bevel), t)

    def prism_zy(self, pts, x0, x1, t=1.0, bevel=0.0):
        self.take(_solid(zy(pts, x0), zy(pts, x1), bevel), t)

    def loft(self, a, b, t=1.0, bevel=0.0):
        """Тело между двумя кольцами точек этажа [(x, y, z), …] одинаковой длины."""
        self.take(_solid([P(*p) for p in a], [P(*p) for p in b], bevel), t)

    def cone(self, a, apex, t=1.0, bevel=0.0):
        self.take(_cone([P(*p) for p in a], P(*apex), bevel), t)

    def _frame_bevel(self, bevel, a0, a1):
        return bevel or (self.bevel if abs(a1 - a0) >= self.bevel_min else 0.0)

    def frame_xy(self, outer, inner, z0, z1, t=1.0, bevel=0.0):
        bevel = self._frame_bevel(bevel, z0, z1)
        self.take(_frame(xy(outer, z0), xy(outer, z1), xy(inner, z0), xy(inner, z1), bevel), t)

    def frame_xz(self, outer, inner, y0, y1, t=1.0, bevel=0.0):
        bevel = self._frame_bevel(bevel, y0, y1)
        self.take(_frame(xz(outer, y0), xz(outer, y1), xz(inner, y0), xz(inner, y1), bevel), t)

    def frame_zy(self, outer, inner, x0, x1, t=1.0, bevel=0.0):
        self.take(_frame(zy(outer, x0), zy(outer, x1), zy(inner, x0), zy(inner, x1), bevel), t)

    def plane(self, outer, holes, normal, t=1.0, grid=2.0):
        """Плоская грань с проёмами: outer и holes — кольца точек этажа [(x, y, z)], normal — куда смотрит (этаж)."""
        bm = bmesh.new()
        edges = []
        for ring in [outer] + list(holes):
            vs = [bm.verts.new(P(*p)) for p in ring]
            for i in range(len(vs)):
                edges.append(bm.edges.new((vs[i], vs[(i + 1) % len(vs)])))
        nb = Vector((-normal[0], normal[2], normal[1]))
        bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges, normal=nb)
        # регулярная сетка: разрезы через grid стадов по обеим осям плоскости (затенение в вершинах ложится
        # ровно, без «пилы» по длинным треугольникам)
        nb.normalize()
        ua = Vector((0, 0, 1)) if abs(nb.z) < 0.9 else Vector((1, 0, 0))
        ua = (ua - nb * ua.dot(nb)).normalized()
        va = nb.cross(ua)
        if self.adapt:  # одна грань на стену: её режет adaptive_cut
            bmesh.ops.dissolve_limit(bm, angle_limit=0.01, verts=bm.verts[:], edges=bm.edges[:])
        for axis in (ua, va) if self.grid <= 0 and not self.adapt else ():  # при общей сетке плоскость режется в finish
            vals = [v.co.dot(axis) for v in bm.verts]
            lo, hi = min(vals), max(vals)
            k = math.ceil(lo / grid) * grid
            while k < hi - 1e-4:
                if k > lo + 1e-4:
                    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5, plane_co=axis * k,
                                           plane_no=axis, clear_inner=False, clear_outer=False)
                k += grid
        bm.normal_update()
        for f in bm.faces:
            if f.normal.dot(nb) < 0:
                f.normal_flip()
        wide = bm.faces.layers.int.new("wide")  # плоскость стены всегда крупная: её треугольники не «узкие грани»
        for f in bm.faces:
            f[wide] = 1
        self.take(bm, t)

    def gem_xy(self, girdle, table, z_girdle, z_table, tones, cap=True):
        """Огранка камня: грани от пояска (girdle) к площадке (table), у каждой грани свой оттенок."""
        n = len(girdle)
        g, tb = xy(girdle, z_girdle), xy(table, z_table)
        out = Vector((0, -1, 0)) if z_table < z_girdle else Vector((0, 1, 0))  # наружу по оси Z этажа
        for i in range(n + 1 if cap else n):
            bm = bmesh.new()
            if i < n:
                j = (i + 1) % n
                f = bm.faces.new([bm.verts.new(p) for p in (g[i], g[j], tb[j], tb[i])])
            else:
                f = bm.faces.new([bm.verts.new(p) for p in tb])
            bm.normal_update()
            if f.normal.dot(out) < 0:
                f.normal_flip()
            self.take(bm, tones[i % len(tones)] if i < n else tones[-1])

    def tufted(self, origin, u, v, n, wu, wv, nu, nv, depth, light=(0.0, 1.0, 0.0), contrast=0.22, t=1.0):
        """Стёганая обивка: ромбы между «пуговицами» (решётка nu × nv на панели wu × wv), вершина ромба выпукла на
        depth. origin — угол панели, u и v — оси по панели, n — наружу (всё в осях этажа). Грани к свету светлее.
        Возвращает точки пуговиц внутри панели (оси этажа)."""
        o, u, v, n, lt = Vector(origin), Vector(u).normalized(), Vector(v).normalized(), Vector(n).normalized(), Vector(light)
        cu, cv = wu / nu, wv / nv

        def at(a, b, d=0.0):
            return o + u * (a * cu) + v * (b * cv) + n * d

        def inside(a, b):
            return -1e-6 <= a <= nu + 1e-6 and -1e-6 <= b <= nv + 1e-6

        base = tone(t)
        for i in range(nu + 1):
            for j in range(nv + 1):
                for da, db in ((0.5, 0.5), (0.5, -0.5), (-0.5, 0.5), (-0.5, -0.5)):
                    bi, bj = i + da, j + db
                    if not inside(bi, bj):
                        continue
                    for pk in ((i + da, j), (i, j + db)):
                        if not inside(*pk):
                            continue
                        bm = bmesh.new()
                        pts = [at(i, j), at(bi, bj), at(pk[0], pk[1], depth)]
                        f = bm.faces.new([bm.verts.new(P(*q)) for q in pts])
                        bm.normal_update()
                        nb = Vector((-n.x, n.z, n.y))
                        if f.normal.dot(nb) < 0:
                            f.normal_flip()
                            bm.normal_update()
                        fn = Vector((-f.normal.x, f.normal.z, f.normal.y))  # нормаль в осях этажа
                        k = 1.0 + contrast * (fn.dot(lt) - n.dot(lt)) * 3.0
                        self.take(bm, tuple(min(1.0, c * max(0.55, k)) for c in base))
        knots = []
        for i in range(nu + 1):
            for j in range(nv + 1):
                if 0 < i < nu and 0 < j < nv:
                    knots.append(tuple(at(i, j)))
        for i in range(nu):
            for j in range(nv):
                knots.append(tuple(at(i + 0.5, j + 0.5)))
        return knots

    def stud(self, center, n, r, h, t=1.0):
        """Гвоздик обивки: четырёхгранная пирамидка ромбом на стене с нормалью n (оси этажа)."""
        c, n = Vector(center), Vector(n).normalized()
        u = Vector((-n.z, 0, n.x)) if abs(n.y) < 0.9 else Vector((1, 0, 0))
        u.normalize()
        w = n.cross(u)
        ring = [tuple(c + d * r - n * 0.03) for d in (u, w, -u, -w)]
        self.cone(ring, tuple(c + n * h), t)

    def _give_narrow(self):
        """Узкие четырёхугольные грани — в деталь partner (до её finish)."""
        tone_l = self.bm.loops.layers.float_color["tone"]
        wide = self.bm.faces.layers.int["wide"]
        dst = self.partner.bm
        dst_l = dst.loops.layers.float_color["tone"]
        moved = []
        for f in self.bm.faces:
            if f[wide] or len(f.verts) != 4:
                continue
            e = [(f.verts[i].co - f.verts[(i + 1) % 4].co).length for i in range(4)]
            if min((e[0] + e[2]) / 2, (e[1] + e[3]) / 2) < self.narrow:
                moved.append(f)
        for f in moved:
            nf = dst.faces.new([dst.verts.new(v.co) for v in f.verts])
            for a, b in zip(nf.loops, f.loops):
                a[dst_l] = b[tone_l]
        bmesh.ops.delete(self.bm, geom=moved, context="FACES")
        return len(moved)

    def give_tones(self, dst, codes, tol=0.02):
        """Грани оттенков codes (hex) — в деталь dst: ткань (бархат, ковёр) уходит на тихий материал, золото
        остаётся с рисунком. Флаг крупной грани (wide) переносится."""
        tone_l = self.bm.loops.layers.float_color["tone"]
        wide = self.bm.faces.layers.int["wide"]
        want = [rgb(c) for c in codes]
        dst_l = dst.bm.loops.layers.float_color["tone"]
        dst_w = dst.bm.faces.layers.int["wide"]
        moved = []
        for f in self.bm.faces:
            c = f.loops[0][tone_l]
            if any(all(abs(c[i] - w[i]) <= tol for i in range(3)) for w in want):
                moved.append(f)
        for f in moved:
            nf = dst.bm.faces.new([dst.bm.verts.new(v.co) for v in f.verts])
            nf[dst_w] = f[wide]
            for a, b in zip(nf.loops, f.loops):
                a[dst_l] = b[tone_l]
        bmesh.ops.delete(self.bm, geom=moved, context="FACES")
        return len(moved)

    def give_narrow(self):
        if self.partner is not None and self.narrow > 0 and not self.gave:
            self.gave = True
            self._give_narrow()

    def finish(self, collection):
        self.give_narrow()
        if self.adapt:
            refine(self.bm, 99.0)
        elif self.grid > 0:
            bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=1e-4)
            grid_cut(self.bm, self.grid)
            refine(self.bm, 99.0)
        else:
            refine(self.bm, self.limit)
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        self.obj = bpy.data.objects.new(self.name, me)
        collection.objects.link(self.obj)
        return self.obj


def _hemisphere(count):
    dirs = []
    for k in range(count):
        u1 = (k + 0.5) / count
        u2 = (k * 0.61803398875) % 1.0
        r, phi = math.sqrt(u1), 2 * math.pi * u2
        dirs.append(Vector((r * math.cos(phi), r * math.sin(phi), math.sqrt(1 - u1))))
    return dirs


def _bm_tree(parts, extra=()):
    verts, polys = [], []
    for part in parts:
        if not part.occlude:
            continue
        base = len(verts)
        part.bm.verts.index_update()
        verts.extend(v.co.copy() for v in part.bm.verts)
        polys.extend([base + v.index for v in f.verts] for f in part.bm.faces)
    for obj in extra:
        base = len(verts)
        verts.extend(v.co.copy() for v in obj.data.vertices)
        polys.extend([base + i for i in poly.vertices] for poly in obj.data.polygons)
    return BVHTree.FromPolygons(verts, polys)


def _fit(field, mask, us, vs):
    """Наибольшая ошибка билинейной сетки с линиями us × vs на поле field (только точки внутри грани) и её место."""
    nu, nv = field.shape
    grid = field[np.ix_(us, vs)]
    cols = np.empty((nu, len(vs)))
    ru = np.arange(nu)
    for c in range(len(vs)):
        cols[:, c] = np.interp(ru, us, grid[:, c])
    rv = np.arange(nv)
    full = np.empty((nu, nv))
    for r in range(nu):
        full[r, :] = np.interp(rv, vs, cols[r, :])
    err = np.abs(full - field) * mask
    k = int(err.argmax())
    return float(err.flat[k]), k // nv, k % nv


def _clip_convex(subject, clipper):
    """Пересечение выпуклых многоугольников 2D (clipper — против часовой)."""
    out = subject
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        inp, out = out, []
        if not inp:
            break
        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            ip = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-9
            iq = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0]) >= -1e-9
            if iq != ip:
                x1, y1, x2, y2, x3, y3, x4, y4 = a[0], a[1], b[0], b[1], p[0], p[1], q[0], q[1]
                den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
                if abs(den) > 1e-12:
                    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
                    out.append((x1 + t * (x2 - x1), y1 + t * (y2 - y1)))
            if iq:
                out.append(q)
    return out


def _area2(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2


def _tris2(pts):
    """Треугольники многоугольника 2D (против часовой) для подсчёта перекрытий."""
    from mathutils.geometry import tessellate_polygon
    tri = tessellate_polygon([[Vector((x, y, 0.0)) for x, y in pts]])
    out = []
    for a, b, c in tri:
        t = [pts[a], pts[b], pts[c]]
        if (t[1][0] - t[0][0]) * (t[2][1] - t[0][1]) - (t[1][1] - t[0][1]) * (t[2][0] - t[0][0]) < 0:
            t = [t[0], t[2], t[1]]
        out.append(t)
    return out


def resolve_coplanar(parts, gap=0.012, push=0.03, passes=3):
    """Мерцание (z-fighting): грани разных тел в одной плоскости и смотрящие в одну сторону. Меньшая из пары
    выдвигается по нормали на push — накладка ложится поверх, большая поверхность остаётся на месте. Вызывать до
    adaptive_cut и finish, после give_narrow. Возвращает число сдвинутых граней."""
    for part in parts:
        part.give_narrow()
    total = 0
    for _ in range(passes):
        faces = []
        for part in parts:
            for f in part.bm.faces:
                ar = f.calc_area()
                if ar < 0.004:
                    continue
                n = f.normal.copy()
                if n.length < 0.5:
                    continue
                d = n.dot(f.verts[0].co)
                zc = f.calc_center_median().z  # высота этажа (floor y = Blender z)
                if (n.z < -0.9 and zc < -0.95) or (n.z > 0.9 and zc > 18.95):
                    continue  # низ площадки и верх крыши закрыты соседними этажами; сдвиг вывел бы их из полосы
                faces.append((part, f, n, d, ar))
        buckets = {}
        for i, (_p, _f, n, d, _a) in enumerate(faces):
            key = (round(n.x * 50), round(n.y * 50), round(n.z * 50), round(d / 0.02))
            buckets.setdefault(key, []).append(i)
        movers = {}
        for key, idxs in buckets.items():
            cand = list(idxs) + buckets.get((key[0], key[1], key[2], key[3] + 1), [])
            if len(cand) < 2:
                continue
            n = faces[cand[0]][2]
            ax = max(range(3), key=lambda k: abs(n[k]))
            u, v = [k for k in range(3) if k != ax]
            flip = n[ax] < 0
            proj = []
            for i in cand:
                pts = [(vv.co[u], vv.co[v]) for vv in faces[i][1].verts]
                if flip:
                    pts = pts[::-1]
                if (pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1]) - (pts[1][1] - pts[0][1]) * (pts[2][0] - pts[0][0]) < 0:
                    pts = pts[::-1]
                xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                proj.append((min(xs), max(xs), min(ys), max(ys), i, pts))
            proj.sort(key=lambda r: r[0])
            for a_i in range(len(proj)):
                A = proj[a_i]
                for b_i in range(a_i + 1, len(proj)):
                    Bq = proj[b_i]
                    if Bq[0] >= A[1] - 1e-6:
                        break
                    if Bq[2] >= A[3] - 1e-6 or A[2] >= Bq[3] - 1e-6:
                        continue
                    fa, fb = faces[A[4]], faces[Bq[4]]
                    if abs(fa[3] - fb[3]) > gap or fa[1] is fb[1]:
                        continue
                    if fa[2].dot(fb[2]) < 0.999:
                        continue
                    ov = 0.0
                    for ta in _tris2(A[5]):
                        for tb in _tris2(Bq[5]):
                            c = _clip_convex(ta, tb)
                            if len(c) >= 3:
                                ov += _area2(c)
                    if ov < 0.005:
                        continue
                    order = [A[4], Bq[4]] if (fa[4], A[4]) < (fb[4], Bq[4]) else [Bq[4], A[4]]
                    for mover in order:  # сдвиг не должен выводить тело из полосы этажа −1…19
                        nz = faces[mover][2].z * push
                        if all(-1.0 <= vv.co.z + nz <= 19.0 for vv in faces[mover][1].verts):
                            movers[mover] = faces[mover]
                            break
        if not movers:
            break
        done = {}  # вершина → направления, по которым её уже сдвинули (общая вершина соседних граней — один раз)
        for part, f, n, d, ar in movers.values():
            key = (round(n.x, 2), round(n.y, 2), round(n.z, 2))
            for vv in f.verts:
                seen = done.setdefault(vv, set())
                if key in seen:
                    continue
                seen.add(key)
                vv.co += n * push
        for part in parts:
            part.bm.normal_update()
        total += len(movers)
    return total


def adaptive_cut(parts, extra=(), radius=3.0, rays=12, tol=0.07, fine=0.8, min_size=1.6, max_lines=12):
    """Сетка вершин под затенение — только там, где оно меняется. Для каждой крупной грани по осям этажа: окклюзия
    считается на мелкой сетке точек, затем жадно добавляются линии разреза вдоль двух осей грани, пока билинейная
    сетка не повторит поле с ошибкой ≤ tol. Ровная стена остаётся одной гранью, тень у стыка получает 2–3 линии.
    Вызывать до finish (детали с квадратами к этому времени отдали узкие грани: give_narrow)."""
    for part in parts:
        part.give_narrow()
    tree = _bm_tree(parts, extra)
    dirs = _hemisphere(rays)
    up = Vector((0, 0, 1))
    lines = 0
    for part in parts:
        bm = part.bm
        for f in list(bm.faces):
            if not f.is_valid:
                continue
            n = f.normal.copy()
            k = max(range(3), key=lambda i: abs(n[i]))
            if abs(n[k]) < 0.999:
                continue
            a, b = [i for i in range(3) if i != k]
            ua, ub = [v.co[a] for v in f.verts], [v.co[b] for v in f.verts]
            a0, a1, b0, b1 = min(ua), max(ua), min(ub), max(ub)
            da, db = a1 - a0, b1 - b0
            if max(da, db) < min_size:
                continue
            na = max(2, int(round(da / fine)) + 1) if da >= min_size else 2
            nb = max(2, int(round(db / fine)) + 1) if db >= min_size else 2
            if na == 2 and nb == 2:
                continue
            level = f.verts[0].co[k]
            q = up.rotation_difference(n)
            local = [q @ d for d in dirs]
            field, mask = np.ones((na, nb)), np.zeros((na, nb))
            for i in range(na):
                for j in range(nb):
                    pt = Vector((0.0, 0.0, 0.0))
                    pt[k] = level
                    pt[a] = min(max(a0 + da * i / (na - 1), a0 + 0.06), a1 - 0.06)
                    pt[b] = min(max(b0 + db * j / (nb - 1), b0 + 0.06), b1 - 0.06)
                    if not bmesh.geometry.intersect_face_point(f, pt):
                        continue
                    o = pt + n * 0.22
                    vis = 0.0
                    for d in local:
                        hit = tree.ray_cast(o, d, radius)
                        vis += 1.0 if hit[0] is None else (hit[3] / radius) ** 0.8
                    field[i, j], mask[i, j] = vis / rays, 1.0
            if mask.sum() < 2:
                continue
            mean = float((field * mask).sum() / mask.sum())
            field = np.where(mask > 0, field, mean)
            us, vs = [0, na - 1], [0, nb - 1]
            while len(us) + len(vs) - 4 < max_lines:
                err, i, j = _fit(field, mask, us, vs)
                if err <= tol:
                    break
                tries = []
                if i not in us:
                    tries.append((_fit(field, mask, sorted(us + [i]), vs)[0], 0))
                if j not in vs:
                    tries.append((_fit(field, mask, us, sorted(vs + [j]))[0], 1))
                if not tries:
                    break
                if min(tries)[1] == 0:
                    us = sorted(us + [i])
                else:
                    vs = sorted(vs + [j])
            pieces = [f]
            for axis, idx, lo, span, count in ((a, us, a0, da, na), (b, vs, b0, db, nb)):
                for i in idx[1:-1]:
                    co, no = Vector((0.0, 0.0, 0.0)), Vector((0.0, 0.0, 0.0))
                    co[axis], no[axis] = lo + span * i / (count - 1), 1.0
                    geom = set(pieces)
                    for piece in pieces:
                        geom.update(piece.edges)
                        geom.update(piece.verts)
                    res = bmesh.ops.bisect_plane(bm, geom=list(geom), dist=1e-5, plane_co=co, plane_no=no,
                                                 clear_inner=False, clear_outer=False)
                    pieces = [g for g in res["geom"] if isinstance(g, bmesh.types.BMFace) and g.is_valid]
                    lines += 1
    return lines


def shade_parts(parts, extra=(), radius=5.0, rays=20, form=None, zone=None, floor_lo=0.0):
    """Затенение в цветах вершин: лучи по полусфере до radius, заслоняют все детали группы и тела extra.
    form — множители по сторонам света в осях этажа {"up", "down", "px", "nx", "pz", "nz"}: у каждой стороны блока
    своя ровная яркость (читаются светлые и тёмные стороны объёмов без света игры); form["edge"] — множитель косых
    граней (фаски рёбер: блик на скруглённом ребре бруска); zone(x, y, z) → множитель зоны (ровный по залу; на пол не
    действует); floor_lo — нижний предел множителя."""
    verts, polys = [], []
    for obj in [p.obj for p in parts if p.occlude] + list(extra):
        me, base = obj.data, len(verts)
        verts.extend(v.co.copy() for v in me.vertices)
        polys.extend([base + i for i in poly.vertices] for poly in me.polygons)
    tree = BVHTree.FromPolygons(verts, polys)
    dirs = _hemisphere(rays)
    up = Vector((0, 0, 1))
    for part in parts:
        me = part.obj.data
        tones = me.attributes["tone"].data
        col = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
        amb = [1.0] * len(me.loops)
        groups = {}  # углы одной вершины на одной плоскости затеняются одинаково (без «зубцов» по треугольникам)
        for poly in me.polygons:
            n, c = poly.normal, poly.center
            q = up.rotation_difference(n)
            local = [q @ d for d in dirs]
            key_n = (round(n.x, 2), round(n.y, 2), round(n.z, 2))
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                p = me.vertices[vi].co
                # лучи — чуть над поверхностью: тонкие накладки (инкрустация, ковёр) не дают пятен
                o = p + n * 0.22 + (c - p) * 0.15
                vis = 0.0
                for d in local:
                    hit = tree.ray_cast(o, d, radius)
                    vis += 1.0 if hit[0] is None else (hit[3] / radius) ** 0.8
                amb[li] = vis / rays
                groups.setdefault((vi, key_n), []).append(li)
        for loops in groups.values():
            mean = sum(amb[li] for li in loops) / len(loops)
            for li in loops:
                amb[li] = mean
        side = [1.0] * len(me.loops)
        if form or zone:
            for poly in me.polygons:
                n = poly.normal  # Blender (−X, Z, Y) → оси этажа
                fx, fy, fz = -n.x, n.z, n.y
                k = 1.0
                if form:
                    k = (max(fy, 0) ** 2 * form["up"] + max(-fy, 0) ** 2 * form["down"] + max(fx, 0) ** 2 * form["px"]
                         + max(-fx, 0) ** 2 * form["nx"] + max(fz, 0) ** 2 * form["pz"] + max(-fz, 0) ** 2 * form["nz"])
                    if max(abs(fx), abs(fy), abs(fz)) < 0.9:
                        k *= form.get("edge", 1.0)
                if zone and fy < 0.9:
                    c = poly.center
                    k *= zone(-c.x, c.z, c.y)
                for li in poly.loop_indices:
                    side[li] = k
        for li in range(len(me.loops)):
            a = 1.0 - (1.0 - amb[li]) * part.ao
            t = tones[li].color
            col.data[li].color_srgb = [min(1.0, t[i] * max(floor_lo, (part.shade[i] + (1 - part.shade[i]) * a) * side[li]))
                                       for i in range(3)] + [1.0]
        me.attributes.remove(me.attributes["tone"])
        me.color_attributes.active_color = col
        me.color_attributes.render_color_index = 0


def flat_parts(parts):
    """Без затенения: только оттенки граней (силуэт)."""
    for part in parts:
        me = part.obj.data
        tones = me.attributes["tone"].data
        col = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
        for li in range(len(me.loops)):
            t = tones[li].color
            col.data[li].color_srgb = (t[0], t[1], t[2], 1.0)
        me.attributes.remove(me.attributes["tone"])
        me.color_attributes.active_color = col


def preview_material(part):
    """Материал для проверочных рендеров: цвет вершин × цвет детали (как Color у MeshPart)."""
    mat = bpy.data.materials.new(part.name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    c = rgb(part.tint)
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    mix.inputs[6].default_value = (*lin, 1)
    nt.links.new(attr.outputs["Color"], mix.inputs[7])
    out = mix.outputs[2]
    nt.links.new(out, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.75
    if part.material == "glass":
        nt.links.new(out, bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.6
    part.obj.data.materials.append(mat)


def manifest(parts):
    data = {}
    for part in parts:
        me = part.obj.data
        xs = [v.co for v in me.vertices]
        lo = Vector((min(v.x for v in xs), min(v.y for v in xs), min(v.z for v in xs)))
        hi = Vector((max(v.x for v in xs), max(v.y for v in xs), max(v.z for v in xs)))
        c, s = (lo + hi) / 2, hi - lo
        me.calc_loop_triangles()
        data[part.name] = {"tier": part.tier, "material": part.material, "tint": part.tint,
                           "center": [round(-c.x, 4), round(c.z, 4), round(c.y, 4)],
                           "size": [round(s.x, 4), round(s.z, 4), round(s.y, 4)], "tris": len(me.loop_triangles)}
    return data


def export_fbx(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP", colors_type="SRGB")


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

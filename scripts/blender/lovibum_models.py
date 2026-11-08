"""Игровые модели Ловибумов v5 (D55, этап A): FBX из подвижных частей, карты D39, скелет и Part-версия.

Геометрия — lovibum_shapes.py (та же, что у утверждённого концепта v5). Для каждого вида (Бум, Турбо, Мега):
- меш собирается в закрытом виде, проверяется (≤ 2 000 треугольников, совпадающих граней 0, скелет полный),
  запекается в стиле D39 (цвет с окклюзией и нормали, 512², части разнесены — без чужих теней в любой позе),
  режется на части Base, Core, Claw1…Claw4, Crystal (начало координат — точка вращения) →
  assets/models/lovibums/Lovibum_<Вид>.fbx (меши Lovibum<Вид><Часть>), <Вид>.rig.json, карты
  assets/textures/lovibums/<Вид>_{color,normal}.png. Ядро и кристалл в игре — Neon (решение владельца 2026-11-08),
  их карты не нужны.
- запасная Part-версия (до импорта мешей — импорт и загрузка пока запрещены владельцем) — те же детали из Roblox-
  примитивов: брусок → Block, восьмигранник → Block + 2 Block + 4 Wedge (светящийся — Cylinder), пирамида кристалла →
  4 CornerWedge, многоугольник → Wedge по прямоугольным треугольникам → assets/models/lovibums/parts.json (оси
  Roblox, лицо в +Z) для scripts/lovibum_rig_to_luau.py.
- кадры <рендеры>/: концепт ↔ меш ↔ Part-версия и раскрытие когтей 0 / 50 / 100 % (листы —
  scripts/d55_lovibum_sheets.py --models).
Ничего не загружает. Запуск:
blender --background --factory-startup --python scripts/blender/lovibum_models.py -- <репо> <рендеры> [--quick]
(--quick — без запекания и FBX: только проверки, Part-версия и кадры с материалами сборки).
Зависит от lovibum_shapes.py и art_style.py.
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402
from lovibum_shapes import CLAWS, GLOW, NEON, OPEN_DEG, TYPES, lovibum  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
QUICK = "--quick" in argv
MODELS = os.path.join(REPO, "assets", "models", "lovibums")
TEXDIR = os.path.join(REPO, "assets", "textures", "lovibums")
for d in (OUT, MODELS, TEXDIR):
    os.makedirs(d, exist_ok=True)
S.TEX = 512  # карты 512² (Ловибум маленький: ≈ 1.5 стада)
MAX_TRIS = 2000
NAMES = ("Boom", "Turbo", "Mega")
TO_RBX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))  # оси Blender → оси Roblox
FROM_RBX = TO_RBX.transposed()
EXTRA_COLORS = {"gemp": "FF3B7F", "gemc": "3FE0FF", "white": "FFFDF4"}


def color_of(key, spec):
    """Цвет детали: второй ряд граней кристалла Меги — цвет кристалла (в игре кристалл — один Neon, как у меша)."""
    return spec["crystal"] if key == "crystal2" else spec.get(key) or EXTRA_COLORS[key]


def rbx(v):
    return TO_RBX @ Vector(v)


# ── Part-версия: те же вызовы деталей → примитивы Roblox ─────────────────────────────────────────────────────


def _is_octagon(pts):
    if len(pts) != 8:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    cut = pts[0][0] - x0
    ref = S.octagon(x0, x1, y0, y1, cut)
    if cut > 1e-6 and all(abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6 for a, b in zip(pts, ref)):
        return x0, x1, y0, y1, cut
    return None


def _triangulate(pts):
    """Простой многоугольник → треугольники (отсечение ушей)."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    sign = 1 if sum(pts[i].x * pts[(i + 1) % n].y - pts[(i + 1) % n].x * pts[i].y for i in range(n)) > 0 else -1

    def cross(a, b, c):
        return (b.x - a.x) * (c.y - b.y) - (b.y - a.y) * (c.x - b.x)

    def inside(p, a, b, c):
        d1, d2, d3 = cross(a, b, p) * sign, cross(b, c, p) * sign, cross(c, a, p) * sign
        return d1 > 1e-9 and d2 > 1e-9 and d3 > 1e-9

    idx, tris = list(range(n)), []
    while len(idx) > 3:
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if cross(a, b, c) * sign <= 1e-9:
                continue
            if any(inside(pts[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((a, b, c))
            idx.pop(k)
            break
        else:
            raise ValueError("многоугольник не делится на треугольники")
    tris.append(tuple(pts[i] for i in idx))
    return tris


def _right_tris(a, b, c):
    """Треугольник → прямоугольные (высота из вершины против длинной стороны): (вершина прямого угла, катет, катет)."""
    e1, e2, v = max(((a, b, c), (b, c, a), (c, a, b)), key=lambda e: (e[1] - e[0]).length)
    d = e2 - e1
    f = e1 + d * ((v - e1).dot(d) / d.length_squared)
    return [(f, e - f, v - f) for e in (e1, e2) if (e - f).length > 1e-5 and (v - f).length > 1e-5]


class PartArt:
    """Запись деталей Ловибума примитивами Roblox (тот же набор вызовов, что у art_style.Art). Каждая деталь —
    (часть, ключ цвета, форма, центр и оси Roblox-детали X, Y, Z в осях Blender, размер)."""

    def __init__(self, name, ring_z0=0.0):
        self.name = name
        self.colors = {}
        self.group = None
        self.transform = None
        self.parts = []

    def paint(self, key, code, rings=False):
        self.colors[key] = code

    def _m(self, matrix):
        m = matrix if matrix is not None else Matrix.Identity(4)
        return self.transform @ m if self.transform is not None else m

    def _emit(self, key, shape, c, x, y, size):
        x, y = x.normalized(), y.normalized()
        self.parts.append({"group": self.group, "key": key, "shape": shape, "c": Vector(c), "X": x, "Y": y,
                           "Z": x.cross(y), "size": size})

    def _block(self, key, full, lo, hi):
        """Брусок lo..hi в локальных осях full (оси бруска — столбцы full; правая тройка — Z = X × Y)."""
        rot = full.to_3x3()
        cx, cy, cz = rot.col[0], rot.col[1], rot.col[2]
        c = full @ ((Vector(lo) + Vector(hi)) / 2)
        size = (abs(hi[0] - lo[0]) * cx.length, abs(hi[2] - lo[2]) * cz.length, abs(hi[1] - lo[1]) * cy.length)
        self._emit(key, "Block", c, cx, cz, size)

    def _wedge(self, key, full, p, leg_a, leg_b, depth):
        """Призма прямоугольного треугольника: вершина прямого угла p, катеты leg_a и leg_b (в плоскости z = p.z),
        вытянута по локальной z на depth. Wedge Roblox: прямой угол у (−Y, +Z), катеты вдоль +Y и −Z."""
        rot = full.to_3x3()
        pa, a, b, e = full @ Vector(p), rot @ Vector(leg_a), rot @ Vector(leg_b), rot @ Vector((0, 0, depth))
        y, z = a.normalized(), -b.normalized()
        self._emit(key, "Wedge", pa + a / 2 + b / 2 + e / 2, y.cross(z), y, (e.length, a.length, b.length))

    def _poly(self, key, full, pts, a0, a1):
        for tri in _triangulate(pts):
            for f, la, lb in _right_tris(*tri):
                self._wedge(key, full, (f.x, f.y, a0), (la.x, la.y, 0), (lb.x, lb.y, 0), a1 - a0)

    def box(self, key, x0, x1, y0, y1, z0, z1, bevel=0.0, matrix=None):
        self._block(key, self._m(matrix), (x0, y0, z0), (x1, y1, z1))

    def prism(self, key, pts, a0, a1, axis="z", bevel=0.0, matrix=None):
        full = self._m(matrix) @ S.AXES[axis]
        octa = _is_octagon(pts)
        if not octa:
            self._poly(key, full, pts, a0, a1)
            return
        x0, x1, y0, y1, c = octa
        if key in NEON:  # светящийся ярус — цилиндр: ступени ядра остаются, а Neon граней всё равно не видно
            rot = full.to_3x3()
            ax, ux = rot @ Vector((0, 0, 1)), rot @ Vector((1, 0, 0))
            d = (x1 - x0 + y1 - y0) / 2 * 0.97
            self._emit(key, "Cylinder", full @ Vector(((x0 + x1) / 2, (y0 + y1) / 2, (a0 + a1) / 2)), ax, ux,
                       ((a1 - a0) * ax.length, d, d))
            return
        if min(x1 - x0, y1 - y0) < 0.25:  # мелкая заклёпка — один брусок
            self._block(key, full, (x0 + c / 2, y0 + c / 2, a0), (x1 - c / 2, y1 - c / 2, a1))
            return
        self._block(key, full, (x0, y0 + c, a0), (x1, y1 - c, a1))
        self._block(key, full, (x0 + c, y1 - c, a0), (x1 - c, y1, a1))
        self._block(key, full, (x0 + c, y0, a0), (x1 - c, y0 + c, a1))
        for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            px = x1 - c if sx > 0 else x0 + c
            py = y1 - c if sy > 0 else y0 + c
            self._wedge(key, full, (px, py, a0), (sx * c, 0, 0), (0, sy * c, 0), a1 - a0)

    def frustum(self, key, bottom, top, z0, z1, axis="z", bevel=0.0, matrix=None):
        """Только пирамиды (кристалл): маленький торец (≤ 0.05) считается вершиной → 4 CornerWedge."""
        full = self._m(matrix) @ S.AXES[axis]
        tiny = lambda r: r[1] - r[0] <= 0.05 and r[3] - r[2] <= 0.05  # noqa: E731
        if tiny(top):
            base, zb, za = bottom, z0, z1
        elif tiny(bottom):
            base, zb, za = top, z1, z0
        else:
            raise NotImplementedError("усечённая пирамида в Part-версии")
        rot = full.to_3x3()
        cx, cy = (base[0] + base[1]) / 2, (base[2] + base[3]) / 2
        hu, hw = (base[1] - base[0]) / 2, (base[3] - base[2]) / 2
        up = rot @ Vector((0, 0, za - zb))
        for sx in (-1, 1):
            for sy in (-1, 1):
                c = full @ Vector((cx + sx * hu / 2, cy + sy * hw / 2, (zb + za) / 2))
                # вершина CornerWedge — угол (+X, +Y, −Z): +X и −Z смотрят от наружного угла к центру основания
                da, db = (rot @ Vector((-sx, 0, 0))).normalized(), (rot @ Vector((0, -sy, 0))).normalized()
                sa, sb = hu, hw
                if da.cross(up.normalized()).dot(-db) < 0:
                    da, db, sa, sb = db, da, sb, sa
                self.parts.append({"group": self.group, "key": key, "shape": "CornerWedge", "c": c, "X": da,
                                   "Y": up.normalized(), "Z": -db, "size": (sa, up.length, sb)})

    def extrude(self, key, pts, a0, a1, axis="y", bevel=0.0, matrix=None):
        self._poly(key, self._m(matrix) @ S.AXES[axis], pts, a0, a1)


def part_json(rec, spec):
    """Детали в осях Roblox: форма, размер, CFrame (x, y, z, r00…r22) в координатах модели, цвет, Neon."""
    out = []
    for p in rec.parts:
        x, y, z = rbx(p["X"]), rbx(p["Y"]), rbx(p["Z"])
        c = rbx(p["c"])
        code = color_of(p["key"], spec)
        out.append({"group": p["group"], "key": p["key"], "shape": p["shape"],
                    "size": [round(v, 4) for v in p["size"]],
                    "cf": [round(v, 4) for v in (c.x, c.y, c.z, x.x, y.x, z.x, x.y, y.y, z.y, x.z, y.z, z.z)],
                    "color": code, "neon": p["key"] in NEON})
    return out


def part_mesh(p, collection, mats):
    """Деталь Part-версии в Blender (для кадров и проверки граней): та же форма Roblox, оси Blender."""
    hx, hy, hz = (s / 2 for s in p["size"])
    bm = bmesh.new()
    if p["shape"] == "Block":
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=p["size"], verts=bm.verts)
    elif p["shape"] == "Wedge":
        vs = [bm.verts.new((x, y, z)) for x in (-hx, hx) for y, z in ((-hy, -hz), (-hy, hz), (hy, hz))]
        bm.faces.new((vs[0], vs[1], vs[2]))
        bm.faces.new((vs[5], vs[4], vs[3]))
        for i, j in ((0, 1), (1, 2), (2, 0)):
            bm.faces.new((vs[i], vs[j], vs[j + 3], vs[i + 3]))
    elif p["shape"] == "CornerWedge":
        b = [bm.verts.new(v) for v in ((-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz))]
        apex = bm.verts.new((hx, hy, -hz))
        bm.faces.new(b)
        for i in range(4):
            bm.faces.new((b[i], b[(i + 1) % 4], apex))
    elif p["shape"] == "Cylinder":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=min(hy, hz), radius2=min(hy, hz), depth=2 * hx,
                              matrix=Matrix.Rotation(math.pi / 2, 4, "Y"))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    rot = Matrix((p["X"], p["Y"], p["Z"])).transposed().to_4x4()  # локальные оси Roblox-детали в осях Blender
    rot.translation = p["c"]
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    me = bpy.data.meshes.new("PartVer")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mats[p["key"]])
    obj = bpy.data.objects.new("PartVer_" + (p["group"] or ""), me)
    collection.objects.link(obj)
    return obj


def flat_mats(name, spec):
    mats = {}
    for key in list(spec) + list(EXTRA_COLORS) + ["crystal2"]:
        if not isinstance(spec.get(key, ""), str):
            continue
        code = color_of(key, spec)
        m = bpy.data.materials.new(f"{name}_{key}")
        m.use_nodes = True
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = (*S.lin(code), 1)
        b.inputs["Roughness"].default_value = 0.5
        if key in NEON:  # Neon в игре — ровный яркий цвет
            b.inputs["Emission Color"].default_value = (*S.lin(code), 1)
            b.inputs["Emission Strength"].default_value = GLOW[key]
        mats[key] = m
    return mats


# ── Меш: проверки, запекание, части, FBX, скелет ─────────────────────────────────────────────────────────────


def explode(obj, art, sign):
    """Разнести части по x на 10 шагов квадратов D39 (рисунок не сдвигается): окклюзия при запекании только своя."""
    order = {g: i for i, g in enumerate(dict.fromkeys(art.face_groups))}
    me = obj.data
    done = set()
    for poly in me.polygons:
        dx = order[art.face_groups[poly.index]] * 10 * S.RING["step"] * sign
        for v in poly.vertices:
            if v not in done:
                me.vertices[v].co.x += dx
                done.add(v)


def rig_json(name, art, parts):
    """Скелет Ловибума в осях Roblox: части, родители, точки вращения, габариты меша относительно точки вращения,
    ось раскрытия когтей (поворот на +OpenDeg вокруг оси — наружу), подъём кристалла, Neon-части, точка света."""
    out = {"id": name, "order": list(art.rig), "open_deg": OPEN_DEG, "crystal_lift": art.lift,
           "neon": [g for g in ("Core", "Crystal") if g in art.rig], "light": [round(c, 4) for c in rbx(art.light)],
           "parts": {}}
    for g, (parent, pivot) in art.rig.items():
        co = [TO_RBX @ v.co for v in parts[g].data.vertices]
        lo = Vector([min(c[i] for c in co) for i in range(3)])
        hi = Vector([max(c[i] for c in co) for i in range(3)])
        entry = {"parent": parent, "pivot": [round(c, 4) for c in rbx(pivot)],
                 "center": [round(c, 4) for c in (lo + hi) / 2], "size": [round(c, 4) for c in hi - lo]}
        if g in art.axes:
            entry["axis"] = [round(c, 4) for c in rbx(art.axes[g])]
        out["parts"][g] = entry
    with open(os.path.join(MODELS, f"{name}.rig.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return out


def split_keep(obj, art, collection):
    """Части с материалами сборки (без запекания, режим --quick)."""
    out = {}
    for group, (_, pivot) in art.rig.items():
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if art.face_groups[f.index] != group], context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bmesh.ops.translate(bm, vec=-Vector(pivot), verts=bm.verts)
        me = bpy.data.meshes.new(f"{obj.name}_{group}")
        bm.to_mesh(me)
        bm.free()
        for m in obj.data.materials:
            me.materials.append(m)
        o = bpy.data.objects.new(f"{obj.name}_{group}", me)
        o.location = pivot
        collection.objects.link(o)
        out[group] = o
    bpy.data.objects.remove(obj)
    return out


def neon_look(parts, spec):
    """Ядро и кристалл меша — как в игре: Neon ровного цвета (без карт)."""
    for g, key in (("Core", "core"), ("Crystal", "crystal")):
        if g in parts:
            m = bpy.data.materials.new(f"{parts[g].name}_neon")
            m.use_nodes = True
            b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Base Color"].default_value = (*S.lin(spec[key]), 1)
            b.inputs["Emission Color"].default_value = (*S.lin(spec[key]), 1)
            b.inputs["Emission Strength"].default_value = GLOW[key]
            parts[g].data.materials.clear()
            parts[g].data.materials.append(m)


def _clip_area(a, b):
    """Площадь пересечения двух выпуклых многоугольников (Сазерленд — Ходжман)."""

    def area(p):
        return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2

    if area(a) < 0:
        a = a[::-1]
    if area(b) < 0:
        b = b[::-1]
    out = a
    for i in range(len(b)):
        (x0, y0), (x1, y1) = b[i], b[(i + 1) % len(b)]
        side = lambda p: (x1 - x0) * (p[1] - y0) - (y1 - y0) * (p[0] - x0)  # noqa: E731
        src, out = out, []
        for k in range(len(src)):
            p, q = src[k], src[(k + 1) % len(src)]
            sp, sq_ = side(p), side(q)
            if sp >= 0:
                out.append(p)
            if (sp >= 0) != (sq_ >= 0):
                t = sp / (sp - sq_)
                out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
        if not out:
            return 0.0
    return abs(area(out)) if len(out) > 2 else 0.0


def coplanar_parts(objs):
    """Совпадающие грани Part-версии: видимые (центр грани не внутри другой детали) осевые грани разных деталей в
    одной плоскости, смотрящие в одну сторону, с настоящим перекрытием (> 0.0005 ст²). Должно быть 0."""
    solids = []
    for o in objs:
        me = o.data
        solids.append([(p.normal.copy(), p.normal.dot(me.vertices[p.vertices[0]].co)) for p in me.polygons])
    groups = {}
    for i, o in enumerate(objs):
        me = o.data
        for p in me.polygons:
            n = p.normal
            axis = max(range(3), key=lambda k: abs(n[k]))
            if abs(n[axis]) < 0.999:
                continue
            c = p.center
            if any(j != i and all(nn.dot(c) - d < -1e-4 for nn, d in solids[j]) for j in range(len(objs))):
                continue  # грань внутри другой детали — её не видно
            others = [k for k in range(3) if k != axis]
            poly = [(me.vertices[v].co[others[0]], me.vertices[v].co[others[1]]) for v in p.vertices]
            groups.setdefault((axis, n[axis] > 0, round(c[axis], 3)), []).append((i, poly))
    pairs = []
    for (axis, positive, coord), items in groups.items():
        for a in range(len(items)):
            for b in range(a + 1, len(items)):
                (ia, pa), (ib, pb) = items[a], items[b]
                if ia != ib and _clip_area(pa, pb) > 0.0005:
                    pairs.append(f"{'+' if positive else '-'}{'xyz'[axis]}={coord} детали {ia}/{ib}")
    return pairs


# ── Поза: раскрытие когтей ───────────────────────────────────────────────────────────────────────────────────


def pose(objs_by_group, base, art, frac):
    """Раскрыть когти на долю frac (0…1) вокруг их осей и поднять кристалл (объекты частей в группах)."""
    for g, objs in objs_by_group.items():
        _, pivot = art.rig[g]
        pv = Vector(pivot)
        if g in art.axes:
            m = (Matrix.Translation(pv) @ Matrix.Rotation(math.radians(OPEN_DEG * frac), 4, Vector(art.axes[g]))
                 @ Matrix.Translation(-pv))
        elif g == "Crystal":
            m = Matrix.Translation((0, 0, art.lift * frac))
        else:
            m = Matrix.Identity(4)
        for o in objs:
            o.matrix_world = m @ base[o]


def only(objs):
    keep = set(objs)
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and o.name != "Floor":
            o.hide_render = o not in keep


def hero(prev, objs, path, size=1.7, cz=0.75, res=(700, 700)):
    dist = 2.7 * size + 1.0
    prev.shot(path, (-0.62 * dist, -0.85 * dist, cz + 0.55 * size), (0, 0, cz - 0.05 * size), 75, res)


bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Lovibums")
bpy.context.scene.collection.children.link(collection)

report, rigs, part_data, scenes = {}, {}, {}, {}
for name in NAMES:
    spec = TYPES[name]
    art = lovibum(name)
    obj = art.build(collection)
    groups = list(dict.fromkeys(art.face_groups))
    missing = [g for g in groups if g not in art.rig]
    if art.stats["tris"] > MAX_TRIS or art.stats["coplanar"] or art.stats["flipped"] or missing:
        raise ValueError(f"{name}: {art.stats['tris']} треуг., грани {art.stats['coplanar'][:3]}, "
                         f"вывернуто {art.stats['flipped']}, без скелета {missing}")
    uv = {}
    if not QUICK:
        explode(obj, art, 1)
        uv = S.bake(obj, art, TEXDIR, name)
        explode(obj, art, -1)
        parts = S.split_groups(obj, art, {g: Vector(p) for g, (_, p) in art.rig.items()}, collection)
        for g, o in parts.items():
            o.name = o.data.name = f"Lovibum{name}{g}"
        S.export_fbx([parts[g] for g in art.rig], os.path.join(MODELS, f"Lovibum_{name}.fbx"))
    else:
        parts = split_keep(obj, art, collection)
    rigs[name] = rig_json(name, art, parts)
    neon_look(parts, spec)

    rec = lovibum(name, art_cls=PartArt)
    part_data[name] = {"parts": part_json(rec, spec), "rig": rigs[name], "glow": spec["glow"]}
    mats = flat_mats(f"PV_{name}", spec)
    pv = [part_mesh(p, collection, mats) for p in rec.parts]
    copl = coplanar_parts(pv)
    shapes = {}
    for p in rec.parts:
        shapes[p["shape"]] = shapes.get(p["shape"], 0) + 1
    report[name] = {"tris": art.stats["tris"], "mesh_parts": len(groups), "hidden_faces": art.stats["hidden_faces"],
                    **{k: round(v, 3) for k, v in uv.items()}, "part_version": len(rec.parts), "shapes": shapes,
                    "part_coplanar": copl[:5], "part_coplanar_count": len(copl)}
    if copl:
        print("PART_COPLANAR", name, len(copl), copl[:5], flush=True)

    concept = lovibum(name)
    cobj = concept.build(collection)
    for mat in cobj.data.materials:
        key = mat.name.split("_")[-1]
        if key in GLOW:
            next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs[
                "Emission Strength"].default_value = GLOW[key]
    for o in [cobj] + list(parts.values()) + pv:
        o.hide_render = True
    scenes[name] = (art, cobj, parts, pv, rec)
    print("MODEL_OK", name, json.dumps(report[name], ensure_ascii=False), flush=True)

prev = S.Preview(collection)
for name, (art, cobj, parts, pv, rec) in scenes.items():
    only([cobj])
    hero(prev, [cobj], os.path.join(OUT, f"{name}_concept.png"))
    mesh_groups = {g: [o] for g, o in parts.items()}
    part_groups = {}
    for p, o in zip(rec.parts, pv):
        part_groups.setdefault(p["group"], []).append(o)
    base = {o: o.matrix_world.copy() for o in list(parts.values()) + pv}
    for label, objs, groups in (("mesh", list(parts.values()), mesh_groups), ("parts", pv, part_groups)):
        only(objs)
        for frac in (0.0, 0.5, 1.0):
            pose(groups, base, art, frac)
            bpy.context.view_layer.update()
            hero(prev, objs, os.path.join(OUT, f"{name}_{label}_open{int(frac * 100)}.png"))
        pose(groups, base, art, 0.0)
    only([])

with open(os.path.join(MODELS, "parts.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(part_data, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("LOVIBUM_MODELS_OK " + json.dumps({k: [v["tris"], v["part_version"], v["part_coplanar_count"]]
                                         for k, v in report.items()}), flush=True)

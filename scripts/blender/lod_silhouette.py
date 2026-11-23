"""Опыт: более узнаваемый дальний силуэт этажа (S_All) в том же бюджете 400 треугольников, без пересборки этажа.

Основа — нынешний силуэт этажа (коробка стен, земля, крыша — как есть). Остаток бюджета отдаётся крупнейшим
выступающим частям фасада из готового FBX этажа: объёмные — коробкой (без дна, 10 треугольников), тонкие (окна,
вывески, панели) — цветным прямоугольником на внешней стороне (2 треугольника). Цвет — средний цвет вершин детали.
Всё обрезается габаритом прежнего силуэта: размер и центр детали не меняются, меш можно подменить на месте.
Цвет детали — преобладающий по площади (корзины по 1/6 канала), а не средний: средний красно-белых полос даёт
бледно-розовый, чёрно-белого — серый (так искажались CactusAcrobats и BlackCatIdol). Плоские пластины крупнее
трети стороны (и такие же коробки) не ставятся: это облицовка, которую основа силуэта уже передаёт своим цветом.
Грани разного цвета в одной плоскости (мерцание) не допускаются: добавка, легшая в плоскость основы, пластины или другой
коробки, сдвигается на STEP наружу или внутрь (или не ставится); такие же пары внутри самой основы разводит
unclash_base. У каждой грани свои вершины (Roblox хранит цвет на вершине).

Запуск: blender --background --factory-startup --python scripts/blender/lod_silhouette.py -- <папка> <Тема>...
Пишет <папка>/<Тема>Sil.fbx (один объект <prefix>_S_All) и <папка>/<Тема>Sil.json (треугольники, деталей).
Зависит только от bpy/bmesh; координаты этажа как в audit_floors.py: x = −x', y = z', z = y'."""

import json
import os
import sys

import bmesh
import bpy
from mathutils import Vector

FX, FZ = 18.12, 17.12
BUDGET = 400
MIN_SIZE = 1.2  # меньше — издалека не видно (стад ≈ пиксель с 250+)
THIN = 0.4  # тоньше — прямоугольник на внешней стороне
GAP = 0.15  # прямоугольник не ближе к основе — без мерцания издалека
MAX_QUAD = 0.33  # плоская пластина не больше трети стороны
MIN_FACE = 0.6  # видимая сторона уже — издалека штрих-шум (доски, рейки)
# Грани разного цвета в одной плоскости мерцают (две коробки соседних деталей фасада с общей передней гранью,
# коробка вровень со стеной основы). Такую грань сдвигаем на STEP наружу или внутрь — издалека сдвиг не виден.
STEP = 0.12  # шаг сдвига грани; ближе NEAR — считаем одной плоскостью
NEAR = 0.11
SAME_RGB = 0.02  # грани почти одного цвета (sRGB) в одной плоскости не мерцают заметно


def clip(subj, clipp):
    """Пересечение выпуклых многоугольников (обход против часовой), Сазерленд — Ходжмен."""

    def inside(p, a, b):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-9

    def cross(p, q, a, b):
        den = (p[0] - q[0]) * (a[1] - b[1]) - (p[1] - q[1]) * (a[0] - b[0])
        if abs(den) < 1e-12:
            return q
        t = ((p[0] - a[0]) * (a[1] - b[1]) - (p[1] - a[1]) * (a[0] - b[0])) / den
        return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))

    out = subj
    for i in range(len(clipp)):
        a, b = clipp[i - 1], clipp[i]
        inp, out = out, []
        if not inp:
            break
        s = inp[-1]
        for e in inp:
            if inside(e, a, b):
                if not inside(s, a, b):
                    out.append(cross(s, e, a, b))
                out.append(e)
            elif inside(s, a, b):
                out.append(cross(s, e, a, b))
            s = e
    return out


def area2(poly):
    return 0.5 * sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))


def ccw(poly):
    return poly if area2(poly) > 0 else poly[::-1]


class Planes:
    """Уже поставленные грани по осям этажа: (ось, сторона) → [(плоскость, многоугольник в двух других осях, цвет)]."""

    def __init__(self):
        self.faces = {}

    def add(self, ax, sg, plane, poly, rgb):
        self.faces.setdefault((ax, sg), []).append((plane, ccw(poly), rgb))

    def clash(self, ax, sg, plane, poly, rgb):
        poly = ccw(poly)
        for p, q, c in self.faces.get((ax, sg), ()):
            if abs(p - plane) >= NEAR or max(abs(c[k] - rgb[k]) for k in range(3)) < SAME_RGB:
                continue
            r = clip(poly, q)
            if len(r) >= 3 and abs(area2(r)) > 0.01:
                return True
        return False


def rect(lo, hi, ax):
    a, b = [i for i in range(3) if i != ax]
    return [(lo[a], lo[b]), (hi[a], lo[b]), (hi[a], hi[b]), (lo[a], hi[b])]


def game(v):
    return (-v.x, v.z, v.y)


def blender(x, y, z):
    return Vector((-x, z, y))


def islands(ob):
    """Связные куски меша детали фасада: габарит в осях этажа, площадь, средний цвет (по площади граней)."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.transform(ob.matrix_world)
    col = bm.loops.layers.color.get("Col") or (bm.loops.layers.color.values()[0] if bm.loops.layers.color else None)
    seen, out = set(), []
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        stack, faces = [f0], []
        seen.add(f0.index)
        while stack:
            f = stack.pop()
            faces.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        pts = [game(v.co) for f in faces for v in f.verts]
        lo = [min(p[i] for p in pts) for i in range(3)]
        hi = [max(p[i] for p in pts) for i in range(3)]
        area, bins = 0.0, {}
        for f in faces:
            a = f.calc_area()
            if col is not None:
                cs = [lp[col] for lp in f.loops]
                fc = tuple(sum(x[k] for x in cs) / len(cs) for k in range(3))
                key = tuple(int(v * 6) for v in fc)
                b = bins.setdefault(key, [0.0, 0.0, 0.0, 0.0])
                b[0] += a
                for k in range(3):
                    b[k + 1] += a * fc[k]
            area += a
        best = max(bins.values(), key=lambda b: b[0]) if bins else None
        if best and best[0] > 0:
            rgb = tuple(best[k + 1] / best[0] for k in range(3))
        else:
            continue  # кусок нулевой площади (вырожденные грани) — издалека не виден
        out.append({"lo": lo, "hi": hi, "area": area, "rgb": rgb})
    bm.free()
    return out


def unclash_base(bm):
    """Грани разного цвета в одной плоскости, оставшиеся после добавок (чаще — в самой основе, были и в прежнем
    силуэте): меньшую из пары сдвинуть туда, где она ни с кем не совпадает, — на 1–5 шагов STEP наружу или внутрь,
    не за габарит. Вершины уже разрезаны — грань двигается отдельно. Возвращает число сдвигов."""
    col = bm.loops.layers.color.get("Col") or (bm.loops.layers.color.values()[0] if bm.loops.layers.color else None)
    if col is None:
        return 0
    lo = [min(v.co[i] for v in bm.verts) for i in range(3)]
    hi = [max(v.co[i] for v in bm.verts) for i in range(3)]
    groups = {}
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        if abs(n[ax]) < 0.999 or f.calc_area() < 1e-4:
            continue
        a, b = [i for i in range(3) if i != ax]
        rec = {
            "f": f,
            "plane": f.verts[0].co[ax],
            "poly": ccw([(v.co[a], v.co[b]) for v in f.verts]),
            "rgb": tuple(sum(lp[col][k] for lp in f.loops) / len(f.loops) for k in range(3)),
            "area": f.calc_area(),
        }
        groups.setdefault((ax, 1 if n[ax] > 0 else -1), []).append(rec)

    def clashes(rec, plane, faces):
        for o in faces:
            if o is rec or abs(o["plane"] - plane) >= NEAR:
                continue
            if max(abs(o["rgb"][k] - rec["rgb"][k]) for k in range(3)) < SAME_RGB:
                continue
            r = clip(rec["poly"], o["poly"])
            if len(r) >= 3 and abs(area2(r)) > 0.01:
                return o
        return None

    moved = 0
    for (ax, sg), faces in groups.items():
        for _ in range(4):
            changed = False
            for rec in sorted(faces, key=lambda r: r["area"]):
                other = clashes(rec, rec["plane"], faces)
                if other is None:
                    continue
                f = rec if rec["area"] <= other["area"] else other  # двигается меньшая
                p = f["plane"]
                steps = [s * k for k in range(1, 6) for s in (1, -1)]  # ближние сначала, наружу раньше
                for cand in (p + sg * STEP * k for k in steps):
                    if not (lo[ax] + 0.05 < cand < hi[ax] - 0.05) or clashes(f, cand, faces):
                        continue
                    for v in f["f"].verts:
                        v.co[ax] += cand - p
                    f["plane"] = cand
                    moved += 1
                    changed = True
                    break
            if not changed:
                break
    return moved


def run(theme, src, out_dir):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=src, axis_forward="-Z", axis_up="Y")
    obs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    sil = next(o for o in obs if o.name.endswith("_S_All"))
    facade = [o for o in obs if "_F_" in o.name]
    sil.data.calc_loop_triangles()
    base_tris = len(sil.data.loop_triangles)
    spts = [game(sil.matrix_world @ v.co) for v in sil.data.vertices]
    blo = [min(p[i] for p in spts) for i in range(3)]
    bhi = [max(p[i] for p in spts) for i in range(3)]
    # верх стен основы: самая высокая точка основы над стенами (крыша) — внутри коробки стен ничего не добавляем
    cand = []
    for ob in facade:
        for isl in islands(ob):
            lo = [max(isl["lo"][i], blo[i]) for i in range(3)]
            hi = [min(isl["hi"][i], bhi[i]) for i in range(3)]
            d = [hi[i] - lo[i] for i in range(3)]
            if min(d) < 0 or max(d) < MIN_SIZE:
                continue
            inside = abs(lo[0]) < FX - 0.05 and abs(hi[0]) < FX - 0.05 and abs(lo[2]) < FZ - 0.05 and abs(hi[2]) < FZ - 0.05
            if inside and hi[1] < 18.95:
                continue  # внутри коробки стен силуэта (крыша, балки) — не видно
            if d[1] < THIN and hi[1] < 0.4:
                continue  # плоское у земли — дорожки, коврики: издалека не видно, а мерцает с землёй
            s = sorted(d)
            cand.append({"lo": lo, "hi": hi, "d": d, "score": s[1] * s[2], "rgb": isl["rgb"]})
    cand.sort(key=lambda c: -c["score"])
    # грани основы, перпендикулярные осям, — с ними добавки тоже не должны совпадать плоскостью
    planes = Planes()
    mw, me0 = sil.matrix_world, sil.data
    bcol = me0.color_attributes.active_color or (me0.color_attributes[0] if me0.color_attributes else None)
    for tri in me0.loop_triangles:
        n = game(mw.to_3x3() @ tri.normal)
        ax = max(range(3), key=lambda i: abs(n[i]))
        if abs(n[ax]) < 0.999 * Vector(n).length:
            continue
        ps = [game(mw @ me0.vertices[v].co) for v in tri.vertices]
        if bcol is None:
            rgb = (1.0, 1.0, 1.0)
        else:
            # sRGB, как цвета деталей фасада из bmesh
            cs = [(bcol.data[li] if bcol.domain == "CORNER" else bcol.data[me0.loops[li].vertex_index]).color_srgb for li in tri.loops]
            rgb = tuple(sum(c[k] for c in cs) / 3 for k in range(3))
        a, b = [i for i in range(3) if i != ax]
        poly = [(p[a], p[b]) for p in ps]
        if abs(area2(poly)) > 1e-6:
            planes.add(ax, 1 if n[ax] > 0 else -1, ps[0][ax], poly, rgb)
    bm = bmesh.new()
    col = bm.loops.layers.color.new("Col")
    used, quads, boxes, moved, dropped = base_tris, [], 0, 0, 0
    picked = []

    def face(pts, rgb):
        f = bm.faces.new([bm.verts.new(p) for p in pts])
        for lp in f.loops:
            lp[col] = (rgb[0], rgb[1], rgb[2], 1.0)

    for c in cand:
        lo, hi, d = c["lo"], c["hi"], c["d"]
        thin = min(range(3), key=lambda i: d[i])
        if d[thin] < THIN and thin != 1:
            if used + 2 > BUDGET:
                continue
            a_, b_ = [i for i in range(3) if i != thin]
            if min(d[a_], d[b_]) < MIN_FACE:
                continue
            side = (2 * (FZ if thin == 0 else FX)) * (bhi[1] - blo[1])
            if d[a_] * d[b_] > MAX_QUAD * side:
                continue  # облицовка во всю стену — основа силуэта её уже передаёт
            # внешняя сторона — дальше от центра этажа по тонкой оси
            sign = 1 if (lo[thin] + hi[thin]) > 0 else -1
            depth = hi[thin] if sign > 0 else lo[thin]
            wall = FX if thin == 0 else FZ
            depth = sign * max(abs(depth), wall + GAP)
            for q in quads:  # почти в одной плоскости с уже взятым и перекрываются — чуть дальше наружу
                if q[0] == thin and q[1] == sign and abs(q[2] - depth) < 0.12:
                    o = [i for i in range(3) if i != thin]
                    if all(lo[i] < q[4][i] and hi[i] > q[3][i] for i in o):
                        depth = q[2] + sign * 0.12
            lim = bhi[thin] if sign > 0 else -blo[thin]
            qpoly = rect(lo, hi, thin)
            for _ in range(4):  # в плоскости грани другого цвета (коробка, основа) — дальше наружу
                if abs(depth) > lim - 0.05 or not planes.clash(thin, sign, depth, qpoly, c["rgb"]):
                    break
                depth += sign * STEP
                moved += 1
            if abs(depth) > lim - 0.05:  # не за габарит прежнего силуэта и не в плоскость его крайней грани
                continue
            if planes.clash(thin, sign, depth, qpoly, c["rgb"]):
                dropped += 1
                continue
            planes.add(thin, sign, depth, qpoly, c["rgb"])
            quads.append((thin, sign, depth, lo, hi))
            a, b = [i for i in range(3) if i != thin]
            corners = [(lo[a], lo[b]), (hi[a], lo[b]), (hi[a], hi[b]), (lo[a], hi[b])]
            pts = []
            for u, v in corners:
                p = [0.0, 0.0, 0.0]
                p[thin], p[a], p[b] = depth, u, v
                pts.append(blender(*p))
            n = Vector((0, 0, 0))
            nn = [0.0, 0.0, 0.0]
            nn[thin] = sign
            n = blender(*nn)
            fn = (pts[1] - pts[0]).cross(pts[2] - pts[0])
            face(pts if fn.dot(n) > 0 else list(reversed(pts)), c["rgb"])
            used += 2
            picked.append(("q", [round(v, 1) for v in lo], [round(v, 1) for v in hi], [round(v, 2) for v in c["rgb"]]))
        else:
            if used + 10 > BUDGET:
                continue
            cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
            out_ax = 0 if abs(cx) / FX > abs(cz) / FZ else 2
            other = 2 if out_ax == 0 else 0
            if min(d[other], d[1]) < MIN_FACE:
                continue
            side = (2 * (FZ if out_ax == 0 else FX)) * (bhi[1] - blo[1])
            if d[other] * d[1] > MAX_QUAD * side:
                continue  # стена-облицовка коробкой перекрыла бы цвет основы (CactusAcrobats)
            if hi[1] - lo[1] < 0.15:
                continue  # плоская горизонтальная пластина: вырожденная коробка мерцает, утолщённая — штрих-шум
            # видимые грани коробки (верх и четыре стороны) не в плоскости граней другого цвета: сдвиг на STEP
            # наружу (не за габарит прежнего силуэта) или внутрь (коробка не тоньше 0.15)
            lo, hi = list(lo), list(hi)
            sides5 = [(1, 1), (0, 1), (0, -1), (2, 1), (2, -1)]
            ok = True
            for ax, sg in sides5:
                cur = hi if sg > 0 else lo
                base_p = cur[ax]
                tries = [base_p + sg * STEP * k for k in (1, 2)] + [base_p - sg * STEP * k for k in (1, 2)]
                if not planes.clash(ax, sg, base_p, rect(lo, hi, ax), c["rgb"]):
                    continue
                for p in tries:
                    if sg > 0 and (p > bhi[ax] - 0.05 or p - lo[ax] < 0.15):
                        continue
                    if sg < 0 and (p < blo[ax] + 0.05 or hi[ax] - p < 0.15):
                        continue
                    cur[ax] = p
                    if not planes.clash(ax, sg, p, rect(lo, hi, ax), c["rgb"]):
                        moved += 1
                        break
                    cur[ax] = base_p
                else:
                    ok = False
                    break
            if ok:  # сдвиг одной грани меняет края соседних — проверить все пять ещё раз
                ok = not any(planes.clash(ax, sg, (hi if sg > 0 else lo)[ax], rect(lo, hi, ax), c["rgb"]) for ax, sg in sides5)
            if not ok:
                dropped += 1
                continue
            for ax, sg in sides5:
                planes.add(ax, sg, (hi if sg > 0 else lo)[ax], rect(lo, hi, ax), c["rgb"])
            x0, y0, z0 = lo
            x1, y1, z1 = hi
            v = {(i, j, k): blender((x0, x1)[i], (y0, y1)[j], (z0, z1)[k]) for i in (0, 1) for j in (0, 1) for k in (0, 1)}
            sides = [((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1), (0, 1, 0)),  # верх
                     ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0), (-1, 0, 0)), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1), (1, 0, 0)),
                     ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, -1)), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1), (0, 0, 1))]
            centre = blender((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
            for s in sides:
                pts = [v[k] for k in s[:4]]
                mid = sum(pts, Vector()) / 4
                fn = (pts[1] - pts[0]).cross(pts[2] - pts[0])
                face(pts if fn.dot(mid - centre) > 0 else list(reversed(pts)), c["rgb"])
            used += 10
            boxes += 1
            picked.append(("b", [round(v, 1) for v in lo], [round(v, 1) for v in hi], [round(v, 2) for v in c["rgb"]]))
    me = bpy.data.meshes.new("add")
    bm.to_mesh(me)
    bm.free()
    add = bpy.data.objects.new("add", me)
    bpy.context.scene.collection.objects.link(add)
    # основа — в мировые координаты, затем присоединить добавки (цвет «Col» у обеих)
    bpy.ops.object.select_all(action="DESELECT")
    sil.select_set(True)
    bpy.context.view_layer.objects.active = sil
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if "Col" not in sil.data.color_attributes:
        sil.data.color_attributes[0].name = "Col"
    add.select_set(True)
    bpy.ops.object.join()
    for o in list(bpy.context.scene.objects):
        if o is not sil:
            bpy.data.objects.remove(o)
    # у каждой грани — свои вершины: Roblox хранит цвет на вершине, и общая вершина граней разного цвета
    # красит грань не в её цвет (так передняя стена CactusAcrobats стала серой)
    bm2 = bmesh.new()
    bm2.from_mesh(sil.data)
    bmesh.ops.split_edges(bm2, edges=bm2.edges[:])
    base_moved = unclash_base(bm2)
    bm2.to_mesh(sil.data)
    bm2.free()
    sil.data.calc_loop_triangles()
    tris = len(sil.data.loop_triangles)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, theme + "Sil.fbx")
    bpy.ops.object.select_all(action="DESELECT")
    sil.select_set(True)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP", colors_type="SRGB")
    pts = [game(v.co) for v in sil.data.vertices]
    nlo = [round(min(p[i] for p in pts), 3) for i in range(3)]
    nhi = [round(max(p[i] for p in pts), 3) for i in range(3)]
    info = {"theme": theme, "name": sil.name, "base_tris": base_tris, "tris": tris, "boxes": boxes, "quads": len(quads),
            "moved": moved, "dropped": dropped, "base_moved": base_moved, "bbox_old": [blo, bhi], "bbox_new": [nlo, nhi],
            "picked": picked}
    with open(os.path.join(out_dir, theme + "Sil.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False)
    print("SIL", json.dumps(info), flush=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    out, themes = argv[0], argv[1:]
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    for t in themes:
        try:
            run(t, os.path.join(repo, "assets", "models", "floors", t + "Floor.fbx"), out)
        except Exception as e:  # один этаж не останавливает остальные; ошибка видна в журнале
            print("SILFAIL", t, repr(e), flush=True)

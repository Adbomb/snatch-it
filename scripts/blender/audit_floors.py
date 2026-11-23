"""Аудит готовых этажей по FBX (assets/models/floors/<Theme>Floor.fbx): мерцание (совпадающие или почти совпадающие
грани, смотрящие в одну сторону, у разных треугольников), вылеты (вещи зала снаружи фасада, фасад внутри зала, вещи
за краем площадки), тонкие «висящие» детали не ловит — только геометрию.
Запуск: blender --background --factory-startup --python scripts/blender/audit_floors.py -- <out.json> <Theme> [<Theme> …]
Зависит только от bpy. Координаты этажа: x = −X Blender, y = Z Blender, z = Y Blender (floorkit.P)."""

import json
import math
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

FX, FZ, W, ZB, ZF, C = 18.12, 17.12, 16.88, 15.88, -15.88, 18.0
GAP = 0.012  # грани ближе этого и смотрящие в одну сторону мерцают
NQ = 0.02  # квантование нормали
DQ = 0.02  # квантование смещения плоскости


def tri_area(a, b):
    return 0.5 * abs(a[0] * b[1] - a[1] * b[0])


def poly_area(p):
    s = 0.0
    for i in range(len(p)):
        x0, y0 = p[i]
        x1, y1 = p[(i + 1) % len(p)]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2


def clip(subject, clipper):
    """Пересечение выпуклых многоугольников (Сазерленд — Ходжман); clipper — против часовой."""
    out = subject
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        inp, out = out, []
        if not inp:
            break

        def inside(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-9

        def inter(p, q):
            x1, y1, x2, y2 = a[0], a[1], b[0], b[1]
            x3, y3, x4, y4 = p[0], p[1], q[0], q[1]
            den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(den) < 1e-12:
                return q
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
            return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            if inside(q):
                if not inside(p):
                    out.append(inter(p, q))
                out.append(q)
            elif inside(p):
                out.append(inter(p, q))
    return out


def ccw(t):
    a, b, c = t
    if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) < 0:
        return [a, c, b]
    return [a, b, c]


def audit(theme, path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path, axis_forward="-Z", axis_up="Y")
    tris = []  # (obj, verts3 floor coords, normal)
    bounds = {"interior_outside": [], "facade_inside": [], "off_platform": [], "floating": []}
    allv, allp = [], []
    tri_isl, islands = [], []  # остров (связная деталь) каждого треугольника; острова фасада снаружи здания
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or ob.name.endswith("_S_All"):
            continue
        me = ob.data
        me.calc_loop_triangles()
        mw = ob.matrix_world
        vs = [mw @ v.co for v in me.vertices]
        fl = [(-v.x, v.z, v.y) for v in vs]
        interior = "_I_" in ob.name
        base = len(allv)
        allv += fl
        par = list(range(len(fl)))

        def root(i):
            while par[i] != i:
                par[i] = par[par[i]]
                i = par[i]
            return i

        first = {}
        for i, q in enumerate(fl):
            key = (round(q[0], 3), round(q[1], 3), round(q[2], 3))
            if key in first:
                par[root(i)] = root(first[key])
            else:
                first[key] = i
        for poly in me.polygons:
            for a in poly.vertices[1:]:
                par[root(a)] = root(poly.vertices[0])
        isl_of = {}
        for i in range(len(fl)):
            r = root(i)
            if r not in isl_of:
                isl_of[r] = len(islands)
                islands.append({"part": ob.name, "pts": [], "facade": not interior})
            islands[isl_of[r]]["pts"].append(fl[i])
        big = set()
        for lt in me.loop_triangles:
            allp.append([base + i for i in lt.vertices])
            tri_isl.append(isl_of[root(lt.vertices[0])])
            if lt.area > 0.01:
                big.update(lt.vertices)
        for i in sorted(big):
            x, y, z = fl[i]
            if interior and (abs(x) > FX + 0.05 or abs(z) > FZ + 0.05) and y > 0.05:
                bounds["interior_outside"].append((ob.name, round(x, 2), round(y, 2), round(z, 2)))
            if not interior and abs(x) < W - 0.95 and ZF + 0.95 < z < ZB - 0.95 and 0.2 < y < C - 0.2:
                bounds["facade_inside"].append((ob.name, round(x, 2), round(y, 2), round(z, 2)))
            if not interior and (abs(x) > FX + 2.95 or abs(z) > FZ + 2.95):
                bounds["off_platform"].append((ob.name, round(x, 2), round(y, 2), round(z, 2)))
        ca = me.color_attributes[0] if me.color_attributes else None

        def tcol(lt):
            if ca is None:
                return (1.0, 1.0, 1.0)
            if ca.domain == "CORNER":
                cs = [ca.data[i].color for i in lt.loops]
            else:
                cs = [ca.data[i].color for i in lt.vertices]
            return tuple(sum(c[k] for c in cs) / 3 for k in range(3))

        for lt in me.loop_triangles:
            p = [fl[i] for i in lt.vertices]
            ux, uy, uz = p[1][0] - p[0][0], p[1][1] - p[0][1], p[1][2] - p[0][2]
            vx, vy, vz = p[2][0] - p[0][0], p[2][1] - p[0][1], p[2][2] - p[0][2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            ln = math.sqrt(nx * nx + ny * ny + nz * nz)
            if ln < 1e-8:
                continue
            n = (nx / ln, ny / ln, nz / ln)
            if ln / 2 < 0.002:
                continue
            tris.append((ob.name, p, n, tcol(lt)))
    bvh = BVHTree.FromPolygons([Vector(v) for v in allv], allp, epsilon=0.0)
    # висящие в воздухе детали: стоящая у земли деталь (низ ниже 0.4) снаружи стен, под которой луч вниз
    # не находит ни земли, ни другой детали до y = -1.25
    for k, isl in enumerate(islands):
        if not isl["facade"]:
            continue
        pts = isl["pts"]
        bottom = min(q[1] for q in pts)
        height = max(q[1] for q in pts) - bottom
        if not -0.3 < bottom < 0.4 or (height < 0.02 and bottom < -0.05):
            continue  # не у земли или сама плоскость земли
        mx, mz = sum(q[0] for q in pts) / len(pts), sum(q[2] for q in pts) / len(pts)
        low = {(round(q[0], 2), round(q[2], 2)): q for q in pts
               if q[1] < bottom + 0.05 and (abs(q[0]) > FX + 0.05 or abs(q[2]) > FZ + 0.05)}
        if not low:
            continue
        miss = 0
        low = {k: q for k, q in low.items() if abs(q[0]) > FX + 2.98 or abs(q[2]) > FZ + 2.98}  # за краем земли этажа
        if not low:
            continue  # на земле этажа (грань земли под деталью вырезана как скрытая — луч её не видит)
        for q in list(low.values())[:40]:
            dx, dz = mx - q[0], mz - q[2]
            dl = max(math.hypot(dx, dz), 1e-6)
            sx, sz = q[0] + dx / dl * min(0.05, dl), q[2] + dz / dl * min(0.05, dl)  # чуть внутрь — мимо рёбер
            o = Vector((sx, bottom + 0.15, sz))
            left = o[1] + 1.25
            while True:
                hit = bvh.ray_cast(o, Vector((0, -1, 0)), left)
                if hit[0] is None:
                    miss += 1
                    break
                if tri_isl[hit[2]] != k:
                    break
                left -= (o - hit[0]).length + 0.002
                o = hit[0] + Vector((0, -0.002, 0))
                if left <= 0:
                    miss += 1
                    break
        if miss * 2 > min(len(low), 40):
            xs, ys, zs = [q[0] for q in pts], [q[1] for q in pts], [q[2] for q in pts]
            bounds["floating"].append((isl["part"], round((min(xs) + max(xs)) / 2, 1), round(bottom, 2),
                                       round((min(zs) + max(zs)) / 2, 1),
                                       [round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1), round(max(zs) - min(zs), 1)]))

    def open_front(c, n):
        """Перед гранью есть свободное место (камера может её видеть): луч по нормали не упирается ближе 0.6."""
        o = Vector(c) + Vector(n) * 0.03
        x, y, z = o
        inside = abs(x) < FX + 0.02 and abs(z) < FZ + 0.02
        if inside and (y < -0.02 or C + 0.02 < y < 19.0):
            return False  # в перекрытии
        if inside and -0.02 < y < 19.0 and (abs(x) > W - 0.02 or z < ZF + 0.02 or z > ZB - 0.02):
            if not (z > ZB - 0.02 and abs(x) < 3.6 and y < 10.6):  # проём лифта
                return False  # в толще стены (её заполняет каркас Kit.Wall)
        if y < -0.85 and n[1] < -0.5:
            return False  # низ площадки лежит на этаже ниже
        if y > 18.85 and n[1] > 0.5:
            return False  # верх крыши закрыт этажом выше
        if not inside:  # грань снаружи, смотрит на здание и стоит у стены — щель шире камеры не бывает
            for i, lim in ((0, FX), (2, FZ)):
                if abs(n[i]) > 0.7 and o[i] * n[i] < 0 and abs(o[i]) - lim < 2.0:
                    other = 2 - i
                    if abs(o[other]) < (FZ if i == 0 else FX) + 0.3:
                        return False
        hit = bvh.ray_cast(o, Vector(n), 1.0)
        return hit[0] is None

    buckets = {}
    for idx, (name, p, n, _c) in enumerate(tris):
        d = n[0] * p[0][0] + n[1] * p[0][1] + n[2] * p[0][2]
        key = (round(n[0] / NQ), round(n[1] / NQ), round(n[2] / NQ), round(d / DQ))
        buckets.setdefault(key, []).append((idx, d))
    seen = set()
    hits = []
    for key, items in buckets.items():
        cand = list(items)
        nk = (key[0], key[1], key[2], key[3] + 1)
        if nk in buckets:
            cand += buckets[nk]
        if len(cand) < 2:
            continue
        n = tris[cand[0][0]][2]
        ax = max(range(3), key=lambda i: abs(n[i]))
        u, v = [i for i in range(3) if i != ax]
        proj = []
        for idx, d in cand:
            pts = [(q[u], q[v]) for q in tris[idx][1]]
            xs, ys = [q[0] for q in pts], [q[1] for q in pts]
            proj.append((min(xs), max(xs), min(ys), max(ys), idx, d, ccw(pts)))
        proj.sort()
        for i in range(len(proj)):
            a = proj[i]
            for j in range(i + 1, len(proj)):
                b = proj[j]
                if b[0] >= a[1] - 1e-6:
                    break
                if b[2] >= a[3] - 1e-6 or a[2] >= b[3] - 1e-6:
                    continue
                if abs(a[5] - b[5]) > GAP:
                    continue
                pair = (min(a[4], b[4]), max(a[4], b[4]))
                if pair in seen:
                    continue
                seen.add(pair)
                inter = clip(a[6], b[6])
                if len(inter) < 3:
                    continue
                ar = poly_area(inter)
                if ar < 0.01:
                    continue
                cx = sum(q[0] for q in inter) / len(inter)
                cy = sum(q[1] for q in inter) / len(inter)
                c3 = [0.0, 0.0, 0.0]
                c3[u], c3[v], c3[ax] = cx, cy, tris[a[4]][1][0][ax]
                if not open_front(c3, n):
                    continue
                ca_, cb_ = tris[a[4]][3], tris[b[4]][3]
                dc = max(abs(ca_[k] - cb_[k]) for k in range(3))
                hits.append({"a": tris[a[4]][0], "b": tris[b[4]][0], "area": round(ar, 3), "gap": round(abs(a[5] - b[5]), 4),
                             "dc": round(dc, 3),
                             "at": [round(c, 1) for c in c3], "n": [round(c, 2) for c in n]})
    # сгруппировать попадания по 1-стадовым ячейкам
    clusters = {}
    for h in hits:
        k = (round(h["at"][0]), round(h["at"][1]), round(h["at"][2]), h["a"], h["b"])
        c = clusters.setdefault(k, {"at": h["at"], "a": h["a"], "b": h["b"], "area": 0.0, "n": h["n"], "count": 0, "dc": 0.0})
        c["dc"] = max(c["dc"], h["dc"])
        c["area"] = round(c["area"] + h["area"], 3)
        c["count"] += 1
    cl = sorted(clusters.values(), key=lambda c: -c["area"])
    strong = [h for h in hits if h["dc"] > 0.06]
    return {"theme": theme, "tris": len(tris), "zfight_area": round(sum(h["area"] for h in hits), 2), "zfight_pairs": len(hits),
            "strong_area": round(sum(h["area"] for h in strong), 2), "strong_pairs": len(strong),
            "clusters": cl[:60], "bounds": {k: v[:40] for k, v in bounds.items()},
            "bounds_count": {k: len(v) for k, v in bounds.items()}}


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    out, themes = argv[0], argv[1:]
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    res = {}
    for t in themes:
        res[t] = audit(t, os.path.join(repo, "assets", "models", "floors", t + "Floor.fbx"))
        print("AUDIT", t, res[t]["zfight_area"], res[t]["strong_area"], res[t]["bounds_count"], flush=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

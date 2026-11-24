"""Проверка суставов подвижной модели (правила анатомии D64): щели между частью и её родителем и «летающие» детали.

- Щель в суставе: часть не касается родителя (тело на подставке — подставки или ноги, стоящей на подставке):
  наименьшее расстояние от её поверхности до поверхности родителя больше порога (по умолчанию 0.05 стада) и ни одна
  её вершина не лежит внутри родителя. В анимации такая часть «отрывается».
- Сустав раскрывается (check_bends): вокруг точки вращения есть пустота — сгиб виден щелью при повороте.
- Летающая деталь: связный кусок меша (остров) внутри части, который ни с чем не соприкасается — ни с другими
  островами своей части, ни с другими частями (дальше порога).
- Точка вращения вдали от сустава: от точки вращения до ближайшей поверхности части или родителя больше 0.5 стада —
  при повороте часть уезжает от места крепления.
Модели в позе покоя; объекты частей — в мировых координатах (matrix_world). Порог задаётся в единицах модели
(у существ 1 = 1 стад, у босса 5 — 1 / 2.03 стада).
Подключается: from joint_check import check_bends, check_joints; check_joints(parts, rig, gap=0.05, pivot_far=0.5).
"""

import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _world_bm(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return bm


def _inside(tree, p, limit=64):
    """Точка внутри замкнутой поверхности: нечётное число пересечений луча (+x с небольшим наклоном)."""
    d = Vector((1.0, 0.0137, 0.0071)).normalized()
    n, q = 0, Vector(p)
    for _ in range(limit):
        hit = tree.ray_cast(q, d)
        if hit[0] is None:
            break
        n += 1
        q = hit[0] + d * 1e-4
    return n % 2 == 1


def _islands(bm):
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, isl = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        out.append(isl)
    return out


def _min_dist(points, tree):
    best = float("inf")
    for p in points:
        hit = tree.find_nearest(p)
        if hit[0] is not None:
            best = min(best, hit[3])
    return best


def check_joints(parts, rig, gap=0.05, pivot_far=0.5):
    """parts — {часть: объект}, rig — {часть: (родитель, точка вращения)}. Возвращает список проблем (словари)."""
    bms = {n: _world_bm(o) for n, o in parts.items() if len(o.data.polygons)}
    trees = {n: BVHTree.FromBMesh(bm) for n, bm in bms.items()}
    issues = []
    for n, (parent, pivot) in rig.items():
        if n not in bms:
            continue
        pts = [v.co for v in bms[n].verts] + [f.calc_center_median() for f in bms[n].faces]
        if parent and parent in trees:
            d = _min_dist(pts, trees[parent])
            if d > gap and rig.get(parent, (None,))[0] is None:
                # часть на подставке стоит на ногах (своих детях или соседях на той же подставке): касание через
                # ногу, которая касается подставки, — не щель
                for c, (cp, _) in rig.items():
                    if c != n and cp in (n, parent) and c in trees and                             _min_dist([v.co for v in bms[c].verts], trees[parent]) <= gap:
                        d = min(d, _min_dist(pts, trees[c]))
            if d > gap and not any(_inside(trees[parent], p) for p in pts[:: max(1, len(pts) // 40)]):
                issues.append({"kind": "щель в суставе", "part": n, "parent": parent, "gap": round(d, 3)})
            pv = Vector(pivot)
            dp = min(trees[n].find_nearest(pv)[3], trees[parent].find_nearest(pv)[3])
            if dp > pivot_far:
                issues.append({"kind": "точка вращения вдали от сустава", "part": n, "dist": round(dp, 3)})
        # летающие острова: не касаются ни других островов части, ни других частей
        isl = _islands(bms[n])
        if len(isl) < 2 and parent:
            continue
        others = [t for m, t in trees.items() if m != n]
        for k, faces in enumerate(isl):
            ipts = [v.co for f in faces for v in f.verts] + [f.calc_center_median() for f in faces]
            rest = [f for j, fs in enumerate(isl) if j != k for f in fs]
            near = float("inf")
            if rest:
                tb = bmesh.new()
                vmap = {}
                for f in rest:
                    vs = []
                    for v in f.verts:
                        if v.index not in vmap:
                            vmap[v.index] = tb.verts.new(v.co)
                        vs.append(vmap[v.index])
                    try:
                        tb.faces.new(vs)
                    except ValueError:
                        pass
                near = min(near, _min_dist(ipts, BVHTree.FromBMesh(tb)))
                tb.free()
            for t in others:
                if near <= gap:
                    break
                near = min(near, _min_dist(ipts, t))
            if near > gap and any(_inside(t, ipts[0]) for t in others):
                near = 0.0  # остров целиком внутри другой части — не летает
            if near > gap:
                c = sum((p for p in ipts), Vector()) / len(ipts)
                issues.append({"kind": "летающая деталь", "part": n, "gap": round(near, 3),
                               "at": [round(x, 2) for x in c]})
    for bm in bms.values():
        bm.free()
    return issues


def _enclosed(tree, p):
    """Точка внутри (у сложенных из пересекающихся тел частей чётность не работает): лучи во все 6 сторон упираются
    в поверхность части."""
    for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        if tree.ray_cast(p, Vector(d))[0] is None:
            return False
    return True


def check_bends(parts, rig, frac=0.12, min_r=0.05):
    """Раскрытие сгиба: точки на сфере вокруг точки вращения (радиус — до ближайшей поверхности части или родителя)
    должны лежать внутри части или родителя. Доля точек снаружи больше frac — сустав раскрывается (щель на сгибе)."""
    bms = {n: _world_bm(o) for n, o in parts.items() if len(o.data.polygons)}
    trees = {n: BVHTree.FromBMesh(bm) for n, bm in bms.items()}
    dirs = []
    n_dirs = 60
    for i in range(n_dirs):
        z = 1 - 2 * (i + 0.5) / n_dirs
        r = (1 - z * z) ** 0.5
        a = 2.399963 * i
        dirs.append(Vector((r * __import__("math").cos(a), r * __import__("math").sin(a), z)))
    issues = []
    for n, (parent, pivot) in rig.items():
        if not parent or n not in trees or parent not in trees or rig.get(parent, (None,))[0] is None:
            continue  # части на подставке не сгибаются относительно неё
        pv = Vector(pivot)
        if not (_enclosed(trees[n], pv) or _enclosed(trees[parent], pv)):
            continue  # ось вне частей — это ловит check_joints («точка вращения вдали от сустава»)
        r = max(min(trees[n].find_nearest(pv)[3], trees[parent].find_nearest(pv)[3]) * 0.9, min_r)
        out = sum(1 for d in dirs if not (_enclosed(trees[n], pv + d * r) or _enclosed(trees[parent], pv + d * r)))
        if out / n_dirs > frac:
            issues.append({"kind": "сустав раскрывается", "part": n, "parent": parent, "share": round(out / n_dirs, 2)})
    for bm in bms.values():
        bm.free()
    return issues

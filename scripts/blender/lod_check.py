"""Проверка дальних силуэтов этажей: прежний <prefix>_S_All (из FBX этажа) против нового <Тема>Sil.fbx.

Считает для каждого этажа:
- пары граней разного цвета (sRGB, разница ≥ 0.03) в одной плоскости и с одной стороной, перекрытые больше 0.01 кв.
  стада, — такие грани мерцают (вертикальные и горизонтальные отдельно);
- вершины, треугольники и «вершины для видеокарты» (уникальные вершина + нормаль грани + цвет).
Запуск: blender --background --factory-startup --python scripts/blender/lod_check.py -- <out.json> <Тема>...
Пишет <out.json> и итог строкой LODCHECK. Зависит только от bpy; пути — от корня репозитория."""

import io
import json
import os
import sys

import bpy

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FLOORS = os.path.join(REPO, "assets", "models", "floors")
LOD = os.path.join(REPO, "assets", "models", "floors_lod")
SAME_RGB = 0.03


def clip(subj, clipp):
    """Пересечение выпуклых многоугольников (против часовой), Сазерленд — Ходжмен."""

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


def area(poly):
    return 0.5 * sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))


def ccw(poly):
    return poly if area(poly) > 0 else poly[::-1]


def check(o):
    m, mw = o.data, o.matrix_world
    m.calc_loop_triangles()
    col = m.color_attributes.active_color
    planes, gpu = {}, set()
    for tri in m.loop_triangles:
        if col is None:
            cc = [(1.0, 1.0, 1.0)]
        elif col.domain == "CORNER":
            cc = [col.data[li].color_srgb for li in tri.loops]
        else:
            cc = [col.data[v].color_srgb for v in tri.vertices]
        rgb = tuple(sum(c[k] for c in cc) / len(cc) for k in range(3))
        nr = tuple(round(x, 3) for x in tri.normal)
        for li, v in zip(tri.loops, tri.vertices):
            c = col.data[li if col.domain == "CORNER" else v].color_srgb if col else (1, 1, 1)
            gpu.add((v, nr, tuple(round(x, 3) for x in c[:3])))
        n = (mw.to_3x3() @ tri.normal).normalized()
        ax = max(range(3), key=lambda i: abs(n[i]))
        if abs(n[ax]) < 0.999:
            continue
        vs = [mw @ m.vertices[v].co for v in tri.vertices]
        u, w = [i for i in range(3) if i != ax]
        poly = ccw([(v[u], v[w]) for v in vs])
        if abs(area(poly)) >= 1e-6:
            planes.setdefault((ax, n[ax] > 0, round(vs[0][ax], 2)), []).append((poly, rgb))
    r = {"vert": 0, "vert_area": 0.0, "horiz": 0, "verts": len(m.vertices), "tris": len(m.loop_triangles),
         "gpu_verts": len(gpu)}
    for (ax, _sg, _c), polys in planes.items():
        for i in range(len(polys)):
            for j in range(i + 1, len(polys)):
                (pa, ca), (pb, cb) = polys[i], polys[j]
                if max(abs(ca[k] - cb[k]) for k in range(3)) < SAME_RGB:
                    continue
                c = clip(pa, pb)
                if len(c) >= 3 and abs(area(c)) > 0.01:
                    if ax == 2:  # Blender Z — вертикаль игры: горизонтальные грани
                        r["horiz"] += 1
                    else:
                        r["vert"] += 1
                        r["vert_area"] = round(max(r["vert_area"], abs(area(c))), 3)
    return r


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    return [o for o in bpy.data.objects if o.type == "MESH"]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    out, themes = argv[0], argv[1:]
    res = {}
    for t in themes:
        ids = json.load(io.open(os.path.join(FLOORS, t + "Floor.ids.json"), encoding="utf-8"))
        pre = [k for k in ids["meshes"] if k.endswith("_S_All")][0]
        old = [o for o in load(os.path.join(FLOORS, t + "Floor.fbx")) if o.name.startswith(pre)][0]
        res[t] = {"old": check(old), "new": check(load(os.path.join(LOD, t + "Sil.fbx"))[0])}
    json.dump(res, io.open(out, "w", encoding="utf-8"), indent=0)
    keys = ("vert", "horiz", "tris", "gpu_verts")
    total = {s: {k: sum(v[s][k] for v in res.values()) for k in keys} for s in ("old", "new")}
    print("LODCHECK", len(res), json.dumps(total), flush=True)


if __name__ == "__main__":
    main()

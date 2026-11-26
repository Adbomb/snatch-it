"""Лист Б v3 (D74): органические редкие этажи в микро-вокселях поверх сцен floor_rarity_v3.py.

Решения владельца 2026-11-26: блоки — «кубики» текстурой (voxelkit); Мифический и Космический лепятся органически, как
у слизня, внутри правил модуля (плиты снизу и сверху ровные, след по сетке, CHECK_TOP, кант); этаж сливается со своим
существом: салун Кактуса-боксёра — дом, выросший внутри огромного кактуса (рёбра с колючками, врезанные окна и дверь
салуна, перчатка сбоку, лицо на фасаде); океанариум Верблюда-аквариума — этаж-верблюд (горбы-аквариумы с рыбами,
иллюминаторы в боках, морда на фасаде). Мифический — органика проступает сквозь здание D39, Космический — существо-дом
целиком. Золотой — атриум, за стеклом жилец (существо этажа) в микро-вокселях. Палитра темы с переходами (свет
запечён), блики на выпуклостях, светящиеся акценты (окна, цветки, фонарь, вода) — не неон-полосы.

Запуск (папка <v3> — прогоны floor_rarity_v3.py: <тема>_base.blend):
  blender -b --factory-startup --python scripts/blender/floor_organic_v3.py -- <репо> <v3> saloon
  blender -b --factory-startup --python scripts/blender/floor_organic_v3.py -- <репо> <v3> aquarium
  blender -b --factory-startup --python scripts/blender/floor_organic_v3.py -- <репо> <v3> tower
Только концепт: в игру не экспортируется.
"""

import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import floorkit as K  # noqa: E402
import voxelkit as V  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT, MODE = os.path.abspath(argv[0]), os.path.abspath(argv[1]), argv[2]
X, Z = 18.12, 17.12
H = [20, 27, 32, 38, 46, 60]
SLAB = 2.6
NAMES = ["Деревянный", "Каменный", "Мраморный", "Золотой", "Мифический", "Космический"]
STEP, RES_STEP, FAR = 0.5, 0.25, 2.0
FIXED = {"glow": "FFE07A", "glassw": "FFD27A", "frame": "6B4524", "door": "4A2E18", "aqua": "62D6EA",
         "brass": "1F6F7A", "white": "F6F4EE", "black": "1C1C1C", "fish": "FF8A3D", "pink": "FF6FA8"}
GLOW = ("glow", "glassw", "aqua")


def band_top(tier):
    return -1 + H[tier - 1] - SLAB


def boxes_mesh(name, items, color_hex, coll, fixed=None, bake=False):
    """Много мелких брусков одним мешем (колючки, зубы): items — (центр игры, полуразмер игры)."""
    verts, faces = [], []
    for (cx, cy, cz), (hx, hy, hz) in items:
        k = len(verts)
        for dx in (-1, 1):
            for dy in (-1, 1):
                for dz in (-1, 1):
                    verts.append(tuple(K.P(cx + dx * hx, cy + dy * hy, cz + dz * hz)))
        faces += [(k, k + 1, k + 3, k + 2), (k + 4, k + 6, k + 7, k + 5), (k, k + 4, k + 5, k + 1),
                  (k + 2, k + 3, k + 7, k + 6), (k, k + 2, k + 6, k + 4), (k + 1, k + 5, k + 7, k + 3)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    m = bpy.data.materials.new(name + "_M")
    m.use_nodes = True
    next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (
        *V.srgb2lin(V.hex_rgb(color_hex)), 1)
    me.materials.append(m)
    if fixed:
        o["fixed"] = fixed
    if bake:
        o["bake"] = 1
    return o


def fit(objs, body, lo_g, hi_g):
    """Вписать тело (body) в коробку игры lo_g…hi_g; тот же перенос — всем objs (колючки, рёбра)."""
    blo, bhi = V.bounds_game([body])
    s = [(hi_g[i] - lo_g[i]) / max(1e-6, bhi[i] - blo[i]) for i in range(3)]
    t = [lo_g[i] - s[i] * blo[i] for i in range(3)]
    # игра (x, y, z) → Blender (−x, z, y): масштаб по осям Blender и перенос
    m = Matrix.Diagonal((s[0], s[2], s[1], 1.0))
    m.translation = Vector((-t[0], t[2], t[1]))
    for o in objs:
        o.matrix_world = m @ o.matrix_world
    bpy.context.view_layer.update()


def E(co, size):
    return ("ELLIPSOID", co, 1.0, size)


def B(co, r):
    return ("BALL", co, r, None)


def chain(a, b, r, n):
    return [B(tuple(a[i] + (b[i] - a[i]) * k / (n - 1) for i in range(3)), r) for k in range(n)]


def face_cactus(coll, cx, cy, cz, s, mood="fight"):
    """Лицо кактуса на фасаде (перед — −z): глаза, зрачки, сердитые брови, ухмылка с зубами."""
    out = [V.mb("FEyes", "F7F7F2", [E((cx + d * 2.6 * s, cy, cz), (1.15 * s, 1.4 * s, 0.7 * s)) for d in (-1, 1)], coll,
                bake=False, fixed="white"),
           V.mb("FPupil", "1C1C1C", [B((cx + d * 2.45 * s, cy - 0.25 * s, cz - 0.62 * s), 0.6 * s) for d in (-1, 1)],
                coll, bake=False, fixed="black")]
    brows = []
    for d in (-1, 1):
        brows += chain((cx + d * 1.2 * s, cy + 1.45 * s, cz - 0.45 * s), (cx + d * 4.0 * s, cy + 2.1 * s, cz - 0.45 * s),
                       0.42 * s, 5)
    out.append(V.mb("FBrow", "245A2C", brows, coll, bake=False))
    mouth = [E((cx, cy - 3.6 * s, cz - 0.1 * s), (3.2 * s, 0.95 * s, 0.6 * s)), B((cx + 3.0 * s, cy - 3.1 * s,
                                                                                  cz - 0.1 * s), 0.7 * s)]
    out.append(V.mb("FMouth", "7A1F2B", mouth, coll, bake=False))
    teeth = [((cx + x * s, cy - 3.05 * s, cz - 0.62 * s), (0.32 * s, 0.32 * s, 0.22 * s)) for x in (-2.2, -1.1, 0, 1.1,
                                                                                                    2.2)]
    out.append(boxes_mesh("FTeeth", teeth, "F6F4EE", coll, fixed="white"))
    return out


def glove(coll, x, y, z, r, tag):
    return [V.mb("GGlove" + tag, "D2302B", [B((x, y, z), r), B((x - 0.75 * r, y - 0.3 * r, z - 0.6 * r), 0.42 * r)],
                 coll),
            V.mb("GCuff" + tag, "F2EFE6", [E((x, y - 1.05 * r, z), (0.8 * r, 0.3 * r, 0.8 * r))], coll)]


def flower(coll, pts, tag):
    """Цветки кактуса: розовые лепестки и светящаяся серединка."""
    pet = []
    for (x, y, z) in pts:
        pet += [B((x + dx, y, z + dz), 0.75) for dx, dz in ((0.8, 0), (-0.8, 0), (0, 0.8), (0, -0.8))]
    return [V.mb("Flw" + tag, "FF6FA8", pet, coll, fixed="pink", bake=False),
            V.mb("FlwC" + tag, "FFE07A", [B(p, 0.55) for p in pts], coll, fixed="glow", bake=False)]


def spines_on(body_objs, rays, coll, name):
    """Колючки на поверхности тела: rays — (точка снаружи, точка внутри) в координатах игры; луч от внешней точки к
    внутренней, колючка — у точки попадания, вытянута по нормали (кремовые воксели)."""
    from mathutils.bvhtree import BVHTree
    verts, polys = [], []
    for o in body_objs:
        mw = o.matrix_world
        k = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        polys += [[k + i for i in p.vertices] for p in o.data.polygons]
    tree = BVHTree.FromPolygons(verts, polys)
    items = []
    for a, b in rays:
        pa, pb = K.P(*a), K.P(*b)
        hit = tree.ray_cast(pa, (pb - pa).normalized(), (pb - pa).length)
        if hit[0] is None:
            continue
        loc, nrm = hit[0], hit[1]
        c = loc + nrm * 0.45
        g = (-c.x, c.z, c.y)
        ng = (abs(nrm.x), abs(nrm.z), abs(nrm.y))
        items.append((g, (0.2 + 0.35 * ng[0], 0.2 + 0.35 * ng[1], 0.2 + 0.35 * ng[2])))
    return boxes_mesh(name, items, "F3E7C0", coll, fixed="white")


def rib_rays(points, inward):
    """Лучи к рёбрам: points — (x, z) ребра снаружи, inward — точка, к которой стреляем (x, z); по высоте с шагом."""
    out = []
    for (x, z), (y0, y1, every) in points:
        y = y0
        k = 0
        while y < y1:
            yy = y + 0.6 * (k % 2)
            ix, iz = inward(x, z)
            out.append(((x, yy, z), (ix, yy, iz)))
            y += every
            k += 1
    return out


# ── Космический: дом-кактус ───────────────────────────────────────────────────────────────────────────────────
def cosmic_saloon(coll):
    top = band_top(6)
    body_el = [("CUBE", (0, 28, 0), 4.0, (12.5, 23.5, 11.5))]
    rp = []
    for x in (-13, -6.5, 0, 6.5, 13):
        for sz in (-1, 1):
            body_el.append(E((x, 28, sz * 15.6), (1.9, 26, 1.9)))
    for z in (-10, -3.5, 3.5, 10):
        for sx in (-1, 1):
            body_el.append(E((sx * 16.6, 28, z), (1.9, 26, 1.9)))
    body = V.mb("SBody", "3E9E4A", body_el, coll)
    fit([body], body, (-17.7, 0.3, -16.7), (17.7, top - 0.2, 16.7))
    lo, hi = V.bounds_game([body])
    sxf, szf = (hi.x - lo.x) / 2 / 18.5, (hi.z - lo.z) / 2 / 17.5  # куда легли рёбра после вписывания
    for x in (-13, -6.5, 0, 6.5, 13):
        for sz in (-1, 1):
            rp.append(((x * sxf, sz * 30.0), (2.5, top - 2.0, 3.2)))
    for z in (-10, -3.5, 3.5, 10):
        for sx in (-1, 1):
            rp.append(((sx * 30.0, z * szf), (2.5, top - 2.0, 3.2)))
    sp = spines_on([body], rib_rays(rp, lambda x, z: (x * 0.2, z * 0.2)), coll, "SSpines")
    parts = [body, sp]
    parts += face_cactus(coll, 0, 43.5, -17.4, 1.55)
    arm = [E((-19.5, 28, -1), (3.2, 1.9, 1.9)), E((-21.2, 33, -1), (1.9, 5.0, 1.9))]
    parts.append(V.mb("SArm", "3E9E4A", arm, coll))
    parts += glove(coll, -21.0, 41.0, -1.0, 2.9, "S")
    parts += flower(coll, [(-12.5, top - 1.6, -15.6), (12.5, top - 1.6, -15.6), (-16.6, top - 2.0, 8), (-16.8, 30.5, -9)],
                    "S")
    parts.append(V.mb("SLamp", "FFE07A", [B((5.2, 9.0, -18.4), 0.8)], coll, fixed="glow", bake=False))
    grid, org, st, pal, fx = V.voxelize(parts, STEP, colors_k=24, fixed_colors=FIXED)
    win = []
    for x in (-9.75, 9.75):
        win.append(((x, 6.8, -17), 2.0, 2.6, "front"))
    for x in (-9.75, -3.25, 3.25, 9.75):
        win.append(((x, 21.5, -17), 2.0, 2.8, "front"))
    for y in (8.0, 21.5, 34.0, 46.5):
        for z in (-6.75, 0.0, 6.75):
            win.append(((-18, y, z), 2.0, 2.8, "left"))
            win.append(((18, y, z), 2.0, 2.8, "right"))
        for x in (-9.75, -3.25, 3.25, 9.75):
            win.append(((x, y, 17), 2.0, 2.8, "back"))
    for c, ha, hb, f in win:
        V.carve(grid, org, st, c, ha, hb, f, fx["glassw"], fx["frame"], depth=2)
    V.carve(grid, org, st, (0, 4.9, -17), 3.0, 4.5, "front", fx["glassw"], fx["frame"], depth=2, fill=fx["door"])
    return clip_top(grid, org, st, top), org, st, pal, fx


def clip_top(grid, org, st, top):
    """Ничего выше нижней грани верхней плиты: воксели выше — убрать (CHECK_TOP)."""
    k = int(math.floor((top - org[2]) / st + 1e-6))
    if 0 <= k < grid.shape[2]:
        grid[:, :, k:] = -1
    return grid


# ── Космический: дом-верблюд-аквариум ─────────────────────────────────────────────────────────────────────────
def cosmic_camel(coll):
    top = band_top(6)
    body = V.mb("CBody", "D8A65A", [("CUBE", (0, 22, 0), 6.0, (11.0, 8.0, 10.0)),
                                    E((-14.0, 20.0, 0.0), (5.0, 9.0, 12.5)), E((14.0, 20.0, 0.0), (5.0, 9.0, 12.5)),
                                    E((0.0, 21.0, -13.0), (11.5, 9.0, 4.5)), E((0.0, 21.0, 13.0), (11.5, 9.0, 4.5))],
                coll)  # туловище-дом во весь след: корпус и круглые бока
    fit([body], body, (-17.7, 8.0, -16.7), (17.7, 37.5, 16.7))
    parts = [body]
    parts.append(V.mb("CLegs", "C9944C", [E((sx * 12.3, 5.2, sz * 11.3), (4.6, 5.4, 4.4)) for sx in (-1, 1)
                                          for sz in (-1, 1)], coll))
    parts.append(V.mb("CHoof", "5A3A22", [E((sx * 12.3, 1.0, sz * 11.3), (4.7, 0.9, 4.5)) for sx in (-1, 1)
                                          for sz in (-1, 1)], coll))
    parts.append(V.mb("CBelt", "2FC4B2", [E((0, 30.5, 0), (17.9, 0.9, 16.9))], coll, bake=False))
    hump = [E((0, 44.0, -7.5), (11.0, 10.5, 7.6)), E((0, 44.0, 8.0), (11.0, 10.5, 7.6))]
    parts.append(V.mb("CHump", "62D6EA", hump, coll, fixed="aqua", bake=False))
    fish, bub = [], []
    for k in range(14):
        a = 2.4 * k
        hz = -7.5 if k % 2 == 0 else 8.5
        x = math.cos(a) * 10.4
        z = hz + math.sin(a) * 7.4
        y = 41 + (k % 4) * 3.2
        fish.append(E((x, y, z), (1.3, 0.75, 0.7)))
        bub.append(B((x * 0.9, y + 2.2, z * 0.95 + (0.3 if z < 0 else -0.3)), 0.45))
    parts.append(V.mb("CFish", "FF8A3D", fish, coll, fixed="fish", bake=False))
    parts.append(V.mb("CBub", "F6F4EE", bub, coll, fixed="white", bake=False))
    head = chain((0, 31, -14.5), (0, 37.5, -16.10), 3.8, 5) + [E((0, 41, -17.50), (6.3, 5.6, 4.1))]
    parts.append(V.mb("CHead", "D8A65A", head, coll))
    parts.append(V.mb("CMuzzle", "E9C489", [E((0, 37.6, -19.50), (4.6, 3.1, 2.1))], coll))
    parts.append(V.mb("CEar", "C98F45", [E((d * 4.9, 46.2, -16.70), (1.2, 1.9, 0.9)) for d in (-1, 1)], coll))
    parts.append(V.mb("CEye", "F7F7F2", [B((d * 2.9, 42.3, -20.80), 1.55) for d in (-1, 1)], coll, fixed="white",
                      bake=False))
    parts.append(V.mb("CPup", "1C1C1C", [B((d * 2.7, 42.0, -22.05), 0.72) for d in (-1, 1)], coll, fixed="black",
                      bake=False))
    lash = [((d * 2.9 + j * 0.6 * d, 44.1 + j * 0.15, -21.30), (0.2, 0.34, 0.2)) for d in (-1, 1) for j in (-1, 0, 1)]
    parts.append(boxes_mesh("CLash", lash, "1C1C1C", coll, fixed="black"))
    smile = [B((x, 36.2 + 0.12 * x * x, -21.45), 0.34) for x in (-2.2, -1.5, -0.75, 0, 0.75, 1.5, 2.2)]
    smile += [B((d * 1.4, 38.9, -21.50), 0.45) for d in (-1, 1)]
    parts.append(V.mb("CMouth", "6B3A26", smile, coll, bake=False))
    grid, org, st, pal, fx = V.voxelize(parts, STEP, colors_k=24, fixed_colors=FIXED)
    for y in (15.0, 25.0):
        for z in (-9.0, 0.0, 9.0):
            V.carve(grid, org, st, (-17.7, y, z), 3.2, 3.2, "left", fx["aqua"], fx["brass"], depth=2, round_=True)
            V.carve(grid, org, st, (17.7, y, z), 3.2, 3.2, "right", fx["aqua"], fx["brass"], depth=2, round_=True)
    for x in (-11.0, 11.0):
        for y in (15.0, 25.0):
            V.carve(grid, org, st, (x, y, -16), 3.2, 3.2, "front", fx["aqua"], fx["brass"], depth=2, round_=True)
    for x in (-9.0, 0.0, 9.0):
        for y in (15.0, 25.0):
            V.carve(grid, org, st, (x, y, 16), 3.2, 3.2, "back", fx["aqua"], fx["brass"], depth=2, round_=True)
    return clip_top(grid, org, st, top), org, st, pal, fx


# ── Мифический: органика проступает сквозь здание D39 ───────────────────────────────────────────────────────────
def mythic_saloon(coll):
    top = band_top(5)
    parts, rays = [], []
    for (cx, cz) in ((-15.0, -14.0), (15.0, 14.0)):
        el = [E((cx, 21.0, cz), (4.0, 21.5, 4.0))]
        for k in range(6):
            a = k * math.pi / 3
            el.append(E((cx + math.cos(a) * 3.6, 21.0, cz + math.sin(a) * 3.6), (1.0, 21.0, 1.0)))
        col = V.mb("MCol%d" % len(parts), "3E9E4A", el, coll)
        parts.append(col)
        for k in range(6):
            a = k * math.pi / 3
            ox, oz = cx + math.cos(a) * 12, cz + math.sin(a) * 12
            y = 2.5
            j = 0
            while y < top - 1.5:
                rays.append(((ox, y + 0.6 * (j % 2), oz), (cx, y + 0.6 * (j % 2), cz)))
                y += 3.2
                j += 1
    parts.append(spines_on(parts[:], rays, coll, "MSpines"))
    arm = [E((-9.5, 26.0, -18.0), (5.6, 1.8, 1.8)), E((-3.8, 29.8, -18.3), (1.8, 4.4, 1.8))]
    parts.append(V.mb("MArm", "3E9E4A", arm, coll))
    parts += glove(coll, -3.8, 36.4, -18.9, 2.6, "M")
    parts += face_cactus(coll, -15.0, 33.5, -18.25, 0.72)
    parts += flower(coll, [(-15.0, top - 0.8, -14.0), (15.0, top - 0.8, 14.0), (-12.5, top - 1.0, -16.5)], "M")
    grid, org, st, pal, fx = V.voxelize(parts, STEP, colors_k=18, fixed_colors=FIXED)
    return clip_top(grid, org, st, top), org, st, pal, fx


def mythic_camel(coll):
    top = band_top(5)
    parts = [V.mb("MLeg", "D8A65A", [E((sx * 14.6, 9.5, -13.6), (2.9, 9.5, 2.9)) for sx in (-1, 1)], coll),
             V.mb("MHoof", "5A3A22", [E((sx * 14.6, 1.2, -13.6), (3.0, 1.1, 3.0)) for sx in (-1, 1)], coll)]
    head = chain((0, 29.5, -16.0), (0, 33.0, -18.0), 3.0, 4) + [E((0, 35.5, -18.8), (4.4, 3.9, 3.2))]
    parts.append(V.mb("MHead", "D8A65A", head, coll))
    parts.append(V.mb("MMuzzle", "E9C489", [E((0, 33.0, -20.4), (3.3, 2.3, 1.6))], coll))
    parts.append(V.mb("MEar", "C98F45", [E((d * 3.4, 39.3, -18.2), (0.9, 1.4, 0.7)) for d in (-1, 1)], coll))
    parts.append(V.mb("MEye", "F7F7F2", [B((d * 2.0, 36.3, -21.4), 1.1) for d in (-1, 1)], coll, fixed="white",
                      bake=False))
    parts.append(V.mb("MPup", "1C1C1C", [B((d * 1.9, 36.1, -22.3), 0.52) for d in (-1, 1)], coll, fixed="black",
                      bake=False))
    parts.append(V.mb("MMouth", "6B3A26", [B((x, 31.7 + 0.12 * x * x, -21.85), 0.3) for x in (-1.5, -0.75, 0, 0.75, 1.5)],
                      coll, bake=False))
    parts.append(V.mb("MHump", "62D6EA", [E((sx * 18.4, 33.0, 0.0), (3.0, 7.0, 9.0)) for sx in (-1, 1)], coll,
                      fixed="aqua", bake=False))
    parts.append(V.mb("MFish", "FF8A3D", [E((sx * 21.0, 31 + k * 2.6, -5 + k * 3.4), (0.5, 0.7, 1.2)) for sx in (-1, 1)
                                          for k in range(4)], coll, fixed="fish", bake=False))
    grid, org, st, pal, fx = V.voxelize(parts, STEP, colors_k=16, fixed_colors=FIXED)
    return clip_top(grid, org, st, top), org, st, pal, fx


# ── жильцы атриума Золотого ────────────────────────────────────────────────────────────────────────────────────
def resident_cactus(coll, x, y, z, s):
    el = [E((x, y + 3.6 * s, z), (1.25 * s, 3.4 * s, 1.15 * s)), E((x, y + 6.6 * s, z), (1.2 * s, 1.0 * s, 1.1 * s))]
    for d in (-1, 1):
        el += [E((x + d * 1.9 * s, y + 4.6 * s, z), (1.3 * s, 0.55 * s, 0.55 * s)),
               E((x + d * 2.9 * s, y + 6.2 * s, z), (0.55 * s, 1.5 * s, 0.55 * s)),
               E((x + d * 0.7 * s, y + 0.6 * s, z), (0.55 * s, 0.9 * s, 0.6 * s))]
    parts = [V.mb("RBody", "3E9E4A", el, coll)]
    for d in (-1, 1):
        parts += glove(coll, x + d * 2.9 * s, y + 8.4 * s, z - 0.1 * s, 1.25 * s, "R%d" % d)
    parts.append(V.mb("RShorts", "D2302B", [E((x, y + 2.2 * s, z), (1.45 * s, 0.75 * s, 1.35 * s))], coll))
    parts.append(V.mb("RBelt", "F2EFE6", [E((x, y + 2.85 * s, z), (1.42 * s, 0.22 * s, 1.32 * s))], coll))
    parts += face_cactus(coll, x, y + 6.7 * s, z - 1.05 * s, 0.34 * s)
    return parts


def resident_camel(coll, x, y, z, s):
    el = [E((x, y + 6.5 * s, z), (3.2 * s, 2.2 * s, 2.6 * s))]
    el += [E((x + sx * 2.2 * s, y + 2.4 * s, z + sz * 1.7 * s), (0.7 * s, 2.4 * s, 0.7 * s)) for sx in (-1, 1)
           for sz in (-1, 1)]
    el += chain((x, y + 7.2 * s, z - 2.4 * s), (x, y + 10.2 * s, z - 3.4 * s), 1.0 * s, 4)
    el += [E((x, y + 11.0 * s, z - 3.9 * s), (1.5 * s, 1.3 * s, 1.4 * s))]
    parts = [V.mb("RCamel", "D8A65A", el, coll)]
    parts.append(V.mb("RHump", "62D6EA", [E((x, y + 9.4 * s, z + d * 1.3 * s), (1.9 * s, 2.0 * s, 1.3 * s))
                                          for d in (-1, 1)], coll, fixed="aqua", bake=False))
    parts.append(V.mb("RFish", "FF8A3D", [E((x + 0.9 * s * d, y + 9.6 * s, z + d * 1.3 * s - 1.2 * s),
                                            (0.45 * s, 0.3 * s, 0.25 * s)) for d in (-1, 1)], coll, fixed="fish",
                      bake=False))
    parts.append(V.mb("REye", "F7F7F2", [B((x + d * 0.7 * s, y + 11.4 * s, z - 5.15 * s), 0.42 * s) for d in (-1, 1)],
                      coll, fixed="white", bake=False))
    parts.append(V.mb("RPup", "1C1C1C", [B((x + d * 0.66 * s, y + 11.35 * s, z - 5.5 * s), 0.2 * s) for d in (-1, 1)],
                      coll, fixed="black", bake=False))
    return parts


# ══ сборка темы ═══════════════════════════════════════════════════════════════════════════════════════════════
def theme_build(theme):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, theme + "_base.blend"))
    scene = bpy.context.scene
    pre = "CB" if theme == "saloon" else "AQ"
    base = [o for o in bpy.data.objects if o.name.startswith((pre + "_F_", pre + "_I_"))]
    base_coll = base[0].users_collection[0]
    work = bpy.data.collections.new("Work")
    scene.collection.children.link(work)
    work.hide_render = True
    T = {k: list(bpy.data.collections["T%d" % k].objects) for k in range(1, 7)}
    nums = []

    def mk(name, objs):
        c = bpy.data.collections.new(name)
        scene.collection.children.link(c)
        for o in objs:
            c.objects.link(o)
        return c

    def matk(o):
        return o.data.materials[0].name if (o.type == "MESH" and o.data.materials) else ""

    def voxel_into(coll, label, built, glow=GLOW):
        grid, org, st, pal, fx = built
        q = V.greedy(grid, org, st)
        o = V.build_mesh(label, q, pal, coll, st, glow_idx=[fx[n] for n in glow])
        r = V.report(label, grid, q)
        far = V.downsample(grid, int(FAR / st))
        r["far"] = len(V.greedy(far, org, FAR)) * 2
        occ = np.argwhere(grid >= 0)
        r["top"] = float(org[2] + (occ[:, 2].max() + 1) * st)
        nums.append(r)
        print("FAR", label, r["far"], "TOP", r["top"], flush=True)
        return o

    for o in list(work.objects):
        bpy.data.objects.remove(o)
    O1 = mk("O1", T[1])
    O2 = mk("O2", T[2])
    O3 = mk("O3", T[3])
    # Золотой: атриум + жилец, свет в атриуме
    O4 = mk("O4", T[4])
    rp = (resident_cactus(work, 0.0, 19.25, -Z + 4.8, 1.38) if theme == "saloon"
          else resident_camel(work, 0.0, 19.25, -Z + 8.0, 1.2))
    voxel_into(O4, "Res_" + theme, V.voxelize(rp, RES_STEP, colors_k=12, fixed_colors=FIXED))
    lamp = bpy.data.objects.new("AtriumLight", bpy.data.lights.new("AtriumLight", "POINT"))
    lamp.data.energy, lamp.data.color = 2600, (1.0, 0.92, 0.8)
    lamp.location = K.P(0, 31, -Z + 2.5)
    O4.objects.link(lamp)
    # Мифический: D39 без «геройского» знака + органика
    sign = (0.0, 19.0 + (45 - 2.6 - 19.0) / 3 + 0.5 + 2.3 * 2.3, -Z - 2.5)
    keep5 = [o for o in T[5] if not (matk(o).startswith(("R_glove", "R_cuff", "R_trim", "R_fish", "R_fin", "R_eye",
                                                         "R_black"))
                                     and (o.matrix_world.translation - K.P(*sign)).length < 9.5)]
    O5 = mk("O5", keep5)
    for o in list(work.objects):
        bpy.data.objects.remove(o)
    voxel_into(O5, "Myth_" + theme, mythic_saloon(work) if theme == "saloon" else mythic_camel(work))
    # Космический: существо-дом целиком, плиты и кант — чёткие
    crisp6 = [o for o in T[6] if (matk(o).startswith("R_slab") and o.dimensions.x > 35 and o.dimensions.y > 33)
              or matk(o).startswith("R_k_") or (matk(o)[:3] == "R_r" and matk(o)[3:4].isdigit())]  # плиты во весь след и кант
    O6 = mk("O6", crisp6)
    for o in list(work.objects):
        bpy.data.objects.remove(o)
    voxel_into(O6, "Cosmic_" + theme, cosmic_saloon(work) if theme == "saloon" else cosmic_camel(work))
    for o in list(work.objects):
        bpy.data.objects.remove(o)
    for c in list(scene.collection.children):
        if c.name.startswith("T") and c.name[1:].isdigit():
            c.hide_render = True
    # проверки: ничего выше верхней плиты
    for t, col in ((1, O1), (4, O4), (5, O5), (6, O6)):
        objs = [o for o in col.objects if o.type == "MESH"] + ([] if t == 6 else base)
        top = max((o.matrix_world @ Vector(cc)).z for o in objs for cc in o.bound_box
                  if abs(cc[0]) < 29.5 and abs(cc[1]) < 29.5)
        lo, hi = V.bounds_game([o for o in col.objects if o.type == "MESH" and o.name.startswith(("Cosmic", "Myth",
                                                                                                 "Res"))] or objs)
        print("CHECK_TOP %s %s %s: верх %.2f ≤ %d; вынос органики: вбок %.1f, вперёд %.1f" % (
            "OK" if top <= H[t - 1] - 1 + 1e-3 else "FAIL", theme, NAMES[t - 1], top, H[t - 1] - 1,
            max(-lo.x, hi.x) - X, -lo.z - Z), flush=True)
    # кадры
    cam = scene.camera
    scene.render.resolution_x, scene.render.resolution_y = 900, 1100

    def aim(eye, target, fov):
        cam.data.angle_y = math.radians(fov)
        e, t = K.P(*eye), K.P(*target)
        cam.location = e
        cam.rotation_euler = (e - t).to_track_quat("Z", "Y").to_euler()

    def show(name, with_base):
        for c in scene.collection.children:
            if c.name.startswith(("O", "Work")):
                c.hide_render = c.name != name
        base_coll.hide_render = not with_base

    def render(n):
        scene.render.filepath = os.path.join(OUT, "%s_%s.png" % (theme, n))
        bpy.ops.render.render(write_still=True)
        print("SHOT", n, flush=True)

    aim((-104, 40, -118), (0, 27, -2), 36)
    for n, c, wb in (("v3_1", "O1", True), ("v3_4", "O4", True), ("v3_5", "O5", True), ("v3_6", "O6", False)):
        show(c, wb)
        render(n)
    show("O6", False)
    aim((-26, 44, -64), (0, 36, -14), 44)
    render("v3_6_close")
    show("O4", True)
    aim((-10, 27, -42), (0, 25.5, -14), 40)
    render("v3_4_atrium")
    show("O5", True)
    aim((-30, 34, -56), (-6, 28, -16), 44)
    render("v3_5_close")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, theme + "_organic.blend"))
    json.dump(nums, open(os.path.join(OUT, theme + "_numbers.json"), "w", encoding="utf-8"), ensure_ascii=False, default=int)
    print("DONE_THEME", flush=True)


# ══ башня 1-6-3-5-2-4 ══════════════════════════════════════════════════════════════════════════════════════════
def tower():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "saloon_organic.blend"))
    scene = bpy.context.scene
    cb = [o for o in bpy.data.objects if o.name.startswith(("CB_F_", "CB_I_"))]
    with bpy.data.libraries.load(os.path.join(OUT, "aquarium_organic.blend")) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(("AQ_F_", "AQ_I_"))]
        dst.collections = ["O1", "O3", "O4"]
    aq = [o for o in dst.objects if o is not None]
    aqc = {k: list(c.objects) for k, c in zip(("O1", "O3", "O4"), dst.collections)}
    sc = {k: list(bpy.data.collections[k].objects) for k in ("O2", "O5", "O6")}
    for c in scene.collection.children:
        c.hide_render = True
    TX = 400.0
    order = [(1, aqc["O1"], aq), (6, sc["O6"], []), (3, aqc["O3"], aq), (5, sc["O5"], cb), (2, sc["O2"], cb),
             (4, aqc["O4"], aq)]
    tw = bpy.data.collections.new("Tower")
    scene.collection.children.link(tw)
    y = 0.0
    yfl = {}
    for t, over, base in order:
        oy = y + 1.0
        made = []
        for o in over + base:
            c = o.copy()
            tw.objects.link(c)
            c.location = o.location + Vector((-TX, 0, oy))
            made.append(c)
        bpy.context.view_layer.update()
        top = max((c.matrix_world @ Vector(cc)).z for c in made if c.type == "MESH" for cc in c.bound_box
                  if abs(cc[0]) < 29.5 and abs(cc[1]) < 29.5) - oy
        print("CHECK_TOP %s башня %s: верх %.2f ≤ %d" % ("OK" if top <= H[t - 1] - 1 + 1e-3 else "FAIL", NAMES[t - 1],
                                                        top, H[t - 1] - 1), flush=True)
        yfl[t] = y
        y += H[t - 1]
    ry = y

    def gbox(hx, x0, x1, y0, y1, z0, z1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=K.P((x0 + x1) / 2 + TX, (y0 + y1) / 2, (z0 + z1) / 2))
        o = bpy.context.active_object
        o.scale = (abs(x1 - x0), abs(z1 - z0), abs(y1 - y0))
        mat_of(o, hx)

    def gcone(hx, r1, r2, y0, y1):
        bpy.ops.mesh.primitive_cone_add(vertices=8 if r1 == r2 else 4, radius1=r1, radius2=r2, depth=y1 - y0,
                                        location=K.P(TX, (y0 + y1) / 2, 0))
        mat_of(bpy.context.active_object, hx)

    def mat_of(o, hx):
        for c in o.users_collection:
            c.objects.unlink(o)
        tw.objects.link(o)
        m = bpy.data.materials.new("C_" + hx)
        m.use_nodes = True
        next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (
            *V.srgb2lin(V.hex_rgb(hx)), 1)
        o.data.materials.append(m)

    gbox("4E9A3A", -X + 1, X - 1, ry, ry + 1.5, -Z + 1, Z - 1)  # колпак C: сад, кольцо, кристалл в когтях
    gcone("E9B43A", 9.5, 9.5, ry + 1.5, ry + 4.5)
    gcone("8E44D8", 10.0, 10.0, ry + 4.5, ry + 5.5)
    gcone("38D6E0", 0.01, 8.5, ry + 5.5, ry + 19.0)
    gcone("38D6E0", 8.5, 0.01, ry + 19.0, ry + 35.0)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        cx, cz = math.cos(a) * 9.2, math.sin(a) * 9.2
        gbox("E9B43A", cx - 1.6, cx + 1.6, ry + 4.5, ry + 23.0, cz - 1.6, cz + 1.6)
    tw.hide_render = False
    cam = scene.camera

    def aim(eye, target, fov, w, h):
        scene.render.resolution_x, scene.render.resolution_y = w, h
        cam.data.angle_y = math.radians(fov)
        e, t = K.P(eye[0] + TX, eye[1], eye[2]), K.P(target[0] + TX, target[1], target[2])
        cam.location = e
        cam.rotation_euler = (e - t).to_track_quat("Z", "Y").to_euler()

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
    aim((-12, 5, -60 - Z), (0, 75, -Z), 72, 900, 1200)
    render("60_ground")
    print("TOWER_HEIGHT", ry, "DONE_TOWER", flush=True)


if MODE == "tower":
    tower()
else:
    theme_build(MODE)

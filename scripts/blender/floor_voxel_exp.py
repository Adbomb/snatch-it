"""Эксперимент D74 (не решение): редкие этажи в стиле «микро-воксели» — «из другого мира», редкость видна сразу.

  Космический этаж салуна целиком в микро-вокселях: этаж листа Б v2 (база + надстройки Космического, углы скруглены
  фаской — «гладкая лепка») и геройский объект — кактус-боксёр, вылепленный метаболами, → вокселизация поверхности
  на сетке STEP (кратна стаду) → цвет вокселя — от треугольника, квантование в палитру темы (k-средних) → склейка
  граней (greedy meshing) → цвета в карту-палитру (UV каждой склеенной грани — в свой тексель).
  Золотой этаж салуна — D39 (лист Б v2), геройский объект — кактус-боксёр в микро-вокселях (шаг HERO_STEP).
  Правила модуля не меняются: плиты снизу и сверху с кантом (чёткие, D39), след по сетке, CHECK_TOP.
Числа печатаются: треугольники до и после склейки, сколько мешей (лимит MeshPart 20 000), дальняя версия (STEP_FAR).
Только концепт: в игру не экспортируется.

Запуск (сцены — из прогона листа Б v2, папка <v2>):
  blender -b --factory-startup --python scripts/blender/floor_voxel_exp.py -- <репо> <папка> <v2> build
  blender -b --factory-startup --python scripts/blender/floor_voxel_exp.py -- <репо> <папка> <v2> tower
"""

import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import floorkit as K  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT, V2, MODE = os.path.abspath(argv[0]), os.path.abspath(argv[1]), os.path.abspath(argv[2]), argv[3]
os.makedirs(OUT, exist_ok=True)
STEP, HERO_STEP, STEP_FAR = 0.5, 0.25, 2.0
COLORS = 22  # палитра этажа после квантования
MESH_LIMIT = 20000
DITHER = 0.09 if "dither" in sys.argv else 0.0  # второй оттенок геометрией (дорого); по умолчанию — текстурой
CELLS = 64  # клеток-вокселей в одной плитке текстуры «кубик»
CELL_PX = 8
X, Z = 18.12, 17.12
H = [20, 27, 32, 38, 46, 60]
NAMES = ["Деревянный", "Каменный", "Мраморный", "Золотой", "Мифический", "Космический"]


def lin2srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def obj_colors(o):
    """Цвет каждого треугольника объекта (sRGB 0…1): цвет вершин «Col» × тон материала, иначе цвет материала."""
    me = o.data
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    mat = me.materials[0] if me.materials else None
    tint = np.ones(3)
    base = np.array([0.8, 0.8, 0.8])
    if mat and mat.use_nodes:
        mix = next((nd for nd in mat.node_tree.nodes if nd.type == "MIX"), None)
        bsdf = next((nd for nd in mat.node_tree.nodes if nd.type == "BSDF_PRINCIPLED"), None)
        if mix is not None:
            tint = np.array(mix.inputs[6].default_value[:3])
        elif bsdf is not None:
            base = np.array(bsdf.inputs["Base Color"].default_value[:3])
    col = me.color_attributes.get("Col")
    if col is not None and col.domain == "CORNER":
        cc = np.empty(len(me.loops) * 4)
        col.data.foreach_get("color", cc)
        cc = cc.reshape(-1, 4)[:, :3]
        lt = np.empty(n * 3, dtype=np.int64)
        me.loop_triangles.foreach_get("loops", lt)
        tri = cc[lt.reshape(-1, 3)].mean(axis=1) * tint
    else:
        tri = np.tile(base, (n, 1))
    return lin2srgb(tri)


def obj_tris(o):
    """Треугольники объекта в мировых координатах (n, 3, 3)."""
    me = o.data
    me.calc_loop_triangles()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mw = np.array(o.matrix_world)
    co = co @ mw[:3, :3].T + mw[:3, 3]
    vi = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", vi)
    return co[vi.reshape(-1, 3)]


def sample_tris(tris, colors, step):
    """Точки по треугольникам с шагом ≤ step/2 и цвет каждой точки."""
    pts, cols = [], []
    e = np.stack([np.linalg.norm(tris[:, 1] - tris[:, 0], axis=1), np.linalg.norm(tris[:, 2] - tris[:, 1], axis=1),
                  np.linalg.norm(tris[:, 0] - tris[:, 2], axis=1)], axis=1).max(axis=1)
    ns = np.maximum(1, np.ceil(e / (step * 0.45))).astype(int)
    for n in np.unique(ns):
        sel = ns == n
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
        m = (i + j) <= n
        a, b = (i[m] / n)[None, :, None], (j[m] / n)[None, :, None]
        t = tris[sel]
        p = t[:, None, 0] + (t[:, None, 1] - t[:, None, 0]) * a + (t[:, None, 2] - t[:, None, 0]) * b
        pts.append(p.reshape(-1, 3))
        cols.append(np.repeat(colors[sel], p.shape[1], axis=0))
    return np.concatenate(pts), np.concatenate(cols)


def voxelize(objs, step, colors_k=COLORS, palette=None):
    """Воксели поверхности объектов: (сетка цветов int, начало, шаг, палитра). Сетка — по мировым координатам, кратным
    шагу (совпадает с сеткой стадов). Цвет вокселя — последний записанный (надстройки поверх базы)."""
    allp, allc = [], []
    for o in objs:
        if o.type != "MESH" or len(o.data.polygons) == 0:
            continue
        tris, cols = obj_tris(o), obj_colors(o)
        keep = (np.abs(tris[:, :, 0]) < 29.5).all(axis=1) & (np.abs(tris[:, :, 1]) < 29.5).all(axis=1)  # без якорей ±30
        if not keep.any():
            continue
        p, c = sample_tris(tris[keep], cols[keep], step)
        allp.append(p)
        allc.append(c)
    p, c = np.concatenate(allp), np.concatenate(allc)
    idx = np.floor(p / step + 1e-6).astype(np.int64)
    lo = idx.min(axis=0)
    idx -= lo
    dims = idx.max(axis=0) + 1
    flat = np.ravel_multi_index(idx.T, dims)
    order = np.argsort(flat, kind="stable")
    flat_s = flat[order]
    last = np.r_[flat_s[1:] != flat_s[:-1], True]
    vox = flat_s[last]
    vcol = c[order][last]
    if palette is None:  # k-средних по цветам вокселей
        colors_k = min(colors_k, len(vcol))
        rng = np.random.default_rng(7)
        palette = vcol[rng.choice(len(vcol), colors_k, replace=False)]
        for _ in range(12):
            lab = np.argmin(((vcol[:, None, :] - palette[None]) ** 2).sum(-1), axis=1)
            for k in range(colors_k):
                if np.any(lab == k):
                    palette[k] = vcol[lab == k].mean(axis=0)
    lab = np.argmin(((vcol[:, None, :] - palette[None]) ** 2).sum(-1), axis=1)
    k = len(palette)
    if DITHER:  # фактура «микро-вокселей»: у каждого цвета второй оттенок (темнее на DITHER), выбор — хеш вокселя
        ii = np.array(np.unravel_index(vox, dims)).T + lo
        h = (ii[:, 0] * 73856093) ^ (ii[:, 1] * 19349663) ^ (ii[:, 2] * 83492791)
        lab = np.where((h >> 3) % 3 == 0, lab + k, lab)
        palette = np.concatenate([palette, np.clip(palette * (1 - DITHER), 0, 1)])
    grid = np.full(dims, -1, dtype=np.int16)
    grid.flat[vox] = lab
    return grid, lo * step, step, palette


def downsample(grid, f):
    """Дальняя версия: блоки f³ → один воксель (цвет — самый частый)."""
    d = [(s + f - 1) // f * f for s in grid.shape]
    g = np.full(d, -1, dtype=np.int16)
    g[: grid.shape[0], : grid.shape[1], : grid.shape[2]] = grid
    g = g.reshape(d[0] // f, f, d[1] // f, f, d[2] // f, f).transpose(0, 2, 4, 1, 3, 5).reshape(d[0] // f, d[1] // f,
                                                                                                  d[2] // f, -1)
    out = np.full(g.shape[:3], -1, dtype=np.int16)
    filled = (g >= 0).sum(-1) > 0
    for i, j, k in zip(*np.nonzero(filled)):
        v = g[i, j, k]
        v = v[v >= 0]
        out[i, j, k] = np.bincount(v).argmax()
    return out


def faces_count(grid):
    """Число граней вокселей до склейки (каждая — квадрат = 2 треугольника)."""
    occ = grid >= 0
    n = 0
    for a in range(3):
        pad = np.pad(occ, [(1, 1) if i == a else (0, 0) for i in range(3)])
        sl0 = [slice(None)] * 3
        sl1 = [slice(None)] * 3
        sl0[a], sl1[a] = slice(1, -1), slice(2, None)
        n += np.count_nonzero(pad[tuple(sl0)] & ~pad[tuple(sl1)])
        sl1[a] = slice(0, -2)
        n += np.count_nonzero(pad[tuple(sl0)] & ~pad[tuple(sl1)])
    return n


def greedy(grid, origin, step):
    """Склейка граней: прямоугольники одного цвета в каждой плоскости. Возвращает список (4 угла, цвет)."""
    occ = grid >= 0
    quads = []
    other = {0: (1, 2), 1: (0, 2), 2: (0, 1)}
    for a in range(3):
        b, c = other[a]
        for s in (-1, 1):
            shifted = np.full(occ.shape, False)
            src = [slice(None)] * 3
            dst = [slice(None)] * 3
            if s > 0:
                src[a], dst[a] = slice(1, None), slice(0, -1)
            else:
                src[a], dst[a] = slice(0, -1), slice(1, None)
            shifted[tuple(dst)] = occ[tuple(src)]
            face = occ & ~shifted
            for i in np.nonzero(face.any(axis=tuple(x for x in range(3) if x != a)))[0]:
                sl = [slice(None)] * 3
                sl[a] = i
                m = np.where(face[tuple(sl)], grid[tuple(sl)], -1)  # оси (b, c)
                vis = np.zeros(m.shape, dtype=bool)
                plane = origin[a] + (i + (1 if s > 0 else 0)) * step
                vs, us = np.nonzero(m.T >= 0)  # цвет 0 — тоже цвет
                for v, u in zip(vs, us):
                    if vis[u, v]:
                        continue
                    col = m[u, v]
                    w = 1
                    while u + w < m.shape[0] and m[u + w, v] == col and not vis[u + w, v]:
                        w += 1
                    h = 1
                    while v + h < m.shape[1] and np.all(m[u : u + w, v + h] == col) and not vis[u : u + w, v + h].any():
                        h += 1
                    vis[u : u + w, v : v + h] = True
                    p = []
                    for du, dv in ((0, 0), (w, 0), (w, h), (0, h)):
                        q = [0.0, 0.0, 0.0]
                        q[a] = plane
                        q[b] = origin[b] + (u + du) * step
                        q[c] = origin[c] + (v + dv) * step
                        p.append(q)
                    flip = (a == 1) != (s < 0)
                    quads.append((p[::-1] if flip else p, int(col)))
    return quads


_cell_img = None


def cell_image():
    """Плитка «кубики»: CELLS × CELLS вокселей по CELL_PX пикселей. У каждого — свой оттенок (0.9…1.08), тёмный шов по
    краю и скос (светлее сверху-слева, темнее снизу-справа): каждый воксель читается отдельным кубиком, как на
    референсе, а треугольников не прибавляется (склеенная грань несёт столько клеток, сколько вокселей)."""
    global _cell_img
    if _cell_img is not None:
        return _cell_img
    n = CELLS * CELL_PX
    rng = np.random.default_rng(11)
    shade = rng.uniform(0.9, 1.08, (CELLS, CELLS))
    y, x = np.mgrid[0:n, 0:n]
    v = shade[y // CELL_PX, x // CELL_PX]
    cx, cy = x % CELL_PX, y % CELL_PX
    v = np.where((cx == 1) | (cy == CELL_PX - 2), v * 1.08, v)
    v = np.where((cx == CELL_PX - 2) | (cy == 1), v * 0.9, v)
    v = np.where((cx == 0) | (cy == 0) | (cx == CELL_PX - 1) | (cy == CELL_PX - 1), v * 0.7, v)
    px = np.ones((n, n, 4), dtype=np.float32)
    px[..., 0] = px[..., 1] = px[..., 2] = np.clip(v, 0, 1)
    img = bpy.data.images.new("VoxelCells", n, n)
    img.colorspace_settings.name = "Non-Color"
    img.pixels[:] = px.ravel().tolist()
    img.update()
    img.pack()
    _cell_img = img
    return img


def palette_material(name, palette):
    """Цвет — карта-палитра (тексель на цвет, UV «UV»), × плитка «кубики» (UV «Cell», клетка = воксель)."""
    n = len(palette)
    img = bpy.data.images.new(name, n, 1)
    px = np.ones((n, 4))
    px[:, :3] = palette
    img.colorspace_settings.name = "sRGB"
    img.pixels[:] = px.astype(np.float32).ravel().tolist()
    img.update()
    img.pack()
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED")
    uv_a = nt.nodes.new("ShaderNodeUVMap")
    uv_a.uv_map = "UV"
    uv_b = nt.nodes.new("ShaderNodeUVMap")
    uv_b.uv_map = "Cell"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    cells = nt.nodes.new("ShaderNodeTexImage")
    cells.image = cell_image()
    cells.interpolation = "Closest"
    nt.links.new(uv_a.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(uv_b.outputs["UV"], cells.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    nt.links.new(tex.outputs["Color"], mix.inputs[6])
    nt.links.new(cells.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.7
    return m


def build_mesh(name, quads, palette, coll, step):
    n = len(palette)
    verts, faces, uvs, cuv = [], [], [], []
    for p, col in quads:
        k = len(verts)
        verts.extend(p)
        faces.append((k, k + 1, k + 2, k + 3))
        u = (col + 0.5) / n
        uvs.extend([(u, 0.5)] * 4)
        arr = np.array(p)
        a = int(np.argmin(arr.max(axis=0) - arr.min(axis=0)))  # ось нормали: координата не меняется
        b, c = [i for i in range(3) if i != a]
        for q in p:
            cuv.append((q[b] / step / CELLS, q[c] / step / CELLS))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UV")
    uv.data.foreach_set("uv", np.array(uvs, dtype=np.float32).ravel())
    uv2 = me.uv_layers.new(name="Cell")
    uv2.data.foreach_set("uv", np.array(cuv, dtype=np.float32).ravel())
    me.materials.append(palette_material(name + "_Pal", palette))
    glow = palette_material(name + "_Glow", palette)
    bsdf = next(nd for nd in glow.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
    mixn = next(nd for nd in glow.node_tree.nodes if nd.type == "MIX")
    glow.node_tree.links.new(mixn.outputs[2], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.8
    me.materials.append(glow)
    lit = (palette[:, 0] > 0.85) & (palette[:, 1] > 0.75) & (palette[:, 2] < 0.75)  # тёплое стекло окон
    me.polygons.foreach_set("material_index", np.array([1 if lit[c] else 0 for _, c in quads], dtype=np.int32))
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def report(label, grid, quads):
    before = faces_count(grid) * 2
    after = len(quads) * 2
    meshes = max(1, math.ceil(after / MESH_LIMIT))
    print("NUM %s: вокселей %d, треугольников до склейки %d, после %d (в %.1f раза меньше), мешей %d (лимит %d)"
          % (label, int((grid >= 0).sum()), before, after, before / max(after, 1), meshes, MESH_LIMIT), flush=True)
    return before, after, meshes


# ── герой: кактус-боксёр, вылепленный метаболами ───────────────────────────────────────────────────────────────
def mb_object(family, color_hex, elements, at, coll):
    """Метабол-семья (своё имя — не сливается с другими семьями) → меш с цветом материала."""
    mb = bpy.data.metaballs.new(family)
    mb.resolution = 0.12
    mb.render_resolution = 0.12
    for kind, co, r, size in elements:
        el = mb.elements.new(type=kind)
        el.co = co
        el.radius = r
        if kind == "ELLIPSOID":
            el.size_x, el.size_y, el.size_z = size
    ob = bpy.data.objects.new(family, mb)
    coll.objects.link(ob)
    ob.location = at
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    mesh_ob = bpy.data.objects.new(family + "_Mesh", me)
    coll.objects.link(mesh_ob)
    mesh_ob.matrix_world = ob.matrix_world
    bpy.data.objects.remove(ob)
    m = bpy.data.materials.new(family + "_M")
    m.use_nodes = True
    rgb = [int(color_hex[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (
        *[c**2.2 for c in rgb], 1)
    me.materials.append(m)
    return mesh_ob


def hero(at_game, s, coll, tag):
    """Кактус-боксёр в позе чемпиона: ствол, руки вверх в красных перчатках с белыми манжетами, красные трусы с белым
    поясом, сердитые глаза. Координаты метаболов — Blender (z вверх, перед — −y)."""
    at = K.P(*at_game)
    E = "ELLIPSOID"
    cactus = [
        (E, (0, 0, 3.6 * s), 1.0, (1.25 * s, 1.15 * s, 3.4 * s)),
        (E, (0, 0, 6.6 * s), 1.0, (1.2 * s, 1.1 * s, 1.0 * s)),
        (E, (1.9 * s, 0, 4.6 * s), 1.0, (1.3 * s, 0.55 * s, 0.55 * s)),  # плечи
        (E, (-1.9 * s, 0, 4.6 * s), 1.0, (1.3 * s, 0.55 * s, 0.55 * s)),
        (E, (2.9 * s, 0, 6.2 * s), 1.0, (0.55 * s, 0.55 * s, 1.5 * s)),  # руки вверх
        (E, (-2.9 * s, 0, 6.2 * s), 1.0, (0.55 * s, 0.55 * s, 1.5 * s)),
        (E, (0.7 * s, 0, 0.6 * s), 1.0, (0.55 * s, 0.6 * s, 0.9 * s)),  # ноги
        (E, (-0.7 * s, 0, 0.6 * s), 1.0, (0.55 * s, 0.6 * s, 0.9 * s)),
    ]
    gloves = [
        ("BALL", (2.9 * s, -0.1 * s, 8.4 * s), 1.25 * s, None),
        ("BALL", (-2.9 * s, -0.1 * s, 8.4 * s), 1.25 * s, None),
        ("BALL", (2.2 * s, -0.7 * s, 8.0 * s), 0.55 * s, None),
        ("BALL", (-2.2 * s, -0.7 * s, 8.0 * s), 0.55 * s, None),
        (E, (0, 0, 2.2 * s), 1.0, (1.45 * s, 1.35 * s, 0.75 * s)),  # трусы
    ]
    white = [
        (E, (2.9 * s, 0, 7.1 * s), 1.0, (0.75 * s, 0.75 * s, 0.35 * s)),
        (E, (-2.9 * s, 0, 7.1 * s), 1.0, (0.75 * s, 0.75 * s, 0.35 * s)),
        (E, (0, 0, 2.85 * s), 1.0, (1.42 * s, 1.32 * s, 0.22 * s)),  # пояс
        ("BALL", (0.5 * s, -1.0 * s, 6.5 * s), 0.38 * s, None),  # глаза
        ("BALL", (-0.5 * s, -1.0 * s, 6.5 * s), 0.38 * s, None),
    ]
    dark = [
        ("BALL", (0.5 * s, -1.28 * s, 6.45 * s), 0.18 * s, None),
        ("BALL", (-0.5 * s, -1.28 * s, 6.45 * s), 0.18 * s, None),
        (E, (0.55 * s, -1.05 * s, 6.98 * s), 1.0, (0.4 * s, 0.15 * s, 0.1 * s)),  # брови
        (E, (-0.55 * s, -1.05 * s, 6.98 * s), 1.0, (0.4 * s, 0.15 * s, 0.1 * s)),
        (E, (0, -1.08 * s, 5.85 * s), 1.0, (0.35 * s, 0.12 * s, 0.1 * s)),  # рот
    ]
    return [mb_object("HCactus" + tag, "3FA64A", cactus, at, coll), mb_object("HGlove" + tag, "D2302B", gloves, at, coll),
            mb_object("HWhite" + tag, "F4F1E8", white, at, coll), mb_object("HDark" + tag, "1E2A1E", dark, at, coll)]


def mat_key(o):
    return o.data.materials[0].name if (o.type == "MESH" and o.data.materials) else ""


def near(o, p_game, r):
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for cc in o.bound_box:
        w = o.matrix_world @ Vector(cc)
        lo, hi = Vector(map(min, lo, w)), Vector(map(max, hi, w))
    return ((lo + hi) / 2 - K.P(*p_game)).length < r


def bevelled(o, coll):
    """Копия бруска надстройки со скруглёнными рёбрами («гладкая лепка» перед вокселями)."""
    d = o.dimensions
    w = min(1.4, 0.32 * min(d))
    c = o.copy()
    c.data = o.data.copy()
    coll.objects.link(c)
    c.data.transform(c.matrix_basis)  # масштаб и поворот — в вершины: фаска в стадах
    c.matrix_basis = Matrix.Identity(4)
    if w >= 0.2:
        mod = c.modifiers.new("Bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = w, 3, "NONE"
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(c.evaluated_get(dg))
        c.modifiers.clear()
        c.data = me
    return c


def top_of(objs):
    return max((o.matrix_world @ Vector(cc)).z for o in objs if o.type == "MESH" for cc in o.bound_box)


# ══ build: два этажа ══════════════════════════════════════════════════════════════════════════════════════════
if MODE == "build":
    bpy.ops.wm.open_mainfile(filepath=os.path.join(V2, "saloon_base.blend"))
    scene = bpy.context.scene
    coll = {c.name: c for c in bpy.data.collections}
    base_f = [o for o in bpy.data.objects if o.name.startswith("CB_F_")]
    work = bpy.data.collections.new("Work")
    scene.collection.children.link(work)
    work.hide_render = True
    # ── Космический: надстройки без плит, канта и прежней вывески; брусья скруглены; герой — метаболы
    t6 = list(coll["T6"].objects)
    crisp6 = [o for o in t6 if mat_key(o).startswith(("R_slab", "R_kant"))]
    sign6 = (0.0, 34.0, -Z - 3.0)
    keep6 = [o for o in t6 if o not in crisp6 and not (mat_key(o).startswith(("R_glove", "R_cuff", "R_trim"))
                                                       and near(o, sign6, 9.0))]
    # терраса героя (из надстроек) — у верха её плиты, y ≈ 27.1
    soft6 = [bevelled(o, work) for o in keep6]
    hero6 = hero((0.0, 27.1, -Z - 3.0), 2.6, work, "6")
    grid6, org6, st6, pal6 = voxelize(base_f + soft6 + hero6, STEP)
    q6 = greedy(grid6, org6, st6)
    vox_coll = bpy.data.collections.new("VOX6")
    scene.collection.children.link(vox_coll)
    vox6 = build_mesh("Vox6", q6, pal6, vox_coll, st6)
    for o in crisp6:
        vox_coll.objects.link(o)
    n6 = report("Космический (этаж целиком, шаг %.2f)" % STEP, grid6, q6)
    far6 = downsample(grid6, int(STEP_FAR / STEP))
    qf6 = greedy(far6, org6, STEP_FAR)
    nf6 = report("Космический — дальняя версия (шаг %.1f)" % STEP_FAR, far6, qf6)
    top6 = top_of([vox6] + crisp6)
    print("CHECK_TOP %s Космический воксельный: верх деталей %.2f, верх плиты %.2f" % (
        "OK" if top6 <= H[5] - 1 + 1e-3 else "FAIL", top6, H[5] - 1), flush=True)
    # ── Золотой: D39, прежняя вывеска убрана, герой на переднем балконе — микро-воксели
    t4 = list(coll["T4"].objects)
    sign4 = (0.0, 19.0 + 8.35 * 0.6, -Z - 2.9)
    drop4 = [o for o in t4 if mat_key(o).startswith(("R_glove", "R_cuff", "R_trim")) and near(o, sign4, 4.6)]
    gold = bpy.data.collections.new("GOLD4")
    scene.collection.children.link(gold)
    for o in t4:
        if o not in drop4:
            gold.objects.link(o)
    for o in list(gold.objects):  # балкон второго яруса спереди (y 27…30): проём |x| < 7 над героем
        ws = [o.matrix_world @ Vector(cc) for cc in o.bound_box]
        zlo, zhi = min(w.z for w in ws), max(w.z for w in ws)
        ylo = min(w.y for w in ws)
        xlo, xhi = min(w.x for w in ws), max(w.x for w in ws)
        if 27.0 < zlo < 30.5 and ylo < -Z - 1.0 and xlo < -7 and xhi > 7:
            for a, b in ((xlo, -7.0), (7.0, xhi)):
                c = o.copy()
                gold.objects.link(c)
                c.location.x = (a + b) / 2
                c.scale.x = (b - a) / (o.dimensions.x / o.scale.x)
            gold.objects.unlink(o)
    hero4 = hero((0.0, 19.5, -Z - 1.6), 1.5, work, "4")
    grid4, org4, st4, pal4 = voxelize(hero4, HERO_STEP, colors_k=8)
    q4 = greedy(grid4, org4, st4)
    vox4 = build_mesh("Vox4Hero", q4, pal4, gold, st4)
    n4 = report("Золотой — герой (шаг %.2f)" % HERO_STEP, grid4, q4)
    far4 = downsample(grid4, int(STEP_FAR / HERO_STEP))
    report("Золотой — герой, дальняя версия (шаг %.1f)" % STEP_FAR, far4, greedy(far4, org4, STEP_FAR))
    top4 = top_of([vox4] + [o for o in gold.objects if o.type == "MESH"] + base_f)
    print("CHECK_TOP %s Золотой с героем: верх деталей %.2f, верх плиты %.2f" % (
        "OK" if top4 <= H[3] - 1 + 1e-3 else "FAIL", top4, H[3] - 1), flush=True)
    d4 = [(vox4.matrix_world @ Vector(cc)) for cc in vox4.bound_box]
    print("HERO4 вынос вперёд %.2f (предел 4)" % (max(-p.y for p in d4) - Z), flush=True)
    # ── кадры: тот же ракурс, что у листа Б v2
    cam = scene.camera
    scene.render.resolution_x, scene.render.resolution_y = 900, 1100

    def aim(eye, target, fov):
        cam.data.angle_y = math.radians(fov)
        e, t = K.P(*eye), K.P(*target)
        cam.location = e
        cam.rotation_euler = (e - t).to_track_quat("Z", "Y").to_euler()

    base_coll = base_f[0].users_collection[0]

    def show(names, base=True):
        for c in scene.collection.children:
            if c.name.startswith(("T", "VOX", "GOLD", "Work")):
                c.hide_render = c.name not in names
        base_coll.hide_render = not base

    def render(name):
        scene.render.filepath = os.path.join(OUT, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("SHOT", name, flush=True)

    aim((-104, 40, -118), (0, 27, -2), 36)
    show({"T6"})
    render("cosmic_d39")
    show({"VOX6"}, base=False)
    render("cosmic_vox")
    show({"GOLD4"})
    render("gold_vox_hero")
    show({"VOX6"}, base=False)
    aim((-34, 40, -52), (0, 36, -14), 40)
    render("cosmic_vox_close")
    show({"GOLD4"})
    aim((-12, 27, -32), (0, 25, -18), 42)
    render("gold_hero_close")
    for o in list(work.objects):
        bpy.data.objects.remove(o)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "voxel_exp.blend"))
    with open(os.path.join(OUT, "numbers.txt"), "w", encoding="utf-8") as f:
        f.write("cosmic %d %d %d far %d %d\nhero %d %d %d\n" % (n6 + nf6[1:] + n4))
    print("DONE_BUILD", flush=True)
    sys.exit(0)

# ══ tower: 1-6-3-5-2-4 с воксельными этажами, колпак C ══════════════════════════════════════════════════════════
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "voxel_exp.blend"))
scene = bpy.context.scene
coll = {c.name: c for c in bpy.data.collections}
cb_base = [o for o in bpy.data.objects if o.name.startswith(("CB_F_", "CB_I_"))]
with bpy.data.libraries.load(os.path.join(V2, "aquarium_base.blend")) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith(("AQ_F_", "AQ_I_"))]
    dst.collections = ["T3", "T5"]
aq_base = [o for o in dst.objects if o is not None]
aq_t = {k: list(c.objects) for k, c in zip(("T3", "T5"), dst.collections)}  # имена в файле — с суффиксом
for c in scene.collection.children:
    c.hide_render = True
TX = 400.0
ORDER = [(1, "cb", list(coll["T1"].objects)), (6, "vox", list(coll["VOX6"].objects)), (3, "aq", aq_t["T3"]),
         (5, "aq", aq_t["T5"]), (2, "cb", list(coll["T2"].objects)), (4, "cb", list(coll["GOLD4"].objects))]
tower = bpy.data.collections.new("Tower")
scene.collection.children.link(tower)
y = 0.0
floor_y = {}
for t, kind, over in ORDER:
    oy = y + 1.0
    off = Vector((-TX, 0, oy))
    src = over + (cb_base if kind == "cb" else aq_base if kind == "aq" else [])
    made = []
    for o in src:
        c = o.copy()
        tower.objects.link(c)
        c.location = o.location + off
        made.append(c)
    bpy.context.view_layer.update()
    top = max((c.matrix_world @ Vector(cc)).z for c in made if c.type == "MESH" for cc in c.bound_box
              if abs(cc[0]) < 29 and abs(cc[1]) < 29) - oy
    print("CHECK_TOP %s башня %s %s: верх %.2f ≤ %d" % ("OK" if top <= H[t - 1] - 1 + 1e-3 else "FAIL", kind,
                                                       NAMES[t - 1], top, H[t - 1] - 1), flush=True)
    floor_y[t] = y
    y += H[t - 1]
ry = y
print("TOWER_HEIGHT", ry, flush=True)


def gbox(key_hex, x0, x1, y0, y1, z0, z1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=K.P((x0 + x1) / 2 + TX, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.active_object
    o.scale = (abs(x1 - x0), abs(z1 - z0), abs(y1 - y0))
    for c in o.users_collection:
        c.objects.unlink(o)
    tower.objects.link(o)
    m = bpy.data.materials.new("C_" + key_hex)
    m.use_nodes = True
    rgb = [int(key_hex[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (
        *[c**2.2 for c in rgb], 1)
    o.data.materials.append(m)
    return o


def gcone(key_hex, r1, r2, y0, y1, x=0.0, z=0.0, n=4):
    bpy.ops.mesh.primitive_cone_add(vertices=n, radius1=r1, radius2=r2, depth=y1 - y0,
                                    location=K.P(x + TX, (y0 + y1) / 2, z))
    o = bpy.context.active_object
    for c in o.users_collection:
        c.objects.unlink(o)
    tower.objects.link(o)
    m = bpy.data.materials.new("C_" + key_hex)
    m.use_nodes = True
    rgb = [int(key_hex[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (
        *[c**2.2 for c in rgb], 1)
    o.data.materials.append(m)


# колпак C (как в листе Б v2): сад, золотое кольцо, кристалл в когтях; кант лучшего этажа (Космический — радужный)
gbox("4E9A3A", -X + 1, X - 1, ry, ry + 1.5, -Z + 1, Z - 1)
gcone("E9B43A", 9.5, 9.5, ry + 1.5, ry + 4.5, n=8)
gcone("FF5FA8", 10.0, 10.0, ry + 4.5, ry + 5.5, n=8)
gcone("38D6E0", 0.01, 8.5, ry + 5.5, ry + 19.0)
gcone("38D6E0", 8.5, 0.01, ry + 19.0, ry + 35.0)
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    cx, cz = math.cos(a) * 9.2, math.sin(a) * 9.2
    gbox("E9B43A", cx - 1.6, cx + 1.6, ry + 4.5, ry + 23.0, cz - 1.6, cz + 1.6)
tower.hide_render = False
cam = scene.camera


def aim(eye, target, fov, w=900, h=1600):
    scene.render.resolution_x, scene.render.resolution_y = w, h
    cam.data.angle_y = math.radians(fov)
    e, t = K.P(eye[0] + TX, eye[1], eye[2]), K.P(target[0] + TX, target[1], target[2])
    cam.location = e
    cam.rotation_euler = (e - t).to_track_quat("Z", "Y").to_euler()


def render(name):
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("SHOT", name, flush=True)


mid = ry / 2 + 10
aim((-230, mid + 70, -270), (0, mid + 14, 0), 52)
render("tower_full")
y6 = floor_y[6] + 30  # середина Космического этажа
aim((-20, y6 + 6, -60 - Z), (0, y6, -Z), 62, 1200, 900)  # с 60 стадов от фасада, на уровне этажа
render("tower_60_level")
aim((-12, 5, -60 - Z), (0, 70, -Z), 70, 900, 1200)  # с 60 стадов, глаза игрока у земли
render("tower_60_ground")
y4 = floor_y[4] + 19
aim((-38, y4 + 8, -44 - Z), (0, y4 - 2, -Z), 58, 1200, 900)  # крупно: Золотой с героем
render("tower_close_gold")
print("DONE_TOWER", flush=True)

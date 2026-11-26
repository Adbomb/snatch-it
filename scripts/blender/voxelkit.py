"""Микро-воксели для этажей D74 (принято владельцем 2026-11-26: «кубики» текстурой, склейка граней).

  voxelize(objs, step)  — воксели поверхности объектов на сетке, кратной стаду; цвет — от треугольника: у объектов с
                          bake=1 свет запечён (переходы оттенков, блики на выпуклостях), у объектов с fixed=<имя> —
                          точный цвет палитры (светящиеся акценты, стекло) без квантования; прочее — k-средних;
  carve(...)            — врезанный проём (окно, дверь, иллюминатор): дыра в оболочке, откос цвета рамы, стекло
                          в глубине;
  greedy(...)           — склейка граней одного цвета в прямоугольники;
  build_mesh(...)       — меш: цвет из карты-палитры (UV «UV») × плитка «кубики» (UV «Cell», клетка = воксель: шов, скос,
                          свой оттенок), светящиеся цвета — второй материал со свечением;
  mb(...)               — лепка метаболами (семья — одно имя; элементы в координатах игры) → меш с цветом.
Координаты игры (y — вверх) переводятся в Blender функцией floorkit.P. Зависит от bpy, numpy, floorkit.
"""

import math

import bpy
import numpy as np
from mathutils import Vector

import floorkit as K

CELLS = 64  # клеток-вокселей в одной плитке «кубики»
CELL_PX = 8
MESH_LIMIT = 20000
LIGHT = np.array([0.35, -0.55, 0.75]) / np.linalg.norm([0.35, -0.55, 0.75])  # сверху, спереди слева (Blender)


def hex_rgb(h):
    return np.array([int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)])


def lin2srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def srgb2lin(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.04045, c / 12.92, np.power((c + 0.055) / 1.055, 2.4))


def obj_tris(o):
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


def obj_colors(o, tris):
    """sRGB 0…1 каждого треугольника: «Col» × тон материала, иначе цвет материала; bake=1 — запечённый свет."""
    me = o.data
    n = len(tris)
    mat = me.materials[0] if me.materials else None
    tint = np.ones(3)
    base = np.array([0.8, 0.8, 0.8])
    if mat and mat.use_nodes:
        mix = next((nd for nd in mat.node_tree.nodes if nd.type == "MIX"), None)
        bsdf = next((nd for nd in mat.node_tree.nodes if nd.type == "BSDF_PRINCIPLED"), None)
        if mix is not None and not mix.inputs[6].is_linked:
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
        lin = cc[lt.reshape(-1, 3)].mean(axis=1) * tint
    else:
        lin = np.tile(base, (n, 1))
    if o.get("bake"):
        nrm = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
        d = np.clip(nrm @ LIGHT, 0, 1)
        zc = tris[:, :, 2].mean(axis=1)
        h = (zc - zc.min()) / max(1e-6, zc.max() - zc.min())
        shade = (0.58 + 0.5 * d + 0.08 * np.clip(nrm[:, 2], 0, 1)) * (0.86 + 0.14 * h)
        lin = lin * shade[:, None] + 0.22 * np.clip((d - 0.82) / 0.18, 0, 1)[:, None] ** 2  # блик на выпуклостях
    return lin2srgb(lin)


def sample_tris(tris, colors, fixed, step):
    pts, cols, fxs = [], [], []
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
        fxs.append(np.repeat(fixed[sel], p.shape[1]))
    return np.concatenate(pts), np.concatenate(cols), np.concatenate(fxs)


def voxelize(objs, step, colors_k=24, fixed_colors=None, clip=29.5):
    """→ (grid int16 [-1 — пусто], origin, step, palette sRGB, индексы фиксированных цветов {имя: i})."""
    fixed_colors = fixed_colors or {}
    fnames = list(fixed_colors)
    allp, allc, allf = [], [], []
    for o in objs:
        if o.type != "MESH" or len(o.data.polygons) == 0:
            continue
        tris = obj_tris(o)
        t0 = np.array(o.matrix_world.translation)
        rel = tris - t0
        keep = ((np.abs(rel[:, :, 0]) < clip) & (np.abs(rel[:, :, 1]) < clip)).all(axis=1)  # без якорей floorbase ±30
        if not keep.any():
            continue
        tris = tris[keep]
        cols = obj_colors(o, tris)
        fx = np.full(len(tris), fnames.index(o["fixed"]) if o.get("fixed") in fnames else -1)
        p, c, f = sample_tris(tris, cols, fx, step)
        allp.append(p)
        allc.append(c)
        allf.append(f)
    p, c, f = np.concatenate(allp), np.concatenate(allc), np.concatenate(allf)
    idx = np.floor(p / step + 1e-6).astype(np.int64)
    lo = idx.min(axis=0) - 2
    idx -= lo
    dims = idx.max(axis=0) + 3
    flat = np.ravel_multi_index(idx.T, dims)
    order = np.argsort(flat, kind="stable")
    flat_s = flat[order]
    last = np.r_[flat_s[1:] != flat_s[:-1], True]
    vox = flat_s[last]
    vcol, vfix = c[order][last], f[order][last]
    free = vfix < 0
    k = min(colors_k, int(free.sum()))
    rng = np.random.default_rng(7)
    pal = vcol[free][rng.choice(int(free.sum()), k, replace=False)]
    for _ in range(14):
        lab = np.argmin(((vcol[free][:, None, :] - pal[None]) ** 2).sum(-1), axis=1)
        for j in range(k):
            if np.any(lab == j):
                pal[j] = vcol[free][lab == j].mean(axis=0)
    lab = np.argmin(((vcol[:, None, :] - pal[None]) ** 2).sum(-1), axis=1)
    lab = np.where(free, lab, k + vfix)
    palette = np.concatenate([pal, np.array([hex_rgb(fixed_colors[n]) for n in fnames]).reshape(-1, 3)])
    grid = np.full(dims, -1, dtype=np.int16)
    grid.flat[vox] = lab
    return grid, lo * step, step, palette, {n: k + i for i, n in enumerate(fnames)}


def to_cell(origin, step, p_blender):
    return np.floor((np.array(p_blender) - origin) / step + 1e-6).astype(int)


def carve(grid, origin, step, center_game, half_a, half_b, face, glass, frame, depth=2, round_=False, fill=None):
    """Врезанный проём на грани face ('front' | 'back' | 'left' | 'right') вокруг центра (координаты игры): дыра
    полуразмером half_a (вдоль стены) × half_b (по высоте), откос цвета frame, стекло glass в глубине depth вокселей;
    fill — цвет «створок» (дверь салуна) вместо стекла."""
    c = to_cell(origin, step, K.P(*center_game))
    ax = 1 if face in ("front", "back") else 0  # Blender: y = z игры, x = −x игры
    inward = 1 if face == "front" else -1 if face == "back" else (-1 if face == "left" else 1)
    if face == "left":
        inward = -1  # левый бок игры (x < 0) — это Blender x > 0: внутрь — к меньшим x
    elif face == "right":
        inward = 1
    other = 0 if ax == 1 else 1
    na, nb = int(round(half_a / step)), int(round(half_b / step))
    cols = []
    for da in range(-na, na + 1):
        for db in range(-nb, nb + 1):
            if round_ and (da / max(na, 1)) ** 2 + (db / max(nb, 1)) ** 2 > 1.0:
                continue
            cols.append((da, db))
    if not cols:
        return
    surf = {}
    for da, db in cols:
        idx = [0, 0, 0]
        idx[other], idx[2] = c[other] + da, c[2] + db
        if not (0 <= idx[other] < grid.shape[other] and 0 <= idx[2] < grid.shape[2]):
            continue
        line = grid[idx[0], :, idx[2]] if ax == 1 else grid[:, idx[1], idx[2]]
        occ = np.nonzero(line >= 0)[0]
        if len(occ) == 0:
            continue
        surf[(da, db)] = occ[0] if inward > 0 else occ[-1]
    if not surf:
        return
    s_med = int(np.median(list(surf.values())))
    back = s_med + inward * depth
    edge = set()
    for da, db in surf:
        for dd in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (da + dd[0], db + dd[1]) not in surf:
                edge.add((da, db))
    for (da, db), s0 in surf.items():
        rng_ = range(min(s0, back), max(s0, back) + 1)
        for t in rng_:
            idx = [0, 0, 0]
            idx[other], idx[2], idx[ax] = c[other] + da, c[2] + db, t
            if not all(0 <= idx[i] < grid.shape[i] for i in range(3)):
                continue
            if (da, db) in edge:
                grid[tuple(idx)] = frame
            elif t == back:
                grid[tuple(idx)] = glass if fill is None else fill
            else:
                grid[tuple(idx)] = -1


def faces_count(grid):
    occ = grid >= 0
    n = 0
    for a in range(3):
        pad = np.pad(occ, [(1, 1) if i == a else (0, 0) for i in range(3)])
        sl0, sl1 = [slice(None)] * 3, [slice(None)] * 3
        sl0[a], sl1[a] = slice(1, -1), slice(2, None)
        n += np.count_nonzero(pad[tuple(sl0)] & ~pad[tuple(sl1)])
        sl1[a] = slice(0, -2)
        n += np.count_nonzero(pad[tuple(sl0)] & ~pad[tuple(sl1)])
    return n


def greedy(grid, origin, step):
    occ = grid >= 0
    quads = []
    other = {0: (1, 2), 1: (0, 2), 2: (0, 1)}
    for a in range(3):
        b, c = other[a]
        for s in (-1, 1):
            shifted = np.full(occ.shape, False)
            src, dst = [slice(None)] * 3, [slice(None)] * 3
            if s > 0:
                src[a], dst[a] = slice(1, None), slice(0, -1)
            else:
                src[a], dst[a] = slice(0, -1), slice(1, None)
            shifted[tuple(dst)] = occ[tuple(src)]
            face = occ & ~shifted
            for i in np.nonzero(face.any(axis=tuple(x for x in range(3) if x != a)))[0]:
                sl = [slice(None)] * 3
                sl[a] = i
                m = np.where(face[tuple(sl)], grid[tuple(sl)], -1)
                vis = np.zeros(m.shape, dtype=bool)
                plane = origin[a] + (i + (1 if s > 0 else 0)) * step
                vs, us = np.nonzero(m.T >= 0)
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


def downsample(grid, f):
    d = [(s + f - 1) // f * f for s in grid.shape]
    g = np.full(d, -1, dtype=np.int16)
    g[: grid.shape[0], : grid.shape[1], : grid.shape[2]] = grid
    g = g.reshape(d[0] // f, f, d[1] // f, f, d[2] // f, f).transpose(0, 2, 4, 1, 3, 5).reshape(
        d[0] // f, d[1] // f, d[2] // f, -1)
    out = np.full(g.shape[:3], -1, dtype=np.int16)
    for i, j, k in zip(*np.nonzero((g >= 0).sum(-1) > 0)):
        v = g[i, j, k]
        out[i, j, k] = np.bincount(v[v >= 0]).argmax()
    return out


_cell_img = None


def cell_image():
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


def palette_material(name, palette, glow=0.0):
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
    uv_a, uv_b = nt.nodes.new("ShaderNodeUVMap"), nt.nodes.new("ShaderNodeUVMap")
    uv_a.uv_map, uv_b.uv_map = "UV", "Cell"
    tex, cells = nt.nodes.new("ShaderNodeTexImage"), nt.nodes.new("ShaderNodeTexImage")
    tex.image, cells.image = img, cell_image()
    tex.interpolation = cells.interpolation = "Closest"
    nt.links.new(uv_a.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(uv_b.outputs["UV"], cells.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    nt.links.new(tex.outputs["Color"], mix.inputs[6])
    nt.links.new(cells.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.7
    if glow:
        nt.links.new(mix.outputs[2], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = glow
    return m


def build_mesh(name, quads, palette, coll, step, glow_idx=()):
    n = len(palette)
    verts, faces, uvs, cuv = [], [], [], []
    for p, col in quads:
        k = len(verts)
        verts.extend(p)
        faces.append((k, k + 1, k + 2, k + 3))
        uvs.extend([((col + 0.5) / n, 0.5)] * 4)
        arr = np.array(p)
        a = int(np.argmin(arr.max(axis=0) - arr.min(axis=0)))
        b, c = [i for i in range(3) if i != a]
        for q in p:
            cuv.append((q[b] / step / CELLS, q[c] / step / CELLS))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.uv_layers.new(name="UV").data.foreach_set("uv", np.array(uvs, dtype=np.float32).ravel())
    me.uv_layers.new(name="Cell").data.foreach_set("uv", np.array(cuv, dtype=np.float32).ravel())
    me.materials.append(palette_material(name + "_Pal", palette))
    me.materials.append(palette_material(name + "_Glow", palette, glow=1.1))
    gl = set(glow_idx)
    me.polygons.foreach_set("material_index", np.array([1 if c in gl else 0 for _, c in quads], dtype=np.int32))
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def report(label, grid, quads):
    before, after = faces_count(grid) * 2, len(quads) * 2
    meshes = max(1, math.ceil(after / MESH_LIMIT))
    print("NUM %s: вокселей %d, треугольников до склейки %d, после %d, мешей %d" % (
        label, int((grid >= 0).sum()), before, after, meshes), flush=True)
    return {"label": label, "before": before, "after": after, "meshes": meshes}


_mb_k = {}


def _mb_ratio(kind):
    """Где у метабола реальная поверхность: доля от заданного размера (меряется один раз на тип)."""
    if kind in _mb_k:
        return _mb_k[kind]
    data = bpy.data.metaballs.new("_probe")
    data.resolution = data.render_resolution = 0.2
    el = data.elements.new(type=kind)
    el.co = (0, 0, 0)
    if kind == "BALL":
        el.radius = 10.0
    else:
        el.radius = 1.0
        el.size_x = el.size_y = el.size_z = 10.0
    ob = bpy.data.objects.new("_probe", data)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    half = max(abs(v.co.x) for v in me.vertices) if len(me.vertices) else 10.0
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    _mb_k[kind] = max(0.2, half / 10.0)
    print("MB_RATIO", kind, round(_mb_k[kind], 3), flush=True)
    return _mb_k[kind]


def mb(family, color_hex, elements, coll, bake=True, fixed=None, res=0.3):
    """Лепка метаболами: elements — (тип, (x, y, z) игры, радиус, (sx, sy, sz) игры | None). Семья — одно имя (разные
    семьи не сливаются). → меш-объект с цветом материала (bake — запечь свет, fixed — точный цвет палитры)."""
    data = bpy.data.metaballs.new(family)
    data.resolution = data.render_resolution = res
    for kind, co, r, size in elements:
        el = data.elements.new(type=kind)
        el.co = K.P(*co)
        k = _mb_ratio(kind) if kind in ("BALL", "ELLIPSOID") else 1.0  # размеры в коде — настоящая поверхность
        el.radius = r / k if kind == "BALL" else r
        if size is not None:
            el.size_x, el.size_y, el.size_z = size[0] / k, size[2] / k, size[1] / k
    ob = bpy.data.objects.new(family, data)
    coll.objects.link(ob)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob)
    mo = bpy.data.objects.new(family + "_Mesh", me)
    coll.objects.link(mo)
    m = bpy.data.materials.new(family + "_M")
    m.use_nodes = True
    next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (
        *srgb2lin(hex_rgb(color_hex)), 1)
    me.materials.append(m)
    if bake:
        mo["bake"] = 1
    if fixed:
        mo["fixed"] = fixed
    return mo


def bounds_game(objs):
    """Габариты объектов в координатах игры: (lo, hi) как Vector(x, y, z)."""
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            g = Vector((-w.x, w.z, w.y))
            lo, hi = Vector(map(min, lo, g)), Vector(map(max, hi, g))
    return lo, hi

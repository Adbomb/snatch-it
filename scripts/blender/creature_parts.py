"""Part-версия существ босса 3 (D55, этап D): блоки по подвижным частям из FBX D54 — до импорта мешей в игре.

Импорт и загрузка мешей пока запрещены владельцем, поэтому в игре существо собирается из блоков Roblox: каждая
подвижная часть (Body, Head, LegFL…) — свой набор блоков вокруг своей точки вращения (pivot), суставы — Motor6D по
rig.json, анимация та же, что будет у мешей. Подставка, которую в игре скрывают (stand_policy hide, D54), и скрываемые с
ней части не строятся. Блоки: объём части (вокселизация меша: точка внутри по ближайшей грани или ближе полвокселя к
поверхности — тонкие пластины не пропадают); каждый воксель помечен цветом ближайшей грани — цвета грани по карте D39
(color.png) части делятся на 1–3 группы (зрачок, рот, зубы — отдельно от тела), и воксели одной группы жадно сливаются в
прямоугольники цвета этой группы. Бюджет — ≤ 40 блоков на существо (CLAUDE.md: предмет 8–40): делится между частями по
размеру (у каждой хотя бы один), у каждой — самый мелкий воксель, при котором она укладывается в свою долю; лишнее
(округления) — самые маленькие блоки (у части остаётся хотя бы один). Пишет assets/models/art/Boss3Creatures.parts.json (оси Roblox, центр блока — от точки вращения части) и кадры
<рендеры>/<id>.png (FBX с картой и блоки рядом) для листа scripts/d55_creature_sheets.py.
Запуск: blender --background --factory-startup --python scripts/blender/creature_parts.py -- <репо> <рендеры> [id…]
Зависит от art_style.py (студия кадров).
"""

import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(OUT, exist_ok=True)
ART = os.path.join(REPO, "assets", "models", "art")
INDEX = json.load(open(os.path.join(ART, "Boss3Creatures.index.json"), encoding="utf-8"))
ONLY = set(argv[2:])
BUDGET = 40
VOXELS = (0.1, 0.12, 0.15, 0.18, 0.22, 0.27, 0.33, 0.4, 0.5, 0.65, 0.8)


def to_rbx(v):
    return Vector((v.x, v.z, -v.y))


def world_bm(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    bm.normal_update()
    return bm


def face_colors(o, tex):
    """Цвет каждой грани (многоугольника) части: среднее карты по её треугольникам (по площади) и площадь."""
    me = o.data
    me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    h, w = tex.shape[:2]
    acc = np.zeros((len(me.polygons), 3))
    area = np.zeros(len(me.polygons))
    for lt in me.loop_triangles:
        for k in range(3):  # три точки внутри треугольника — ровнее, чем одна в центре (кольца D39)
            a = Vector((0, 0))
            for j, li in enumerate(lt.loops):
                a += uv[li].uv * (0.6 if j == k else 0.2)
            px = tex[min(h - 1, max(0, int((1 - a.y) * h))), min(w - 1, max(0, int(a.x * w)))]
            acc[lt.polygon_index] += np.array(px[:3]) * lt.area / 3
        area[lt.polygon_index] += lt.area
    return acc / np.maximum(area, 1e-9)[:, None], area


def clusters(cols, area, k=3):
    """Группы цветов граней (k-средних по площади): метка каждой грани и цвет группы. Мелкие (< 2.5 % площади) и
    близкие (< 0.14) группы сливаются с ближайшей."""
    if len(cols) == 0:
        return np.zeros(0, dtype=int), [np.array([0.5, 0.5, 0.5])]
    order = np.argsort(-area)
    centers = [cols[order[0]]]
    for _ in range(1, k):  # следующий центр — самый далёкий от уже выбранных
        d = np.min([np.linalg.norm(cols - c, axis=1) for c in centers], axis=0) * (area > 0)
        if d.max() < 0.14:
            break
        centers.append(cols[int(np.argmax(d))])
    centers = np.array(centers)
    for _ in range(8):
        label = np.argmin([np.linalg.norm(cols - c, axis=1) for c in centers], axis=0)
        for j in range(len(centers)):
            m = label == j
            if area[m].sum() > 0:
                centers[j] = (cols[m] * area[m][:, None]).sum(0) / area[m].sum()
    total = area.sum()
    keep = [j for j in range(len(centers)) if area[label == j].sum() >= 0.025 * total] or [0]
    merged = []
    for j in keep:
        if all(np.linalg.norm(centers[j] - centers[m]) >= 0.14 for m in merged):
            merged.append(j)
    centers = centers[merged]
    label = np.argmin([np.linalg.norm(cols - c, axis=1) for c in centers], axis=0)
    return label, list(centers)


def voxel_boxes(bm, vox, face_label, colors):
    """Объём меша → жадно слитые прямоугольники одного цвета (мир Blender): [(lo, hi, цвет)]. Метка вокселя —
    группа цвета ближайшей грани."""
    tree = BVHTree.FromBMesh(bm)
    co = [v.co for v in bm.verts]
    lo = Vector([min(c[i] for c in co) for i in range(3)])
    hi = Vector([max(c[i] for c in co) for i in range(3)])
    n = [max(1, int(math.ceil((hi[i] - lo[i]) / vox))) for i in range(3)]
    step = Vector([(hi[i] - lo[i]) / n[i] for i in range(3)])
    label = np.full(n, -1, dtype=int)
    for ix in range(n[0]):
        for iy in range(n[1]):
            for iz in range(n[2]):
                c = lo + Vector(((ix + 0.5) * step.x, (iy + 0.5) * step.y, (iz + 0.5) * step.z))
                loc, normal, index, dist = tree.find_nearest(c)
                if loc is None:
                    continue
                if dist < 0.5 * min(step) or (c - loc).dot(normal) < 0:
                    label[ix, iy, iz] = face_label[index] if index < len(face_label) else 0
    used = np.zeros(n, dtype=bool)
    boxes = []
    for iz in range(n[2]):
        for iy in range(n[1]):
            for ix in range(n[0]):
                g = label[ix, iy, iz]
                if g < 0 or used[ix, iy, iz]:
                    continue
                x1 = ix
                while x1 + 1 < n[0] and label[x1 + 1, iy, iz] == g and not used[x1 + 1, iy, iz]:
                    x1 += 1
                y1 = iy
                while (y1 + 1 < n[1] and (label[ix:x1 + 1, y1 + 1, iz] == g).all()
                       and not used[ix:x1 + 1, y1 + 1, iz].any()):
                    y1 += 1
                z1 = iz
                while (z1 + 1 < n[2] and (label[ix:x1 + 1, iy:y1 + 1, z1 + 1] == g).all()
                       and not used[ix:x1 + 1, iy:y1 + 1, z1 + 1].any()):
                    z1 += 1
                used[ix:x1 + 1, iy:y1 + 1, iz:z1 + 1] = True
                boxes.append((lo + Vector((ix * step.x, iy * step.y, iz * step.z)),
                              lo + Vector(((x1 + 1) * step.x, (y1 + 1) * step.y, (z1 + 1) * step.z)), colors[g]))
    if not boxes:  # совсем тонкая часть — её габарит
        boxes.append((lo, hi, colors[0]))
    return boxes


def hexcol(col):
    # карта уже в sRGB (to_srgb при запекании), пиксели Blender — как сохранены (Non-Color)
    return "".join(f"{int(round(max(0, min(1, x)) * 255)):02X}" for x in col)


def build_item(item):
    item_id = item["id"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(REPO, item["fbx"]))
    bpy.context.view_layer.update()
    img = bpy.data.images.load(os.path.join(REPO, item["maps"][0]))
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    tex = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
    prefix = f"Art_{item_id}_"
    objs = {o.name[len(prefix):]: o for o in bpy.context.scene.objects if o.type == "MESH" and o.name.startswith(prefix)}
    hidden = set(item.get("hide_with_stand") or [])
    if item.get("stand_policy") != "keep":
        hidden.add("Stand")
    build = {name: o for name, o in objs.items() if name not in hidden}
    groups = {}
    for name, o in build.items():
        cols, area = face_colors(o, tex)
        groups[name] = clusters(cols, area)
    # доля бюджета — по размеру части (площадь поверхности ~ объём^(2/3)), у каждой хотя бы один блок
    weight = {}
    for name, o in build.items():
        d = o.dimensions
        weight[name] = max(d.x * d.y * d.z, 1e-4) ** (2 / 3)
    total_w = sum(weight.values())
    share = {name: max(1, int(BUDGET * w / total_w)) for name, w in weight.items()}
    roles = {pp["name"]: pp.get("role") or "" for pp in item["parts"]}
    for name in build:
        # у глаза и других многоцветных частей — хотя бы по блоку на цвет (зрачок не теряется), не больше 3
        need = min(3, len(groups[name][1]))
        if roles.get(name, "").startswith("глаз"):
            need = max(need, 2)
        share[name] = max(share[name], need)
    parts = {}
    for name, o in build.items():
        bm = world_bm(o)
        label, colors = groups[name]
        best = None
        for vox in VOXELS:
            boxes = voxel_boxes(bm, vox, label, colors)
            best = boxes
            if len(boxes) <= share[name]:
                break
        parts[name] = best
        bm.free()
    vox = 0
    # не влезло и при крупном вокселе — убрать самые маленькие блоки (у каждой части остаётся самый большой)
    flat = [(name, b) for name, boxes in parts.items() for b in boxes]
    if len(flat) > BUDGET:
        keep = {name: max(boxes, key=lambda b: (b[1] - b[0]).length) for name, boxes in parts.items() if boxes}
        rest = sorted([fb for fb in flat if fb[1] is not keep[fb[0]]],
                      key=lambda fb: -((fb[1][1] - fb[1][0]).x * (fb[1][1] - fb[1][0]).y * (fb[1][1] - fb[1][0]).z))
        chosen = list(keep.items()) + rest[: BUDGET - len(keep)]
        parts = {name: [] for name in parts}
        for name, b in chosen:
            parts[name].append(b)
    out = {}
    for name, boxes in parts.items():
        pivot = objs[name].matrix_world.translation
        entries = []
        for b in boxes:
            col = b[2]
            lo, hi = to_rbx(b[0] - pivot), to_rbx(b[1] - pivot)
            mn = Vector([min(lo[i], hi[i]) for i in range(3)])
            mx = Vector([max(lo[i], hi[i]) for i in range(3)])
            entries.append({"c": [round(v, 3) for v in (mn + mx) / 2], "s": [round(v, 3) for v in mx - mn],
                            "col": hexcol(col)})
        out[name] = entries
    for name in hidden:
        if name in objs:
            out[name] = []  # скрывается в игре: блоков нет (сустав остаётся)
    return objs, parts, out, vox


def render_pair(item, objs, parts, out):
    """Кадр: FBX с картой слева, блоки справа (тот же ракурс 3/4)."""
    col = bpy.data.collections.new("Blocks")
    bpy.context.scene.collection.children.link(col)
    mats = {}
    shift = Vector((4.2, 0, 0))
    for name, entries in out.items():
        pivot = objs[name].matrix_world.translation
        for e in entries:
            c = Vector((e["c"][0], -e["c"][2], e["c"][1])) + pivot + shift
            s = (e["s"][0], e["s"][2], e["s"][1])
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=s, verts=bm.verts)
            bmesh.ops.translate(bm, vec=c, verts=bm.verts)
            me = bpy.data.meshes.new("Blk")
            bm.to_mesh(me)
            bm.free()
            key = e["col"]
            if key not in mats:
                m = bpy.data.materials.new(key)
                m.use_nodes = True
                b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
                b.inputs["Base Color"].default_value = (*S.lin(key), 1)
                b.inputs["Roughness"].default_value = 0.55
                mats[key] = m
            me.materials.append(mats[key])
            col.objects.link(bpy.data.objects.new("Blk", me))
    # FBX — материал с картой цвета
    tex_mat = bpy.data.materials.new("Tex")
    tex_mat.use_nodes = True
    nt = tex_mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(REPO, item["maps"][0]))
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    hide = set(item.get("hide_with_stand") or []) | ({"Stand"} if item.get("stand_policy") != "keep" else set())
    for name, o in objs.items():
        o.data.materials.clear()
        o.data.materials.append(tex_mat)
        o.hide_render = name in hide
    prev = S.Preview(bpy.context.scene.collection)
    center = Vector((2.1, 0, item["height"] / 2))
    prev.aim_lights(center)
    prev.shot(os.path.join(OUT, f"{item['id']}.png"), (center.x - 4.5, -9.5, item["height"] + 3.2), center, 50,
              (900, 520))


report, allparts = {}, {}
for item in INDEX["items"]:
    if ONLY and item["id"] not in ONLY:
        continue
    objs, parts, out, vox = build_item(item)
    allparts[item["id"]] = {"parts": out}
    report[item["id"]] = {"blocks": sum(len(v) for v in out.values()), "parts": len(out)}
    render_pair(item, objs, parts, out)
    print("CREATURE_OK", item["id"], json.dumps(report[item["id"]]), flush=True)

path = os.path.join(ART, "Boss3Creatures.parts.json")
if ONLY and os.path.exists(path):
    old = json.load(open(path, encoding="utf-8"))
    old.update(allparts)
    allparts = old
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(allparts, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("CREATURE_PARTS_OK", len(report), flush=True)

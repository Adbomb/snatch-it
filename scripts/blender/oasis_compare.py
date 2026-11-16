"""Сравнение версий существа босса 4 «до/после» (полировка): каждая версия — её игровой FBX и её карты, кадры одной
камерой, одним светом, одним фоном и одними настройками рендера; поза покоя, без обработки кадров.
Кадры фенека №20 (есть часть Cube): три четверти, спереди, сзади, морда спереди, лицо крупно, контуры D39 крупно,
кубик, медальон, кадр как в игре (песок пустыни, подставка скрыта, как у живого существа в игре, манекен Roblox 5.2
стада, кадр телефона 844 × 390) и замеры контура D39 прямо по карте цвета: профиль поперёк линии квадрата на затылке
(точки модели → UV → карта): глубина линии, ширина на половине глубины и ширина ската 10–90 % в текселях.
Кадры любого другого существа: три четверти, спереди, спереди-слева и спереди-справа под 45°, сбоку, сзади, сверху,
лицо крупно спереди и под 45° с обеих сторон, кадр как в игре; силуэты (чёрное на белом, без подставки) спереди и под
45°. Лицо — передняя грань части Head (если её нет — Body, иначе самой крупной части).
Запуск: blender --background --factory-startup --python scripts/blender/oasis_compare.py -- <репо> <папка кадров>
        <метка> <fbx> <префикс карт> [<метка> <fbx> <префикс карт> …]
Префикс карт: путь без _color.png / _normal.png. Пишет <папка>/<метка>_<кадр>.png и <папка>/metrics.json.
Зависит от art_style.py (студия, манекен).
"""

import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
MODELS = [(argv[i], os.path.abspath(argv[i + 1]), os.path.abspath(argv[i + 2])) for i in range(2, len(argv), 3)]
SAND, SKY = "DBAF5C", (0.62, 0.76, 0.98)  # SAND — пол зоны 4 (GameConfig.Zones, Desert)
STAND_H = 0.22  # высота подставки Rare: в игре подставку живого существа прячут
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Compare")
bpy.context.scene.collection.children.link(collection)


def material(tag, prefix):
    mat = bpy.data.materials.new(f"M_{tag}")
    mat.use_nodes = True
    mat.use_backface_culling = True  # как в Roblox
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.5  # шероховатость общая 0.5 (art_roughness.png)
    col = nt.nodes.new("ShaderNodeTexImage")
    col.image = bpy.data.images.load(prefix + "_color.png")
    col.interpolation = "Linear"
    nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    nrm = nt.nodes.new("ShaderNodeTexImage")
    nrm.image = bpy.data.images.load(prefix + "_normal.png")
    nrm.image.colorspace_settings.name = "Non-Color"
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return mat, col.image


def import_model(tag, fbx, prefix):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=fbx)
    objs = [o for o in bpy.data.objects if o not in before]
    mat, img = material(tag, prefix)
    root = bpy.data.objects.new(f"Root_{tag}", None)
    collection.objects.link(root)
    parts = {}
    for o in objs:
        if o.type != "MESH":
            continue
        o.data.materials.clear()
        o.data.materials.append(mat)
        part = o.name.split(".")[0].split("_", 2)[-1]
        o.name = f"{tag}_{part}"
        o.parent = root
        parts[part] = o
    return root, parts, img


models = {tag: import_model(tag, fbx, prefix) for tag, fbx, prefix in MODELS}


# ── Замер контура D39 по карте цвета ────────────────────────────────────────────────────────────────────────


def sampler(obj, img):
    me = obj.data
    me.calc_loop_triangles()
    m = obj.matrix_world
    verts = [m @ v.co for v in me.vertices]
    tris = [tuple(lt.vertices) for lt in me.loop_triangles]
    uvs = [[Vector(me.uv_layers[0].data[li].uv) for li in lt.loops] for lt in me.loop_triangles]
    tree = BVHTree.FromPolygons(verts, tris)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)  # sRGB-значения файла (байты PNG / 255)
    arr = px.reshape(h, w, 4)[..., :3]

    def at(p):
        loc, _, i, _ = tree.find_nearest(p)
        wts = poly_3d_calc([verts[k] for k in tris[i]], loc)
        uv = sum((uvs[i][k] * wts[k] for k in range(3)), Vector((0.0, 0.0)))
        x, y = uv.x * w - 0.5, uv.y * h - 0.5  # пиксели img.pixels идут снизу вверх, как v
        x0, y0 = int(math.floor(x)), int(math.floor(y))
        fx, fy = x - x0, y - y0
        c = (arr[y0, x0] * (1 - fx) * (1 - fy) + arr[y0, x0 + 1] * fx * (1 - fy) + arr[y0 + 1, x0] * (1 - fx) * fy
             + arr[y0 + 1, x0 + 1] * fx * fy)
        return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]), Vector((uv.x * w, uv.y * h))

    return at


def profile(at, p0, p1, n=241):
    p0, p1 = Vector(p0), Vector(p1)
    lum, tex = [], []
    for i in range(n):
        lv, t = at(p0.lerp(p1, i / (n - 1)))
        lum.append(lv)
        tex.append(t)
    lum = np.array(lum)
    pos = np.concatenate([[0.0], np.cumsum([(tex[i + 1] - tex[i]).length for i in range(n - 1)])])  # в текселях
    base = float(np.median(np.concatenate([lum[: n // 6], lum[-n // 6 :]])))
    dark = 1 - lum / base  # доля затемнения
    depth = float(dark.max())
    k = int(dark.argmax())

    def cross(level, side):
        i = k
        while 0 < i < n - 1 and dark[i] >= level:
            i += side
        j = i - side  # dark[j] ≥ level > dark[i]
        f = (dark[j] - level) / max(dark[j] - dark[i], 1e-9)
        return pos[j] + (pos[i] - pos[j]) * f

    fwhm = cross(depth / 2, 1) - cross(depth / 2, -1)
    ramp = ((cross(0.1 * depth, 1) - cross(0.9 * depth, 1)) + (cross(0.9 * depth, -1) - cross(0.1 * depth, -1))) / 2
    return {"depth": round(depth, 3), "fwhm_texels": round(float(fwhm), 2), "ramp_10_90_texels": round(float(ramp), 2),
            "texels_per_stud": round(float(pos[-1] / (p1 - p0).length), 1),
            "profile": [round(float(x), 4) for x in dark[::4]]}


metrics = {}
FENNEC = all("Cube" in parts for _, parts, _ in models.values())
for tag, (root, parts, img) in models.items():
    if not FENNEC:
        break
    at = sampler(parts["Head"], img)
    # затылок (грань y = 0.46, смотрит назад): квадрат D39 с центром x = 0, z = 2.2 (ряд z0 = 1.0, шаг 0.6);
    # его вертикальная сторона — x = 0.21, горизонтальная — z = 2.41 (полуразмер 0.21)
    metrics[tag] = {"vertical_edge": profile(at, (0.12, 0.461, 2.2), (0.30, 0.461, 2.2)),
                    "horizontal_edge": profile(at, (0.0, 0.461, 2.32), (0.0, 0.461, 2.50))}
    print("METRIC", tag, json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "profile"}
                                     for k, v in metrics[tag].items()}))


# ── Кадры ───────────────────────────────────────────────────────────────────────────────────────────────────


prev = S.Preview(collection)
scene = bpy.context.scene
scene.render.film_transparent = False
studio_world = scene.world
floor = bpy.data.objects["Floor"]
sky = bpy.data.worlds.new("Sky")
sky.use_nodes = True
bg = next(n for n in sky.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (*SKY, 1)
bg.inputs["Strength"].default_value = 0.7
sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy, sun_data.angle = 2.7, math.radians(3)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(42), 0, math.radians(-28))
scene.collection.objects.link(sun)
sand_mat = bpy.data.materials.new("Sand")
sand_mat.use_nodes = True
sb = next(n for n in sand_mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
sb.inputs["Base Color"].default_value = (*S.lin(SAND), 1)
sb.inputs["Roughness"].default_value = 0.8
sand_me = bpy.data.meshes.new("Sand")
sand_me.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
sand_me.materials.append(sand_mat)
sand = bpy.data.objects.new("Sand", sand_me)
collection.objects.link(sand)
S.mannequin(collection, -4.6, -5.8)  # игрок слева впереди, не заслоняет существо
men = [o for o in bpy.data.objects if o.name.startswith("Mannequin")]


def set_game(on):
    scene.world = sky if on else studio_world
    floor.hide_render = on
    for light, _ in prev.lights:
        light.hide_render = on
    sun.hide_render = not on
    sand.hide_render = not on
    for o in men:
        o.hide_render = not on


def only(tag):
    for t, (root, parts, _) in models.items():
        for o in parts.values():
            o.hide_render = t != tag


ref_root, ref_parts, _ = next(iter(models.values()))
bpy.context.view_layer.update()
co = [o.matrix_world @ v.co for o in ref_parts.values() for v in o.data.vertices]
lo = Vector([min(c[i] for c in co) for i in range(3)])
hi = Vector([max(c[i] for c in co) for i in range(3)])
size = max(hi - lo)
cz, cx, cy = (lo.z + hi.z) / 2, (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
dist = 2.6 * size + 1.0
# лицо — часть Head, иначе Body, иначе самая крупная часть кроме подставки (у кита №22 голова в части Whale)
face_part = ref_parts.get("Head") or ref_parts.get("Body") or max(
    (o for k, o in ref_parts.items() if k != "Stand"), key=lambda o: len(o.data.vertices))
fco = [face_part.matrix_world @ v.co for v in face_part.data.vertices]
face = Vector(((min(c.x for c in fco) + max(c.x for c in fco)) / 2, min(c.y for c in fco),
               (min(c.z for c in fco) + max(c.z for c in fco)) / 2))
GENERIC = [  # (имя, игра?, поворот, глаз, цель, объектив, кадр)
    ("hero", False, 0, (cx - 0.6 * dist, cy - 0.86 * dist, cz + 0.5 * size), (cx, cy, cz - 0.04 * size), 75,
     (1200, 1200)),
    ("front", False, 0, (0, -dist, cz + 0.12 * size), (0, 0, cz), 75, (1000, 1200)),
    ("front34", False, 0, (-0.71 * dist, -0.71 * dist, cz + 0.12 * size), (0, 0, cz), 75, (1000, 1200)),
    ("front34r", False, 0, (0.71 * dist, -0.71 * dist, cz + 0.12 * size), (0, 0, cz), 75, (1000, 1200)),
    ("side", False, -90, (0, -dist, cz + 0.12 * size), (0, 0, cz), 75, (1000, 1200)),
    ("back", False, 180, (0, -dist, cz + 0.12 * size), (0, 0, cz), 75, (1000, 1200)),
    ("top", False, 0, (cx, cy - 0.01, cz + 0.95 * dist), (cx, cy, cz), 75, (1200, 1200)),
    ("face", False, 0, tuple(face + Vector((-0.8, -3.0, 0.55))), tuple(face + Vector((-0.1, 0, 0.05))), 85, (1400, 1100)),
    ("face34", False, 0, tuple(face + Vector((-2.2, -2.2, 0.6))), tuple(face), 85, (1100, 1100)),
    ("face34r", False, 0, tuple(face + Vector((2.2, -2.2, 0.6))), tuple(face), 85, (1100, 1100)),
    ("game", True, 0, (0.2, -18.5, 9.0), (-0.6, -1.0, 2.0), 32, (844, 390)),
]
if FENNEC:
    head = ref_parts["Head"].matrix_world.translation.copy()
    body = ref_parts["Body"].matrix_world.translation.copy()
    cube = ref_parts["Cube"].matrix_world.translation + Vector((0, 0, 0.25))
    medal = Vector((0.0, -0.45, STAND_H + 1.37))

SHOTS = GENERIC if not FENNEC else [  # (имя, игра?, поворот, глаз, цель, объектив, кадр)
    ("hero", False, 0, (cx - 0.6 * dist, cy - 0.86 * dist, cz + 0.5 * size), (cx, cy, cz - 0.04 * size), 75,
     (1200, 1200)),
    ("front", False, 0, (0, -dist, cz + 0.12 * size), (0, 0, cz), 75, (1000, 1200)),
    ("back", False, 180, (0, -dist, cz + 0.12 * size), (0, 0, cz), 75, (1000, 1200)),
    ("muzzle", False, 0, (0, -6.2, 2.9), (0, -0.5, 2.3), 85, (1200, 1000)),
    ("face", False, 0, (head.x - 0.9, head.y - 3.6, head.z + 0.9), (head.x - 0.15, head.y - 0.5, head.z + 0.7), 85,
     (1400, 1100)),
    ("texture", False, 0, (body.x - 1.2, body.y - 2.2, body.z + 1.0), (body.x - 0.5, body.y - 0.4, body.z + 0.5), 105,
     (1400, 1100)),
    ("cube", False, 0, tuple(cube + Vector((-1.1, -2.4, 0.9))), tuple(cube), 85, (1000, 1000)),
    ("medal", False, 0, tuple(medal + Vector((-0.3, -2.6, -0.1))), tuple(medal), 85, (1000, 1000)),
    ("game", True, 0, (0.2, -18.5, 9.0), (-0.6, -1.0, 2.0), 32, (844, 390)),
]
for tag, (root, parts, _) in models.items():
    only(tag)
    for name, game, deg, eye, target, lens, res in SHOTS:
        set_game(game)
        root.rotation_euler = (0, 0, math.radians(deg))
        parts["Stand"].hide_render = game  # в игре подставку живого существа прячут
        root.location.z = -STAND_H if game else 0.0
        bpy.context.view_layer.update()
        prev.shot(os.path.join(OUT, f"{tag}_{name}.png"), eye, target, lens, res)
    root.rotation_euler = (0, 0, 0)
    root.location.z = 0.0
    parts["Stand"].hide_render = False

if not FENNEC:  # силуэты: чёрная эмиссия на белом фоне, без подставки, спереди (ортографически) и под 45°
    set_game(False)
    floor.hide_render = True
    black = bpy.data.materials.new("Silhouette")
    black.use_nodes = True
    nt = black.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (0, 0, 0, 1)
    nt.links.new(emit.outputs["Emission"], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
    white = bpy.data.worlds.new("White")
    white.use_nodes = True
    wbg = next(n for n in white.node_tree.nodes if n.type == "BACKGROUND")
    wbg.inputs["Color"].default_value, wbg.inputs["Strength"].default_value = (1, 1, 1, 1), 1.0
    scene.world = white
    for tag, (root, parts, _) in models.items():
        only(tag)
        parts["Stand"].hide_render = True
        for o in parts.values():
            o.data.materials.clear()
            o.data.materials.append(black)
        prev.cam_data.type = "ORTHO"
        prev.cam_data.ortho_scale = size * 1.15
        prev.shot(os.path.join(OUT, f"{tag}_sil_front.png"), (0, -30, cz), (0, 0, cz), 50, (1000, 1000))
        prev.cam_data.type = "PERSP"
        prev.shot(os.path.join(OUT, f"{tag}_sil_34.png"), (-0.71 * dist, -0.71 * dist, cz + 0.12 * size), (0, 0, cz),
                  75, (1000, 1000))

with open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(metrics, f, ensure_ascii=False, indent=1)
print("COMPARE_OK", [m[0] for m in MODELS])

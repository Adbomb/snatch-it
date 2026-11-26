"""Лист Б (D74): один этаж во всех 6 редкостях — Деревянный / Каменный / Мраморный / Золотой / Мифический / Космический.

Редкость — общие надстройки поверх базового этажа (карнизы, пилоны, балконы, портик, купол, золотая отделка, «корона»
Космического), а не новый этаж: тема и зал остаются от существа. Чем реже — тем выше, богаче и шире этаж; неона нет.
Базовый этаж — «Кактус-боксёр» (salun, floor_cactusboxer.py, без изменений), он же «Деревянный».
Только концепт на утверждение: в игру не экспортируется, файлы этажей не меняет.

Запуск: blender --background --factory-startup --python scripts/blender/floor_rarity_sheet.py -- <репо> <папка>
Кадры <папка>/tier_1…6.png (3/4 с одной точки — размеры сравнимы) и tower.png (стопка из шести этажей).
"""

import math
import os
import runpy
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import floorkit as K  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
OUT = os.path.abspath(argv[1])
# базовый этаж: сборка и сцена показа (свет, материалы, камера) без кадров
sys.argv = [sys.argv[0], "--", argv[0], OUT, "render", "shot=__none__"]
runpy.run_path(os.path.join(HERE, "floor_cactusboxer.py"), run_name="__main__")

scene = bpy.context.scene
for name in ("TowerAbove", "TowerBelow"):
    if name in bpy.data.objects:
        bpy.data.objects[name].hide_render = True

TIERS = ["Деревянный", "Каменный", "Мраморный", "Золотой", "Мифический", "Космический"]
PAL = {
    "stone": "8E9196",
    "stone_dark": "6E7176",
    "marble": "EEEBE4",
    "marble_shade": "D6D1C7",
    "gold": "E9B43A",
    "gold_dark": "B9821C",
    "copper": "5FAE98",
    "copper_dark": "3E8A76",
    "navy": "1E2A5C",
    "violet": "4C3D92",
    "star": "FFF4C8",
    "wood": "8A5A34",
}
_mats = {}


def mat(key):
    if key in _mats:
        return _mats[key]
    hexs = PAL[key]
    m = bpy.data.materials.new("R_" + key)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    rgb = [int(hexs[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    bsdf.inputs["Base Color"].default_value = (*[c**2.2 for c in rgb], 1)
    gold = key.startswith("gold")
    bsdf.inputs["Metallic"].default_value = 0.55 if gold else 0.0
    bsdf.inputs["Roughness"].default_value = 0.32 if gold else (0.35 if key.startswith("marble") else 0.7)
    _mats[key] = m
    return m


COLL = {}


def coll(tier):
    if tier not in COLL:
        c = bpy.data.collections.new("Tier%d" % tier)
        scene.collection.children.link(c)
        COLL[tier] = c
    return COLL[tier]


def _put(obj, tier, key):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    coll(tier).objects.link(obj)
    obj.data.materials.clear()
    obj.data.materials.append(mat(key))
    for poly in obj.data.polygons:
        poly.use_smooth = False
    return obj


def box(tier, key, x0, x1, y0, y1, z0, z1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=K.P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.active_object
    o.scale = (abs(x1 - x0), abs(z1 - z0), abs(y1 - y0))
    return _put(o, tier, key)


def cyl(tier, key, x, z, r, y0, y1, n=16, r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=y1 - y0, location=K.P(x, (y0 + y1) / 2, z))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=n, radius1=r, radius2=r2, depth=y1 - y0, location=K.P(x, (y0 + y1) / 2, z))
    return _put(bpy.context.active_object, tier, key)


def dome(tier, key, x, z, r, y0, squash=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, radius=r, location=K.P(x, y0, z))
    o = bpy.context.active_object
    o.scale = (1, 1, squash)
    return _put(o, tier, key)


def ring(tier, key, x, y, z, big, small, tilt=0.0, flat=1.0):
    bpy.ops.mesh.primitive_torus_add(major_radius=big, minor_radius=small, major_segments=40, minor_segments=8,
                                     location=K.P(x, y, z))
    o = bpy.context.active_object
    o.scale = (1, 1, flat)
    o.rotation_euler = (math.radians(tilt), 0, 0)
    return _put(o, tier, key)


# ── общие надстройки ───────────────────────────────────────────────────────────────────────────────────────────
X, Z, ROOF = 18.12, 17.12, 19.0  # наружные стены и верх стены базового этажа


def cornice(tier, key, y, h, out):
    """Карниз-обвязка по периметру на высоте y."""
    box(tier, key, -X - out, X + out, y, y + h, -Z - out, -Z + 0.6)
    box(tier, key, -X - out, X + out, y, y + h, Z - 0.6, Z + out)
    box(tier, key, -X - out, -X + 0.6, y, y + h, -Z, Z)
    box(tier, key, X - 0.6, X + out, y, y + h, -Z, Z)


def pylons(tier, key, w, y0, y1, cap=None):
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * (X - w / 2 + 0.6), sz * (Z - w / 2 + 0.6)
            box(tier, key, cx - w / 2, cx + w / 2, y0, y1, cz - w / 2, cz + w / 2)
            if cap:
                box(tier, cap, cx - w / 2 - 0.4, cx + w / 2 + 0.4, y1, y1 + 0.8, cz - w / 2 - 0.4, cz + w / 2 + 0.4)


def plinth(tier, key, h, out):
    box(tier, key, -X - out, X + out, -1.0, h, -Z - out, Z + out)


def balustrade(tier, key, rail, x0, x1, z, y, n):
    """Балюстрада вдоль x на линии z: столбики и перила."""
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        box(tier, key, x - 0.25, x + 0.25, y, y + 1.6, z - 0.25, z + 0.25)
    box(tier, rail, x0 - 0.3, x1 + 0.3, y + 1.6, y + 2.0, z - 0.4, z + 0.4)


def portico(tier, col, top, n=6, y1=17.0, depth=7.0, pediment=True):
    """Портик спереди: колонны, архитрав и фронтон."""
    z = -Z - depth
    for k in range(n):
        x = -X + 2.2 + (2 * X - 4.4) * k / (n - 1)
        cyl(tier, col, x, z, 0.85, 0.6, y1, n=12)
        box(tier, col, x - 1.1, x + 1.1, 0.0, 0.6, z - 1.1, z + 1.1)
        box(tier, col, x - 1.1, x + 1.1, y1, y1 + 0.5, z - 1.1, z + 1.1)
    box(tier, top, -X - 0.6, X + 0.6, y1 + 0.5, y1 + 2.2, z - 1.3, -Z)
    box(tier, col, -X - 0.6, X + 0.6, -0.6, 0.0, z - 1.6, -Z)  # ступень
    if pediment:
        h = 5.0
        for k in range(6):  # ступенчатый фронтон (D39 — ступени, не наклон)
            w = (X + 0.6) * (1 - k / 6)
            box(tier, top if k % 2 == 0 else col, -w, w, y1 + 2.2 + k * h / 6, y1 + 2.2 + (k + 1) * h / 6, z - 1.3,
                z + 0.4)


def attic(tier, key, y0, h, inset=1.5):
    box(tier, key, -X + inset, X - inset, y0, y0 + h, -Z + inset, Z - inset)


# 1 Деревянный — базовый этаж как есть (только подпись листа)

# 2 Каменный: нижний ярус обшит камнем, угловые башни-пилоны с зубцами, каменный карниз и зубчатый парапет —
# этаж «тяжелее» и выше
T = 2
plinth(T, "stone_dark", 1.2, 0.7)
for (x0, x1, z0, z1) in ((-X - 0.5, X + 0.5, -Z - 0.5, -Z), (-X - 0.5, X + 0.5, Z, Z + 0.5), (-X - 0.5, -X, -Z, Z),
                         (X, X + 0.5, -Z, Z)):
    box(T, "stone", x0, x1, 1.2, 4.2, z0, z1)
box(T, "stone_dark", -X - 0.8, X + 0.8, 4.2, 4.8, -Z - 0.8, -Z)
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx * X, sz * Z
        box(T, "stone", cx - 2.0, cx + 2.0, 0.0, ROOF + 5.0, cz - 2.0, cz + 2.0)
        box(T, "stone_dark", cx - 2.5, cx + 2.5, ROOF + 5.0, ROOF + 5.8, cz - 2.5, cz + 2.5)
        for dx in (-1.8, 0, 1.8):
            for dz in (-1.8, 1.8):
                box(T, "stone", cx + dx - 0.5, cx + dx + 0.5, ROOF + 5.8, ROOF + 7.0, cz + dz - 0.5, cz + dz + 0.5)
cornice(T, "stone", ROOF, 1.2, 1.0)
for k in range(9):
    x = -X + 3.5 + k * (2 * X - 7) / 8
    for z in (-Z - 0.6, Z + 0.6):
        box(T, "stone_dark", x - 0.9, x + 0.9, ROOF + 1.2, ROOF + 3.2, z - 0.6, z + 0.6)

# 3 Мраморный: мраморный портик с колоннами и фронтоном, мраморный аттик, балюстрада на крыше — выше и наряднее
T = 3
plinth(T, "marble_shade", 0.9, 0.9)
portico(T, "marble", "marble_shade")
cornice(T, "marble", ROOF, 1.0, 1.0)
attic(T, "marble", ROOF + 1.0, 6.0)
cornice(T, "marble_shade", ROOF + 6.4, 0.6, -1.0)
for z in (-Z + 2.0, Z - 2.0):
    balustrade(T, "marble", "marble_shade", -X + 2.5, X - 2.5, z, ROOF + 7.0, 14)

# 4 Золотой: мрамор + золото: портик с золотым фронтоном, золотые карнизы, барабан и золотой купол со шпилем,
# балконы с золотыми перилами по бокам
T = 4
plinth(T, "marble_shade", 0.9, 0.9)
portico(T, "marble", "gold")
cornice(T, "gold", ROOF, 1.0, 1.2)
attic(T, "marble", ROOF + 1.0, 3.0)
cyl(T, "marble", 0, 0, 8.0, ROOF + 4.0, ROOF + 8.0, n=24)
cornice(T, "gold_dark", ROOF + 3.6, 0.5, 0.4)
dome(T, "gold", 0, 0, 7.6, ROOF + 8.0, squash=0.9)
cyl(T, "gold_dark", 0, 0, 0.6, ROOF + 14.5, ROOF + 18.0, n=8, r2=0.05)
for sx in (-1, 1):
    x = sx * (X + 2.5)
    box(T, "marble_shade", min(x, sx * X), max(x, sx * X), 9.0, 9.8, -9.0, 9.0)
    for k in range(7):
        zz = -8.5 + k * 17 / 6
        box(T, "gold", x - 0.25, x + 0.25, 9.8, 11.4, zz - 0.25, zz + 0.25)
    box(T, "gold", x - 0.4, x + 0.4, 11.4, 11.8, -9.0, 9.0)

# 5 Мифический: вдвое выше — второй ярус-аттик, четыре угловые башни с медными шатрами, большой купол, террасы за
# контур башни; мрамор, медь, золото
T = 5
plinth(T, "marble_shade", 0.9, 1.2)
portico(T, "marble", "gold")
cornice(T, "gold", ROOF, 1.0, 1.4)
attic(T, "marble", ROOF + 1.0, 6.0, inset=2.5)
cornice(T, "gold_dark", ROOF + 6.6, 0.6, -1.6)
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx * (X - 1.2), sz * (Z - 1.2)
        cyl(T, "marble", cx, cz, 3.0, 0.0, ROOF + 13.0, n=16)
        cyl(T, "gold", cx, cz, 3.5, ROOF + 13.0, ROOF + 13.8, n=16)
        cyl(T, "copper", cx, cz, 3.4, ROOF + 13.8, ROOF + 21.0, n=16, r2=0.2)
cyl(T, "marble", 0, 0, 9.0, ROOF + 7.0, ROOF + 11.0, n=24)
dome(T, "copper", 0, 0, 8.6, ROOF + 11.0, squash=1.05)
cyl(T, "gold", 0, 0, 1.4, ROOF + 19.5, ROOF + 21.5, n=12)
cyl(T, "gold_dark", 0, 0, 0.7, ROOF + 21.5, ROOF + 26.0, n=8, r2=0.05)
for sx in (-1, 1):  # террасы за контур
    x0, x1 = sorted((sx * X, sx * (X + 6.0)))
    box(T, "marble_shade", x0, x1, 11.0, 12.0, -12.0, 12.0)
    for k in range(4):
        zz = -10 + k * 20 / 3
        box(T, "marble", x0 + 0.4 if sx > 0 else x1 - 1.6, x0 + 1.6 if sx > 0 else x1 - 0.4, 6.0, 11.0, zz - 0.6,
            zz + 0.6)
    edge = x1 - 0.4 if sx > 0 else x0 + 0.4
    for k in range(9):
        zz = -11.5 + k * 23 / 8
        box(T, "gold", edge - 0.25, edge + 0.25, 12.0, 13.6, zz - 0.25, zz + 0.25)
    box(T, "gold", edge - 0.4, edge + 0.4, 13.6, 14.0, -12.0, 12.0)

# 6 Космический: втрое выше и шире контура — тёмно-синий с фиолетовым и золотом: кольцо-платформа вокруг этажа
# (как у планеты), трёхъярусная корона из золотых зубцов, планета-шар с наклонным золотым кольцом на вершине,
# звёзды — светлые кубики на тёмных панелях (без неона, не светятся)
T = 6
plinth(T, "navy", 1.0, 1.4)
portico(T, "violet", "gold", y1=17.0)
cornice(T, "gold", ROOF, 1.2, 1.6)
ring(T, "gold", 0, ROOF + 3.0, 0, 28.0, 1.1, flat=0.6)  # кольцо планеты вокруг основания короны, за контуром
for sx in (-1, 1):  # растяжки кольца к углам
    for sz in (-1, 1):
        a = math.atan2(sz * Z, sx * X)
        x0, z0 = sx * (X - 1.0), sz * (Z - 1.0)
        x1, z1 = math.cos(a) * 27.2, math.sin(a) * 27.2
        for k in range(5):
            f = (k + 0.5) / 5
            x, z = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f
            box(T, "violet", x - 0.6, x + 0.6, ROOF + 2.6, ROOF + 3.4, z - 0.6, z + 0.6)
for k, (h, inset) in enumerate(((7.0, 2.0), (7.0, 5.0), (6.0, 8.0))):  # три яруса короны
    y0 = ROOF + 1.2 + k * 7.0
    box(T, "navy", -X + inset, X - inset, y0, y0 + h, -Z + inset, Z - inset)
    cornice_y = y0 + h - 0.6
    w = X - inset + 0.8
    d = Z - inset + 0.8
    box(T, "gold", -w, w, cornice_y, cornice_y + 0.8, -d, d)
    n = 10 - 2 * k
    for j in range(n):  # зубцы короны
        x = -w + 1.2 + (2 * w - 2.4) * j / (n - 1)
        for z in (-d + 0.6, d - 0.6):
            cyl(T, "gold", x, z, 0.9, cornice_y + 0.8, cornice_y + 4.2 - k * 0.6, n=8, r2=0.05)
    for j in range(14):  # звёзды на тёмных панелях
        a = (j * 2.399) % 1
        x = -X + inset + 0.8 + a * (2 * (X - inset) - 1.6)
        yy = y0 + 1.0 + ((j * 0.618) % 1) * (h - 2.5)
        box(T, "star", x - 0.25, x + 0.25, yy - 0.25, yy + 0.25, -Z + inset - 0.3, -Z + inset + 0.1)
top = ROOF + 1.2 + 21.0
cyl(T, "gold", 0, 0, 3.4, top, top + 2.0, n=16)
dome(T, "violet", 0, 0, 5.2, top + 6.4)
ring(T, "gold", 0, top + 6.4, 0, 8.4, 0.5, tilt=22, flat=1.0)
cyl(T, "gold_dark", 0, 0, 0.5, top + 11.4, top + 16.0, n=8, r2=0.05)
for sx in (-1, 1):  # боковые башенки за контур
    cx = sx * (X + 4.5)
    cyl(T, "navy", cx, 0, 2.6, 0.0, ROOF + 16.0, n=12)
    cyl(T, "gold", cx, 0, 3.0, ROOF + 16.0, ROOF + 16.8, n=12)
    cyl(T, "violet", cx, 0, 2.8, ROOF + 16.8, ROOF + 24.0, n=12, r2=0.15)

# ── кадры ──────────────────────────────────────────────────────────────────────────────────────────────────────
cam = scene.camera
cam.data.angle_y = math.radians(34)
eye, target = K.P(-90, 38, -100), K.P(0, 19, -3)
cam.location = eye
cam.rotation_euler = (eye - target).to_track_quat("Z", "Y").to_euler()
scene.render.resolution_x, scene.render.resolution_y = 1000, 1150
hide_prefix = ("CB_S_", "Item", "Hall")
for o in bpy.data.objects:
    if any(o.name.startswith(h) for h in hide_prefix):
        o.hide_render = True
for t in range(1, 7):
    for k, c in COLL.items():
        c.hide_render = k != t
    scene.render.filepath = os.path.join(OUT, "tier_%d.png" % t)
    bpy.ops.render.render(write_still=True)
    print("SHOT tier", t, flush=True)
print("DONE_SHEET", flush=True)

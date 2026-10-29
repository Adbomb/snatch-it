"""Гантели (D30, D33, референс заказчика — большая неоновая гантель у таблички «Улучшение») →
assets/models/Pack1_dumbbells.fbx.

Пропорции: диски огромные (диаметр ≈ 2.8 толщины грифа), гриф короткий и толстый, рукоять рифлёная.
Диски — «пиксельные» круги из кубиков с фаской, швы между кубиками видны (Model.voxel_plate); LEGO-рисунок
даёт материал игры. Каждый уровень отличается силуэтом, а не только цветом.
Центр рукояти — в начале координат, ось x; бюджет ≤ 3 000 треугольников на гантель.

Запуск из корня репозитория:
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup \\
    --python scripts/blender/pack1_dumbbells.py -- . <папка превью> [номера через запятую]
С полным набором (1–10) пишет assets/models/Pack1_dumbbells.fbx и .layout.json; с частью — только превью.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lego  # noqa: E402
from lego import Model, align, noise, pixel_circle, rot  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
INDICES = [int(x) for x in argv[2].split(",")] if len(argv) > 2 else list(range(1, 11))
os.makedirs(PREVIEWS, exist_ok=True)

BUDGET = 3000
CELL = 1.45  # кубик диска; диск 7 кубиков ≈ 10.2 стада
BAR = 3.6  # толщина грифа (квадратное сечение)
GRIP = 4.4  # полудлина рукояти между дисками
DISC_D = 3.0  # толщина диска
DISC_X = GRIP + DISC_D / 2  # центр диска
END_X = DISC_X + DISC_D / 2 + 0.8  # торец грифа за диском


def one(role, color):
    return lambda i, j: (role, color)


def bar(m, color, end_color=None):
    """Квадратный толстый гриф насквозь через диски; торцы выступают за диски."""
    m.box("Body", (0, 0, 0), (2 * END_X, BAR, BAR), color, bevel=0.3)
    if end_color:
        for s in (-1, 1):
            m.box("Body", (s * (END_X + 0.3), 0, 0), (0.6, BAR - 0.8, BAR - 0.8), end_color, bevel=0.15)


def ridges(m, role, color, count=3, width=0.7):
    """Рифление рукояти: выпуклые полосы."""
    step = 2 * GRIP / (count + 1)
    for k in range(count):
        m.box(role, (-GRIP + step * (k + 1), 0, 0), (width, BAR + 0.4, BAR + 0.4), color, bevel=0.14)


def discs(m, cells, paint, back_groove=False, lift=None, x=DISC_X, depth=DISC_D, cell=CELL):
    for s in (-1, 1):
        m.voxel_plate((s * x, 0, 0), cells, cell, depth, paint, normal=(s, 0, 0), back_groove=back_groove,
                      lift=lift)


# ================================================================ уровни
def wooden(m):
    """1 Деревянная: по одному простому диску из грубых досок, рукоять обмотана верёвкой."""
    bar(m, "darkwood", end_color="wood")
    for k in range(7):  # витки верёвки спиралью
        m.box("Body", (-3.0 + k * 1.0, 0, 0), (0.5, BAR + 0.36, BAR + 0.36), "rope", rotation=rot(z=12), bevel=0.12)

    def paint(i, j):
        if noise(i, j, 1) < 0.12:
            return ("Body", "darkwood")  # сучки и потемневшие доски
        return ("Body", "wood" if j % 2 else "lightwood")  # доски рядами

    discs(m, pixel_circle(7), paint, lift=lambda i, j: (noise(i, j, 2) - 0.5) * 0.3)


def silver(m):
    """5 Серебряная: диски с прорезями-окнами, ступица темнее, стальные шайбы у рукояти."""
    bar(m, "steel", end_color="silver")
    ridges(m, "Body", "silver")
    windows = ((2, 0), (-2, 0), (0, 2), (0, -2))
    for s in (-1, 1):
        m.box("Body", (s * (GRIP - 0.4), 0, 0), (0.8, BAR + 1.2, BAR + 1.2), "silver", bevel=0.2)

    def paint(i, j):
        return ("Body", "iron" if abs(i) <= 1 and abs(j) <= 1 else "silver")

    discs(m, pixel_circle(7, windows), paint, back_groove=True)


def gem(m, surface, normal, size=0.9, color="neongreen"):
    """Квадратный неоновый камень-пирамидка, вставленный в кубик: основание на поверхности, остриё наружу."""
    h = size * 0.5
    center = tuple(surface[k] + normal[k] * (h / 2 - 0.05) for k in range(3))
    m.cylinder("Glow", center, size * 0.71, h, color, segments=4, radius2=size * 0.33, rotation=align(normal, 45),
               bevel=0)


def crystal(m, base, direction, length, radius):
    """Кристалл-осколок: стеклянный изумрудный конус с неоновой сердцевиной."""
    d = Vector(direction).normalized()
    m.cylinder("Glass", tuple(Vector(base) + d * (length / 2)), radius, length, "emerald", segments=4, radius2=0,
               rotation=align(d), bevel=0)
    m.cylinder("Glow", tuple(Vector(base) + d * (length * 0.4)), radius * 0.55, length * 0.8, "neongreen",
               segments=3, radius2=0, rotation=align(d), bevel=0)


def neon(m):
    """9 Неоновая (референс заказчика): тело угольно-чёрное из кубиков, золотые канты; неоновые только детали —
    квадратные камни в кубиках дисков и грифа и кристаллы веером из-за дисков. Свет неона на кубиках даёт
    PointLight в игре — места ламп в layout («lights»)."""
    c = CELL
    # Гриф: чёрный брус, золотые рёбра, ряд камней спереди и сзади, золотые шайбы у дисков.
    m.box("Body", (0, 0, 0), (2 * END_X, BAR, BAR), "black", bevel=0.25)
    for sy in (-1, 1):
        for sz in (-1, 1):
            m.box("Body", (0, sy * (BAR / 2 - 0.12), sz * (BAR / 2 - 0.12)), (2 * GRIP - 0.6, 0.55, 0.55), "brass",
                  bevel=0)
    for k in range(4):
        x = -GRIP + 2 * GRIP * (k + 0.5) / 4
        for sz in (-1, 1):
            gem(m, (x, 0, sz * BAR / 2), (0, 0, sz), size=1.0)
    for s in (-1, 1):
        m.box("Body", (s * (GRIP - 0.35), 0, 0), (0.7, BAR + 0.9, BAR + 0.9), "brass", bevel=0.15)

    def paint(i, j):
        return ("Body", "charcoal" if noise(i, j, 7) < 0.35 else "black")

    def lift(i, j):
        return (noise(i, j, 8) - 0.5) * 0.3

    face = DISC_X + DISC_D / 2
    block = [(i, j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
    for s in (-1, 1):
        # Большой диск: рельеф из кубиков смотрит к грифу (как на референсе), снаружи гладко под ступицей.
        # Золотой пояс по ступенчатому краю, внешняя чёрная ступица на золотой подложке, торец.
        m.voxel_plate((s * DISC_X, 0, 0), pixel_circle(7), c, DISC_D, paint, normal=(-s, 0, 0), back_groove=False,
                      lift=lift)
        m.voxel_plate((s * (DISC_X - 0.35), 0, 0), pixel_circle(7) - pixel_circle(5), c * 1.05, 0.5,
                      one("Body", "brass"), normal=(s, 0, 0), groove=0)
        m.voxel_plate((s * (face + 0.22), 0, 0), set(block), c * 1.2, 0.4, one("Body", "brass"), normal=(s, 0, 0),
                      groove=0)
        m.voxel_plate((s * (face + 1.22), 0, 0), set(block), c, 1.6, paint, normal=(s, 0, 0), back_groove=False)
        cap = face + 2.02 + 0.4
        m.box("Body", (s * cap, 0, 0), (0.8, 2.2, 2.2), "black", bevel=0.15)
        gem(m, (s * (cap + 0.4), 0, 0), (s, 0, 0), size=1.1)
        # Камни в кубиках внутренней стороны диска (вокруг шайбы), снаружи — по углам ступицы, по краю.
        inner = DISC_X - DISC_D / 2
        for i, j in ((2, 2), (-2, 2), (2, -2), (-2, -2), (3, 0), (-3, 0), (0, 3), (0, -3)):
            gem(m, (s * (inner - lift(i, j)), j * c, s * i * c), (-s, 0, 0))
        for i, j in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
            gem(m, (s * face, j * c, i * c), (s, 0, 0))
        for ny, nz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            gem(m, (s * (DISC_X + 0.6), ny * 3.5 * c, nz * 3.5 * c), (0, ny, nz))
        # Кристаллы веером из-за диска, наклонены наружу.
        for k in range(6):
            a = math.radians(k * 60 + 30)
            tilt = math.radians(32)
            d = (s * math.sin(tilt), math.cos(tilt) * math.cos(a), math.cos(tilt) * math.sin(a))
            base = (s * (DISC_X - DISC_D / 2 + 0.6), 3.2 * math.cos(a), 3.2 * math.sin(a))
            crystal(m, base, d, 5.6 if k % 2 else 4.4, 1.7 if k % 2 else 1.35)
    green = "39FF6A"
    lights = [(s * DISC_X, 1.0, sz * 6.5) for s in (-1, 1) for sz in (-1, 1)]  # перед дисками и за ними
    return {"lights": [{"position": list(p), "color": green, "range": 14, "brightness": 2} for p in lights]}


BUILDERS = {1: ("Деревянная", wooden), 5: ("Серебряная", silver), 9: ("Неоновая", neon)}


# ================================================================ сборка
bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.context.scene.collection
layout = {}
objects = []
LIFT = 5.8  # в превью гантель висит над полем, как на референсе
SPACING = 20
for k, index in enumerate(INDICES):
    title, builder = BUILDERS[index]
    m = Model(f"Dumbbell{index:02d}")
    extras = builder(m) or {}
    roles = m.build(collection, (k * SPACING, LIFT, 0))
    total = sum(r["triangles"] for r in roles.values())
    layout[m.name] = {"title": title, "roles": roles, "triangles": total, **extras}
    print(f"DUMBBELL {m.name} parts={len(roles)} triangles={total} budget={BUDGET}")
    objects += [o for o in collection.objects if o.name.startswith(m.name + "_")]

if sorted(INDICES) == list(range(1, 11)):
    models_dir = os.path.join(REPO, "assets", "models")
    lego.export_fbx(os.path.join(models_dir, "Pack1_dumbbells.fbx"), objects)
    lego.write_json(os.path.join(models_dir, "Pack1_dumbbells.layout.json"), layout)

# Превью на фоне поля из LEGO-плиток, как на референсе.
ground = Model("Ground")
ground.box("Body", (0, -0.5, 0), (600, 1, 600), "grass", bevel=0)
ground.build(collection)
ground_obj = [o for o in collection.objects if o.name.startswith("Ground_")]
lego.preview_materials(objects + ground_obj, os.path.join(REPO, "assets", "textures", "lego_studs_color.png"))
lego.setup_render(1000)
scene = bpy.context.scene
# Лампы неона (в игре — PointLight без теней): зелёный свет ложится на кубики.
for k, index in enumerate(INDICES):
    for light in layout[f"Dumbbell{index:02d}"].get("lights", []):
        x, y, z = light["position"]
        data = bpy.data.lights.new("NeonLight", "POINT")
        data.color = lego.hex_to_rgb(light["color"])
        data.energy = 35 * light["brightness"] * light["range"]
        data.use_shadow = False
        obj = bpy.data.objects.new("NeonLight", data)
        obj.location = lego.to_blender((x + k * SPACING, y + LIFT, z))
        collection.objects.link(obj)
for k, index in enumerate(INDICES):
    name = f"Dumbbell{index:02d}"
    vis = [o for o in objects if o.name.startswith(name + "_")] + ground_obj
    ox = k * SPACING
    lego.render(os.path.join(PREVIEWS, f"{name}.png"), (ox - 2, LIFT + 3.5, 17), (ox, LIFT - 0.3, 0), vis, lens=22)
mid = (len(INDICES) - 1) * SPACING / 2
scene.render.resolution_x, scene.render.resolution_y = 1500, 700
lego.render(os.path.join(PREVIEWS, "Dumbbells_row.png"), (mid - 20, LIFT + 17, 66), (mid, LIFT - 1.5, 0),
            objects + ground_obj, lens=40)
print("DUMBBELLS_OK")

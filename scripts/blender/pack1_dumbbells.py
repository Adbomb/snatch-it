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

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lego  # noqa: E402
from lego import Model, noise, pixel_circle, rot  # noqa: E402

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


def neon(m):
    """9 Неоновая: тёмное тело в два тона, неоновые кольца по контуру дисков, светящиеся «камни» (как на референсе)."""
    bar(m, "neonbody", end_color="neonbody2")
    ridges(m, "Glow", "neongreen", width=0.6)

    def paint(i, j):
        return ("Body", "neonbody2" if noise(i, j, 5) < 0.4 else "neonbody")  # два тёмных тона: кубики видны

    discs(m, pixel_circle(7), paint)
    ring = pixel_circle(7) - pixel_circle(5)
    rim = 0.35
    for s in (-1, 1):
        # Неоновый контур: тонкие светящиеся кольца у переднего и заднего края, чуть шире диска —
        # снаружи видна только яркая линия по ступенчатому краю, тело остаётся тёмным.
        for edge in (DISC_X + DISC_D / 2 - 0.2 - rim / 2, DISC_X - DISC_D / 2 + 0.2 + rim / 2):
            m.voxel_plate((s * edge, 0, 0), ring, CELL * 1.07, rim, one("Glow", "neongreen"), normal=(s, 0, 0),
                          groove=0)
        face = s * (DISC_X + DISC_D / 2)
        for u, v in ((-1.5, 1.5), (1.5, -1.5), (1.5, 1.5), (-1.5, -1.5)):  # камни на лице диска, на стыках кубиков
            m.box("Glow", (face + s * 0.45, v * CELL, u * CELL), (1.2, 1.25, 1.25), "neonlime",
                  rotation=rot(x=45), bevel=0.2)
        for u, tilt in ((-0.6, -18), (0.8, 14)):  # камни торчат из верхнего края
            m.box("Glow", (s * DISC_X, 3.5 * CELL + 0.35, u * CELL), (1.2, 1.4, 1.2), "neonlime",
                  rotation=rot(x=tilt, z=8 * s), bevel=0.2)


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
    builder(m)
    roles = m.build(collection, (k * SPACING, LIFT, 0))
    total = sum(r["triangles"] for r in roles.values())
    layout[m.name] = {"title": title, "roles": roles, "triangles": total}
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
for k, index in enumerate(INDICES):
    name = f"Dumbbell{index:02d}"
    vis = [o for o in objects if o.name.startswith(name + "_")] + ground_obj
    ox = k * SPACING
    lego.render(os.path.join(PREVIEWS, f"{name}.png"), (ox - 30, LIFT + 11, 21), (ox, LIFT - 1.2, 0), vis, lens=40)
mid = (len(INDICES) - 1) * SPACING / 2
scene.render.resolution_x, scene.render.resolution_y = 1500, 700
lego.render(os.path.join(PREVIEWS, "Dumbbells_row.png"), (mid - 20, LIFT + 17, 66), (mid, LIFT - 1.5, 0),
            objects + ground_obj, lens=40)
print("DUMBBELLS_OK")

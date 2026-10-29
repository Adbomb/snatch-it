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


def bar(m, color, end_color=None, end=END_X):
    """Квадратный толстый гриф насквозь через диски; торцы (end) выступают за диски."""
    m.box("Body", (0, 0, 0), (2 * end, BAR, BAR), color, bevel=0.3)
    if end_color:
        for s in (-1, 1):
            m.box("Body", (s * (end + 0.3), 0, 0), (0.6, BAR - 0.8, BAR - 0.8), end_color, bevel=0.15)


def ridges(m, role, color, count=3, width=0.7, bevel=0.14, half=GRIP):
    """Рифление рукояти: выпуклые полосы (half — полудлина рукояти)."""
    step = 2 * half / (count + 1)
    for k in range(count):
        m.box(role, (-half + step * (k + 1), 0, 0), (width, BAR + 0.4, BAR + 0.4), color, bevel=bevel)


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


def gem(m, surface, normal, size=0.9, color="neongreen", role="Glow"):
    """Квадратный неоновый камень-пирамидка, вставленный в кубик: основание на поверхности, остриё наружу."""
    h = size * 0.5
    center = tuple(surface[k] + normal[k] * (h / 2 - 0.05) for k in range(3))
    m.cylinder(role, center, size * 0.71, h, color, segments=4, radius2=size * 0.33, rotation=align(normal, 45),
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


def basis(direction):
    """Ось direction и два перпендикуляра к ней."""
    d = Vector(direction).normalized()
    ref = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
    e1 = d.cross(ref).normalized()
    return d, e1, d.cross(e1)


def lights(color, points, brightness=2, light_range=14):
    """Места ламп (в игре — PointLight без теней): свет неона и кристаллов ложится на кубики."""
    code = lego.PALETTE.get(color, color)
    return {"lights": [{"position": list(p), "color": code, "range": light_range, "brightness": brightness}
                       for p in points]}


def disc_lights(color, x=DISC_X):
    return lights(color, [(s * x, 1.0, sz * 6.5) for s in (-1, 1) for sz in (-1, 1)])


def prism(m, role, polygon, x0, x1, color, bevel=0.18):
    """Призма с фаской: многоугольник в плоскости y–z (точки (y, z)) от x0 до x1."""
    m.hull(role, [(x, y, z) for x in (x0, x1) for y, z in polygon], color, bevel)


def bolt(m, center, normal, color="black"):
    """Болт: шестигранная головка."""
    m.cylinder("Body", center, 0.42, 0.4, color, segments=6, rotation=align(normal), bevel=0)


def crystal_prism(m, base, direction, length, radius, color="emerald"):
    """Кристалл: шестигранный столбик с острой верхушкой, одна стеклянная оболочка (без внутренних граней)."""
    d, e1, e2 = basis(direction)
    b = Vector(base)
    ring = [(e1 * math.cos(math.radians(60 * k)) + e2 * math.sin(math.radians(60 * k))) * radius for k in range(6)]
    points = [b + r for r in ring] + [b + d * length * 0.68 + r for r in ring] + [b + d * length]
    m.hull("Glass", [tuple(p) for p in points], color)


def stone(m):
    """2 Каменная: диски из грубых глыб — неровные, со сколами: выбитые кубики по краю, торчащие обломки."""
    bar(m, "darkrock")
    for x, tilt in ((-1.7, -9), (1.7, 11)):  # каменная перевязь — рифление рукояти
        m.box("Body", (x, 0, 0), (1.1, BAR + 0.5, BAR + 0.5), "rock", rotation=rot(z=tilt), bevel=0.2)

    def paint(i, j):
        n = noise(i, j, 11)
        return ("Body", "darkrock" if n < 0.3 else "stone" if n > 0.82 else "rock")

    def lift(i, j):
        return (noise(i, j, 12) - 0.25) * 0.5  # грубая поверхность: глыбы разной высоты

    chips = {1: ((3, 1), (-1, -3), (2, 2)), -1: ((-3, -1), (1, 3), (-2, -2), (3, 0))}
    for s in (-1, 1):
        m.voxel_plate((s * DISC_X, 0, 0), pixel_circle(7, chips[s]), CELL, DISC_D, paint, normal=(s, 0, 0),
                      back_groove=True, lift=lift)
        for k, a in enumerate((35, 150, 255)):  # обломки торчат из края
            r = math.radians(a + 20 * s)
            m.box("Body", (s * (DISC_X + 0.3 * k - 0.3), 4.7 * math.cos(r), 4.7 * math.sin(r)), (1.6, 1.5, 1.7),
                  "darkrock" if k % 2 else "rock", rotation=rot(x=a + 17, y=14 * s, z=22), bevel=0.22)
        m.box("Body", (s * (END_X + 0.35), 0, 0), (0.7, 2.6, 2.4), "rock", rotation=rot(x=8 * s), bevel=0.2)


def iron(m):
    """3 Железная: по два диска разного размера (большой и малый), болты на торцах, рифлёная рукоять."""
    c = CELL
    big, small = 2.2, 1.6
    xb, xs, face = GRIP + big / 2, GRIP + big + small / 2, GRIP + big + small
    bar(m, "steel", end=face + 0.7)
    ridges(m, "Body", "iron")

    def paint(i, j):
        return ("Body", "steel" if noise(i, j, 21) < 0.2 else "iron")

    for s in (-1, 1):
        m.voxel_plate((s * xb, 0, 0), pixel_circle(7), c, big, paint, normal=(s, 0, 0))
        m.voxel_plate((s * xs, 0, 0), pixel_circle(5), c, small, one("Body", "steel"), normal=(s, 0, 0))
        for i, j in ((1, 1), (-1, 1), (1, -1), (-1, -1)):  # болты на малом диске
            bolt(m, (s * (face + 0.15), j * c, i * c), (s, 0, 0))
        for i, j in ((3, 0), (-3, 0), (0, 3), (0, -3)):  # и на открытом кольце большого
            bolt(m, (s * (GRIP + big + 0.15), j * c, i * c), (s, 0, 0))
        m.box("Body", (s * (face + 1.0), 0, 0), (0.6, 2.4, 2.4), "black", bevel=0.15)
        bolt(m, (s * (face + 1.45), 0, 0), (s, 0, 0), "steel")


def bronze(m):
    """4 Бронзовая: три диска лесенкой (большой → средний → малый) и кольцо-замок с защёлкой на конце грифа."""
    d1, d2, d3 = 2.0, 1.5, 1.3
    x1, x2, x3 = GRIP + d1 / 2, GRIP + d1 + d2 / 2, GRIP + d1 + d2 + d3 / 2
    lock = GRIP + d1 + d2 + d3 + 0.6
    bar(m, "darkbronze", end=lock + 0.9)
    ridges(m, "Body", "bronze", count=2, bevel=0)

    def paint(i, j):
        return ("Body", "darkbronze" if noise(i, j, 31) < 0.18 else "bronze")

    block = {(i, j) for i in (-1, 0, 1) for j in (-1, 0, 1)}
    for s in (-1, 1):
        m.voxel_plate((s * x1, 0, 0), pixel_circle(7), CELL, d1, paint, normal=(s, 0, 0))
        m.voxel_plate((s * x2, 0, 0), pixel_circle(5), CELL, d2, paint, normal=(s, 0, 0))
        m.voxel_plate((s * x3, 0, 0), block, CELL, d3, paint, normal=(s, 0, 0))
        # Кольцо-замок: восьмигранная обойма на грифе и защёлка сверху.
        m.cylinder("Body", (s * lock, 0, 0), BAR * 0.78, 1.0, "darkbronze", axis="x", segments=8, bevel=0.1)
        m.box("Body", (s * lock, BAR * 0.78 + 0.3, 0), (0.7, 0.9, 1.4), "bronze", bevel=0.15)


def golden(m):
    """6 Золотая: шестигранные диски из блоков-сегментов (швы видны), приподнятый кант тёмного золота, рубины."""
    bar(m, "gold", end_color="darkgold")
    ridges(m, "Body", "darkgold")
    r_hub, r_mid, r_out = 2.6, 3.9, 5.5

    def at(r, a):
        return (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))

    face = GRIP + DISC_D
    for s in (-1, 1):
        prism(m, "Body", [at(r_hub, 60 * k + 30) for k in range(6)], s * GRIP, s * (face + 0.3), "darkgold")
        prism(m, "Body", [at(r_out + 0.25, 60 * k + 30) for k in range(6)], s * GRIP, s * (GRIP + 0.5), "darkgold")
        for k in range(6):
            a0, a1 = 60 * k + 31.2, 60 * k + 88.8  # узкий зазор между сегментами — шов
            prism(m, "Body", [at(r_hub + 0.05, a0), at(r_hub + 0.05, a1), at(r_mid, a1), at(r_mid, a0)],
                  s * (GRIP + 0.5), s * face, "gold")
            prism(m, "Body", [at(r_mid + 0.05, a0), at(r_mid + 0.05, a1), at(r_out, a1), at(r_out, a0)],
                  s * (GRIP + 0.5), s * (face + 0.35), "darkgold")  # кант выше лица
            y, z = at((r_mid + r_out) / 2, 60 * k + 60)
            gem(m, (s * (face + 0.35), y, z), (s, 0, 0), size=0.9, color="ruby", role="Glass")


def emerald(m):
    """7 Изумрудная: тёмно-изумрудные диски из кубиков с неоновыми вставками; из края и с торцов торчат кристаллы."""
    bar(m, "deepemerald", end_color="gold")
    ridges(m, "Body", "gold")
    inlays = {(0, 2), (0, -2), (2, 0), (-2, 0), (2, 2), (-2, 2), (2, -2), (-2, -2)}

    def paint(i, j):
        if (i, j) in inlays:
            return ("Glow", "neongreen")  # неоновые вставки кольцом
        return ("Body", "darkemerald" if noise(i, j, 51) < 0.35 else "deepemerald")

    for s in (-1, 1):
        m.voxel_plate((s * DISC_X, 0, 0), pixel_circle(7), CELL, DISC_D, paint, normal=(s, 0, 0))
        for k in range(8):  # кристаллы торчат из края, чуть наружу
            a = math.radians(45 * k + 20)
            tilt = math.radians(18)
            d = (s * math.sin(tilt), math.cos(tilt) * math.cos(a), math.cos(tilt) * math.sin(a))
            long = k % 2 == 0
            crystal_prism(m, (s * DISC_X, 3.9 * math.cos(a), 3.9 * math.sin(a)), d, 4.4 if long else 3.0,
                          0.8 if long else 0.6)
        for d, length in (((s, 0.35, 0.2), 3.2), ((s, -0.3, -0.35), 2.4)):  # друза на торце
            crystal_prism(m, (s * (END_X + 0.2), 0, 0), d, length, 0.7)
    return disc_lights("neongreen")


def diamond(m):
    """8 Алмазная: диски — огранённые стеклянные кристаллы с неоновым ядром в серебряной оправе с лапками."""
    ridges(m, "Body", "steel")
    mount = 1.2
    g0 = GRIP + mount  # начало кристалла
    pav, gird, crown = 0.9, 1.0, 1.4
    top = g0 + pav + gird + crown
    bar(m, "silver", end=top + 0.5)

    def ring(r, x, offset):
        return [(x, r * math.cos(math.radians(30 * k + offset)), r * math.sin(math.radians(30 * k + offset)))
                for k in range(12)]

    for s in (-1, 1):
        m.voxel_plate((s * (GRIP + mount / 2), 0, 0), pixel_circle(5), CELL, mount, one("Body", "silver"),
                      normal=(s, 0, 0))
        facets = ring(3.6, s * g0, 15) + ring(5.2, s * (g0 + pav), 0) + ring(5.2, s * (g0 + pav + gird), 0)
        m.hull("Glass", facets + ring(3.3, s * top, 15), "diamond")
        m.cylinder("Glow", (s * (g0 + pav + gird / 2), 0, 0), 2.3, pav + gird + 0.6, "neoncyan", axis="x",
                   segments=8, bevel=0)  # неоновое ядро внутри
        for k in range(6):  # лапки оправы держат кристалл за пояс
            a = 60 * k
            r = math.radians(a)
            m.box("Body", (s * (g0 + 0.7), 5.35 * math.cos(r), 5.35 * math.sin(r)), (2.4, 0.55, 0.7), "silver",
                  rotation=rot(x=a), bevel=0.12)
        m.box("Body", (s * (top + 0.75), 0, 0), (0.5, 2.0, 2.0), "steel", bevel=0.12)
        tip = s * (top + 1.0)
        m.hull("Glass", ring(1.0, tip, 0) + [(tip + s * 1.2, 0, 0)], "diamond")
    return disc_lights("neoncyan", x=GRIP + mount + pav + gird / 2)


def cosmic(m):
    """10 Космическая (референс заказчика): толстые, почти кубические диски из тёмных «космических» кубиков
    (чёрно-фиолетовые, фиолетовые, синие, светящиеся «туманности»), рельеф к грифу, по ободу тёмные швы рядов;
    белые светящиеся кубики по краю, светящиеся ядра со звездой на ободе и снаружи; на диске толстое розовое
    неоновое кольцо, вокруг — два тонких голубых кольца-орбиты; короткий гриф с розовыми неоновыми полосами."""
    grip = 3.4  # гриф короче, чем у остальных: диски почти вплотную, как на референсе
    depth = 5.2
    x = grip + depth / 2
    face = grip + depth
    bar(m, "cosmicblack", end_color="cosmicdark", end=face + 0.6)
    ridges(m, "Glow", "magenta", width=0.6, half=grip)
    glow_cells = {(-1, -3), (0, -3), (1, 3), (3, 1)}  # белые светящиеся кубики по краю
    nebula = {(-2, 1), (2, -1), (0, 2)}  # светящиеся фиолетовые кубики-«туманности»

    def paint(i, j):
        if (i, j) in glow_cells:
            return ("Glow", "whiteglow")
        if (i, j) in nebula:
            return ("Glow", "violet")
        n = noise(i, j, 61)
        return ("Body", "cosmicblue" if n < 0.12 else "cosmicmid" if n < 0.4 else "cosmicblack")

    r = 3.5 * CELL
    for s in (-1, 1):
        m.voxel_plate((s * x, 0, 0), pixel_circle(7), CELL, depth, paint, normal=(-s, 0, 0))
        for t in (-1, 1):  # тёмные швы рядов по ободу
            m.voxel_plate((s * (x + t * depth / 6), 0, 0), pixel_circle(7), CELL * 1.012, 0.14,
                          one("Body", "cosmicblack"), normal=(s, 0, 0), groove=0)
        for sz in (-1, 1):  # светящееся ядро на ободе спереди и сзади
            m.box("Glow", (s * x, 0, sz * (r + 0.05)), (2.2, 2.2, 0.3), "violet", bevel=0)
            gem(m, (s * x, 0, sz * (r + 0.2)), (0, 0, sz), size=1.0, color="whiteglow")
        m.box("Glow", (s * (face + 0.05), 2.2, 2.2), (0.3, 2.2, 2.2), "violet", bevel=0)  # и снаружи
        gem(m, (s * (face + 0.2), 2.2, 2.2), (s, 0, 0), size=1.0, color="whiteglow")
        # Толстое розовое кольцо на диске и два тонких голубых кольца-орбиты, прижатых к нему.
        m.torus("Glow", (s * (x - 0.6), 0, 0), 6.0, 0.55, "magenta", axis="x", segments=24, minor_segments=4)
        for yaw, roll in ((22, 25), (-20, -28)):
            m.torus("Glow", (s * x, 0, 0), 6.5, 0.17, "neoncyan", axis="x", segments=16, minor_segments=3,
                    rotation=rot(y=yaw * s, z=roll))
    lamps = [(s * (grip + 0.5), 1.0, sz * 6.5) for s in (-1, 1) for sz in (-1, 1)]
    return lights("violet", lamps, brightness=1)  # тело тёмное, светятся детали — как на референсе

BUILDERS = {
    1: ("Деревянная", wooden),
    2: ("Каменная", stone),
    3: ("Железная", iron),
    4: ("Бронзовая", bronze),
    5: ("Серебряная", silver),
    6: ("Золотая", golden),
    7: ("Изумрудная", emerald),
    8: ("Алмазная", diamond),
    9: ("Неоновая", neon),
    10: ("Космическая", cosmic),
}


# ================================================================ сборка
bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.context.scene.collection
layout = {}
objects = []
LIFT = 5.8  # в превью гантель висит над полем, как на референсе
SPACING = 22
FRONT = {9, 10}  # гантели с референсом заказчика — превью ещё и в его ракурсе


def spot(k):
    """Место k-й гантели в превью: два ряда по пять."""
    return ((k % 5) * SPACING, LIFT, -(k // 5) * 30)


for k, index in enumerate(INDICES):
    title, builder = BUILDERS[index]
    m = Model(f"Dumbbell{index:02d}")
    extras = builder(m) or {}
    roles = m.build(collection, spot(k))
    total = sum(r["triangles"] for r in roles.values())
    layout[m.name] = {"title": title, "roles": roles, "triangles": total, **extras}
    detail = ", ".join(f"{r}={v['triangles']}" for r, v in roles.items())
    print(f"DUMBBELL {m.name} parts={len(roles)} triangles={total} budget={BUDGET} ({detail})")
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
# Лампы неона (в игре — PointLight без теней): свет ложится на кубики. На крупном плане — только свои.
lamps = {}
for k, index in enumerate(INDICES):
    for light in layout[f"Dumbbell{index:02d}"].get("lights", []):
        x, y, z = light["position"]
        data = bpy.data.lights.new("NeonLight", "POINT")
        data.color = lego.hex_to_rgb(light["color"])
        data.energy = 35 * light["brightness"] * light["range"]
        data.use_shadow = False
        obj = bpy.data.objects.new("NeonLight", data)
        ox, oy, oz = spot(k)
        obj.location = lego.to_blender((x + ox, y + oy, z + oz))
        collection.objects.link(obj)
        lamps.setdefault(k, []).append(obj)
for k, index in enumerate(INDICES):
    name = f"Dumbbell{index:02d}"
    vis = [o for o in objects if o.name.startswith(name + "_")] + ground_obj
    for other, objs in lamps.items():
        for obj in objs:
            obj.hide_render = other != k
    ox, oy, oz = spot(k)
    lego.render(os.path.join(PREVIEWS, f"{name}.png"), (ox - 17, oy + 7.5, oz + 16), (ox, oy - 0.6, oz), vis, lens=36)
    if index in FRONT:  # ракурс референса заказчика: спереди, на уровне грифа
        lego.render(os.path.join(PREVIEWS, f"{name}_front.png"), (ox - 2, oy + 3.5, oz + 21), (ox, oy - 0.3, oz), vis,
                    lens=22)
for objs in lamps.values():
    for obj in objs:
        obj.hide_render = False
mid = (min(len(INDICES), 5) - 1) * SPACING / 2
back = -(len(INDICES) - 1) // 5 * 30 / 2
scene.render.resolution_x, scene.render.resolution_y = 1800, 1000
lego.render(os.path.join(PREVIEWS, "Dumbbells_row.png"), (mid - 10, LIFT + 40, back + 80), (mid, LIFT - 3, back),
            objects + ground_obj, lens=30)
print("DUMBBELLS_OK")

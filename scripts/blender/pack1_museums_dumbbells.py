"""Пачка 1 (D28, D30, D31): 5 моделей музея и 10 гантелей из LEGO-кирпичей → assets/models/Pack1.fbx.

Музей — классическое здание с колоннами, игрок восстанавливает его по уровням:
1 (ур. 1–2) руины: сломанные и упавшие колонны, обломки фронтона, дыры в крыше, леса и доски;
2 (ур. 3–4) восстановленный малый зал, 2 колонны, фронтон; 3 (ур. 5–6) портик на 4 колонны;
4 (ур. 7–8) 6 колонн, окна с карнизами, купол; 5 (ур. 9–10) золото, вазы, статуи.
Стиль референса: крупные блоки с мягкой фаской (1–2 сегмента), LEGO-рисунок даёт материал игры.
Светлый камень; цвет участка — крыша и купол (AccentDark), тимпан (Accent), знамёна и брезент (DecorAccent).
Начало координат — центр участка на уровне пола, вход в -z: фасад на z = FACADE, проём 12×10, над ним
место под вывеску (y ≈ 11.5, ширина 18); внутри свободно для витрин. Бюджет: музей ≤ 20 000 треугольников.
Гантели: центр рукояти в начале координат, ось x, ~16 стадов, ≤ 3 000 треугольников.

Запуск из корня репозитория:
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup \\
    --python scripts/blender/pack1_museums_dumbbells.py -- . <папка превью>
Пишет assets/models/Pack1.fbx и assets/models/Pack1.layout.json, превью — в указанную папку.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lego  # noqa: E402
from lego import Model, rot  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(PREVIEWS, exist_ok=True)

BACK = 21.0
FACADE = -12.0
DOOR_W, DOOR_H = 12.0, 10.0
COLUMN_Z = -19.4
SIGN_Y = 11.5
WALL_T = 1.4
MUSEUM_BUDGET = 20000
DUMBBELL_BUDGET = 3000


# ================================================================ части классики
def column(m, x, z, height, cap="white", radius=1.05, drums=3):
    """Колонна: квадратная плита, круглая база, ствол из барабанов с лёгким сужением, капитель."""
    m.box("Body", (x, 0.35, z), (3.0, 0.7, 3.0), "white", bevel=0.15)
    m.cylinder("Body", (x, 0.95, z), radius + 0.35, 0.5, "white", segments=14, bevel=0.15)
    shaft = height - 2.6
    for i in range(drums):
        r0 = radius - 0.12 * i / drums
        r1 = radius - 0.12 * (i + 1) / drums
        m.cylinder("Body", (x, 1.2 + (i + 0.5) * shaft / drums, z), r0, shaft / drums - 0.05, "white", segments=14,
                   radius2=r1, bevel=0.1)
    m.cylinder("Body", (x, height - 1.15, z), radius - 0.1, 0.5, cap, segments=14, radius2=radius + 0.4, bevel=0.1)
    m.box("Body", (x, height - 0.45, z), (3.0, 0.9, 3.0), cap, bevel=0.18)


def entablature(m, span, h, z_front, depth, gold, frieze_color):
    """Архитрав (две ступени), фриз с триглифами или золотыми вставками, карниз с зубчиками."""
    zc = z_front + depth / 2
    m.box("Body", (0, h + 0.4, zc), (span, 0.8, depth), "white", bevel=0.12)
    m.box("Body", (0, h + 1.0, zc - 0.1), (span + 0.3, 0.5, depth + 0.2), "white", bevel=0.1)
    m.box("Body", (0, h + 1.85, zc), (span, 1.2, depth), frieze_color, bevel=0.12)
    n = int(span / 3.0)
    for i in range(n):
        x = -span / 2 + (i + 0.5) * span / n
        m.box("Body", (x, h + 1.85, z_front - 0.15), (0.9, 1.0, 0.3), "gold" if gold else "stone", bevel=0)
    m.box("Body", (0, h + 2.75, zc - 0.3), (span + 1.4, 0.6, depth + 1.0), "white", bevel=0.15)
    for i in range(int(span / 1.2)):
        x = -span / 2 + 0.6 + i * 1.2
        m.box("Body", (x, h + 2.3, z_front - 0.55), (0.6, 0.4, 0.4), "white", bevel=0)


def pediment(m, span, y, z_front, gold, emblem=True):
    """Фронтон: тимпан цвета участка, белые наклонные и нижний карнизы, эмблема."""
    ph = min(7.2, span * 0.22)
    half = span / 2
    angle = math.degrees(math.atan2(ph, half))
    rake = math.hypot(half, ph) + 1.0
    m.prism_triangle("Accent", (0, y + 0.2, z_front + 0.9), span - 1.2, ph - 0.5, 1.2, "Accent", bevel=0.08)
    for side in (-1, 1):
        m.box("Body", (side * half / 2, y + ph / 2 + 0.25, z_front + 0.5), (rake, 0.9, 2.0), "white",
              rotation=rot(z=-side * angle), bevel=0.15)
    m.box("Body", (0, y + 0.3, z_front + 0.6), (span + 1.0, 0.6, 1.8), "white", bevel=0.12)
    if emblem:
        color = "gold" if gold else "white"
        m.cylinder("Body", (0, y + ph * 0.42, z_front + 0.2), 1.5, 0.4, color, axis="z", segments=16, bevel=0.1)
        m.cylinder("Body", (0, y + ph * 0.42, z_front), 0.8, 0.3, "Accent" if not gold else "white", axis="z",
                   segments=12, bevel=0.06)
    return ph


def tiled_gable(m, z0, z1, y, width, height, rows=4):
    """Двускатная крыша рядами-«черепицей» (каждый ряд чуть выступает) и конёк."""
    depth = z1 - z0
    half = width / 2
    for side in (-1, 1):
        for r in range(rows):
            t0, t1 = r / rows, (r + 1) / rows
            x0, x1 = side * half * (1 - t0), side * half * (1 - t1)
            y0, y1 = y + height * t0, y + height * t1
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            length = math.hypot(x1 - x0, y1 - y0) + 0.5
            angle = math.degrees(math.atan2(height, half))
            m.box("AccentDark", (cx, cy + 0.2, (z0 + z1) / 2), (length, 0.6, depth), "Accent",
                  rotation=rot(z=-side * angle), bevel=0.12)
    m.box("AccentDark", (0, y + height + 0.2, (z0 + z1) / 2), (1.4, 0.8, depth + 0.4), "Accent", bevel=0.15)


def walls(m, half_w, h, windows, arched, crowns, gold, holes_extra=None, tops=None):
    """Стены зала крупными панелями: цоколь, панели между пилястрами, пояс, верхний фриз и карниз.
    Окна — проёмы в панелях. tops — функция (сторона, t) → высота обломанного верха (для руин)."""
    zs = [FACADE, BACK]
    # Боковые стены: панели между окнами.
    win = []
    if windows:
        step = (BACK - FACADE) / windows
        for i in range(windows):
            zc = FACADE + (i + 0.5) * step
            win.append((zc - 2.2, zc + 2.2))
    for sx in (-1, 1):
        x = sx * (half_w - WALL_T / 2)
        m.box("Body", (x + sx * 0.2, 0.7, (FACADE + BACK) / 2), (WALL_T + 0.4, 1.4, BACK - FACADE + 0.4), "stone",
              bevel=0.15)
        edges = [FACADE] + [v for w in win for v in w] + [BACK]
        for i in range(0, len(edges), 2):
            a, b = edges[i], edges[i + 1]
            if b - a < 0.3:
                continue
            top = h if tops is None else tops(sx, (a + b) / 2)
            m.box("Body", (x, 1.4 + (top - 1.4) / 2, (a + b) / 2), (WALL_T, top - 1.4, b - a), "cream", bevel=0.12)
        for a, b in win:
            y0, y1 = 3.4, h - 4.2
            top = h if tops is None else tops(sx, (a + b) / 2)
            if top > y1 + 1:
                m.box("Body", (x, (y1 + top) / 2, (a + b) / 2), (WALL_T, top - y1, b - a), "cream", bevel=0.12)
            m.box("Body", (x, 1.4 + (y0 - 1.4) / 2, (a + b) / 2), (WALL_T, y0 - 1.4, b - a), "cream", bevel=0.12)
            if top > y1:
                window(m, x + sx * 0.35, (a + b) / 2, y0, y1, b - a, arched, crowns, gold)
        if tops is None:
            m.box("Body", (x + sx * 0.15, h - 2.4, (FACADE + BACK) / 2), (WALL_T + 0.3, 0.6, BACK - FACADE), "white",
                  bevel=0.12)
    # Задняя стена.
    top = h if tops is None else tops(0, 0)
    m.box("Body", (0, 0.7, BACK + 0.2), (2 * half_w + 0.4, 1.4, WALL_T + 0.4), "stone", bevel=0.15)
    m.box("Body", (0, 1.4 + (top - 1.4) / 2, BACK - WALL_T / 2), (2 * half_w, top - 1.4, WALL_T), "cream", bevel=0.12)
    # Фасад с проёмом.
    side_w = half_w - DOOR_W / 2
    for sx in (-1, 1):
        cx = sx * (DOOR_W / 2 + side_w / 2)
        m.box("Body", (cx, 0.7, FACADE - 0.2), (side_w, 1.4, WALL_T + 0.4), "stone", bevel=0.15)
        ftop = h if tops is None else tops(2 * sx, 0)
        m.box("Body", (cx, 1.4 + (ftop - 1.4) / 2, FACADE), (side_w, ftop - 1.4, WALL_T), "cream", bevel=0.12)
    lintel_top = h if tops is None else tops(3, 0)
    m.box("Body", (0, DOOR_H + (lintel_top - DOOR_H) / 2, FACADE), (DOOR_W, lintel_top - DOOR_H, WALL_T), "cream",
          bevel=0.12)
    # Пилястры по углам.
    for sx in (-1, 1):
        for z in zs:
            ptop = h if tops is None else min(h, tops(sx, z))
            m.box("Body", (sx * (half_w - 0.5), ptop / 2, z + (0.3 if z == BACK else -0.3)), (1.8, ptop, 1.8), "white",
                  bevel=0.18)


def window(m, x, z, y0, y1, width, arched, crown, gold):
    h = y1 - y0
    m.box("Glass", (x, (y0 + y1) / 2, z), (0.3, h, width), "glass", bevel=0)
    trim = "gold" if gold else "white"
    for dz in (-width / 2 - 0.35, width / 2 + 0.35):
        m.box("Body", (x, (y0 + y1) / 2, z + dz), (1.0, h + 0.4, 0.7), "white", bevel=0.12)
    m.box("Body", (x, y0 - 0.3, z), (1.4, 0.6, width + 1.8), "white", bevel=0.12)
    if arched:
        m.cylinder("Body", (x, y1, z), width / 2 + 0.7, 0.9, "white", axis="x", segments=12, bevel=0.1)
        m.cylinder("Glass", (x, y1, z), width / 2, 0.35, "glass", axis="x", segments=12, bevel=0)
        m.box("Body", (x, y1 + width / 2 + 0.4, z), (1.2, 1.0, 0.9), trim, bevel=0.12)  # замковый камень
    else:
        m.box("Body", (x, y1 + 0.3, z), (1.2, 0.6, width + 1.2), "white", bevel=0.12)
    if crown:
        m.box("Body", (x, y1 + (width / 2 + 1.3 if arched else 0.9), z), (1.6, 0.5, width + 2.2), trim, bevel=0.1)


def doors(m, gold):
    """Распахнутые внутрь двери у краёв проёма и наличник."""
    trim = "gold" if gold else "white"
    for sx in (-1, 1):
        m.box("Body", (sx * (DOOR_W / 2 + 0.55), DOOR_H / 2, FACADE - 0.45), (1.1, DOOR_H, 0.9), trim, bevel=0.12)
        m.box("Body", (sx * (DOOR_W / 2 - 0.3), DOOR_H / 2 - 0.4, FACADE + 2.6), (0.4, DOOR_H - 0.8, 4.6), "darkwood",
              bevel=0.12)
        m.box("Body", (sx * (DOOR_W / 2 - 0.55), DOOR_H / 2 - 0.4, FACADE + 4.2), (0.2, 0.5, 0.5), "gold", bevel=0.05)
    m.box("Body", (0, DOOR_H + 0.35, FACADE - 0.45), (DOOR_W + 2.2, 0.7, 0.9), trim, bevel=0.12)


def steps(m, span, count):
    for k in range(count):
        m.box("Body", (0, -0.35 - k * 0.7, -21.6 - k * 1.3), (span + 1.0 + k * 2.0, 0.7, 1.6), "stone", bevel=0.12)
    for sx in (-1, 1):
        m.box("Body", (sx * (span / 2 + 1.0 + count), -0.7 * count / 2 + 0.1, -21.6 - (count - 1) * 0.65),
              (1.6, 0.7 * count + 0.4, 1.3 * count + 0.8), "darkstone", bevel=0.15)


def dome(m, radius, gold, cz=5.0, base=0.0):
    trim = "gold" if gold else "white"
    m.cylinder("Body", (0, base + 0.5, cz), radius + 1.0, 1.0, "white", segments=24, bevel=0.15)
    m.cylinder("Body", (0, base + 3.0, cz), radius, 4.0, "cream", segments=24, bevel=0.12)
    for k in range(12):
        a = 2 * math.pi * k / 12
        m.box("Glass", (radius * math.cos(a), base + 3.0, cz + radius * math.sin(a)), (1.0, 2.2, 1.0), "glass", bevel=0)
        b = a + math.pi / 12
        m.box("Body", ((radius + 0.25) * math.cos(b), base + 3.0, cz + (radius + 0.25) * math.sin(b)), (0.7, 4.0, 0.7),
              "white", bevel=0.1)
    m.cylinder("Body", (0, base + 5.3, cz), radius + 0.6, 0.6, "white", segments=24, bevel=0.1)
    m.sphere("AccentDark", (0, base + 5.6, cz), radius, "Accent", segments=24, rings=12, half=True)
    for k in range(8):  # рёбра
        a = 2 * math.pi * k / 8
        for j in range(5):
            t = (j + 0.5) / 5 * math.pi / 2
            r = radius + 0.1
            m.box("Body", (r * math.cos(t) * math.cos(a), base + 5.6 + r * math.sin(t), cz + r * math.cos(t) * math.sin(a)),
                  (0.55, 0.55, 0.55), trim, bevel=0)
    top = base + 5.6 + radius
    for k in range(6):  # фонарик на колонках
        a = 2 * math.pi * k / 6
        m.box("Body", (1.2 * math.cos(a), top + 1.2, cz + 1.2 * math.sin(a)), (0.4, 2.0, 0.4), "white", bevel=0)
    m.cylinder("Body", (0, top + 0.1, cz), 1.8, 0.4, "white", segments=12, bevel=0.08)
    m.cylinder("Body", (0, top + 2.4, cz), 1.9, 0.5, trim, segments=12, bevel=0.08)
    m.cylinder("AccentDark", (0, top + 3.4, cz), 1.6, 1.6, "Accent", segments=12, radius2=0.2, bevel=0)
    m.sphere("Body", (0, top + 4.4, cz), 0.6, "gold", segments=12, rings=6)


def balustrade(m, x0, z0, x1, z1, y):
    along_x = abs(x1 - x0) > 1
    length = abs(x1 - x0) if along_x else abs(z1 - z0)
    n = max(1, int(length / 2.0))
    for i in range(n + 1):
        t = -length / 2 + i * length / n
        px, pz = ((x0 + x1) / 2 + t, z0) if along_x else (x0, (z0 + z1) / 2 + t)
        m.cylinder("Body", (px, y + 0.8, pz), 0.35, 1.6, "white", segments=8, bevel=0)
    size = (length + 0.8, 0.5, 1.0) if along_x else (1.0, 0.5, length + 0.8)
    m.box("Body", ((x0 + x1) / 2, y + 1.85, (z0 + z1) / 2), size, "white", bevel=0.1)


# ================================================================ декор
def lantern(m, x, z):
    m.box("Decor", (x, 0.5, z), (1.8, 1.0, 1.8), "darkstone", bevel=0.15)
    m.cylinder("Decor", (x, 3.6, z), 0.3, 5.2, "black", segments=8, bevel=0)
    m.box("Decor", (x, 6.6, z), (1.5, 1.8, 1.5), "yellow", bevel=0.2)
    m.cylinder("Decor", (x, 7.8, z), 1.1, 0.7, "black", segments=8, radius2=0.2, bevel=0)


def banner(m, x, top, z, length=6.5):
    m.box("Decor", (x, top, z), (3.6, 0.4, 0.4), "gold", bevel=0.1)
    m.box("DecorAccent", (x, top - length / 2 - 0.2, z), (3.0, length, 0.2), "Accent", bevel=0.05)
    m.wedge("DecorAccent", (x, top - length - 0.8, z), (3.0, 1.2, 0.2), "Accent", down="+z", bevel=0)
    m.cylinder("Decor", (x, top - length * 0.35, z - 0.15), 0.8, 0.15, "gold", axis="z", segments=10, bevel=0)


def flag(m, x, y, z, height=6.0):
    m.cylinder("Decor", (x, y + height / 2, z), 0.2, height, "white", segments=8, bevel=0)
    m.box("DecorAccent", (x, y + height - 1.3, z + 1.7), (0.15, 2.2, 3.2), "Accent", bevel=0.04)
    m.sphere("Decor", (x, y + height + 0.35, z), 0.4, "gold", segments=8, rings=5)


def pedestal(m, x, z, top_color="white"):
    m.box("Decor", (x, -0.3, z), (3.8, 2.2, 3.8), "darkstone", bevel=0.15)
    m.box("Decor", (x, 1.6, z), (3.0, 1.6, 3.0), top_color, bevel=0.15)
    m.box("Decor", (x, 2.6, z), (3.5, 0.4, 3.5), "darkstone", bevel=0.1)
    return 2.8


def statue(m, x, y, z, color):
    """Классическая статуя: хитон-конус, торс, руки (одна с поднятым факелом), голова."""
    m.cylinder("Decor", (x, y + 0.25, z), 1.1, 0.5, color, segments=12, bevel=0.08)
    m.cylinder("Decor", (x, y + 2.0, z), 1.05, 3.0, color, segments=12, radius2=0.7, bevel=0.1)
    m.box("Decor", (x, y + 4.0, z), (1.8, 1.4, 1.0), color, bevel=0.2)
    m.box("Decor", (x - 1.1, y + 3.4, z), (0.5, 1.8, 0.6), color, bevel=0.12)
    m.box("Decor", (x + 1.0, y + 5.0, z), (0.5, 1.8, 0.6), color, bevel=0.12, rotation=rot(z=-15))
    m.cylinder("Decor", (x + 1.25, y + 6.2, z), 0.35, 0.9, color, segments=8, radius2=0.5, bevel=0)
    m.gem("Glow", (x + 1.25, y + 6.9, z), 0.45, 0.01, 0.8, "orange", segments=6, axis="y", table=1.0)
    m.cylinder("Decor", (x, y + 4.9, z), 0.3, 0.4, color, segments=8, bevel=0)
    m.sphere("Decor", (x, y + 5.6, z), 0.75, color, segments=12, rings=8)


# ================================================================ музеи
def classic(name, half_w, h, columns, windows, roof="gable", dome_r=None, gold=False, n_steps=2, decor=None):
    m = Model(name)
    walls(m, half_w, h, windows, arched=windows >= 3, crowns=windows >= 3, gold=gold)
    doors(m, gold)
    xs = sorted({s * x for x in columns for s in (-1, 1)})
    span = max(abs(x) for x in xs) * 2 + 4.0
    for x in xs:
        column(m, x, COLUMN_Z, h, cap="gold" if gold else "white")
    depth = FACADE - COLUMN_Z + 1.8
    entablature(m, span, h, COLUMN_Z - 1.5, depth, gold, "gold" if gold else "cream")
    # Карниз по периметру зала.
    m.box("Body", (0, h + 0.5, (FACADE + BACK) / 2 + 0.3), (2 * half_w + 1.4, 1.0, BACK - FACADE + 0.6), "white",
          bevel=0.15)
    py = h + 3.05
    ph = pediment(m, span, py, COLUMN_Z - 2.2, gold)
    if roof == "gable":
        tiled_gable(m, COLUMN_Z - 1.6, BACK + 1.0, py + 0.5, max(span, 2 * half_w) + 1.2, ph - 0.3)
    else:
        tiled_gable(m, COLUMN_Z - 1.6, FACADE + 1.5, py + 0.5, span + 1.2, ph - 0.3, rows=3)
        m.box("Body", (0, h + 1.3, (FACADE + BACK) / 2 + 1.0), (2 * half_w - 0.4, 0.6, BACK - FACADE - 1.4), "slate",
              bevel=0.1)
        balustrade(m, -half_w + 0.5, BACK, half_w - 0.5, BACK, h + 1.0)
        for x in (-half_w + 0.5, half_w - 0.5):
            balustrade(m, x, FACADE + 2.0, x, BACK, h + 1.0)
    if dome_r:
        dome(m, dome_r, gold, cz=6.0, base=h + 1.6)
    steps(m, span, n_steps)
    if decor:
        decor(m, h, span, py, ph)
    return m, {"wallHeight": h, "signY": SIGN_Y, "lampHeight": h - 2.5, "facadeZ": FACADE, "halfWidth": half_w}


def decor_hall(m, h, span, py, ph):
    for x in (-span / 2 - 1.8, span / 2 + 1.8):
        lantern(m, x, -21.0)
    for x in (-9.5, 9.5):
        m.box("Decor", (x, 0.7, -13.8), (5.0, 1.4, 1.8), "darkstone", bevel=0.15)
        for k in range(4):
            m.sphere("Decor", (x - 1.8 + k * 1.2, 1.8, -13.8), 0.75, "leaf" if k % 2 else "green", segments=8, rings=6)


def decor_banners(m, h, span, py, ph):
    for x in (-15.0, 15.0):
        banner(m, x, h - 0.4, FACADE - 0.9)
    for x in (-span / 2 - 1.8, span / 2 + 1.8):
        lantern(m, x, -21.0)


def decor_dome(m, h, span, py, ph):
    decor_banners(m, h, span, py, ph)
    for x in (-span / 2 + 1.0, span / 2 - 1.0):
        y = pedestal(m, x, -25.8)
        m.vase("Decor", (x, y, -25.8), 3.4, "white")
    for x in (-19.5, 19.5):
        flag(m, x, h + 3.4, 19.0)


def decor_gold(m, h, span, py, ph):
    decor_banners(m, h, span, py, ph)
    for x in (-span / 2 + 1.0, span / 2 - 1.0):
        y = pedestal(m, x, -25.8)
        statue(m, x, y, -25.8, "gold")
    for x in (-span / 2 + 0.8, span / 2 - 0.8):
        m.vase("Decor", (x, py + 0.6, COLUMN_Z - 1.6), 2.6, "gold")
    m.box("Decor", (0, py + ph + 0.6, COLUMN_Z - 1.6), (1.8, 0.6, 1.8), "white", bevel=0.12)
    statue(m, 0, py + ph + 0.9, COLUMN_Z - 1.6, "gold")
    for x in (-19.5, 19.5):
        flag(m, x, h + 3.4, 19.0, height=7.0)


# ---------------------------------------------------------------- руины
def museum_ruins():
    """Руины классического музея: стены обломаны, дыры в крыше, колонны сломаны и упали, обломки фронтона,
    леса и доски. Внутри свободно для витрин."""
    m = Model("Museum1")
    half_w, h = 19.0, 14.4

    def tops(side, z):
        if side == 3:  # над входом держится кусок стены под вывеску
            return 13.6
        if side in (-2, 2):
            return 12.0 if side < 0 else 8.4
        if side == 0:
            return 10.8
        if side < 0:
            return 12.6 if z < 2 else 9.0
        return 7.2 if z < 6 else 11.4

    walls(m, half_w, h, windows=2, arched=False, crowns=False, gold=False, tops=tops)
    # Проём входа: наличники уцелели, двери — одна висит, другая лежит.
    for sx in (-1, 1):
        m.box("Body", (sx * (DOOR_W / 2 + 0.55), DOOR_H / 2, FACADE - 0.45), (1.1, DOOR_H, 0.9), "white", bevel=0.12)
    m.box("Body", (0, DOOR_H + 0.35, FACADE - 0.45), (DOOR_W + 2.2, 0.7, 0.9), "white", bevel=0.12)
    m.box("Body", (-DOOR_W / 2 + 0.3, DOOR_H / 2 - 0.6, FACADE + 2.4), (0.4, DOOR_H - 1.2, 4.4), "darkwood",
          rotation=rot(y=8), bevel=0.12)
    m.box("Body", (DOOR_W / 2 + 3.0, 0.3, FACADE - 4.0), (4.4, 0.4, DOOR_H - 1.2), "darkwood", rotation=rot(y=25),
          bevel=0.12)

    # Колонны портика: целая, сломанная пополам, пенёк и упавшая (по частям на земле).
    column(m, -10.5, COLUMN_Z, h)
    m.box("Body", (-10.5, 0.35, COLUMN_Z), (3.0, 0.7, 3.0), "white", bevel=0.15)
    m.box("Body", (10.5, 0.35, COLUMN_Z), (3.0, 0.7, 3.0), "white", bevel=0.15)
    m.cylinder("Body", (10.5, 0.95, COLUMN_Z), 1.4, 0.5, "white", segments=14, bevel=0.15)
    m.cylinder("Body", (10.5, 3.6, COLUMN_Z), 1.05, 4.8, "white", segments=14, radius2=1.0, bevel=0.1)
    m.cylinder("Body", (10.4, 6.6, COLUMN_Z + 0.2), 1.0, 1.4, "white", segments=14, radius2=0.95,
               rotation=rot(x=14, z=10), bevel=0.1)  # обломанный верх
    for sx, z in ((-17.5, COLUMN_Z), (17.5, COLUMN_Z)):
        m.box("Body", (sx, 0.35, z), (3.0, 0.7, 3.0), "white", bevel=0.15)
        m.cylinder("Body", (sx, 1.6, z), 1.05, 1.8, "white", segments=14, bevel=0.1)
    # Упавшая колонна: барабаны лежат вдоль фасада, капитель отдельно.
    for i, (x, yaw) in enumerate(((19.5, 80), (19.0, 95), (18.6, 70))):
        m.cylinder("Body", (x + i * 0.3, 1.05, -24.6 + i * 3.4), 1.05, 3.1, "white", axis="z", segments=14,
                   rotation=rot(y=yaw - 90), bevel=0.1)
    m.box("Body", (14.8, 0.45, -25.2), (3.0, 0.9, 3.0), "white", rotation=rot(y=30, x=8), bevel=0.18)

    # Антаблемент: уцелел над левой колонной, правый конец рухнул и лежит одним краем на земле.
    m.box("Body", (-8.0, h + 0.6, COLUMN_Z + 1.0), (10.0, 1.4, 4.0), "white", bevel=0.15)
    m.box("Body", (5.0, h - 4.2, COLUMN_Z + 0.8), (13.0, 1.4, 3.6), "white", rotation=rot(z=34), bevel=0.15)
    # Обломки фронтона на земле: треугольный кусок тимпана и наклонного карниза.
    m.prism_triangle("Accent", (-15.6, 0.0, -25.0), 6.0, 2.4, 1.2, "Accent", bevel=0.08)
    m.box("Body", (-15.4, 0.5, -26.0), (7.0, 0.9, 2.0), "white", rotation=rot(y=-12), bevel=0.15)

    # Крыша: стропила над залом (на них висят лампы), уцелевшие куски кровли, остальное — дыры.
    for z in (-6.0, -2.0, 4.0, 12.0, 17.0):
        m.box("Body", (0, 13.9, z), (2 * half_w - 0.6, 0.9, 0.9), "darkwood", bevel=0.12)
    m.box("Body", (0, 14.8, (FACADE + BACK) / 2), (0.9, 0.9, BACK - FACADE), "darkwood", bevel=0.12)
    for side in (-1, 1):  # прогоны вдоль скатов
        m.box("Body", (side * 9.5, 17.2, 6.0), (0.7, 0.7, 26.0), "darkwood", bevel=0.1)
    for z in (-6.0, 4.0, 12.0, 17.0):  # стропила-«ноги» от стен к коньку
        for side in (-1, 1):
            m.box("Body", (side * half_w / 2, 17.1, z), (math.hypot(half_w, 5.8), 0.6, 0.6), "darkwood",
                  rotation=rot(z=-side * math.degrees(math.atan2(5.8, half_w))), bevel=0.08)
    angle = math.degrees(math.atan2(5.8, half_w))
    for zc, length, side in ((15.5, 11.0, -1), (4.0, 7.0, -1), (17.0, 8.0, 1)):
        x = side * half_w / 2
        m.box("AccentDark", (x, 17.6, zc), (math.hypot(half_w, 5.8) + 0.6, 0.6, length), "Accent",
              rotation=rot(z=-side * angle), bevel=0.12)

    # Обломанный неровный верх стен: ступеньки из блоков на краях проломов.
    for sx, z0, z1, top in ((-1, FACADE, 2.0, 12.6), (-1, 2.0, BACK, 9.0), (1, FACADE, 6.0, 7.2), (1, 6.0, BACK, 11.4)):
        x = sx * (half_w - WALL_T / 2)
        for i in range(3):
            t = (math.sin((z0 + i) * 7.3) * 0.5 + 0.5)
            length = 2.0 + 2.5 * t
            zc = z0 + (z1 - z0) * (0.15 + 0.3 * i)
            m.box("Body", (x, top + 0.6, zc), (WALL_T, 1.2, length), "cream", bevel=0.12)
            if i == 1:
                m.box("Body", (x, top + 1.8, zc + 0.6), (WALL_T, 1.2, length * 0.5), "cream", bevel=0.12)
    m.box("Body", (-6.0, 11.4, BACK - WALL_T / 2), (8.0, 1.2, WALL_T), "cream", bevel=0.12)
    m.box("Body", (5.0, 11.4, BACK - WALL_T / 2), (5.0, 1.2, WALL_T), "cream", bevel=0.12)
    m.box("Body", (-14.0, 12.4, FACADE), (4.0, 0.8, WALL_T), "cream", bevel=0.12)

    # Строительные леса вдоль правой стены и доски.
    sx = half_w + 2.4
    for z in (-10.0, -2.0, 6.0):
        for dx in (-1.2, 1.2):
            m.box("Body", (sx + dx, 7.0, z), (0.5, 14.0, 0.5), "lightwood", bevel=0)
    for y in (4.8, 9.6):
        m.box("Body", (sx, y, -2.0), (3.2, 0.35, 17.0), "wood", bevel=0.08)
        m.box("Body", (sx + 1.2, y + 1.2, -2.0), (0.3, 0.3, 17.0), "lightwood", bevel=0)
    m.box("Body", (sx + 1.1, 5.0, 2.0), (0.3, 10.0, 0.3), "lightwood", rotation=rot(x=0, z=0), bevel=0)
    for k in range(4):
        m.box("Body", (-13.0 + k * 0.15, 0.25 + k * 0.4, -26.5), (6.0, 0.35, 1.2), "wood", rotation=rot(y=8 * k),
              bevel=0.06)
    # Груды камней внутри по углам (не на месте витрин) и у фасада.
    for cx, cz, seed in ((-15.5, 18.0, 1), (15.5, 18.5, 2), (16.0, -8.5, 3), (-21.5, -16.0, 4)):
        for i in range(5):
            r1 = (math.sin(i * 12.9 + seed * 78.2) * 43758.5) % 1
            r2 = (math.sin(i * 39.3 + seed * 11.7) * 24634.6) % 1
            m.box("Body", (cx + (r1 - 0.5) * 3.2, 0.5 + (i // 3) * 0.9, cz + (r2 - 0.5) * 3.2),
                  (1.6 + r2, 1.0, 1.4 + r1), "stone" if i % 2 else "cream", rotation=rot(y=r1 * 90, z=(r2 - 0.5) * 20),
                  bevel=0.15)
    # Декор (уровень 2): брезент цвета участка на лесах, фонари, ограждение у обломков.
    m.box("DecorAccent", (sx + 1.6, 9.0, -2.0), (0.15, 9.0, 15.0), "Accent", bevel=0.03)
    for x in (-15.0, 15.0):
        lantern(m, x, -21.5)
    for x in (-19.0, -14.0):
        m.box("Decor", (x, 1.4, -28.0), (4.6, 0.6, 0.3), "orange", bevel=0.05)
        m.box("Decor", (x, 2.2, -28.0), (4.6, 0.6, 0.3), "white", bevel=0.05)
        for dx in (-2.0, 2.0):
            m.box("Decor", (x + dx, 1.2, -28.0), (0.4, 2.4, 0.4), "white", bevel=0)
    return m, {"wallHeight": h, "signY": SIGN_Y, "lampHeight": 13.4, "facadeZ": FACADE, "halfWidth": half_w}


MUSEUMS = [
    museum_ruins,
    lambda: classic("Museum2", 16.0, 14.4, (10.5,), windows=2, decor=decor_hall),
    lambda: classic("Museum3", 19.0, 14.4, (10.5, 17.0), windows=2, decor=decor_banners),
    lambda: classic("Museum4", 21.5, 16.8, (10.5, 15.0, 19.5), windows=3, roof="flat", dome_r=7.5, n_steps=3,
                    decor=decor_dome),
    lambda: classic("Museum5", 21.5, 18.0, (10.5, 15.0, 19.5), windows=3, roof="flat", dome_r=8.5, gold=True,
                    n_steps=3, decor=decor_gold),
]


# ================================================================ гантели
def handle(m, length, color, ring=None, radius=0.9, segments=10):
    m.cylinder("Body", (0, 0, 0), radius, length, color, axis="x", segments=segments, bevel=0.1)
    if ring:
        for k in (-1.4, 0, 1.4):
            m.cylinder("Body", (k, 0, 0), radius + 0.18, 0.5, ring, axis="x", segments=segments, bevel=0.08)


def dumbbell(index):
    m = Model(f"Dumbbell{index:02d}")
    sides = (-1, 1)
    if index == 1:  # Деревянная: круглые чурбаки из досок на брёвнышке
        handle(m, 15.0, "darkwood", ring="wood", radius=1.0, segments=8)
        for s in sides:
            m.voxel_disc("Body", (s * 5.2, 0, 0), 4.6, 1.8, "wood", cell=1.5)
            m.voxel_disc("Body", (s * 6.9, 0, 0), 3.6, 1.4, "lightwood", cell=1.5)
            m.box("Body", (s * 7.8, 0, 0), (0.5, 1.4, 1.4), "darkwood", bevel=0.1)
    elif index == 2:  # Каменная: грубые каменные глыбы на перевязанной ручке
        m.box("Body", (0, 0, 0), (14.0, 1.8, 1.8), "darkrock", bevel=0.25)
        m.box("Body", (0, 0, 0), (4.0, 2.1, 2.1), "wood", bevel=0.2)
        for s in sides:
            m.box("Body", (s * 5.8, 0, 0), (4.8, 6.4, 6.0), "rock", rotation=rot(y=6 * s), bevel=0.5)
            m.box("Body", (s * 5.4, 3.4, 0.8), (3.6, 1.6, 3.4), "darkrock", bevel=0.35)
            m.box("Body", (s * 6.6, -2.2, -2.8), (2.6, 2.4, 1.6), "darkrock", bevel=0.3)
            m.box("Body", (s * 8.0, 1.0, 1.6), (1.2, 2.0, 2.0), "rock", rotation=rot(x=20), bevel=0.25)
    elif index == 3:  # Железная: стопка блинов из брусков
        handle(m, 17.0, "steel", ring="iron", radius=0.8)
        for s in sides:
            for k, (r, c) in enumerate(((4.8, "iron"), (4.0, "steel"), (3.2, "iron"))):
                m.voxel_disc("Body", (s * (4.6 + k * 1.15), 0, 0), r, 1.05, c, cell=1.6)
            m.cylinder("Body", (s * 3.6, 0, 0), 1.4, 0.9, "black", axis="x", segments=10, bevel=0.1)
    elif index == 4:  # Бронзовая: шестигранные головы
        handle(m, 14.0, "steel", ring="black")
        for s in sides:
            m.cylinder("Body", (s * 6.0, 0, 0), 4.3, 4.4, "bronze", axis="x", segments=6, bevel=0.4)
            m.cylinder("Body", (s * 8.45, 0, 0), 3.0, 0.6, "darkbronze", axis="x", segments=6, bevel=0.12)
            m.cylinder("Body", (s * 3.55, 0, 0), 3.4, 0.6, "darkbronze", axis="x", segments=6, bevel=0.12)
    elif index == 5:  # Серебряная: шары из брусков
        handle(m, 12.0, "steel", ring="silver")
        for s in sides:
            m.voxel_ball("Body", (s * 6.6, 0, 0), 4.4, "silver", cell=1.6)
            m.cylinder("Body", (s * 3.0, 0, 0), 1.8, 1.0, "steel", axis="x", segments=10, bevel=0.1)
    elif index == 6:  # Золотая: диски-короны с рубинами
        handle(m, 15.0, "darkgold", ring="gold")
        for s in sides:
            m.voxel_disc("Body", (s * 5.6, 0, 0), 4.8, 2.2, "gold", cell=1.6)
            for k in range(8):
                a = 2 * math.pi * k / 8
                m.box("Body", (s * 5.6, 5.3 * math.cos(a), 5.3 * math.sin(a)), (1.6, 1.4, 1.4), "gold",
                      rotation=rot(x=math.degrees(a)), bevel=0.2)
            m.voxel_disc("Body", (s * 7.0, 0, 0), 2.6, 0.8, "darkgold", cell=1.3)
            m.gem("Glass", (s * 7.6, 0, 0), 1.3, 0.6, 0.8, "ruby", segments=8, axis="x" if s > 0 else "-x")
    elif index == 7:  # Изумрудная: друзы кристаллов
        handle(m, 13.0, "darkemerald", ring="gold")
        for s in sides:
            m.cylinder("Body", (s * 3.6, 0, 0), 2.6, 1.0, "gold", axis="x", segments=8, bevel=0.1)
            m.cylinder("Glass", (s * 5.6, 0, 0), 2.8, 3.2, "emerald", axis="x", segments=6, bevel=0.15)
            m.gem("Glass", (s * 8.2, 0, 0), 2.8, 0.01, 2.6, "emerald", segments=6, axis="-x" if s > 0 else "x",
                  table=1.0)
            for k in range(5):
                a = 2 * math.pi * k / 5 + 0.3
                m.cylinder("Glass", (s * 5.2, 3.0 * math.cos(a), 3.0 * math.sin(a)), 0.9, 3.2, "emerald", segments=6,
                           radius2=0.0, rotation=rot(x=math.degrees(a), z=25 * s), bevel=0)
    elif index == 8:  # Алмазная: два бриллианта в серебряной оправе
        handle(m, 12.0, "silver", ring="steel")
        for s in sides:
            m.gem("Glass", (s * 5.2, 0, 0), 4.8, 1.7, 4.6, "diamond", segments=12, axis="-x" if s > 0 else "x",
                  table=0.55)
            m.cylinder("Body", (s * 3.3, 0, 0), 2.4, 0.8, "silver", axis="x", segments=12, bevel=0.1)
            for k in range(6):
                a = 2 * math.pi * k / 6
                m.box("Body", (s * 4.6, 4.2 * math.cos(a), 4.2 * math.sin(a)), (2.6, 0.6, 0.6), "silver",
                      rotation=rot(x=math.degrees(a)), bevel=0.1)
    elif index == 9:  # Неоновая: тёмные диски с неоновыми кольцами
        handle(m, 15.0, "black", ring="steel")
        for s in sides:
            for k, x in enumerate((4.6, 6.0, 7.4)):
                m.voxel_disc("Body", (s * x, 0, 0), 4.4 - k * 0.4, 1.1, "black", cell=1.6)
            for x in (5.3, 6.7):
                m.torus("Glow", (s * x, 0, 0), 4.0, 0.3, "neongreen", axis="x", segments=16, minor_segments=5)
            m.cylinder("Glow", (s * 8.1, 0, 0), 2.0, 0.4, "neongreen", axis="x", segments=12, bevel=0)
            for k in range(4):
                a = 2 * math.pi * k / 4 + math.pi / 4
                m.box("Glow", (s * 6.0, 4.6 * math.cos(a), 4.6 * math.sin(a)), (3.0, 1.0, 1.0), "neongreen",
                      rotation=rot(x=math.degrees(a)), bevel=0.12)
    elif index == 10:  # Космическая: планеты с кольцами, луны и звёзды
        handle(m, 14.0, "cosmicdark", ring="star")
        for s in sides:
            m.sphere("Body", (s * 6.6, 0, 0), 4.4, "cosmic", segments=16, rings=10)
            m.sphere("Body", (s * 6.6, 0, 0), 4.46, "cosmicdark", segments=16, rings=10, scale=(1.0, 0.3, 1.0))
            m.torus("Glow", (s * 6.6, 0, 0), 6.4, 0.4, "neoncyan", axis="y", segments=20, minor_segments=5)
            m.sphere("Body", (s * 6.6, 4.4, 4.4), 1.0, "star", segments=8, rings=6)
            m.gem("Glow", (s * 9.0, 3.0, -3.0), 0.8, 0.4, 0.4, "star", segments=4, axis="y")
    return m


# ================================================================ сборка
bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.context.scene.collection
layout = {"museums": {}, "dumbbells": {}}
objects = []
for i, build in enumerate(MUSEUMS):
    model, anchors = build()
    roles = model.build(collection, (i * 70, 0, 0))
    layout["museums"][model.name] = {"roles": roles, **anchors}
    objects += [o for o in collection.objects if o.name.startswith(model.name + "_")]
for index in range(1, 11):
    model = dumbbell(index)
    roles = model.build(collection, ((index - 1) % 5 * 24, 0, 120 + (index - 1) // 5 * 18))
    layout["dumbbells"][model.name] = {"roles": roles}
    objects += [o for o in collection.objects if o.name.startswith(model.name + "_")]

over = []
for group, budget in (("museums", MUSEUM_BUDGET), ("dumbbells", DUMBBELL_BUDGET)):
    for name, data in layout[group].items():
        total = sum(info["triangles"] for info in data["roles"].values())
        data["triangles"] = total
        print(f"PACK1 {name} parts={len(data['roles'])} triangles={total} budget={budget}")
        if total > budget:
            over.append(name)

models_dir = os.path.join(REPO, "assets", "models")
os.makedirs(models_dir, exist_ok=True)
lego.export_fbx(os.path.join(models_dir, "Pack1.fbx"), objects)
lego.write_json(os.path.join(models_dir, "Pack1.layout.json"), layout)

lego.preview_materials(objects, os.path.join(REPO, "assets", "textures", "lego_studs_color.png"))
lego.setup_render(1000)
for i in range(5):
    name = f"Museum{i + 1}"
    vis = [o for o in objects if o.name.startswith(name + "_")]
    ox = i * 70
    lego.render(os.path.join(PREVIEWS, f"{name}.png"), (ox + 40, 26, -62), (ox, 9, -2), vis, lens=32)
vis = [o for o in objects if o.name.startswith("Museum1_")]
lego.render(os.path.join(PREVIEWS, "Museum1_left.png"), (-44, 30, -50), (0, 6, -4), vis, lens=32)
lego.render(os.path.join(PREVIEWS, "Museum1_top.png"), (10, 70, -40), (0, 0, 2), vis, lens=32)
vis = [o for o in objects if o.name.startswith("Dumbbell")]
lego.render(os.path.join(PREVIEWS, "Dumbbells.png"), (48, 60, 175), (48, 0, 129), vis, lens=32)
print("PACK1_OVER " + (",".join(over) if over else "none"))
print("PACK1_OK")

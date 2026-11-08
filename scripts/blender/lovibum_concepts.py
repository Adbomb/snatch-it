"""Концепты Ловибумов (D55, этап 0): Бум, Турбо и Мега — устройства поимки существ, стиль D39.

Только концепт на утверждение владельца: рендеры, без запекания, FBX и загрузок. Три устройства отличаются силуэтом,
формой и деталями, а не только цветом:
- Бум (бонус ×1) — «кусь-кубик»: куб с крышкой-пастью, зубы по шву, мультяшные глаза, квадратный пупырышек сверху,
  на спине — комикс-взрыв «БУМ»;
- Турбо (×1.5) — «ракета-ловушка»: восьмигранный корпус вдоль броска, нос-челюсть как у крокодила, глаза в
  лётных очках, плавники, сопло с пламенем, молния на боку;
- Мега (×2) — «королевский кристалл»: восьмигранник с золотым ободом-пастью, корона, большая звезда, крылья.
Общее у всех: захват — пасть раскрывается и «кусает» (не шар, без половинок с кнопкой), глаза, номер уровня (1–10) на
табличке. Числа — стады (1 единица Blender = 1 стад), z вверх, лицом в −y, низ на z = 0.

Пишет в папку превью: повороты каждого (спереди, 3/4, сбоку, сзади), крупный кадр, кадр открытой пасти, три рядом,
вид сзади (как в мини-игре поимки), манекены Roblox (5.2 стада) с Ловибумом в руке и крупный план руки, report.json.
Подписи и листы — scripts/d55_lovibum_sheets.py.
Запуск: blender --background --factory-startup --python scripts/blender/lovibum_concepts.py -- <репо> <превью>
Зависит от art_style.py.
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(OUT, exist_ok=True)

LEVEL_DIGIT = ["0110", "1110", "0110", "0110", "0110", "0110", "1111"]  # «1» — номер уровня на табличке


# ── Помощники ────────────────────────────────────────────────────────────────────────────────────────────────


def ngon(cx, cy, r, n=8, phase=None):
    phase = math.pi / n if phase is None else phase
    return [(cx + r * math.cos(phase + 2 * math.pi * i / n), cy + r * math.sin(phase + 2 * math.pi * i / n))
            for i in range(n)]


def hinge(h, deg, axis="X"):
    """Поворот вокруг шарнира h (для открытой пасти)."""
    h = Vector(h)
    return Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h)


def eye(a, c, w, h=None, look=(0.0, 0.0), depth=0.08, sparkle=False):
    """Глаз лицом к −y: белок w × h выступает от грани y = c[1], зрачок со смещением look, блик (у Меги — два)."""
    x, y, z = c
    h = h or w
    a.box("white", x - w / 2, x + w / 2, y - depth, y + 0.02, z - h / 2, z + h / 2)
    pw = min(w, h) * 0.5
    px, pz = x + look[0] * (w - pw) / 2 * 0.8, z + look[1] * (h - pw) / 2 * 0.8
    a.box("dark", px - pw / 2, px + pw / 2, y - depth - 0.025, y - depth + 0.01, pz - pw / 2, pz + pw / 2, bevel=0)
    g = pw * 0.34
    a.box("glint", px - pw / 2 + 0.015, px - pw / 2 + 0.015 + g, y - depth - 0.04, y - depth - 0.02,
          pz + pw / 2 - 0.015 - g, pz + pw / 2 - 0.015, bevel=0)
    if sparkle:
        g2 = g * 0.6
        a.box("glint", px + pw / 2 - 0.02 - g2, px + pw / 2 - 0.02, y - depth - 0.04, y - depth - 0.02,
              pz - pw / 2 + 0.02, pz - pw / 2 + 0.02 + g2, bevel=0)


def plaque(a, plane, at, side, h0, z_top, frame_key, cell=0.045):
    """Табличка с номером уровня: белая плашка, рамка и цифра пикселями на вертикальной грани."""
    w, hgt = cell * (len(LEVEL_DIGIT[0]) + 2), cell * (len(LEVEL_DIGIT) + 2)
    d0, d1 = side * (at - 0.02), side * (at + 0.03)
    f0, f1 = side * (at - 0.02), side * (at + 0.015)
    if plane == "xz":
        a.box(frame_key, h0 - 0.03, h0 + w + 0.03, f0, f1, z_top - hgt - 0.03, z_top + 0.03, bevel=0)
        a.box("white", h0, h0 + w, d0, d1, z_top - hgt, z_top, bevel=0)
    else:
        a.box(frame_key, f0, f1, h0 - 0.03, h0 + w + 0.03, z_top - hgt - 0.03, z_top + 0.03, bevel=0)
        a.box("white", d0, d1, h0, h0 + w, z_top - hgt, z_top, bevel=0)
    flip = (plane == "xz" and side > 0) or (plane == "yz" and side < 0)  # цифра читается снаружи
    a.pixels(LEVEL_DIGIT, {"1": ("digit", 0.025)}, cell, h0 + w - cell if flip else h0 + cell, z_top - cell, plane,
             at + 0.03, sides=(side,), flip=flip)


def sparkle(a, key, c, size, depth=0.04):
    """Блик-«плюс» из трёх брусков (виден с любой стороны), как у предметов коллекций."""
    x, y, z = c
    t = size * 0.28
    a.box(key, x - size / 2, x + size / 2, y - depth, y + depth, z - t / 2, z + t / 2, bevel=0)
    a.box(key, x - t / 2, x + t / 2, y - depth, y + depth, z - size / 2, z - t / 2 - 0.004, bevel=0)
    a.box(key, x - t / 2, x + t / 2, y - depth, y + depth, z + t / 2 + 0.004, z + size / 2, bevel=0)


# ── Бум: «кусь-кубик» ───────────────────────────────────────────────────────────────────────────────────────


def boom(opened=False):
    a = S.Art("Lovibum_Boom" + ("_open" if opened else ""), ring_z0=0.36)
    for key, code, rings in (("body", "FFC21A", True), ("lid", "FF7A1A", True), ("stud", "22C3B4", False),
                             ("studtop", "8AF0E6", False), ("feet", "22C3B4", False), ("base", "2A3344", False),
                             ("mouth", "5A1020", False), ("tongue", "F06A86", False), ("white", "FFFDF4", False),
                             ("dark", "1E1E24", False), ("glint", "FFFFFF", False), ("brow", "B8470A", False),
                             ("blush", "FF8FA3", False), ("burst", "FF3B3B", False), ("burstin", "FFF27A", False),
                             ("spring", "8AF0E6", False), ("pom", "FF3B5C", False), ("digit", "1E3A8A", False),
                             ("frame", "22C3B4", False)):
        a.paint(key, code, rings)
    # Ножки-уголки и тёмное дно.
    for sx in (-1, 1):
        for sy in (-1, 1):
            a.box("feet", sx * 0.4, sx * 0.61, sy * 0.4, sy * 0.61, 0.0, 0.16)
    a.box("base", -0.5, 0.5, -0.5, 0.5, 0.05, 0.13)
    # Корпус (нижняя челюсть) и пасть внутри.
    a.box("body", -0.56, 0.56, -0.56, 0.56, 0.12, 0.62)
    a.box("mouth", -0.52, 0.52, -0.52, 0.52, 0.58, 0.64 if opened else 0.69)
    if opened:
        a.box("tongue", -0.26, 0.26, -0.42, 0.2, 0.6, 0.7)
    # Нижние клыки — по углам рта.
    for sx in (-1, 1):
        a.box("white", sx * 0.4, sx * 0.5, -0.61, -0.53, 0.57, 0.7)
    # Спина: комикс-взрыв «бум» на всю спину корпуса (виден в мини-игре — игрок смотрит Ловибуму в спину).
    burst = ["X....X....X", ".XX..X..XX.", "..XXXXXXX..", ".XXXOOOXXX.", "XXXOOOOOXXX", ".XXXOOOXXX.",
             "..XXXXXXX..", ".XX..X..XX."]
    a.pixels(burst, {"X": ("burst", 0.03), "O": ("burstin", 0.045)}, 0.05, 0.275, 0.575, "xz", 0.56, sides=(1,),
             flip=True)
    # Крышка (верхняя челюсть) — открывается назад вокруг заднего ребра.
    a.transform = hinge((0, 0.58, 0.64), -58) if opened else None
    a.box("lid", -0.6, 0.6, -0.6, 0.6, 0.66, 1.12)
    a.box("mouth", -0.5, 0.5, -0.5, 0.5, 0.645, 0.7)  # нёбо: видно, когда пасть открыта
    a.box("stud", -0.25, 0.25, -0.25, 0.25, 1.1, 1.26)
    a.box("studtop", -0.18, 0.18, -0.18, 0.18, 1.24, 1.3, bevel=0)
    # Пружинка-антенна с помпоном: «бум-бум» при прыжке и полёте.
    a.box("stud", -0.04, 0.04, -0.04, 0.04, 1.28, 1.66)  # стержень внутри витков
    for i in range(5):  # витки пружинки: плоские кольца, через одно сдвинуты
        z0, dx = 1.3 + 0.075 * i, 0.03 if i % 2 else -0.03
        a.box("spring" if i % 2 else "stud", dx - 0.12, dx + 0.12, -0.12, 0.12, z0, z0 + 0.05)
    a.box("pom", -0.14, 0.14, -0.14, 0.14, 1.66, 1.92)
    a.box("glint", -0.11, -0.04, -0.15, -0.13, 1.82, 1.89, bevel=0)
    # Верхние зубы по краю крышки.
    for x in (-0.3, -0.1, 0.1, 0.3):
        a.box("white", x - 0.085, x + 0.085, -0.64, -0.57, 0.55, 0.7)
    # Глаза, румянец рядом с ними и брови: хитрый взгляд, одна бровь выше.
    eye(a, (-0.21, -0.6, 0.9), 0.3, 0.32, look=(0.35, -0.1))
    eye(a, (0.21, -0.6, 0.9), 0.3, 0.32, look=(0.35, -0.1))
    for sx in (-1, 1):
        a.box("blush", sx * 0.48 - 0.07, sx * 0.48 + 0.07, -0.63, -0.58, 0.74, 0.8, bevel=0)
    a.box("brow", -0.36, -0.06, -0.66, -0.6, 1.07, 1.12, bevel=0, matrix=hinge((-0.21, 0, 1.09), -8, "Y"))
    a.box("brow", 0.06, 0.36, -0.66, -0.6, 1.08, 1.13, bevel=0, matrix=hinge((0.21, 0, 1.1), 14, "Y"))
    # Номер уровня — на спине крышки.
    plaque(a, "xz", 0.6, 1, -0.12, 1.06, "frame", cell=0.04)
    a.transform = None
    return a


# ── Турбо: «ракета-ловушка» ─────────────────────────────────────────────────────────────────────────────────


def turbo(opened=False):
    a = S.Art("Lovibum_Turbo" + ("_open" if opened else ""), ring_z0=0.62)
    for key, code, rings in (("body", "2F7BFF", True), ("band", "3FE0FF", False), ("nose", "FF4A4A", True),
                             ("chin", "C42E3A", False), ("strap", "283246", False), ("white", "FFFDF4", False),
                             ("dark", "1E1E24", False), ("glint", "FFFFFF", False), ("rim", "3FE0FF", False),
                             ("fin", "FFC21A", False), ("tip", "FF7A1A", False), ("nozzle", "3A4252", False),
                             ("nozzlein", "1C2230", False), ("flame1", "FFF27A", False), ("flame2", "FFB21E", False),
                             ("flame3", "FF6A2E", False), ("bolt", "FFE14D", False), ("mouth", "5A1020", False),
                             ("tongue", "F06A86", False), ("digit", "1E3A8A", False), ("frame", "FFC21A", False)):
        a.paint(key, code, rings)
    cz, r = 0.62, 0.46
    # Корпус вдоль броска (−y — нос), голубые кольца-полосы.
    a.prism("body", ngon(0, cz, r), -0.36, 0.56, axis="y")
    for y0, y1 in ((0.12, 0.2), (0.34, 0.4)):
        a.prism("band", ngon(0, cz, r + 0.025), y0, y1, axis="y")
    # Нижняя челюсть и пасть.
    a.frustum("chin", (-0.4, 0.4, 0.22, 0.6), (-0.15, 0.15, 0.5, 0.6), -0.34, -0.96, axis="y")
    a.frustum("mouth", (-0.38, 0.38, 0.56, 0.62 if opened else 0.66), (-0.14, 0.14, 0.56, 0.62 if opened else 0.66),
              -0.34, -0.94, axis="y")
    if opened:
        a.box("tongue", -0.16, 0.16, -0.78, -0.38, 0.58, 0.66)
    # Опора спереди — маленький полоз; сзади стоит на двух нижних плавниках.
    a.box("fin", -0.05, 0.05, -0.64, -0.4, 0.04, 0.32)
    a.box("tip", -0.055, 0.055, -0.66, -0.52, 0.02, 0.12)
    # Плавники сзади: верхний и боковые — ступенчатые треугольники, два нижних — ножки.
    a.box("fin", -0.07, 0.07, 0.16, 0.58, 1.0, 1.22)
    a.box("fin", -0.07, 0.07, 0.34, 0.66, 1.2, 1.4)
    a.box("tip", -0.075, 0.075, 0.5, 0.72, 1.38, 1.48)
    for s in (-1, 1):
        a.box("fin", s * 0.38, s * 0.7, 0.16, 0.58, 0.55, 0.69)
        a.box("fin", s * 0.68, s * 0.88, 0.34, 0.66, 0.55, 0.69)
        a.box("tip", s * 0.86, s * 0.96, 0.5, 0.72, 0.545, 0.695)
        a.box("fin", s * 0.26, s * 0.38, 0.16, 0.58, 0.04, 0.3)
        a.box("tip", s * 0.255, s * 0.385, 0.48, 0.66, 0.02, 0.12)
    # Сопло и пламя ступенями (видно игроку в мини-игре).
    a.prism("nozzle", ngon(0, cz, 0.33), 0.54, 0.74, axis="y")
    a.prism("nozzlein", ngon(0, cz, 0.24), 0.73, 0.77, axis="y")
    a.box("flame2", -0.25, 0.25, 0.76, 0.92, cz - 0.25, cz + 0.25)
    a.box("flame1", -0.17, 0.17, 0.78, 1.04, cz - 0.17, cz + 0.17)
    a.box("flame2", -0.12, 0.12, 1.02, 1.18, cz - 0.12, cz + 0.12)
    a.box("flame3", -0.07, 0.07, 1.16, 1.32, cz - 0.07, cz + 0.07)
    # Молния на левом боку, номер уровня на правом.
    bolt = ["..XX", ".XX.", "XXXX", "..XX", ".XX.", ".X.."]
    a.pixels(bolt, {"X": ("bolt", 0.03)}, 0.058, -0.16, 0.79, "yz", 0.425, sides=(-1,), flip=False)
    plaque(a, "yz", 0.425, 1, -0.105, 0.76, "frame", cell=0.03)
    # Красный нос — верхняя челюсть (открывается вверх): зубы по шву с боков и два передних.
    a.transform = hinge((0, -0.34, 0.62), -38) if opened else None
    a.frustum("nose", (-0.42, 0.42, 0.62, 1.02), (-0.16, 0.16, 0.62, 0.76), -0.34, -0.98, axis="y")
    for y in (-0.45, -0.6, -0.75):
        half = 0.42 + (0.16 - 0.42) * (-0.34 - y) / 0.64
        for s in (-1, 1):
            a.box("white", s * (half - 0.07), s * (half + 0.03), y - 0.05, y + 0.05, 0.53, 0.64)
    for x in (-0.07, 0.07):
        a.box("white", x - 0.06, x + 0.06, -1.0, -0.93, 0.5, 0.64)
    # Лётные очки на макушке: ремешок вокруг корпуса, тёмная основа, голубые оправы, глаза, брови «в бой».
    a.prism("strap", ngon(0, cz, r + 0.03), -0.32, -0.2, axis="y")
    for s in (-1, 1):
        a.box("strap", s * 0.05, s * 0.42, -0.335, -0.06, 0.98, 1.3)
        a.box("rim", s * 0.08, s * 0.4, -0.375, -0.3, 1.0, 1.28)
        eye(a, (s * 0.24, -0.375, 1.14), 0.24, 0.24, look=(0.0, 0.1), depth=0.04)
        a.box("strap", s * 0.08, s * 0.4, -0.4, -0.34, 1.28, 1.36, bevel=0,
              matrix=hinge((s * 0.24, 0, 1.32), s * 12, "Y"))
    a.transform = None
    return a


# ── Мега: «королевский кристалл» ────────────────────────────────────────────────────────────────────────────


def mega(opened=False):
    a = S.Art("Lovibum_Mega" + ("_open" if opened else ""), ring_z0=0.35)
    for key, code, rings in (("body", "8E3CFF", True), ("lid", "B070FF", True), ("gold", "F2C230", False),
                             ("golddark", "C98E12", False), ("mouth", "3A0F5A", False), ("crystal", "4FF0FF", False),
                             ("white", "FFFDF4", False), ("dark", "1E1E24", False), ("glint", "FFFFFF", False),
                             ("gemc", "3FE0FF", False), ("gemp", "FF3B7F", False), ("wing", "FFFFFF", False),
                             ("star", "FFD84A", False), ("staredge", "E39A12", False), ("digit", "6B1FB8", False),
                             ("frame", "F2C230", False)):
        a.paint(key, code, rings)
    sq = lambda h, cut: S.octagon(-h, h, -h, h, cut)  # noqa: E731 — квадрат со срезанными углами
    # Золотой цоколь и гранёный низ ступенями (кристалл, а не ярус торта).
    a.prism("golddark", sq(0.44, 0.13), 0.0, 0.12)
    a.prism("body", sq(0.4, 0.12), 0.1, 0.24)
    a.prism("body", sq(0.48, 0.145), 0.22, 0.38)
    a.prism("body", sq(0.56, 0.17), 0.36, 0.6)
    a.prism("mouth", sq(0.52, 0.15), 0.58, 0.62 if opened else 0.7)
    if opened:
        a.box("crystal", -0.14, 0.14, -0.14, 0.14, 0.56, 0.86)
        a.box("crystal", -0.22, 0.22, -0.08, 0.08, 0.64, 0.76)
    # Самоцвет-сердце спереди (ромб пикселями) и камни по бокам ступени.
    gem = ["..X..", ".XXX.", "XXOXX", ".XXX.", "..X.."]
    a.pixels(gem, {"X": ("gemc", 0.03), "O": ("glint", 0.045)}, 0.044, -0.11, 0.585, "xz", 0.56, sides=(-1,))
    for s in (-1, 1):
        a.box("gemp", s * 0.52, s * 0.6, -0.08, 0.08, 0.42, 0.54)
    # Крылья по бокам — перья ступенями, золотой кант сверху, приподняты к концам.
    for s in (-1, 1):
        a.transform = hinge((s * 0.6, 0, 0.7), -s * 14, "Y")
        a.box("gold", s * 0.52, s * 0.72, -0.1, 0.13, 0.5, 0.98)
        for i, (x1, z0, z1) in enumerate(((1.3, 0.88, 1.04), (1.16, 0.72, 0.88), (1.0, 0.56, 0.72),
                                          (0.86, 0.42, 0.56))):
            a.box("wing", s * 0.7, s * x1, -0.06 - 0.01 * i, 0.12 - 0.015 * i, z0, z1 - 0.005)
        a.box("gold", s * 0.72, s * 1.32, -0.075, 0.135, 1.02, 1.08)
    a.transform = None
    # Номер уровня — на спине.
    plaque(a, "xz", 0.56, 1, -0.12, 0.56, "frame", cell=0.04)
    # Блики-звёздочки рядом (не на крышке — не двигаются вместе с ней).
    sparkle(a, "glint", (-0.7, -0.1, 1.72), 0.2)
    sparkle(a, "glint", (0.74, -0.1, 1.5), 0.15)
    # Крышка с золотым ободом-пастью, большими глазами, короной и звездой — открывается назад.
    a.transform = hinge((0, 0.58, 0.64), -48) if opened else None
    a.prism("gold", sq(0.6, 0.18), 0.64, 0.74)
    a.prism("lid", sq(0.57, 0.17), 0.72, 1.08)
    a.prism("mouth", sq(0.53, 0.15), 0.69, 0.75)  # нёбо
    for x in (-0.27, -0.09, 0.09, 0.27):
        a.box("white", x - 0.07, x + 0.07, -0.65, -0.57, 0.54, 0.68)
    eye(a, (-0.2, -0.57, 0.9), 0.3, 0.32, look=(0.0, 0.25), sparkle=True)
    eye(a, (0.2, -0.57, 0.9), 0.3, 0.32, look=(0.0, 0.25), sparkle=True)
    # Корона: обод с камнями, четыре больших зубца ступенями по сторонам и четыре малых на углах.
    a.prism("gold", sq(0.61, 0.18), 1.06, 1.2)
    for x, key in ((-0.3, "gemp"), (0.0, "gemc"), (0.3, "gemp")):
        a.box(key, x - 0.065, x + 0.065, -0.65, -0.6, 1.08, 1.18)
    for ax, ay in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        cx, cy = ax * 0.5, ay * 0.5
        for k, (w, z0, z1) in enumerate(((0.16, 1.18, 1.32), (0.1, 1.3, 1.42), (0.05, 1.4, 1.48))):
            dx, dy = (w, 0.06) if ay else (0.06, w)
            a.box("gold", cx - dx, cx + dx, cy - dy, cy + dy, z0, z1)
    for ax, ay in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        cx, cy = ax * 0.47, ay * 0.47
        a.box("gold", cx - 0.06, cx + 0.06, cy - 0.06, cy + 0.06, 1.18, 1.3)
        a.box("gemp" if ay < 0 else "gemc", cx - 0.045, cx + 0.045, cy - 0.045, cy + 0.045, 1.29, 1.37)
    # Большая звезда над короной (видна издалека и со спины).
    star = ["....X....", "...XXX...", "...XXX...", "XXXXXXXXX", ".XXXXXXX.", "..XXXXX..", "..XXXXX..",
            ".XXX.XXX.", ".XX...XX."]
    a.pixels(star, {"X": ("star", 0.07)}, 0.075, -0.3375, 1.9, "xz", 0.035, sides=(-1,), flip=False)
    a.box("staredge", -0.06, 0.06, -0.035, 0.035, 1.18, 1.36)
    a.transform = None
    return a


# ── Сборка и кадры ──────────────────────────────────────────────────────────────────────────────────────────

MAKERS = (("Boom", boom), ("Turbo", turbo), ("Mega", mega))

bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Lovibums")
bpy.context.scene.collection.children.link(collection)

report, closed, opened = {}, {}, {}
for name, make in MAKERS:
    for state, store in ((False, closed), (True, opened)):
        art = make(state)
        obj = art.build(collection)
        lo, hi = S.bounds(obj)
        if not state:
            report[name] = {**art.stats, "size": [round(hi[i] - lo[i], 2) for i in range(3)]}
        else:
            report[name]["open_coplanar"] = art.stats["coplanar"]
        store[name] = obj
        obj.hide_render = True
print("REPORT " + json.dumps(report, ensure_ascii=False), flush=True)

prev = S.Preview(collection)


def only(objs):
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and o.name != "Floor":
            o.hide_render = o not in objs


# Повороты и крупный кадр каждого (закрытый).
for name, obj in closed.items():
    only([obj])
    S.render_item(prev, obj, OUT)

# Открытая пасть — крупный кадр 3/4.
for name, obj in opened.items():
    only([obj])
    lo, hi = S.bounds(obj)
    size, cz = max(hi - lo), (lo.z + hi.z) / 2
    dist = 2.7 * size + 1.0
    prev.shot(os.path.join(OUT, f"{obj.name}_hero.png"), (-0.62 * dist, -0.85 * dist, cz + 0.55 * size),
              (0, 0, cz - 0.05 * size), 75, (1100, 1100))

# Три рядом: 3/4 спереди и сзади (так Ловибум видит игрок в мини-игре поимки).
xs = {"Boom": -2.5, "Turbo": 0.0, "Mega": 2.7}
turn = {"Boom": -28, "Turbo": -58, "Mega": -22}  # Турбо боком: виден силуэт ракеты
for name, obj in closed.items():
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    lo, hi = S.bounds(obj)
    obj.location.x = xs[name] - (lo.x + hi.x) / 2
    obj.rotation_euler = (0, 0, math.radians(turn[name]))
only(list(closed.values()))
prev.aim_lights(Vector((0, 0, 0)))
prev.shot(os.path.join(OUT, "trio_front.png"), (-2.0, -10.5, 4.2), (0.1, 0, 0.72), 50, (2000, 1000))
for name, obj in closed.items():
    obj.rotation_euler = (0, 0, math.radians(180 + turn[name]))
prev.shot(os.path.join(OUT, "trio_back.png"), (-2.0, -10.5, 4.2), (0.1, 0, 0.72), 50, (2000, 1000))
for obj in closed.values():
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()


def holder(x, turn):
    """Блочный манекен Roblox (рост ≈ 5.2) лицом в −y, правая рука вытянута в сторону ладонью вверх, поворот на turn
    градусов вокруг вертикали; возвращает пустышку-родителя и точку на ладони в его осях."""
    grey = bpy.data.materials.get("Mannequin") or bpy.data.materials.new("Mannequin")
    grey.use_nodes = True
    next(n for n in grey.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (
        *S.lin("8E98AC"), 1)
    root = bpy.data.objects.new("MannequinRoot", None)
    collection.objects.link(root)
    root.location = (x, 0, 0)
    root.rotation_euler = (0, 0, math.radians(turn))
    blocks = (((0, 0, 4.65), (1.15, 1.15, 1.15)), ((0, 0, 3.2), (2.0, 1.0, 1.75)),
              ((1.5, 0, 3.2), (0.95, 0.95, 1.75)), ((-2.15, 0, 3.6), (2.3, 0.95, 0.95)),
              ((-0.5, 0, 1.15), (0.95, 0.95, 2.3)), ((0.5, 0, 1.15), (0.95, 0.95, 2.3)))
    for center, size in blocks:
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.05, segments=2, affect="EDGES")
        bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
        me = bpy.data.meshes.new("Mannequin")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(grey)
        o = bpy.data.objects.new("Mannequin", me)
        collection.objects.link(o)
        o.parent = root
    return root, Vector((-2.85, 0, 4.075))  # ладонь: конец вытянутой руки, верхняя грань


# Масштаб: три манекена, у каждого на ладони вытянутой в сторону руки свой Ловибум.
TURN = -12
roots = {}
for name, x in (("Boom", -6.4), ("Turbo", 1.2), ("Mega", 8.8)):
    root, palm = holder(x, TURN)
    obj = closed[name]
    lo, hi = S.bounds(obj)  # объект в начале координат без поворота (view_layer обновлён выше)
    cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
    obj.parent = root
    if name == "Turbo":  # ракета вдоль руки носом наружу — видна её длина
        obj.rotation_euler = (0, 0, math.radians(-90))
        cx, cy = cy, -cx
    else:
        obj.rotation_euler = (0, 0, 0)
    obj.location = palm - Vector((cx, cy, lo.z))
    roots[name] = (root, palm)
bpy.context.view_layer.update()
only(list(closed.values()) + [o for o in bpy.context.scene.objects if o.name.startswith("Mannequin")])
prev.aim_lights(Vector((0, 0, 0)))
prev.shot(os.path.join(OUT, "hand_scale.png"), (-0.8, -31.0, 7.5), (0.2, 0, 2.9), 50, (2200, 1100))
for name, (root, palm) in roots.items():
    p = root.matrix_world @ palm
    prev.aim_lights(Vector((p.x, 0, 0)))
    prev.shot(os.path.join(OUT, f"hand_{name}.png"), (p.x - 1.6, p.y - 6.2, p.z + 1.5), (p.x + 0.9, p.y, p.z + 0.2),
              50, (900, 900))

with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("LOVIBUMS_OK", flush=True)

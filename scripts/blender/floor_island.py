"""Этаж «Черепаха-остров» музея-небоскрёба (пятая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — тропический пляж с тики-баром. Снаружи — хижина из бамбука под многослойной соломенной крышей
с бахромой, бамбуковые колонны, стойка бара с кокосовыми коктейлями и табуретами, факелы, пальмы с гамаком,
доски для серфинга у стены, полосатый зонт с шезлонгом, кромка песка и волн, ракушки и морские звёзды; бока —
бамбуковые решётки и доски; сзади — каноэ на песке. Внутри — лагуна на закате: стены-небо полосами от
оранжевого к лиловому с горизонтом моря, песчаный пол, бирюзовая вода вокруг островка, пальмы, тики-бар с
кокосами, гирлянды лампочек, гамак, круг-фламинго, морские звёзды; экспонат — на песчаном островке с
пальмочкой посреди лагуны.
Запуск: blender --background --factory-startup --python scripts/blender/floor_island.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab  # noqa: E402

BAMBOO, BAMBOO2, THATCH, THATCH2, THATCH3, WOOD, WOOD2 = "D8B860", "B8984A", "E0B868", "C89A48", "F0CC80", "9A6A3A", "7A4E2A"
SAND, SAND2, WATER, WATER2, FOAM, CORAL, PINK = "F4DEA0", "E4C886", "2AC0D8", "5AE0EC", "F4FCFF", "FF7A5A", "FF8AB8"
SKY = ("FFB04A", "FF8A5A", "F06A7A", "B05AA8", "6A4AA0")
TEAL, RED, YEL, LEAF, LEAF2, COCO = "2AA8A0", "E8483A", "FFD23A", "3FA64A", "2E8A3C", "7A5030"

F = B.Floor("IT", "IslandTurtle", quiet=(SAND, SAND2, THATCH2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def bamboo_post(p, x, z, y0, y1, r=0.35):
    """Бамбуковый ствол с узлами-кольцами."""
    p.prism_xz(K.ngon(x, z, r, 8), y0, y1, BAMBOO)
    y = y0 + 1.2
    while y < y1 - 0.4:
        p.prism_xz(K.ngon(x, z, r * 1.15, 8), y - 0.08, y + 0.08, BAMBOO2)
        y += 1.6


def thatch(p, x0, x1, z_front, z_back, y_eave, y_ridge, layers=3):
    """Соломенная крыша-навес: наклонные слои с бахромой из треугольников по кромке."""
    for k in range(layers):
        t0, t1 = k / layers, (k + 1) / layers
        za, zb = z_front + (z_back - z_front) * t0, z_front + (z_back - z_front) * t1
        ya, yb = y_eave + (y_ridge - y_eave) * t0, y_eave + (y_ridge - y_eave) * t1
        p.loft([(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb)],
               [(x0, ya + 0.45, za), (x1, ya + 0.45, za), (x1, yb + 0.45, zb), (x0, yb + 0.45, zb)], (THATCH, THATCH2, THATCH3)[k % 3])
        n = int((x1 - x0) // 1.0)
        for m in range(n):
            x = x0 + (x1 - x0) * (m + 0.5) / n
            p.prism_xy([(x - 0.5, ya + 0.1), (x + 0.5, ya + 0.1), (x + 0.05 * (m % 3 - 1), ya - 0.7 - 0.25 * (m % 2))], za - 0.06, za + 0.06,
                       (THATCH2, THATCH3)[(m + k) % 2])


def hammock(p, a, b, sag, width, cols):
    """Гамак: сплошное провисающее полотно из полос (соседние полосы стыкуются) и верёвки к опорам."""
    n = 8
    pts = [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n - sag * 4 * (k / n) * (1 - k / n), a[2] + (b[2] - a[2]) * k / n)
           for k in range(n + 1)]
    dx, dz = b[0] - a[0], b[2] - a[2]
    L = math.hypot(dx, dz)
    nx, nz = -dz / L * width / 2, dx / L * width / 2
    for k, (q0, q1) in enumerate(zip(pts[1:-2], pts[2:-1])):
        p.loft([(q0[0] - nx, q0[1], q0[2] - nz), (q1[0] - nx, q1[1], q1[2] - nz), (q1[0] + nx, q1[1], q1[2] + nz), (q0[0] + nx, q0[1], q0[2] + nz)],
               [(q0[0] - nx, q0[1] + 0.12, q0[2] - nz), (q1[0] - nx, q1[1] + 0.12, q1[2] - nz), (q1[0] + nx, q1[1] + 0.12, q1[2] + nz),
                (q0[0] + nx, q0[1] + 0.12, q0[2] + nz)], cols[k % len(cols)])
    for q0, q1 in ((pts[0], pts[1]), (pts[-2], pts[-1])):
        beam(p, q0, q1, 0.08, 0.08, "E8D8B0")


def surfboard(p, x, z, h, col, stripe, lean=0.25):
    """Доска для серфинга, прислонённая к стене (плоская заострённая фигура в плоскости xy)."""
    pts = [(-0.55, 0.0), (0.55, 0.0), (0.7, h * 0.3), (0.6, h * 0.75), (0.0, h), (-0.6, h * 0.75), (-0.7, h * 0.3)]
    p.prism_xy([(x + u + v * lean * 0.1, v) for u, v in pts], z - 0.12, z + 0.12, col)
    sh = lean * 0.1
    p.prism_xy([(x - 0.08 + h * 0.15 * sh, h * 0.15), (x + 0.08 + h * 0.15 * sh, h * 0.15), (x + 0.08 + h * 0.85 * sh, h * 0.85),
                (x - 0.08 + h * 0.85 * sh, h * 0.85)], z - 0.14, z - 0.12, stripe)


def coconut_drink(p, x, z, y):
    """Коктейль в кокосе: половинка ореха, трубочка, зонтик."""
    p.prism_xz(K.ngon(x, z, 0.32, 8), y, y + 0.35, COCO)
    p.prism_xz(K.ngon(x, z, 0.26, 8), y + 0.35, y + 0.38, "F8F0E0")
    beam(p, (x + 0.08, y + 0.35, z), (x + 0.2, y + 0.9, z), 0.06, 0.06, RED)
    p.cone([(x - 0.1 + 0.3 * math.cos(t), y + 0.9, z + 0.3 * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]],
           (x - 0.1, y + 1.05, z), PINK)


def starfish(p, x, z, y, r, col):
    """Морская звезда: плоская пятилучевая фигура."""
    pts = [(x + r * (1.0 if k % 2 == 0 else 0.42) * math.cos(math.pi / 2 + k * math.pi / 5),
            z + r * (1.0 if k % 2 == 0 else 0.42) * math.sin(math.pi / 2 + k * math.pi / 5)) for k in range(10)]
    p.prism_xz(pts, y, y + 0.14, col)


def umbrella(p, x, z, h, r, cols):
    """Пляжный зонт: шест и купол из цветных клиньев."""
    p.prism_xz(K.ngon(x, z, 0.1, 6), 0.0, h, "F4F4F4")
    for k in range(8):
        t0, t1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        p.cone([(x + r * math.cos(t0), h - 0.6, z + r * math.sin(t0)), (x + r * math.cos(t1), h - 0.6, z + r * math.sin(t1)),
                (x, h - 0.6, z)], (x, h + 0.4, z), cols[k % 2])


# ══ ФАСАД: тики-бар на пляже ══════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, BAMBOO, BAMBOO, THATCH2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, SAND)
    slab(FR, axis, fixed, out, 1.2, -half - 0.2, half + 0.2, -0.1, 0.8, WOOD2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 0.8, 13.0, BAMBOO)
    for k in range(int(2 * half // 0.9)):  # бамбуковая обшивка из стволов разной толщины
        a = -half + 0.9 * k + 0.45
        pr = FR.prism_xz
        if axis == "z":
            pr(K.ngon(a, fixed + out * 0.95, 0.4, 6), 0.8, 13.0, (BAMBOO, BAMBOO2)[k % 2])
        else:
            pr(K.ngon(fixed + out * 0.95, a, 0.4, 6), 0.8, 13.0, (BAMBOO, BAMBOO2)[k % 2])
    slab(FR, axis, fixed, out, 1.4, -half, half, 6.4, 6.8, WOOD2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 13.0, 18.9, THATCH2)
    if axis == "x":  # бока: доски для серфинга и бамбуковая решётка
        for k in range(5):
            z = -6.0 + 3.0 * k
            for y in (2.0, 4.5):
                slab(FS, axis, fixed, out, 1.6, z - 1.3, z + 1.3, y, y + 0.25, WOOD2)
# соломенная крыша по периметру с бахромой
thatch(FS, -FX - 2.4, FX + 2.4, -FZ - 3.6, -FZ - 0.9, 12.6, 18.4, layers=5)
for k in range(int(2 * (FX + 2.4) // 1.6)):  # пучки соломы по скату
    x = -FX - 2.0 + 1.6 * k
    FS.loft([(x, 12.9, -FZ - 3.5), (x + 0.5, 12.9, -FZ - 3.5), (x + 0.5, 13.0, -FZ - 3.3), (x, 13.0, -FZ - 3.3)],
            [(x + 0.1, 18.7, -FZ - 1.1), (x + 0.4, 18.7, -FZ - 1.1), (x + 0.4, 18.8, -FZ - 0.9), (x + 0.1, 18.8, -FZ - 0.9)],
            (THATCH3, THATCH2)[k % 2])
for s in (-1, 1):
    FS.loft([(s * (FX + 0.9), 12.6, -FZ - 0.9), (s * (FX + 0.9), 12.6, FZ + 0.9), (s * (FX + 2.6), 12.2, FZ + 0.9),
             (s * (FX + 2.6), 12.2, -FZ - 0.9)],
            [(s * (FX + 0.9), 13.2, -FZ - 0.9), (s * (FX + 0.9), 13.2, FZ + 0.9), (s * (FX + 2.6), 12.8, FZ + 0.9),
             (s * (FX + 2.6), 12.8, -FZ - 0.9)], THATCH)
# бамбуковые колонны, стойка бара, табуреты, коктейли
for x in (-16.0, -6.0, 6.0, 16.0):
    bamboo_post(FS, x, -FZ - 3.2, 0.0, 12.8, 0.45)
FS.box(-5.0, 5.0, 0.8, 3.6, -FZ - 2.6, -FZ - 0.88, WOOD)
FS.box(-5.3, 5.3, 3.6, 3.9, -FZ - 2.9, -FZ - 0.88, WOOD2)
for k in range(7):
    FS.prism_xz(K.ngon(-4.4 + 1.47 * k, -FZ - 2.66, 0.2, 6), 0.8, 3.6, BAMBOO2)
for k in range(4):
    coconut_drink(FS, -3.6 + 2.4 * k, -FZ - 2.2, 3.9)
for x in (-3.6, 0.0, 3.6):
    FS.prism_xz(K.ngon(x, -FZ - 4.0, 0.15, 6), 0.0, 2.2, BAMBOO2)
    FS.prism_xz(K.ngon(x, -FZ - 4.0, 0.7, 8), 2.2, 2.5, RED)
FG.box(-4.4, 4.4, 4.4, 10.6, -FZ - 0.94, -FZ - 0.9, "FFD890")
FS.frame_xy(K.rect(-4.8, 4.8, 4.0, 11.0), K.rect(-4.4, 4.4, 4.4, 10.6), -FZ - 1.3, -FZ - 0.88, WOOD2)
pts = D.chain(FS, (-FX, 12.0, -FZ - 3.4), (FX, 12.0, -FZ - 3.4), 12, 0.05, "3A3A30", 1.2)
for k, q in enumerate(pts[1:-1]):
    FG.prism_xz(K.octa(q[0], q[2], 0.18, 0.18, 0.07), q[1] - 0.45, q[1] - 0.05, (YEL, PINK, "7AF0FF")[k % 3])
# факелы, пальмы с гамаком, доски для серфинга, зонт с шезлонгом
for x in (-8.6, 8.6):
    D.torch(FS, FG, x, 0.0, -FZ - 4.6, 3.6, BAMBOO2)
D.palm(FS, (-14.0, 0.0, -FZ - 5.4), (1.4, -0.4), 11.0)
D.palm(FS, (-6.6, 0.0, -FZ - 6.4), (-0.8, -0.5), 9.0)
hammock(FS, (-13.2, 5.0, -FZ - 5.6), (-7.2, 5.0, -FZ - 6.4), 1.6, 1.4, (RED, YEL, TEAL))
for k, x in enumerate((10.6, 12.0, 13.4)):
    surfboard(FS, x, -FZ - 1.4, 7.0 + 0.6 * (k % 2), (TEAL, RED, YEL)[k], "F4F4F4", lean=0.4)
umbrella(FS, 15.2, -FZ - 4.8, 5.0, 2.4, (RED, "F4F4F4"))
FS.box(12.6, 17.4, 0.4, 0.7, -FZ - 6.8, -FZ - 5.8, TEAL)
FS.loft([(12.6, 0.7, -FZ - 6.8), (13.6, 0.7, -FZ - 6.8), (13.6, 0.7, -FZ - 5.8), (12.6, 0.7, -FZ - 5.8)],
        [(12.0, 2.4, -FZ - 6.8), (13.0, 2.4, -FZ - 6.8), (13.0, 2.4, -FZ - 5.8), (12.0, 2.4, -FZ - 5.8)], TEAL)
# песчаный пляж перед фасадом до кромки волн (продолжение земли этажа), кромка волн и ракушки
FQ.box(-FX - 2.88, FX + 2.88, -1.0, -0.1, -FZ - 6.9, -FZ - 2.88, SAND)
for k in range(9):
    x = -FX - 2.6 + 4.6 * k
    FG.prism_xz([(x, -FZ - 7.0), (x + 4.6, -FZ - 7.0), (x + 4.6, -FZ - 7.3), (x + 2.3, -FZ - 7.6), (x, -FZ - 7.3)], -0.6, -0.15, WATER)
    FS.prism_xz([(x, -FZ - 6.8), (x + 2.3, -FZ - 7.1), (x + 4.6, -FZ - 6.8), (x + 4.6, -FZ - 7.0), (x, -FZ - 7.0)], -0.6, -0.1, FOAM)
for k, (x, z) in enumerate(((-2.0, -FZ - 5.4), (3.6, -FZ - 5.0), (6.0, -FZ - 6.0), (-10.0, -FZ - 4.4))):
    starfish(FS, x, z, -0.1, 0.6, (CORAL, PINK, YEL, CORAL)[k])
# тыл: каноэ на песке
FS.loft([(-8.0, 0.0, FZ + 2.4), (0.0, 0.0, FZ + 2.4), (0.0, 0.0, FZ + 3.0), (-8.0, 0.0, FZ + 3.0)],
        [(-9.0, 1.2, FZ + 1.8), (1.0, 1.2, FZ + 1.8), (1.0, 1.2, FZ + 3.6), (-9.0, 1.2, FZ + 3.6)], RED)
beam(FS, (-6.0, 1.3, FZ + 2.7), (-1.0, 2.0, FZ + 3.4), 0.15, 0.15, WOOD2)

# ══ ИНТЕРЬЕР: лагуна на закате ════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), SAND)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.2, BAMBOO2)
        for k, (y0, y1) in enumerate(((1.2, 3.0), (3.0, 4.0), (4.0, 6.4), (6.4, 9.6), (9.6, 13.2), (13.2, C))):  # море и небо полосами
            if gap and y0 >= DOOR[1]:
                break
            col = (TEAL, WATER2, SKY[0], SKY[1], SKY[2], SKY[3])[k]
            slab(IR, axis, fixed, out, 0.88, a0, a1, y0, min(y1, DOOR[1] + 0.1) if gap else y1, col)
    if gap:
        for k, (y0, y1) in enumerate(((DOOR[1] + 0.1, 13.2), (13.2, C))):
            slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, y0, y1, SKY[2 + k])
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, BAMBOO2)
    else:  # солнце садится в море, далёкие островки
        pr = IS.prism_xy if axis == "z" else IS.prism_zy
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.96))
        if idx == 2:
            IG.prism_xy([(3.0 * math.cos(math.pi * k / 10), 4.0 + 3.0 * math.sin(math.pi * k / 10)) for k in range(11)], d0, d1, "FFE08A")
        for k, a in enumerate((-10.0, 9.0) if idx != 2 else (-11.0, 12.0)):
            pr([(a - 3.0, 4.0), (a + 3.0, 4.0), (a + 1.4, 5.2), (a - 0.6, 5.6)], *sorted((fixed + out * 0.96, fixed + out * 1.02)), "3A6A4A")
            pr([(a - 0.2, 5.4), (a + 0.1, 5.4), (a + 0.4, 7.2), (a + 0.1, 7.2)], *sorted((fixed + out * 0.96, fixed + out * 1.02)), COCO)
            pr([(a + 0.3, 7.2), (a + 1.8, 6.6), (a + 0.4, 7.0), (a - 1.2, 6.6)], *sorted((fixed + out * 0.96, fixed + out * 1.02)), LEAF2)
# лагуна вокруг островка, пальмы, тики-бар, гирлянды, гамак, круг-фламинго, морские звёзды
lag = [(1.8 * 4.6 * math.cos(2 * math.pi * k / 20) * (1.0 + 0.1 * math.sin(3 * k)), -3.0 + 4.6 * 1.6 * math.sin(2 * math.pi * k / 20))
       for k in range(20)]
IG.prism_xz(lag, 0.02, 0.12, WATER)
IQ.frame_xz([(x * 1.08, -3.0 + (z + 3.0) * 1.08) for x, z in lag], lag, 0.02, 0.1, SAND2)
for k, (x, z, lx, lz, h) in enumerate(((-13.6, -12.4, 1.4, 0.8, 11.0), (13.4, -12.0, -1.2, 0.8, 12.0), (-13.4, 5.0, 1.0, -0.4, 10.0),
                                       (13.2, 4.0, -1.2, -0.6, 9.0))):
    D.palm(IS, (x, 0.0, z), (lx, lz), h)
IR.box(-12.0, -4.0, 0.0, 3.2, ZF + 2.0, ZF + 4.0, BAMBOO2)
IS.box(-12.3, -3.7, 3.2, 3.5, ZF + 1.8, ZF + 4.2, WOOD)
for k in range(9):
    IS.prism_xz(K.ngon(-11.6 + 0.95 * k, ZF + 4.1, 0.2, 6), 0.0, 3.2, BAMBOO)
for k in range(4):
    coconut_drink(IS, -11.0 + 2.0 * k, ZF + 3.0, 3.5)
for k in range(3):
    x = -6.0 + 6.0 * k
    pts = D.chain(IS, (x, 15.6, ZF + 1.0), (x, 15.6, ZB - 2.0), 10, 0.05, "3A3A30", 1.6)
    for m, q in enumerate(pts[1:-1]):
        IG.prism_xz(K.octa(q[0], q[2], 0.2, 0.2, 0.08), q[1] - 0.5, q[1] - 0.05, (YEL, PINK, "7AF0FF")[(m + k) % 3])
hammock(IS, (13.3, 5.6, -11.4), (13.3, 5.6, 3.4), 2.0, 1.6, (RED, YEL, TEAL))  # гамак между пальмами справа
ring_y(IS, 6.4, 1.6, 0.9, 1.6, 0.12, 0.6, PINK, n=12)  # круг-фламинго плавает в лагуне
beam(IS, (6.4, 0.5, 0.2), (6.6, 2.4, 0.0), 0.4, 0.4, PINK)
IS.box(6.3, 7.1, 2.4, 2.7, -0.2, 0.2, "FFB04A")
for k, (x, z) in enumerate(((-5.6, 3.6), (6.0, -9.0), (-7.0, -9.6), (4.6, 2.4))):
    starfish(IS, x, z, 0.02, 0.55, (CORAL, PINK, YEL, CORAL)[k])
# постамент — песчаный островок с пальмочкой посреди лагуны
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.2, 14), 0.0, 0.5, SAND2)
IR.prism_xz(K.ngon(px, pz, 3.5, 14), 0.5, TOP, SAND)
D.palm(IS, (px - 3.0, TOP - 0.1, pz - 2.0), (-0.8, -0.6), 5.4)
for k in range(5):
    t = 2 * math.pi * (k + 0.4) / 5
    IS.prism_xz(K.octa(px + 3.9 * math.cos(t), pz + 3.9 * math.sin(t), 0.3, 0.26, 0.1), 0.4, 0.62, ("F8E0D0", "FFC8B0")[k % 2])
B.lift_leaves(IS, WOOD2, YEL)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 13.0, -FZ, FZ, BAMBOO)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, SAND)
SL.box(-FX, FX, 13.0, 18.9, -FZ, FZ, THATCH2)
SL.loft([(-FX - 2.4, 12.6, -FZ - 3.6), (FX + 2.4, 12.6, -FZ - 3.6), (FX + 2.4, 12.6, -FZ - 0.9), (-FX - 2.4, 12.6, -FZ - 0.9)],
        [(-FX - 2.4, 13.4, -FZ - 3.6), (FX + 2.4, 13.4, -FZ - 3.6), (FX + 2.4, 18.4, -FZ - 0.9), (-FX - 2.4, 18.4, -FZ - 0.9)], THATCH)
SL.prism_xz(K.ngon(-14.0, -FZ - 6.6, 2.6, 6), 9.0, 11.6, LEAF)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2800, (1.0, 0.85, 0.7)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.95, 0.85)),
                                                   ("Sunset", (0, 6, -12), 1100, (1.0, 0.6, 0.4))])

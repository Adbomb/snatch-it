"""Этаж «Змейка-соломинка» музея-небоскрёба (восьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — кафе-мороженое и молочных коктейлей. Снаружи — розово-мятный домик с волнистым карнизом-«глазурью»,
с которого стекают капли, над навесом — вывески: гигантский рожок с тремя шариками и огромный стакан коктейля с
полосатой трубочкой; по фасаду — полосатый навес, окно выдачи с прилавком, круглые столики с зонтиками и стульями,
тележка мороженщика, вывеска-леденец; на боках — окна в форме вафельных квадратов. Внутри — зал кафе: пол в
розово-белую клетку, длинная витрина-холодильник с лотками разноцветного мороженого, автомат коктейлей, табуреты у
стойки, столики, полки с баночками посыпки, под потолком — гирлянда из шариков; экспонат — на круглом «торте»-
тумбе в три яруса с глазурью и вишенками.
Запуск: blender --background --factory-startup --python scripts/blender/floor_icecream.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab, taper  # noqa: E402

PINK, PINK2, MINT, MINT2, CREAM, WAFER = "F4A6C0", "E07898", "9EE4CC", "6CC8AC", "FFF4E4", "D8A058"
WAFER2, CHOCO, CHERRY, WHITE, STRAW, GLASS = "B07C3A", "6A3E26", "D82A3A", "F8F6F2", "E8343A", "FFF0D8"
SCOOPS = ("F4A6C0", "9EE4CC", "FFF0B0", "8A5A3A", "C8A0F0", "F0C878")
SPRINKLE = ("E8343A", "2EA8E0", "F0C820", "4AB04A", "B070F0")

F = B.Floor("IC", "StrawSnake", quiet=(PINK2, "E8D8DC", WHITE), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def scoop(p, x, y, z, r, col):
    """Шарик мороженого: гранёный шар из трёх ярусов с волнистой юбкой."""
    p.prism_xz(K.ngon(x, z, r * 1.05, 10), y, y + r * 0.35, col)
    p.prism_xz(K.ngon(x, z, r, 10), y + r * 0.35, y + r * 1.1, col)
    p.prism_xz(K.ngon(x, z, r * 0.7, 10), y + r * 1.1, y + r * 1.55, col)


def cone(p, x, z, y, h, r):
    """Вафельный рожок остриём вниз с поясками-клеткой."""
    p.cone([(xx, y + h, zz) for xx, zz in K.ngon(x, z, r, 10)], (x, y, z), WAFER)
    for k in range(3):
        t = 0.35 + 0.22 * k
        p.prism_xz(K.ngon(x, z, r * t + 0.04, 10), y + h * t - 0.05, y + h * t + 0.05, WAFER2)


def glass_shake(p, g, x, z, y, h, r, col):
    """Стакан коктейля: стекло, напиток, шапка сливок, вишня, полосатая трубочка."""
    p.prism_xz(K.ngon(x, z, r * 0.7, 10), y, y + 0.2, WHITE)
    g.loft([(x + r * 0.7 * math.cos(a), y + 0.2, z + r * 0.7 * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(10)]],
           [(x + r * math.cos(a), y + h, z + r * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(10)]], col)
    p.prism_xz(K.ngon(x, z, r * 1.05, 10), y + h, y + h + 0.25 * r, WHITE)
    p.prism_xz(K.ngon(x, z, r * 0.75, 10), y + h + 0.25 * r, y + h + 0.6 * r, WHITE)
    p.prism_xz(K.octa(x, z, 0.3 * r, 0.3 * r, 0.1 * r), y + h + 0.6 * r, y + h + 0.95 * r, CHERRY)
    n = 6
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        a = (x + r * 0.4 + 0.2 * r * t0, y + h * 0.5 + h * 0.9 * t0, z)
        b = (x + r * 0.4 + 0.2 * r * t1, y + h * 0.5 + h * 0.9 * t1, z)
        beam(p, a, b, 0.22 * r, 0.22 * r, STRAW if k % 2 == 0 else WHITE)


def table(p, x, z, y=0.0, umbrella=None):
    """Круглый столик кафе; с зонтиком, если задан цвет."""
    p.prism_xz(K.ngon(x, z, 0.5, 8), y, y + 0.15, "C8C8CC")
    p.prism_xz(K.ngon(x, z, 0.12, 6), y + 0.15, y + 2.2, "C8C8CC")
    p.prism_xz(K.ngon(x, z, 1.1, 12), y + 2.2, y + 2.35, WHITE)
    if umbrella:
        p.prism_xz(K.ngon(x, z, 0.08, 6), y + 2.35, y + 5.0, WHITE)
        for k in range(8):
            a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
            p.loft([(x + 0.1 * math.cos(a0), y + 5.4, z + 0.1 * math.sin(a0)), (x + 0.1 * math.cos(a1), y + 5.4, z + 0.1 * math.sin(a1)),
                    (x + 0.1 * math.cos(a1), y + 5.45, z + 0.1 * math.sin(a1)), (x + 0.1 * math.cos(a0), y + 5.45, z + 0.1 * math.sin(a0))],
                   [(x + 2.0 * math.cos(a0), y + 4.4, z + 2.0 * math.sin(a0)), (x + 2.0 * math.cos(a1), y + 4.4, z + 2.0 * math.sin(a1)),
                    (x + 2.0 * math.cos(a1), y + 4.5, z + 2.0 * math.sin(a1)), (x + 2.0 * math.cos(a0), y + 4.5, z + 2.0 * math.sin(a0))],
                   umbrella if k % 2 else WHITE)


def chair(p, x, z, y=0.0, col=PINK2):
    p.prism_xz(K.ngon(x, z, 0.5, 8), y + 1.2, y + 1.4, col)
    p.prism_xz(K.ngon(x, z, 0.08, 6), y, y + 1.2, "C8C8CC")
    p.prism_xz(K.ngon(x, z, 0.35, 8), y, y + 0.08, "C8C8CC")


# ══ ФАСАД: кафе-мороженое ═════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, PINK, PINK, CHOCO)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "E8D8DC")
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, -0.1, 1.4, MINT2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.4, 15.4, PINK)
    for k in range(int(2 * half // 2.4)):  # вертикальные мятные полосы
        a = -half + 1.2 + 2.4 * k
        if k % 2 == 0:
            slab(FR, axis, fixed, out, 0.98, a - 0.6, a + 0.6, 1.4, 15.4, MINT)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 15.4, 16.4, CREAM)
    for k in range(int(2 * half // 1.6) + 1):  # волнистая глазурь с каплями
        a = -half - 0.3 + 1.6 * k
        L = 0.6 + 1.0 * rng(fi, k)
        lo, hi = sorted((fixed + out * 1.38, fixed + out * 1.5))
        pts = [(a, 15.4), (a + 1.6, 15.4), (a + 1.4, 15.4 - 0.4), (a + 0.9, 15.4 - L), (a + 0.6, 15.4 - L - 0.2), (a + 0.3, 15.4 - 0.4)]
        (FS.prism_xy if axis == "z" else FS.prism_zy)(pts, lo, hi, CREAM)
    slab(FR, axis, fixed, out, 1.18, -half - 0.1, half + 0.1, 16.4, 18.9, PINK2)
    for k in range(int(2 * half // 1.2)):  # посыпка на парапете
        a = -half + 0.6 + 1.2 * k
        y = 16.9 + 1.4 * rng(k, fi)
        slab(FS, axis, fixed, out, 1.26, a, a + 0.5, y, y + 0.16, SPRINKLE[k % 5])
    if fi > 0:  # бока и тыл: вафельные окна
        for a in (-10.0, -2.0, 6.0):
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
            pr = FG.prism_zy if axis == "x" else FG.prism_xy
            pr(K.rect(a, a + 3.0, 5.0, 11.0), d0, d1, GLASS)
            for i in range(4):
                slab(FS, axis, fixed, out, 1.05, a - 0.1 + 1.0 * i, a + 0.1 + 1.0 * i, 4.9, 11.1, WAFER)
            for j in range(4):
                slab(FS, axis, fixed, out, 1.05, a - 0.1, a + 3.1, 4.9 + 2.0 * j, 5.1 + 2.0 * j, WAFER)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# окно выдачи с прилавком и полосатый навес, дверь
FS.box(-14.8, -4.6, 1.4, 8.0, -FZ - 0.96, -FZ - 0.88, CHOCO)
FG.box(-14.4, -5.0, 4.0, 7.6, -FZ - 1.0, -FZ - 0.96, GLASS)
FS.box(-15.0, -4.4, 3.6, 4.0, -FZ - 2.2, -FZ - 0.88, WHITE)
FS.box(-14.8, -4.6, 1.4, 3.6, -FZ - 1.6, -FZ - 0.96, MINT2)
F.objects(True)
for k, x in enumerate((-13.0, -10.4, -7.8)):
    cone(FS, x, -FZ - 1.6, 4.0, 1.2, 0.4)
    scoop(FS, x, 5.15, -FZ - 1.6, 0.42, SCOOPS[k])
F.objects(False)
for k in range(10):
    x0 = -15.4 + 1.1 * k
    FS.loft([(x0, 9.2, -FZ - 0.9), (x0 + 1.1, 9.2, -FZ - 0.9), (x0 + 1.1, 9.35, -FZ - 0.9), (x0, 9.35, -FZ - 0.9)],
            [(x0, 8.2, -FZ - 2.8), (x0 + 1.1, 8.2, -FZ - 2.8), (x0 + 1.1, 8.35, -FZ - 2.8), (x0, 8.35, -FZ - 2.8)], PINK2 if k % 2 else WHITE)
FS.box(-0.6, 4.0, 1.4, 8.4, -FZ - 0.96, -FZ - 0.88, CHOCO)
FS.box(-0.2, 3.6, 1.4, 8.0, -FZ - 1.06, -FZ - 0.96, MINT2)
FG.prism_xy([(0.4, 5.2), (3.0, 5.2), (3.0, 6.8), (1.7, 7.6), (0.4, 6.8)], -FZ - 1.1, -FZ - 1.06, GLASS)
# вывеска-леденец над дверью
F.objects(True)
FS.box(1.65, 1.75, 8.4, 10.4, -FZ - 1.3, -FZ - 1.2, WHITE)
for k in range(12):
    a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
    FS.prism_xy([(1.7, 12.2), (1.7 + 1.6 * math.cos(a0), 12.2 + 1.6 * math.sin(a0)), (1.7 + 1.6 * math.cos(a1), 12.2 + 1.6 * math.sin(a1))],
                -FZ - 1.4, -FZ - 1.2, STRAW if k % 2 else WHITE)
F.objects(False)
# столики с зонтиками, тележка мороженщика
F.objects(True)
for x, col in ((8.4, PINK2), (14.2, MINT2)):
    table(FS, x, -FZ - 1.9, y=-0.1, umbrella=col)
    for e in (-1, 1):
        chair(FS, x + e * 1.6, -FZ - 1.9, y=-0.1, col=(PINK2, MINT2)[(e + 1) // 2])
CX = -17.0
FS.box(CX - 1.2, CX + 1.6, 1.0, 3.2, -FZ - 2.6, -FZ - 1.1, WHITE)
FS.box(CX - 1.3, CX + 1.7, 3.2, 3.4, -FZ - 2.7, -FZ - 1.0, PINK2)
for e in (-1, 1):
    FS.prism_xy(K.ngon(CX + e * 0.8, 0.6, 0.6, 10), -FZ - 2.75, -FZ - 2.6, CHOCO)
for k in range(3):
    scoop(FS, CX - 0.6 + 0.8 * k, 3.4, -FZ - 1.85, 0.3, SCOOPS[k + 2])
F.objects(False)
# над навесом — вывески: гигантский рожок с тремя шариками и стакан коктейля на кронштейне
F.objects(True)
cone(FS, -9.6, -FZ - 2.0, 9.8, 3.6, 1.3)
for k, (dx, dy) in enumerate(((-0.6, 0.0), (0.6, 0.0), (0.0, 1.0))):
    scoop(FS, -9.6 + dx, 13.3 + dy, -FZ - 2.0, 0.9, SCOOPS[k])
FS.box(-10.0, -9.2, 10.0, 10.4, -FZ - 2.0, -FZ - 0.88, CHOCO)
FS.box(9.6, 13.2, 9.8, 10.1, -FZ - 2.6, -FZ - 0.88, WHITE)
for x in (10.0, 12.8):
    beam(FS, (x, 9.8, -FZ - 2.4), (x, 8.6, -FZ - 0.9), 0.15, 0.15, "C8C8CC")
glass_shake(FS, FG, 11.4, -FZ - 1.8, 10.1, 3.8, 1.2, SCOOPS[0])
F.objects(False)

# ══ ИНТЕРЬЕР: зал кафе ════════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), WHITE)
for i in range(-7, 7):
    for j in range(-7, 7):
        if (i + j) % 2 == 0:
            x, z = 2.4 * i, 2.4 * j
            if -W + 0.2 < x and x + 2.4 < W - 0.2 and ZF + 0.2 < z and z + 2.4 < ZB - 0.2:
                IQ.box(x, x + 2.4, 0.02, 0.04, z, z + 2.4, PINK)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, MINT)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 3.0, PINK2)
        slab(IS, axis, fixed, out, 1.05, a0, a1, 3.0, 3.3, CREAM)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, MINT)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, PINK2)
    slab(IR, axis, fixed, out, 1.3, -half, half, 15.6, 16.4, CREAM)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.5, C - 0.2, 4.4 * k - 0.2, 4.4 * k + 0.2, PINK2)
# витрина-холодильник с лотками мороженого у дальней стены, автомат коктейлей
F.objects(True)
VZ = ZF + 3.4
IS.box(-11.0, 11.0, 0.0, 3.2, VZ - 1.2, VZ + 1.2, WHITE)
IS.box(-11.0, 11.0, 0.0, 0.4, VZ + 1.0, VZ + 1.3, MINT2)
for k in range(10):
    x = -10.0 + 2.2 * k
    IS.box(x - 0.9, x + 0.9, 3.2, 3.5, VZ - 0.9, VZ + 0.9, "C8C8CC")
    scoop(IS, x - 0.3, 3.3, VZ - 0.2, 0.55, SCOOPS[k % 6])
    scoop(IS, x + 0.4, 3.3, VZ + 0.3, 0.45, SCOOPS[(k + 2) % 6])
IG.box(-11.0, 11.0, 4.8, 4.86, VZ - 1.3, VZ + 1.3, "D8F0F8")
for x in (-11.0, 11.0):
    IS.box(x - 0.08, x + 0.08, 3.2, 4.8, VZ - 1.2, VZ + 1.2, "C8C8CC")
MX = 13.4
IS.box(MX - 1.4, MX + 1.4, 0.0, 6.0, ZF + 1.0, ZF + 3.4, PINK2)
IG.box(MX - 1.0, MX + 1.0, 3.6, 5.4, ZF + 3.4, ZF + 3.44, "F8E0F0")
for k in range(3):
    glass_shake(IS, IG, MX - 0.8 + 0.8 * k, ZF + 3.9, 2.2, 1.0, 0.3, SCOOPS[k])
IS.box(MX - 1.4, MX + 1.4, 2.0, 2.2, ZF + 3.4, ZF + 4.4, WHITE)
F.objects(False)
# стойка с табуретами вдоль левой стены, столики, полки с посыпкой
F.objects(True)
BXc = -W + 2.2
IS.box(BXc - 0.8, BXc + 0.8, 0.0, 2.8, -10.0, 4.0, PINK2)
IS.box(BXc - 1.0, BXc + 1.0, 2.8, 3.0, -10.2, 4.2, CREAM)
for k in range(5):
    chair(IS, BXc + 2.0, -8.6 + 3.0 * k, col=(MINT2, PINK2)[k % 2])
for x, z in ((9.6, -3.0), (9.6, 3.6)):
    table(IS, x, z)
    for e in (-1, 1):
        chair(IS, x + e * 1.6, z, col=(PINK2, MINT2)[(e + 1) // 2])
x = W - 0.88
for y in (7.0, 9.2):
    IS.box(x - 1.0, x, y, y + 0.15, -9.0, -1.0, WAFER)
    for k in range(6):
        IS.prism_xz(K.ngon(x - 0.5, -8.4 + 1.3 * k, 0.3, 8), y + 0.15, y + 0.9, WHITE)
        IS.prism_xz(K.ngon(x - 0.5, -8.4 + 1.3 * k, 0.32, 8), y + 0.5, y + 0.75, SPRINKLE[k % 5])
F.objects(False)
for k in range(6):  # гирлянда шариков под потолком
    z = -12.0 + 3.8 * k
    if z > 7.0:
        continue
    pts = D.chain(IS, (-W + 1.0, C - 1.2, z), (W - 1.0, C - 1.2, z), 8, 0.06, "C8C8CC", sag=1.6)
    for j, (xx, yy, zz) in enumerate(pts[1:-1]):
        IS.prism_xz(K.octa(xx, zz, 0.32, 0.32, 0.12), yy - 0.7, yy - 0.05, SCOOPS[(j + k) % 6])
# постамент: «торт» в три яруса с глазурью и вишенками
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.5, CHOCO)
IS.prism_xz(K.ngon(px, pz, 3.7, 16), 0.5, 1.0, PINK)
IS.prism_xz(K.ngon(px, pz, 3.8, 16), 1.0, TOP - 0.1, CREAM)
IS.prism_xz(K.ngon(px, pz, 3.6, 16), TOP - 0.1, TOP, WHITE)
for k in range(16):
    a = 2 * math.pi * (k + 0.5) / 16
    x, z = px + 3.82 * math.cos(a), pz + 3.82 * math.sin(a)
    IS.prism_xz(K.ngon(x, z, 0.2, 6), 0.6 + 0.2 * (k % 2), 1.0, CREAM)
for k in range(6):
    a = 2 * math.pi * k / 6 + 0.3
    IS.prism_xz(K.octa(px + 3.4 * math.cos(a), pz + 3.4 * math.sin(a), 0.22, 0.22, 0.08), TOP, TOP + 0.4, CHERRY)
B.lift_leaves(IS, PINK2, CREAM)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, PINK)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "E8D8DC")
SL.box(-FX - 0.4, FX + 0.4, 15.4, 16.4, -FZ - 0.4, FZ + 0.4, CREAM)

F.build(exhibit=(PED[0], TOP, PED[1], 3.0), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.96, 0.96)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Case", (0, 7, ZF + 6), 600, (1.0, 0.95, 1.0))])

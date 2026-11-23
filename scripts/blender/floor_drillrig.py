"""Этаж «Песчаный червь-бурильщик» музея-небоскрёба (седьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — буровая в пустыне. Снаружи — гофрированные стальные стены (оранжевые внизу, серые наверху) с
жёлто-чёрными полосами; у левого переднего угла — решётчатая вышка буровой до крыши с площадкой и талевым блоком,
у правого — станок-качалка с балансиром и противовесами; вдоль фасада — трубы на опорах с вентилями, на земле —
песчаные барханы, бочки и огромное буровое долото на подставке; в центре — ворота ангара с полосой окон под
навесом, на боках — ленты окон и трубы. Внутри — буровой зал: стальной настил с
решётками, у дальней стены — разрез земли слоями (песок, охра, глина, камень) с норами червя и пробитой дырой,
перед ним — ротор с бурильной трубой, уходящей в пол; стеллажи с трубами, ящики с кернами (цветные слои),
кабина оператора с экранами, кран-балка с крюком под потолком, предупреждающие полосы; экспонат — на стальной
площадке с жёлто-чёрной каймой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_drillrig.py -- <репо> <превью>
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

SAND, SAND2, RUST, ORANGE, ORANGE2 = "E0B878", "C89A5A", "B85A2A", "E8822A", "C86A1E"
STEEL, STEEL2, STEEL3, YEL, BLACK, OIL = "8A949E", "6A747E", "4A525A", "F0C020", "2A2A2E", "2A2224"
# нижние пласты — холодный сланец: оранжевый червь читается на них, а не тонет в рыжей глине
STRATA = ("E0B878", "C89A5A", "7A7468", "5E6268", "4A5058", "3A3E46")
GLASS = "BFD8EA"

F = B.Floor("OR", "DrillWorm", quiet=(SAND, SAND2, STEEL3), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def hazard(p, axis, fixed, out, a0, a1, y0, y1, depth=0.06, step=1.0):
    """Жёлто-чёрная полоса из наклонных параллелограммов."""
    n = int((a1 - a0) / step)
    lo, hi = sorted((fixed, fixed + out * depth))
    for k in range(n):
        a = a0 + step * k
        pts = [(a, y0), (a + step * 0.5, y0), (a + step * 0.5 + (y1 - y0) * 0.6, y1), (a + (y1 - y0) * 0.6, y1)]
        pts = [(min(max(x, a0), a1), y) for x, y in pts]
        (p.prism_xy if axis == "z" else p.prism_zy)(pts, lo, hi, YEL if k % 2 == 0 else BLACK)


def pipe_x(p, x0, x1, y, z, r, col):
    """Труба вдоль x (сечение — восьмиугольник)."""
    p.prism_zy(K.ngon(z, y, r, 8), x0, x1, col)


def valve(p, x, y, z, col="D83A2A"):
    """Вентиль-штурвал на трубе (сверху)."""
    p.prism_xz(K.ngon(x, z, 0.12, 6), y, y + 0.6, STEEL3)
    ring_y(p, x, z, 0.35, 0.5, y + 0.6, y + 0.72, col, n=8)


def barrel(p, x, z, y=0.0, col=RUST):
    D.barrel(p, x, z, y=y, r=0.7, h=1.6, wood=col, hoop=STEEL3)


def drill_bit(p, x, z, y, s=1.0):
    """Огромное трёхшарошечное долото: хвостовик, корпус, три конуса-шарошки."""
    p.prism_xz(K.ngon(x, z, 0.5 * s, 8), y + 2.4 * s, y + 3.4 * s, STEEL)
    p.prism_xz(K.ngon(x, z, 0.9 * s, 8), y + 1.6 * s, y + 2.4 * s, STEEL2)
    for k in range(3):
        t = 2 * math.pi * k / 3
        cx, cz = x + 0.55 * s * math.cos(t), z + 0.55 * s * math.sin(t)
        p.cone([(xx, y + 1.6 * s, zz) for xx, zz in K.ngon(cx, cz, 0.6 * s, 8)], (cx + 0.2 * s * math.cos(t), y + 0.4 * s, cz + 0.2 * s * math.sin(t)),
               YEL)


def lattice_tower(p, x, z, y0, y1, w0, w1, col, levels=6):
    """Решётчатая вышка: четыре наклонные стойки, пояса и раскосы."""
    for e in (-1, 1):
        for f in (-1, 1):
            beam(p, (x + e * w0, y0, z + f * w0), (x + e * w1, y1, z + f * w1), 0.24, 0.24, col)
    for k in range(levels + 1):
        t = k / levels
        y = y0 + (y1 - y0) * t
        w = w0 + (w1 - w0) * t
        for e in (-1, 1):
            p.box(x - w, x + w, y - 0.08, y + 0.08, z + e * w - 0.08, z + e * w + 0.08, col)
            p.box(x + e * w - 0.08, x + e * w + 0.08, y - 0.08, y + 0.08, z - w, z + w, col)
        if k < levels:
            t1 = (k + 1) / levels
            y1_ = y0 + (y1 - y0) * t1
            w1_ = w0 + (w1 - w0) * t1
            beam(p, (x - w, y, z - w), (x + w1_, y1_, z - w1_), 0.1, 0.1, col)
            beam(p, (x - w, y, z + w), (x - w1_, y1_, z - w1_), 0.1, 0.1, col)


# ══ ФАСАД: буровая ════════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, ORANGE, STEEL, STEEL3)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, SAND)
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, -0.1, 1.0, STEEL3)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 9.0, ORANGE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 10.0, 17.6, STEEL)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 17.6, 18.9, STEEL2)
    hazard(FS, axis, fixed + out * 0.88, out, -half, half, 9.0, 10.0, depth=0.3)
    for k in range(int(2 * half // 1.2)):  # гофр
        a = -half + 0.3 + 1.2 * k
        slab(FS, axis, fixed, out, 1.02, a, a + 0.5, 1.0, 9.0, ORANGE2)
        slab(FS, axis, fixed, out, 1.02, a, a + 0.5, 10.0, 17.6, STEEL2)
    if fi > 0:  # бока и тыл: окна-ленты и трубы
        slab(FG, axis, fixed, out, 0.92, -half + 2.0, half - 2.0, 13.0, 15.0, GLASS)
        slab(FS, axis, fixed, out, 1.2, -half + 1.8, half - 1.8, 12.7, 13.0, STEEL3)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# пробоина в стене наверху: червь вылез наружу, из дыры сыплется песок
HXc, HYc = -6.4, 13.6
FS.prism_xy(K.ngon(HXc, HYc, 1.9, 12), -FZ - 1.1, -FZ - 1.04, OIL)
for k in range(12):  # рваная кромка — лепестки гофры, отогнутые наружу
    t = 2 * math.pi * (k + 0.5) / 12
    r0, r1 = 1.9, 2.6 + 0.6 * rng(k, 21)
    FS.prism_xy([(HXc + r0 * math.cos(t - 0.22), HYc + r0 * math.sin(t - 0.22)), (HXc + r0 * math.cos(t + 0.22), HYc + r0 * math.sin(t + 0.22)),
                 (HXc + r1 * math.cos(t), HYc + r1 * math.sin(t))], -FZ - 1.3 - 0.3 * rng(k, 22), -FZ - 0.88, STEEL2 if k % 2 else STEEL)
F.objects(True)  # из дыры свисает хвост червя: кольца сужаются, через одно — жёлтые полосы
tail = [(HXc, HYc - 0.2, -FZ - 1.0), (HXc + 0.5, HYc - 0.9, -FZ - 1.9), (HXc + 1.3, HYc - 1.9, -FZ - 2.4),
        (HXc + 2.2, HYc - 2.8, -FZ - 2.5), (HXc + 2.7, HYc - 3.9, -FZ - 2.3), (HXc + 2.6, HYc - 4.8, -FZ - 2.0)]
for k, (a, b) in enumerate(zip(tail, tail[1:])):
    w = 1.5 - 0.22 * k
    taper(FS, a, b, w, w - 0.22, "BE5932" if k % 2 == 0 else "F0B030")
F.objects(False)
FQ.prism_xz(K.octa(HXc, -FZ - 2.0, 1.6, 0.8, 0.45), -0.1, 0.6, SAND2)  # осыпавшийся песок
# ворота ангара с полосой окон под навесом
FS.box(-5.2, 5.2, 1.0, 8.6, -FZ - 1.0, -FZ - 0.88, STEEL3)
for k in range(7):
    y = 1.0 + 1.08 * k
    FS.box(-5.0, 5.0, y, y + 0.98, -FZ - 1.08, -FZ - 1.0, STEEL if k != 4 else STEEL2)
for k in range(6):
    FG.box(-4.6 + 1.6 * k, -3.6 + 1.6 * k, 5.5, 6.2, -FZ - 1.12, -FZ - 1.08, GLASS)
FS.box(-6.0, 6.0, 8.6, 9.0, -FZ - 3.0, -FZ - 0.88, STEEL2)
for x in (-5.6, 5.6):
    beam(FS, (x, 9.0, -FZ - 2.9), (x, 12.0, -FZ - 0.9), 0.15, 0.15, STEEL3)
hazard(FS, "z", -FZ - 1.12, -1, -5.0, 5.0, 1.0, 1.8, depth=0.04)
# вышка буровой у левого (по фасаду +x) угла
TX, TZ = 13.6, -FZ - 1.9
F.objects(True)
FS.box(TX - 2.6, TX + 2.6, -0.1, 1.2, TZ - 1.0, TZ + 1.0, STEEL3)
lattice_tower(FS, TX, TZ, 1.2, 17.6, 2.2, 0.7, ORANGE, levels=6)
FS.box(TX - 1.6, TX + 1.6, 17.6, 17.9, TZ - 1.0, TZ + 1.0, STEEL2)
FS.box(TX - 0.5, TX + 0.5, 15.6, 16.8, TZ - 0.4, TZ + 0.4, YEL)  # талевый блок
FS.box(TX - 0.04, TX + 0.04, 6.0, 15.6, TZ - 0.04, TZ + 0.04, STEEL3)
FS.prism_xz(K.ngon(TX, TZ, 0.3, 8), 1.2, 6.0, STEEL)
FS.box(TX + 0.3, TX + 2.4, 18.0, 18.6, TZ - 0.2, TZ + 0.2, "D83A2A")
F.objects(False)
# станок-качалка у правого угла
QX, QZ = -12.4, -FZ - 1.8
F.objects(True)
FS.box(QX - 3.6, QX + 3.0, -0.1, 0.5, QZ - 0.8, QZ + 0.8, STEEL3)
for e in (-1, 1):
    beam(FS, (QX - 1.6, 0.5, QZ + e * 0.7), (QX - 0.6, 5.2, QZ + e * 0.1), 0.25, 0.25, STEEL2)
    beam(FS, (QX + 0.6, 0.5, QZ + e * 0.7), (QX - 0.6, 5.2, QZ + e * 0.1), 0.25, 0.25, STEEL2)
FS.box(QX - 4.2, QX + 2.2, 5.2, 5.9, QZ - 0.3, QZ + 0.3, ORANGE)  # балансир
FS.prism_xy([(QX - 4.2, 5.9), (QX - 4.2, 4.2), (QX - 5.0, 3.4), (QX - 5.2, 4.6), (QX - 5.0, 6.2)], QZ - 0.4, QZ + 0.4, ORANGE)  # «голова»
FS.box(QX - 5.06, QX - 4.96, 0.5, 3.6, QZ - 0.05, QZ + 0.05, STEEL3)
FS.prism_xz(K.ngon(QX - 5.0, QZ, 0.35, 8), 0.5, 1.4, STEEL)
for e in (-1, 1):  # кривошипы-противовесы
    FS.prism_xy(K.ngon(QX + 1.7, 2.4, 1.1, 10), QZ + e * 0.5 - 0.2, QZ + e * 0.5 + 0.2, STEEL3)
beam(FS, (QX + 1.7, 2.4, QZ), (QX + 2.0, 5.3, QZ), 0.2, 0.2, STEEL)
F.objects(False)
# трубы вдоль фасада с вентилями, барханы, бочки, долото
for y, col in ((2.2, "8A3A2A"), (3.0, STEEL2)):
    pipe_x(FS, -FX - 1.0, FX + 1.0, y, -FZ - 1.3 - (y - 2.2) * 0.5, 0.28, col)
for x in (-16.4, -6.6, 6.6, 16.4):
    FS.box(x - 0.15, x + 0.15, -0.1, 3.3, -FZ - 1.9, -FZ - 1.2, STEEL3)
F.objects(True)
for x in (-7.4, 7.4):
    valve(FS, x, 3.3, -FZ - 1.7)
for k, (x, z, r) in enumerate(((-16.6, -FZ - 2.2, 1.4), (8.8, -FZ - 2.2, 1.1), (16.8, -FZ - 2.3, 1.2))):
    FQ.prism_xz(K.octa(x, z, r, r * 0.6, r * 0.3), -0.1, 0.5 * r, SAND2)
    FQ.prism_xz(K.octa(x - 0.3, z, r * 0.6, r * 0.4, r * 0.2), 0.5 * r, 0.9 * r, SAND)
for k, x in enumerate((-9.2, -8.0)):
    barrel(FS, x, -FZ - 2.2, y=-0.1, col=(RUST, YEL)[k])
drill_bit(FS, 10.4, -FZ - 2.0, 0.6, s=1.0)
FS.prism_xz(K.ngon(10.4, -FZ - 2.0, 1.1, 8), -0.1, 0.6, STEEL3)
F.objects(False)

# ══ ИНТЕРЬЕР: буровой зал ═════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), STEEL3)
for i in range(-6, 7):
    for j in range(-6, 7):
        if (i + j) % 3 == 0:
            x, z = 2.4 * i, 2.4 * j
            if abs(x) < W - 1.4 and ZF + 6 < z < ZB - 1.4:
                IS.box(x - 1.0, x + 1.0, 0.02, 0.05, z - 1.0, z + 1.0, STEEL2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, STEEL)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.2, STEEL3)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, STEEL)
        hazard(IS, axis, fixed + out * 0.88, out, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.9, depth=0.2)
    if idx < 2:
        for k in range(int(2 * half // 1.2)):
            a = -half + 0.3 + 1.2 * k
            slab(IS, axis, fixed, out, 1.0, a, a + 0.5, 1.2, 15.6, STEEL2)
    slab(IR, axis, fixed, out, 1.3, -half, half, 15.6, 16.4, STEEL3)
    hazard(IS, axis, fixed + out * 1.3, out, -half, half, 15.6, 16.4, depth=0.04, step=1.2)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.8, C - 0.2, 4.4 * k - 0.25, 4.4 * k + 0.25, STEEL3)
# дальняя стена: разрез земли слоями с норами червя
z0 = ZF + 0.88
for k, col in enumerate(STRATA):
    y0, y1 = 15.6 - 2.6 * (k + 1), 15.6 - 2.6 * k
    pts = [(-W + 0.9, max(0.0, y0)), (W - 0.9, max(0.0, y0 + 0.4 * math.sin(k))), (W - 0.9, y1 + 0.4 * math.sin(k + 1)), (-W + 0.9, y1)]
    IR.prism_xy(pts, z0, z0 + 0.4 + 0.1 * k, col)
for k, (x, y, r) in enumerate(((-9.0, 10.4, 1.2), (8.6, 3.2, 1.0), (-4.4, 4.0, 0.9), (13.0, 6.2, 0.7), (-12.8, 3.0, 0.6))):
    IS.prism_xy(K.ngon(x, y, r, 10), z0 + 0.9, z0 + 0.96, OIL)
    IS.frame_xy(K.ngon(x, y, r + 0.35, 10), K.ngon(x, y, r, 10), z0 + 0.5, z0 + 1.0, STRATA[(k + 2) % 6])
for pts in (((-9.0, 10.4), (-8.0, 8.4), (-5.4, 6.8), (-4.4, 4.0)), ((8.6, 3.2), (10.4, 3.6), (11.6, 5.0), (13.0, 6.2))):
    B.tube(IS, [(x, y, z0 + 0.93) for x, y in pts], [1.1, 1.0, 0.95, 0.9], 0.08, (0, 0, 1), "3A2E28")  # извилистые ходы
# ротор и бурильная труба перед разрезом
F.objects(True)
RX, RZ = 0.0, ZF + 3.2
IS.box(RX - 2.2, RX + 2.2, 0.0, 1.0, RZ - 1.6, RZ + 1.6, STEEL2)
ring_y(IS, RX, RZ, 0.6, 1.3, 1.0, 1.4, ORANGE, n=12)
IS.prism_xz(K.ngon(RX, RZ, 0.35, 8), 1.0, C - 3.0, STEEL)
IS.box(RX - 1.2, RX + 1.2, C - 3.0, C - 2.0, RZ - 0.8, RZ + 0.8, YEL)
for e in (-1, 1):
    beam(IS, (RX + e * 2.0, 1.0, RZ - 1.4), (RX + e * 0.6, C - 3.0, RZ), 0.25, 0.25, ORANGE)
F.objects(False)
hazard(IS, "z", RZ + 1.62, 1, RX - 2.2, RX + 2.2, 0.0, 1.0, depth=0.04, step=0.6)
# стеллажи с трубами, ящики с кернами, кабина оператора
F.objects(True)
for s in (-1, 1):
    x = s * (W - 2.6)
    for z in (-12.0, -6.0):
        for e in (-1, 1):
            IS.box(x - 1.4, x + 1.4, 0.0, 3.6, z + e * 2.2 - 0.15, z + e * 2.2 + 0.15, STEEL3)
        for row in range(3):
            for k in range(4):
                xx = x - 1.0 + 0.66 * k
                IS.prism_xy(K.ngon(xx, 0.5 + 1.1 * row + 0.3, 0.3, 8), z - 2.5, z + 2.5, (STEEL, ORANGE2, STEEL2)[row])
CX, CZ = W - 3.0, 9.0  # кабина у лифта, сбоку: не заслоняет зал в кадре от двери
for k in range(3):
    z = -1.2 + 1.6 * k
    IS.box(-W + 1.2, -W + 3.4, 0.0, 0.6, z - 0.7, z + 0.7, "6A5A3A")
    for i, col in enumerate(STRATA[:5]):
        IS.prism_zy(K.ngon(z, 0.85, 0.22, 6), -W + 1.4 + 0.42 * i, -W + 1.8 + 0.42 * i, col)
IS.box(CX - 1.8, CX + 1.8, 0.0, 1.0, CZ - 2.4, CZ + 2.4, STEEL3)
IS.box(CX - 1.8, CX + 1.8, 1.0, 5.6, CZ - 2.4, CZ - 2.2, STEEL2)
IS.box(CX - 1.8, CX + 1.8, 1.0, 5.6, CZ + 2.2, CZ + 2.4, STEEL2)
IS.box(CX + 1.6, CX + 1.8, 1.0, 5.6, CZ - 2.4, CZ + 2.4, STEEL2)
IS.box(CX - 2.0, CX + 2.0, 5.6, 6.0, CZ - 2.6, CZ + 2.6, YEL)
IS.box(CX + 0.2, CX + 1.4, 1.0, 2.2, CZ - 1.6, CZ + 1.6, BLACK)
F.objects(False)
IG.prism_xy(K.rect(CX - 1.6, CX + 1.6, 1.4, 5.4), CZ - 2.24, CZ - 2.2, GLASS)
for k in range(3):
    IG.box(CX + 1.0, CX + 1.42, 2.6, 3.8, CZ - 1.4 + 1.0 * k, CZ - 0.6 + 1.0 * k, ("3AD0F0", "5AE07A", "F0C020")[k])
# кран-балка с крюком
IS.box(-W, W, C - 2.2, C - 1.6, -9.2, -8.6, YEL)
IS.box(3.6, 5.2, C - 2.8, C - 1.6, -9.6, -8.2, STEEL3)
IS.box(4.36, 4.44, 9.0, C - 2.8, -8.94, -8.86, BLACK)
IS.box(4.3, 4.5, 8.2, 9.2, -9.0, -8.8, YEL)  # крюк: стержень и загиб
for k in range(5):
    t0, t1 = math.pi * (1.0 + k / 5), math.pi * (1.0 + (k + 1) / 5)
    beam(IS, (4.9 + 0.5 * math.cos(t0), 8.2 + 0.5 * math.sin(t0), -8.9), (4.9 + 0.5 * math.cos(t1), 8.2 + 0.5 * math.sin(t1), -8.9), 0.2, 0.2, YEL)
# стальная площадка с жёлто-чёрной каймой
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 8, 0.0), 0.0, 0.5, STEEL2)
for k in range(8):
    t0, t1 = 2 * math.pi * (k - 0.5) / 8, 2 * math.pi * (k + 0.5) / 8
    IS.prism_xz([(px + 4.1 * math.cos(t0), pz + 4.1 * math.sin(t0)), (px + 4.1 * math.cos(t1), pz + 4.1 * math.sin(t1)),
                 (px + 3.5 * math.cos(t1), pz + 3.5 * math.sin(t1)), (px + 3.5 * math.cos(t0), pz + 3.5 * math.sin(t0))],
                0.5, 0.7, YEL if k % 2 else BLACK)
IS.prism_xz(K.ngon(px, pz, 3.5, 8, 0.0), 0.5, TOP - 0.08, STEEL3)
IS.prism_xz(K.ngon(px, pz, 3.6, 8, 0.0), TOP - 0.08, TOP, STEEL)
B.lift_leaves(IS, STEEL2, YEL)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 9.0, -FZ, FZ, ORANGE)
SL.box(-FX, FX, 9.0, 18.9, -FZ, FZ, STEEL)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, SAND)
SL.prism_xz(K.rect(TX - 2.2, TX + 2.2, TZ - 2.2, TZ + 2.2), -0.1, 1.2, STEEL3)
SL.cone([(TX - 2.2, 1.2, TZ - 2.2), (TX + 2.2, 1.2, TZ - 2.2), (TX + 2.2, 1.2, TZ + 2.2), (TX - 2.2, 1.2, TZ + 2.2)], (TX, 18.4, TZ), ORANGE)

F.build(exhibit=(PED[0], TOP, PED[1], 3.0), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.95, 0.88)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Strata", (0, 8, ZF + 6), 700, (1.0, 0.85, 0.6))])

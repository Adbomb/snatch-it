"""Этаж «Кроссовок с жильцом» музея-небоскрёба (пятая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — магазин кроссовок в день релиза. Снаружи — белый фасад с чёрными рамами и смелыми цветными
полосами, над входом на козырьке стоит огромный красный кроссовок (белая подошва, шнурки, полоса-молния, без
логотипов), по бокам — витрины-«стены кроссовок»: подсвеченные полки с парами разных цветов, у входа — очередь
из стоек с канатами, скамья, башни из оранжевых обувных коробок, световые короба; бока — геометрические полосы и
круглые окна-подошвы; сзади — тележка с коробками. Внутри — бутик: светлый деревянный пол с тёмной дорожкой,
стены с подсвеченными полками кроссовок, остров-витрина с парами, пуфы для примерки, зеркало, касса, неоновые
кольца под потолком; экспонат — на огромной обувной коробке с приподнятой крышкой и бумагой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_sneakers.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

WHITE, WHITE2, BLACK, BLACK2, GREY = "F4F4F2", "DCDCDA", "26262C", "3A3A42", "9A9AA4"
RED, RED2, ORANGE, ORANGE2, TEAL, VIOLET, LIME, PINK = "E8322E", "B8221E", "FF8A2A", "D86A18", "2AC8B8", "8A5AF0", "A8E83A", "FF5AA8"
WOOD, WOOD2, NEON, NEON2, GLASS = "E0BC8A", "C8A070", "FF3A8A", "3AE8FF", "BFE8FF"
SHOES = (RED, TEAL, VIOLET, LIME, PINK, ORANGE, BLACK2, WHITE)

F = B.Floor("SN", "SneakerTenant", quiet=(WHITE2, BLACK, WOOD2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def sneaker(p, x, y, z, L, col, along_x=True, flip=1, sole=WHITE, accent=WHITE, simple=False):
    """Кроссовок в профиль (вдоль x или z, flip — куда смотрит носок): подошва, верх, шнурки, полоса."""
    w = 0.38 * L

    def prof(pts, d0, d1, c):
        pp = [(u * flip, v) for u, v in pts]
        if along_x:
            p.prism_xy([(x + u, y + v) for u, v in pp], z + d0, z + d1, c)
        else:
            p.prism_zy([(z + u, y + v) for u, v in pp], x + d0, x + d1, c)

    prof([(-0.5 * L, 0.02 * L), (0.42 * L, 0.0), (0.5 * L, 0.06 * L), (0.48 * L, 0.16 * L), (-0.5 * L, 0.18 * L)], -w / 2, w / 2, sole)
    upper = [(-0.48 * L, 0.18 * L), (0.46 * L, 0.16 * L), (0.42 * L, 0.27 * L), (0.18 * L, 0.36 * L), (-0.12 * L, 0.5 * L),
             (-0.3 * L, 0.56 * L), (-0.48 * L, 0.52 * L)]
    prof(upper, -w * 0.46, w * 0.46, col)
    if simple:
        return
    prof([(-0.12 * L, 0.24 * L), (0.22 * L, 0.24 * L), (0.36 * L, 0.29 * L), (0.0, 0.38 * L), (-0.1, 0.32 * L)], -w * 0.5, w * 0.5, accent)
    for k in range(3):  # шнурки
        u = (-0.05 + 0.1 * k) * L
        v = (0.44 - 0.05 * k) * L
        if along_x:
            p.box(x + flip * u - 0.04 * L, x + flip * u + 0.04 * L, y + v - 0.02 * L, y + v + 0.02 * L, z - w * 0.48, z + w * 0.48, WHITE)
        else:
            p.box(x - w * 0.48, x + w * 0.48, y + v - 0.02 * L, y + v + 0.02 * L, z + flip * u - 0.04 * L, z + flip * u + 0.04 * L, WHITE)


def shoebox(p, x, z, y, a, b, h, col=ORANGE, lid=ORANGE2):
    """Обувная коробка: корпус, крышка с нависанием, белая полоса."""
    p.box(x - a / 2, x + a / 2, y, y + h * 0.8, z - b / 2, z + b / 2, col)
    p.box(x - a / 2 - 0.06, x + a / 2 + 0.06, y + h * 0.8, y + h, z - b / 2 - 0.06, z + b / 2 + 0.06, lid)
    p.box(x - a / 2 - 0.02, x + a / 2 + 0.02, y + h * 0.35, y + h * 0.45, z - b / 2 - 0.02, z + b / 2 + 0.02, WHITE)


def stanchion(p, x, z):
    """Стойка очереди: основание, столб, навершие."""
    p.prism_xz(K.ngon(x, z, 0.5, 8), 0.0, 0.12, BLACK)
    p.prism_xz(K.ngon(x, z, 0.1, 6), 0.12, 2.4, "D4B04A")
    p.prism_xz(K.ngon(x, z, 0.18, 6), 2.4, 2.6, "D4B04A")


# ══ ФАСАД: магазин кроссовок ══════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, WHITE, WHITE, BLACK)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, BLACK)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.0, BLACK2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 15.0, WHITE)
    for k in range(int(2 * half // 4.4)):  # панели фасада со швами
        a = -half + 4.4 * k
        slab(FR, axis, fixed, out, 0.96, a + 0.08, a + 4.32, 12.0, 14.8, (WHITE2, WHITE)[k % 2])
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 15.0, 15.9, BLACK)
    slab(FR, axis, fixed, out, 0.88, -half, half, 15.9, 18.9, BLACK2)
    pr = FS.prism_xy if axis == "z" else FS.prism_zy
    for k in range(int(2 * half // 5.0) + 1):  # смелые косые полосы наверху
        a = -half + 5.0 * k
        pr([(a, 16.3), (a + 2.6, 16.3), (a + 4.0, 18.5), (a + 1.4, 18.5)], *sorted((fixed + out * 0.88, fixed + out * 1.0)),
           SHOES[k % 6])
    if axis == "x":  # бока: широкие цветные полосы, круглые окна-подошвы
        for k, (z0, z1) in enumerate(((-14.0, -10.6), (-9.6, -8.2), (6.0, 9.4), (10.4, 11.8))):
            slab(FS, axis, fixed, out, 1.0, z0, z1, 1.0, 11.6, (RED, TEAL, VIOLET, LIME)[(k + (fixed > 0)) % 4])
        z = -0.7  # одно большое окно-витрина (пара окон рядом читалась бы как «глаза»)
        FS.prism_zy(K.rect(z - 3.4, z + 3.4, 2.4, 10.6), *sorted((fixed + out * 0.88, fixed + out * 1.3)), BLACK)
        FG.prism_zy(K.rect(z - 2.9, z + 2.9, 2.9, 10.1), *sorted((fixed + out * 1.3, fixed + out * 1.34)), GLASS)
        for r, y in enumerate((3.4, 6.4)):
            slab(FS, axis, fixed, out, 2.0, z - 2.9, z + 2.9, y - 0.16, y, WHITE2)
            sneaker(FS, fixed + out * 1.7, y, z, 2.6, SHOES[(r + (fixed > 0) * 3) % 6], along_x=False, flip=1, simple=False)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед: витрины-«стены кроссовок» в чёрных рамах
for s in (-1, 1):
    x0, x1 = sorted((s * 4.6, s * 15.6))
    FG.box(x0, x1, 1.6, 11.2, -FZ - 0.6, -FZ - 0.56, "E8F4FF")
    FS.frame_xy(K.rect(x0 - 0.5, x1 + 0.5, 1.1, 11.7), K.rect(x0, x1, 1.6, 11.2), -FZ - 1.5, -FZ - 0.88, BLACK)
    for r in range(4):  # подсвеченные полки с парами
        y = 2.0 + 2.4 * r
        FS.box(x0 + 0.2, x1 - 0.2, y - 0.14, y, -FZ - 1.5, -FZ - 0.6, WHITE2)
        FG.box(x0 + 0.2, x1 - 0.2, y - 0.2, y - 0.14, -FZ - 1.4, -FZ - 0.7, NEON2 if r % 2 else NEON)
        for k in range(4):
            xx = x0 + 1.4 + (x1 - x0 - 2.8) * k / 3
            sneaker(FS, xx, y, -FZ - 1.05, 1.8, SHOES[(k + r * 3 + (s > 0)) % 8], along_x=True, flip=s, simple=k % 2 == 1)
# вход: чёрный портал, неоновая рамка, козырёк с огромным кроссовком
FS.box(-3.6, 3.6, 1.0, 9.6, -FZ - 1.0, -FZ - 0.88, BLACK)
FG.box(-3.0, 3.0, 1.0, 8.8, -FZ - 1.06, -FZ - 1.0, "FFF0E6")
FS.box(-0.08, 0.08, 1.0, 8.8, -FZ - 1.12, -FZ - 1.06, BLACK)
FG.frame_xy(K.rect(-4.1, 4.1, 1.0, 10.1), K.rect(-3.7, 3.7, 1.0, 9.7), -FZ - 1.2, -FZ - 1.0, NEON)
FS.box(-7.6, 7.6, 10.1, 10.7, -FZ - 4.6, -FZ - 0.88, BLACK)
FS.box(-7.6, 7.6, 10.0, 10.1, -FZ - 4.6, -FZ - 4.4, RED)
for s in (-1, 1):
    beam(FS, (s * 7.0, 10.1, -FZ - 4.3), (s * 7.0, 13.0, -FZ - 0.9), 0.24, 0.24, BLACK2)
sneaker(FS, 0.0, 10.7, -FZ - 2.6, 12.4, RED, along_x=True, flip=1, sole=WHITE, accent=WHITE)
FS.prism_xy([(-1.8, 13.4), (0.4, 14.6), (-0.2, 13.9), (2.4, 14.4), (0.2, 13.0), (0.8, 13.6)], -FZ - 2.6 - 2.4, -FZ - 2.6 - 2.3, "FFE83A")
# очередь: стойки с канатами, скамья, башни коробок, световые короба
for k in range(5):
    x = -13.0 + 2.6 * k
    stanchion(FS, x, -FZ - 4.0)
    if k:
        mid = (x - 1.3, 1.7, -FZ - 4.0)
        beam(FS, (x - 2.6, 2.2, -FZ - 4.0), mid, 0.12, 0.12, RED2)
        beam(FS, mid, (x, 2.2, -FZ - 4.0), 0.12, 0.12, RED2)
FS.box(8.0, 13.0, 1.0, 1.4, -FZ - 3.6, -FZ - 2.6, WOOD)
for x in (8.4, 12.6):
    FS.box(x - 0.15, x + 0.15, 0.0, 1.0, -FZ - 3.4, -FZ - 2.8, BLACK)
for k, (x, z, n) in enumerate(((15.4, -FZ - 3.0, 4), (14.0, -FZ - 5.6, 3), (-16.0, -FZ - 6.0, 3))):
    for m in range(n):
        shoebox(FS, x + 0.1 * (m % 2), z, 1.1 * m, 2.0, 1.3, 1.1, (ORANGE, BLACK2, ORANGE)[m % 3], (ORANGE2, RED, ORANGE2)[m % 3])
for s in (-1, 1):
    FS.box(s * 17.2 - 0.7, s * 17.2 + 0.7, 1.0, 9.0, -FZ - 1.4, -FZ - 0.88, BLACK)
    FG.box(s * 17.2 - 0.5, s * 17.2 + 0.5, 1.4, 8.6, -FZ - 1.46, -FZ - 1.4, (NEON, NEON2)[s > 0])
# тыл: тележка с коробками
FS.box(-6.0, -2.0, 0.0, 0.3, FZ + 1.4, FZ + 4.2, GREY)
for k in range(3):
    shoebox(FS, -4.0, FZ + 2.8, 0.3 + 1.1 * k, 3.0, 2.0, 1.1, ORANGE, ORANGE2)
beam(FS, (-6.0, 0.3, FZ + 4.2), (-6.0, 4.6, FZ + 4.4), 0.2, 0.2, GREY)

# ══ ИНТЕРЬЕР: бутик кроссовок ═════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.6
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), WOOD)
for k in range(-8, 8):
    if k % 2:
        IQ.box(2.1 * k + 0.04, 2.1 * k + 2.06, 0.02, 0.04, ZF, ZB, WOOD2)
IQ.box(-3.0, 3.0, 0.04, 0.07, 1.0, ZB - 0.5, BLACK)
IQ.box(-2.6, 2.6, 0.07, 0.09, 1.2, ZB - 0.7, RED)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.0, BLACK)
        slab(IR, axis, fixed, out, 0.88, a0, a1, 1.0, 11.4 if not gap else DOOR[1] + 0.1, WHITE)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 11.4, WHITE)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, NEON)
    slab(IR, axis, fixed, out, 0.88, -half, half, 11.4, C, BLACK2)
    slab(IS, axis, fixed, out, 1.0, -half, half, 11.4, 11.7, RED)
    if idx in (0, 1):  # боковые стены: подсвеченные полки с кроссовками
        for z0, z1 in ((-14.6, -6.4), (-4.6, 5.4)):
            IS.frame_zy(K.rect(z0 - 0.3, z1 + 0.3, 1.8, 10.8), K.rect(z0, z1, 2.1, 10.5), *sorted((fixed + out * 0.88, fixed + out * 1.4)),
                        BLACK)
            for r in range(4):
                y = 2.6 + 2.2 * r
                slab(IS, axis, fixed, out, 2.0, z0, z1, y - 0.14, y, WHITE2)
                for k in range(3):
                    zz = z0 + 1.2 + (z1 - z0 - 2.4) * k / 2
                    sneaker(IS, fixed + out * 1.5, y, zz, 1.6, SHOES[(k + r * 2 + idx) % 8], along_x=False, flip=1, simple=True)
            IG.box(*sorted((fixed + out * 0.9, fixed + out * 0.94)), 2.1, 10.5, z0, z1, ("C8F4FF", "FFD0EC")[idx])
# дальняя стена: зеркало и касса
IG.box(-13.0, -7.0, 2.0, 9.4, ZF + 0.9, ZF + 0.94, "8AB8D8")
IS.frame_xy(K.rect(-13.3, -6.7, 1.7, 9.7), K.rect(-13.0, -7.0, 2.0, 9.4), ZF + 0.88, ZF + 1.2, BLACK)
IR.box(7.0, 13.0, 0.0, 3.2, ZF + 2.0, ZF + 4.0, BLACK)
IS.box(6.8, 13.2, 3.2, 3.5, ZF + 1.8, ZF + 4.2, WHITE)
IS.box(9.0, 10.6, 3.5, 4.6, ZF + 2.4, ZF + 3.2, BLACK2)
IG.box(9.15, 10.45, 3.7, 4.45, ZF + 3.2, ZF + 3.24, NEON2)
for k in range(3):
    shoebox(IS, 11.8, ZF + 6.0 - 1.2 * k, 0.0, 2.0, 1.2, 1.1 + 0.2 * k, ORANGE, ORANGE2)
# остров-витрина с парами, пуфы для примерки
for s in (-1, 1):
    IR.box(s * 8.0 - 2.4, s * 8.0 + 2.4, 0.0, 2.4, 2.0, 5.0, BLACK)
    IS.box(s * 8.0 - 2.6, s * 8.0 + 2.6, 2.4, 2.6, 1.8, 5.2, WHITE)
    for k in range(2):
        sneaker(IS, s * 8.0 - 1.2 + 2.4 * k, 2.6, 3.5, 1.9, SHOES[k + (s > 0) * 2], along_x=True, flip=-s)
    for z in (8.0, 11.0):
        IS.prism_xz(K.ngon(s * 11.0, z, 0.9, 8), 0.0, 1.3, (VIOLET, TEAL)[z > 9])
# неоновые кольца под потолком
for x, z in ((-8.0, -6.0), (8.0, -6.0), (0.0, 6.0)):
    IS.prism_xz(K.ngon(x, z, 0.06, 4), C - 1.6, C, BLACK)
    ring = [(x + 2.2 * math.cos(t), z + 2.2 * math.sin(t)) for t in [2 * math.pi * k / 16 for k in range(16)]]
    inner = [(x + 1.9 * math.cos(t), z + 1.9 * math.sin(t)) for t in [2 * math.pi * k / 16 for k in range(16)]]
    IG.frame_xz(ring, inner, C - 1.8, C - 1.6, (NEON, NEON2, "FFE83A")[int(x + z) % 3])
# пары кроссовок, подвешенные за шнурки под потолком
for k, (x, z) in enumerate(((-11.0, -11.0), (11.0, -10.0), (-12.0, 0.0), (12.0, 1.0))):
    for e in (-1, 1):
        IS.box(x + e * 0.5 - 0.03, x + e * 0.5 + 0.03, 12.6, C, z - 0.03, z + 0.03, WHITE)
        sneaker(IS, x + e * 0.5, 11.4, z, 2.0, SHOES[(k * 2) % 8], along_x=False, flip=e, simple=False)
# постамент — огромная обувная коробка с приподнятой крышкой и бумагой
px, pz = PED
IR.box(px - 4.2, px + 4.2, 0.0, TOP - 0.3, pz - 3.0, pz + 3.0, ORANGE)
IS.box(px - 4.3, px + 4.3, 0.5, 0.8, pz - 3.1, pz + 3.1, WHITE)
IS.box(px - 4.1, px + 4.1, TOP - 0.3, TOP, pz - 2.9, pz + 2.9, WHITE2)
for k in range(6):  # бумага-упаковка зубцами по краю
    x = px - 3.6 + 1.44 * k
    IS.prism_xy([(x, TOP), (x + 0.72, TOP + 0.5), (x + 1.44, TOP)], pz + 2.5, pz + 2.8, WHITE)
IS.loft([(px - 4.5, TOP - 0.4, pz - 3.3), (px + 4.5, TOP - 0.4, pz - 3.3), (px + 4.5, TOP - 0.4, pz - 2.9), (px - 4.5, TOP - 0.4, pz - 2.9)],
        [(px - 4.5, TOP + 5.6, pz - 4.6), (px + 4.5, TOP + 5.6, pz - 4.6), (px + 4.5, TOP + 5.6, pz - 4.2), (px - 4.5, TOP + 5.6, pz - 4.2)],
        ORANGE2)
IS.box(px - 4.0, px + 4.0, TOP + 2.0, TOP + 2.6, pz - 3.85, pz - 3.55, WHITE)
B.lift_leaves(IS, BLACK, NEON)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, WHITE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, BLACK)
SL.box(-FX - 1.9, FX + 1.9, 15.0, 15.9, -FZ - 1.9, FZ + 1.9, BLACK)
for s in (-1, 1):
    SL.box(*sorted((s * 4.6, s * 15.6)), 1.6, 11.2, -FZ - 0.4, -FZ + 0.1, BLACK)
SL.prism_xy([(-6.2, 10.7), (5.6, 10.7), (5.2, 14.0), (-1.5, 17.6), (-6.0, 17.4)], -FZ - 4.9, -FZ - 0.3, RED)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 3000, (1.0, 0.97, 0.95)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.97, 0.92)),
                                                   ("Neon", (12, 6, -6), 800, (1.0, 0.4, 0.7))])

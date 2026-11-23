"""Этаж «Билетик-беглец» музея-небоскрёба (шестая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — ретро-кинотеатр в стиле ар-деко. Снаружи — кремовый фасад с золотыми рёбрами-пилястрами, ступенчатый
аттик с веером лучей, фриз-киноплёнка под карнизом, три стеклянные двери под огромным козырьком с рядами лампочек,
вертикальная вывеска-«лезвие» со звёздами на углу, афиши в рамах с лампами, круглая билетная касса со стеклом и
куполом, красная дорожка со стойками и бархатными канатами, тележка попкорна; на боку — пожарная лестница.
Внутри — маленький зрительный зал: большой экран в золотой раме, красный бархатный занавес складками, ар-деко
панели и бра-веера на стенах, блоки красных кресел по бокам, кессонный потолок с люстрой-кольцом, будка
киномеханика над дверью лифта, аппарат попкорна, коробки с плёнкой; экспонат — на круглой сцене-барабане.
Запуск: blender --background --factory-startup --python scripts/blender/floor_cinema.py -- <репо> <превью>
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

CREAM, CREAM2, GOLD, GOLD2, RED, RED2 = "F2E2C0", "E2CCA0", "E8B840", "C89028", "C42838", "8E1C2A"
NAVY, NAVY2, BLACK, WHITE, BULB, TEAL = "22284A", "181C36", "26262C", "F8F4EA", "FFE89A", "3AA8A0"
POSTER = ("3A6AD8", "E85A9A", "48B868", "F08A30")

F = B.Floor("CN", "RunawayTicket", quiet=(RED2, NAVY2, "6A1820"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def star(cx, cy, r, k=5, inner=0.45):
    return [(cx + r * (1.0 if i % 2 == 0 else inner) * math.cos(math.pi / 2 + i * math.pi / k),
             cy + r * (1.0 if i % 2 == 0 else inner) * math.sin(math.pi / 2 + i * math.pi / k)) for i in range(2 * k)]


def poster(p, g, axis, fixed, out, a, y, w, h, seed, bulbs=True):
    """Афиша в золотой раме: фон, простая картинка (ракета / сердце / звезда / катушка), лампы по раме."""
    d = lambda v: fixed + out * v  # noqa: E731
    pr = p.prism_xy if axis == "z" else p.prism_zy
    fr = p.frame_xy if axis == "z" else p.frame_zy
    fr(K.rect(a - w / 2 - 0.35, a + w / 2 + 0.35, y - h / 2 - 0.35, y + h / 2 + 0.35), K.rect(a - w / 2, a + w / 2, y - h / 2, y + h / 2),
       *sorted((d(0.88), d(1.25))), GOLD)
    pr(K.rect(a - w / 2, a + w / 2, y - h / 2, y + h / 2), *sorted((d(0.88), d(1.0))), POSTER[seed % 4])
    z0, z1 = sorted((d(1.0), d(1.08)))
    kind = seed % 4
    if kind == 0:  # ракета
        pr([(a, y + h * 0.32), (a + w * 0.16, y + h * 0.1), (a + w * 0.16, y - h * 0.2), (a - w * 0.16, y - h * 0.2), (a - w * 0.16, y + h * 0.1)], z0, z1, WHITE)
        pr([(a - w * 0.16, y - h * 0.2), (a - w * 0.3, y - h * 0.32), (a - w * 0.16, y - h * 0.05)], z0, z1, RED)
        pr([(a + w * 0.16, y - h * 0.2), (a + w * 0.3, y - h * 0.32), (a + w * 0.16, y - h * 0.05)], z0, z1, RED)
    elif kind == 1:  # сердце
        pr([(a, y - h * 0.25), (a + w * 0.32, y + h * 0.05), (a + w * 0.2, y + h * 0.22), (a, y + h * 0.1), (a - w * 0.2, y + h * 0.22),
            (a - w * 0.32, y + h * 0.05)], z0, z1, RED)
    elif kind == 2:  # звезда
        pr(star(a, y + h * 0.02, w * 0.33), z0, z1, "FFE060")
    else:  # катушка плёнки
        pr(K.ngon(a, y + h * 0.02, w * 0.32, 12), z0, z1, BLACK)
        for i in range(4):
            t = math.pi / 2 * i + math.pi / 4
            pr(K.ngon(a + w * 0.16 * math.cos(t), y + h * 0.02 + w * 0.16 * math.sin(t), w * 0.07, 6), z1 - 0.02, z1 + 0.02, POSTER[seed % 4])
    pr(K.rect(a - w * 0.36, a + w * 0.36, y - h * 0.42, y - h * 0.34), z0, z1, WHITE)
    if bulbs:
        for i in range(5):
            for e in (-1, 1):
                yy = y - h / 2 + h * (i + 0.5) / 5
                aa = a + e * (w / 2 + 0.18)
                if axis == "z":
                    g.box(aa - 0.09, aa + 0.09, yy - 0.09, yy + 0.09, *sorted((d(1.25), d(1.34))), BULB)
                else:
                    g.box(*sorted((d(1.25), d(1.34))), yy - 0.09, yy + 0.09, aa - 0.09, aa + 0.09, BULB)


def seat(p, x, z, col=RED):
    """Кресло зрительного зала лицом к экрану (−z): сиденье, спинка, подлокотники, ножка."""
    p.box(x - 0.55, x + 0.55, 1.0, 1.35, z - 0.55, z + 0.4, col)
    p.box(x - 0.55, x + 0.55, 1.0, 2.9, z + 0.4, z + 0.72, col)
    p.box(x - 0.5, x + 0.5, 2.9, 3.0, z + 0.42, z + 0.7, RED2)
    for e in (-1, 1):
        p.box(x + e * 0.6 - 0.07, x + e * 0.6 + 0.07, 0.0, 1.8, z - 0.5, z + 0.6, BLACK)
    p.box(x - 0.12, x + 0.12, 0.0, 1.0, z - 0.1, z + 0.3, BLACK)


# ══ ФАСАД: кинотеатр ар-деко ═════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, CREAM, CREAM, NAVY2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "8A8A92")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.2, BLACK)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 15.0, CREAM)
    slab(FR, axis, fixed, out, 1.0, -half, half, 1.2, 2.6, NAVY)
    for k in range(int(2 * half // 4.5) + 1):  # золотые рёбра-пилястры с ар-деко капителью
        a = -half + 0.6 + 4.5 * k
        if a > half - 0.4 or (fi == 0 and -6.4 < a < 6.4):
            continue
        slab(FS, axis, fixed, out, 1.2, a - 0.3, a + 0.3, 2.6, 14.0, CREAM2)
        slab(FS, axis, fixed, out, 1.32, a - 0.1, a + 0.1, 2.6, 14.0, GOLD)
        slab(FS, axis, fixed, out, 1.4, a - 0.5, a + 0.5, 14.0, 14.6, GOLD2)
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 15.0, 15.6, NAVY)
    slab(FR, axis, fixed, out, 1.95, -half - 0.5, half + 0.5, 15.6, 16.8, BLACK)  # фриз-киноплёнка
    if fi == 0:
        for k in range(30):
            a = -half + 0.7 + 1.2 * k
            for yy in (15.75, 16.5):
                slab(FG, axis, fixed, out, 2.0, a - 0.2, a + 0.2, yy, yy + 0.18, "D8E8F0")
            if k % 2 == 0:
                slab(FS, axis, fixed, out, 2.0, a - 0.45, a + 0.45, 16.05, 16.35, POSTER[k // 2 % 4])
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.8, 18.9, CREAM2)
    slab(FR, axis, fixed, out, 1.3, -half - 0.2, half + 0.2, 18.4, 18.9, GOLD2)
    if axis == "x":  # бока: ряд афиш с лампами
        for k, z in enumerate((-11.0, -3.5, 4.0, 11.5)):
            poster(FS, FG, axis, fixed, out, z, 8.0, 3.0, 4.4, k + (2 if fixed > 0 else 0), bulbs=k % 2 == 0)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# ступенчатый аттик с веером лучей над входом
FR.prism_xy([(-8.0, 16.8), (8.0, 16.8), (8.0, 17.6), (5.0, 17.6), (5.0, 18.3), (2.5, 18.3), (2.5, 18.9), (-2.5, 18.9), (-2.5, 18.3),
             (-5.0, 18.3), (-5.0, 17.6), (-8.0, 17.6)], -FZ - 1.6, -FZ - 0.88, CREAM)
for k in range(9):
    t0 = math.pi * (0.1 + 0.8 * k / 9)
    t1 = math.pi * (0.1 + 0.8 * (k + 0.55) / 9)
    FS.prism_xy([(0.0, 11.0), (5.2 * math.cos(t0), 11.0 + 3.6 * math.sin(t0)), (5.2 * math.cos(t1), 11.0 + 3.6 * math.sin(t1))],
                -FZ - 1.1, -FZ - 0.88, (GOLD, GOLD2)[k % 2])
FS.prism_xy(K.ngon(0.0, 11.0, 1.0, 12), -FZ - 1.25, -FZ - 0.88, RED)
# три стеклянные двери
FS.box(-6.0, 6.0, 1.2, 7.6, -FZ - 1.0, -FZ - 0.88, NAVY2)
for x in (-4.0, 0.0, 4.0):
    FG.box(x - 1.6, x + 1.6, 1.4, 7.0, -FZ - 1.06, -FZ - 1.0, "FFE0A8")
    FS.frame_xy(K.rect(x - 1.8, x + 1.8, 1.2, 7.2), K.rect(x - 1.6, x + 1.6, 1.4, 7.0), -FZ - 1.3, -FZ - 0.95, GOLD)
    FS.box(x - 0.9, x + 0.9, 4.0, 4.15, -FZ - 1.36, -FZ - 1.25, GOLD2)
# козырёк с лампочками и табло
FS.box(-9.0, 9.0, 8.4, 10.8, -FZ - 4.4, -FZ - 0.88, NAVY)
FS.box(-9.2, 9.2, 8.2, 8.4, -FZ - 4.6, -FZ - 0.88, GOLD)
FS.box(-9.2, 9.2, 10.8, 11.0, -FZ - 4.6, -FZ - 0.88, GOLD)
FS.box(-8.4, 8.4, 8.8, 10.4, -FZ - 4.48, -FZ - 4.4, WHITE)
for r in range(2):
    for k in range(6):
        x0 = -7.8 + 2.7 * k
        FS.box(x0, x0 + 1.4 + 0.6 * ((k + r) % 2), 9.95 - 0.7 * r, 10.2 - 0.7 * r, -FZ - 4.54, -FZ - 4.48, POSTER[(k + r) % 4])
for k in range(25):
    x = -8.8 + 0.733 * k
    FG.box(x - 0.1, x + 0.1, 8.0, 8.2, -FZ - 4.56, -FZ - 4.36, BULB)
    FG.box(x - 0.1, x + 0.1, 11.0, 11.2, -FZ - 4.56, -FZ - 4.36, BULB)
for k in range(6):
    z = -FZ - 1.2 - 0.6 * k
    for x in (-9.2, 9.2):
        FG.box(x - 0.1, x + 0.1, 8.0, 8.2, z - 0.1, z + 0.1, BULB)
for x in (-8.6, 8.6):
    beam(FS, (x, 10.8, -FZ - 4.2), (x, 14.4, -FZ - 0.9), 0.12, 0.12, GOLD2)
# вертикальная вывеска-«лезвие» со звёздами на левом углу
bx = -13.0
FS.box(bx - 0.3, bx + 0.3, 7.8, 18.6, -FZ - 3.4, -FZ - 0.88, RED)
FS.box(bx - 0.36, bx + 0.36, 7.6, 7.8, -FZ - 3.6, -FZ - 0.88, GOLD)
FS.box(bx - 0.36, bx + 0.36, 18.6, 18.8, -FZ - 3.6, -FZ - 0.88, GOLD)
for k, y in enumerate((9.4, 11.6, 13.8, 16.0)):
    for e in (-1, 1):
        FS.prism_zy(star(-FZ - 2.15, y + 0.6, 0.85), bx + e * 0.3, bx + e * 0.38, ("FFE060", WHITE)[k % 2])
for k in range(14):
    y = 8.0 + 0.75 * k
    for e in (-1, 1):
        FG.box(bx + e * 0.3 - 0.06, bx + e * 0.3 + 0.06, y, y + 0.18, -FZ - 3.5, -FZ - 3.3, BULB)
# афиши слева от входа (справа — касса)
poster(FS, FG, "z", -FZ, -1, -9.0, 4.8, 2.6, 4.0, 0)
poster(FS, FG, "z", -FZ, -1, 15.4, 9.6, 2.4, 3.6, 1)
# круглая билетная касса
kx, kz = 11.0, -FZ - 4.6
FS.prism_xz(K.ngon(kx, kz, 1.9, 10), 0.0, 3.0, RED)
FS.prism_xz(K.ngon(kx, kz, 2.0, 10), 2.9, 3.2, GOLD)
FG.prism_xz(K.ngon(kx, kz, 1.8, 10), 3.2, 6.2, "C8E4F0")
for k in range(10):
    t = 2 * math.pi * (k + 0.5) / 10
    FS.box(kx + 1.8 * math.cos(t) - 0.08, kx + 1.8 * math.cos(t) + 0.08, 3.2, 6.2, kz + 1.8 * math.sin(t) - 0.08,
           kz + 1.8 * math.sin(t) + 0.08, GOLD2)
FS.prism_xz(K.ngon(kx, kz, 2.1, 10), 6.2, 6.6, GOLD)
FS.cone([(kx + 2.0 * math.cos(t), 6.6, kz + 2.0 * math.sin(t)) for t in [2 * math.pi * (k + 0.5) / 10 for k in range(10)]],
        (kx, 8.0, kz), RED)
FS.prism_xz(K.ngon(kx, kz, 0.25, 6), 8.0, 8.6, GOLD)
FS.prism_xz(star(kx, kz, 0.6), 8.6, 8.75, "FFE060")
# красная дорожка, стойки и бархатные канаты
FQ.box(-5.0, 5.0, -0.1, -0.02, -FZ - 2.88, -FZ - 0.5, RED)
for x in (-5.6, 5.6):
    for k in range(3):
        z = -FZ - 1.6 - 2.2 * k
        FS.prism_xz(K.ngon(x, z, 0.35, 8), 0.0, 0.15, GOLD2)
        FS.prism_xz(K.ngon(x, z, 0.1, 6), 0.15, 2.4, GOLD)
        FS.prism_xz(K.ngon(x, z, 0.2, 8), 2.4, 2.65, GOLD)
    for k in range(2):
        D.chain(FS, (x, 2.2, -FZ - 1.6 - 2.2 * k), (x, 2.2, -FZ - 3.8 - 2.2 * k), 5, 0.14, RED2, sag=0.4)
# тележка попкорна
cx, cz = -14.6, -FZ - 5.0
for e in (-1, 1):
    FS.prism_zy(K.ngon(cz + e * 1.0, 0.5, 0.5, 10), cx - 1.3, cx - 1.1, BLACK)
FS.box(cx - 1.2, cx + 1.2, 0.8, 3.0, cz - 1.3, cz + 1.3, RED)
for k in range(4):
    FS.box(cx - 1.25 + 0.6 * k, cx - 0.95 + 0.6 * k, 0.8, 3.0, cz - 1.34, cz - 1.3, WHITE)
FG.box(cx - 1.0, cx + 1.0, 3.0, 5.0, cz - 1.0, cz + 1.0, "FFF0B0")
for k in range(6):
    FS.prism_xz(K.octa(cx - 0.5 + 0.5 * (k % 3), cz - 0.3 + 0.6 * (k // 3), 0.35, 0.35, 0.14), 3.0, 3.5, "FFE8A0")
FS.box(cx - 1.3, cx + 1.3, 5.0, 5.3, cz - 1.3, cz + 1.3, RED)
FS.cone([(cx - 1.3, 5.3, cz - 1.3), (cx + 1.3, 5.3, cz - 1.3), (cx + 1.3, 5.3, cz + 1.3), (cx - 1.3, 5.3, cz + 1.3)], (cx, 6.3, cz), WHITE)
# правый бок: пожарная лестница
lx = FX + 1.0
for k in range(3):
    y = 5.0 + 4.6 * k
    FS.box(lx, lx + 2.6, y, y + 0.15, -4.0, 6.0, BLACK)
    for z in (-4.0, 6.0):
        FS.box(lx + 2.5, lx + 2.6, y, y + 1.4, z - 0.05, z + 0.05, BLACK)
    FS.box(lx + 2.5, lx + 2.6, y + 1.3, y + 1.4, -4.0, 6.0, BLACK)
    for i in range(7):
        yy, z = y - 4.6 + 0.66 * i, 5.0 - 1.3 * i
        FS.box(lx + 0.8, lx + 2.2, yy, yy + 0.1, z - 0.3, z + 0.3, BLACK)
    beam(FS, (lx + 0.75, y - 4.6, 5.6), (lx + 0.75, y, -3.6), 0.1, 0.3, BLACK)
# тыл: вентиляционный короб
FS.box(-12.0, -6.0, 13.0, 16.6, FZ + 0.88, FZ + 3.2, "A8ACB4")
for k in range(5):
    FS.box(-11.6 + 1.1 * k, -11.0 + 1.1 * k, 13.4, 16.2, FZ + 3.2, FZ + 3.3, "70747C")

# ══ ИНТЕРЬЕР: зрительный зал ═════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.3
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), RED2)
for i in range(-6, 7):  # ромбы ковра
    for j in range(-6, 7):
        if (i + j) % 2 == 0:
            x, z = 2.6 * i, 2.5 * j
            IQ.prism_xz([(x, z - 0.6), (x + 0.6, z), (x, z + 0.6), (x - 0.6, z)], 0.02, 0.04, GOLD2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, NAVY)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 3.2, RED2)
        slab(IR, axis, fixed, out, 1.1, a0, a1, 3.2, 3.5, GOLD2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, NAVY)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, GOLD)
    if idx < 2:  # ар-деко панели и бра-веера
        for k, a in enumerate((-12.0, -4.0, 4.0, 12.0)):
            slab(IS, axis, fixed, out, 1.0, a - 2.2, a + 2.2, 4.2, 13.6, NAVY2)
            for e in (-1, 1):
                slab(IS, axis, fixed, out, 1.08, a + e * 1.6 - 0.12, a + e * 1.6 + 0.12, 4.2, 13.6, GOLD)
            slab(IS, axis, fixed, out, 1.08, a - 2.2, a + 2.2, 13.6, 13.9, GOLD)
            if k in (0, 2):
                pr = IS.prism_zy
                d0, d1 = sorted((fixed + out * 1.0, fixed + out * 1.5))
                for i in range(5):
                    t0, t1 = math.pi * (0.15 + 0.7 * i / 5), math.pi * (0.15 + 0.7 * (i + 0.6) / 5)
                    IG.prism_zy([(a, 9.0), (a + 1.5 * math.cos(t0), 9.0 + 1.6 * math.sin(t0)), (a + 1.5 * math.cos(t1), 9.0 + 1.6 * math.sin(t1))],
                                d0, d1, "FFD890")
    slab(IR, axis, fixed, out, 1.5, -half, half, 14.4, 15.0, GOLD2)
# кессонный потолок и люстра-кольцо
for k in range(-3, 4):
    IS.box(-W, W, C - 0.7, C - 0.2, 4.4 * k - 0.25, 4.4 * k + 0.25, NAVY)
    IS.box(4.6 * k - 0.25, 4.6 * k + 0.25, C - 0.7, C - 0.2, ZF, ZB, NAVY)
ring_y(IS, 0.0, -3.0, 2.6, 3.0, C - 2.2, C - 1.9, GOLD, n=16)
ring_y(IG, 0.0, -3.0, 2.7, 2.9, C - 2.4, C - 2.2, "FFE8B0", n=16)
for k in range(4):
    t = math.pi / 2 * k + math.pi / 4
    IS.box(2.8 * math.cos(t) - 0.03, 2.8 * math.cos(t) + 0.03, C - 1.9, C - 0.7, -3.0 + 2.8 * math.sin(t) - 0.03, -3.0 + 2.8 * math.sin(t) + 0.03, GOLD)
# экран в золотой раме, занавес складками
IS.frame_xy(K.rect(-10.4, 10.4, 3.4, 14.4), K.rect(-9.6, 9.6, 4.2, 13.6), ZF + 0.88, ZF + 1.5, GOLD)
IG.box(-9.6, 9.6, 4.2, 13.6, ZF + 0.9, ZF + 1.0, "8EA8D0")
IG.prism_xy(star(4.4, 10.2, 1.6), ZF + 1.0, ZF + 1.04, "FFF0A0")  # «кадр»: звезда и комета на экране
IG.prism_xy([(-7.0, 7.0), (-1.0, 9.6), (-0.6, 9.0), (-6.8, 6.4)], ZF + 1.0, ZF + 1.04, "D8E8FF")
IG.prism_xy(K.ngon(-0.6, 9.3, 0.7, 8), ZF + 1.0, ZF + 1.06, "FFFFFF")
for e in (-1, 1):
    for k in range(7):
        x0 = e * (9.2 + 0.85 * k)
        IS.box(*sorted((x0, x0 + e * 0.85)), 0.0, 15.2, ZF + 1.2 + 0.35 * (k % 2), ZF + 1.7 + 0.35 * (k % 2), (RED, "A82030")[k % 2])
    IS.box(*sorted((e * 9.0, e * 15.2)), 13.8, 15.4, ZF + 1.0, ZF + 2.4, RED2)
IS.box(-15.2, 15.2, 14.8, 15.8, ZF + 0.9, ZF + 2.6, RED)
for k in range(16):
    x = -14.6 + 1.95 * k
    IS.prism_xy([(x - 0.9, 14.8), (x + 0.9, 14.8), (x, 14.0)], ZF + 2.5, ZF + 2.6, GOLD)
IS.box(-11.0, 11.0, 0.0, 1.0, ZF + 0.88, ZF + 3.0, NAVY2)
IS.box(-11.2, 11.2, 1.0, 1.15, ZF + 0.88, ZF + 3.2, GOLD2)
# блоки кресел по бокам
for s in (-1, 1):
    for r in range(4):
        z = -9.0 + 3.4 * r
        for k in range(4):
            x = s * (7.4 + 1.5 * k)
            if r == 3 and s * x > 12.0:
                continue
            seat(IS, x, z)
    IS.box(*sorted((s * 6.3, s * 6.5)), 0.0, 1.6, -10.0, 1.6, GOLD2)
# будка киномеханика над дверью лифта
IR.box(-4.6, 4.6, 11.6, 15.6, ZB - 3.0, ZB - 0.88, NAVY2)
IS.box(-4.8, 4.8, 11.4, 11.6, ZB - 3.2, ZB - 0.88, GOLD2)
IG.box(-2.0, 2.0, 12.8, 14.6, ZB - 3.06, ZB - 3.0, "FFE8B0")
IS.prism_xy(K.ngon(1.2, 13.7, 0.5, 10), ZB - 3.3, ZB - 3.0, BLACK)
IG.prism_xy(K.ngon(1.2, 13.7, 0.3, 10), ZB - 3.34, ZB - 3.3, "F8F8FF")
# аппарат попкорна и коробки с плёнкой у лифта
ax, az = -11.0, 11.0
IS.box(ax - 1.2, ax + 1.2, 0.0, 3.0, az - 1.2, az + 1.2, RED)
IG.box(ax - 1.0, ax + 1.0, 3.0, 5.4, az - 1.0, az + 1.0, "FFF0B0")
for k in range(6):
    IS.prism_xz(K.octa(ax - 0.5 + 0.5 * (k % 3), az - 0.3 + 0.6 * (k // 3), 0.35, 0.35, 0.14), 3.0, 3.5, "FFE8A0")
IS.box(ax - 1.3, ax + 1.3, 5.4, 5.8, az - 1.3, az + 1.3, RED)
IS.prism_xz(star(ax, az, 0.7), 5.8, 6.0, "FFE060")
for k in range(4):
    IS.prism_xz(K.ngon(11.4, 11.6, 1.2, 12), 0.35 * k, 0.35 * k + 0.32, ("6A6A72", "50505A")[k % 2])
for k in range(3):
    IS.prism_zy(K.ngon(10.2, 1.3, 1.3, 12), 13.4 + 0.3 * k, 13.68 + 0.3 * k, ("6A6A72", "50505A")[k % 2])
# сцена-барабан для экспоната
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.1, 16), 0.0, 0.6, RED2)
IS.prism_xz(K.ngon(px, pz, 4.2, 16), 0.6, 0.75, GOLD)
IS.prism_xz(K.ngon(px, pz, 3.6, 16), 0.75, TOP - 0.1, RED)
IS.prism_xz(K.ngon(px, pz, 3.35, 16), TOP - 0.1, TOP, RED2)  # тёмно-красный верх: жёлтый билет не сливается
ring_y(IS, px, pz, 3.35, 3.7, TOP - 0.1, TOP, GOLD2, n=16)
for k in range(8):
    t = 2 * math.pi * (k + 0.5) / 8
    IG.box(px + 4.0 * math.cos(t) - 0.1, px + 4.0 * math.cos(t) + 0.1, 0.25, 0.45, pz + 4.0 * math.sin(t) - 0.1, pz + 4.0 * math.sin(t) + 0.1, BULB)
B.lift_leaves(IS, NAVY2, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, CREAM)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "8A8A92")
SL.box(-FX - 0.5, FX + 0.5, 15.0, 16.8, -FZ - 0.5, FZ + 0.5, BLACK)
SL.box(-9.2, 9.2, 8.2, 11.0, -FZ - 4.6, -FZ, NAVY)
SL.box(bx - 0.3, bx + 0.3, 7.8, 18.6, -FZ - 3.4, -FZ, RED)
SL.prism_xz(K.ngon(kx, kz, 2.0, 8), 0.0, 7.0, RED)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2200, (1.0, 0.88, 0.75)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.95, 0.85)),
                                                   ("Screen", (0, 9, ZF + 4), 900, (0.8, 0.88, 1.0))])

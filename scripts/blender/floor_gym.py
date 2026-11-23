"""Этаж «Крыса-качок» музея-небоскрёба (пятая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — старый боксёрский и силовой зал. Снаружи — кирпичный цех с тёмно-синими стальными рамами, большие
окна (за стеклом — силуэты тренажёров), на крыше — огромная гантель-вывеска на стойках, над входом — козырёк с
полосами-молниями, у входа — гигантские гири, стопка покрышек, штанга на стойке, груша на кронштейне; бока — флаги-
баннеры с молниями, пожарная лестница; сзади — водонапорный бак. Внутри — зал: пол из резиновой плитки с
цветной разметкой, вдоль стены — зеркала и стойки с блинами, скамьи со штангами, ряд гантелей на стойке, беговые
дорожки, груши на цепях, ринг-канаты по углу, табло; экспонат — на помосте для тяжёлой атлетики (деревянный центр,
резиновые края) с огромными блинами по бокам.
Запуск: blender --background --factory-startup --python scripts/blender/floor_gym.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

BRICK, BRICK2, BRICK3, NAVY, NAVY2, STEEL, STEEL2 = "B85A42", "9A4634", "CC7458", "2A3A6A", "1E2A4E", "C8CCD4", "7A808C"
RUB, RUB2, RED, RED2, YEL, YEL2, GRN, BLU = "2E2E34", "3E3E46", "E83A3A", "B82A2A", "FFC82A", "E0A018", "3AC06A", "3A8AF0"
WOOD, WOOD2, LEATH, LEATH2, MIRROR, WHITE = "D8A868", "B08048", "B03A2A", "7A2A20", "7AA8C8", "F4F4F0"
PLATES = (RED, BLU, YEL, GRN, "2A2A30")

F = B.Floor("BR", "BuffRat", quiet=(RUB, RUB2, NAVY2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def plate_x(p, x, y, z, r, w, col):
    """Блин штанги, ось вдоль x: диск, бортик, втулка."""
    p.prism_zy(K.ngon(z, y, r, 12), x - w / 2, x + w / 2, col)
    p.prism_zy(K.ngon(z, y, r * 0.35, 8), x - w / 2 - 0.05, x + w / 2 + 0.05, STEEL)


def plate_z(p, x, y, z, r, w, col):
    """Блин, ось вдоль z."""
    p.prism_xy(K.ngon(x, y, r, 12), z - w / 2, z + w / 2, col)
    p.prism_xy(K.ngon(x, y, r * 0.35, 8), z - w / 2 - 0.05, z + w / 2 + 0.05, STEEL)


def barbell_x(p, x0, x1, y, z, r, col):
    """Штанга вдоль x: гриф, по два блина с каждой стороны, замки."""
    p.prism_zy(K.ngon(z, y, 0.12, 6), x0, x1, STEEL)
    L = x1 - x0
    for s, xe in ((1, x0), (-1, x1)):
        plate_x(p, xe + s * L * 0.12, y, z, r, 0.3, col)
        plate_x(p, xe + s * L * 0.17, y, z, r * 0.8, 0.25, PLATES[(PLATES.index(col) + 1) % 5])
        p.prism_zy(K.ngon(z, y, 0.22, 6), *sorted((xe + s * L * 0.2, xe + s * L * 0.22)), STEEL2)


def dumbbell_x(p, x, y, z, L, r, col):
    """Гантель вдоль x."""
    p.prism_zy(K.ngon(z, y, 0.1, 6), x - L / 2, x + L / 2, STEEL)
    for s in (-1, 1):
        p.prism_zy(K.ngon(z, y, r, 8), *sorted((x + s * L * 0.3, x + s * L / 2)), col)


def kettlebell(p, x, z, y, s, col):
    """Гиря: шар-брюшко из ярусов, ручка-скоба."""
    for k, (rr, y0, y1) in enumerate(((0.8, 0.0, 0.3), (1.0, 0.3, 1.1), (0.8, 1.1, 1.45))):
        p.prism_xz(K.ngon(x, z, rr * s, 10), y + y0 * s, y + y1 * s, col)
    for e in (-1, 1):
        beam(p, (x + e * 0.55 * s, y + 1.4 * s, z), (x + e * 0.5 * s, y + 2.1 * s, z), 0.24 * s, 0.24 * s, col)
    beam(p, (x - 0.5 * s, y + 2.1 * s, z), (x + 0.5 * s, y + 2.1 * s, z), 0.24 * s, 0.24 * s, col)


def bench(p, x, z, along_x=True):
    """Скамья для жима: кожаная подушка, стальная рама, стойки."""
    if along_x:
        p.box(x - 1.8, x + 1.8, 1.1, 1.45, z - 0.5, z + 0.5, LEATH)
        for e in (-1, 1):
            p.box(x + e * 1.4 - 0.15, x + e * 1.4 + 0.15, 0.0, 1.1, z - 0.4, z + 0.4, STEEL2)
    else:
        p.box(x - 0.5, x + 0.5, 1.1, 1.45, z - 1.8, z + 1.8, LEATH)
        for e in (-1, 1):
            p.box(x - 0.4, x + 0.4, 0.0, 1.1, z + e * 1.4 - 0.15, z + e * 1.4 + 0.15, STEEL2)


def treadmill(p, g, x, z):
    """Беговая дорожка лицом к −z: лента, рама, стойки, пульт с экраном."""
    p.box(x - 1.0, x + 1.0, 0.0, 0.5, z - 1.8, z + 2.0, RUB2)
    p.box(x - 0.8, x + 0.8, 0.5, 0.56, z - 1.6, z + 1.8, RUB)
    for e in (-1, 1):
        beam(p, (x + e * 0.9, 0.5, z - 1.4), (x + e * 0.9, 3.4, z - 1.8), 0.18, 0.18, STEEL2)
    p.box(x - 1.0, x + 1.0, 3.2, 3.8, z - 2.1, z - 1.6, STEEL2)
    g.box(x - 0.6, x + 0.6, 3.35, 3.7, z - 1.62, z - 1.58, "6AF0C0")


def punching_bag(p, x, z, top, h=3.0, col=RED2):
    """Груша на цепи."""
    p.prism_xz(K.ngon(x, z, 0.08, 4), top - 1.2, top, STEEL2)
    p.prism_xz(K.ngon(x, z, 0.65, 10), top - 1.2 - h, top - 1.2, col)
    p.prism_xz(K.ngon(x, z, 0.7, 10), top - 1.45, top - 1.2, "1E1E22")
    p.prism_xz(K.ngon(x, z, 0.5, 10), top - 1.4 - h, top - 1.2 - h, col)


# ══ ФАСАД: кирпичный зал ══════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, BRICK, BRICK, NAVY2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, RUB2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.2, NAVY)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 15.4, BRICK)
    for r in range(7):  # кирпичная кладка поясами
        y = 1.2 + 2.0 * r
        off = 1.0 if r % 2 else 0.0
        for k in range(int(2 * half // 2.0)):
            a = -half + off + 2.0 * k
            if a + 1.9 > half or rng(fi, r, k) < 0.6:
                continue
            if fi == 0 and -13.4 < a + 1.0 < 13.4 and 3.0 < y < 12.2:
                continue
            if axis == "x" and 2.8 < y < 11.4 and min(abs(a + 1.0 - zc) for zc in (-9.0, 0.0, 9.0)) < 4.4:
                continue  # не закрывать боковые окна
            slab(FR, axis, fixed, out, 1.0, a + 0.08, a + 1.92, y + 0.08, y + 0.92, (BRICK2, BRICK3)[(k + r) % 2])
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 15.4, 16.4, NAVY)
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.4, 18.9, BRICK2)
    slab(FS, axis, fixed, out, 1.0, -half, half, 17.2, 17.6, YEL)
    if axis == "x":  # бока: окна в стальных рамах, баннеры с молнией
        for z in (-9.0, 0.0, 9.0):
            gp = FG.prism_zy
            gp(K.rect(z - 3.0, z + 3.0, 4.0, 11.0), *sorted((fixed + out * 0.9, fixed + out * 0.94)), "9ED0F0")
            FS.frame_zy(K.rect(z - 3.3, z + 3.3, 3.7, 11.3), K.rect(z - 3.0, z + 3.0, 4.0, 11.0),
                        *sorted((fixed + out * 0.88, fixed + out * 1.3)), NAVY)
            for m in (-1, 1):
                slab(FS, axis, fixed, out, 1.2, z + m * 1.0 - 0.1, z + m * 1.0 + 0.1, 4.0, 11.0, NAVY)
            slab(FS, axis, fixed, out, 1.2, z - 3.0, z + 3.0, 7.4, 7.6, NAVY)
        for z in (-13.8, 13.8):
            slab(FS, axis, fixed, out, 1.1, z - 1.4, z + 1.4, 6.0, 14.6, (RED, BLU)[z > 0])
            pr = FS.prism_zy
            pr([(z - 0.3, 13.2), (z + 0.6, 10.6), (z, 10.6), (z + 0.4, 7.6), (z - 0.6, 10.4), (z, 10.4)],
               *sorted((fixed + out * 1.1, fixed + out * 1.2)), YEL)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед: большие окна с тренажёрами за стеклом, вход с козырьком-молнией
for s in (-1, 1):
    x0, x1 = s * 4.2, s * 13.2
    FG.box(*sorted((x0, x1)), 3.6, 11.6, -FZ - 0.94, -FZ - 0.9, "9ED0F0")
    FS.frame_xy(K.rect(*sorted((x0, x1)), 3.3, 11.9), K.rect(*sorted((x0, x1)), 3.6, 11.6), -FZ - 1.4, -FZ - 0.88, NAVY)
    for m in range(1, 3):
        xm = x0 + (x1 - x0) * m / 3
        FS.box(xm - 0.12, xm + 0.12, 3.6, 11.6, -FZ - 1.2, -FZ - 0.88, NAVY)
    FS.box(*sorted((x0, x1)), 7.5, 7.7, -FZ - 1.2, -FZ - 0.88, NAVY)
    for k in range(3):  # силуэты тренажёров за стеклом
        xm = x0 + (x1 - x0) * (k + 0.5) / 3
        FS.box(xm - 0.9, xm + 0.9, 3.6, 4.2, -FZ - 0.6, -FZ - 0.2, RUB)
        dumbbell_x(FS, xm, 5.4, -FZ - 0.5, 2.2, 0.45, PLATES[k])
FS.box(-3.4, 3.4, 1.2, 9.6, -FZ - 1.0, -FZ - 0.88, NAVY2)
FG.box(-2.8, 2.8, 1.2, 8.8, -FZ - 1.06, -FZ - 1.0, "FFE6A0")
FS.box(-0.1, 0.1, 1.2, 8.8, -FZ - 1.12, -FZ - 1.06, NAVY)
FS.box(-5.0, 5.0, 9.8, 10.4, -FZ - 3.6, -FZ - 0.88, NAVY)
for k in range(5):
    x = -4.5 + 2.2 * k
    FS.prism_xy([(x, 10.4), (x + 1.2, 10.4), (x + 0.5, 11.4), (x + 1.4, 11.4), (x + 0.2, 13.0), (x + 0.6, 11.7), (x - 0.2, 11.7)],
                -FZ - 3.6, -FZ - 3.3, YEL)
# угловые баннеры с молниями и боксёрские перчатки под козырьком
for s in (-1, 1):
    FS.box(s * 15.0 - 1.4, s * 15.0 + 1.4, 5.0, 14.6, -FZ - 1.1, -FZ - 0.88, (RED, BLU)[s > 0])
    FS.prism_xy([(s * 15.0 - 0.3, 13.0), (s * 15.0 + 0.6, 10.2), (s * 15.0, 10.2), (s * 15.0 + 0.4, 6.8), (s * 15.0 - 0.6, 10.0),
                 (s * 15.0, 10.0)], -FZ - 1.2, -FZ - 1.1, YEL)
    FS.prism_xy(K.octa(s * 15.0, 4.4, 1.4, 0.5, 0.3), -FZ - 1.16, -FZ - 0.88, (RED2, NAVY2)[s > 0])
    gx = -2.4 + s * 0.75  # пара перчаток висит вместе слева от двери (симметричная пара по бокам читалась бы «глазами»)
    gy = 0.5 if s > 0 else 0.0
    FS.prism_xz(K.ngon(gx, -FZ - 3.0, 0.05, 4), 8.2 - gy, 9.8, WHITE)
    FS.box(gx - 0.55, gx + 0.55, 6.6 - gy, 8.2 - gy, -FZ - 3.5, -FZ - 2.5, RED)
    FS.box(gx - 0.5, gx + 0.5, 6.1 - gy, 6.6 - gy, -FZ - 3.4, -FZ - 2.6, WHITE)
    FS.box(gx + s * 0.55, gx + s * 0.95, 7.0 - gy, 7.9 - gy, -FZ - 3.3, -FZ - 2.7, RED)
# огромная гантель-вывеска на крыше
for s in (-1, 1):
    FS.box(s * 5.0 - 0.3, s * 5.0 + 0.3, 15.4, 16.6, -FZ - 2.0, -FZ - 1.4, STEEL2)
FS.prism_zy(K.ngon(-FZ - 1.7, 17.2, 0.4, 8), -8.0, 8.0, STEEL)
for s in (-1, 1):
    for k, (r, w) in enumerate(((1.7, 0.9), (1.35, 0.7))):
        xc = s * (8.6 + 0.85 * k)
        FS.prism_zy(K.ngon(-FZ - 1.7, 17.2, r, 12), xc - w / 2, xc + w / 2, (RED, YEL)[k])
    FS.prism_zy(K.ngon(-FZ - 1.7, 17.2, 0.5, 8), s * 10.0, s * 10.5, STEEL2)
# у входа: гигантские гири, покрышки, стойка со штангой, груша на кронштейне
kettlebell(FS, -7.0, -FZ - 3.0, 0.0, 1.6, RUB)
kettlebell(FS, 7.0, -FZ - 3.2, 0.0, 1.3, RED)
for k in range(3):
    FS.prism_xz(K.ngon(-12.0 + 0.1 * k, -FZ - 4.0, 1.5, 12), 0.6 * k, 0.6 * k + 0.55, RUB)
    FS.prism_xz(K.ngon(-12.0 + 0.1 * k, -FZ - 4.0, 0.8, 10), 0.6 * k + 0.55, 0.6 * k + 0.58, RUB2)
for s in (-1, 1):
    FS.box(11.0 + s * 2.2 - 0.2, 11.0 + s * 2.2 + 0.2, 0.0, 4.0, -FZ - 4.4, -FZ - 4.0, STEEL2)
barbell_x(FS, 7.8, 14.2, 4.2, -FZ - 4.2, 1.1, RED)
beam(FS, (15.6, 9.0, -FZ - 0.9), (15.6, 9.0, -FZ - 3.0), 0.3, 0.3, STEEL2)
punching_bag(FS, 15.6, -FZ - 2.8, 9.0, 3.4, RED2)
# тыл: водонапорный бак на опорах, покрышки
for e in (-1, 1):
    for f in (-1, 1):
        FS.box(4.0 + e * 2.0 - 0.2, 4.0 + e * 2.0 + 0.2, 0.0, 9.0, FZ + 3.0 + f * 1.6 - 0.2, FZ + 3.0 + f * 1.6 + 0.2, STEEL2)
FS.prism_xz(K.ngon(4.0, FZ + 3.0, 2.6, 12), 9.0, 14.0, "6A8AB0")
FS.cone([(4.0 + 2.8 * math.cos(t), 14.0, FZ + 3.0 + 2.8 * math.sin(t)) for t in [2 * math.pi * k / 12 for k in range(12)]],
        (4.0, 16.0, FZ + 3.0), NAVY)
for k in range(2):
    FS.prism_xz(K.ngon(-6.0, FZ + 2.4, 1.4, 12), 0.6 * k, 0.6 * k + 0.55, RUB)

# ══ ИНТЕРЬЕР: силовой и боксёрский зал ════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), RUB)
for i in range(-8, 8):  # плитка резины в шахматку
    for j in range(-7, 8):
        if (i + j) % 2:
            IQ.box(2.1 * i + 0.05, 2.1 * i + 2.05, 0.02, 0.04, 2.1 * j + 0.05, 2.1 * j + 2.05, RUB2)
for x in (-6.5, 6.5):
    IQ.box(x - 0.12, x + 0.12, 0.04, 0.07, -14.0, 7.0, YEL)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.6, NAVY)
        slab(IR, axis, fixed, out, 0.88, a0, a1, 1.6, C if not gap else DOOR[1] + 0.1, BRICK)
        for r in range(6):  # кладка
            y = 2.0 + 2.2 * r
            if gap and y > DOOR[1]:
                break
            for k in range(int((a1 - a0) // 2.4)):
                a = a0 + 2.4 * k + (1.2 if r % 2 else 0.0)
                if a + 2.2 > a1 or rng(idx, r, k) < 0.55:
                    continue
                if idx == 0 and a + 2.2 > -14.6 and a < 6.6 and y < 9.4:
                    continue  # не закрывать зеркала
                slab(IR, axis, fixed, out, 1.0, a + 0.1, a + 2.2, y + 0.1, y + 1.0, (BRICK2, BRICK3)[(k + r) % 2])
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, BRICK)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, YEL)
    slab(IR, axis, fixed, out, 1.6, -half, half, 14.6, 15.4, NAVY)
# зеркала вдоль левой стены, стойки с блинами, скамьи со штангами
for k, z in enumerate((-11.0, -4.0, 3.0)):
    IG.box(-W + 0.9, -W + 0.96, 2.0, 9.0, z - 3.2, z + 3.2, MIRROR)
    IS.frame_zy(K.rect(z - 3.5, z + 3.5, 1.7, 9.3), K.rect(z - 3.2, z + 3.2, 2.0, 9.0), -W + 0.88, -W + 1.2, STEEL2)
for z in (-10.0, 1.0):
    IS.box(-W + 1.2, -W + 2.0, 0.0, 4.6, z - 0.2, z + 0.2, STEEL2)
    for k in range(3):
        for m in range(2):
            plate_x(IS, -W + 2.1 + 0.32 * m, 1.2 + 1.4 * k, z, 0.9 - 0.15 * k, 0.28, PLATES[(k + m) % 5])
for x, z in ((-9.0, -8.0), (-9.0, -1.0)):
    bench(IS, x, z, along_x=True)
    for e in (-1, 1):
        IS.box(x + e * 1.4 - 0.12, x + e * 1.4 + 0.12, 0.0, 3.0, z - 1.0, z - 0.8, STEEL2)
    barbell_x(IS, x - 3.2, x + 3.2, 3.1, z - 0.9, 0.85, PLATES[int(abs(z)) % 4])
# стойка с гантелями вдоль дальней стены, беговые дорожки, груши на цепях, угол ринга
IS.box(-11.0, -3.0, 0.0, 2.4, ZF + 1.0, ZF + 2.4, STEEL2)
for k in range(6):
    x = -10.3 + 1.4 * k
    dumbbell_x(IS, x, 2.6, ZF + 1.4, 1.2, 0.32 + 0.03 * k, PLATES[k % 5])
    dumbbell_x(IS, x, 1.3, ZF + 2.0, 1.2, 0.3 + 0.03 * k, PLATES[(k + 2) % 5])
for x in (4.5, 8.0, 11.5):
    treadmill(IS, IG, x, ZF + 3.6)
for x, z in ((12.4, -3.0), (12.4, 2.6)):
    punching_bag(IS, x, z, C - 0.5, 3.2, (RED2, BLU)[z > 0])
RZ = 5.2
for h, col in ((1.0, RED), (1.8, WHITE), (2.6, BLU)):  # канаты ринга у правой стены
    beam(IS, (W - 6.0, h, RZ), (W - 0.9, h, RZ), 0.12, 0.12, col)
IS.box(W - 6.3, W - 5.7, 0.0, 3.0, RZ - 0.3, RZ + 0.3, STEEL)
# табло над дальней стеной
IS.box(-4.0, 4.0, 11.0, 14.0, ZF + 0.88, ZF + 1.3, NAVY2)
for k in range(4):
    IG.box(-3.4 + 1.8 * k, -2.0 + 1.8 * k, 11.8, 13.2, ZF + 1.3, ZF + 1.34, (RED, YEL, GRN, RED)[k])
# лампы-колпаки под потолком
for x in (-8.0, 0.0, 8.0):
    for z in (-8.0, 2.0):
        IS.prism_xz(K.ngon(x, z, 0.06, 4), C - 2.2, C, STEEL2)
        IS.cone([(x + 1.1 * math.cos(t), C - 2.6, z + 1.1 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]],
                (x, C - 2.0, z), NAVY)
        IG.prism_xz(K.ngon(x, z, 0.6, 8), C - 2.68, C - 2.6, "FFF4D0")
# помост: резиновые края, деревянный центр, огромные блины по бокам, гири
px, pz = PED
IR.box(px - 4.4, px + 4.4, 0.0, TOP - 0.1, pz - 3.6, pz + 3.6, RUB2)
IS.box(px - 2.6, px + 2.6, TOP - 0.1, TOP, pz - 3.5, pz + 3.5, WOOD)
for k in range(5):
    IS.box(px - 2.6 + 1.04 * k, px - 2.6 + 1.04 * k + 0.04, TOP, TOP + 0.02, pz - 3.5, pz + 3.5, WOOD2)
for s in (-1, 1):
    plate_x(IS, px + s * 5.2, 1.7, pz - 2.4, 1.7, 0.5, (RED, BLU)[s > 0])
    plate_x(IS, px + s * 5.7, 1.35, pz - 2.4, 1.35, 0.4, YEL)
kettlebell(IS, px - 5.4, pz + 3.2, 0.0, 0.7, RED)
kettlebell(IS, px + 5.4, pz + 3.4, 0.0, 0.6, BLU)
B.lift_leaves(IS, NAVY, YEL)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, BRICK)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, RUB2)
SL.box(-FX - 1.9, FX + 1.9, 15.4, 16.4, -FZ - 1.9, FZ + 1.9, NAVY)
for s in (-1, 1):
    SL.box(*sorted((s * 4.2, s * 13.2)), 3.6, 11.6, -FZ - 0.4, -FZ + 0.1, "9ED0F0")
    SL.prism_zy(K.ngon(-FZ - 1.7, 17.2, 1.7, 6), s * 8.2, s * 9.0, RED)
SL.box(-8.2, 8.2, 16.9, 17.5, -FZ - 1.9, -FZ - 1.5, STEEL)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 2800, (1.0, 0.95, 0.88)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.96, 0.9)),
                                                   ("Warm", (-12, 6, -6), 800, (1.0, 0.7, 0.45))])

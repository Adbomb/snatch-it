"""Этаж «Золотой крысомех» музея-небоскрёба (шестая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — ангар боевых роботов. Снаружи — клёпаные стальные панели с рёбрами, огромные раздвижные ворота
с жёлто-чёрными кромками, приоткрытые: в щели — тёмный ангар и голубая подсветка; над воротами — рельс с тележкой
крана и ряд оранжевых мигалок, эмблема «шестерня с молнией», на площадке — жёлтые шевроны и большой след ноги
робота, слева на поддоне лежит запасной кулак меха, справа — бочки с топливом, ящики, инструментальная тележка
и ступня робота на подставке; на крыше — тарелка радара, антенны и прожекторы; на боку — вентиляционные короба
и трубы. Внутри — ремонтный отсек: пол из стальных плит с жёлтой разметкой и кругом, вокруг постамента — портал
из двух башен с перекладиной, кабели и две роборуки со сварочными искрами, у дальней стены — большой экран
со схемой робота, на стенах — щиты с инструментами, запасная рука меха на подставке, светящиеся топливные
элементы, пульт у лифта, кран-балка и лампы; экспонат — на тёмной стальной площадке с зеброй, зажимами
и голубым светящимся кольцом.
Запуск: blender --background --factory-startup --python scripts/blender/floor_hangar.py -- <репо> <превью>
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

STEEL, STEEL2, PANEL, DARK, DARK2, HAZ = "8494A4", "6A7888", "A4B2C0", "262C34", "343C46", "F2C230"
BLACK, ORANGE, RED, WHITE, CYAN, CONC = "22252A", "F08A30", "D83A2E", "E8ECF0", "4AE0F0", "8A8E94"
OLIVE, BLUE, GOLDM = "6A7A4A", "3A6AB0", "D8A838"

F = B.Floor("MH", "GoldenRatMech", quiet=(CONC, DARK2, "6A7480"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def hazard(p, axis, fixed, out, a0, a1, y0, y1, depth):
    """Жёлто-чёрная «зебра» наклонными полосами."""
    slab(p, axis, fixed, out, depth, a0, a1, y0, y1, HAZ)
    d0, d1 = sorted((fixed + out * depth, fixed + out * (depth + 0.04)))
    pr = p.prism_xy if axis == "z" else p.prism_zy
    a = a0
    while a < a1 - 0.6:
        pr([(a, y0), (min(a + 0.6, a1), y0), (min(a + 0.6 + (y1 - y0), a1), y1), (min(a + (y1 - y0), a1), y1)], d0, d1, BLACK)
        a += 1.2


def fist(p, x, y, z, s, col):
    """Кулак робота: ладонь-блок, четыре пальца-сегмента, большой палец, манжета (лицом к −z)."""
    p.box(x - 1.6 * s, x + 1.6 * s, y, y + 2.2 * s, z - 1.0 * s, z + 1.2 * s, col)
    for k in range(4):
        xx = x - 1.2 * s + 0.8 * k * s
        p.box(xx - 0.36 * s, xx + 0.36 * s, y + 0.2 * s, y + 2.0 * s, z - 1.6 * s, z - 1.0 * s, PANEL)
        p.box(xx - 0.38 * s, xx + 0.38 * s, y + 1.0 * s, y + 1.15 * s, z - 1.65 * s, z - 0.98 * s, DARK)
    p.box(x + 1.6 * s, x + 2.2 * s, y + 0.3 * s, y + 1.6 * s, z - 1.0 * s, z + 0.4 * s, PANEL)
    p.box(x - 1.8 * s, x + 1.8 * s, y - 0.1 * s, y + 2.4 * s, z + 1.2 * s, z + 2.0 * s, DARK2)
    for k in range(3):
        p.prism_zy(K.ngon(z + 1.6 * s, y + 0.4 * s + 0.8 * k * s, 0.18 * s, 6), x - 1.85 * s, x + 1.85 * s, HAZ)


def barrel(p, x, z, col):
    p.prism_xz(K.ngon(x, z, 0.8, 10), 0.0, 2.0, col)
    for yy in (0.5, 1.5):
        p.prism_xz(K.ngon(x, z, 0.85, 10), yy - 0.06, yy + 0.06, DARK)


def emblem(pr, cx, cy, r, d0, d1):
    """Эмблема: шестерня с молнией (без надписей)."""
    teeth = []
    for k in range(16):
        t0 = 2 * math.pi * k / 16
        rr = r if k % 2 == 0 else r * 0.82
        teeth.append((cx + rr * math.cos(t0), cy + rr * math.sin(t0)))
    pr(teeth, d0, d1, HAZ)
    pr(K.ngon(cx, cy, r * 0.65, 12), d0 - 0.04, d0, DARK)  # слои выступают наружу, к −z
    pr([(cx + 0.1 * r, cy + 0.55 * r), (cx - 0.3 * r, cy - 0.05 * r), (cx, cy - 0.05 * r), (cx - 0.15 * r, cy - 0.55 * r),
        (cx + 0.35 * r, cy + 0.1 * r), (cx + 0.05 * r, cy + 0.1 * r)], d0 - 0.08, d0 - 0.04, WHITE)


# ══ ФАСАД: ангар ══════════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, STEEL, PANEL, DARK)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, CONC)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.2, DARK2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 15.4, STEEL)
    for k in range(int(2 * half // 3.0) + 1):  # рёбра и клёпка
        a = -half + 3.0 * k
        if fi == 0 and -11.4 < a < 11.4:
            continue
        slab(FS, axis, fixed, out, 1.1, a - 0.2, a + 0.2, 1.2, 15.4, STEEL2)
    for y in (5.0, 10.0):
        slab(FS, axis, fixed, out, 0.98, -half, half, y - 0.1, y + 0.1, STEEL2)
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 15.4, 16.2, DARK)
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.2, 18.9, PANEL)
    hazard(FS, axis, fixed, out, -half - 0.5, half + 0.5, 16.2, 16.8, 0.92)
    slab(FR, axis, fixed, out, 1.3, -half - 0.2, half + 0.2, 18.4, 18.9, DARK2)
    if axis == "x":  # бока: вентиляционные короба и трубы
        for z in (-9.0, 4.0):
            slab(FR, axis, fixed, out, 2.0, z - 2.6, z + 2.6, 6.0, 11.0, DARK2)
            for k in range(6):
                slab(FS, axis, fixed, out, 2.1, z - 2.4, z + 2.4, 6.4 + 0.75 * k, 6.7 + 0.75 * k, STEEL2)
        beam(FS, (fixed + out * 1.4, 0.0, 12.0), (fixed + out * 1.4, 15.4, 12.0), 0.6, 0.6, ORANGE)
        beam(FS, (fixed + out * 1.4, 0.0, -14.4), (fixed + out * 1.4, 15.4, -14.4), 0.6, 0.6, STEEL2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# жёлтые шевроны и след ноги на площадке
for k in range(6):
    x = -15.0 + 6.0 * k
    FQ.prism_xz([(x - 1.2, -FZ - 2.6), (x, -FZ - 1.6), (x + 1.2, -FZ - 2.6), (x + 1.2, -FZ - 2.2), (x, -FZ - 1.2), (x - 1.2, -FZ - 2.2)],
                -0.1, -0.06, HAZ)
# раздвижные ворота, приоткрытые
FS.box(-11.4, 11.4, 1.2, 14.4, -FZ - 0.96, -FZ - 0.88, BLACK)
IGap = 1.6
for e in (-1, 1):
    x0, x1 = sorted((e * IGap, e * 11.0))
    FS.box(x0, x1, 1.2, 14.0, -FZ - 1.6, -FZ - 1.0, PANEL)
    for k in range(4):
        y = 2.6 + 3.0 * k
        FS.box(x0 + 0.3, x1 - 0.3, y, y + 0.25, -FZ - 1.7, -FZ - 1.6, STEEL2)
    for k in range(3):
        xx = x0 + 1.2 + (x1 - x0 - 2.4) * k / 2
        FS.box(xx - 0.15, xx + 0.15, 1.4, 13.8, -FZ - 1.7, -FZ - 1.6, STEEL2)
    edge = e * IGap
    for k in range(10):
        y = 1.2 + 1.28 * k
        FS.box(*sorted((edge, edge + e * 0.6)), y, y + 0.64, -FZ - 1.72, -FZ - 1.66, (HAZ, BLACK)[k % 2])
FG.box(-IGap + 0.1, IGap - 0.1, 2.0, 12.0, -FZ - 0.98, -FZ - 0.96, "1E3A50")
for y in (3.0, 6.0, 9.0):
    FG.box(-IGap + 0.2, IGap - 0.2, y, y + 0.2, -FZ - 1.0, -FZ - 0.98, CYAN)
FS.box(-12.0, 12.0, 14.0, 15.0, -FZ - 2.2, -FZ - 0.88, DARK2)  # рельс крана и мигалки
FS.box(-3.0, 0.0, 13.2, 14.0, -FZ - 2.4, -FZ - 1.4, HAZ)
FS.box(-1.55, -1.45, 10.4, 13.2, -FZ - 1.95, -FZ - 1.85, DARK)
FS.prism_zy([(-FZ - 2.4, 10.4), (-FZ - 1.4, 10.4), (-FZ - 1.6, 9.8), (-FZ - 2.2, 9.8)], -1.8, -1.2, STEEL2)
for k in range(5):
    x = -9.0 + 4.5 * k
    FS.prism_xz(K.ngon(x, -FZ - 1.8, 0.35, 8), 15.0, 15.3, DARK)
    FG.prism_xz(K.ngon(x, -FZ - 1.8, 0.28, 8), 15.3, 15.8, ORANGE)
emblem(FS.prism_xy, -14.6, 11.0, 1.8, -FZ - 1.2, -FZ - 0.88)
# запасной кулак на поддоне, бочки, ящики, тележка, ступня
FS.box(-17.0, -11.0, 0.0, 0.6, -FZ - 7.2, -FZ - 3.2, "A07A4A")
fist(FS, -14.0, 0.6, -FZ - 4.8, 1.0, GOLDM)
for k, (x, z) in enumerate(((11.4, -FZ - 6.4), (13.2, -FZ - 6.6), (12.2, -FZ - 4.9))):
    barrel(FS, x, z, (RED, OLIVE, RED)[k])
for k in range(3):
    D.crate(FS, 15.6, -FZ - 3.4 - 1.4 * k, 0.0, 1.3, OLIVE, "4A5A30")
D.crate(FS, 15.6, -FZ - 4.8, 1.3, 1.3, OLIVE, "4A5A30")
FS.box(5.0, 8.0, 1.0, 3.2, -FZ - 6.6, -FZ - 5.0, RED)  # инструментальная тележка
for k in range(3):
    FS.box(5.1, 7.9, 1.3 + 0.65 * k, 1.36 + 0.65 * k, -FZ - 6.66, -FZ - 6.6, DARK)
for e in (-1, 1):
    FS.prism_xy(K.ngon(6.5 + e * 1.1, 0.4, 0.4, 8), -FZ - 6.0, -FZ - 5.6, BLACK)
FS.box(-7.6, -3.4, 0.0, 1.2, -FZ - 7.2, -FZ - 4.2, DARK2)  # ступня на подставке
FS.loft([(-7.4, 1.2, -FZ - 7.2), (-3.6, 1.2, -FZ - 7.2), (-3.6, 1.2, -FZ - 4.4), (-7.4, 1.2, -FZ - 4.4)],
        [(-7.0, 2.6, -FZ - 6.4), (-4.0, 2.6, -FZ - 6.4), (-4.0, 2.6, -FZ - 4.6), (-7.0, 2.6, -FZ - 4.6)], GOLDM)
FS.box(-6.2, -4.8, 2.6, 4.2, -FZ - 6.0, -FZ - 4.9, DARK2)
# крыша: радар, антенны, прожекторы
FS.box(8.0, 12.0, 16.2, 17.0, -FZ - 1.8, -FZ + 1.0, DARK2)
FS.cone([(10.0 + 1.8 * math.cos(t), 18.7, -FZ - 1.4 + 0.8 * math.sin(t)) for t in [2 * math.pi * k / 12 for k in range(12)]],
        (10.0, 17.6, -FZ - 1.2), WHITE)
FS.box(9.9, 10.1, 17.0, 18.0, -FZ - 1.3, -FZ - 1.1, STEEL2)
for x in (-4.0, -2.6):
    FS.prism_xz(K.ngon(x, -FZ - 1.4, 0.1, 6), 16.2, 18.8, STEEL2)
FG.prism_xz(K.ngon(-4.0, -FZ - 1.4, 0.16, 6), 18.6, 18.9, RED)
for x in (4.0, -8.0):
    FS.box(x - 0.8, x + 0.8, 16.2, 17.6, -FZ - 1.8, -FZ - 1.0, DARK)
    FG.box(x - 0.6, x + 0.6, 16.4, 17.4, -FZ - 1.86, -FZ - 1.8, "F8F4E0")
# тыл: генератор
FS.box(-12.0, -4.0, 0.0, 4.2, FZ + 0.88, FZ + 3.6, OLIVE)
hazard(FS, "z", FZ + 3.6, 1, -12.0, -4.0, 0.0, 0.6, 0.0)

# ══ ИНТЕРЬЕР: ремонтный отсек ════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), DARK2)
for i in range(-4, 4):
    for j in range(-4, 4):
        IQ.box(4.2 * i + 0.1, 4.2 * i + 4.1, 0.02, 0.04, 4.0 * j + 0.1, 4.0 * j + 3.9, ("3A424C", "404852")[(i + j) % 2])
for k in range(28):
    t0, t1 = 2 * math.pi * k / 28, 2 * math.pi * (k + 0.5) / 28
    IQ.prism_xz([(5.6 * math.cos(t0), -3.0 + 5.6 * math.sin(t0)), (6.0 * math.cos(t0), -3.0 + 6.0 * math.sin(t0)),
                 (6.0 * math.cos(t1), -3.0 + 6.0 * math.sin(t1)), (5.6 * math.cos(t1), -3.0 + 5.6 * math.sin(t1))], 0.04, 0.06, HAZ)
for x in (-1.6, 1.6):
    IQ.box(x - 0.12, x + 0.12, 0.04, 0.06, 3.0, ZB - 0.9, HAZ)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, PANEL)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.2, DARK2)
        for k in range(int((a1 - a0) // 3.0) + 1):
            a = a0 + 3.0 * k
            slab(IS, axis, fixed, out, 1.1, a - 0.2, a + 0.2, 1.2, C if not gap else DOOR[1], STEEL2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, PANEL)
        hazard(IS, axis, fixed, out, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.9, 1.0)
    slab(IR, axis, fixed, out, 1.3, -half, half, 15.4, 16.0, DARK)
# портал вокруг постамента: две башни, перекладина, кабели, роборуки с искрами
for s in (-1, 1):
    tx = s * 6.6
    for e in (-1, 1):
        for f in (-1, 1):
            IS.box(tx + e * 0.7 - 0.15, tx + e * 0.7 + 0.15, 0.0, 14.6, -3.0 + f * 0.7 - 0.15, -3.0 + f * 0.7 + 0.15, PANEL)
    for k in range(6):
        y = 1.0 + 2.3 * k
        beam(IS, (tx - 0.7, y, -3.7), (tx + 0.7, y + 2.3, -3.7), 0.12, 0.12, STEEL2)
        beam(IS, (tx - 0.7, y, -2.3), (tx + 0.7, y + 2.3, -2.3), 0.12, 0.12, STEEL2)
    IS.box(tx - 0.9, tx + 0.9, 0.0, 0.4, -3.9, -2.1, DARK)
    # роборука: плечо на башне, локоть, сварочная головка, искры
    sx, sy = tx - s * 0.8, 6.0
    IS.prism_zy(K.ngon(-3.0, sy, 0.6, 10), *sorted((sx, sx - s * 0.5)), DARK)
    beam(IS, (sx - s * 0.4, sy, -3.0), (sx - s * 2.2, sy + 1.6, -1.6), 0.45, 0.45, ORANGE)
    beam(IS, (sx - s * 2.2, sy + 1.6, -1.6), (sx - s * 3.2, sy - 0.4, -0.8), 0.38, 0.38, ORANGE)
    IS.prism_xz(K.ngon(sx - s * 3.2, -0.8, 0.22, 6), sy - 1.0, sy - 0.4, DARK)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4 * s
        IG.box(sx - s * 3.2 + 0.4 * math.cos(a) - 0.06, sx - s * 3.2 + 0.4 * math.cos(a) + 0.06, sy - 1.3 - 0.2 * k, sy - 1.18 - 0.2 * k,
               -0.8 + 0.4 * math.sin(a) - 0.06, -0.8 + 0.4 * math.sin(a) + 0.06, ("FFE070", "FFB040")[k % 2])
IS.box(-7.4, 7.4, 14.6, 15.6, -3.9, -2.1, HAZ)
for k in range(5):
    x = -5.0 + 2.5 * k
    D.chain(IS, (x, 14.6, -3.0), (x * 0.6, 11.6, -3.0 + (0.6 if k % 2 else -0.6)), 4, 0.1, (BLACK, BLUE, RED)[k % 3], sag=0.4)
# большой экран со схемой робота у дальней стены
IS.box(-9.0, 9.0, 5.0, 14.0, ZF + 0.88, ZF + 1.2, DARK)
IG.box(-8.6, 8.6, 5.4, 13.6, ZF + 1.2, ZF + 1.24, "10263A")
for (x0, x1, y0, y1) in ((-1.4, 1.4, 11.0, 12.8), (-2.4, 2.4, 8.0, 10.8), (-3.6, -2.6, 8.4, 10.4), (2.6, 3.6, 8.4, 10.4),
                         (-1.8, -0.4, 5.8, 7.8), (0.4, 1.8, 5.8, 7.8)):
    IG.frame_xy(K.rect(x0, x1, y0, y1), K.rect(x0 + 0.12, x1 - 0.12, y0 + 0.12, y1 - 0.12), ZF + 1.24, ZF + 1.28, CYAN)
for k in range(5):
    IG.box(4.6, 4.6 + 1.0 + 2.0 * rng(k, 2), 12.6 - 0.9 * k, 12.85 - 0.9 * k, ZF + 1.24, ZF + 1.28, ("6AE86A", CYAN, HAZ)[k % 3])
    IG.box(-7.8, -6.8 + 1.4 * rng(k, 5), 12.6 - 0.9 * k, 12.85 - 0.9 * k, ZF + 1.24, ZF + 1.28, (CYAN, "FF6A5A")[k % 2])
# щиты с инструментами на стенах
for s in (-1, 1):
    for z in (-11.0, 1.0):
        x = s * (W - 0.95)
        IS.box(*sorted((x, x - s * 0.1)), 4.0, 9.0, z - 3.0, z + 3.0, "8A7A5A")
        for k in range(5):
            zz = z - 2.4 + 1.2 * k
            if k % 2:
                IS.box(*sorted((x - s * 0.1, x - s * 0.2)), 5.0, 8.0, zz - 0.12, zz + 0.12, STEEL2)
                IS.prism_zy(K.ngon(zz, 8.0, 0.3, 6), *sorted((x - s * 0.1, x - s * 0.2)), STEEL2)
            else:
                IS.box(*sorted((x - s * 0.1, x - s * 0.22)), 5.6, 7.6, zz - 0.3, zz + 0.3, (RED, BLUE, HAZ)[k % 3])
# запасная рука меха на подставке (слева) и топливные элементы (справа)
IS.box(-14.6, -10.6, 0.0, 1.0, -12.0, -8.0, DARK)
beam(IS, (-12.6, 1.0, -10.0), (-12.6, 5.6, -10.0), 1.4, 1.4, STEEL)
IS.prism_xy(K.ngon(-12.6, 5.6, 1.0, 10), -10.8, -9.2, DARK)
beam(IS, (-12.6, 5.6, -10.0), (-10.0, 8.6, -10.0), 1.2, 1.2, STEEL)
fist(IS, -9.6, 7.6, -10.0, 0.6, PANEL)
for k in range(4):
    z = -12.0 + 2.2 * k
    IS.prism_xz(K.ngon(13.4, z, 0.7, 10), 0.0, 0.5, DARK)
    IG.prism_xz(K.ngon(13.4, z, 0.55, 10), 0.5, 3.4, CYAN)
    IS.prism_xz(K.ngon(13.4, z, 0.7, 10), 3.4, 3.8, DARK)
# пульт у лифта
IR.box(9.0, 14.0, 0.0, 3.0, 8.0, 10.6, DARK2)
IS.loft([(9.0, 3.0, 8.0), (14.0, 3.0, 8.0), (14.0, 3.0, 10.6), (9.0, 3.0, 10.6)],
        [(9.0, 3.6, 8.0), (14.0, 3.6, 8.0), (14.0, 3.2, 10.6), (9.0, 3.2, 10.6)], STEEL2)
for k in range(4):
    IG.box(9.4 + 1.2 * k, 10.2 + 1.2 * k, 3.5, 3.58, 8.4, 9.2, (CYAN, "6AE86A", ORANGE, CYAN)[k])
IS.box(9.4, 13.6, 3.6, 6.4, 7.8, 8.1, DARK)
IG.box(9.6, 13.4, 3.8, 6.2, 8.1, 8.14, "1E4A6A")
# кран-балка и лампы
IS.box(-W, W, C - 1.6, C - 0.9, 7.6, 8.4, HAZ)
IS.box(3.0, 5.0, C - 2.4, C - 1.6, 7.2, 8.8, DARK)
IS.box(3.95, 4.05, 11.0, C - 2.4, 7.95, 8.05, DARK)
for i in (-1, 1):
    for j in (-1, 1):
        x, z = i * 10.0, -3.0 + j * 7.0
        IS.box(x - 0.03, x + 0.03, C - 2.4, C, z - 0.03, z + 0.03, DARK)
        IS.cone([(x + 1.1 * math.cos(t), C - 3.0, z + 1.1 * math.sin(t)) for t in [2 * math.pi * k / 10 for k in range(10)]], (x, C - 2.3, z), STEEL2)
        IG.prism_xz(K.ngon(x, z, 0.5, 8), C - 3.15, C - 3.0, "F0F8FF")
# площадка-постамент: зебра, зажимы, голубое кольцо
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.3, 8, turn=0.5), 0.0, 0.45, DARK)
for k in range(8):
    t0, t1 = 2 * math.pi * (k + 0.5) / 8, 2 * math.pi * (k + 1.5) / 8
    for i in range(3):
        a0, a1 = t0 + (t1 - t0) * i / 3, t0 + (t1 - t0) * (i + 1) / 3
        IS.prism_xz([(px + 4.0 * math.cos(a0), pz + 4.0 * math.sin(a0)), (px + 4.32 * math.cos(a0), pz + 4.32 * math.sin(a0)),
                     (px + 4.32 * math.cos(a1), pz + 4.32 * math.sin(a1)), (px + 4.0 * math.cos(a1), pz + 4.0 * math.sin(a1))],
                    0.45, TOP, (HAZ, BLACK)[(k * 3 + i) % 2])
IS.prism_xz(K.ngon(px, pz, 4.0, 8, turn=0.5), 0.45, TOP, DARK2)
ring_y(IG, px, pz, 3.3, 3.55, TOP, TOP + 0.04, CYAN, n=16)
for k in range(4):
    t = math.pi / 2 * k
    cx, cz = px + 3.4 * math.cos(t), pz + 3.4 * math.sin(t)
    IS.box(cx - 0.5, cx + 0.5, TOP, TOP + 0.5, cz - 0.5, cz + 0.5, STEEL2)
B.lift_leaves(IS, DARK2, HAZ)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, STEEL)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, CONC)
SL.box(-11.0, 11.0, 1.2, 14.0, -FZ - 1.6, -FZ, PANEL)
SL.box(-FX - 0.5, FX + 0.5, 15.4, 16.8, -FZ - 0.5, FZ + 0.5, HAZ)
SL.box(-15.8, -12.2, 0.6, 3.0, -FZ - 6.6, -FZ - 2.8, STEEL)
SL.box(-0.6, 0.6, 1.2, 14.0, -FZ - 1.0, -FZ - 0.4, CYAN)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 2400, (0.92, 0.96, 1.0)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.98, 0.95)),
                                                   ("Cyan", (0, 6, ZF + 5), 700, (0.4, 0.9, 1.0))])

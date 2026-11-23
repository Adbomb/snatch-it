"""Этаж «Арбуз-броненосец» музея-небоскрёба (девятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — крытый бахчевой рынок. Снаружи — жёлто-зелёный рыночный павильон с крупной кирпичной кладкой и
арками-воротами, над входом — огромная вывеска-ломоть арбуза с семечками, по фасаду — прилавки под полосатыми
тентами на шестах, пирамиды арбузов и дынь в ящиках, тележка с арбузами, весы с гирями, ящики-лотки, мешки.
Внутри — рыночный зал: ряды прилавков с горками арбузов и дынь, висящие весы, гирлянды из сеток с дынями,
полосатые тенты над рядами, ящики штабелями, грифельные доски с ломтиками-ценниками; экспонат — на гигантской
половинке арбуза (зелёная корка, красная мякоть с семечками).
Запуск: blender --background --factory-startup --python scripts/blender/floor_melon.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
import floorshell as S  # noqa: E402
from floorbase import C, FX, FZ, W, ZB, ZF, beam, rng  # noqa: E402

YEL, YEL2, BRICK, GREEN, GREEN2, RIND = "F2D46A", "D8B448", "C86A3E", "3E9A3E", "2A7A30", "8ADA6A"
FLESH, SEED, MELON, MELON2, WOOD, WOOD2 = "F04A5A", "2A1A1A", "E8C060", "C89A40", "B08048", "8A6234"
WHITE, IRON, GLASS, BLUE = "F4F0E4", "4A4A50", "F8E8C0", "3A6AC8"

F = B.Floor("ME", "MelonArmadillo", quiet=(YEL2, "C8B080", "8A9A6A"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def melon(p, x, z, y, r, water=True):
    """Арбуз — вытянутый тёмно-зелёный овал, дыня — круглая жёлтая: пояса по сфере одного цвета (без чередования
    поясов — иначе читается кочаном), верхний пояс светлее — блик."""
    ts = (-1.0, -0.62, 0.0, 0.62, 1.0)
    for k in range(4):
        t0, t1 = ts[k], ts[k + 1]
        rr = r * math.sqrt(max(0.0, 1 - ((t0 + t1) / 2) ** 2)) * 1.08
        if water:
            p.prism_xz(K.octa(x, z, rr * 1.35, rr * 0.95, rr * 0.4), y + r * (1 + t0), y + r * (1 + t1), GREEN if k == 3 else "2E6A2E")
        else:
            p.prism_xz(K.ngon(x, z, rr, 8), y + r * (1 + t0), y + r * (1 + t1), MELON2 if k == 0 else MELON)


def crate(p, x, z, y, w=2.2, d=1.4):
    p.box(x - w / 2, x + w / 2, y, y + 0.9, z - d / 2, z + d / 2, WOOD)
    for e in (-1, 1):
        p.box(x - w / 2 - 0.05, x + w / 2 + 0.05, y + 0.35 + 0.25 * e, y + 0.45 + 0.25 * e, z - d / 2 - 0.05, z + d / 2 + 0.05, WOOD2)


def awning(p, x0, x1, z0, z1, y0, y1, cols, n=6):
    for k in range(n):
        xa, xb = x0 + (x1 - x0) * k / n, x0 + (x1 - x0) * (k + 1) / n
        p.loft([(xa, y0, z0), (xb, y0, z0), (xb, y0 + 0.15, z0), (xa, y0 + 0.15, z0)],
               [(xa, y1, z1), (xb, y1, z1), (xb, y1 + 0.15, z1), (xa, y1 + 0.15, z1)], cols[k % len(cols)])
        p.prism_xy([(xa, y1), (xb, y1), ((xa + xb) / 2, y1 - 0.6)], z1 - 0.04, z1 + 0.04, cols[k % len(cols)])


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, YEL, BRICK, GREEN2, "C8B080", "5A4A3A", roof="flat", roof_col=YEL, top=16.2, pilaster=BRICK,
         band=(10.2, 10.8, BRICK), side=S.side_windows(F, GREEN2, GLASS, kind="arch", y0=11.6, y1=15.2, w=2.4, xs=(-11.20, -3.20, 4.80)))
for k in range(17):  # кирпичная кладка поясами
    y = 1.6 + 0.6 * k
    if y < 10.0:
        for j in range(16):
            x = -FX + 1.4 + 2.2 * j + (1.1 if k % 2 else 0.0)
            if j < 15 and not (y < 9.4 and min(abs(x - ax) for ax in (-11.0, 0.0, 11.0)) < 4.0):  # не поверх проёмов арок
                FS.box(x - 0.9, x + 0.9, y, y + 0.08, -FZ - 0.94, -FZ - 0.88, YEL2)
# три арки-ворот с зелёными рамами
for x in (-11.0, 0.0, 11.0):
    S.window(F, "z", -FZ, -1, x - 2.8, 1.0, 9.0, 5.6, GREEN2, "3A2A1A", kind="arch", mull=False)
    FR.box(x - 3.4, x + 3.4, 9.0, 10.2, -FZ - 1.3, -FZ - 0.88, BRICK)
    FR.box(x - 0.6, x + 0.6, 8.0, 10.4, -FZ - 1.45, -FZ - 1.3, YEL2)
# вывеска-ломоть арбуза над средней аркой
SX, SY = 0.0, 13.4
n = 10
FS.prism_xy([(SX - 4.6, SY), (SX + 4.6, SY)] + [(SX + 4.6 * math.cos(math.pi * k / n), SY - 2.6 * math.sin(math.pi * k / n))
                                                for k in range(1, n)], -FZ - 1.2, -FZ - 0.88, GREEN)
FS.prism_xy([(SX - 4.2, SY), (SX + 4.2, SY)] + [(SX + 4.2 * math.cos(math.pi * k / n), SY - 2.2 * math.sin(math.pi * k / n))
                                                for k in range(1, n)], -FZ - 1.3, -FZ - 1.2, WHITE)
FS.prism_xy([(SX - 3.9, SY), (SX + 3.9, SY)] + [(SX + 3.9 * math.cos(math.pi * k / n), SY - 1.9 * math.sin(math.pi * k / n))
                                                for k in range(1, n)], -FZ - 1.4, -FZ - 1.3, FLESH)
FS.box(SX - 4.8, SX + 4.8, SY, SY + 0.3, -FZ - 1.45, -FZ - 0.88, GREEN2)
for k in range(7):
    a = math.pi * (k + 1) / 8
    FS.prism_xy(K.octa(SX + 2.5 * math.cos(a), SY - 1.1 * math.sin(a) - 0.2, 0.12, 0.22, 0.06), -FZ - 1.5, -FZ - 1.4, SEED)
# прилавки под полосатыми тентами, ящики и пирамиды арбузов
F.objects(True)
for xs, cols in (((-17.4, -14.0), (GREEN, WHITE)), ((-7.4, -3.6), ("F08A30", WHITE)), ((3.6, 7.4), (GREEN, WHITE)),
                 ((14.0, 17.4), (FLESH, WHITE))):
    x0, x1 = xs
    awning(FS, x0, x1, -FZ - 0.9, -FZ - 2.8, 6.6, 5.6, cols, n=4)
    for x in (x0 + 0.15, x1 - 0.15):
        FS.box(x - 0.1, x + 0.1, -0.1, 5.7, -FZ - 2.8, -FZ - 2.6, WOOD2)
    crate(FS, (x0 + x1) / 2, -FZ - 2.0, -0.1, w=x1 - x0 - 0.6)
    for k in range(3):
        melon(FS, x0 + 0.9 + 0.95 * k, -FZ - 2.0, 0.8, 0.45, water=k % 2 == 0)
    melon(FS, (x0 + x1) / 2, -FZ - 2.0, 1.6, 0.42, water=True)
# тележка с арбузами
CX = 9.8
FS.box(CX - 1.6, CX + 1.6, 1.0, 1.9, -FZ - 2.6, -FZ - 1.4, WOOD)
S.disc(FS, (CX - 0.6, 0.9, -FZ - 2.7), (0, 0, -1), 0.9, 0.2, WOOD2, seg=10)
beam(FS, (CX + 1.6, 1.4, -FZ - 2.0), (CX + 3.0, 1.0, -FZ - 2.0), 0.15, 0.15, WOOD2)
for k in range(4):
    melon(FS, CX - 1.0 + 0.7 * k, -FZ - 2.0 + 0.3 * (k % 2), 1.9, 0.38, water=True)
# весы с гирями
FS.box(12.0, 13.2, -0.1, 2.4, -FZ - 1.6, -FZ - 1.2, IRON)
FS.prism_xz(K.ngon(12.6, -FZ - 1.4, 0.6, 10), 2.4, 2.5, "C8C8C8")
for k in range(3):
    FS.prism_xz(K.ngon(-9.6 + 0.5 * k, -FZ - 1.4, 0.18 + 0.05 * k, 6), -0.1, 0.3 + 0.1 * k, IRON)
F.objects(False)

# ══ ИНТЕРЬЕР: рыночный зал ════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.6
S.interior(F, YEL, "B8A07A", "6A8A5A", GREEN2, wain=(2.8, BRICK), beams=(5, WOOD2), beam_dir="z")
F.objects(True)
for s in (-1, 1):  # ряды прилавков с горками вдоль стен
    for k in range(3):
        z = -11.0 + 6.0 * k
        x = s * (W - 3.2)
        IS.box(x - 2.0, x + 2.0, 0.0, 2.6, z - 2.4, z + 2.4, WOOD)
        IS.box(x - 2.2, x + 2.2, 2.6, 2.8, z - 2.6, z + 2.6, WOOD2)
        for j in range(3):
            for i in range(3):
                melon(IS, x - 1.2 + 1.2 * i, z - 1.6 + 1.6 * j, 2.8, 0.55, water=(i + j + k) % 2 == 0)
        melon(IS, x, z, 3.9, 0.55, water=k % 2 == 0)
        awning(IS, *sorted((s * (W - 0.88), x - s * 2.8)), z - 2.8, z - 2.8, 7.6, 7.6, (GREEN, WHITE) if k % 2 else (FLESH, WHITE), n=1)
        IS.loft([(s * (W - 0.88), 8.0, z - 2.8), (s * (W - 0.88), 8.0, z + 2.8), (s * (W - 0.88), 8.2, z + 2.8), (s * (W - 0.88), 8.2, z - 2.8)],
                [(x - s * 2.6, 6.4, z - 2.8), (x - s * 2.6, 6.4, z + 2.8), (x - s * 2.6, 6.6, z + 2.8), (x - s * 2.6, 6.6, z - 2.8)],
                (GREEN, FLESH, "F08A30")[k])
        for i in range(5):
            zz = z - 2.4 + 1.2 * i
            IS.box(x - s * 2.6 - 0.06, x - s * 2.6 + 0.06, 5.8, 6.4, zz - 0.04, zz + 0.04, WHITE)
# сетки с дынями гирляндой у дальней стены и ящики штабелями
for k in range(6):
    x = -12.0 + 4.8 * k
    IS.box(x - 0.03, x + 0.03, 9.0, C - 0.6, ZF + 2.0 - 0.03, ZF + 2.0 + 0.03, "6A6A60")
    melon(IS, x, ZF + 2.0, 7.4 + 0.6 * (k % 2), 0.7, water=False)
for row in range(3):
    for k in range(4 - row):
        crate(IS, -14.0 + 2.4 * k + 1.2 * row, ZF + 6.6, 0.9 * row, w=2.2, d=1.6)
        crate(IS, 14.0 - 2.4 * k - 1.2 * row, ZF + 6.6, 0.9 * row, w=2.2, d=1.6)
# висящие весы
for x in (-6.0, 6.0):
    IS.box(x - 0.03, x + 0.03, 9.6, C - 0.6, -9.0 - 0.03, -9.0 + 0.03, IRON)
    IS.prism_xz(K.ngon(x, -9.0, 0.9, 10), 8.6, 9.6, "D8D8D0")
    IS.prism_xz(K.ngon(x, -9.0, 1.2, 10), 7.2, 7.4, "C8C8C8")
    for a in range(3):
        beam(IS, (x + 1.1 * math.cos(a * 2.1), 7.4, -9.0 + 1.1 * math.sin(a * 2.1)), (x, 8.6, -9.0), 0.05, 0.05, IRON)
F.objects(False)
for k, z in enumerate((-8.0, -2.0, 4.0)):  # грифельные доски с ломтиками
    x = -W + 0.88
    IS.box(x, x + 0.12, 9.6, 12.4, z - 1.6, z + 1.6, "2A3A2A")
    IS.prism_zy([(z - 0.8, 11.4), (z + 0.8, 11.4), (z, 10.4)], x + 0.12, x + 0.2, FLESH)
    IS.box(x + 0.12, x + 0.2, 11.4, 11.6, z - 0.85, z + 0.85, GREEN)
for x, z in ((-4.0, 3.0), (4.0, 3.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.8, z - 0.03, z + 0.03, IRON)
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=GREEN2, light="FFE8B0")
# постамент: тёмный дубовый ящик-прилавок с железными обручами и сланцевой крышкой — арбузный экспонат
# (зелёный, красный, семечки) больше не сливается с подставкой тех же цветов
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 8, 0.0), 0.0, TOP - 0.2, "5A3A22")
for y in (0.3, TOP - 0.7):
    IS.prism_xz(K.ngon(px, pz, 4.06, 8, 0.0), y, y + 0.2, IRON)
for k in range(8):  # стойки ящика по углам
    a = 2 * math.pi * k / 8
    IS.box(px + 4.02 * math.cos(a) - 0.18, px + 4.02 * math.cos(a) + 0.18, 0.0, TOP - 0.2, pz + 4.02 * math.sin(a) - 0.18,
           pz + 4.02 * math.sin(a) + 0.18, WOOD2)
IS.prism_xz(K.ngon(px, pz, 4.15, 8, 0.0), TOP - 0.2, TOP, "34343A")
B.lift_leaves(IS, GREEN2, YEL)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, YEL, "C8B080", YEL, top=16.2)
SL.prism_xy([(-4.6, 13.4), (4.6, 13.4), (0.0, 10.8)], -FZ - 1.2, -FZ, FLESH)

F.build(exhibit=(PED[0], TOP, PED[1], 3.2), lamps=[("Hall", (0, 14, 6), 1900, (1.0, 0.96, 0.86)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.9)),
                                                   ("Warm", (0, 8, -12), 600, (1.0, 0.85, 0.6))])
